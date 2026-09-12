/* 文明观察台 OBS-01 —— 前端（世界概览改版）。
   原则：回放只读已保存的记录；一切数字都来自后台的原始整数账。
   不调用 LLM，不补编动机或因果。 */
"use strict";

const S = {
  token: sessionStorage.getItem("obs_token") || "",
  cfg: null, map: null, run: null, meta: null, series: [], years: new Map(),
  runs: [], t: 0, playing: false, speed: 1, view: "truth", selBand: null, selCell: null,
  timer: null, band: null,
  epoch: 0,
  evScope: "year", evFilter: "all",
  layer: "resource",
  cam: { x: 0, y: 0, k: 1 },
  lastYearLabel: null,
  yearWait: null,
  yearMiss: {},
  hoverCell: null,
  yearLoading: null,
  skin: "sandtable",
  playMode: "year",
  selEvent: null,
  bandScope: "as_of",
  fxGen: 0,
  fxTimers: [],
  fxRaf: null,
  _mapYear: null,
  _mapRun: null,
  opGen: 0,
  bandReqGen: 0,
  bandCache: new Map(),
  loadGen: 0,
  loadOverlay: null,
  lastOkT: 0,
  playWait: null,
  relations: null,
  relReqGen: 0,
  relCache: new Map(),
  relSel: null,
  relCardKey: "",
  cmp: { a: "", b: "", t: null },
  cmpReqGen: 0,
};
const PLAY_PENDING_MS = 700;
function navResult(kind, extra) {
  const ok = kind === "success";
  return Object.assign({ ok: ok, kind: kind, reason: kind }, extra || {});
}
function beginYearLoad(t, op, runId) {
  const gen = ++S.loadGen;
  S.loadOverlay = { gen: gen, t: t, op: op, runId: runId };
  S.yearLoading = t;
  const el = $("year-load");
  if (el) {
    el.hidden = false;
    if ($("year-load-n")) $("year-load-n").textContent = String(t);
  }
  return gen;
}
function endYearLoad(gen) {
  if (!S.loadOverlay || S.loadOverlay.gen !== gen) return;
  S.loadOverlay = null;
  S.yearLoading = null;
  const el = $("year-load");
  if (el) el.hidden = true;
}
function reapNavUi() {
  if (S.loadOverlay && !opAlive(S.loadOverlay.op)) {
    endYearLoad(S.loadOverlay.gen);
  }
  if (S.playWait && !opAlive(S.playWait.op)) S.playWait = null;
  renderYearFailBar();
}
function bumpOp() {
  S.opGen += 1;
  reapNavUi();
  return S.opGen;
}
function opAlive(op) {
  return op === S.opGen;
}
function bandCacheKey(runId, bandId, scope, year) {
  return String(runId) + "|" + String(bandId) + "|" + scope + "|" +
    (scope === "full" ? "full" : String(year));
}
function bandAccept(epoch, runId, bandId, scope, year, req) {
  if (stale(epoch, runId)) return false;
  if (S.selBand !== bandId) return false;
  const nowScope = S.bandScope === "full" ? "full" : "as_of";
  if (nowScope !== scope) return false;
  if (scope !== "full" && S.t !== year) return false;
  if (S.bandReqGen !== req) return false;
  return true;
}
const ykey = (runId, t) => `${runId}|${t}`;
const bump = () => ++S.epoch;
const stale = (myEpoch, myRun) =>
  S.epoch !== myEpoch || !S.run || S.run.run_id !== myRun;
const $ = (id) => document.getElementById(id);

