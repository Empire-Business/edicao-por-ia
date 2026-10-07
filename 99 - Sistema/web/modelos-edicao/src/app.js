import { icon } from './icons.js';
import { PreviewManager } from './players.js';
import { filterFormats, buildPrompt, buildStarterPrompt, readStorage, writeStorage, selectionFromHash } from './selection.js';

const main = document.querySelector('main');
const escape = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const favoriteKey = 'modelos-edicao:favorites:v1';
let catalog, players, toastTimer;
let storage;
try { storage = window.localStorage; } catch { storage = { getItem: () => null, setItem: () => { throw Error('Storage unavailable'); } }; }
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const state = { query: '', category: 'all', material: 'all', presence: 'all', favoritesOnly: false,
  favorites: readStorage(storage, favoriteKey, [], value => Array.isArray(value) && value.every(item => /^F\d{2,}$/.test(item))),
  autoplay: readStorage(storage, 'modelos-edicao:autoplay:v1', !reducedMotion.matches, value => typeof value === 'boolean'),
  selectedFormat: null, selectedIdentity: null, selectedExampleId: null, aspect: '9:16', choosing: false, galleryScroll: 0 };

function notify(message) {
  const toast = document.querySelector('#toast'); toast.textContent = message; toast.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { toast.hidden = true; }, 4500);
}

function newPlayers() { players?.destroy(); players = new PreviewManager({ autoplay: state.autoplay, notify }); }
const duration = seconds => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
const button = (label, name = 'arrow', className = '', attrs = '') => `<button class="button ${className}" ${attrs}>${escape(label)}${icon(name)}</button>`;

function media(format, detail = false) {
  const video = Boolean(format.video || format.vimeo);
  return `<div class="media ${detail ? 'detail-media' : ''}" data-media="${format.code}">
    <div class="media-stage"><img src="${escape(format.poster)}" alt="${escape(format.evidence === 'guide' ? 'Esquema ilustrativo' : 'Imagem de referência')} do formato ${escape(format.name)}" ${detail ? 'fetchpriority="high"' : 'loading="lazy"'} width="540" height="960"></div>
    ${detail ? '' : `<a class="media-open" href="#modelo=${format.code}" aria-label="Ver exemplo e detalhes de ${escape(format.name)}"></a>`}
    <span class="media-label"><strong class="preview-code">${format.code}</strong>${video ? `<span class="status-dot" aria-hidden="true"></span><span>${duration(format.duration || 0)}</span>` : '<span>GUIA</span>'}</span>
    ${video ? `<div class="media-controls"><button class="icon-button" data-play aria-label="${state.autoplay ? 'Pausar' : 'Reproduzir'} ${escape(format.name)}" title="${state.autoplay ? 'Pausar' : 'Reproduzir'} prévia">${icon(state.autoplay ? 'pause' : 'play')}</button><button class="icon-button" data-sound aria-pressed="false" aria-label="Ativar som de ${escape(format.name)}" title="Ativar som">${icon('mute')}</button></div>` : ''}
    ${detail ? '' : `<span class="media-expand" aria-hidden="true">${icon('expand')} Ver exemplo</span>`}
  </div>`;
}

function mountPlayers() {
  document.querySelectorAll('[data-media]').forEach(element => {
    const format = catalog.formats.find(item => item.code === element.dataset.media);
    const example = element.classList.contains('detail-media') && format.examples?.find(item => item.id === state.selectedExampleId);
    players.mount(element, example ? {...format,...example} : format, { detail: element.classList.contains('detail-media') });
  });
}

function favoriteButton(format) {
  const active = state.favorites.includes(format.code);
  return `<button class="favorite-button ${active ? 'is-favorite' : ''}" data-favorite="${format.code}" aria-pressed="${active}" aria-label="${active ? 'Remover' : 'Salvar'} ${escape(format.name)} ${active ? 'dos' : 'nos'} favoritos" title="${active ? 'Remover dos favoritos' : 'Salvar nos favoritos'}">${icon('heart')}</button>`;
}

