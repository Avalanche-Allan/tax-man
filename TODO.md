# Tax Man — Project TODO

Full task tracker for preparing the 2025 federal tax return.

---

## Phase 0: Infrastructure

- [x] Research and evaluate open-source tax repos (7 repos analyzed)
- [x] Clone reference repos (habutax, direct-file, UsTaxes, tax-logic-core, py1040, OpenTaxFormFiller, PyPDFForm)
- [x] Build Python package structure (`taxman/`)
- [x] Build data models (`models.py`)
- [x] Build 2025 tax constants with OBBBA corrections (`constants.py`)
- [x] Build tax calculation engine (`calculator.py`)
- [x] Build PDF document parser (`parse_documents.py`)
- [x] Build IRS PDF form filler (`fill_forms.py`)
- [x] Build report generator (`reports.py`)
- [x] Smoke test full calculation pipeline with sample data
- [x] Code audit: fix all critical bugs (10 bugs found, all fixed)
- [x] Code audit: fix code quality issues (wildcard imports, rounding, enum consistency)
- [x] Re-smoke test after all fixes — all checks pass
- [ ] Create GitHub repo (`taxman` under Avalanche-Allan)
- [ ] Initial commit and push

### Bugs Fixed in Code Audit

- [x] **BUG-1**: `HomeOffice` missing `regular_deduction` property — added with business% calculation
- [x] **BUG-2**: `BusinessExpenses.total` counted meals at 100% — now applies 50% per IRC §274(n)
- [x] **BUG-3**: SE threshold used `> 400` — fixed to `>= SE_MINIMUM_INCOME` per IRS rules
- [x] **BUG-4**: FEIE stacking used raw earned income — now uses actual taxable income and computed tax
- [x] **BUG-5/6/7**: K-1 only flowed Box 2 (rental) — now handles Boxes 1, 4, 5, 9a, 14
- [x] **BUG-8/9**: Brackets, QBI threshold, Addl Medicare all hardcoded to MFS — parameterized with filing status lookup dicts
- [x] **BUG-10**: `fill_and_flatten()` didn't flatten — now uses PyPDFForm `flatten=True` kwarg
- [x] **TAX-1**: SE health insurance deduction wasn't limited by net income minus deductible SE tax
- [x] **TAX-4**: Added NIIT calculation (3.8% on net investment income above $125K MFS)
- [x] **TAX-6**: Added MFS passive activity loss suspension — rental losses suspended per IRC §469(i)(5)(B)
- [x] **Code quality**: Replaced wildcard imports with explicit imports in calculator.py and reports.py
- [x] **Code quality**: FilingStatus enum values matched to STANDARD_DEDUCTION dict keys
- [x] **Code quality**: Consistent rounding throughout calculator

---

## Phase 1: Document Collection

### Documents Needed from Taxpayer

- [ ] **2023 federal tax return** (PDF) — place in `returns-2023/`
- [ ] **2024 federal tax return** (PDF) — place in `returns-2024/`
- [ ] **1099-NEC** from law firm (2025) — place in `data-2025/`
- [ ] **Schedule K-1** from Denver rental property (2025) — place in `data-2025/`
- [ ] **Health insurance premium records** (2025) — place in `data-2025/`
- [ ] **Estimated tax payment confirmations** (Q1–Q4 2025) — place in `data-2025/`
- [ ] **Business expense records** for law firm LLC — place in `data-2025/expenses-contracting/`
- [ ] **Business expense records** for DocSherpa LLC — place in `data-2025/expenses-docsherpa/`
- [ ] **Home office details** (square footage, months used)
- [ ] **Days physically present** in Mexico during 2025 (for FEIE evaluation)
- [ ] **Days physically present** in the US during 2025

### Information Needed (No Document)

