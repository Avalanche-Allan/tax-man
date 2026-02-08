"""Step-by-step wizard for tax return preparation.

13 steps with save/resume between each:
1. Welcome, 2. Filing status, 3. Document scan, 4. Document review,
5. Personal info, 6. Income review, 7. Business expenses,
8. Deductions, 9. Foreign income, 10. Calculate, 11. Optimization,
12. Generate forms, 13. Filing checklist.
"""

import sys
from pathlib import Path
from typing import Optional

import questionary
from rich.console import Console

from taxman.calculator import (
    calculate_return,
    compare_feie_scenarios,
    estimate_quarterly_payments,
    generate_optimization_recommendations,
)
from taxman.cli.display import (
    console,
    display_document_scan,
    display_feie_comparison,
    display_income_table,
    display_optimization_recommendations,
    display_quarterly_plan,
    display_result_panel,
    display_schedule_c,
    display_tax_breakdown,
    display_welcome,
    format_currency,
)
from taxman.cli.serialization import (
    deserialize_profile,
    deserialize_result,
    serialize_profile,
    serialize_result,
)
from taxman.cli.state import SessionState
from taxman.models import (
    BusinessExpenses,
    BusinessType,
    CharityReceipt,
    EstimatedPayment,
    FilingStatus,
    Form1095A,
    Form1098,
    Form1099NEC,
    FormW2,
    HealthInsurance,
    HomeOffice,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)
from taxman.parse_documents import (
    ParseResult,
    parse_1095_a,
    parse_1098_mortgage,
    parse_1099_nec,
    parse_charity_receipt,
    parse_k1_1065,
    parse_prior_return,
    parse_w2,
    scan_documents_folder,
)
from taxman.reports import (
    generate_filing_checklist,
    generate_quarterly_plan as gen_quarterly_text,
    generate_tax_summary,
)


WIZARD_STEPS = [
    "welcome",
    "filing_status",
    "document_scan",
    "document_review",
    "personal_info",
    "income_review",
    "business_expenses",
    "deductions",
    "foreign_income",
    "calculate",
    "optimization",
    "generate_forms",
    "filing_checklist",
]


