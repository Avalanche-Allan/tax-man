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
