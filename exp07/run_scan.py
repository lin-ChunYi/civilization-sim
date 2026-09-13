#!/usr/bin/env python3
"""EXP-07 观察扫描：原始耕作与弃耕。

**只报告现象，不判定好坏，也不为了让读数好看而调参。**

固定 42 组：7 种子 × SIGMA_M{0,400} × FARM_M{0,250,500}，
每组 300 年，MOVE_MORT_M=50 / SHARE_M=1000 / AID_M=1000 / RECIP_M=1000，记忆臂。

    python3 exp07/run_scan.py [--output-dir 目录] [--years 300]

"连续居住"只按**同一个群体 ID 连续待在同一格的步数**观察，并标出三种截断：
开局就在（左截断）、中途分裂出来（左截断）、跑到末年还没离开（右截断）。
**它不等于"定居文明"**——这里没有任何村落、产权或制度，只有"这群人没动"。
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("v7_scan", str(REPO / "exp07" / "verify7.py"))
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]
SIGMAS = [0, 400]
FARMS = [0, 250, 500]
MORT, SHARE, AID, RECIP = 50, 1000, 1000, 1000
N = v.NEED_PC


def stay_runs(history, years):
    """同一群体 ID 连续位于同格的步数。返回 (全部段, 未截断段)。

    history: {bid: [(tick, cell), ...]}，每年一条。
    截断标记：`left` = 这一段从它第一次被看到就开始（开局或刚分裂出来）；
             `right` = 跑到末年还没离开。两端都不算"自然结束的一段居住"。
    """
    segs = []
    for bid, seq in history.items():
        if not seq:
            continue
        start_t, cur = seq[0]
        first_seen = seq[0][0]
        for tick, cell in seq[1:]:
            if cell != cur:
                segs.append({"bid": str(bid), "cell": cur, "from": start_t, "to": tick - 1,
                             "steps": tick - start_t,
                             "left": start_t == first_seen, "right": False})
                start_t, cur = tick, cell
        segs.append({"bid": str(bid), "cell": cur, "from": start_t, "to": seq[-1][0],
                     "steps": seq[-1][0] - start_t + 1,
                     "left": start_t == first_seen, "right": seq[-1][0] >= years})
    clean = [s for s in segs if not s["left"] and not s["right"]]
    return segs, clean


def stay_extra(history, segs):
    """补两个统计，免得"未截断段"这一个数字把话说反。

    一个群体从分裂出来到末年都没挪过窝，它的那一段**两端都被截断**，于是不进 clean —— 
    只看 clean 会读成"没人久居"，实际恰恰相反。所以这里另外报：
      * `never_moved`：整段生命里一次都没换过格的群体数（以及占比）；
      * `final_steps_median`：每个群体**最后那一段**（跑到末年仍在原地）的步数中位数。
    """
    never = [bid for bid, seq in history.items()
             if seq and len({c for _t, c in seq}) == 1]
    finals = [s["steps"] for s in segs if s["right"]]
    return {
        "bands_seen": len(history),
        "never_moved": len(never),
        "never_moved_pct_m": (len(never) * 1000 // len(history)) if history else 0,
        "final_steps_median": int(statistics.median(finals)) if finals else 0,
        "final_steps_max": max(finals, default=0),
    }


def one(seed, sigma, farm, years):
    st = v.make_world(seed, "", sigma, MORT, SHARE, AID, RECIP, farm)
    history = {}
    first_built = None
    first_harvest = None
    for _ in range(years):
        v.step(st)
        t = st["tick"]
        for bid, b in st["bands"].items():
            history.setdefault(bid, []).append((t, b["cell"]))
        for e in st["farm_log"]:
            if e["tick"] != t - 1:
                continue
            if first_built is None and e["type"] == "field_built":
                first_built = {"tick": e["tick"], "cell": e["cell"],
                               "bands": [str(x) for x in e["bands"]],
                               "labour_m": e["labour_m"], "amount_m": e["amount_m"],
                               "field_before_m": e["field_before_m"],
                               "field_after_m": e["field_after_m"]}
            if first_harvest is None and e["type"] == "farm_harvest":
                first_harvest = {"tick": e["tick"], "cell": e["cell"],
                                 "bands": [str(x) for x in e["bands"]],
                                 "worked_m": e["worked_m"], "weather_m": e["weather_m"],
                                 "potential_kcal": e["potential_kcal"], "kcal": e["kcal"],
                                 "uncollected_kcal": e["uncollected_kcal"],
                                 "per_band_kcal": {str(k): x for k, x in
                                                   e["per_band_kcal"].items()}}
    segs, clean = stay_runs(history, years)
    extra = stay_extra(history, segs)
    errs = {"conservation": v.conservation_error(st), "labour": v.farm_labour_error(st),
            "field": v.field_ledger_error(st), "yield": v.farm_yield_error(st),
            "inflow_source": v.inflow_source_error(st),
            "population": v.population_identity_error(st),
            "share": v.share_ledger_error(st), "aid": v.aid_ledger_error(st),
            "aid_memory": v.aid_memory_error(st)}
    return {
        "seed": seed, "sigma_m": sigma, "farm_m": farm, "years": years,
        "pop": sum(b["size"] for b in st["bands"].values()), "bands": len(st["bands"]),
        "personyears": st["personyear_cum"], "need_kcal": st["need_cum"],
        "deficit_kcal": st["deficit_cum"],
        "deficit_rate_m": (st["deficit_cum"] * 1000 // st["need_cum"]) if st["need_cum"] else 0,
        "births": st["births_cum"], "deaths_demo": st["deaths_demo_cum"],
        "mig": st["mig_total"], "mig_deaths": st["mig_deaths_cum"],
        "aid_transfers": st["aid_transfers"], "aid_kcal": st["aid_kcal"],
        "repay_transfers": st["repay_transfers"], "repay_kcal": st["repay_kcal"],
        "farm_effort_m": st["farm_effort_cum"], "farm_effort_used_m": st["farm_effort_used_cum"],
        "farm_potential_kcal": st["farm_potential_cum"],
        "farm_harvest_kcal": st["farm_harvest_cum"],
        "farm_uncollected_kcal": st["farm_uncollected_cum"],
        "farm_harvest_py": st["farm_harvest_cum"] // N,
        "field_built_m": st["field_built_cum"], "field_decay_m": st["field_decay_cum"],
        "field_end_m": sum(st["field_m"].values()),
        "field_cells": sum(1 for x in st["field_m"].values() if x > 0),
        "clim_credited": st["clim_credited"],
        "inflow": st["inflow"],
        "stay_segments": len(segs), "stay_untruncated": len(clean),
        "stay_max_steps": max([s["steps"] for s in clean], default=0),
        "stay_median_steps": int(statistics.median([s["steps"] for s in clean]))
        if clean else 0,
        "bands_seen": extra["bands_seen"], "never_moved": extra["never_moved"],
        "never_moved_pct_m": extra["never_moved_pct_m"],
        "final_steps_median": extra["final_steps_median"],
        "final_steps_max": extra["final_steps_max"],
        "identity_errors": errs,
        "first_field_built": first_built, "first_farm_harvest": first_harvest,
        "state_hash": v.state_hash(st),
        "full_digest": v.full_digest(st),
    }


COLS = ["seed", "sigma_m", "farm_m", "pop", "bands", "personyears", "deficit_rate_m",
        "births", "deaths_demo", "mig", "mig_deaths", "aid_transfers", "aid_kcal",
        "repay_transfers", "repay_kcal", "farm_effort_m", "farm_effort_used_m",
        "farm_potential_kcal", "farm_harvest_kcal", "farm_uncollected_kcal",
        "farm_harvest_py", "field_built_m", "field_decay_m", "field_end_m", "field_cells",
        "stay_segments", "stay_untruncated", "stay_max_steps", "stay_median_steps",
        "bands_seen", "never_moved", "never_moved_pct_m", "final_steps_median",
        "final_steps_max"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default=None)
    ap.add_argument("--years", type=int, default=300)
    args = ap.parse_args()

    rows = []
    t0 = time.time()
    for sg in SIGMAS:
        for fm in FARMS:
            for sd in SEEDS:
                rows.append(one(sd, sg, fm, args.years))
                r = rows[-1]
                print("seed=%-6d SIGMA=%-4d FARM=%-4d 人口 %-4d 耕地 %-6d 采收 %-6d 人年 "
                      "未采收 %-7d 人年 开垦 %-7d 退化 %-6d"
                      % (r["seed"], r["sigma_m"], r["farm_m"], r["pop"], r["field_end_m"],
                         r["farm_harvest_py"], r["farm_uncollected_kcal"] // N,
                         r["field_built_m"], r["field_decay_m"]), flush=True)

    bad = [r for r in rows if any(r["identity_errors"].values())]
    print("\n九本账全部恒等的组数：%d / %d" % (len(rows) - len(bad), len(rows)))
    if bad:
        print("对不上的组：", [(r["seed"], r["sigma_m"], r["farm_m"]) for r in bad])

    print("\n=== 按 FARM_M 汇总（每档 14 组：7 种子 × 2 个 SIGMA）===")
    print("%-6s %-8s %-8s %-9s %-9s %-8s %-8s %-8s %-9s %-8s" %
          ("FARM", "末人口", "人年", "缺粮‰", "采收人年", "未采收", "耕地", "居住中位",
           "没挪过窝‰", "末段中位"))
    summary = {}
    for fm in FARMS:
        grp = [r for r in rows if r["farm_m"] == fm]
        summary[fm] = {
            "pop_median": int(statistics.median([r["pop"] for r in grp])),
            "py_median": int(statistics.median([r["personyears"] for r in grp])),
            "deficit_rate_m_median": int(statistics.median([r["deficit_rate_m"] for r in grp])),
            "harvest_py_median": int(statistics.median([r["farm_harvest_py"] for r in grp])),
            "uncollected_py_median": int(statistics.median(
                [r["farm_uncollected_kcal"] // N for r in grp])),
            "field_end_median": int(statistics.median([r["field_end_m"] for r in grp])),
            "stay_median": int(statistics.median([r["stay_median_steps"] for r in grp])),
            "stay_max": max(r["stay_max_steps"] for r in grp),
            "never_moved_pct_m_median": int(statistics.median(
                [r["never_moved_pct_m"] for r in grp])),
            "final_steps_median": int(statistics.median(
                [r["final_steps_median"] for r in grp])),
        }
        s = summary[fm]
        print("%-6d %-8d %-8d %-9d %-9d %-8d %-8d %-8d %-9d %-8d" %
              (fm, s["pop_median"], s["py_median"], s["deficit_rate_m_median"],
               s["harvest_py_median"], s["uncollected_py_median"], s["field_end_median"],
               s["stay_median"], s["never_moved_pct_m_median"], s["final_steps_median"]))
    print("\n注：'居住中位' 只数**两端都没被截断**的那些段 —— 一个群体从分裂出来到末年都没挪窝，"
          "\n    它两端都被截断，不进这个统计。所以另外报了'没挪过窝‰'与'末段中位'，"
          "\n    免得只看一个数把话读反。三个数都只是观察，"
          "\n    **不是定居文明**——模型里没有村落、产权或制度。")
    print("    耕地规模单位 = 1000 个 field 刻度；不是亩、公顷，也不是人数。")
    print("    FIELD_CAP_M / FIELD_DECAY_M / FARM_YIELD_M 是本项目自拟的实验假设（D 级），"
          "\n    **不冒充中国史校准**。")

    if args.output_dir:
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "scan.json").write_text(json.dumps({
            "experiment": "EXP-07", "generated_at": time.time(),
            "elapsed_sec": round(time.time() - t0, 1),
            "config": {"seeds": SEEDS, "sigmas": SIGMAS, "farms": FARMS, "years": args.years,
                       "move_mort_m": MORT, "share_m": SHARE, "aid_m": AID,
                       "recip_m": RECIP, "arm": "memory"},
            "constants": {"FIELD_CAP_M": v.FIELD_CAP_M, "FIELD_DECAY_M": v.FIELD_DECAY_M,
                          "FARM_YIELD_M": v.FARM_YIELD_M, "NEED_PC": N},
            "params_fingerprint": v.params_fingerprint(400, MORT, SHARE, AID, RECIP, 250),
            "rows": rows, "summary_by_farm_m": summary,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        with (out / "scan.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        firsts = [{"seed": r["seed"], "sigma_m": r["sigma_m"], "farm_m": r["farm_m"],
                   "first_field_built": r["first_field_built"],
                   "first_farm_harvest": r["first_farm_harvest"]} for r in rows]
        (out / "first-events.json").write_text(
            json.dumps(firsts, ensure_ascii=False, indent=1), encoding="utf-8")
        print("\n原始数据已写入 %s（scan.json / scan.csv / first-events.json）" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
