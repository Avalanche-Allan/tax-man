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
- [x] 218 tests across 7 test files + fixtures
- [x] Calculator tests (~60): brackets, SE tax, QBI, FEIE, NIIT, quarterly estimates
- [x] Model tests (~40): validation, properties, edge cases
- [x] Validation tests (~30): TIN, EIN, ranges, percentages
- [x] Parser tests (~25): document classification, amount extraction
- [x] Integration tests (~20): full MFS/single/MFJ returns, consistency checks
- [x] Colorado tests (~13): source income, Form 104, apportionment
- [x] Fill forms tests (~5): paths, IRS URLs

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

---

## Remaining

### Before Filing

- [ ] **Discover real PDF field names** — run `inspect_form_fields_raw()` against 2025 IRS PDFs and update `taxman/field_mappings/` with actual field names (currently placeholders)
- [ ] **Download 2025 IRS fillable PDFs** — place in `forms/` (f1040, f1040sc, f1040sse, f1040se, f8995, f2555, etc.)
- [ ] **Collect tax documents** — 1099-NEC, K-1, health insurance records, estimated payment confirmations, business expenses
- [ ] **Collect personal info** — SSN, foreign address, EINs, NAICS codes, property manager EIN
- [ ] **Parse prior returns** — 2023 and 2024 for comparison and safe harbor calculation
- [ ] **Verify OBBBA constants** — cross-check against final IRS publications (Pub 17, form instructions) when released

### Forms Not Yet Implemented

- [ ] Form 7206 (SE health insurance deduction) — calculation exists but no PDF mapping
- [ ] Form 8829 (regular method home office) — if regular method chosen over simplified
- [ ] Form 4562 (depreciation) — if equipment purchases need Section 179
- [ ] Form 8960 (NIIT) — calculation exists but no PDF mapping
- [ ] Schedule 1 / Schedule 2 field mappings — adjustments and additional taxes

### Nice to Have

- [ ] QBI loss carryforward tracking across tax years
- [ ] Suspended passive loss carryforward tracking
- [ ] MeF e-file XML generation (if feasible)
- [ ] Additional state tax support beyond Colorado
- [ ] Prior-year data import from parsed returns
- [ ] Expense receipt OCR (photos of receipts)
