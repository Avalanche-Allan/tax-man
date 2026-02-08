"""Field mappings for IRS PDF form filling.

Each module exports a build_*_data() function that maps calculated
results to PDF field names. Actual field names must be discovered
via inspect_form_fields_raw() against 2025 IRS PDFs.
"""

from taxman.field_mappings.f1040 import build_1040_data
from taxman.field_mappings.f1040sc import build_schedule_c_data
from taxman.field_mappings.f1040se import build_schedule_e_data
from taxman.field_mappings.f1040sse import build_schedule_se_data
from taxman.field_mappings.f8995 import build_8995_data
from taxman.field_mappings.f2555 import build_2555_data

__all__ = [
    "build_1040_data",
    "build_schedule_c_data",
    "build_schedule_e_data",
    "build_schedule_se_data",
    "build_8995_data",
    "build_2555_data",
]
