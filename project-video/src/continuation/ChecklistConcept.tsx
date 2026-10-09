import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {clamp, palette, type} from '../film/style';

const ease = Easing.bezier(0.2, 0.8, 0.2, 1);
const ink = palette.ink;
const muted = '#526074';
const line = '#D4DAE3';
const green = '#246348';
const amber = '#83571B';
const ui = type.ui;

type TaskStatus = 'Open' | 'In progress' | 'Complete' | 'Needs review';
type ChecklistStage = 'outline' | 'suggestion' | 'accepted' | 'sources' | 'recording' | 'complete';

const groups = [
  {name: 'Documents and facts', total: 2, completed: 2},
  {name: 'Evidence and checks', total: 2, completed: 1},
  {name: 'Drafting', total: 1, completed: 0},
  {name: 'Signing and attestation', total: 1, completed: 0},
  {name: 'Stamping and registration', total: 1, completed: 0},
  {name: 'Final completion', total: 1, completed: 0},
] as const;

const Check: React.FC<{complete?: boolean; review?: boolean; size?: number}> = ({complete, review, size = 32}) => (
  <svg width={size} height={size} viewBox="0 0 32 32" style={{flexShrink: 0}}>
    {complete ? <>
      <circle cx="16" cy="16" r="14" fill={green}/>
      <path d="m9 16 5 5 9-10" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
    </> : review ? <>
      <path d="M16 3 30 28H2Z" fill="#F1DEBA" stroke={amber} strokeWidth="1.8" strokeLinejoin="round"/>
      <path d="M16 11v8" stroke={amber} strokeWidth="2.5" strokeLinecap="round"/>
      <circle cx="16" cy="23" r="1.5" fill={amber}/>
    </> : <circle cx="16" cy="16" r="13" fill="none" stroke="#8290A2" strokeWidth="2"/>}
  </svg>
);

const Status: React.FC<{status: TaskStatus}> = ({status}) => {
  const color = status === 'Complete' ? green : status === 'Needs review' ? amber : status === 'In progress' ? '#2F527D' : muted;
  const background = status === 'Complete' ? '#E7F0EA' : status === 'Needs review' ? '#F6E8CD' : status === 'In progress' ? '#E8EFF8' : '#EBEEF3';
  return <span style={{display: 'inline-flex', alignItems: 'center', gap: 9, fontSize: 26, fontWeight: 550, color, background, borderRadius: 5, padding: '6px 12px', whiteSpace: 'nowrap'}}>
    <span style={{width: 8, height: 8, borderRadius: status === 'Needs review' ? 0 : 8, background: color}}/>{status}
  </span>;
};

const SectionLabel: React.FC<{children: React.ReactNode; color?: string}> = ({children, color = muted}) => (
  <div style={{fontFamily: ui, fontSize: 26, fontWeight: 550, color, lineHeight: 1.25}}>{children}</div>
);

const GroupRail: React.FC<{completed: boolean; review: boolean}> = ({completed, review}) => (
  <div style={{width: 408, flexShrink: 0, background: '#F0F3F7', borderRight: `1px solid ${line}`, paddingTop: 24}}>
    <div style={{padding: '0 26px 18px', fontSize: 26, color: muted}}>Checklist groups</div>
    {groups.map((group, index) => <div key={group.name} style={{position: 'relative', padding: '9px 24px 9px 26px', minHeight: 65, display: 'flex', alignItems: 'center', background: index === 1 ? '#E4EAF2' : 'transparent', borderTop: `1px solid ${index === 1 ? '#D4DCE6' : 'transparent'}`, borderBottom: `1px solid ${index === 1 ? '#D4DCE6' : 'transparent'}`}}>
      {index === 1 ? <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: 5, background: review ? '#A97729' : palette.gold}}/> : null}
      <div style={{display: 'flex', alignItems: 'center', gap: 16, width: '100%'}}>
        <span style={{fontSize: 26, color: index === 1 ? ink : muted, fontVariantNumeric: 'tabular-nums', width: 33, flexShrink: 0}}>{String(index + 1).padStart(2, '0')}</span>
        <div style={{fontSize: 26, color: ink, fontWeight: index === 1 ? 600 : 450, lineHeight: 1.15, flex: 1}}>{group.name}</div>
        <span style={{fontSize: 26, color: index === 1 && completed ? green : muted, fontVariantNumeric: 'tabular-nums', flexShrink: 0}}>{index === 1 && completed ? 2 : group.completed}/{group.total}</span>
      </div>
    </div>)}
  </div>
);

