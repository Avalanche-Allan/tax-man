"""Tests for data models and validation."""

import pytest

from taxman.models import (
    BusinessExpenses,
    CharityReceipt,
    EstimatedPayment,
    FilingStatus,
    Form1095A,
    Form1098,
    Form1099NEC,
    FormW2,
    HealthInsurance,
    HomeOffice,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)
from taxman.validation import (
    ValidationError,
    validate_ein,
    validate_months,
    validate_non_negative,
    validate_percentage,
    validate_positive,
    validate_quarter,
    validate_range,
    validate_tin,
)


# =============================================================================
# TIN / EIN Validation (via models)
# =============================================================================

class TestTINValidation:
    def test_valid_ssn_dashed(self):
        p = TaxpayerProfile(ssn="123-45-6789")
        assert p.ssn == "123-45-6789"

    def test_valid_ssn_digits(self):
        """Normalizes 9-digit SSN to dashed format."""
        p = TaxpayerProfile(ssn="123456789")
        assert p.ssn == "123-45-6789"

    def test_empty_ssn_ok(self):
        p = TaxpayerProfile(ssn="")
        assert p.ssn == ""

    def test_invalid_ssn(self):
        with pytest.raises(ValidationError):
            TaxpayerProfile(ssn="123-456-789")

    def test_spouse_ssn_validated(self):
        p = TaxpayerProfile(spouse_ssn="987654321")
        assert p.spouse_ssn == "987-65-4321"


class TestEINValidation:
    def test_valid_ein_dashed(self):
        nec = Form1099NEC(payer_tin="12-3456789")
        assert nec.payer_tin == "12-3456789"

    def test_valid_ein_digits(self):
        nec = Form1099NEC(payer_tin="123456789")
        assert nec.payer_tin == "12-3456789"

    def test_empty_ein_ok(self):
        nec = Form1099NEC(payer_tin="")
        assert nec.payer_tin == ""

    def test_invalid_ein(self):
        with pytest.raises(ValidationError):
            Form1099NEC(payer_tin="abc-defghij")

    def test_k1_ein_validated(self):
        k1 = ScheduleK1(partnership_ein="987654321")
        assert k1.partnership_ein == "98-7654321"

    def test_schedule_c_ein(self):
        sc = ScheduleCData(business_ein="123456789")
        assert sc.business_ein == "12-3456789"


# =============================================================================
# Amount / Range Validation (via models)
# =============================================================================

class TestAmountValidation:
    def test_negative_compensation_rejected(self):
        with pytest.raises(ValidationError):
            Form1099NEC(nonemployee_compensation=-100)

    def test_negative_withheld_rejected(self):
        with pytest.raises(ValidationError):
            Form1099NEC(federal_tax_withheld=-50)

    def test_negative_estimated_payment(self):
        with pytest.raises(ValidationError):
            EstimatedPayment(amount=-100)

    def test_negative_premiums(self):
        with pytest.raises(ValidationError):
            HealthInsurance(total_premiums=-500)

    def test_negative_gross_receipts(self):
        with pytest.raises(ValidationError):
            ScheduleCData(gross_receipts=-1000)

    def test_zero_amounts_ok(self):
        nec = Form1099NEC(nonemployee_compensation=0)
        assert nec.nonemployee_compensation == 0


class TestQuarterValidation:
    def test_valid_quarters(self):
        for q in (1, 2, 3, 4):
            p = EstimatedPayment(quarter=q, amount=1000)
            assert p.quarter == q

    def test_zero_quarter_ok(self):
        p = EstimatedPayment(quarter=0)
        assert p.quarter == 0

    def test_invalid_quarter(self):
        with pytest.raises(ValidationError):
            EstimatedPayment(quarter=5)

    def test_negative_quarter(self):
        with pytest.raises(ValidationError):
            EstimatedPayment(quarter=-1)


class TestMonthsValidation:
    def test_valid_months(self):
        hi = HealthInsurance(months_covered=6)
        assert hi.months_covered == 6

    def test_invalid_months_zero(self):
        with pytest.raises(ValidationError):
            HealthInsurance(months_covered=0)

    def test_invalid_months_13(self):
        with pytest.raises(ValidationError):
            HealthInsurance(months_covered=13)


# =============================================================================
# HomeOffice
# =============================================================================

