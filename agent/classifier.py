"""
ML intent classifier — trained on startup from agent/training_data.py.
No training examples live here; edit training_data.py to add patterns.

Classifies text into: "weather" | "calculator" | "time" | "notes" | "other"
Supports live retraining via retrain() when the user gives feedback.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from agent.training_data import TRAINING_DATA

# ---------------------------------------------------------------------------
# Model objects (module-level so retrain() can replace them in-place)
# ---------------------------------------------------------------------------

_vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, min_df=1)
_model      = LogisticRegression(max_iter=1000, random_state=42, C=2.0)


def _fit(data: list[tuple[str, str]]) -> None:
    """Internal: fit vectorizer + model on the given examples."""
    texts, labels = zip(*data)
    _vectorizer.fit(texts)
    X = _vectorizer.transform(texts)
    _model.fit(X, labels)


# Train on startup with the base dataset
_fit(TRAINING_DATA)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_intent(text: str) -> tuple[str, float]:
    """Return (label, confidence) for the given text."""
    x    = _vectorizer.transform([text.lower().strip()])
    probs = _model.predict_proba(x)[0]
    idx  = int(np.argmax(probs))
    return _model.classes_[idx], float(probs[idx])


def retrain(extra_examples: list[tuple[str, str]]) -> None:
    """
    Re-train the model with base data plus user-corrected examples.
    Called automatically whenever a feedback correction is saved.
    """
    _fit(list(TRAINING_DATA) + extra_examples)
