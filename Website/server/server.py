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

# App setup
app = Flask(__name__, static_folder=None)
CORS(app)

WEB_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))

HISTORY_FILE      = os.path.join(SERVER_DIR, 'history.json')
MODELS_FILE       = os.path.join(SERVER_DIR, 'available_models.json')
LEAN_MODELS_FILE  = os.path.join(SERVER_DIR, 'available_lean_models.json')

# External proof generation API (API.py / FastAPI on port 8000)
PROOF_API_BASE = 'http://127.0.0.1:8000'

# Lean verification settings
LEAN_ATTEMPTS   = 3      # how many times the Lean model tries to write the Lean proof
CLAUDE_FIX      = True  # whether Claude attempts to patch Lean syntax errors
MAX_NL_RETRIES  = 3      # how many NL proofs to generate before giving up



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


# STATIC FILE SERVING

@app.route('/')
def serve_index():
    return send_from_directory(WEB_ROOT, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve any file from the New/ directory."""
    return send_from_directory(WEB_ROOT, filename)


# API — Models

@app.route('/api/models', methods=['GET'])
def api_models():
    """
    Returns the list of available NL AI models from available_models.json.
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


@app.route('/api/lean-models', methods=['GET'])
def api_lean_models():
    """
    Returns the list of available Lean verification models from available_lean_models.json.
    The front-end populates its lean model-selector dropdown from this endpoint.
    """
    try:
        with open(LEAN_MODELS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'available_lean_models.json not found'}), 404
    except json.JSONDecodeError:
        return jsonify({'error': 'available_lean_models.json is malformed'}), 500


# API — History

@app.route('/api/history', methods=['GET'])
def api_history_get():
    """
    Returns the persisted proof history so the dashboard can reload
    previous questions and answers on page load.
    """
    history = load_history()
    return jsonify(history)


@app.route('/api/history/<int:index>', methods=['DELETE'])
def api_history_delete(index):
    """
    Deletes the history entry at the given zero-based index.
    Called by the front-end when the user clicks the trash-can button.
    """
    history = load_history()
    if index < 0 or index >= len(history):
        return jsonify({'error': 'Index out of range'}), 404
    history.pop(index)
    save_history(history)
    return jsonify({'status': 'deleted'})


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
    history.insert(0, entry)
    history = history[:50]
    save_history(history)

    return jsonify({'status': 'saved'})


# API — Proof Generation

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """
    Generates a natural-language proof and verifies it with Lean.
    Retries NL generation up to MAX_NL_RETRIES times until Lean confirms the
    proof is valid.  Only returns a proof to the frontend once verified —
    this is what keeps the traffic light green only for correct proofs.

    Receives:
        {
          "question":   "Prove that √2 is irrational.",
          "model":      "claude-sonnet-...",   (NL model)
          "lean_model": "aristotle"            (Lean verification model, optional)
        }

    Returns:
        { "proof": "<verified proof text in Markdown/LaTeX>" }

    External API endpoints used (port 8000):
        POST /nl/           { query, model }                         → { proof }
        POST /lean-verify/  { proof, model, lean_attempts, claude_fix_this } → { valid }
    """
    data       = request.get_json(silent=True) or {}
    question   = data.get('question', '').strip()
    model      = data.get('model', 'claude-sonnet-4-5-20250929').strip()
    lean_model = data.get('lean_model', 'aristotle').strip()

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    nl_payload = {'query': question, 'model': model}

    try:
        for attempt in range(1, MAX_NL_RETRIES + 1):

            # Generate natural-language proof
            nl_resp = http_requests.post(
                f'{PROOF_API_BASE}/nl/',
                json=nl_payload,
                timeout=120,
            )
            nl_resp.raise_for_status()
            proof = nl_resp.json().get('proof', '')

            if not proof:
                return jsonify({'error': 'The proof API returned an empty response.'}), 502

            # Verify with Lean
            verify_payload = {
                'proof':          proof,
                'model':          lean_model,
                'lean_attempts':  LEAN_ATTEMPTS,
                'claude_fix_this': CLAUDE_FIX,
                'local_verify':   True,
            }
            verify_resp = http_requests.post(
                f'{PROOF_API_BASE}/lean-verify/',
                json=verify_payload,
                timeout=1200,   # Lean compilation can be SLOW
            )
            verify_resp.raise_for_status()
            valid = verify_resp.json().get('valid', False)

            if valid:
                return jsonify({'proof': proof})



        return jsonify({
            'error': (
                f'Could not produce a Lean-verified proof after {MAX_NL_RETRIES} attempt(s). '
                'Try a different model or rephrase the theorem.'
            )
        }), 422

    except http_requests.exceptions.ConnectionError:
        return jsonify({
            'error': (
                'Cannot reach the proof generation server at port 8000. '
                'Please start the Provably API: uvicorn API:provablyAPI --port 8000'
            )
        }), 503

    except http_requests.exceptions.Timeout:
        return jsonify({
            'error': 'Proof generation or verification timed out. Try a simpler statement or a faster model.'
        }), 504

    except http_requests.exceptions.HTTPError as e:
        return jsonify({'error': f'Proof API returned an error: {e.response.status_code}'}), 502

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


