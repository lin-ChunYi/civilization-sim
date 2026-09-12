"""OBS-01 文明观察台：FastAPI 同时提供网页与 API。

- 读接口：里程碑、模型信息、运行列表、逐年记录。
- 写接口：新建运行、取消、删除。全部服务端校验 + 令牌鉴权 + 限流 + 单并发。
- 模拟在独立子进程里跑，页面用定时轮询看进度，不阻塞。
"""
from __future__ import annotations

import subprocess
import sys
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StrictInt, StrictStr

from . import adapter, config, milestones, presets, store

app = FastAPI(title="文明观察台 OBS-01", docs_url=None, redoc_url=None)
# observer/web/ 归 UI 分支（Grok）所有；后台只读它，不往里写任何文件。
WEB_DIR = config.WEB_DIR


def repo_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                             cwd=config.REPO_ROOT, capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:  # noqa: BLE001
        return ""


@app.on_event("startup")
def _startup() -> None:
    store.init_db()
    k = presets.install_presets()
    if k:
        print(f"[observer] 装入 {k} 个预生成案例")
    n = store.recover_interrupted()
    if n:
        print(f"[observer] 启动时把 {n} 个未完成任务标记为中断")


# ---------------------------------------------------------------- 访问保护

_hits: Dict[str, Deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    return (request.client.host if request.client else "?")


def _token_of(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.headers.get("x-observer-token", "").strip()


def require_read(request: Request) -> None:
    """设了 OBSERVER_TOKEN 就全站需要令牌；没设则只读开放（本地单用户模式）。"""
    if not config.TOKEN:
        return
    if _token_of(request) != config.TOKEN:
        raise HTTPException(status_code=401, detail="需要访问令牌。请在页面右上角填入令牌。")


def require_write(request: Request) -> None:
    if config.TOKEN:
        if _token_of(request) != config.TOKEN:
            raise HTTPException(status_code=401, detail="写操作需要访问令牌。")
    else:
        if _client_ip(request) not in config.LOCAL_HOSTS:
            raise HTTPException(
                status_code=403,
                detail="未设置 OBSERVER_TOKEN 时，写操作只允许来自本机。"
                       "公网部署必须设置 OBSERVER_TOKEN。")
    ip = _client_ip(request)
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= config.WRITE_RATE_LIMIT:
        raise HTTPException(status_code=429,
                            detail=f"写请求过于频繁（每分钟上限 {config.WRITE_RATE_LIMIT} 次）。")
    q.append(now)


# ---------------------------------------------------------------- 读接口

@app.get("/api/health")
def health():
    return {"ok": True, "time": time.time()}


@app.get("/api/config", dependencies=[Depends(require_read)])
def get_config():
    return {
        "api_version": config.API_VERSION,       # 见 docs/OBS-01-API-CONTRACT.md
        "token_required": bool(config.TOKEN),
        "limits": {"min_years": config.MIN_YEARS, "max_years": config.MAX_YEARS,
                   "max_runs": config.MAX_RUNS, "max_data_mb": config.MAX_DATA_MB,
                   "max_seed": config.MAX_SEED,
                   "write_rate_per_min": config.WRITE_RATE_LIMIT},
        "arms": {k: {"label": v["label"], "note": v["note"]} for k, v in config.ARMS.items()},
        "engine": adapter.engine_info(),          # 默认引擎，保持向后兼容
        "engines": adapter.engines_info(),        # obs-1.2 新增：全部可用引擎
        "default_engine": config.DEFAULT_ENGINE,
        "repo_commit": repo_commit(),
        "data": {"runs": store.run_count(), "size_mb": round(store.data_size_mb(), 2)},
    }


@app.get("/api/milestones", dependencies=[Depends(require_read)])
def get_milestones():
    return {"statuses": milestones.STATUSES, "items": milestones.MILESTONES,
            "note": milestones.NOTE, "repo_commit": repo_commit()}


@app.get("/api/map", dependencies=[Depends(require_read)])
def get_map():
    return adapter.map_geometry()


@app.get("/api/runs", dependencies=[Depends(require_read)])
def get_runs():
    store.reap_stale()          # 顺手回收没人在算却占着槽的记录，列表才是真实状态
    runs = store.list_runs()
    for r in runs:
        r["years_recorded"] = max(store.year_count(r["run_id"]) - 1, 0)
    return {"runs": runs, "active": store.active_run()}


@app.get("/api/runs/{run_id}", dependencies=[Depends(require_read)])
def get_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, "没有这次运行")
    run["years_recorded"] = max(store.year_count(run_id) - 1, 0)
    run["meta"] = store.read_meta(run_id)
    # obs-1.5：这次运行**实际用的**引擎、参数（带标签与单位）、代码版本与状态，
    # 一次给全，前端不用再去拼 /api/config。
    eng = run.get("engine") or config.DEFAULT_ENGINE
    try:
        info = adapter.engine_info(eng)
        run["params_used"] = [
            {**spec, "value": run.get(spec["name"])}
            for spec in info["params"] if spec["name"] in run.keys()
        ]
        run["engine_label"] = info["engine_label"]
    except Exception:                                   # noqa: BLE001 引擎缺失也不能打挂接口
        run["params_used"] = []
    return run


@app.get("/api/runs/{run_id}/series", dependencies=[Depends(require_read)])
def get_series(run_id: str):
    if not store.get_run(run_id):
        raise HTTPException(404, "没有这次运行")
    return {"run_id": run_id, "series": store.read_series(run_id)}


@app.get("/api/runs/{run_id}/year/{t}", dependencies=[Depends(require_read)])
def get_year(run_id: str, t: int):
    if not store.get_run(run_id):
        raise HTTPException(404, "没有这次运行")
    rec = store.read_year(run_id, t)
    if rec is None:
        raise HTTPException(404, f"第 {t} 年还没有被计算出来（或超出本次运行范围）")
    # 老记录里没有事件 id（obs-1.5 之前写的），按同一套规则补上，保证前端拿到的都有稳定标识
    for i, e in enumerate(rec.get("events", [])):
        e.setdefault("id", f"t{rec['t']}-{e.get('type', 'event')}-{i}")
        e.setdefault("year", rec["t"])
    return rec


@app.get("/api/runs/{run_id}/band/{band_id}", dependencies=[Depends(require_read)])
def get_band(run_id: str, band_id: str):
    """某个群体的可记录轨迹。全部来自已保存的逐年记录与模型日志，不做任何推测。"""
    if not store.get_run(run_id):
        raise HTTPException(404, "没有这次运行")
    traj, sizes = [], []
    name = band_id
    first_seen = last_seen = None
    parent = None
    born_at = None
    children = []
    extinct_at = None
    for rec in store.iter_years(run_id):
        t = rec["t"]
        for b in rec["bands"]:
            if b["id"] == band_id:
                name = b["name"]
                if first_seen is None:
                    first_seen = t
                last_seen = t
                sizes.append([t, b["size"], b["store"]])
                if not traj or traj[-1][1] != b["cell"]:
                    traj.append([t, b["cell"]])
        for e in rec["events"]:
            if e["type"] == "split" and e.get("band") == band_id:
                parent, born_at = e.get("parent"), t
            elif e["type"] == "split" and e.get("parent") == band_id:
                children.append([t, e.get("band")])
            elif e["type"] == "extinct" and e.get("band") == band_id:
                extinct_at = t
    if first_seen is None:
        raise HTTPException(404, "这次运行里没有这个群体")
    return {"id": band_id, "name": name, "first_seen": first_seen, "last_seen": last_seen,
            "origin": ("由 " + parent + " 分裂而来" if parent else
                       ("开局的初始群体" if first_seen == 0 else "未记录")),
            "parent": parent, "born_at": born_at, "children": children,
            "extinct_at": extinct_at, "trajectory": traj, "sizes": sizes,
            "source": "全部来自本次运行已保存的逐年记录与模型日志；"
                      "群体层的出生/死亡分项未记录，账本只记全局分项。"}


# ---------------------------------------------------------------- 写接口

class NewRun(BaseModel):
    seed: StrictInt = Field(..., description="随机种子")
    years: StrictInt = Field(..., description="模拟年数")
    sigma_m: StrictInt = Field(0, description="SIGMA_M：资源再生年际波动强度，千分之一")
    move_mort_m: StrictInt = Field(0, description="MOVE_MORT_M：迁移死亡强度，千分之一")
    arm: StrictStr = Field("memory", description="信息条件（对照臂）")
    label: StrictStr = Field("", description="备注")
    engine: StrictStr = Field(config.DEFAULT_ENGINE, description="模拟引擎：exp03 | exp04")
    share_m: StrictInt = Field(0, description="SHARE_M：同格信息交换的参与概率，千分之一（exp04 起）")
    aid_m: StrictInt = Field(0, description="AID_M：供给方愿意拿出的可援助余粮比例，千分之一（exp05 起）")
    recip_m: StrictInt = Field(0, description="RECIP_M：优先回助的预算比例，千分之一（仅 exp06）")


def _validate(body: NewRun) -> None:
    if body.engine not in config.ENGINES:
        raise HTTPException(400, f"engine 只能是 {sorted(config.ENGINES)} 之一")
    v3, _ = adapter.load_engine(body.engine)
    params = config.ENGINES[body.engine]["params"]
    if "share_m" in params:
        if not (v3.SHARE_M_MIN <= body.share_m <= v3.SHARE_M_MAX):
            raise HTTPException(400, f"SHARE_M 越界，合法范围 "
                                     f"[{v3.SHARE_M_MIN}, {v3.SHARE_M_MAX}]")
    elif body.share_m != 0:
        raise HTTPException(400, f"引擎 {body.engine} 没有 SHARE_M 这个参数，"
                                 f"要用同格信息交换请选 exp04")
    if "aid_m" in params:
        if not (v3.AID_M_MIN <= body.aid_m <= v3.AID_M_MAX):
            raise HTTPException(400, f"AID_M 越界，合法范围 [{v3.AID_M_MIN}, {v3.AID_M_MAX}]")
    elif body.aid_m != 0:
        raise HTTPException(400, f"引擎 {body.engine} 没有 AID_M 这个参数，"
                                 f"要用同格食物援助请选 exp05")
    if "recip_m" in params:
        if not (v3.RECIP_M_MIN <= body.recip_m <= v3.RECIP_M_MAX):
            raise HTTPException(400, f"RECIP_M 越界，合法范围 "
                                     f"[{v3.RECIP_M_MIN}, {v3.RECIP_M_MAX}]")
    elif body.recip_m != 0:
        raise HTTPException(400, f"引擎 {body.engine} 没有 RECIP_M 这个参数，"
                                 f"要用优先回助请选 exp06")
    if not (0 <= body.seed <= config.MAX_SEED):
        raise HTTPException(400, f"seed 越界，合法范围 [0, {config.MAX_SEED}]")
    if not (config.MIN_YEARS <= body.years <= config.MAX_YEARS):
        raise HTTPException(400, f"年数越界，合法范围 [{config.MIN_YEARS}, {config.MAX_YEARS}]")
    if not (v3.SIGMA_M_MIN <= body.sigma_m <= v3.SIGMA_M_MAX):
        raise HTTPException(400, f"SIGMA_M 越界，合法范围 [{v3.SIGMA_M_MIN}, {v3.SIGMA_M_MAX}]")
    if not (v3.MOVE_MORT_M_MIN <= body.move_mort_m <= v3.MOVE_MORT_M_MAX):
        raise HTTPException(
            400, f"MOVE_MORT_M 越界，合法范围 [{v3.MOVE_MORT_M_MIN}, {v3.MOVE_MORT_M_MAX}]")
    if body.arm not in config.ARMS:
        raise HTTPException(400, f"arm 只能是 {list(config.ARMS)} 之一")
    if len(body.label) > 60:
        raise HTTPException(400, "备注最长 60 字")


@app.post("/api/runs", dependencies=[Depends(require_write)])
def post_run(body: NewRun):
    _validate(body)
    reaped = store.reap_stale()   # 先回收死记录，再占槽：死进程不该把槽永久占死
    if reaped:
        print(f"[observer] 回收了 {len(reaped)} 个无人执行的任务槽：{reaped}")
    if store.run_count() >= config.MAX_RUNS:
        raise HTTPException(409, f"运行条数已达上限 {config.MAX_RUNS}，请先删除旧运行。")
    if store.data_size_mb() >= config.MAX_DATA_MB:
        raise HTTPException(409, f"数据目录已达上限 {config.MAX_DATA_MB} MB，请先删除旧运行。")

    # 占槽与建记录在同一个事务里完成：两个同时到达的请求只有一个能拿到槽
    run_id = store.claim_slot(seed=body.seed, years=body.years, sigma_m=body.sigma_m,
                              move_mort_m=body.move_mort_m, arm=body.arm,
                              label=body.label, kind="user", share_m=body.share_m,
                              aid_m=body.aid_m, recip_m=body.recip_m,
                              engine_name=body.engine,
                              engine=adapter.engine_info(body.engine),
                              repo_commit=repo_commit())
    if run_id is None:
        act = store.active_run()
        raise HTTPException(409, "已有任务在跑" +
                            (f"（{act['run_id']}，{act['years_done']}/{act['years']} 年）"
                             if act else "") +
                            "。本版同时只执行一个模拟任务，请等它结束或先取消。")
    try:
        proc = subprocess.Popen([sys.executable, "-m", "observer.worker", run_id],
                                cwd=str(config.REPO_ROOT), start_new_session=True)
    except Exception as exc:                                    # noqa: BLE001
        store.drop_run_row(run_id)                              # 起不来就把槽还回去
        raise HTTPException(500, f"工作进程启动失败：{type(exc).__name__}: {exc}")
    store.set_pid(run_id, proc.pid)      # 只写 pid，不碰 status（工作进程可能已经 running）
    return {"run_id": run_id, "status": "queued"}


@app.post("/api/runs/{run_id}/cancel", dependencies=[Depends(require_write)])
def cancel_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, "没有这次运行")
    if run["status"] not in ("queued", "running"):
        raise HTTPException(409, f"该运行状态为 {run['status']}，无需取消")
    store.request_cancel(run_id)
    if not store._is_our_worker(run["pid"], run_id):
        # 进程已经不在了，取消请求没人会读到：直接按“回收”处理，别让槽卡住
        store.reap_stale()
        return {"ok": True, "note": "该运行的工作进程已不在，任务槽已回收并标记为中断。"}
    return {"ok": True, "note": "已请求取消，工作进程会在当前这一年算完后停下。"}


@app.delete("/api/runs/{run_id}", dependencies=[Depends(require_write)])
def delete_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, "没有这次运行")
    if run["status"] in ("queued", "running"):
        raise HTTPException(409, "任务还在跑，先取消再删除")
    if run["kind"] == "preset":
        raise HTTPException(409, "预生成案例不可删除")
    import shutil
    shutil.rmtree(store.run_dir(run_id), ignore_errors=True)
    with store.connect() as conn:
        conn.execute("DELETE FROM runs WHERE run_id=?", (run_id,))
    return {"ok": True}


# ---------------------------------------------------------------- 网页

@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.exception_handler(404)
def not_found(request: Request, exc):  # noqa: ANN001
    return JSONResponse({"detail": getattr(exc, "detail", "没有这个地址")}, status_code=404)


app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

# 后台自己的浏览器回归页面。与 /static 分开挂载，所以不需要往 UI 分支的目录里放东西。
if config.SELFTEST_DIR.is_dir():
    app.mount("/selftest", StaticFiles(directory=str(config.SELFTEST_DIR)), name="selftest")
