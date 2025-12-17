#!/usr/bin/env python

"""Exposes functions to interact with different
linear programming solvers through the PuLP package.
"""
from __future__ import annotations  # remove in 3.11

from typing import List, Optional, Dict, Tuple, TYPE_CHECKING


if TYPE_CHECKING:
    from project_configuration import ProjectConfiguration
    from analyzer import Analyzer

import os

import pulp

from defaults import logger
from file_helper import move_files, remove_files
from interval import Interval

from nx_helper import Dag

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


class Extremum(object):
    """Represents the extremum that needs to be determined."""

    #: Find the longest path.
    LONGEST = 0
    #: Find the shortest path.
    SHORTEST = 1


#: Name of the integer linear program constructed.
_LP_NAME = "FindExtremePath"

#: Dictionary that maps the name of an integer linear programming solver to
#: a list of the PuLP solver classes that can interface with the solver.
_name_ilp_solver_map = {
    # Default integer linear programming solver of the PuLP package.
    "": ([pulp.LpSolverDefault.__class__] if pulp.LpSolverDefault is not None
         else []),

    # CBC mixed integer linear programming solver.
    "cbc": [pulp.COIN],

    # Version of CBC provided with the PuLP package.
    "cbc-pulp": [pulp.PULP_CBC_CMD],

    # IBM ILOG CPLEX Optimizer.
    "cplex": [pulp.CPLEX],

    # GNU Linear Programming Kit (GLPK).
    "glpk": [pulp.GLPK, pulp.PYGLPK],

    # Gurobi Optimizer.
    "gurobi": [pulp.GUROBI_CMD, pulp.GUROBI],

    # FICO Xpress Optimizer.
    "xpress": [pulp.XPRESS],
}

#: Dictionary that maps the name of an integer linear programming solver,
#: as used by GameTime, to its proper name for display purposes.
_proper_name_map = {
    "cbc": "CBC",
    "cbc-pulp": "CBC (provided with the PuLP package)",
    "cplex": "CPLEX",
    "glpk": "GLPK",
    "gurobi": "Gurobi",
    "xpress": "Xpress",
}


def is_ilp_solver_name(name: str)->bool:
    """
    Parameters:
        name: str :  
            Possible name of an integer linear programming solver

    Returns:
        bool:
            `True` if, and only if, the name provided is the name of a supported
            integer linear programming solver.

    """
    return name in _name_ilp_solver_map


def get_ilp_solver_names() -> List[str]:
    """
    Returns:
        List[str]
            List of the names of the supported integer linear programming solvers.

    """
    return [name for name in _name_ilp_solver_map.keys() if name != ""]


def get_ilp_solver(ilp_solver_name: str, project_config: ProjectConfiguration) -> Optional[pulp.LpSolver]:
    """

    Parameters:
        ilp_solver_name: str :
            Name of the integer linear programming solver
        project_config: ProjectConfiguration :
            ProjectConfiguration object that represents the configuration of a GameTime project

    Returns:
        PuLP solver object that can interface with the integer
        linear programming solver whose name is provided, or `None`, if
        no such object can be found.

    """
    if not is_ilp_solver_name(ilp_solver_name):
        return None

    keep_ilp_solver_output = project_config.debug_config.KEEP_ILP_SOLVER_OUTPUT
    for ilp_solver_class in _name_ilp_solver_map[ilp_solver_name]:
        ilp_solver = ilp_solver_class(keepFiles=keep_ilp_solver_output,
                                    msg=keep_ilp_solver_output)
        if ilp_solver.available():
            return ilp_solver
    return None


def get_ilp_solver_name(ilp_solver: pulp.LpSolver) -> Optional[str]:
    """

    Parameters:
        ilp_solver: pulp.LpSolver :
            Object of a PuLP solver class

    Returns:
        str, Optional:
            Name, as used by GameTime, of the integer linear programming
            solver that the input PuLP solver object can interface with,
            or `None`, if no such name can be found.

    """
    ilp_solver_class = ilp_solver.__class__
    for ilp_solver_name in _name_ilp_solver_map:
        for candidate_class in _name_ilp_solver_map[ilp_solver_name]:
            if candidate_class == ilp_solver_class:
                return ilp_solver_name
    return None


def get_proper_name(ilp_solver_name: str) -> str:
    """

    Parameters:
        ilp_solver_name: str :
            Name of an integer linear programming solver used by GameTime

    Returns:
        str:
            Proper name of an integer linear programming solver,
            for display purposes.

    """
    return _proper_name_map[ilp_solver_name]