function originalFrames(format) {
  if (!format.referenceFrames?.length) return '';
  return `<section class="original-reference" aria-label="Quadros originais da referência"><h2>${escape(format.referenceFramesTitle || "Quadros da referência")}</h2><p>${escape(format.referenceFramesNote || "Quadros reais recuperados da referência. Eles não demonstram áudio ou transições.")}</p><div class="reference-frame-grid">${format.referenceFrames.map(frame => `<figure><img src="${escape(frame.poster)}" alt="${escape(frame.caption)}" loading="lazy" width="270" height="480"><figcaption>${escape(frame.caption)}</figcaption></figure>`).join('')}</div></section>`;
}

function card(format) {
  return `<article class="model-card" data-code="${format.code}">
    ${media(format)}
    <div class="card-code-row"><strong class="model-code">${format.code}</strong><button class="quick-code-copy" data-copy-code="${format.code}" aria-label="Copiar pedido inicial para ${format.code} ${escape(format.name)}" title="Copiar pedido com este código; completar as outras escolhas depois">${icon('copy')}<span>Copiar pedido</span></button></div>
    <div class="card-heading"><div><span class="eyebrow">${escape(format.tags[0])}</span><h2><a href="#modelo=${format.code}">${escape(format.name)}</a></h2></div>${favoriteButton(format)}</div>
    <p class="card-description">${escape(format.description)}</p>
    ${format.referenceFrames?.length ? '<p class="card-reference-note">Vídeo complementar + quadros originais</p>' : ''}
    <div class="card-bottom"><a class="card-action" href="#modelo=${format.code}">Escolher modelo ${icon('arrow')}</a><span class="evidence-badge" title="${escape(format.evidenceLabel)}">${format.evidenceLabel.includes('Prévia') ? 'Prévia' : format.evidenceLabel.includes('Referência') ? 'Referência' : format.evidence === 'video' ? 'Vídeo' : 'Imagem'}</span></div>
  </article>`;
}

function renderGrid() {
  newPlayers();
  const filtered = filterFormats(catalog.formats, state);
  const grid = document.querySelector('#model-grid');
  grid.innerHTML = filtered.length ? filtered.map(card).join('') : `<div class="empty-state">${icon(state.favoritesOnly ? 'heart' : 'search')}<h2>${state.favoritesOnly ? 'Sua seleção começa aqui.' : 'Vamos tentar outra busca?'}</h2><p>${state.favoritesOnly ? 'Salve modelos no coração para reencontrá-los aqui. Seus favoritos ficam neste navegador.' : 'Busque por “chat”, “narração”, “produto” ou pelo código do modelo.'}</p>${button('Ver todos os modelos', 'arrow', '', 'data-reset')}</div>`;
  document.querySelector('#result-count').textContent = `${filtered.length} ${filtered.length === 1 ? 'modelo' : 'modelos'}`;
  document.querySelector('#favorite-count').textContent = state.favorites.length;
  document.querySelectorAll('[data-category]').forEach(element => element.setAttribute('aria-pressed', String(state.category === element.dataset.category)));
  document.querySelector('[data-favorites-only]').setAttribute('aria-pressed', String(state.favoritesOnly));
  mountPlayers();
}

