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
  for (const sample of [format,...(format.examples || [])]) {
    if (sample.vimeo && (!/^\d{1,15}$/.test(sample.vimeo.id) || sample.vimeo.status !== 'complete' || (sample.vimeo.hash && !/^[a-zA-Z0-9]{1,64}$/.test(sample.vimeo.hash)))) throw Error('Referência Vimeo inválida ou ainda em processamento.');
  }
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
const publishedVideoBytes = (await Promise.all(catalog.formats.flatMap(format => [format,...(format.examples || [])]).filter(sample=>sample.video).map(sample=>stat(path.join(root,'public',sample.video))))).reduce((sum,item)=>sum+item.size,0);
if (publishedVideoBytes > 128*1024*1024) throw Error('Vídeos locais acima do limite do painel; publicar referências no Vimeo antes.');
console.log(`Build concluído: ${catalog.formats.length} formatos e ${catalog.identities.length} identidades. Apenas src/ e public/ publicados.`);
