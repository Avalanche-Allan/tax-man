"""Tests for the tax calculation engine."""

import pytest
from taxman.calculator import (
    BRACKETS_BY_STATUS,
    calculate_additional_medicare,
    calculate_amt,
    calculate_income_tax,
    calculate_niit,
    calculate_qbi_deduction,
    calculate_return,
    calculate_schedule_c,
    calculate_schedule_d,
    calculate_schedule_e,
    calculate_schedule_se,
    calculate_tax_credits,
    calculate_tax_with_qdcg_worksheet,
    compare_feie_scenarios,
    estimate_quarterly_payments,
    evaluate_feie,
    Form2555Result,
    generate_optimization_recommendations,
)
from taxman.constants import (
    ADDITIONAL_MEDICARE_THRESHOLD_MFS,
    ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    ADDITIONAL_MEDICARE_THRESHOLD_MFJ,
    HOH_BRACKETS,
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
    Dependent,
    FilingStatus,
    Form1099B,
    Form1099DIV,
    Form1099INT,
    Form1099NEC,
    FormW2,
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

    def test_home_office_regular_with_mortgage(self):
        """Mortgage interest prorated by business percentage."""
        biz = ScheduleCData(
            business_name="Mortgage Office",
            gross_receipts=80_000,
            home_office=HomeOffice(
                use_simplified_method=False,
                total_home_sqft=2_000,
                office_sqft=400,  # 20%
                mortgage_interest=12_000,
                months_used=12,
            ),
        )
        result = calculate_schedule_c(biz)
        # 12,000 * 20% = 2,400
        assert abs(result.total_expenses - 2_400) < 0.01

    def test_home_office_regular_with_real_estate_taxes(self):
        """Real estate taxes prorated by business percentage."""
        biz = ScheduleCData(
            business_name="RE Tax Office",
            gross_receipts=80_000,
            home_office=HomeOffice(
                use_simplified_method=False,
                total_home_sqft=2_000,
                office_sqft=400,  # 20%
                real_estate_taxes=6_000,
                months_used=12,
            ),
        )
        result = calculate_schedule_c(biz)
        # 6,000 * 20% = 1,200
        assert abs(result.total_expenses - 1_200) < 0.01

    def test_home_office_regular_all_expenses(self):
        """Full regular method with all expense types including mortgage/RE taxes."""
        biz = ScheduleCData(
            business_name="Full Regular Office",
            gross_receipts=80_000,
            home_office=HomeOffice(
                use_simplified_method=False,
                total_home_sqft=1_000,
                office_sqft=200,  # 20%
                rent=12_000,
                utilities=2_400,
                insurance=1_200,
                repairs=600,
                internet=1_200,
                internet_business_pct=0.60,
                mortgage_interest=18_000,
                real_estate_taxes=6_000,
                months_used=12,
            ),
        )
        result = calculate_schedule_c(biz)
        # direct = (12000+2400+1200+600+18000+6000) * 0.2 = 40200*0.2 = 8040
        # internet = 1200 * 0.60 = 720
        # total = 8760
        assert abs(result.total_expenses - 8_760) < 0.01

    def test_cogs(self):
        """COGS is subtracted to get gross profit (Line 5), which feeds
        into gross income (Line 7 = gross profit + other income)."""
        biz = ScheduleCData(
            business_name="COGS Biz",
            gross_receipts=100_000,
            cost_of_goods_sold=30_000,
        )
        result = calculate_schedule_c(biz)
        assert result.cost_of_goods_sold == 30_000
        assert result.gross_profit == 70_000  # 100K - 30K COGS
        assert result.gross_income == 70_000  # gross profit + 0 other income
        assert result.net_profit_loss == 70_000  # gross income - 0 expenses

    def test_returns_and_allowances(self):
        biz = ScheduleCData(
            business_name="Returns Biz",
            gross_receipts=100_000,
            returns_and_allowances=5_000,
        )
        result = calculate_schedule_c(biz)
        assert result.gross_profit == 95_000  # 100K - 5K returns - 0 COGS
        assert result.gross_income == 95_000

    def test_other_income(self):
        """Other income (Line 6) is added to gross profit to get gross income."""
        biz = ScheduleCData(
            business_name="Other Income Biz",
            gross_receipts=80_000,
            other_income=5_000,
        )
        result = calculate_schedule_c(biz)
        assert result.gross_profit == 80_000
        assert result.other_income == 5_000
        assert result.gross_income == 85_000  # gross profit + other income
        assert result.net_profit_loss == 85_000

    def test_cogs_with_returns_and_other_income(self):
        """Full Schedule C income flow: receipts - returns - COGS + other."""
        biz = ScheduleCData(
            business_name="Full Flow Biz",
            gross_receipts=200_000,
            returns_and_allowances=10_000,
            cost_of_goods_sold=50_000,
            other_income=3_000,
            expenses=BusinessExpenses(supplies=5_000),
        )
        result = calculate_schedule_c(biz)
        assert result.gross_profit == 140_000  # 200K - 10K - 50K
        assert result.gross_income == 143_000  # 140K + 3K
        assert result.net_profit_loss == 138_000  # 143K - 5K expenses

    def test_employee_benefit_programs_deducted(self):
        """Line 14: Employee benefit programs must be included in expenses."""
        biz = ScheduleCData(
            business_name="Benefits Biz",
            gross_receipts=100_000,
            expenses=BusinessExpenses(employee_benefit_programs=5_000),
        )
        result = calculate_schedule_c(biz)
        assert result.total_expenses == 5_000
        assert result.net_profit_loss == 95_000

    def test_pension_profit_sharing_deducted(self):
        """Line 19: Pension and profit-sharing must be included in expenses."""
        biz = ScheduleCData(
            business_name="Pension Biz",
            gross_receipts=100_000,
            expenses=BusinessExpenses(pension_profit_sharing=8_000),
        )
        result = calculate_schedule_c(biz)
        assert result.total_expenses == 8_000
        assert result.net_profit_loss == 92_000


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

    def test_cap_reduced_by_net_capital_gain(self):
        """IRC §199A(a): QBI cap is 20% of (taxable income - net capital gain)."""
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Big QBI", net_profit_loss=200_000)
        # Taxable = 100K, cap gain = 60K → cap base = 40K → cap = 20% of 40K = 8K
        result = calculate_qbi_deduction(
            100_000, [sc], FilingStatus.SINGLE, net_capital_gain=60_000,
        )
        assert result.qbi_deduction == 8_000

    def test_cap_not_reduced_without_cap_gains(self):
        """Regression: no capital gains means cap is 20% of full taxable income."""
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Big", net_profit_loss=200_000)
        result = calculate_qbi_deduction(30_000, [sc], FilingStatus.MFS)
        # 20% of QBI = 40K, 20% of taxable = 6K (no cap gain reduction)
        assert result.qbi_deduction == 6_000

    def test_cap_includes_qualified_dividends(self):
        """Qualified dividends are part of net_capital_gain for QBI cap."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            businesses=[
                ScheduleCData(business_name="Big Biz", gross_receipts=200_000),
            ],
            forms_1099_div=[
                Form1099DIV(ordinary_dividends=50_000, qualified_dividends=40_000),
            ],
        )
        result = calculate_return(profile)
        # Qualified dividends should reduce the QBI cap
        # Without qualified divs, cap would be higher
        # This just checks it doesn't error and QBI is computed
        assert result.qbi is not None
        assert result.qbi.qbi_deduction >= 0


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

    def test_hoh_lower_than_single(self):
        """HOH has wider 10% and 12% brackets than Single."""
        tax_hoh = calculate_income_tax(50_000, HOH_BRACKETS)
        tax_single = calculate_income_tax(50_000, SINGLE_BRACKETS)
        assert tax_hoh < tax_single

    def test_hoh_10_pct_bracket(self):
        """HOH 10% bracket goes up to $17,000 (vs $11,925 for Single)."""
        tax = calculate_income_tax(17_000, HOH_BRACKETS)
        assert tax == 1_700.0  # 17K * 10%

    def test_hoh_bracket_lookup(self):
        """BRACKETS_BY_STATUS maps HOH to HOH_BRACKETS, not Single."""
        brackets = BRACKETS_BY_STATUS[FilingStatus.HOH]
        assert brackets is HOH_BRACKETS


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
# TestCalculateAMT
# =============================================================================

class TestCalculateAMT:
    def test_no_amt_standard_deduction_filer(self):
        """Standard deduction filer should not trigger AMT (no SALT addback)."""
        result = calculate_amt(100_000, 15_000, FilingStatus.SINGLE, salt_deduction=0)
        assert result.amt == 0

    def test_amt_with_salt_addback(self):
        """SALT addback can trigger AMT."""
        # Taxable = 200K, regular tax ~40K, SALT addback = 40K
        # AMTI = 240K, exemption = 88,100, amt_taxable = 151,900
        # TMT = 151,900 * 0.26 = 39,494
        # AMT = max(39,494 - regular_tax, 0)
        regular_tax = calculate_income_tax(200_000, SINGLE_BRACKETS)
        result = calculate_amt(200_000, regular_tax, FilingStatus.SINGLE, salt_deduction=40_000)
        # TMT should be around 39,494. Regular tax at 200K is ~39,110.50
        # So AMT should be small positive
        assert result.amti == 240_000
        assert result.exemption == 88_100
        assert result.amt >= 0

    def test_mfs_exemption(self):
        result = calculate_amt(100_000, 15_000, FilingStatus.MFS, salt_deduction=20_000)
        assert result.exemption <= 68_500  # MFS exemption

    def test_single_exemption(self):
        result = calculate_amt(50_000, 5_000, FilingStatus.SINGLE, salt_deduction=10_000)
        assert result.exemption == 88_100  # No phaseout at this level

    def test_mfj_exemption(self):
        result = calculate_amt(100_000, 10_000, FilingStatus.MFJ, salt_deduction=10_000)
        assert result.exemption == 137_000

    def test_exemption_phaseout(self):
        """Exemption phases out at 25 cents per dollar above threshold."""
        # Single: threshold = 626,350
        # AMTI = 700,000, excess = 73,650
        # reduction = 73,650 * 0.25 = 18,412.50
        # exemption = 88,100 - 18,412.50 = 69,687.50
        result = calculate_amt(680_000, 150_000, FilingStatus.SINGLE, salt_deduction=20_000)
        assert result.amti == 700_000
        expected_exemption = 88_100 - (700_000 - 626_350) * 0.25
        assert result.exemption == round(expected_exemption, 2)

    def test_26_pct_rate(self):
        """Below breakpoint, TMT = 26% of excess."""
        # AMTI = 200K, exemption = 88,100, excess = 111,900
        # TMT = 111,900 * 0.26 = 29,094
        result = calculate_amt(200_000, 0, FilingStatus.SINGLE, salt_deduction=0)
        assert result.tentative_minimum_tax == round(111_900 * 0.26, 2)

    def test_28_pct_rate(self):
        """Above breakpoint ($239,100 for non-MFS), 28% kicks in."""
        # AMTI = 400K, exemption = 88,100, excess = 311,900
        # TMT = 239,100 * 0.26 + (311,900 - 239,100) * 0.28
        # = 62,166 + 72,800 * 0.28 = 62,166 + 20,384 = 82,550
        result = calculate_amt(400_000, 0, FilingStatus.SINGLE, salt_deduction=0)
        expected = 239_100 * 0.26 + (311_900 - 239_100) * 0.28
        assert result.tentative_minimum_tax == round(expected, 2)

    def test_amt_zero_when_regular_exceeds_tmt(self):
        """AMT = 0 when regular tax exceeds TMT."""
        result = calculate_amt(50_000, 100_000, FilingStatus.SINGLE, salt_deduction=0)
        assert result.amt == 0

    def test_amt_flows_to_total_tax(self):
        """AMT should be included in total_tax via calculate_return."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            uses_itemized_deductions=True,
            state_local_tax_deduction=40_000,
            businesses=[
                ScheduleCData(business_name="Big Biz", gross_receipts=300_000),
            ],
        )
        result = calculate_return(profile)
        if result.amt > 0:
            assert result.total_tax > result.tax + result.se_tax


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
# TestW2Integration
# =============================================================================

