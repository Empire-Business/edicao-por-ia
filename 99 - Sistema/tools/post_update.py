#!/usr/bin/env python3
"""Additive, idempotent data migration after a verified code update. Never delete user data."""
import argparse,json
from pathlib import Path
from design_catalog import initialize_defaults,import_legacy_formats,complete_stock_examples,migrate_f02_talking_head_v2
from format_catalog import refresh
from project_layout import engine_root
from factory_common import atomic_json,inside


def annotate_keys(root):
 # 2.11.0: OpenRouter = music, narration and covers; ElevenLabs = only noise. Append-only notes on the
 # EXISTING keys file (never created here, values never read out or changed). Never fails the update.
 try:
  from service_keys import annotate_services
  return annotate_services(root)
 except Exception as exc:
  return {'ok':False,'status':'skipped','reason':type(exc).__name__,'values_exposed':False}


def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=engine_root(a.root)
 receipt=initialize_defaults(root)
 legacy=import_legacy_formats(root)
 examples=complete_stock_examples(root)
 f02_recipe=migrate_f02_talking_head_v2(root)
 # A new registry can coexist with the preserved legacy stores. Original databases are untouched.
 guides=refresh(root)
 # Machine-level fix delivered by updates: entry skill + folder registry. Additive; never fails the update.
 from global_skill import safe_install
 global_skill=safe_install(root,True)
 key_notes=annotate_keys(root)
 result={'ok':guides['ok'],'migration':'design-v2','defaults':receipt,'legacy':legacy,'examples':examples,'f02_recipe':f02_recipe,'guides':guides,'global_skill':global_skill,'key_notes':key_notes,'original_data_preserved':True}
 atomic_json(inside(root,'.factory/migrations/design-v2.json'),result)
 print(json.dumps(result,ensure_ascii=False));return 0 if result['ok'] else 2
if __name__=='__main__':raise SystemExit(main())
