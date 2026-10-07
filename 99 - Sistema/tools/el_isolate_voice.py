#!/usr/bin/env python3
"""Clean the camera voice of a talking-head job with ElevenLabs Audio Isolation.

The FULL source audio is isolated first (mono, level-normalized, long real pauses give the
model context), and only then cut by the job EDL. Isolating the already-cut voice barely
removed noise (3-4 dB) while this order removes ~15 dB or more in the pauses.

usage: python3 tools/el_isolate_voice.py jobs/<id> --base-video renders/draft-v2.mp4 --out renders/draft-v4.mp4
Loads ELEVENLABS_API_KEY from the visible integration keys file (service_keys). Uploads the source AUDIO only (no video).
"""
import argparse, json, os, subprocess, sys
import numpy as np
import requests
from service_keys import api_key
from edit_support import read_data

FPS = 30
SR = 48000


def run(cmd):
    subprocess.run(cmd, check=True)


def load(path, extra=()):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, *extra, '-vn', '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def env(x, hop):
    m = len(x) // hop
    return np.sqrt((x[:m * hop].reshape(m, hop) ** 2).mean(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('job')
    ap.add_argument('--base-video', required=True, help='render whose picture is kept (relative to job)')
    ap.add_argument('--out', required=True, help='new render (relative to job)')
    ap.add_argument('--target-lufs', type=float, default=-16.7)
    ap.add_argument('--expander', action='store_true', help='gentle downward expander on the isolated voice')
    a = ap.parse_args()
    J = a.job.rstrip('/')
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
    src = sources.pop()
    D = edl['total_frames'] / FPS
    el = f'{J}/renders/el'
    os.makedirs(el, exist_ok=True)
    norm, iso = f'{el}/src-mono-norm.wav', f'{el}/src-isolated.mp3'

    # 1) source audio -> mono, peak-normalized to about -2 dBFS (plain gain, no dynamics)
    if not os.path.exists(norm):
        x = load(src)
        gain = -2.0 - 20 * np.log10(np.abs(x).max() + 1e-12)
        run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-af', f'pan=mono|c0=0.5*c0+0.5*c1,volume={gain:.2f}dB',
             '-ar', str(SR), '-c:a', 'pcm_s16le', norm])
    # 2) ElevenLabs Audio Isolation (cached)
    if not os.path.exists(iso):
        key = api_key('ELEVENLABS_API_KEY')
        try:
            with open(norm, 'rb') as audio:
                response = requests.post('https://api.elevenlabs.io/v1/audio-isolation',
                    headers={'xi-api-key': key}, files={'audio': ('audio.wav', audio, 'audio/wav')},
                    timeout=(30, 300), stream=True, allow_redirects=False)
            with response:
                if response.status_code != 200:
                    sys.exit(f'ElevenLabs HTTP {response.status_code}: confira a chave e os créditos.')
                with open(iso + '.part', 'wb') as output:
                    for chunk in response.iter_content(1024 * 1024):
                        output.write(chunk)
        except requests.RequestException:
            sys.exit('Não foi possível concluir a conexão com ElevenLabs.')
        os.rename(iso + '.part', iso)

    x, y = load(norm), load(iso)
    # 3) codec delay of the returned mp3, from 1 ms envelopes
    hop = 48
    n = min(len(x), len(y))
    ex, ey = env(x[:n], hop), env(y[:n], hop)
    best = max(range(-60, 61), key=lambda s: float(np.dot(ex[max(0, -s):len(ex) - max(0, s)], ey[max(0, s):len(ey) - max(0, -s)])))
    off = best / 1000.0  # isolated lags the source by `off` seconds when positive
    # 4) noise in the real pauses of the source, before/after
    report = {'source': src, 'codec_delay_ms': best}
    sil_path = f'{J}/analysis/silence-regions.json'
    if os.path.exists(sil_path):
        sil = [s for s in json.load(open(sil_path))['silences'] if s['end'] - s['start'] >= 0.5]
        yy = y[max(0, best * 48):]
        ra = [db(x[int((s['start'] + .15) * SR):int((s['end'] - .15) * SR)]) for s in sil]
        rb = [db(yy[int((s['start'] + .15) * SR):int((s['end'] - .15) * SR)]) for s in sil if int((s['end'] - .15) * SR) < len(yy)]
        report.update(pauses=len(sil), pause_noise_before_db=round(float(np.median(ra)), 1), pause_noise_after_db=round(float(np.median(rb)), 1))
    # 5) cut the isolated source with the EDL (same fades as master.py)
    f = ';'.join(f"[0:a]atrim={s['in'] + off:.4f}:{s['out'] + off:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,"
                 f"afade=t=out:st={s['frames'] / FPS - 0.015:.4f}:d=0.015[a{i}]" for i, s in enumerate(segs))
    f += ';' + ''.join(f'[a{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=0:a=1[o]'
    cut = f'{el}/voice-iso-cut.wav'
    run(['ffmpeg', '-v', 'error', '-y', '-i', iso, '-filter_complex', f, '-map', '[o]', '-ar', str(SR), '-c:a', 'pcm_s16le', cut])
    # 6) voice chain: HPF + (optional expander) + gain to target + peak limiter
    pre = 'highpass=f=70'
    if a.expander:
        pre += ',agate=threshold=0.006:ratio=2:range=0.18:attack=4:release=160:knee=6'
    out = subprocess.run(['ffmpeg', '-nostats', '-i', cut, '-af', pre + ',ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float([l for l in out.splitlines() if l.strip().startswith('I:')][-1].split()[1])
    g = a.target_lufs - I
    voice = f'{J}/renders/' + os.path.basename(a.out).replace('.mp4', '-voice.wav')
    run(['ffmpeg', '-v', 'error', '-y', '-i', cut, '-af', f'{pre},volume={g:.2f}dB,alimiter=limit=0.84:attack=5:release=80:level=disabled,apad=whole_dur={D:.4f}',
         '-t', f'{D:.4f}', '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le', voice])
    run(['ffmpeg', '-v', 'error', '-y', '-i', f'{J}/{a.base_video}', '-i', voice, '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
         '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', f'{J}/{a.out}'])
    report.update(voice=voice, out=f'{J}/{a.out}', gain_db=round(g, 2), expander=a.expander, duration=D)
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