- [ ] Full legal name, SSN, date of birth
- [ ] Current foreign address (Mexico City)
- [ ] Spouse's name and ITIN (if applicable)
- [ ] EIN for each LLC (law firm contracting LLC, DocSherpa LLC)
- [ ] NAICS business activity codes for each LLC
- [ ] Property management company name + EIN (Denver rental)
- [ ] Bank account info for direct deposit refund (if applicable)
- [ ] 2024 total tax liability (for estimated payment safe harbor calculation)

---

## Phase 2: Parse Prior Returns

- [ ] Parse 2023 federal return PDF into structured data
  - [ ] Identify all forms/schedules filed
  - [ ] Extract every line item with amounts
  - [ ] Document CPA's approach for each area
- [ ] Parse 2024 federal return PDF into structured data
  - [ ] Identify all forms/schedules filed
  - [ ] Extract every line item with amounts
  - [ ] Document CPA's approach for each area
- [ ] Compare 2023 vs 2024 for trends and changes
- [ ] Flag potential optimization opportunities CPA may have missed
- [ ] Save parsed data as JSON for reference during 2025 preparation

---

## Phase 3: Build 2025 Return

### Income

- [ ] Parse 1099-NEC and populate Schedule C #1 (law firm LLC)
- [ ] Collect DocSherpa LLC revenue and populate Schedule C #2
- [ ] Parse K-1 and populate Schedule E
- [ ] Verify no other income sources

### Business Expenses (Schedule C #1 — Law Firm LLC)

- [ ] Categorize all expenses into Schedule C line items
- [ ] Determine home office deduction method (simplified vs. regular)
- [ ] Calculate home office deduction
- [ ] Review internet/phone business use percentage
- [ ] Review travel expenses and documentation
- [ ] Review software/subscription expenses
- [ ] Review meals (50% deductible)
- [ ] Review any equipment purchases (Section 179 / depreciation)
- [ ] Calculate total expenses and net profit

### Business Expenses (Schedule C #2 — DocSherpa LLC)

- [ ] Categorize all expenses (hosting, software, etc.)
- [ ] Calculate net profit/loss
- [ ] Evaluate whether to take a loss (audit risk vs. legitimate business)

### Self-Employment Tax (Schedule SE)

- [ ] Calculate combined net SE earnings from both Schedule C's + K-1 Box 14
- [ ] Compute SE tax (SS + Medicare portions)
- [ ] Compute deductible half of SE tax
- [ ] Evaluate Additional Medicare Tax (Form 8959) if SE > $125K

### Deductions and Adjustments

- [ ] Apply standard deduction ($15,750 MFS)
- [ ] Calculate self-employed health insurance deduction (Schedule 1, Line 17)
- [ ] Calculate QBI deduction (Form 8995)
  - [ ] Determine if below/above $197,300 threshold
  - [ ] If above, evaluate W-2 wage / UBIA limitations
- [ ] Verify no other applicable adjustments

### FEIE Evaluation (Form 2555)

- [ ] Confirm physical presence test (330 days abroad in 12-month period)
- [ ] Calculate tax WITH FEIE (stacking method)
- [ ] Calculate tax WITHOUT FEIE
- [ ] Compare total tax liability under both scenarios
- [ ] Document recommendation with reasoning
- [ ] If beneficial, complete Form 2555

### Tax Calculation

- [ ] Calculate taxable income (AGI - deductions - QBI)
- [ ] Calculate income tax from MFS brackets
- [ ] Add self-employment tax
- [ ] Add Additional Medicare Tax (if applicable)
- [ ] Add NIIT (if applicable)
- [ ] Calculate total tax
- [ ] Apply estimated payment credits
- [ ] Determine refund or amount owed

### Optimization Analysis

- [ ] Compare 2025 return against 2023 CPA return — flag differences
- [ ] Compare 2025 return against 2024 CPA return — flag differences
- [ ] Evaluate all deduction strategies
- [ ] Document conservative vs. aggressive positions taken
- [ ] Flag any audit risk items with reasoning
- [ ] Estimate potential savings from any missed opportunities

---

## Phase 4: Generate Output

### PDF Forms

