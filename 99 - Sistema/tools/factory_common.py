#!/usr/bin/env python3
"""Shared filesystem and accounting primitives. Local-only, no third-party dependency."""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import hashlib, json, os, re, tempfile
from pathlib import Path
from project_layout import translate, root_for_path
ROOT=Path(__file__).resolve().parents[1]
class FactoryError(ValueError):
    def __init__(self, code, message, next_action=None, **details):
        super().__init__(message); self.code=code; self.next_action=next_action; self.details=details
    def as_dict(self):
        return {'ok':False,'code':self.code,'message':str(self),'next_action':self.next_action,**self.details}
def fail(code,message,next_action=None,**details):raise FactoryError(code,message,next_action,**details)
def stamp():return datetime.now(timezone.utc).isoformat(timespec='microseconds')
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))
def fingerprint(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def ident(value,label='id'):
    if not isinstance(value,str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',value):
        fail('INVALID_ID',f'{label}: use um identificador curto com letras minúsculas, números, - ou _.')
    return value
def inside(root,rel):
    root=Path(root).resolve();p=root/rel
    if not p.resolve().is_relative_to(root):fail('UNSAFE_PATH','Caminho fora da pasta autorizada.')
    for parent in (p,*p.parents):
        if parent==root:break
        if parent.is_symlink():fail('SYMLINK','Atalho simbólico em caminho de escrita; operação bloqueada.')
    return p
def read_json(path):
    with Path(path).open(encoding='utf-8') as f:
        data=json.load(f,parse_constant=lambda v:fail('INVALID_NUMBER',f'Valor não finito: {v}'))
    return translate(data,root_for_path(path,ROOT))
def atomic_json(path,value):return atomic_bytes(path,(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def atomic_bytes(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as f:
        tmp=Path(f.name);f.write(data);f.flush();os.fsync(f.fileno())
    try:
        os.replace(tmp,p)
        try:p.chmod(0o600)
        except OSError:pass
    finally:tmp.unlink(missing_ok=True)
    if p.read_bytes()!=data:fail('WRITE_VERIFY_FAILED','A gravação não foi confirmada.')
    return str(p)
@contextmanager
def workspace_lock(root,name='setup'):
    p=inside(root,f'.factory/{ident(name)}.lock');p.parent.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:fail('WORKSPACE_LOCKED','Outra atualização está em andamento ou foi interrompida.','Confira o processo antes de remover o arquivo de trava.')
    try:
        os.write(fd,f'{os.getpid()} {stamp()}'.encode());os.close(fd);yield
    finally:p.unlink(missing_ok=True)
def usd_units(value):
    if isinstance(value,bool) or value is None:fail('INVALID_MONEY','Informe um valor monetário não negativo.')
    try:d=Decimal(str(value))
    except InvalidOperation:fail('INVALID_MONEY','Valor monetário inválido.')
    if not d.is_finite() or d<0 or d>Decimal('1000000'):fail('INVALID_MONEY','Valor fora dos limites seguros.')
    return int((d*1000000).to_integral_value(rounding=ROUND_CEILING))
def dollars(units):return str((Decimal(units)/Decimal(1000000)).quantize(Decimal('0.000001')))
def validate_profile(root,name):
    profiles=read_json(Path(root)/'config/execution-profiles.json')
    if name not in profiles:fail('UNKNOWN_PROFILE','Perfil desconhecido.',profiles=list(profiles))
    return profiles[name]
def safe_text(value,label,limit=2000):
    if not isinstance(value,str) or not value.strip() or len(value)>limit:fail('INVALID_TEXT',f'{label}: texto obrigatório, até {limit} caracteres.')
    if re.search(r'(?i)(-----BEGIN .*PRIVATE KEY|\bsk-(?:ant-)?[\w-]{16,}|\b(?:password|senha|api[_ -]?key|access[_ -]?token)\s*[:=]\s*\S{4,})',value):
        fail('POSSIBLE_SECRET',f'{label}: possível credencial. Não a guarde nesta fábrica.')
    return value.strip()
