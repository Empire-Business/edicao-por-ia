import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createEffectsView } from '../src/effects.js';
import { effectNativeAssets, publicEffectData } from '../scripts/export_effects.mjs';

class FakeMain {
  constructor() {
    this.innerHTML = '';
    this.listeners = new Map();
    this.canvas = {
      dataset: { fxCanvas: 'FX01' },
      isConnected: true,
      closest: () => null,
      width: 0,
      height: 0
    };
  }
  addEventListener(type, listener) { this.listeners.set(type, listener); }
  removeEventListener(type, listener) {
    if (this.listeners.get(type) === listener) this.listeners.delete(type);
  }
  contains() { return true; }
  querySelectorAll(selector) { return selector === '[data-fx-canvas]' ? [this.canvas] : []; }
  querySelector() { return null; }
}

function withBrowserStubs(run) {
  const previous = {
    window: globalThis.window,
    document: globalThis.document,
    IntersectionObserver: globalThis.IntersectionObserver,
    requestAnimationFrame: globalThis.requestAnimationFrame,
    cancelAnimationFrame: globalThis.cancelAnimationFrame
  };
  const observers = [];
  const frames = new Map();
  const cancelled = [];
  let nextFrame = 1;
  globalThis.window = { CortezEffects: { render() {} } };
  globalThis.IntersectionObserver = class {
    constructor(callback, options) { this.callback = callback; this.options = options; this.targets = []; this.disconnected = false; observers.push(this); }
    observe(target) { this.targets.push(target); }
    disconnect() { this.disconnected = true; }
  };
  globalThis.window.IntersectionObserver = globalThis.IntersectionObserver;
  globalThis.document = { hidden: false, listeners: new Map(),
    addEventListener(type, listener) { this.listeners.set(type, listener); },
    removeEventListener(type, listener) { if (this.listeners.get(type) === listener) this.listeners.delete(type); }
  };
  globalThis.requestAnimationFrame = callback => { const id = nextFrame++; frames.set(id, callback); return id; };
  globalThis.cancelAnimationFrame = id => { cancelled.push(id); frames.delete(id); };
  try { return run({ observers, frames, cancelled }); }
  finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) delete globalThis[key]; else globalThis[key] = value;
    }
  }
}

const reducedMotion = { matches: true, addEventListener() {}, removeEventListener() {} };
const storage = { getItem: () => '[]', setItem() {} };

