"""Canonical engine and human folders; legacy reads do not change stored evidence."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

SYSTEM = '99 - Sistema'


def engine_root(root):
    root = Path(root).resolve()
    candidate = root / SYSTEM
    if candidate.is_dir() and not candidate.is_symlink() and (candidate/'tools/factory_common.py').is_file():
        return candidate
    return root


def surface_root(root):
    root = engine_root(root)
    if root.name == SYSTEM and ((root/'.factory/layout.json').is_file() or (root.parent/'.factory-root.json').is_file()):
        return root.parent
    return root


def root_for_path(path, default):
    for parent in Path(path).resolve().parents:
        if (parent/'.factory/layout.json').is_file() or (parent/'.factory/workspace.json').is_file() or (parent/'.factory-root.json').is_file():
            return engine_root(parent)
    return engine_root(default)


def rules(root):
    root = engine_root(root)
    path = root/'.factory/layout.json'
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding='utf-8'))
    result = []
    for old, relative in data.get('legacy_paths', {}).items():
        destination = (surface_root(root)/relative).resolve()
        if not destination.is_relative_to(surface_root(root)):
            raise ValueError('Layout destination escapes project')
        result.append((old.rstrip('/'), str(destination)))
    return sorted(result, key=lambda pair: len(pair[0]), reverse=True)


def translate(value, root, reverse=False):
    mappings = rules(root)
    material_map_path=engine_root(root)/'.factory/material-map.json'
    if material_map_path.is_symlink() or not material_map_path.resolve().is_relative_to(surface_root(root)):raise ValueError('Material map cannot escape the workspace')
    material_map=json.loads(material_map_path.read_text()) if material_map_path.exists() and not reverse else {}
    if reverse:
        mappings = sorted([(new, old) for old, new in mappings], key=lambda pair:len(pair[0]), reverse=True)
    def visit(v):
        if isinstance(v, str):
            imported=material_map.get(hashlib.sha256(v.encode('utf-8')).hexdigest()) if not reverse else None
            if imported:v=imported
            if not reverse and v.startswith('workspace://'):
                from workspace_files import resolve_file
                relative=v[len('workspace://'):]
                first,separator,tail=relative.partition('/')
                # A workspace reference written before the physical engine move also relocates.
                matches=[(old,new) for old,new in mappings if Path(old).name==first]
                if matches and first!='99 - Sistema':
                    candidate=Path(matches[0][1])/tail if separator else Path(matches[0][1])
                    v=str(resolve_file(candidate,root,False))
                else:v=str(resolve_file(v,root,False))
            if not reverse:
                for old, new in mappings:
                    if new != old and (v == new or v.startswith(new+'/') or v.startswith(new+'\\')):
                        return v
            for old, new in mappings:
                if v == old or v.startswith(old+'/') or v.startswith(old+'\\'):
                    return new+v[len(old):].replace('\\','/')
            return v
        if isinstance(v, list):return [visit(x) for x in v]
        if isinstance(v, dict):return {k:visit(x) for k,x in v.items()}
        return v
    return visit(value)


def managed_path(root, relative):
    from factory_common import inside
    if relative.startswith('@surface/'):
        return inside(surface_root(root),relative[len('@surface/'):])
    base = surface_root(root) if relative=='.gitignore' or relative.startswith(('.claude/', '.codex/', '.agents/')) else engine_root(root)
    return inside(base, relative)
