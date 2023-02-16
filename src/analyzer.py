#!/usr/bin/env python
import os
import shutil
import time
from typing import List, Set, Tuple

import clang_helper
import file_helper
import nx_helper
from defaults import config, logger
from file_helper import remove_all_except
from gametime_error import GameTimeError
from nx_helper import Dag
from project_configuration import ProjectConfiguration
import numpy as np

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
        self.basisMatrix = None

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

        if True: # TODO: Make this depend on project configuration
            processing: str = clang_helper.compile_to_llvm(self.projectConfig)


        # Preprocessing pass: inline functions.
        if self.projectConfig.inlined: # Note: This is made into a bool rather than a list
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

    def _run_inliner(self, input_file: str=None):
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
        self.basisMatrix = eye(self.pathDimension)
        if self.projectConfig.RANDOMIZE_INITIAL_BASIS:
            self._randomizeBasisMatrix()

    ### PATH GENERATION FUNCTIONS ###
    def add_path_exclusive_constraint(self, edges: Tuple[str, str]):
        """Adds the edges provided to the list of path-exclusive
        constraints, if not already present. These edges must not
        be taken together along any path through the DAG.

        @param edges List of edges to add to the list of
        path-exclusive constraints.
        """
        if edges not in self.pathExclusiveConstraints:
            self.pathExclusiveConstraints.append(edges)

    def add_path_bundled_constraint(self, edges: Tuple[str, str]):
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


    ####### Fuctions to FIX
    def generateBasisPaths(self):
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
        start_time = time.clock()

        logger.info("Initializing the basis matrix...")
        self._init_basis_matrix()
        logger.info("Basis matrix initialized to")
        logger.info(self.basisMatrix)
        logger.info("")
        logger.info("There are a maximum of %d possible basis paths." %
                    self.pathDimension)
        logger.info("")

        def onExit(startTime, infeasible):
            """Helper function that is called when this method is about to
            return the basis Path objects, and performs the appropriate
            pre-exit cleanup. This inner function will be used in two
            places below, and is defined once to keep the code neat,
            to prevent deeper indentation, and to reduce confusion.

            @param startTime Time when the generation of basis Path objects
                was started.
            @retval List of basis paths of the code being analyzed, each
                represented by an object of the Path class.
            """
            self.basisPaths = basis_paths
            self.basisPathsNodes = [path.nodes for path in basis_paths]
            # self.resetPathExclusiveConstraints()

            logger.info("Time taken to generate paths: %.2f seconds." %
                        (time.clock() - startTime))

            logger.info("Basis paths generated.")

            # If we are computing overcomplete basis, use the computed set as
            # the initial set of paths in the iterative algorithm,
            if self.projectConfig.OVER_COMPLETE_BASIS:
                logger.info("Iteratively improving the basis")
                for path in infeasible:
                    self.addPathExclusiveConstraint(path)
                edgePaths = \
                    [Dag.getEdges(path.nodes) for path in self.basisPaths]
                result = self.iterativelyFindOvercompleteBasis(
                    edgePaths, self.projectConfig.MAXIMUM_ERROR_SCALE_FACTOR)
                logger.info("Number of paths generated: %d" % len(result))
                logger.info("Time taken to generate paths: %.2f seconds." %
                            (time.clock() - startTime))
                return result
            else:
                return self.basisPaths

        if self.pathDimension == 1:
            warnMsg = ("Basis matrix has dimensions 1x1. "
                       "There is only one path through the function "
                       "under analysis, which is the only basis path.")
            logger.warn(warnMsg)

        # Collects all infeasible paths discovered during the computation
        infeasible = []
        currentRow, numPathsUnsat = 0, 0
        while currentRow < (self.pathDimension - self.numBadRows):
            logger.info("Currently at row %d..." % (currentRow + 1))
            logger.info("So far, the bottom %d rows of the basis "
                        "matrix are `bad'." % self.numBadRows)
            logger.info("So far, %d candidate paths were found to be "
                        "unsatisfiable." % numPathsUnsat)
            logger.info("Basis matrix is")
            logger.info(self.basisMatrix)
            logger.info("")

            logger.info("Calculating subdeterminants...")
            if numPathsUnsat == 0:
                # Calculate the subdeterminants only if the replacement
                # of this row has not yet been attempted.
                self.dag.resetEdgeWeights()
                self.dag.edgeWeights = self._calculateSubdets(currentRow)
            logger.info("Calculation complete.")

            logger.info("Finding a candidate path using an integer "
                        "linear program...")
            logger.info("")
            candidatePathNodes, ilpProblem = pulpHelper.find_extreme_path(self)
            logger.info("")

            if ilpProblem.objVal is None:
                logger.info("Unable to find a candidate path to "
                            "replace row %d." % (currentRow + 1))
                logger.info("Moving the bad row to the bottom "
                            "of the basis matrix.")
                for k in xrange((currentRow + 1), self.pathDimension):
                    self._swapBasisMatrixRows(k - 1, k)
                self.numBadRows += 1
                numPathsUnsat = 0
                continue

            logger.info("Candidate path found.")
            candidatePathEdges = Dag.getEdges(candidatePathNodes)
            compressedPath = self._compressPath(candidatePathEdges)

            # Temporarily replace the row in the basis matrix
            # to calculate the new determinant.
            prevMatrixRow = self.basisMatrix[currentRow].copy()
            self.basisMatrix[currentRow] = compressedPath
            sign, newBasisMatrixLogDet = slogdet(self.basisMatrix)
            newBasisMatrixDet = exp(newBasisMatrixLogDet)
            logger.info("Absolute value of the new determinant: %g" %
                        newBasisMatrixDet)
            logger.info("")

            DETERMINANT_THRESHOLD = self.projectConfig.DETERMINANT_THRESHOLD
            MAX_INFEASIBLE_PATHS = self.projectConfig.MAX_INFEASIBLE_PATHS
            if ((sign == 0 and newBasisMatrixLogDet == float("-inf")) or
                    newBasisMatrixDet < DETERMINANT_THRESHOLD or
                    numPathsUnsat >= MAX_INFEASIBLE_PATHS):
                if (newBasisMatrixDet < DETERMINANT_THRESHOLD and
                        not (sign == 0 and newBasisMatrixLogDet == float("-inf"))):
                    logger.info("Determinant is too small.")
                else:
                    logger.info("Unable to find a path that makes "
                                "the determinant non-zero.")
                logger.info("Moving the bad row to the bottom "
                            "of the basis matrix.")
                self.basisMatrix[currentRow] = prevMatrixRow
                for k in xrange((currentRow + 1), self.pathDimension):
                    self._swapBasisMatrixRows(k - 1, k)
                self.numBadRows += 1
                numPathsUnsat = 0
            else:
                logger.info("Possible replacement for row found.")
                logger.info("Checking if replacement is feasible...")
                logger.info("")
                resultPath = self.checkFeasibility(candidatePathNodes,
                                                   ilpProblem)
                querySatisfiability = resultPath.smtQuery.satisfiability
                if querySatisfiability == Satisfiability.SAT:
                    # Sanity check:
                    # A row should not be replaced if it replaces a good
                    # row and decreases the determinant. However,
                    # replacing a bad row and decreasing the determinant
                    # is okay. (TODO: Are we actually doing this?)
                    logger.info("Replacement is feasible.")
                    logger.info("Row %d replaced." % (currentRow + 1))

                    basis_paths.append(resultPath)
                    currentRow += 1
                    numPathsUnsat = 0
                elif querySatisfiability == Satisfiability.UNSAT:
                    logger.info("Replacement is infeasible.")
                    logger.info("Finding the edges to exclude...")
                    unsatCore = resultPath.smtQuery.unsatCore
                    excludeEdges = resultPath.get_edges_for_conditions(unsatCore)
                    logger.info("Edges to be excluded found.")
                    logger.info("Adding a constraint to exclude "
                                "these edges...")
                    if len(excludeEdges) > 0:
                        self.addPathExclusiveConstraint(excludeEdges)
                        infeasible.append(excludeEdges)
                    else:
                        self.addPathExclusiveConstraint(candidatePathEdges)
                        infeasible.append(candidatePathEdges)
                    logger.info("Constraint added.")

                    self.basisMatrix[currentRow] = prevMatrixRow
                    numPathsUnsat += 1

            logger.info("")
            logger.info("")

        if self.projectConfig.PREVENT_BASIS_REFINEMENT:
            return onExit(start_time, infeasible)

        logger.info("Refining the basis into a 2-barycentric spanner...")
        logger.info("")
        isTwoBarycentric = False
        refinementRound = 0
        while not isTwoBarycentric:
            logger.info("Currently in round %d of refinement..." %
                        (refinementRound + 1))
            logger.info("")

            isTwoBarycentric = True
            currentRow, numPathsUnsat = 0, 0
            goodRows = (self.pathDimension - self.numBadRows)
            while currentRow < goodRows:
                logger.info("Currently at row %d out of %d..." %
                            (currentRow + 1, goodRows))
                logger.info("So far, %d candidate paths were found to be "
                            "unsatisfiable." % numPathsUnsat)
                logger.info("Basis matrix is")
                logger.info(self.basisMatrix)
                logger.info("")

                logger.info("Calculating subdeterminants...")
                if numPathsUnsat == 0:
                    # Calculate the subdeterminants only if the replacement
                    # of this row has not yet been attempted.
                    self.dag.resetEdgeWeights()
                    self.dag.edgeWeights = self._calculateSubdets(currentRow)
                logger.info("Calculation complete.")

                logger.info("Finding a candidate path using an integer "
                            "linear program...")
                logger.info("")
                candidatePathNodes, ilpProblem = \
                    pulpHelper.find_extreme_path(self)
                logger.info("")

                if ilpProblem.objVal is None:
                    logger.info("Unable to find a candidate path to "
                                "replace row %d." % (currentRow + 1))
                    currentRow += 1
                    numPathsUnsat = 0
                    continue

                logger.info("Candidate path found.")
                candidatePathEdges = Dag.getEdges(candidatePathNodes)
                compressedPath = self._compressPath(candidatePathEdges)

                sign, oldBasisMatrixLogDet = slogdet(self.basisMatrix)
                oldBasisMatrixDet = exp(oldBasisMatrixLogDet)
                logger.info("Absolute value of the old determinant: %g" %
                            oldBasisMatrixDet)

                # Temporarily replace the row in the basis matrix
                # to calculate the new determinant.
                prevMatrixRow = self.basisMatrix[currentRow].copy()
                self.basisMatrix[currentRow] = compressedPath
                sign, newBasisMatrixLogDet = slogdet(self.basisMatrix)
                newBasisMatrixDet = exp(newBasisMatrixLogDet)
                logger.info("Absolute value of the new determinant: %g" %
                            newBasisMatrixDet)

                if newBasisMatrixDet > 2 * oldBasisMatrixDet:
                    logger.info("Possible replacement for row found.")
                    logger.info("Checking if replacement is feasible...")
                    logger.info("")
                    resultPath = self.checkFeasibility(candidatePathNodes,
                                                       ilpProblem)
                    querySatisfiability = resultPath.smtQuery.satisfiability
                    if querySatisfiability == Satisfiability.SAT:
                        logger.info("Replacement is feasible.")
                        isTwoBarycentric = False
                        basis_paths[currentRow] = resultPath
                        logger.info("Row %d replaced." % (currentRow + 1))

                        currentRow += 1
                        numPathsUnsat = 0
                    elif querySatisfiability == Satisfiability.UNSAT:
                        logger.info("Replacement is infeasible.")

                        logger.info("Finding the edges to exclude...")
                        unsatCore = resultPath.smtQuery.unsatCore
                        excludeEdges = \
                            resultPath.get_edges_for_conditions(unsatCore)
                        logger.info("Edges to be excluded found.")
                        logger.info("Adding a constraint to exclude "
                                    "these edges...")
                        if len(excludeEdges) > 0:
                            self.addPathExclusiveConstraint(excludeEdges)
                            infeasible.append(excludeEdges)
                        else:
                            self.addPathExclusiveConstraint(candidatePathEdges)
                            infeasible.append(candidatePathEdges)
                        logger.info("Constraint added.")

                        self.basisMatrix[currentRow] = prevMatrixRow
                        numPathsUnsat += 1
                else:
                    logger.info("No replacement for row %d found." %
                                (currentRow + 1))
                    self.basisMatrix[currentRow] = prevMatrixRow
                    currentRow += 1
                    numPathsUnsat = 0

                logger.info("")
                logger.info("")

            refinementRound += 1
            logger.info("")

        logger.info("Basis refined.")
        return onExit(start_time, infeasible)
