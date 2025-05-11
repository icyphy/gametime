#!/usr/bin/env python

"""Exposes functions to interact with different
linear programming solvers through the PuLP package.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""

import os

import pulp

from defaults import logger
from fileHelper import moveFiles
from fileHelper import removeFiles
from interval import Interval

from nxHelper import Dag


class Extremum(object):
    """Represents the extremum that needs to be determined."""

    #: Find the longest path.
    LONGEST = 0
    #: Find the shortest path.
    SHORTEST = 1


#: Name of the integer linear program constructed.
_LP_NAME = "gt-FindExtremePath"

#: Dictionary that maps the name of an integer linear programming solver to
#: a list of the PuLP solver classes that can interface with the solver.
_nameIlpSolverMap = {
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
_properNameMap = {
    "cbc": "CBC",
    "cbc-pulp": "CBC (provided with the PuLP package)",
    "cplex": "CPLEX",
    "glpk": "GLPK",
    "gurobi": "Gurobi",
    "xpress": "Xpress",
}

def isIlpSolverName(name):
    """
    Arguments:
        name:
            Possible name of an integer linear programming solver.

    Returns:
        `True` if, and only if, the name provided is the name of a supported
        integer linear programming solver.
    """
    return name in _nameIlpSolverMap

def getIlpSolverNames():
    """
    Returns:
        List of the names of the supported integer linear programming solvers.
    """
    return [name for name in _nameIlpSolverMap.keys() if name is not ""]

def getIlpSolver(ilpSolverName, projectConfig):
    """
    Arguments:
        ilpSolverName:
            Name of the integer linear programming solver.
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.

    Returns:
        PuLP solver object that can interface with the integer
        linear programming solver whose name is provided, or `None`, if
        no such object can be found.
    """
    if not isIlpSolverName(ilpSolverName):
        return None

    keepIlpSolverOutput = projectConfig.debugConfig.KEEP_ILP_SOLVER_OUTPUT
    for ilpSolverClass in _nameIlpSolverMap[ilpSolverName]:
        ilpSolver = ilpSolverClass(keepFiles=keepIlpSolverOutput, 
                                   msg=keepIlpSolverOutput)
        if ilpSolver.available():
            return ilpSolver
    return None

def getIlpSolverName(ilpSolver):
    """
    Arguments:
        ilpSolver:
            Object of a PuLP solver class.

    Returns:
        Name, as used by GameTime, of the integer linear programming
        solver that the input PuLP solver object can interface with,
        or `None`, if no such name can be found.
    """
    ilpSolverClass = ilpSolver.__class__
    for ilpSolverName in _nameIlpSolverMap:
        for candidateClass in _nameIlpSolverMap[ilpSolverName]:
            if candidateClass == ilpSolverClass:
                return ilpSolverName
    return None

def getProperName(ilpSolverName):
    """
    Arguments:
        ilpSolverName:
            Name of an integer linear programming solver, as
            used by GameTime.

    Returns:
        Proper name of an integer linear programming solver,
        for display purposes.
    """
    return _properNameMap[ilpSolverName]

def getIlpSolverProperNames():
    """
    Returns:
        List of proper names of the supported integer linear programming
        solvers, for display purposes.
    """
    return [getProperName(name) for name in getIlpSolverNames()]


class IlpProblem(pulp.LpProblem):
    """Maintains information about an integer linear programming problem.
    It is a subclass of the :class:`~pulp.LpProblem` class of the PuLP
    package, and stores additional information relevant to the GameTime
    analysis, such as the value of the objective function of the problem.
    """

    def __init__(self, *args, **kwargs):
        super(IlpProblem, self).__init__(*args, **kwargs)

        #: Value of the objective function, stored for efficiency purposes.
        self.objVal = None


def _getEdgeFlowVar(analyzer, edgeFlowVars, edge):
    """
    Arguments:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        edgeFlowVars:
            Dictionary that maps a positive integer to a PuLP variable that
            represents the flow through an edge. (Each postive integer is
            the position of an edge in the list of edges maintained by
            the input ``Analyzer`` object.)
        edges:
            Edge whose corresponding PuLP variable is needed.

    Returns:
        PuLP variable that corresponds to the input edge.
    """
    return edgeFlowVars[analyzer.dag.edgesIndices[edge]]

def _getEdgeFlowVars(analyzer, edgeFlowVars, edges):
    """
    Arguments:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        edgeFlowVars:
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
    return [_getEdgeFlowVar(analyzer, edgeFlowVars, edge) for edge in edges]

