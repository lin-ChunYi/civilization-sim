/* 文明观察台 OBS-01 —— 前端。
   原则：回放只读已保存的记录；一切数字都来自后台的原始整数账，前端只做单位换算与显示。 */
"use strict";

const S = {
  token: sessionStorage.getItem("obs_token") || "",
  cfg: null, map: null, run: null, meta: null, series: [], years: new Map(),
  runs: [], t: 0, playing: false, speed: 1, view: "truth", selBand: null, selCell: null,
  timer: null, band: null,
};
const $ = (id) => document.getElementById(id);
/* 允许用地址栏定位：#tab=metrics&run=<id>&t=60&b=<band id>，便于分享与自动化检查 */
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
  const str = Object.entries(h).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join("&");
  history.replaceState(null, "", "#" + str);
}
const NEED = () => (S.cfg ? S.cfg.engine.constants.NEED_PC : 730000);

/* ---------------- 工具 ---------------- */
const nf = (x) => (x === null || x === undefined ? "—" : Number(x).toLocaleString("zh-CN"));
function py(kcal, digits = 1) {           // kcal -> 人年口粮
  if (kcal === null || kcal === undefined) return "—";
  return (kcal / NEED()).toFixed(digits);
}
function kcalCell(kcal) {
  return `${py(kcal)} <small>人年口粮 / ${nf(kcal)} kcal</small>`;
}
function pct(num, den, digits = 3) {      // 分母为 0 一律“不适用”，不伪造 0%
  if (!den) return `<span class="muted">不适用（分母为 0）</span>`;
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
  const [txt, cls] = STATUS_TEXT[st] || [st, "s-off"];
  return `<span class="badge ${cls}">${txt}</span>`;
}

/* ---------------- API ---------------- */
async function api(path, opts = {}) {
  const h = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
  if (S.token) h["X-Observer-Token"] = S.token;
  const r = await fetch(path, Object.assign({}, opts, { headers: h }));
  if (!r.ok) {
    let detail = `HTTP ${r.status}`;
    try { detail = (await r.json()).detail || detail; } catch (e) { /* 忽略 */ }
    const err = new Error(detail); err.status = r.status; throw err;
  }
  return r.json();
}

/* ---------------- 顶部状态条 ---------------- */
function renderStatus() {
  const box = $("statusline");
  if (!S.cfg) { box.textContent = "正在连接后台…"; return; }
  const parts = [];
  if (S.run) {
    parts.push(`<b>当前运行</b> ${S.run.label || S.run.run_id} ${statusBadge(S.run.status)}` +
      (S.run.kind === "preset" ? ` <span class="badge s-off">预生成案例</span>` : ""));
    parts.push(`<b>参数</b> seed=${S.run.seed} · years=${S.run.years} · SIGMA_M=${S.run.sigma_m}‰ ·
                MOVE_MORT_M=${S.run.move_mort_m}‰ · ${S.cfg.arms[S.run.arm].label}`);
    parts.push(`<b>计算进度</b> ${S.run.years_recorded ?? S.run.years_done}/${S.run.years} 年`);
    parts.push(`<b>回放</b> 第 ${S.t} 年`);
  } else {
    parts.push("尚未选择运行");
  }
  parts.push(`<b>模型</b> ${S.cfg.engine.engine_path} @ ${S.cfg.engine.baseline_commit}
              · sha256 ${S.cfg.engine.engine_sha256.slice(0, 12)}`);
  box.innerHTML = parts.join(" ");
}

