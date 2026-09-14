/* EXP-07 farming UI helpers. Field scale is field_m/1000 耕作规模单位, not kcal. */
(function (root) {
  "use strict";
  const TYPES = ["field_built", "field_decay", "farm_harvest"];
  const TYPE_LABEL = {
    field_built: "开垦",
    field_decay: "弃耕退化",
    farm_harvest: "耕作采收",
  };

  function farmRecord(rec) {
    if (!rec || !rec.farm || rec.farm.schema !== "farm-1") return null;
    return rec.farm;
  }
  function supported(run, cfg) {
    if (run && run.engine === "exp07") return true;
    const name = (run && run.engine) || "";
    const inf = cfg && cfg.engines && cfg.engines[name];
    if (inf && inf.engine_params && inf.engine_params.indexOf("farm_m") >= 0) return true;
    if (inf && inf.metrics && inf.metrics.farm === true) return true;
    return false;
  }
  function supportLabel(run, rec, cfg) {
    if (supported(run, cfg)) {
      const m = run && run.farm_m;
      return m == null ? "支持耕作（本运行 FARM_M 未写入摘要）" : ("支持耕作 · FARM_M " + m + "‰");
    }
    if (rec && rec.farm && rec.farm.schema === "farm-1") return "支持耕作";
    return "不支持耕作";
  }
  function scaleUnits(fieldM) {
    const n = Number(fieldM);
    if (!Number.isFinite(n) || n <= 0) return 0;
    return n / 1000;
  }
  function fieldVector(rec) {
    const farm = farmRecord(rec);
    if (!farm || !Array.isArray(farm.field_m)) return null;
    return farm.field_m;
  }
  function cellFarm(rec, cell) {
    const farm = farmRecord(rec);
    if (!farm) return null;
    const cells = farm.cells || [];
    const hit = cells.find((c) => c && +c.cell === +cell);
    if (hit) return hit;
    const vec = farm.field_m;
    if (!vec || vec[+cell] == null) return { cell: +cell, field_before_m: 0, field_after_m: 0, absent: true };
    const after = +vec[+cell] || 0;
    return { cell: +cell, field_before_m: after, field_after_m: after, built_m: 0, decayed_m: 0, worked_m: 0 };
  }
  function cellCopy(cellRec, rec, t) {
    if (!farmRecord(rec)) {
      return {
        supported: false,
        title: "不支持耕作",
        lines: ["这个引擎没有耕地记录。不是农业产出 0。"],
      };
    }
    const c = cellRec || {};
    const before = c.field_before_m != null ? c.field_before_m : 0;
    const after = c.field_after_m != null ? c.field_after_m : 0;
    const built = c.built_m || 0;
    const decayed = c.decayed_m || 0;
    const lines = [];
    lines.push("年末规模 " + scaleUnits(after).toFixed(3) + " 个耕作规模单位（field_m/1000）。不是 kcal，不能加进野外食物。");
    lines.push("旧规模 " + scaleUnits(before).toFixed(3) + " → 开垦 +" + scaleUnits(built).toFixed(3)
      + " / 退化 −" + scaleUnits(decayed).toFixed(3) + " → 新规模 " + scaleUnits(after).toFixed(3) + "。");
    lines.push("投入劳动 " + (c.worked_m != null ? c.worked_m : "未记录")
      + " · 开垦劳动见参与者 farm_effort_m。有效劳动与天气刻度 weather_m="
      + (c.weather_m == null ? "未记录（新开垦当年不产）" : c.weather_m) + "。");
    lines.push("潜在采收 " + (c.potential_kcal != null ? c.potential_kcal : "未记录")
      + " kcal · 实际采收 " + (c.harvested_kcal != null ? c.harvested_kcal : "未记录")
      + " kcal · 未采收 " + (c.uncollected_kcal != null ? c.uncollected_kcal : "未记录") + " kcal。");
    lines.push("新开垦下一年才产出：当年 built>0 且 potential 为 0 是机制，不是漏记。");
    lines.push("未采收不是库存损耗：它从未进入群体储粮。");
    if (t === 0) lines.push("第 0 年 field_m 全 0、cells 空。");
    const parts = Array.isArray(c.participants) ? c.participants : [];
    return {
      supported: true, cell: c.cell, before: before, after: after, built: built, decayed: decayed,
      worked: c.worked_m, weather: c.weather_m, potential: c.potential_kcal,
      harvested: c.harvested_kcal, uncollected: c.uncollected_kcal,
      participants: parts, lines: lines, title: "第 " + c.cell + " 号格耕地",
    };
  }
  function participantLine(p, rec) {
    const id = String(p.id);
    const live = (rec && rec.bands || []).find((b) => String(b.id) === id);
    const name = live ? live.name : ("群体 " + id.slice(0, 8));
    const loc = live
      ? ("年末在第 " + live.cell + " 格")
      : "历史参与者：已迁移或消失，不伪造现时位置";
    return name + " · 相位前人口 " + p.population_before
      + " · 耕作劳动 " + p.farm_effort_m + " · 采集劳动 " + p.forage_effort_m
      + " · 采集 kcal " + p.forage_kcal + " · 作物 kcal " + p.crop_kcal
      + "。 " + loc + "。";
  }
  function isFarmEvent(e) {
    return !!(e && TYPES.indexOf(e.type) >= 0);
  }
  function farmEventLabel(type) {
    return TYPE_LABEL[type] || type;
  }
  function yearFarmRows(rec) {
    const farm = farmRecord(rec);
    if (!farm) return { supported: false, label: "不支持耕作" };
    const y = farm.year || {};
    const c = farm.cum || {};
    const total = farm.field_total_m != null ? farm.field_total_m
      : (Array.isArray(farm.field_m) ? farm.field_m.reduce((s, n) => s + (n || 0), 0) : 0);
    return {
      supported: true,
      fieldTotalUnits: scaleUnits(total),
      year: y, cum: c,
    };
  }
  function miniFieldSvg(rec, opts) {
    opts = opts || {};
    const W = 160, H = 132, r = 9;
    const farm = farmRecord(rec);
    if (!farm) {
      return "<svg class=\"farm-mini\" viewBox=\"0 0 " + W + " " + H + "\"><text x=\"8\" y=\"20\" fill=\"#c4b58a\" font-size=\"10\">不支持耕作</text></svg>";
    }
    const vec = farm.field_m || [];
    const cells = opts.cells || [];
    let out = "<svg class=\"farm-mini\" viewBox=\"0 0 " + W + " " + H + "\" data-farm-mini=\"1\">";
    const SQ3 = Math.sqrt(3);
    cells.forEach((c) => {
      const cx = 10 + (c.col + (c.row % 2 === 0 ? 0.5 : 0)) * SQ3 * r + SQ3 * r / 2;
      const cy = 10 + c.row * 1.5 * r + r;
      let d = "";
      for (let k = 0; k < 6; k++) {
        const a = Math.PI / 180 * (60 * k - 90);
        d += (k ? "L" : "M") + (cx + r * Math.cos(a)).toFixed(1) + "," + (cy + r * Math.sin(a)).toFixed(1);
      }
      d += "Z";
      const m = vec[c.i] || 0;
      const fill = m > 0 ? "rgba(196,168,72," + Math.min(0.85, 0.18 + scaleUnits(m) / 40) + ")" : "rgba(20,24,18,0.4)";
      out += "<path d=\"" + d + "\" fill=\"" + fill + "\" stroke=\"#3a4030\" stroke-width=\"0.6\" data-cell=\"" + c.i + "\" data-field-m=\"" + m + "\"/>";
    });
    out += "</svg>";
    return out;
  }
  function eventIdentity(runId, eventId) {
    return String(runId || "") + "::" + String(eventId || "");
  }
  const FarmingLogic = {
    TYPES: TYPES, TYPE_LABEL: TYPE_LABEL,
    farmRecord: farmRecord, supported: supported, supportLabel: supportLabel,
    scaleUnits: scaleUnits, fieldVector: fieldVector, cellFarm: cellFarm,
    cellCopy: cellCopy, participantLine: participantLine, isFarmEvent: isFarmEvent,
    farmEventLabel: farmEventLabel, yearFarmRows: yearFarmRows, miniFieldSvg: miniFieldSvg,
    eventIdentity: eventIdentity,
  };
  root.FarmingLogic = FarmingLogic;
  if (typeof module !== "undefined" && module.exports) module.exports = FarmingLogic;
})(typeof window !== "undefined" ? window : globalThis);