function gallery() {
  main.innerHTML = `<section class="intro" aria-labelledby="gallery-title"><div><p class="eyebrow intro-eyebrow">A BIBLIOTECA DA SUA PRÓXIMA EDIÇÃO</p><h1 id="gallery-title">Seu próximo vídeo<br>começa <em>aqui.</em></h1></div><div class="intro-aside"><p>Encontre o formato. Escolha a aparência.<br>Leve o pedido pronto para a sua pasta.</p><a href="#como-usar" class="text-link">Como funciona ${icon('arrow')}</a><span class="intro-note"><span class="status-dot" aria-hidden="true"></span> ${catalog.formats.filter(format => format.evidence === 'video').length} referências em vídeo · ${catalog.formats.length} modelos</span></div></section>
    <section class="library" aria-label="Biblioteca de modelos"><div class="library-toolbar"><div class="search-field">${icon('search')}<label for="search" class="sr-only">Buscar modelos</label><input id="search" type="search" placeholder="WhatsApp, tutorial, sem aparecer, mapas…" value="${escape(state.query)}" autocomplete="off"><kbd aria-hidden="true">/</kbd></div><div class="toolbar-actions"><button class="filter-favorite" data-favorites-only aria-pressed="${state.favoritesOnly}">${icon('heart')}<span>Favoritos</span><span id="favorite-count" class="count">${state.favorites.length}</span></button><button class="autoplay-toggle" data-autoplay aria-pressed="${state.autoplay}" title="${state.autoplay ? 'Pausar todas as prévias' : 'Reproduzir prévias automaticamente'}">${icon(state.autoplay ? 'pause' : 'play')}<span>${state.autoplay ? 'Pausar prévias' : 'Reproduzir prévias'}</span></button></div></div>
    <div class="filter-row"><div class="categories" role="group" aria-label="Filtrar por tipo de conteúdo">${catalog.categories.map(category => `<button data-category="${category.id}" aria-pressed="${category.id === state.category}">${escape(category.label)}<span>${category.id === 'all' ? catalog.formats.length : filterFormats(catalog.formats, {category:category.id}).length}</span></button>`).join('')}</div><span id="result-count" role="status" aria-live="polite"></span></div>
    <div class="discovery-bar"><div class="search-suggestions"><span>Experimente</span>${['WhatsApp','Sem aparecer','Tutorial','Mapas'].map(query => `<button data-query="${query}">${query}</button>`).join('')}</div><details class="refine-search"><summary>Refinar escolha</summary><div><label>Começo com<select id="material"><option value="all">Qualquer material</option>${Array.from(new Set(catalog.formats.flatMap(format => format.startingMaterials))).map(value => `<option value="${value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()}" ${state.material === value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase() ? 'selected' : ''}>${value}</option>`).join('')}</select></label><label>Pessoa em cena<select id="presence"><option value="all" ${state.presence === 'all' ? 'selected' : ''}>Qualquer opção</option><option value="person" ${state.presence === 'person' ? 'selected' : ''}>Com pessoa</option><option value="none" ${state.presence === 'none' ? 'selected' : ''}>Sem pessoa em câmera</option><option value="no-recording" ${state.presence === 'no-recording' ? 'selected' : ''}>Sem gravar câmera</option></select></label></div></details></div>
    <p class="library-hint">As prévias começam sem som. ${icon('mute')} Ative o áudio no vídeo que quiser ouvir.</p>
    <div id="model-grid" class="model-grid"></div></section>
    <section class="local-callout"><div><p class="eyebrow">DA ESCOLHA À EDIÇÃO</p><h2>A criação acontece na sua pasta.</h2><p>Você escolhe aqui e leva um pedido pronto para a IA. Seus arquivos continuam no seu computador.</p></div><a href="#como-usar" class="button button-outline">Ver o passo a passo ${icon('arrow')}</a></section>`;
  renderGrid();
}

function sample(identity, compact = false) {
  const p = identity.palette;
  const family = escape(identity.typography.headline);
  return `<div class="identity-sample ${compact ? 'compact-sample' : ''}" style="--id-bg:${p.background};--id-fg:${p.text};--id-accent:${p.primary};--id-surface:${p.surface};--id-muted:${p.muted};--id-font:'${family}'"><span class="sample-label">UMA IDEIA. A SUA CARA.</span><strong>Clareza<br>em cada <span>cena.</span></strong><div class="sample-line"></div><span class="sample-caption">O mesmo conteúdo. Outra aparência.</span><span class="sample-swatch" aria-hidden="true"></span></div>`;
}

