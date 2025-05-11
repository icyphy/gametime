#!/usr/bin/env python

"""Defines a class that maintains a representation of,
and information about, an interval of values.
"""

"""See the LICENSE file, located in the root directory of
the source distribution and
at http://verifun.eecs.berkeley.edu/gametime/about/LICENSE,
for details on the GameTime license and authors.
"""


class Interval(object):
    """Maintains a representation of, and information about,
    an interval of values.

    Attributes:
        lower:
            Lower bound of the interval. The lower bound is itself
            included in the interval. If this attribute is `None`,
            the interval has no finite lower bound.
        upper:
            Upper bound of the interval. The upper bound is itself
            included in the interval. If this attribute is `None`,
            the interval has no finite upper bound.
    """

    def __init__(self, lower=None, upper=None):
        if lower is not None and upper is not None:
            lower, upper = sorted((lower, upper))
        self.lower = lower
        self.upper = upper

    def __str__(self):
        return ("%s%s, %s%s" %
                ("(" if self.lower is None else "[",
                 (self.lower or "-Infinity"),
                 (self.upper or "Infinity"),
                 ")" if self.upper is None else "]"))

    @property
    def lowerBound(self):
        """Lower bound of the interval represented by this object,
        or `None` if the interval has no finite lower bound.
        """
        return self.lower

    @property
    def upperBound(self):
        """Upper bound of the interval represented by this object,
        or `None` if the interval has no finite upper bound.
        """
        return self.upper

    def hasFiniteLowerBound(self):
        """
        Returns:
            `True` if, and only if, the represented interval has
            a finite lower bound.
        """
        return self.lower is not None

    def hasFiniteUpperBound(self):
        """
        Returns:
            `True` if, and only if, the represented interval has
            a finite upper bound.
        """
        return self.upper is not None
