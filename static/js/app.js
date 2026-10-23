/**
 * HotSeat AI — Core Diligence Controller, Provider Telemetry, IC Memo & SKILL.md
 * ==============================================================================
 */

let lastSkillMd = '';
let isInitialized = false;
let cachedPingResults = {};

const PERSONA_LABELS = {
  sand_hill_vc: 'Managing Partner (Venture & Growth)',
  ruthless_cfo: 'Chief Financial Officer (Unit Economics & Audit)',
  enterprise_buyer: 'Enterprise Procurement Lead (Security & ROI)',
  demo_day_judge: 'Technical Diligence Partner (Architecture & Defensibility)',
};

// ─── Header Controls & Connection Testing ─────────────────────────────────
function showConnectionError(msg) {
  const banner = document.getElementById('connectionErrorBanner');
  const textEl = document.getElementById('connectionErrorText');
  if (textEl) textEl.textContent = msg;
  if (banner) banner.classList.remove('hidden');
}

function hideConnectionError() {
  const banner = document.getElementById('connectionErrorBanner');
  if (banner) banner.classList.add('hidden');
}

// ─── Free-Tier Gemini API Startup Notice ──────────────────────────────────
function showStartupNotice() {
  const overlay = document.getElementById('startupNoticeOverlay');
  if (!overlay) return;
  overlay.classList.remove('hidden');
  overlay.classList.add('flex');
  document.getElementById('noticeTestConnBtn')?.focus();
}

function dismissStartupNotice() {
  const overlay = document.getElementById('startupNoticeOverlay');
  if (overlay) {
    overlay.classList.add('hidden');
    overlay.classList.remove('flex');
  }
  try {
    sessionStorage.setItem('hotseatStartupNoticeDismissed', '1');
  } catch (_err) {
    /* Storage can be unavailable in private/embedded contexts. */
  }
}

function maybeShowStartupNotice() {
  let dismissed = false;
  try {
    dismissed = sessionStorage.getItem('hotseatStartupNoticeDismissed') === '1';
  } catch (_err) {
    dismissed = false;
  }
  if (!dismissed) showStartupNotice();
}

async function testConnectionFromNotice() {
  const btn = document.getElementById('noticeTestConnBtn');
  const statusEl = document.getElementById('startupNoticeStatus');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Testing...';
  }
  if (statusEl) {
    statusEl.classList.remove('hidden');
    statusEl.className =
      'mt-3 px-2.5 py-1.5 rounded bg-[#0b0d13] border border-[#1e2330] font-mono-code text-[11px] text-slate-300';
    statusEl.textContent = 'Contacting provider endpoints...';
  }

  try {
    await testAllConnections(true);
    const provider = document.getElementById('providerSelect')?.value || 'gemini_api';
    const status = cachedPingResults[provider];
    if (!statusEl) return;
    if (status?.ok) {
      statusEl.className =
        'mt-3 px-2.5 py-1.5 rounded bg-[#10b981]/10 border border-[#10b981]/50 font-mono-code text-[11px] text-[#10b981]';
      statusEl.textContent = `Connected to ${status.model_id} in ${status.latency_ms} ms.`;
    } else {
      statusEl.className =
        'mt-3 px-2.5 py-1.5 rounded bg-[#dc2626]/10 border border-[#dc2626]/50 font-mono-code text-[11px] text-rose-300';
      statusEl.textContent = status?.error || 'Connection failed. Check the header telemetry.';
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Test Connection';
    }
  }
}

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  const overlay = document.getElementById('startupNoticeOverlay');
  if (overlay && !overlay.classList.contains('hidden')) dismissStartupNotice();
});

function toggleProviderModelInput() {
  const provider = document.getElementById('providerSelect')?.value;
  const wrapper = document.getElementById('ollamaModelWrapper');
  const modelInput = document.getElementById('ollamaModelInput');
  if (wrapper) {
    if (provider === 'ollama' || provider === 'lmstudio') {
      wrapper.classList.remove('hidden');
      wrapper.classList.add('flex');
      if (modelInput) {
        if (provider === 'ollama' && modelInput.value === 'gemma-4-12b-it') {
          modelInput.value = 'gemma4:12b';
        } else if (provider === 'lmstudio' && modelInput.value === 'gemma4:12b') {
          modelInput.value = 'gemma-4-12b-it';
        }
      }
    } else {
      wrapper.classList.add('hidden');
      wrapper.classList.remove('flex');
    }
  }

  const status = cachedPingResults[provider];
  if (status) {
    if (status.ok) {
      hideConnectionError();
      updateTelemetryBadge(status.model_id, status.latency_ms);
    } else {
      updateTelemetryBadge(status.model_id, null);
      showConnectionError(status.error || `Failed to connect to ${provider}`);
      appendChat('system', status.error || `Failed to connect to ${provider}`);
    }
  } else {
    testAllConnections(false);
  }
}

