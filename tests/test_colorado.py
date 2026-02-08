"""Tests for Colorado state tax calculation."""

import pytest

from taxman.calculator import calculate_return
from taxman.colorado import (
    ColoradoForm104Result,
    calculate_co_source_income,
    calculate_colorado_104,
    calculate_full_return,
)
from taxman.constants import CO_TAX_RATE
from taxman.models import (
    BusinessExpenses,
    FilingStatus,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)


@pytest.fixture
def co_profile():
    """Profile with CO rental property."""
    return TaxpayerProfile(
        filing_status=FilingStatus.MFS,
        foreign_address=True,
        has_colorado_filing_obligation=True,
        businesses=[
            ScheduleCData(
                business_name="Consulting",
                gross_receipts=100_000,
                expenses=BusinessExpenses(office_expense=5_000),
            ),
        ],
        schedule_k1s=[
            ScheduleK1(
                partnership_name="Denver Rentals",
                net_rental_income=8_000,
                interest_income=200,
            ),
        ],
    )


class TestCalculateCOSourceIncome:
    def test_rental_income(self, co_profile):
        co_source = calculate_co_source_income(co_profile)
        # 8000 rental + 200 interest = 8200
        assert co_source == 8_200.0

    def test_no_k1s(self):
        profile = TaxpayerProfile(filing_status=FilingStatus.SINGLE)
        assert calculate_co_source_income(profile) == 0.0

    def test_negative_rental(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            schedule_k1s=[
                ScheduleK1(net_rental_income=-3_000),
            ],
        )
        assert calculate_co_source_income(profile) == -3_000.0


class TestCalculateColorado104:
    def test_nonresident_apportionment(self, co_profile):
        federal = calculate_return(co_profile)
        co = calculate_colorado_104(federal, co_profile)

        assert co.is_nonresident
        assert co.federal_taxable_income == federal.taxable_income
        assert co.co_tax_before_apportion == round(
            co.co_taxable_income * CO_TAX_RATE, 2
        )
        # Apportioned tax should be less than full tax
        assert co.co_tax <= co.co_tax_before_apportion
        assert co.co_tax > 0

    def test_apportionment_percentage(self, co_profile):
        federal = calculate_return(co_profile)
        co = calculate_colorado_104(federal, co_profile)

        # CO source / total income
        co_source = calculate_co_source_income(co_profile)
        expected_pct = co_source / federal.total_income
        assert abs(co.apportionment_pct - expected_pct) < 0.001

    def test_override_co_source(self, co_profile):
        federal = calculate_return(co_profile)
        co = calculate_colorado_104(federal, co_profile, co_source_income=50_000)
        assert co.co_source_income == 50_000

    def test_resident_no_apportionment(self):
        """Resident gets full tax, no apportionment."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            foreign_address=False,
            state="CO",
            businesses=[
                ScheduleCData(
                    business_name="Local Biz",
                    gross_receipts=80_000,
                    expenses=BusinessExpenses(office_expense=5_000),
                ),
            ],
        )
        federal = calculate_return(profile)
        co = calculate_colorado_104(federal, profile)

        assert not co.is_nonresident
        assert co.apportionment_pct == 1.0
        assert co.co_tax == co.co_tax_before_apportion

    def test_flat_rate(self, co_profile):
        """CO tax rate is 4.4%."""
        federal = calculate_return(co_profile)
        co = calculate_colorado_104(federal, co_profile)
        expected_full = round(co.co_taxable_income * 0.044, 2)
        assert co.co_tax_before_apportion == expected_full

    def test_zero_income(self):
        profile = TaxpayerProfile(filing_status=FilingStatus.SINGLE)
        federal = calculate_return(profile)
        co = calculate_colorado_104(federal, profile)
        assert co.co_tax == 0

    def test_line_items_present(self, co_profile):
        federal = calculate_return(co_profile)
        co = calculate_colorado_104(federal, co_profile)
        assert len(co.lines) > 0
        forms = [li.form for li in co.lines]
        assert any("CO Form 104" in f for f in forms)


class TestCalculateFullReturn:
    def test_with_colorado(self, co_profile):
        federal, colorado = calculate_full_return(co_profile)
        assert federal is not None
        assert colorado is not None
        assert colorado.co_tax >= 0

    def test_without_colorado(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            has_colorado_filing_obligation=False,
            businesses=[
                ScheduleCData(business_name="Test", gross_receipts=50_000),
            ],
        )
        federal, colorado = calculate_full_return(profile)
        assert federal is not None
        assert colorado is None

    def test_mfs_suspended_rental_co(self):
        """MFS rental loss is suspended federally but CO still sees it."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            foreign_address=True,
            has_colorado_filing_obligation=True,
            businesses=[
                ScheduleCData(
                    business_name="Consulting",
                    gross_receipts=100_000,
                ),
            ],
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Denver Loss Rental",
                    net_rental_income=-5_000,
                ),
            ],
        )
        federal, colorado = calculate_full_return(profile)

        # Federal suspends the loss
        assert federal.schedule_e.net_rental_income == 0

        # CO source income reflects the actual loss
        co_source = calculate_co_source_income(profile)
        assert co_source == -5_000
