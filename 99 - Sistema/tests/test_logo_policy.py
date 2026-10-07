"""Logo suppression defaults and explicit per-job opt-in, without paid calls/rendering."""
import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from client_memory import Memory
from resolve_client_context import resolve,check

class LogoPolicyTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.memory=Memory(self.root);self.memory.init('sample','Sample')
 def save(self,value):
  self.memory.commit('sample',[{'kind':'preference','key':'branding.logos_enabled','setting':'branding.logos_enabled','value':value,'scope':'format','scope_id':'sample','basis':'user_explicit','source':'user_message','quote':'Synthetic preference for a past format.','reason':'Fixture only.'}],'fixture')
 def job(self,**kwargs):return {'id':'fixture','format':'sample','pattern':'test','explicit_fields':[],**kwargs}
 def test_no_logo_is_the_default(self):
  out,_=resolve(self.memory,self.job());self.assertFalse(out['branding']['logos_enabled']);self.assertIsNone(out['branding']['logo_path'])
 def test_historical_format_logo_true_is_not_permission(self):
  self.save(True);out,_=resolve(self.memory,self.job());self.assertFalse(out['branding']['logos_enabled']);self.assertTrue(check(self.memory,out)['ok'])
 def test_template_flag_or_legacy_manifest_does_not_enable_logo(self):
  for pins in ([],None):
   job=self.job(branding={'logos_enabled':True,'logo_path':'old-logo.svg'})
   if pins is None:job.pop('explicit_fields')
   out,_=resolve(self.memory,job);self.assertFalse(out['branding']['logos_enabled']);self.assertIsNone(out['branding']['logo_path'])
 def test_current_explicit_job_request_wins_over_format_default(self):
  self.save(False)
  out,_=resolve(self.memory,self.job(branding={'logos_enabled':True},explicit_fields=['branding.logos_enabled']))
  self.assertTrue(out['branding']['logos_enabled']);self.assertTrue(check(self.memory,out)['ok'])

class ProductTemplateLogoTests(unittest.TestCase):
 def build(self,enabled):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);job=Path(temp.name)
  shutil.copytree(ROOT/'studio/product-motion/kit/src',job/'src')
  for name in ('fonts','brand','vendor','img','audio'):(job/'assets'/name).mkdir(parents=True)
  shutil.copy2(ROOT/'studio/product-motion/kit/vendor/gsap.min.js',job/'assets/vendor/gsap.min.js')
  brand=json.loads((job/'src/brand.json').read_text());brand.update(name='Synthetic Current Brand',jobId='fixture',formatId='sample',videoName='Fixture',logoEnabled=enabled)
  (job/'src/brand.json').write_text(json.dumps(brand))
  subprocess.run(['node','src/build.mjs'],cwd=job,check=True,capture_output=True,text=True)
  return job
 def test_default_build_contains_no_wordmark_and_ships_local_runtime(self):
  job=self.build(False)
  for variant in ('h','v'):
   body=(job/f'build/{variant}/compositions/s01-intro.html').read_text()
   self.assertNotIn('<div class="wordmark"',body)
   index=(job/f'build/{variant}/index.html').read_text()
   self.assertIn('src="assets/vendor/gsap.min.js"',index);self.assertNotIn('https://cdn.',index)
   self.assertTrue((job/f'build/{variant}/assets/vendor/gsap.min.js').is_file())
   self.assertFalse((job/f'build/{variant}/assets/brand').exists())
 def test_explicit_logo_flag_includes_only_current_job_wordmark(self):
  job=self.build(True)
  body=(job/'build/h/compositions/s01-intro.html').read_text()
  self.assertIn('<div class="wordmark"',body);self.assertIn('Synthetic Current Brand',body)

if __name__=='__main__':unittest.main()
