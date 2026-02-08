# Form 6251 Instructions (2025) - Alternative Minimum Tax (AMT) for Individuals
Source: https://www.irs.gov/instructions/i6251

---

## General Information

Form 6251 is used by individuals to determine whether they owe Alternative Minimum Tax (AMT). The AMT is a parallel tax system that limits certain tax benefits available under the regular tax code. Taxpayers must compute both their regular tax and AMT, and pay whichever is higher. The AMT ensures that taxpayers with higher economic incomes who benefit from certain deductions, exclusions, or credits pay at least a minimum amount of tax.

### Who Must File

File Form 6251 if any of the following apply:

- Your taxable income plus AMT adjustments and preferences exceed the AMT exemption amount for your filing status
- You claim any of the following: net operating loss deduction, investment interest expense from private activity bonds, qualified electric vehicle credit, alternative fuel vehicle refueling property credit, or credit for prior year minimum tax (Form 8801)
- The AMT computed on Form 6251 exceeds your regular tax (after nonrefundable credits)
- Form 6251 is required even if you do not owe AMT, if certain credits or deductions are claimed

> **Tip:** Many tax software programs compute Form 6251 automatically. However, taxpayers with ISOs exercised during the year, large state/local tax deductions, or private activity bond interest should review this form carefully.

---

## AMT Tax Rates (2025)

The AMT uses a two-bracket rate structure applied to the amount by which AMTI exceeds the exemption (the "taxable excess"):

| Rate | Applies To |
|---|---|
| **26%** | First $239,100 of taxable excess ($119,550 MFS) |
| **28%** | Taxable excess above $239,100 ($119,550 MFS) |

For married filing jointly (MFJ) and qualifying surviving spouse, the breakpoint between the 26% and 28% brackets is also $239,100.

> **Note:** If the taxpayer has qualified dividends or net long-term capital gains, a special Part III computation (lines 12-39) applies to tax those amounts at the preferential capital gains rates (0%/15%/20%) rather than the flat 26%/28% AMT rates. This prevents double-taxation of capital gains under both systems.

---

## AMT Exemption Amounts (2025)

The AMT exemption shields a portion of AMTI from the AMT. It is subtracted from AMTI before applying the AMT rates.

| Filing Status | Exemption Amount |
|---|---|
| Single / Head of Household | $88,100 |
| Married Filing Jointly / Qualifying Surviving Spouse | $137,000 |
| Married Filing Separately | $68,500 |

### Exemption Phase-Out

The AMT exemption phases out for higher-income taxpayers. The exemption is reduced by **25 cents** for every **$1** of AMTI above the phase-out threshold:

| Filing Status | Phase-Out Begins | Exemption Fully Eliminated |
|---|---|---|
| Single / HOH | $626,350 | $978,750 |
| Married Filing Jointly / QSS | $1,252,700 | $1,800,700 |
| Married Filing Separately | $626,350 | $900,350 |

**Formula:** Exemption reduction = (AMTI - phase-out threshold) x 25%

> **Example (MFJ):** If AMTI = $1,400,000, the reduction is ($1,400,000 - $1,252,700) x 0.25 = $36,825. The remaining exemption is $137,000 - $36,825 = $100,175.

---

## AMTI Computation Overview

Alternative Minimum Taxable Income (AMTI) is computed by starting with regular taxable income and adding back certain adjustments (Part I of Form 6251) and tax preference items (Part I, continued).

### Computation Flow

1. **Start:** Regular taxable income from Form 1040, line 15
2. **Add/Subtract:** AMT adjustments (lines 2a through 2t)
3. **Add:** Tax preference items (lines 3a through 3j)
4. **Result:** AMTI (line 4)
5. **Subtract:** AMT exemption (line 5), reduced by phase-out if applicable
6. **Result:** AMT taxable excess (line 6)
7. **Apply:** 26%/28% AMT rates (or Part III for capital gains)
8. **Result:** Tentative minimum tax (line 9 or line 39)
9. **Subtract:** Regular tax liability (after nonrefundable credits)
10. **Result:** AMT owed (line 11) -- the excess of tentative minimum tax over regular tax; if zero or negative, no AMT is owed

