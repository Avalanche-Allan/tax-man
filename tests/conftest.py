"""Shared test fixtures."""

import pytest

from tests.fixtures.profiles import (
    make_mfs_expat_profile,
    make_single_freelancer_profile,
    make_mfj_high_income_profile,
    make_minimal_profile,
    make_zero_income_profile,
)


@pytest.fixture
def mfs_expat():
    """MFS expat profile with law firm + DocSherpa + K-1."""
    return make_mfs_expat_profile()


@pytest.fixture
def single_freelancer():
    """Single freelancer with one Schedule C."""
    return make_single_freelancer_profile()


@pytest.fixture
def mfj_high_income():
    """MFJ high-income couple with consulting + rental."""
    return make_mfj_high_income_profile()


@pytest.fixture
def minimal_profile():
    """Minimal profile — single, small business."""
    return make_minimal_profile()


@pytest.fixture
def zero_income():
    """Zero income profile."""
    return make_zero_income_profile()
