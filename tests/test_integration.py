"""Integration tests — full return scenarios, document parsing, and form infra."""

import importlib
import os
from pathlib import Path

import pytest

from taxman.calculator import (
    calculate_return,
    compare_feie_scenarios,
    estimate_quarterly_payments,
)
from taxman.constants import STANDARD_DEDUCTION
from taxman.fill_forms import FORMS_DIR, IRS_FORM_URLS
from taxman.models import (
    BusinessExpenses,
    EstimatedPayment,
    FilingStatus,
    HealthInsurance,
    HomeOffice,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)
from taxman.parse_documents import (
    ParseResult,
    _classify_document,
    _detect_form,
    _extract_line_items,
    find_amount,
)
from taxman.reports import (
    generate_filing_checklist,
    generate_line_detail,
    generate_quarterly_plan,
    generate_tax_summary,
)


# =============================================================================
# Full Return Scenarios
# =============================================================================

class TestMFSExpatReturn:
    """Full return for MFS expat — the primary user scenario."""

    def test_complete_return(self, mfs_expat):
        result = calculate_return(mfs_expat)

        # Income should include both businesses + K-1
        biz_income = sum(sc.net_profit_loss for sc in result.schedule_c_results)
        assert biz_income > 0

        # Standard deduction for MFS
        assert result.deduction == STANDARD_DEDUCTION["mfs"]

        # All tax components should be computed
        assert result.tax >= 0
        assert result.se_tax >= 0
        assert result.total_tax > 0

    def test_rental_loss_suspended(self, mfs_expat):
        result = calculate_return(mfs_expat)
        # MFS rental losses are suspended
        assert result.schedule_e.net_rental_income == 0

    def test_feie_scenarios(self, mfs_expat):
        scenarios = compare_feie_scenarios(mfs_expat)
        assert "without_feie" in scenarios
        assert "feie_evaluation" in scenarios
        assert "recommendation" in scenarios
        # With 340 days abroad, should qualify
        assert scenarios["feie_evaluation"]["qualifies"]

    def test_tax_summary_report(self, mfs_expat):
        result = calculate_return(mfs_expat)
        summary = generate_tax_summary(result, mfs_expat)
        assert "FEDERAL TAX RETURN SUMMARY" in summary
        assert "MFS" in summary
        assert "TOTAL TAX" in summary

    def test_line_detail_report(self, mfs_expat):
        result = calculate_return(mfs_expat)
        detail = generate_line_detail(result)
        assert "LINE-BY-LINE" in detail
        assert "Schedule C" in detail
        assert "Schedule SE" in detail

    def test_filing_checklist(self, mfs_expat):
        result = calculate_return(mfs_expat)
        checklist = generate_filing_checklist(result, mfs_expat)
        assert "FILING CHECKLIST" in checklist
        assert "Form 1040" in checklist
        assert "Schedule C" in checklist

    def test_quarterly_plan(self, mfs_expat):
        result = calculate_return(mfs_expat)
        plan = generate_quarterly_plan(
            result.total_tax, 30_000, result.agi,
            filing_status=mfs_expat.filing_status,
        )
        assert "QUARTERLY" in plan
        assert "Q1 due" in plan


class TestSingleFreelancerReturn:
    def test_complete_return(self, single_freelancer):
        result = calculate_return(single_freelancer)
        assert len(result.schedule_c_results) == 1
        assert result.deduction == STANDARD_DEDUCTION["single"]
        assert result.se_tax > 0
        assert result.schedule_e is None

    def test_no_k1_income(self, single_freelancer):
        result = calculate_return(single_freelancer)
        assert result.schedule_e is None

    def test_qbi_below_threshold(self, single_freelancer):
        result = calculate_return(single_freelancer)
        assert result.qbi is not None
        assert result.qbi.qbi_deduction > 0
        assert not result.qbi.is_limited


class TestMFJHighIncomeReturn:
    def test_complete_return(self, mfj_high_income):
        result = calculate_return(mfj_high_income)
        assert result.deduction == STANDARD_DEDUCTION["mfj"]
        assert result.schedule_e is not None

    def test_additional_medicare(self, mfj_high_income):
        result = calculate_return(mfj_high_income)
        # With ~$416K income, should trigger additional medicare
        assert result.additional_medicare > 0

    def test_niit_on_investment(self, mfj_high_income):
        result = calculate_return(mfj_high_income)
        # Rental + interest + cap gains should trigger NIIT
        assert result.niit >= 0


