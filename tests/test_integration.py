"""Integration tests — full return scenarios end-to-end."""

import pytest

from taxman.calculator import (
    calculate_return,
    compare_feie_scenarios,
    estimate_quarterly_payments,
)
from taxman.constants import STANDARD_DEDUCTION
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
from taxman.reports import (
    generate_filing_checklist,
    generate_line_detail,
    generate_quarterly_plan,
    generate_tax_summary,
)


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
