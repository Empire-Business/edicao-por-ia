#!/usr/bin/env python3
"""Generate one original, royalty-free instrumental cue with ElevenLabs Music (see method/EXTERNAL_SERVICES.md).

Paid call: explicit current consent required (--accept-paid). Prefer music_library.py for licensed local tracks.
The prompt describes instruments, mood, tempo and structure — never artists or song names.

usage: el_music.py --prompt "..." --seconds 180 --out context/clients/<format>/assets/music/<name>.mp3
"""
import argparse, sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))


ap = argparse.ArgumentParser()
ap.add_argument('--accept-paid', action='store_true')
ap.add_argument('--prompt', required=True); ap.add_argument('--seconds', type=float, required=True); ap.add_argument('--out', required=True)
a = ap.parse_args()
if not a.accept_paid:
    ap.error('ElevenLabs Music é opcional e pago. Prefira music_library.py; confirme o gasto antes de usar --accept-paid.')
import math
if not math.isfinite(a.seconds) or not 3 <= a.seconds <= 600:
    ap.error('Duração inválida; use entre 3 e 600 segundos.')
out = Path(a.out)
if out.exists():
    raise SystemExit(f'exists, not overwriting: {out}')
from audio_local import output_path, probe, publish, receipt
from audio_remote import eleven_request
from workspace_files import digest
import tempfile
out = output_path(out)
if out.suffix.lower() != '.mp3': ap.error('ElevenLabs Music requer saída .mp3.')
if out.with_suffix('.audio.json').exists(): ap.error('Recibo já existe; escolha outra versão.')
with tempfile.TemporaryDirectory(prefix='.music-', dir=out.parent) as folder:
    result = Path(folder) / 'music.mp3'
    eleven_request('/v1/music', result, payload={'prompt': a.prompt, 'music_length_ms': int(a.seconds * 1000),
                   'model_id': 'music_v1', 'force_instrumental': True})
    info = probe(result)
    publish(result, out)
    receipt(out.with_suffix('.audio.json'), {'provider': 'elevenlabs', 'paid_request': True,
            'duration': info['duration'], 'output_sha256': digest(result), 'quality_review': 'pending_listening'})
print(out)
