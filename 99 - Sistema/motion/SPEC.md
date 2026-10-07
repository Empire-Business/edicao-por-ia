# Motion spec contract

`id` and `child_id`: nonempty identifiers. `template`: keyphrase / steps / lower-third / proof-frame. `width`, `height`: actual final output geometry. `fps`: same constant frame rate as the clean master. `duration_frames`: integer duration of this local animation, not the entire base video.

`mode`: overlay keeps outside pixels transparent; fullframe covers the frame. `lines`: up to three short lines; proof-frame may use an empty array. `steps`: two to four short step labels, required only for steps. `label`: optional label for proof-frame. `asset_path`: an authorized PNG/JPEG/WebP relative to this spec; originals are not rewritten. Animated image files and SVG assets are rejected by the lightweight route.

`colors`: explicit hex foreground/background/accent from approved context. `font_family`: a local installed family/fallback; no font files are distributed or fetched. `box`: normalized x/y/w/h inside the frame. Verify actual face/subtitle-safe areas: it is not enough for the box to be inside the canvas.

The JS validator enforces structure. The model/user supplies semantic correctness, readable copy, styling and safe position; those are not guaranteed by a passing syntax test. Examples are labeled simulations. Unknown complex animation requirements require reviewed new code, not unsupported fields added to a spec.

## Plan contract
`motion/MOTION_PLAN_TEMPLATE.json` uses clean_master_frames. Each layer starts at a nonnegative integer frame; its duration comes from a complete frames.json. `base` and `edl` path/hash pairs freeze the version. `frames` includes path/hash of the rendered manifest. `child_id` must match at plan/layer/manifest levels. `speech_cue` and `reason` explain placement. Layers are ordered back-to-front; editorial overlap checking remains required.

Changing a source EDL/master or rendered frame breaks validation until reviewed hashes and placement are deliberately regenerated. Never automatically replace stale hashes without re-evaluating timings.
