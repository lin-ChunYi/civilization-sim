#!/usr/bin/env node
/** G03_R2 导航收尾契约 VM：success/stale/pending404/failed。不访问真实网络。 */
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(join(here, "app.js"), "utf8");

function el() {
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
    appendChild(c) { return c; },
    scrollIntoView() {},
    getBoundingClientRect() { return { x: 0, y: 0, width: 10, height: 10 }; },
  };
  return n;
}
function make() {
  const els = {};
  const pending = [];
  const document = {
    getElementById(id) { return (els[id] = els[id] || el()); },
    querySelector() { return el(); },
    querySelectorAll() { return []; },
    addEventListener() {},
    documentElement: { clientWidth: 1440 },
    body: el(),
    createElement() { return el(); },
    createElementNS() { const n = el(); n.appendChild = function () { return n; }; return n; },
  };
  const ctx = {
    window: { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) },
    document, location: { hash: "", search: "", href: "" },
    history: { replaceState() {} },
    sessionStorage: { getItem() { return ""; }, setItem() {} },
    performance: { now: Date.now }, console, setTimeout, clearTimeout,
    requestAnimationFrame: (fn) => setTimeout(fn, 0),
    cancelAnimationFrame: clearTimeout,
    fetch: (url) => new Promise((resolve, reject) => pending.push({ url: String(url), resolve, reject })),
    URLSearchParams,
  };
  ctx.globalThis = ctx;
  ctx.window.__OBS_MANUAL_BOOT__ = true;
  vm.createContext(ctx);
  vm.runInContext(SRC, ctx);
  const O = ctx.window.__obs;
  ["setPlaying", "tickEvents", "tick", "bumpOp", "gotoYear", "afterPlayStep",
    "beginYearLoad", "endYearLoad", "retryYear", "reapNavUi"].forEach((k) => {
    if (O && !O[k] && typeof ctx[k] === "function") O[k] = ctx[k];
  });
  const cells = [];
  for (let i = 0; i < 64; i++) cells.push({ i, row: 0, col: i % 8, passable: true, region: "A", neighbors: [] });
  O.S.map = { w: 8, h: 8, cells, barrier_cols: [] };
  O.S.cfg = { default_engine: "exp06", arms: {}, engines: {} };
  return { O, pending, els };
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
const y124 = {
  t: 124, events: [{ id: "t124-aid-0", type: "aid", cell: 1, donor: "D", receiver: "R", text: "aid", source: "log" }],
  bands: [{ id: "R", name: "r", cell: 1, size: 10, store: 0, mem: {} }],
  year: { births_cum: 1, deaths_demo_cum: 0, mig_deaths_cum: 0, mig_total: 0 },
  agg: { pop: 200, bands: 6 }, cum: {},
  aid: { events: 1, transfers: 2, kcal: 1 },
  recip: { repay_transfers: 1, transfers: 0, changed: 0 },
  integrity: { conservation_error: 0, population_identity_error: 0, state_hash: "x" },
  stock: new Array(64).fill(0),
};
const y125 = {
  t: 125, events: [{ id: "t125-share-1", type: "share", cell: 0, donor: "D", receiver: "R", text: "s", source: "log" }],
  bands: [{ id: "R", name: "r", cell: 1, size: 10, store: 0, mem: {} }],
  year: { births_cum: 1, deaths_demo_cum: 0, mig_deaths_cum: 0, mig_total: 0 },
  agg: { pop: 201, bands: 6 }, cum: {},
  integrity: { conservation_error: 0, population_identity_error: 0, state_hash: "x" },
  stock: new Array(64).fill(0),
};
function setup(O, extra) {
  extra = extra || {};
  O.S.run = {
    run_id: "runA", years_recorded: extra.recorded != null ? extra.recorded : 150,
    years: 150, status: extra.status || "done", engine: "exp06", label: "runA",
  };
  O.S.t = extra.t != null ? extra.t : 124;
  O.S.lastOkT = O.S.t;
  O.S.epoch += 1;
  O.S.playing = !!extra.playing;
  O.S.playMode = extra.mode || "year";
  O.S.selEvent = extra.selEvent || "t124-aid-0";
  O.S.cam = { x: 3, y: 4, k: 1 };
  O.S.years = new Map();
  O.S.years.set(O.ykey("runA", 124), y124);
  if (extra.t === 0) O.S.years.set(O.ykey("runA", 0), Object.assign({}, y124, { t: 0, events: [], aid: null, recip: null }));
  O.S.series = [];
  for (let t = 0; t <= (O.S.run.years_recorded || 0); t++) {
    O.S.series.push({ t: t, events: (t === 124 || t === 125) ? 1 : 0, agg: { pop: 120, bands: 6 }, year: {} });
  }
}

