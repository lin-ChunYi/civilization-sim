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
  default_engine: "exp06",
  engines: {
    exp03: { engine_params: ["sigma_m", "move_mort_m"], params: [] },
    exp06: { engine_params: ["sigma_m", "move_mort_m", "share_m", "aid_m", "recip_m"],
      params: [{ name: "aid_m", min: 0, max: 1000, default: 0 }, { name: "recip_m", min: 0, max: 1000, default: 0 }] },
  },
};
["f-engine","f-seed","f-years","f-sigma","f-mort","f-share","f-aid","f-recip","f-arm","f-label"].forEach((id) => { els[id] = el(); });
els["f-engine"].value = "exp06"; els["f-seed"].value = "1"; els["f-years"].value = "10";
els["f-sigma"].value = "0"; els["f-mort"].value = "0"; els["f-share"].value = "0";
els["f-aid"].value = "0"; els["f-recip"].value = "1000"; els["f-arm"].value = "memory"; els["f-label"].value = "";
const out = [];
const ok = (n, c, d) => out.push((c ? "PASS" : "FAIL") + " " + n + (d ? " :: " + d : ""));
const d = O.collectRunDraft();
ok("W1 recip>0 且 AID=0 不暗改 AID", d.ok && d.body.aid_m === 0 && d.body.recip_m === 1000 && d.notes.length > 0, JSON.stringify(d));
O.applyForgePreset("recip");
ok("W2 援助+优先回助预设同时写 AID 与 RECIP", els["f-aid"].value === "1000" && els["f-recip"].value === "1000");
els["f-engine"].value = "exp03";
O.applyForgePreset("aid");
ok("W3 EXP03 无援助参数则不写 AID", els["f-aid"].value === "1000"); // applyForgePreset returns early, aid field leftover from before - check flash. For exp03 engineHasParam aid false, value unchanged.
const d3 = (els["f-engine"].value = "exp03", O.collectRunDraft());
ok("W4 EXP03 摘要不含编造的 AID_M=0 作为能力", d3.ok && d3.body.aid_m == null && /无此参数/.test(d3.summary), d3.summary);
const bad = (els["f-years"].value = "12.5", O.collectRunDraft());
ok("W5 小数年数被拒绝", !bad.ok, bad.error);
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
