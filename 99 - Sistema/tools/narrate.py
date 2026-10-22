#!/usr/bin/env python3
"""Local VoiceStudio / macOS narration, or explicitly authorized paid TTS."""
from __future__ import annotations
import argparse
import base64
import json
import math
import os
import platform
import sys
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
import requests
from audio_local import ROOT, run, probe, output_path, publish, receipt
from workspace_files import resolve_file, digest

# OpenAI aliases and 'omnivoice' use VoiceStudio's active backend (possibly
# remote). Only explicit local engines are allowed through the local adapter.
LOCAL_ENGINES = {'omnivoice-subprocess', 'cosyvoice', 'mlx-audio', 'voxcpm2', 'kittentts',
                 'moss-tts-nano', 'supertonic3', 'pockettts'}


def local_url(value):
    u = urlsplit(value)
    if (u.scheme != 'http' or u.hostname not in ('127.0.0.1', '::1') or u.username or u.password
            or u.path not in ('', '/') or u.query or u.fragment or not u.port):
        raise ValueError('VoiceStudio precisa de HTTP local (127.0.0.1 ou ::1), com porta e sem credenciais.')
    return value.rstrip('/')


def voicestudio(endpoint, base_url, payload=None, output=None):
    url = local_url(base_url) + endpoint
    with requests.Session() as session:
        session.trust_env = False
        try:
            with session.request('POST' if payload else 'GET', url, json=payload,
                                 timeout=(3, 600), allow_redirects=False, stream=True) as response:
                if response.status_code != 200:
                    raise ValueError(f'VoiceStudio local HTTP {response.status_code}; confira o aplicativo e o modelo instalado.')
                if output:
                    size = 0
                    with Path(output).open('xb') as stream:
                        for chunk in response.iter_content(1024 * 1024):
                            size += len(chunk)
                            if size > 128 * 1024 * 1024: raise ValueError('Áudio excedeu 128 MB.')
                            stream.write(chunk)
                    return
                return response.json()
        except requests.RequestException:
            raise ValueError('VoiceStudio local indisponível. Abra o aplicativo com o modelo preparado; nenhum serviço pago foi chamado.') from None


def speak(text_file, output, voice, provider='cortez-voz', model=None, speed=1.0,
          base_url='http://127.0.0.1:3930', accept_paid=False, root=ROOT):
    if provider not in ('cortez-voz', 'voicestudio', 'macos', 'elevenlabs'): raise ValueError('Provedor desconhecido.')
    if provider == 'elevenlabs' and not accept_paid:
        raise ValueError('ElevenLabs é opcional e pago; falta autorização explícita para esta chamada.')
    if provider in ('cortez-voz', 'voicestudio'):
        local_url(base_url)
        if model not in LOCAL_ENGINES:
            raise ValueError('Escolha um engine local explícito com --model; aliases do backend ativo não são permitidos.')
    if not voice or len(voice) > 160 or '\n' in voice: raise ValueError('Escolha uma voz válida.')
    if not math.isfinite(speed) or not .5 <= speed <= 2: raise ValueError('Velocidade deve ficar entre 0.5 e 2.')
    if provider == 'cortez-voz':
        identity = voicestudio('/cortez/identity', base_url)
        if identity.get('distribution') != 'Empire-Business/cortez-voz':
            raise ValueError('A porta local não pertence ao Cortez Voz da Empire-Business.')
    source = resolve_file(text_file, root)
    text = source.read_text(encoding='utf-8').strip()
    if not text or len(text) > 10000: raise ValueError('Use entre 1 e 10000 caracteres por trecho.')
    target = output_path(output, root)
    fmt = target.suffix.lstrip('.').lower()
    if fmt not in ('wav', 'mp3', 'flac'): raise ValueError('Use WAV, MP3 ou FLAC.')
    sidecar = target.with_suffix('.audio.json')
    if sidecar.exists() or target.with_suffix('.words.json').exists(): raise ValueError('Recibos já existem; escolha outra versão.')
    words = None
    with tempfile.TemporaryDirectory(prefix='.narration-', dir=target.parent) as folder:
        tmp = Path(folder); raw = tmp / 'voice.wav'
        if provider in ('cortez-voz', 'voicestudio'):
            voicestudio('/v1/audio/speech', base_url, {'model': model, 'voice': voice,
                        'input': text, 'language': 'pt', 'response_format': 'wav', 'speed': speed}, raw)
        elif provider == 'macos':
            if platform.system() != 'Darwin': raise ValueError('A voz do macOS só está disponível no Mac.')
            raw = tmp / 'voice.aiff'
            run(['/usr/bin/say', '-v', voice, '-r', str(round(175 * speed)), '-f', source, '-o', raw], 600)
        else:
            from audio_remote import eleven_request
            if not re.fullmatch(r'[A-Za-z0-9_-]+', voice): raise ValueError('ID de voz inválido.')
            if not model: raise ValueError('Escolha o modelo ElevenLabs explicitamente.')
            result = eleven_request(f'/v1/text-to-speech/{voice}/with-timestamps', payload={
                'text': text, 'model_id': model, 'voice_settings': {'speed': speed}})
            raw = tmp / 'voice.mp3'; raw.write_bytes(base64.b64decode(result['audio_base64'], validate=True))
            al = result.get('alignment') or {}; words, current = [], None
            for char, start, end in zip(al.get('characters', []), al.get('character_start_times_seconds', []), al.get('character_end_times_seconds', [])):
                if char.isspace(): current = None; continue
                if current is None:
                    current = {'word': '', 'start': start, 'end': end}; words.append(current)
                current['word'] += char; current['end'] = end
        probe(raw)
        converted = tmp / ('output.' + fmt)
        run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', raw, converted])
        info = probe(converted)
        evidence = {'schema_version': 1, 'provider': provider, 'model': model, 'voice': voice,
                    'text_sha256': digest(source), 'output': str(target), 'output_sha256': digest(converted),
                    'duration': info['duration'], 'paid_request': provider == 'elevenlabs', 'cloud_fallback': False,
                    'alignment': 'available' if words else 'pending_local_transcription', 'quality_review': 'pending_listening'}
        publish(converted, target); receipt(sidecar, evidence, root)
        if words: receipt(target.with_suffix('.words.json'), {'words': words, 'text': text, 'provider': provider}, root)
    return evidence


