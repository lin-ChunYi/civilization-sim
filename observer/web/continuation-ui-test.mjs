#!/usr/bin/env node
/** G_CONT_UI_01: real UI continue-evolution. --base-url --report --service-json */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as sleep } from "node:timers/promises";
import vm from "node:vm";

const here = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const flag = (name, def) => {
  const i = argv.indexOf("--" + name);
  return i >= 0 ? argv[i + 1] : def;
};
const BASE = (flag("base-url", "http://127.0.0.1:8793") || "").replace(/\/$/, "");
const ART = flag("artifact-dir", join(here, "screenshots", "cont-ui"));
const REPORT = flag("report", join(ART, "continuation-ui-report.txt"));
const USER = flag("user-data-dir", "/tmp/g-cont-ui-01");
const CDP = Number(flag("cdp-port", "9361"));
const SERVICE_JSON = flag("service-json", "");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
mkdirSync(ART, { recursive: true });
mkdirSync(USER, { recursive: true });

const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));
const uncovered = (name, why) => out.push("UNCOVERED " + name + " :: " + why);

const motionCode = readFileSync(join(here, "motion.js"), "utf8");
const appCode = readFileSync(join(here, "app.js"), "utf8");
const ctx = {
  window: { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) },
  document: { getElementById() { return null; }, querySelector() { return null; }, querySelectorAll() { return []; }, addEventListener() {}, documentElement: { classList: { toggle() {}, contains() { return false; } } } },
  location: { hash: "", search: "", href: "http://127.0.0.1/static/index.html" },
  history: { replaceState() {} },
  sessionStorage: { getItem() { return ""; }, setItem() {} },
  performance: { now: Date.now },
  console, setTimeout, clearTimeout,
  requestAnimationFrame: (fn) => setTimeout(fn, 16),
  cancelAnimationFrame: clearTimeout,
  fetch: async () => ({ ok: true, json: async () => ({}) }),
};
ctx.window = Object.assign(ctx.window, ctx);
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(motionCode, ctx);
vm.runInContext(appCode, ctx);
const CL = ctx.window.ContinuationLogic;
ok("L0 ContinuationLogic loaded", !!CL && typeof CL.segmentCaption === "function");
ok("L1 extra years reject decimals", !CL.parseExtraYears("300.5", 300).ok && CL.parseExtraYears("300", 300).value === 300);
ok("L2 unknown version is 未记录 not 过期",
  CL.versionLabel({}) === "版本身份未记录" && CL.versionLabel({ version: {} }) === "版本身份未记录");
ok("L3 continuation caption uses inherited range",
  /继承0–300年/.test(CL.segmentCaption({
    lineage: { kind: "continuation", from_year: 300 },
    segment: { from_year: 300, additional_years: 300, completed_steps: 37, history_ready: true },
    years_recorded: 337,
  }, 312)) && /正在回放312年/.test(CL.segmentCaption({
    lineage: { kind: "continuation", from_year: 300 },
    segment: { from_year: 300, additional_years: 300, completed_steps: 37 },
    years_recorded: 337,
  }, 312)));

