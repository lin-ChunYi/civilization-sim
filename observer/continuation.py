"""续演：判定一条运行此刻能不能从检查点继续算，并为子运行准备好历史前缀。

本文件**不跑模型**，也不启动进程。它只回答两个问题：

1. 这条记录现在有没有资格续演（`eligibility`）——不行的话给一个明确的原因码；
2. 子运行的历史前缀怎么从父运行**复制**过来（`prepare_history`）。

两条容易混淆的概念，这里分得很清：

* `supported` —— **引擎**支不支持续演（本批只有 EXP-06 会写检查点）；
* `eligible`  —— **这条记录此刻**能不能续演。

引擎支持但这条记录没有检查点，是 `supported=true, eligible=false`。
没有检查点时 `from_year` 就是 `null` —— **不拿最后一帧画面的年份冒充检查点年份**。
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from . import adapter, checkpoints, config, store

READY = "ready"
# 不可续演的原因码。人话说明必须和它说的是同一件事。
REASONS = (
    "unsupported_engine", "missing_checkpoint", "source_active", "worker_unknown",
    "checkpoint_invalid", "checkpoint_not_at_tip", "engine_mismatch", "config_mismatch",
    "world_limit", "quota_exceeded",
)
# 所有引擎都有的那几项。**FARM_M 不能无条件加进来**：
# 旧的 EXP-06 检查点里根本没有这个键，而新数据库的 farm_m 默认是 0，
# 于是 None != 0 会把一份完全正常的旧存档判成 config_mismatch。
# 只对**声明支持它的引擎**才把 farm_m 纳入比对。
PARAM_KEYS = ("seed", "sigma_m", "move_mort_m", "share_m", "aid_m", "recip_m", "arm")
ENGINE_EXTRA_PARAM_KEYS = ("farm_m",)


def param_keys_for(engine_name):
    """这台引擎要比对哪些参数。旧引擎的键集合**保持原样**，新键只加给支持它的引擎。"""
    params = config.ENGINES.get(engine_name, {}).get("params", [])
    return PARAM_KEYS + tuple(k for k in ENGINE_EXTRA_PARAM_KEYS if k in params)


def _no(code: str, why: str, *, supported: bool = True,
        from_year: Optional[int] = None) -> Dict[str, Any]:
    return {"supported": supported, "eligible": False, "reason_code": code, "reason": why,
            "from_year": from_year, "max_additional_years": 0,
            "max_world_year": config.MAX_WORLD_YEAR,
            "checkpoint_schema": checkpoints.CHECKPOINT_SCHEMA}


def run_params(run: Dict[str, Any], engine_name: str = None) -> Dict[str, Any]:
    name = engine_name or run.get("engine") or config.DEFAULT_ENGINE
    return {k: run.get(k) for k in param_keys_for(name)}


def eligibility(run: Dict[str, Any], *, for_new_run: bool = True) -> Dict[str, Any]:
    """这条记录此刻能不能续演。**每次 POST 与每次 worker 启动都要重跑这一遍**，
    不拿缓存当许可证。

    `for_new_run` 把两件事分开：

      * `True`（POST 受理新请求时）：要做**资源准入** —— 运行条数与数据目录的上限。
      * `False`（worker 启动时对**已经占好槽**的任务复核存档）：只复核存档、历史与引擎身份，
        **不再做资源准入**。否则第 49 条续演占掉第 50 个名额之后，worker 一开机就会把
        "自己刚占的那一条"算成新的超限，把一个合法任务判死。
        上限本身没有放松：第 51 条仍然进不来，因为 POST 那一侧照样查。
    """
    engine = run.get("engine") or config.DEFAULT_ENGINE
    if engine not in config.CONTINUATION_ENGINES:
        return _no("unsupported_engine",
                   "引擎 %s 本批不写检查点，无法续演（目前只有 %s 支持）"
                   % (engine, "、".join(config.CONTINUATION_ENGINES)), supported=False)

    # 来源必须是**已确认结束**的终态，且没有活着或状态未知的旧工作进程。
    if run.get("status") not in store.TERMINAL:
        return _no("source_active", "这条运行还没结束（当前 %s），先让它结束或取消"
                   % run.get("status"))
    probe = store.probe_worker(run.get("pid"), run["run_id"])
    if probe == store.WORKER_ALIVE:
        return _no("source_active", "这条运行的旧工作进程还活着，不能同时续演")
    if probe == store.WORKER_UNKNOWN:
        return _no("worker_unknown",
                   "查不到这条运行的旧工作进程状态（ps 超时 / 权限不足）。"
                   "未知不等于已停止，这一轮先不放行")

    path = store.checkpoint_path(run["run_id"])
    if not path.exists():
        return _no("missing_checkpoint",
                   "这条运行没有检查点（旧运行与预生成案例都没有），不自动补跑")
    try:
        payload = checkpoints.load(path)
    except checkpoints.CheckpointError as exc:
        return _no("checkpoint_invalid", "检查点校验不过：%s" % exc)

    # 引擎身份：**全量 sha256 逐字比对**，不用短前缀。
    try:
        live = adapter.engine_info(engine)
    except Exception as exc:                                         # noqa: BLE001
        return _no("engine_mismatch", "读不出当前引擎信息：%s" % exc)
    if payload["engine"] != engine or payload["engine_sha256"] != live["engine_sha256"]:
        return _no("engine_mismatch",
                   "检查点记的引擎源码与现在这份不是同一版（%s… vs %s…）"
                   % (payload["engine_sha256"][:12], live["engine_sha256"][:12]))
    # 引擎对上了，再看记录器格式与这台引擎配不配。
    # 顺序不能反：引擎本身就不同的时候，engine_mismatch 才是准确的原因。
    want_rec = adapter.Recorder.schema_for(engine)
    if payload.get("recorder_schema") != want_rec:
        return _no("checkpoint_invalid",
                   "记录器格式 %s 与引擎 %s 对不上（应为 %s）；旧存档不会被无声升级"
                   % (payload.get("recorder_schema"), engine, want_rec))

    want = run_params(run, engine)
    got = payload.get("params") or {}
    diff = [k for k in param_keys_for(engine) if got.get(k) != want.get(k)]
    if diff or payload.get("params_fingerprint") != live["params_fingerprint"]:
        return _no("config_mismatch",
                   "检查点的配置与这条运行对不上：%s" % (", ".join(diff) or "参数指纹不同"))

    hist = payload["history"]
    years_file = store.years_path(run["run_id"])
    try:
        size = years_file.stat().st_size
    except OSError as exc:
        return _no("checkpoint_invalid", "读不到历史文件：%s" % exc)
    if size < hist["bytes"]:
        return _no("checkpoint_invalid", "历史文件比检查点记的还短，记录与检查点对不上")
    try:
        if checkpoints.prefix_sha256(years_file, hist["bytes"]) != hist["sha256"]:
            return _no("checkpoint_invalid", "历史前缀的校验和与检查点对不上")
    except checkpoints.CheckpointError as exc:
        return _no("checkpoint_invalid", str(exc))

    # 完整历史比检查点更新：历史照样能回放，但**这一版明确拒绝从它续演**。
    complete = store.year_count(run["run_id"])
    if complete > hist["records"]:
        return _no("checkpoint_not_at_tip",
                   "完整历史已经到第 %d 年，检查点停在第 %d 年。历史仍可回放，"
                   "但本版不从对不齐的地方续演；不会删历史，也不会伪造较新的检查点"
                   % (complete - 1, payload["tick"]), from_year=payload["tick"])
    if complete < hist["records"]:
        return _no("checkpoint_invalid",
                   "完整历史只有 %d 条，检查点却说有 %d 条" % (complete, hist["records"]))

    from_year = int(payload["tick"])
    room = config.MAX_WORLD_YEAR - from_year
    if room < config.MIN_ADDITIONAL_YEARS:
        return _no("world_limit",
                   "已经到第 %d 年，累计世界年上限是 %d 年，没有可新增的年数"
                   % (from_year, config.MAX_WORLD_YEAR), from_year=from_year)
    if for_new_run and (store.run_count() >= config.MAX_RUNS
                        or store.data_size_mb() >= config.MAX_DATA_MB):
        return _no("quota_exceeded",
                   "运行条数或数据目录已达上限（续演要复制一份完整历史，同样占配额）",
                   from_year=from_year)

    return {"supported": True, "eligible": True, "reason_code": READY,
            "reason": "可从第 %d 年继续" % from_year,
            "from_year": from_year,
            "max_additional_years": min(config.MAX_ADDITIONAL_YEARS, room),
            "max_world_year": config.MAX_WORLD_YEAR,
            "checkpoint_schema": checkpoints.CHECKPOINT_SCHEMA}


def prepare_history(parent_run_id: str, child_run_id: str, nbytes: int) -> int:
    """把父运行**有效前缀的原始字节**复制成子运行自己的 years.jsonl。

    不用硬链接、不共享可写文件：复制完的子运行完全独立，回放不依赖祖先文件。
    先写临时文件、fsync、再 os.replace 发布 —— 发布之前 history_ready 一直是 false。
    """
    src = store.years_path(parent_run_id)
    dst = store.years_path(child_run_id)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".jsonl.prefix-tmp")
    copied = 0
    with src.open("rb") as fin, tmp.open("wb") as fout:
        left = nbytes
        while left > 0:
            chunk = fin.read(min(1 << 20, left))
            if not chunk:
                raise ValueError("父运行的历史比预期短，复制中止")
            fout.write(chunk)
            copied += len(chunk)
            left -= len(chunk)
        fout.flush()
        os.fsync(fout.fileno())
    os.replace(tmp, dst)
    try:
        os.chmod(dst, 0o600)
    except OSError:
        pass
    store._CACHE.pop(child_run_id, None)
    store.mark_history_ready(child_run_id)
    return copied


def checkpoint_bytes(run_id: str) -> int:
    try:
        return store.checkpoint_path(run_id).stat().st_size
    except OSError:
        return 0
