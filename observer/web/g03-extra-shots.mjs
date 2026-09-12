#!/usr/bin/env node
/** G03 补截图：无事件年、援助、回助、开局。 */
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g03");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9336;
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`,
  "--user-data-dir=/tmp/g03-extra-shots",
  "--window-size=1440,1100",
  "http://127.0.0.1:8772/static/index.html#tab=world&run=preset-exp06-recip1000&t=0",
], { stdio: "ignore" });
const out = [];
const ok = (n, c, d) => out.push((c ? "PASS" : "FAIL") + " " + n + (d ? " :: " + d : ""));
try {
  await sleep(1400);
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
  await sleep(3000);
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(SHOT, name), Buffer.from(r.result.data, "base64"));
    ok("shot " + name, true, "screenshots/g03/" + name);
  };
  const emptyMeta = await ev(`(async function(){
    var O=window.__obs; await O.openRun('preset-exp06-recip1000'); await O.gotoYear(1);
    document.getElementById('mode-year').click();
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,1));
    var n=rec && rec.events ? rec.events.length : -1;
    var note=(document.getElementById('dir-mode-note')||{}).innerText||'';
    var evs=(document.getElementById('events')||{}).innerText||'';
    var sum=(document.getElementById('year-summary')||{}).innerText||'';
    return {t:O.S.t,n:n,pop:rec&&rec.agg&&rec.agg.pop,bands:rec&&rec.agg&&rec.agg.bands,blob:note+evs+sum};
  })()`);
  ok("empty-year is t1 with 0 events", !!(emptyMeta && emptyMeta.t === 1 && emptyMeta.n === 0), JSON.stringify(emptyMeta));
  ok("empty-year copy", !!(emptyMeta && emptyMeta.n === 0 && /没有可核实事件/.test(emptyMeta.blob || "")), (emptyMeta && emptyMeta.blob || "").slice(0, 160));
  await shot("desktop-empty-year.png");

  const aid = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(83);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,83));
    var e=(rec.events||[]).find(function(x){return x.type==='aid' && !x.repay;});
    if(!e) return {ok:false};
    await O.focusEvent(Object.assign({},e,{t:83}));
    return {ok:true,id:e.id,cell:e.cell,sel:O.S.selCell,repay:!!e.repay};
  })()`);
  ok("aid focus cell", aid && aid.ok && aid.sel === aid.cell, JSON.stringify(aid));
  await shot("desktop-aid.png");

  const repay = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(125);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,125));
    var e=(rec.events||[]).find(function(x){return x.type==='aid' && x.repay;});
    if(!e){
      for(var t=80;t<=150;t++){
        if(!O.S.years.has(O.ykey(O.S.run.run_id,t))){
          try{O.S.years.set(O.ykey(O.S.run.run_id,t), await O.api('/api/runs/'+O.S.run.run_id+'/year/'+t));}catch(err){continue;}
        }
        rec=O.S.years.get(O.ykey(O.S.run.run_id,t));
        e=((rec&&rec.events)||[]).find(function(x){return x.type==='aid' && x.repay;});
        if(e){ await O.focusEvent(Object.assign({},e,{t:t})); return {ok:true,t:t,id:e.id,cell:e.cell,sel:O.S.selCell}; }
      }
      return {ok:false};
    }
    await O.focusEvent(Object.assign({},e,{t:125}));
    return {ok:true,t:125,id:e.id,cell:e.cell,sel:O.S.selCell};
  })()`);
  ok("repay distinct", repay && repay.ok && repay.sel === repay.cell, JSON.stringify(repay));
  await shot("desktop-repay.png");

  await ev("(async function(){var O=window.__obs; await O.gotoYear(4); var rec=O.S.years.get(O.ykey(O.S.run.run_id,4)); var e=(rec.events||[])[0]; if(e) await O.focusEvent(Object.assign({},e,{t:4})); return true;})()");
  await sleep(80);
  await shot("desktop-migrate-kf1.png");
  await sleep(400);
  await shot("desktop-migrate-kf2.png");

  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await sleep(400);
  await ev("(async function(){var O=window.__obs; await O.gotoYear(1); document.getElementById('mode-year').click(); return O.S.years.get(O.ykey(O.S.run.run_id,1)).events.length;})()");
  await sleep(300);
  await shot("mobile-390-empty-year.png");
  ws.close();
} catch (e) {
  out.push("FAIL :: " + (e && e.stack ? e.stack.split("\n")[0] : e));
} finally {
  chrome.kill();
}
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
