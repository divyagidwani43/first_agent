"""
ML intent classifier.
Trained locally with scikit-learn — no LLM, no API key.
Classifies user text into: "weather" | "calculator" | "other"
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# ---------------------------------------------------------------------------
# Training data
# ---------------------------------------------------------------------------

_TRAINING_DATA: list[tuple[str, str]] = [
    # ---- weather: explicit phrases ----
    ("weather in london", "weather"),
    ("give me weather of london", "weather"),
    ("himme weather of london", "weather"),
    ("weather of paris", "weather"),
    ("what is the weather in new york", "weather"),
    ("weather in mumbai", "weather"),
    ("show weather for delhi", "weather"),
    ("forecast for tokyo", "weather"),
    ("temperature in berlin", "weather"),
    ("how is weather in sydney", "weather"),
    ("weather today in chicago", "weather"),
    ("what is the temperature in dubai", "weather"),
    ("tell me the weather in rome", "weather"),
    ("weather report for toronto", "weather"),
    ("is it raining in amsterdam", "weather"),
    ("how hot is it in cairo", "weather"),
    ("what is the climate in moscow", "weather"),
    ("how cold is oslo", "weather"),
    ("weather for los angeles", "weather"),
    # ---- weather: bare city / place names ----
    ("london", "weather"),
    ("paris", "weather"),
    ("new york", "weather"),
    ("tokyo", "weather"),
    ("mumbai", "weather"),
    ("delhi", "weather"),
    ("berlin", "weather"),
    ("sydney", "weather"),
    ("chicago", "weather"),
    ("dubai", "weather"),
    ("rome", "weather"),
    ("toronto", "weather"),
    ("amsterdam", "weather"),
    ("bangalore", "weather"),
    ("los angeles", "weather"),
    ("san francisco", "weather"),
    ("mexico city", "weather"),
    ("rio de janeiro", "weather"),
    ("cairo", "weather"),
    ("moscow", "weather"),
    ("oslo", "weather"),
    ("seoul", "weather"),
    ("beijing", "weather"),
    ("istanbul", "weather"),
    ("jaipur", "weather"),
    ("hyderabad", "weather"),
    ("kolkata", "weather"),
    ("chennai", "weather"),
    ("pune", "weather"),
    ("lahore", "weather"),
    ("karachi", "weather"),
    ("dhaka", "weather"),
    ("kathmandu", "weather"),
    ("colombo", "weather"),
    # ---- calculator: expressions ----
    ("5+2", "calculator"),
    ("5 + 2", "calculator"),
    ("3*4", "calculator"),
    ("10-3", "calculator"),
    ("4*5", "calculator"),
    ("100-50", "calculator"),
    ("6 + 7", "calculator"),
    ("20 - 5", "calculator"),
    ("3 * 3", "calculator"),
    ("8 * 9", "calculator"),
    ("100 + 200", "calculator"),
    ("50 - 25", "calculator"),
    # ---- calculator: natural language ----
    ("give me answer for 5+2", "calculator"),
    ("gimme answer for 3*4", "calculator"),
    ("calculate 10-3", "calculator"),
    ("what is 4*5", "calculator"),
    ("compute 100-50", "calculator"),
    ("what is 6 + 7", "calculator"),
    ("solve 100 + 200", "calculator"),
    ("50 - 25 equals what", "calculator"),
    ("add 5 and 3", "calculator"),
    ("multiply 4 by 5", "calculator"),
    ("subtract 10 from 20", "calculator"),
    ("what is 8 * 9", "calculator"),
    ("plus 3 and 7", "calculator"),
    ("times 6 and 9", "calculator"),
    ("minus 4 from 10", "calculator"),
    # ---- other / greeting ----
    ("hello", "other"),
    ("hi", "other"),
    ("hey there", "other"),
    ("how are you", "other"),
    ("what can you do", "other"),
    ("help", "other"),
    ("who are you", "other"),
    ("what are you", "other"),
    ("good morning", "other"),
    ("thanks", "other"),
    ("thank you", "other"),
]

# ---------------------------------------------------------------------------
# Train on startup
# ---------------------------------------------------------------------------

_texts, _labels = zip(*_TRAINING_DATA)

_vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, min_df=1)
_X = _vectorizer.fit_transform(_texts)

_model = LogisticRegression(max_iter=1000, random_state=42, C=2.0)
_model.fit(_X, _labels)


def predict_intent(text: str) -> tuple[str, float]:
    """
    Predict the intent of user text.
    Returns (label, confidence) where label is one of:
    'weather', 'calculator', 'other'
    """
    x = _vectorizer.transform([text.lower().strip()])
    probs = _model.predict_proba(x)[0]
    idx = int(np.argmax(probs))
    return _model.classes_[idx], float(probs[idx])
