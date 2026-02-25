"""
╔══════════════════════════════════════════════════════════════════╗
║  AcademIQ — Python Web Server                                    ║
║  File: server/server.py                                          ║
║                                                                  ║
║  HOW TO RUN:                                                     ║
║    1. Install Flask (once):  pip install flask flask-cors        ║
║    2. From the 'New/' directory, run:                            ║
║         python server/server.py                                  ║
║    3. Open http://localhost:5000 in your browser.               ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import json
from flask import Flask, send_from_directory, request, jsonify, make_response
from flask_cors import CORS

# ── App Setup ──────────────────────────────────────────────────────
app = Flask(__name__, static_folder=None)
CORS(app)  # Allow cross-origin requests from the browser

# Root of the web files is the parent directory (New/)
WEB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


# ══════════════════════════════════════════════════════════════════
# STATIC FILE SERVING
# Serves index.html, education.html, dashboard.html, style.css, script.js
# ══════════════════════════════════════════════════════════════════

@app.route('/')
def serve_index():
    return send_from_directory(WEB_ROOT, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve any file from the New/ directory."""
    return send_from_directory(WEB_ROOT, filename)


# ══════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """
    ┌─────────────────────────────────────────────────────────────┐
    │  ★  CUSTOM ENDPOINT — ADD YOUR LOGIC HERE  ★               │
    │                                                             │
    │  Receives a JSON body:                                      │
    │    { "question": "2x + 4 = 10", "level": "highschool" }    │
    │                                                             │
    │  Must return a JSON array of step objects:                  │
    │    [ { "content": "Step explanation..." }, ... ]            │
    │                                                             │
    │  Replace the placeholder_steps below with a call to your   │
    │  AI model, math solver, or any other Python logic.         │
    └─────────────────────────────────────────────────────────────┘
    """
    data     = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    level    = data.get('level', 'highschool')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # ── ★ YOUR CUSTOM LOGIC STARTS HERE ────────────────────────────
    #
    # Example integration (replace this block):
    #
    #   import anthropic
    #   client = anthropic.Anthropic(api_key="YOUR_KEY")
    #   response = client.messages.create(
    #       model="claude-opus-4-5",
    #       max_tokens=1024,
    #       messages=[{"role": "user", "content": f"Solve step by step: {question}"}]
    #   )
    #   steps = parse_steps(response.content[0].text)
    #   return jsonify(steps)
    #
    # ── ★ YOUR CUSTOM LOGIC ENDS HERE ──────────────────────────────

    # Placeholder response — remove once you plug in your solver.
    placeholder_steps = [
        {
            "content": (
                f"<strong>Question received:</strong> <em>{question}</em> "
                f"(Level: {level.capitalize()}). "
                "Connect your AI model or math solver in "
                "<code>server/server.py → /api/ask</code> to see real steps here."
            )
        },
        {
            "content": (
                "This is a placeholder for Step 2. "
                "Your backend will return each logical step as a separate item in the JSON array."
            )
        },
        {
            "content": (
                "Step 3 placeholder. Once your solver is integrated, "
                "the final answer will appear here."
            )
        },
    ]

    return jsonify(placeholder_steps)


@app.route('/api/clarify', methods=['POST'])
def api_clarify():
    """
    ┌─────────────────────────────────────────────────────────────┐
    │  ★  CUSTOM ENDPOINT — ADD YOUR LOGIC HERE  ★               │
    │                                                             │
    │  Receives a JSON body:                                      │
    │    { "step": "Subtract 4 from both sides…",                 │
    │      "level": "highschool" }                                │
    │                                                             │
    │  Must return a plain-text (or HTML) explanation string.     │
    │                                                             │
    │  Replace the placeholder below with a call to your AI      │
    │  model or knowledge base for deeper explanations.          │
    └─────────────────────────────────────────────────────────────┘
    """
    data  = request.get_json(silent=True) or {}
    step  = data.get('step', '').strip()
    level = data.get('level', 'highschool')

    if not step:
        return make_response('No step content provided.', 400)

    # ── ★ YOUR CUSTOM LOGIC STARTS HERE ────────────────────────────
    #
    # Example:
    #   explanation = my_ai_client.clarify(step, level)
    #   return make_response(explanation, 200)
    #
    # ── ★ YOUR CUSTOM LOGIC ENDS HERE ──────────────────────────────

    # Placeholder response
    placeholder = (
        "This is a placeholder clarification. "
        "Plug in your AI model inside <code>server/server.py → /api/clarify</code> "
        "to generate real explanations for this step."
    )

    return make_response(placeholder, 200)


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print()
    print('  ╔═══════════════════════════════════════════╗')
    print('  ║   AcademIQ Development Server             ║')
    print('  ║   http://localhost:5000                   ║')
    print('  ║                                           ║')
    print('  ║   API endpoints:                          ║')
    print('  ║     POST /api/ask      ← add solver here  ║')
    print('  ║     POST /api/clarify  ← add AI here      ║')
    print('  ╚═══════════════════════════════════════════╝')
    print()
    app.run(debug=True, port=5000, host='0.0.0.0')
