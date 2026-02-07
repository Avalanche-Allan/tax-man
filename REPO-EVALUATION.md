# Open-Source Tax Repository Evaluation

## Summary of Findings

After researching and cloning 7 repositories, here is my evaluation of each against the
requirements of a self-prepared 2025 federal return for a self-employed US expat filing MFS
with Schedule C, Schedule SE, Schedule E/K-1, and potential FEIE (Form 2555).

**Key finding:** No single open-source tool covers this tax situation end-to-end. The best
approach is to combine reference repos for tax logic with PDF-filling libraries for output.

---

## Tier 1: Primary Tools (Will Use)

### 1. HabuTax (Python tax solver framework)
- **Repo:** https://github.com/habutax/habutax
- **Language:** Python
- **License:** AGPLv3
- **What it provides:**
  - Well-architected dependency-driven tax calculation engine
  - Form 1040, Schedules 1/3/A/B, Forms 8606/8889/8959/8995
  - PDF filling via pdftk with FDF generation
  - Clean form abstraction (each form = Python class with fields, inputs, thresholds)
  - Multi-tax-year support (2021-2023)
- **What it's missing:**
  - Schedule C, Schedule SE, Schedule E, Form 2555 (all marked `not_implemented()`)
  - No 2025 tax year bracket/threshold updates
- **How we'll use it:**
  - **Primary framework** - extend with custom Schedule C, SE, E, and 2555 implementations
  - Architecture is specifically designed for this: each form is a standalone Python class
  - PDF filling pipeline is production-ready
- **Effort to extend:** Moderate. ~30-40 hours to implement the 4 missing forms.
- **Rating for our use case: 8/10**

### 2. PyPDFForm (Python PDF form library)
- **Repo:** https://github.com/chinapandaman/PyPDFForm
- **Language:** Python
- **License:** MIT
- **What it provides:**
  - Pure Python PDF form filling (no pdftk dependency)
  - Inspect form fields, fill with dictionary, flatten output
  - Actively maintained, modern Python
- **How we'll use it:**
  - **Backup/alternative to pdftk** for PDF generation
  - Can fill IRS fillable PDFs directly from calculated values
  - Useful if pdftk causes issues
- **Rating for our use case: 7/10**

### 3. IRS Direct File / Fact Graph (tax logic reference)
- **Repo:** https://github.com/IRS-Public/direct-file
- **Language:** Scala (Fact Graph), TypeScript (frontend)
- **License:** IRS Open Source (public domain elements)
- **What it provides:**
  - Official IRS-authored tax calculation logic for 2024
  - 675+ tax facts encoded in declarative XML
  - Complete tax bracket implementation for all filing statuses
  - EITC, CTC, PTC, CDCC credit calculations
  - Dependent eligibility testing rules
  - MeF XML schema integration for e-file
- **What it's missing:**
  - No Schedule C, SE, E, K-1 support (explicitly excluded)
  - No Form 2555 / international tax
  - No QBI deduction (hardcoded to $0)
  - Only 2024 tax year
- **How we'll use it:**
  - **Reference only** - verify our tax bracket calculations, threshold values,
    and credit eligibility logic against IRS's own implementation
  - The Fact Graph XML files are an authoritative source for how the IRS
    interprets specific tax rules
  - Note: Direct File has been discontinued for 2026 filing season
- **Rating for our use case: 6/10 (reference value only)**

---

## Tier 2: Supporting References (Useful but Limited)

### 4. OpenTaxFormFiller (JSON-to-PDF mapper)
- **Repo:** https://github.com/codehero/OpenTaxFormFiller
- **Language:** Node.js
- **License:** Not specified
- **What it provides:**
  - Complete field mapping for 2011 Form 1040, Schedule C, Schedule A, Schedule D
  - Partial Schedule SE (Section A) and Schedule E (Part I)
  - Two-file mapping system: definition (field types) + transform (PDF field IDs)
  - Working PDF filling pipeline via pdftk
- **Limitations:**
  - Only 2011-2012 tax years (form fields change yearly)
  - Unmaintained (last commit 2021)
  - No calculation logic (just field mapping)
- **How we'll use it:**
  - **Reference for PDF field mapping patterns** when creating our own mappings
  - The definition/transform architecture is a good model
  - Field names from 2011 won't match 2025 PDFs but the approach transfers
- **Rating for our use case: 4/10**

### 5. tax-logic-core (JS tax calculation engine)
- **Repo:** https://github.com/tax-logic-core/tax-logic-core
- **Language:** JavaScript
- **License:** MIT
- **What it provides:**
  - 2025 tax brackets (updated for One Big Beautiful Bill Act)
  - Self-employment tax calculation
  - QBI deduction logic
  - All 50 states + DC income tax
  - IRS citations for each calculation
