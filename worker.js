/**
 * HotSeat AI — Cloudflare Workers Edge Runtime (https://hotseat-ai.ojasdeshpande.in/)
 * ===================================================================================
 *
 * Serves static assets from `./static` via `env.ASSETS` and provides full edge
 * API parity with `app.py` & `engine.py` using live Gemma 4 multimodal inference
 * (`gemma-4-26b-a4b-it` → `gemma-4-31b-it`), structured observability logs, and
 * distributed tracing.
 */

const CLOUD_CASCADE = ['gemma-4-26b-a4b-it', 'gemma-4-31b-it'];
const DEFAULT_TEMPERATURE = 0.3;
const MAX_LEDGER_IN_PROMPT = 25;

const INITIAL_STATE = {
  conviction_score: 50,
  discrepancy_count: 0,
  evasion_strikes: 0,
  detected_industry: '—',
  business_model: '—',
  last_vc_question: '',
  claim_ledger: [],
  history: [],
  skill_rules: [],
  contradictions_logged: [],
};

let SESSION_STATE = structuredClone(INITIAL_STATE);

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...CORS_HEADERS,
    },
  });
}

function clamp(val, lo, hi) {
  return Math.max(lo, Math.min(hi, val));
}

function cleanEnvValue(val) {
  return String(val || '')
    .trim()
    .replace(/^["']+|["']+$/g, '')
    .trim();
}

/**
 * Resolve every .env / Cloudflare Secret variable with `||` fallback defaults
 */
function resolveEnvConfig(env = {}, overrides = {}) {
  const geminiApiKey =
    cleanEnvValue(overrides.apiKey) ||
    cleanEnvValue(env.GEMINI_API_KEY) ||
    '';
  const gemmaModelId =
    cleanEnvValue(env.GEMMA_MODEL_ID) || 'gemma-4-26b-a4b-it';
  const gemmaFallbackModels =
    cleanEnvValue(env.GEMMA_FALLBACK_MODELS) ||
    cleanEnvValue(env.GEMMA_FALLBACK_MODEL) ||
    'gemma-4-26b-a4b-it,gemma-4-31b-it,gemma-3-27b-it';

  const ollamaHost =
    cleanEnvValue(env.OLLAMA_HOST) || 'http://127.0.0.1:11434';
  const ollamaUrl =
    cleanEnvValue(env.OLLAMA_URL) ||
    `${ollamaHost.replace(/\/$/, '')}/api/chat`;
  const ollamaModel =
    cleanEnvValue(overrides.ollamaModel) ||
    cleanEnvValue(env.OLLAMA_MODEL) ||
    'gemma4:12b';
  const ollamaKeepAlive =
    cleanEnvValue(env.OLLAMA_KEEP_ALIVE) || '30m';

  const lmstudioUrl =
    cleanEnvValue(env.LMSTUDIO_URL) ||
    'http://127.0.0.1:1234/v1/chat/completions';
  const lmstudioModel =
    cleanEnvValue(overrides.ollamaModel) ||
    cleanEnvValue(env.LMSTUDIO_MODEL) ||
    'gemma-4-12b-it';

  const port = parseInt(cleanEnvValue(env.PORT) || '8000', 10) || 8000;
  const host = cleanEnvValue(env.HOST) || '0.0.0.0';

  return {
    geminiApiKey,
    gemmaModelId,
    gemmaFallbackModels,
    ollamaHost,
    ollamaUrl,
    ollamaModel,
    ollamaKeepAlive,
    lmstudioUrl,
    lmstudioModel,
    port,
    host,
  };
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  const chunkSize = 0x8000;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

/**
 * 3-Layer JSON Extractor (Zero Canned Fallbacks)
 */
function extractJsonSafely(rawText) {
  if (!rawText || !rawText.trim()) {
    throw new Error('Gemma 4 returned an empty response.');
  }

  // Layer 1: strip <thought>...</thought> blocks
  let cleaned = rawText.replace(/<thought>[\s\S]*?<\/thought>/g, '');

  // Layer 2: strip markdown code fences
  cleaned = cleaned
    .replace(/```json/gi, '')
    .replace(/```/g, '')
    .trim();

  // Layer 3: locate outermost braces
  const firstBrace = cleaned.indexOf('{');
  const lastBrace = cleaned.lastIndexOf('}');
  if (firstBrace === -1 || lastBrace === -1 || lastBrace <= firstBrace) {
    throw new Error(
      `Gemma 4 response did not contain a JSON object. Raw output: ${cleaned.slice(0, 300)}`
    );
  }

  const candidate = cleaned.slice(firstBrace, lastBrace + 1);
  try {
    return JSON.parse(candidate);
  } catch (_err) {
    const repaired = candidate.replace(/,\s*([}\]])/g, '$1');
    return JSON.parse(repaired);
  }
}

/**
 * Build the Senior Managing Partner Multimodal Interrogation Prompt
 */
function buildInterrogationPrompt(userMessage, lastVcQuestion, claimLedger) {
  const recentClaims = claimLedger.slice(-MAX_LEDGER_IN_PROMPT);
  const claimLedgerJson = recentClaims.length
    ? JSON.stringify(recentClaims, null, 2)
    : '[]';

  return `You are a Senior Managing Partner at an institutional Venture Capital firm conducting formal due diligence on a startup pitch.
Maintain a composed, analytical, professional, and rigorous tone at all times. Never use slang, internet memes, "roast" language, or casual insults.

INPUTS PROVIDED TO YOU:
1. Attached Slide Image: The presentation slide currently displayed on screen by the founder.
2. Founder's Verbal/Written Statement: "${userMessage}"
3. Prior Session Claim Ledger (from earlier slides/turns in this session only): ${claimLedgerJson}
4. Previous Inquiry Asked by Partner: "${lastVcQuestion}"

YOUR ANALYTICAL MANDATE:
1. INSPECT THE SLIDE IMAGE DIRECTLY: Read the exact title, sector, metrics, charts, and claims shown visually on the attached slide image.
2. CROSS-CHECK VISUAL SLIDE VS. FOUNDER STATEMENT:
   - Does the founder's statement ("${userMessage}") contradict the visual slide currently on screen? (For example, if the slide on screen visually depicts a Healthcare/MedTech product, and the founder states "We are a finance company", immediately flag \`contradiction_detected: true\` and formally ask the founder to explain why their verbal statement contradicts the sector and product shown on their slide).
   - Does the current slide or statement contradict an earlier entry in the Prior Session Claim Ledger?
   - If \`last_vc_question\` was asked, did the founder provide a substantive, direct answer, or did they evade the question?
3. FORMULATE AN INSTITUTIONAL DILIGENCE INQUIRY:
   - Address the founder formally and respectfully in 2 to 3 concise sentences (under 55 words).
   - Cite the exact figures, terminology, or visual elements from their slide and contrast them with their statement.
   - Probe unit economics, market sizing methodology, regulatory pathways, distribution economics, or thesis consistency.

Return ONLY a valid JSON object with this exact structure:
{
  "detected_industry": "Inferred strictly from current slide & statement",
  "business_model": "Inferred strictly from current slide & statement",
  "visual_claims_extracted": ["Exact metric or claim read from the slide image"],
  "evaluation": {
    "answered_previous_question": true,
    "evasion_detected": false,
    "contradiction_detected": false,
    "contradiction_detail": "Formal explanation of the discrepancy between the visual slide, current statement, or prior slide (empty string if none)",
    "conviction_delta": 5,
    "inquiry_category": "THESIS INCONSISTENCY | UNIT ECONOMICS DILIGENCE | MARKET & GTM VALIDATION | REGULATORY & MOAT REVIEW | UNANSWERED INQUIRY"
  },
  "vc_spoken_response": "Formal, executive 2-3 sentence question to the founder.",
  "new_skill_guardrail": "Formal due-diligence checklist item to append to SKILL.md"
}`;
}

/**
 * Build the Investment Committee Verdict Prompt
 */
function buildVerdictPrompt() {
  const score = SESSION_STATE.conviction_score;
  const industry = SESSION_STATE.detected_industry;
  const bizModel = SESSION_STATE.business_model;
  const strikes = SESSION_STATE.discrepancy_count;
  const ledger = SESSION_STATE.claim_ledger.slice(-MAX_LEDGER_IN_PROMPT);
  const history = SESSION_STATE.history;
  const contradictions = SESSION_STATE.contradictions_logged;

  let decisionBand = 'DECLINE TO ADVANCE';
  if (score >= 68) {
    decisionBand = 'PROCEED TO TERM SHEET';
  } else if (score >= 45) {
    decisionBand = 'ADVANCE TO SECOND-STAGE DILIGENCE';
  }

  return `You are the Voting Investment Committee of a Tier-1 institutional venture capital firm.
Maintain a composed, analytical, professional, and rigorous tone at all times.

Synthesize a formal Investment Committee Evaluation Memorandum from the live diligence record below. Base every score, strength, risk, and revision item strictly on the actual claims and interrogation transcript recorded in this session.

SESSION DILIGENCE RECORD:
- Sector / Vertical: ${industry}
- Business Model: ${bizModel}
- Final Conviction Index: ${score}/100
- Unresolved Discrepancy Flags: ${strikes}
- Policy Decision Band: ${decisionBand}
- Logged Material Discrepancies:
${JSON.stringify(contradictions, null, 2)}
- Verified Session Claim Ledger:
${JSON.stringify(ledger, null, 2)}
- Diligence Transcript:
${JSON.stringify(history, null, 2)}

Return ONLY a single valid JSON object (no markdown fences, no commentary outside the JSON) with these exact keys:
1. "decision": Must be "${decisionBand}" (one of "PROCEED TO TERM SHEET", "ADVANCE TO SECOND-STAGE DILIGENCE", or "DECLINE TO ADVANCE").
2. "headline_offer_or_reason": A formal 1-sentence executive summary of the IC decision citing specific metrics or findings from the session.
3. "scores": An object with 4 integer keys (each 0 to 100):
   - "market_timing"
   - "unit_economics"
   - "defensibility_moat"
   - "founder_conviction"
4. "biggest_strength": 1 formal sentence citing the most compelling quantitative or strategic evidence established during the session.
5. "fatal_flaw": 1 formal sentence citing the most critical discrepancy, unit-economics vulnerability, or unanswered diligence risk from the session.
6. "mandatory_deck_fixes": Array of 3 specific, actionable deck revisions required prior to advancing.`;
}

/**
 * Compile SKILL.md from SESSION_STATE
 */
function compileSkillMd() {
  const industry = SESSION_STATE.detected_industry;
  const bizModel = SESSION_STATE.business_model;
  const score = SESSION_STATE.conviction_score;
  const contradictions = SESSION_STATE.contradictions_logged;
  const rules = SESSION_STATE.skill_rules;

  const frontmatter = [
    '---',
    'name: hotseat-pitch-defense',
    'description: >',
    '  Audit pitch decks, financial projections, and founder narratives for cross-slide',
    '  contradictions, unit economics flaws, and investor objections before live VC pitches.',
    'license: Apache-2.0',
    'metadata:',
    '  engine: Gemma 4 Multimodal Harness',
    `  detected_industry: "${industry}"`,
    `  business_model: "${bizModel}"`,
    `  conviction_score: "${score}/100"`,
    '---',
    '',
  ].join('\n');

  const section1 = contradictions.length
    ? contradictions.map((c, idx) => `${idx + 1}. ${c}`).join('\n')
    : '_No material cross-slide contradictions logged in the active diligence session._';

  const section2 = rules.length
    ? rules.map((r, idx) => `${idx + 1}. ${r}`).join('\n')
    : '_No session guardrails synthesized yet. Submit a slide or founder defense to compile live rules._';

  const baseChecklist = [
    'Reconcile top-down TAM/SAM/SOM figures against bottom-up customer count and pricing assumptions.',
    'Cross-audit customer acquisition cost (CAC), payback period, and gross margin across marketing and financial slides.',
    'Verify that headcount, R&D milestones, and capital deployment schedules align with stated burn rate and runway.',
    'Confirm that channel partner, distributor, or payment processing fees are reflected in net contribution margins.',
    ...rules.slice(0, 6).map((r) => `[Session Rule] ${r}`),
  ]
    .map((item) => `- [ ] ${item}`)
    .join('\n');

  return [
    frontmatter,
    `# Institutional Pitch-Defense Skill — ${industry}\n`,
    `> **Active IC Conviction Index: ${score}/100** | **Model: ${bizModel}**\n`,
    '## 1. Material Cross-Slide Contradictions & Audit Flags\n',
    section1,
    '',
    '## 2. Synthesized Institutional Diligence Guardrails (Gemma 4 Live Loop)\n',
    section2,
    '',
    '## 3. Pre-Committee Verification Protocol\n',
    baseChecklist,
    '',
  ].join('\n');
}

/**
 * Call Gemma 4 via Google Gemini REST API with multimodal image part BEFORE text prompt
 */
async function callGeminiCascade(prompt, imageBase64, mimeType, apiKey, env) {
  const cfg = resolveEnvConfig(env, { apiKey });
  if (!cfg.geminiApiKey) {
    throw new Error('GEMINI_API_KEY is missing in Cloudflare Worker secrets/environment.');
  }

  const primary = cfg.gemmaModelId;
  const fallbacks = cfg.gemmaFallbackModels
    .split(',')
    .map((s) => cleanEnvValue(s))
    .filter(Boolean);
  const cascade = Array.from(new Set([primary, ...fallbacks, ...CLOUD_CASCADE]));

  // Multimodal ordering rule: image part BEFORE text prompt
  const parts = [];
  if (imageBase64) {
    parts.push({
      inline_data: {
        mime_type: mimeType || 'image/jpeg',
        data: imageBase64,
      },
    });
  }
  parts.push({ text: prompt });

  let lastError = null;
  for (const modelId of cascade) {
    try {
      const startT = Date.now();
      const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(
        modelId
      )}:generateContent?key=${encodeURIComponent(apiKey)}`;

      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ role: 'user', parts }],
          generationConfig: {
            temperature: DEFAULT_TEMPERATURE,
          },
        }),
      });

      const latencyMs = Date.now() - startT;
      const body = await resp.json();

      if (!resp.ok) {
        const errMsg = body?.error?.message || `HTTP ${resp.status}`;
        throw new Error(errMsg);
      }

      const rawText =
        body?.candidates?.[0]?.content?.parts
          ?.map((p) => p.text || '')
          .join('') || '';
      const parsed = extractJsonSafely(rawText);
      parsed.model_id = modelId;
      parsed.engine_used = `gemini_api/${modelId}`;
      parsed.latency_ms = latencyMs;

      console.log(
        JSON.stringify({
          event: 'gemma4_inference_success',
          model_id: modelId,
          latency_ms: latencyMs,
          has_image: Boolean(imageBase64),
        })
      );
      return parsed;
    } catch (err) {
      lastError = err;
      console.warn(
        JSON.stringify({
          event: 'gemma4_model_retry',
          model_id: modelId,
          error: String(err?.message || err),
        })
      );
    }
  }

  throw new Error(
    `Gemini API connection/inference failed across [${cascade.join(', ')}]: ${
      lastError?.message || lastError
    }`
  );
}

/**
 * Ping provider connectivity & measure round-trip latency
 */
async function pingProvider(provider, apiKey, env, ollamaModelOverride = '') {
  const cfg = resolveEnvConfig(env, {
    apiKey,
    ollamaModel: ollamaModelOverride,
  });

  if (provider === 'gemini_api') {
    const modelId = cfg.gemmaModelId;
    if (!cfg.geminiApiKey) {
      return {
        provider: 'gemini_api',
        ok: false,
        model_id: modelId,
        latency_ms: null,
        error: 'GEMINI_API_KEY is missing in environment and no override key was provided.',
      };
    }
    try {
      const startT = Date.now();
      const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(
        modelId
      )}:generateContent?key=${encodeURIComponent(cfg.geminiApiKey)}`;
      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ role: 'user', parts: [{ text: 'Respond only with {"ok": true}' }] }],
          generationConfig: { temperature: 0.0, maxOutputTokens: 16 },
        }),
      });
      const latencyMs = Date.now() - startT;
      if (!resp.ok) {
        const errBody = await resp.json().catch(() => ({}));
        throw new Error(errBody?.error?.message || `HTTP ${resp.status}`);
      }
      return {
        provider: 'gemini_api',
        ok: true,
        model_id: modelId,
        latency_ms: latencyMs,
        error: null,
      };
    } catch (err) {
      return {
        provider: 'gemini_api',
        ok: false,
        model_id: modelId,
        latency_ms: null,
        error: `Gemini API connection error: ${err.message || err}`,
      };
    }
  }

  if (provider === 'ollama') {
    return {
      provider: 'ollama',
      ok: false,
      model_id: cfg.ollamaModel,
      endpoint: cfg.ollamaUrl,
      latency_ms: null,
      error: `Local Ollama (${cfg.ollamaUrl}) is unreachable from Cloudflare Edge runtime. Run locally or use Gemini API.`,
    };
  }

  if (provider === 'lmstudio') {
    return {
      provider: 'lmstudio',
      ok: false,
      model_id: cfg.lmstudioModel,
      endpoint: cfg.lmstudioUrl,
      latency_ms: null,
      error: `Local LM Studio (${cfg.lmstudioUrl}) is unreachable from Cloudflare Edge runtime. Run locally or use Gemini API.`,
    };
  }

  return {
    provider,
    ok: false,
    model_id: 'unknown',
    latency_ms: null,
    error: `Unknown provider '${provider}'`,
  };
}

