#!/usr/bin/env node
/** G04 真实页面：at_year=124 关系网、档案不含 131、t83-aid-3 跳转。 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g04");
mkdirSync(SHOT, { recursive: true });
const PAGE = "http://127.0.0.1:8772/static/index.html";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9339;
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`, "--user-data-dir=/tmp/g04-cdp",
  "--window-size=1440,1100",
  PAGE + "?g04=" + Date.now() + "#tab=world&run=preset-exp06-recip1000&t=124",
], { stdio: "ignore" });
const out = [];
const ok = (n, c, d) => out.push((c ? "PASS" : "FAIL") + " " + n + (d ? " :: " + d : ""));
try {
  await sleep(1500);
  const list = await fetch("http://127.0.0.1:" + PORT + "/json/list").then((r) => r.json());
  const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let seq = 0; const pend = new Map();
  ws.addEventListener("message", (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) pend.get(m.id)(m); });
  await new Promise((res, rej) => { ws.addEventListener("open", res); ws.addEventListener("error", rej); });
  const send = (method, params = {}) => { const id = ++seq; return new Promise((r) => { pend.set(id, r); ws.send(JSON.stringify({ id, method, params })); }); };
  await send("Runtime.enable"); await send("Page.enable");
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
    ok("shot " + name, true, "screenshots/g04/" + name);
  };
  ok("G0 加载", !!(await ev("window.__obs && window.__obs.S && window.__obs.S.run")));
  const rel = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(124); O.S.bandScope='as_of';
    await O.loadRelations();
    var d=O.S.relations||{};
    var sc=d.history_scope||{};
    var edges=d.edges||[];
    var ids=JSON.stringify(edges);
    return {t:O.S.t, mode:sc.mode, at:sc.at_year, edges:edges.length, has131:ids.indexOf('t131')>=0,
      donorType: edges[0] ? typeof edges[0].donor : 'none'};
  })()`);
  ok("G1 124 关系 as_of 且边 id 为字符串", rel && rel.t === 124 && rel.mode === "as_of_year" && rel.at === 124 && rel.donorType === "string", JSON.stringify(rel));
  await ev("window.__obs.showTab('network')");
  await sleep(400);
  ok("G2 关系网 SVG 有节点", !!(await ev("document.querySelectorAll('#net-svg .net-node').length>0")));
  await shot("desktop-network-t124.png");
  const band = await ev(`(async function(){
    var O=window.__obs; var id='7567856178022945294';
    O.S.selBand=id; O.S.bandScope='as_of';
    await O.loadBand(id);
    var d=O.S.band||{}; var traj=JSON.stringify(d.trajectory||[]);
    return {scope:d.history_scope&&d.history_scope.mode, last:d.last_seen, has125:traj.indexOf('[125')>=0, has131:traj.indexOf('[131')>=0};
  })()`);
  ok("G3 档案 124 不含 125/131", band && band.scope === "as_of_year" && band.has125 === false && band.has131 === false, JSON.stringify(band));
  const jump = await ev(`(async function(){
    var O=window.__obs; await O.gotoYear(83);
    var rec=O.S.years.get(O.ykey(O.S.run.run_id,83));
    var e=(rec.events||[]).find(function(x){return x.id==='t83-aid-3';});
    if(!e) return {ok:false};
    await O.focusEvent(Object.assign({},e,{t:83}));
    return {t:O.S.t, id:e.id, cell:O.S.selCell, eCell:e.cell};
  })()`);
  ok("G4 t83-aid-3 跳 83 不是 82", jump && jump.t === 83 && jump.id === "t83-aid-3", JSON.stringify(jump));
  const exp03 = await ev(`(async function(){
    var O=window.__obs; var r=(O.S.runs||[]).find(function(x){return (x.run_id||'').indexOf('s4242')>=0;});
    if(!r) return {ok:false};
    await O.openRun(r.run_id); await O.gotoYear(50); O.S.bandScope='as_of';
    await O.loadRelations();
    var d=O.S.relations||{};
    return {edges:(d.edges||[]).length, kcal:d.totals&&d.totals.kcal};
  })()`);
  ok("G5 EXP03 关系边为 0 不编造", exp03 && exp03.edges === 0, JSON.stringify(exp03));
  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await ev("window.__obs.showTab('network')");
  await sleep(300);
  ok("G6 手机宽度", (await ev("document.documentElement.clientWidth")) === 390);
  await shot("mobile-network-390.png");
  ws.close();
} catch (e) {
  out.push("FAIL CDP :: " + (e && e.stack ? e.stack.split("\n")[0] : e));
} finally { chrome.kill(); }
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