/* ---------------- 地图 ---------------- */
const R = 36, SQ3 = Math.sqrt(3);
function hexPath(cx, cy) {
  let d = "";
  for (let k = 0; k < 6; k++) {
    const a = Math.PI / 180 * (60 * k - 90);
    d += (k ? "L" : "M") + (cx + R * Math.cos(a)).toFixed(1) + "," + (cy + R * Math.sin(a)).toFixed(1);
  }
  return d + "Z";
}
function cellCenter(c) {
  const x = 40 + (c.col + (c.row % 2 === 0 ? 0.5 : 0)) * SQ3 * R + SQ3 * R / 2;
  const y = 40 + c.row * 1.5 * R + R;
  return [x, y];
}
function ramp(f) {                      // 0..1 -> 浅到深的绿
  f = Math.max(0, Math.min(1, f));
  const a = [246, 249, 244], b = [30, 94, 60];
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * f)).join(",")})`;
}
function renderMap() {
  const svg = $("map");
  if (!S.map || !S.run) { svg.innerHTML = ""; return; }
  const rec = S.years.get(S.t);
  if (!rec) { svg.innerHTML = `<text x="20" y="40" fill="#6b7280">正在读取第 ${S.t} 年…</text>`; return; }
  const cap = S.meta ? S.meta.cap : null;
  const memBand = S.view === "mem" && S.selBand
    ? rec.bands.find((b) => b.id === S.selBand) : null;

  let out = `<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse"
      patternTransform="rotate(45)"><rect width="6" height="6" fill="#e6e6e2"/>
      <line x1="0" y1="0" x2="0" y2="6" stroke="#c9c9c4" stroke-width="2.5"/></pattern></defs>`;

  const byCell = {};
  rec.bands.forEach((b) => { (byCell[b.cell] = byCell[b.cell] || []).push(b); });

  S.map.cells.forEach((c, idx) => {
    const [cx, cy] = cellCenter(c);
    let fill = "url(#hatch)", label = "", sub = "";
    if (c.passable) {
      const capv = cap ? cap[idx] : 0;
      if (memBand) {
        const e = memBand.mem[String(c.i)];
        if (!e) { fill = "#eceae6"; label = "未知"; }
        else {
          fill = ramp(capv ? e[0] / capv : 0);
          const age = S.t - (e[1] === null ? 0 : e[1]);
          label = py(e[0], 0);
          sub = age > 0 ? `${age} 年前` : "当年";
        }
      } else {
        fill = ramp(capv ? rec.stock[idx] / capv : 0);
        label = py(rec.stock[idx], 0);
        sub = capv ? Math.round(rec.stock[idx] / capv * 100) + "% 容量" : "";
      }
    }
    const selected = S.selCell === c.i;
    out += `<path d="${hexPath(cx, cy)}" fill="${fill}" stroke="${selected ? "#1f2937" : "#cfd2cd"}"
        stroke-width="${selected ? 2.6 : 1}" data-cell="${c.i}" class="cell"/>`;
    if (c.passable) {
      const dark = fill.startsWith("rgb") &&
        (parseInt(fill.slice(4).split(",")[1]) < 150);
      const ink = dark ? "#eef5ef" : "#4b534e";
      out += `<text x="${cx}" y="${cy - 19}" text-anchor="middle" font-size="9.5"
          fill="${ink}" opacity="0.85" pointer-events="none">${c.i}</text>`;
      out += `<text x="${cx}" y="${cy + 14}" text-anchor="middle" font-size="10.5"
          fill="${ink}" pointer-events="none">${label}</text>`;
      if (sub) out += `<text x="${cx}" y="${cy + 24}" text-anchor="middle" font-size="8"
          fill="${ink}" opacity="0.8" pointer-events="none">${sub}</text>`;
    }
  });

  // 群体：同格多个时排成一行分开摆放，互不遮挡，也不压住格子的数值标签
  S.map.cells.forEach((c) => {
    const list = byCell[c.i]; if (!list) return;
    const [cx, cy] = cellCenter(c);
    const n = list.length;
    const rCap = (56 - 2 * (n - 1)) / (2 * n);      // 一行放得下的最大半径
    const rads = list.map((b) =>
      Math.min(rCap, Math.max(5, 4.2 + Math.sqrt(Math.max(b.size, 1)) * 1.4)));
    const total = rads.reduce((a, r) => a + 2 * r, 0) + (n - 1) * 2;
    let x0 = cx - total / 2;
    list.forEach((b, k) => {
      const rad = rads[k];
      const x = x0 + rad, y = cy - 7;
      x0 += 2 * rad + 2;
      const on = S.selBand === b.id;
      out += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${rad.toFixed(1)}"
          fill="${on ? "#b45309" : "#8a5a2b"}" fill-opacity="0.93"
          stroke="${on ? "#fff8e8" : "#fdfaf4"}" stroke-width="${on ? 2.4 : 1.5}"
          data-band="${b.id}" class="band" style="cursor:pointer"><title>${b.name} · ${b.size} 人</title></circle>`;
      if (rad >= 7.5) {
        out += `<text x="${x.toFixed(1)}" y="${(y + 3.4).toFixed(1)}" text-anchor="middle"
            font-size="${rad >= 10 ? 10 : 8.5}" fill="#fff" pointer-events="none">${b.size}</text>`;
      }
    });
  });
  svg.innerHTML = out;
  svg.querySelectorAll(".band").forEach((n) =>
    n.addEventListener("click", (e) => { e.stopPropagation(); selectBand(n.dataset.band); }));
  svg.querySelectorAll(".cell").forEach((n) =>
    n.addEventListener("click", () => { S.selCell = +n.dataset.cell; renderMap(); renderSide(); }));

  $("legend").innerHTML = memBand
    ? `记忆视图（${memBand.name}）：<span class="bar"></span> 记得的存量少 → 多 ·
       <span style="background:#eceae6;padding:1px 6px;border-radius:3px">未知</span> ·
       灰斜纹 = 不可通行`
    : `真实资源：<span class="bar"></span> 存量少 → 多 · 灰斜纹 = 不可通行 ·
       棕色圆点 = 群体（数字为人口）`;
  $("maphint").innerHTML = memBand
    ? `记忆视图只替换<b>资源读数</b>；群体位置画的仍是世界真实位置，不代表该群体知道别人在哪。
       格内第二行是记忆的年龄（按模型的 <code>memt</code> 时间戳算）。
       <b>注意模型的既有口径</b>：群体自己所在格的存量每年都会刷新，但时间戳只在侦察或迁入时更新，
       所以本格可能显示成“若干年前”。观察台如实显示，不替模型修正。`
    : `点击格子看它的资源与占用；点击群体看详情。同格多个群体分开摆放，互不遮挡。`;
}