function esc(x) {
  return String(x === null || x === undefined ? "" : x)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

/* ---------------- 展示层纯函数（也给自检用） ---------------- */
function yearMetricRows(aid, recip) {
  const rows = [];
  if (aid) {
    rows.push({ key: "活动", value: aid.events, unit: "次" });
    rows.push({ key: "转移", value: aid.transfers, unit: "笔" });
  }
  if (recip) {
    rows.push({ key: "回助", value: recip.repay_transfers, unit: "笔" });
    rows.push({ key: "分配改变", value: recip.changed, unit: "次" });
  }
  return rows;
}
const OverviewLogic = {
  parseStrictInt(raw, opts) {
    const o = opts || {};
    const s = String(raw == null ? "" : raw).trim();
    if (!/^-?\d+$/.test(s)) {
      return { ok: false, error: (o.name || "这项") + "必须是整数，不能是小数、空值或科学计数法。" };
    }
    const n = Number(s);
    if (!Number.isSafeInteger(n)) {
      return { ok: false, error: (o.name || "这项") + "超出整数范围。" };
    }
    if (o.min != null && n < o.min) {
      return { ok: false, error: (o.name || "这项") + "不能小于 " + o.min + "。" };
    }
    if (o.max != null && n > o.max) {
      return { ok: false, error: (o.name || "这项") + "不能大于 " + o.max + "。" };
    }
    return { ok: true, value: n };
  },
  yearViewLabel(t) {
    return t === 0 ? "开局" : "第 " + t + " 个模拟年";
  },
  formatDelta(now, start, unit) {
    if (now == null || start == null) return { text: "开局读数未加载", dir: 0 };
    const u = unit ? " " + unit : "";
    if (now === start) return { text: "与开局相同", dir: 0 };
    const d = now - start;
    return { text: (d > 0 ? "较开局 +" : "较开局 ") + d + u, dir: Math.sign(d) };
  },
  eventTypeCounts(events) {
    const out = { migrate: 0, split: 0, extinct: 0, share: 0, aid: 0, other: 0, total: 0 };
    (events || []).forEach((e) => {
      if (e && out[e.type] != null) out[e.type] += 1;
      else out.other += 1;
      out.total += 1;
    });
    return out;
  },
  cumulativeRecordedEvents(series, t) {
    const byT = new Map();
    (series || []).forEach((r) => {
      if (r && typeof r.t === "number") byT.set(r.t, r);
    });
    let count = 0, missing = 0;
    for (let i = 0; i <= t; i++) {
      const r = byT.get(i);
      if (!r || typeof r.events !== "number") missing += 1;
      else count += r.events;
    }
    return {
      count, missing, expected: t + 1, have: t + 1 - missing,
      complete: missing === 0,
    };
  },
  flattenEvents(getYear, runId, tEnd) {
    const items = [];
    const missing = [];
    for (let t = 0; t <= tEnd; t++) {
      const rec = getYear(runId, t);
      if (!rec) { missing.push(t); continue; }
      (rec.events || []).forEach((e, i) => {
        items.push(Object.assign({}, e, { t: t, _i: i }));
      });
    }
    return { items, missing };
  },
  memCaption(entry, t) {
    if (!entry) return { kind: "unknown", text: "未知" };
    const ts = entry[1];
    if (ts === null || ts === undefined) {
      return { kind: "known-untimed", text: "时间未记录" };
    }
    if (ts === t) return { kind: "fresh", text: "当年已知" };
    return { kind: "stale", text: "第 " + ts + " 年的记录" };
  },
  buildYearSummary(input) {
    const t = input.t, year = input.year || {}, agg = input.agg || {};
    const ev = OverviewLogic.eventTypeCounts(input.events);
    const births = year.births_cum, demo = year.deaths_demo_cum, md = year.mig_deaths_cum;
    const sentences = [];
    if (t === 0) {
      sentences.push("这是开局。当前共有 " + (agg.bands == null ? "—" : agg.bands) +
        " 个群体、" + (agg.pop == null ? "—" : agg.pop) + " 人。");
      sentences.push("第 0 年没有上一年度，不显示同比变化。");
      if (ev.total === 0) sentences.push("本年没有记录到迁移、分裂、群体消失、信息交换或食物援助事件。");
      else {
        sentences.push("记录到 " + ev.migrate + " 次迁移、" + ev.split +
          " 次群体分裂、" + ev.extinct + " 次群体消失、" + ev.share +
          " 次信息交换、" + ev.aid + " 条食物援助（逐笔转移）。");
      }
      return {
        sentences, events: ev, births: births, demoDeaths: demo, migDeaths: md,
        metrics: yearMetricRows(input.aid, input.recip)
      };
    }
    sentences.push("本年出生 " + births + " 人，原规则死亡 " + demo + " 人，迁移死亡 " + md + " 人。");
    if (ev.total === 0) {
      sentences.push("本年没有记录到迁移、分裂、消失、信息交换或援助事件。当前 " +
        agg.bands + " 个群体、" + agg.pop + " 人。");
    } else {
      sentences.push("记录 " + ev.migrate + " 次迁移、" + ev.split + " 次分裂、" +
        ev.share + " 次信息交换、" + ev.aid + " 条援助。当前 " +
        agg.bands + " 个群体、" + agg.pop + " 人。");
    }
    return {
      sentences, events: ev, births: births, demoDeaths: demo, migDeaths: md,
      metrics: yearMetricRows(input.aid, input.recip)
    };
  },
  yearMetrics: yearMetricRows,
  _appendAidLedger(sentences, aid) {
    if (!aid) return;
    sentences.push("援助账本：援助活动 " + aid.events + " 次（格×年，一次多人援助算 1），" +
      "逐笔转移 " + aid.transfers + " 笔（一个供给方给一个接收方算 1）。" +
      "活动次数与转移笔数不是同一个计数，不能相加或互相替代。");
  },
  _appendRecipLedger(sentences, recip) {
    if (!recip) return;
    sentences.push("回助账本：记得对方帮过自己的转移 " + recip.repay_transfers +
      " 笔（含碰巧，不代表规则起作用）；优先阶段 " + recip.transfers +
      " 笔；分配被优先规则改变 " + recip.changed +
      " 次（格×年）。repay、优先阶段笔数、changed 不是同一个计数。");
  },
  flowAnchor(e, endCellByBand) {
    if (!e || (e.type !== "share" && e.type !== "aid")) return null;
    if (e.cell === null || e.cell === undefined || e.cell === "") {
      return { kind: "unrecorded", cell: null };
    }
    const cell = +e.cell;
    if (!Number.isFinite(cell)) return { kind: "unrecorded", cell: null };
    const d = endCellByBand ? endCellByBand[String(e.donor)] : undefined;
    const r = endCellByBand ? endCellByBand[String(e.receiver)] : undefined;
    if (d === cell && r === cell) return { kind: "arc", cell: cell };
    return { kind: "mark", cell: cell };
  },
};
window.OverviewLogic = OverviewLogic;

const DirectorLogic = {
  orderNote: "同一年的事件按记录数组列出，这个顺序不保证年内机制先后，也不是因果或精确发生顺序。",
  yearFromEventId(eid) {
    const m = String(eid || "").match(/^t(\d+)-/);
    return m ? Number(m[1]) : null;
  },
  eventKey(e, t, i) {
    if (e && e.id != null && String(e.id) !== "") return String(e.id);
    const yr = e && e.year != null ? e.year : t;
    const idx = e && e._i != null ? e._i : i;
    return "t" + yr + "-" + ((e && e.type) || "ev") + "-" + idx;
  },
  eventYearsFromSeries(series) {
    const years = [];
    (series || []).forEach((r) => {
      if (!r || typeof r.t !== "number") return;
      if (typeof r.events === "number" && r.events > 0) years.push(r.t);
    });
    years.sort((a, b) => a - b);
    return years;
  },
  nextEventYear(eventYears, t) {
    const ys = eventYears || [];
    for (let i = 0; i < ys.length; i++) if (ys[i] > t) return ys[i];
    return null;
  },
  prevEventYear(eventYears, t) {
    const ys = eventYears || [];
    for (let i = ys.length - 1; i >= 0; i--) if (ys[i] < t) return ys[i];
    return null;
  },
  eventModeStatus(input) {
    const series = (input && input.series) || [];
    const recorded = input && input.yearsRecorded != null ? input.yearsRecorded : 0;
    const runStatus = (input && input.runStatus) || "";
    const rec = input ? input.rec : null;
    const t = input ? input.t : null;
    const computing = runStatus === "queued" || runStatus === "running";
    if (computing && recorded <= 0) {
      return { kind: "computing", text: "后台还在计算，事件清单尚未落盘。不把空清单当成 0 条事件。" };
    }
    if (t != null && t > recorded && computing) {
      return { kind: "computing", text: "第 " + t + " 年还在计算，记录尚未落盘。" };
    }
    if (t != null && rec == null && recorded >= t) {
      return { kind: "missing", text: "第 " + t + " 年的记录尚未加载或读取失败，不把空清单当成 0 条事件。" };
    }
    const years = this.eventYearsFromSeries(series);
    if (series.length && years.length === 0 && !computing) {
      return { kind: "none", text: "这次运行已保存的年份里没有可核实事件。人口、出生与账本迁移次数不是事件。" };
    }
    if (rec && Array.isArray(rec.events) && rec.events.length === 0) {
      return { kind: "empty-year", text: (t === 0 ? "开局" : "第 " + t + " 年") +
        "没有可核实事件。人口变化与出生人数不是事件。" };
    }
    if (rec && rec.events && rec.events.length) return { kind: "ready", text: "" };
    if (computing) {
      return { kind: "computing", text: "后台还在计算，事件清单尚未落盘。不把空清单当成 0 条事件。" };
    }
    return { kind: "missing", text: "事件记录尚未就绪，不补编。" };
  },
  displayYearFromMemory(mem) {
    if (!mem) return { year: null, eventId: null, note: "未记录" };
    if (mem.last_year_display != null && mem.last_year_display !== "") {
      return { year: mem.last_year_display, eventId: mem.last_event_id || null, source: "last_year_display" };
    }
    if (mem.last_event_id) {
      const y = this.yearFromEventId(mem.last_event_id);
      if (y != null) return { year: y, eventId: mem.last_event_id, source: "last_event_id" };
    }
    return { year: null, eventId: null,
      note: "未记录：没有可跳转的展示年份（不使用内部 tick last_year）" };
  },
  displayYearFromBasis(basis) {
    if (!basis) return { year: null, eventId: null };
    if (basis.remembered_last_year_display != null && basis.remembered_last_year_display !== "") {
      return { year: basis.remembered_last_year_display,
        eventId: basis.remembered_last_event_id || null, source: "remembered_last_year_display" };
    }
    if (basis.remembered_last_event_id) {
      const y = this.yearFromEventId(basis.remembered_last_event_id);
      if (y != null) {
        return { year: y, eventId: basis.remembered_last_event_id, source: "remembered_last_event_id" };
      }
    }
    const priors = basis.prior_events || [];
    if (priors.length) {
      const last = priors[priors.length - 1];
      const y = this.yearFromEventId(last);
      if (y != null) return { year: y, eventId: last, source: "prior_events" };
    }
    return { year: null, eventId: null,
      note: "未记录：找不到先前事件（不使用 remembered_last_year 内部 tick）" };
  },
  eventFocus(e) {
    if (!e) return { cells: [], locate: false, kind: "none", note: "未选中事件", related: [] };
    const related = [];
    ["parent", "donor", "receiver", "band"].forEach((k) => {
      if (e[k] != null && e[k] !== "") related.push({ role: k, id: String(e[k]) });
    });
    if (e.type === "share" || e.type === "aid") {
      if (e.cell === null || e.cell === undefined || e.cell === "") {
        return { cells: [], locate: false, kind: e.type,
          note: "信息/援助地点未记录，不拿年末群体位置猜测。", related, repay: !!e.repay };
      }
      const cell = +e.cell;
      if (!Number.isFinite(cell)) {
        return { cells: [], locate: false, kind: e.type,
          note: "信息/援助地点未记录，不拿年末群体位置猜测。", related, repay: !!e.repay };
      }
      return { cells: [cell], locate: true, kind: e.type,
        note: "锚定事件格第 " + cell + " 号（不是年末群体位置）。", related, repay: !!e.repay };
    }
    if (e.type === "migrate") {
      const cells = [];
      if (e.from != null && e.from !== "") cells.push(+e.from);
      if (e.to != null && e.to !== "") cells.push(+e.to);
      const valid = cells.filter((n) => Number.isFinite(n));
      if (!valid.length) {
        return { cells: [], locate: false, kind: "migrate",
          note: "迁移地点未记录，不拿年末位置猜测。", related };
      }
      return { cells: valid, locate: true, kind: "migrate",
        note: "只表现端点位置变化。具体路线未记录，不虚构中间格子。",
        related, from: e.from, to: e.to };
    }
    if (e.type === "split" || e.type === "extinct") {
      return { cells: [], locate: false, kind: e.type,
        note: "现有日志只有群体 ID，没有事件格。地点未记录，禁用地图定位，不拿年末位置猜测。",
        related, parent: e.parent || null, band: e.band || null };
    }
    if (e.cell != null && e.cell !== "") {
      const cell = +e.cell;
      if (Number.isFinite(cell)) {
        return { cells: [cell], locate: true, kind: e.type || "other",
          note: "锚定记录中的格子。", related };
      }
    }
    return { cells: [], locate: false, kind: e.type || "other",
      note: "地点未记录，不拿年末位置猜测。", related };
  },
  prefersReducedMotion() {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    try { return window.matchMedia("(prefers-reduced-motion: reduce)").matches; }
    catch (err) { return false; }
  },
};
window.DirectorLogic = DirectorLogic;

const NetworkLogic = {
  layoutCircle(nodes, w, h) {
    const list = nodes || [];
    const n = list.length;
    const cx = w / 2, cy = h / 2, r = Math.min(w, h) / 2 - 40;
    if (!n) return [];
    if (n === 1) return [{ id: String(list[0].id), x: cx, y: cy, node: list[0] }];
    return list.map((node, i) => {
      const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
      return { id: String(node.id), x: cx + r * Math.cos(a), y: cy + r * Math.sin(a), node: node };
    });
  },
  pairKind(edges, donor, receiver) {
    const hasRev = (edges || []).some((e) =>
      String(e.donor) === String(receiver) && String(e.receiver) === String(donor));
    return hasRev ? "two-way" : "one-way";
  },
  idStr(x) { return x == null ? "" : String(x); },
  futureSteps(traj, atYear) {
    if (atYear == null) return [];
    return (traj || []).filter((p) => p && p[0] > atYear);
  },
  sparkPath(sizes, w, h) {
    const pts = (sizes || []).filter((p) => p && p.length >= 2);
    if (pts.length < 2) return "";
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    const minX = Math.min.apply(null, xs), maxX = Math.max.apply(null, xs);
    const minY = Math.min.apply(null, ys), maxY = Math.max.apply(null, ys);
    const dx = Math.max(1, maxX - minX), dy = Math.max(1, maxY - minY);
    return pts.map((p, i) => {
      const x = ((p[0] - minX) / dx) * (w - 4) + 2;
      const y = h - 2 - ((p[1] - minY) / dy) * (h - 4);
      return (i ? "L" : "M") + x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
  },
  migrateEndpoints(traj) {
    const pts = (traj || []).filter((p) => p && p.length >= 2);
    const out = [];
    for (let i = 1; i < pts.length; i++) {
      if (pts[i][1] === pts[i - 1][1]) continue;
      out.push({ fromYear: pts[i - 1][0], from: pts[i - 1][1], toYear: pts[i][0], to: pts[i][1] });
    }
    return out;
  },
  quadControl(ax, ay, bx, by, sign, mag) {
    const mx = (ax + bx) / 2, my = (ay + by) / 2;
    let dx = bx - ax, dy = by - ay;
    if (dx < 0 || (dx === 0 && dy < 0)) { dx = -dx; dy = -dy; }
    const len = Math.hypot(dx, dy) || 1;
    const m = mag == null ? 36 : mag;
    const s = sign == null ? 1 : sign;
    return { x: mx + (-dy / len) * m * s, y: my + (dx / len) * m * s };
  },
  edgeBendSign(edges, donor, receiver) {
    if (this.pairKind(edges, donor, receiver) !== "two-way") return 1;
    return String(donor) < String(receiver) ? 1 : -1;
  },
  nodeName(nodes, id) {
    const n = (nodes || []).find((x) => String(x.id) === String(id));
    return (n && n.name) ? n.name : (String(id).slice(0, 8) + "…");
  },
};
window.NetworkLogic = NetworkLogic;

const CompareLogic = {
  row(label, a, b, missA, missB) {
    return {
      label: label,
      a: missA ? null : a,
      b: missB ? null : b,
      missA: !!missA,
      missB: !!missB,
      diff: !missA && !missB && a !== b,
    };
  },
  configDiff(runA, runB) {
    const keys = ["engine", "seed", "sigma_m", "move_mort_m", "share_m", "aid_m", "recip_m", "years", "arm"];
    const out = [];
    (keys).forEach((k) => {
      const va = runA ? runA[k] : null, vb = runB ? runB[k] : null;
      if (String(va) !== String(vb)) out.push({ key: k, a: va, b: vb });
    });
    return out;
  },
  stockSum(rec) {
    if (!rec || !rec.stock) return null;
    return rec.stock.reduce((s, x) => s + (x || 0), 0);
  },
};
window.CompareLogic = CompareLogic;

const LIB_KEY = "obs_lib_v1";
const LibraryLogic = {
  empty() { return { years: [], events: [] }; },
  loadAll() {
    try { return JSON.parse(localStorage.getItem(LIB_KEY) || "{}") || {}; }
    catch (e) { return {}; }
  },
  saveAll(all) { localStorage.setItem(LIB_KEY, JSON.stringify(all)); },
  forRun(all, runId) {
    const id = String(runId || "");
    if (!all[id]) all[id] = this.empty();
    return all[id];
  },
  pinYear(all, runId, t) {
    const lib = this.forRun(all, runId);
    if (lib.years.indexOf(t) < 0) lib.years.push(t);
    lib.years.sort((a, b) => a - b);
    return all;
  },
  pinEvent(all, runId, ev) {
    const lib = this.forRun(all, runId);
    const id = ev && ev.id;
    if (!id) return all;
    if (!lib.events.some((e) => e.id === id)) lib.events.push({ id: String(id), t: ev.t != null ? ev.t : ev.year, type: ev.type || "" });
    return all;
  },
  exportRecord(run, t, rec, extra) {
    extra = extra || {};
    const evs = ((rec && rec.events) || []).map((e) => ({
      id: String(e.id || ""), type: e.type || "", text: e.text || "", source: e.source || "",
    }));
    return {
      run_id: run ? String(run.run_id) : "",
      engine: run ? (run.engine || "") : "",
      engine_sha256: run ? (run.engine_sha256 || "") : "",
      seed: run ? run.seed : null,
      years: run ? run.years : null,
      sigma_m: run ? run.sigma_m : null,
      move_mort_m: run ? run.move_mort_m : null,
      share_m: run ? run.share_m : null,
      aid_m: run ? run.aid_m : null,
      recip_m: run ? run.recip_m : null,
      arm: run ? run.arm : null,
      year: t,
      year_summary: extra.summary || "",
      events: evs,
      selected_event: extra.selEvent || "",
      selected_band: extra.selBand || "",
    };
  },
  hasForbidden(obj) {
    const s = JSON.stringify(obj);
    return /X-Observer-Token|obs_token|\/Users\/|app_secret|server_config/i.test(s);
  },
};
window.LibraryLogic = LibraryLogic;

function hashParams() {
  const out = {};
  (location.hash || "").replace(/^#/, "").split("&").forEach((kv) => {
    const [k, v] = kv.split("=");
    if (k) out[k] = decodeURIComponent(v || "");
  });
  return out;
}
function setHash(patch) {
  const h = Object.assign(hashParams(), patch);
  Object.keys(h).forEach((k) => { if (h[k] === "" || h[k] === null) delete h[k]; });
  const str = Object.entries(h).map(([k, v]) => k + "=" + encodeURIComponent(v)).join("&");
  history.replaceState(null, "", "#" + str);
}
function runEngineName(run) {
  return (run && run.engine) || (S.cfg && S.cfg.default_engine) || "exp03";
}
function runEngineInfo(run) {
  const name = runEngineName(run);
  if (S.cfg && S.cfg.engines && S.cfg.engines[name]) return S.cfg.engines[name];
  return (S.cfg && S.cfg.engine) || {};
}
function engineHasParam(name, param) {
  const inf = S.cfg && S.cfg.engines && S.cfg.engines[name];
  if (!inf) return false;
  if (inf.engine_params && inf.engine_params.indexOf(param) >= 0) return true;
  if (Array.isArray(inf.params) && inf.params.some((p) => p && p.name === param)
      && param !== "seed" && param !== "years") return true;
  return false;
}
function engineParamMeta(engine, param) {
  const inf = S.cfg && S.cfg.engines && S.cfg.engines[engine];
  if (inf && Array.isArray(inf.params)) {
    const hit = inf.params.find((p) => p && p.name === param);
    if (hit) return hit;
  }
  return null;
}
const NEED = () => {
  const inf = S.run ? runEngineInfo(S.run) : (S.cfg && S.cfg.engine);
  return (inf && inf.constants && inf.constants.NEED_PC) ? inf.constants.NEED_PC : 730000;
};

const nf = (x) => (x === null || x === undefined ? "—" : Number(x).toLocaleString("zh-CN"));
function py(kcal, digits) {
  if (digits == null) digits = 1;
  if (kcal === null || kcal === undefined) return "—";
  return (kcal / NEED()).toFixed(digits);
}
function kcalCell(kcal) {
  if (kcal === null || kcal === undefined) return `<span class="na">未记录</span>`;
  return `${py(kcal)} <small>人年口粮 / ${nf(kcal)} kcal</small>`;
}
function pct(num, den, digits) {
  if (digits == null) digits = 3;
  if (!den) return `<span class="na">不适用（分母为 0）</span>`;
  return (num / den * 100).toFixed(digits) + "%";
}
function tsfmt(v) {
  if (!v) return "—";
  const d = new Date(v * 1000);
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
const STATUS_TEXT = {
  queued: ["排队中", "s-wait"], running: ["运行中", "s-run"], done: ["完成", "s-done"],
  failed: ["失败", "s-bad"], interrupted: ["中断", "s-bad"], canceled: ["已取消", "s-off"],
};
function statusBadge(st) {
  const pair = STATUS_TEXT[st] || [st, "s-off"];
  return `<span class="badge ${pair[1]}">${esc(pair[0])}</span>`;
}
function recNow() {
  return S.run ? S.years.get(ykey(S.run.run_id, S.t)) : null;
}
function yearMissKey(runId, t) { return runId + "|" + t; }
function isPendingYearError(err, t) {
  if (!err || err.status !== 404) return false;
  if (!S.run) return false;
  const rec = S.run.years_recorded ?? 0;
  const st = S.run.status;
  if (st === "queued" || st === "running") return true;
  if (rec < t) return true;
  if (t === 0 && rec === 0) return true;
  if (st === "done" && rec >= t) return true;
  return false;
}
function yearWaitMessage() {
  if (!S.run) return "还没有选中任何运行。";
  if (S.yearWait && !S.yearWait.pending) {
    return "读取第 " + S.t + " 年失败：" + (S.yearWait.message || "未知错误");
  }
  if (S.t === 0) return "等待开局记录生成（后台还在写入第 0 年，不会重新计算世界）。";
  return "等待第 " + S.t + " 年落盘（已计算 " + (S.run.years_recorded ?? 0) + " 年）。";
}
function shouldRetryMissingYear(run, t) {
  if (!run) return false;
  if (S.years.has(ykey(run.run_id, t))) return false;
  const st = run.status;
  if (st === "failed" || st === "interrupted" || st === "canceled") return false;
  const rec = run.years_recorded ?? 0;
  if (st === "queued" || st === "running") return true;
  if (rec >= t) {
    const n = S.yearMiss[yearMissKey(run.run_id, t)] || 0;
    return n < 8;
  }
  return false;
}

/* ---------------- API ---------------- */
async function api(path, opts) {
  const h = Object.assign({ "Content-Type": "application/json" }, (opts && opts.headers) || {});
  if (S.token) h["X-Observer-Token"] = S.token;
  const r = await fetch(path, Object.assign({}, opts || {}, { headers: h }));
  if (!r.ok) {
    let detail = "HTTP " + r.status;
    try { detail = (await r.json()).detail || detail; } catch (e) { /* 忽略 */ }
    const err = new Error(detail); err.status = r.status; throw err;
  }
  return r.json();
}

/* ---------------- 顶部状态条（契约：必须含运行名） ---------------- */
function renderStatus() {
  const box = $("statusline");
  if (!S.cfg) { box.textContent = "正在连接后台…"; return; }
  const parts = [];
  if (S.run) {
    parts.push(`<b>当前运行</b> ${esc(S.run.label || S.run.run_id)} ${statusBadge(S.run.status)}` +
      (S.run.kind === "preset" ? ` <span class="badge s-off">预生成案例</span>` : ""));
    parts.push(`<b>回放</b> ${esc(OverviewLogic.yearViewLabel(S.t))}`);
    parts.push(`<b>已计算</b> ${S.run.years_recorded ?? S.run.years_done}/${S.run.years} 年`);
    const einfo = runEngineInfo(S.run);
    parts.push(`<b>模型</b> ${esc(S.run.engine_path || einfo.engine_path || runEngineName(S.run))}`);
  } else {
    parts.push("尚未选择运行");
  }
  box.innerHTML = parts.join(" ");
}

/* ---------------- 六项概览 + 人话摘要 ---------------- */
function startAgg() {
  const r = (S.series || []).find((x) => x.t === 0);
  return r ? r.agg : null;
}
function renderOverview() {
  if (!$("ov-year-value")) return;
  const rec = recNow();
  const ylab = OverviewLogic.yearViewLabel(S.t);
  $("ov-year-value").textContent = ylab;
  if (S.lastYearLabel !== ylab) {
    $("ov-year-value").classList.remove("pulse");
    void $("ov-year-value").offsetWidth;
    $("ov-year-value").classList.add("pulse");
    S.lastYearLabel = ylab;
  }
  $("ov-year-sub").textContent = S.t === 0
    ? "开局 · 这是回放位置，不是后台算到哪"
    : "正在回放这一年，不是后台计算进度";
  $("ov-year").classList.add("viewing");
  renderHudParams();
  renderDensity();

  if (!S.run) {
    ["ov-calc-value", "ov-pop-value", "ov-bands-value", "ov-ev-cum-value", "ov-ev-now-value"]
      .forEach((id) => { $(id).textContent = "—"; });
    $("year-summary").textContent = "还没有选中运行。到「创世 / 运行」发起或打开一次模拟。";
    return;
  }
  const recorded = S.run.years_recorded ?? 0;
  $("ov-calc-value").textContent = recorded + " / " + S.run.years + " 年";
  $("ov-calc-sub").innerHTML = statusBadge(S.run.status) +
    (S.run.kind === "preset" ? " · 预生成案例" : "") +
    " · 后台已经算到第 " + recorded + " 年";

  if (!rec) {
    $("ov-pop-value").textContent = "…";
    $("ov-pop-sub").textContent = yearWaitMessage();
    $("ov-bands-value").textContent = "…";
    $("ov-bands-sub").textContent = "跟随回放年份";
    $("ov-ev-now-value").textContent = "…";
    $("ov-ev-now-sub").textContent = "本年事件清单尚未加载";
    $("year-summary").textContent = yearWaitMessage();
    if ($("year-metrics")) $("year-metrics").innerHTML = "";
  } else {
    const st = startAgg();
    $("ov-pop-value").textContent = nf(rec.agg.pop) + " 人";
    if (S.t === 0) {
      $("ov-pop-sub").textContent = "开局（无同比）";
      $("ov-pop-sub").className = "ov-s";
    } else {
      const d = OverviewLogic.formatDelta(rec.agg.pop, st ? st.pop : null, "人");
      $("ov-pop-sub").textContent = d.text;
      $("ov-pop-sub").className = "ov-s " + (d.dir > 0 ? "up" : d.dir < 0 ? "down" : "");
    }
    $("ov-bands-value").textContent = nf(rec.agg.bands) + " 个";
    if (S.t === 0) {
      $("ov-bands-sub").textContent = "开局（无同比）";
      $("ov-bands-sub").className = "ov-s";
    } else {
      const d = OverviewLogic.formatDelta(rec.agg.bands, st ? st.bands : null, "个");
      $("ov-bands-sub").textContent = d.text;
      $("ov-bands-sub").className = "ov-s " + (d.dir > 0 ? "up" : d.dir < 0 ? "down" : "");
    }
    $("ov-ev-now-value").textContent = rec.events.length + " 条";
    $("ov-ev-now-sub").textContent = "来自已记录事件清单，不是出生人数";
    const sum = OverviewLogic.buildYearSummary({
      t: S.t, year: rec.year, agg: rec.agg, events: rec.events,
      ledgerMig: rec.year ? rec.year.mig_total : null,
      aid: rec.aid || null,
      recip: rec.recip || null,
    });
    $("year-summary").textContent = sum.sentences.join("");
    if ($("year-metrics")) {
      $("year-metrics").innerHTML = (sum.metrics || []).map((m) =>
        `<span class="metric-chip"><b>${esc(m.key)}</b> ${nf(m.value)} <small>${esc(m.unit)}</small></span>`).join("");
    }
  }

  const cum = OverviewLogic.cumulativeRecordedEvents(S.series, S.t);
  if (!S.series.length) {
    $("ov-ev-cum-value").textContent = "…";
    $("ov-ev-cum-sub").textContent = "曲线数据尚未加载，不把空值当成 0 条";
  } else if (!cum.complete) {
    $("ov-ev-cum-value").textContent = nf(cum.count) + " 条";
    $("ov-ev-cum-sub").textContent = "只统计已加载的 " + cum.have + "/" + cum.expected +
      " 年，不是最终总数";
  } else {
    $("ov-ev-cum-value").textContent = nf(cum.count) + " 条";
    $("ov-ev-cum-sub").textContent = "截至" + OverviewLogic.yearViewLabel(S.t) + " · 已记录事件";
  }
  renderYearFailBar();
}

function renderHudParams() {
  const box = $("hud-params");
  if (!box) return;
  if (!S.run) { box.textContent = ""; return; }
  const bits = [
    "引擎 " + (S.run.engine || "exp03"),
    "seed " + S.run.seed,
    "SIGMA_M " + S.run.sigma_m + "‰",
    "MOVE_MORT_M " + S.run.move_mort_m + "‰",
  ];
  if (engineHasParam(runEngineName(S.run), "share_m")) bits.push("SHARE_M " + (S.run.share_m ?? 0) + "‰");
  if (engineHasParam(runEngineName(S.run), "aid_m")) bits.push("AID_M " + (S.run.aid_m ?? 0) + "‰");
  if (engineHasParam(runEngineName(S.run), "recip_m")) bits.push("RECIP_M " + (S.run.recip_m ?? 0) + "‰");
  bits.push(S.cfg && S.cfg.arms[S.run.arm] ? S.cfg.arms[S.run.arm].label : S.run.arm);
  box.textContent = bits.join("  ·  ");
}

function renderDensity() {
  const svg = $("density");
  if (!svg) return;
  const s = S.series || [];
  if (!s.length) { svg.innerHTML = ""; return; }
  const w = 1000, h = 18;
  svg.setAttribute("viewBox", "0 0 " + w + " " + h);
  const maxe = Math.max(1, ...s.map((r) => r.events || 0));
  let bars = "";
  s.forEach((r, i) => {
    const x = i * w / Math.max(s.length, 1);
    const bh = (r.events || 0) / maxe * (h - 2);
    const hot = r.t === S.t;
    const hasEv = (r.events || 0) > 0;
    const fill = hot ? "#d4b06a"
      : (S.playMode === "events" && !hasEv ? "rgba(94,102,96,.28)" : "rgba(111,179,124,.55)");
    bars += `<rect x="${x.toFixed(2)}" y="${(h - bh).toFixed(2)}" width="${Math.max(1, w / s.length - 0.4).toFixed(2)}" height="${bh.toFixed(2)}" fill="${fill}"/>`;
  });
  svg.innerHTML = bars;
}

function renderTech() {
  const box = $("tech-body");
  if (!box) return;
  if (!S.run || !S.cfg) { box.textContent = "打开一次运行后显示。"; return; }
  const rec = recNow();
  const arm = S.cfg.arms[S.run.arm];
  const einfo = runEngineInfo(S.run);
  const rows = [
    ["本次运行引擎", (S.run.engine || runEngineName(S.run)) + " · " + (S.run.engine_path || einfo.engine_path || "")],
    ["基线", S.run.baseline_commit || einfo.baseline_commit || "—"],
    ["引擎 sha256", ((S.run.engine_sha256 || einfo.engine_sha256 || "") + "").slice(0, 16) + "…"],
    ["种子 / 年数", S.run.seed + " / " + S.run.years],
    ["SIGMA_M", S.run.sigma_m + "‰"],
    ["MOVE_MORT_M", S.run.move_mort_m + "‰"],
    ["SHARE_M", engineHasParam(runEngineName(S.run), "share_m")
      ? (S.run.share_m ?? 0) + "‰（本次运行实际值）" : "无此参数"],
    ["AID_M", engineHasParam(runEngineName(S.run), "aid_m")
      ? (S.run.aid_m ?? 0) + "‰（本次运行实际值）" : "无此参数"],
    ["RECIP_M", engineHasParam(runEngineName(S.run), "recip_m")
      ? (S.run.recip_m ?? 0) + "‰（本次运行实际值）" : "无此参数"],
    ["信息条件", arm ? arm.label : S.run.arm],
    ["model_run_id", S.run.model_run_id || "（尚未写入）"],
    ["full_digest", S.run.full_digest || "（尚未写入）"],
  ];
  if (rec) {
    rows.push(["状态哈希", rec.integrity.state_hash]);
    rows.push(["能量守恒误差", String(rec.integrity.conservation_error)]);
    rows.push(["人口恒等误差", String(rec.integrity.population_identity_error)]);
    if (rec.integrity.share_ledger_error != null) {
      rows.push(["信息账误差", String(rec.integrity.share_ledger_error)]);
    }
    if (rec.integrity.aid_ledger_error != null) {
      rows.push(["援助账误差", String(rec.integrity.aid_ledger_error)]);
    }
    if (rec.share) {
      rows.push(["本年信息交换（采纳/拒绝）",
        rec.share.adopted + " / " + rec.share.rejected +
        "（收到 " + rec.share.received + "）"]);
      rows.push(["累计采纳", String(rec.share.cum_adopted)]);
    }
    if (rec.aid) {
      rows.push(["援助活动次数", rec.aid.events + " 次（格×年）"]);
      rows.push(["逐笔转移", rec.aid.transfers + " 笔"]);
      rows.push(["本年援助食物", rec.aid.kcal + " kcal"]);
      rows.push(["累计援助活动 / 转移", rec.aid.cum_events + " 次 / " + rec.aid.cum_transfers + " 笔"]);
    }
    if (rec.recip) {
      rows.push(["回助（含碰巧）", rec.recip.repay_transfers + " 笔"]);
      rows.push(["优先阶段转移", rec.recip.transfers + " 笔"]);
      rows.push(["分配被规则改变", rec.recip.changed + " 次（格×年）"]);
      rows.push(["累计分配改变", String(rec.recip.cum_changed) + " 次"]);
    }
    const used = S.run.params_used;
    if (Array.isArray(used) && used.length) {
      rows.push(["本次实际参数", used.map((p) =>
        (p.label || p.name) + "=" + p.value + (p.unit ? p.unit : "")).join(" · ")]);
    }
    rows.push(["累计吃掉", py(rec.cum.out_eat) + " 人年口粮"]);
    rows.push(["累计腐损", py(rec.cum.out_spoil) + " 人年口粮"]);
  }
  box.innerHTML = `<div class="kv">${rows.map(([k, v]) =>
    `<div class="k">${esc(k)}</div><div class="v">${esc(v)}</div>`).join("")}</div>`;
}

/* ---------------- 地图 ---------------- */
const R = 30, SQ3 = Math.sqrt(3);
function hexPath(cx, cy) {
  let d = "";
  for (let k = 0; k < 6; k++) {
    const a = Math.PI / 180 * (60 * k - 90);
    d += (k ? "L" : "M") + (cx + R * Math.cos(a)).toFixed(1) + "," + (cy + R * Math.sin(a)).toFixed(1);
  }
  return d + "Z";
}
function cellCenter(c) {
  const x = 28 + (c.col + (c.row % 2 === 0 ? 0.5 : 0)) * SQ3 * R + SQ3 * R / 2;
  const y = 26 + c.row * 1.5 * R + R;
  return [x, y];
}
function ramp(f) {
  f = Math.max(0, Math.min(1, f));
  const a = [18, 32, 26], b = [111, 179, 124], c = [212, 176, 106];
  const mix = (p, q, t) => p.map((v, i) => Math.round(v + (q[i] - v) * t));
  const rgb = f < 0.55 ? mix(a, b, f / 0.55) : mix(b, c, (f - 0.55) / 0.45);
  return "rgb(" + rgb.join(",") + ")";
}
function camViewBox() {
  const W = 520, H = 430, k = S.cam.k;
  const w = W / k, h = H / k;
  const x = (W - w) / 2 - S.cam.x, y = (H - h) / 2 - S.cam.y;
  return x + " " + y + " " + w + " " + h;
}
function setLayer(name) {
  if (name === "mem") { setView("mem"); S.layer = "mem"; }
  else {
    S.layer = name || "resource";
    if (S.view === "mem") S.view = "truth";
    setHash({ view: "" });
  }
  document.querySelectorAll("#layers [data-layer]").forEach((b) =>
    b.classList.toggle("on", b.dataset.layer === S.layer || (S.layer === "resource" && b.id === "v-truth")));
  if ($("v-truth")) $("v-truth").classList.toggle("on", S.layer === "resource" && S.view !== "mem");
  if ($("v-mem")) $("v-mem").classList.toggle("on", S.view === "mem" || S.layer === "mem");
  renderMap();
}
function renderMap() {
  const svg = $("map");
  if (!svg) return;
  svg.setAttribute("viewBox", camViewBox());
  if (!S.map || !S.run) { svg.innerHTML = ""; return; }
  const rec = recNow();
  if (!rec) {
    svg.innerHTML = `<text x="24" y="40" fill="#d4b06a">${esc(yearWaitMessage())}</text>`;
    return;
  }
  const cap = S.meta ? S.meta.cap : null;
  const layer = S.view === "mem" ? "mem" : (S.layer || "resource");
  const memBand = layer === "mem" && S.selBand
    ? rec.bands.find((b) => b.id === S.selBand) : null;
  const byCell = {};
  rec.bands.forEach((b) => { (byCell[b.cell] = byCell[b.cell] || []).push(b); });
  const popByCell = {}, storeByCell = {};
  rec.bands.forEach((b) => {
    popByCell[b.cell] = (popByCell[b.cell] || 0) + b.size;
    storeByCell[b.cell] = (storeByCell[b.cell] || 0) + b.store;
  });
  const maxPop = Math.max(1, ...Object.values(popByCell), 1);
  const maxStore = Math.max(1, ...Object.values(storeByCell), 1);
  const eventCells = new Set();
  (rec.events || []).forEach((e) => {
    if (e.cell != null) eventCells.add(+e.cell);
    if (e.to != null) eventCells.add(+e.to);
    if (e.from != null) eventCells.add(+e.from);
    const bd = rec.bands.find((b) => b.id === e.band || b.id === e.receiver || b.id === e.donor);
    if (bd) eventCells.add(bd.cell);
  });

  let out = `<defs>
    <pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="7" height="7" fill="#141a16"/><line x1="0" y1="0" x2="0" y2="7" stroke="#3a433c" stroke-width="3"/>
    </pattern>
    <filter id="glow"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>`;

  S.map.cells.forEach((c, idx) => {
    const xy = cellCenter(c), cx = xy[0], cy = xy[1];
    let fill = "url(#hatch)", label = "", sub = "", title = "第 " + c.i + " 号格";
    if (c.passable) {
      const capv = cap ? cap[idx] : 0;
      if (layer === "mem") {
        if (!memBand) { fill = "#1a2420"; label = "先选群体"; }
        else {
          const e = memBand.mem[String(c.i)];
          const capn = OverviewLogic.memCaption(e, S.t);
          if (capn.kind === "unknown") { fill = "#2a2e2b"; label = "未知"; title += " · 该群体未知"; }
          else {
            fill = ramp(capv ? e[0] / capv : 0);
            label = py(e[0], 0); sub = capn.text;
            title += " · 记得食物 " + py(e[0], 1) + " 人年口粮 · " + capn.text;
          }
        }
      } else if (layer === "pop") {
        const p = popByCell[c.i] || 0;
        fill = ramp(p / maxPop); label = p ? p + "人" : "";
        title += " · 本格人口 " + p;
      } else if (layer === "store") {
        const st = storeByCell[c.i] || 0;
        fill = ramp(st / maxStore); label = st ? py(st, 0) : "";
        title += " · 本格储粮 " + py(st, 1) + " 人年口粮";
      } else if (layer === "event") {
        fill = eventCells.has(c.i) ? "#3d4a28" : "#16201b";
        label = eventCells.has(c.i) ? "事" : py(rec.stock[idx], 0);
        title += eventCells.has(c.i) ? " · 本年有可核实事件" : " · 本年无事件";
      } else {
        fill = ramp(capv ? rec.stock[idx] / capv : 0);
        label = py(rec.stock[idx], 0);
        title += " · 食物 " + py(rec.stock[idx], 1) + " 人年口粮";
        if (capv) title += " · 容量 " + Math.round(rec.stock[idx] / capv * 100) + "%（次要）";
      }
      title += " · 格子编号 " + c.i;
    } else title += " · 不可通行";
    const selected = S.selCell === c.i;
    const hovered = S.hoverCell === c.i;
    const hot = eventCells.has(c.i) && (layer === "event" || layer === "flow");
    const stroke = selected ? "#f3deaa" : hovered ? "#e6c888" : (hot ? "#d4b06a" : (S.skin === "console" ? "#2c4a48" : "#2a3530"));
    out += `<path d="${hexPath(cx, cy)}" fill="${fill}" stroke="${stroke}"
        stroke-width="${selected ? 2.8 : hovered ? 2 : hot ? 1.8 : 1}" data-cell="${c.i}" class="cell${hovered ? " hover" : ""}"${selected ? ' filter="url(#glow)"' : ""}>
        <title>${esc(title)}</title></path>`;
    const lod = S.cam.k;
    const showNum = lod >= 1.45 || selected || S.hoverCell === c.i;
    if (c.passable && label && showNum) {
      out += `<text x="${cx}" y="${cy + (sub ? 6 : 12)}" text-anchor="middle" font-size="10"
          fill="#e8eadc" opacity="0.9" pointer-events="none">${esc(label)}</text>`;
      if (sub && lod >= 1.6) out += `<text x="${cx}" y="${cy + 18}" text-anchor="middle" font-size="8"
          fill="#d4b06a" pointer-events="none">${esc(sub)}</text>`;
    }
  });

  const bandPos = {};
  S.map.cells.forEach((c) => {
    const list = byCell[c.i]; if (!list) return;
    const xy = cellCenter(c), cx = xy[0], cy = xy[1];
    const n = list.length;
    const rCap = (48 - 2 * (n - 1)) / (2 * n);
    const rads = list.map((b) =>
      Math.min(rCap, Math.max(6, 4.2 + Math.sqrt(Math.max(b.size, 1)) * 1.35)));
    const total = rads.reduce((a, r) => a + 2 * r, 0) + (n - 1) * 2;
    let x0 = cx - total / 2;
    list.forEach((b, k) => {
      const rad = rads[k];
      const x = x0 + rad, y = cy - 10;
      x0 += 2 * rad + 2;
      bandPos[String(b.id)] = [x, y, c.i];
      const on = S.selBand === b.id;
      const lodB = S.cam.k;
      if (S.skin === "console") {
        const d = rad * 0.92;
        const fillC = on ? "#8fd4d0" : "#3d7a76";
        const strokeC = on ? "#d7f4f2" : "#99e0dd";
        out += `<polygon points="${x},${(y-d).toFixed(1)} ${(x+d).toFixed(1)},${y} ${x},${(y+d).toFixed(1)} ${(x-d).toFixed(1)},${y}"
            fill="${fillC}" stroke="${strokeC}" stroke-width="${on ? 2.4 : 1.3}"
            data-band="${b.id}" class="band" style="cursor:pointer">
            <title>${esc(b.name)} · ${b.size}人</title></polygon>`;
      } else {
        out += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${rad.toFixed(1)}"
            fill="${on ? "#e8a04a" : "#c47a3a"}" fill-opacity="0.95"
            stroke="${on ? "#f3deaa" : "#f6e7c8"}" stroke-width="${on ? 2.6 : 1.4}"
            data-band="${b.id}" class="band" style="cursor:pointer"${on ? ' filter="url(#glow)"' : ""}>
            <title>${esc(b.name)} · ${b.size}人</title></circle>`;
      }
      if (lodB >= 0.95 && rad >= 7) {
        out += `<text x="${x.toFixed(1)}" y="${(y + 3.2).toFixed(1)}" text-anchor="middle"
            font-size="${rad >= 11 ? 9 : 7.5}" fill="#1a1408" font-weight="700" pointer-events="none">${b.size}人</text>`;
      }
      if (lodB >= 1.7) {
        out += `<text x="${x.toFixed(1)}" y="${(y - rad - 4).toFixed(1)}" text-anchor="middle"
            font-size="8" fill="#f3deaa" pointer-events="none">${esc(b.name)}</text>`;
      }
    });
  });

  if (layer === "flow") {
    const col = { migrate: "#d4b06a", share: "#6eb8b4", aid: "#6fb37c", split: "#7aa7d8" };
    (rec.events || []).forEach((e) => {
      let a, b;
      if (e.type === "migrate" && e.from != null && e.to != null) {
        a = cellCenter(S.map.cells[e.from]); b = cellCenter(S.map.cells[e.to]);
      } else if (e.type === "share" || e.type === "aid") {
        const endCells = {};
        Object.keys(bandPos).forEach((id) => { endCells[id] = bandPos[id][2]; });
        const anc = OverviewLogic.flowAnchor(e, endCells);
        const stroke = e.repay ? "#f3deaa" : (col[e.type] || "#6fb37c");
        const eid = e.id != null ? String(e.id) : "";
        if (!anc || anc.kind === "unrecorded") {
          return;
        }
        const cell = S.map.cells[anc.cell];
        if (!cell) return;
        const xy = cellCenter(cell);
        const attrs = `data-event-id="${esc(eid)}" data-event-cell="${anc.cell}" data-event-type="${esc(e.type)}"`;
        if (anc.kind === "arc") {
          a = bandPos[String(e.donor)]; b = bandPos[String(e.receiver)];
          const x = a[0], y = a[1] - (e.repay ? 20 : 16);
          out += `<path ${attrs} d="M${a[0].toFixed(1)},${a[1].toFixed(1)} Q${x.toFixed(1)},${y} ${b[0].toFixed(1)},${b[1].toFixed(1)}"
            class="flow-line${e.repay ? " repay-flow" : ""}" stroke="${stroke}" stroke-width="${e.repay ? 2.2 : 1.6}"/>`;
        } else {
          out += `<g class="flow-mark" ${attrs}>
            <circle cx="${xy[0].toFixed(1)}" cy="${(xy[1] - 6).toFixed(1)}" r="5.5" fill="${stroke}" stroke="#f3deaa" stroke-width="1.2"/>
            <title>${esc(TYPE_LABEL(e.type))}记录在第 ${anc.cell} 号格；年末群体位置不是事件地点，不把线画到年末格。</title>
          </g>`;
        }
        return;
      } else if (e.type === "split" || e.type === "extinct") {
        return;
      }
      if (!a || !b) return;
      if (e.type === "aid" || e.type === "share") return;
      const eid = e.id != null ? String(e.id) : "";
      out += `<line data-event-id="${esc(eid)}" x1="${a[0].toFixed(1)}" y1="${a[1].toFixed(1)}" x2="${b[0].toFixed(1)}" y2="${b[1].toFixed(1)}"
        class="flow-line" stroke="${col[e.type] || "#d4b06a"}"/>`;
    });
  }

  svg.innerHTML = out;
  S._mapYear = S.t;
  S._mapRun = S.run ? S.run.run_id : null;
  paintDirectorFx();
  svg.querySelectorAll(".band").forEach((n) =>
    n.addEventListener("click", (e) => {
      e.stopPropagation();
      if (S._ignoreClickUntil && performance.now() < S._ignoreClickUntil) return;
      selectBand(n.dataset.band, { force: true });
    }));
  svg.querySelectorAll(".cell").forEach((n) => {
    n.addEventListener("click", () => {
      if (S._ignoreClickUntil && performance.now() < S._ignoreClickUntil) return;
      S.selCell = +n.dataset.cell; S.selBand = null; showRail("dossier"); renderMap(); renderSide();
    });
    n.addEventListener("pointerenter", () => {
      const c = +n.dataset.cell;
      if (S.hoverCell === c) return;
      S.hoverCell = c;
      n.classList.add("hover");
    });
    n.addEventListener("pointerleave", () => {
      if (S.hoverCell === +n.dataset.cell) S.hoverCell = null;
      n.classList.remove("hover");
    });
  });

  const keys = {
    resource: "资源层：绿色深浅 = 野外食物（人年口粮）。灰斜纹 = 不可通行。",
    pop: "人口层：颜色按本格在世人口。圆点仍是各个群体。",
    store: "储粮层：颜色按本格群体储粮合计。",
    mem: memBand ? ("记忆层（" + memBand.name + "）：未知格标灰，时间戳如实显示。") : "记忆层：先点一个群体。",
    event: "事件层：金色描边的格子本年有可核实事件。",
    flow: "流向层：只画同格事实。金=迁移，青=信息交换，绿=援助，亮金=回助。不补编跨格路线。",
  };
  if ($("legend")) $("legend").innerHTML = `<span class="bar"></span> ${esc(keys[layer] || keys.resource)}`;
  if ($("maphint")) {
    $("maphint").textContent = memBand
      ? "记忆视图只替换资源读数；群体位置仍是世界真实位置。没有时间戳显示「时间未记录」。"
      : "滚轮缩放，拖拽平移。点圆点看群体，点格子看地形。";
  }
  if ($("map-key")) {
    $("map-key").textContent = "圆点是群体，数字是人口。" + (keys[layer] || "");
  }
}

function bandName(rec, id) {
  const b = (rec.bands || []).find((x) => String(x.id) === String(id));
  return b ? b.name : (String(id).slice(0, 8) + "…");
}
function yearFromEventId(eid) {
  return DirectorLogic.yearFromEventId(eid);
}
function renderAidMemory(b, rec) {
  const mem = b.aid_memory;
  if (mem == null) {
    return `<div class="muted" style="margin-top:8px">援助记忆：未记录。此引擎或此年没有 aid_memory 字段。</div>`;
  }
  const keys = Object.keys(mem);
  if (!keys.length) {
    return `<div class="muted" style="margin-top:8px">援助记忆：空。没有谁帮助过这个群体。</div>`;
  }
  const rows = keys.map((id) => {
    const e = mem[id] || {};
    const shown = DirectorLogic.displayYearFromMemory(e);
    const last = shown.year == null ? (shown.note || "时间未记录") : ("最近第 " + shown.year + " 年");
    const jump = shown.year == null
      ? `<span>${esc(bandName(rec, id))}</span>`
      : `<button type="button" class="prior-jump" data-prior-year="${shown.year}"${shown.eventId ? ` data-prior-id="${esc(shown.eventId)}"` : ""}>${esc(bandName(rec, id))}</button>`;
    return `<div class="mem-row">${jump}
      累计 ${nf(e.kcal)} kcal（${py(e.kcal)} 人年口粮）· ${esc(last)}</div>`;
  }).join("");
  return `<h4 class="subh">谁帮助过我</h4>
    <p class="muted">只由实际转移累加，不是好感、债务或联盟。</p>${rows}`;
}
function renderRecipCompare(rec, cell) {
  if (!rec.recip || !Array.isArray(rec.recip.compare) || !rec.recip.compare.length) return "";
  const hits = rec.recip.compare.filter((c) => c && (cell == null || c.cell === cell));
  if (!hits.length) return "";
  return `<h4 class="subh">同状态分配对照</h4>` + hits.map((c) => {
    const ch = c.changed ? "开/关优先回助后，这一格的分配不同" : "开/关优先回助后，这一格的分配相同";
    const withN = Array.isArray(c.with_totals) ? c.with_totals.length : 0;
    const withoutN = Array.isArray(c.without_totals) ? c.without_totals.length : 0;
    return `<div class="compare-row">${esc(ch)}（第 ${c.cell} 号格；开启 ${withN} 对 / 关闭 ${withoutN} 对）。这是规则是否起作用的证据，不是 repay 笔数。</div>`;
  }).join("");
}

/* ---------------- 侧栏 ---------------- */
function renderSide() {
  const rec = recNow();
  if (!S.run) {
    $("side-empty").hidden = false;
    $("side-empty").textContent = "还没有选中任何运行。";
    $("side-body").hidden = true;
    return;
  }
  if (!rec) {
    $("side-empty").hidden = false;
    $("side-empty").textContent = yearWaitMessage();
    $("side-body").hidden = true;
    return;
  }
  $("side-empty").hidden = true;
  $("side-body").hidden = false;
  $("side-year").textContent = S.t;
  document.querySelectorAll("#band-scope [data-scope]").forEach((b) =>
    b.classList.toggle("on", b.dataset.scope === S.bandScope));
  if ($("band-scope-note")) {
    $("band-scope-note").textContent = S.bandScope === "full"
      ? "全档案含该年之后才发生的轨迹。导演回放请用截至当前回放年。"
      : "只用第 0.." + S.t + " 年已保存的记录；之后的出生/迁移/分裂/消失不计入。";
  }
  const y = rec.year, cum = rec.cum, agg = rec.agg;
  const rows = [
    ["总人口", `${nf(agg.pop)} <small>人</small>`],
    ["群体数", `${nf(agg.bands)} <small>个</small>`],
    ["野外食物", kcalCell(agg.stock_total)],
    ["群体储粮", kcalCell(agg.store_total)],
    ["当年出生", `${nf(y.births_cum)} <small>人</small>`],
    ["当年原规则死亡", `${nf(y.deaths_demo_cum)} <small>人</small>`],
    ["当年迁移死亡", `${nf(y.mig_deaths_cum)} <small>人</small>`],
    ["当年迁移（账本）", `${nf(y.mig_total)} <small>次</small>`],
    ["当年缺粮 / 需求", pct(y.deficit_cum, y.need_cum)],
    ["当年迁移误判率", y.mig_total ? pct(y.mig_regret, y.mig_total, 1)
      : `<span class="na">不适用（当年迁移 0 次）</span>`],
  ];
  if (rec.share) {
    rows.push(["本年信息交换采纳", `${nf(rec.share.adopted)} <small>条</small>`]);
    rows.push(["本年信息交换拒绝", `${nf(rec.share.rejected)} <small>条</small>`]);
    rows.push(["决策因交换而改变", rec.share.decision_changed == null
      ? `<span class="na">未记录</span>` : `${nf(rec.share.decision_changed)} <small>次</small>`]);
  }
  if (rec.aid) {
    rows.push(["援助活动次数", `${nf(rec.aid.events)} <small>次（格×年）</small>`]);
    rows.push(["逐笔转移", `${nf(rec.aid.transfers)} <small>笔</small>`]);
    rows.push(["本年援助食物", kcalCell(rec.aid.kcal)]);
  }
  if (rec.recip) {
    rows.push(["回助（含碰巧）", `${nf(rec.recip.repay_transfers)} <small>笔</small>`]);
    rows.push(["优先阶段转移", `${nf(rec.recip.transfers)} <small>笔</small>`]);
    rows.push(["分配被规则改变", `${nf(rec.recip.changed)} <small>次（格×年）</small>`]);
  }
  $("side-now").innerHTML = rows.map(([k, v]) =>
    `<div class="k">${k}</div><div class="v">${v}</div>`).join("");
  const crows = [
    ["累计出生", `${nf(cum.births_cum)} <small>人</small>`],
    ["累计原规则死亡", `${nf(cum.deaths_demo_cum)} <small>人</small>`],
    ["累计迁移死亡", `${nf(cum.mig_deaths_cum)} <small>人</small>`],
    ["累计迁移（账本）", `${nf(cum.mig_total)} <small>次</small>`],
    ["累计缺粮 / 需求", pct(cum.deficit_cum, cum.need_cum)],
    ["累计人年", `${nf(cum.personyear_cum)} <small>人年</small>`],
    ["累计吃掉", kcalCell(cum.out_eat)],
    ["累计腐损", kcalCell(cum.out_spoil)],
  ];
  if (rec.aid) {
    crows.push(["累计援助活动", `${nf(rec.aid.cum_events)} <small>次（格×年）</small>`]);
    crows.push(["累计逐笔转移", `${nf(rec.aid.cum_transfers)} <small>笔</small>`]);
    crows.push(["累计援助食物", kcalCell(rec.aid.cum_kcal)]);
  }
  if (rec.recip) {
    crows.push(["累计回助（含碰巧）", `${nf(rec.recip.cum_repay_transfers)} <small>笔</small>`]);
    crows.push(["累计分配改变", `${nf(rec.recip.cum_changed)} <small>次</small>`]);
  }
  $("side-cum").innerHTML = crows.map(([k, v]) =>
    `<div class="k">${k}</div><div class="v">${v}</div>`).join("");
  const ok = (v) => v === 0 ? `<span style="color:var(--ok)">0 ✓</span>` : `<span class="err">${v} ✗</span>`;
  $("side-int").innerHTML =
    `<div class="k">能量守恒误差</div><div class="v">${ok(rec.integrity.conservation_error)}</div>
     <div class="k">人口恒等误差</div><div class="v">${ok(rec.integrity.population_identity_error)}</div>
     ${rec.integrity.aid_ledger_error != null
       ? `<div class="k">援助账误差</div><div class="v">${ok(rec.integrity.aid_ledger_error)}</div>` : ""}
     ${rec.integrity.aid_memory_error != null
       ? `<div class="k">援助记忆误差</div><div class="v">${ok(rec.integrity.aid_memory_error)}</div>` : ""}
     <div class="k">状态哈希</div><div class="v"><small>${esc(rec.integrity.state_hash.slice(0, 16))}…</small></div>`;

  const selWrap = $("side-sel"), h = $("side-sel-h");
  if (S.selCell !== null && S.selBand === null) {
    const c = S.map.cells[S.selCell];
    const here = rec.bands.filter((b) => b.cell === S.selCell);
    h.hidden = false; h.textContent = "选中格子";
    const capv = S.meta ? S.meta.cap[S.selCell] : null;
    const pctCap = capv ? Math.round(rec.stock[S.selCell] / capv * 100) + "%" : "容量未记录";
    selWrap.innerHTML = `<div class="kv">
      <div class="k">位置</div><div class="v">第 ${c.row} 行 第 ${c.col} 列 · 区块 ${esc(c.region)}</div>
      <div class="k">格子编号</div><div class="v">${c.i} <small>（次要）</small></div>
      <div class="k">可通行</div><div class="v">${c.passable ? "是" : "否（屏障列）"}</div>
      <div class="k">食物</div><div class="v">${kcalCell(rec.stock[S.selCell])}</div>
      <div class="k">容量（次要）</div><div class="v">${S.meta ? kcalCell(capv) + " · " + pctCap : "未记录"}</div>
      <div class="k">年再生基准</div><div class="v">${S.meta ? kcalCell(S.meta.regen[S.selCell]) : "未记录"}</div>
      </div>
      <p class="muted">格子上的食物是野外存量，不能据此说某个群体一定能活多少年。</p>
      <div>格上群体：${here.length
        ? here.map((b) => `<span class="link" data-b="${esc(b.id)}">${esc(b.name)}（${b.size}人）</span>`).join("　")
        : "无"}</div>`;
    selWrap.querySelectorAll("[data-b]").forEach((n) =>
      n.addEventListener("click", () => selectBand(n.dataset.b)));
    return;
  }
  if (!S.selBand) { h.hidden = true; selWrap.innerHTML = ""; return; }
  const b = rec.bands.find((x) => x.id === S.selBand);
  h.hidden = false;
  if (!b) {
    h.textContent = "历史群体";
    selWrap.innerHTML = directorLineageHtml() +
      `<div class="gone-note">该群体在第 ${S.t} 年不在世，不把它画在地图上。
      下面是已保存的历史记录，不是当前地图上的位置。</div>
      <div id="bandmore" class="muted" style="margin-top:8px">正在读取历史记录…</div>`;
    bindDirectorLineage(selWrap);
    loadBand(S.selBand);
    return;
  }
  h.textContent = "选中群体";
  const known = Object.keys(b.mem).length;
  selWrap.innerHTML = directorLineageHtml() + `<div class="kv">
    <div class="k">名称</div><div class="v">${esc(b.name)}</div>
    <div class="k">人口</div><div class="v">${nf(b.size)} <small>人</small></div>
    <div class="k">储粮</div><div class="v">${kcalCell(b.store)}</div>
    <div class="k">所在位置</div><div class="v">第 ${b.cell} 号格（区块 ${esc(S.map.cells[b.cell].region)}）</div>
    <div class="k">记忆条目</div><div class="v">${known} <small>格</small></div>
    <div class="k">实体 id</div><div class="v"><small>${esc(String(b.id))}</small></div>
  </div>
  ${renderAidMemory(b, rec)}
  ${renderRecipCompare(rec, b.cell)}
  <div id="bandmore" class="muted" style="margin-top:8px">正在读取轨迹…</div>`;
  selWrap.querySelectorAll(".prior-jump").forEach((n) => {
    n.addEventListener("click", (e) => {
      e.preventDefault(); e.stopPropagation();
      const y = +n.dataset.priorYear;
      if (Number.isFinite(y)) gotoYear(y);
    });
    n.addEventListener("pointerdown", (e) => e.stopPropagation());
  });
  bindDirectorLineage(selWrap);
  loadBand(b.id);
}

function aidEventButtons(list) {
  return (list || []).map((e) => {
    const y = e.year != null ? e.year : DirectorLogic.yearFromEventId(e.id);
    const ph = e.phase === "recip" ? "优先阶段" : "普通援助";
    const rp = e.repay ? " · 回助" : "";
    const lab = (y == null ? "年份未记录" : ("第 " + y + " 年")) + " · " + ph + rp + " · " + nf(e.kcal) + " kcal";
    if (y == null || !e.id) return `<div class="muted">${esc(lab)}</div>`;
    return `<button type="button" class="prior-jump" data-prior-year="${y}" data-prior-id="${esc(e.id)}">${esc(lab)}</button>`;
  }).join(" ");
}
function applyBandDossier(d) {
  S.band = d;
  const box = $("bandmore"); if (!box) return;
  const scope = d.history_scope || {};
  const atY = scope.mode === "as_of_year" ? scope.at_year : null;
  const future = NetworkLogic.futureSteps(d.trajectory, atY);
  const scopeLine = scope.mode === "as_of_year"
    ? ("档案口径：截至第 " + scope.at_year + " 年。" + (scope.note ? " " + scope.note : ""))
    : ("档案口径：全档案。" + (scope.note ? " " + scope.note : "含该年之后发生的事。"));
  const ends = NetworkLogic.migrateEndpoints(d.trajectory);
  const mig = ends.length
    ? ends.map((m) => `第${m.fromYear}年 ${m.from}号格 → 第${m.toYear}年 ${m.to}号格（端点，路线未记录）`).join("；")
    : "无记录的位置变化";
  const spark = NetworkLogic.sparkPath(d.sizes, 220, 32);
  const sparkSvg = spark
    ? `<svg class="spark" viewBox="0 0 220 32" aria-label="人口曲线"><path d="${spark}" fill="none" stroke="#6fb37c" stroke-width="1.6"/></svg>`
    : `<span class="muted">人口曲线未记录</span>`;
  const parent = d.parent
    ? `<button type="button" class="prior-jump" data-b="${esc(String(d.parent))}">父群体 ${esc(String(d.parent))}</button>`
    : "无记录";
  const kids = (d.children && d.children.length)
    ? d.children.map((p) => `<button type="button" class="prior-jump" data-b="${esc(String(p[1]))}">第${p[0]}年 ${esc(String(p[1]))}</button>`).join(" ")
    : "无记录";
  const given = d.aid_given || {};
  const recv = d.aid_received || {};
  const gone = d.extinct_at !== null ? `（第 ${d.extinct_at} 年被移除）` : "";
  const st = d.state_at_year;
  const stateLine = st
    ? ("截至该年：第 " + st.year + " 年 · " + nf(st.size) + " 人 · " + st.cell + " 号格 · 储粮 " + nf(st.store) + " kcal")
    : "截至该年的状态未记录";
  box.innerHTML = `<div class="muted">${esc(scopeLine)}</div>
    <div class="muted">${future.length ? "此口径不含未来轨迹。" : (scope.mode === "full" ? "全档案含该年之后的轨迹。" : "")}</div>
    <div><b>来源</b>：${esc(d.origin || "未记录")}${d.born_at != null ? " · 第 " + d.born_at + " 年出现" : ""}</div>
    <div><b>存续</b>：第 ${d.first_seen} 年 至 第 ${d.last_seen} 年 ${gone}</div>
    <div><b>谱系</b>：${parent} → 本群体 → ${kids}</div>
    <div><b>人口曲线</b> ${sparkSvg}</div>
    <div><b>移动端点</b>：${esc(mig)}</div>
    <div class="muted">${esc(stateLine)}</div>
    <h4 class="subh">援助往来（不是盟友）</h4>
    <div>给出：${nf(given.transfers || 0)} 笔 · ${nf(given.kcal || 0)} kcal</div>
    <div class="dir-related">${aidEventButtons(given.events)}</div>
    <div>收到：${nf(recv.transfers || 0)} 笔 · ${nf(recv.kcal || 0)} kcal</div>
    <div class="dir-related">${aidEventButtons(recv.events)}</div>
    <details><summary>原始 id 与轨迹数组</summary>
      <div class="muted">id=${esc(String(d.id))}</div>
      <div class="muted">${esc(JSON.stringify(d.trajectory || []))}</div>
      <div>${esc(d.source || "")}</div>
    </details>`;
  box.querySelectorAll("[data-b]").forEach((n) => {
    n.addEventListener("click", (e) => {
      e.preventDefault();
      selectBand(n.dataset.b, { force: true, keepCell: true, rail: "dossier" });
    });
  });
  box.querySelectorAll(".prior-jump[data-prior-year]").forEach((n) => {
    n.addEventListener("click", (e) => {
      e.preventDefault();
      jumpToRecordedEvent(n.dataset.priorId, n.dataset.priorYear);
    });
  });
}
function bandScopeMatches(d, scope, year) {
  const hs = d && d.history_scope;
  if (!hs || !hs.mode) return true;
  if (scope === "full") return hs.mode === "full";
  return hs.mode === "as_of_year" && (hs.at_year == null || hs.at_year === year);
}
async function loadBand(id) {
  if (!S.run) return { ok: false, reason: "no-run" };
  const myRun = S.run.run_id, myEpoch = S.epoch, myBand = id;
  const myScope = S.bandScope === "full" ? "full" : "as_of";
  const myYear = S.t;
  const myReq = ++S.bandReqGen;
  const key = bandCacheKey(myRun, myBand, myScope, myYear);
  const accept = () => bandAccept(myEpoch, myRun, myBand, myScope, myYear, myReq);
  const cached = S.bandCache.get(key);
  if (cached && accept()) applyBandDossier(cached);
  const q = myScope === "full" ? "" : ("?at_year=" + myYear);
  try {
    const d = await api(`/api/runs/${myRun}/band/${id}` + q);
    if (!accept()) return { ok: false, reason: "stale" };
    if (!bandScopeMatches(d, myScope, myYear)) return { ok: false, reason: "scope-mismatch" };
    S.bandCache.set(key, d);
    if (!accept()) return { ok: false, reason: "stale" };
    applyBandDossier(d);
    return { ok: true };
  } catch (e) {
    if (!accept()) return { ok: false, reason: "stale" };
    const box = $("bandmore");
    if (!box) return { ok: false, reason: e.message };
    if (e.status === 404 && myScope !== "full") {
      box.innerHTML = `<span class="muted">截至第 ${myYear} 年的记录里没有这个群体。不把它画在当年地图上，也不用后来的位置补。</span>`;
    } else {
      box.innerHTML = `<span class="err">轨迹读取失败：${esc(e.message)}</span>`;
    }
    return { ok: false, reason: e.message };
  }
}

function renderLibrary() {
  const boxY = $("lib-years"), boxE = $("lib-events");
  if (!boxY || !boxE) return;
  if (!S.run) { boxY.textContent = "先打开一次运行。"; boxE.textContent = ""; return; }
  const all = LibraryLogic.loadAll();
  const lib = LibraryLogic.forRun(all, S.run.run_id);
  boxY.innerHTML = lib.years.length
    ? lib.years.map((t) => `<button type="button" class="prior-jump" data-y="${t}">第 ${t} 年</button>`).join(" ")
    : "无";
  boxE.innerHTML = lib.events.length
    ? lib.events.map((e) => `<button type="button" class="prior-jump" data-eid="${esc(e.id)}" data-y="${e.t}">${esc(e.id)}</button>`).join(" ")
    : "无";
  boxY.querySelectorAll("[data-y]").forEach((n) => n.addEventListener("click", () => {
    bumpOp();
    gotoYear(+n.dataset.y, { opGen: S.opGen });
  }));
  boxE.querySelectorAll("[data-eid]").forEach((n) => n.addEventListener("click", () => {
    jumpToRecordedEvent(n.dataset.eid, n.dataset.y);
  }));
}
function pinCurrentYear() {
  if (!S.run) return;
  const all = LibraryLogic.pinYear(LibraryLogic.loadAll(), S.run.run_id, S.t);
  LibraryLogic.saveAll(all);
  renderLibrary();
}
function pinCurrentEvent() {
  if (!S.run || !S.selEvent) { flash("先选中一条事件。", true); return; }
  const ev = findEventByKey(S.selEvent, S.t) || { id: S.selEvent, t: S.t };
  const all = LibraryLogic.pinEvent(LibraryLogic.loadAll(), S.run.run_id, ev);
  LibraryLogic.saveAll(all);
  renderLibrary();
}
function exportCurrentRecord() {
  if (!S.run) { flash("没有打开的运行。", true); return; }
  const rec = recNow();
  const payload = LibraryLogic.exportRecord(S.run, S.t, rec, {
    summary: ($("year-summary") && $("year-summary").textContent) || "",
    selEvent: S.selEvent || "",
    selBand: S.selBand || "",
  });
  if (LibraryLogic.hasForbidden(payload)) { flash("导出被拦截：含禁止字段。", true); return; }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "obs-" + S.run.run_id + "-t" + S.t + ".json";
  a.click();
}
function relContextKey() {
  const run = S.run ? S.run.run_id : "";
  const scope = S.bandScope === "full" ? "full" : "as_of";
  return run + "|" + S.t + "|" + scope;
}
function clearRelEdgeCard() {
  S.relSel = null;
  const card = $("net-edge-card");
  if (card) { card.hidden = true; card.innerHTML = ""; }
}
function fillRelEdgeCard(e, nodes) {
  const card = $("net-edge-card");
  if (!card || !e) { clearRelEdgeCard(); return; }
  const nrm = (e.phase_counts && e.phase_counts.normal) || 0;
  const recp = (e.phase_counts && e.phase_counts.recip) || 0;
  const dn = NetworkLogic.nodeName(nodes, e.donor);
  const rn = NetworkLogic.nodeName(nodes, e.receiver);
  const evs = (e.event_ids || []).map((id) => {
    const y = DirectorLogic.yearFromEventId(id);
    return y == null ? esc(id)
      : `<button type="button" class="prior-jump" data-prior-year="${y}" data-prior-id="${esc(id)}">${esc(id)}</button>`;
  }).join(" ");
  card.hidden = false;
  card.innerHTML = `<div class="dir-title">有向往来 · ${esc(dn)} → ${esc(rn)}</div>
    <div class="dir-meta">${nf(e.transfers)} 笔 · ${nf(e.kcal)} kcal · 普通 ${nrm} · 优先阶段 ${recp} · 回助 ${nf(e.repay_transfers || 0)}</div>
    <div class="dir-meta">最近 ${e.last_year != null ? ("第 " + e.last_year + " 年") : "未记录"} · 事件 ${evs || "未记录"}</div>
    <details><summary>原始 id</summary><div class="muted">${esc(String(e.donor))} → ${esc(String(e.receiver))}</div></details>
    <p class="muted">这不是盟友。A→B 与 B→A 若都存在，是两条边。</p>`;
  card.querySelectorAll(".prior-jump").forEach((b) => b.addEventListener("click", (ev) => {
    ev.preventDefault();
    showTab("world");
    jumpToRecordedEvent(b.dataset.priorId, b.dataset.priorYear);
  }));
}
function relCacheKey(runId, scope, year) {
  return String(runId) + "|rel|" + scope + "|" + (scope === "full" ? "full" : String(year));
}
function relAccept(epoch, runId, scope, year, req) {
  if (stale(epoch, runId)) return false;
  const nowScope = S.bandScope === "full" ? "full" : "as_of";
  if (nowScope !== scope) return false;
  if (scope !== "full" && S.t !== year) return false;
  if (S.relReqGen !== req) return false;
  return true;
}
function renderRelations(d) {
  S.relations = d;
  const ctxKey = relContextKey();
  if (S.relCardKey !== ctxKey) {
    clearRelEdgeCard();
    S.relCardKey = ctxKey;
  }
  const scope = (d && d.history_scope) || {};
  const totals = (d && d.totals) || {};
  const diag = (d && d.diagnostics) || {};
  const nodes = (d && d.nodes) || [];
  const edges = (d && d.edges) || [];
  if (S.relSel != null && !edges[S.relSel]) clearRelEdgeCard();
  if ($("net-scope-pill")) {
    $("net-scope-pill").textContent = scope.mode === "full"
      ? "全档案（含该年之后）"
      : ("截至第 " + (scope.at_year != null ? scope.at_year : S.t) + " 年 · 不含未来");
  }
  if ($("net-totals")) {
    $("net-totals").textContent = "节点 " + (totals.nodes || 0) + " · 有向边 " + (totals.edges || 0) +
      " · 转移 " + (totals.transfers || 0) + " 笔 · " + nf(totals.kcal || 0) + " kcal";
  }
  if ($("net-note")) {
    $("net-note").textContent = "有向边：A→B 与 B→A 分开。普通援助 / 优先阶段 / 回助笔数分列。" +
      "分配改变 " + (diag.recip_changed_cellyears != null ? diag.recip_changed_cellyears : "未记录") +
      " 次（格×年），不属于任何一条边。布局不是地理位置。";
  }
  if ($("rel-rail-summary")) {
    $("rel-rail-summary").textContent = (scope.mode === "full" ? "全档案" : ("截至第 " + S.t + " 年")) +
      "：有向边 " + (totals.edges || 0) + "，转移 " + (totals.transfers || 0) + " 笔。不是盟友或国家。";
  }
  if ($("net-year") && document.activeElement !== $("net-year")) $("net-year").value = String(S.t);
  const svg = $("net-svg");
  if (svg) {
    const W = 720, H = 420;
    const laid = NetworkLogic.layoutCircle(nodes, W, H);
    const byId = {};
    laid.forEach((p) => { byId[p.id] = p; });
    let out = "";
    edges.forEach((e, i) => {
      const a = byId[String(e.donor)], b = byId[String(e.receiver)];
      if (!a || !b) return;
      const kind = NetworkLogic.pairKind(edges, e.donor, e.receiver);
      const sign = NetworkLogic.edgeBendSign(edges, e.donor, e.receiver);
      const mag = kind === "two-way" ? 38 : 14;
      const c = NetworkLogic.quadControl(a.x, a.y, b.x, b.y, sign, mag);
      const repay = (e.repay_transfers || 0) > 0;
      const d = `M${a.x.toFixed(1)},${a.y.toFixed(1)} Q${c.x.toFixed(1)},${c.y.toFixed(1)} ${b.x.toFixed(1)},${b.y.toFixed(1)}`;
      const cls = "net-edge " + kind + (repay ? " repay" : "") + (S.relSel === i ? " on" : "");
      out += `<path class="net-edge-hit" data-ei="${i}" d="${d}" fill="none"/>`;
      out += `<path class="${cls}" data-ei="${i}" d="${d}" fill="none"
        stroke-width="${S.relSel === i ? 2.6 : 1.8}" marker-end="url(#arr)" pointer-events="none"/>`;
      out += `<circle class="net-edge-hit net-edge-knob" data-ei="${i}" cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="11"
        fill="${S.relSel === i ? "#e8a04a" : "rgba(212,176,106,.55)"}" stroke="#f3deaa" stroke-width="1.2"/>`;
    });
    out = `<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6" fill="#d4b06a"/></marker></defs>` + out;
    laid.forEach((p) => {
      const on = S.selBand && String(S.selBand) === p.id;
      const label = p.node.name || p.id.slice(0, 8);
      const tw = Math.max(48, label.length * 7);
      out += `<g class="net-node" data-b="${esc(p.id)}" tabindex="0" role="button">
        <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${on ? 12 : 10}"
          fill="${on ? "#e8a04a" : (p.node.alive_at_year ? "#6fb37c" : "#5c645c")}" stroke="#f3deaa" stroke-width="${on ? 2 : 1}"/>
        <rect class="net-label-hit" x="${(p.x - tw / 2).toFixed(1)}" y="${(p.y - 28).toFixed(1)}" width="${tw.toFixed(1)}" height="16" fill="transparent"/>
        <text x="${p.x.toFixed(1)}" y="${(p.y - 16).toFixed(1)}" text-anchor="middle" font-size="11" fill="#e8eadc">${esc(label)}</text>
      </g>`;
    });
    svg.innerHTML = out;
    const openNode = (id) => {
      selectBand(id, { force: true, rail: "dossier" });
      showTab("world");
    };
    svg.querySelectorAll(".net-node").forEach((n) => {
      n.addEventListener("click", () => openNode(n.getAttribute("data-b")));
      n.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openNode(n.getAttribute("data-b")); }
      });
    });
    svg.querySelectorAll(".net-edge-hit").forEach((n) => n.addEventListener("click", () => {
      const ei = +n.getAttribute("data-ei");
      S.relSel = ei;
      fillRelEdgeCard(edges[ei], nodes);
      renderRelations(S.relations);
    }));
  }
  const tbl = $("net-table");
  if (tbl) {
    tbl.innerHTML = `<tr><th>供给方</th><th>接收方</th><th>笔数</th><th>kcal</th><th>普通</th><th>优先</th><th>回助</th><th>最近年</th></tr>` +
      edges.map((e) => `<tr data-donor="${esc(String(e.donor))}" data-recv="${esc(String(e.receiver))}">
        <td class="clickable" data-b="${esc(String(e.donor))}">${esc(NetworkLogic.nodeName(nodes, e.donor))}<div class="muted"><small>${esc(String(e.donor))}</small></div></td>
        <td class="clickable" data-b="${esc(String(e.receiver))}">${esc(NetworkLogic.nodeName(nodes, e.receiver))}<div class="muted"><small>${esc(String(e.receiver))}</small></div></td>
        <td>${nf(e.transfers)}</td><td>${nf(e.kcal)}</td>
        <td>${(e.phase_counts && e.phase_counts.normal) || 0}</td>
        <td>${(e.phase_counts && e.phase_counts.recip) || 0}</td>
        <td>${nf(e.repay_transfers || 0)}</td>
        <td>${e.last_year != null ? e.last_year : "未记录"}</td></tr>`).join("");
    tbl.querySelectorAll("[data-b]").forEach((n) => n.addEventListener("click", () => {
      selectBand(n.dataset.b, { force: true, rail: "dossier" });
      showTab("world");
    }));
  }
  if ($("net-raw")) $("net-raw").textContent = JSON.stringify({
    history_scope: scope, totals: totals, diagnostics: diag,
    nodes: nodes.map((n) => n.id),
    edges: edges.map((e) => ({ donor: e.donor, receiver: e.receiver, event_ids: e.event_ids })),
  }, null, 2);
}
async function loadRelations() {
  if (!S.run) return { ok: false, reason: "no-run" };
  const myRun = S.run.run_id, myEpoch = S.epoch;
  const myScope = S.bandScope === "full" ? "full" : "as_of";
  const myYear = S.t;
  const myReq = ++S.relReqGen;
  const key = relCacheKey(myRun, myScope, myYear);
  const accept = () => relAccept(myEpoch, myRun, myScope, myYear, myReq);
  const cached = S.relCache.get(key);
  if (cached && accept()) renderRelations(cached);
  const q = myScope === "full" ? "" : ("?at_year=" + myYear);
  try {
    const d = await api(`/api/runs/${myRun}/relations` + q);
    if (!accept()) return { ok: false, reason: "stale" };
    S.relCache.set(key, d);
    if (!accept()) return { ok: false, reason: "stale" };
    renderRelations(d);
    return { ok: true };
  } catch (e) {
    if (!accept()) return { ok: false, reason: "stale" };
    if ($("rel-rail-summary")) $("rel-rail-summary").textContent = "关系读取失败：" + e.message;
    if ($("net-note")) $("net-note").textContent = "关系读取失败：" + e.message;
    clearRelEdgeCard();
    return { ok: false, reason: e.message };
  }
}

function showRail(name) {
  const tabs = document.querySelectorAll("#rail-tabs button");
  if (!tabs.length) return;
  tabs.forEach((x) => x.classList.toggle("on", x.dataset.rail === name));
  ["chronicle", "dossier", "network", "library", "help"].forEach((n) => {
    const pane = $("pane-" + n); if (!pane) return;
    const on = n === name;
    pane.hidden = !on;
    pane.classList.toggle("on", on);
  });
  if (name === "network") loadRelations();
  if (name === "library") renderLibrary();
}
function selectBand(id, opts) {
  opts = opts || {};
  bump();
  S.band = null;
  if (!opts.force && S.selBand === id) S.selBand = null;
  else S.selBand = id || null;
  setHash({ b: S.selBand || "" });
  if (!opts.keepCell) S.selCell = null;
  if (!S.selBand && S.view === "mem") setView("truth");
  if (S.selBand && opts.rail !== "none") showRail(opts.rail || "dossier");
  if (!opts.skipMap) renderMap();
  renderSide();
}
function setView(v) {
  if (v === "mem" && !S.selBand) { flash("先点一个群体，才能看它记忆里的世界。"); return; }
  S.view = v;
  if (v === "mem") S.layer = "mem";
  else if (S.layer === "mem") S.layer = "resource";
  setHash({ view: v === "mem" ? "mem" : "" });
  if ($("v-truth")) $("v-truth").classList.toggle("on", v === "truth" && S.layer === "resource");
  if ($("v-mem")) $("v-mem").classList.toggle("on", v === "mem");
  document.querySelectorAll("#layers [data-layer]").forEach((b) =>
    b.classList.toggle("on", (v === "mem" && b.dataset.layer === "mem") ||
      (v !== "mem" && b.dataset.layer === S.layer)));
  renderMap();
}

/* ---------------- 时间轴 ---------------- */
function maxT() { return Math.max(0, (S.run ? (S.run.years_recorded ?? 0) : 0)); }
function syncYearWidgets(t) {
  $("scrub").value = t;
  $("scrub-year").textContent = t;
  if ($("ev-year")) $("ev-year").textContent = t;
  $("tl-play").textContent = "正在回放：" + OverviewLogic.yearViewLabel(t);
  if (S.run) {
    $("tl-calc").textContent = "已计算到：第 " + maxT() + " 年 / 目标 " + S.run.years + " 年";
  }
}
function setYearLoadOverlay(t, on) {
  if (on) beginYearLoad(t, S.opGen, S.run ? S.run.run_id : "");
  else if (S.loadOverlay) endYearLoad(S.loadOverlay.gen);
}
function renderYearFailBar() {
  const bar = $("year-fail");
  if (!bar) return;
  const w = S.yearWait;
  if (w && !w.pending) {
    bar.hidden = false;
    if ($("year-fail-text")) {
      $("year-fail-text").textContent = "第 " + w.t + " 年读取失败" +
        (w.message ? "：" + w.message : "") +
        "。可重试。不把其他年份的数字标到这一年。";
    }
  } else {
    bar.hidden = true;
  }
}
function commitYear(t, wait) {
  S.t = t;
  S.yearWait = wait || null;
  if (!wait) S.lastOkT = t;
  syncYearWidgets(t);
  setHash({
    t: String(t),
    mode: S.playMode === "events" ? "events" : "",
    event: S.selEvent || "",
    archive: S.bandScope === "full" ? "full" : "",
  });
  renderDirectorChrome();
  renderYearFailBar();
  loadRelations();
}
function yearNavAlive(myEpoch, myRun, myOp) {
  return opAlive(myOp) && !stale(myEpoch, myRun);
}
function pendingCurrentYear() {
  if (!S.run) return false;
  if (S.years.has(ykey(S.run.run_id, S.t))) return false;
  if (S.playWait && S.playWait.t === S.t && opAlive(S.playWait.op)) return true;
  if (S.yearWait && S.yearWait.pending && S.yearWait.t === S.t) return true;
  return false;
}
function schedulePlayTimer(myOp, ms, fn) {
  if (!S.playing || !opAlive(myOp)) return;
  clearTimeout(S.timer);
  S.timer = setTimeout(() => {
    if (!S.playing || !opAlive(myOp)) return;
    fn();
  }, ms);
}
function afterPlayStep(gy, myOp) {
  if (!opAlive(myOp)) return false;
  if (!gy || gy.kind === "stale") return false;
  if (gy.kind === "pending404") {
    const waitT = gy.t != null ? gy.t : S.t;
    S.playWait = { t: waitT, op: myOp, runId: S.run ? S.run.run_id : null };
    if ($("tl-note")) {
      $("tl-note").textContent = "等待第 " + waitT + " 年落盘，拿到记录前不进入下一年。";
    }
    schedulePlayTimer(myOp, PLAY_PENDING_MS, tick);
    return false;
  }
  if (!gy.ok || gy.kind === "failed") {
    S.playWait = null;
    if (S.playing && opAlive(myOp)) setPlaying(false);
    return false;
  }
  if (S.playWait && (gy.t == null || S.playWait.t === gy.t)) S.playWait = null;
  return true;
}
function retryYear() {
  if (!S.run) return;
  const t = S.yearWait && S.yearWait.t != null ? S.yearWait.t : S.t;
  setPlaying(false);
  bumpOp();
  return gotoYear(t, { opGen: S.opGen });
}
async function gotoYear(t, opts) {
  opts = opts || {};
  if (!S.run) return navResult("failed", { reason: "no-run" });
  const myOp = opts.opGen != null ? opts.opGen : S.opGen;
  if (!opAlive(myOp)) return navResult("stale");
  const myRun = S.run.run_id;
  const myEpoch = bump();
  t = Math.max(0, Math.min(t, maxT()));
  if (!yearNavAlive(myEpoch, myRun, myOp)) return navResult("stale");
  let loadGen = 0;
  const finishOk = () => {
    if (!yearNavAlive(myEpoch, myRun, myOp)) {
      endYearLoad(loadGen);
      return navResult("stale");
    }
    cancelFx({ keepStatic: !!opts.keepEvent && !!S.selEvent });
    if (!opts.keepEvent && S.selEvent) {
      const ey = DirectorLogic.yearFromEventId(S.selEvent);
      if (ey != null && ey !== t) S.selEvent = null;
    }
    endYearLoad(loadGen);
    commitYear(t, null);
    renderOverview(); renderMap(); renderSide(); renderStatus(); renderEvents();
    renderTech();
    if (!opts.quiet) renderCharts();
    if (S.evScope === "until") prefetchYears(myRun, t);
    return navResult("success", { t: t });
  };
  if (S.years.has(ykey(myRun, t))) {
    return finishOk();
  }
  loadGen = beginYearLoad(t, myOp, myRun);
  let rec;
  try { rec = await api(`/api/runs/${myRun}/year/${t}`); }
  catch (e) {
    if (!yearNavAlive(myEpoch, myRun, myOp)) {
      endYearLoad(loadGen);
      return navResult("stale");
    }
    const pending = isPendingYearError(e, t);
    const kind = pending ? "pending404" : "failed";
    endYearLoad(loadGen);
    commitYear(t, {
      runId: myRun, t: t, pending: pending, status: e.status, message: e.message,
    });
    if (!pending) flash("读取第 " + t + " 年失败：" + e.message, true);
    renderOverview(); renderMap(); renderSide(); renderStatus(); renderEvents();
    renderYearFailBar();
    return navResult(kind, { t: t, reason: e.message, status: e.status });
  }
  if (!yearNavAlive(myEpoch, myRun, myOp)) {
    if (!stale(myEpoch, myRun)) {
      S.years.set(ykey(myRun, t), rec);
      delete S.yearMiss[yearMissKey(myRun, t)];
    }
    endYearLoad(loadGen);
    return navResult("stale");
  }
  S.years.set(ykey(myRun, t), rec);
  delete S.yearMiss[yearMissKey(myRun, t)];
  return finishOk();
}
function playDelay() {
  return Math.max(80, (S.playMode === "events" ? 900 : 600) / Math.max(S.speed || 1, 0.25));
}
function tick() {
  if (!S.playing) return;
  const myOp = S.opGen;
  if (pendingCurrentYear()) {
    gotoYear(S.t, { quiet: true, opGen: myOp }).then((gy) => {
      if (!afterPlayStep(gy, myOp)) return;
      if (!S.playing || !opAlive(myOp)) return;
      if (S.playMode === "events") {
        tickEvents();
        return;
      }
      renderCharts();
      schedulePlayTimer(myOp, playDelay(), tick);
    });
    return;
  }
  if (S.playMode === "events") {
    tickEvents();
    return;
  }
  if (S.t >= maxT()) {
    if (S.run && (S.run.status === "running" || S.run.status === "queued")) {
      $("tl-note").textContent = "已经放到最新算出来的一年，等后台继续计算…";
      schedulePlayTimer(myOp, PLAY_PENDING_MS, tick);
      return;
    }
    setPlaying(false); return;
  }
  gotoYear(S.t + 1, { quiet: true, opGen: myOp }).then((gy) => {
    if (!afterPlayStep(gy, myOp)) return;
    renderCharts();
    if (!opAlive(myOp) || !S.playing) return;
    schedulePlayTimer(myOp, playDelay(), tick);
  });
}
function setPlaying(v) {
  const was = S.playing;
  if (!v && was) bumpOp();
  S.playing = v;
  if ($("b-play")) {
    $("b-play").textContent = v ? "⏸ 暂停"
      : (S.playMode === "events" ? "▶ 播放事件" : "▶ 播放");
  }
  if ($("tl-note")) {
    $("tl-note").textContent = v
      ? (S.playMode === "events" ? "按有记录的事件年播放（只读）" : "回放中（只读已保存的记录）")
      : "回放只读取已保存的记录，不会重新计算世界。";
  }
  clearTimeout(S.timer);
  S.timer = null;
  if (!v) cancelFx({ keepStatic: !!S.selEvent });
  if (v) tick();
}

async function prefetchYears(runId, tEnd) {
  const missing = [];
  for (let t = 0; t <= tEnd; t++) {
    if (!S.years.has(ykey(runId, t))) missing.push(t);
  }
  const BATCH = 10;
  for (let i = 0; i < missing.length; i += BATCH) {
    if (!S.run || S.run.run_id !== runId) return;
    const slice = missing.slice(i, i + BATCH);
    await Promise.all(slice.map(async (t) => {
      if (S.years.has(ykey(runId, t))) return;
      try {
        const rec = await api(`/api/runs/${runId}/year/${t}`);
        S.years.set(ykey(runId, t), rec);
        delete S.yearMiss[yearMissKey(runId, t)];
      } catch (e) { /* 保留缺口；refresh 会在记录可用后补当前年 */ }
    }));
    if (S.run && S.run.run_id === runId) {
      renderOverview(); renderEvents();
      if (S.years.has(ykey(runId, S.t))) {
        S.yearWait = null;
        renderMap(); renderSide(); renderTech(); renderStatus();
      }
    }
  }
}

/* ---------------- 曲线 ---------------- */
function lineChart(title, series, key, color, conv) {
  const w = 320, h = 120, pad = 26;
  if (!series.length) return "";
  const vals = [];
  series.forEach((r, i) => {
    const v = key(r);
    if (v === null || v === undefined || Number.isNaN(v)) return;
    vals.push(v);
  });
  if (!vals.length) {
    return `<div class="chart"><h4>${esc(title)}</h4>
      <p class="muted">没有可画的点（分母为 0 或数据缺失，不画成 0%）</p></div>`;
  }
  const mx = Math.max.apply(null, vals.concat([1]));
  const mn = Math.min.apply(null, vals.concat([0]));
  const X = (i) => pad + i * (w - pad - 6) / Math.max(series.length - 1, 1);
  const Y = (v) => h - 18 - (v - mn) / Math.max(mx - mn, 1) * (h - 30);
  let d = "", drawing = false;
  series.forEach((r, i) => {
    const v = key(r);
    if (v === null || v === undefined || Number.isNaN(v)) { drawing = false; return; }
    d += (drawing ? "L" : "M") + X(i).toFixed(1) + "," + Y(v).toFixed(1);
    drawing = true;
  });
  const cx = X(Math.min(S.t, series.length - 1));
  return `<div class="chart"><h4>${esc(title)}</h4>
    <svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto">
      <path d="${d}" fill="none" stroke="${color}" stroke-width="1.8"/>
      <line x1="${cx}" y1="8" x2="${cx}" y2="${h - 18}" stroke="#d4b06a" stroke-dasharray="3 3"/>
      <text x="2" y="14" font-size="9" fill="#8e9688">${esc(String(conv(mx)))}</text>
      <text x="2" y="${h - 20}" font-size="9" fill="#8e9688">${esc(String(conv(mn)))}</text>
      <text x="${pad}" y="${h - 4}" font-size="9" fill="#8e9688">0</text>
      <text x="${w - 20}" y="${h - 4}" font-size="9" fill="#8e9688">${series.length - 1}</text>
    </svg></div>`;
}
function renderCharts() {
  if ($("tab-metrics").hidden) return;
  const s = S.series;
  $("charts").innerHTML =
    lineChart("总人口（人）", s, (r) => r.agg.pop, "#6fb37c", (v) => nf(Math.round(v))) +
    lineChart("群体数（个）", s, (r) => r.agg.bands, "#6eb8b4", (v) => nf(Math.round(v))) +
    lineChart("野外食物（人年口粮）", s, (r) => r.agg.stock_total, "#d4b06a", (v) => py(v, 0)) +
    lineChart("群体储粮（人年口粮）", s, (r) => r.agg.store_total, "#c47a3a", (v) => py(v, 0)) +
    lineChart("当年迁移次数（账本，次）", s, (r) => r.year.mig_total, "#c8a05a", (v) => nf(v)) +
    lineChart("当年迁移死亡（人）", s, (r) => r.year.mig_deaths_cum, "#c45c52", (v) => nf(v)) +
    lineChart("当年缺粮/需求（‰）", s, (r) => r.year.need_cum
      ? Math.round(r.year.deficit_cum / r.year.need_cum * 1000) : null, "#d4b06a", (v) => v + "‰");
  const head = `<tr><th>年</th><th>总人口</th><th>群体数</th><th>野外食物(人年)</th><th>储粮(人年)</th>
    <th>当年出生</th><th>当年原死亡</th><th>当年迁移死亡</th><th>当年迁移(账本)</th><th>当年缺粮/需求</th>
    <th>累计出生</th><th>累计原死亡</th><th>累计迁移死亡</th><th>守恒误差</th></tr>`;
  const rows = s.map((r) => `<tr class="${r.t === S.t ? "on" : ""}" data-t="${r.t}">
    <td class="clickable">${r.t === 0 ? "开局" : r.t}</td><td>${nf(r.agg.pop)}</td><td>${nf(r.agg.bands)}</td>
    <td>${py(r.agg.stock_total, 0)}</td><td>${py(r.agg.store_total, 0)}</td>
    <td>${nf(r.year.births_cum)}</td><td>${nf(r.year.deaths_demo_cum)}</td>
    <td>${nf(r.year.mig_deaths_cum)}</td><td>${nf(r.year.mig_total)}</td>
    <td>${r.year.need_cum ? (r.year.deficit_cum / r.year.need_cum * 100).toFixed(3) + "%" : "不适用"}</td>
    <td>${nf(r.cum.births_cum)}</td><td>${nf(r.cum.deaths_demo_cum)}</td>
    <td>${nf(r.cum.mig_deaths_cum)}</td><td>${r.integrity.conservation_error}</td></tr>`).join("");
  $("yeartable").innerHTML = head + rows;
  $("yeartable").querySelectorAll("tr[data-t]").forEach((n) =>
    n.addEventListener("click", () => gotoYear(+n.dataset.t)));
  $("charts").querySelectorAll(".chart svg").forEach((svg) => {
    svg.style.cursor = "pointer";
    svg.addEventListener("click", (e) => {
      const box = svg.getBoundingClientRect();
      const x = (e.clientX - box.left) / Math.max(box.width, 1);
      const t = Math.round(x * Math.max(S.series.length - 1, 0));
      gotoYear(t);
    });
  });
}

/* ---------------- 事件 ---------------- */
function TYPE_LABEL(t) {
  return ({ migrate: "迁移", split: "分裂", extinct: "群体消失", share: "信息交换", aid: "食物援助" })[t] || t;
}
function renderEvents() {
  const box = $("events");
  if (!box) return;
  const rec = recNow();
  document.querySelectorAll("#ev-scope button").forEach((b) =>
    b.classList.toggle("on", b.dataset.scope === S.evScope));
  document.querySelectorAll("#ev-filter button").forEach((b) =>
    b.classList.toggle("on", b.dataset.type === S.evFilter));

  let items = [];
  let loadNote = "";
  if (!S.run) {
    box.innerHTML = `<div class="emptystate">没有数据</div>`;
    if ($("ev-load-note")) $("ev-load-note").textContent = "";
    if ($("ev-ledger-note")) $("ev-ledger-note").textContent = "";
    return;
  }
  if (S.evScope === "year") {
    if (!rec) {
      box.innerHTML = `<div class="emptystate">${esc(yearWaitMessage())}</div>`;
      if ($("ev-load-note")) $("ev-load-note").textContent = "本年事件清单尚未加载，不把空清单当成 0 条事件。";
      if ($("ev-ledger-note")) $("ev-ledger-note").textContent = "";
      return;
    }
    items = (rec.events || []).map((e, i) => Object.assign({}, e, { t: S.t, _i: i }));
  } else {
    const flat = OverviewLogic.flattenEvents(
      (runId, t) => S.years.get(ykey(runId, t)), S.run.run_id, S.t);
    items = flat.items;
    if (flat.missing.length) {
      const a = flat.missing[0], b = flat.missing[flat.missing.length - 1];
      loadNote = "截至当前年份的清单尚未加载完整（缺 " + flat.missing.length +
        " 年，约第 " + a + "–" + b + " 年）。下面只列出已加载年份，不是最终总数。";
      prefetchYears(S.run.run_id, S.t);
    } else {
      loadNote = "已加载开局至" + OverviewLogic.yearViewLabel(S.t) + "的全部事件清单。";
    }
  }
  if ($("ev-load-note")) {
    $("ev-load-note").textContent = loadNote
      ? loadNote + " " + DirectorLogic.orderNote
      : DirectorLogic.orderNote;
  }

  const filtered = S.evFilter === "all" ? items
    : S.evFilter === "repay" ? items.filter((e) => e.type === "aid" && e.repay)
    : items.filter((e) => e.type === S.evFilter);
  if (!filtered.length) {
    box.innerHTML = `<div class="emptystate">${S.evScope === "year"
      ? (S.t === 0 ? "开局" : "第 " + S.t + " 年") + "没有可核实的" +
        (S.evFilter === "all" ? "迁移、分裂、群体消失、信息交换或食物援助"
          : S.evFilter === "repay" ? "回助" : TYPE_LABEL(S.evFilter)) + "事件。"
      : "已加载范围内没有符合筛选的事件。"}</div>`;
  } else {
    box.innerHTML = filtered.map((e) => {
      const badges = [];
      if (e.type === "aid" && e.repay) badges.push(`<span class="badge s-wait">回助</span>`);
      if (e.phase === "recip") badges.push(`<span class="badge s-run">优先阶段</span>`);
      else if (e.phase === "normal" && e.type === "aid") badges.push(`<span class="badge s-off">普通阶段</span>`);
      let basis = "";
      if (e.basis) {
        const priors = (e.basis.prior_events || []).map((id) => {
          const y = yearFromEventId(id);
          return y == null ? esc(String(id))
            : `<button type="button" class="prior-jump" data-prior-year="${y}" data-prior-id="${esc(id)}">第 ${y} 年原援助</button>`;
        }).join("");
        const shownY = DirectorLogic.displayYearFromBasis(e.basis);
        basis = `<div class="src basis-row">依据：${esc(e.basis.why || "未记录")}` +
          (e.basis.remembered_kcal != null ? ` · 援助前记住 ${nf(e.basis.remembered_kcal)} kcal` : "") +
          (shownY.year == null ? (" · " + (shownY.note || "先前年份未记录")) : ` · 最近受助于第 ${shownY.year} 年`) +
          (priors ? `<div class="prior-row">跳转 ${priors}</div>` : " · 先前事件未记录") + `</div>`;
      }
      const cls = [e.type, e.repay ? "repay" : "", e.phase === "recip" ? "phase-recip" : ""]
        .filter(Boolean).join(" ");
      const ek = DirectorLogic.eventKey(e, e.t, e._i);
      const on = S.selEvent && ek === S.selEvent;
      return `<div class="ev ${esc(cls)}${on ? " on" : ""}" data-t="${e.t}" data-eid="${esc(ek)}"
        data-type="${esc(e.type || "")}" data-band="${esc(e.band || e.receiver || "")}"
        data-parent="${esc(e.parent || "")}" data-donor="${esc(e.donor || "")}"
        data-receiver="${esc(e.receiver || "")}" data-to="${e.to != null ? e.to : ""}"
        data-from="${e.from != null ? e.from : ""}" data-cell="${e.cell != null ? e.cell : ""}">
        <div><span class="when">${e.t === 0 ? "开局" : "第 " + e.t + " 年"}</span>
          ${badges.join(" ")} ${esc(TYPE_LABEL(e.type))} · ${esc(e.text)}</div>
        <div class="src">来源：${esc(e.source || "未标注")}${e.unrecorded
          ? "　·　未记录：" + esc(e.unrecorded) : ""}</div>${basis}
      </div>`;
    }).join("");
    box.querySelectorAll(".ev").forEach((n) => n.addEventListener("click", (ev) => {
      if (ev.target.closest(".prior-jump, .prior-row, [data-prior-year]")) return;
      const found = findEventByKey(n.dataset.eid, +n.dataset.t);
      if (found) focusEvent(found);
      else {
        focusEvent({
          t: +n.dataset.t, id: n.dataset.eid, type: n.dataset.type,
          band: n.dataset.band || null, parent: n.dataset.parent || null,
          donor: n.dataset.donor || null, receiver: n.dataset.receiver || null,
          to: n.dataset.to === "" ? null : +n.dataset.to,
          from: n.dataset.from === "" ? null : +n.dataset.from,
          cell: n.dataset.cell === "" ? null : +n.dataset.cell,
        });
      }
    }));
    box.querySelectorAll(".prior-jump").forEach((n) => {
      const go = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        const y = +n.dataset.priorYear;
        const pid = n.dataset.priorId;
        if (Number.isFinite(y) && pid) jumpToRecordedEvent(pid, y);
        else if (Number.isFinite(y)) { bumpOp(); gotoYear(y, { opGen: S.opGen }); }
      };
      n.addEventListener("click", go);
      n.addEventListener("pointerdown", (e) => { e.stopPropagation(); });
      n.addEventListener("mousedown", (e) => { e.stopPropagation(); });
    });
  }

  if (rec && $("ev-ledger-note")) {
    const listed = OverviewLogic.eventTypeCounts(rec.events).migrate;
    const ledger = rec.year.mig_total;
    if (S.evScope === "year" && ledger !== listed) {
      $("ev-ledger-note").textContent = "模型账本本年迁移 " + ledger +
        " 次；本页可恢复的迁移事件 " + listed + " 条。口径不同，不强行对齐。";
    } else if (S.evScope === "year" && rec.events) {
      $("ev-ledger-note").textContent = "本年账本迁移次数与已记录迁移事件条数一致（" + ledger + "）。出生人数不是事件条数。";
    } else {
      $("ev-ledger-note").textContent = "累计事件只统计当前回放年份及以前。出生人数不等于事件条数。";
    }
    if (rec.aid) {
      const listedAid = OverviewLogic.eventTypeCounts(rec.events).aid;
      $("ev-ledger-note").textContent += " 援助活动 " + rec.aid.events +
        " 次（格×年）；逐笔转移 " + rec.aid.transfers + " 笔；已记录食物援助事件 " +
        listedAid + " 条。活动次数与转移笔数不是同一个计数。";
    }
    if (rec.recip) {
      $("ev-ledger-note").textContent += " 回助（含碰巧） " + rec.recip.repay_transfers +
        " 笔；优先阶段 " + rec.recip.transfers + " 笔；分配被规则改变 " + rec.recip.changed +
        " 次。repay 不是 changed。";
    }
  }

  if (rec) {
    const head = `<tr><th>群体</th><th>人口</th><th>储粮(人年)</th><th>所在格</th><th>区块</th>
                  <th>记忆格数</th></tr>`;
    const q = (($("band-search") && $("band-search").value) || "").trim().toLowerCase();
    const shown = rec.bands.filter((b) => {
      if (!q) return true;
      return String(b.name).toLowerCase().indexOf(q) >= 0 || String(b.id).toLowerCase().indexOf(q) >= 0;
    });
    $("bandtable").innerHTML = head + shown.map((b) => `<tr data-b="${esc(b.id)}"
        class="${S.selBand === b.id ? "on" : ""}"><td class="clickable">${esc(b.name)}</td>
        <td>${nf(b.size)}人</td><td>${py(b.store)}</td><td>${b.cell}</td>
        <td>${esc(S.map.cells[b.cell].region)}</td><td>${Object.keys(b.mem).length}</td></tr>`).join("");
    $("bandtable").querySelectorAll("tr[data-b]").forEach((n) =>
      n.addEventListener("click", () => { selectBand(n.dataset.b, { force: true }); showTab("world"); }));
  }
  renderDirectorCard();
  renderDirectorChrome();
}

function cancelFx(opts) {
  opts = opts || {};
  S.fxGen += 1;
  (S.fxTimers || []).forEach((id) => { clearTimeout(id); });
  S.fxTimers = [];
  if (S.fxRaf != null && typeof cancelAnimationFrame === "function") {
    cancelAnimationFrame(S.fxRaf);
  }
  S.fxRaf = null;
  const svg = $("map");
  if (svg) {
    const layer = svg.querySelector("#fx-overlay");
    if (layer) layer.remove();
    svg.querySelectorAll(".fx-hot,.fx-share,.fx-aid,.fx-repay,.fx-migrate").forEach((n) => {
      n.classList.remove("fx-hot", "fx-share", "fx-aid", "fx-repay", "fx-migrate");
    });
  }
  if (opts.keepStatic && S.selEvent) paintDirectorFx({ staticOnly: true });
}
function scheduleFx(fn, ms) {
  const gen = S.fxGen;
  const id = setTimeout(() => { if (gen === S.fxGen) fn(); }, ms);
  S.fxTimers.push(id);
  return id;
}
function mapIsCurrent() {
  return !!(S.run && S._mapRun === S.run.run_id && S._mapYear === S.t &&
    $("map") && $("map").querySelector(".cell"));
}
function findEventByKey(key, tHint) {
  if (!key || !S.run) return null;
  const tryYear = (t) => {
    if (t == null || t < 0) return null;
    const rec = S.years.get(ykey(S.run.run_id, t));
    if (!rec || !rec.events) return null;
    for (let i = 0; i < rec.events.length; i++) {
      const e = rec.events[i];
      if (DirectorLogic.eventKey(e, t, i) === key) {
        return Object.assign({}, e, { t: t, _i: i });
      }
    }
    return null;
  };
  if (tHint != null) {
    const hit = tryYear(tHint);
    if (hit) return hit;
  }
  const y = DirectorLogic.yearFromEventId(key);
  if (y != null) {
    const hit = tryYear(y);
    if (hit) return hit;
  }
  return tryYear(S.t);
}
async function jumpToRecordedEvent(eid, year, opts) {
  opts = opts || {};
  if (!eid) return navResult("failed", { reason: "no-event" });
  const y = +year;
  if (!Number.isFinite(y)) return navResult("failed", { reason: "no-year" });
  if (!opts.keepPlaying) setPlaying(false);
  bumpOp();
  const myOp = S.opGen;
  const myRun = S.run ? S.run.run_id : null;
  if (!myRun) return navResult("failed", { reason: "no-run" });
  const gy = await gotoYear(y, { quiet: opts.quiet, keepEvent: true, opGen: myOp });
  if (!opAlive(myOp) || !gy || gy.kind === "stale" || !gy.ok) return gy || navResult("stale");
  if (!S.run || S.run.run_id !== myRun) return navResult("stale");
  if (S.t !== y) return navResult("stale");
  const found = findEventByKey(String(eid), y);
  if (!found) return navResult("failed", { reason: "missing-event" });
  return focusEvent(found, { opGen: myOp, fromHash: true, quiet: opts.quiet });
}
function directorLineageHtml() {
  const ev = findEventByKey(S.selEvent, S.t);
  if (!ev || (ev.type !== "split" && ev.type !== "extinct")) return "";
  if (ev.type === "split") {
    return `<div class="dir-lineage">谱系提示来自事件记录，不是地图位置。
      父群体 ${esc(String(ev.parent || "未记录"))} 分裂出 ${esc(String(ev.band || "未记录"))}。
      地点未记录，禁用地图定位，不拿年末位置猜测。</div>`;
  }
  return `<div class="dir-gone">消失提示来自事件记录：群体 ${esc(String(ev.band || "未记录"))}
    人口归零被移除。地点未记录，不拿年末位置猜测。</div>`;
}
function bindDirectorLineage(wrap) {
  if (!wrap) return;
  wrap.querySelectorAll(".prior-jump").forEach((n) => {
    n.addEventListener("click", (e) => {
      e.preventDefault(); e.stopPropagation();
      const y = +n.dataset.priorYear;
      if (Number.isFinite(y)) gotoYear(y);
    });
    n.addEventListener("pointerdown", (e) => e.stopPropagation());
  });
}
function svgEl(name, attrs) {
  const n = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.keys(attrs || {}).forEach((k) => n.setAttribute(k, attrs[k]));
  return n;
}
function paintDirectorFx(opts) {
  opts = opts || {};
  const svg = $("map");
  if (!svg || !S.map) return;
  const prev = svg.querySelector("#fx-overlay");
  if (prev) prev.remove();
  svg.querySelectorAll(".fx-hot,.fx-share,.fx-aid,.fx-repay,.fx-migrate").forEach((n) => {
    n.classList.remove("fx-hot", "fx-share", "fx-aid", "fx-repay", "fx-migrate");
  });
  if (!S.selEvent) return;
  const ev = findEventByKey(S.selEvent, S.t);
  if (!ev) return;
  const focus = DirectorLogic.eventFocus(ev);
  focus.cells.forEach((i) => {
    const p = svg.querySelector('.cell[data-cell="' + i + '"]');
    if (!p) return;
    p.classList.add("fx-hot");
    if (ev.type === "share") p.classList.add("fx-share");
    else if (ev.type === "aid" && ev.repay) p.classList.add("fx-repay");
    else if (ev.type === "aid") p.classList.add("fx-aid");
    else if (ev.type === "migrate") p.classList.add("fx-migrate");
  });
  if (!focus.locate) return;
  const overlay = svgEl("g", { id: "fx-overlay", "pointer-events": "none" });
  const reduced = opts.staticOnly || DirectorLogic.prefersReducedMotion();
  if (ev.type === "migrate") {
    if (Number.isFinite(+ev.from) && S.map.cells[+ev.from]) {
      const xy = cellCenter(S.map.cells[+ev.from]);
      overlay.appendChild(svgEl("circle", {
        class: "fx-endpoint fx-endpoint-from", cx: xy[0].toFixed(1), cy: xy[1].toFixed(1), r: "11",
      }));
    }
    if (Number.isFinite(+ev.to) && S.map.cells[+ev.to]) {
      const xy = cellCenter(S.map.cells[+ev.to]);
      overlay.appendChild(svgEl("circle", {
        class: "fx-endpoint fx-endpoint-to", cx: xy[0].toFixed(1), cy: xy[1].toFixed(1), r: "13",
      }));
    }
  } else if ((ev.type === "share" || ev.type === "aid") && focus.cells.length) {
    const cell = S.map.cells[focus.cells[0]];
    if (cell) {
      const xy = cellCenter(cell);
      const mark = ev.type === "share" ? "fx-share-mark"
        : (ev.repay ? "fx-repay-mark" : "fx-aid-mark");
      overlay.appendChild(svgEl("circle", {
        class: mark + (reduced ? "" : " fx-pulse"),
        cx: xy[0].toFixed(1), cy: (xy[1] - 6).toFixed(1), r: "7",
      }));
    }
  }
  svg.appendChild(overlay);
}
function panToCell(i, gen) {
  if (DirectorLogic.prefersReducedMotion()) return;
  if (!S.map || !S.map.cells[i]) return;
  const xy = cellCenter(S.map.cells[i]);
  const start = { x: S.cam.x, y: S.cam.y };
  const tx = 260 - xy[0], ty = 215 - xy[1];
  const t0 = performance.now();
  const dur = 280;
  const step = (now) => {
    if (gen !== S.fxGen) return;
    const u = Math.min(1, (now - t0) / dur);
    S.cam.x = start.x + (tx - start.x) * u;
    S.cam.y = start.y + (ty - start.y) * u;
    applyCam();
    if (u < 1) S.fxRaf = requestAnimationFrame(step);
  };
  S.fxRaf = requestAnimationFrame(step);
}
function renderDirectorChrome() {
  document.querySelectorAll("#play-mode [data-mode]").forEach((b) =>
    b.classList.toggle("on", b.dataset.mode === S.playMode));
  const years = DirectorLogic.eventYearsFromSeries(S.series);
  const prev = DirectorLogic.prevEventYear(years, S.t);
  const next = DirectorLogic.nextEventYear(years, S.t);
  if ($("b-prev-ev")) $("b-prev-ev").disabled = prev == null;
  if ($("b-next-ev")) $("b-next-ev").disabled = next == null;
  const rec = recNow();
  const st = DirectorLogic.eventModeStatus({
    series: S.series, yearsRecorded: S.run ? (S.run.years_recorded ?? 0) : 0,
    runStatus: S.run ? S.run.status : "", rec: rec, t: S.t,
  });
  if ($("dir-mode-note")) {
    if (S.playMode === "events") {
      $("dir-mode-note").textContent = st.text ||
        ("只跳有记录的事件年（" + years.length + " 个年份）。" + DirectorLogic.orderNote);
    } else {
      $("dir-mode-note").textContent = st.kind === "empty-year" || st.kind === "none"
        ? st.text
        : "逐年推进已保存记录。空年也会停，不把出生人数当成事件。";
    }
  }
}
function renderDirectorCard() {
  const box = $("director-card");
  const body = $("director-card-body");
  if (!box || !body) return;
  const ev = findEventByKey(S.selEvent, S.t);
  if (!ev) { box.hidden = true; body.innerHTML = ""; return; }
  box.hidden = false;
  const focus = DirectorLogic.eventFocus(ev);
  const rec = recNow();
  const related = focus.related.map((r) => {
    const name = rec ? bandName(rec, r.id) : (String(r.id).slice(0, 8) + "…");
    const role = ({ parent: "父群体", donor: "供给方", receiver: "接收方", band: "相关群体" })[r.role] || r.role;
    return `<button type="button" class="prior-jump" data-b="${esc(r.id)}">${esc(role)} · ${esc(name)}</button>`;
  }).join("");
  body.innerHTML = `<div class="dir-title">${ev.t === 0 ? "开局" : "第 " + ev.t + " 年"} · ${esc(TYPE_LABEL(ev.type))}${ev.repay ? " · 回助" : ""} · ${esc(DirectorLogic.eventKey(ev, ev.t, ev._i))}</div>
    <p class="dir-text">${esc(ev.text || "")}</p>
    <div class="dir-meta">来源：${esc(ev.source || "未标注")}${ev.unrecorded ? "　·　未记录：" + esc(ev.unrecorded) : ""}</div>
    <div class="dir-meta">${esc(focus.note)}</div>
    <div class="dir-meta">${esc(DirectorLogic.orderNote)}</div>
    ${related ? `<div class="dir-related">${related}</div>` : ""}`;
  body.querySelectorAll("[data-b]").forEach((n) => {
    n.addEventListener("click", (e) => {
      e.preventDefault();
      selectBand(n.dataset.b, { force: true, keepCell: true, skipMap: mapIsCurrent(), rail: "dossier" });
    });
  });
}
function setPlayMode(mode, opts) {
  opts = opts || {};
  const next = mode === "events" ? "events" : "year";
  if (S.playMode === next && !opts.force) {
    renderDirectorChrome();
    setHash({ mode: next === "events" ? "events" : "" });
    return;
  }
  if (!opts.keepPlaying) setPlaying(false);
  bumpOp();
  cancelFx({ keepStatic: !!S.selEvent });
  S.playMode = next;
  setHash({ mode: next === "events" ? "events" : "" });
  renderDirectorChrome();
  renderDensity();
  if (!opts.silent) {
    renderEvents();
    paintDirectorFx({ staticOnly: true });
  }
}
async function gotoEventYear(t) {
  setPlaying(false);
  bumpOp();
  const myOp = S.opGen;
  const gy = await gotoYear(t, { opGen: myOp });
  if (!opAlive(myOp) || !gy || gy.kind === "stale") return gy || navResult("stale");
  if (!gy.ok) return gy;
  const rec = recNow();
  if (rec && rec.events && rec.events.length) {
    return focusEvent(Object.assign({}, rec.events[0], { t: t, _i: 0 }), { opGen: myOp });
  }
  S.selEvent = null;
  renderDirectorCard();
  renderDirectorChrome();
  return { ok: true, t: t };
}
async function stepEventYear(dir) {
  const years = DirectorLogic.eventYearsFromSeries(S.series);
  const t = dir < 0 ? DirectorLogic.prevEventYear(years, S.t) : DirectorLogic.nextEventYear(years, S.t);
  if (t == null) {
    const rec = recNow();
    const st = DirectorLogic.eventModeStatus({
      series: S.series, yearsRecorded: S.run ? (S.run.years_recorded ?? 0) : 0,
      runStatus: S.run ? S.run.status : "", rec: rec, t: S.t,
    });
    if ($("tl-note")) $("tl-note").textContent = st.text || "没有更多有记录的事件年。";
    return { ok: false, reason: "no-event-year" };
  }
  return gotoEventYear(t);
}
async function tickEvents() {
  if (!S.playing) return;
  const myOp = S.opGen;
  if (pendingCurrentYear()) {
    tick();
    return;
  }
  const years = DirectorLogic.eventYearsFromSeries(S.series);
  const rec0 = recNow();
  const st = DirectorLogic.eventModeStatus({
    series: S.series, yearsRecorded: S.run ? (S.run.years_recorded ?? 0) : 0,
    runStatus: S.run ? S.run.status : "", rec: rec0, t: S.t,
  });
  if (!years.length) {
    if ($("tl-note")) $("tl-note").textContent = st.text;
    setPlaying(false);
    return;
  }
  const rec = rec0;
  if (rec && rec.events && rec.events.length) {
    const items = rec.events.map((e, i) => Object.assign({}, e, { t: S.t, _i: i }));
    const idx = items.findIndex((e) => DirectorLogic.eventKey(e, S.t, e._i) === S.selEvent);
    if (idx < 0) {
      const fe = await focusEvent(items[0], { fromPlay: true, skipMap: mapIsCurrent(), opGen: myOp });
      if (!afterPlayStep(fe, myOp)) return;
      if (!S.playing || !opAlive(myOp)) return;
      schedulePlayTimer(myOp, playDelay(), tick);
      return;
    }
    if (idx + 1 < items.length) {
      const fe = await focusEvent(items[idx + 1], { fromPlay: true, skipMap: mapIsCurrent(), opGen: myOp });
      if (!afterPlayStep(fe, myOp)) return;
      if (!S.playing || !opAlive(myOp)) return;
      schedulePlayTimer(myOp, playDelay(), tick);
      return;
    }
  }
  const ny = DirectorLogic.nextEventYear(years, S.t);
  if (ny == null) {
    if (S.run && (S.run.status === "running" || S.run.status === "queued")) {
      if ($("tl-note")) $("tl-note").textContent = "已经放到最新有记录的事件年，等后台继续计算…";
      schedulePlayTimer(myOp, PLAY_PENDING_MS, tick);
      return;
    }
    setPlaying(false);
    return;
  }
  const gy = await gotoYear(ny, { quiet: true, opGen: myOp });
  if (!afterPlayStep(gy, myOp)) return;
  const rec2 = recNow();
  if (!rec2) {
    if ($("tl-note")) $("tl-note").textContent = "第 " + ny + " 年的记录尚未加载，不把空清单当成 0 条事件。";
    S.playWait = { t: ny, op: myOp, runId: S.run ? S.run.run_id : null };
    schedulePlayTimer(myOp, PLAY_PENDING_MS, tick);
    return;
  }
  if (!rec2.events || !rec2.events.length) {
    if ($("tl-note")) $("tl-note").textContent = "第 " + ny + " 年曲线记有事件，但事件清单缺失。不补编。";
    schedulePlayTimer(myOp, playDelay(), tick);
    return;
  }
  const fe = await focusEvent(Object.assign({}, rec2.events[0], { t: ny, _i: 0 }), { fromPlay: true, opGen: myOp });
  if (!afterPlayStep(fe, myOp)) return;
  if (!S.playing || !opAlive(myOp)) return;
  schedulePlayTimer(myOp, playDelay(), tick);
}
async function focusEvent(ev, opts) {
  opts = opts || {};
  if (!ev) return { ok: false, reason: "no-event" };
  if (!opts.fromPlay && !opts.fromHash) setPlaying(false);
  const myOp = opts.opGen != null ? opts.opGen : S.opGen;
  if (!opAlive(myOp)) return { ok: false, reason: "stale" };
  const myRun = S.run ? S.run.run_id : null;
  showTab("world");
  const t = ev.t != null ? ev.t : ev.year;
  cancelFx();
  const myFx = S.fxGen;
  if (t != null && t !== S.t) {
    const gy = await gotoYear(t, { quiet: opts.quiet, keepEvent: true, opGen: myOp });
    if (!opAlive(myOp) || !gy || gy.kind === "stale") return gy || navResult("stale");
    if (!gy.ok) return gy;
  }
  if (!opAlive(myOp)) return navResult("stale");
  if (!S.run || (myRun && S.run.run_id !== myRun)) return navResult("stale");
  if (t != null && S.t !== t) return navResult("stale");
  if (!recNow() && t != null) return navResult("failed", { t: t, reason: "missing-record" });
  const rec = recNow();
  const resolved = (rec && rec.events)
    ? findEventByKey(DirectorLogic.eventKey(ev, t, ev._i), S.t) || Object.assign({}, ev, { t: S.t })
    : Object.assign({}, ev, { t: t });
  S.selEvent = DirectorLogic.eventKey(resolved, resolved.t, resolved._i);
  const focus = DirectorLogic.eventFocus(resolved);
  if (focus.locate && focus.cells.length) {
    if (resolved.type === "migrate" && resolved.to != null) S.selCell = +resolved.to;
    else S.selCell = focus.cells[0];
  } else if (resolved.type === "split" || resolved.type === "extinct") {
    S.selCell = null;
  }
  const relatedId = resolved.band || resolved.receiver || resolved.donor || resolved.parent || null;
  if (relatedId) S.selBand = String(relatedId);
  setHash({
    event: S.selEvent, t: String(S.t),
    mode: S.playMode === "events" ? "events" : "",
    b: S.selBand || "",
  });
  if (resolved.type === "split" || resolved.type === "extinct") showRail("dossier");
  else showRail("chronicle");
  const skipMap = opts.skipMap && mapIsCurrent();
  if (!skipMap) renderMap();
  else paintDirectorFx();
  renderEvents();
  renderSide();
  renderDirectorCard();
  const evNode = document.querySelector('#events .ev[data-eid="' + S.selEvent + '"]');
  if (evNode && evNode.scrollIntoView) evNode.scrollIntoView({ block: "nearest" });
  if (focus.locate && focus.cells.length) panToCell(focus.cells[0], myFx);
  return navResult("success", { t: S.t, event: S.selEvent });
}

function jumpToEvent(ev) {
  focusEvent(ev);
}

function fillCompareSelects() {
  const opts = (S.runs || []).map((r) =>
    `<option value="${esc(r.run_id)}">${esc(r.label || r.run_id)} · ${esc(r.engine || "")} · 已算${r.years_recorded}</option>`).join("");
  ["cmp-a", "cmp-b"].forEach((id, i) => {
    const el = $(id); if (!el) return;
    const keep = el.value || (S.cmp && (i ? S.cmp.b : S.cmp.a)) || "";
    el.innerHTML = `<option value="">选择…</option>` + opts;
    if (keep) el.value = keep;
  });
  if ($("cmp-year") && document.activeElement !== $("cmp-year")) {
    const y = S.cmp.t != null ? S.cmp.t : S.t;
    $("cmp-year").value = String(y);
  }
}
async function fetchYearOrMiss(runId, t) {
  try {
    const rec = await api(`/api/runs/${runId}/year/${t}`);
    return { rec: rec, missing: false, failed: false };
  } catch (e) {
    const run = (S.runs || []).find((r) => r.run_id === runId);
    const recorded = run && run.years_recorded != null ? run.years_recorded : -1;
    const outOfRange = t > recorded;
    const missing = e.status === 404 && outOfRange;
    const failed = !missing;
    return { rec: null, missing: missing, failed: failed, error: e.message, status: e.status };
  }
}
function cmpCell(side, row, t, packSide) {
  if (packSide && packSide.failed) {
    return `<td class="miss">第 ${t} 年读取失败${packSide.error ? "：" + esc(packSide.error) : ""}。可重试。不是缺失。</td>`;
  }
  if (row["miss" + side]) return `<td class="miss">第 ${t} 年缺失</td>`;
  const v = row[side === "A" ? "a" : "b"];
  return `<td class="${row.diff ? "diff" : ""}">${v == null ? "未记录" : esc(String(v))}</td>`;
}
function renderCompare(pack) {
  const { runA, runB, t, a, b, relA, relB } = pack;
  const diffs = CompareLogic.configDiff(runA, runB);
  if ($("cmp-cfg")) {
    $("cmp-cfg").textContent = diffs.length
      ? ("真实配置不同：" + diffs.map((d) => d.key + " " + d.a + " / " + d.b).join(" · ") + "。不同不解释成因。")
      : "这两次运行列出的引擎与参数字段相同。不同不解释成因。";
  }
  const missA = !!(a && a.missing), missB = !!(b && b.missing);
  const recA = a && a.rec, recB = b && b.rec;
  const rows = [
    CompareLogic.row("人口", recA && recA.agg ? recA.agg.pop : null, recB && recB.agg ? recB.agg.pop : null, missA, missB),
    CompareLogic.row("群体数", recA && recA.agg ? recA.agg.bands : null, recB && recB.agg ? recB.agg.bands : null, missA, missB),
    CompareLogic.row("野外存量合计 kcal", CompareLogic.stockSum(recA), CompareLogic.stockSum(recB), missA, missB),
    CompareLogic.row("本年缺粮", recA && recA.year ? recA.year.deficit_cum : null, recB && recB.year ? recB.year.deficit_cum : null, missA, missB),
    CompareLogic.row("可核实事件条数", recA && recA.events ? recA.events.length : null, recB && recB.events ? recB.events.length : null, missA, missB),
    CompareLogic.row("援助转移笔数", recA && recA.aid ? recA.aid.transfers : "未记录", recB && recB.aid ? recB.aid.transfers : "未记录", missA, missB),
    CompareLogic.row("援助食物 kcal", recA && recA.aid ? recA.aid.kcal : "未记录", recB && recB.aid ? recB.aid.kcal : "未记录", missA, missB),
    CompareLogic.row("回助笔数", recA && recA.recip ? recA.recip.repay_transfers : "未记录", recB && recB.recip ? recB.recip.repay_transfers : "未记录", missA, missB),
    CompareLogic.row("分配改变（格×年）", recA && recA.recip ? recA.recip.changed : "未记录", recB && recB.recip ? recB.recip.changed : "未记录", missA, missB),
  ];
  if ($("cmp-table")) {
    $("cmp-table").innerHTML = `<tr><th>指标</th><th>${esc((runA && (runA.label || runA.run_id)) || "A")}</th><th>${esc((runB && (runB.label || runB.run_id)) || "B")}</th></tr>` +
      rows.map((row) => `<tr><td>${esc(row.label)}</td>${cmpCell("A", row, t, a)}${cmpCell("B", row, t, b)}</tr>`).join("");
  }
  const evA = ((recA && recA.events) || []).map((e) => e.id || (e.type + ":" + e.t));
  const evB = ((recB && recB.events) || []).map((e) => e.id || (e.type + ":" + e.t));
  if ($("cmp-events")) {
    $("cmp-events").innerHTML = `<tr><th>事件 id</th><th>A</th><th>B</th></tr>` +
      Array.from(new Set(evA.concat(evB))).map((id) => {
        const inA = evA.indexOf(id) >= 0, inB = evB.indexOf(id) >= 0;
        return `<tr><td>${esc(String(id))}</td><td class="${inA && !inB ? "diff" : ""}">${inA ? "有" : (a && a.missing ? "年缺失" : "无")}</td><td class="${inB && !inA ? "diff" : ""}">${inB ? "有" : (b && b.missing ? "年缺失" : "无")}</td></tr>`;
      }).join("");
  }
  const edgesA = ((relA && relA.edges) || []).map((e) => String(e.donor) + "→" + String(e.receiver) + ":" + (e.kcal || 0));
  const edgesB = ((relB && relB.edges) || []).map((e) => String(e.donor) + "→" + String(e.receiver) + ":" + (e.kcal || 0));
  if ($("cmp-edges")) {
    const keys = Array.from(new Set(((relA && relA.edges) || []).concat((relB && relB.edges) || []).map((e) => String(e.donor) + "→" + String(e.receiver))));
    $("cmp-edges").innerHTML = `<tr><th>有向边</th><th>A kcal / 笔</th><th>B kcal / 笔</th></tr>` +
      keys.map((k) => {
        const ea = ((relA && relA.edges) || []).find((e) => String(e.donor) + "→" + String(e.receiver) === k);
        const eb = ((relB && relB.edges) || []).find((e) => String(e.donor) + "→" + String(e.receiver) === k);
        const va = ea ? (nf(ea.kcal) + " / " + ea.transfers) : "无";
        const vb = eb ? (nf(eb.kcal) + " / " + eb.transfers) : "无";
        return `<tr><td>${esc(k)}</td><td class="${va !== vb ? "diff" : ""}">${va}</td><td class="${va !== vb ? "diff" : ""}">${vb}</td></tr>`;
      }).join("");
  }
  void edgesA; void edgesB;
}
async function loadCompare() {
  const aId = ($("cmp-a") && $("cmp-a").value) || S.cmp.a;
  const bId = ($("cmp-b") && $("cmp-b").value) || S.cmp.b;
  const parsed = OverviewLogic.parseStrictInt(($("cmp-year") && $("cmp-year").value) || S.cmp.t, { name: "对照年份", min: 0 });
  if (!parsed.ok) { flash(parsed.error, true); return { ok: false }; }
  const t = parsed.value;
  S.cmp = { a: aId, b: bId, t: t };
  if (!aId || !bId) { flash("请选两个已有运行。", true); return { ok: false }; }
  const myReq = ++S.cmpReqGen;
  const runA = (S.runs || []).find((r) => r.run_id === aId);
  const runB = (S.runs || []).find((r) => r.run_id === bId);
  const accept = () => S.cmpReqGen === myReq && S.cmp.a === aId && S.cmp.b === bId && S.cmp.t === t;
  const [a, b, relA, relB] = await Promise.all([
    fetchYearOrMiss(aId, t),
    fetchYearOrMiss(bId, t),
    api(`/api/runs/${aId}/relations?at_year=${t}`).catch(() => ({ edges: [] })),
    api(`/api/runs/${bId}/relations?at_year=${t}`).catch(() => ({ edges: [] })),
  ]);
  if (!accept()) return { ok: false, reason: "stale" };
  renderCompare({ runA, runB, t, a, b, relA, relB });
  return { ok: true, a: a, b: b, t: t, stale: false };
}

/* ---------------- 运行记录 ---------------- */
function renderRuns() {
  const head = `<tr><th>运行</th><th>状态</th><th>引擎</th><th>seed</th><th>年数</th><th>SIGMA_M</th>
    <th>MOVE_MORT_M</th><th>SHARE_M</th><th>AID_M</th><th>RECIP_M</th><th>信息条件</th><th>已算/目标</th><th>创建时间</th><th>模型版本</th><th>操作</th></tr>`;
  $("runtable").innerHTML = head + S.runs.map((r) => `<tr class="${S.run && S.run.run_id === r.run_id ? "on" : ""}">
    <td class="clickable" data-open="${esc(r.run_id)}">${esc(r.label || r.run_id)}
      ${r.kind === "preset" ? '<span class="badge s-off">预生成</span>' : ""}</td>
    <td>${statusBadge(r.status)}</td>
    <td>${esc(r.engine || "exp03")}</td><td>${r.seed}</td><td>${r.years}</td>
    <td>${r.sigma_m}‰</td><td>${r.move_mort_m}‰</td>
    <td>${engineHasParam(r.engine || "exp03", "share_m") ? (r.share_m ?? 0) + "‰" : "—"}</td>
    <td>${engineHasParam(r.engine || "exp03", "aid_m") ? (r.aid_m ?? 0) + "‰" : "—"}</td>
    <td>${engineHasParam(r.engine || "exp03", "recip_m") ? (r.recip_m ?? 0) + "‰" : "—"}</td>
    <td>${S.cfg.arms[r.arm] ? esc(S.cfg.arms[r.arm].label) : esc(r.arm)}</td>
    <td>${r.years_recorded}/${r.years}</td><td>${tsfmt(r.created_at)}</td>
    <td><small>${esc(r.engine_path || "")} · ${esc((r.engine_sha256 || "").slice(0, 8))}</small></td>
    <td>${["queued", "running"].includes(r.status)
      ? `<span class="link" data-cancel="${esc(r.run_id)}">取消</span>`
      : (r.kind === "preset" ? "" : `<span class="link" data-del="${esc(r.run_id)}">删除</span>`)}
      ${r.error ? `<div class="err"><small>${esc(r.error)}</small></div>` : ""}</td></tr>`).join("");
  $("runtable").querySelectorAll("[data-open]").forEach((n) =>
    n.addEventListener("click", () => openRun(n.dataset.open)));
  $("runtable").querySelectorAll("[data-cancel]").forEach((n) =>
    n.addEventListener("click", async () => {
      try { await api(`/api/runs/${n.dataset.cancel}/cancel`, { method: "POST" }); flash("已请求取消"); }
      catch (e) { flash("取消失败：" + e.message, true); } refresh();
    }));
  $("runtable").querySelectorAll("[data-del]").forEach((n) =>
    n.addEventListener("click", async () => {
      if (!confirm("删除这次运行的全部记录？")) return;
      try { await api(`/api/runs/${n.dataset.del}`, { method: "DELETE" }); }
      catch (e) { flash("删除失败：" + e.message, true); } refresh();
    }));
  const sw = $("run-switch");
  if (sw) {
    const cur = S.run ? S.run.run_id : "";
    sw.innerHTML = `<option value="">选择世界…</option>` + S.runs.map((r) =>
      `<option value="${esc(r.run_id)}"${r.run_id === cur ? " selected" : ""}>${esc(r.label || r.run_id)} · ${esc(r.engine || "")} · ${r.years_recorded}/${r.years}</option>`).join("");
  }
  fillCompareSelects();
}

async function openRun(id) {
  setPlaying(false);
  bumpOp();
  const myOp = S.opGen;
  const myEpoch = bump();
  cancelFx();
  S.selEvent = null;
  S.bandCache = new Map();
  S.relCache = new Map();
  S.bandReqGen += 1;
  S.relReqGen += 1;
  S.relations = null;
  S.relSel = null;
  S.relCardKey = "";
  clearRelEdgeCard();
  let run, ser;
  try {
    run = await api(`/api/runs/${id}`);
    if (S.epoch !== myEpoch || !opAlive(myOp)) return { ok: false, reason: "stale" };
    ser = await api(`/api/runs/${id}/series`);
    if (S.epoch !== myEpoch || !opAlive(myOp)) return { ok: false, reason: "stale" };
  } catch (e) {
    if (S.epoch === myEpoch) flash("打开运行失败：" + e.message, true);
    return;
  }
  S.run = run;
  S.meta = run.meta || null;
  S.years.clear(); S.selBand = null; S.selCell = null; S.band = null;
  S.cam = { x: 0, y: 0, k: 1 }; S.layer = "resource"; S.view = "truth";
  S.yearWait = { runId: id, t: 0, pending: true };
  S.series = ser.series;
  S.view = "truth";
  if ($("v-truth")) $("v-truth").classList.add("on");
  if ($("v-mem")) $("v-mem").classList.remove("on");
  $("scrub").max = maxT();
  S.t = 0;
  syncYearWidgets(0);
  setHash({
    run: id, b: "", view: "", t: "0", event: "",
    mode: S.playMode === "events" ? "events" : "",
    archive: S.bandScope === "full" ? "full" : "",
  });
  renderOverview(); renderMap(); renderSide(); renderEvents(); renderStatus();
  renderDirectorCard(); renderDirectorChrome();
  const gy = await gotoYear(0, { opGen: myOp });
  if (!opAlive(myOp) || !gy || !gy.ok) return { ok: false, reason: "stale" };
  renderRuns(); renderCharts(); renderStatus(); renderOverview();
  renderLibrary();
  prefetchYears(id, maxT());
}

/* ---------------- 里程碑 ---------------- */
async function renderMilestones() {
  const d = await api("/api/milestones");
  const bold = (x) => esc(x).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  const cls = { "已验收": "s-done", "已实现待审": "s-run", "进行中": "s-run", "待批准": "s-wait", "未开始": "s-off" };
  $("ms-note").textContent = d.note;
  $("milestones").innerHTML = d.items.map((m) => `<div class="ms">
    <h4>${esc(m.title)} <span class="badge ${cls[m.status] || "s-off"}">${esc(m.status)}</span></h4>
    <div>${bold(m.note)}</div>
    <div class="meta">更新：${esc(m.updated)}　·　提交：${esc(m.commit)}　·　来源：${esc(m.sources.join("、"))}</div>
  </div>`).join("") + `<div class="muted">仓库 HEAD：${esc(d.repo_commit || "未知")}　·　
    状态只有这五种：${d.statuses.join(" / ")}，不给总体百分比。模拟年数不是项目开发进度。</div>`;
}

/* ---------------- 杂项 ---------------- */
function flash(msg, bad) {
  const n = $("formnote");
  const t = $("toast");
  if (n) {
    n.textContent = String(msg);
    n.classList.toggle("err", !!bad);
  }
  if (t) {
    t.hidden = false;
    t.textContent = String(msg);
    t.classList.toggle("err", !!bad);
    setTimeout(() => { if (t.textContent === String(msg)) t.hidden = true; }, 5000);
  }
  if (n) setTimeout(() => { if (n.textContent === String(msg)) n.textContent = ""; }, 6000);
}
function showTab(name) {
  if (name === "events") {
    name = "world";
    setTimeout(() => { const p = $("events"); if (p) p.scrollIntoView({ block: "start" }); }, 0);
  }
  if (["world", "network", "compare", "metrics", "runs", "progress"].indexOf(name) < 0) name = "world";
  ["world", "network", "compare", "metrics", "events", "runs", "progress"].forEach((t) => {
    const el = $("tab-" + t); if (el) el.hidden = t !== name;
  });
  document.querySelectorAll("#tabs button, .hud-actions [data-tab]").forEach((b) =>
    b.classList.toggle("on", b.dataset.tab === name));
  setHash({ tab: name });
  if (name === "metrics") renderCharts();
  if (name === "network") loadRelations();
  if (name === "compare") { fillCompareSelects(); }
  if (name === "progress") renderMilestones().catch((e) => flash(e.message, true));
}

async function refresh() {
  try {
    const d = await api("/api/runs");
    S.runs = d.runs;
    if (S.run) {
      const myRun = S.run.run_id, myEpoch = S.epoch;
      const cur = S.runs.find((r) => r.run_id === myRun);
      if (cur) {
        const grew = cur.years_recorded > (S.run.years_recorded ?? 0);
        Object.assign(S.run, cur);
        $("scrub").max = maxT();
        $("tl-calc").textContent = `已计算到：第 ${maxT()} 年 / 目标 ${S.run.years} 年`;
        if (grew) {
          const d2 = await api(`/api/runs/${myRun}/series`);
          if (stale(myEpoch, myRun)) return;
          S.series = d2.series; renderCharts();
        }
        const wantT = S.t;
        const hasYear = S.years.has(ykey(myRun, wantT));
        if (!hasYear && shouldRetryMissingYear(S.run, wantT)) {
          try {
            const rec = await api(`/api/runs/${myRun}/year/${wantT}`);
            if (stale(myEpoch, myRun) || S.t !== wantT) return;
            S.years.set(ykey(myRun, wantT), rec);
            delete S.yearMiss[yearMissKey(myRun, wantT)];
            S.yearWait = null;
          } catch (e) {
            if (stale(myEpoch, myRun) || S.t !== wantT) return;
            const k = yearMissKey(myRun, wantT);
            S.yearMiss[k] = (S.yearMiss[k] || 0) + 1;
            const pending = isPendingYearError(e, wantT) && shouldRetryMissingYear(S.run, wantT);
            S.yearWait = { runId: myRun, t: wantT, pending: pending, status: e.status, message: e.message };
            if (!pending && e.status !== 404) flash("读取第 " + wantT + " 年失败：" + e.message, true);
          }
        }
        if (!S.meta) {
          const d3 = await api(`/api/runs/${myRun}`);
          if (stale(myEpoch, myRun)) return;
          if (d3.meta) S.meta = d3.meta;
        }
      }
    }
    renderRuns(); renderStatus(); renderOverview();
    if (S.run && S.years.has(ykey(S.run.run_id, S.t))) {
      renderMap(); renderSide(); renderEvents(); renderTech();
    } else if (S.run) {
      renderMap(); renderSide(); renderEvents();
    }
  } catch (e) {
    $("statusline").innerHTML = `<span class="err">后台读取失败：${esc(e.message)}</span>`;
  }
}

async function boot() {
  const skin = new URLSearchParams(location.search).get("skin");
  if (skin === "console") {
    S.skin = "console";
    document.documentElement.classList.add("skin-console");
  }
  if (new URLSearchParams(location.search).get("tex") === "0") {
    document.documentElement.classList.add("notex");
  }
  $("token").value = S.token;
  $("tokbtn").addEventListener("click", () => {
    S.token = $("token").value.trim();
    sessionStorage.setItem("obs_token", S.token);
    location.reload();
  });
  document.querySelectorAll("#tabs button, .hud-actions [data-tab]").forEach((b) =>
    b.addEventListener("click", () => showTab(b.dataset.tab)));
  $("v-truth").addEventListener("click", () => setLayer("resource"));
  $("v-mem").addEventListener("click", () => setLayer("mem"));
  document.querySelectorAll("#layers [data-layer]").forEach((b) => {
    if (b.id === "v-truth" || b.id === "v-mem") return;
    b.addEventListener("click", () => setLayer(b.dataset.layer));
  });
  if ($("run-switch")) $("run-switch").addEventListener("change", (e) => {
    if (e.target.value) openRun(e.target.value);
  });
  bindMapCam();
  if ($("zoom-in")) $("zoom-in").addEventListener("click", () => { S.cam.k = Math.min(3.2, S.cam.k * 1.25); renderMap(); });
  if ($("zoom-out")) $("zoom-out").addEventListener("click", () => { S.cam.k = Math.max(0.7, S.cam.k / 1.25); renderMap(); });
  if ($("zoom-reset")) $("zoom-reset").addEventListener("click", () => { S.cam = { x: 0, y: 0, k: 1 }; renderMap(); });
  $("b-play").addEventListener("click", () => setPlaying(!S.playing));
  $("b-next").addEventListener("click", () => {
    setPlaying(false);
    bumpOp();
    if (S.playMode === "events") stepEventYear(1);
    else gotoYear(S.t + 1, { opGen: S.opGen });
  });
  $("b-prev").addEventListener("click", () => {
    setPlaying(false);
    bumpOp();
    if (S.playMode === "events") stepEventYear(-1);
    else gotoYear(S.t - 1, { opGen: S.opGen });
  });
  $("b-home").addEventListener("click", () => {
    setPlaying(false);
    bumpOp();
    cancelFx();
    S.selEvent = null;
    gotoYear(0, { opGen: S.opGen });
  });
  if ($("b-prev-ev")) $("b-prev-ev").addEventListener("click", () => stepEventYear(-1));
  if ($("b-next-ev")) $("b-next-ev").addEventListener("click", () => stepEventYear(1));
  if ($("play-mode")) $("play-mode").addEventListener("click", (e) => {
    const b = e.target.closest("[data-mode]"); if (!b) return;
    setPlayMode(b.dataset.mode);
  });
  if ($("b-retry-year")) $("b-retry-year").addEventListener("click", () => { retryYear(); });
  if ($("band-scope")) $("band-scope").addEventListener("click", (e) => {
    const b = e.target.closest("[data-scope]"); if (!b) return;
    S.bandScope = b.dataset.scope === "full" ? "full" : "as_of";
    setHash({ archive: S.bandScope === "full" ? "full" : "" });
    if (S.selBand) loadBand(S.selBand);
    loadRelations();
    renderSide();
  });
  if ($("b-open-network")) $("b-open-network").addEventListener("click", () => { showTab("network"); loadRelations(); });
  if ($("net-use-play")) $("net-use-play").addEventListener("click", () => {
    if ($("net-year")) $("net-year").value = String(S.t);
    loadRelations();
  });
  if ($("cmp-go")) $("cmp-go").addEventListener("click", () => loadCompare());
  if ($("cmp-use-play")) $("cmp-use-play").addEventListener("click", () => {
    if ($("cmp-year")) $("cmp-year").value = String(S.t);
    loadCompare();
  });
  if ($("net-year")) $("net-year").addEventListener("change", () => {
    const parsed = OverviewLogic.parseStrictInt($("net-year").value, { name: "年份", min: 0 });
    if (!parsed.ok) { flash(parsed.error, true); return; }
    bumpOp();
    const myOp = S.opGen;
    gotoYear(parsed.value, { opGen: myOp }).then((gy) => {
      if (!opAlive(myOp) || !gy || !gy.ok) return;
      loadRelations();
    });
  });
  $("speed").addEventListener("change", (e) => { S.speed = +e.target.value; });
  $("scrub").addEventListener("input", (e) => {
    setPlaying(false);
    bumpOp();
    gotoYear(+e.target.value, { opGen: S.opGen });
  });
  $("b-start").addEventListener("click", startRun);
  if ($("b-confirm")) $("b-confirm").addEventListener("click", confirmStartRun);
  if ($("b-confirm-cancel")) $("b-confirm-cancel").addEventListener("click", () => {
    S._runDraft = null; if ($("forge-confirm")) $("forge-confirm").hidden = true;
  });
  if ($("b-pin-year")) $("b-pin-year").addEventListener("click", pinCurrentYear);
  if ($("b-pin-event")) $("b-pin-event").addEventListener("click", pinCurrentEvent);
  if ($("b-export-rec")) $("b-export-rec").addEventListener("click", exportCurrentRecord);
  if ($("band-search")) $("band-search").addEventListener("input", () => renderEvents());
  if ($("forge-presets")) $("forge-presets").addEventListener("click", (e) => {
    const b = e.target.closest("[data-preset]"); if (!b) return;
    applyForgePreset(b.dataset.preset);
  });
  if ($("recip-off")) $("recip-off").addEventListener("click", () => { $("f-recip").value = "0"; });
  if ($("recip-on")) $("recip-on").addEventListener("click", () => { $("f-recip").value = "1000"; });
  const railTabs = $("rail-tabs");
  if (railTabs) railTabs.addEventListener("click", (e) => {
    const b = e.target.closest("[data-rail]"); if (!b) return;
    showRail(b.dataset.rail);
  });
  document.addEventListener("keydown", (e) => {
    const el = e.target || document.activeElement;
    const tag = (el && el.tagName) || "";
    if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA" || tag === "BUTTON") return;
    if (el && el.isContentEditable) return;
    if (e.key === "ArrowLeft") {
      e.preventDefault(); setPlaying(false); bumpOp();
      if (S.playMode === "events") stepEventYear(-1); else gotoYear(S.t - 1, { opGen: S.opGen });
    } else if (e.key === "ArrowRight") {
      e.preventDefault(); setPlaying(false); bumpOp();
      if (S.playMode === "events") stepEventYear(1); else gotoYear(S.t + 1, { opGen: S.opGen });
    } else if (e.key === "Home") {
      e.preventDefault(); setPlaying(false); bumpOp(); cancelFx(); S.selEvent = null; gotoYear(0, { opGen: S.opGen });
    } else if (e.key === " " || e.code === "Space") { e.preventDefault(); setPlaying(!S.playing); }
  });
  $("ev-scope").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-scope]"); if (!b) return;
    S.evScope = b.dataset.scope; renderEvents();
  });
  $("ev-filter").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-type]"); if (!b) return;
    S.evFilter = b.dataset.type; renderEvents();
  });

  try {
    S.cfg = await api("/api/config");
  } catch (e) {
    $("statusline").innerHTML = e.status === 401
      ? `<span class="err">需要访问令牌：请在右上角填入后点“保存”。</span>`
      : `<span class="err">后台连接失败：${esc(e.message)}</span>`;
    return;
  }
  S.map = await api("/api/map");
  $("f-arm").innerHTML = Object.entries(S.cfg.arms)
    .map(([k, v]) => `<option value="${esc(k)}">${esc(v.label)}</option>`).join("");
  $("armnote").textContent = Object.values(S.cfg.arms).map((v) => v.label + "：" + v.note).join("　");
  const engines = S.cfg.engines || {};
  const engineKeys = Object.keys(engines);
  if (engineKeys.length) {
    $("f-engine").innerHTML = engineKeys.map((k) =>
      `<option value="${esc(k)}"${k === S.cfg.default_engine ? " selected" : ""}>${esc(engines[k].engine_label || k)}</option>`).join("");
    $("f-engine").addEventListener("change", syncEngineForm);
    syncEngineForm();
  }
  $("footer").textContent = "仓库 " + (S.cfg.repo_commit || "") +
    " · 本页只显示本服务自己的数据库。当前回放用的是该次运行自己的模型路径，不是默认引擎。";

  await refresh();
  const hp = hashParams();
  const wanted = hp.run && S.runs.find((r) => r.run_id === hp.run);
  const first = wanted || S.runs.find((r) => r.status === "running") ||
    S.runs.find((r) => r.years_recorded > 0);
  if (hp.mode === "events") S.playMode = "events";
  if (hp.archive === "full") S.bandScope = "full";
  if (first) {
    await openRun(first.run_id);
    if (hp.mode === "events") setPlayMode("events", { silent: true, force: true });
    if (hp.t) {
      const parsed = OverviewLogic.parseStrictInt(hp.t, { name: "年份", min: 0 });
      if (parsed.ok) await gotoYear(parsed.value);
    }
    if (hp.event) {
      const ev = findEventByKey(hp.event, S.t);
      if (ev) await focusEvent(ev, { fromHash: true });
    }
    if (hp.b) selectBand(hp.b, { force: true, keepCell: !!S.selEvent });
    if (hp.view === "mem") setView("mem");
  } else {
    $("side-empty").textContent = "还没有任何运行记录。到“运行记录”页发起一次模拟。";
    renderOverview();
  }
  if (hp.tab) showTab(hp.tab);
  setInterval(refresh, 1500);
}

