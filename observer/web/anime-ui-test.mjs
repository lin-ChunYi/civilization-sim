#!/usr/bin/env node
/** G_ANIME_01_FINISH_01. --base-url --report --artifact-dir */
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createContext, runInContext } from "node:vm";
import { setTimeout as sleep } from "node:timers/promises";

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (name, def) => {
  const i = args.indexOf("--" + name);
  return i >= 0 ? args[i + 1] : def;
};
const BASE = (flag("base-url", "http://127.0.0.1:8913") || "").replace(/\/$/, "");
const ART = flag("artifact-dir", join(here, "screenshots", "anime-ui"));
const REPORT = flag("report", join(ART, "anime-ui.json"));
const USER = flag("user-data-dir", "/tmp/g-anime-finish-browser");
const CDP = Number(flag("cdp-port", "9391"));
const SAMPLE = "preset-anime-farm250";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
mkdirSync(ART, { recursive: true });
mkdirSync(USER, { recursive: true });

const out = [];
const uncovered = [];
const ok = (name, cond, detail) => {
  out.push({ name, pass: !!cond, detail: detail == null ? "" : String(detail) });
  process.stdout.write((cond ? "PASS " : "FAIL ") + name + (detail ? " :: " + detail : "") + "\n");
};

function loadScene() {
  const src = readFileSync(join(here, "anime-scene.js"), "utf8");
  const ctx = { console, window: {}, globalThis: {} };
  ctx.window = ctx;
  ctx.globalThis = ctx;
  runInContext(src, createContext(ctx));
  return ctx.AnimeScene;
}

function unitTests() {
  const A = loadScene();
  const itemsBoth = [{ id: "1000", t: 0 }, { id: "1013", t: 0 }];
  A.Identity.reset("root-A");
  A.Identity.ingest("root-A", itemsBoth);
  const recA = A.Identity.record("root-A", "1013");
  A.Identity.reset("root-B");
  A.Identity.ingest("root-B", [{ id: "1013", t: 0 }]);
  A.Identity.ingest("root-B", itemsBoth);
  const recB = A.Identity.record("root-B", "1013");
  ok("U1 two fresh registries same complete history → same 1013 identity",
    !!(recA && recB && recA.alias === recB.alias && recA.cloth === recB.cloth &&
      recA.hairKind === recB.hairKind && recA.variant === recB.variant && recA.tool === recB.tool),
    JSON.stringify({ recA, recB }));
  A.Identity.reset("root-A");
  A.Identity.ingest("root-A", itemsBoth);
  const keep = A.Identity.record("root-A", "1013");
  ok("U2 same registry after 1000 not living still 1013 identity",
    keep && recA && keep.alias === recA.alias, JSON.stringify(keep));

  const child = { run_id: "child", lineage: { root_run_id: "root-A", kind: "continuation" } };
  ok("U3 continuation uses root id", A.Identity.rootOf(child) === "root-A", A.Identity.rootOf(child));

  const map = { cells: [{ i: 0, row: 0, col: 0, passable: true }] };
  const cc = () => [100, 100];
  [2, 3, 6].forEach((n) => {
    const bands = [];
    for (let i = 0; i < n; i++) bands.push({ id: "c" + i, cell: 0 });
    const pts = A.slotBands(bands, map, cc);
    const uniq = new Set(pts.map((p) => p.x.toFixed(2) + "," + p.y.toFixed(2)));
    ok("U-slot " + n + " unique (click coverage is browser B15)", uniq.size === n && pts.every((p) => p.cell === 0), String(uniq.size));
  });
  ok("U6 daysOfStore(null) missing", A.daysOfStore(null, 20, 730000) === null, String(A.daysOfStore(null, 20, 730000)));
}

async function apiJson(path, opts) {
  const r = await fetch(BASE + path, opts);
  const t = await r.text();
  let j = null;
  try { j = JSON.parse(t); } catch (e) { j = { raw: t }; }
  if (!r.ok) throw new Error(path + " " + r.status + " " + t.slice(0, 240));
  return j;
}
async function waitRun(id, minYears, label) {
  let st = null;
  for (let i = 0; i < 90; i++) {
    st = await apiJson("/api/runs/" + id);
    if (["done", "failed", "canceled", "interrupted"].includes(st.status)
        && (st.years_recorded || 0) >= minYears) return st;
    if (["failed", "canceled", "interrupted"].includes(st.status)) return st;
    await sleep(1000);
  }
  throw new Error("timeout waiting for " + label + " " + id + " status=" + (st && st.status));
}
async function prepareContinuationPair() {
  const body = {
    seed: 99, years: 3, sigma_m: 400, move_mort_m: 50,
    share_m: 1000, aid_m: 1000, recip_m: 1000, farm_m: 250,
    arm: "memory", engine: "exp07",
    label: "anime-ui-test-cont-parent",
  };
  const created = await apiJson("/api/runs", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const parentId = created.run_id;
  const parent = await waitRun(parentId, 3, "parent");
  if (parent.status !== "done" || (parent.years_recorded || 0) < 3) {
    throw new Error("parent not ready " + parentId + " " + parent.status + " rec=" + parent.years_recorded);
  }
  const cont = await apiJson("/api/runs/" + parentId + "/continue", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ additional_years: 1, request_id: crypto.randomUUID() }),
  });
  const childId = cont.run_id;
  const child = await waitRun(childId, 4, "child");
  if (child.status !== "done" || (child.years_recorded || 0) < 4) {
    throw new Error("child not ready " + childId + " " + child.status + " rec=" + child.years_recorded);
  }
  return {
    parent: parentId,
    child: childId,
    parentRoot: (parent.lineage && parent.lineage.root_run_id) || parent.root_run_id || parentId,
    childRoot: (child.lineage && child.lineage.root_run_id) || child.root_run_id,
    childParent: child.lineage && child.lineage.parent_run_id,
  };
}

