/* Watch-plan player. Real API watch-plan-1. No LLM copy. */
(function (root) {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }
  function cmpId(a, b) {
    const sa = String(a), sb = String(b);
    if (sa.length !== sb.length) return sa.length - sb.length;
    if (sa < sb) return -1;
    if (sa > sb) return 1;
    return 0;
  }
  function factVal(facts, key) {
    const f = facts && facts[key];
    if (!f || f.value == null) return null;
    return f;
  }
  function aliasOf(id, aliasFn) {
    if (id == null || id === "") return "一群人";
    try { return aliasFn ? (aliasFn(id) || String(id)) : String(id); }
    catch (e) { return String(id); }
  }
  function names(ids, aliasFn) {
    const list = (ids || []).map((id) => aliasOf(id, aliasFn));
    if (!list.length) return "";
    if (list.length === 1) return list[0];
    return list.slice(0, -1).join("、") + "和" + list[list.length - 1];
  }
  function gapText(prevYear, year) {
    if (prevYear == null || year == null) return "";
    const a = Number(prevYear), b = Number(year);
    if (!Number.isFinite(a) || !Number.isFinite(b) || b <= a) return "";
    const d = b - a;
    if (d <= 1) return "";
    return "第 " + a + " 年 → 第 " + b + " 年，相隔 " + d + " 年。画面上的人物是群体代表，不是活了几百岁的同一个人。";
  }
  function missingLabel(reason) {
    if (reason === "engine_lacks_mechanism") return "这个世界里没有这回事";
    if (reason === "param_zero") return "参数设成了 0，所以一次都没有";
    if (reason === "not_observed") return "没有发生过";
    if (reason === "outside_watermark") return "这一段还没到";
    if (reason === "history_incomplete") return "还在生成";
    if (reason === "capability_unknown") return "未记录";
    return "没有这一章";
  }
  function roundPy(n) {
    const x = Number(n);
    if (!Number.isFinite(x)) return null;
    if (Math.abs(x) >= 10) return String(Math.round(x));
    return x.toFixed(1).replace(/\.0$/, "");
  }
  function fieldUnits(m) {
    const n = Number(m);
    if (!Number.isFinite(n)) return null;
    const u = n / 1000;
    if (Math.abs(u - Math.round(u)) < 1e-6) return String(Math.round(u));
    return u.toFixed(1).replace(/\.0$/, "");
  }
  const RAW_MAIN = /\b(built_m|field_before_m|field_after_m|labour_m|harvested_kcal(?:_here_this_year)?|potential_kcal|uncollected_kcal|worked_m|weather_m|per_band_kcal|person_years|field_total_m|store_total|stock_total|aid_kcal_cum|births_cum|deaths_cum|migration_deaths|mig_deaths|remembered_kcal|remembered_last_year|field_m（|amount_m)\b/;
  function rawInMain(text) {
    return RAW_MAIN.test(String(text || ""));
  }
  function formatSourceFacts(ch) {
    if (!ch) return "";
    const lines = [];
    if (ch.event_id) lines.push("event_id " + ch.event_id);
    if (ch.cell != null) lines.push("cell " + ch.cell);
    if (ch.from != null || ch.to != null) lines.push("from " + ch.from + " to " + ch.to);
    const facts = ch.facts || {};
    Object.keys(facts).forEach((k) => {
      const f = facts[k];
      if (!f) return;
      let val = f.value;
      if (val != null && typeof val === "object") {
        try { val = JSON.stringify(val); } catch (e) { val = String(val); }
      }
      lines.push(k + " = " + (val == null ? "" : val)
        + (f.unit ? " " + f.unit : "")
        + (f.source ? " · " + f.source : "")
        + (f.basis ? " · " + f.basis : "")
        + (f.year != null ? " · year " + f.year : "")
        + (f.note ? " · " + f.note : ""));
    });
    if (ch.basis_event_ids && ch.basis_event_ids.length) {
      lines.push("basis_event_ids " + ch.basis_event_ids.join(", "));
    }
    return lines.join("\n");
  }
  function sharePhrase(facts) {
    const py = factVal(facts, "person_years");
    const share = py ? roundPy(py.value) : null;
    return share ? ("按模型口粮约相当于 " + share + " 人一年的份额") : "";
  }
  function narrate(ch, aliasFn, opts) {
    opts = opts || {};
    if (!ch) return { title: "", copy: "", facts: "", source: "", banned: false };
    const facts = ch.facts || {};
    const who = names(ch.actor_ids, aliasFn);
    const title = ch.title || "";
    let copy = "";
    if (ch.kind === "origin") {
      const pop = factVal(facts, "pop");
      const nb = factVal(facts, "bands");
      copy = "这是有完整记录的开局。"
        + (pop ? ("当时一共 " + pop.value + " 人。") : "")
        + (nb ? (nb.value + " 个群体住在这里。") : "")
        + "画面上的人物是群体代表，不是独立的个人。";
    } else if (ch.kind === "clearing") {
      const built = factVal(facts, "built_m") || factVal(facts, "amount_m");
      const units = built ? fieldUnits(built.value) : null;
      copy = (who || "有人") + "一行在这里开垦了土地"
        + (units ? ("，按记录折合约 " + units + " 个耕作规模单位") : "")
        + "。新开的地要到以后年份才可能有收成。";
    } else if (ch.kind === "harvest") {
      const share = sharePhrase(facts);
      copy = (who || "有人") + "一行收获了食物" + (share ? ("，" + share) : "") + "。";
    } else if (ch.kind === "migrate") {
      const place = (ch.from != null && ch.to != null)
        ? ("从第 " + ch.from + " 格迁到第 " + ch.to + " 格。")
        : "迁到了另一处。";
      copy = (who || "有人") + place + "这是群体代表的位置变化，不是某个人走完了整段人生。";
    } else if (ch.kind === "aid") {
      const a = (ch.actor_ids || [])[0], b = (ch.actor_ids || [])[1];
      const share = sharePhrase(facts);
      copy = aliasOf(a, aliasFn) + "把一部分粮食交给" + aliasOf(b, aliasFn)
        + (share ? ("，" + share) : "") + "。";
    } else if (ch.kind === "repay") {
      const a = (ch.actor_ids || [])[0], b = (ch.actor_ids || [])[1];
      const share = sharePhrase(facts);
      copy = "这次接收帮助的群体，以前也帮助过对方。"
        + (a && b ? (aliasOf(a, aliasFn) + "把粮食交给了" + aliasOf(b, aliasFn)
          + (share ? ("，" + share) : "") + "。") : "");
    } else if (ch.kind === "final") {
      const pop = factVal(facts, "pop");
      copy = "看到这里，已记录历史到第 " + ch.year + " 年。"
        + (pop ? ("年末一共 " + pop.value + " 人。") : "")
        + "后面没有再往下编。";
    } else copy = title || "这一段记录。";
    const extra = [];
    (ch.actor_ids || []).forEach((id) => extra.push(aliasOf(id, aliasFn)));
    const source = formatSourceFacts(ch);
    const banned = /因此没有人饿死|为了感恩|明年一定丰收|保证能活/.test(copy) || rawInMain(copy);
    return { title: title, copy: copy, facts: "", source: source, actors: extra, banned: banned };
  }
  function chapterAction(kind) {
    if (kind === "clearing") return "till";
    if (kind === "harvest") return "harvest";
    if (kind === "migrate") return "walk";
    if (kind === "aid" || kind === "repay") return "give";
    return null;
  }
  function pinPath(runId, through) {
    let p = "/api/runs/" + encodeURIComponent(runId) + "/watch-plan";
    if (through != null && Number.isFinite(+through)) p += "?through=" + encodeURIComponent(String(through));
    return p;
  }

  const WatchLogic = {
    cmpId: cmpId, gapText: gapText, narrate: narrate, missingLabel: missingLabel,
    chapterAction: chapterAction, pinPath: pinPath, names: names, factVal: factVal,
    formatSourceFacts: formatSourceFacts, rawInMain: rawInMain, fieldUnits: fieldUnits,
  };

  const Player = {
    host: null,
    plan: null,
    idx: 0,
    gen: 0,
    paused: false,
    activeFlag: false,
    timers: [],
    lastYear: null,
  };
  function $(id) {
    if (Player.host && Player.host.$) return Player.host.$(id);
    return (typeof document !== "undefined") ? document.getElementById(id) : null;
  }
  function clearTimers() {
    Player.timers.forEach((id) => clearTimeout(id));
    Player.timers = [];
  }
  function later(fn, ms) {
    const gen = Player.gen;
    const id = setTimeout(() => { if (Player.gen === gen && Player.activeFlag) fn(); }, ms);
    Player.timers.push(id);
    return id;
  }
  function speed() {
    const st = Player.host && Player.host.getState ? Player.host.getState() : {};
    return Math.max(0.25, Number(st.speed) || 1);
  }
  function holdMs(ch) {
    const base = (ch && (ch.kind === "origin" || ch.kind === "final")) ? 4200 : 6800;
    return Math.max(900, base / speed());
  }
  function paintBar() {
    const bar = $("an-watch-bar");
    if (!bar) return;
    const ch = Player.plan && Player.plan.chapters && Player.plan.chapters[Player.idx];
    if (!Player.activeFlag || !ch) { bar.hidden = true; return; }
    bar.hidden = false;
    const st = Player.host && Player.host.getState ? Player.host.getState() : {};
    const aliasFn = Player.host && Player.host.alias;
    const said = narrate(ch, aliasFn, st);
    const prev = Player.idx > 0 ? Player.plan.chapters[Player.idx - 1] : null;
    const gap = gapText(prev && prev.year, ch.year);
    const title = $("an-watch-title");
    const copy = $("an-watch-copy");
    const gapEl = $("an-watch-gap");
    const facts = $("an-watch-facts");
    const actors = $("an-watch-actors");
    const pause = $("an-watch-pause");
    const status = $("an-watch-status");
    if (title) title.textContent = (Player.idx + 1) + "/" + Player.plan.chapters.length + " · " + said.title;
    if (copy) copy.textContent = said.copy;
    if (gapEl) { gapEl.hidden = !gap; gapEl.textContent = gap; }
    if (facts) {
      facts.textContent = "";
      facts.hidden = true;
    }
    const srcBody = $("an-watch-src-body");
    if (srcBody) srcBody.textContent = said.source || "";
    if (actors) {
      const ids = ch.actor_ids || [];
      actors.innerHTML = ids.map((id) => {
        return "<button type=\"button\" class=\"an-watch-actor\" data-band=\"" + esc(id) + "\">" +
          esc(aliasOf(id, aliasFn)) + "</button>";
      }).join("");
      actors.querySelectorAll("[data-band]").forEach((n) => {
        n.addEventListener("click", (e) => {
          e.preventDefault(); e.stopPropagation();
          if (Player.host && Player.host.selectBand) Player.host.selectBand(n.getAttribute("data-band"), { fromWatch: true });
        });
      });
    }
    if (pause) pause.textContent = Player.paused ? "继续" : "暂停";
    if (status) {
      status.textContent = Player.paused ? "已暂停" : ("正在看第 " + ch.year + " 年");
    }
    const miss = $("an-watch-missing");
    if (miss) {
      const rows = (Player.plan.missing_kinds || []).map((m) => missingLabel(m.reason) + "（" + m.kind + "）");
      miss.textContent = rows.join(" · ");
      miss.hidden = !rows.length;
    }
    if (typeof document !== "undefined") document.documentElement.classList.add("watch-on");
  }
  async function playIndex(i) {
    if (!Player.activeFlag || !Player.plan) return;
    const chs = Player.plan.chapters || [];
    if (!chs.length) { exit({ reason: "empty" }); return; }
    if (i < 0) i = 0;
    if (i >= chs.length) i = chs.length - 1;
    Player.idx = i;
    Player.paused = false;
    clearTimers();
    const ch = chs[i];
    paintBar();
    const host = Player.host;
    if (!host) return;
    if (host.setPlaying) host.setPlaying(false);
    if (host.showTab) host.showTab("world");
    const gy = await host.gotoYear(ch.year, { quiet: true });
    if (!Player.activeFlag) return;
    if (!gy || !gy.ok) {
      const fail = $("an-watch-copy");
      if (fail) fail.textContent = "这一年记录没读到。可以重试，不会拿旧年数字冒充。";
      const retry = $("an-watch-retry");
      if (retry) retry.hidden = false;
      return;
    }
    const retry = $("an-watch-retry");
    if (retry) retry.hidden = true;
    paintBar();
    if (ch.event_id && host.focusEvent) {
      const rec = host.recNow && host.recNow();
      const ev = rec && (rec.events || []).find((e) => String(e.id) === String(ch.event_id));
      if (ev) await host.focusEvent(Object.assign({}, ev, { t: ch.year }), { fromWatch: true });
    }
    if (!Player.activeFlag) return;
    Player.lastYear = ch.year;
    if (i < chs.length - 1) {
      later(() => { if (!Player.paused) playIndex(i + 1); }, holdMs(ch));
    }
  }
  async function start(opts) {
    opts = opts || {};
    const host = Player.host;
    if (!host || !host.api) throw new Error("watch host missing");
    const st = host.getState ? host.getState() : {};
    const run = st.run;
    if (!run || !run.run_id) { if (host.flash) host.flash("请先打开一个世界。", true); return { ok: false }; }
    if (host.setPlaying) host.setPlaying(false);
    const through = (run.years_recorded != null) ? run.years_recorded : null;
    let plan;
    try {
      plan = await host.api(pinPath(run.run_id, through));
    } catch (e) {
      if (host.flash) host.flash("看这段历史失败：" + e.message, true);
      return { ok: false, error: e.message };
    }
    if (!plan || plan.schema !== "watch-plan-1" || !Array.isArray(plan.chapters)) {
      if (host.flash) host.flash("这份观看计划不可用。", true);
      return { ok: false };
    }
    Player.gen += 1;
    Player.plan = plan;
    Player.idx = 0;
    Player.paused = false;
    Player.activeFlag = true;
    Player.lastYear = null;
    if (host.ingestPlan && plan.identities) host.ingestPlan(plan);
    paintBar();
    await playIndex(0);
    return { ok: true, plan: plan };
  }
  function pauseToggle() {
    if (!Player.activeFlag) return;
    Player.paused = !Player.paused;
    if (Player.paused) clearTimers();
    else {
      const ch = Player.plan && Player.plan.chapters[Player.idx];
      later(() => { if (!Player.paused) playIndex(Player.idx + 1); }, holdMs(ch));
    }
    paintBar();
  }
  function next() {
    if (!Player.activeFlag) return;
    playIndex(Player.idx + 1);
  }
  function prev() {
    if (!Player.activeFlag) return;
    playIndex(Math.max(0, Player.idx - 1));
  }
  function exit(opts) {
    opts = opts || {};
    if (!Player.activeFlag) return;
    Player.activeFlag = false;
    Player.paused = false;
    Player.gen += 1;
    clearTimers();
    const bar = $("an-watch-bar");
    if (bar) bar.hidden = true;
    if (typeof document !== "undefined") document.documentElement.classList.remove("watch-on");
    if (Player.host && Player.host.cancelFx && opts.keepFx !== true) Player.host.cancelFx();
  }
  function bind() {
    const startBtn = $("an-watch-start");
    const startM = $("an-watch-start-m");
    const go = (e) => { if (e) { e.preventDefault(); e.stopPropagation(); } start(); };
    if (startBtn) startBtn.addEventListener("click", go);
    if (startM) startM.addEventListener("click", go);
    const pause = $("an-watch-pause");
    if (pause) pause.addEventListener("click", (e) => { e.preventDefault(); pauseToggle(); });
    const nx = $("an-watch-next");
    if (nx) nx.addEventListener("click", (e) => { e.preventDefault(); next(); });
    const pv = $("an-watch-prev");
    if (pv) pv.addEventListener("click", (e) => { e.preventDefault(); prev(); });
    const ex = $("an-watch-exit");
    if (ex) ex.addEventListener("click", (e) => { e.preventDefault(); exit({ reason: "button" }); });
    const retry = $("an-watch-retry");
    if (retry) retry.addEventListener("click", (e) => { e.preventDefault(); playIndex(Player.idx); });
    const src = $("an-watch-source");
    if (src) src.addEventListener("click", (e) => {
      e.preventDefault();
      const body = $("an-watch-src-body");
      if (body) body.hidden = !body.hidden;
      const ch = Player.plan && Player.plan.chapters[Player.idx];
      if (ch && ch.event_id && Player.host && Player.host.openEventSource) Player.host.openEventSource(ch.event_id);
    });
  }

  const WatchPlayer = {
    init(host) { Player.host = host || {}; bind(); },
    start: start, exit: exit, pauseToggle: pauseToggle, next: next, prev: prev,
    active() { return !!Player.activeFlag; },
    state() {
      return {
        active: Player.activeFlag, idx: Player.idx, paused: Player.paused,
        chapter: Player.plan && Player.plan.chapters && Player.plan.chapters[Player.idx],
        through: Player.plan && Player.plan.source && Player.plan.source.recorded_through,
        n: Player.plan && Player.plan.chapters ? Player.plan.chapters.length : 0,
        run: Player.plan && Player.plan.run_id,
      };
    },
    _player: Player,
  };

  root.WatchLogic = WatchLogic;
  root.WatchPlayer = WatchPlayer;
  if (typeof globalThis !== "undefined") {
    globalThis.WatchLogic = WatchLogic;
    globalThis.WatchPlayer = WatchPlayer;
  }
})(typeof window !== "undefined" ? window : globalThis);
