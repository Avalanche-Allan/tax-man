# Tax Man

Personal 2025 US federal tax return preparation, powered by Claude Code.

## Overview

Tax Man replaces a CPA for preparing a 2025 federal return. It's not a standalone app — it's a **Claude Code-driven interactive system**. The Python package handles all tax math, document parsing, and PDF form generation. Claude Code acts as the CPA: analyzing documents, walking through each form, explaining decisions, and flagging optimization opportunities.

## Filing Profile

| Item | Detail |
|------|--------|
| **Tax Year** | 2025 (filing in 2026) |
| **Filing Status** | Married Filing Separately (MFS) |
| **Residence** | US citizen living full-time in Mexico City |
| **Spouse** | Mexican citizen, non-resident alien (NRA), no US tax obligations |
| **Spouse election** | NOT electing to treat spouse as US resident |
| **Primary income** | 1099-NEC contracting to US law firm (~$110–135K) via single-member LLC |
| **Secondary income** | DocSherpa LLC (~$500 revenue, SaaS product) |
| **Passive income** | K-1 from co-owned Denver rental property |
| **W-2 income** | None |
| **Dependents** | None |
| **Foreign bank accounts** | None exceeding $10K (no FBAR/8938) |
| **Crypto** | None |
| **Foreign taxes paid** | None (no FTC) |
| **Retirement contributions** | None in 2025 |

## Required IRS Forms

| Form | Purpose | Status |
|------|---------|--------|
| **Form 1040** | Individual Income Tax Return | Engine built |
| **Schedule 1** | Additional Income and Adjustments | Engine built |
| **Schedule 2** | Additional Taxes (SE tax, Addl Medicare) | Engine built |
| **Schedule C** (x2) | Profit or Loss — Law Firm LLC | Engine built |
| **Schedule C** (x2) | Profit or Loss — DocSherpa LLC | Engine built |
| **Schedule SE** | Self-Employment Tax | Engine built |
| **Schedule E** | Supplemental Income (K-1 rental) | Engine built |
| **Form 8995** | QBI Deduction (Section 199A) | Engine built |
| **Form 2555** | Foreign Earned Income Exclusion | Evaluation engine built |
| **Form 8959** | Additional Medicare Tax | Calculation built |
| **Form 7206** | SE Health Insurance Deduction | Not yet built |

## How to Use

### Phase 1: Document Collection

Drop all 2025 tax documents into `data-2025/`:

```
data-2025/
├── 1099-nec-lawfirm.pdf           # Primary 1099-NEC
├── k1-rental.pdf                   # Schedule K-1 from Denver rental
├── health-insurance/               # Premium payment records
├── estimated-payments/             # 1040-ES confirmations (Q1-Q4)
├── expenses-contracting/           # Business expenses for law firm LLC
│   ├── software-subscriptions.csv
│   ├── internet-phone.csv
│   ├── travel-receipts/
│   └── equipment/
├── expenses-docsherpa/             # Business expenses for DocSherpa LLC
│   ├── hosting.csv
│   ├── software.csv
│   └── other/
└── other/                          # Anything else potentially relevant
```

Also place prior returns for reference:
- `returns-2023/` — 2023 federal return PDF (1040 + all schedules)
- `returns-2024/` — 2024 federal return PDF (1040 + all schedules)

### Phase 2: Analysis (Claude Code)

Claude Code scans `data-2025/`, classifies every document, and produces a situation report:
- What documents were found and what they contain
- Which IRS forms are required and why
- What's missing that still needs to be provided
- Key decisions to make (FEIE, home office method, etc.)

### Phase 3: Interactive CPA Session (Claude Code)

Form-by-form walkthrough:
- Claude presents each line item with data from parsed documents
- Asks clarifying questions where needed (e.g., business use % for internet)
- Explains tax law reasoning in plain English
- Flags conservative vs. aggressive positions with dollar impact
- Shows the math for every number

### Phase 4: Optimization

- Compares FEIE vs. no FEIE (income tax savings vs. SE tax implications)
- Evaluates QBI deduction eligibility and phase-out
- Compares against 2023/2024 CPA returns for missed opportunities
- Flags audit risk items

### Phase 5: Output

Generated into `output/`:
- Completed IRS PDF forms (1040 + all schedules)
- `tax-summary.md` — plain English summary
- `line-detail.md` — every line item with calculation
- `optimization-analysis.md` — decisions made and alternatives considered
- `filing-checklist.md` — where to file, deadlines, e-file options
- `2026-estimated-payments.md` — recommended quarterly amounts

## Project Structure

```
taxman/
├── README.md                      # This file
├── TODO.md                        # Full project task tracker
├── REPO-EVALUATION.md             # Open-source repo research and evaluation
│
├── taxman/                        # Python package
│   ├── __init__.py
│   ├── constants.py               # 2025 tax brackets, rates, thresholds
│   ├── models.py                  # Data models (1099, K-1, Schedule C, profile)
│   ├── calculator.py              # Tax calculation engine
│   ├── parse_documents.py         # PDF document parser
│   ├── fill_forms.py              # IRS PDF form filler
│   └── reports.py                 # Report generation
│
├── repos/                         # Cloned reference repos (gitignored)
│   ├── habutax/                   # Python tax solver framework
│   ├── direct-file/               # IRS Fact Graph tax logic
│   ├── UsTaxes/                   # TypeScript tax filing app
│   ├── tax-logic-core/            # JS tax calc engine (2025 brackets)
│   ├── py1040/                    # Python 1040 calculator
│   ├── OpenTaxFormFiller/         # JSON-to-PDF form filler
│   └── PyPDFForm/                 # Python PDF form library
│
├── forms/                         # Downloaded IRS fillable PDFs (gitignored)
├── returns-2023/                  # 2023 prior return (gitignored)
├── returns-2024/                  # 2024 prior return (gitignored)
├── data-2025/                     # Source documents (gitignored)
├── output/                        # Generated forms and reports (gitignored)
└── scripts/                       # Utility scripts
```

