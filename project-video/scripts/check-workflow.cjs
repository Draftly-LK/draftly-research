const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const required=[
 'brand/logo-mark-white.png','brand/plex-latin.woff2',
 'sound/folder.wav','sound/page.wav','sound/pen.wav','sound/click.wav','sound/score.wav',
 'people/anura-dhanaratna.jpeg','people/aruni-gunarathna.jpeg','people/priyal-wijayaweera.jpeg','people/ishan-rathnapala.jpeg',
 'evidence/title.png','evidence/survey.png','evidence/identity.png','evidence/instrument.png',
 'evidence/title-extent.png','evidence/instrument-extent.png','evidence/survey-extent.png',
 'footage/case-001-reopen.mp4','footage/case-001-process.mp4','footage/case-001-accept-facts.mp4','footage/case-001-draft-current.mp4',
 'footage/17-legal-sources.mp4','footage/18-research-scope.mp4','footage/19-citation.mp4',
];
const missing=required.filter(file=>!fs.existsSync(path.join(root,'public',file)));
if(missing.length){console.error('Workflow film cannot render; missing local assets:\n'+missing.join('\n'));process.exit(1);}
console.log(`Workflow film: ${required.length} required local assets present.`);
