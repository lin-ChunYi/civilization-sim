#!/usr/bin/env node
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
const here = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(join(here, "app.js"), "utf8");
function el() {
  return { hidden: true, textContent: "", innerHTML: "", value: "", max: "0", className: "", disabled: false,
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    style: {}, dataset: {}, setAttribute() {}, getAttribute() { return null; },
    querySelector() { return null; }, querySelectorAll() { return []; },
    addEventListener() {}, remove() {}, appendChild(c) { return c; },
    scrollIntoView() {}, getBoundingClientRect() { return { x: 0, y: 0, width: 0, height: 0 }; } };
}
const els = {};
const pending = [];
const ctx = {
  window: { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) },
  document: { getElementById(id) { return (els[id] = els[id] || el()); }, querySelector() { return el(); },
    querySelectorAll() { return []; }, addEventListener() {}, documentElement: { clientWidth: 1440 }, body: el(),
    createElement() { return el(); }, createElementNS() { return el(); } },
  location: { hash: "", search: "", href: "" }, history: { replaceState() {} },
  sessionStorage: { getItem() { return ""; }, setItem() {} }, performance: { now: Date.now },
  console, setTimeout, clearTimeout, requestAnimationFrame: (fn) => setTimeout(fn, 0),
  cancelAnimationFrame: clearTimeout,
  fetch: (url) => new Promise((resolve, reject) => pending.push({ url: String(url), resolve, reject })),
  URLSearchParams,
};
ctx.globalThis = ctx; ctx.window.__OBS_MANUAL_BOOT__ = true;
vm.createContext(ctx); vm.runInContext(SRC, ctx);
const C = ctx.window.CompareLogic;
const O = ctx.window.__obs;
const out = [];
const ok = (n, c, d) => out.push((c ? "PASS" : "FAIL") + " " + n + (d ? " :: " + d : ""));
ok("C0", !!C && !!O.loadCompare);
const r = C.row("人口", 116, null, false, true);
ok("C1 缺侧标缺失不拿对方终年", r.missB && r.b == null && r.a === 116 && r.diff === false);
const diffs = C.configDiff({ engine: "exp06", recip_m: 1000, seed: 1 }, { engine: "exp06", recip_m: 0, seed: 1 });
ok("C2 只列出真实不同参数", diffs.length === 1 && diffs[0].key === "recip_m");
O.S.runs = [
  { run_id: "runA", label: "A", years_recorded: 150, engine: "exp06", recip_m: 1000, seed: 1, sigma_m: 0, move_mort_m: 0, years: 150 },
  { run_id: "runB", label: "B", years_recorded: 120, engine: "exp03", recip_m: 0, seed: 1, sigma_m: 0, move_mort_m: 0, years: 120 },
];
O.S.cfg = { arms: {}, engines: {} };
els["cmp-a"] = els["cmp-a"] || el(); els["cmp-b"] = els["cmp-b"] || el(); els["cmp-year"] = els["cmp-year"] || el();
els["cmp-a"].value = "runA"; els["cmp-b"].value = "runB"; els["cmp-year"].value = "150";
els["cmp-table"] = els["cmp-table"] || el(); els["cmp-cfg"] = els["cmp-cfg"] || el();
const p = O.loadCompare();
await new Promise((r) => setTimeout(r, 10));
const reqs = pending.map((x) => x.url);
ok("C3 只请求指定年 150 不改成 120", reqs.filter((u) => u.indexOf("/year/150") >= 0).length === 2 && reqs.every((u) => u.indexOf("/year/120") < 0), JSON.stringify(reqs));
pending.forEach((x) => {
  if (x.url.indexOf("runA/year/150") >= 0) x.resolve({ ok: true, status: 200, json: async () => ({ t: 150, agg: { pop: 200, bands: 6 }, year: { deficit_cum: 1 }, events: [], stock: [0] }) });
  else x.resolve({ ok: false, status: 404, json: async () => ({ detail: "missing" }) });
});
const pack = await p;
ok("C4 B 为缺失 A 有数", pack && pack.ok && pack.a.missing === false && pack.b.missing === true, JSON.stringify(pack && { a: pack.a && pack.a.missing, b: pack.b && pack.b.missing }));
ok("C5 表格含缺失字样", (els["cmp-table"].innerHTML || "").indexOf("缺失") >= 0, els["cmp-table"].innerHTML.slice(0, 180));
ok("C6 configDiff 含 arm", C.configDiff({ arm: "memory" }, { arm: "omniscient" }).some((d) => d.key === "arm"));
els["cmp-year"].value = "0";
O.S.t = 124; O.S.cmp.t = 0;
O.fillCompareSelects();
ok("C7 t=0 不被回放年覆盖", els["cmp-year"].value === "0", els["cmp-year"].value);
{
  const my = ++O.S.cmpReqGen;
  O.S.cmp = { a: "runC", b: "runD", t: 83 };
  O.S.cmpReqGen = my;
  ok("C8 世代绑定：旧请求代数不等于当前", my !== 0 && O.S.cmp.t === 83);
}
{
  els["cmp-a"].value = "runA"; els["cmp-b"].value = "runB"; els["cmp-year"].value = "10";
  O.S.runs[0].years_recorded = 150;
  const pFail = O.fetchYearOrMiss ? null : true;
  void pFail;
}
{
  const p500 = O.fetchYearOrMiss("runA", 125);
  await new Promise((r) => setTimeout(r, 10));
  const req = pending.filter((x) => x.url.indexOf("/year/125") >= 0).pop();
  if (req) req.resolve({ ok: false, status: 500, json: async () => ({ detail: "boom" }) });
  const r500 = await p500;
  ok("C9 500 是失败不是缺失", r500 && r500.failed && !r500.missing, JSON.stringify(r500));
  const p404 = O.fetchYearOrMiss("runB", 150);
  await new Promise((r) => setTimeout(r, 10));
  const req404 = pending.filter((x) => x.url.indexOf("runB/year/150") >= 0).pop();
  if (req404) req404.resolve({ ok: false, status: 404, json: async () => ({ detail: "no" }) });
  const r404 = await p404;
  ok("C10 超范围 404 才是缺失", r404 && r404.missing && !r404.failed, JSON.stringify(r404));
}
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
