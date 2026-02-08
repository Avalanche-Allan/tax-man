# Publication 596 -- Earned Income Credit (EIC) (2025)

> **Reference document for Tax Man engine.**
> Sourced from IRS Publication 596 (2025), IRS EITC tables, and OBBBA (P.L. 119-21) provisions.
> Applicable to tax year 2025 (returns filed in 2026).

---

## Overview

The Earned Income Credit (EIC), also called the Earned Income Tax Credit (EITC), is a **refundable** tax credit for low-to-moderate income workers. Unlike most credits, the EIC can result in a refund even if the taxpayer owes no tax. The credit amount depends on earned income, filing status, and the number of qualifying children.

For 2025, the maximum EIC ranges from **$649** (no children) to **$8,046** (three or more children).

---

## 1. Who Qualifies -- General Eligibility Rules

To claim the EIC, a taxpayer must meet **all** of the following requirements:

### Earned Income Requirement
- The taxpayer must have **earned income** during the tax year.
- Earned income includes: wages, salaries, tips, net self-employment earnings, union strike benefits, long-term disability payments received before minimum retirement age, and nontaxable combat pay (if elected).
- Earned income does **not** include: interest, dividends, pensions, annuities, Social Security benefits, unemployment compensation, alimony, child support, welfare benefits, workers' compensation, or income earned while incarcerated.

### AGI Limits (2025)

| Number of Qualifying Children | Single / HOH / QSS | Married Filing Jointly |
|-------------------------------|--------------------|-----------------------|
| 0 | $19,104 | $26,214 |
| 1 | $50,434 | $57,554 |
| 2 | $57,310 | $64,430 |
| 3 or more | $61,555 | $68,675 |

### Investment Income Limit
- The taxpayer's **investment income** for the year must be **$11,950 or less** (2025).
- Investment income includes: taxable interest, tax-exempt interest, ordinary dividends, capital gain net income, net rental or royalty income (if positive), and net passive income (if positive).

### Valid Social Security Number
- The taxpayer (and spouse if filing jointly) must have a **valid SSN for employment** issued by the SSA before the due date of the return (including extensions).
- ITINs and ATINs do not qualify.
- Each qualifying child must also have a valid SSN.

### Filing Status
- **Eligible statuses:** Single, Head of Household, Married Filing Jointly, Qualifying Surviving Spouse.
- **Married Filing Separately:** Generally **not eligible** for the EIC. The OBBBA did not change this rule for 2025. However, an exception exists: taxpayers who lived apart from their spouse for the last 6 months of the year and meet certain conditions may be able to use HOH status or may qualify under the separated spouse rule (see IRS Publication 596 for details).

### Not a Qualifying Child of Another Person
- The taxpayer cannot be claimed as a qualifying child on another person's return.

### U.S. Residency
- The taxpayer (and spouse) must have lived in the United States for more than half of the tax year.
- Members of the military stationed outside the U.S. on extended active duty are considered U.S. residents.

### Cannot Claim with Foreign Earned Income Exclusion
- A taxpayer who files **Form 2555** (Foreign Earned Income Exclusion) or **Form 2555-EZ** **cannot** claim the EIC for the tax year, even if the excluded income is below the EIC thresholds.

---

## 2. Age Rules (Taxpayers with No Qualifying Children)

Taxpayers who do **not** have a qualifying child must also meet the following age requirements:

- Must be at least **age 25** but under **age 65** at the end of the tax year.
- If married filing jointly, at least **one spouse** must meet the age requirement.
- Cannot be a dependent of another taxpayer.
- Cannot be a qualifying child of another taxpayer.
- Must have lived in the United States for more than half the year.

*Note: The temporary ARPA expansion (2021) that lowered the age to 19/24 for students has expired and was not renewed by the OBBBA.*

---

## 3. Qualifying Child Rules for EIC

A qualifying child for EIC purposes must meet **all four** of these tests:

