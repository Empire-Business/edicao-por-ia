"""The human area contains real folders; compatibility flags do not hide the engine."""
import os,stat,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from organize_workspace import organize,VISIBLE

class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        for name in VISIBLE:
            p=self.root/name
            if name.endswith('.html'):p.write_text('fixture')
            else:p.mkdir()
        (self.root/'AGENTS.md').write_text('fixture')
    def test_preview_does_not_change_flags(self):
        before=(self.root/'AGENTS.md').stat()
        report=organize(self.root)
        self.assertFalse(report['applied'])
        after=(self.root/'AGENTS.md').stat()
        self.assertEqual(after.st_mode,before.st_mode)
        self.assertEqual(after.st_mtime_ns,before.st_mtime_ns)
        if hasattr(before,'st_flags'):self.assertEqual(after.st_flags,before.st_flags)
    def test_keys_file_stays_visible_after_presentation(self):
        from service_keys import KEY_FILE
        organize(self.root,apply=True)
        self.assertTrue((self.root/KEY_FILE).is_file())
        self.assertNotIn(KEY_FILE,(self.root/'.hidden').read_text().splitlines())
        if sys.platform=='darwin':
            self.assertFalse((self.root/KEY_FILE).stat().st_flags & stat.UF_HIDDEN)
    def test_user_symlink_is_not_accepted(self):
        (self.root/'04 - Formatos').rmdir()
        (self.root/'04 - Formatos').symlink_to('99 - Sistema',target_is_directory=True)
        with self.assertRaises(ValueError):organize(self.root,apply=True)
    @unittest.skipUnless(sys.platform=='darwin','macOS flags')
    def test_only_compatibility_entries_are_hidden_and_restorable(self):
        (self.root/'old-tools').symlink_to('99 - Sistema',target_is_directory=True)
        organize(self.root,apply=True)
        self.assertTrue((self.root/'old-tools').lstat().st_flags & stat.UF_HIDDEN)
        for name in VISIBLE:self.assertFalse((self.root/name).lstat().st_flags & stat.UF_HIDDEN)
        organize(self.root,apply=True,restore=True)
        self.assertFalse((self.root/'old-tools').lstat().st_flags & stat.UF_HIDDEN)

if __name__=='__main__':unittest.main()
