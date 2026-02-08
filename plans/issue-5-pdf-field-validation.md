# Issue #5: PDF Field Mapping Validation

## Problem
Field mappings use `f1_XX[0]` names discovered via `inspect_form_fields()`, but IRS does not
label fields semantically. The SSN field split logic is acknowledged as a guess. There is no
automated way to verify that `f1_47[0]` is actually Line 1a (wages) vs. some other field.

## What Codex got wrong
The Schedule C "double-count" claim is incorrect. `total_expenses` does not include home office —
Line 28 is expenses *before* home office, Line 30 is home office deduction separately. This is
correct IRS form math: Line 31 = Line 7 - Line 28 - Line 30.

## What is actually risky
1. **SSN field splitting** (`f1040.py:39-43`): The 3-part SSN → multi-field mapping is guessed.
   IRS splits SSN across fields with varying maxLength (2/2/4 or 3/2/4 depending on year).
2. **Field ordering assumptions**: `f1_47[0]` might be Line 1a on the 2025 PDF but could shift
   if IRS adds or removes fields in a revision.
3. **No golden-file tests**: We fill forms but never verify the output visually or with snapshot
   comparison.

## Plan

### Phase 1: Visual spot-check (manual, one-time)
1. Generate filled PDFs for the `mfs_expat` test fixture with known values.
2. Open each PDF and visually verify that values appear in the correct lines.
3. Document corrections needed directly in code comments.

This is inherently a manual step — no code can verify "does $50,000 appear on Line 1a?"
without a known-correct reference.

### Phase 2: Field inventory tests
4. Write tests that call `inspect_form_fields(form_key)` for each form and assert the field
   names we use actually exist in the PDF. This catches IRS form revisions immediately.
   ```python
   def test_f1040_expected_fields_exist():
       fields = inspect_form_fields("f1040")
       # Spot-check critical fields used in build_1040_data()
       for key in ["f1_01[0]", "f1_02[0]", "f1_47[0]", "f1_65[0]", "f2_09[0]"]:
           assert key in fields, f"Field {key} missing from f1040 PDF"

   def test_f1040sc_expected_fields_exist():
       fields = inspect_form_fields("f1040sc")
       for key in ["f1_10[0]", "f1_41[0]", "f1_43[0]", "f1_44[0]"]:
           assert key in fields, f"Field {key} missing from Schedule C PDF"
   ```
5. Run for all 6 form types: f1040, f1040sc, f1040sse, f1040se, f8995, f2555.

### Phase 3: Line-consistency tests (math validation)
6. Write tests that verify the *values* written to PDF fields are mathematically consistent,
   independent of whether they land on the correct visual line. This catches logic bugs in the
   field mapping builders.
   ```python
   def test_schedule_c_line_math_consistency():
       """Line 28 + Line 30 subtracted from Line 7 should equal Line 31."""
       data = build_schedule_c_data(sc_result, biz_data, profile)
       line7 = parse_currency(data["f1_16[0]"])     # gross income
       line28 = parse_currency(data["f1_41[0]"])     # total expenses
       line30 = parse_currency(data.get("f1_43[0]", "0"))  # home office
       line31 = parse_currency(data["f1_44[0]"])     # net profit
       assert line31 == line7 - line28 - line30

   def test_1040_total_tax_consistency():
       """Tax + SE tax + additional medicare should flow to total tax."""
       data = build_1040_data(result, profile)
       # Verify key summary lines are internally consistent
   ```
7. Cover: Schedule C (lines 7/28/30/31), Schedule SE (lines 4/6/10/12), Form 1040 (income
   lines sum to total income, tax lines sum to total tax).

### Phase 4: Golden-file snapshot tests
8. After visual verification (Phase 1), write snapshot tests that:
   - Generate a PDF with deterministic test data
   - Extract text from the generated PDF (via pdfplumber)
   - Assert known values appear (e.g., "50,000" appears in output)
   - This doesn't verify position but catches field name regressions
9. If IRS updates the PDF (new field names), tests will fail and force re-mapping.

### Phase 5: SSN field fix
10. After visual verification, fix the SSN split logic if it's wrong. If IRS uses a single
    full-SSN field, simplify to just that. If it's split 3/2/4, update accordingly.
11. Remove the "this is a guess" comment once verified.

### Tests needed (summary)
- Field inventory: ~6 tests (one per form), ~50 lines
- Line-consistency math: ~4 tests (Sch C, Sch SE, 1040 income, 1040 tax), ~60 lines
- Golden-file snapshots: ~3 tests (1040, Sch C, Sch SE), ~40 lines

### Definition of done
1. Field inventory tests fail on unknown/missing field names (catches IRS PDF revisions).
2. Line-consistency tests verify math relationships between filled fields.
3. Generated PDFs pass visual spot-check for representative fixtures.

### Estimated scope
- Phase 1: Manual, ~1 hour
- Phase 2: ~50 lines of test code
- Phase 3: ~60 lines of test code
- Phase 4: ~40 lines of test code
- Phase 5: ~5 lines if needed

### Files touched
- `tests/test_field_mappings.py` (new)
- `taxman/field_mappings/f1040.py` (SSN fix if needed)
- `taxman/field_mappings/common.py` (possibly add `parse_currency` test helper)

### Note
This is the lowest-priority item because it only affects PDF output appearance, not tax
calculation correctness. The engine is correct; only the form-filling presentation layer is at
risk.
