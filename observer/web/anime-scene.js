/* Anime landscape + chibi group-reps. Not a screenshot of the reference PNG. */
(function (root) {
  "use strict";
  const ALIAS = ["青禾", "松果", "山雀", "河柳", "石楠", "云杉", "暖丘", "苔原", "芦花", "丹枫", "谷雨", "薄暮"];
  const PAL = [
    { hair: "#3b2a1a", cloth: "#5b8c3a", accent: "#e8c96a", skin: "#f3d2b3", tag: "#6aa84f" },
    { hair: "#5c3317", cloth: "#c45c2d", accent: "#f2d38a", skin: "#efc9a8", tag: "#e67a3a" },
    { hair: "#2c2118", cloth: "#3d6ea8", accent: "#9fd0e8", skin: "#f0d0b0", tag: "#4a90c8" },
    { hair: "#6b3e1f", cloth: "#7a4ea3", accent: "#d7b0f0", skin: "#f4d4b8", tag: "#8e6bb5" },
    { hair: "#24180f", cloth: "#2f6f62", accent: "#b7e3c9", skin: "#efceb0", tag: "#3d9a86" },
    { hair: "#8a5a2b", cloth: "#b43b4a", accent: "#f4c4b0", skin: "#f2d0b4", tag: "#d45a64" },
  ];

  function hashId(id) {
    let h = 0;
    const s = String(id == null ? "" : id);
    for (let i = 0; i < s.length; i++) h = (h * 33 + s.charCodeAt(i)) >>> 0;
    return h;
  }
  function aliasOf(id, used) {
    const h = hashId(id);
    let name = ALIAS[h % ALIAS.length];
    if (used && used[name] && used[name] !== String(id)) name = name + "·" + String(id).slice(-3);
    if (used) used[name] = String(id);
    return name;
  }
  function palOf(id) { return PAL[hashId(id) % PAL.length]; }
  function daysOfStore(store, size, needPc) {
    const n = Number(size), s = Number(store), need = Number(needPc);
    if (!n || n <= 0 || !Number.isFinite(s) || !Number.isFinite(need) || need <= 0) return null;
    return Math.floor((s / (n * need)) * 365);
  }
  function speech(ev, alias) {
    if (!ev) return "";
    const a = (id) => alias(id);
    if (ev.type === "aid") return a(ev.donor) + " 把粮食分给了 " + a(ev.receiver);
    if (ev.type === "share") return a(ev.donor) + " 把见闻告诉了 " + a(ev.receiver);
    if (ev.type === "migrate") return a(ev.band) + " 迁到了另一处";
    if (ev.type === "field_built") return a((ev.participants && ev.participants[0]) || ev.band) + " 在这里开垦了土地";
    if (ev.type === "farm_harvest") return a((ev.participants && ev.participants[0]) || ev.band) + " 收成了作物";
    if (ev.type === "field_decay") return "这片耕地在退化";
    if (ev.type === "split") return a(ev.parent || ev.band) + " 分成了两个群体";
    if (ev.type === "extinct") return a(ev.band) + " 这一支已无在世人口";
    return ev.text || ev.type;
  }
  function blob(cx, cy, rx, ry, fill) {
    return "<ellipse cx=\"" + cx.toFixed(1) + "\" cy=\"" + cy.toFixed(1) + "\" rx=\"" + rx + "\" ry=\"" + ry + "\" fill=\"" + fill + "\"/>";
  }
  function chibi(b, x, y, opts) {
    opts = opts || {};
    const pal = palOf(b.id);
    const on = !!opts.selected;
    const pose = opts.pose || "idle";
    const alias = opts.alias || aliasOf(b.id);
    const bob = pose === "walk" ? -1.4 : (pose === "give" ? 0.6 : 0);
    const arm = pose === "give" ? -42 : (pose === "receive" ? -28 : -8);
    const title = alias + " · " + (b.size != null ? b.size : "?") + "人。群体代表，不是独立个人。";
    return "<g class=\"an-chibi band unit" + (on ? " selected" : "") + "\" data-band=\"" + String(b.id) + "\" data-unit=\"group-rep\" data-art=\"chibi\" transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")\">" +
      "<title>" + title + "</title>" +
      "<ellipse cx=\"0\" cy=\"10\" rx=\"11\" ry=\"4\" fill=\"rgba(40,50,20,0.22)\"/>" +
      "<g transform=\"translate(0," + bob + ")\">" +
      "<rect class=\"an-leg\" x=\"-4.2\" y=\"4\" width=\"3.2\" height=\"8\" rx=\"1.4\" fill=\"#4a3728\"/>" +
      "<rect class=\"an-leg\" x=\"1.2\" y=\"4\" width=\"3.2\" height=\"8\" rx=\"1.4\" fill=\"#4a3728\"/>" +
      "<path d=\"M-7.5,-1 C-8,7 -3,9 0,9 C3,9 8,7 7.5,-1 C3,-3 -3,-3 -7.5,-1Z\" fill=\"" + pal.cloth + "\" stroke=\"#2a2016\" stroke-width=\"0.7\"/>" +
      "<g transform=\"rotate(" + arm + ")\">" +
      "<rect x=\"-9\" y=\"-1\" width=\"3\" height=\"7\" rx=\"1.4\" fill=\"" + pal.skin + "\"/>" +
      "</g>" +
      "<g transform=\"rotate(" + (-arm) + ")\">" +
      "<rect x=\"6\" y=\"-1\" width=\"3\" height=\"7\" rx=\"1.4\" fill=\"" + pal.skin + "\"/>" +
      "</g>" +
      "<circle cx=\"0\" cy=\"-8.2\" r=\"6.1\" fill=\"" + pal.skin + "\" stroke=\"#2a2016\" stroke-width=\"0.7\"/>" +
      "<path d=\"M-6.2,-9 C-5,-15 5,-15 6.2,-9 C2.4,-11.5 -2.4,-11.5 -6.2,-9Z\" fill=\"" + pal.hair + "\"/>" +
      "<circle cx=\"-2.1\" cy=\"-8\" r=\"0.7\" fill=\"#2a2016\"/>" +
      "<circle cx=\"2.1\" cy=\"-8\" r=\"0.7\" fill=\"#2a2016\"/>" +
      "<path d=\"M-1.4,-5.4 Q0,-4.4 1.4,-5.4\" fill=\"none\" stroke=\"#c27a6a\" stroke-width=\"0.6\"/>" +
      "</g>" +
      "<g class=\"an-tag\" transform=\"translate(0,-22)\">" +
      "<rect x=\"-28\" y=\"-9\" width=\"56\" height=\"16\" rx=\"8\" fill=\"" + pal.tag + "\" fill-opacity=\"0.95\" stroke=\"#fff\" stroke-width=\"1.2\"/>" +
      "<text x=\"0\" y=\"2.2\" text-anchor=\"middle\" font-size=\"7.2\" fill=\"#fff\" font-weight=\"700\">" + alias + " · " + (b.size != null ? b.size : "?") + "人</text>" +
      "</g></g>";
  }
  function tree(x, y, h) {
    return "<g class=\"an-tree\" transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")\">" +
      "<rect x=\"-1.4\" y=\"-2\" width=\"2.8\" height=\"7\" fill=\"#6b4a2a\"/>" +
      "<ellipse cx=\"0\" cy=\"" + (-h) + "\" rx=\"" + (5 + h * 0.15) + "\" ry=\"" + (6 + h * 0.2) + "\" fill=\"#3f7a3a\"/>" +
      "<ellipse cx=\"-2\" cy=\"" + (-h + 2) + "\" rx=\"3.2\" ry=\"3.6\" fill=\"#4e9244\"/>" +
      "</g>";
  }
  function rocks(x, y) {
    return "<g class=\"an-rock\" transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")\">" +
      "<ellipse cx=\"0\" cy=\"2\" rx=\"10\" ry=\"5\" fill=\"#8b8a86\"/>" +
      "<ellipse cx=\"-4\" cy=\"0\" rx=\"6\" ry=\"7\" fill=\"#9a9892\"/>" +
      "<ellipse cx=\"5\" cy=\"1\" rx=\"5\" ry=\"6\" fill=\"#7d7c78\"/>" +
      "</g>";
  }
  function fieldPatch(x, y, units) {
    const w = 10 + Math.min(14, units * 1.6);
    const h = 7 + Math.min(8, units);
    let rows = "";
    for (let i = -2; i <= 2; i++) {
      rows += "<line x1=\"" + (-w + 1) + "\" y1=\"" + (i * 1.6) + "\" x2=\"" + (w - 1) + "\" y2=\"" + (i * 1.6) + "\" stroke=\"#c4a15a\" stroke-width=\"0.7\"/>";
    }
    return "<g class=\"an-field\" data-field-units=\"" + units.toFixed(3) + "\" transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")\">" +
      "<ellipse rx=\"" + w + "\" ry=\"" + h + "\" fill=\"#b8894a\" stroke=\"#8a6230\" stroke-width=\"0.8\"/>" + rows + "</g>";
  }
  function paint(svg, st) {
    if (!svg || !st || !st.map) return;
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    const rec = st.rec;
    const cells = st.map.cells || [];
    const farm = rec && rec.farm && rec.farm.schema === "farm-1" ? rec.farm : null;
    const fields = farm && Array.isArray(farm.field_m) ? farm.field_m : null;
    const used = {};
    const alias = (id) => aliasOf(id, used);
    let out = "<defs><linearGradient id=\"anSky\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">" +
      "<stop offset=\"0%\" stop-color=\"#9ad4f0\"/><stop offset=\"55%\" stop-color=\"#d7ecc4\"/><stop offset=\"100%\" stop-color=\"#b7d48a\"/></linearGradient></defs>";
    out += "<rect class=\"an-sky\" x=\"-40\" y=\"-40\" width=\"600\" height=\"520\" fill=\"url(#anSky)\"/>";
    out += "<ellipse cx=\"430\" cy=\"70\" rx=\"70\" ry=\"28\" fill=\"#fff\" opacity=\"0.55\"/>";
    out += "<ellipse cx=\"70\" cy=\"50\" rx=\"50\" ry=\"20\" fill=\"#fff\" opacity=\"0.4\"/>";
    cells.forEach((c) => {
      const xy = st.cellCenter(c);
      const cx = xy[0], cy = xy[1];
      if (!c.passable) {
        out += rocks(cx, cy - 2);
        return;
      }
      const stock = rec && rec.stock ? rec.stock[c.i] : 0;
      const lush = stock ? Math.min(1, stock / 90000000) : 0.35;
      const g = Math.round(140 + lush * 50);
      out += blob(cx, cy + 6, 26, 16, "rgb(" + Math.round(90 + lush * 20) + "," + g + "," + Math.round(70 + lush * 20) + ")");
      const h = hashId("tree" + c.i);
      if (h % 5 === 0) out += tree(cx - 10, cy - 4, 8 + (h % 4));
      if (h % 7 === 0) out += tree(cx + 11, cy - 2, 7);
      if (fields && fields[c.i] > 0) out += fieldPatch(cx, cy + 2, fields[c.i] / 1000);
      out += "<path class=\"cell\" d=\"M" + (cx - 16) + "," + cy + " L" + cx + "," + (cy - 12) + " L" + (cx + 16) + "," + cy + " L" + cx + "," + (cy + 12) + "Z\" fill=\"transparent\" data-cell=\"" + c.i + "\"/>";
    });
    const evs = (rec && rec.events) || [];
    evs.slice(0, 4).forEach((e, i) => {
      if (e.cell == null || !st.map.cells[e.cell]) return;
      const xy = st.cellCenter(st.map.cells[e.cell]);
      const txt = speech(e, alias);
      out += "<g class=\"an-bubble\" transform=\"translate(" + (xy[0] + 8) + "," + (xy[1] - 28 - i * 2) + ")\">" +
        "<rect x=\"-4\" y=\"-10\" width=\"" + Math.min(92, 8 + txt.length * 6.2) + "\" height=\"16\" rx=\"7\" fill=\"#fff\" stroke=\"#d8e4d0\"/>" +
        "<text x=\"2\" y=\"1.5\" font-size=\"6.2\" fill=\"#3a4a38\">" + txt.slice(0, 16) + "</text></g>";
    });
    (rec && rec.bands || []).forEach((b) => {
      const cell = st.map.cells[b.cell];
      if (!cell) return;
      const xy = st.cellCenter(cell);
      const on = st.selBand && String(st.selBand) === String(b.id);
      const pose = on && st.pose ? st.pose : "idle";
      out += chibi(b, xy[0], xy[1] - 6, { selected: on, pose: pose, alias: alias(b.id) });
    });
    svg.innerHTML = out;
  }
  function fillChrome(st) {
    const rec = st.rec, run = st.run, t = st.t;
    const pop = rec && rec.agg ? rec.agg.pop : null;
    const nb = rec && rec.bands ? rec.bands.length : null;
    const farm = rec && rec.farm && rec.farm.schema === "farm-1" ? rec.farm : null;
    const fieldU = farm ? (farm.field_total_m || 0) / 1000 : null;
    const harv = farm && farm.year ? farm.year.harvested_kcal : null;
    const need = st.needPc || 730000;
    if (st.$("an-pop")) st.$("an-pop").textContent = pop == null ? "—" : String(pop);
    if (st.$("an-bands")) st.$("an-bands").textContent = nb == null ? "—" : String(nb);
    if (st.$("an-fields")) {
      st.$("an-fields").textContent = farm ? (fieldU.toFixed(1) + " 单位") : "不支持耕作";
    }
    if (st.$("an-food")) {
      st.$("an-food").textContent = harv == null ? (farm ? "0" : "不支持耕作") : (harv / need).toFixed(1) + " 人年";
    }
    if (st.$("an-mig")) st.$("an-mig").textContent = rec && rec.year && rec.year.mig_total != null ? String(rec.year.mig_total) : "未记录";
    if (st.$("an-aid")) st.$("an-aid").textContent = rec && rec.aid && rec.aid.events != null ? String(rec.aid.events) : "未记录";
    if (st.$("an-badge")) st.$("an-badge").textContent = "示例世界 · 历史回放";
    const used = {};
    const alias = (id) => aliasOf(id, used);
    const list = st.$("an-events");
    if (list) {
      const items = (rec && rec.events) || [];
      list.innerHTML = items.slice(0, 6).map((e) => {
        return "<button type=\"button\" class=\"an-ev\" data-eid=\"" + String(e.id || "") + "\" data-year=\"" + t + "\">" +
          "<b>第 " + t + " 年</b> " + speech(e, alias) + "</button>";
      }).join("") || "<p class=\"muted\">这一年没有可核实事件。</p>";
    }
    const card = st.$("an-card");
    if (card && rec) {
      const b = (rec.bands || []).find((x) => String(x.id) === String(st.selBand)) || rec.bands[0];
      if (b) {
        const days = daysOfStore(b.store, b.size, need);
        const pal = palOf(b.id);
        const al = alias(b.id);
        const farmCell = farm && farm.cells && farm.cells.find((c) => +c.cell === +b.cell);
        const fu = farmCell ? (farmCell.field_after_m / 1000) : null;
        card.innerHTML = "<div class=\"an-card-h\"><span class=\"an-avatar\" style=\"background:" + pal.cloth + "\"></span><div><strong>" + al + "</strong>" +
          "<div class=\"muted\">来源 ID " + String(b.id) + "</div></div></div>" +
          "<ul class=\"an-card-kv\">" +
          "<li>人口 " + b.size + " 人</li>" +
          "<li>储粮 " + (b.store / need).toFixed(1) + " 人年" +
          (days == null ? "" : " · 按当前" + b.size + "人折算约可供 " + days + " 天。这是当前库存的标准口粮折算，不含未来收成，不保证存活时长。") + "</li>" +
          "<li>耕地 " + (fu == null ? (farm ? "本格无田" : "不支持耕作") : fu.toFixed(1) + " 单位") + "</li>" +
          "<li>位置 第 " + b.cell + " 格（底层坐标，画面不显示格号）</li></ul>";
      }
    }
    const mini = st.$("an-mini");
    if (mini && st.map) {
      let m = "<svg viewBox=\"0 0 120 90\" class=\"an-mini-svg\">";
      (st.map.cells || []).forEach((c) => {
        const x = 8 + (c.col + (c.row % 2 ? 0.5 : 0)) * 12;
        const y = 8 + c.row * 9;
        const fill = c.passable ? "#8fbc6a" : "#8a8680";
        m += "<rect x=\"" + x + "\" y=\"" + y + "\" width=\"10\" height=\"8\" rx=\"2\" fill=\"" + fill + "\"/>";
      });
      (rec && rec.bands || []).forEach((b) => {
        const c = st.map.cells[b.cell];
        if (!c) return;
        const x = 13 + (c.col + (c.row % 2 ? 0.5 : 0)) * 12;
        const y = 12 + c.row * 9;
        m += "<circle cx=\"" + x + "\" cy=\"" + y + "\" r=\"2.4\" fill=\"" + palOf(b.id).tag + "\" stroke=\"#fff\" stroke-width=\"0.6\"/>";
      });
      m += "</svg>";
      mini.innerHTML = m;
    }
  }
  root.AnimeScene = {
    aliasOf: aliasOf, palOf: palOf, daysOfStore: daysOfStore, speech: speech,
    paint: paint, fillChrome: fillChrome,
  };
})(typeof window !== "undefined" ? window : globalThis);
