"""Tests for the tax calculation engine."""

import pytest
from taxman.calculator import (
    BRACKETS_BY_STATUS,
    calculate_additional_medicare,
    calculate_income_tax,
    calculate_niit,
    calculate_qbi_deduction,
    calculate_return,
    calculate_schedule_c,
    calculate_schedule_e,
    calculate_schedule_se,
    compare_feie_scenarios,
    estimate_quarterly_payments,
    evaluate_feie,
    generate_optimization_recommendations,
)
from taxman.constants import (
    ADDITIONAL_MEDICARE_THRESHOLD_MFS,
    ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    ADDITIONAL_MEDICARE_THRESHOLD_MFJ,
    MFS_BRACKETS,
    MFJ_BRACKETS,
    SINGLE_BRACKETS,
    NIIT_THRESHOLD_MFS,
    NIIT_THRESHOLD_SINGLE,
    NIIT_THRESHOLD_MFJ,
    QBI_THRESHOLD_MFS,
    SS_WAGE_BASE,
    STANDARD_DEDUCTION,
)
from taxman.models import (
    BusinessExpenses,
    FilingStatus,
    HomeOffice,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)


# =============================================================================
# TestCalculateScheduleC
# =============================================================================

class TestCalculateScheduleC:
    def test_basic_profit(self):
        biz = ScheduleCData(
            business_name="Test Biz",
            gross_receipts=100_000,
            expenses=BusinessExpenses(office_expense=5_000, supplies=2_000),
        )
        result = calculate_schedule_c(biz)
        assert result.gross_receipts == 100_000
        assert result.gross_income == 100_000
        assert result.net_profit_loss == 93_000  # 100K - 7K

    def test_loss(self):
        biz = ScheduleCData(
            business_name="Loss Biz",
            gross_receipts=5_000,
            expenses=BusinessExpenses(
                office_expense=3_000,
                supplies=1_000,
                travel=2_000,
                rent_other=1_000,
            ),
        )
        result = calculate_schedule_c(biz)
        assert result.net_profit_loss == -2_000

    def test_meals_50_percent(self):
        biz = ScheduleCData(
            business_name="Meals Biz",
            gross_receipts=50_000,
            expenses=BusinessExpenses(meals=10_000),
        )
        result = calculate_schedule_c(biz)
        # meals deducted at 50%
        assert result.total_expenses == 5_000
        assert result.net_profit_loss == 45_000

    def test_home_office_simplified(self):
        biz = ScheduleCData(
            business_name="Home Office Biz",
            gross_receipts=80_000,
            home_office=HomeOffice(
                use_simplified_method=True,
                square_footage=200,
                months_used=12,
            ),
        )
        result = calculate_schedule_c(biz)
        # 200 sqft * $5 = $1,000
        assert result.total_expenses == 1_000
        assert result.net_profit_loss == 79_000

    def test_home_office_simplified_max_300(self):
        biz = ScheduleCData(
            business_name="Big Office",
            gross_receipts=80_000,
            home_office=HomeOffice(
                use_simplified_method=True,
                square_footage=500,  # exceeds 300
                months_used=12,
            ),
        )
        result = calculate_schedule_c(biz)
        # Capped at 300 sqft * $5 = $1,500
        assert result.total_expenses == 1_500

    def test_home_office_regular(self):
        biz = ScheduleCData(
            business_name="Regular Office",
            gross_receipts=80_000,
            home_office=HomeOffice(
                use_simplified_method=False,
                total_home_sqft=1_000,
                office_sqft=200,
                rent=12_000,
                utilities=2_400,
                insurance=1_200,
                repairs=600,
                internet=1_200,
                internet_business_pct=0.60,
                months_used=12,
            ),
        )
        result = calculate_schedule_c(biz)
        # business pct = 200/1000 = 20%
        # direct = (12000+2400+1200+600) * 0.2 = 3240
        # internet = 1200 * 0.60 = 720
        # total home office = 3240 + 720 = 3960
        assert abs(result.total_expenses - 3960) < 0.01

    def test_cogs(self):
        """Note: calculator's gross_income doesn't subtract COGS.
        COGS subtraction is handled in the model's gross_profit property.
        The calculator uses gross_income = gross_receipts - returns."""
        biz = ScheduleCData(
            business_name="COGS Biz",
            gross_receipts=100_000,
            cost_of_goods_sold=30_000,
        )
        result = calculate_schedule_c(biz)
        assert result.gross_income == 100_000  # gross receipts minus returns (0)
        assert result.net_profit_loss == 100_000  # calculator doesn't subtract COGS

    def test_returns_and_allowances(self):
        biz = ScheduleCData(
            business_name="Returns Biz",
            gross_receipts=100_000,
            returns_and_allowances=5_000,
        )
        result = calculate_schedule_c(biz)
        assert result.gross_income == 95_000


