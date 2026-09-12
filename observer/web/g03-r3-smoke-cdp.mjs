#!/usr/bin/env node
/** G03_R3 受影响操作复核：模式切换、原援助 83、缺地点 split、手机宽度。8774 透传，不注入 404。 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g03");
mkdirSync(SHOT, { recursive: true });
const PAGE = "http://127.0.0.1:8774/static/index.html";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9338;
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`,
  "--user-data-dir=/tmp/g03-r3-smoke",
  "--window-size=1440,1100",
  PAGE + "?r3=" + Date.now() + "#tab=world&run=preset-exp06-recip1000&t=124",
], { stdio: "ignore" });
const out = [];
const ok = (n, c, d) => out.push((c ? "PASS" : "FAIL") + " " + n + (d ? " :: " + d : ""));
try {
  await sleep(1600);
  const list = await fetch("http://127.0.0.1:" + PORT + "/json/list").then((r) => r.json());
  const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
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
  await sleep(2800);
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
  ok("S0 已加载", !!(await ev("window.__obs && window.__obs.S && window.__obs.S.run")));
  const mode = await ev(`(function(){
    document.getElementById('mode-events').click();
    var a=window.__obs.S.playMode;
    document.getElementById('mode-year').click();
    var b=window.__obs.S.playMode;
    return {events:a,year:b,playing:window.__obs.S.playing};
  })()`);
  ok("S1 模式切换不自动播放", mode && mode.events === "events" && mode.year === "year" && mode.playing === false, JSON.stringify(mode));
  const aid = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(83);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,83));
    var e=(rec.events||[]).find(function(x){return x.id==='t83-aid-3';});
    if(!e) return {ok:false};
    await O.focusEvent(Object.assign({},e,{t:83}));
    return {ok:true,t:O.S.t,cell:O.S.selCell,eCell:e.cell,id:e.id};
  })()`);
  ok("S2 原援助 t83-aid-3", aid && aid.ok && aid.t === 83 && aid.cell === aid.eCell, JSON.stringify(aid));
  await shot("r3-aid-83.png");
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
        return {ok:true,t:t,selCell:O.S.selCell,playing:O.S.playing};
      }
    }
    return {ok:false,why:'no-split'};
  })()`);
  ok("S3 缺地点 split 不定位且不自动播放", split && split.ok && split.selCell == null && split.playing === false, JSON.stringify(split));
  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await sleep(300);
  const mob = await ev("({w:document.documentElement.clientWidth,t:window.__obs.S.t,playing:window.__obs.S.playing})");
  ok("S4 手机宽度 390", mob && mob.w === 390 && mob.playing === false, JSON.stringify(mob));
  await shot("r3-mobile-390.png");
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