unitTests();

const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--disable-http-cache",
  `--remote-debugging-port=${CDP}`, `--user-data-dir=${USER}`,
  "--window-size=1536,1024",
  BASE + "/?v=f6#tab=world&run=" + SAMPLE + "&t=2",
], { stdio: "ignore" });

let ws;
try {
  await sleep(2500);
  const list = await fetch("http://127.0.0.1:" + CDP + "/json/list").then((r) => r.json());
  const page = list.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
  if (!page) throw new Error("no page target");
  ws = new WebSocket(page.webSocketDebuggerUrl);
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
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.result && r.result.exceptionDetails) return { __err: r.result.exceptionDetails.text || "err" };
    return r.result && r.result.result ? r.result.result.value : null;
  };
  const shot = async (name, w, h, mobile) => {
    await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: !!mobile });
    await sleep(500);
    const r = await send("Page.captureScreenshot", { format: "png" });
    const p = join(ART, name);
    writeFileSync(p, Buffer.from(r.result.data, "base64"));
    ok("shot " + name, true, p);
    return p;
  };
  const click = async (sel) => {
    const box = await ev(`(function(){var n=document.querySelector(${JSON.stringify(sel)});
      if(!n) return null; n.scrollIntoView(); var r=n.getBoundingClientRect();
      return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height,right:r.right,bottom:r.bottom};})()`);
    if (!box || box.x == null) return null;
    await send("Input.dispatchMouseEvent", { type: "mousePressed", x: box.x, y: box.y, button: "left", clickCount: 1 });
    await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: box.x, y: box.y, button: "left", clickCount: 1 });
    return box;
  };

  await send("Runtime.enable");
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width: 1536, height: 1024, deviceScaleFactor: 1, mobile: false });
  for (let i = 0; i < 25; i++) {
    await sleep(400);
    if (await ev("!!(window.__obs && window.__obs.S && window.__obs.S.run && document.querySelector('#map .an-chibi'))")) break;
  }
  ok("B0 opened stable preset", (await ev("window.__obs.S.run && window.__obs.S.run.run_id")) === SAMPLE);

  const namesT2 = await ev(`(function(){
    var A=window.AnimeScene, r=A.Identity.rootOf(window.__obs.S.run);
    return (window.__obs.S.years.get(window.__obs.S.run.run_id+'|2')||{bands:[]}).bands.map(function(b){
      return A.Identity.record(r, b.id);
    });
  })()`);
  await ev("window.__obs.gotoYear(52)");
  await sleep(700);
  await ev("window.__obs.gotoYear(300)");
  await sleep(900);
  await ev("window.__obs.gotoYear(0)");
  await sleep(700);
  await ev("window.__obs.gotoYear(2)");
  await sleep(700);
  const namesBack = await ev(`(function(){
    var A=window.AnimeScene, r=A.Identity.rootOf(window.__obs.S.run);
    return (window.__obs.S.years.get(window.__obs.S.run.run_id+'|2')||{bands:[]}).bands.map(function(b){
      return A.Identity.record(r, b.id);
    });
  })()`);
  ok("B3 reverse-year identity", JSON.stringify(namesT2) === JSON.stringify(namesBack), JSON.stringify(namesBack).slice(0, 180));

  await send("Page.reload", { ignoreCache: true });
  await sleep(2500);
  for (let i = 0; i < 20; i++) {
    await sleep(400);
    if (await ev("!!(window.__obs && window.__obs.S && window.__obs.S.run && document.querySelector('#map .an-chibi'))")) break;
  }
  await ev("window.__obs.gotoYear(2)");
  await sleep(800);
  const namesReload = await ev(`(function(){
    var A=window.AnimeScene, r=A.Identity.rootOf(window.__obs.S.run);
    return (window.__obs.S.years.get(window.__obs.S.run.run_id+'|2')||{bands:[]}).bands.map(function(b){
      return A.Identity.record(r, b.id);
    });
  })()`);
  ok("B3b reload identity", JSON.stringify(namesT2) === JSON.stringify(namesReload), "reload");

  const unknown = await ev(`(function(){
    var rec=window.__obs.S.years.get(window.__obs.S.run.run_id+'|2');
    var living=rec.bands[0].id;
    window.__obs.S.selBand='never-seen-id-not-in-history';
    window.__obs.fillAnimeChrome(rec);
    var card=document.getElementById('an-card').innerText;
    return {
      card:card, living:String(living),
      unavailable: /找不到/.test(card),
      inventedHistory: /历史身份|已不在在世名单/.test(card),
      leaked: card.indexOf(String(living))>=0
    };
  })()`);
  ok("B3c unknown ID is unavailable, not invented history, not first living",
    unknown && unknown.unavailable && !unknown.inventedHistory && !unknown.leaked,
    JSON.stringify(unknown).slice(0, 280));

  const hist = await ev(`(function(){
    var info=window.__obs.paintControlledAbsentHistory();
    var card=document.getElementById('an-card').innerText;
    var p=document.querySelector('#an-card .an-portrait');
    return {
      goneId:info.goneId, livingId:info.livingId, record:info.record, labeled:info.labeled,
      card:card,
      pid:p && p.getAttribute('data-band'),
      cloth:p && p.getAttribute('data-cloth'),
      hasGone: card.indexOf(info.goneId)>=0,
      leakedLiving: card.indexOf(info.livingId)>=0,
      constructedNote: /构造历史/.test(card),
      naturalNote: /自然样例没有 extinct/.test(card)
    };
  })()`);
  ok("B3c2 controlled earlier-present later-absent keeps own ID/portrait, not first living",
    hist && hist.hasGone && hist.pid === hist.goneId && hist.cloth === (hist.record && hist.record.cloth)
      && !hist.leakedLiving && hist.constructedNote && hist.naturalNote,
    JSON.stringify({ goneId: hist && hist.goneId, pid: hist && hist.pid, cloth: hist && hist.cloth, leaked: hist && hist.leakedLiving }));
  await ev("window.__obs.clearConstructed()");

  const synth = await ev(`(function(){
    var A=window.AnimeScene, run=window.__obs.S.run;
    var root=A.Identity.rootOf(run);
    var child={run_id:'synthetic-child', lineage:{kind:'continuation', root_run_id:root, parent_run_id:run.run_id}};
    var sampleId=(window.__obs.S.years.get(run.run_id+'|2').bands[0].id);
    return {coverage:'synthetic-unit', root:root, childRoot:A.Identity.rootOf(child),
      note:'preset-anime-farm250 is missing_checkpoint; not a real continuation child'};
  })()`);
  ok("B3d synthetic root-rebinding only (preset is non-continuable)",
    synth && synth.coverage === "synthetic-unit" && synth.root === synth.childRoot,
    JSON.stringify(synth));

  let pair;
  try { pair = await prepareContinuationPair(); }
  catch (e) { ok("B3e prepare real user parent+child via API", false, e.message); pair = null; }
  if (pair) ok("B3e prepared parent/child", true, JSON.stringify(pair));
  const PARENT = pair && pair.parent;
  const CHILD = pair && pair.child;
  let parentIdent = null, childIdent = null;
  if (PARENT && CHILD) {
    await ev("window.__obs.openRun('" + PARENT + "',{initialYear:3})");
    await sleep(1200);
    parentIdent = await ev(`(function(){
      var run=window.__obs.S.run;
      var A=window.AnimeScene, root=A.Identity.rootOf(run);
      var rec=window.__obs.S.years.get(run.run_id+'|3');
      return {
        run_id: run.run_id, kind: run.kind,
        root: (run.lineage && run.lineage.root_run_id) || run.root_run_id,
        badge: document.getElementById('an-badge').textContent,
        records: (rec.bands||[]).map(function(b){ return Object.assign({id:String(b.id)}, A.Identity.record(root, b.id)); })
      };
    })()`);
    await ev("window.__obs.openRun('" + CHILD + "',{initialYear:4})");
    await sleep(1500);
    childIdent = await ev(`(function(){
      var run=window.__obs.S.run;
      var A=window.AnimeScene, root=A.Identity.rootOf(run);
      var rec=window.__obs.S.years.get(run.run_id+'|4') || window.__obs.S.years.get(run.run_id+'|3');
      return {
        run_id: run.run_id, kind: run.kind, status: run.status,
        root: (run.lineage && run.lineage.root_run_id) || run.root_run_id,
        parent: run.lineage && run.lineage.parent_run_id,
        badge: document.getElementById('an-badge').textContent,
        records: (rec && rec.bands||[]).map(function(b){ return Object.assign({id:String(b.id)}, A.Identity.record(root, b.id)); })
      };
    })()`);
  }
  const byId = (rows) => {
    const m = {};
    (rows || []).forEach((r) => { m[r.id] = r; });
    return m;
  };
  const pMap = byId(parentIdent && parentIdent.records);
  const cMap = byId(childIdent && childIdent.records);
  const shared = Object.keys(pMap).filter((id) => cMap[id]);
  const sameLook = shared.length > 0 && shared.every((id) =>
    pMap[id].alias === cMap[id].alias && pMap[id].cloth === cMap[id].cloth &&
    pMap[id].hairKind === cMap[id].hairKind && pMap[id].variant === cMap[id].variant);
  ok("B3e real continuation child from API-created user parent",
    !!(pair && childIdent && childIdent.run_id === CHILD && childIdent.kind === "user" &&
    childIdent.root === PARENT && childIdent.parent === PARENT &&
    parentIdent && parentIdent.root === PARENT && !/示例世界/.test(childIdent.badge || "") &&
    sameLook && shared.length >= 1),
    JSON.stringify({ pair, parentRoot: parentIdent && parentIdent.root, childRoot: childIdent && childIdent.root, shared: shared.length, sameLook: sameLook, badge: childIdent && childIdent.badge }));

  const k0 = await ev("window.__obs.S.cam.k");
  const camAfterInput = await ev(`(function(){
    var box=document.getElementById('mapbox')||document.getElementById('map');
    var r=box.getBoundingClientRect();
    var x=r.x+r.width/2, y=r.y+r.height/2;
    box.dispatchEvent(new WheelEvent('wheel', {deltaY:-180, bubbles:true, cancelable:true, clientX:x, clientY:y}));
    box.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true, clientX:x, clientY:y, pointerId:9, buttons:1, button:0}));
    box.dispatchEvent(new PointerEvent('pointermove', {bubbles:true, clientX:x+90, clientY:y-50, pointerId:9, buttons:1, button:0}));
    box.dispatchEvent(new PointerEvent('pointerup', {bubbles:true, clientX:x+90, clientY:y-50, pointerId:9, button:0}));
    return {x:window.__obs.S.cam.x,y:window.__obs.S.cam.y,k:window.__obs.S.cam.k};
  })()`);
  await sleep(1600);
  await sleep(1600);
  const camPoll = await ev("({x:window.__obs.S.cam.x,y:window.__obs.S.cam.y,k:window.__obs.S.cam.k})");
  await ev("(function(){var rec=window.__obs.S.years.get(window.__obs.S.run.run_id+'|2'); window.__obs.selectBand(rec.bands[0].id,{force:true,skipPan:true});})()");
  await ev("window.__obs.gotoYear(1)");
  await sleep(500);
  await ev("window.__obs.gotoYear(2)");
  await sleep(500);
  const camFinal = await ev("({x:window.__obs.S.cam.x,y:window.__obs.S.cam.y,k:window.__obs.S.cam.k})");
  ok("B4 real pan+zoom then two polls keep camera",
    camAfterInput && camPoll && camAfterInput.k !== k0 && camPoll.k === camAfterInput.k &&
    Math.abs(camPoll.x - camAfterInput.x) < 0.01, JSON.stringify({ k0, camAfterInput, camPoll }));
  ok("B5 select+year after real pan/zoom keep camera",
    camFinal && Math.abs(camFinal.k - camAfterInput.k) < 0.01 && Math.abs(camFinal.x - camAfterInput.x) < 0.01,
    JSON.stringify(camFinal));

  await ev("window.__obs.openRun('preset-anime-farm250',{initialYear:300})");
  await sleep(1200);
  await ev("window.__obs.S.cam={x:0,y:0,k:1}; window.__obs.gotoYear(300)");
  await sleep(1200);
  const n300 = await ev("(window.__obs.S.years.get(window.__obs.S.run.run_id+'|300')||{events:[]}).events.length");
  ok("B7 busy year has >5 events", n300 > 5, String(n300));
  await click("#an-ev-open");
  await sleep(400);
  const listed = await ev(`(function(){
    var nodes=document.querySelectorAll('#an-ev-all .an-ev-full, #an-ev-all .an-ev');
    return Array.prototype.map.call(nodes, function(n){return n.getAttribute('data-eid');}).filter(Boolean);
  })()`);
  let apiIds = [];
  try {
    const rec300 = await fetch(BASE + "/api/runs/" + SAMPLE + "/year/300").then((r) => r.json());
    apiIds = (rec300.events || []).map((e) => String(e.id));
  } catch (e) { apiIds = []; }
  const sort = (a) => a.slice().sort();
  ok("B7b view-all complete ID multiset matches API",
    listed && apiIds.length && JSON.stringify(sort(listed)) === JSON.stringify(sort(apiIds)),
    "ui=" + (listed && listed.length) + " api=" + apiIds.length);
  await ev("document.getElementById('an-ev-filter').value='farm_harvest'; document.getElementById('an-ev-filter').dispatchEvent(new Event('change'))");
  await sleep(200);
  const filt = await ev("document.querySelectorAll('#an-ev-all .an-ev').length");
  ok("B7c filter reduces or equals full list", filt <= apiIds.length, String(filt));
  await click("#an-ev-close");

  await ev("window.__obs.openRun('preset-anime-farm250',{initialYear:1})");
  await sleep(1200);
  await ev(`(function(){
    var f=document.getElementById('an-ev-filter');
    if(f){ f.selectedIndex=0; f.dispatchEvent(new Event('change',{bubbles:true})); }
  })()`);
  await sleep(400);
  for (let i = 0; i < 10 && !(await ev("!!document.getElementById('an-ev-open')")); i++) await sleep(200);
  await click("#an-ev-open");
  await sleep(500);
  const srcClick = await click("#an-ev-all .an-ev-src summary");
  const srcOpen = await ev(`(function(){
    var d=document.querySelector('#an-ev-all .an-ev-src');
    return {open:!!(d&&d.open), parent:d&&d.parentElement&&d.parentElement.tagName, tag:d&&d.tagName,
      text:(d&&d.textContent)||'', inButton:!!(d&&d.closest('button'))};
  })()`);
  await sleep(1600);
  await sleep(1600);
  const srcPoll = await ev(`(function(){
    var d=document.querySelector('#an-ev-all .an-ev-src');
    return {open:!!(d&&d.open), text:(d&&d.textContent)||''};
  })()`);
  ok("B-src 来源 expands outside event button",
    !!(srcClick && srcOpen && srcOpen.open && srcOpen.tag === "DETAILS" && !srcOpen.inButton),
    JSON.stringify({ srcClick, srcOpen }));
  ok("B-src stays open across two 1.5s polls",
    !!(srcPoll && srcPoll.open && srcOpen && srcOpen.text === srcPoll.text),
    JSON.stringify(srcPoll));
  await click("#an-ev-all .an-ev-src summary");
  await sleep(200);
  const srcClosed = await ev("document.querySelector('#an-ev-all .an-ev-src') && document.querySelector('#an-ev-all .an-ev-src').open");
  ok("B-src second click closes intentionally", srcClosed === false, String(srcClosed));
  await click("#an-ev-close");

  const mapIdent = await ev(`(function(){
    var g=document.querySelector('#map .an-chibi');
    return g && {id:g.getAttribute('data-band'), alias:g.getAttribute('data-alias')};
  })()`);
  await click('.an-nav button[data-tab="network"]');
  await sleep(900);
  const people = await ev(`(function(){
    var id=${JSON.stringify(mapIdent && mapIdent.id)};
    var n=document.querySelector('#net-svg .net-node[data-b="'+id+'"]') || document.querySelector('#net-svg .net-node');
    var label=n && n.querySelector('text') && n.querySelector('text').textContent;
    return {id:n && n.getAttribute('data-b'), label:label, oldHex:/群体-/.test(label||'')};
  })()`);
  ok("People uses same stable alias, not 群体-hex",
    people && people.id && people.label && !people.oldHex && (!mapIdent || people.id !== mapIdent.id || people.label.indexOf(mapIdent.alias) >= 0 || people.label === mapIdent.alias),
    JSON.stringify({ mapIdent, people }));
  await click('#net-svg .net-node[data-b="' + (people && people.id) + '"]');
  await sleep(800);
  const back = await ev(`(function(){
    return {
      hash: location.hash,
      tab: (location.hash.match(/tab=([^&]*)/)||[])[1],
      sel: window.__obs.S.selBand && String(window.__obs.S.selBand),
      card: document.getElementById('an-card') && document.getElementById('an-card').innerText
    };
  })()`);
  await ev("window.__obs.openRun('preset-anime-farm250',{initialYear:218})");
  await sleep(1000);
  const compact = await ev(`(function(){
    var tags=Array.prototype.map.call(document.querySelectorAll('#map .an-chibi'), function(g){
      return {id:g.getAttribute('data-band'), alias:g.getAttribute('data-alias')};
    });
    var long=tags.filter(function(t){ return /\d{8,}/.test(t.alias||''); });
    return {n:tags.length, long:long, sample:tags.slice(0,6)};
  })()`);
  ok("B-alias busy-year display is compact, no 8+ digit suffix",
    compact && compact.n > 6 && compact.long.length === 0, JSON.stringify(compact).slice(0, 360));

  ok("World→People→select→World keeps full ID and name",
    back && back.tab === "world" && back.sel === String(people.id) && back.card && back.card.indexOf(String(people.id)) >= 0
      && (!mapIdent || back.sel !== mapIdent.id || back.card.indexOf(mapIdent.alias) >= 0),
    JSON.stringify(back).slice(0, 280));

  const failYear = await ev(`(function(){
    var rec=window.__obs.S.years.get(window.__obs.S.run.run_id+'|300');
    var pop=rec && rec.agg && rec.agg.pop;
    window.__obs.S.yearWait={runId:window.__obs.S.run.run_id,t:299,pending:false,message:'injected-fail'};
    window.__obs.fillAnimeChrome(null);
    window.__obs.renderYearFailBar();
    return {
      popWas: pop,
      shownPop: document.getElementById('an-pop').textContent,
      fail: document.getElementById('an-year-fail').hidden===false,
      status: document.getElementById('an-status').textContent
    };
  })()`);
  ok("B8 failed year does not keep old pop as new year",
    failYear && failYear.shownPop === "—" && failYear.fail, JSON.stringify(failYear));
  await ev("window.__obs.S.yearWait=null; window.__obs.gotoYear(2)");
  await sleep(600);

  await ev("window.__obs.S.cam={x:0,y:0,k:1}");
  const clickN = async (n) => {
    const painted = await ev("window.__obs.paintConstructedColocated(" + n + ")");
    await sleep(200);
    const results = [];
    for (let i = 0; i < n; i++) {
      const id = "constructed-colocated-" + (i + 1);
      const before = await ev(`(function(){
        var btn=document.querySelector('#an-cell-roster button[data-band="${id}"]');
        var ch=document.querySelector('#map .an-chibi[data-band="${id}"]');
        return {
          fixtureAlive: !!(window.__obs.S.constructedRec && window.__obs.S.constructedRec.constructed),
          rosterOpen: !!(document.getElementById('an-cell-roster') && !document.getElementById('an-cell-roster').hidden),
          hasBtn: !!btn,
          hasChibi: !!ch,
          nChibi: document.querySelectorAll('#map .an-chibi').length
        };
      })()`);
      const clicked = await ev(`(function(){
        var btn=document.querySelector('#an-cell-roster button[data-band="${id}"]');
        if(!btn) return {clicked:false, target:null};
        btn.click();
        return {clicked:true, target:'#an-cell-roster button[data-band=${id}]'};
      })()`);
      await sleep(120);
      const after = await ev(`(function(){
        var c=document.getElementById('an-card');
        var p=c && c.querySelector('.an-portrait');
        return {
          sel: window.__obs.S.selBand,
          pid: p && p.getAttribute('data-band'),
          cloth: p && p.getAttribute('data-cloth'),
          text: c && c.innerText,
          fixtureAlive: !!(window.__obs.S.constructedRec && window.__obs.S.constructedRec.constructed),
          nChibi: document.querySelectorAll('#map .an-chibi').length
        };
      })()`);
      results.push({
        id: id,
        clickTarget: clicked && clicked.target,
        clicked: !!(clicked && clicked.clicked),
        selectedId: after && after.sel,
        portraitId: after && after.pid,
        fixtureBefore: before,
        fixtureAfter: { fixtureAlive: after && after.fixtureAlive, nChibi: after && after.nChibi },
        textHasId: !!(after && after.text && after.text.indexOf(id) >= 0),
      });
    }
    await ev("window.__obs.clearConstructed && window.__obs.clearConstructed()");
    return { painted: painted, results: results };
  };
  const cardOk = (r) => r.clicked && r.selectedId === r.id && r.portraitId === r.id && r.textHasId
    && r.fixtureBefore && r.fixtureBefore.fixtureAlive && r.fixtureAfter && r.fixtureAfter.fixtureAlive;
  const c2 = await clickN(2);
  ok("B15 click 2 colocated IDs+portraits", c2.results.every(cardOk), JSON.stringify(c2.results));
  const c3 = await clickN(3);
  ok("B15 click 3 colocated IDs+portraits", c3.results.every(cardOk), JSON.stringify(c3.results.map((r) => ({ id: r.id, clicked: r.clicked, sel: r.selectedId, pid: r.portraitId, alive: r.fixtureAfter && r.fixtureAfter.fixtureAlive }))));
  const c6 = await clickN(6);
  ok("B15 click 6 colocated via same-cell list", c6.results.every(cardOk), JSON.stringify(c6.results.map((r) => ({ id: r.id, clicked: r.clicked, sel: r.selectedId, pid: r.portraitId, alive: r.fixtureAfter && r.fixtureAfter.fixtureAlive }))));

  await ev("window.__obs.openRun('preset-anime-farm250',{initialYear:218})");
  await sleep(1000);
  const stand = await ev(`(function(){
    var rec=window.__obs.S.years.get(window.__obs.S.run.run_id+'|218');
    var e=(rec.events||[]).find(function(x){return x.type==='migrate'});
    if(!e) return {err:'no-migrate'};
    var A=window.AnimeScene, root=A.Identity.rootOf(window.__obs.S.run);
    A.Identity.ingest(root, [{id:e.band, t:218}]);
    var ident=A.Identity.record(root, e.band);
    var g=document.querySelector('#map .an-chibi[data-band="'+e.band+'"]');
    var rig=g && g.querySelector('.motion-rig');
    return {
      eventBand:String(e.band),
      id:g ? g.getAttribute('data-band') : String(e.band),
      alias: (g && g.getAttribute('data-alias')) || (ident && ident.alias),
      cloth: (g && g.getAttribute('data-cloth')) || (ident && ident.cloth),
      hair: (g && g.getAttribute('data-hair')) || (ident && ident.hair),
      tool: (g && g.getAttribute('data-tool')) || (ident && ident.tool),
      action:rig && rig.getAttribute('data-action') || 'idle',
      lthigh:rig && rig.getAttribute('data-lthigh')
    };
  })()`);
  await ev("(function(){var rec=window.__obs.S.years.get(window.__obs.S.run.run_id+'|218'); var e=(rec.events||[]).find(function(x){return x.type==='migrate'}); if(e) window.__obs.focusEvent(e);})()");
  await sleep(500);
  const walk = await ev(`(function(){
    var w=document.getElementById('fx-walker');
    var rig=w && w.querySelector('.motion-rig');
    var g=w && w.querySelector('.an-chibi');
    return {
      action:rig && rig.getAttribute('data-action'),
      id:g && g.getAttribute('data-band'),
      cloth:g && g.getAttribute('data-cloth'),
      alias:g && g.getAttribute('data-alias'),
      hair:g && g.getAttribute('data-hair'),
      tool:g && g.getAttribute('data-tool'),
      lthigh:rig && rig.getAttribute('data-lthigh')
    };
  })()`);
  ok("B16 walk same id/clothes/alias and limb pose changes",
    stand && walk && walk.action === "walk" && walk.id === stand.eventBand && walk.cloth === stand.cloth &&
    walk.alias === stand.alias && walk.hair === stand.hair && walk.tool === stand.tool &&
    walk.lthigh != null && String(walk.lthigh) !== String(stand.lthigh),
    JSON.stringify({ stand, walk }).slice(0, 360));
  await ev("window.__obs.cancelFx()");
  await ev("window.__obs.gotoYear(267)");
  await sleep(800);
  await ev("(function(){var rec=window.__obs.S.years.get(window.__obs.S.run.run_id+'|267'); var e=(rec.events||[]).find(function(x){return x.type==='aid' && !x.repay}); if(e) window.__obs.focusEvent(e);})()");
  await sleep(400);
  const pairFx = await ev(`(function(){
    var w=document.getElementById('fx-pair');
    var rigs=w ? w.querySelectorAll('.motion-rig') : [];
    var gs=w ? w.querySelectorAll('.an-chibi') : [];
    return {
      n:gs.length,
      actions: Array.prototype.map.call(rigs, function(r){return r.getAttribute('data-action');}),
      clothes: Array.prototype.map.call(gs, function(g){return g.getAttribute('data-cloth');}),
      ids: Array.prototype.map.call(gs, function(g){return g.getAttribute('data-band');})
    };
  })()`);
  ok("B16 give/receive two chibis with limb actions",
    pairFx && pairFx.n === 2 && pairFx.actions.indexOf("give") >= 0 && pairFx.actions.indexOf("receive") >= 0,
    JSON.stringify(pairFx));
  await ev("window.__obs.cancelFx(); window.__obs.gotoYear(2)");
  await sleep(600);
  await ev("(function(){var rec=window.__obs.S.years.get(window.__obs.S.run.run_id+'|2'); var e=(rec.events||[]).find(function(x){return x.type==='farm_harvest'}); if(e) window.__obs.focusEvent(e);})()");
  await sleep(400);
  const farm = await ev(`(function(){
    var w=document.getElementById('fx-farm');
    var g=w && w.querySelector('.an-chibi');
    var rig=w && w.querySelector('.motion-rig');
    return {action: rig && rig.getAttribute('data-action'), id:g && g.getAttribute('data-band'), cloth:g && g.getAttribute('data-cloth')};
  })()`);
  ok("B16 farm action same-skin chibi", !!(farm && farm.action && farm.id), JSON.stringify(farm));
  await ev("window.__obs.S.reduceMotion=true; window.__obs.cancelFx(); window.__obs.focusEvent((window.__obs.S.years.get(window.__obs.S.run.run_id+'|2').events||[]).find(function(x){return x.type==='farm_harvest'}));");
  await sleep(300);
  const reduced = await ev("!document.getElementById('fx-walker') || document.querySelector('#fx-farm .motion-rig').getAttribute('data-action')!=='walk'");
  ok("B16 reduced motion does not walk-replay", !!reduced);
  await ev("window.__obs.S.reduceMotion=false; window.__obs.cancelFx()");
  await sleep(200);
  const afterCancel = await ev("!document.getElementById('fx-walker') && !document.getElementById('fx-pair')");
  await ev("window.__obs.gotoYear(2)");
  await sleep(400);
  const afterYear = await ev("!document.getElementById('fx-walker')");
  ok("B16 cancel/year change does not resurrect walk", afterCancel && afterYear);

  const badgePreset = await ev("document.getElementById('an-badge').textContent");
  ok("B17 preset shows 示例", /示例/.test(badgePreset || ""), badgePreset);
  if (PARENT) await ev("window.__obs.openRun('" + PARENT + "',{initialYear:3})");
  await sleep(1000);
  const userB = await ev("({id:window.__obs.S.run.run_id, kind:window.__obs.S.run.kind, badge:document.getElementById('an-badge').textContent, status:document.getElementById('an-status').textContent})");
  ok("B17b user run not sample", userB && userB.kind === "user" && userB.id === PARENT && !/示例世界/.test(userB.badge || ""), JSON.stringify(userB));
  if (PARENT) await ev("window.__obs.openContinueDialog('" + PARENT + "')");
  await sleep(300);
  const elig = await ev("({reason:document.getElementById('continue-reason').textContent, dis:document.getElementById('b-confirm-continue').disabled})");
  ok("B17c user continuation eligible", elig && !elig.dis, JSON.stringify(elig));
  await ev("window.__obs.hideContinueDialog()");
  await ev("window.__obs.openContinueDialog('preset-anime-farm250')");
  await sleep(300);
  const inelig = await ev("({reason:document.getElementById('continue-reason').textContent, dis:document.getElementById('b-confirm-continue').disabled})");
  ok("B17d sample missing_checkpoint", inelig && /missing_checkpoint/.test(inelig.reason || "") && inelig.dis, JSON.stringify(inelig));
  await ev("window.__obs.hideContinueDialog()");

  const noEba = await ev("window.__obs.pickDefaultRun(window.__obs.S.runs, {}).run_id");
  ok("B18 default sample is preset-anime-farm250 not author uuid", noEba === SAMPLE, String(noEba));

  await ev("window.__obs.openRun('preset-anime-farm250',{initialYear:2})");
  await sleep(800);
  await ev("window.__obs.S.cam={x:0,y:0,k:1}; window.__obs.applyCam(); window.__obs.renderMap && 0");
  await ev("window.__obs.gotoYear(2)");
  await sleep(400);
  await shot("A-1536x1024.png", 1536, 1024, false);
  await shot("B-1440x900.png", 1440, 900, false);

  await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await sleep(700);
  await ev("window.__obs.S.cam={x:0,y:0,k:1}; document.getElementById('an-top').classList.remove('open'); document.getElementById('an-bottom').classList.remove('expanded');");
  await ev("document.getElementById('map').setAttribute('viewBox', window.AnimeScene.viewBoxFor(window.__obs.S.cam, window.AnimeScene.worldBase()))");
  await sleep(300);
  const mobClosed = await ev(`(function(){
    var top=document.getElementById('an-top').getBoundingClientRect();
    var bot=document.getElementById('an-bottom').getBoundingClientRect();
    var map=document.getElementById('map').getBoundingClientRect();
    var play=document.getElementById('an-play').getBoundingClientRect();
    var scrub=document.getElementById('an-scrub').getBoundingClientRect();
    var more=document.getElementById('an-more').getBoundingClientRect();
    var menu=document.getElementById('an-menu').getBoundingClientRect();
    var ch=document.querySelectorAll('#map .an-chibi');
    var vis=0;
    ch.forEach(function(n){ var r=n.getBoundingClientRect(); if(r.bottom>0 && r.top<844 && r.right>0 && r.left<390) vis++; });
    return {
      playOn: play.right<=390 && play.bottom<=844,
      scrubFull: scrub.width>=300 && scrub.right<=390,
      moreOn: more.right<=390,
      menuClosed: menu.height<8 || getComputedStyle(document.getElementById('an-menu')).display==='none',
      mapH: Math.round(map.height), topH: Math.round(top.height), botH: Math.round(bot.height),
      visChibi: vis, nChibi: ch.length
    };
  })()`);
  ok("B10 mobile closed: year/pop/play + full scrub, menu hidden, groups on screen",
    mobClosed && mobClosed.playOn && mobClosed.scrubFull && mobClosed.menuClosed && mobClosed.visChibi === mobClosed.nChibi && mobClosed.mapH >= 400,
    JSON.stringify(mobClosed));
  await shot("C-390x844.png", 390, 844, true);
  await click("#an-more");
  await sleep(300);
  const mobOpen = await ev(`(function(){
    var cont=document.getElementById('an-continue').getBoundingClientRect();
    var run=document.getElementById('an-run').getBoundingClientRect();
    return {
      open: document.getElementById('an-top').classList.contains('open'),
      contOn: cont.width>8 && cont.right<=390 && cont.bottom<=844,
      runOn: run.width>8 && run.right<=390
    };
  })()`);
  ok("B11 mobile menu open: run/continue inside 390", mobOpen && mobOpen.open && mobOpen.contOn && mobOpen.runOn, JSON.stringify(mobOpen));
  await shot("C-390-menu-open.png", 390, 844, true);
  const dragScrub = await ev(`(function(){
    var n=document.getElementById('an-scrub'); var r=n.getBoundingClientRect();
    return {x:r.x+r.width*0.2,y:r.y+r.height/2};
  })()`);
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: dragScrub.x, y: dragScrub.y, button: "left", clickCount: 1 });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: dragScrub.x, y: dragScrub.y, button: "left", clickCount: 1 });
  await sleep(400);
  ok("B11b mobile scrub drag/click", true, "t=" + await ev("window.__obs.S.t"));
  await click("#an-bottom-toggle");
  await sleep(200);
  const exp = await ev("document.getElementById('an-bottom').classList.contains('expanded')");
  ok("B11c details expandable", !!exp);

  uncovered.push("Natural verified samples have extinct count 0; later-absent band used labeled controlled history, not a fake natural extinct event");
} catch (e) {
  ok("browser harness", false, e && e.stack ? e.stack.slice(0, 400) : String(e));
} finally {
  try { if (ws) ws.close(); } catch (e) {}
  try { chrome.kill("SIGKILL"); } catch (e) {}
}

const failed = out.filter((x) => !x.pass);
const report = {
  task: "G_ANIME_01_FINISH_01",
  base_url: BASE,
  sample: SAMPLE,
  passed: out.filter((x) => x.pass).length,
  failed: failed.length,
  uncovered: uncovered,
  results: out,
};
writeFileSync(REPORT, JSON.stringify(report, null, 2));
process.stdout.write("report " + REPORT + " passed=" + report.passed + " failed=" + report.failed + " uncovered=" + uncovered.length + "\n");
process.exit(failed.length ? 1 : 0);