function applyCam() {
  const svg = $("map");
  if (svg) svg.setAttribute("viewBox", camViewBox());
}
function mapHitAt(clientX, clientY) {
  const el = document.elementFromPoint(clientX, clientY);
  let n = el;
  while (n && n !== document.body) {
    if (n.getAttribute) {
      const band = n.getAttribute("data-band");
      if (band) return { kind: "band", id: band };
      if (n.classList && n.classList.contains("cell") && n.getAttribute("data-cell") != null) {
        return { kind: "cell", i: +n.getAttribute("data-cell") };
      }
    }
    n = n.parentElement || n.parentNode;
  }
  return null;
}
function endMapPointer(e) {
  const drag = S._drag;
  S._drag = null;
  S._suppressClick = false;
  try {
    if (e && e.pointerId != null && $("mapbox") && $("mapbox").hasPointerCapture &&
        $("mapbox").hasPointerCapture(e.pointerId)) {
      $("mapbox").releasePointerCapture(e.pointerId);
    }
  } catch (err) { /* 已释放 */ }
  return drag;
}
function bindMapCam() {
  const box = $("mapbox"); if (!box) return;
  box.addEventListener("wheel", (e) => {
    e.preventDefault();
    const next = e.deltaY < 0 ? S.cam.k * 1.12 : S.cam.k / 1.12;
    S.cam.k = Math.max(0.7, Math.min(3.2, next));
    renderMap();
  }, { passive: false });
  box.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    S._drag = {
      x: e.clientX, y: e.clientY, cx: S.cam.x, cy: S.cam.y,
      moved: false, pointerId: e.pointerId
    };
  });
  box.addEventListener("pointermove", (e) => {
    if (!S._drag || S._drag.pointerId !== e.pointerId) return;
    const dx = e.clientX - S._drag.x, dy = e.clientY - S._drag.y;
    if (!S._drag.moved) {
      if (Math.abs(dx) + Math.abs(dy) <= 6) return;
      S._drag.moved = true;
      try { box.setPointerCapture(e.pointerId); } catch (err) { /* 忽略 */ }
    }
    S.cam.x = S._drag.cx + dx / S.cam.k;
    S.cam.y = S._drag.cy + dy / S.cam.k;
    applyCam();
  });
  box.addEventListener("pointerup", (e) => {
    const drag = endMapPointer(e);
    if (drag && drag.moved) {
      S._ignoreClickUntil = performance.now() + 80;
      return;
    }
    const hit = mapHitAt(e.clientX, e.clientY);
    if (hit && hit.kind === "band") selectBand(hit.id, { force: true });
    else if (hit && hit.kind === "cell") {
      S.selBand = null; S.selCell = hit.i; showRail("dossier"); renderMap(); renderSide();
    }
  });
  box.addEventListener("pointercancel", (e) => { endMapPointer(e); });
  box.addEventListener("lostpointercapture", () => {
    if (S._drag && !S._drag.moved) return;
  });
}