class TestMinimalReturn:
    def test_small_business(self, minimal_profile):
        result = calculate_return(minimal_profile)
        assert result.total_income == 5_000
        assert result.total_tax > 0

    def test_se_tax_on_small_income(self, minimal_profile):
        result = calculate_return(minimal_profile)
        assert result.se_tax > 0  # 5K > $400 threshold


class TestZeroIncomeReturn:
    def test_zero_everything(self, zero_income):
        result = calculate_return(zero_income)
        assert result.total_income == 0
        assert result.agi == 0
        assert result.taxable_income == 0
        assert result.tax == 0
        assert result.se_tax == 0
        assert result.total_tax == 0
        assert result.amount_owed == 0


class TestInternalConsistency:
    """Verify mathematical relationships in results."""

    def test_agi_equals_income_minus_adjustments(self, mfs_expat):
        result = calculate_return(mfs_expat)
        assert result.agi == round(result.total_income - result.adjustments, 2)

    def test_taxable_income_nonnegative(self, mfs_expat):
        result = calculate_return(mfs_expat)
        assert result.taxable_income >= 0

    def test_total_tax_components(self, mfs_expat):
        result = calculate_return(mfs_expat)
        expected = round(
            result.tax + result.se_tax
            + result.additional_medicare + result.niit, 2
        )
        assert result.total_tax == expected

    def test_refund_or_owed_not_both(self, mfs_expat):
        result = calculate_return(mfs_expat)
        assert not (result.overpayment > 0 and result.amount_owed > 0)

    def test_se_tax_matches_schedule_se(self, mfs_expat):
        result = calculate_return(mfs_expat)
        if result.schedule_se:
            assert result.se_tax == result.schedule_se.se_tax

    def test_qbi_deduction_matches(self, mfs_expat):
        result = calculate_return(mfs_expat)
        if result.qbi:
            assert result.qbi_deduction == result.qbi.qbi_deduction

    def test_taxable_income_formula(self, mfs_expat):
        result = calculate_return(mfs_expat)
        expected = max(result.agi - result.deduction - result.qbi_deduction, 0)
        assert result.taxable_income == round(expected, 2)

    def test_estimated_payments_match_profile(self, mfs_expat):
        result = calculate_return(mfs_expat)
        assert result.estimated_payments == mfs_expat.total_estimated_payments


# =============================================================================
# Document Parsing
# =============================================================================

class TestFindAmount:
    def test_basic_amount(self):
        text = "Box 1 Nonemployee compensation $125,000.00"
        assert find_amount(text, r'nonemployee\s+compensation') == 125_000.0

    def test_amount_without_dollar_sign(self):
        text = "Box 1 Nonemployee compensation 125000.00"
        assert find_amount(text, r'nonemployee\s+compensation') == 125_000.0

    def test_amount_with_commas(self):
        text = "Total: $1,234,567.89"
        assert find_amount(text, r'Total') == 1_234_567.89

    def test_no_match(self):
        text = "Nothing relevant here"
        assert find_amount(text, r'compensation') == 0.0

    def test_zero_amount(self):
        text = "Box 1 compensation $0.00"
        assert find_amount(text, r'compensation') == 0.0

    def test_negative_amount_parentheses(self):
        text = "Box 2 Net rental income ($3,500.00)"
        amount = find_amount(text, r'net\s+rental.*income')
        assert amount == -3_500.0

    def test_integer_amount(self):
        text = "Box 12 Section 179 $5000"
        assert find_amount(text, r'section\s*179') == 5_000.0


class TestDetectForm:
    def test_form_1040(self):
        assert _detect_form("Form 1040 U.S. Individual Income Tax") == "Form 1040"

    def test_schedule_c(self):
        assert _detect_form("Schedule C Profit or Loss From Business") == "Schedule C"

    def test_schedule_se(self):
        assert _detect_form("Schedule SE Self-Employment Tax") == "Schedule SE"

    def test_schedule_e(self):
        assert _detect_form("Schedule E Supplemental Income and Loss") == "Schedule E"

    def test_form_2555(self):
        assert _detect_form("Form 2555 Foreign Earned Income") == "Form 2555"

    def test_form_8995(self):
        assert _detect_form("Form 8995 Qualified Business Income") == "Form 8995"

    def test_no_match(self):
        assert _detect_form("Random text with no form") is None

    def test_w2(self):
        assert _detect_form("Form W-2 Wage and Tax Statement") == "W-2"


