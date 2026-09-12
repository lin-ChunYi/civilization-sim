#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g05");
mkdirSync(SHOT, { recursive: true });
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9340;
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-sandbox",
  `--remote-debugging-port=${PORT}`, "--user-data-dir=/tmp/g05-cdp", "--window-size=1440,1000",
  "http://127.0.0.1:8772/static/index.html?g05=1#tab=compare"], { stdio: "ignore" });
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
  await sleep(2800);
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(SHOT, name), Buffer.from(r.result.data, "base64"));
    ok("shot " + name, true, "screenshots/g05/" + name);
  };
  const r = await ev(`(async function(){
    var O=window.__obs; if(O.showTab) O.showTab('compare'); else document.querySelector('[data-tab=compare]').click();
    var runs=O.S.runs||[];
    var a=runs.find(function(x){return (x.run_id||'').indexOf('recip1000')>=0;});
    var b=runs.find(function(x){return (x.run_id||'').indexOf('s4242')>=0;});
    if(!a||!b) return {ok:false,why:'runs'};
    document.getElementById('cmp-a').value=a.run_id;
    document.getElementById('cmp-b').value=b.run_id;
    document.getElementById('cmp-year').value='150';
    var pack=await O.loadCompare();
    var html=document.getElementById('cmp-table').innerText;
    return {ok:true, missA:pack.a.missing, missB:pack.b.missing, html:html.slice(0,200), cfg:document.getElementById('cmp-cfg').innerText};
  })()`);
  ok("D1 exp03 第150年标缺失", r && r.ok && r.missB === true && /缺失/.test(r.html || ""), JSON.stringify(r).slice(0, 280));
  await shot("desktop-compare-missing.png");
  const r2 = await ev(`(async function(){
    var O=window.__obs;
    var a=(O.S.runs||[]).find(function(x){return (x.run_id||'').indexOf('recip1000')>=0;});
    var b=(O.S.runs||[]).find(function(x){return (x.run_id||'').indexOf('recip0')>=0;});
    if(!a||!b) return {ok:false};
    document.getElementById('cmp-a').value=a.run_id;
    document.getElementById('cmp-b').value=b.run_id;
    document.getElementById('cmp-year').value='124';
    var pack=await O.loadCompare();
    return {ok:true, missA:pack.a.missing, missB:pack.b.missing, cfg:document.getElementById('cmp-cfg').innerText, diff:/recip/.test(document.getElementById('cmp-cfg').innerText)};
  })()`);
  ok("D2 recip1000 vs recip0 同年都有记录并标出 recip 差异", r2 && r2.ok && !r2.missA && !r2.missB && r2.diff, JSON.stringify(r2).slice(0, 240));
  await shot("desktop-compare-recip.png");
  ws.close();
} catch (e) { out.push("FAIL " + (e && e.stack ? e.stack.split("\n")[0] : e)); }
finally { chrome.kill(); }
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
