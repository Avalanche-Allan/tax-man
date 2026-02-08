# Issue #3: Wire Up `taxman export`, `review`, and `compare` Commands

## Problem
`taxman export` validates session/results then prints "Export complete" without actually calling
form generation or report output. `taxman review` dumps raw dict. `taxman compare` is a stub.

## Dependency
Requires Issue #2 (session resume) to be implemented first, specifically:
- `session.results` must be populated by the wizard (Phase 5 of Issue #2)
- `session.profile_data` must be populated so we can reconstruct `TaxpayerProfile`
- `deserialize_profile()` and `deserialize_result()` must exist (Phase 1 of Issue #2)

## Plan

### Phase 1: Wire `export` to generate PDFs + reports
1. In `app.py:export()`, after loading session:
   ```python
   from taxman.cli.serialization import deserialize_profile, deserialize_result
   profile = deserialize_profile(session.profile_data)
   result = deserialize_result(session.results)
   ```
2. Call `generate_all_forms(result, profile, output_dir)` from `fill_forms.py`.
3. Call report generators and write to files:
   - `generate_tax_summary(result, profile)` → `output_dir/tax_summary.txt`
   - `generate_line_detail_report(result)` → `output_dir/line_detail.txt`
   - `generate_filing_checklist(result, profile)` → `output_dir/filing_checklist.txt`
   - `generate_quarterly_plan(result.total_tax, ...)` → `output_dir/quarterly_plan.txt`
4. Print actual list of generated files with sizes.
5. Fail loudly with specific error if `session.profile_data` or `session.results` is empty:
   ```
   Error: Session has no calculated results. Run 'taxman prepare' first to complete the wizard.
   ```

### Phase 2: Wire `review` to display computed results
6. In `app.py:review()`, reconstruct objects:
   ```python
   result = deserialize_result(session.results)
   ```
7. Call display functions from `cli/display.py`:
   - `display_income_table(result.schedule_c_results, result.schedule_e)`
   - `display_tax_breakdown(result)`
   - `display_result_panel(result)`
8. Also display: filing status, total income, AGI, deduction, taxable income, total tax,
   refund/amount owed — the key numbers a user wants to see at a glance.

### Phase 3: Wire `compare` to run FEIE comparison
9. In `app.py:compare()`, reconstruct profile:
   ```python
   profile = deserialize_profile(session.profile_data)
   ```
10. Call `compare_feie_scenarios(profile)` and `generate_feie_comparison_report(scenarios)`.
11. Display the comparison report.

### Tests needed
- **Export integration**: create session with known profile+results, call export, verify:
  - PDF files exist on disk (or at least attempted — PDF download may fail in CI)
  - Report text files exist and contain expected strings
- **Review output**: verify display functions are called with correct reconstructed data
- **Compare output**: verify FEIE comparison report is generated
- **Error handling**: verify clear error when session has no results, no profile_data

### Definition of done
1. `taxman export <session>` emits report files and attempts PDF generation.
2. `taxman review <session>` displays meaningful computed return sections.
3. `taxman compare <session>` displays FEIE with/without comparison.
4. All three fail with helpful messages when session data is missing.

### Estimated scope
- `cli/app.py`: ~60 lines across export/review/compare
- Tests: ~50 lines

### Files touched
- `taxman/cli/app.py`
- `tests/test_cli_commands.py` (new or extend existing)
