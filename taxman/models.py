"""Data models for tax documents and form data."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from taxman.validation import (
    validate_ein,
    validate_months,
    validate_non_negative,
    validate_percentage,
    validate_quarter,
    validate_tin,
)


class FilingStatus(Enum):
    SINGLE = "single"
    MFJ = "mfj"
    MFS = "mfs"
    HOH = "hoh"
    QSS = "qss"


class BusinessType(Enum):
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    SINGLE_MEMBER_LLC = "single_member_llc"


class AccountingMethod(Enum):
    CASH = "cash"
    ACCRUAL = "accrual"


# --- Source Documents ---

@dataclass
class Form1099NEC:
    """1099-NEC: Nonemployee Compensation"""
    payer_name: str = ""
    payer_tin: str = ""
    recipient_name: str = ""
    recipient_tin: str = ""
    nonemployee_compensation: float = 0.0  # Box 1
    federal_tax_withheld: float = 0.0  # Box 4
    state_tax_withheld: float = 0.0  # Box 5
    state: str = ""
    tax_year: int = 2025

    def __post_init__(self):
        if self.payer_tin:
            self.payer_tin = validate_ein(self.payer_tin, "payer_tin")
        if self.recipient_tin:
            # Could be SSN or EIN
            try:
                self.recipient_tin = validate_tin(self.recipient_tin, "recipient_tin")
            except Exception:
                self.recipient_tin = validate_ein(self.recipient_tin, "recipient_tin")
        validate_non_negative(self.nonemployee_compensation, "nonemployee_compensation")
        validate_non_negative(self.federal_tax_withheld, "federal_tax_withheld")
        validate_non_negative(self.state_tax_withheld, "state_tax_withheld")


@dataclass
class ScheduleK1:
    """Schedule K-1 (Form 1065): Partner's Share of Income"""
    partnership_name: str = ""
    partnership_ein: str = ""
    partner_name: str = ""
    partner_tin: str = ""
    partner_share_profit: float = 0.0  # percent
    partner_share_loss: float = 0.0  # percent
    partner_share_capital: float = 0.0  # percent
    ordinary_business_income: float = 0.0  # Box 1
    net_rental_income: float = 0.0  # Box 2
    other_net_rental_income: float = 0.0  # Box 3
    guaranteed_payments: float = 0.0  # Box 4
    interest_income: float = 0.0  # Box 5
    dividends: float = 0.0  # Box 6a
    qualified_dividends: float = 0.0  # Box 6b
    royalties: float = 0.0  # Box 7
    net_short_term_capital_gain: float = 0.0  # Box 8
    net_long_term_capital_gain: float = 0.0  # Box 9a
    net_section_1231_gain: float = 0.0  # Box 10
    other_income: float = 0.0  # Box 11
    section_179_deduction: float = 0.0  # Box 12
    other_deductions: float = 0.0  # Box 13
    self_employment_earnings: float = 0.0  # Box 14
    # QBI info (Box 20, Code Z — reported on Statement A)
    qbi_amount: float = 0.0  # Partner's share of QBI
    qbi_w2_wages: float = 0.0  # Partner's share of W-2 wages for QBI
    qbi_ubia: float = 0.0  # Partner's share of UBIA
    is_sstb: bool = False  # Specified service trade or business
    tax_year: int = 2025

    def __post_init__(self):
        if self.partnership_ein:
            self.partnership_ein = validate_ein(self.partnership_ein, "partnership_ein")
        if self.partner_tin:
            try:
                self.partner_tin = validate_tin(self.partner_tin, "partner_tin")
            except Exception:
                self.partner_tin = validate_ein(self.partner_tin, "partner_tin")


@dataclass
class EstimatedPayment:
    """Quarterly estimated tax payment (Form 1040-ES)"""
    quarter: int = 0  # 1-4
    date_paid: str = ""
    amount: float = 0.0

    def __post_init__(self):
        validate_quarter(self.quarter, "quarter")
        validate_non_negative(self.amount, "amount")


@dataclass
class HealthInsurance:
    """Self-employed health insurance premiums"""
    provider: str = ""
    total_premiums: float = 0.0
    months_covered: int = 12

    def __post_init__(self):
        validate_non_negative(self.total_premiums, "total_premiums")
        validate_months(self.months_covered, "months_covered")


# --- New Document Types (Phase 3) ---

