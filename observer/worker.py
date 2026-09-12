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

from . import adapter, store


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

    try:
        eng = run["engine"] if "engine" in run.keys() else None
        keys = run.keys()
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
            store.worker_progress(run_id, pid, 0)
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
                    store.worker_finish(run_id, pid, "canceled", finished_at=time.time(),
                                        years_done=k, error=note, cancel_note=note)
                    return 0
                adapter.step(st, eng)                           # 原样调用引擎的 step
                store.append_year(fh, rec.year_record(st))
                now = time.time()
                if now - last_push > 0.25 or k == run["years"] - 1:
                    if not store.worker_progress(run_id, pid, k + 1):
                        print(f"运行 {run_id} 的进度写入被围栏拒绝，停止计算", file=sys.stderr)
                        return 4
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python -m observer.worker <run_id>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(execute(sys.argv[1]))
