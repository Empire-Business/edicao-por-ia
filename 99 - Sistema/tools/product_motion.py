#!/usr/bin/env python3
"""Product-motion helper (HyperFrames HTML+GSAP, 16:9 + 9:16 proportions from one scene source).

Method: workflows/PRODUCT_MOTION.md. Kit: studio/product-motion/kit. Reference job: jobs/omnx-sell-motion.
  new     scaffold jobs/<id>/ from the kit            product_motion.py new --format X --job-id X-motion --name "X" [--repo PATH] [--fonts-from DIR]
  build   expand scenes -> <job>/build/{h,v}          product_motion.py build JOB [--scenes s01,s02] [--out build-w1]
  check   hyperframes lint+layout on both proportions  product_motion.py check JOB [--out build]
  snap    still frames at times (never uploads)        product_motion.py snap JOB --at 1,3,5 [--scene ID] [--proportion 16:9|9:16|both]
  sheet   contact sheet from a rendered mp4            product_motion.py sheet JOB [--every 3.2]
  music   loop/trim the bed to the film length         product_motion.py music JOB TOTAL_SECONDS
  render  final mp4s into <job>/renders                product_motion.py render JOB [--proportion 16:9|9:16|both] [--quality looks|delivery]
Legacy --fmt h|v|both remains accepted for snap and render.
No network except `npx hyperframes@PIN` (already cached after the first run) and no composition network dependency: GSAP ships locally with the job.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys
from pathlib import Path
from output_naming import next_version, output_filename
from client_memory import Memory
from workspace_files import resolve_file, portable
from design_catalog import select_pair,product_tokens
from edition_codes import code_for

ROOT = Path(__file__).resolve().parent.parent
KIT = ROOT / "studio" / "product-motion" / "kit"
HF = "hyperframes@0.8.92"  # pinned: the version the reference job was validated with


def node_env():
    env = dict(os.environ)
    cands = sorted(glob.glob(os.path.expanduser("~/.nvm/versions/node/v2[2-9]*/bin")), reverse=True)
    if cands:
        env["PATH"] = cands[0] + os.pathsep + env["PATH"]
    return env


def run(cmd, cwd, env=None, check=True):
    print("$", " ".join(map(str, cmd)))
    r = subprocess.run(cmd, cwd=cwd, env=env or node_env())
    if check and r.returncode:
        sys.exit(r.returncode)
    return r.returncode


def job_dir(arg):
    p = Path(arg)
    if not p.exists():
        p = ROOT / "jobs" / arg
    if not (p / "src" / "scenes.json").exists():
        sys.exit(f"not a product-motion job (no src/scenes.json): {p}")
    return p.resolve()


def cmd_new(a):
    editing,identity=select_pair(ROOT,a.format_id,a.visual_id)
    a.format_id=editing['memory_store']
    if a.repo:
        a.repo=str(resolve_file(a.repo,ROOT,False))
        if not Path(a.repo).is_dir():raise ValueError('O repositório de referência precisa estar dentro da fábrica.')
    if a.fonts_from:
        a.fonts_from=str(resolve_file(a.fonts_from,ROOT,False))
        if not Path(a.fonts_from).is_dir():raise ValueError('As fontes precisam estar dentro da fábrica.')
    job = ROOT / "jobs" / a.job_id
    if job.exists():
        sys.exit(f"job exists: {job}")
    shutil.copytree(KIT / "src", job / "src")
    for d in ("assets/fonts", "assets/brand", "assets/vendor", "assets/img", "assets/audio", "assets/refs", "qa", "edit", "renders"):
        (job / d).mkdir(parents=True, exist_ok=True)
    bj = job / "src" / "brand.json"
    template=bj.read_text()
    for token,value in (("{{BRAND_NAME}}",a.name),("{{JOB_ID}}",a.job_id),
                        ("{{FORMAT_ID}}",a.format_id),("{{VIDEO_NAME}}",a.video_name or a.job_id)):
        template=template.replace(token,json.dumps(value,ensure_ascii=False)[1:-1])
    cfg=json.loads(template)
    cfg['formatCode']=editing['code'];cfg['visualIdentity']=identity['code'];cfg['editionCode']=code_for(ROOT,a.job_id,a.video_name or a.job_id)
    cfg['colors']=product_tokens(identity)
    cfg['font']={'family':identity['typography']['headline'],'weights':[],'faces':[]}
    for face in identity.get('font_faces',[]):
        font_source=resolve_file(face['path'],ROOT)
        shutil.copy2(font_source,job/'assets/fonts'/font_source.name)
        cfg['font']['faces'].append({**face,'src':'assets/fonts/'+font_source.name})
    cfg['typography']=identity['typography']
    cfg['logoEnabled']=bool(getattr(a,'include_logo',False))
    bj.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    shutil.copy2(KIT/'vendor/gsap.min.js',job/'assets/vendor/gsap.min.js')
    if a.fonts_from:
        for f in Path(a.fonts_from).glob("*.woff2"):
            shutil.copy(f, job / "assets" / "fonts" / f.name)
    (job / "job.yaml").write_text(
        f"edition_code: {cfg['editionCode']}\nselection_version: 2\nformat_code: {editing['code']}\nvisual_identity: {identity['code']}\njob_id: {a.job_id}\nname: {json.dumps(a.video_name or a.job_id,ensure_ascii=False)}\nformat: {a.format_id}\nclient: {a.format_id}\nproject: product-motion\ntype: product-motion (no source footage)\n"
        f"engine: {HF} (HTML + GSAP, deterministic seek render)\n"
        f"explicit_fields: {json.dumps(['branding.logos_enabled'] if getattr(a,'include_logo',False) else [])}\nbranding:\n  logos_enabled: {str(bool(getattr(a,'include_logo',False))).lower()}\nsource_of_truth:\n  product_repo: {portable(a.repo,ROOT) if a.repo else 'TODO'}\n  design: TODO (path to tokens/DESIGN.md)\n  reference_screens: assets/refs/*.png\n"
        "deliverables:\n  - renders/<video-name>_<proportion>_<format>_PREVIEW_V<n>.mp4\n"
        "  - renders/<video-name>_<proportion>_<format>_V<n>.mp4\n"
        f"build: python3 tools/product_motion.py build {a.job_id}\n")
    (job / "edit" / "decision_log.md").write_text(f"# Decision log — {a.job_id}\n- (record every reversible default here)\n")
    print(f"created {job}\nnext: fill src/brand.json with the product's REAL tokens, copy fonts/refs into assets/; logos stay disabled unless explicitly requested, read workflows/PRODUCT_MOTION.md step 2.")
    missing = [w for w in json.loads(bj.read_text())["font"]["weights"]
               if not list((job / "assets/fonts").glob(f"*-{w}-latin.woff2"))]
    if missing:
        print(f"WARNING fonts missing for weights {missing}: copy <slug>-<weight>-latin.woff2 into assets/fonts")


def cmd_build(a):
    j = job_dir(a.job)
    env = node_env()
    if a.scenes:
        env["SCENES"] = a.scenes
    if a.out:
        env["OUT"] = a.out
    run(["node", "src/build.mjs"], j, env)


def cmd_check(a):
    j = job_dir(a.job)
    for f in ("h", "v"):
        run(["npx", "--yes", HF, "check", f"{a.out}/{f}"], j, check=False)


def cmd_snap(a):
    j = job_dir(a.job)
    target = selected_proportion(a)
    fmts = ["h", "v"] if target == "both" else [target]
    for f in fmts:
        out = f"qa/snap-{a.scene or 'full'}-{f}"
        run(["npx", "--yes", HF, "snapshot", f"{a.out}/{f}", "--at", a.at, "--no-end", "--describe", "false", "-o", out], j)


def cmd_sheet(a):
    j = job_dir(a.job)
    for mp4 in sorted((j / "renders").glob("*.mp4")):
        d = j / "qa" / "mp4"
        d.mkdir(parents=True, exist_ok=True)
        tag = "v" if "9x16" in mp4.name else "h"
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout or 0)
        rows = max(1, -(-int(dur / a.every + 1) // 6))
        vf = f"fps=1/{a.every},scale=360:-1,tile=6x{rows}"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-vf", vf, "-frames:v", "1", str(d / f"sheet-{tag}.jpg")], j)


def cmd_music(a):
    j = job_dir(a.job)
    if not (j / "assets/audio/music.mp3").exists():
        sys.exit("put the chosen track at assets/audio/music.mp3 first; edit BPM/downbeat constants in src/make_music.sh for that track")
    run(["zsh", "src/make_music.sh", str(a.total)], j)


def cmd_render(a):
    j = job_dir(a.job)
    cfg = json.loads((j / "src" / "brand.json").read_text())
    target = selected_proportion(a)
    video_name=cfg.get("videoName") or cfg["jobId"]
    format_id=cfg.get("formatCode") or cfg.get("formatId") or job_format(j)
    naming={"visual_id":cfg.get("visualIdentity"),"edition_code":cfg.get("editionCode")}
    version=a.version if a.version is not None else next_version(j/"renders",video_name,format_id,a.kind,"mp4",**naming)
    outputs=[]
    for f, ratio in (("h", "16:9"), ("v", "9:16")):
        if target in (f, "both"):
            filename=output_filename(video_name,ratio,format_id,version,a.kind,"mp4",**naming)
            out=j/"renders"/filename
            if out.exists():sys.exit(f"output exists: {out}; choose a new --version")
            outputs.append((f,filename))
    for f,filename in outputs:
        run(["npx", "--yes", HF, "render", f"build/{f}", "-q", a.quality, "-o", f"renders/{filename}"], j)


def job_format(job):
    text=(job/"job.yaml").read_text(encoding="utf-8") if (job/"job.yaml").exists() else ""
    for key in ("format", "client"):
        match=re.search(rf"(?m)^{key}:\s*([^\s#]+)",text)
        if match:
            value=match.group(1).strip("\"'")
            if value.lower() not in {"null","none","~"}:return value
    return "sem-formato"


def add_proportion_arg(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--proportion", choices=["16:9", "9:16", "both"],
                       help="Select output proportion")
    group.add_argument("--fmt", dest="legacy_fmt", choices=["h", "v", "both"],
                       help=argparse.SUPPRESS)


def selected_proportion(args):
    if args.proportion:
        return {"16:9": "h", "9:16": "v", "both": "both"}[args.proportion]
    return args.legacy_fmt or "both"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="c", required=True)
    n = s.add_parser("new"); identity=n.add_mutually_exclusive_group(required=True)
    identity.add_argument("--format", dest="format_id", metavar="ID", help="ID do formato")
    identity.add_argument("--client", dest="format_id", metavar="ID", help=argparse.SUPPRESS)
    n.add_argument("--visual-id", required=True); n.add_argument("--job-id", required=True)
    n.add_argument("--video-name", help="Short name to show in exported filenames; defaults to the job ID")
    n.add_argument("--include-logo", action="store_true", help="Only when explicitly requested for this job"); n.add_argument("--name", required=True); n.add_argument("--repo"); n.add_argument("--fonts-from"); n.set_defaults(f=cmd_new)
    b = s.add_parser("build"); b.add_argument("job"); b.add_argument("--scenes"); b.add_argument("--out"); b.set_defaults(f=cmd_build)
    c = s.add_parser("check"); c.add_argument("job"); c.add_argument("--out", default="build"); c.set_defaults(f=cmd_check)
    t = s.add_parser("snap"); t.add_argument("job"); t.add_argument("--at", required=True); t.add_argument("--scene")
    add_proportion_arg(t); t.add_argument("--out", default="build"); t.set_defaults(f=cmd_snap)
    h = s.add_parser("sheet"); h.add_argument("job"); h.add_argument("--every", type=float, default=3.2); h.set_defaults(f=cmd_sheet)
    m = s.add_parser("music"); m.add_argument("job"); m.add_argument("total", type=float); m.set_defaults(f=cmd_music)
    r = s.add_parser("render"); r.add_argument("job"); add_proportion_arg(r)
    r.add_argument("--quality", default="looks")
    r.add_argument("--kind", choices=["preview", "final"], default="preview", help="Preview exports include PREVIEW; finals omit it")
    r.add_argument("--version", type=int, help="Use a specific positive version; otherwise choose the next available")
    r.set_defaults(f=cmd_render)
    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
