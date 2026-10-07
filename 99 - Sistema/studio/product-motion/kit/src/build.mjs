// Builds two proportion variants (16:9 and 9:16) from one scene source.
// usage: node src/build.mjs            -> build/h (1920x1080) and build/v (1080x1920)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { icon } from './icons.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const job = path.resolve(here, '..');
const cfg = JSON.parse(fs.readFileSync(path.join(here, 'scenes.json'), 'utf8'));
const proportions = cfg.proportions || cfg.formats; // `formats` is the legacy key in existing jobs.
if (!proportions) throw new Error('scenes.json needs proportions (legacy formats is also accepted)');
// SCENES=a,b builds only those scenes (for isolated previews); OUT=dir changes the output folder.
if (process.env.SCENES) { const keep = process.env.SCENES.split(','); cfg.scenes = cfg.scenes.filter((s) => keep.includes(s.id)); }
const OUT = process.env.OUT || 'build';
const brand = JSON.parse(fs.readFileSync(path.join(here, 'brand.json'), 'utf8'));
const kebab = (s) => s.replace(/[A-Z]/g, (c) => '-' + c.toLowerCase());
// brand.json -> :root custom properties + @font-face (files in assets/fonts named <slug>-<weight>-latin[-ext].woff2)
function brandCss() {
  const vars = Object.entries(brand.colors).map(([k, v]) => `  --${kebab(k)}: ${v};`).join('\n');
  const slug = brand.font.slug || brand.font.family.toLowerCase().replace(/\s+/g, '-');
  const faces = [];
  for (const face of brand.font.faces || []) {
    faces.push(`@font-face { font-family: "${face.family}"; font-weight: ${face.weight}; src: url("${face.src}") format("${face.format}"); }`);
  }
  for (const w of brand.font.weights) {
    faces.push(`@font-face { font-family: "${brand.font.family}"; font-weight: ${w}; src: url("assets/fonts/${slug}-${w}-latin.woff2") format("woff2"); }`);
    if (fs.existsSync(path.join(job, 'assets', 'fonts', `${slug}-${w}-latin-ext.woff2`)))
      faces.push(`@font-face { font-family: "${brand.font.family}"; font-weight: ${w}; src: url("assets/fonts/${slug}-${w}-latin-ext.woff2") format("woff2"); unicode-range: U+0100-024F; }`);
  }
  return `${faces.join('\n')}\n:root {\n${vars}\n  --ease-ui: cubic-bezier(0, 0, 0.2, 1);\n  --font: "${brand.font.family}", -apple-system, "Segoe UI", Arial, sans-serif;\n}`;
}
const typeCss = brand.typography ? `:root { --font-body: "${brand.typography.body}", sans-serif; --font-labels: "${brand.typography.labels}", monospace; } body { font-family: var(--font-body); } .headline, .line, .pg-title { font-family: "${brand.typography.headline}", sans-serif; } .lbl, .kicker { font-family: var(--font-labels); }` : '';
const baseCss = fs.readFileSync(path.join(here, 'base.css'), 'utf8').replace('/*__BRAND__*/', brandCss()) + typeCss;
const macros = {};
for (const f of fs.readdirSync(path.join(here, 'partials'))) {
  macros[path.basename(f, '.html')] = fs.readFileSync(path.join(here, 'partials', f), 'utf8');
}

function expand(src, ctx, depth = 0) {
  if (depth > 5) throw new Error('macro recursion');
  let out = src
    .replace(/\{\{icon:([a-z0-9-]+)(?::(\d+))?(?::([a-z0-9 -]+))?\}\}/g, (_, n, s, c) => icon(n, s ? +s : 20, c || ''))
    .replace(/\{\{partial:([a-z0-9-]+)(?::([^}]*))?\}\}/g, (_, n, arg) => {
      if (n === 'logo' && brand.logoEnabled !== true) return '';
      if (!(n in macros)) throw new Error(`partial not found: ${n}`);
      return expand(macros[n].replaceAll('{{ARG}}', arg || ''), ctx, depth + 1);
    });
  for (const [k, v] of Object.entries(ctx)) out = out.replaceAll(`{{${k}}}`, String(v));
  const left = out.match(/\{\{[^}]+\}\}/);
  if (left) throw new Error(`unexpanded token ${left[0]}`);
  return out;
}

function copyDir(a, b) {
  fs.mkdirSync(b, { recursive: true });
  for (const e of fs.readdirSync(a, { withFileTypes: true })) {
    const s = path.join(a, e.name), d = path.join(b, e.name);
    if (e.isDirectory()) copyDir(s, d); else fs.copyFileSync(s, d);
  }
}

