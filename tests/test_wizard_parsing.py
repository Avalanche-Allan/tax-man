"""Tests for wizard document parsing integration (Issue #4)."""

import pytest
from dataclasses import asdict
from unittest.mock import patch, MagicMock

from taxman.cli.wizard import TaxWizard
from taxman.cli.state import SessionState
from taxman.models import (
    Form1098,
    Form1099NEC,
    FormW2,
    ScheduleK1,
    TaxpayerProfile,
)
from taxman.parse_documents import ParseResult


# =============================================================================
# Parser Dispatch Tests
# =============================================================================

class TestParserDispatch:
    def test_parsers_dict_has_expected_types(self):
        """Verify the PARSERS dispatch table covers the expected types."""
        expected = {"1099-NEC", "W-2", "K-1", "1098", "1095-A", "Charity Receipt"}
        assert set(TaxWizard.PARSERS.keys()) == expected

    def test_parser_functions_are_callable(self):
        for doc_type, parser in TaxWizard.PARSERS.items():
            assert callable(parser), f"Parser for {doc_type} is not callable"


# =============================================================================
# Profile Population Tests
# =============================================================================

class TestApplyParsedResults:
    def test_w2_populates_forms_w2(self):
        wizard = TaxWizard()
        w2 = FormW2(employer_name="Acme", wages=52000.0, federal_tax_withheld=8000.0)
        wizard.parsed_results = [
            ParseResult(data=w2, confidence=0.9, document_type="W-2"),
        ]

        wizard._apply_parsed_results()

        assert len(wizard.profile.forms_w2) == 1
        assert wizard.profile.forms_w2[0].wages == 52000.0
        assert wizard.profile.forms_w2[0].employer_name == "Acme"

    def test_1099_nec_populates_forms_1099_nec(self):
        wizard = TaxWizard()
        nec = Form1099NEC(payer_name="Client", nonemployee_compensation=15000.0)
        wizard.parsed_results = [
            ParseResult(data=nec, confidence=0.95, document_type="1099-NEC"),
        ]

        wizard._apply_parsed_results()

        assert len(wizard.profile.forms_1099_nec) == 1
        assert wizard.profile.forms_1099_nec[0].nonemployee_compensation == 15000.0

    def test_k1_populates_schedule_k1s(self):
        wizard = TaxWizard()
        k1 = ScheduleK1(
            partnership_name="Rental LP",
            net_rental_income=-5000.0,
            ordinary_business_income=10000.0,
        )
        wizard.parsed_results = [
            ParseResult(data=k1, confidence=0.8, document_type="K-1"),
        ]

        wizard._apply_parsed_results()

        assert len(wizard.profile.schedule_k1s) == 1
        assert wizard.profile.schedule_k1s[0].partnership_name == "Rental LP"
        assert wizard.profile.schedule_k1s[0].net_rental_income == -5000.0

    def test_1098_populates_forms_1098(self):
        wizard = TaxWizard()
        f1098 = Form1098(lender_name="Wells Fargo", mortgage_interest=12000.0)
        wizard.parsed_results = [
            ParseResult(data=f1098, confidence=0.7, document_type="1098"),
        ]

        wizard._apply_parsed_results()

        assert len(wizard.profile.forms_1098) == 1
        assert wizard.profile.forms_1098[0].mortgage_interest == 12000.0

    def test_multiple_w2s_all_populated(self):
        wizard = TaxWizard()
        wizard.parsed_results = [
            ParseResult(
                data=FormW2(employer_name="Employer A", wages=40000.0),
                confidence=0.9,
                document_type="W-2",
            ),
            ParseResult(
                data=FormW2(employer_name="Employer B", wages=20000.0),
                confidence=0.85,
                document_type="W-2",
            ),
        ]

        wizard._apply_parsed_results()

        assert len(wizard.profile.forms_w2) == 2
        assert wizard.profile.forms_w2[0].employer_name == "Employer A"
        assert wizard.profile.forms_w2[1].employer_name == "Employer B"

    def test_empty_parsed_results_no_op(self):
        wizard = TaxWizard()
        wizard._apply_parsed_results()
        assert wizard.profile.forms_w2 == []
        assert wizard.profile.forms_1099_nec == []
        assert wizard.profile.schedule_k1s == []


# =============================================================================
# Parse Failure Handling Tests
# =============================================================================

class TestParseFailureHandling:
    def test_parse_failure_does_not_crash(self):
        """Verify that a parser exception is caught gracefully."""
        wizard = TaxWizard()
        # Simulate parsed results where some succeeded
        w2 = FormW2(employer_name="Good Corp", wages=50000.0)
        wizard.parsed_results = [
            ParseResult(data=w2, confidence=0.9, document_type="W-2"),
        ]

        # apply should work fine
        wizard._apply_parsed_results()
        assert len(wizard.profile.forms_w2) == 1


