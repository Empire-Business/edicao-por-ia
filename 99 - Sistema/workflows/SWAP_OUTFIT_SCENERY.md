# Workflow — Swap Outfit / Scenery (any format)

## Goal
Change what the presenter wears and/or the place behind them in a short range of a recording,
from ONE take, with a generative video-edit model. It is a picture treatment of the source, not an
editing format: it can be requested in any F/FP with any ID and never changes cuts, captions,
pacing, palette or fonts.

Triggers: “troca a minha roupa”, “me coloca de blazer”, “muda o cenário”, “troca o fundo”,
“com um estalo eu troco de roupa”.

## Before spending
1. Read `method/EXTERNAL_SERVICES.md` → *OpenRouter — outfit/scenery swap*.
2. Resolve F + ID and run `FORMAT_MEMORY.md` as in any edit. A missing pair blocks the edit, not the
   answer about what this capability does.
3. Ask only for what is missing, in plain language:
   - which recording and which moment (the user may point to a phrase or gesture, e.g. a finger snap);
   - what changes (outfit, scenery or both) and the new look in their own words;
   - how the short range may reach the provider (see consent below).
4. Tell the price before running: `python3 tools/gen_video_edit.py models` gives the live price.
   The tool refuses a run above `--max-usd` (default US$ 0.50); raise it only with the user's yes.

## Consent — per clip, never assumed
The range leaves the computer. The provider (OpenRouter + the model's company) only accepts a public
HTTPS link, not a file. Offer exactly these two options and wait for the answer:
- the user hosts the range and gives the link → `--source-url`;
- a temporary public link, removed after 1 hour (Litterbox) → `--temp-public-link`. Anyone holding
  the random link can watch the range during that hour. Say so.
An earlier yes does not cover another recording or another person. Never send a range showing someone
who is not the requester without their stated authorization. This is not ScrapeCreators or voice
isolation: there is no standing authorization.

## Quality: send the crop, keep the original face (author, 20/10/2026)
"Achei que a minha imagem de roupa social ficou com baixa qualidade" / "o MEU VÍDEO está com baixíssima qualidade".
The model returns ~704×1248 whatever it receives. Sending the full 2160×3840 frame meant a ~3× upscale, and the split
layout then zoomed in again (~6–7×); the model also redraws the face (smoother skin, slightly different expression).
Mandatory for presenter shots:
1. Send only what will be on screen: cut each range as an upright 9:16 crop from head to just below the waist at
   native resolution (e.g. 1440×2560 out of a 2160×3840 frame) and pass that clip as `--input` (start 0). The same
   704×1248 then covers the crop, not the whole frame. One generation per range that stays in the cut (≤ 10 s each).
2. Put the ORIGINAL head back: `tools/composite_original_head.py --original <crop> --generated <generation>
   --out <crop>-camisa.mov --head X,Y --head-size W,H --report …` (X,Y = head centre in the first frame; read it on a
   coordinate grid of that frame). It keeps the generated clothes/hands/background and pastes the original head at
   full resolution, tracked frame by frame, scale-matched and feathered, with an edge colour fix. Check the report:
   `ncc_median` ≥ 0.95; a low `ncc_min` usually means a hand crossed the face — inspect that frame.
3. Frame the presenter from these crops (e.g. split panel ≈ 1240×1102 of the 1440×2560 crop, full screen ≈ 1260×2240)
   so the face is downscaled, never upscaled. Compare a face close-up of the result with the original before delivery.
4. If an older job used the full frame, re-use its generations: cut the matching original ranges at the same size and
   run step 2 (no new spend).

## Process
1. Pick the range in SOURCE time, inside a part of the recording that stays in the cut. Keep it short:
   1–10 s per generation (validated at 5 s). A snap, clap or cut is a good start point; the swap
   back happens at the end of the phrase or on the next cut.
2. Translate the user's description to a concrete English description (garment, colour, fit; or
   place, time of day, light). For scenery, match the time of day of the recording unless asked
   otherwise: the model does not relight the person.
3. Generate:
   `python3 tools/gen_video_edit.py run --input <recording> --start S --duration D --change roupa|cenario|ambos --describe "<english>" --out <job>/assets/generated/<name>.mp4 (--source-url URL | --temp-public-link)`
   Output: the range at the recording's size and frame rate with the ORIGINAL audio, a side-by-side
   `…-antes-e-depois.mp4`, and `<name>.receipt.json` (model, prompt, cost, sizes; no key, no link).
4. Inspect real frames of the side-by-side before showing it: identity of the face, hands, held
   objects, edges while gesturing, flicker, and the first/last frame against their neighbours.
5. Show the side-by-side and get the user's approval. A rejected result is regenerated only with a
   new yes (it costs again); change the description, do not repeat the same request.
6. Put it in the edit without touching timing:
   `python3 tools/gen_video_edit.py patch --input <recording> --clip <name>.mp4 --start S --out <job>/sources/derived/<recording>-troca-v1.mov`
   The derived copy has the same duration, size, frame rate and untouched audio. Point the job's
   source/EDL to it and re-render only the picture stages that depend on that range. Voice isolation,
   transcript, cuts, captions and motion remain valid. The original recording is never modified.
7. Optional, by format/job: mark the swap with a short transition (flash, frame, label) through the
   normal motion workflow. It is not added by default.
8. Record in `edit/decision_log.md`: range, change, model, cost from the receipt, hosting option
   chosen and the user's approval. Count the cost in the job budget.

## Checks
- The person is still recognisably the same; the model slightly redraws the face. If the user
  rejects the likeness, do not deliver the range.
- Mouth and gestures stay in sync with the untouched audio.
- No jump in framing at the entry and exit frames.
- The result returns near 720p and is upscaled to the recording's size: compare sharpness with the
  neighbouring original frames, especially in 4K sources.
- Nothing was sent beyond the approved range; the receipt matches the decision log.

## Limits to state honestly
- Validated on 2026-10-12 with `black-forest-labs/flux-video-edit`, a 5 s vertical talking-head
  range, for outfit, scenery and both at once. Other models, longer ranges, several people, fast
  camera movement and horizontal sources are untested: run a short paid test with consent first.
- Not for a whole video: cost grows per second and consistency between separate generations is not
  guaranteed. Chain ranges only when each one starts on a cut.
- Never use it to put a person in clothing, places or situations that misrepresent them, or on
  someone who did not ask. The result is a generated image of a real person.

## Common errors
- Sending the whole recording or a range that the cut later removes.
- Assuming yesterday's consent or a public link for a new clip.
- Replacing the audio with the model's output (the tool keeps the original on purpose).
- Calling it “edited only by the assistant”: the picture comes from the video model; say which one.
