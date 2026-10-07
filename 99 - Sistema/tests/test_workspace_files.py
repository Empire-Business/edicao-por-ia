"""Portable material references, import containment and real copy/resume tests."""
import json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from workspace_files import import_file,portable,resolve_file
from project_layout import translate
from factory_state import State
from factory_common import FactoryError
from client_memory import Memory
from design_catalog import register_visual

class WorkspaceFilesTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.base=Path(self.temp.name).resolve();self.root=self.base/'Factory';self.root.mkdir()
  self.source=self.root/'video.mp4';self.source.write_bytes(b'synthetic original')
 def test_external_file_is_rejected(self):
  outside=self.base/'outside.mp4';outside.write_bytes(b'outside')
  with self.assertRaises(ValueError):resolve_file(outside,self.root)
 def test_external_symlink_is_rejected(self):
  outside=self.base/'outside.mp4';outside.write_bytes(b'outside');link=self.root/'link.mp4';link.symlink_to(outside)
  with self.assertRaises(ValueError):resolve_file(link,self.root)
 def test_import_preserves_original_and_reuses_verified_copy(self):
  outside=self.base/'outside.mp4';outside.write_bytes(b'original')
  result=import_file(outside,self.root);self.assertTrue(result['original_preserved'])
  self.assertEqual(resolve_file(result['path'],self.root).read_bytes(),b'original')
  self.assertEqual(outside.read_bytes(),b'original')
  self.assertEqual(import_file(outside,self.root)['status'],'existing')
  self.assertNotIn(str(outside),json.dumps(result))
 def test_existing_name_is_not_overwritten(self):
  outside=self.base/'video.mp4';outside.write_bytes(b'new')
  destination=self.root/'01 - Enviar vídeos/Importados/video.mp4';destination.parent.mkdir(parents=True);destination.write_bytes(b'old')
  result=import_file(outside,self.root)
  self.assertEqual(destination.read_bytes(),b'old');self.assertEqual(resolve_file(result['path'],self.root).read_bytes(),b'new')
 def test_output_escape_and_secret_import_are_rejected(self):
  outside=self.base/'outside.mp4';outside.write_bytes(b'fixture')
  with self.assertRaises(ValueError):import_file(outside,self.root,self.base/'escape.mp4')
  secret=self.base/'.env';secret.write_text('synthetic value')
  with self.assertRaises(ValueError):import_file(secret,self.root)
 def test_reference_survives_copy_and_original_removal(self):
  stored=portable({'source':str(self.source)},self.root)
  clone=self.base/'Copied and renamed folder';shutil.copytree(self.root,clone);shutil.rmtree(self.root)
  self.assertEqual(translate(stored,clone)['source'],str(clone/'video.mp4'))
  self.assertTrue(Path(translate(stored,clone)['source']).exists())
 def test_imported_legacy_reference_works_after_both_origins_disappear(self):
  outside=self.base/'old-video.mp4';outside.write_bytes(b'old original')
  result=import_file(outside,self.root)
  stored={'source':str(outside)}
  clone=self.base/'Copied';shutil.copytree(self.root,clone)
  outside.unlink();shutil.rmtree(self.root)
  resolved=translate(stored,clone)['source']
  self.assertEqual(Path(resolved).read_bytes(),b'old original')
  self.assertNotIn(str(outside),(clone/'.factory/material-map.json').read_text())
 def test_traversal_in_stored_reference_is_blocked(self):
  with self.assertRaises(ValueError):translate({'source':'workspace://../outside.mp4'},self.root)
 def test_managed_job_resumes_after_copy_with_budget_and_fingerprint(self):
  for name in ('config','patterns'):shutil.copytree(ROOT/name,self.root/name,ignore=shutil.ignore_patterns('*.local.json','.env*'))
  Memory(self.root).init('sample','Sample');register_visual(self.root,'Fixture',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'Arial','body':'Arial','labels':'monospace'})
  state=State(self.root);state.intake({'id':'sample-job','format':'sample','visual_identity':'IDP01','sources':[str(self.source)],'budget':{'mode':'usd','limit_usd':'1'}})
  state.authorize('sample-job','Synthetic authorization')
  state.reserve('sample-job','edit','claude','mock','standard','fixture','.4',native_cap=True)
  old_budget=state.budget('sample-job')
  raw=(self.root/'jobs/sample-job/job.yaml').read_text();self.assertIn('workspace://',raw);self.assertNotIn(str(self.root),raw)
  clone=self.base/'Copied Factory';shutil.copytree(self.root,clone);shutil.rmtree(self.root)
  copied=State(clone)
  self.assertEqual(copied.resume('sample-job')['input_changes'],[])
  self.assertEqual(copied.budget('sample-job'),old_budget)
  result=copied.intake({'id':'sample-job','format':'sample','visual_identity':'IDP01','sources':[str(clone/'video.mp4')],'budget':{'mode':'usd','limit_usd':'1'}})
  self.assertEqual(result['status'],'resume');self.assertEqual(copied.budget('sample-job'),old_budget)
 def test_intake_rejects_source_script_and_asset_outside_workspace(self):
  for name in ('config','patterns'):shutil.copytree(ROOT/name,self.root/name,ignore=shutil.ignore_patterns('*.local.json','.env*'))
  Memory(self.root).init('sample','Sample');register_visual(self.root,'Fixture',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'Arial','body':'Arial','labels':'monospace'});state=State(self.root)
  outside=self.base/'outside.mp4';outside.write_bytes(b'outside')
  requests=[{'sources':[str(outside)]},{'reference_scripts':[str(outside)]},{'supporting_assets':[str(outside)]}]
  for extra in requests:
   with self.subTest(extra=extra),self.assertRaises(FactoryError) as caught:
    state.intake({'format':'sample','visual_identity':'IDP01','sources':[str(self.source)],**extra})
   self.assertEqual(caught.exception.code,'EXTERNAL_ASSET')

if __name__=='__main__':unittest.main()
