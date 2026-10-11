import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { buildPrompt, buildStarterPrompt, filterFormats, readStorage, writeStorage, selectionFromHash } from '../src/selection.js';

const catalog = JSON.parse(await readFile(new URL('../public/catalog.json', import.meta.url), 'utf8'));
const publication = JSON.parse(await readFile(new URL('../publication.json', import.meta.url), 'utf8'));

test('discarded formats cannot be offered again; F13 is present and F11 is consolidated', () => {
  assert.deepEqual(publication.excluded_codes.sort(), ['F18']);
  for (const uid of ['factory.f09','factory.f11','factory.f17']) assert.ok(publication.excluded_uids.includes(uid));
  assert.ok(publication.excluded_uids.includes('factory.f02'));
  assert.ok(publication.excluded_uids.includes('factory.f03'));
  assert.equal(catalog.formats.some(format => publication.excluded_codes.includes(format.code)), false);
  assert.equal(catalog.formats.some(format => format.code === 'F13'), true);
  assert.deepEqual(catalog.formats.map(format => format.code).sort(), publication.formats.map(format => format.code).sort());
});

test('search accepts accents and code; categories and favorites intersect', () => {
  assert.equal(filterFormats(catalog.formats, { query: 'documentario' })[0].code, 'F12');
  assert.equal(filterFormats(catalog.formats, { query: 'F13' })[0].name, 'Dados Dark');
  assert.equal(filterFormats(catalog.formats, { query: 'F02' })[0].name, 'Talking Head');
  assert.equal(filterFormats(catalog.formats, { query: 'F03' })[0].name, 'Dark com B-roll');
  assert.deepEqual(filterFormats(catalog.formats, { category: 'products', favoritesOnly: true, favorites: ['F01', 'F10'] }).map(format => format.code), ['F10']);
});

test('a copyable request requires explicit format and identity and preserves local rules', () => {
  assert.throws(() => buildPrompt(catalog.formats[0], null), /Escolha/);
  assert.throws(() => buildPrompt(null, catalog.identities[0]), /Escolha/);
  const prompt = buildPrompt(catalog.formats[0], catalog.identities[2], '16:9');
  assert.match(prompt, /F01 \(WhatsApp Narrado\)/);
  assert.match(prompt, /ID03 \(Azul\)/);
  assert.match(prompt, /16:9/);
  assert.match(prompt, /Preserve os originais/);
  assert.match(prompt, /confira|Confira/);
  assert.match(prompt, /Logotipos somente se eu pedir/);
  assert.throws(() => buildPrompt(catalog.formats[0], catalog.identities[0], 'invalid'), /Tamanho/);
});

test('shared links do not assign a default identity or restore a retired format', () => {
  const formatOnly = selectionFromHash('#modelo=F01', catalog);
  assert.equal(formatOnly.identity, null);
  assert.equal(selectionFromHash('#modelo=F18&id=ID03', catalog).format, null);
  assert.equal(selectionFromHash('#modelo=F09', catalog).format.pattern, 'f09-personagem-v1');
  assert.equal(selectionFromHash('#modelo=F11', catalog).format.pattern, 'f11-narracao-ilustrada-v1');
  assert.equal(selectionFromHash('#modelo=F17', catalog).format.pattern, 'f17-colunas-v1');
  assert.equal(selectionFromHash('#modelo=F03', catalog).format.pattern, 'f03-dark-com-broll-v1');
  assert.equal(selectionFromHash('#modelo=F02', catalog).format.pattern, 'f02-talking-head-v1');
  assert.equal(selectionFromHash('#modelo=F13&id=ID99', catalog).identity, null);
  const pair = selectionFromHash('#modelo=F13&id=ID06&tamanho=16%3A9', catalog);
  assert.equal(pair.format.code, 'F13'); assert.equal(pair.identity.code, 'ID06'); assert.equal(pair.aspect, '16:9');
});

test('storage failures and invalid values cannot break the library', () => {
  assert.deepEqual(readStorage({ getItem: () => '{broken' }, 'k', []), []);
  assert.equal(readStorage({ getItem: () => '"true"' }, 'k', false, value => typeof value === 'boolean'), false);
  assert.equal(writeStorage({ setItem: () => { throw Error('denied'); } }, 'k', true), false);
});

test('public catalogue contains no private factory records or machine paths', () => {
  const text = JSON.stringify(catalog);
  for (const privateMarker of ['memory_store', 'legacy_stores', 'example_videos', 'jobs/', 'context/clients', '/Users/', '/Volumes/', 'drive_id', 'registration_receipt']) assert.equal(text.includes(privateMarker), false, privateMarker);
  assert.equal(catalog.identities.length, 8);
});

