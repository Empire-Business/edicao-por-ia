"""Format/visual separation, mandatory selections, stable codes and update-safe data."""
import json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from client_memory import Memory
from design_catalog import register_format,register_visual,select_pair,visual_identity,update_visual,initialize_defaults,catalogue
from format_catalog import create,refresh
from factory_state import State
from factory_common import FactoryError,sha
from resolve_client_context import resolve,check
from edition_codes import code_for
from output_naming import output_filename,next_version

class DesignTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  for name in ('config','patterns','assets'):shutil.copytree(ROOT/name,self.root/name,ignore=shutil.ignore_patterns('*.local.json','.env*'))
  self.memory=Memory(self.root);self.memory.init('simple','Simple')
  register_format(self.root,'simple','Simple',example_url='https://example.com/video',legacy=True)
  self.a=register_visual(self.root,'A',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},{'headline':'A font','body':'A font','labels':'monospace'})['code']
  self.b=register_visual(self.root,'B',{'background':'#111111','text':'#FFFFFF','primary':'#FF9900'},{'headline':'B font','body':'B font','labels':'monospace'})['code']
  self.media=self.root/'source.mp4';self.media.write_bytes(b'fixture');self.state=State(self.root)
 def request(self,**kwargs):return {'format':'FP01','visual_identity':self.a,'sources':[str(self.media)],**kwargs}
 def test_one_format_has_two_independent_appearances(self):
  a=self.state.intake(self.request(id='a'));b=self.state.intake(self.request(id='b',visual_identity=self.b))
  from edit_support import read_data
  x=read_data(self.root/'jobs/a/job.effective.json');y=read_data(self.root/'jobs/b/job.effective.json')
  self.assertEqual(x['pattern'],y['pattern']);self.assertEqual(x['format_code'],y['format_code'])
  self.assertNotEqual(x['design']['palette'],y['design']['palette']);self.assertNotEqual(x['design']['typography'],y['design']['typography'])
 def test_missing_identity_blocks_before_a_job_is_created(self):
  request=self.request();request.pop('visual_identity')
  with self.assertRaises(FactoryError) as e:self.state.intake(request)
  self.assertEqual(e.exception.code,'VISUAL_IDENTITY_REQUIRED');self.assertFalse((self.root/'jobs').exists())
 def test_unknown_identity_never_falls_back(self):
  with self.assertRaises(FactoryError):self.state.intake(self.request(visual_identity='ID99'))
  self.assertFalse((self.root/'jobs').exists())
 def test_legacy_brand_facts_never_leak_into_editing_context(self):
  self.memory.commit('simple',[{'kind':'fact','key':'brand.palette','value':'Old purple and OldFont','scope':'format','scope_id':'simple','basis':'user_explicit','source':'user_message','quote':'Synthetic old brand.','reason':'Fixture.'}],'oldbrand')
  self.state.intake(self.request(id='a'))
  context=(self.root/'jobs/a/job.effective.context.md').read_text()
  self.assertNotIn('OldFont',context);self.assertNotIn('Old purple',context)
 def test_visual_revision_preserves_old_file_and_invalidates_snapshot(self):
  self.state.intake(self.request(id='a'));raw=json.loads((self.root/'jobs/a/job.effective.json').read_text())
  before=(self.root/'context/visual-identities/IDP01/identity-v1.json').read_bytes()
  update_visual(self.root,'IDP01',{'palette':{'background':'#FFFFFF','text':'#111111','primary':'#AA0055'}},'User correction')
  self.assertEqual((self.root/'context/visual-identities/IDP01/identity-v1.json').read_bytes(),before)
  self.assertFalse(check(self.memory,raw)['ok'])
 def test_new_format_requires_example_before_memory_creation(self):
  with self.assertRaises(ValueError):create(self.root,'New')
  self.assertFalse((self.root/'context/clients/new').exists())
  result=create(self.root,'New',example_url='https://example.com/clip');self.assertEqual(result['code'],'FP02')
 def test_existing_format_may_remain_without_url(self):
  self.memory.init('old','Old');register_format(self.root,'old','Old',legacy=True)
  self.assertEqual(catalogue(self.root)['formats'][-1]['example_link_status'],'legacy_exempt')
 def test_codes_and_budget_survive_assignment_and_repeated_access(self):
  self.state.intake(self.request(id='a',budget={'mode':'usd','limit_usd':'1'}));self.state.authorize('a','Fixture consent')
  self.state.reserve('a','edit','claude','mock','standard','call','.3',native_cap=True)
  before=self.state.budget('a');code=self.state.job('a')['edition_code'];self.assertEqual(code_for(self.root,'a'),code)
  self.state.assign_design(code,'FP01','IDP02','Explicit selection')
  self.assertEqual(self.state.budget('a'),before);self.assertEqual(self.state.resume(code)['edition_code'],code)
 def test_initialize_defaults_preserves_custom_identity_and_allocates_collisions(self):
  old=visual_identity(self.root,self.a);initialize_defaults(self.root)
  self.assertEqual(visual_identity(self.root,self.a),old)
  self.assertGreater(len(catalogue(self.root)['visual_identities']),2)
 def test_legacy_custom_store_is_projected_without_changing_original_bytes(self):
  from design_catalog import import_legacy_formats
  old=Memory(self.root);old.init('custom-legacy','Private old name')
  old.commit('custom-legacy',[{'kind':'preference','key':'motion.intensity','setting':'motion.intensity','value':'restrained','scope':'format','scope_id':'custom-legacy','basis':'user_explicit','source':'user_message','quote':'Keep movement discreet.','reason':'Fixture.'}],'fixture')
  before=old.path('custom-legacy').read_bytes();receipt=import_legacy_formats(self.root)
  self.assertTrue(receipt['imported']);self.assertEqual(old.path('custom-legacy').read_bytes(),before)
  code=receipt['imported'][0]['code'];ctx=old.context(code)
  self.assertTrue(any(r['key']=='motion.intensity' for r in ctx['active']))
 def test_guides_exist_and_explain_both_choices(self):
  result=refresh(self.root);folder=self.root/'04 - Formatos'/result['folders'][0]
  self.assertTrue((folder/'GUIA DA EDIÇÃO.html').exists())
  self.assertIn('ID visual',(folder/'GUIA DA EDIÇÃO.html').read_text())
 def test_numbered_export_names_and_versions(self):
  name=output_filename('Demo','9:16','F01',1,'preview',visual_id='ID02',edition_code='E01')
  self.assertEqual(name,'E01_demo_9x16_F01_ID02_PREVIEW_V1.mp4');(self.root/name).write_text('fixture')
  self.assertEqual(next_version(self.root,'Demo','F01','preview',visual_id='ID02',edition_code='E01'),2)

 def test_stock_example_links_add_only_missing_and_keep_custom_links(self):
  from design_catalog import complete_stock_examples,save
  initialize_defaults(self.root);data=catalogue(self.root)
  stock=[x for x in data['formats'] if x.get('uid','').startswith('factory.')]
  stock[0]['example_url']='https://example.com/user-reference'
  stock[1]['example_url']=None;stock[1]['example_link_status']='legacy_exempt'
  save(self.root,data);result=complete_stock_examples(self.root)
  updated=catalogue(self.root)
  self.assertEqual(next(x for x in updated['formats'] if x['code']==stock[0]['code'])['example_url'],'https://example.com/user-reference')
  self.assertEqual(len(result['changed']),1);self.assertEqual(result['changed'][0]['code'],stock[1]['code'])
  self.assertFalse(complete_stock_examples(self.root)['changed'])

if __name__=='__main__':unittest.main()
