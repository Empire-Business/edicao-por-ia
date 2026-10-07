"""Offline integration tests with synthetic keys and mocked provider/media responses."""
import contextlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import service_keys
import scrapecreators
import broll_research as broll


class KeysTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {}, clear=True).start()

    def test_visible_empty_template_is_private_and_setup_never_reads_or_overwrites_it(self):
        path = service_keys.prepare(self.root)
        self.assertEqual(path.name, 'CHAVES DAS INTEGRAÇÕES.txt')
        self.assertEqual(service_keys.read_assignments(path), {})
        if os.name != 'nt': self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        path.write_text('ELEVENLABS_API_KEY=fake-existing-key\n')
        with patch.object(Path, 'read_text', side_effect=AssertionError('setup cannot read secrets')):
            self.assertEqual(service_keys.prepare(self.root), path)
        self.assertIn('fake-existing-key', path.read_text())

    def test_visible_file_wins_over_environment(self):
        path = service_keys.prepare(self.root)
        path.write_text('SCRAPECREATORS_API_KEY="fake-visible"\nELEVENLABS_API_KEY=fake-voice\n')
        os.environ['SCRAPECREATORS_API_KEY'] = 'fake-stale'
        self.assertEqual(service_keys.api_key('SCRAPECREATORS_API_KEY', self.root), 'fake-visible')
        self.assertEqual(service_keys.api_key('ELEVENLABS_API_KEY', self.root), 'fake-voice')

    def test_empty_visible_file_preserves_environment_and_legacy_env(self):
        service_keys.prepare(self.root)
        os.environ['SCRAPECREATORS_API_KEY'] = 'fake-env'
        (self.root / '.env').write_text("export ELEVENLABS_API_KEY='fake-legacy'\n")
        self.assertEqual(service_keys.api_key('SCRAPECREATORS_API_KEY', self.root), 'fake-env')
        self.assertEqual(service_keys.api_key('ELEVENLABS_API_KEY', self.root), 'fake-legacy')

    def test_legacy_local_json_still_works(self):
        (self.root / 'config').mkdir()
        (self.root / 'config/scrapecreators.local.json').write_text('{"api_key":"fake-old"}')
        self.assertEqual(service_keys.api_key('SCRAPECREATORS_API_KEY', self.root), 'fake-old')

    def test_relocated_engine_reads_visible_root(self):
        engine = self.root / '99 - Sistema'; (engine / 'tools').mkdir(parents=True)
        (engine / 'tools/factory_common.py').write_text('fixture')
        (self.root / '.factory-root.json').write_text('{}')
        service_keys.prepare(engine).write_text('ELEVENLABS_API_KEY=fake-root\n')
        self.assertEqual(service_keys.api_key('ELEVENLABS_API_KEY', engine), 'fake-root')

    def test_missing_key_tells_user_the_visible_file(self):
        with self.assertRaisesRegex(ValueError, service_keys.KEY_FILE):
            service_keys.api_key('ELEVENLABS_API_KEY', self.root)

    def test_parser_does_not_execute_shell_text(self):
        path = service_keys.prepare(self.root)
        path.write_text('SCRAPECREATORS_API_KEY=$(touch /tmp/never-run)\n')
        with patch('subprocess.run', side_effect=AssertionError('must not execute')):
            with self.assertRaises(ValueError) as error:
                service_keys.api_key('SCRAPECREATORS_API_KEY', self.root)
        self.assertNotIn('never-run', str(error.exception))

    def test_symlink_rejected(self):
        outside = self.root / 'outside'; outside.write_text('fake-key')
        (self.root / service_keys.KEY_FILE).symlink_to(outside)
        with self.assertRaises(ValueError): service_keys.prepare(self.root)
        with self.assertRaises(ValueError): service_keys.api_key('ELEVENLABS_API_KEY', self.root)


class ProviderTests(unittest.TestCase):
    def test_api_sends_key_only_to_scrapecreators_header(self):
        with patch.object(scrapecreators, 'key', return_value='fake-key'), patch.object(scrapecreators.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"success":true}')) as call:
            scrapecreators.yt_search('tela de produto')
        request = call.call_args.args[0]
        self.assertTrue(request.full_url.startswith('https://api.scrapecreators.com/v1/youtube/search?'))
        self.assertEqual(request.get_header('X-api-key'), 'fake-key')
        self.assertNotIn('fake-key', request.full_url)

    def test_api_key_is_not_forwarded_on_redirect(self):
        with patch.object(scrapecreators,'key',return_value='fake-key'), patch.object(scrapecreators.urllib.request,'urlopen',return_value=io.BytesIO(b'{"success":true}')) as call:
            scrapecreators.yt_search('office')
        original=call.call_args.args[0]
        redirected=scrapecreators.urllib.request.HTTPRedirectHandler().redirect_request(original,None,302,'',{},'https://cdn.example/other')
        self.assertIsNone(redirected.get_header('X-api-key'))

    def test_http_and_provider_errors_never_echo_body(self):
        for response in (urllib.error.HTTPError('https://api.scrapecreators.com',401,'secret-in-message',{},io.BytesIO(b'fake-secret')),
                         io.BytesIO(b'{"success":false,"message":"fake-secret"}')):
            kwargs={'side_effect':response} if isinstance(response,Exception) else {'return_value':response}
            with patch.object(scrapecreators,'key',return_value='fake-key'), patch.object(scrapecreators.urllib.request,'urlopen',**kwargs):
                with self.assertRaises(ValueError) as error: scrapecreators.yt_video('https://youtu.be/abcdefghijk')
            self.assertNotIn('fake-secret',str(error.exception)); self.assertNotIn('secret-in-message',str(error.exception))


class BrollTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.job = Path(self.temp.name)
        (self.job / 'job.yaml').write_text('{"format":"synthetic","visual_identity":"ID01"}')

    def test_no_format_blocks_before_api(self):
        (self.job / 'job.yaml').write_text('{"format":null}')
        with patch.object(broll,'api') as api:
            with self.assertRaisesRegex(ValueError,'Qual formato'): broll.search(self.job,'office','both')
            api.assert_not_called()

    def test_both_platform_searches_use_only_provider(self):
        with patch.object(broll,'api',return_value={'success':True}) as api, contextlib.redirect_stdout(io.StringIO()):
            broll.search(self.job,'office','both')
        self.assertEqual([c.args[0] for c in api.call_args_list],['tiktok/search/keyword','youtube/search'])
        self.assertEqual(len(list((self.job/'assets/viral/search').glob('*.json'))),2)

    def test_direct_youtube_link_records_unavailable_without_fallback(self):
        with patch.object(broll,'yt_video',return_value={'title':'Example','channel':{'handle':'example'}}) as api, patch.object(broll,'download') as download, contextlib.redirect_stdout(io.StringIO()):
            result = broll.get(self.job,['https://www.youtube.com/watch?v=abcdefghijk=cena'])
        api.assert_called_once_with('https://www.youtube.com/watch?v=abcdefghijk')
        download.assert_not_called()
        self.assertEqual(result[0]['status'],'media_unavailable')
        self.assertEqual(result[0]['provider'],'scrapecreators')
        self.assertFalse(result[0]['downloaded'])

    def test_youtube_explicit_media_only_and_tiktok_play_urls(self):
        self.assertEqual(broll.media_urls({'url':'https://youtube.com/watch?v=abcdefghijk','thumbnail':'https://example.com/image.jpg'},'youtube'),[])
        self.assertEqual(broll.media_urls({'downloadOptions':{'formats':[{'url':'https://cdn.example/video.mp4','height':720},{'url':'https://cdn.example/audio','mimeType':'audio/mp4'}]}},'youtube'),['https://cdn.example/video.mp4'])
        self.assertEqual(broll.media_urls({'aweme_detail':{'video':{'play_addr':{'url_list':['https://cdn.example/video.mp4']}}}},'tiktok'),['https://cdn.example/video.mp4'])

    def test_expired_tiktok_search_urls_refresh_through_same_provider(self):
        d = self.job / 'assets/viral/search'; d.mkdir(parents=True)
        video = {'aweme_id':'123456789012345678','author':{'unique_id':'sample'},'video':{'play_addr':{'url_list':['https://cdn.example/expired']}}}
        (d / 'tt_office.json').write_text(json.dumps({'search_item_list':[{'aweme_info':video}]}))
        with patch.object(broll,'download',side_effect=[False,True]) as download, patch.object(broll,'tt_video',return_value={'aweme_detail':{'video':{'play_addr':{'url_list':['https://cdn.example/new']}}}}) as api, contextlib.redirect_stdout(io.StringIO()):
            result = broll.get(self.job,['123456789012345678=cena'])
        api.assert_called_once_with('https://www.tiktok.com/@sample/video/123456789012345678')
        self.assertEqual(download.call_args.args[0],['https://cdn.example/new'])
        self.assertTrue(result[0]['downloaded'])

    def test_provider_failure_is_persisted_without_success(self):
        with patch.object(broll,'yt_video',side_effect=ValueError('ScrapeCreators HTTP 403')), contextlib.redirect_stdout(io.StringIO()):
            result = broll.get(self.job,['abcdefghijk=cena'])
        saved = json.loads((self.job/'assets/viral/sources.json').read_text())
        self.assertEqual(saved,result); self.assertEqual(saved[0]['status'],'api_error')
        self.assertFalse(saved[0]['downloaded'])

    def test_invalid_names_rejected_before_calls(self):
        with patch.object(broll,'yt_video') as api:
            for value in ['abcdefghijk=../escape','https://example.com/video=cena','abcdefghijk=cena/escape']:
                with self.assertRaises(ValueError): broll.get(self.job,[value])
            api.assert_not_called()

    def test_http_error_page_is_rejected_and_previous_media_preserved(self):
        output = self.job / 'video.mp4'; output.write_bytes(b'previous-valid-media')
        def fake_run(command, **kwargs):
            if command[0] == 'curl':
                Path(command[command.index('-o')+1]).write_text('<html>Error</html>')
                return subprocess.CompletedProcess(command,0)
            return subprocess.CompletedProcess(command,1,'{}','Invalid video')
        with patch.object(broll.subprocess,'run',side_effect=fake_run):
            self.assertFalse(broll.download(['https://cdn.example/invalid'],output,'youtube'))
        self.assertEqual(output.read_bytes(),b'previous-valid-media')
        self.assertFalse(output.with_suffix('.part.mp4').exists())


if __name__ == '__main__': unittest.main()
