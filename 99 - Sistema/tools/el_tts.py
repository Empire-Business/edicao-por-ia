#!/usr/bin/env python3
"""Compatibility entrypoint for tools/narrate.py (OpenRouter narration by default, local voices as alternative).

ElevenLabs no longer narrates (owner decision, 09/11/2026); every paid call still needs --accept-paid.
"""
from narrate import main

if __name__ == '__main__': main()