/* ---------------- 侧栏 ---------------- */
function renderSide() {
  const rec = S.years.get(S.t);
  $("side-empty").hidden = !!rec;
  $("side-body").hidden = !rec;
  if (!rec) return;
  $("side-year").textContent = S.t;
  const y = rec.year, cum = rec.cum, agg = rec.agg;
  const rows = [
    ["总人口", `${nf(agg.pop)} <small>人</small>`],
    ["群体数", `${nf(agg.bands)} <small>个</small>`],
    ["野外资源存量", kcalCell(agg.stock_total)],
    ["群体储粮", kcalCell(agg.store_total)],
    ["当年出生", `${nf(y.births_cum)} <small>人</small>`],
    ["当年原规则死亡", `${nf(y.deaths_demo_cum)} <small>人</small>`],
    ["当年迁移死亡", `${nf(y.mig_deaths_cum)} <small>人</small>`],
    ["当年迁移次数", `${nf(y.mig_total)} <small>次</small>`],
    ["当年缺粮 / 需求", pct(y.deficit_cum, y.need_cum)],
    ["当年迁移误判率", y.mig_total ? pct(y.mig_regret, y.mig_total, 1) :
      `<span class="muted">不适用（当年迁移 0 次）</span>`],
  ];
  $("side-now").innerHTML = rows.map(([k, v]) =>
    `<div class="k">${k}</div><div class="v">${v}</div>`).join("");
  const crows = [
    ["累计出生", `${nf(cum.births_cum)} <small>人</small>`],
    ["累计原规则死亡", `${nf(cum.deaths_demo_cum)} <small>人</small>`],
    ["累计迁移死亡", `${nf(cum.mig_deaths_cum)} <small>人</small>`],
    ["累计迁移次数", `${nf(cum.mig_total)} <small>次</small>`],
    ["累计缺粮 / 需求", pct(cum.deficit_cum, cum.need_cum)],
    ["累计人年", `${nf(cum.personyear_cum)} <small>人年</small>`],
    ["累计吃掉", kcalCell(cum.out_eat)],
    ["累计腐损", kcalCell(cum.out_spoil)],
  ];
  $("side-cum").innerHTML = crows.map(([k, v]) =>
    `<div class="k">${k}</div><div class="v">${v}</div>`).join("");
  const ok = (v) => v === 0 ? `<span style="color:var(--ok)">0 ✓</span>` : `<span class="err">${v} ✗</span>`;
  $("side-int").innerHTML =
    `<div class="k">能量守恒误差</div><div class="v">${ok(rec.integrity.conservation_error)}</div>
     <div class="k">人口恒等误差</div><div class="v">${ok(rec.integrity.population_identity_error)}</div>
     <div class="k">状态哈希</div><div class="v"><small>${rec.integrity.state_hash.slice(0, 16)}…</small></div>`;

  const selWrap = $("side-sel"), h = $("side-sel-h");
  if (S.selCell !== null && S.selBand === null) {
    const c = S.map.cells[S.selCell];
    const here = rec.bands.filter((b) => b.cell === S.selCell);
    h.hidden = false; h.textContent = `第 ${S.selCell} 号格`;
    selWrap.innerHTML = `<div class="kv">
      <div class="k">位置</div><div class="v">第 ${c.row} 行 第 ${c.col} 列 · 区块 ${c.region}</div>
      <div class="k">可通行</div><div class="v">${c.passable ? "是" : "否（屏障列）"}</div>
      <div class="k">当年存量</div><div class="v">${kcalCell(rec.stock[S.selCell])}</div>
      <div class="k">容量上限</div><div class="v">${S.meta ? kcalCell(S.meta.cap[S.selCell]) : "—"}</div>
      <div class="k">年再生基准</div><div class="v">${S.meta ? kcalCell(S.meta.regen[S.selCell]) : "—"}</div>
      <div class="k">邻格</div><div class="v">${c.neighbors.join("、") || "无"}</div>
      </div>
      <div class="muted" style="margin-top:6px">格上群体：${here.length
        ? here.map((b) => `<span class="link" data-b="${b.id}">${b.name}(${b.size}人)</span>`).join("、")
        : "无"}</div>`;
    selWrap.querySelectorAll("[data-b]").forEach((n) =>
      n.addEventListener("click", () => selectBand(n.dataset.b)));
    return;
  }
  if (!S.selBand) { h.hidden = true; selWrap.innerHTML = ""; return; }
  const b = rec.bands.find((x) => x.id === S.selBand);
  h.hidden = false; h.textContent = "选中群体";
  if (!b) {
    selWrap.innerHTML = `<div class="note">该群体在第 ${S.t} 年不在世。
      ${S.band && S.band.extinct_at !== null ? `它在第 ${S.band.extinct_at} 年人口归零后被移除。` : ""}</div>`;
    return;
  }
  const known = Object.keys(b.mem).length;
  selWrap.innerHTML = `<div class="kv">
    <div class="k">名称</div><div class="v">${b.name}</div>
    <div class="k">实体 id</div><div class="v"><small>${b.id}</small></div>
    <div class="k">人口</div><div class="v">${nf(b.size)} <small>人</small></div>
    <div class="k">储粮</div><div class="v">${kcalCell(b.store)}</div>
    <div class="k">位置</div><div class="v">第 ${b.cell} 号格（区块 ${S.map.cells[b.cell].region}）</div>
    <div class="k">记忆条目</div><div class="v">${known} <small>格</small></div>
    <div class="k">迁移死亡累加器</div><div class="v">${b.macc} <small>/1000</small></div>
  </div>
  <div id="bandmore" class="muted" style="margin-top:8px">正在读取轨迹…</div>`;
  loadBand(b.id);
}

