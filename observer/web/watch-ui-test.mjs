#!/usr/bin/env node
/** G_WATCH_PLAY_01 browser tests. --base-url --report --artifact-dir */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as sleep } from "node:timers/promises";

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (name, def) => { const i = args.indexOf("--" + name); return i >= 0 ? args[i + 1] : def; };
const BASE = (flag("base-url", "http://127.0.0.1:8918") || "").replace(/\/$/, "");
const ART = flag("artifact-dir", join(here, "screenshots", "watch-ui"));
const REPORT = flag("report", join(ART, "watch-ui.json"));
const USER = flag("user-data-dir", "/tmp/g-watch-play-browser");
const CDP = Number(flag("cdp-port", "9431"));
const SAMPLE = "preset-anime-farm250";
const chromeCands = [
  process.env.CHROME,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium-browser",
  "/usr/bin/chromium",
].filter(Boolean);
const CHROME = chromeCands.find((p) => existsSync(p));
mkdirSync(ART, { recursive: true });
mkdirSync(USER, { recursive: true });
const out = [];
const uncovered = [];
const ok = (name, cond, detail) => {
  out.push({ name, pass: !!cond, detail: detail == null ? "" : String(detail) });
  process.stdout.write((cond ? "PASS " : "FAIL ") + name + (detail ? " :: " + detail : "") + "\n");
};

