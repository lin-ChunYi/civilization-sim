#!/usr/bin/env node
/** G04 返工：边卡绑定 run/year、jump 取消令牌、双向曲线分离。受控 VM，不是浏览器点击。 */
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
const here = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(join(here, "app.js"), "utf8");
function el() {
  return {
    hidden: true, textContent: "", innerHTML: "", value: "0",
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    style: {}, dataset: {}, setAttribute() {}, getAttribute() { return null; },
    querySelector() { return null; }, querySelectorAll() { return []; },
    addEventListener() {}, appendChild(c) { return c; },
  };
}
function make() {
  const els = {};
  const pending = [];
  const ctx = {
    window: { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) },
    document: {
      getElementById(id) { return (els[id] = els[id] || el()); },
      querySelector() { return el(); }, querySelectorAll() { return []; },
      addEventListener() {}, documentElement: { clientWidth: 1440 }, body: el(),
      createElement() { return el(); }, createElementNS() { return el(); },
    },
    location: { hash: "", search: "", href: "" }, history: { replaceState() {} },
    sessionStorage: { getItem() { return ""; }, setItem() {} },
    localStorage: { getItem() { return null; }, setItem() {} },
    performance: { now: Date.now }, console, setTimeout, clearTimeout,
    requestAnimationFrame: (fn) => setTimeout(fn, 0), cancelAnimationFrame: clearTimeout,
    fetch: (url) => new Promise((resolve, reject) => pending.push({ url: String(url), resolve, reject })),
    URLSearchParams,
  };
  ctx.globalThis = ctx; ctx.window.__OBS_MANUAL_BOOT__ = true;
  vm.createContext(ctx); vm.runInContext(SRC, ctx);
  const O = ctx.window.__obs;
  ["jumpToRecordedEvent", "clearRelEdgeCard", "fillRelEdgeCard", "renderRelations",
    "gotoYear", "bumpOp", "setPlaying", "focusEvent"].forEach((k) => {
    if (O && !O[k] && typeof ctx[k] === "function") O[k] = ctx[k];
  });
  const cells = [];
  for (let i = 0; i < 64; i++) cells.push({ i: i, region: "A", passable: true, neighbors: [] });
  O.S.map = { w: 8, h: 8, cells: cells, barrier_cols: [] };
  O.S.cfg = { default_engine: "exp06", arms: {}, engines: {} };
  return { O, pending, els, N: ctx.window.NetworkLogic };
}
function wait(ms) { return new Promise((r) => setTimeout(r, ms)); }
function jsonOk(body) { return { ok: true, status: 200, json: async () => body }; }
const y83 = {
  t: 83, events: [{ id: "t83-aid-3", type: "aid", cell: 1, donor: "D", receiver: "R", kcal: 6457, text: "aid", source: "log" }],
  bands: [{ id: "R", name: "r", cell: 1, size: 17, store: 0, mem: {} }],
  year: { births_cum: 0, deaths_demo_cum: 0, mig_deaths_cum: 0, mig_total: 0 },
  agg: { pop: 17, bands: 1 }, cum: {}, integrity: { conservation_error: 0, population_identity_error: 0, state_hash: "x" },
  stock: new Array(8).fill(0),
};
const y0 = {
  t: 0, events: [], bands: [{ id: "R", name: "r", cell: 0, size: 10, store: 0, mem: {} }],
  year: { births_cum: 0, deaths_demo_cum: 0, mig_deaths_cum: 0, mig_total: 0 },
  agg: { pop: 10, bands: 1 }, cum: {}, integrity: { conservation_error: 0, population_identity_error: 0, state_hash: "x" },
  stock: new Array(8).fill(0),
};
const out = [];
const ok = (n, c, d) => out.push((c ? "PASS" : "FAIL") + " " + n + (d ? " :: " + d : ""));
try {
  const { N } = make();
  const edges = [
    { donor: "A", receiver: "B" },
    { donor: "B", receiver: "A" },
  ];
  const s1 = N.edgeBendSign(edges, "A", "B");
  const s2 = N.edgeBendSign(edges, "B", "A");
  const c1 = N.quadControl(0, 0, 100, 0, s1, 38);
  const c2 = N.quadControl(100, 0, 0, 0, s2, 38);
  const dist = Math.hypot(c1.x - c2.x, c1.y - c2.y);
  ok("F1 双向控制点分离", s1 === -s2 && dist > 20, JSON.stringify({ s1, s2, c1, c2, dist }));

  {
    const { O, els } = make();
    O.S.run = { run_id: "exp06", years_recorded: 150, years: 150, status: "done" };
    O.S.t = 124; O.S.bandScope = "as_of";
    const d124 = {
      history_scope: { mode: "as_of_year", at_year: 124 },
      nodes: [{ id: "A", name: "甲" }, { id: "B", name: "乙" }],
      edges: [{ donor: "A", receiver: "B", kcal: 1, transfers: 1, last_year: 124, event_ids: ["t124-aid-1"], phase_counts: { normal: 1, recip: 0 }, repay_transfers: 0 }],
      totals: { nodes: 2, edges: 1, transfers: 1, kcal: 1 }, diagnostics: {},
    };
    O.renderRelations(d124);
    O.S.relSel = 0;
    O.fillRelEdgeCard(d124.edges[0], d124.nodes);
    ok("F2 选中边卡可见且含 124", els["net-edge-card"].hidden === false && /t124-aid-1/.test(els["net-edge-card"].innerHTML), els["net-edge-card"].innerHTML.slice(0, 120));
    O.S.t = 0;
    const d0 = { history_scope: { mode: "as_of_year", at_year: 0 }, nodes: [], edges: [], totals: { nodes: 0, edges: 0, transfers: 0, kcal: 0 }, diagnostics: {} };
    O.renderRelations(d0);
    ok("F3 换年后面卡清空", els["net-edge-card"].hidden === true && !els["net-edge-card"].innerHTML, "hidden=" + els["net-edge-card"].hidden + " html=" + els["net-edge-card"].innerHTML);
  }
  {
    const { O, els } = make();
    O.S.run = { run_id: "exp06", years_recorded: 150, years: 150, status: "done" };
    O.S.t = 124;
    const d124 = {
      history_scope: { mode: "as_of_year", at_year: 124 },
      nodes: [{ id: "A", name: "甲" }],
      edges: [{ donor: "A", receiver: "B", kcal: 1, transfers: 1, last_year: 125, event_ids: ["t125-aid-6"], phase_counts: { normal: 1, recip: 0 }, repay_transfers: 0 }],
      totals: { nodes: 1, edges: 1, transfers: 1, kcal: 1 }, diagnostics: {},
    };
    O.renderRelations(d124);
    O.fillRelEdgeCard(d124.edges[0], d124.nodes);
    O.S.run = { run_id: "s4242", years_recorded: 120, years: 120, status: "done", engine: "exp03" };
    O.S.t = 50;
    O.renderRelations({ history_scope: { mode: "as_of_year", at_year: 50 }, nodes: [], edges: [], totals: { nodes: 0, edges: 0, transfers: 0, kcal: 0 }, diagnostics: {} });
    ok("F4 换 EXP03 后面卡清空", els["net-edge-card"].hidden === true && !/t125/.test(els["net-edge-card"].innerHTML || ""));
  }
  {
    const { O, pending } = make();
    O.S.run = { run_id: "runA", years_recorded: 150, years: 150, status: "done" };
    O.S.t = 0; O.S.epoch = 1;
    O.S.years = new Map();
    O.S.years.set(O.ykey("runA", 0), y0);
    const p = O.jumpToRecordedEvent("t83-aid-3", 83);
    await wait(5);
    const req = pending.find((x) => x.url.indexOf("/year/83") >= 0);
    O.bumpOp();
    O.S.run = { run_id: "runB", years_recorded: 150, years: 150, status: "done" };
    O.S.t = 0; O.S.epoch += 1;
    O.S.years.set(O.ykey("runB", 0), y0);
    O.S.years.set(O.ykey("runB", 83), y83);
    O.S.selEvent = null; O.S.selCell = null;
    if (req) req.resolve(jsonOk(y83));
    const r = await p;
    ok("F5 A83 延迟后切 B0 不跳错", r && r.ok === false && O.S.run.run_id === "runB" && O.S.t === 0 && O.S.selEvent == null,
      JSON.stringify({ r, t: O.S.t, run: O.S.run.run_id, ev: O.S.selEvent }));
  }
  {
    const { O, pending } = make();
    O.S.run = { run_id: "runA", years_recorded: 150, years: 150, status: "done" };
    O.S.t = 0; O.S.epoch = 1;
    O.S.years = new Map();
    O.S.years.set(O.ykey("runA", 0), y0);
    O.S.years.set(O.ykey("runA", 83), y83);
    const p = O.jumpToRecordedEvent("t83-aid-3", 83);
    await wait(5);
    pending.filter((x) => x.url.indexOf("/year/83") >= 0).forEach((x) => x.resolve(jsonOk(y83)));
    const r = await p;
    ok("F6 同 run 跳 t83-aid-3 成功", r && r.ok && O.S.t === 83 && O.S.selEvent === "t83-aid-3",
      JSON.stringify({ r, t: O.S.t, ev: O.S.selEvent }));
  }
} catch (e) {
  out.push("FAIL 脚本出错 :: " + (e && e.stack ? e.stack : e));
}
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