---

## Part I: AMT Adjustments (Lines 2a-2t)

Adjustments can increase or decrease AMTI relative to regular taxable income. These are items where the AMT rules differ from regular tax rules.

### Key Adjustments

**Line 2a -- State and Local Taxes (SALT):**
- The itemized deduction for state/local income taxes, sales taxes, real estate taxes, and personal property taxes must be added back to taxable income for AMT purposes
- Under the TCJA (and continued by OBBBA), the regular-tax SALT deduction is capped at $10,000 ($5,000 MFS); for 2025, the OBBBA raises this cap to $40,000 ($20,000 single/MFS) for taxpayers with AGI below the phase-out. Regardless of the cap, the entire SALT deduction claimed on Schedule A is added back for AMT
- This is typically the single largest AMT adjustment for most affected taxpayers

**Line 2b -- Tax Refund (if taxes deducted in prior year):**
- If you included a state/local tax refund in income on Form 1040 (because you deducted those taxes in a prior year), subtract that amount here, since the underlying deduction was already disallowed for AMT

**Line 2c -- Investment Interest Expense:**
- Refigure your investment interest deduction using AMT income and AMT-adjusted gains. The AMT may disallow a portion of the deduction allowed under regular tax

**Line 2d -- Depletion:**
- Refigure depletion using AMT cost depletion rules instead of percentage depletion

**Line 2e -- Net Operating Loss (NOL) Deduction:**
- The AMT NOL deduction may differ from the regular NOL deduction. Add back the regular NOL deduction and then subtract the AMT NOL deduction

**Line 2g -- Alternative Tax NOL Deduction:**
- Enter the AMT NOL deduction as a negative number (reduces AMTI)

**Line 2i -- Medical and Dental Expenses:**
- For AMT, the medical expense deduction floor is the same 7.5% of AGI as regular tax (post-TCJA). If there is no difference, enter zero. If your regular tax medical deduction was computed differently, adjust here

**Line 2l -- Depreciation of Assets Placed in Service After 1986:**
- Refigure depreciation using the AMT depreciation system (typically 150% declining balance for personal property instead of 200% DB under MACRS, and straight-line over 40 years for real property instead of 27.5/39 years)
- Do **not** include depreciation from passive activities here (use line 2m instead)

**Line 2m -- Passive Activities:**
- Refigure passive activity gains/losses using AMT amounts for income, deductions, and depreciation. The difference between the AMT and regular tax passive activity loss limitation is entered here

**Line 2n -- Loss Limitations:**
- Refigure at-risk and basis loss limitations using AMT amounts

**Line 2o -- Circulation Costs:**
- Circulation expenditures that were expensed for regular tax may need to be capitalized and amortized for AMT

**Line 2p -- Long-Term Contracts:**
- Refigure income from long-term contracts using the percentage-of-completion method for AMT if you used another method for regular tax

**Line 2q -- Mining Exploration and Development Costs:**
- Capitalize and amortize over 10 years for AMT instead of expensing

**Line 2s -- Enhanced Deduction for Seniors (OBBBA):**
- The $6,000 senior bonus deduction (for taxpayers born before January 2, 1961), reported on Schedule 1-A (Form 1040), line 37, is treated as a personal exemption that must be added back for AMT purposes under section 56(b)(5)(D)

**Line 2t -- Other Adjustments:**
- Catch-all for adjustments not covered by specific lines, including: research and experimental expenditures, certain installment sale adjustments, incentive stock option adjustments (reported via Schedule D), and other items

---

## Tax Preference Items (Lines 3a-3j)

Tax preference items are always **added** to taxable income (they only increase AMTI). These represent items that receive especially favorable treatment under regular tax law.

### Common Preference Items

**Line 3a -- Private Activity Bond Interest:**
- Interest income from specified private activity municipal bonds (issued after August 7, 1986) is tax-exempt for regular tax but must be included in AMTI
- This includes bonds for airports, housing, student loans, industrial development, etc.
- Exception: bonds issued in 2009-2010 and certain qualified 501(c)(3) bonds are excluded

