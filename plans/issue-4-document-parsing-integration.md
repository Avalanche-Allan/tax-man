# Issue #4: Wire Document Parsing into Wizard Workflow

## Problem
Wizard calls `scan_documents_folder()` to classify documents and shows the user a confirmation
UI, but parsed data is never converted into model objects or fed into `TaxpayerProfile`. The
parse functions (`parse_1099_nec`, `parse_w2`, `parse_k1_1065`, etc.) exist and return
`ParseResult` objects with model instances, but are never called from the wizard.

## Current Flow
1. Step 3 (`document_scan`): Calls `scan_documents_folder()` → classification only
2. Step 4 (`document_review`): Shows classified docs, user confirms each
3. Step 6 (`income_review`): User manually enters all income via prompts

## Desired Flow
1. Step 3: Scan and classify (unchanged)
2. Step 4: For each confirmed document, parse it and show extracted values + confidence
3. Step 6: Pre-populate profile with parsed data, let user review/override

## Dependency
- Benefits from Issue #2 (session resume) so parsed data survives resume.
- Can be implemented independently — parsed data just won't survive a quit/resume until #2 lands.

## Plan

### Phase 1: Parse confirmed documents
1. In `_step_document_review()`, after user confirms a document, call the matching parser:
   ```python
   PARSERS = {
       "1099-NEC": parse_1099_nec,
       "W-2": parse_w2,
       "K-1": parse_k1_1065,
       "1098": parse_1098_mortgage,
       "1095-A": parse_1095_a,
       "Charity Receipt": parse_charity_receipt,
   }
   parser = PARSERS.get(doc["classification"])
   if parser:
       try:
           parse_result = parser(doc["path"])
           self.parsed_results.append(parse_result)
           self._display_parse_result(parse_result)
       except Exception as e:
           console.print(f"[yellow]Could not parse {doc['name']}: {e}[/yellow]")
   ```
2. Add `self.parsed_results: list[ParseResult] = []` to wizard `__init__`.

### Phase 2: Profile population layer
3. Write `_apply_parsed_results(self)` method, called at the start of `_step_income_review()`:
   ```python
   for pr in self.parsed_results:
       if isinstance(pr.data, Form1099NEC):
           self.profile.forms_1099_nec.append(pr.data)
       elif isinstance(pr.data, FormW2):
           self.profile.forms_w2.append(pr.data)
       elif isinstance(pr.data, ScheduleK1):
           self.profile.schedule_k1s.append(pr.data)
       # etc.
   ```
4. Display what was populated:
   ```
   Pre-populated from documents:
     2 W-2s (confidence: 0.92, 0.87)
     1 1099-NEC (confidence: 0.95)
     1 K-1 (confidence: 0.78 ⚠ needs review)
   ```
5. For `parse_result.needs_manual_review` or confidence < 0.7, flag for user attention.

### Phase 3: Pre-populate income review with edit capability
6. In `_step_income_review()`, if profile already has forms from parsing:
   - Display each parsed form with key values
   - Ask user to confirm or edit each:
     ```
     W-2 from Acme Corp: Wages $52,000, Federal withholding $8,500
     [Confirm] [Edit] [Remove]
     ```
   - Only prompt for manual entry of form types not found in documents
7. For K-1s with low confidence, show warnings and parsed values side-by-side for user to verify.

### Phase 4: Persist parsed documents to session
8. Save parsed results to `session.parsed_documents` for resume support:
   ```python
   self.session.parsed_documents = [
       {"type": pr.document_type, "file": pr.source_file,
        "confidence": pr.confidence, "warnings": pr.warnings,
        "data": asdict(pr.data) if pr.data else None}
       for pr in self.parsed_results
   ]
   self.session.save()
   ```
9. On resume, rehydrate `self.parsed_results` from session (requires Issue #2 serialization
   module for model reconstruction).

### Phase 5: Prior return parsing
10. If a "Prior Return" document is found, parse it via `parse_prior_return()` to extract
    `prior_year_tax` — needed for quarterly estimated tax safe harbor calculation.
11. Store in `self.profile.prior_year_tax` (may need to add this field to TaxpayerProfile).

### Tests needed
- **Parser dispatch**: Mock `parse_w2()` etc., confirm the right parser is called for each
  classification type.
- **Profile population**: Given a list of ParseResults, verify profile.forms_w2,
  profile.schedule_k1s, etc. are populated correctly.
- **Low-confidence handling**: Verify warnings are surfaced when confidence < 0.7.
- **Parse failure graceful**: Verify that a parser exception doesn't crash the wizard.
- **Round-trip**: parse → save to session → restore on resume → verify data intact.
- **Pre-populate**: Verify Step 6 skips manual entry prompts for already-parsed form types.

### Edge cases
- Multiple W-2s from same employer (keep separate — different EINs mean different employers)
- Parser returns confidence < 0.5 — show warning, still apply but mark for review
- Parser fails on malformed/encrypted PDF — graceful error, fall back to manual entry
- Document classified as "unknown" — skip parsing, no error
- Prior return parsing — useful for `prior_year_tax` in quarterly estimates

### Definition of done
1. A folder with W-2/1099/K-1 PDFs pre-populates the wizard profile with extracted values.
2. User can confirm, edit, or remove each extracted form before calculation.
3. Parse failures are handled gracefully with fallback to manual entry.

### Estimated scope
- `cli/wizard.py`: ~100 lines (parse dispatch, apply_parsed_results, pre-populate income,
  display helpers)
- Tests: ~80 lines (mocked parsers, profile population, error handling)

### Files touched
- `taxman/cli/wizard.py`
- `taxman/models.py` (possibly add `prior_year_tax` field)
- `tests/test_wizard_parsing.py` (new)
