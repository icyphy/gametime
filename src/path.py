#!/usr/bin/env python

"""Defines a class that maintains a representation of, and information about,
a single path in the code that is being analyzed.
"""
from typing import List, Dict, Tuple

import os

from ast import literal_eval

from pulp import PulpError

from gametime_error import GameTimeError
from index_expression import VariableIndexExpression, ArrayIndexExpression, IndexExpression
from pulp_helper import IlpProblem

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


class Path(object):
    """Maintains a representation of, and information about,
    a single path in the code that is being analyzed.
    """

    def __init__(self, ilp_problem: IlpProblem = None, nodes: List[str] = None,
                 line_numbers: List[str] = None,
                 conditions: List[str] = None, condition_edges: Dict[int, Tuple[str]] = None,
                 condition_truths: Dict[str, bool] = None,
                 array_accesses: Dict[str, List[Tuple[int]]] = None,
                 agg_index_exprs: IndexExpression = None, assignments: Dict[str, str] = None,
                 predicted_value: float = 0, measured_value: float = 0):
        #: Integer linear programming problem that, when solved, produced
        #: this path, represented as an ``IlpProblem`` object.
        self.ilp_problem = ilp_problem

        #: IDs of the nodes in a directed acyclic graph along this path,
        #: represented as a list of strings.
        self.nodes = nodes or []

        #: Line numbers of the source-level statements along this path,
        #: represented as a list of positive integers.
        self.line_numbers = line_numbers or []

        #: Conditions along this path, represented as a list of strings.
        self.conditions = conditions or []

        #: Dictionary that associates the number of a condition with
        #: the edge in the directed acyclic graph that is associated with
        #: the condition. The edge is represented as a tuple.
        self.condition_edges = condition_edges or {}

        #: Dictionary that associates the line numbers of the conditional points
        #: in the code being analyzed with their truth values.
        self.condition_truths = condition_truths or {}

        #: Information about array accesses made in conditions along this path,
        #: represented as a dictionary that maps the name of an array to a
        #: list of tuples, each of which contains the numbers of the temporary
        #: index variables in an array access.
        self.array_accesses = array_accesses or {}

        #: Information about the expressions associated with the temporary
        #: index variables of aggregate accesses along this path, represented
        #: as a dictionary that maps the number of a temporary index variable
        #: to an ``IndexExpression`` object.
        self.agg_index_exprs = agg_index_exprs or {}

        #: Dictionary of assignments to variables that would drive an execution
        #: of the code along this path.
        self.assignments = assignments or {}

        #: Predicted value (runtime, energy consumption, etc.)
        #: of this path, represented as a number (either
        #: an integer or a floating-point number).
        self.predicted_value = predicted_value

        #: Measured value (runtime, energy consumption, etc.)
        #: of this path, represented as a number (either
        #: an integer or a floating-point number).
        self.measured_value = measured_value

        self.path_analyzer = None

        self.name = None

    def write_ilp_problem_to_lp_file(self, location) -> None:
        """Writes, to an LP file, the integer linear programming problem that,
        when solved, produced this path.

        Parameters
        ----------
        location :
            Location of the file

        """
        if self.ilp_problem is not None:
            _, extension = os.path.splitext(location)
            if extension.lower() != ".lp":
                location += ".lp"
            try:
                self.ilp_problem.writeLP(location)
            except (PulpError, EnvironmentError) as e:
                err_msg = ("Error writing the integer linear programming "
                           "problem to an LP file: %s") % e
                raise GameTimeError(err_msg)
        else:
            err_msg = ("This path is not associated with an integer linear "
                       "programming problem.")
            raise GameTimeError(err_msg)

    def get_nodes(self) -> str:
        """
        Returns
        -------
        str
            String representation of the IDs of the nodes in
            a directed acyclic graph along this path.

        """
        return " ".join(self.nodes)

    def write_nodes_to_file(self, location: str) -> None:
        """Writes the IDs of the nodes in a directed acyclic graph
        along this path to a file.

        Parameters
        ----------
        location: str :
            Location of the file
            
        """
        try:
            nodes_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = ("Error writing the IDs of the nodes in "
                       "a directed acyclic graph along the path: %s") % e
            raise GameTimeError(err_msg)
        else:
            with nodes_file_handler:
                nodes_file_handler.write(self.get_nodes())

    @staticmethod
    def read_nodes_from_file(location: str) -> List[str]:
        """Reads the IDs of the nodes in a directed acyclic graph
        along a path from a file.

        Parameters
        ----------
        location: str :
            Location of the file
            

        Returns
        -------
        List[str]
            IDs of the nodes in a directed acyclic graph along a path,
            represented as a list of strings.

        """
        try:
            nodes_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = ("Error reading the IDs of the nodes in "
                       "a directed acyclic graph along a path: %s") % e
            raise GameTimeError(err_msg)
        else:
            with nodes_file_handler:
                nodes = nodes_file_handler.readline().strip().split()
                return nodes

    def get_line_numbers(self) -> str:
        """

        Returns
        -------
        str
            String representation of the line numbers of
            the source-level statements that lie along this path.

        """
        return " ".join([str(lineNumber) for lineNumber in self.line_numbers])

    def write_line_numbers_to_file(self, location: str) -> None:
        """Writes the line numbers of the source-level statements that
        lie along this path to a file.

        Parameters
        ----------
        location: str:
            Location of the file

        """
        try:
            line_numbers_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = ("Error writing line numbers of the source-level "
                       "statements along the path: %s") % e
            raise GameTimeError(err_msg)
        else:
            with line_numbers_file_handler:
                line_numbers_file_handler.write(self.get_line_numbers())

    @staticmethod
    def read_line_numbers_from_file(location: str) -> List[int]:
        """Reads the line numbers of the source-level statements that
        lie along a path from a file.

        Parameters
        ----------
        location: str :
            Location of the file

        Returns
        -------
        List[int]
            Line numbers of the source-level statements along this path,
            represented as a list of positive integers.

        """
        try:
            line_numbers_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = ("Error reading line numbers of the source-level "
                       "statements along a path: %s") % e
            raise GameTimeError(err_msg)
        else:
            with line_numbers_file_handler:
                line_numbers = line_numbers_file_handler.readline().strip().split()
                line_numbers = [int(lineNumber) for lineNumber in line_numbers]
                return line_numbers

    def get_conditions(self) -> str:
        """
        Returns
        -------
        str
            String representation of the conditions along this path.

        """
        return "\n".join(self.conditions)

    def write_conditions_to_file(self, location: str) -> None:
        """Writes the conditions along this path to a file.

        Parameters
        ----------
        location: str :
            Location of the file


        """
        try:
            conditions_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = "Error writing conditions along the path: %s" % e
            raise GameTimeError(err_msg)
        else:
            with conditions_file_handler:
                conditions_file_handler.write(self.get_conditions())

    @staticmethod
    def read_conditions_from_file(location: str) -> List[str]:
        """Reads the conditions along a path from a file.

        Parameters
        ----------
        location: str :
            Location of the file

        Returns
        -------
        List[str]
            Conditions along a path, represented as a list of strings.

        """
        try:
            conditions_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = "Error reading conditions along a path: %s" % e
            raise GameTimeError(err_msg)
        else:
            with conditions_file_handler:
                conditions = conditions_file_handler.readlines()
                conditions = [condition.strip() for condition in conditions]
                conditions = [condition for condition in conditions
                              if condition != ""]
                return conditions

    def get_condition_edges(self) -> str:
        """
        Returns
        -------
        str
            String representation of the numbers of the conditions along
            this path, and the edges that are associated with the conditions.

        """
        result = []
        sorted_keys = sorted(self.condition_edges.keys())
        for key in sorted_keys:
            result.append("%s: " % key)
            result.append(" ".join(self.condition_edges[key]))
            result.append("\n")
        return "".join(result)

    def write_condition_edges_to_file(self, location: str) -> None:
        """Writes the numbers of the conditions along this path, and
        the edges that are associated with the conditions, to a file.

        Parameters
        ----------
        location: str :
            Location of the file

        """
        try:
            condition_edges_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = ("Error writing the numbers of the conditions along "
                       "the path, and the edges that are associated with "
                       "the conditions: %s") % e
            raise GameTimeError(err_msg)
        else:
            with condition_edges_file_handler:
                condition_edges_file_handler.write(self.get_condition_edges())

    @staticmethod
    def read_condition_edges_from_file(location: str) -> Dict[int, Tuple[str]]:
        """Reads the numbers of the conditions along a path, and
        the edges that are associated with the conditions, from a file.

        Parameters
        ----------
        location: str :
            Location of the file

        Returns
        -------
         Dict[int, Tuple[str]]
            Dictionary that associates the number of a condition with
            the edge in the directed acyclic graph that is associated with
            the condition. The edge is represented as a tuple.

        """
        try:
            condition_edges_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = ("Error reading the numbers of the conditions along "
                       "a path, and the edges that are associated with "
                       "the conditions: %s") % e
            raise GameTimeError(err_msg)
        else:
            condition_edges = {}
            with condition_edges_file_handler:
                condition_edges_file_lines = condition_edges_file_handler.readlines()
                for line in condition_edges_file_lines:
                    (conditionNum, edge) = line.strip().split(": ")
                    edge = tuple(edge.strip().split(" "))
                    condition_edges[int(conditionNum.strip())] = edge
                return condition_edges

    def get_edges_for_conditions(self, condition_nums: List[int]) -> List[Tuple[str]]:
        """

        Parameters
        ----------
        condition_nums: List[int] :
            List of conditions

        Returns
        -------
        List[Tuple[str]]
            List of the edges that are associated with the conditions
            (along this path) whose numbers are provided. Each edge is
            represented as a tuple, and appears only once in the list.

        """
        return list(set([self.condition_edges[conditionNum]
                         for conditionNum in condition_nums]))

    def get_condition_truths(self) -> str:
        """
        Returns
        -------
        str
            String representation of the line numbers of the conditional points
            in the code being analyzed, along with their truth values.

        """
        result = []
        sorted_keys = sorted([int(key) for key in self.condition_truths.keys()])
        for key in sorted_keys:
            result.append("%s: " % key)
            result.append(str(self.condition_truths[str(key)]))
            result.append("\n")
        return "".join(result)

    def write_condition_truths_to_file(self, location: str) -> None:
        """Writes the line numbers of the conditional points in the code
        being analyzed, along with their truth values, to a file.

        Parameters
        ----------
        location: str :
            Location of the file
        """
        try:
            condition_truths_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = ("Error writing line numbers of the conditional "
                       "points in the code being analyzed, along with "
                       "their truth values: %s") % e
            raise GameTimeError(err_msg)
        else:
            with condition_truths_file_handler:
                condition_truths_file_handler.write(self.get_condition_truths())

    @staticmethod
    def read_condition_truths_from_file(location: str) -> Dict[int, bool]:
        """Reads the line numbers of the conditional points in the code
        being analyzed, along with their truth values along a path,
        from a file.

        Parameters
        ----------
        location: str :
            Location of the file
            

        Returns
        -------
        Dict[int, bool]
            Dictionary that associates the line numbers of
            the conditional points in the code being analyzed with
            their truth values.

        """
        try:
            condition_truths_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = ("Error reading line numbers of the conditional "
                       "points in the code being analyzed, along with "
                       "their truth values along a path: %s") % e
            raise GameTimeError(err_msg)
        else:
            condition_truths = {}
            with condition_truths_file_handler:
                condition_truths_file_lines = \
                    condition_truths_file_handler.readlines()
                for line in condition_truths_file_lines:
                    (lineNumber, conditionTruth) = line.strip().split(": ")
                    condition_truths[lineNumber] = conditionTruth == "True"
                return condition_truths

    def get_array_accesses(self) -> str:
        """
        Returns
        -------
        str
            String representation of the array accesses made in
            conditions along this path.

        """
        result = []
        for array_name in self.array_accesses:
            result.append("%s: " % array_name)
            result.append(str(self.array_accesses[array_name]))
            result.append("\n")
        return "".join(result)

    def write_array_accesses_to_file(self, location: str) -> None:
        """Writes information about the array accesses made in conditions
        along this path to a file.

        Parameters
        ----------
        location: str :
            Location of the file
            

        """
        try:
            array_accesses_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = ("Error writing information about the array accesses "
                       "made in conditions along the path: %s") % e
            raise GameTimeError(err_msg)
        else:
            with array_accesses_file_handler:
                array_accesses_file_handler.write(self.get_array_accesses())

    @staticmethod
    def read_array_accesses_from_file(location: str) -> Dict[str, List[Tuple[int, int]]]:
        """Reads information about the array accesses made in conditions
        along a path from a file.

        Parameters
        ----------
        location: str :
            Location of the file
            

        Returns
        -------
        Dict[str, List[Tuple[int, int]]]
            Dictionary that maps an array name to a list of tuples, each of
            which contains the numbers of the temporary index variables
            in an array access.

        """
        try:
            array_accesses_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = ("Error reading information about the array accesses "
                       "made in conditions along a path: %s") % e
            raise GameTimeError(err_msg)
        else:
            array_accesses = {}
            with array_accesses_file_handler:
                array_access_lines = array_accesses_file_handler.readlines()
                for array_access_line in array_access_lines:
                    # Process the array access information.
                    array_access_line = array_access_line.strip().split(": ")
                    array_name = array_access_line[0]

                    temp_indices_tuples = literal_eval(array_access_line[1])
                    if array_name in array_accesses:
                        array_accesses[array_name].extend(temp_indices_tuples)
                    else:
                        array_accesses[array_name] = temp_indices_tuples
                return array_accesses

    def get_agg_index_exprs(self) -> str:
        """
        Returns
        -------
        str
            String representation of the expressions associated
            with the temporary index variables of aggregate accesses
            along a path.

        """
        result = []
        for index_number in self.agg_index_exprs:
            result.append("%d: " % index_number)
            result.append(str(self.agg_index_exprs[index_number]))
            result.append("\n")
        return "".join(result)

    def write_agg_index_exprs_to_file(self, location: str) -> None:
        """Writes information about the expressions associated with the
        temporary index variables of aggregate accesses along this path
        to a file.

        Parameters
        ----------
        location: str :
            Location of the file
        """
        try:
            agg_index_exprs_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = ("Error writing information about the expressions "
                       "associated with the temporary index variables of "
                       "aggregate accesses along this path: %s") % e
            raise GameTimeError(err_msg)
        else:
            with agg_index_exprs_file_handler:
                agg_index_exprs_file_handler.write(self.get_agg_index_exprs())

    @staticmethod
    def read_agg_index_exprs_from_file(location: str) -> Dict[int, IndexExpression]:
        """Reads, from a file, information about the expressions associated with
        the temporary index variables of aggregate accesses along a path.

        Parameters
        ----------
        location: str :
            Location of the file
            

        Returns
        -------
        Dict[int, IndexExpression]
            Dictionary that maps the number of a temporary index
            variable to an ``IndexExpression`` object.

        """
        try:
            agg_index_exprs_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = ("Error reading information about the expressions "
                       "associated with the temporary index variables of "
                       "aggregate accesses along a path: %s") % e
            raise GameTimeError(err_msg)
        else:
            agg_index_exprs = {}
            with agg_index_exprs_file_handler:
                agg_index_exprs_lines = agg_index_exprs_file_handler.readlines()
                for aggIndexExprsLine in agg_index_exprs_lines:
                    line_tokens = aggIndexExprsLine.strip().split(": ")

                    temp_index_number = int(line_tokens[0])
                    line_tokens = line_tokens[1].split()
                    if len(line_tokens) == 1:
                        var_name = line_tokens[0]
                        agg_index_exprs[temp_index_number] = \
                            VariableIndexExpression(var_name)
                    else:
                        array_var_name = line_tokens[0]
                        indices = tuple(int(index) for index in line_tokens[1:])
                        agg_index_exprs[temp_index_number] = \
                            ArrayIndexExpression(array_var_name, indices)
                return agg_index_exprs

    def get_assignments(self) -> str:
        """
        Returns
        -------
        str
            String representation of the assignments to variables
            that would drive an execution of the code under analysis
            along this path.

        """
        result = []
        for key in sorted(self.assignments.keys()):
            result.append("%s = %s;" % (key, self.assignments[key]))
            result.append("\n")
        return "".join(result)

    def write_assignments_to_file(self, location: str) -> None:
        """Writes the assignments to variables that would drive an execution
        of the code under analysis along this path to a file.

        Parameters
        ----------
        location: str :
            Location of the file


        """
        try:
            assignment_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = ("Error writing the assignments to variables "
                       "that would drive an execution of the code "
                       "along the path: %s") % e
            raise GameTimeError(err_msg)
        else:
            with assignment_file_handler:
                assignment_file_handler.write(self.get_assignments())

    @staticmethod
    def read_assignments_from_file(location: str) -> Dict[str, str]:
        """Reads, from a file, the assignments to variables that would
        drive an execution of the code under analysis along a path.

        Parameters
        ----------
        location: str :
            Location of the file
            

        Returns
        -------
        Dict[str, str]
            Dictionary of assignments to variables that would
            drive an execution of the code under analysis along a path.

        """
        try:
            assignment_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = ("Error reading the assignments to variables "
                       "that would drive an execution of the code "
                       "along a path: %s") % e
            raise GameTimeError(err_msg)
        else:
            assignments = {}
            with assignment_file_handler:
                assignment_file_lines = assignment_file_handler.readlines()
                for line in assignment_file_lines:
                    (variable, assignment) = \
                        line.strip().replace(";", "").split(" = ")
                    assignments[variable] = assignment
                return assignments

    def set_predicted_value(self, value: float):
        """Sets the predicted value (runtime, energy consumption, etc.)
        of this path.

        Parameters
        ----------
        value: float :
            Value to set as the predicted value of this path

        """
        self.predicted_value = value

    def get_predicted_value(self) -> str:
        """
        Returns
        -------
        str
            String representation of the predicted value
            (runtime, energy consumption, etc.) of this path.

        """
        return "%g" % self.predicted_value

    def write_predicted_value_to_file(self, location: str) -> None:
        """Writes the predicted value of this path to a file.   
        
        location: str :
            Location of the file

        """
        try:
            predicted_value_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = ("Error writing the predicted value of the path "
                       "to the file located at %s: %s" % (location, e))
            raise GameTimeError(err_msg)
        else:
            with predicted_value_file_handler:
                predicted_value_file_handler.write(self.get_predicted_value())

    @staticmethod
    def read_predicted_value_from_file(location: str) -> float:
        """Reads the predicted value of a path from a file.

        Parameters
        ----------
        location: str :
            Location of the file

        Returns
        -------
        float
            Predicted value of a path, represented as a number
            (either an integer or a floating-point number).

        """
        try:
            predicted_value_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = ("Error reading the predicted value of a path from "
                       "the file located at %s: %s" % (location, e))
            raise GameTimeError(err_msg)
        else:
            with predicted_value_file_handler:
                line = predicted_value_file_handler.readline().strip()
                try:
                    result = int(line)
                except ValueError:
                    try:
                        result = float(line)
                    except ValueError:
                        err_msg = ("The following line, in the file located "
                                   "at %s, does not represent a valid "
                                   "predicted value of a path: %s" %
                                   (location, line))
                        raise GameTimeError(err_msg)
                return result

    def set_measured_value(self, value: float) -> None:
        """Sets the measured value (runtime, energy consumption, etc.)
        of this path.

        Parameters
        ----------
        value: float :
            Value to set as the measured value of this path

        """
        self.measured_value = value

    def get_measured_value(self) -> str:
        """
        Returns
        -------
        str
            String representation of the measured value
            (runtime, energy consumption, etc.) of this path.

        """
        return "%g" % self.measured_value

    def write_measured_value_to_file(self, location: str) -> None:
        """Writes the measured value of this path to a file.

        Parameters
        ----------
        location: str :
            Location of the file

        """
        try:
            measured_value_file_handler = open(location, "w")
        except EnvironmentError as e:
            err_msg = ("Error writing the measured value of the path "
                       "to the file located at %s: %s" % (location, e))
            raise GameTimeError(err_msg)
        else:
            with measured_value_file_handler:
                measured_value_file_handler.write(self.get_measured_value())

    @staticmethod
    def read_measured_value_from_file(location: str) -> float:
        """Reads the measured value of a path from a file.

        Parameters
        ----------
        location: str :
            Location of the file

        Returns
        -------
        float
            Measured value of a path, represented as a number
            (either an integer or a floating-point number).

        """
        try:
            measured_value_file_handler = open(location, "r")
        except EnvironmentError as e:
            err_msg = ("Error reading the measured value of a path from "
                       "the file located at %s: %s" % (location, e))
            raise GameTimeError(err_msg)
        else:
            with measured_value_file_handler:
                line = measured_value_file_handler.readline().strip()
                try:
                    result = int(line)
                except ValueError:
                    try:
                        result = float(line)
                    except ValueError:
                        err_msg = ("The following line, in the file located "
                                   "at %s, does not represent a valid "
                                   "measured value of a path: %s" %
                                   (location, line))
                        raise GameTimeError(err_msg)
                return result

    def __str__(self):
        result = []
        result.append("*** Node IDs ***")
        result.append("%s\n" % self.get_nodes())
        result.append("*** Line numbers ***")
        result.append("%s\n" % self.get_line_numbers())
        result.append("*** Conditions ***")
        result.append("%s\n" % self.get_conditions())
        result.append("*** Condition truths ***")
        result.append(self.get_condition_truths())
        result.append("*** Array accesses ***")
        result.append(self.get_array_accesses())
        result.append("*** Aggregate access index expressions ***")
        result.append(self.get_agg_index_exprs())
        result.append("*** Assignments ***")
        result.append(self.get_assignments())
        result.append("*** Predicted value: %s ***" % self.get_predicted_value())
        result.append("*** Measured value: %s ***" % self.get_measured_value())
        result.append("")
        return "\n".join(result)
