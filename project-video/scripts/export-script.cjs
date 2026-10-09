// Writes SCRIPT.md (the narration sheet) from src/script.ts.
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

const root = path.resolve(__dirname, "..");
const src = fs.readFileSync(path.join(root, "src", "script.ts"), "utf8");
const js = ts.transpileModule(src, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } }).outputText;
const mod = { exports: {} };
new Function("module", "exports", js)(mod, mod.exports);
const { SCRIPT } = mod.exports;

const fmt = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
let t = 0;
const out = [
  "# Draftly demo video: narration sheet",
  "",
  "Generated from `src/script.ts`. Edit the lines there, then run",
  "`node scripts/export-script.cjs` to refresh this sheet.",
  "",
  "Read at a calm pace (about 140 words a minute). Record each section as its",
  "own audio file, named as shown, into `public/audio/`, then list it in",
  "`src/media.ts`.",
  "",
];
for (const s of SCRIPT) {
  const words = s.lines.join(" ").split(/\s+/).length;
  out.push(`## ${fmt(t)}–${fmt(t + s.seconds)} · ${s.title}`, "");
  out.push(`- On-screen text: “${s.onScreen}”`);
  out.push(`- Length: ${s.seconds} s (${words} words)`);
  out.push(`- Audio file: \`public/audio/${s.id}.mp3\``, "");
  for (const l of s.lines) out.push(`> ${l}`, ">");
  out.pop();
  out.push("");
  t += s.seconds;
}
out.push(`Total: ${fmt(t)}`, "");
fs.writeFileSync(path.join(root, "SCRIPT.md"), out.join("\n"));
console.log("SCRIPT.md written,", fmt(t));
