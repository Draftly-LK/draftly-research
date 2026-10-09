// Editable shot list. Seconds are editorial holds, not guessed speech timestamps.
// No narration or estimated captions are used in this version.
export type ShotKind = 'opening'|'source'|'practitioners'|'bundle'|'manual'|'app'|'question'|'thread'|'research'|'planned'|'closing';
export interface Shot {
  id: string;
  seconds: number;
  kind: ShotKind;
  headline?: string;
  source?: string;
  clip?: string;
  start?: number;
  end?: number;
  crop?: [number, number, number, number];
  label?: string;
  replacement?: string;
  mode?: string;
}
export interface Chapter {id: string; title: string; shots: Shot[]}
export const EDIT: Chapter[] = [
  {id:'problem',title:'The file opens',shots:[
    {id:'opening',seconds:45,kind:'opening'},
    {id:'opening-source-return',seconds:12,kind:'source',source:'title',headline:'A detail is useful when its source stays in view.'},
    {id:'opening-thread',seconds:8,kind:'thread',mode:'source'},
  ]},
  {id:'why',title:'Practitioner input',shots:[
    {id:'practitioner-notes',seconds:30,kind:'practitioners'},
  ]},
  {id:'bundle',title:'The client bundle',shots:[
    {id:'bundle-spread',seconds:10,kind:'bundle'},
    {id:'bundle-survey',seconds:10,kind:'source',source:'survey',headline:'The survey extract needs its own reading.'},
    {id:'bundle-resolution',seconds:10,kind:'source',source:'resolution',headline:'What does the resolution authorize?'},
    {id:'bundle-payment',seconds:10,kind:'source',source:'payment',headline:'What does the payment record establish?'},
  ]},
  {id:'compare',title:'Keep the detail connected',shots:[
    {id:'manual-two-pages',seconds:14,kind:'manual'},
    {id:'comparison-review',seconds:16,kind:'app',clip:'04-review',start:10,end:26.5,crop:[.13,.2,.85,.76],label:'Prepared extraction · approved client file',replacement:'case-001-review.mp4'},
  ]},
  {id:'matter',title:'Define the matter',shots:[
    {id:'matter-create',seconds:12,kind:'app',clip:'02-intake',start:0,end:18,crop:[.12,0,.88,1],label:'Recorded intake choices',replacement:'case-001-intake.mp4'},
    {id:'matter-scope',seconds:16,kind:'app',clip:'02-intake',start:18,end:43,crop:[.13,.16,.85,.78],label:'Scope and routing · recorded intake choices',replacement:'case-001-scope.mp4'},
    {id:'matter-attach',seconds:12,kind:'app',clip:'02-intake',start:49.7,end:59.5,label:'Attach the evidence · recorded intake choices',replacement:'case-001-attach.mp4'},
  ]},
  {id:'verify',title:'Inspect and confirm',shots:[
    {id:'processing',seconds:16,kind:'app',clip:'03-process',start:0,end:18,label:'Prepared extraction results · approved client file',replacement:'case-001-process.mp4'},
    {id:'review-type',seconds:15,kind:'app',clip:'04-review',start:0,end:12,crop:[.13,.2,.85,.76],label:'Document type and pages · prepared extraction',replacement:'case-001-review.mp4'},
    {id:'review-decision',seconds:19,kind:'app',clip:'04-review',start:12,end:27.5,crop:[.13,.28,.85,.7],label:'Proposed value → lawyer review · prepared extraction',replacement:'case-001-review.mp4'},
    {id:'reviewed-facts',seconds:10,kind:'app',clip:'05-facts',start:13.5,end:21.2,crop:[.13,.24,.85,.73],label:'Saved facts · recorded approved client file',replacement:'case-001-facts.mp4'},
    {id:'review-source-again',seconds:10,kind:'source',source:'title',headline:'Reopen the evidence. Read the extent again.'},
  ]},
  {id:'difference',title:'Investigate the question',shots:[
    {id:'extent-question',seconds:16,kind:'question'},
    {id:'extent-source-inspection',seconds:12,kind:'manual'},
    {id:'implemented-checks',seconds:17,kind:'app',crop:[.13,.2,.85,.76],label:'Investigate the matter’s review state',replacement:'case-001-checks.mp4'},
    {id:'question-left-open',seconds:10,kind:'research',mode:'question',headline:'What does each record describe?'},
  ]},
  {id:'instrument',title:'The working instrument',shots:[
    {id:'open-working-draft',seconds:19,kind:'app',clip:'10-draft',start:0,end:24,crop:[.13,.2,.85,.76],label:'Working draft · approved client file · template unvalidated',replacement:'case-001-draft.mp4'},
    {id:'confirm-draft-fields',seconds:12,kind:'app',clip:'11-draft-confirm-a',start:0,end:6.4,crop:[.13,.25,.85,.72],label:'Confirm populated fields · approved client file',replacement:'case-001-draft-confirm.mp4'},
    {id:'inspect-draft-field',seconds:10,kind:'app',clip:'12-draft-confirm-b',start:0,end:6.4,crop:[.13,.25,.85,.72],label:'Working draft · approved client file',replacement:'case-001-draft-field.mp4'},
    {id:'return-to-supplied-instrument',seconds:14,kind:'source',source:'instrument',headline:'0.0159 hectares, on the supplied instrument.',label:'Supplied source record. This is not a generated Draftly draft.'},
  ]},
  {id:'status',title:'The review record',shots:[
    {id:'preflight',seconds:22,kind:'app',crop:[.13,.18,.85,.78],label:'Inspect the current review state',replacement:'case-001-preflight.mp4'},
    {id:'internal-manifest',seconds:10,kind:'app',clip:'15-export',start:2,end:8,crop:[.13,.18,.85,.78],label:'Internal manifest. Filing remains with the practitioner.',replacement:'case-001-manifest.mp4'},
    {id:'review-record',seconds:8,kind:'app',clip:'15-export',start:30,end:48.8,label:'Recorded review state. No successful registration is claimed.',replacement:'case-001-review-record.mp4'},
  ]},
  {id:'research',title:'From the matter to supporting law',shots:[
    {id:'matter-question',seconds:14,kind:'research',mode:'matter',replacement:'matter-conversation.mp4'},
    {id:'enter-research',seconds:14,kind:'app',clip:'18-research-scope',start:0,end:11.6,label:'Dedicated Research workspace · source-scope controls',replacement:'case-001-research-scope.mp4'},
    {id:'legal-catalogue',seconds:16,kind:'app',clip:'17-legal-sources',start:0,end:16.3,crop:[.13,.1,.85,.82],label:'Counts visible in this recording: 57 statutes · 18 amendments',replacement:'case-001-legal-sources.mp4'},
    {id:'research-question-answer',seconds:24,kind:'research',mode:'citation',replacement:'research-answer-current.mp4'},
    {id:'unverified-case-lead',seconds:16,kind:'research',mode:'case',replacement:'case-law-live.mp4'},
    {id:'evaluate-retrieval',seconds:26,kind:'research',mode:'evaluation'},
    {id:'planned-date-inspection',seconds:20,kind:'planned'},
  ]},
  {id:'closing',title:'Return to the file',shots:[
    {id:'source-return',seconds:12,kind:'source',source:'title',headline:'The original evidence remains available.'},
    {id:'instrument-return',seconds:10,kind:'source',source:'instrument',headline:'A working instrument still needs review.'},
    {id:'close-the-file',seconds:23,kind:'closing'},
  ]},
];
export const TOTAL_SECONDS=EDIT.reduce((n,c)=>n+c.shots.reduce((s,shot)=>s+shot.seconds,0),0);
export const ALL_SHOTS=EDIT.flatMap(c=>c.shots);
