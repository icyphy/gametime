#!/usr/bin/env python

"""Defines a class that maintains information about the code being analyzed,
such as the name of the file that contains the code being analyzed and
the basis paths in the code.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import bz2
import os
import pickle
import random
import shutil
import time
from copy import deepcopy

from numpy import dot, exp, eye, genfromtxt, savetxt
from numpy.linalg import det, inv, slogdet

import cilHelper
import inliner
import loopHandler
import merger
import nxHelper
import phoenixHelper
import pulpHelper
import networkx as nx
from defaults import config, logger
from fileHelper import createDir, removeAllExcept, removeFile
from gametimeError import GameTimeError
from nxHelper import Dag
from path import Path
from pathGenerator import PathGenerator
from smt.query import readQueryFromFile, Satisfiability


class Analyzer(object):
    """Maintains information about the code being analyzed, such as
    the name of the file that contains the code being analyzed
    and the basis paths of the code.

    Attributes:
        projectConfig:
            :class:`~gametime.projectConfiguration.ProjectConfiguration`
            object that represents the configuration of a GameTime project.
    """
    def __init__(self, projectConfig):
        ### CONFIGURATIONS ###
        #: :class:`~gametime.projectConfiguration.ProjectConfiguration` object
        #: that represents the configuration of a GameTime project.
        self.projectConfig = projectConfig

        ### GRAPH INFORMATION ###
        #: Data structure for the DAG of the code being analyzed.
        self.dag = Dag()

        ### PATHS INFORMATION ###
        #: Dimension of the vector representing each path.
        self.pathDimension = 0

        #: Basis matrix.
        self.basisMatrix = None

        #: Set whose elements are lists of edges that must not be taken
        #: together along any path through the DAG. For example, the element
        #: [e1, e2] means "if you take e1, you cannot take e2" and
        #: "if you take e2, you cannot take e1".
        self.pathExclusiveConstraints = []

        #: List whose elements are lists of edges that must be taken together,
        #: if at least one is taken along a path through the DAG. For example,
        #: the element [e1, e2] means "if you take e1, then you take e2".
        self.pathBundledConstraints = []

        # Number of `bad' rows in the basis matrix.
        self.numBadRows = 0

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
        self.inferredMuMax = 0
        # The in predictions is error is 2 * inferredMuMax * errorScaleFactor
        self.errorScaleFactor = 0

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
        origFile = self.projectConfig.locationOrigFile
        projectTempDir = self.projectConfig.locationTempDir
        if not os.path.exists(origFile):
            shutil.rmtree(projectTempDir)
            errMsg = "File to analyze not found: %s" % origFile
            raise GameTimeError(errMsg)

        # Remove any temporary directory created during a previous run
        # of the same GameTime project, and create a fresh new
        # temporary directory.
        if os.path.exists(projectTempDir):
            if self.projectConfig.UNROLL_LOOPS:
                # If a previous run of the same GameTime project produced
                # a loop configuration file, and the current run involves
                # unrolling the loops that are configured in the file,
                # do not remove the file.
                removeAllExcept([config.TEMP_LOOP_CONFIG], projectTempDir)
            else:
                removeAllExcept([], projectTempDir)
        else:
            os.mkdir(projectTempDir)

        # Make a temporary copy of the original file to preprocess.
        preprocessedFile = self.projectConfig.locationTempFile
        shutil.copyfile(origFile, preprocessedFile)

        # Preprocessing pass: merge other source files.
        if len(self.projectConfig.merged) > 0:
            self._runMerger()

        # Preprocessing pass: unroll loops.
        if self.projectConfig.UNROLL_LOOPS:
            self._runLoopUnroller()

        # Preprocessing pass: inline functions.
        if len(self.projectConfig.inlined) > 0:
            self._runInliner()

        # Preprocessing pass: run the file through CIL once more,
        # to reduce the C file to the subset of constructs used by CIL
        # for ease of analysis.
        self._runCil()

        # We are done with the preprocessing.
        logger.info("Preprocessing complete.")
        logger.info("")

    ### PREPROCESSING HELPER FUNCTIONS ###
    def _runMerger(self):
        """As part of preprocessing, runs CIL on the source file under
        analysis to merge other source files. A copy of the file that
        results from the CIL preprocessing is made and renamed for use by
        other preprocessing phases, and the file itself is renamed and
        stored for later perusal.
        """
        preprocessedFile = self.projectConfig.locationTempFile
        # Infer the name of the file that results from the CIL preprocessing.
        cilFile = "%s.cil.c" % self.projectConfig.locationTempNoExtension

        logger.info("Preprocessing the file: merging other source files...")

        if merger.runMerger(self.projectConfig):
            errMsg = "Error running the merger."
            raise GameTimeError(errMsg)
        else:
            shutil.copyfile(cilFile, preprocessedFile)
            shutil.move(cilFile,
                        "%s%s.c" % (self.projectConfig.locationTempNoExtension,
                                    config.TEMP_SUFFIX_MERGED))
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                cilHelper.removeTempCilFiles(self.projectConfig)

            logger.info("")
            logger.info("Other source files merged.")

    def _runLoopUnroller(self):
        """As part of preprocessing, runs CIL on the source file under
        analysis to unroll loops. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.
        """
        preprocessedFile = self.projectConfig.locationTempFile
        # Infer the name of the file that results from the CIL preprocessing.
        cilFile = "%s.cil.c" % self.projectConfig.locationTempNoExtension

        logger.info("Preprocessing the file: unrolling loops in the code...")

        if loopHandler.runUnroller(self.projectConfig):
            errMsg = "Error running the loop unroller."
            raise GameTimeError(errMsg)
        else:
            shutil.copyfile(cilFile, preprocessedFile)
            shutil.move(cilFile,
                        "%s%s.c" % (self.projectConfig.locationTempNoExtension,
                                    config.TEMP_SUFFIX_UNROLLED))
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                cilHelper.removeTempCilFiles(self.projectConfig)

            logger.info("")
            logger.info("Loops in the code have been unrolled.")

    def _runInliner(self):
        """As part of preprocessing, runs CIL on the source file under
        analysis to inline functions. A copy of the file that results from
        the CIL preprocessing is made and renamed for use by other
        preprocessing phases, and the file itself is renamed and
        stored for later perusal.
        """
        preprocessedFile = self.projectConfig.locationTempFile
        # Infer the name of the file that results from the CIL preprocessing.
        cilFile = "%s.cil.c" % self.projectConfig.locationTempNoExtension

        logger.info("Preprocessing the file: inlining...")

        if inliner.runInliner(self.projectConfig):
            errMsg = "Error running the inliner."
            raise GameTimeError(errMsg)
        else:
            shutil.copyfile(cilFile, preprocessedFile)
            shutil.move(cilFile,
                        "%s%s.c" % (self.projectConfig.locationTempNoExtension,
                                    config.TEMP_SUFFIX_INLINED))
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                cilHelper.removeTempCilFiles(self.projectConfig)

            logger.info("")
            logger.info("Inlining complete.")

    def _runCil(self):
        """As part of preprocessing, runs CIL on the source file under
        analysis to to reduce the C file to the subset of constructs
        used by CIL for ease of analysis. The file that results from
        the CIL preprocessing is renamed for use by the rest of
        the GameTime toolflow. Another copy, with preprocessor directives
        that maintain the line numbers from the original source file
        (and other merged source files), is also made.
        """
        preprocessedFile = self.projectConfig.locationTempFile
        # Infer the name of the file that results from the CIL preprocessing.
        cilFile = "%s.cil.c" % self.projectConfig.locationTempNoExtension

        logger.info("Preprocessing the file: running CIL to produce code "
                    "simplified for analysis...")

        if cilHelper.runCil(self.projectConfig, keepLineNumbers=True):
            errMsg = "Error running CIL in the final preprocessing phase."
            raise GameTimeError(errMsg)
        else:
            shutil.move(cilFile,
                        "%s%s.c" % (self.projectConfig.locationTempNoExtension,
                                    config.TEMP_SUFFIX_LINE_NUMS))
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                cilHelper.removeTempCilFiles(self.projectConfig)

        if cilHelper.runCil(self.projectConfig):
            errMsg = "Error running CIL in the final preprocessing phase."
            raise GameTimeError(errMsg)
        else:
            shutil.move(cilFile, preprocessedFile)
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                cilHelper.removeTempCilFiles(self.projectConfig)

        logger.info("")
        logger.info("Final preprocessing phase complete.")

    ### BASIS MATRIX FUNCTIONS ###
    def _initBasisMatrix(self):
        """Initializes the basis matrix."""
        self.basisMatrix = eye(self.pathDimension)
        if self.projectConfig.RANDOMIZE_INITIAL_BASIS:
            self._randomizeBasisMatrix()

    def _randomizeBasisMatrix(self):
        """Randomizes the rows of the basis matrix using
        a Fisher-Yates shuffle.

        Precondition: The basis matrix has been initialized.
        """
        for i in xrange(self.pathDimension, 0, -1):
            j = random.randrange(i)
            self._swapBasisMatrixRows(i-1, j)

    def _swapBasisMatrixRows(self, i, j):
        """Swaps two rows of the basis matrix.

        @param i Index of one row to swap.
        @param j Index of other row to swap.
        """
        rowToSwapOut = self.basisMatrix[j]
        rowToSwapIn = self.basisMatrix[i]
        rowLen = len(rowToSwapOut)

        tempRowToSwapOut = [0] * rowLen
        for k in xrange(rowLen):
            tempRowToSwapOut[k] = rowToSwapOut[k]
        for k in xrange(rowLen):
            rowToSwapOut[k] = rowToSwapIn[k]
            rowToSwapIn[k] = tempRowToSwapOut[k]

    def saveBasisMatrix(self, location=None):
        """Saves the basis matrix to a file for future analysis.

        @param location Location of the file. If this is not provided,
        the basis matrix will be stored in a temporary file located in
        the temporary directory used by GameTime for its analysis.
        """
        location = location or os.path.join(self.projectConfig.locationTempDir,
                                            config.TEMP_BASIS_MATRIX)
        try:
            savetxt(location, self.basisMatrix, fmt="%01.1f")
        except EnvironmentError as e:
            errMsg = "Error saving the basis matrix: %s" % e
            raise GameTimeError(errMsg)

    def loadBasisMatrix(self, location=None):
        """Loads the basis matrix from a file.

        @param location Location of the file. If this is not provided,
        the basis file will be loaded from a temporary file located in
        the temporary directory used by GameTime for its analysis.
        """
        location = location or os.path.join(self.projectConfig.locationTempDir,
                                            config.TEMP_BASIS_MATRIX)
        try:
            self.basisMatrix = genfromtxt(location, delimiter=" ")
        except EnvironmentError as e:
            errMsg = "Error loading the basis matrix: %s" % e
            raise GameTimeError(errMsg)

    ### GRAPH FUNCTIONS ###
    def createDag(self):
        """Creates the DAG corresponding to the code being analyzed
        and dumps the DAG, in DOT format, to a temporary file for further
        analysis. This method also stores a local copy in a data
        structure that represents the DAG.
        """
        logger.info("Generating the DAG and associated information...")

        if phoenixHelper.createDag(self.projectConfig):
            errMsg = "Error running the Phoenix program analyzer."
            raise GameTimeError(errMsg)

        location = os.path.join(self.projectConfig.locationTempDir,
                                config.TEMP_DAG)
        self.loadDagFromDotFile(location)

        numEdgesReduced = len(self.dag.edgesReduced)
        self.pathDimension = self.dag.numEdges - self.dag.numNodes + 2
        if numEdgesReduced != self.pathDimension:
            errMsg = ("The number of non-special edges is different "
                      "from the dimension of the path.")
            raise GameTimeError(errMsg)

        logger.info("DAG generated.")

        if nxHelper.hasCycles(self.dag):
            logger.warn("The control-flow graph has cycles.")
            self._runLoopDetector()
        else:
            logger.info("The control-flow graph has %d nodes and %d edges, "
                        "with at most %d possible paths." %
                        (self.dag.numNodes, self.dag.numEdges,
                         self.dag.numPaths))
            logger.info("There are at most %d possible basis paths." %
                        self.pathDimension)
        logger.info("")

    def loadDagFromDotFile(self, location):
        """Loads the DAG that corresponds to the code being analyzed
        from a DOT file.

        @param location Location of the file.
        """
        self.dag = nxHelper.constructDag(location)

        # Reset variables of this "Analyzer" object.
        self.resetPathExclusiveConstraints()
        self.resetPathBundledConstraints()

    def writeDagToDotFile(self, location=None, annotateEdges=False,
                          highlightedPath=None, highlightColor="red"):
        """Writes the DAG that corresponds to the code being analyzed
        to a DOT file.

        @param location Location of the file. If this is not provided,
        the basis matrix will be stored in a temporary file located in
        the temporary directory used by GameTime for its analysis.
        @param annotateEdges Whether each edge should be annotated with
        its weight, when the file is processed by a visualization tool.
        @param highlightedPath "Path" object whose corresponding edges
        will be highlighted when the DOT file is processed by
        a visualization tool. If this argument is not provided, no edges
        will be highlighted.
        @param highlightColor Color of the highlighted edges. This argument
        can be any value that is legal in the DOT format; by default, its value
        is "red". If the "highlightedPath" argument is not provided,
        this argument is ignored.
        """
        location = location or os.path.join(self.projectConfig.locationTempDir,
                                            config.TEMP_DAG_WEIGHTS)
        edgeWeights = [("%g" % edgeWeight) for edgeWeight
                       in self.dag.edgeWeights]
        edgesToWeights = (dict(zip(self.dag.allEdges, edgeWeights))
                          if annotateEdges else None)
        nxHelper.writeDagToDotFile(self.dag, location,
                                   self.projectConfig.func, edgesToWeights,
                                   (Dag.getEdges(highlightedPath.nodes)
                                    if highlightedPath else None),
                                   highlightColor)

    def _runLoopDetector(self):
        """Runs the loop detector on the code under analysis."""
        logger.info("Detecting loops in the code...")

        if loopHandler.runDetector(self.projectConfig):
            errMsg = "Error running the loop detector."
            raise GameTimeError(errMsg)
        else:
            if not self.projectConfig.debugConfig.KEEP_CIL_TEMPS:
                cilHelper.removeTempCilFiles(self.projectConfig)

        logger.info("")
        logger.info("Loops in the code have been detected.")
        logger.info("Before proceeding, please modify the loop configuration "
                    "file in the temporary directory generated by GameTime "
                    "for this analysis, and then run the loop unroller "
                    "to unroll these loops.")

    def _compressPath(self, pathEdges):
        """Compresses the path provided: this method converts
        the provided path to a 0-1 vector that is 1 if a
        'non-special' edge is along the path, and 0 otherwise.

        @param pathEdges Edges along the path to represent with
        'non-special' edges.
        @retval 0-1 vector that is 1 if a `non-special' edge is along
        the path, and 0 otherwise.
        """
        return [(1.0 if edge in pathEdges else 0.0)
                for edge in self.dag.edgesReduced]

    ### PATH GENERATION FUNCTIONS ###
    def addPathExclusiveConstraint(self, edges):
        """Adds the edges provided to the list of path-exclusive
        constraints, if not already present. These edges must not
        be taken together along any path through the DAG.

        @param edges List of edges to add to the list of
        path-exclusive constraints.
        """
        if edges not in self.pathExclusiveConstraints:
            self.pathExclusiveConstraints.append(edges)

    def addPathBundledConstraint(self, edges):
        """Adds the edges provided to the list of path-bundled
        constraints, if not already present. These edges must
        be taken together if at least one of them is taken along
        a path through the DAG.

        @param edges List of edges to add to the list of path-bundled
        constraints.
        """
        if edges not in self.pathBundledConstraints:
            self.pathBundledConstraints.append(edges)

    def resetPathExclusiveConstraints(self):
        """Resets the path-exclusive constraints."""
        self.pathExclusiveConstraints = []

    def resetPathBundledConstraints(self):
        """Resets the path-bundled constraints."""
        self.pathBundledConstraints = []

    def generateOvercompleteBasis(self, k):
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
        pulpHelper.findMinimalOvercompleteBasis(self, feasible, k)  

    def iterativelyFindOvercompleteBasis(self, initialPaths, k):
        """Generates overcomplete basis such the the lenth of the longest
           feasible path is at most 'k'. The basis is computed by iteratively
           extending the basis with the longest path.  Parameter 'initialPaths'
           specifies the set of paths the iterative algorithm begins with. This
           can be any set of paths, in practice we use the paths generated by
           the standard algorithm.
        """
        infeasible = []
        edgeNodePaths = initialPaths
        optimalBound = 1
        startTime = time.clock()
        while True:
            beforeTime = time.clock()
            length, path, ilpProblem = \
                pulpHelper.findWorstExpressiblePath(self, self.basisPaths, 0)
            afterTime = time.clock()
            logger.info("Found a candidate path of length %.2f in %d seconds" %
                        (length, afterTime - beforeTime))

            optimalBound = length
            # if the length of the longest path is within the given bound, stop
            if (length <= k): break

            candidatePathNodes = path
            candidatePathEdges = Dag.getEdges(candidatePathNodes)

            logger.info("Checking if the found path is feasible...")
            resultPath = self.checkFeasibility(candidatePathNodes,
                                               ilpProblem)
            querySatisfiability = resultPath.smtQuery.satisfiability
            if querySatisfiability == Satisfiability.SAT:
                logger.info("Path is feasible.")
                self.basisPaths.append(resultPath)
                edgeNodePaths.append(candidatePathEdges)
            elif querySatisfiability == Satisfiability.UNSAT:
                logger.info("Path is infeasible.")
                logger.info("Finding the edges to exclude...")
                infeasible.append(candidatePathEdges)
                unsatCore = resultPath.smtQuery.unsatCore
                excludeEdges = resultPath.getEdgesForConditions(unsatCore)
                logger.info("Edges to be excluded found.")
                logger.info("Adding a constraint to exclude "
                            "these edges...")
                if len(excludeEdges) > 0:
                    self.addPathExclusiveConstraint(excludeEdges)
                else:
                    self.addPathExclusiveConstraint(candidatePathEdges)
                logger.info("Constraint added.")
          
        logger.info("Found overcomplete basis of size %d, yielding bound %.2f" %
            (len(edgeNodePaths), optimalBound))
        
        self.basisPathsNodes = [path.nodes for path in self.basisPaths]
        return self.basisPaths 

    def generateBasisPaths(self):
        """Generates a list of "Path" objects, each of which represents
        a basis path of the code being analyzed. The basis "Path" objects
        are regenerated each time this method is called.

        @retval List of basis paths of the code being analyzed, each
        represented by an object of the "Path" class.
        """
        basisPaths = []

        if nxHelper.hasCycles(self.dag):
            logger.warn("Loops in the code have been detected.")
            logger.warn("No basis paths have been generated.")
            return []

        logger.info("Generating the basis paths...")
        logger.info("")
        startTime = time.clock()

        logger.info("Initializing the basis matrix...")
        self._initBasisMatrix()
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
            self.basisPaths = basisPaths
            self.basisPathsNodes = [path.nodes for path in basisPaths]
            #self.resetPathExclusiveConstraints()

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
            logger.info("Currently at row %d..." % (currentRow+1))
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
            candidatePathNodes, ilpProblem = pulpHelper.findExtremePath(self)
            logger.info("")

            if ilpProblem.objVal is None:
                logger.info("Unable to find a candidate path to "
                            "replace row %d." % (currentRow+1))
                logger.info("Moving the bad row to the bottom "
                            "of the basis matrix.")
                for k in xrange((currentRow+1), self.pathDimension):
                    self._swapBasisMatrixRows(k-1, k)
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
                for k in xrange((currentRow+1), self.pathDimension):
                    self._swapBasisMatrixRows(k-1, k)
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
                    logger.info("Row %d replaced." % (currentRow+1))

                    basisPaths.append(resultPath)
                    currentRow += 1
                    numPathsUnsat = 0
                elif querySatisfiability == Satisfiability.UNSAT:
                    logger.info("Replacement is infeasible.")
                    logger.info("Finding the edges to exclude...")
                    unsatCore = resultPath.smtQuery.unsatCore
                    excludeEdges = resultPath.getEdgesForConditions(unsatCore)
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
            return onExit(startTime, infeasible)

        logger.info("Refining the basis into a 2-barycentric spanner...")
        logger.info("")
        isTwoBarycentric = False
        refinementRound = 0
        while not isTwoBarycentric:
            logger.info("Currently in round %d of refinement..." %
                        (refinementRound+1))
            logger.info("")

            isTwoBarycentric = True
            currentRow, numPathsUnsat = 0, 0
            goodRows = (self.pathDimension - self.numBadRows)
            while currentRow < goodRows:
                logger.info("Currently at row %d out of %d..." %
                            (currentRow+1, goodRows))
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
                pulpHelper.findExtremePath(self)
                logger.info("")

                if ilpProblem.objVal is None:
                    logger.info("Unable to find a candidate path to "
                                "replace row %d." % (currentRow+1))
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
                        basisPaths[currentRow] = resultPath
                        logger.info("Row %d replaced." % (currentRow+1))

                        currentRow += 1
                        numPathsUnsat = 0
                    elif querySatisfiability == Satisfiability.UNSAT:
                        logger.info("Replacement is infeasible.")

                        logger.info("Finding the edges to exclude...")
                        unsatCore = resultPath.smtQuery.unsatCore
                        excludeEdges = \
                        resultPath.getEdgesForConditions(unsatCore)
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
                                (currentRow+1))
                    self.basisMatrix[currentRow] = prevMatrixRow
                    currentRow += 1
                    numPathsUnsat = 0

                logger.info("")
                logger.info("")

            refinementRound += 1
            logger.info("")

        logger.info("Basis refined.")
        return onExit(startTime, infeasible)

    # Methods imported from the "PathGenerator" class.
    def generatePaths(self, *args, **kwargs):
        return PathGenerator.generatePaths(self, *args, **kwargs)

    ### PATH GENERATION HELPER FUNCTIONS ###
    def _calculateSubdets(self, row):
        """Returns a list of weights, where weight i is assigned to
        edge i. The weights assigned to the `non-special' edges are
        subdeterminants of the basis matrix without row i and column j:
        column j corresponds to the `non-special' edge j.

        @param row Row to ignore.
        @retval List of weights as specified above.
        """
        edgesReduced = self.dag.edgesReduced
        edgesReducedIndices = self.dag.edgesReducedIndices

        edgeWeightList = [0] * self.dag.numEdges

        rowList = range(self.pathDimension)
        rowList.remove(row)

        for j in xrange(self.pathDimension):
            colList = range(self.pathDimension)
            colList.remove(j)
            subMatrix = self.basisMatrix[rowList][:, colList]

            if subMatrix.size != 0:
                # Compute the subdeterminant of this submatrix.
                subdet = det(subMatrix)
                if ((row+j) % 2) == 1:
                    edgeWeight = -1 * subdet
                else:
                    edgeWeight = subdet
            else:
                # Special case of a 1x1 matrix, or of code under analysis
                # with only one path that goes through.
                edgeWeight = 1

            # Assign this edge weight to the proper `non-special' edge.
            edgeWeightList[edgesReducedIndices[edgesReduced[j]]] = edgeWeight

        return edgeWeightList

    def checkFeasibility(self, pathNodes, ilpProblem):
        """Determines the feasibility of the provided path in the DAG;
        the feasibility is checked with an SMT solver. This method
        returns a Path object that contains, at least, a Query object
        that represents the SMT query that contains the conditions along
        the path provided; the feasibility of the path is the same as the
        satisfiability of this Query object. If the path is feasible,
        then the Path object also contains satisfying assignments.

        @param pathNodes Path whose feasibility should be checked, given
        as a list of nodes along the path.
        @param ilpProblem Integer linear programming problem that, when solved,
        produced this path, represented as an IlpProblem object.
        @retval Path object as described above.
        """
        # First, check if the candidate path is already a basis path.
        # This allows us to prevent unnecessary work.
        # It is also a hack around a problem in Z3, where the same query
        # can result in different models when checked more than once in
        # the same execution.
        # (See http://stackoverflow.com/q/15731179/1834042 for more details.)
        logger.info("Checking if the candidate path is already "
                    "a basis path...")
        try:
            basisPathIndex = self.basisPathsNodes.index(pathNodes)
            logger.info("Candidate path is a basis path.")

            # Create a copy of the Path object that represents the basis path:
            # we do not want to modify the IlpProblem object associated with
            # the basis Path object.
            pathCopy = deepcopy(self.basisPaths[basisPathIndex])
            pathCopy.ilpProblem = ilpProblem
            return pathCopy
        except ValueError as e:
            logger.info("Candidate path is not a basis path.")

        # Write the candidate path to a file for further analysis
        # by the Phoenix backend.
        logger.info("Writing nodes along candidate path to file...")
        nodesFile = os.path.join(self.projectConfig.locationTempDir,
                                 config.TEMP_PATH_NODES)
        try:
            nodesFileHandler = open(nodesFile, "w")
        except EnvironmentError as e:
            errMsg = "Error writing nodes along candidate path: %s" % e
            raise GameTimeError(errMsg)
        else:
            with nodesFileHandler:
                nodesFileHandler.write(" ".join(pathNodes))
        logger.info("Writing complete.")

        logger.info("Running the Phoenix program analyzer...")
        logger.info("")
        if phoenixHelper.findConditions(self.projectConfig):
            errMsg = "Error running the Phoenix program analyzer."
            raise GameTimeError(errMsg)
        logger.info("Phoenix program analysis complete.")
        logger.info("")

        logger.info("Reading the line numbers of statements "
                    "along the path...")
        lineNumbersFile = os.path.join(self.projectConfig.locationTempDir,
                                       config.TEMP_PATH_LINE_NUMBERS)
        lineNumbers = Path.readLineNumbersFromFile(lineNumbersFile)
        logger.info("Line numbers of the statements along "
                    "the path read and processed.")

        logger.info("Reading the conditions along the path...")
        conditionsFile = os.path.join(self.projectConfig.locationTempDir,
                                      config.TEMP_PATH_CONDITIONS)
        conditions = Path.readConditionsFromFile(conditionsFile)
        logger.info("Path conditions read and processed.")

        logger.info("Reading the edges that are associated with "
                    "the conditions along the path...")
        conditionEdgesFile = os.path.join(self.projectConfig.locationTempDir,
                                          config.TEMP_PATH_CONDITION_EDGES)
        conditionEdges = Path.readConditionEdgesFromFile(conditionEdgesFile)
        logger.info("Edges read and processed.")

        logger.info("Reading the line numbers and truth values "
                    "of conditional points...")
        conditionTruthsFile = os.path.join(self.projectConfig.locationTempDir,
                                           config.TEMP_PATH_CONDITION_TRUTHS)
        conditionTruths = Path.readConditionTruthsFromFile(conditionTruthsFile)
        logger.info("Path condition truths read and processed.")

        logger.info("Reading information about array accesses...")
        arrayAccessesFile = os.path.join(self.projectConfig.locationTempDir,
                                         config.TEMP_PATH_ARRAY_ACCESSES)
        arrayAccesses = Path.readArrayAccessesFromFile(arrayAccessesFile)
        logger.info("Array accesses information read and processed.")

        logger.info("Reading information about the expressions "
                    "for aggregate accesses...")
        aggIndexExprsFile = os.path.join(self.projectConfig.locationTempDir,
                                         config.TEMP_PATH_AGG_INDEX_EXPRS)
        aggIndexExprs = Path.readAggIndexExprsFromFile(aggIndexExprsFile)
        logger.info("Aggregate accesses information read and processed.")

        logger.info("Reading the SMT query generated by the "
                    "Phoenix program analyzer...")
        smtQueryFile = os.path.join(self.projectConfig.locationTempDir,
                                    "%s.smt" % config.TEMP_PATH_QUERY)
        smtQuery = readQueryFromFile(smtQueryFile)
        logger.info("SMT query read.")

        assignments = {}

        logger.info("Checking the satisfiability of the SMT query...")
        smtSolver = self.projectConfig.smtSolver
        smtSolver.checkSat(smtQuery)
        logger.info("Satisfiability checked.")

        if smtQuery.satisfiability == Satisfiability.SAT:
            logger.info("Candidate path is FEASIBLE.")

            logger.info("Generating assignments...")
            smtModelParser = self.projectConfig.smtModelParser
            assignments = smtModelParser.parseModel(smtQuery.model,
                                                    arrayAccesses,
                                                    aggIndexExprs,
                                                    self.projectConfig)
            logger.info("Assignments generated.")
        elif smtQuery.satisfiability == Satisfiability.UNSAT:
            logger.info("Candidate path is INFEASIBLE.")
        elif smtQuery.satisfiability == Satisfiability.UNKNOWN:
            errMsg = "Candidate path has UNKNOWN satisfiability."
            raise GameTimeError(errMsg)

        if self.projectConfig.debugConfig.DUMP_ALL_QUERIES:
            try:
                allQueriesFile = \
                os.path.join(self.projectConfig.locationTempDir,
                             config.TEMP_PATH_QUERY_ALL)
                allQueriesFileHandler = open(allQueriesFile, "a")
            except EnvironmentError as e:
                errMsg = "Error writing the candidate SMT query: %s" % e
                raise GameTimeError(errMsg)
            else:
                with allQueriesFileHandler:
                    allQueriesFileHandler.write("*** CANDIDATE QUERY ***\n")
                    allQueriesFileHandler.write("%s\n\n" % smtQuery)

        logger.info("Removing temporary path information files...")
        self._removeTempPathFiles()
        logger.info("Temporary path information files removed.")
        logger.info("")

        return Path(ilpProblem, pathNodes, lineNumbers,
                    conditions, conditionEdges, conditionTruths,
                    arrayAccesses, aggIndexExprs,
                    smtQuery, assignments)

    def estimateEdgeWeights(self):
        """Estimates the weights on the edges of the DAG, using the values
        of the basis "Path" objects. The result is stored in the instance
        variable "edgeWeights".

        Precondition: The basis paths have been generated and have values.
        """
        self.dag.resetEdgeWeights()

        basisValues = [basisPath.measuredValue for basisPath
                       in self.basisPaths]
        # By default, we assume a value of 0 for each of the rows in
        # the basis matrix that no replacement could be found for
        # (the `bad' rows in the basis matrix).
        basisValues += [0] * (self.pathDimension - len(basisValues))

        # Estimate the weights on the `non-special' edges of the graph.
        logger.info("Estimating the weights on the `non-special' edges...")
        reducedEdgeWeights = dot(inv(self.basisMatrix), basisValues)
        logger.info("Weights estimated.")

        # Generate the list of edge weights that the integer linear
        # programming problem will use.
        logger.info("Generating the list of weights on all edges...")
        for reducedEdgeIndex, reducedEdge in enumerate(self.dag.edgesReduced):
            self.dag.edgeWeights[self.dag.edgesReducedIndices[reducedEdge]] = \
            reducedEdgeWeights[reducedEdgeIndex]
        logger.info("List generated.")

    def _removeTempPathFiles(self):
        """Removes the temporary path information files that are
        generated when the feasibility of a path is determined.
        """
        nodesFile = os.path.join(self.projectConfig.locationTempDir,
                                 config.TEMP_PATH_NODES)
        removeFile(nodesFile)

        lineNumbersFile = os.path.join(self.projectConfig.locationTempDir,
                                       config.TEMP_PATH_LINE_NUMBERS)
        removeFile(lineNumbersFile)

        conditionsFile = os.path.join(self.projectConfig.locationTempDir,
                                      config.TEMP_PATH_CONDITIONS)
        removeFile(conditionsFile)

        conditionEdgesFile = os.path.join(self.projectConfig.locationTempDir,
                                          config.TEMP_PATH_CONDITION_EDGES)
        removeFile(conditionEdgesFile)

        conditionTruthsFile = os.path.join(self.projectConfig.locationTempDir,
                                           config.TEMP_PATH_CONDITION_TRUTHS)
        removeFile(conditionTruthsFile)

        arrayAccessesFile = os.path.join(self.projectConfig.locationTempDir,
                                         config.TEMP_PATH_ARRAY_ACCESSES)
        removeFile(arrayAccessesFile)

        aggIndexExprsFile = os.path.join(self.projectConfig.locationTempDir,
                                         config.TEMP_PATH_AGG_INDEX_EXPRS)
        removeFile(aggIndexExprsFile)

        smtQueryFile = os.path.join(self.projectConfig.locationTempDir,
                                    "%s.smt" % config.TEMP_PATH_QUERY)
        removeFile(smtQueryFile)

    ### PATH VALUE FUNCTIONS ###
    def writeBasisValuesToFile(self, location, measured=False):
        """Convenience wrapper around the "writePathValuesToFile" method
        that writes the values of the "Path" objects that represent
        the feasible basis paths of the code being analyzed to a file.

        Arguments:
            location:
                Location of the file.
            measured:
                `True` if, and only if, the values that will be written to
                the file are the measured values of the feasible basis paths.
        """
        Analyzer.writePathValuesToFile(self.basisPaths, location, measured)

    def writeTemplateBasisValuesFile(self, location):
        """Creates a template file, at the location provided, which can
        be used as input to the "loadBasisValuesFromFile" method.

        The template file contains instructions on how to specify
        the measured values to be associated with the feasible basis
        "Path" objects, and follows the grammar described in
        the documentation of the "loadBasisValuesFromFile" method.

        @param location Location of the file.
        """
        try:
            templateBasisValuesFileHander = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing the template file to load values "
                      "for the basis Path objects: %s") % e
            raise GameTimeError(errMsg)
        else:
            with templateBasisValuesFileHander:
                projectConfig = self.projectConfig
                templateHeader = \