function applyParamChrome(engine, param, titleId, hintId, inputId) {
  const spec = engineParamMeta(engine, param);
  if (spec && $(titleId)) {
    const unit = spec.unit ? "（" + spec.unit + "）" : "";
    $(titleId).textContent = (spec.label || param) + unit;
  }
  if (spec && $(hintId)) {
    const bits = [];
    if (spec.min != null && spec.max != null) bits.push("范围 " + spec.min + "–" + spec.max);
    if (spec.default != null) bits.push("默认 " + spec.default);
    if (spec.unit) bits.push(spec.unit);
    if (bits.length) $(hintId).textContent = bits.join(" · ");
  }
  if (spec && $(inputId) && document.activeElement !== $(inputId) && !$(inputId).value) {
    $(inputId).value = String(spec.default != null ? spec.default : 0);
  }
}

function syncEngineForm() {
  if (!$("f-engine")) return;
  const name = $("f-engine").value;
  const shareWrap = $("f-share-wrap");
  const aidWrap = $("f-aid-wrap");
  const recipWrap = $("f-recip-wrap");
  if (shareWrap) shareWrap.hidden = !engineHasParam(name, "share_m");
  if (aidWrap) aidWrap.hidden = !engineHasParam(name, "aid_m");
  if (recipWrap) recipWrap.hidden = !engineHasParam(name, "recip_m");
  applyParamChrome(name, "share_m", "f-share-title", "f-share-hint", "f-share");
  applyParamChrome(name, "aid_m", "f-aid-title", "f-aid-hint", "f-aid");
  applyParamChrome(name, "recip_m", "f-recip-title", null, "f-recip");
  applyParamChrome(name, "sigma_m", null, null, "f-sigma");
  applyParamChrome(name, "move_mort_m", null, null, "f-mort");
  if (engineHasParam(name, "recip_m") && $("f-recip-hint")) {
    const spec = engineParamMeta(name, "recip_m");
    const range = spec ? ("范围 " + spec.min + "–" + spec.max + "，默认 " + spec.default + "。") : "";
    $("f-recip-hint").textContent = range +
      "0 = 关闭优先回助（合法对照）。1000 = 开启优先回助。repay 含碰巧；changed 才表示规则改变了分配。";
  }
}

