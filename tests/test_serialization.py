"""Tests for session serialization/deserialization (Issue #2)."""

import json
import pytest
from pathlib import Path

from taxman.cli.serialization import (
    deserialize_profile,
    deserialize_result,
    serialize_profile,
    serialize_result,
)
from taxman.cli.state import SessionState
from taxman.calculator import calculate_return
from taxman.models import (
    AccountingMethod,
    BusinessExpenses,
    BusinessType,
    Dependent,
    EstimatedPayment,
    FilingStatus,
    Form1099B,
    Form1099DIV,
    Form1099INT,
    Form1099NEC,
    FormW2,
    HealthInsurance,
    HomeOffice,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)


# =============================================================================
# Profile Round-Trip Tests
# =============================================================================

class TestProfileSerialization:
    def test_empty_profile_round_trip(self):
        profile = TaxpayerProfile()
        data = serialize_profile(profile)
        restored = deserialize_profile(data)
        assert restored.filing_status == profile.filing_status
        assert restored.first_name == ""
        assert restored.businesses == []

    def test_mfs_expat_profile_round_trip(self):
        """MFS expat with businesses, K-1s, health insurance."""
        profile = TaxpayerProfile(
            first_name="John",
            last_name="Doe",
            ssn="123-45-6789",
            filing_status=FilingStatus.MFS,
            spouse_name="Jane Doe",
            spouse_ssn="987-65-4321",
            spouse_is_nra=True,
            foreign_address=True,
            country="Mexico",
            foreign_country="Mexico",
            days_in_foreign_country_2025=330,
            days_in_us_2025=35,
            businesses=[
                ScheduleCData(
                    business_name="Consulting LLC",
                    business_type=BusinessType.SINGLE_MEMBER_LLC,
                    accounting_method=AccountingMethod.CASH,
                    gross_receipts=120000.0,
                    cost_of_goods_sold=5000.0,
                    other_income=500.0,
                    expenses=BusinessExpenses(
                        office_expense=1200.0,
                        travel=3500.0,
                        meals=2000.0,
                        insurance=600.0,
                    ),
                    home_office=HomeOffice(
                        use_simplified_method=True,
                        square_footage=200,
                    ),
                ),
            ],
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Rental Partners LP",
                    partnership_ein="12-3456789",
                    net_rental_income=-5000.0,
                    ordinary_business_income=10000.0,
                    is_sstb=False,
                ),
            ],
            health_insurance=HealthInsurance(
                provider="Cigna",
                total_premiums=9600.0,
            ),
            estimated_payments=[
                EstimatedPayment(quarter=1, amount=5000.0),
                EstimatedPayment(quarter=2, amount=5000.0),
            ],
        )

        data = serialize_profile(profile)
        restored = deserialize_profile(data)

        assert restored.filing_status == FilingStatus.MFS
        assert restored.first_name == "John"
        assert restored.ssn == "123-45-6789"
        assert restored.spouse_name == "Jane Doe"
        assert restored.days_in_foreign_country_2025 == 330

        # Businesses
        assert len(restored.businesses) == 1
        biz = restored.businesses[0]
        assert biz.business_name == "Consulting LLC"
        assert biz.business_type == BusinessType.SINGLE_MEMBER_LLC
        assert biz.accounting_method == AccountingMethod.CASH
        assert biz.gross_receipts == 120000.0
        assert biz.cost_of_goods_sold == 5000.0
        assert biz.expenses.office_expense == 1200.0
        assert biz.expenses.meals == 2000.0
        assert biz.home_office is not None
        assert biz.home_office.use_simplified_method is True
        assert biz.home_office.square_footage == 200

        # K-1s
        assert len(restored.schedule_k1s) == 1
        k1 = restored.schedule_k1s[0]
        assert k1.partnership_name == "Rental Partners LP"
        assert k1.net_rental_income == -5000.0
        assert k1.ordinary_business_income == 10000.0

        # Health insurance
        assert restored.health_insurance is not None
        assert restored.health_insurance.total_premiums == 9600.0

        # Estimated payments
        assert len(restored.estimated_payments) == 2
        assert restored.estimated_payments[0].quarter == 1
        assert restored.estimated_payments[0].amount == 5000.0

    def test_profile_with_w2s_and_1099s(self):
        """Profile with W-2s, 1099-NEC, 1099-INT, 1099-DIV, 1099-B, dependents."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFJ,
            forms_w2=[
                FormW2(
                    employer_name="Acme Corp",
                    wages=52000.0,
                    federal_tax_withheld=8500.0,
                    ss_wages=52000.0,
                    medicare_wages=52000.0,
                ),
            ],
            forms_1099_nec=[
                Form1099NEC(
                    payer_name="Client A",
                    nonemployee_compensation=15000.0,
                ),
            ],
            forms_1099_int=[
                Form1099INT(payer_name="Big Bank", interest_income=500.0),
            ],
            forms_1099_div=[
                Form1099DIV(
                    payer_name="Vanguard",
                    ordinary_dividends=3000.0,
                    qualified_dividends=2500.0,
                ),
            ],
            forms_1099_b=[
                Form1099B(
                    broker_name="Schwab",
                    st_proceeds=10000.0,
                    st_cost_basis=9000.0,
                    lt_proceeds=20000.0,
                    lt_cost_basis=15000.0,
                ),
            ],
            dependents=[
                Dependent(
                    first_name="Junior",
                    last_name="Doe",
                    ssn="111-22-3333",
                    relationship="son",
                    is_qualifying_child_ctc=True,
                ),
            ],
        )

        data = serialize_profile(profile)
        restored = deserialize_profile(data)

        assert restored.filing_status == FilingStatus.MFJ
        assert len(restored.forms_w2) == 1
        assert restored.forms_w2[0].wages == 52000.0
        assert len(restored.forms_1099_nec) == 1
        assert restored.forms_1099_nec[0].nonemployee_compensation == 15000.0
        assert len(restored.forms_1099_int) == 1
        assert restored.forms_1099_int[0].interest_income == 500.0
        assert len(restored.forms_1099_div) == 1
        assert restored.forms_1099_div[0].qualified_dividends == 2500.0
        assert len(restored.forms_1099_b) == 1
        assert restored.forms_1099_b[0].net_lt_gain_loss == 5000.0
        assert len(restored.dependents) == 1
        assert restored.dependents[0].first_name == "Junior"
        assert restored.dependents[0].is_qualifying_child_ctc is True

    def test_deserialize_empty_dict(self):
        restored = deserialize_profile({})
        assert restored.filing_status == FilingStatus.MFS
        assert restored.businesses == []

    def test_deserialize_none_like(self):
        restored = deserialize_profile(None)
        assert isinstance(restored, TaxpayerProfile)


# =============================================================================
# Result Round-Trip Tests
# =============================================================================

class TestResultSerialization:
    def test_serialize_none_result(self):
        assert serialize_result(None) == {}

    def test_deserialize_empty_result(self):
        assert deserialize_result({}) is None
        assert deserialize_result(None) is None

    def test_result_round_trip(self):
        """Calculate a return, serialize, deserialize, verify fields match."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            businesses=[
                ScheduleCData(
                    business_name="Freelance",
                    gross_receipts=80000.0,
                    expenses=BusinessExpenses(
                        office_expense=500.0,
                        supplies=200.0,
                    ),
                ),
            ],
        )

        result = calculate_return(profile)
        data = serialize_result(result)
        restored = deserialize_result(data)

        # Key fields
        assert restored.total_income == result.total_income
        assert restored.agi == result.agi
        assert restored.taxable_income == result.taxable_income
        assert restored.tax == result.tax
        assert restored.se_tax == result.se_tax
        assert restored.total_tax == result.total_tax
        assert restored.amount_owed == result.amount_owed
        assert restored.overpayment == result.overpayment
        assert restored.deduction == result.deduction
        assert restored.qbi_deduction == result.qbi_deduction

        # Schedule C results
        assert len(restored.schedule_c_results) == 1
        assert restored.schedule_c_results[0].business_name == "Freelance"
        assert restored.schedule_c_results[0].gross_receipts == 80000.0
        assert restored.schedule_c_results[0].net_profit_loss == result.schedule_c_results[0].net_profit_loss

        # Schedule SE
        assert restored.schedule_se is not None
        assert restored.schedule_se.se_tax == result.schedule_se.se_tax

        # QBI
        if result.qbi:
            assert restored.qbi is not None
            assert restored.qbi.qbi_deduction == result.qbi.qbi_deduction


