#!/usr/bin/env node
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
const here = dirname(fileURLToPath(import.meta.url));
const SRC = readFileSync(join(here, "app.js"), "utf8");
const store = {};
const ctx = {
  window: { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) },
  document: { getElementById() { return { hidden: true, textContent: "", innerHTML: "", value: "", classList: { add() {}, remove() {}, toggle() {} }, style: {}, querySelectorAll() { return []; }, addEventListener() {} }; },
    querySelector() { return null; }, querySelectorAll() { return []; }, addEventListener() {},
    documentElement: { clientWidth: 800 }, body: {}, createElement() { return { click() {}, href: "", download: "" }; }, createElementNS() { return {}; } },
  location: { hash: "", search: "", href: "" }, history: { replaceState() {} },
  sessionStorage: { getItem() { return ""; }, setItem() {} },
  localStorage: { getItem(k) { return store[k] || null; }, setItem(k, v) { store[k] = String(v); } },
  performance: { now: Date.now }, console, setTimeout, clearTimeout,
  requestAnimationFrame: (fn) => setTimeout(fn, 0), cancelAnimationFrame: clearTimeout,
  fetch: () => Promise.resolve({ ok: true, json: async () => ({}) }), URLSearchParams, URL,
};
ctx.globalThis = ctx; ctx.window.__OBS_MANUAL_BOOT__ = true;
vm.createContext(ctx); vm.runInContext(SRC, ctx);
const L = ctx.window.LibraryLogic;
const out = [];
const ok = (n, c, d) => out.push((c ? "PASS" : "FAIL") + " " + n + (d ? " :: " + d : ""));
let all = {};
all = L.pinYear(all, "runA", 83);
all = L.pinYear(all, "runA", 125);
all = L.pinEvent(all, "runA", { id: "t83-aid-3", t: 83, type: "aid" });
all = L.pinYear(all, "runB", 1);
ok("L1 按 run 隔离", all.runA.years.join() === "83,125" && all.runB.years.join() === "1" && !all.runB.events.length);
const rec = { events: [{ id: "t83-aid-3", type: "aid", text: "援助", source: "log" }] };
const payload = L.exportRecord({ run_id: "runA", engine: "exp06", engine_sha256: "abc", seed: 1, years: 150, sigma_m: 0, move_mort_m: 0, share_m: 0, aid_m: 0, recip_m: 1000, arm: "memory" }, 83, rec, { summary: "第83年有援助", selEvent: "t83-aid-3" });
ok("L2 白名单含版本参数年份来源", payload.run_id === "runA" && payload.year === 83 && payload.engine_sha256 === "abc" && payload.events[0].id === "t83-aid-3");
ok("L3 不含令牌与私人路径", !L.hasForbidden(payload) && payload.token == null);
ok("L4 禁止字段检测", L.hasForbidden({ token: "x", path: "/Users/ecool/secret" }));
const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