@dataclass
class FormW2:
    """W-2: Wage and Tax Statement"""
    employer_name: str = ""
    employer_ein: str = ""
    employee_name: str = ""
    employee_ssn: str = ""
    wages: float = 0.0  # Box 1
    federal_tax_withheld: float = 0.0  # Box 2
    ss_wages: float = 0.0  # Box 3
    ss_tax_withheld: float = 0.0  # Box 4
    medicare_wages: float = 0.0  # Box 5
    medicare_tax_withheld: float = 0.0  # Box 6
    state_wages: float = 0.0  # Box 16
    state_tax_withheld: float = 0.0  # Box 17
    state: str = ""
    tax_year: int = 2025

    def __post_init__(self):
        if self.employer_ein:
            self.employer_ein = validate_ein(self.employer_ein, "employer_ein")
        if self.employee_ssn:
            self.employee_ssn = validate_tin(self.employee_ssn, "employee_ssn")
        validate_non_negative(self.wages, "wages")
        validate_non_negative(self.federal_tax_withheld, "federal_tax_withheld")


@dataclass
class Form1098:
    """1098: Mortgage Interest Statement"""
    lender_name: str = ""
    lender_ein: str = ""
    mortgage_interest: float = 0.0  # Box 1
    points_paid: float = 0.0  # Box 6
    outstanding_principal: float = 0.0  # Box 2
    tax_year: int = 2025

    def __post_init__(self):
        if self.lender_ein:
            self.lender_ein = validate_ein(self.lender_ein, "lender_ein")
        validate_non_negative(self.mortgage_interest, "mortgage_interest")
        validate_non_negative(self.points_paid, "points_paid")


@dataclass
class Form1095A:
    """1095-A: Health Insurance Marketplace Statement"""
    marketplace_name: str = ""
    policy_number: str = ""
    monthly_premiums: list[float] = field(default_factory=lambda: [0.0] * 12)
    monthly_slcsp: list[float] = field(default_factory=lambda: [0.0] * 12)
    monthly_aptc: list[float] = field(default_factory=lambda: [0.0] * 12)
    tax_year: int = 2025

    @property
    def total_premiums(self) -> float:
        return sum(self.monthly_premiums)

    @property
    def total_slcsp(self) -> float:
        return sum(self.monthly_slcsp)

    @property
    def total_aptc(self) -> float:
        return sum(self.monthly_aptc)


@dataclass
class Form1099INT:
    """1099-INT: Interest Income"""
    payer_name: str = ""
    payer_tin: str = ""
    interest_income: float = 0.0           # Box 1 (taxable interest)
    early_withdrawal_penalty: float = 0.0  # Box 2
    tax_exempt_interest: float = 0.0       # Box 8
    federal_tax_withheld: float = 0.0      # Box 4
    tax_year: int = 2025

    def __post_init__(self):
        if self.payer_tin:
            self.payer_tin = validate_ein(self.payer_tin, "payer_tin")
        validate_non_negative(self.interest_income, "interest_income")
        validate_non_negative(self.tax_exempt_interest, "tax_exempt_interest")
        validate_non_negative(self.federal_tax_withheld, "federal_tax_withheld")


@dataclass
class Form1099DIV:
    """1099-DIV: Dividends and Distributions"""
    payer_name: str = ""
    payer_tin: str = ""
    ordinary_dividends: float = 0.0        # Box 1a
    qualified_dividends: float = 0.0       # Box 1b
    capital_gain_distributions: float = 0.0  # Box 2a
    federal_tax_withheld: float = 0.0      # Box 4
    section_199a_dividends: float = 0.0    # Box 5
    tax_year: int = 2025

    def __post_init__(self):
        if self.payer_tin:
            self.payer_tin = validate_ein(self.payer_tin, "payer_tin")
        validate_non_negative(self.ordinary_dividends, "ordinary_dividends")
        validate_non_negative(self.qualified_dividends, "qualified_dividends")
        validate_non_negative(self.capital_gain_distributions, "capital_gain_distributions")
        validate_non_negative(self.federal_tax_withheld, "federal_tax_withheld")


@dataclass
class Form1099B:
    """1099-B: Proceeds From Broker and Barter Exchange Transactions (aggregated)"""
    broker_name: str = ""
    broker_tin: str = ""
    st_proceeds: float = 0.0      # Short-term total proceeds
    st_cost_basis: float = 0.0    # Short-term total cost basis
    lt_proceeds: float = 0.0      # Long-term total proceeds
    lt_cost_basis: float = 0.0    # Long-term total cost basis
    federal_tax_withheld: float = 0.0
    tax_year: int = 2025

    def __post_init__(self):
        if self.broker_tin:
            self.broker_tin = validate_ein(self.broker_tin, "broker_tin")
        validate_non_negative(self.federal_tax_withheld, "federal_tax_withheld")

    @property
    def net_st_gain_loss(self) -> float:
        return self.st_proceeds - self.st_cost_basis

    @property
    def net_lt_gain_loss(self) -> float:
        return self.lt_proceeds - self.lt_cost_basis


