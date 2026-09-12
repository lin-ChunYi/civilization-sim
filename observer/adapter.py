"""观察适配层 —— 只读地把冻结的 EXP-03 引擎变成可展示的年度记录。

纪律（对应验收第 1 条）：
  1. 只调用引擎的 make_world / step 与纯读函数；
  2. 只读取与复制状态，**不往模型对象里写任何观察字段**；
  3. **一次都不调用引擎的 rng**，不消耗模型随机数；
  4. 观察用的显示名、事件来源标注放在本层自己的结构里，不进模型实体。

引擎以 importlib 按路径只读加载（和 EXP-02/03 判定退化恒等时的做法一致），
exp03/ 目录本身不被修改。
"""
from __future__ import annotations

import hashlib
import importlib.util
from functools import lru_cache
from typing import Any, Dict, List, Optional

from . import config

def _param_spec(name: str, engine_mod) -> Dict[str, Any]:
    """参数能力：展示信息来自 config.PARAM_SPECS，取值范围以**引擎常量**为准。"""
    spec = dict(config.PARAM_SPECS.get(name, {"label": name, "unit": "", "min": 0,
                                              "max": 0, "default": 0, "note": ""}))
    lo = getattr(engine_mod, f"{name.upper()}_MIN", None)
    hi = getattr(engine_mod, f"{name.upper()}_MAX", None)
    if lo is not None: spec["min"] = lo
    if hi is not None: spec["max"] = hi
    spec["name"] = name
    return spec


