"""
╔══════════════════════════════════════════════════════════════════╗
║  Provably — Proof Generator Server                               ║
║  File: server/server.py                                          ║
║                                                                  ║
║  HOW TO RUN:                                                     ║
║    1. Install deps (once):                                       ║
║         pip install flask flask-cors requests                    ║
║    2. From the 'New/' directory, run:                            ║
║         python server/server.py                                  ║
║    3. Open http://localhost:5000 in your browser.                ║
║                                                                  ║
║  REQUIRES: The Provably proof API server running on port 8000.   ║
║    Start it with:  uvicorn API:provablyAPI --port 8000           ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import json
import datetime
import requests as http_requests
from flask import Flask, send_from_directory, request, jsonify, make_response
from flask_cors import CORS

# ── App Setup ──────────────────────────────────────────────────────
app = Flask(__name__, static_folder=None)
CORS(app)  # Allow cross-origin requests from the browser

# Root of the web files is the parent directory (New/)
WEB_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))

# Data files live alongside server.py in New/server/
HISTORY_FILE = os.path.join(SERVER_DIR, 'history.json')
MODELS_FILE  = os.path.join(SERVER_DIR, 'available_models.json')

# External proof generation API (API.py / FastAPI on port 8000)
PROOF_API_BASE = 'http://127.0.0.1:8000'


# ══════════════════════════════════════════════════════════════════
# HELPERS — JSON persistence
# ══════════════════════════════════════════════════════════════════

def load_history():
    """Return the history list; empty list on any error."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history):
    """Persist the history list to disk."""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════
# STATIC FILE SERVING
# ══════════════════════════════════════════════════════════════════

@app.route('/')
def serve_index():
    return send_from_directory(WEB_ROOT, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve any file from the New/ directory."""
    return send_from_directory(WEB_ROOT, filename)


# ══════════════════════════════════════════════════════════════════
# API — Models
# ══════════════════════════════════════════════════════════════════

@app.route('/api/models', methods=['GET'])
def api_models():
    """
    Returns the list of available AI models from available_models.json.
    The front-end populates its model-selector dropdown from this endpoint.
    """
    try:
        with open(MODELS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'available_models.json not found'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'available_models.json is malformed'}), 500


# ══════════════════════════════════════════════════════════════════
# API — History
# ══════════════════════════════════════════════════════════════════

@app.route('/api/history', methods=['GET'])
def api_history_get():
    """
    Returns the persisted proof history so the dashboard can reload
    previous questions and answers on page load.
    """
    history = load_history()
    return jsonify(history)


@app.route('/api/history', methods=['POST'])
def api_history_post():
    """
    Appends a new { question, proof, model, timestamp } entry to history.json.
    Called by the front-end after every successful proof generation.
    Keeps at most 50 entries (newest first).
    """
    data      = request.get_json(silent=True) or {}
    question  = data.get('question', '').strip()
    proof     = data.get('proof', '').strip()
    model     = data.get('model', '').strip()
    timestamp = data.get('timestamp', datetime.datetime.utcnow().isoformat() + 'Z')

    if not question or not proof:
        return jsonify({'error': 'Missing question or proof'}), 400

    history = load_history()
    entry = {
        'question':  question,
        'proof':     proof,
        'model':     model,
        'timestamp': timestamp,
    }
    history.insert(0, entry)   # newest first
    history = history[:50]      # cap at 50 entries
    save_history(history)

    return jsonify({'status': 'saved'})


# ══════════════════════════════════════════════════════════════════
# API — Proof Generation
# ══════════════════════════════════════════════════════════════════

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """
    Forwards a proof-generation request to the Provably FastAPI server
    running on port 8000 (see 'API to implement/API.py').

    Receives:
        { "question": "Prove that √2 is irrational.", "model": "claude-sonnet-..." }

    Returns:
        { "proof": "<full proof text in Markdown/LaTeX>" }

    The external API endpoint used is:
        POST http://127.0.0.1:8000/nl/
        Body: { "query": <question>, "model": <model> }
        Response: { "proof": <proof string> }
    """
    data     = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    model    = data.get('model', 'claude-sonnet-4-5-20250929').strip()

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    # ── Forward to Provably proof-generation API ────────────────────
    nl_payload = {
        'query': question,
        'model': model,
    }

    try:
        resp = http_requests.post(
            f'{PROOF_API_BASE}/nl/',
            json=nl_payload,
            timeout=120,          # proof generation can take up to 2 minutes (ok for claude/nl?)
        )
        resp.raise_for_status()
        result = resp.json()
        proof  = result.get('proof', '')

        if not proof:
            return jsonify({'error': 'The proof API returned an empty response.'}), 502

        return jsonify({'proof': proof})

    except http_requests.exceptions.ConnectionError:
        return jsonify({
            'error': (
                'Cannot reach the proof generation server at port 8000. '
                'Please start the Provably API: uvicorn API:provablyAPI --port 8000'
            )
        }), 503

    except http_requests.exceptions.Timeout:
        return jsonify({
            'error': 'Proof generation timed out (>120 s). Try a simpler statement or a faster model.'
        }), 504

    except http_requests.exceptions.HTTPError as e:
        return jsonify({'error': f'Proof API returned an error: {e.response.status_code}'}), 502

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print()
    print('  ╔═══════════════════════════════════════════════════╗')
    print('  ║   Provably — Proof Generator Server               ║')
    print('  ║   http://localhost:5000                           ║')
    print('  ║                                                   ║')
    print('  ║   API endpoints:                                  ║')
    print('  ║     GET  /api/models   ← available AI models      ║')
    print('  ║     GET  /api/history  ← proof history            ║')
    print('  ║     POST /api/history  ← save proof entry         ║')
    print('  ║     POST /api/ask      ← generate proof           ║')
    print('  ║                                                   ║')
    print('  ║   Requires: proof API on http://127.0.0.1:8000    ║')
    print('  ╚═══════════════════════════════════════════════════╝')
    print()
    app.run(debug=True, port=5000, host='0.0.0.0')
