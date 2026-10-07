#!/usr/bin/env python3
"""Verify the user's own GitHub login for guided installation; never handle token values."""
import argparse,json,shutil,subprocess
from pathlib import Path
from project_layout import engine_root
from factory_common import inside,atomic_json,stamp

def verify(root):
    if not shutil.which('gh'):raise ValueError('Autentique sua conta na integração/CLI oficial do GitHub antes da preparação. Não envie tokens à conversa.')
    def get(path):
        result=subprocess.run(['gh','api',path],capture_output=True,text=True,timeout=30)
        if result.returncode:raise ValueError('Login do GitHub não confirmado. Conclua a autenticação da sua própria conta; a instalação permanece pendente.')
        return json.loads(result.stdout)
    user=get('user');repository=get('repos/Empire-Business/edicao-por-ia')
    if not user.get('login') or not isinstance(user.get('id'),int) or repository.get('id')!=1408655066:raise ValueError('Conta ou repositório não correspondem ao destino autorizado.')
    result={'ok':True,'authenticated':True,'login':user['login'],'user_id':user['id'],
            'repository':'Empire-Business/edicao-por-ia','repository_id':1408655066,
            'maintainer_write':bool((repository.get('permissions') or {}).get('push')),
            'at':stamp(),'tokens_stored_in_factory':False}
    atomic_json(inside(engine_root(root),'.factory/github-access.json'),result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    try:print(json.dumps(verify(a.root),ensure_ascii=False,indent=2))
    except (ValueError,OSError,subprocess.SubprocessError) as exc:raise SystemExit(str(exc))