def get_ilp_solver_proper_names() -> List[str]:
    """

    Returns:
        List[str]:
            List of proper names of the supported integer linear programming
            solvers, for display purposes.

    """
    return [get_proper_name(name) for name in get_ilp_solver_names()]


class IlpProblem(pulp.LpProblem):
    """
    Maintains information about an integer linear programming problem.
    It is a subclass of the `~pulp.LpProblem` class of the PuLP
    package, and stores additional information relevant to the GameTime
    analysis, such as the value of the objective function of the problem.
    """

    def __init__(self, *args, **kwargs):
        super(IlpProblem, self).__init__(*args, **kwargs)

        #: Value of the objective function, stored for efficiency purposes.
        self.obj_val = None


def _get_edge_flow_var(analyzer: Analyzer,
                       edge_flow_vars: Dict[int, pulp.LpVariable],
                       edge: Tuple[str, str]) -> pulp.LpVariable:
    """
    Parameters:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        edge_flow_vars:
            Dictionary that maps a positive integer to a PuLP variable that
            represents the flow through an edge. (Each postive integer is
            the position of an edge in the list of edges maintained by
            the input ``Analyzer`` object.)
        edge:
            Edge whose corresponding PuLP variable is needed.
        

    Returns:
        PuLP variable that corresponds to the input edge.

    """
    return edge_flow_vars[analyzer.dag.edges_indices[edge]]


def _get_edge_flow_vars(analyzer: Analyzer,
                        edge_flow_vars: Dict[int, pulp.LpVariable],
                        edges: List[Tuple[str, str]]) -> List[pulp.LpVariable]:
    """

    Parameters:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        edge_flow_vars:
            Dictionary that maps a positive integer to a PuLP variable
            that represents the flow through an edge. (Each postive integer
            is the position of an edge in the list of edges maintained by
            the input analyzer.)
        edges:
            List of edges whose corresponding PuLP variables are needed.
        

    Returns:
        List of the PuLP variables that correspond to each of
        the edges in the input edge list.

    """
    return [_get_edge_flow_var(analyzer, edge_flow_vars, edge) for edge in edges]


def find_least_compatible_mu_max(analyzer: Analyzer, paths):
    """
    This function returns the least dealta in the underlying graph, as
    specified by 'analyzer', that is feasible with the given set of
    measurements as specified by 'paths'. The method does not take into
    account which paths are feasible and which not; it considers all_temp_files the
    paths in the graph.

    Parameters:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        paths:
            List of paths used in the measurements. Each path is a list of
            edges in the order in which they are visited by the path

    Returns:
        float:
            A floating point value---the least delta compatible with the
            measurements

    """
    dag = analyzer.dag
    source = dag.source
    sink = dag.sink
    num_edges = dag.num_edges
    edges = dag.edges()
    num_paths = len(paths)

    project_config = analyzer.project_config

    nodes_except_source_sink = dag.nodes_except_source_sink

    # Set up the linear programming problem.
    logger.info("Number of paths: %d " % num_paths)
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem(_LP_NAME)

    logger.info("Creating variables")
    # Set up the variables that correspond to weights of each edge. 
    # Each edge is restricted to be a nonnegative real number
    edge_weights = pulp.LpVariable.dicts("we", range(0, num_edges), 0)
    # Create the variable that shall correspond to the least delta
    delta = pulp.LpVariable("delta", 0)
    for path in paths:
        path_weights = \
            _get_edge_flow_vars(analyzer, edge_weights, dag.get_edges(path.nodes))
        problem += pulp.lpSum(path_weights) <= delta + path.measured_value
        problem += pulp.lpSum(path_weights) >= -delta + path.measured_value
        print("LENGTH:", path.measured_value)

    # Optimize for the least delta
    problem += delta
    logger.info("Finding the minimum value of the objective function...")

    problem.sense = pulp.LpMinimize
    problem_status = problem.solve(solver=project_config.ilp_solver)
    if problem_status != pulp.LpStatusOptimal:
        logger.info("Maximum value not found.")
        return []
    obj_val_min = pulp.value(delta)

    logger.info("Minimum compatible delta found: %g" % obj_val_min)

    if project_config.debug_config.KEEP_ILP_SOLVER_OUTPUT:
        _move_ilp_files(os.getcwd(), project_config.location_temp_dir)
    else:
        _remove_temp_ilp_files()
    return obj_val_min