function identityChoices() {
  return catalog.identities.map(identity => `<button class="identity-choice ${state.selectedIdentity?.code === identity.code ? 'is-selected' : ''}" data-identity="${identity.code}" aria-pressed="${state.selectedIdentity?.code === identity.code}"><span class="mini-palette" aria-hidden="true" style="--p1:${identity.palette.background};--p2:${identity.palette.primary};--p3:${identity.palette.text}"><i></i><i></i><i></i></span><span><small>${identity.code}</small>${escape(identity.name)}</span>${state.selectedIdentity?.code === identity.code ? icon('check') : ''}</button>`).join('');
}

function choiceArea(format) {
  if (!state.choosing) return `<div class="choose-start"><p class="eyebrow">GOSTOU DESTE FORMATO?</p><p>Agora você escolhe as cores e fontes do seu vídeo.</p>${button('Usar este modelo', 'arrow', 'button-primary', 'data-choose')}<p class="fine-print">A aparência do exemplo é só referência. A próxima edição pode ter outra identidade.</p></div>`;
  const identity = state.selectedIdentity;
  return `<section class="choice-builder" aria-labelledby="choice-title"><div class="step-title"><span class="step-number">02</span><h2 id="choice-title">Escolha a identidade visual</h2></div><p class="step-description">O formato é ${format.code}. Estas são as cores e fontes.</p><div class="identity-choices" role="group" aria-label="Escolher identidade visual">${identityChoices()}</div>
    ${identity ? `<div class="selected-sample">${sample(identity, true)}<p>${escape(identity.typography.headline)} <span>títulos</span> · ${escape(identity.typography.body)} <span>texto</span></p></div>` : `<p class="identity-required">Escolha uma identidade para continuar. Nenhuma vem selecionada.</p>`}
    <div class="aspect-row"><label for="aspect">Tamanho do vídeo</label><select id="aspect"><option value="9:16" ${state.aspect === '9:16' ? 'selected' : ''}>Vertical · 9:16</option><option value="16:9" ${state.aspect === '16:9' ? 'selected' : ''}>Horizontal · 16:9</option><option value="1:1" ${state.aspect === '1:1' ? 'selected' : ''}>Quadrado · 1:1</option></select></div>
    <div class="prompt-area"><div class="step-title"><span class="step-number">03</span><h2>Leve a escolha para a sua pasta</h2></div><p>Cole este pedido na conversa com a IA da sua fábrica.</p>
    <label for="prompt" class="sr-only">Pedido completo para a IA</label><textarea id="prompt" readonly rows="8" ${identity ? '' : 'disabled'}>${identity ? escape(buildPrompt(format, identity, state.aspect)) : 'Seu pedido aparece aqui depois de escolher uma identidade visual.'}</textarea>
    ${button(identity ? 'Copiar pedido de edição' : 'Escolha uma identidade', 'copy', 'button-primary', `data-copy-prompt ${identity ? '' : 'disabled'}`)}<div class="prompt-secondary"><button class="text-link" data-download ${identity ? '' : 'disabled'}>${icon('download')} Baixar escolha</button><button class="text-link" data-share ${identity ? '' : 'disabled'}>${icon('link')} Compartilhar</button></div></div></section>`;
}

