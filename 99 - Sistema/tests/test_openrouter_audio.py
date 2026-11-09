"""Offline tests for OpenRouter music/narration and the 2.11.0 keys file notes.

Fake keys, mocked HTTP sessions and synthetic audio made with FFmpeg. No network, nothing paid.
"""
import base64
import json
import math
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import audio_remote
import narrate
import or_music
import post_update
import service_keys

FFMPEG = shutil.which('ffmpeg')


def tone_mp3(path, seconds):
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-f', 'lavfi', '-i', f'sine=frequency=330:duration={seconds}',
                    '-ar', '44100', '-ac', '2', '-c:a', 'libmp3lame', '-b:a', '128k', str(path)], check=True)
    return Path(path).read_bytes()


def pcm_tone(seconds, rate=24000):
    return b''.join(struct.pack('<h', int(6000 * math.sin(2 * math.pi * 220 * i / rate))) for i in range(round(seconds * rate)))


def rms(path, start, end):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-ss', str(start), '-t', str(end - start), '-i', str(path),
                          '-ac', '1', '-ar', '8000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
    samples = struct.unpack(f'<{len(raw) // 2}h', raw)
    return math.sqrt(sum(x * x for x in samples) / max(1, len(samples)))


def sse(audio, cost=0.04, generation='gen-fixture', piece=4096):
    encoded = base64.b64encode(audio).decode()
    events = [b': OPENROUTER PROCESSING', b'']
    for i in range(0, len(encoded), piece):
        events += [b'data: ' + json.dumps({'id': generation, 'choices': [{'delta': {'audio': {'data': encoded[i:i + piece]}}}]}).encode(), b'']
    events += [b'data: ' + json.dumps({'id': generation, 'choices': [{'delta': {'content': '<instrumental>'}}]}).encode(), b'']
    events += [b'data: ' + json.dumps({'id': generation, 'choices': [], 'usage': {'cost': cost}}).encode(), b'', b'data: [DONE]', b'']
    return b'\n'.join(events)


def fake_session(status=200, chunks=(), headers=None):
    session = MagicMock()
    response = session.request.return_value
    response.__enter__.return_value = response
    response.status_code = status
    response.headers = headers or {}
    response.iter_content.return_value = iter(chunks)
    response.raw.read.return_value = b'{"error":{"message":"fixture detail"}}'
    return session


class OpenRouterClientTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(audio_remote, 'api_key', return_value='fake-or-key').start()

    def run_music(self, session):
        with patch.object(audio_remote.requests, 'Session', return_value=session):
            return audio_remote.openrouter_music('google/lyria-3-clip-preview', 'Calm piano, 80 BPM.')

    def test_sse_pieces_are_joined_and_cost_comes_from_usage(self):
        audio = bytes(range(256)) * 50
        body = sse(audio, cost=0.0412)
        # Arbitrary network chunking must not break lines or base64 pieces.
        session = fake_session(chunks=[body[i:i + 777] for i in range(0, len(body), 777)])
        result = self.run_music(session)
        self.assertEqual(result['audio'], audio)
        self.assertEqual(result['cost_usd'], 0.0412)
        self.assertEqual(result['text'], '<instrumental>')
        self.assertEqual(result['generation_id'], 'gen-fixture')
        call = session.request.call_args
        self.assertEqual(call.args[:2], ('POST', 'https://openrouter.ai/api/v1/chat/completions'))
        self.assertEqual(call.kwargs['headers'], {'Authorization': 'Bearer fake-or-key'})
        payload = call.kwargs['json']
        self.assertEqual((payload['model'], payload['stream'], payload['modalities'], payload['audio']),
                         ('google/lyria-3-clip-preview', True, ['text', 'audio'], {'format': 'mp3'}))
        self.assertEqual(payload['messages'], [{'role': 'user', 'content': 'Calm piano, 80 BPM.'}])
        self.assertFalse(call.kwargs['allow_redirects']); self.assertFalse(session.trust_env)
        session.request.assert_called_once()

    def test_http_errors_are_explained_once_without_retry_or_key(self):
        cases = {401: 'recusou a chave', 402: 'sem créditos', 429: 'instável', 503: 'instável', 400: 'fixture detail'}
        for status, text in cases.items():
            session = fake_session(status=status)
            with self.assertRaises(ValueError) as error:
                self.run_music(session)
            self.assertIn(text, str(error.exception))
            self.assertNotIn('fake-or-key', str(error.exception))
            session.request.assert_called_once()
        self.assertIn('biblioteca local', audio_remote.openrouter_error(402))
        self.assertIn('não houve nova tentativa', audio_remote.openrouter_error(503).lower())

    def test_stream_error_or_missing_audio_is_reported(self):
        error_event = b'data: {"error": {"message": "provider overloaded"}}\n\n'
        with self.assertRaisesRegex(ValueError, 'provider overloaded'):
            self.run_music(fake_session(chunks=[error_event]))
        with self.assertRaisesRegex(ValueError, 'sem áudio'):
            self.run_music(fake_session(chunks=[b'data: {"choices": []}\n\ndata: [DONE]\n\n']))

    def test_response_size_limit(self):
        with patch.object(audio_remote, 'MAX_RESPONSE_BYTES', 10):
            with self.assertRaisesRegex(ValueError, 'limite'):
                self.run_music(fake_session(chunks=[b'data: ' + b'x' * 20]))

    def test_speech_writes_raw_audio_and_rejects_non_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'voice.raw'
            session = fake_session(chunks=[b'abc', b'def'], headers={'Content-Type': 'audio/pcm;rate=24000;channels=1', 'X-Generation-Id': 'gen-tts'})
            with patch.object(audio_remote.requests, 'Session', return_value=session):
                meta = audio_remote.openrouter_speech({'model': 'm/x', 'input': 'oi', 'voice': 'Kore'}, target)
            self.assertEqual(target.read_bytes(), b'abcdef')
            self.assertEqual(meta, {'content_type': 'audio/pcm;rate=24000;channels=1', 'generation_id': 'gen-tts'})
            self.assertEqual(session.request.call_args.args[1], 'https://openrouter.ai/api/v1/audio/speech')
            other = Path(folder) / 'json.raw'
            session = fake_session(chunks=[b'{}'], headers={'Content-Type': 'application/json'})
            with patch.object(audio_remote.requests, 'Session', return_value=session):
                with self.assertRaisesRegex(ValueError, 'não devolveu áudio'):
                    audio_remote.openrouter_speech({'model': 'm/x'}, other)
            self.assertFalse(other.exists())

    def test_key_check_never_returns_key_or_label(self):
        body = json.dumps({'data': {'label': 'sk-or-v1-abc...xyz', 'limit': 5, 'limit_remaining': 4.2, 'usage': 0.8, 'is_free_tier': False}}).encode()
        session = fake_session(chunks=[body])
        with patch.object(audio_remote.requests, 'Session', return_value=session):
            result = audio_remote.openrouter_key_status()
        self.assertEqual(result['limit_remaining_usd'], 4.2)
        self.assertNotIn('sk-or', json.dumps(result)); self.assertNotIn('fake-or-key', json.dumps(result))
        self.assertEqual(session.request.call_args.args[:2], ('GET', 'https://openrouter.ai/api/v1/key'))

    def test_elevenlabs_is_restricted_to_noise_isolation(self):
        for endpoint in ('/v1/music', '/v1/text-to-speech/voice/with-timestamps', '/v2/voices'):
            with patch.object(audio_remote.requests, 'Session', side_effect=AssertionError('no call')):
                with self.assertRaisesRegex(ValueError, 'só isola ruído'):
                    audio_remote.eleven_request(endpoint, payload={})


class MusicToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.addCleanup(patch.stopall)

    def test_model_choice_limits_and_estimate(self):
        self.assertEqual(or_music.estimate(30), ('google/lyria-3-clip-preview', 0.04))
        self.assertEqual(or_music.estimate(31), ('google/lyria-3-pro-preview', 0.08))
        self.assertEqual(or_music.choose_model(10, 'pro'), 'google/lyria-3-pro-preview')
        with self.assertRaisesRegex(ValueError, 'clip'): or_music.choose_model(60, 'clip')
        with self.assertRaises(ValueError): or_music.choose_model(20, 'elevenlabs/music')
        for seconds in (2, 241, float('nan')):
            with self.assertRaisesRegex(ValueError, 'Duração'): or_music.check_seconds(seconds)
        prompt = or_music.build_prompt('Warm acoustic guitar, 90 BPM, builds to a hopeful chorus', 45)
        self.assertIn('Instrumental only, no vocals.', prompt); self.assertIn('45 seconds', prompt)

    def test_refuses_without_accept_paid_before_key_or_call_and_shows_cost(self):
        patch.object(service_keys, 'api_key', side_effect=AssertionError('no keys')).start()
        patch.object(audio_remote, 'openrouter_music', side_effect=AssertionError('no call')).start()
        with self.assertRaisesRegex(ValueError, r'US\$ 0,08') as error:
            or_music.generate('Dark synth pulse, 100 BPM', 60, self.root / 'music.mp3', root=self.root)
        self.assertIn('--accept-paid', str(error.exception))
        self.assertFalse((self.root / 'music.mp3').exists())

    def test_never_overwrites_output_or_receipt(self):
        patch.object(audio_remote, 'openrouter_music', side_effect=AssertionError('no call')).start()
        (self.root / 'music.mp3').write_bytes(b'previous')
        with self.assertRaises(ValueError):
            or_music.generate('Dark synth pulse, 100 BPM', 20, self.root / 'music.mp3', accept_paid=True, root=self.root)
        self.assertEqual((self.root / 'music.mp3').read_bytes(), b'previous')
        (self.root / 'other.audio.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Recibo'):
            or_music.generate('Dark synth pulse, 100 BPM', 20, self.root / 'other.mp3', accept_paid=True, root=self.root)
        with self.assertRaisesRegex(ValueError, 'mp3'):
            or_music.generate('Dark synth pulse, 100 BPM', 20, self.root / 'music.wav', accept_paid=True, root=self.root)

    def test_longer_result_is_cut_to_requested_length_with_fade_and_receipt(self):
        if not FFMPEG: self.skipTest('FFmpeg absent')
        audio = tone_mp3(self.root / 'source.mp3', 12)
        calls = []
        def fake(model, prompt):
            calls.append((model, prompt))
            return {'audio': audio, 'text': '<instrumental>', 'cost_usd': 0.04, 'generation_id': 'gen-1'}
        patch.object(audio_remote, 'openrouter_music', side_effect=fake).start()
        out = self.root / 'music/track.mp3'
        result = or_music.generate('Calm piano, 80 BPM, soft ending', 8, out, accept_paid=True, root=self.root)
        self.assertEqual(len(calls), 1); self.assertEqual(calls[0][0], 'google/lyria-3-clip-preview')
        self.assertAlmostEqual(result['duration'], 8, delta=0.1)
        self.assertTrue(result['trimmed']); self.assertEqual(result['fade_out_seconds'], 2)
        self.assertGreater(result['raw_duration'], 11.5)
        self.assertGreater(rms(out, 3, 4), 4 * rms(out, 7.85, 7.98))  # fades out at the end
        saved = json.loads(out.with_suffix('.audio.json').read_text())
        self.assertEqual((saved['provider'], saved['model'], saved['cost_usd'], saved['quality_review']),
                         ('openrouter', 'google/lyria-3-clip-preview', 0.04, 'pending_listening'))
        self.assertTrue(saved['paid_request']); self.assertFalse(saved['shorter_than_requested'])
        self.assertEqual(saved['output_sha256'], or_music.digest(out))
        self.assertTrue(saved['output'].startswith('workspace://'))
        self.assertEqual(sorted(p.name for p in out.parent.iterdir()), ['track.audio.json', 'track.mp3'])

    def test_shorter_result_is_kept_and_reported_not_stretched(self):
        if not FFMPEG: self.skipTest('FFmpeg absent')
        audio = tone_mp3(self.root / 'source.mp3', 5)
        patch.object(audio_remote, 'openrouter_music', return_value={'audio': audio, 'text': '', 'cost_usd': 0.08, 'generation_id': None}).start()
        result = or_music.generate('Upbeat drums, 120 BPM', 40, self.root / 'short.mp3', accept_paid=True, root=self.root)
        self.assertFalse(result['trimmed']); self.assertTrue(result['shorter_than_requested'])
        self.assertEqual(result['model'], 'google/lyria-3-pro-preview')
        self.assertLess(result['duration'], 6); self.assertIn('Não foi esticada', result['warning'])
        self.assertEqual((self.root / 'short.mp3').read_bytes(), audio)

    def test_provider_failure_saves_nothing_and_suggests_library(self):
        patch.object(audio_remote, 'api_key', return_value='fake-or-key').start()
        session = fake_session(status=402)
        patch.object(audio_remote.requests, 'Session', return_value=session).start()
        with self.assertRaisesRegex(ValueError, 'biblioteca local'):
            or_music.generate('Calm piano, 80 BPM', 20, self.root / 'x.mp3', accept_paid=True, root=self.root)
        session.request.assert_called_once()
        self.assertEqual([p.name for p in self.root.iterdir()], [])

    def test_retired_el_music_explains_new_command_without_calling_anything(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/el_music.py'), '--accept-paid', '--prompt', 'x', '--seconds', '30', '--out', 'x.mp3'],
                                capture_output=True, text=True, env={'PATH': os.environ.get('PATH', '')})
        self.assertEqual(result.returncode, 2)
        self.assertIn('or_music.py', result.stderr); self.assertIn('OpenRouter', result.stderr)
        self.assertEqual(result.stdout, '')


class NarrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.text = self.root / 'texto.txt'; self.text.write_text('Olá, esta é uma narração de teste.', encoding='utf-8')
        self.addCleanup(patch.stopall)

    def test_openrouter_is_default_and_paid_requires_consent(self):
        patch.object(service_keys, 'api_key', side_effect=AssertionError('no keys')).start()
        patch.object(audio_remote, 'openrouter_speech', side_effect=AssertionError('no call')).start()
        with self.assertRaisesRegex(ValueError, 'accept-paid'):
            narrate.speak(self.text, self.root / 'n.wav', root=self.root)
        with self.assertRaisesRegex(ValueError, 'openrouter'):
            narrate.speak(self.text, self.root / 'n.wav', 'voz', 'elevenlabs', accept_paid=True, root=self.root)
        with self.assertRaisesRegex(ValueError, '--voice'):
            narrate.speak(self.text, self.root / 'n.wav', None, 'openrouter', 'elevenlabs/eleven-multilingual-v2', accept_paid=True, root=self.root)
        self.assertFalse((self.root / 'n.wav').exists())

    def test_gemini_pcm_becomes_wav_with_receipt_and_pending_alignment(self):
        if not FFMPEG: self.skipTest('FFmpeg absent')
        sent = []
        def fake(payload, output):
            sent.append(payload); Path(output).write_bytes(pcm_tone(1.5))
            return {'content_type': 'audio/pcm;rate=24000;channels=1', 'generation_id': 'gen-tts'}
        patch.object(audio_remote, 'openrouter_speech', side_effect=fake).start()
        result = narrate.speak(self.text, self.root / 'narracao.wav', accept_paid=True, root=self.root)
        self.assertEqual(len(sent), 1)
        self.assertEqual((sent[0]['model'], sent[0]['voice'], sent[0]['response_format']), ('google/gemini-3.8-flash-tts', 'Kore', 'pcm'))
        self.assertIn('português do Brasil', sent[0]['instructions']); self.assertNotIn('speed', sent[0])
        self.assertEqual(sent[0]['input'], 'Olá, esta é uma narração de teste.')
        self.assertAlmostEqual(result['duration'], 1.5, delta=0.02)
        saved = json.loads((self.root / 'narracao.audio.json').read_text())
        self.assertEqual((saved['provider'], saved['generation_id'], saved['alignment'], saved['quality_review']),
                         ('openrouter', 'gen-tts', 'pending_local_transcription', 'pending_listening'))
        self.assertTrue(saved['paid_request']); self.assertFalse(saved['cloud_fallback'])
        self.assertEqual(saved['output_sha256'], narrate.digest(self.root / 'narracao.wav'))
        self.assertFalse((self.root / 'narracao.words.json').exists())
        info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(self.root / 'narracao.wav')],
                                         capture_output=True, check=True).stdout)['streams'][0]
        self.assertEqual((info['sample_rate'], info['channels']), ('24000', 1))
        with self.assertRaises(ValueError):  # never overwrites
            narrate.speak(self.text, self.root / 'narracao.wav', accept_paid=True, root=self.root)

    def test_other_models_receive_mp3_and_explicit_voice(self):
        if not FFMPEG: self.skipTest('FFmpeg absent')
        audio = tone_mp3(self.root / 'tts.mp3', 1)
        sent = []
        def fake(payload, output):
            sent.append(payload); Path(output).write_bytes(audio)
            return {'content_type': 'audio/mpeg', 'generation_id': None}
        patch.object(audio_remote, 'openrouter_speech', side_effect=fake).start()
        result = narrate.speak(self.text, self.root / 'n.mp3', 'Rachel', 'openrouter', 'elevenlabs/eleven-multilingual-v2',
                               speed=1.1, accept_paid=True, root=self.root)
        self.assertEqual((sent[0]['response_format'], sent[0]['voice'], sent[0]['speed']), ('mp3', 'Rachel', 1.1))
        self.assertNotIn('instructions', sent[0])
        self.assertAlmostEqual(result['duration'], 1, delta=0.1)

    def test_pcm_header_parsing(self):
        self.assertEqual(narrate.pcm_input('audio/pcm;rate=24000;channels=1'), ['-f', 's16le', '-ar', '24000', '-ac', '1'])
        self.assertEqual(narrate.pcm_input('audio/pcm'), ['-f', 's16le', '-ar', '24000', '-ac', '1'])
        for bad in ('audio/pcm;rate=abc', 'audio/pcm;rate=5;channels=1', 'audio/pcm;channels=6'):
            with self.assertRaises(ValueError): narrate.pcm_input(bad)
        with self.assertRaisesRegex(ValueError, 'Modelo'):
            narrate.openrouter_payload('oi', 'Kore', 'not a model', 1, None)


class KeysFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {}, clear=True).start()

    def test_new_template_explains_services_in_plain_language(self):
        path = service_keys.prepare(self.root)
        text = path.read_text(encoding='utf-8')
        for expected in ('https://openrouter.ai/settings/keys', 'música com IA, a narração', 'limite de gasto',
                         'só para tratar ruído', 'https://elevenlabs.io/app/settings/api-keys', 'Nunca cole uma chave na conversa',
                         'COMO CONFIGURAR O OPENROUTER.html', service_keys.SERVICES_MARKER):
            self.assertIn(expected, text)
        self.assertEqual(service_keys.read_assignments(path), {})
        before = path.read_bytes()
        self.assertEqual(service_keys.annotate_services(self.root)['status'], 'already_documented')
        self.assertEqual(path.read_bytes(), before)

    def test_old_file_gets_notes_and_missing_line_without_touching_values(self):
        path = service_keys.prepare(self.root)
        original = b'\xef\xbb\xbfSCRAPECREATORS_API_KEY=fake-scrape\r\nELEVENLABS_API_KEY="fake-eleven"\r\nAPIFY_API_TOKEN=fake-apify'
        path.write_bytes(original); os.chmod(path, 0o600)
        result = service_keys.annotate_services(self.root)
        self.assertEqual(result['status'], 'service_notes_added')
        self.assertEqual(result['empty_lines_added'], ['OPENROUTER_API_KEY'])
        self.assertNotIn('fake', json.dumps(result))
        content = path.read_bytes()
        self.assertTrue(content.startswith(original))
        self.assertIn(b'\nOPENROUTER_API_KEY=\n', content)
        self.assertEqual(service_keys.read_assignments(path), {'SCRAPECREATORS_API_KEY': 'fake-scrape',
                         'ELEVENLABS_API_KEY': 'fake-eleven', 'APIFY_API_TOKEN': 'fake-apify'})
        if os.name != 'nt': self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(service_keys.annotate_services(self.root)['status'], 'already_documented')
        self.assertEqual(path.read_bytes(), content)

    def test_existing_openrouter_value_is_kept_and_not_duplicated(self):
        path = service_keys.prepare(self.root)
        path.write_text('# antigo\nexport OPENROUTER_API_KEY=fake-router\n', encoding='utf-8')
        result = service_keys.annotate_services(self.root)
        self.assertEqual(result['empty_lines_added'], [])
        self.assertEqual(path.read_text(encoding='utf-8').count('OPENROUTER_API_KEY='), 1)
        self.assertEqual(service_keys.api_key('OPENROUTER_API_KEY', self.root), 'fake-router')

    def test_no_file_is_not_created_by_the_update_and_errors_never_block(self):
        self.assertEqual(service_keys.annotate_services(self.root)['status'], 'no_keys_file')
        self.assertFalse((self.root / service_keys.KEY_FILE).exists())
        outside = self.root / 'outside.txt'; outside.write_text('OPENROUTER_API_KEY=fake')
        (self.root / service_keys.KEY_FILE).symlink_to(outside)
        result = post_update.annotate_keys(self.root)
        self.assertEqual((result['ok'], result['status']), (False, 'skipped'))
        self.assertEqual(outside.read_text(), 'OPENROUTER_API_KEY=fake')

    def test_missing_openrouter_key_points_to_the_guide(self):
        service_keys.prepare(self.root)
        with self.assertRaisesRegex(ValueError, 'COMO CONFIGURAR O OPENROUTER'):
            service_keys.api_key('OPENROUTER_API_KEY', self.root)


if __name__ == '__main__': unittest.main()
