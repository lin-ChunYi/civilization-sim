#!/usr/bin/env node
/** 对各已接入引擎走一遍向导确认提交（短年数）。失败如实记录，不拿 EXP03 冒充。 */
import { spawn } from "node:child_process";
import { setTimeout as sleep } from "node:timers/promises";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9345;
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-sandbox",
  `--remote-debugging-port=${PORT}`, "--user-data-dir=/tmp/g09-create-cdp", "--window-size=1200,900",
  "http://127.0.0.1:8772/static/index.html?create=1#tab=runs"], { stdio: "ignore" });
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
  const engines = await ev("Object.keys((window.__obs.S.cfg&&window.__obs.S.cfg.engines)||{})");
  ok("K0 引擎列表来自 config", Array.isArray(engines) && engines.length > 0, JSON.stringify(engines));
  const want = ["exp03", "exp04", "exp05", "exp06"];
  const missing = want.filter((e) => (engines || []).indexOf(e) < 0);
  ok("K1 EXP01/02 未在列表则不强造", missing.indexOf("exp01") >= 0 || (engines || []).indexOf("exp01") < 0, "missing=" + missing.join(","));
  const created = [];
  for (const name of want) {
    if ((engines || []).indexOf(name) < 0) { ok("K-" + name + " 未接入（不冒充）", true, "skip"); continue; }
    const r = await ev(`(async function(){
      var O=window.__obs; O.showTab('runs');
      var eng=document.getElementById('f-engine'); eng.value=${JSON.stringify(name)}; eng.dispatchEvent(new Event('change'));
      document.getElementById('f-seed').value=String(Date.now()%100000);
      document.getElementById('f-years').value='5';
      document.getElementById('f-sigma').value='0';
      document.getElementById('f-mort').value='0';
      if(document.getElementById('f-share') && !document.getElementById('f-share-wrap').hidden) document.getElementById('f-share').value='0';
      if(document.getElementById('f-aid') && !document.getElementById('f-aid-wrap').hidden) document.getElementById('f-aid').value='0';
      if(document.getElementById('f-recip') && !document.getElementById('f-recip-wrap').hidden) document.getElementById('f-recip').value='0';
      document.getElementById('f-label').value='qa-'+${JSON.stringify(name)};
      document.getElementById('b-start').click();
      var sum=document.getElementById('forge-summary').innerText;
      if(sum.indexOf(${JSON.stringify(name)})<0) return {ok:false, sum:sum};
      try { await O.confirmStartRun(); }
      catch(e){ return {ok:false, err:String(e)}; }
      return {ok:true, run:O.S.run&&O.S.run.run_id, engine:O.S.run&&O.S.run.engine, t:O.S.t, sum:sum};
    })()`);
    created.push(r);
    ok("K-" + name + " 确认提交", r && r.ok && r.engine === name && r.t === 0, JSON.stringify(r).slice(0, 200));
    await sleep(400);
  }
  void created;
  ws.close();
} catch (e) { out.push("FAIL " + (e && e.stack ? e.stack.split("\n")[0] : e)); }
finally { chrome.kill(); }
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