@dataclass
class Dependent:
    """A dependent claimed on the return."""
    first_name: str = ""
    last_name: str = ""
    ssn: str = ""
    relationship: str = ""
    is_qualifying_child_ctc: bool = False  # Qualifies for Child Tax Credit

    def __post_init__(self):
        if self.ssn:
            self.ssn = validate_tin(self.ssn, "ssn")


@dataclass
class CharityReceipt:
    """Charitable contribution receipt"""
    organization_name: str = ""
    organization_ein: str = ""
    amount: float = 0.0
    date: str = ""
    cash_or_property: str = "cash"
    description: str = ""

    def __post_init__(self):
        if self.organization_ein:
            self.organization_ein = validate_ein(self.organization_ein, "organization_ein")
        validate_non_negative(self.amount, "amount")


# --- Business Expenses ---

@dataclass
class BusinessExpenses:
    """Categorized business expenses for Schedule C"""
    advertising: float = 0.0
    car_and_truck: float = 0.0
    commissions_and_fees: float = 0.0
    contract_labor: float = 0.0
    depreciation: float = 0.0
    employee_benefit_programs: float = 0.0
    insurance: float = 0.0
    interest_mortgage: float = 0.0
    interest_other: float = 0.0
    legal_and_professional: float = 0.0
    office_expense: float = 0.0
    pension_profit_sharing: float = 0.0
    rent_vehicles_equipment: float = 0.0
    rent_other: float = 0.0
    repairs_maintenance: float = 0.0
    supplies: float = 0.0
    taxes_licenses: float = 0.0
    travel: float = 0.0
    meals: float = 0.0  # 50% deductible
    utilities: float = 0.0
    wages: float = 0.0
    other_expenses: float = 0.0
    other_expenses_description: str = ""

    @property
    def total(self) -> float:
        """Total deductible expenses. Meals at 50% per IRC §274(n)."""
        return (
            self.advertising + self.car_and_truck + self.commissions_and_fees
            + self.contract_labor + self.depreciation
            + self.employee_benefit_programs + self.insurance
            + self.interest_mortgage + self.interest_other
            + self.legal_and_professional + self.office_expense
            + self.pension_profit_sharing + self.rent_vehicles_equipment
            + self.rent_other + self.repairs_maintenance + self.supplies
            + self.taxes_licenses + self.travel + (self.meals * 0.50)
            + self.utilities + self.wages + self.other_expenses
        )


@dataclass
class HomeOffice:
    """Home office deduction data (Form 8829 or simplified method)"""
    use_simplified_method: bool = True
    # Simplified method
    square_footage: float = 0.0  # Max 300 sq ft for simplified
    months_used: int = 12
    # Regular method
    total_home_sqft: float = 0.0
    office_sqft: float = 0.0
    rent: float = 0.0
    utilities: float = 0.0
    insurance: float = 0.0
    repairs: float = 0.0
    internet: float = 0.0
    internet_business_pct: float = 0.0  # Stored as decimal (0.0 to 1.0)
    mortgage_interest: float = 0.0    # From Form 1098 or direct entry
    real_estate_taxes: float = 0.0    # Annual property taxes

    def __post_init__(self):
        # Bug 9 fix: normalize >1 values to decimal
        if self.internet_business_pct > 1:
            self.internet_business_pct = self.internet_business_pct / 100.0

    @property
    def simplified_deduction(self) -> float:
        sqft = min(self.square_footage, 300)
        return sqft * 5.0 * (self.months_used / 12.0)

    @property
    def business_percentage(self) -> float:
        if self.total_home_sqft == 0:
            return 0.0
        return self.office_sqft / self.total_home_sqft

    @property
    def regular_deduction(self) -> float:
        """Regular method home office deduction (Form 8829).
        Business percentage of rent, utilities, insurance, repairs,
        plus business portion of internet."""
        pct = self.business_percentage
        direct = (
            self.rent * pct
            + self.utilities * pct
            + self.insurance * pct
            + self.repairs * pct
            + self.mortgage_interest * pct
            + self.real_estate_taxes * pct
        )
        # Bug 9 fix: internet_business_pct is always decimal after __post_init__
        internet_deduction = self.internet * self.internet_business_pct
        return (direct + internet_deduction) * (self.months_used / 12.0)


