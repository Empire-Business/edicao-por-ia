"""Stable human codes E01/E02 for editing jobs; never renumber or reset spend."""
import re,json
from pathlib import Path
from factory_common import inside,atomic_json,workspace_lock
from project_layout import engine_root


def data(root):
 p=inside(engine_root(root),'.factory/edition-codes.json')
 return json.loads(p.read_text()) if p.exists() else {}


def code_for(root,job,name=None):
 root=engine_root(root)
 for code,item in data(root).items():
  if item['job']==job:return code
 with workspace_lock(root,'edition-codes'):
  records=data(root)
  for code,item in records.items():
   if item['job']==job:return code
  marker=inside(root,'.factory/catalog-publisher.json')
  official=marker.is_file() and json.loads(marker.read_text()).get('role')=='publisher'
  if official:
   from design_catalog import require_publisher
   require_publisher(root)
  prefix='E' if official else 'EP'
  number=max([int(match.group(1)) for k in records if (match:=re.fullmatch(re.escape(prefix)+r'(\d+)',k))],default=0)+1;code=f'{prefix}{number:02d}'
  records[code]={'job':job,'name':name or job};atomic_json(inside(root,'.factory/edition-codes.json'),records)
  return code


def job_key(root,value):
 if isinstance(value,str) and (match:=re.fullmatch(r'(EP|E)(\d+)',value,re.I)):
  code=match.group(1).upper()+f'{int(match.group(2)):02d}'
  if code not in data(root):raise ValueError('Código de edição desconhecido.')
  return data(root)[code]['job']
 return value
