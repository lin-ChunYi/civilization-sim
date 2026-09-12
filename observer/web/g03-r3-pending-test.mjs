#!/usr/bin/env node
/** G03_R3：受控状态/响应测试（不是后台真实 404）。
 *  pending404 必须重试同一年；旧 da22 会先跳 126/130。 */
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const NEW_SRC = readFileSync(join(here, "app.js"), "utf8");
const OLD_SRC = execFileSync("git", ["show", "da22bfe:observer/web/app.js"], { encoding: "utf8" });

function el() {
  return {
    hidden: true, textContent: "", innerHTML: "", value: "0", max: "0",
    className: "", disabled: false,
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    style: {}, dataset: {},
    setAttribute() {}, getAttribute() { return null; },
    querySelector() { return null; }, querySelectorAll() { return []; },
    addEventListener() {}, remove() {}, appendChild(c) { return c; },
    scrollIntoView() {},
    getBoundingClientRect() { return { x: 0, y: 0, width: 10, height: 10 }; },
  };
}
function make(src) {
  const els = {};
  const pending = [];
  const urls = [];
  const ctx = {
    window: { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) },
    document: {
      getElementById(id) { return (els[id] = els[id] || el()); },
      querySelector() { return el(); }, querySelectorAll() { return []; },
      addEventListener() {}, documentElement: { clientWidth: 1440 }, body: el(),
      createElement() { return el(); },
      createElementNS() { const n = el(); n.appendChild = function () { return n; }; return n; },
    },
    location: { hash: "", search: "", href: "" },
    history: { replaceState() {} },
    sessionStorage: { getItem() { return ""; }, setItem() {} },
    performance: { now: Date.now }, console, setTimeout, clearTimeout,
    requestAnimationFrame: (fn) => setTimeout(fn, 0),
    cancelAnimationFrame: clearTimeout,
    fetch: (url) => {
      const u = String(url);
      urls.push(u);
      return new Promise((resolve, reject) => pending.push({ url: u, resolve, reject }));
    },
    URLSearchParams,
  };
  ctx.globalThis = ctx;
  ctx.window.__OBS_MANUAL_BOOT__ = true;
  vm.createContext(ctx);
  vm.runInContext(src, ctx);
  const O = ctx.window.__obs;
  ["setPlaying", "tickEvents", "tick", "bumpOp", "gotoYear", "afterPlayStep",
    "pendingCurrentYear", "retryYear", "openRun"].forEach((k) => {
    if (O && !O[k] && typeof ctx[k] === "function") O[k] = ctx[k];
  });
  const cells = [];
  for (let i = 0; i < 64; i++) cells.push({ i, row: 0, col: i % 8, passable: true, region: "A", neighbors: [] });
  O.S.map = { w: 8, h: 8, cells, barrier_cols: [] };
  O.S.cfg = { default_engine: "exp06", arms: {}, engines: {} };
  return { O, pending, urls, els };
}
function take(pending, part) {
  const i = pending.findIndex((p) => p.url.indexOf(part) >= 0);
  if (i < 0) return null;
  return pending.splice(i, 1)[0];
}
function wait(ms) { return new Promise((r) => setTimeout(r, ms)); }
function okBody(body) { return { ok: true, status: 200, json: async () => body }; }
function errBody(status, detail) {
  return { ok: false, status, json: async () => ({ detail: detail || ("HTTP " + status) }) };
}
function yearNums(urls) {
  return urls.map((u) => {
    const m = String(u).match(/\/year\/(\d+)/);
    return m ? Number(m[1]) : null;
  }).filter((n) => n != null);
}
const y124 = {
  t: 124, events: [{ id: "t124-aid-0", type: "aid", cell: 1, donor: "D", receiver: "R", text: "aid", source: "log" }],
  bands: [{ id: "R", name: "r", cell: 1, size: 10, store: 0, mem: {} }],
  year: { births_cum: 1, deaths_demo_cum: 0, mig_deaths_cum: 0, mig_total: 0 },
  agg: { pop: 200, bands: 6 }, cum: {},
  integrity: { conservation_error: 0, population_identity_error: 0, state_hash: "x" },
  stock: new Array(64).fill(0),
};
const y125 = {
  t: 125, events: [{ id: "t125-share-1", type: "share", cell: 0, donor: "D", receiver: "R", text: "share", source: "log" }],
  bands: [{ id: "R", name: "r", cell: 0, size: 10, store: 0, mem: {} }],
  year: { births_cum: 1, deaths_demo_cum: 0, mig_deaths_cum: 0, mig_total: 0 },
  agg: { pop: 282, bands: 6 }, cum: {},
  integrity: { conservation_error: 0, population_identity_error: 0, state_hash: "x" },
  stock: new Array(64).fill(0),
};
function setup(O, extra) {
  extra = extra || {};
  O.S.run = {
    run_id: extra.runId || "runA", years_recorded: extra.recorded != null ? extra.recorded : 150,
    years: 150, status: extra.status || "running", engine: "exp06", label: extra.runId || "runA",
  };
  O.S.t = extra.t != null ? extra.t : 124;
  O.S.lastOkT = O.S.t;
  O.S.epoch += 1;
  O.S.playing = extra.playing !== false;
  O.S.playMode = extra.mode || "year";
  O.S.selEvent = extra.selEvent != null ? extra.selEvent : "t124-aid-0";
  O.S.cam = { x: 3, y: 4, k: 1 };
  O.S.years = new Map();
  O.S.years.set(O.ykey(O.S.run.run_id, 124), y124);
  O.S.series = [];
  for (let t = 0; t <= 150; t++) {
    const evn = (t === 124 || t === 125 || t === 130) ? 1 : 0;
    O.S.series.push({ t: t, events: evn, agg: { pop: 120, bands: 6 }, year: {} });
  }
}

