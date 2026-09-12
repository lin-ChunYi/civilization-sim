#!/usr/bin/env node
/** G04 按年档案与有向关系网。受控数据，ID 保持字符串。 */
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(join(here, "app.js"), "utf8");
function el() {
  return {
    hidden: true, textContent: "", innerHTML: "", value: "0", max: "0",
    className: "", disabled: false, classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    style: {}, dataset: {}, setAttribute() {}, getAttribute() { return null; },
    querySelector() { return null; }, querySelectorAll() { return []; },
    addEventListener() {}, remove() {}, appendChild(c) { return c; },
    scrollIntoView() {}, getBoundingClientRect() { return { x: 0, y: 0, width: 10, height: 10 }; },
  };
}
const els = {};
const pending = [];
const ctx = {
  window: { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) },
  document: {
    getElementById(id) { return (els[id] = els[id] || el()); },
    querySelector() { return el(); }, querySelectorAll() { return []; },
    addEventListener() {}, documentElement: { clientWidth: 1440 }, body: el(),
    createElement() { return el(); },
    createElementNS() { const n = el(); n.appendChild = function () { return n; }; return n; },
  },
  location: { hash: "", search: "", href: "" }, history: { replaceState() {} },
  sessionStorage: { getItem() { return ""; }, setItem() {} },
  performance: { now: Date.now }, console, setTimeout, clearTimeout,
  requestAnimationFrame: (fn) => setTimeout(fn, 0), cancelAnimationFrame: clearTimeout,
  fetch: (url) => new Promise((resolve, reject) => pending.push({ url: String(url), resolve, reject })),
  URLSearchParams,
};
ctx.globalThis = ctx; ctx.window.__OBS_MANUAL_BOOT__ = true;
vm.createContext(ctx); vm.runInContext(SRC, ctx);
const N = ctx.window.NetworkLogic;
const D = ctx.window.DirectorLogic;
const O = ctx.window.__obs;
const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

const BIG = "18446744073709551557";
ok("N0 NetworkLogic", !!N && !!D);
ok("N1 64bit id 保持字符串", N.idStr(BIG) === BIG && N.idStr(BIG).length > 15);
const traj = [[0, 0], [72, 1], [75, 2], [79, 1], [84, 0], [125, 1], [131, 0]];
ok("N2 at_year=124 不含未来 125/131", N.futureSteps(traj, 124).map((p) => p[0]).join() === "125,131");
ok("N3 全档案不筛未来", N.futureSteps(traj, null).length === 0);
const ends = N.migrateEndpoints([[0, 0], [72, 1], [75, 1], [84, 0]]);
ok("N4 迁移只给端点且同格不编路径", ends.length === 2 && ends[0].from === 0 && ends[0].to === 1 && ends[1].from === 1 && ends[1].to === 0);
const edges = [
  { donor: "A", receiver: "B", kcal: 1, transfers: 1, repay_transfers: 0, phase_counts: { normal: 1, recip: 0 } },
  { donor: "B", receiver: "A", kcal: 2, transfers: 1, repay_transfers: 1, phase_counts: { normal: 0, recip: 1 } },
];
ok("N5 A→B 与 B→A 是双向记录仍为两条", N.pairKind(edges, "A", "B") === "two-way" && N.pairKind(edges, "C", "A") === "one-way");
const laid = N.layoutCircle([{ id: "A" }, { id: "B" }, { id: BIG }], 200, 200);
ok("N6 圆布局不是格子坐标", laid.length === 3 && laid[2].id === BIG && laid[0].x !== laid[1].x);
ok("N7 展示年不用 raw tick", D.displayYearFromMemory({ last_year: 82, last_year_display: 83, last_event_id: "t83-aid-3" }).year === 83);
ok("N8 spark 至少两点才有路径", N.sparkPath([[0, 10]], 100, 20) === "" && N.sparkPath([[0, 10], [10, 20]], 100, 20).indexOf("M") === 0);

const rel124 = {
  history_scope: { mode: "as_of_year", at_year: 124 },
  nodes: [{ id: BIG, name: "x", alive_at_year: true, cell: 0, last_seen_year: 124 }],
  edges: [{ donor: "A", receiver: "B", kcal: 6457, transfers: 1, last_year: 83, last_event_id: "t83-aid-3",
    phase_counts: { recip: 0, normal: 1 }, repay_transfers: 0, event_ids: ["t83-aid-3"] }],
  totals: { nodes: 1, edges: 1, transfers: 1, kcal: 6457 },
  diagnostics: { recip_changed_cellyears: 0 },
};
O.S.run = { run_id: "preset-exp06-recip1000", years_recorded: 150, years: 150, status: "done", engine: "exp06" };
O.S.t = 124; O.S.bandScope = "as_of"; O.S.epoch = 1; O.S.map = { cells: [] };
const p = O.loadRelations();
const hit = pending.find((x) => x.url.indexOf("/relations") >= 0);
ok("N9 relations 默认带 at_year=124", !!(hit && hit.url.indexOf("at_year=124") >= 0), hit && hit.url);
if (hit) hit.resolve({ ok: true, status: 200, json: async () => rel124 });
await p;
ok("N10 加载后口径 as_of", O.S.relations && O.S.relations.history_scope.mode === "as_of_year");
ok("N11 边 id 仍是字符串", typeof O.S.relations.edges[0].donor === "string");

O.S.bandScope = "full";
const p2 = O.loadRelations();
const hit2 = pending.find((x) => x.url.indexOf("/relations") >= 0 && x.url.indexOf("at_year") < 0);
ok("N12 全档案省略 at_year", !!hit2, hit2 && hit2.url);
if (hit2) hit2.resolve({ ok: true, status: 200, json: async () => Object.assign({}, rel124, { history_scope: { mode: "full" } }) });
await p2;
ok("N13 全档案 mode=full", O.S.relations.history_scope.mode === "full");

const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
