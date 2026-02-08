# Tax Man — TODO

## Completed

### Engine (Phase 1)
- [x] 2025 tax constants with OBBBA corrections
- [x] Data models with `__post_init__` validation
- [x] Tax calculation engine (Schedule C, SE, E, QBI, FEIE, 1040, NIIT, Additional Medicare)
- [x] PDF document parser (1099-NEC, K-1, W-2, 1098, 1095-A, charity)
- [x] IRS PDF form filler with `generate_all_forms()` pipeline
- [x] Report generator (summary, line detail, checklist, quarterly, FEIE comparison, prior year)
- [x] Input validation module (TIN, EIN, amounts, ranges, percentages)
- [x] Optimization engine (`generate_optimization_recommendations()`)
- [x] `pyproject.toml` with Hatchling build and `taxman` entry point

### Bug Fixes (Phase 1)
- [x] NIIT uses filing-status-specific thresholds (was hardcoded to MFS)
- [x] QBI deduction respects W-2 wages and UBIA limitations (was assuming zero)
- [x] FEIE stacking uses filing-status-specific brackets (was using default)
- [x] Quarterly payments respect filing status for high-income threshold
- [x] 1099-NEC uses labeled regex for payer/recipient TIN (was positional)
- [x] K-1 extracts Box 11, 13, 14 (was missing SE earnings and other boxes)
- [x] `FORMS_DIR` uses `Path(__file__)` with `TAXMAN_FORMS_DIR` env override (was hardcoded)
- [x] Reports are data-driven from profile and result (was hardcoded values)
- [x] `HomeOffice.internet_business_pct` normalizes >1 values to decimal
- [x] `inspect_form_fields` uses clean single iteration (was redundant logic)

### Testing (Phase 2)
- [x] 301 tests across 4 test files + fixtures
- [x] Calculator tests (136): brackets, SE tax, QBI, FEIE, NIIT, AMT, credits, QDCG worksheet, 1099-NEC routing, investment income, Schedule D, K-1 all boxes
- [x] Model tests (84): validation, properties, edge cases, parsing, form filling
- [x] Integration tests (61): full MFS/single/MFJ returns, consistency checks
- [x] Colorado tests (20): source income, Form 104, apportionment, SALT addback, pension/TABOR

### Document Parsing (Phase 3)
- [x] `ParseResult` wrapper with confidence, warnings, needs_manual_review
- [x] Multi-strategy extraction (regex + table + positional)
- [x] New parsers: W-2, 1098, 1095-A, charity receipts
- [x] Document validation (warn on $0 compensation, unusually high values)

### Interactive CLI (Phase 4)
- [x] Typer app with 6 commands (prepare, scan, review, export, compare, sessions)
- [x] 13-step Questionary wizard with save/resume
- [x] Rich display helpers (tables, panels, trees, progress bars)
- [x] Session state persistence (JSON to ~/.taxman/sessions/)
- [x] Config loading from ~/.taxman/config.toml

### Colorado State Tax (Phase 5)
- [x] Colorado Form 104 engine (4.4% flat rate)
- [x] CO-source income calculation (K-1 rental apportionment)
- [x] `calculate_full_return()` for federal + state

### Form Generation (Phase 6)
- [x] Field mapping modules (1040, Schedule C, Schedule E, Schedule SE, 8995, 2555)
- [x] Common formatting helpers (SSN, EIN, currency for PDF, checkboxes)
- [x] `generate_all_forms()` orchestration pipeline

### Engine Enhancements (Phase 7)
- [x] Home office regular method: mortgage interest + real estate taxes prorated by business %
- [x] Investment income: Form 1099-INT/DIV/B models, Lines 2a/2b/3a/3b/7 on 1040
- [x] Schedule D: capital gains/losses from 1099-B, K-1 Boxes 8/9a/10, 1099-DIV Box 2a; loss limitation ($3,000 / $1,500 MFS)
- [x] K-1 all boxes: Boxes 3, 6a/6b, 7, 8, 10, 11, 12, 13 handled in `calculate_schedule_e()`
- [x] QBI cap: IRC §199A(a) reduces by net capital gain (incl. qualified dividends)
- [x] Colorado Form 104: SALT addback for itemizers, TABOR subtraction, age-based pension subtraction
- [x] AMT (Form 6251): exemption with phaseout, 26%/28% rates, integrated into total_tax
- [x] Credits (Schedule 8812): CTC $2,500/child (OBBBA), ODC $500, ACTC refundable — with phaseout

