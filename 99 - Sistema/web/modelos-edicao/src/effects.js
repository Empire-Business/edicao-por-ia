const FAVORITES_KEY = 'cortez:effects:favorites:v1';
const PALETTE = { accent: '#A855F7', secondaryAccent: '#C88BF7', foreground: '#F4EEFB', background: '#140B21', fontFamily: 'Manrope' };
const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const safeUrl = value => { try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };
const inspectionLabels = { 'motion-observed': 'Movimento observado', 'frames-observed': 'Quadros observados', 'text-only': 'Texto consultado' };
const originLabels = { original: 'Estudo original do Cortez', 'cortez-study': 'Estudo original do Cortez', research: 'Pesquisa complementar' };
const supportLabels = { 'review-required': 'Revisão editorial necessária', 'study-only': 'Somente estudo visual', 'tested-component': 'Componente testado', 'preview-only': 'Estudo de demonstração' };

export function createEffectsView({ main, library, references = {}, notify = () => {}, copyText = async () => {}, storage = window.localStorage, reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)'), icon = () => '', getPromptContext = () => ({}) }) {
  const effects = library.effects || [];
  const find = code => effects.find(effect => effect.code === code);
  let query = '', category = 'all', favoritesOnly = false;
  let globalPlaying = !reducedMotion.matches;
  let overrides = new Map();
  let favorites = [];
  try {
    const saved = JSON.parse(storage.getItem(FAVORITES_KEY) || '[]');
    if (Array.isArray(saved)) favorites = saved.map(value => find(value)?.code || effects.find(effect => effect.id === value)?.code).filter(Boolean);
    storage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
  } catch { /* storage can be unavailable */ }

  let observer = null, raf = 0, active = new Map(), current = null, destroyed = false, listenersAttached = false;
  const isPlaying = code => overrides.has(code) ? overrides.get(code) : globalPlaying;
  const durationOf = effect => Math.max(.01, Number(effect.demo.duration) || 3);
  const stillTime = effect => durationOf(effect) * .52;
  const refFor = id => references instanceof Map ? references.get(id) : Array.isArray(references.sources) ? references.sources.find(source => source.id === id) : references[id];
  const options = (effect, extra = {}) => ({ ...effect.demo, ...PALETTE, mode: 'demo', ...extra });
  const demoOptions = effect => ({ text: main.querySelector('[data-fx-text]')?.value, title: main.querySelector('[data-fx-text]')?.value, accent: main.querySelector('[data-fx-accent]')?.value });

  function renderFrame(canvas, effect, time, extra = {}) {
    window.CortezEffects?.render(canvas, effect.id, time, options(effect, extra));
  }
  function cancelLoop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
  function scheduleLoop() {
    if (!raf && [...active.values()].some(item => item.running) && !document.hidden) raf = requestAnimationFrame(tick);
  }
  function tick(now) {
    raf = 0;
    if (destroyed || document.hidden) return;
    for (const [canvas, item] of active) {
      if (!canvas.isConnected || !main.contains(canvas)) { active.delete(canvas); continue; }
      if (!item.running) continue;
      item.time = ((now - item.started) / 1000) % durationOf(item.effect);
      renderFrame(canvas, item.effect, item.time, canvas.closest('.fx-detail-media') ? demoOptions(item.effect) : {});
      const scrub = canvas.closest('.fx-detail-media') && main.querySelector('[data-fx-scrub]');
      if (scrub) scrub.value = String(item.time);
    }
    scheduleLoop();
  }
  function updatePlaybackButtons() {
    main.querySelectorAll('[data-fx-play]').forEach(button => {
      const on = isPlaying(button.dataset.fxPlay);
      button.innerHTML = icon(on ? 'pause' : 'play');
      button.setAttribute('aria-label', `${on ? 'Pausar' : 'Reproduzir'} prévia de ${button.dataset.fxPlay}`);
      button.title = `${on ? 'Pausar' : 'Reproduzir'} prévia`;
    });
    const button = main.querySelector('[data-fx-toggle]');
    if (button) { const on = isPlaying(current?.code); button.setAttribute('aria-pressed', String(on)); button.innerHTML = `${icon(on ? 'pause' : 'play')} ${on ? 'Pausar' : 'Reproduzir'}`; }
  }
  function setPlayback(code, on, { restart = false } = {}) {
    overrides.set(code, on);
    for (const [canvas, item] of active) {
      if (item.effect.code !== code) continue;
      item.running = on;
      if (restart || (on && !item.started)) item.time = 0;
      if (on) item.started = performance.now() - item.time * 1000;
      else if (!canvas.closest('.fx-detail-media')) { item.time = stillTime(item.effect); renderFrame(canvas, item.effect, item.time); }
    }
    if (on) scheduleLoop(); else if (![...active.values()].some(item => item.running)) cancelLoop();
    updatePlaybackButtons();
  }
  function mountVisible() {
    observer?.disconnect(); observer = null;
    active.clear(); cancelLoop();
    const canvases = [...main.querySelectorAll('[data-fx-canvas]')];
    const enter = canvas => {
      const effect = find(canvas.dataset.fxCanvas); if (!effect) return;
      const run = isPlaying(effect.code), time = run ? 0 : stillTime(effect);
      const item = { effect, running: run, time, started: run ? performance.now() : 0 };
      active.set(canvas, item);
      renderFrame(canvas, effect, time, canvas.closest('.fx-detail-media') ? demoOptions(effect) : {});
      scheduleLoop();
    };
    if ('IntersectionObserver' in window) {
      observer = new IntersectionObserver(entries => entries.forEach(entry => {
        if (entry.isIntersecting) { if (!active.has(entry.target)) enter(entry.target); }
        else active.delete(entry.target);
        if (![...active.values()].some(item => item.running)) cancelLoop();
      }), { rootMargin: '180px 0px' });
      canvases.forEach(canvas => { canvas.width = 540; canvas.height = 960; observer.observe(canvas); });
    } else {
      canvases.forEach(canvas => {
        canvas.width = 540; canvas.height = 960;
        const rect = canvas.getBoundingClientRect();
        if (rect.bottom >= 0 && rect.top <= innerHeight) enter(canvas);
      });
    }
  }

  function activate() {
    destroyed = false;
    if (listenersAttached) return;
    main.addEventListener('input', onInput);
    main.addEventListener('click', onClick);
    document.addEventListener('keydown', onKeydown);
    document.addEventListener('visibilitychange', onVisibility);
    reducedMotion.addEventListener?.('change', onReducedMotion);
    listenersAttached = true;
  }
  function deactivate() {
    observer?.disconnect(); observer = null;
    active.clear(); cancelLoop();
    if (!listenersAttached) return;
    main.removeEventListener('input', onInput);
    main.removeEventListener('click', onClick);
    document.removeEventListener('keydown', onKeydown);
    document.removeEventListener('visibilitychange', onVisibility);
    reducedMotion.removeEventListener?.('change', onReducedMotion);
    listenersAttached = false;
  }

  function gallery() {
    activate(); current = null;
    const categories = [...new Set(effects.map(effect => effect.category))], shown = filtered();
    main.innerHTML = `<section class="intro" aria-labelledby="fx-title"><div><p class="eyebrow intro-eyebrow">BIBLIOTECA DE MOTION · ${effects.length} EFEITOS</p><h1 id="fx-title">Dê forma à<br>sua <em>mensagem.</em></h1></div><div class="intro-aside"><p>Explore estudos visuais e escolha o movimento que combina com a fala.</p><span class="intro-note"><span class="status-dot" aria-hidden="true"></span> Prévias ilustrativas · F e ID continuam escolhas do trabalho</span></div></section><section class="library" aria-label="Biblioteca de efeitos"><div class="library-toolbar"><div class="search-field">${icon('search')}<label class="sr-only" for="fx-search">Buscar efeitos</label><input id="fx-search" type="search" data-fx-search placeholder="Buscar por nome, código ou uso…" value="${escape(query)}" autocomplete="off"><kbd aria-hidden="true">/</kbd></div><div class="toolbar-actions"><button class="filter-favorite" data-fx-favorites aria-pressed="${favoritesOnly}">${icon('heart')}<span>Favoritos</span><span id="fx-favorite-count" class="count">${favorites.length}</span></button><button class="autoplay-toggle" data-fx-autoplay aria-pressed="${globalPlaying}" title="${globalPlaying ? 'Pausar' : 'Reproduzir'} prévias">${icon(globalPlaying ? 'pause' : 'play')}<span>${globalPlaying ? 'Pausar prévias' : 'Reproduzir prévias'}</span></button></div></div><div class="filter-row"><div class="categories" role="group" aria-label="Filtrar por categoria"><button data-fx-category="all" aria-pressed="${category === 'all'}">Todos<span>${effects.length}</span></button>${categories.map(name => `<button data-fx-category="${escape(name)}" aria-pressed="${category === name}">${escape(name)}<span>${effects.filter(effect => effect.category === name).length}</span></button>`).join('')}</div><span role="status" aria-live="polite">${shown.length} ${shown.length === 1 ? 'efeito' : 'efeitos'}</span></div><p class="library-hint">Cada quadro é uma ilustração de demonstração. Confira fonte e cuidados antes de usar.</p><div id="fx-grid" class="model-grid">${shown.length ? shown.map(card).join('') : `<div class="empty-state"><h2>Nenhum efeito encontrado.</h2><p>Altere a busca ou a categoria selecionada.</p><button class="button button-primary" data-fx-reset>Ver todos os efeitos ${icon('arrow')}</button></div>`}</div></section>`;
    mountVisible();
  }

  function promptFor(effect) {
    const context = getPromptContext() || {};
    const choices = [context.format && `Formato de edição: ${context.format}.`, context.identity && `Identidade visual: ${context.identity}.`].filter(Boolean).join(' ');
    const missing = [!context.format && 'formato F', !context.identity && 'identidade visual ID'].filter(Boolean);
    const selection = `Este efeito complementa o formato F e a identidade visual ID escolhidos para o trabalho. ${choices}${missing.length ? ` Antes de editar, pergunte pela escolha de ${missing.join(' e ')}; não escolha códigos automaticamente.` : ' Preserve essas escolhas.'}`;
    return `Cortez, aplique o efeito ${effect.code} — ${effect.name}. ${effect.production_note || effect.description} Sincronize com as palavras da montagem final. ${selection} Preserve originais. Logotipos só entram se eu pedir explicitamente nesta edição.`;
  }

  const favoriteButton = effect => {
    const saved = favorites.includes(effect.code);
    return `<button class="favorite-button ${saved ? 'is-favorite' : ''}" data-fx-favorite="${escape(effect.code)}" aria-pressed="${saved}" aria-label="${saved ? 'Remover' : 'Salvar'} ${escape(effect.name)} ${saved ? 'dos' : 'nos'} favoritos" title="${saved ? 'Remover dos favoritos' : 'Salvar nos favoritos'}">${icon('heart')}</button>`;
  };
  const card = effect => {
    const on = isPlaying(effect.code);
    return `<article class="model-card fx-card" data-fx-card="${escape(effect.code)}"><div class="media fx-media"><div class="media-stage"><canvas data-fx-canvas="${escape(effect.code)}" aria-label="Prévia ilustrativa: ${escape(effect.name)}"></canvas></div><a class="media-open" href="#efeito=${encodeURIComponent(effect.code)}" aria-label="Ver detalhes de ${escape(effect.name)}"></a><span class="media-label"><strong class="preview-code">${escape(effect.code)}</strong><span>${escape(effect.status_label || 'Estudo')}</span></span><div class="media-controls"><button class="icon-button" data-fx-play="${escape(effect.code)}" aria-label="${on ? 'Pausar' : 'Reproduzir'} prévia" title="${on ? 'Pausar' : 'Reproduzir'} prévia">${icon(on ? 'pause' : 'play')}</button></div><span class="media-expand" aria-hidden="true">${icon('expand')} Ver efeito</span></div><div class="card-code-row"><strong class="model-code">${escape(effect.code)}</strong><button class="quick-code-copy" data-fx-copy="${escape(effect.code)}">${icon('copy')}<span>Copiar pedido</span></button></div><div class="card-heading"><div><span class="eyebrow">${escape(effect.category)}</span><h2><a href="#efeito=${encodeURIComponent(effect.code)}">${escape(effect.name)}</a></h2></div>${favoriteButton(effect)}</div><p class="card-description">${escape(effect.description)}</p><div class="card-bottom"><a class="card-action" href="#efeito=${encodeURIComponent(effect.code)}">Ver efeito ${icon('arrow')}</a><span class="evidence-badge">${escape(effect.status_label || 'Estudo')}</span></div></article>`;
  };
  function filtered() {
    const terms = normalize(query).trim().split(/\s+/).filter(Boolean);
    return effects.filter(effect => (category === 'all' || effect.category === category) && (!favoritesOnly || favorites.includes(effect.code)) && terms.every(term => normalize([effect.code, effect.id, effect.name, effect.category, effect.description, effect.use_when, effect.caution].join(' ')).includes(term)));
  }

  function referenceMarkup(effect) {
    return (effect.reference_ids || []).map(id => {
      const ref = refFor(id);
      if (!ref || ref.visibility === 'internal' || ref.local_path || !safeUrl(ref.url || ref.href)) return '';
      const href = safeUrl(ref.url || ref.href), label = inspectionLabels[ref.inspection] || 'Referência documental';
      return `<div class="fx-source"><span class="eyebrow">${escape(label)}</span>${href ? `<a href="${escape(href)}" target="_blank" rel="noopener noreferrer">${escape(ref.title || ref.name || id)} ↗</a>` : `<strong>${escape(ref.title || ref.name || id)}</strong>`}<span>${escape(ref.observed || ref.notes || 'A referência contextualiza o efeito; não comprova o resultado desta demonstração.')}</span></div>`;
    }).join('') || '<p>Nenhuma referência pública vinculada a este efeito.</p>';
  }
  function detail(code) {
    activate();
    const effect = find(code);
    if (!effect) { current = null; main.innerHTML = `<div class="empty-state"><h1>Esse efeito não está na biblioteca.</h1><a href="#efeitos" class="button button-primary">Ver efeitos ${icon('arrow')}</a></div>`; return; }
    current = effect;
    const prompt = promptFor(effect), on = isPlaying(effect.code);
    main.innerHTML = `<div class="detail-top"><a href="#efeitos" class="text-link">${icon('back')} Voltar à biblioteca</a><span class="eyebrow">${escape(effect.code)} / ${escape(effect.status_label || 'ESTUDO')}</span></div><div class="detail-layout fx-detail-layout"><div class="detail-left"><div class="media detail-media fx-detail-media"><div class="media-stage"><canvas data-fx-canvas="${escape(effect.code)}" aria-label="Prévia ilustrativa: ${escape(effect.name)}"></canvas></div><span class="media-label"><strong class="preview-code">${escape(effect.code)}</strong><span>DEMONSTRAÇÃO</span></span></div><div class="fx-player"><button class="button button-outline" data-fx-toggle aria-pressed="${on}">${icon(on ? 'pause' : 'play')} ${on ? 'Pausar' : 'Reproduzir'}</button><button class="button button-outline" data-fx-restart>${icon('arrow')} Reiniciar</button><label>Momento<input data-fx-scrub type="range" min="0" max="${durationOf(effect)}" step="0.01" value="${on ? 0 : stillTime(effect)}" aria-label="Posição da prévia"></label></div><p class="reference-caption">${escape(effect.evidence || library.demo_notice || 'Demonstração ilustrativa.')}</p></div><div class="detail-content"><div class="detail-title"><div><span class="eyebrow">${escape(effect.category)} · ${escape(effect.code)}</span><h1 tabindex="-1">${escape(effect.name)}</h1></div>${favoriteButton(effect)}</div><p class="detail-lead">${escape(effect.description)}</p><div class="model-fit"><h2>Quando funciona</h2><p>${escape(effect.use_when || 'Use quando o movimento reforçar uma ideia da fala.')}</p></div><div class="model-fit fx-caution"><h2>Cuidados</h2><p>${escape(effect.caution || 'Revise a leitura e a posição na montagem final.')}</p></div><div class="format-facts">${originLabels[effect.origin] ? `<div><span>Origem</span><strong>${escape(originLabels[effect.origin])}</strong></div>` : ''}<div><span>Aplicação</span><strong>${escape(supportLabels[effect.production_support] || 'Revisão editorial')}</strong></div></div><div class="model-fit"><h2>Fontes e referências</h2><div class="fx-sources">${referenceMarkup(effect)}</div></div><label class="fx-edit-label" for="fx-demo-text">Texto de demonstração</label><textarea id="fx-demo-text" data-fx-text rows="2">${escape(effect.demo.text || effect.demo.title || '')}</textarea><label class="fx-edit-label" for="fx-demo-accent">Cor de demonstração</label><input id="fx-demo-accent" data-fx-accent type="color" value="${PALETTE.accent}"><div class="prompt-area"><p>O pedido combina este efeito às escolhas atuais de F e ID.</p><button class="button button-primary" data-fx-copy-prompt>${icon('copy')} Copiar pedido</button><textarea data-fx-prompt readonly aria-label="Pedido completo para copiar">${escape(prompt)}</textarea></div></div></div>`;
    mountVisible();
  }

  function updateFavorites(code) {
    favorites = favorites.includes(code) ? favorites.filter(value => value !== code) : [...favorites, code];
    try { storage.setItem(FAVORITES_KEY, JSON.stringify(favorites)); } catch { notify('Não foi possível salvar os favoritos neste navegador.'); }
    if (current?.code === code) detail(code);
    else if (favoritesOnly && !favorites.includes(code)) gallery();
    else {
      const old = main.querySelector(`[data-fx-card="${CSS.escape(code)}"]`), effect = find(code);
      if (old && effect) { const holder = document.createElement('div'); holder.innerHTML = card(effect); old.replaceWith(holder.firstElementChild); mountVisible(); }
      const count = main.querySelector('#fx-favorite-count'); if (count) count.textContent = String(favorites.length);
    }
  }
  function onInput(event) {
    if (event.target.matches('[data-fx-search]')) {
      query = event.target.value;
      const position = event.target.selectionStart;
      gallery();
      const input = main.querySelector('[data-fx-search]'); input?.focus(); input?.setSelectionRange(position, position);
    } else if (event.target.matches('[data-fx-text],[data-fx-accent]') && current) {
      const canvas = main.querySelector('[data-fx-canvas]'), item = active.get(canvas);
      if (canvas) renderFrame(canvas, current, item?.time ?? stillTime(current), demoOptions(current));
    } else if (event.target.matches('[data-fx-scrub]') && current) {
      const canvas = main.querySelector('[data-fx-canvas]'), item = active.get(canvas), time = Number(event.target.value);
      if (item) { item.running = false; item.time = time; }
      overrides.set(current.code, false);
      if (canvas) renderFrame(canvas, current, time, demoOptions(current));
      if (![...active.values()].some(value => value.running)) cancelLoop();
      updatePlaybackButtons();
    }
  }
  async function onClick(event) {
    const target = event.target.closest('[data-fx-category],[data-fx-favorites],[data-fx-autoplay],[data-fx-favorite],[data-fx-copy],[data-fx-copy-prompt],[data-fx-play],[data-fx-reset],[data-fx-toggle],[data-fx-restart]');
    if (!target || !main.contains(target)) return;
    if (target.hasAttribute('data-fx-category')) { category = target.dataset.fxCategory; gallery(); }
    else if (target.hasAttribute('data-fx-favorites')) { favoritesOnly = !favoritesOnly; gallery(); }
    else if (target.hasAttribute('data-fx-autoplay')) {
      globalPlaying = !globalPlaying; overrides.clear();
      for (const [canvas, item] of active) {
        item.running = globalPlaying; item.time = globalPlaying ? 0 : stillTime(item.effect); item.started = globalPlaying ? performance.now() : 0;
        if (!globalPlaying) renderFrame(canvas, item.effect, item.time, canvas.closest('.fx-detail-media') ? demoOptions(item.effect) : {});
      }
      if (globalPlaying) scheduleLoop(); else cancelLoop();
      const button = main.querySelector('[data-fx-autoplay]'); if (button) { button.setAttribute('aria-pressed', String(globalPlaying)); button.title = `${globalPlaying ? 'Pausar' : 'Reproduzir'} prévias`; button.innerHTML = `${icon(globalPlaying ? 'pause' : 'play')}<span>${globalPlaying ? 'Pausar prévias' : 'Reproduzir prévias'}</span>`; }
      updatePlaybackButtons();
    } else if (target.hasAttribute('data-fx-favorite')) updateFavorites(target.dataset.fxFavorite);
    else if (target.hasAttribute('data-fx-copy') || target.hasAttribute('data-fx-copy-prompt')) {
      const field = target.hasAttribute('data-fx-copy-prompt') ? main.querySelector('[data-fx-prompt]') : null;
      const effect = find(target.dataset.fxCopy || target.closest('[data-fx-copy-prompt]')?.dataset.fxCopyPrompt || current?.code);
      if (effect) { const text = field ? field.value : promptFor(effect); await copyText(text, field); }
    } else if (target.hasAttribute('data-fx-play')) setPlayback(target.dataset.fxPlay, !isPlaying(target.dataset.fxPlay));
    else if (target.hasAttribute('data-fx-reset')) { query = ''; category = 'all'; favoritesOnly = false; gallery(); }
    else if (target.hasAttribute('data-fx-toggle') && current) setPlayback(current.code, !isPlaying(current.code));
    else if (target.hasAttribute('data-fx-restart') && current) setPlayback(current.code, true, { restart: true });
  }
  function onKeydown(event) {
    if (event.key !== '/' || event.metaKey || event.ctrlKey || event.altKey) return;
    const target = event.target;
    if (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)) return;
    const input = main.querySelector('[data-fx-search]');
    if (input) { event.preventDefault(); input.focus(); }
  }
  function onVisibility() {
    if (document.hidden) cancelLoop();
    else { for (const item of active.values()) if (item.running) item.started = performance.now() - item.time * 1000; scheduleLoop(); }
  }
  function onReducedMotion(event) {
    globalPlaying = !event.matches; overrides.clear();
    for (const [canvas, item] of active) {
      item.running = globalPlaying; item.time = globalPlaying ? 0 : stillTime(item.effect); item.started = globalPlaying ? performance.now() : 0;
      if (!globalPlaying) renderFrame(canvas, item.effect, item.time, canvas.closest('.fx-detail-media') ? demoOptions(item.effect) : {});
    }
    if (globalPlaying) scheduleLoop(); else cancelLoop();
    updatePlaybackButtons();
    const button = main.querySelector('[data-fx-autoplay]');
    if (button) { button.setAttribute('aria-pressed', String(globalPlaying)); button.title = `${globalPlaying ? 'Pausar' : 'Reproduzir'} prévias`; button.innerHTML = `${icon(globalPlaying ? 'pause' : 'play')}<span>${globalPlaying ? 'Pausar prévias' : 'Reproduzir prévias'}</span>`; }
  }
  return {
    gallery,
    detail,
    destroy() { destroyed = true; deactivate(); }
  };
}
