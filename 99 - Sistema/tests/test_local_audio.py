"""Offline tests: synthetic audio, isolated files, mocked HTTP. No DB or paid APIs."""
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch, MagicMock
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import audio_local as audio
import narrate
import music_library as music
import service_keys
import audio_remote


def make_wav(path, seconds=.7):
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        stream.writeframes(b''.join(struct.pack('<h', int(4000 * math.sin(2 * math.pi * 220 * i / 48000)))
                                   for i in range(round(seconds * 48000))))


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / 'source.wav'; make_wav(self.src)

    def test_default_and_missing_local_provider_never_choose_paid(self):
        with patch.object(audio, 'deepfilter_binary', return_value=None):
            self.assertEqual(audio.select_cleaner('auto'), 'ffmpeg')
            with self.assertRaisesRegex(ValueError, 'DeepFilterNet'): audio.select_cleaner('deepfilter')
        with patch.object(service_keys, 'api_key', side_effect=AssertionError('no keys')):
            with self.assertRaisesRegex(ValueError, 'autorização'):
                audio.clean(self.src, self.root/'out.wav', 'elevenlabs', root=self.root)

    def test_local_cleanup_preserves_duration_original_and_produces_receipt(self):
        if not shutil.which('ffmpeg'): self.skipTest('FFmpeg absent')
        before = self.src.read_bytes()
        with patch.object(service_keys, 'api_key', side_effect=AssertionError('no keys')):
            result = audio.clean(self.src, self.root/'clean.wav', 'ffmpeg', root=self.root)
        self.assertEqual(self.src.read_bytes(), before)
        self.assertAlmostEqual(result['duration'], .7, places=3)
        self.assertFalse(result['paid_request'])
        saved = json.loads((self.root/'clean.audio.json').read_text())
        self.assertTrue(saved['source'].startswith('workspace://'))
        self.assertEqual(saved['output_sha256'], audio.digest(self.root/'clean.wav'))
        with self.assertRaises(ValueError): audio.clean(self.src, self.root/'clean.wav', 'ffmpeg', root=self.root)

    def test_deepfilter_real_runtime_if_available(self):
        binary = audio.deepfilter_binary(ROOT)
        if not binary or not shutil.which('ffmpeg'): self.skipTest('Native runtime absent')
        with patch.object(audio, 'deepfilter_binary', return_value=binary):
            result = audio.clean(self.src, self.root/'deep.wav', 'deepfilter', root=self.root)
        self.assertAlmostEqual(result['duration'], .7, places=3)
        self.assertTrue(result['settings']['delay_compensated'])

    def test_paths_do_not_overwrite_sources_or_escape_workspace(self):
        with self.assertRaises(ValueError): audio.output_path(self.src, self.root)
        with self.assertRaises(ValueError): audio.output_path(self.root/'../escape.wav', self.root)
        (self.root/'link.wav').symlink_to(self.src)
        with self.assertRaises(ValueError): audio.output_path(self.root/'link.wav', self.root)

    def test_existing_edl_entrypoint_renders_local_audio_and_reuses_cache(self):
        if not shutil.which('ffmpeg'): self.skipTest('FFmpeg absent')
        (ROOT/'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp', prefix='audio-edl-test-') as folder:
            job = Path(folder); (job/'renders').mkdir(); (job/'edit').mkdir()
            source = job/'source.wav'; make_wav(source)
            (job/'job.yaml').write_text(json.dumps({'format': 'F99', 'visual_identity': 'ID99'}))
            (job/'edit/edl.json').write_text(json.dumps({'fps': 30, 'total_frames': 12,
                'segments': [{'source': str(source), 'in': .1, 'out': .3, 'frames': 6},
                             {'source': str(source), 'in': .4, 'out': .6, 'frames': 6}]}))
            audio.run(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-f', 'lavfi', '-i',
                       'color=size=64x64:rate=30:duration=0.4', '-c:v', 'libx264', job/'renders/base.mp4'])
            for i in (1, 2):
                audio.run([sys.executable, ROOT/'tools/el_isolate_voice.py', job, '--provider', 'ffmpeg',
                           '--base-video', 'renders/base.mp4', '--out', f'renders/v{i}.mp4'], 30)
            evidence = json.loads((job/'renders/v2.audio.json').read_text())
            self.assertTrue(evidence['cached']); self.assertFalse(evidence['paid_request'])
            self.assertAlmostEqual(audio.probe(job/'renders/v2.mp4')['duration'], .4, places=2)

    def test_music_requires_rights_and_reuses_verified_local_track(self):
        if not shutil.which('ffmpeg'): self.skipTest('FFmpeg absent')
        with self.assertRaises(ValueError): music.add(self.src, 'fixture', 'Fixture', 'synthetic', root=self.root)
        music.add(self.src, 'fixture', 'Fixture', 'Synthetic test tone', True, self.root)
        result = music.prepare('fixture', self.root/'bed.wav', 1.2, self.root)
        self.assertAlmostEqual(result['duration'], 1.2, places=2)
        self.assertTrue(result['looped']); self.assertFalse(result['paid_request'])
        source = self.root/'context/audio-library/fixture/original.wav'
        source.write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'integridade'):
            music.prepare('fixture', self.root/'bad.wav', 1.2, self.root)

    def test_narration_blocks_paid_and_ambiguous_engines_before_io(self):
        for model in ('tts-1', 'omnivoice', 'gpt-4o-mini-tts', 'elevenlabs', None):
            with self.assertRaisesRegex(ValueError, 'engine local'):
                narrate.speak('missing', 'missing', 'default', model=model, root=self.root)
        with patch.object(service_keys, 'api_key', side_effect=AssertionError('no keys')):
            with self.assertRaisesRegex(ValueError, 'autorização'):
                narrate.speak('missing', 'missing', 'voice', 'elevenlabs', root=self.root)

    def test_voicestudio_mocked_contract_and_no_fabricated_alignment(self):
        if not shutil.which('ffmpeg'): self.skipTest('FFmpeg absent')
        text = self.root/'text.txt'; text.write_text('Teste local em português.')
        def response(endpoint, base_url, payload=None, output=None):
            if endpoint == '/cortez/identity':
                return {'distribution': 'Empire-Business/cortez-voz'}
            self.assertEqual(endpoint, '/v1/audio/speech')
            self.assertEqual(payload['model'], 'mlx-audio')
            self.assertEqual(payload['language'], 'pt')
            shutil.copyfile(self.src, output)
        with patch.object(narrate, 'voicestudio', side_effect=response):
            result = narrate.speak(text, self.root/'narration.wav', 'default', model='mlx-audio', root=self.root)
        self.assertEqual(result['alignment'], 'pending_local_transcription')
        self.assertFalse((self.root/'narration.words.json').exists())

    def test_loopback_only_and_redirect_not_followed(self):
        for url in ('https://example.com', 'http://localhost:3900', 'http://127.0.0.1:3900@evil.com',
                    'http://127.0.0.1:3900/path', 'http://127.0.0.1:3900?key=x', 'http://10.0.0.1:3900'):
            with self.assertRaises(ValueError): narrate.local_url(url)
        self.assertEqual(narrate.local_url('http://127.0.0.1:3900/'), 'http://127.0.0.1:3900')
        session = MagicMock(); response = session.request.return_value.__enter__.return_value
        response.status_code = 302
        with patch.object(narrate.requests, 'Session') as cls:
            cls.return_value.__enter__.return_value = session
            with self.assertRaisesRegex(ValueError, '302'): narrate.voicestudio('/v1/audio/voices', 'http://127.0.0.1:3900')
        self.assertFalse(session.trust_env)
        self.assertFalse(session.request.call_args.kwargs['allow_redirects'])

    def test_key_annotation_preserves_every_original_byte_and_is_idempotent(self):
        p = service_keys.prepare(self.root)
        original = b'\xef\xbb\xbfELEVENLABS_API_KEY="fake-private"\r\nAPIFY_API_TOKEN=fake-apify\r\n'
        p.write_bytes(original); mode = p.stat().st_mode
        result = service_keys.annotate_optional(self.root)
        self.assertTrue(result['credential_bytes_preserved'])
        self.assertNotIn('fake-private', json.dumps(result))
        content = p.read_bytes(); self.assertTrue(content.startswith(original))
        self.assertEqual(p.stat().st_mode, mode)
        service_keys.annotate_optional(self.root); self.assertEqual(p.read_bytes(), content)
        self.assertEqual(service_keys.read_assignments(p)['ELEVENLABS_API_KEY'], 'fake-private')

    def test_paid_response_limit_removes_partial_file_and_never_retries(self):
        session = MagicMock(); response = session.request.return_value
        response.__enter__.return_value = response; response.status_code = 200
        response.iter_content.return_value = iter([b'1234', b'56789'])
        target = self.root/'partial.mp3'
        with patch.object(audio_remote, 'MAX_RESPONSE_BYTES', 8), patch.object(audio_remote, 'api_key', return_value='fake-key'), patch.object(audio_remote.requests, 'Session') as cls:
            cls.return_value.__enter__.return_value = session
            with self.assertRaisesRegex(ValueError, 'limite'): audio_remote.eleven_request('/v1/music', target, payload={'prompt': 'fixture'})
        self.assertFalse(target.exists()); session.request.assert_called_once()
        self.assertFalse(session.request.call_args.kwargs['allow_redirects'])

    def test_alignment_uses_offline_model_and_records_real_word_times(self):
        def mock_run(command, timeout=600, env=None):
            self.assertEqual(env['HF_HUB_OFFLINE'], '1')
            out = Path(command[command.index('--output')+1])
            out.write_text(json.dumps({'backend': 'fixture-asr', 'text': 'Olá',
                'segments': [{'words': [{'word': 'Olá', 'start': .1, 'end': .5}]}]}))
            return b'', b''
        with patch.object(narrate, 'run', side_effect=mock_run), patch.object(narrate, 'probe', return_value={'duration': .7}):
            result = narrate.align(self.src, 'mlx', 'cached-fixture-model', root=self.root)
        self.assertEqual(result['words'], 1)
        self.assertEqual(json.loads(self.src.with_suffix('.words.json').read_text())['words'][0]['start'], .1)


if __name__ == '__main__': unittest.main()
