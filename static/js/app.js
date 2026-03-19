const messagesEl = document.getElementById("messages");
const input = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

// Track the last real user query so the "Wrong?" button knows what to blame
let lastUserText = "";

// Quick-start capability chips shown after the welcome message
const CAPABILITIES = [
    { label: "🌤 Weather", example: "London" },
    { label: "🔢 Calculator", example: "12 * 8" },
    { label: "🕐 Time", example: "time in Tokyo" },
    { label: "📝 Notes", example: "remind me to call mom" },
];

// ── DOM helpers ───────────────────────────────────────────────────────────

function scroll() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addBubble(text, role, extraClass = "") {
    const row = document.createElement("div");
    row.className = `bubble-row ${role} ${extraClass}`;

    const avatar = document.createElement("div");
    avatar.className = "bubble-avatar";
    avatar.textContent = role === "agent" ? "🤖" : "🧑";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesEl.appendChild(row);
    scroll();
    return row;
}

function addChips() {
    const row = document.createElement("div");
    row.className = "chips-row";
    CAPABILITIES.forEach(cap => {
        const chip = document.createElement("button");
        chip.className = "chip";
        chip.textContent = cap.label;
        chip.addEventListener("click", () => {
            row.remove();
            addBubble(cap.example, "user");
            send(cap.example);
        });
        row.appendChild(chip);
    });
    messagesEl.appendChild(row);
    scroll();
}

function addButtons(buttons) {
    const row = document.createElement("div");
    row.className = "action-buttons";
    buttons.forEach(btn => {
        const b = document.createElement("button");
        b.className = "action-btn";
        b.textContent = btn.label;
        b.addEventListener("click", () => {
            row.remove();
            addBubble(btn.label, "user");
            send(btn.value);
        });
        row.appendChild(b);
    });
    messagesEl.appendChild(row);
    scroll();
}

// "Wrong answer?" link shown below each agent response
function addFeedbackBtn(originalUserText) {
    // Don't show for internal system messages
    if (!originalUserText || originalUserText.startsWith("__")) return;

    const btn = document.createElement("button");
    btn.className = "feedback-btn";
    btn.textContent = "✗ Wrong answer?";
    btn.addEventListener("click", () => {
        btn.remove();
        addBubble("✗ Wrong answer?", "user");
        send(`__feedback__: ${originalUserText}`);
    });
    messagesEl.appendChild(btn);
    scroll();
}

// ── Welcome screen ────────────────────────────────────────────────────────

addBubble("Hey! 👋 What can I help with today?", "agent");
addChips();

// ── Core send / receive ───────────────────────────────────────────────────

async function send(overrideText) {
    const text = overrideText != null ? overrideText : input.value.trim();
    if (!text) return;

    if (overrideText == null) {
        addBubble(text, "user");
        input.value = "";
    }

    // Only track real user queries for feedback attribution
    if (!text.startsWith("__")) {
        lastUserText = text;
    }

    sendBtn.disabled = true;
    const thinkRow = addBubble("...", "agent", "thinking");

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
        });
        const data = await res.json();
        thinkRow.remove();

        const capturedQuery = lastUserText;   // capture before any async side-effects
        addBubble(data.reply || "No response.", "agent");

        if (data.buttons && data.buttons.length > 0) {
            addButtons(data.buttons);
        } else if (!text.startsWith("__feedback")) {
            // Only show "Wrong?" on normal responses, not during the feedback flow itself
            addFeedbackBtn(capturedQuery);
        }
    } catch {
        thinkRow.remove();
        addBubble("⚠️ Could not reach the agent. Make sure app.py is running.", "agent");
    }

    sendBtn.disabled = false;
    input.focus();
}

// ── Event listeners ───────────────────────────────────────────────────────

sendBtn.addEventListener("click", () => send());
input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        send();
    }
});
