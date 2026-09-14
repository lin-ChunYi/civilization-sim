#!/usr/bin/env node
/** Real-UI recording: CDP mouse/keyboard/slider only. No __obs controller calls. */
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as sleep } from "node:timers/promises";

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf("--" + name);
  return i >= 0 ? args[i + 1] : def;
};
const BASE = (flag("base-url", "http://127.0.0.1:8913") || "").replace(/\/$/, "");
const ART = flag("artifact-dir", join(here, "screenshots", "anime-record"));
const USER = flag("user-data-dir", "/tmp/g-anime-record");
const CDP = Number(flag("cdp-port", "9411"));
const PAGE = BASE + "/?v=f6#tab=world&run=preset-anime-farm250&t=0";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const FRAMES = join(ART, "rec-frames-real");
const SAMPLE = "preset-anime-farm250";
mkdirSync(ART, { recursive: true });
mkdirSync(USER, { recursive: true });
rmSync(FRAMES, { recursive: true, force: true });
mkdirSync(FRAMES, { recursive: true });

async function apiJson(path, opts) {
  const r = await fetch(BASE + path, opts);
  const t = await r.text();
  let j = null;
  try { j = JSON.parse(t); } catch (e) { j = { raw: t }; }
  if (!r.ok) throw new Error(path + " " + r.status + " " + t.slice(0, 240));
  return j;
}
async function waitRun(id, minYears) {
  let st = null;
  for (let i = 0; i < 90; i++) {
    st = await apiJson("/api/runs/" + id);
    if (st.status === "done" && (st.years_recorded || 0) >= minYears) return st;
    if (["failed", "canceled", "interrupted"].includes(st.status)) throw new Error("run " + id + " " + st.status);
    await sleep(1000);
  }
  throw new Error("timeout " + id);
}