# =============================================================================
# Resume Parity Test
# =============================================================================

class TestResumeParity:
    def test_serialized_profile_produces_same_result(self):
        """The strongest correctness test: serialize → deserialize → calculate
        produces the same Form1040Result as the original profile."""
        profile = TaxpayerProfile(
            first_name="Test",
            last_name="User",
            filing_status=FilingStatus.MFS,
            businesses=[
                ScheduleCData(
                    business_name="Consulting",
                    gross_receipts=100000.0,
                    cost_of_goods_sold=2000.0,
                    other_income=500.0,
                    expenses=BusinessExpenses(
                        office_expense=1200.0,
                        travel=3500.0,
                        meals=2000.0,
                        insurance=600.0,
                        contract_labor=5000.0,
                    ),
                    home_office=HomeOffice(
                        use_simplified_method=True,
                        square_footage=250,
                    ),
                ),
            ],
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="RE Partners",
                    net_rental_income=-3000.0,
                ),
            ],
            health_insurance=HealthInsurance(
                provider="Blue Cross",
                total_premiums=7200.0,
            ),
            estimated_payments=[
                EstimatedPayment(quarter=1, amount=4000.0),
                EstimatedPayment(quarter=2, amount=4000.0),
                EstimatedPayment(quarter=3, amount=4000.0),
                EstimatedPayment(quarter=4, amount=4000.0),
            ],
        )

        # Calculate from original profile
        result_original = calculate_return(profile)

        # Round-trip the profile through serialization
        serialized = serialize_profile(profile)
        restored_profile = deserialize_profile(serialized)

        # Calculate from restored profile
        result_restored = calculate_return(restored_profile)

        # All key fields must match
        assert result_restored.total_income == result_original.total_income
        assert result_restored.agi == result_original.agi
        assert result_restored.taxable_income == result_original.taxable_income
        assert result_restored.tax == result_original.tax
        assert result_restored.se_tax == result_original.se_tax
        assert result_restored.additional_medicare == result_original.additional_medicare
        assert result_restored.total_tax == result_original.total_tax
        assert result_restored.total_payments == result_original.total_payments
        assert result_restored.overpayment == result_original.overpayment
        assert result_restored.amount_owed == result_original.amount_owed


