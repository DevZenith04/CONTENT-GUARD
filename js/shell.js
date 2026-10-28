/* Shared shell: header, navigation, banner, helpers · frontend/js/shell.js */
(function (global) {
  'use strict';
  const CG = (global.CG = global.CG || {});

  CG.esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  CG.fmtTime = iso => new Date(iso).toLocaleString([], { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false });
  CG.glyph = { ALLOW: '○', WARN: '◐', REVIEW: '◇', BLOCK: '■' };
  CG.pill = o => `<span class="pill" data-o="${CG.esc(o)}">${CG.esc(o)}</span>`;

  /* Discrete 20-segment progress bar */
  CG.bar = (value, max = 1) => {
    const count = 20;
    const on = Math.min(count, Math.max(0, Math.round((Number(value) / max) * count)));
    let s = '<div class="bar" aria-hidden="true">';
    for (let i = 0; i < count; i++) {
      s += `<i class="${i < on ? 'on' : ''}"></i>`;
    }
    return s + '</div>';
  };

  CG.signalList = function (signals) {
    if (!signals || !signals.length) return '<p class="muted small">No signals. Nothing matched.</p>';
    return '<ul class="trace">' + signals.map(s => s.source === 'rule'
      ? `<li><span class="src">RULE</span><span>${CG.esc(s.name)}</span>${CG.bar(s.score)}<span class="mono small">${Number(s.score).toFixed(2)}</span></li>`
      : `<li><span class="src">LLM</span><span>${CG.esc(s.category)}${s.abstain ? ' <span class="chip">ABSTAIN</span>' : ''}</span>${CG.bar(s.confidence)}<span class="mono small">${Number(s.confidence).toFixed(2)}</span></li>`
    ).join('') + '</ul>';
  };

  const NAV = [
    { key: 'workbench', href: 'index.html', n: '01', label: 'Workbench' },
    { key: 'review', href: 'review.html', n: '02', label: 'Review queue' },
    { key: 'event', href: 'event.html', n: '03', label: 'Event' },
    { key: 'evaluation', href: 'evaluation.html', n: '04', label: 'Evaluation' }
  ];

  CG.renderShell = function (active) {
    const mark = `<svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
      <circle cx="15" cy="15" r="7" fill="none" stroke="currentColor" stroke-width="1.2"/>
      <ellipse cx="15" cy="15" rx="14" ry="5.5" fill="none" stroke="currentColor" stroke-width="1" opacity=".6" transform="rotate(-14 15 15)"/>
      <circle cx="26" cy="10" r="1.8" fill="currentColor"/></svg>`;
    document.querySelector('#site').innerHTML = `
      <a class="brand" href="index.html" aria-label="ContentGuard home">${mark}<span>CONTENTGUARD<small>MODERATION CONTROL</small></span></a>
      <nav class="tabs" aria-label="Primary">${NAV.map(n =>
        `<a href="${n.href}" ${n.key === active ? 'aria-current="page"' : ''}><span>${n.n}</span>${n.label}</a>`).join('')}</nav>`;
    const item = NAV.find(n => n.key === active);
    document.title = 'ContentGuard · ' + (item ? item.label : '');
  };

  CG.banner = function (source) {
    const b = document.querySelector('#banner');
    if (b && source === 'preview') {
      b.textContent = 'PREVIEW · API UNREACHABLE · SHOWING LABELLED FIXTURES, NOT MODEL OUTPUT OR MEASURED RESULTS';
      b.classList.add('on');
    }
  };
})(window);
