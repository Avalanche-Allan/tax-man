# Tax Man

2025 US federal (and Colorado state) tax return preparation engine with an interactive CLI.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Launch the interactive wizard
taxman prepare

# Or point it at your documents folder
taxman prepare --documents-dir data-2025/

# Resume a previous session
taxman prepare --resume <session-id>
```

## Requirements

- Python 3.10+
- Dependencies are installed automatically: pypdf, pdfplumber, PyPDFForm, rich, questionary, typer

## CLI Commands

| Command | Description |
|---------|-------------|
| `taxman prepare` | Interactive step-by-step wizard for building your return |
| `taxman scan <dir>` | Classify tax documents in a folder (1099-NEC, K-1, W-2, etc.) |
| `taxman review <session>` | Display a saved return with Rich tables |
| `taxman export <session>` | Generate filled IRS PDFs and reports |
| `taxman compare <session>` | FEIE with/without comparison |
| `taxman sessions` | List all saved sessions |

### `taxman prepare`

Walks through 13 steps:

1. Welcome and disclaimers
2. Filing status selection
3. Document scan — auto-classify PDFs in a folder
4. Document review — confirm parsed values from each document
5. Personal info — name, SSN, address (validated)
6. Income review — all sources with running totals
7. Business expenses — per-business Schedule C walkthrough with home office sub-wizard
8. Deductions — standard vs. itemized, QBI explanation
9. Foreign income — physical presence calculator, FEIE side-by-side
10. Calculate — run the engine, display income/tax/effective rate tables
11. Optimization — FEIE scenarios, retirement suggestions, expense review
12. Generate forms — PDF generation with progress bar
13. Filing checklist — required forms, deadlines, payment info

Progress is saved after each step. Quit and resume anytime with `--resume`.

### `taxman scan`

```bash
taxman scan data-2025/
```

Scans a folder of PDFs and classifies each document (1099-NEC, K-1, W-2, 1098, 1095-A, etc.). Shows a Rich tree of what was found.

## Configuration

Create `~/.taxman/config.toml` to pre-fill defaults:

```toml
[general]
documents_dir = "~/taxes/data-2025"
output_dir = "~/taxes/output"

[taxpayer]
first_name = "Jane"
last_name = "Doe"
filing_status = "married_filing_separately"
foreign_country = "Mexico"
prior_year_tax = 18500.00
```

Sessions are stored in `~/.taxman/sessions/`.

## What It Calculates

### Federal

- **Form 1040** — AGI, taxable income, total tax, refund/owed, Lines 1-9 (wages, interest, dividends, capital gains)
- **Schedule C** (multiple businesses) — gross income, categorized expenses, net profit/loss, home office (simplified + regular with mortgage/RE taxes), COGS
- **Schedule D** — capital gains/losses from 1099-B, K-1 Boxes 8/9a/10, 1099-DIV Box 2a; loss limitation ($3,000 / $1,500 MFS)
- **Schedule SE** — self-employment tax (SS + Medicare split), deductible half, W-2 SS wage base coordination
- **Schedule E** — all K-1 boxes (1-14): rental income, ordinary business income, guaranteed payments, interest, dividends, royalties, capital gains, §1231 gains, other income, §179/other deductions
- **Form 8995** — QBI deduction with W-2/UBIA wage limitation, phase-out, and §199A(a) cap reduced by net capital gain
- **Form 2555** — FEIE evaluation with physical presence test and stacking method comparison
- **Form 6251** — Alternative Minimum Tax with exemption, phaseout (25%/dollar), 26%/28% rates
- **Form 8959** — Additional Medicare Tax (0.9% above filing-status threshold)
- **NIIT** — Net Investment Income Tax (3.8%) on interest, dividends, capital gains, rental income, royalties
- **Schedule 8812** — Child Tax Credit ($2,500/child OBBBA), Other Dependent Credit ($500), ACTC refundable
- **Quarterly estimates** — 2026 safe harbor calculations (100%/110% of prior year)

All calculations respect filing status (Single, MFJ, MFS, HOH, QSS). MFS-specific rules are fully implemented: passive rental loss suspension (IRC 469), NIIT/Medicare thresholds, QBI phase-out, FEIE stacking brackets, $1,500 capital loss limit.

### Colorado

- **Form 104** — flat 4.4% rate on federal taxable income
- Nonresident apportionment for CO-source income (e.g., Denver rental property)
- SALT deduction addback for itemizers
- TABOR refund subtraction
- Pension/annuity subtraction (age-based: $20K for 55-64, $24K for 65+)

## Document Parsing

Parses these document types from PDF:

| Document | What's Extracted |
|----------|-----------------|
| 1099-NEC | Payer/recipient TINs, nonemployee compensation |
| Schedule K-1 (1065) | Boxes 1-14 (income, dividends, royalties, capital gains, §1231, §179, SE earnings) |
| W-2 | Boxes 1-6, 16-17 |
| 1098 (Mortgage) | Box 1 (interest), Box 6 (points) |
| 1095-A | Monthly premiums, SLCSP, APTC |
| Charity receipts | Organization, amount, date |
| Prior returns | Form detection, line item extraction |

Each parse returns a `ParseResult` with confidence score, warnings, and a flag for items needing manual review.

## PDF Form Generation

Generates filled IRS PDFs for: 1040, Schedule C, Schedule D, Schedule SE, Schedule E, Form 6251, Form 8995, Form 2555, Schedule 8812.

```python
from taxman.fill_forms import generate_all_forms

