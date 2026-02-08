# Child Tax Credit / Schedule 8812 (2025)

> **Reference document for Tax Man engine.**
> Sourced from IRS Schedule 8812 (Form 1040) instructions, IRS Publication 972, and OBBBA (P.L. 119-21) provisions.
> Applicable to tax year 2025 (returns filed in 2026).

---

## Overview

Schedule 8812 (Form 1040), "Credits for Qualifying Children and Other Dependents," is used to calculate three credits:

1. **Child Tax Credit (CTC)** -- up to **$2,500** per qualifying child (OBBBA increase from the prior $2,000).
2. **Additional Child Tax Credit (ACTC)** -- the refundable portion of the CTC for taxpayers whose CTC exceeds their tax liability.
3. **Credit for Other Dependents (ODC)** -- **$500** per qualifying dependent who does not qualify for the CTC.

---

## 1. OBBBA Changes for 2025

The One Big Beautiful Bill Act (P.L. 119-21, signed July 4, 2025) made the following changes to the Child Tax Credit:

| Item | Prior TCJA Law | OBBBA (2025) |
|------|---------------|--------------|
| Maximum CTC per qualifying child | $2,000 | **$2,500** |
| Phase-out threshold (MFJ) | $400,000 (temporary) | **$400,000 (permanent)** |
| Phase-out threshold (all other) | $200,000 (temporary) | **$200,000 (permanent)** |
| Refundable portion (ACTC) cap | $1,700 (2024) | **Up to $1,400 per child** |
| Inflation indexing | None | **Indexed beginning 2026** |
| SSN requirement for claimant | Not required | **Required (taxpayer or at least one spouse on joint return)** |

- The $2,500 amount applies for tax year 2025. For 2026 and beyond, the credit amount is indexed to inflation.
- The phase-out thresholds of $400,000 (MFJ) and $200,000 (other) are now **permanent** -- they were previously set to revert to $110,000/$75,000 after 2025.
- Personal exemptions remain eliminated (as under TCJA), with the increased CTC and standard deduction serving as replacements.

---

## 2. Qualifying Child for the CTC

A child must meet **all seven** of the following tests to be a "qualifying child" for the Child Tax Credit:

### Age Test
- The child must be **under age 17** (i.e., age 16 or younger) at the end of the tax year (December 31, 2025).

### Social Security Number (SSN) Test
- The child must have a valid **Social Security number** issued by the Social Security Administration **before the due date of the return** (including extensions).
- The SSN must be valid for employment (not an ITIN or ATIN).
- **New for 2025 (OBBBA):** The taxpayer claiming the credit (or at least one spouse on a joint return) must also have a valid SSN.

### Relationship Test
The child must be the taxpayer's:
- Son, daughter, stepchild, or eligible foster child; **or**
- Brother, sister, stepbrother, stepsister, half-brother, or half-sister; **or**
- A descendant of any of the above (e.g., grandchild, niece, nephew).

An adopted child is treated the same as a biological child. An eligible foster child is a child placed with the taxpayer by an authorized placement agency or by court order.

### Residency Test
- The child must have **lived with the taxpayer for more than half the tax year** (more than 6 months).
- Temporary absences for school, vacation, medical care, military service, or detention count as time lived with the taxpayer.
- A child born or died during the year is treated as having lived with the taxpayer for the entire year if the taxpayer's home was the child's home for the entire time the child was alive during the year.

### Support Test
- The child must **not have provided more than half of his or her own support** during the tax year.
- Support includes food, lodging, clothing, education, medical care, recreation, transportation, and similar necessities.

### Dependent Test
- The child must be **claimed as a dependent** on the taxpayer's return.
- The child cannot file a joint return for the year (unless filed only to claim a refund of withheld taxes or estimated tax paid).

### Citizenship Test
- The child must be a **U.S. citizen, U.S. national, or U.S. resident alien**.
- Children who are residents of Canada or Mexico do **not** qualify for the CTC (they may qualify for the ODC).

---

## 3. Phase-Out Calculation

The combined CTC and ODC begins to phase out when Modified Adjusted Gross Income (MAGI) exceeds the applicable threshold:

| Filing Status | Phase-Out Begins |
|---------------|-----------------|
| Married Filing Jointly (MFJ) | **$400,000** |
| All other filing statuses (Single, HOH, MFS, QSS) | **$200,000** |

**Phase-out rate:** The credit is reduced by **$50 for every $1,000** (or fraction thereof) of MAGI exceeding the threshold.

### Phase-Out Formula

```
Excess = MAGI - Threshold
Reduction = ceiling(Excess / 1,000) x $50
Net Credit = max(0, Total Credit - Reduction)
```

### Example