class TestHomeOffice:
    def test_internet_pct_as_decimal(self):
        ho = HomeOffice(internet_business_pct=0.60)
        assert ho.internet_business_pct == 0.60

    def test_internet_pct_as_whole_number(self):
        """Bug 9 fix: >1 values normalized to decimal."""
        ho = HomeOffice(internet_business_pct=60)
        assert ho.internet_business_pct == 0.60

    def test_internet_pct_100(self):
        ho = HomeOffice(internet_business_pct=100)
        assert ho.internet_business_pct == 1.0

    def test_simplified_deduction(self):
        ho = HomeOffice(
            use_simplified_method=True,
            square_footage=250,
            months_used=12,
        )
        assert ho.simplified_deduction == 1_250.0  # 250 * $5

    def test_simplified_capped_at_300(self):
        ho = HomeOffice(
            use_simplified_method=True,
            square_footage=500,
        )
        assert ho.simplified_deduction == 1_500.0  # 300 * $5

    def test_simplified_partial_year(self):
        ho = HomeOffice(
            use_simplified_method=True,
            square_footage=300,
            months_used=6,
        )
        assert ho.simplified_deduction == 750.0  # 1500 * 6/12

    def test_business_percentage(self):
        ho = HomeOffice(
            total_home_sqft=1000,
            office_sqft=200,
        )
        assert ho.business_percentage == 0.2

    def test_business_percentage_zero_total(self):
        ho = HomeOffice(total_home_sqft=0)
        assert ho.business_percentage == 0.0

    def test_regular_deduction(self):
        ho = HomeOffice(
            use_simplified_method=False,
            total_home_sqft=1000,
            office_sqft=200,
            rent=12_000,
            utilities=2_400,
            insurance=1_200,
            repairs=600,
            internet=1_200,
            internet_business_pct=0.5,
            months_used=12,
        )
        # pct = 0.2
        # direct = (12000+2400+1200+600) * 0.2 = 3240
        # internet = 1200 * 0.5 = 600
        # total = 3840
        assert abs(ho.regular_deduction - 3_840.0) < 0.01


# =============================================================================
# BusinessExpenses
# =============================================================================

class TestBusinessExpenses:
    def test_total_with_meals_50pct(self):
        exp = BusinessExpenses(
            office_expense=1_000,
            meals=2_000,
        )
        # office + meals*50%
        assert exp.total == 2_000.0

    def test_total_all_zeros(self):
        exp = BusinessExpenses()
        assert exp.total == 0.0


# =============================================================================
# ScheduleCData Properties
# =============================================================================

class TestScheduleCData:
    def test_gross_income(self):
        sc = ScheduleCData(gross_receipts=100_000, returns_and_allowances=5_000)
        assert sc.gross_income == 95_000

    def test_gross_profit(self):
        sc = ScheduleCData(
            gross_receipts=100_000,
            cost_of_goods_sold=30_000,
        )
        assert sc.gross_profit == 70_000

    def test_net_profit(self):
        sc = ScheduleCData(
            gross_receipts=100_000,
            expenses=BusinessExpenses(office_expense=10_000),
        )
        assert sc.net_profit == 90_000


# =============================================================================
# Document Types
# =============================================================================

class TestFormW2:
    def test_basic_w2(self):
        w2 = FormW2(
            employer_name="ACME Corp",
            employer_ein="12-3456789",
            wages=75_000,
            federal_tax_withheld=15_000,
        )
        assert w2.wages == 75_000
        assert w2.employer_ein == "12-3456789"

    def test_w2_negative_wages_rejected(self):
        with pytest.raises(ValidationError):
            FormW2(wages=-1000)


class TestForm1098:
    def test_basic_1098(self):
        f = Form1098(
            lender_name="Bank of America",
            mortgage_interest=12_000,
            points_paid=500,
        )
        assert f.mortgage_interest == 12_000

    def test_negative_interest_rejected(self):
        with pytest.raises(ValidationError):
            Form1098(mortgage_interest=-100)


class TestForm1095A:
    def test_totals(self):
        f = Form1095A(
            monthly_premiums=[500.0] * 12,
            monthly_slcsp=[600.0] * 12,
            monthly_aptc=[100.0] * 12,
        )
        assert f.total_premiums == 6_000.0
        assert f.total_slcsp == 7_200.0
        assert f.total_aptc == 1_200.0


