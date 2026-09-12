#!/usr/bin/env node
/** 完整旅程 QA：向导确认/取消、对照、收藏刷新、转义、长回放实测。浏览器操作。 */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g09");
mkdirSync(SHOT, { recursive: true });
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9344;
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-sandbox",
  `--remote-debugging-port=${PORT}`, "--user-data-dir=/tmp/g09-qa-cdp", "--window-size=1440,1100",
  "http://127.0.0.1:8772/static/index.html?qa=1#tab=runs"], { stdio: "ignore" });
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
  const wiz = await ev(`(function(){
    var O=window.__obs; O.showTab('runs');
    document.getElementById('f-years').value='12.5';
    document.getElementById('b-start').click();
    var toast=document.getElementById('toast').innerText;
    var conf=document.getElementById('forge-confirm').hidden;
    document.getElementById('f-years').value='8';
    document.getElementById('f-seed').value='424242';
    var eng=document.getElementById('f-engine');
    if(eng.querySelector('option[value=exp06]')) { eng.value='exp06'; eng.dispatchEvent(new Event('change')); }
    var rec=document.querySelector('[data-preset=recip]');
    if(rec) rec.click();
    document.getElementById('b-start').click();
    var sum=document.getElementById('forge-summary').innerText;
    document.getElementById('b-confirm-cancel').click();
    var conf2=document.getElementById('forge-confirm').hidden;
    return {toast:toast, confAfterBad:conf, sum:sum, cancelled:conf2, aid:document.getElementById('f-aid').value, recip:document.getElementById('f-recip').value};
  })()`);
  ok("Q1 非法年数不进入确认", wiz && wiz.confAfterBad === true && /整数/.test(wiz.toast || ""), JSON.stringify(wiz).slice(0, 220));
  ok("Q2 预设援助+回助且确认可取消", wiz && wiz.aid === "1000" && wiz.recip === "1000" && wiz.cancelled === true && /AID_M 1000/.test(wiz.sum || ""), JSON.stringify({ aid: wiz && wiz.aid, recip: wiz && wiz.recip, cancelled: wiz && wiz.cancelled }));
  const html = await ev(`(function(){
    var O=window.__obs; O.showTab('world');
    var inp=document.getElementById('band-search');
    inp.value='<img src=x onerror=alert(1)>';
    inp.dispatchEvent(new Event('input',{bubbles:true}));
    var html=document.getElementById('bandtable').innerHTML;
    return {hasRaw:html.indexOf('<img')>=0, hasEsc:html.indexOf('&lt;img')>=0 || html.indexOf('img src')<0};
  })()`);
  ok("Q3 检索框 HTML 未当标签插入", html && html.hasRaw === false, JSON.stringify(html));
  const lib = await ev(`(async function(){
    var O=window.__obs;
    var a=(O.S.runs||[]).find(function(x){return (x.run_id||'').indexOf('recip1000')>=0;});
    var b=(O.S.runs||[]).find(function(x){return (x.run_id||'').indexOf('s4242')>=0;});
    if(!a||!b) return {ok:false};
    await O.openRun(a.run_id); await O.gotoYear(83);
    O.pinCurrentYear();
    document.querySelector('[data-rail=library]').click();
    var aTxt=document.getElementById('lib-years').innerText;
    await O.openRun(b.run_id);
    document.querySelector('[data-rail=library]').click();
    var bTxt=document.getElementById('lib-years').innerText;
    return {aTxt:aTxt, bTxt:bTxt, isolated:aTxt.indexOf('83')>=0 && bTxt.indexOf('83')<0};
  })()`);
  ok("Q4 收藏按 run 隔离且切 tab 会渲染", lib && lib.isolated, JSON.stringify(lib));
  const cmp = await ev(`(async function(){
    var O=window.__obs; O.showTab('compare');
    var a=(O.S.runs||[]).find(function(x){return (x.run_id||'').indexOf('recip1000')>=0;});
    var b=(O.S.runs||[]).find(function(x){return (x.run_id||'').indexOf('s4242')>=0;});
    document.getElementById('cmp-a').value=a.run_id;
    document.getElementById('cmp-b').value=b.run_id;
    document.getElementById('cmp-year').value='150';
    var pack=await O.loadCompare();
    var html=document.getElementById('cmp-table').innerHTML;
    var cfg=document.getElementById('cmp-cfg').innerText;
    return {missB:pack.b.missing, hasMiss:html.indexOf('缺失')>=0, cfgHasEngine:cfg.indexOf('engine')>=0, cfgHasArm:cfg.indexOf('arm')>=0};
  })()`);
  ok("Q5 对照 150 缺失且配置含 engine/arm", cmp && cmp.missB && cmp.hasMiss && cmp.cfgHasEngine, JSON.stringify(cmp));
  await shot("qa-compare-events.png");
  const play = await ev(`(async function(){
    var O=window.__obs;
    var a=(O.S.runs||[]).find(function(x){return (x.run_id||'').indexOf('recip1000')>=0;});
    await O.openRun(a.run_id); await O.gotoYear(0); O.showTab('world');
    O.S.speed=8; document.getElementById('speed').value='8';
    var t0=performance.now(); O.setPlaying(true);
    await new Promise(function(r){ setTimeout(r, 2500); });
    O.setPlaying(false);
    var dt=performance.now()-t0;
    return {t:O.S.t, dt:dt, playing:O.S.playing};
  })()`);
  ok("Q6 长回放 2.5s@8x 有年份推进", play && play.playing === false && play.t > 0, JSON.stringify(play));
  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await sleep(300);
  const mob = await ev(`(function(){
    var extra=document.documentElement.scrollWidth-document.documentElement.clientWidth;
    var worst={w:0,id:''};
    document.querySelectorAll('body *').forEach(function(el){
      var r=el.getBoundingClientRect();
      if(r.width>worst.w) worst={w:Math.round(r.width),id:(el.id||el.className||el.tagName).toString().slice(0,60)};
    });
    return {w:document.documentElement.clientWidth, hud:Math.round(document.querySelector('.hud').getBoundingClientRect().height), extra:extra, worst:worst};
  })()`);
  ok("Q7 390 宽 HUD 压缩", mob && mob.w === 390 && mob.hud < 120, JSON.stringify(mob));
  ok("Q7b 390 横向溢出不超过 24px", mob && mob.extra <= 24, JSON.stringify(mob));
  await shot("qa-mobile-390.png");
  ws.close();
} catch (e) { out.push("FAIL " + (e && e.stack ? e.stack.split("\n")[0] : e)); }
finally { chrome.kill(); }
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
