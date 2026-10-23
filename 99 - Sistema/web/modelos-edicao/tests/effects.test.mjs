import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import { effectCatalogHTML } from '../scripts/export_effects.mjs';

test('effect identifiers have one renderer and valid reference provenance', async () => {
  const root=new URL('../../../motion/effects/',import.meta.url);
  const catalog=JSON.parse(await readFile(new URL('catalog.json',root),'utf8'));
  const refs=JSON.parse(await readFile(new URL('references.json',root),'utf8'));
  const context={};vm.runInNewContext(await readFile(new URL('renderer.js',root),'utf8'),context);
  assert.deepEqual([...context.CortezEffects.ids].sort(),catalog.effects.map(e=>e.id).sort());
  for(const entry of catalog.effects){
    assert.ok(Array.isArray(entry.reference_ids),entry.code);
    assert.ok(entry.reference_ids.every(id=>refs.sources.some(s=>s.id===id)),entry.code);
  }
});

test('export works offline and excludes private research locations', async () => {
  const html=await effectCatalogHTML();
  assert.match(html,/id="catalog-data"/);
  assert.doesNotMatch(html,/\{\{(?:SITE_CSS|EFFECTS_CSS|CATALOG|REFERENCES|RENDERER|VIEW_MODULE|LOGO)\}\}/);
  const referenceBlock=html.match(/<script id="reference-data" type="application\/json">(.*?)<\/script>/s)[1];
  const references=JSON.parse(referenceBlock);
  assert.ok(references.sources.length>1);
  assert.doesNotMatch(referenceBlock,/local_path|\/Users\/|workspace:\/\//);
  assert.doesNotMatch(html,/Li o PDF local|PDF de referência/);
  assert.doesNotMatch(html,/<script[^>]+src=/);
  assert.doesNotMatch(html,/<iframe\b/i);
  assert.match(html,/prefers-reduced-motion/);
  assert.match(html,/Sincronize com as palavras da montagem final/);
});
