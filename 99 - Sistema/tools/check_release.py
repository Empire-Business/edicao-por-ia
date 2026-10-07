#!/usr/bin/env python3
"""Validate a release and run tests from manifest-only code, without local private data."""
import argparse,json,subprocess,sys,tempfile,shutil,hashlib
from pathlib import Path
from update_local import locate,package_files,validate_manifest,target_path,atomic,json_write,install


def exercise_old_layout(base,package,package_engine):
    from client_memory import Memory
    from design_catalog import register_format,register_visual
    from factory_state import State
    from recover_installation import recover
    from project_layout import translate
    old=base/'legacy-flat';old.mkdir()
    for name in ('config','patterns','assets'):shutil.copytree(package_engine/name,old/name)
    memory=Memory(old);memory.init('legacy-demo','Fixture')
    fixture_format=register_format(old,'legacy-demo','Fixture',example_url='https://example.com/fixture',legacy=True)
    fixture_visual=register_visual(old,'Fixture',{'background':'#FFFFFF','text':'#111111','primary':'#336699'},
                    {'headline':'Inter','body':'Inter','labels':'monospace'})
    source=old/'sources/fixture.mp4';source.parent.mkdir();source.write_bytes(b'synthetic original media')
    state=State(old);state.intake({'id':'legacy-demo','format':fixture_format['code'],'visual_identity':fixture_visual['code'],'sources':[str(source)],'budget':{'mode':'usd','limit_usd':'1'}})
    state.authorize('legacy-demo','Synthetic fixture consent');state.reserve('legacy-demo','edit','claude','mock','standard','call','.4',native_cap=True)
    budget=state.budget('legacy-demo')
    before={p.relative_to(old).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in old.rglob('*') if p.is_file()}
    destination=base/'recovered';result=recover(old,destination,package,True)
    if result['status']!='recovered':raise ValueError('Old layout recovery failed.')
    after={p.relative_to(old).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in old.rglob('*') if p.is_file()}
    if before!=after:raise ValueError('Recovery changed an original fixture.')
    engine=destination.resolve()/'99 - Sistema'
    if State(engine).budget('legacy-demo')!=budget:raise ValueError('Recovery changed the budget ledger.')
    original_catalog=json.loads((old/'context/catalog/registry.json').read_text())
    recovered_catalog=json.loads((engine/'context/catalog/registry.json').read_text())
    for group in ('formats','visual_identities'):
        if not all(entry in recovered_catalog[group] for entry in original_catalog[group]):raise ValueError('Recovery replaced an original design definition.')
    if translate(str(source),engine)!=str(engine/'sources/fixture.mp4'):raise ValueError('Legacy media mapping failed.')
    for name,digest in before.items():
        # Config is new code; all original job/memory files must retain exact bytes.
        if name.startswith(('jobs/','context/clients/','context/visual-identities/')) and hashlib.sha256((engine/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Recovered original bytes differ: '+name)


def check(root,tests=False):
 engine,_=locate(root);manifest=validate_manifest(json.loads((engine/'PACKAGE_MANIFEST.json').read_text()))
 files=package_files(root,manifest)
 for name in files:
  if name.startswith(('context/','.factory/')) or '.sqlite' in name:raise ValueError('Private data in release: '+name)
 defaults=json.loads(files['config/design-defaults.json']);examples=json.loads(files['config/format-examples.json'])
 for item in defaults['formats']:
  if not item.get('example_url') or not examples.get(item['code']):raise ValueError('Missing stock example: '+item['code'])
  for entry in examples[item['code']]:
   if entry['path'] not in files:raise ValueError('Missing bundled image: '+entry['path'])
 library=json.loads(files['config/reference-library.json']) if 'config/reference-library.json' in files else None
 if library:
  for item in defaults['formats']:
   group=library['formats'].get(item['code'])
   if not group or not group.get('references'):raise ValueError('Missing real references for stock format: '+item['code'])
  for name,digest in library['files'].items():
   if name not in files or hashlib.sha256(files[name]).hexdigest()!=digest:raise ValueError('Stock reference missing/corrupt: '+name)
 if tests:
  with tempfile.TemporaryDirectory(prefix='factory-release-') as directory:
   package=Path(directory)/'package';package_engine=package/'99 - Sistema';package_engine.mkdir(parents=True)
   for name,content in files.items():atomic(target_path(package_engine,package,name),content)
   json_write(package_engine/'PACKAGE_MANIFEST.json',manifest)
   # Actual clean installation exercises the packaged migration executor.
   clean=Path(directory)/'installation';clean_engine=clean/'99 - Sistema';clean_engine.mkdir(parents=True)
   installed=install(clean,package,True)
   exercise_old_layout(Path(directory),package,package_engine)
   if installed['status']!='installed':raise ValueError('Clean installation failed.')
   command=[sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-q']
   if subprocess.run(command,cwd=clean_engine).returncode:raise ValueError('Manifest-only regression failed.')
   for filename in ('test_motion.cjs','test_studio.cjs'):
    if subprocess.run(['node','--test','tests/'+filename],cwd=clean_engine).returncode:raise ValueError('JavaScript regression failed.')
 return {'ok':True,'version':manifest['version'],'files':len(files),'manifest_only_installation_tested':tests}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--tests',action='store_true');a=p.parse_args()
 print(json.dumps(check(a.root,a.tests),ensure_ascii=False))