### Relationship Test
The child must be the taxpayer's:
- Son, daughter, stepchild, adopted child, or eligible foster child; **or**
- Brother, sister, half-brother, half-sister, stepbrother, stepsister; **or**
- A descendant of any of the above (e.g., grandchild, niece, nephew).

### Age Test
- The child must be **under age 19** at the end of the tax year; **or**
- **Under age 24** at the end of the year and a **full-time student** for at least 5 months during the year; **or**
- **Any age** if **permanently and totally disabled**.

### Residency Test
- The child must have **lived with the taxpayer in the United States for more than half of the tax year**.
- Temporary absences for school, medical care, vacation, military service, or detention count as time lived together.

### Joint Return Test
- The child cannot file a **joint return** for the year, unless filed solely to claim a refund of withheld taxes or estimated tax paid.

### Tiebreaker Rules
If a child qualifies as a qualifying child for more than one person:
1. If only one person is the child's parent, the parent claims the credit.
2. If both parents can claim, the parent with whom the child lived longer claims the credit. If equal, the parent with the higher AGI claims.
3. If neither person is the child's parent, the person with the higher AGI claims the credit.
4. If a parent can claim but does not, the other eligible person may claim.

---

## 4. Maximum Credit Amounts (2025)

| Number of Qualifying Children | Maximum EIC |
|-------------------------------|-------------|
| 0 | **$649** |
| 1 | **$4,328** |
| 2 | **$7,152** |
| 3 or more | **$8,046** |

---

## 5. Phase-In and Phase-Out Parameters (2025)

### Phase-In (Credit Builds Up)

| Children | Phase-In Rate | Earned Income to Reach Max Credit |
|----------|--------------|----------------------------------|
| 0 | 7.65% | $8,490 |
| 1 | 34% | $12,730 |
| 2 | 40% | $17,880 |
| 3+ | 45% | $17,880 |

During the phase-in range, the EIC equals the **phase-in rate** multiplied by earned income.

### Plateau (Credit Stays at Maximum)

After earned income reaches the amount needed for the maximum credit, the EIC remains at its maximum level until the taxpayer's AGI (or earned income, whichever is greater) exceeds the phase-out threshold.

### Phase-Out (Credit Decreases)

| Children | Phase-Out Rate | Phase-Out Begins (Single/HOH/QSS) | Phase-Out Begins (MFJ) | Phase-Out Ends (Single/HOH/QSS) | Phase-Out Ends (MFJ) |
|----------|---------------|-----------------------------------|----------------------|--------------------------------|---------------------|
| 0 | 7.65% | $10,620 | $17,730 | $19,104 | $26,214 |
| 1 | 15.98% | $23,350 | $30,460 | $50,434 | $57,554 |
| 2 | 21.06% | $23,350 | $30,460 | $57,310 | $64,430 |
| 3+ | 21.06% | $23,350 | $30,460 | $61,555 | $68,675 |

*Note: The MFJ phase-out thresholds are approximately $7,110 higher than the Single/HOH thresholds (the "marriage penalty relief" amount, which is permanent under OBBBA).*

During the phase-out range, the EIC is reduced at the **phase-out rate** for each dollar of AGI (or earned income, if greater) above the phase-out threshold.

### EIC Calculation Formula

```
If earned income <= phase-in completion:
    EIC = earned income x phase-in rate

If AGI > phase-out begin threshold:
    EIC = max credit - (AGI - phase-out threshold) x phase-out rate

Credit = min(phase-in amount, max credit - phase-out reduction)
Credit = max(0, Credit)
```

---

## 6. Earned Income Definition

Earned income for EIC purposes includes:

| Included | Excluded |
|----------|----------|
| Wages, salaries, tips (W-2, Box 1) | Interest and dividends |
| Net earnings from self-employment (Schedule SE) | Social Security / SSI benefits |
| Union strike benefits | Unemployment compensation |
| Certain disability payments (before min retirement age) | Pensions and annuities |
| Nontaxable combat pay (if elected, Form W-2 Box 12, Code Q) | Alimony |
| | Workers' compensation |
| | Child support |
| | Income earned while incarcerated |

