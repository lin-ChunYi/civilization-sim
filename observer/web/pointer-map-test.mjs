#!/usr/bin/env node
/** Chromium CDP 真实鼠标：按下/移动/抬起，不用 element.click()。 */
import { spawn } from "node:child_process";
import { setTimeout as sleep } from "node:timers/promises";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PORT = 9333;
const RUN = "946a58d28b05";
const PAGE = `http://127.0.0.1:8772/static/index.html#tab=world&run=${RUN}&t=124`;
const BANDS = [
  "907731079216851761",
  "7567856178022945294",
  "10431967184297706310",
];

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`,
  "--user-data-dir=/tmp/g02r1-cdp",
  "--window-size=1440,900",
  PAGE,
], { stdio: "ignore" });

const out = [];
const ok = (name, cond, detail) => {
  out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));
};

try {
  await sleep(1200);
  const list = await fetch(`http://127.0.0.1:${PORT}/json/list`).then((r) => r.json());
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
    return new Promise((res) => {
      pending.set(id, res);
      ws.send(JSON.stringify({ id, method, params }));
    });
  };
  await send("Runtime.enable");
  await send("Page.enable");
  await sleep(2800);

  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: false });
    if (r.result && r.result.exceptionDetails) return null;
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const clickXY = async (x, y) => {
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
  };
  const rectOf = async (sel) => ev(`(function(){var n=document.querySelector(${JSON.stringify(sel)});
    if(!n) return null; var r=n.getBoundingClientRect();
    return {x:r.x,y:r.y,w:r.width,h:r.height,tag:n.tagName};})()`);

  const ready = await ev("!!(window.__obs && window.__obs.S && window.__obs.S.run && document.querySelector('#map .band'))");
  ok("P0 页面已加载运行与棋子", !!ready);

  for (const bid of BANDS) {
    const sel = `#map .band[data-band="${bid}"]`;
    const rect = await rectOf(sel);
    ok("P1 棋子节点 " + bid.slice(0, 6), !!rect && rect.w > 0, JSON.stringify(rect));
    if (!rect) continue;
    const x = rect.x + rect.w / 2, y = rect.y + rect.h / 2;
    const hit = await ev(`(function(){var n=document.elementFromPoint(${x},${y});
      return n && (n.getAttribute('data-band')|| (n.closest && n.closest('[data-band]') && n.closest('[data-band]').getAttribute('data-band')));})()`);
    ok("P2 中心 elementFromPoint 是该棋子 " + bid.slice(0, 6), String(hit) === bid, "hit=" + hit);
    await clickXY(x, y);
    await sleep(500);
    const hash = await ev("location.hash");
    const side = await ev("document.getElementById('side-sel') && document.getElementById('side-sel').innerText");
    const dossier = await ev("document.getElementById('pane-dossier') && !document.getElementById('pane-dossier').hidden");
    ok("P3 URL 含 b=" + bid.slice(0, 6), typeof hash === "string" && hash.indexOf(bid) >= 0, hash);
    ok("P4 档案轨打开且有选中数据 " + bid.slice(0, 6),
      !!dossier && typeof side === "string" && side.indexOf(bid) >= 0, (side || "").slice(0, 120));
  }

  const cell = await rectOf('#map .cell[data-cell="8"]');
  if (cell) {
    await clickXY(cell.x + cell.w / 2, cell.y + cell.h / 2);
    await sleep(300);
    const selCell = await ev("window.__obs.S.selCell");
    ok("P5 格子真实点击选中 8", selCell === 8, "selCell=" + selCell);
  } else ok("P5 格子真实点击选中 8", false, "no cell 8");

  const empty = await ev(`(function(){var n=document.querySelector('#map .cell[data-cell="3"]');
    if(!n) return null; var r=n.getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
  if (empty) {
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x: empty.x, y: empty.y, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: empty.x + 40, y: empty.y + 12 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: empty.x + 40, y: empty.y + 12, button: "left", clickCount: 1 });
    await sleep(200);
    const bid = BANDS[1];
    const rect = await rectOf(`#map .band[data-band="${bid}"]`);
    if (rect) {
      await clickXY(rect.x + rect.w / 2, rect.y + rect.h / 2);
      await sleep(400);
      const hash = await ev("location.hash");
      ok("P6 拖拽后再点棋子仍可选", typeof hash === "string" && hash.indexOf(bid) >= 0, hash);
    } else ok("P6 拖拽后再点棋子仍可选", false, "band gone");
  }

  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: 200, y: 200, button: "left", clickCount: 1 });
  await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: 210, y: 200 });
  /* 不抬起，发 cancel 等价：抬起到外并清 drag */
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: 10, y: 10, button: "left", clickCount: 1 });
  await sleep(150);
  const bid0 = BANDS[0];
  const r0 = await rectOf(`#map .band[data-band="${bid0}"]`);
  if (r0) {
    await clickXY(r0.x + r0.w / 2, r0.y + r0.h / 2);
    await sleep(400);
    const hash = await ev("location.hash");
    ok("P7 取消手势后下一次点击可用", typeof hash === "string" && hash.indexOf(bid0) >= 0, hash);
  } else ok("P7 取消手势后下一次点击可用", false);

  const t0 = await ev("window.__obs.S.t");
  const key = await ev(`(function(){
    var box=document.querySelector('.tokbox'); if(box) box.open=true;
    var i=document.getElementById('token'); if(!i) return 'no-input';
    i.focus();
    var ev=new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true});
    i.dispatchEvent(ev);
    return (document.activeElement && document.activeElement.id==='token' ? 'kept-focus' : 'lost')
      + '|t=' + window.__obs.S.t;
  })()`);
  const t1 = await ev("window.__obs.S.t");
  ok("P8 输入框时方向键不改年份", t1 === t0, "before=" + t0 + " after=" + t1 + " " + key);

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
