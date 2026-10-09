// Capture helpers: CDP screencast to JPEG frames, encoded to H.264 with
// Remotion's bundled ffmpeg; a drawn cursor; smooth, readable interactions.
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const ROOT = path.resolve(__dirname, "..");
const FRAMES = path.join(__dirname, "frames");
const OUT = path.join(ROOT, "public", "footage");
fs.mkdirSync(OUT, { recursive: true });

const FFMPEG = (() => {
  const dir = path.join(ROOT, "node_modules", "@remotion");
  for (const d of fs.readdirSync(dir)) {
    const p = path.join(dir, d, "ffmpeg.exe");
    if (d.startsWith("compositor-") && fs.existsSync(p)) return p;
  }
  throw new Error("Remotion ffmpeg not found");
})();

// A cursor and click ripple drawn into the page, since headless has none.
const CURSOR_SCRIPT = `
(() => {
  const install = () => {
    if (document.getElementById("__cap_cursor")) return;
    const style = document.createElement("style");
    style.textContent = \`
      nextjs-portal, [data-nextjs-toast], #__next-build-watcher { display: none !important; }
      #__cap_cursor { position: fixed; z-index: 2147483647; pointer-events: none; width: 26px; height: 26px;
        left: 0; top: 0; transform: translate(-3px, -2px); transition: none; }
      .__cap_ripple { position: fixed; z-index: 2147483646; pointer-events: none; width: 40px; height: 40px;
        margin: -20px 0 0 -20px; border-radius: 50%; border: 3px solid rgba(198,148,54,.95);
        animation: __cap_r .55s ease-out forwards; }
      @keyframes __cap_r { from { transform: scale(.3); opacity: 1 } to { transform: scale(1.4); opacity: 0 } }
    \`;
    document.head.appendChild(style);
    const c = document.createElement("div");
    c.id = "__cap_cursor";
    c.innerHTML = '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M3 2l7.5 19 2.6-8.1L21 10.3z" fill="#0F1F38" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    const pos = window.__cap_pos || { x: -50, y: -50 };
    c.style.left = pos.x + "px"; c.style.top = pos.y + "px";
    document.body.appendChild(c);
    document.addEventListener("mousemove", (e) => {
      window.__cap_pos = { x: e.clientX, y: e.clientY };
      c.style.left = e.clientX + "px"; c.style.top = e.clientY + "px";
    }, true);
    document.addEventListener("mousedown", (e) => {
      const r = document.createElement("div");
      r.className = "__cap_ripple"; r.style.left = e.clientX + "px"; r.style.top = e.clientY + "px";
      document.body.appendChild(r); setTimeout(() => r.remove(), 600);
    }, true);
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install);
  else install();
})();
`;

class Recorder {
  constructor(page) {
    this.page = page;
    this.session = null;
    this.clip = null;
    this.mouse = { x: 960, y: 540 };
  }

  async init() {
    await this.page.addInitScript(CURSOR_SCRIPT);
    this.session = await this.page.context().newCDPSession(this.page);
    this.session.on("Page.screencastFrame", (f) => {
      // Ack first so Chrome can produce the next frame while this one is written.
      this.session.send("Page.screencastFrameAck", { sessionId: f.sessionId }).catch(() => {});
      if (this.clip) {
        const n = this.clip.frames.length;
        const file = path.join(this.clip.dir, String(n).padStart(6, "0") + ".jpg");
        this.clip.frames.push({ file, t: f.metadata.timestamp });
        fs.writeFile(file, Buffer.from(f.data, "base64"), () => {});
      }
    });
  }

  async start(name) {
    const dir = path.join(FRAMES, name);
    if (!dir.startsWith(path.resolve(FRAMES) + path.sep)) throw new Error('Capture path outside frames workspace');
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    this.clip = { name, dir, frames: [], startedAt: Date.now() / 1000 };
    // Re-assert the cursor position after any navigation.
    await this.page.mouse.move(this.mouse.x, this.mouse.y);
    await this.session.send("Page.startScreencast", {
      format: "jpeg", quality: 92, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1,
    });
    console.log(`[clip] start ${name}`);
  }

  async stop() {
    if (!this.clip) return;
    await this.page.waitForTimeout(400);
    await this.session.send("Page.stopScreencast");
    await new Promise((r) => setTimeout(r, 500)); // let pending frame writes land
    const clip = this.clip;
    this.clip = null;
    const end = Date.now() / 1000;
    if (clip.frames.length === 0) { console.log(`[clip] ${clip.name}: no frames`); return; }
    // Concat list with real durations, so static stretches keep their time.
    const lines = ["ffconcat version 1.0"];
    clip.frames.forEach((fr, i) => {
      // CDP timestamps are seconds since the epoch, the same clock as `end`.
      const next = i + 1 < clip.frames.length ? clip.frames[i + 1].t : Math.max(fr.t + 0.04, end);
      const dur = Math.max(0.001, Math.min(next - fr.t, 30));
      lines.push(`file '${path.basename(fr.file)}'`, `duration ${dur.toFixed(4)}`);
    });
    lines.push(`file '${path.basename(clip.frames[clip.frames.length - 1].file)}'`);
    fs.writeFileSync(path.join(clip.dir, "list.txt"), lines.join("\n"));
    const out = path.join(OUT, `${clip.name}.mp4`);
    execFileSync(FFMPEG, [
      "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt",
      "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-r", "30", "-fps_mode", "cfr",
      "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-movflags", "+faststart", out,
    ], { cwd: clip.dir, stdio: "inherit" });
    const secs = clip.frames[clip.frames.length - 1].t - clip.frames[0].t;
    console.log(`[clip] saved ${clip.name}.mp4 (${clip.frames.length} frames, ~${secs.toFixed(1)}s)`);
  }

  // Interactions -----------------------------------------------------------
  async moveTo(locator, { steps = 28, pause = 250 } = {}) {
    await locator.scrollIntoViewIfNeeded();
    const box = await locator.boundingBox();
    if (!box) throw new Error("no bounding box");
    const x = box.x + box.width / 2;
    const y = box.y + box.height / 2;
    await this.page.mouse.move(x, y, { steps });
    this.mouse = { x, y };
    await this.page.waitForTimeout(pause);
  }

  async click(locator, opts = {}) {
    await this.moveTo(locator, opts);
    await locator.click();
    await this.page.waitForTimeout(opts.after ?? 600);
  }

  async type(locator, text, { delay = 55 } = {}) {
    await this.click(locator, { after: 200 });
    await locator.pressSequentially(text, { delay });
    await this.page.waitForTimeout(400);
  }

  async scroll(dy, { steps = 20, pause = 30 } = {}) {
    const per = dy / steps;
    for (let i = 0; i < steps; i++) {
      await this.page.mouse.wheel(0, per);
      await this.page.waitForTimeout(pause);
    }
    await this.page.waitForTimeout(300);
  }

  async hold(ms) { await this.page.waitForTimeout(ms); }
}

module.exports = { Recorder, FFMPEG, OUT };
