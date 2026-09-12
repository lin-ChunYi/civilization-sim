"""OBS-01 文明观察台：FastAPI 同时提供网页与 API。

- 读接口：里程碑、模型信息、运行列表、逐年记录。
- 写接口：新建运行、取消、删除。全部服务端校验 + 令牌鉴权 + 限流 + 单并发。
- 模拟在独立子进程里跑，页面用定时轮询看进度，不阻塞。
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
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


def _git_head() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"],
                             cwd=config.REPO_ROOT, capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            return (out.stdout or "").strip()
    except Exception:  # noqa: BLE001
        pass
    return ""


def _service_identity() -> dict:
    explicit = os.environ.get("OBSERVER_BUILD_COMMIT", "").strip()
    ui = os.environ.get("OBSERVER_UI_BUILD", "").strip()
    if explicit:
        ident = {"repo_commit": explicit, "repo_commit_source": "explicit_build"}
    else:
        git = _git_head()
        if git:
            ident = {"repo_commit": git, "repo_commit_source": "git_startup"}
        else:
            ident = {"repo_commit": "unknown", "repo_commit_source": "unknown"}
    ident["api_version"] = config.API_VERSION
    ident["ui_build"] = ui or None
    ident["ui_build_note"] = (
        "optional operator-supplied label; not a hash of bytes currently loaded in the browser"
    )
    return ident


SERVICE_IDENTITY = _service_identity()


def repo_commit() -> str:
    """兼容旧字段：启动时固定的服务身份，不在每次请求时重读磁盘 HEAD。"""
    c = SERVICE_IDENTITY.get("repo_commit") or "unknown"
    if SERVICE_IDENTITY.get("repo_commit_source") == "git_startup" and len(c) == 40:
        return c[:12]
    if c == "unknown":
        return ""
    return c


@app.on_event("startup")
def _startup() -> None:
    store.init_db()
    k = presets.install_presets()
    if k:
        print(f"[observer] 装入 {k} 个预生成案例")
    n = store.recover_interrupted()
    if n:
        print(f"[observer] 启动时把 {n} 个未完成任务标记为中断")
    pending = store.recovery_pending()
    if pending:
        # 没确认停下来就不放槽。这里如实报数，不把它们算进"已标记为中断"。
        print(f"[observer] {pending} 个任务的旧工作进程没能确认停止，记录保持活动状态、"
              f"任务槽继续占着；详见 /api/runs 的 recovery_note")


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
        "service_identity": {
            "api_version": SERVICE_IDENTITY["api_version"],
            "repo_commit": SERVICE_IDENTITY["repo_commit"],
            "repo_commit_source": SERVICE_IDENTITY["repo_commit_source"],
            "ui_build": SERVICE_IDENTITY["ui_build"],
            "ui_build_note": SERVICE_IDENTITY["ui_build_note"],
        },
        "data": {"runs": store.run_count(), "size_mb": round(store.data_size_mb(), 2)},
    }


@app.get("/api/milestones", dependencies=[Depends(require_read)])
def get_milestones():
    return {"statuses": milestones.STATUSES, "items": milestones.MILESTONES,
            "note": milestones.NOTE, "repo_commit": repo_commit()}


@app.get("/api/map", dependencies=[Depends(require_read)])
def get_map():
    return adapter.map_geometry()


_CANCEL_TIMERS: Dict[str, "threading.Timer"] = {}


def arm_cancel_deadline(run_id: str) -> None:
    """用户按下取消之后，安排**一次**到点检查。

    只有这一处会安排它，而且只在用户明确取消之后 —— 没有轮询线程、没有后台监控，
    没人取消就什么都不会跑。到点时调用的还是同一个 `enforce_cancels()`，
    所以判据、身份核验、竞态保护完全一致。
    """
    old = _CANCEL_TIMERS.pop(run_id, None)
    if old is not None:
        old.cancel()

    def fire():
        _CANCEL_TIMERS.pop(run_id, None)
        try:
            store.enforce_cancels()
        except Exception:                                   # noqa: BLE001
            pass          # 到点检查失败不影响服务；下一次页面刷新还会再走一遍
    timer = threading.Timer(config.CANCEL_GRACE_SEC + 0.5, fire)
    timer.daemon = True
    _CANCEL_TIMERS[run_id] = timer
    timer.start()


def settle_slot():
    """每次要看"槽是不是真的被占着"之前先跑一遍。

    顺序固定：**先收尾用户明确请求的取消，再回收没人在算的记录**。
    反过来的话，一条用户取消、进程又刚好没了的运行会被记成"中断"，
    把用户自己按下的取消写成了系统故障。
    """
    store.enforce_cancels()
    store.reap_stale()


@app.get("/api/runs", dependencies=[Depends(require_read)])
def get_runs():
    settle_slot()               # 顺手收尾取消 / 回收死记录，列表才是真实状态
    runs = store.list_runs()
    for r in runs:
        r["years_recorded"] = max(store.year_count(r["run_id"]) - 1, 0)
        r["cancel"] = store.cancel_stage(r)
    return {"runs": runs, "active": store.active_run()}


@app.get("/api/runs/{run_id}", dependencies=[Depends(require_read)])
def get_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, "没有这次运行")
    run["years_recorded"] = max(store.year_count(run_id) - 1, 0)
    run["cancel"] = store.cancel_stage(run)
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
    return _with_event_ids(rec)   # 老记录没有事件 id，按同一套规则补上


def _with_event_ids(rec):
    """老记录（obs-1.5 之前写的）没有事件 id，按同一规则补齐，前端不用分两套逻辑。"""
    for i, e in enumerate(rec.get("events", [])):
        e.setdefault("id", "t%s-%s-%s" % (rec["t"], e.get("type", "event"), i))
        e.setdefault("year", rec["t"])
    return rec


def _engine_supports(engine_name):
    """这台引擎有哪些机制。两个端点共用一份，免得各写一份、口径走偏。"""
    params = config.ENGINES.get(engine_name, {}).get("params", [])
    return {"engine": engine_name,
            "sigma": "sigma_m" in params, "move_mort": "move_mort_m" in params,
            "share": "share_m" in params, "aid": "aid_m" in params,
            "recip": "recip_m" in params}


def _scope(run_id, at_year):
    """确定"截至哪一年"。越界/负数一律 400 说清楚，不静默夹取。"""
    recorded = max(store.year_count(run_id) - 1, 0)
    if at_year is None:
        return {"mode": "full", "at_year": None, "years_recorded": recorded,
                "note": "未指定 at_year：返回全档案（含该年之后发生的事）"}, None
    if at_year < 0 or at_year > recorded:
        raise HTTPException(400, "at_year=%s 越界：这次运行已保存 0..%s 年" % (at_year, recorded))
    return {"mode": "as_of_year", "at_year": at_year, "years_recorded": recorded,
            "note": "只用第 0..%s 年已保存的记录；之后发生的出生/迁移/分裂/消失一律不计入"
                    % at_year}, at_year


def _years(run_id, upto):
    for rec in store.iter_years(run_id):
        if upto is not None and rec["t"] > upto:
            break
        yield _with_event_ids(rec)


def _aid_events(rec):
    return [e for e in rec.get("events", []) if e.get("type") == "aid"]


@app.get("/api/runs/{run_id}/relations", dependencies=[Depends(require_read)])
def get_relations(run_id: str, at_year: Optional[int] = None):
    """**截至某一年**的真实援助往来汇总。

    只把已保存的逐笔援助事件聚合起来：谁给过谁、多少 kcal、几笔、最近哪一年、
    走优先还是普通阶段、其中几笔是回助、以及可追溯的事件 id。
    这里**没有**"盟友""国家""联盟"这类东西 —— 只有实际发生过的食物转移。
    `recip.changed` 是"格×年"的诊断计数，属于那一格那一年，**不归给任何一条边**，
    所以它只作为运行级读数放在 diagnostics 里，也不能用 repay 笔数去替代它。
    """
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, "没有这次运行")
    eng = run.get("engine") or config.DEFAULT_ENGINE
    scope, upto = _scope(run_id, at_year)
    edges = {}
    names, last_seen, alive_cells = {}, {}, {}
    recip_changed = 0
    last_rec_t = None
    for rec in _years(run_id, upto):
        last_rec_t = rec["t"]
        for b in rec.get("bands", []):
            names[b["id"]] = b.get("name", b["id"])
            last_seen[b["id"]] = rec["t"]
        alive_cells = {b["id"]: b.get("cell") for b in rec.get("bands", [])}
        recip_changed += (rec.get("recip") or {}).get("changed", 0) or 0
        for e in _aid_events(rec):
            d, r = str(e.get("donor")), str(e.get("receiver"))
            key = d + "->" + r
            edge = edges.setdefault(key, {
                "donor": d, "receiver": r, "kcal": 0, "transfers": 0,
                "last_year": None, "last_event_id": None,
                "phase_counts": {"recip": 0, "normal": 0}, "repay_transfers": 0,
                "event_ids": []})
            edge["kcal"] += int(e.get("kcal") or 0)
            edge["transfers"] += 1
            edge["last_year"] = e.get("year", rec["t"])
            edge["last_event_id"] = e.get("id")
            phase = e.get("phase") or "normal"
            edge["phase_counts"][phase] = edge["phase_counts"].get(phase, 0) + 1
            if e.get("repay"):
                edge["repay_transfers"] += 1
            edge["event_ids"].append(e.get("id"))
    node_ids = set(names) | {x for k in edges for x in (edges[k]["donor"], edges[k]["receiver"])}
    nodes = [{"id": nid, "name": names.get(nid, nid),
              "alive_at_year": nid in alive_cells,
              "cell": alive_cells.get(nid),
              "last_seen_year": last_seen.get(nid)}
             for nid in sorted(node_ids)]
    return {
        "run_id": run_id, "history_scope": scope,
        "as_of_record_year": last_rec_t,
        "nodes": nodes,
        "edges": sorted(edges.values(), key=lambda e: (-e["kcal"], e["donor"], e["receiver"])),
        "totals": {"nodes": len(nodes), "edges": len(edges),
                   "transfers": sum(e["transfers"] for e in edges.values()),
                   "kcal": sum(e["kcal"] for e in edges.values())},
        "diagnostics": {"recip_changed_cellyears": recip_changed,
                        "note": "recip.changed 是格×年的诊断，不属于任何一条边；"
                                "也不要用 repay_transfers 代替它 —— 回助在 RECIP_M=0 时"
                                "同样会发生，那是碰巧"},
        "engine_supports": _engine_supports(eng),
        "source": "只聚合本次运行已保存的逐笔援助事件（模型日志 st['aid_log']）；"
                  "不含任何推断出来的关系、称谓或立场。"
                  "engine_supports.aid=false 时边集为空是能力事实，不是缺年。",
    }


@app.get("/api/runs/{run_id}/band/{band_id}", dependencies=[Depends(require_read)])
def get_band(run_id: str, band_id: str, at_year: Optional[int] = None):
    """某个群体的卷宗。全部来自已保存的逐年记录与模型日志，不做任何推测。

    带 `at_year=N` 时只用第 0..N 年的记录：那一年之后才发生的迁移、分裂、消失、
    援助往来**一概不出现**（回放到第 124 年时，档案里不该已经写着第 125 年的迁移）。
    不带参数则是全档案，`history_scope.mode` 会说清楚是哪一种。
    """
    if not store.get_run(run_id):
        raise HTTPException(404, "没有这次运行")
    scope, upto = _scope(run_id, at_year)
    traj, sizes = [], []
    name = band_id
    first_seen = last_seen = None
    parent = born_at = extinct_at = None
    children = []
    aid_given = {"kcal": 0, "transfers": 0, "events": []}
    aid_received = {"kcal": 0, "transfers": 0, "events": []}
    aid_memory = None
    alive_at = False
    last_state = None
    for rec in _years(run_id, upto):
        t = rec["t"]
        present = False
        for b in rec["bands"]:
            if b["id"] == band_id:
                present = True
                name = b["name"]
                if first_seen is None:
                    first_seen = t
                last_seen = t
                sizes.append([t, b["size"], b["store"]])
                if not traj or traj[-1][1] != b["cell"]:
                    traj.append([t, b["cell"]])
                aid_memory = b.get("aid_memory")
                last_state = {"year": t, "cell": b["cell"], "size": b["size"],
                              "store": b["store"]}
        alive_at = present
        for e in rec["events"]:
            kind = e.get("type")
            if kind == "split" and e.get("band") == band_id:
                parent, born_at = e.get("parent"), t
            elif kind == "split" and e.get("parent") == band_id:
                children.append([t, e.get("band")])
            elif kind == "extinct" and e.get("band") == band_id:
                extinct_at = t
            elif kind == "aid":
                if str(e.get("donor")) == band_id:
                    aid_given["kcal"] += int(e.get("kcal") or 0)
                    aid_given["transfers"] += 1
                    aid_given["events"].append(
                        {"id": e.get("id"), "year": e.get("year", t),
                         "receiver": str(e.get("receiver")), "kcal": e.get("kcal"),
                         "phase": e.get("phase"), "repay": bool(e.get("repay"))})
                elif str(e.get("receiver")) == band_id:
                    aid_received["kcal"] += int(e.get("kcal") or 0)
                    aid_received["transfers"] += 1
                    aid_received["events"].append(
                        {"id": e.get("id"), "year": e.get("year", t),
                         "donor": str(e.get("donor")), "kcal": e.get("kcal"),
                         "phase": e.get("phase"), "repay": bool(e.get("repay"))})
    if first_seen is None:
        raise HTTPException(404, "截至该年份的记录里没有这个群体"
                            if upto is not None else "这次运行里没有这个群体")
    # aid_memory 里的 last_year 是**引擎内部 tick**，比记录年份小 1，直接显示就会像
    # "第 83 年的援助写成第 82 年"。展示年份一律从**本次范围内真实的援助事件**推出来：
    # 老记录（obs-1.6 之前写的）没有这几个字段，这里补齐；新记录则用同一批事件复核一遍，
    # 保证截到第 N 年时不会指向第 N 年之后的事件。
    if isinstance(aid_memory, dict):
        last_from = {}
        for ev in aid_received["events"]:
            last_from[ev["donor"]] = ev
        fixed = {}
        for donor, mem in aid_memory.items():
            mem = dict(mem) if isinstance(mem, dict) else {"raw": mem}
            ev = last_from.get(str(donor))
            if ev:
                mem["last_year_display"] = ev["year"]
                mem["last_event_id"] = ev["id"]
                mem["display_source"] = "本次运行的援助事件 " + str(ev["id"])
            else:
                mem["last_year_display"] = None
                mem["last_event_id"] = None
                mem["display_source"] = (
                    "未记录：截至第 %s 年的已保存记录里没有 %s 给本群体的援助事件"
                    % (upto if upto is not None else last_seen, donor))
            fixed[str(donor)] = mem
        aid_memory = fixed
    return {"id": band_id, "name": name, "history_scope": scope,
            "first_seen": first_seen, "last_seen": last_seen,
            "alive_at_year": alive_at, "state_at_year": last_state,
            "origin": ("由 " + parent + " 分裂而来" if parent else
                       ("开局的初始群体" if first_seen == 0 else "未记录")),
            "parent": parent, "born_at": born_at, "children": children,
            "extinct_at": extinct_at, "trajectory": traj, "sizes": sizes,
            "aid_given": aid_given, "aid_received": aid_received,
            "aid_memory": aid_memory,
            # 与 /relations 同一口径：没有援助机制的引擎，援助字段为空是**能力事实**，
            # 不是缺数据，界面不要显示成"0 笔援助"。
            "engine_supports": _engine_supports(
                (store.get_run(run_id) or {}).get("engine") or config.DEFAULT_ENGINE),
            "source": "全部来自本次运行已保存的逐年记录与模型日志；"
                      "群体层的出生/死亡分项未记录，账本只记全局分项。"
                      "aid_memory 里的 last_year 是引擎内部 tick，"
                      "要显示请用 last_year_display / last_event_id。"}


# ---------------------------------------------------------------- 写接口

class NewRun(BaseModel):
    seed: StrictInt = Field(..., description="随机种子")
    years: StrictInt = Field(..., description="模拟年数")
    sigma_m: StrictInt = Field(0, description="SIGMA_M：资源再生年际波动强度，千分之一")
    move_mort_m: StrictInt = Field(0, description="MOVE_MORT_M：迁移死亡强度，千分之一")
    arm: StrictStr = Field("memory", description="信息条件（对照臂）")
    label: StrictStr = Field("", description="备注")
    engine: StrictStr = Field(config.DEFAULT_ENGINE, description="模拟引擎：exp01–exp06")
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
    if "sigma_m" in params:
        if not (v3.SIGMA_M_MIN <= body.sigma_m <= v3.SIGMA_M_MAX):
            raise HTTPException(400, f"SIGMA_M 越界，合法范围 [{v3.SIGMA_M_MIN}, {v3.SIGMA_M_MAX}]")
    elif body.sigma_m != 0:
        raise HTTPException(400, f"引擎 {body.engine} 没有 SIGMA_M 这个参数，"
                                 f"不要把 EXP-03 的波动参数套到 {body.engine} 上")
    if "move_mort_m" in params:
        if not (v3.MOVE_MORT_M_MIN <= body.move_mort_m <= v3.MOVE_MORT_M_MAX):
            raise HTTPException(
                400, f"MOVE_MORT_M 越界，合法范围 [{v3.MOVE_MORT_M_MIN}, {v3.MOVE_MORT_M_MAX}]")
    elif body.move_mort_m != 0:
        raise HTTPException(400, f"引擎 {body.engine} 没有 MOVE_MORT_M 这个参数，"
                                 f"不要把 EXP-03 的迁移死亡参数套到 {body.engine} 上")
    if body.arm not in config.ARMS:
        raise HTTPException(400, f"arm 只能是 {list(config.ARMS)} 之一")
    if len(body.label) > 60:
        raise HTTPException(400, "备注最长 60 字")


@app.post("/api/runs", dependencies=[Depends(require_write)])
def post_run(body: NewRun):
    _validate(body)
    settle_slot()                 # 先收尾取消、再回收死记录，然后才占槽
    reaped = []                   # 卡住的取消不该把唯一的槽永久占死
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
    """用户明确请求取消。**有界收尾**，不会一直占着唯一的任务槽。

    正常的工作进程会在当前这一年算完后自己停下（那是干净的收尾，记录也最完整）；
    如果它卡在某一步里读不到取消标志，协作窗口用完后会被停止 —— 前提是先核验过
    那个进程号确实是这次运行的工作进程。身份查不到就一个信号都不发。
    """
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(404, "没有这次运行")
    if run["status"] not in ("queued", "running"):
        raise HTTPException(409, f"该运行状态为 {run['status']}，无需取消")
    store.request_cancel(run_id)
    store.enforce_cancels()           # 进程已经不在 / 协作窗口早就用完了，这一下就收尾
    after = store.get_run(run_id) or run
    stage = store.cancel_stage(after)
    if after["status"] in store.TERMINAL:
        return {"ok": True, "run_id": run_id, "status": after["status"],
                "cancel": stage, "note": after.get("cancel_note") or after.get("error") or
                "已停止，任务槽已释放。"}
    # 还在跑：安排一次**一次性**的到点检查，让收尾时间不依赖页面刷不刷新。
    arm_cancel_deadline(run_id)
    # enforce_cancels 已经按实际探测/停止结果写好了准确说明（协作窗口 / 身份未知 /
    # 信号发了但没确认停下）。**不要用一句乐观的通稿把它盖掉。**
    note = (after.get("cancel_note") or "").strip()
    if not note:
        note = ("已请求取消：工作进程会在当前这一年算完后自己停下；"
                "若它卡住，最多 %.0f 秒后会被强制停止。已完整保存的年份都留着。"
                % config.CANCEL_GRACE_SEC)
        store.set_cancel_note(run_id, note)
    return {"ok": True, "run_id": run_id, "status": after["status"],
            "cancel": dict(stage, note=note), "note": note}


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
