const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const shots = JSON.parse(fs.readFileSync(path.join(root, 'src/long-film/edit.json'), 'utf8'));
const required = new Set([
  'brand/logo-mark-black.png', 'brand/logo-mark-white.png', 'brand/plex-latin.woff2',
  'sound/score.wav', 'sound/page.wav', 'sound/click.wav', 'sound/pen.wav', 'sound/folder.wav',
  'evidence/title.png', 'evidence/instrument.png', 'evidence/survey.png', 'evidence/identity.png',
  'evidence/title-extent.png', 'evidence/instrument-extent.png', 'evidence/survey-extent.png',
  'people/anura-dhanaratna.jpeg', 'people/aruni-gunarathna.jpeg',
  'people/priyal-wijayaweera.jpeg', 'people/ishan-rathnapala.jpeg',
  'research/paper-title.png',
]);
let frame = 0;
for (const shot of shots) {
  if (shot.from * 30 !== frame) throw new Error(`Timeline gap or overlap at ${shot.id}`);
  if (!(shot.seconds > 0)) throw new Error(`Invalid duration: ${shot.id}`);
  if (/synthetic|sythatic|placeholder/i.test([shot.headline, shot.note, shot.detail].join(' '))) {
    throw new Error(`Unapproved visible label: ${shot.id}`);
  }
  frame += shot.seconds * 30;
  if (shot.file) required.add(shot.file);
  if (shot.source) required.add(shot.source.includes('/') ? shot.source : `evidence/${shot.source}.png`);
}
if (frame !== 18000) throw new Error(`Expected 18000 frames, got ${frame}`);
const missing = [...required].filter(file => !fs.existsSync(path.join(root, 'public', file)));
if (missing.length) throw new Error(`Missing assets:\n${missing.join('\n')}`);
if (!fs.existsSync(path.join(root, 'out/draftly-opening.mp4'))) throw new Error('The fast exporter needs out/draftly-opening.mp4');
console.log(`Full film: ${shots.length} shots, 600 seconds, ${required.size} local assets present.`);
