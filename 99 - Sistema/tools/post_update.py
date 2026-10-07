#!/usr/bin/env python3
"""Additive, idempotent data migration after a verified code update. Never delete user data."""
import argparse,json
from pathlib import Path
from design_catalog import initialize_defaults,import_legacy_formats,complete_stock_examples
from format_catalog import refresh
from project_layout import engine_root
from factory_common import atomic_json,inside


def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=engine_root(a.root)
 receipt=initialize_defaults(root)
 legacy=import_legacy_formats(root)
 examples=complete_stock_examples(root)
 # A new registry can coexist with the preserved legacy stores. Original databases are untouched.
 guides=refresh(root)
 result={'ok':guides['ok'],'migration':'design-v2','defaults':receipt,'legacy':legacy,'examples':examples,'guides':guides,'original_data_preserved':True}
 atomic_json(inside(root,'.factory/migrations/design-v2.json'),result)
 print(json.dumps(result,ensure_ascii=False));return 0 if result['ok'] else 2
if __name__=='__main__':raise SystemExit(main())
