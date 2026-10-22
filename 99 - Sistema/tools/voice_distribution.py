"""Bounded HTTPS downloads and regular-file extraction for pinned distributions."""
from __future__ import annotations
import hashlib
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tarfile
import time
import urllib.parse
import urllib.request
import zipfile

HOSTS = {'github.com', 'codeload.github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}

def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def checked_url(url):
    u = urllib.parse.urlsplit(url)
    if u.scheme != 'https' or u.hostname not in HOSTS or u.username or u.password or u.port not in (None, 443):
        raise ValueError('Destino de download não autorizado.')
    return url

class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, checked_url(newurl))

def download(spec, target):
    if not re.fullmatch('[0-9a-f]{64}', spec['sha256']): raise ValueError('Hash inválido.')
    expected = spec['size']
    if not isinstance(expected, int) or not 0 < expected <= 256 * 1024 * 1024: raise ValueError('Tamanho inválido.')
    target = Path(target)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), Redirect())
    count = 0; deadline = time.monotonic() + 600
    try:
        with opener.open(checked_url(spec['url']), timeout=30) as response, target.open('xb') as out:
            while chunk := response.read(1024 * 1024):
                count += len(chunk)
                if count > expected or time.monotonic() > deadline: raise ValueError('Limite de download excedido.')
                out.write(chunk)
        if count != expected or digest(target) != spec['sha256']: raise ValueError('Integridade do download não confere.')
    except BaseException:
        target.unlink(missing_ok=True)
        raise

def extract(archive, destination):
    """Fresh destination only; reject links, devices, traversal and ambiguous Windows paths."""
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=False)
    seen = set(); total = 0
    def path_for(name, size, directory):
        nonlocal total
        p = PurePosixPath(name.rstrip('/'))
        if not p.parts or p.is_absolute() or any(x in ('.', '..') or ':' in x or '\\' in x or x.endswith((' ', '.')) or re.match(r'(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', x) for x in p.parts):
            raise ValueError('Caminho inseguro no pacote.')
        key = p.as_posix().casefold()
        if key in seen: raise ValueError('Entrada duplicada no pacote.')
        seen.add(key); total += size
        if len(seen) > 20000 or size > 256*1024*1024 or total > 1024*1024*1024: raise ValueError('Pacote excedeu limites de extração.')
        target = dest.joinpath(*p.parts)
        if directory: target.mkdir(parents=True, exist_ok=True)
        else: target.parent.mkdir(parents=True, exist_ok=True)
        return target
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                mode = member.external_attr >> 16
                if stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR): raise ValueError('Links e arquivos especiais não são aceitos.')
                target = path_for(member.filename, member.file_size, member.is_dir())
                if not member.is_dir():
                    with z.open(member) as inp, target.open('xb') as out: shutil.copyfileobj(inp, out)
                    if mode & 0o111: target.chmod(0o755)
    else:
        with tarfile.open(archive, 'r:*') as tar:
            for member in tar:
                if not (member.isfile() or member.isdir()): raise ValueError('Links e arquivos especiais não são aceitos.')
                target = path_for(member.name, member.size, member.isdir())
                if member.isfile():
                    with tar.extractfile(member) as inp, target.open('xb') as out: shutil.copyfileobj(inp, out)
                    if member.mode & 0o111: target.chmod(0o755)
    return dest