const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

async function first404ThenWatch(src, mode) {
  const { O, pending, urls } = make(src);
  setup(O, { mode: mode, playing: true, status: "running", recorded: 150, selEvent: "t124-aid-0" });
  if (mode === "events") O.tickEvents();
  else O.tick();
  await wait(20);
  const r1 = take(pending, "/year/125");
  if (!r1) return { O, pending, urls, missing: true };
  r1.resolve(errBody(404, "not yet"));
  await wait(30);
  return { O, pending, urls };
}

try {
  ok("old src 是 da22", OLD_SRC.indexOf("function afterPlayStep") >= 0 && OLD_SRC.indexOf("pendingCurrentYear") < 0);
  ok("new src 含 pendingCurrentYear", NEW_SRC.indexOf("function pendingCurrentYear") >= 0);

  {
    const { O, pending, urls, missing } = await first404ThenWatch(OLD_SRC, "year");
    ok("OLD year 发出 125", !missing, "missing first 125");
    await wait(850);
    const ys = yearNums(urls);
    ok("OLD year 700ms 后会请求 126（缺陷）", ys.indexOf(126) >= 0,
      JSON.stringify(ys));
    const late = take(pending, "/year/126");
    if (late) late.resolve(okBody(Object.assign({}, y125, { t: 126 })));
    void O;
  }
  {
    const { O, pending, urls, missing } = await first404ThenWatch(NEW_SRC, "year");
    ok("NEW year 发出 125", !missing);
    await wait(850);
    const ys = yearNums(urls);
    ok("NEW year 850ms 内只重试 125 不跳 126", ys.indexOf(126) < 0 && ys.indexOf(130) < 0 && ys.every((n) => n === 125),
      JSON.stringify(ys));
    const r2 = take(pending, "/year/125");
    ok("NEW year 仍在等 125", !!r2, "pending=" + pending.map((p) => p.url).join(","));
    if (r2) r2.resolve(okBody(y125));
    await wait(80);
    ok("NEW year 125 恢复后才有记录", !!(O.S.years.get(O.ykey("runA", 125))),
      "t=" + O.S.t + " pop=" + ((O.S.years.get(O.ykey("runA", 125)) || {}).agg || {}).pop);
    await wait(700);
    const later = yearNums(urls);
    ok("NEW year 125 呈现后才允许 126", later.indexOf(126) >= 0 && O.S.years.get(O.ykey("runA", 125)),
      JSON.stringify(later));
  }
  {
    const { O, pending, urls, missing } = await first404ThenWatch(OLD_SRC, "events");
    ok("OLD events 发出 125", !missing);
    await wait(850);
    const ys = yearNums(urls);
    ok("OLD events 700ms 后会请求 130（缺陷）", ys.indexOf(130) >= 0,
      JSON.stringify(ys));
    void O; void pending;
  }
  {
    const { O, pending, urls, missing } = await first404ThenWatch(NEW_SRC, "events");
    ok("NEW events 发出 125", !missing);
    await wait(850);
    const ys = yearNums(urls);
    ok("NEW events 850ms 内只重试 125 不跳 130", ys.indexOf(130) < 0 && ys.indexOf(126) < 0 && ys.every((n) => n === 125),
      JSON.stringify(ys));
    const r2 = take(pending, "/year/125");
    if (r2) r2.resolve(okBody(y125));
    await wait(120);
    const rec = O.S.years.get(O.ykey("runA", 125));
    ok("NEW events 125 恢复后事件可呈现", !!(rec && rec.events && rec.events[0] && rec.events[0].id === "t125-share-1"),
      JSON.stringify(rec && rec.events));
    await wait(1000);
    const later = yearNums(urls);
    ok("NEW events 125 之后才允许 130", later.indexOf(130) >= 0 && rec,
      JSON.stringify(later));
  }
  {
    const { O, pending, urls } = await first404ThenWatch(NEW_SRC, "year");
    const before = urls.length;
    O.setPlaying(false);
    await wait(850);
    const afterPause = yearNums(urls.slice(before));
    ok("NEW 暂停后不再自动重试/跳年", afterPause.length === 0 && O.S.playing === false,
      JSON.stringify({ afterPause, playing: O.S.playing, t: O.S.t }));
    take(pending, "/year/125");
  }
  {
    const { O, pending, urls } = await first404ThenWatch(NEW_SRC, "year");
    const before = urls.length;
    O.bumpOp();
    O.S.run = { run_id: "runB", years_recorded: 10, years: 10, status: "done", engine: "exp03", label: "B" };
    O.S.t = 0;
    O.S.playing = false;
    O.S.years = new Map();
    await wait(850);
    const after = urls.slice(before).filter((u) => u.indexOf("runA") >= 0 && /\/year\/(126|130)/.test(u));
    ok("NEW 换 run 后旧 125 等待不复活跳年", after.length === 0,
      JSON.stringify(urls.slice(before)));
    take(pending, "/year/125");
    void O;
  }
  {
    const { O, pending } = make(NEW_SRC);
    setup(O, { playing: true, mode: "year" });
    const myOp = O.S.opGen;
    const p = O.gotoYear(125, { quiet: true, opGen: myOp });
    await wait(10);
    take(pending, "/year/125").resolve(errBody(500, "boom"));
    const gy = await p;
    O.afterPlayStep(gy, myOp);
    ok("NEW 500 仍明确暂停", gy.kind === "failed" && O.S.playing === false && O.S.timer == null,
      JSON.stringify({ gy, playing: O.S.playing, timer: O.S.timer }));
  }
  {
    const { O, pending } = make(NEW_SRC);
    setup(O, { t: 0, playing: false, status: "running", recorded: 0, selEvent: null });
    O.S.years = new Map();
    const p = O.gotoYear(0, { opGen: O.S.opGen });
    await wait(10);
    take(pending, "/year/0").resolve(errBody(404, "not yet"));
    const gy = await p;
    ok("NEW 开局 0 仍是 pending404", gy.kind === "pending404" && gy.t === 0, JSON.stringify(gy));
    const p2 = O.gotoYear(0, { opGen: O.S.opGen });
    await wait(10);
    take(pending, "/year/0").resolve(okBody(Object.assign({}, y124, { t: 0, events: [] })));
    const gy2 = await p2;
    ok("NEW 开局 0 恢复不跳到 1", gy2.kind === "success" && O.S.t === 0, JSON.stringify({ gy2, t: O.S.t }));
  }
} catch (e) {
  out.push("FAIL 脚本出错 :: " + (e && e.stack ? e.stack : e));
}
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
