"""外部运行器：初始化世界 → 记录第 0 步 → 调用原 step → 记录状态副本与当步指标。

以独立子进程执行（`python -m observer.worker <run_id>`），所以模拟计算不阻塞页面访问。
本模块只读模型状态，不往模型对象里写观察数据，也不消耗模型随机数。

**状态围栏**：所有对台账的写入都带 `status='running' AND pid=<自己>` 的条件。
一旦服务端把这次运行判成 interrupted / canceled，本进程再也改不回 done——
这条规则配合“服务启动时先停旧进程、再标中断”的顺序，堵住了
“记录标成中断、旧进程却继续写并改回完成”这条路。
"""
from __future__ import annotations

import os
import sys
import time
import traceback

from . import adapter, checkpoints, config, continuation, store


def _write_checkpoint(run_id, eng, st, rec, fh, years_file):
    """在**完整年度边界**上存检查点。

    顺序是固定的：年度记录已经 append + flush + fsync（调用方保证）-> 这里再把
    检查点写进临时文件、flush、fsync、os.replace -> 调用方最后才公布可续演年。
    只保留最新一份，不逐年堆越来越大的模型副本。

    **这一步一个随机数都不取、一个字段都不改模型。** 用的全是只读函数
    （state_hash / full_digest / run_id）与状态的编码副本。
    """
    if eng not in config.CONTINUATION_ENGINES:
        return None
    fh.flush()
    os.fsync(fh.fileno())
    size = years_file.stat().st_size
    doc = checkpoints.build(
        engine=eng,
        engine_sha256=adapter.engine_info(eng)["engine_sha256"],
        engine_path=adapter.engine_info(eng)["engine_path"],
        params=continuation.run_params({
            "seed": st["seed"], "sigma_m": st.get("sigma_m"),
            "move_mort_m": st.get("move_mort_m"), "share_m": st.get("share_m"),
            "aid_m": st.get("aid_m"), "recip_m": st.get("recip_m"),
            "arm": ARM_OF_POISON.get(st.get("poison", ""), st.get("poison", "")),
        }),
        params_fingerprint=adapter.engine_info(eng)["params_fingerprint"],
        model_run_id=adapter.run_identity(st, eng)["model_run_id"],
        tick=st["tick"],
        full_digest=adapter.run_identity(st, eng)["full_digest"],
        state_hash=adapter.run_identity(st, eng)["state_hash"],
        model_state=st,
        recorder_state=rec.export_state(),
        history_bytes=size,
        history_records=store.year_count(run_id),
        history_sha256=checkpoints.prefix_sha256(years_file, size))
    checkpoints.save(store.checkpoint_path(run_id), doc)
    return doc


ARM_OF_POISON = {cfg["poison"]: name for name, cfg in config.ARMS.items()}


