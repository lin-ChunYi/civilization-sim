#!/usr/bin/env node
/** G_MOTION_01 browser checks. --base-url --report --user-data-dir --artifact-dir */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as sleep } from "node:timers/promises";

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf("--" + name);
  return i >= 0 ? args[i + 1] : def;
};
const BASE = flag("base-url", "http://127.0.0.1:8793");
const ART = flag("artifact-dir", join(here, "screenshots", "motion"));
const REPORT = flag("report", join(ART, "motion-ui-report.txt"));
const USER = flag("user-data-dir", "/tmp/g-motion-01-browser");
const CDP = Number(flag("cdp-port", "9353"));
const RUN = "preset-exp06-recip1000";
const PAGE = BASE.replace(/\/$/, "") + "/static/index.html?v=motion-01#tab=world&run=" + RUN + "&t=0";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
mkdirSync(ART, { recursive: true });
mkdirSync(USER, { recursive: true });

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${CDP}`,
  `--user-data-dir=${USER}`,
  "--window-size=1440,1100",
  PAGE,
], { stdio: "ignore" });

const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

const kill = () => { try { chrome.kill("SIGKILL"); } catch (e) {} };

try {
  await sleep(2200);
  const list = await fetch("http://127.0.0.1:" + CDP + "/json/list").then((r) => r.json());
  const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
  if (!page) throw new Error("no page target");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let seq = 0;
  const pending = new Map();
  ws.addEventListener("message", (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) pending.get(msg.id)(msg);
  });
  await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
  const send = (method, params = {}) => {
    const id = ++seq;
    return new Promise((res) => { pending.set(id, res); ws.send(JSON.stringify({ id, method, params })); });
  };
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await sleep(3800);

  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text || "err" };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    const b64 = r.result && r.result.data;
    if (!b64) { ok("shot " + name, false, "no data"); return null; }
    const p = join(ART, name);
    writeFileSync(p, Buffer.from(b64, "base64"));
    ok("shot " + name, true, p);
    return p;
  };

  const ready = await ev("!!(window.__obs && window.Motion && window.__obs.S && window.__obs.S.run && document.querySelector('#map .unit'))");
  ok("B0 page ready with Motion", !!ready, JSON.stringify(ready));

  const ident = await ev(`(function(){
    var M=window.Motion, U=window.UnitArt;
    var id="7567856178022945294";
    var v=U.variant(id), skin=U.silhouetteName(v);
    var dirs=["e","w","n","s","ne"];
    var skins=dirs.map(function(d){return M.samplePose({id:id,skin:skin,action:"walk",dir:d,phase:0.3}).skin;});
    return {skin:skin, skins:skins, allSame: skins.every(function(s){return s===skin;})};
  })()`);
  ok("B1 same variant/skin across directions", ident && ident.allSame, JSON.stringify(ident));

  const limbs = await ev(`(function(){
    var M=window.Motion, samples=[];
    for(var i=0;i<8;i++) samples.push(M.samplePose({skin:"staff",action:"walk",dir:"e",phase:i/8}));
    var n=0;
    for(var j=1;j<8;j++){
      var a=samples[j-1], b=samples[j];
      if(Math.abs(b.lFoot.y-a.lFoot.y)>0.15 || Math.abs(b.joints.lThigh-a.joints.lThigh)>1 || Math.abs(b.joints.rArm-a.joints.rArm)>1) n++;
    }
    var z=M.samplePose({skin:"staff",action:"walk",dir:"e",phase:0});
    var one=M.samplePose({skin:"staff",action:"walk",dir:"e",phase:1});
    return {n:n, closed: Math.abs(z.lFoot.y-one.lFoot.y)<1e-6};
  })()`);
  ok("B2 fixed-root 8 phases change limbs and close", limbs && limbs.n >= 6 && limbs.closed, JSON.stringify(limbs));

  const mig = await ev(`(async function(){
    var O=window.__obs;
    await O.gotoYear(4);
    var rec=O.S.years.get(O.S.run.run_id+'|4');
    var e=(rec.events||[]).find(function(x){return x.type==='migrate';});
    if(!e) return {ok:false};
    var fe=await O.focusEvent(Object.assign({}, e, {t:4,_i:0}));
    await new Promise(function(r){setTimeout(r, 180);});
    var w=document.getElementById('fx-walker');
    var rig=w && w.querySelector('.motion-rig');
    return {ok:!!(fe&&fe.ok), walker:!!w, rig:!!rig, art: rig && rig.getAttribute('data-art'),
      skin: rig && rig.getAttribute('data-skin'), path: w && w.getAttribute('data-path'),
      dir: rig && rig.getAttribute('data-dir'), phase: rig && rig.getAttribute('data-phase'),
      lthigh: rig && rig.getAttribute('data-lthigh')};
  })()`);
  ok("B3 real migrate path uses layered rig not face png",
    mig && mig.ok && mig.rig && mig.art === "rig" && mig.path === "endpoints-only" && mig.skin,
    JSON.stringify(mig));
  await shot("desktop-1440-migrate.png");

  const poll = await ev(`(async function(){
    var O=window.__obs;
    var before=O.S.fxAnim && O.S.fxAnim.phase;
    var t0=O.S.fxAnim && O.S.fxAnim.t0;
    await O.refresh();
    await new Promise(function(r){setTimeout(r, 220);});
    var after=O.S.fxAnim && O.S.fxAnim.phase;
    var t1=O.S.fxAnim && O.S.fxAnim.t0;
    var rig=document.querySelector('#fx-walker .motion-rig');
    return {before:before, after:after, sameT0: t0===t1, stillRig:!!rig};
  })()`);
  ok("B4 refresh/polling does not restart phase clock",
    poll && poll.stillRig && poll.sameT0 && poll.after >= (poll.before || 0) - 0.02,
    JSON.stringify(poll));

  const pause = await ev(`(function(){
    var O=window.__obs;
    O.setPlaying(false);
    O.cancelFx({keepStatic:true});
    return {raf:O.S.fxRaf, walk:O.S.fxWalkRaf, overlay: !!document.getElementById('fx-overlay')};
  })()`);
  ok("B5 pause cancels RAF", pause && pause.raf == null && pause.walk == null, JSON.stringify(pause));

  const reduced = await ev(`(async function(){
    var O=window.__obs;
    O.S.reduceMotion=true;
    O.DirectorLogic.applyMotionPolicy();
    document.documentElement.classList.add('reduce-motion');
    await O.gotoYear(4);
    var rec=O.S.years.get(O.S.run.run_id+'|4');
    var e=(rec.events||[]).find(function(x){return x.type==='migrate';});
    await O.focusEvent(Object.assign({}, e, {t:4,_i:0}));
    return {cls: document.documentElement.classList.contains('reduce-motion'),
      raf: O.S.fxRaf, prefers: O.DirectorLogic.prefersReducedMotion(),
      walker: !!document.getElementById('fx-walker')};
  })()`);
  ok("B6 manual reduced motion stops RAF but keeps static mark",
    reduced && reduced.cls && reduced.prefers && reduced.raf == null && reduced.walker,
    JSON.stringify(reduced));

  const pair = await ev(`(async function(){
    var O=window.__obs;
    O.S.reduceMotion=false;
    O.DirectorLogic.applyMotionPolicy();
    await O.gotoYear(83);
    var rec=O.S.years.get(O.S.run.run_id+'|83');
    var e=(rec.events||[]).find(function(x){return x.type==='aid';});
    if(!e) return {ok:false};
    await O.focusEvent(Object.assign({}, e, {t:83}));
    await new Promise(function(r){setTimeout(r, 120);});
    var wrap=document.getElementById('fx-pair');
    var rigs=wrap ? wrap.querySelectorAll('.motion-rig') : [];
    var skins=[].map.call(rigs, function(n){return n.getAttribute('data-skin');});
    var roles=[].map.call(rigs, function(n){return n.getAttribute('data-role');});
    return {ok:true, n:rigs.length, skins:skins, roles:roles, cell: wrap && wrap.getAttribute('data-event-cell')};
  })()`);
  ok("B7 aid uses donor and receiver rigs at event cell",
    pair && pair.n >= 2 && pair.roles.indexOf("donor") >= 0 && pair.roles.indexOf("receiver") >= 0,
    JSON.stringify(pair));
  await shot("desktop-1440-aid.png");

  const dense = await ev(`(function(){
    var O=window.__obs, M=window.Motion;
    var rec=O.S.years.get(O.S.run.run_id+'|'+O.S.t);
    var live=M.aggregate((rec&&rec.events)||[], {runId:O.S.run.run_id, year:O.S.t, playCap:4});
    var fx=JSON.parse(${JSON.stringify(readFileSync(join(here, "motion-dense-fixture.json"), "utf8"))});
    var agg=M.aggregate(fx.events, {runId:fx.runId, year:fx.year, playCap:4});
    O.fillMotionGroups(agg);
    var box=document.getElementById('motion-groups');
    return {liveIds: live.ids.length, fxIds: agg.ids.length, fxEvents: fx.events.length,
      kcal: agg.kcal, shown: agg.shownCount, text: box ? box.textContent : '', hidden: !box || box.hidden};
  })()`);
  ok("B8 dense fixture groups conserved and listed",
    dense && dense.fxIds === dense.fxEvents && /本年共12条/.test(dense.text) && dense.hidden === false,
    JSON.stringify({ fxIds: dense && dense.fxIds, shown: dense && dense.shown, hidden: dense && dense.hidden }));

  const switchRun = await ev(`(async function(){
    var O=window.__obs;
    var a=O.S.run.run_id;
    var other=(O.S.runs||[]).find(function(r){return r.run_id!==a && r.status==='done';});
    if(!other) return {ok:false, reason:'no-other'};
    await O.openRun(other.run_id);
    await new Promise(function(r){setTimeout(r, 200);});
    return {ok:true, from:a, to:O.S.run.run_id, mixed: O.S.run.run_id===a,
      walker: !!document.getElementById('fx-walker')};
  })()`);
  ok("B9 switching run does not keep previous walker",
    switchRun && switchRun.ok && switchRun.to !== switchRun.from && !switchRun.walker,
    JSON.stringify(switchRun));

  await ev(`(async function(){ var O=window.__obs; await O.openRun(${JSON.stringify(RUN)}); await O.gotoYear(4); })()`);
  await shot("desktop-1440-world.png");

  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await sleep(500);
  const mobile = await ev(`(async function(){
    var O=window.__obs;
    O.layoutPlayDock();
    await O.gotoYear(4);
    var rec=O.S.years.get(O.S.run.run_id+'|4');
    var e=(rec.events||[]).find(function(x){return x.type==='migrate';});
    if(e) await O.focusEvent(Object.assign({}, e, {t:4}));
    var map=document.getElementById('map');
    var dock=document.getElementById('play-dock');
    var sheet=document.getElementById('sel-sheet');
    var year=document.getElementById('scrub-year');
    var play=document.getElementById('b-play');
    var mr=map&&map.getBoundingClientRect();
    var dr=dock&&dock.getBoundingClientRect();
    var sr=sheet&&!sheet.hidden?sheet.getBoundingClientRect():null;
    return {vw: window.innerWidth, mapH: mr?Math.round(mr.height):0,
      dockIn: !!(dr && dr.top>=0 && dr.bottom<=window.innerHeight+8),
      playIn: !!(play && play.getBoundingClientRect().bottom<=window.innerHeight+8),
      year: year && year.textContent,
      sheetAbove: !sr || sr.bottom<=dr.top+8};
  })()`);
  ok("B10 390 map year play same screen, sheet above dock",
    mobile && mobile.vw <= 400 && mobile.mapH > 140 && mobile.dockIn && mobile.playIn && mobile.sheetAbove,
    JSON.stringify(mobile));
  await shot("mobile-390-world.png");

  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await ev("location.hash='#tab=world'; location.pathname;");
  const frames = [];
  await send("Page.startScreencast", { format: "jpeg", quality: 52, everyNthFrame: 2 });
  const onCast = (msg) => {
    if (msg.method === "Page.screencastFrame" && msg.params && msg.params.data) {
      frames.push(msg.params.data);
      send("Page.screencastFrameAck", { sessionId: msg.params.sessionId });
    }
  };
  ws.addEventListener("message", (e) => { try { onCast(JSON.parse(e.data)); } catch (err) {} });
  await ev(`(async function(){
    var O=window.__obs; await O.openRun(${JSON.stringify(RUN)});
    O.S.reduceMotion=false; O.DirectorLogic.applyMotionPolicy();
    await O.gotoYear(4);
    var rec=O.S.years.get(O.S.run.run_id+'|4');
    var e=(rec.events||[]).find(function(x){return x.type==='migrate';});
    await O.focusEvent(Object.assign({}, e, {t:4}));
  })()`);
  await sleep(1600);
  await send("Page.stopScreencast");
  const recDir = join(ART, "recording-frames");
  mkdirSync(recDir, { recursive: true });
  frames.slice(0, 24).forEach((b64, i) => {
    writeFileSync(join(recDir, "f" + String(i).padStart(3, "0") + ".jpg"), Buffer.from(b64, "base64"));
  });
  ok("B11 short screencast frames", frames.length >= 4, "frames=" + frames.length + " dir=" + recDir);

  await send("Page.navigate", { url: BASE.replace(/\/$/, "") + "/static/motion-contact.html" });
  await sleep(800);
  await shot("contact-8phase.png");

  await ws.close();
} catch (e) {
  ok("B-crash", false, String(e && e.message || e));
} finally {
  kill();
  const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
  out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
  const text = out.join("\n") + "\n";
  writeFileSync(REPORT, text);
  process.stdout.write(text);
  process.exit(nf ? 1 : 0);
}
