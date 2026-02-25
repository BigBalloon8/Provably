/* ═══════════════════════════════════════════════════════════════════
   AcademIQ — Dashboard Script
   Handles: level detection, question submission, step rendering,
            clarifications, history sidebar, mobile sidebar toggle.
   ═══════════════════════════════════════════════════════════════════ */

// ── Config ─────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:5000'; // Python server (server/server.py)

// ── State ───────────────────────────────────────────────────────────
let currentLevel   = 'highschool'; // default fallback
let problemHistory = [];           // { question, steps }[]

// ── DOM References ──────────────────────────────────────────────────
const questionInput   = document.getElementById('questionInput');
const solveBtn        = document.getElementById('solveBtn');
const stepsArea       = document.getElementById('stepsArea');
const welcomeState    = document.getElementById('welcomeState');
const historyList     = document.getElementById('historyList');
const navLevelPill    = document.getElementById('navLevelPill');
const sidebarLevelBadge = document.getElementById('sidebarLevelBadge');
const sidebarLevelIcon  = document.getElementById('sidebarLevelIcon');
const sidebarLevelText  = document.getElementById('sidebarLevelText');
const newProblemBtn   = document.getElementById('newProblemBtn');
const sidebarToggle   = document.getElementById('sidebarToggle');
const sidebar         = document.getElementById('sidebar');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');
const exampleChips    = document.getElementById('exampleChips');

// ── Init ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // 1. Parse education level from URL
  const params = new URLSearchParams(window.location.search);
  const levelParam = params.get('level') || 'highschool';
  setLevel(levelParam);

  // 2. Page fade-in
  document.body.classList.add('loaded');

  // 3. Attach events
  solveBtn.addEventListener('click', handleSolve);
  questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSolve();
    }
  });

  newProblemBtn.addEventListener('click', resetToWelcome);

  // Example chips → populate input
  exampleChips?.addEventListener('click', (e) => {
    const chip = e.target.closest('.example-chip');
    if (chip) {
      questionInput.value = chip.dataset.eq;
      questionInput.focus();
    }
  });

  // Sidebar toggle (mobile)
  sidebarToggle.addEventListener('click', toggleSidebar);
  sidebarBackdrop.addEventListener('click', closeSidebar);
});

// ── Level Setup ─────────────────────────────────────────────────────
function setLevel(level) {
  currentLevel = level;

  const isUniversity = level === 'university';
  const label = isUniversity ? 'University' : 'High School';
  const icon  = isUniversity ? '∫' : '📐';

  // Nav pill
  navLevelPill.textContent = label;

  // Sidebar badge
  sidebarLevelIcon.textContent = icon;
  sidebarLevelText.textContent = label;

  // Update page title
  document.title = `AcademIQ — ${label} Tutor`;

  // Filter example chips by level (university gets calculus chip by default)
  if (isUniversity && exampleChips) {
    document.querySelectorAll('.example-chip').forEach(chip => {
      if (chip.dataset.eq === '2x + 4 = 10') chip.style.display = 'none';
    });
  }
}

// ── Solve Handler ────────────────────────────────────────────────────
async function handleSolve() {
  const question = questionInput.value.trim();
  if (!question) {
    questionInput.focus();
    shakeInput();
    return;
  }

  // Disable input while loading
  setLoading(true);

  // Hide welcome state; clear any previous result
  welcomeState.style.display  = 'none';
  clearPreviousSteps();

  // Show loading indicator
  const loadingEl = showLoading();

  try {
    const response = await fetch(`${API_BASE}/api/ask`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ question, level: currentLevel }),
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);

    const steps = await response.json();

    loadingEl.remove();
    renderSteps(steps);

    // Save to history
    addToHistory(question, steps);

    // Clear input for next question
    questionInput.value = '';

  } catch (err) {
    loadingEl.remove();
    showError('Could not connect to the tutor server. Make sure server/server.py is running.');
    console.error('[AcademIQ]', err);
  } finally {
    setLoading(false);
  }
}

// ── Render Steps ─────────────────────────────────────────────────────
function renderSteps(steps) {
  steps.forEach((step, index) => {
    // For steps after the first, insert a "Reveal" button first
    if (index > 0) {
      const revealRow = document.createElement('div');
      revealRow.className = 'reveal-row';

      const revealBtn = document.createElement('button');
      revealBtn.className = 'reveal-btn';
      revealBtn.textContent = `Reveal Step ${index + 1}`;
      revealBtn.setAttribute('aria-label', `Reveal step ${index + 1}`);

      revealBtn.addEventListener('click', () => {
        stepCard.classList.remove('step-blurred');
        stepCard.removeAttribute('aria-hidden');
        revealRow.remove();
      });

      revealRow.appendChild(revealBtn);
      stepsArea.appendChild(revealRow);
    }

    // Build step card
    const stepCard = buildStepCard(step, index);

    // Blur all steps except the first
    if (index > 0) {
      stepCard.classList.add('step-blurred');
      stepCard.setAttribute('aria-hidden', 'true');
    }

    stepsArea.appendChild(stepCard);
  });

  // Scroll to first step
  stepsArea.scrollTop = 0;
}

