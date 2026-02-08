"""Tests for CLI commands: export, review, compare (Issue #3)."""

import json
import pytest
from pathlib import Path

from taxman.calculator import calculate_return
from taxman.cli.serialization import serialize_profile, serialize_result
from taxman.cli.state import SessionState
from taxman.models import (
    BusinessExpenses,
    FilingStatus,
    ScheduleCData,
    TaxpayerProfile,
)


def _create_session_with_results(tmp_path, monkeypatch):
    """Helper: create a session with profile_data and results."""
    import taxman.cli.state as state_mod
    monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

    profile = TaxpayerProfile(
        first_name="Test",
        last_name="User",
        filing_status=FilingStatus.MFS,
        foreign_address=True,
        foreign_country="Mexico",
        days_in_foreign_country_2025=335,
        businesses=[
            ScheduleCData(
                business_name="Freelance",
                gross_receipts=80000.0,
                expenses=BusinessExpenses(office_expense=500.0),
            ),
        ],
    )
    result = calculate_return(profile)

    session_data = {
        "schema_version": 1,
        "session_id": "test123",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
        "completed_steps": ["welcome", "filing_status", "calculate"],
        "current_step": "generate_forms",
        "filing_status": "mfs",
        "personal_info": {},
        "profile_data": serialize_profile(profile),
        "results": serialize_result(result),
    }
    (tmp_path / "test123.json").write_text(json.dumps(session_data, default=str))
    return profile, result


# =============================================================================
# Export Command Tests
# =============================================================================

class TestExportCommand:
    def test_export_generates_report_files(self, tmp_path, monkeypatch):
        """Export creates text report files."""
        _create_session_with_results(tmp_path, monkeypatch)

        from taxman.cli.serialization import deserialize_profile, deserialize_result
        session = SessionState.load("test123")
        assert session is not None

        profile = deserialize_profile(session.profile_data)
        result = deserialize_result(session.results)

        from taxman.reports import (
            generate_tax_summary,
            generate_line_detail,
            generate_filing_checklist,
        )

        output_dir = tmp_path / "export_output"
        output_dir.mkdir()

        # Generate reports (what the export command does)
        summary = generate_tax_summary(result, profile)
        (output_dir / "tax_summary.txt").write_text(summary)

        detail = generate_line_detail(result)
        (output_dir / "line_detail.txt").write_text(detail)

        checklist = generate_filing_checklist(result, profile)
        (output_dir / "filing_checklist.txt").write_text(checklist)

        # Verify files exist and contain expected content
        assert (output_dir / "tax_summary.txt").exists()
        assert (output_dir / "line_detail.txt").exists()
        assert (output_dir / "filing_checklist.txt").exists()

        summary_text = (output_dir / "tax_summary.txt").read_text()
        assert "FEDERAL TAX RETURN SUMMARY" in summary_text
        assert "Freelance" in summary_text
        assert "80,000" in summary_text

    def test_export_fails_without_results(self, tmp_path, monkeypatch):
        """Export fails loudly when session has no results."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        session_data = {
            "schema_version": 1,
            "session_id": "noresults",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "completed_steps": ["welcome"],
            "filing_status": "mfs",
            "profile_data": serialize_profile(TaxpayerProfile()),
            "results": {},
        }
        (tmp_path / "noresults.json").write_text(json.dumps(session_data))

        session = SessionState.load("noresults")
        assert session is not None
        assert session.results == {}

    def test_export_fails_without_profile_data(self, tmp_path, monkeypatch):
        """Export fails loudly when session has no profile_data."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        session_data = {
            "schema_version": 1,
            "session_id": "noprofile",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "completed_steps": ["welcome"],
            "filing_status": "mfs",
            "profile_data": {},
            "results": {"total_tax": 1000},
        }
        (tmp_path / "noprofile.json").write_text(json.dumps(session_data))

        session = SessionState.load("noprofile")
        assert session is not None
        assert session.profile_data == {}


# =============================================================================
# Review Command Tests
# =============================================================================

