"""
Agent controller — the "brain" that decides what to do with user input.

Decision flow (priority order):
  1. Rule-based math detection (fast, reliable)
  2. Rule-based location detection (fast, reliable)
  3. ML intent classifier (learned from training examples)
  4. Smart fallback (low-confidence handling)
"""

from __future__ import annotations

import re

from agent.classifier import predict_intent
from agent.tools.calculator import calculate
from agent.tools.weather import extract_city, get_weather

# ---------------------------------------------------------------------------
# Help text shown when agent doesn't understand
# ---------------------------------------------------------------------------

HELP = (
    "I can help with:\n"
    "• 🌤 Weather — just type a city name, e.g. \"London\" or \"weather in Paris\"\n"
    "• 🔢 Calculator (+, -, *) — e.g. \"5+2\", \"20 - 3\", \"multiply 4 by 5\""
)

# ---------------------------------------------------------------------------
# Rule-based detectors (used BEFORE ML for reliable fast-path)
# ---------------------------------------------------------------------------

# Matches pure math: "5+2", "10 - 3", "3 * 4"
_MATH_EXPR = re.compile(r"\d+(?:\.\d+)?\s*[+\-*]\s*\d+(?:\.\d+)?")

# Matches natural language math keywords
_MATH_WORDS = re.compile(
    r"\b(add|subtract|multiply|plus|minus|times)\b", re.I
)

# Greeting words
_GREETINGS = re.compile(r"\b(hi|hello|hey|howdy|greetings)\b", re.I)


def _is_math(text: str) -> bool:
    return bool(_MATH_EXPR.search(text) or _MATH_WORDS.search(text))


def _is_only_letters(text: str) -> bool:
    """True if text is only letters/spaces (likely a place name)."""
    return bool(re.match(r"^[a-zA-Z\s,\.\-]+$", text.strip()))


# ---------------------------------------------------------------------------
# Main agent handler
# ---------------------------------------------------------------------------

def agent_handle(text: str) -> str:
    text = text.strip()
    if not text:
        return "Please type something!"

    # ------------------------------------------------------------------ #
    # STEP 1 — Rule-based: math expressions are unambiguous, handle first #
    # ------------------------------------------------------------------ #
    if _is_math(text):
        return calculate(text)

    # ------------------------------------------------------------------ #
    # STEP 2 — ML classifier                                              #
    # ------------------------------------------------------------------ #
    intent, confidence = predict_intent(text)

    # ------------------------------------------------------------------ #
    # STEP 3 — Route based on intent                                      #
    # ------------------------------------------------------------------ #

    if intent == "weather":
        # Try to extract city from pattern ("weather in X"), else use full text
        city = extract_city(text) or text.strip()
        return get_weather(city)

    if intent == "calculator":
        return calculate(text)

    # ------------------------------------------------------------------ #
    # STEP 4 — Smart fallback for low-confidence / "other" predictions    #
    # ------------------------------------------------------------------ #

    # Greetings
    if _GREETINGS.search(text):
        return f"Hey! 👋 {HELP}"

    # If confidence is low AND text is only letters → likely a place name
    if confidence < 0.6 and _is_only_letters(text):
        city = text.strip()
        return get_weather(city)

    return HELP
