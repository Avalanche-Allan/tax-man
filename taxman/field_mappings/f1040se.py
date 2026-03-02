"""Field mapping for Schedule E (Supplemental Income and Loss).

Field names discovered via diagnostic fill against 2025 IRS PDF
(irs.gov/pub/irs-pdf/f1040se.pdf, Created 5/6/25).

Page 1 (Part I: Rental properties):
  f1_1=Name, f1_2=SSN
  Property addresses: f1_3=A, f1_4=B, f1_5=C
  Property type: (dropdown fields near 1b)
  Fair Rental Days: A=f1_9, B=f1_11, C=f1_13
  Personal Use Days: A=f1_10, B=f1_12, C=f1_14
  Income Lines 3-4, Expense Lines 5-19, Totals Lines 20-26
  Each line has 3 columns (A, B, C) — field numbers increment across columns.

Page 2 (Part II: Partnerships, Part III: Estates, Part V: Summary):
  f2_1=Name, f2_2=SSN
  28 rows A-D: f2_3/f2_5=A name/EIN, f2_6/f2_8=B, f2_9/f2_11=C, f2_12/f2_14=D
  Passive/Nonpassive per row: g/h/i/j/k columns
  Line 30: f2_45, Line 31: f2_46, Line 32: f2_47
  Line 41: f2_78 (total Schedule E income)
"""

from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


# Map property_type string to IRS numeric code for the Type of Property field
_PROPERTY_TYPE_CODE = {
    "single_family": "1",
    "multi_family": "2",
    "vacation": "3",
    "commercial": "4",
    "land": "5",
    "royalties": "6",
    "self_rental": "7",
    "other": "8",
}


