#!/usr/bin/env python3
"""Build an engine + reviewed stock-reference release; exclude mutable/user material and credentials."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from update_local import allowed,PACKAGE,sha
from project_layout import engine_root,surface_root


def build(root):
 root=engine_root(root);surface=surface_root(root);files={}
 from format_fidelity import validate_locks
 validate_locks(root)
 tracked=set(subprocess.run(['git','ls-files'],cwd=surface,capture_output=True,text=True).stdout.splitlines())
 defaults=json.loads((root/'config/design-defaults.json').read_text()) if (root/'config/design-defaults.json').exists() else {'formats':[]}
 stock_patterns={f"patterns/{x['pattern']}.yaml" for x in defaults['formats']}
 directories=('tools','method','workflows','patterns','motion','studio','adapters','examples','visual','assets','config','memory','tests')
 excluded={'node_modules','.venv','__pycache__','.git','.factory','projetos','rendered','results','.DS_Store'}
 for directory in directories:
  base=root/directory
  if not base.exists():continue
  for p in base.rglob('*'):
   if not p.is_file() or p.is_symlink() or any(x in excluded for x in p.relative_to(root).parts):continue
   name=p.relative_to(root).as_posix()
   if name.startswith('examples/reference-library/'):continue
   if name.startswith('patterns/') and name not in stock_patterns and str(p.relative_to(surface)) not in tracked:continue
   if not allowed(name) or p.suffix in ('.pyc','.mp4','.wav','.mp3','.mov','.zip'):continue
   files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
 for p in root.iterdir():
  if not p.is_file() or p.is_symlink() or p.name=='PACKAGE_MANIFEST.json' or not allowed(p.name):continue
  files[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 from update_local import JOB_FILES,SURFACE_FILES
 for name in JOB_FILES:
  p=root/name
  if p.is_file():files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
 for name in SURFACE_FILES:
  p=surface/name
  if p.is_file() and not p.is_symlink():files['@surface/'+name]=hashlib.sha256(p.read_bytes()).hexdigest()
 # Native skills/role prompts are code; user settings/auth never enter a release.
 for directory in ('.agents/skills','.claude/skills','.claude/agents','.codex/agents'):
  base=surface/directory
  if base.exists():
   for p in base.rglob('*'):
    if p.is_file() and not p.is_symlink() and p.suffix in ('.md','.toml','.json'):
     name=p.relative_to(surface).as_posix()
     if allowed(name):files[name]=hashlib.sha256(p.read_bytes()).hexdigest()

 # Only the author-reviewed immutable reference index may enter a release.
 reference_index=root/'config/reference-library.json'
 if reference_index.exists():
  library=json.loads(reference_index.read_text())
  for name,digest in library['files'].items():
   if not name.startswith('examples/reference-library/') or not allowed(name):raise ValueError('Invalid reference index path.')
   file=root/name
   if file.is_symlink() or not file.resolve().is_relative_to(root) or not file.is_file() or sha(file)!=digest:raise ValueError('Reference index mismatch: '+name)
   files[name]=digest
 manifest={'package':PACKAGE,'version':(root/'VERSION').read_text().strip(),'release_schema':2,'minimum_python':'3.11','files':dict(sorted(files.items())),
           'migrations':['initialize-design-v2','refresh-guides-v2'],'user_data_policy':'preserve','update_source':'Empire-Business/edicao-por-ia@main'}
 (root/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 return {'ok':True,'version':manifest['version'],'files':len(files),'user_data_included':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();print(json.dumps(build(a.root),ensure_ascii=False,indent=2))
