# Issue #2: Session Resume — Full Profile Hydration

## Problem
Wizard resumes by step index but creates a fresh `TaxpayerProfile()` on every run.
Steps 6–9 collect the bulk of tax data (businesses, K-1s, expenses, deductions, foreign income)
directly into `self.profile` — none of it is persisted to `SessionState`. On resume, all collected
data is lost.

## Current State
- `SessionState` (in `cli/state.py`) has placeholder fields: `income_data`, `expense_data`,
  `deduction_choices`, `foreign_info`, `parsed_documents` — all empty dicts, never written.
- Only `filing_status` and a minimal `personal_info` dict are saved.
- `self.result` (Form1040Result) is also never persisted to `session.results`.

## Plan

### Phase 1: Serialization module (`cli/serialization.py`)
1. Create `taxman/cli/serialization.py` with:
   - `serialize_profile(profile: TaxpayerProfile) -> dict` — handles enums (`.value`),
     nested dataclasses (`asdict` + special handling), and lists of models.
   - `deserialize_profile(data: dict) -> TaxpayerProfile` — reconstructs full object graph:
     `FilingStatus(d['filing_status'])`, `[ScheduleCData(**b) for b in d['businesses']]`,
     nested `HomeOffice`, `HealthInsurance`, `Dependent`, `ScheduleK1`, `FormW2`,
     `Form1099NEC/INT/DIV/B`, etc.
   - `serialize_result(result: Form1040Result) -> dict`
   - `deserialize_result(data: dict) -> Form1040Result`
2. Rationale: keeps serialization logic out of models (which are pure data) and out of the
   wizard (which is UI). Single place to maintain when models change.

### Phase 2: Session schema versioning
3. Add `schema_version: int = 1` field to `SessionState`.
4. In `SessionState.load()`, check `data.get("schema_version", 0)`:
   - Version 0 (legacy, no profile_data): warn user, allow re-entry of data.
   - Version 1+: deserialize `profile_data` normally.
5. When schema changes in the future, bump version and add migration logic.
6. This prevents crashes on old session files after we change the format.

### Phase 3: Persist profile to session
7. Add `profile_data: dict = {}` field to `SessionState` (replaces the fragmented
   `income_data`, `expense_data`, `deduction_choices`, `foreign_info` fields).
8. At the end of each wizard step that mutates `self.profile`, call:
   ```python
   self.session.profile_data = serialize_profile(self.profile)
   self.session.save()
   ```
   Steps that need this: `filing_status`, `personal_info`, `income_review`,
   `business_expenses`, `deductions`, `foreign_income`.

### Phase 4: Rehydrate on resume
9. In `TaxWizard.__init__`, after loading session:
   ```python
   if session and session.profile_data:
       self.profile = deserialize_profile(session.profile_data)
   ```
10. Also rehydrate `self.scan_results` from `session.parsed_documents` if present
    (for Issue #4 compatibility).

### Phase 5: Persist calculation results
11. After `_step_calculate()`, persist the result:
    ```python
    self.session.results = serialize_result(self.result)
    self.session.save()
    ```
12. This unblocks `export` and `review` commands (Issue #3).

### Tests needed
- **Round-trip**: `profile` → `serialize_profile()` → `deserialize_profile()` → assert equality.
  Cover: empty profile, MFS expat with businesses + K-1s, profile with W-2s + 1099s + dependents.
- **Resume parity**: Build a profile programmatically, calculate return. Then: create wizard with
  that profile already serialized in session, call `_step_calculate()`. Assert the two
  `Form1040Result` objects match field-for-field. This is the strongest correctness test — proves
  an interrupted+resumed run produces the same result as an uninterrupted run.
- **Schema versioning**: Load a session JSON with no `schema_version` key, verify it loads
  gracefully with empty profile (version 0 path).
- **Result persistence**: calculate → serialize → deserialize → assert result fields match.

### Definition of done
1. Resume from step N shows previously entered values and computes the same return as an
   uninterrupted run.
2. Old session files (no schema_version) load without crashing.

### Estimated scope
- New file `cli/serialization.py`: ~120 lines
- `cli/state.py`: ~15 lines (schema_version, profile_data, cleanup old fields)
- `cli/wizard.py`: ~20 lines (save profile after each step, rehydrate on init)
- Tests `tests/test_serialization.py`: ~100 lines

### Files touched
- `taxman/cli/serialization.py` (new)
- `taxman/cli/state.py`
- `taxman/cli/wizard.py`
- `tests/test_serialization.py` (new)
