#!/usr/bin/env node
/** G03 确定性延迟响应回归：旧候选应红、新版应绿。不访问真实网络。 */
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const NEW_SRC = readFileSync(join(here, "app.js"), "utf8");
const OLD_SRC = execFileSync("git", ["show", "f5fea4b:observer/web/app.js"], { encoding: "utf8" });

function el() {
  const kids = [];
  const n = {
    hidden: true, textContent: "", innerHTML: "", value: "0", max: "0",
    className: "", disabled: false,
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    style: {}, dataset: {},
    setAttribute() {}, getAttribute() { return null; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    addEventListener() {},
    remove() {},
    appendChild(c) { kids.push(c); return c; },
    removeChild() {},
    scrollIntoView() {},
    getBoundingClientRect() { return { x: 0, y: 0, width: 10, height: 10 }; },
  };
  return n;
}

function makeCtx() {
  const els = {};
  const document = {
    getElementById(id) { return (els[id] = els[id] || el()); },
    querySelector() { return el(); },
    querySelectorAll() { return []; },
    addEventListener() {},
    documentElement: { clientWidth: 1440 },
    body: el(),
    createElement() { return el(); },
    createElementNS(_ns, name) { const n = el(); n.tagName = name; n.appendChild = function () {}; return n; },
  };
  const pending = [];
  const fetchFn = (url) => new Promise((resolve, reject) => {
    pending.push({ url: String(url), resolve, reject });
  });
  const location = { hash: "", search: "", href: "http://127.0.0.1/static/index.html" };
  const windowObj = { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) };
  const ctx = {
    window: windowObj,
    document,
    location,
    history: { replaceState() { } },
    sessionStorage: { getItem() { return ""; }, setItem() { } },
    performance: { now: Date.now },
    console,
    setTimeout,
    clearTimeout,
    requestAnimationFrame: (fn) => setTimeout(fn, 0),
    cancelAnimationFrame: clearTimeout,
    fetch: fetchFn,
    URLSearchParams,
  };
  ctx.globalThis = ctx;
  windowObj.__OBS_MANUAL_BOOT__ = true;
  vm.createContext(ctx);
  return { ctx, pending, els };
}

function bootSrc(src) {
  const h = makeCtx();
  vm.runInContext(src, h.ctx);
  const O = h.ctx.window.__obs;
  ["setPlaying", "tickEvents", "tick", "bumpOp", "opAlive", "bandAccept", "gotoYear", "focusEvent", "loadBand"].forEach((k) => {
    if (O && !O[k] && typeof h.ctx[k] === "function") O[k] = h.ctx[k];
  });
  const cells = [];
  for (let i = 0; i < 64; i++) cells.push({ i, row: Math.floor(i / 8), col: i % 8, passable: true, region: "A", neighbors: [] });
  O.S.map = { w: 8, h: 8, cells, barrier_cols: [] };
  O.S.cfg = { default_engine: "exp06", arms: {}, engines: {}, repo_commit: "test" };
  return { O, pending: h.pending, els: h.els, DirectorLogic: h.ctx.window.DirectorLogic };
}

function jsonOk(body) {
  return { ok: true, status: 200, json: async () => body };
}

function take(pending, part) {
  const i = pending.findIndex((p) => p.url.indexOf(part) >= 0);
  if (i < 0) return null;
  return pending.splice(i, 1)[0];
}

function wait(ms) { return new Promise((r) => setTimeout(r, ms)); }

const BAND = "7567856178022945294";
const asOf52 = {
  id: BAND, origin: "test", first_seen: 0, last_seen: 52, extinct_at: null, children: [], source: "as_of",
  history_scope: { mode: "as_of_year", at_year: 52, years_recorded: 150, note: "截至52" },
  trajectory: [[0, 0], [4, 10], [52, 1]],
};
const fullD = {
  id: BAND, origin: "test", first_seen: 0, last_seen: 150, extinct_at: null, children: [], source: "full",
  history_scope: { mode: "full", at_year: null, years_recorded: 150, note: "全档案" },
  trajectory: [[0, 0], [4, 10], [52, 1], [125, 1], [131, 0]],
};
const year0 = { t: 0, events: [], bands: [], year: {}, agg: { pop: 120, bands: 6 }, cum: {}, integrity: { conservation_error: 0, population_identity_error: 0, state_hash: "x" }, stock: new Array(64).fill(0) };
const year124 = { t: 124, events: [{ id: "t124-aid-0", type: "aid", cell: 1, donor: "D", receiver: "R", text: "aid", source: "log" }], bands: [{ id: "R", name: "r", cell: 1, size: 10, store: 0, mem: {} }], year: { births_cum: 1, deaths_demo_cum: 0, mig_deaths_cum: 0, mig_total: 0 }, agg: { pop: 116, bands: 6 }, cum: {}, integrity: { conservation_error: 0, population_identity_error: 0, state_hash: "x" }, stock: new Array(64).fill(0) };
const year125 = { t: 125, events: [{ id: "t125-share-1", type: "share", cell: 0, donor: "D", receiver: "R", text: "share", source: "log" }], bands: [{ id: "R", name: "r", cell: 1, size: 10, store: 0, mem: {} }], year: { births_cum: 1, deaths_demo_cum: 0, mig_deaths_cum: 0, mig_total: 0 }, agg: { pop: 117, bands: 6 }, cum: {}, integrity: { conservation_error: 0, population_identity_error: 0, state_hash: "x" }, stock: new Array(64).fill(0) };

