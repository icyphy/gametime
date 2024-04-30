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
    """

    def __init__(self, lower: int=None, upper: int=None):
        if lower is not None and upper is not None:
            lower, upper = sorted((lower, upper))
        self.lower: int = lower
        self.upper: int = upper

    def __str__(self):
        return ("%s%s, %s%s" %
                ("(" if self.lower is None else "[",
                 (self.lower or "-Infinity"),
                 (self.upper or "Infinity"),
                 ")" if self.upper is None else "]"))

    @property
    def lower_bound(self) -> int:
        """
        Returns
        -------
        Lower bound of the interval represented by this object, or `None` if the interval has no finite lower bound.
        """
        return self.lower

    @property
    def upper_bound(self) -> int:
        """
        Returns
        -------
        Upper bound of the interval represented by this object, or `None` if the interval has no finite upper bound.
        """
        return self.upper

    def has_finite_lower_bound(self) -> bool:
        """
        Returns
        -------
        `True` if, and only if, the represented interval has a finite lower bound.

        """
        return self.lower is not None

    def has_finite_upper_bound(self) -> bool:
        """
        Returns
        -------
        `True` if, and only if, the represented interval has a finite upper bound.

        """
        return self.upper is not None