def findLeastCompatibleMuMax(analyzer, paths):
    """This function returns the least dealta in the underlying graph, as
       specified by 'analyzer', that is feasible with the given set of
       measurements as specified by 'paths'. The method does not take into
       account which paths are feasible and which not; it considers all the
       paths in the graph.

       Arguments:
           analyzer:
               ``Analyzer`` object that maintains information about
               the code being analyzed.
           paths:
               List of paths used in the measurements. Each path is a list of
               edges in the order in which they are visited by the path

       Returns:
           A floting point value---the least delta compatible with the
           measurements
    """
    dag = analyzer.dag
    source = dag.source
    sink = dag.sink
    numEdges = dag.numEdges
    edges = dag.edges()
    numPaths = len(paths)
    
    projectConfig = analyzer.projectConfig

    nodesExceptSourceSink = dag.nodesExceptSourceSink

    # Set up the linear programming problem.
    logger.info("Number of paths: %d " % numPaths)
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem(_LP_NAME)

    logger.info("Creating variables")
    # Set up the variables that correspond to weights of each edge. 
    # Each edge is restricted to be a nonnegative real number
    edgeWeights = pulp.LpVariable.dicts("we", range(0, numEdges), 0)
    # Create the variable that shall correspond to the least delta
    delta = pulp.LpVariable("delta", 0)
    for path in paths:
        pathWeights = \
            _getEdgeFlowVars(analyzer, edgeWeights, dag.getEdges(path.nodes)) 
        problem += pulp.lpSum(pathWeights) <= delta + path.measuredValue
        problem += pulp.lpSum(pathWeights) >= -delta + path.measuredValue
        print "LENGTH:", path.measuredValue

    # Optimize for the least delta
    problem += delta
    logger.info("Finding the minimum value of the objective function...")

    problem.sense = pulp.LpMinimize
    problemStatus = problem.solve(solver=projectConfig.ilpSolver)
    if problemStatus != pulp.LpStatusOptimal:
        logger.info("Maximum value not found.")
        return []
    objValMin = pulp.value(delta)

    logger.info("Minimum compatible delta found: %g" % objValMin)

    if projectConfig.debugConfig.KEEP_ILP_SOLVER_OUTPUT:
        _moveIlpFiles(os.getcwd(), projectConfig.locationTempDir)
    else:
        _removeTempIlpFiles()
    return objValMin

#compact
def findLongestPathWithDelta(analyzer, paths, delta,
                             extremum=Extremum.LONGEST):
    """ This functions finds the longest/shortest path compatible with the
        measured lengths of paths, as given in 'paths', such the actual
        lengths are within 'delta' of the measured lengths
         
         Arguments:
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
    val, resultPath, problem = generateAndSolveCoreProblem(
        analyzer, paths, (lambda path: path.measuredValue + delta),
                         (lambda path: path.measuredValue - delta),
        True, extremum=extremum)
    return resultPath, problem

def makeCompact(dag):
  """  Function to create a compact representation of the given graph
       Compact means that if in the original graph, there is a simple
       path without any branching between two nodes, then in the resulting
       graph the entire simple path is replaced by only one edge

       Arguments:
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
    if (node in processed):
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


