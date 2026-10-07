"""GitHub authority and independent namespaces across formats, IDs, editions and revisions."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from design_catalog import register_visual,visual_identity,update_visual,publisher_can_write
from edition_codes import code_for,job_key
from output_naming import output_filename,next_version

class Authority(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.palette={'background':'#FFFFFF','text':'#111111','primary':'#336699'};self.fonts={'headline':'Test','body':'Test','labels':'Test'}
 def test_reader_can_create_idp_and_edit_only_its_local_revision(self):
  code=register_visual(self.root,'Private',self.palette,self.fonts)['code'];self.assertEqual(code,'IDP01')
  self.assertEqual(visual_identity(self.root,'idp1')['code'],code)
  self.assertEqual(update_visual(self.root,code,{'notes':'Personal'},'Explicit local request')['version'],2)
  with patch('design_catalog.publisher_can_write',return_value=False),self.assertRaises(ValueError):register_visual(self.root,'Claim',self.palette,self.fonts,official=True)
 def test_official_id_creation_and_change_require_server_authority(self):
  with patch('design_catalog.publisher_can_write',return_value=True):
   self.assertEqual(register_visual(self.root,'Official',self.palette,self.fonts,official=True)['code'],'ID01')
  before=visual_identity(self.root,'ID01')
  with patch('design_catalog.publisher_can_write',return_value=False),self.assertRaises(ValueError):update_visual(self.root,'ID01',{'notes':'Unauthorized'},'Cannot change')
  self.assertEqual(visual_identity(self.root,'ID01'),before)
 def test_private_edition_and_revision_do_not_conflict_with_historical_e(self):
  p=self.root/'.factory';p.mkdir();(p/'edition-codes.json').write_text(json.dumps({'E01':{'job':'old','name':'Old'}}))
  self.assertEqual(code_for(self.root,'old'),'E01');self.assertEqual(code_for(self.root,'new'),'EP01')
  self.assertEqual(job_key(self.root,'ep1'),'new')
  name=output_filename('Demo','9:16','FP01',1,'preview',visual_id='IDP01',edition_code='EP01')
  self.assertEqual(name,'EP01_demo_9x16_FP01_IDP01_PREVIEW_VP1.mp4');(self.root/name).write_text('fixture')
  self.assertEqual(next_version(self.root,'Demo','FP01','preview',visual_id='IDP01',edition_code='EP01'),2)
 def test_publisher_edition_requires_real_account_permission_even_with_local_marker(self):
  p=self.root/'.factory';p.mkdir();(p/'catalog-publisher.json').write_text('{"role":"publisher"}')
  with patch('design_catalog.publisher_can_write',return_value=False),self.assertRaises(ValueError):code_for(self.root,'denied')
  self.assertFalse((p/'edition-codes.json').exists())
 def test_permission_check_rejects_reader_and_wrong_repository(self):
  from types import SimpleNamespace
  for value in [{'id':1408655066,'permissions':{'push':False}},{'id':5,'permissions':{'push':True}}]:
   with patch('design_catalog.shutil.which',return_value='/fixture/gh'),patch('design_catalog.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(value))):self.assertFalse(publisher_can_write(self.root))

if __name__=='__main__':unittest.main()
