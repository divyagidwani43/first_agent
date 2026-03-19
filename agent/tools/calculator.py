"""
Calculator tool.
Supports +, -, * with both expression syntax and natural language.
Safe: no eval() — pure regex-based.
"""

from __future__ import annotations

import re


def calculate(text: str) -> str:
    """
    Parse and evaluate a simple math expression from user text.
    Supports: +, -, * (integers and decimals).
    """

    # --- Direct numeric expression: "5+2", "10 - 3", "4 * 5" ---
    m = re.search(r"(\d+(?:\.\d+)?)\s*([+\-*])\s*(\d+(?:\.\d+)?)", text)
    if m:
        a, op, b = float(m.group(1)), m.group(2), float(m.group(3))
        result = _apply(a, op, b)
        return _fmt(a, op, b, result)

    text_l = text.lower()

    # --- Natural language: "add 5 and 3" / "5 plus 3" ---
    m = re.search(r"(\d+(?:\.\d+)?)\s+plus\s+(\d+(?:\.\d+)?)", text_l)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return _fmt(a, "+", b, a + b)

    m = re.search(r"add\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)", text_l)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return _fmt(a, "+", b, a + b)

    # --- "subtract 10 from 20" / "10 minus 5" ---
    m = re.search(r"subtract\s+(\d+(?:\.\d+)?)\s+from\s+(\d+(?:\.\d+)?)", text_l)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return _fmt(b, "-", a, b - a)

    m = re.search(r"(\d+(?:\.\d+)?)\s+minus\s+(\d+(?:\.\d+)?)", text_l)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return _fmt(a, "-", b, a - b)

    # --- "multiply 4 by 5" / "4 times 5" ---
    m = re.search(r"multiply\s+(\d+(?:\.\d+)?)\s+by\s+(\d+(?:\.\d+)?)", text_l)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return _fmt(a, "*", b, a * b)

    m = re.search(r"(\d+(?:\.\d+)?)\s+times\s+(\d+(?:\.\d+)?)", text_l)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return _fmt(a, "*", b, a * b)

    return "I couldn't parse that. Try: '5+2', '10 - 3', 'multiply 4 by 5'."


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply(a: float, op: str, b: float) -> float:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    return a * b  # *


def _fmt(a: float, op: str, b: float, result: float) -> str:
    """Format numbers: drop .0 for whole numbers."""
    def n(x: float) -> str:
        return str(int(x)) if x == int(x) else str(x)
    return f"🔢 {n(a)} {op} {n(b)} = {n(result)}"
