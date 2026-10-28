/* Module 04 · Evaluation · frontend/js/evaluation.js
   Every metric is computed here from confusion counts (docs/14, metric functions). */
(function () {
  'use strict';
  const CG = window.CG;
  CG.renderShell('evaluation');

  const CATS = ['threat', 'harassment', 'hate', 'self_harm'];
  const MODES = [['rule_only', 'Rule only'], ['llm_only', 'LLM only'], ['hybrid', 'Hybrid']];
  let mode = 'hybrid';
  let data = null;
  const main = document.querySelector('#main');

  main.innerHTML = `
    <div class="page-title">
      <div>
        <div class="label">Module 04 · Research</div>
        <h1>Evaluation</h1>
        <p>Rule-only, LLM-only and hybrid run on the same labelled items. Every figure below is computed from confusion counts, not typed in.</p>
      </div>
      <div class="switch" role="radiogroup" aria-label="Approach">
        ${MODES.map(([v, l]) => `<button role="radio" aria-checked="${v === mode}" data-mode="${v}">${l}</button>`).join('')}
      </div>
    </div>
    <section class="tiles" id="tiles"></section>
    <div class="grid g-2 mt">
      <section class="panel"><div class="label">Per category</div><div class="mt" id="percat"></div></section>
      <section class="panel"><div class="label">Comparison · all approaches</div><div class="mt" id="compare"></div></section>
    </div>
    <section class="panel mt"><div class="label">Confusion · <span id="cmName"></span></div><div class="cm mt" id="cm"></div></section>
    <section class="panel mt"><div class="label">Run record</div><div class="mt" id="meta"></div></section>`;

  const div = (a, b) => (b ? a / b : null);
  const pct = v => (v == null ? '—' : (v * 100).toFixed(1) + '%');

  function metrics(c) {
    const P = div(c.tp, c.tp + c.fp);
    const R = div(c.tp, c.tp + c.fn);
    const F1 = P != null && R != null && P + R > 0 ? 2 * P * R / (P + R) : null;
    return { P, R, F1, FPR: div(c.fp, c.fp + c.tn), FNR: div(c.fn, c.fn + c.tp) };
  }

  function summary(modeKey) {
    const m = data.modes[modeKey];
    const rows = CATS.filter(k => m.counts && m.counts[k])
      .map(k => ({ k, ...metrics(m.counts[k]), pos: m.counts[k].tp + m.counts[k].fn }));
    const avg = f => {
      const v = rows.map(r => r[f]).filter(x => x != null);
      return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
    };
    return { rows, P: avg('P'), R: avg('R'), F1: avg('F1'), FPR: avg('FPR'), FNR: avg('FNR'), review: m.review_rate, lat: m.latency_ms, cost: m.cost_per_1k };
  }

  const tile = (label, value, note) =>
    `<div class="tile"><div class="label">${label}</div><div class="v">${value}</div><div class="small muted">${note}</div></div>`;

  function render() {
    const s = summary(mode);
    document.querySelector('#cmName').textContent = MODES.find(m => m[0] === mode)[1];

    document.querySelector('#tiles').innerHTML = [
      tile('Precision', pct(s.P), 'macro, 4 categories'),
      tile('Recall', pct(s.R), 'macro, 4 categories'),
      tile('F1', pct(s.F1), 'macro, 4 categories'),
      tile('False positive rate', pct(s.FPR), 'macro'),
      tile('False negative rate', pct(s.FNR), 'macro'),
      tile('Review rate', pct(s.review), 'share sent to a human'),
      tile('Latency median', s.lat.median + ' ms', 'p95 ' + s.lat.p95 + ' ms'),
      tile('Cost per 1,000', s.cost == null ? 'not measured' : '$' + s.cost, 'provider dependent')
    ].join('');

    document.querySelector('#percat').innerHTML = `<table class="thin">
      <thead><tr><th>Category</th><th>Positives</th><th>Precision</th><th>Recall</th><th>F1</th><th>FPR</th><th>FNR</th></tr></thead>
      <tbody>${s.rows.map(r => `<tr><td>${r.k}</td><td class="mono small">${r.pos}</td><td class="mono small">${pct(r.P)}</td>
        <td class="mono small">${pct(r.R)}</td><td class="mono small">${pct(r.F1)}</td><td class="mono small">${pct(r.FPR)}</td><td class="mono small">${pct(r.FNR)}</td></tr>`).join('')}</tbody></table>`;

    const cmp = MODES.map(([k, l]) => {
      const x = summary(k);
      return `<tr aria-selected="${k === mode}"><td>${l}</td><td class="mono small">${pct(x.F1)}</td><td class="mono small">${pct(x.FPR)}</td>
        <td class="mono small">${pct(x.FNR)}</td><td class="mono small">${pct(x.review)}</td><td class="mono small">${x.lat.median} ms</td></tr>`;
    }).join('');
    document.querySelector('#compare').innerHTML = `<table class="thin">
      <thead><tr><th>Approach</th><th>F1</th><th>FPR</th><th>FNR</th><th>Review</th><th>Median</th></tr></thead>
      <tbody>${cmp}</tbody></table>
      <p class="small muted mt">Cost is not measured in this run, so no cost figures are shown.</p>`;

    const counts = data.modes[mode].counts || {};
    document.querySelector('#cm').innerHTML = CATS.filter(k => counts[k]).map(k => {
      const c = counts[k];
      const total = c.tp + c.fp + c.fn + c.tn;
      const cell = (label, n, cls) => {
        const on = Math.round(n / total * 100);
        const dots = Array.from({ length: 100 }, (_, i) => `<i class="${i < on ? 'on' : ''}"></i>`).join('');
        return `<div class="cell ${cls}"><span>${label}</span><b>${n}</b><div class="dotfield">${dots}</div></div>`;
      };
      return `<div class="cmcat">
        <div class="label">${k}</div>
        <div class="cmgrid">
          ${cell('True positive', c.tp, 'tp')}${cell('False positive', c.fp, 'fp')}
          ${cell('False negative', c.fn, 'fn')}${cell('True negative', c.tn, 'tn')}
        </div></div>`;
    }).join('');

    document.querySelector('#meta').innerHTML = `
      <div class="kv"><span>Dataset hash</span><span>${CG.esc(data.meta.dataset_hash)}</span></div>
      <div class="kv"><span>Labelled items per category</span><span>${data.meta.items}</span></div>
      <div class="kv"><span>Policy version</span><span>${CG.esc(data.meta.policy_version)}</span></div>
      <div class="kv"><span>Model version</span><span>${CG.esc(data.meta.model_version)}</span></div>
      <div class="kv"><span>Run recorded</span><span>${data.meta.run_at ? CG.esc(data.meta.run_at) : 'preview · no run'}</span></div>`;
  }

  main.addEventListener('click', e => {
    const m = e.target.closest('[data-mode]');
    if (!m) return;
    mode = m.dataset.mode;
    document.querySelectorAll('[data-mode]').forEach(b => b.setAttribute('aria-checked', String(b.dataset.mode === mode)));
    render();
  });

  (async function load() {
    try {
      const { data: d, source } = await CG.api.evaluation();
      CG.banner(source);
      data = d;
      render();
    } catch (e) {
      document.querySelector('#tiles').innerHTML =
        `<div class="empty" role="alert">Could not load the evaluation: ${CG.esc(e.message)}</div>`;
    }
  })();
})();
