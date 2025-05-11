#!/usr/bin/env python

"""Defines classes and methods to generate objects of the "Path" class
that represent different types of feasible paths in the code being analyzed,
such as those with the worst-case values.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""

import time

import nxHelper
import pulpHelper

from defaults import logger
from gametimeError import GameTimeError
from nxHelper import Dag
from smt.query import Satisfiability


class PathType(object):
    """Represents the type of paths that can be generated."""

    #: Worst-case feasible paths, arranged in decreasing order of value.
    WORST_CASE = 0

    #: Best-case feasible paths, arranged in increasing order of value.
    BEST_CASE = 1

    #: Random feasible paths.
    RANDOM = 2

    #: All feasible paths, arranged in decreasing order of value.
    ALL_DECREASING = 3

    #: All feasible paths, arranged in increasing order of value.
    ALL_INCREASING = 4

    @staticmethod
    def getDescription(pathType):
        """
        Returns:
            One-word description of the path type provided.
        """
        return ("worst" if pathType is PathType.WORST_CASE else
                "best" if pathType is PathType.BEST_CASE else
                "random" if pathType is PathType.RANDOM else
                "all-dec" if pathType is PathType.ALL_DECREASING else
                "all-inc" if pathType is PathType.ALL_INCREASING else "")


class PathGenerator(object):
    """Exposes static methods to generate objects of the ``Path`` class that
    represent different types of feasible paths in the code being analyzed.

    This class is closely related to the ``Analyzer`` class: except
    for the private helper methods, all of the static methods
    can also be accessed as instance methods of an ``Analyzer`` object.

    These methods are maintained in this class to keep the codebase cleaner
    and more modular. Instances of this class should not need to be made.
    """

    @staticmethod
    def generatePaths(analyzer, numPaths=5, pathType=PathType.WORST_CASE,
                      interval=None, useObExtraction=False):
        """Generates a list of feasible paths of the code being analyzed,
        each represented by an object of the ``Path`` class.

        The type of the generated paths is determined by the pathType
        argument, which is a class variable of the ``PathType`` class.
        By default, this argument is ``PathType.WORST_CASE``. For
        a description of the types, refer to the documentation of
        the ``PathType`` class.

        The ``numPaths`` argument is an upper bound on how many paths should
        be generated, which is 5 by default. This argument is ignored if
        this method is used to generate all of the feasible paths of the code
        being analyzed.

        The ``interval`` argument is an ``Interval`` object that represents
        the interval of values that the generated paths can have. If
        no ``Interval`` object is provided, the interval of values is
        considered to be all real numbers.

        This method is idempotent: a second call to this method will produce
        the same list of ``Path`` objects as the first call, assuming that
        nothing has changed between the two calls.

        Precondition: The basis ``Path`` objects of the input ``Analyzer``
        object have values associated with them. Refer to either the method
        ``loadBasisValuesFromFile`` or the method ``loadBasisValues`` in
        the ``Analyzer`` class.

        Arguments:
            analyzer:
                ``Analyzer`` object that maintains information about
                the code being analyzed.
            numPaths:
                Upper bound on the number of paths to generate.
            pathType:
                Type of paths to generate, represented by a class variable of
                the ``PathType`` class. The different types of paths are
                described in the documentation of the ``PathType`` class.
            interval:
                ``Interval`` object that represents the interval of
                values that the generated paths can have. If no
                ``Interval`` object is provided, the interval of values
                is considered to be all real numbers.
            useObExtraction:
                Boolean value specifiying whether to use overcomplete
                basis extraction algorithm

        Returns:
            List of feasible paths of the code being analyzed, each
            represented by an object of the ``Path`` class.
        """
        paths = None

        if pathType == PathType.WORST_CASE:
            logger.info("Generating %d worst-case feasible paths..." %
                        numPaths)
            paths = \
            PathGenerator._generatePaths(analyzer, numPaths,
                                         pulpHelper.Extremum.LONGEST,
                                         interval, useObExtraction)
        elif pathType == PathType.BEST_CASE:
            logger.info("Generating %d best-case feasible paths..." %
                        numPaths)
            paths = \
            PathGenerator._generatePaths(analyzer, numPaths,
                                         pulpHelper.Extremum.SHORTEST,
                                         interval, useObExtraction)
        if paths is not None:
            logger.info("%d of %d paths have been generated." %
                        (len(paths), numPaths))
            return paths

        if pathType == PathType.ALL_DECREASING:
            logger.info("Generating all feasible paths in decreasing order "
                        "of value...")
            paths = \
            PathGenerator._generatePaths(analyzer, analyzer.dag.numPaths,
                                         pulpHelper.Extremum.LONGEST,
                                         interval, useObExtraction)
        elif pathType == PathType.ALL_INCREASING:
            logger.info("Generating all feasible paths in increasing order "
                        "of value...")
            paths = \
            PathGenerator._generatePaths(analyzer, analyzer.dag.numPaths,
                                         pulpHelper.Extremum.SHORTEST,
                                         interval, useObExtraction)
        if paths is not None:
            logger.info("%d feasible paths have been generated." % len(paths))
            return paths

        if pathType == PathType.RANDOM:
            logger.info("Generating random feasible paths...")
            paths = \
            PathGenerator._generatePaths(analyzer, numPaths, None, interval)
            logger.info("%d of %d paths have been generated." %
                        (len(paths), numPaths))
            return paths
        else:
            raise GameTimeError("Unrecognized path type: %d" % pathType)

    @staticmethod
    def _generatePaths(analyzer, numPaths,
                       extremum=pulpHelper.Extremum.LONGEST,
                       interval=None, useObExtraction=False):
        """Helper static method for the ``generatePaths`` static method.
        Generates a list of feasible paths of the code being analyzed,
        each represented by an object of the ``Path`` class.

        Arguments:
            analyzer:
                ``Analyzer`` object that maintains information about
                the code being analyzed.
            numPaths:
                Upper bound on the number of paths to generate.
            extremum:
                Type of paths to calculate (longest or shortest),
                represented by an element of the ``Extremum`` class in
                the ``pulpHelper`` module.
            interval:
                ``Interval`` object that represents the interval of
                values that the generated paths can have. If
                no ``Interval`` object is provided, the interval of values
                is considered to be all real numbers.
            useObExtraction:
                Boolean value specifiying whether to use overcomplete
                basis extraction algorithm

        Returns:
            List of feasible paths of the code being analyzed,
            each represented by an object of the ``Path`` class.
        """
        if nxHelper.hasCycles(analyzer.dag):
            logger.warn("Loops in the code have been detected.")
            logger.warn("No feasible paths have been generated.")
            return []

        logger.info("")
        startTime = time.clock()

        if useObExtraction:
            beforeTime = time.clock()
            logger.info("Using the new algorithm to extract the longest path")
            logger.info("Finding Least Compatible Delta")
            muMax = pulpHelper.findLeastCompatibleMuMax(
                analyzer, analyzer.basisPaths)
            logger.info("Found the least mu_max compatible with measurements: "
                        "%.2f in %.2f seconds" %
                        (muMax, time.clock() - beforeTime))
            analyzer.inferredMuMax = muMax
            
            beforeTime = time.clock()
            logger.info("Calculating error bounds in the estimate")
            analyzer.errorScaleFactor, path, ilpProblem = \
                pulpHelper.findWorstExpressiblePath(
                    analyzer, analyzer.basisPaths, 0)    
            logger.info(
                "Total maximal error in estimates is 2 x %.2f x %.2f = %.2f" %
                (analyzer.errorScaleFactor, muMax,
                2 * analyzer.errorScaleFactor * muMax))
            logger.info("Calculated in %.2f ms" % (time.clock() - beforeTime))
        else:
            analyzer.estimateEdgeWeights()

        resultPaths = []
        currentPathNum, numPathsUnsat, numCandidatePaths = 0, 0, 0
        while (currentPathNum < numPaths and
               numCandidatePaths < analyzer.dag.numPaths):
            logger.info("Currently generating path %d..." %
                        (currentPathNum+1))
            logger.info("So far, %d candidate paths were found to be "
                        "unsatisfiable." % numPathsUnsat)

            if analyzer.pathDimension == 1:
                warnMsg = ("Basis matrix has dimensions 1x1. "
                           "There is only one path through the function "
                           "under analysis.")
                logger.warn(warnMsg)

            logger.info("Finding a candidate path using an integer "
                        "linear program...")
            logger.info("")

            if extremum is None:
                source, sink = analyzer.dag.source, analyzer.dag.sink
                candidatePathNodes = nxHelper.getRandomPath(analyzer.dag,
                                                            source, sink)
                candidatePathEdges = Dag.getEdges(candidatePathNodes)
                analyzer.addPathBundledConstraint(candidatePathEdges)

            if useObExtraction:
                candidatePathNodes, ilpProblem = \
                    pulpHelper.findLongestPathWithDelta(
                        analyzer, analyzer.basisPaths, muMax, extremum)
            else:
                candidatePathNodes, ilpProblem = \
                    pulpHelper.findExtremePath(analyzer,
                                               extremum if extremum is not None
                                               else pulpHelper.Extremum.LONGEST,
                                               interval)
            logger.info("")

            if ilpProblem.objVal is None:
                if (extremum is not None or
                    numCandidatePaths == analyzer.dag.numPaths):
                    logger.info("Unable to find a new candidate path.")
                    break
                elif extremum is None:
                    analyzer.addPathExclusiveConstraint(candidatePathEdges)
                    analyzer.resetPathBundledConstraints()
                    numCandidatePaths = len(analyzer.pathExclusiveConstraints)
                    continue

            logger.info("Candidate path found.")
            candidatePathEdges = Dag.getEdges(candidatePathNodes)
            candidatePathValue = ilpProblem.objVal

            logger.info("Checking if candidate path is feasible...")
            logger.info("")
            resultPath = analyzer.checkFeasibility(candidatePathNodes,
                                                   ilpProblem)
            querySatisfiability = resultPath.smtQuery.satisfiability
            if querySatisfiability == Satisfiability.SAT:
                logger.info("Candidate path is feasible.")
                resultPath.setPredictedValue(candidatePathValue)
                resultPaths.append(resultPath)
                logger.info("Path %d generated." % (currentPathNum+1))

                # Exclude the path generated from future iterations.
                analyzer.addPathExclusiveConstraint(candidatePathEdges)
                currentPathNum += 1
                numPathsUnsat = 0
            elif querySatisfiability == Satisfiability.UNSAT:
                logger.info("Candidate path is infeasible.")

                logger.info("Finding the edges to exclude...")
                unsatCore = resultPath.smtQuery.unsatCore
                excludeEdges = resultPath.getEdgesForConditions(unsatCore)
                logger.info("Edges to be excluded found.")
                logger.info("Adding constraint to exclude these edges...")
                if len(excludeEdges) > 0:
                    analyzer.addPathExclusiveConstraint(excludeEdges)
                else:
                    analyzer.addPathExclusiveConstraint(candidatePathEdges)
                logger.info("Constraint added.")

                numPathsUnsat += 1

            numCandidatePaths += 1
            if extremum is None:
                analyzer.resetPathBundledConstraints()
            logger.info("")
            logger.info("")

        analyzer.resetPathExclusiveConstraints()

        logger.info("Time taken to generate paths: %.2f seconds." %
                    (time.clock() - startTime))
        return resultPaths
