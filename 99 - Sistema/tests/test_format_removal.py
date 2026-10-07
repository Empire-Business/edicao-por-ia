"""Removing a format preserves its generation and prevents default resurrection."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from client_memory import Memory
from design_catalog import catalogue,save,register_format,editing_format,initialize_defaults,next_code
from format_catalog import refresh,remove
class Removal(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.memory=Memory(self.root);self.memory.init('test-f02','Dynamic fixture')
  gate=patch('design_catalog.publisher_can_write',return_value=True);gate.start();self.addCleanup(gate.stop)
  (self.root/'.factory').mkdir(exist_ok=True);(self.root/'.factory/catalog-publisher.json').write_text('{"role":"publisher"}')
  entry={'code':'F02','name':'Dynamic fixture','memory_store':'test-f02','pattern':'fixture-v1','uid':'fixture.f02','legacy_stores':['old-dynamic'],'description':'Fixture','example_url':'https://example.com/clip','example_link_status':'provided'}
  save(self.root,{'version':2,'formats':[entry],'visual_identities':[]})
  (self.root/'patterns').mkdir();(self.root/'patterns/fixture-v1.yaml').write_text('id: fixture-v1\n')
  (self.root/'config').mkdir();(self.root/'config/design-defaults.json').write_text(json.dumps({'formats':[entry],'visual_identities':[]}))
  # Exercise catalogue deletion without needing the real documentation renderer.
  self.folder=self.root/'04 - Formatos/F02 - Dynamic fixture';self.folder.mkdir(parents=True);(self.folder/'note.txt').write_text('preserve')
 def test_removal_preserves_files_and_reserves_code(self):
  from unittest.mock import patch
  before=self.memory.path('test-f02').read_bytes()
  with patch('format_catalog.refresh',return_value={'ok':True}):r=remove(self.root,'F02','User requested')
  self.assertTrue(r['visible_folder_removed']);self.assertEqual(catalogue(self.root)['formats'],[])
  self.assertEqual(self.memory.path('test-f02').read_bytes(),before)
  self.assertEqual((self.root/r['archived_folder']/'note.txt').read_text(),'preserve')
  self.assertEqual(next_code([], 'F', catalogue(self.root)['retired_formats']),'F01')
  with self.assertRaises(ValueError):editing_format(self.root,'F02')
  with self.assertRaises(ValueError):editing_format(self.root,'old-dynamic')
 def test_default_initialization_does_not_restore_removed_entry(self):
  from unittest.mock import patch
  with patch('format_catalog.refresh',return_value={'ok':True}):remove(self.root,'F02','User requested')
  self.assertEqual(initialize_defaults(self.root)['added'],[])
  self.assertEqual(catalogue(self.root)['formats'],[])
if __name__=='__main__':unittest.main()
