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
