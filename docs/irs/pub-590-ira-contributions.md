# IRS Publication 590-A -- Contributions to Individual Retirement Arrangements (2025)

> **Source:** [IRS Publication 590-A (2025)](https://www.irs.gov/publications/p590a)
> **Applicable Tax Year:** 2025
> **Related Forms:** Form 8606, Form 5498, Form 1040 (Lines 20a/20b), Schedule 1
> **IRC Authority:** Sections 219 (traditional IRA), 408A (Roth IRA), 408(d)(6) (recharacterizations)

---

## 1. Overview

Publication 590-A covers the rules for contributing to traditional and Roth IRAs, including annual limits, income-based phase-outs for deductibility and eligibility, spousal IRAs, excess contribution penalties, recharacterizations, and nondeductible contributions reported on Form 8606.

---

## 2. Traditional IRA Contribution Limits

### 2.1 Annual Limits

| Parameter | 2025 Limit |
|---|---|
| Contribution limit (under age 50) | **$7,000** |
| Contribution limit (age 50 or older) | **$8,000** ($7,000 + $1,000 catch-up) |
| Compensation requirement | Must have **taxable compensation** at least equal to the contribution |
| Age limit | **None** (SECURE Act eliminated the age 70 1/2 limit for contributions) |

### 2.2 Contribution Deadline

Contributions for tax year 2025 must be made by the **due date of the return, not including extensions**:
- **April 15, 2026** for calendar-year filers.
- Extensions do **not** extend the IRA contribution deadline (unlike SEP-IRAs).

### 2.3 Compensation Requirement

"Taxable compensation" includes:
- Wages, salaries, tips, bonuses, commissions
- Net self-employment income
- Alimony received (under pre-2019 divorce agreements)
- Nontaxable combat pay (may elect to treat as compensation)

It does **not** include:
- Rental income, interest, dividends, or capital gains
- Pension or annuity income
- Deferred compensation
- Income excluded from tax (e.g., foreign earned income exclusion)

---

## 3. Traditional IRA Deductibility Phase-Outs

Whether a traditional IRA contribution is tax-deductible depends on (a) whether you or your spouse is covered by an employer-sponsored retirement plan and (b) your modified adjusted gross income (MAGI).

### 3.1 Covered by an Employer Retirement Plan

| Filing Status | MAGI Phase-Out Range (2025) | Full Deduction Below | No Deduction At or Above |
|---|---|---|---|
| **Single / Head of Household** | **$79,000 -- $89,000** | $79,000 | $89,000 |
| **Married Filing Jointly (MFJ)** | **$126,000 -- $146,000** | $126,000 | $146,000 |
| **Married Filing Separately (MFS)** | **$0 -- $10,000** | $0 | $10,000 |

### 3.2 NOT Covered by an Employer Plan, but Spouse IS Covered

| Filing Status | MAGI Phase-Out Range (2025) | Full Deduction Below | No Deduction At or Above |
|---|---|---|---|
| **Married Filing Jointly (MFJ)** | **$236,000 -- $246,000** | $236,000 | $246,000 |

### 3.3 Neither Spouse Covered by an Employer Plan

If **neither** you nor your spouse is covered by an employer plan, your traditional IRA contribution is **fully deductible regardless of MAGI**.

### 3.4 Partial Deduction Calculation

When MAGI falls within the phase-out range, the deductible amount is calculated as:

```
Deductible amount = Contribution limit x [(Upper limit - MAGI) / Phase-out range]
```

Round up to the nearest $10. The minimum partial deduction is $200 (if the formula produces a result between $0 and $200, you may deduct $200).

**Example:** Single filer, age 45, covered by employer plan, MAGI = $84,000:
```
$7,000 x [($89,000 - $84,000) / $10,000] = $7,000 x 0.50 = $3,500 deductible
Remaining $3,500 is a nondeductible contribution (report on Form 8606)
```

---

## 4. Roth IRA Contribution Limits

### 4.1 Annual Limits

The Roth IRA contribution limit is the **same** as the traditional IRA limit:

| Parameter | 2025 Limit |
|---|---|
| Contribution limit (under age 50) | **$7,000** |
| Contribution limit (age 50 or older) | **$8,000** |

The combined total of traditional and Roth IRA contributions cannot exceed $7,000 ($8,000 if age 50+). These limits are **aggregate** across all traditional and Roth IRA accounts.

### 4.2 Income Phase-Outs (Eligibility to Contribute)

Unlike traditional IRAs, Roth IRA contributions are **never deductible** but are subject to income limits that restrict or prohibit contributions entirely:

| Filing Status | MAGI Phase-Out Range (2025) | Full Contribution Below | No Contribution At or Above |
|---|---|---|---|
| **Single / Head of Household** | **$150,000 -- $165,000** | $150,000 | $165,000 |
| **Married Filing Jointly (MFJ)** | **$236,000 -- $246,000** | $236,000 | $246,000 |
| **Married Filing Separately (MFS)** | **$0 -- $10,000** | $0 | $10,000 |

### 4.3 Reduced Contribution Calculation

When MAGI falls within the phase-out range:

```
Reduced limit = Contribution limit x [(Upper limit - MAGI) / Phase-out range]
```

Round up to the nearest $10. The minimum reduced contribution is $200.

**Example:** Single filer, age 52, MAGI = $157,000:
```
$8,000 x [($165,000 - $157,000) / $15,000] = $8,000 x 0.5333 = $4,267 -> round up to $4,270
Maximum Roth IRA contribution = $4,270
```

---

## 5. Spousal IRA

### 5.1 Rules

A **spousal IRA** allows a working spouse to make IRA contributions on behalf of a non-working or low-earning spouse, provided they file a joint return.

- The working spouse must have **taxable compensation** equal to or greater than the combined IRA contributions for both spouses.
- Each spouse may contribute up to the full IRA limit ($7,000 / $8,000 if 50+) to their own IRA.
- The combined contribution for both spouses cannot exceed the working spouse's compensation.

### 5.2 Deductibility

The same MAGI phase-out rules apply to the spousal IRA. The non-working spouse's deduction phase-out depends on whether the working spouse is covered by an employer plan:
- If the working spouse **is** covered: the non-working spouse's deduction phases out at MAGI **$236,000 -- $246,000** (MFJ).
- If **neither** spouse is covered: the non-working spouse's contribution is fully deductible regardless of MAGI.

---

## 6. Excess Contributions

### 6.1 Definition

An **excess contribution** occurs when:
- You contribute more than the annual limit ($7,000 / $8,000).
- You contribute to a Roth IRA when your MAGI exceeds the eligibility threshold.
- You contribute more than your taxable compensation for the year.
- You make an ineligible rollover contribution.

### 6.2 Penalty

Excess contributions are subject to a **6% excise tax** per year for each year the excess remains in the IRA. The penalty is reported on **Form 5329, Part III** (traditional) or **Part IV** (Roth).

### 6.3 Correcting Excess Contributions

To avoid the 6% penalty, withdraw the excess contribution **plus net income attributable (NIA)** before the tax filing deadline (including extensions):
- The excess amount is not taxed (it was already included in income, or in the case of traditional IRA, was not deducted).
- The NIA is taxable in the year of the contribution and may be subject to the 10% early withdrawal penalty if under age 59 1/2.

Alternatively, the excess can be absorbed in a later year if the contribution limit is not fully used.

---

## 7. Recharacterizations

### 7.1 What Is a Recharacterization

A **recharacterization** allows you to treat a contribution made to one type of IRA (traditional or Roth) as if it had been made to the other type. The contribution, plus NIA, is transferred between IRAs.

### 7.2 Key Rules

- Must be completed by the **due date of the return, including extensions** (October 15, 2026 for 2025 contributions, if extended).
- The NIA attributable to the recharacterized contribution must be transferred along with the contribution.
- You may recharacterize a **contribution** (traditional to Roth, or Roth to traditional), but you **cannot** recharacterize a **conversion** (this restriction was enacted by the Tax Cuts and Jobs Act of 2017).
- The recharacterized contribution is treated as if it were originally made to the second IRA.
- Report the recharacterization on the tax return for the year of the original contribution. Attach a statement explaining the recharacterization.

### 7.3 Common Uses

- You contributed to a Roth IRA but your MAGI turned out to exceed the limit -- recharacterize to traditional.
- You contributed to a traditional IRA but decide a Roth would be more beneficial -- recharacterize to Roth (subject to Roth income limits).

---

## 8. Backdoor Roth IRA Strategy

### 8.1 Overview

The "backdoor Roth" is a legal strategy for high-income taxpayers who exceed the Roth IRA income limits to effectively make Roth IRA contributions via a two-step process:

1. **Step 1:** Make a **nondeductible contribution** to a traditional IRA ($7,000 / $8,000). There is no income limit for nondeductible traditional IRA contributions.
2. **Step 2:** **Convert** the traditional IRA to a Roth IRA. There is no income limit on Roth conversions.

### 8.2 Pro-Rata Rule (Aggregation Rule)

The IRS treats **all traditional, SEP, and SIMPLE IRAs** as a single pool when determining the taxable portion of a conversion. If you have existing pre-tax IRA balances, the conversion will be partially taxable:

```
Taxable portion = Conversion amount x (Total pre-tax IRA balance / Total IRA balance)
```

**Example:** You have $93,000 in a rollover IRA (all pre-tax) and make a $7,000 nondeductible contribution to a separate traditional IRA. Total IRA balance = $100,000.

If you convert the $7,000:
```
Taxable portion = $7,000 x ($93,000 / $100,000) = $6,510 taxable
Only $490 is tax-free (the nondeductible basis portion)
```

### 8.3 Avoiding the Pro-Rata Rule

To execute a clean backdoor Roth (minimal tax on conversion):
- **Roll pre-tax IRA funds into an employer plan** (401(k), 403(b)) before year-end. This removes the pre-tax balance from the IRA aggregation calculation.
- Ensure all traditional, SEP, and SIMPLE IRA balances are **$0** on December 31 of the conversion year.
- The pro-rata rule is assessed based on year-end IRA balances.

### 8.4 Reporting

- Report the nondeductible contribution on **Form 8606, Part I**.
- Report the conversion on **Form 8606, Part II**.
- The nontaxable basis carries forward on Form 8606 from year to year.

---

## 9. Nondeductible Contributions (Form 8606)

### 9.1 When to File Form 8606

File **Form 8606** if you:
1. Made **nondeductible contributions** to a traditional IRA.
2. Received **distributions** from a traditional, SEP, or SIMPLE IRA and you have basis (prior nondeductible contributions).
3. **Converted** from a traditional, SEP, or SIMPLE IRA to a Roth IRA.
4. Received distributions from a Roth IRA.

### 9.2 Tracking Basis

Form 8606 tracks your cumulative **basis** (nondeductible contributions) in traditional IRAs. This basis is not taxed again when distributed or converted.

- **Line 1:** Current year nondeductible contributions.
- **Line 2:** Basis from prior years (carried from prior Form 8606).
- **Line 3:** Total basis = Line 1 + Line 2.
- **Line 14:** Basis remaining after distributions/conversions (carries to next year).

### 9.3 Penalty for Failure to File

If you fail to file Form 8606 to report nondeductible contributions, the IRS may impose a **$50 penalty** per occurrence. More importantly, without Form 8606, you may lose track of your basis and be taxed twice on the same money.

---

## 10. Key Rules and Coordination

### 10.1 Combined Limit

The $7,000 / $8,000 annual limit applies to the **combined total** of all traditional and Roth IRA contributions. You can split contributions between both types, but the total cannot exceed the limit.

### 10.2 IRA vs. Employer Plan Contributions

IRA contributions are **separate** from employer plan limits. You can contribute $7,000 to an IRA **and** $23,500 to a 401(k) in the same year (subject to deductibility phase-outs for the traditional IRA).

### 10.3 Contribution Ordering

If you contribute to both traditional and Roth IRAs and the total exceeds the limit, the excess is applied to the **Roth contributions first** (by default). You can designate which account holds the excess when correcting.

### 10.4 Tax Filing Requirements

| Situation | Form Required |
|---|---|
| Deductible traditional IRA contribution | Schedule 1, Line 20 |
| Nondeductible traditional IRA contribution | Form 8606, Part I |
| Roth IRA contribution | No form required (not deductible, no Form 8606 unless converting) |
| Roth conversion | Form 8606, Part II; Form 1040, Lines 4a/4b |
| Excess contribution penalty | Form 5329 |
| Recharacterization | Statement attached to return |

---

## 11. MAGI Phase-Out Summary Table

| Situation | Filing Status | 2025 Phase-Out Range |
|---|---|---|
| Traditional IRA deduction -- covered by employer plan | Single / HOH | $79,000 -- $89,000 |
| Traditional IRA deduction -- covered by employer plan | MFJ | $126,000 -- $146,000 |
| Traditional IRA deduction -- covered by employer plan | MFS | $0 -- $10,000 |
| Traditional IRA deduction -- NOT covered, but spouse IS | MFJ | $236,000 -- $246,000 |
| Roth IRA contribution eligibility | Single / HOH | $150,000 -- $165,000 |
| Roth IRA contribution eligibility | MFJ | $236,000 -- $246,000 |
| Roth IRA contribution eligibility | MFS | $0 -- $10,000 |
