"""Session state management — save/resume wizard progress.

Persists wizard state to ~/.taxman/sessions/<id>.json so users can
quit and resume later.
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from taxman.cli.config import SESSIONS_DIR


@dataclass
class SessionState:
    """Tracks wizard progress and collected data."""
    session_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    completed_steps: list[str] = field(default_factory=list)
    current_step: str = ""

    # Collected data (serialized as dicts)
    filing_status: str = ""
    personal_info: dict = field(default_factory=dict)
    documents_dir: str = ""
    parsed_documents: list[dict] = field(default_factory=list)
    income_data: dict = field(default_factory=dict)
    expense_data: dict = field(default_factory=dict)
    deduction_choices: dict = field(default_factory=dict)
    foreign_info: dict = field(default_factory=dict)

    # Results (set after calculation)
    results: dict = field(default_factory=dict)
    optimization: dict = field(default_factory=dict)
    generated_forms: list[str] = field(default_factory=list)

    @classmethod
    def create(cls) -> "SessionState":
        """Create a new session."""
        now = datetime.now().isoformat()
        return cls(
            session_id=uuid.uuid4().hex[:12],
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def load(cls, session_id: str) -> Optional["SessionState"]:
        """Load a session from disk."""
        path = SESSIONS_DIR / f"{session_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        state = cls()
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)
        return state

    def save(self):
        """Save session to disk."""
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.updated_at = datetime.now().isoformat()
        path = SESSIONS_DIR / f"{self.session_id}.json"
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2, default=str)

    def complete_step(self, step_name: str):
        """Mark a step as completed."""
        if step_name not in self.completed_steps:
            self.completed_steps.append(step_name)
        self.save()

    @property
    def session_path(self) -> Path:
        return SESSIONS_DIR / f"{self.session_id}.json"

    @classmethod
    def list_sessions(cls) -> list[dict]:
        """List all saved sessions."""
        sessions = []
        if SESSIONS_DIR.exists():
            for f in sorted(SESSIONS_DIR.glob("*.json")):
                try:
                    with open(f) as fh:
                        data = json.load(fh)
                    sessions.append({
                        "id": data.get("session_id", f.stem),
                        "created": data.get("created_at", ""),
                        "updated": data.get("updated_at", ""),
                        "steps": len(data.get("completed_steps", [])),
                        "filing_status": data.get("filing_status", ""),
                    })
                except Exception:
                    pass
        return sessions
