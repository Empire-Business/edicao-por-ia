import { icon } from './icons.js';

let sdk;
function vimeoSDK() {
  if (window.Vimeo?.Player) return Promise.resolve(window.Vimeo.Player);
  if (!sdk) sdk = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://player.vimeo.com/api/player.js';
    script.onload = () => window.Vimeo?.Player ? resolve(window.Vimeo.Player) : reject(Error('Player indisponível'));
    script.onerror = () => reject(Error('Player indisponível'));
    document.head.append(script);
  });
  return sdk;
}

export class PreviewManager {
  constructor({ autoplay = true, notify = () => {} } = {}) {
    this.autoplay = autoplay; this.notify = notify; this.players = new Map(); this.destroyed = false;
    this.observer = new IntersectionObserver(entries => entries.forEach(entry => {
      const record = this.players.get(entry.target);
      if (!record) return;
      record.visible = entry.isIntersecting;
      if (record.visible) { this.load(record); this.resume(record); }
      else this.pause(record, true);
    }), { threshold: 0.16 });
    this.visibility = () => this.players.forEach(record => document.hidden ? this.pause(record, true) : this.resume(record));
    document.addEventListener('visibilitychange', this.visibility);
  }

  mount(container, format, { detail = false } = {}) {
    const record = { container, format, detail, player: null, type: null, visible: false, muted: true,
      paused: !this.autoplay, blocked: false, loaded: false, generation: 0 };
    this.players.set(container, record);
    const controls = container.querySelector('.media-controls');
    if (!format.video && !format.vimeo) { controls?.remove(); return; }
    controls.querySelector('[data-sound]').addEventListener('click', () => this.toggleSound(record));
    controls.querySelector('[data-play]').addEventListener('click', () => this.togglePlay(record));
    this.observer.observe(container);
  }

  updateControls(record) {
    if (this.destroyed) return;
    const play = record.container.querySelector('[data-play]');
    const sound = record.container.querySelector('[data-sound]');
    const isPaused = record.paused || record.blocked;
    play.innerHTML = icon(isPaused ? 'play' : 'pause');
    play.setAttribute('aria-label', `${isPaused ? 'Reproduzir' : 'Pausar'} ${record.format.name}`);
    play.setAttribute('title', `${isPaused ? 'Reproduzir' : 'Pausar'} prévia`);
    sound.innerHTML = icon(record.muted ? 'mute' : 'sound');
    sound.setAttribute('aria-label', `${record.muted ? 'Ativar' : 'Desativar'} som de ${record.format.name}`);
    sound.setAttribute('aria-pressed', String(!record.muted));
    sound.setAttribute('title', record.muted ? 'Ativar som' : 'Desativar som');
    record.container.classList.toggle('has-sound', !record.muted);
  }

  async load(record) {
    if (record.loaded || this.destroyed) return;
    record.loaded = true;
    if (record.format.vimeo) {
      try {
        record.type = 'vimeo';
        const Player = await vimeoSDK();
        if (this.destroyed) return;
        const iframe = document.createElement('iframe');
        const params = new URLSearchParams({ autoplay: '0', loop: '1', muted: '1', autopause: '0', controls: record.detail ? '1' : '0', title: '0', byline: '0', portrait: '0', dnt: '1', playsinline: '1' });
        const reference = record.format.vimeo;
        if (reference.hash) params.set('h', reference.hash);
        iframe.src = `https://player.vimeo.com/video/${reference.id}?${params}`;
        iframe.title = `Exemplo em vídeo de ${record.format.name}`;
        iframe.allow = 'autoplay; fullscreen; picture-in-picture'; iframe.allowFullscreen = true;
        record.container.querySelector('.media-stage').append(iframe);
        record.player = new Player(iframe);
        record.timeout = setTimeout(() => this.localFallback(record), 12000);
        await record.player.ready();
        clearTimeout(record.timeout);
        if (this.destroyed || record.type !== 'vimeo') return;
        record.player.on('play', () => { record.container.classList.add('is-playing'); });
        record.player.on('error', () => this.localFallback(record));
        this.resume(record);
      } catch { this.localFallback(record); }
    } else this.localFallback(record);
  }