// ── Build a Single Step Card ─────────────────────────────────────────
function buildStepCard(step, index) {
  const card = document.createElement('div');
  card.className = 'step-card';
  card.id = `step-${index}`;

  // Label row
  const header = document.createElement('div');
  header.className = 'step-card-header';

  const label = document.createElement('span');
  label.className = 'step-card-label';
  label.textContent = `Step ${index + 1}`;

  header.appendChild(label);

  // Content
  const content = document.createElement('p');
  content.className = 'step-card-content';
  // Allow basic formatting; content comes from our own server so this is safe
  content.innerHTML = step.content || step;

  // Clarification button
  const clarifyBtn = document.createElement('button');
  clarifyBtn.className = 'clarify-btn';
  clarifyBtn.setAttribute('aria-expanded', 'false');
  clarifyBtn.innerHTML = `
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
      <circle cx="6" cy="6" r="5.25" stroke="currentColor" stroke-width="1.5"/>
      <path d="M6 8V6M6 4h.006" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    I don't understand this step
  `;

  // Clarification box (hidden by default)
  const clarifyBox = document.createElement('div');
  const clarifyId  = `clarify-${index}`;
  clarifyBox.className = 'clarification-box';
  clarifyBox.id = clarifyId;
  clarifyBox.setAttribute('aria-live', 'polite');

  clarifyBtn.addEventListener('click', () =>
    handleClarification(step.content || step, clarifyBtn, clarifyBox)
  );

  card.appendChild(header);
  card.appendChild(content);
  card.appendChild(clarifyBtn);
  card.appendChild(clarifyBox);

  return card;
}

// ── Clarification Request ────────────────────────────────────────────
async function handleClarification(stepContent, btn, box) {
  // Toggle off if already showing
  if (box.classList.contains('visible')) {
    box.classList.remove('visible');
    btn.setAttribute('aria-expanded', 'false');
    return;
  }

  box.classList.add('visible');
  btn.setAttribute('aria-expanded', 'true');
  box.innerHTML = `<strong>Tutor</strong>Thinking…`;

  try {
    const response = await fetch(`${API_BASE}/api/clarify`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ step: stepContent, level: currentLevel }),
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);

    const explanation = await response.text();
    box.innerHTML = `<strong>Tutor says</strong>${explanation}`;

  } catch (err) {
    box.innerHTML = `<strong>Tutor says</strong>Could not load clarification. Check that the server is running.`;
    console.error('[AcademIQ clarify]', err);
  }
}

// ── History Sidebar ──────────────────────────────────────────────────
function addToHistory(question, steps) {
  problemHistory.unshift({ question, steps });

  // Re-render history list
  historyList.innerHTML = '';
  problemHistory.slice(0, 12).forEach((entry, idx) => {
    const item = document.createElement('div');
    item.className = 'sidebar-history-item' + (idx === 0 ? ' active' : '');
    item.textContent = truncate(entry.question, 30);
    item.title = entry.question;
    item.setAttribute('role', 'button');
    item.setAttribute('tabindex', '0');

    item.addEventListener('click', () => reloadHistoryEntry(entry, item));
    item.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') reloadHistoryEntry(entry, item);
    });

    historyList.appendChild(item);
  });
}

function reloadHistoryEntry(entry, clickedItem) {
  // Mark active
  document.querySelectorAll('.sidebar-history-item').forEach(el => el.classList.remove('active'));
  clickedItem.classList.add('active');

  // Redisplay the saved steps
  welcomeState.style.display = 'none';
  clearPreviousSteps();
  renderSteps(entry.steps);
  questionInput.value = entry.question;

  // Close sidebar on mobile
  closeSidebar();
}

// ── Helpers ──────────────────────────────────────────────────────────
function clearPreviousSteps() {
  // Remove all children except the welcome state
  Array.from(stepsArea.children).forEach(child => {
    if (child.id !== 'welcomeState') child.remove();
  });
}

function resetToWelcome() {
  clearPreviousSteps();
  welcomeState.style.display = '';
  questionInput.value = '';
  questionInput.focus();

  document.querySelectorAll('.sidebar-history-item').forEach(el => el.classList.remove('active'));
}

function showLoading() {
  const row = document.createElement('div');
  row.className = 'loading-row';
  row.innerHTML = `
    <div class="loading-dots" aria-label="Loading">
      <span></span><span></span><span></span>
    </div>
    <span>Working through the problem…</span>
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

function setLoading(loading) {
  solveBtn.disabled     = loading;
  questionInput.disabled = loading;
  solveBtn.textContent  = loading ? 'Solving…' : 'Solve';
}

function shakeInput() {
  questionInput.style.transition = 'border-color 80ms';
  questionInput.style.borderColor = 'var(--error)';
  setTimeout(() => {
    questionInput.style.borderColor = '';
    questionInput.style.transition = '';
  }, 600);
}

function truncate(str, maxLen) {
  return str.length > maxLen ? str.slice(0, maxLen - 1) + '…' : str;
}

// ── Mobile Sidebar ───────────────────────────────────────────────────
function toggleSidebar() {
  const isOpen = sidebar.classList.toggle('open');
  sidebarToggle.setAttribute('aria-expanded', isOpen);
  sidebarBackdrop.style.display = isOpen ? 'block' : 'none';
  document.body.style.overflow  = isOpen ? 'hidden' : '';
}

function closeSidebar() {
  sidebar.classList.remove('open');
  sidebarToggle.setAttribute('aria-expanded', 'false');
  sidebarBackdrop.style.display = 'none';
  document.body.style.overflow  = '';
}