const TaskList: React.FC<{status: TaskStatus; accepted: boolean}> = ({status, accepted}) => (
  <div style={{width: 496, flexShrink: 0, borderRight: `1px solid ${line}`, background: '#FCFDFE', padding: '28px 26px'}}>
    <SectionLabel>Evidence and checks</SectionLabel>
    <div style={{fontSize: 30, fontWeight: 600, marginTop: 6, marginBottom: 18}}>Two checks. One next step.</div>
    <div style={{padding: '16px 0', borderTop: `1px solid ${line}`, borderBottom: `1px solid ${line}`}}>
      <div style={{display: 'flex', gap: 17, alignItems: 'flex-start'}}><Check complete/><div style={{fontSize: 29, lineHeight: 1.2}}>Review title record</div></div>
      <div style={{marginTop: 12, marginLeft: 49}}><Status status="Complete"/></div>
    </div>
    <div style={{border: `2px solid ${status === 'Needs review' ? '#AF823E' : palette.gold}`, background: status === 'Needs review' ? '#FCF6E9' : '#FAF8F0', padding: '17px 19px', marginTop: 18, borderRadius: 6}}>
      <div style={{display: 'flex', alignItems: 'flex-start', gap: 16}}><Check complete={status === 'Complete'} review={status === 'Needs review'}/><div style={{fontSize: 30, fontWeight: 600, lineHeight: 1.18}}>{status === 'Needs review' ? <>Recheck supporting<br/>evidence</> : <>Compare recorded<br/>extents</>}</div></div>
      <div style={{margin: '13px 0 12px 48px'}}><Status status={status}/></div>
      <div style={{fontSize: 26, color: muted, lineHeight: 1.3, paddingTop: 13, borderTop: '1px solid #DCD9CC', whiteSpace: 'pre-line'}}>{status === 'Complete' ? 'Illustrative record saved.\nClarification remains open.' : status === 'Needs review' ? 'Review proposed for a new source version.' : accepted ? 'Accepted review step.\nCompare both recorded extents.' : 'A source difference remains to be checked.'}</div>
    </div>
  </div>
);

/** Owner-approved case-001 crops and extents match the preserved Opening scene. */
const SourceCrop: React.FC<{name: string; code: string; extent: '0.0159' | '0.0153'; source: 'title' | 'survey'; updated?: boolean; active?: boolean}> = ({name, code, extent, source, updated = false, active = true}) => (
  <div style={{background: '#FFFEFB', border: `1px solid ${active ? '#C5CDD9' : '#DADFE7'}`, borderLeft: `4px solid ${updated ? '#A97729' : palette.gold}`, padding: '10px 20px', position: 'relative'}}>
    <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, lineHeight: 1}}><div style={{fontSize: 26, fontWeight: 600, color: '#526074'}}>{name}</div><div style={{fontSize: 26, color: muted}}>{code}</div></div>
    <div style={{borderTop: '1px solid #CBD1D9', paddingTop: 10, marginTop: 8, display: 'flex', alignItems: 'center', gap: 19}}><Img src={staticFile(`evidence/${source}-extent.png`)} style={{width: source === 'title' ? 350 : 88, height: 43, objectFit: 'contain', objectPosition: 'left center'}}/><div style={{fontFamily: type.display, fontSize: 40, lineHeight: 1, padding: '0 11px 3px', background: updated ? '#F1DEBA' : '#F9E8C6', color: ink, marginLeft: 'auto', whiteSpace: 'nowrap'}}>{extent} <span style={{fontFamily: ui, fontSize: 26}}>ha</span></div></div>
  </div>
);

const OutlineInspector: React.FC = () => <>
  <SectionLabel>Task inspector</SectionLabel>
  <div style={{fontSize: 36, fontWeight: 600, lineHeight: 1.16, margin: '17px 0 22px'}}>Compare recorded extents</div>
  <Status status="Open"/>
  <div style={{fontSize: 28, lineHeight: 1.45, color: muted, marginTop: 26}}>The title certificate and transfer instrument record 0.0159 ha. The survey extract records 0.0153 ha.</div>
  <div style={{display: 'flex', alignItems: 'baseline', gap: 28, borderTop: `1px solid ${line}`, borderBottom: `1px solid ${line}`, padding: '26px 0', marginTop: 28}}>
    <span style={{fontSize: 26, color: muted}}>Title and instrument <strong style={{display: 'block', fontFamily: type.display, fontSize: 48, color: ink, marginTop: 8}}>0.0159 ha</strong></span><span style={{fontSize: 34, color: '#A1ABBA'}}>↔</span><span style={{fontSize: 26, color: muted}}>Survey extract <strong style={{display: 'block', fontFamily: type.display, fontSize: 48, color: ink, marginTop: 8}}>0.0153 ha</strong></span>
  </div>
  <div style={{fontSize: 27, lineHeight: 1.4, color: muted, marginTop: 27}}>Next action<br/><strong style={{color: ink, fontWeight: 550}}>Inspect the recorded extents.</strong></div>