def execute(run_id: str) -> int:
    pid = os.getpid()
    run = store.get_run(run_id)
    if run is None:
        print(f"没有这次运行：{run_id}", file=sys.stderr)
        return 2
    if not store.worker_begin(run_id, pid):
        # 记录已经不是 queued（被取消、被判中断，或另有进程接手），本进程一个字都不写
        print(f"运行 {run_id} 已不可接管（当前状态 {store.get_run(run_id)['status']}），退出",
              file=sys.stderr)
        return 3

    parent_id = run["parent_run_id"] if "parent_run_id" in run.keys() else ""
    try:
        eng = run["engine"] if "engine" in run.keys() else None
        keys = run.keys()
        if parent_id:
            return _resume(run_id, pid, run, eng, parent_id)
        st = adapter.make_world(run["seed"], run["sigma_m"], run["move_mort_m"], run["arm"],
                                engine=eng,
                                share_m=run["share_m"] if "share_m" in keys else 0,
                                aid_m=run["aid_m"] if "aid_m" in keys else 0,
                                recip_m=run["recip_m"] if "recip_m" in keys else 0)
        ident = adapter.run_identity(st, eng)
        meta = adapter.static_run_meta(st)
        meta["engine"] = adapter.engine_info(eng)
        meta["model_run_id"] = ident["model_run_id"]
        store.write_meta(run_id, meta)

        rec = adapter.Recorder(eng)
        path = store.years_path(run_id)
        with path.open("w", encoding="utf-8") as fh:
            store.append_year(fh, rec.year_record(st))          # 第 0 步：开局状态
            _write_checkpoint(run_id, eng, st, rec, fh, path)   # 第 0 年同样存检查点
            store.worker_progress(run_id, pid, 0)               # 公布可续演年
            store.mark_history_ready(run_id)
            store.set_segment_progress(run_id, pid, 0)
            last_push = time.time()
            for k in range(run["years"]):
                state = store.worker_state(run_id, pid)
                if state is None or state["status"] != "running" or state["pid"] != pid:
                    print(f"运行 {run_id} 已被服务端接管或判定结束，停止计算", file=sys.stderr)
                    return 4                                    # 被围栏拦下，不改状态
                if state["cancel_requested"]:
                    # 协作收尾：这一年还没开始算，前 k 年都是完整写入的。
                    note = ("用户取消：工作进程在第 %d 年的边界上自己停下，"
                            "前 %d 年完整保存，可以回放。" % (k, k))
                    store.set_segment_progress(run_id, pid, k)
                    store.worker_finish(run_id, pid, "canceled", finished_at=time.time(),
                                        years_done=k, error=note, cancel_note=note)
                    return 0
                adapter.step(st, eng)                           # 原样调用引擎的 step
                store.append_year(fh, rec.year_record(st))
                _write_checkpoint(run_id, eng, st, rec, fh, path)
                now = time.time()
                if now - last_push > 0.25 or k == run["years"] - 1:
                    # 记录与检查点都落盘之后，才公布"算到第几年"
                    if not store.worker_progress(run_id, pid, k + 1):
                        print(f"运行 {run_id} 的进度写入被围栏拒绝，停止计算", file=sys.stderr)
                        return 4
                    store.set_segment_progress(run_id, pid, k + 1)
                    last_push = now

        final = adapter.run_identity(st, eng)
        ok = store.worker_finish(run_id, pid, "done", finished_at=time.time(),
                                 years_done=run["years"], full_digest=final["full_digest"],
                                 model_run_id=final["model_run_id"])
        if not ok:
            print(f"运行 {run_id} 已被判定结束，不改写为 done", file=sys.stderr)
            return 4
        return 0
    except Exception as exc:                                    # noqa: BLE001
        store.worker_finish(run_id, pid, "failed", finished_at=time.time(),
                            error=f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        return 1


def _resume(run_id, pid, run, eng, parent_id):
    """续演：从父运行的检查点接着算，**不重跑第 0..C 年**。

    先把父运行的有效历史前缀原样复制成子运行自己的文件（复制也算在这个任务槽里），
    再恢复模型与记录器，从第 C+1 年往后追加。第 C 年只从父历史来一次，
    子运行**不重复输出第 C 年**。
    """
    parent = store.get_run(parent_id)
    if parent is None:
        raise RuntimeError("父运行 %s 已经不在了" % parent_id)
    verdict = continuation.eligibility(parent)          # 启动时**重新**校验一遍
    if not verdict["eligible"]:
        note = "续演前复核不通过：%s（%s）" % (verdict["reason"], verdict["reason_code"])
        store.worker_finish(run_id, pid, "failed", finished_at=time.time(), error=note)
        print(note, file=sys.stderr)
        return 1

    payload = checkpoints.load(store.checkpoint_path(parent_id))
    live = adapter.engine_info(eng)
    # 引擎身份再核一次，**全量 sha256 逐字比对**，不用短前缀，也不看展示用的版本块。
    if payload["engine"] != eng or payload["engine_sha256"] != live["engine_sha256"]:
        note = "续演前引擎身份不符，拒绝加载"
        store.worker_finish(run_id, pid, "failed", finished_at=time.time(), error=note)
        return 1

    hist = payload["history"]
    continuation.prepare_history(parent_id, run_id, hist["bytes"])
    st, rec_state = checkpoints.restore(payload)
    rec = adapter.Recorder.from_state(rec_state)
    if st["tick"] != payload["tick"] or rec.engine != eng:
        note = "检查点内部对不上（tick 或引擎名），拒绝续演"
        store.worker_finish(run_id, pid, "failed", finished_at=time.time(), error=note)
        return 1
    # 恢复出来的状态必须与检查点记的身份逐字相符，否则解码本身就出了问题。
    ident = adapter.run_identity(st, eng)
    if ident["state_hash"] != payload["state_hash"] or \
            ident["full_digest"] != payload["full_digest"]:
        note = "恢复出来的状态哈希与检查点不符，拒绝续演"
        store.worker_finish(run_id, pid, "failed", finished_at=time.time(), error=note)
        return 1

    meta = store.read_meta(parent_id) or {}
    meta.update({"root_run_id": run["root_run_id"], "parent_run_id": parent_id,
                 "from_year": int(run["from_year"]),
                 "additional_years": int(run["additional_years"]),
                 "history_note": "第 0..%d 年继承自父运行 %s 的原始字节，"
                                 "不是由本次计算重新产生的"
                                 % (int(run["from_year"]), parent_id)})
    store.write_meta(run_id, meta)

    from_year = int(run["from_year"])
    target = int(run["years"])
    path = store.years_path(run_id)
    with path.open("a", encoding="utf-8") as fh:     # **追加**，不是 w
        store.worker_progress(run_id, pid, from_year)
        store.set_segment_progress(run_id, pid, 0)
        last_push = time.time()
        for k in range(from_year, target):
            state = store.worker_state(run_id, pid)
            if state is None or state["status"] != "running" or state["pid"] != pid:
                print(f"运行 {run_id} 已被服务端接管或判定结束，停止计算", file=sys.stderr)
                return 4
            if state["cancel_requested"]:
                note = ("用户取消：续演进程在第 %d 年的边界上自己停下，"
                        "到该年为止的历史完整可回放。" % k)
                store.set_segment_progress(run_id, pid, k - from_year)
                store.worker_finish(run_id, pid, "canceled", finished_at=time.time(),
                                    years_done=k, error=note, cancel_note=note)
                return 0
            adapter.step(st, eng)
            store.append_year(fh, rec.year_record(st))
            _write_checkpoint(run_id, eng, st, rec, fh, path)
            now = time.time()
            if now - last_push > 0.25 or k == target - 1:
                if not store.worker_progress(run_id, pid, k + 1):
                    print(f"运行 {run_id} 的进度写入被围栏拒绝，停止计算", file=sys.stderr)
                    return 4
                store.set_segment_progress(run_id, pid, k + 1 - from_year)
                last_push = now

    final = adapter.run_identity(st, eng)
    ok = store.worker_finish(run_id, pid, "done", finished_at=time.time(),
                             years_done=target, full_digest=final["full_digest"],
                             model_run_id=final["model_run_id"])
    if not ok:
        print(f"运行 {run_id} 已被判定结束，不改写为 done", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python -m observer.worker <run_id>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(execute(sys.argv[1]))
