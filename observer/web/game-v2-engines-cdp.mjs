#!/usr/bin/env node
/** 8788 obs-1.8：六引擎向导、EXP01 未记录、键盘跳年、刷新 hash。 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "game-v2");
mkdirSync(SHOT, { recursive: true });
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9342;
const PAGE = "http://127.0.0.1:8788/static/index.html?v=game-v2-eng#tab=runs";
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`,
  "--user-data-dir=/tmp/game-v2-eng-cdp",
  "--window-size=1440,1100",
  PAGE,
], { stdio: "ignore" });
const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

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
    return new Promise((res) => { pending.set(id, res); ws.send(JSON.stringify({ id, method, params })); });
  };
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await sleep(2800);
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text || "err" };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    const b64 = r.result && r.result.data;
    if (!b64) { ok("shot " + name, false, "no data"); return; }
    writeFileSync(join(SHOT, name), Buffer.from(b64, "base64"));
    ok("shot " + name, true, "screenshots/game-v2/" + name);
  };

  const forge = await ev(`(function(){
    var sel=document.getElementById('f-engine');
    var opts=[].slice.call(sel?sel.options:[]).map(function(o){return o.value;});
    var O=window.__obs;
    if(sel){ sel.value='exp01'; O.syncEngineForm(); }
    return {opts:opts, api:(O.S.cfg&&O.S.cfg.api_version)||'',
      sigmaHidden: !!(document.getElementById('f-sigma-wrap')&&document.getElementById('f-sigma-wrap').hidden),
      mortHidden: !!(document.getElementById('f-mort-wrap')&&document.getElementById('f-mort-wrap').hidden),
      note:(document.getElementById('forge-engine-note')||{}).textContent||''};
  })()`);
  ok("E1 向导列出六引擎且默认能力来自后台",
    forge && forge.opts.join(",") === "exp01,exp02,exp03,exp04,exp05,exp06"
    && forge.api === "obs-1.8" && forge.sigmaHidden && forge.mortHidden,
    JSON.stringify(forge));
  await shot("forge-six-engines.png");

  const exp01 = await ev(`(async function(){
    var O=window.__obs;
    var run=(O.S.runs||[]).find(function(r){return r.engine==='exp01' && r.status==='done';});
    if(!run) return {ok:false};
    await O.openRun(run.run_id);
    await O.gotoYear(1);
    var rec=O.S.years.get(run.run_id+'|1');
    var units=document.querySelectorAll('#map .unit[data-unit="group-rep"]').length;
    var side=document.getElementById('side-now')?document.getElementById('side-now').textContent:'';
    return {ok:true, run:run.run_id, t:O.S.t, units:units, bands:rec&&rec.agg&&rec.agg.bands,
      pop:rec&&rec.agg&&rec.agg.pop, births: rec&&rec.year&&rec.year.births_cum,
      unrecorded: /未记录/.test(side), hash: location.hash};
  })()`);
  ok("E2 EXP01 可回放：人物在场且出生写未记录",
    exp01 && exp01.ok && exp01.units === exp01.bands && exp01.units > 0
    && exp01.births == null && exp01.unrecorded,
    JSON.stringify(exp01));
  await shot("exp01-unrecorded.png");

  const keys = await ev(`(async function(){
    var O=window.__obs;
    O.showTab('world');
    if(document.activeElement && document.activeElement.blur) document.activeElement.blur();
    await O.gotoYear(0);
    var before=O.S.t;
    document.body.dispatchEvent(new KeyboardEvent('keydown', {key:'ArrowRight', bubbles:true}));
    await new Promise(function(r){setTimeout(r, 800);});
    var after=O.S.t;
    return {before:before, after:after, hash:location.hash, advanced: after>before};
  })()`);
  ok("E3 键盘右方向可跳年", keys && keys.advanced, JSON.stringify(keys));

  const restore = await ev(`(async function(){
    var O=window.__obs;
    var run=O.S.run && O.S.run.run_id;
    await O.gotoYear(4);
    var h=location.hash;
    return {run:run, t:O.S.t, hashHasRun: h.indexOf(run)>=0, hashHasT: /t=4/.test(h)};
  })()`);
  ok("E4 跳年后 hash 含 run 与 t=4 可刷新恢复",
    restore && restore.t === 4 && restore.hashHasRun && restore.hashHasT,
    JSON.stringify(restore));

  const xss = await ev(`(function(){
    var O=window.__obs;
    return {esc: O.esc('<img src=x onerror=alert(1)>') === '&lt;img src=x onerror=alert(1)&gt;'};
  })()`);
  ok("E5 HTML 转义仍生效", xss && xss.esc, JSON.stringify(xss));
} catch (e) {
  ok("engines cdp crashed", false, String(e && e.stack || e));
} finally {
  chrome.kill("SIGKILL");
  const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
  out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
  process.stdout.write(out.join("\n") + "\n");
  process.exit(nf ? 1 : 0);
}
