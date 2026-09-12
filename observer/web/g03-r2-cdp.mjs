#!/usr/bin/env node
/** G03_R2：测试代理 8774 故障注入 + 真实点击。不是纯 VM。 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g03");
mkdirSync(SHOT, { recursive: true });
const PROXY = "http://127.0.0.1:8774";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9337;
const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

async function arm(q) {
  const r = await fetch(PROXY + "/__test/arm?" + q);
  const t = await r.text();
  return { status: r.status, t };
}
async function release() {
  const r = await fetch(PROXY + "/__test/release");
  return { status: r.status, t: await r.text() };
}
async function proxyStatus() {
  const r = await fetch(PROXY + "/__test/status");
  const t = await r.text();
  try { return JSON.parse(t); } catch (e) { return { raw: t, http: r.status }; }
}

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`,
  "--user-data-dir=/tmp/g03-r2-cdp",
  "--window-size=1440,1100",
  "about:blank",
], { stdio: "ignore" });

try {
  const st0 = await proxyStatus();
  ok("P0 测试代理 8774 可达", st0 && (st0.raw === undefined || st0.hits != null || st0.held != null || st0.mode != null || st0.ok !== false),
    JSON.stringify(st0).slice(0, 200));

  await sleep(1200);
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
    return new Promise((res) => { pending.set(id, res); ws.send(JSON.stringify({ id, method, params })); });
  };
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });

  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(SHOT, name), Buffer.from(r.result.data, "base64"));
    ok("shot " + name, true, "screenshots/g03/" + name);
  };
  const clickSel = async (sel) => {
    const box = await ev(`(function(){var n=document.querySelector(${JSON.stringify(sel)});
      if(!n) return null; n.scrollIntoView(); var r=n.getBoundingClientRect();
      return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    if (!box || box.__err || box.x == null) return false;
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: box.x, y: box.y });
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x: box.x, y: box.y, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: box.x, y: box.y, button: "left", clickCount: 1 });
    return true;
  };
  const openAt = async (hash) => {
    const url = PROXY + "/static/index.html?r2=" + Date.now() + hash;
    await send("Page.navigate", { url: url });
    await sleep(3500);
  };
  const dropYear = async (t) => ev(`(function(){var O=window.__obs; if(!O||!O.S.run) return false;
    O.S.years.delete(O.ykey(O.S.run.run_id,${t})); return !O.S.years.has(O.ykey(O.S.run.run_id,${t}));})()`);
  const snapFail = () => ev(`({t:window.__obs.S.t,playing:window.__obs.S.playing,timer:window.__obs.S.timer,
    btn:document.getElementById('b-play').textContent,note:document.getElementById('tl-note').innerText,
    failHidden:document.getElementById('year-fail').hidden,
    fail:(document.getElementById('year-fail-text')||{}).innerText,
    chips:document.getElementById('year-metrics').innerText,
    overlay:document.getElementById('year-load').hidden,
    rec:!!window.__obs.S.years.get(window.__obs.ykey(window.__obs.S.run.run_id, window.__obs.S.t)),
    wait:window.__obs.S.yearWait})`);

  await arm("mode=hold&suffix=/year/125");
  await openAt("#tab=world&run=preset-exp06-recip1000&t=124");
  const ready = await ev("!!(window.__obs && window.__obs.S && window.__obs.S.run)");
  ok("P1 页面加载", !!ready, JSON.stringify(ready));
  const t124 = await ev("({t:window.__obs.S.t,run:window.__obs.S.run&&window.__obs.S.run.run_id})");
  ok("P2 停在 t124", t124 && t124.t === 124, JSON.stringify(t124));
  await ev("document.getElementById('mode-year').click()");
  ok("P3 点播放", await clickSel("#b-play"));
  await sleep(400);
  const loading = await ev("({hidden:document.getElementById('year-load').hidden,n:(document.getElementById('year-load-n')||{}).textContent,playing:window.__obs.S.playing})");
  ok("P4 等待 125 时遮罩可见", loading && loading.hidden === false && String(loading.n) === "125", JSON.stringify(loading));
  await shot("r2-hold-overlay.png");
  ok("P5 点暂停", await clickSel("#b-play"));
  await sleep(200);
  const paused = await ev("({t:window.__obs.S.t,playing:window.__obs.S.playing,hidden:document.getElementById('year-load').hidden,btn:document.getElementById('b-play').textContent})");
  ok("P6 暂停后 t124 且遮罩关闭", paused && paused.t === 124 && paused.playing === false && paused.hidden === true,
    JSON.stringify(paused));
  await shot("r2-pause-clears-overlay.png");
  await release();
  await sleep(500);
  const afterRel = await ev("({t:window.__obs.S.t,hidden:document.getElementById('year-load').hidden,playing:window.__obs.S.playing})");
  ok("P7 release 后仍 124 不串遮罩", afterRel && afterRel.t === 124 && afterRel.hidden === true && afterRel.playing === false,
    JSON.stringify(afterRel));

  const armed500 = await arm("mode=error&status=500&suffix=/year/125");
  ok("P8a arm 500", armed500 && armed500.status < 500, JSON.stringify(armed500).slice(0, 160));
  await openAt("#tab=world&run=preset-exp06-recip1000&t=124");
  await ev("document.getElementById('mode-year').click()");
  const dropped = await dropYear(125);
  ok("P8b 丢掉缓存的 125", dropped === true, JSON.stringify(dropped));
  ok("P8 500 测试点播放", await clickSel("#b-play"));
  await sleep(400);
  let mid = await snapFail();
  if (mid && mid.overlay === false) await release();
  else await release();
  await sleep(600);
  const fail = await snapFail();
  ok("P9 year/500 暂停且不显示仍在播放", fail && fail.playing === false && fail.timer == null && /播放/.test(fail.btn || "") && !/回放中/.test(fail.note || ""),
    JSON.stringify(fail).slice(0, 280));
  ok("P10 失败年不沿用 124 援助 chips", fail && fail.t === 125 && !fail.rec && (!fail.chips || fail.chips.indexOf("活动") < 0),
    JSON.stringify({ t: fail && fail.t, chips: fail && fail.chips, rec: fail && fail.rec }));
  ok("P11 失败条可见可重试", fail && fail.failHidden === false && /125/.test(fail.fail || ""), JSON.stringify(fail && fail.fail));
  await shot("r2-year-500.png");

  await arm("mode=hold&suffix=/year/125");
  await release();
  ok("P12 点重试", await clickSel("#b-retry-year"));
  await sleep(900);
  const retried = await ev("({t:window.__obs.S.t,has:!!window.__obs.S.years.get(window.__obs.ykey(window.__obs.S.run.run_id,125)),failHidden:document.getElementById('year-fail').hidden,playing:window.__obs.S.playing})");
  ok("P13 重试恢复 125 记录", retried && retried.t === 125 && retried.has === true && retried.failHidden === true,
    JSON.stringify(retried));
  await shot("r2-retry-ok.png");

  await arm("mode=error&status=500&suffix=/year/125");
  await openAt("#tab=world&run=preset-exp06-recip1000&t=124&mode=events");
  const primed = await ev(`(async function(){
    var O=window.__obs;
    document.getElementById('mode-events').click();
    await O.gotoYear(124);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,124));
    var evs=(rec&&rec.events)||[];
    O.S.selEvent = evs.length ? evs[evs.length-1].id : null;
    O.S.years.delete(O.ykey(O.S.run.run_id,125));
    return {n:evs.length,last:O.S.selEvent,t:O.S.t,mode:O.S.playMode};
  })()`);
  ok("P14a 事件模式停在 124 末条", primed && primed.t === 124 && primed.mode === "events" && primed.n > 0, JSON.stringify(primed));
  ok("P14 事件模式点播放", await clickSel("#b-play"));
  await sleep(400);
  await release();
  await sleep(600);
  const evFail = await ev("({t:window.__obs.S.t,playing:window.__obs.S.playing,timer:window.__obs.S.timer,mode:window.__obs.S.playMode,btn:document.getElementById('b-play').textContent})");
  ok("P15 events/500 诚实暂停", evFail && evFail.playing === false && evFail.timer == null && evFail.mode === "events",
    JSON.stringify(evFail));
  await shot("r2-events-500.png");
  await arm("mode=hold&suffix=/year/125");
  await release();
  if (await clickSel("#b-retry-year")) await sleep(800);
  const evRetry = await ev("({t:window.__obs.S.t,has:!!window.__obs.S.years.get(window.__obs.ykey(window.__obs.S.run.run_id,125)),playing:window.__obs.S.playing})");
  ok("P16 events 重试可恢复", evRetry && evRetry.has === true, JSON.stringify(evRetry));

  await ev("window.__obs.setPlaying(false)");
  await openAt("#tab=world&run=preset-exp06-recip1000&t=1");
  const empty = await ev(`(function(){
    var O=window.__obs; var rec=O.S.years.get(O.ykey(O.S.run.run_id,1));
    var n=rec&&rec.events?rec.events.length:-1;
    var blob=(document.getElementById('dir-mode-note').innerText||'')+(document.getElementById('year-summary').innerText||'');
    return {t:O.S.t,n:n,pop:rec&&rec.agg&&rec.agg.pop,bands:rec&&rec.agg&&rec.agg.bands,ok:n===0&&/没有可核实事件/.test(blob)};
  })()`);
  ok("P17 空态 t1", empty && empty.ok && empty.t === 1 && empty.n === 0 && empty.pop === 116 && empty.bands === 6, JSON.stringify(empty));

  const aid = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(83);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,83));
    var e=(rec.events||[]).find(function(x){return x.id==='t83-aid-3';}) || (rec.events||[]).find(function(x){return x.type==='aid';});
    if(!e) return {ok:false};
    await O.focusEvent(Object.assign({},e,{t:83}));
    return {ok:true,t:O.S.t,id:e.id,cell:O.S.selCell,eCell:e.cell};
  })()`);
  ok("P18 原援助跳 83 不倒退", aid && aid.ok && aid.t === 83 && aid.cell === aid.eCell, JSON.stringify(aid));

  const share = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(125);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,125));
    var e=(rec.events||[]).find(function(x){return x.id==='t125-share-1';});
    if(!e) return {ok:false};
    await O.focusEvent(Object.assign({},e,{t:125}));
    return {ok:true,cell:O.S.selCell,fx:!!document.querySelector('#map .fx-hot, #fx-overlay')};
  })()`);
  ok("P19 t125-share-1 仍锚 0 格", share && share.ok && share.cell === 0, JSON.stringify(share));

  const split = await ev(`(async function(){
    var O=window.__obs; var runs=O.S.runs||[];
    var r=runs.find(function(x){return (x.run_id||'').indexOf('s4242')>=0;});
    if(!r) return {ok:false,why:'no-exp03'};
    await O.openRun(r.run_id);
    var max=r.years_recorded||0;
    for (var t=0;t<=max;t++){
      if(!O.S.years.has(O.ykey(r.run_id,t))){
        try { O.S.years.set(O.ykey(r.run_id,t), await O.api('/api/runs/'+r.run_id+'/year/'+t)); }
        catch(e){ continue; }
      }
      var rec=O.S.years.get(O.ykey(r.run_id,t));
      var e=((rec&&rec.events)||[]).find(function(x){return x.type==='split';});
      if(e){
        await O.focusEvent(Object.assign({},e,{t:t}));
        return {ok:true,t:t,selCell:O.S.selCell,text:(document.getElementById('director-card-body').innerText||'')};
      }
    }
    return {ok:false,why:'no-split'};
  })()`);
  ok("P20 EXP03 分裂不定位", split && split.ok && split.selCell == null, JSON.stringify(split).slice(0, 220));
  await shot("r2-exp03-split.png");

  ws.close();
} catch (e) {
  out.push("FAIL CDP :: " + (e && e.stack ? e.stack.split("\n")[0] : e));
} finally {
  chrome.kill();
  try { await fetch(PROXY + "/__test/release"); } catch (e) { /* ignore */ }
}
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
