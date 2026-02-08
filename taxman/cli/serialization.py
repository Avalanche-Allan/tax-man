"""Serialization/deserialization for TaxpayerProfile and Form1040Result.

Keeps serialization logic out of models (pure data) and wizard (UI).
Handles enums, nested dataclasses, and lists of models.
"""

from dataclasses import asdict, fields
from enum import Enum
from typing import Optional

from taxman.models import (
    AccountingMethod,
    BusinessExpenses,
    BusinessType,
    CharityReceipt,
    Dependent,
    EstimatedPayment,
    FilingStatus,
    Form1095A,
    Form1098,
    Form1099B,
    Form1099DIV,
    Form1099INT,
    Form1099NEC,
    FormW2,
    HealthInsurance,
    HomeOffice,
    ScheduleCData,
    ScheduleK1,
    TaxpayerProfile,
)


def serialize_profile(profile: TaxpayerProfile) -> dict:
    """Serialize a TaxpayerProfile to a JSON-safe dict."""
    d = asdict(profile)
    # Convert enums to their string values
    d["filing_status"] = profile.filing_status.value
    for i, biz in enumerate(d.get("businesses", [])):
        biz["business_type"] = profile.businesses[i].business_type.value
        biz["accounting_method"] = profile.businesses[i].accounting_method.value
    return d


def deserialize_profile(data: dict) -> TaxpayerProfile:
    """Reconstruct a TaxpayerProfile from a serialized dict."""
    if not data:
        return TaxpayerProfile()

    # Work on a copy to avoid mutating the input
    d = dict(data)

    # Enums
    d["filing_status"] = FilingStatus(d.get("filing_status", "mfs"))

    # Nested list models
    d["forms_w2"] = [FormW2(**w) for w in d.get("forms_w2", [])]
    d["forms_1098"] = [Form1098(**f) for f in d.get("forms_1098", [])]
    d["forms_1099_nec"] = [Form1099NEC(**f) for f in d.get("forms_1099_nec", [])]
    d["forms_1099_int"] = [Form1099INT(**f) for f in d.get("forms_1099_int", [])]
    d["forms_1099_div"] = [Form1099DIV(**f) for f in d.get("forms_1099_div", [])]
    d["forms_1099_b"] = [Form1099B(**f) for f in d.get("forms_1099_b", [])]
    d["schedule_k1s"] = [ScheduleK1(**k) for k in d.get("schedule_k1s", [])]
    d["dependents"] = [Dependent(**dep) for dep in d.get("dependents", [])]
    d["estimated_payments"] = [
        EstimatedPayment(**p) for p in d.get("estimated_payments", [])
    ]

    # Businesses with nested HomeOffice and BusinessExpenses
    businesses = []
    for biz_dict in d.get("businesses", []):
        biz_dict = dict(biz_dict)
        biz_dict["business_type"] = BusinessType(
            biz_dict.get("business_type", "single_member_llc")
        )
        biz_dict["accounting_method"] = AccountingMethod(
            biz_dict.get("accounting_method", "cash")
        )
        # Nested expenses
        expenses_data = biz_dict.get("expenses")
        if isinstance(expenses_data, dict):
            biz_dict["expenses"] = BusinessExpenses(**expenses_data)
        # Nested home_office
        ho_data = biz_dict.get("home_office")
        if isinstance(ho_data, dict):
            biz_dict["home_office"] = HomeOffice(**ho_data)
        businesses.append(ScheduleCData(**biz_dict))
    d["businesses"] = businesses

    # Optional HealthInsurance
    hi_data = d.get("health_insurance")
    if isinstance(hi_data, dict):
        d["health_insurance"] = HealthInsurance(**hi_data)

    return TaxpayerProfile(**d)


def serialize_result(result) -> dict:
    """Serialize a Form1040Result to a JSON-safe dict.

    Converts nested dataclass results using asdict.
    """
    if result is None:
        return {}
    return asdict(result)


def deserialize_result(data: dict):
    """Reconstruct a Form1040Result from a serialized dict."""
    if not data:
        return None

    from taxman.calculator import (
        Form1040Result,
        Form2555Result,
        Form6251Result,
        Form8995Result,
        LineItem,
        ScheduleCResult,
        ScheduleDResult,
        ScheduleEResult,
        ScheduleSEResult,
        TaxCreditsResult,
    )

    d = dict(data)

    # Reconstruct LineItem lists
    d["lines"] = [LineItem(**li) for li in d.get("lines", [])]

    # Schedule C results
    sc_results = []
    for sc in d.get("schedule_c_results", []):
        sc = dict(sc)
        sc["lines"] = [LineItem(**li) for li in sc.get("lines", [])]
        sc_results.append(ScheduleCResult(**sc))
    d["schedule_c_results"] = sc_results

    # Schedule SE
    se = d.get("schedule_se")
    if se:
        se = dict(se)
        se["lines"] = [LineItem(**li) for li in se.get("lines", [])]
        d["schedule_se"] = ScheduleSEResult(**se)

    # Schedule E
    sch_e = d.get("schedule_e")
    if sch_e:
        sch_e = dict(sch_e)
        sch_e["lines"] = [LineItem(**li) for li in sch_e.get("lines", [])]
        d["schedule_e"] = ScheduleEResult(**sch_e)

    # Schedule D
    sch_d = d.get("schedule_d")
    if sch_d:
        sch_d = dict(sch_d)
        sch_d["lines"] = [LineItem(**li) for li in sch_d.get("lines", [])]
        d["schedule_d"] = ScheduleDResult(**sch_d)

    # Form 6251 (AMT)
    f6251 = d.get("form_6251")
    if f6251:
        f6251 = dict(f6251)
        f6251["lines"] = [LineItem(**li) for li in f6251.get("lines", [])]
        d["form_6251"] = Form6251Result(**f6251)

    # Tax Credits
    tc = d.get("tax_credits")
    if tc:
        tc = dict(tc)
        tc["lines"] = [LineItem(**li) for li in tc.get("lines", [])]
        d["tax_credits"] = TaxCreditsResult(**tc)

    # QBI
    qbi = d.get("qbi")
    if qbi:
        qbi = dict(qbi)
        qbi["lines"] = [LineItem(**li) for li in qbi.get("lines", [])]
        d["qbi"] = Form8995Result(**qbi)

    # FEIE
    feie = d.get("feie")
    if feie:
        feie = dict(feie)
        feie["lines"] = [LineItem(**li) for li in feie.get("lines", [])]
        d["feie"] = Form2555Result(**feie)

    return Form1040Result(**d)
