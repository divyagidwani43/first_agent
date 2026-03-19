"""
Local AI Agent — Flask entry point.
All agent logic lives in the agent/ package.
"""

from flask import Flask, jsonify, render_template, request

from agent.controller import agent_handle

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "Please type something."})
    reply = agent_handle(user_msg)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    print("Agent running at http://localhost:5000")
    app.run(debug=False, port=5000)
