export const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
export const compareFormatCodes = (a,b) => Number(a.code.match(/\d+$/)?.[0] || 0)-Number(b.code.match(/\d+$/)?.[0] || 0) || a.code.localeCompare(b.code);

const stopWords = new Set(['de','da','do','das','dos','a','o','um','uma','e','para','pra','eu','quero','meu','minha','fazer','video','videos','sobre','que','como']);
const aliases = { whastapp:'whatsapp', whatsap:'whatsapp', zap:'whatsapp', wpp:'whatsapp', photo:'foto', mensagens:'mensagem', graficos:'grafico', mapas:'mapa', numeros:'numero', comparacoes:'comparacao', narracao:'narracao', naracao:'narracao', tutorial:'tutorial' };
const canonical = value => normalize(value).replace(/\b(?:mensagens|graficos|mapas|numeros|comparacoes|whastapp|whatsap|zap|wpp|photo)\b/g,word=>aliases[word] || word);
const searchable = format => canonical([format.code,format.name,format.description,format.use,format.inputs,format.mechanism,format.evidenceLabel,
  ...(format.tags || []),...(format.searchTerms || []),...(format.buildingBlocks || []),...(format.startingMaterials || [])].join(' '));

export function filterFormats(formats, { query = '', category = 'all', favoritesOnly = false, favorites = [], material = 'all', presence = 'all' } = {}) {
  let text = normalize(query).trim().replace(/\b(?:eu|quero|preciso|prefiro)\b/g,' ').replace(/\s+/g,' ').trim();
  const noPerson = /sem (aparecer|apresentador)|nao aparecer/.test(text);
  const noRecording = /sem (gravar|camera)|nao gravar/.test(text);
  text = text.replace(/sem (aparecer|apresentador|gravar(?: camera)?|camera)|nao (aparecer|gravar)/g,' ');
  const terms = text.split(/[^a-z0-9]+/).filter(term => term && !stopWords.has(term)).map(term => aliases[term] || term);
  const result = formats.filter(format => (!favoritesOnly || favorites.includes(format.code))
    && (category === 'all' || (category === 'presenter' ? format.hasPersonOnScreen : format.category === category || format.categories?.includes(category)))
    && (material === 'all' || (format.startingMaterials || []).some(value => normalize(value) === material))
    && (presence === 'all' || (presence === 'person' ? format.hasPersonOnScreen : presence === 'none' ? !format.hasPersonOnScreen : !format.cameraRequired))
    && (!noPerson || !format.hasPersonOnScreen)
    && (!noRecording || !format.cameraRequired)
    && terms.every(term => searchable(format).includes(term)));
  return result.sort(compareFormatCodes);
}

export function buildPrompt(format, identity, aspect = '9:16') {
  if (!format || !/^F\d{2,}$/.test(format.code) || !identity || !/^ID\d{2,}$/.test(identity.code)) throw Error('Escolha um formato e uma identidade visual.');
  if (!['9:16', '16:9', '1:1'].includes(aspect)) throw Error('Tamanho inválido.');
  return `Quero editar o material que coloquei em “01 - Enviar vídeos”.\n\nFormato de edição: ${format.code} (${format.name}).\nIdentidade visual: ${identity.code} (${identity.name}).\nTamanho do vídeo: ${aspect}.\n\nConfira se esses códigos correspondem ao catálogo desta pasta e me avise se houver diferença, sem substituir minha escolha. Use as regras atuais da fábrica e confirme qual material usar se houver mais de um vídeo. Preserve os originais e prepare uma prévia para revisão. As cores e fontes devem vir da identidade escolhida; a pessoa, marca e aparência dos exemplos são apenas referência. Não acrescente nome de marca, assinatura, logotipo, monograma ou cartela comercial da referência. Logotipos somente se eu pedir para esta edição.${format.code === 'F05' ? ' No F05, não escrever EMPIRE como cabeçalho, assinatura ou marca da edição.' : ''}`;
}

export function buildStarterPrompt(format) {
  if (!format || !/^F\d{2,}$/.test(format.code)) throw Error('Escolha um formato válido.');
  return `Quero usar o formato ${format.code} (${format.name}) no meu próximo vídeo.\n\nIdentidade visual: ainda vou escolher.\nTamanho do vídeo: ainda vou escolher.\nMaterial: vou indicar os arquivos em “01 - Enviar vídeos”.\n\nConfira se ${format.code} corresponde a esse modelo no catálogo da minha pasta. Ajude-me a completar as escolhas que faltam antes de iniciar a edição. Não use a marca, os textos de assinatura, a pessoa ou o logotipo do exemplo automaticamente.${format.code === 'F05' ? ' No F05, não escrever EMPIRE como marca da edição.' : ''}`;
}

export function readStorage(storage, key, fallback, validate = () => true) {
  try { const value = JSON.parse(storage.getItem(key)); return value !== null && validate(value) ? value : fallback; } catch { return fallback; }
}

export function writeStorage(storage, key, value) { try { storage.setItem(key, JSON.stringify(value)); return true; } catch { return false; } }

export function selectionFromHash(hash, catalog) {
  const params = new URLSearchParams(hash.replace(/^#/, ''));
  return { format: catalog.formats.find(format => format.code === params.get('modelo')) || null,
    identity: catalog.identities.find(identity => identity.code === params.get('id')) || null,
    aspect: ['9:16', '16:9', '1:1'].includes(params.get('tamanho')) ? params.get('tamanho') : '9:16' };
}
