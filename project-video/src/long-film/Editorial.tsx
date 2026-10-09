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
import {Desk, FilmBase, clamp, palette, type} from '../film/style';

const ease = Easing.bezier(0.2, 0.8, 0.2, 1);
const paper = '#F2EFE9';
const secondaryInk = '#566377';

const sourceNames: Record<string, string> = {
  title: 'Title certificate',
  'paper-title': 'Our legal information retrieval research',
  'title-act-cover': 'Official source lead',
  instrument: 'Transfer instrument · page 2',
  'instrument-cover': 'Transfer instrument · cover',
  survey: 'Survey extract',
  resolution: 'Board resolution',
  payment: 'Payment record',
  identity: 'Identity document',
  'title-extent': 'Title certificate · extent detail',
  'instrument-extent': 'Transfer instrument · extent detail',
  'survey-extent': 'Survey extract · extent detail',
};

const EditorialLabel: React.FC<{children: React.ReactNode; dark?: boolean}> = ({children, dark}) => (
  <div style={{position: 'absolute', left: 96, top: 58, fontSize: 28, letterSpacing: 2, textTransform: 'uppercase', color: dark ? secondaryInk : palette.cream}}>
    {children}
  </div>
);

const EditorialMark: React.FC<{dark?: boolean}> = ({dark}) => {
  const {fps} = useVideoConfig();
  return <CanvasImage src={staticFile(`brand/logo-mark-${dark ? 'black' : 'white'}.png`)} premountFor={fps} style={{position: 'absolute', right: 96, top: 48, width: 58, height: 58}} />;
};

type PortraitProps = {
  name: string;
  file: string;
  left: number;
  revealAt: number;
  children?: React.ReactNode;
};

const PractitionerPortrait: React.FC<PortraitProps> = ({name, file, left, revealAt, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <div style={{position: 'absolute', left, top: 300, width: 400, opacity: interpolate(frame, [revealAt * fps, (revealAt + 0.55) * fps], [0, 1], clamp), translate: `0 ${interpolate(frame, [revealAt * fps, (revealAt + 0.8) * fps], [20, 0], {...clamp, easing: ease})}px`}}>
      <CanvasImage src={staticFile(file)} premountFor={fps} style={{display: 'block', width: 400, height: 382, objectFit: 'contain', objectPosition: '50% 100%'}} />
      <div style={{height: 2, background: palette.gold, marginTop: 26}} />
      <div style={{fontFamily: type.display, fontSize: 34, lineHeight: 1.15, marginTop: 20, color: palette.cream}}>{name}</div>
      {children ? <div style={{fontSize: 28, lineHeight: 1.35, color: palette.muted, marginTop: 13}}>{children}</div> : null}
    </div>
  );
};

/** Twenty-second editorial hold; photographs retain their original proportions. */
export const PractitionerStory: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <FilmBase>
      <EditorialLabel>Practitioner conversations</EditorialLabel>
      <EditorialMark />
      <div style={{position: 'absolute', left: 96, top: 145, fontFamily: type.display, fontSize: 82, lineHeight: 1.1, color: palette.cream, opacity: interpolate(frame, [0, 0.45 * fps], [0, 1], clamp)}}>Grounded in practice.</div>
      <PractitionerPortrait name="Anura Dhanaratna" file="people/anura-dhanaratna.jpeg" left={96} revealAt={0.1}>
        Attorney-at-Law &amp;<br />
        Notary Public;<br />
        Lecturer, SLLC
      </PractitionerPortrait>
      <PractitionerPortrait name="Aruni Gunarathne" file="people/aruni-gunarathna.jpeg" left={539} revealAt={0.2}>
        Attorney-at-Law &amp;<br />Notary Public
      </PractitionerPortrait>
      <PractitionerPortrait name="Priyal Wijayaweera, PC" file="people/priyal-wijayaweera.jpeg" left={982} revealAt={0.3}>
        President’s Counsel,<br />Attorney-at-Law
      </PractitionerPortrait>
      <PractitionerPortrait name="Ishan Rathnapala" file="people/ishan-rathnapala.jpeg" left={1425} revealAt={0.4}>
        Senior State Counsel,<br />Attorney General’s Dept.
      </PractitionerPortrait>
      <div style={{position: 'absolute', left: 96, right: 96, top: 929, height: 1, background: '#536071'}} />
      <div style={{position: 'absolute', left: 96, top: 962, fontSize: 34, color: palette.cream, opacity: interpolate(frame, [0.8 * fps, 1.3 * fps, 6.1 * fps, 6.5 * fps], [0, 1, 1, 0], clamp)}}>Discussions with five lawyers.</div>
      <div style={{position: 'absolute', left: 96, top: 962, fontSize: 34, color: palette.cream, opacity: interpolate(frame, [6.5 * fps, 7 * fps, 12.6 * fps, 13 * fps], [0, 1, 1, 0], clamp)}}>One lawyer contributed to developing the workflow.</div>
      <div style={{position: 'absolute', left: 96, top: 962, fontSize: 34, color: palette.cream, opacity: interpolate(frame, [13 * fps, 13.5 * fps], [0, 1], clamp)}}>Guidance from Legal IR and NLP experts.</div>
    </FilmBase>
  );
};