for (const variant of ['h', 'v']) {
  const { W, H } = proportions[variant];
  const V = variant === 'v';
  const out = path.join(job, OUT, variant);
  fs.rmSync(path.join(out, 'compositions'), { recursive: true, force: true });
  fs.mkdirSync(path.join(out, 'compositions'), { recursive: true });
  copyDir(path.join(job, 'assets', 'fonts'), path.join(out, 'assets', 'fonts'));
  copyDir(path.join(job, 'assets', 'vendor'), path.join(out, 'assets', 'vendor'));
  if (brand.logoEnabled === true) copyDir(path.join(job, 'assets', 'brand'), path.join(out, 'assets', 'brand'));
  else fs.rmSync(path.join(out, 'assets', 'brand'), { recursive: true, force: true });
  copyDir(path.join(job, 'assets', 'img'), path.join(out, 'assets', 'img'));
  copyDir(path.join(job, 'assets', 'audio'), path.join(out, 'assets', 'audio'));

  let t = 0;
  const slots = [];
  cfg.scenes.forEach((sc, i) => {
    const start = +(t).toFixed(3);
    const ctx = { BRAND: brand.name, W, H, V: V ? 'true' : 'false', FMT: V ? 'fmt-v' : 'fmt-h', DUR: sc.dur, ID: sc.id };
    const body = expand(fs.readFileSync(path.join(here, 'scenes', `${sc.id}.html`), 'utf8'), ctx);
    const html = `<template id="${sc.id}-template">\n<div data-composition-id="${sc.id}" data-width="${W}" data-height="${H}" data-duration="${sc.dur}" class="scene ${sc.cls || ""}">\n${body}\n</div>\n</template>\n`;
    fs.writeFileSync(path.join(out, 'compositions', `${sc.id}.html`), html);
    slots.push(`    <div id="el-${sc.id}" data-composition-id="${sc.id}" data-composition-src="compositions/${sc.id}.html" data-start="${start}" data-duration="${sc.dur}" data-track-index="${1 + (i % 2)}"></div>`);
    t += sc.dur - (sc.overlap ?? cfg.overlap);
  });
  const total = +(t + cfg.overlap).toFixed(3);
  const audio = [];
  if (cfg.music && !process.env.SCENES) audio.push(`    <audio id="bgm" src="${cfg.music.src}" data-start="0" data-duration="${total}" data-track-index="10" data-volume="${cfg.music.volume}"></audio>`);
  (process.env.SCENES ? [] : cfg.sfx || []).forEach((s, i) => {
    audio.push(`    <audio id="sfx-${i}" src="${s.src}" data-start="${s.at}" data-duration="${s.dur || 1.5}" data-track-index="${11 + (i % 4)}" data-volume="${s.volume ?? 0.5}"></audio>`);
  });

  const index = `<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${W}, height=${H}" />
    <title>${brand.name} — motion ${V ? '9:16' : '16:9'}</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
${baseCss}
    </style>
    <script>
      // (name kept for scene compatibility) Layout measurements in scene scripts need the scene laid out even while its clip is inactive.
      window.__omnxShow = (el) => {
        const changed = [];
        for (let e = el; e && e !== document.documentElement; e = e.parentElement) {
          const cs = getComputedStyle(e);
          if (cs.display === 'none') { changed.push([e, 'display', e.style.display]); e.style.display = 'block'; }
        }
        return () => changed.forEach(([e, k, v]) => { e.style[k] = v; });
      };
${fs.existsSync(path.join(here, 'lib.js')) ? fs.readFileSync(path.join(here, 'lib.js'), 'utf8') : ''}
    </script>
  </head>
  <body>
    <div id="root" class="${V ? 'fmt-v' : 'fmt-h'}" data-composition-id="root" data-start="0" data-width="${W}" data-height="${H}" data-duration="${total}">
${slots.join('\n')}
${audio.join('\n')}
    </div>
    <script>
      window.__timelines["root"] = gsap.timeline({ paused: true });
    </script>
  </body>
</html>
`;
  fs.writeFileSync(path.join(out, 'index.html'), index);
  fs.writeFileSync(path.join(out, 'hyperframes.json'), JSON.stringify({ $schema: 'https://hyperframes.heygen.com/schema/hyperframes.json', paths: { assets: 'assets' }, media: { autoProxy: true } }, null, 2));
  fs.writeFileSync(path.join(out, 'meta.json'), JSON.stringify({ id: `${brand.jobId}-${variant}`, name: `${brand.jobId}-${variant}` }, null, 2));
  console.log(`${variant}: ${W}x${H}, ${cfg.scenes.length} scenes, ${total}s`);
}
