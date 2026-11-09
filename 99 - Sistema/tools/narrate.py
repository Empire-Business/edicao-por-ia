#!/usr/bin/env python3
"""Narration: OpenRouter TTS by default (paid, explicit --accept-paid), or local Cortez Voz / VoiceStudio / macOS voices.

ElevenLabs no longer narrates (owner decision, 09/11/2026). Word timings always come from local alignment (align).
"""
from __future__ import annotations
import argparse
import json
import math
import os
import platform
import sys
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
try:
    import requests
except ImportError:  # instalado pela capacidade base; só a voz local precisa dele aqui
    requests = None
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
    if requests is None: raise ValueError('Falta o pacote requests no Python do Cortez. A IA deve rodar factory.py dependencies --capability base --apply e tentar de novo.')
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


OPENROUTER_TTS_MODEL = 'google/gemini-3.8-flash-tts'
OPENROUTER_TTS_VOICE = 'Kore'
OPENROUTER_TTS_INSTRUCTIONS = 'Fale em português do Brasil, tom natural, claro e próximo.'
PROVIDERS = ('openrouter', 'cortez-voz', 'voicestudio', 'macos')
ELEVENLABS_RETIRED = ('A narração pelo ElevenLabs foi desligada em 09/11/2026: o ElevenLabs agora só trata ruído. '
                      'Use --provider openrouter (padrão; pago, com o sim da pessoa e --accept-paid) '
                      'ou uma voz local sem custo (--provider cortez-voz ou macos).')
OPENROUTER_PAID = ('Narração pelo OpenRouter é paga: custo estimado de frações de centavo de dólar por trecho curto '
                   '(o preço exato por token está na lista de modelos da OpenRouter). Mostre o custo, peça o sim da pessoa '
                   'para esta narração e rode de novo com --accept-paid. Sem gasto: --provider cortez-voz ou macos.')
PCM_TYPES = ('audio/pcm', 'audio/l16')
SUFFIXES = {'audio/mpeg': '.mp3', 'audio/mp3': '.mp3', 'audio/wav': '.wav', 'audio/x-wav': '.wav', 'audio/wave': '.wav',
            'audio/flac': '.flac', 'audio/ogg': '.ogg', 'audio/opus': '.opus', 'audio/aac': '.aac'}


def pcm_input(content_type):
    """FFmpeg input options for raw PCM (Gemini sends 16-bit little-endian, 24 kHz, mono)."""
    params = {}
    for part in content_type.split(';')[1:]:
        name, sep, value = part.partition('=')
        if sep: params[name.strip().lower()] = value.strip()
    try:
        rate, channels = int(params.get('rate', 24000)), int(params.get('channels', 1))
    except ValueError:
        raise ValueError('A OpenRouter devolveu um formato de áudio inesperado; nada foi salvo.') from None
    if not 8000 <= rate <= 192000 or channels not in (1, 2):
        raise ValueError('A OpenRouter devolveu um formato de áudio inesperado; nada foi salvo.')
    return ['-f', 's16le', '-ar', str(rate), '-ac', str(channels)]


def openrouter_payload(text, voice, model, speed, instructions):
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._:-]*', model or ''):
        raise ValueError('Modelo de fala inválido; use o id da OpenRouter, como google/gemini-3.8-flash-tts.')
    payload = {'model': model, 'input': text, 'voice': voice,
               # Gemini TTS only returns raw PCM; other speech models return MP3.
               'response_format': 'pcm' if model.startswith('google/') else 'mp3'}
    if instructions is None and model.startswith('google/'):
        instructions = OPENROUTER_TTS_INSTRUCTIONS
    if instructions:
        if len(instructions) > 1000: raise ValueError('Instruções de fala muito longas; use até 1000 caracteres.')
        payload['instructions'] = instructions
    if speed != 1:
        payload['speed'] = speed
    return payload