export default {
  async fetch(request, env, _ctx) {
    const url = new URL(request.url);
    const { pathname } = url;

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    console.log(
      JSON.stringify({
        event: 'http_request',
        method: request.method,
        path: pathname,
        ray: request.headers.get('cf-ray') || null,
      })
    );

    // 1. Health Check
    if (pathname === '/health' && request.method === 'GET') {
      return jsonResponse({
        status: 'ok',
        engine: 'gemma-4-multimodal',
        runtime: 'cloudflare-workers',
      });
    }

    // 2. Provider Connectivity & Latency Probe (/api/ping)
    if (pathname === '/api/ping') {
      let provider = url.searchParams.get('provider') || 'all';
      let apiKeyOverride = '';

      if (request.method === 'POST') {
        const fd = await request.formData().catch(() => null);
        if (fd) {
          provider = String(fd.get('provider') || 'all');
          apiKeyOverride = String(fd.get('api_key') || '').trim();
        }
      }

      const activeKey = cleanEnvValue(apiKeyOverride) || cleanEnvValue(env.GEMINI_API_KEY);

      if (provider === 'all') {
        const [geminiStatus, ollamaStatus, lmstudioStatus] = await Promise.all([
          pingProvider('gemini_api', activeKey, env),
          pingProvider('ollama', activeKey, env),
          pingProvider('lmstudio', activeKey, env),
        ]);
        return jsonResponse({
          providers: {
            gemini_api: geminiStatus,
            ollama: ollamaStatus,
            lmstudio: lmstudioStatus,
          },
        });
      }

      const single = await pingProvider(provider, activeKey, env);
      return jsonResponse(single);
    }

    // 3. Session State Snapshot (/api/state)
    if (pathname === '/api/state' && request.method === 'GET') {
      return jsonResponse(SESSION_STATE);
    }

    // 4. Reset Session (/api/reset)
    if (pathname === '/api/reset' && request.method === 'POST') {
      SESSION_STATE = structuredClone(INITIAL_STATE);
      return jsonResponse({ status: 'reset', session: SESSION_STATE });
    }

    // 5. Self-Improving SKILL.md (/api/skill)
    if (pathname === '/api/skill') {
      const skillMd = compileSkillMd();
      if (request.method === 'POST') {
        return jsonResponse({
          status: 'written',
          path: '.claude/skills/pitch-defense/SKILL.md',
          size_bytes: skillMd.length,
          skill_md: skillMd,
        });
      }
      return new Response(skillMd, {
        status: 200,
        headers: {
          'Content-Type': 'text/markdown; charset=utf-8',
          ...CORS_HEADERS,
        },
      });
    }

    // 6. Multimodal Interrogation (/api/interrogate)
    if (pathname === '/api/interrogate' && request.method === 'POST') {
      try {
        const fd = await request.formData();
        const slideFile = fd.get('slide_image');
        const slideNumber = parseInt(String(fd.get('slide_number') || '1'), 10) || 1;
        const userMessage = String(fd.get('user_message') || '').trim();
        const persona = String(fd.get('persona') || 'sand_hill_vc');
        const provider = String(fd.get('provider') || 'gemini_api');
        const apiKeyOverride = String(fd.get('api_key') || '').trim();

        if (provider !== 'gemini_api') {
          return jsonResponse(
            {
              error: `Provider '${provider}' requires a local server (127.0.0.1) and is not reachable from the Cloudflare Workers edge runtime. Please select 'Gemini API: Gemma 4' or run the backend locally.`,
            },
            500
          );
        }

        let imageBase64 = null;
        let mimeType = 'image/jpeg';
        if (slideFile && typeof slideFile.arrayBuffer === 'function') {
          const buf = await slideFile.arrayBuffer();
          if (buf && buf.byteLength > 0) {
            imageBase64 = arrayBufferToBase64(buf);
            mimeType = slideFile.type || 'image/jpeg';
          }
        }

        if (!imageBase64 && !userMessage) {
          return jsonResponse(
            {
              error: 'Please upload a pitch-deck slide or enter a verbal defense statement.',
            },
            400
          );
        }

        const activeKey = cleanEnvValue(apiKeyOverride) || cleanEnvValue(env.GEMINI_API_KEY);
        const prompt = buildInterrogationPrompt(
          userMessage,
          SESSION_STATE.last_vc_question,
          SESSION_STATE.claim_ledger
        );

        const result = await callGeminiCascade(
          prompt,
          imageBase64,
          mimeType,
          activeKey,
          env
        );

        const rawEval =
          result.evaluation && typeof result.evaluation === 'object'
            ? result.evaluation
            : {};
        const rawClaims = Array.isArray(result.visual_claims_extracted)
          ? result.visual_claims_extracted
          : Array.isArray(result.visual_claims)
            ? result.visual_claims
            : [];
        const visualClaims = rawClaims
          .map((c) => String(c).trim())
          .filter(Boolean);

        const detectedIndustry = String(result.detected_industry || '').trim();
        const businessModel = String(result.business_model || '').trim();
        const answeredPreviousQuestion = Boolean(
          rawEval.answered_previous_question ??
            result.answered_previous_question ??
            true
        );
        const contradictionDetected = Boolean(
          rawEval.contradiction_detected ??
            result.contradiction_detected ??
            false
        );
        const contradictionDetail = String(
          rawEval.contradiction_detail || result.contradiction_detail || ''
        ).trim();
        const evasionDetected = Boolean(
          rawEval.evasion_detected ?? result.evasion_detected ?? false
        );

        const inquiryCategory =
          String(
            rawEval.inquiry_category ||
              result.inquiry_category ||
              rawEval.attack_vector_badge ||
              result.attack_vector_badge ||
              ''
          ).trim() ||
          (contradictionDetected
            ? 'THESIS INCONSISTENCY'
            : evasionDetected
              ? 'UNANSWERED INQUIRY'
              : 'UNIT ECONOMICS DILIGENCE');

        const vcSpokenResponse = String(result.vc_spoken_response || '').trim();
        const convictionDelta = clamp(
          parseInt(
            String(
              rawEval.conviction_delta ?? result.conviction_delta ?? 0
            ),
            10
          ) || 0,
          -20,
          15
        );
        const newSkillGuardrail = String(result.new_skill_guardrail || '').trim();
        const modelId = String(result.model_id || 'gemma-4-26b-a4b-it');
        const engineUsed = String(result.engine_used || `gemini_api/${modelId}`);
        const latencyMs = Number(result.latency_ms || 0);

        for (const claimText of visualClaims) {
          const exists = SESSION_STATE.claim_ledger.some(
            (e) =>
              e.slide === slideNumber &&
              e.source === 'Visual Slide' &&
              e.claim === claimText
          );
          if (!exists) {
            SESSION_STATE.claim_ledger.push({
              slide: slideNumber,
              source: 'Visual Slide',
              claim: claimText,
            });
          }
        }

        if (userMessage) {
          SESSION_STATE.claim_ledger.push({
            slide: slideNumber,
            source: 'Verbal Defense',
            claim: userMessage,
          });
        }

        SESSION_STATE.conviction_score = clamp(
          SESSION_STATE.conviction_score + convictionDelta,
          0,
          100
        );

        if (evasionDetected || contradictionDetected) {
          SESSION_STATE.discrepancy_count += 1;
          SESSION_STATE.evasion_strikes = SESSION_STATE.discrepancy_count;
        }

        if (
          contradictionDetected &&
          contradictionDetail &&
          !SESSION_STATE.contradictions_logged.includes(contradictionDetail)
        ) {
          SESSION_STATE.contradictions_logged.push(contradictionDetail);
        }

        if (detectedIndustry) SESSION_STATE.detected_industry = detectedIndustry;
        if (businessModel) SESSION_STATE.business_model = businessModel;
        SESSION_STATE.last_vc_question = vcSpokenResponse;

        if (
          newSkillGuardrail &&
          !SESSION_STATE.skill_rules.includes(newSkillGuardrail)
        ) {
          SESSION_STATE.skill_rules.push(newSkillGuardrail);
        }

        const turnRecord = {
          turn: SESSION_STATE.history.length + 1,
          slide_number: slideNumber,
          persona,
          user_message: userMessage,
          vc_spoken_response: vcSpokenResponse,
          conviction_delta: convictionDelta,
          evasion_detected: evasionDetected,
          contradiction_detected: contradictionDetected,
          contradiction_detail: contradictionDetail,
          inquiry_category: inquiryCategory,
          attack_vector_badge: inquiryCategory,
          model_id: modelId,
          engine_used: engineUsed,
          latency_ms: latencyMs,
        };
        SESSION_STATE.history.push(turnRecord);

        const evaluation = {
          answered_previous_question: answeredPreviousQuestion,
          evasion_detected: evasionDetected,
          contradiction_detected: contradictionDetected,
          contradiction_detail: contradictionDetail,
          conviction_delta: convictionDelta,
          inquiry_category: inquiryCategory,
          attack_vector_badge: inquiryCategory,
          vc_spoken_response: vcSpokenResponse,
          model_id: modelId,
          latency_ms: latencyMs,
        };

        return jsonResponse({
          turn: turnRecord,
          evaluation,
          visual_claims_extracted: visualClaims,
          visual_claims: visualClaims,
          detected_industry: SESSION_STATE.detected_industry,
          business_model: SESSION_STATE.business_model,
          contradiction_detected: contradictionDetected,
          contradiction_detail: contradictionDetail,
          evasion_detected: evasionDetected,
          inquiry_category: inquiryCategory,
          attack_vector_badge: inquiryCategory,
          vc_spoken_response: vcSpokenResponse,
          conviction_delta: convictionDelta,
          new_skill_guardrail: newSkillGuardrail,
          model_id: modelId,
          engine_used: engineUsed,
          latency_ms: latencyMs,
          session: SESSION_STATE,
        });
      } catch (err) {
        console.error(
          JSON.stringify({
            event: 'interrogate_error',
            error: String(err?.message || err),
          })
        );
        return jsonResponse(
          { error: String(err?.message || err), detail: String(err?.message || err) },
          500
        );
      }
    }

    // 7. Investment Committee Verdict (/api/verdict)
    if (pathname === '/api/verdict' && request.method === 'POST') {
      try {
        if (!SESSION_STATE.history.length && !SESSION_STATE.claim_ledger.length) {
          return jsonResponse(
            {
              error:
                'Cannot generate an Investment Committee Verdict before conducting at least one diligence turn.',
            },
            400
          );
        }

        const fd = await request.formData();
        const provider = String(fd.get('provider') || 'gemini_api');
        const apiKeyOverride = String(fd.get('api_key') || '').trim();

        if (provider !== 'gemini_api') {
          return jsonResponse(
            {
              error: `Provider '${provider}' requires a local server and is not reachable from Cloudflare Workers.`,
            },
            500
          );
        }

        const activeKey = cleanEnvValue(apiKeyOverride) || cleanEnvValue(env.GEMINI_API_KEY);
        const prompt = buildVerdictPrompt();
        const result = await callGeminiCascade(prompt, null, 'image/jpeg', activeKey, env);

        const score = SESSION_STATE.conviction_score;
        const bandDecision =
          score >= 68
            ? 'PROCEED TO TERM SHEET'
            : score >= 45
              ? 'ADVANCE TO SECOND-STAGE DILIGENCE'
              : 'DECLINE TO ADVANCE';

        const rawScores =
          result.scores && typeof result.scores === 'object' ? result.scores : {};
        const scores = {
          market_timing: clamp(parseInt(String(rawScores.market_timing ?? score), 10) || score, 0, 100),
          unit_economics: clamp(parseInt(String(rawScores.unit_economics ?? score), 10) || score, 0, 100),
          defensibility_moat: clamp(parseInt(String(rawScores.defensibility_moat ?? score), 10) || score, 0, 100),
          founder_conviction: clamp(parseInt(String(rawScores.founder_conviction ?? score), 10) || score, 0, 100),
        };

        const fixes = Array.isArray(result.mandatory_deck_fixes)
          ? result.mandatory_deck_fixes.map((f) => String(f).trim()).filter(Boolean)
          : [];

        const modelId = String(result.model_id || 'gemma-4-26b-a4b-it');
        return jsonResponse({
          decision: String(result.decision || bandDecision).trim(),
          headline_offer_or_reason: String(result.headline_offer_or_reason || '').trim(),
          scores,
          biggest_strength: String(result.biggest_strength || '').trim(),
          fatal_flaw: String(result.fatal_flaw || '').trim(),
          mandatory_deck_fixes: fixes,
          model_id: modelId,
          engine_used: String(result.engine_used || `gemini_api/${modelId}`),
          latency_ms: Number(result.latency_ms || 0),
          session: SESSION_STATE,
        });
      } catch (err) {
        console.error(
          JSON.stringify({
            event: 'verdict_error',
            error: String(err?.message || err),
          })
        );
        return jsonResponse(
          { error: String(err?.message || err), detail: String(err?.message || err) },
          500
        );
      }
    }

    // 8. Static Assets Fallback (./static via Cloudflare Assets Binding)
    if (env.ASSETS && typeof env.ASSETS.fetch === 'function') {
      return env.ASSETS.fetch(request);
    }

    return new Response('Not Found', { status: 404 });
  },
};
