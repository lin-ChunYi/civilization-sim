#!/usr/bin/env node
/** G_WATCH_PLAY_01 unit tests: pose, identity, narration. */
import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
function load(name) {
  const src = readFileSync(join(here, name), "utf8");
  const ctx = { console, window: {}, globalThis: {}, document: undefined };
  ctx.window = ctx;
  ctx.globalThis = ctx;
  runInContext(src, createContext(ctx));
  return ctx;
}
const motion = load("motion.js");
const scene = load("anime-scene.js");
const watch = load("watch-player.js");
const M = motion.Motion;
const A = scene.AnimeScene;
const L = watch.WatchLogic;
const out = [];
const ok = (name, cond, detail) => {
  out.push({ name, pass: !!cond, detail: detail == null ? "" : String(detail) });
  process.stdout.write((cond ? "PASS " : "FAIL ") + name + (detail ? " :: " + detail : "") + "\n");
};

ok("L0 modules", !!(M && A && L && A.applyPose && M.tillAt && M.harvestAt));

const idle = M.samplePose({ action: "idle", phase: 0, id: "1" });
const till0 = M.samplePose({ action: "till", phase: 0, id: "1" });
ok("L1 till phase 0 matches idle joints",
  till0.joints.lThigh === idle.joints.lThigh && till0.joints.rArm === idle.joints.rArm
  && till0.joints.torso === idle.joints.torso, JSON.stringify(till0.joints));
const har0 = M.samplePose({ action: "harvest", phase: 0, id: "1" });
ok("L1b harvest phase 0 matches idle", har0.joints.rArm === idle.joints.rArm);

const tillM = M.samplePose({ action: "till", phase: 0.5, id: "1" });
ok("L2 till mid is not give-substitute",
  Math.abs(tillM.joints.torso - idle.joints.torso) > 8
  && tillM.action === "till");
const giveM = M.samplePose({ action: "give", phase: 0.5, id: "1" });
ok("L2b till mid differs from give mid",
  Math.abs(tillM.joints.torso - giveM.joints.torso) > 5
  || Math.abs(tillM.joints.rArm - giveM.joints.rArm) > 10);

let limb = 0;
let prev = M.samplePose({ action: "till", phase: 0, id: "x" });
for (let i = 1; i < 8; i++) {
  const p = M.samplePose({ action: "till", phase: i / 8, id: "x" });
  if (Math.abs(p.joints.rArm - prev.joints.rArm) > 4
    || Math.abs(p.joints.torso - prev.joints.torso) > 2
    || Math.abs(p.joints.lThigh - prev.joints.lThigh) > 2) limb += 1;
  prev = p;
}
ok("L3 eight till samples change limbs", limb >= 4, "changes=" + limb);
limb = 0;
prev = M.samplePose({ action: "harvest", phase: 0, id: "x" });
for (let i = 1; i < 8; i++) {
  const p = M.samplePose({ action: "harvest", phase: i / 8, id: "x" });
  if (Math.abs(p.joints.rArm - prev.joints.rArm) > 4
    || Math.abs(p.joints.torso - prev.joints.torso) > 2) limb += 1;
  prev = p;
}
ok("L3b eight harvest samples change limbs", limb >= 4, "changes=" + limb);

const fake = () => {
  const kids = {};
  return {
    setAttribute(k, v) { this[k] = v; },
    getAttribute(k) { return this[k]; },
    querySelector(sel) {
      if (!kids[sel]) kids[sel] = { setAttribute(k, v) { this[k] = v; this.transform = v; }, transform: "scale(9,9)" };
      return kids[sel];
    },
    kids,
  };
};
const el = fake();
el.setAttribute("transform", "scale(2.15,2.15)");
A.applyPose(el, tillM);
ok("L4 applyPose does not rewrite root scale", el.transform === "scale(2.15,2.15)");
ok("L4b shin uses anime origin 12 not 8",
  /translate\(0,12\)/.test(el.kids[".m-shin-l"].transform), el.kids[".m-shin-l"].transform);
ok("L4c forearm uses ±10,15 not 0,7",
  /translate\(-10,15\)/.test(el.kids[".m-fore-l"].transform)
  && /translate\(10,15\)/.test(el.kids[".m-fore-r"].transform),
  el.kids[".m-fore-l"].transform + " " + el.kids[".m-fore-r"].transform);

const research = { kids: {}, setAttribute() {}, querySelector(sel) {
  if (!this.kids[sel]) this.kids[sel] = { setAttribute(k, v) { this.transform = v; } };
  return this.kids[sel];
} };
M.applyPose(research, tillM);
ok("L5 Motion.applyPose still uses research 8/7 origins",
  /translate\(0,8\)/.test(research.kids[".m-shin-l"].transform)
  && /translate\(0,7\)/.test(research.kids[".m-fore-l"].transform));