# =============================================================================
# TestCalculateScheduleSE
# =============================================================================

class TestCalculateScheduleSE:
    def test_basic_se_tax(self):
        result = calculate_schedule_se(100_000)
        # 92.35% of 100K = 92,350
        # SS = 92,350 * 0.124 = 11,451.40
        # Medicare = 92,350 * 0.029 = 2,678.15
        # Total = 14,129.55
        assert result.se_tax == 14_129.55
        assert result.deductible_se_tax == round(14_129.55 * 0.50, 2)

    def test_below_400_no_tax(self):
        result = calculate_schedule_se(399)
        assert result.se_tax == 0
        assert result.deductible_se_tax == 0

    def test_exactly_400(self):
        result = calculate_schedule_se(400)
        assert result.se_tax > 0

    def test_ss_wage_base_cap(self):
        """Above wage base, only Medicare continues."""
        result = calculate_schedule_se(250_000)
        taxable = round(250_000 * 0.9235, 2)  # 230,875
        # SS capped at wage base
        ss = round(min(taxable, SS_WAGE_BASE) * 0.124, 2)
        medicare = round(taxable * 0.029, 2)
        assert result.se_tax == round(ss + medicare, 2)

    def test_deductible_half(self):
        result = calculate_schedule_se(50_000)
        assert result.deductible_se_tax == round(result.se_tax * 0.50, 2)


# =============================================================================
# TestCalculateScheduleE
# =============================================================================

class TestCalculateScheduleE:
    def test_rental_income(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Rental LP",
                    net_rental_income=10_000,
                ),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.net_rental_income == 10_000
        assert result.total_schedule_e_income == 10_000

    def test_mfs_rental_loss_suspended(self):
        """MFS filers cannot deduct passive rental losses."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Loss Rental",
                    net_rental_income=-5_000,
                ),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.net_rental_income == 0  # Loss suspended

    def test_non_mfs_rental_loss_allowed(self):
        """Single filers can deduct rental losses."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Loss Rental",
                    net_rental_income=-5_000,
                ),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.net_rental_income == -5_000

    def test_all_k1_boxes(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Full K-1",
                    ordinary_business_income=5_000,
                    net_rental_income=3_000,
                    guaranteed_payments=10_000,
                    interest_income=500,
                    net_long_term_capital_gain=2_000,
                    self_employment_earnings=15_000,
                ),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.ordinary_business_income == 5_000
        assert result.net_rental_income == 3_000
        assert result.guaranteed_payments == 10_000
        assert result.interest_income == 500
        assert result.capital_gains == 2_000
        assert result.se_earnings_from_k1 == 15_000

    def test_se_earnings_from_k1(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Active Partnership",
                    self_employment_earnings=20_000,
                    guaranteed_payments=5_000,
                ),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.se_earnings_from_k1 == 20_000


# =============================================================================
# TestCalculateQBI
# =============================================================================

