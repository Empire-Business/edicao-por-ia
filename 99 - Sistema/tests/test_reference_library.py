"""Published references accompany every stock F; private stores remain outside releases."""
import base64,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from bootstrap_update import prepare
from update_local import allowed,validate_manifest
from design_catalog import catalogue,initialize_defaults,complete_stock_examples,save
from client_memory import Memory

class BootstrapTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  (self.root/'tools').mkdir();(self.root/'tools/update_local.py').write_text('# old active updater\n')
  self.code=b'print("verified fixture updater")\n';self.sha='a'*40
 def responses(self,code=None,repository_id=1408655066):
  manifest={'package':'claude-video-factory','minimum_python':'3.11','files':{'tools/update_local.py':hashlib.sha256(self.code).hexdigest()}}
  return [{'id':repository_id},{'sha':self.sha},{'content':base64.b64encode(json.dumps(manifest).encode()).decode()},{'content':base64.b64encode(code or self.code).decode()}]
 def test_prepare_verifies_pinned_code_without_touching_active_updater(self):
  before=(self.root/'tools/update_local.py').read_bytes()
  with patch('bootstrap_update.remote',side_effect=self.responses()) as api:result=prepare(self.root)
  self.assertEqual((self.root/'tools/update_local.py').read_bytes(),before)
  self.assertEqual(Path(result['updater']).read_bytes(),self.code);self.assertTrue(result['active_code_unchanged'])
  for call in api.call_args_list[2:]:self.assertIn('?ref='+self.sha,call.args[1])
 def test_wrong_code_checksum_never_writes_or_executes_code(self):
  with patch('bootstrap_update.remote',side_effect=self.responses(b'print("wrong")\n')):
   with self.assertRaises(ValueError):prepare(self.root)
  self.assertFalse((self.root/'.factory').exists())
 def test_wrong_repository_blocks_before_content_fetch(self):
  with patch('bootstrap_update.remote',side_effect=self.responses(repository_id=9)) as api:
   with self.assertRaises(ValueError):prepare(self.root)
  self.assertEqual(api.call_count,1);self.assertFalse((self.root/'.factory').exists())
 def test_external_bootstrap_symlink_is_rejected(self):
  outside=self.root.parent/(self.root.name+'-outside');outside.mkdir();self.addCleanup(outside.rmdir)
  (self.root/'.factory').symlink_to(outside,target_is_directory=True)
  with patch('bootstrap_update.remote',side_effect=self.responses()):
   with self.assertRaises(ValueError):prepare(self.root)
  self.assertFalse(list(outside.iterdir()))

class StockLibraryTests(unittest.TestCase):
 def test_all_stock_formats_have_real_reference_files_in_the_package(self):
  library=json.loads((ROOT/'config/reference-library.json').read_text());defaults=json.loads((ROOT/'config/design-defaults.json').read_text())
  manifest=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text())
  for item in defaults['formats']:
   self.assertTrue(library['formats'][item['code']]['references']);self.assertFalse(library['formats'][item['code']]['missing_sources'])
  for name,digest in library['files'].items():
   self.assertTrue(name.startswith('examples/reference-library/'));self.assertTrue(allowed(name))
   self.assertEqual(manifest['files'][name],digest)
   self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)
 def test_private_stores_and_work_manifests_remain_forbidden(self):
  for name in ('context/clients/a/memory.sqlite3','jobs/a/job.yaml','config/api.local.json','@surface/CHAVES DAS INTEGRAÇÕES.txt'):
   with self.assertRaises(ValueError):validate_manifest({'package':'claude-video-factory','version':'2','files':{name:'a'*64}})

if __name__=='__main__':unittest.main()
