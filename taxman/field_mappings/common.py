"""Common formatting helpers for PDF field mappings."""


def format_ssn(ssn: str) -> str:
    """Format SSN for PDF fields: 123-45-6789."""
    ssn = ssn.replace("-", "").replace(" ", "")
    if len(ssn) == 9:
        return f"{ssn[:3]}-{ssn[3:5]}-{ssn[5:]}"
    return ssn


def format_ein(ein: str) -> str:
    """Format EIN for PDF fields: 12-3456789."""
    ein = ein.replace("-", "").replace(" ", "")
    if len(ein) == 9:
        return f"{ein[:2]}-{ein[2:]}"
    return ein


def format_currency_for_pdf(amount: float) -> str:
    """Format currency for PDF fields — no $ sign, rounded to whole dollars."""
    if amount == 0:
        return ""
    return f"{round(amount):,}"


def format_currency_cents(amount: float) -> str:
    """Format currency with cents for PDF fields."""
    if amount == 0:
        return ""
    return f"{amount:,.2f}"


def checkbox(value: bool) -> str:
    """Return PDF checkbox value."""
    return "Yes" if value else "Off"


def split_ssn(ssn: str) -> tuple:
    """Split SSN into 3 parts for forms with separate boxes."""
    ssn = ssn.replace("-", "").replace(" ", "")
    if len(ssn) == 9:
        return ssn[:3], ssn[3:5], ssn[5:]
    return "", "", ""
