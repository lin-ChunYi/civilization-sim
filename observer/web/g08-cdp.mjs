#!/usr/bin/env node
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const here = dirname(fileURLToPath(import.meta.url));
const SHOT = join(here, "screenshots", "g08");
mkdirSync(SHOT, { recursive: true });
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9341;
const chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-sandbox",
  `--remote-debugging-port=${PORT}`, "--user-data-dir=/tmp/g08-cdp", "--window-size=1440,900",
  "http://127.0.0.1:8772/static/index.html?g08=1#tab=world&run=preset-exp06-recip1000&t=1"], { stdio: "ignore" });
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
  await send("Emulation.setDeviceMetricsOverride", { width: 375, height: 812, deviceScaleFactor: 2, mobile: true });
  await sleep(2800);
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name) => {
    const r = await send("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(SHOT, name), Buffer.from(r.result.data, "base64"));
    ok("shot " + name, true, "screenshots/g08/" + name);
  };
  const geo = await ev(`(function(){
    var h=document.querySelector('.hud');
    var o=document.querySelector('.overview');
    var hr=h.getBoundingClientRect(); var or=o.getBoundingClientRect();
    var overflow=document.documentElement.scrollWidth>document.documentElement.clientWidth+2;
    return {hudH:Math.round(hr.height), ovH:Math.round(or.height), w:document.documentElement.clientWidth, overflow:overflow, t:window.__obs.S.t};
  })()`);
  ok("H1 375 宽 HUD 高度低于 160px", geo && geo.w === 375 && geo.hudH < 160 && geo.overflow === false, JSON.stringify(geo));
  await shot("mobile-375-hud.png");
  const t0 = await ev("performance.now()");
  const ms = await ev(`(async function(){
    var O=window.__obs; var t0=performance.now();
    await O.gotoYear(4); await O.gotoYear(83); await O.gotoYear(125); await O.gotoYear(1);
    return performance.now()-t0;
  })()`);
  ok("H2 四次跳年实测耗时 ms 非编造 FPS", typeof ms === "number" && ms >= 0, Number(ms).toFixed(1) + "ms (t0=" + t0 + ")");
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await sleep(200);
  await shot("desktop-world.png");
  ws.close();
} catch (e) { out.push("FAIL " + (e && e.stack ? e.stack.split("\n")[0] : e)); }
finally { chrome.kill(); }
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
