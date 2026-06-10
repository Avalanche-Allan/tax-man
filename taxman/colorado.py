"""Colorado state income tax calculation — Form 104.

Colorado has a flat income tax rate. Nonresidents owe Colorado tax
only on income sourced to Colorado (apportionment).

For this profile: CO-source income comes from K-1 rental property
located in Denver.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from taxman.calculator import Form1040Result, LineItem
from taxman.constants import (
    CO_PENSION_SUBTRACTION_55_64,
    CO_PENSION_SUBTRACTION_65_PLUS,
    CO_STANDARD_DEDUCTION,
    CO_TAX_RATE,
)
from taxman.models import FilingStatus, TaxpayerProfile


@dataclass
class ColoradoForm104Result:
    """Calculated Colorado Form 104."""
    federal_taxable_income: float = 0.0
    co_additions: float = 0.0
    co_subtractions: float = 0.0
    co_taxable_income: float = 0.0
    co_source_income: float = 0.0
    # DR 0104PN lines 32/33: apportionment numerator and denominator
    federal_modified_agi: float = 0.0   # PN line 32
    co_modified_agi: float = 0.0        # PN line 33
    apportionment_pct: float = 0.0      # PN line 34 (CO AGI / federal AGI)
    co_tax_before_apportion: float = 0.0
    co_tax: float = 0.0
    is_nonresident: bool = True
    lines: list[LineItem] = field(default_factory=list)


_STATE_IN_ADDRESS = re.compile(r",\s*([A-Z]{2})\s+\d{5}")


def _property_state(address: str) -> str:
    """Extract the two-letter state from 'street, City, ST 12345'."""
    m = _STATE_IN_ADDRESS.search(address or "")
    return m.group(1) if m else ""


def calculate_co_source_income(profile: TaxpayerProfile) -> float:
    """Calculate Colorado-source income.

    For nonresidents, CO-source income includes:
    - Net rental income from directly owned CO real property
      (Schedule E Part I — property state detected from the address)
    - Rental income from CO property (K-1 Box 2 from CO partnerships)
    - Ordinary business income from CO partnerships
    - Guaranteed payments from CO partnerships
    - Any CO wages (unlikely for this profile)

    Note: For simplicity, we assume all K-1 income from CO partnerships
    is CO-source. The user should flag which K-1s are from CO.
    """
    co_source = 0.0

    # Direct rental properties located in Colorado
    is_mfs = profile.filing_status == FilingStatus.MFS
    for prop in profile.schedule_e_properties:
        if _property_state(prop.property_address) != "CO":
            continue
        net = prop.net_income
        if net < 0 and is_mfs:
            # Mirror the federal MFS passive-loss suspension
            net = 0.0
        co_source += net

    for k1 in profile.schedule_k1s:
        # Treat all K-1 income as CO-source if it's from a CO partnership
        # A more sophisticated approach would check the partnership's state
        co_source += k1.net_rental_income
        co_source += k1.ordinary_business_income
        co_source += k1.guaranteed_payments
        co_source += k1.interest_income

    return co_source


def calculate_colorado_104(
    federal_result: Form1040Result,
    profile: TaxpayerProfile,
    co_source_income: Optional[float] = None,
) -> ColoradoForm104Result:
    """Calculate Colorado Form 104 (Individual Income Tax Return).

    Colorado uses a flat rate applied to federal taxable income.
    Nonresidents apportion: CO tax = CO rate * federal taxable income
    * (CO source income / total income).

    Args:
        federal_result: Completed federal return
        profile: Taxpayer profile
        co_source_income: Override for CO-source income (auto-calculated if None)
    """
    result = ColoradoForm104Result()
    lines = []

    # Line 1: Federal taxable income
    result.federal_taxable_income = federal_result.taxable_income
    lines.append(LineItem("CO Form 104", "1",
                          "Federal taxable income",
                          federal_result.taxable_income,
                          "From federal Form 1040, Line 15"))

    # Additions: state/local tax deduction addback (itemizers only)
    co_additions = 0.0
    if profile.uses_itemized_deductions and profile.state_local_tax_deduction > 0:
        co_additions += profile.state_local_tax_deduction
        lines.append(LineItem("CO Form 104", "Add",
                              "State/local tax deduction addback",
                              profile.state_local_tax_deduction,
                              "SALT deducted on federal Schedule A added back for CO"))
    result.co_additions = co_additions

    # Subtractions
    co_subtractions = 0.0
    # TABOR refund
    if profile.co_tabor_refund > 0:
        co_subtractions += profile.co_tabor_refund
        lines.append(LineItem("CO Form 104", "Sub",
                              "TABOR refund subtraction",
                              profile.co_tabor_refund))
    # Pension/annuity subtraction (age-based)
    if profile.co_pension_income > 0 and profile.taxpayer_age >= 55:
        if profile.taxpayer_age >= 65:
            pension_limit = CO_PENSION_SUBTRACTION_65_PLUS
        else:
            pension_limit = CO_PENSION_SUBTRACTION_55_64
        pension_sub = min(profile.co_pension_income, pension_limit)
        co_subtractions += pension_sub
        lines.append(LineItem("CO Form 104", "Sub",
                              "Pension/annuity subtraction",
                              pension_sub,
                              f"Age {profile.taxpayer_age}: up to ${pension_limit:,}"))
    result.co_subtractions = co_subtractions

    # Colorado taxable income = federal taxable + additions - subtractions
    result.co_taxable_income = max(
        federal_result.taxable_income + result.co_additions - result.co_subtractions,
        0
    )
    lines.append(LineItem("CO Form 104", "4",
                          "Colorado taxable income",
                          result.co_taxable_income))

    # Tax at flat rate
    result.co_tax_before_apportion = round(
        result.co_taxable_income * CO_TAX_RATE, 2
    )
    lines.append(LineItem("CO Form 104", "5",
                          f"Colorado tax ({CO_TAX_RATE*100:.1f}%)",
                          result.co_tax_before_apportion,
                          f"${result.co_taxable_income:,.2f} × {CO_TAX_RATE}"))

    # Nonresident apportionment
    is_nonresident = profile.foreign_address or profile.state != "CO"
    result.is_nonresident = is_nonresident

    if is_nonresident:
        # Calculate CO-source income
        if co_source_income is not None:
            result.co_source_income = co_source_income
        else:
            result.co_source_income = calculate_co_source_income(profile)

        # DR 0104PN method (lines 32-34): apportionment percentage is
        # modified Colorado AGI / modified federal AGI. CO adjustments
        # are 0 here (SE income is not CO-source for this profile), so
        # CO modified AGI == CO-source income.
        result.federal_modified_agi = federal_result.agi
        result.co_modified_agi = result.co_source_income
        if result.federal_modified_agi > 0:
            result.apportionment_pct = min(
                max(result.co_modified_agi / result.federal_modified_agi, 0),
                1.0,
            )
        else:
            result.apportionment_pct = 0.0
        lines.append(LineItem("CO Form 104-PN", "33",
                              "Modified Colorado AGI",
                              round(result.co_modified_agi, 2),
                              "Income sourced to Colorado"))
        lines.append(LineItem("CO Form 104-PN", "34",
                              "Apportionment percentage",
                              round(result.apportionment_pct * 100, 4),
                              f"CO modified AGI / federal modified AGI: "
                              f"${result.co_modified_agi:,.2f} / "
                              f"${result.federal_modified_agi:,.2f}"))

        # Apportioned tax (PN line 36 → DR 0104 line 13)
        result.co_tax = round(
            result.co_tax_before_apportion * result.apportionment_pct, 2
        )
        lines.append(LineItem("CO Form 104", "13",
                              "Colorado tax (apportioned)",
                              result.co_tax,
                              f"${result.co_tax_before_apportion:,.2f} × "
                              f"{result.apportionment_pct:.4f}"))
    else:
        # Resident — full tax
        result.co_tax = result.co_tax_before_apportion
        result.apportionment_pct = 1.0
        lines.append(LineItem("CO Form 104", "7",
                              "Colorado tax",
                              result.co_tax))

    result.lines = lines
    return result


def calculate_full_return(
    profile: TaxpayerProfile,
) -> tuple[Form1040Result, Optional[ColoradoForm104Result]]:
    """Calculate federal return and Colorado if applicable.

    Returns:
        Tuple of (federal_result, colorado_result or None)
    """
    from taxman.calculator import calculate_return

    federal = calculate_return(profile)

    colorado = None
    if profile.has_colorado_filing_obligation:
        colorado = calculate_colorado_104(federal, profile)

    return federal, colorado
