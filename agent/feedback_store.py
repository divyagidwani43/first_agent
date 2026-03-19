"""
Feedback store — persists user-corrected intent examples between restarts.

When a user marks an agent response as wrong and selects the correct intent,
that (text, label) pair is saved to feedback_data.json.
On next startup, classifier.retrain() picks these up automatically.
"""

from __future__ import annotations

import json
from pathlib import Path

_FEEDBACK_FILE = Path(__file__).parent.parent / "feedback_data.json"


def load_feedback() -> list[tuple[str, str]]:
    """Return all saved corrections as (text, label) pairs."""
    if not _FEEDBACK_FILE.exists():
        return []
    with open(_FEEDBACK_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return [(item["text"], item["label"]) for item in data]


def save_feedback(text: str, label: str) -> None:
    """Append a new correction to the feedback file."""
    existing: list[dict] = []
    if _FEEDBACK_FILE.exists():
        with open(_FEEDBACK_FILE, encoding="utf-8") as f:
            existing = json.load(f)
    existing.append({"text": text, "label": label})
    with open(_FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def feedback_count() -> int:
    """How many corrections have been saved."""
    return len(load_feedback())
