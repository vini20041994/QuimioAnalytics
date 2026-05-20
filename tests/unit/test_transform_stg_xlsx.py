from decimal import Decimal

import pytest

from scripts.transform.transform_stg_xlsx import (
    safe_int,
    safe_numeric,
    validate_required_columns,
)


@pytest.mark.unit
def test_safe_numeric_converts_valid_values():
    assert safe_numeric("12.5") == Decimal("12.5")
    assert safe_numeric(10) == 10


@pytest.mark.unit
def test_safe_numeric_returns_none_for_invalid_values():
    assert safe_numeric("abc") is None
    assert safe_numeric(None) is None


@pytest.mark.unit
def test_safe_int_converts_valid_values():
    assert safe_int("7") == 7
    assert safe_int(5.0) == 5


@pytest.mark.unit
def test_safe_int_returns_none_for_invalid_values():
    assert safe_int("x") is None
    assert safe_int(None) is None


@pytest.mark.unit
def test_validate_required_columns_raises_clear_error():
    df = __import__("pandas").DataFrame({"a": [1], "b": [2]})

    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes"):
        validate_required_columns(df, ["a", "c"])
