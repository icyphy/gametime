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

from defaults import logger
from gametime_error import GameTimeError
from nx_helper import Dag
from path import Path
from path_analyzer import PathAnalyzer


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
    def get_description(path_type):
        """

        Parameters:
            path_type :
                One of the predefined path types


        Returns:
            One-word description of the path type provided.

        """
        return (
            "worst"
            if path_type is PathType.WORST_CASE
            else (
                "best"
                if path_type is PathType.BEST_CASE
                else (
                    "random"
                    if path_type is PathType.RANDOM
                    else (
                        "all-dec"
                        if path_type is PathType.ALL_DECREASING
                        else "all-inc" if path_type is PathType.ALL_INCREASING else ""
                    )
                )
            )
        )


class PathGenerator(object):
    """
    Exposes static methods to generate objects of the ``Path`` class that
    represent different types of feasible paths in the code being analyzed.

    This class is closely related to the ``Analyzer`` class: except
    for the private helper methods, all of the static methods
    can also be accessed as instance methods of an ``Analyzer`` object.

    These methods are maintained in this class to keep the codebase cleaner
    and more modular. Instances of this class should not need to be made.

    """

    @staticmethod
    def generate_paths(
        analyzer,
        num_paths=10,
        path_type=PathType.WORST_CASE,
        interval=None,
        use_ob_extraction=False,
    ):
        """
        Generates a list of feasible paths of the code being analyzed,
        each represented by an object of the ``Path`` class.

        The type of the generated paths is determined by the path_type
        argument, which is a class variable of the ``PathType`` class.
        By default, this argument is ``PathType.WORST_CASE``. For
        a description of the types, refer to the documentation of
        the ``PathType`` class.

        The ``num_paths`` argument is an upper bound on how many paths should
        be generated, which is 10 by default. This argument is ignored if
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

        Parameters:
            analyzer:
                ``Analyzer`` object that maintains information about
                the code being analyzed.
            num_paths:
                Upper bound on the number of paths to generate.
            path_type:
                Type of paths to generate, represented by a class variable of
                the ``PathType`` class. The different types of paths are
                described in the documentation of the ``PathType`` class.
            interval:
                ``Interval`` object that represents the interval of
                values that the generated paths can have. If no
                ``Interval`` object is provided, the interval of values
                is considered to be all real numbers.
            use_ob_extraction:
                Boolean value specifiying whether to use overcomplete
                basis extraction algorithm

        Returns:
            List[Path]
                List of feasible paths of the code being analyzed, each
                represented by an object of the ``Path`` class.

        """
        paths = None

        if path_type == PathType.WORST_CASE:
            logger.info("Generating %d worst-case feasible paths..." % num_paths)
            paths = PathGenerator._generate_paths(
                analyzer,
                num_paths,
                pulp_helper.Extremum.LONGEST,
                interval,
                use_ob_extraction,
            )
        elif path_type == PathType.BEST_CASE:
            logger.info("Generating %d best-case feasible paths..." % num_paths)
            paths = PathGenerator._generate_paths(
                analyzer,
                num_paths,
                pulp_helper.Extremum.SHORTEST,
                interval,
                use_ob_extraction,
            )
        if paths is not None:
            logger.info("%d of %d paths have been generated." % (len(paths), num_paths))
            return paths

        if path_type == PathType.ALL_DECREASING:
            logger.info(
                "Generating all feasible paths in decreasing order " "of value..."
            )
            paths = PathGenerator._generate_paths(
                analyzer,
                analyzer.dag.num_paths,
                pulp_helper.Extremum.LONGEST,
                interval,
                use_ob_extraction,
            )
        elif path_type == PathType.ALL_INCREASING:
            logger.info(
                "Generating all feasible paths in increasing order " "of value..."
            )
            paths = PathGenerator._generate_paths(
                analyzer,
                analyzer.dag.num_paths,
                pulp_helper.Extremum.SHORTEST,
                interval,
                use_ob_extraction,
            )
        if paths is not None:
            logger.info("%d feasible paths have been generated." % len(paths))
            return paths

        if path_type == PathType.RANDOM:
            logger.info("Generating random feasible paths...")
            paths = PathGenerator._generate_paths(analyzer, num_paths, None, interval)
            logger.info("%d of %d paths have been generated." % (len(paths), num_paths))
            return paths
        else:
            raise GameTimeError("Unrecognized path type: %d" % path_type)

    @staticmethod
    def _generate_paths(
        analyzer,
        num_paths,
        extremum=pulp_helper.Extremum.LONGEST,
        interval=None,
        use_ob_extraction=False,
    ):
        """
        Helper static method for the ``generate_paths`` static method.
        Generates a list of feasible paths of the code being analyzed,
        each represented by an object of the ``Path`` class.

        Parameters:
            analyzer:
                ``Analyzer`` object that maintains information about
                the code being analyzed.
            num_paths:
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
            use_ob_extraction:
                Boolean value specifiying whether to use overcomplete
                basis extraction algorithm

        Returns:
            List[Path]
                List of feasible paths of the code being analyzed,
                each represented by an object of the ``Path`` class.

        """
        if nx_helper.has_cycles(analyzer.dag):
            logger.log("Loops in the code have been detected.")
            logger.log("No feasible paths have been generated.")
            return []

        logger.info("")
        start_time = time.perf_counter()

        if use_ob_extraction:
            before_time = time.perf_counter()
            logger.info("Using the new algorithm to extract the longest path")
            logger.info("Finding Least Compatible Delta")
            mu_max = pulp_helper.find_least_compatible_mu_max(
                analyzer, analyzer.basis_paths
            )
            logger.info(
                "Found the least mu_max compatible with measurements: "
                "%.2f in %.2f seconds" % (mu_max, time.perf_counter() - before_time)
            )
            analyzer.inferred_mu_max = mu_max

            before_time = time.perf_counter()
            logger.info("Calculating error bounds in the estimate")
            analyzer.error_scale_factor, path, ilp_problem = (
                pulp_helper.find_worst_expressible_path(
                    analyzer, analyzer.basis_paths, 0
                )
            )
            logger.info(
                "Total maximal error in estimates is 2 x %.2f x %.2f = %.2f"
                % (
                    analyzer.error_scale_factor,
                    mu_max,
                    2 * analyzer.error_scale_factor * mu_max,
                )
            )
            logger.info("Calculated in %.2f ms" % (time.perf_counter() - before_time))
        else:
            analyzer.estimate_edge_weights()

        result_paths = []
        current_path_num, num_paths_unsat, num_candidate_paths = 0, 0, 0
        while (
            current_path_num < num_paths
            and num_candidate_paths < analyzer.dag.num_paths
        ):
            logger.info("Currently generating path %d..." % (current_path_num + 1))
            logger.info(
                "So far, %d candidate paths were found to be "
                "unsatisfiable." % num_paths_unsat
            )

            if analyzer.path_dimension == 1:
                warn_msg = (
                    "Basis matrix has dimensions 1x1. "
                    "There is only one path through the function "
                    "under analysis."
                )
                logger.warning(warn_msg)

            logger.info(
                "Finding a candidate path using an integer " "linear program..."
            )
            logger.info("")

            if extremum is None:
                source, sink = analyzer.dag.source, analyzer.dag.sink
                candidate_path_nodes = nx_helper.get_random_path(
                    analyzer.dag, source, sink
                )
                candidate_path_edges = Dag.get_edges(candidate_path_nodes)
                analyzer.add_path_bundled_constraint(candidate_path_edges)

            if use_ob_extraction:
                candidate_path_nodes, ilp_problem = (
                    pulp_helper.find_longest_path_with_delta(
                        analyzer, analyzer.basis_paths, mu_max, extremum
                    )
                )
            else:
                candidate_path_nodes, ilp_problem = pulp_helper.find_extreme_path(
                    analyzer,
                    extremum if extremum is not None else pulp_helper.Extremum.LONGEST,
                    interval,
                )
            logger.info("")

            if ilp_problem.obj_val is None:
                if (
                    extremum is not None
                    or num_candidate_paths == analyzer.dag.num_paths
                ):
                    logger.info("Unable to find a new candidate path.")
                    break
                elif extremum is None:
                    analyzer.add_path_exclusive_constraint(candidate_path_nodes)
                    analyzer.reset_path_bundled_constraints()
                    num_candidate_paths = len(analyzer.path_exclusive_constraints)
                    continue

            logger.info("Candidate path found.")
            candidate_path_edges = Dag.get_edges(candidate_path_nodes)
            candidate_path_value = ilp_problem.obj_val

            result_path = Path(ilp_problem=ilp_problem, nodes=candidate_path_nodes)
            result_path.set_predicted_value(candidate_path_value)

            # Check path feasibility using KLEE/SMT solver
            logger.info("Checking feasibility...")
            path_name = f"feasible-path{current_path_num}"
            path_analyzer = PathAnalyzer(
                analyzer.preprocessed_path,
                analyzer.project_config,
                analyzer.dag,
                result_path,
                path_name,
            )
            is_feasible = path_analyzer.check_feasibility()

            if is_feasible:
                logger.info("Candidate path is feasible.")

                # Measure the path (now that we know it's feasible)
                logger.info("Measuring run time...")
                result_path.path_analyzer = path_analyzer
                result_path.name = path_name
                value = path_analyzer.measure_path(analyzer.backend)
                result_path.set_measured_value(value)
                result_paths.append(result_path)

                logger.info("Path %d generated." % (current_path_num + 1))
                analyzer.add_path_exclusive_constraint(candidate_path_edges)
                current_path_num += 1
                num_paths_unsat = 0
            else:
                logger.info("Candidate path is infeasible.")
                result_path.set_measured_value(float("inf"))
                analyzer.add_path_exclusive_constraint(candidate_path_edges)
                logger.info("Constraint added.")
                num_paths_unsat += 1

            num_candidate_paths += 1
            if extremum is None:
                analyzer.reset_path_bundled_constraints()

        analyzer.reset_path_exclusive_constraints()

        logger.info(
            "Time taken to generate paths: %.2f seconds."
            % (time.perf_counter() - start_time)
        )
        return result_paths