function formatPingBadge(elId, label, info) {
  const el = document.getElementById(elId);
  if (!el || !info) return;
  if (info.ok) {
    el.textContent = `${label}: ${info.latency_ms} ms`;
    el.className =
      'px-2 py-0.5 rounded bg-[#10b981]/10 border border-[#10b981]/50 text-[#10b981]';
    el.title = `Connected (${info.model_id}) — ${info.latency_ms} ms`;
  } else {
    el.textContent = `${label}: Offline`;
    el.className =
      'px-2 py-0.5 rounded bg-[#dc2626]/10 border border-[#dc2626]/50 text-[#dc2626]';
    el.title = info.error || `${label} unreachable`;
  }
}

async function testAllConnections(verbose = false) {
  const btn = document.getElementById('testConnBtn');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Testing...';
  }

  try {
    const fd = new FormData();
    fd.append('provider', 'all');
    fd.append('api_key', document.getElementById('apiKeyInput')?.value || '');
    fd.append('ollama_model', document.getElementById('ollamaModelInput')?.value || '');

    const resp = await fetch('/api/ping', { method: 'POST', body: fd });
    const data = await resp.json();
    const providers = data.providers || {};
    cachedPingResults = providers;

    formatPingBadge('pingGeminiBadge', 'Gemini API', providers.gemini_api);
    formatPingBadge('pingOllamaBadge', 'Ollama', providers.ollama);
    formatPingBadge('pingLmstudioBadge', 'LM Studio', providers.lmstudio);

    const activeProvider = document.getElementById('providerSelect')?.value || 'gemini_api';
    const activeStatus = providers[activeProvider];
    if (activeStatus) {
      if (activeStatus.ok) {
        hideConnectionError();
        updateTelemetryBadge(activeStatus.model_id, activeStatus.latency_ms);
      } else {
        updateTelemetryBadge(activeStatus.model_id, null);
        showConnectionError(activeStatus.error);
        if (verbose) {
          appendChat('system', activeStatus.error);
        }
      }
    }
  } catch (err) {
    showConnectionError(`Backend connection check failed: ${err.message}`);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Test Connection';
    }
  }
}

function updatePersonaBadge() {
  const personaKey = document.getElementById('personaSelect')?.value || 'sand_hill_vc';
  const label = PERSONA_LABELS[personaKey] || PERSONA_LABELS.sand_hill_vc;
  const badgeEl = document.getElementById('livePersonaAvatarBadge');
  if (badgeEl) badgeEl.textContent = label;
}

const updatePersonaHeader = updatePersonaBadge;

function updateTelemetryBadge(modelId, latencyMs) {
  const el = document.getElementById('telemetryBadge');
  if (!el) return;
  const cleanModel = modelId || 'gemma-4-26b-a4b-it';
  const cleanLatency =
    typeof latencyMs === 'number' && latencyMs >= 0
      ? `${latencyMs.toLocaleString()} ms`
      : '-- ms';
  el.textContent = `Model: ${cleanModel} • Latency: ${cleanLatency}`;
}

// ─── API Calls & Loading State ────────────────────────────────────────────
async function callInterrogate(slideBlob, userMessage) {
  const fd = new FormData();
  if (slideBlob) {
    fd.append('slide_image', slideBlob, `slide_${currentSlide + 1}.jpg`);
  }
  fd.append('slide_number', String(currentSlide + 1));
  fd.append('user_message', userMessage || '');
  fd.append('persona', document.getElementById('personaSelect').value);
  fd.append('provider', document.getElementById('providerSelect').value);
  fd.append('api_key', document.getElementById('apiKeyInput').value);

  const ollamaModelEl = document.getElementById('ollamaModelInput');
  if (ollamaModelEl && ollamaModelEl.value.trim()) {
    fd.append('ollama_model', ollamaModelEl.value.trim());
  }

  const resp = await fetch('/api/interrogate', { method: 'POST', body: fd });
  const data = await resp.json();
  if (!resp.ok || data.error) {
    throw new Error(data.error || data.detail || `HTTP ${resp.status}`);
  }
  return data;
}

