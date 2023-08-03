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

import nx_helper
import pulp_helper
import clang_helper

from defaults import logger
from gametime_error import GameTimeError
from nx_helper import Dag
from path import Path
from simulator.flexpret_simulator import flexpret_simulator


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
    def get_description(pathType):
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
    def generate_paths(analyzer, numPaths=5, pathType=PathType.WORST_CASE,
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
            PathGenerator._generate_paths(analyzer, numPaths,
                                         pulp_helper.Extremum.LONGEST,
                                         interval, useObExtraction)
        elif pathType == PathType.BEST_CASE:
            logger.info("Generating %d best-case feasible paths..." %
                        numPaths)
            paths = \
            PathGenerator._generate_paths(analyzer, numPaths,
                                         pulp_helper.Extremum.SHORTEST,
                                         interval, useObExtraction)
        if paths is not None:
            logger.info("%d of %d paths have been generated." %
                        (len(paths), numPaths))
            return paths

        if pathType == PathType.ALL_DECREASING:
            logger.info("Generating all feasible paths in decreasing order "
                        "of value...")
            paths = \
            PathGenerator._generate_paths(analyzer, analyzer.dag.numPaths,
                                         pulp_helper.Extremum.LONGEST,
                                         interval, useObExtraction)
        elif pathType == PathType.ALL_INCREASING:
            logger.info("Generating all feasible paths in increasing order "
                        "of value...")
            paths = \
            PathGenerator._generate_paths(analyzer, analyzer.dag.numPaths,
                                         pulp_helper.Extremum.SHORTEST,
                                         interval, useObExtraction)
        if paths is not None:
            logger.info("%d feasible paths have been generated." % len(paths))
            return paths

        if pathType == PathType.RANDOM:
            logger.info("Generating random feasible paths...")
            paths = \
            PathGenerator._generate_paths(analyzer, numPaths, None, interval)
            logger.info("%d of %d paths have been generated." %
                        (len(paths), numPaths))
            return paths
        else:
            raise GameTimeError("Unrecognized path type: %d" % pathType)

    @staticmethod
    def _generate_paths(analyzer, numPaths,
                       extremum=pulp_helper.Extremum.LONGEST,
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
        if nx_helper.has_cycles(analyzer.dag):
            logger.log("Loops in the code have been detected.")
            logger.log("No feasible paths have been generated.")
            return []

        logger.info("")
        startTime = time.perf_counter()

        if useObExtraction:
            beforeTime = time.perf_counter()
            logger.info("Using the new algorithm to extract the longest path")
            logger.info("Finding Least Compatible Delta")
            muMax = pulp_helper.find_least_compatible_mu_max(
                analyzer, analyzer.basisPaths)
            logger.info("Found the least mu_max compatible with measurements: "
                        "%.2f in %.2f seconds" %
                        (muMax, time.perf_counter()- beforeTime))
            analyzer.inferredMuMax = muMax

            beforeTime = time.perf_counter()
            logger.info("Calculating error bounds in the estimate")
            analyzer.errorScaleFactor, path, ilpProblem = \
                pulp_helper.find_worst_expressible_path(
                    analyzer, analyzer.basisPaths, 0)
            logger.info(
                "Total maximal error in estimates is 2 x %.2f x %.2f = %.2f" %
                (analyzer.errorScaleFactor, muMax,
                2 * analyzer.errorScaleFactor * muMax))
            logger.info("Calculated in %.2f ms" % (time.perf_counter()- beforeTime))
        else:
            analyzer.estimate_edge_weights()

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
                candidatePathNodes = nx_helper.get_random_path(analyzer.dag,
                                                            source, sink)
                candidatePathEdges = Dag.get_edges(candidatePathNodes)
                analyzer.add_path_bundled_constraint(candidatePathEdges)

            if useObExtraction:
                candidatePathNodes, ilpProblem = \
                    pulp_helper.find_longest_path_with_delta(
                        analyzer, analyzer.basisPaths, muMax, extremum)
            else:
                candidatePathNodes, ilpProblem = \
                    pulp_helper.find_extreme_path(analyzer,
                                               extremum if extremum is not None
                                               else pulp_helper.Extremum.LONGEST,
                                               interval)
            logger.info("")

            if ilpProblem.objVal is None:
                if (extremum is not None or
                    numCandidatePaths == analyzer.dag.numPaths):
                    logger.info("Unable to find a new candidate path.")
                    break
                elif extremum is None:
                    analyzer.add_path_exclusive_constraint(candidatePathEdges)
                    analyzer.reset_path_bundled_constraints()
                    numCandidatePaths = len(analyzer.pathExclusiveConstraints)
                    continue

            logger.info("Candidate path found.")
            logger.info("Running the candidate path to check feasibility and measure run time")
            candidatePathEdges = Dag.get_edges(candidatePathNodes)
            candidatePathValue = ilpProblem.objVal
            resultPath = Path(ilp_problem=ilpProblem, nodes=candidatePathNodes)

            value = analyzer.measure_path(resultPath, f'feasible-path{currentPathNum}')

            #TODO: replace with actual value of infeasible path
            if value < float('inf'):
                logger.info("Candidate path is feasible.")
                resultPath.set_measured_value(value)
                resultPath.set_predicted_value(candidatePathValue)
                resultPaths.append(resultPath)
                logger.info("Path %d generated." % (currentPathNum+1))
                analyzer.add_path_exclusive_constraint(candidatePathEdges)
                currentPathNum += 1
                numPathsUnsat = 0
            else:
                logger.info("Candidate path is infeasible.")
                analyzer.add_path_exclusive_constraint(candidatePathEdges)
                logger.info("Constraint added.")
                numPathsUnsat += 1

            numCandidatePaths += 1
            if extremum is None:
                analyzer.reset_path_bundled_constraints()
            logger.info("")
            logger.info("")

        analyzer.reset_path_exclusive_constraints()

        logger.info("Time taken to generate paths: %.2f seconds." %
                    (time.perf_counter() - startTime))
        return resultPaths