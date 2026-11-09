#!/usr/bin/env python3
"""Generate one original instrumental track with Google Lyria 3 on OpenRouter (see method/EXTERNAL_SERVICES.md).

Paid call: the person's current yes for this generation is required (--accept-paid); a filled key is not
consent. Prefer music_library.py for licensed local tracks; if OpenRouter fails, offer the library.
The prompt describes instruments, mood, tempo (BPM) and structure — never artists or song names.

usage:
  or_music.py --prompt "..." --seconds 60 --out context/clients/<format>/assets/music/<name>.mp3 --accept-paid
  or_music.py --check-key        # free check that the key is accepted; prints only limits/usage

Up to 30 s uses google/lyria-3-clip-preview (~30 s clip, US$ 0.04); longer uses google/lyria-3-pro-preview
(full song, US$ 0.08). Lyria does not respect the requested length: the result is cut to the requested
length with a fade-out. A shorter result is kept as is and reported, never stretched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_local import ROOT, run, probe, output_path, publish, receipt
from workspace_files import digest, portable

MODELS = {
    'google/lyria-3-clip-preview': {'alias': 'clip', 'usd': 0.04, 'max_seconds': 30},
    'google/lyria-3-pro-preview': {'alias': 'pro', 'usd': 0.08, 'max_seconds': 240},
}
ALIASES = {info['alias']: model for model, info in MODELS.items()}
MIN_SECONDS, MAX_SECONDS = 3, 240
SHORTER_TOLERANCE = 0.5  # seconds


def choose_model(seconds, model='auto'):
    if model == 'auto':
        model = 'google/lyria-3-clip-preview' if seconds <= 30 else 'google/lyria-3-pro-preview'
    model = ALIASES.get(model, model)
    if model not in MODELS:
        raise ValueError('Modelo de música desconhecido. Use auto, clip (até 30 s) ou pro (música completa).')
    if seconds > MODELS[model]['max_seconds']:
        raise ValueError('O modelo clip gera só trechos de cerca de 30 s; para mais tempo use pro (ou auto).')
    return model


def estimate(seconds, model='auto'):
    chosen = choose_model(seconds, model)
    return chosen, MODELS[chosen]['usd']


def check_seconds(seconds):
    if not math.isfinite(seconds) or not MIN_SECONDS <= seconds <= MAX_SECONDS:
        raise ValueError(f'Duração inválida: use entre {MIN_SECONDS} e {MAX_SECONDS} segundos. '
                         'Para vídeos mais longos, gere partes (por exemplo, tensão e virada) e junte na mixagem.')


def build_prompt(prompt, seconds):
    text = ' '.join((prompt or '').split())
    if len(text) < 8 or len(text) > 2000:
        raise ValueError('Descreva a música em 8 a 2000 caracteres: instrumentos, clima, BPM e estrutura, sem artistas ou músicas.')
    return f'{text.rstrip(".")}. Instrumental only, no vocals. Duration: about {round(seconds)} seconds.'


def refusal(seconds, model='auto'):
    chosen, usd = estimate(seconds, model)
    price = f'{usd:.2f}'.replace('.', ',')
    return (f'Música com IA pelo OpenRouter é paga: custo estimado US$ {price} ({chosen}). '
            'Mostre o custo, peça o sim da pessoa para esta geração e rode de novo com --accept-paid. '
            'Sem gasto: use a biblioteca local (tools/music_library.py).')


def generate(prompt, seconds, out, model='auto', fade=2.0, accept_paid=False, root=ROOT):
    check_seconds(seconds)
    chosen, usd = estimate(seconds, model)
    if not accept_paid:
        raise ValueError(refusal(seconds, model))
    if not math.isfinite(fade) or not 0 <= fade <= 10:
        raise ValueError('Fade-out deve ficar entre 0 e 10 segundos.')
    text = build_prompt(prompt, seconds)
    target = output_path(out, root)
    if target.suffix.lower() != '.mp3':
        raise ValueError('A música do OpenRouter é salva em .mp3; escolha um nome terminado em .mp3.')
    sidecar = target.with_suffix('.audio.json')
    if sidecar.exists():
        raise ValueError('Recibo já existe; escolha outra versão.')
    from audio_remote import openrouter_music
    with tempfile.TemporaryDirectory(prefix='.music-', dir=target.parent) as folder:
        tmp = Path(folder)
        result = openrouter_music(chosen, text)  # the only paid step; never repeated here
        raw = tmp / 'raw.mp3'
        raw.write_bytes(result['audio'])
        try:
            raw_duration = probe(raw)['duration']
            fade_used = 0.0
            if raw_duration > seconds + 0.05:
                fade_used = round(min(fade, seconds / 3), 3)
                final = tmp / 'final.mp3'
                filters = f'afade=t=out:st={seconds - fade_used:.3f}:d={fade_used:.3f}' if fade_used else 'anull'
                run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', raw, '-t', f'{seconds:.3f}', '-af', filters,
                     '-c:a', 'libmp3lame', '-b:a', '192k', final], max(120, seconds * 2))
            else:
                final = raw
            duration = probe(final)['duration']
        except ValueError:
            # Already paid: keep the untouched file so the spend is not lost.
            kept = target.with_name(target.stem + '-sem-corte.mp3')
            if not kept.exists():
                publish(raw, kept)
            raise ValueError(f'A música foi gerada, mas o corte local falhou. O arquivo original ficou em {kept.name}; '
                             'confira o FFmpeg antes de gerar de novo.') from None
        shorter = raw_duration < seconds - SHORTER_TOLERANCE
        evidence = {'schema_version': 1, 'provider': 'openrouter', 'model': chosen, 'paid_request': True,
                    'cost_usd': result['cost_usd'], 'estimated_cost_usd': usd, 'generation_id': result['generation_id'],
                    'prompt': text, 'prompt_sha256': hashlib.sha256(text.encode()).hexdigest(),
                    'requested_seconds': seconds, 'raw_duration': raw_duration, 'duration': duration,
                    'trimmed': final is not raw, 'fade_out_seconds': fade_used,
                    'shorter_than_requested': shorter, 'provider_text': result['text'],
                    'output': str(target), 'output_sha256': digest(final), 'cloud_fallback': False,
                    'quality_review': 'pending_listening'}
        publish(final, target)
        receipt(sidecar, evidence, root)
    if shorter:
        evidence['warning'] = (f'A música veio com {raw_duration:.1f} s, menos que os {seconds:g} s pedidos. '
                               'Não foi esticada: use em loop pela biblioteca, gere outra parte ou ajuste a edição.')
    return evidence


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check-key', action='store_true', help='confere a chave sem gerar nada (sem custo)')
    ap.add_argument('--accept-paid', action='store_true')
    ap.add_argument('--prompt'); ap.add_argument('--seconds', type=float); ap.add_argument('--out')
    ap.add_argument('--model', default='auto', help='auto, clip (até 30 s) ou pro (música completa)')
    ap.add_argument('--fade', type=float, default=2.0, help='fade-out em segundos no corte (padrão 2)')
    a = ap.parse_args()
    try:
        if a.check_key:
            from audio_remote import openrouter_key_status
            result = openrouter_key_status()
        else:
            if not a.prompt or a.seconds is None or not a.out:
                ap.error('Informe --prompt, --seconds e --out (ou use --check-key).')
            result = generate(a.prompt, a.seconds, a.out, a.model, a.fade, a.accept_paid)
            result = portable(result, ROOT)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        ap.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