- **Limitations:**
  - Brand new repo (created Feb 2026, only 10 commits)
  - Minimal community adoption (3 stars, 0 forks)
  - No form-level implementation (just calculations)
  - No PDF output
- **How we'll use it:**
  - **Cross-reference for 2025 tax brackets and thresholds**, especially for
    One Big Beautiful Bill Act changes
  - Verify our SE tax and QBI calculations
- **Rating for our use case: 5/10**

### 6. py1040 (Python 1040 calculator)
- **Repo:** https://github.com/b-k/py1040
- **Language:** Python
- **License:** GPL
- **What it provides:**
  - Interview-based tax calculation for Form 1040
  - Line-by-line calculation output
  - Cell-based dependency model
- **Limitations:**
  - Explicitly does NOT support Schedule C or Schedule F (author is not self-employed)
  - No Schedule SE, E, or Form 2555
  - Unknown maintenance status
- **How we'll use it:**
  - **Limited reference** for 1040 line calculation patterns
  - HabuTax is strictly better for our purposes
- **Rating for our use case: 3/10**

### 7. UsTaxes (TypeScript tax filing web app)
- **Repo:** https://github.com/ustaxes/UsTaxes
- **Language:** TypeScript
- **License:** AGPL
- **What it provides:**
  - Web-based tax filing interface
  - Schedule B, D, E support
  - Form 8949, 8889, 8959, 8960
  - PDF generation
- **Limitations:**
  - No Schedule C, SE, or Form 2555
  - No Married Filing Separately support
  - No 1099-NEC support
  - Only covers 2020-2023 tax years
- **How we'll use it:**
  - **Reference for Schedule E implementation** (it does support Schedule E)
  - TypeScript codebase is less useful since we'll work in Python
- **Rating for our use case: 4/10**

---

## Repos NOT Cloned (Evaluated and Rejected)

### OpenTaxSolver (C-based tax calculator)
- **Site:** https://opentaxsolver.sourceforge.net/
- **Why rejected:** Written in C (not Python), harder to extend and integrate.
  Does have 2025 support including Schedules A, B, C, D. Could be useful as a
  cross-check tool but not as our primary framework.

### rawrcollective/US-Tax-Code
- **Repo:** https://github.com/rawrcollective/US-Tax-Code
- **Why rejected:** Aspirational project to digitize US Tax Code. Not functional
  software, just links to Cornell Law Institute.

### PSLmodels/Tax-Calculator
- **Repo:** https://github.com/PSLmodels/Tax-Calculator
- **Why rejected:** Policy microsimulation model for analyzing tax reform impacts.
  Not designed for individual return preparation.

---

## Recommended Approach

### What we'll build:

1. **Extend HabuTax** with custom form implementations for:
   - Schedule C (Profit or Loss from Business) x2
   - Schedule SE (Self-Employment Tax)
   - Schedule E (Supplemental Income - rental/K-1)
   - Form 2555 (Foreign Earned Income Exclusion) - if beneficial
   - Form 8995 (QBI Deduction) - full version, not just 199A dividends
   - Update thresholds/brackets to 2025 values

2. **Use IRS Direct File Fact Graph** as authoritative reference for:
   - Tax bracket calculations
   - Standard deduction amounts
   - Credit eligibility thresholds

3. **Use tax-logic-core** to cross-reference:
   - 2025 bracket changes from One Big Beautiful Bill Act
   - SE tax calculation formulas
   - QBI deduction logic

4. **Use PyPDFForm or pdftk** for:
   - Downloading official IRS fillable PDFs
   - Programmatically filling completed forms
   - Generating print-ready return package

5. **Manual verification** against:
   - 2023 and 2024 prior returns (once parsed)
   - IRS instructions for each form
   - OpenTaxSolver output (as independent cross-check)

### PDF Form Filling Strategy:

IRS publishes fillable PDFs for all forms at https://www.irs.gov/forms-instructions.
We'll:
1. Download 2025 versions of each required form
2. Map PDF field names using pdftk's `dump_data_fields` command
3. Create field mappings (JSON dictionaries)
4. Fill programmatically with calculated values
5. Flatten and concatenate into final return package

---

## Key Risk: 2025 Tax Law Changes

The **One Big Beautiful Bill Act of 2025** made significant changes including:
- Modified tax brackets
- Changes to standard deduction
- SALT deduction cap modifications
- Various credit changes

We need to verify all 2025 thresholds against official IRS publications before
finalizing any calculations. The IRS 2025 form instructions (published late 2025
/ early 2026) are the authoritative source.
