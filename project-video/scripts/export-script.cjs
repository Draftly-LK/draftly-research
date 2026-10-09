// Export the active visual edit, without narration or guessed captions.
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

const root = path.resolve(__dirname, "..");
const src = fs.readFileSync(path.join(root, "src", "film", "edit.ts"), "utf8");
const js = ts.transpileModule(src, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;
const mod = { exports: {} };
new Function("module", "exports", js)(mod, mod.exports);
const { EDIT } = mod.exports;

const fmt = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
let t = 0;
const out = [
  "# Draftly film: visual script",
  "",
  "Generated from `src/film/edit.ts`. Edit the shots there, then run",
  "`node scripts/export-script.cjs` to refresh this sheet.",
  "",
  "One property transfer. Follow the evidence. This version uses sound and",
  "music, with no voiceover or speech captions, as requested. Client source",
  "display copies are unmasked with owner approval; originals stay unchanged.",
  "",
];
for (const chapter of EDIT) {
  const seconds=chapter.shots.reduce((n,s)=>n+s.seconds,0);
  out.push(`## ${fmt(t)}–${fmt(t+seconds)} · ${chapter.title}`, "");
  for(const shot of chapter.shots){
    out.push(`- ${fmt(t)} · ${shot.id} (${shot.seconds}s): ${shot.headline??shot.label??shot.kind}.`);
    t+=shot.seconds;
  }
  out.push("");
}
out.push(`Total: ${fmt(t)}`, "");
fs.writeFileSync(path.join(root, "SCRIPT.md"), out.join("\n"));
console.log("SCRIPT.md written,", fmt(t));
