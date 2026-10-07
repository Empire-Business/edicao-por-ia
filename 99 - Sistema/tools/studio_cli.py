#!/usr/bin/env python3
"""Single entry for studio's local utilities; never dispatches remote models itself."""
import sys

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h','--help'):
        print('factory.py studio {render | plan-check | briefs | sheets | review | beats | sfx} ...')
        print('Workflow: workflows/MOTION_STUDIO.md. No automatic downloads or paid calls.');return 0
    if argv[0]=='render':
        from studio_render import main as run
        return run(argv[1:])
    if argv[0] in ('beats','sfx'):
        from studio_audio import main as run
        return run(argv)
    if argv[0] in ('plan-check','briefs','sheets','review'):
        from studio_review import main as run
        return run(argv)
    print('Unknown studio command',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
