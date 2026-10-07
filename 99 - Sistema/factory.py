#!/usr/bin/env python3
"""Single local entry point. Ask the agent to operate it; no CLI vocabulary is required of the user."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools'))
from factory_cli import main
if __name__=='__main__':raise SystemExit(main())