class TestExtractLineItems:
    def test_basic_line(self):
        text = "7  Wages, salaries, tips          75,000"
        items = _extract_line_items(text)
        assert items.get("line_7") == 75_000.0

    def test_lettered_line(self):
        text = "8a  Interest income               2,500"
        items = _extract_line_items(text)
        assert items.get("line_8a") == 2_500.0

    def test_multiple_lines(self):
        text = """
7  Wages                    75,000
8a Interest                  2,500
9  Total income             77,500
"""
        items = _extract_line_items(text)
        assert items.get("line_7") == 75_000.0
        assert items.get("line_8a") == 2_500.0
        assert items.get("line_9") == 77_500.0


class TestClassifyDocument:
    def test_1099_nec_by_content(self):
        assert _classify_document("1099-NEC Form", "document.pdf") == "1099-NEC"

    def test_1099_nec_by_filename(self):
        assert _classify_document("some text", "1099nec.pdf") == "1099-NEC"

    def test_k1_by_content(self):
        assert _classify_document("Schedule K-1 Form 1065", "doc.pdf") == "K-1"

    def test_k1_by_filename(self):
        assert _classify_document("some text", "k1-2025.pdf") == "K-1"

    def test_w2_by_content(self):
        assert _classify_document("W-2 Wage and Tax Statement", "doc.pdf") == "W-2"

    def test_1098_by_content(self):
        assert _classify_document("Form 1098 Mortgage Interest", "doc.pdf") == "1098"

    def test_1095a_by_content(self):
        assert _classify_document("1095-A Health Insurance Marketplace", "doc.pdf") == "1095-A"

    def test_prior_return(self):
        assert _classify_document("Form 1040 Individual Income Tax", "doc.pdf") == "Prior Return"

    def test_estimated_payment(self):
        assert _classify_document("Form 1040-ES estimated tax payment", "doc.pdf") == "1040-ES"

    def test_charity(self):
        assert _classify_document("charitable contribution receipt", "doc.pdf") == "Charity Receipt"

    def test_unknown(self):
        assert _classify_document("random text", "random.pdf") == "unknown"


class TestParseResult:
    def test_default_values(self):
        r = ParseResult()
        assert r.data is None
        assert r.confidence == 0.0
        assert r.warnings == []
        assert not r.needs_manual_review

    def test_add_warning(self):
        r = ParseResult()
        r.add_warning("Missing field")
        assert len(r.warnings) == 1
        assert r.needs_manual_review

    def test_multiple_warnings(self):
        r = ParseResult()
        r.add_warning("Warning 1")
        r.add_warning("Warning 2")
        assert len(r.warnings) == 2


# =============================================================================
# Form Filling Infrastructure
# =============================================================================

class TestFormsDir:
    def test_forms_dir_not_hardcoded(self):
        """Bug 7 fix: FORMS_DIR should use package-relative path."""
        assert "/home/user/" not in str(FORMS_DIR)

    def test_forms_dir_env_override(self, monkeypatch, tmp_path):
        """TAXMAN_FORMS_DIR env var overrides default."""
        monkeypatch.setenv("TAXMAN_FORMS_DIR", str(tmp_path))
        # Re-import to pick up env var
        import taxman.fill_forms
        importlib.reload(taxman.fill_forms)
        assert taxman.fill_forms.FORMS_DIR == tmp_path
        # Restore
        monkeypatch.delenv("TAXMAN_FORMS_DIR", raising=False)
        importlib.reload(taxman.fill_forms)


class TestIRSFormURLs:
    def test_all_urls_are_irs(self):
        for key, url in IRS_FORM_URLS.items():
            assert url.startswith("https://www.irs.gov/"), f"{key} URL invalid"

    def test_required_forms_present(self):
        required = ["f1040", "f1040sc", "f1040se", "f1040sse", "f2555", "f8995"]
        for form in required:
            assert form in IRS_FORM_URLS, f"Missing {form}"

    def test_all_urls_are_pdf(self):
        for key, url in IRS_FORM_URLS.items():
            assert url.endswith(".pdf"), f"{key} URL doesn't end with .pdf"