async function loadBand(id) {
  try {
    const d = await api(`/api/runs/${S.run.run_id}/band/${id}`);
    S.band = d;
    const box = $("bandmore"); if (!box) return;
    const traj = d.trajectory.map(([t, c]) => `第${t}年→${c}号格`).join("，");
    box.innerHTML = `<div><b>来源</b>：${d.origin}</div>
      <div><b>存续</b>：第 ${d.first_seen} 年 至 第 ${d.last_seen} 年
        ${d.extinct_at !== null ? `（第 ${d.extinct_at} 年被移除）` : ""}</div>
      <div><b>分裂出</b>：${d.children.length
        ? d.children.map(([t, c]) => `第${t}年 ${c.slice(0, 8)}…`).join("，") : "无记录"}</div>
      <div><b>迁移轨迹</b>：${traj}</div>
      <div style="margin-top:4px">${d.source}</div>`;
  } catch (e) {
    const box = $("bandmore"); if (box) box.innerHTML = `<span class="err">轨迹读取失败：${e.message}</span>`;
  }
}

function selectBand(id) {
  S.selBand = (S.selBand === id ? null : id);
  setHash({ b: S.selBand || "" });
  S.selCell = null;
  if (!S.selBand && S.view === "mem") setView("truth");
  renderMap(); renderSide();
}
function setView(v) {
  if (v === "mem" && !S.selBand) { flash("先点一个群体，才能看它记忆里的世界。"); return; }
  S.view = v;
  setHash({ view: v === "mem" ? "mem" : "" });
  $("v-truth").classList.toggle("on", v === "truth");
  $("v-mem").classList.toggle("on", v === "mem");
  renderMap();
}

