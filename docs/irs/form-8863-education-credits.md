# Form 8863 -- Education Credits (2025)

> **Reference document for Tax Man engine.**
> Sourced from IRS Form 8863 instructions, IRS Topic 456, and related guidance.
> Applicable to tax year 2025 (returns filed in 2026).

---

## Overview

Form 8863, "Education Credits (American Opportunity and Lifetime Learning Credits)," is used to calculate and claim two education-related tax credits:

1. **American Opportunity Credit (AOC)** -- up to **$2,500** per eligible student, partially refundable.
2. **Lifetime Learning Credit (LLC)** -- up to **$2,000** per return, nonrefundable.

This document also covers the **Student Loan Interest Deduction** (reported on Schedule 1, Line 21), which is a related education tax benefit.

---

## 1. American Opportunity Credit (AOC)

### Credit Amount
- **Maximum:** $2,500 per eligible student per year.
- **Calculation:** 100% of the **first $2,000** of qualified education expenses + 25% of the **next $2,000** of qualified education expenses.

```
AOC = min($2,000, qualified expenses) + 0.25 x min($2,000, max(0, qualified expenses - $2,000))
```

### Refundable Portion
- **40%** of the AOC (up to **$1,000**) is **refundable** -- it can be received as a refund even if the taxpayer owes no tax.
- The remaining 60% is nonrefundable (reduces tax liability to zero but no further).

### Eligibility Requirements

| Requirement | Details |
|-------------|---------|
| Enrollment | Student must be enrolled **at least half-time** for at least one academic period during the tax year. |
| Degree program | Student must be pursuing a **degree or other recognized credential**. |
| Year limit | Available only for the **first four years** of postsecondary education. Cannot be claimed for more than 4 tax years per student. |
| No felony drug conviction | Student must not have a **federal or state felony drug conviction** at the end of the tax year. |
| Not previously claimed 4 times | The AOC has not been claimed for this student in 4 prior tax years. |

### MAGI Phase-Out (AOC)

| Filing Status | Phase-Out Begins | Phase-Out Complete | Phase-Out Range |
|---------------|-----------------|-------------------|-----------------|
| Single / HOH / QSS | $80,000 | $90,000 | $10,000 |
| Married Filing Jointly | $160,000 | $180,000 | $20,000 |
| Married Filing Separately | **Not eligible** | -- | -- |

**Phase-out formula:**
```
If MAGI > lower threshold:
    Reduction fraction = (MAGI - lower threshold) / phase-out range
    Allowable credit = credit x (1 - reduction fraction)
```

### Example (AOC)
A single filer with MAGI of $85,000 pays $4,000 in qualified tuition for one eligible student:
- Full AOC = $2,000 + (0.25 x $2,000) = $2,500
- Reduction fraction = ($85,000 - $80,000) / $10,000 = 0.50
- Allowable AOC = $2,500 x (1 - 0.50) = **$1,250**
- Refundable portion = 40% x $1,250 = **$500**
- Nonrefundable portion = 60% x $1,250 = **$750**

---

## 2. Lifetime Learning Credit (LLC)

### Credit Amount
- **Maximum:** $2,000 per return (not per student).
- **Calculation:** 20% of up to **$10,000** of qualified education expenses.

```
LLC = 0.20 x min($10,000, total qualified expenses across all students)
```

### Nonrefundable
- The LLC is entirely **nonrefundable** -- it can reduce tax liability to zero but cannot generate a refund.

### Eligibility Requirements

| Requirement | Details |
|-------------|---------|
| Enrollment | Student must be enrolled in **at least one course** at an eligible educational institution. |
| Degree program | **Not required** -- courses taken to acquire or improve job skills qualify. |
| Year limit | **No limit** on the number of years the LLC can be claimed. |
| Felony drug conviction | **No restriction** (unlike the AOC). |
| Number of students | Credit is per **return**, not per student. Expenses for multiple students can be combined up to the $10,000 cap. |

### MAGI Phase-Out (LLC)

| Filing Status | Phase-Out Begins | Phase-Out Complete | Phase-Out Range |
|---------------|-----------------|-------------------|-----------------|
| Single / HOH / QSS | $80,000 | $90,000 | $10,000 |
| Married Filing Jointly | $160,000 | $180,000 | $20,000 |
| Married Filing Separately | **Not eligible** | -- | -- |

*Note: The LLC phase-out ranges are the same as the AOC ranges for 2025. This is the result of prior legislation unifying the thresholds.*

---

## 3. Comparison of the Two Credits