class TestW2Integration:
    def test_wage_income_flows_to_total(self):
        """W-2 wages should appear in total income."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_w2=[
                FormW2(wages=75_000, federal_tax_withheld=10_000,
                       ss_wages=75_000, medicare_wages=75_000),
            ],
        )
        result = calculate_return(profile)
        assert result.wage_income == 75_000
        assert result.total_income == 75_000

    def test_withholding_flows_to_payments(self):
        """W-2 federal withholding should be included in total payments."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_w2=[
                FormW2(wages=75_000, federal_tax_withheld=10_000,
                       ss_wages=75_000, medicare_wages=75_000),
            ],
        )
        result = calculate_return(profile)
        assert result.withholding == 10_000
        assert result.total_payments == 10_000

    def test_w2_plus_schedule_c(self):
        """W-2 wages + Schedule C income both flow into total income."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_w2=[
                FormW2(wages=60_000, federal_tax_withheld=8_000,
                       ss_wages=60_000, medicare_wages=60_000),
            ],
            businesses=[
                ScheduleCData(
                    business_name="Side Gig",
                    gross_receipts=30_000,
                ),
            ],
        )
        result = calculate_return(profile)
        assert result.wage_income == 60_000
        assert result.total_income == 90_000  # 60K wages + 30K biz

    def test_ss_wage_base_coordination(self):
        """W-2 SS wages reduce remaining SS base for SE tax."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_w2=[
                FormW2(wages=150_000, federal_tax_withheld=20_000,
                       ss_wages=150_000, medicare_wages=150_000),
            ],
            businesses=[
                ScheduleCData(
                    business_name="Side Gig",
                    gross_receipts=50_000,
                ),
            ],
        )
        result = calculate_return(profile)
        # SS wage base = $176,100. W-2 used $150K, leaving $26,100 for SE.
        # SE taxable = 50K * 0.9235 = 46,175
        # SS portion: min(46_175, 26_100) * 12.4% = 26_100 * 0.124 = 3,236.40
        # Medicare: 46_175 * 2.9% = 1,339.08
        # Total SE = 4,575.48
        assert result.schedule_se is not None
        assert result.se_tax < 7_065  # Would be ~7,065 without coordination

    def test_multiple_w2s(self):
        """Multiple W-2s should be summed."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_w2=[
                FormW2(wages=40_000, federal_tax_withheld=5_000,
                       ss_wages=40_000, medicare_wages=40_000),
                FormW2(wages=35_000, federal_tax_withheld=4_500,
                       ss_wages=35_000, medicare_wages=35_000),
            ],
        )
        result = calculate_return(profile)
        assert result.wage_income == 75_000
        assert result.withholding == 9_500


# =============================================================================
# TestK1QBI
# =============================================================================

class TestK1QBI:
    def test_k1_qbi_included(self):
        """K-1 QBI from non-SSTB partnerships should be included in QBI deduction."""
        from taxman.calculator import ScheduleCResult
        sc = ScheduleCResult(business_name="Test", net_profit_loss=50_000)
        result = calculate_qbi_deduction(
            80_000, [sc], FilingStatus.SINGLE, k1_qbi=30_000,
        )
        # Total QBI = 50K + 30K = 80K, deduction = 20% of 80K = 16K
        assert result.total_qbi == 80_000
        assert result.qbi_deduction == 16_000

    def test_sstb_k1_excluded(self):
        """K-1 from SSTB partnerships should NOT contribute QBI."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            businesses=[
                ScheduleCData(
                    business_name="Main Biz",
                    gross_receipts=50_000,
                ),
            ],
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="SSTB Partnership",
                    ordinary_business_income=30_000,
                    qbi_amount=30_000,
                    is_sstb=True,
                ),
            ],
        )
        result = calculate_return(profile)
        # SSTB K-1 QBI should be excluded
        assert result.qbi.total_qbi == 50_000  # Only Schedule C

    def test_k1_qbi_in_full_return(self):
        """K-1 QBI flows through calculate_return correctly."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            businesses=[
                ScheduleCData(
                    business_name="Main Biz",
                    gross_receipts=50_000,
                ),
            ],
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Non-SSTB Partnership",
                    ordinary_business_income=30_000,
                    qbi_amount=30_000,
                    is_sstb=False,
                ),
            ],
        )
        result = calculate_return(profile)
        # Total QBI should include both Schedule C and K-1
        assert result.qbi.total_qbi == 80_000  # 50K + 30K


# =============================================================================
# TestInvestmentIncome
# =============================================================================

class TestInvestmentIncome:
    def test_interest_flows_to_line_2b(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_int=[
                Form1099INT(interest_income=2_000),
            ],
        )
        result = calculate_return(profile)
        assert result.taxable_interest == 2_000
        assert result.total_income == 2_000

    def test_tax_exempt_interest_line_2a(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_int=[
                Form1099INT(interest_income=1_000, tax_exempt_interest=500),
            ],
        )
        result = calculate_return(profile)
        assert result.tax_exempt_interest == 500
        # Tax-exempt doesn't go into total income
        assert result.taxable_interest == 1_000
        assert result.total_income == 1_000

    def test_dividends_flow_to_line_3b(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_div=[
                Form1099DIV(ordinary_dividends=5_000, qualified_dividends=3_000),
            ],
        )
        result = calculate_return(profile)
        assert result.ordinary_dividends == 5_000
        assert result.qualified_dividends == 3_000
        assert result.total_income == 5_000

    def test_capital_gain_flows_to_line_7(self):
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_b=[
                Form1099B(lt_proceeds=50_000, lt_cost_basis=30_000),
            ],
        )
        result = calculate_return(profile)
        assert result.capital_gain_loss == 20_000
        assert result.schedule_d is not None
        assert result.schedule_d.net_lt_gain_loss == 20_000
        assert result.total_income == 20_000

    def test_capital_loss_limited_single(self):
        """Single filer capital loss limited to $3,000."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_b=[
                Form1099B(st_proceeds=5_000, st_cost_basis=15_000),
            ],
        )
        result = calculate_return(profile)
        assert result.capital_gain_loss == -3_000
        assert result.schedule_d.net_capital_gain_loss == -10_000

    def test_capital_loss_limited_mfs(self):
        """MFS capital loss limited to $1,500."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            forms_1099_b=[
                Form1099B(st_proceeds=5_000, st_cost_basis=15_000),
            ],
        )
        result = calculate_return(profile)
        assert result.capital_gain_loss == -1_500

    def test_investment_income_feeds_niit(self):
        """Interest and dividends feed net investment income for NIIT."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            businesses=[
                ScheduleCData(business_name="Biz", gross_receipts=250_000),
            ],
            forms_1099_int=[Form1099INT(interest_income=20_000)],
            forms_1099_div=[Form1099DIV(ordinary_dividends=30_000)],
        )
        result = calculate_return(profile)
        # AGI well above NIIT threshold (200K), NII = 20K+30K = 50K
        assert result.niit > 0

    def test_no_double_count_k1_interest(self):
        """K-1 interest flows to Line 2b, not double-counted in Schedule 1."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Bond Fund LP",
                    interest_income=5_000,
                ),
            ],
        )
        result = calculate_return(profile)
        assert result.taxable_interest == 5_000
        assert result.total_income == 5_000

    def test_investment_withholding_flows_to_payments(self):
        """1099 withholding should be included in total payments."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_int=[Form1099INT(interest_income=10_000, federal_tax_withheld=1_000)],
            forms_1099_div=[Form1099DIV(ordinary_dividends=5_000, federal_tax_withheld=500)],
            forms_1099_b=[Form1099B(lt_proceeds=20_000, lt_cost_basis=10_000, federal_tax_withheld=200)],
        )
        result = calculate_return(profile)
        assert result.withholding == 1_700  # 1000+500+200

    def test_schedule_d_st_and_lt(self):
        """Schedule D aggregates short and long term gains."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_b=[
                Form1099B(
                    st_proceeds=10_000, st_cost_basis=8_000,
                    lt_proceeds=20_000, lt_cost_basis=15_000,
                ),
            ],
        )
        sch_d = calculate_schedule_d(profile, FilingStatus.SINGLE)
        assert sch_d.net_st_gain_loss == 2_000
        assert sch_d.net_lt_gain_loss == 5_000
        assert sch_d.net_capital_gain_loss == 7_000
        assert sch_d.capital_gain_for_1040 == 7_000

    def test_cap_gains_from_1099_div(self):
        """1099-DIV Box 2a capital gain distributions flow to Schedule D LT."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_div=[
                Form1099DIV(ordinary_dividends=3_000, capital_gain_distributions=2_000),
            ],
        )
        result = calculate_return(profile)
        assert result.schedule_d is not None
        assert result.schedule_d.net_lt_gain_loss == 2_000
        assert result.capital_gain_loss == 2_000