def speak(text_file, output, voice=None, provider='openrouter', model=None, speed=1.0,
          base_url='http://127.0.0.1:3930', accept_paid=False, root=ROOT, instructions=None):
    if provider == 'elevenlabs': raise ValueError(ELEVENLABS_RETIRED)
    if provider not in PROVIDERS: raise ValueError('Provedor desconhecido.')
    if provider == 'openrouter':
        model = model or OPENROUTER_TTS_MODEL
        if not voice:
            if model != OPENROUTER_TTS_MODEL:
                raise ValueError('Escolha a voz deste modelo com --voice (alguns modelos exigem uma voz explícita).')
            voice = OPENROUTER_TTS_VOICE
        if not accept_paid: raise ValueError(OPENROUTER_PAID)
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
    payload = openrouter_payload(text, voice, model, speed, instructions) if provider == 'openrouter' else None
    remote = {}
    with tempfile.TemporaryDirectory(prefix='.narration-', dir=target.parent) as folder:
        tmp = Path(folder); raw = tmp / 'voice.wav'; decode = []
        if provider in ('cortez-voz', 'voicestudio'):
            voicestudio('/v1/audio/speech', base_url, {'model': model, 'voice': voice,
                        'input': text, 'language': 'pt', 'response_format': 'wav', 'speed': speed}, raw)
        elif provider == 'macos':
            if platform.system() != 'Darwin': raise ValueError('A voz do macOS só está disponível no Mac.')
            raw = tmp / 'voice.aiff'
            run(['/usr/bin/say', '-v', voice, '-r', str(round(175 * speed)), '-f', source, '-o', raw], 600)
        else:
            from audio_remote import openrouter_speech
            raw = tmp / 'voice.raw'
            remote = openrouter_speech(payload, raw)  # the only paid step; never repeated here
            kind = remote['content_type'].split(';')[0].strip().lower()
            if kind in PCM_TYPES:
                decode = pcm_input(remote['content_type'])
            else:
                raw = raw.rename(tmp / ('voice' + SUFFIXES.get(kind, '.bin')))
        if not decode: probe(raw)
        converted = tmp / ('output.' + fmt)
        run(['ffmpeg', '-v', 'error', '-nostdin', '-n', *decode, '-i', raw, converted])
        info = probe(converted)
        evidence = {'schema_version': 1, 'provider': provider, 'model': model, 'voice': voice,
                    'text_sha256': digest(source), 'output': str(target), 'output_sha256': digest(converted),
                    'duration': info['duration'], 'paid_request': provider == 'openrouter', 'cloud_fallback': False,
                    'alignment': 'pending_local_transcription', 'quality_review': 'pending_listening'}
        if provider == 'openrouter':
            evidence.update({'instructions': payload.get('instructions'), 'response_format': payload['response_format'],
                             'provider_content_type': remote['content_type'], 'generation_id': remote.get('generation_id'),
                             'cost_usd': None, 'cost_note': 'A resposta de fala não traz o custo; consulte https://openrouter.ai/activity pelo generation_id.'})
        publish(converted, target); receipt(sidecar, evidence, root)
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
        # 'elevenlabs' stays accepted by the parser only to explain that it was retired.
        p.add_argument('--provider', choices=[*PROVIDERS, 'elevenlabs'], default='openrouter')
        p.add_argument('--url', default='http://127.0.0.1:3930')
    voices.add_argument('--lang', default='pt')
    sp.add_argument('--text-file', required=True); sp.add_argument('--out', required=True)
    sp.add_argument('--voice'); sp.add_argument('--model'); sp.add_argument('--instructions')
    sp.add_argument('--speed', type=float, default=1); sp.add_argument('--accept-paid', action='store_true')
    a = ap.parse_args()
    try:
        if a.command == 'align': result = align(a.audio, a.backend, a.model, a.language)
        elif a.command == 'speak': result = speak(a.text_file, a.out, a.voice, a.provider, a.model, a.speed, a.url,
                                                  a.accept_paid, instructions=a.instructions)
        elif a.provider == 'elevenlabs': raise ValueError(ELEVENLABS_RETIRED)
        elif a.provider == 'openrouter':
            result = {'provider': 'openrouter', 'default_model': OPENROUTER_TTS_MODEL, 'default_voice': OPENROUTER_TTS_VOICE,
                      'default_instructions': OPENROUTER_TTS_INSTRUCTIONS, 'paid': True,
                      'note': 'A OpenRouter não lista vozes por API. Kore é a voz padrão verificada no Gemini; '
                              'outros modelos (ex.: fish-audio/s2.1-pro, microsoft/mai-voice-2.1, elevenlabs/eleven-multilingual-v2) '
                              'são escolhidos com --model e alguns exigem --voice explícita.'}
        elif a.provider in ('cortez-voz', 'voicestudio'): result = voicestudio('/v1/audio/voices', a.url)
        else:
            raw, _ = run(['/usr/bin/say', '-v', '?'], 20)
            result = [line for line in raw.decode().splitlines() if not a.lang or a.lang in line]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc: ap.exit(2, str(exc) + '\n')


if __name__ == '__main__': main()