</>;

const SuggestionInspector: React.FC<{accepted: boolean}> = ({accepted}) => <>
  <SectionLabel>Task inspector · recorded extent comparison</SectionLabel>
  <div style={{marginTop: 18, borderLeft: `4px solid ${accepted ? green : palette.gold}`, paddingLeft: 24}}>
    <div style={{fontSize: 27, color: accepted ? green : amber, fontWeight: 600, lineHeight: 1.2}}>{accepted ? 'Lawyer accepted the review step' : 'Agent suggestion · awaiting lawyer decision'}</div>
    <div style={{fontSize: 34, fontWeight: 600, lineHeight: 1.2, marginTop: 14}}>Compare the<br/>recorded extents.</div>
    <div style={{fontSize: 27, lineHeight: 1.3, marginTop: 14, color: muted}}>Title certificate: 0.0159 ha<br/>Transfer instrument: 0.0159 ha<br/>Survey extract: 0.0153 ha</div>
  </div>
  <div style={{marginTop: 18, paddingTop: 16, borderTop: `1px solid ${line}`, fontSize: 26, lineHeight: 1.3, color: muted}}>{accepted ? <>Review step added to this task.<br/><span style={{color: ink}}>The source difference is still open.</span></> : <>Suggested step for the existing task.<br/>A lawyer decides whether to add it.</>}</div>
  <div style={{display: 'flex', alignItems: 'center', gap: 22, marginTop: 20}}>
    <div style={{background: accepted ? '#E7F0EA' : palette.navy, border: `1px solid ${accepted ? '#BBD0C1' : palette.navy}`, color: accepted ? green : palette.cream, fontSize: 28, fontWeight: 550, padding: '13px 24px', borderRadius: 5}}>{accepted ? '✓ Review step accepted' : 'Accept review step'}</div>
    {!accepted ? <div style={{fontSize: 26, color: muted}}>Dismiss</div> : null}
  </div>
</>;

const SourcesInspector: React.FC<{recording: boolean; complete: boolean}> = ({recording, complete}) => <>
  <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}><SectionLabel>{complete ? 'Lawyer record · illustrative' : 'Two sources open · case-001 display crops'}</SectionLabel>{complete ? <Status status="Complete"/> : null}</div>
  <div style={{fontSize: 32, fontWeight: 600, marginTop: 10, marginBottom: 14}}>{complete ? 'Illustrative comparison record saved.' : recording ? 'Lawyer records the comparison.' : 'Read the extent in each source.'}</div>
  <SourceCrop name="TITLE CERTIFICATE" code="Source A" extent="0.0159" source="title"/>
  <div style={{height: 14}}/>
  <SourceCrop name="SURVEY EXTRACT" code="Source B" extent="0.0153" source="survey"/>
  <div style={{borderTop: `1px solid ${line}`, marginTop: 16, paddingTop: 14}}>
    {recording || complete ? <>
      <div style={{fontSize: 26, color: muted}}>Lawyer note · illustrative comparison</div>
      <div style={{fontSize: 26, lineHeight: 1.2, marginTop: 7, color: ink}}>Title and instrument record 0.0159 ha.<br/>Survey extract records 0.0153 ha; clarification remains open.</div>
      <div style={{display: 'flex', alignItems: 'center', gap: 19, marginTop: 10}}><div style={{fontSize: 28, fontWeight: 550, padding: '8px 23px', background: complete ? '#E7F0EA' : palette.navy, color: complete ? green : palette.cream, borderRadius: 5}}>{complete ? '✓ Source comparison recorded' : 'Record source comparison'}</div></div>
    </> : <div style={{fontSize: 27, lineHeight: 1.4, color: muted}}>Extents differ. The task stays in progress<br/>until the lawyer records the comparison.</div>}
  </div>
</>;

