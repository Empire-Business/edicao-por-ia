#!/usr/bin/env python3
"""Extract every Lucide icon body from a local lucide-react install into a JSON map {name: svg-inner}.
usage: lucide_extract.py <path/to/node_modules/lucide-react> <out.json>   (ISC license; no network)"""
import json, re, sys
from pathlib import Path
src, out = Path(sys.argv[1]) / "dist/esm/icons", Path(sys.argv[2])
icons = {}
for f in sorted(src.glob("*.js")):
    t = f.read_text()
    if "createLucideIcon(" not in t:
        continue  # alias re-export
    parts = []
    for tag, attrs in re.findall(r'\[\s*"(\w+)",\s*\{([^}]*)\}\s*\]', t):
        a = "".join(f' {k}="{v}"' for k, v in re.findall(r'(\w+):\s*"([^"]*)"', attrs) if k != "key")
        parts.append(f"<{tag}{a}/>")
    if parts:
        icons[f.stem] = "".join(parts)
out.write_text(json.dumps(icons, separators=(",", ":")))
print(len(icons), "icons ->", out)