def generateAndSolveCoreProblem(analyzer, paths, pathFunctionUpper,
                                pathFunctionLower, weightsPositive,
                                printProblem=False, extremum=Extremum.LONGEST):
    """This function actually constructs the ILP to find the longest path
    in the graph specified by 'analyzer' using the set of measured paths given
    by 'paths'. 
        
        Arguments
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
    dag.initializeDictionaries()
    source = dag.source
    sink = dag.sink
    numEdges = dag.numEdges
    edges = dag.edges()
    numPaths = len(paths)
   
    # Use the compact representation of the DAG
    # compact is now a mapping that for each edge of dag gives an index of an
    # edge in the compact graph.
    compact = makeCompact(dag)
    projectConfig = analyzer.projectConfig

    nodesExceptSourceSink = dag.nodesExceptSourceSink
    pathExclusiveConstraints = analyzer.pathExclusiveConstraints
    pathBundledConstraints = analyzer.pathBundledConstraints

    # Set up the linear programming problem.
    logger.info("Number of paths: %d " % numPaths)
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem(_LP_NAME)

  
    # Take M to be the maximum edge length. Add 1.0 to make sure there are
    # no problems due to rounding errors.
    M = max([pathFunctionUpper(path) for path in paths] + [0]) + 1.0
    if not weightsPositive: M *= numEdges

    logger.info("Using value %.2f for M --- the maximum edge weight" % M)
    logger.info("Creating variables")
    
    values = set()
    for key in compact:
        values.add(compact[key])
    new_edges = len(values)
    
    # Set up the variables that correspond to the flow through each edge.
    # Set each of the variables to be an integer binary variable.
    edgeFlows = pulp.LpVariable.dicts("EdgeFlow", range(0, new_edges),
                                      0, 1, pulp.LpBinary)
    edgeWeights = pulp.LpVariable.dicts(
        "we", range(0, new_edges), 0 if weightsPositive else -M, M)
   
    # for a given 'path' in the original DAG returns the edgeFlow variables
    # corresponding to the edges along the same path in the compact DAG.
    def getNewIndices(compact, edgeFlows, path):
        edges = [compact[edge] for edge in path]
        pathWeights = [edgeFlows[edge] for edge in set(edges)]
        return pathWeights

    for path in paths:
        pathWeights = \
            getNewIndices(compact, edgeWeights, dag.getEdges(path.nodes))
        problem += pulp.lpSum(pathWeights) <= pathFunctionUpper(path)
        problem += pulp.lpSum(pathWeights) >= pathFunctionLower(path)


    # Add a constraint for the flow from the source. The flow through all of
    # the edges out of the source should sum up to exactly 1.
    edgeFlowsFromSource = \
        getNewIndices(compact, edgeFlows, dag.out_edges(source))
    problem += pulp.lpSum(edgeFlowsFromSource) == 1, "Flows from source"

    # Add constraints for the rest of the nodes (except sink). The flow
    # through all of the edges into a node should equal the flow through
    # all of the edges out of the node. Hence, for node n, if e_i and e_j
    # enter a node, and e_k and e_l exit a node, the corresponding flow
    # equation is e_i + e_j = e_k + e_l.
    for node in nodesExceptSourceSink:
        if (dag.neighbors(node) == 1) and (dag.predecessors(node) == 1):
            continue
        edgeFlowsToNode = getNewIndices(compact, edgeFlows,
                                           dag.in_edges(node))
        edgeFlowsFromNode = getNewIndices(compact, edgeFlows,
                                             dag.out_edges(node))
        problem += \
        (pulp.lpSum(edgeFlowsToNode) == pulp.lpSum(edgeFlowsFromNode),
         "Flows through %s" % node)

    # Add a constraint for the flow to the sink. The flow through all of
    # the edges into the sink should sum up to exactly 1.
    edgeFlowsToSink = getNewIndices(compact, edgeFlows,
                                       dag.in_edges(sink))
    problem += pulp.lpSum(edgeFlowsToSink) == 1, "Flows to sink"

    # Add constraints for the exclusive path constraints. To ensure that
    # the edges in each constraint are not taken together, the total flow
    # through all the edges should add to at least one unit less than
    # the number of edges in the constraint. Hence, if a constraint
    # contains edges e_a, e_b, e_c, then e_a + e_b + e_c must be less than 3.
    # This way, all three of these edges can never be taken together.
    for constraintNum, path in enumerate(pathExclusiveConstraints):
        edgeFlowsInConstraint = getNewIndices(compact, edgeFlows, path)
        problem += (pulp.lpSum(edgeFlowsInConstraint) <=
                    (len(edgeFlowsInConstraint)-1),
                    "Path exclusive constraint %d" % (constraintNum+1))


    # Each productVars[index] in the longest path should correspond to
    # edgeFlows[index] * edgeWeights[index]
    productVars = pulp.LpVariable.dicts("pe", range(0, new_edges), -M, M)
    for index in range(0, new_edges):
        if extremum == Extremum.LONGEST:
            problem += productVars[index] <= edgeWeights[index]
            problem += productVars[index] <= M * edgeFlows[index]
        else:
            problem += productVars[index] >= edgeWeights[index] - M * (1.0 - edgeFlows[index])
            problem += productVars[index] >= 0
            

    objective = pulp.lpSum(productVars)
    problem += objective
    logger.info("Objective function constructed.")

    if extremum == Extremum.LONGEST:
        logger.info("Finding the maximum value of the objective function...")
        problem.sense = pulp.LpMaximize
    else:
        logger.info("Finding the minimum value of the objective function...")
        problem.sense = pulp.LpMinimize
    problemStatus = problem.solve(solver=projectConfig.ilpSolver)
   
    if (printProblem): logger.info(problem)

    if problemStatus != pulp.LpStatusOptimal:
        logger.info("Maximum value not found.")
        return -1, [], problem

    objValMax = pulp.value(objective)
    problem.objVal = objValMax
    logger.info("Maximum value found: %g" % objValMax)
    
    logger.info("Finding the path that corresponds to the maximum value...")
    # Determine the edges along the extreme path using the solution.
    maxPath = [edges[edgeNum] for edgeNum in edgeFlows
               if edgeFlows[edgeNum].value() > 0.1]
    logger.info("Path found.")
   
    totalLength = sum([productVars[edgeNum].value() for edgeNum in edgeFlows
                       if edgeFlows[edgeNum].value() == 1])
    logger.info("Total length of the path %.2f" % totalLength)
    objValMax = totalLength

    maxPath = [edgeNum for edgeNum in range(0, new_edges)
               if edgeFlows[edgeNum].value() > 0.1]
    extremePath = []
    #reverse exremePath according to the compact edgeMap
    for edge in maxPath:
        map_to = [source for source in compact if compact[source] == edge]
        extremePath.extend(map_to)
    
    # Arrange the nodes along the extreme path in order of traversal
    # from source to sink.
    resultPath = []

    logger.info("Arranging the nodes along the chosen extreme path "
                "in order of traversal...")
    # To do so, first construct a dictionary mapping a node along the path
    # to the edge from that node.
    extremePathDict = {}
    for edge in extremePath:
        extremePathDict[edge[0]] = edge
    # Now, "thread" a path through the dictionary.
    currNode = dag.source
    resultPath.append(currNode)
    while currNode in extremePathDict:
        newEdge = extremePathDict[currNode]
        currNode = newEdge[1]
        resultPath.append(currNode)
    logger.info("Nodes along the chosen extreme path arranged.")

    if projectConfig.debugConfig.KEEP_ILP_SOLVER_OUTPUT:
        _moveIlpFiles(os.getcwd(), projectConfig.locationTempDir)
    else:
        _removeTempIlpFiles()
    # We're done!
    return objValMax, resultPath, problem


def findWorstExpressiblePath(analyzer, paths, bound):
    """
        Function to find the longest path in the underlying graph of 'analyzer'
        assuming the lengths of all measured paths are between -1 and 1. 
        Arguments
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
    return generateAndSolveCoreProblem(
        analyzer, paths, (lambda x: 1), (lambda x: -1), False)

