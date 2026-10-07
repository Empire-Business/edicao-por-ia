# Optional React / Remotion adapter

Status: adapter/source supplied; NOT installed or integration-tested in this build. The fully tested path is the bundled JavaScript/SVG browser renderer. Use this adapter when the chosen effect requires React or complex scenes. This is not necessary for normal cuts, pause removal or simple motion.

## Authorized local setup
1. Use an isolated project directory. Review Remotion's current license for your intended business/team use. Do not assume that every commercial use is free.
2. Read official docs listed in `sources/MOTION_RESEARCH.md`. Install an available Node.js release supported by your selected Remotion version.
3. In this folder, only after permission: `npm install --save-exact remotion @remotion/cli react react-dom`. Check that remotion and @remotion/cli resolved to exactly the same version. If not, pin both to one available compatible version. Retain package-lock.json and use `npm ci` thereafter. Do not run install on every video.
4. `npm run dev` opens local Studio. The included `src/index.jsx` imports the same reviewed JS/SVG template library as the lightweight engine.
5. Preview with supplied default demo or a props JSON of the form `{"spec":{...}}`. External raster assets must be staged/embedded deliberately; the React wrapper does not resolve arbitrary filesystem paths from asset_path.
6. A local transparent export command, after actual installation:
   `npx --no-install remotion render src/index.jsx Motion motion.webm --props props.json --codec vp9 --image-format png --pixel-format yuva420p`
   Ensure output does not exist. For verified integration into external NLEs, use an alpha-capable codec as documented, not H.264 transparency.
7. Test a short sequence with your installed dependency versions before production. Review actual frames, alpha and sync. Store command, versions, asset hashes and any local lockfile. Missing dependencies mean PENDING, never PASS.

## Evolving beyond the adapter
Use useCurrentFrame/interpolate/spring, local assets, inputProps, explicit durationInFrames/fps and responsive composition layout. Decode video with Remotion's documented frame-aware media components, not a free-playing HTML video tag. Re-time against the clean master before mounting a Sequence.

For complete composition inside Remotion, keep the clean master as the sole narrator audio source and place overlays above it. For an external FFmpeg finish, preserve alpha and supply validated frames/metadata. The lightweight PNG compositor does not directly accept a WebM file.

No cloud/Lambda upload, browser download or package installation should be hidden in an edit operation. No fonts are distributed in this package.