async function http(path, opts) {
  const r = await fetch(BASE + path, opts || {});
  const body = await r.json().catch(() => ({}));
  return { status: r.status, body };
}
async function waitRun(id, pred, ms, label) {
  const t0 = Date.now();
  let last = null;
  while (Date.now() - t0 < ms) {
    const { status, body } = await http("/api/runs/" + id);
    last = body;
    if (status === 200 && pred(body)) return body;
    await sleep(2000);
  }
  throw new Error("timeout " + (label || id) + " last=" + JSON.stringify({
    status: last && last.status, rec: last && last.years_recorded, ready: last && last.segment,
  }));
}
function portOf(url) {
  try { return Number(new URL(url).port); } catch (e) { return 0; }
}
async function restartIsolatedService() {
  if (!SERVICE_JSON || !existsSync(SERVICE_JSON)) {
    throw new Error("need --service-json to restart isolated service");
  }
  const info = JSON.parse(readFileSync(SERVICE_JSON, "utf8"));
  const runs = await http("/api/runs");
  if (runs.body && runs.body.active) throw new Error("active simulation, refuse restart");
  const pid = info.pid;
  if (!pid) throw new Error("service-json missing pid");
  try { process.kill(pid, "SIGTERM"); } catch (e) { /* already gone */ }
  await sleep(800);
  const env = Object.assign({}, process.env, {
    PYTHONPATH: info.pythonpath || info.cwd,
    OBSERVER_DATA_DIR: info.data_dir,
    OBSERVER_WEB_DIR: info.web_dir || join(info.cwd, "observer/web"),
    OBSERVER_UI_BUILD: "game-v2",
  });
  const child = spawn(info.argv[0], info.argv.slice(1), {
    cwd: info.cwd, env: env, stdio: "ignore", detached: true,
  });
  child.unref();
  info.pid = child.pid;
  info.previous_pid = pid;
  writeFileSync(SERVICE_JSON, JSON.stringify(info, null, 2));
  const t0 = Date.now();
  while (Date.now() - t0 < 30000) {
    try {
      const h = await fetch(BASE + "/api/health");
      if (h.ok) return info.pid;
    } catch (e) { /* wait */ }
    await sleep(400);
  }
  throw new Error("service did not come back");
}

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${CDP}`,
  `--user-data-dir=${USER}`,
  "--window-size=1440,1100",
  BASE + "/static/index.html?v=cont-ui#tab=runs",
], { stdio: "ignore" });
const killChrome = () => { try { chrome.kill("SIGKILL"); } catch (e) {} };

try {
  await sleep(2500);
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
  await sleep(3500);
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text || "err" };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    const b64 = r.result && r.result.data;
    if (!b64) { ok("shot " + name, false); return; }
    writeFileSync(join(ART, name), Buffer.from(b64, "base64"));
    ok("shot " + name, true, join(ART, name));
  };
  const clickSel = async (sel) => {
    const box = await ev(`(function(){var n=document.querySelector(${JSON.stringify(sel)});
      if(!n) return null; var r=n.getBoundingClientRect();
      return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height,disabled:!!n.disabled};})()`);
    if (!box || box.__err || box.x == null) return false;
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: box.x, y: box.y });
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x: box.x, y: box.y, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: box.x, y: box.y, button: "left", clickCount: 1 });
    return box;
  };

  const ready = await ev("!!(window.__obs && window.__obs.ContinuationLogic && document.getElementById('b-continue'))");
  ok("C0 continue hooks present", !!ready, JSON.stringify(ready));

  const disabled = await ev(`(async function(){
    var O=window.__obs;
    var exp1=(O.S.runs||[]).find(function(r){return r.engine==='exp01';});
    if(!exp1) return {ok:false, reason:'no-exp01'};
    await O.openContinueDialog(exp1.run_id);
    var btn=document.getElementById('b-confirm-continue');
    var reason=(document.getElementById('continue-reason')||{}).textContent||'';
    return {ok:true, disabled: !!(btn && btn.disabled), reason:reason, hidden: document.getElementById('continue-dialog').hidden};
  })()`);
  ok("C1 unsupported/missing checkpoint disables confirm",
    disabled && disabled.ok && disabled.disabled && /unsupported_engine|missing_checkpoint/.test(disabled.reason),
    JSON.stringify(disabled));
  await ev("window.__obs.hideContinueDialog()");

  const draft = await ev(`(function(){
    var O=window.__obs;
    O.showTab('runs');
    var eng=document.getElementById('f-engine');
    if(eng){ eng.value='exp06'; O.syncEngineForm(); }
    document.getElementById('f-seed').value='31337';
    document.getElementById('f-years').value='300';
    if(document.getElementById('f-sigma')) document.getElementById('f-sigma').value='0';
    if(document.getElementById('f-mort')) document.getElementById('f-mort').value='50';
    if(document.getElementById('f-share')) document.getElementById('f-share').value='1000';
    if(document.getElementById('f-aid')) document.getElementById('f-aid').value='1000';
    if(document.getElementById('f-recip')) document.getElementById('f-recip').value='1000';
    document.getElementById('f-label').value='G_CONT_UI_01 parent';
    return O.collectRunDraft();
  })()`);
  ok("C2 forge draft is exp06 300y",
    draft && draft.ok && draft.body && draft.body.engine === "exp06" && draft.body.years === 300,
    JSON.stringify(draft && draft.body));

  await clickSel("#b-start");
  await sleep(200);
  const started = await clickSel("#b-confirm");
  ok("C3 clicked confirm to create parent through UI", !!started);

  const parentId = await ev(`(async function(){
    var O=window.__obs;
    var t0=Date.now();
    while(Date.now()-t0<15000){
      await O.refresh();
      var r=(O.S.runs||[]).find(function(x){return x.label==='G_CONT_UI_01 parent';});
      if(r) return r.run_id;
      await new Promise(function(res){setTimeout(res,400);});
    }
    return O.S.run && O.S.run.label==='G_CONT_UI_01 parent' ? O.S.run.run_id : null;
  })()`);
  ok("C4 parent run id from UI", !!parentId, String(parentId));
  if (!parentId) throw new Error("no parent run");

  const parentDone = await waitRun(parentId, (r) => r.status === "done" && r.years_recorded >= 300, 2400000, "parent-300");
  ok("C5 parent 300y done", parentDone.status === "done" && parentDone.years_recorded >= 300,
    JSON.stringify({ rec: parentDone.years_recorded, status: parentDone.status }));

  const newPid = await restartIsolatedService();
  ok("C6 restarted isolated service", !!newPid, "pid=" + newPid);
  await send("Page.navigate", { url: BASE + "/static/index.html?v=cont-ui2#tab=world&run=" + parentId + "&t=300" });
  await sleep(4000);
  const afterRestart = await ev("!!(window.__obs && window.__obs.S && window.__obs.S.run && window.__obs.S.run.run_id)");
  ok("C7 page alive after restart", !!afterRestart);

  await ev(`(async function(){ var O=window.__obs; await O.openRun(${JSON.stringify(parentId)}, {initialYear:300}); })()`);
  await clickSel("#b-continue");
  await sleep(400);
  const dlg = await ev(`(function(){
    var d=document.getElementById('continue-dialog');
    var btn=document.getElementById('b-confirm-continue');
    var years=document.getElementById('f-extra-years');
    if(years) years.value='300';
    return {hidden: !d || d.hidden, disabled: !!(btn && btn.disabled),
      reason: (document.getElementById('continue-reason')||{}).textContent||'',
      summary: (document.getElementById('continue-summary')||{}).textContent||'',
      req: window.__obs.S.continueReq && window.__obs.S.continueReq.requestId};
  })()`);
  ok("C8 continue dialog eligible after restart",
    dlg && dlg.hidden === false && dlg.disabled === false && /继续/.test(dlg.reason + dlg.summary),
    JSON.stringify(dlg));
  await shot("desktop-continue-dialog.png");

  const reqId = dlg && dlg.req;
  const firstPost = await ev(`(async function(){
    var O=window.__obs;
    var id=O.S.continueReq.requestId;
    var parent=O.S.continueDraft.parentId;
    var a=await O.api('/api/runs/'+parent+'/continue',{method:'POST',body:JSON.stringify({additional_years:300,request_id:id})});
    var b=await O.api('/api/runs/'+parent+'/continue',{method:'POST',body:JSON.stringify({additional_years:300,request_id:id})});
    return {a:a, b:b, same: a.run_id===b.run_id, reused: b.reused===true};
  })()`);
  ok("C9 same request_id does not create two children",
    firstPost && firstPost.same && firstPost.reused && firstPost.a.run_id,
    JSON.stringify(firstPost));
  const childId = firstPost && firstPost.a.run_id;
  if (!childId) throw new Error("no child");

  await ev(`(function(){
    var O=window.__obs;
    O.S.continueWatch={parentId:${JSON.stringify(parentId)}, childId:${JSON.stringify(childId)}, fromYear:300, stay:true};
    O.hideContinueDialog();
  })()`);

  const steal = await ev(`(async function(){
    var O=window.__obs;
    var other=(O.S.runs||[]).find(function(r){return r.run_id!==${JSON.stringify(parentId)} && r.run_id!==${JSON.stringify(childId)};});
    if(!other) return {ok:false};
    await O.openRun(other.run_id);
    await new Promise(function(r){setTimeout(r,200);});
    await O.maybeOpenContinuedRun();
    return {ok:true, run:O.S.run && O.S.run.run_id, other:other.run_id, stolen: O.S.run && O.S.run.run_id===${JSON.stringify(childId)}};
  })()`);
  ok("C10 switching run does not steal UI to child",
    steal && steal.ok && steal.run === steal.other && !steal.stolen, JSON.stringify(steal));

  const childReady = await waitRun(childId, (r) => r.segment && r.segment.history_ready, 120000, "history-ready");
  ok("C11 child history_ready", !!(childReady.segment && childReady.segment.history_ready),
    JSON.stringify(childReady.segment));

  const childDone = await waitRun(childId, (r) => r.status === "done" && r.years_recorded >= 600, 2400000, "child-600");
  ok("C12 child reached year 600", childDone.status === "done" && childDone.years_recorded >= 600,
    JSON.stringify({ rec: childDone.years_recorded, steps: childDone.segment }));

  await ev(`(async function(){ var O=window.__obs; await O.openRun(${JSON.stringify(childId)}, {initialYear:300}); })()`);
  const at300 = await ev("window.__obs.S.t");
  ok("C13 open child lands on from_year not t=0", at300 === 300, "t=" + at300);
  await shot("desktop-child-t300.png");

  const years = {};
  for (const y of [299, 300, 301, 600]) {
    const apiY = await http("/api/runs/" + childId + "/year/" + y);
    const uiY = await ev(`(async function(){
      var O=window.__obs; await O.gotoYear(${y});
      var rec=O.S.years.get(O.S.run.run_id+'|'+${y});
      return rec ? {t:rec.t, pop: rec.agg && rec.agg.pop, ev:(rec.events||[]).length, ids:(rec.events||[]).map(function(e){return e.id;})} : null;
    })()`);
    years[y] = { api: apiY.body, ui: uiY };
    ok("C14 year " + y + " UI matches API",
      uiY && apiY.status === 200 && uiY.pop === (apiY.body.agg && apiY.body.agg.pop)
      && uiY.ev === ((apiY.body.events || []).length),
      JSON.stringify({ pop: uiY && uiY.pop, ev: uiY && uiY.ev }));
  }
  const p300 = await http("/api/runs/" + parentId + "/year/300");
  const c300 = years[300];
  const pIds = ((p300.body.events || []).map((e) => e.id)).join(",");
  const cIds = (c300.ui && c300.ui.ids || []).join(",");
  ok("C15 year 300 not re-recorded as a new event set", pIds === cIds && pIds.length > 0, "ids=" + pIds.slice(0, 80));

  const repay = await ev(`(async function(){
    var O=window.__obs;
    var found=null;
    for (var y=301; y<=Math.min(600, O.S.run.years_recorded); y++){
      var rec=O.S.years.get(O.S.run.run_id+'|'+y);
      if(!rec) {
        try { rec=await O.api('/api/runs/'+O.S.run.run_id+'/year/'+y); O.S.years.set(O.S.run.run_id+'|'+y, rec);} catch(e){ continue; }
      }
      var e=(rec.events||[]).find(function(x){return x.type==='aid' && x.repay && x.basis && (x.basis.prior_events||[]).length;});
      if(e){ found={y:y, e:e}; break; }
    }
    if(!found) return {ok:false};
    var prior=found.e.basis.prior_events[0];
    var py=O.DirectorLogic.yearFromEventId(prior);
    var jump=await O.jumpToRecordedEvent(prior, py);
    return {ok:!!(jump&&jump.ok), prior:prior, py:py, t:O.S.t, ev:O.S.selEvent};
  })()`);
  ok("C16 repay basis jumps to inherited original event",
    repay && repay.ok && repay.py != null && repay.py <= 300, JSON.stringify(repay));

  const cap = await ev("document.getElementById('cont-seg') && document.getElementById('cont-seg').textContent");
  ok("C17 segment caption on child", /继承0–300年/.test(cap || "") && /正在回放/.test(cap || ""), cap);

  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await sleep(400);
  await ev("window.__obs.layoutPlayDock()");
  const mobile = await ev(`(function(){
    var b=document.getElementById('b-continue');
    var d=document.getElementById('play-dock');
    var dlg=document.getElementById('continue-dialog');
    var br=b&&b.getBoundingClientRect();
    var dr=d&&d.getBoundingClientRect();
    return {btn:!!b, inDock: !!(br && dr && br.bottom<=dr.bottom+4 && br.top>=dr.top-4),
      w: br&&br.width, h: br&&br.height, dlgBottom: dlg&&!dlg.hidden?dlg.getBoundingClientRect().bottom:null,
      dockTop: dr&&dr.top};
  })()`);
  ok("C18 390 continue button in play-dock",
    mobile && mobile.btn && mobile.inDock && mobile.w >= 24 && mobile.h >= 24, JSON.stringify(mobile));
  await clickSel("#b-continue");
  await sleep(200);
  const dlg390 = await ev(`(function(){
    var dlg=document.getElementById('continue-dialog');
    var dock=document.getElementById('play-dock');
    var play=document.getElementById('b-play');
    if(!dlg||dlg.hidden) return {open:false};
    var a=dlg.getBoundingClientRect(), b=dock.getBoundingClientRect(), p=play.getBoundingClientRect();
    return {open:true, dlgBottom:a.bottom, dockTop:b.top, playVisible: p.bottom<=window.innerHeight+4 && p.height>10};
  })()`);
  ok("C19 390 dialog does not cover play controls",
    dlg390 && dlg390.open && dlg390.dlgBottom <= dlg390.dockTop + 8 && dlg390.playVisible,
    JSON.stringify(dlg390));
  await shot("mobile-390-continue.png");

  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await send("Page.navigate", { url: BASE + "/static/index.html?v=cont-ui3#tab=world&run=" + childId + "&t=301" });
  await sleep(4000);
  const restored = await ev("({run: window.__obs.S.run && window.__obs.S.run.run_id, t: window.__obs.S.t})");
  ok("C20 refresh/hash restores child run",
    restored && restored.run === childId && restored.t === 301, JSON.stringify(restored));
  await shot("desktop-restore-child.png");

  writeFileSync(join(ART, "ids.json"), JSON.stringify({
    parent_run_id: parentId, child_run_id: childId,
    play_url: BASE + "/static/index.html#tab=world&run=" + childId + "&t=300",
    parent_url: BASE + "/static/index.html#tab=world&run=" + parentId + "&t=300",
    request_id: reqId, port: portOf(BASE),
  }, null, 2));

  await ws.close();
} catch (e) {
  if (/no page target|ECONNREFUSED/.test(String(e))) {
    uncovered("browser", String(e && e.message || e));
  } else {
    ok("C-crash", false, String(e && e.stack || e));
  }
} finally {
  killChrome();
  const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
  out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length
    + " fail=" + nf
    + " uncovered=" + out.filter((l) => l.indexOf("UNCOVERED") === 0).length);
  const text = out.join("\n") + "\n";
  writeFileSync(REPORT, text);
  process.stdout.write(text);
  process.exit(nf ? 1 : 0);
}