"""# This template was generated by GameTime during the analysis of
# the function %s in the file located at
# %s.
# Below, supply the values to be associated with the Path objects
# that represent the basis paths.
""" % (projectConfig.func, projectConfig.locationOrigFile)

                contents = []
                contents.append(templateHeader)
                for position in xrange(len(self.basisPaths)):
                    contents.append("# Append the value for basis path %d "
                                    "to the line below." % (position+1))
                    contents.append("%d\t" % (position + 1))
                    contents.append("")
                templateBasisValuesFileHander.write("\n".join(contents))

    def loadBasisValuesFromFile(self, location):
        """Loads the measured values of the "Path" objects that represent
        the feasible basis paths of the code being analyzed from a file.

        Each line of the file should have a pair of numbers separated by
        whitespace: the former is the (one-based) number of a basis
        "Path" object, which is also its (one-based) position in the list
        of basis "Path" objects maintained by this "Analyzer" object, while
        the latter is the value to be associated with the "Path" object.

        Lines that start with a "#" character are assumed to be comments,
        and are thus ignored. For a template file, refer to the
        "writeTemplateBasisValuesFile" method.

        Precondition: The basis paths have been generated.

        @param location Location of the file.
        """
        try:
            basisValuesFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = "Error loading the values of the basis paths: %s" % e
            raise GameTimeError(errMsg)
        else:
            with basisValuesFileHandler:
                basisValuesLines = basisValuesFileHandler.readlines()
                basisValuesLines = [line.strip() for line in basisValuesLines]
                basisValuesLines = [line for line in basisValuesLines
                                    if line != "" and not line.startswith("#")]
                basisValuesLines = [line.split() for line in basisValuesLines]
                self.loadBasisValues([(int(position), int(value))
                                      for position, value in basisValuesLines])

    def loadBasisValues(self, basisValues):
        """Loads the measured values of the "Path" objects that represent
        the feasible basis paths of the code being analyzed from the list of
        tuples provided. Each tuple has two elements: the first element is
        the (one-based) position of a basis "Path" object in the list of
        basis "Path" objects maintained by this "Analyzer" object, and
        the second element is the measured value to be associated with
        the "Path" object.

        Precondition: The basis paths have been generated.

        @param basisValues List of tuples, as described.
        """
        numBasisPaths, numBasisValues = len(self.basisPaths), len(basisValues)
        if numBasisPaths != numBasisValues:
            errMsg = ("There are %d basis paths, but %d values "
                      "were provided.") % (numBasisPaths, numBasisValues)
            raise GameTimeError(errMsg)

        for position, value in basisValues:
            self.basisPaths[position-1].setMeasuredValue(value)

    @staticmethod
    def writePathValuesToFile(paths, location, measured=False):
        """Writes the values of each of the :class:`~gametime.path.Path`
        objects in the list provided to a file.

        Each line of the file is a pair of numbers separated by whitespace:
        the former is the (one-based) number of
        a :class:`~gametime.path.Path` object, which is also its (one-based)
        position in the list provided, while the latter is a value of
        the :class:`~gametime.path.Path` object.

        Arguments:
            paths:
                List of :class:`~gametime.path.Path` objects whose values
                are to be written to a file.
            location:
                Location of the file.
            measured:
                `True` if, and only if, the values that will be written to
                the file are the measured values of the feasible paths.
        """
        try:
            pathValuesFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = "Error writing the values of the paths: %s" % e
            raise GameTimeError(errMsg)
        else:
            with pathValuesFileHandler:
                for position, path in enumerate(paths):
                    pathValue = (path.measuredValue if measured else
                                 path.predictedValue)
                    pathValuesFileHandler.write("%d\t%d\n" %
                                                (position+1, pathValue))

    @staticmethod
    def writeValueToFile(value, location):
        """Write the given `value` into file `location`. `value` is a floating
           point. It is written with 2 decimal points. For compatibility
           purposes, if the `value` is an int, it is written without any decimal
           points
        """
        try:
            valuesFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = "Error writing the value: %s" % e
            raise GameTimeError(errMsg)
        else:
            with valuesFileHandler:
                if (int(value) == value):
                  valuesFileHandler.write("%d\n" % value)
                else:
                  valuesFileHandler.write("%.2f\n" % value)



    ### SERIALIZATION FUNCTIONS ###
    def saveToFile(self, location):
        """Saves the current state of this Analyzer object to a file.

        @param location Location of the file to save the current state
        of this Analyzer object to.
        """
        try:
            logger.info("Saving the Analyzer object to a file...")
            analyzerFileHandler = bz2.BZ2File(location, "w")
        except EnvironmentError as e:
            errMsg = "Error saving the Analyzer object to a file: %s" % e
            raise GameTimeError(errMsg)
        else:
            with analyzerFileHandler:
                pickle.dump(self, analyzerFileHandler)
                logger.info("Analyzer object saved.")

    @staticmethod
    def loadFromFile(location):
        """Loads an Analyzer object from the file whose location is provided.

        @param location Location of the file.
        @return Analyzer object, loaded from the file whose location
        is provided.
        """
        try:
            logger.info("Loading an Analyzer object from a file...")
            analyzerFileHandler = bz2.BZ2File(location, "r")
        except EnvironmentError as e:
            errMsg = "Error loading an Analyzer object: %s" % e
            raise GameTimeError(errMsg)
        else:
            with analyzerFileHandler:
                analyzer = pickle.load(analyzerFileHandler)
                logger.info("Analyzer object loaded.")
                return analyzer

    def writePathsToFiles(self, paths, writePerPath=False, rootDir=None):
        """Utility method that writes information available within the Path
        objects in the list provided to different files.

        All of the files are stored within directories. The hierarchy of these
        directories and files is determined by the "writePerPath" argument.

        If the "writePerPath" argument is True, each directory corresponds
        to one Path object. The contents of each directory are files, one
        for each type of information available within the Path object.
        For example, the conditions of the first Path object in the list will
        be written in the file "[config.TEMP_PATH_CONDITIONS]", located in
        the directory "[config.TEMP_CASE]-1". "config" is the Configuration
        object of this analysis.

        If the "writePerPath" argument is False, which is the default value,
        this hierarchy is `rotated'. Each directory instead corresponds to
        one type of information. The contents of each directory are files,
        one for each Path object. For example, the conditions of the first
        Path object in the list will be written in the file
        "[config.TEMP_PATH_CONDITIONS]-1", located in the directory
        "[config.TEMP_PATH_CONDITIONS]".

        The "rootDir" argument specifies where the directories should be
        created; if None is provided, which is the default value, they are
        created in the temporary directory created by GameTime for
        this analysis. Directories from a previous execution will be
        overwritten.

        @param paths List of Path objects to write to files.
        @param writePerPath Boolean flag, as described. True if each directory
        created corresponds to one Path object; False if each directory
        created corresponds to one type of information available within
        a Path object.
        @param rootDir Location of a root directory, as described.
        """
        rootDir = rootDir or self.projectConfig.locationTempDir

        def generateLocation(infoType):
            """Helper function that returns the location of the file where
            the provided type of information (about a Path object) will be
            written.

            @param infoType Type of information (about a Path object) that
            will be written, provided as a string.
            @retval Location of the file where the information will be written.
            """
            infoDir = os.path.join(rootDir,
                                   ("%s-%s" % (config.TEMP_CASE, pathNum + 1))
                                   if writePerPath else infoType)
            createDir(infoDir)
            infoFile = os.path.join(infoDir,
                                    "%s%s" % (infoType,
                                              ("" if writePerPath
                                               else ("-%s" % (pathNum + 1)))))
            return infoFile

        for pathNum, path in enumerate(paths):
            ilpProblemFile = generateLocation(config.TEMP_PATH_ILP_PROBLEM)
            path.writeIlpProblemToLpFile(ilpProblemFile)

            nodeFile = generateLocation(config.TEMP_PATH_NODES)
            path.writeNodesToFile(nodeFile)

            lineNumbersFile = generateLocation(config.TEMP_PATH_LINE_NUMBERS)
            path.writeLineNumbersToFile(lineNumbersFile)

            conditionsFile = generateLocation(config.TEMP_PATH_CONDITIONS)
            path.writeConditionsToFile(conditionsFile)

            conditionEdgesFile = \
            generateLocation(config.TEMP_PATH_CONDITION_EDGES)
            path.writeConditionEdgesToFile(conditionEdgesFile)

            conditionTruthsFile = \
            generateLocation(config.TEMP_PATH_CONDITION_TRUTHS)
            path.writeConditionTruthsToFile(conditionTruthsFile)

            arrayAccessesFile = \
            generateLocation(config.TEMP_PATH_ARRAY_ACCESSES)
            path.writeArrayAccessesToFile(arrayAccessesFile)

            aggIndexExprsFile = \
            generateLocation(config.TEMP_PATH_AGG_INDEX_EXPRS)
            path.writeAggIndexExprsToFile(aggIndexExprsFile)

            smtQueryFile = "%s.smt" % generateLocation(config.TEMP_PATH_QUERY)
            path.smtQuery.writeSmtQueryToFile(smtQueryFile)

            smtModelFile = generateLocation(config.TEMP_SMT_MODEL)
            path.smtQuery.writeModelToFile(smtModelFile)

            caseFile = generateLocation(config.TEMP_CASE)
            path.writeAssignmentsToFile(caseFile)

            predictedValueFile = \
            generateLocation(config.TEMP_PATH_PREDICTED_VALUE)
            path.writePredictedValueToFile(predictedValueFile)

            measuredValueFile = \
            generateLocation(config.TEMP_PATH_MEASURED_VALUE)
            path.writeMeasuredValueToFile(measuredValueFile)
