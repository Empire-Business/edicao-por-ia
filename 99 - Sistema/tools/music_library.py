#!/usr/bin/env python3
"""Private portable library of licensed tracks. No generation or paid calls."""
import argparse
import json
import math
from pathlib import Path
import shutil
import tempfile
from audio_local import ROOT, probe, output_path, run, publish, receipt
from factory_common import ident
from workspace_files import resolve_file, digest


def library(root=ROOT):
    return resolve_file(Path(root) / 'context/audio-library', root, False)


def add(source, track_id, title, license_note, rights_confirmed=False, root=ROOT):
    ident(track_id, 'trilha')
    if not rights_confirmed or not license_note.strip() or not title.strip():
        raise ValueError('Informe título, licença/origem e confirme o direito de reutilizar a trilha.')
    source = resolve_file(source, root); probe(source)
    base = library(root) / track_id; base.mkdir(parents=True, exist_ok=False)
    try:
        target = base / ('original' + source.suffix.lower())
        with target.open('xb') as out, source.open('rb') as src: shutil.copyfileobj(src, out)
        if digest(target) != digest(source): raise ValueError('Cópia da trilha não confere.')
        data = {'id': track_id, 'title': title, 'license': license_note, 'rights_confirmed_by_user': True,
                'file': target.name, 'sha256': digest(target)}
        receipt(base / 'track.json', data, root); return data
    except Exception:
        shutil.rmtree(base)  # Directory created exclusively above by this operation.
        raise


def tracks(root=ROOT):
    return [json.loads(p.read_text()) for p in sorted(library(root).glob('*/track.json'))]


def prepare(track_id, output, seconds, root=ROOT):
    ident(track_id, 'trilha')
    if not math.isfinite(seconds) or not .1 <= seconds <= 14400: raise ValueError('Duração inválida (0.1 a 14400 segundos).')
    base = library(root) / track_id; data = json.loads((base / 'track.json').read_text())
    source = resolve_file(base / data['file'], root)
    if not source.is_relative_to(base) or not data.get('rights_confirmed_by_user') or digest(source) != data['sha256']:
        raise ValueError('Licença ou integridade da trilha não confirmada.')
    target = output_path(output, root)
    if target.suffix.lower() not in ('.wav', '.mp3', '.flac'): raise ValueError('Use WAV, MP3 ou FLAC.')
    sidecar = target.with_suffix('.audio.json')
    if sidecar.exists(): raise ValueError('Recibo já existe; escolha outra versão.')
    fade = min(3, seconds / 2)
    with tempfile.TemporaryDirectory(prefix='.music-', dir=target.parent) as folder:
        result = Path(folder) / target.name
        run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-stream_loop', '-1', '-i', source,
             '-t', str(seconds), '-af', f'loudnorm=I=-20:TP=-2:LRA=7,afade=t=out:st={seconds-fade}:d={fade}', result], max(120, seconds * 2))
        info = probe(result)
        if abs(info['duration'] - seconds) > .1: raise ValueError('Duração da trilha não confere.')
        evidence = {'provider': 'local-library', 'track': track_id, 'license': data['license'],
                    'source_sha256': data['sha256'], 'output_sha256': digest(result), 'duration': info['duration'],
                    'paid_request': False, 'looped': seconds > probe(source)['duration'], 'quality_review': 'pending_listening'}
        publish(result, target); receipt(sidecar, evidence, root)
    return evidence


def main():
    ap = argparse.ArgumentParser(description=__doc__); sub = ap.add_subparsers(dest='command', required=True)
    sub.add_parser('list'); a = sub.add_parser('add'); a.add_argument('source'); a.add_argument('--id', required=True)
    a.add_argument('--title', required=True); a.add_argument('--license', required=True); a.add_argument('--rights-confirmed', action='store_true')
    p = sub.add_parser('prepare'); p.add_argument('--track', required=True); p.add_argument('--out', required=True); p.add_argument('--seconds', type=float, required=True)
    a = ap.parse_args()
    try:
        if a.command == 'add': result = add(a.source, a.id, a.title, a.license, a.rights_confirmed)
        elif a.command == 'prepare': result = prepare(a.track, a.out, a.seconds)
        else: result = tracks()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc: ap.exit(2, str(exc) + '\n')


if __name__ == '__main__': main()
