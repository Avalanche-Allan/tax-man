"""PDF form filler for IRS tax forms.

Downloads official IRS fillable PDFs and fills them with calculated values.
Uses PyPDFForm for pure-Python PDF manipulation (no pdftk needed).
"""

import os
import urllib.request
from pathlib import Path

from PyPDFForm import PdfWrapper


# =============================================================================
# IRS Form URLs (2025 tax year / 2026 filing season)
# =============================================================================

IRS_FORM_URLS = {
    "f1040": "https://www.irs.gov/pub/irs-pdf/f1040.pdf",
    "f1040s1": "https://www.irs.gov/pub/irs-pdf/f1040s1.pdf",   # Schedule 1
    "f1040s2": "https://www.irs.gov/pub/irs-pdf/f1040s2.pdf",   # Schedule 2
    "f1040s3": "https://www.irs.gov/pub/irs-pdf/f1040s3.pdf",   # Schedule 3
    "f1040sc": "https://www.irs.gov/pub/irs-pdf/f1040sc.pdf",   # Schedule C
    "f1040se": "https://www.irs.gov/pub/irs-pdf/f1040se.pdf",   # Schedule E
    "f1040sse": "https://www.irs.gov/pub/irs-pdf/f1040sse.pdf", # Schedule SE
    "f2555": "https://www.irs.gov/pub/irs-pdf/f2555.pdf",       # FEIE
    "f8995": "https://www.irs.gov/pub/irs-pdf/f8995.pdf",       # QBI simplified
    "f8995a": "https://www.irs.gov/pub/irs-pdf/f8995a.pdf",     # QBI full
}

FORMS_DIR = Path("/home/user/taxman/forms")


def download_irs_form(form_key: str, force: bool = False) -> Path:
    """Download an IRS PDF form if not already cached."""
    FORMS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = FORMS_DIR / f"{form_key}.pdf"
    if output_path.exists() and not force:
        return output_path

    url = IRS_FORM_URLS.get(form_key)
    if not url:
        raise ValueError(f"Unknown form: {form_key}. Available: {list(IRS_FORM_URLS.keys())}")

    print(f"Downloading {form_key} from {url}...")
    urllib.request.urlretrieve(url, output_path)
    print(f"Saved to {output_path}")
    return output_path


def download_all_forms(force: bool = False):
    """Download all required IRS forms."""
    for form_key in IRS_FORM_URLS:
        try:
            download_irs_form(form_key, force=force)
        except Exception as e:
            print(f"Failed to download {form_key}: {e}")


def inspect_form_fields(form_key: str) -> dict:
    """Inspect a PDF form to discover its fillable field names and types.

    This is essential for building the field mapping — we need to know
    the exact PDF field names to fill them programmatically.
    """
    pdf_path = download_irs_form(form_key)
    wrapper = PdfWrapper(str(pdf_path))

    fields = {}
    for page_num, page_fields in enumerate(wrapper.schema.items()):
        field_name, field_info = page_fields
        fields[field_name] = {
            "type": str(type(field_info).__name__),
            "value": str(field_info) if field_info else None,
        }

    # Alternative: use schema property which gives all fields
    try:
        schema = wrapper.schema
        for name, info in schema.items():
            if name not in fields:
                fields[name] = {"type": "unknown", "value": str(info)}
    except Exception:
        pass

    return fields


def inspect_form_fields_raw(form_key: str) -> list[str]:
    """Get raw list of all field names in a PDF form using pypdf."""
    from pypdf import PdfReader

    pdf_path = download_irs_form(form_key)
    reader = PdfReader(str(pdf_path))

    field_names = []
    if reader.get_fields():
        for name, field in reader.get_fields().items():
            field_type = field.get('/FT', 'unknown')
            field_names.append(f"{name} [{field_type}]")

    return sorted(field_names)


def fill_form(form_key: str, data: dict, output_path: str) -> str:
    """Fill a PDF form with data and save the output.

    Args:
        form_key: Key from IRS_FORM_URLS (e.g., "f1040", "f1040sc")
        data: Dict mapping PDF field names to values
        output_path: Where to save the filled PDF

    Returns:
        Path to the filled PDF
    """
    pdf_path = download_irs_form(form_key)

    wrapper = PdfWrapper(str(pdf_path))
    wrapper.fill(data)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "wb") as f:
        f.write(wrapper.read())

    print(f"Filled {form_key} → {output}")
    return str(output)


def fill_and_flatten(form_key: str, data: dict, output_path: str) -> str:
    """Fill and flatten a PDF form (makes fields non-editable).

    Uses PyPDFForm's flatten=True parameter to burn field values
    into the page content, making the form read-only.
    """
    pdf_path = download_irs_form(form_key)

    wrapper = PdfWrapper(str(pdf_path))
    wrapper.fill(data, flatten=True)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "wb") as f:
        f.write(wrapper.read())

    print(f"Filled and flattened {form_key} → {output}")
    return str(output)