function detail(format) {
  newPlayers();
  const selectedExample = format.examples?.find(example => example.id === state.selectedExampleId);
  const view = selectedExample ? {...format,...selectedExample} : format;
  main.innerHTML = `<div class="detail-top"><a href="#modelos" class="text-link">${icon('back')} Voltar à biblioteca</a><span class="eyebrow">${format.code} / ${escape(format.evidenceLabel)}</span><button class="text-link" data-share>${icon('link')} Copiar link</button></div><div class="detail-layout"><div class="detail-left">${format.examples?.length ? `<div class="example-switcher" role="group" aria-label="Variações deste formato"><button data-example="" aria-pressed="${!state.selectedExampleId}">Pessoa integrada</button>${format.examples.map(example => `<button data-example="${example.id}" aria-pressed="${state.selectedExampleId === example.id}">${escape(example.label)}</button>`).join('')}</div>` : ''}${media(view, true)}<p class="reference-caption">${escape(view.evidenceNote)}</p>${originalFrames(format)}</div><div class="detail-content"><div class="detail-title"><div><span class="eyebrow">01 / SEU FORMATO DE EDIÇÃO</span><h1 tabindex="-1">${escape(format.name)}</h1></div>${favoriteButton(format)}</div><p class="detail-lead">${escape(format.description)}</p><div class="detail-tags">${format.tags.map(tag => `<span>${escape(tag)}</span>`).join('')}</div><div class="format-facts"><div><span>Pessoa em cena</span><strong>${format.hasPersonOnScreen ? format.cameraRequired ? 'Apresentador em vídeo' : 'Foto ou avatar' : 'Sem apresentador'}</strong></div><div><span>Material de partida</span><strong>${format.startingMaterials.map(escape).join(' · ')}</strong></div><div><span>Como é construído</span><strong>${format.buildingBlocks.map(escape).join(' · ')}</strong></div></div><div class="model-fit"><h2>Funciona bem para</h2><p>${escape(format.use)}</p></div><div id="choice-area">${choiceArea(format)}</div>
    <details class="model-guide"><summary>Entenda como a edição funciona <span aria-hidden="true">+</span></summary><div><h3>O que enviar</h3><p>${escape(format.inputs)}</p><h3>Como o formato organiza o vídeo</h3><p>${escape(format.mechanism)}</p><ol>${format.steps.map(step => `<li>${escape(step)}</li>`).join('')}</ol><h3>Cuidados deste formato</h3><p>${escape(format.avoid)}</p><p class="fine-print">Na sua pasta: “04 - Formatos” → “${format.code}” → “GUIA DA EDIÇÃO”. Cores e fontes ficam em “05 - IDs Visuais”.</p></div></details></div></div>`;
  mountPlayers();
}

function identities() {
  main.innerHTML = `<section class="page-intro"><p class="eyebrow">AS CORES E FONTES DO SEU VÍDEO</p><h1>Mesmo formato.<br>Outra <em>personalidade.</em></h1><p>Identidade visual é a aparência. Você pode combinar qualquer uma delas com qualquer formato de edição.</p></section><div class="identity-grid">${catalog.identities.map(identity => `<article class="identity-card">${sample(identity)}<div class="identity-heading"><div><p class="eyebrow">${identity.code}</p><h2>${escape(identity.name)}</h2></div><span class="palette-dots" aria-label="Cores da identidade">${Object.values(identity.palette).slice(0, 3).map(color => `<i style="background:${color}" title="${color}"></i>`).join('')}</span></div><p class="identity-fonts">${escape(identity.typography.headline)} · ${escape(identity.typography.body)}</p><button class="card-action" data-pick-identity="${identity.code}">Escolher esta identidade ${icon('arrow')}</button></article>`).join('')}</div><div class="identity-explainer"><h2>Cores não escolhem a edição.</h2><p>As amostras mostram a paleta e a fonte de título. O formato escolhido define cortes, ritmo, composição e animações. Nenhum logotipo vem ativado automaticamente.</p></div>`;
}

