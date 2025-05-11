#!/usr/bin/env python

"""Defines a class that maintains a representation of, and information about,
a single path in the code that is being analyzed.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


import os

from ast import literal_eval

from pulp import PulpError

from gametimeError import GameTimeError
from indexExpression import VariableIndexExpression, ArrayIndexExpression


class Path(object):
    """Maintains a representation of, and information about,
    a single path in the code that is being analyzed.

    Attributes:
        ilpProblem:
            :class:`~gametime.ilpProblem.IlpProblem` object that represents
            the integer linear programming problem that, when solved,
            produced this path.
        nodes:
            IDs of the nodes in a directed acyclic graph along this path,
            represented as a list of strings.
        lineNumbers:
            Line numbers of the source-level statements along this path,
            represented as a list of positive integers.
        conditions:
            Conditions along this path, represented as a list of strings.
        conditionEdges:
            Dictionary that associates the number of a condition with
            the edge in the directed acyclic graph that is associated
            with the condition, represented as a tuple.
        conditionTruths:
            Dictionary that associates the line numbers of the conditional
            points in the code being analyzed with their truth values.
        arrayAccesses:
            Information about array accesses made in conditions along
            this path, represented as a dictionary that maps the name of
            an array to a list of tuples, each of which contains
            the numbers of the temporary index variables in an array access.
        aggIndexExprs:
            Information about the expressions associated with the temporary
            index variables of aggregate accesses along this path, represented
            as a dictionary that maps the number of a temporary index variable
            to an :class:`~gametime.indexExpression.IndexExpression` object.
        smtQuery:
            ``Query`` object that represents the SMT query used to determine
            the feasibility of this path.
        assignments:
            Dictionary of assignments to variables that would drive
            an execution of the code along this path.
        predictedValue:
            Predicted value (runtime, energy consumption, etc.) of this path.
        measuredValue:
            Measured value (runtime, energy consumption, etc.) of this path.
    """

    def __init__(self, ilpProblem=None, nodes=None, lineNumbers=None,
                 conditions=None, conditionEdges=None, conditionTruths=None,
                 arrayAccesses=None, aggIndexExprs=None,
                 smtQuery=None, assignments=None,
                 predictedValue=0, measuredValue=0):
        #: Integer linear programming problem that, when solved, produced
        #: this path, represented as an ``IlpProblem`` object.
        self.ilpProblem = ilpProblem

        #: IDs of the nodes in a directed acyclic graph along this path,
        #: represented as a list of strings.
        self.nodes = nodes or []

        #: Line numbers of the source-level statements along this path,
        #: represented as a list of positive integers.
        self.lineNumbers = lineNumbers or []

        #: Conditions along this path, represented as a list of strings.
        self.conditions = conditions or []

        #: Dictionary that associates the number of a condition with
        #: the edge in the directed acyclic graph that is associated with
        #: the condition. The edge is represented as a tuple.
        self.conditionEdges = conditionEdges or {}

        #: Dictionary that associates the line numbers of the conditional points
        #: in the code being analyzed with their truth values.
        self.conditionTruths = conditionTruths or {}

        #: Information about array accesses made in conditions along this path,
        #: represented as a dictionary that maps the name of an array to a
        #: list of tuples, each of which contains the numbers of the temporary
        #: index variables in an array access.
        self.arrayAccesses = arrayAccesses or {}

        #: Information about the expressions associated with the temporary
        #: index variables of aggregate accesses along this path, represented
        #: as a dictionary that maps the number of a temporary index variable
        #: to an ``IndexExpression`` object.
        self.aggIndexExprs = aggIndexExprs or {}

        #: SMT query that was used to determine the feasibility of this path,
        #: represented as a ``Query`` object.
        self.smtQuery = smtQuery

        #: Dictionary of assignments to variables that would drive an execution
        #: of the code along this path.
        self.assignments = assignments or {}

        #: Predicted value (runtime, energy consumption, etc.)
        #: of this path, represented as a number (either
        #: an integer or a floating-point number).
        self.predictedValue = predictedValue

        #: Measured value (runtime, energy consumption, etc.)
        #: of this path, represented as a number (either
        #: an integer or a floating-point number).
        self.measuredValue = measuredValue

    def writeIlpProblemToLpFile(self, location):
        """
        Writes, to an LP file, the integer linear programming problem that,
        when solved, produced this path.

        Arguments:
            location:
                Location of the file.
        """
        if self.ilpProblem is not None:
            _, extension = os.path.splitext(location)
            if extension.lower() != ".lp":
                location = location + ".lp"
            try:
                self.ilpProblem.writeLP(location)
            except (PulpError, EnvironmentError) as e:
                errMsg = ("Error writing the integer linear programming "
                          "problem to an LP file: %s") % e
                raise GameTimeError(errMsg)
        else:
            errMsg = ("This path is not associated with an integer linear "
                      "programming problem.")
            raise GameTimeError(errMsg)

    def getNodes(self):
        """
        Returns:
            String representation of the IDs of the nodes in
            a directed acyclic graph along this path.
        """
        return " ".join(self.nodes)

    def writeNodesToFile(self, location):
        """
        Writes the IDs of the nodes in a directed acyclic graph
        along this path to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            nodesFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing the IDs of the nodes in "
                      "a directed acyclic graph along the path: %s") % e
            raise GameTimeError(errMsg)
        else:
            with nodesFileHandler:
                nodesFileHandler.write(self.getNodes())

    @staticmethod
    def readNodesFromFile(location):
        """
        Reads the IDs of the nodes in a directed acyclic graph
        along a path from a file.

        Arguments:
            location:
                Location of the file.

        Returns:
            IDs of the nodes in a directed acyclic graph along a path,
            represented as a list of strings.
        """
        try:
            nodesFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = ("Error reading the IDs of the nodes in "
                      "a directed acyclic graph along a path: %s") % e
            raise GameTimeError(errMsg)
        else:
            with nodesFileHandler:
                nodes = nodesFileHandler.readline().strip().split()
                return nodes

    def getLineNumbers(self):
        """
        Returns:
            String representation of the line numbers of
            the source-level statements that lie along this path.
        """
        return " ".join([str(lineNumber) for lineNumber in self.lineNumbers])

    def writeLineNumbersToFile(self, location):
        """
        Writes the line numbers of the source-level statements that
        lie along this path to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            lineNumbersFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing line numbers of the source-level "
                      "statements along the path: %s") % e
            raise GameTimeError(errMsg)
        else:
            with lineNumbersFileHandler:
                lineNumbersFileHandler.write(self.getLineNumbers())

    @staticmethod
    def readLineNumbersFromFile(location):
        """
        Reads the line numbers of the source-level statements that
        lie along a path from a file.

        Arguments:
            location:
                Location of the file.

        Returns:
            Line numbers of the source-level statements along this path,
            represented as a list of positive integers.
        """
        try:
            lineNumbersFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = ("Error reading line numbers of the source-level "
                      "statements along a path: %s") % e
            raise GameTimeError(errMsg)
        else:
            with lineNumbersFileHandler:
                lineNumbers = lineNumbersFileHandler.readline().strip().split()
                lineNumbers = [int(lineNumber) for lineNumber in lineNumbers]
                return lineNumbers

    def getConditions(self):
        """
        Returns:
            String representation of the conditions along this path.
        """
        return "\n".join(self.conditions)

    def writeConditionsToFile(self, location):
        """
        Writes the conditions along this path to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            conditionsFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = "Error writing conditions along the path: %s" % e
            raise GameTimeError(errMsg)
        else:
            with conditionsFileHandler:
                conditionsFileHandler.write(self.getConditions())

    @staticmethod
    def readConditionsFromFile(location):
        """
        Reads the conditions along a path from a file.

        Arguments:
            location:
                Location of the file.

        Returns:
            Conditions along a path, represented as a list of strings.
        """
        try:
            conditionsFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = "Error reading conditions along a path: %s" % e
            raise GameTimeError(errMsg)
        else:
            with conditionsFileHandler:
                conditions = conditionsFileHandler.readlines()
                conditions = [condition.strip() for condition in conditions]
                conditions = [condition for condition in conditions
                              if condition is not ""]
                return conditions

    def getConditionEdges(self):
        """
        Returns:
            String representation of the numbers of the conditions along
            this path, and the edges that are associated with the conditions.
        """
        result = []
        sortedKeys = sorted(self.conditionEdges.keys())
        for key in sortedKeys:
            result.append("%s: " % key)
            result.append(" ".join(self.conditionEdges[key]))
            result.append("\n")
        return "".join(result)

    def writeConditionEdgesToFile(self, location):
        """
        Writes the numbers of the conditions along this path, and
        the edges that are associated with the conditions, to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            conditionEdgesFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing the numbers of the conditions along "
                      "the path, and the edges that are associated with "
                      "the conditions: %s") % e
            raise GameTimeError(errMsg)
        else:
            with conditionEdgesFileHandler:
                conditionEdgesFileHandler.write(self.getConditionEdges())

    @staticmethod
    def readConditionEdgesFromFile(location):
        """
        Reads the numbers of the conditions along a path, and
        the edges that are associated with the conditions, from a file.

        Arguments:
            location:
                Location of the file.

        Returns:
            Dictionary that associates the number of a condition with
            the edge in the directed acyclic graph that is associated with
            the condition. The edge is represented as a tuple.
        """
        try:
            conditionEdgesFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = ("Error reading the numbers of the conditions along "
                      "a path, and the edges that are associated with "
                      "the conditions: %s") % e
            raise GameTimeError(errMsg)
        else:
            conditionEdges = {}
            with conditionEdgesFileHandler:
                conditionEdgesFileLines = conditionEdgesFileHandler.readlines()
                for line in conditionEdgesFileLines:
                    (conditionNum, edge) = line.strip().split(": ")
                    edge = tuple(edge.strip().split(" "))
                    conditionEdges[int(conditionNum.strip())] = edge
                return conditionEdges

    def getEdgesForConditions(self, conditionNums):
        """
        Arguments:
            conditionNums:
                List of (non-negative) numbers of conditions along this path.

        Returns:
            List of the edges that are associated with the conditions
            (along this path) whose numbers are provided. Each edge is
            represented as a tuple, and appears only once in the list.
        """
        return list(set([self.conditionEdges[conditionNum]
                         for conditionNum in conditionNums]))

    def getConditionTruths(self):
        """
        Returns:
            String representation of the line numbers of the conditional points
            in the code being analyzed, along with their truth values.
        """
        result = []
        sortedKeys = sorted([int(key) for key in self.conditionTruths.keys()])
        for key in sortedKeys:
            result.append("%s: " % key)
            result.append(str(self.conditionTruths[str(key)]))
            result.append("\n")
        return "".join(result)

    def writeConditionTruthsToFile(self, location):
        """
        Writes the line numbers of the conditional points in the code
        being analyzed, along with their truth values, to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            conditionTruthsFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing line numbers of the conditional "
                      "points in the code being analyzed, along with "
                      "their truth values: %s") % e
            raise GameTimeError(errMsg)
        else:
            with conditionTruthsFileHandler:
                conditionTruthsFileHandler.write(self.getConditionTruths())

    @staticmethod
    def readConditionTruthsFromFile(location):
        """
        Reads the line numbers of the conditional points in the code
        being analyzed, along with their truth values along a path,
        from a file.

        Arguments:
            location:
                Location of the file.

        Returns:
            Dictionary that associates the line numbers of
            the conditional points in the code being analyzed with
            their truth values.
        """
        try:
            conditionTruthsFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = ("Error reading line numbers of the conditional "
                      "points in the code being analyzed, along with "
                      "their truth values along a path: %s") % e
            raise GameTimeError(errMsg)
        else:
            conditionTruths = {}
            with conditionTruthsFileHandler:
                conditionTruthsFileLines = \
                conditionTruthsFileHandler.readlines()
                for line in conditionTruthsFileLines:
                    (lineNumber, conditionTruth) = line.strip().split(": ")
                    conditionTruths[lineNumber] = conditionTruth == "True"
                return conditionTruths

    def getArrayAccesses(self):
        """
        Returns:
            String representation of the array accesses made in
            conditions along this path.
        """
        result = []
        for arrayName in self.arrayAccesses:
            result.append("%s: " % arrayName)
            result.append(str(self.arrayAccesses[arrayName]))
            result.append("\n")
        return "".join(result)

    def writeArrayAccessesToFile(self, location):
        """
        Writes information about the array accesses made in conditions
        along this path to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            arrayAccessesFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing information about the array accesses "
                      "made in conditions along the path: %s") % e
            raise GameTimeError(errMsg)
        else:
            with arrayAccessesFileHandler:
                arrayAccessesFileHandler.write(self.getArrayAccesses())

    @staticmethod
    def readArrayAccessesFromFile(location):
        """
        Reads information about the array accesses made in conditions
        along a path from a file.

        Arguments:
            location:
                Location of the file.

        Returns:
            Dictionary that maps an array name to a list of tuples, each of
            which contains the numbers of the temporary index variables
            in an array access.
        """
        try:
            arrayAccessesFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = ("Error reading information about the array accesses "
                      "made in conditions along a path: %s") % e
            raise GameTimeError(errMsg)
        else:
            arrayAccesses = {}
            with arrayAccessesFileHandler:
                arrayAccessLines = arrayAccessesFileHandler.readlines()
                for arrayAccessLine in arrayAccessLines:
                    # Process the array access information.
                    arrayAccessLine = arrayAccessLine.strip().split(": ")
                    arrayName = arrayAccessLine[0]

                    tempIndicesTuples = literal_eval(arrayAccessLine[1])
                    if arrayName in arrayAccesses:
                        arrayAccesses[arrayName].extend(tempIndicesTuples)
                    else:
                        arrayAccesses[arrayName] = tempIndicesTuples
                return arrayAccesses

    def getAggIndexExprs(self):
        """
        Returns:
            String representation of the expressions associated
            with the temporary index variables of aggregate accesses
            along a path.
        """
        result = []
        for indexNumber in self.aggIndexExprs:
            result.append("%d: " % indexNumber)
            result.append(str(self.aggIndexExprs[indexNumber]))
            result.append("\n")
        return "".join(result)

    def writeAggIndexExprsToFile(self, location):
        """
        Writes information about the expressions associated with the
        temporary index variables of aggregate accesses along this path
        to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            aggIndexExprsFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing information about the expressions "
                      "associated with the temporary index variables of "
                      "aggregate accesses along this path: %s") % e
            raise GameTimeError(errMsg)
        else:
            with aggIndexExprsFileHandler:
                aggIndexExprsFileHandler.write(self.getAggIndexExprs())

    @staticmethod
    def readAggIndexExprsFromFile(location):
        """
        Reads, from a file, information about the expressions associated with
        the temporary index variables of aggregate accesses along a path.

        Arguments:
            location:
                Location of the file.

        Returns:
            Dictionary that maps the number of a temporary index
            variable to an ``IndexExpression`` object.
        """
        try:
            aggIndexExprsFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = ("Error reading information about the expressions "
                      "associated with the temporary index variables of "
                      "aggregate accesses along a path: %s") % e
            raise GameTimeError(errMsg)
        else:
            aggIndexExprs = {}
            with aggIndexExprsFileHandler:
                aggIndexExprsLines = aggIndexExprsFileHandler.readlines()
                for aggIndexExprsLine in aggIndexExprsLines:
                    lineTokens = aggIndexExprsLine.strip().split(": ")

                    tempIndexNumber = int(lineTokens[0])
                    lineTokens = lineTokens[1].split()
                    if len(lineTokens) == 1:
                        varName = lineTokens[0]
                        aggIndexExprs[tempIndexNumber] = \
                        VariableIndexExpression(varName)
                    else:
                        arrayVarName = lineTokens[0]
                        indices = tuple(int(index) for index in lineTokens[1:])
                        aggIndexExprs[tempIndexNumber] = \
                        ArrayIndexExpression(arrayVarName, indices)
                return aggIndexExprs

    def getAssignments(self):
        """
        Returns:
            String representation of the assignments to variables
            that would drive an execution of the code under analysis
            along this path.
        """
        result = []
        for key in sorted(self.assignments.keys()):
            result.append("%s = %s;" % (key, self.assignments[key]))
            result.append("\n")
        return "".join(result)

    def writeAssignmentsToFile(self, location):
        """
        Writes the assignments to variables that would drive an execution
        of the code under analysis along this path to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            assignmentFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing the assignments to variables "
                      "that would drive an execution of the code "
                      "along the path: %s") % e
            raise GameTimeError(errMsg)
        else:
            with assignmentFileHandler:
                assignmentFileHandler.write(self.getAssignments())

    @staticmethod
    def readAssignmentsFromFile(location):
        """
        Reads, from a file, the assignments to variables that would
        drive an execution of the code under analysis along a path.

        Arguments:
            location:
                Location of the file.

        Returns:
            Dictionary of assignments to variables that would
            drive an execution of the code under analysis along a path.
        """
        try:
            assignmentFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = ("Error reading the assignments to variables "
                      "that would drive an execution of the code "
                      "along a path: %s") % e
            raise GameTimeError(errMsg)
        else:
            assignments = {}
            with assignmentFileHandler:
                assignmentFileLines = assignmentFileHandler.readlines()
                for line in assignmentFileLines:
                    (variable, assignment) = \
                    line.strip().replace(";", "").split(" = ")
                    assignments[variable] = assignment
                return assignments

    def setPredictedValue(self, value):
        """Sets the predicted value (runtime, energy consumption, etc.)
        of this path.

        Arguments:
            value:
                Value to set as the predicted value of this path.
        """
        self.predictedValue = value

    def getPredictedValue(self):
        """
        Returns:
            String representation of the predicted value
            (runtime, energy consumption, etc.) of this path.
        """
        return "%g" % self.predictedValue

    def writePredictedValueToFile(self, location):
        """Writes the predicted value of this path to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            predictedValueFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing the predicted value of the path "
                      "to the file located at %s: %s" % (location, e))
            raise GameTimeError(errMsg)
        else:
            with predictedValueFileHandler:
                predictedValueFileHandler.write(self.getPredictedValue())

    @staticmethod
    def readPredictedValueFromFile(location):
        """Reads the predicted value of a path from a file.

        Arguments:
            location:
                Location of the file.

        Returns:
            Predicted value of a path, represented as a number
            (either an integer or a floating-point number).
        """
        try:
            predictedValueFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = ("Error reading the predicted value of a path from "
                      "the file located at %s: %s" % (location, e))
            raise GameTimeError(errMsg)
        else:
            with predictedValueFileHandler:
                line = predictedValueFileHandler.readline().strip()
                try:
                    result = int(line)
                except ValueError:
                    try:
                        result = float(line)
                    except ValueError:
                        errMsg = ("The following line, in the file located "
                                  "at %s, does not represent a valid "
                                  "predicted value of a path: %s" %
                                  (location, line))
                        raise GameTimeError(errMsg)
                return result

    def setMeasuredValue(self, value):
        """Sets the measured value (runtime, energy consumption, etc.)
        of this path.

        Arguments:
            value:
                Value to set as the measured value of this path.
        """
        self.measuredValue = value

    def getMeasuredValue(self):
        """
        Returns:
            String representation of the measured value
            (runtime, energy consumption, etc.) of this path.
        """
        return "%g" % self.measuredValue

    def writeMeasuredValueToFile(self, location):
        """Writes the measured value of this path to a file.

        Arguments:
            location:
                Location of the file.
        """
        try:
            measuredValueFileHandler = open(location, "w")
        except EnvironmentError as e:
            errMsg = ("Error writing the measured value of the path "
                      "to the file located at %s: %s" % (location, e))
            raise GameTimeError(errMsg)
        else:
            with measuredValueFileHandler:
                measuredValueFileHandler.write(self.getMeasuredValue())

    @staticmethod
    def readMeasuredValueFromFile(location):
        """Reads the measured value of a path from a file.

        Arguments:
            location:
                Location of the file.

        Returns:
            Measured value of a path, represented as a number
            (either an integer or a floating-point number).
        """
        try:
            measuredValueFileHandler = open(location, "r")
        except EnvironmentError as e:
            errMsg = ("Error reading the measured value of a path from "
                      "the file located at %s: %s" % (location, e))
            raise GameTimeError(errMsg)
        else:
            with measuredValueFileHandler:
                line = measuredValueFileHandler.readline().strip()
                try:
                    result = int(line)
                except ValueError:
                    try:
                        result = float(line)
                    except ValueError:
                        errMsg = ("The following line, in the file located "
                                  "at %s, does not represent a valid "
                                  "measured value of a path: %s" %
                                  (location, line))
                        raise GameTimeError(errMsg)
                return result

    def __str__(self):
        result = []
        result.append("*** Node IDs ***")
        result.append("%s\n" % self.getNodes())
        result.append("*** Line numbers ***")
        result.append("%s\n" % self.getLineNumbers())
        result.append("*** Conditions ***")
        result.append("%s\n" % self.getConditions())
        result.append("*** Condition truths ***")
        result.append(self.getConditionTruths())
        result.append("*** Array accesses ***")
        result.append(self.getArrayAccesses())
        result.append("*** Aggregate access index expressions ***")
        result.append(self.getAggIndexExprs())
        result.append("*** SMT query ***")
        result.append("%s" % self.smtQuery)
        result.append("*** Assignments ***")
        result.append(self.getAssignments())
        result.append("*** Predicted value: %s ***" % self.getPredictedValue())
        result.append("*** Measured value: %s ***" % self.getMeasuredValue())
        result.append("")
        return "\n".join(result)
