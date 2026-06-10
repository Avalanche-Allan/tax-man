"""Roll a completed tax year's profile forward to the next year.

Keeps recurring structures as planning estimates; clears the
year-specific income documents that arrive fresh each January.
"""

import copy

from taxman.models import TaxpayerProfile


def rollover_profile(
    profile: TaxpayerProfile, prior_year_total_tax: float
) -> TaxpayerProfile:
    """Create next year's starting profile from a completed return.

    Kept (recurring structures / planning estimates):
    - Identity, address, filing status, spouse info
    - Businesses (Schedule C) with last year's amounts as estimates
    - Rental properties (depreciation schedule continues unchanged)
    - Health insurance, days-abroad pattern (FEIE planning)
    - nol_carryforward passes through unchanged — recompute manually
      if the completed year generated or consumed an NOL

    Cleared (year-specific documents, re-collected next filing season):
    - W-2s, 1098s, all 1099s, K-1s, estimated payment records

    Set:
    - tax_year bumped by one
    - prior_year_tax = the completed year's total tax (safe-harbor
      basis for next year's quarterly estimates)
    """
    new = copy.deepcopy(profile)
    new.tax_year = profile.tax_year + 1
    new.prior_year_tax = round(prior_year_total_tax, 2)

    new.forms_w2 = []
    new.forms_1098 = []
    new.forms_1099_nec = []
    new.forms_1099_int = []
    new.forms_1099_div = []
    new.forms_1099_b = []
    new.forms_1099_r = []
    new.schedule_k1s = []
    new.estimated_payments = []

    return new