class TaxWizard:
    """Interactive wizard that walks through tax return preparation."""

    def __init__(self, session: Optional[SessionState] = None,
                 documents_dir: str = "",
                 config=None):
        self.session = session or SessionState.create()
        self.documents_dir = documents_dir or self.session.documents_dir
        self.config = config
        self.scan_results = None
        self.parsed_results = []

        # Rehydrate profile and result from session if resuming
        if self.session.profile_data:
            self.profile = deserialize_profile(self.session.profile_data)
        else:
            self.profile = TaxpayerProfile()

        if self.session.results:
            self.result = deserialize_result(self.session.results)
        else:
            self.result = None

    def _save_profile(self):
        """Persist the current profile to the session."""
        self.session.profile_data = serialize_profile(self.profile)
        self.session.save()

    def run(self):
        """Run the wizard from the current step."""
        # Find where to resume
        start_idx = 0
        if self.session.completed_steps:
            last = self.session.completed_steps[-1]
            if last in WIZARD_STEPS:
                start_idx = WIZARD_STEPS.index(last) + 1

        for step_name in WIZARD_STEPS[start_idx:]:
            self.session.current_step = step_name
            self.session.save()

            step_fn = getattr(self, f"_step_{step_name}", None)
            if step_fn:
                try:
                    step_fn()
                except KeyboardInterrupt:
                    console.print("\n[yellow]Session saved. Resume with: "
                                  f"taxman prepare --resume {self.session.session_id}[/yellow]")
                    return
                except EOFError:
                    console.print("\n[yellow]Session saved.[/yellow]")
                    return

                self.session.complete_step(step_name)

        console.print("\n[bold green]Tax return preparation complete![/bold green]")

    # ── Step 1: Welcome ──────────────────────────────────────────────

    def _step_welcome(self):
        display_welcome()
        console.print(f"\n[dim]Session ID: {self.session.session_id}[/dim]")
        questionary.press_any_key_to_continue("Press any key to begin...").ask()

    # ── Step 2: Filing Status ────────────────────────────────────────

    def _step_filing_status(self):
        console.print("\n[bold]Step 2: Filing Status[/bold]")

        status_choices = [
            questionary.Choice("Single", value="single"),
            questionary.Choice("Married Filing Jointly (MFJ)", value="mfj"),
            questionary.Choice("Married Filing Separately (MFS)", value="mfs"),
            questionary.Choice("Head of Household (HOH)", value="hoh"),
            questionary.Choice("Qualifying Surviving Spouse (QSS)", value="qss"),
        ]

        answer = questionary.select(
            "Select your filing status:",
            choices=status_choices,
        ).ask()

        if answer is None:
            raise KeyboardInterrupt

        self.profile.filing_status = FilingStatus(answer)
        self.session.filing_status = answer

        # Spouse info for MFS/MFJ
        if answer in ("mfs", "mfj"):
            name = questionary.text("Spouse's full name:").ask()
            if name:
                self.profile.spouse_name = name

            ssn = questionary.text(
                "Spouse's SSN/ITIN (or leave blank):",
                validate=lambda x: True,
            ).ask()
            if ssn:
                self.profile.spouse_ssn = ssn

            if answer == "mfs":
                nra = questionary.confirm(
                    "Is your spouse a nonresident alien?", default=True
                ).ask()
                self.profile.spouse_is_nra = nra

        self._save_profile()

    # ── Step 3: Document Scan ────────────────────────────────────────

    def _step_document_scan(self):
        console.print("\n[bold]Step 3: Document Scan[/bold]")

        doc_dir = self.documents_dir
        if not doc_dir:
            doc_dir = questionary.path(
                "Path to your tax documents folder:",
                only_directories=True,
            ).ask()

        if not doc_dir or not Path(doc_dir).exists():
            console.print("[yellow]No documents folder provided. Skipping scan.[/yellow]")
            return

        self.documents_dir = doc_dir
        self.session.documents_dir = doc_dir

        console.print(f"Scanning [bold]{doc_dir}[/bold]...")
        self.scan_results = scan_documents_folder(doc_dir)
        display_document_scan(self.scan_results)

    # ── Step 4: Document Review ──────────────────────────────────────

    # Parser dispatch table
    PARSERS = {
        "1099-NEC": parse_1099_nec,
        "W-2": parse_w2,
        "K-1": parse_k1_1065,
        "1098": parse_1098_mortgage,
        "1095-A": parse_1095_a,
        "Charity Receipt": parse_charity_receipt,
    }

    def _step_document_review(self):
        console.print("\n[bold]Step 4: Document Review[/bold]")

        if not self.scan_results or not self.scan_results.get("documents"):
            console.print("[dim]No documents to review.[/dim]")
            return

        parseable_types = set(self.PARSERS.keys()) | {"Prior Return"}

        for doc in self.scan_results["documents"]:
            classification = doc.get("classification", "unknown")
            if classification not in parseable_types:
                continue

            console.print(f"\n[bold]{doc['name']}[/bold] — {classification}")
            if "text_preview" in doc:
                console.print(f"[dim]{doc['text_preview'][:200]}...[/dim]")

            confirm = questionary.confirm("Accept this document?", default=True).ask()
            if confirm is None:
                raise KeyboardInterrupt

            if not confirm:
                continue

            # Parse the accepted document
            if classification == "Prior Return":
                try:
                    prior_data = parse_prior_return(doc["path"])
                    prior_tax = prior_data.get("data", {}).get("Form 1040", {}).get("line_24", 0)
                    if prior_tax:
                        console.print(f"  [green]Prior year total tax: {format_currency(prior_tax)}[/green]")
                except Exception as e:
                    console.print(f"  [yellow]Could not parse prior return: {e}[/yellow]")
                continue

            parser = self.PARSERS.get(classification)
            if parser:
                try:
                    parse_result = parser(doc["path"])
                    self.parsed_results.append(parse_result)
                    self._display_parse_result(parse_result)
                except Exception as e:
                    console.print(f"  [yellow]Could not parse {doc['name']}: {e}[/yellow]")

        # Persist parsed documents to session
        self._save_parsed_documents()

    # ── Parse helpers ────────────────────────────────────────────────

    def _display_parse_result(self, pr: ParseResult):
        """Display extracted values from a parsed document."""
        confidence_str = f"{pr.confidence:.0%}"
        style = "green" if pr.confidence >= 0.7 else "yellow"
        console.print(f"  [{style}]Parsed ({pr.document_type}, confidence: {confidence_str})[/{style}]")

        data = pr.data
        if isinstance(data, FormW2):
            console.print(f"    Employer: {data.employer_name}")
            console.print(f"    Wages: {format_currency(data.wages)}")
            console.print(f"    Federal withheld: {format_currency(data.federal_tax_withheld)}")
        elif isinstance(data, Form1099NEC):
            console.print(f"    Payer: {data.payer_name}")
            console.print(f"    Compensation: {format_currency(data.nonemployee_compensation)}")
        elif isinstance(data, ScheduleK1):
            console.print(f"    Partnership: {data.partnership_name}")
            if data.net_rental_income:
                console.print(f"    Rental income: {format_currency(data.net_rental_income)}")
            if data.ordinary_business_income:
                console.print(f"    Ordinary income: {format_currency(data.ordinary_business_income)}")
        elif isinstance(data, Form1098):
            console.print(f"    Lender: {data.lender_name}")
            console.print(f"    Mortgage interest: {format_currency(data.mortgage_interest)}")

        if pr.warnings:
            for w in pr.warnings:
                console.print(f"    [yellow]Warning: {w}[/yellow]")

        if pr.confidence < 0.7:
            console.print(f"    [yellow]Low confidence — please review carefully[/yellow]")

    def _save_parsed_documents(self):
        """Persist parsed results to session for resume support."""
        from dataclasses import asdict

        self.session.parsed_documents = []
        for pr in self.parsed_results:
            entry = {
                "type": pr.document_type,
                "file": pr.source_file,
                "confidence": pr.confidence,
                "warnings": pr.warnings,
                "needs_manual_review": pr.needs_manual_review,
                "data": asdict(pr.data) if pr.data else None,
            }
            self.session.parsed_documents.append(entry)
        self.session.save()

    def _apply_parsed_results(self):
        """Populate profile from parsed document results.

        Called at the start of _step_income_review to pre-fill profile
        from parsed documents. Shows user what was populated.
        """
        if not self.parsed_results:
            return

        counts = {}
        for pr in self.parsed_results:
            data = pr.data
            if isinstance(data, FormW2):
                self.profile.forms_w2.append(data)
                counts["W-2"] = counts.get("W-2", 0) + 1
            elif isinstance(data, Form1099NEC):
                self.profile.forms_1099_nec.append(data)
                counts["1099-NEC"] = counts.get("1099-NEC", 0) + 1
            elif isinstance(data, ScheduleK1):
                self.profile.schedule_k1s.append(data)
                counts["K-1"] = counts.get("K-1", 0) + 1
            elif isinstance(data, Form1098):
                self.profile.forms_1098.append(data)
                counts["1098"] = counts.get("1098", 0) + 1
            elif isinstance(data, Form1095A):
                # Store for potential PTC calculation
                counts["1095-A"] = counts.get("1095-A", 0) + 1
            elif isinstance(data, CharityReceipt):
                counts["Charity"] = counts.get("Charity", 0) + 1

        if counts:
            console.print("\n[bold]Pre-populated from documents:[/bold]")
            for doc_type, count in counts.items():
                console.print(f"  {count} {doc_type}(s)")

    # ── Step 5: Personal Info ────────────────────────────────────────

    def _step_personal_info(self):
        console.print("\n[bold]Step 5: Personal Information[/bold]")

        fields = [
            ("first_name", "First name:", self.profile.first_name),
            ("last_name", "Last name:", self.profile.last_name),
            ("ssn", "SSN (123-45-6789):", self.profile.ssn),
            ("occupation", "Occupation:", self.profile.occupation),
            ("street_address", "Street address:", self.profile.street_address),
            ("city", "City:", self.profile.city),
            ("state", "State:", self.profile.state),
            ("zip_code", "ZIP code:", self.profile.zip_code),
        ]

        for attr, prompt, default in fields:
            answer = questionary.text(prompt, default=default or "").ask()
            if answer is None:
                raise KeyboardInterrupt
            setattr(self.profile, attr, answer)

        # Foreign address
        is_foreign = questionary.confirm(
            "Do you have a foreign address?",
            default=self.profile.foreign_address,
        ).ask()
        self.profile.foreign_address = is_foreign
        if is_foreign:
            country = questionary.text(
                "Country:", default=self.profile.country
            ).ask()
            self.profile.country = country or "Mexico"
            self.profile.foreign_country = self.profile.country

        self.session.personal_info = {
            "first_name": self.profile.first_name,
            "last_name": self.profile.last_name,
        }
        self._save_profile()

    # ── Step 6: Income Review ────────────────────────────────────────

    def _step_income_review(self):
        console.print("\n[bold]Step 6: Income Review[/bold]")

        # Apply any parsed document results to profile
        self._apply_parsed_results()

        # How many businesses?
        num_biz = questionary.text(
            "How many Schedule C businesses do you have?",
            default=str(len(self.profile.businesses) or 1),
        ).ask()

        try:
            num_biz = int(num_biz)
        except (TypeError, ValueError):
            num_biz = 1

        # Collect business info
        self.profile.businesses = []
        for i in range(num_biz):
            console.print(f"\n[bold]Business #{i+1}[/bold]")
            name = questionary.text(f"Business name:").ask() or f"Business {i+1}"
            gross = questionary.text("Gross receipts ($):", default="0").ask()
            try:
                gross_val = float(gross.replace(",", "").replace("$", ""))
            except (ValueError, AttributeError):
                gross_val = 0.0

            biz_type = questionary.select(
                "Business type:",
                choices=[
                    questionary.Choice("Single Member LLC", value="single_member_llc"),
                    questionary.Choice("Sole Proprietorship", value="sole_proprietorship"),
                ],
            ).ask()

            self.profile.businesses.append(ScheduleCData(
                business_name=name,
                gross_receipts=gross_val,
                business_type=BusinessType(biz_type or "single_member_llc"),
            ))

        # K-1s
        has_k1 = questionary.confirm("Do you have any K-1s?", default=bool(self.profile.schedule_k1s)).ask()
        if has_k1:
            num_k1 = questionary.text("How many K-1s?", default="1").ask()
            try:
                num_k1 = int(num_k1)
            except (TypeError, ValueError):
                num_k1 = 1

            self.profile.schedule_k1s = []
            for i in range(num_k1):
                console.print(f"\n[bold]K-1 #{i+1}[/bold]")
                pname = questionary.text("Partnership name:").ask() or f"Partnership {i+1}"
                rental = questionary.text("Net rental income ($, negative for loss):", default="0").ask()
                try:
                    rental_val = float(rental.replace(",", "").replace("$", ""))
                except (ValueError, AttributeError):
                    rental_val = 0.0

                self.profile.schedule_k1s.append(ScheduleK1(
                    partnership_name=pname,
                    net_rental_income=rental_val,
                ))

        self._save_profile()

    # ── Step 7: Business Expenses ────────────────────────────────────

    def _step_business_expenses(self):
        console.print("\n[bold]Step 7: Business Expenses[/bold]")

        for biz in self.profile.businesses:
            console.print(f"\n[bold]{biz.business_name}[/bold] (Gross: {format_currency(biz.gross_receipts)})")

            expense_categories = [
                ("office_expense", "Office expense"),
                ("supplies", "Supplies"),
                ("travel", "Travel"),
                ("meals", "Meals (will be 50% deductible)"),
                ("advertising", "Advertising"),
                ("legal_and_professional", "Legal & professional"),
                ("car_and_truck", "Car & truck"),
                ("insurance", "Insurance"),
                ("contract_labor", "Contract labor"),
                ("taxes_licenses", "Taxes & licenses"),
                ("other_expenses", "Other expenses"),
            ]

            expenses = BusinessExpenses()
            for attr, label in expense_categories:
                answer = questionary.text(f"  {label} ($):", default="0").ask()
                try:
                    val = float(answer.replace(",", "").replace("$", ""))
                except (ValueError, AttributeError):
                    val = 0.0
                setattr(expenses, attr, val)

            biz.expenses = expenses

            # Home office
            has_ho = questionary.confirm(
                "Do you have a home office for this business?", default=False
            ).ask()
            if has_ho:
                method = questionary.select(
                    "Home office method:",
                    choices=[
                        questionary.Choice("Simplified ($5/sqft, max 300)", value="simplified"),
                        questionary.Choice("Regular (Form 8829)", value="regular"),
                    ],
                ).ask()

                if method == "simplified":
                    sqft = questionary.text("Square footage:", default="200").ask()
                    biz.home_office = HomeOffice(
                        use_simplified_method=True,
                        square_footage=float(sqft or "0"),
                    )
                else:
                    total_sqft = questionary.text("Total home sq ft:", default="1000").ask()
                    office_sqft = questionary.text("Office sq ft:", default="200").ask()
                    rent = questionary.text("Monthly rent ($):", default="0").ask()
                    utils = questionary.text("Monthly utilities ($):", default="0").ask()
                    internet = questionary.text("Monthly internet ($):", default="0").ask()
                    inet_pct = questionary.text("Internet business use %:", default="50").ask()

                    biz.home_office = HomeOffice(
                        use_simplified_method=False,
                        total_home_sqft=float(total_sqft or "0"),
                        office_sqft=float(office_sqft or "0"),
                        rent=float(rent or "0") * 12,
                        utilities=float(utils or "0") * 12,
                        internet=float(internet or "0") * 12,
                        internet_business_pct=float(inet_pct or "50"),
                    )

        self._save_profile()

    # ── Step 8: Deductions ───────────────────────────────────────────

    def _step_deductions(self):
        console.print("\n[bold]Step 8: Deductions[/bold]")
        console.print("[dim]Standard deduction is used for most situations.[/dim]")
        console.print("[dim]QBI (Section 199A) deduction is calculated automatically.[/dim]")

        # Health insurance
        has_health = questionary.confirm(
            "Do you have self-employed health insurance?", default=False
        ).ask()
        if has_health:
            provider = questionary.text("Insurance provider:", default="").ask()
            premiums = questionary.text("Annual premiums ($):", default="0").ask()
            try:
                prem_val = float(premiums.replace(",", "").replace("$", ""))
            except (ValueError, AttributeError):
                prem_val = 0.0

            self.profile.health_insurance = HealthInsurance(
                provider=provider or "",
                total_premiums=prem_val,
            )

        # Estimated payments
        has_est = questionary.confirm(
            "Did you make estimated tax payments?", default=False
        ).ask()
        if has_est:
            self.profile.estimated_payments = []
            for q in range(1, 5):
                amt = questionary.text(f"  Q{q} payment ($):", default="0").ask()
                try:
                    amt_val = float(amt.replace(",", "").replace("$", ""))
                except (ValueError, AttributeError):
                    amt_val = 0.0
                if amt_val > 0:
                    self.profile.estimated_payments.append(
                        EstimatedPayment(quarter=q, amount=amt_val)
                    )

        self._save_profile()

    # ── Step 9: Foreign Income ───────────────────────────────────────

    def _step_foreign_income(self):
        console.print("\n[bold]Step 9: Foreign Income[/bold]")

        is_abroad = questionary.confirm(
            "Did you live abroad during 2025?",
            default=self.profile.foreign_address,
        ).ask()

        if not is_abroad:
            self.profile.days_in_foreign_country_2025 = 0
            return

        country = questionary.text(
            "Foreign country:", default=self.profile.foreign_country or "Mexico"
        ).ask()
        self.profile.foreign_country = country or "Mexico"

        days = questionary.text(
            "Days physically present in the foreign country:",
            default=str(self.profile.days_in_foreign_country_2025 or 330),
        ).ask()
        try:
            self.profile.days_in_foreign_country_2025 = int(days or "0")
        except ValueError:
            self.profile.days_in_foreign_country_2025 = 0

        days_us = questionary.text(
            "Days in the US during 2025:", default="0"
        ).ask()
        try:
            self.profile.days_in_us_2025 = int(days_us or "0")
        except ValueError:
            self.profile.days_in_us_2025 = 0

        if self.profile.days_in_foreign_country_2025 >= 330:
            console.print("[green]You meet the Physical Presence Test "
                          "for the Foreign Earned Income Exclusion (FEIE).[/green]")
        else:
            console.print("[yellow]You may not meet the Physical Presence Test "
                          f"({self.profile.days_in_foreign_country_2025}/330 days).[/yellow]")

        self._save_profile()

    # ── Step 10: Calculate ───────────────────────────────────────────

    def _step_calculate(self):
        console.print("\n[bold]Step 10: Tax Calculation[/bold]")
        console.print("Calculating your return...")

        self.result = calculate_return(self.profile)

        console.print()
        display_income_table(
            self.result.schedule_c_results,
            self.result.schedule_e,
        )
        console.print()
        display_tax_breakdown(self.result)
        console.print()
        display_result_panel(self.result)

        # Persist results for export/review commands
        self.session.results = serialize_result(self.result)
        self.session.save()

    # ── Step 11: Optimization ────────────────────────────────────────

    def _step_optimization(self):
        console.print("\n[bold]Step 11: Optimization[/bold]")

        if not self.result:
            console.print("[yellow]No calculation results available.[/yellow]")
            return

        # FEIE comparison
        if self.profile.days_in_foreign_country_2025 >= 330:
            console.print("\n[bold]FEIE Analysis[/bold]")
            scenarios = compare_feie_scenarios(self.profile)
            display_feie_comparison(scenarios)

            # Persist FEIE result for PDF generation (Form 2555)
            feie_result = scenarios.get("feie_result")
            if feie_result and feie_result.is_beneficial:
                self.result.feie = feie_result

        # General optimization recommendations
        console.print("\n[bold]Optimization Recommendations[/bold]")
        recs = generate_optimization_recommendations(self.result, self.profile)
        display_optimization_recommendations(recs)

        # Persist updated result (FEIE may have been added)
        self.session.results = serialize_result(self.result)
        self.session.save()

    # ── Step 12: Generate Forms ──────────────────────────────────────

    def _step_generate_forms(self):
        console.print("\n[bold]Step 12: Generate Forms[/bold]")

        if not self.result:
            console.print("[yellow]No results to generate forms from.[/yellow]")
            return

        output_dir = questionary.text(
            "Output directory:", default="output"
        ).ask() or "output"

        console.print(f"Generating forms to [bold]{output_dir}[/bold]...")

        # Generate text reports
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        summary = generate_tax_summary(self.result, self.profile)
        (output_path / "tax_summary.txt").write_text(summary)
        console.print("  [green]tax_summary.txt[/green]")

        checklist = generate_filing_checklist(self.result, self.profile)
        (output_path / "filing_checklist.txt").write_text(checklist)
        console.print("  [green]filing_checklist.txt[/green]")

        # Try PDF generation
        try:
            from taxman.fill_forms import generate_all_forms
            forms = generate_all_forms(self.result, self.profile, output_dir)
            for f in forms:
                console.print(f"  [green]{Path(f).name}[/green]")
        except Exception as e:
            console.print(f"[yellow]PDF generation: {e}[/yellow]")
            console.print("[dim]Text reports were generated successfully.[/dim]")

        self.session.generated_forms = [str(output_path)]

    # ── Step 13: Filing Checklist ────────────────────────────────────

    def _step_filing_checklist(self):
        console.print("\n[bold]Step 13: Filing Checklist[/bold]")

        checklist = generate_filing_checklist(self.result, self.profile)
        console.print(checklist)

        # Quarterly plan
        if self.result:
            prior_tax = questionary.text(
                "Prior year total tax (for estimated payments):",
                default="30000",
            ).ask()
            try:
                prior_val = float(prior_tax.replace(",", "").replace("$", ""))
            except (ValueError, AttributeError):
                prior_val = 30_000.0

            est = estimate_quarterly_payments(
                self.result.total_tax, prior_val, self.result.agi,
                filing_status=self.profile.filing_status,
            )
            display_quarterly_plan(est)

        console.print("\n[bold green]Done! Your tax return preparation is complete.[/bold green]")
        console.print(f"[dim]Session: {self.session.session_id}[/dim]")
