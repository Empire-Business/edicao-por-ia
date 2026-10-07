"""Deterministic tests only. These are not real-speech or LLM editorial evaluations."""
import copy
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from detect_silence import parse_silences
from edit_support import check_output, merge_ranges, write_json
from plan_silence_cuts import build_plan, settings_for
from prepare_script_comparison import prepare, read_script

SRC = str(Path('/tmp/synthetic-video-factory-source.mp4').resolve())

def tr():
    return {'input': SRC, 'segments': [
        {'start': 1.0, 'end': 2.0, 'text': 'primeiro trecho', 'words': [
            {'start': 1.0, 'end': 1.4, 'word': 'primeiro'}, {'start': 1.5, 'end': 2.0, 'word': 'trecho'}]},
        {'start': 4.0, 'end': 5.0, 'text': 'segundo trecho', 'words': [
            {'start': 4.0, 'end': 4.4, 'word': 'segundo'}, {'start': 4.5, 'end': 5.0, 'word': 'trecho'}]}]}

def silence():
    return {'input': SRC, 'duration': 6.0, 'status': 'ok',
            'silences': [{'start': 0, 'end': 1}, {'start': 2, 'end': 4}, {'start': 5, 'end': 6}]}

def overlaps(a, b, c, d):
    return max(a, c) < min(b, d) - 1e-8

