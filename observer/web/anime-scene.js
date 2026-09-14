/* Independent anime landscape + chibi reps. Not the reference PNG as a world texture. */
(function (root) {
  "use strict";
  const ALIAS = ["青禾", "松果", "山雀", "河柳", "石楠", "云杉", "暖丘", "苔原", "芦花", "丹枫", "谷雨", "薄暮"];
  const PAL = [
    { hair: "#2a1810", cloth: "#4e8f33", sash: "#e7c45a", skin: "#f3d2b3", tag: "#5ea34a", tool: "basket", pants: "#3d6a28", hairKind: "bowl" },
    { hair: "#4a2410", cloth: "#c45c2d", sash: "#f0d48a", skin: "#efc9a8", tag: "#e06a2e", tool: "hoe", pants: "#8a3e1c", hairKind: "tail" },
    { hair: "#1a120c", cloth: "#3a6eae", sash: "#9fd0e8", skin: "#f0d0b0", tag: "#3d86c4", tool: "staff", pants: "#2a4e7a", hairKind: "spike" },
    { hair: "#5a3014", cloth: "#7a4ea3", sash: "#d7b0f0", skin: "#f4d4b8", tag: "#8e6bb5", tool: "gourd", pants: "#4e3270", hairKind: "long" },
    { hair: "#24180f", cloth: "#2f6f62", sash: "#b7e3c9", skin: "#efceb0", tag: "#2f9a84", tool: "basket", pants: "#1f4e46", hairKind: "bun" },
    { hair: "#6a3014", cloth: "#b43b4a", sash: "#f4c4b0", skin: "#f2d0b4", tag: "#d45a64", tool: "hoe", pants: "#7a2832", hairKind: "part" },
  ];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }
  function hashId(id) {
    let h = 0;
    const s = String(id == null ? "" : id);
    for (let i = 0; i < s.length; i++) h = (h * 33 + s.charCodeAt(i)) >>> 0;
    return h;
  }
  function aliasOf(id, used) {
    const h = hashId(id);
    const sid = String(id);
    if (used) {
      for (const k of Object.keys(used)) if (used[k] === sid) return k;
      for (let k = 0; k < ALIAS.length; k++) {
        const name = ALIAS[(h + k) % ALIAS.length];
        if (!used[name]) { used[name] = sid; return name; }
      }
      const name = ALIAS[h % ALIAS.length] + "·" + sid.slice(-3);
      used[name] = sid;
      return name;
    }
    return ALIAS[h % ALIAS.length];
  }
  function palOfName(name) {
    const base = String(name || "").split("·")[0];
    const i = ALIAS.indexOf(base);
    return PAL[(i >= 0 ? i : 0) % PAL.length];
  }
  function palOf(id) { return PAL[hashId(id) % PAL.length]; }
  function bindAliases(ids) {
    const used = {};
    const map = {};
    const unique = [];
    const seen = {};
    (ids || []).forEach((id) => {
      const s = String(id);
      if (seen[s]) return;
      seen[s] = 1;
      unique.push(s);
    });
    unique.sort();
    unique.forEach((id) => { map[id] = aliasOf(id, used); });
    return function alias(id) {
      const s = String(id);
      if (!map[s]) map[s] = aliasOf(s, used);
      return map[s];
    };
  }
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
  function toolMarkup(kind, pal) {
    if (kind === "hoe") {
      return "<g class=\"an-tool\" transform=\"translate(13,-8) rotate(-22)\">" +
        "<rect x=\"-1\" y=\"-3\" width=\"2\" height=\"18\" rx=\"0.8\" fill=\"#6b4424\"/>" +
        "<path d=\"M-5,13 L6,13 L3,18 Z\" fill=\"#8a8f96\" stroke=\"#3a3d42\" stroke-width=\"0.6\"/></g>";
    }
    if (kind === "staff") {
      return "<g class=\"an-tool\" transform=\"translate(13,-14)\">" +
        "<rect x=\"-1\" y=\"0\" width=\"2\" height=\"26\" rx=\"0.8\" fill=\"#7a5230\"/>" +
        "<circle cx=\"0\" cy=\"-1\" r=\"2.2\" fill=\"#c9a45a\" stroke=\"#5a3a18\" stroke-width=\"0.5\"/></g>";
    }
    if (kind === "gourd") {
      return "<g class=\"an-tool\" transform=\"translate(-14,1)\">" +
        "<ellipse cx=\"0\" cy=\"2\" rx=\"2.4\" ry=\"2.2\" fill=\"" + pal.sash + "\"/>" +
        "<ellipse cx=\"0\" cy=\"7\" rx=\"3.4\" ry=\"4.2\" fill=\"" + pal.sash + "\" stroke=\"#5a3a18\" stroke-width=\"0.5\"/></g>";
    }
    return "<g class=\"an-tool\" transform=\"translate(-13,2)\">" +
      "<path d=\"M-5,2 C-6,10 5,10 4,2 L3,-1 L-4,-1 Z\" fill=\"" + pal.sash + "\" stroke=\"#5a3a18\" stroke-width=\"0.6\"/>" +
      "<ellipse cx=\"-1\" cy=\"5\" rx=\"1.6\" ry=\"1.1\" fill=\"#c45c2d\"/></g>";
  }
  function hairMarkup(kind, pal) {
    if (kind === "tail") {
      return "<path d=\"M-9.5,-14 C-8,-24 8,-24 9.5,-14 C4,-18 -4,-18 -9.5,-14Z\" fill=\"" + pal.hair + "\"/>" +
        "<path d=\"M7,-12 Q12,-8 10,2 Q8,4 7,-2\" fill=\"" + pal.hair + "\"/>" +
        "<path d=\"M-8,-12 Q-6,-6 -3,-5\" fill=\"" + pal.hair + "\"/>";
    }
    if (kind === "spike") {
      return "<path d=\"M-9,-13 L-7,-22 L-3,-14 L0,-23 L3,-14 L7,-22 L9,-13 C4,-17 -4,-17 -9,-13Z\" fill=\"" + pal.hair + "\"/>";
    }
    if (kind === "long") {
      return "<path d=\"M-10,-12 C-12,-22 12,-22 10,-12 C12,-6 11,2 9,6 L7,-8 C3,-16 -3,-16 -7,-8 L-9,6 C-11,2 -12,-6 -10,-12Z\" fill=\"" + pal.hair + "\"/>" +
        "<path d=\"M-6,-14 C-2,-18 4,-18 6,-14\" fill=\"" + pal.hair + "\"/>";
    }
    if (kind === "bun") {
      return "<circle cx=\"0\" cy=\"-20\" r=\"4.2\" fill=\"" + pal.hair + "\"/>" +
        "<path d=\"M-9.2,-13 C-8,-22 8,-22 9.2,-13 C4,-16 -4,-16 -9.2,-13Z\" fill=\"" + pal.hair + "\"/>" +
        "<path d=\"M-8.5,-11 Q-10,-6 -6,-5\" fill=\"" + pal.hair + "\"/>";
    }
    if (kind === "part") {
      return "<path d=\"M-9.5,-13 C-10,-22 2,-24 4,-14 C8,-22 11,-16 9.5,-12 C5,-16 -4,-16 -9.5,-13Z\" fill=\"" + pal.hair + "\"/>" +
        "<path d=\"M8.5,-11 Q11,-4 6,1\" fill=\"" + pal.hair + "\"/>";
    }
    return "<path d=\"M-9.6,-13 C-9,-23 9,-23 9.6,-13 C5,-17 -5,-17 -9.6,-13Z\" fill=\"" + pal.hair + "\"/>" +
      "<path d=\"M-9,-12 Q-11,-6 -5,-4\" fill=\"" + pal.hair + "\"/>" +
      "<path d=\"M9,-12 Q11,-6 5,-4\" fill=\"" + pal.hair + "\"/>";
  }
  function chibiBody(b, opts) {
    opts = opts || {};
    const pal = opts.pal || palOf(b.id);
    const pose = opts.pose || "idle";
    const bob = pose === "walk" ? -2.4 : (pose === "give" ? 0.8 : 0);
    const armL = pose === "give" ? -52 : (pose === "receive" ? -26 : -14);
    const armR = pose === "give" ? 16 : (pose === "walk" ? 24 : 12);
    const legL = pose === "walk" ? -14 : 5;
    const legR = pose === "walk" ? 12 : -5;
    return "<g class=\"an-body\" transform=\"translate(0," + bob + ")\">" +
      "<ellipse cx=\"0\" cy=\"20\" rx=\"13\" ry=\"4.2\" fill=\"rgba(40,50,20,0.22)\"/>" +
      "<g transform=\"rotate(" + legL + " -4 9)\">" +
      "<path d=\"M-7,8 Q-8,18 -6,21 L-2,21 Q-3,13 -2,8Z\" fill=\"" + pal.pants + "\"/>" +
      "<ellipse cx=\"-4\" cy=\"21.5\" rx=\"3.2\" ry=\"1.6\" fill=\"#3a2a1c\"/></g>" +
      "<g transform=\"rotate(" + legR + " 4 9)\">" +
      "<path d=\"M2,8 Q3,18 5,21 L8,21 Q7,13 6,8Z\" fill=\"" + pal.pants + "\"/>" +
      "<ellipse cx=\"6\" cy=\"21.5\" rx=\"3.2\" ry=\"1.6\" fill=\"#2e2118\"/></g>" +
      "<path d=\"M-12,-1 C-13,12 -6,16 0,16 C6,16 13,12 12,-1 C6,-5 -6,-5 -12,-1Z\" fill=\"" + pal.cloth + "\" stroke=\"#2a1c12\" stroke-width=\"1.15\"/>" +
      "<path d=\"M-6,-2 L6,-2 L5,2 L-5,2Z\" fill=\"" + pal.sash + "\" opacity=\"0.85\"/>" +
      "<path d=\"M-9,5 L9,6 L8,8.5 L-10,7.4Z\" fill=\"" + pal.sash + "\"/>" +
      "<g transform=\"rotate(" + armL + " -9 1)\">" +
      "<path d=\"M-10,0 Q-13,9 -10,15\" fill=\"none\" stroke=\"" + pal.skin + "\" stroke-width=\"3.4\" stroke-linecap=\"round\"/></g>" +
      "<g transform=\"rotate(" + armR + " 9 1)\">" +
      "<path d=\"M10,0 Q13,9 10,15\" fill=\"none\" stroke=\"" + pal.skin + "\" stroke-width=\"3.4\" stroke-linecap=\"round\"/></g>" +
      toolMarkup(pal.tool, pal) +
      "<circle cx=\"0\" cy=\"-12\" r=\"10\" fill=\"" + pal.skin + "\" stroke=\"#2a1c12\" stroke-width=\"1.1\"/>" +
      hairMarkup(pal.hairKind, pal) +
      "<ellipse cx=\"-5.2\" cy=\"-10.2\" rx=\"2.1\" ry=\"1.3\" fill=\"#f2b8a8\" opacity=\"0.55\"/>" +
      "<ellipse cx=\"5.2\" cy=\"-10.2\" rx=\"2.1\" ry=\"1.3\" fill=\"#f2b8a8\" opacity=\"0.55\"/>" +
      "<circle cx=\"-3.4\" cy=\"-12.1\" r=\"1.2\" fill=\"#2a1c12\"/>" +
      "<circle cx=\"3.4\" cy=\"-12.1\" r=\"1.2\" fill=\"#2a1c12\"/>" +
      "<circle cx=\"-2.9\" cy=\"-12.55\" r=\"0.4\" fill=\"#fff\"/>" +
      "<circle cx=\"3.9\" cy=\"-12.55\" r=\"0.4\" fill=\"#fff\"/>" +
      "<path d=\"M-2.4,-8 Q0,-6.2 2.4,-8\" fill=\"none\" stroke=\"#c27a6a\" stroke-width=\"0.95\" stroke-linecap=\"round\"/>" +
      "</g>";
  }
  function chibi(b, x, y, opts) {
    opts = opts || {};
    const pal = opts.pal || palOfName(opts.alias) || palOf(b.id);
    const on = !!opts.selected;
    const alias = opts.alias || aliasOf(b.id);
    const sc = opts.scale != null ? opts.scale : (on ? 2.35 : 2.15);
    const title = alias + " · " + (b.size != null ? b.size : "?") + "人。群体代表，不是独立个人。";
    const ring = on ? "<circle cx=\"0\" cy=\"18\" r=\"16\" fill=\"none\" stroke=\"#fff4c8\" stroke-width=\"2.2\" opacity=\"0.95\"/>" : "";
    const tag = opts.noTag ? "" : ("<g class=\"an-tag\" transform=\"translate(0,-56)\">" +
      "<rect x=\"-42\" y=\"-11\" width=\"84\" height=\"20\" rx=\"10\" fill=\"" + pal.tag + "\" stroke=\"#fff\" stroke-width=\"1.6\"/>" +
      "<text x=\"0\" y=\"3.2\" text-anchor=\"middle\" font-size=\"9\" fill=\"#fff\" font-weight=\"700\">" +
      esc(alias) + " · " + (b.size != null ? b.size : "?") + "人</text></g>");
    return "<g class=\"an-chibi band unit" + (on ? " selected" : "") + "\" data-band=\"" + esc(String(b.id)) +
      "\" data-unit=\"group-rep\" data-art=\"chibi\" transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")\">" +
      "<title>" + esc(title) + "</title>" + ring +
      "<g transform=\"scale(" + sc + ")\">" + chibiBody(b, { pose: opts.pose, pal: pal }) + "</g>" + tag + "</g>";
  }
  function portraitSvg(b, alias) {
    const pal = palOfName(alias) || palOf(b.id);
    return "<svg class=\"an-portrait\" viewBox=\"-22 -34 44 60\" width=\"72\" height=\"88\" aria-hidden=\"true\">" +
      chibiBody(b, { pose: "idle", pal: pal }) + "</svg>";
  }
  function pine(x, y, s) {
    s = s || 1;
    return "<g class=\"an-tree\" transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ") scale(" + s.toFixed(2) + ")\">" +
      "<rect x=\"-2.2\" y=\"-4\" width=\"4.4\" height=\"14\" rx=\"1\" fill=\"#6a4326\"/>" +
      "<path d=\"M0,-36 L16,-8 L-16,-8 Z\" fill=\"#245a2c\" stroke=\"#1a3d20\" stroke-width=\"0.6\"/>" +
      "<path d=\"M0,-28 L14,-2 L-14,-2 Z\" fill=\"#2f6e34\"/>" +
      "<path d=\"M0,-18 L12,8 L-12,8 Z\" fill=\"#3d8640\"/></g>";
  }
  function roundTree(x, y, s, fruit) {
    s = s || 1;
    const dots = fruit
      ? "<circle cx=\"-6\" cy=\"-18\" r=\"1.6\" fill=\"#d44a3a\"/><circle cx=\"5\" cy=\"-16\" r=\"1.5\" fill=\"#e05a42\"/><circle cx=\"1\" cy=\"-24\" r=\"1.4\" fill=\"#c43a32\"/>"
      : "";
    return "<g class=\"an-tree\" transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ") scale(" + s.toFixed(2) + ")\">" +
      "<rect x=\"-2.4\" y=\"-6\" width=\"4.8\" height=\"16\" rx=\"1.2\" fill=\"#6e4a28\"/>" +
      "<ellipse cx=\"-8\" cy=\"-16\" rx=\"10\" ry=\"9\" fill=\"#2f7a38\"/>" +
      "<ellipse cx=\"8\" cy=\"-15\" rx=\"11\" ry=\"10\" fill=\"#3b8c42\"/>" +
      "<ellipse cx=\"0\" cy=\"-24\" rx=\"12\" ry=\"11\" fill=\"#4a9c4c\" stroke=\"#2a5a30\" stroke-width=\"0.7\"/>" +
      dots + "</g>";
  }
  function bush(x, y, s) {
    s = s || 1;
    return "<g transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ") scale(" + s + ")\">" +
      "<ellipse rx=\"10\" ry=\"7\" fill=\"#3f7a34\"/>" +
      "<ellipse cx=\"-6\" cy=\"2\" rx=\"7\" ry=\"5\" fill=\"#2f6a2c\"/>" +
      "<ellipse cx=\"7\" cy=\"1.5\" rx=\"7\" ry=\"5.2\" fill=\"#4f9440\"/></g>";
  }
  function tuft(x, y) {
    return "<g transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")\">" +
      "<path d=\"M0,0 C-3,-8 2,-10 1.2,-1\" fill=\"none\" stroke=\"#5b8f3a\" stroke-width=\"1.3\"/>" +
      "<path d=\"M1.4,0 C0,-9 5,-8 3.4,0\" fill=\"none\" stroke=\"#6aa246\" stroke-width=\"1.15\"/>" +
      "<path d=\"M-1,0 C-4,-7 -1,-9 -0.2,-1\" fill=\"none\" stroke=\"#7bb24c\" stroke-width=\"1\"/></g>";
  }
  function flower(x, y, col) {
    return "<g transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")\">" +
      "<circle r=\"1.6\" fill=\"" + col + "\"/><circle cx=\"0\" cy=\"0\" r=\"0.6\" fill=\"#f6e27a\"/></g>";
  }
  function boulder(x, y, s) {
    s = s || 1;
    return "<g transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ") scale(" + s + ")\">" +
      "<path d=\"M-8,4 C-10,-2 -4,-8 2,-7 C8,-8 10,-1 7,5 C2,8 -6,8 -8,4Z\" fill=\"#9a8f82\" stroke=\"#5a5248\" stroke-width=\"0.9\"/>" +
      "<path d=\"M-3,-3 Q1,-5 4,-1\" fill=\"none\" stroke=\"#cfc6ba\" stroke-width=\"0.8\"/></g>";
  }
  function tent(x, y, pal) {
    return "<g transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")\">" +
      "<path d=\"M-14,10 L0,-12 L14,10 Z\" fill=\"" + pal.cloth + "\" stroke=\"#2a1c12\" stroke-width=\"1.15\"/>" +
      "<path d=\"M0,-12 L0,10\" stroke=\"#2a1c12\" stroke-width=\"1\"/>" +
      "<path d=\"M-4,10 L0,2 L4,10 Z\" fill=\"#3a2a18\"/></g>";
  }
  function fieldPatch(x, y, units) {
    const w = 26 + Math.min(14, units * 1.6);
    const h = 16 + Math.min(8, units);
    let crops = "";
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 5; c++) {
        const cx = -w / 2 + 5 + c * ((w - 8) / 4);
        const cy = -h / 2 + 4 + r * ((h - 6) / 2);
        crops += "<rect x=\"" + cx.toFixed(1) + "\" y=\"" + cy.toFixed(1) + "\" width=\"3.4\" height=\"2.6\" rx=\"0.7\" fill=\"#5fa83a\"/>";
      }
    }
    return "<g class=\"an-field\" data-field-units=\"" + units.toFixed(3) + "\" transform=\"translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")\">" +
      "<rect x=\"" + (-w / 2) + "\" y=\"" + (-h / 2) + "\" width=\"" + w + "\" height=\"" + h + "\" rx=\"3\" fill=\"#b6864a\" stroke=\"#6e4a22\" stroke-width=\"1.2\"/>" +
      crops + "</g>";
  }
  function convexHull(pts) {
    const p = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    if (p.length < 3) return p;
    const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const low = [];
    p.forEach((pt) => {
      while (low.length >= 2 && cross(low[low.length - 2], low[low.length - 1], pt) <= 0) low.pop();
      low.push(pt);
    });
    const up = [];
    for (let i = p.length - 1; i >= 0; i--) {
      const pt = p[i];
      while (up.length >= 2 && cross(up[up.length - 2], up[up.length - 1], pt) <= 0) up.pop();
      up.push(pt);
    }
    low.pop(); up.pop();
    return low.concat(up);
  }
  function chaikin(pts, n) {
    let p = pts;
    for (let k = 0; k < n; k++) {
      const out = [];
      for (let i = 0; i < p.length; i++) {
        const a = p[i], b = p[(i + 1) % p.length];
        out.push([a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25]);
        out.push([a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75]);
      }
      p = out;
    }
    return p;
  }
  function hullPath(pts, pad) {
    const hull = convexHull(pts);
    if (!hull.length) return "";
    const cx = hull.reduce((s, p) => s + p[0], 0) / hull.length;
    const cy = hull.reduce((s, p) => s + p[1], 0) / hull.length;
    const exp = hull.map((p) => {
      const dx = p[0] - cx, dy = p[1] - cy;
      const n = Math.sqrt(dx * dx + dy * dy) || 1;
      return [p[0] + dx / n * pad, p[1] + dy / n * pad];
    });
    const smooth = chaikin(exp, 2);
    return "M" + smooth.map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join("L") + "Z";
  }
  function jitter(h, mag) {
    return [((h % 97) / 97 - 0.5) * mag, (((h >>> 8) % 53) / 53 - 0.5) * mag];
  }
  function spreadBands(bands, map, cellCenter) {
    const pts = (bands || []).map((b) => {
      const cell = map.cells[b.cell];
      const xy = cell ? cellCenter(cell) : [0, 0];
      return { b: b, x: xy[0], y: xy[1] };
    });
    const home = pts.map((p) => ({ x: p.x, y: p.y }));
    const minD = 96;
    const maxMove = 34;
    const streamX = 260;
    for (let n = 0; n < 12; n++) {
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[j].x - pts[i].x, dy = pts[j].y - pts[i].y;
          const d = Math.hypot(dx, dy) || 0.2;
          if (d >= minD) continue;
          const f = (minD - d) / 2;
          pts[i].x -= dx / d * f; pts[i].y -= dy / d * f;
          pts[j].x += dx / d * f; pts[j].y += dy / d * f;
        }
      }
      pts.forEach((p, i) => {
        p.x = Math.max(home[i].x - maxMove, Math.min(home[i].x + maxMove, p.x));
        p.y = Math.max(home[i].y - maxMove, Math.min(home[i].y + maxMove, p.y));
        if (home[i].x < streamX) p.x = Math.min(p.x, streamX - 42);
        else p.x = Math.max(p.x, streamX + 42);
      });
    }
    return pts;
  }
  function streamMarkup(blocks) {
    if (!blocks.length) return "";
    const byRow = {};
    blocks.forEach((p) => {
      const r = p.c.row;
      if (!byRow[r]) byRow[r] = { x: 0, y: 0, n: 0 };
      byRow[r].x += p.x; byRow[r].y += p.y; byRow[r].n++;
    });
    const spine = Object.keys(byRow).sort((a, b) => +a - +b).map((r) => ({
      x: byRow[r].x / byRow[r].n, y: byRow[r].y / byRow[r].n,
    }));
    if (spine.length < 2) return "";
    spine.unshift({ x: spine[0].x - 6, y: spine[0].y - 90 });
    spine.push({ x: spine[spine.length - 1].x + 8, y: spine[spine.length - 1].y + 90 });
    const bank = (w) => {
      const L = spine.map((p) => [p.x - w, p.y]);
      const R = spine.map((p) => [p.x + w, p.y]).reverse();
      return "M" + L.concat(R).map((p) => p[0].toFixed(1) + "," + p[1].toFixed(1)).join("L") + "Z";
    };
    let rocks = "";
    spine.forEach((p, i) => {
      if (i === 0 || i === spine.length - 1) return;
      rocks += boulder(p.x - 18 - (i % 3) * 3, p.y + 4, 0.85 + (i % 3) * 0.12);
      rocks += boulder(p.x + 16 + (i % 2) * 4, p.y - 3, 0.7 + (i % 4) * 0.1);
    });
    return "<path d=\"" + bank(26) + "\" fill=\"#c4b49a\" stroke=\"#8a7a62\" stroke-width=\"1.1\"/>" +
      "<path d=\"" + bank(13) + "\" fill=\"#6eb7d2\"/>" +
      "<path d=\"" + bank(7) + "\" fill=\"#8fd0e6\" opacity=\"0.7\"/>" + rocks;
  }
  function paint(svg, st) {
    if (!svg || !st || !st.map) return;
    svg.setAttribute("viewBox", "-80 -90 720 480");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.setAttribute("preserveAspectRatio", "xMidYMid slice");
    const rec = st.rec;
    const cells = st.map.cells || [];
    const farm = rec && rec.farm && rec.farm.schema === "farm-1" ? rec.farm : null;
    const fields = farm && Array.isArray(farm.field_m) ? farm.field_m : null;
    const alias = bindAliases((rec && rec.bands || []).map((b) => b.id));
    const pass = [];
    const block = [];
    const occ = new Set();
    (rec && rec.bands || []).forEach((b) => occ.add(+b.cell));
    cells.forEach((c) => {
      const xy = st.cellCenter(c);
      (c.passable ? pass : block).push({ c: c, x: xy[0], y: xy[1] });
    });
    const left = pass.filter((p) => p.c.col <= 2);
    const right = pass.filter((p) => p.c.col >= 5);
    let out = "<defs>" +
      "<linearGradient id=\"anSky\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">" +
      "<stop offset=\"0%\" stop-color=\"#6eb8ea\"/><stop offset=\"42%\" stop-color=\"#c5e8ff\"/>" +
      "<stop offset=\"68%\" stop-color=\"#d9edb4\"/><stop offset=\"100%\" stop-color=\"#7fb445\"/></linearGradient>" +
      "<linearGradient id=\"anHill\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">" +
      "<stop offset=\"0%\" stop-color=\"#8fbc5a\"/><stop offset=\"100%\" stop-color=\"#5e9140\"/></linearGradient>" +
      "<pattern id=\"anGrass\" width=\"36\" height=\"22\" patternUnits=\"userSpaceOnUse\">" +
      "<path d=\"M4,18 C2,8 7,7 6,18\" fill=\"none\" stroke=\"#5d8f38\" stroke-width=\"1.1\"/>" +
      "<path d=\"M12,20 C10,9 16,8 15,20\" fill=\"none\" stroke=\"#6aa246\" stroke-width=\"1\"/>" +
      "<path d=\"M22,19 C21,10 26,9 25,19\" fill=\"none\" stroke=\"#4e7f32\" stroke-width=\"1.05\"/>" +
      "<path d=\"M30,20 C29,11 34,10 33,20\" fill=\"none\" stroke=\"#74a84a\" stroke-width=\"0.95\"/>" +
      "</pattern></defs>";
    out += "<rect class=\"an-sky\" x=\"-80\" y=\"-90\" width=\"720\" height=\"480\" fill=\"url(#anSky)\"/>";
    out += "<path d=\"M-80,70 L10,-8 L70,42 L140,-28 L210,36 L290,-18 L370,40 L460,-22 L560,32 L640,8 L640,120 L-80,120Z\" fill=\"#8aa7c4\" opacity=\"0.7\"/>";
    out += "<path d=\"M-80,88 L40,22 L110,62 L190,8 L270,54 L360,18 L450,58 L560,24 L640,48 L640,150 L-80,150Z\" fill=\"#9bb3c9\"/>";
    out += "<path d=\"M120,-18 L140,22 L100,22Z\" fill=\"#eef6ff\" opacity=\"0.55\"/>";
    out += "<path d=\"M290,-8 L312,28 L268,28Z\" fill=\"#eef6ff\" opacity=\"0.45\"/>";
    out += "<path d=\"M460,-12 L478,24 L442,24Z\" fill=\"#eef6ff\" opacity=\"0.5\"/>";
    out += "<ellipse cx=\"90\" cy=\"4\" rx=\"70\" ry=\"22\" fill=\"#fff\" opacity=\"0.5\"/>";
    out += "<ellipse cx=\"400\" cy=\"-18\" rx=\"90\" ry=\"26\" fill=\"#fff\" opacity=\"0.42\"/>";
    out += "<rect x=\"-80\" y=\"70\" width=\"720\" height=\"320\" fill=\"#7fb445\"/>";
    out += "<rect x=\"-80\" y=\"70\" width=\"720\" height=\"320\" fill=\"url(#anGrass)\" opacity=\"0.55\"/>";
    out += "<path d=\"M-80,210 C40,160 160,230 280,180 C400,130 520,210 640,170 L640,390 L-80,390Z\" fill=\"#6fa03c\" opacity=\"0.35\"/>";
    out += "<ellipse cx=\"110\" cy=\"168\" rx=\"130\" ry=\"54\" fill=\"#8fbc52\" opacity=\"0.55\"/>";
    out += "<ellipse cx=\"120\" cy=\"250\" rx=\"120\" ry=\"48\" fill=\"#67963a\" opacity=\"0.28\"/>";
    out += "<ellipse cx=\"430\" cy=\"160\" rx=\"125\" ry=\"50\" fill=\"#8fbc52\" opacity=\"0.5\"/>";
    out += "<ellipse cx=\"450\" cy=\"255\" rx=\"118\" ry=\"46\" fill=\"#67963a\" opacity=\"0.28\"/>";
    out += "<ellipse cx=\"90\" cy=\"310\" rx=\"55\" ry=\"18\" fill=\"#c4a06a\" opacity=\"0.28\"/>";
    out += "<ellipse cx=\"470\" cy=\"300\" rx=\"48\" ry=\"16\" fill=\"#c4a06a\" opacity=\"0.26\"/>";
    if (left.length) {
      out += "<path d=\"" + hullPath(left.map((p) => [p.x, p.y + 10]), 58) + "\" fill=\"#86b84a\" stroke=\"#5d8230\" stroke-width=\"1.4\"/>";
      out += "<path d=\"" + hullPath(left.map((p) => [p.x, p.y + 10]), 58) + "\" fill=\"url(#anGrass)\" opacity=\"0.45\"/>";
    }
    if (right.length) {
      out += "<path d=\"" + hullPath(right.map((p) => [p.x, p.y + 10]), 58) + "\" fill=\"#7db043\" stroke=\"#5d8230\" stroke-width=\"1.4\"/>";
      out += "<path d=\"" + hullPath(right.map((p) => [p.x, p.y + 10]), 58) + "\" fill=\"url(#anGrass)\" opacity=\"0.45\"/>";
    }
    out += streamMarkup(block);
    const edgeTrees = [
      [-40, 120, 1.3, "p"], [20, 100, 1.1, "r"], [80, 88, 1.4, "p"], [160, 96, 1.2, "r"],
      [240, 84, 1.5, "p"], [500, 92, 1.35, "p"], [560, 108, 1.2, "r"], [610, 130, 1.45, "p"],
      [-30, 200, 1.1, "r"], [600, 220, 1.2, "p"], [-20, 300, 1.3, "p"], [580, 310, 1.15, "r"],
      [40, 340, 1.0, "r"], [520, 350, 1.25, "p"],
    ];
    edgeTrees.forEach((t) => {
      out += t[3] === "p" ? pine(t[0], t[1], t[2]) : roundTree(t[0], t[1], t[2], false);
    });
    pass.forEach((p) => {
      const h = hashId("veg" + p.c.i);
      const j = jitter(h, 28);
      const j2 = jitter(h * 7 + 13, 22);
      const busy = occ.has(p.c.i);
      const lush = rec && rec.stock ? Math.min(1, (rec.stock[p.c.i] || 0) / 90000000) : 0.4;
      if (h % 3 === 0) out += tuft(p.x - 10 + j[0], p.y + 14 + j[1]);
      if (h % 4 === 1) out += tuft(p.x + 12 + j2[0], p.y + 10 + j2[1]);
      if (h % 5 === 2) out += flower(p.x + 8 + j[0], p.y + 16, h % 2 ? "#e07a9a" : "#f0d45a");
      if (fields && fields[p.c.i] > 0) {
        out += fieldPatch(p.x + (busy ? 30 : j[0] * 0.4), p.y + (busy ? 14 : 6), fields[p.c.i] / 1000);
      }
      if (busy) {
        out += (h % 2 ? pine : roundTree)(p.x - 30 + j[0] * 0.4, p.y - 20 + j[1] * 0.3, 1.05 + (h % 4) * 0.1, h % 3 === 0);
        out += bush(p.x + 28 + j2[0] * 0.3, p.y + 14, 0.95);
      } else {
        const kind = h % 5;
        const sc = 0.95 + (h % 7) * 0.12;
        if (kind === 0 || kind === 1) out += pine(p.x + j[0], p.y + j[1] * 0.6, sc);
        if (kind === 2 || kind === 3) out += roundTree(p.x + j2[0], p.y + j[1] * 0.5, sc * 0.95, kind === 3);
        if (kind === 4) {
          out += pine(p.x + j[0] - 10, p.y + j[1], sc);
          out += roundTree(p.x + j2[0] + 12, p.y + j2[1], 0.9, false);
        }
        if (h % 3 === 0) out += bush(p.x + j2[0], p.y + 12 + j[1] * 0.3, 1);
        if (lush > 0.7 && h % 4 === 0) out += roundTree(p.x + j[0] * 0.5 - 12, p.y + 10, 0.85, true);
      }
      out += "<path class=\"cell\" d=\"M" + (p.x - 24) + "," + p.y + " L" + p.x + "," + (p.y - 18) +
        " L" + (p.x + 24) + "," + p.y + " L" + p.x + "," + (p.y + 18) + "Z\" fill=\"transparent\" data-cell=\"" + p.c.i + "\"/>";
    });
    const laid = spreadBands(rec && rec.bands || [], st.map, st.cellCenter)
      .slice().sort((a, b) => a.y - b.y);
    laid.forEach((p) => {
      const name = alias(p.b.id);
      out += tent(p.x - 32, p.y + 10, palOfName(name));
    });
    const evs = (rec && rec.events) || [];
    evs.slice(0, 3).forEach((e, i) => {
      if (e.cell == null || !st.map.cells[e.cell]) return;
      const xy = st.cellCenter(st.map.cells[e.cell]);
      const txt = speech(e, alias);
      const w = Math.min(132, 16 + txt.length * 7.2);
      const side = i % 2 ? -1 : 1;
      out += "<g class=\"an-bubble\" transform=\"translate(" + (xy[0] + side * 36) + "," + (xy[1] - 70) + ")\">" +
        "<rect x=\"-8\" y=\"-13\" width=\"" + w + "\" height=\"20\" rx=\"9\" fill=\"#fff\" stroke=\"#d5e4cc\"/>" +
        "<text x=\"2\" y=\"1.6\" font-size=\"8\" fill=\"#334433\">" + esc(txt.slice(0, 18)) + "</text></g>";
    });
    laid.forEach((p) => {
      const on = st.selBand && String(st.selBand) === String(p.b.id);
      const name = alias(p.b.id);
      out += chibi(p.b, p.x, p.y - 4, {
        selected: on, pose: on && st.pose ? st.pose : "idle",
        alias: name, pal: palOfName(name),
      });
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
    if (st.$("an-year")) st.$("an-year").textContent = String(t);
    if (st.$("an-pop")) st.$("an-pop").textContent = pop == null ? "—" : String(pop);
    if (st.$("an-pop-top")) st.$("an-pop-top").textContent = pop == null ? "—" : String(pop);
    if (st.$("an-bands")) st.$("an-bands").textContent = nb == null ? "—" : String(nb);
    if (st.$("an-bands-top")) st.$("an-bands-top").textContent = nb == null ? "—" : String(nb);
    if (st.$("an-fields")) st.$("an-fields").textContent = farm ? (fieldU.toFixed(1) + " 单位") : "不支持耕作";
    if (st.$("an-food")) st.$("an-food").textContent = harv == null ? (farm ? "0" : "不支持耕作") : (harv / need).toFixed(1) + " 人年";
    if (st.$("an-mig")) st.$("an-mig").textContent = rec && rec.year && rec.year.mig_total != null ? String(rec.year.mig_total) : "未记录";
    if (st.$("an-aid")) st.$("an-aid").textContent = rec && rec.aid && rec.aid.events != null ? String(rec.aid.events) : "未记录";
    if (st.$("an-badge")) st.$("an-badge").textContent = "示例世界 · 历史回放";
    if (st.$("an-scrub") && t != null) st.$("an-scrub").value = String(t);
    if (st.$("an-run") && st.runs) {
      const cur = run && run.run_id;
      st.$("an-run").innerHTML = st.runs.map((r) => {
        const sel = r.run_id === cur ? " selected" : "";
        const lab = r.label || ("世界 " + String(r.run_id).slice(0, 6));
        return "<option value=\"" + esc(r.run_id) + "\"" + sel + ">" + esc(lab) + "</option>";
      }).join("");
    }
    const alias = bindAliases((rec && rec.bands || []).map((b) => b.id));
    const list = st.$("an-events");
    if (list) {
      const items = (rec && rec.events) || [];
      list.innerHTML = "<h3>这一年</h3>" + (items.slice(0, 5).map((e) => {
        return "<button type=\"button\" class=\"an-ev\" data-eid=\"" + esc(String(e.id || "")) + "\" data-year=\"" + t + "\">" +
          esc(speech(e, alias)) + "</button>";
      }).join("") || "<p class=\"muted\">这一年没有可核实事件。</p>");
    }
    const card = st.$("an-card");
    if (card && rec) {
      const b = (rec.bands || []).find((x) => String(x.id) === String(st.selBand)) || rec.bands[0];
      if (b) {
        const days = daysOfStore(b.store, b.size, need);
        const al = alias(b.id);
        const farmCell = farm && farm.cells && farm.cells.find((c) => +c.cell === +b.cell);
        const fu = farmCell ? (farmCell.field_after_m / 1000) : null;
        card.innerHTML = "<div class=\"an-card-h\">" + portraitSvg(b, al) +
          "<div><strong>" + esc(al) + "</strong>" +
          "<div class=\"muted\">来源 ID " + esc(String(b.id)) + "</div>" +
          "<ul class=\"an-card-kv\">" +
          "<li>人口 " + b.size + " 人</li>" +
          "<li>储粮 " + (b.store / need).toFixed(1) + " 人年" +
          (days == null ? "" : "，约 " + days + " 天") + "</li>" +
          "<li>耕地 " + (fu == null ? (farm ? "本格无田" : "不支持耕作") : fu.toFixed(1) + " 单位") + "</li></ul></div></div>";
      }
    }
    const mini = st.$("an-mini");
    if (mini && st.map) {
      let m = "<svg viewBox=\"0 0 120 90\" class=\"an-mini-svg\">";
      (st.map.cells || []).forEach((c) => {
        const x = 8 + (c.col + (c.row % 2 ? 0.5 : 0)) * 12;
        const y = 8 + c.row * 9;
        m += "<rect x=\"" + x + "\" y=\"" + y + "\" width=\"10\" height=\"8\" rx=\"2\" fill=\"" + (c.passable ? "#8fbc6a" : "#8a8680") + "\"/>";
      });
      (rec && rec.bands || []).forEach((b) => {
        const c = st.map.cells[b.cell];
        if (!c) return;
        const x = 13 + (c.col + (c.row % 2 ? 0.5 : 0)) * 12;
        const y = 12 + c.row * 9;
        m += "<circle cx=\"" + x + "\" cy=\"" + y + "\" r=\"2.6\" fill=\"" + palOfName(alias(b.id)).tag + "\" stroke=\"#fff\" stroke-width=\"0.6\"/>";
      });
      m += "</svg>";
      mini.innerHTML = m;
    }
  }
  root.AnimeScene = {
    aliasOf: aliasOf, palOf: palOf, palOfName: palOfName, daysOfStore: daysOfStore, speech: speech,
    paint: paint, fillChrome: fillChrome, portraitSvg: portraitSvg, chibi: chibi,
  };
})(typeof window !== "undefined" ? window : globalThis);
