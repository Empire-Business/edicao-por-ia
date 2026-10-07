#!/usr/bin/env python3
"""Report local motion prerequisites. Does not install or contact external services."""
import importlib.util,json,shutil,subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[1]
report={'python_playwright':bool(importlib.util.find_spec('playwright')),
'pillow':bool(importlib.util.find_spec('PIL')),
'commands':{x:shutil.which(x) for x in ['ffmpeg','ffprobe','node','chromium','google-chrome']},
'remotion_installed':(r/'motion/remotion/node_modules/remotion/package.json').exists(),
'note':'An installed browser is also required; no install/download has been performed.'}
if report['python_playwright']:
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:report['playwright_browser_exists']=Path(p.chromium.executable_path).exists()
print(json.dumps(report,indent=2))