class TestCharityReceipt:
    def test_basic_receipt(self):
        r = CharityReceipt(
            organization_name="Red Cross",
            amount=500,
        )
        assert r.amount == 500

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            CharityReceipt(amount=-100)


# =============================================================================
# TaxpayerProfile
# =============================================================================

class TestTaxpayerProfile:
    def test_total_estimated_payments(self):
        p = TaxpayerProfile(
            estimated_payments=[
                EstimatedPayment(quarter=1, amount=5_000),
                EstimatedPayment(quarter=2, amount=5_000),
            ],
        )
        assert p.total_estimated_payments == 10_000

    def test_empty_estimated_payments(self):
        p = TaxpayerProfile()
        assert p.total_estimated_payments == 0

    def test_filing_status_enum(self):
        for status in FilingStatus:
            p = TaxpayerProfile(filing_status=status)
            assert p.filing_status == status


# =============================================================================
# Standalone Validation Functions
# =============================================================================

class TestValidateTIN:
    def test_dashed_ssn(self):
        assert validate_tin("123-45-6789") == "123-45-6789"

    def test_digits_only(self):
        assert validate_tin("123456789") == "123-45-6789"

    def test_empty_ok(self):
        assert validate_tin("") == ""

    def test_whitespace_stripped(self):
        assert validate_tin("  123-45-6789  ") == "123-45-6789"

    def test_invalid_format(self):
        with pytest.raises(ValidationError):
            validate_tin("12-345-6789")

    def test_too_short(self):
        with pytest.raises(ValidationError):
            validate_tin("12345")

    def test_letters(self):
        with pytest.raises(ValidationError):
            validate_tin("abc-de-fghi")


class TestValidateEIN:
    def test_dashed_ein(self):
        assert validate_ein("12-3456789") == "12-3456789"

    def test_digits_only(self):
        assert validate_ein("123456789") == "12-3456789"

    def test_empty_ok(self):
        assert validate_ein("") == ""

    def test_invalid_format(self):
        with pytest.raises(ValidationError):
            validate_ein("123-45-6789")  # SSN format

    def test_too_short(self):
        with pytest.raises(ValidationError):
            validate_ein("12345")


class TestValidateNonNegative:
    def test_zero(self):
        assert validate_non_negative(0) == 0

    def test_positive(self):
        assert validate_non_negative(100.50) == 100.50

    def test_negative(self):
        with pytest.raises(ValidationError):
            validate_non_negative(-1)


class TestValidatePositive:
    def test_positive(self):
        assert validate_positive(1) == 1

    def test_zero_rejected(self):
        with pytest.raises(ValidationError):
            validate_positive(0)

    def test_negative_rejected(self):
        with pytest.raises(ValidationError):
            validate_positive(-5)


class TestValidateRange:
    def test_in_range(self):
        assert validate_range(50, 0, 100) == 50

    def test_at_min(self):
        assert validate_range(0, 0, 100) == 0

    def test_at_max(self):
        assert validate_range(100, 0, 100) == 100

    def test_below_min(self):
        with pytest.raises(ValidationError):
            validate_range(-1, 0, 100)

    def test_above_max(self):
        with pytest.raises(ValidationError):
            validate_range(101, 0, 100)


class TestValidatePercentage:
    def test_zero(self):
        assert validate_percentage(0) == 0

    def test_hundred(self):
        assert validate_percentage(100) == 100

    def test_decimal(self):
        assert validate_percentage(0.5) == 0.5

    def test_whole_number(self):
        assert validate_percentage(50) == 50

    def test_above_100(self):
        with pytest.raises(ValidationError):
            validate_percentage(150)

    def test_negative(self):
        with pytest.raises(ValidationError):
            validate_percentage(-10)


class TestValidateQuarter:
    def test_valid_quarters(self):
        for q in (1, 2, 3, 4):
            assert validate_quarter(q) == q

    def test_zero_ok(self):
        assert validate_quarter(0) == 0

    def test_invalid_5(self):
        with pytest.raises(ValidationError):
            validate_quarter(5)

    def test_negative(self):
        with pytest.raises(ValidationError):
            validate_quarter(-1)


class TestValidateMonths:
    def test_valid_months(self):
        for m in range(1, 13):
            assert validate_months(m) == m

    def test_zero(self):
        with pytest.raises(ValidationError):
            validate_months(0)

    def test_13(self):
        with pytest.raises(ValidationError):
            validate_months(13)