generate_all_forms(result, profile, output_dir="output/")
```

IRS form PDFs are expected in `forms/` (or set `TAXMAN_FORMS_DIR` env var). Download the 2025 fillable PDFs from irs.gov.

**Note:** PDF field names in `taxman/field_mappings/` are placeholders. Run `inspect_form_fields_raw()` against the actual 2025 IRS PDFs to discover real field names, then update the mappings.

## Reports

```python
from taxman.reports import (
    generate_tax_summary,
    generate_line_detail,
    generate_filing_checklist,
    generate_quarterly_plan,
    generate_feie_comparison_report,
    generate_prior_year_comparison,
)
```

- **Tax summary** — plain English return summary with effective rates
- **Line detail** — every line item with calculation and explanation
- **Filing checklist** — required forms, deadlines, mailing addresses (data-driven from results)
- **Quarterly plan** — 2026 estimated payment schedule with safe harbor
- **FEIE comparison** — side-by-side with/without analysis
- **Prior year comparison** — year-over-year changes

## Optimization Engine

```python
from taxman.calculator import generate_optimization_recommendations

recommendations = generate_optimization_recommendations(result, profile)
for rec in recommendations:
    print(f"{rec['category']}: {rec['recommendation']} (${rec['potential_savings']})")
```

Checks: FEIE benefit, retirement contribution room, home office method comparison, expense categorization opportunities.

## Using as a Library

```python
from taxman.models import TaxpayerProfile, FilingStatus, ScheduleCData
from taxman.calculator import calculate_return

profile = TaxpayerProfile(
    first_name="Jane",
    last_name="Doe",
    ssn="123-45-6789",
    filing_status=FilingStatus.MARRIED_FILING_SEPARATELY,
    schedule_c_data=[ScheduleCData(...)],
    ...
)

result = calculate_return(profile)
print(f"Total tax: ${result.total_tax:,.2f}")
print(f"Effective rate: {result.effective_tax_rate:.1%}")
```

For Colorado:

```python
from taxman.colorado import calculate_full_return

federal_result, co_result = calculate_full_return(profile)
print(f"CO tax: ${co_result.co_tax_after_apportion:,.2f}")
```

## Testing

```bash
# Run all 287 tests
pytest

# With coverage
pytest --cov=taxman

