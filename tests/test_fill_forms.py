"""Tests for form filling infrastructure."""

import os
from pathlib import Path

import pytest

from taxman.fill_forms import FORMS_DIR, IRS_FORM_URLS


class TestFormsDir:
    def test_forms_dir_not_hardcoded(self):
        """Bug 7 fix: FORMS_DIR should use package-relative path."""
        assert "/home/user/" not in str(FORMS_DIR)

    def test_forms_dir_env_override(self, monkeypatch, tmp_path):
        """TAXMAN_FORMS_DIR env var overrides default."""
        monkeypatch.setenv("TAXMAN_FORMS_DIR", str(tmp_path))
        # Re-import to pick up env var
        import importlib
        import taxman.fill_forms
        importlib.reload(taxman.fill_forms)
        assert taxman.fill_forms.FORMS_DIR == tmp_path
        # Restore
        monkeypatch.delenv("TAXMAN_FORMS_DIR", raising=False)
        importlib.reload(taxman.fill_forms)


class TestIRSFormURLs:
    def test_all_urls_are_irs(self):
        for key, url in IRS_FORM_URLS.items():
            assert url.startswith("https://www.irs.gov/"), f"{key} URL invalid"

    def test_required_forms_present(self):
        required = ["f1040", "f1040sc", "f1040se", "f1040sse", "f2555", "f8995"]
        for form in required:
            assert form in IRS_FORM_URLS, f"Missing {form}"

    def test_all_urls_are_pdf(self):
        for key, url in IRS_FORM_URLS.items():
            assert url.endswith(".pdf"), f"{key} URL doesn't end with .pdf"
