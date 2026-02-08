"""Factory functions for test profiles."""

from taxman.models import (
    AccountingMethod,
    BusinessExpenses,
    BusinessType,
    EstimatedPayment,
    FilingStatus,
    Form1099NEC,
    HealthInsurance,
    HomeOffice,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)


def make_mfs_expat_profile() -> TaxpayerProfile:
    """MFS expat in Mexico with law firm LLC + DocSherpa + K-1 rental.

    This is the primary test profile matching the actual user scenario.
    """
    return TaxpayerProfile(
        first_name="Test",
        last_name="Taxpayer",
        ssn="123-45-6789",
        filing_status=FilingStatus.MFS,
        foreign_address=True,
        country="Mexico",
        foreign_country="Mexico",
        days_in_foreign_country_2025=340,
        days_in_us_2025=25,
        has_colorado_filing_obligation=True,
        forms_1099_nec=[
            Form1099NEC(
                payer_name="Big Law Firm LLP",
                payer_tin="12-3456789",
                nonemployee_compensation=120_000.00,
            ),
        ],
        businesses=[
            ScheduleCData(
                business_name="Law Consulting LLC",
                business_type=BusinessType.SINGLE_MEMBER_LLC,
                principal_business_code="541110",
                business_description="Legal consulting",
                accounting_method=AccountingMethod.CASH,
                gross_receipts=120_000.00,
                expenses=BusinessExpenses(
                    office_expense=1_200.00,
                    supplies=500.00,
                    travel=3_000.00,
                    meals=2_000.00,
                    legal_and_professional=800.00,
                ),
                home_office=HomeOffice(
                    use_simplified_method=True,
                    square_footage=200,
                    months_used=12,
                ),
            ),
            ScheduleCData(
                business_name="DocSherpa LLC",
                business_type=BusinessType.SINGLE_MEMBER_LLC,
                principal_business_code="511210",
                business_description="SaaS software",
                accounting_method=AccountingMethod.CASH,
                gross_receipts=500.00,
                expenses=BusinessExpenses(
                    office_expense=100.00,
                    supplies=50.00,
                ),
            ),
        ],
        schedule_k1s=[
            ScheduleK1(
                partnership_name="Denver Rental Partners",
                partnership_ein="98-7654321",
                partner_share_profit=50.0,
                net_rental_income=-3_500.00,
                interest_income=150.00,
            ),
        ],
        health_insurance=HealthInsurance(
            provider="BUPA Mexico",
            total_premiums=8_400.00,
            months_covered=12,
        ),
        estimated_payments=[
            EstimatedPayment(quarter=1, amount=8_000.00),
            EstimatedPayment(quarter=2, amount=8_000.00),
            EstimatedPayment(quarter=3, amount=8_000.00),
            EstimatedPayment(quarter=4, amount=8_000.00),
        ],
    )


def make_single_freelancer_profile() -> TaxpayerProfile:
    """Single freelancer — one Schedule C, no K-1, domestic."""
    return TaxpayerProfile(
        first_name="Jane",
        last_name="Freelancer",
        ssn="987-65-4321",
        filing_status=FilingStatus.SINGLE,
        foreign_address=False,
        country="US",
        state="TX",
        businesses=[
            ScheduleCData(
                business_name="Jane Design Studio",
                business_type=BusinessType.SOLE_PROPRIETORSHIP,
                principal_business_code="541430",
                business_description="Graphic design",
                gross_receipts=85_000.00,
                expenses=BusinessExpenses(
                    office_expense=600.00,
                    supplies=1_200.00,
                    advertising=500.00,
                    travel=2_000.00,
                    meals=1_500.00,
                ),
            ),
        ],
    )


def make_mfj_high_income_profile() -> TaxpayerProfile:
    """MFJ high-income couple with W-2 wages (simulated as 1099) + rental."""
    return TaxpayerProfile(
        first_name="Rich",
        last_name="Couple",
        ssn="111-22-3333",
        filing_status=FilingStatus.MFJ,
        foreign_address=False,
        country="US",
        businesses=[
            ScheduleCData(
                business_name="Consulting Inc",
                business_type=BusinessType.SINGLE_MEMBER_LLC,
                gross_receipts=450_000.00,
                expenses=BusinessExpenses(
                    legal_and_professional=15_000.00,
                    travel=10_000.00,
                    meals=8_000.00,
                    office_expense=5_000.00,
                ),
            ),
        ],
        schedule_k1s=[
            ScheduleK1(
                partnership_name="Real Estate Fund LP",
                partnership_ein="55-1234567",
                partner_share_profit=25.0,
                net_rental_income=12_000.00,
                interest_income=2_500.00,
                net_long_term_capital_gain=5_000.00,
            ),
        ],
        health_insurance=HealthInsurance(
            provider="Blue Cross",
            total_premiums=18_000.00,
        ),
        estimated_payments=[
            EstimatedPayment(quarter=1, amount=25_000.00),
            EstimatedPayment(quarter=2, amount=25_000.00),
            EstimatedPayment(quarter=3, amount=25_000.00),
            EstimatedPayment(quarter=4, amount=25_000.00),
        ],
    )


def make_minimal_profile() -> TaxpayerProfile:
    """Minimal profile — single, one small business, no deductions."""
    return TaxpayerProfile(
        first_name="Min",
        last_name="Profile",
        filing_status=FilingStatus.SINGLE,
        businesses=[
            ScheduleCData(
                business_name="Side Gig",
                gross_receipts=5_000.00,
            ),
        ],
    )


def make_zero_income_profile() -> TaxpayerProfile:
    """Profile with zero income (edge case)."""
    return TaxpayerProfile(
        first_name="Zero",
        last_name="Income",
        filing_status=FilingStatus.SINGLE,
    )
