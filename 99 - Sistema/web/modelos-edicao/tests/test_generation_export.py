"""A reused F alias must generate fresh media rather than reuse retired cached files."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
SITE=Path(__file__).resolve().parents[1]
location=SITE/'scripts/export_catalog.py'
spec=importlib.util.spec_from_file_location('gallery_generation_export',location)
exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
class Generations(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.engine=Path(self.tmp.name).resolve();self.site=self.engine/'web/gallery'
  for name in ['config','tools','examples/new','assets/fonts/portable','web/gallery/public/assets/videos','web/gallery/public/assets/posters']:(self.engine/name).mkdir(parents=True,exist_ok=True)
  self.source=self.engine/'examples/new/reference.mp4';self.source.write_bytes(b'new-author-selected-reference')
  self.uid='official.new-generation';ref={'path':'examples/new/reference.mp4','sha256':exporter.digest(self.source)}
  self.library={'formats':{'F02':{'uid':self.uid,'references':[ref]}}}
  documents={self.engine/'config/design-defaults.json':{'formats':[{'code':'F02','uid':self.uid}],'visual_identities':[]},self.engine/'config/reference-library.json':self.library,self.site/'publication.json':{'formats':[{'code':'F02','uid':self.uid,'asset_id':'F02-talking-head-new','name':'Talking Head','description':'New mechanism','pattern':'new-v1','mechanism_details':{'inputs':'Input','mechanism':'Mechanism','steps':['Observed scene'],'avoid':'No inheritance'}}],'excluded_codes':[],'excluded_uids':['factory.f02']},self.site/'descriptors.json':{'F02':{'category':'presenter','tags':['Presenter'],'use':'Explain with evidence'}},self.site/'vimeo.json':{}}
  for p,value in documents.items():p.write_text(json.dumps(value))
  (self.engine/'tools/format_guides.py').write_text('# fixture')
  for name in ['manrope-variable.ttf','libre-baskerville-variable.ttf','jetbrains-mono-variable.ttf','ibm-plex-mono-400-latin.woff2','inter-400-latin.woff2','inter-600-latin.woff2','inter-800-latin.woff2']:(self.engine/'assets/fonts/portable'/name).write_bytes(b'font fixture')
  self.old=self.site/'public/assets/videos/F02.mp4';self.old.write_bytes(b'retired reference')
 def test_reused_alias_does_not_reuse_existing_retired_web_video(self):
  def encode(command,**kwargs):Path(command[-1]).write_bytes(b'newly encoded fixture')
  with patch.object(exporter,'ENGINE',self.engine),patch.object(exporter,'SITE',self.site),patch.object(exporter.subprocess,'check_output',return_value=json.dumps({'format':{'duration':'185.36'}}).encode()),patch.object(exporter.subprocess,'run',side_effect=encode) as run:
   exporter.export(media=True)
  data=json.loads((self.site/'public/catalog.json').read_text())['formats'][0]
  self.assertEqual(data['video'],'assets/videos/F02-talking-head-new.mp4')
  self.assertEqual((self.site/'public'/data['video']).read_bytes(),b'newly encoded fixture')
  self.assertEqual(self.old.read_bytes(),b'retired reference');self.assertEqual(run.call_count,2)
 def test_other_generation_reference_is_rejected_before_encoding(self):
  self.library['formats']['F02']['uid']='factory.f02';(self.engine/'config/reference-library.json').write_text(json.dumps(self.library))
  with patch.object(exporter,'ENGINE',self.engine),patch.object(exporter,'SITE',self.site),patch.object(exporter.subprocess,'run') as run:
   with self.assertRaisesRegex(ValueError,'geração'):exporter.export(media=True)
   run.assert_not_called()
if __name__=='__main__':unittest.main()