test('FX export contains portable public assets and strips local research metadata', async () => {
  const assets = await effectNativeAssets();
  assert.ok(assets.library.effects.length >= 1);
  assert.match(assets.renderer, /CortezEffects/);
  assert.match(assets.dataModule, /export const library/);
  assert.match(assets.dataModule, /export const references/);

  const allowedReferenceFields = ['author', 'id', 'inspection', 'kind', 'notes', 'observed', 'title', 'url'];
  for (const source of assets.references.sources) {
    assert.deepEqual(Object.keys(source).sort(), allowedReferenceFields);
    assert.ok(source.url === undefined || /^https?:\/\//.test(source.url));
  }
  assert.doesNotMatch(JSON.stringify(assets.references), /local_path|license|\/Users\/|workspace:\/\//i);
  const publicIds = new Set(assets.references.sources.map(source => source.id));
  for (const effect of assets.library.effects) {
    assert.notEqual(effect.origin, 'pdf');
    assert.ok(effect.reference_ids.every(id => publicIds.has(id)), effect.code);
  }
  const canonical = JSON.parse(await readFile(new URL('../../../motion/effects/references.json', import.meta.url), 'utf8'));
  for (const source of canonical.sources.filter(source => source.local_path || source.visibility === 'internal')) {
    for (const field of ['id','title','author','observed','notes']) {
      if (source[field]) assert.ok(!assets.dataModule.includes(source[field]), `Internal source ${field} leaked`);
    }
  }
});

test('private provenance never enters publication even when supplied to the exporter', () => {
  const result = publicEffectData({ schema_version: 1, effects: [{ code: 'FX01', origin: 'pdf', reference_ids: ['internal-note', 'public-source'] }] },
    { schema_version: 1, sources: [
      { id: 'internal-note', visibility: 'internal', title: 'Internal title', url: 'https://example.org/internal', observed: 'Private observation' },
      { id: 'local-file', local_path: 'local/research.txt', title: 'Local material' },
      { id: 'public-source', title: 'Public source', url: 'https://example.org/reference', local_secret: 'not exported' }
    ] });
  assert.deepEqual(result.library.effects[0].reference_ids, ['public-source']);
  assert.equal(result.library.effects[0].origin, undefined);
  assert.deepEqual(result.references.sources.map(source => source.id), ['public-source']);
  assert.doesNotMatch(JSON.stringify(result), /Internal title|Private observation|internal-note|local-file|Local material|local_secret|not exported/);
});

test('FX gallery and detail render into the provided native main and keep F/ID distinct', () => withBrowserStubs(() => {
  const main = new FakeMain();
  const library = {
    effects: [{
      code: 'FX01', id: 'counter', name: 'Contador', category: 'Dados', description: 'Destaca um número.',
      use_when: 'Quando a fala apresenta um resultado.', caution: 'Confira a sincronização.',
      demo: { duration: 3, text: '42' }, status_label: 'Estudo', reference_ids: []
    }]
  };
  const view = createEffectsView({ main, library, storage, reducedMotion, references: {}, icon: () => '' });
  view.gallery();
  const gallery = main.innerHTML;
  assert.match(gallery, /aria-label="Biblioteca de efeitos"/);
  assert.match(gallery, /data-fx-canvas="FX01"/);
  assert.match(gallery, /href="#efeito=FX01"/);
  assert.doesNotMatch(gallery, /<iframe\b/i);
  assert.doesNotMatch(gallery, /<main\b/i);

  view.detail('FX01');
  const detail = main.innerHTML;
  assert.match(detail, /class="detail-layout fx-detail-layout"/);
  assert.match(detail, /Fontes e referências/);
  assert.match(detail, /identidade visual/i);
  assert.doesNotMatch(detail, /<iframe\b/i);
  assert.doesNotMatch(detail, /\bF\d{2,}\s*\+\s*ID\d{2,}\b/);
  view.destroy();

  const selectedView = createEffectsView({ main, library, storage, reducedMotion, icon: () => '',
    getPromptContext: () => ({ format: 'F07', identity: 'ID02' }) });
  selectedView.detail('FX01');
  assert.match(main.innerHTML, /Formato de edição: F07/);
  assert.match(main.innerHTML, /Identidade visual: ID02/);
  assert.match(main.innerHTML, /Preserve essas escolhas/);
  selectedView.destroy();
}));

test('FX view disconnects its observer, cancels pending animation and removes delegated listeners', () => withBrowserStubs(({ observers, frames, cancelled }) => {
  const main = new FakeMain();
  const library = { effects: [{ code: 'FX01', id: 'counter', name: 'Contador', category: 'Dados', description: 'Número.', demo: { duration: 3 } }] };
  const view = createEffectsView({ main, library, storage, reducedMotion: { matches: false }, references: {}, icon: () => '' });
  view.gallery();

  assert.equal(main.listeners.size, 2);
  assert.equal(observers.length, 1);
  assert.deepEqual(observers[0].targets, [main.canvas]);
  observers[0].callback([{ target: main.canvas, isIntersecting: true }]);
  assert.equal(frames.size, 1);

  view.destroy();
  assert.equal(observers[0].disconnected, true);
  assert.equal(frames.size, 0);
  assert.deepEqual(cancelled, [1]);
  assert.equal(main.listeners.size, 0);
  // The router reuses this instance after leaving and returning to Efeitos.
  view.gallery();
  assert.equal(main.listeners.size, 2);
  assert.equal(observers.length, 2);
  observers[1].callback([{ target: main.canvas, isIntersecting: true }]);
  assert.equal(frames.size, 1);
  view.destroy();
}));

test('native panel applies the site stylesheet to the same main route used by models', async () => {
  const [html, app, styles, effectsCss] = await Promise.all([
    readFile(new URL('../src/index.html', import.meta.url), 'utf8'),
    readFile(new URL('../src/app.js', import.meta.url), 'utf8'),
    readFile(new URL('../src/styles.css', import.meta.url), 'utf8'),
    readFile(new URL('../src/effects.css', import.meta.url), 'utf8')
  ]);
  assert.match(html, /<main id="main"/);
  assert.match(html, /href="styles\.css"/);
  assert.match(html, /href="effects\.css"/);
  assert.match(html, /href="#modelos"/);
  assert.match(html, /href="#efeitos"/);
  assert.match(app, /createEffectsView\(\{\s*main,/);
  assert.match(app, /effectsView\.gallery\(\)/);
  assert.match(app, /effectsView\.detail\(/);
  assert.match(styles, /--accent:/);
  assert.match(styles, /--surface:/);
  assert.match(effectsCss, /var\(--accent\)/);
  assert.match(effectsCss, /var\(--line\)/);
  assert.doesNotMatch(effectsCss, /:root\s*\{/);
});
