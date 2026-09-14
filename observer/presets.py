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
        old = store.get_run(run_id)
        if old is not None:
            # 已经装过：只有内容确实变了（换了参数/重跑过）才刷新，否则跳过。
            # 以前这里无条件跳过，结果更新了预置数据、库里还是旧的一份。
            # 摘要相同还不够：引擎代码变了（engine_sha256 变了）也要刷新，
            # 否则界面上标的"引擎身份"会停留在旧版本。
            # 摘要与引擎都没变，还要看**记录文件本身**是否一样：
            # 记录层加了新字段（模型结果不变）时摘要照旧相同，只比摘要会漏刷。
            same_files = all(
                (src / nm).exists() and (store.run_dir(run_id) / nm).exists()
                and (src / nm).read_bytes() == (store.run_dir(run_id) / nm).read_bytes()
                for nm in ("years.jsonl", "meta.json"))
            if (old["full_digest"] == info["full_digest"]
                    and old["engine_sha256"] == info["engine_sha256"]
                    and same_files):
                continue
            with store.connect() as conn:
                conn.execute("DELETE FROM runs WHERE run_id=?", (run_id,))
            _CACHE_RESET = getattr(store, "_CACHE", None)
            if isinstance(_CACHE_RESET, dict):
                _CACHE_RESET.pop(run_id, None)
        dst = store.run_dir(run_id)
        dst.mkdir(parents=True, exist_ok=True)
        for name in ("years.jsonl", "meta.json"):
            if (src / name).exists():
                shutil.copyfile(src / name, dst / name)
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO runs (run_id,label,kind,status,created_at,started_at,finished_at,"
                "seed,years,sigma_m,move_mort_m,share_m,aid_m,recip_m,engine,arm,years_done,"
                "engine_sha256,engine_path,baseline_commit,repo_commit,model_run_id,"
                "full_digest,farm_m) VALUES (?,?,'preset','done',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, info["label"], info["created_at"], info["created_at"],
                 info["created_at"], info["seed"], info["years"], info["sigma_m"],
                 info["move_mort_m"], info.get("share_m", 0), info.get("aid_m", 0),
                 info.get("recip_m", 0), info.get("engine", "exp03"),
                 info["arm"], info["years"], info["engine_sha256"],
                 info["engine_path"], info["baseline_commit"], info.get("repo_commit", ""),
                 info["model_run_id"], info["full_digest"],
                 # EXP-07 的预置案例必须把 farm_m 一起登记：漏了它，库里会写成 0，
                 # 界面与续演比对就会拿"参数 0"去对一份 FARM_M≠0 的历史。
                 info.get("farm_m", 0)))
        n += 1
    return n


def build(seed: int, years: int, sigma_m: int, move_mort_m: int, arm: str,
          label: str, run_id: str, engine: str = None, share_m: int = 0,
          aid_m: int = 0, recip_m: int = 0, farm_m: int = 0) -> Path:
    """真跑一次，把结果写进 observer/preset/<run_id>/。"""
    from . import adapter
    out = PRESET_DIR / run_id
    out.mkdir(parents=True, exist_ok=True)
    st = adapter.make_world(seed, sigma_m, move_mort_m, arm, engine=engine,
                            share_m=share_m, aid_m=aid_m, recip_m=recip_m, farm_m=farm_m)
    meta = adapter.static_run_meta(st)
    meta["engine"] = adapter.engine_info(engine)   # 必须带上引擎名：
    # 漏了它，预置案例会把**默认引擎**的代码版本记成自己的（本轮修）
    ident0 = adapter.run_identity(st)
    meta["model_run_id"] = ident0["model_run_id"]
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    rec = adapter.Recorder(engine)
    with (out / "years.jsonl").open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(rec.year_record(st), ensure_ascii=False, separators=(",", ":")) + "\n")
        for _ in range(years):
            adapter.step(st, engine)
            fh.write(json.dumps(rec.year_record(st), ensure_ascii=False,
                                separators=(",", ":")) + "\n")
    final = adapter.run_identity(st, engine)
    info = {"run_id": run_id, "label": label, "seed": seed, "years": years,
            "sigma_m": sigma_m, "move_mort_m": move_mort_m, "arm": arm,
            "engine": engine or config.DEFAULT_ENGINE, "share_m": share_m,
            "aid_m": aid_m, "recip_m": recip_m, "farm_m": farm_m,
            "created_at": time.time(),
            "engine_sha256": meta["engine"]["engine_sha256"],
            "engine_path": meta["engine"]["engine_path"],
            "baseline_commit": meta["engine"]["baseline_commit"],
            "model_run_id": final["model_run_id"], "full_digest": final["full_digest"]}
    (out / "run.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    return out
