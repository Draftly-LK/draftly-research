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
import {FilmBase, clamp, palette, type} from '../film/style';

const paper = '#F2EFE9';
const secondaryInk = '#566377';
const ease = Easing.bezier(0.2, 0.8, 0.2, 1);

const ResearchHeading: React.FC<{label: string; children: React.ReactNode}> = ({label, children}) => {
  const {fps} = useVideoConfig();
  return <>
    <div style={{position: 'absolute', left: 96, top: 58, color: secondaryInk, fontSize: 28, letterSpacing: 2}}>{label}</div>
    <CanvasImage src={staticFile('brand/logo-mark-black.png')} premountFor={fps} style={{position: 'absolute', right: 96, top: 48, width: 58, height: 58}} />
    <div style={{position: 'absolute', left: 96, right: 96, top: 149, fontFamily: type.display, fontSize: 70, lineHeight: 1.12}}>{children}</div>
  </>;
};

/** Twenty-five seconds: scenario, unverified source lead, then the missing authority. */
export const ResearchContribution: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <FilmBase>
      <AbsoluteFill style={{background: paper, color: palette.ink}}>
        <ResearchHeading label="LEGAL INFORMATION RETRIEVAL">Find the provisions behind the question.</ResearchHeading>
        <div style={{position: 'absolute', left: 96, right: 96, top: 288, height: 2, background: '#B9B5AC'}} />

        <div style={{position: 'absolute', left: 96, top: 323, fontFamily: type.display, fontSize: 40}}>Scenario</div>
        <div style={{position: 'absolute', left: 620, top: 320, fontSize: 44, color: palette.gold}}>→</div>
        <div style={{position: 'absolute', left: 705, top: 323, fontFamily: type.display, fontSize: 40}}>Required provisions</div>
        <div style={{position: 'absolute', left: 1230, top: 320, fontSize: 44, color: palette.gold}}>→</div>
        <div style={{position: 'absolute', left: 1315, top: 323, fontFamily: type.display, fontSize: 40}}>Retrieved provisions</div>

        <div style={{position: 'absolute', left: 96, top: 421, width: 495, opacity: interpolate(frame, [0, 0.6 * fps], [0, 1], clamp), translate: `0 ${interpolate(frame, [0, 0.8 * fps], [18, 0], {...clamp, easing: ease})}px`}}>
          <div style={{fontSize: 28, color: secondaryInk}}>TITLE &amp; INSTRUMENT</div>
          <CanvasImage src={staticFile('evidence/title-extent.png')} premountFor={fps} style={{display: 'block', width: 495, height: 44, objectFit: 'contain', objectPosition: 'left center', marginTop: 19}} />
          <div style={{fontFamily: type.display, fontSize: 52, marginTop: 15}}>0.0159 <span style={{fontFamily: type.ui, fontSize: 28}}>hectares</span></div>
          <div style={{fontSize: 28, color: secondaryInk, marginTop: 32}}>SURVEY EXTRACT</div>
          <div style={{display: 'flex', gap: 25, alignItems: 'center', marginTop: 16}}>
            <CanvasImage src={staticFile('evidence/survey-extent.png')} premountFor={fps} style={{display: 'block', width: 92, height: 110, objectFit: 'contain'}} />
            <div style={{fontFamily: type.display, fontSize: 52}}>0.0153 <span style={{fontFamily: type.ui, fontSize: 28}}>ha</span></div>
          </div>
          <div style={{fontFamily: type.display, fontSize: 35, lineHeight: 1.25, marginTop: 32}}>How should the differing extents be examined for this transfer?</div>
        </div>

        <div style={{position: 'absolute', left: 657, top: 421, width: 1, height: 450, background: '#CBC5BA'}} />
        <div style={{position: 'absolute', left: 705, top: 421, width: 493, opacity: interpolate(frame, [8 * fps, 8.6 * fps], [0, 1], clamp), translate: `0 ${interpolate(frame, [8 * fps, 8.8 * fps], [18, 0], {...clamp, easing: ease})}px`}}>
          <div style={{fontSize: 28, color: secondaryInk}}>FOR LAWYER IDENTIFICATION</div>
          <div style={{fontSize: 30, marginTop: 50, color: secondaryInk}}>Source lead to inspect</div>
          <div style={{fontFamily: type.display, fontSize: 52, lineHeight: 1.17, marginTop: 19}}>Registration of<br />Title Act</div>
          <div style={{fontSize: 31, color: '#76541D', marginTop: 27}}>Unverified source lead</div>
          <div style={{width: 100, height: 3, background: palette.gold, marginTop: 38}} />
          <div style={{fontSize: 31, lineHeight: 1.4, marginTop: 29}}>The required provisions have not been established here.</div>
        </div>

        <div style={{position: 'absolute', left: 1267, top: 421, width: 1, height: 450, background: '#CBC5BA'}} />
        <div style={{position: 'absolute', left: 1315, top: 421, right: 96, opacity: interpolate(frame, [16 * fps, 16.6 * fps], [0, 1], clamp), translate: `0 ${interpolate(frame, [16 * fps, 16.8 * fps], [18, 0], {...clamp, easing: ease})}px`}}>
          <div style={{fontSize: 28, color: secondaryInk}}>MISSING AUTHORITY</div>
          <div style={{fontFamily: type.display, fontSize: 53, lineHeight: 1.17, marginTop: 49}}>Approved passage unavailable.</div>
          <div style={{width: '100%', borderTop: '3px dashed #A58D60', marginTop: 42}} />
          <div style={{fontSize: 31, lineHeight: 1.4, marginTop: 29}}>No approved supporting passage is available in this recording.</div>
          <div style={{fontSize: 31, lineHeight: 1.4, marginTop: 27}}>Lawyer inspection remains required.</div>
        </div>

        <div style={{position: 'absolute', left: 96, right: 96, bottom: 53, borderTop: `3px solid ${palette.gold}`, paddingTop: 24, fontSize: 29, lineHeight: 1.3, color: secondaryInk, opacity: interpolate(frame, [17 * fps, 17.6 * fps], [0, 1], clamp)}}>Keep the source lead and the missing authority visible for review.</div>
      </AbsoluteFill>
    </FilmBase>
  );
};

