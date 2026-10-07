import React from 'react';
import {AbsoluteFill, Composition, getInputProps, registerRoot, useCurrentFrame} from 'remotion';
import '../../browser/motion.js';
import demo from '../../examples/keyphrase.json';

const Motion = ({spec}) => {
  const frame = useCurrentFrame();
  // Only reviewed code builds this SVG, and all plain-text values are escaped.
  return <AbsoluteFill dangerouslySetInnerHTML={{__html: globalThis.CVFMotion.renderFrame(frame, spec)}} />;
};
const Root = () => {
  const {spec = demo} = getInputProps();
  globalThis.CVFMotion.validate(spec);
  return <Composition id="Motion" component={Motion} width={spec.width} height={spec.height}
    fps={spec.fps} durationInFrames={spec.duration_frames} defaultProps={{spec}} />;
};
registerRoot(Root);
