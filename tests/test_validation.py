"""Tests for validation module."""

import pytest

from taxman.validation import (
    ValidationError,
    validate_ein,
    validate_months,
    validate_non_negative,
    validate_percentage,
    validate_positive,
    validate_quarter,
    validate_range,
    validate_tin,
)


class TestValidateTIN:
    def test_dashed_ssn(self):
        assert validate_tin("123-45-6789") == "123-45-6789"

    def test_digits_only(self):
        assert validate_tin("123456789") == "123-45-6789"

    def test_empty_ok(self):
        assert validate_tin("") == ""

    def test_whitespace_stripped(self):
        assert validate_tin("  123-45-6789  ") == "123-45-6789"

    def test_invalid_format(self):
        with pytest.raises(ValidationError):
            validate_tin("12-345-6789")

    def test_too_short(self):
        with pytest.raises(ValidationError):
            validate_tin("12345")

    def test_letters(self):
        with pytest.raises(ValidationError):
            validate_tin("abc-de-fghi")


class TestValidateEIN:
    def test_dashed_ein(self):
        assert validate_ein("12-3456789") == "12-3456789"

    def test_digits_only(self):
        assert validate_ein("123456789") == "12-3456789"

    def test_empty_ok(self):
        assert validate_ein("") == ""

    def test_invalid_format(self):
        with pytest.raises(ValidationError):
            validate_ein("123-45-6789")  # SSN format

    def test_too_short(self):
        with pytest.raises(ValidationError):
            validate_ein("12345")


class TestValidateNonNegative:
    def test_zero(self):
        assert validate_non_negative(0) == 0

    def test_positive(self):
        assert validate_non_negative(100.50) == 100.50

    def test_negative(self):
        with pytest.raises(ValidationError):
            validate_non_negative(-1)


class TestValidatePositive:
    def test_positive(self):
        assert validate_positive(1) == 1

    def test_zero_rejected(self):
        with pytest.raises(ValidationError):
            validate_positive(0)

    def test_negative_rejected(self):
        with pytest.raises(ValidationError):
            validate_positive(-5)


class TestValidateRange:
    def test_in_range(self):
        assert validate_range(50, 0, 100) == 50

    def test_at_min(self):
        assert validate_range(0, 0, 100) == 0

    def test_at_max(self):
        assert validate_range(100, 0, 100) == 100

    def test_below_min(self):
        with pytest.raises(ValidationError):
            validate_range(-1, 0, 100)

    def test_above_max(self):
        with pytest.raises(ValidationError):
            validate_range(101, 0, 100)


class TestValidatePercentage:
    def test_zero(self):
        assert validate_percentage(0) == 0

    def test_hundred(self):
        assert validate_percentage(100) == 100

    def test_decimal(self):
        assert validate_percentage(0.5) == 0.5

    def test_whole_number(self):
        assert validate_percentage(50) == 50

    def test_above_100(self):
        with pytest.raises(ValidationError):
            validate_percentage(150)

    def test_negative(self):
        with pytest.raises(ValidationError):
            validate_percentage(-10)


class TestValidateQuarter:
    def test_valid_quarters(self):
        for q in (1, 2, 3, 4):
            assert validate_quarter(q) == q

    def test_zero_ok(self):
        assert validate_quarter(0) == 0

    def test_invalid_5(self):
        with pytest.raises(ValidationError):
            validate_quarter(5)

    def test_negative(self):
        with pytest.raises(ValidationError):
            validate_quarter(-1)


class TestValidateMonths:
    def test_valid_months(self):
        for m in range(1, 13):
            assert validate_months(m) == m

    def test_zero(self):
        with pytest.raises(ValidationError):
            validate_months(0)

    def test_13(self):
        with pytest.raises(ValidationError):
            validate_months(13)
