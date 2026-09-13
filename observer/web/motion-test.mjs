#!/usr/bin/env node
/** G_MOTION_01 pure functions: gait, identity, aggregation conservation. */
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const code = readFileSync(join(here, "motion.js"), "utf8");
const ctx = { window: {}, console, module: { exports: {} } };
ctx.globalThis = ctx;
ctx.window = ctx;
vm.createContext(ctx);
vm.runInContext(code, ctx);
const M = ctx.Motion;
const fixture = JSON.parse(readFileSync(join(here, "motion-dense-fixture.json"), "utf8"));
const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

ok("M0 Motion loaded", !!M && typeof M.samplePose === "function");

const a = M.samplePose({ skin: "staff", action: "walk", dir: "e", phase: 0.25, id: "1" });
const b = M.samplePose({ skin: "staff", action: "walk", dir: "e", phase: 0.25, id: "1" });
ok("M1 same inputs same pose",
  a.joints.lThigh === b.joints.lThigh && a.lFoot.y === b.lFoot.y && a.skin === "staff");

const skins = M.SKINS.map((s) => M.samplePose({ skin: s, action: "walk", dir: "e", phase: 0, id: s }).prop);
ok("M2 six skins keep distinct props", new Set(skins).size >= 4 && skins.length === 6);

const p0 = M.samplePose({ skin: "scout", action: "walk", dir: "e", phase: 0 });
const p1 = M.samplePose({ skin: "scout", action: "walk", dir: "e", phase: 1 });
ok("M3 walk phase 0 equals phase 1 (closed loop)",
  Math.abs(p0.joints.lThigh - p1.joints.lThigh) < 1e-6
  && Math.abs(p0.lFoot.y - p1.lFoot.y) < 1e-6);

const feet = [];
for (let i = 0; i < 8; i++) {
  feet.push(M.samplePose({ skin: "staff", action: "walk", dir: "e", phase: i / 8 }));
}
let limbChange = 0;
for (let i = 1; i < 8; i++) {
  if (Math.abs(feet[i].lFoot.y - feet[i - 1].lFoot.y) > 0.15
    || Math.abs(feet[i].joints.lThigh - feet[i - 1].joints.lThigh) > 1
    || Math.abs(feet[i].joints.rArm - feet[i - 1].joints.rArm) > 1) limbChange += 1;
}
ok("M4 eight samples at fixed root show limb change", limbChange >= 6, "changes=" + limbChange);

const west = M.samplePose({ skin: "staff", action: "walk", dir: "w", phase: 0.2 });
const east = M.samplePose({ skin: "staff", action: "walk", dir: "e", phase: 0.2 });
ok("M5 west is a mirror of east, same skin",
  west.flip === -1 && east.flip === 1 && west.skin === east.skin && west.joints.lThigh === east.joints.lThigh);

ok("M6 MANIFEST does not claim unique painted frames",
  /mirror/i.test(M.MANIFEST.shared) && /squash/i.test(M.MANIFEST.shared));

const give0 = M.samplePose({ skin: "gather", action: "give", dir: "e", phase: 0 });
const giveM = M.samplePose({ skin: "gather", action: "give", dir: "e", phase: 0.4 });
const give1 = M.samplePose({ skin: "gather", action: "give", dir: "e", phase: 1 });
ok("M7 aid give returns to idle at phase 1 and mid pose differs",
  Math.abs(give0.joints.rArm - give1.joints.rArm) < 1e-6
  && Math.abs(giveM.joints.rArm - give0.joints.rArm) > 10);

const talkM = M.samplePose({ skin: "cloak", action: "talk", dir: "e", phase: 0.4 });
ok("M8 share talk is a distinct short gesture",
  Math.abs(talkM.joints.rArm - give0.joints.rArm) > 5);

const agg = M.aggregate(fixture.events, { runId: fixture.runId, year: fixture.year, playCap: 4 });
const idSet = agg.ids.slice().sort().join(",");
const srcSet = fixture.events.map((e) => e.id).slice().sort().join(",");
const kcalSrc = fixture.events.filter((e) => e.type === "aid").reduce((n, e) => n + e.kcal, 0);
const migGroups = agg.groups.filter((g) => g.kind === "migrate");
ok("M9 dense fixture conserves ids and kcal and does not merge migrate endpoints",
  idSet === srcSet && agg.kcal === kcalSrc && agg.totalEvents === fixture.events.length
  && migGroups.length === 2 && migGroups[0].from !== migGroups[1].from
  && /本年共12条/.test(agg.summary) && agg.shownCount === 4,
  JSON.stringify({ kcal: agg.kcal, groups: agg.groupCount, shown: agg.shownCount, summary: agg.summary }));

ok("M10 aid groups split normal/recip/repay",
  agg.groups.filter((g) => g.kind === "aid").length >= 3);

const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