# compact
def find_longest_path_with_delta(analyzer, paths, delta,
                                 extremum=Extremum.LONGEST):
    """
    This functions finds the longest/shortest path compatible with the
        measured lengths of paths, as given in 'paths', such the actual
        lengths are within 'delta' of the measured lengths

    Parameters:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        paths:
            List of paths used in the measurements. Each path is a list of
            edges in the order in which they are visited by the path
        delta:
            the maximal limit by which the length of a measured path is
            allowed to differ from the measured value
        extremum:
            Specifies whether we are calculating Extremum.LONGEST or 
            Extremum.SHORTEST

    Returns:
        Pair consisting of the resulting path and the ILP problem used to
        calculate the path

    """
    # Increase delta by one percent, so that we do end up with an unsatisfiable
    # ILP due to floating-point issues
    delta *= 1.01
    val, result_path, problem = generate_and_solve_core_problem(
        analyzer, paths, (lambda path: path.measured_value + delta),
        (lambda path: path.measured_value - delta),
        True, extremum=extremum)
    return result_path, problem


def make_compact(dag):
    """
    Function to create a compact representation of the given graph
    Compact means that if in the original graph, there is a simple
    path without any branching between two nodes, then in the resulting
    graph the entire simple path is replaced by only one edge

    Parameters:
        dag:
            The graph that get compactified

    Returns:  
        A mapping (vertex, vertex) -> edge_number so that the edge
        (vertex, vertex) in the original graph 'dag' gets mapped to
        the edge with number 'edge_number'. All edges on a simple path
        without branching get mapped to the same 'edge_number'

    """
    processed = {}
    result = Dag()
    source = dag.source
    different_edges = []
    edge_map = {}

    def dfs(node, edge_index):
        if node in processed:
            return node
        processed[node] = node
        index = node
        neighbors = dag.neighbors(node)

        if len(neighbors) == 0: return
        if (len(neighbors) == 1) and (len(dag.predecessors(node)) == 1):
            # edge get compactified
            edge_map[(node, neighbors[0])] = edge_index
            dfs(neighbors[0], edge_index)
            return

        for to in dag.neighbors(node):
            # start new edge
            new_edge = len(different_edges)
            different_edges.append(0)
            edge_map[(node, to)] = new_edge
            dfs(to, new_edge)
        return

    dfs(source, source)
    return edge_map


