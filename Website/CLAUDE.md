# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

**Start the Flask backend** (from the `Website/` directory):
```bash
python server/server.py
```
Serves the frontend at `http://localhost:5000` with `debug=True` enabled.

**Start the external proof generation API** (required separately, from the repo root):
```bash
uvicorn API:provablyAPI --port 8000
```
The Flask server proxies proof generation requests to this FastAPI instance at `http://127.0.0.1:8000/nl/`.

**Install backend dependencies:**
```bash
pip install flask flask-cors requests
```

There is no build step — the frontend is vanilla HTML/CSS/JS with CDN-loaded libraries.

## Architecture

This is a fullstack proof generation web app with three layers:

1. **Frontend** (`index.html`, `dashboard.html`, `education.html`, `script.js`, `style.css`) — Vanilla JS SPA. No bundler or framework. Dependencies (Marked.js, KaTeX) are loaded from CDN.

2. **Flask middleware** (`server/server.py`) — Serves static files and provides a REST API. Acts as a proxy between the frontend and the external proof engine. Persists history to `server/history.json` (max 50 entries).

3. **External proof engine** — A separate FastAPI service (not in this directory) that handles actual AI-powered proof generation. The Flask server forwards POST `/api/ask` to `http://127.0.0.1:8000/nl/` with a 120-second timeout.

## Key Files

- `script.js` — All dashboard logic: proof submission (`handleSolve`), history management, and the Markdown+LaTeX rendering pipeline (`renderMarkdownMath`)
- `server/server.py` — Flask API routes: `/api/models`, `/api/history`, `/api/ask`
- `server/available_models.json` — List of selectable AI models shown in the UI dropdown

## Markdown + Math Rendering

Math rendering in `renderMarkdownMath()` uses a placeholder approach to avoid conflicts between Marked.js and KaTeX:
1. Extract `$$...$$` (block) and `$...$` (inline) expressions, replace with null-byte placeholders
2. Run Marked.js on the remaining Markdown
3. Restore placeholders and render with KaTeX
4. Graceful fallback to raw text if libraries are unavailable

## API Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/models` | Returns `available_models.json` |
| GET | `/api/history` | Returns all proof history entries |
| POST | `/api/history` | Appends entry (enforces 50-item cap) |
| POST | `/api/ask` | Proxies to FastAPI proof engine at `:8000/nl/` |

Error responses: 503 (proof API unreachable), 504 (timeout), 502 (upstream error), 400 (bad request).
