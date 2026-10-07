import { cp, mkdir, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const destination = path.join(root, 'dist');
const catalog = JSON.parse(await readFile(path.join(root, 'public/catalog.json'), 'utf8'));
const publication = JSON.parse(await readFile(path.join(root, 'publication.json'), 'utf8'));
const codes = new Set();
for (const format of catalog.formats) {
  if (publication.excluded_codes.includes(format.code)) throw Error('Um formato descartado não pode voltar à galeria.');
  if (!publication.formats.some(item => item.code === format.code)) throw Error('Formato não autorizado para publicação.');
  if (!/^F\d{2,}$/.test(format.code) || codes.has(format.code)) throw Error('Código de formato inválido/duplicado.');
  codes.add(format.code);
  for (const key of ['poster', 'video']) {
   for (const sample of [format,...(format.examples || []),...(format.referenceFrames || [])]) {
    const value = sample[key];
    if (!value) continue;
    if (!/^assets\/[a-zA-Z0-9_./-]+$/.test(value) || value.includes('..')) throw Error('Caminho de mídia inválido.');
    await stat(path.join(root, 'public', value));
   }
  }
}
if (catalog.identities.some(identity => !/^ID\d{2,}$/.test(identity.code))) throw Error('Identidade inválida.');
await rm(destination, { recursive: true, force: true });
await mkdir(destination, { recursive: true });
await cp(path.join(root, 'public/catalog.json'), path.join(destination, 'catalog.json'));
await cp(path.join(root, 'public/assets/fonts'), path.join(destination, 'assets/fonts'), { recursive: true });
for (const format of catalog.formats) {
 for (const sample of [format,...(format.examples || []),...(format.referenceFrames || [])]) {
  for (const key of ['poster', 'video']) {
    if (!sample[key]) continue;
    const output = path.join(destination, sample[key]);
    await mkdir(path.dirname(output), { recursive: true });
    await cp(path.join(root, 'public', sample[key]), output);
  }
 }
}
await cp(path.join(root, 'src'), destination, { recursive: true });
const html = await readFile(path.join(root, 'src/index.html'), 'utf8');
await writeFile(path.join(destination, 'index.html'), html);
console.log(`Build concluído: ${catalog.formats.length} formatos e ${catalog.identities.length} identidades. Apenas src/ e public/ publicados.`);
