"""
Notes tool.
Saves notes/reminders to notes.json in the project root.
Supports: save, view/list, delete by number.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

_NOTES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "notes.json")


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _load() -> list[dict]:
    if not os.path.exists(_NOTES_FILE):
        return []
    try:
        with open(_NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(notes: list[dict]) -> None:
    with open(_NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Public actions
# ---------------------------------------------------------------------------

def add_note(text: str) -> str:
    notes = _load()
    note = {
        "id": len(notes) + 1,
        "text": text.strip(),
        "created": datetime.now().strftime("%b %d, %I:%M %p"),
    }
    notes.append(note)
    _save(notes)
    return f"📝 Got it! Saved: \"{text.strip()}\""


def get_notes() -> str:
    notes = _load()
    if not notes:
        return (
            "📋 You have no notes yet.\n"
            "Try: \"remind me to buy milk\" or \"note: call the dentist\""
        )
    lines = [f"📋 Your notes ({len(notes)}):"]
    for n in notes:
        lines.append(f"  {n['id']}. {n['text']}  ·  {n['created']}")
    lines.append("\nSay \"delete note 2\" to remove one.")
    return "\n".join(lines)


def delete_note(idx: int) -> str:
    notes = _load()
    if idx < 1 or idx > len(notes):
        return f"❌ No note #{idx}. Say \"show notes\" to see all."
    removed = notes.pop(idx - 1)
    for i, n in enumerate(notes, 1):
        n["id"] = i
    _save(notes)
    return f"🗑 Deleted note #{idx}: \"{removed['text']}\""


def clear_notes() -> str:
    _save([])
    return "🗑 All notes cleared."


# ---------------------------------------------------------------------------
# Text parsers
# ---------------------------------------------------------------------------

def extract_note_text(text: str) -> str | None:
    """Pull the note content from common natural-language phrases."""
    patterns = [
        r"note\s*[:;]\s*(.+)",
        r"remind\s+me\s+to\s+(.+)",
        r"remember\s+(?:to\s+)?(.+)",
        r"don'?t\s+forget\s+(?:to\s+)?(.+)",
        r"save\s+(?:a?\s*note[:\s]+)?(.+)",
        r"add\s+(?:a?\s*note[:\s]+)?(.+)",
        r"write\s+(?:down\s+)?(.+)",
        r"jot\s+(?:down\s+)?(.+)",
        r"keep\s+(?:a?\s*note[:\s]+)?(.+)",
        r"memo\s*[:;]?\s*(.+)",
        r"log\s+(?:this\s+)?(.+)",
    ]
    for pat in patterns:
        m = re.search(pat, text.strip(), re.I)
        if m:
            return m.group(1).strip()
    return None


def extract_delete_index(text: str) -> int | None:
    """Extract note number from 'delete note 2', 'remove #3' etc."""
    m = re.search(
        r"(?:delete|remove|erase|clear)\s+(?:note\s+)?#?(\d+)", text, re.I
    )
    if m:
        return int(m.group(1))
    return None


def is_view_request(text: str) -> bool:
    """True if user wants to see their notes."""
    return bool(re.search(
        r"\b(show|view|list|see|display|tell me|what are|read|get)\b.{0,30}\bnotes?\b"
        r"|notes?\b.{0,20}\b(show|list|view|see|display|read|get)\b"
        r"|\bmy notes?\b"
        r"|\bshow notes?\b"
        r"|\blist notes?\b"
        r"|\bview notes?\b",
        text, re.I
    ))


def is_clear_request(text: str) -> bool:
    return bool(re.search(
        r"(clear|delete|remove|erase)\s+all\s+notes?", text, re.I
    ))