## Python Package Details

### `constants.py` — 2025 Tax Law Constants

All values verified against IRS Revenue Procedure 2024-40 and the One Big Beautiful Bill Act of 2025 (OBBBA, P.L. 119-21, signed July 4, 2025).

Key values for this return:
- **MFS tax brackets:** 10/12/22/24/32/35/37% (TCJA rates, made permanent by OBBBA)
- **MFS 35% bracket cap:** $375,800 (not $394,600 — MFS ≠ half of MFJ for this bracket)
- **Standard deduction MFS:** $15,750 (OBBBA §101 raised from Rev. Proc. 2024-40's $15,000)
- **SE tax rate:** 15.3% (12.4% SS + 2.9% Medicare) on 92.35% of net SE income
- **SS wage base:** $176,100
- **Additional Medicare:** 0.9% on SE earnings above $125,000 (MFS threshold)
- **QBI threshold MFS:** $197,300 (above this, W-2 wage limitations apply)
- **FEIE exclusion:** $130,000 (excludes from income tax only, NOT SE tax)
- **SALT cap MFS:** $20,000 (OBBBA raised from $5,000)
- **Estimated tax safe harbor:** 110% of prior year tax (AGI > $75K MFS)

### `models.py` — Data Models

- `TaxpayerProfile` — master profile holding all data for the year
- `Form1099NEC` — 1099-NEC nonemployee compensation
- `ScheduleK1` — K-1 partner's share of income
- `ScheduleCData` — business data for Schedule C (income + expenses + home office)
- `BusinessExpenses` — categorized expenses matching Schedule C line items
- `HomeOffice` — simplified or regular method home office data
- `EstimatedPayment` — quarterly estimated tax payments
- `HealthInsurance` — self-employed health insurance premiums

### `calculator.py` — Tax Calculation Engine

Each function returns a result object with every line item, its amount, and an explanation.

- `calculate_schedule_c()` — business income/expenses, net profit
- `calculate_schedule_se()` — SE tax with SS/Medicare split, deductible half
- `calculate_schedule_e()` — rental/K-1 income from partnerships
- `calculate_qbi_deduction()` — Section 199A with phase-out logic
- `calculate_income_tax()` — progressive bracket calculation
- `calculate_additional_medicare()` — Form 8959 (0.9% above $125K MFS)
- `evaluate_feie()` — Form 2555 cost/benefit analysis
- `calculate_return()` — master function that builds the complete 1040
- `compare_feie_scenarios()` — side-by-side FEIE comparison
- `estimate_quarterly_payments()` — 2026 safe harbor calculations

### `parse_documents.py` — Document Parser

- `extract_text_from_pdf()` — raw text extraction
- `extract_pages_from_pdf()` — page-by-page extraction
- `extract_tables_from_pdf()` — table extraction
- `parse_1099_nec()` — structured 1099-NEC parsing
- `parse_k1_1065()` — structured K-1 parsing
- `parse_prior_return()` — prior year return parsing with form detection
- `scan_documents_folder()` — folder scan with document classification

### `fill_forms.py` — PDF Form Filler

- `download_irs_form()` — downloads official IRS fillable PDFs
- `inspect_form_fields()` / `inspect_form_fields_raw()` — discovers PDF field names
- `fill_form()` — fills a PDF form from a data dictionary
- `fill_and_flatten()` — fills and flattens (non-editable output)

### `reports.py` — Report Generator

- `generate_tax_summary()` — plain English return summary with effective rates
- `generate_line_detail()` — line-by-line calculation detail for every form
- `generate_filing_checklist()` — forms to file, deadlines, mailing addresses
- `generate_quarterly_plan()` — 2026 estimated payment recommendations

## Dependencies

```bash
pip install pypdf pdfplumber PyPDFForm
```

- **pypdf** — PDF reading and form field inspection
- **pdfplumber** — Text and table extraction from PDFs
- **PyPDFForm** — Pure Python PDF form filling (no pdftk needed)

## Important Tax Notes

1. **FEIE does NOT reduce SE tax.** Even if you exclude income via Form 2555, self-employment tax still applies to the full amount. Evaluate carefully whether FEIE actually saves money.

2. **MFS filers cannot claim the OBBBA senior bonus deduction** ($6,000 for age 65+).

3. **Additional Medicare Tax threshold for MFS is $125,000** — lower than the $200,000 employer withholding threshold. If your SE income exceeds $125K, you likely owe additional Medicare tax that was never withheld.

4. **QBI deduction phases out above $197,300** (MFS). With no W-2 wages paid by your business and no qualified property (UBIA), the deduction goes to $0 above $247,300. At ~$116K net SE income, you should be well below this.

5. **Colorado state filing** — you may have a CO filing obligation based on rental property income sourced to Colorado. Evaluate Form 104.

6. **Taxpayers abroad** get an automatic 2-month extension to June 15, 2026 (attach a statement to the return). Interest still accrues from April 15 on any balance owed.
