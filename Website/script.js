/* ═══════════════════════════════════════════════════════════════════
   Provably — Dashboard Script
   Handles: model loading, proof generation, Markdown+Math rendering,
            status lights, history persistence, mobile sidebar.
   ═══════════════════════════════════════════════════════════════════ */

// ── Config ─────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:5000'; // Flask server (server/server.py)

// ── State ───────────────────────────────────────────────────────────
let proofHistory = []; // { question, proof, model, timestamp }[]

// ── DOM References ──────────────────────────────────────────────────
const questionInput   = document.getElementById('questionInput');
const solveBtn        = document.getElementById('solveBtn');
const stepsArea       = document.getElementById('stepsArea');
const welcomeState    = document.getElementById('welcomeState');
const historyList     = document.getElementById('historyList');
const newProblemBtn   = document.getElementById('newProblemBtn');
const sidebarToggle   = document.getElementById('sidebarToggle');
const sidebar         = document.getElementById('sidebar');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');
const exampleChips    = document.getElementById('exampleChips');
const modelSelect     = document.getElementById('modelSelect');
const lightIdle       = document.getElementById('lightIdle');
const lightThinking   = document.getElementById('lightThinking');
const lightFailed     = document.getElementById('lightFailed');


// ══════════════════════════════════════════════════════════════════
// STATUS LIGHTS
// ══════════════════════════════════════════════════════════════════

/**
 * setStatus('idle' | 'thinking' | 'failed')
 * Illuminates exactly one light; the others are dimmed.
 */
function setStatus(status) {
  lightIdle.classList.toggle('active',     status === 'idle');
  lightThinking.classList.toggle('active', status === 'thinking');
  lightFailed.classList.toggle('active',   status === 'failed');
}


// ══════════════════════════════════════════════════════════════════
// MARKDOWN + MATH RENDERING
// ══════════════════════════════════════════════════════════════════

/**
 * renderMarkdownMath(text) → HTML string
 *
 * Strategy:
 *  1. Extract all $...$ and $$...$$ math spans, replace with null-byte
 *     placeholders so Marked.js doesn't mangle them.
 *  2. Run Marked.js to convert Markdown → HTML.
 *  3. Restore each placeholder by rendering the math with KaTeX.
 *
 * Falls back gracefully if libraries are not yet loaded.
 */
function renderMarkdownMath(text) {
  if (!text) return '';

  const mathBlocks = [];

  // ── Step 1: protect display math  $$...$$
  let safe = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, expr) => {
    mathBlocks.push({ display: true, expr });
    return `\x00MATH${mathBlocks.length - 1}\x00`;
  });

  // ── Step 2: protect inline math  $...$
  //   Negative look-behind/ahead for $ to avoid double-matches.
  safe = safe.replace(/\$([^$\n]+?)\$/g, (_, expr) => {
    mathBlocks.push({ display: false, expr });
    return `\x00MATH${mathBlocks.length - 1}\x00`;
  });

  // ── Step 3: also protect \[...\] and \(...\) delimiters
  safe = safe.replace(/\\\[([\s\S]+?)\\\]/g, (_, expr) => {
    mathBlocks.push({ display: true, expr });
    return `\x00MATH${mathBlocks.length - 1}\x00`;
  });

  safe = safe.replace(/\\\((.+?)\\\)/g, (_, expr) => {
    mathBlocks.push({ display: false, expr });
    return `\x00MATH${mathBlocks.length - 1}\x00`;
  });

  // ── Step 4: Markdown → HTML
  let html;
  if (typeof marked !== 'undefined') {
    marked.setOptions({ breaks: true, gfm: true });
    html = marked.parse(safe);
  } else {
    // Minimal fallback
    html = '<p>' + safe
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>') + '</p>';
  }

  // ── Step 5: restore math placeholders via KaTeX
  html = html.replace(/\x00MATH(\d+)\x00/g, (_, idxStr) => {
    const { display, expr } = mathBlocks[+idxStr];
    if (typeof katex !== 'undefined') {
      try {
        return katex.renderToString(expr.trim(), {
          displayMode: display,
          throwOnError: false,
          output: 'html',
        });
      } catch (_) {
        // KaTeX parse error — return raw source
        return display ? `$$${expr}$$` : `$${expr}$`;
      }
    }
    // KaTeX not loaded — return raw source so text is still readable
    return display ? `$$${expr}$$` : `$${expr}$`;
  });

  return html;
}


