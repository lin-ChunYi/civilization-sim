#!/usr/bin/env node
/** G04 返工：真实鼠标点双向边/文字节点，换年清卡。 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g04");
mkdirSync(SHOT, { recursive: true });
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9343;
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-sandbox",
  `--remote-debugging-port=${PORT}`, "--user-data-dir=/tmp/g04-fix-cdp", "--window-size=1440,1100",
  "http://127.0.0.1:8772/static/index.html?g04f=1#tab=network&run=preset-exp06-recip1000&t=124"],
  { stdio: "ignore" });
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
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await sleep(3200);
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
  const click = async (x, y) => {
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x: x, y: y, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x, y: y, button: "left", clickCount: 1 });
  };
  await ev("window.__obs && window.__obs.showTab('network')");
  await sleep(400);
  const pair = await ev(`(function(){
    var O=window.__obs; var edges=(O.S.relations&&O.S.relations.edges)||[];
    for (var i=0;i<edges.length;i++){
      for (var j=i+1;j<edges.length;j++){
        if (String(edges[i].donor)===String(edges[j].receiver) && String(edges[i].receiver)===String(edges[j].donor))
          return {i:i,j:j,a:edges[i].donor,b:edges[i].receiver};
      }
    }
    return {i:0,j:1};
  })()`);
  ok("C0 找到互反边", pair && pair.i != null && pair.j != null, JSON.stringify(pair));
  const pt = await ev(`(function(){
    var knobs=document.querySelectorAll('#net-svg .net-edge-knob');
    function mid(el){
      if(!el) return null;
      var r=el.getBoundingClientRect();
      return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height,ei:el.getAttribute('data-ei')};
    }
    return {a:mid(knobs[${pair && pair.i != null ? pair.i : 0}]), b:mid(knobs[${pair && pair.j != null ? pair.j : 1}]), n:knobs.length};
  })()`);
  ok("C1 两条边中点可采样且不重合", pt && pt.a && pt.b && (Math.abs(pt.a.x-pt.b.x)+Math.abs(pt.a.y-pt.b.y))>8, JSON.stringify(pt));
  const hitA = pt && pt.a ? await ev("({tag:document.elementFromPoint("+pt.a.x+","+pt.a.y+")&&document.elementFromPoint("+pt.a.x+","+pt.a.y+").className,ei:document.elementFromPoint("+pt.a.x+","+pt.a.y+")&&document.elementFromPoint("+pt.a.x+","+pt.a.y+").getAttribute('data-ei')})") : null;
  if (pt && pt.a) await click(Math.round(pt.a.x), Math.round(pt.a.y));
  await sleep(250);
  const cardA = await ev("document.getElementById('net-edge-card').innerText");
  if (pt && pt.b) await click(Math.round(pt.b.x), Math.round(pt.b.y));
  await sleep(250);
  const cardB = await ev("document.getElementById('net-edge-card').innerText");
  ok("C1b elementFromPoint 边中点", hitA && hitA.ei != null, JSON.stringify(hitA));
  ok("C2 实际点击两条方向得到不同详情", cardA && cardB && cardA !== cardB && /有向往来/.test(cardA) && /有向往来/.test(cardB),
    JSON.stringify({ a: (cardA || "").slice(0, 80), b: (cardB || "").slice(0, 80) }));
  await shot("two-way-edge-card.png");
  const lab = await ev(`(function(){
    var hit=document.querySelector('#net-svg .net-label-hit');
    var cir=document.querySelector('#net-svg .net-node circle');
    var t=document.querySelector('#net-svg .net-node text');
    var r=(hit&&hit.getBoundingClientRect().width)?hit.getBoundingClientRect():(cir?cir.getBoundingClientRect():null);
    if(!r) return null;
    return {x:r.x+r.width/2,y:r.y+r.height/2,name:t&&t.textContent,w:r.width,h:r.height};
  })()`);
  if (lab && lab.x) await click(lab.x, lab.y);
  await sleep(500);
  const afterLab = await ev("({tab:document.getElementById('tab-world').hidden===false, band:window.__obs.S.selBand, rail:document.getElementById('pane-dossier')&&!document.getElementById('pane-dossier').hidden})");
  ok("C3 点击文字标签打开档案", afterLab && afterLab.band, JSON.stringify({ lab: lab, after: afterLab }));
  await ev("window.__obs.showTab('network')");
  await sleep(200);
  await ev(`(function(){
    var O=window.__obs; var hits=document.querySelectorAll('#net-svg .net-edge-hit');
    if(hits[0]) hits[0].dispatchEvent(new MouseEvent('click',{bubbles:true}));
  })()`);
  await sleep(150);
  const before = await ev("document.getElementById('net-edge-card').hidden===false");
  const inp = await ev(`(function(){
    var n=document.getElementById('net-year');
    n.value='83';
    n.dispatchEvent(new Event('change',{bubbles:true}));
    return n.value;
  })()`);
  await sleep(800);
  const afterYr = await ev("({t:window.__obs.S.t, hidden:document.getElementById('net-edge-card').hidden, html:document.getElementById('net-edge-card').innerHTML, totals:document.getElementById('net-totals').innerText})");
  ok("C4 换到 83 年旧边卡关闭", before === true && afterYr && afterYr.t === 83 && afterYr.hidden === true,
    JSON.stringify({ inp: inp, before: before, after: afterYr }));
  await shot("year-83-cleared-card.png");
  ws.close();
} catch (e) { out.push("FAIL " + (e && e.stack ? e.stack.split("\n")[0] : e)); }
finally { chrome.kill(); }
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
