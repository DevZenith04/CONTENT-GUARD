/* ContentGuard API client · frontend/js/api.js
   Calls FastAPI under /v1 (docs/5. API.md). If the server cannot be reached at all,
   returns clearly labelled preview fixtures so the screens can be reviewed.
   Auth, validation and not-found errors are never masked. */
(function (global) {
  'use strict';
  const CG = (global.CG = global.CG || {});

  CG.config = { apiBase: global.CG_API_BASE || '/v1', maxLength: 2000 };
  const clone = o => JSON.parse(JSON.stringify(o));

  class ApiError extends Error {
    constructor(status, code, message) { super(message); this.status = status; this.code = code; }
  }

  async function call(path, options) {
    let res;
    try {
      res = await fetch(CG.config.apiBase + path, Object.assign({
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' }
      }, options || {}));
    } catch (_) {
      const e = new Error('Network unreachable');
      e.network = true;
      throw e;
    }
    let body = null;
    try { body = await res.json(); } catch (_) { /* not JSON */ }
    if (body === null) {
      // The API always answers in JSON. A non-JSON reply means something else answered:
      // a static file server (404/405/501), a gateway error page (502-504), or an HTML
      // fallback page (200). Treat that as "API unreachable" so preview mode still works.
      if (res.ok || [404, 405, 501, 502, 503, 504].includes(res.status)) {
        const e = new Error('API unreachable (non-JSON response, HTTP ' + res.status + ')');
        e.network = true;
        throw e;
      }
      body = {};
    }
    if (!res.ok) {
      const err = (body && body.error) || {};
      throw new ApiError(res.status, err.code, err.message || ('HTTP ' + res.status));
    }
    return body;
  }

  function withPreview(live, preview) {
    return async function (...args) {
      try { return { data: await live(...args), source: 'api' }; }
      catch (e) {
        if (!e.network) throw e;
        return { data: await preview(...args), source: 'preview' };
      }
    };
  }

  const T = s => '2026-10-26T' + s + 'Z';

  // Preview fixtures: illustrative only. They follow the documented shapes and are
  // labelled as preview everywhere they appear. They are not model output or measured results.
  const EVENTS = [
    { id: 'mod_01HZX1A', created_at: T('09:14:22'), mode: 'hybrid', outcome: 'REVIEW', severity: 'high', categories: ['threat'],
      explanation: 'Rule match on a threat pattern. The contextual model reports a direct threat toward a person at 0.91, inside the review band.',
      signals: [{ source: 'rule', name: 'threat_direct_first_person', score: 0.8 }, { source: 'llm', category: 'threat', confidence: 0.91, abstain: false }],
      policy_version: '2026.01.0', model_version: 'transformer:unitary/toxic-bert', latency_ms: 812, text_length: 41,
      review: { case_id: 'case_7F2', status: 'open', reviewer: null, final_outcome: null, reason: null,
        history: [{ at: T('09:14:23'), event: 'Case opened', actor: 'system' }] } },
    { id: 'mod_01HZX2B', created_at: T('09:21:07'), mode: 'hybrid', outcome: 'WARN', severity: 'low', categories: ['harassment'],
      explanation: 'An insult term matched inside a quoted or reported context. Contextual confidence is moderate, so the result is a warning, not a block.',
      signals: [{ source: 'rule', name: 'insult_term', score: 0.4 }, { source: 'llm', category: 'harassment', confidence: 0.52, abstain: false }],
      policy_version: '2026.01.0', model_version: 'transformer:unitary/toxic-bert', latency_ms: 640, text_length: 88, review: null },
    { id: 'mod_01HZX3C', created_at: T('09:33:45'), mode: 'hybrid', outcome: 'ALLOW', severity: 'none', categories: [],
      explanation: 'No configured violation detected with sufficient evidence.',
      signals: [], policy_version: '2026.01.0', model_version: 'transformer:unitary/toxic-bert', latency_ms: 590, text_length: 52, review: null },
    { id: 'mod_01HZX4D', created_at: T('09:40:11'), mode: 'hybrid', outcome: 'BLOCK', severity: 'high', categories: ['threat'],
      explanation: 'An auto-block rule matched and the contextual model confirms a direct threat. Only rules marked auto_block can block without contextual confirmation.',
      signals: [{ source: 'rule', name: 'threat_auto_block', score: 0.97 }, { source: 'llm', category: 'threat', confidence: 0.95, abstain: false }],
      policy_version: '2026.01.0', model_version: 'transformer:unitary/toxic-bert', latency_ms: 905, text_length: 37, review: null },
    { id: 'mod_01HZX5E', created_at: T('10:02:18'), mode: 'llm_only', outcome: 'REVIEW', severity: 'medium', categories: ['hate'],
      explanation: 'The contextual model abstained, which suggests sarcasm or metaphor. Routed to a reviewer.',
      signals: [{ source: 'llm', category: 'hate', confidence: 0.58, abstain: true }],
      policy_version: '2026.01.0', model_version: 'transformer:unitary/toxic-bert', latency_ms: 730, text_length: 64,
      review: { case_id: 'case_3A9', status: 'resolved', reviewer: 'rev_04', final_outcome: 'WARN',
        reason: 'Sarcastic quotation with no target. Warning only.',
        history: [
          { at: T('10:02:19'), event: 'Case opened', actor: 'system' },
          { at: T('10:15:40'), event: 'Assigned', actor: 'rev_04' },
          { at: T('10:21:03'), event: 'Resolved as WARN', actor: 'rev_04' }] } },
    { id: 'mod_01HZX6F', created_at: T('10:30:44'), mode: 'hybrid', outcome: 'REVIEW', severity: 'medium', categories: ['self_harm'],
      explanation: 'No rule matched. The contextual model reports ambiguous distress language at moderate confidence. A person should check for risk.',
      signals: [{ source: 'llm', category: 'self_harm', confidence: 0.44, abstain: false }],
      policy_version: '2026.01.0', model_version: 'transformer:unitary/toxic-bert', latency_ms: 701, text_length: 73,
      review: { case_id: 'case_9C1', status: 'open', reviewer: null, final_outcome: null, reason: null,
        history: [{ at: T('10:30:45'), event: 'Case opened', actor: 'system' }] } }
  ];

  const EVAL = {
    meta: { dataset_hash: 'preview-fixture', items: 200, policy_version: '2026.01.0', model_version: 'transformer:unitary/toxic-bert', run_at: null, preview: true },
    modes: {
      rule_only: { review_rate: 0.11, latency_ms: { median: 14, p95: 31 }, cost_per_1k: null,
        counts: { threat: { tp: 31, fp: 12, fn: 20, tn: 137 }, harassment: { tp: 22, fp: 19, fn: 28, tn: 131 },
                  hate: { tp: 9, fp: 6, fn: 14, tn: 171 }, self_harm: { tp: 5, fp: 4, fn: 9, tn: 182 } } },
      llm_only: { review_rate: 0.18, latency_ms: { median: 640, p95: 1310 }, cost_per_1k: null,
        counts: { threat: { tp: 44, fp: 5, fn: 7, tn: 144 }, harassment: { tp: 38, fp: 9, fn: 12, tn: 141 },
                  hate: { tp: 13, fp: 4, fn: 10, tn: 173 }, self_harm: { tp: 8, fp: 2, fn: 6, tn: 184 } } },
      hybrid: { review_rate: 0.16, latency_ms: { median: 690, p95: 1420 }, cost_per_1k: null,
        counts: { threat: { tp: 46, fp: 4, fn: 5, tn: 145 }, harassment: { tp: 41, fp: 7, fn: 9, tn: 143 },
                  hate: { tp: 14, fp: 3, fn: 9, tn: 174 }, self_harm: { tp: 9, fp: 2, fn: 5, tn: 184 } } }
    }
  };

  function previewModerate(text, mode) {
    const t = text.toLowerCase();
    let outcome = 'ALLOW', severity = 'none', categories = [], signals = [];
    let explanation = 'No configured violation detected with sufficient evidence.';
    if (/\b(hurt|kill|find|stab) you\b/.test(t)) {
      outcome = 'REVIEW'; severity = 'high'; categories = ['threat'];
      signals = [{ source: 'rule', name: 'threat_direct_first_person', score: 0.8 },
                 { source: 'llm', category: 'threat', confidence: 0.91, abstain: false }];
      explanation = 'Rule match on a threat pattern. The contextual model indicates a direct threat toward a person.';
    } else if (/\b(idiot|stupid|pathetic)\b/.test(t)) {
      outcome = 'WARN'; severity = 'low'; categories = ['harassment'];
      signals = [{ source: 'rule', name: 'insult_term', score: 0.4 },
                 { source: 'llm', category: 'harassment', confidence: 0.52, abstain: false }];
      explanation = 'An insult term matched. Contextual assessment is not strong enough to confirm harassment.';
    }
    if (mode === 'llm_only') signals = signals.filter(s => s.source === 'llm');
    if (mode === 'rule_only') signals = signals.filter(s => s.source === 'rule');
    return {
      request_id: 'mod_preview', outcome, severity, categories, explanation, signals,
      policy_version: '2026.01.0', model_version: mode === 'rule_only' ? 'none' : 'preview:fixture',
      latency_ms: null, mode, preview: true
    };
  }

  const caseRow = e => ({
    case_id: e.review.case_id, event_id: e.id, status: e.review.status, severity: e.severity,
    categories: e.categories, created_at: e.created_at, outcome: e.outcome, final_outcome: e.review.final_outcome
  });

  CG.api = {
    moderate: withPreview(
      (text, mode) => call('/moderate', { method: 'POST', body: JSON.stringify({ text, mode }) }),
      async (text, mode) => previewModerate(text, mode)),

    getEvent: withPreview(
      id => call('/moderations/' + encodeURIComponent(id)),
      async id => {
        const ev = EVENTS.find(e => e.id === id);
        if (!ev) throw new ApiError(404, 'not_found', 'Event not found: ' + id);
        return clone(ev);
      }),

    listReviews: withPreview(
      () => call('/reviews'),
      async () => EVENTS.filter(e => e.review).map(caseRow)),

    decideReview: withPreview(
      (caseId, body) => call('/reviews/' + encodeURIComponent(caseId) + '/decision', { method: 'POST', body: JSON.stringify(body) }),
      async (caseId, body) => {
        const ev = EVENTS.find(e => e.review && e.review.case_id === caseId);
        if (!ev) throw new ApiError(404, 'not_found', 'Case not found: ' + caseId);
        if (!['ALLOW', 'WARN', 'BLOCK'].includes(body.final_outcome)) throw new ApiError(422, 'invalid', 'final_outcome must be ALLOW, WARN or BLOCK');
        if (!body.reason) throw new ApiError(422, 'invalid', 'reason is required');
        ev.review.status = 'resolved';
        ev.review.final_outcome = body.final_outcome;
        ev.review.reason = body.reason;
        ev.review.reviewer = 'preview_reviewer';
        ev.review.history.push({ at: T('12:00:00'), event: 'Resolved as ' + body.final_outcome, actor: 'preview_reviewer' });
        return { case_id: caseId, status: 'resolved', final_outcome: body.final_outcome };
      }),

    evaluation: withPreview(
      () => call('/evaluation/latest'),
      async () => clone(EVAL))
  };
})(window);