function setupRun(O, id, recorded) {
  O.S.run = { run_id: id, years_recorded: recorded, years: recorded, status: "done", engine: "exp06", label: id };
  O.S.t = 0;
  O.S.epoch += 1;
  O.S.selBand = null;
  O.S.selCell = null;
  O.S.selEvent = null;
  O.S.band = null;
  O.S.playing = false;
  O.S.playMode = "year";
  O.S.bandScope = "as_of";
  O.S.cam = { x: 0, y: 0, k: 1 };
  O.S.years = new Map();
  O.S.series = [];
  for (let t = 0; t <= recorded; t++) O.S.series.push({ t: t, events: (t === 124 || t === 125) ? 1 : 0, agg: { pop: 120, bands: 6 }, year: {} });
  O.S.years.set(O.ykey(id, 0), year0);
}

const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

async function raceLoadBand(label, src, expectRejectLateFull) {
  const { O, pending } = bootSrc(src);
  setupRun(O, "preset-exp06-recip1000", 150);
  O.S.selBand = BAND;
  O.S.t = 52;
  O.S.bandScope = "full";
  const pFull = O.loadBand(BAND);
  O.S.bandScope = "as_of";
  const pAs = O.loadBand(BAND);
  await wait(5);
  const asReq = take(pending, "at_year=52");
  const fullReq = take(pending, "/band/" + BAND);
  if (!asReq || !fullReq) {
    ok(label + " 发出 full 与 as_of 请求", false, "as=" + !!asReq + " full=" + !!fullReq + " n=" + pending.length);
    return;
  }
  asReq.resolve(jsonOk(asOf52));
  await pAs;
  fullReq.resolve(jsonOk(fullD));
  await pFull;
  const mode = O.S.band && O.S.band.history_scope && O.S.band.history_scope.mode;
  const traj = (O.S.band && O.S.band.trajectory) || [];
  const hasFuture = traj.some((p) => p[0] === 125 || p[0] === 131);
  const selectedScope = O.S.bandScope;
  const pass = expectRejectLateFull
    ? (selectedScope === "as_of" && mode === "as_of_year" && !hasFuture)
    : (mode === "full" && hasFuture);
  ok(label + " selectedScope=" + selectedScope + " band.mode=" + mode + " future=" + hasFuture,
    pass, JSON.stringify({ mode, traj: traj.map((p) => p[0]), expectRejectLateFull }));
}

async function raceSwitchRun(label, src, expectStale) {
  const { O, pending } = bootSrc(src);
  setupRun(O, "runA", 150);
  O.S.years.set(O.ykey("runA", 124), year124);
  O.S.t = 0;
  O.S.cam = { x: 9, y: 9, k: 1 };
  const p = O.focusEvent(Object.assign({}, year125.events[0], { t: 125 }));
  await wait(5);
  const yreq = take(pending, "/year/125");
  O.bumpOp ? O.bumpOp() : (O.S.opGen = (O.S.opGen || 0) + 1);
  O.S.epoch += 1;
  setupRun(O, "runB", 10);
  O.S.t = 0;
  O.S.selEvent = null;
  O.S.selBand = null;
  O.S.selCell = null;
  O.S.cam = { x: 0, y: 0, k: 1 };
  if (yreq) yreq.resolve(jsonOk(year125));
  const r = await p;
  const leaked = O.S.run.run_id === "runB" && O.S.t === 0 && (
    O.S.selEvent === "t125-share-1" || O.S.selBand === "R" || O.S.selCell === 0 || O.S.cam.x !== 0 || O.S.cam.y !== 0
  );
  const staleOk = r && r.ok === false && r.reason === "stale";
  if (expectStale) {
    ok(label + " A125→B0 不泄漏", !leaked && staleOk && O.S.t === 0 && O.S.run.run_id === "runB" && O.S.selEvent == null,
      JSON.stringify({ r, t: O.S.t, run: O.S.run.run_id, ev: O.S.selEvent, band: O.S.selBand, cell: O.S.selCell, cam: O.S.cam }));
  } else {
    ok(label + " 旧候选泄漏 t125 到 B0", leaked,
      JSON.stringify({ r, t: O.S.t, run: O.S.run.run_id, ev: O.S.selEvent, band: O.S.selBand, cell: O.S.selCell, cam: O.S.cam }));
  }
}