### Codex Review Fixes (Phase 8)
- [x] QDCG Worksheet: `calculate_tax_with_qdcg_worksheet()` — qualified dividends + net LTCG taxed at preferential 0%/15%/20% rates using stacking method. LTCG thresholds (Rev. Proc. 2024-40) in constants.py. Integrated into `calculate_return()` when qual divs or net LTCG > 0.
- [x] 1099-NEC routing: auto-creates Schedule C from 1099-NEC total when `profile.businesses` is empty (uses local list — profile not mutated). NEC federal withholding added to payments sum.
- [x] FEIE integration: `compare_feie_scenarios()` returns `feie_result` (Form2555Result). Wizard Step 11 persists `self.result.feie` when beneficial, enabling Form 2555 PDF generation.
- [x] PDF field mappings: updated all 6 field_mappings files with real field names from 2025 IRS fillable PDFs discovered via `inspect_form_fields()`. Uses `f1_01[0]` format for PyPDFForm.

---

## Remaining

### Before Filing

- [x] **Discover real PDF field names** — ran `inspect_form_fields()` against 2025 IRS PDFs, updated all 6 field_mappings files
- [x] **Download 2025 IRS fillable PDFs** — placed in `forms/` (f1040, f1040sc, f1040sse, f1040se, f8995, f2555)
- [ ] **Visually verify PDF field mappings** — IRS does not label fields semantically; exact line-to-field mapping needs visual spot-check against filled test PDFs
- [ ] **Collect tax documents** — 1099-NEC, K-1, health insurance records, estimated payment confirmations, business expenses
- [ ] **Collect personal info** — SSN, foreign address, EINs, NAICS codes, property manager EIN
- [ ] **Parse prior returns** — 2023 and 2024 for comparison and safe harbor calculation
- [ ] **Verify OBBBA constants** — cross-check against final IRS publications (Pub 17, form instructions) when released

### Forms Not Yet Implemented (PDF field mappings)

- [ ] Schedule D — calculation exists but no PDF mapping
- [ ] Form 6251 (AMT) — calculation exists but no PDF mapping
- [ ] Schedule 8812 (CTC/ACTC) — calculation exists but no PDF mapping
- [ ] Form 7206 (SE health insurance deduction) — calculation exists but no PDF mapping
- [ ] Form 8829 (regular method home office) — if regular method chosen over simplified
- [ ] Form 4562 (depreciation) — if equipment purchases need Section 179
- [ ] Form 8960 (NIIT) — calculation exists but no PDF mapping
- [ ] Schedule 1 / Schedule 2 field mappings — adjustments and additional taxes

### Codex Review — Skipped Issues

A GPT Codex review identified 10 issues. We triaged and implemented the 4 highest-impact fixes (see Phase 8 above). The remaining 6 were deferred for these reasons:

- **Schedule A (itemized deductions)** — Skipped because our primary use case (self-employed MFS expat) almost always takes the standard deduction. SALT cap at $10K makes itemizing rarely beneficial for MFS. Would add significant complexity (mortgage interest, charitable contributions, medical expenses, SALT limitation) for a path most users won't take.
- **Session resume data rehydration** — `--resume` restores step tracking but not the TaxpayerProfile data collected in earlier steps. Skipped because it requires serializing/deserializing the full profile model graph (including nested K-1s, 1099s, businesses). Currently users must re-enter data if resuming. Low priority since the wizard completes in one sitting.
- **Document parsing → profile wiring** — `parse_documents.py` extracts data from PDFs but the results aren't automatically populated into TaxpayerProfile. Skipped because the wizard already has a manual review step (Step 4) where users confirm parsed values. Auto-wiring risks silently importing incorrect OCR results.
- **Schedule 1 / Schedule 2 field mappings** — These supplemental forms aggregate adjustments and additional taxes that are already calculated and placed on the correct 1040 lines. Skipped because the IRS accepts the 1040 with these amounts inline; the schedules are only strictly required for e-file.
- **Additional form PDFs** (Schedule D, Form 6251, Schedule 8812, Form 8960, Form 7206, Form 8829, Form 4562) — Calculations exist but no PDF field mappings. Skipped because each form requires downloading the IRS PDF, discovering field names, and building a mapping file. These can be added incrementally as needed.
- **EITC** — Stub exists but MFS filers are categorically disqualified. Not applicable to our primary use case.

### Nice to Have

- [x] ~~Capital gains preferential rates (qualified dividends/LTCG at 0%/15%/20%)~~ — Implemented in Phase 8 (QDCG worksheet)
- [ ] Schedule A (itemized deductions) — see Codex Review notes above
- [ ] Schedule B form generation (threshold tracking only)
- [ ] QBI loss carryforward tracking across tax years
- [ ] Suspended passive loss carryforward tracking
- [ ] MeF e-file XML generation (if feasible)
- [ ] Additional state tax support beyond Colorado
- [ ] Prior-year data import from parsed returns
- [ ] Expense receipt OCR (photos of receipts)
