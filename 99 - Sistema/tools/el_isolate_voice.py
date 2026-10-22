#!/usr/bin/env python3
"""Clean camera voice locally; ElevenLabs is an explicit paid option.

The FULL source audio is isolated first (mono, level-normalized, long real pauses give the
model context), and only then cut by the job EDL. Isolating the already-cut voice barely
removed noise (3-4 dB) while this order removes ~15 dB or more in the pauses.

usage: python3 tools/el_isolate_voice.py jobs/<id> --base-video renders/draft-v2.mp4 --out renders/draft-v4.mp4
Default auto selects DeepFilterNet when installed, else basic FFmpeg. No automatic paid fallback.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path
import math
import numpy as np
from audio_local import clean, cache_key, select_cleaner, run as bounded_run, probe, output_path, publish, receipt, ROOT
from workspace_files import resolve_file, digest
import tempfile
from edit_support import read_data
from factory_common import workspace_lock

FPS = 30
SR = 48000


def run(cmd):
    bounded_run(cmd, timeout=3600)


def load(path, extra=()):
    raw, _ = bounded_run(['ffmpeg', '-v', 'error', '-nostdin', '-i', path, *extra, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], 3600)
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def env(x, hop):
    m = len(x) // hop
    return np.sqrt((x[:m * hop].reshape(m, hop) ** 2).mean(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('job')
    ap.add_argument('--provider', choices=['auto', 'deepfilter', 'ffmpeg', 'elevenlabs'], default='auto')
    ap.add_argument('--accept-paid', action='store_true')
    ap.add_argument('--base-video', required=True, help='render whose picture is kept (relative to job)')
    ap.add_argument('--out', required=True, help='new render (relative to job)')
    ap.add_argument('--target-lufs', type=float, default=-16.7)
    ap.add_argument('--expander', action='store_true', help='gentle downward expander on the isolated voice')
    a = ap.parse_args()
    J = str(Path(a.job).resolve())
    destination = output_path(Path(J) / a.out)
    base_video = resolve_file(Path(J) / a.base_video, ROOT)
    if not destination.is_relative_to(Path(J)):
        ap.error('A saída precisa ficar dentro do trabalho.')
    if not math.isfinite(a.target_lufs) or not -30 <= a.target_lufs <= -10:
        ap.error('Loudness fora do intervalo permitido (-30 a -10 LUFS).')
    provider = select_cleaner(a.provider)
    if provider == 'elevenlabs' and not a.accept_paid:
        ap.error('ElevenLabs é opcional; confirme o gasto para esta chamada com --accept-paid.')
    manifest = read_data(f'{J}/job.yaml')
    if not (manifest.get('format') or manifest.get('client')):
        sys.exit('Informe ou cadastre o formato deste vídeo antes de editar.')
    if manifest.get('format') and manifest.get('client') and manifest['format'] != manifest['client']:
        sys.exit('O trabalho informa formatos diferentes; resolva o cadastro antes de editar.')
    if not manifest.get('visual_identity'):sys.exit('Escolha a ID visual deste vídeo antes de editar.')
    edl = read_data(f'{J}/edit/edl.json')
    segs = edl['segments']
    sources = {s['source'] for s in segs}
    if len(sources) != 1:
        sys.exit(f'expected one source, got {sources}')
    src = str(resolve_file(sources.pop(), ROOT))
    fps = float(edl.get('fps', FPS))
    if not math.isfinite(fps) or fps <= 0:
        ap.error('FPS inválido.')
    D = edl['total_frames'] / fps
    source_duration = probe(src)['duration']
    if not segs or any(not (0 <= s['in'] < s['out'] <= source_duration + .01) or s['frames'] <= 0 for s in segs):
        ap.error('EDL fora da duração da fonte.')
    if abs(sum(s['frames'] for s in segs) / fps - D) > 1 / fps:
        ap.error('Duração da EDL inconsistente.')
    el = str(resolve_file(Path(J) / 'renders/audio' / cache_key(src, provider), ROOT, False))
    os.makedirs(el, exist_ok=True)
    norm, iso = src, f'{el}/source-clean.wav'
    sidecar = Path(iso).with_suffix('.audio.json')
    cached = False
    with workspace_lock(ROOT, 'audio-'+Path(el).name):
        if Path(iso).exists():
            evidence = json.loads(sidecar.read_text()) if sidecar.is_file() else {}
            if evidence.get('output_sha256') != digest(Path(iso)) or evidence.get('source_sha256') != digest(Path(src)) or evidence.get('provider') != provider:
                ap.error('Cache de áudio inválido; preserve o arquivo e escolha uma nova versão de cache.')
            cached = True
        else:
            clean(src, iso, provider, a.accept_paid)

    x, y = load(norm), load(iso)
    # 3) codec delay of the returned mp3, from 1 ms envelopes
    hop = 48
    n = min(len(x), len(y))
    ex, ey = env(x[:n], hop), env(y[:n], hop)
    best = max(range(-min(60, len(ex)-1), min(60, len(ex)-1)+1), key=lambda s: float(np.dot(ex[max(0, -s):len(ex) - max(0, s)], ey[max(0, s):len(ey) - max(0, -s)])))
    if provider != 'elevenlabs': best = 0
    off = best / 1000.0  # isolated lags the source by `off` seconds when positive
    # 4) noise in the real pauses of the source, before/after
    report = {'source': src, 'codec_delay_ms': best, 'provider': provider, 'cached': cached,
              'paid_request': provider == 'elevenlabs' and not cached, 'quality_review': 'pending_listening'}
    sil_path = f'{J}/analysis/silence-regions.json'
    if os.path.exists(sil_path):
        sil = [s for s in json.load(open(sil_path))['silences'] if s['end'] - s['start'] >= 0.5]
        yy = y[max(0, best * 48):]
        ra = [db(x[int((s['start'] + .15) * SR):int((s['end'] - .15) * SR)]) for s in sil]
        rb = [db(yy[int((s['start'] + .15) * SR):int((s['end'] - .15) * SR)]) for s in sil if int((s['end'] - .15) * SR) < len(yy)]
        if ra and rb:
            report.update(pauses=len(sil), pause_noise_before_db=round(float(np.median(ra)), 1), pause_noise_after_db=round(float(np.median(rb)), 1))
    # 5) cut the isolated source with the EDL (same fades as master.py)
    f = ';'.join(f"[0:a]atrim={max(0, s['in'] + off):.4f}:{s['out'] + off:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
                 f"afade=t=out:st={max(0, s['frames'] / fps - 0.015):.4f}:d=0.015[a{i}]" for i, s in enumerate(segs))
    f += ';' + ''.join(f'[a{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=0:a=1[o]'
    stage = tempfile.TemporaryDirectory(prefix='.mix-', dir=destination.parent)
    cut = str(Path(stage.name) / 'cut.wav')
    run(['ffmpeg', '-v', 'error', '-y', '-i', iso, '-filter_complex', f, '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', cut])
    # 6) voice chain: HPF + (optional expander) + gain to target + peak limiter
    pre = 'highpass=f=70'
    if a.expander:
        pre += ',agate=threshold=0.006:ratio=2:range=0.18:attack=4:release=160:knee=6'
    _, measured = bounded_run(['ffmpeg', '-nostats', '-nostdin', '-i', cut, '-af', pre + ',ebur128', '-f', 'null', '-'], 3600)
    out = measured.decode(errors='replace')
    I = float([l for l in out.splitlines() if l.strip().startswith('I:')][-1].split()[1])
    g = max(-30, min(30, a.target_lufs - I)) if math.isfinite(I) and I > -69 else 0
    voice = str(Path(stage.name) / 'voice.wav')
    run(['ffmpeg', '-v', 'error', '-y', '-i', cut, '-af', f'{pre},volume={g:.2f}dB,alimiter=limit=0.84:attack=5:release=80:level=disabled,apad=whole_dur={D:.4f}',
         '-t', f'{D:.4f}', '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le', voice])
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(base_video), '-i', voice, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
         '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(Path(stage.name) / destination.name)])
    rendered = Path(stage.name) / destination.name
    if abs(probe(rendered)['duration'] - D) > max(.1, 2/fps):
        raise ValueError('A montagem mudou a duração; saída bloqueada.')
    report.update(out=str(destination), output_sha256=digest(rendered), gain_db=round(g, 2), expander=a.expander, duration=D)
    receipt_path = destination.with_suffix('.audio.json')
    if receipt_path.exists(): raise ValueError('Recibo da saída já existe.')
    publish(rendered, destination)
    receipt(receipt_path, report)
    stage.cleanup()
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    try: main()
    except (ValueError, OSError) as exc: sys.exit(str(exc))