def findGoodnessOfFit(analyzer, paths, basis):
    """
        This function is here only for test purposes. Each path pi in `paths',
        can be expressed as a linear combination 
              pi = a_1 b_1 + ... + a_n b_n
        of paths b_i from `basis`. This function returns the least number `c`
        such that every path can be expressed as a linear combination of basis
        paths b_i such that the sum of absolute value of coefficients is at
        most `c`:
           |a_1| + |a_2| + ... + |a_n| <= c
        Arguments
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
    numEdges = dag.numEdges
    edges = dag.edges()
    numPaths = len(paths)
    numBasis = len(basis)
    projectConfig = analyzer.projectConfig

    # Set up the linear programming problem.
    logger.info("Number of paths: %d " % numPaths)
    logger.info("Number of basis paths: %d " % numBasis)
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem("BLAH")

    logger.info("Creating variables")
    indices = [(i, j) for i in range(numPaths) for j in range(numBasis)]
    coeffs = pulp.LpVariable.dicts("c", indices, -100, 100)
    absValues = pulp.LpVariable.dicts("abs", indices, 0, 100)
    bound = pulp.LpVariable("bnd", 0, 10000)

    logger.info("Add absolute values")
    for index in indices:
        problem += absValues[index] >= coeffs[index]
        problem += absValues[index] >= -coeffs[index]

    for i in range(numPaths):
        # all coefficients expressing path i
        allCoeffExpressing = [absValues[(i, j)] for j in range(numBasis)]
        problem += pulp.lpSum(allCoeffExpressing) <= bound
        # express path i as a linear combination of basis paths
        for edge in edges:
            pathsContainingEdge = \
                [j for j in range(numBasis) if (edge in basis[j])]
            presentCoeffs = [coeffs[(i, j)] for j in pathsContainingEdge]
            present = 1 if (edge in paths[i]) else 0
            problem += pulp.lpSum(presentCoeffs) == present
    problem += bound
    problem.sense = pulp.LpMinimize
  
    problemStatus = problem.solve(solver=projectConfig.ilpSolver)
    if problemStatus != pulp.LpStatusOptimal:
        logger.info("Minimum value not found.")
        return [], problem
    objValMin = pulp.value(bound)

    logger.info("Minimum value found: %g" % objValMin)

    return objValMin


def findMinimalOvercompleteBasis(analyzer, paths, k):
    """
        This function is here only for test purposes. The functions finds the
        smallest set of 'basis paths' with the following property: Each path pi
        in `paths', can be expressed as a linear combination 
                  pi = a_1 b_1 + ... + a_n b_n
        of paths b_i from `basis`. This function finds the set of basis paths
        such that every path can be expressed as a linear combination of basis
        paths b_i  such that the sum of absolute value of coefficients is at
        most 'k':
           |a_1| + |a_2| + ... + |a_n| <= k
        Arguments
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
 
    dag = analyzer.dag
    source = dag.soure
    sink = dag.sink
    numEdges = dag.numEdges
    edges = dag.edges()
    numPaths = len(paths)

    # Set up the linear programming problem.
    logger.info("Number of paths: %d " % numPaths)
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem(_LP_NAME)

    logger.info("Creating variables")
    indices = [(i, j) for i in range(numPaths) for j in range(numPaths)]
    coeffs = pulp.LpVariable.dicts("c", indices, -k, k)
    absValues = pulp.LpVariable.dicts("abs", indices, 0, k)
    usedPaths = pulp.LpVariable.dicts(
        "used", range(numPaths), 0, 1, pulp.LpBinary)
    
    logger.info("Adding usedPaths")
    for i in range(numPaths):
        for j in range(numPaths):
            problem += k * usedPaths[j] >= absValues[(i,j)]

    logger.info("Add absolute values")
    for index in indices:
        problem += absValues[index] >= coeffs[index]
        problem += absValues[index] >= -coeffs[index]

    for i in range(numPaths):
        logger.info("Processing path number %d" % i)
        # all coefficients expressing path i
        allCoeffExpressing = [absValues[(i, j)] for j in range(numPaths)]
        problem += pulp.lpSum(allCoeffExpressing) <= k
        for edge in edges:
            pathsContainingEdge = \
                [j for j in range(numPaths) if (edge in paths[j])]
            presentCoeffs = [coeffs[(i, j)] for j in pathsContainingEdge]
            present = 1 if (edge in paths[i]) else 0
            problem += pulp.lpSum(presentCoeffs) == present
    objective = pulp.lpSum(usedPaths)
    problem += objective
    problem.sense = pulp.LpMinimize
   
    problemStatus = problem.solve(solver=projectConfig.ilpSolver)
    if problemStatus != pulp.LpStatusOptimal:
        logger.info("Minimum value not found.")
        return [], problem
    objValMin = pulp.value(objective)

    logger.info("Minimum value found: %g" % objValMin)

    solutionPaths = \
        [index for index in range(numPaths) if usedPaths[index].value() == 1]
    return solutionPaths


def findExtremePath(analyzer, extremum=Extremum.LONGEST, interval=None):
    """Determines either the longest or the shortest path through the DAG
    with the constraints stored in the ``Analyzer`` object provided.

    Arguments:
        analyzer:
            ``Analyzer`` object that maintains information about
            the code being analyzed.
        extremum:
            Type of extreme path to calculate.
        interval:
            ``Interval`` object that represents the interval of values
            that the generated paths can have. If no ``Interval`` object
            is provided, the interval of values is considered to be
            all real numbers.

    Returns:
        Tuple whose first element is the longest or the shortest path
        through the DAG, as a list of nodes along the path (ordered
        by traversal from source to sink), and whose second element is
        the integer linear programming problem that was solved to obtain
        the path, as an object of the ``IlpProblem`` class.

        If no such path is feasible, given the constraints stored in
        the ``Analyzer`` object and the ``Interval`` object provided,
        the first element of the tuple is an empty list, and the second
        element of the tuple is an ``IlpProblem`` object whose ``objVal``
        instance variable is None.
    """
    # Make temporary variables for the frequently accessed
    # variables from the ``Analyzer`` object provided.
    projectConfig = analyzer.projectConfig

    dag = analyzer.dag
    source = dag.source
    sink = dag.sink
    numEdges = dag.numEdges

    nodesExceptSourceSink = dag.nodesExceptSourceSink
    edges = dag.allEdges
    edgeWeights = dag.edgeWeights

    pathExclusiveConstraints = analyzer.pathExclusiveConstraints
    pathBundledConstraints = analyzer.pathBundledConstraints

    # Set up the linear programming problem.
    logger.info("Setting up the integer linear programming problem...")
    problem = IlpProblem(_LP_NAME)

    logger.info("Creating the variables and adding the constraints...")

    # Set up the variables that correspond to the flow through each edge.
    # Set each of the variables to be an integer binary variable.
    edgeFlows = pulp.LpVariable.dicts("EdgeFlow", range(0, numEdges),
                                      0, 1, pulp.LpBinary)

    # Add a constraint for the flow from the source. The flow through all of
    # the edges out of the source should sum up to exactly 1.
    edgeFlowsFromSource = _getEdgeFlowVars(analyzer, edgeFlows,
                                           dag.out_edges(source))
    problem += pulp.lpSum(edgeFlowsFromSource) == 1, "Flows from source"

    # Add constraints for the rest of the nodes (except sink). The flow
    # through all of the edges into a node should equal the flow through
    # all of the edges out of the node. Hence, for node n, if e_i and e_j
    # enter a node, and e_k and e_l exit a node, the corresponding flow
    # equation is e_i + e_j = e_k + e_l.
    for node in nodesExceptSourceSink:
        edgeFlowsToNode = _getEdgeFlowVars(analyzer, edgeFlows,
                                           dag.in_edges(node))
        edgeFlowsFromNode = _getEdgeFlowVars(analyzer, edgeFlows,
                                             dag.out_edges(node))
        problem += \
        (pulp.lpSum(edgeFlowsToNode) == pulp.lpSum(edgeFlowsFromNode),
         "Flows through %s" % node)

    # Add a constraint for the flow to the sink. The flow through all of
    # the edges into the sink should sum up to exactly 1.
    edgeFlowsToSink = _getEdgeFlowVars(analyzer, edgeFlows,
                                       dag.in_edges(sink))
    problem += pulp.lpSum(edgeFlowsToSink) == 1, "Flows to sink"

    # Add constraints for the exclusive path constraints. To ensure that
    # the edges in each constraint are not taken together, the total flow
    # through all the edges should add to at least one unit less than
    # the number of edges in the constraint. Hence, if a constraint
    # contains edges e_a, e_b, e_c, then e_a + e_b + e_c must be less than 3.
    # This way, all three of these edges can never be taken together.
    for constraintNum, path in enumerate(pathExclusiveConstraints):
        edgeFlowsInConstraint = _getEdgeFlowVars(analyzer, edgeFlows, path)
        problem += (pulp.lpSum(edgeFlowsInConstraint) <= (len(path)-1),
                    "Path exclusive constraint %d" % (constraintNum+1))

    # Add constraints for the bundled path constraints. If a constraint
    # contains edges e_a, e_b, e_c, e_d, and each edge *must* be taken,
    # then e_b + e_c + e_d must sum up to e_a, scaled by -3 (or one less
    # than the number of edges in the path constraint). Hence, the flow
    # constraint is e_b + e_c + e_d = -3 * e_a. By default, we scale
    # the first edge in a constraint with this negative value.
    for constraintNum, path in enumerate(pathBundledConstraints):
        firstEdge = path[0]
        firstEdgeFlow = _getEdgeFlowVar(analyzer, edgeFlows, firstEdge)
        edgeFlowsForRest = _getEdgeFlowVars(analyzer, edgeFlows, path[1:])
        problem += \
        (pulp.lpSum(edgeFlowsForRest) == (len(path)-1) * firstEdgeFlow,
         "Path bundled constraint %d" % (constraintNum+1))

    # There may be bounds on the values of the paths that are generated
    # by this function: we add constraints for these bounds. For this,
    # we weight the PuLP variables for the edges using the list of
    # edge weights provided, and then impose bounds on the sum.
    weightedEdgeFlowVars = []
    for edgeIndex, edgeFlowVar in edgeFlows.items():
        edgeWeight = edgeWeights[edgeIndex]
        weightedEdgeFlowVars.append(edgeWeight * edgeFlowVar)
    interval = interval or Interval()
    if interval.hasFiniteLowerBound():
        problem += \
        (pulp.lpSum(weightedEdgeFlowVars) >= interval.lowerBound)
    if interval.hasFiniteUpperBound():
        problem += \
        (pulp.lpSum(weightedEdgeFlowVars) <= interval.upperBound)

    logger.info("Variables created and constraints added.")

    logger.info("Constructing the objective function...")
    # Finally, construct and add the objective function.
    # We reuse the constraint (possibly) added in the last step of
    # the constraint addition phase.
    objective = pulp.lpSum(weightedEdgeFlowVars)
    problem += objective
    logger.info("Objective function constructed.")

    logger.info("Finding the maximum value of the objective function...")

    problem.sense = pulp.LpMaximize
    problemStatus = problem.solve(solver=projectConfig.ilpSolver)
    if problemStatus != pulp.LpStatusOptimal:
        logger.info("Maximum value not found.")
        return [], problem
    objValMax = pulp.value(objective)

    logger.info("Maximum value found: %g" % objValMax)

    logger.info("Finding the path that corresponds to the maximum value...")
    # Determine the edges along the extreme path using the solution.
    maxPath = [edges[edgeNum] for edgeNum in edgeFlows
               if edgeFlows[edgeNum].value() == 1]
    logger.info("Path found.")

    logger.info("Finding the minimum value of the objective function...")

    problem.sense = pulp.LpMinimize
    problemStatus = problem.solve(solver=projectConfig.ilpSolver)
    if problemStatus != pulp.LpStatusOptimal:
        logger.info("Minimum value not found.")
        return [], problem
    objValMin = pulp.value(objective)

    logger.info("Minimum value found: %g" % objValMin)

    logger.info("Finding the path that corresponds to the minimum value...")
    # Determine the edges along the extreme path using the solution.
    minPath = [edges[edgeNum] for edgeNum in edgeFlows
               if edgeFlows[edgeNum].value() == 1]
    logger.info("Path found.")

    # Choose the correct extreme path based on the optimal solutions
    # and the type of extreme path required.
    absMax, absMin = abs(objValMax), abs(objValMin)
    if extremum is Extremum.LONGEST:
        extremePath = maxPath if absMax >= absMin else minPath
        problem.sense = (pulp.LpMaximize if absMax >= absMin
                         else pulp.LpMinimize)
        problem.objVal = max(absMax, absMin)
    elif extremum is Extremum.SHORTEST:
        extremePath = minPath if absMax >= absMin else maxPath
        problem.sense = (pulp.LpMinimize if absMax >= absMin
                         else pulp.LpMaximize)
        problem.objVal = min(absMax, absMin)

    # Arrange the nodes along the extreme path in order of traversal
    # from source to sink.
    resultPath = []

    logger.info("Arranging the nodes along the chosen extreme path "
                "in order of traversal...")
    # To do so, first construct a dictionary mapping a node along the path
    # to the edge from that node.
    extremePathDict = {}
    for edge in extremePath:
        extremePathDict[edge[0]] = edge
    # Now, "thread" a path through the dictionary.
    currNode = source
    resultPath.append(currNode)
    while currNode in extremePathDict:
        newEdge = extremePathDict[currNode]
        currNode = newEdge[1]
        resultPath.append(currNode)
    logger.info("Nodes along the chosen extreme path arranged.")

    if projectConfig.debugConfig.KEEP_ILP_SOLVER_OUTPUT:
        _moveIlpFiles(os.getcwd(), projectConfig.locationTempDir)
    else:
        _removeTempIlpFiles()

    # We're done!
    return resultPath, problem

def _moveIlpFiles(sourceDir, destDir):
    """Moves the files that are generated when an integer linear program
    is solved, from the source directory whose location is provided
    to the destination directory whose location is provided.

    Arguments:
        sourceDir:
            Location of the source directory.
        destDir:
            Location of the destination directory.
    """
    moveFiles([_LP_NAME + r"-pulp\.lp", _LP_NAME + r"-pulp\.mps",
               _LP_NAME + r"-pulp\.prt", _LP_NAME + r"-pulp\.sol"],
              sourceDir, destDir)

def _removeTempIlpFiles():
    """Removes the temporary files that are generated when an
    integer linear program is solved.
    """
    removeFiles([r".*\.lp", r".*\.mps", r".*\.prt", r".*\.sol"], os.getcwd())
