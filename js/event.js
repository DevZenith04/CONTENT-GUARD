/* Module 03 · Event details · frontend/js/event.js */
(function () {
  'use strict';
  const CG = window.CG;
  CG.renderShell('event');
  const main = document.querySelector('#main');
  const id = new URLSearchParams(location.search).get('id');

  if (!id) {
    main.innerHTML = `
      <div class="page-title"><div>
        <div class="label">Module 03 · Event</div>
        <h1>No event selected</h1>
        <p>Open an event from the review queue or from a workbench result.</p>
      </div></div>
      <div class="row"><a class="btn" href="review.html">Go to review queue</a><a class="btn" href="index.html">Go to workbench</a></div>`;
  } else {
    load();
  }

  async function load() {
    try {
      const { data: ev, source } = await CG.api.getEvent(id);
      CG.banner(source);
      render(ev);
    } catch (e) {
      main.innerHTML = `
        <div class="page-title"><div>
          <div class="label">Module 03 · Event</div>
          <h1>${e.status === 404 ? 'Not found' : 'Could not load event'}</h1>
          <p class="mono err-msg">${CG.esc(e.message)}</p>
        </div></div>
        <a class="btn" href="review.html">Go to review queue</a>`;
    }
  }

  function render(ev) {
    const r = ev.review;
    const final = r && r.final_outcome ? r.final_outcome : null;
    main.innerHTML = `
      <div class="page-title">
        <div>
          <div class="label">Module 03 · Event details</div>
          <h1 class="id mono">${CG.esc(ev.id)}</h1>
          <p>${CG.fmtTime(ev.created_at)} · ${CG.esc(ev.mode)} mode. Metadata only. Raw text is not stored with the event.</p>
        </div>
      </div>
      <div class="grid g-2">
        <section class="panel">
          <div class="label">Decision chain</div>
          <div class="chain mt">
            <div class="link"><div class="label">Original</div>${CG.pill(ev.outcome)}<p class="small muted">Decision engine output</p></div>
            <div class="arrow" aria-hidden="true">→</div>
            <div class="link"><div class="label">Final</div>
              ${final ? CG.pill(final) : '<span class="pill" data-o="REVIEW">Not reviewed</span>'}
              <p class="small muted">${final ? 'Reviewer ' + CG.esc(r.reviewer) : 'No reviewer action'}</p></div>
          </div>
          <p class="mt lead-text">${CG.esc(ev.explanation)}</p>
          ${final ? `<p class="mt"><span class="label">Reason</span><br>${CG.esc(r.reason)}</p>` : ''}
        </section>
        <section class="panel">
          <div class="label">Versions and timing</div>
          <div class="kv mt"><span>Policy version</span><span>${CG.esc(ev.policy_version)}</span></div>
          <div class="kv"><span>Model version</span><span>${CG.esc(ev.model_version)}</span></div>
          <div class="kv"><span>Mode</span><span>${CG.esc(ev.mode)}</span></div>
          <div class="kv"><span>Processing time</span><span>${ev.latency_ms == null ? '—' : ev.latency_ms + ' ms'}</span></div>
          <div class="kv"><span>Text length</span><span>${ev.text_length == null ? '—' : ev.text_length + ' chars'}</span></div>
          <div class="kv"><span>Raw text stored</span><span>NO</span></div>
        </section>
      </div>
      <section class="panel mt">
        <div class="label">Signals</div>
        <div class="mt">${CG.signalList(ev.signals)}</div>
      </section>
      <section class="panel mt">
        <div class="label">Review history</div>
        ${r ? `<ul class="timeline mt">${r.history.map(h => `<li><span class="mono small">${CG.fmtTime(h.at)}</span><br>${CG.esc(h.event)} <span class="muted">· ${CG.esc(h.actor)}</span></li>`).join('')}</ul>`
            : '<p class="muted mt">No review case was created for this event.</p>'}
      </section>
      <div class="row mt">
        <a class="btn" href="review.html">← Review queue</a>
        ${r ? `<a class="btn" href="review.html#${encodeURIComponent(r.case_id)}">Case ${CG.esc(r.case_id)}</a>` : ''}
      </div>`;
  }
})();
