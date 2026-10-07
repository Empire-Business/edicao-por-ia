# Method

## Objective
Turn raw local media into reproducible, reviewed edits while minimizing model context and keeping editorial intent inspectable.

## Core sequence

### 1. Identify the unit of work
A **job** equals one intended final video. One source may create several jobs; several sources may feed one job.

### 2. Inventory before reasoning
Record source paths, hashes, stream metadata, duration, orientation, frame rate, audio presence and basic integrity. Do this with local tools.

### 3. Build compact evidence
For speech-driven material:
- timestamped local transcript;
- silence map;
- optional scene/frame map;
- contact sheet at low resolution;
- extra frames only around candidate cuts or visual questions.

Do not ask a model to inspect every frame.

### 4. Separate deterministic from editorial work
Deterministic operations belong to scripts. Model reasoning belongs to questions such as:
- Is this a retake or intentional repetition?
- Which take communicates the idea cleanly?
- Where does one independent video end and another begin?
- Which style pattern best applies?

### 4a. Optional script and automatic silence
Transcribe the recording independently. When a reference script is provided, compare by idea/meaning and select actual takes before shortening pauses. Do not demand verbatim delivery. Mark intentional pauses; use the local silence planner against the approved assembly EDL. Never shorten audio separately from video.

### 5. Plan before rendering
Write candidate decisions, then an EDL. Every segment must name its source and source-time `in`/`out` points.

### 6. Render a draft
Drafts are disposable. Final exports are not created until QA gates pass.

### 7. QA mechanically and editorially
Mechanical QA: streams, duration, black frames, abnormal silence, corruption, output properties.
Editorial QA: meaning preserved, no obvious cut words, correct order, requested pattern respected, captions/visuals readable.

### 8. Learn only from evidence
Approved/exported is not automatically a winner. A reusable “winner” requires real result evidence recorded under `memory/`.


## Proactive format memory (v1.4)
Explicit user facts/preferences need no audience metrics to be saved. At entry and after feedback,
run `workflows/FORMAT_MEMORY.md`; apply the effective job and verify personalization. Keep measured
performance separate from taste, and format/project/job memory separate from universal patterns.
