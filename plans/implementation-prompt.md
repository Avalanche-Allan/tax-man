# Implementation Prompt — CLI Completeness (Issues #2–#5)

Paste everything below the line into a new Claude Code chat window.

---

Implement 4 issues for the tax-man project. These are CLI plumbing fixes — the tax calculation engine (306 tests, all passing) is correct and should NOT be modified. Read the plan files before writing any code.

## Execution Order (strict — #3 depends on #2)

1. **Issue #2** — Session resume / profile hydration
2. **Issue #3** — Wire export/review/compare commands
3. **Issue #4** — Document parsing integration
4. **Issue #5** — PDF field mapping validation tests

## Plans

All plans are in `plans/` with full phase breakdowns, code snippets, files to touch, tests needed, and definitions of done. Read them first:

- `plans/issue-2-session-resume.md`
- `plans/issue-3-export-command.md`
- `plans/issue-4-document-parsing-integration.md`
- `plans/issue-5-pdf-field-validation.md`

## Key Files You'll Need to Read

Before starting, read these files to understand the current state:

| File | What it contains |
|------|-----------------|
| `taxman/models.py` | All dataclasses: TaxpayerProfile, ScheduleCData, ScheduleK1, FormW2, Form1099NEC/INT/DIV/B, HealthInsurance, HomeOffice, Dependent, FilingStatus enum, etc. |
| `taxman/cli/state.py` | SessionState dataclass — save/load/list sessions to ~/.taxman/sessions/*.json |
| `taxman/cli/wizard.py` | TaxWizard with 13 _step_* methods, WIZARD_STEPS list, resume logic |
| `taxman/cli/app.py` | Typer CLI commands: prepare, review, export, compare, scan, sessions |
| `taxman/cli/display.py` | Rich display functions: display_tax_breakdown, display_result_panel, display_income_table |
| `taxman/calculator.py` | Form1040Result dataclass, calculate_return(), compare_feie_scenarios(), estimate_quarterly_payments() |
| `taxman/parse_documents.py` | ParseResult dataclass, parse_1099_nec(), parse_w2(), parse_k1_1065(), parse_1098_mortgage(), parse_1095_a(), parse_charity_receipt(), parse_prior_return(), scan_documents_folder() |
| `taxman/fill_forms.py` | generate_all_forms(), fill_form(), inspect_form_fields() |
| `taxman/field_mappings/` | build_*_data() functions for each form (f1040.py, f1040sc.py, f1040sse.py, f1040se.py, f8995.py, f2555.py, common.py) |
| `taxman/reports.py` | generate_tax_summary(), generate_line_detail_report(), generate_filing_checklist(), generate_quarterly_plan(), generate_feie_comparison_report() |

## Current Test Baseline

306 tests, all passing:
```
python3 -m pytest tests/ --tb=short
```

Test files:
- `tests/test_calculator.py` — 140 tests (engine logic)
- `tests/test_colorado.py` — 20 tests (CO state tax)
- `tests/test_integration.py` — 62 tests (end-to-end scenarios)
- `tests/test_models.py` — 84 tests (model validation)

## Constraints

1. **Do NOT modify the tax calculation engine** (`calculator.py` logic, `constants.py` values). It is correct and tested. You are only wiring up the CLI layer.
2. **Do NOT modify existing tests** unless a test is directly testing something you're changing (e.g., if you remove `income_data` from SessionState, update any test that references it).
3. **Run `python3 -m pytest tests/ --tb=short` after each issue** to ensure no regressions. All existing 306 tests must continue to pass.
4. **Commit after each issue** with a descriptive message. Do not batch all 4 into one commit.
5. **Follow existing code patterns**: the project uses dataclasses (not Pydantic), Rich for display, Typer for CLI, questionary for prompts, PyPDFForm for PDF filling.
6. For Issue #5 (field inventory tests), the tests need the actual IRS PDF files downloaded. Use `download_irs_form(form_key)` from `fill_forms.py` to ensure they're cached in `forms/` before running `inspect_form_fields()`. Mark these tests with `@pytest.mark.slow` or skip if PDFs aren't available.

## Issue #2 Summary — Session Resume

Create `taxman/cli/serialization.py` with serialize/deserialize functions for TaxpayerProfile and Form1040Result. Add `schema_version` and `profile_data` fields to SessionState. Save profile after each wizard step that mutates it. Rehydrate on resume. Persist calculation results after Step 10.

Key test: **resume parity** — prove that an interrupted+resumed wizard produces the same Form1040Result as an uninterrupted run.

## Issue #3 Summary — Export/Review/Compare

Wire `export` to call `generate_all_forms()` + report generators, writing files to output_dir. Wire `review` to call display functions with deserialized result. Wire `compare` to call `compare_feie_scenarios()`. All three should fail loudly with helpful messages when session data is missing.

## Issue #4 Summary — Document Parsing Integration

In `_step_document_review()`, dispatch confirmed documents to the matching `parse_*()` function. Store results. In `_step_income_review()`, call `_apply_parsed_results()` to populate the profile from parsed data, then let user confirm/edit/remove. Persist parsed documents to session.

## Issue #5 Summary — PDF Field Mapping Validation

Write `tests/test_field_mappings.py` with: (a) field inventory tests that assert our field names exist in the actual PDFs, (b) line-consistency math tests that verify build_*_data() output is internally consistent (e.g., Schedule C: Line 31 = Line 7 - Line 28 - Line 30), (c) golden-file snapshot tests that fill a PDF and verify known values appear in extracted text.