test('retired media is absent and references without video have honest evidence labels', async () => {
  const files = await readdir(new URL('../public/assets/videos/', import.meta.url));
  assert.equal(files.some(name => /^F0?2\./.test(name)), false);
  const data = catalog.formats.find(format => format.code === 'F13');
  assert.equal(data.evidenceLabel, 'Referência externa');
  assert.match(data.evidenceNote, /Não é um novo vídeo produzido pela fábrica/);
  for (const format of catalog.formats.filter(item => !item.video)) assert.notEqual(format.evidence, 'video');
});


test('descriptive search understands common words and camera constraints', () => {
  assert.equal(filterFormats(catalog.formats,{query:'mensagens'})[0].code,'F01');
  assert.equal(filterFormats(catalog.formats,{query:'zap'})[0].code,'F01');
  assert.equal(filterFormats(catalog.formats,{query:'whastapp'})[0].code,'F01');
  const voiceOnly=filterFormats(catalog.formats,{query:'eu nao quero aparecer'});
  assert.ok(voiceOnly.length>0 && voiceOnly.every(format=>!format.hasPersonOnScreen));
  assert.deepEqual(filterFormats(catalog.formats,{query:'pesquisa broll'}).map(format=>format.code),['F03','F16']);
  assert.equal(filterFormats(catalog.formats,{material:'telas',presence:'person'}).some(format=>format.code==='F08'),true);
  assert.ok(filterFormats(catalog.formats,{category:'presenter'}).every(format=>format.hasPersonOnScreen));
});

test('branding is never inherited; F05 specifically forbids the reference signature', () => {
  const prompt=buildPrompt(catalog.formats.find(format=>format.code==='F05'),catalog.identities[0]);
  assert.match(prompt,/não escrever EMPIRE/);
  assert.match(prompt,/Não acrescente nome de marca/);
});

test('the rich research model remains independent and the combined format keeps variations', () => {
  const research=catalog.formats.find(format=>format.code==='F16');
  assert.match(research.mechanism,/pesquisadas/);
  assert.match(research.steps.join(' '),/ScrapeCreators/);
  const combined=catalog.formats.find(format=>format.code==='F08');
  assert.equal(combined.name,'Pessoa + Tela');
  assert.equal(combined.examples.some(example=>example.id==='pessoa-midia'),false);
  assert.equal(combined.examples.some(example=>example.id==='conversas'),true);
});


test('homepage quick copy names the code and leaves required choices explicit', () => {
 const starter=buildStarterPrompt(catalog.formats.find(format=>format.code==='F14'));
 assert.match(starter,/F14 \(Lista em Tela\)/);
 assert.match(starter,/Identidade visual: ainda vou escolher/);
 assert.match(starter,/antes de iniciar a edição/);
 assert.equal(/ID[0-9]{2}/.test(starter),false);
});

test('withdrawn models and unsolicited examples cannot return through search or shared links', async () => {
 for (const code of ['F18']) {
  assert.equal(catalog.formats.some(format=>format.code===code),false);
  assert.equal(filterFormats(catalog.formats,{query:code}).length,0);
  assert.equal(selectionFromHash(`#modelo=${code}`,catalog).format,null);
 }
 for (const folder of ['videos','posters']) {
  const files=await readdir(new URL(`../public/assets/${folder}/`,import.meta.url));
  assert.equal(files.some(name=>/^F18(?:[.-])/.test(name)),false);
 }
});

test("numeric code order is stable for library, favorites and searches", () => {
 const shuffled=[catalog.formats.find(x=>x.code==="F16"),catalog.formats.find(x=>x.code==="F04"),catalog.formats.find(x=>x.code==="F01")];
 assert.deepEqual(filterFormats(shuffled).map(x=>x.code),["F01","F04","F16"]);
 assert.deepEqual(filterFormats(shuffled,{favoritesOnly:true,favorites:["F16","F01"]}).map(x=>x.code),["F01","F16"]);
 assert.deepEqual(catalog.formats.map(x=>x.code),["F01","F02","F03","F04","F05","F06","F07","F08","F09","F10","F11","F12","F13","F14","F15","F16","F17"]);
});

test('the authorized new F02 uses its actual full example and a fresh media generation', () => {
 const item=catalog.formats.find(f=>f.code==='F02');
 assert.equal(item.name,'Talking Head');
 assert.equal(item.duration,185);
 assert.equal(item.evidenceLabel,'Referência externa');
 assert.match(item.video,/F02-talking-head-20261007\.mp4$/);
 assert.equal(item.referenceFrames.length,3);
 assert.notEqual(publication.formats.find(f=>f.code==='F02').uid,'factory.f02');
 assert.equal(filterFormats(catalog.formats,{query:'talking head'})[0].code,'F02');
});
