"""观看计划：把**已经存下来的**一段历史整理成可回放的章节目录。

这是一层**只读投影**，不是新机制：

* 不跑模拟、不补事件、不写年记录/检查点/模型对象，也不占模拟任务槽；
* 只扫描"请求开始那一刻"确定下来的有效前缀 `0..recorded_through`，
  尾巴上还没写完的那一年不算数（判据在 `store._lines`）；
* 子运行读**自己**那份完整历史，从第 0 年起，不依赖父运行还在不在。

身份目录是逐年**实际在世记录**扫出来的，不是拿"群体总数有没有变多"去猜：
同一年一个群体消失、另一个分裂，净数不变，这种年份照样得扫。
`first_year` 是"这份档案里第一次可核实地出现"，不是生日；`last_year` 也不是死亡年份；
只有真的出现过 `extinct` 事件才会填 `extinct_year`。
"""
from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import config, store

SCHEMA = "watch-plan-1"

# 章节种类（除开局与末年概览外，都对应一条**真实事件**）。
KIND_ORIGIN = "origin"
KIND_FINAL = "final"
EVENT_KINDS = ("clearing", "harvest", "migrate", "aid", "repay")

# 每种章节对应记录里的哪种事件。回助不是独立事件类型：它是 aid 上的 repay=true。
_MATCH = {
    "clearing": lambda e: e.get("type") == "field_built",
    "harvest": lambda e: e.get("type") == "farm_harvest",
    "migrate": lambda e: e.get("type") == "migrate",
    "aid": lambda e: e.get("type") == "aid" and not e.get("repay"),
    "repay": lambda e: e.get("type") == "aid" and bool(e.get("repay")),
}
_TITLE = {
    "clearing": "第一次开垦", "harvest": "第一次收成", "migrate": "第一次迁移",
    "aid": "第一次援助", "repay": "第一次回助",
    KIND_ORIGIN: "世界开局", KIND_FINAL: "目前记录到的最后一年",
}

# 缺某一类时，理由必须分清是哪一种缺。
REASON_NO_MECHANISM = "engine_lacks_mechanism"   # 这台引擎根本没有这套机制
REASON_PARAM_ZERO = "param_zero"                 # 机制在，但控制它的参数是 0
REASON_NOT_OBSERVED = "not_observed"             # 机制开着、参数非 0，这段历史里没发生
REASON_INCOMPLETE = "history_incomplete"         # 记录还没写完，后面可能还会出现
REASON_OUTSIDE = "outside_watermark"             # 这份水位里没有，但已记录的后面有
REASON_UNKNOWN_ENGINE = "capability_unknown"     # 记录没写引擎、或引擎不在登记表里

# 哪个参数管哪一类。迁移是所有引擎都有的基础机制，不受单独参数开关控制。
_PARAM_OF = {"clearing": "farm_m", "harvest": "farm_m", "aid": "aid_m", "recip": "recip_m"}

_CACHE: "OrderedDict[Tuple, Dict[str, Any]]" = OrderedDict()
_CACHE_MAX = 16


class PlanError(ValueError):
    """历史读不出来：明确报错，绝不返回一份空目录再宣布"看完了"。"""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _fact(value, unit, source, **extra) -> Dict[str, Any]:
    """一条事实 = 数值 + 原始单位 + 它在记录里的字段名。解释留给界面，这里不写故事。"""
    out = {"value": value, "unit": unit, "source": source}
    out.update(extra)
    return out


def _year_fact(value, unit, source, year, note) -> Dict[str, Any]:
    """**全年口径**的读数：标清年份与 year_end 口径，免得被说成这一件事造成的变化。"""
    return _fact(value, unit, source, year=year, basis="year_end", note=note)


def _watermark(run_id: str) -> int:
    """请求开始那一刻的有效记录水位；-1 表示一年都还没写完。"""
    return store.year_count(run_id) - 1


def _file_key(run_id: str) -> Tuple:
    p = store.years_path(run_id)
    if not p.exists():
        return ("missing",)
    st = p.stat()
    return (st.st_mtime_ns, st.st_size)