**Line 3b -- Qualified Small Business Stock (Section 1202 Exclusion):**
- 7% of the excluded gain from the sale of QSBS is a preference item (applies to stock acquired before September 28, 2010; for stock acquired after that date, the exclusion is 100% and there is no AMT preference)

**Line 3d -- Accelerated Depreciation of Pre-1987 Property:**
- The excess of accelerated depreciation over straight-line for pre-1987 real property and leased personal property

**Line 3e -- Intangible Drilling Costs:**
- The excess of IDC expensed for regular tax over the amount that would have been deductible under a 10-year amortization, if that excess exceeds 65% of the net income from the property

**Line 3f -- Other Preferences:**
- Includes tax-exempt interest from certain private activity bonds, accelerated depreciation on certain leased property, and other items

### Incentive Stock Options (ISOs) -- Key AMT Trigger

**Line 2t (or applicable adjustment line):**
- When an employee exercises an ISO but does not sell the stock in the same year, the **bargain element** (fair market value at exercise minus the exercise price) is not taxable for regular tax purposes but must be included in AMTI
- This is one of the most common triggers of AMT for individual taxpayers
- If the stock is sold in a disqualifying disposition (same year as exercise), the bargain element is taxed as ordinary income for regular tax, and no AMT adjustment is needed
- If held beyond the year of exercise, the full spread at exercise is an AMT adjustment, which can result in significant AMT liability

> **Planning Note:** Taxpayers who exercise ISOs should model the AMT impact before exercise. Strategies include exercising only enough shares to stay below the AMT threshold, or timing exercises in years with lower income.

---

## Part II: AMT Calculation (Lines 5-11)

| Line | Description |
|---|---|
| 4 | AMTI (sum of taxable income + adjustments + preferences) |
| 5 | AMT exemption amount (by filing status, reduced by phase-out) |
| 6 | AMT taxable excess (line 4 minus line 5, but not less than zero) |
| 7 | AMT at 26%/28% rates (or use Part III if capital gains apply) |
| 8 | AMT foreign tax credit |
| 9 | Tentative minimum tax (line 7 minus line 8) |
| 10 | Regular tax after nonrefundable credits (from Form 1040) |
| 11 | **AMT owed** (line 9 minus line 10; if zero or negative, no AMT) |

> **Key Point:** You owe AMT only if the tentative minimum tax (line 9) exceeds your regular tax (line 10). The AMT is the difference.

---

## Part III: Capital Gains Rate Computation (Lines 12-39)

If the taxpayer has qualified dividends or net capital gains, Part III applies preferential capital gains rates to those amounts even within the AMT system. This prevents qualified dividends and long-term capital gains from being taxed at the full 26%/28% AMT rates.

- Lines 12-39 replicate the qualified dividends / capital gains worksheet logic, but using AMT taxable excess as the base
- The maximum rates of 0%, 15%, and 20% apply to the capital gains portion
- The 26%/28% AMT rates apply only to the non-capital-gains portion of AMT taxable excess
- The 3.8% Net Investment Income Tax (Form 8960) is computed separately and is not part of the AMT calculation

---

## AMT Foreign Tax Credit (Line 8)

- Taxpayers who claim a foreign tax credit on their regular return must recompute the credit for AMT purposes
- Use Form 1116 refigured for AMT to determine the AMT foreign tax credit
- For 2025, there is **no AMT foreign tax credit carryback or carryforward** allowed

---

## Minimum Tax Credit -- Form 8801

If you paid AMT in a prior year, you may be eligible for a **Minimum Tax Credit (MTC)** in the current year, claimed on Form 8801 (Credit for Prior Year Minimum Tax -- Individuals, Estates, and Trusts).

### How the Credit Works

- The AMT is caused by two types of items: **deferral items** and **exclusion items**
- **Deferral items** (e.g., depreciation differences, ISO exercises, passive activity adjustments) create timing differences that reverse in future years. AMT paid because of deferral items generates a credit that can be used in future years to reduce regular tax
- **Exclusion items** (e.g., state/local tax deduction, standard deduction, private activity bond interest) cause permanent differences. AMT paid because of exclusion items does **not** generate a credit
- The MTC can reduce regular tax in a future year to no lower than the tentative minimum tax for that year
- Unused MTC carries forward indefinitely

