"""Pure installer planning/configuration tests; no setup, DB, network or packages."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from install_environment import plan
from factory_setup import desired_setup


class InstallationPlanTests(unittest.TestCase):
    def test_supported_targets_and_native_paths(self):
        for system, machine, manager, backend in (
            ('Darwin', 'arm64', 'brew', 'mlx-whisper'),
            ('Windows', 'AMD64', 'winget', 'faster-whisper'),
            ('Linux', 'x86_64', 'dnf', 'faster-whisper'),
        ):
            with self.subTest(system=system), tempfile.TemporaryDirectory() as d:
                result = plan(d, system, machine, (3, 12), lambda name: '/tools/'+name if name == manager else None, 'glibc')
                self.assertTrue(result['voice_platform_supported'])
                self.assertEqual(result['package_managers'], [manager])
                self.assertEqual(result['speech_backend'], backend)
                self.assertIn('Scripts/python.exe' if system == 'Windows' else 'bin/python', result['check'][0])
                self.assertIn('--preserve-agent-config', result['setup_apply'])
                self.assertEqual(list(Path(d).iterdir()), [])

    def test_new_python_requires_side_by_side_interpreter(self):
        result = plan(ROOT, 'Windows', 'AMD64', (3, 13), lambda _: None, '')
        self.assertFalse(result['compatible_python'])
        self.assertIsNone(result['bootstrap'])
        self.assertTrue(any('lado a lado' in action for action in result['agent_actions']))

    def test_unsupported_voice_does_not_claim_success(self):
        for system, machine, libc in (('Darwin', 'x86_64', ''), ('Linux', 'aarch64', 'glibc'), ('Linux', 'x86_64', 'musl')):
            result = plan(ROOT, system, machine, (3, 12), lambda _: None, libc)
            self.assertFalse(result['voice_platform_supported'])
            self.assertEqual(result['status'], 'plan')
            self.assertTrue(result['setup_requires_explicit_local_data_authorization'])

    def test_paths_with_spaces_are_single_arguments(self):
        result = plan(ROOT / 'folder with spaces', 'Linux', 'x86_64', (3, 11), lambda _: None, 'glibc')
        self.assertIn('folder with spaces', result['check'][0])
        self.assertEqual(result['check'][2:], ['doctor', '--smoke'])


class PreserveAgentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'config').mkdir()
        for name in ('model-catalog.json', 'execution-profiles.json'):
            shutil.copyfile(ROOT / 'config' / name, self.root / 'config' / name)
        shutil.copytree(ROOT / 'adapters', self.root / 'adapters')

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_agents_inherit_session_model(self):
        files = desired_setup(self.root, preserve_agent_config=True)
        self.assertNotIn('.codex/config.toml', files)
        for name, data in files.items():
            if name.endswith('.toml'):
                agent = tomllib.loads(data.decode())
                self.assertNotIn('model', agent)
                self.assertNotIn('model_reasoning_effort', agent)
                self.assertEqual(agent['sandbox_mode'], 'read-only')
            if name.endswith('.md'):
                self.assertNotIn('\nmodel:', data.decode())

    def test_existing_agents_and_settings_preserved(self):
        for name in ('.codex/agents/video-director.toml', '.claude/agents/video-director.md', '.codex/config.toml'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('user-owned choices and permissions\n')
        path = self.root / '.claude/settings.json'
        path.write_text(json.dumps({'model': 'user-choice', 'permissions': {'deny': ['Read(.env)']}}))
        files = desired_setup(self.root, preserve_agent_config=True)
        self.assertNotIn('.codex/agents/video-director.toml', files)
        self.assertNotIn('.claude/agents/video-director.md', files)
        self.assertNotIn('.codex/config.toml', files)
        settings = json.loads(files['.claude/settings.json'])
        self.assertEqual(settings['model'], 'user-choice')
        self.assertEqual(settings['permissions']['deny'], ['Read(.env)'])
        self.assertEqual((self.root / '.codex/config.toml').read_text(), 'user-owned choices and permissions\n')


if __name__ == '__main__':
    unittest.main()