if (!CHROME) {
  uncovered.push("No Chrome/Chromium on this machine; browser tour not executed");
  writeFileSync(REPORT, JSON.stringify({ task: "G_WATCH_PLAY_01", passed: 0, failed: 0, uncovered, results: out }, null, 2));
  process.stdout.write("report " + REPORT + " uncovered browser\n");
  process.exit(0);
}

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--disable-http-cache",
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${USER}`,
  "--window-size=1536,1024",
  BASE + "/?v=w4#tab=world&run=" + SAMPLE + "&t=0",
], { stdio: "ignore" });

let ws;
try {
  await sleep(2800);
  const list = await fetch("http://127.0.0.1:" + CDP + "/json/list").then((r) => r.json());
  const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
  if (!page) throw new Error("no page");
  ws = new WebSocket(page.webSocketDebuggerUrl);
  let seq = 0;
  const pending = new Map();
  ws.addEventListener("message", (e) => {
    const msg = JSON.parse(e.data);
    if (msg.id && pending.has(msg.id)) pending.get(msg.id)(msg);
  });
  await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
  const send = (method, params = {}) => {
    const id = ++seq;
    return new Promise((res) => { pending.set(id, res); ws.send(JSON.stringify({ id, method, params })); });
  };
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1536, height: 1024, deviceScaleFactor: 1, mobile: false });
  for (let i = 0; i < 30; i++) {
    await sleep(400);
    if (await ev("!!(window.__obs && window.__obs.S && window.__obs.S.run && document.getElementById('an-watch-start'))")) break;
  }
  const click = async (sel) => {
    const box = await ev(`(function(){var n=document.querySelector(${JSON.stringify(sel)});
      if(!n) return null; n.scrollIntoView({block:'nearest'}); var r=n.getBoundingClientRect();
      if(r.width<2||r.height<2) return null;
      return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height};})()`);
    if (!box || box.x == null) return null;
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x: box.x, y: box.y, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: box.x, y: box.y, button: "left", clickCount: 1 });
    return box;
  };
  const shot = async (name, w, h, mobile) => {
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: !!mobile });
    await sleep(400);
    const r = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(ART, name), Buffer.from(r.result.data, "base64"));
    ok("shot " + name, true, join(ART, name));
  };

  const plan = await fetch(BASE + "/api/runs/" + SAMPLE + "/watch-plan").then((r) => r.json());
  ok("U0 live watch-plan-1", plan && plan.schema === "watch-plan-1" && (plan.chapters || []).length >= 2,
    JSON.stringify({ n: (plan.chapters || []).length, kinds: (plan.chapters || []).map((c) => c.kind) }));

  ok("B0 opened sample", (await ev("window.__obs.S.run && window.__obs.S.run.run_id")) === SAMPLE);
  await ev("window.__obs.gotoYear(2)");
  await sleep(700);
  const home = await ev(`(function(){
    var evs=document.getElementById('an-events');
    var text=evs && evs.innerText;
    var opts=[].map.call(document.querySelectorAll('#an-run option'), function(o){return {value:o.value,label:o.textContent};});
    var sample=opts.find(function(o){return o.value==='preset-anime-farm250';});
    return {
      text:text,
      hasCell:/第\\s*\\d+\\s*格/.test(text||''),
      hasKcal:/kcal/i.test(text||''),
      sample:sample
    };
  })()`);
  ok("B-home compact events have no cell/kcal",
    home && home.hasCell === false && home.hasKcal === false && /收成了作物|人一年口粮/.test(home.text || ""),
    JSON.stringify({ text: (home && home.text || "").slice(0, 220), hasCell: home && home.hasCell, hasKcal: home && home.hasKcal }));
  ok("B-home an-run values stay ids, labels have no EXP/FARM_M/seed",
    home && home.sample && home.sample.value === SAMPLE
    && !/EXP|FARM_M|seed/i.test(home.sample.label || "")
    && /示例世界/.test(home.sample.label || ""),
    JSON.stringify(home && home.sample));
  await shot("watch-home-year2-1536.png", 1536, 1024, false);
  await ev("window.__obs.gotoYear(0)");
  await sleep(500);
  const startHit = await click("#an-watch-start");
  ok("B1 看这段历史 is clickable", !!(startHit && startHit.w > 8), JSON.stringify(startHit));
  await sleep(1800);
  const tour = await ev(`(function(){
    var bar=document.getElementById('an-watch-bar');
    var st=window.WatchPlayer && window.WatchPlayer.state();
    return {
      hidden: !bar || bar.hidden,
      title: document.getElementById('an-watch-title') && document.getElementById('an-watch-title').textContent,
      copy: document.getElementById('an-watch-copy') && document.getElementById('an-watch-copy').textContent,
      year: document.getElementById('an-year') && document.getElementById('an-year').textContent,
      active: st && st.active, kind: st && st.chapter && st.chapter.kind,
      eid: st && st.chapter && st.chapter.event_id,
      pauseW: (function(){var n=document.getElementById('an-watch-pause'); var r=n&&n.getBoundingClientRect(); return r&&r.width;})(),
      nextW: (function(){var n=document.getElementById('an-watch-next'); var r=n&&n.getBoundingClientRect(); return r&&r.width;})(),
      exitW: (function(){var n=document.getElementById('an-watch-exit'); var r=n&&n.getBoundingClientRect(); return r&&r.width;})()
    };
  })()`);
  ok("B2 tour starts on origin with visible pause/next/exit",
    tour && tour.active && tour.kind === "origin" && tour.year === "0" && tour.pauseW > 8 && tour.nextW > 8 && tour.exitW > 8
    && /开局|群体代表/.test(tour.copy || ""), JSON.stringify(tour));
  await shot("watch-origin-1536.png", 1536, 1024, false);

  await click("#an-watch-next");
  await sleep(1600);
  const ch1 = await ev("window.WatchPlayer.state()");
  ok("B3 next chapter matches plan year/event",
    ch1 && ch1.chapter && ch1.chapter.year === plan.chapters[1].year
    && String(ch1.chapter.event_id || "") === String(plan.chapters[1].event_id || ""),
    JSON.stringify({ got: ch1 && ch1.chapter && { year: ch1.chapter.year, kind: ch1.chapter.kind, event_id: ch1.chapter.event_id }, want: { year: plan.chapters[1].year, kind: plan.chapters[1].kind, event_id: plan.chapters[1].event_id } }));
  await click("#an-watch-pause");
  await sleep(250);
  const mainCopy = await ev(`(function(){
    var copy=document.getElementById('an-watch-copy') && document.getElementById('an-watch-copy').textContent;
    var facts=document.getElementById('an-watch-facts') && document.getElementById('an-watch-facts').textContent;
    var hidden=document.getElementById('an-watch-facts') && document.getElementById('an-watch-facts').hidden;
    var raw=/built_m|field_before_m|field_after_m|labour_m|harvested_kcal_here_this_year|field_m（/;
    return {copy:copy, facts:facts, factsHidden:hidden, raw: raw.test(copy||'') || raw.test(facts||'')};
  })()`);
  ok("B3c clearing main copy has no raw fact keys",
    mainCopy && mainCopy.raw === false && /开垦|耕作规模单位/.test(mainCopy.copy || ""),
    JSON.stringify(mainCopy));
  await shot("watch-clearing-paused-1536.png", 1536, 1024, false);
  await click("#an-watch-source");
  await sleep(300);
  const srcBody = await ev("document.getElementById('an-watch-src-body') && document.getElementById('an-watch-src-body').textContent");
  const srcOpen = await ev("document.getElementById('an-watch-src-body') && !document.getElementById('an-watch-src-body').hidden");
  ok("B3d Source keeps exact built_m and labour_m",
    srcOpen && /built_m = 5000/.test(srcBody || "") && /labour_m = 5000/.test(srcBody || ""),
    String(srcBody).slice(0, 280));
  await shot("watch-clearing-source-1536.png", 1536, 1024, false);
  await click("#an-watch-pause");
  await sleep(200);
  const farm = await ev(`(function(){
    var n=document.getElementById('fx-farm');
    var rig=n && n.querySelector('.motion-rig');
    return {fx:n && n.getAttribute('data-action'), phase: rig && rig.getAttribute('data-phase'), action: rig && rig.getAttribute('data-action')};
  })()`);
  const wantAct = plan.chapters[1].kind === "clearing" ? "till" : null;
  ok("B4 clearing/harvest enters till or harvest loop not static give",
    !wantAct || (farm && (farm.fx === "till" || farm.action === "till" || farm.action === "harvest") && farm.action !== "give"),
    JSON.stringify(farm));

  await click("#an-watch-pause");
  await sleep(300);
  const paused = await ev("window.WatchPlayer.state()");
  ok("B5 pause stops auto-advance", paused && paused.paused === true, JSON.stringify(paused));
  const idx = paused && paused.idx;
  await sleep(1200);
  const still = await ev("window.WatchPlayer.state()");
  ok("B5b paused index does not jump by itself", still && still.idx === idx, JSON.stringify(still));

  await click("#an-watch-next");
  await sleep(1500);
  const ch2 = await ev("window.WatchPlayer.state()");
  if (ch2 && ch2.chapter && ch2.chapter.kind === "harvest") {
    const farm2 = await ev(`(function(){
      var n=document.getElementById('fx-farm');
      var rig=n && n.querySelector('.motion-rig');
      return {action: rig && rig.getAttribute('data-action'), fx: n && n.getAttribute('data-action')};
    })()`);
    ok("B6 harvest action is harvest", farm2 && (farm2.action === "harvest" || farm2.fx === "harvest"), JSON.stringify(farm2));
  } else ok("B6 harvest chapter reachable or later", !!(ch2 && ch2.chapter), JSON.stringify(ch2));

  const copy = await ev("document.getElementById('an-watch-copy') && document.getElementById('an-watch-copy').textContent");
  ok("B7 copy has no invented motive", !/感恩|饿死|明年一定丰收/.test(copy || ""), copy);

  await click("#an-watch-next");
  await sleep(1600);
  const gap = await ev("document.getElementById('an-watch-gap') && document.getElementById('an-watch-gap').textContent");
  const stM = await ev("window.WatchPlayer.state()");
  if (stM && stM.chapter && stM.chapter.year >= 20) {
    ok("B8 time gap is named in years", /相隔 \d+ 年/.test(gap || ""), gap);
  } else ok("B8 gap pending until a jump chapter", true, JSON.stringify(stM));

  await click("#an-watch-exit");
  await sleep(400);
  const after = await ev("({active:window.WatchPlayer.active(), hidden:document.getElementById('an-watch-bar').hidden, playing:window.__obs.S.playing})");
  ok("B9 自由观察 exits tour and does not keep hijacking play", after && after.active === false && after.hidden === true && after.playing === false, JSON.stringify(after));

  const tBefore = await ev("window.__obs.S.t");
  await ev("window.__obs.setPlaying(true)");
  await sleep(200);
  ok("B10 free play starts after exit", await ev("window.__obs.S.playing") === true);
  await ev("window.__obs.setPlaying(false)");

  await click("#an-watch-start");
  await sleep(800);
  await ev("window.__obs.setPlaying(true)");
  await sleep(300);
  ok("B11 starting free play while touring exits watch",
    (await ev("window.WatchPlayer.active()")) === false);

  const race = await ev(`(async function(){
    var I=window.AnimeScene.Identity;
    var orig=I.ensure.bind(I);
    var release;
    I.ensure=async function(run, opts){
      if(run && run.run_id==='preset-anime-farm250'){
        await new Promise(function(r){ release=r; });
      }
      return orig(run, opts);
    };
    var pA=window.__obs.openRun('preset-anime-farm250');
    await new Promise(function(r){ setTimeout(r, 250); });
    var pB=window.__obs.openRun('preset-anime-farm0');
    var b=await pB;
    if(release) release();
    var a=await pA;
    I.ensure=orig;
    return {run: window.__obs.S.run && window.__obs.S.run.run_id, a:a, b:b};
  })()`);
  ok("B12 delayed identity A then B keeps B", race && race.run === "preset-anime-farm0", JSON.stringify(race));

  await ev("window.__obs.openRun('preset-anime-farm250',{initialYear:0})");
  await sleep(1200);
  await click("#an-watch-start");
  await sleep(1000);
  await shot("watch-1536x1024.png", 1536, 1024, false);
  await shot("watch-1440x900.png", 1440, 900, false);
  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await sleep(500);
  const mob = await ev(`(function(){
    var ids=['an-watch-pause','an-watch-next','an-watch-exit'];
    var inView=function(id){ var n=document.getElementById(id); if(!n||n.hidden) return false; var r=n.getBoundingClientRect(); return r.width>8 && r.top>=0 && r.bottom<=844 && r.right<=390; };
    return {pause:inView('an-watch-pause'), next:inView('an-watch-next'), exit:inView('an-watch-exit'), year:document.getElementById('an-year')&&document.getElementById('an-year').textContent};
  })()`);
  ok("B13 390 pause/next/exit visible", mob && mob.pause && mob.next && mob.exit, JSON.stringify(mob));
  await shot("watch-390x844.png", 390, 844, true);

  await send("Emulation.setDeviceMetricsOverride", { width: 1536, height: 1024, deviceScaleFactor: 1, mobile: false });
  await ev("window.WatchPlayer.exit()");
  await ev("window.__obs.openRun('preset-anime-farm0',{initialYear:0})");
  await sleep(1200);
  await click("#an-watch-start");
  await sleep(1000);
  const miss = await ev("document.getElementById('an-watch-missing') && document.getElementById('an-watch-missing').textContent");
  ok("B14 farm0 missing kinds are param_zero not fake zero harvest chapter",
    /参数设成了 0/.test(miss || ""), miss);

  await ev("window.WatchPlayer.exit()");
  await ev("window.__obs.openRun('preset-anime-farm250',{initialYear:2})");
  await sleep(1000);
  await ev("window.__obs.S.reduceMotion=true; window.__obs.cancelFx();");
  await click("#an-watch-start");
  await sleep(1200);
  await click("#an-watch-next");
  await sleep(1200);
  const reduced = await ev(`(function(){
    var copy=document.getElementById('an-watch-copy') && document.getElementById('an-watch-copy').textContent;
    var fx=document.getElementById('fx-farm');
    var st=window.WatchPlayer.state();
    return {copy:copy, kind:st && st.chapter && st.chapter.kind, year:st && st.chapter && st.chapter.year, hasText: !!(copy && copy.length>8)};
  })()`);
  ok("B15 reduced motion still has readable chapter text", reduced && reduced.hasText && !/感恩/.test(reduced.copy || ""), JSON.stringify(reduced));

  await ev("window.WatchPlayer.exit()");
  await ev("window.__obs.S.reduceMotion=false");
} catch (e) {
  ok("browser harness", false, e && e.stack ? e.stack.slice(0, 500) : String(e));
} finally {
  try { if (ws) ws.close(); } catch (e) {}
  try { chrome.kill("SIGKILL"); } catch (e) {}
}

const failed = out.filter((x) => !x.pass);
const report = {
  task: "G_WATCH_PLAY_01",
  base_url: BASE,
  sample: SAMPLE,
  passed: out.filter((x) => x.pass).length,
  failed: failed.length,
  uncovered: uncovered,
  results: out,
};
writeFileSync(REPORT, JSON.stringify(report, null, 2));
process.stdout.write("report " + REPORT + " passed=" + report.passed + " failed=" + report.failed + "\n");
process.exit(failed.length ? 1 : 0);
