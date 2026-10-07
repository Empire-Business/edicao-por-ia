# Pesquisa externa — animações por JavaScript
Verified: 2026-09-25. Added for v1.3.0, not derived from the user's original methodology document.

## Fatos externos e fontes primárias
- Anthropic, Introducing Claude Opus 5.5: https://www.anthropic.com/claude-opus-5-5
  Supports coding capability and the model's existence. The announcement consulted did NOT establish a specific benchmark of superior JavaScript animation quality. User's observation is a useful design input, not measured evidence from this package.
- Remotion, Prompting videos with coding agents: https://www.remotion.dev/docs/ai/coding-agents
  Describes using coding agents, including Claude Code and Codex, to create programmatic videos; Node.js and a local project are part of that route.
- Remotion, Animating properties: https://www.remotion.dev/docs/animating-properties
  Documents frame-driven animation using useCurrentFrame, interpolate and spring; warns about uncontrolled CSS transitions causing render problems.
- Remotion, Flickering: https://www.remotion.dev/docs/flickering
  Basis for deterministic rendering and avoiding hidden time/random state.
- Remotion, renderMedia: https://www.remotion.dev/docs/renderer/render-media
  Documents programmatic exports, input props, composition dimensions/fps, and render configuration.
- Remotion, Transparent videos: https://www.remotion.dev/docs/transparent-videos
  Documents alpha-compatible video settings. Transparent PNG layers are used for the bundled lightweight route instead.
- Remotion license entry: https://www.remotion.dev/license
  Verify current terms before business use. No interpretation of licensing eligibility is asserted here.
- Playwright Python screenshots: https://playwright.dev/python/docs/screenshots
  Browser screenshot capture, used by the lightweight local renderer.
- Playwright Page API: https://playwright.dev/python/docs/api/class-page
  JavaScript injection/evaluation and screenshot parameters for rendering reviewed local code.
- FFmpeg filters: https://ffmpeg.org/ffmpeg-filters.html#overlay
  Overlay/filter support, used to composite layers while mapping audio from the clean master.
- Claude Code subagents: https://code.claude.com/docs/en/sub-agents
  Per-subagent model selection. This does not automatically implement the same routing in Codex or another host.

## Decisões de arquitetura (não benchmarks externos)
Opus for a new complex motion design; Sonnet/local props for reuse; zero LLM calls during rendering; place motion after silence edits; default to an offline lightweight renderer where enough, Remotion for advanced compositions. These are engineering choices in this skill. Token reductions are not measured or guaranteed percentages.

## Verification limitations
npm registry access failed (DNS EAI_AGAIN) in the build environment. No Remotion packages were installed; no Remotion render was run. The optional adapter is labeled accordingly. Local JavaScript/browser/FFmpeg tests are recorded separately in the v1.3 report, not inferred from documentation.
