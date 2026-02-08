"""Tests for headless wizard mode (Claude Code copilot integration)."""

import json

import pytest
from typer.testing import CliRunner

from taxman.calculator import calculate_return
from taxman.cli.app import app
from taxman.cli.headless import (
    PROCESSORS,
    STEP_ORDER,
    _get_step_spec,
    _load_profile,
    _next_step,
    _save_profile,
)
from taxman.cli.serialization import serialize_profile, serialize_result
from taxman.cli.state import SessionState
from taxman.models import (
    BusinessExpenses,
    FilingStatus,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)

runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def patch_sessions(tmp_path, monkeypatch):
    """Redirect SESSIONS_DIR to tmp_path for isolation."""
    import taxman.cli.state as state_mod
    import taxman.cli.config as config_mod
    monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "SESSIONS_DIR", tmp_path)
    monkeypatch.setattr(config_mod, "CONFIG_DIR", tmp_path)
    return tmp_path


def _create_session(tmp_path, completed_steps=None, profile=None, results=None):
    """Create a session file and return its ID."""
    session_data = {
        "schema_version": 1,
        "session_id": "headless01",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
        "completed_steps": completed_steps or [],
        "current_step": "",
        "filing_status": "",
        "personal_info": {},
        "documents_dir": "",
        "parsed_documents": [],
        "scan_results": {},
        "profile_data": serialize_profile(profile) if profile else {},
        "results": serialize_result(results) if results else {},
        "optimization": {},
        "generated_forms": [],
    }
    (tmp_path / "headless01.json").write_text(json.dumps(session_data, default=str))
    return "headless01"


def _make_profile_with_business():
    """Create a simple profile with one business."""
    return TaxpayerProfile(
        first_name="Test",
        last_name="User",
        filing_status=FilingStatus.MFS,
        businesses=[
            ScheduleCData(
                business_name="Freelance",
                gross_receipts=80000.0,
                expenses=BusinessExpenses(office_expense=500.0),
            ),
        ],
    )


# =============================================================================
# Step Spec Tests
# =============================================================================

class TestStepSpecs:
    def test_all_steps_have_specs(self):
        for step in STEP_ORDER:
            spec = _get_step_spec(step)
            assert spec is not None, f"Missing spec for step '{step}'"
            assert spec.name == step
            assert spec.title

    def test_all_steps_have_processors(self):
        for step in STEP_ORDER:
            assert step in PROCESSORS, f"Missing processor for step '{step}'"

    def test_next_step(self):
        assert _next_step("welcome") == "filing_status"
        assert _next_step("filing_checklist") is None
        assert _next_step("nonexistent") is None

    def test_step_order_matches_wizard(self):
        assert STEP_ORDER[0] == "welcome"
        assert STEP_ORDER[-1] == "filing_checklist"
        assert len(STEP_ORDER) == 13


# =============================================================================
# CLI: start command
# =============================================================================

