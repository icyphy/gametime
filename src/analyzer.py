#!/usr/bin/env python
import os
import shutil
import time
from typing import List, Tuple, Optional

import numpy as np
import networkx as nx

import clang_helper
import nx_helper
import pulp_helper
import inliner
import unroller
from defaults import config, logger
from file_helper import remove_all_except
from gametime_error import GameTimeError
from nx_helper import Dag, write_dag_to_dot_file
from path import Path
from path_analyzer import PathAnalyzer
from project_configuration import ProjectConfiguration
from path_generator import PathGenerator

from numpy import dot, exp, eye
from numpy.linalg import det, inv, slogdet

from backend.flexpret_backend.flexpret_backend import FlexpretBackend
from backend.x86_backend.x86_backend import X86Backend
from backend.arm_backend.arm_backend import ArmBackend
from backend.backend import Backend
from smt_solver.extract_labels import find_labels

"""Defines a class that maintains information about the code being analyzed,
such as the name of the file that contains the code being analyzed and
the basis paths in the code.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""

class Analyzer(object):
    """
    Maintains information about the code being analyzed, such as
    the name of the file that contains the code being analyzed
    and the basis paths of the code.

    Parameters:
        project_config:
            Object that represents the configuration of a GameTime project.
    """

    def __init__(self, project_config: ProjectConfiguration):
        ### CONFIGURATIONS ###
        #: :class:`~gametime.projectConfiguration.ProjectConfiguration` object
        #: that represents the configuration of a GameTime project.
        self.project_config: ProjectConfiguration = project_config

        ### GRAPH INFORMATION ###
        #: Data structure for the DAG of the code being analyzed.
        self.dag: Dag = Dag()

        ### PATHS INFORMATION ###
        #: Dimension of the vector representing each path.
        self.path_dimension: int = 0

        #: Basis matrix.
        self.basis_matrix: Optional[np.ndarray] = None

        #: Set whose elements are lists of edges that must not be taken
        #: together along any path through the DAG. For example, the element
        #: [e1, e2] means "if you take e1, you cannot take e2" and
        #: "if you take e2, you cannot take e1".
        self.path_exclusive_constraints: List[List[Tuple[str, str]]] = []

        #: List whose elements are lists of edges that must be taken together,
        #: if at least one is taken along a path through the DAG. For example,
        #: the element [e1, e2] means "if you take e1, then you take e2".
        self.path_bundled_constraints: List[List[Tuple[str, str]]] = []

        # Number of `bad' rows in the basis matrix.
        self.num_bad_rows: int = 0

        # List of the Path objects associated with all_temp_files basis paths
        # generated so far.
        self.basis_paths: List[Path] = []

        # List of lists, each of which is a list of IDs of the nodes in
        # the DAG along each basis path. Each ID is a string. The lists are
        # arranged in the same order as the Path objects associated with
        # the basis paths are arranged in the `basis_paths' list.
        # This list is maintained for efficiency purposes.
        self.basis_paths_nodes: List[Path] = []

        # Specify default parameters for the values used with
        # --ob_extraction flag. The values are outputted only
        # when the flag is used.
        # Value of mu_max computed for the observed measurements
        self.inferred_mu_max: int = 0
        # The in predictions is error is 2 * inferredMuMax * errorScaleFactor
        self.error_scale_factor: int = 0

        self.dag_path: str = ""

        backend_dict = {
            "flexpret": FlexpretBackend, 
            "x86": X86Backend, 
            "arm": ArmBackend,
            # Keep legacy capitalized names for backward compatibility
            "Flexpret": FlexpretBackend, 
            "X86": X86Backend, 
            "ARM": ArmBackend
        }
        
        if self.project_config.backend not in backend_dict:
            raise GameTimeError("No valid backend specified")
        
        self.backend: Backend = backend_dict[self.project_config.backend](self.project_config)

        # Finally, preprocess the file before analysis.
        self._preprocess()

    def _preprocess(self):
        """
        Preprocesses the file before analysis. The preprocessing steps are:
        1. Create a temporary directory that will contain the files
        generated during analysis.
        2. Copy the source file being analyzed into this temporary directory.
        3. Run CIL on the copied source file to perform, for example, loop
        unrolling and function inlining.
        """
        # Check if the file to be analyzed exists.
        orig_file = self.project_config.location_orig_file
        project_temp_dir = self.project_config.location_temp_dir
        if not os.path.exists(orig_file):
            shutil.rmtree(project_temp_dir)
            err_msg = "File to analyze not found: %s" % orig_file
            raise GameTimeError(err_msg)
        
        # Check if the additional files to be analyzed exists.
        additional_files = self.project_config.location_additional_files
        if additional_files:
            for additional_file in additional_files:
                project_temp_dir = self.project_config.location_temp_dir
                if not os.path.exists(additional_file):
                    shutil.rmtree(project_temp_dir)
                    err_msg = "External File to analyze not found: %s" % additional_file
                    raise GameTimeError(err_msg)

        # Remove any temporary directory created during a previous run
        # of the same GameTime project, and create a fresh new
        # temporary directory.
        if os.path.exists(project_temp_dir):
            if self.project_config.UNROLL_LOOPS:
                # If a previous run of the same GameTime project produced
                # a loop configuration file, and the current run involves
                # unrolling the loops that are configured in the file,
                # do not remove the file.
                remove_all_except([config.TEMP_LOOP_CONFIG], project_temp_dir)
            else:
                remove_all_except([], project_temp_dir)
        else:
            os.mkdir(project_temp_dir)

        os.chmod(project_temp_dir, 0o777) # make dir read and write by everyone

        # Make a temporary copy of the original file to preprocess.
        preprocessed_file = self.project_config.location_temp_file
        shutil.copyfile(orig_file, preprocessed_file)

        processing: str = ""

        processing = clang_helper.compile_to_llvm_for_analysis(self.project_config.location_orig_file, self.project_config.location_temp_dir,
                                                          f"{self.project_config.name_orig_no_extension}_{config.TEMP_SUFFIX}", self.project_config.included, self.project_config.compile_flags)

        additional_files_processing = []
        if additional_files:
            additional_files_processing = clang_helper.compile_list_to_llvm_for_analysis(self.project_config.location_additional_files, self.project_config.location_temp_dir,
                                                        self.project_config.included, self.project_config.compile_flags)
        
        # Preprocessing pass: inline functions.
        if self.project_config.inlined:  # Note: This is made into a bool rather than a list
            processing = self._run_inliner(input_file=processing, additional_files=additional_files_processing)

        # Preprocessing pass: unroll loops.
        if self.project_config.UNROLL_LOOPS:
            processing = self._run_loop_unroller(compiled_file=processing)
        
        # Generate control-flow diagrams (CFGs), which are directed acyclic graphs (DAGs).
        self.dag_path: str = clang_helper.generate_dot_file(processing, self.project_config.location_temp_dir)
        self.preprocessed_path: str = processing
        # We are done with the preprocessing.
        logger.info("Preprocessing complete.")
        logger.info("")

    def _run_loop_unroller(self, compiled_file: str) -> str:
        """
        As part of preprocessing, runs CIL on the source file under
        analysis to unroll loops. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.

        Parameters:
            compiled_file: str :
                Path to the original file.

        Returns:
            Path to unrolled file.
        """
        preprocessed_file: str = self.project_config.location_temp_file

        # Infer the name of the file that results from the CIL preprocessing.
        unrolled_file: str = unroller.unroll(compiled_file, self.project_config.location_temp_dir,
                                                       f"{self.project_config.name_orig_no_extension}")

        logger.info("Preprocessing the file: unrolling loops in the code...")

        if not unrolled_file:
            err_msg = "Error running the loop unroller."
            raise GameTimeError(err_msg)
        else:
            shutil.copyfile(unrolled_file, preprocessed_file)
    
            logger.info("")
            logger.info("Loops in the code have been unrolled.")

            return unrolled_file

    def _run_inliner(self, input_file: str, additional_files: str):
        """
        As part of preprocessing, runs CIL on the source file under
        analysis to inline functions. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.

        Parameters:
            input_file: str :
                Path to input file.

        Returns:
            Path to inlined file.
        """
        preprocessed_file = self.project_config.location_temp_file
        # Infer the name of the file that results from the CIL preprocessing.

        logger.info("Preprocessing the file: inlining...")

        input_files = [input_file] + additional_files
        inlined_file = inliner.inline_functions(input_files, self.project_config.location_temp_dir,
                                                     f"{self.project_config.name_orig_no_extension}", self.project_config.func)
        
        if not inlined_file:
            err_msg = "Error running the inliner."
            raise GameTimeError(err_msg)
        else:
            shutil.copyfile(inlined_file, preprocessed_file)

            logger.info("")
            logger.info("Inlining complete.")

            return inlined_file
        
    ### GRAPH FUNCTIONS ###
    def create_dag(self):
        """
        Creates the DAG corresponding to the code being analyzed
        and dumps the DAG, in DOT format, to a temporary file for further
        analysis. This method also stores a local copy in a data
        structure that represents the DAG.
        """
        logger.info("Generating the DAG and associated information...")

        #TODO: add back construction dag from filepath
        # if nx_helper.construct_dag(self.dag_path):
        #     err_msg = "Error running the Phoenix program analyzer."
        #     raise GameTimeError(err_msg)

        location = os.path.join(self.project_config.location_temp_dir,
                                f".{self.project_config.func}.dot")
        self.load_dag_from_dot_file(location)


        bitcode = []
        for node in self.dag.nodes:
            bitcode.append(self.dag.get_node_label(self.dag.nodes_indices[node]))
        find_labels("".join(bitcode), self.project_config.location_temp_dir)
        logger.info("All possible labels extracted.")


        # special case for single node dag
        if self.dag.num_nodes == 1 and self.dag.num_edges == 0:
            self.path_dimension = 1
            return

        num_edges_reduced = len(self.dag.edges_reduced)
        # Note: The number of feasible basis paths is bounded by (num_edges - num_nodes + 2)
        # (Page 8 of "The Internals of GameTime" by Jonathan Kotker).
        self.path_dimension = self.dag.num_edges - self.dag.num_nodes + 2
        print(f"num_edges_reduced = {num_edges_reduced}, self.path_dimension = {self.path_dimension}")
        if num_edges_reduced != self.path_dimension:
            err_msg = ("The number of non-special edges is different from the dimension of the path.")
            raise GameTimeError(err_msg)

        logger.info("DAG generated.")
        
        logger.info("The control-flow graph has %d nodes and %d edges, with at most %d possible paths." %
                    (self.dag.num_nodes, self.dag.num_edges, self.dag.num_paths))
        logger.info("There are at most %d possible basis paths." % self.path_dimension)
        logger.info("")

    def load_dag_from_dot_file(self, location: str):
        """
        Loads the DAG that corresponds to the code being analyzed from a DOT file.

        Parameters:
            location: str :
                Location of the file.

        """
        self.dag, modified = nx_helper.construct_dag(location)
        print(f"num_edges in load_dag_from_dot_file = {self.dag.num_edges}")
        if modified:
            modified_dag_location = os.path.join(self.project_config.location_temp_dir,
                            f".{self.project_config.func}_modified.dot")
            write_dag_to_dot_file(self.dag, modified_dag_location)
            logger.info("Cycles detected in the DAG. Removed cycles and output modified CFG outputed to folder.")

        # Reset variables of this "Analyzer" object.
        self.reset_path_exclusive_constraints()
        self.reset_path_bundled_constraints()


    ### BASIS MATRIX FUNCTIONS ###
    def _init_basis_matrix(self):
        """Initializes the basis matrix."""
        self.basis_matrix: np.ndarray = eye(self.path_dimension)
        if self.project_config.RANDOMIZE_INITIAL_BASIS:
            self._randomize_basis_matrix()

    def _randomize_basis_matrix(self):
        """
        Randomizes the rows of the basis matrix using
        a Fisher-Yates shuffle.
        
        Precondition: The basis matrix has been initialized.
        """
        for i in range(self.path_dimension, 0, -1):
            j = np.random.randint(i)
            self._swap_basis_matrix_rows(i - 1, j)

    def _swap_basis_matrix_rows(self, i, j):
        """
        Swaps two rows of the basis matrix.

        Parameters:
            i: 
                Index of one row to swap.
            j:
                Index of other row to swap.
        """
        row_to_swap_out = self.basis_matrix[j]
        row_to_swap_in = self.basis_matrix[i]
        row_len = len(row_to_swap_out)

        temp_row_to_swap_out = [0] * row_len
        for k in range(row_len):
            temp_row_to_swap_out[k] = row_to_swap_out[k]
        for k in range(row_len):
            row_to_swap_out[k] = row_to_swap_in[k]
            row_to_swap_in[k] = temp_row_to_swap_out[k]


    ### PATH GENERATION FUNCTIONS ###
    def add_path_exclusive_constraint(self, edges: List[Tuple[str, str]]):
        """
        Adds the edges provided to the list of path-exclusive
        constraints, if not already present. These edges must not
        be taken together along any path through the DAG.

        Parameters:
            edges: List[Tuple[str, str]] :
                List of edges to add to the list of path-exclusive constraints.

        """
        if edges not in self.path_exclusive_constraints:
            self.path_exclusive_constraints.append(edges)

    def add_path_bundled_constraint(self, edges: List[Tuple[str, str]]):
        """
        Adds the edges provided to the list of path-bundled
        constraints, if not already present. These edges must
        be taken together if at least one of them is taken along
        a path through the DAG.
        
        Parameters:
            edges: List[Tuple[str, str]] :
                List of edges to add to the list of path-bundled constraints.

        """
        if edges not in self.path_bundled_constraints:
            self.path_bundled_constraints.append(edges)

    def reset_path_exclusive_constraints(self):
        """Resets the path-exclusive constraints."""
        self.path_exclusive_constraints = []

    def reset_path_bundled_constraints(self):
        """Resets the path-bundled constraints."""
        self.path_bundled_constraints = []

    def _compress_path(self, path_edges: List[Tuple[str, str]]) -> List[float]:
        """
        Compresses the path provided: this method converts
        the provided path to a 0-1 vector that is 1 if a
        'non-special' edge is along the path, and 0 otherwise.

        Parameters:
            path_edges: List[Tuple[str, str]] :
                Edges along the path to represent with 'non-special' edges.

        Returns:
            0-1 vector that is 1 if a `non-special' edge is along the path, and 0 otherwise.
        """
        return [(1.0 if edge in path_edges else 0.0)
                for edge in self.dag.edges_reduced]

    ####### Fuctions to FIX
    def generate_overcomplete_basis(self, k: int):
        """
        Generates an overcomplete basis so that each feasible path can be
           written as a liner combination of the paths in the basis so that the
           L1 norm is at most 'k'. This method is for testing purposes
           only as it exhaustively generates all_temp_files paths in the graph!. Use the
           function below for a scalable version.

        Parameters:
            k: int :
                Maximum value of L1 norm.

        """
        logger.info("Generating all_temp_files paths")
        paths = nx.all_simple_paths(self.dag, self.dag.source, self.dag.sink)
        feasible = list(paths)
        logger.info("Find minimal overcomplete basis")
        pulp_helper.find_minimal_overcomplete_basis(self, feasible, k)


    def iteratively_find_overcomplete_basis(self, initial_paths: List[List[Tuple[str, str]]], k: int):
        """
        Generates overcomplete basis such the lenth of the longest
        feasible path is at most 'k'. The basis is computed by iteratively
        extending the basis with the longest path.  Parameter 'initial_paths'
        specifies the set of paths the iterative algorithm begins with. This
        can be any set of paths, in practice we use the paths generated by
        the standard algorithm.

        Parameters:
            initial_paths: List[List[Tuple[str, str]]] :
                A list of initial paths to begin with.
                
            k: int :
                Maximum value of L1 norm.

        Returns:
            The set of basis paths.
        """
        infeasible = []
        edge_node_paths = initial_paths
        optimal_bound = 1
        start_time = time.perf_counter()
        while True:
            before_time = time.perf_counter()
            length, path, ilp_problem = \
                pulp_helper.find_worst_expressible_path(self, self.basis_paths, 0)
            after_time = time.perf_counter()
            logger.info("Found a candidate path of length %.2f in %d seconds" %
                        (length, after_time - before_time))

            optimal_bound = length
            # if the length of the longest path is within the given bound, stop
            if length <= k: break

            candidate_path_nodes = path
            candidate_path_edges = Dag.get_edges(candidate_path_nodes)

            logger.info("Checking if the found path is feasible...")
            result_path = Path(ilp_problem=ilp_problem, nodes=candidate_path_nodes)
            value = self.measure_path(result_path)
            if value < float('inf'):
                logger.info("Path is feasible.")
                self.basis_paths.append(result_path)
                edge_node_paths.append(candidate_path_edges)
            else:
                logger.info("Path is infeasible.")
                logger.info("Finding the edges to exclude...")
                infeasible.append(candidate_path_edges)
                unsat_core = result_path.smtQuery.unsatCore
                exclude_edges = result_path.get_edges_for_conditions(unsat_core)
                logger.info("Edges to be excluded found.")
                logger.info("Adding a constraint to exclude "
                            "these edges...")
                if len(exclude_edges) > 0:
                    self.add_path_exclusive_constraint(exclude_edges)
                else:
                    self.add_path_exclusive_constraint(candidate_path_edges)
                logger.info("Constraint added.")

        logger.info("Found overcomplete basis of size %d, yielding bound %.2f" %
                    (len(edge_node_paths), optimal_bound))

        self.basis_paths_nodes = [path.nodes for path in self.basis_paths]
        return self.basis_paths

    def  generate_basis_paths(self):
        """
        Generates a list of "Path" objects, each of which represents
        a basis path of the code being analyzed. The basis "Path" objects
        are regenerated each time this method is called.

        Returns:
            List of basis paths of the code being analyzed, each
            represented by an object of the "Path" class.
        """
        basis_paths = []

        if nx_helper.has_cycles(self.dag):
            logger.warning("Loops in the code have been detected.")
            # logger.warning("No basis paths have been generated.")
            return []

        logger.info("Generating the basis paths...")
        logger.info("")
        start_time = time.perf_counter()

        logger.info("Initializing the basis matrix...")
        self._init_basis_matrix()
        logger.info("Basis matrix initialized to")
        logger.info(self.basis_matrix)
        logger.info("")
        logger.info("There are a maximum of %d possible basis paths." %
                    self.path_dimension)
        logger.info("")

        def on_exit(start_time, infeasible):
            """
            Helper function that is called when this method is about to
            return the basis Path objects, and performs the appropriate
            pre-exit cleanup. This inner function will be used in two
            places below, and is defined once to keep the code neat,
            to prevent deeper indentation, and to reduce confusion.

            Parameters:
                start_time :
                    Time when the generation of basis Path objects was started.
                infeasible :
                    Set of infeasible paths.

            Returns:            
                List of basis paths of the code being analyzed, each represented by an object of the Path class.
            """
            self.basis_paths = basis_paths
            self.basis_paths_nodes = [path.nodes for path in basis_paths]
            # self.resetPathExclusiveConstraints()

            logger.info("Time taken to generate paths: %.2f seconds." %
                        (time.perf_counter() - start_time))

            logger.info("Basis paths generated.")

            # If we are computing overcomplete basis, use the computed set as
            # the initial set of paths in the iterative algorithm,
            if self.project_config.OVER_COMPLETE_BASIS:
                logger.info("Iteratively improving the basis")
                for path in infeasible:
                    self.add_path_exclusive_constraint(path)
                edge_paths = \
                    [Dag.get_edges(path.nodes) for path in self.basis_paths]
                result = self.iteratively_find_overcomplete_basis(
                    edge_paths, self.project_config.MAXIMUM_ERROR_SCALE_FACTOR)
                logger.info("Number of paths generated: %d" % len(result))
                logger.info("Time taken to generate paths: %.2f seconds." %
                            (time.perf_counter() - start_time))
                return result
            else:
                return self.basis_paths
            
        if self.path_dimension == 1:
            warn_msg = ("Basis matrix has dimensions 1x1. "
                        "There is only one path through the function "
                        "under analysis, which is the only basis path.")
            logger.warning(warn_msg)   
            
        if self.dag.num_nodes == 1 and self.dag.num_edges == 0:
            warn_msg = "Single node CFD with no edge. Only one possible path."
            logger.warning(warn_msg)
            basis_paths = [Path(nodes=[self.dag.source])]
            return on_exit(start_time, [])
        
        i = 0

        # Collects all_temp_files infeasible paths discovered during the computation
        infeasible = []
        current_row, num_paths_unsat = 0, 0
        while current_row < (self.path_dimension - self.num_bad_rows):
            logger.info("Currently at row %d..." % (current_row + 1))
            logger.info("So far, the bottom %d rows of the basis matrix are `bad'." % self.num_bad_rows)
            logger.info("So far, %d candidate paths were found to be unsatisfiable." % num_paths_unsat)
            logger.info(f"Basis matrix is {self.basis_matrix}")
            logger.info("")

            logger.info("Calculating subdeterminants...")
            if num_paths_unsat == 0:
                # Calculate the subdeterminants only if the replacement of this row has not yet been attempted.
                self.dag.reset_edge_weights()
                self.dag.edge_weights = self._calculate_subdets(current_row)
            logger.info("Calculation complete.")

            logger.info("Finding a candidate path using an integer linear program...")
            logger.info("")
            candidate_path_nodes, ilp_problem = pulp_helper.find_extreme_path(self)
            logger.info("")

            if ilp_problem.obj_val is None:
                logger.info("Unable to find a candidate path to replace row %d." % (current_row + 1))
                logger.info("Moving the bad row to the bottom of the basis matrix.")
                for k in range((current_row + 1), self.path_dimension):
                    self._swap_basis_matrix_rows(k - 1, k)
                self.num_bad_rows += 1
                num_paths_unsat = 0
                continue
            logger.info("Candidate path found.")

            candidate_path_edges = Dag.get_edges(candidate_path_nodes)
            print("candidate_path_edges: ", candidate_path_edges)
            compressed_path = self._compress_path(candidate_path_edges)
            print("compressed_path: ", compressed_path)

            # Temporarily replace the row in the basis matrix to calculate the new determinant.
            prev_matrix_row = self.basis_matrix[current_row].copy()
            self.basis_matrix[current_row] = compressed_path
            sign, new_basis_matrix_log_det = slogdet(self.basis_matrix)
            new_basis_matrix_det = exp(new_basis_matrix_log_det)
            logger.info("Absolute value of the new determinant: %g" % new_basis_matrix_det)
            logger.info("")

            DETERMINANT_THRESHOLD = self.project_config.DETERMINANT_THRESHOLD
            MAX_INFEASIBLE_PATHS = self.project_config.MAX_INFEASIBLE_PATHS
            if ((sign == 0 and new_basis_matrix_log_det == float("-inf")) or
                    new_basis_matrix_det < DETERMINANT_THRESHOLD or
                    num_paths_unsat >= MAX_INFEASIBLE_PATHS):  # If row is bad
                
                if (new_basis_matrix_det < DETERMINANT_THRESHOLD and not (sign == 0 and new_basis_matrix_log_det == float("-inf"))):
                    logger.info("Determinant is too small.")
                else:
                    logger.info("Unable to find a path that makes the determinant non-zero.")

                logger.info("Moving the bad row to the bottom of the basis matrix.")

                self.basis_matrix[current_row] = prev_matrix_row
                for k in range((current_row + 1), self.path_dimension):
                    self._swap_basis_matrix_rows(k - 1, k)
                self.num_bad_rows += 1
                num_paths_unsat = 0
            else:  # Row is good, check feasibility
                logger.info("Possible replacement for row found.")
                logger.info("Checking if replacement is feasible...")
                logger.info("")
                result_path = Path(ilp_problem=ilp_problem, nodes=candidate_path_nodes)
  
                # feasibility test
                value = self.measure_path(result_path, f'gen-basis-path-row{current_row}-attempt{i}')
                i += 1
                if value < float('inf'):
                    # Sanity check:
                    # A row should not be replaced if it replaces a good row and decreases the determinant. However, replacing a bad row and decreasing the determinant is okay. (TODO: Are we actually doing this?)
                    logger.info("Replacement is feasible.")
                    logger.info("Row %d replaced." % (current_row + 1))
                    basis_paths.append(result_path)
                    current_row += 1
                    num_paths_unsat = 0
                else:
                    logger.info("Replacement is infeasible.")
                    logger.info("Adding a constraint to exclude these edges...")
                    self.add_path_exclusive_constraint(candidate_path_edges)
                    infeasible.append(candidate_path_edges)
                    logger.info("Constraint added.")
                    self.basis_matrix[current_row] = prev_matrix_row
                    num_paths_unsat += 1

            logger.info("")
            logger.info("")

        if self.project_config.PREVENT_BASIS_REFINEMENT:
            return on_exit(start_time, infeasible)

        logger.info("Refining the basis into a 2-barycentric spanner...")
        logger.info("")
        is_two_barycentric = False
        refinement_round = 0
        while not is_two_barycentric:
            logger.info("Currently in round %d of refinement..." % (refinement_round + 1))
            logger.info("")

            is_two_barycentric = True
            current_row, num_paths_unsat = 0, 0
            good_rows = (self.path_dimension - self.num_bad_rows)
            while current_row < good_rows:
                logger.info("Currently at row %d out of %d..." % (current_row + 1, good_rows))
                logger.info("So far, %d candidate paths were found to be unsatisfiable." % num_paths_unsat)
                logger.info(f"Basis matrix is {self.basis_matrix}")
                logger.info("")

                logger.info("Calculating subdeterminants...")
                if num_paths_unsat == 0:
                    # Calculate the subdeterminants only if the replacement of this row has not yet been attempted.
                    self.dag.reset_edge_weights()
                    self.dag.edge_weights = self._calculate_subdets(current_row)
                logger.info("Calculation complete.")

                logger.info("Finding a candidate path using an integer linear program...")
                logger.info("")
                candidate_path_nodes, ilp_problem = pulp_helper.find_extreme_path(self)
                logger.info("")

                if ilp_problem.obj_val is None:
                    logger.info("Unable to find a candidate path to replace row %d." % (current_row + 1))
                    current_row += 1
                    num_paths_unsat = 0
                    continue

                logger.info("Candidate path found.")
                candidate_path_edges = Dag.get_edges(candidate_path_nodes)
                compressed_path = self._compress_path(candidate_path_edges)

                sign, old_basis_matrix_log_det = slogdet(self.basis_matrix)
                old_basis_matrix_det = exp(old_basis_matrix_log_det)
                logger.info("Absolute value of the old determinant: %g" % old_basis_matrix_det)

                # Temporarily replace the row in the basis matrix
                # to calculate the new determinant.
                prev_matrix_row = self.basis_matrix[current_row].copy()
                self.basis_matrix[current_row] = compressed_path
                sign, new_basis_matrix_log_det = slogdet(self.basis_matrix)
                new_basis_matrix_det = exp(new_basis_matrix_log_det)
                logger.info("Absolute value of the new determinant: %g" % new_basis_matrix_det)

                if new_basis_matrix_det > 2 * old_basis_matrix_det:
                    logger.info("Possible replacement for row found.")
                    logger.info("Checking if replacement is feasible...")
                    logger.info("")
                    result_path = Path(ilp_problem=ilp_problem, nodes=candidate_path_nodes)
                    basis_paths[current_row] = result_path
                    current_row += 1
                    num_paths_unsat = 0
                    
                    #feasibility test
                    value = self.measure_path(result_path, f'gen-basis-path-replace-candid-{current_row+1}-{good_rows}')

                    if value < float('inf'):
                        logger.info("Replacement is feasible.")
                        is_two_barycentric = False
                        basis_paths[current_row] = result_path
                        logger.info("Row %d replaced." % (current_row + 1))
                        current_row += 1
                        num_paths_unsat = 0
                    else:
                        logger.info("Replacement is infeasible.")
                        self.add_path_exclusive_constraint(candidate_path_edges)
                        logger.info("Adding a constraint to exclude these edges...")
                        infeasible.append(candidate_path_edges)
                        logger.info("Constraint added.")
                        self.basis_matrix[current_row] = prev_matrix_row
                        num_paths_unsat += 1

                else:
                    logger.info("No replacement for row %d found." % (current_row + 1))
                    self.basis_matrix[current_row] = prev_matrix_row
                    current_row += 1
                    num_paths_unsat = 0

                logger.info("")
                logger.info("")

            refinement_round += 1
            logger.info("")

        logger.info("Basis refined.")
        return on_exit(start_time, infeasible)

    ### PATH GENERATION HELPER FUNCTIONS ###
    def _calculate_subdets(self, row: int) -> List[int]:
        """
        Returns a list of weights, where weight i is assigned to
        edge i. The weights assigned to the `non-special' edges are
        subdeterminants of the basis matrix without row i and column j:
        column j corresponds to the `non-special' edge j.

        Parameters:
            row: int :
                Row to ignore.

        Returns:
            List of weights as specified above.
        """
        edges_reduced = self.dag.edges_reduced
        edges_reduced_indices = self.dag.edges_reduced_indices

        edge_weight_list = [0] * self.dag.num_edges

        row_list = list(range(self.path_dimension))
        row_list.remove(row)

        for j in range(self.path_dimension):
            col_list = list(range(self.path_dimension))
            col_list.remove(j)
            sub_matrix = self.basis_matrix[row_list][:, col_list]

            if sub_matrix.size != 0:
                # Compute the subdeterminant of this submatrix.
                subdet = det(sub_matrix)
                if ((row + j) % 2) == 1:
                    edge_weight = -1 * subdet
                else:
                    edge_weight = subdet
            else:
                # Special case of a 1x1 matrix, or of code under analysis
                # with only one path that goes through.
                edge_weight = 1

            # Assign this edge weight to the proper `non-special' edge.
            edge_weight_list[edges_reduced_indices[edges_reduced[j]]] = edge_weight

        return edge_weight_list


    def estimate_edge_weights(self):
        """
        Estimates the weights on the edges of the DAG, using the values
        of the basis "Path" objects. The result is stored in the instance
        variable "edgeWeights".
        
        Precondition: The basis paths have been generated and have values.
        """
        self.dag.reset_edge_weights()

        basis_values = [basis_path.measured_value for basis_path
                        in self.basis_paths]
        # By default, we assume a value of 0 for each of the rows in
        # the basis matrix that no replacement could be found for
        # (the `bad' rows in the basis matrix).
        basis_values += [0] * (self.path_dimension - len(basis_values))

        # Estimate the weights on the `non-special' edges of the graph.
        logger.info("Estimating the weights on the `non-special' edges...")
        reduced_edge_weights = dot(inv(self.basis_matrix), basis_values)
        logger.info("Weights estimated.")

        # Generate the list of edge weights that the integer linear
        # programming problem will use.
        logger.info("Generating the list of weights on all_temp_files edges...")
        for reduced_edge_index, reduced_edge in enumerate(self.dag.edges_reduced):
            self.dag.edge_weights[self.dag.edges_reduced_indices[reduced_edge]] = \
                reduced_edge_weights[reduced_edge_index]
        logger.info("List generated.")

    def generate_paths(self, *args, **kwargs):
        return PathGenerator.generate_paths(self, *args, **kwargs)

    ### MEASUREMENT FUNCTIONS ####
    def measure_basis_paths(self):
        """Measure all generated BASIS_PATHS again
        """
        for i in range(len(self.basis_paths)):
            p: Path = self.basis_paths[i]
            self.measure_path(p, f"basis_path{i}")

    def measure_path(self, path: Path, output_name: str) -> int:
        """
        Measure the Path if never measured before. If no name was set, the parameter output_name is used. 

        Parameters:
            path: Path :
                The path object
            output_name: str :
                Name for this path.

        Returns:
            Measured cycle count for PATH.
        """

        if path.path_analyzer == None or path.name != output_name:
            path.name = output_name
            path_analyzer: PathAnalyzer = PathAnalyzer(self.preprocessed_path, self.project_config, self.dag, path, output_name)
            path.path_analyzer = path_analyzer
            
            path_analyzer = path.path_analyzer
            value: int = path.measured_value
            value = max(value, path_analyzer.measure_path(self.backend))
            path.set_measured_value(value)
        return path.measured_value

    def measure_paths(self, paths: list[Path], output_name_prefix: str) -> int:
        """
        Measure the list of PATHS. Using prefix and index as name if none is given.
        
        Parameters:
            paths: list[Path] :
                List of paths to measure.
            output_name_prefix: str :
                Prefix to use for the name of each path

        Returns:
            List of measured values for the paths.
        """
        result = []
        for i in range(len(paths)):
            output_name: str = f'{output_name_prefix}{i}'
            result.append(self.measure_path(paths[i], output_name))
        return result