# Specific test file
pytest tests/test_calculator.py -v
```

Test files:

| File | Tests | Covers |
|------|-------|--------|
| `test_calculator.py` | 122 | All tax calculations, brackets, SE, QBI, FEIE, NIIT, AMT, credits, investment income, Schedule D, K-1 boxes |
| `test_models.py` | 84 | Dataclass validation, properties, edge cases, parsing, form filling |
| `test_integration.py` | 61 | Full return scenarios (MFS expat, freelancer, MFJ), consistency |
| `test_colorado.py` | 20 | CO source income, Form 104, apportionment, SALT addback, pension subtraction |

## Project Structure

```
tax-man/
  pyproject.toml
  README.md
  TODO.md

  taxman/                         # Core package
    __init__.py
    constants.py                  # 2025 brackets, rates, thresholds (federal + CO)
    models.py                     # Dataclasses with validation (TaxpayerProfile, 1099, K-1, etc.)
    calculator.py                 # Tax engine (Schedule C/SE/E, QBI, FEIE, 1040, optimization)
    parse_documents.py            # PDF parsing (1099-NEC, K-1, W-2, 1098, 1095-A, charity)
    fill_forms.py                 # IRS PDF form filling and generation pipeline
    reports.py                    # Report generation (summary, line detail, checklist, quarterly)
    validation.py                 # Input validators (TIN, EIN, amounts, ranges)
    colorado.py                   # Colorado Form 104 engine

    cli/                          # Interactive CLI
      app.py                      # Typer commands (prepare, scan, review, export, etc.)
      wizard.py                   # 13-step Questionary wizard
      display.py                  # Rich rendering (tables, panels, trees, progress bars)
      state.py                    # Session persistence (save/resume to JSON)
      config.py                   # ~/.taxman/config.toml loading

    field_mappings/               # IRS PDF field name mappings
      common.py                   # format_ssn(), format_ein(), format_currency_for_pdf()
      f1040.py                    # Form 1040 field mapping
      f1040sc.py                  # Schedule C field mapping
      f1040se.py                  # Schedule E field mapping
      f1040sse.py                 # Schedule SE field mapping
      f8995.py                    # Form 8995 (QBI) field mapping
      f2555.py                    # Form 2555 (FEIE) field mapping

  tests/                          # pytest suite (287 tests)
    conftest.py                   # Shared fixtures
    fixtures/profiles.py          # Factory functions for test profiles
    test_calculator.py            # 122 tests — brackets, SE, QBI, FEIE, NIIT, AMT, credits, Schedule D
    test_models.py                # 84 tests — validation, properties, parsing, form filling
    test_integration.py           # 61 tests — full return scenarios, consistency
    test_colorado.py              # 20 tests — CO source income, Form 104, SALT, pension

  forms/                          # IRS fillable PDFs (gitignored, download from irs.gov)
  data-2025/                      # Source tax documents (gitignored)
  output/                         # Generated forms and reports (gitignored)
```

## Tax Notes

1. **FEIE does NOT reduce SE tax.** Self-employment tax applies to the full amount even if income is excluded via Form 2555. Always run the comparison.

2. **MFS passive rental losses are suspended** per IRC 469(i)(5)(B). The $25K active participation allowance is $0 for MFS. Suspended losses carry forward.

3. **Additional Medicare Tax threshold for MFS is $125,000** — lower than the $200K single/$250K MFJ thresholds.

4. **QBI deduction phases out above $197,300 (MFS)**. With no W-2 wages and no UBIA, the deduction reaches $0 above $247,300.

5. **Taxpayers abroad** get an automatic 2-month extension to June 15, 2026. Interest still accrues from April 15 on any balance owed.

6. **Colorado nonresidents** owe CO tax only on CO-source income. K-1 rental income from Denver property is CO-source.

7. **QBI deduction cap** per IRC §199A(a): 20% of (taxable income minus net capital gain). Net capital gain includes qualified dividends.

8. **AMT** primarily affects itemizers who deduct significant SALT. Standard deduction filers rarely trigger AMT.

9. **Child Tax Credit (OBBBA 2025)** is $2,500 per qualifying child. Phases out at $50 per $1,000 of AGI above $400K (MFJ) or $200K (other). Unused CTC becomes refundable ACTC up to $1,700/child.

## Dependencies

| Package | Purpose |
|---------|---------|
| pypdf | PDF reading and form field inspection |
| pdfplumber | Text and table extraction from PDFs |
| PyPDFForm | PDF form filling (pure Python, no pdftk) |
| rich | Terminal tables, panels, trees, progress bars |
| questionary | Interactive prompts with validation |
| typer | CLI command structure |
| pytest | Test framework (dev dependency) |