A married couple filing jointly with MAGI of $425,000 and two qualifying children:
- Total CTC = 2 x $2,500 = $5,000
- Excess = $425,000 - $400,000 = $25,000
- Reduction = ($25,000 / $1,000) x $50 = $1,250
- Net CTC = $5,000 - $1,250 = **$3,750**

### MAGI Definition for Schedule 8812

MAGI = Form 1040, Line 11 (AGI) **plus** any amounts excluded under:
- Form 2555 (Foreign Earned Income Exclusion)
- Form 4563 (Exclusion of Income for Residents of American Samoa)
- Excluded income from Puerto Rico

---

## 4. Refundable Portion -- Additional Child Tax Credit (ACTC)

If the CTC exceeds the taxpayer's income tax liability (after other nonrefundable credits), the excess may be refunded as the **Additional Child Tax Credit (ACTC)**, subject to limits.

### ACTC Calculation

The ACTC equals the **lesser** of:

1. The CTC amount that exceeds the tax liability (the "unused" CTC); **or**
2. **15%** of earned income exceeding **$2,500** (the earned income formula); **or**
3. The per-child refundable cap (**$1,400 per qualifying child** for 2025).

```
ACTC = min(Unused CTC, 15% x (Earned Income - $2,500), $1,400 x Number of Qualifying Children)
```

### Earned Income Threshold

- Earned income must exceed **$2,500** to qualify for any ACTC.
- Earned income includes wages, salaries, tips, net self-employment income, and other compensation for personal services.
- Earned income does **not** include interest, dividends, pensions, Social Security benefits, unemployment compensation, or alimony.

### Special Rule for Three or More Qualifying Children

Taxpayers with **three or more qualifying children** may use an alternative ACTC calculation:

```
Alternative ACTC = Social Security taxes paid (including employee share + self-employment tax) - Earned Income Credit (EIC)
```

The taxpayer uses the **greater** of:
- 15% of (earned income - $2,500); **or**
- Social Security taxes paid minus EIC claimed.

This alternative benefits low-income families with three or more children whose Social Security taxes exceed their EIC.

---

## 5. Credit for Other Dependents (ODC)

### Amount
**$500** per qualifying dependent (non-refundable).

### Who Qualifies

A dependent who does **not** qualify for the CTC, including:
- Children age 17 or older (e.g., college students age 17-23 claimed as dependents).
- Dependents who have an ITIN (Individual Taxpayer Identification Number) instead of an SSN.
- Qualifying relatives (e.g., elderly parents, other relatives who meet the dependency tests).
- Dependents who are not U.S. citizens/nationals/residents but are residents of Canada or Mexico.

### Requirements
- The dependent must be claimed on the taxpayer's return.
- The dependent must have an SSN, ITIN, or ATIN issued before the due date of the return.
- The dependent cannot be the taxpayer or the taxpayer's spouse.

### Phase-Out
The ODC is subject to the **same phase-out** as the CTC:
- $400,000 MAGI for MFJ
- $200,000 MAGI for all others
- Reduction of $50 per $1,000 of excess MAGI

The total of CTC + ODC is calculated first, then the combined phase-out reduction is applied.

---

## 6. Schedule 8812 -- Line-by-Line Instructions

### Part I -- Child Tax Credit and Credit for Other Dependents

| Line | Description |
|------|-------------|
| **1** | Enter the amount from Form 1040, Line 11 (AGI). |
| **2a** | Enter any income from Puerto Rico excluded from gross income. |
| **2b** | Enter any amounts from Form 2555, Lines 45 and 50 (FEIE/foreign housing). |
| **2c** | Enter any amounts from Form 4563, Line 15 (American Samoa exclusion). |
| **2d** | Add Lines 2a through 2c. |
| **3** | Add Lines 1 and 2d. This is your **Modified AGI** for the credit. |
| **4** | Enter the number of qualifying children under age 17 with valid SSNs (from Form 1040 Dependents section, column 4 checked). |
| **5** | Multiply Line 4 by **$2,500**. This is the total CTC before phase-out. |
| **6** | Enter the number of other dependents (from Form 1040 Dependents section, column 4 not checked). Do not include yourself, your spouse, or dependents who are not U.S. citizens/nationals/residents. |
| **7** | Multiply Line 6 by **$500**. This is the total ODC before phase-out. |
| **8** | Add Lines 5 and 7. This is the combined CTC + ODC before phase-out. |
| **9** | Enter **$400,000** if MFJ; otherwise enter **$200,000**. |
| **10** | Subtract Line 9 from Line 3. If zero or less, enter 0. |
| **11** | Multiply Line 10 by **5%** (0.05). This is the phase-out reduction. |
| **12** | Subtract Line 11 from Line 8. If zero or less, you cannot claim the CTC, ACTC, or ODC. |
| **13** | Enter the tax liability from Form 1040 (tax minus certain credits). |
| **14** | Enter the **smaller** of Line 12 or Line 13. This is the nonrefundable CTC/ODC claimed on Form 1040, Line 19. |