def build_schedule_e_data(se_result, profile=None) -> dict:
    """Build field data dict for Schedule E.

    Args:
        se_result: ScheduleEResult from calculator
        profile: TaxpayerProfile
    """
    data = {}

    # ── Page 1 Header ──
    if profile:
        data["f1_1[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_2[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

    # ── Page 1: Part I — Rental Properties (up to 3) ──
    # Property address fields
    addr_fields = ["f1_3[0]", "f1_4[0]", "f1_5[0]"]
    # Fair rental / personal use days
    days_fields = [
        ("f1_9[0]", "f1_10[0]"),   # A: fair rental, personal use
        ("f1_11[0]", "f1_12[0]"),  # B
        ("f1_13[0]", "f1_14[0]"),  # C
    ]
    # Income: Line 3 (rents), Line 4 (royalties)
    rent_fields = ["f1_16[0]", "f1_17[0]", "f1_18[0]"]
    # Expense fields: Lines 5-18 (3 columns each)
    expense_map = [
        # (attr_name, field_A, field_B, field_C)
        ("advertising",          "f1_22[0]", "f1_23[0]", "f1_24[0]"),  # Line 5
        ("auto_travel",          "f1_25[0]", "f1_26[0]", "f1_27[0]"),  # Line 6
        ("cleaning_maintenance", "f1_28[0]", "f1_29[0]", "f1_30[0]"),  # Line 7
        ("commissions",          "f1_31[0]", "f1_32[0]", "f1_33[0]"),  # Line 8
        ("insurance",            "f1_34[0]", "f1_35[0]", "f1_36[0]"),  # Line 9
        ("legal_professional",   "f1_37[0]", "f1_38[0]", "f1_39[0]"),  # Line 10
        ("management_fees",      "f1_40[0]", "f1_41[0]", "f1_42[0]"),  # Line 11
        ("mortgage_interest",    "f1_43[0]", "f1_44[0]", "f1_45[0]"),  # Line 12
        ("other_interest",       "f1_46[0]", "f1_47[0]", "f1_48[0]"),  # Line 13
        ("repairs",              "f1_49[0]", "f1_50[0]", "f1_51[0]"),  # Line 14
        ("supplies",             "f1_52[0]", "f1_53[0]", "f1_54[0]"),  # Line 15
        ("taxes",                "f1_55[0]", "f1_56[0]", "f1_57[0]"),  # Line 16
        ("utilities",            "f1_58[0]", "f1_59[0]", "f1_60[0]"),  # Line 17
        ("depreciation",         "f1_61[0]", "f1_62[0]", "f1_63[0]"),  # Line 18
    ]
    # Line 19 other expenses: f1_65[0], f1_66[0], f1_67[0] (f1_64[0] is description)
    other_exp_fields = ["f1_65[0]", "f1_66[0]", "f1_67[0]"]
    # Line 20 total expenses
    total_exp_fields = ["f1_68[0]", "f1_69[0]", "f1_70[0]"]
    # Line 21 net (rents - expenses)
    net_fields = ["f1_71[0]", "f1_72[0]", "f1_73[0]"]
    # Line 22 deductible loss after limitation
    loss_fields = ["f1_74[0]", "f1_75[0]", "f1_76[0]"]

    # Aggregated totals for Lines 23a-26
    total_rents = 0.0
    total_mortgage = 0.0
    total_depreciation = 0.0
    total_expenses_all = 0.0
    total_income = 0.0
    total_loss = 0.0
    is_mfs = False
    if profile:
        from taxman.models import FilingStatus
        is_mfs = profile.filing_status == FilingStatus.MFS

    if profile:
        for i, prop in enumerate(profile.schedule_e_properties[:3]):
            # Property address
            data[addr_fields[i]] = prop.property_address

            # Property type code
            type_code = _PROPERTY_TYPE_CODE.get(prop.property_type, "1")
            # Type fields are near the address — they're small fields labeled "f" in diagnostic
            # We skip these as they may be dropdowns not easily fillable

            # Fair rental / personal use days
            fair_f, personal_f = days_fields[i]
            data[fair_f] = str(prop.days_rented)
            data[personal_f] = str(prop.days_personal)

            # Line 3: Rents received
            if prop.gross_rents > 0:
                data[rent_fields[i]] = format_currency_for_pdf(prop.gross_rents)
                total_rents += prop.gross_rents

            # Lines 5-18: Individual expense lines
            for attr, fa, fb, fc in expense_map:
                val = getattr(prop, attr, 0) or 0
                field = [fa, fb, fc][i]
                if val > 0:
                    data[field] = format_currency_for_pdf(val)

            # Line 19: Other expenses (pmi + other_expenses)
            other = (prop.pmi or 0) + (prop.other_expenses or 0)
            if other > 0:
                data[other_exp_fields[i]] = format_currency_for_pdf(other)

            # Line 20: Total expenses
            total_exp = prop.total_expenses
            if total_exp > 0:
                data[total_exp_fields[i]] = format_currency_for_pdf(total_exp)
                total_expenses_all += total_exp

            # Track mortgage interest and depreciation for Lines 23c/23d
            total_mortgage += prop.mortgage_interest or 0
            total_depreciation += prop.depreciation or 0

            # Line 21: Net income (rents - expenses)
            net = prop.net_income
            data[net_fields[i]] = format_currency_for_pdf(net)

            # Line 22: Deductible loss after limitation
            if net < 0:
                if is_mfs:
                    # MFS: $0 passive loss allowance — loss fully suspended
                    data[loss_fields[i]] = format_currency_for_pdf(0)
                else:
                    # Non-MFS: up to $25K allowance (simplified — full 8582 not modeled)
                    data[loss_fields[i]] = format_currency_for_pdf(net)
                    total_loss += net
            else:
                total_income += net

    # Lines 23a-23e: Aggregate totals
    if total_rents > 0:
        data["f1_77[0]"] = format_currency_for_pdf(total_rents)       # 23a
    if total_mortgage > 0:
        data["f1_79[0]"] = format_currency_for_pdf(total_mortgage)     # 23c
    if total_depreciation > 0:
        data["f1_80[0]"] = format_currency_for_pdf(total_depreciation) # 23d
    if total_expenses_all > 0:
        data["f1_81[0]"] = format_currency_for_pdf(total_expenses_all) # 23e

    # Line 24: Income (positive amounts from line 21)
    if total_income > 0:
        data["f1_82[0]"] = format_currency_for_pdf(total_income)
    # Line 25: Losses
    if total_loss < 0:
        data["f1_83[0]"] = format_currency_for_pdf(abs(total_loss))

    # Line 26: Total rental real estate and royalty income or loss
    rental_total = total_income + total_loss
    data["f1_84[0]"] = format_currency_for_pdf(rental_total)

    # ── Page 2 Header ──
    if profile:
        data["f2_1[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f2_2[0]"] = profile.ssn.replace("-", "") if profile.ssn else ""

    # ── Page 2: Part II — Partnerships and S Corps (up to 4 rows) ──
    # Row fields: (name, EIN) per row A-D
    k1_name_fields = ["f2_3[0]", "f2_6[0]", "f2_9[0]", "f2_12[0]"]
    k1_ein_fields = ["f2_5[0]", "f2_8[0]", "f2_11[0]", "f2_14[0]"]
    # Income columns per row: (g) passive loss, (h) passive income,
    # (i) nonpassive loss, (j) Sec 179, (k) nonpassive income
    k1_passive_loss = ["f2_15[0]", "f2_20[0]", "f2_25[0]", "f2_30[0]"]
    k1_passive_inc = ["f2_16[0]", "f2_21[0]", "f2_26[0]", "f2_31[0]"]
    k1_nonpassive_loss = ["f2_17[0]", "f2_22[0]", "f2_27[0]", "f2_32[0]"]
    k1_sec179 = ["f2_18[0]", "f2_23[0]", "f2_28[0]", "f2_33[0]"]
    k1_nonpassive_inc = ["f2_19[0]", "f2_24[0]", "f2_29[0]", "f2_34[0]"]

    # Totals accumulators
    total_passive_inc = 0.0
    total_passive_loss = 0.0
    total_nonpassive_inc = 0.0
    total_nonpassive_loss = 0.0

    if profile:
        for i, k1 in enumerate(profile.schedule_k1s[:4]):
            data[k1_name_fields[i]] = k1.partnership_name
            if k1.partnership_ein:
                data[k1_ein_fields[i]] = k1.partnership_ein.replace("-", "")

            # Categorize K-1 income into passive vs nonpassive
            # Rental income (Box 2/3) is passive
            rental = k1.net_rental_income + k1.other_net_rental_income
            if rental > 0:
                data[k1_passive_inc[i]] = format_currency_for_pdf(rental)
                total_passive_inc += rental
            elif rental < 0:
                if is_mfs:
                    data[k1_passive_loss[i]] = format_currency_for_pdf(0)
                else:
                    data[k1_passive_loss[i]] = format_currency_for_pdf(rental)
                    total_passive_loss += rental

            # Ordinary business income (Box 1) + guaranteed payments (Box 4) = nonpassive
            nonpassive = (k1.ordinary_business_income + k1.guaranteed_payments
                          + k1.interest_income + k1.royalties
                          + k1.net_st_capital_gain + k1.capital_gains
                          + k1.net_section_1231_gain + k1.other_income)
            if nonpassive > 0:
                data[k1_nonpassive_inc[i]] = format_currency_for_pdf(nonpassive)
                total_nonpassive_inc += nonpassive
            elif nonpassive < 0:
                data[k1_nonpassive_loss[i]] = format_currency_for_pdf(nonpassive)
                total_nonpassive_loss += nonpassive

    # Line 29a totals (positive: passive income + nonpassive income)
    if total_passive_inc > 0:
        data["f2_36[0]"] = format_currency_for_pdf(total_passive_inc)
    if total_nonpassive_inc > 0:
        data["f2_39[0]"] = format_currency_for_pdf(total_nonpassive_inc)

    # Line 29b totals (losses)
    if total_passive_loss < 0:
        data["f2_40[0]"] = format_currency_for_pdf(total_passive_loss)
    if total_nonpassive_loss < 0:
        data["f2_41[0]"] = format_currency_for_pdf(total_nonpassive_loss)

    # Line 30: Add columns (h) and (k) of line 29a
    line30 = total_passive_inc + total_nonpassive_inc
    if line30 > 0:
        data["f2_45[0]"] = format_currency_for_pdf(line30)

    # Line 31: Add columns (g), (i), and (j) of line 29b
    line31 = total_passive_loss + total_nonpassive_loss
    if line31 < 0:
        data["f2_46[0]"] = format_currency_for_pdf(line31)

    # Line 32: Total partnership and S corporation income or loss
    line32 = line30 + line31
    data["f2_47[0]"] = format_currency_for_pdf(line32)

    # ── Part V: Summary ──
    # Line 41: Total income or loss (combines lines 26, 32, 37, 39, 40)
    data["f2_78[0]"] = format_currency_for_pdf(se_result.total_schedule_e_income)

    return data
