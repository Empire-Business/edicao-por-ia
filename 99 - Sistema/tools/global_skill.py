#!/usr/bin/env python3
"""Install the small "cortez" entry skill for the user's Claude and register this work folder.

The entry skill lives in adapters/skill-global/cortez and is copied to ~/.claude/skills/cortez.
The folder registry is ~/.config/cortez/config.json. This is additive and idempotent: it never
touches videos, jobs, memory, keys or settings, never overwrites a "cortez" skill that it did not
install, and a failure here never blocks setup or an update.
Set CORTEZ_SKILL_GLOBAL=0 to skip it.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from project_layout import engine_root, surface_root

ORIGIN = 'Empire-Business/edicao-por-ia'
MARKER = '.cortez-skill.json'
FILES = ('SKILL.md', 'cortez_pasta.py')


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _helper(source: Path):
    spec = importlib.util.spec_from_file_location('cortez_pasta_entry', source / 'cortez_pasta.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install(root, apply: bool = False, home=None) -> dict:
    engine = engine_root(root)
    surface = surface_root(engine)
    home = Path(home or Path.home())
    source = engine / 'adapters' / 'skill-global' / 'cortez'
    version = (engine / 'VERSION').read_text(encoding='utf-8').strip() if (engine / 'VERSION').is_file() else None
    result = {'ok': True, 'applied': False, 'skill': None, 'folder': None}
    if os.environ.get('CORTEZ_SKILL_GLOBAL') == '0':
        result['skill'] = result['folder'] = 'disabled'
        return result
    if not all((source / name).is_file() for name in FILES):
        result['skill'] = 'source_missing'
        return result

    claude = home / '.claude'
    target = claude / 'skills' / 'cortez'
    if not claude.is_dir():
        result['skill'] = 'claude_not_found'
    elif target.exists() and not (target / MARKER).is_file():
        result['skill'] = 'conflict_foreign_skill_kept'
        result['skill_path'] = str(target)
    else:
        changed = [name for name in FILES if not (target / name).is_file() or _sha(target / name) != _sha(source / name)]
        result['skill_path'] = str(target)
        result['skill'] = ('updated' if changed else 'already_current') if apply else ('would_update' if changed else 'already_current')
        if apply and changed:
            target.mkdir(parents=True, exist_ok=True)
            for name in changed:
                temporary = target / (name + '.tmp')
                shutil.copyfile(source / name, temporary)
                os.replace(temporary, target / name)
        if apply:
            marker = {'origin': ORIGIN, 'version': version, 'installed_from': str(surface),
                      'at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
            previous = json.loads((target / MARKER).read_text(encoding='utf-8')) if (target / MARKER).is_file() else {}
            if changed or previous.get('version') != version:
                (target / MARKER).write_text(json.dumps(marker, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            result['applied'] = True

    helper = _helper(source)
    if not helper.e_pasta_do_cortez(surface):
        result['folder'] = 'not_a_cortez_workspace'
    elif apply:
        registered = helper.registrar(surface, home, version)
        result['folder'] = 'registered' if registered['ok'] else 'not_registered'
        if not registered['ok']:
            result['folder_reason'] = registered.get('motivo')
    else:
        result['folder'] = 'would_register'
    result['folder_path'] = str(surface)
    return result


def safe_install(root, apply: bool = True, home=None) -> dict:
    """Best-effort wrapper for setup/update: report problems, never raise."""
    try:
        return install(root, apply, home)
    except Exception as exc:  # noqa: BLE001 - must never block an update
        return {'ok': False, 'applied': False, 'error': type(exc).__name__ + ': ' + str(exc)[:300]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps(install(args.root, args.apply), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