# --------------------------------------------------------------------------- 身份目录
def _scan(run_id: str, through: int):
    """一次扫描同时产出身份目录与每一类的首次事件。**只读**，逐年记录一行都不改。"""
    ident: Dict[str, Dict[str, Any]] = {}
    first: Dict[str, Tuple[int, int, Dict[str, Any]]] = {}
    origin_rec = final_rec = None
    year_index: Dict[int, Dict[str, Any]] = {}
    seen_event_ids: Dict[str, int] = {}

    for rec in store.iter_years(run_id):
        t = rec["t"]
        if t > through:
            break
        if t == 0:
            origin_rec = rec
        final_rec = rec
        year_index[t] = rec

        # 在世记录：**逐年实际出现过的群体**，不看净数增减。
        for b in rec.get("bands", ()):
            bid = str(b["id"])
            row = ident.get(bid)
            if row is None:
                ident[bid] = {"id": bid, "first_year": t, "last_year": t,
                              "parent_id": None, "extinct_year": None}
            else:
                row["last_year"] = t

        for i, e in enumerate(rec.get("events", ())):
            eid = e.get("id")
            if eid is not None:
                seen_event_ids[eid] = t
            etype = e.get("type")
            if etype == "split":
                child = str(e.get("band"))
                if child in ident and ident[child]["parent_id"] is None:
                    # 亲缘只认日志里写下来的那一条，不按"谁先出现"猜。
                    ident[child]["parent_id"] = str(e.get("parent"))
            elif etype == "extinct":
                bid = str(e.get("band"))
                if bid in ident:
                    ident[bid]["extinct_year"] = t
            for kind, match in _MATCH.items():
                if kind not in first and match(e):
                    first[kind] = (t, i, e)
    return ident, first, origin_rec, final_rec, year_index, seen_event_ids


