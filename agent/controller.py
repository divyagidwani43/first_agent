"""
Agent controller — the "brain" that decides what to do with user input.

Decision flow (priority order):
  1. Special prefixes (__save_note__, __dismiss__) from button clicks
  2. Rule-based: math expressions (reliable, fast)
  3. ML intent classifier → routes to weather / calculator / time / notes
  4. Smart fallback: action-word heuristic → offer to save as note
                     only-letters heuristic → try as city
"""

from __future__ import annotations

import re
from typing import Union

from agent import classifier as _classifier
from agent.classifier import predict_intent
from agent.feedback_store import load_feedback, save_feedback
from agent.tools.calculator import calculate
from agent.tools.weather import extract_city, get_weather
from agent.tools.datetime_tool import handle as handle_time
from agent.tools.notes import (
    add_note, get_notes, delete_note, clear_notes,
    extract_note_text, extract_delete_index,
    is_view_request, is_clear_request,
)

# Apply any saved user feedback so the model starts smarter each restart
_saved_feedback = load_feedback()
if _saved_feedback:
    _classifier.retrain(_saved_feedback)

# Response type: either a plain string or a dict with reply + optional buttons
ResponseType = Union[str, dict]

# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------

HELP = (
    "I can help with:\n"
    "• 🌤 Weather — e.g. \"London\" or \"weather in Paris\"\n"
    "• 🔢 Calculator — e.g. \"5+2\", \"multiply 4 by 5\"\n"
    "• 🕐 Time & Date — e.g. \"time in Tokyo\", \"what day is today\"\n"
    "• 📝 Notes — e.g. \"remind me to buy milk\", \"show notes\""
)

# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

_MATH_EXPR  = re.compile(r"\d+(?:\.\d+)?\s*[+\-*]\s*\d+(?:\.\d+)?")
_MATH_WORDS = re.compile(r"\b(subtract|multiply|plus|minus|times)\b", re.I)
_GREETINGS  = re.compile(r"\b(hi|hello|hey|howdy|greetings|sup)\b", re.I)

# Words that strongly suggest the user wants to remember/do something
_ACTION_WORDS = re.compile(
    r"\b(get|buy|pick|grab|fetch|order|call|email|send|book|pay|fix|"
    r"clean|wash|cook|read|watch|go to|meet|contact|schedule|plan|"
    r"prepare|check|collect|remind|return|drop|print|sign|submit|review|"
    r"update|cancel|renew|register|apply|follow|visit|post|upload|download)\b",
    re.I,
)


def _is_math(text: str) -> bool:
    return bool(_MATH_EXPR.search(text) or _MATH_WORDS.search(text))


def _is_only_letters(text: str) -> bool:
    return bool(re.match(r"^[a-zA-Z\s,\.\-]+$", text.strip()))


def _looks_like_task(text: str) -> bool:
    """True if text looks like a task/reminder (has an action verb + noun)."""
    return bool(_ACTION_WORDS.search(text))


# ---------------------------------------------------------------------------
# Button helper
# ---------------------------------------------------------------------------

def _with_buttons(reply: str, buttons: list[dict]) -> dict:
    return {"reply": reply, "buttons": buttons}


# ---------------------------------------------------------------------------
# Main agent handler
# ---------------------------------------------------------------------------

def agent_handle(text: str) -> ResponseType:
    text = text.strip()
    if not text:
        return "Please type something!"

    # ------------------------------------------------------------------ #
    # STEP 0 — Handle button-click special prefixes                       #
    # ------------------------------------------------------------------ #
    if text.startswith("__save_note__:"):
        note_text = text[len("__save_note__:"):].strip()
        return add_note(note_text)

    if text == "__dismiss__":
        return "OK! Let me know if you need anything. 😊"

    # ------------------------------------------------------------------ #
    # STEP 0b — Feedback: user flagged a wrong response                   #
    # ------------------------------------------------------------------ #
    if text.startswith("__feedback__:"):
        original = text[len("__feedback__:"):].strip()
        return _with_buttons(
            f'Sorry about that! 😅 What did you mean by "{original}"?\n\nPick the right category:',
            [
                {"label": "🌤 Weather",    "value": f"__feedback_label__: {original} ||| weather"},
                {"label": "🔢 Calculator", "value": f"__feedback_label__: {original} ||| calculator"},
                {"label": "🕐 Time/Date",  "value": f"__feedback_label__: {original} ||| time"},
                {"label": "📝 Notes",      "value": f"__feedback_label__: {original} ||| notes"},
            ],
        )

    if text.startswith("__feedback_label__:"):
        payload  = text[len("__feedback_label__:"):].strip()
        original, label = payload.split(" ||| ", 1)
        original, label = original.strip(), label.strip()
        save_feedback(original, label)
        _classifier.retrain(load_feedback())
        return f'✅ Got it! I\'ll now recognize "{original}" as {label}. Thanks for teaching me! 🎓'

    # ------------------------------------------------------------------ #
    # STEP 1 — Rule-based: math is unambiguous                            #
    # ------------------------------------------------------------------ #
    if _is_math(text):
        return calculate(text)

    # ------------------------------------------------------------------ #
    # STEP 2 — ML classifier                                              #
    # ------------------------------------------------------------------ #
    intent, confidence = predict_intent(text)

    # ------------------------------------------------------------------ #
    # STEP 3 — Route based on ML intent                                   #
    # ------------------------------------------------------------------ #

    if intent == "weather" and confidence > 0.40:
        city = extract_city(text) or text.strip()
        return get_weather(city)

    if intent == "calculator" and confidence > 0.40:
        return calculate(text)

    if intent == "time" and confidence > 0.40:
        return handle_time(text)

    if intent == "notes" and confidence > 0.40:
        return _handle_notes(text)

    # ------------------------------------------------------------------ #
    # STEP 4 — Smart fallback                                             #
    # ------------------------------------------------------------------ #

    # Greetings
    if _GREETINGS.search(text):
        return f"Hey! 👋\n\n{HELP}"

    # Text has action words → offer to save as a reminder (check BEFORE city fallback)
    if _looks_like_task(text):
        return _with_buttons(
            f"Hmm, I'm not sure what you mean by \"{text}\"."
            f"\n\nDid you want to save this as a note/reminder?",
            [
                {"label": "✅ Yes, save it", "value": f"__save_note__: {text}"},
                {"label": "❌ No thanks",    "value": "__dismiss__"},
            ],
        )

    # Text is only letters and low confidence → likely a city name
    if _is_only_letters(text) and confidence < 0.55:
        return get_weather(text.strip())

    return f"I'm not sure about that.\n\n{HELP}"


# ---------------------------------------------------------------------------
# Notes sub-router
# ---------------------------------------------------------------------------

def _handle_notes(text: str) -> ResponseType:
    # Delete
    idx = extract_delete_index(text)
    if idx is not None:
        return delete_note(idx)

    # Clear all
    if is_clear_request(text):
        return _with_buttons(
            "Are you sure you want to delete ALL notes?",
            [
                {"label": "🗑 Yes, clear all", "value": "__save_note__: __clear_all__"},
                {"label": "❌ Cancel",          "value": "__dismiss__"},
            ],
        )

    # View
    if is_view_request(text):
        return get_notes()

    # Save
    note_text = extract_note_text(text)
    if note_text:
        return add_note(note_text)

    # Ambiguous — offer to save full text as note
    return _with_buttons(
        f"Did you want to save \"{text}\" as a note?",
        [
            {"label": "✅ Yes, save it", "value": f"__save_note__: {text}"},
            {"label": "❌ No",           "value": "__dismiss__"},
        ],
    )
