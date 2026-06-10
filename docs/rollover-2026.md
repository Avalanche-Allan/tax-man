# 2026 Tax Year Rollover Checklist

The engine targets one tax year at a time (`taxman/constants.py:TAX_YEAR`).
Rolling to 2026 is two phases: **profile rollover (do anytime)** and
**engine update (wait for the 2026 forms, ~Dec 2026 – Jan 2027)**.

## Phase 1 — Profile rollover (already available)

```bash
taxman rollover <2025-session-id>
```

Creates a new 2026 session: keeps identity/businesses/rental/health
insurance as planning estimates, clears W-2s/1099s/K-1s, and sets
`prior_year_tax` to the 2025 total tax for safe-harbor estimates.

**2025 → 2026 carryforward facts (Austin's return, filed June 2026):**
- 2025 total tax: **$13,778.12** → 100% safe harbor = $3,444.53/quarter
  (AGI $4,693 is far below the $75k MFS 110% threshold)
- No capital loss carryforward (2025 net loss -$226 fully used, under
  the $1,500 MFS limit)
- No NOL carryforward, no QBI loss carryforward
- No suspended passive losses (rental was profitable: +$3,997)
- Rental depreciation continues: $5,090.91/yr (50% share, 27.5-yr SL,
  $280k building basis, 2075 Jamaica St)
- 2026 estimated payment due dates: Apr 15 / Jun 15 / Sep 15, 2026 and
  Jan 15, 2027. Record each payment in the new session so Form 1040
  line 26 is right next spring.

## Phase 2 — Engine update (when 2026 forms are released)

### Step 1: Update `taxman/constants.py` (numbers already published)

All 2026 inflation adjustments are final — sources:
[Rev. Proc. 2025-32](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill)
(IRS, Oct 9 2025) and the
[SSA 2026 COLA fact sheet](https://www.ssa.gov/news/en/cola/factsheets/2026.html).

| Constant | 2025 | 2026 | Source |
|---|---|---|---|
| `TAX_YEAR` | 2025 | 2026 | — |
| `STANDARD_DEDUCTION` single/mfs | 15,750 | **16,100** | Rev. Proc. 2025-32 |
| `STANDARD_DEDUCTION` mfj/qss | 31,500 | **32,200** | Rev. Proc. 2025-32 |
| `STANDARD_DEDUCTION` hoh | 23,625 | **24,150** | Rev. Proc. 2025-32 |
| `SS_WAGE_BASE` | 176,100 | **184,500** | SSA COLA 2026 |
| `FEIE_EXCLUSION_LIMIT` | 130,000 | **132,900** | Rev. Proc. 2025-32 |
| All bracket tables (MFS/Single/MFJ/HOH) | Rev. Proc. 2024-40 | Rev. Proc. 2025-32 §2.01 | look up each |
| QBI thresholds (`QBI_THRESHOLD_*`) | 197,300 MFS | Rev. Proc. 2025-32 | look up |
| AMT exemption/phaseout | Rev. Proc. 2024-40 | Rev. Proc. 2025-32 (OBBBA changed phaseouts) | look up |
| QDCG 0%/15%/20% breakpoints | 2025 values | Rev. Proc. 2025-32 §2.03 | look up |
| Capital loss limits, SE rates, Medicare/NIIT thresholds | unchanged by statute | verify anyway | IRC |
| `CO_TAX_RATE` | check current | CO sets rate annually (TABOR triggers) | tax.colorado.gov |
| Hard-coded `2025` strings | wizard prompts, model field names (`days_in_*_2025`), docstrings | rename or bump | grep `2025` |

### Step 2: Download the 2026 forms and re-verify EVERY field mapping

**IRS URLs are versionless** — irs.gov swaps the new revision in at the
same URL. The `TestFormVintage` tests fail as soon as a cached PDF's
year doesn't match `TAX_YEAR`; that's the signal to do this step.
Colorado URLs are year-stamped: change `DR0104_2025.pdf` →
`DR0104_2026.pdf` in `IRS_FORM_URLS`.

```bash
rm forms/*.pdf forms/*.checkbox_patched   # force fresh downloads
python3 -m pytest tests/test_field_mappings.py -q
```

For each form, repeat the verification workflow used in 2025
(it caught the f1040 checkbox shift that checked "Deceased" on every
return — assume the layout moved until proven otherwise):
1. Dump widgets: pymupdf `page.widgets()` names + x/y positions
2. Render the blank form and map positions to line numbers visually
3. Fix the `build_*_data()` mapping
4. Fill with the standard test profile, render, and inspect every page
5. Run the line-math + golden tests

### Step 3: Update tests

Many tests assert exact 2025 dollar amounts (standard deduction,
SE tax on known incomes, bracket math). Expect a large mechanical
update; the calculation tests in `tests/test_calculator.py` are the
spec — recompute expected values from the 2026 constants, never
loosen assertions to make them pass.

### Step 4: Tag before and after

The filed 2025 state is tagged `2025-return-filed`. Tag the completed
2026 update similarly so each filing year is recoverable.

## Known gaps to revisit during the 2026 cycle

- Itemized deductions (Schedule A) — standard deduction only
- Form 8949 (only covered, basis-reported lots supported on Sch D 1a/8a)
- Form 8959/8960 PDFs not generated when Additional Medicare/NIIT apply
- CO: DR 0104AD subtractions schedule, QBI/std-deduction addbacks
  (only relevant above $300k/$500k AGI)
- Street address missing from the saved profile (1040 + DR 0104
  address lines render blank)