| Feature | American Opportunity Credit | Lifetime Learning Credit |
|---------|-----------------------------|--------------------------|
| Maximum credit | **$2,500** per student | **$2,000** per return |
| Refundable | **Yes** (40%, up to $1,000) | **No** |
| Qualified expenses | Tuition, required fees, **course materials** (books, supplies, equipment) | Tuition, required fees (no books unless required for enrollment) |
| Years available | First **4 years** of postsecondary | **Unlimited** years |
| Enrollment requirement | At least **half-time** | At least **one course** |
| Degree required | **Yes** | **No** |
| Drug conviction disqualifier | **Yes** | **No** |
| Per student or per return | **Per student** | **Per return** |
| MAGI phase-out (Single) | $80,000 - $90,000 | $80,000 - $90,000 |
| MAGI phase-out (MFJ) | $160,000 - $180,000 | $160,000 - $180,000 |

### Choosing Between Credits

- You **cannot** claim both the AOC and LLC for the **same student** in the same year.
- You **can** claim the AOC for one student and the LLC for a different student in the same year.
- If a student is in the first 4 years and meets all AOC requirements, the AOC is generally more beneficial due to its higher maximum and partial refundability.
- The LLC is appropriate for graduate students, students taking courses for career development, or students who have already claimed the AOC for 4 years.

---

## 4. Qualified Education Expenses

### For the AOC
- Tuition and required enrollment fees.
- Course-related books, supplies, and equipment needed for the course of study (do not need to be purchased from the institution).

### For the LLC
- Tuition and fees required for enrollment or attendance at the institution.
- Books and supplies are included **only** if required to be purchased from the educational institution as a condition of enrollment.

### Not Qualified (Both Credits)
- Room and board.
- Insurance.
- Medical expenses (including student health fees, unless required for enrollment).
- Transportation.
- Personal, living, or family expenses.
- Expenses paid with tax-free scholarships, grants, or employer-provided educational assistance.
- Expenses paid with Pell grants or other tax-free education benefits.

### Adjustments
Qualified expenses must be **reduced** by:
- Tax-free portions of scholarships and fellowships.
- Tax-free employer-provided educational assistance (Section 127).
- Veterans' educational assistance.
- Any other tax-free educational benefit (other than gifts, bequests, or inheritances).

---

## 5. Form 1098-T Requirement

- Taxpayers must receive **Form 1098-T, Tuition Statement** from the eligible educational institution to claim either credit.
- The institution reports amounts billed (Box 1) or amounts received (Box 1) for qualified tuition and related expenses.
- Box 5 reports scholarships and grants.
- If the institution is not required to file Form 1098-T (e.g., certain foreign institutions), the taxpayer can still claim the credit with adequate documentation.

### Eligible Educational Institution
An institution that:
- Is eligible to participate in a student aid program administered by the U.S. Department of Education; **and**
- Includes most accredited colleges, universities, vocational schools, and other postsecondary institutions (domestic and foreign).

---

## 6. Form 8863 -- Line-by-Line Instructions

### Part I -- Refundable American Opportunity Credit

| Line | Description |
|------|-------------|
| **1** | Tentative AOC from Part III (complete Part III first for each student). |
| **2** | Enter the tentative AOC from Part III for all students combined. |
| **3-7** | MAGI phase-out calculation. Enter MAGI, apply the phase-out reduction. |
| **8** | Adjusted AOC after phase-out. |
| **9** | Multiply Line 8 by **40%** (0.40). This is the **refundable** portion. Enter on Form 1040, Line 29. |

### Part II -- Nonrefundable Education Credits

| Line | Description |
|------|-------------|
| **10** | Subtract Line 9 from Line 8. This is the nonrefundable portion of the AOC. |
| **11-17** | LLC calculation. Enter qualified expenses (up to $10,000), multiply by 20%, apply MAGI phase-out. |
| **18** | Total nonrefundable education credits (AOC nonrefundable portion + LLC). |
| **19** | Tax liability limit. Enter the tax liability less certain credits. |
| **20** | Enter the **smaller** of Line 18 or Line 19. This is the nonrefundable education credit. Enter on Schedule 3, Line 2. |

### Part III -- Student and Education Information (per student)

| Line | Description |
|------|-------------|
| **21** | Student name (as shown on SSN card). |
| **22** | Student SSN. |
| **23** | Eligible educational institution EIN (from Form 1098-T). |
| **24** | Institution name. |
| **25** | Indicate if student received Form 1098-T. |
| **26** | Check if AOC was claimed for this student for any 4 prior tax years. |
| **27** | Check if student completed first 4 years of postsecondary education before 2025. |
| **28** | Check if student was enrolled at least half-time for at least one academic period. |
| **29** | Check if student had felony drug conviction. |
| **30** | Adjusted qualified expenses (after reducing by tax-free scholarships, etc.). |
| **31** | If claiming AOC: enter the smaller of Line 30 or $10,000. |

