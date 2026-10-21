"""No real API calls or credentials. Validate upload destination and credential separation."""
import io,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from vimeo_publish import Vimeo

class VimeoBoundaryTests(unittest.TestCase):
 def test_invalid_upload_hosts_are_rejected_before_network_or_file_read(self):
  with patch('urllib.request.build_opener') as opener:
   for link in ['http://files.tus.vimeo.com/upload','https://vimeo.com.evil.test/upload','https://127.0.0.1/upload','file:///tmp/upload']:
    with self.assertRaises(ValueError):Vimeo('fixture-token').upload(link,Path('absent.mp4'))
   opener.assert_not_called()
 def test_tus_resume_sends_only_remaining_bytes_and_never_account_token(self):
  calls=[]
  class Response(io.BytesIO):
   def __init__(self,offset):super().__init__();self.headers={'Upload-Offset':str(offset)}
  class Opener:
   def open(self,req,**kwargs):
    calls.append(req)
    return Response(2 if req.method=='HEAD' else 5)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'fixture.mp4';path.write_bytes(b'12345')
   with patch('urllib.request.build_opener',return_value=Opener()):self.assertEqual(Vimeo('fixture-token').upload('https://files.tus.vimeo.com/upload',path),5)
  self.assertEqual(calls[1].data,b'345')
  for req in calls:self.assertNotIn('Authorization',req.headers);self.assertNotIn('fixture-token',str(req.headers))
 def test_api_refuses_cross_host_paging_inputs(self):
  with patch('urllib.request.build_opener') as opener:
   for path in ['https://evil.test/me','//evil.test/me']:
    with self.assertRaises(ValueError):Vimeo('fixture-token').api(path)
   opener.assert_not_called()

if __name__=='__main__':unittest.main()