function howTo() {
  main.innerHTML = `<section class="page-intro how-intro"><p class="eyebrow">DO NAVEGADOR PARA A SUA FÁBRICA</p><h1>Escolha aqui.<br>Crie na <em>sua pasta.</em></h1><p>O painel ajuda a decidir. A IA monta a edição no seu computador, usando os arquivos e as regras da sua fábrica.</p></section><div class="how-steps"><section><span class="how-number">01</span><div><h2>Veja e escolha um modelo</h2><p>Assista às prévias, ative o som quando quiser e abra os detalhes. Escolha o formato que combina com o que você quer explicar.</p><a href="#modelos" class="text-link">Explorar a biblioteca ${icon('arrow')}</a></div></section><section><span class="how-number">02</span><div><h2>Dê a sua cara ao vídeo</h2><p>Escolha uma identidade visual e o tamanho. O exemplo mostra uma forma de editar; a pessoa, marca, cores e fontes do exemplo não entram automaticamente no seu vídeo.</p><a href="#identidades" class="text-link">Ver identidades visuais ${icon('arrow')}</a></div></section><section><span class="how-number">03</span><div><h2>Copie o pedido e continue na pasta</h2><p>Coloque sua gravação e materiais em <strong>“01 - Enviar vídeos”</strong>. Abra a conversa com a IA na pasta da fábrica e cole o pedido copiado. Ela confere as escolhas, prepara a edição e entrega uma prévia para você revisar.</p><div class="folder-flow"><span>${icon('folder')}01 - Enviar vídeos</span>${icon('arrow')}<span>${icon('folder')}02 - Ver vídeos</span></div></div></section></div><div class="faq"><h2>Bom saber antes de começar</h2><details><summary>Preciso baixar uma skill para cada modelo? <span>+</span></summary><p>Os modelos distribuídos já fazem parte da sua fábrica. O pedido usa o código do formato e da identidade. Se sua pasta estiver desatualizada, peça à IA para atualizar a fábrica, preservando seus trabalhos e configurações.</p></details><details><summary>E se eu tiver modelos ou identidades próprios? <span>+</span></summary><p>Este painel mostra a biblioteca distribuída pelo autor. Os seus cadastros locais ficam em “04 - Formatos” e “05 - IDs Visuais”. Diga à IA o código que deseja usar; ela consulta o catálogo da sua pasta antes de editar.</p></details><details><summary>Meus vídeos são enviados por este painel? <span>+</span></summary><p>Você assiste aos exemplos publicados aqui. Suas gravações ficam na pasta local. Este painel não tem envio de arquivos, acesso ao disco nem sincronização dos seus trabalhos.</p></details><details><summary>Como peço um ajuste depois? <span>+</span></summary><p>Use o código da edição, como E01, e indique o momento: “Na E01, aos 12 segundos, tire o texto”. Ajustes de edição ficam no formato; mudanças de cor e fonte ficam na identidade visual.</p></details></div>`;
}

function notFound() { main.innerHTML = `<div class="empty-state"><h1>Esse modelo não está na biblioteca.</h1><p>Escolha um modelo disponível ou consulte os códigos da sua pasta local.</p><a href="#modelos" class="button button-primary">Ver modelos ${icon('arrow')}</a></div>`; }

function renderRoute({ focus = false } = {}) {
  players?.destroy();
  const hash = location.hash.slice(1);
  const detailRoute = hash.startsWith('modelo=');
  document.querySelectorAll('[data-nav]').forEach(link => {
    const active = link.dataset.nav === (detailRoute || !hash ? 'modelos' : hash);
    if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
  });
  if (detailRoute) {
    const selection = selectionFromHash(location.hash, catalog);
    if (!selection.format) { notFound(); return; }
    if (state.selectedFormat?.code !== selection.format.code) { state.choosing = false; state.selectedExampleId = null; }
    state.selectedFormat = selection.format;
    // A shared link is an explicit F/ID selection; no fallback identity is ever assigned.
    if (selection.identity) { state.selectedIdentity = selection.identity; state.choosing = true; }
    state.aspect = selection.aspect;
    detail(selection.format);
    document.title = `${selection.format.code} · ${selection.format.name} | Modelos de edição`;
  } else {
    if (hash === 'identidades') identities(); else if (hash === 'como-usar') howTo(); else gallery();
    document.title = 'Modelos de edição | Escolha seu próximo vídeo';
  }
  if (focus) { window.scrollTo(0, hash === 'modelos' ? state.galleryScroll : 0); main.focus({ preventScroll: true }); }
}