/** Fifteen-second illustration; planned status remains visible on every frame. */
export const PlannedSourceInspection: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (
    <FilmBase>
      <AbsoluteFill style={{background: paper, color: palette.ink}}>
        <ResearchHeading label="Planned source inspection">Read the source at the relevant date.</ResearchHeading>
        <div style={{position: 'absolute', left: 96, right: 96, top: 288, height: 2, background: '#B9B5AC'}} />

        <div style={{position: 'absolute', left: 96, top: 353, width: 545, opacity: interpolate(frame, [0.2 * fps, 0.8 * fps], [0, 1], clamp)}}>
          <div style={{fontSize: 28, letterSpacing: 1.2, color: secondaryInk}}>SOURCE AND RELATED AMENDMENTS</div>
          <div style={{fontFamily: type.display, fontSize: 54, lineHeight: 1.15, marginTop: 37}}>Registration of<br />Title Act</div>
          <div style={{height: 3, width: 110, background: palette.gold, marginTop: 37}} />
          <div style={{fontSize: 32, lineHeight: 1.4, marginTop: 30}}>Bring the source and related amendments into the same review.</div>
          <div style={{fontSize: 29, color: secondaryInk, lineHeight: 1.4, marginTop: 31}}>Source lead awaiting inspection.</div>
        </div>

        <div style={{position: 'absolute', left: 726, top: 351, width: 1, height: 495, background: '#CBC5BA'}} />
        <div style={{position: 'absolute', left: 825, top: 363, fontSize: 34}}>Transaction date</div>
        <div style={{position: 'absolute', right: 113, top: 363, fontSize: 34}}>Current date</div>
        <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
          <path d="M845 476 L1785 476" fill="none" stroke="#A29B8D" strokeWidth="3" />
          <path d="M845 476 L1785 476" fill="none" stroke={palette.gold} strokeWidth="4" strokeDasharray="940" strokeDashoffset={interpolate(frame, [0.4 * fps, 1.4 * fps], [940, 0], {...clamp, easing: ease})} />
          <circle cx="845" cy="476" r="10" fill={palette.ink} />
          <circle cx="1785" cy="476" r="10" fill={palette.ink} />
          <path d="M845 505 L845 559 M1785 505 L1785 559" fill="none" stroke="#A29B8D" strokeWidth="2" />
        </svg>
        <div style={{position: 'absolute', left: 825, top: 585, fontSize: 29, color: secondaryInk}}>Inspect source context</div>
        <div style={{position: 'absolute', right: 113, top: 585, fontSize: 29, color: secondaryInk}}>Inspect source context</div>

        <div style={{position: 'absolute', left: 825, right: 96, top: 703, borderTop: '2px dashed #A58D60', paddingTop: 29, opacity: interpolate(frame, [4.5 * fps, 5.2 * fps], [0, 1], clamp)}}>
          <div style={{fontFamily: type.display, fontSize: 44}}>Unknown commencement dates</div>
          <div style={{fontSize: 32, color: secondaryInk, lineHeight: 1.35, marginTop: 20}}>Kept for lawyer review.</div>
        </div>

        <div style={{position: 'absolute', left: 96, right: 96, bottom: 60, borderTop: `3px solid ${palette.gold}`, paddingTop: 26, fontSize: 29, lineHeight: 1.4}}>Deployment and runtime acceptance have not been verified for this recording.</div>
      </AbsoluteFill>
    </FilmBase>
  );
};
