/* OBS-01 motion: inspectable layered rig. No paid APIs.
   Walk is 8 keyframes on one skeleton. Eight directions share that gait:
   W/SW/NW are mirrors of E/SE/NE; N/S are foreshortened copies. Not unique drawings.
   Actors keep UnitArt variant/skin/palette/prop. Hooded face-*.png is not used as a body swap.
*/
(function (root) {
  "use strict";

  const SKINS = ["staff", "scout", "gather", "stocky", "cloak", "elder"];
  const DIRS = ["e", "se", "s", "sw", "w", "nw", "n", "ne"];
  const DIR_XFORM = {
    e: { flip: 1, squash: 1, note: "profile; base gait" },
    se: { flip: 1, squash: 0.82, note: "3/4 from E, foreshortened" },
    s: { flip: 1, squash: 0.48, note: "front; same gait, stride squashed" },
    sw: { flip: -1, squash: 0.82, note: "mirror of SE" },
    w: { flip: -1, squash: 1, note: "mirror of E" },
    nw: { flip: -1, squash: 0.82, note: "mirror of NE" },
    n: { flip: 1, squash: 0.42, note: "back; same gait, stride squashed" },
    ne: { flip: 1, squash: 0.82, note: "3/4 back from E, foreshortened" },
  };
  const SKIN_RIG = {
    staff: { w: 1.00, h: 1.08, prop: "staff" },
    scout: { w: 0.90, h: 1.02, prop: "pack" },
    gather: { w: 1.00, h: 1.00, prop: "basket" },
    stocky: { w: 1.18, h: 0.90, prop: "none" },
    cloak: { w: 1.06, h: 1.04, prop: "hood" },
    elder: { w: 0.96, h: 0.98, prop: "staff" },
  };
  const PLAY_CAP = 4;
  const WALK = [
    { hipY: 0.25, lThigh: 28, rThigh: -22, lShin: -8, rShin: 18, lArm: -24, rArm: 26, lFore: -6, rFore: 8, torso: 2 },
    { hipY: -1.15, lThigh: 18, rThigh: -8, lShin: 6, rShin: 22, lArm: -12, rArm: 14, lFore: -2, rFore: 4, torso: 1 },
    { hipY: 0.55, lThigh: 4, rThigh: 12, lShin: 10, rShin: 4, lArm: 6, rArm: -6, lFore: 2, rFore: -2, torso: 0 },
    { hipY: 1.45, lThigh: -10, rThigh: 30, lShin: 16, rShin: -12, lArm: 18, rArm: -20, lFore: 8, rFore: -6, torso: -2 },
    { hipY: 0.25, lThigh: -22, rThigh: 28, lShin: 18, rShin: -8, lArm: 26, rArm: -24, lFore: 8, rFore: -6, torso: -2 },
    { hipY: -1.15, lThigh: -8, rThigh: 18, lShin: 22, rShin: 6, lArm: 14, rArm: -12, lFore: 4, rFore: -2, torso: -1 },
    { hipY: 0.55, lThigh: 12, rThigh: 4, lShin: 4, rShin: 10, lArm: -6, rArm: 6, lFore: -2, rFore: 2, torso: 0 },
    { hipY: 1.45, lThigh: 30, rThigh: -10, lShin: -12, rShin: 16, lArm: -20, rArm: 18, lFore: -6, rFore: 8, torso: 2 },
  ];
  const IDLE = { hipY: 0, lThigh: 4, rThigh: -3, lShin: 6, rShin: 8, lArm: 8, rArm: -6, lFore: 4, rFore: -2, torso: 0 };

  function clamp01(u) {
    const n = Number(u);
    if (!Number.isFinite(n)) return 0;
    if (n < 0) return 0;
    if (n > 1) return 1;
    return n;
  }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function mixPose(a, b, t) {
    const o = {};
    Object.keys(a).forEach((k) => { o[k] = lerp(a[k], b[k], t); });
    return o;
  }
  function wrapPhase(p) {
    const u = clamp01(p);
    return u >= 1 ? 0 : u;
  }
  function gaitAt(phase) {
    const u = wrapPhase(phase);
    const x = u * 8;
    const i = Math.floor(x) % 8;
    const t = x - Math.floor(x);
    const a = WALK[i];
    const b = WALK[(i + 1) % 8];
    return mixPose(a, b, t);
  }
  function aidDonorAt(phase) {
    const u = clamp01(phase);
    const idle = IDLE;
    const give = { hipY: 0.2, lThigh: 6, rThigh: -4, lShin: 8, rShin: 6, lArm: -8, rArm: -70, lFore: 4, rFore: -20, torso: 6 };
    const hold = { hipY: 0.1, lThigh: 5, rThigh: -3, lShin: 8, rShin: 6, lArm: -4, rArm: -78, lFore: 2, rFore: -8, torso: 8 };
    if (u < 0.25) return mixPose(idle, give, u / 0.25);
    if (u < 0.5) return mixPose(give, hold, (u - 0.25) / 0.25);
    if (u < 0.75) return mixPose(hold, give, (u - 0.5) / 0.25);
    return mixPose(give, idle, (u - 0.75) / 0.25);
  }
  function aidRecvAt(phase) {
    const u = clamp01(phase);
    const idle = IDLE;
    const open = { hipY: 0, lThigh: 3, rThigh: -2, lShin: 7, rShin: 7, lArm: -40, rArm: -42, lFore: -12, rFore: -12, torso: -4 };
    const take = { hipY: 0.2, lThigh: 4, rThigh: -3, lShin: 7, rShin: 7, lArm: -55, rArm: -58, lFore: -6, rFore: -6, torso: -2 };
    if (u < 0.25) return mixPose(idle, open, u / 0.25);
    if (u < 0.5) return mixPose(open, take, (u - 0.25) / 0.25);
    if (u < 0.75) return mixPose(take, open, (u - 0.5) / 0.25);
    return mixPose(open, idle, (u - 0.75) / 0.25);
  }
  function talkAt(phase) {
    const u = clamp01(phase);
    const idle = IDLE;
    const talk = { hipY: 0, lThigh: 3, rThigh: -2, lShin: 6, rShin: 7, lArm: -8, rArm: -48, lFore: 4, rFore: -18, torso: 5 };
    if (u < 0.3) return mixPose(idle, talk, u / 0.3);
    if (u < 0.7) return talk;
    return mixPose(talk, idle, (u - 0.7) / 0.3);
  }
  function listenAt(phase) {
    const u = clamp01(phase);
    const idle = IDLE;
    const lean = { hipY: 0, lThigh: 5, rThigh: -2, lShin: 6, rShin: 7, lArm: 10, rArm: 6, lFore: 4, rFore: 2, torso: -8 };
    if (u < 0.3) return mixPose(idle, lean, u / 0.3);
    if (u < 0.7) return lean;
    return mixPose(lean, idle, (u - 0.7) / 0.3);
  }
  function tillAt(phase) {
    const u = clamp01(phase);
    const idle = IDLE;
    const raise = { hipY: 0.2, lThigh: 6, rThigh: -4, lShin: 8, rShin: 6, lArm: 10, rArm: -82, lFore: 4, rFore: -18, torso: -6 };
    const bend = { hipY: 2.4, lThigh: 16, rThigh: 8, lShin: 10, rShin: 12, lArm: 14, rArm: -38, lFore: 8, rFore: 22, torso: 18 };
    const plant = { hipY: 3.0, lThigh: 18, rThigh: 10, lShin: 12, rShin: 14, lArm: 16, rArm: 8, lFore: 10, rFore: 28, torso: 22 };
    if (u <= 0) return Object.assign({}, idle);
    if (u < 0.22) return mixPose(idle, raise, u / 0.22);
    if (u < 0.45) return mixPose(raise, bend, (u - 0.22) / 0.23);
    if (u < 0.7) return mixPose(bend, plant, (u - 0.45) / 0.25);
    return mixPose(plant, idle, (u - 0.7) / 0.3);
  }
  function harvestAt(phase) {
    const u = clamp01(phase);
    const idle = IDLE;
    const reach = { hipY: 1.2, lThigh: 10, rThigh: 4, lShin: 8, rShin: 8, lArm: -18, rArm: -58, lFore: -8, rFore: -12, torso: 12 };
    const pick = { hipY: 2.2, lThigh: 14, rThigh: 6, lShin: 10, rShin: 10, lArm: -22, rArm: -36, lFore: -6, rFore: 16, torso: 16 };
    const basket = { hipY: 0.6, lThigh: 6, rThigh: -2, lShin: 8, rShin: 6, lArm: -48, rArm: 36, lFore: -16, rFore: -28, torso: 4 };
    if (u <= 0) return Object.assign({}, idle);
    if (u < 0.25) return mixPose(idle, reach, u / 0.25);
    if (u < 0.5) return mixPose(reach, pick, (u - 0.25) / 0.25);
    if (u < 0.75) return mixPose(pick, basket, (u - 0.5) / 0.25);
    return mixPose(basket, idle, (u - 0.75) / 0.25);
  }
  function foot(thigh, shin, squash) {
    const t = thigh * Math.PI / 180;
    const s = (thigh + shin) * Math.PI / 180;
    const hip = 8, kn = 7;
    return {
      x: (Math.sin(t) * hip + Math.sin(s) * kn) * squash,
      y: Math.cos(t) * hip + Math.cos(s) * kn,
    };
  }
  function skinOf(id, explicit) {
    if (explicit && SKINS.indexOf(explicit) >= 0) return explicit;
    if (root.UnitArt && typeof root.UnitArt.variant === "function") {
      return SKINS[(root.UnitArt.variant(id) || 0) % 6];
    }
    let h = 0;
    const s = String(id == null ? "" : id);
    for (let i = 0; i < s.length; i++) h = (h * 33 + s.charCodeAt(i)) >>> 0;
    return SKINS[h % 6];
  }

  function samplePose(opts) {
    opts = opts || {};
    const skin = skinOf(opts.id, opts.skin);
    const action = opts.action || "idle";
    const dir = DIRS.indexOf(opts.dir) >= 0 ? opts.dir : "e";
    const role = opts.role || "solo";
    const phaseIn = Number(opts.phase);
    const phase = Number.isFinite(phaseIn) ? phaseIn : 0;
    const xform = DIR_XFORM[dir];
    let joints;
    if (action === "walk") joints = gaitAt(phase);
    else if (action === "give") joints = aidDonorAt(phase);
    else if (action === "receive") joints = aidRecvAt(phase);
    else if (action === "talk") joints = talkAt(phase);
    else if (action === "listen") joints = listenAt(phase);
    else if (action === "till" || action === "farm") joints = tillAt(phase);
    else if (action === "harvest") joints = harvestAt(phase);
    else joints = Object.assign({}, IDLE);
    const lFoot = foot(joints.lThigh, joints.lShin, xform.squash);
    const rFoot = foot(joints.rThigh, joints.rShin, xform.squash);
    const closed = action === "walk" ? wrapPhase(phase) : clamp01(phase);
    return {
      skin: skin, action: action, dir: dir, role: role, phase: closed,
      flip: xform.flip, squash: xform.squash, prop: SKIN_RIG[skin].prop,
      joints: joints, lFoot: lFoot, rFoot: rFoot,
      dirNote: xform.note,
    };
  }

  function rigMarkup(sample, pal) {
    pal = pal || { cloth: "#6a5340", skin: "#e2c7a4", hair: "#2a1810", sash: "#8a6a3a", accent: "#d4b06a" };
    const s = sample || samplePose({});
    const j = s.joints;
    const rig = SKIN_RIG[s.skin] || SKIN_RIG.staff;
    const w = 7.2 * rig.w;
    const hood = s.prop === "hood"
      ? `<path class="m-hood" d="M${(-w * 0.55).toFixed(1)},-11 C-2,-18 2,-18 ${(w * 0.55).toFixed(1)},-11 L2.2,-8 C1,-9.2 -1,-9.2 -2.2,-8Z" fill="${pal.sash}" opacity="0.92"/>`
      : "";
    const staff = s.prop === "staff"
      ? `<path class="m-prop m-staff" d="M10,-16 L11,14" stroke="${pal.accent}" stroke-width="1.5" stroke-linecap="round"/>`
      : "";
    const pack = s.prop === "pack"
      ? `<ellipse class="m-prop m-pack" cx="-8.6" cy="3.2" rx="3.1" ry="2.4" fill="${pal.sash}" stroke="${pal.accent}" stroke-width="0.6"/>`
      : "";
    const basket = s.prop === "basket"
      ? `<path class="m-prop m-basket" d="M-11,1 L-6,1 L-5.2,6 L-11.6,6Z" fill="${pal.sash}" stroke="${pal.accent}" stroke-width="0.6"/>`
      : "";
    const gift = s.action === "give"
      ? `<circle class="m-gift" cx="12" cy="-8" r="2.2" fill="${pal.accent}" opacity="0.9"/>`
      : "";
    return `<g class="motion-rig" data-art="rig" data-skin="${s.skin}" data-action="${s.action}" data-dir="${s.dir}" data-role="${s.role}" data-phase="${s.phase.toFixed(4)}" data-prop="${s.prop}" data-lfoot-y="${s.lFoot.y.toFixed(3)}" data-rfoot-y="${s.rFoot.y.toFixed(3)}" data-lthigh="${j.lThigh.toFixed(2)}" data-rthigh="${j.rThigh.toFixed(2)}" transform="scale(${(s.flip * rig.w).toFixed(3)},${rig.h.toFixed(3)})">
      <g class="m-hip" transform="translate(0,${j.hipY.toFixed(2)})">
        <g class="m-leg-l" transform="rotate(${j.lThigh.toFixed(2)})">
          <path class="m-thigh-l" d="M0,0 L0,8" stroke="${pal.hair}" stroke-width="2.3" stroke-linecap="round"/>
          <g class="m-shin-l" transform="translate(0,8) rotate(${j.lShin.toFixed(2)})">
            <path d="M0,0 L0,7" stroke="${pal.hair}" stroke-width="2.1" stroke-linecap="round"/>
            <ellipse class="m-foot-l" cx="1.2" cy="7.4" rx="2.6" ry="1.1" fill="${pal.hair}"/>
          </g>
        </g>
        <g class="m-leg-r" transform="rotate(${j.rThigh.toFixed(2)})">
          <path class="m-thigh-r" d="M0,0 L0,8" stroke="${pal.hair}" stroke-width="2.3" stroke-linecap="round"/>
          <g class="m-shin-r" transform="translate(0,8) rotate(${j.rShin.toFixed(2)})">
            <path d="M0,0 L0,7" stroke="${pal.hair}" stroke-width="2.1" stroke-linecap="round"/>
            <ellipse class="m-foot-r" cx="1.2" cy="7.4" rx="2.6" ry="1.1" fill="${pal.hair}"/>
          </g>
        </g>
        <g class="m-torso" transform="rotate(${j.torso.toFixed(2)})">
          <path class="m-tunic unit-tunic" d="M${(-w).toFixed(1)},-2 C${(-w - 0.4).toFixed(1)},6 ${(-w * 0.4).toFixed(1)},11 -2.4,11.4 L2.4,11.4 C${(w * 0.4).toFixed(1)},11 ${(w + 0.4).toFixed(1)},6 ${w.toFixed(1)},-2 C3.2,-4.2 -3.2,-4.2 ${(-w).toFixed(1)},-2Z" fill="${pal.cloth}" stroke="#2a1810" stroke-width="0.8"/>
          <path class="m-sash" d="M${(-w * 0.7).toFixed(1)},2.2 L${(w * 0.7).toFixed(1)},3.2 L${(w * 0.65).toFixed(1)},4.8 L${(-w * 0.75).toFixed(1)},3.6Z" fill="${pal.sash}"/>
          <g class="m-arm-l" transform="rotate(${j.lArm.toFixed(2)})">
            <path d="M-4.6,-0.4 L-4.6,7" stroke="${pal.skin}" stroke-width="1.8" stroke-linecap="round"/>
            <g class="m-fore-l" transform="translate(0,7) rotate(${j.lFore.toFixed(2)})">
              <path d="M-4.6,0 L-4.6,6" stroke="${pal.skin}" stroke-width="1.6" stroke-linecap="round"/>
            </g>
          </g>
          <g class="m-arm-r" transform="rotate(${j.rArm.toFixed(2)})">
            <path d="M4.6,-0.4 L4.6,7" stroke="${pal.skin}" stroke-width="1.8" stroke-linecap="round"/>
            <g class="m-fore-r" transform="translate(0,7) rotate(${j.rFore.toFixed(2)})">
              <path d="M4.6,0 L4.6,6" stroke="${pal.skin}" stroke-width="1.6" stroke-linecap="round"/>
              ${gift}
            </g>
          </g>
          <g class="m-head">
            <circle class="unit-head" cx="0" cy="-8.2" r="3.9" fill="${pal.skin}" stroke="${pal.hair}" stroke-width="0.7"/>
            <path class="m-hair" d="M-3.8,-8.6 C-3.2,-12.4 3.2,-12.4 3.8,-8.6 C1.6,-10 -1.6,-10 -3.8,-8.6Z" fill="${pal.hair}"/>
            ${hood}
          </g>
          ${staff}${pack}${basket}
        </g>
      </g>
    </g>`;
  }

  function applyPose(root, sample) {
    if (!root || !sample) return;
    const j = sample.joints;
    const rig = SKIN_RIG[sample.skin] || SKIN_RIG.staff;
    root.setAttribute("data-phase", sample.phase.toFixed(4));
    root.setAttribute("data-dir", sample.dir);
    root.setAttribute("data-action", sample.action);
    root.setAttribute("data-lfoot-y", sample.lFoot.y.toFixed(3));
    root.setAttribute("data-rfoot-y", sample.rFoot.y.toFixed(3));
    root.setAttribute("data-lthigh", j.lThigh.toFixed(2));
    root.setAttribute("data-rthigh", j.rThigh.toFixed(2));
    root.setAttribute("transform", "scale(" + (sample.flip * rig.w).toFixed(3) + "," + rig.h.toFixed(3) + ")");
    const set = (sel, tr) => { const n = root.querySelector(sel); if (n) n.setAttribute("transform", tr); };
    set(".m-hip", "translate(0," + j.hipY.toFixed(2) + ")");
    set(".m-leg-l", "rotate(" + j.lThigh.toFixed(2) + ")");
    set(".m-shin-l", "translate(0,8) rotate(" + j.lShin.toFixed(2) + ")");
    set(".m-leg-r", "rotate(" + j.rThigh.toFixed(2) + ")");
    set(".m-shin-r", "translate(0,8) rotate(" + j.rShin.toFixed(2) + ")");
    set(".m-torso", "rotate(" + j.torso.toFixed(2) + ")");
    set(".m-arm-l", "rotate(" + j.lArm.toFixed(2) + ")");
    set(".m-fore-l", "translate(0,7) rotate(" + j.lFore.toFixed(2) + ")");
    set(".m-arm-r", "rotate(" + j.rArm.toFixed(2) + ")");
    set(".m-fore-r", "translate(0,7) rotate(" + j.rFore.toFixed(2) + ")");
  }

  function aidMark(e) {
    if (!e) return "normal";
    if (e.repay) return "repay";
    if (e.phase === "recip" || e.phase === "priority") return "recip";
    return "normal";
  }
  function emptyGroup(kind, cell, mark, runId, year) {
    return {
      key: [runId, year, kind, cell, mark || ""].join("|"),
      kind: kind, cell: cell, mark: mark || "",
      ids: [], events: [], donors: [], receivers: [],
      kcal: 0, transfers: 0, shares: 0, animate: kind === "migrate" || kind === "aid" || kind === "share",
      from: null, to: null, band: null,
    };
  }
  function pushActor(list, id) {
    if (id == null || id === "") return;
    const s = String(id);
    if (list.indexOf(s) < 0) list.push(s);
  }
  function aggregate(events, opts) {
    opts = opts || {};
    const runId = opts.runId != null ? String(opts.runId) : "";
    const year = opts.year;
    const playCap = opts.playCap != null ? opts.playCap : PLAY_CAP;
    const list = events || [];
    const groups = [];
    const index = {};
    list.forEach((e, i) => {
      const ev = Object.assign({}, e, { _i: i });
      const type = ev.type || "other";
      if (type === "migrate") {
        const g = emptyGroup("migrate", null, "", runId, year);
        g.ids.push(String(ev.id || i));
        g.events.push(ev);
        g.from = ev.from; g.to = ev.to; g.band = ev.band || null;
        g.animate = ev.from != null && ev.to != null;
        groups.push(g);
        return;
      }
      if (type === "split" || type === "extinct") {
        const g = emptyGroup(type, null, "", runId, year);
        g.ids.push(String(ev.id || i));
        g.events.push(ev);
        g.animate = false;
        g.band = ev.band || ev.parent || null;
        groups.push(g);
        return;
      }
      const mark = type === "aid" ? aidMark(ev) : "";
      const cell = ev.cell != null && ev.cell !== "" ? String(ev.cell) : "none";
      const key = [runId, year, type, cell, mark].join("|");
      if (!index[key]) {
        const g = emptyGroup(type, cell === "none" ? null : +cell, mark, runId, year);
        g.animate = (type === "aid" || type === "share") && cell !== "none";
        index[key] = g;
        groups.push(g);
      }
      const g = index[key];
      g.ids.push(String(ev.id || i));
      g.events.push(ev);
      pushActor(g.donors, ev.donor);
      pushActor(g.receivers, ev.receiver);
      if (type === "aid") {
        g.transfers += 1;
        g.kcal += Number(ev.kcal) || 0;
      }
      if (type === "share") g.shares += 1;
    });
    const playable = groups.filter((g) => g.animate);
    const shown = playable.slice(0, playCap);
    const kcal = groups.reduce((n, g) => n + g.kcal, 0);
    const ids = [];
    groups.forEach((g) => { g.ids.forEach((id) => ids.push(id)); });
    return {
      totalEvents: list.length,
      groupCount: groups.length,
      shownCount: shown.length,
      playCap: playCap,
      groups: groups,
      shown: shown,
      ids: ids,
      kcal: kcal,
      summary: "本年共" + list.length + "条，当前展示" + shown.length + "组",
      note: "组内展示顺序不是历史因果顺序。援助格×年只按真实年度 aid.events 口径，不与笔数相加。",
    };
  }

  function contactRows() {
    const rows = [];
    SKINS.forEach((skin) => {
      const cells = [];
      for (let i = 0; i < 8; i++) {
        const p = i / 8;
        cells.push(samplePose({ skin: skin, action: "walk", dir: "e", phase: p }));
      }
      cells.push(samplePose({ skin: skin, action: "walk", dir: "e", phase: 1 }));
      rows.push({ skin: skin, cells: cells });
    });
    return rows;
  }

  const Motion = {
    SKINS: SKINS, DIRS: DIRS, DIR_XFORM: DIR_XFORM, SKIN_RIG: SKIN_RIG, PLAY_CAP: PLAY_CAP,
    MANIFEST: {
      gait: "8 keyframes on one layered skeleton; phase 0 equals phase 1",
      directions: DIR_XFORM,
      shared: "W/SW/NW mirror E/SE/NE. N/S reuse E gait with squash. No independent painted frames.",
      assets: "vector rig, not face-*.png body swap; palette/prop from UnitArt variant",
    },
    wrapPhase: wrapPhase, clamp01: clamp01, skinOf: skinOf,
    samplePose: samplePose, rigMarkup: rigMarkup, applyPose: applyPose,
    aggregate: aggregate, aidMark: aidMark, contactRows: contactRows,
    gaitAt: gaitAt, tillAt: tillAt, harvestAt: harvestAt, IDLE: IDLE,
  };
  root.Motion = Motion;
  if (typeof globalThis !== "undefined") globalThis.Motion = Motion;
  if (typeof module !== "undefined" && module.exports) module.exports = Motion;
})(typeof window !== "undefined" ? window : globalThis);