/* ---------------- 时间轴 ---------------- */
function maxT() { return Math.max(0, (S.run ? (S.run.years_recorded ?? 0) : 0)); }
async function gotoYear(t, opts = {}) {
  t = Math.max(0, Math.min(t, maxT()));
  S.t = t;
  $("scrub").value = t; $("scrub-year").textContent = t; $("ev-year").textContent = t;
  $("tl-play").textContent = `正在回放：第 ${t} 年`;
  if (!S.years.has(t)) {
    try { S.years.set(t, await api(`/api/runs/${S.run.run_id}/year/${t}`)); }
    catch (e) { flash("读取第 " + t + " 年失败：" + e.message); return; }
  }
  renderMap(); renderSide(); renderStatus(); renderEvents();
  setHash({ t: String(t) });
  if (!opts.quiet) renderCharts();
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
  $("b-play").textContent = v ? "⏸ 暂停" : "▶ 播放";
  $("tl-note").textContent = v ? "回放中（只读已保存的记录）"
    : "回放只读取已保存的记录，不会重新计算世界。";
  clearTimeout(S.timer);
  if (v) tick();
}

/* ---------------- 曲线与逐年表 ---------------- */
function lineChart(title, series, key, color, conv) {
  const w = 320, h = 120, pad = 26;
  if (!series.length) return "";
  const vals = series.map(key);
  const mx = Math.max(...vals, 1), mn = Math.min(...vals, 0);
  const X = (i) => pad + i * (w - pad - 6) / Math.max(series.length - 1, 1);
  const Y = (v) => h - 18 - (v - mn) / Math.max(mx - mn, 1) * (h - 30);
  const d = vals.map((v, i) => (i ? "L" : "M") + X(i).toFixed(1) + "," + Y(v).toFixed(1)).join("");
  const cx = X(Math.min(S.t, series.length - 1));
  return `<div class="chart"><h4>${title}</h4>
    <svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto">
      <path d="${d}" fill="none" stroke="${color}" stroke-width="1.8"/>
      <line x1="${cx}" y1="8" x2="${cx}" y2="${h - 18}" stroke="#b45309" stroke-dasharray="3 3"/>
      <text x="2" y="14" font-size="9" fill="#6b7280">${conv(mx)}</text>
      <text x="2" y="${h - 20}" font-size="9" fill="#6b7280">${conv(mn)}</text>
      <text x="${pad}" y="${h - 4}" font-size="9" fill="#6b7280">0</text>
      <text x="${w - 20}" y="${h - 4}" font-size="9" fill="#6b7280">${series.length - 1}</text>
    </svg></div>`;
}
function renderCharts() {
  if ($("tab-metrics").hidden) return;
  const s = S.series;
  $("charts").innerHTML =
    lineChart("总人口（人）", s, (r) => r.agg.pop, "#2f6f4f", (v) => nf(Math.round(v))) +
    lineChart("群体数（个）", s, (r) => r.agg.bands, "#2c4a8a", (v) => nf(Math.round(v))) +
    lineChart("野外资源存量（人年口粮）", s, (r) => r.agg.stock_total, "#7a6f2b", (v) => py(v, 0)) +
    lineChart("群体储粮（人年口粮）", s, (r) => r.agg.store_total, "#8a5a2b", (v) => py(v, 0)) +
    lineChart("当年迁移次数（次）", s, (r) => r.year.mig_total, "#59748a", (v) => nf(v)) +
    lineChart("当年迁移死亡（人）", s, (r) => r.year.mig_deaths_cum, "#a12b2b", (v) => nf(v)) +
    lineChart("当年缺粮/需求（‰）", s, (r) => r.year.need_cum ?
      Math.round(r.year.deficit_cum / r.year.need_cum * 1000) : 0, "#b4531f", (v) => v + "‰");
  const head = `<tr><th>年</th><th>总人口</th><th>群体数</th><th>野外存量(人年)</th><th>储粮(人年)</th>
    <th>当年出生</th><th>当年原死亡</th><th>当年迁移死亡</th><th>当年迁移</th><th>当年缺粮/需求</th>
    <th>累计出生</th><th>累计原死亡</th><th>累计迁移死亡</th><th>守恒误差</th></tr>`;
  const rows = s.map((r) => `<tr class="${r.t === S.t ? "on" : ""}" data-t="${r.t}">
    <td class="clickable">${r.t}</td><td>${nf(r.agg.pop)}</td><td>${nf(r.agg.bands)}</td>
    <td>${py(r.agg.stock_total, 0)}</td><td>${py(r.agg.store_total, 0)}</td>
    <td>${nf(r.year.births_cum)}</td><td>${nf(r.year.deaths_demo_cum)}</td>
    <td>${nf(r.year.mig_deaths_cum)}</td><td>${nf(r.year.mig_total)}</td>
    <td>${r.year.need_cum ? (r.year.deficit_cum / r.year.need_cum * 100).toFixed(3) + "%" : "不适用"}</td>
    <td>${nf(r.cum.births_cum)}</td><td>${nf(r.cum.deaths_demo_cum)}</td>
    <td>${nf(r.cum.mig_deaths_cum)}</td><td>${r.integrity.conservation_error}</td></tr>`).join("");
  $("yeartable").innerHTML = head + rows;
  $("yeartable").querySelectorAll("tr[data-t]").forEach((n) =>
    n.addEventListener("click", () => gotoYear(+n.dataset.t)));
}