const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

try {
  {
    const { O, pending, els } = make();
    setup(O, { playing: true });
    const p = O.gotoYear(125, { quiet: true, opGen: O.S.opGen });
    await wait(5);
    ok("R2-1 加载中遮罩打开", els["year-load"] && els["year-load"].hidden === false,
      "hidden=" + (els["year-load"] && els["year-load"].hidden));
    O.setPlaying(false);
    ok("R2-2 暂停后遮罩关闭", els["year-load"].hidden === true && O.S.t === 124,
      JSON.stringify({ hidden: els["year-load"].hidden, t: O.S.t, playing: O.S.playing }));
    const yreq = take(pending, "/year/125");
    if (yreq) yreq.resolve(okBody(y125));
    const gy = await p;
    ok("R2-3 晚到 125 是 stale 且年份仍 124", gy && gy.kind === "stale" && O.S.t === 124 && els["year-load"].hidden === true,
      JSON.stringify({ gy, t: O.S.t, hidden: els["year-load"].hidden }));
  }
  {
    const { O, pending, els } = make();
    setup(O, { t: 124 });
    const p125 = O.gotoYear(125, { quiet: true, opGen: O.S.opGen });
    await wait(5);
    O.bumpOp();
    const p80 = O.gotoYear(80, { opGen: O.S.opGen });
    await wait(5);
    const n80 = els["year-load-n"] && els["year-load-n"].textContent;
    const r125 = take(pending, "/year/125");
    if (r125) r125.resolve(okBody(y125));
    await p125;
    ok("R2-4 旧 125 返回不清新遮罩", els["year-load"].hidden === false && String(n80) === "80",
      JSON.stringify({ hidden: els["year-load"].hidden, n: n80, overlay: O.S.loadOverlay }));
    const r80 = take(pending, "/year/80");
    if (r80) r80.resolve(okBody(Object.assign({}, y124, { t: 80, events: [], aid: null, recip: null })));
    await p80;
  }
  {
    const { O, pending, els } = make();
    setup(O, { playing: true, mode: "year" });
    els["year-metrics"] = els["year-metrics"] || el();
    els["year-metrics"].innerHTML = "<span class=\"metric-chip\"><b>活动</b> 1</span>";
    const myOp = O.S.opGen;
    const p = O.gotoYear(125, { quiet: true, opGen: myOp });
    await wait(5);
    const yreq = take(pending, "/year/125");
    if (yreq) yreq.resolve(errBody(500, "boom"));
    const gy = await p;
    O.afterPlayStep(gy, myOp);
    const chips = els["year-metrics"].innerHTML;
    const failText = (els["year-fail-text"] && els["year-fail-text"].textContent) || "";
    ok("R2-5 year/500 明确暂停且有失败口径",
      gy.kind === "failed" && O.S.playing === false && O.S.timer == null && O.S.t === 125 &&
      O.S.yearWait && O.S.yearWait.pending === false && chips.indexOf("活动") < 0 && /125/.test(failText),
      JSON.stringify({ gy, playing: O.S.playing, timer: O.S.timer, t: O.S.t, chips: chips.slice(0, 80), fail: failText.slice(0, 80) }));
  }
  {
    const { O, pending } = make();
    setup(O, { playing: true, mode: "events", recorded: 150 });
    const myOp = O.S.opGen;
    const p = O.tickEvents();
    await wait(5);
    const yreq = take(pending, "/year/125");
    if (yreq) yreq.resolve(errBody(500, "boom"));
    await p;
    ok("R2-6 events/500 不保持空调度播放",
      O.S.playing === false && O.S.timer == null && O.S.t === 125 && O.S.yearWait && !O.S.yearWait.pending,
      JSON.stringify({ playing: O.S.playing, timer: O.S.timer, t: O.S.t, wait: O.S.yearWait }));
  }
  {
    const { O, pending } = make();
    setup(O, { playing: true, t: 124, status: "done", recorded: 150, selEvent: "t124-aid-0" });
    const myOp = O.S.opGen;
    const p = O.gotoYear(125, { quiet: true, opGen: myOp });
    await wait(5);
    const yreq = take(pending, "/year/125");
    if (yreq) yreq.resolve(errBody(404, "not yet"));
    const gy = await p;
    O.afterPlayStep(gy, myOp);
    ok("R2-7 year/404 待计算有界等待",
      gy.kind === "pending404" && gy.t === 125 && O.S.playing === true && O.S.timer != null && O.S.yearWait && O.S.yearWait.pending === true,
      JSON.stringify({ gy, playing: O.S.playing, timer: !!O.S.timer, wait: O.S.yearWait }));
    clearTimeout(O.S.timer); O.S.timer = null; O.setPlaying(false);
  }
  {
    const { O, pending } = make();
    setup(O, { playing: true, mode: "events", t: 124, status: "done", recorded: 150, selEvent: "t124-aid-0" });
    const p = O.tickEvents();
    await wait(5);
    const yreq = take(pending, "/year/125");
    if (yreq) yreq.resolve(errBody(404, "not yet"));
    await p;
    ok("R2-8 events/404 待计算仍有 timer",
      O.S.playing === true && O.S.timer != null && O.S.yearWait && O.S.yearWait.pending === true,
      JSON.stringify({ playing: O.S.playing, timer: !!O.S.timer, wait: O.S.yearWait, t: O.S.t }));
    clearTimeout(O.S.timer); O.S.timer = null; O.setPlaying(false);
  }
  {
    const { O, pending, els } = make();
    setup(O, { playing: false });
    const pFail = O.gotoYear(125, { opGen: O.S.opGen });
    await wait(5);
    take(pending, "/year/125").resolve(errBody(500, "boom"));
    await pFail;
    ok("R2-9 失败后 chips 已清空", (els["year-metrics"].innerHTML || "").indexOf("活动") < 0,
      els["year-metrics"].innerHTML);
    const pRetry = O.retryYear();
    await wait(5);
    take(pending, "/year/125").resolve(okBody(y125));
    const gy = await pRetry;
    ok("R2-10 重试 125 恢复成功", gy && gy.kind === "success" && O.S.t === 125 && O.S.years.get(O.ykey("runA", 125)),
      JSON.stringify({ gy, t: O.S.t }));
  }
  {
    const { O, pending } = make();
    setup(O, { t: 0, status: "running", recorded: 0, playing: false, selEvent: null });
    O.S.years = new Map();
    const p = O.gotoYear(0, { opGen: O.S.opGen });
    await wait(5);
    take(pending, "/year/0").resolve(errBody(404, "not yet"));
    const gy = await p;
    ok("R2-11 新世界开局 404 是 pending 可自动恢复",
      gy.kind === "pending404" && O.S.yearWait && O.S.yearWait.pending,
      JSON.stringify(gy));
    const rec0 = Object.assign({}, y124, { t: 0, events: [], aid: null, recip: null, agg: { pop: 120, bands: 6 } });
    const p2 = O.gotoYear(0, { opGen: O.S.opGen });
    await wait(5);
    take(pending, "/year/0").resolve(okBody(rec0));
    const gy2 = await p2;
    ok("R2-12 开局 404 后重试成功", gy2.kind === "success" && O.S.t === 0 && O.S.years.get(O.ykey("runA", 0)),
      JSON.stringify(gy2));
  }
} catch (e) {
  out.push("FAIL 脚本出错 :: " + (e && e.stack ? e.stack : e));
}
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