# =============================================================================
# Schema Versioning Tests
# =============================================================================

class TestSchemaVersioning:
    def test_new_session_has_schema_version_1(self):
        session = SessionState.create()
        assert session.schema_version == 1

    def test_load_legacy_session_without_schema_version(self, tmp_path, monkeypatch):
        """Version 0 (legacy) sessions load gracefully with empty profile_data."""
        import taxman.cli.config as config_mod
        monkeypatch.setattr(config_mod, "SESSIONS_DIR", tmp_path)
        # Also monkeypatch state.py's reference
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        # Write a legacy session file (no schema_version, no profile_data)
        legacy_data = {
            "session_id": "legacy123",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "completed_steps": ["welcome", "filing_status"],
            "current_step": "document_scan",
            "filing_status": "mfs",
            "personal_info": {"first_name": "John"},
            "income_data": {"wages": 50000},
        }
        session_file = tmp_path / "legacy123.json"
        session_file.write_text(json.dumps(legacy_data))

        session = SessionState.load("legacy123")
        assert session is not None
        assert session.schema_version == 0
        assert session.profile_data == {}
        assert session.filing_status == "mfs"
        assert len(session.completed_steps) == 2

    def test_load_v1_session_with_profile_data(self, tmp_path, monkeypatch):
        """Version 1 sessions load profile_data normally."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        profile = TaxpayerProfile(
            first_name="Jane",
            filing_status=FilingStatus.SINGLE,
            businesses=[
                ScheduleCData(business_name="Freelance", gross_receipts=50000.0),
            ],
        )
        profile_data = serialize_profile(profile)

        session_data = {
            "schema_version": 1,
            "session_id": "v1session",
            "created_at": "2025-06-01T00:00:00",
            "updated_at": "2025-06-01T00:00:00",
            "completed_steps": ["welcome", "filing_status", "personal_info"],
            "current_step": "income_review",
            "filing_status": "single",
            "personal_info": {},
            "profile_data": profile_data,
            "results": {},
        }
        (tmp_path / "v1session.json").write_text(json.dumps(session_data))

        session = SessionState.load("v1session")
        assert session is not None
        assert session.schema_version == 1
        assert session.profile_data != {}

        # Deserialize and verify
        restored = deserialize_profile(session.profile_data)
        assert restored.first_name == "Jane"
        assert restored.filing_status == FilingStatus.SINGLE
        assert len(restored.businesses) == 1
        assert restored.businesses[0].business_name == "Freelance"

    def test_session_has_profile_data_field(self):
        session = SessionState.create()
        assert hasattr(session, "profile_data")
        assert session.profile_data == {}
