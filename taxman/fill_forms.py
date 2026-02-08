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

# Bug 7 fix: Use package-relative path with env var override
_DEFAULT_FORMS_DIR = Path(__file__).resolve().parent.parent / "forms"
FORMS_DIR = Path(os.environ.get("TAXMAN_FORMS_DIR", str(_DEFAULT_FORMS_DIR)))


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

    Bug 10 fix: Single clean iteration over wrapper.schema.items().
    """
    pdf_path = download_irs_form(form_key)
    wrapper = PdfWrapper(str(pdf_path))

    fields = {}
    for field_name, field_info in wrapper.schema.items():
        fields[field_name] = {
            "type": str(type(field_info).__name__),
            "value": str(field_info) if field_info else None,
        }

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


# =============================================================================
# Form Generation Pipeline (Phase 6)
# =============================================================================

def generate_all_forms(result, profile, output_dir: str) -> list[str]:
    """Orchestrate generation of all required tax forms.

    Args:
        result: Form1040Result from calculator
        profile: TaxpayerProfile
        output_dir: Directory to save generated PDFs

    Returns:
        List of paths to generated PDFs
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    generated = []

    # Import field mapping builders lazily to avoid circular imports
    try:
        from taxman.field_mappings import (
            build_1040_data,
            build_schedule_c_data,
            build_schedule_e_data,
            build_schedule_se_data,
            build_8995_data,
            build_2555_data,
        )
    except ImportError:
        print("Field mappings not yet configured — skipping form generation.")
        return generated

    # Form 1040
    try:
        data_1040 = build_1040_data(result, profile)
        path = fill_form("f1040", data_1040, str(output / "f1040_filled.pdf"))
        generated.append(path)
    except Exception as e:
        print(f"Error generating 1040: {e}")

    # Schedule C (one per business)
    for i, sc_result in enumerate(result.schedule_c_results):
        try:
            biz = profile.businesses[i] if i < len(profile.businesses) else None
            data_sc = build_schedule_c_data(sc_result, biz, profile)
            path = fill_form(
                "f1040sc", data_sc,
                str(output / f"schedule_c_{i+1}_filled.pdf")
            )
            generated.append(path)
        except Exception as e:
            print(f"Error generating Schedule C #{i+1}: {e}")

    # Schedule SE
    if result.schedule_se and result.schedule_se.se_tax > 0:
        try:
            data_se = build_schedule_se_data(result.schedule_se, profile)
            path = fill_form("f1040sse", data_se, str(output / "schedule_se_filled.pdf"))
            generated.append(path)
        except Exception as e:
            print(f"Error generating Schedule SE: {e}")

    # Schedule E
    if result.schedule_e:
        try:
            data_e = build_schedule_e_data(result.schedule_e, profile)
            path = fill_form("f1040se", data_e, str(output / "schedule_e_filled.pdf"))
            generated.append(path)
        except Exception as e:
            print(f"Error generating Schedule E: {e}")

    # Form 8995 (QBI)
    if result.qbi and result.qbi.qbi_deduction > 0:
        try:
            data_qbi = build_8995_data(result.qbi, result, profile)
            form_key = "f8995a" if result.qbi.is_limited else "f8995"
            path = fill_form(form_key, data_qbi, str(output / "f8995_filled.pdf"))
            generated.append(path)
        except Exception as e:
            print(f"Error generating Form 8995: {e}")

    # Form 2555 (FEIE) — only if beneficial
    if result.feie and result.feie.is_beneficial:
        try:
            data_2555 = build_2555_data(result.feie, profile)
            path = fill_form("f2555", data_2555, str(output / "f2555_filled.pdf"))
            generated.append(path)
        except Exception as e:
            print(f"Error generating Form 2555: {e}")

    return generated
