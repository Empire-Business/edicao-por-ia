import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const engine = fileURLToPath(new URL('../../../', import.meta.url));
const panel = path.join(engine, 'web/modelos-edicao');
const effects = path.join(engine, 'motion/effects');
const jsonForHTML = value => JSON.stringify(value).replace(/</g, '\\u003c').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');
const safeScript = source => source.replace(/<\/script/gi, '<\\/script');

export async function effectNativeAssets() {
  const [renderer, rawLibrary, rawReferences] = await Promise.all([
    readFile(path.join(effects, 'renderer.js'), 'utf8'),
    readFile(path.join(effects, 'catalog.json'), 'utf8'),
    readFile(path.join(effects, 'references.json'), 'utf8')
  ]);
  const { library, references } = publicEffectData(JSON.parse(rawLibrary), JSON.parse(rawReferences));
  return { library, references, renderer,
    dataModule: `export const library = ${jsonForHTML(library)};\nexport const references = ${jsonForHTML(references)};\n` };
}

export function publicEffectData(privateLibrary, privateReferences) {
  if (privateLibrary.schema_version !== 1 || privateReferences.schema_version !== 1) throw Error('Catálogo de efeitos incompatível.');
  // References without a public link and explicitly internal sources stay out of every UI export.
  const publicSources = privateReferences.sources.filter(source => {
    if (source.visibility === 'internal' || source.local_path) return false;
    try { return ['http:', 'https:'].includes(new URL(source.url).protocol); } catch { return false; }
  });
  const publicIds = new Set(publicSources.map(source => source.id));
  const references = { schema_version: 1, sources: publicSources.map(({ id, title, url, author, kind, observed, inspection, notes }) => ({ id, title, url, author, kind, observed, inspection, notes })) };
  const library = { ...privateLibrary, effects: privateLibrary.effects.map(({ origin, reference_ids, ...effect }) => ({
    ...effect, ...(origin && origin !== 'pdf' ? { origin } : {}),
    reference_ids: (reference_ids || []).filter(id => publicIds.has(id))
  })) };
  return { library, references };
}

async function offlineSiteCSS(css) {
  const paths = [...new Set([...css.matchAll(/url\(['"]?(assets\/fonts\/[^)'"\s]+)['"]?\)/g)].map(match => match[1]))];
  const fonts = await Promise.all(paths.map(async name => {
    const bytes = await readFile(path.join(panel, 'public', name));
    const mime = name.endsWith('.woff2') ? 'font/woff2' : 'font/ttf';
    return [name, `data:${mime};base64,${bytes.toString('base64')}`];
  }));
  const lookup = new Map(fonts);
  return css.replace(/url\(['"]?(assets\/fonts\/[^)'"\s]+)['"]?\)/g, (_, name) => `url('${lookup.get(name)}')`);
}

export async function effectCatalogHTML() {
  const [assets, template, siteCSS, effectsCSS, viewSource, iconsSource, logo] = await Promise.all([
    effectNativeAssets(),
    readFile(path.join(effects, 'catalog.template.html'), 'utf8'),
    readFile(path.join(panel, 'src/styles.css'), 'utf8'),
    readFile(path.join(panel, 'src/effects.css'), 'utf8'),
    readFile(path.join(panel, 'src/effects.js'), 'utf8'),
    readFile(path.join(panel, 'src/icons.js'), 'utf8'),
    readFile(path.join(panel, 'public/assets/brand/cortez/logo-lockup.svg'))
  ]);
  const standaloneModule = `${iconsSource}\n${viewSource}`.replace(/^export\s+(?=(?:function|const|let|class)\b)/gm, '');
  if (/^import\s/m.test(standaloneModule)) throw Error('O módulo compartilhado de efeitos deve receber suas dependências por parâmetros para funcionar offline.');
  const replacements = {
    SITE_CSS: await offlineSiteCSS(siteCSS), EFFECTS_CSS: effectsCSS,
    CATALOG: jsonForHTML(assets.library), REFERENCES: jsonForHTML(assets.references),
    RENDERER: safeScript(assets.renderer), VIEW_MODULE: safeScript(standaloneModule),
    LOGO: `data:image/svg+xml;base64,${logo.toString('base64')}`
  };
  return template.replace(/\{\{(SITE_CSS|EFFECTS_CSS|CATALOG|REFERENCES|RENDERER|VIEW_MODULE|LOGO)\}\}/g, (_, key) => replacements[key]);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [html, assets] = await Promise.all([effectCatalogHTML(), effectNativeAssets()]);
  const destinations = [path.join(effects, 'catalogo.html'), path.join(engine, '../03 - Ajuda/CATÁLOGO DE EFEITOS.html')];
  for (const destination of destinations) { await mkdir(path.dirname(destination), { recursive: true }); await writeFile(destination, html); }
  await writeFile(path.join(panel, 'public/effects-data.js'), assets.dataModule);
  await writeFile(path.join(panel, 'public/effects-renderer.js'), assets.renderer);
  console.log(JSON.stringify({ ok: true, effects: assets.library.effects.length, outputs: destinations.map(p => path.relative(engine, p)) }));
}
