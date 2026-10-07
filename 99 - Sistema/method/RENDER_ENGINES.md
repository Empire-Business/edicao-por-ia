# Render Engines

## FFmpeg — default
Best for:
- cuts and concatenation;
- crop/scale/pad;
- audio fades/normalization;
- simple captions/overlays;
- transcodes and delivery variants.

Advantages: deterministic, fast, scriptable, low overhead.

## Hybrid FFmpeg + Remotion — optional
Use when the pattern genuinely requires:
- elaborate animated typography;
- reusable branded motion systems;
- data-driven compositions;
- complex visual templates that are easier to express in React.

Preferred flow:
1. create clean assembly with FFmpeg;
2. retime transcript/caption data;
3. apply motion layer in Remotion;
4. final media QA with FFmpeg/ffprobe.

Do not introduce Remotion merely for cuts, simple subtitles or reframing.

## v1.3 execution paths and precedence
The above engine descriptions are capabilities, not claims that the old cut-only `render_edl.py` implements all overlays. The executable motion route is now `tools/render_motion.py` (reviewed JavaScript/SVG → transparent PNGs) + `tools/composite_motion.py` (validated PNG layers over a locked clean master; narrator retained).

Use Remotion as the preferred advanced JS/React option when composition complexity warrants it, not solely because it is installed. See `motion/remotion/README.md` for the optional untested adapter. Never substitute a silent animation clip into spoken segments to simulate an overlay.
