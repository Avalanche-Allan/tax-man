"""Input validation for tax data models.

Provides validators for TINs, EINs, amounts, percentages, and other
tax-specific data. Used in __post_init__ hooks on dataclasses.
"""

import re


class ValidationError(ValueError):
    """Raised when tax data fails validation."""
    pass


# --- TIN / EIN Validators ---

_SSN_PATTERN = re.compile(r'^\d{3}-\d{2}-\d{4}$')
_EIN_PATTERN = re.compile(r'^\d{2}-\d{7}$')
_SSN_DIGITS = re.compile(r'^\d{9}$')
_EIN_DIGITS = re.compile(r'^\d{9}$')


def validate_tin(value: str, field_name: str = "TIN") -> str:
    """Validate a Taxpayer Identification Number (SSN or ITIN).

    Accepts: 123-45-6789 or 123456789 (normalizes to dashed format).
    Empty string is allowed (not yet entered).
    """
    if not value:
        return value
    value = value.strip()
    if _SSN_PATTERN.match(value):
        return value
    if _SSN_DIGITS.match(value):
        return f"{value[:3]}-{value[3:5]}-{value[5:]}"
    raise ValidationError(
        f"{field_name} must be in format 123-45-6789 or 123456789, got: {value!r}"
    )


def validate_ein(value: str, field_name: str = "EIN") -> str:
    """Validate an Employer Identification Number.

    Accepts: 12-3456789 or 123456789 (normalizes to dashed format).
    Empty string is allowed.
    """
    if not value:
        return value
    value = value.strip()
    if _EIN_PATTERN.match(value):
        return value
    if _EIN_DIGITS.match(value):
        return f"{value[:2]}-{value[2:]}"
    raise ValidationError(
        f"{field_name} must be in format 12-3456789 or 123456789, got: {value!r}"
    )


# --- Amount Validators ---

def validate_non_negative(value: float, field_name: str = "amount") -> float:
    """Validate that a value is not negative."""
    if value < 0:
        raise ValidationError(f"{field_name} cannot be negative, got: {value}")
    return value


def validate_positive(value: float, field_name: str = "amount") -> float:
    """Validate that a value is positive (> 0)."""
    if value <= 0:
        raise ValidationError(f"{field_name} must be positive, got: {value}")
    return value


def validate_range(value: float, min_val: float, max_val: float,
                   field_name: str = "value") -> float:
    """Validate that a value falls within a range (inclusive)."""
    if not (min_val <= value <= max_val):
        raise ValidationError(
            f"{field_name} must be between {min_val} and {max_val}, got: {value}"
        )
    return value


def validate_percentage(value: float, field_name: str = "percentage") -> float:
    """Validate a percentage value (0.0 to 100.0).

    Values > 1 and <= 100 are treated as whole-number percentages.
    Values > 100 are invalid.
    """
    if value < 0 or value > 100:
        raise ValidationError(
            f"{field_name} must be between 0 and 100, got: {value}"
        )
    return value


def validate_quarter(value: int, field_name: str = "quarter") -> int:
    """Validate a tax quarter (1-4). Zero is allowed (not yet set)."""
    if value != 0 and value not in (1, 2, 3, 4):
        raise ValidationError(
            f"{field_name} must be 1-4 (or 0 if unset), got: {value}"
        )
    return value


def validate_months(value: int, field_name: str = "months") -> int:
    """Validate months (1-12)."""
    if not (1 <= value <= 12):
        raise ValidationError(
            f"{field_name} must be between 1 and 12, got: {value}"
        )
    return value