class TestStartCommand:
    def test_start_new_session(self, patch_sessions):
        result = runner.invoke(app, ["headless", "start"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "session_id" in data
        assert data["next_step"] == "welcome"
        assert data["resumed"] is False
        assert data["next_spec"]["name"] == "welcome"

    def test_start_resume(self, patch_sessions):
        sid = _create_session(patch_sessions, completed_steps=["welcome", "filing_status"])
        result = runner.invoke(app, ["headless", "start", "--session-id", sid])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["session_id"] == sid
        assert data["resumed"] is True
        assert data["next_step"] == "document_scan"

    def test_start_resume_not_found(self, patch_sessions):
        result = runner.invoke(app, ["headless", "start", "--session-id", "nonexistent"])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert data["error"] is True
        assert data["error_type"] == "not_found"


# =============================================================================
# CLI: step command
# =============================================================================

class TestStepCommand:
    def test_step_get_spec(self, patch_sessions):
        sid = _create_session(patch_sessions)
        result = runner.invoke(app, ["headless", "step", sid, "filing_status"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["step"] == "filing_status"
        assert "spec" in data
        assert len(data["spec"]["fields"]) > 0

    def test_step_process_welcome(self, patch_sessions):
        sid = _create_session(patch_sessions)
        result = runner.invoke(app, ["headless", "step", sid, "welcome", "--answers", "{}"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["step"] == "welcome"
        assert data["next_step"] == "filing_status"

    def test_step_process_filing_status(self, patch_sessions):
        sid = _create_session(patch_sessions)
        answers = json.dumps({
            "filing_status": "mfs",
            "spouse_name": "Jane Doe",
            "spouse_is_nra": True,
        })
        result = runner.invoke(app, ["headless", "step", sid, "filing_status", "--answers", answers])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["result"]["filing_status"] == "mfs"
        assert data["next_step"] == "document_scan"

    def test_step_invalid_filing_status(self, patch_sessions):
        sid = _create_session(patch_sessions)
        answers = json.dumps({"filing_status": "invalid"})
        result = runner.invoke(app, ["headless", "step", sid, "filing_status", "--answers", answers])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert data["error"] is True
        assert "validation_error" in data["error_type"]

    def test_step_unknown_step(self, patch_sessions):
        sid = _create_session(patch_sessions)
        result = runner.invoke(app, ["headless", "step", sid, "nonexistent", "--answers", "{}"])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert data["error"] is True

    def test_step_invalid_json(self, patch_sessions):
        sid = _create_session(patch_sessions)
        result = runner.invoke(app, ["headless", "step", sid, "welcome", "--answers", "{bad json}"])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert data["error_type"] == "json_error"

    def test_step_session_not_found(self, patch_sessions):
        result = runner.invoke(app, ["headless", "step", "nonexistent", "welcome", "--answers", "{}"])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert data["error_type"] == "not_found"


# =============================================================================
# CLI: status command
# =============================================================================

class TestStatusCommand:
    def test_status_empty_session(self, patch_sessions):
        sid = _create_session(patch_sessions)
        result = runner.invoke(app, ["headless", "status", sid])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["session_id"] == sid
        assert data["total_steps"] == 13
        assert data["progress_pct"] == 0

    def test_status_with_profile(self, patch_sessions):
        profile = _make_profile_with_business()
        sid = _create_session(
            patch_sessions,
            completed_steps=["welcome", "filing_status"],
            profile=profile,
        )
        result = runner.invoke(app, ["headless", "status", sid])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["progress_pct"] > 0
        assert data["profile_summary"]["filing_status"] == "mfs"
        assert data["profile_summary"]["businesses"] == 1

    def test_status_with_results(self, patch_sessions):
        profile = _make_profile_with_business()
        calc_result = calculate_return(profile)
        sid = _create_session(
            patch_sessions,
            completed_steps=["welcome", "filing_status", "calculate"],
            profile=profile,
            results=calc_result,
        )
        result = runner.invoke(app, ["headless", "status", sid])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["results_summary"]["total_income"] > 0
        assert data["results_summary"]["total_tax"] > 0

    def test_status_not_found(self, patch_sessions):
        result = runner.invoke(app, ["headless", "status", "nonexistent"])
        assert result.exit_code == 1
        data = json.loads(result.stdout)
        assert data["error"] is True


# =============================================================================
# Processor Unit Tests
# =============================================================================

class TestProcessors:
    def test_process_personal_info(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = TaxpayerProfile()

        result = PROCESSORS["personal_info"](session, profile, {
            "first_name": "John",
            "last_name": "Doe",
            "ssn": "123-45-6789",
            "occupation": "Software Engineer",
            "street_address": "123 Main St",
            "city": "Denver",
            "state": "CO",
            "zip_code": "80202",
            "foreign_address": False,
        })

        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.ssn == "123-45-6789"
        assert profile.foreign_address is False

    def test_process_income_review_with_businesses(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = TaxpayerProfile()

        result = PROCESSORS["income_review"](session, profile, {
            "businesses": [
                {"business_name": "LLC1", "gross_receipts": 50000},
                {"business_name": "LLC2", "gross_receipts": 30000},
            ],
        })

        assert len(profile.businesses) == 2
        assert profile.businesses[0].business_name == "LLC1"
        assert profile.businesses[0].gross_receipts == 50000.0
        assert result["businesses"][1]["name"] == "LLC2"

    def test_process_income_review_with_k1s(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = TaxpayerProfile()

        result = PROCESSORS["income_review"](session, profile, {
            "businesses": [{"business_name": "Biz", "gross_receipts": 10000}],
            "additional_k1s": [
                {"partnership_name": "RE Fund", "net_rental_income": 5000},
            ],
        })

        assert len(profile.schedule_k1s) == 1
        assert profile.schedule_k1s[0].partnership_name == "RE Fund"

    def test_process_business_expenses(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = TaxpayerProfile(
            businesses=[
                ScheduleCData(business_name="Freelance", gross_receipts=80000.0),
            ],
        )

        result = PROCESSORS["business_expenses"](session, profile, {
            "expenses": {
                "Freelance": {"office_expense": 500, "travel": 2000, "meals": 1000},
            },
            "home_office": {
                "Freelance": {"method": "simplified", "square_footage": 200},
            },
        })

        biz = profile.businesses[0]
        assert biz.expenses.office_expense == 500.0
        assert biz.expenses.travel == 2000.0
        assert biz.home_office is not None
        assert biz.home_office.use_simplified_method is True
        assert biz.home_office.square_footage == 200.0
        assert result["businesses"][0]["net_profit"] > 0

    def test_process_deductions(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = TaxpayerProfile()

        result = PROCESSORS["deductions"](session, profile, {
            "has_health_insurance": True,
            "health_insurance_provider": "Blue Cross",
            "health_insurance_premiums": 6000,
            "estimated_payments": [
                {"quarter": 1, "amount": 5000},
                {"quarter": 2, "amount": 5000},
            ],
            "prior_year_tax": 15000,
        })

        assert profile.health_insurance is not None
        assert profile.health_insurance.total_premiums == 6000.0
        assert len(profile.estimated_payments) == 2
        assert profile.prior_year_tax == 15000.0

    def test_process_foreign_income(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = TaxpayerProfile()

        result = PROCESSORS["foreign_income"](session, profile, {
            "lived_abroad": True,
            "foreign_country": "Mexico",
            "days_abroad": 340,
            "days_us": 25,
        })

        assert profile.days_in_foreign_country_2025 == 340
        assert result["feie_eligible"] is True

    def test_process_foreign_income_not_abroad(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = TaxpayerProfile()

        result = PROCESSORS["foreign_income"](session, profile, {
            "lived_abroad": False,
        })

        assert profile.days_in_foreign_country_2025 == 0
        assert result["feie_eligible"] is False

    def test_process_calculate(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = _make_profile_with_business()

        result = PROCESSORS["calculate"](session, profile, {})

        assert result["total_income"] > 0
        assert result["total_tax"] > 0
        assert result["agi"] > 0
        assert session.results  # results persisted

    def test_process_optimization(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = _make_profile_with_business()
        profile.days_in_foreign_country_2025 = 340
        profile.foreign_address = True
        profile.foreign_country = "Mexico"

        # Must calculate first
        calc_result = calculate_return(profile)
        session.results = serialize_result(calc_result)
        session.save()

        result = PROCESSORS["optimization"](session, profile, {})

        assert "feie" in result
        assert "recommendations" in result

    def test_process_optimization_no_results(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = TaxpayerProfile()

        result = PROCESSORS["optimization"](session, profile, {})
        assert result["error"] is True

    def test_process_filing_checklist(self, patch_sessions):
        session = SessionState.create()
        session.save()
        profile = _make_profile_with_business()

        calc_result = calculate_return(profile)
        session.results = serialize_result(calc_result)
        session.save()

        result = PROCESSORS["filing_checklist"](session, profile, {})

        assert "checklist" in result
        assert "quarterly_payments" in result
        assert result["quarterly_payments"]["recommended_quarterly"] >= 0

    def test_process_generate_forms(self, patch_sessions, tmp_path):
        session = SessionState.create()
        session.save()
        profile = _make_profile_with_business()

        calc_result = calculate_return(profile)
        session.results = serialize_result(calc_result)
        session.save()

        output_dir = str(tmp_path / "output")
        result = PROCESSORS["generate_forms"](session, profile, {"output_dir": output_dir})

        assert len(result["generated_files"]) > 0
        assert result["output_dir"] == output_dir


# =============================================================================
# Full Flow Integration Test
# =============================================================================

class TestFullFlow:
    def test_headless_flow(self, patch_sessions):
        """Walk through a minimal headless flow via CLI."""
        # Start
        r = runner.invoke(app, ["headless", "start"])
        assert r.exit_code == 0
        start_data = json.loads(r.stdout)
        sid = start_data["session_id"]

        # Welcome
        r = runner.invoke(app, ["headless", "step", sid, "welcome", "--answers", "{}"])
        assert r.exit_code == 0

        # Filing status
        r = runner.invoke(app, ["headless", "step", sid, "filing_status",
                                "--answers", json.dumps({"filing_status": "mfs", "spouse_is_nra": True})])
        assert r.exit_code == 0

        # Skip document scan (no docs dir)
        r = runner.invoke(app, ["headless", "step", sid, "document_scan",
                                "--answers", "{}"])
        assert r.exit_code == 0

        # Skip document review (no docs)
        r = runner.invoke(app, ["headless", "step", sid, "document_review",
                                "--answers", "{}"])
        assert r.exit_code == 0

        # Personal info
        r = runner.invoke(app, ["headless", "step", sid, "personal_info",
                                "--answers", json.dumps({
                                    "first_name": "John", "last_name": "Doe",
                                    "ssn": "123-45-6789", "occupation": "Consultant",
                                    "foreign_address": False,
                                })])
        assert r.exit_code == 0

        # Income review
        r = runner.invoke(app, ["headless", "step", sid, "income_review",
                                "--answers", json.dumps({
                                    "businesses": [
                                        {"business_name": "Consulting", "gross_receipts": 80000},
                                    ],
                                })])
        assert r.exit_code == 0

        # Business expenses
        r = runner.invoke(app, ["headless", "step", sid, "business_expenses",
                                "--answers", json.dumps({
                                    "expenses": {"Consulting": {"office_expense": 500}},
                                })])
        assert r.exit_code == 0

        # Deductions
        r = runner.invoke(app, ["headless", "step", sid, "deductions",
                                "--answers", json.dumps({"prior_year_tax": 10000})])
        assert r.exit_code == 0

        # Foreign income
        r = runner.invoke(app, ["headless", "step", sid, "foreign_income",
                                "--answers", json.dumps({"lived_abroad": False})])
        assert r.exit_code == 0

        # Calculate
        r = runner.invoke(app, ["headless", "step", sid, "calculate", "--answers", "{}"])
        assert r.exit_code == 0
        calc_data = json.loads(r.stdout)
        assert calc_data["result"]["total_tax"] > 0

        # Optimization
        r = runner.invoke(app, ["headless", "step", sid, "optimization", "--answers", "{}"])
        assert r.exit_code == 0

        # Generate forms
        output_dir = str(patch_sessions / "output")
        r = runner.invoke(app, ["headless", "step", sid, "generate_forms",
                                "--answers", json.dumps({"output_dir": output_dir})])
        assert r.exit_code == 0

        # Filing checklist
        r = runner.invoke(app, ["headless", "step", sid, "filing_checklist", "--answers", "{}"])
        assert r.exit_code == 0
        checklist_data = json.loads(r.stdout)
        assert checklist_data["completed"] is True

        # Check final status
        r = runner.invoke(app, ["headless", "status", sid])
        assert r.exit_code == 0
        status_data = json.loads(r.stdout)
        assert status_data["progress_pct"] == 100
        assert len(status_data["completed_steps"]) == 13
        assert status_data["results_summary"]["total_tax"] > 0