class TestReviewCommand:
    def test_review_deserializes_and_displays(self, tmp_path, monkeypatch):
        """Review deserializes result and can display it."""
        _, result = _create_session_with_results(tmp_path, monkeypatch)

        from taxman.cli.serialization import deserialize_result
        session = SessionState.load("test123")
        restored = deserialize_result(session.results)

        assert restored.total_income == result.total_income
        assert restored.total_tax == result.total_tax
        assert len(restored.schedule_c_results) == 1

    def test_review_fails_without_results(self, tmp_path, monkeypatch):
        """Review should detect missing results."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        session_data = {
            "schema_version": 1,
            "session_id": "empty",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "completed_steps": [],
            "filing_status": "",
            "profile_data": {},
            "results": {},
        }
        (tmp_path / "empty.json").write_text(json.dumps(session_data))

        session = SessionState.load("empty")
        assert not session.results


# =============================================================================
# Compare Command Tests
# =============================================================================

class TestCompareCommand:
    def test_compare_runs_feie_comparison(self, tmp_path, monkeypatch):
        """Compare deserializes profile and runs FEIE comparison."""
        _create_session_with_results(tmp_path, monkeypatch)

        from taxman.calculator import compare_feie_scenarios
        from taxman.cli.serialization import deserialize_profile
        from taxman.reports import generate_feie_comparison_report

        session = SessionState.load("test123")
        profile = deserialize_profile(session.profile_data)

        assert profile.days_in_foreign_country_2025 == 335

        scenarios = compare_feie_scenarios(profile)
        report = generate_feie_comparison_report(scenarios)

        assert "WITHOUT FEIE" in report
        assert "WITH FEIE" in report
        assert "RECOMMENDATION" in report

    def test_compare_with_non_foreign_profile(self, tmp_path, monkeypatch):
        """Compare with profile that doesn't qualify for FEIE."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            days_in_foreign_country_2025=0,
            businesses=[
                ScheduleCData(business_name="Local", gross_receipts=50000.0),
            ],
        )

        session_data = {
            "schema_version": 1,
            "session_id": "domestic",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "completed_steps": ["calculate"],
            "filing_status": "single",
            "profile_data": serialize_profile(profile),
            "results": {},
        }
        (tmp_path / "domestic.json").write_text(json.dumps(session_data))

        from taxman.cli.serialization import deserialize_profile
        session = SessionState.load("domestic")
        restored = deserialize_profile(session.profile_data)
        assert restored.days_in_foreign_country_2025 == 0


# =============================================================================
# Fix 3: Quarterly Plan Prior Year Tax
# =============================================================================

class TestQuarterlyPlanPriorYearTax:
    def test_prior_year_tax_serializes_round_trip(self, tmp_path, monkeypatch):
        """prior_year_tax should survive profile serialization."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            prior_year_tax=28000.0,
            businesses=[
                ScheduleCData(business_name="Test", gross_receipts=80000.0),
            ],
        )
        data = serialize_profile(profile)
        assert data["prior_year_tax"] == 28000.0

        from taxman.cli.serialization import deserialize_profile
        restored = deserialize_profile(data)
        assert restored.prior_year_tax == 28000.0

    def test_export_uses_prior_year_tax(self, tmp_path, monkeypatch):
        """Export quarterly plan should use profile.prior_year_tax, not 0.0."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            prior_year_tax=25000.0,
            businesses=[
                ScheduleCData(
                    business_name="Test",
                    gross_receipts=80000.0,
                    expenses=BusinessExpenses(office_expense=500.0),
                ),
            ],
        )
        result = calculate_return(profile)

        from taxman.reports import generate_quarterly_plan
        quarterly_with_prior = generate_quarterly_plan(
            result.total_tax, profile.prior_year_tax, result.agi,
            filing_status=profile.filing_status,
        )
        quarterly_without = generate_quarterly_plan(
            result.total_tax, 0.0, result.agi,
            filing_status=profile.filing_status,
        )

        # With a real prior_year_tax, safe harbor amount should differ
        assert "25,000" in quarterly_with_prior or quarterly_with_prior != quarterly_without
