# Scene authoring guide — OMNX Sell motion

Reference scenes (read both before writing): `src/scenes/s01-intro.html`, `src/scenes/s05-room.html`.

## Files
- One file per scene: `src/scenes/<id>.html` (style + markup + script, NO <template> — build wraps it).
- Tokens expanded at build: `{{ID}}`, `{{DUR}}`, `{{V}}` (true/false), `{{icon:name[:size]}}` (see `src/icons.mjs`; you MAY add missing Lucide icons there, append-only, never change existing ones), `{{partial:name[:arg]}}` (`src/partials/`: `sidebar`, `logo:<unique-suffix>`, `cursor`).
- Do NOT edit `src/base.css`, `src/build.mjs`, `src/scenes.json` or other agents' scenes. If you need a shared style, copy it scoped into your scene.
- Build only your scenes: `SCENES=s02-shell,s03-agenda OUT=build-<you> node src/build.mjs` (Node 24: `export PATH=~/.nvm/versions/node/v24.15.0/bin:$PATH`).
- Check: `npx hyperframes@0.8.92 check build-<you>/h` (and `/v`). Fix all lint errors and text_occluded/overflow errors that are real.
- Snapshot: `npx hyperframes@0.8.92 snapshot build-<you>/h --at t1,t2,... --no-end --describe false -o qa/<you>-h` — ALWAYS `--describe false` (no uploads). Look at frames in both formats and iterate until it looks premium.

## Hard rules (learned)
- Scope every CSS rule: `[data-composition-id="<id>"] .x {}`. Vertical overrides: `.fmt-v [data-composition-id="<id>"] .x {}` — NEVER the compound form `[data-composition-id="<id>"].fmt-v`, it doesn't match.
- Script pattern: IIFE; `const all=document.querySelectorAll('[data-composition-id="{{ID}}"]'); const root=all[all.length-1]; const $=gsap.utils.selector(root);` one `gsap.timeline({paused:true})`, register at end `window.__timelines["{{ID}}"]=tl`.
- Never tween left/top/width/height (lint `gsap_non_transform_motion`). Use x/y/scale/scaleX/opacity/clipPath/filter. Bars: `scaleX` with `transform-origin:0 50%` on a block element with real width.
- No negative z-index, no `repeat:-1` (finite repeat), no Date/random. Text changes via `tl.call` or onUpdate from a tweened object (seek-safe).
- `data-layout-allow-overflow` on intentionally bleeding decoratives (paper-grid, .win, .cam).
- No `<br>` in body text.

## Frame system
- Background: `<div class="paper"></div><div class="paper-grid" data-layout-allow-overflow></div>`.
- Caption `.cap`: `.kicker` (with `<i class="dot"></i>`) + `.hstack` holding 1–2 `.headline` (swap in place). Headline in 16:9 must fit ONE line (≈ 55 characters max at 50px, 1728px wide). Use `<em>` for the gold highlight. Words wrapped in spans/em for stagger.
- Window `.win` (light) — 16:9: x 96..1824, top 236, bleeds off bottom. 9:16: x 40..1040, top 440, bleeds bottom. Put the UI in `.cam` (transform-origin 0 0) and move the camera with GSAP (push-ins to the element being explained).
- 16:9 native canvas: author app screens at 1440px wide (sidebar 240 + main) and set cam scale 1728/1440 = 1.2. Effective body text should be ≥ 16px on screen.
- 9:16: do NOT just shrink the desktop. Re-arrange: hide sidebar, stack cards vertically, scale content so effective text ≥ 26px (cam scale ~1.6–2 over a ~560px-wide native column), or show one focused panel at a time with camera moves.
- Entrance (first 0.6s): window rises/fades in (y 60→0, opacity), kicker + headline words stagger. Exit (last 0.5s): `.cam` / `.win` fade/scale out and `.cap` fades up. Scenes overlap 0.4s (crossfade).
- Motion vocabulary: staggered build of rows/cards, number count-ups (tabular-nums), bars growing, typing/revealing text (clipPath), tab switches, cursor moving + click ring, highlighted card lifting (scale 1.04 + gold glow `0 0 0 1px rgba(138,100,16,.1), 0 18px 40px -12px rgba(138,100,16,.35)`), camera push-ins. Ease: expo.out / power3.out; nothing bouncy except small badges. Every scene must MOVE continuously — never a static screenshot hold longer than ~1s.

## Fidelity
- Recreate the real UI from the repo `/Volumes/bguzelassd/05-desenvolvimento/omnx-sell` (open the JSX of your screens for exact labels/layout) and the reference screenshots in `assets/refs/` (2–7.png, sell-*.png). Portuguese strings exactly as in the UI. Light theme: paper `#fbfaf7`, cards white with `#ebe7de` hairline, radius 12, gold `#8a6410`, brand-10 `#fdf6e4`, Poppins.
- Sample data: coherent and fictitious (Nova Vertex, Marina Costa closer, Rafael Nunes lead, Hubbi Parts / Yuri Soares da Silva, Acelerador de Audiência workspace) — never invent product features that don't exist in the code.
