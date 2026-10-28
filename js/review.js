/* Module 02 · Review queue · frontend/js/review.js */
(function () {
  'use strict';
  const CG = window.CG;
  CG.renderShell('review');

  const CATS = ['harassment', 'threat', 'hate', 'self_harm'];
  const state = { cases: [], openId: null, filters: { severity: 'all', category: 'all', status: 'all', q: '' } };
  const main = document.querySelector('#main');

  main.innerHTML = `
    <div class="page-title">
      <div>
        <div class="label">Module 02 · Reviewers</div>
        <h1>Review queue</h1>
        <p>Cases the system could not decide with confidence. A reviewer confirms or overrides the outcome, and every decision is audited.</p>
      </div>
      <div class="tiles tiles-sm" id="qTiles" style="min-width:min(520px,100%)"></div>
    </div>
    <div class="panel filters" role="search">
      <label class="fld"><span class="label">Severity</span>
        <select id="fSev"><option value="all">All</option><option>high</option><option>medium</option><option>low</option></select></label>
      <label class="fld"><span class="label">Category</span>
        <select id="fCat"><option value="all">All</option>${CATS.map(c => `<option>${c}</option>`).join('')}</select></label>
      <label class="fld"><span class="label">Status</span>
        <select id="fStatus"><option value="all">All</option><option>open</option><option>in_review</option><option>resolved</option></select></label>
      <label class="fld grow"><span class="label">Search by ID</span>
        <input id="fQ" type="search" placeholder="case_ or mod_"></label>
    </div>
    <div class="panel tablewrap" id="tableWrap"></div>
    <div class="scrim" id="scrim"></div>
    <aside class="drawer" id="drawer" role="dialog" aria-modal="true" aria-label="Case details" aria-hidden="true"></aside>`;

  function visible() {
    const f = state.filters, q = f.q.trim().toLowerCase();
    return state.cases.filter(c =>
      (f.severity === 'all' || c.severity === f.severity) &&
      (f.category === 'all' || c.categories.includes(f.category)) &&
      (f.status === 'all' || c.status === f.status) &&
      (!q || c.case_id.toLowerCase().includes(q) || c.event_id.toLowerCase().includes(q)));
  }

  function render() {
    const t = state.cases;
    document.querySelector('#qTiles').innerHTML = [
      ['Open', t.filter(c => c.status === 'open').length],
      ['In review', t.filter(c => c.status === 'in_review').length],
      ['Resolved', t.filter(c => c.status === 'resolved').length],
      ['High · unresolved', t.filter(c => c.status !== 'resolved' && c.severity === 'high').length]
    ].map(([l, v]) => `<div class="tile"><div class="label">${l}</div><div class="v">${v}</div></div>`).join('');

    const rows = visible();
    document.querySelector('#tableWrap').innerHTML = rows.length ? `
      <table class="thin">
        <thead><tr><th>Case</th><th>Event</th><th>Created</th><th>Severity</th><th>Categories</th><th>System</th><th>Status</th></tr></thead>
        <tbody>${rows.map(c => `
          <tr tabindex="0" data-case="${CG.esc(c.case_id)}" aria-selected="${c.case_id === state.openId}">
            <td class="mono small">${CG.esc(c.case_id)}</td>
            <td class="mono small muted">${CG.esc(c.event_id)}</td>
            <td class="mono small">${CG.fmtTime(c.created_at)}</td>
            <td>${CG.esc(c.severity)}</td>
            <td>${c.categories.map(x => `<span class="chip">${CG.esc(x)}</span>`).join(' ')}</td>
            <td>${CG.pill(c.outcome)}</td>
            <td class="mono small">${CG.esc(c.status)}${c.final_outcome ? ' → ' + CG.esc(c.final_outcome) : ''}</td>
          </tr>`).join('')}</tbody>
      </table>` : '<div class="empty">No cases match these filters.</div>';
  }

  async function load() {
    try {
      const { data, source } = await CG.api.listReviews();
      CG.banner(source);
      state.cases = data;
      render();
    } catch (e) {
      document.querySelector('#tableWrap').innerHTML =
        `<div class="empty" role="alert">Could not load the review queue: ${CG.esc(e.message)}</div>`;
    }
  }

  function openDrawer() {
    const d = document.querySelector('#drawer');
    d.classList.add('open');
    d.setAttribute('aria-hidden', 'false');
    document.querySelector('#scrim').classList.add('on');
    const btn = d.querySelector('[data-close]');
    if (btn) btn.focus();
  }

  function closeDrawer() {
    const d = document.querySelector('#drawer');
    d.classList.remove('open');
    d.setAttribute('aria-hidden', 'true');
    document.querySelector('#scrim').classList.remove('on');
    state.openId = null;
    render();
  }

  async function openCase(caseId) {
    const c = state.cases.find(x => x.case_id === caseId);
    if (!c) return;
    let ev, source;
    try {
      ({ data: ev, source } = await CG.api.getEvent(c.event_id));
    } catch (e) {
      CG.toast('Could not open case: ' + e.message);
      return;
    }
    CG.banner(source);
    const r = ev.review;
    if (!r) { CG.toast('No review case exists for this event'); return; }
    state.openId = caseId;
    const drawer = document.querySelector('#drawer');
    drawer.dataset.case = caseId;
    drawer.innerHTML = `
      <div class="row between"><span class="label mono">${CG.esc(caseId)}</span><button class="btn btn-sm" type="button" data-close>Close</button></div>
      <div class="row mt">${CG.pill(ev.outcome)}<span class="label">system · ${CG.esc(ev.severity)}</span></div>
      <p class="mt" style="line-height:1.6">${CG.esc(ev.explanation)}</p>
      <div class="label mt">Signals</div>
      <div class="mt">${CG.signalList(ev.signals)}</div>
      <div class="panel-inset mt">
        <div class="label">Case text</div>
        <p class="small muted mt">Withheld. Text for review cases needs a separate, access-controlled store, and its retention rule is not defined yet.</p>
      </div>
      ${r.status === 'resolved' ? `
        <div class="mt"><div class="label">Final decision</div>
          <div class="mt">${CG.pill(r.final_outcome)}</div>
          <p class="mt">${CG.esc(r.reason)}</p>
          <p class="small muted mt">Reviewer ${CG.esc(r.reviewer)}</p></div>`
      : `<form id="decide" class="mt" novalidate>
          <div class="label">Reviewer decision</div>
          <div class="radios mt">${['ALLOW', 'WARN', 'BLOCK'].map(o =>
            `<label class="opt"><input type="radio" name="final" value="${o}"><span>${CG.glyph[o]} ${o}</span></label>`).join('')}</div>
          <p class="small muted mt">REVIEW is a case status, not a final outcome. A reason is always required.</p>
          <label class="fld mt"><span class="label">Reason</span>
            <textarea id="reason" rows="3" placeholder="What decided this case?"></textarea></label>
          <p class="mono small mt" id="fErr" role="alert" style="min-height:20px;color:var(--accent)"></p>
          <div class="row"><button class="btn btn-primary" type="submit">Record decision</button>
            <span class="small muted">Audit entry: review.override</span></div>
        </form>`}
      <div class="mt"><div class="label">History</div>
        <ul class="timeline mt">${r.history.map(h => `<li><span class="mono small">${CG.fmtTime(h.at)}</span><br>${CG.esc(h.event)} <span class="muted">· ${CG.esc(h.actor)}</span></li>`).join('')}</ul>
      </div>`;
    openDrawer();
    render();
  }

  main.addEventListener('click', e => {
    const row = e.target.closest('tr[data-case]');
    if (row) openCase(row.dataset.case);
  });
  main.addEventListener('keydown', e => {
    const row = e.target.closest('tr[data-case]');
    if (row && e.key === 'Enter') openCase(row.dataset.case);
  });
  main.addEventListener('input', e => {
    if (e.target.id === 'fQ') { state.filters.q = e.target.value; render(); }
  });
  main.addEventListener('change', e => {
    const map = { fSev: 'severity', fCat: 'category', fStatus: 'status' };
    if (map[e.target.id]) { state.filters[map[e.target.id]] = e.target.value; render(); }
  });

  document.addEventListener('click', e => {
    if (e.target.closest('[data-close]') || e.target.id === 'scrim') closeDrawer();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && document.querySelector('#drawer').classList.contains('open')) closeDrawer();
  });

  document.querySelector('#drawer').addEventListener('submit', async e => {
    e.preventDefault();
    const drawer = document.querySelector('#drawer');
    const caseId = drawer.dataset.case;
    const picked = drawer.querySelector('input[name=final]:checked');
    const reasonEl = drawer.querySelector('#reason');
    const reason = reasonEl ? reasonEl.value.trim() : '';
    const err = drawer.querySelector('#fErr');
    if (!picked) { err.textContent = 'Choose ALLOW, WARN, or BLOCK.'; return; }
    if (!reason) { err.textContent = 'A reason is required.'; return; }
    err.textContent = '';
    const submitBtn = drawer.querySelector('button[type=submit]');
    if (submitBtn) submitBtn.disabled = true;
    try {
      const { data, source } = await CG.api.decideReview(caseId, { final_outcome: picked.value, reason });
      CG.banner(source);
      CG.toast('Recorded ' + data.final_outcome + ' · audit entry written');
      await load();
      await openCase(caseId);
    } catch (ex) {
      err.textContent = ex.message;
      if (submitBtn) submitBtn.disabled = false;
    }
  });

  // Deep link from the event page: review.html#case_7F2 opens that case
  load().then(() => {
    const wanted = decodeURIComponent(location.hash.slice(1));
    if (wanted) openCase(wanted);
  });
})();