async function racePausePlay(label, src, expectHold) {
  const { O, pending } = bootSrc(src);
  setupRun(O, "runA", 150);
  O.S.years.set(O.ykey("runA", 124), year124);
  O.S.t = 124;
  O.S.selEvent = "t124-aid-0";
  O.S.playMode = "events";
  O.S.playing = true;
  O.S.cam = { x: 3, y: 4, k: 1 };
  const cam0 = { x: O.S.cam.x, y: O.S.cam.y };
  const capturedOp = O.S.opGen;
  const tickP = O.tickEvents
    ? O.tickEvents()
    : (async () => {
      await O.gotoYear(125, { quiet: true });
      await O.focusEvent(Object.assign({}, year125.events[0], { t: 125 }), { fromPlay: true });
    })();
  await wait(5);
  const yreq = take(pending, "/year/125");
  O.setPlaying(false);
  await wait(40);
  if (yreq) yreq.resolve(jsonOk(year125));
  await tickP;
  await wait(20);
  void capturedOp;
  void cam0;
  const moved = O.S.t === 125 || O.S.selEvent === "t125-share-1" || O.S.cam.x !== cam0.x || O.S.cam.y !== cam0.y;
  const timers = (O.S.fxTimers || []).length + (O.S.timer ? 1 : 0);
  if (expectHold) {
    ok(label + " 暂停后仍停在 124", O.S.playing === false && O.S.t === 124 && O.S.selEvent === "t124-aid-0" && !moved && timers === 0,
      JSON.stringify({ playing: O.S.playing, t: O.S.t, ev: O.S.selEvent, cam: O.S.cam, timers }));
  } else {
    ok(label + " 旧候选暂停后仍跳到 125", moved || O.S.t === 125 || O.S.selEvent === "t125-share-1",
      JSON.stringify({ playing: O.S.playing, t: O.S.t, ev: O.S.selEvent, cam: O.S.cam, timers }));
  }
}

try {
  ok("old src 来自 checkpoint f5fea4b", OLD_SRC.indexOf("async function loadBand") >= 0 && OLD_SRC.indexOf("bandReqGen") < 0);
  ok("new src 含 bandReqGen/opGen", NEW_SRC.indexOf("bandReqGen") >= 0 && NEW_SRC.indexOf("function opAlive") >= 0);

  await raceLoadBand("OLD loadBand", OLD_SRC, false);
  await raceLoadBand("NEW loadBand", NEW_SRC, true);
  await raceSwitchRun("OLD A125→B0", OLD_SRC, false);
  await raceSwitchRun("NEW A125→B0", NEW_SRC, true);
  await racePausePlay("OLD pause-during-await", OLD_SRC, false);
  await racePausePlay("NEW pause-during-await", NEW_SRC, true);

  {
    const { O, pending } = bootSrc(NEW_SRC);
    setupRun(O, "runA", 150);
    O.S.years.set(O.ykey("runA", 124), year124);
    O.S.t = 124;
    O.S.selEvent = "t124-aid-0";
    O.S.playMode = "events";
    O.S.playing = true;
    const p = O.tickEvents();
    await wait(5);
    const yreq = take(pending, "/year/125");
    O.setPlayMode("year");
    await wait(10);
    if (yreq) yreq.resolve(jsonOk(year125));
    await p;
    ok("NEW 切逐年模式不跳到 125", O.S.t === 124 && O.S.playMode === "year" && O.S.selEvent !== "t125-share-1",
      JSON.stringify({ t: O.S.t, mode: O.S.playMode, ev: O.S.selEvent }));
  }
  {
    const { O, pending } = bootSrc(NEW_SRC);
    setupRun(O, "runA", 150);
    O.S.t = 124;
    O.S.years.set(O.ykey("runA", 124), year124);
    O.S.playing = true;
    const myOp = O.S.opGen;
    const p = O.gotoYear(125, { quiet: true, opGen: myOp });
    await wait(5);
    const yreq = take(pending, "/year/125");
    O.bumpOp();
    O.S.t = 83;
    if (yreq) yreq.resolve(jsonOk(year125));
    const r = await p;
    ok("NEW 手动改年使 125 请求失效", r && r.ok === false && O.S.t === 83,
      JSON.stringify({ r, t: O.S.t }));
  }

  const { O } = bootSrc(NEW_SRC);
  const legacy = (epoch, runId, bandId) => {
    const stale = O.S.epoch !== epoch || !O.S.run || O.S.run.run_id !== runId;
    return !stale && O.S.selBand === bandId;
  };
  setupRun(O, "preset-exp06-recip1000", 150);
  O.S.selBand = BAND;
  O.S.t = 52;
  O.S.bandScope = "as_of";
  const e0 = O.S.epoch;
  ok("legacy 谓词在切口径后仍接受旧 full", legacy(e0, "preset-exp06-recip1000", BAND) === true);
  ok("new bandAccept 在口径不符时拒绝",
    O.bandAccept(e0, "preset-exp06-recip1000", BAND, "full", 52, O.S.bandReqGen) === false);
} catch (e) {
  out.push("FAIL 脚本出错 :: " + (e && e.stack ? e.stack : e));
}

const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