/* ---------------- 事件 ---------------- */
function renderEvents() {
  const rec = S.years.get(S.t);
  if (!rec) { $("events").innerHTML = `<div class="emptystate">没有数据</div>`; return; }
  $("events").innerHTML = rec.events.length
    ? rec.events.map((e) => `<div class="ev ${e.type}">
        <div>${e.text}</div>
        <div class="src">来源：${e.source}${e.unrecorded ? "　·　未记录：" + e.unrecorded : ""}</div>
      </div>`).join("")
    : `<div class="emptystate">第 ${S.t} 年没有可核实的事件（无分裂、无迁移、无群体消失）。</div>`;
  const head = `<tr><th>群体</th><th>人口</th><th>储粮(人年)</th><th>所在格</th><th>区块</th>
                <th>记忆格数</th><th>迁移累加器</th></tr>`;
  $("bandtable").innerHTML = head + rec.bands.map((b) => `<tr data-b="${b.id}"
      class="${S.selBand === b.id ? "on" : ""}"><td class="clickable">${b.name}</td>
      <td>${nf(b.size)}</td><td>${py(b.store)}</td><td>${b.cell}</td>
      <td>${S.map.cells[b.cell].region}</td><td>${Object.keys(b.mem).length}</td>
      <td>${b.macc}</td></tr>`).join("");
  $("bandtable").querySelectorAll("tr[data-b]").forEach((n) =>
    n.addEventListener("click", () => { selectBand(n.dataset.b); showTab("world"); }));
}

/* ---------------- 运行记录 ---------------- */
function renderRuns() {
  const head = `<tr><th>运行</th><th>状态</th><th>seed</th><th>年数</th><th>SIGMA_M</th>
    <th>MOVE_MORT_M</th><th>信息条件</th><th>已算/目标</th><th>创建时间</th><th>模型版本</th><th>操作</th></tr>`;
  $("runtable").innerHTML = head + S.runs.map((r) => `<tr class="${S.run && S.run.run_id === r.run_id ? "on" : ""}">
    <td class="clickable" data-open="${r.run_id}">${r.label || r.run_id}
      ${r.kind === "preset" ? '<span class="badge s-off">预生成</span>' : ""}</td>
    <td>${statusBadge(r.status)}</td><td>${r.seed}</td><td>${r.years}</td>
    <td>${r.sigma_m}‰</td><td>${r.move_mort_m}‰</td>
    <td>${S.cfg.arms[r.arm] ? S.cfg.arms[r.arm].label : r.arm}</td>
    <td>${r.years_recorded}/${r.years}</td><td>${tsfmt(r.created_at)}</td>
    <td><small>${(r.engine_sha256 || "").slice(0, 8)} @ ${r.baseline_commit || "—"}</small></td>
    <td>${["queued", "running"].includes(r.status)
      ? `<span class="link" data-cancel="${r.run_id}">取消</span>`
      : (r.kind === "preset" ? "" : `<span class="link" data-del="${r.run_id}">删除</span>`)}
      ${r.error ? `<div class="err"><small>${r.error}</small></div>` : ""}</td></tr>`).join("");
  $("runtable").querySelectorAll("[data-open]").forEach((n) =>
    n.addEventListener("click", () => openRun(n.dataset.open)));
  $("runtable").querySelectorAll("[data-cancel]").forEach((n) =>
    n.addEventListener("click", async () => {
      try { await api(`/api/runs/${n.dataset.cancel}/cancel`, { method: "POST" }); flash("已请求取消"); }
      catch (e) { flash("取消失败：" + e.message); } refresh();
    }));
  $("runtable").querySelectorAll("[data-del]").forEach((n) =>
    n.addEventListener("click", async () => {
      if (!confirm("删除这次运行的全部记录？")) return;
      try { await api(`/api/runs/${n.dataset.del}`, { method: "DELETE" }); }
      catch (e) { flash("删除失败：" + e.message); } refresh();
    }));
}

