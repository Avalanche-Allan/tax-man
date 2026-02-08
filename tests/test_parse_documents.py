"""Tests for document parsing."""

import pytest

from taxman.parse_documents import (
    ParseResult,
    _classify_document,
    _detect_form,
    _extract_line_items,
    find_amount,
)


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
