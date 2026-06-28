"""Tests for ETL transformers."""
import pytest
from datetime import datetime

from app.etl.transformers import (
    coerce_int, coerce_float, coerce_bool,
    parse_date, normalize_currency, strip_whitespace,
    map_values, default_if_none,
)


class TestCoerceInt:
    def test_coerce_valid_int(self):
        assert coerce_int("42") == 42
        assert coerce_int(42) == 42
        assert coerce_int(42.9) == 42

    def test_coerce_invalid_default(self):
        assert coerce_int("abc") == 0
        assert coerce_int(None) == 0
        assert coerce_int("abc", default=-1) == -1


class TestCoerceFloat:
    def test_coerce_valid_float(self):
        assert coerce_float("3.14") == pytest.approx(3.14)
        assert coerce_float(3.14) == pytest.approx(3.14)

    def test_coerce_invalid_default(self):
        assert coerce_float("abc") == 0.0
        assert coerce_float(None) == 0.0


class TestCoerceBool:
    def test_coerce_strings(self):
        assert coerce_bool("true") is True
        assert coerce_bool("True") is True
        assert coerce_bool("1") is True
        assert coerce_bool("yes") is True
        assert coerce_bool("false") is False
        assert coerce_bool("0") is False

    def test_coerce_native(self):
        assert coerce_bool(True) is True
        assert coerce_bool(False) is False


class TestParseDate:
    def test_parse_valid_date(self):
        result = parse_date("2024-06-15", "%Y-%m-%d")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 6
        assert result.day == 15

    def test_parse_invalid_returns_none(self):
        assert parse_date("not-a-date") is None
        assert parse_date(None) is None


class TestNormalizeCurrency:
    def test_normalize_with_symbol(self):
        assert normalize_currency("$1,234.56") == pytest.approx(1234.56)
        assert normalize_currency("€99.99") == pytest.approx(99.99)
        assert normalize_currency("£500") == pytest.approx(500.0)

    def test_normalize_numeric(self):
        assert normalize_currency(100) == pytest.approx(100.0)
        assert normalize_currency(42.5) == pytest.approx(42.5)


class TestStripWhitespace:
    def test_strip(self):
        assert strip_whitespace("  hello  ") == "hello"
        assert strip_whitespace(None) == ""
        assert strip_whitespace(123) == "123"


class TestMapValues:
    def test_map_values(self):
        mapping = {"a": "A", "b": "B"}
        assert map_values("a", mapping) == "A"
        assert map_values("c", mapping) == "c"  # unmapped returns original


class TestDefaultIfNone:
    def test_default(self):
        assert default_if_none(None, "default") == "default"
        assert default_if_none("value", "default") == "value"