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
        "engine_params": cfg["params"],
        "engine_path": str(cfg["path"].relative_to(config.REPO_ROOT)),
        "engine_sha256": sha,
        "baseline_commit": cfg["baseline_commit"],
        "params_fingerprint": (v3.params_fingerprint(0, 0, 0) if "share_m" in cfg["params"]
                               else v3.params_fingerprint(0, 0)),
        "constants": {
            "NEED_PC": v3.NEED_PC, "MILLE": v3.MILLE, "SPLIT_SIZE": v3.SPLIT_SIZE,
            "SPOIL_M": v3.SPOIL_M, "MOVE_LOSS_M": v3.MOVE_LOSS_M,
            "MIG_E_M": v3.MIG_E_M, "MIG_GAIN_M": v3.MIG_GAIN_M,
            "SHOCK_P_M": v3.SHOCK_P_M, "K_HALF": v3.K_HALF,
            "SIGMA_M_MAX": v3.SIGMA_M_MAX, "MOVE_MORT_M_MAX": v3.MOVE_MORT_M_MAX,
            **({"SHARE_M_MAX": v3.SHARE_M_MAX} if hasattr(v3, "SHARE_M_MAX") else {}),
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
               engine: str = None, share_m: int = 0):
    """建世界。参数校验由引擎自己做（严格整数 + 范围），这里不重复实现一份。"""
    v3, _ = load_engine(engine)
    poison = config.ARMS[arm]["poison"]
    if "share_m" in config.ENGINES[engine or config.DEFAULT_ENGINE]["params"]:
        return v3.make_world(seed, poison, sigma_m, move_mort_m, share_m)
    return v3.make_world(seed, poison, sigma_m, move_mort_m)


def step(st, engine: str = None):
    v3, _ = load_engine(engine)
    v3.step(st)


# EXP-04 才有的信息账字段。引擎没有就不出现在记录里（前端要容忍缺席）。
SHARE_FIELDS = ("share_groups", "share_participants", "share_received",
                "share_adopted", "share_rejected", "share_decision_changed")

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
        self._prev_cum: Optional[Dict[str, int]] = None
        self._prev_cells: Dict[str, int] = {}
        self._log_len = 0
        self._share_len = 0
        self._names: Dict[str, str] = {}
        self._birth_year: Dict[str, int] = {}

    # -- 只读抽取 ------------------------------------------------------
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

        bands: List[Dict[str, Any]] = []
        cells_now: Dict[str, int] = {}
        for bid, b in sorted(st["bands"].items()):
            sid = str(bid)                      # 64 位 id 一律以字符串下发，避免 JS 精度丢失
            cells_now[sid] = b["cell"]
            self._birth_year.setdefault(sid, t)
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
            })

        fields = tuple(CUM_FIELDS) + tuple(f for f in SHARE_FIELDS if f in st)
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
        events = self._events(st, t, cells_now)
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

        for sid, cell in cells_now.items():          # 来源二：状态差分（可核实）
            old = self._prev_cells.get(sid)
            if old is not None and old != cell:
                out.append({"type": "migrate", "source": "状态差分（cell 字段前后不同）",
                            "band": sid, "from": old, "to": cell,
                            "text": f"{self._names.get(sid, sid)} 由 {old} 号格迁至 {cell} 号格",
                            "unrecorded": "本次迁移的死亡人数未记录：当年账本只记全局分项，"
                                          "群体层的出生/原死亡/迁移死亡无法从年末快照拆开"})
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
