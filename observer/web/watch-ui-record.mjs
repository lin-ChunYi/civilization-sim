#!/usr/bin/env node
/** Real-UI watch tour recording. CDP mouse only. */
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync, rmSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as sleep } from "node:timers/promises";

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (name, def) => { const i = args.indexOf("--" + name); return i >= 0 ? args[i + 1] : def; };
const BASE = (flag("base-url", "http://127.0.0.1:8918") || "").replace(/\/$/, "");
const ART = flag("artifact-dir", join(here, "screenshots", "watch-record"));
const USER = flag("user-data-dir", "/tmp/g-watch-record");
const CDP = Number(flag("cdp-port", "9435"));
const PAGE = BASE + "/?v=w2#tab=world&run=preset-anime-farm250&t=0";
const chromeCands = [
  process.env.CHROME,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium-browser",
].filter(Boolean);
const CHROME = chromeCands.find((p) => existsSync(p));
if (!CHROME) { process.stdout.write("no chrome\n"); process.exit(2); }
const FRAMES = join(ART, "rec-frames");
mkdirSync(ART, { recursive: true });
mkdirSync(USER, { recursive: true });
rmSync(FRAMES, { recursive: true, force: true });
mkdirSync(FRAMES, { recursive: true });

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

let seq = 0, ackId = 200000, n = 0, ws;
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
      frames.push({ n, file: name, wallMs: wall, elapsedMs: wall - t0, sessionId: msg.params.sessionId });
      ws.send(JSON.stringify({ id: ++ackId, method: "Page.screencastFrameAck", params: { sessionId: msg.params.sessionId } }));
    }
  });
  await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
  const send = (method, params = {}) => {
    const id = ++seq;
    return new Promise((res) => { pending.set(id, res); ws.send(JSON.stringify({ id, method, params })); });
  };
  const inspect = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
    return r.result && r.result.result ? r.result.result.value : null;
  };
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1536, height: 1024, deviceScaleFactor: 1, mobile: false });
  for (let i = 0; i < 25; i++) {
    await sleep(400);
    if (await inspect("!!document.getElementById('an-watch-start') && document.querySelector('#map .an-chibi')")) break;
  }
  const boxOf = async (sel) => inspect(`(function(){
    var n=document.querySelector(${JSON.stringify(sel)});
    if(!n) return null; n.scrollIntoView({block:'nearest'});
    var r=n.getBoundingClientRect();
    if(r.width<2||r.height<2) return null;
    return {x:r.x+r.width/2,y:r.y+r.height/2};
  })()`);
  const clickSel = async (sel, note) => {
    for (let i = 0; i < 8; i++) {
      const dbg = await inspect(`(function(){
        var n=document.querySelector(${JSON.stringify(sel)});
        var bar=document.getElementById('an-watch-bar');
        var st=window.WatchPlayer && window.WatchPlayer.state();
        if(!n) return {ok:false, why:'missing', active:st&&st.active, hidden:bar&&bar.hidden};
        n.scrollIntoView({block:'nearest'});
        var r=n.getBoundingClientRect();
        return {ok:r.width>=2&&r.height>=2, x:r.x+r.width/2, y:r.y+r.height/2, w:r.width, h:r.height, top:r.top, hidden:bar&&bar.hidden, active:st&&st.active, kind:st&&st.chapter&&st.chapter.kind};
      })()`);
      if (dbg && dbg.ok) {
        await send("Input.dispatchMouseEvent", { type: "mousePressed", x: dbg.x, y: dbg.y, button: "left", clickCount: 1, buttons: 1 });
        await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: dbg.x, y: dbg.y, button: "left", clickCount: 1, buttons: 0 });
        logAct("click", { sel, note, x: dbg.x, y: dbg.y });
        return true;
      }
      logAct("click-wait", { sel, note, attempt: i, dbg });
      await sleep(400);
    }
    logAct("click-miss", { sel, note });
    return false;
  };
  await send("Page.startScreencast", { format: "jpeg", quality: 70, everyNthFrame: 1, maxWidth: 1280, maxHeight: 848 });
  const recStart = Date.now();
  logAct("screencast-start", { wall: recStart });
  await sleep(2500);
  if (!await clickSel("#an-watch-start", "start tour")) throw new Error("start");
  await sleep(5000);
  if (!await clickSel("#an-watch-pause", "pause")) throw new Error("pause");
  await sleep(2000);
  if (!await clickSel("#an-watch-pause", "resume")) throw new Error("resume");
  await sleep(1500);
  for (let i = 0; i < 6; i++) {
    if (!await clickSel("#an-watch-next", "next " + i)) break;
    await sleep(4500);
    const st = await inspect("window.WatchPlayer && window.WatchPlayer.state()");
    logAct("observe", { chapter: st && st.chapter, copy: await inspect("document.getElementById('an-watch-copy')&&document.getElementById('an-watch-copy').textContent") });
    if (st && st.chapter && st.chapter.kind === "migrate") {
      const gap = await inspect("document.getElementById('an-watch-gap')&&document.getElementById('an-watch-gap').textContent");
      logAct("gap", { gap });
    }
    if (st && st.chapter && st.chapter.kind === "final") break;
  }
  await clickSel("#an-watch-pause", "hold final");
  await sleep(800);
  if (!await clickSel("#an-watch-source", "source")) logAct("source-optional", {});
  await sleep(2000);
  if (!await clickSel("#an-watch-exit", "exit free observe")) throw new Error("exit");
  await sleep(4000);
  await send("Page.stopScreencast");
  await sleep(300);
  if (ws) ws.close();
  const recEnd = frames.length ? frames[frames.length - 1].wallMs : Date.now();
  const wallSpanMs = frames.length ? (frames[frames.length - 1].wallMs - frames[0].wallMs) : 0;
  const concat = join(FRAMES, "concat.txt");
  let txt = "ffconcat version 1.0\n";
  let sumDur = 0;
  for (let i = 0; i < frames.length; i++) {
    let durMs = i + 1 < frames.length ? (frames[i + 1].wallMs - frames[i].wallMs) : 1;
    if (durMs < 1) durMs = 1;
    const dur = durMs / 1000;
    frames[i].durationSec = dur;
    sumDur += dur;
    txt += "file '" + join(FRAMES, frames[i].file).replace(/'/g, "'\\''") + "'\n";
    txt += "duration " + dur.toFixed(6) + "\n";
  }
  if (frames.length) txt += "file '" + join(FRAMES, frames[frames.length - 1].file).replace(/'/g, "'\\''") + "'\n";
  writeFileSync(concat, txt);
  const mp4 = join(ART, "G_WATCH_PLAY_01.mp4");
  const ff = spawnSync("ffmpeg", [
    "-y", "-f", "concat", "-safe", "0", "-i", concat,
    "-fps_mode", "vfr", "-video_track_timescale", "1000",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4,
  ], { encoding: "utf8" });
  const probe = spawnSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", mp4], { encoding: "utf8" });
  const fileDuration = parseFloat(String(probe.stdout || "").trim());
  const log = {
    url: PAGE, startedAt: new Date(frames[0] ? frames[0].wallMs : recStart).toISOString(),
    endedAt: new Date(recEnd).toISOString(), elapsedMs: recEnd - recStart,
    frameCount: frames.length, wallSpanMs, concatSumDurationSec: sumDur,
    fileDurationSec: fileDuration, durationDriftSec: fileDuration - wallSpanMs / 1000,
    ffmpegStatus: ff.status, actions,
  };
  writeFileSync(join(ART, "recording-log.json"), JSON.stringify(log, null, 2));
  process.stdout.write("elapsedMs=" + log.elapsedMs + " wallSpanMs=" + wallSpanMs +
    " ffprobe=" + fileDuration + " drift=" + (log.durationDriftSec).toFixed(3) + " frames=" + frames.length + "\n");
  if (ff.status !== 0) process.exit(1);
} catch (e) {
  process.stdout.write("RECORD FAIL " + (e && e.stack ? e.stack : e) + "\n");
  process.exit(1);
} finally {
  try { chrome.kill("SIGKILL"); } catch (e) {}
}
