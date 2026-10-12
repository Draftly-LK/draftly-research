/* Progressive enhancement: the poster and resource links also work without JS. */
(() => {
  'use strict';
  const dialog = document.querySelector('#poster-viewer');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  const stage = document.querySelector('#poster-viewport');
  const poster = document.querySelector('#viewer-poster');
  const value = document.querySelector('#zoom-value');
  const zoomOut = document.querySelector('#zoom-out');
  const zoomIn = document.querySelector('#zoom-in');
  const fullscreen = document.querySelector('#viewer-fullscreen');
  const presets = {
    whole: {x: 0, y: 0, w: 1920, h: 1080},
    software: {x: 16, y: 160, w: 610, h: 904},
    research: {x: 634, y: 160, w: 1266, h: 906},
    results: {x: 1490, y: 588, w: 420, h: 472}
  };
  let scale = 1, tx = 0, ty = 0, fit = 1, selected = 'whole', opener;
  let viewerFullscreen = false;
  const points = new Map();
  let pinch;
  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
  const limits = () => {
    const w = stage.clientWidth, h = stage.clientHeight;
    tx = 1920 * scale <= w ? (w - 1920 * scale) / 2 : clamp(tx, w - 1920 * scale - 32, 32);
    ty = 1080 * scale <= h ? (h - 1080 * scale) / 2 : clamp(ty, h - 1080 * scale - 32, 32);
  };
  const render = () => {
    limits();
    poster.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
    value.value = `${Math.round(scale * 100)}%`;
    stage.dataset.zoom = scale.toFixed(5);
    stage.dataset.view = selected || 'custom';
    zoomOut.disabled = scale <= fit + .0001;
    zoomIn.disabled = scale >= 3 - .0001;
    if (document.activeElement === zoomOut && zoomOut.disabled || document.activeElement === zoomIn && zoomIn.disabled) {
      stage.focus({preventScroll: true});
    }
    dialog.querySelectorAll('[data-poster-view]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.posterView === selected));
    });
  };
  const frame = (name = 'whole') => {
    if (!dialog.open || !stage.clientWidth || !stage.clientHeight) return;
    const area = presets[name] || presets.whole;
    fit = Math.min((stage.clientWidth - 24) / 1920, (stage.clientHeight - 24) / 1080);
    scale = clamp(Math.min((stage.clientWidth - 24) / area.w, (stage.clientHeight - 24) / area.h), fit, 3);
    tx = stage.clientWidth / 2 - (area.x + area.w / 2) * scale;
    ty = stage.clientHeight / 2 - (area.y + area.h / 2) * scale;
    selected = name;
    render();
  };
  const zoom = (next, x = stage.clientWidth / 2, y = stage.clientHeight / 2) => {
    next = clamp(next, fit, 3);
    tx = x - (x - tx) * next / scale;
    ty = y - (y - ty) * next / scale;
    scale = next;
    selected = null;
    render();
  };
  document.querySelectorAll('[data-open-poster]').forEach(link => {
    link.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.altKey || event.shiftKey || event.button > 0) return;
      event.preventDefault();
      opener = link;
      dialog.showModal();
      document.body.classList.add('poster-viewer-open');
      selected = link.dataset.openPoster;
      frame(selected);
      document.querySelector('#viewer-close').focus({preventScroll: true});
    });
  });
  const close = async () => {
    if (viewerFullscreen && document.fullscreenElement) {
      try { await document.exitFullscreen(); } catch (_) { /* Closing still works. */ }
    }
    dialog.close();
  };
  document.querySelector('#viewer-close').addEventListener('click', close);
  dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
  dialog.addEventListener('close', () => {
    points.clear();
    pinch = null;
    stage.classList.remove('is-dragging');
    document.body.classList.remove('poster-viewer-open');
    opener?.focus({preventScroll: true});
  });
  dialog.querySelectorAll('[data-poster-view]').forEach(button => {
    button.addEventListener('click', () => frame(button.dataset.posterView));
  });
  zoomOut.addEventListener('click', () => zoom(scale / 1.25));
  zoomIn.addEventListener('click', () => zoom(scale * 1.25));
  document.querySelector('#zoom-fit').addEventListener('click', () => frame());
  stage.addEventListener('wheel', event => {
    event.preventDefault();
    const box = stage.getBoundingClientRect();
    const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? stage.clientHeight : 1);
    zoom(scale * Math.exp(clamp(-delta * .002, -.7, .7)), event.clientX - box.left, event.clientY - box.top);
  }, {passive: false});
  const localPoint = event => {
    const box = stage.getBoundingClientRect();
    return {x: event.clientX - box.left, y: event.clientY - box.top};
  };
  const beginPinch = () => {
    if (points.size !== 2) { pinch = null; return; }
    const [a, b] = [...points.values()];
    pinch = {distance: Math.max(1, Math.hypot(a.x - b.x, a.y - b.y)), scale,
      x: ((a.x + b.x) / 2 - tx) / scale, y: ((a.y + b.y) / 2 - ty) / scale};
  };
  stage.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    stage.focus({preventScroll: true});
    stage.setPointerCapture(event.pointerId);
    points.set(event.pointerId, localPoint(event));
    stage.classList.add('is-dragging');
    beginPinch();
  });
  stage.addEventListener('pointermove', event => {
    if (!points.has(event.pointerId)) return;
    const old = points.get(event.pointerId), next = localPoint(event);
    points.set(event.pointerId, next);
    if (points.size === 2 && pinch) {
      const [a, b] = [...points.values()];
      scale = clamp(pinch.scale * Math.hypot(a.x - b.x, a.y - b.y) / pinch.distance, fit, 3);
      tx = (a.x + b.x) / 2 - pinch.x * scale;
      ty = (a.y + b.y) / 2 - pinch.y * scale;
    } else if (points.size === 1) {
      tx += next.x - old.x;
      ty += next.y - old.y;
    }
    selected = null;
    render();
  });
  const release = event => {
    points.delete(event.pointerId);
    beginPinch();
    if (!points.size) stage.classList.remove('is-dragging');
  };
  stage.addEventListener('pointerup', release);
  stage.addEventListener('pointercancel', release);
  stage.addEventListener('lostpointercapture', release);
  dialog.addEventListener('keydown', event => {
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key === 'Tab') {
      const controls = [...dialog.querySelectorAll('a[href],button:not(:disabled),[tabindex="0"]')]
        .filter(element => element.getClientRects().length);
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first || !event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      }
      return;
    }
    if (event.key === '+' || event.key === '=') zoom(scale * 1.25);
    else if (event.key === '-' || event.key === '_') zoom(scale / 1.25);
    else if (event.key === '0') frame();
    else if (event.target === stage && ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
      tx += event.key === 'ArrowLeft' ? 45 : event.key === 'ArrowRight' ? -45 : 0;
      ty += event.key === 'ArrowUp' ? 45 : event.key === 'ArrowDown' ? -45 : 0;
      selected = null;
      render();
    } else return;
    event.preventDefault();
  });
  if (!document.fullscreenEnabled || !document.documentElement.requestFullscreen) fullscreen.hidden = true;
  fullscreen.addEventListener('click', async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else {
        await document.documentElement.requestFullscreen();
        viewerFullscreen = true;
      }
    } catch (_) {
      document.querySelector('#poster-viewer-help').textContent = 'Fullscreen is unavailable here. You can still zoom and drag the poster.';
    }
  });
  document.addEventListener('fullscreenchange', () => {
    fullscreen.textContent = document.fullscreenElement ? 'Exit fullscreen' : 'Fullscreen';
    if (!document.fullscreenElement) viewerFullscreen = false;
  });
  new ResizeObserver(() => { if (dialog.open) frame(selected || 'whole'); }).observe(stage);
  const projectURL = 'https://draftly-lk.github.io/draftly-research/';
  const shareStatus = document.querySelector('#share-status');
  document.querySelectorAll('.share-link').forEach(button => button.addEventListener('click', async () => {
    document.querySelector('.share-fallback').hidden = true;
    shareStatus.textContent = '';
    if (navigator.share) {
      try { await navigator.share({title: 'Explore Draftly', url: projectURL}); return; }
      catch (error) { if (error.name === 'AbortError') return; }
    }
    try {
      await navigator.clipboard.writeText(projectURL);
      shareStatus.textContent = 'Project link copied.';
    } catch (_) {
      document.querySelector('.share-fallback').hidden = false;
      const input = document.querySelector('#share-url');
      input.focus();
      input.select();
      shareStatus.textContent = 'Copy the project link below.';
    }
  }));
  document.documentElement.classList.add('enhanced');
})();