function updateChoice() { document.querySelector('#choice-area').innerHTML = choiceArea(state.selectedFormat); }

async function copyText(text, fallback) {
  try { await navigator.clipboard.writeText(text); notify('Copiado. Agora é só colar na conversa com a IA.'); }
  catch {
    const previous = document.activeElement;
    const temporary = document.createElement('textarea');
    temporary.value = text; temporary.readOnly = true;
    temporary.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0';
    document.body.append(temporary); temporary.focus(); temporary.select();
    let copied = false;
    try { copied = document.execCommand('copy'); } catch {}
    temporary.remove();
    if (copied) { previous?.focus({preventScroll:true}); notify('Copiado. Agora é só colar na conversa com a IA.'); return; }
    if (fallback) { fallback.focus(); fallback.select(); notify('Selecionei o pedido. Copie com Ctrl+C ou ⌘C.'); }
    else {
      main.querySelector('.manual-copy')?.remove();
      const field = document.createElement('textarea'); field.className = 'manual-copy'; field.value = text; field.readOnly = true; field.rows = 6; field.setAttribute('aria-label', 'Texto para copiar');
      main.prepend(field); field.focus(); field.select(); notify('Selecionei o texto. Copie com Ctrl+C ou ⌘C.');
    }
  }
}

main.addEventListener('input', event => { if (event.target.id === 'search') { state.query = event.target.value; renderGrid(); } });
main.addEventListener('change', event => {
  if (event.target.id === 'aspect') { state.aspect = event.target.value; const area = document.querySelector('#prompt'); if (state.selectedIdentity) area.value = buildPrompt(state.selectedFormat, state.selectedIdentity, state.aspect); }
  if (event.target.id === 'material' || event.target.id === 'presence') { state[event.target.id] = event.target.value; renderGrid(); }
});

