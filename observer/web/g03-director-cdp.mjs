#!/usr/bin/env node
/** G03：真实指针/按钮 + 桌面/手机截图。不编 FPS。 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g03");
mkdirSync(SHOT, { recursive: true });
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9335;
const PAGE = "http://127.0.0.1:8772/static/index.html#tab=world";
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`,
  "--user-data-dir=/tmp/g03-director-cdp",
  "--window-size=1440,1100",
  PAGE,
], { stdio: "ignore" });

const out = [];
const ok = (name, cond, detail) => {
  out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));
};

try {
  await sleep(1400);
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
  await sleep(3200);

  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) {
      const t = r.result.exceptionDetails.text || "err";
      return { __err: t };
    }
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    const b64 = r.result && r.result.data;
    if (!b64) { ok("shot " + name, false, "no data"); return; }
    writeFileSync(join(SHOT, name), Buffer.from(b64, "base64"));
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

  const ready = await ev("!!(window.__obs && window.__obs.S && window.__obs.S.run)");
  ok("B0 页面已加载运行", !!ready, JSON.stringify(ready));

  const opened = await ev(`(async function(){
    var O=window.__obs; var runs=O.S.runs||[];
    var r=runs.find(function(x){return (x.run_id||'').indexOf('exp06-recip1000')>=0;}) ||
      runs.find(function(x){return x.engine==='exp06' && x.kind==='preset';});
    if(!r) return 'no-exp06';
    await O.openRun(r.run_id);
    return r.run_id;
  })()`);
  ok("B1 打开 exp06", typeof opened === "string" && opened !== "no-exp06", String(opened));

  ok("B2 点只看有记录的事件", await clickSel("#mode-events"));
  await sleep(200);
  const mode = await ev("window.__obs.S.playMode+'|'+location.hash");
  ok("B3 模式与 URL", typeof mode === "string" && mode.indexOf("events") >= 0, String(mode));

  ok("B4 点下一事件年", await clickSel("#b-next-ev"));
  await sleep(600);
  const afterNext = await ev("({t:window.__obs.S.t,ev:window.__obs.S.selEvent,card:(document.getElementById('director-card-body')||{}).innerText})");
  ok("B5 落到事件年并有选中卡", afterNext && afterNext.t > 0 && afterNext.card, JSON.stringify(afterNext).slice(0, 180));
  await shot("desktop-event-year.png");

  const share = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(125);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,125));
    var e=(rec.events||[]).find(function(x){return x.id==='t125-share-1';});
    if(!e) e=(rec.events||[]).find(function(x){return x.type==='share' && x.cell===0;});
    if(!e) return {ok:false};
    await O.focusEvent(Object.assign({},e,{t:125}));
    return {ok:true, cell:O.S.selCell, id:e.id, fx:!!document.querySelector('#map .fx-hot, #fx-overlay')};
  })()`);
  ok("B6 t125-share-1 锚 0 格", share && share.ok && share.cell === 0, JSON.stringify(share));
  await shot("desktop-t125-share-1.png");

  ok("B7 点暂停", await clickSel("#b-play"));
  await sleep(80);
  ok("B8 再点暂停/播放切停", await clickSel("#b-play"));
  const paused = await ev("({playing:window.__obs.S.playing,gen:window.__obs.S.fxGen,timers:window.__obs.S.fxTimers.length})");
  ok("B9 暂停后 playing=false", paused && paused.playing === false, JSON.stringify(paused));
  await shot("desktop-paused.png");

  const split = await ev(`(async function(){
    var O=window.__obs; var runs=O.S.runs||[];
    var r=runs.find(function(x){return (x.run_id||'').indexOf('s4242')>=0;});
    if(!r) return {ok:false, why:'no-exp03'};
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
        var side=(document.getElementById('side-sel')||{}).innerText||'';
        var card=(document.getElementById('director-card-body')||{}).innerText||'';
        return {ok:true,t:t,selCell:O.S.selCell,text:side+card};
      }
    }
    return {ok:false, why:'no-split'};
  })()`);
  ok("B10 EXP03 分裂无定位", split && split.ok && split.selCell == null && /谱系|分裂/.test(split.text || ""), JSON.stringify(split).slice(0, 200));
  await shot("desktop-exp03-split.png");

  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await sleep(400);
  await ev(`(async function(){
    var O=window.__obs; var runs=O.S.runs||[];
    var r=runs.find(function(x){return (x.run_id||'').indexOf('exp06-recip1000')>=0;});
    if(r) await O.openRun(r.run_id);
    document.getElementById('mode-events') && document.getElementById('mode-events').click();
    document.getElementById('b-next-ev') && document.getElementById('b-next-ev').click();
    return true;
  })()`);
  await sleep(700);
  const mobileW = await ev("document.documentElement.clientWidth");
  ok("B11 手机宽度 390", mobileW === 390, "w=" + mobileW);
  await shot("mobile-390-event.png");

  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  const t0 = await ev("performance.now()");
  await ev(`(async function(){
    var O=window.__obs; document.getElementById('mode-year').click();
    var t1=performance.now();
    await O.gotoYear(48); await O.gotoYear(83); await O.gotoYear(124); await O.gotoYear(0);
    window.__g03gotoMs = performance.now()-t1;
    return window.__g03gotoMs;
  })()`);
  const ms = await ev("window.__g03gotoMs");
  ok("B12 快速换年耗时已测（非编造 FPS）", typeof ms === "number" && ms >= 0, Number(ms).toFixed(1) + "ms for 4 gotos");
  await shot("desktop-year-mode.png");
  const unused = t0;

  ws.close();
} catch (e) {
  out.push("FAIL CDP :: " + (e && e.stack ? e.stack.split("\n")[0] : e));
} finally {
  chrome.kill();
}
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