class SilenceTests(unittest.TestCase):
    def test_automatic_cuts_and_protects_words(self):
        edl, report = build_plan(SRC, silence(), tr())
        self.assertEqual(len(report['cuts']), 3)
        self.assertGreater(report['removed_seconds'], 2)
        for seg in tr()['segments']:
            for word in seg['words']:
                self.assertTrue(any(c['in'] <= word['start'] and c['out'] >= word['end'] for c in edl['segments']))
    def test_intentional_pause(self):
        _, r = build_plan(SRC, silence(), tr(), protected={'ranges': [{'start': 2, 'end': 4, 'reason': 'dramatic_pause'}]})
        self.assertFalse(any(overlaps(c['start'], c['end'], 2, 4) for c in r['cuts']))
    def test_low_volume_word_inside_detected_silence(self):
        transcript = tr()
        transcript['segments'].append({'start': 2.8, 'end': 3.1, 'text': 'não', 'words': [{'start': 2.8, 'end': 3.1, 'word': 'não'}]})
        _, r = build_plan(SRC, silence(), transcript)
        self.assertFalse(any(overlaps(c['start'], c['end'], 2.7, 3.2) for c in r['cuts']))
    def test_coarse_segment_protects_entire_phrase(self):
        transcript = {'input': SRC, 'segments': [{'start': 1, 'end': 5, 'text': 'fala sem alinhamento por palavra'}]}
        _, r = build_plan(SRC, silence(), transcript)
        self.assertFalse(any(overlaps(c['start'], c['end'], 1, 5) for c in r['cuts']))
    def test_missing_transcript_is_blocked(self):
        with self.assertRaisesRegex(ValueError, 'protection'):
            build_plan(SRC, silence())
    def test_empty_transcript_is_blocked(self):
        with self.assertRaises(ValueError):
            build_plan(SRC, silence(), {'segments': []})
    def test_vad_can_protect_without_transcript(self):
        _, r = build_plan(SRC, silence(), vad={'speech_regions': [{'start': 1, 'end': 2}, {'start': 4, 'end': 5}]})
        self.assertGreater(r['removed_seconds'], 0)
    def test_off_does_not_require_transcript(self):
        _, r = build_plan(SRC, silence(), settings=settings_for(mode='off'))
        self.assertEqual(r['removed_seconds'], 0)
    def test_all_silent_is_blocked(self):
        data = silence(); data['silences'] = [{'start': 0, 'end': 6}]
        with self.assertRaisesRegex(ValueError, 'Entire'):
            build_plan(SRC, data, tr())
    def test_no_audio_is_not_applicable(self):
        data = silence(); data['status'] = 'not_applicable_no_audio'
        with self.assertRaises(ValueError):
            build_plan(SRC, data, tr())
    def test_selected_audio_track_propagates_to_render_edl(self):
        data = silence(); data['audio_stream'] = 1
        edl, _ = build_plan(SRC, data, tr())
        self.assertTrue(all(c['audio_stream'] == 1 for c in edl['segments']))
    def test_conflicting_audio_selection_rejected(self):
        data = silence(); data['audio_stream'] = 1
        base = {'segments':[{'source':SRC,'in':0,'out':6,'audio_stream':0}]}
        with self.assertRaisesRegex(ValueError,'different audio streams'):
            build_plan(SRC, data, tr(), base_edl=base)
    def test_source_mismatch_is_blocked(self):
        data = tr(); data['input'] = '/tmp/different-source.mp4'
        with self.assertRaisesRegex(ValueError, 'different source'):
            build_plan(SRC, silence(), data)
    def test_evidence_hash_mismatch_is_blocked(self):
        data = tr(); data['source_sha256'] = 'old'
        s = silence(); s['source_sha256'] = 'new'
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            build_plan(SRC, s, data)
    def test_base_edl_never_reintroduces_discarded_takes(self):
        base = {'version': '1', 'output': {'fps': 30}, 'segments': [
            {'source': SRC, 'in': 4, 'out': 6, 'label': 'last-first'},
            {'source': SRC, 'in': 0, 'out': 2, 'label': 'first-last'}]}
        edl, _ = build_plan(SRC, silence(), tr(), base_edl=base)
        self.assertEqual([c['label'] for c in edl['segments']], ['last-first', 'first-last'])
        self.assertFalse(any(overlaps(c['in'], c['out'], 2, 4) for c in edl['segments']))
    def test_other_source_preserved(self):
        other = {'source': '/tmp/other.mp4', 'in': 10, 'out': 12}
        base = {'version': '1', 'segments': [other, {'source': SRC, 'in': 0, 'out': 6}]}
        edl, _ = build_plan(SRC, silence(), tr(), base_edl=base)
        self.assertEqual(edl['segments'][0], other)
    def test_empty_base_fails(self):
        with self.assertRaises(ValueError):
            build_plan(SRC, silence(), tr(), base_edl={'segments': []})
    def test_short_pauses_preserved(self):
        s = silence(); s['silences'] = [{'start': 2.3, 'end': 2.5}]
        _, r = build_plan(SRC, s, tr())
        self.assertEqual(r['removed_seconds'], 0)
    def test_legacy_pattern_threshold_preserved(self):
        p = {'editorial': {'target_pace': 'natural', 'max_unmotivated_silence_seconds': 1.5}}
        self.assertEqual(settings_for(p)['minimum_silence_seconds'], 1.5)
    def test_explicit_mode_overrides_pattern(self):
        p = {'editorial': {'target_pace': 'natural', 'max_unmotivated_silence_seconds': 1.5}}
        self.assertEqual(settings_for(p, 'tight')['minimum_silence_seconds'], 0.5)
    def test_bad_settings_rejected(self):
        for value in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                settings_for(overrides={'word_handle_seconds': value})
    def test_negative_and_reversed_ranges_rejected(self):
        for a,b in [(-1,2),(3,2),(0,100)]:
            s = silence(); s['silences'] = [{'start': a, 'end': b}]
            with self.assertRaises(ValueError):
                build_plan(SRC, s, tr())
    def test_trailing_unclosed_silence_parsed(self):
        out = parse_silences('silence_start: 0\nsilence_end: 1 | silence_duration: 1\nsilence_start: 5', 6)
        self.assertEqual([(x['start'],x['end']) for x in out], [(0,1),(5,6)])
    def test_overlapping_maps_merged(self):
        s = silence(); s['silences'] = [{'start': 2, 'end': 3.5}, {'start': 3, 'end': 4}]
        _, r = build_plan(SRC, s, tr())
        self.assertEqual(len(r['cuts']), 1)
    def test_random_protected_ranges_never_cut(self):
        rng = random.Random(123)
        for _ in range(80):
            a = rng.uniform(2, 3.6); b = min(4, a + rng.uniform(.01,.4))
            _, r = build_plan(SRC, silence(), tr(), protected={'ranges': [{'start':a,'end':b}]})
            self.assertFalse(any(overlaps(c['start'],c['end'],a,b) for c in r['cuts']))

