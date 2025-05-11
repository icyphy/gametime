#!/usr/bin/env python

"""Defines a class that maintains information about an expression
associated with a temporary index variable.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


class IndexExpression(object):
    """Maintains information about an expression associated with
    a temporary index variable.

    Attributes:
        name:
            Name of the variable in the expression.
        indices:
            Tuple of temporary index numbers used as
            indices in the expression.
    """

    def __init__(self, name, indices):
        self.name = name
        self.indices = indices

    def getName(self):
        """
        Returns:
            Name of the variable in the expression
            whose information is stored in this object.
        """
        return self.name

    def getIndices(self):
        """
        Returns:
            Tuple of the temporary index numbers used
            as indices in the expression.
        """
        return self.indices

    def __eq__(self, other):
        if type(other) is type(self):
            return self.indices == other.indices
        return False

    def __str__(self):
        result = self.name
        for index in self.indices:
            result = "%s %s" % (result, index)
        return result.strip()


class VariableIndexExpression(IndexExpression):
    """Maintains information about an expression associated with
    a temporary index variable, where the expression represents a
    variable.

    Attributes:
        name:
            Name of the variable in the expression.
    """
    def __init__(self, name):
        IndexExpression.__init__(self, name, [])


class ArrayIndexExpression(IndexExpression):
    """Maintains information about an expression associated with
    a temporary index variable, where the expression represents an
    array (or aggregate) access.
    """
    pass