### Part II-A -- Additional Child Tax Credit (Refundable)

| Line | Description |
|------|-------------|
| **15** | Subtract Line 14 from Line 12. If zero, you cannot claim the ACTC. |
| **16a** | Number of qualifying children under age 17 with valid SSNs (same as Line 4). |
| **16b** | Multiply Line 16a by **$1,400**. This is the maximum ACTC. |
| **17** | Enter the **smaller** of Line 15 or Line 16b. |
| **18a** | Enter earned income (wages, salaries, tips, net SE income). |
| **18b** | Enter nontaxable combat pay (if elected to include). |
| **19** | Is Line 18a more than $2,500? If **yes**, subtract $2,500 from Line 18a. If **no**, enter 0. |
| **20** | Multiply Line 19 by **15%** (0.15). |
| **21** | If you have fewer than three qualifying children, enter the amount from Line 20. If three or more, complete Part II-B, then enter the larger of Line 20 or Line 27. |
| **22** | Enter the **smaller** of Line 17 or Line 21. This is your ACTC. Enter on Form 1040, Line 28. |

### Part II-B -- Certain Filers with Three or More Qualifying Children

| Line | Description |
|------|-------------|
| **23** | Enter withheld Social Security and Medicare taxes (from W-2, Boxes 4 and 6). |
| **24** | Enter Schedule 1 amounts + Schedule 2 amounts + Schedule 3 amounts as instructed (additional Social Security taxes, self-employment tax, etc.). |
| **25** | Add Lines 23 and 24. Total Social Security taxes. |
| **26** | Enter the total EIC from Form 1040, Line 27. |
| **27** | Subtract Line 26 from Line 25. If zero or less, enter 0. |

---

## 7. Key Filing Considerations

### Who Must File Schedule 8812
- Any taxpayer claiming the CTC, ACTC, or ODC must complete and attach Schedule 8812 to Form 1040.

### Divorced or Separated Parents
- Generally, only the **custodial parent** can claim the CTC for a qualifying child.
- The noncustodial parent may claim the CTC if the custodial parent releases the claim using **Form 8332** (Release/Revocation of Release of Claim to Exemption for Child by Custodial Parent).
- If Form 8332 is used, the noncustodial parent claims the CTC/ODC, but the **custodial parent** retains eligibility for the EIC and dependent care credit.

### Taxpayers with Foreign Earned Income Exclusion
- Taxpayers who claim the Foreign Earned Income Exclusion (Form 2555) must add back excluded amounts to AGI when computing MAGI for the CTC phase-out.
- The excluded income is **not** treated as earned income for the ACTC calculation.

### Due Diligence
- The IRS requires paid preparers to exercise due diligence when claiming the CTC/ACTC (Form 8867).
- Penalties apply to preparers who fail to meet due diligence requirements.

---

## 8. Interaction with Other Credits

| Credit | Interaction |
|--------|------------|
| Earned Income Credit (EIC) | The EIC is calculated separately. The EIC amount is used in the ACTC Part II-B calculation for filers with 3+ qualifying children. |
| Child and Dependent Care Credit | Calculated separately on Form 2441. Does not affect CTC amount, but may affect tax liability used to compute the nonrefundable CTC. |
| Education Credits | Calculated on Form 8863. Reduces tax liability, which may increase the ACTC. |
| Foreign Tax Credit | Reduces tax liability, which may increase the ACTC. |

---

## 9. Summary Table

| Item | 2025 Amount |
|------|-------------|
| CTC per qualifying child | **$2,500** |
| ODC per other dependent | **$500** |
| ACTC maximum per child | **$1,400** |
| ACTC earned income threshold | **$2,500** |
| ACTC earned income rate | **15%** |
| Phase-out threshold (MFJ) | **$400,000** |
| Phase-out threshold (other) | **$200,000** |
| Phase-out rate | **$50 per $1,000 excess** |
| Qualifying child age limit | **Under 17** |

---

*Source: [IRS Schedule 8812 Instructions (2025)](https://www.irs.gov/instructions/i1040s8), [IRS Child Tax Credit](https://www.irs.gov/credits-deductions/individuals/child-tax-credit), [OBBBA Tax Provisions (P.L. 119-21)](https://www.irs.gov/newsroom/one-big-beautiful-bill-provisions), [H&R Block OBBBA Family Changes](https://www.hrblock.com/tax-center/irs/tax-law-and-policy/one-big-beautiful-bill-families/).*
