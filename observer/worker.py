"""外部运行器：初始化世界 → 记录第 0 步 → 调用原 step → 记录状态副本与当步指标。

以独立子进程执行（`python -m observer.worker <run_id>`），所以模拟计算不阻塞页面访问。
本模块只读模型状态，不往模型对象里写观察数据，也不消耗模型随机数。
"""
from __future__ import annotations

import json
import sys
import time
import traceback

from . import adapter, config, store


def execute(run_id: str) -> int:
    run = store.get_run(run_id)
    if run is None:
        print(f"没有这次运行：{run_id}", file=sys.stderr)
        return 2
    if run["status"] not in ("queued", "running"):
        print(f"运行 {run_id} 的状态是 {run['status']}，不再执行", file=sys.stderr)
        return 3

    store.set_status(run_id, "running", started_at=time.time(), pid=None)
    try:
        st = adapter.make_world(run["seed"], run["sigma_m"], run["move_mort_m"], run["arm"])
        ident = adapter.run_identity(st)
        meta = adapter.static_run_meta(st)
        meta["engine"] = adapter.engine_info()
        meta["model_run_id"] = ident["model_run_id"]
        store.write_meta(run_id, meta)
        store.set_status(run_id, "running", model_run_id=ident["model_run_id"])

        rec = adapter.Recorder()
        path = store.years_path(run_id)
        with path.open("w", encoding="utf-8") as fh:
            store.append_year(fh, rec.year_record(st))          # 第 0 步：开局状态
            store.update_progress(run_id, 0)
            last_push = time.time()
            for k in range(run["years"]):
                if store.cancel_requested(run_id):
                    store.set_status(run_id, "canceled", finished_at=time.time(),
                                     years_done=k, error="用户取消")
                    return 0
                adapter.step(st)                                # 原样调用引擎的 step
                store.append_year(fh, rec.year_record(st))
                now = time.time()
                if now - last_push > 0.25 or k == run["years"] - 1:
                    store.update_progress(run_id, k + 1)
                    last_push = now

        final = adapter.run_identity(st)
        store.set_status(run_id, "done", finished_at=time.time(),
                         years_done=run["years"], full_digest=final["full_digest"],
                         model_run_id=final["model_run_id"])
        return 0
    except Exception as exc:                                    # noqa: BLE001
        store.set_status(run_id, "failed", finished_at=time.time(),
                         error=f"{type(exc).__name__}: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python -m observer.worker <run_id>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(execute(sys.argv[1]))
