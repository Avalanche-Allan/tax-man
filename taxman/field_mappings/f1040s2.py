"""Field mapping for Schedule 2 (Additional Taxes).

Field names discovered via widget-position dump against the 2025 IRS PDF
(irs.gov/pub/irs-pdf/f1040s2.pdf, Created 5/8/25).

Page 1:
  f1_01=Name, f1_02=SSN
  Part I: f1_12=2 (AMT), f1_13=3 (total Part I)
  Part II: f1_15=4 (SE tax), f1_19=8 (early distributions,
  c1_6=5329-not-required checkbox), f1_22=11 (Additional Medicare),
  f1_23=12 (NIIT)
Page 2:
  f2_24=21 (total other taxes → Form 1040 Line 23)
"""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def build_schedule_2_data(result, profile=None) -> dict:
    """Build field data dict for Schedule 2.

    Args:
        result: Form1040Result
        profile: TaxpayerProfile
    """
    data = {}

    if profile:
        data["f1_01[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_02[0]"] = format_ssn(profile.ssn) if profile.ssn else ""

    # ── Part I: Tax ──
    # Line 2: Alternative minimum tax (Form 6251)
    if result.amt > 0:
        data["f1_12[0]"] = format_currency_for_pdf(result.amt)
        # Line 3: Add lines 1z and 2 → Form 1040 Line 17
        data["f1_13[0]"] = format_currency_for_pdf(result.amt)

    # ── Part II: Other Taxes ──
    # Line 4: Self-employment tax (Schedule SE)
    if result.se_tax > 0:
        data["f1_15[0]"] = format_currency_for_pdf(result.se_tax)

    # Line 8: Additional tax on early distributions (10%).
    # Form 5329 is not required when the 10% additional tax applies
    # with no exception — check the "if not required" box.
    if result.early_withdrawal_penalty > 0:
        data["f1_19[0]"] = format_currency_for_pdf(
            result.early_withdrawal_penalty
        )
        data["c1_6[0]"] = True

    # Line 11: Additional Medicare Tax (Form 8959)
    if result.additional_medicare > 0:
        data["f1_22[0]"] = format_currency_for_pdf(result.additional_medicare)

    # Line 12: Net investment income tax (Form 8960)
    if result.niit > 0:
        data["f1_23[0]"] = format_currency_for_pdf(result.niit)

    # Line 21: Total other taxes → Form 1040 Line 23
    line21 = (result.se_tax + result.early_withdrawal_penalty
              + result.additional_medicare + result.niit)
    if line21 > 0:
        data["f2_24[0]"] = format_currency_for_pdf(round(line21, 2))

    return data
