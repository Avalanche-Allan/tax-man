# Implementation Prompt — Codex Review Fixes (Batch 6)

Paste everything below the line into a new Claude Code chat window.

---

Fix 6 bugs found by Codex review of the CLI layer. These are all CLI/wizard/plumbing fixes — the tax calculation engine (361 tests, all passing) is correct and should NOT be modified. The fixes are ordered P1 first, then P2, then P3.

## Execution Order

1. **Fix 1 (P1)** — Parsed document prefill lost on resume
2. **Fix 2 (P1)** — K-1 parsed detail overwritten in income step
3. **Fix 3 (P2)** — Quarterly plan uses placeholder prior_year_tax
4. **Fix 4 (P2)** — Foreign-income "not abroad" branch skips profile save
5. **Fix 5 (P2)** — SSN split field mapping is guessed
6. **Fix 6 (P3)** — generated_forms list set but not saved

## Current State

All 4 previous CLI issues (#2–#5) are complete and committed. The codebase has:
- Full profile serialization/deserialization (`taxman/cli/serialization.py`)
- Wired export/review/compare commands (`taxman/cli/app.py`)
- Document parsing integration in wizard (`taxman/cli/wizard.py`)
- PDF field mapping validation tests (`tests/test_field_mappings.py`)

## Key Files You'll Need to Read

| File | What it contains |
|------|-----------------|
| `taxman/cli/wizard.py` | TaxWizard class — `__init__` (line 97), `_apply_parsed_results` (line 336), `_step_income_review` (line 410), `_step_foreign_income` (line 599), `_step_generate_forms` (line 693) |
| `taxman/cli/app.py` | Typer CLI commands — `export()` calls `generate_quarterly_plan(..., prior_year_tax=0.0, ...)` at line 162 |
| `taxman/cli/state.py` | SessionState — `parsed_documents` list, `generated_forms` list, `save()` |
| `taxman/cli/serialization.py` | `serialize_profile()`, `deserialize_profile()`, `serialize_result()`, `deserialize_result()` |
| `taxman/field_mappings/f1040.py` | SSN split mapping with guess comment at line 42 |
| `taxman/models.py` | TaxpayerProfile, ScheduleK1 (all K-1 box fields), FormW2, Form1099NEC, etc. |
| `taxman/parse_documents.py` | ParseResult dataclass, parse_k1_1065() — returns ScheduleK1 with all boxes |

## Current Test Baseline

361 tests, all passing:
```
python3 -m pytest tests/ --tb=short
```

Test files:
- `tests/test_calculator.py` — calculator engine tests
- `tests/test_cli_commands.py` — export/review/compare tests
- `tests/test_colorado.py` — CO state tax tests
- `tests/test_field_mappings.py` — PDF field mapping validation
- `tests/test_integration.py` — end-to-end scenarios
- `tests/test_models.py` — model validation
- `tests/test_serialization.py` — session serialization round-trips
- `tests/test_wizard_parsing.py` — document parsing integration

## Constraints

1. **Do NOT modify the tax calculation engine** (`calculator.py` logic, `constants.py` values).
2. **Do NOT modify existing tests** unless directly testing something you're changing.
3. **Run `python3 -m pytest tests/ --tb=short` after each fix** — all 361 existing tests must continue to pass.
4. **Commit after each fix** (or batch closely related fixes) with a descriptive message.
5. **Follow existing patterns**: dataclasses (not Pydantic), Rich, Typer, questionary, PyPDFForm.
6. **Write tests for each fix** — add them to the appropriate existing test file or create a new one if needed.

---

## Fix 1 (P1): Parsed document prefill lost on resume

**Problem:** `TaxWizard.__init__` (line 104) initializes `self.parsed_results = []` unconditionally. On resume, `session.parsed_documents` contains saved parse results, but they are never rehydrated into `self.parsed_results`. So `_apply_parsed_results()` (line 342) has nothing to apply.

**Impact:** User scans/parses documents, quits, resumes at Step 5/6 — all document-derived prefill silently disappears.

**Fix:** In `__init__`, after rehydrating profile and result, rebuild `self.parsed_results` from `self.session.parsed_documents`. Each entry is a dict with keys `type`, `confidence`, `needs_manual_review`, `warnings`, `data`, `source_file`. Reconstruct `ParseResult` objects with the appropriate model instances (FormW2, Form1099NEC, ScheduleK1, Form1098) based on the `type` field.

**Files to modify:** `taxman/cli/wizard.py`

**Test:** Add a test to `tests/test_wizard_parsing.py` that saves parsed results to a session, creates a new TaxWizard with that session, and verifies `self.parsed_results` is populated and `_apply_parsed_results()` works.

---

## Fix 2 (P1): K-1 parsed detail overwritten in income step

**Problem:** `_step_income_review` (line 465) resets `self.profile.schedule_k1s = []` and only re-collects `partnership_name` + `net_rental_income` (line 475). This drops all other parsed K-1 fields: `ordinary_business_income` (Box 1), `guaranteed_payments` (Box 4), `interest_income` (Box 5), `capital_gains` (Boxes 8/9a), `section_1231_gain` (Box 10), `other_income` (Box 11), and distribution/tax fields (Boxes 13/14).

**Impact:** Parser integration correctly populates rich K-1 data, but Step 6 wipes it all to just two fields.

**Fix:** When the user already has K-1s populated (from parsing), present the existing data for confirmation/editing instead of wiping and re-collecting from scratch. If user chooses to edit a K-1, let them modify specific fields. If adding new K-1s manually (no parsed data), the current simple collection is fine as a starting point — but don't overwrite parsed K-1s.

**Files to modify:** `taxman/cli/wizard.py`

**Test:** Add a test to `tests/test_wizard_parsing.py` that populates K-1s via `_apply_parsed_results()`, then verifies the K-1 data survives (or is properly merged) rather than being wiped.

---

## Fix 3 (P2): Exported quarterly plan uses placeholder prior_year_tax

**Problem:** `export()` in `app.py` (line 162) calls `generate_quarterly_plan(result.total_tax, 0.0, result.agi, ...)` — hardcoded `prior_year_tax=0.0`. This makes the safe-harbor calculation (110% of prior year) meaningless.

**Impact:** The quarterly_plan.txt output is not decision-grade for tax planning.

**Fix:** Add `prior_year_tax` as an optional field on TaxpayerProfile (or SessionState). Collect it in the wizard (Step 8 deductions area or a new substep). Pass the real value to `generate_quarterly_plan()`. If not available, default to 0.0 but include a warning in the output.

**Files to modify:** `taxman/models.py` (add field), `taxman/cli/wizard.py` (collect it), `taxman/cli/app.py` (pass it), `taxman/cli/serialization.py` (serialize it)

**Test:** Add a test to `tests/test_cli_commands.py` that verifies the quarterly plan uses a real prior_year_tax value when available.

---

## Fix 4 (P2): Foreign-income "not abroad" branch skips profile save

**Problem:** `_step_foreign_income` (line 607) returns early when user says "not abroad" without calling `self._save_profile()`. The profile mutation (`days_in_foreign_country_2025 = 0`) is not persisted.

**Impact:** On resume, the foreign income state can be stale/inconsistent.

**Fix:** Add `self._save_profile()` before the early return at line 609.

**Files to modify:** `taxman/cli/wizard.py`

**Test:** Add a test that verifies the profile is saved when user says "not abroad" (mock save and verify it's called, or check session state).

---

## Fix 5 (P2): SSN split field mapping is guessed

**Problem:** In `f1040.py` line 42, the SSN split across `f1_03`/`f1_05` includes a `# This is a guess` comment. The actual IRS field layout for the 2025 1040 may differ.

**Impact:** SSN digits could be placed in wrong fields on the generated PDF.

**Fix:** Use `inspect_form_fields()` from `fill_forms.py` to examine the actual 2025 f1040 PDF field schema and determine the correct SSN field mapping. Update the mapping to match reality, or if the fields truly can't be determined from the schema, map only the full SSN to `f1_16[0]` and remove the guessed split. Remove the guess comment either way.

**Files to modify:** `taxman/field_mappings/f1040.py`

**Test:** Add a test to `tests/test_field_mappings.py` that verifies no field mapping file contains the word "guess" (defensive lint test).

---

## Fix 6 (P3): generated_forms list set but not saved

**Problem:** `_step_generate_forms` (line 730) sets `self.session.generated_forms = [str(output_path)]` but never calls `self.session.save()`.

**Impact:** Minor state-tracking inconsistency — generated_forms won't survive restart.

**Fix:** Add `self.session.save()` after setting `generated_forms`.

**Files to modify:** `taxman/cli/wizard.py`

**Test:** Add a test that verifies session is saved after form generation step.
