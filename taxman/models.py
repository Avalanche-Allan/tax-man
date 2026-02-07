"""Data models for tax documents and form data."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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
    royalties: float = 0.0  # Box 7
    net_short_term_capital_gain: float = 0.0  # Box 8
    net_long_term_capital_gain: float = 0.0  # Box 9a
    net_section_1231_gain: float = 0.0  # Box 10
    other_income: float = 0.0  # Box 11
    section_179_deduction: float = 0.0  # Box 12
    other_deductions: float = 0.0  # Box 13
    self_employment_earnings: float = 0.0  # Box 14
    tax_year: int = 2025


@dataclass
class EstimatedPayment:
    """Quarterly estimated tax payment (Form 1040-ES)"""
    quarter: int = 0  # 1-4
    date_paid: str = ""
    amount: float = 0.0


@dataclass
class HealthInsurance:
    """Self-employed health insurance premiums"""
    provider: str = ""
    total_premiums: float = 0.0
    months_covered: int = 12


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
    internet_business_pct: float = 0.0

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
        )
        internet_deduction = self.internet * (self.internet_business_pct / 100.0
                                              if self.internet_business_pct > 1
                                              else self.internet_business_pct)
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
    forms_1099_nec: list[Form1099NEC] = field(default_factory=list)
    schedule_k1s: list[ScheduleK1] = field(default_factory=list)

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

    # State
    has_colorado_filing_obligation: bool = False  # Evaluate based on rental property

    @property
    def total_estimated_payments(self) -> float:
        return sum(p.amount for p in self.estimated_payments)