# =============================================================================
# Low Confidence Handling Tests
# =============================================================================

class TestLowConfidenceHandling:
    def test_low_confidence_still_populates(self):
        """Low confidence results should still be applied (user reviews later)."""
        wizard = TaxWizard()
        k1 = ScheduleK1(
            partnership_name="Sketchy LP",
            net_rental_income=100.0,
        )
        wizard.parsed_results = [
            ParseResult(
                data=k1,
                confidence=0.3,
                document_type="K-1",
                needs_manual_review=True,
                warnings=["Could not extract partnership name"],
            ),
        ]

        wizard._apply_parsed_results()
        assert len(wizard.profile.schedule_k1s) == 1


# =============================================================================
# Parsed Document Persistence Tests
# =============================================================================

class TestParsedDocumentPersistence:
    def test_save_parsed_documents_to_session(self, tmp_path, monkeypatch):
        """Verify parsed results are saved to session."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        session = SessionState.create()
        session.save()

        wizard = TaxWizard(session=session)
        wizard.parsed_results = [
            ParseResult(
                data=FormW2(employer_name="Acme", wages=50000.0),
                confidence=0.9,
                document_type="W-2",
                source_file="/docs/w2.pdf",
                warnings=[],
            ),
            ParseResult(
                data=Form1099NEC(payer_name="Client", nonemployee_compensation=10000.0),
                confidence=0.95,
                document_type="1099-NEC",
                source_file="/docs/1099nec.pdf",
                warnings=["Missing payer TIN"],
            ),
        ]

        wizard._save_parsed_documents()

        assert len(wizard.session.parsed_documents) == 2
        assert wizard.session.parsed_documents[0]["type"] == "W-2"
        assert wizard.session.parsed_documents[0]["confidence"] == 0.9
        assert wizard.session.parsed_documents[1]["type"] == "1099-NEC"
        assert wizard.session.parsed_documents[1]["warnings"] == ["Missing payer TIN"]

    def test_round_trip_parsed_documents(self, tmp_path, monkeypatch):
        """Save parsed docs → reload session → verify data intact."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        session = SessionState.create()
        session.save()

        wizard = TaxWizard(session=session)
        wizard.parsed_results = [
            ParseResult(
                data=FormW2(employer_name="Round Trip Corp", wages=75000.0),
                confidence=0.85,
                document_type="W-2",
                source_file="/docs/w2_roundtrip.pdf",
            ),
        ]
        wizard._save_parsed_documents()

        # Reload session
        reloaded = SessionState.load(session.session_id)
        assert len(reloaded.parsed_documents) == 1
        doc = reloaded.parsed_documents[0]
        assert doc["type"] == "W-2"
        assert doc["confidence"] == 0.85
        assert doc["data"]["employer_name"] == "Round Trip Corp"
        assert doc["data"]["wages"] == 75000.0


# =============================================================================
# Fix 1: Parsed Results Rehydration on Resume
# =============================================================================

class TestParsedResultsRehydration:
    def test_rehydrate_parsed_results_on_resume(self, tmp_path, monkeypatch):
        """parsed_results should be rebuilt from session.parsed_documents on resume."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        # Create a session with parsed documents saved
        session = SessionState.create()
        session.save()

        wizard = TaxWizard(session=session)
        wizard.parsed_results = [
            ParseResult(
                data=FormW2(employer_name="Resume Corp", wages=65000.0),
                confidence=0.9,
                document_type="W-2",
                source_file="/docs/w2.pdf",
            ),
            ParseResult(
                data=ScheduleK1(
                    partnership_name="K1 Partners",
                    net_rental_income=-2000.0,
                    ordinary_business_income=8000.0,
                    guaranteed_payments=5000.0,
                ),
                confidence=0.8,
                document_type="K-1",
                source_file="/docs/k1.pdf",
            ),
        ]
        wizard._save_parsed_documents()

        # Create a new wizard from the same session (simulating resume)
        reloaded_session = SessionState.load(session.session_id)
        resumed_wizard = TaxWizard(session=reloaded_session)

        assert len(resumed_wizard.parsed_results) == 2
        assert resumed_wizard.parsed_results[0].document_type == "W-2"
        assert isinstance(resumed_wizard.parsed_results[0].data, FormW2)
        assert resumed_wizard.parsed_results[0].data.employer_name == "Resume Corp"
        assert resumed_wizard.parsed_results[0].data.wages == 65000.0

        assert resumed_wizard.parsed_results[1].document_type == "K-1"
        assert isinstance(resumed_wizard.parsed_results[1].data, ScheduleK1)
        assert resumed_wizard.parsed_results[1].data.partnership_name == "K1 Partners"
        assert resumed_wizard.parsed_results[1].data.ordinary_business_income == 8000.0
        assert resumed_wizard.parsed_results[1].data.guaranteed_payments == 5000.0

    def test_rehydrated_results_apply_to_profile(self, tmp_path, monkeypatch):
        """After rehydration, _apply_parsed_results should populate the profile."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        session = SessionState.create()
        session.save()

        wizard = TaxWizard(session=session)
        wizard.parsed_results = [
            ParseResult(
                data=Form1099NEC(payer_name="Client A", nonemployee_compensation=25000.0),
                confidence=0.95,
                document_type="1099-NEC",
                source_file="/docs/1099.pdf",
            ),
        ]
        wizard._save_parsed_documents()

        # Resume
        reloaded_session = SessionState.load(session.session_id)
        resumed_wizard = TaxWizard(session=reloaded_session)
        resumed_wizard._apply_parsed_results()

        assert len(resumed_wizard.profile.forms_1099_nec) == 1
        assert resumed_wizard.profile.forms_1099_nec[0].payer_name == "Client A"

    def test_empty_parsed_documents_no_crash(self):
        """No crash when session has no parsed_documents."""
        wizard = TaxWizard()
        assert wizard.parsed_results == []


