#!/usr/bin/env python3
"""SYNTHETIC CLI protocol fixture. Not Claude, not Codex. Never makes network requests."""
import json, os, sys, time
args=sys.argv[1:]
if '--version' in args:
    print('2.1.248 (SYNTHETIC TEST FIXTURE, not a real CLI)');raise SystemExit(0)
if '--help' in args:
    print('--ignore-user-config --json --restricted --max-budget-usd (SYNTHETIC)');raise SystemExit(0)
text=sys.stdin.read()
if os.environ.get('VF_SYNTHETIC_SCENARIO')=='timeout':time.sleep(10)
if os.environ.get('VF_SYNTHETIC_SCENARIO')=='bad-json':print('synthetic incomplete response');raise SystemExit(1)
result='SYNTHETIC worker result. Prompt length: '+str(len(text))
if 'exec' in args:
    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':result}}))
    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':101,'cached_input_tokens':0,'output_tokens':23}}))
else:
    print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':result,
          'total_cost_usd':0.08,'usage':{'input_tokens':101,'output_tokens':23},
          'modelUsage':{'SYNTHETIC-reported-model':{}},'session_id':'SYNTHETIC'}))