export type SourceInspectionProps = {
  source: string;
  headline: string;
  note: string;
  detail?: string;
};

/** Six-to-twelve-second source view. All entrance motion finishes within one second. */
export const SourceInspection: React.FC<SourceInspectionProps> = ({source, headline, note, detail}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sourcePath = source.includes('/') ? source.replace(/^\/+/, '') : `evidence/${source.endsWith('.png') ? source : `${source}.png`}`;
  const sourceId = sourcePath.split('/').pop()?.replace(/\.png$/i, '') ?? source;

  return (
    <FilmBase>
      <AbsoluteFill style={{background: paper, color: palette.ink}}>
        <EditorialLabel dark>{sourceNames[sourceId] ?? 'Read the supplied source'}</EditorialLabel>
        <EditorialMark dark />
        <div style={{position: 'absolute', left: 76, top: 144, width: 1044, height: 826, translate: `0 ${interpolate(frame, [0, 0.9 * fps], [24, 0], {...clamp, easing: ease})}px`, rotate: `${interpolate(frame, [0, 0.9 * fps], [-0.45, 0], {...clamp, easing: ease})}deg`}}>
          <CanvasImage src={staticFile(sourcePath)} premountFor={fps} style={{display: 'block', width: '100%', height: '100%', objectFit: 'contain', filter: 'drop-shadow(0 12px 18px rgba(15,27,46,0.14))'}} />
        </div>
        <div style={{position: 'absolute', left: 1190, right: 96, top: 188, bottom: 107, display: 'flex', flexDirection: 'column', opacity: interpolate(frame, [0.15 * fps, 0.7 * fps], [0, 1], clamp)}}>
          <div style={{fontFamily: type.display, fontSize: 60, lineHeight: 1.12}}>{headline}</div>
          {detail ? <div style={{fontSize: 32, lineHeight: 1.45, color: secondaryInk, marginTop: 38}}>{detail}</div> : null}
          <div style={{marginTop: 'auto', paddingTop: 36}}>
            <div style={{width: 104, height: 3, background: palette.gold, marginBottom: 26}} />
            <div style={{fontSize: 29, lineHeight: 1.45}}>{note}</div>
          </div>
        </div>
      </AbsoluteFill>
    </FilmBase>
  );
};

