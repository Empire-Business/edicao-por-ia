"""Offline tests for the outfit/scenery swap tool: synthetic key, mocked provider, synthetic media."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import gen_video_edit as gve
import service_keys

FFMPEG = shutil.which('ffmpeg') and shutil.which('ffprobe')
MODEL = {'id': gve.DEFAULT_MODEL, 'pricing_skus': {'cents_per_second_output': '3'}}


def synth(path, size, fps, seconds, audio=True):
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'testsrc=size={size}:rate={fps}:duration={seconds}']
    if audio:
        cmd += ['-f', 'lavfi', '-i', f'sine=frequency=440:duration={seconds}', '-c:a', 'aac']
    subprocess.run(cmd + ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path)], check=True)


def run_args(**changes):
    values = dict(input='in.mp4', start=0.0, duration=5.0, change='roupa', describe='a tailored black blazer',
                  prompt=None, out='out.mp4', model=gve.DEFAULT_MODEL, source_url=None, temp_public_link=True,
                  max_usd=0.5, accept_unknown_cost=False, long_side=1280)
    values.update(changes)
    return argparse.Namespace(**values)


class RequestTests(unittest.TestCase):
    def test_prompts_keep_the_person_and_name_the_change(self):
        outfit = gve.build_prompt('roupa', '  a tailored   black blazer. ')
        self.assertIn("clothing with a tailored black blazer.", outfit)
        self.assertIn('the lighting and the background', outfit)
        scenery = gve.build_prompt('cenario', 'a bright modern office')
        self.assertIn('Replace only the background', scenery)
        self.assertIn('clothing, face', scenery)
        self.assertIn('lip movements', gve.build_prompt('ambos', 'blazer; bright office'))
        with self.assertRaises(ValueError): gve.build_prompt('roupa', 'azul')
        with self.assertRaises(ValueError): gve.build_prompt('rosto', 'another person entirely')

    def test_cost_estimate_uses_live_skus_and_never_guesses(self):
        self.assertAlmostEqual(gve.estimate_usd(MODEL, 5), 0.15)
        self.assertAlmostEqual(gve.estimate_usd(MODEL, 4.2), 0.15)
        minimum = {'pricing_skus': {'cents_per_second_output': '28', 'minimum_cents_per_generation': '56'}}
        self.assertAlmostEqual(gve.estimate_usd(minimum, 1), 0.56)
        self.assertIsNone(gve.estimate_usd({'pricing_skus': {'video_tokens': '0.0000035'}}, 5))

    def test_key_goes_only_to_the_provider_host_in_the_header(self):
        with patch.object(gve, 'http', return_value=(202, b'{"id":"job","status":"pending"}')) as call:
            gve.api('/videos', 'fake-key', {'model': 'm'})
        url, body, headers = call.call_args.args
        self.assertEqual(url, 'https://openrouter.ai/api/v1/videos')
        self.assertEqual(headers['Authorization'], 'Bearer fake-key')
        self.assertNotIn('fake-key', url); self.assertNotIn(b'fake-key', body)
        with patch.object(gve, 'http') as call:
            with self.assertRaises(ValueError): gve.api('https://evil.example/api/v1/videos/job', 'fake-key')
            call.assert_not_called()

    def test_redirects_are_refused_and_errors_do_not_echo_the_key(self):
        self.assertIsNone(gve.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://cdn.example/x'))
        for status in (401, 402, 400):
            with patch.object(gve, 'http', return_value=(status, b'{"error":{"message":"Only HTTPS URLs are allowed"}}')):
                with self.assertRaises(ValueError) as error: gve.api('/videos', 'fake-key', {})
            self.assertNotIn('fake-key', str(error.exception))
        self.assertIn('Only HTTPS', str(error.exception))

    def test_source_link_must_be_https(self):
        self.assertEqual(gve.check_source_url('https://files.example/clip.mp4'), 'https://files.example/clip.mp4')
        for bad in ('http://files.example/clip.mp4', 'data:video/mp4;base64,AAAA', '/tmp/clip.mp4'):
            with self.assertRaises(ValueError): gve.check_source_url(bad)

    def test_generation_polls_until_done_and_reports_failure(self):
        steps = [{'id': 'job', 'status': 'pending', 'polling_url': 'https://openrouter.ai/api/v1/videos/job'},
                 {'id': 'job', 'status': 'in_progress', 'polling_url': 'https://openrouter.ai/api/v1/videos/job'},
                 {'id': 'job', 'status': 'completed', 'usage': {'cost': 0.15}}]
        with patch.object(gve, 'api', side_effect=steps) as call, patch.object(gve.time, 'sleep'):
            job = gve.generate('fake-key', gve.DEFAULT_MODEL, 'prompt', 'https://files.example/clip.mp4')
        self.assertEqual(job['usage']['cost'], 0.15)
        body = call.call_args_list[0].args[2]
        self.assertEqual(body['input_references'], [{'type': 'video_url', 'video_url': {'url': 'https://files.example/clip.mp4'}}])
        with patch.object(gve, 'api', return_value={'id': 'job', 'status': 'failed', 'error': 'blocked'}):
            with self.assertRaisesRegex(ValueError, 'failed'): gve.generate('fake-key', 'm', 'p', 'https://x.example/c.mp4')


class ConsentAndBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'in.mp4'; self.source.write_bytes(b'fixture')
        self.addCleanup(patch.stopall)
        self.upload = patch.object(gve, 'temp_public_link').start()
        self.key = patch.object(service_keys, 'api_key').start()
        patch.object(gve, 'list_models', return_value=[MODEL, {'id': 'volume/model', 'pricing_skus': {'video_tokens': '1'}}]).start()

    def blocked(self, pattern, **changes):
        with self.assertRaisesRegex(ValueError, pattern):
            gve.cmd_run(run_args(input=str(self.source), out=str(Path(self.temp.name) / 'out.mp4'), **changes))
        self.upload.assert_not_called(); self.key.assert_not_called()

    def test_hosting_choice_is_explicit(self):
        self.blocked('consentimento', temp_public_link=False, source_url=None)
        self.blocked('consentimento', temp_public_link=True, source_url='https://files.example/clip.mp4')

    def test_spend_above_the_limit_or_unknown_stops_before_any_upload(self):
        self.blocked('acima do limite', duration=10.0, max_usd=0.2)
        self.blocked('accept-unknown-cost', model='volume/model')
        self.blocked('não encontrado', model='missing/model')

    def test_range_is_short(self):
        self.blocked('1 a 10 segundos', duration=30.0)
        self.blocked('1 a 10 segundos', duration=0.2)


class KeyTemplateTests(unittest.TestCase):
    def test_openrouter_key_is_read_from_the_visible_file(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True):
            path = service_keys.prepare(Path(temp))
            self.assertIn('OPENROUTER_API_KEY=', path.read_text(encoding='utf-8'))
            with self.assertRaisesRegex(ValueError, service_keys.KEY_FILE): service_keys.api_key('OPENROUTER_API_KEY', Path(temp))
            path.write_text('ELEVENLABS_API_KEY=fake-voice\nOPENROUTER_API_KEY=fake-router\n', encoding='utf-8')
            self.assertEqual(service_keys.api_key('OPENROUTER_API_KEY', Path(temp)), 'fake-router')


@unittest.skipUnless(FFMPEG, 'ffmpeg/ffprobe not available')
class MediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.source = self.dir / 'gravacao.mp4'; synth(self.source, '320x568', 30, 3)

    def test_result_matches_the_recording_and_keeps_its_audio(self):
        reference, sent, generated, out = (self.dir / n for n in ('ref.mp4', 'sent.mp4', 'gen.mp4', 'out.mp4'))
        gve.cut_reference(self.source, 1, 1, reference)
        gve.make_upload_clip(reference, sent, 284)
        self.assertEqual(max(gve.probe(sent)['width'], gve.probe(sent)['height']), 284)
        synth(generated, '304x544', 24, 1.04, audio=False)
        gve.conform(generated, reference, out)
        want, got = gve.probe(reference), gve.probe(out)
        self.assertEqual((got['width'], got['height']), (want['width'], want['height']))
        self.assertAlmostEqual(got['fps'], want['fps'], places=2)
        self.assertAlmostEqual(got['duration'], want['duration'], delta=0.08)
        streams = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', str(out)],
                                 capture_output=True, text=True).stdout.split()
        self.assertIn('audio', streams)
        gve.side_by_side(reference, out, self.dir / 'lado.mp4')
        self.assertEqual(gve.probe(self.dir / 'lado.mp4')['width'], want['width'] * 2)

    def test_patch_builds_a_derived_copy_and_never_touches_the_original(self):
        clip = self.dir / 'clip.mp4'; synth(clip, '320x568', 30, 1)
        before = self.source.read_bytes()
        derived = self.dir / 'derivada.mov'
        gve.cmd_patch(argparse.Namespace(input=str(self.source), clip=str(clip), start=1.0, out=str(derived)))
        self.assertEqual(self.source.read_bytes(), before)
        self.assertAlmostEqual(gve.probe(derived)['duration'], gve.probe(self.source)['duration'], delta=0.1)
        for bad in (dict(out=str(self.source)), dict(out=str(self.dir / 'x.mp4')), dict(start=2.5)):
            values = dict(input=str(self.source), clip=str(clip), start=1.0, out=str(self.dir / 'y.mov')); values.update(bad)
            with self.assertRaises(ValueError): gve.cmd_patch(argparse.Namespace(**values))
        other = self.dir / 'outro.mp4'; synth(other, '160x284', 30, 1)
        with self.assertRaisesRegex(ValueError, 'tamanho'):
            gve.cmd_patch(argparse.Namespace(input=str(self.source), clip=str(other), start=1.0, out=str(self.dir / 'z.mov')))

    def test_download_rejects_an_error_page_and_keeps_the_key_on_its_host(self):
        job = {'id': 'job', 'unsigned_urls': ['https://cdn.example/result.mp4']}
        with patch.object(gve, 'http', return_value=(200, b'<html>error</html>')) as call:
            with self.assertRaises(ValueError): gve.download('fake-key', job, self.dir / 'bad.mp4')
        self.assertEqual(call.call_args.args[2], {})
        with patch.object(gve, 'http', return_value=(200, self.source.read_bytes())) as call:
            gve.download('fake-key', {'id': 'job'}, self.dir / 'ok.mp4')
        self.assertEqual(call.call_args.args[0], 'https://openrouter.ai/api/v1/videos/job/content?index=0')
        self.assertEqual(call.call_args.args[2], {'Authorization': 'Bearer fake-key'})


if __name__ == '__main__':
    unittest.main()
