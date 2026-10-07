"""Old layouts/mixed folders recover without merging data or touching originals."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from recover_installation import recover
from project_layout import translate

class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
  self.old=self.base/'antiga';self.old.mkdir();self.dest=self.base/'nova';self.pkg=self.base/'pacote';eng=self.pkg/'99 - Sistema';(eng/'tools').mkdir(parents=True)
  # This fixture migration deliberately needs no optional packages or real user stores.
  (eng/'tools/post_update.py').write_text('print("fixture migration")\n')
  (eng/'tools/factory_common.py').write_text('# engine marker\n')
  (eng/'VERSION').write_text('2.0.1')
  (self.pkg/'.factory-root.json').write_text('{"version":1}')
  (self.pkg/'README.md').write_text('new guide')
  names={'tools/post_update.py':eng/'tools/post_update.py','tools/factory_common.py':eng/'tools/factory_common.py','VERSION':eng/'VERSION','@surface/.factory-root.json':self.pkg/'.factory-root.json','@surface/README.md':self.pkg/'README.md'}
  (eng/'PACKAGE_MANIFEST.json').write_text(json.dumps({'package':'claude-video-factory','version':'2.0.1','release_schema':2,'files':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in names.items()}}))
  (self.old/'jobs/edicao').mkdir(parents=True);(self.old/'jobs/edicao/job.yaml').write_text('spent: 0.40\nsource: old\n')
  (self.old/'jobs/edicao/video.mp4').write_bytes(b'original video fixture')
  (self.old/'context/clients/test').mkdir(parents=True);(self.old/'context/clients/test/memory.sqlite3').write_bytes(b'original archive')
  (self.old/'.factory').mkdir();(self.old/'.factory/edition-codes.json').write_text('{"E01":"edicao"}')
  (self.old/'CHAVES DAS INTEGRAÇÕES.txt').write_text('SYNTHETIC_FIXTURE=abc')
  self.before=self.snapshot()
 def snapshot(self):return {str(p.relative_to(self.old)):p.read_bytes() for p in self.old.rglob('*') if p.is_file() and not p.is_symlink()}
 def assert_original(self):self.assertEqual(self.snapshot(),self.before)
 def test_preview_makes_no_folders_and_reads_no_credentials(self):
  result=recover(self.old,self.dest,self.pkg);self.assertEqual(result['status'],'preview');self.assertFalse(self.dest.exists());self.assert_original()
 def test_flat_recovery_copies_jobs_memory_budget_keys_and_internal_mapping(self):
  result=recover(self.old,self.dest,self.pkg,True);self.assertEqual(result['status'],'recovered');self.assert_original()
  engine=self.dest.resolve()/'99 - Sistema'
  self.assertEqual((engine/'jobs/edicao/job.yaml').read_bytes(),self.before['jobs/edicao/job.yaml'])
  self.assertEqual((engine/'.factory/edition-codes.json').read_bytes(),self.before['.factory/edition-codes.json'])
  self.assertEqual((engine/'context/clients/test/memory.sqlite3').read_bytes(),self.before['context/clients/test/memory.sqlite3'])
  self.assertEqual((self.dest/'CHAVES DAS INTEGRAÇÕES.txt').read_bytes(),self.before['CHAVES DAS INTEGRAÇÕES.txt'])
  self.assertEqual(translate(str(self.old/'jobs/edicao/video.mp4'),engine),str(engine/'jobs/edicao/video.mp4'))
  self.assertEqual(translate('workspace://jobs/edicao/video.mp4',engine),str(engine/'jobs/edicao/video.mp4'))
 def test_existing_destination_and_nested_destination_never_modified(self):
  self.dest.mkdir();(self.dest/'keep').write_text('keep')
  with self.assertRaises(ValueError):recover(self.old,self.dest,self.pkg,True)
  self.assertEqual((self.dest/'keep').read_text(),'keep')
  with self.assertRaises(ValueError):recover(self.old,self.old/'new',self.pkg,True)
  self.assert_original()
 def test_external_link_is_a_blocker_before_any_copy(self):
  outside=self.base/'outside';outside.write_text('outside');(self.old/'jobs/edicao/link').symlink_to(outside)
  result=recover(self.old,self.dest,self.pkg,True);self.assertEqual(result['status'],'blocked_links');self.assertFalse(self.dest.exists());self.assert_original()
 def test_internal_file_link_becomes_portable_regular_file(self):
  (self.old/'jobs/edicao/link.mp4').symlink_to('video.mp4')
  result=recover(self.old,self.dest,self.pkg,True);self.assertTrue(result['ok'])
  link=self.dest/'99 - Sistema/jobs/edicao/link.mp4';self.assertFalse(link.is_symlink());self.assertEqual(link.read_bytes(),b'original video fixture')
 def test_mixed_root_and_engine_data_are_both_preserved_without_merging(self):
  engine=self.old/'99 - Sistema';(engine/'jobs/edicao').mkdir(parents=True);(engine/'jobs/edicao/job.yaml').write_text('newer version')
  self.before=self.snapshot();recover(self.old,self.dest,self.pkg,True);self.assert_original()
  self.assertEqual((self.dest/'99 - Sistema/jobs/edicao/job.yaml').read_text(),'newer version')
  self.assertEqual((self.dest/'99 - Sistema/arquivo/recuperacao/raiz/jobs/edicao/job.yaml').read_bytes(),self.before['jobs/edicao/job.yaml'])
 def test_old_code_customization_is_archived_not_executed(self):
  (self.old/'tools').mkdir();(self.old/'tools/post_update.py').write_text('raise RuntimeError("old code")')
  self.before=self.snapshot();recover(self.old,self.dest,self.pkg,True);self.assert_original()
  self.assertEqual((self.dest/'99 - Sistema/arquivo/recuperacao/engine/tools/post_update.py').read_text(),'raise RuntimeError("old code")')
 def test_failed_migration_never_publishes_destination(self):
  import recover_installation
  with patch.object(recover_installation.subprocess,'run',return_value=type('Result',(),{'returncode':1})()):
   with self.assertRaises(ValueError):recover(self.old,self.dest,self.pkg,True)
  self.assertFalse(self.dest.exists());self.assert_original();self.assertFalse(list(self.base.glob('.recovery-*')))
 def test_corrupt_package_and_running_update_are_blocked(self):
  (self.pkg/'99 - Sistema/VERSION').write_text('corrupt')
  with self.assertRaises(ValueError):recover(self.old,self.dest,self.pkg,True)
  self.assertFalse(self.dest.exists());self.assert_original()
 def test_busy_installation_preserves_source(self):
  (self.old/'.factory/update.lock').write_text('');self.before=self.snapshot()
  with self.assertRaises(ValueError):recover(self.old,self.dest,self.pkg,True)
  self.assertFalse(self.dest.exists());self.assert_original()
 def test_no_space_leaves_source_and_destination_intact(self):
  with patch('recover_installation.shutil.disk_usage',return_value=type('Usage',(),{'free':0})()):
   with self.assertRaises(ValueError):recover(self.old,self.dest,self.pkg,True)
  self.assertFalse(self.dest.exists());self.assert_original()

if __name__=='__main__':unittest.main()