const ProgressStrip: React.FC<{completed: boolean; review: boolean; accepting?: boolean}> = ({completed, review, accepting = false}) => {
  return <div style={{height: 103, borderTop: `1px solid ${line}`, background: '#EDF1F6', display: 'flex', alignItems: 'center', padding: '0 29px', gap: 29, flexShrink: 0}}>
    <div style={{width: 377, flexShrink: 0}}><div style={{fontSize: 24, color: muted, whiteSpace:'nowrap'}}>Illustrative progress · {completed ? '50' : '37.5'}%</div><div style={{fontSize: 31, fontWeight: 600, marginTop: 4, fontVariantNumeric: 'tabular-nums', whiteSpace:'nowrap'}}>{completed ? '4' : '3'}/8 tasks complete</div></div>
    <div style={{width: 220, height: 8, background: '#CFD7E2', borderRadius: 2, overflow: 'hidden'}}><div style={{height: '100%', background: completed ? green : review ? '#A97729' : palette.gold, width: completed ? '50%' : '37.5%'}}/></div>
    <div style={{width: 1, height: 54, background: '#C7D0DD', margin: '0 2px 0 7px'}}/>
    <div style={{flex: 1}}><div style={{fontSize: 26, color: muted}}>Next action</div><div style={{fontSize: 30, fontWeight: 550, marginTop: 4}}>{review ? 'Recheck supporting evidence.' : completed ? 'Follow up on the extent difference.' : accepting ? 'Open both sources for comparison.' : 'Compare recorded extents.'}</div></div>
  </div>;
};

const Workspace: React.FC<{status: TaskStatus; accepted: boolean; completed: boolean; review?: boolean; children: React.ReactNode}> = ({status, accepted, completed, review = false, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <div style={{position: 'absolute', left: 96, top: 260, width: 1728, height: 752, background: '#FFF', color: ink, border: '1px solid #6D7C91', borderRadius: 8, overflow: 'hidden', display: 'flex', flexDirection: 'column', translate: `0 ${interpolate(frame, [0, 0.6 * fps], [14, 0], {...clamp, easing: ease})}px`, opacity: interpolate(frame, [0, 0.4 * fps], [0, 1], clamp)}}>
    <div style={{height: 70, flexShrink: 0, background: '#E1E7EF', display: 'flex', alignItems: 'center', padding: '0 28px', borderBottom: `1px solid ${line}`, gap: 24}}>
      <div style={{fontSize: 29, fontWeight: 600}}>case-001 · Property transfer</div><div style={{height: 26, width: 1, background: '#ADB8C7'}}/><div style={{fontSize: 27, color: muted}}>Title extent · 0.0159 ha</div><div style={{marginLeft: 'auto', fontSize: 26, color: muted}}>Checklist workspace · concept</div>
    </div>
    <div style={{display: 'flex', flex: 1, minHeight: 0}}><GroupRail completed={completed} review={review}/><TaskList status={status} accepted={accepted}/><div style={{flex: 1, padding: '28px 27px', background: '#FFF', overflow: 'hidden'}}>{children}</div></div>
    <ProgressStrip completed={completed} review={review} accepting={accepted && !completed}/>
  </div>;
};

const ConceptHeading: React.FC<{overview?: boolean}> = ({overview = false}) => <>
  <div style={{position: 'absolute', left: 96, top: 49, right: 96, paddingBottom: 19, borderBottom: '1px solid #526075', color: palette.cream, fontSize: 28, letterSpacing: 0.25}}>Workflow concept · case-001 · illustrative progress</div>
  <div style={{position: 'absolute', left: 96, top: 122, fontFamily: type.display, color: palette.paper, fontSize: overview ? 66 : 70, lineHeight: 1.1}}>{overview ? 'Know what’s done—and what comes next.' : 'A living checklist. A clear next action.'}</div>
  <div style={{position: 'absolute', left: 99, top: 213, color: palette.muted, fontSize: 26}}>Owner-approved case-001 sources · proposed lawyer-directed workflow.</div>
</>;

const ConceptCursor: React.FC<{action: 'accept' | 'complete'}> = ({action}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const arrival = action === 'accept' ? 4.65 : 13.75;
  const commit = action === 'accept' ? 5.2 : 14.4;
  return <svg width="42" height="49" viewBox="0 0 42 49" style={{position: 'absolute', left: action === 'accept' ? 1317 : 1398, top: action === 'accept' ? 813 : 828, pointerEvents: 'none', zIndex: 5, opacity: interpolate(frame, [(arrival - 0.4) * fps, arrival * fps, commit * fps, (commit + 0.3) * fps], [0, 1, 1, 0], clamp), translate: `${interpolate(frame, [(arrival - 0.4) * fps, arrival * fps], [40, 0], {...clamp, easing: ease})}px ${interpolate(frame, [(arrival - 0.4) * fps, arrival * fps], [28, 0], {...clamp, easing: ease})}px`, scale: interpolate(frame, [(commit - 0.1) * fps, commit * fps, (commit + 0.12) * fps], [1, 0.84, 1], {...clamp, easing: ease})}}><path d="M5 3v35l9-9 9 17 8-5-9-15 14-2Z" fill={palette.cream} stroke={palette.navy} strokeWidth="2.5" strokeLinejoin="round"/></svg>;
};

/** 18 seconds; render inside the parent's FilmBase. All state comes from the frame. */
export const ChecklistConcept: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame / fps;
  const stage: ChecklistStage = seconds < 2.3 ? 'outline' : seconds < 5.2 ? 'suggestion' : seconds < 7 ? 'accepted' : seconds < 11 ? 'sources' : seconds < 14.4 ? 'recording' : 'complete';
  const accepted = seconds >= 5.2;
  const completed = stage === 'complete';
  const status: TaskStatus = completed ? 'Complete' : accepted ? 'In progress' : 'Open';
  const paneStart = stage === 'outline' ? 0 : stage === 'suggestion' ? 2.3 : stage === 'accepted' ? 5.2 : stage === 'sources' ? 7 : stage === 'recording' ? 11 : 14.4;
  return <AbsoluteFill style={{background: palette.navy, fontFamily: ui}}>
    <ConceptHeading/>
    <Workspace status={status} accepted={accepted} completed={completed}>
      <div style={{opacity: interpolate(frame, [paneStart * fps, (paneStart + 0.22) * fps], [0.45, 1], clamp), translate: `0 ${interpolate(frame, [paneStart * fps, (paneStart + 0.32) * fps], [10, 0], {...clamp, easing: ease})}px`}}>
        {stage === 'outline' ? <OutlineInspector/> : stage === 'suggestion' || stage === 'accepted' ? <SuggestionInspector accepted={accepted}/> : <SourcesInspector recording={stage === 'recording'} complete={completed}/>}
      </div>
    </Workspace>
    {stage === 'suggestion' ? <ConceptCursor action="accept"/> : stage === 'recording' ? <ConceptCursor action="complete"/> : null}
  </AbsoluteFill>;
};

