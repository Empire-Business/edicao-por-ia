"""Platform routing without launching GUI applications or requiring other OSes."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from workspace_navigation import open_path, main


class PortableNavigationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'Fábrica com espaços'
        self.root.mkdir()

    def test_mac_uses_argument_array(self):
        with patch('workspace_navigation.subprocess.run') as run:
            open_path(self.root, 'darwin')
            run.assert_called_once_with(['open',str(self.root.resolve())],check=True)

    def test_windows_uses_native_opener(self):
        with patch('workspace_navigation.os.startfile', create=True) as start:
            open_path(self.root, 'win32')
            start.assert_called_once_with(str(self.root.resolve()))

    def test_linux_uses_xdg_open(self):
        with patch('workspace_navigation.shutil.which', return_value='/usr/bin/xdg-open'), patch('workspace_navigation.subprocess.run') as run:
            open_path(self.root, 'linux')
            run.assert_called_once_with(['/usr/bin/xdg-open',str(self.root.resolve())],check=True)

    def test_linux_gio_fallback_and_missing_opener(self):
        with patch('workspace_navigation.shutil.which', side_effect=lambda name:'/usr/bin/gio' if name=='gio' else None), patch('workspace_navigation.subprocess.run') as run:
            open_path(self.root, 'linux')
            run.assert_called_once_with(['/usr/bin/gio','open',str(self.root.resolve())],check=True)
        with patch('workspace_navigation.shutil.which',return_value=None):
            with self.assertRaises(ValueError):open_path(self.root,'linux')

    def test_launch_action_opens_canonical_folder(self):
        (self.root/'entrada').mkdir()
        with patch('workspace_navigation.open_path') as opener:
            self.assertEqual(main(['--root',str(self.root),'--action','input']),0)
            opener.assert_called_once_with(self.root.resolve()/'entrada')


if __name__=='__main__':
    unittest.main()