async function openRun(id) {
  S.run = await api(`/api/runs/${id}`);
  S.meta = S.run.meta; S.years.clear(); S.selBand = null; S.selCell = null; S.band = null;
  S.view = "truth"; $("v-truth").classList.add("on"); $("v-mem").classList.remove("on");
  const d = await api(`/api/runs/${id}/series`); S.series = d.series;
  $("scrub").max = maxT();
  $("tl-calc").textContent = `已计算到：第 ${maxT()} 年 / 目标 ${S.run.years} 年`;
  await gotoYear(0);
  renderRuns(); renderCharts(); renderStatus();
  setHash({ run: id });
}

/* ---------------- 里程碑 ---------------- */
async function renderMilestones() {
  const d = await api("/api/milestones");
  const bold = (x) => String(x).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  const cls = { "已验收": "s-done", "已实现待审": "s-run", "进行中": "s-run", "待批准": "s-wait", "未开始": "s-off" };
  $("ms-note").textContent = d.note;
  $("milestones").innerHTML = d.items.map((m) => `<div class="ms">
    <h4>${m.title} <span class="badge ${cls[m.status] || "s-off"}">${m.status}</span></h4>
    <div>${bold(m.note)}</div>
    <div class="meta">更新：${m.updated}　·　提交：${m.commit}　·　来源：${m.sources.join("、")}</div>
  </div>`).join("") + `<div class="muted">仓库 HEAD：${d.repo_commit || "未知"}　·　
    状态只有这五种：${d.statuses.join(" / ")}，不给总体百分比。</div>`;
}

/* ---------------- 杂项 ---------------- */
function flash(msg) {
  const n = $("formnote"); n.innerHTML = msg; n.scrollIntoView({ block: "nearest" });
  setTimeout(() => { if (n.innerHTML === msg) n.innerHTML = ""; }, 6000);
}
function showTab(name) {
  ["world", "metrics", "events", "runs", "progress"].forEach((t) => {
    $("tab-" + t).hidden = t !== name;
  });
  document.querySelectorAll("#tabs button").forEach((b) =>
    b.classList.toggle("on", b.dataset.tab === name));
  setHash({ tab: name });
  if (name === "metrics") renderCharts();
  if (name === "progress") renderMilestones().catch((e) => flash(e.message));
}

async function refresh() {
  try {
    const d = await api("/api/runs");
    S.runs = d.runs;
    if (S.run) {
      const cur = S.runs.find((r) => r.run_id === S.run.run_id);
      if (cur) {
        const grew = cur.years_recorded > (S.run.years_recorded ?? 0);
        Object.assign(S.run, cur);
        $("scrub").max = maxT();
        $("tl-calc").textContent = `已计算到：第 ${maxT()} 年 / 目标 ${S.run.years} 年`;
        if (grew) {
          const d2 = await api(`/api/runs/${S.run.run_id}/series`);
          S.series = d2.series; renderCharts();
        }
      }
    }
    renderRuns(); renderStatus();
  } catch (e) {
    $("statusline").innerHTML = `<span class="err">后台读取失败：${e.message}</span>`;
  }
}

