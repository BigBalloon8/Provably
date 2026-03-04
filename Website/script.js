const API_BASE    = 'http://localhost:5000';
const MAX_RETRIES = 3;

let proofHistory = [];

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
const leanModelSelect = document.getElementById('leanModelSelect');


// Renders Markdown + LaTeX in a single pass.
// Math spans ($...$ and $$...$$) are extracted and replaced with null-byte
// placeholders before Marked.js runs, then restored via KaTeX afterwards.
// This prevents Marked from mangling LaTeX syntax.
function renderMarkdownMath(text) {
  if (!text) return '';

  const mathBlocks = [];

  let safe = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, expr) => {
    mathBlocks.push({ display: true, expr });
    return `\x00MATH${mathBlocks.length - 1}\x00`;
  });

  safe = safe.replace(/\$([^$\n]+?)\$/g, (_, expr) => {
    mathBlocks.push({ display: false, expr });
    return `\x00MATH${mathBlocks.length - 1}\x00`;
  });

  safe = safe.replace(/\\\[([\s\S]+?)\\\]/g, (_, expr) => {
    mathBlocks.push({ display: true, expr });
    return `\x00MATH${mathBlocks.length - 1}\x00`;
  });

  safe = safe.replace(/\\\((.+?)\\\)/g, (_, expr) => {
    mathBlocks.push({ display: false, expr });
    return `\x00MATH${mathBlocks.length - 1}\x00`;
  });

  let html;
  if (typeof marked !== 'undefined') {
    marked.setOptions({ breaks: true, gfm: true });
    html = marked.parse(safe);
  } else {
    html = '<p>' + safe
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>') + '</p>';
  }

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
        return display ? `$$${expr}$$` : `$${expr}$`;
      }
    }
    return display ? `$$${expr}$$` : `$${expr}$`;
  });

  return html;
}


document.addEventListener('DOMContentLoaded', async () => {
  document.body.classList.add('loaded');

  await loadModels();
  await loadLeanModels();
  await loadHistory();

  solveBtn.addEventListener('click', handleSolve);

  questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSolve();
    }
  });

  questionInput.addEventListener('input', autoGrowTextarea);
  newProblemBtn.addEventListener('click', resetToWelcome);

  exampleChips?.addEventListener('click', (e) => {
    const chip = e.target.closest('.example-chip');
    if (!chip) return;
    questionInput.value = chip.dataset.eq;
    autoGrowTextarea.call(questionInput);
    questionInput.focus();
  });

  sidebarToggle.addEventListener('click', toggleSidebar);
  sidebarBackdrop.addEventListener('click', closeSidebar);
});

function autoGrowTextarea() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 130) + 'px';
}


// Models

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
    modelSelect.innerHTML = '<option value="default">Default Model</option>';
    console.warn('[Provably] Could not load models:', err.message);
  }
}

