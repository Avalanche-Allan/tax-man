"""2025 Tax Year Constants, Brackets, and Thresholds.

Sources:
- IRS Revenue Procedure 2024-40 (inflation adjustments for 2025)
- One Big Beautiful Bill Act of 2025 (OBBBA, P.L. 119-21, signed July 4, 2025)
- IRC Title 26 sections cited inline
- IRS Publications 505, 535, Form 2555/7206/8959 Instructions

OBBBA made TCJA rates permanent and increased the standard deduction.
Bracket thresholds from Rev. Proc. 2024-40 remain unchanged by OBBBA.
"""

# =============================================================================
# TAX BRACKETS - Married Filing Separately (2025)
# Source: Rev. Proc. 2024-40, §3.01 (MFS = half of MFJ thresholds)
# OBBBA made these rates permanent (were set to sunset end of 2025).
# =============================================================================
# Format: (upper_bound, rate) — income up to upper_bound taxed at rate

MFS_BRACKETS = [
    (11_925, 0.10),
    (48_475, 0.12),
    (103_350, 0.22),
    (197_300, 0.24),
    (250_525, 0.32),
    (375_800, 0.35),
    (float('inf'), 0.37),
]

SINGLE_BRACKETS = [
    (11_925, 0.10),
    (48_475, 0.12),
    (103_350, 0.22),
    (197_300, 0.24),
    (250_525, 0.32),
    (626_350, 0.35),
    (float('inf'), 0.37),
]

# Head of Household brackets (2025)
# Source: Rev. Proc. 2024-40, §3.01 — HOH has its own bracket thresholds
HOH_BRACKETS = [
    (17_000, 0.10),
    (64_850, 0.12),
    (103_350, 0.22),
    (197_300, 0.24),
    (250_500, 0.32),
    (626_350, 0.35),
    (float('inf'), 0.37),
]

MFJ_BRACKETS = [
    (23_850, 0.10),
    (96_950, 0.12),
    (206_700, 0.22),
    (394_600, 0.24),
    (501_050, 0.32),
    (751_600, 0.35),
    (float('inf'), 0.37),
]


# =============================================================================
# STANDARD DEDUCTION (2025)
# Source: OBBBA §101 amended upward from Rev. Proc. 2024-40 amounts.
# Pre-OBBBA: Single/MFS $15,000; MFJ $30,000; HOH $22,500
# Post-OBBBA: Single/MFS $15,750; MFJ $31,500; HOH $23,625
# =============================================================================

STANDARD_DEDUCTION = {
    "single": 15_750,
    "mfj": 31_500,
    "mfs": 15_750,
    "hoh": 23_625,
    "qss": 31_500,
}

# Additional standard deduction for age 65+ or blind (per person)
ADDITIONAL_STD_DEDUCTION_MARRIED = 1_550
ADDITIONAL_STD_DEDUCTION_SINGLE = 2_000

# OBBBA senior bonus deduction ($6,000 for age 65+)
# NOTE: MFS filers are EXCLUDED from this deduction
SENIOR_BONUS_DEDUCTION = 6_000
SENIOR_BONUS_MFS_ELIGIBLE = False


# =============================================================================
# SELF-EMPLOYMENT TAX (2025) — IRC §1401, §1402
# =============================================================================

SE_TAX_RATE = 0.153  # 15.3% total (12.4% SS + 2.9% Medicare)
SS_TAX_RATE = 0.124  # Social Security portion
MEDICARE_TAX_RATE = 0.029  # Medicare portion

# Social Security wage base for 2025 (Source: SSA announcement)
SS_WAGE_BASE = 176_100
SS_MAX_TAX = 21_836.40  # 12.4% × $176,100

# Net SE income multiplier (92.35% of net SE earnings)
SE_INCOME_FACTOR = 0.9235

# Deductible portion of SE tax — 50% is above-the-line (IRC §164(f))
SE_DEDUCTIBLE_FRACTION = 0.50

# Minimum net SE income to trigger SE tax
SE_MINIMUM_INCOME = 400

# Additional Medicare Tax (IRC §1401(b)(2)) — Form 8959
ADDITIONAL_MEDICARE_THRESHOLD_MFS = 125_000  # Half of MFJ $250K
ADDITIONAL_MEDICARE_THRESHOLD_SINGLE = 200_000
ADDITIONAL_MEDICARE_THRESHOLD_MFJ = 250_000
ADDITIONAL_MEDICARE_RATE = 0.009  # 0.9%


# =============================================================================
# QUALIFIED BUSINESS INCOME (QBI) DEDUCTION — IRC §199A
# Source: Rev. Proc. 2024-40; OBBBA made §199A permanent (no sunset).
# =============================================================================

QBI_DEDUCTION_RATE = 0.20  # 20% of QBI

# Taxable income threshold where W-2 wage/SSTB limitations begin
QBI_THRESHOLD_MFS = 197_300
QBI_THRESHOLD_MFJ = 394_600
QBI_THRESHOLD_SINGLE = 197_300