class ScriptTests(unittest.TestCase):
    def test_paraphrase_never_auto_declared_error(self):
        script = {'id':'ref','blocks':[{'id':'A','kind':'spoken','text':'Você não precisa publicar todos os dias.'}]}
        transcript = {'segments':[{'start':0,'end':3,'text':'Não é necessário postar diariamente.'}]}
        packet = prepare(script, transcript)
        self.assertEqual(packet['blocks'][0]['status'], 'pending_semantic_review')
        self.assertNotIn('segments',packet)
    def test_high_lexical_similarity_is_not_semantic_approval(self):
        p=prepare({'blocks':[{'id':'A','text':'Você não precisa postar.'}]},
                  {'segments':[{'start':0,'end':3,'text':'Você precisa postar.'}]})
        self.assertEqual(p['blocks'][0]['status'],'pending_semantic_review')
        self.assertIn('lexical_score_not_confidence', p['blocks'][0]['candidate_windows'][0])
    def test_missing_retrieval_requires_search_not_missing_claim(self):
        p=prepare({'blocks':[{'id':'A','text':'Resultado extraordinário.'}]},
                  {'segments':[{'start':0,'end':3,'text':'Olá mundo.'}]})
        self.assertTrue(p['blocks'][0]['needs_broader_search'])
        self.assertEqual(p['blocks'][0]['status'],'pending_semantic_review')
    def test_two_takes_returned_not_auto_selected(self):
        p=prepare({'blocks':[{'id':'A','text':'Três caminhos para crescer.'}]}, {'segments':[
            {'start':1,'end':3,'text':'Três caminhos para crescer.'},
            {'start':60,'end':63,'text':'Três caminhos para crescer.'}]})
        self.assertEqual(len(p['blocks'][0]['candidate_windows']),2)
    def test_stage_direction_not_treated_as_missing_speech(self):
        p=prepare({'blocks':[{'id':'A','kind':'direction','text':'pausa de dois segundos'}]}, tr())
        self.assertEqual(p['blocks'][0]['status'],'direction_not_spoken')
        self.assertNotIn('candidate_windows',p['blocks'][0])
    def test_child_scope_isolation(self):
        p=prepare({'blocks':[{'id':'A','text':'segundo trecho'}]}, tr(), scope_start=3,scope_end=6)
        for w in p['blocks'][0]['candidate_windows']:
            self.assertGreaterEqual(w['start'],3)
            self.assertLessEqual(w['end'],6)
    def test_invalid_scope_fails(self):
        with self.assertRaises(ValueError):
            prepare({'blocks':[]},tr(),scope_start=5,scope_end=1)
    def test_text_requires_block_type_review(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'reference.txt'; p.write_text('Um exemplo.\n\n[pausa]',encoding='utf-8')
            s=read_script(p)
            self.assertTrue(s['needs_block_type_review'])
            self.assertEqual(len(s['blocks']),2)
    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'r.json'; p.write_text(json.dumps({'blocks':[{'id':'A','text':'oi'},{'id':'A','text':'ola'}]}))
            with self.assertRaises(ValueError): read_script(p)
    def test_empty_script_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'r.txt'; p.write_text('')
            with self.assertRaises(ValueError): read_script(p)

class SafetyTests(unittest.TestCase):
    def test_never_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.json'; write_json(p,{'unchanged':True})
            with self.assertRaises(ValueError): check_output(p)
            with self.assertRaises(FileExistsError): write_json(p,{})
            self.assertTrue(json.loads(p.read_text())['unchanged'])
    def test_input_alias_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.json'
            with self.assertRaises(ValueError): check_output(p,[p])

if __name__=='__main__': unittest.main(verbosity=2)
