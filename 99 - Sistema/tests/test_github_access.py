"""Public installation needs no account; explicit authenticated operations stay protected."""
import io
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from github_access import verify

class Login(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def test_missing_cli_or_failed_login_cannot_approve_setup(self):
  with patch('github_access.shutil.which',return_value=None),self.assertRaises(ValueError):verify(self.root)
  with patch('github_access.shutil.which',return_value='/fixture/gh'),patch('github_access.subprocess.run',return_value=SimpleNamespace(returncode=1,stdout='')),self.assertRaises(ValueError):verify(self.root)
  self.assertFalse((self.root/'.factory/github-access.json').exists())
 def test_read_only_account_gets_metadata_receipt_without_maintainer_permission(self):
  outputs=[{'login':'reader-fixture','id':10},{'id':1408655066,'permissions':{'push':False}}]
  with patch('github_access.shutil.which',return_value='/fixture/gh'),patch('github_access.subprocess.run',side_effect=[SimpleNamespace(returncode=0,stdout=json.dumps(x)) for x in outputs]):result=verify(self.root)
  self.assertTrue(result['authenticated']);self.assertFalse(result['maintainer_write'])
  saved=json.loads((self.root/'.factory/github-access.json').read_text());self.assertNotIn('token',saved);self.assertFalse(saved['tokens_stored_in_factory'])
 def test_wrong_repository_is_rejected(self):
  outputs=[{'login':'reader-fixture','id':10},{'id':7,'permissions':{'push':True}}]
  with patch('github_access.shutil.which',return_value='/fixture/gh'),patch('github_access.subprocess.run',side_effect=[SimpleNamespace(returncode=0,stdout=json.dumps(x)) for x in outputs]),self.assertRaises(ValueError):verify(self.root)
 def test_setup_stops_before_changes_when_login_is_not_verified(self):
  from factory_setup import setup
  from factory_common import FactoryError
  (self.root/'config').mkdir();(self.root/'config/github-access.json').write_text('{"require_authenticated_guided_setup":true}')
  with patch('github_access.verify',side_effect=ValueError('Login pending')),self.assertRaises(FactoryError) as error:setup(self.root,apply=True)
  self.assertEqual(error.exception.code,'GITHUB_AUTH_REQUIRED');self.assertFalse((self.root/'.claude').exists())
 def test_public_setup_does_not_require_github_account(self):
  from factory_setup import setup
  policy=json.loads((ROOT/'config/github-access.json').read_text())
  self.assertFalse(policy['require_authenticated_guided_setup'])
  (self.root/'config').mkdir();(self.root/'config/github-access.json').write_text(json.dumps(policy))
  # Stop before configuration/data application: this test never prepares a database.
  with patch('github_access.verify') as auth,patch('factory_setup.desired_setup',side_effect=RuntimeError('reached-local-setup')):
   with self.assertRaisesRegex(RuntimeError,'reached-local-setup'):setup(self.root,apply=True)
   auth.assert_not_called()
 def test_official_write_still_requires_authenticated_permission(self):
  from design_catalog import require_publisher
  with patch('design_catalog.shutil.which',return_value=None),self.assertRaises(ValueError):require_publisher(self.root)
  reader=SimpleNamespace(returncode=0,stdout=json.dumps({'id':1408655066,'permissions':{'push':False}}))
  with patch('design_catalog.shutil.which',return_value='/fixture/gh'),patch('design_catalog.subprocess.run',return_value=reader),self.assertRaises(ValueError):require_publisher(self.root)
 def test_public_reads_work_with_missing_or_logged_out_cli(self):
  import update_local,bootstrap_update
  for module,read in ((update_local,update_local.remote_json),(bootstrap_update,bootstrap_update.remote)):
   for executable in (None,'/fixture/gh'):
    with self.subTest(module=module.__name__,cli=executable),patch.object(module.shutil,'which',return_value=executable),patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='',stderr='To get started with GitHub CLI, please run: gh auth login')),patch.object(module.urllib.request,'urlopen',return_value=io.BytesIO(b'{"id":1408655066}')) as network:
     self.assertEqual(read('Empire-Business/edicao-por-ia','')['id'],1408655066)
     request=network.call_args.args[0]
     self.assertEqual(request.full_url,'https://api.github.com/repos/Empire-Business/edicao-por-ia')
     self.assertIsNone(request.get_header('Authorization'))

 def test_public_reads_do_not_retry_rate_limits_or_service_errors(self):
  import update_local,bootstrap_update
  for module,read in ((update_local,update_local.remote_json),(bootstrap_update,bootstrap_update.remote)):
   for error in ('HTTP 403: API rate limit exceeded','HTTP 429: Too Many Requests','HTTP 500: Internal Server Error','HTTP 401: Bad credentials'):
    with self.subTest(module=module.__name__,error=error),patch.object(module.shutil,'which',return_value='/fixture/gh'),patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='',stderr=error)),patch.object(module.urllib.request,'urlopen') as network:
     with self.assertRaisesRegex(ValueError,'Consulta ao GitHub falhou'):read('Empire-Business/edicao-por-ia','')
     network.assert_not_called()

if __name__=='__main__':unittest.main()