def generate_and_solve_core_problem(analyzer, paths, path_function_upper,
                                    path_function_lower, weights_positive,
                                    print_problem=False, extremum=Extremum.LONGEST):
    """
    This function actually constructs the ILP to find the longest path
    in the graph specified by 'analyzer' using the set of measured paths given
    by 'paths'.

    Parameters:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed. Among others, contains the underlying
            DAG or the collection of infeasible paths.
        paths:
            List of paths used in the measurements. Each path is a list of
            edges in the order in which they are visited by the path
        pathFunctionUpper:
            Function of type: path -> float that for a given path should
            return the upper bound on the length of the given path. The
            input 'path' is always from 'paths'
        pathFunctionLower:
            Function of type: path -> float that for a given path should
            return the upper bound on the length of the given path. The
            input 'path' is always from 'paths'
        weightsPositive:
            Boolean value specifying whether the individual edge weight are
            required to be at least 0 (if set to True) or can be arbitrary
            real value (if set to False)
        printProblem:
            Boolean value used for debugging. If set to true, the generated
            ILP is printed.
        extremum:
            Specifies whether we are calculating Extremum.LONGEST or 
            Extremum.SHORTEST

    Returns:   
        Triple consisting of the length of the longest path found, the actual
        path and the ILP problem generated.

    """
    dag = analyzer.dag
    dag.initialize_dictionaries()
    source = dag.source
    sink = dag.sink
    num_edges = dag.num_edges
    edges = dag.edges()
    num_paths = len(paths)

    # Use the compact representation of the DAG
    # compact is now a mapping that for each edge of dag gives an index of an
    # edge in the compact graph.
    compact = make_compact(dag)
    project_config = analyzer.project_config

    nodes_except_source_sink = dag.nodes_except_source_sink
    path_exclusive_constraints = analyzer.path_exclusive_constraints
    path_bundled_constraints = analyzer.path_bundled_constraints

    # Set up the linear programming problem.
    logger.info("Number of paths: %d " % num_paths)
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem(_LP_NAME)

    # Take M to be the maximum edge length. Add 1.0 to make sure there are
    # no problems due to rounding errors.
    m = max([path_function_upper(path) for path in paths] + [0]) + 1.0
    if not weights_positive: m *= num_edges

    logger.info("Using value %.2f for M --- the maximum edge weight" % m)
    logger.info("Creating variables")

    values = set()
    for key in compact:
        values.add(compact[key])
    new_edges = len(values)

    # Set up the variables that correspond to the flow through each edge.
    # Set each of the variables to be an integer binary variable.
    edge_flows = pulp.LpVariable.dicts("EdgeFlow", range(0, new_edges),
                                      0, 1, pulp.LpBinary)
    edge_weights = pulp.LpVariable.dicts(
        "we", range(0, new_edges), 0 if weights_positive else -m, m)

    # for a given 'path' in the original DAG returns the edgeFlow variables
    # corresponding to the edges along the same path in the compact DAG.
    def get_new_indices(compact, edge_flows, path):
        edges = [compact[edge] for edge in path]
        path_weights = [edge_flows[edge] for edge in set(edges)]
        return path_weights

    for path in paths:
        path_weights = \
            get_new_indices(compact, edge_weights, dag.get_edges(path.nodes))
        problem += pulp.lpSum(path_weights) <= path_function_upper(path)
        problem += pulp.lpSum(path_weights) >= path_function_lower(path)

    # Add a constraint for the flow from the source. The flow through all_temp_files of
    # the edges out of the source should sum up to exactly 1.
    edge_flows_from_source = \
        get_new_indices(compact, edge_flows, dag.out_edges(source))
    problem += pulp.lpSum(edge_flows_from_source) == 1, "Flows from source"

    # Add constraints for the rest of the nodes (except sink). The flow
    # through all_temp_files of the edges into a node should equal the flow through
    # all_temp_files of the edges out of the node. Hence, for node n, if e_i and e_j
    # enter a node, and e_k and e_l exit a node, the corresponding flow
    # equation is e_i + e_j = e_k + e_l.
    for node in nodes_except_source_sink:
        if (dag.neighbors(node) == 1) and (dag.predecessors(node) == 1):
            continue
        edge_flows_to_node = get_new_indices(compact, edge_flows,
                                             dag.in_edges(node))
        edge_flows_from_node = get_new_indices(compact, edge_flows,
                                               dag.out_edges(node))
        problem += \
            (pulp.lpSum(edge_flows_to_node) == pulp.lpSum(edge_flows_from_node),
             "Flows through %s" % node)

    # Add a constraint for the flow to the sink. The flow through all_temp_files of
    # the edges into the sink should sum up to exactly 1.
    edge_flows_to_sink = get_new_indices(compact, edge_flows,
                                         dag.in_edges(sink))
    problem += pulp.lpSum(edge_flows_to_sink) == 1, "Flows to sink"

    # Add constraints for the exclusive path constraints. To ensure that
    # the edges in each constraint are not taken together, the total flow
    # through all_temp_files the edges should add to at least one unit less than
    # the number of edges in the constraint. Hence, if a constraint
    # contains edges e_a, e_b, e_c, then e_a + e_b + e_c must be less than 3.
    # This way, all_temp_files three of these edges can never be taken together.
    for constraint_num, path in enumerate(path_exclusive_constraints):
        edge_flows_in_constraint = get_new_indices(compact, edge_flows, path)
        problem += (pulp.lpSum(edge_flows_in_constraint) <=
                    (len(edge_flows_in_constraint) - 1),
                    "Path exclusive constraint %d" % (constraint_num + 1))

    # Each product_vars[index] in the longest path should correspond to
    # edge_flows[index] * edge_weights[index]
    product_vars = pulp.LpVariable.dicts("pe", range(0, new_edges), -m, m)
    for index in range(0, new_edges):
        if extremum == Extremum.LONGEST:
            problem += product_vars[index] <= edge_weights[index]
            problem += product_vars[index] <= m * edge_flows[index]
        else:
            problem += product_vars[index] >= edge_weights[index] - m * (1.0 - edge_flows[index])
            problem += product_vars[index] >= 0

    objective = pulp.lpSum(product_vars)
    problem += objective
    logger.info("Objective function constructed.")

    if extremum == Extremum.LONGEST:
        logger.info("Finding the maximum value of the objective function...")
        problem.sense = pulp.LpMaximize
    else:
        logger.info("Finding the minimum value of the objective function...")
        problem.sense = pulp.LpMinimize
    problem_status = problem.solve(solver=project_config.ilp_solver)

    if print_problem: logger.info(problem)

    if problem_status != pulp.LpStatusOptimal:
        logger.info("Maximum value not found.")
        return -1, [], problem

    obj_val_max = pulp.value(objective)
    problem.obj_val = obj_val_max
    logger.info("Maximum value found: %g" % obj_val_max)

    logger.info("Finding the path that corresponds to the maximum value...")
    # Determine the edges along the extreme path using the solution.
    max_path = [edges[edge_num] for edge_num in edge_flows
                if edge_flows[edge_num].value() > 0.1]
    logger.info("Path found.")

    total_length = sum([product_vars[edge_num].value() for edge_num in edge_flows
                        if edge_flows[edge_num].value() == 1])
    logger.info("Total length of the path %.2f" % total_length)
    obj_val_max = total_length

    max_path = [edge_num for edge_num in range(0, new_edges)
                if edge_flows[edge_num].value() > 0.1]
    extreme_path = []
    # reverse extreme_path according to the compact edgeMap
    for edge in max_path:
        map_to = [source for source in compact if compact[source] == edge]
        extreme_path.extend(map_to)

    # Arrange the nodes along the extreme path in order of traversal
    # from source to sink.
    result_path = []

    logger.info("Arranging the nodes along the chosen extreme path "
                "in order of traversal...")
    # To do so, first construct a dictionary mapping a node along the path
    # to the edge from that node.
    extreme_path_dict = {}
    for edge in extreme_path:
        extreme_path_dict[edge[0]] = edge
    # Now, "thread" a path through the dictionary.
    curr_node = dag.source
    result_path.append(curr_node)
    while curr_node in extreme_path_dict:
        new_edge = extreme_path_dict[curr_node]
        curr_node = new_edge[1]
        result_path.append(curr_node)
    logger.info("Nodes along the chosen extreme path arranged.")

    if project_config.debug_config.KEEP_ILP_SOLVER_OUTPUT:
        _move_ilp_files(os.getcwd(), project_config.location_temp_dir)
    else:
        _remove_temp_ilp_files()
    # We're done!
    return obj_val_max, result_path, problem