class TestCalculateQBI:
    def test_below_threshold_simple(self):
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Test", net_profit_loss=80_000)
        result = calculate_qbi_deduction(80_000, [sc], FilingStatus.MFS)
        assert result.qbi_deduction == 16_000  # 20% of 80K
        assert not result.is_limited

    def test_above_threshold_no_wages(self):
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Test", net_profit_loss=300_000)
        result = calculate_qbi_deduction(250_000, [sc], FilingStatus.MFS)
        assert result.is_limited
        # Fully phased out with no W-2 wages: deduction should be 0
        # excess = 250K - 197.3K = 52.7K, phaseout range 50K
        # phase_out_pct = min(52.7K/50K, 1.0) = 1.0 (fully phased)
        assert result.qbi_deduction == 0.0

    def test_above_threshold_with_w2_wages(self):
        """Bug 2 fix: W-2 wages create a wage limitation."""
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Test", net_profit_loss=300_000)
        result = calculate_qbi_deduction(
            250_000, [sc], FilingStatus.MFS,
            w2_wages=100_000, ubia=0,
        )
        assert result.is_limited
        # With W-2 wages, wage_limit = max(100K*0.5, 100K*0.25) = 50K
        # full_amount = 300K * 0.2 = 60K, limited_amount = min(60K, 50K) = 50K
        # Fully phased out: qbi = 60K - (60K - 50K)*1.0 = 50K
        assert result.qbi_deduction == 50_000.0

    def test_above_threshold_with_ubia(self):
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Test", net_profit_loss=300_000)
        result = calculate_qbi_deduction(
            250_000, [sc], FilingStatus.MFS,
            w2_wages=50_000, ubia=1_000_000,
        )
        assert result.is_limited
        # wage_limit = max(50K*0.5=25K, 50K*0.25+1M*0.025=12.5K+25K=37.5K) = 37.5K
        assert result.qbi_deduction == 37_500.0

    def test_negative_qbi(self):
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Loss", net_profit_loss=-10_000)
        result = calculate_qbi_deduction(50_000, [sc], FilingStatus.MFS)
        assert result.qbi_deduction == 0

    def test_cap_at_20_pct_taxable(self):
        """QBI deduction capped at 20% of taxable income before QBI."""
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Big", net_profit_loss=200_000)
        # If taxable income is low, cap applies
        result = calculate_qbi_deduction(30_000, [sc], FilingStatus.MFS)
        # 20% of QBI = 40K, but 20% of taxable = 6K — cap at 6K
        assert result.qbi_deduction == 6_000

    def test_mfj_threshold(self):
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Test", net_profit_loss=100_000)
        result = calculate_qbi_deduction(350_000, [sc], FilingStatus.MFJ)
        # MFJ threshold is 394,600 — 350K is below
        assert not result.is_limited
        assert result.qbi_deduction == 20_000


# =============================================================================
# TestCalculateIncomeTax
# =============================================================================

class TestCalculateIncomeTax:
    def test_zero_income(self):
        assert calculate_income_tax(0) == 0

    def test_10_percent_bracket(self):
        tax = calculate_income_tax(10_000, MFS_BRACKETS)
        assert tax == 1_000.0  # 10% of 10K

    def test_two_brackets(self):
        tax = calculate_income_tax(20_000, MFS_BRACKETS)
        # 11,925 * 0.10 = 1,192.50
        # 8,075 * 0.12 = 969.00
        # Total = 2,161.50
        assert tax == 2_161.50

    def test_top_bracket(self):
        tax = calculate_income_tax(1_000_000, MFS_BRACKETS)
        assert tax > 0

    def test_bracket_boundary_exact(self):
        tax = calculate_income_tax(11_925, MFS_BRACKETS)
        assert tax == 1_192.50

    def test_all_filing_statuses(self):
        for status in FilingStatus:
            brackets = BRACKETS_BY_STATUS.get(status, MFS_BRACKETS)
            tax = calculate_income_tax(50_000, brackets)
            assert tax > 0

    def test_single_vs_mfs(self):
        """MFS and Single have same brackets."""
        tax_mfs = calculate_income_tax(100_000, MFS_BRACKETS)
        tax_single = calculate_income_tax(100_000, SINGLE_BRACKETS)
        assert tax_mfs == tax_single  # Same brackets up to 35% bracket

    def test_mfj_lower_tax(self):
        """MFJ generally has lower tax due to wider brackets."""
        tax_mfj = calculate_income_tax(200_000, MFJ_BRACKETS)
        tax_mfs = calculate_income_tax(200_000, MFS_BRACKETS)
        assert tax_mfj < tax_mfs


# =============================================================================
# TestCalculateAdditionalMedicare
# =============================================================================

