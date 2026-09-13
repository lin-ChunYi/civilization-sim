#!/usr/bin/env node
/** game-v2：人物化群体代表与事件动作纯函数。不编路径、不把分裂放上地图。 */
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const motionCode = readFileSync(join(here, "motion.js"), "utf8");
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
vm.runInContext(motionCode, ctx);
vm.runInContext(code, ctx);
const U = ctx.window.UnitArt;
const M = ctx.window.Motion;
const D = ctx.window.DirectorLogic;
const out = [];
const ok = (name, cond, detail) => out.push((cond ? "PASS" : "FAIL") + " " + name + (detail ? " :: " + detail : ""));

ok("U0 UnitArt loaded", !!U && typeof U.markup === "function" && typeof U.actionPlan === "function");

const idA = "10431967184297706310";
const idB = "907731079216851761";
const palA1 = U.palette(idA);
const palA2 = U.palette(idA);
const palB = U.palette(idB);
ok("U1 palette stable for same id", palA1.cloth === palA2.cloth && palA1.sash === palA2.sash);
ok("U2 palette differs across bands", palA1.cloth !== palB.cloth || palA1.sash !== palB.sash);
ok("U3 scale grows with size but stays bounded",
  U.scale(1) < U.scale(80) && U.scale(1) >= 1.05 && U.scale(400) <= 1.58);

const mk = U.markup({ id: idA, name: "群体-ABC123", size: 20, cell: 10 }, 100, 80, { selected: true, pose: "select" });
ok("U4 markup is a group representative not a lone circle token",
  /data-unit="group-rep"/.test(mk) && /class="band unit selected"/.test(mk) && /unit-tunic/.test(mk)
  && /unit-head/.test(mk) && /群体代表/.test(mk));
ok("U5 selected ring and data-band preserved for clicks",
  /data-band="10431967184297706310"/.test(mk) && /unit-ring/.test(mk) && /unit-hit/.test(mk)
  && /data-art="sprite"/.test(mk));
ok("U6 name is escaped", !mk.includes("<script>") && U.markup({ id: "1", name: "<x>", size: 1, cell: 0 }, 0, 0).includes("&lt;x&gt;"));

const mig = U.actionPlan({ type: "migrate", from: 18, to: 10, band: idA }, D.eventFocus({ type: "migrate", from: 18, to: 10, band: idA }));
ok("U7 migrate is endpoint-only", mig.kind === "migrate" && mig.animate && mig.path === "endpoints-only"
  && mig.from === 18 && mig.to === 10 && U.midCells(18, 10).length === 0, JSON.stringify(mig));
const a = [0, 0], b = [10, 20];
const mid = U.lerp(a, b, 0.5);
ok("U8 lerp stays on the endpoint segment", mid[0] === 5 && mid[1] === 10);
ok("U9 lerp clamps", U.lerp(a, b, -1)[0] === 0 && U.lerp(a, b, 2)[0] === 10);

const share = U.actionPlan({ type: "share", cell: 0, donor: idA, receiver: idB });
ok("U10 share anchors event cell not year-end", share.kind === "share" && share.cell === 0 && share.path === "none" && share.locate, JSON.stringify(share));
const aid = U.actionPlan({ type: "aid", cell: 1, donor: idA, receiver: idB, repay: true });
ok("U11 repay stays aid-at-cell", aid.kind === "aid" && aid.repay === true && aid.cell === 1);

const split = U.actionPlan({ type: "split", parent: idA, band: idB });
ok("U12 split does not invent a map cell", split.locate === false && split.animate === false && split.cells.length === 0, JSON.stringify(split));
const extinct = U.actionPlan({ type: "extinct", band: idA });
ok("U13 extinct does not invent a map cell", extinct.locate === false && extinct.cells.length === 0);
const shareMiss = U.actionPlan({ type: "share", donor: idA, receiver: idB });
ok("U14 share without cell is unlocated", shareMiss.locate === false && shareMiss.animate === false);

const slot0 = U.slot(3, 0, 100, 50);
const slot2 = U.slot(3, 2, 100, 50);
ok("U15 same-cell representatives are offset not stacked", slot0[0] < 100 && slot2[0] > 100);
ok("U16 party count follows group size not individuals",
  U.partyCount(10) === 1 && U.partyCount(20) === 2 && U.partyCount(40) === 3);
