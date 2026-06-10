"""Field mapping for Schedule D (Capital Gains and Losses).

Field names discovered via widget-position dump against the 2025 IRS PDF
(irs.gov/pub/irs-pdf/f1040sd.pdf, Created 10/6/25).

Page 1 — Part I (short-term) / Part II (long-term), columns
(d)=proceeds, (e)=cost, (g)=adjustments, (h)=gain/loss:
  c1_1[0/1]=QOF Yes/No
  1a: f1_3 (d), f1_4 (e), f1_6 (h)       [column (g) not used on 1a]
  5:  f1_20 (K-1 short-term)             7:  f1_22 (net short-term)
  8a: f1_23 (d), f1_24 (e), f1_26 (h)
  11: f1_39 (Section 1231 via Form 4797) 12: f1_40 (K-1 long-term)
  13: f1_41 (capital gain distributions) 15: f1_43 (net long-term)
Page 2 — Part III:
  16: f2_1   17: c2_1[0/1] Yes/No   18: f2_2   19: f2_3
  20: c2_2[0/1] Yes/No   21: f2_4 (loss, pre-parenthesized)
  22: c2_3[0/1] Yes/No

NOTE: 1099-B totals are reported directly on lines 1a/8a, which is
only valid for covered transactions with basis reported to the IRS
and no adjustments. Form 8949 generation is not implemented.
"""

from taxman.calculator import CAPITAL_LOSS_LIMITS
from taxman.constants import CAPITAL_LOSS_LIMIT_OTHER
from taxman.field_mappings.common import format_currency_for_pdf, format_ssn


def build_schedule_d_data(sd_result, profile=None, result=None) -> dict:
    """Build field data dict for Schedule D.

    Args:
        sd_result: ScheduleDResult from calculator
        profile: TaxpayerProfile
        result: Form1040Result (for qualified dividends on line 22)
    """
    data = {}

    if profile:
        data["f1_1[0]"] = f"{profile.first_name} {profile.last_name}"
        data["f1_2[0]"] = format_ssn(profile.ssn) if profile.ssn else ""

    # QOF disposition question — engine does not model QOF investments
    data["c1_1[1]"] = True  # No

    # ── Part I: Short-Term ──
    st_proceeds = st_basis = 0.0
    lt_proceeds = lt_basis = 0.0
    if profile:
        st_proceeds = sum(b.st_proceeds for b in profile.forms_1099_b)
        st_basis = sum(b.st_cost_basis for b in profile.forms_1099_b)
        lt_proceeds = sum(b.lt_proceeds for b in profile.forms_1099_b)
        lt_basis = sum(b.lt_cost_basis for b in profile.forms_1099_b)

    # Line 1a: covered short-term transactions (basis reported, no
    # adjustments) reported in aggregate
    if st_proceeds or st_basis:
        data["f1_3[0]"] = format_currency_for_pdf(st_proceeds)
        data["f1_4[0]"] = format_currency_for_pdf(st_basis)
        data["f1_6[0]"] = format_currency_for_pdf(st_proceeds - st_basis)

    # Line 5: Net short-term gain/loss from K-1s (Box 8)
    k1_st = sum(
        k1.net_short_term_capital_gain for k1 in profile.schedule_k1s
    ) if profile else 0.0
    if k1_st != 0:
        data["f1_20[0]"] = format_currency_for_pdf(k1_st)

    # Line 7: Net short-term capital gain or (loss)
    if sd_result.net_st_gain_loss != 0:
        data["f1_22[0]"] = format_currency_for_pdf(sd_result.net_st_gain_loss)

    # ── Part II: Long-Term ──
    # Line 8a: covered long-term transactions in aggregate
    if lt_proceeds or lt_basis:
        data["f1_23[0]"] = format_currency_for_pdf(lt_proceeds)
        data["f1_24[0]"] = format_currency_for_pdf(lt_basis)
        data["f1_26[0]"] = format_currency_for_pdf(lt_proceeds - lt_basis)

    # Line 11: Section 1231 gain (K-1 Box 10, normally via Form 4797)
    k1_1231 = sum(
        k1.net_section_1231_gain for k1 in profile.schedule_k1s
    ) if profile else 0.0
    if k1_1231 != 0:
        data["f1_39[0]"] = format_currency_for_pdf(k1_1231)

    # Line 12: Net long-term gain/loss from K-1s (Box 9a)
    k1_lt = sum(
        k1.net_long_term_capital_gain for k1 in profile.schedule_k1s
    ) if profile else 0.0
    if k1_lt != 0:
        data["f1_40[0]"] = format_currency_for_pdf(k1_lt)

    # Line 13: Capital gain distributions (1099-DIV Box 2a)
    cap_gain_dist = sum(
        d.capital_gain_distributions for d in profile.forms_1099_div
    ) if profile else 0.0
    if cap_gain_dist > 0:
        data["f1_41[0]"] = format_currency_for_pdf(cap_gain_dist)

    # Line 15: Net long-term capital gain or (loss)
    if sd_result.net_lt_gain_loss != 0:
        data["f1_43[0]"] = format_currency_for_pdf(sd_result.net_lt_gain_loss)

    # ── Part III: Summary ──
    # Line 16: Combine lines 7 and 15
    net = sd_result.net_capital_gain_loss
    data["f2_1[0]"] = format_currency_for_pdf(net)

    qualified_dividends = result.qualified_dividends if result else 0.0

    if net > 0:
        # Line 17: Are lines 15 and 16 both gains?
        both_gains = sd_result.net_lt_gain_loss > 0
        data["c2_1[0]" if both_gains else "c2_1[1]"] = True
        if both_gains:
            # Lines 18/19 are zero (no 28%-rate or unrecaptured 1250
            # gain modeled) → Line 20 Yes → QDCG worksheet
            data["c2_2[0]"] = True
    elif net < 0:
        # Line 21: smaller of the loss or the filing-status limit
        # (pre-parenthesized field — enter positive)
        loss_limit = CAPITAL_LOSS_LIMIT_OTHER
        if profile:
            loss_limit = CAPITAL_LOSS_LIMITS.get(
                profile.filing_status, CAPITAL_LOSS_LIMIT_OTHER
            )
        data["f2_4[0]"] = format_currency_for_pdf(min(abs(net), loss_limit))
        # Line 22: qualified dividends on Form 1040 line 3a?
        data["c2_3[0]" if qualified_dividends > 0 else "c2_3[1]"] = True
    else:
        # net == 0 → Line 22
        data["c2_3[0]" if qualified_dividends > 0 else "c2_3[1]"] = True

    return data
