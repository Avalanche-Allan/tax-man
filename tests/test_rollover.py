"""Tests for rolling a profile forward to the next tax year."""

from taxman.models import (
    FilingStatus,
    Form1099INT,
    Form1099R,
    FormW2,
    HealthInsurance,
    ScheduleCData,
    ScheduleEProperty,
    ScheduleK1,
    TaxpayerProfile,
)
from taxman.rollover import rollover_profile


def _completed_profile() -> TaxpayerProfile:
    return TaxpayerProfile(
        first_name="Test",
        last_name="User",
        ssn="123-45-6789",
        filing_status=FilingStatus.MFS,
        tax_year=2025,
        days_in_foreign_country_2025=334,
        prior_year_tax=9_999.99,  # 2024 tax — should be replaced
        businesses=[ScheduleCData(
            business_name="Consulting LLC",
            gross_receipts=100_000,
        )],
        schedule_e_properties=[ScheduleEProperty(
            property_address="2075 Jamaica St, Aurora, CO 80010",
            gross_rents=17_000,
            depreciation=5_090.91,
        )],
        health_insurance=HealthInsurance(total_premiums=5_000),
        forms_w2=[FormW2(employer_name="Acme", wages=50_000)],
        forms_1099_int=[Form1099INT(interest_income=600)],
        forms_1099_r=[Form1099R(gross_distribution=100)],
        schedule_k1s=[ScheduleK1(partnership_name="Old LP")],
        nol_carryforward=2_000,
        has_colorado_filing_obligation=True,
    )


class TestRolloverProfile:
    def test_year_and_prior_tax(self):
        new = rollover_profile(_completed_profile(), 13_778.12)
        assert new.tax_year == 2026
        assert new.prior_year_tax == 13_778.12

    def test_recurring_structures_kept(self):
        new = rollover_profile(_completed_profile(), 13_778.12)
        assert new.first_name == "Test"
        assert new.filing_status == FilingStatus.MFS
        assert len(new.businesses) == 1
        assert new.businesses[0].business_name == "Consulting LLC"
        assert len(new.schedule_e_properties) == 1
        # Depreciation schedule continues
        assert new.schedule_e_properties[0].depreciation == 5_090.91
        assert new.health_insurance.total_premiums == 5_000
        assert new.has_colorado_filing_obligation is True
        # NOL passes through (recomputed manually when applicable)
        assert new.nol_carryforward == 2_000

    def test_year_specific_documents_cleared(self):
        new = rollover_profile(_completed_profile(), 13_778.12)
        assert new.forms_w2 == []
        assert new.forms_1099_int == []
        assert new.forms_1099_r == []
        assert new.schedule_k1s == []
        assert new.estimated_payments == []

    def test_original_profile_untouched(self):
        original = _completed_profile()
        rollover_profile(original, 13_778.12)
        assert original.tax_year == 2025
        assert original.prior_year_tax == 9_999.99
        assert len(original.forms_w2) == 1
