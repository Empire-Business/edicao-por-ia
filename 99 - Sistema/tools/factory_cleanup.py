"""Conservative cleanup of reproducible render chunks from delivered jobs."""
from __future__ import annotations

import re
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path


def _eligible_files(job_path: Path):
    studio = job_path / 'studio'
    if studio.is_dir() and not studio.is_symlink():
        for folder in studio.iterdir():
            if folder.is_dir() and not folder.is_symlink() and re.fullmatch(r'parts-[A-Za-z0-9_-]+', folder.name):
                for path in folder.iterdir():
                    if path.is_file() and not path.is_symlink() and re.fullmatch(r'part_\d+\.mov', path.name):
                        yield path
    m4k = job_path / 'renders' / 'm4k'
    if m4k.is_dir() and not m4k.is_symlink():
        for path in m4k.iterdir():
            if path.is_file() and not path.is_symlink() and re.fullmatch(r's\d+\.mov', path.name):
                yield path


def cleanup(root: Path, job: str | None = None, apply: bool = False, confirm: str | None = None):
    root = root.resolve()
    db_path = root / '.factory' / 'state.sqlite3'
    if not db_path.is_file():
        raise ValueError('Não há banco de trabalhos gerenciados para conferir a entrega.')
    if apply and (not job or confirm != job):
        raise ValueError('Para remover, informe --job ID --apply --confirm ID após conferir a prévia.')
    if job and (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', job)):
        raise ValueError('ID de trabalho inválido.')
    result = []
    with sqlite3.connect(f'file:{db_path}?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        jobs = db.execute('SELECT id, path FROM jobs WHERE id=?' if job else 'SELECT id, path FROM jobs ORDER BY id', (job,) if job else ()).fetchall()
        if job and not jobs:
            raise ValueError('Trabalho não encontrado no controlador.')
        for row in jobs:
            job_path = (root / row['path']).resolve()
            if job_path != root / 'jobs' / row['id'] or not job_path.is_dir() or job_path.is_symlink():
                result.append({'job': row['id'], 'eligible': False, 'reason': 'Caminho do trabalho ausente ou inesperado.'})
                continue
            chunks = sorted(_eligible_files(job_path))
            potential_bytes = sum(p.stat().st_size for p in chunks)
            stages = {r['stage']: r for r in db.execute('SELECT stage,status,evidence FROM stages WHERE job=?', (row['id'],))}
            ready = all(stages.get(s) and stages[s]['status'] == 'completed' for s in ('final', 'qa', 'delivery'))
            if not ready:
                result.append({'job': row['id'], 'eligible': False, 'potential_bytes': potential_bytes, 'reason': 'Final, QA e entrega precisam estar concluídos no controlador.'})
                continue
            final_evidence = json.loads(stages['final']['evidence'])
            final_paths = [(root / item['path']).resolve() for item in final_evidence if isinstance(item, dict) and isinstance(item.get('path'), str)]
            if not any(p.is_file() and p.stat().st_size for p in final_paths):
                result.append({'job': row['id'], 'eligible': False, 'potential_bytes': potential_bytes, 'reason': 'O arquivo final registrado não está disponível.'})
                continue
            protected = set()
            for stage in stages.values():
                for item in json.loads(stage['evidence']):
                    if isinstance(item, dict) and isinstance(item.get('path'), str):
                        protected.add((root / item['path']).resolve())
            files = [p for p in chunks if p not in protected]
            bytes_total = sum(p.stat().st_size for p in files)
            if apply:
                removed = []
                for path in files:
                    if path.is_symlink() or not path.is_file() or not path.is_relative_to(job_path):
                        raise ValueError(f'Arquivo mudou durante a limpeza: {path}')
                    size = path.stat().st_size
                    path.unlink()
                    removed.append({'path': str(path.relative_to(root)), 'bytes': size})
                receipt = job_path / 'qa' / f'cleanup-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}.json'
                receipt.parent.mkdir(exist_ok=True)
                receipt.write_text(json.dumps({'job': row['id'], 'removed': removed, 'total_bytes': sum(x['bytes'] for x in removed)}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            result.append({'job': row['id'], 'eligible': True, 'files': len(files), 'bytes': bytes_total,
                           'removed': apply, 'paths_sample': [str(p.relative_to(root)) for p in files[:10]]})
    return {'ok': True, 'mode': 'apply' if apply else 'preview',
            'eligible_bytes': sum(r.get('bytes', 0) for r in result),
            'protected_potential_bytes': sum(r.get('potential_bytes', 0) for r in result), 'jobs': result}
