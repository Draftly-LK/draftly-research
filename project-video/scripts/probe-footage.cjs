// Writes src/footage.json: the length in seconds of every clip in public/footage.
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const dir = path.join(root, "public", "footage");
const probe = path.join(root, "node_modules", "@remotion", "compositor-win32-x64-msvc", "ffprobe.exe");
const out = {};
for (const f of fs.readdirSync(dir).filter((f) => f.endsWith(".mp4")).sort()) {
  const s = execFileSync(probe, ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path.join(dir, f)]).toString().trim();
  out[f.replace(/\.mp4$/, "")] = Math.floor(Number(s) * 10) / 10;
}
fs.writeFileSync(path.join(root, "src", "footage.json"), JSON.stringify(out, null, 2) + "\n");
console.log(out);