async function loadLeanModels() {
  try {
    const resp = await fetch(`${API_BASE}/api/lean-models`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data   = await resp.json();
    const models = data.models || [];

    leanModelSelect.innerHTML = '';
    models.forEach((name, i) => {
      const opt    = document.createElement('option');
      opt.value    = name;
      opt.textContent = name;
      if (i === 0) opt.selected = true;
      leanModelSelect.appendChild(opt);
    });
  } catch (err) {
    leanModelSelect.innerHTML = '<option value="aristotle">aristotle</option>';
    console.warn('[Provably] Could not load Lean models:', err.message);
  }
}


// History

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
    item.className = 'sidebar-history-item' + (idx === 0 ? ' active' : '');
    item.setAttribute('role',     'button');
    item.setAttribute('tabindex', '0');

    const itemText = document.createElement('span');
    itemText.className   = 'history-item-text';
    itemText.textContent = truncate(entry.question, 34);
    itemText.title       = entry.question;

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'history-delete-btn';
    deleteBtn.setAttribute('aria-label', 'Delete this proof');
    deleteBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <line x1="10" y1="11" x2="10" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      <line x1="14" y1="11" x2="14" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </svg>`;
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteHistoryEntry(idx);
    });

    item.appendChild(itemText);
    item.appendChild(deleteBtn);

    item.addEventListener('click',   () => reloadHistoryEntry(entry, item));
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') reloadHistoryEntry(entry, item);
    });

    historyList.appendChild(item);
  });
}

async function deleteHistoryEntry(idx) {
  try {
    await fetch(`${API_BASE}/api/history/${idx}`, { method: 'DELETE' });
  } catch (err) {
    console.warn('[Provably] Could not delete history entry:', err.message);
  }
  proofHistory.splice(idx, 1);
  renderHistorySidebar();
}

function reloadHistoryEntry(entry, clickedItem) {
  document.querySelectorAll('.sidebar-history-item')
    .forEach(el => el.classList.remove('active'));
  clickedItem.classList.add('active');

  welcomeState.style.display = 'none';
  clearPreviousProof();
  renderProof(entry.question, entry.proof);

  closeSidebar();
}


// Proof generation — NL first, then Lean verification loop

async function handleSolve() {
  const question = questionInput.value.trim();
  if (!question) {
    shakeInput();
    return;
  }

  const model     = modelSelect.value     || 'default';
  const leanModel = leanModelSelect.value || 'aristotle';

  setLoading(true);
  welcomeState.style.display = 'none';
  clearPreviousProof();

  renderQuestion(question);

  const nlLoadingEl = showLoading('Generating proof…');
  let proofBlockEl = null;

  try {
    const nlResp = await fetch(`${API_BASE}/api/nl`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ question, model }),
    });

    if (!nlResp.ok) {
      const errBody = await nlResp.json().catch(() => ({}));
      throw new Error(errBody.error || `Server error: ${nlResp.status}`);
    }

    const nlResult   = await nlResp.json();
    let currentProof = nlResult.proof;

    if (!currentProof) throw new Error('The server returned an empty proof.');

    nlLoadingEl.remove();
    proofBlockEl = renderNLProof(currentProof);

    let verified = false;

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      const verifyResp = await fetch(`${API_BASE}/api/verify`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ proof: currentProof, lean_model: leanModel }),
      });

      if (!verifyResp.ok) {
        const errBody = await verifyResp.json().catch(() => ({}));
        throw new Error(errBody.error || `Verification error: ${verifyResp.status}`);
      }

      const verifyResult = await verifyResp.json();

      if (verifyResult.valid) {
        verified = true;
        break;
      }

      // Verification failed — fetch a new NL proof and try again
      if (attempt < MAX_RETRIES - 1) {
        const retryResp = await fetch(`${API_BASE}/api/nl`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ question, model }),
        });
        if (retryResp.ok) {
          const retryResult = await retryResp.json();
          if (retryResult.proof) {
            currentProof = retryResult.proof;
            updateProofBlock(proofBlockEl, currentProof);
          }
        }
      }
    }

    if (verified) {
      markProofVerified(proofBlockEl);

      const entry = {
        question,
        proof:     currentProof,
        model,
        timestamp: new Date().toISOString(),
      };
      await saveHistoryEntry(entry);
      proofHistory.unshift(entry);
      renderHistorySidebar();
    } else {
      markProofFailed(proofBlockEl);
      showError(
        `Lean could not formally verify this proof after ${MAX_RETRIES} attempt(s). ` +
        'The proof shown may contain errors.'
      );
    }

    questionInput.value = '';
    questionInput.style.height = '';

  } catch (err) {
    nlLoadingEl?.remove();
    if (proofBlockEl) markProofFailed(proofBlockEl);
    showError(err.message || 'Could not connect to the proof server. Make sure server/server.py is running.');
    console.error('[Provably]', err);
  } finally {
    setLoading(false);
  }
}


// Rendering

function renderQuestion(question) {
  const qBlock = document.createElement('div');
  qBlock.className = 'proof-question';

  const qLabel = document.createElement('span');
  qLabel.className   = 'proof-label';
  qLabel.textContent = 'Question';

  const qContent = document.createElement('div');
  qContent.innerHTML = renderMarkdownMath(question);

  qBlock.appendChild(qLabel);
  qBlock.appendChild(qContent);
  stepsArea.appendChild(qBlock);
  stepsArea.scrollTop = 0;
}

function renderNLProof(proofText) {
  const pBlock = document.createElement('div');
  pBlock.className = 'proof-block proof-unverified';

  const banner = document.createElement('div');
  banner.className = 'verifying-banner';
  banner.innerHTML = `
    <span class="verifying-banner-dots">
      <span></span><span></span><span></span>
    </span>
    Verifying with Lean…
  `;

  const pLabel = document.createElement('span');
  pLabel.className   = 'proof-label';
  pLabel.textContent = 'Proof';

  const pContent = document.createElement('div');
  pContent.className = 'proof-content';
  pContent.innerHTML = renderMarkdownMath(proofText);

  pBlock.appendChild(banner);
  pBlock.appendChild(pLabel);
  pBlock.appendChild(pContent);
  stepsArea.appendChild(pBlock);

  return pBlock;
}

function updateProofBlock(pBlock, proofText) {
  const content = pBlock.querySelector('.proof-content');
  if (content) content.innerHTML = renderMarkdownMath(proofText);
}

function markProofVerified(pBlock) {
  pBlock.classList.remove('proof-unverified');
  const banner = pBlock.querySelector('.verifying-banner');
  if (banner) banner.remove();
}

function markProofFailed(pBlock) {
  pBlock.classList.remove('proof-unverified');
  pBlock.classList.add('proof-failed');
  const banner = pBlock.querySelector('.verifying-banner');
  if (banner) banner.remove();
}

// Used when reloading a history entry (already verified, skip the banner)
function renderProof(question, proofText) {
  renderQuestion(question);
  const pBlock = renderNLProof(proofText);
  markProofVerified(pBlock);
  stepsArea.scrollTop = 0;
}


// Helpers

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
}

function showLoading(msg = 'Generating &amp; verifying proof…') {
  const row = document.createElement('div');
  row.className = 'loading-row';
  row.innerHTML = `
    <div class="loading-dots" aria-label="Generating proof">
      <span></span><span></span><span></span>
    </div>
    <span>${msg}</span>
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
  solveBtn.textContent      = isLoading ? 'Generating & verifying…' : 'Generate Proof';
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


// Mobile sidebar

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