const mk2 = U.markup({ id: idA, name: "群体-ABC123", size: 20, cell: 10 }, 100, 80, { selected: true });
ok("U17 twenty-person group keeps party=2 camp as one sprite representative",
  /data-party="2"/.test(mk2) && /unit-camp/.test(mk2) && /data-art="sprite"/.test(mk2)
  && /char-/.test(mk2) && /unit-prop-art/.test(mk2) && !/unit-companion/.test(mk2));
ok("U18 migrate stages stay on the endpoint segment",
  U.migrateStage(0) === "leave" && U.migrateStage(0.5) === "travel" && U.migrateStage(1) === "arrive");
const pal = U.palette(idA);
const f0 = U.figureMarkup(pal, "idle", 0, 0, 0, 1, true);
const f1 = U.figureMarkup(pal, "idle", 1, 0, 0, 1, true);
const f2 = U.figureMarkup(pal, "idle", 2, 0, 0, 1, true);
const f3 = U.figureMarkup(pal, "idle", 3, 0, 0, 1, true);
ok("U19 six silhouettes stay distinct; walk uses layered rig not a body swap",
  U.silhouetteName(0) === "staff" && U.silhouetteName(1) === "scout"
  && U.silhouetteName(2) === "gather" && U.silhouetteName(3) === "stocky"
  && U.silhouetteName(4) === "cloak" && U.silhouetteName(5) === "elder"
  && /\/static\/assets\/sprites\/char-/.test(mk)
  && /motion-rig/.test(U.markup({ id: idA, name: "n", size: 8, cell: 1 }, 0, 0, { pose: "walk" }))
  && /data-art="rig"/.test(U.markup({ id: idA, name: "n", size: 8, cell: 1 }, 0, 0, { pose: "walk" }))
  && !/face-ne\.png/.test(U.markup({ id: idA, name: "n", size: 8, cell: 1 }, 0, 0, { pose: "walk", face: "ne" }))
  && f0 !== f1 && f1 !== f2 && f2 !== f3);
let gatherId = null;
for (let i = 0; i < 4000 && !gatherId; i++) {
  if (U.silhouetteName(U.variant(String(i))) === "gather") gatherId = String(i);
}
ok("U19b gather select/give use state sprites of the same role",
  gatherId
  && /state-wave/.test(U.poseHref(gatherId, "select"))
  && /state-give/.test(U.poseHref(gatherId, "give"))
  && /char-gather/.test(U.poseHref(gatherId, "idle")));
const palGap = [idA, idB, "1", "2", "3", "99"].every((id) => {
  const p = U.palette(id);
  return U.luma(p.skin) - U.luma(p.cloth) >= 70;
});
ok("U20 skin is lighter than cloth for camp contrast", palGap && /port-/.test(U.portraitHref(idA)));
ok("U21 eight facings map from endpoint delta",
  U.faceName(10, 0) === "e" && U.faceName(-10, 0) === "w"
  && U.faceName(0, 10) === "s" && U.faceName(0, -10) === "n"
  && /face-e/.test(U.faceHref("e")) && /face-nw/.test(U.faceHref("nw")));
const mkFace = U.markup({ id: idA, name: "n", size: 8, cell: 1 }, 0, 0, { pose: "walk", face: "ne" });
ok("U22 migrate walker uses 8-dir layered gait of the same variant",
  /data-dir="ne"/.test(mkFace) && /motion-rig/.test(mkFace)
  && /data-skin="/.test(mkFace) && /m-leg-l/.test(mkFace)
  && !/face-ne\.png/.test(mkFace)
  && !!M && M.samplePose({ skin: "staff", action: "walk", dir: "e", phase: 0 }).skin === "staff");

const nf = out.filter((l) => l.indexOf("FAIL") === 0).length;
out.push("SUMMARY pass=" + out.filter((l) => l.indexOf("PASS") === 0).length + " fail=" + nf);
process.stdout.write(out.join("\n") + "\n");
process.exit(nf ? 1 : 0);