// ══════════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', async () => {
  // Page fade-in
  document.body.classList.add('loaded');

  // Default state: idle (green light on)
  setStatus('idle');

  // Load available models into dropdown
  await loadModels();

  // Load persisted proof history from server
  await loadHistory();

  // ── Event listeners ────────────────────────────────────────────
  solveBtn.addEventListener('click', handleSolve);

  // Ctrl+Enter or Cmd+Enter inside textarea submits
  questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSolve();
    }
  });

  // Auto-grow textarea
  questionInput.addEventListener('input', autoGrowTextarea);

  newProblemBtn.addEventListener('click', resetToWelcome);

  // Example chips → populate input
  exampleChips?.addEventListener('click', (e) => {
    const chip = e.target.closest('.example-chip');
    if (!chip) return;
    questionInput.value = chip.dataset.eq;
    autoGrowTextarea.call(questionInput);
    questionInput.focus();
  });

  // Mobile sidebar
  sidebarToggle.addEventListener('click', toggleSidebar);
  sidebarBackdrop.addEventListener('click', closeSidebar);
});

function autoGrowTextarea() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 130) + 'px';
}


// ══════════════════════════════════════════════════════════════════
// MODELS
// ══════════════════════════════════════════════════════════════════

async function loadModels() {
  try {
    const resp = await fetch(`${API_BASE}/api/models`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data   = await resp.json();
    const models = data.models || [];

    modelSelect.innerHTML = '';
    models.forEach((name, i) => {
      const opt    = document.createElement('option');
      opt.value    = name;
      opt.textContent = name;
      if (i === 0) opt.selected = true;
      modelSelect.appendChild(opt);
    });
  } catch (err) {
    // Fallback: single placeholder so the UI still works
    modelSelect.innerHTML = '<option value="default">Default Model</option>';
    console.warn('[Provably] Could not load models:', err.message);
  }
}


// ══════════════════════════════════════════════════════════════════
// HISTORY  (server-persisted via history.json)
// ══════════════════════════════════════════════════════════════════

async function loadHistory() {
  try {
    const resp = await fetch(`${API_BASE}/api/history`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    proofHistory = await resp.json();
    renderHistorySidebar();
  } catch (err) {
    console.warn('[Provably] Could not load history:', err.message);
  }
}

async function saveHistoryEntry(entry) {
  try {
    await fetch(`${API_BASE}/api/history`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(entry),
    });
  } catch (err) {
    console.warn('[Provably] Could not save history entry:', err.message);
  }
}

function renderHistorySidebar() {
  historyList.innerHTML = '';

  if (proofHistory.length === 0) {
    historyList.innerHTML =
      '<div class="sidebar-history-item sidebar-history-empty">No proofs yet</div>';
    return;
  }

  proofHistory.slice(0, 20).forEach((entry, idx) => {
    const item = document.createElement('div');
    item.className   = 'sidebar-history-item' + (idx === 0 ? ' active' : '');
    item.textContent = truncate(entry.question, 34);
    item.title       = entry.question;
    item.setAttribute('role',     'button');
    item.setAttribute('tabindex', '0');

    item.addEventListener('click',   () => reloadHistoryEntry(entry, item));
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') reloadHistoryEntry(entry, item);
    });

    historyList.appendChild(item);
  });
}

function reloadHistoryEntry(entry, clickedItem) {
  // Mark active
  document.querySelectorAll('.sidebar-history-item')
    .forEach(el => el.classList.remove('active'));
  clickedItem.classList.add('active');

  // Redisplay saved proof
  welcomeState.style.display = 'none';
  clearPreviousProof();
  renderProof(entry.question, entry.proof);

  // Close sidebar on mobile
  closeSidebar();
}


// ══════════════════════════════════════════════════════════════════
// SOLVE / GENERATE PROOF
// ══════════════════════════════════════════════════════════════════