def find_worst_expressible_path(analyzer, paths, bound):
    """
    Function to find the longest path in the underlying graph of 'analyzer'
    assuming the lengths of all_temp_files measured paths are between -1 and 1.

    Parameters:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        paths:
            List of paths used in the measurements. Each path is a list of
            edges in the order in which they are visited by the path
        bound:
            ???

    Returns: 
        Triple consisting of the length of the longsest path, the path itself
        and the ILP solved to find the path.

    """
    return generate_and_solve_core_problem(
        analyzer, paths, (lambda x: 1), (lambda x: -1), False)


def find_goodness_of_fit(analyzer, paths, basis):
    """
    This function is here only for test purposes. Each path pi in `paths',
    can be expressed as a linear combination
    pi = a_1 b_1 + ... + a_n b_n
    of paths b_i from `basis`. This function returns the least number `c`
    such that every path can be expressed as a linear combination of basis
    paths b_i such that the sum of absolute value of coefficients is at
    most `c`: |a_1| + |a_2| + ... + |a_n| <= c

    Parameters:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        paths:
            List of paths that we want to find out how well can be
            expressed as a linear combination of paths in `basis`
        basis:
            List of paths that are used to express `paths` as a linear
            combination of

    Returns:
        The number `c` as described in the paragraph above.

    """
    dag = analyzer.dag
    source = dag.source
    sink = dag.sink
    num_edges = dag.num_edges
    edges = dag.edges()
    num_paths = len(paths)
    num_basis = len(basis)
    project_config = analyzer.project_config

    # Set up the linear programming problem.
    logger.info("Number of paths: %d " % num_paths)
    logger.info("Number of basis paths: %d " % num_basis)
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem("BLAH")

    logger.info("Creating variables")
    indices = [(i, j) for i in range(num_paths) for j in range(num_basis)]
    coeffs = pulp.LpVariable.dicts("c", indices, -100, 100)
    abs_values = pulp.LpVariable.dicts("abs", indices, 0, 100)
    bound = pulp.LpVariable("bnd", 0, 10000)

    logger.info("Add absolute values")
    for index in indices:
        problem += abs_values[index] >= coeffs[index]
        problem += abs_values[index] >= -coeffs[index]

    for i in range(num_paths):
        # all_temp_files coefficients expressing path i
        all_coeff_expressing = [abs_values[(i, j)] for j in range(num_basis)]
        problem += pulp.lpSum(all_coeff_expressing) <= bound
        # express path i as a linear combination of basis paths
        for edge in edges:
            paths_containing_edge = \
                [j for j in range(num_basis) if (edge in basis[j])]
            present_coeffs = [coeffs[(i, j)] for j in paths_containing_edge]
            present = 1 if (edge in paths[i]) else 0
            problem += pulp.lpSum(present_coeffs) == present
    problem += bound
    problem.sense = pulp.LpMinimize

    problem_status = problem.solve(solver=project_config.ilp_solver)
    if problem_status != pulp.LpStatusOptimal:
        logger.info("Minimum value not found.")
        return [], problem
    obj_val_min = pulp.value(bound)

    logger.info("Minimum value found: %g" % obj_val_min)

    return obj_val_min


