#!/usr/bin/env python

"""Defines a class that maintains information about an expression
associated with a temporary index variable.
"""
from typing import Tuple

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


class IndexExpression(object):
    """Maintains information about an expression associated with
    a temporary index variable.
    """

    def __init__(self, name: str, indices: Tuple[int]):
        self.name: str = name
        self.indices: Tuple[int] = indices

    def get_name(self) -> str:
        """Name of the variable in the expression whose information is stored in this object.
        """
        return self.name

    def get_indices(self) -> Tuple[int]:
        """Tuple of the temporary index numbers used as indices in the expression.
        """
        return self.indices

    def __eq__(self, other):
        if type(other) is type(self):
            return self.indices == other.indices
        return False

    def __str__(self):
        result: str = self.name
        for index in self.indices:
            result = "%s %s" % (result, index)
        return result.strip()


class VariableIndexExpression(IndexExpression):
    """Maintains information about an expression associated with
    a temporary index variable, where the expression represents a
    variable.
    """
    def __init__(self, name):
        IndexExpression.__init__(self, name, [])


class ArrayIndexExpression(IndexExpression):
    """Maintains information about an expression associated with
    a temporary index variable, where the expression represents an
    array (or aggregate) access.
    """
    pass