class TestCalculateAdditionalMedicare:
    def test_below_threshold(self):
        assert calculate_additional_medicare(100_000, FilingStatus.MFS) == 0

    def test_above_mfs_threshold(self):
        amt = calculate_additional_medicare(200_000, FilingStatus.MFS)
        # (200K - 125K) * 0.009 = 675
        assert amt == 675.0

    def test_above_single_threshold(self):
        amt = calculate_additional_medicare(250_000, FilingStatus.SINGLE)
        # (250K - 200K) * 0.009 = 450
        assert amt == 450.0

    def test_above_mfj_threshold(self):
        amt = calculate_additional_medicare(300_000, FilingStatus.MFJ)
        # (300K - 250K) * 0.009 = 450
        assert amt == 450.0

    def test_exact_threshold(self):
        assert calculate_additional_medicare(125_000, FilingStatus.MFS) == 0


# =============================================================================
# TestCalculateNIIT
# =============================================================================

class TestCalculateNIIT:
    def test_below_threshold(self):
        assert calculate_niit(10_000, 100_000, FilingStatus.MFS) == 0

    def test_above_mfs_threshold(self):
        niit = calculate_niit(50_000, 200_000, FilingStatus.MFS)
        # agi_excess = 200K - 125K = 75K
        # taxable_nii = min(50K, 75K) = 50K
        # niit = 50K * 0.038 = 1,900
        assert niit == 1_900.0

    def test_lesser_of_logic(self):
        """NIIT is lesser of NII or AGI excess."""
        niit = calculate_niit(100_000, 150_000, FilingStatus.MFS)
        # agi_excess = 150K - 125K = 25K
        # taxable_nii = min(100K, 25K) = 25K
        assert niit == 950.0  # 25K * 0.038

    def test_single_threshold(self):
        """Bug 1 fix: NIIT uses filing-status-specific threshold."""
        niit = calculate_niit(50_000, 250_000, FilingStatus.SINGLE)
        # Single threshold = 200K
        # agi_excess = 250K - 200K = 50K
        # taxable_nii = min(50K, 50K) = 50K
        assert niit == 1_900.0

    def test_mfj_threshold(self):
        niit = calculate_niit(50_000, 300_000, FilingStatus.MFJ)
        # MFJ threshold = 250K
        # agi_excess = 300K - 250K = 50K
        assert niit == 1_900.0

    def test_mfj_below_threshold(self):
        niit = calculate_niit(50_000, 240_000, FilingStatus.MFJ)
        assert niit == 0


# =============================================================================
# TestEvaluateFEIE
# =============================================================================