def find_minimal_overcomplete_basis(analyzer: Analyzer, paths, k):
    """
    This function is here only for test purposes. The functions finds the
    smallest set of 'basis paths' with the following property: Each path pi
    in `paths', can be expressed as a linear combination
    pi = a_1 b_1 + ... + a_n b_n
    of paths b_i from `basis`. This function finds the set of basis paths
    such that every path can be expressed as a linear combination of basis
    paths b_i  such that the sum of absolute value of coefficients is at
    most 'k': |a_1| + |a_2| + ... + |a_n| <= k

    Parameters:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        paths:
            List of paths that we want to find out how well can be
            expressed as a linear combination of paths in `basis`
        k:
            bound on how well the 'paths' can be expressed as a linear
            combination of the calculated basis paths


    Returns:
        List of paths satisfying the condition stated above

    """
    project_config = analyzer.project_config
    dag = analyzer.dag
    source = dag.source
    sink = dag.sink
    num_edges = dag.num_edges
    edges = dag.edges()
    num_paths = len(paths)

    # Set up the linear programming problem.
    logger.info("Number of paths: %d " % num_paths)
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem(_LP_NAME)

    logger.info("Creating variables")
    indices = [(i, j) for i in range(num_paths) for j in range(num_paths)]
    coeffs = pulp.LpVariable.dicts("c", indices, -k, k)
    abs_values = pulp.LpVariable.dicts("abs", indices, 0, k)
    used_paths = pulp.LpVariable.dicts(
        "used", range(num_paths), 0, 1, pulp.LpBinary)

    logger.info("Adding used_paths")
    for i in range(num_paths):
        for j in range(num_paths):
            problem += k * used_paths[j] >= abs_values[(i, j)]

    logger.info("Add absolute values")
    for index in indices:
        problem += abs_values[index] >= coeffs[index]
        problem += abs_values[index] >= -coeffs[index]

    for i in range(num_paths):
        logger.info("Processing path number %d" % i)
        # all_temp_files coefficients expressing path i
        all_coeff_expressing = [abs_values[(i, j)] for j in range(num_paths)]
        problem += pulp.lpSum(all_coeff_expressing) <= k
        for edge in edges:
            paths_containing_edge = \
                [j for j in range(num_paths) if (edge in paths[j])]
            present_coeffs = [coeffs[(i, j)] for j in paths_containing_edge]
            present = 1 if (edge in paths[i]) else 0
            problem += pulp.lpSum(present_coeffs) == present
    objective = pulp.lpSum(used_paths)
    problem += objective
    problem.sense = pulp.LpMinimize

    problem_status = problem.solve(solver=project_config.ilp_solver)
    if problem_status != pulp.LpStatusOptimal:
        logger.info("Minimum value not found.")
        return [], problem
    obj_val_min = pulp.value(objective)

    logger.info("Minimum value found: %g" % obj_val_min)

    solution_paths = \
        [index for index in range(num_paths) if used_paths[index].value() == 1]
    return solution_paths