async function handleSolve() {
  const question = questionInput.value.trim();
  if (!question) {
    shakeInput();
    return;
  }

  const model = modelSelect.value || 'default';

  // UI → loading state
  setLoading(true);
  setStatus('thinking');

  // Clear previous result
  welcomeState.style.display = 'none';
  clearPreviousProof();
  const loadingEl = showLoading();

  try {
    const response = await fetch(`${API_BASE}/api/ask`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ question, model }),
    });

    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.error || `Server error: ${response.status}`);
    }

    const result = await response.json();
    const proof  = result.proof;

    if (!proof) throw new Error('The server returned an empty proof.');

    // Render the proof
    loadingEl.remove();
    renderProof(question, proof);
    setStatus('idle');

    // Persist to history
    const entry = {
      question,
      proof,
      model,
      timestamp: new Date().toISOString(),
    };
    await saveHistoryEntry(entry);
    proofHistory.unshift(entry);
    renderHistorySidebar();

    // Clear input
    questionInput.value = '';
    questionInput.style.height = '';

  } catch (err) {
    loadingEl.remove();
    showError(err.message || 'Could not connect to the proof server. Make sure server/server.py is running.');
    setStatus('failed');
    console.error('[Provably]', err);
  } finally {
    setLoading(false);
  }
}


// ══════════════════════════════════════════════════════════════════
// PROOF RENDERING  (single continuous block — no step-by-step)
// ══════════════════════════════════════════════════════════════════

/**
 * renderProof(question, proofText)
 *
 * Renders the theorem statement and the full proof as two
 * continuous blocks with Markdown + KaTeX rendering.
 */
function renderProof(question, proofText) {
  // ── Theorem / question block ──────────────────────────────────
  const qBlock = document.createElement('div');
  qBlock.className = 'proof-question';

  const qLabel = document.createElement('span');
  qLabel.className   = 'proof-label';
  qLabel.textContent = 'Theorem';

  const qContent = document.createElement('div');
  qContent.innerHTML = renderMarkdownMath(question);

  qBlock.appendChild(qLabel);
  qBlock.appendChild(qContent);
  stepsArea.appendChild(qBlock);

  // ── Proof block ───────────────────────────────────────────────
  const pBlock = document.createElement('div');
  pBlock.className = 'proof-block';

  const pLabel = document.createElement('span');
  pLabel.className   = 'proof-label';
  pLabel.textContent = 'Proof';

  const pContent = document.createElement('div');
  pContent.innerHTML = renderMarkdownMath(proofText);

  pBlock.appendChild(pLabel);
  pBlock.appendChild(pContent);
  stepsArea.appendChild(pBlock);

  // Scroll to top of proof
  stepsArea.scrollTop = 0;
}


// ══════════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════════

function clearPreviousProof() {
  Array.from(stepsArea.children).forEach(child => {
    if (child.id !== 'welcomeState') child.remove();
  });
}

function resetToWelcome() {
  clearPreviousProof();
  welcomeState.style.display = '';
  questionInput.value        = '';
  questionInput.style.height = '';
  questionInput.focus();
  document.querySelectorAll('.sidebar-history-item')
    .forEach(el => el.classList.remove('active'));
  setStatus('idle');
}

function showLoading() {
  const row = document.createElement('div');
  row.className = 'loading-row';
  row.innerHTML = `
    <div class="loading-dots" aria-label="Generating proof">
      <span></span><span></span><span></span>
    </div>
    <span>Generating proof…</span>
  `;
  stepsArea.appendChild(row);
  row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  return row;
}

function showError(message) {
  const row = document.createElement('div');
  row.className = 'error-row';
  row.setAttribute('role', 'alert');
  row.textContent = message;
  stepsArea.appendChild(row);
}

function setLoading(isLoading) {
  solveBtn.disabled         = isLoading;
  questionInput.disabled    = isLoading;
  solveBtn.textContent      = isLoading ? 'Generating…' : 'Generate Proof';
}

function shakeInput() {
  questionInput.style.transition  = 'border-color 80ms';
  questionInput.style.borderColor = 'var(--error)';
  setTimeout(() => {
    questionInput.style.borderColor = '';
    questionInput.style.transition  = '';
  }, 600);
}

function truncate(str, maxLen) {
  return str.length > maxLen ? str.slice(0, maxLen - 1) + '…' : str;
}


// ══════════════════════════════════════════════════════════════════
// MOBILE SIDEBAR
// ══════════════════════════════════════════════════════════════════

function toggleSidebar() {
  const isOpen = sidebar.classList.toggle('open');
  sidebarToggle.setAttribute('aria-expanded', String(isOpen));
  sidebarBackdrop.style.display = isOpen ? 'block' : 'none';
  document.body.style.overflow  = isOpen ? 'hidden' : '';
}

function closeSidebar() {
  sidebar.classList.remove('open');
  sidebarToggle.setAttribute('aria-expanded', 'false');
  sidebarBackdrop.style.display = 'none';
  document.body.style.overflow  = '';
}
