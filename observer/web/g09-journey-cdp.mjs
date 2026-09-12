#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g09");
mkdirSync(SHOT, { recursive: true });
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9342;
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-sandbox",
  `--remote-debugging-port=${PORT}`, "--user-data-dir=/tmp/g09-cdp", "--window-size=1440,1000",
  "http://127.0.0.1:8772/static/index.html?g09=1#tab=world&run=preset-exp06-recip1000&t=0"], { stdio: "ignore" });
const out = [];
const ok = (n, c, d) => out.push((c ? "PASS" : "FAIL") + " " + n + (d ? " :: " + d : ""));
try {
  await sleep(1400);
  const list = await fetch("http://127.0.0.1:" + PORT + "/json/list").then((r) => r.json());
  const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let seq = 0; const pend = new Map();
  ws.addEventListener("message", (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) pend.get(m.id)(m); });
  await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
  const send = (method, params = {}) => { const id = ++seq; return new Promise((r) => { pend.set(id, r); ws.send(JSON.stringify({ id, method, params })); }); };
  await send("Runtime.enable"); await send("Page.enable");
  await sleep(3000);
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(SHOT, name), Buffer.from(r.result.data, "base64"));
    ok("shot " + name, true, "screenshots/g09/" + name);
  };
  const t1 = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(1);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,1));
    return {t:O.S.t,n:(rec.events||[]).length,pop:rec.agg.pop,bands:rec.agg.bands};
  })()`);
  ok("J1 t1 空事件 116人6群体", t1 && t1.t===1 && t1.n===0 && t1.pop===116 && t1.bands===6, JSON.stringify(t1));
  const t4 = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(4);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,4));
    var e=(rec.events||[]).find(function(x){return x.type==='migrate';});
    if(!e) return {ok:false};
    await O.focusEvent(Object.assign({},e,{t:4}));
    return {from:e.from,to:e.to,id:e.id,sel:O.S.selCell};
  })()`);
  ok("J2 t4 迁移端点 18→10", t4 && t4.from===18 && t4.to===10, JSON.stringify(t4));
  const t52 = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(52);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,52));
    var e=(rec.events||[]).find(function(x){return x.type==='split';});
    if(!e) return {ok:false};
    await O.focusEvent(Object.assign({},e,{t:52}));
    return {id:e.id,cell:e.cell==null,selCell:O.S.selCell,text:(document.getElementById('director-card-body')||{}).innerText};
  })()`);
  ok("J3 t52 split 无事件格不定位", t52 && t52.ok!==false && t52.selCell==null, JSON.stringify(t52).slice(0,200));
  const t83 = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(83);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,83));
    var e=(rec.events||[]).find(function(x){return x.id==='t83-aid-3';});
    await O.focusEvent(Object.assign({},e,{t:83}));
    return {t:O.S.t,kcal:e.kcal,id:e.id};
  })()`);
  ok("J4 t83-aid-3 kcal 6457", t83 && t83.t===83 && t83.kcal===6457, JSON.stringify(t83));
  const t124 = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(124);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,124));
    var kcal=(rec.events||[]).filter(function(e){return e.repay;}).reduce(function(s,e){return s+(e.kcal||0);},0);
    return {repay:rec.recip&&rec.recip.repay_transfers, changed:rec.recip&&rec.recip.changed, kcal:kcal};
  })()`);
  ok("J5 t124 回助与 changed 分列", t124 && t124.changed===0 && t124.repay>=1 && t124.kcal===1011984, JSON.stringify(t124));
  const t125 = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(125);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,125));
    var e=(rec.events||[]).find(function(x){return x.id==='t125-share-1';});
    await O.focusEvent(Object.assign({},e,{t:125}));
    return {cell:e.cell,sel:O.S.selCell};
  })()`);
  ok("J6 t125-share-1 锚格 0", t125 && t125.cell===0 && t125.sel===0, JSON.stringify(t125));
  await shot("journey-t125.png");
  const exp = await ev(`(function(){
    var O=window.__obs; var rec=O.S.years.get(O.ykey(O.S.run.run_id,O.S.t));
    var p=window.LibraryLogic.exportRecord(O.S.run,O.S.t,rec,{});
    return {forbid:window.LibraryLogic.hasForbidden(p), hasToken:!!p.token, year:p.year};
  })()`);
  ok("J7 导出无令牌", exp && exp.forbid===false && exp.hasToken===false, JSON.stringify(exp));
  const hash = await ev("location.hash");
  ok("J8 URL 含 run 与 t", /run=/.test(String(hash)) && /t=125/.test(String(hash)), String(hash));
  ws.close();
} catch (e) { out.push("FAIL " + (e && e.stack ? e.stack.split("\n")[0] : e)); }
finally { chrome.kill(); }
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
