"""预生成案例：随仓库一起提供的一份真实模拟结果。

它是**预先算好的**，不是正在运行的任务 —— 页面上带“预生成”标记，不冒充实时任务。
数据放在 observer/preset/ 里跟着 git 走；observer/data/ 是运行期目录（不进版本库）。
启动时把缺失的预置案例装进数据目录与台账。
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import List

from . import config, store

PRESET_DIR = config.OBSERVER_DIR / "preset"


def available() -> List[Path]:
    if not PRESET_DIR.exists():
        return []
    return sorted(p for p in PRESET_DIR.iterdir() if (p / "run.json").exists())


def install_presets() -> int:
    store.init_db()
    n = 0
    for src in available():
        info = json.loads((src / "run.json").read_text(encoding="utf-8"))
        run_id = info["run_id"]
        if store.get_run(run_id):
            continue
        dst = store.run_dir(run_id)
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("years.jsonl", "meta.json"):
            if (src / name).exists():
                shutil.copyfile(src / name, dst / name)
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO runs (run_id,label,kind,status,created_at,started_at,finished_at,"
                "seed,years,sigma_m,move_mort_m,arm,years_done,engine_sha256,engine_path,"
                "baseline_commit,repo_commit,model_run_id,full_digest) "
                "VALUES (?,?,'preset','done',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, info["label"], info["created_at"], info["created_at"],
                 info["created_at"], info["seed"], info["years"], info["sigma_m"],
                 info["move_mort_m"], info["arm"], info["years"], info["engine_sha256"],
                 info["engine_path"], info["baseline_commit"], info.get("repo_commit", ""),
                 info["model_run_id"], info["full_digest"]))
        n += 1
    return n


def build(seed: int, years: int, sigma_m: int, move_mort_m: int, arm: str,
          label: str, run_id: str) -> Path:
    """真跑一次，把结果写进 observer/preset/<run_id>/。"""
    from . import adapter
    out = PRESET_DIR / run_id
    out.mkdir(parents=True, exist_ok=True)
    st = adapter.make_world(seed, sigma_m, move_mort_m, arm)
    meta = adapter.static_run_meta(st)
    meta["engine"] = adapter.engine_info()
    ident0 = adapter.run_identity(st)
    meta["model_run_id"] = ident0["model_run_id"]
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    rec = adapter.Recorder()
    with (out / "years.jsonl").open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec.year_record(st), ensure_ascii=False, separators=(",", ":")) + "\n")
        for _ in range(years):
            adapter.step(st)
            fh.write(json.dumps(rec.year_record(st), ensure_ascii=False,
                                separators=(",", ":")) + "\n")
    final = adapter.run_identity(st)
    info = {"run_id": run_id, "label": label, "seed": seed, "years": years,
            "sigma_m": sigma_m, "move_mort_m": move_mort_m, "arm": arm,
            "created_at": time.time(),
            "engine_sha256": meta["engine"]["engine_sha256"],
            "engine_path": meta["engine"]["engine_path"],
            "baseline_commit": meta["engine"]["baseline_commit"],
            "model_run_id": final["model_run_id"], "full_digest": final["full_digest"]}
    (out / "run.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    return out