function collectRunDraft() {
  const lim = S.cfg.limits;
  const seed = OverviewLogic.parseStrictInt($("f-seed").value, { name: "种子 seed", min: 0, max: lim.max_seed });
  const years = OverviewLogic.parseStrictInt($("f-years").value, { name: "年数 years", min: lim.min_years, max: lim.max_years });
  const sigma = OverviewLogic.parseStrictInt($("f-sigma").value, { name: "SIGMA_M", min: 0, max: 1000 });
  const mort = OverviewLogic.parseStrictInt($("f-mort").value, { name: "MOVE_MORT_M", min: 0, max: 1000 });
  for (const x of [seed, years, sigma, mort]) {
    if (!x.ok) return { ok: false, error: x.error };
  }
  const engine = $("f-engine") ? $("f-engine").value : (S.cfg.default_engine || "exp03");
  const known = S.cfg.engines ? Object.keys(S.cfg.engines) : [];
  if (known.length && known.indexOf(engine) < 0) return { ok: false, error: "未知引擎：" + engine };
  const body = {
    seed: seed.value, years: years.value, sigma_m: sigma.value,
    move_mort_m: mort.value, arm: $("f-arm").value, label: $("f-label").value.trim(),
    engine: engine,
  };
  const notes = [];
  if (engineHasParam(engine, "share_m")) {
    const share = OverviewLogic.parseStrictInt($("f-share").value, { name: "SHARE_M", min: 0, max: 1000 });
    if (!share.ok) return { ok: false, error: share.error };
    body.share_m = share.value;
  }
  if (engineHasParam(engine, "aid_m")) {
    const spec = engineParamMeta(engine, "aid_m") || { min: 0, max: 1000 };
    const aid = OverviewLogic.parseStrictInt($("f-aid").value, {
      name: (spec.label || "AID_M"), min: spec.min != null ? spec.min : 0,
      max: spec.max != null ? spec.max : 1000 });
    if (!aid.ok) return { ok: false, error: aid.error };
    body.aid_m = aid.value;
  }
  if (engineHasParam(engine, "recip_m")) {
    const spec = engineParamMeta(engine, "recip_m") || { min: 0, max: 1000 };
    const recip = OverviewLogic.parseStrictInt($("f-recip").value, {
      name: (spec.label || "RECIP_M"), min: spec.min != null ? spec.min : 0,
      max: spec.max != null ? spec.max : 1000 });
    if (!recip.ok) return { ok: false, error: recip.error };
    body.recip_m = recip.value;
    if ((body.aid_m || 0) <= 0 && recip.value > 0) {
      notes.push("优先回助需要 AID_M>0 才有预算。当前 AID_M=0，优先机制不会发生。未暗改 AID_M。");
    }
  }
  const lines = [
    "引擎 " + engine,
    "seed " + body.seed,
    "年数 " + body.years,
    "SIGMA_M " + body.sigma_m + "‰",
    "MOVE_MORT_M " + body.move_mort_m + "‰",
    body.share_m != null ? ("SHARE_M " + body.share_m + "‰") : "SHARE_M 此引擎无此参数",
    body.aid_m != null ? ("AID_M " + body.aid_m + "‰") : "AID_M 此引擎无此参数（缺指标不填 0）",
    body.recip_m != null ? ("RECIP_M " + body.recip_m + "‰") : "RECIP_M 此引擎无此参数",
    "信息条件 " + body.arm,
  ];
  return { ok: true, body: body, notes: notes, summary: lines.join(" · ") };
}
function applyForgePreset(name) {
  const engine = $("f-engine") ? $("f-engine").value : "";
  if (name === "none") {
    if ($("f-aid") && engineHasParam(engine, "aid_m")) $("f-aid").value = "0";
    if ($("f-recip") && engineHasParam(engine, "recip_m")) $("f-recip").value = "0";
  } else if (name === "aid") {
    if (!engineHasParam(engine, "aid_m")) { flash("当前引擎没有援助参数。", true); return; }
    $("f-aid").value = "1000";
    if ($("f-recip") && engineHasParam(engine, "recip_m")) $("f-recip").value = "0";
  } else if (name === "recip") {
    if (!engineHasParam(engine, "aid_m") || !engineHasParam(engine, "recip_m")) {
      flash("当前引擎不能同时开援助和优先回助。", true); return;
    }
    $("f-aid").value = "1000";
    $("f-recip").value = "1000";
  }
}
async function startRun() {
  const draft = collectRunDraft();
  if (!draft.ok) { flash(draft.error, true); return; }
  if ($("forge-confirm")) $("forge-confirm").hidden = false;
  if ($("forge-summary")) {
    $("forge-summary").innerHTML = `<p>${esc(draft.summary)}</p>` +
      (draft.notes.length ? `<p class="err">${esc(draft.notes.join(" "))}</p>` : "") +
      `<p class="muted">确认后才会提交。不会改已有世界。</p>`;
  }
  S._runDraft = draft.body;
}
async function confirmStartRun() {
  const body = S._runDraft;
  if (!body) { flash("请先核对参数。", true); return; }
  $("b-confirm").disabled = true;
  try {
    const r = await api("/api/runs", { method: "POST", body: JSON.stringify(body) });
    flash("已提交，运行号 " + r.run_id + "。计算在后台独立进程里进行，可以直接看进度。");
    S._runDraft = null;
    if ($("forge-confirm")) $("forge-confirm").hidden = true;
    await refresh(); await openRun(r.run_id);
    showTab("world");
  } catch (e) {
    flash("启动失败：" + e.message, true);
  } finally {
    if ($("b-confirm")) $("b-confirm").disabled = false;
  }
}

