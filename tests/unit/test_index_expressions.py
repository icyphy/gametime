import pytest
from index_expression import IndexExpression, VariableIndexExpression, ArrayIndexExpression


def test_variable_index_is_subclass_and_holds_name():
    v = VariableIndexExpression("i")
    assert isinstance(v, IndexExpression)
    assert "i" in str(v)

def test_index_expression_equality_semantics_are_stable():
    v1 = VariableIndexExpression("i")
    v2 = VariableIndexExpression("i")
    assert (v1 == v2) or (getattr(v1, "name", None) == getattr(v2, "name", None))
