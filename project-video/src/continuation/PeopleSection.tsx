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

type PortraitProps = {
  name: string;
  file: string;
  left: number;
  revealAt: number;
  objectPosition?: string;
  children?: React.ReactNode;
};

// A single editorial treatment intentionally controls all four portraits.
// The square aperture crops the photograph without altering facial proportions.
const Portrait: React.FC<PortraitProps> = ({
  name,
  file,
  left,
  revealAt,
  objectPosition = '50% 50%',
  children,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <div
      style={{
        position: 'absolute',
        left,
        top: 342,
        width: 400,
        opacity: interpolate(frame, [revealAt * fps, (revealAt + 0.55) * fps], [0, 1], clamp),
        translate: `0 ${interpolate(frame, [revealAt * fps, (revealAt + 0.65) * fps], [24, 0], {...clamp, easing: ease})}px`,
      }}
    >
      <div style={{width: 400, height: 400, overflow: 'hidden', background: palette.cream}}>
        <CanvasImage
          src={staticFile(file)}
          premountFor={fps}
          style={{
            display: 'block',
            width: 400,
            height: 400,
            objectFit: 'cover',
            objectPosition,
          }}
        />
      </div>
      <div
        style={{
          height: 2,
          marginTop: 28,
          background: palette.gold,
          scale: `${interpolate(frame, [(revealAt + 0.35) * fps, (revealAt + 0.95) * fps], [0, 1], {...clamp, easing: ease})} 1`,
          transformOrigin: 'left',
        }}
      />
      <div style={{fontFamily: type.display, fontSize: 34, lineHeight: 1.15, marginTop: 21, color: palette.cream}}>
        {name}
      </div>
      {children ? <div style={{fontSize: 23, lineHeight: 1.45, color: palette.muted, marginTop: 12}}>{children}</div> : null}
    </div>
  );
};

/** Six seconds at the parent composition's fps; render within FilmBase. */
export const PeopleSection: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <AbsoluteFill style={{background: palette.navy, color: palette.paper}}>
      <BrandBug />
      <div style={{position: 'absolute', left: 96, top: 58, color: palette.cream, fontSize: 23, letterSpacing: 2}}>
        PRACTITIONER CONVERSATIONS
      </div>
      <div
        style={{
          position: 'absolute',
          left: 96,
          top: 148,
          fontFamily: type.display,
          fontSize: 82,
          lineHeight: 1.1,
          color: palette.cream,
          opacity: interpolate(frame, [0, 0.4 * fps], [0, 1], clamp),
          translate: `0 ${interpolate(frame, [0, 0.65 * fps], [18, 0], {...clamp, easing: ease})}px`,
        }}
      >
        Grounded in practice.
      </div>
      <div
        style={{
          position: 'absolute',
          left: 96,
          right: 96,
          top: 290,
          height: 1,
          background: '#536071',
          scale: `${interpolate(frame, [0.1 * fps, 0.8 * fps], [0, 1], {...clamp, easing: ease})} 1`,
          transformOrigin: 'left',
        }}
      />

      <Portrait name="Anura Dhanaratna" file="people/anura-dhanaratna.jpeg" left={96} revealAt={0.12} objectPosition="50% 38%">
        Lawyer · Notary<br />
        Law College conveyancing lecturer
      </Portrait>
      <Portrait name="Aruni Gunarathna" file="people/aruni-gunarathna.jpeg" left={539} revealAt={0.22} objectPosition="50% 0%" />
      <Portrait name="Priyal Wijayaweera" file="people/priyal-wijayaweera.jpeg" left={982} revealAt={0.32} />
      <Portrait name="Ishan Rathnapala" file="people/ishan-rathnapala.jpeg" left={1425} revealAt={0.42} />

      <div
        style={{
          position: 'absolute',
          left: 96,
          bottom: 46,
          fontSize: 28,
          color: palette.cream,
          opacity: interpolate(frame, [0.75 * fps, 1.25 * fps], [0, 1], clamp),
        }}
      >
        Five lawyer discussions · workflow input from one lawyer<br/>
        Legal IR and NLP expert guidance
      </div>
    </AbsoluteFill>
  );
};
