"""Official holes, private namespace, safe generation reuse and preserved local codes."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from client_memory import Memory
from design_catalog import catalogue,next_code,register_format,editing_format,retire_format,initialize_defaults,save
from format_catalog import create

class Namespaces(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.m=Memory(self.root)
 def publisher(self):
  gate=patch('design_catalog.publisher_can_write',return_value=True);gate.start();self.addCleanup(gate.stop)
  p=self.root/'.factory/catalog-publisher.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{"role":"publisher"}')
 def register(self,store,official=False):
  self.m.init(store,store);return register_format(self.root,store,store,example_url='https://example.com/video',official=official)
 def test_reader_creates_fp_and_cannot_claim_f(self):
  one=create(self.root,'Particular',example_url='https://example.com/video');self.assertEqual(one['code'],'FP01')
  with patch('design_catalog.publisher_can_write',return_value=False),self.assertRaises(ValueError):create(self.root,'Oficial',example_url='https://example.com/video',official=True)
  self.assertFalse(self.m.path('oficial').exists())
  self.assertEqual(self.m.name('FP01'),'Particular');self.assertEqual(editing_format(self.root,'fp1')['code'],'FP01')
 def test_allocator_fills_lowest_official_hole_without_changing_existing_codes(self):
  active=[{'code':'F01'},{'code':'F04'},{'code':'FP02'},{'code':'F10'}]
  self.assertEqual(next_code(active,'F',[{'code':'F02'}]),'F02')
  self.assertEqual(next_code(active,'FP'),'FP03');self.assertEqual(active[1]['code'],'F04')
 def test_reused_alias_has_new_uid_store_and_historical_bytes(self):
  self.publisher();old=self.register('old',True);before=self.m.path('old').read_bytes()
  retire_format(self.root,'F01','Author retirement')
  new=self.register('new',True)
  self.assertEqual(old['code'],new['code']);self.assertNotEqual(old['uid'],new['uid'])
  self.assertEqual(self.m.path('old').read_bytes(),before)
  self.assertEqual(editing_format(self.root,'F01')['memory_store'],'new')
  with self.assertRaises(ValueError):editing_format(self.root,'old')
  retire_format(self.root,'F01','Second retirement')
  archive=list((self.root/'context/catalog/retired/F01').rglob('entry.json'));self.assertEqual(len(archive),2)
 def test_new_stock_generation_can_use_retired_number_without_restoring_old(self):
  self.publisher();old=self.register('old',True);retire_format(self.root,'F01','Withdrawn')
  conf=self.root/'config';conf.mkdir()
  template={**old,'uid':'official.new-generation','memory_store':'ignored','name':'New official'}
  (conf/'design-defaults.json').write_text(json.dumps({'formats':[template],'visual_identities':[]}))
  self.assertEqual(initialize_defaults(self.root)['added'],['F01'])
  self.assertEqual(catalogue(self.root)['formats'][0]['uid'],'official.new-generation')
  self.assertEqual(len(catalogue(self.root)['retired_formats']),1)
 def test_conflicting_legacy_local_code_is_not_silently_renumbered(self):
  self.publisher();local=self.register('local',True)
  conf=self.root/'config';conf.mkdir();template={**local,'uid':'factory.other','name':'Stock'}
  (conf/'design-defaults.json').write_text(json.dumps({'formats':[template],'visual_identities':[]}))
  before=self.m.path('local').read_bytes();result=initialize_defaults(self.root)
  self.assertEqual(result['added'],[]);self.assertEqual(result['conflicts'][0]['code'],'F01')
  self.assertEqual(catalogue(self.root)['formats'][0],local);self.assertEqual(self.m.path('local').read_bytes(),before)

if __name__=='__main__':unittest.main()