- [ ] Download 2025 IRS fillable PDFs (f1040, f1040sc, f1040sse, f1040se, f8995, etc.)
- [ ] Map PDF field names for each form
- [ ] Build field-mapping dictionaries (calculated values → PDF fields)
- [ ] Fill Form 1040
- [ ] Fill Schedule 1
- [ ] Fill Schedule 2
- [ ] Fill Schedule C #1 (law firm)
- [ ] Fill Schedule C #2 (DocSherpa)
- [ ] Fill Schedule SE
- [ ] Fill Schedule E
- [ ] Fill Form 8995 (QBI)
- [ ] Fill Form 2555 (if taking FEIE)
- [ ] Fill Form 8959 (if Additional Medicare Tax applies)
- [ ] Fill Form 8960 (if NIIT applies)
- [ ] Flatten all PDFs
- [ ] Assemble complete return package

### Reports

- [ ] Generate tax summary (`output/tax-summary.md`)
- [ ] Generate line-by-line detail (`output/line-detail.md`)
- [ ] Generate optimization analysis (`output/optimization-analysis.md`)
- [ ] Generate filing checklist (`output/filing-checklist.md`)
- [ ] Generate 2026 estimated payment plan (`output/2026-estimated-payments.md`)

---

## Phase 5: Filing

- [ ] Review complete return for accuracy
- [ ] Verify all math against IRS instructions
- [ ] Determine filing method (e-file vs. paper)
- [ ] If e-file: identify MeF-approved software that supports MFS + foreign address
- [ ] If paper: print, sign, and mail to IRS Austin
- [ ] File return by deadline (June 15, 2026 with abroad auto-extension)
- [ ] Pay any balance owed by April 15, 2026 (to avoid interest)
- [ ] Set up 2026 Q1 estimated payment

---

## Phase 6: State Filing

- [ ] Evaluate Colorado filing obligation (rental property income)
- [ ] If required: prepare CO Form 104
- [ ] Determine CO-source income from K-1
- [ ] File CO return if needed

---

## Engine Improvements (As Needed)

- [ ] Add Form 7206 calculation (SE health insurance deduction form)
- [ ] Add Form 8829 calculation (regular method home office)
- [ ] Add Form 4562 support (depreciation, if equipment purchases)
- [ ] Add Form 8960 field mapping (NIIT)
- [ ] Add Colorado Form 104 support
- [ ] Improve PDF parser for varied 1099/K-1 formats
- [ ] Add validation checks (cross-form consistency)
- [ ] Add prior-year comparison report
- [ ] Add QBI loss carryforward tracking across tax years
- [ ] Verify OBBBA constants against final IRS publications when available

---

## Known Issues and Caveats

1. **Cannot download from irs.gov** in this environment (proxy blocks it). IRS PDFs must be downloaded locally or in a different environment.

2. **Cannot create GitHub repos** from this environment (commit signing server only recognizes authorized repos).

3. **OBBBA constants need final verification.** Some provisions have different effective dates or may have been amended. Cross-check against official IRS publications (Pub 17, form instructions) when they're released for 2025.

4. **FEIE stacking calculation.** Now uses actual taxable income and computed tax for the stacking method. The excluded portion is taxed at the bottom of the bracket stack. Edge cases (e.g., FEIE + capital gains) may need additional work.

5. **QBI deduction for losses.** If DocSherpa LLC has a net loss, its negative QBI reduces the total QBI from the law firm LLC. The engine handles this correctly. QBI loss carryforward across years is not yet implemented.

6. **Rental property depreciation.** The K-1 should report depreciation already factored in. Verify that Schedule E correctly flows the K-1 amounts without double-counting.

7. **MFS passive rental losses.** Rental losses are correctly suspended for MFS filers ($0 passive loss allowance per IRC §469(i)(5)(B)). Suspended losses carry forward but tracking is not yet implemented.

8. **NIIT threshold.** Currently hardcoded to MFS $125K threshold. Should be parameterized if filing status changes.
