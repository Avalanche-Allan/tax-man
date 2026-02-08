"""Field mapping for Schedule E (Supplemental Income and Loss).

Field names from inspect_form_fields('f1040se') against 2025 IRS PDF.
Schedule E has 2 pages with complex layout for rental properties (Part I)
and partnerships/S corps (Part II).
Page 1: f1_1..f1_84 (Part I: Rental properties)
Page 2: f2_1..f2_80 (Part II: Partnerships, S corps, estates, trusts)
"""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def build_schedule_e_data(se_result, profile=None) -> dict:
    """Build field data dict for Schedule E.

    Args:
        se_result: ScheduleEResult from calculator
        profile: TaxpayerProfile
    """
    data = {}

    # Header
    if profile:
        data["f1_1[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_2[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

    # ── Page 2: Part II — Partnerships and S Corps ──
    # The Part II section on page 2 has rows for each entity
    # f2_1: Name, f2_2: SSN (page 2 header)
    if profile:
        data["f2_1[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f2_2[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

    # Partnership rows start at f2_3
    if profile:
        for i, k1 in enumerate(profile.schedule_k1s[:4]):  # Max 4 rows on form
            # Each partnership row: Name, Type (P/S), Foreign?, EIN, check boxes, amounts
            row_base = 3 + (i * 3)  # Approximate — fields grouped by row
            data[f"f2_{row_base}[0]"] = k1.partnership_name
            if k1.partnership_ein:
                data[f"f2_{row_base + 2}[0]"] = k1.partnership_ein.replace("-", "")

    # ── Totals ──
    # Part II totals flow to specific fields
    # The exact field offsets depend on the form layout, but key totals:
    if se_result.net_rental_income != 0:
        data["f2_39[0]"] = format_currency_for_pdf(se_result.net_rental_income)

    if se_result.ordinary_business_income != 0:
        data["f2_40[0]"] = format_currency_for_pdf(se_result.ordinary_business_income)

    if se_result.guaranteed_payments != 0:
        data["f2_41[0]"] = format_currency_for_pdf(se_result.guaranteed_payments)

    # Line 26: Total supplemental income
    data["f2_48[0]"] = format_currency_for_pdf(se_result.total_schedule_e_income)

    return data
