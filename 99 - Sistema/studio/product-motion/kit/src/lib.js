// Shared scene helpers (inlined into index.html by build.mjs). Usage inside a scene script, after fonts are ready:
//   const pm = window.__pm(root, tl, { V, S });  // S = base camera scale
// Everything is seek-safe: only adds tweens to the paused timeline.
window.__pm = (root, tl, { V, S }) => {
  const $ = gsap.utils.selector(root);
  const cam = $('.cam')[0];
  const cur = $('.cursor')[0], ring = $('.click-ring')[0];
  // visible window size in screen px (win is 1728 wide in 16:9, 1000 in 9:16; it bleeds off the bottom)
  const VIEW = V ? { w: 1000, h: 1480 } : { w: 1728, h: 844 };
  if (cam) gsap.set(cam, { scale: S, x: 0, y: 0 });
  // point of an element in cam-native coordinates (layout based: ignores transforms)
  const pt = (el, fx = 0.5, fy = 0.5) => { let x = 0, y = 0, e = el; while (e && e !== cam) { x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; } return { x: x + el.offsetWidth * fx, y: y + el.offsetHeight * fy }; };
  // sidebar: mark the active item and scroll the nav so it is visible (like the real app)
  const sbItem = $('.sb-it[data-k="' + ($('.sb')[0]?.dataset.active || '') + '"]')[0];
  if (sbItem) { sbItem.classList.add('on'); const nav = $('.sb-nav')[0], sc = $('.sb-scroll')[0]; const over = sbItem.offsetTop + sbItem.offsetHeight + 60 - nav.offsetHeight; if (over > 0) gsap.set(sc, { y: -Math.min(over, sc.offsetHeight - nav.offsetHeight) }); }
  const bn = $('.bnav')[0]; if (bn) { const b = bn.querySelector('[data-k="' + bn.dataset.active + '"]'); if (b) b.classList.add('on'); }
  const api = {
    $, cam, cur, VIEW, pt,
    // cursor appears at native point (x,y)
    cursorIn(at, x, y) { gsap.set(cur, { x, y, opacity: 0 }); tl.to(cur, { opacity: 1, duration: 0.25 }, at); },
    cursorOut(at) { tl.to(cur, { opacity: 0, duration: 0.2 }, at); },
    // move the cursor to el and click it at time `at` (cursor + ring must be children of .cam)
    click(el, at, move = 0.7, dy = 0) {
      const p = pt(el, 0.5, 0.55); p.y += dy;
      tl.to(cur, { x: p.x, y: p.y, duration: move, ease: 'power3.inOut' }, at - move);
      tl.set(ring, { x: p.x + 4, y: p.y + 4 }, at);
      tl.fromTo(ring, { opacity: 0.9, scale: 0.3 }, { opacity: 0, scale: 1.4, duration: 0.45, ease: 'power2.out' }, at);
      tl.to(el, { scale: 0.96, duration: 0.09, yoyo: true, repeat: 1 }, at);
    },
    // camera push-in: brings el's (fx,fy) point to the (vx,vy) fraction of the visible window at `scale`
    focus(el, scale, at, dur = 1, { fx = 0.5, fy = 0.5, vx = 0.5, vy = 0.5, dy = 0, ease = 'power3.inOut', clamp = true } = {}) {
      const p = pt(el, fx, fy);
      // clamp so the app never slides out of the window (pass clamp:false to allow it)
      const cl = (v, lo) => clamp === false ? v : Math.min(0, Math.max(lo, v));
      const x = cl(VIEW.w * vx - p.x * scale, VIEW.w - cam.offsetWidth * scale);
      const y = cl(VIEW.h * vy - (p.y + dy) * scale, VIEW.h - cam.offsetHeight * scale);
      tl.to(cam, { scale, x, y, duration: dur, ease }, at);
    },
    reset(at, dur = 0.9) { tl.to(cam, { scale: S, x: 0, y: 0, duration: dur, ease: 'power3.inOut' }, at); },
    // standard entrance: window rises, kicker + first headline words stagger; other headlines hidden
    enter(at = 0) {
      tl.fromTo($('.win'), { y: 70, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: 'expo.out' }, at);
      tl.fromTo($('.cap .kicker'), { x: -20, opacity: 0 }, { x: 0, opacity: 1, duration: 0.5, ease: 'power3.out' }, at + 0.1);
      tl.fromTo($('.h-a > *'), { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.55, stagger: 0.05, ease: 'power3.out' }, at + 0.2);
      const rest = $('.h-b > *, .h-c > *'); if (rest.length) gsap.set(rest, { opacity: 0 });
    },
    // headline swap in place: swap('.h-a', '.h-b', t)
    swap(from, to, at) {
      tl.to($(from + ' > *'), { y: -30, opacity: 0, duration: 0.3, stagger: 0.025, ease: 'power2.in' }, at);
      tl.fromTo($(to + ' > *'), { y: 40, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, stagger: 0.05, ease: 'power3.out' }, at + 0.35);
    },
    kicker(text, at) { const k = $('.cap .kicker .kt')[0]; if (k) { tl.to(k, { opacity: 0, duration: 0.2 }, at); tl.call(() => { k.textContent = text; }, null, at + 0.2); tl.to(k, { opacity: 1, duration: 0.25 }, at + 0.22); } },
    exit(D) {
      tl.to($('.win'), { opacity: 0, y: -20, scale: 0.985, duration: 0.45, ease: 'power2.in' }, D - 0.5);
      tl.to($('.cap'), { opacity: 0, y: -20, duration: 0.4, ease: 'power2.in' }, D - 0.5);
    },
    // number count-up on el (integer or 1 decimal with comma), seek-safe
    count(el, to, at, dur = 0.9, { from = 0, dec = 0, pre = '', suf = '' } = {}) {
      const o = { v: from }; const f = (v) => pre + (dec ? v.toFixed(dec).replace('.', ',') : Math.round(v).toLocaleString('pt-BR')) + suf;
      el.textContent = f(from);
      tl.to(o, { v: to, duration: dur, ease: 'power2.out', onUpdate: () => { el.textContent = f(o.v); } }, at);
    },
    // typing reveal for a single-line text element
    type(el, at, dur = 0.8) { tl.fromTo(el, { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)', duration: dur, ease: 'none' }, at); },
  };
  return api;
};