function showInterrogationSkeleton(slideNum) {
  removeInterrogationSkeleton();
  const feed = document.getElementById('chatFeed');
  const empty = document.getElementById('emptyTranscriptState');
  if (empty) empty.remove();

  const skel = document.createElement('div');
  skel.id = 'vcLoadingSkeleton';
  skel.className = 'inst-subcard p-3.5 animate-pulse';
  skel.innerHTML = `
    <div class="flex items-center justify-between mb-2">
      <span class="font-mono-code text-[11px] text-slate-400">
        Gemma 4 Multimodal Audit in Progress (Slide ${slideNum})
      </span>
      <span class="font-mono-code text-[10px] text-slate-500">Inspecting visual &amp; verbal claims...</span>
    </div>
    <div class="h-2 bg-[#1e2330] rounded w-4/5 mb-2"></div>
    <div class="h-2 bg-[#1e2330] rounded w-3/5"></div>
  `;
  feed.appendChild(skel);
  feed.scrollTop = feed.scrollHeight;
}

function removeInterrogationSkeleton() {
  const existing = document.getElementById('vcLoadingSkeleton');
  if (existing) existing.remove();
}

// ─── Present Current Slide & Submit Founder Response ──────────────────────
async function pitchCurrentSlide() {
  if (slides.length === 0) return;
  if (window.speechSynthesis) window.speechSynthesis.cancel();

  const slideNum = currentSlide + 1;
  const input = document.getElementById('userInput');
  const optionalMsg = input ? input.value.trim() : '';
  if (input && optionalMsg) input.value = '';

  const btn = document.getElementById('pitchSlideBtn');
  btn.disabled = true;
  btn.textContent = `Auditing Slide ${slideNum} via Gemma 4...`;

  const transcriptNote = optionalMsg
    ? `[Presented Slide ${slideNum}] ${optionalMsg}`
    : `[Presented Slide ${slideNum} for Visual Diligence Audit]`;
  appendChat('founder', transcriptNote);
  showInterrogationSkeleton(slideNum);

  try {
    const blob = await getSlideBlob();
    const data = await callInterrogate(blob, optionalMsg);
    removeInterrogationSkeleton();
    hideConnectionError();
    handleInterrogationResponse(data);
  } catch (err) {
    removeInterrogationSkeleton();
    showConnectionError(err.message);
    appendChat('system', err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Present Current Slide to Partner';
  }
}

async function sendFounderReply() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();

  const input = document.getElementById('userInput');
  const msg = input.value.trim();
  if (!msg) return;

  input.value = '';
  appendChat('founder', msg);

  const slideNum = currentSlide + 1;
  const btn = document.getElementById('sendBtn');
  btn.disabled = true;
  btn.textContent = 'Submitting...';

  showInterrogationSkeleton(slideNum);

  try {
    const blob = await getSlideBlob();
    const data = await callInterrogate(blob, msg);
    removeInterrogationSkeleton();
    hideConnectionError();
    handleInterrogationResponse(data);
  } catch (err) {
    removeInterrogationSkeleton();
    showConnectionError(err.message);
    appendChat('system', err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Submit Response';
  }
}

const sendDefense = sendFounderReply;

// ─── Handle Live Gemma 4 Response ─────────────────────────────────────────
function handleInterrogationResponse(data) {
  const session = data.session || {};
  const evaluation = data.evaluation || data;

  const contradictionDetected = Boolean(
    evaluation.contradiction_detected ?? data.contradiction_detected
  );
  const evasionDetected = Boolean(
    evaluation.evasion_detected ?? data.evasion_detected
  );
  const contradictionDetail =
    evaluation.contradiction_detail || data.contradiction_detail || '';
  const convictionDelta = Number(
    evaluation.conviction_delta ?? data.conviction_delta ?? 0
  );
  const inquiryCategory =
    evaluation.inquiry_category ||
    data.inquiry_category ||
    evaluation.attack_vector_badge ||
    data.attack_vector_badge ||
    'UNIT ECONOMICS DILIGENCE';

  const modelId =
    data.model_id ||
    evaluation.model_id ||
    (data.engine_used ? String(data.engine_used).split('/').pop() : 'gemma-4-26b-a4b-it');
  const latencyMs = Number(data.latency_ms ?? evaluation.latency_ms ?? 0);
  updateTelemetryBadge(modelId, latencyMs);

  if (data.detected_industry || session.detected_industry) {
    document.getElementById('industryPill').textContent =
      data.detected_industry || session.detected_industry;
  }
  if (data.business_model || session.business_model) {
    document.getElementById('bizModelPill').textContent =
      data.business_model || session.business_model;
  }

  const extractedClaims = data.visual_claims_extracted || data.visual_claims;
  if (Array.isArray(extractedClaims)) {
    updateVisualClaims(extractedClaims);
  }

  let discrepancyAlertHtml = '';
  if (contradictionDetected) {
    discrepancyAlertHtml = `
      <div class="mb-3 p-3 rounded-md bg-[#dc2626]/10 border border-[#dc2626] text-xs">
        <div class="font-mono-code text-[10px] font-semibold uppercase tracking-wider text-[#dc2626] mb-1">
          MATERIAL DISCREPANCY IDENTIFIED
        </div>
        <div class="text-slate-200 leading-relaxed">${escapeHtml(contradictionDetail)}</div>
      </div>`;
  } else if (evasionDetected) {
    discrepancyAlertHtml = `
      <div class="mb-3 p-3 rounded-md bg-[#d97706]/10 border border-[#d97706] text-xs">
        <div class="font-mono-code text-[10px] font-semibold uppercase tracking-wider text-[#d97706] mb-1">
          UNANSWERED DILIGENCE INQUIRY
        </div>
        <div class="text-slate-200 leading-relaxed">
          The previous inquiry was not directly addressed with verifiable quantitative data.
        </div>
      </div>`;
  }

  const categoryColor = contradictionDetected
    ? 'text-[#dc2626] border-[#dc2626]/50 bg-[#dc2626]/10'
    : 'text-[#d97706] border-[#d97706]/50 bg-[#d97706]/10';

  const vcHtml = `
    <div class="mb-2 flex items-center justify-between gap-2">
      <span class="inline-block px-2 py-0.5 rounded font-mono-code text-[10px] font-medium uppercase tracking-wider border ${categoryColor}">
        ${escapeHtml(inquiryCategory)}
      </span>
      <span class="font-mono-code text-[10px] text-slate-500">
        ${escapeHtml(modelId)}${latencyMs ? ` • ${latencyMs.toLocaleString()} ms` : ''}
      </span>
    </div>
    ${discrepancyAlertHtml}
    <div class="text-slate-100 text-xs leading-relaxed">
      ${escapeHtml(data.vc_spoken_response || '')}
    </div>
  `;

  const personaKey = data.turn?.persona || document.getElementById('personaSelect').value;
  const roleTitle = PERSONA_LABELS[personaKey] || PERSONA_LABELS.sand_hill_vc;
  appendChat('vc', vcHtml, roleTitle);

  if (data.vc_spoken_response) {
    speakVCResponse(data.vc_spoken_response);
  }

  updateTelemetry(session, convictionDelta, contradictionDetected);
  updateClaimLedger(session.claim_ledger || []);

  document.getElementById('turnCount').textContent =
    `Turn ${session.history?.length || 0}`;

  fetchSkillPreview();
}

// ─── Append Message to Dialogue Transcript ────────────────────────────────
function appendChat(role, content, roleTitle) {
  const feed = document.getElementById('chatFeed');
  const empty = document.getElementById('emptyTranscriptState');
  if (empty) empty.remove();

  const wrapper = document.createElement('div');
  const timeStr = new Date().toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  if (role === 'vc') {
    wrapper.className = 'inst-subcard p-3.5 border-l-2 border-l-[#2563eb]';
    wrapper.innerHTML = `
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-semibold text-slate-200">${escapeHtml(roleTitle || 'Managing Partner')}</span>
        <span class="font-mono-code text-[10px] text-slate-500">${timeStr}</span>
      </div>
      ${content}
    `;
  } else if (role === 'founder') {
    wrapper.className = 'bg-[#161b28] border border-[#1e2330] rounded-md p-3 ml-8';
    wrapper.innerHTML = `
      <div class="flex items-center justify-between mb-1">
        <span class="font-mono-code text-[10px] uppercase tracking-wider text-slate-400">Founder Statement</span>
        <span class="font-mono-code text-[10px] text-slate-500">${timeStr}</span>
      </div>
      <div class="text-xs text-slate-200 leading-relaxed">${escapeHtml(content)}</div>
    `;
  } else {
    wrapper.className = 'p-3 rounded-md bg-[#dc2626]/10 border border-[#dc2626] text-xs text-rose-200';
    wrapper.innerHTML = `
      <div class="font-mono-code text-[10px] font-semibold uppercase tracking-wider text-[#dc2626] mb-1">
        Runtime Error
      </div>
      <div class="font-mono-code text-[11px] leading-relaxed">${escapeHtml(content)}</div>
    `;
  }

  feed.appendChild(wrapper);
  feed.scrollTop = feed.scrollHeight;
}

// ─── Telemetry, Visual Extraction & Claim Ledger Updates ──────────────────
function updateTelemetry(session, delta, contradictionDetected = false) {
  const score = session.conviction_score ?? 50;
  const flags = session.discrepancy_count ?? session.evasion_strikes ?? 0;

  document.getElementById('convictionValue').textContent = score;
  const bar = document.getElementById('convictionBar');
  bar.style.width = `${score}%`;

  if (score >= 68) {
    bar.className = 'conviction-bar h-full bg-[#10b981]';
  } else if (score >= 45) {
    bar.className = 'conviction-bar h-full bg-[#2563eb]';
  } else {
    bar.className = 'conviction-bar h-full bg-[#dc2626]';
  }

  const deltaEl = document.getElementById('convictionDelta');
  const sign = delta > 0 ? '+' : '';
  deltaEl.textContent = `${sign}${delta}`;
  if (delta > 0) {
    deltaEl.className = 'font-mono-code text-[11px] text-[#10b981] font-medium';
  } else if (delta < 0) {
    deltaEl.className = 'font-mono-code text-[11px] text-[#dc2626] font-medium';
  } else {
    deltaEl.className = 'font-mono-code text-[11px] text-slate-400';
  }

  const statusBadge = document.getElementById('skepticismBadge');
  if (contradictionDetected || flags >= 2 || score < 40) {
    statusBadge.textContent = 'Material Discrepancy';
    statusBadge.className =
      'inline-block px-2 py-0.5 rounded font-mono-code text-[11px] font-medium bg-[#dc2626]/15 text-[#dc2626] border border-[#dc2626]/50';
  } else if (flags >= 1 || score < 50) {
    statusBadge.textContent = 'Heightened Scrutiny';
    statusBadge.className =
      'inline-block px-2 py-0.5 rounded font-mono-code text-[11px] font-medium bg-[#d97706]/15 text-[#d97706] border border-[#d97706]/50';
  } else {
    statusBadge.textContent = 'Standard Review';
    statusBadge.className =
      'inline-block px-2 py-0.5 rounded font-mono-code text-[11px] font-medium bg-[#0b0d13] text-slate-300 border border-[#1e2330]';
  }

  document.getElementById('strikesValue').textContent = flags;

  if (session.detected_industry) {
    document.getElementById('industryPill').textContent = session.detected_industry;
  }
  if (session.business_model) {
    document.getElementById('bizModelPill').textContent = session.business_model;
  }
}

function updateVisualClaims(claims) {
  const el = document.getElementById('visualClaimsList');
  if (!claims || !claims.length) {
    el.innerHTML = `
      <div class="inst-subcard p-2.5 text-slate-500 text-xs">
        No quantitative claims extracted from this turn.
      </div>`;
    return;
  }

  el.innerHTML = claims
    .map(
      (c, i) => `
      <div class="inst-subcard p-2 flex items-start gap-2">
        <span class="font-mono-code text-[10px] text-[#10b981] font-semibold mt-0.5">0${i + 1}</span>
        <span class="text-slate-200 text-xs leading-relaxed">${escapeHtml(c)}</span>
      </div>`
    )
    .join('');
}

function updateClaimLedger(ledger) {
  const el = document.getElementById('claimLedgerList');
  const countBadge = document.getElementById('ledgerCountBadge');
  if (countBadge) {
    countBadge.textContent = `${ledger.length} ${ledger.length === 1 ? 'entry' : 'entries'}`;
  }

  if (!ledger.length) {
    el.innerHTML = `
      <div class="inst-subcard p-3 text-slate-500 text-xs">
        No session claims logged yet. Visual slide assertions and founder statements are recorded here chronologically.
      </div>`;
    return;
  }

  el.innerHTML = ledger
    .map((c) => {
      const isVisual = c.source === 'Visual Slide';
      const tagLabel = isVisual ? `[Slide ${c.slide}]` : `[Founder Statement]`;
      const tagClass = isVisual ? 'text-[#10b981]' : 'text-[#2563eb]';
      return `
        <div class="inst-subcard p-2.5 space-y-1">
          <div class="flex items-center justify-between">
            <span class="font-mono-code text-[10px] font-semibold ${tagClass}">${escapeHtml(tagLabel)}</span>
            <span class="font-mono-code text-[10px] text-slate-500">Slide ${escapeHtml(String(c.slide))}</span>
          </div>
          <p class="text-xs text-slate-200 leading-relaxed">${escapeHtml(c.claim)}</p>
        </div>`;
    })
    .join('');
  el.scrollTop = el.scrollHeight;
}

// ─── IC Evaluation Memo (/api/verdict) ────────────────────────────────────
async function generateVerdict() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  switchTab('verdict');

  const btn = document.getElementById('generateVerdictBtn');
  btn.disabled = true;
  btn.textContent = 'Generating IC Evaluation Memo...';

  try {
    const fd = new FormData();
    fd.append('provider', document.getElementById('providerSelect').value);
    fd.append('api_key', document.getElementById('apiKeyInput').value);

    const ollamaModelEl = document.getElementById('ollamaModelInput');
    if (ollamaModelEl && ollamaModelEl.value.trim()) {
      fd.append('ollama_model', ollamaModelEl.value.trim());
    }

    const resp = await fetch('/api/verdict', { method: 'POST', body: fd });
    const data = await resp.json();
    if (!resp.ok || data.error) {
      throw new Error(data.error || data.detail || `HTTP ${resp.status}`);
    }

    if (data.model_id || data.latency_ms) {
      updateTelemetryBadge(data.model_id, Number(data.latency_ms || 0));
    }

    const content = document.getElementById('verdictContent');
    content.classList.remove('hidden');

    const decBox = document.getElementById('verdictDecisionBox');
    const dec = data.decision || 'DECLINE TO ADVANCE';
    document.getElementById('verdictDecision').textContent = dec;
    document.getElementById('verdictHeadline').textContent =
      data.headline_offer_or_reason || '';

    if (dec === 'PROCEED TO TERM SHEET') {
      decBox.className = 'p-3 rounded-md border bg-[#10b981]/10 border-[#10b981]';
      document.getElementById('verdictDecision').className =
        'text-sm font-bold tracking-wide text-[#10b981]';
    } else if (dec === 'ADVANCE TO SECOND-STAGE DILIGENCE') {
      decBox.className = 'p-3 rounded-md border bg-[#d97706]/10 border-[#d97706]';
      document.getElementById('verdictDecision').className =
        'text-sm font-bold tracking-wide text-[#d97706]';
    } else {
      decBox.className = 'p-3 rounded-md border bg-[#dc2626]/10 border-[#dc2626]';
      document.getElementById('verdictDecision').className =
        'text-sm font-bold tracking-wide text-[#dc2626]';
    }

    const scores = data.scores || {};
    setScoreBar('Market', scores.market_timing);
    setScoreBar('Econ', scores.unit_economics);
    setScoreBar('Moat', scores.defensibility_moat);
    setScoreBar('Founder', scores.founder_conviction);

    document.getElementById('verdictStrength').textContent =
      data.biggest_strength || '';
    document.getElementById('verdictFlaw').textContent = data.fatal_flaw || '';

    const fixesList = document.getElementById('verdictFixes');
    const fixes = data.mandatory_deck_fixes || [];
    fixesList.innerHTML = fixes
      .map((f) => `<li class="py-0.5">${escapeHtml(f)}</li>`)
      .join('');
    hideConnectionError();
  } catch (err) {
    showConnectionError(err.message);
    appendChat('system', err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate IC Evaluation Memo';
  }
}

function setScoreBar(suffix, value) {
  const v = Math.max(0, Math.min(100, Number(value ?? 0)));
  document.getElementById('score' + suffix).textContent = `${v}/100`;
  requestAnimationFrame(() => {
    document.getElementById('bar' + suffix).style.width = `${v}%`;
  });
}

// ─── SKILL.md Guardrails Preview & Export ─────────────────────────────────
async function fetchSkillPreview() {
  try {
    const resp = await fetch('/api/skill');
    const text = await resp.text();
    lastSkillMd = text;
    const skillContentEl = document.getElementById('skillContent');
    if (skillContentEl) skillContentEl.textContent = text;
  } catch (err) {
    console.warn('Skill preview fetch failed:', err);
  }
}

async function downloadSkill() {
  try {
    const resp = await fetch('/api/skill', { method: 'POST' });
    if (resp.ok) {
      const payload = await resp.json();
      if (payload.skill_md) {
        lastSkillMd = payload.skill_md;
        const skillContentEl = document.getElementById('skillContent');
        if (skillContentEl) skillContentEl.textContent = lastSkillMd;
      }
    }
  } catch (err) {
    console.warn('POST /api/skill failed:', err);
  }

  if (!lastSkillMd) {
    await fetchSkillPreview();
  }

  const blob = new Blob([lastSkillMd || '# Institutional Pitch-Defense Skill\n'], {
    type: 'text/markdown;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'SKILL.md';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

const downloadSkillMd = downloadSkill;

function switchTab(tab) {
  const tabVerdict = document.getElementById('tabVerdict');
  const tabSkill = document.getElementById('tabSkill');
  const verdictPanel = document.getElementById('verdictPanel');
  const skillPanel = document.getElementById('skillPanel');

  if (tab === 'verdict') {
    tabVerdict.className = 'flex-1 py-2.5 px-3 text-xs font-medium tab-active transition-colors';
    tabSkill.className = 'flex-1 py-2.5 px-3 text-xs font-medium tab-inactive transition-colors';
    verdictPanel.classList.remove('hidden');
    skillPanel.classList.add('hidden');
    skillPanel.classList.remove('flex');
  } else {
    tabSkill.className = 'flex-1 py-2.5 px-3 text-xs font-medium tab-active transition-colors';
    tabVerdict.className = 'flex-1 py-2.5 px-3 text-xs font-medium tab-inactive transition-colors';
    skillPanel.classList.remove('hidden');
    skillPanel.classList.add('flex');
    verdictPanel.classList.add('hidden');
    fetchSkillPreview();
  }
}

// ─── Reset Session ────────────────────────────────────────────────────────
async function resetSession() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  await fetch('/api/reset', { method: 'POST' });

  document.getElementById('chatFeed').innerHTML = `
    <div id="emptyTranscriptState" class="flex justify-center py-12">
      <div class="max-w-md text-center p-5 inst-subcard">
        <div class="text-xs font-semibold text-slate-200 mb-1">
          Ready for Institutional Diligence
        </div>
        <p class="text-xs text-slate-400 leading-relaxed">
          Select a presentation slide on the left and click <span class="text-slate-200 font-medium">"Present Current Slide to Partner"</span>, or enter a pitch statement below to initiate live Gemma 4 multimodal cross-examination.
        </p>
      </div>
    </div>`;

  updateTelemetry(
    {
      conviction_score: 50,
      discrepancy_count: 0,
      evasion_strikes: 0,
      detected_industry: '—',
      business_model: '—',
    },
    0,
    false
  );

  document.getElementById('visualClaimsList').innerHTML = `
    <div class="inst-subcard p-2.5 text-slate-500 text-xs">
      Click "Present Current Slide to Partner" to extract visual claims from the active slide.
    </div>`;
  updateClaimLedger([]);
  document.getElementById('verdictContent').classList.add('hidden');
  document.getElementById('turnCount').textContent = 'Turn 0';
  updatePersonaBadge();
  fetchSkillPreview();
}

// ─── Utilities & Initialization ───────────────────────────────────────────
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text ?? '';
  return div.innerHTML;
}

async function initializeApp() {
  if (isInitialized) return;
  isInitialized = true;

  maybeShowStartupNotice();
  updatePersonaBadge();
  await loadSampleDeck('fintech', false);
  await testAllConnections(false);

  if (window.speechSynthesis && window.speechSynthesis.getVoices) {
    window.speechSynthesis.getVoices();
  }
}

window.onload = initializeApp;
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  initializeApp();
}