# =============================================================================
# TestK1OrphanedBoxes
# =============================================================================

class TestK1OrphanedBoxes:
    def test_box3_other_rental_income(self):
        """Box 3: Other net rental income flows to Schedule E."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(partnership_name="Rental LP", other_net_rental_income=8_000),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.net_rental_income == 8_000

    def test_box6_dividends_flow_to_line_3b(self):
        """Box 6a dividends flow to Form 1040 Line 3b."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(partnership_name="Div Fund", dividends=4_000, qualified_dividends=2_000),
            ],
        )
        result = calculate_return(profile)
        assert result.ordinary_dividends == 4_000
        assert result.qualified_dividends == 2_000

    def test_box7_royalties_in_schedule_e_and_niit(self):
        """Box 7 royalties flow to Schedule E and count as NII."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            businesses=[ScheduleCData(business_name="Biz", gross_receipts=250_000)],
            schedule_k1s=[
                ScheduleK1(partnership_name="Oil LP", royalties=10_000),
            ],
        )
        result = calculate_return(profile)
        assert result.schedule_e.royalties == 10_000
        # Royalties should contribute to NII and thus NIIT
        assert result.niit > 0

    def test_box8_st_capital_gain_flows_to_schedule_d(self):
        """Box 8 ST capital gain flows to Schedule D."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(partnership_name="Trading LP", net_short_term_capital_gain=5_000),
            ],
        )
        result = calculate_return(profile)
        assert result.schedule_d is not None
        assert result.schedule_d.net_st_gain_loss == 5_000
        assert result.capital_gain_loss == 5_000

    def test_box10_section_1231_gain_as_ltcg(self):
        """Box 10 §1231 gain treated as LTCG on Schedule D."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(partnership_name="Equipment LP", net_section_1231_gain=7_000),
            ],
        )
        result = calculate_return(profile)
        assert result.schedule_d is not None
        assert result.schedule_d.net_lt_gain_loss == 7_000

    def test_box11_other_income(self):
        """Box 11 other income flows to Schedule E total."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(partnership_name="Misc LP", other_income=3_000),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.other_income == 3_000
        assert result.total_schedule_e_income == 3_000

    def test_box12_section_179(self):
        """Box 12 §179 deduction reduces Schedule E income."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Equipment LP",
                    ordinary_business_income=20_000,
                    section_179_deduction=5_000,
                ),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.section_179_deduction == 5_000
        assert result.total_schedule_e_income == 15_000

    def test_box13_other_deductions(self):
        """Box 13 other deductions reduce Schedule E income."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Deduction LP",
                    ordinary_business_income=10_000,
                    other_deductions=2_000,
                ),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.other_deductions == 2_000
        assert result.total_schedule_e_income == 8_000

    def test_multiple_k1s_aggregate(self):
        """Multiple K-1s should aggregate all boxes correctly."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="LP One",
                    ordinary_business_income=10_000,
                    royalties=2_000,
                ),
                ScheduleK1(
                    partnership_name="LP Two",
                    ordinary_business_income=5_000,
                    other_income=1_000,
                    section_179_deduction=3_000,
                ),
            ],
        )
        result = calculate_schedule_e(profile)
        assert result.ordinary_business_income == 15_000
        assert result.royalties == 2_000
        assert result.other_income == 1_000
        assert result.section_179_deduction == 3_000
        # 15000 + 2000 + 1000 - 3000 = 15000
        assert result.total_schedule_e_income == 15_000

    def test_existing_boxes_unchanged(self, mfs_expat):
        """Existing K-1 handling (Boxes 1,2,4,5,9a,14) unchanged."""
        result = calculate_return(mfs_expat)
        assert result.schedule_e is not None
        assert result.schedule_e.net_rental_income == 0  # MFS loss suspended


# =============================================================================
# TestK1CapitalGainsRegression (P0 fix — no double subtraction)
# =============================================================================

class TestK1CapitalGainsRegression:
    """Regression: K-1 capital gains must not be subtracted from Schedule 1
    income twice. Before fix, a K-1 with $10K LTCG produced total_income = 0."""

    def test_k1_ltcg_only_not_zeroed(self):
        """Single K-1 with LTCG should have total_income == capital gain."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Cap LP",
                    net_long_term_capital_gain=10_000,
                ),
            ],
        )
        result = calculate_return(profile)
        assert result.total_income == 10_000
        assert result.capital_gain_loss == 10_000

    def test_k1_ltcg_plus_ordinary_income(self):
        """K-1 LTCG + ordinary income should both appear in total_income."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Mixed LP",
                    ordinary_business_income=50_000,
                    net_long_term_capital_gain=10_000,
                ),
            ],
        )
        result = calculate_return(profile)
        # Ordinary flows to Schedule 1, LTCG flows to Schedule D / Line 7
        assert result.total_income == 60_000

    def test_k1_stcg_not_double_subtracted(self):
        """K-1 STCG should also not be double-subtracted."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Trading LP",
                    net_short_term_capital_gain=15_000,
                ),
            ],
        )
        result = calculate_return(profile)
        assert result.total_income == 15_000

    def test_k1_section_1231_not_double_subtracted(self):
        """K-1 §1231 gain (treated as LTCG) should not be double-subtracted."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            schedule_k1s=[
                ScheduleK1(
                    partnership_name="Equipment LP",
                    net_section_1231_gain=20_000,
                ),
            ],
        )
        result = calculate_return(profile)
        assert result.total_income == 20_000


# =============================================================================
# TestTaxCredits
# =============================================================================

class TestTaxCredits:
    def _make_family_profile(self, filing_status=FilingStatus.MFJ, num_children=2,
                             gross_receipts=100_000, wages=0):
        deps = [
            Dependent(first_name=f"Child{i}", last_name="Test",
                      relationship="child", is_qualifying_child_ctc=True)
            for i in range(num_children)
        ]
        p = TaxpayerProfile(
            filing_status=filing_status,
            dependents=deps,
            businesses=[
                ScheduleCData(business_name="Family Biz", gross_receipts=gross_receipts),
            ],
        )
        if wages > 0:
            p.forms_w2 = [FormW2(wages=wages, ss_wages=wages, medicare_wages=wages)]
        return p

    def test_ctc_basic(self):
        """2 children × $2,500 = $5,000 CTC."""
        profile = self._make_family_profile()
        result = calculate_return(profile)
        assert result.tax_credits is not None
        assert result.tax_credits.gross_ctc == 5_000

    def test_ctc_phaseout_mfj(self):
        """CTC phases out above $400K for MFJ."""
        profile = self._make_family_profile(
            filing_status=FilingStatus.MFJ, gross_receipts=500_000,
        )
        result = calculate_return(profile)
        # AGI > 400K: phaseout should reduce credits
        assert result.tax_credits.phaseout_reduction > 0
        assert result.tax_credits.total_credit_after_phaseout < 5_000

    def test_ctc_phaseout_single(self):
        """CTC phases out above $200K for Single."""
        profile = self._make_family_profile(
            filing_status=FilingStatus.SINGLE, num_children=1, gross_receipts=250_000,
        )
        result = calculate_return(profile)
        assert result.tax_credits.phaseout_reduction > 0

    def test_no_children_zero_credits(self):
        """No dependents means no credits."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            businesses=[ScheduleCData(business_name="Biz", gross_receipts=100_000)],
        )
        result = calculate_return(profile)
        assert result.tax_credits is None
        assert result.nonrefundable_credits == 0

    def test_ctc_limited_to_tax_liability(self):
        """Nonrefundable CTC cannot exceed tax liability."""
        # Low income: tax is small, CTC should be limited
        profile = self._make_family_profile(gross_receipts=30_000)
        result = calculate_return(profile)
        assert result.tax_credits.nonrefundable_credit <= (result.tax + result.amt)

    def test_actc_refundable(self):
        """Unused CTC becomes refundable ACTC up to per-child cap."""
        # Low income so CTC exceeds tax, remainder → ACTC
        profile = self._make_family_profile(gross_receipts=40_000)
        result = calculate_return(profile)
        if result.tax_credits.nonrefundable_credit < result.tax_credits.gross_ctc:
            # There's unused CTC, ACTC should be computed
            assert result.tax_credits.refundable_actc >= 0

    def test_actc_earned_income_formula(self):
        """ACTC = 15% of (earned income - $2,500)."""
        profile = self._make_family_profile(num_children=3, gross_receipts=20_000)
        result = calculate_return(profile)
        # earned_income = 20K, ACTC formula = 15% * (20K - 2.5K) = 2,625
        max_by_formula = round(0.15 * (20_000 - 2_500), 2)
        assert result.tax_credits.refundable_actc <= max_by_formula

    def test_odc(self):
        """Other dependent credit = $500 per non-CTC dependent."""
        deps = [
            Dependent(first_name="Child", last_name="Test",
                      relationship="child", is_qualifying_child_ctc=True),
            Dependent(first_name="Grandma", last_name="Test",
                      relationship="parent", is_qualifying_child_ctc=False),
        ]
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            dependents=deps,
            businesses=[ScheduleCData(business_name="Biz", gross_receipts=100_000)],
        )
        result = calculate_return(profile)
        assert result.tax_credits.gross_odc == 500
        assert result.tax_credits.gross_ctc == 2_500

    def test_credits_flow_to_return(self):
        """Nonrefundable credits reduce total_tax; ACTC increases payments."""
        profile = self._make_family_profile()
        result_with = calculate_return(profile)
        # Compare to no-dependent profile
        profile_no_deps = TaxpayerProfile(
            filing_status=FilingStatus.MFJ,
            businesses=[ScheduleCData(business_name="Biz", gross_receipts=100_000)],
        )
        result_without = calculate_return(profile_no_deps)
        # With credits, total tax should be lower
        assert result_with.total_tax <= result_without.total_tax

    def test_mfs_no_eitc(self):
        """MFS filers are disqualified from EITC (stub returns 0)."""
        profile = self._make_family_profile(filing_status=FilingStatus.MFS)
        result = calculate_return(profile)
        # No EITC field — it's just not computed for MFS
        # This test confirms MFS with children still works
        assert result.tax_credits is not None


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


