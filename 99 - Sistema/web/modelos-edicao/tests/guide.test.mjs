import test from 'node:test';
import assert from 'node:assert/strict';
import { readdir } from 'node:fs/promises';
import { functions, groups, internalWorkflows, guideUpdated } from '../src/guide.js';

const workflowsDir = new URL('../../../workflows/', import.meta.url);

test('every user-facing workflow is documented in the panel', async () => {
  const workflows = (await readdir(workflowsDir)).filter(name => name.endsWith('.md'));
  const documented = new Set(functions.flatMap(fn => fn.workflows));
  const missing = workflows.filter(name => !documented.has(name) && !internalWorkflows.includes(name));
  assert.deepEqual(missing, [], 'Documente estes workflows em src/guide.js ou marque-os como internos.');
});

test('functions are complete, unique and grouped', () => {
  assert.match(guideUpdated, /^\d{4}-\d{2}-\d{2}$/);
  const ids = functions.map(fn => fn.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const fn of functions) {
    assert.ok(groups.some(group => group.id === fn.group), fn.id);
    for (const key of ['title', 'what', 'say', 'prompt']) assert.ok(fn[key]?.trim(), `${fn.id}.${key}`);
    // O painel não entrega comandos de terminal ao usuário.
    assert.doesNotMatch(`${fn.say} ${fn.prompt}`, /python|factory\.py|\.py\b|--[a-z]/, fn.id);
  }
  assert.ok(functions.find(fn => fn.id === 'variacoes')?.prompt.includes('variações para teste'));
});

test('the Cortez panel publishes the exact user tutorial and installer, with a safe contribution prompt', async () => {
  const { tutorials, installerPdf } = await import('../src/guide.js');
  assert.equal(installerPdf, 'instalar.pdf');
  const usage = tutorials.find(item => item.id === 'como-usar');
  assert.equal(usage.videoId, '1238030963');
  assert.equal(usage.hash, '1c867e709c');
  const contribution = functions.find(item => item.id === 'contribuir');
  assert.match(contribution.what, /proposta de mudança/);
  assert.match(contribution.prompt, /PR em rascunho/);
  assert.match(contribution.prompt, /Não envie meus vídeos de trabalho, memória, chaves ou configurações/);
  assert.match(contribution.prompt, /Não altere a versão oficial/);
  assert.deepEqual(contribution.workflows, ['CONTRIBUTE_PULL_REQUEST.md']);
  const { readFile, stat } = await import('node:fs/promises');
  const html = await readFile(new URL('../src/index.html', import.meta.url),'utf8');
  const app = await readFile(new URL('../src/app.js', import.meta.url),'utf8');
  assert.match(html, /Painel do Cortez/);
  assert.match(app, /id="tutoriais"/);
  assert.match(app, /contribute-title/);
  assert.match(app, /href="#funcao=contribuir"/);
  assert.doesNotMatch(app, /autoplay=1/);
  for (const asset of ['logo-lockup.svg','favicon.svg','apresentacao.webp']) {
    assert.ok((await stat(new URL(`../public/assets/brand/cortez/${asset}`,import.meta.url))).size > 0);
  }
});
