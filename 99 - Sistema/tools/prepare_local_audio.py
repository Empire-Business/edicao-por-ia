#!/usr/bin/env python3
"""Preview/apply a pinned native DeepFilterNet runtime; no Python dependency changes."""
import argparse
import json
import os
import platform
from pathlib import Path
import tempfile
import time
from urllib.request import build_opener, ProxyHandler, HTTPSHandler, HTTPRedirectHandler, Request
from audio_local import ROOT, run, publish, receipt
from workspace_files import digest, resolve_file


class HTTPSRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith('https://'): raise ValueError('Redirecionamento sem HTTPS bloqueado.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def prepare(apply=False, root=ROOT):
    key = platform.system() + '-' + platform.machine()
    catalog = json.loads((Path(root) / 'config/audio-runtimes.json').read_text())
    spec = catalog['deepfilter'].get(key)
    if spec is None:
        return {'ok': False, 'status': 'runtime_not_reviewed', 'platform': key,
                'message': 'Use a limpeza básica FFmpeg ou prepare um runtime oficial revisado para esta plataforma.'}
    target = resolve_file(Path(root) / '.factory/runtimes/deepfilter/deep-filter', root, False)
    if target.exists():
        if digest(target) != spec['sha256']: raise ValueError('Runtime existente difere do revisado; nada foi sobrescrito.')
        return {'ok': True, 'status': 'already_installed', 'version': spec['version']}
    if not apply:
        return {'ok': True, 'status': 'preview', 'download': spec['url'], 'bytes': spec['size'],
                'changes': 'Somente runtime local do DeepFilterNet; nenhuma proteção do sistema é alterada.'}
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.download-', dir=target.parent) as folder:
        candidate = Path(folder) / 'deep-filter'
        opener = build_opener(ProxyHandler({}), HTTPSHandler(), HTTPSRedirect())
        size = 0; started = time.monotonic()
        with opener.open(Request(spec['url']), timeout=30) as response, candidate.open('xb') as stream:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if time.monotonic() - started > 180: raise ValueError('Download excedeu 180 segundos.')
                if size > spec['size']: raise ValueError('Download excedeu o tamanho revisado.')
                stream.write(chunk)
        if size != spec['size'] or digest(candidate) != spec['sha256']: raise ValueError('Integridade do runtime não confere.')
        if platform.system() == 'Darwin': run(['codesign', '--verify', '--verbose', candidate], 30)
        candidate.chmod(0o755)
        run([candidate, '--version'], 15)
        publish(candidate, target)
        receipt(target.with_name('install.json'), spec, root)
    return {'ok': True, 'status': 'installed', 'version': spec['version']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--apply', action='store_true'); a = p.parse_args()
    try:
        result = prepare(a.apply)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result['ok']: p.exit(2)
    except (ValueError, OSError): p.exit(2, 'Preparação local não concluída; confira rede, integridade e permissões.\n')