  localFallback(record) {
    if (this.destroyed || record.type === 'local') return;
    clearTimeout(record.timeout);
    record.player?.destroy?.().catch(() => {});
    record.container.querySelector('iframe')?.remove();
    record.type = 'local';
    const video = document.createElement('video');
    video.src = record.format.video; video.poster = record.format.poster;
    video.muted = true; video.defaultMuted = true; video.playsInline = true; video.loop = true;
    video.preload = 'metadata'; video.controls = record.detail;
    video.setAttribute('aria-label', `Exemplo em vídeo de ${record.format.name}`);
    video.addEventListener('loadeddata', () => record.container.classList.add('has-media-frame'));
    video.addEventListener('playing', () => { record.paused = false; record.blocked = false; record.container.classList.add('is-playing'); this.updateControls(record); });
    video.addEventListener('volumechange', () => {
      record.muted = video.muted || video.volume === 0;
      if (!record.muted) this.silenceOthers(record);
      this.updateControls(record);
    });
    video.addEventListener('pause', () => {
      record.container.classList.remove('is-playing');
      if (record.visible && !document.hidden && !this.destroyed) record.paused = true;
      this.updateControls(record);
    });
    video.addEventListener('error', () => {
      record.container.classList.remove('has-media-frame');
      record.blocked = true; this.updateControls(record);
      const message = document.createElement('p'); message.className = 'media-error';
      message.textContent = 'Prévia indisponível. Você ainda pode consultar o guia e escolher este modelo.';
      record.container.querySelector('.media-error')?.remove(); record.container.append(message);
    });
    record.player = video; record.container.querySelector('.media-stage').append(video);
    this.resume(record);
  }

  async resume(record) {
    if (!record.player || !record.visible || document.hidden || record.paused || this.destroyed) return;
    try { await record.player.play(); record.blocked = false; }
    catch { record.blocked = true; }
    this.updateControls(record);
  }

  pause(record, silence = false) {
    if (record.player) {
      if (record.type === 'vimeo') record.player.pause().catch(() => {});
      else record.player.pause();
    }
    if (silence) this.mute(record);
  }

  mute(record) {
    record.muted = true;
    if (record.type === 'vimeo') record.player?.setMuted(true).catch(() => {});
    else if (record.player) record.player.muted = true;
    this.updateControls(record);
  }

  silenceOthers(record) { this.players.forEach(other => { if (other !== record && !other.muted) this.mute(other); }); }

  async toggleSound(record) {
    if (!record.player) { await this.load(record); if (!record.player) return; }
    const muted = !record.muted;
    if (!muted) this.silenceOthers(record);
    try {
      if (record.type === 'vimeo') { await record.player.setMuted(muted); if (!muted) await record.player.setVolume(1); }
      else { record.player.muted = muted; if (!muted) record.player.volume = 1; }
      record.muted = muted;
      if (!muted) { record.paused = false; await this.resume(record); }
      this.updateControls(record);
    } catch { this.notify('O navegador não liberou o áudio. Abra os detalhes e use os controles do vídeo.'); }
  }

  async togglePlay(record) {
    const play = record.paused || record.blocked;
    record.paused = !play; record.blocked = false;
    if (play) { await this.load(record); await this.resume(record); }
    else this.pause(record, true);
    this.updateControls(record);
  }

  setAutoplay(value) {
    this.autoplay = value;
    this.players.forEach(record => {
      record.paused = !value; record.blocked = false;
      if (value) this.resume(record); else this.pause(record, true);
      this.updateControls(record);
    });
  }

  destroy() {
    this.observer.disconnect(); this.destroyed = true;
    document.removeEventListener('visibilitychange', this.visibility);
    this.players.forEach(record => {
      clearTimeout(record.timeout);
      if (record.type === 'vimeo') record.player?.destroy().catch(() => {});
      else if (record.player) { record.player.pause(); record.player.removeAttribute('src'); record.player.load(); }
    });
    this.players.clear();
  }
}
