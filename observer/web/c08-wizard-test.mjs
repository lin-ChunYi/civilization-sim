#!/usr/bin/env node
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
const here = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(join(here, "app.js"), "utf8");
function el(extra) {
  return Object.assign({ hidden: true, textContent: "", innerHTML: "", value: "", className: "", disabled: false,
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    style: {}, dataset: {}, setAttribute() {}, getAttribute() { return null; },
    querySelector() { return null; }, querySelectorAll() { return []; }, addEventListener() {},
    appendChild(c) { return c; } }, extra || {});
}
const els = {};
const ctx = {
  window: { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) },
  document: { getElementById(id) { return (els[id] = els[id] || el()); }, querySelector() { return el(); },
    querySelectorAll() { return []; }, addEventListener() {}, documentElement: { clientWidth: 800 }, body: el(),
    createElement() { return el(); }, createElementNS() { return el(); } },
  location: { hash: "", search: "", href: "" }, history: { replaceState() {} },
  sessionStorage: { getItem() { return ""; }, setItem() {} }, performance: { now: Date.now },
  console, setTimeout, clearTimeout, requestAnimationFrame: (fn) => setTimeout(fn, 0),
  cancelAnimationFrame: clearTimeout, fetch: () => Promise.resolve({ ok: true, json: async () => ({}) }),
  URLSearchParams,
};
ctx.globalThis = ctx; ctx.window.__OBS_MANUAL_BOOT__ = true;
vm.createContext(ctx); vm.runInContext(SRC, ctx);
const O = ctx.window.__obs;
O.S.cfg = {
  limits: { max_seed: 1e9, min_years: 1, max_years: 500 },
  default_engine: "exp03",
  engines: {
    exp01: { engine_params: [], params: [{ name: "seed" }, { name: "years" }] },
    exp02: { engine_params: ["sigma_m"], params: [{ name: "sigma_m", min: 0, max: 1000, default: 0 }] },
    exp03: { engine_params: ["sigma_m", "move_mort_m"], params: [] },
  },
};
["f-engine","f-seed","f-years","f-sigma","f-mort","f-share","f-aid","f-recip","f-arm","f-label",
 "f-sigma-wrap","f-mort-wrap","f-share-wrap","f-aid-wrap","f-recip-wrap"].forEach((id) => { els[id] = el(); });
els["f-engine"].value = "exp01"; els["f-seed"].value = "31337"; els["f-years"].value = "4";
els["f-sigma"].value = "400"; els["f-mort"].value = "50"; els["f-arm"].value = "memory"; els["f-label"].value = "";
const out = [];
const ok = (n, c, d) => out.push((c ? "PASS" : "FAIL") + " " + n + (d ? " :: " + d : ""));
O.syncEngineForm();
ok("W01 exp01 hides sigma/mort", els["f-sigma-wrap"].hidden === true && els["f-mort-wrap"].hidden === true);
const d1 = O.collectRunDraft();
ok("W02 exp01 draft ok without reading hidden sigma", d1.ok === true && d1.body.engine === "exp01"
  && d1.body.sigma_m === 0 && d1.body.move_mort_m === 0, JSON.stringify(d1));
ok("W03 exp01 summary does not claim SIGMA as a capability",
  d1.ok && /SIGMA_M 此引擎无此参数/.test(d1.summary) && /MOVE_MORT_M 此引擎无此参数/.test(d1.summary),
  d1.summary);
els["f-years"].value = "12.5";
const bad = O.collectRunDraft();
ok("W04 invalid years still rejected", !bad.ok);
els["f-years"].value = "4";
els["f-engine"].value = "exp02";
O.syncEngineForm();
els["f-sigma"].value = "1000";
ok("W05 exp02 shows sigma hides mort", els["f-sigma-wrap"].hidden === false && els["f-mort-wrap"].hidden === true);
const d2 = O.collectRunDraft();
ok("W06 exp02 sigma 1000 is submitted", d2.ok && d2.body.sigma_m === 1000 && /SIGMA_M 1000/.test(d2.summary)
  && /MOVE_MORT_M 此引擎无此参数/.test(d2.summary), d2.summary);
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