document.addEventListener('click', async event => {
  const target = event.target.closest('button, a');
  if (!target) return;
  if (target.matches('a[href^="#modelo="]') && !location.hash.startsWith('#modelo=')) state.galleryScroll = window.scrollY;
  if (target.dataset.favorite) {
    const code = target.dataset.favorite; const active = state.favorites.includes(code);
    state.favorites = active ? state.favorites.filter(item => item !== code) : [...state.favorites, code];
    const saved = writeStorage(storage, favoriteKey, state.favorites);
    target.outerHTML = favoriteButton(catalog.formats.find(format => format.code === code));
    if (state.favoritesOnly && document.querySelector('#model-grid')) renderGrid();
    const nextFocus = document.querySelector(`[data-favorite="${code}"]`) || document.querySelector('[data-favorites-only]');
    nextFocus?.focus({ preventScroll: true });
    const count = document.querySelector('#favorite-count'); if (count) count.textContent = state.favorites.length;
    notify(saved ? active ? 'Modelo removido dos favoritos.' : 'Modelo salvo nos favoritos deste navegador.' : 'Favorito marcado para esta visita. O navegador não permitiu salvar.');
  } else if (target.dataset.category) {
    state.category = target.dataset.category; renderGrid();
  } else if (target.dataset.copyCode) {
    await copyText(buildStarterPrompt(catalog.formats.find(format => format.code === target.dataset.copyCode)));
  } else if (target.hasAttribute('data-favorites-only')) {
    state.favoritesOnly = !state.favoritesOnly; renderGrid();
  } else if (target.hasAttribute('data-reset')) {
    state.query = ''; state.category = 'all'; state.material = 'all'; state.presence = 'all'; state.favoritesOnly = false;
    document.querySelector('#search').value = ''; document.querySelector('#material').value = 'all'; document.querySelector('#presence').value = 'all'; renderGrid();
  } else if (target.dataset.query) {
    state.query = target.dataset.query; document.querySelector('#search').value = state.query; renderGrid(); document.querySelector('#search').focus({ preventScroll: true });
  } else if (target.hasAttribute('data-autoplay')) {
    state.autoplay = !state.autoplay; writeStorage(storage, 'modelos-edicao:autoplay:v1', state.autoplay);
    players?.setAutoplay(state.autoplay); target.setAttribute('aria-pressed', String(state.autoplay));
    target.setAttribute('title', state.autoplay ? 'Pausar todas as prévias' : 'Reproduzir prévias automaticamente');
    target.innerHTML = `${icon(state.autoplay ? 'pause' : 'play')}<span>${state.autoplay ? 'Pausar prévias' : 'Reproduzir prévias'}</span>`;
  } else if (target.hasAttribute('data-choose')) {
    state.choosing = true; updateChoice(); document.querySelector('#choice-title').setAttribute('tabindex', '-1'); document.querySelector('#choice-title').focus({ preventScroll: true });
    if (window.innerWidth < 900) document.querySelector('#choice-area').scrollIntoView({ behavior: reducedMotion.matches ? 'instant' : 'smooth', block: 'start' });
  } else if (target.dataset.identity) {
    state.selectedIdentity = catalog.identities.find(identity => identity.code === target.dataset.identity); updateChoice();
    document.querySelector(`[data-identity="${state.selectedIdentity.code}"]`).focus({ preventScroll: true });
  } else if (target.hasAttribute('data-example')) {
    state.selectedExampleId = target.dataset.example || null; detail(state.selectedFormat);
    document.querySelector(`[data-example="${state.selectedExampleId || ''}"]`)?.focus({ preventScroll: true });
  } else if (target.dataset.pickIdentity) {
    state.selectedIdentity = catalog.identities.find(identity => identity.code === target.dataset.pickIdentity);
    if (state.selectedFormat) { state.choosing = true; location.hash = `modelo=${state.selectedFormat.code}&id=${state.selectedIdentity.code}&tamanho=${encodeURIComponent(state.aspect)}`; }
    else { location.hash = 'modelos'; notify(`${state.selectedIdentity.code} escolhida. Agora escolha o formato de edição.`); }
  } else if (target.hasAttribute('data-copy-prompt')) {
    const text = buildPrompt(state.selectedFormat, state.selectedIdentity, state.aspect);
    await copyText(text, document.querySelector('#prompt'));
  } else if (target.hasAttribute('data-download')) {
    const text = buildPrompt(state.selectedFormat, state.selectedIdentity, state.aspect);
    const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a'); link.href = url; link.download = `Minha-edicao-${state.selectedFormat.code}-${state.selectedIdentity.code}.txt`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000); notify('Escolha salva. Leve esse pedido para a IA na sua pasta.');
  } else if (target.hasAttribute('data-share')) {
    const url = new URL(location.href); const format = state.selectedFormat;
    url.hash = `modelo=${format.code}${state.selectedIdentity && state.choosing ? `&id=${state.selectedIdentity.code}&tamanho=${encodeURIComponent(state.aspect)}` : ''}`;
    await copyText(url.href);
  }
});

document.addEventListener('keydown', event => {
  if (event.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName) && document.querySelector('#search')) { event.preventDefault(); document.querySelector('#search').focus(); }
});
window.addEventListener('hashchange', () => renderRoute({ focus: true }));
window.addEventListener('pagehide', () => players?.destroy());
window.addEventListener('pageshow', event => { if (event.persisted && catalog) renderRoute(); });

try {
  const response = await fetch('catalog.json'); if (!response.ok) throw Error('Catálogo indisponível');
  catalog = await response.json();
  state.favorites = state.favorites.filter(code => catalog.formats.some(format => format.code === code));
  renderRoute();
} catch {
  main.innerHTML = `<div class="empty-state"><h1>A biblioteca não carregou.</h1><p>Confira sua conexão e tente novamente. Os guias continuam disponíveis em “04 - Formatos” na sua pasta local.</p>${button('Tentar novamente', 'arrow', 'button-primary', 'data-retry')}</div>`;
  document.querySelector('[data-retry]').addEventListener('click', () => location.reload());
}