### Form 8801 Workflow

1. Determine the prior year's AMT attributable to deferral items (Part I of Form 8801)
2. Calculate the current year's regular tax minus the current year's tentative minimum tax (Part II)
3. The MTC allowed is the lesser of the credit available and the excess computed in step 2
4. Any unused credit carries forward to the next year

> **Example:** A taxpayer paid $15,000 AMT in 2024 due to ISO exercise (deferral item). In 2025, their regular tax exceeds their tentative minimum tax by $10,000. They can use $10,000 of MTC to reduce their 2025 tax, with $5,000 carrying forward to 2026.

---

## OBBBA (One Big Beautiful Bill Act) Changes Affecting AMT

The One Big Beautiful Bill Act (OBBBA), signed into law in 2025, makes several changes that affect the AMT both for 2025 and future years.

### 2025 Impacts

- **SALT Cap Increase:** The regular-tax SALT deduction cap is increased to $40,000 ($20,000 for single filers and MFS), up from $10,000. However, because the entire SALT deduction is added back for AMT, a higher SALT deduction on the regular return creates a larger AMT adjustment, potentially increasing AMT exposure
- **SALT Cap Phase-Out:** The $40,000 cap phases out for higher-income taxpayers (AGI above $400,000 single / $800,000 MFJ), reducing back toward $10,000. This interaction reduces the AMT impact for the highest earners but can create a "middle zone" where AMT is more likely
- **Senior Bonus Deduction ($6,000):** The enhanced deduction for seniors (age 65+) is treated as a personal exemption and must be added back for AMT purposes (line 2s)
- **Permanent AMT Exemption Amounts:** The OBBBA makes the higher AMT exemption amounts (originally from TCJA) permanent and indexed for inflation, providing long-term certainty

### 2026 and Beyond

- **Phase-Out Threshold Reduction:** Starting in 2026, the AMT exemption phase-out thresholds revert to the pre-TCJA base of $500,000 (single) / $1,000,000 (MFJ), adjusted for inflation from 2018 -- significantly lower than the 2025 thresholds
- **Phase-Out Rate Doubles:** The exemption phase-out rate increases from **25%** to **50%** starting in 2026. For every $1 of AMTI above the threshold, the exemption is reduced by $0.50 (instead of $0.25). This means the exemption is eliminated at a much lower income level
- **Net Effect:** While low-to-moderate income taxpayers remain protected by the permanent high exemption amounts, the faster phase-out and lower thresholds will pull significantly more high-income taxpayers into the AMT starting in 2026

> **Planning Note for 2025:** Taxpayers with large ISO exercises or significant SALT deductions should model their AMT exposure carefully. The OBBBA's higher SALT cap may increase regular-tax savings but simultaneously increase the AMT adjustment amount. Consider timing ISO exercises and deduction strategies with the 2026 AMT rule changes in mind.

---

## Quick Reference Summary

| Parameter | Single/HOH | MFJ/QSS | MFS |
|---|---|---|---|
| Exemption Amount | $88,100 | $137,000 | $68,500 |
| Phase-Out Begins | $626,350 | $1,252,700 | $626,350 |
| Exemption Fully Eliminated | $978,750 | $1,800,700 | $900,350 |
| 26% Rate Applies To | First $239,100 | First $239,100 | First $119,550 |
| 28% Rate Applies Above | $239,100 | $239,100 | $119,550 |

---

## Related Forms and Schedules

| Form | Purpose |
|---|---|
| Form 6251 | Compute AMT for individuals |
| Form 8801 | Minimum tax credit for prior year AMT (deferral items) |
| Form 1116 | Foreign tax credit (refigured for AMT on line 8) |
| Schedule D | Capital gains/losses (refigured for AMT in Part III) |
| Form 8960 | Net investment income tax (3.8% surtax, computed separately) |
| Schedule A | Itemized deductions (SALT add-back is key AMT adjustment) |
