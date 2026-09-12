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
};
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
      OverviewLogic._appendAidLedger(sentences, input.aid);
      OverviewLogic._appendRecipLedger(sentences, input.recip);
      return { sentences, events: ev, births: births, demoDeaths: demo, migDeaths: md };
    }
    sentences.push("本年出生 " + births + " 人，非迁移死亡（模型的原规则死亡） " +
      demo + " 人，迁移死亡 " + md + " 人。");
    if (ev.total === 0) {
      sentences.push("本年没有记录到迁移、分裂、群体消失、信息交换或食物援助事件。");
    } else {
      sentences.push("记录到 " + ev.migrate + " 次迁移、" + ev.split +
        " 次群体分裂、" + ev.extinct + " 次群体消失、" + ev.share +
        " 次信息交换、" + ev.aid + " 条食物援助（逐笔转移）。");
    }
    sentences.push("当前共有 " + agg.bands + " 个群体、" + agg.pop + " 人。");
    if (input.ledgerMig != null && input.ledgerMig !== ev.migrate) {
      sentences.push("模型账本统计本年迁移 " + input.ledgerMig +
        " 次，已记录的迁移事件 " + ev.migrate +
        " 条；人数与事件条数不能混加，也不强行对齐。");
    }
    OverviewLogic._appendAidLedger(sentences, input.aid);
    OverviewLogic._appendRecipLedger(sentences, input.recip);
    return { sentences, events: ev, births: births, demoDeaths: demo, migDeaths: md };
  },
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
    bars += `<rect x="${x.toFixed(2)}" y="${(h - bh).toFixed(2)}" width="${Math.max(1, w / s.length - 0.4).toFixed(2)}" height="${bh.toFixed(2)}" fill="${hot ? "#d4b06a" : "rgba(111,179,124,.55)"}"/>`;
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
      } else if (e.type === "split" && e.parent && e.band) {
        a = bandPos[String(e.parent)]; b = bandPos[String(e.band)];
      }
      if (!a || !b) return;
      if (e.type === "aid" || e.type === "share") return;
      out += `<line x1="${a[0].toFixed(1)}" y1="${a[1].toFixed(1)}" x2="${b[0].toFixed(1)}" y2="${b[1].toFixed(1)}"
        class="flow-line" stroke="${col[e.type] || "#d4b06a"}"/>`;
    });
  }

  svg.innerHTML = out;
  svg.querySelectorAll(".band").forEach((n) =>
    n.addEventListener("click", (e) => {
      e.stopPropagation();
      if (S._suppressClick) { S._suppressClick = false; return; }
      selectBand(n.dataset.band);
    }));
  svg.querySelectorAll(".cell").forEach((n) => {
    n.addEventListener("click", () => {
      if (S._suppressClick) { S._suppressClick = false; return; }
      S.selCell = +n.dataset.cell; S.selBand = null; renderMap(); renderSide();
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
  const m = String(eid || "").match(/^t(\d+)-/);
  return m ? Number(m[1]) : null;
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
    const last = (e.last_year === null || e.last_year === undefined)
      ? "时间未记录" : ("最近第 " + e.last_year + " 年");
    const jump = (e.last_year === null || e.last_year === undefined)
      ? `<span>${esc(bandName(rec, id))}</span>`
      : `<button type="button" class="prior-jump" data-prior-year="${e.last_year}">${esc(bandName(rec, id))}</button>`;
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
    selWrap.innerHTML = `<div class="gone-note">该群体在第 ${S.t} 年不在世，不把它画在地图上。
      下面是已保存的历史记录，不是当前地图上的位置。</div>
      <div id="bandmore" class="muted" style="margin-top:8px">正在读取历史记录…</div>`;
    loadBand(S.selBand);
    return;
  }
  h.textContent = "选中群体";
  const known = Object.keys(b.mem).length;
  selWrap.innerHTML = `<div class="kv">
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
  loadBand(b.id);
}

async function loadBand(id) {
  if (!S.run) return;
  const myRun = S.run.run_id, myEpoch = S.epoch, myBand = id;
  try {
    const d = await api(`/api/runs/${myRun}/band/${id}`);
    if (stale(myEpoch, myRun) || S.selBand !== myBand) return;
    S.band = d;
    const box = $("bandmore"); if (!box) return;
    const traj = d.trajectory.map((p) => `第${p[0]}年→${p[1]}号格`).join("，");
    const gone = d.extinct_at !== null
      ? `（第 ${d.extinct_at} 年被移除，当年不在地图上）` : "";
    box.innerHTML = `<div><b>来源</b>：${esc(d.origin)}</div>
      <div><b>存续</b>：第 ${d.first_seen} 年 至 第 ${d.last_seen} 年 ${gone}</div>
      <div><b>分裂出</b>：${d.children.length
        ? d.children.map((p) => `第${p[0]}年 ${esc(String(p[1]).slice(0, 8))}…`).join("，") : "无记录"}</div>
      <div><b>迁移轨迹</b>：${esc(traj)}</div>
      <div style="margin-top:4px">${esc(d.source)}</div>`;
  } catch (e) {
    if (stale(myEpoch, myRun) || S.selBand !== myBand) return;
    const box = $("bandmore");
    if (box) box.innerHTML = `<span class="err">轨迹读取失败：${esc(e.message)}</span>`;
  }
}

function selectBand(id, opts) {
  opts = opts || {};
  bump();
  S.band = null;
  if (!opts.force && S.selBand === id) S.selBand = null;
  else S.selBand = id || null;
  setHash({ b: S.selBand || "" });
  S.selCell = null;
  if (!S.selBand && S.view === "mem") setView("truth");
  renderMap(); renderSide();
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
  const el = $("year-load");
  if (!el) return;
  if (on) {
    S.yearLoading = t;
    el.hidden = false;
    if ($("year-load-n")) $("year-load-n").textContent = String(t);
  } else {
    S.yearLoading = null;
    el.hidden = true;
  }
}
function commitYear(t) {
  S.t = t;
  S.yearWait = null;
  setYearLoadOverlay(t, false);
  syncYearWidgets(t);
  setHash({ t: String(t) });
}
async function gotoYear(t, opts) {
  opts = opts || {};
  if (!S.run) return;
  const myRun = S.run.run_id;
  const myEpoch = bump();
  t = Math.max(0, Math.min(t, maxT()));
  if (S.years.has(ykey(myRun, t))) {
    if (stale(myEpoch, myRun)) return;
    commitYear(t);
    renderOverview(); renderMap(); renderSide(); renderStatus(); renderEvents(); renderTech();
    if (!opts.quiet) renderCharts();
    if (S.evScope === "until") prefetchYears(myRun, t);
    return;
  }
  setYearLoadOverlay(t, true);
  let rec;
  try { rec = await api(`/api/runs/${myRun}/year/${t}`); }
  catch (e) {
    if (stale(myEpoch, myRun)) return;
    const pending = isPendingYearError(e, t);
    S.yearWait = { runId: myRun, t: t, pending: pending, status: e.status, message: e.message };
    commitYear(t);
    if (!pending) flash("读取第 " + t + " 年失败：" + e.message, true);
    renderOverview(); renderMap(); renderSide(); renderStatus(); renderEvents();
    return;
  }
  S.years.set(ykey(myRun, t), rec);
  delete S.yearMiss[yearMissKey(myRun, t)];
  if (stale(myEpoch, myRun)) return;
  commitYear(t);
  renderOverview(); renderMap(); renderSide(); renderStatus(); renderEvents(); renderTech();
  if (!opts.quiet) renderCharts();
  if (S.evScope === "until") prefetchYears(myRun, t);
}
function tick() {
  if (!S.playing) return;
  if (S.t >= maxT()) {
    if (S.run && (S.run.status === "running" || S.run.status === "queued")) {
      $("tl-note").textContent = "已经放到最新算出来的一年，等后台继续计算…";
      S.timer = setTimeout(tick, 700); return;
    }
    setPlaying(false); return;
  }
  gotoYear(S.t + 1, { quiet: true }).then(() => {
    renderCharts();
    S.timer = setTimeout(tick, Math.max(60, 600 / S.speed));
  });
}
function setPlaying(v) {
  S.playing = v;
  $("b-play").textContent = v ? "⏸ 暂停" : "▶ 播放历史";
  $("tl-note").textContent = v ? "回放中（只读已保存的记录）"
    : "回放只读取已保存的记录，不会重新计算世界。";
  clearTimeout(S.timer);
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
  if ($("ev-load-note")) $("ev-load-note").textContent = loadNote;

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
        const remY = e.basis.remembered_last_year;
        basis = `<div class="src basis-row">依据：${esc(e.basis.why || "未记录")}` +
          (e.basis.remembered_kcal != null ? ` · 援助前记住 ${nf(e.basis.remembered_kcal)} kcal` : "") +
          (remY == null ? "" : ` · 最近受助于第 ${remY} 年`) +
          (priors ? `<div class="prior-row">跳转 ${priors}</div>` : " · 先前事件未记录") + `</div>`;
      }
      const cls = [e.type, e.repay ? "repay" : "", e.phase === "recip" ? "phase-recip" : ""]
        .filter(Boolean).join(" ");
      return `<div class="ev ${esc(cls)}" data-t="${e.t}"
        data-band="${esc(e.band || e.receiver || "")}" data-to="${e.to != null ? e.to : ""}"
        data-from="${e.from != null ? e.from : ""}" data-cell="${e.cell != null ? e.cell : ""}">
        <div><span class="when">${e.t === 0 ? "开局" : "第 " + e.t + " 年"}</span>
          ${badges.join(" ")} ${esc(TYPE_LABEL(e.type))} · ${esc(e.text)}</div>
        <div class="src">来源：${esc(e.source || "未标注")}${e.unrecorded
          ? "　·　未记录：" + esc(e.unrecorded) : ""}</div>${basis}
      </div>`;
    }).join("");
    box.querySelectorAll(".ev").forEach((n) => n.addEventListener("click", (ev) => {
      if (ev.target.closest(".prior-jump, .prior-row, [data-prior-year]")) return;
      jumpToEvent({
        t: +n.dataset.t,
        band: n.dataset.band || null,
        to: n.dataset.to === "" ? null : +n.dataset.to,
        from: n.dataset.from === "" ? null : +n.dataset.from,
        cell: n.dataset.cell === "" ? null : +n.dataset.cell,
      });
    }));
    box.querySelectorAll(".prior-jump").forEach((n) => {
      const go = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        const y = +n.dataset.priorYear;
        if (Number.isFinite(y)) gotoYear(y);
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
    $("bandtable").innerHTML = head + rec.bands.map((b) => `<tr data-b="${esc(b.id)}"
        class="${S.selBand === b.id ? "on" : ""}"><td class="clickable">${esc(b.name)}</td>
        <td>${nf(b.size)}人</td><td>${py(b.store)}</td><td>${b.cell}</td>
        <td>${esc(S.map.cells[b.cell].region)}</td><td>${Object.keys(b.mem).length}</td></tr>`).join("");
    $("bandtable").querySelectorAll("tr[data-b]").forEach((n) =>
      n.addEventListener("click", () => { selectBand(n.dataset.b, { force: true }); showTab("world"); }));
  }
}

function jumpToEvent(ev) {
  setPlaying(false);
  showTab("world");
  gotoYear(ev.t).then(() => {
    if (ev.to != null) S.selCell = ev.to;
    else if (ev.from != null) S.selCell = ev.from;
    else if (ev.cell != null && ev.cell !== "") S.selCell = +ev.cell;
    if (ev.band) selectBand(ev.band, { force: true });
    else { renderMap(); renderSide(); }
  });
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
}

async function openRun(id) {
  const myEpoch = bump();
  setPlaying(false);
  let run, ser;
  try {
    run = await api(`/api/runs/${id}`);
    if (S.epoch !== myEpoch) return;
    ser = await api(`/api/runs/${id}/series`);
    if (S.epoch !== myEpoch) return;
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
  setHash({ run: id, b: "", view: "", t: "0" });
  renderOverview(); renderMap(); renderSide(); renderEvents(); renderStatus();
  await gotoYear(0);
  renderRuns(); renderCharts(); renderStatus(); renderOverview();
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
  if (["world", "metrics", "runs", "progress"].indexOf(name) < 0) name = "world";
  ["world", "metrics", "events", "runs", "progress"].forEach((t) => {
    const el = $("tab-" + t); if (el) el.hidden = t !== name;
  });
  document.querySelectorAll("#tabs button, .hud-actions [data-tab]").forEach((b) =>
    b.classList.toggle("on", b.dataset.tab === name));
  setHash({ tab: name });
  if (name === "metrics") renderCharts();
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
  $("b-next").addEventListener("click", () => { setPlaying(false); gotoYear(S.t + 1); });
  $("b-prev").addEventListener("click", () => { setPlaying(false); gotoYear(S.t - 1); });
  $("b-home").addEventListener("click", () => { setPlaying(false); gotoYear(0); });
  $("speed").addEventListener("change", (e) => { S.speed = +e.target.value; });
  $("scrub").addEventListener("input", (e) => { setPlaying(false); gotoYear(+e.target.value); });
  $("b-start").addEventListener("click", startRun);
  if ($("recip-off")) $("recip-off").addEventListener("click", () => { $("f-recip").value = "0"; });
  if ($("recip-on")) $("recip-on").addEventListener("click", () => { $("f-recip").value = "1000"; });
  const railTabs = $("rail-tabs");
  if (railTabs) railTabs.addEventListener("click", (e) => {
    const b = e.target.closest("[data-rail]"); if (!b) return;
    document.querySelectorAll("#rail-tabs button").forEach((x) => x.classList.toggle("on", x === b));
    ["chronicle", "dossier", "help"].forEach((name) => {
      const pane = $("pane-" + name); if (!pane) return;
      const on = name === b.dataset.rail;
      pane.hidden = !on;
      pane.classList.toggle("on", on);
    });
  });
  document.addEventListener("keydown", (e) => {
    const tag = (e.target && e.target.tagName) || "";
    if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
    if (e.key === "ArrowLeft") { e.preventDefault(); setPlaying(false); gotoYear(S.t - 1); }
    else if (e.key === "ArrowRight") { e.preventDefault(); setPlaying(false); gotoYear(S.t + 1); }
    else if (e.key === "Home") { e.preventDefault(); setPlaying(false); gotoYear(0); }
    else if (e.key === " " || e.code === "Space") { e.preventDefault(); setPlaying(!S.playing); }
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
  if (first) {
    await openRun(first.run_id);
    if (hp.t) {
      const parsed = OverviewLogic.parseStrictInt(hp.t, { name: "年份", min: 0 });
      if (parsed.ok) await gotoYear(parsed.value);
    }
    if (hp.b) selectBand(hp.b, { force: true });
    if (hp.view === "mem") setView("mem");
  } else {
    $("side-empty").textContent = "还没有任何运行记录。到“运行记录”页发起一次模拟。";
    renderOverview();
  }
  if (hp.tab) showTab(hp.tab);
  setInterval(refresh, 1500);
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
    S._drag = { x: e.clientX, y: e.clientY, cx: S.cam.x, cy: S.cam.y, moved: false };
    box.setPointerCapture(e.pointerId);
  });
  box.addEventListener("pointermove", (e) => {
    if (!S._drag) return;
    const dx = e.clientX - S._drag.x, dy = e.clientY - S._drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 4) S._drag.moved = true;
    S.cam.x = S._drag.cx + dx / S.cam.k;
    S.cam.y = S._drag.cy + dy / S.cam.k;
    renderMap();
  });
  box.addEventListener("pointerup", () => {
    if (S._drag && S._drag.moved) S._suppressClick = true;
    S._drag = null;
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

async function startRun() {
  const lim = S.cfg.limits;
  const seed = OverviewLogic.parseStrictInt($("f-seed").value, { name: "种子 seed", min: 0, max: lim.max_seed });
  const years = OverviewLogic.parseStrictInt($("f-years").value, { name: "年数 years", min: lim.min_years, max: lim.max_years });
  const sigma = OverviewLogic.parseStrictInt($("f-sigma").value, { name: "SIGMA_M", min: 0, max: 1000 });
  const mort = OverviewLogic.parseStrictInt($("f-mort").value, { name: "MOVE_MORT_M", min: 0, max: 1000 });
  for (const x of [seed, years, sigma, mort]) {
    if (!x.ok) { flash(x.error, true); return; }
  }
  const engine = $("f-engine") ? $("f-engine").value : (S.cfg.default_engine || "exp03");
  let share_m = 0;
  if (engineHasParam(engine, "share_m")) {
    const share = OverviewLogic.parseStrictInt($("f-share").value, { name: "SHARE_M", min: 0, max: 1000 });
    if (!share.ok) { flash(share.error, true); return; }
    share_m = share.value;
  }
  let aid_m = 0;
  if (engineHasParam(engine, "aid_m")) {
    const spec = engineParamMeta(engine, "aid_m") || { min: 0, max: 1000 };
    const aid = OverviewLogic.parseStrictInt($("f-aid").value, {
      name: (spec.label || "AID_M"), min: spec.min != null ? spec.min : 0,
      max: spec.max != null ? spec.max : 1000 });
    if (!aid.ok) { flash(aid.error, true); return; }
    aid_m = aid.value;
  }
  let recip_m = 0;
  let sendRecip = false;
  if (engineHasParam(engine, "recip_m")) {
    const spec = engineParamMeta(engine, "recip_m") || { min: 0, max: 1000 };
    const recip = OverviewLogic.parseStrictInt($("f-recip").value, {
      name: (spec.label || "RECIP_M"), min: spec.min != null ? spec.min : 0,
      max: spec.max != null ? spec.max : 1000 });
    if (!recip.ok) { flash(recip.error, true); return; }
    recip_m = recip.value;
    sendRecip = true;
  }
  const body = {
    seed: seed.value, years: years.value, sigma_m: sigma.value,
    move_mort_m: mort.value, arm: $("f-arm").value, label: $("f-label").value.trim(),
    engine: engine, share_m: share_m, aid_m: aid_m,
  };
  if (sendRecip) body.recip_m = recip_m;
  $("b-start").disabled = true;
  try {
    const r = await api("/api/runs", { method: "POST", body: JSON.stringify(body) });
    flash("已提交，运行号 " + r.run_id + "。计算在后台独立进程里进行，可以直接看进度。");
    await refresh(); await openRun(r.run_id);
    showTab("world");
  } catch (e) {
    flash("启动失败：" + e.message, true);
  } finally {
    $("b-start").disabled = false;
  }
}

window.__obs = { S, api, esc, ykey, openRun, gotoYear, selectBand, refresh, renderRuns, boot, startRun, setLayer };

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
