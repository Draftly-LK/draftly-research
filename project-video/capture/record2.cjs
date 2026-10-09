// Extra scenes for the updated script: Legal sources, research scope, opening a citation.
const path = require("node:path");
const { chromium } = require("C:/Users/ASUS/Desktop/desp-web/frontend/node_modules/@playwright/test");
const { Recorder } = require("./lib.cjs");
const APP = "http://localhost:4310";
(async () => {
  const browser = await chromium.launch({ channel: "chromium" });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.setDefaultTimeout(30000);
  const rec = new Recorder(page); await rec.init();
  const ready = async (url, loc) => { await page.goto(url, { waitUntil: "load", timeout: 120000 }); await loc.waitFor({ timeout: 120000 }); await page.waitForTimeout(1500); };

  await ready(APP + "/library", page.getByText("75 sources"));
  await rec.start("17-legal-sources");
  await rec.hold(1500);
  await rec.moveTo(page.getByText("All sources", { exact: true }).first(), { pause: 1800 });
  await rec.moveTo(page.getByText("Statutes", { exact: true }).first(), { pause: 1500 });
  await rec.moveTo(page.getByText("Amendments", { exact: true }).first(), { pause: 1500 });
  await rec.type(page.getByRole("textbox", { name: "Search legal sources" }), "Registration of Title", { delay: 60 });
  await rec.hold(2500);
  await rec.scroll(250, { steps: 15 });
  await rec.hold(1500);
  await rec.stop();

  await ready(APP + "/research", page.getByRole("button", { name: "New conversation" }));
  await rec.start("18-research-scope");
  await rec.hold(800);
  await rec.click(page.getByRole("button", { name: "New conversation" }), { after: 1000 });
  await rec.click(page.getByRole("button", { name: "All sources", exact: true }), { after: 1600 });
  await rec.click(page.getByRole("button", { name: "Statutes & amendments" }), { after: 1600 });
  await rec.click(page.getByRole("button", { name: "Case law", exact: true }), { after: 1600 });
  await rec.click(page.getByRole("button", { name: "Statutes & amendments" }), { after: 1500 });
  await rec.stop();

  await rec.start("19-citation");
  await rec.hold(500);
  await rec.type(page.getByRole("textbox", { name: "Ask a legal research question" }), "What is registration of title?", { delay: 55 });
  await rec.click(page.getByRole("button", { name: "Send" }), { after: 300 });
  await page.getByRole("heading", { name: "Sources used" }).last().waitFor({ timeout: 150000 });
  await rec.hold(2500);
  await rec.scroll(600, { steps: 30 });
  await rec.hold(1200);
  const first = page.locator("summary").filter({ hasText: /Registration of Title Act/ }).first();
  await rec.click(first, { after: 600 });
  await rec.hold(4500);
  const second = page.locator("summary").filter({ hasText: /Registration of Title Act/ }).nth(1);
  if (await second.count()) { await rec.click(second, { after: 600 }); await rec.hold(3500); }
  await rec.stop();
  await browser.close();
  console.log("done");
})().catch((e) => { console.error("FAILED:", e.message); process.exit(1); });
