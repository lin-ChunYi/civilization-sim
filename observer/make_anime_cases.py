"""生成交给前端（Grok/Codex）的四条真实案例，并写出一份可分发的清单。

这四条都是**自然演化**的运行，不是构造出来的演示：同一颗种子 4242、同一组社会参数，
只改引擎与 `FARM_M`。它们已经在 `docs/evidence/anime-cases-20260914/` 里被逐条核过。

    python3 -m observer.make_anime_cases            # 生成数据 + 写清单
    python3 -m observer.make_anime_cases --check    # 只重算清单并与已提交的那份逐字段比

**数据不进版本库**：一条 300 年的 `years.jsonl` 有 8 MB 上下，四条二十多兆
（`observer/preset/preset-anime-*/` 已在 .gitignore 里）。它们是**确定性重算**出来的 ——
同一版引擎、同一组参数，每次生成的 `model_run_id` 与 `full_digest` 都一样，
所以清单里的标识在任何一台机器上都指向同一段历史。生成一次约几秒。

生成完直接起服务就能看到：预置案例在启动时由 `presets.install_presets()` 装进数据目录，
`run_id` 是下面这四个固定值，不是随机 uuid。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import config, presets

# 同一颗种子、同一组社会参数；只有引擎与 FARM_M 不同。
COMMON = dict(seed=4242, years=300, sigma_m=400, move_mort_m=50, arm="memory",
              share_m=1000, aid_m=1000, recip_m=1000)
CASES = [
    dict(run_id="preset-anime-farm250", engine="exp07", farm_m=250,
         label="动漫案例 A · EXP-07 耕作（FARM_M=250）· seed 4242 · 300 年", **COMMON),
    dict(run_id="preset-anime-exp06", engine="exp06",
         label="动漫案例 B · EXP-06 旧引擎（没有农业）· seed 4242 · 300 年", **COMMON),
    dict(run_id="preset-anime-farm0", engine="exp07", farm_m=0,
         label="动漫案例 C · EXP-07 受控对照（FARM_M=0）· seed 4242 · 300 年", **COMMON),
    dict(run_id="preset-anime-farm1000", engine="exp07", farm_m=1000,
         label="动漫案例 D · EXP-07 全员耕作（FARM_M=1000，出现弃耕）· seed 4242 · 300 年",
         **COMMON),
]
TAGS = {"preset-anime-farm250": "A", "preset-anime-exp06": "B",
        "preset-anime-farm0": "C", "preset-anime-farm1000": "D"}

MANIFEST = (config.REPO_ROOT / "docs" / "evidence" / "anime-cases-20260914"
            / "anime-cases-manifest.json")

# 前端要的五类事件 -> 记录里的判据。回助不是独立事件类型：它是 aid 上的两个字段。
CATEGORIES = (
    ("clearing", "开垦", lambda e: e["type"] == "field_built"),
    ("harvest", "收获", lambda e: e["type"] == "farm_harvest"),
    ("migrate", "迁移", lambda e: e["type"] == "migrate"),
    ("aid", "援助", lambda e: e["type"] == "aid"),
    ("repay", "回助", lambda e: e["type"] == "aid" and e.get("repay") is True),
)


def _absence(case, key):
    """缺项要说清是**哪一种**缺：引擎没有这套机制 / 参数关掉了 / 机制开着但没发生。"""
    farm_side = key in ("clearing", "harvest")
    if farm_side and case["engine"] != "exp07":
        return ("engine_lacks_mechanism",
                "这台引擎没有农业机制，年度记录里整个 farm 段都缺席（不是 0）")
    if farm_side and case.get("farm_m", 0) == 0:
        return ("param_zero",
                "FARM_M=0：机制在、farm 段也在，但一分劳动都没投到耕作，所以没有这类事件")
    return ("not_observed", "机制开着、参数非 0，但这 300 年里一次都没有发生")


def scan(run_id, case):
    """读刚生成的逐年记录，统计五类事件的首次年份与事件 id。"""
    src = presets.PRESET_DIR / run_id
    rows = [json.loads(l) for l in (src / "years.jsonl").open(encoding="utf-8")]
    info = json.loads((src / "run.json").read_text(encoding="utf-8"))
    out = {}
    for key, label, pred in CATEGORIES:
        hits = [(r["t"], e["id"]) for r in rows for e in r["events"] if pred(e)]
        if hits:
            out[key] = {"label": label, "present": True, "count": len(hits),
                        "first_year": hits[0][0], "first_event_id": hits[0][1],
                        "last_year": hits[-1][0], "last_event_id": hits[-1][1]}
        else:
            code, why = _absence(case, key)
            out[key] = {"label": label, "present": False, "count": 0,
                        "first_year": None, "first_event_id": None,
                        "reason_code": code, "reason": why}
    last = rows[-1]
    return {
        "sample_id": run_id,
        "tag": TAGS[run_id],
        "label": case["label"],
        "engine": case["engine"],
        "engine_label": config.ENGINES[case["engine"]]["label"],
        "engine_sha256": info["engine_sha256"],
        "engine_path": info["engine_path"],
        "config": {k: case[k] for k in
                   ("seed", "years", "sigma_m", "move_mort_m", "share_m", "aid_m",
                    "recip_m", "arm")} | (
                   {"farm_m": case["farm_m"]} if case["engine"] == "exp07"
                   else {"farm_m": None}),
        "model_run_id": info["model_run_id"],
        "full_digest": info["full_digest"],
        "has_farm_section": "farm" in last,
        "final_year": {"year": last["t"], "pop": last["agg"]["pop"],
                       "bands": last["agg"]["bands"],
                       "store_total_kcal": last["agg"]["store_total"],
                       "field_total_m": (last["farm"]["field_total_m"]
                                         if "farm" in last else None)},
        "total_events": sum(len(r["events"]) for r in rows),
        "events": out,
    }


def manifest():
    return {
        "contract": "anime-cases-1",
        "what": "交给前端的四条真实案例：固定 sample_id、固定模型哈希、五类事件的真实年份与事件 id。",
        "id_note": ("sample_id 是**预置案例的固定 run_id**，不是随机 uuid；"
                    "model_run_id / full_digest 由种子 + 全部规则参数 + 引擎常量决定，"
                    "同一版引擎在任何机器上重算都一样。"),
        "absence_codes": {
            "engine_lacks_mechanism": "这台引擎没有这套机制，字段整段缺席，界面显示未记录，不要填 0",
            "param_zero": "机制在、字段在，值确实是 0",
            "not_observed": "机制开着、参数非 0，但这段历史里没有发生",
        },
        "endpoints": {
            "run": "GET /api/runs/{sample_id}",
            "year": "GET /api/runs/{sample_id}/year/{t}",
            "series": "GET /api/runs/{sample_id}/series",
            "band": "GET /api/runs/{sample_id}/band/{band_id}?at_year=N",
            "relations": "GET /api/runs/{sample_id}/relations?at_year=N",
            "config": "GET /api/config",
        },
        "install": ["python3 -m observer.make_anime_cases",
                    "OBSERVER_DATA_DIR=<空目录> python3 -m uvicorn observer.app:app "
                    "--host 127.0.0.1 --port <空闲端口>"],
        "samples": [scan(c["run_id"], c) for c in CASES],
    }


def main(argv):
    check = "--check" in argv
    if not check:
        for case in CASES:
            out = presets.build(**case)
            size = sum(p.stat().st_size for p in out.iterdir()) / 1024 / 1024
            print(f"已生成 {out.name}（{size:.1f} MB）")
    doc = manifest()
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    if check:
        old = MANIFEST.read_text(encoding="utf-8")
        if old != text:
            print("清单与已提交的那份不一致", file=sys.stderr)
            return 1
        print("清单与已提交的那份逐字节相同")
        return 0
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(text, encoding="utf-8")
    print(f"清单已写入 {MANIFEST}")
    for s in doc["samples"]:
        have = [v["label"] for v in s["events"].values() if v["present"]]
        miss = [f"{v['label']}({v['reason_code']})" for v in s["events"].values()
                if not v["present"]]
        print(f"  {s['tag']} {s['sample_id']:24s} 有：{'/'.join(have) or '无'}"
              + (f"   缺：{'/'.join(miss)}" if miss else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
