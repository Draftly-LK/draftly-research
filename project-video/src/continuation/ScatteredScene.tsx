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
import {BrandBug, clamp, palette, type} from '../film/style';

const ease = Easing.bezier(0.2, 0.8, 0.2, 1);

type DocumentPageProps = {
  file: string;
  left: number;
  top: number;
  width: number;
  height: number;
  angle: number;
  arriveAt: number;
};

const DocumentPage: React.FC<DocumentPageProps> = ({file, left, top, width, height, angle, arriveAt}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <div
      style={{
        position: 'absolute',
        left,
        top,
        width,
        height,
        opacity: interpolate(frame, [arriveAt * fps, (arriveAt + 0.3) * fps], [0, 1], clamp),
        translate: `0 ${interpolate(frame, [arriveAt * fps, (arriveAt + 0.65) * fps], [42, 0], {...clamp, easing: ease})}px`,
        rotate: `${interpolate(frame, [arriveAt * fps, (arriveAt + 0.65) * fps], [angle - 3, angle], {...clamp, easing: ease})}deg`,
        transformOrigin: 'center bottom',
      }}
    >
      <CanvasImage
        src={staticFile(file)}
        premountFor={fps}
        style={{
          width: '100%',
          height: '100%',
          display: 'block',
          objectFit: 'contain',
          filter: 'drop-shadow(0 7px 7px rgba(15,27,46,0.18))',
        }}
      />
    </div>
  );
};

/** Six-second approved CASE-001 source board; render within FilmBase. */
export const ScatteredScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <AbsoluteFill style={{background: palette.navy, color: palette.paper}}>
      <BrandBug />
      <div style={{position: 'absolute', left: 96, top: 58, color: palette.cream, fontSize: 23, letterSpacing: 1.3}}>
        CASE-001 · approved client bundle
      </div>
      <div
        style={{
          position: 'absolute',
          left: 96,
          top: 144,
          fontFamily: type.display,
          fontSize: 78,
          lineHeight: 1.08,
          color: palette.cream,
          opacity: interpolate(frame, [0, 0.35 * fps], [0, 1], clamp),
        }}
      >
        Every matter starts with<br />
        scattered information.
      </div>

      <div style={{position: 'absolute', left: 0, right: 0, top: 350, bottom: 0, background: '#E8E3DA'}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 350, height: 3, background: palette.gold}} />

      <DocumentPage file="evidence/title.png" left={110} top={378} width={394} height={550} angle={-1.4} arriveAt={0.12} />
      <DocumentPage file="evidence/survey.png" left={550} top={378} width={394} height={550} angle={1.2} arriveAt={0.22} />
      <DocumentPage file="evidence/instrument.png" left={990} top={378} width={394} height={550} angle={-0.8} arriveAt={0.32} />
      <DocumentPage file="evidence/identity.png" left={1458} top={415} width={335} height={476} angle={1.8} arriveAt={0.42} />

      <div
        style={{
          position: 'absolute',
          left: 96,
          right: 96,
          top: 950,
          color: palette.ink,
          opacity: interpolate(frame, [0.9 * fps, 1.3 * fps], [0, 1], clamp),
        }}
      >
        <div style={{position: 'absolute', left: 0, width: 394}}>
          <div style={{fontSize: 20, letterSpacing: 1.1}}>TITLE CERTIFICATE</div>
          <div style={{fontFamily: type.display, fontSize: 50, marginTop: 5}}>0.0159 <span style={{fontSize: 28}}>ha</span></div>
        </div>
        <div style={{position: 'absolute', left: 440, width: 394}}>
          <div style={{fontSize: 20, letterSpacing: 1.1}}>SURVEY EXTRACT</div>
          <div style={{fontFamily: type.display, fontSize: 50, marginTop: 5}}>0.0153 <span style={{fontSize: 28}}>ha</span></div>
        </div>
        <div style={{position: 'absolute', left: 880, width: 394}}>
          <div style={{fontSize: 20, letterSpacing: 1.1}}>TRANSFER INSTRUMENT</div>
          <div style={{fontFamily: type.display, fontSize: 50, marginTop: 5}}>0.0159 <span style={{fontSize: 28}}>ha</span></div>
        </div>
        <div style={{position: 'absolute', left: 1320, width: 394}}>
          <div style={{fontSize: 20, letterSpacing: 1.1}}>IDENTITY DOCUMENT</div>
          <div style={{fontFamily: type.display, fontSize: 30, lineHeight: 1.1, marginTop: 14}}>What does each<br />record describe?</div>
        </div>
      </div>
      <div
        style={{
          position: 'absolute',
          left: 96,
          width: 835,
          bottom: 31,
          height: 2,
          background: palette.gold,
          scale: `${interpolate(frame, [1.25 * fps, 1.95 * fps], [0, 1], {...clamp, easing: ease})} 1`,
          transformOrigin: 'left',
        }}
      />
    </AbsoluteFill>
  );
};
