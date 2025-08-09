import pytest
from interval import Interval

def test_normalizes_when_lower_greater_than_upper():
    x = Interval(10, 2)
    assert x.lower == 2 and x.upper == 10
    assert x.has_finite_lower_bound() and x.has_finite_upper_bound()
    assert str(x) == "[2, 10]"


def test_both_finite_bounds_and_closed_form():
    x = Interval(1, 5)
    assert x.lower == 1 and x.upper == 5
    assert str(x) == "[1, 5]"


def test_equal_bounds_is_singleton_interval():
    x = Interval(3, 3)
    assert x.lower == 3 and x.upper == 3
    assert str(x) == "[3, 3]"


def test_infinite_lower_only():
    x = Interval(None, 7)
    assert x.lower is None and x.upper == 7
    assert not x.has_finite_lower_bound() and x.has_finite_upper_bound()
    assert str(x) == "(-Infinity, 7]"


def test_infinite_upper_only():
    x = Interval(1, None)
    assert x.lower == 1 and x.upper is None
    assert x.has_finite_lower_bound() and not x.has_finite_upper_bound()
    assert str(x) == "[1, Infinity)"


def test_both_infinite():
    x = Interval(None, None)
    assert x.lower is None and x.upper is None
    assert not x.has_finite_lower_bound() and not x.has_finite_upper_bound()
    assert str(x) == "(-Infinity, Infinity)"


def test_alias_properties_match_bounds():
    x = Interval(4, 9)
    assert x.lower_bound == x.lower == 4
    assert x.upper_bound == x.upper == 9