### Self-Employment Income
- Net self-employment earnings for EIC purposes = net profit from Schedule C (or Schedule F for farming) minus the deductible portion of self-employment tax (Schedule SE, Section A, Line 6 or Section B, Line 13).
- If self-employment results in a net loss, it reduces earned income for EIC purposes.

### Nontaxable Combat Pay Election
- Taxpayers may elect to include nontaxable combat pay as earned income for EIC purposes.
- This election may increase or decrease the EIC depending on where the taxpayer falls in the phase-in/phase-out range.
- The election applies only to the EIC calculation -- it does not affect other tax computations.

---

## 7. Disqualifying Rules

The EIC is **not** available if:

1. **Filing Status is Married Filing Separately** (with the limited separated spouse exception noted above).
2. **Form 2555 is filed** (Foreign Earned Income Exclusion) -- even if no income is actually excluded, filing the form disqualifies the taxpayer from the EIC.
3. **Investment income exceeds $11,950** (2025).
4. The taxpayer is a **nonresident alien** for any part of the year (unless married to a U.S. citizen or resident and elects to be treated as a resident alien for the full year).
5. The taxpayer is the **qualifying child** of another person.

---

## 8. Schedule EIC

Taxpayers claiming the EIC with one or more qualifying children must complete and attach **Schedule EIC** (Form 1040) to their return.

### Information Required for Each Qualifying Child

| Field | Description |
|-------|-------------|
| Child's name | Full legal name |
| Child's SSN | Valid SSN for employment |
| Child's year of birth | To verify age test |
| Disability status | If age 19+ and permanently/totally disabled |
| Student status | If age 19-23 and full-time student |
| Relationship | Relationship to taxpayer |
| Months lived with taxpayer in U.S. | Must be more than 6 months |

- Schedule EIC is for **informational purposes** -- the credit amount is calculated on the EIC Worksheet in the Form 1040 instructions (or by tax software).
- Taxpayers without qualifying children do **not** file Schedule EIC but must still meet all other requirements.

---

## 9. Due Diligence Requirements (Paid Preparers)

Paid preparers must satisfy due diligence requirements under IRC Section 6695(g) when preparing returns claiming the EIC:

- Complete **Form 8867** (Paid Preparer's Due Diligence Checklist).
- Compute the credit using the EIC Worksheet or software.
- Retain records documenting how eligibility was determined.
- Ask the taxpayer additional questions if information seems incorrect or incomplete.
- **Penalty for failure:** $600 per return for failure to meet due diligence requirements (2025).

---

## 10. Refund Timing

Under the PATH Act (Protecting Americans from Tax Hikes Act of 2015):

- Returns claiming the EIC or ACTC cannot have refunds issued before **mid-February**.
- The IRS must hold the **entire refund** (not just the EIC portion) until it can verify EIC eligibility.
- Most EIC refunds are issued by the **first week of March** if filed electronically with direct deposit.

---

## 11. Summary Table

| Item | 2025 Amount |
|------|-------------|
| Maximum EIC (0 children) | **$649** |
| Maximum EIC (1 child) | **$4,328** |
| Maximum EIC (2 children) | **$7,152** |
| Maximum EIC (3+ children) | **$8,046** |
| Investment income limit | **$11,950** |
| AGI limit (3+ children, MFJ) | **$68,675** |
| AGI limit (0 children, Single) | **$19,104** |
| Age requirement (no children) | **25 to 64** |
| MFS eligible | **No** (limited exception) |
| Form 2555 disqualifies | **Yes** |

---

*Source: [IRS Publication 596 (2025)](https://www.irs.gov/publications/p596), [IRS EITC Tables](https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/earned-income-and-earned-income-tax-credit-eitc-tables), [IRS Who Qualifies for EITC](https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/who-qualifies-for-the-earned-income-tax-credit-eitc), [Tax Foundation 2025 Parameters](https://taxfoundation.org/data/all/federal/2025-tax-brackets/).*
