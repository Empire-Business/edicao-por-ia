"""Small local helpers shared by the 1.1 editing tools; no network or model calls."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from project_layout import translate, root_for_path


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_data(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    text = p.read_text(encoding='utf-8-sig')
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        if p.suffix.lower() not in {'.yaml', '.yml'}:
            raise ValueError(f'Expected a JSON object: {p}')
        try:
            import yaml
        except ImportError as e:
            raise ValueError('YAML needs optional PyYAML. Use JSON or authorize its installation.') from e
        result = yaml.safe_load(text)
    if not isinstance(result, dict):
        raise ValueError(f'Expected an object: {p}')
    return translate(result, root_for_path(p, Path(__file__).resolve().parents[1]))


def number(value: Any, name: str, minimum: float = 0) -> float:
    if isinstance(value, bool):
        raise ValueError(f'{name} must be numeric, not boolean')
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise ValueError(f'Invalid {name}: {value}')
    return result


def same_path(a: str | Path, b: str | Path) -> bool:
    x, y = Path(a), Path(b)
    return x.resolve() == y.resolve() or (x.exists() and y.exists() and x.samefile(y))


def check_output(path: str | Path, inputs: list[str | Path] = ()) -> Path:
    p = Path(path).resolve()
    if any(same_path(p, x) for x in inputs):
        raise ValueError(f'Output aliases an input: {p}')
    if p.exists():
        raise ValueError(f'Refusing to overwrite {p}; choose a new versioned output')
    return p


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    root=root_for_path(p,Path(__file__).resolve().parents[1])
    from project_layout import surface_root
    if p.resolve().is_relative_to(surface_root(root)):
        from workspace_files import portable
        data=portable(data,root)
    content = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        f.write(content)


def merge_ranges(ranges: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for a, b in sorted(ranges):
        if b <= a:
            continue
        if out and a <= out[-1][1] + 1e-9:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def subtract_ranges(a: float, b: float, blocked: list[tuple[float, float]]) -> list[tuple[float, float]]:
    result = []
    cursor = a
    for start, end in blocked:
        if end <= cursor:
            continue
        if start >= b:
            break
        if start > cursor:
            result.append((cursor, min(start, b)))
        cursor = max(cursor, end)
        if cursor >= b:
            break
    if cursor < b:
        result.append((cursor, b))
    return result