ok("L6 gap 2→218 is 216 years not continuous days",
  L.gapText(2, 218).indexOf("相隔 216 年") >= 0
  && L.gapText(2, 218).indexOf("群体代表") >= 0, L.gapText(2, 218));
ok("L6b adjacent years have no gap banner", L.gapText(1, 2) === "");

const alias = (id) => id === "7567856178022945294" ? "云杉2" : "青禾2";
const harvestCh = {
  kind: "harvest", title: "第一次收成", year: 2, actor_ids: ["7567856178022945294"],
  facts: { harvested_kcal: { value: 3849598, unit: "kcal", source: "events[].kcal" },
    person_years: { value: 5.273, unit: "人年口粮", source: "events[].person_years" },
    pop_year_end: { value: 120, unit: "人", basis: "year_end", note: "不是这件事直接造成的变化" } },
};
const said = L.narrate(harvestCh, alias);
ok("L7 harvest copy uses alias and person-years, not invented motive",
  /云杉2/.test(said.copy) && /5\.3|5 人一年/.test(said.copy)
  && !said.banned && !/感恩|饿死|明年一定/.test(said.copy), said.copy);
ok("L7b main scene has no raw fact keys", !L.rawInMain(said.copy) && !L.rawInMain(said.facts) && said.facts === "", said.copy + " || " + said.facts);
ok("L7c exact harvest facts live in Source", /harvested_kcal = 3849598/.test(said.source) && /person_years/.test(said.source), said.source.slice(0, 180));

const clearCh = {
  kind: "clearing", title: "第一次开垦", year: 1, actor_ids: ["7567856178022945294"],
  facts: {
    built_m: { value: 5000, unit: "field_m（1000 = 1 个耕作规模单位）", source: "events[].amount_m" },
    field_before_m: { value: 0, unit: "field_m", source: "events[].field_before_m" },
    field_after_m: { value: 5000, unit: "field_m", source: "events[].field_after_m" },
    labour_m: { value: 5000, unit: "劳动刻度（人数 × 1000）", source: "events[].labour_m" },
    harvested_kcal_here_this_year: { value: 0, unit: "kcal", source: "模型规则" },
  },
};
const cleared = L.narrate(clearCh, alias);
ok("L7d clearing copy is ordinary wording plus readable units",
  /云杉2/.test(cleared.copy) && /5 个耕作规模单位/.test(cleared.copy)
  && /以后年份才可能有收成/.test(cleared.copy)
  && !L.rawInMain(cleared.copy) && !L.rawInMain(cleared.facts) && cleared.facts === "",
  cleared.copy);
ok("L7e clearing Source keeps exact built_m/labour_m",
  /built_m = 5000/.test(cleared.source) && /labour_m = 5000/.test(cleared.source)
  && /harvested_kcal_here_this_year = 0/.test(cleared.source), cleared.source.slice(0, 240));

const aidCh = { kind: "aid", title: "第一次援助", actor_ids: ["a", "b"] };
const aidSaid = L.narrate(aidCh, (id) => id === "a" ? "青禾2" : "芦花");
ok("L8 aid names donor then receiver", /青禾2.*芦花/.test(aidSaid.copy), aidSaid.copy);
ok("L8b repay does not claim priority rule change",
  /以前也帮助过对方/.test(L.narrate({ kind: "repay", actor_ids: ["a", "b"] }, (id) => id).copy));

ok("L9 missing labels distinguish reasons",
  L.missingLabel("engine_lacks_mechanism").indexOf("没有这回事") >= 0
  && L.missingLabel("param_zero").indexOf("参数设成了 0") >= 0
  && L.missingLabel("not_observed").indexOf("没有发生过") >= 0);

A.Identity.reset("root-plan");
A.Identity.ingestPlan("root-plan", {
  schema: "watch-plan-1",
  source: { identity_complete_through: 300 },
  identities: [
    { id: "100", first_year: 0, parent_id: null },
    { id: "20", first_year: 0, parent_id: null },
    { id: "3", first_year: 5, parent_id: "100" },
  ],
});
const order = A.Identity.table("root-plan").order;
ok("L10 identity order is first_year then decimal-id length, not JS Number",
  order[0] === "20" && order[1] === "100" && order[2] === "3", JSON.stringify(order));
ok("L10b ready watermark from plan", A.Identity.ready["root-plan"].through === 300);
ok("L10c Number() would have reordered 20 vs 100 if used as numbers — we did not",
  Number("20") < Number("100") && order.indexOf("20") < order.indexOf("100"));

ok("L11 chapter actions", L.chapterAction("clearing") === "till" && L.chapterAction("harvest") === "harvest");
ok("L12 pin path keeps through", L.pinPath("preset-anime-farm250", 300).indexOf("through=300") >= 0);

const failed = out.filter((x) => !x.pass);
process.stdout.write("watch-logic passed=" + (out.length - failed.length) + " failed=" + failed.length + "\n");
process.exit(failed.length ? 1 : 0);