@lru_cache(maxsize=4)
def load_engine(name: str = None):
    """只读加载指定引擎，返回 (module, sha256)。"""
    name = name or config.DEFAULT_ENGINE
    if name not in config.ENGINES:
        raise ValueError(f"未登记的引擎：{name}")
    path = config.ENGINES[name]["path"]
    src = path.read_bytes()
    sha = hashlib.sha256(src).hexdigest()
    spec = importlib.util.spec_from_file_location(f"{name}_engine_readonly", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, sha


def engine_info(name: str = None) -> Dict[str, Any]:
    name = name or config.DEFAULT_ENGINE
    cfg = config.ENGINES[name]
    v3, sha = load_engine(name)
    return {
        "engine": name,
        "engine_label": cfg["label"],
        "engine_params": cfg["params"],          # 参数名（obs-1.2 起，保持不变）
        # obs-1.5：参数能力表 —— 范围 / 默认值 / 单位 / 含义，前端按能力展示
        "params": [_param_spec(name, v3) for name in ("seed", "years") + tuple(cfg["params"])],
        "engine_path": str(cfg["path"].relative_to(config.REPO_ROOT)),
        "engine_sha256": sha,
        "baseline_commit": cfg["baseline_commit"],
        "params_fingerprint": v3.params_fingerprint(*([0] * len(cfg["params"]))),
        "constants": {
            "NEED_PC": v3.NEED_PC, "MILLE": v3.MILLE, "SPLIT_SIZE": v3.SPLIT_SIZE,
            "SPOIL_M": v3.SPOIL_M, "MOVE_LOSS_M": v3.MOVE_LOSS_M,
            "MIG_E_M": v3.MIG_E_M, "MIG_GAIN_M": v3.MIG_GAIN_M,
            "SHOCK_P_M": v3.SHOCK_P_M, "K_HALF": v3.K_HALF,
            "SIGMA_M_MAX": v3.SIGMA_M_MAX, "MOVE_MORT_M_MAX": v3.MOVE_MORT_M_MAX,
            **({"SHARE_M_MAX": v3.SHARE_M_MAX} if hasattr(v3, "SHARE_M_MAX") else {}),
            **({"AID_M_MAX": v3.AID_M_MAX} if hasattr(v3, "AID_M_MAX") else {}),
            **({"RECIP_M_MAX": v3.RECIP_M_MAX} if hasattr(v3, "RECIP_M_MAX") else {}),
        },
    }


def engines_info() -> Dict[str, Any]:
    """全部可用引擎。前端据此决定给哪些参数控件。"""
    return {name: engine_info(name) for name in config.ENGINES}


def map_geometry(engine: str = None) -> Dict[str, Any]:
    """静态地图：8×8、第 3/4 列不可通行、pointy-top 六邻接。与引擎同源，不另写一份。"""
    v3, _ = load_engine(engine)
    cells = []
    for i in v3.cells():
        r, c = divmod(i, v3.W)
        cells.append({
            "i": i, "row": r, "col": c,
            "passable": bool(v3.passable(i)),
            "region": v3.region(i),
            "neighbors": v3.neighbors(i) if v3.passable(i) else [],
        })
    return {"w": v3.W, "h": v3.H, "barrier_cols": sorted(v3.BARRIER_COLS), "cells": cells}


# ---------------------------------------------------------------- 运行期

def make_world(seed: int, sigma_m: int, move_mort_m: int, arm: str,
               engine: str = None, share_m: int = 0, aid_m: int = 0,
               recip_m: int = 0):
    """建世界。参数校验由引擎自己做（严格整数 + 范围），这里不重复实现一份。"""
    v3, _ = load_engine(engine)
    poison = config.ARMS[arm]["poison"]
    params = config.ENGINES[engine or config.DEFAULT_ENGINE]["params"]
    extra = []
    if "share_m" in params: extra.append(share_m)
    if "aid_m" in params: extra.append(aid_m)
    if "recip_m" in params: extra.append(recip_m)
    return v3.make_world(seed, poison, sigma_m, move_mort_m, *extra)


def step(st, engine: str = None):
    v3, _ = load_engine(engine)
    v3.step(st)


# EXP-04 才有的信息账字段。引擎没有就不出现在记录里（前端要容忍缺席）。
SHARE_FIELDS = ("share_groups", "share_participants", "share_received",
                "share_adopted", "share_rejected", "share_decision_changed")

# EXP-05 才有的援助账字段。注意 aid_events（一次多人援助活动）与 aid_transfers（一笔转移）
# 是两个不同的计数，不要合并。
AID_FIELDS = ("aid_events", "aid_transfers", "aid_kcal", "aid_donors",
              "aid_receivers", "aid_supply", "aid_demand")

# EXP-06 才有的优先回助与记忆账字段。
# 注意 repay（供给方记得对方帮过自己）与 recip_changed（优先规则真的改变了分配）
# 是两回事：RECIP_M=0 时 repay 也可能发生，那是碰巧。
RECIP_FIELDS = ("recip_budget", "recip_kcal", "recip_transfers", "recip_changed",
                "repay_kcal", "repay_transfers", "amem_dropped_kcal",
                "amem_entries_dropped")

CUM_FIELDS = (
    "births_cum", "deaths_demo_cum", "mig_deaths_cum", "mig_total", "mig_regret",
    "need_cum", "deficit_cum", "personyear_cum", "stale_sum",
    "inflow", "out_eat", "out_spoil", "out_move", "out_lost",
    "prop_total", "prop_conflict",
    "clim_nominal", "clim_planned", "clim_credited", "clim_capped",
)


def band_display_name(bid: int) -> str:
    """观察层的显示名，由实体 id 派生，稳定且不写回模型。"""
    return "群体-" + format(bid & 0xFFFFFFFFFFFFFFFF, "016x")[:6].upper()


class Recorder:
    """把一次运行变成逐年记录。持有自己的上一年缓存，不碰模型对象。"""

    def __init__(self, engine: str = None):
        self.engine = engine or config.DEFAULT_ENGINE
        # (供给方, 接收方) -> 这对之间**以前**每一笔援助的事件 id，用来给回助事件挂依据
        self._aid_by_pair: Dict[Any, List[str]] = {}
        self._prev_cum: Optional[Dict[str, int]] = None
        self._prev_cells: Dict[str, int] = {}
        self._log_len = 0
        self._share_len = 0
        self._aid_len = 0
        self._names: Dict[str, str] = {}
        self._birth_year: Dict[str, int] = {}

    # -- 只读抽取 ------------------------------------------------------
    def _display_year(self, donor, receiver) -> Dict[str, Any]:
        """把"谁帮过我"换算成**可展示**的年份：取这一对之间最后一笔真实援助事件。
        找不到（例如构造场景里预置的历史、或本次运行之前发生的）就如实给 null。"""
        ids = self._aid_by_pair.get((int(donor), int(receiver)))
        if not ids:
            return {"last_year_display": None, "last_event_id": None,
                    "display_source": "未记录：本次运行的已保存记录里没有这一对的援助事件"}
        last = ids[-1]
        return {"last_year_display": int(last.split('-')[0][1:]), "last_event_id": last,
                "display_source": "本次运行的援助事件 " + last}

    def _name(self, sid: str, bid: int) -> str:
        n = self._names.get(sid)
        if n is None:
            n = band_display_name(bid)
            if n in self._names.values():          # 极罕见的显示名撞车，补足位数
                n = "群体-" + format(bid, "016x")[:10].upper()
            self._names[sid] = n
        return n

    def year_record(self, st) -> Dict[str, Any]:
        v3, _ = load_engine(self.engine)
        t = st["tick"]
        cell_ids = sorted(st["stock"])
        stock = [st["stock"][i] for i in cell_ids]

        # 先做一遍轻量预处理：登记显示名与所在格，然后**先收事件**。
        # 顺序很要紧：aid_memory 的展示口径字段要引用"本年这笔援助事件"的 id 与 year，
        # 事件收在后面的话，当年更新的那条记忆就只能拿到 null。
        cells_now: Dict[str, int] = {}
        for bid, b in sorted(st["bands"].items()):
            sid = str(bid)                      # 64 位 id 一律以字符串下发，避免 JS 精度丢失
            cells_now[sid] = b["cell"]
            self._birth_year.setdefault(sid, t)
            self._name(sid, bid)
        events = self._events(st, t, cells_now)

        bands: List[Dict[str, Any]] = []
        for bid, b in sorted(st["bands"].items()):
            sid = str(bid)
            bands.append({
                "id": sid,
                "name": self._name(sid, bid),
                "cell": b["cell"],
                "size": b["size"],
                "store": b["store"],
                "macc": b["macc"],
                "bacc": b["bacc"],
                "dacc": b["dacc"],
                "mem": {str(c): [b["mem"][c], b["memt"].get(c)] for c in sorted(b["mem"])},
                # EXP-06：援助记忆（谁实际援助过我）。只由实际转移累加，来源见 source 字段。
                # last_year 是**引擎内部 tick**，保持原语义不动；
                # last_year_display / last_event_id 是**展示口径**，由本次运行里那笔
                # 真实援助事件的 year 与稳定事件 id 推出。没有对应记录就给 null，
                # 绝不在不认识的引擎版本上猜 ±1。
                **({"aid_memory": {
                        str(k): dict({"kcal": b["amem"][k][0],
                                      "last_year": b["amem"][k][1]},
                                     **self._display_year(k, bid))
                        for k in sorted(b["amem"])}}
                   if "amem" in b else {}),
            })

        fields = (tuple(CUM_FIELDS) + tuple(f for f in SHARE_FIELDS if f in st)
                  + tuple(f for f in AID_FIELDS if f in st)
                  + tuple(f for f in RECIP_FIELDS if f in st))
        cum = {k: st[k] for k in fields}
        prev = self._prev_cum or {k: 0 for k in fields}
        year = {k: cum[k] - prev.get(k, 0) for k in fields}

        agg = {
            "pop": sum(b["size"] for b in bands),
            "bands": len(bands),
            "stock_total": sum(stock),
            "store_total": sum(b["store"] for b in bands),
        }
        integrity = {
            "conservation_error": v3.conservation_error(st),
            "population_identity_error": v3.population_identity_error(st),
            "state_hash": v3.state_hash(st),
        }
        if "share_ledger_error" in dir(v3):
            integrity["share_ledger_error"] = v3.share_ledger_error(st)
        if "aid_ledger_error" in dir(v3):
            integrity["aid_ledger_error"] = v3.aid_ledger_error(st)
        if "aid_memory_error" in dir(v3):
            integrity["aid_memory_error"] = v3.aid_memory_error(st)
        rec = {"t": t, "stock": stock, "bands": bands, "cum": cum, "year": year,
               "agg": agg, "integrity": integrity, "events": events}
        if "share_log" in st:                       # EXP-04：信息交换的当年统计
            rec["share"] = {
                "groups": year.get("share_groups", 0),
                "participants": year.get("share_participants", 0),
                "received": year.get("share_received", 0),
                "adopted": year.get("share_adopted", 0),
                "rejected": year.get("share_rejected", 0),
                "decision_changed": year.get("share_decision_changed", 0),
                "cum_adopted": cum.get("share_adopted", 0),
            }
        if "aid_log" in st:                         # EXP-05：食物援助的当年统计
            rec["aid"] = {
                "events": year.get("aid_events", 0),        # 一次多人援助活动
                "transfers": year.get("aid_transfers", 0),  # 逐笔转移
                "kcal": year.get("aid_kcal", 0),
                "donors": year.get("aid_donors", 0),
                "receivers": year.get("aid_receivers", 0),
                "supply": year.get("aid_supply", 0),
                "demand": year.get("aid_demand", 0),
                "cum_kcal": cum.get("aid_kcal", 0),
                "cum_events": cum.get("aid_events", 0),
                "cum_transfers": cum.get("aid_transfers", 0),
            }
        if "recip_m" in st:                         # EXP-06：优先回助的当年统计
            rec["recip"] = {
                "budget": year.get("recip_budget", 0),
                "kcal": year.get("recip_kcal", 0),
                "transfers": year.get("recip_transfers", 0),
                "changed": year.get("recip_changed", 0),      # 优先规则真的改变了分配的次数
                "repay_kcal": year.get("repay_kcal", 0),      # 回助（含碰巧的）
                "repay_transfers": year.get("repay_transfers", 0),
                "cum_kcal": cum.get("recip_kcal", 0),
                "cum_changed": cum.get("recip_changed", 0),
                "cum_repay_transfers": cum.get("repay_transfers", 0),
                "memory_entries": sum(len(b.get("amem", {})) for b in st["bands"].values()),
                "memory_dropped": cum.get("amem_entries_dropped", 0),
                # 同状态分配对照：同一份援助前状态下"开/关优先回助"各算一遍的逐笔结果。
                # **这才是"优先规则确实改变了分配"的依据**，不能只凭双方以前有往来就认定。
                "compare": [{
                    "cell": c["cell"], "changed": c["changed"],
                    "with_recip": [{"donor": str(d), "receiver": str(r),
                                    "kcal": a, "phase": ph}
                                   for d, r, a, ph in c["with_recip"]],
                    "without_recip": [{"donor": str(d), "receiver": str(r),
                                       "kcal": a, "phase": ph}
                                      for d, r, a, ph in c["without_recip"]],
                    # 判据本身：逐对群体的总额。拆成两笔但总额不变 -> changed = false
                    "with_totals": [{"donor": str(d), "receiver": str(r), "kcal": a}
                                    for d, r, a in c.get("with_totals", [])],
                    "without_totals": [{"donor": str(d), "receiver": str(r), "kcal": a}
                                       for d, r, a in c.get("without_totals", [])],
                } for c in st.get("recip_compare", [])],
            }
        self._prev_cum = cum
        self._prev_cells = cells_now
        return rec

    # -- 事件：只有两个来源，都标注出来 --------------------------------
    def _events(self, st, t: int, cells_now: Dict[str, int]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        log = st["log"]
        for entry in log[self._log_len:]:            # 来源一：模型自己的日志
            kind = entry[1]
            if kind == "split":
                parent, child = str(entry[2]), str(entry[3])
                out.append({"type": "split", "source": "模型日志 st['log']",
                            "band": child, "parent": parent,
                            "text": f"{self._names.get(parent, parent)} 分裂出 "
                                    f"{self._names.get(child, child)}"})
            elif kind == "extinct":
                bid = str(entry[2])
                out.append({"type": "extinct", "source": "模型日志 st['log']", "band": bid,
                            "text": f"{self._names.get(bid, bid)} 人口归零，被移除"})
        self._log_len = len(log)

        share_log = st.get("share_log")             # 来源三：模型记录的信息交换（EXP-04）
        if share_log is not None:
            for (tick, cell, donor, recv, key, val, stamp) in share_log[self._share_len:]:
                d, r = str(donor), str(recv)
                out.append({
                    "type": "share", "source": "模型日志 st['share_log']",
                    "band": r, "donor": d, "receiver": r, "cell": cell,
                    "mem_cell": key, "value": val, "memt": stamp,
                    "text": f"{self._names.get(d, d)} 把第 {key} 号格的记忆"
                            f"（{val} kcal，记于第 {stamp} 年）传给了 "
                            f"{self._names.get(r, r)}，地点在第 {cell} 号格",
                })
            self._share_len = len(share_log)

        aid_log = st.get("aid_log")                 # 来源四：模型记录的食物援助（EXP-05）
        if aid_log is not None:
            need_pc = load_engine(self.engine)[0].NEED_PC
            amem_pre = st.get("amem_pre", {})
            for entry in aid_log[self._aid_len:]:
                tick, cell, donor, recv, amt = entry[:5]
                phase = entry[5] if len(entry) > 5 else "normal"
                repay = bool(entry[6]) if len(entry) > 6 else False
                d, r = str(donor), str(recv)
                tag = "回助 · " if repay else ""
                why = ("（优先回助阶段：供给方记得对方帮过自己）" if phase == "recip"
                       else ("（普通阶段，但供给方确实记得对方帮过自己）" if repay else ""))
                ev = {
                    "type": "aid", "source": "模型日志 st['aid_log']",
                    "band": r, "donor": d, "receiver": r, "cell": cell,
                    "kcal": amt, "person_years": amt / need_pc,
                    "phase": phase, "repay": repay,
                    "text": f"{tag}{self._names.get(d, d)} 向 {self._names.get(r, r)} "
                            f"援助了 {amt} kcal（{amt / need_pc:.2f} 人年口粮），"
                            f"地点在第 {cell} 号格{why}",
                    "unrecorded": "动机、路线与因果关系未记录：模型里没有这些量，"
                                  "不要为动画补编。",
                }
                if repay:
                    # 依据：对方**以前**实际援助过我的那几笔（事件 id 可直接跳转），
                    # 以及供给方在援助前记住的累计量与最近年份。
                    mem = amem_pre.get(donor, {}).get(recv)
                    prior = list(self._aid_by_pair.get((recv, donor), []))
                    ev["basis"] = {
                        "why": "供给方的援助记忆里有接收方，且该记忆只由实际转移累加",
                        "remembered_kcal": mem[0] if mem else None,
                        # 原语义保留：这是引擎内部 tick
                        "remembered_last_year": mem[1] if mem else None,
                        # 展示口径：最后一笔作为依据的真实事件的年份与 id（找不到则 null）
                        "remembered_last_year_display": (int(prior[-1].split('-')[0][1:])
                                                         if prior else None),
                        "remembered_last_event_id": prior[-1] if prior else None,
                        "prior_events": prior,
                        "year_note": ("remembered_last_year 是引擎内部 tick；"
                                      "要显示或跳转请用 remembered_last_year_display / "
                                      "remembered_last_event_id，它们来自真实事件记录"),
                        "source": "模型状态 band['amem'] 的援助前快照 + 本次运行的援助日志",
                    }
                out.append(ev)
            self._aid_len = len(aid_log)

        for sid, cell in cells_now.items():          # 来源二：状态差分（可核实）
            old = self._prev_cells.get(sid)
            if old is not None and old != cell:
                out.append({"type": "migrate", "source": "状态差分（cell 字段前后不同）",
                            "band": sid, "from": old, "to": cell,
                            "text": f"{self._names.get(sid, sid)} 由 {old} 号格迁至 {cell} 号格",
                            "unrecorded": "本次迁移的死亡人数未记录：当年账本只记全局分项，"
                                          "群体层的出生/原死亡/迁移死亡无法从年末快照拆开"})

        # 稳定标识：同一次运行里唯一且可复现（年份 + 类型 + 当年序号），供时间轴定位与详情面板用
        for i, e in enumerate(out):
            e["id"] = f"t{t}-{e['type']}-{i}"
            e["year"] = t
        for e in out:                               # 登记援助配对，供后续回助事件挂依据
            if e["type"] == "aid":
                self._aid_by_pair.setdefault(
                    (int(e["donor"]), int(e["receiver"])), []).append(e["id"])
        return out


def run_identity(st, engine: str = None) -> Dict[str, str]:
    v3, _ = load_engine(engine)
    return {"model_run_id": v3.run_id(st), "full_digest": v3.full_digest(st),
            "state_hash": v3.state_hash(st)}


def static_run_meta(st) -> Dict[str, Any]:
    """一次运行里不随年份变化的东西：格容量、年再生、初始禀赋。"""
    cell_ids = sorted(st["stock"])
    return {
        "cell_ids": cell_ids,
        "cap": [st["cap"][i] for i in cell_ids],
        "regen": [st["regen"][i] for i in cell_ids],
        "start_stock": st["start_stock"],
        "start_store": st["start_store"],
        "pop_start": st["pop_start"],
    }
