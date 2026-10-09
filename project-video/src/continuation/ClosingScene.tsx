import React from 'react';
import {
  AbsoluteFill,
  CanvasImage,
  Easing,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {clamp, palette, type} from '../film/style';

const ease = Easing.bezier(0.2, 0.8, 0.2, 1);

/** Three-second closing; the final 2.2 seconds hold the settled wordmark. */
export const ClosingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <AbsoluteFill style={{background: palette.navy, color: palette.cream, alignItems: 'center'}}>
      <CanvasImage
        src={staticFile('brand/logo-mark-white.png')}
        premountFor={fps}
        style={{
          position: 'absolute',
          top: 302,
          width: 104,
          height: 104,
          objectFit: 'contain',
          opacity: interpolate(frame, [0, 0.35 * fps], [0, 1], clamp),
          translate: `0 ${interpolate(frame, [0, 0.35 * fps], [10, 0], {...clamp, easing: ease})}px`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 440,
          fontFamily: type.display,
          fontSize: 152,
          lineHeight: 1,
          letterSpacing: -3,
          opacity: interpolate(frame, [0.08 * fps, 0.45 * fps], [0, 1], clamp),
          translate: `0 ${interpolate(frame, [0.08 * fps, 0.45 * fps], [14, 0], {...clamp, easing: ease})}px`,
        }}
      >
        Draftly
      </div>
      <div
        style={{
          position: 'absolute',
          top: 632,
          width: 480,
          height: 2,
          background: palette.gold,
          scale: `${interpolate(frame, [0.15 * fps, 0.6 * fps], [0, 1], {...clamp, easing: ease})} 1`,
          transformOrigin: 'center',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: 684,
          fontSize: 39,
          lineHeight: 1.3,
          fontFamily: type.ui,
          textAlign: 'center',
          opacity: interpolate(frame, [0.24 * fps, 0.75 * fps], [0, 1], clamp),
        }}
      >
        From documents to a guided matter workflow.
      </div>
    </AbsoluteFill>
  );
};
