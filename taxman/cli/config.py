"""Configuration management for Tax Man CLI.

Loads user config from ~/.taxman/config.toml.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Python 3.10 fallback


CONFIG_DIR = Path.home() / ".taxman"
CONFIG_FILE = CONFIG_DIR / "config.toml"
SESSIONS_DIR = CONFIG_DIR / "sessions"


@dataclass
class TaxManConfig:
    """User configuration."""
    documents_dir: str = ""
    output_dir: str = "output"
    taxpayer_first_name: str = ""
    taxpayer_last_name: str = ""
    filing_status: str = ""
    foreign_country: str = ""
    default_prior_year_tax: float = 0.0

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "TaxManConfig":
        """Load config from TOML file."""
        config_path = path or CONFIG_FILE
        config = cls()

        if config_path.exists():
            with open(config_path, "rb") as f:
                data = tomllib.load(f)

            general = data.get("general", {})
            config.documents_dir = general.get("documents_dir", "")
            config.output_dir = general.get("output_dir", "output")

            taxpayer = data.get("taxpayer", {})
            config.taxpayer_first_name = taxpayer.get("first_name", "")
            config.taxpayer_last_name = taxpayer.get("last_name", "")
            config.filing_status = taxpayer.get("filing_status", "")
            config.foreign_country = taxpayer.get("foreign_country", "")
            config.default_prior_year_tax = taxpayer.get("prior_year_tax", 0.0)

        return config

    def ensure_dirs(self):
        """Create config and session directories if needed."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
