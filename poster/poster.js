// The static canvas always shows the complete story; full figures are optional detail.
(() => {
  const figures = [
    {id:'workflow',title:'Synthetic matter workflow',src:'images/01-synthetic-matter-pipeline.webp',note:'Synthetic demo: stub extraction and BM25 search. Matter chat and cited research are separate views; unresolved blockers stop preflight.'},
    {id:'corpus',title:'Syllabus-guided statutory corpus',src:'images/01-syllabus-guided-corpus.webp',note:'Frozen research corpus: 52 principal enactments, 60 amending Acts, 4,557 sections and 6,346 typed edges. Structural checks are separate from legal indispensability.'},
    {id:'benchmark',title:'Benchmark construction',src:'images/01-benchmark-construction.svg',note:'The scored benchmark has 50 statute-only questions across 40 matters. Automated annotation is complete; the three-attorney legal validation stage is planned and pending.'},
    {id:'retrieval',title:'Independent retrieval systems and complete recall',src:'images/01-retrieval-evaluation.webp',note:'Offline comparison of seven alternatives on the frozen corpus. Each produces its own ranking; the typed graph enters S7 only. Reference labels are provisional. Hosted search is lexical.'},
    {id:'case-law',title:'Case-law retrieval pilot',src:'images/01-case-law-retrieval.webp',note:'Optional supporting study: 14/20 and 10/20 come from different corpus snapshots and LLM proxy judgements. Dense retrieval was inactive in the recorded pilot. These are not lawyer-validated accuracy scores.'},
    {id:'document-processing',title:'Document-processing design reference',src:'images/01-document-processing.webp',note:'Historical component design: OCR, quality checks, rotation, classification, grouping, extraction and human review. Neon/GCS labels belong to this reference; the later hosted demo uses self-hosted PostgreSQL, a VPS volume and stub extraction.'},
    {id:'matter-agent',title:'Matter-agent service architecture',src:'images/01-matter-agent-architecture.webp',note:'Optional design reference. Preserve explicit user confirmation, human-only actions and abstention. The legal research tool port is reserved/unimplemented. Storage labels do not establish the current hosted provider configuration.'}
  ];
  const viewer = document.createElement('dialog');
  viewer.id = 'figure-viewer';
  viewer.setAttribute('aria-label','Full-size figures and supporting diagrams');
  viewer.innerHTML = '<div class="viewer-head"><h2 id="viewer-title"></h2><button class="viewer-close" type="button">Close · Esc</button></div><nav class="gallery-tabs" aria-label="Choose a figure"></nav><img class="viewer-image" alt=""><p class="viewer-note"></p>';
  document.body.append(viewer);
  const tabs = viewer.querySelector('.gallery-tabs');
  let opener = null;
  function show(id) {
    const f = figures.find(item => item.id === id) || figures[0];
    viewer.querySelector('#viewer-title').textContent = f.title;
    const img = viewer.querySelector('.viewer-image');
    img.src = f.src; img.alt = f.title;
    viewer.querySelector('.viewer-note').textContent = f.note;
    tabs.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed',String(b.dataset.figure === f.id)));
  }
  figures.forEach(f => {
    const tab = document.createElement('button');
    tab.className = 'gallery-tab'; tab.type = 'button'; tab.dataset.figure = f.id;
    tab.textContent = f.title; tab.addEventListener('click',() => show(f.id)); tabs.append(tab);
  });
  window.openPosterFigure = id => {
    opener = document.activeElement; show(id);
    if (!viewer.open) viewer.showModal();
  };
  document.querySelectorAll('.poster [data-figure]').forEach(button => button.addEventListener('click',() => window.openPosterFigure(button.dataset.figure)));
  viewer.querySelector('.viewer-close').addEventListener('click',() => viewer.close());
  viewer.addEventListener('close',() => opener?.focus());
  // Capture prevents the deck's Esc/arrow shortcuts from consuming dialog navigation.
  addEventListener('keydown',e => {
    if (!viewer.open) return;
    if (e.key === 'Escape') {e.preventDefault();viewer.close();}
    e.stopImmediatePropagation();
  },true);
  const detailButton = document.createElement('button');
  detailButton.type='button';detailButton.textContent='Figures + detail';
  detailButton.addEventListener('click',() => window.openPosterFigure('corpus'));
  document.querySelector('#hint').prepend(detailButton);
  const params = new URLSearchParams(location.search);
  if (params.has('export')) document.body.classList.add('export');
  function fit() {
    document.documentElement.style.setProperty('--poster-scale',String(Math.min(innerWidth/1920,innerHeight/1080)));
  }
  addEventListener('resize',fit); fit();
  window.__setLowPowerMode?.(true,{persist:false});
  window.__posterFigures = figures;
})();