window.__obs = { S, api, esc, ykey, openRun, gotoYear, selectBand, refresh, renderRuns, boot, startRun, setLayer,
  setPlayMode, focusEvent, cancelFx, loadBand, gotoEventYear, stepEventYear, findEventByKey,
  bumpOp, opAlive, bandAccept, bandCacheKey, applyBandDossier, setPlaying, tickEvents, tick,
  navResult, beginYearLoad, endYearLoad, afterPlayStep, retryYear, reapNavUi, renderYearFailBar,
  pendingCurrentYear, PLAY_PENDING_MS, loadRelations, renderRelations, NetworkLogic,
  loadCompare, CompareLogic, fillCompareSelects, fetchYearOrMiss, showTab, showRail,
  collectRunDraft, applyForgePreset, confirmStartRun, LibraryLogic, renderLibrary,
  pinCurrentYear, pinCurrentEvent, exportCurrentRecord, jumpToRecordedEvent,
  clearRelEdgeCard, fillRelEdgeCard };

if (!window.__OBS_MANUAL_BOOT__) {
  boot().catch((e) => {
    $("statusline").innerHTML = `<span class="err">初始化失败：${esc(e.message)}</span>`;
  });
}

if (hashParams().diag === "1") {
  setTimeout(() => {
    const w = (sel) => { const n = document.querySelector(sel); return n ? Math.round(n.getBoundingClientRect().width) : -1; };
    document.title = `vw=${window.innerWidth} body=${w("body")} main=${w("main")} grid=${w(".worldgrid")} map=${w(".mapwrap")} svg=${w("#map")} hint=${w(".maphint")} side=${w(".side")} scroll=${document.documentElement.scrollWidth}`;
    const d = document.createElement("div");
    d.style.cssText = "position:fixed;bottom:0;left:0;background:#000;color:#0f0;font:11px monospace;z-index:999;padding:2px";
    d.textContent = document.title; document.body.appendChild(d);
  }, 1200);
}