async function boot() {
  $("token").value = S.token;
  $("tokbtn").addEventListener("click", () => {
    S.token = $("token").value.trim();
    sessionStorage.setItem("obs_token", S.token);
    location.reload();
  });
  document.querySelectorAll("#tabs button").forEach((b) =>
    b.addEventListener("click", () => showTab(b.dataset.tab)));
  $("v-truth").addEventListener("click", () => setView("truth"));
  $("v-mem").addEventListener("click", () => setView("mem"));
  $("b-play").addEventListener("click", () => setPlaying(!S.playing));
  $("b-next").addEventListener("click", () => { setPlaying(false); gotoYear(S.t + 1); });
  $("b-prev").addEventListener("click", () => { setPlaying(false); gotoYear(S.t - 1); });
  $("b-home").addEventListener("click", () => { setPlaying(false); gotoYear(0); });
  $("speed").addEventListener("change", (e) => { S.speed = +e.target.value; });
  $("scrub").addEventListener("input", (e) => { setPlaying(false); gotoYear(+e.target.value); });
  $("b-start").addEventListener("click", startRun);

  try {
    S.cfg = await api("/api/config");
  } catch (e) {
    $("statusline").innerHTML = e.status === 401
      ? `<span class="err">需要访问令牌：请在右上角填入后点“保存”。</span>`
      : `<span class="err">后台连接失败：${e.message}</span>`;
    return;
  }
  S.map = await api("/api/map");
  $("f-arm").innerHTML = Object.entries(S.cfg.arms)
    .map(([k, v]) => `<option value="${k}">${v.label}</option>`).join("");
  $("armnote").textContent = Object.values(S.cfg.arms).map((v) => v.label + "：" + v.note).join("　");
  $("f-years").max = S.cfg.limits.max_years;
  $("footer").innerHTML = `模型：${S.cfg.engine.engine_path} @ ${S.cfg.engine.baseline_commit}
    （sha256 ${S.cfg.engine.engine_sha256.slice(0, 16)}…，参数指纹 ${S.cfg.engine.params_fingerprint}）　·　
    仓库 HEAD ${S.cfg.repo_commit}　·　数据：${S.cfg.data.runs} 次运行 / ${S.cfg.data.size_mb} MB　·　
    单次上限 ${S.cfg.limits.max_years} 年，最多保存 ${S.cfg.limits.max_runs} 次运行　·　
    本页只显示本服务自己的数据库。`;

  await refresh();
  const hp = hashParams();
  const wanted = hp.run && S.runs.find((r) => r.run_id === hp.run);
  const first = wanted || S.runs.find((r) => r.status === "running") ||
    S.runs.find((r) => r.years_recorded > 0);
  if (first) {
    await openRun(first.run_id);
    if (hp.t) await gotoYear(parseInt(hp.t, 10) || 0);
    if (hp.b) selectBand(hp.b);
    if (hp.view === "mem") setView("mem");
  } else {
    $("side-empty").textContent = "还没有任何运行记录。到“运行记录”页发起一次模拟。";
  }
  if (hp.tab) showTab(hp.tab);
  setInterval(refresh, 1500);
}

async function startRun() {
  const body = {
    seed: parseInt($("f-seed").value, 10),
    years: parseInt($("f-years").value, 10),
    sigma_m: parseInt($("f-sigma").value, 10),
    move_mort_m: parseInt($("f-mort").value, 10),
    arm: $("f-arm").value,
    label: $("f-label").value.trim(),
  };
  for (const [k, v] of Object.entries(body)) {
    if (typeof v === "number" && !Number.isFinite(v)) { flash(`参数 ${k} 不是整数`); return; }
  }
  $("b-start").disabled = true;
  try {
    const r = await api("/api/runs", { method: "POST", body: JSON.stringify(body) });
    flash(`已提交，运行号 ${r.run_id}。计算在后台独立进程里进行，可以直接看进度。`);
    await refresh(); await openRun(r.run_id);
    showTab("world");
  } catch (e) {
    flash(`<span class="err">启动失败：${e.message}</span>`);
  } finally {
    $("b-start").disabled = false;
  }
}

boot().catch((e) => { $("statusline").innerHTML = `<span class="err">初始化失败：${e.message}</span>`; });

/* 诊断用：#diag=1 时把关键元素宽度写进页面标题，便于用截图核对布局 */
if (hashParams().diag === "1") {
  setTimeout(() => {
    const w = (sel) => { const n = document.querySelector(sel); return n ? Math.round(n.getBoundingClientRect().width) : -1; };
    document.title = `vw=${window.innerWidth} body=${w("body")} main=${w("main")} grid=${w(".worldgrid")} map=${w(".mapwrap")} svg=${w("#map")} hint=${w(".maphint")} side=${w(".side")} scroll=${document.documentElement.scrollWidth}`;
    const d = document.createElement("div");
    d.style.cssText = "position:fixed;bottom:0;left:0;background:#000;color:#0f0;font:11px monospace;z-index:999;padding:2px";
    d.textContent = document.title; document.body.appendChild(d);
  }, 1200);
}
