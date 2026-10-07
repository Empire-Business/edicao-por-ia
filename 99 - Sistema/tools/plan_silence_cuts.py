#!/usr/bin/env python3
"""Convert detected silence to a non-destructive A/V EDL, protecting speech and marked pauses."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from edit_support import (check_output, merge_ranges, number, read_data, same_path,
                          sha256, subtract_ranges, write_json)

PRESETS = {
    'natural': {'enabled': True, 'minimum_silence_seconds': 0.8, 'keep_pause_seconds': 0.30,
                'word_handle_seconds': 0.10, 'minimum_cut_seconds': 0.10, 'trim_edges': True},
    'tight': {'enabled': True, 'minimum_silence_seconds': 0.5, 'keep_pause_seconds': 0.18,
              'word_handle_seconds': 0.08, 'minimum_cut_seconds': 0.10, 'trim_edges': True},
    'relaxed': {'enabled': True, 'minimum_silence_seconds': 1.5, 'keep_pause_seconds': 0.50,
                'word_handle_seconds': 0.12, 'minimum_cut_seconds': 0.12, 'trim_edges': True},
    'off': {'enabled': False, 'minimum_silence_seconds': 0.8, 'keep_pause_seconds': 0.30,
            'word_handle_seconds': 0.10, 'minimum_cut_seconds': 0.10, 'trim_edges': True},
}


def settings_for(pattern: dict | None = None, mode: str | None = None, overrides: dict | None = None) -> dict:
    pattern = pattern or {}
    editorial = pattern.get('editorial', {})
    chosen = mode or editorial.get('target_pace', 'natural')
    if chosen not in PRESETS:
        raise ValueError('Unknown silence mode: ' + str(chosen))
    settings = dict(PRESETS[chosen])
    # Legacy v1 values remain authoritative, rather than silently changing approved pace.
    if 'max_unmotivated_silence_seconds' in editorial and not mode:
        settings['minimum_silence_seconds'] = editorial['max_unmotivated_silence_seconds']
    settings.update(editorial.get('silence_removal', {}))
    if mode:
        settings.update(PRESETS[mode])
    if overrides:
        unknown = set(overrides) - set(PRESETS['natural'])
        if unknown:
            raise ValueError('Unknown silence settings: ' + ', '.join(sorted(unknown)))
        settings.update(overrides)
    for key in ('minimum_silence_seconds', 'keep_pause_seconds', 'word_handle_seconds', 'minimum_cut_seconds'):
        settings[key] = number(settings[key], key)
    if settings['minimum_silence_seconds'] <= 0 or settings['minimum_cut_seconds'] <= 0:
        raise ValueError('Minimum silence and minimum cut must be positive')
    for key in ('enabled', 'trim_edges'):
        if not isinstance(settings[key], bool):
            raise ValueError(f'{key} must be boolean')
    return settings


def timed_ranges(items: list[dict], duration: float, handle: float = 0) -> list[tuple[float, float]]:
    out = []
    for item in items:
        start, end = number(item['start'], 'start'), number(item['end'], 'end')
        if end <= start or end > duration + 0.10:
            raise ValueError('Invalid or out-of-bounds evidence range')
        out.append((max(0, start - handle), min(duration, end + handle)))
    return merge_ranges(out)


def speech_ranges(transcript: dict | None, duration: float, handle: float) -> list[tuple[float, float]]:
    if not transcript:
        return []
    items = list(transcript.get('words', []))
    for seg in transcript.get('segments', []):
        if seg.get('words'):
            items.extend(seg['words'])
        elif seg.get('text', '').strip():
            # Coarse timestamps protect the entire utterance instead of guessing word boundaries.
            items.append(seg)
    return timed_ranges(items, duration, handle)


def validate_evidence(data: dict | None, source: str, expected_hash: str | None = None) -> None:
    if not data:
        return
    origin = data.get('input') or data.get('source')
    if origin and not same_path(origin, source):
        raise ValueError('Evidence belongs to a different source')
    if expected_hash and data.get('source_sha256') and data['source_sha256'] != expected_hash:
        raise ValueError('Stale evidence: source hash mismatch')


def build_plan(source: str, silence: dict, transcript: dict | None = None,
               protected: dict | None = None, vad: dict | None = None,
               base_edl: dict | None = None, settings: dict | None = None,
               output_config: dict | None = None) -> tuple[dict, dict]:
    settings = settings_for(overrides=settings) if settings else settings_for()
    if silence.get('status', 'ok') != 'ok':
        raise ValueError('No usable audio silence map; keep this source unchanged in the visual workflow')
    selected_track = silence.get('audio_stream', 0)
    if not isinstance(selected_track, int) or isinstance(selected_track, bool) or selected_track < 0:
        raise ValueError('Invalid selected audio stream')
    if transcript and transcript.get('audio_stream', selected_track) != selected_track:
        raise ValueError('Transcript and silence map use different audio streams')
    duration = number(silence['duration'], 'duration')
    if duration <= 0:
        raise ValueError('Empty source')
    for data in (silence, transcript, protected, vad):
        validate_evidence(data, source, silence.get('source_sha256'))
    quiet = timed_ranges(silence.get('silences', []), duration)
    voice = speech_ranges(transcript, duration, settings['word_handle_seconds'])
    if vad:
        voice = merge_ranges(voice + timed_ranges(vad.get('speech_regions', []), duration, settings['word_handle_seconds']))
    intentional = timed_ranges((protected or {}).get('ranges', []), duration)
    if settings['enabled'] and not voice:
        raise ValueError('Speech protection is missing or empty. Provide timestamped transcription/VAD; do not cut blindly')
    if settings['enabled'] and quiet and sum(b-a for a,b in quiet) >= duration - 0.05:
        raise ValueError('Entire source appears silent. Review microphone/threshold/track before cutting')
    blocked = merge_ranges(voice + intentional)
    base = base_edl or {'version': '1.1', 'output': output_config or {},
                       'segments': [{'source': source, 'in': 0, 'out': duration}]}
    if not base.get('segments'):
        raise ValueError('Empty base EDL')
    clips, cuts = [], []
    original_duration = 0.0
    matched_source = False
    for index, seg in enumerate(base['segments']):
        start, end = number(seg['in'], 'clip in'), number(seg['out'], 'clip out')
        if end <= start:
            raise ValueError('Invalid base EDL range')
        original_duration += end - start
        if not same_path(seg['source'], source):
            clips.append(dict(seg))
            continue
        matched_source = True
        if seg.get('audio_stream', selected_track) != selected_track:
            raise ValueError('Base EDL and silence map use different audio streams')
        if end > duration + 1e-6:
            raise ValueError('Base EDL exceeds source duration')
        proposed = []
        if settings['enabled']:
            for qs, qe in quiet:
                a, b = max(qs, start), min(qe, end)
                if b <= a:
                    continue
                for x, y in subtract_ranges(a, b, blocked):
                    if y - x + 1e-9 < settings['minimum_silence_seconds']:
                        continue
                    lead, tail = abs(x - start) < 1e-6, abs(y - end) < 1e-6
                    keep = settings['keep_pause_seconds']
                    if lead and tail:
                        continue  # Do not delete a whole silent shot or child job automatically.
                    if lead and settings['trim_edges']:
                        cut_start, cut_end = x, y - keep
                    elif tail and settings['trim_edges']:
                        cut_start, cut_end = x + keep, y
                    else:
                        cut_start, cut_end = x + keep/2, y - keep/2
                    if cut_end - cut_start >= settings['minimum_cut_seconds']:
                        proposed.append((cut_start, cut_end))
        proposed = merge_ranges(proposed)
        retained = subtract_ranges(start, end, proposed)
        # Restore any cut that would leave an impractically tiny source fragment.
        if any(b-a < 0.05 for a,b in retained):
            proposed, retained = [], [(start, end)]
        for a, b in proposed:
            cuts.append({'source': source, 'base_segment_index': index, 'start': a, 'end': b,
                         'duration': b-a, 'reason': 'detected_quiet_outside_protected_speech_and_pauses'})
        for a, b in retained:
            clip = {**seg, 'in': round(a, 6), 'out': round(b, 6), 'audio_stream': selected_track}
            if proposed:
                clip['silence_cleanup'] = '1.1'
            clips.append(clip)
    if not matched_source:
        raise ValueError('Source is not present in the base EDL')
    final_duration = sum(c['out'] - c['in'] for c in clips)
    result = {**base, 'version': '1.1', 'segments': clips}
    report = {'status': 'draft_requires_editorial_qa', 'source': source,
              'source_sha256': silence.get('source_sha256'), 'timebase': 'original_source_seconds',
              'settings': settings, 'speech_protection_ranges': len(voice),
              'intentional_pause_ranges': len(intentional), 'cuts': cuts,
              'before_seconds': original_duration, 'after_seconds': final_duration,
              'removed_seconds': original_duration-final_duration,
              'notes': ['Quiet detection is not proof of absent speech.',
                        'No speech meaning, breaths or rhetorical pauses were evaluated by this script.',
                        'Apply the same EDL to audio and video; retime captions from this EDL.']}
    return result, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', required=True)
    ap.add_argument('--silence', required=True)
    ap.add_argument('--transcript')
    ap.add_argument('--speech-regions', help='Optional JSON VAD: input, speech_regions:[{start,end}]')
    ap.add_argument('--protected', help='JSON: input, ranges:[{start,end,reason}]')
    ap.add_argument('--base-edl', help='Existing assembly EDL. Only subtract; never reintroduce discarded takes.')
    ap.add_argument('--pattern', help='Pattern JSON/YAML; YAML requires optional PyYAML')
    ap.add_argument('--mode', choices=list(PRESETS))
    ap.add_argument('--settings', help='Resolved job overrides as a JSON/YAML object')
    ap.add_argument('--output', required=True)
    ap.add_argument('--report', required=True)
    a = ap.parse_args()
    source = str(Path(a.source).resolve(strict=True))
    inputs = [x for x in [source, a.silence, a.transcript, a.speech_regions, a.protected,
                          a.base_edl, a.pattern, a.settings] if x]
    out = check_output(a.output, inputs)
    report_path = check_output(a.report, inputs + [out])
    silence = read_data(a.silence)
    actual_hash = sha256(source)
    if silence.get('source_sha256') and silence['source_sha256'] != actual_hash:
        raise ValueError('Source changed: rerun detection')
    silence['source_sha256'] = actual_hash
    load = lambda x: read_data(x) if x else None
    pattern = load(a.pattern)
    settings = settings_for(pattern, a.mode, load(a.settings))
    edl, report = build_plan(source, silence, load(a.transcript), load(a.protected),
                             load(a.speech_regions), load(a.base_edl), settings,
                             (pattern or {}).get('output'))
    report['evidence_sha256'] = {str(Path(p).resolve()): sha256(p) for p in inputs if p != source}
    write_json(out, edl)
    write_json(report_path, report)
    print(json.dumps({'edl': str(out), 'report': str(report_path),
                      'cuts': len(report['cuts']), 'removed_seconds': report['removed_seconds']}, indent=2))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as e:
        raise SystemExit(str(e))