def align(audio_file, backend, model, language='pt', root=ROOT):
    """Align actual generated speech with a cached local ASR model, without regenerating it."""
    if backend not in ('mlx', 'faster') or not model:
        raise ValueError('Escolha o backend e o modelo de transcrição local já preparado.')
    source = resolve_file(audio_file, root)
    target = output_path(source.with_suffix('.words.json'), root)
    alignment_receipt = source.with_suffix('.alignment.json')
    if alignment_receipt.exists(): raise ValueError('Alinhamento já existe; preserve a versão anterior.')
    duration = probe(source)['duration']
    with tempfile.TemporaryDirectory(prefix='.alignment-', dir=source.parent) as folder:
        transcript = Path(folder) / 'transcript.json'
        env = dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1')
        run([sys.executable, ROOT/'tools/transcribe.py', source, '--output', transcript,
             '--backend', backend, '--model', model, '--language', language], max(120, duration * 20), env=env)
        data = json.loads(transcript.read_text())
        words = [word for segment in data.get('segments', []) for word in segment.get('words', [])]
        previous = 0
        for word in words:
            start, end = float(word['start']), float(word['end'])
            if not (math.isfinite(start) and math.isfinite(end) and previous <= start <= end <= duration + .1):
                raise ValueError('Tempos de palavras inconsistentes; confira a transcrição local.')
            previous = start
        if not words: raise ValueError('O transcritor não retornou tempos reais por palavra.')
        receipt(target, {'text': data.get('text', ''), 'words': words, 'backend': data['backend'],
                         'model': model, 'audio_sha256': digest(source)}, root)
        receipt(alignment_receipt, {'status': 'available', 'audio_sha256': digest(source),
                                   'backend': data['backend'], 'model': model, 'words': len(words), 'offline': True}, root)
    return {'alignment': 'available', 'words': len(words), 'paid_request': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__); sub = ap.add_subparsers(dest='command', required=True)
    voices = sub.add_parser('voices'); sp = sub.add_parser('speak')
    al = sub.add_parser('align'); al.add_argument('audio'); al.add_argument('--backend', choices=['mlx', 'faster'], required=True)
    al.add_argument('--model', required=True); al.add_argument('--language', default='pt')
    for p in (voices, sp):
        p.add_argument('--provider', choices=['cortez-voz', 'voicestudio', 'macos', 'elevenlabs'], default='cortez-voz')
        p.add_argument('--url', default='http://127.0.0.1:3930')
    voices.add_argument('--lang', default='pt')
    sp.add_argument('--text-file', required=True); sp.add_argument('--out', required=True)
    sp.add_argument('--voice', required=True); sp.add_argument('--model')
    sp.add_argument('--speed', type=float, default=1); sp.add_argument('--accept-paid', action='store_true')
    a = ap.parse_args()
    try:
        if a.command == 'align': result = align(a.audio, a.backend, a.model, a.language)
        elif a.command == 'speak': result = speak(a.text_file, a.out, a.voice, a.provider, a.model, a.speed, a.url, a.accept_paid)
        elif a.provider in ('cortez-voz', 'voicestudio'): result = voicestudio('/v1/audio/voices', a.url)
        elif a.provider == 'macos':
            raw, _ = run(['/usr/bin/say', '-v', '?'], 20)
            result = [line for line in raw.decode().splitlines() if not a.lang or a.lang in line]
        else:
            from audio_remote import eleven_request
            result = eleven_request('/v2/voices', method='GET')
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc: ap.exit(2, str(exc) + '\n')


if __name__ == '__main__': main()