---

## 7. MAGI Definition for Education Credits

MAGI for education credits = AGI (Form 1040, Line 11) **plus**:
- Foreign earned income exclusion (Form 2555).
- Foreign housing exclusion or deduction (Form 2555).
- Exclusion of income from Puerto Rico or American Samoa.

---

## 8. Student Loan Interest Deduction

Although not part of Form 8863, the student loan interest deduction is a related education tax benefit.

### Deduction Amount
- Deduct up to **$2,500** of student loan interest paid during the year.
- Reported on **Schedule 1 (Form 1040), Line 21** as an adjustment to income (above-the-line deduction).
- The deduction is available whether or not the taxpayer itemizes deductions.

### Eligibility Requirements
- The loan must have been taken out **solely to pay qualified education expenses**.
- The student must have been enrolled at least half-time in a program leading to a degree, certificate, or other recognized credential.
- The taxpayer must be **legally obligated** to pay the interest.
- Filing status cannot be **Married Filing Separately**.
- The taxpayer cannot be claimed as a **dependent** on another return.

### MAGI Phase-Out

| Filing Status | Phase-Out Begins | Phase-Out Complete | Phase-Out Range |
|---------------|-----------------|-------------------|-----------------|
| Single / HOH / QSS | $85,000 | $100,000 | $15,000 |
| Married Filing Jointly | $170,000 | $200,000 | $30,000 |
| Married Filing Separately | **Not eligible** | -- | -- |

**Phase-out formula:**
```
If MAGI > lower threshold:
    Reduction fraction = (MAGI - lower threshold) / phase-out range
    Allowable deduction = deduction x (1 - reduction fraction)
```

### Qualified Education Expenses for Student Loan Interest
Qualified expenses include: tuition, fees, room and board, books, supplies, equipment, and other necessary expenses (such as transportation) -- **broader** than the definition for education credits.

### Where to Report
- Deducted on **Schedule 1, Line 21** ("Student loan interest deduction").
- Flows to Form 1040, Line 10 as part of total adjustments.
- The lender provides **Form 1098-E** showing student loan interest paid during the year (if $600 or more).

---

## 9. Key Filing Considerations

### Cannot Double-Dip
- The same expenses cannot be used for both an education credit and the student loan interest deduction.
- The same expenses cannot be used for both an education credit and a tax-free distribution from a 529 plan or Coverdell ESA.
- However, different portions of total expenses can be allocated to different benefits.

### Married Filing Separately
- **Neither** education credit (AOC or LLC) is available to MFS filers.
- The student loan interest deduction is also **not available** to MFS filers.

### Coordination with 529 Plans / Coverdell ESA
- Qualified expenses must be reduced by amounts paid with tax-free distributions from 529 plans or Coverdell ESAs before calculating the education credit.
- Strategy: Use 529/ESA distributions for room and board (which do not qualify for the credits), and use out-of-pocket payments for tuition (which do qualify for the credits).

### Foreign Institutions
- Both credits can be claimed for eligible foreign educational institutions.
- The institution must be eligible to participate in a U.S. Department of Education student aid program.

---

## 10. Summary Table

| Item | AOC | LLC | Student Loan Interest |
|------|-----|-----|-----------------------|
| Maximum benefit | **$2,500** per student | **$2,000** per return | **$2,500** deduction |
| Refundable | **40%** (up to $1,000) | **No** | N/A (deduction) |
| Form | 8863 | 8863 | Schedule 1, Line 21 |
| MAGI phase-out (Single) | $80K - $90K | $80K - $90K | $85K - $100K |
| MAGI phase-out (MFJ) | $160K - $180K | $160K - $180K | $170K - $200K |
| MFS eligible | **No** | **No** | **No** |
| Year limit | **4 years** | **None** | **None** |
| Enrollment | Half-time | One course | Half-time (when loan originated) |

---

*Source: [IRS Form 8863 Instructions (2025)](https://www.irs.gov/instructions/i8863), [IRS Education Credits (AOTC and LLC)](https://www.irs.gov/credits-deductions/individuals/education-credits-aotc-and-llc), [IRS Topic 456 (Student Loan Interest)](https://www.irs.gov/taxtopics/tc456), [SmartAsset Student Loan Interest Deduction](https://smartasset.com/taxes/student-loan-interest-deduction).*