# =============================================================================
# TestQDCGWorksheet — Fix #2
# =============================================================================

class TestQDCGWorksheet:
    """Tests for the Qualified Dividends and Capital Gain Tax Worksheet."""

    def test_zero_pct_rate_single(self):
        """LTCG fully in the 0% bracket for a single filer."""
        # $40,000 taxable income, all from LTCG → all in 0% bracket ($48,350 threshold)
        tax = calculate_tax_with_qdcg_worksheet(
            taxable_income=40_000, qualified_dividends=0,
            net_lt_gain=40_000, net_st_gain=0,
            filing_status=FilingStatus.SINGLE,
        )
        assert tax == 0.0

    def test_fifteen_pct_rate_single(self):
        """LTCG taxed at 15% for a single filer above 0% threshold."""
        # $100,000 ordinary + $50,000 LTCG = $150,000 taxable
        # All LTCG is above the $48,350 threshold, taxed at 15%
        tax = calculate_tax_with_qdcg_worksheet(
            taxable_income=150_000, qualified_dividends=0,
            net_lt_gain=50_000, net_st_gain=0,
            filing_status=FilingStatus.SINGLE,
        )
        ordinary_tax = calculate_income_tax(100_000, BRACKETS_BY_STATUS[FilingStatus.SINGLE])
        # All $50K LTCG is above the 0% zone (ordinary already fills it)
        expected = ordinary_tax + 50_000 * 0.15
        assert tax == round(expected, 2)

    def test_twenty_pct_rate_single(self):
        """LTCG taxed at 20% for very high income single filer."""
        # $540,000 ordinary + $50,000 LTCG = $590,000 taxable
        # 15% threshold for single is $533,400
        tax = calculate_tax_with_qdcg_worksheet(
            taxable_income=590_000, qualified_dividends=0,
            net_lt_gain=50_000, net_st_gain=0,
            filing_status=FilingStatus.SINGLE,
        )
        ordinary_tax = calculate_income_tax(540_000, BRACKETS_BY_STATUS[FilingStatus.SINGLE])
        # ordinary $540K > $533,400 threshold, so all LTCG at 20%
        expected = ordinary_tax + 50_000 * 0.20
        assert tax == round(expected, 2)

    def test_qualified_dividends_at_zero_pct(self):
        """Qualified dividends taxed at 0% when under threshold."""
        # $30,000 all qualified dividends, single filer
        tax = calculate_tax_with_qdcg_worksheet(
            taxable_income=30_000, qualified_dividends=30_000,
            net_lt_gain=0, net_st_gain=0,
            filing_status=FilingStatus.SINGLE,
        )
        assert tax == 0.0

    def test_mixed_ordinary_and_preferential(self):
        """Mixed ordinary income + qualified dividends + LTCG."""
        # MFS: $60,000 ordinary + $10,000 qual divs + $20,000 LTCG = $90,000
        # 0% threshold MFS: $48,350; 15% threshold: $300,000
        tax = calculate_tax_with_qdcg_worksheet(
            taxable_income=90_000, qualified_dividends=10_000,
            net_lt_gain=20_000, net_st_gain=0,
            filing_status=FilingStatus.MFS,
        )
        ordinary_tax = calculate_income_tax(60_000, BRACKETS_BY_STATUS[FilingStatus.MFS])
        # preferential = 30K, ordinary = 60K
        # 0% room: max(48350 - 60000, 0) = 0 → all 30K at 15%
        expected = ordinary_tax + 30_000 * 0.15
        assert tax == round(expected, 2)

    def test_stcl_offsets_ltcg(self):
        """Short-term capital loss reduces net capital gain."""
        # $80,000 ordinary + $20,000 LTCG - $10,000 STCL = $90,000 taxable
        # net_cap_gain = max(20000 + (-10000), 0) = 10000
        tax = calculate_tax_with_qdcg_worksheet(
            taxable_income=90_000, qualified_dividends=0,
            net_lt_gain=20_000, net_st_gain=-10_000,
            filing_status=FilingStatus.SINGLE,
        )
        ordinary_tax = calculate_income_tax(80_000, BRACKETS_BY_STATUS[FilingStatus.SINGLE])
        # preferential = 10K, ordinary = 80K
        # 0% room: max(48350 - 80000, 0) = 0 → all 10K at 15%
        expected = ordinary_tax + 10_000 * 0.15
        assert tax == round(expected, 2)

    def test_min_check_returns_regular_if_lower(self):
        """QDCG worksheet never produces more tax than regular brackets."""
        # Edge case: all income is ordinary (no preferential income)
        regular_tax = calculate_income_tax(50_000, BRACKETS_BY_STATUS[FilingStatus.SINGLE])
        worksheet_tax = calculate_tax_with_qdcg_worksheet(
            taxable_income=50_000, qualified_dividends=0,
            net_lt_gain=0, net_st_gain=0,
            filing_status=FilingStatus.SINGLE,
        )
        assert worksheet_tax == regular_tax

    def test_integration_with_calculate_return(self):
        """calculate_return() uses QDCG worksheet when qualified dividends exist."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_div=[Form1099DIV(
                payer_name="Vanguard",
                ordinary_dividends=10_000,
                qualified_dividends=8_000,
            )],
        )
        result = calculate_return(profile)
        # Tax should be less than if all dividends were ordinary
        regular_tax = calculate_income_tax(result.taxable_income, BRACKETS_BY_STATUS[FilingStatus.SINGLE])
        assert result.tax <= regular_tax


# =============================================================================
# TestNECWithholdingAndRouting — Fix #5
# =============================================================================

class TestNECWithholdingAndRouting:
    """Tests for 1099-NEC withholding and auto Schedule C creation."""

    def test_nec_withholding_included(self):
        """1099-NEC federal withholding should be included in total payments."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            businesses=[ScheduleCData(
                business_name="Consulting",
                gross_receipts=50_000,
            )],
            forms_1099_nec=[Form1099NEC(
                payer_name="Client A",
                nonemployee_compensation=50_000,
                federal_tax_withheld=5_000,
            )],
        )
        result = calculate_return(profile)
        assert result.withholding == 5_000

    def test_auto_create_schedule_c_from_nec(self):
        """When no businesses defined, 1099-NEC creates auto Schedule C."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_nec=[
                Form1099NEC(payer_name="Client A", nonemployee_compensation=30_000),
                Form1099NEC(payer_name="Client B", nonemployee_compensation=20_000),
            ],
        )
        result = calculate_return(profile)
        assert len(result.schedule_c_results) == 1
        assert result.schedule_c_results[0].gross_receipts == 50_000
        assert result.schedule_c_results[0].business_name == "1099-NEC Income"

    def test_no_auto_create_when_businesses_exist(self):
        """When businesses are defined, 1099-NEC does NOT auto-create Schedule C."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            businesses=[ScheduleCData(
                business_name="My Biz",
                gross_receipts=80_000,
            )],
            forms_1099_nec=[Form1099NEC(
                payer_name="Client",
                nonemployee_compensation=80_000,
            )],
        )
        result = calculate_return(profile)
        assert len(result.schedule_c_results) == 1
        assert result.schedule_c_results[0].business_name == "My Biz"

    def test_profile_not_mutated(self):
        """Auto Schedule C creation should not mutate profile.businesses."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.SINGLE,
            forms_1099_nec=[Form1099NEC(
                payer_name="Client",
                nonemployee_compensation=25_000,
            )],
        )
        assert len(profile.businesses) == 0
        calculate_return(profile)
        assert len(profile.businesses) == 0  # profile unchanged


# =============================================================================
# TestFEIEIntegration — Fix #1
# =============================================================================

class TestFEIEIntegration:
    """Tests for FEIE result returned from compare_feie_scenarios()."""

    def test_feie_result_key_returned(self):
        """compare_feie_scenarios() should include 'feie_result' key."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            days_in_foreign_country_2025=340,
            businesses=[ScheduleCData(
                business_name="Remote Consulting",
                gross_receipts=120_000,
            )],
        )
        scenarios = compare_feie_scenarios(profile)
        assert "feie_result" in scenarios

    def test_feie_result_is_form2555_result(self):
        """feie_result should be a Form2555Result instance."""
        profile = TaxpayerProfile(
            filing_status=FilingStatus.MFS,
            days_in_foreign_country_2025=340,
            businesses=[ScheduleCData(
                business_name="Remote Consulting",
                gross_receipts=120_000,
            )],
        )
        scenarios = compare_feie_scenarios(profile)
        assert isinstance(scenarios["feie_result"], Form2555Result)