process.stdout.write("prepare user parent via API\n");
const created = await apiJson("/api/runs", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({
    seed: 99, years: 3, sigma_m: 400, move_mort_m: 50,
    share_m: 1000, aid_m: 1000, recip_m: 1000, farm_m: 250,
    arm: "memory", engine: "exp07",
    label: "anime-ui-record-parent",
  }),
});
const parentId = created.run_id;
await waitRun(parentId, 3);
process.stdout.write("user parent " + parentId + " ready\n");

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--disable-http-cache",
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${USER}`,
  "--window-size=1536,1024", PAGE,
], { stdio: "ignore" });

const actions = [];
const frames = [];
const t0 = Date.now();
const logAct = (type, detail) => {
  const rec = { elapsedMs: Date.now() - t0, type, ...detail };
  actions.push(rec);
  process.stdout.write("ACT " + rec.elapsedMs + " " + type + " " + JSON.stringify(detail) + "\n");
};

let seq = 0;
let ackId = 200000;
let n = 0;
let ws;
try {
  await sleep(2800);
  const list = await fetch("http://127.0.0.1:" + CDP + "/json/list").then((r) => r.json());
  const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
  if (!page) throw new Error("no page");
  ws = new WebSocket(page.webSocketDebuggerUrl);
  const pending = new Map();
  ws.addEventListener("message", (e) => {
    const msg = JSON.parse(e.data);
    if (msg.id && pending.has(msg.id)) pending.get(msg.id)(msg);
    if (msg.method === "Page.screencastFrame" && msg.params && msg.params.data) {
      n += 1;
      const wall = Date.now();
      const name = String(n).padStart(5, "0") + ".jpg";
      writeFileSync(join(FRAMES, name), Buffer.from(msg.params.data, "base64"));
      frames.push({
        n, file: name, wallMs: wall, elapsedMs: wall - t0,
        cdpTimestamp: msg.params.timestamp, sessionId: msg.params.sessionId,
      });
      ws.send(JSON.stringify({
        id: ++ackId, method: "Page.screencastFrameAck",
        params: { sessionId: msg.params.sessionId },
      }));
    }
  });
  await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
  const send = (method, params = {}) => {
    const id = ++seq;
    return new Promise((res) => { pending.set(id, res); ws.send(JSON.stringify({ id, method, params })); });
  };
  const inspect = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1536, height: 1024, deviceScaleFactor: 1, mobile: false,
  });
  for (let i = 0; i < 25; i++) {
    await sleep(400);
    if (await inspect("!!document.querySelector('#map .an-chibi') && document.getElementById('an-play')")) break;
  }
  logAct("page-ready", { url: PAGE, parentId });

  const boxOf = async (sel) => inspect(`(function(){
    var n=document.querySelector(${JSON.stringify(sel)});
    if(!n) return null;
    n.scrollIntoView({block:'nearest'});
    var r=n.getBoundingClientRect();
    if(r.width<2 || r.height<2) return null;
    return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height,left:r.x,top:r.y};
  })()`);
  const clickAt = async (x, y) => {
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1, buttons: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1, buttons: 0 });
  };
  const clickSel = async (sel, note) => {
    const b = await boxOf(sel);
    if (!b || b.x == null) {
      logAct("click-miss", { sel, note });
      return false;
    }
    await clickAt(b.x, b.y);
    logAct("click", { sel, note, x: b.x, y: b.y });
    return true;
  };
  const key = async (name) => {
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: name, windowsVirtualKeyCode: name === "ArrowDown" ? 40 : (name === "ArrowUp" ? 38 : 13) });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: name, windowsVirtualKeyCode: name === "ArrowDown" ? 40 : (name === "ArrowUp" ? 38 : 13) });
  };
  const observe = async () => inspect(`(function(){
    return {
      year: document.getElementById('an-year') && document.getElementById('an-year').textContent,
      run: document.getElementById('an-run') && document.getElementById('an-run').value,
      eid: (document.getElementById('map-event-chip') && document.getElementById('map-event-chip').getAttribute('data-eid'))
        || (window.__obs && window.__obs.S && window.__obs.S.selEvent),
      badge: document.getElementById('an-badge') && document.getElementById('an-badge').textContent,
      continueReason: document.getElementById('continue-reason') && document.getElementById('continue-reason').textContent
    };
  })()`);
  const requireYear = async (want) => {
    const o = await observe();
    logAct("observe", { wantYear: want, observed: o });
    if (String(o && o.year) !== String(want)) throw new Error("year want " + want + " got " + (o && o.year));
  };
  const requireRun = async (id) => {
    const o = await observe();
    logAct("observe", { wantRun: id, observed: o });
    if ((o && o.run) !== id) throw new Error("run want " + id + " got " + (o && o.run));
  };
  const requireEvent = async (eid) => {
    const o = await observe();
    logAct("observe", { wantEid: eid, observed: o });
    if (String(o && o.eid) !== String(eid)) throw new Error("event want " + eid + " got " + (o && o.eid));
  };
  const waitYear = async (want, ms) => {
    const tEnd = Date.now() + ms;
    while (Date.now() < tEnd) {
      const y = await inspect("document.getElementById('an-year') && document.getElementById('an-year').textContent");
      if (String(y) === String(want)) return true;
      await sleep(200);
    }
    return false;
  };
  const scrubTo = async (year) => {
    const info = await inspect(`(function(){
      var n=document.getElementById('an-scrub');
      if(!n) return null;
      var r=n.getBoundingClientRect();
      var max=Math.max(1, +n.max || 300);
      var t=Math.max(0, Math.min(max, ${Number(year)}));
      return {x:r.x + (t/max)*Math.max(r.width-2,1), y:r.y+r.height/2, max:max, w:r.width, left:r.x};
    })()`);
    if (!info || info.x == null) throw new Error("scrub control missing for year " + year);
    let x = info.x;
    for (let attempt = 0; attempt < 6; attempt++) {
      await clickAt(x, info.y);
      logAct("scrub", { year, x, attempt });
      if (await waitYear(year, 2500)) { await requireYear(year); return; }
      const got = +(await inspect("document.getElementById('an-year') && document.getElementById('an-year').textContent"));
      if (got === year + 1 && await clickSel("#an-prev", "correct year-1")) {
        if (await waitYear(year, 2500)) { await requireYear(year); return; }
      }
      if (got === year - 1 && await clickSel("#an-next", "correct year+1")) {
        if (await waitYear(year, 2500)) { await requireYear(year); return; }
      }
      x += (got > year ? -8 : 8);
    }
    throw new Error("failed to reach year " + year + " via scrub");
  };
  const openFullList = async (note) => {
    if (!await clickSel("#an-ev-open", note || "view all")) throw new Error("view-all failed: " + note);
    await sleep(400);
    const filt = await inspect("document.getElementById('an-ev-filter') && document.getElementById('an-ev-filter').value");
    if (filt && filt !== "all") {
      const idx = await inspect("document.getElementById('an-ev-filter') && document.getElementById('an-ev-filter').selectedIndex");
      await clickSel("#an-ev-filter", "focus filter to 全部");
      for (let i = 0; i < (idx || 0); i++) await key("ArrowUp");
      logAct("key", { key: "ArrowUp", note: "reset filter to all" });
      await sleep(400);
    }
  };
  const clickEventId = async (eid, note) => {
    const compact = "#an-events .an-ev[data-eid=\"" + eid + "\"]";
    if (await boxOf(compact)) {
      if (!await clickSel(compact, note || eid)) throw new Error("event button missing " + eid);
    } else {
      await openFullList("view all for " + eid);
      const sel = "#an-ev-all .an-ev[data-eid=\"" + eid + "\"]";
      if (!await clickSel(sel, note || eid)) throw new Error("event button missing " + eid);
    }
    await sleep(600);
    await requireEvent(eid);
  };

  await send("Page.startScreencast", {
    format: "jpeg", quality: 70, everyNthFrame: 1, maxWidth: 1280, maxHeight: 848,
  });
  const recStart = Date.now();
  logAct("screencast-start", { wall: recStart, url: PAGE });

  await sleep(5000);
  await requireYear(0);
  if (!await clickSel("#an-play", "play")) throw new Error("play button failed");
  await sleep(32000);
  if (!await clickSel("#an-play", "pause")) throw new Error("pause button failed");
  await sleep(1000);
  await scrubTo(0);
  await requireYear(0);

  if (!await clickSel("#an-next", "next to year 1")) throw new Error("next failed");
  if (!await waitYear(1, 6000)) throw new Error("did not reach year 1");
  await requireYear(1);
  await sleep(2000);
  await openFullList("view all at year 1");
  if (!await clickSel("#an-ev-all .an-ev-src summary", "open 来源")) throw new Error("source summary failed");
  await sleep(8000);
  if (!await clickSel("#an-ev-close", "close view all")) throw new Error("close view-all failed");
  await sleep(1000);
  if (!await clickSel("#an-next", "next to year 2 harvest")) throw new Error("next2 failed");
  if (!await waitYear(2, 6000)) throw new Error("did not reach year 2");
  await requireYear(2);
  await clickEventId("t2-farm_harvest-0", "year-2 harvest");
  await sleep(12000);

  const chibi = await boxOf("#map .an-chibi .an-chibi-zoom") || await boxOf("#map .an-chibi");
  if (chibi && chibi.x != null) {
    await clickAt(chibi.x, chibi.y);
    logAct("click", { sel: "#map .an-chibi", note: "select group representative" });
  } else throw new Error("no chibi to click");
  await sleep(6000);

  await scrubTo(52);
  await requireYear(52);
  await openFullList("view all at year 52");
  await sleep(12000);
  if (!await clickSel("#an-ev-close", "close view all")) throw new Error("close view-all failed");

  await scrubTo(218);
  await requireYear(218);
  await clickEventId("t218-migrate-1", "migrate t218-migrate-1");
  await sleep(20000);

  await scrubTo(267);
  await requireYear(267);
  await clickEventId("t267-aid-4", "aid t267-aid-4");
  await sleep(20000);

  await scrubTo(0);
  await requireYear(0);
  if (!await clickSel('.an-nav button[data-tab="network"]', "People tab")) throw new Error("people nav failed");
  await sleep(7000);
  if (!await clickSel("#net-svg .net-node", "select band in People")) throw new Error("people node failed");
  await sleep(7000);

  if (!await clickSel("#an-continue", "continue on sample")) throw new Error("continue button failed");
  await sleep(8000);
  const reason = await inspect("document.getElementById('continue-reason') && document.getElementById('continue-reason').textContent");
  logAct("observe", { want: "missing_checkpoint", continueReason: reason });
  if (!reason || String(reason).indexOf("missing_checkpoint") < 0) throw new Error("sample continue want missing_checkpoint got " + reason);
  if (!await clickSel("#b-continue-cancel", "cancel sample continue")) throw new Error("continue cancel failed");
  await sleep(1500);

  if (!await clickSel('.an-nav button[data-tab="runs"]', "open 创建世界")) throw new Error("runs tab failed");
  await sleep(1500);
  if (!await clickSel('[data-open="' + parentId + '"]', "open user parent from list")) throw new Error("user run row failed");
  await sleep(4000);
  await requireRun(parentId);
  const badge = await inspect("document.getElementById('an-badge') && document.getElementById('an-badge').textContent");
  logAct("observe", { badge, want: "not sample" });
  if (badge && /示例世界/.test(badge)) throw new Error("user run still showing sample badge: " + badge);

  if (!await clickSel("#an-continue", "continue on user run")) throw new Error("user continue button failed");
  await sleep(8000);
  const reason2 = await inspect("document.getElementById('continue-reason') && document.getElementById('continue-reason').textContent");
  logAct("observe", { want: "eligible ready", continueReason: reason2 });
  if (!reason2 || /missing_checkpoint/.test(reason2) || !/继续/.test(reason2)) {
    throw new Error("user continue not eligible, got " + reason2);
  }
  if (!await clickSel("#b-continue-cancel", "cancel user continue")) throw new Error("user continue cancel failed");
  await sleep(8000);

  await send("Page.stopScreencast");
  await sleep(400);
  const recEnd = Date.now();
  logAct("screencast-stop", { wall: recEnd, elapsedMs: recEnd - recStart, frames: n });

  const concat = join(FRAMES, "concat.txt");
  let txt = "ffconcat version 1.0\n";
  for (let i = 0; i < frames.length; i++) {
    const dur = i + 1 < frames.length
      ? Math.max(0.04, (frames[i + 1].wallMs - frames[i].wallMs) / 1000)
      : 0.2;
    frames[i].durationSec = dur;
    txt += "file '" + join(FRAMES, frames[i].file).replace(/'/g, "'\\''") + "'\n";
    txt += "duration " + dur.toFixed(4) + "\n";
  }
  if (frames.length) txt += "file '" + join(FRAMES, frames[frames.length - 1].file).replace(/'/g, "'\\''") + "'\n";
  writeFileSync(concat, txt);
  const mp4 = join(ART, "G_ANIME_01_FINISH_01.mp4");
  const ff = spawnSync("ffmpeg", [
    "-y", "-f", "concat", "-safe", "0", "-i", concat,
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4,
  ], { encoding: "utf8" });
  const probe = spawnSync("ffprobe", [
    "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", mp4,
  ], { encoding: "utf8" });
  const fileDuration = parseFloat(String(probe.stdout || "").trim());
  const firstTs = frames[0] ? frames[0].cdpTimestamp : null;
  const lastTs = frames.length ? frames[frames.length - 1].cdpTimestamp : null;
  const cdpSpan = (firstTs != null && lastTs != null) ? (lastTs - firstTs) : null;
  const log = {
    url: PAGE,
    parent_run_id: parentId,
    startedAt: new Date(recStart).toISOString(),
    endedAt: new Date(recEnd).toISOString(),
    elapsedMs: recEnd - recStart,
    frameCount: frames.length,
    cdpTimestampSpanSec: cdpSpan,
    wallSpanMs: frames.length ? (frames[frames.length - 1].wallMs - frames[0].wallMs) : null,
    fileDurationSec: fileDuration,
    ffmpegStatus: ff.status,
    actions,
    frames: frames.map((f) => ({
      n: f.n, file: f.file, elapsedMs: f.elapsedMs, wallMs: f.wallMs,
      cdpTimestamp: f.cdpTimestamp, durationSec: f.durationSec,
    })),
  };
  writeFileSync(join(ART, "recording-log.json"), JSON.stringify(log, null, 2));
  process.stdout.write("elapsedMs=" + log.elapsedMs + " fileDuration=" + fileDuration + " frames=" + frames.length + "\n");
  if (ff.status !== 0) process.stdout.write((ff.stderr || "").slice(-800) + "\n");
  if (ws) ws.close();
  if (ff.status !== 0 || frames.length < 80 || !(fileDuration >= 180)) {
    process.stdout.write("duration too short or encode failed\n");
    process.exit(1);
  }
} catch (e) {
  process.stdout.write("RECORD FAIL " + (e && e.stack ? e.stack : e) + "\n");
  process.exit(1);
} finally {
  try { chrome.kill("SIGKILL"); } catch (e) {}
}