# API — NL Generation

@app.route('/api/nl', methods=['POST'])
def api_nl():
    """
    Generates a natural-language proof without verifying it.
    The frontend calls this first, displays the result immediately,
    then calls /api/verify to check it with Lean.

    Receives:  { "question": "...", "model": "..." }
    Returns:   { "proof": "..." }
    """
    data     = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    model    = data.get('model', 'claude-sonnet-4-5-20250929').strip()

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    try:
        nl_resp = http_requests.post(
            f'{PROOF_API_BASE}/nl/',
            json={'query': question, 'model': model},
            timeout=120,
        )
        nl_resp.raise_for_status()
        proof = nl_resp.json().get('proof', '')

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
        return jsonify({'error': 'Proof generation timed out.'}), 504
    except http_requests.exceptions.HTTPError as e:
        return jsonify({'error': f'Proof API returned an error: {e.response.status_code}'}), 502
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


# API — Lean Verification

@app.route('/api/verify', methods=['POST'])
def api_verify():
    """
    Verifies a natural-language proof with Lean.
    The frontend calls this after displaying the NL proof.

    Receives:  { "proof": "...", "lean_model": "aristotle" }
    Returns:   { "valid": true|false }
    """
    data       = request.get_json(silent=True) or {}
    proof      = data.get('proof', '').strip()
    lean_model = data.get('lean_model', 'aristotle').strip()

    if not proof:
        return jsonify({'error': 'No proof provided'}), 400

    verify_payload = {
        'proof':           proof,
        'model':           lean_model,
        'lean_attempts':   LEAN_ATTEMPTS,
        'claude_fix_this': CLAUDE_FIX,
        'local_verify':    True,
    }

    try:
        verify_resp = http_requests.post(
            f'{PROOF_API_BASE}/lean-verify/',
            json=verify_payload,
            timeout=1200,
        )
        verify_resp.raise_for_status()
        valid = verify_resp.json().get('valid', False)
        return jsonify({'valid': valid})

    except http_requests.exceptions.ConnectionError:
        return jsonify({
            'error': (
                'Cannot reach the proof generation server at port 8000. '
                'Please start the Provably API: uvicorn API:provablyAPI --port 8000'
            )
        }), 503
    except http_requests.exceptions.Timeout:
        return jsonify({'error': 'Lean verification timed out.'}), 504
    except http_requests.exceptions.HTTPError as e:
        return jsonify({'error': f'Proof API returned an error: {e.response.status_code}'}), 502
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


# ENTRY POINT

if __name__ == '__main__':
    print()
    print('  ╔═══════════════════════════════════════════════════╗')
    print('  ║   Provably — Proof Generator Server               ║')
    print('  ║   http://localhost:5000                           ║')
    print('  ║                                                   ║')
    print('  ║   API endpoints:                                  ║')
    print('  ║     GET  /api/models        ← NL AI models        ║')
    print('  ║     GET  /api/lean-models   ← Lean verify models  ║')
    print('  ║     GET  /api/history       ← proof history       ║')
    print('  ║     POST /api/history       ← save proof entry    ║')
    print('  ║     POST /api/nl            ← generate NL proof   ║')
    print('  ║     POST /api/verify        ← Lean verification   ║')
    print('  ║     POST /api/ask           ← generate+verify     ║')
    print('  ║                                                   ║')
    print('  ║   Requires: proof API on http://127.0.0.1:8000    ║')
    print('  ╚═══════════════════════════════════════════════════╝')
    print()
    app.run(debug=True, port=5000, host='0.0.0.0')