def _sorted_identities(ident: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 (first_year, 数值型完整 ID) 排序。**ID 一路是字符串**，排序才转数值 ——
    64 位 id 交给 JS 的 Number 排序会掉精度，所以顺序由后台定死。"""
    def key(row):
        try:
            n = int(row["id"])
        except (TypeError, ValueError):
            n = float("inf")
        return (row["first_year"], n, row["id"])
    return sorted(ident.values(), key=key)


# --------------------------------------------------------------------------- 章节
def _origin_chapter(rec) -> Dict[str, Any]:
    agg = rec["agg"]
    return {
        "chapter_id": KIND_ORIGIN, "kind": KIND_ORIGIN, "year": rec["t"],
        "title": _TITLE[KIND_ORIGIN], "event_id": None, "actor_ids": [],
        "cell": None, "from": None, "to": None, "basis_event_ids": [],
        "facts": {
            "pop": _fact(agg["pop"], "人", "agg.pop", year=rec["t"], basis="snapshot"),
            "bands": _fact(agg["bands"], "个群体", "agg.bands", year=rec["t"],
                           basis="snapshot"),
            "store_total": _fact(agg["store_total"], "kcal", "agg.store_total",
                                 year=rec["t"], basis="snapshot"),
            "stock_total": _fact(agg["stock_total"], "kcal", "agg.stock_total",
                                 year=rec["t"], basis="snapshot",
                                 note="野外还没被采走的存量，不是群体的存粮"),
        },
    }


def _final_chapter(rec) -> Dict[str, Any]:
    agg, cum = rec["agg"], rec["cum"]
    facts = {
        "pop": _year_fact(agg["pop"], "人", "agg.pop", rec["t"], "第 %d 年末的全局人口" % rec["t"]),
        "bands": _year_fact(agg["bands"], "个群体", "agg.bands", rec["t"],
                            "第 %d 年末还在的群体数" % rec["t"]),
        "store_total": _year_fact(agg["store_total"], "kcal", "agg.store_total", rec["t"],
                                  "第 %d 年末全部群体的存粮合计" % rec["t"]),
        "births_cum": _fact(cum.get("births_cum"), "人", "cum.births_cum",
                            basis="cumulative", note="0..%d 年累计" % rec["t"]),
        "deaths_cum": _fact(cum.get("deaths_demo_cum"), "人", "cum.deaths_demo_cum",
                            basis="cumulative", note="0..%d 年累计，不含迁移死亡" % rec["t"]),
        "migration_deaths_cum": _fact(cum.get("mig_deaths_cum"), "人", "cum.mig_deaths_cum",
                                      basis="cumulative", note="0..%d 年累计" % rec["t"]),
        "aid_kcal_cum": _fact(cum.get("aid_kcal"), "kcal", "cum.aid_kcal",
                              basis="cumulative", note="0..%d 年累计" % rec["t"]),
    }
    if "farm" in rec:
        facts["field_total_m"] = _year_fact(
            rec["farm"]["field_total_m"], "field_m（1000 = 1 个耕作规模单位）",
            "farm.field_total_m", rec["t"], "第 %d 年末全图耕地规模" % rec["t"])
        facts["harvested_kcal_cum"] = _fact(
            rec["farm"]["cum"].get("harvested_kcal"), "kcal", "farm.cum.harvested_kcal",
            basis="cumulative", note="0..%d 年累计实际采收" % rec["t"])
    return {
        "chapter_id": KIND_FINAL, "kind": KIND_FINAL, "year": rec["t"],
        "title": _TITLE[KIND_FINAL], "event_id": None, "actor_ids": [],
        "cell": None, "from": None, "to": None, "basis_event_ids": [], "facts": facts,
    }


def _actors(e) -> List[str]:
    """出场主体：只来自事件本身。援助固定 [给的人, 收的人]。"""
    if e.get("type") in ("field_built", "farm_harvest"):
        src = e.get("participants") or e.get("bands") or []
        return [str(x) for x in src]
    if e.get("type") == "aid":
        return [str(e.get("donor")), str(e.get("receiver"))]
    if e.get("type") == "migrate":
        return [str(e.get("band"))]
    return []


def _event_facts(kind, e, rec) -> Dict[str, Any]:
    t = rec["t"]
    f: Dict[str, Any] = {}
    if kind == "clearing":
        f["built_m"] = _fact(e.get("amount_m"), "field_m（1000 = 1 个耕作规模单位）",
                             "events[].amount_m")
        f["field_before_m"] = _fact(e.get("field_before_m"), "field_m",
                                    "events[].field_before_m")
        f["field_after_m"] = _fact(e.get("field_after_m"), "field_m",
                                   "events[].field_after_m")
        f["labour_m"] = _fact(e.get("labour_m"), "劳动刻度（人数 × 1000）",
                              "events[].labour_m")
        f["harvested_kcal_here_this_year"] = _fact(
            0, "kcal", "模型规则：新开垦的地当年没有产出",
            note="新开的地要到以后的年份才参与产出结算，不是这一格今年颗粒无收")
    elif kind == "harvest":
        f["harvested_kcal"] = _fact(e.get("kcal"), "kcal", "events[].kcal")
        f["person_years"] = _fact(e.get("person_years"), "人年口粮",
                                  "events[].person_years",
                                  note="按模型口粮折算的展示值，不是人数")
        f["potential_kcal"] = _fact(e.get("potential_kcal"), "kcal",
                                    "events[].potential_kcal")
        f["uncollected_kcal"] = _fact(e.get("uncollected_kcal"), "kcal",
                                      "events[].uncollected_kcal",
                                      note="采收限额之外的部分，就地作废，不转给别人也不留到明年")
        f["worked_m"] = _fact(e.get("worked_m"), "field_m", "events[].worked_m")
        f["weather_m"] = _fact(e.get("weather_m"), "‰（1000 = 不增不减）",
                               "events[].weather_m", note="这一格这一年的产量乘数")
        if e.get("per_band_kcal"):
            f["per_band_kcal"] = _fact({str(k): v for k, v in e["per_band_kcal"].items()},
                                       "kcal", "events[].per_band_kcal",
                                       note="多个群体参与时各自实际收到多少")
    elif kind == "migrate":
        f["migration_deaths_this_year"] = _year_fact(
            rec["year"].get("mig_deaths_cum"), "人", "year.mig_deaths_cum", t,
            "全年全局分项：拆不到具体群体，事件里的 unrecorded 已写明")
        f["migrations_this_year"] = _year_fact(
            rec["year"].get("mig_total"), "次", "year.mig_total", t, "全年全部群体的迁移次数")
    elif kind in ("aid", "repay"):
        f["kcal"] = _fact(e.get("kcal"), "kcal", "events[].kcal")
        f["person_years"] = _fact(e.get("person_years"), "人年口粮",
                                  "events[].person_years",
                                  note="按模型口粮折算的展示值，不是人数")
        f["phase"] = _fact(e.get("phase"), "阶段名", "events[].phase")
        basis = e.get("basis") or {}
        if kind == "repay" and basis:
            f["remembered_kcal"] = _fact(basis.get("remembered_kcal"), "kcal",
                                         "events[].basis.remembered_kcal",
                                         note="供给方记忆里对方以前给过自己的量")
            if basis.get("remembered_last_year_display") is not None:
                f["remembered_last_year"] = _fact(
                    basis["remembered_last_year_display"], "年",
                    "events[].basis.remembered_last_year_display")
    # 统一附上"这一年年末"的口径读数：**不是**这件事造成的变化。
    f["pop_year_end"] = _year_fact(rec["agg"]["pop"], "人", "agg.pop", t,
                                   "第 %d 年末的全局人口，不是这件事直接造成的变化" % t)
    f["store_total_year_end"] = _year_fact(
        rec["agg"]["store_total"], "kcal", "agg.store_total", t,
        "第 %d 年末全部群体的存粮合计，不是这件事直接造成的变化" % t)
    return f


def _event_chapter(kind, t, e, rec, seen_event_ids) -> Dict[str, Any]:
    basis_ids: List[str] = []
    if kind == "repay":
        prior = ((e.get("basis") or {}).get("prior_events")) or []
        for pid in prior:
            pid = str(pid)
            # 依据只认**本次运行里真的存在、而且早于这次事件**的那些 id。
            yr = seen_event_ids.get(pid)
            if yr is not None and yr < t:
                basis_ids.append(pid)
    return {
        "chapter_id": kind, "kind": kind, "year": t, "title": _TITLE[kind],
        "event_id": e.get("id"), "actor_ids": _actors(e),
        "cell": e.get("cell"), "from": e.get("from"), "to": e.get("to"),
        "facts": _event_facts(kind, e, rec), "basis_event_ids": basis_ids,
    }


# --------------------------------------------------------------------------- 缺项
def _capabilities(run) -> Tuple[Optional[Dict[str, Any]], Dict[str, int]]:
    engine = (run.get("engine") or "") if run else ""
    spec = config.ENGINES.get(engine)
    params = {k: (run.get(k) or 0) for k in ("farm_m", "aid_m", "recip_m")} if run else {}
    return spec, params


def _missing(first, run, complete: bool, windowed: bool) -> List[Dict[str, str]]:
    """缺项理由。`windowed` 表示这次只看了已记录历史的**一段前缀**（through < 水位）——
    那时候"没有"只能说"这段水位里没有"，不能说"整段历史里没发生过"。"""
    spec, params = _capabilities(run)
    out = []
    for kind in EVENT_KINDS:
        if kind in first:
            continue
        param = _PARAM_OF.get("recip" if kind == "repay" else kind)
        if spec is None:
            reason = REASON_UNKNOWN_ENGINE
        elif param is not None and param not in spec["params"]:
            reason = REASON_NO_MECHANISM
        elif param is not None and params.get(param, 0) == 0:
            reason = REASON_PARAM_ZERO
        elif windowed:
            reason = REASON_OUTSIDE
        elif not complete:
            reason = REASON_INCOMPLETE
        else:
            reason = REASON_NOT_OBSERVED
        out.append({"kind": kind, "reason": reason})
    return out


# --------------------------------------------------------------------------- 组装
def build(run_id: str, run: Optional[Dict[str, Any]], through: int,
          watermark: Optional[int] = None) -> Dict[str, Any]:
    """按已确定的水位组一份计划。**纯读**：不落盘、不起模拟、不改任何记录。"""
    if through < 0:
        raise PlanError("no_history", "这次运行还没有写完整的第 0 年，没有可看的历史")
    ident, first, origin_rec, final_rec, _idx, seen = _scan(run_id, through)
    if origin_rec is None:
        raise PlanError("no_history", "读不到第 0 年的记录，无法组装观看计划")

    chapters = [_origin_chapter(origin_rec)]
    for kind, (t, i, e) in first.items():
        chapters.append(_event_chapter(kind, t, e, _idx[t], seen))
    # 开局永远在前、末年概览永远在后；同年按记录里的原顺序。
    order = {KIND_ORIGIN: (-1, -1)}
    for kind, (t, i, _e) in first.items():
        order[kind] = (t, i)
    chapters[1:] = sorted(chapters[1:], key=lambda c: order[c["kind"]])
    if through > 0:
        chapters.append(_final_chapter(final_rec))

    status = (run or {}).get("status")
    complete = status in ("done", "canceled", "cancelled") or status is None
    return {
        "schema": SCHEMA,
        "run_id": run_id,
        "root_run_id": str((run or {}).get("root_run_id") or run_id),
        "source": {
            "engine_sha256": (run or {}).get("engine_sha256") or None,
            "recorded_through": through,
            "identity_complete_through": through,
            "scope": "recorded_history",
        },
        "identities": _sorted_identities(ident),
        "chapters": chapters,
        "missing_kinds": _missing(first, run, complete,
                                  windowed=(watermark is not None and through < watermark)),
    }


def get(run_id: str, run: Optional[Dict[str, Any]],
        through: Optional[int] = None) -> Dict[str, Any]:
    """带上限的只读缓存。键里有记录水位与源文件标识 ——
    记录长出新的一年，键就变了；文件没动过就直接复用，不为每次轮询全量重扫。"""
    mark = _watermark(run_id)
    if through is None:
        through = mark
    elif through > mark:
        raise PlanError("through_out_of_range",
                        "through=%s 超过已记录的 %s 年" % (through, mark))
    elif through < 0:
        raise PlanError("through_out_of_range", "through 不能是负数")
    key = (run_id, through, _file_key(run_id), SCHEMA, config.API_VERSION)
    hit = _CACHE.get(key)
    if hit is not None:
        _CACHE.move_to_end(key)
        return hit
    plan = build(run_id, run, through, watermark=mark)
    _CACHE[key] = plan
    _CACHE.move_to_end(key)
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return plan
