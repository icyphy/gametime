#!/usr/bin/env python
import os
import shutil
import time
from copy import deepcopy
from random import random
from typing import List, Set, Tuple, Optional

import numpy as np
import networkx as nx

import clang_helper
import file_helper
import nx_helper
import pulp_helper
from defaults import config, logger
from file_helper import remove_all_except
from gametime_error import GameTimeError
from nx_helper import Dag
from path import Path
from project_configuration import ProjectConfiguration

from numpy import dot, exp, eye, genfromtxt, savetxt
from numpy.linalg import det, inv, slogdet

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
    """Maintains information about the code being analyzed, such as
    the name of the file that contains the code being analyzed
    and the basis paths of the code.

    Attributes:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
    """

    def __init__(self, project_config: ProjectConfiguration):
        ### CONFIGURATIONS ###
        #: :class:`~gametime.projectConfiguration.ProjectConfiguration` object
        #: that represents the configuration of a GameTime project.
        self.projectConfig: ProjectConfiguration = project_config

        ### GRAPH INFORMATION ###
        #: Data structure for the DAG of the code being analyzed.
        self.dag: Dag = Dag()

        ### PATHS INFORMATION ###
        #: Dimension of the vector representing each path.
        self.pathDimension: int = 0

        #: Basis matrix.
        self.basisMatrix: Optional[np.ndarray] = None

        #: Set whose elements are lists of edges that must not be taken
        #: together along any path through the DAG. For example, the element
        #: [e1, e2] means "if you take e1, you cannot take e2" and
        #: "if you take e2, you cannot take e1".
        self.pathExclusiveConstraints: List[List[Tuple[str, str]]] = []

        #: List whose elements are lists of edges that must be taken together,
        #: if at least one is taken along a path through the DAG. For example,
        #: the element [e1, e2] means "if you take e1, then you take e2".
        self.pathBundledConstraints: List[List[Tuple[str, str]]] = []

        # Number of `bad' rows in the basis matrix.
        self.numBadRows: int = 0

        # List of the Path objects associated with all basis paths
        # generated so far.
        self.basisPaths = []

        # List of lists, each of which is a list of IDs of the nodes in
        # the DAG along each basis path. Each ID is a string. The lists are
        # arranged in the same order as the Path objects associated with
        # the basis paths are arranged in the `basisPaths' list.
        # This list is maintained for efficiency purposes.
        self.basisPathsNodes = []

        # Specify default parameters for the values used with
        # --ob_extraction flag. The values are outputted only
        # when the flag is used.
        # Value of mu_max computed for the observed measurements
        self.inferredMuMax: int = 0
        # The in predictions is error is 2 * inferredMuMax * errorScaleFactor
        self.errorScaleFactor: int = 0

        # Finally, preprocess the file before analysis.
        self._preprocess()

    def _preprocess(self):
        """Preprocesses the file before analysis. The preprocessing steps are:
        1. Create a temporary directory that will contain the files
        generated during analysis.
        2. Copy the source file being analyzed into this temporary directory.
        3. Run CIL on the copied source file to perform, for example, loop
        unrolling and function inlining.
        """
        # Check if the file to be analyzed exists.
        orig_file = self.projectConfig.locationOrigFile
        project_temp_dir = self.projectConfig.locationTempDir
        if not os.path.exists(orig_file):
            shutil.rmtree(project_temp_dir)
            err_msg = "File to analyze not found: %s" % orig_file
            raise GameTimeError(err_msg)

        # Remove any temporary directory created during a previous run
        # of the same GameTime project, and create a fresh new
        # temporary directory.
        if os.path.exists(project_temp_dir):
            if self.projectConfig.UNROLL_LOOPS:
                # If a previous run of the same GameTime project produced
                # a loop configuration file, and the current run involves
                # unrolling the loops that are configured in the file,
                # do not remove the file.
                remove_all_except([config.TEMP_LOOP_CONFIG], project_temp_dir)
            else:
                remove_all_except([], project_temp_dir)
        else:
            os.mkdir(project_temp_dir)

        # Make a temporary copy of the original file to preprocess.
        preprocessed_file = self.projectConfig.locationTempFile
        shutil.copyfile(orig_file, preprocessed_file)

        # TODO: Make merger work
        # # Preprocessing pass: merge other source files.
        # if len(self.projectConfig.merged) > 0:
        #     self._run_merger()

        if True:  # TODO: Make this depend on project configuration
            processing: str = clang_helper.compile_to_llvm(self.projectConfig)

        # Preprocessing pass: inline functions.
        if self.projectConfig.inlined:  # Note: This is made into a bool rather than a list
            processing = self._run_inliner(input_file=processing)

        # Preprocessing pass: unroll loops.
        if self.projectConfig.UNROLL_LOOPS:
            processing = self._run_loop_unroller(compiled_file=processing)

        # TODO: Not sure what this entials and what we need to do here.
        # Preprocessing pass: run the file through CIL once more,
        # to reduce the C file to the subset of constructs used by CIL
        # for ease of analysis.
        # self._runCil()

        # We are done with the preprocessing.
        logger.info("Preprocessing complete.")
        logger.info("")

    ### PREPROCESSING HELPER FUNCTIONS ###
    # TODO: Make this work (see self._preprocess)
    # def _run_merger(self):
    #     """As part of preprocessing, runs CIL on the source file under
    #     analysis to merge other source files. A copy of the file that
    #     results from the CIL preprocessing is made and renamed for use by
    #     other preprocessing phases, and the file itself is renamed and
    #     stored for later perusal.
    #     """
    #     preprocessed_file: str = self.projectConfig.locationTempFile
    #     # Infer the name of the file that results from the CIL preprocessing.
    #     cil_file = "%s.cil.c" % self.projectConfig.locationTempNoExtension
    #
    #     logger.info("Preprocessing the file: merging other source files...")
    #
    #     if merger.runMerger(self.projectConfig):
    #         errMsg = "Error running the merger."
    #         raise GameTimeError(errMsg)
    #     else:
    #         shutil.copyfile(cil_file, preprocessed_file)
    #         shutil.move(cil_file,
    #                     "%s%s.c" % (self.projectConfig.locationTempNoExtension,
    #                                 config.TEMP_SUFFIX_MERGED))
    #         if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
    #             cilHelper.removeTempCilFiles(self.projectConfig)
    #
    #         logger.info("")
    #         logger.info("Other source files merged.")

    def _run_loop_unroller(self, compiled_file: str = None):
        """As part of preprocessing, runs CIL on the source file under
        analysis to unroll loops. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.
        """
        preprocessed_file: str = self.projectConfig.locationTempFile

        if not compiled_file:
            compiled_file = self.projectConfig.get_temp_filename_with_extension(".bc", "compile-gt")
        # Infer the name of the file that results from the CIL preprocessing.
        unrolled_file: str = clang_helper.unroll_loops(compiled_file, self.projectConfig)

        logger.info("Preprocessing the file: unrolling loops in the code...")

        if not unrolled_file:
            err_msg = "Error running the loop unroller."
            raise GameTimeError(err_msg)
        else:
            shutil.copyfile(unrolled_file, preprocessed_file)
            shutil.move(unrolled_file,
                        "%s%s.bt" % (self.projectConfig.locationTempNoExtension,
                                     config.TEMP_SUFFIX_UNROLLED))
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                clang_helper.remove_temp_cil_files(self.projectConfig)

            logger.info("")
            logger.info("Loops in the code have been unrolled.")
            return "%s%s.bt" % (self.projectConfig.locationTempNoExtension,
                                config.TEMP_SUFFIX_UNROLLED)

    def _run_inliner(self, input_file: str = None):
        """As part of preprocessing, runs CIL on the source file under
        analysis to inline functions. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.
        """
        preprocessed_file = self.projectConfig.locationTempFile
        # Infer the name of the file that results from the CIL preprocessing.

        if not input_file:
            input_file = self.projectConfig.get_temp_filename_with_extension(".bc", "inlined-gt")

        logger.info("Preprocessing the file: inlining...")

        inlined_file = clang_helper.inline_functions(input_file, self.projectConfig)
        if not inlined_file:
            err_msg = "Error running the inliner."
            raise GameTimeError(err_msg)
        else:
            shutil.copyfile(inlined_file, preprocessed_file)
            shutil.move(inlined_file,
                        "%s%s.bt" % (self.projectConfig.locationTempNoExtension,
                                     config.TEMP_SUFFIX_INLINED))
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                clang_helper.remove_temp_cil_files(self.projectConfig)

            logger.info("")
            logger.info("Inlining complete.")
            return "%s%s.bt" % (self.projectConfig.locationTempNoExtension,
                                config.TEMP_SUFFIX_INLINED)

    # TODO: Figure out what this is supposed to do (see self._preprocess)
    # def _runCil(self):
    #     """As part of preprocessing, runs CIL on the source file under
    #     analysis to to reduce the C file to the subset of constructs
    #     used by CIL for ease of analysis. The file that results from
    #     the CIL preprocessing is renamed for use by the rest of
    #     the GameTime toolflow. Another copy, with preprocessor directives
    #     that maintain the line numbers from the original source file
    #     (and other merged source files), is also made.
    #     """
    #     preprocessedFile = self.projectConfig.locationTempFile
    #     # Infer the name of the file that results from the CIL preprocessing.
    #     cilFile = "%s.cil.c" % self.projectConfig.locationTempNoExtension
    #
    #     logger.info("Preprocessing the file: running CIL to produce code "
    #                 "simplified for analysis...")
    #
    #     if cilHelper.runCil(self.projectConfig, keepLineNumbers=True):
    #         errMsg = "Error running CIL in the final preprocessing phase."
    #         raise GameTimeError(errMsg)
    #     else:
    #         shutil.move(cilFile,
    #                     "%s%s.c" % (self.projectConfig.locationTempNoExtension,
    #                                 config.TEMP_SUFFIX_LINE_NUMS))
    #         if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
    #             cilHelper.removeTempCilFiles(self.projectConfig)
    #
    #     if cilHelper.runCil(self.projectConfig):
    #         errMsg = "Error running CIL in the final preprocessing phase."
    #         raise GameTimeError(errMsg)
    #     else:
    #         shutil.move(cilFile, preprocessedFile)
    #         if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
    #             cilHelper.removeTempCilFiles(self.projectConfig)
    #
    #     logger.info("")
    #     logger.info("Final preprocessing phase complete.")

    ### BASIS MATRIX FUNCTIONS ###
    def _init_basis_matrix(self):
        """Initializes the basis matrix."""
        self.basisMatrix: np.ndarray = eye(self.pathDimension)
        if self.projectConfig.RANDOMIZE_INITIAL_BASIS:
            self._randomize_basis_matrix()

    def _randomize_basis_matrix(self):
        """Randomizes the rows of the basis matrix using
        a Fisher-Yates shuffle.

        Precondition: The basis matrix has been initialized.
        """
        for i in range(self.pathDimension, 0, -1):
            j = np.random.randint(i)
            self._swap_basis_matrix_rows(i - 1, j)

    def _swap_basis_matrix_rows(self, i, j):
        """Swaps two rows of the basis matrix.

        @param i Index of one row to swap.
        @param j Index of other row to swap.
        """
        row_to_swap_out = self.basisMatrix[j]
        row_to_swap_in = self.basisMatrix[i]
        row_len = len(row_to_swap_out)

        temp_row_to_swap_out = [0] * row_len
        for k in range(row_len):
            temp_row_to_swap_out[k] = row_to_swap_out[k]
        for k in range(row_len):
            row_to_swap_out[k] = row_to_swap_in[k]
            row_to_swap_in[k] = temp_row_to_swap_out[k]

    ### PATH GENERATION FUNCTIONS ###
    def add_path_exclusive_constraint(self, edges: List[Tuple[str, str]]):
        """Adds the edges provided to the list of path-exclusive
        constraints, if not already present. These edges must not
        be taken together along any path through the DAG.

        @param edges List of edges to add to the list of
        path-exclusive constraints.
        """
        if edges not in self.pathExclusiveConstraints:
            self.pathExclusiveConstraints.append(edges)

    def add_path_bundled_constraint(self, edges: List[Tuple[str, str]]):
        """Adds the edges provided to the list of path-bundled
        constraints, if not already present. These edges must
        be taken together if at least one of them is taken along
        a path through the DAG.

        @param edges List of edges to add to the list of path-bundled
        constraints.
        """
        if edges not in self.pathBundledConstraints:
            self.pathBundledConstraints.append(edges)

    def reset_path_exclusive_constraints(self):
        """Resets the path-exclusive constraints."""
        self.pathExclusiveConstraints = []

    def reset_path_bundled_constraints(self):
        """Resets the path-bundled constraints."""
        self.pathBundledConstraints = []

    def _compress_path(self, path_edges: List[Tuple[str, str]]) -> List[float]:
        """Compresses the path provided: this method converts
        the provided path to a 0-1 vector that is 1 if a
        'non-special' edge is along the path, and 0 otherwise.

        @param path_edges Edges along the path to represent with
        'non-special' edges.
        @retval 0-1 vector that is 1 if a `non-special' edge is along
        the path, and 0 otherwise.
        """
        return [(1.0 if edge in path_edges else 0.0)
                for edge in self.dag.edgesReduced]

    ####### Fuctions to FIX
    def generate_overcomplete_basis(self, k: int):
        """Generates an overcomplete basis so that each feasible path can be
           written as a liner combination of the paths in the basis so that the
           L1 norm is at most 'k'. This method is for testing purposes
           only as it exhaustively generates all paths in the graph!. Use the
           function below for a scalable version.
        """
        logger.info("Generating all paths")
        paths = nx.all_simple_paths(self.dag, self.dag.source, self.dag.sink)
        feasible = list(paths)
        logger.info("Find minimal overcomplete basis")
        pulp_helper.find_minimal_overcomplete_basis(self, feasible, k)

    def iteratively_find_overcomplete_basis(self, initial_paths: List[List[Tuple[str, str]]], k: int):
        """Generates overcomplete basis such the lenth of the longest
           feasible path is at most 'k'. The basis is computed by iteratively
           extending the basis with the longest path.  Parameter 'initial_paths'
           specifies the set of paths the iterative algorithm begins with. This
           can be any set of paths, in practice we use the paths generated by
           the standard algorithm.
        """
        infeasible = []
        edge_node_paths = initial_paths
        optimal_bound = 1
        start_time = time.perf_counter()
        while True:
            before_time = time.perf_counter()
            length, path, ilp_problem = \
                pulp_helper.find_worst_expressible_path(self, self.basisPaths, 0)
            after_time = time.perf_counter()
            logger.info("Found a candidate path of length %.2f in %d seconds" %
                        (length, after_time - before_time))

            optimal_bound = length
            # if the length of the longest path is within the given bound, stop
            if length <= k: break

            candidate_path_nodes = path
            candidate_path_edges = Dag.get_edges(candidate_path_nodes)

            # TODO: add feasibility
            edge_node_paths.append(candidate_path_edges)
            result_path = Path(ilp_problem=ilp_problem, nodes=candidate_path_nodes)
            self.basisPaths.append(result_path)
            edge_node_paths.append(candidate_path_edges)
            # logger.info("Checking if the found path is feasible...")
            # result_path = self.check_feasibility(candidate_path_nodes,
            #                                      ilp_problem)
            # query_satisfiability = result_path.smtQuery.satisfiability
            # if query_satisfiability == Satisfiability.SAT:
            #     logger.info("Path is feasible.")
            #     self.basisPaths.append(result_path)
            #     edge_node_paths.append(candidate_path_edges)
            # elif query_satisfiability == Satisfiability.UNSAT:
            #     logger.info("Path is infeasible.")
            #     logger.info("Finding the edges to exclude...")
            #     infeasible.append(candidate_path_edges)
            #     unsat_core = result_path.smtQuery.unsatCore
            #     exclude_edges = result_path.get_edges_for_conditions(unsat_core)
            #     logger.info("Edges to be excluded found.")
            #     logger.info("Adding a constraint to exclude "
            #                 "these edges...")
            #     if len(exclude_edges) > 0:
            #         self.add_path_exclusive_constraint(exclude_edges)
            #     else:
            #         self.add_path_exclusive_constraint(candidate_path_edges)
            #     logger.info("Constraint added.")

        logger.info("Found overcomplete basis of size %d, yielding bound %.2f" %
                    (len(edge_node_paths), optimal_bound))

        self.basisPathsNodes = [path.nodes for path in self.basisPaths]
        return self.basisPaths

    def generate_basis_paths(self):
        """Generates a list of "Path" objects, each of which represents
        a basis path of the code being analyzed. The basis "Path" objects
        are regenerated each time this method is called.

        @retval List of basis paths of the code being analyzed, each
        represented by an object of the "Path" class.
        """
        basis_paths = []

        if nx_helper.has_cycles(self.dag):
            logger.warning("Loops in the code have been detected.")
            logger.warning("No basis paths have been generated.")
            return []

        logger.info("Generating the basis paths...")
        logger.info("")
        start_time = time.perf_counter()

        logger.info("Initializing the basis matrix...")
        self._init_basis_matrix()
        logger.info("Basis matrix initialized to")
        logger.info(self.basisMatrix)
        logger.info("")
        logger.info("There are a maximum of %d possible basis paths." %
                    self.pathDimension)
        logger.info("")

        def on_exit(start_time, infeasible):
            """Helper function that is called when this method is about to
            return the basis Path objects, and performs the appropriate
            pre-exit cleanup. This inner function will be used in two
            places below, and is defined once to keep the code neat,
            to prevent deeper indentation, and to reduce confusion.

            @param start_time Time when the generation of basis Path objects
                was started.
            @retval List of basis paths of the code being analyzed, each
                represented by an object of the Path class.
            """
            self.basisPaths = basis_paths
            self.basisPathsNodes = [path.nodes for path in basis_paths]
            # self.resetPathExclusiveConstraints()

            logger.info("Time taken to generate paths: %.2f seconds." %
                        (time.perf_counter() - start_time))

            logger.info("Basis paths generated.")

            # If we are computing overcomplete basis, use the computed set as
            # the initial set of paths in the iterative algorithm,
            if self.projectConfig.OVER_COMPLETE_BASIS:
                logger.info("Iteratively improving the basis")
                for path in infeasible:
                    self.add_path_exclusive_constraint(path)
                edge_paths = \
                    [Dag.get_edges(path.nodes) for path in self.basisPaths]
                result = self.iteratively_find_overcomplete_basis(
                    edge_paths, self.projectConfig.MAXIMUM_ERROR_SCALE_FACTOR)
                logger.info("Number of paths generated: %d" % len(result))
                logger.info("Time taken to generate paths: %.2f seconds." %
                            (time.perf_counter() - start_time))
                return result
            else:
                return self.basisPaths

        if self.pathDimension == 1:
            warn_msg = ("Basis matrix has dimensions 1x1. "
                        "There is only one path through the function "
                        "under analysis, which is the only basis path.")
            logger.warn(warn_msg)

        # Collects all infeasible paths discovered during the computation
        infeasible = []
        current_row, num_paths_unsat = 0, 0
        while current_row < (self.pathDimension - self.numBadRows):
            logger.info("Currently at row %d..." % (current_row + 1))
            logger.info("So far, the bottom %d rows of the basis "
                        "matrix are `bad'." % self.numBadRows)
            logger.info("So far, %d candidate paths were found to be "
                        "unsatisfiable." % num_paths_unsat)
            logger.info("Basis matrix is")
            logger.info(self.basisMatrix)
            logger.info("")

            logger.info("Calculating subdeterminants...")
            if num_paths_unsat == 0:
                # Calculate the subdeterminants only if the replacement
                # of this row has not yet been attempted.
                self.dag.reset_edge_weights()
                self.dag.edgeWeights = self._calculate_subdets(current_row)
            logger.info("Calculation complete.")

            logger.info("Finding a candidate path using an integer "
                        "linear program...")
            logger.info("")
            candidate_path_nodes, ilp_problem = pulp_helper.find_extreme_path(self)
            logger.info("")

            if ilp_problem.objVal is None:
                logger.info("Unable to find a candidate path to "
                            "replace row %d." % (current_row + 1))
                logger.info("Moving the bad row to the bottom "
                            "of the basis matrix.")
                for k in range((current_row + 1), self.pathDimension):
                    self._swap_basis_matrix_rows(k - 1, k)
                self.numBadRows += 1
                num_paths_unsat = 0
                continue

            logger.info("Candidate path found.")
            candidate_path_edges = Dag.get_edges(candidate_path_nodes)
            compressed_path = self._compress_path(candidate_path_edges)

            # Temporarily replace the row in the basis matrix
            # to calculate the new determinant.
            prev_matrix_row = self.basisMatrix[current_row].copy()
            self.basisMatrix[current_row] = compressed_path
            sign, new_basis_matrix_log_det = slogdet(self.basisMatrix)
            new_basis_matrix_det = exp(new_basis_matrix_log_det)
            logger.info("Absolute value of the new determinant: %g" %
                        new_basis_matrix_det)
            logger.info("")

            DETERMINANT_THRESHOLD = self.projectConfig.DETERMINANT_THRESHOLD
            MAX_INFEASIBLE_PATHS = self.projectConfig.MAX_INFEASIBLE_PATHS
            if ((sign == 0 and new_basis_matrix_log_det == float("-inf")) or
                    new_basis_matrix_det < DETERMINANT_THRESHOLD or
                    num_paths_unsat >= MAX_INFEASIBLE_PATHS):  # If row is bad
                if (new_basis_matrix_det < DETERMINANT_THRESHOLD and
                        not (sign == 0 and new_basis_matrix_log_det == float("-inf"))):
                    logger.info("Determinant is too small.")
                else:
                    logger.info("Unable to find a path that makes "
                                "the determinant non-zero.")
                logger.info("Moving the bad row to the bottom "
                            "of the basis matrix.")
                self.basisMatrix[current_row] = prev_matrix_row
                for k in range((current_row + 1), self.pathDimension):
                    self._swap_basis_matrix_rows(k - 1, k)
                self.numBadRows += 1
                num_paths_unsat = 0
            else:  # Row is good, check feasibility
                logger.info("Possible replacement for row found.")
                # logger.info("Checking if replacement is feasible...")
                logger.info("")
                result_path = Path(ilp_problem=ilp_problem, nodes=candidate_path_nodes)
                basis_paths.append(result_path)
                current_row += 1
                num_paths_unsat = 0
                # result_path = self.check_feasibility(candidate_path_nodes,
                #                                      ilp_problem)
                # query_satisfiability = result_path.smtQuery.satisfiability
                # if query_satisfiability == Satisfiability.SAT:  # Replace and move on
                #     # Sanity check:
                #     # A row should not be replaced if it replaces a good
                #     # row and decreases the determinant. However,
                #     # replacing a bad row and decreasing the determinant
                #     # is okay. (TODO: Are we actually doing this?)
                #     logger.info("Replacement is feasible.")
                #     logger.info("Row %d replaced." % (current_row + 1))
                #
                #     basis_paths.append(result_path)
                #     current_row += 1
                #     num_paths_unsat = 0
                # elif query_satisfiability == Satisfiability.UNSAT:
                #     # loops back and tries again with current row
                #     logger.info("Replacement is infeasible.")
                #     logger.info("Finding the edges to exclude...")
                #     unsat_core = result_path.smtQuery.unsatCore
                #     exclude_edges = result_path.get_edges_for_conditions(unsat_core)
                #     logger.info("Edges to be excluded found.")
                #     logger.info("Adding a constraint to exclude "
                #                 "these edges...")
                #     if len(exclude_edges) > 0:
                #         self.add_path_exclusive_constraint(exclude_edges)
                #         infeasible.append(exclude_edges)
                #     else:
                #         self.add_path_exclusive_constraint(candidate_path_edges)
                #         infeasible.append(candidate_path_edges)
                #     logger.info("Constraint added.")
                #
                #     self.basisMatrix[current_row] = prev_matrix_row
                #     num_paths_unsat += 1

            logger.info("")
            logger.info("")

        if self.projectConfig.PREVENT_BASIS_REFINEMENT:
            return on_exit(start_time, infeasible)

        logger.info("Refining the basis into a 2-barycentric spanner...")
        logger.info("")
        is_two_barycentric = False
        refinement_round = 0
        while not is_two_barycentric:
            logger.info("Currently in round %d of refinement..." %
                        (refinement_round + 1))
            logger.info("")

            is_two_barycentric = True
            current_row, num_paths_unsat = 0, 0
            good_rows = (self.pathDimension - self.numBadRows)
            while current_row < good_rows:
                logger.info("Currently at row %d out of %d..." %
                            (current_row + 1, good_rows))
                logger.info("So far, %d candidate paths were found to be "
                            "unsatisfiable." % num_paths_unsat)
                logger.info("Basis matrix is")
                logger.info(self.basisMatrix)
                logger.info("")

                logger.info("Calculating subdeterminants...")
                if num_paths_unsat == 0:
                    # Calculate the subdeterminants only if the replacement
                    # of this row has not yet been attempted.
                    self.dag.resetEdgeWeights()
                    self.dag.edgeWeights = self._calculate_subdets(current_row)
                logger.info("Calculation complete.")

                logger.info("Finding a candidate path using an integer "
                            "linear program...")
                logger.info("")
                candidate_path_nodes, ilp_problem = \
                    pulp_helper.find_extreme_path(self)
                logger.info("")

                if ilp_problem.objVal is None:
                    logger.info("Unable to find a candidate path to "
                                "replace row %d." % (current_row + 1))
                    current_row += 1
                    num_paths_unsat = 0
                    continue

                logger.info("Candidate path found.")
                candidate_path_edges = Dag.get_edges(candidate_path_nodes)
                compressed_path = self._compress_path(candidate_path_edges)

                sign, old_basis_matrix_log_det = slogdet(self.basisMatrix)
                old_basis_matrix_det = exp(old_basis_matrix_log_det)
                logger.info("Absolute value of the old determinant: %g" %
                            old_basis_matrix_det)

                # Temporarily replace the row in the basis matrix
                # to calculate the new determinant.
                prev_matrix_row = self.basisMatrix[current_row].copy()
                self.basisMatrix[current_row] = compressed_path
                sign, new_basis_matrix_log_det = slogdet(self.basisMatrix)
                new_basis_matrix_det = exp(new_basis_matrix_log_det)
                logger.info("Absolute value of the new determinant: %g" %
                            new_basis_matrix_det)

                if new_basis_matrix_det > 2 * old_basis_matrix_det:
                    logger.info("Possible replacement for row found.")
                    # logger.info("Checking if replacement is feasible...")
                    logger.info("")
                    result_path = Path(ilp_problem=ilp_problem, nodes=candidate_path_nodes)
                    basis_paths[current_row] = result_path
                    current_row += 1
                    num_paths_unsat = 0
                    # result_path = self.check_feasibility(candidate_path_nodes,
                    #                                      ilp_problem)
                    # query_satisfiability = result_path.smtQuery.satisfiability
                    # if query_satisfiability == Satisfiability.SAT:
                    #     logger.info("Replacement is feasible.")
                    #     is_two_barycentric = False
                    #     basis_paths[current_row] = result_path
                    #     logger.info("Row %d replaced." % (current_row + 1))
                    #
                    #     current_row += 1
                    #     num_paths_unsat = 0
                    # elif query_satisfiability == Satisfiability.UNSAT:
                    #     logger.info("Replacement is infeasible.")
                    #
                    #     logger.info("Finding the edges to exclude...")
                    #     unsat_core = result_path.smtQuery.unsatCore
                    #     exclude_edges = \
                    #         result_path.get_edges_for_conditions(unsat_core)
                    #     logger.info("Edges to be excluded found.")
                    #     logger.info("Adding a constraint to exclude "
                    #                 "these edges...")
                    #     if len(exclude_edges) > 0:
                    #         self.add_path_exclusive_constraint(exclude_edges)
                    #         infeasible.append(exclude_edges)
                    #     else:
                    #         self.add_path_exclusive_constraint(candidate_path_edges)
                    #         infeasible.append(candidate_path_edges)
                    #     logger.info("Constraint added.")
                    #
                    #     self.basisMatrix[current_row] = prev_matrix_row
                    #     num_paths_unsat += 1
                else:
                    logger.info("No replacement for row %d found." %
                                (current_row + 1))
                    self.basisMatrix[current_row] = prev_matrix_row
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
        """Returns a list of weights, where weight i is assigned to
        edge i. The weights assigned to the `non-special' edges are
        subdeterminants of the basis matrix without row i and column j:
        column j corresponds to the `non-special' edge j.

        @param row Row to ignore.
        @retval List of weights as specified above.
        """
        edges_reduced = self.dag.edgesReduced
        edges_reduced_indices = self.dag.edgesReducedIndices

        edge_weight_list = [0] * self.dag.numEdges

        row_list = list(range(self.pathDimension))
        row_list.remove(row)

        for j in range(self.pathDimension):
            col_list = list(range(self.pathDimension))
            col_list.remove(j)
            sub_matrix = self.basisMatrix[row_list][:, col_list]

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

    # TODO: replace with code that works with LLVM
    # def check_feasibility(self, path_nodes, ilp_problem):
    #     """Determines the feasibility of the provided path in the DAG;
    #     the feasibility is checked with an SMT solver. This method
    #     returns a Path object that contains, at least, a Query object
    #     that represents the SMT query that contains the conditions along
    #     the path provided; the feasibility of the path is the same as the
    #     satisfiability of this Query object. If the path is feasible,
    #     then the Path object also contains satisfying assignments.
    #
    #     @param path_nodes Path whose feasibility should be checked, given
    #     as a list of nodes along the path.
    #     @param ilp_problem Integer linear programming problem that, when solved,
    #     produced this path, represented as an IlpProblem object.
    #     @retval Path object as described above.
    #     """
    #     # First, check if the candidate path is already a basis path.
    #     # This allows us to prevent unnecessary work.
    #     # It is also a hack around a problem in Z3, where the same query
    #     # can result in different models when checked more than once in
    #     # the same execution.
    #     # (See http://stackoverflow.com/q/15731179/1834042 for more details.)
    #     logger.info("Checking if the candidate path is already "
    #                 "a basis path...")
    #     try:
    #         basis_path_index = self.basisPathsNodes.index(path_nodes)
    #         logger.info("Candidate path is a basis path.")
    #
    #         # Create a copy of the Path object that represents the basis path:
    #         # we do not want to modify the IlpProblem object associated with
    #         # the basis Path object.
    #         path_copy = deepcopy(self.basisPaths[basis_path_index])
    #         path_copy.ilpProblem = ilp_problem
    #         return path_copy
    #     except ValueError as e:
    #         logger.info("Candidate path is not a basis path.")
    #
    #     # Write the candidate path to a file for further analysis
    #     # by the Phoenix backend.
    #     logger.info("Writing nodes along candidate path to file...")
    #     nodes_file = os.path.join(self.projectConfig.locationTempDir,
    #                              config.TEMP_PATH_NODES)
    #     try:
    #         nodes_file_handler = open(nodes_file, "w")
    #     except EnvironmentError as e:
    #         errMsg = "Error writing nodes along candidate path: %s" % e
    #         raise GameTimeError(errMsg)
    #     else:
    #         with nodes_file_handler:
    #             nodes_file_handler.write(" ".join(path_nodes))
    #     logger.info("Writing complete.")
    #
    #     logger.info("Running the Phoenix program analyzer...")
    #     logger.info("")
    #     if phoenixHelper.findConditions(self.projectConfig):
    #         errMsg = "Error running the Phoenix program analyzer."
    #         raise GameTimeError(errMsg)
    #     logger.info("Phoenix program analysis complete.")
    #     logger.info("")
    #
    #     logger.info("Reading the line numbers of statements "
    #                 "along the path...")
    #     lineNumbersFile = os.path.join(self.projectConfig.locationTempDir,
    #                                    config.TEMP_PATH_LINE_NUMBERS)
    #     lineNumbers = Path.readLineNumbersFromFile(lineNumbersFile)
    #     logger.info("Line numbers of the statements along "
    #                 "the path read and processed.")
    #
    #     logger.info("Reading the conditions along the path...")
    #     conditionsFile = os.path.join(self.projectConfig.locationTempDir,
    #                                   config.TEMP_PATH_CONDITIONS)
    #     conditions = Path.readConditionsFromFile(conditionsFile)
    #     logger.info("Path conditions read and processed.")
    #
    #     logger.info("Reading the edges that are associated with "
    #                 "the conditions along the path...")
    #     conditionEdgesFile = os.path.join(self.projectConfig.locationTempDir,
    #                                       config.TEMP_PATH_CONDITION_EDGES)
    #     conditionEdges = Path.readConditionEdgesFromFile(conditionEdgesFile)
    #     logger.info("Edges read and processed.")
    #
    #     logger.info("Reading the line numbers and truth values "
    #                 "of conditional points...")
    #     conditionTruthsFile = os.path.join(self.projectConfig.locationTempDir,
    #                                        config.TEMP_PATH_CONDITION_TRUTHS)
    #     conditionTruths = Path.readConditionTruthsFromFile(conditionTruthsFile)
    #     logger.info("Path condition truths read and processed.")
    #
    #     logger.info("Reading information about array accesses...")
    #     arrayAccessesFile = os.path.join(self.projectConfig.locationTempDir,
    #                                      config.TEMP_PATH_ARRAY_ACCESSES)
    #     arrayAccesses = Path.readArrayAccessesFromFile(arrayAccessesFile)
    #     logger.info("Array accesses information read and processed.")
    #
    #     logger.info("Reading information about the expressions "
    #                 "for aggregate accesses...")
    #     aggIndexExprsFile = os.path.join(self.projectConfig.locationTempDir,
    #                                      config.TEMP_PATH_AGG_INDEX_EXPRS)
    #     aggIndexExprs = Path.readAggIndexExprsFromFile(aggIndexExprsFile)
    #     logger.info("Aggregate accesses information read and processed.")
    #
    #     logger.info("Reading the SMT query generated by the "
    #                 "Phoenix program analyzer...")
    #     smtQueryFile = os.path.join(self.projectConfig.locationTempDir,
    #                                 "%s.smt" % config.TEMP_PATH_QUERY)
    #     smtQuery = readQueryFromFile(smtQueryFile)
    #     logger.info("SMT query read.")
    #
    #     assignments = {}
    #
    #     logger.info("Checking the satisfiability of the SMT query...")
    #     smtSolver = self.projectConfig.smtSolver
    #     smtSolver.checkSat(smtQuery)
    #     logger.info("Satisfiability checked.")
    #
    #     if smtQuery.satisfiability == Satisfiability.SAT:
    #         logger.info("Candidate path is FEASIBLE.")
    #
    #         logger.info("Generating assignments...")
    #         smtModelParser = self.projectConfig.smtModelParser
    #         assignments = smtModelParser.parseModel(smtQuery.model,
    #                                                 arrayAccesses,
    #                                                 aggIndexExprs,
    #                                                 self.projectConfig)
    #         logger.info("Assignments generated.")
    #     elif smtQuery.satisfiability == Satisfiability.UNSAT:
    #         logger.info("Candidate path is INFEASIBLE.")
    #     elif smtQuery.satisfiability == Satisfiability.UNKNOWN:
    #         errMsg = "Candidate path has UNKNOWN satisfiability."
    #         raise GameTimeError(errMsg)
    #
    #     if self.projectConfig.debugConfig.DUMP_ALL_QUERIES:
    #         try:
    #             allQueriesFile = \
    #                 os.path.join(self.projectConfig.locationTempDir,
    #                              config.TEMP_PATH_QUERY_ALL)
    #             allQueriesFileHandler = open(allQueriesFile, "a")
    #         except EnvironmentError as e:
    #             errMsg = "Error writing the candidate SMT query: %s" % e
    #             raise GameTimeError(errMsg)
    #         else:
    #             with allQueriesFileHandler:
    #                 allQueriesFileHandler.write("*** CANDIDATE QUERY ***\n")
    #                 allQueriesFileHandler.write("%s\n\n" % smtQuery)
    #
    #     logger.info("Removing temporary path information files...")
    #     self._removeTempPathFiles()
    #     logger.info("Temporary path information files removed.")
    #     logger.info("")
    #
    #     return Path(ilp_problem, path_nodes, lineNumbers,
    #                 conditions, conditionEdges, conditionTruths,
    #                 arrayAccesses, aggIndexExprs,
    #                 smtQuery,)

    def estimate_edge_weights(self):
        """Estimates the weights on the edges of the DAG, using the values
        of the basis "Path" objects. The result is stored in the instance
        variable "edgeWeights".

        Precondition: The basis paths have been generated and have values.
        """
        self.dag.resetEdgeWeights()

        basis_values = [basisPath.measuredValue for basisPath
                        in self.basisPaths]
        # By default, we assume a value of 0 for each of the rows in
        # the basis matrix that no replacement could be found for
        # (the `bad' rows in the basis matrix).
        basis_values += [0] * (self.pathDimension - len(basis_values))

        # Estimate the weights on the `non-special' edges of the graph.
        logger.info("Estimating the weights on the `non-special' edges...")
        reduced_edge_weights = dot(inv(self.basisMatrix), basis_values)
        logger.info("Weights estimated.")

        # Generate the list of edge weights that the integer linear
        # programming problem will use.
        logger.info("Generating the list of weights on all edges...")
        for reducedEdgeIndex, reducedEdge in enumerate(self.dag.edgesReduced):
            self.dag.edgeWeights[self.dag.edgesReducedIndices[reducedEdge]] = \
                reduced_edge_weights[reducedEdgeIndex]
        logger.info("List generated.")
