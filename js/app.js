/* Ora AI — Explorador de torres */
(() => {
  'use strict';

  const C = window.ORA;
  const W = 1672, H = 941;
  const NS = 'http://www.w3.org/2000/svg';
  const $ = (s, r = document) => r.querySelector(s);
  const clamp = (v, a, b) => Math.min(Math.max(v, a), b);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const qs = new URLSearchParams(location.search);
  const scanEnabled = qs.get('scan') !== '0';
  const isTouch = matchMedia('(hover: none)').matches;

  if (qs.has('debug')) document.body.classList.add('debug');

  // ---------------------------------------------------------------- DOM
  const el = {
    stage: $('#stage'), hot: $('#hot'), hud: $('#hud'), flash: $('#flash'),
    imgs: { day: $('#img-day'), night: $('#img-night') },
    tops: { day: $('#top-day'), night: $('#top-night') },
    dot: $('#dot'), line: $('#tipLine'), tip: $('#tip'), hint: $('#hintTxt'), tod: $('#tod'),
    int: $('#int'), fx: $('#fx'), vwrap: $('#vwrap'), vid: $('#vid'), snap: $('#snap'),
    back: $('#back'), backTxt: $('#backTxt'), cap: $('#cap'), capK: $('#capK'), capT: $('#capT'),
    chips: $('#chips'), panel: $('#panel'), panelDetails: $('#panelDetails'), panelToggle: $('#panelToggle'),
    nav: $('#nav'), menuToggle: $('#menuToggle'), mediaStatus: $('#mediaStatus'), loading: $('#mediaLoading'),
  };

  // marca y textos
  document.querySelectorAll('[data-brand]').forEach(n => { n.textContent = C.brand[n.dataset.brand]; });
  $('#legal').textContent = C.copy.legal;
  el.hint.textContent = isTouch ? C.copy.hintTouch : C.copy.hint;
  $('#cta').textContent = C.brand.cta.label;
  $('#cta').href = C.brand.cta.href;
  $('#pPlan').href = C.brand.cta.href;
  $('#brand').addEventListener('click', e => e.preventDefault());

  // ---------------------------------------------------------------- geometría
  // Homografía cuadrado unidad → cuadrilátero [TL, TR, BR, BL] (Heckbert).
  function quadMap(q) {
    const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = q;
    const dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3;
    const dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
    const den = dx1 * dy2 - dx2 * dy1;
    const g = den === 0 ? 0 : (dx3 * dy2 - dx2 * dy3) / den;
    const h = den === 0 ? 0 : (dx1 * dy3 - dx3 * dy1) / den;
    const a = x1 - x0 + g * x1, b = x3 - x0 + h * x3, c = x0;
    const d = y1 - y0 + g * y1, e = y3 - y0 + h * y3, f = y0;
    return (u, v) => { const w = g * u + h * v + 1; return [(a * u + b * v + c) / w, (d * u + e * v + f) / w]; };
  }
  // piso k (1 = el de abajo) de un plano con N pisos
  function floorPoly(map, N, k) {
    const vt = (N - k) / N, vb = (N - k + 1) / N;
    return [map(0, vt), map(1, vt), map(1, vb), map(0, vb)];
  }
  const centroid = p => [p.reduce((s, q) => s + q[0], 0) / p.length, p.reduce((s, q) => s + q[1], 0) / p.length];
  const mk = (tag, attrs = {}) => { const n = document.createElementNS(NS, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); return n; };

  // ---------------------------------------------------------------- estado
  let tod = qs.get('tod') === 'night' ? 'night' : 'day';
  let mode = 'res';
  let state = 'ext';           // ext | int
  let busy = false;
  let hov = null;
  let view = { tx: 0, ty: 0, s: 1 };
  let tl = null;
  let cur = null;              // sesión de interior
  const polys = { day: {}, night: {} };

  function unitFor(plane, k) {
    const T = C.towers[plane.tower];
    return k > T.floors - T.pent ? 'pent' : 'res';
  }

  // ---------------------------------------------------------------- SVG de pisos
  function buildHot() {
    el.hot.innerHTML = '';
    for (const t of ['day', 'night']) {
      const g = mk('g', { 'data-tod': t });
      const pins = mk('g', { class: 'pins' });
      polys[t] = {};
      for (const plane of C.images[t].planes) {
        const T = C.towers[plane.tower];
        const map = quadMap(plane.quad);
        polys[t][plane.id] = {};
        for (let k = 1; k <= T.floors; k++) {
          const pts = floorPoly(map, T.floors, k);
          const node = mk('polygon', { class: 'fl', points: pts.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ') });
          node.dataset.tod = t; node.dataset.plane = plane.id; node.dataset.k = k;
          if (unitFor(plane, k) === 'pent') node.dataset.pent = '1';
          const c = centroid(pts);
          polys[t][plane.id][k] = {
            node, pts, c, plane,
            minX: Math.min(...pts.map(p => p[0])), maxX: Math.max(...pts.map(p => p[0])),
            minY: Math.min(...pts.map(p => p[1])), maxY: Math.max(...pts.map(p => p[1])),
          };
          g.append(node);
        }
      }
      // etiquetas de depuración
      for (const plane of C.images[t].planes) {
        const T = C.towers[plane.tower];
        for (let k = 1; k <= T.floors; k++) {
          const p = polys[t][plane.id][k];
          const tx = mk('text', { class: 'dbg', x: p.c[0], y: p.c[1] + 3, 'text-anchor': 'middle' });
          tx.textContent = T.base + k - 1;
          g.append(tx);
        }
      }
      for (const pin of C.images[t].pins || []) {
        const pg = mk('g', { class: 'pin' });
        pg.append(mk('circle', { class: 'r', cx: pin.x, cy: pin.y, r: 5 }), mk('circle', { class: 'c', cx: pin.x, cy: pin.y, r: 5.5 }));
        const lb = mk('text', { x: pin.x + 14, y: pin.y + 5 }); lb.textContent = pin.label;
        pg.append(lb); pins.append(pg);
      }
      g.append(pins);
      el.hot.append(g);
    }
    syncTodGroups();
  }
  function syncTodGroups() {
    el.hot.querySelectorAll('g[data-tod]').forEach(g => g.classList.toggle('act', g.dataset.tod === tod));
  }

  // ---------------------------------------------------------------- vista (cover)
  function fitView() {
    const vw = innerWidth, vh = innerHeight;
    const s = Math.max(vw / W, vh / H);
    const f = C.images[tod].focus;
    return {
      s,
      tx: clamp(vw / 2 - f[0] * W * s, vw - W * s, 0),
      ty: clamp(vh / 2 - f[1] * H * s, vh - H * s, 0),
    };
  }
  function applyView() { el.stage.style.transform = `translate3d(${view.tx}px,${view.ty}px,0) scale(${view.s})`; }
  const toScreen = (x, y) => [view.tx + view.s * x, view.ty + view.s * y];

  // ---------------------------------------------------------------- hover + tooltip
  let clearTimer = null;
  function info(node) {
    const t = node.dataset.tod, id = node.dataset.plane, k = +node.dataset.k;
    const poly = polys[t][id][k];
    const T = C.towers[poly.plane.tower];
    const unitKey = unitFor(poly.plane, k);
    return { node, tod: t, planeId: id, k, poly, tower: T, floorNo: T.base + k - 1, unitKey, unit: C.units[unitKey] };
  }
  function setHover(node) {
    clearTimeout(clearTimer);
    if (hov && hov.node === node) return;
    if (hov) hov.node.classList.remove('on');
    if (!node) { hov = null; hideTip(); return; }
    hov = info(node);
    node.classList.add('on');
    showTip(hov);
  }
  function scheduleClear() {
    clearTimeout(clearTimer);
    clearTimer = setTimeout(() => setHover(null), 260);
  }
  function hideTip() {
    el.tip.classList.remove('show');
    document.body.classList.remove('tip-on');
    el.dot.style.opacity = 0; el.line.style.opacity = 0;
  }
  function showTip(h) {
    const u = h.unit;
    el.tip.innerHTML =
      `<span class="num"><small>PISO</small><b>${h.floorNo}</b></span><i class="sep"></i>` +
      `<span class="body"><span class="tw">${h.tower.name}</span><strong>${u.name}</strong>` +
      `<span class="sp">${u.specs}</span><em class="chip ${h.unitKey === 'pent' ? 'ex' : ''}">${u.status}</em></span>` +
      `<span class="go" aria-hidden="true">→</span>`;
    el.tip.setAttribute('aria-label', `${h.tower.name}, piso ${h.floorNo}, ${u.name}. Entrar`);
    el.tip.classList.add('show');
    document.body.classList.add('tip-on');
    positionTip(h);
  }
  function positionTip(h) {
    if (innerWidth <= 900) { positionTipCompact(h); return; }
    const vw = innerWidth, vh = innerHeight;
    const p = h.poly;
    const [sx, sy] = toScreen(p.c[0], p.c[1]);
    const tw = el.tip.offsetWidth, th = el.tip.offsetHeight;
    let side = 'r', ex = toScreen(p.maxX, 0)[0] + 52;
    if (ex + tw > vw - 18) { side = 'l'; ex = toScreen(p.minX, 0)[0] - 52 - tw; }
    ex = clamp(ex, 14, vw - tw - 14);
    const ey = clamp(sy, th / 2 + 84, vh - th / 2 - 96);
    el.tip.style.left = ex + 'px';
    el.tip.style.top = (ey - th / 2) + 'px';
    const lx = side === 'r' ? ex : ex + tw, ly = ey;
    const dx = lx - sx, dy = ly - sy;
    el.line.style.width = Math.hypot(dx, dy) + 'px';
    el.line.style.transform = `translate(${sx}px,${sy}px) rotate(${Math.atan2(dy, dx)}rad)`;
    el.dot.style.transform = `translate(${sx}px,${sy}px)`;
    el.dot.style.opacity = 1; el.line.style.opacity = 1;
  }
  // Pantallas estrechas: la misma tarjeta, anclada encima (o debajo) del piso elegido,
  // unida a él por un trazo corto, como en escritorio. Nunca invade la barra ni los controles.
  function positionTipCompact(h) {
    const vw = innerWidth, vh = innerHeight;
    const p = h.poly;
    const [sx, sy] = toScreen(p.c[0], p.c[1]);
    const top = toScreen(0, p.minY)[1], bottom = toScreen(0, p.maxY)[1];
    const tw = el.tip.offsetWidth, th = el.tip.offsetHeight;
    const gap = 26, minTop = 84, maxBottom = vh - 70;
    let ty = top - gap - th, edge = 'b';
    if (ty < minTop) { ty = bottom + gap; edge = 't'; }
    if (ty + th > maxBottom) { ty = clamp(top - gap - th, minTop, maxBottom - th); edge = ty + th <= sy ? 'b' : 't'; }
    const tx = clamp(sx - tw / 2, 12, vw - tw - 12);
    el.tip.style.left = tx + 'px';
    el.tip.style.top = ty + 'px';
    const lx = clamp(sx, tx + 18, tx + tw - 18), ly = edge === 'b' ? ty + th : ty;
    const dx = lx - sx, dy = ly - sy;
    el.line.style.width = Math.hypot(dx, dy) + 'px';
    el.line.style.transform = `translate(${sx}px,${sy}px) rotate(${Math.atan2(dy, dx)}rad)`;
    el.dot.style.transform = `translate(${sx}px,${sy}px)`;
    // Si el piso quedó fuera de la pantalla (se arrastró la fachada), no se dibuja un trazo al vacío.
    const onScreen = sx >= 0 && sx <= vw;
    el.dot.style.opacity = onScreen ? 1 : 0; el.line.style.opacity = onScreen ? 1 : 0;
  }

  // ---------------------------------------------------------------- recorrido automático (modo escaparate)
  const SCAN = {
    res:  [['T2R', 5], ['T2R', 8], ['T2L', 11], ['T2R', 12], ['T2L', 7], ['T1', 6], ['T1', 11], ['T2R', 9]],
  };
  let scanTimer = null, scanI = 0, idleTimer = null;
  function scanStep() {
    scanTimer = null;
    if (!scanEnabled || state !== 'ext' || busy || mode === 'amen') return;
    const seq = mode === 'pent'
      ? C.images[tod].planes.filter(p => p.id === 'T1' || p.id === 'T2R').flatMap(p => {
        const tower = C.towers[p.tower];
        return Array.from({ length: tower.pent }, (_, i) => [p.id, tower.floors - i]);
      })
      : SCAN.res;
    if (!seq.length) return;
    // En pantallas estrechas la fachada no cabe completa: el recorrido solo señala pisos
    // que están a la vista, para que la tarjeta siempre acompañe a un piso visible.
    for (let tries = 0; tries < seq.length; tries++) {
      const [id, k] = seq[scanI++ % seq.length];
      const p = polys[tod][id] && polys[tod][id][k];
      if (!p) continue;
      const sx = toScreen(p.c[0], 0)[0];
      if (sx < 24 || sx > innerWidth - 24) continue;
      setHover(p.node);
      break;
    }
    scanTimer = setTimeout(scanStep, 1050);
  }
  function startScan(delay = 900) {
    stopScan();
    if (scanEnabled && state === 'ext' && !busy && mode !== 'amen') scanTimer = setTimeout(scanStep, delay);
  }
  function stopScan() { clearTimeout(scanTimer); scanTimer = null; }
  function userActive() {
    stopScan(); clearTimeout(idleTimer);
    if (!scanEnabled || mode === 'amen') return;
    idleTimer = setTimeout(() => { if (state === 'ext' && !busy) { setHover(null); startScan(400); } }, 14000);
  }

  // ---------------------------------------------------------------- eventos exterior
  let lastPointer = 'mouse';
  // en pantallas estrechas el edificio es más ancho que la pantalla: se arrastra con el dedo
  let drag = null, moved = false;
  el.hot.addEventListener('pointerdown', e => {
    lastPointer = e.pointerType;
    moved = false;
    if (e.pointerType === 'touch') drag = { x: e.clientX, tx: view.tx, id: e.pointerId };
  });
  addEventListener('pointermove', e => {
    if (!drag || e.pointerId !== drag.id || state !== 'ext' || busy) return;
    const dx = e.clientX - drag.x;
    if (Math.abs(dx) > 8) moved = true;
    if (moved) { view.tx = clamp(drag.tx + dx, innerWidth - W * view.s, 0); applyView(); if (hov) setHover(null); }
  });
  addEventListener('pointerup', () => { drag = null; });
  addEventListener('pointercancel', () => { drag = null; });
  el.hot.addEventListener('pointermove', e => {
    if (state !== 'ext' || busy || e.pointerType === 'touch') return;
    userActive();
    const t = e.target;
    if (t.classList && t.classList.contains('fl')) setHover(t); else scheduleClear();
  });
  el.hot.addEventListener('pointerleave', () => { if (!scanTimer) scheduleClear(); });
  el.hot.addEventListener('click', e => {
    const t = e.target;
    if (!(t.classList && t.classList.contains('fl')) || busy || state !== 'ext') return;
    if (moved) { moved = false; return; }
    userActive();
    if (lastPointer === 'touch' && (!hov || hov.node !== t)) { setHover(t); return; }
    enter(info(t));
  });
  el.tip.addEventListener('pointerenter', () => clearTimeout(clearTimer));
  el.tip.addEventListener('pointerleave', () => scheduleClear());
  el.tip.addEventListener('click', () => { if (hov && !busy) enter(hov); });
  addEventListener('keydown', e => {
    if (e.key === 'Escape' && el.menuToggle.getAttribute('aria-expanded') === 'true') { closeMenu(); el.menuToggle.focus(); return; }
    if (state === 'ext') { if (e.key === 'Enter' && e.target === document.body && hov && !busy) enter(hov); return; }
    if (e.key === 'Escape') onBack();
    if (!cur || cur.mode !== 'room') return;
    if (e.key === 'ArrowRight') goRoom((cur.room + 1) % cur.unit.rooms.length);
    if (e.key === 'ArrowLeft') goRoom((cur.room + cur.unit.rooms.length - 1) % cur.unit.rooms.length);
  });

  // día / noche
  el.tod.addEventListener('click', e => {
    const b = e.target.closest('button[data-tod]');
    if (b) setTod(b.dataset.tod);
  });
  function setTod(t) {
    if (t === tod || busy || state !== 'ext') return;
    stopScan(); setHover(null);
    tod = t; syncTodGroups();
    el.tod.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.tod === t));
    gsap.to([el.imgs.night, el.tops.night], { opacity: t === 'night' ? 1 : 0, duration: reduce ? 0 : 1.3, ease: 'power1.inOut' });
    const to = fitView();
    gsap.to(view, { ...to, duration: reduce ? 0 : 1.3, ease: 'power1.inOut', onUpdate: applyView });
    applyMode();
    userActive();
  }

  function closeMenu() {
    el.nav.classList.remove('open');
    el.menuToggle.setAttribute('aria-expanded', 'false');
  }
  el.menuToggle.addEventListener('click', () => {
    if (cur) return;
    const open = el.menuToggle.getAttribute('aria-expanded') !== 'true';
    el.nav.classList.toggle('open', open);
    el.menuToggle.setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('click', e => {
    if (!el.nav.contains(e.target) && !el.menuToggle.contains(e.target)) closeMenu();
  });

  function setInteriorNavigation(interior) {
    closeMenu();
    el.nav.hidden = interior;
    el.nav.inert = interior;
    el.menuToggle.hidden = interior;
    el.menuToggle.inert = interior;
  }
  const sheetQuery = matchMedia('(max-width: 600px), (max-height: 500px)');
  let panelExpanded = false;
  function syncPanel() {
    const expanded = !sheetQuery.matches || panelExpanded;
    if (!expanded && el.panelDetails.contains(document.activeElement)) el.panelToggle.focus();
    el.panelDetails.hidden = !expanded;
    el.panelToggle.setAttribute('aria-expanded', String(expanded));
    // Rótulo corto y estable; el estado lo comunican aria-expanded y la flecha.
    el.panelToggle.setAttribute('aria-label', expanded ? 'Ocultar detalles' : 'Ver detalles');
  }
  el.panelToggle.addEventListener('click', () => {
    if (!cur || cur.exiting || cur.mode !== 'plan') return;
    panelExpanded = !panelExpanded;
    syncPanel();
  });
  sheetQuery.addEventListener('change', () => { panelExpanded = false; syncPanel(); });
  syncPanel();

  function setLoading(loading) {
    el.loading.hidden = !loading;
    el.int.setAttribute('aria-busy', String(loading));
  }

  // modos del menú: residencias / penthouses / amenidades
  el.nav.addEventListener('click', e => {
    const b = e.target.closest('button[data-mode]');
    if (e.target.closest('a')) closeMenu();
    if (!b || busy || state !== 'ext') return;
    const wasOpen = el.nav.classList.contains('open');
    closeMenu();
    if (wasOpen) el.menuToggle.focus();
    clearTimeout(idleTimer);
    mode = b.dataset.mode;
    el.nav.querySelectorAll('button').forEach(n => n.classList.toggle('on', n === b));
    applyMode();
    setHover(null); scanI = 0;
    if (mode === 'amen') stopScan(); else startScan(500);
  });
  function applyMode() {
    document.body.classList.toggle('mode-amen', mode === 'amen');
    document.body.classList.toggle('mode-pent', mode === 'pent');
    for (const t of ['day', 'night']) for (const id in polys[t]) for (const k in polys[t][id]) {
      const n = polys[t][id][k].node;
      n.classList.toggle('pent-hint', mode === 'pent' && !!n.dataset.pent);
    }
  }

  // ---------------------------------------------------------------- transición exterior → interior
  function buildParts(t, poly, tx, ty, s) {
    el.fx.innerHTML = '';
    const [a, b, c, d] = poly.pts; // TL TR BR BL
    const yAt = (p, q, x) => p[1] + (q[1] - p[1]) * (x - p[0]) / (q[0] - p[0]);
    const X0 = -4000, X1 = 6000, Y = 8000;
    const shapes = {
      top:  [[X0, -Y], [X1, -Y], [X1, yAt(a, b, X1)], [X0, yAt(a, b, X0)]],
      band: [[X0, yAt(a, b, X0)], [X1, yAt(a, b, X1)], [X1, yAt(d, c, X1)], [X0, yAt(d, c, X0)]],
      bot:  [[X0, yAt(d, c, X0)], [X1, yAt(d, c, X1)], [X1, Y], [X0, Y]],
    };
    const out = {};
    for (const key in shapes) {
      const part = document.createElement('div'); part.className = 'part';
      const clone = document.createElement('div'); clone.className = 'clone';
      clone.style.transform = `translate3d(${tx}px,${ty}px,0) scale(${s})`;
      clone.style.clipPath = 'polygon(' + shapes[key].map(p => `${p[0].toFixed(1)}px ${p[1].toFixed(1)}px`).join(',') + ')';
      const im = new Image(); im.src = C.images[t].src; im.alt = ''; im.draggable = false;
      const topExt = document.createElement('div'); topExt.className = 'ext-top';
      const ti = new Image(); ti.src = C.images[t].src; ti.alt = ''; topExt.append(ti);
      clone.append(topExt, im); part.append(clone); el.fx.append(part);
      out[key] = part;
    }
    return out;
  }

  function enter(h) {
    if (busy || state !== 'ext') return;
    setInteriorNavigation(true);
    setLoading(true);
    el.mediaStatus.hidden = true;
    busy = true; stopScan(); clearTimeout(idleTimer);
    cur = { h, unitKey: h.unitKey, unit: h.unit, mode: 'intro', room: 0, busy: true, controller: new AbortController(), exiting: false, staticPlayback: false };
    // Una sola carga, iniciada durante el zoom; los errores se consumen al iniciar el interior.
    cur.ready = ensureSrc(h.unit.clip).then(() => null, error => error);
    prepareInterior();

    const vw = innerWidth, vh = innerHeight;
    const p = h.poly, bw = p.maxX - p.minX;
    const s1 = clamp(0.8 * vw / bw, view.s * 1.7, view.s * 4.4);
    const tx = vw * 0.5 - s1 * p.c[0], ty = vh * 0.5 - s1 * p.c[1];
    const parts = buildParts(h.tod, p, tx, ty, s1);
    const D = reduce ? 0.01 : 1;
    const zoomT = 1.15 * D, split = 1.05 * D;

    // El interior queda operativo cuando las dos mitades de la fachada ya despejaron la
    // pantalla, no al terminar su último milímetro: la ficha aparece al ritmo del original.
    const settle = () => {
      if (tl.reversed() || state === 'int' || !cur || cur.exiting) return;
      busy = false; state = 'int'; document.body.classList.add('is-int'); document.body.classList.remove('is-ext');
      if (cur.planReady) onPlan();
    };
    tl = gsap.timeline({
      paused: true,
      onComplete: settle,
      onReverseComplete: afterExit,
    });
    tl.to(view, { tx, ty, s: s1, duration: zoomT, ease: 'power3.inOut', onUpdate: applyView }, 0)
      .to(el.hud, { autoAlpha: 0, duration: .3 * D, ease: 'none' }, 0)
      .fromTo(el.flash, { opacity: 0 }, { opacity: .55, duration: .4 * D, ease: 'sine.in' }, .62 * D)
      .addLabel('split', split)
      .set(el.stage, { autoAlpha: 0 }, 'split')
      .set(el.fx, { autoAlpha: 1 }, 'split')
      .set(el.int, { autoAlpha: 1 }, 'split')
      .to(el.flash, { opacity: 0, duration: .55 * D, ease: 'sine.out' }, 'split')
      .to(parts.top, { y: -vh * .9, duration: 1.2 * D, ease: 'power3.inOut' }, 'split')
      .to(parts.bot, { y: vh * .9, duration: 1.2 * D, ease: 'power3.inOut' }, 'split')
      .to(parts.band, { autoAlpha: 0, duration: .4 * D, ease: 'power1.out' }, 'split')
      .set(el.fx, { autoAlpha: 0 }, 'split+=' + (1.25 * D))
      .call(() => { if (!tl.reversed()) startInterior(); }, null, 'split+=' + (0.12 * D))
      .call(settle, null, 'split+=' + (0.55 * D));
    tl.timeScale(1).play(0);
  }

  function exitToTower(failed = false) {
    if (!cur || cur.exiting) return;
    const session = cur;
    session.exiting = true;
    setLoading(false);
    session.controller.abort();
    cancelStopper();
    vid.pause();
    busy = true;
    hideUI([el.panel, el.chips, el.cap, el.back]);
    const reverse = () => {
      if (cur !== session) return;
      document.body.classList.remove('is-int'); document.body.classList.add('is-ext');
      state = 'ext';
      if (tl.time() === 0) { tl.kill(); afterExit(); }
      else tl.timeScale(1.15).reverse();
    };
    if (failed || session.busy || vid.readyState < 2) reverse();
    else dissolve(0.04, { fade: .5, signal: null }).catch(() => {}).finally(reverse);
  }
  function mediaFailure(session) {
    if (cur !== session || session.controller.signal.aborted) return;
    el.mediaStatus.textContent = 'No se pudo reproducir el recorrido. Selecciona un piso para volver a intentarlo.';
    el.mediaStatus.hidden = false;
    exitToTower(true);
  }
  function afterExit() {
    cur?.controller.abort();
    setLoading(false);
    setInteriorNavigation(false);
    el.fx.innerHTML = '';
    gsap.set(el.flash, { opacity: 0 });
    gsap.set(el.snap, { opacity: 0 });
    gsap.set([el.stage, el.fx, el.int], { clearProps: 'visibility,opacity' });
    gsap.set(el.stage, { autoAlpha: 1 });
    gsap.set(el.fx, { autoAlpha: 0 });
    gsap.set(el.int, { autoAlpha: 0 });
    gsap.to(el.hud, { autoAlpha: 1, duration: .4 });
    view = fitView(); applyView();
    setHover(null);
    el.vid.pause(); el.vwrap.classList.remove('kb');
    cur = null; busy = false;
    userActive(); startScan(1200);
  }

  // ---------------------------------------------------------------- interior
  const vid = el.vid;
  let stopper = null;
  function cancelStopper() { if (stopper) { stopper.cancel(); stopper = null; } }
  const MEDIA_TIMEOUT = 15000;
  // Todos los listeners, cuadros y temporizadores se limpian al terminar o salir.
  function waitMedia(check, { signal = cur?.controller.signal, start = () => {} } = {}) {
    return new Promise((resolve, reject) => {
      let frame = 0, timer, settled = false;
      const events = ['loadedmetadata', 'loadeddata', 'seeked', 'timeupdate', 'ended', 'error'];
      const cleanup = () => {
        clearTimeout(timer); cancelAnimationFrame(frame);
        events.forEach(event => vid.removeEventListener(event, inspect));
        signal?.removeEventListener('abort', aborted);
      };
      const finish = error => {
        if (settled) return;
        settled = true; cleanup(); error ? reject(error) : resolve();
      };
      const aborted = () => finish(new DOMException('Recorrido cancelado', 'AbortError'));
      const inspect = () => {
        if (settled) return;
        try {
          if (vid.error) return finish(new Error('Error de video'));
          if (check()) return finish();
          cancelAnimationFrame(frame); frame = requestAnimationFrame(inspect);
        } catch (error) { finish(error); }
      };
      if (signal?.aborted) return aborted();
      events.forEach(event => vid.addEventListener(event, inspect));
      signal?.addEventListener('abort', aborted, { once: true });
      timer = setTimeout(() => finish(new Error('Tiempo de espera de video agotado')), MEDIA_TIMEOUT);
      try { start(); inspect(); } catch (error) { finish(error); }
    });
  }
  function ensureSrc(url) {
    if (vid.dataset.src === url && vid.readyState >= 1 && !vid.error) return Promise.resolve();
    return waitMedia(() => vid.readyState >= 1, { start: () => {
      vid.preload = 'auto'; vid.dataset.src = url; vid.src = url; vid.load();
    } });
  }
  vid.addEventListener('error', () => { if (cur) mediaFailure(cur); });
  function prepareInterior() {
    panelExpanded = false; syncPanel();
    gsap.set([el.panel, el.chips, el.cap, el.back], { autoAlpha: 0 });
    gsap.set($('#pBack'), { autoAlpha: 1 });
    gsap.set(el.back, { autoAlpha: 1 });
    const u = cur.unit;
    // panel
    $('#pK').textContent = `PISO ${cur.h.floorNo} · ${u.status}`;
    $('#pT').textContent = u.name;
    $('#pBeds').textContent = u.beds; $('#pBaths').textContent = u.baths; $('#pArea').textContent = u.area;
    $('#pDesc').textContent = u.desc;
    const list = $('#pRooms'); list.innerHTML = '';
    u.rooms.forEach((r, i) => { const li = document.createElement('li'); const b = document.createElement('button'); b.type = 'button'; b.textContent = r.label; b.onclick = () => goRoom(i); li.append(b); list.append(li); });
    // chips
    el.chips.innerHTML = '';
    u.rooms.forEach((r, i) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = r.label; b.dataset.i = i; b.onclick = () => goRoom(i); el.chips.append(b); });
    el.vwrap.classList.remove('kb');
  }

  async function startInterior() {
    const session = cur;
    try {
      el.backTxt.textContent = 'Volver a la torre';
      showUI([el.back]);
      const error = await session.ready;
      if (error) throw error;
      if (session.controller.signal.aborted) return;
      // El aviso de carga se retira con el primer cuadro: no debe quedar sobre el plano visible.
      if (vid.readyState >= 2) setLoading(false);
      else vid.addEventListener('loadeddata', () => { if (cur === session && !session.exiting) setLoading(false); }, { once: true });
      // Los metadatos bastan para buscar un cuadro aunque iOS restrinja play().
      vid.currentTime = 0;
      await playUntil(session.unit.plan.hold);
      if (cur === session && !session.controller.signal.aborted) onPlan();
    } catch (_) { mediaFailure(session); }
  }
  async function playUntil(t) {
    if (cur.staticPlayback) { await dissolve(t); return; }
    cancelStopper();
    const controller = new AbortController();
    const session = cur;
    const sessionSignal = session.controller.signal;
    const abort = () => controller.abort();
    sessionSignal.addEventListener('abort', abort, { once: true });
    if (sessionSignal.aborted) abort();
    stopper = { cancel: abort };
    try {
      let playbackError;
      await waitMedia(() => {
        if (playbackError) throw playbackError;
        return vid.currentTime >= t - 0.02;
      }, { signal: controller.signal, start: () => {
        vid.play().catch(error => { playbackError = error; });
      } });
      vid.pause();
      if (Math.abs(vid.currentTime - t) > 0.04) await dissolve(t, { fade: 0 });
    } catch (error) {
      if (error.name !== 'NotAllowedError' || sessionSignal.aborted) throw error;
      // El bloqueo de autoplay no es un fallo del archivo: muestra sus cuadros en pausa.
      session.staticPlayback = true;
      await dissolve(t);
    } finally {
      sessionSignal.removeEventListener('abort', abort);
      stopper = null;
    }
  }
  // Conserva la disolvencia visual, pero una búsqueda fallida ya no bloquea la interfaz.
  async function dissolve(t, { fade = .5, signal = cur?.controller.signal } = {}) {
    cancelStopper(); vid.pause();
    el.vwrap.classList.remove('kb');
    try {
      el.snap.width = vid.videoWidth || 1600; el.snap.height = vid.videoHeight || 874;
      el.snap.getContext('2d').drawImage(vid, 0, 0, el.snap.width, el.snap.height);
      gsap.set(el.snap, { opacity: 1 });
    } catch (_) { /* El primer cuadro todavía puede no estar disponible. */ }
    if (Math.abs(vid.currentTime - t) >= 0.01 || vid.seeking) {
      await waitMedia(() => vid.readyState >= 2 && !vid.seeking && Math.abs(vid.currentTime - t) < .1,
        { signal, start: () => { vid.currentTime = t; } });
    }
    // Espera a que el navegador pinte el nuevo cuadro antes de retirar la captura.
    let frames = 0;
    await waitMedia(() => vid.readyState >= 2 && ++frames >= 3, { signal });
    gsap.to(el.snap, { opacity: 0, duration: reduce ? 0 : fade, ease: 'power1.inOut' });
  }

  function showUI(list) {
    list.forEach(node => { node.inert = false; });
    gsap.to(list, { autoAlpha: 1, duration: .5, ease: 'power1.out', overwrite: 'auto' });
  }
  function hideUI(list) {
    // Retirar clics y foco inmediatamente, conservando el fundido visual.
    list.forEach(node => { node.inert = true; });
    gsap.to(list, { autoAlpha: 0, duration: .25, overwrite: 'auto' });
  }

  function onPlan() {
    if (!cur || cur.exiting) return;
    cur.planReady = true;
    // No mostrar controles que todavía descartarían un clic durante la transición.
    if (state !== 'int' || busy) return;
    setLoading(false);
    cur.mode = 'plan'; cur.busy = false;
    el.backTxt.textContent = 'Volver a la torre';
    // El panel ya contiene la salida: evita duplicarla y tapar las habitaciones.
    gsap.killTweensOf(el.back);
    el.back.inert = true;
    gsap.set(el.back, { autoAlpha: 0 });
    gsap.set($('#pBack'), { autoAlpha: 1 });
    showUI([el.panel]);
  }
  function enterRoom(i) {
    const u = cur.unit;
    cur.mode = 'room'; cur.room = i; cur.busy = false;
    el.capK.textContent = `PISO ${cur.h.floorNo} · ${u.name.toUpperCase()}`;
    el.capT.textContent = u.rooms[i].label;
    el.chips.querySelectorAll('button').forEach(b => b.classList.toggle('on', +b.dataset.i === i));
    el.backTxt.textContent = 'Volver al plano';
    void el.vwrap.offsetWidth; el.vwrap.classList.add('kb');
    showUI([el.cap, el.chips, el.back]);
  }
  async function goRoom(i) {
    if (!cur || cur.busy || state !== 'int') return;
    if (cur.mode === 'room' && cur.room === i) return;
    const session = cur;
    cur.busy = true;
    const u = cur.unit;
    gsap.set($('#pBack'), { autoAlpha: 0 });
    el.backTxt.textContent = 'Volver a la torre';
    showUI([el.back]);
    hideUI([el.panel, el.cap]);
    try {
      if (cur.mode === 'plan' && i === 0 && !cur.staticPlayback) {
        await dissolve(u.plan.resume, { fade: .45 });
        if (session.controller.signal.aborted) return;
        cur.mode = 'flying';
        await playUntil(u.rooms[0].hold);
      } else await dissolve(u.rooms[i].hold, { fade: .55 });
      if (cur === session && !session.controller.signal.aborted) enterRoom(i);
    } catch (_) { mediaFailure(session); }
  }
  async function goPlan() {
    if (!cur || cur.busy) return;
    const session = cur;
    cur.busy = true;
    gsap.set($('#pBack'), { autoAlpha: 0 });
    el.backTxt.textContent = 'Volver a la torre';
    showUI([el.back]);
    hideUI([el.cap, el.chips]);
    try {
      await dissolve(cur.unit.plan.hold, { fade: .5 });
      if (cur === session && !session.controller.signal.aborted) onPlan();
    } catch (_) { mediaFailure(session); }
  }
  function onBack() {
    if (!cur || cur.exiting) return;
    if (cur.mode === 'room' && !cur.busy) goPlan(); else exitToTower();
  }
  el.back.addEventListener('click', onBack);
  $('#pBack').addEventListener('click', () => {
    if (state === 'int' && cur?.mode === 'plan' && !cur.busy && !el.panel.inert) exitToTower();
  });
  $('#cta').addEventListener('click', e => { if (C.brand.cta.href === '#') e.preventDefault(); });
  $('#pPlan').addEventListener('click', e => { if (C.brand.cta.href === '#') e.preventDefault(); });

  // ---------------------------------------------------------------- arranque
  addEventListener('resize', () => {
    if (innerWidth > 900) closeMenu();
    if (state !== 'ext' || busy) return;
    view = fitView(); applyView();
    if (hov) positionTip(hov);
  });

  function init() {
    buildHot();
    if (tod === 'night') {
      el.imgs.night.style.opacity = 1; el.tops.night.style.opacity = 1;
      el.tod.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.tod === 'night'));
    }
    view = fitView(); applyView();
    applyMode();
    startScan(1600);
    // Los videos se cargan al elegir una unidad, durante la transición de entrada.
  }
  init();

  // API para pruebas y para controlarlo desde la consola
  window.ORA_API = {
    hover: (t, id, k) => { setHover(polys[t][id][k].node); },
    enter: (t, id, k) => { if (t !== tod) { tod = t; syncTodGroups(); } enter(info(polys[t][id][k].node)); },
    exit: exitToTower,
    setTod, goRoom, goPlan,
    timeline: () => tl,   // para revisar la transición cuadro por cuadro: ORA_API.timeline().pause().time(1.2)
    get state() { return { state, busy, mode: cur && cur.mode, tod, t: vid.currentTime }; },
  };
})();