# --- Schedule C ---

@dataclass
class ScheduleCData:
    """All data for one Schedule C (one business)"""
    business_name: str = ""
    business_ein: str = ""
    business_type: BusinessType = BusinessType.SINGLE_MEMBER_LLC
    principal_business_code: str = ""  # NAICS code
    business_description: str = ""
    accounting_method: AccountingMethod = AccountingMethod.CASH
    did_materially_participate: bool = True
    started_in_current_year: bool = False

    # Income
    gross_receipts: float = 0.0
    returns_and_allowances: float = 0.0
    cost_of_goods_sold: float = 0.0
    other_income: float = 0.0

    # Expenses
    expenses: BusinessExpenses = field(default_factory=BusinessExpenses)
    home_office: Optional[HomeOffice] = None

    def __post_init__(self):
        if self.business_ein:
            self.business_ein = validate_ein(self.business_ein, "business_ein")
        validate_non_negative(self.gross_receipts, "gross_receipts")
        validate_non_negative(self.returns_and_allowances, "returns_and_allowances")
        validate_non_negative(self.cost_of_goods_sold, "cost_of_goods_sold")

    @property
    def gross_income(self) -> float:
        return self.gross_receipts - self.returns_and_allowances

    @property
    def gross_profit(self) -> float:
        return self.gross_income - self.cost_of_goods_sold

    @property
    def total_expenses(self) -> float:
        total = self.expenses.total
        if self.home_office:
            if self.home_office.use_simplified_method:
                total += self.home_office.simplified_deduction
            else:
                total += self.home_office.regular_deduction
        return total

    @property
    def net_profit(self) -> float:
        return self.gross_profit + self.other_income - self.total_expenses


# --- Master Taxpayer Profile ---

@dataclass
class TaxpayerProfile:
    """Complete taxpayer profile for the year"""
    # Personal info
    first_name: str = ""
    last_name: str = ""
    ssn: str = ""
    date_of_birth: str = ""
    occupation: str = ""
    phone: str = ""
    email: str = ""

    # Address
    street_address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "Mexico"
    foreign_address: bool = True

    # Filing
    filing_status: FilingStatus = FilingStatus.MFS
    spouse_name: str = ""
    spouse_ssn: str = ""  # ITIN if applicable
    tax_year: int = 2025

    # Spouse info (for MFS)
    spouse_is_nra: bool = True
    treat_spouse_as_resident: bool = False

    # Income documents
    forms_w2: list[FormW2] = field(default_factory=list)
    forms_1098: list[Form1098] = field(default_factory=list)
    forms_1099_nec: list[Form1099NEC] = field(default_factory=list)
    forms_1099_int: list[Form1099INT] = field(default_factory=list)
    forms_1099_div: list[Form1099DIV] = field(default_factory=list)
    forms_1099_b: list[Form1099B] = field(default_factory=list)
    schedule_k1s: list[ScheduleK1] = field(default_factory=list)

    # Dependents
    dependents: list[Dependent] = field(default_factory=list)

    # Businesses (Schedule C)
    businesses: list[ScheduleCData] = field(default_factory=list)

    # Payments & insurance
    estimated_payments: list[EstimatedPayment] = field(default_factory=list)
    health_insurance: Optional[HealthInsurance] = None

    # Foreign
    days_in_us_2025: int = 0
    days_in_foreign_country_2025: int = 0
    foreign_country: str = "Mexico"
    foreign_tax_paid: float = 0.0  # Should be 0 per user

    # Prior year (for quarterly estimated payment safe harbor)
    prior_year_tax: float = 0.0

    # State
    has_colorado_filing_obligation: bool = False  # Evaluate based on rental property
    co_tabor_refund: float = 0.0
    co_pension_income: float = 0.0
    taxpayer_age: int = 0
    uses_itemized_deductions: bool = False
    state_local_tax_deduction: float = 0.0

    def __post_init__(self):
        if self.ssn:
            self.ssn = validate_tin(self.ssn, "ssn")
        if self.spouse_ssn:
            self.spouse_ssn = validate_tin(self.spouse_ssn, "spouse_ssn")

    @property
    def total_estimated_payments(self) -> float:
        return sum(p.amount for p in self.estimated_payments)