const OverviewInspector: React.FC<{changed: boolean; review: boolean}> = ({changed, review}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <>
    <SectionLabel>{changed ? 'Proposed source-version event · concept' : 'Matter overview · illustrative record'}</SectionLabel>
    <div style={{fontSize: 35, fontWeight: 600, marginTop: 12, lineHeight: 1.2}}>{changed ? 'New source version received' : 'The source comparison is recorded.'}</div>
    <div style={{marginTop: 18}}><SourceCrop name={changed ? 'TITLE CERTIFICATE · VERSION 3' : 'TITLE CERTIFICATE · CURRENT'} code="Source A" extent="0.0159" source="title" updated={changed}/></div>
    <div style={{borderTop: `1px solid ${line}`, marginTop: 18, paddingTop: 16, opacity: changed ? interpolate(frame, [1.2 * fps, 1.45 * fps], [0, 1], clamp) : 1}}>
      <div style={{fontSize: 26, color: muted}}>{changed ? 'Recorded extent stays unchanged' : 'Lawyer record · illustrative'}</div>
      <div style={{fontSize: 30, lineHeight: 1.3, marginTop: 9}}>{changed ? <>Title extent: <span style={{fontWeight: 550}}>0.0159 ha</span></> : <>0.0159 ha and 0.0153 ha compared.</>}</div>
    </div>
    <div style={{marginTop: 18, padding: '16px 0 0', borderTop: `1px solid ${line}`, opacity: review ? interpolate(frame, [1.7 * fps, 2 * fps], [0, 1], clamp) : 1}}>
      <SectionLabel>{review ? 'Affected task' : 'Current task state'}</SectionLabel>
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 13, marginTop: 12}}><div style={{fontSize: 29, fontWeight: 550}}>{review ? 'Recheck supporting evidence' : 'Compare recorded extents'}</div><Status status={review ? 'Needs review' : 'Complete'}/></div>
      <div style={{fontSize: 27, color: muted, lineHeight: 1.3, marginTop: 14}}>{review ? 'Inspect the new version and supporting sources.' : 'Clarification of the extent difference remains open.'}</div>
    </div>
  </>;
};

/** Five seconds; a proposed source-version event moves illustrative progress from 4/8 to 3/8. */
export const OverviewConcept: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const changed = frame >= 1.2 * fps;
  const review = frame >= 1.7 * fps;
  return <AbsoluteFill style={{background: palette.navy, fontFamily: ui}}>
    <ConceptHeading overview/>
    <Workspace status={review ? 'Needs review' : 'Complete'} accepted completed={!review} review={review}>
      <OverviewInspector changed={changed} review={review}/>
    </Workspace>
  </AbsoluteFill>;
};
