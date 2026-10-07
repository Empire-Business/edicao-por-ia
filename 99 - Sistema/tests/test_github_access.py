"""Guided setup requires a verified own-account login and never stores credentials."""
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

if __name__=='__main__':unittest.main()