/** Twenty seconds with the three actual source details and the question left open. */
export const EvidenceComparison: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <FilmBase>
      <AbsoluteFill style={{background: paper, color: palette.ink}}>
        <EditorialLabel dark>Compare the source records</EditorialLabel>
        <EditorialMark dark />
        <div style={{position: 'absolute', left: 96, top: 149, fontFamily: type.display, fontSize: 72, lineHeight: 1.1}}>The discrepancy remains open.</div>
        <div style={{position: 'absolute', left: 96, top: 301, width: 936, opacity: interpolate(frame, [0, 0.6 * fps], [0, 1], clamp), translate: `0 ${interpolate(frame, [0, 0.8 * fps], [18, 0], {...clamp, easing: ease})}px`}}>
          <div style={{fontSize: 28, letterSpacing: 1.3, color: secondaryInk}}>TITLE CERTIFICATE</div>
          <CanvasImage src={staticFile('evidence/title-extent.png')} premountFor={fps} style={{display: 'block', width: 900, height: 88, objectFit: 'contain', objectPosition: 'left center', marginTop: 24}} />
          <div style={{fontSize: 28, letterSpacing: 1.3, color: secondaryInk, marginTop: 46}}>TRANSFER INSTRUMENT · PAGE 2</div>
          <CanvasImage src={staticFile('evidence/instrument-extent.png')} premountFor={fps} style={{display: 'block', width: 900, height: 80, objectFit: 'contain', objectPosition: 'left center', marginTop: 24}} />
          <div style={{fontFamily: type.display, fontSize: 96, marginTop: 34, fontVariantNumeric: 'tabular-nums'}}>0.0159 <span style={{fontFamily: type.ui, fontSize: 34}}>hectares</span></div>
        </div>
        <div style={{position: 'absolute', left: 1130, top: 310, width: 1, height: 448, background: '#B9B5AC'}} />
        <div style={{position: 'absolute', left: 1230, top: 301, right: 96, opacity: interpolate(frame, [0.7 * fps, 1.2 * fps], [0, 1], clamp), translate: `0 ${interpolate(frame, [0.7 * fps, 1.4 * fps], [18, 0], {...clamp, easing: ease})}px`}}>
          <div style={{fontSize: 28, letterSpacing: 1.3, color: secondaryInk}}>SURVEY EXTRACT</div>
          <CanvasImage src={staticFile('evidence/survey-extent.png')} premountFor={fps} style={{display: 'block', width: 184, height: 220, objectFit: 'contain', marginTop: 26}} />
          <div style={{fontFamily: type.display, fontSize: 96, marginTop: 86, fontVariantNumeric: 'tabular-nums'}}>0.0153</div>
          <div style={{fontSize: 34, marginTop: 3}}>hectares</div>
        </div>
        <div style={{position: 'absolute', left: 96, right: 96, top: 865, borderTop: `3px solid ${palette.gold}`, paddingTop: 30, opacity: interpolate(frame, [2.5 * fps, 3.2 * fps], [0, 1], clamp)}}>
          <div style={{fontFamily: type.display, fontSize: 40, lineHeight: 1.25}}>Parcel identity and transaction context still need checking.</div>
          <div style={{fontSize: 29, color: secondaryInk, marginTop: 20}}>No legal resolution is shown.</div>
        </div>
      </AbsoluteFill>
    </FilmBase>
  );
};

/** Fifteen seconds: return to the source file, then hold the final brand statement. */
export const ClosingLong: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <FilmBase>
      <Desk />
      <EditorialLabel>Return to the source file</EditorialLabel>
      <div style={{position: 'absolute', left: 205, top: 179, width: 900, height: 747, background: '#B6A17D', rotate: '-3deg', boxShadow: '0 22px 42px rgba(0,0,0,.28)'}}>
        <div style={{position: 'absolute', left: 0, top: -35, width: 240, height: 48, background: '#B6A17D', borderRadius: '12px 16px 0 0'}} />
        <CanvasImage src={staticFile('evidence/title.png')} premountFor={fps} style={{position: 'absolute', left: 188, top: 31, width: 492, height: 696, objectFit: 'contain', rotate: '2deg', translate: `0 ${interpolate(frame, [0, 0.9 * fps], [-20, 0], {...clamp, easing: ease})}px`, boxShadow: '0 8px 18px rgba(0,0,0,.2)'}} />
      </div>
      <div style={{position: 'absolute', left: 1225, right: 100, top: 340, opacity: interpolate(frame, [0.3 * fps, 0.9 * fps], [0, 1], clamp)}}>
        <div style={{fontFamily: type.display, fontSize: 66, lineHeight: 1.12, color: palette.cream}}>The evidence stays with the matter.</div>
        <div style={{fontSize: 32, lineHeight: 1.45, marginTop: 36}}>The practitioner decides what follows.</div>
      </div>
      <AbsoluteFill style={{background: palette.navy, opacity: interpolate(frame, [5.2 * fps, 6.3 * fps], [0, 1], clamp)}} />
      <div style={{position: 'absolute', left: 96, right: 96, top: 248, opacity: interpolate(frame, [6.3 * fps, 7.2 * fps], [0, 1], clamp), translate: `0 ${interpolate(frame, [6.3 * fps, 7.3 * fps], [16, 0], {...clamp, easing: ease})}px`}}>
        <CanvasImage src={staticFile('brand/logo-mark-white.png')} premountFor={fps} style={{display: 'block', width: 108, height: 108}} />
        <div style={{fontFamily: type.display, fontSize: 118, lineHeight: 1.05, marginTop: 26}}>Draftly</div>
        <div style={{width: 125, height: 3, background: palette.gold, marginTop: 40}} />
        <div style={{fontFamily: type.display, fontSize: 64, lineHeight: 1.18, marginTop: 38, color: palette.cream}}>From documents to<br />guided matter workflow.</div>
      </div>
    </FilmBase>
  );
};
