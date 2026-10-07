# Workflow — Create, render and insert JavaScript animations

## Format checkpoint (v1.4)
Run `FORMAT_MEMORY.md` at entry: recover the active format's scoped preferences, capture new
facts/feedback and use the resolved effective job. Do not load another format's context.
For a one-off correction, keep it job-scoped. Before delivery, run `PERSONALIZATION_QA.md`.


## Goal and inputs
Make relevant reusable animations, synchronized to edited speech. Input: active child job, approved style/brand, locked clean master + EDL, retimed transcript, and optional authorized images/videos. Load `method/MOTION_POLICY.md` and only the selected motion preset.

## Process
1. Assess purpose. Name the exact spoken idea an animation would clarify. Respect animation off/clean pattern. Do not add a title merely because a template exists.
2. Resolve timing AFTER speech/silence cleanup. Use retained-word times to set clean-master start/end frames; allow reading time, prevent overlap with an unrelated idea. Save `analysis/motion_brief.json` and `analysis/motion_plan.json`.
3. Select an approved component. Existing props/geometry/text substitution → local code or Sonnet. New sophisticated visual system → Opus as motion designer once, then Sonnet for implementation/refinement. Haiku may organize asset notes; not final art direction. No model calls to render frames.
4. For a new design, request: editable JavaScript/TypeScript component, parameter spec, asset map, motion rationale, frame timing, and small tests. Explicitly forbid simulated clocks/CSS loops and rewriting approved material. Review code before executing it.
5. Build a spec using `motion/examples/keyphrase.json` or another listed template. Reuse color/type rules from the active format; shipped examples are simulations only. All paths are relative to the spec/plan location unless absolute. `asset_path` is a local raster screenshot for proof-frame; input originals stay untouched.
6. Render selected keyframes first:
   `python3 tools/render_motion.py jobs/<id>/motion/spec.json --outdir jobs/<id>/motion/keyframes-v1 --frames 0,15,45,89`
   Choose indices inside this spec's duration. Inspect entrance, settled state, exit, text bounds, alpha and the active format identity. Keyframe previews cannot be composited as complete animations.
7. Render full frames to a NEW directory:
   `python3 tools/render_motion.py jobs/<id>/motion/spec.json --outdir jobs/<id>/motion/frames-v1`
   Then create a motion plan using `motion/MOTION_PLAN_TEMPLATE.json`; replace every placeholder with real paths and SHA-256 values. Need a current master and EDL. Each layer references its complete `frames.json` and a clean-master `start_frame`.
8. Validate and composite:
   Get a proportion-specific preview filename with `tools/output_naming.py` using the video name,
   format ID and master proportion, then pass that path to `composite_motion.py --output ... --dry-run`.
   Then run the same command without `--dry-run`. PNG layers have no audio; the compositor retains the clean master's audio. Layer order is explicit bottom-to-top. Prevent unintended overlaps editorially.
9. For advanced scenes use `motion/remotion/README.md`. The simple compositor only accepts the bundled PNG manifest contract. A WebM/ProRes export is NOT directly accepted by it; either composite in Remotion or convert and validate all alpha frames to this contract.
10. Review several actual output frames AND watch the motion at playback speed. Check master duration/audio unchanged, cue alignment, correct child, readability, cropping, alpha, no flicker, no added false claims, no subtitle collision. Update the job's QA state separately from tool execution success.
11. Persist approved component version + props. On future videos only change per-job data. Revise only affected scenes, not transcript/cuts or the full project.

## Outputs
Source code, spec/props, semantic motion plan, complete frame manifest with hashes, composited draft, `qa/motion-qa.json`, reusable preset candidate. Final only after applicable visual/audio/editorial gates.

## Common errors / stop criteria
Source seconds used as output timing; inserting motion as an EDL speech segment; masking the entire face with a black rectangle; regenerating approved code; forcing all assets; judging only still frames; calling rendered synthetic tests a real user approval. Stop only the affected optional step on a dependency error, not unrelated safe editing.

## Reference-driven studio extension (v1.7)
For supplied visual references, bespoke scenes, state lists or a showreel, route through `workflows/MOTION_STUDIO.md`. It adds a style guide, state list, reusable seek renderer, paginated evidence and bounded review. Do not skip locked speech timing, format context or costs.
