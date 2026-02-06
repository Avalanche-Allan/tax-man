# 2025 US Tax Return Preparation Workspace

Personal tax preparation project for 2025 federal return (tax year 2025, filing 2026).

## Filing Profile

- **Filing Status:** Married Filing Separately (MFS)
- **Residence:** US citizen living in Mexico City
- **Spouse:** Mexican citizen, NRA, no US tax obligations
- **Income:** 1099 contracting (~$110-135K), DocSherpa LLC (~$500), K-1 rental property
- **Key Forms:** 1040, Schedule C (x2), Schedule SE, Schedule E, possibly Form 2555

## Directory Structure

```
tax-prep/
├── README.md              # This file
├── REPO-EVALUATION.md     # Detailed evaluation of open-source repos
├── repos/                 # Cloned reference repositories
│   ├── habutax/           # Python tax solver (best extensible framework)
│   ├── direct-file/       # IRS official - Fact Graph tax logic reference
│   ├── UsTaxes/           # TypeScript tax filing web app
│   ├── tax-logic-core/    # JS tax calculation engine
│   ├── py1040/            # Python 1040 calculator
│   ├── OpenTaxFormFiller/ # JSON-to-PDF form filler
│   └── PyPDFForm/         # Python PDF form filling library
├── returns-2023/          # Upload 2023 return PDFs here
├── returns-2024/          # Upload 2024 return PDFs here
├── data-2025/             # 2025 source documents (1099s, K-1, expenses)
├── output/                # Generated forms and analysis
└── scripts/               # Custom calculation and form-filling scripts
```

## Workflow

1. **Step 1 (Complete):** Research and clone open-source repos
2. **Step 2 (Next):** Parse 2023 and 2024 prior returns into structured data
3. **Step 3:** Build 2025 return interactively with calculations and form generation