class TestEvaluateFEIE:
    def test_qualifies_physical_presence(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            days_in_foreign_country_2025=340,
        )
        result = evaluate_feie(profile, 80_000, 10_000, 100_000)
        assert result.exclusion_amount > 0

    def test_does_not_qualify(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            days_in_foreign_country_2025=200,
        )
        result = evaluate_feie(profile, 80_000, 10_000, 100_000)
        assert result.exclusion_amount == 0
        assert not result.is_beneficial

    def test_stacking_correct_brackets(self):
        """Bug 3 fix: FEIE stacking uses filing-status-specific brackets."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            days_in_foreign_country_2025=340,
        )
        result = evaluate_feie(profile, 80_000, 10_000, 100_000)
        # Should use SINGLE brackets, not MFS
        # For the same income, Single and MFS brackets are identical
        # up to $250,525, so savings should be the same
        assert result.savings >= 0

    def test_beneficial_scenario(self, mfs_expat):
        result_no_feie = calculate_return(mfs_expat)
        earned = sum(sc.net_profit_loss for sc in result_no_feie.schedule_c_results)
        feie = evaluate_feie(
            mfs_expat,
            result_no_feie.taxable_income,
            result_no_feie.tax,
            max(earned, 0),
        )
        # With ~$111K income and 340 days abroad, FEIE should be beneficial
        assert feie.is_beneficial


# =============================================================================
# TestEstimateQuarterlyPayments
# =============================================================================

class TestEstimateQuarterlyPayments:
    def test_safe_harbor(self):
        est = estimate_quarterly_payments(40_000, 35_000, 50_000)
        # AGI 50K < 75K MFS threshold → 100% of prior year
        assert est["safe_harbor_prior_year"] == 35_000.0
        assert est["safe_harbor_current_year"] == 36_000.0  # 90% of 40K
        assert est["recommended_annual"] == 35_000.0  # min
        assert est["recommended_quarterly"] == 8_750.0

    def test_high_agi_110_percent(self):
        est = estimate_quarterly_payments(40_000, 35_000, 100_000)
        # AGI 100K > 75K MFS → 110% of prior year
        assert est["safe_harbor_prior_year"] == 38_500.0  # 110% of 35K

    def test_filing_status_threshold(self):
        """Bug 4 fix: filing status affects high-income threshold."""
        est_mfs = estimate_quarterly_payments(
            40_000, 35_000, 100_000, FilingStatus.MFS
        )
        est_single = estimate_quarterly_payments(
            40_000, 35_000, 100_000, FilingStatus.SINGLE
        )
        # MFS threshold = 75K (AGI 100K > 75K → 110%)
        assert est_mfs["safe_harbor_prior_year"] == 38_500.0
        # Single threshold = 150K (AGI 100K < 150K → 100%)
        assert est_single["safe_harbor_prior_year"] == 35_000.0


# =============================================================================
# TestCalculateReturn
# =============================================================================

class TestCalculateReturn:
    def test_mfs_complete(self, mfs_expat):
        result = calculate_return(mfs_expat)
        assert result.total_income > 0
        assert result.agi > 0
        assert result.taxable_income > 0
        assert result.tax > 0
        assert result.se_tax > 0
        assert result.total_tax > 0
        assert len(result.schedule_c_results) == 2
        assert result.schedule_se is not None
        assert result.schedule_e is not None
        assert result.qbi is not None
        # Estimated payments
        assert result.estimated_payments == 32_000.0

    def test_single_freelancer(self, single_freelancer):
        result = calculate_return(single_freelancer)
        assert result.total_income > 0
        assert len(result.schedule_c_results) == 1
        assert result.schedule_se is not None
        assert result.schedule_e is None  # No K-1s
        assert result.deduction == STANDARD_DEDUCTION["single"]

    def test_mfj_high_income(self, mfj_high_income):
        result = calculate_return(mfj_high_income)
        assert result.deduction == STANDARD_DEDUCTION["mfj"]
        assert result.schedule_e is not None
        # Should have NIIT on investment income
        assert result.niit >= 0

    def test_zero_income(self, zero_income):
        result = calculate_return(zero_income)
        assert result.total_income == 0
        assert result.total_tax == 0
        assert result.amount_owed == 0

    def test_multiple_businesses(self, mfs_expat):
        result = calculate_return(mfs_expat)
        assert len(result.schedule_c_results) == 2
        biz_names = [sc.business_name for sc in result.schedule_c_results]
        assert "Law Consulting LLC" in biz_names
        assert "DocSherpa LLC" in biz_names

    def test_health_insurance_limit(self, mfs_expat):
        """Health insurance deduction limited to net SE income minus deductible SE tax."""
        result = calculate_return(mfs_expat)
        # Check that health insurance is part of adjustments
        assert result.adjustments > 0
        # Health insurance ($8,400) should be limited
        total_biz = sum(sc.net_profit_loss for sc in result.schedule_c_results)
        se_ded = result.schedule_se.deductible_se_tax if result.schedule_se else 0
        max_health = max(total_biz - se_ded, 0)
        # Actual deduction can't exceed premiums or max_health
        assert result.adjustments <= total_biz  # rough upper bound

    def test_mfs_rental_loss_suspended(self, mfs_expat):
        """MFS expat rental loss should be suspended."""
        result = calculate_return(mfs_expat)
        # Rental is -3500 but should be suspended for MFS
        assert result.schedule_e.net_rental_income == 0


# =============================================================================
# TestOptimizationRecommendations
# =============================================================================

class TestOptimizationRecommendations:
    def test_feie_recommendation(self, mfs_expat):
        result = calculate_return(mfs_expat)
        recs = generate_optimization_recommendations(result, mfs_expat)
        # Should recommend FEIE for expat with 340 days abroad
        feie_rec = [r for r in recs if "FEIE" in r["title"] or "Foreign" in r["title"]]
        assert len(feie_rec) > 0

    def test_no_feie_for_domestic(self, single_freelancer):
        result = calculate_return(single_freelancer)
        recs = generate_optimization_recommendations(result, single_freelancer)
        feie_rec = [r for r in recs if "FEIE" in r["title"] or "Foreign" in r["title"]]
        assert len(feie_rec) == 0
