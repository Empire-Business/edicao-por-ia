#!/usr/bin/env python3
"""Recover flat, current or mixed installations into a NEW verified folder.

No in-place merge, no deletion of the source, no Git operations, no credential output.
Only standard-library dependencies; run from a newly downloaded release.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, sqlite3, subprocess, sys, uuid
from pathlib import Path
from update_local import locate, validate_manifest, package_files, target_path, atomic, json_write, busy, sha, record_base

SYSTEM = '99 - Sistema'
SKIP = {'.git', '.venv', 'node_modules', '__pycache__', '.DS_Store', '.githooks'}
DATA = {'jobs', 'context', 'sources', 'assets', 'patterns', 'motion', 'studio', 'visual',
        'output', 'arquivo', 'prototipos', 'interface-lab', 'tutorial-omnx-sell', '.factory'}
SURFACE_DATA = {'01 - Enviar vídeos', '02 - Ver vídeos', '04 - Formatos', '05 - IDs Visuais',
                '.agents', '.claude', '.codex'}
ALIASES = {'entrada': '01 - Enviar vídeos', 'saida': '02 - Ver vídeos'}


def inventory(old, manifest):
    """Copy all non-runtime files. Code/unknown files become evidence, not active code."""
    old = Path(old).resolve(); engine = old / SYSTEM if (old / SYSTEM).is_dir() else old
    code = set(manifest['files']); found = []; blockers = []; aliases = []
    roots = [(engine, True)] + ([(old, False)] if engine != old else [])
    def walk(path, relative, logical, engine_view):
        if path.name in SKIP or path.name.startswith('.venv-'): return
        if path.is_symlink():
            resolved = path.resolve()
            if not resolved.is_relative_to(old):
                blockers.append(relative); return
            # Recognized legacy aliases already have an authoritative physical source.
            if path.is_dir() and resolved.is_relative_to(engine) and engine != old and not engine_view:
                aliases.append((path, resolved)); return
            if path.is_dir(): blockers.append(relative); return
        if path.is_dir():
            for child in sorted(path.iterdir()): walk(child, relative + '/' + child.name, logical + '/' + child.name, engine_view)
            return
        if not path.is_file(): blockers.append(relative); return
        first, _, rest = logical.partition('/')
        key = logical if engine_view else '@surface/' + logical
        if engine_view and first in ALIASES:
            destination = ALIASES[first] + ('/' + rest if rest else '')
        elif first in SURFACE_DATA or first.startswith('.env') or first == 'CHAVES DAS INTEGRAÇÕES.txt':
            destination = logical
        elif engine_view and first in DATA and key not in code:
            # Migration metadata is evidence; rebuilt runtime path map lives separately.
            destination = SYSTEM + '/' + logical
            if logical in ('.factory/layout.json', '.factory/update.lock'):
                destination = SYSTEM + '/arquivo/recuperacao/engine/' + logical
        elif engine_view and first == 'config' and (logical.endswith('.local.json') or logical.endswith('.json') and key not in code):
            destination = SYSTEM + '/' + logical
        elif not engine_view and first not in SKIP and key not in code:
            destination = SYSTEM + '/arquivo/recuperacao/raiz/' + logical
        else:
            destination = SYSTEM + '/arquivo/recuperacao/' + ('engine/' if engine_view else 'raiz/') + logical
        # Never activate old native skills/code over the downloaded version.
        if key in code and not destination.startswith(SYSTEM + '/arquivo/'):
            destination = SYSTEM + '/arquivo/recuperacao/' + ('engine/' if engine_view else 'raiz/') + logical
        if engine_view and first in ('.agents', '.claude', '.codex') and logical in code:
            destination = SYSTEM + '/arquivo/recuperacao/engine/' + logical
        found.append({'source':path, 'relative':relative, 'destination':destination, 'bytes':path.stat().st_size})
    for base, is_engine in roots:
        for item in sorted(base.iterdir()):
            if not is_engine and item.name == SYSTEM: continue
            walk(item, (SYSTEM + '/' if base != old else '') + item.name, item.name, is_engine)
    # Duplicate destinations are archived individually, never merged or overwritten.
    occupied = set(); collisions = []
    for item in found:
        dest = item['destination']
        if dest in occupied:
            collisions.append({'source':item['relative'], 'requested_destination':dest})
            item['destination'] = SYSTEM + '/arquivo/recuperacao/conflitos/' + item['relative']
            while item['destination'] in occupied: item['destination'] += '.duplicado'
        occupied.add(item['destination'])
    return found, blockers, collisions, aliases


def recover(old, destination, package, apply=False):
    old_spelling = Path(old).absolute(); old = old_spelling.resolve(); destination = Path(destination).absolute()
    if not old.is_dir(): raise ValueError('Pasta antiga não encontrada.')
    if destination.exists() or destination.is_symlink(): raise ValueError('Escolha uma pasta nova que ainda não exista; nenhuma pasta existente será substituída.')
    if destination.resolve().is_relative_to(old) or old.is_relative_to(destination.resolve()): raise ValueError('A pasta nova precisa ficar separada da pasta antiga.')
    source_engine, _ = locate(package)
    manifest = validate_manifest(json.loads((source_engine / 'PACKAGE_MANIFEST.json').read_text()))
    files = package_files(package, manifest)
    for root in (old, old / SYSTEM):
        if busy(root) or (root / '.factory/update.lock').exists(): raise ValueError('Há uma edição ou atualização em execução. Encerre ou recupere a operação antes de copiar.')
    entries, blockers, collisions, aliases = inventory(old, manifest)
    required = sum(x['bytes'] for x in entries) + sum(len(b) for b in files.values())
    parent = destination.parent
    if not parent.is_dir(): raise ValueError('A pasta que receberá a nova instalação não existe.')
    if shutil.disk_usage(parent).free < required + 64 * 1024 * 1024: raise ValueError('Falta espaço para copiar os dados preservando a pasta antiga.')
    result = {'ok': not blockers, 'status':'blocked_links' if blockers else 'preview', 'version':manifest['version'],
              'files_to_preserve':len(entries), 'bytes_to_copy':required, 'collisions':collisions,
              'links_requiring_review':blockers, 'old_folder_untouched':True, 'destination':str(destination)}
    if not apply or blockers: return result
    identifier = 'recovery-' + uuid.uuid4().hex[:12]
    stage = parent / ('.' + identifier); stage.mkdir()
    engine = stage / SYSTEM; engine.mkdir()
    copied = []; mapping = {}; preserved_keys = []
    try:
        for name, content in files.items(): atomic(target_path(engine, stage, name), content)
        json_write(engine / 'PACKAGE_MANIFEST.json', manifest)
        for item in entries:
            target = stage / item['destination']
            # Native files present in the new code also have an evidence copy.
            if target.exists():
                item['destination'] = SYSTEM + '/arquivo/recuperacao/conflitos/' + item['relative']
                target = stage / item['destination']
                if target.exists(): raise ValueError('Conflito entre cópias preservadas; operação cancelada.')
                result['collisions'].append({'source':item['relative'], 'requested_destination':str(target.relative_to(stage))})
            target.parent.mkdir(parents=True, exist_ok=True)
            # Credentials travel opaquely. Never parse, hash or print their values.
            secret = item['source'].name.startswith('.env') or item['source'].name == 'CHAVES DAS INTEGRAÇÕES.txt' or '.local.' in item['source'].name or item['source'].suffix.lower() in ('.key','.pem','.p12','.pfx') or item['destination'].startswith(('.claude/','.codex/'))
            before = None if secret else sha(item['source'])
            shutil.copy2(item['source'], target, follow_symlinks=True)
            if secret:
                target.chmod(0o600); preserved_keys.append(item['destination'])
            elif sha(target) != before or sha(item['source']) != before:
                raise ValueError('Um arquivo mudou durante a cópia. Pare as edições e tente novamente; a pasta antiga ficou intacta.')
            copied.append({'source':item['relative'], 'destination':item['destination'], 'sha256':before})
            uri = 'workspace://' + item['destination']
            mapping[hashlib.sha256(str(item['source']).encode()).hexdigest()] = uri
            mapping[hashlib.sha256(str(old_spelling / item['source'].relative_to(old)).encode()).hexdigest()] = uri
            source_engine_old = old / SYSTEM if (old / SYSTEM).is_dir() else old
            if item['source'].is_relative_to(source_engine_old):
                former_uri = 'workspace://' + item['source'].relative_to(old).as_posix()
                mapping.setdefault(hashlib.sha256(former_uri.encode()).hexdigest(), uri)
            for source_parent, target_parent in zip(item['source'].parents, Path(item['destination']).parents):
                if source_parent == old or not source_parent.is_relative_to(old): break
                mapping.setdefault(hashlib.sha256(str(source_parent).encode()).hexdigest(), 'workspace://' + target_parent.as_posix())
            for alias, real in aliases:
                if item['source'].is_relative_to(real):
                    mapping[hashlib.sha256(str(alias / item['source'].relative_to(real)).encode()).hexdigest()] = uri
        map_file = engine / '.factory/material-map.json'
        previous = json.loads(map_file.read_text()) if map_file.exists() else {}
        if not (old / SYSTEM).is_dir():
            previous = {k:('workspace://' + SYSTEM + '/' + v[12:] if v.startswith('workspace://') and not v.startswith('workspace://' + SYSTEM + '/') and v[12:].partition('/')[0] in DATA else v) for k,v in previous.items()}
        previous.update(mapping); json_write(map_file, previous)
        # Seed definitions and manuals only after original data has been copied.
        process = subprocess.run([sys.executable, str(engine / 'tools/post_update.py'), '--root', str(engine)], capture_output=True, text=True, timeout=60)
        if process.returncode: raise ValueError('A preparação da pasta recuperada falhou. A pasta antiga ficou intacta; prepare Python 3.11+ e PyYAML e tente novamente.')
        record_base(stage)
        report = {**result, 'ok':True, 'status':'recovered', 'receipt_id':identifier,
                  'copied':copied, 'credentials_preserved':preserved_keys,
                  'environment_needs_setup':True, 'original_job_files_unchanged':True}
        json_write(engine / '.factory/recoveries' / identifier / 'receipt.json', report)
        # Atomic publication: the user never sees a half-built destination.
        if destination.exists(): raise ValueError('A pasta de destino apareceu durante a cópia; nenhuma pasta existente foi substituída.')
        stage.rename(destination)
        return {k:v for k,v in report.items() if k not in ('copied','credentials_preserved')}
    except BaseException:
        # Only our unpublished staging copy is removed; source/destination stay intact.
        shutil.rmtree(stage)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old', type=Path, required=True); parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parents[1]); parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        result = recover(args.old, args.destination, args.package, args.apply)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result['ok'] else 2
    except (ValueError, OSError, subprocess.SubprocessError, sqlite3.Error) as exc:
        print(json.dumps({'ok':False, 'status':'failed', 'message':str(exc), 'old_folder_untouched':True}, ensure_ascii=False)); return 2

if __name__ == '__main__': raise SystemExit(main())
