# How This Local AI Agent Works

A plain-English explanation of every part of the project — no jargon skipped.

---

## Big Picture

```
User types something
       ↓
   Chat UI (browser)
       ↓ HTTP POST /chat
  Flask (app.py)
       ↓
  Agent Controller  ← the "brain"
    ↙    ↓    ↘    ↘
Weather  Calc  Time  Notes
  API  (local)(local)(local file)
       ↓
  Response → back to UI
```

---

## 1. The UI (`templates/index.html`)

A single HTML page served by Flask.

- No React / Vue / framework — pure HTML + CSS + vanilla JavaScript.
- The user types a message and presses Enter or ▶.
- JS sends a `POST /chat` request with `{ "message": "user text" }`.
- It waits for a JSON response `{ "reply": "..." }` (optionally with `"buttons": [...]`).
- If the response contains buttons (Yes/No confirmations), the JS renders them as clickable chips.
- Clicking a button sends its hidden `value` as the next message (e.g. `__save_note__: buy eggs`).

---

## 2. Flask Entry Point (`app.py`)

A tiny Python web server with just two routes:

| Route | What it does |
|---|---|
| `GET /` | Serves the chat page (`index.html`) |
| `POST /chat` | Receives user message, calls `agent_handle()`, returns JSON |

It doesn't know anything about weather, math, or notes. It just talks to the agent and forwards the answer.

---

## 3. The Agent Package (`agent/`)

This is where the intelligence lives. It has three sub-layers:

### 3.1 Classifier (`agent/classifier.py`) — the ML layer

This is the "machine learning" part.

**What it does:**
- Looks at what the user typed and guesses what they _want_.
- Returns a label: `"weather"`, `"calculator"`, `"time"`, `"notes"`, or `"other"`.
- Also returns a _confidence_ score (0.0 to 1.0) — how sure it is.

**How it works (ML stuff):**
1. A list of ~120 example phrases is written in code (training data).
   - e.g. `("weather in london", "weather")`, `("5+2", "calculator")`, `("note: buy milk", "notes")`
2. When the app starts, the model is trained on these examples.
   - **TF-IDF Vectorizer** converts each phrase into a list of numbers (based on word frequency).
   - **Logistic Regression** learns which number patterns map to which label.
3. When a user types something → it gets converted to numbers → the model predicts the label.

This is "local ML" — no internet, no API, no GPT. The model trains in milliseconds at startup.

### 3.2 Controller (`agent/controller.py`) — the brain / decision layer

This is what actually decides what to do with the user's message.

**Decision flow (in order):**

```
1. Is it a button click?  (__save_note__:... or __dismiss__)
   → Handle directly (save note or dismiss)

2. Does it contain numbers + operator?  (5+2, 10 - 3)
   → Calculator (rule-based, no ML needed — 100% reliable)

3. ML classifier → what does it think?
   → weather   → Weather tool
   → calculator → Calculator tool
   → time       → Date/Time tool
   → notes      → Notes tool

4. Fallback / smart guessing:
   → Greetings (hi, hello) → friendly response
   → Only letters + low confidence → try as city name (weather)
   → Contains action words (get, buy, call...) → offer to save as note (with Yes/No buttons)
   → Nothing matched → show help
```

The controller is the only file that imports from all tools. The tools don't know about each other.

### 3.3 Tools (`agent/tools/`) — the workers

Each tool does exactly one job and returns a plain string (or dict with buttons).

#### `weather.py`
- Calls **Nominatim** (OpenStreetMap) to turn city name → GPS coordinates.
- Calls **Open-Meteo** to get current temperature, wind speed, and weather condition.
- Both are free public APIs with no API key required.

#### `calculator.py`
- Uses **regex** to find numbers and operators in the user's text.
- Handles: direct expressions (`5+2`), and natural language (`multiply 4 by 5`, `add 5 and 3`).
- **No `eval()` is used** — it only does math on numbers it explicitly found, so it's safe.
- Works fully offline.

#### `datetime_tool.py`
- Uses Python's built-in `datetime` and **pytz** library for timezone-aware time.
- Has a hardcoded map of city names → IANA timezone strings (e.g. `"tokyo"` → `"Asia/Tokyo"`).
- Handles: current local time, time in a specific city, today's date, date math (e.g. "5 days from now").
- Works fully offline.

#### `notes.py`
- Reads/writes a `notes.json` file in the project folder.
- Supports: save a note, view all notes, delete by number, clear all.
- Parses natural language patterns like "remind me to...", "don't forget to...", "jot down...".
- When a message is ambiguous (e.g. "get eggplants"), the controller asks "save as note?" with Yes/No buttons.

---

## 4. The Button Confirmation System

Some questions need a yes/no from the user (e.g. "save as note?").

**How it works end-to-end:**
1. Controller returns `{ "reply": "...", "buttons": [{ "label": "✅ Yes", "value": "__save_note__: get eggplants" }] }`.
2. Flask/app.py forwards this JSON as-is to the UI.
3. UI sees `buttons` in the response → renders them as clickable chips under the agent bubble.
4. User clicks "✅ Yes" → UI sends `{ "message": "__save_note__: get eggplants" }` to the agent.
5. Controller sees the `__save_note__:` prefix → saves the note → returns "Got it! Saved: ..."
6. "❌ No" button sends `__dismiss__` → controller responds with "OK! No problem."

This is fully stateless — no sessions, no cookies needed.

---

## 5. File Structure

```
first_agent/
├── app.py                        ← Flask entry point (routes only)
├── notes.json                    ← Created automatically when you save a note
│
├── agent/
│   ├── __init__.py
│   ├── classifier.py             ← ML layer (TF-IDF + Logistic Regression)
│   ├── controller.py             ← Agent brain (routing + decision logic)
│   │
│   └── tools/
│       ├── __init__.py
│       ├── weather.py            ← Weather tool (Nominatim + Open-Meteo)
│       ├── calculator.py         ← Safe regex math tool
│       ├── datetime_tool.py      ← Time & date tool (pytz)
│       └── notes.py              ← Notes/reminder tool (JSON file)
│
└── templates/
    └── index.html                ← Chat UI (HTML + CSS + vanilla JS)
```

---

## 6. What "ML" means here vs. real AI

| | This project | Real LLM (GPT etc.) |
|---|---|---|
| Model size | ~KB (in-memory) | Billions of parameters |
| Training data | ~120 hand-written examples | Trillions of tokens |
| What it can learn | Classify intent into 5 buckets | Generate full responses |
| Needs internet | No | Usually yes |
| Needs GPU | No | Often yes |
| Speed | Instant | Hundreds of ms |
| Can handle anything | No | Much broader |

The ML here is a **simple classifier** — it doesn't generate text. It just learns "what is the user asking about?" from examples. The actual responses come from the tools (rules + APIs), not the model.

---

## 7. How to add a new feature

1. Create `agent/tools/your_tool.py` with a `handle(text)` function.
2. Add training examples to `classifier.py` under a new label (e.g. `"jokes"`).
3. Add routing in `controller.py`:
   ```python
   if intent == "jokes":
       return your_tool.handle(text)
   ```
4. Restart `python app.py`.

That's it.
