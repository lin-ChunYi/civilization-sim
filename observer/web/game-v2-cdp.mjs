#!/usr/bin/env node
/** game-v2：真实指针选中群体代表、迁移端点动作、同格援助/信息、分裂不定位、390 宽。 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "game-v2");
mkdirSync(SHOT, { recursive: true });
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9341;
const RUN = "preset-exp06-recip1000";
const PAGE = "http://127.0.0.1:8788/static/index.html?v=game-v2b#tab=world&run=" + RUN + "&t=0";
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`,
  "--user-data-dir=/tmp/game-v2-cdp",
  "--window-size=1440,1100",
  PAGE,
], { stdio: "ignore" });

const out = [];
const ok = (name, cond, detail) => {
  out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));
};

try {
  await sleep(1600);
  const list = await fetch("http://127.0.0.1:" + PORT + "/json/list").then((r) => r.json());
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
    return new Promise((res) => {
      pending.set(id, res);
      ws.send(JSON.stringify({ id, method, params }));
    });
  };
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await sleep(3600);

  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) {
      return { __err: r.result.exceptionDetails.text || "err" };
    }
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    const b64 = r.result && r.result.data;
    if (!b64) { ok("shot " + name, false, "no data"); return; }
    writeFileSync(join(SHOT, name), Buffer.from(b64, "base64"));
    ok("shot " + name, true, "screenshots/game-v2/" + name);
  };
  const clickSel = async (sel) => {
    const box = await ev(`(function(){var n=document.querySelector(${JSON.stringify(sel)});
      if(!n) return null; var r=n.getBoundingClientRect();
      return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height};})()`);
    if (!box || box.__err || box.x == null) return false;
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: box.x, y: box.y });
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x: box.x, y: box.y, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: box.x, y: box.y, button: "left", clickCount: 1 });
    return box;
  };

  const ready = await ev("!!(window.__obs && window.__obs.S && window.__obs.S.run && document.querySelector('#map .unit[data-unit=\"group-rep\"]'))");
  ok("V0 世界里有群体代表", !!ready, JSON.stringify(ready));

  const census = await ev(`(function(){
    var units=[].slice.call(document.querySelectorAll('#map .unit[data-unit="group-rep"]'));
    var circles=[].slice.call(document.querySelectorAll('#map circle.band'));
    var polys=[].slice.call(document.querySelectorAll('#map polygon.band'));
    var O=window.__obs; var rec=O.S.years.get(O.S.run.run_id+'|'+O.S.t);
    var party=units.map(function(n){return n.getAttribute('data-party');});
    return {units:units.length, circleTokens:circles.length, diamondTokens:polys.length,
      bands: rec && rec.bands ? rec.bands.length : 0, t:O.S.t, run:O.S.run && O.S.run.run_id,
      hasHead: !!document.querySelector('#map .unit-head'), hasTunic: !!document.querySelector('#map .unit-tunic'),
      hasCamp: !!document.querySelector('#map .unit-camp'), skirts: document.querySelectorAll('#map .cell-skirt').length,
      party: party};
  })()`);
  ok("V1 代表人数等于在世群体且不是圆点/菱形棋子",
    census && census.units === census.bands && census.units > 0
    && census.circleTokens === 0 && census.diamondTokens === 0 && census.hasHead && census.hasTunic
    && census.hasCamp && census.skirts > 0,
    JSON.stringify(census));
  await shot("desktop-t0-units.png");

  const firstBand = await ev(`(function(){
    var nodes=[].slice.call(document.querySelectorAll('#map .unit[data-unit="group-rep"]'));
    var hit=nodes.find(function(n){var r=n.getBoundingClientRect(); return r.y>140 && r.x>80 && r.width>8;}) || nodes[0];
    return hit ? hit.getAttribute('data-band') : null;
  })()`);
  const clicked = firstBand ? await clickSel('#map .unit[data-band="' + firstBand + '"]') : false;
  await sleep(250);
  const sel = await ev(`(function(){
    var O=window.__obs;
    var n=document.querySelector('#map .unit.selected');
    return {selBand:O.S.selBand, selected: !!(n && n.getAttribute('data-band')===O.S.selBand),
      pose: n && n.getAttribute('data-pose'), rail: document.querySelector('#pane-dossier') && !document.querySelector('#pane-dossier').hidden};
  })()`);
  ok("V2 真实鼠标选中群体代表并打开档案",
    clicked && sel && sel.selBand === firstBand && sel.selected && sel.pose === "select",
    JSON.stringify({ firstBand, clicked, sel }));
  await shot("desktop-select-unit.png");

  const mig = await ev(`(async function(){
    var O=window.__obs;
    var gy=await O.gotoYear(4);
    var rec=O.S.years.get(O.S.run.run_id+'|4');
    var e=(rec.events||[]).find(function(x){return x.type==='migrate';});
    if(!e) return {ok:false, reason:'no-migrate'};
    var fe=await O.focusEvent(Object.assign({}, e, {t:4, _i:0}));
    await new Promise(function(r){setTimeout(r, 120);});
    var w=document.getElementById('fx-walker');
    var line=document.querySelector('#fx-overlay line.fx-endpoint-line');
    var from=document.querySelector('#fx-overlay .fx-endpoint-from');
    var to=document.querySelector('#fx-overlay .fx-endpoint-to');
    return {ok: !!(fe && fe.ok), t:O.S.t, eid:e.id, from:e.from, to:e.to,
      walker: !!(w && w.getAttribute('data-path')==='endpoints-only'),
      stage: w && w.getAttribute('data-stage'),
      linePath: line && line.getAttribute('data-path'),
      endpoints: !!(from && to), caption: (document.querySelector('#fx-overlay .fx-caption')||{}).textContent||''};
  })()`);
  ok("V3 迁移有端点人物动作且不编中间格子",
    mig && mig.ok && mig.t === 4 && mig.walker && mig.linePath === "endpoints-only" && mig.endpoints
    && /路线未记录/.test(mig.caption) && mig.stage,
    JSON.stringify(mig));
  await shot("desktop-migrate-walk.png");
  await sleep(500);
  await shot("desktop-migrate-walk-kf2.png");

  const share = await ev(`(async function(){
    var O=window.__obs;
    await O.gotoYear(125);
    var rec=O.S.years.get(O.S.run.run_id+'|125');
    var e=(rec.events||[]).find(function(x){return x.type==='share' && x.cell===0;}) || (rec.events||[]).find(function(x){return x.type==='share';});
    if(!e) return {ok:false};
    var fe=await O.focusEvent(Object.assign({}, e, {t:125}));
    await new Promise(function(r){setTimeout(r, 80);});
    var pair=document.getElementById('fx-pair');
    return {ok: !!(fe && fe.ok), t:O.S.t, eid:e.id, cell:e.cell,
      pairCell: pair && pair.getAttribute('data-event-cell'),
      fx: pair && pair.getAttribute('data-fx'),
      units: pair ? pair.querySelectorAll('.unit').length : 0};
  })()`);
  ok("V4 信息交换在事件格演示两人互动",
    share && share.ok && String(share.pairCell) === String(share.cell) && share.fx === "share" && share.units >= 2,
    JSON.stringify(share));
  await shot("desktop-share-cell.png");

  const aid = await ev(`(async function(){
    var O=window.__obs;
    await O.gotoYear(83);
    var rec=O.S.years.get(O.S.run.run_id+'|83');
    var e=(rec.events||[]).find(function(x){return x.type==='aid';});
    if(!e) return {ok:false};
    var fe=await O.focusEvent(Object.assign({}, e, {t:83}));
    await new Promise(function(r){setTimeout(r, 80);});
    var pair=document.getElementById('fx-pair');
    return {ok: !!(fe && fe.ok), eid:e.id, cell:e.cell, kcal:e.kcal,
      pairCell: pair && pair.getAttribute('data-event-cell'), fx: pair && pair.getAttribute('data-fx')};
  })()`);
  ok("V5 援助动作锚定事件格",
    aid && aid.ok && String(aid.pairCell) === String(aid.cell) && aid.fx === "aid",
    JSON.stringify(aid));
  await shot("desktop-aid-cell.png");

  const split = await ev(`(async function(){
    var O=window.__obs;
    await O.gotoYear(52);
    var rec=O.S.years.get(O.S.run.run_id+'|52');
    var e=(rec.events||[]).find(function(x){return x.type==='split';});
    if(!e) return {ok:false};
    var fe=await O.focusEvent(Object.assign({}, e, {t:52}));
    await new Promise(function(r){setTimeout(r, 80);});
    var body=document.querySelector('#director-card-body');
    return {ok: !!(fe && fe.ok), eid:e.id, walker: !!document.getElementById('fx-walker'),
      pair: !!document.getElementById('fx-pair'), overlayKids: (document.querySelector('#fx-overlay')||{childNodes:{length:0}}).childNodes.length,
      note: body ? body.textContent : ''};
  })()`);
  ok("V6 分裂不在地图上猜地点",
    split && split.ok && !split.walker && !split.pair && /地点未记录/.test(split.note),
    JSON.stringify(split));
  await shot("desktop-split-no-locate.png");

  const play = await ev(`(async function(){
    var O=window.__obs;
    await O.gotoYear(3);
    O.setPlayMode('year');
    O.setPlaying(true);
    await new Promise(function(r){setTimeout(r, 700);});
    var t=O.S.t; var playing=O.S.playing;
    O.setPlaying(false);
    return {t:t, playingWas: playing, startedAt:3, advanced: t>3};
  })()`);
  ok("V7 播放推进年份", play && play.advanced, JSON.stringify(play));

  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await sleep(400);
  await ev(`(async function(){ var O=window.__obs; await O.gotoYear(0); O.S.selEvent=null; O.cancelFx(); O.S.cam={x:0,y:0,k:1}; 
    var n=document.querySelector('#map'); if(n) n.setAttribute('viewBox', '0 0 520 430'); return true; })()`);
  await sleep(200);
  const mobile = await ev(`(function(){
    var units=document.querySelectorAll('#map .unit[data-unit="group-rep"]').length;
    var hud=document.querySelector('.hud');
    var hr=hud?hud.getBoundingClientRect().height:0;
    return {units:units, hud:Math.round(hr), vw:window.innerWidth};
  })()`);
  ok("V8 390 宽仍能看见群体代表",
    mobile && mobile.units > 0 && mobile.vw <= 400 && mobile.hud <= 120,
    JSON.stringify(mobile));
  await shot("mobile-390-units.png");

  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  const reduced = await ev(`(async function(){
    var O=window.__obs;
    await O.gotoYear(4);
    var rec=O.S.years.get(O.S.run.run_id+'|4');
    var e=(rec.events||[]).find(function(x){return x.type==='migrate';});
    var fe=await O.focusEvent(Object.assign({}, e, {t:4}));
    await new Promise(function(r){setTimeout(r, 40);});
    var w=document.getElementById('fx-walker');
    var pose=w && w.querySelector('.unit') && w.querySelector('.unit').getAttribute('data-pose');
    return {ok: !!(fe && fe.ok), pose: pose, prefers: O.DirectorLogic.prefersReducedMotion(),
      walker: !!w, path: w && w.getAttribute('data-path')};
  })()`);
  ok("V9 减少动效时迁移停在终点姿态，仍有端点代表",
    reduced && reduced.ok && reduced.prefers && reduced.walker && reduced.path === "endpoints-only"
    && reduced.pose === "idle",
    JSON.stringify(reduced));
  await shot("desktop-reduced-migrate.png");

} catch (e) {
  ok("cdp crashed", false, String(e && e.stack || e));
} finally {
  chrome.kill("SIGKILL");
  const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
  out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
  process.stdout.write(out.join("\n") + "\n");
  process.exit(nf ? 1 : 0);
}
