"""Filesystem/network fixtures only: no database, migrations, infrastructure or real API."""
import base64,hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import update_local as u
import reference_cache as cache

def digest(data):return hashlib.sha256(data).hexdigest()
def manifest(files,optional=None):
 return {'package':u.PACKAGE,'version':'3','release_schema':3,'minimum_python':'3.11','files':{n:digest(v) for n,v in files.items()},'file_sizes':{n:len(v) for n,v in files.items()},'optional_references':optional or {},'migrations':[]}

class LightUpdateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def write(self,name,data):
  p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p
 def test_github_download_requests_only_pinned_code_even_with_gigabytes_of_references(self):
  files={'tools/a.py':b'print("ok")\n','VERSION':b'3'};m=manifest(files,{'examples/reference-library/F01/large.mp4':'b'*64})
  self.write('config/update-source.json',json.dumps({'repository':cache.REPOSITORY,'repository_id':cache.REPOSITORY_ID}).encode());self.write('PACKAGE_MANIFEST.json',json.dumps({'files':{}}).encode())
  encoded=base64.b64encode(json.dumps(m).encode()).decode();calls=[]
  def fetch(repo,revision,name,sha,limit,expected):
   self.assertEqual(revision,'a'*40);calls.append(name);return files[name.removeprefix('99 - Sistema/')]
  with patch.object(u,'remote_json',side_effect=[{'id':cache.REPOSITORY_ID},{'sha':'a'*40},{'content':encoded}]),patch.object(u,'download_verified',side_effect=fetch):
   package=u.github_package(self.root)
  self.assertEqual(set(calls),{'99 - Sistema/tools/a.py','99 - Sistema/VERSION'});self.assertFalse(list(package.rglob('*.mp4')))
  self.assertEqual(json.loads((package/'99 - Sistema/PACKAGE_MANIFEST.json').read_text())['source_revision'],'a'*40)
 def test_schema3_preserves_previously_bundled_references_through_update_and_rollback(self):
  original=self.write('examples/reference-library/F01/original.mp4',b'original');self.write('VERSION',b'2')
  self.write('PACKAGE_MANIFEST.json',json.dumps({'package':u.PACKAGE,'version':'2','release_schema':2,'files':{'VERSION':digest(b'2'),'examples/reference-library/F01/original.mp4':digest(b'original')}}).encode())
  package=self.root/'incoming';package.mkdir();(package/'VERSION').write_bytes(b'3');(package/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest({'VERSION':b'3'})))
  result=u.install(self.root,package,True);self.assertEqual(result['status'],'installed');self.assertEqual(original.read_bytes(),b'original');u.rollback(self.root,result['receipt_id']);self.assertEqual(original.read_bytes(),b'original');self.assertEqual((self.root/'VERSION').read_bytes(),b'2')
 def test_release_budget_and_media_regressions_fail_closed(self):
  m=manifest({'tools/a.py':b'x'});m['file_sizes']['tools/a.py']=u.MAX_CODE_BYTES+1
  with self.assertRaises(ValueError):u.validate_manifest(m)
  with self.assertRaises(ValueError):u.validate_manifest(manifest({'examples/unexpected.mp4':b'x'}))
  m=manifest({'tools/a.py':b'x'});m['optional_references']={'../outside.mp4':'a'*64}
  with self.assertRaises(ValueError):u.validate_manifest(m)
 def test_corrupt_or_truncated_download_never_activates(self):
  class Response(io.BytesIO):
   status=200;headers={}
  opener=type('Opener',(),{'open':lambda self,*a,**kw:Response(b'bad')})()
  with patch.object(u.urllib.request,'build_opener',return_value=opener):
   for size,expected in [(2,None),(4,4),(3,None)]:
    with self.assertRaises(ValueError):u.download_verified(cache.REPOSITORY,'a'*40,'99 - Sistema/VERSION',digest(b'good'),size,expected)
 def test_on_demand_cache_pins_revision_verifies_hash_and_preserves_modified_original(self):
  name='examples/reference-library/F01/reference.mp4';content=b'video'
  self.write('config/reference-library.json',json.dumps({'files':{name:digest(content)},'formats':{'F01':{'references':[{'path':name,'bytes':len(content)}]}}}).encode());self.write('PACKAGE_MANIFEST.json',json.dumps({'source_revision':'b'*40}).encode())
  with patch.object(cache,'download_verified',return_value=content) as fetch:
   result=cache.ensure(self.root,[name]);self.assertEqual(result['downloaded'],[name]);self.assertEqual(fetch.call_args.args[1],'b'*40)
   cache.ensure(self.root,[name]);self.assertEqual(fetch.call_count,1)
   (self.root/name).write_bytes(b'custom')
   with self.assertRaises(ValueError):cache.ensure(self.root,[name])
   self.assertEqual((self.root/name).read_bytes(),b'custom')
 def test_reference_symlink_outside_factory_is_rejected(self):
  name='examples/reference-library/F01/reference.mp4';self.write('config/reference-library.json',json.dumps({'files':{name:digest(b'x')},'formats':{}}).encode());outside=self.write('outside',b'x');p=self.root/name;p.parent.mkdir(parents=True);p.symlink_to(outside)
  with self.assertRaises(ValueError):cache.ensure(self.root,[name])

 def test_personal_local_reference_does_not_attempt_public_download(self):
  from format_fidelity import snapshot
  name='sources/personal-reference.mp4';self.write(name,b'personal')
  self.write('patterns/personal.yaml',b'visual: {}\n')
  entry={'code':'FP01','uid':'personal.test','pattern':'personal','mechanism_details':{'mechanism':'Conversa','steps':['Montar'],'avoid':'Não herdar identidade','inputs':'Vídeo'},'reference_materials':[{'path':name,'sha256':digest(b'personal')}]}
  self.write('config/reference-library.json',json.dumps({'formats':{},'files':{}}).encode())
  with patch('reference_cache.ensure') as fetch:
   result=snapshot(self.root,entry)
  fetch.assert_not_called();self.assertEqual(result['primary_reference']['path'],name)

if __name__=='__main__':unittest.main()
