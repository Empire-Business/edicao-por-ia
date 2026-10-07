"""Transactional code updates, local customization merges, retirement and data preservation."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from update_local import install,rollback,record_base,validate_manifest

class SafeUpdateTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)
  self.old=self.base/'old';self.new=self.base/'new';self.old.mkdir();self.new.mkdir()
  for root in (self.old,self.new):(root/'tools').mkdir()
  (self.old/'tools/a.py').write_text('# line one\n# line two\n# line three\n')
  (self.new/'tools/a.py').write_text('# new first line\n# line two\n# line three\n')
  for root,version in ((self.old,'1'),(self.new,'2')):
   (root/'VERSION').write_text(version)
   files={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('tools/a.py','VERSION')}
   (root/'PACKAGE_MANIFEST.json').write_text(json.dumps({'package':'claude-video-factory','version':version,'release_schema':2,'files':files}))
  (self.old/'jobs/video').mkdir(parents=True);(self.old/'jobs/video/progress.json').write_text('{"spent":0.4}')
  (self.old/'context/clients/local').mkdir(parents=True);(self.old/'context/clients/local/memory.sqlite3').write_bytes(b'original user memory')
  (self.old/'context/catalog').mkdir();(self.old/'context/catalog/registry.json').write_text('{"custom":"preserve"}')
  self.data=[self.old/'jobs/video/progress.json',self.old/'context/clients/local/memory.sqlite3',self.old/'context/catalog/registry.json']
  self.before=[p.read_bytes() for p in self.data]
 def assert_data(self):self.assertEqual([p.read_bytes() for p in self.data],self.before)
 def test_update_and_rollback_preserve_work_memory_and_catalog(self):
  result=install(self.old,self.new,True);self.assertEqual(result['status'],'installed');self.assert_data()
  self.assertEqual((self.old/'VERSION').read_text(),'2')
  result=rollback(self.old,result['receipt_id']);self.assertEqual(result['status'],'rolled_back');self.assertEqual((self.old/'VERSION').read_text(),'1');self.assert_data()
 def test_conflicts_leave_entire_active_version_untouched(self):
  (self.old/'tools/a.py').write_text('my own code\n')
  result=install(self.old,self.new,True);self.assertEqual(result['status'],'needs_merge')
  self.assertEqual((self.old/'VERSION').read_text(),'1');self.assertEqual((self.old/'tools/a.py').read_text(),'my own code\n');self.assert_data()
 def test_nonoverlapping_local_code_is_three_way_merged(self):
  record_base(self.old);(self.old/'tools/a.py').write_text('# line one\n# line two\n# my last line\n')
  result=install(self.old,self.new,True);self.assertEqual(result['status'],'installed')
  self.assertEqual((self.old/'tools/a.py').read_text(),'# new first line\n# line two\n# my last line\n');self.assert_data()
 def test_failed_write_recovers_already_applied_files(self):
  import update_local
  original=update_local.atomic;failed=[False]
  def fail_once(path,content):
   if Path(path).resolve()==(self.old/'VERSION').resolve() and content==b'2' and not failed[0]:failed[0]=True;raise OSError('synthetic failure')
   return original(path,content)
  before=(self.old/'tools/a.py').read_bytes()
  with patch('update_local.atomic',side_effect=fail_once):
   with self.assertRaises(OSError):install(self.old,self.new,True)
  self.assertEqual((self.old/'tools/a.py').read_bytes(),before);self.assertEqual((self.old/'VERSION').read_text(),'1');self.assert_data()
 def test_private_paths_and_unknown_migrations_are_rejected(self):
  for name in ('context/clients/a/memory.sqlite3','jobs/video/job.yaml','config/key.local.json','@surface/CHAVES DAS INTEGRAÇÕES.txt','../escape.py'):
   with self.assertRaises(ValueError):validate_manifest({'package':'claude-video-factory','version':'2','files':{name:'a'*64}})
  with self.assertRaises(ValueError):validate_manifest({'package':'claude-video-factory','version':'2','files':{},'migrations':['unknown-destructive-step']})
 def test_obsolete_pristine_code_retired_but_unknown_files_preserved(self):
  (self.old/'tools/old.py').write_text('old')
  manifest=json.loads((self.old/'PACKAGE_MANIFEST.json').read_text());manifest['files']['tools/old.py']=hashlib.sha256(b'old').hexdigest();(self.old/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
  (self.old/'tools/user.py').write_text('my custom unknown file')
  result=install(self.old,self.new,True);self.assertFalse((self.old/'tools/old.py').exists());self.assertTrue((self.old/'tools/user.py').exists());self.assert_data()
  rollback(self.old,result['receipt_id']);self.assertEqual((self.old/'tools/old.py').read_text(),'old')
 def test_real_budget_ledger_is_not_reset(self):
  from factory_state import State
  from client_memory import Memory
  from design_catalog import register_visual
  import shutil
  for name in ('config','patterns'):shutil.copytree(ROOT/name,self.old/name,ignore=shutil.ignore_patterns('*.local.json','.env*'))
  Memory(self.old).init('sample','Sample')
  (self.old/'context/catalog/registry.json').write_text('{"version":2,"formats":[],"visual_identities":[],"custom":"preserve"}')
  register_visual(self.old,'Fixture',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'Arial','body':'Arial','labels':'monospace'})
  media=self.old/'source.mp4';media.write_bytes(b'fixture')
  state=State(self.old);state.intake({'id':'job','format':'sample','visual_identity':'IDP01','sources':[str(media)],'budget':{'mode':'usd','limit_usd':'1'}})
  state.authorize('job','Synthetic consent');state.reserve('job','edit','claude','mock','standard','call','.4',native_cap=True)
  before=state.budget('job')
  install(self.old,self.new,True)
  self.assertEqual(State(self.old).budget('job'),before)
 def test_corrupt_release_never_changes_local_files(self):
  (self.new/'tools/a.py').write_text('corrupt')
  with self.assertRaises(ValueError):install(self.old,self.new,True)
  self.assertEqual((self.old/'VERSION').read_text(),'1');self.assert_data()

 def test_human_output_does_not_claim_conflict_was_success(self):
  from update_local import human_message
  result=human_message({'ok':False,'status':'needs_merge','receipt_id':'update-123456789abc'})
  self.assertIn('NÃO foi aplicada',result);self.assertIn('ATUALIZACAO.md',result);self.assertIn('update-123456789abc',result)
 def test_remote_check_detects_real_local_drift_even_when_manifests_match(self):
  from update_local import github_package
  import base64
  (self.old/'config').mkdir();(self.old/'config/update-source.json').write_text('{"repository":"Empire-Business/edicao-por-ia","branch":"main"}')
  data=json.loads((self.old/'PACKAGE_MANIFEST.json').read_text());encoded=base64.b64encode(json.dumps(data).encode()).decode()
  (self.old/'tools/a.py').write_text('local customization')
  with patch('update_local.remote_json',side_effect=[{'id':1},{'sha':'a'*40},{'content':encoded}]):
   result=github_package(self.old,True)
  self.assertEqual(result['status'],'up_to_date');self.assertIn('tools/a.py',result['local_changes'])

 def test_old_update_shortcuts_are_retired_with_backup_and_never_reinstalled(self):
  manifest=json.loads((self.old/'PACKAGE_MANIFEST.json').read_text())
  names=['Atualizar Fábrica.'+ext for ext in ('cmd','command','sh')]
  for name in names:
   (self.old/name).write_bytes(b'old launcher')
   manifest['files']['@surface/'+name]=hashlib.sha256(b'old launcher').hexdigest()
  (self.old/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
  result=install(self.old,self.new,True)
  self.assertEqual(result['status'],'installed');self.assert_data()
  self.assertTrue(all(not (self.old/name).exists() for name in names))
  rollback(self.old,result['receipt_id'])
  self.assertTrue(all((self.old/name).read_bytes()==b'old launcher' for name in names));self.assert_data()
 def test_new_packages_cannot_publish_retired_root_launchers(self):
  from update_local import RETIRED_SURFACE_FILES
  for name in RETIRED_SURFACE_FILES:
   with self.assertRaises(ValueError):validate_manifest({'package':'claude-video-factory','version':'2','files':{name:'a'*64}})
 def test_customized_old_launcher_is_preserved_instead_of_deleted(self):
  name='@surface/Atualizar Fábrica.cmd';manifest=json.loads((self.old/'PACKAGE_MANIFEST.json').read_text())
  manifest['files'][name]=hashlib.sha256(b'old launcher').hexdigest()
  (self.old/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest))
  (self.old/'Atualizar Fábrica.cmd').write_bytes(b'user customization')
  result=install(self.old,self.new,True)
  self.assertIn(name,result['preserved_local_files']);self.assertEqual((self.old/'Atualizar Fábrica.cmd').read_bytes(),b'user customization');self.assert_data()

if __name__=='__main__':unittest.main()
