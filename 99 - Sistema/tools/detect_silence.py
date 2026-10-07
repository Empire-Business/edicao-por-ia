#!/usr/bin/env python3
"""Detect quiet intervals only. Use plan_silence_cuts.py to create synchronized cuts."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
from edit_support import check_output, number, sha256, write_json

VALUE = r'(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)'
START = re.compile(r'silence_start:\s*' + VALUE, re.I)
END = re.compile(r'silence_end:\s*' + VALUE, re.I)


def parse_silences(log: str, duration: float) -> list[dict]:
    intervals = []
    active = None
    for line in log.splitlines():
        m = START.search(line)
        if m:
            active = max(0.0, float(m.group(1)))
        m = END.search(line)
        if m and active is not None:
            end = min(duration, float(m.group(1)))
            if end > active:
                intervals.append({'start': active, 'end': end, 'duration': end - active})
            active = None
    if active is not None and active < duration:
        intervals.append({'start': active, 'end': duration, 'duration': duration - active})
    return intervals


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input')
    ap.add_argument('--noise', default='-40dB', help='Use --noise=-40dB for negative dB values.')
    ap.add_argument('--duration', type=float, default=0.15)
    ap.add_argument('--audio-stream', type=int, default=0)
    ap.add_argument('--output')
    a = ap.parse_args()
    source = Path(a.input).resolve(strict=True)
    if a.duration <= 0 or a.audio_stream < 0:
        raise ValueError('Duration must be positive and audio stream nonnegative')
    number(a.duration, 'minimum duration')
    if not re.fullmatch(r'-?\d+(?:\.\d+)?(?:dB)?', a.noise):
        raise ValueError('Noise must be a numeric amplitude or dB value')
    output = check_output(a.output, [source]) if a.output else None
    p = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(source)],
                       capture_output=True, text=True, check=True)
    meta = json.loads(p.stdout)
    duration = number(meta['format']['duration'], 'source duration')
    audio = [s for s in meta.get('streams', []) if s.get('codec_type') == 'audio']
    result = {'input': str(source), 'source_sha256': sha256(source), 'duration': duration,
              'noise': a.noise, 'minimum_duration': a.duration, 'audio_stream': a.audio_stream,
              'timebase': 'original_source_seconds', 'silences': []}
    if not audio:
        result['status'] = 'not_applicable_no_audio'
    else:
        if a.audio_stream >= len(audio):
            raise ValueError('Selected audio stream does not exist')
        selected = audio[a.audio_stream]
        # Refuse unusual offsets: normalization must establish a common video/audio time origin.
        fmt_start = float(meta['format'].get('start_time', 0))
        audio_start = float(selected.get('start_time', 0))
        video = next((s for s in meta.get('streams', []) if s.get('codec_type') == 'video'), {})
        video_start = float(video.get('start_time', 0))
        if max(abs(fmt_start), abs(audio_start), abs(video_start)) > 0.05:
            raise ValueError('Nonzero stream origin: normalize a working copy and preserve its source-time mapping first')
        end = min(duration, float(selected.get('duration', duration)) + audio_start)
        p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(source),
                            '-map', f'0:a:{a.audio_stream}', '-vn', '-sn', '-dn',
                            '-af', f'silencedetect=n={a.noise}:d={a.duration}', '-f', 'null', '-'],
                           capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError('FFmpeg failed: ' + p.stderr[-2000:])
        result['status'] = 'ok'
        result['silences'] = parse_silences(p.stderr, end)
        result['audio_end_seconds'] = end
    if output:
        write_json(output, result)
    else:
        print(json.dumps(result, indent=2))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as e:
        raise SystemExit(str(e))