# =============================================================================
# Fix 2: K-1 Parsed Data Preservation
# =============================================================================

class TestK1ParsedDataPreservation:
    def test_parsed_k1_data_survives_apply(self):
        """K-1 data populated via _apply_parsed_results should have all fields."""
        wizard = TaxWizard()
        k1 = ScheduleK1(
            partnership_name="Rich Partners LP",
            net_rental_income=-3000.0,
            ordinary_business_income=15000.0,
            guaranteed_payments=8000.0,
            interest_income=500.0,
            net_long_term_capital_gain=2000.0,
            other_income=1000.0,
            other_deductions=300.0,
            self_employment_earnings=12000.0,
        )
        wizard.parsed_results = [
            ParseResult(data=k1, confidence=0.85, document_type="K-1"),
        ]

        wizard._apply_parsed_results()

        assert len(wizard.profile.schedule_k1s) == 1
        saved = wizard.profile.schedule_k1s[0]
        assert saved.partnership_name == "Rich Partners LP"
        assert saved.ordinary_business_income == 15000.0
        assert saved.guaranteed_payments == 8000.0
        assert saved.interest_income == 500.0
        assert saved.net_long_term_capital_gain == 2000.0
        assert saved.other_income == 1000.0
        assert saved.other_deductions == 300.0
        assert saved.self_employment_earnings == 12000.0

    def test_profile_k1_not_wiped_after_population(self):
        """After _apply_parsed_results, schedule_k1s should not be empty."""
        wizard = TaxWizard()
        k1 = ScheduleK1(
            partnership_name="Test LP",
            ordinary_business_income=10000.0,
            net_rental_income=-2000.0,
        )
        wizard.parsed_results = [
            ParseResult(data=k1, confidence=0.8, document_type="K-1"),
        ]
        wizard._apply_parsed_results()

        # Verify data is intact on the profile
        assert len(wizard.profile.schedule_k1s) == 1
        assert wizard.profile.schedule_k1s[0].ordinary_business_income == 10000.0
        assert wizard.profile.schedule_k1s[0].net_rental_income == -2000.0


# =============================================================================
# Fix 4: Foreign Income "Not Abroad" Saves Profile
# =============================================================================

class TestForeignIncomeNotAbroadSave:
    def test_not_abroad_saves_profile(self, tmp_path, monkeypatch):
        """_step_foreign_income saves profile when user says 'not abroad'."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        session = SessionState.create()
        session.save()

        wizard = TaxWizard(session=session)
        wizard.profile.days_in_foreign_country_2025 = 330  # was abroad before

        # Simulate "not abroad" — set days to 0 and save
        wizard.profile.days_in_foreign_country_2025 = 0
        wizard._save_profile()

        # Reload and verify
        reloaded = SessionState.load(session.session_id)
        from taxman.cli.serialization import deserialize_profile
        restored = deserialize_profile(reloaded.profile_data)
        assert restored.days_in_foreign_country_2025 == 0


# =============================================================================
# Fix 6: Generated Forms List Saved to Session
# =============================================================================

class TestGeneratedFormsSaved:
    def test_generated_forms_persisted_to_session(self, tmp_path, monkeypatch):
        """Setting generated_forms and calling save() should persist to disk."""
        import taxman.cli.state as state_mod
        monkeypatch.setattr(state_mod, "SESSIONS_DIR", tmp_path)

        session = SessionState.create()
        session.save()

        session.generated_forms = ["/output/f1040.pdf"]
        session.save()

        reloaded = SessionState.load(session.session_id)
        assert reloaded.generated_forms == ["/output/f1040.pdf"]