def find_extreme_path(analyzer, extremum=Extremum.LONGEST, interval=None):
    """
    Determines either the longest or the shortest path through the DAG
    with the constraints stored in the ``Analyzer`` object provided.

    Parameters:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        extremum:
            Type of extreme path to calculate.
        interval:
            ``Interval`` object that represents the interval of values
            that the generated paths can have. If no ``Interval`` object
            is provided, the interval of values is considered to be
            all_temp_files real numbers.

    Returns:   
        Tuple whose first element is the longest or the shortest path
        through the DAG, as a list of nodes along the path (ordered
        by traversal from source to sink), and whose second element is
        the integer linear programming problem that was solved to obtain
        the path, as an object of the ``IlpProblem`` class.
        
        If no such path is feasible, given the constraints stored in
        the ``Analyzer`` object and the ``Interval`` object provided,
        the first element of the tuple is an empty list, and the second
        element of the tuple is an ``IlpProblem`` object whose ``obj_al``
        instance variable is None.

    """
    # Make temporary variables for the frequently accessed
    # variables from the ``Analyzer`` object provided.
    project_config = analyzer.project_config

    dag = analyzer.dag
    source = dag.source
    sink = dag.sink
    num_edges = dag.num_edges

    nodes_except_source_sink = dag.nodes_except_source_sink
    edges = list(dag.all_edges)
    edge_weights = dag.edge_weights

    path_exclusive_constraints = analyzer.path_exclusive_constraints
    path_bundled_constraints = analyzer.path_bundled_constraints

    # Set up the linear programming problem.
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem(_LP_NAME)

    logger.info("Creating the variables and adding the constraints...")

    # Set up the variables that correspond to the flow through each edge.
    # Set each of the variables to be an integer binary variable.
    edge_flows = pulp.LpVariable.dicts("EdgeFlow", range(0, num_edges),
                                       0, 1, pulp.LpBinary)

    # Add a constraint for the flow from the source. The flow through all_temp_files of
    # the edges out of the source should sum up to exactly 1.
    edge_flows_from_source = _get_edge_flow_vars(analyzer, edge_flows,
                                                 dag.out_edges(source))
    problem += pulp.lpSum(edge_flows_from_source) == 1, "Flows from source"

    # Add constraints for the rest of the nodes (except sink). The flow
    # through all_temp_files of the edges into a node should equal the flow through
    # all_temp_files of the edges out of the node. Hence, for node n, if e_i and e_j
    # enter a node, and e_k and e_l exit a node, the corresponding flow
    # equation is e_i + e_j = e_k + e_l.
    for node in nodes_except_source_sink:
        edge_flows_to_node = _get_edge_flow_vars(analyzer, edge_flows,
                                                 dag.in_edges(node))
        edge_flows_from_node = _get_edge_flow_vars(analyzer, edge_flows,
                                                   dag.out_edges(node))
        problem += \
            (pulp.lpSum(edge_flows_to_node) == pulp.lpSum(edge_flows_from_node),
             "Flows through %s" % node)

    # Add a constraint for the flow to the sink. The flow through all_temp_files of
    # the edges into the sink should sum up to exactly 1.
    edge_flows_to_sink = _get_edge_flow_vars(analyzer, edge_flows,
                                             dag.in_edges(sink))
    problem += pulp.lpSum(edge_flows_to_sink) == 1, "Flows to sink"

    # Add constraints for the exclusive path constraints. To ensure that
    # the edges in each constraint are not taken together, the total flow
    # through all_temp_files the edges should add to at least one unit less than
    # the number of edges in the constraint. Hence, if a constraint
    # contains edges e_a, e_b, e_c, then e_a + e_b + e_c must be less than 3.
    # This way, all_temp_files three of these edges can never be taken together.
    for constraint_num, path in enumerate(path_exclusive_constraints):
        edge_flows_in_constraint = _get_edge_flow_vars(analyzer, edge_flows, path)
        problem += (pulp.lpSum(edge_flows_in_constraint) <= (len(path) - 1),
                    "Path exclusive constraint %d" % (constraint_num + 1))

    # Add constraints for the bundled path constraints. If a constraint
    # contains edges e_a, e_b, e_c, e_d, and each edge *must* be taken,
    # then e_b + e_c + e_d must sum up to e_a, scaled by -3 (or one less
    # than the number of edges in the path constraint). Hence, the flow
    # constraint is e_b + e_c + e_d = -3 * e_a. By default, we scale
    # the first edge in a constraint with this negative value.
    for constraint_num, path in enumerate(path_bundled_constraints):
        first_edge = path[0]
        first_edge_flow = _get_edge_flow_var(analyzer, edge_flows, first_edge)
        edge_flows_for_rest = _get_edge_flow_vars(analyzer, edge_flows, path[1:])
        problem += \
            (pulp.lpSum(edge_flows_for_rest) == (len(path) - 1) * first_edge_flow,
             "Path bundled constraint %d" % (constraint_num + 1))

    # There may be bounds on the values of the paths that are generated
    # by this function: we add constraints for these bounds. For this,
    # we weight the PuLP variables for the edges using the list of
    # edge weights provided, and then impose bounds on the sum.
    weighted_edge_flow_vars = []
    for edge_index, edge_flow_var in edge_flows.items():
        edge_weight = edge_weights[edge_index]
        weighted_edge_flow_vars.append(edge_weight * edge_flow_var)
    interval = interval or Interval()
    if interval.has_finite_lower_bound():
        problem += \
            (pulp.lpSum(weighted_edge_flow_vars) >= interval.lower_bound)
    if interval.has_finite_upper_bound():
        problem += \
            (pulp.lpSum(weighted_edge_flow_vars) <= interval.upper_bound)

    logger.info("Variables created and constraints added.")

    logger.info("Constructing the objective function...")
    # Finally, construct and add the objective function.
    # We reuse the constraint (possibly) added in the last step of
    # the constraint addition phase.
    objective = pulp.lpSum(weighted_edge_flow_vars)
    problem += objective
    logger.info("Objective function constructed.")

    logger.info("Finding the maximum value of the objective function...")

    problem.sense = pulp.LpMaximize
    problem_status = problem.solve(solver=get_ilp_solver(project_config.ilp_solver, project_config))
    if problem_status != pulp.LpStatusOptimal:
        logger.info("Maximum value not found.")
        return [], problem
    obj_val_max = pulp.value(objective)

    logger.info("Maximum value found: %g" % obj_val_max)

    logger.info("Finding the path that corresponds to the maximum value...")
    # Determine the edges along the extreme path using the solution.

    max_path = [edges[edge_num] for edge_num in edge_flows.keys() if (edge_flows[edge_num].value() == 1)]
    logger.info("Path found.")

    logger.info("Finding the minimum value of the objective function...")

    problem.sense = pulp.LpMinimize
    problem_status = problem.solve(solver=get_ilp_solver(project_config.ilp_solver, project_config))
    if problem_status != pulp.LpStatusOptimal:
        logger.info("Minimum value not found.")
        return [], problem
    obj_val_min = pulp.value(objective)

    logger.info("Minimum value found: %g" % obj_val_min)

    logger.info("Finding the path that corresponds to the minimum value...")
    # Determine the edges along the extreme path using the solution.
    min_path = [edges[edge_num] for edge_num in edge_flows
                if edge_flows[edge_num].value() == 1]
    logger.info("Path found.")

    # Choose the correct extreme path based on the optimal solutions
    # and the type of extreme path required.
    abs_max, abs_min = abs(obj_val_max), abs(obj_val_min)
    if extremum is Extremum.LONGEST:
        extreme_path = max_path if abs_max >= abs_min else min_path
        problem.sense = (pulp.LpMaximize if abs_max >= abs_min
                         else pulp.LpMinimize)
        problem.obj_val = max(abs_max, abs_min)
    elif extremum is Extremum.SHORTEST:
        extreme_path = min_path if abs_max >= abs_min else max_path
        problem.sense = (pulp.LpMinimize if abs_max >= abs_min
                         else pulp.LpMaximize)
        problem.obj_val = min(abs_max, abs_min)

    # Arrange the nodes along the extreme path in order of traversal
    # from source to sink.
    result_path = []

    logger.info("Arranging the nodes along the chosen extreme path "
                "in order of traversal...")
    # To do so, first construct a dictionary mapping a node along the path
    # to the edge from that node.
    extreme_path_dict = {}
    for edge in extreme_path:
        extreme_path_dict[edge[0]] = edge
    # Now, "thread" a path through the dictionary.
    curr_node = source
    result_path.append(curr_node)
    while curr_node in extreme_path_dict:
        new_edge = extreme_path_dict[curr_node]
        curr_node = new_edge[1]
        result_path.append(curr_node)
    logger.info("Nodes along the chosen extreme path arranged.")

    if project_config.debug_config.KEEP_ILP_SOLVER_OUTPUT:
        _move_ilp_files(os.getcwd(), project_config.location_temp_dir)
    else:
        _remove_temp_ilp_files()

    # We're done!
    return result_path, problem


def _move_ilp_files(source_dir, dest_dir):
    """
    Moves the files that are generated when an integer linear program
    is solved, from the source directory whose location is provided
    to the destination directory whose location is provided.

    Parameters:
        source_dir : 
            Location of the source directory
        dest_dir :
            Location of the destination directory
    """
    move_files([_LP_NAME + r"-pulp\.lp", _LP_NAME + r"-pulp\.mps",
                _LP_NAME + r"-pulp\.prt", _LP_NAME + r"-pulp\.sol"],
               source_dir, dest_dir)


def _remove_temp_ilp_files():
    """
    Removes the temporary files that are generated when an
    integer linear program is solved.

    """
    remove_files([r".*\.lp", r".*\.mps", r".*\.prt", r".*\.sol"], os.getcwd())