# Phase-out range above threshold (for 2025; OBBBA increases to $75K in 2026+)
QBI_PHASEOUT_MFS = 50_000  # $197,300 to $247,300
QBI_PHASEOUT_MFJ = 100_000


# =============================================================================
# FOREIGN EARNED INCOME EXCLUSION — IRC §911, Form 2555
# Source: Rev. Proc. 2024-40, §3.35
# =============================================================================

FEIE_EXCLUSION_LIMIT = 130_000  # Maximum excludable foreign earned income
FEIE_HOUSING_BASE = 20_800  # 16% of exclusion limit
FEIE_HOUSING_MAX = 39_000  # 30% of exclusion limit (default; high-cost differs)

# Physical presence test: 330 full days in foreign country during
# any consecutive 12-month period
# CRITICAL: FEIE only excludes from income tax, NOT from SE tax.


# =============================================================================
# ESTIMATED TAX — IRC §6654
# Source: IRS Publication 505 (2025)
# =============================================================================

ESTIMATED_TAX_SAFE_HARBOR_PCT = 0.90  # 90% of current year
ESTIMATED_TAX_PRIOR_YEAR_PCT = 1.00  # 100% of prior year (AGI <= $75K MFS)
ESTIMATED_TAX_PRIOR_YEAR_HIGH_INCOME_PCT = 1.10  # 110% (AGI > $75K MFS)
ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFS = 75_000  # Half of MFJ $150K
ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_SINGLE = 150_000
ESTIMATED_TAX_HIGH_INCOME_THRESHOLD_MFJ = 150_000
ESTIMATED_TAX_DE_MINIMIS = 1_000  # No penalty if balance due < $1,000
UNDERPAYMENT_PENALTY_RATE = 0.07  # ~7% for 2025 (fed short-term + 3%)


# =============================================================================
# SALT DEDUCTION CAP — IRC §164(b)(6)
# Source: OBBBA raised from $10K/$5K to $40K/$20K
# =============================================================================

SALT_DEDUCTION_CAP_MFS = 20_000  # Up from $5,000 (pre-OBBBA)
SALT_DEDUCTION_CAP_OTHER = 40_000  # Up from $10,000
SALT_PHASEOUT_INCOME = 500_000  # Cap reduces above this AGI


# =============================================================================
# OTHER THRESHOLDS
# =============================================================================

# Net Investment Income Tax (IRC §1411)
NIIT_THRESHOLD_MFS = 125_000
NIIT_THRESHOLD_SINGLE = 200_000
NIIT_THRESHOLD_MFJ = 250_000
NIIT_RATE = 0.038  # 3.8%

# AMT exemption (IRC §55, Form 6251)
AMT_EXEMPTION_MFS = 68_500  # Half of MFJ $137,000
AMT_PHASEOUT_MFS = 609_350

# Capital loss deduction limit
CAPITAL_LOSS_LIMIT_MFS = 1_500  # Half of normal $3,000

# Self-employed health insurance: 100% deductible as adjustment to income
# (Schedule 1, Line 17 — NOT a business expense on Schedule C)
# Cannot exceed net SE income. Form 7206 required for calculation.
# Does NOT reduce SE tax base.

# Meals deduction: 50% of business meals (100% restaurant exception expired)
MEALS_DEDUCTION_PCT = 0.50

# Home office simplified method: $5/sqft, max 300 sqft = $1,500
HOME_OFFICE_SIMPLIFIED_RATE = 5.00
HOME_OFFICE_SIMPLIFIED_MAX_SQFT = 300

# Section 179 (OBBBA increased)
SECTION_179_LIMIT = 2_500_000  # Up from $1,220,000
SECTION_179_PHASEOUT_START = 4_000_000

# 100% bonus depreciation restored by OBBBA for property after Jan 20, 2025


# =============================================================================
# FILING DEADLINES (Tax Year 2025)
# =============================================================================

FILING_DEADLINE = "April 15, 2026"
EXTENSION_DEADLINE = "October 15, 2026"
ABROAD_AUTO_EXTENSION = "June 15, 2026"  # US citizens abroad get 2 months

Q1_ESTIMATED_DUE = "April 15, 2025"
Q2_ESTIMATED_DUE = "June 16, 2025"  # June 15 is Sunday
Q3_ESTIMATED_DUE = "September 15, 2025"
Q4_ESTIMATED_DUE = "January 15, 2026"


# =============================================================================
# COLORADO STATE TAX (Tax Year 2025)
# Source: CO Revised Statutes §39-22-104; CO Dept. of Revenue
# =============================================================================

CO_TAX_RATE = 0.044  # 4.4% flat rate for 2025
CO_STANDARD_DEDUCTION = {
    "single": 15_750,
    "mfj": 31_500,
    "mfs": 15_750,
    "hoh": 23_625,
    "qss": 31_500,
}
CO_FILING_DEADLINE = "April 15, 2026"
