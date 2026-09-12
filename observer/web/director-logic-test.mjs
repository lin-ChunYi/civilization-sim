#!/usr/bin/env node
/** G03 DirectorLogic 纯函数自检。不启动服务、不改世界。 */
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const code = readFileSync(join(here, "app.js"), "utf8");
const location = { hash: "", search: "", href: "http://127.0.0.1/static/index.html" };
const document = {
  getElementById() { return null; },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  addEventListener() {},
};
const windowObj = { __OBS_MANUAL_BOOT__: true, matchMedia: () => ({ matches: false }) };
const ctx = {
  window: windowObj,
  document,
  location,
  history: { replaceState() {} },
  sessionStorage: { getItem() { return ""; }, setItem() {} },
  performance: { now: Date.now },
  console,
  setTimeout,
  clearTimeout,
  requestAnimationFrame: (fn) => setTimeout(fn, 16),
  cancelAnimationFrame: clearTimeout,
};
ctx.globalThis = ctx;
windowObj.__OBS_MANUAL_BOOT__ = true;
vm.createContext(ctx);
vm.runInContext(code, ctx);
const D = ctx.window.DirectorLogic;
const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

ok("D0 已加载", !!D);
const years = D.eventYearsFromSeries([
  { t: 0, events: 0, year: { births_cum: 957 } },
  { t: 48, events: 2 },
  { t: 49, events: 0, agg: { pop: 176 } },
  { t: 72, events: 1 },
]);
ok("D1 跳年只用 series.events", years.join() === "48,72", JSON.stringify(years));
ok("D2 下一事件年", D.nextEventYear(years, 48) === 72);
ok("D3 前一事件年", D.prevEventYear(years, 72) === 48);
ok("D4 没有更早事件年", D.prevEventYear(years, 48) == null);
const none = D.eventModeStatus({
  series: [{ t: 0, events: 0 }], yearsRecorded: 0, runStatus: "done", rec: { events: [] }, t: 0,
});
ok("D5 无事件说明", none.kind === "none" && /不是事件/.test(none.text));
const computing = D.eventModeStatus({
  series: [], yearsRecorded: 0, runStatus: "running", rec: null, t: 0,
});
ok("D6 计算中", computing.kind === "computing");
const missing = D.eventModeStatus({
  series: [{ t: 10, events: 2 }], yearsRecorded: 10, runStatus: "done", rec: null, t: 10,
});
ok("D7 缺失", missing.kind === "missing");
const share = D.eventFocus({ type: "share", id: "t125-share-1", cell: 0, donor: "A", receiver: "B" });
ok("D8 share 锚 e.cell=0", share.locate && share.cells[0] === 0);
const aid = D.eventFocus({ type: "aid", cell: 2, repay: true, donor: "A", receiver: "B" });
ok("D9 回助仍锚事件格", aid.locate && aid.cells[0] === 2 && aid.repay);
const mig = D.eventFocus({ type: "migrate", from: 4, to: 7, band: "X" });
ok("D10 迁移端点", mig.cells.join() === "4,7" && /路线未记录/.test(mig.note));
const split = D.eventFocus({ type: "split", parent: "P", band: "C" });
ok("D11 分裂不定位", !split.locate && split.cells.length === 0);
const extinct = D.eventFocus({ type: "extinct", band: "G" });
ok("D12 消失不定位", !extinct.locate);
ok("D13 raw tick 不展示", D.displayYearFromMemory({ last_year: 82 }).year == null);
ok("D14 last_year_display", D.displayYearFromMemory({ last_year: 82, last_year_display: 83 }).year === 83);
ok("D15 prior_events", D.displayYearFromBasis({ remembered_last_year: 82, prior_events: ["t83-aid-3"] }).year === 83);
ok("D16 顺序声明", /不保证年内机制先后/.test(D.orderNote));
ok("D17 事件 id", D.eventKey({ id: "t125-share-1" }, 125, 0) === "t125-share-1");

const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
