"""持久化：SQLite 存运行台账，每次运行一个 years.jsonl 存逐年记录。

刻意选最小可行方案（单用户、小规模）：不引入 Redis、队列、ORM 或数据库平台。
服务重启后已完成记录仍在；重启时把没跑完的任务标为“中断”，不假装能续跑。
"""
from __future__ import annotations

import json
import os
import signal
import sqlite3
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id        TEXT PRIMARY KEY,
  label         TEXT NOT NULL DEFAULT '',
  kind          TEXT NOT NULL DEFAULT 'user',      -- user | preset
  status        TEXT NOT NULL,                      -- queued running done failed interrupted canceled
  created_at    REAL NOT NULL,
  started_at    REAL,
  finished_at   REAL,
  seed          INTEGER NOT NULL,
  years         INTEGER NOT NULL,
  sigma_m       INTEGER NOT NULL,
  move_mort_m   INTEGER NOT NULL,
  share_m       INTEGER NOT NULL DEFAULT 0,
  aid_m         INTEGER NOT NULL DEFAULT 0,
  recip_m       INTEGER NOT NULL DEFAULT 0,
  engine        TEXT    NOT NULL DEFAULT 'exp03',
  arm           TEXT NOT NULL,
  years_done    INTEGER NOT NULL DEFAULT 0,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  cancel_requested_at REAL,                           -- 用户按下取消的时刻（有界收尾的起算点）
  cancel_note   TEXT NOT NULL DEFAULT '',             -- 取消收尾进行到哪一步（人话，给页面看）
  cancel_last_attempt_at REAL,                        -- 上一次真的发过停止信号的时刻（节流用）
  recovery_note TEXT NOT NULL DEFAULT '',             -- 重启恢复没能确认停止时的待处理说明
  engine_sha256 TEXT NOT NULL DEFAULT '',
  engine_path   TEXT NOT NULL DEFAULT '',
  baseline_commit TEXT NOT NULL DEFAULT '',
  repo_commit   TEXT NOT NULL DEFAULT '',
  api_version   TEXT NOT NULL DEFAULT '',             -- 产出这条记录时服务的契约版本
  -- 续演血缘（C_CONT_01）。普通运行 root=自己、parent 为空、from_year=0。
  root_run_id   TEXT NOT NULL DEFAULT '',
  parent_run_id TEXT NOT NULL DEFAULT '',
  from_year     INTEGER NOT NULL DEFAULT 0,            -- 这一段从第几年开始算
  additional_years INTEGER NOT NULL DEFAULT 0,         -- 这一段要新增几年
  completed_steps  INTEGER NOT NULL DEFAULT 0,         -- **这一段**实际算完几步
  history_ready INTEGER NOT NULL DEFAULT 0,            -- 完整历史前缀是否已发布
  model_run_id  TEXT NOT NULL DEFAULT '',
  full_digest   TEXT NOT NULL DEFAULT '',
  error         TEXT NOT NULL DEFAULT '',
  pid           INTEGER
);
"""

_STATUS_ACTIVE = ("queued", "running")

# 合法的状态转换。**终态（done/failed/canceled/interrupted）不再变**——
# 这条是围栏的地基：一旦判定结束，任何迟到的写入都改不回去。
TRANSITIONS = {
    "queued": {"running", "canceled", "interrupted", "failed"},
    "running": {"done", "failed", "canceled", "interrupted"},
    "done": set(), "failed": set(), "canceled": set(), "interrupted": set(),
}
TERMINAL = {"done", "failed", "canceled", "interrupted"}


def sources_for(new_status: str) -> List[str]:
    """能合法转到 new_status 的来源状态。"""
    return sorted(src for src, dsts in TRANSITIONS.items() if new_status in dsts)


def connect() -> sqlite3.Connection:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


# 旧库升级：只补列，不改已有列，不动已有数据。
MIGRATIONS = (("share_m", "INTEGER NOT NULL DEFAULT 0"),
              ("engine", "TEXT NOT NULL DEFAULT 'exp03'"),
              ("aid_m", "INTEGER NOT NULL DEFAULT 0"),
              ("recip_m", "INTEGER NOT NULL DEFAULT 0"),
              ("cancel_requested_at", "REAL"),
              ("cancel_note", "TEXT NOT NULL DEFAULT ''"),
              ("cancel_last_attempt_at", "REAL"),
              ("recovery_note", "TEXT NOT NULL DEFAULT ''"),
              ("api_version", "TEXT NOT NULL DEFAULT ''"),
              ("root_run_id", "TEXT NOT NULL DEFAULT ''"),
              ("parent_run_id", "TEXT NOT NULL DEFAULT ''"),
              ("from_year", "INTEGER NOT NULL DEFAULT 0"),
              ("additional_years", "INTEGER NOT NULL DEFAULT 0"),
              ("completed_steps", "INTEGER NOT NULL DEFAULT 0"),
              ("history_ready", "INTEGER NOT NULL DEFAULT 0"))

# 续演请求的幂等映射。**删掉子运行也不能让同一个 request_id 重放成新任务**，
# 所以这张表独立于 runs，不跟着级联删除。
CONTINUATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS continuations (
  request_id    TEXT PRIMARY KEY,
  parent_run_id TEXT NOT NULL,
  additional_years INTEGER NOT NULL,
  child_run_id  TEXT NOT NULL,
  created_at    REAL NOT NULL
);
"""


def init_db() -> None:
    config.RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.executescript(CONTINUATION_SCHEMA)
        have = {r["name"] for r in conn.execute("PRAGMA table_info(runs)").fetchall()}
        for col, decl in MIGRATIONS:
            if col not in have:
                conn.execute(f"ALTER TABLE runs ADD COLUMN {col} {decl}")


def run_dir(run_id: str) -> Path:
    return config.RUNS_DIR / run_id


def checkpoint_path(run_id: str) -> Path:
    """检查点只放在服务自己的数据目录里，**不接受任意路径**。"""
    return run_dir(run_id) / config.CHECKPOINT_NAME


def years_path(run_id: str) -> Path:
    return run_dir(run_id) / "years.jsonl"


def meta_path(run_id: str) -> Path:
    return run_dir(run_id) / "meta.json"


# ---------------------------------------------------------------- 写

def claim_slot(*, seed: int, years: int, sigma_m: int, move_mort_m: int, arm: str,
               label: str = "", kind: str = "user", engine: Dict[str, Any],
               repo_commit: str = "", api_version: str = "", share_m: int = 0, aid_m: int = 0,
               recip_m: int = 0, engine_name: str = None) -> Optional[str]:
    """**原子**地占用唯一的任务槽并建记录。

    “检查空闲 + 占槽 + 建记录”必须在同一个事务里，否则两个同时到达的请求会双双通过检查。
    用 SQLite 的 BEGIN IMMEDIATE 拿写锁：两个并发事务里只有一个能先提交，
    后一个再看到的就是“已有任务在跑”。单实例够用，不需要任务平台。
    """
    run_id = uuid.uuid4().hex[:12]
    conn = sqlite3.connect(config.DB_PATH, timeout=20.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        busy = conn.execute("SELECT run_id FROM runs WHERE status IN (?,?) LIMIT 1",
                            _STATUS_ACTIVE).fetchone()
        if busy:
            conn.execute("ROLLBACK")
            return None
        conn.execute(
            "INSERT INTO runs (run_id,label,kind,status,created_at,seed,years,sigma_m,"
            "move_mort_m,share_m,aid_m,recip_m,engine,arm,engine_sha256,engine_path,"
            "baseline_commit,repo_commit,api_version,"
            "root_run_id,parent_run_id,from_year,additional_years) "
            "VALUES (?,?,?,'queued',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'',0,?)",
            (run_id, label, kind, time.time(), seed, years, sigma_m, move_mort_m,
             share_m, aid_m, recip_m, engine_name or config.DEFAULT_ENGINE, arm,
             engine["engine_sha256"], engine["engine_path"], engine["baseline_commit"],
             repo_commit, api_version, run_id, years))
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise
    finally:
        conn.close()
    run_dir(run_id).mkdir(parents=True, exist_ok=True)
    return run_id


def claim_continuation(parent: Dict[str, Any], *, request_id: str, additional_years: int,
                       target_years: int, from_year: int, repo_commit: str = "",
                       api_version: str = "", label: str = "") -> Dict[str, Any]:
    """**占槽 + 建子运行 + 登记 request_id，同一个事务里做完。**

    返回 `{"run_id", "reused"}`；`reused=True` 表示这是同一个 request_id 的重试，
    直接把原来那条子运行还回去，绝不重复启动。

    同一个 request_id 配了不同的父运行或不同的新增年数 -> 抛 `IdempotencyConflict`。
    槽被占 -> 返回 None（调用方按 409 处理）。
    """
    init_db()
    now = time.time()
    child_id = uuid.uuid4().hex[:12]
    conn = sqlite3.connect(config.DB_PATH, timeout=20.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("BEGIN IMMEDIATE")
        prior = conn.execute(
            "SELECT * FROM continuations WHERE request_id=?", (request_id,)).fetchone()
        if prior is not None:
            conn.execute("ROLLBACK")
            if prior["parent_run_id"] != parent["run_id"] or \
                    int(prior["additional_years"]) != int(additional_years):
                raise IdempotencyConflict(
                    "同一个 request_id 之前用的是父运行 %s / 新增 %d 年，这次不一样"
                    % (prior["parent_run_id"], prior["additional_years"]))
            return {"run_id": prior["child_run_id"], "reused": True}
        busy = conn.execute("SELECT run_id FROM runs WHERE status IN (?,?) LIMIT 1",
                            _STATUS_ACTIVE).fetchone()
        if busy:
            conn.execute("ROLLBACK")
            return None
        conn.execute(
            "INSERT INTO runs (run_id,label,kind,status,created_at,seed,years,sigma_m,"
            "move_mort_m,share_m,aid_m,recip_m,engine,arm,engine_sha256,engine_path,"
            "baseline_commit,repo_commit,api_version,"
            "root_run_id,parent_run_id,from_year,additional_years,history_ready) "
            "VALUES (?,?,'user','queued',?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
            (child_id, label or ("续演自 %s（第 %d 年起）" % (parent["run_id"], from_year)),
             now, parent["seed"], target_years, parent["sigma_m"], parent["move_mort_m"],
             parent["share_m"], parent["aid_m"], parent["recip_m"], parent["engine"],
             parent["arm"], parent["engine_sha256"], parent["engine_path"],
             parent["baseline_commit"], repo_commit, api_version,
             parent["root_run_id"] or parent["run_id"], parent["run_id"],
             from_year, additional_years))
        conn.execute("INSERT INTO continuations (request_id,parent_run_id,additional_years,"
                     "child_run_id,created_at) VALUES (?,?,?,?,?)",
                     (request_id, parent["run_id"], int(additional_years), child_id, now))
        conn.execute("COMMIT")
    except IdempotencyConflict:
        raise
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except Exception:                                            # noqa: BLE001
            pass
        raise
    finally:
        conn.close()
    run_dir(child_id).mkdir(parents=True, exist_ok=True)
    return {"run_id": child_id, "reused": False}


def dependents(parent_run_id: str) -> List[Dict[str, Any]]:
    """还在排队 / 正在跑、并且依赖这个父运行的子运行。"""
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT run_id,status FROM runs WHERE parent_run_id=? AND status IN (?,?)",
            (parent_run_id, *_STATUS_ACTIVE)).fetchall()]


def mark_history_ready(run_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE runs SET history_ready=1 WHERE run_id=?", (run_id,))


def set_segment_progress(run_id: str, pid: int, completed_steps: int) -> bool:
    """**这一段**算完了几步。与 years_done（全局进度）分开记，父历史不冒充本段进度。"""
    with connect() as conn:
        cur = conn.execute(
            "UPDATE runs SET completed_steps=? WHERE run_id=? AND status='running' AND pid=?",
            (int(completed_steps), run_id, pid))
        return cur.rowcount == 1


def set_pid(run_id: str, pid: int) -> None:
    """只写 pid，**不碰 status** —— 否则会把工作进程已经推进到的 running/done 打回 queued。"""
    with connect() as conn:
        conn.execute("UPDATE runs SET pid=? WHERE run_id=?", (pid, run_id))


def drop_run_row(run_id: str) -> None:
    """占槽后启动失败时把槽还回去。"""
    with connect() as conn:
        conn.execute("DELETE FROM runs WHERE run_id=?", (run_id,))


class IdempotencyConflict(Exception):
    """同一个 request_id 配了不同的请求内容。**不能悄悄当成新任务。**"""


_UNSET = object()


def transition(run_id: str, new_status: str, *, allow_from: Optional[List[str]] = None,
               expect_pid: Any = _UNSET, **fields) -> bool:
    """按状态转换表改状态。来源状态不合法就什么都不写，返回 False。

    `expect_pid` 给回收路径用：把“检查时看到的 pid”一起写进 WHERE，
    如果这中间工作进程刚启动并改写了 pid（或状态），这次写入就落空 ——
    宁可这一轮不回收，也不能误停一个刚起来的任务。

    生产路径一律走这里；`force_status()` 只给测试用。
    """
    srcs = list(allow_from) if allow_from else sources_for(new_status)
    if not srcs:
        return False
    cols = ", ".join(f"{k}=?" for k in fields)
    holes = ",".join("?" for _ in srcs)
    sql = ("UPDATE runs SET status=?" + (", " + cols if cols else "") +
           f" WHERE run_id=? AND status IN ({holes})")
    args = [new_status, *fields.values(), run_id, *srcs]
    if expect_pid is not _UNSET:
        sql += " AND pid IS ?"                  # IS 能正确匹配 NULL
        args.append(expect_pid)
    with connect() as conn:
        cur = conn.execute(sql, args)
        return cur.rowcount == 1


def force_status(run_id: str, status: str, **fields) -> None:
    """不检查转换表的写入。**只用于测试构造前提**，生产代码不要调用。"""
    cols = ", ".join(f"{k}=?" for k in fields)
    sql = "UPDATE runs SET status=?" + (", " + cols if cols else "") + " WHERE run_id=?"
    with connect() as conn:
        conn.execute(sql, (status, *fields.values(), run_id))


def update_progress(run_id: str, years_done: int) -> None:
    with connect() as conn:
        conn.execute("UPDATE runs SET years_done=? WHERE run_id=?", (years_done, run_id))


# ---- 工作进程专用：所有写入都带围栏条件，被判为中断/取消后就再也改不回去 ----

def worker_begin(run_id: str, pid: int) -> bool:
    """queued -> running。只有当这条记录仍是 queued 且 pid 是自己时才成立。"""
    with connect() as conn:
        cur = conn.execute(
            "UPDATE runs SET status='running', started_at=?, pid=? "
            "WHERE run_id=? AND status='queued' AND (pid IS NULL OR pid=?)",
            (time.time(), pid, run_id, pid))
        return cur.rowcount == 1


def worker_state(run_id: str, pid: int) -> Optional[sqlite3.Row]:
    """工作进程每个 tick 查一次：状态、pid、取消标志。返回 None 表示这条记录没了。"""
    with connect() as conn:
        return conn.execute(
            "SELECT status, pid, cancel_requested FROM runs WHERE run_id=?",
            (run_id,)).fetchone()


def worker_progress(run_id: str, pid: int, years_done: int) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE runs SET years_done=? WHERE run_id=? AND status='running' AND pid=?",
            (years_done, run_id, pid))
        return cur.rowcount == 1


def worker_finish(run_id: str, pid: int, status: str, **fields) -> bool:
    """running -> done/failed/canceled。**不能**把已经被判定为 interrupted 的记录改回去。"""
    cols = ", ".join(f"{k}=?" for k in fields)
    sql = ("UPDATE runs SET status=?" + (", " + cols if cols else "") +
           " WHERE run_id=? AND status='running' AND pid=?")
    with connect() as conn:
        cur = conn.execute(sql, (status, *fields.values(), run_id, pid))
        return cur.rowcount == 1


def request_cancel(run_id: str) -> Optional[float]:
    """记下"用户明确要求取消"以及**第一次**要求的时刻，返回那个时刻。

    时刻只记一次：再点一次取消不会把倒计时推后，否则反复点击等于永远不收尾。
    只对还在活动的记录生效；终态记录一个字都不改。
    """
    now = time.time()
    with connect() as conn:
        conn.execute(
            "UPDATE runs SET cancel_requested=1, "
            "cancel_requested_at=COALESCE(cancel_requested_at, ?) "
            "WHERE run_id=? AND status IN (?,?)", (now, run_id, *_STATUS_ACTIVE))
        row = conn.execute("SELECT cancel_requested_at FROM runs WHERE run_id=?",
                           (run_id,)).fetchone()
    return row["cancel_requested_at"] if row else None


def mark_cancel_attempt(run_id: str, when: Optional[float] = None) -> None:
    """记下"这一轮真的发过停止信号"。只用于节流，不参与任何状态判断。"""
    with connect() as conn:
        conn.execute("UPDATE runs SET cancel_last_attempt_at=? WHERE run_id=?",
                     (time.time() if when is None else when, run_id))


def set_recovery_note(run_id: str, note: str) -> None:
    """重启恢复没能确认旧进程停止时的说明。**只写说明，不碰 status**。"""
    with connect() as conn:
        conn.execute("UPDATE runs SET recovery_note=? WHERE run_id=? AND status IN (?,?)",
                     (note, run_id, *_STATUS_ACTIVE))


def recovery_pending() -> int:
    """还有几条记录卡在"旧工作进程没能确认停止"上（仍占着任务槽）。"""
    init_db()
    with connect() as conn:
        return int(conn.execute(
            "SELECT COUNT(*) c FROM runs WHERE status IN (?,?) AND recovery_note<>''",
            _STATUS_ACTIVE).fetchone()["c"])


def set_cancel_note(run_id: str, note: str) -> None:
    """只写给人看的收尾说明，**不碰 status**。"""
    with connect() as conn:
        conn.execute("UPDATE runs SET cancel_note=? WHERE run_id=? AND status IN (?,?)",
                     (note, run_id, *_STATUS_ACTIVE))


def cancel_requested(run_id: str) -> bool:
    with connect() as conn:
        row = conn.execute("SELECT cancel_requested FROM runs WHERE run_id=?",
                           (run_id,)).fetchone()
    return bool(row and row["cancel_requested"])


def write_meta(run_id: str, meta: Dict[str, Any]) -> None:
    """先写临时文件再 os.replace —— 读到的要么是上一版，要么是完整的新版，
    不会出现“半个 meta.json 把接口打成 500”。"""
    dst = meta_path(run_id)
    tmp = dst.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, dst)


def append_year(fh, record: Dict[str, Any]) -> None:
    fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    fh.flush()
    os.fsync(fh.fileno())


# ---------------------------------------------------------------- 读

def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
    return dict(row) if row else None


def list_runs(limit: int = 100) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?",
                            (limit,)).fetchall()
    return [dict(r) for r in rows]


def active_run() -> Optional[Dict[str, Any]]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM runs WHERE status IN (?,?) ORDER BY created_at LIMIT 1",
            _STATUS_ACTIVE).fetchone()
    return dict(row) if row else None


def run_count() -> int:
    with connect() as conn:
        return int(conn.execute("SELECT COUNT(*) c FROM runs").fetchone()["c"])


def data_size_mb() -> float:
    total = 0
    for p in config.DATA_DIR.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total / (1024 * 1024)


def read_meta(run_id: str) -> Optional[Dict[str, Any]]:
    """读不到或读到残缺的一律返回 None（接口给出 meta: null，前端自行补取）。
    绝不让一个写坏的文件把整条运行的接口打掉。"""
    p = meta_path(run_id)
    if not p.exists():
        return None
    try:
        meta = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    return meta if isinstance(meta, dict) else None


_CACHE: Dict[str, Any] = {}

# 一条“完整记录”必须有的字段。缺一个就不算写完，不计入已完成年份。
REQUIRED_YEAR_KEYS = frozenset(("t", "stock", "bands", "cum", "year", "agg",
                                "integrity", "events"))


def _lines(run_id: str) -> List[str]:
    """逐年记录的进程内缓存。回放只读文件，不触发任何计算。

    **只承认写完整的行**：末尾那条半成品（进程正在写，或异常退出留下的）一律不计入
    已完成年份，也不会让 series / year 接口炸掉。两条判据都要满足：
      1. 这一行有换行符结尾 —— 按 "\n" 切开后丢掉最后一段即可：
         文件以换行结束时最后一段是空串，没结束时最后一段正是那条半成品；
      2. 这一行能被 json 解析，t 等于它的行号，且该有的字段一个不缺。
         任一条不满足就在此截断 —— 下游（series / year / 前端）因此可以放心假定记录是完整的。
    """
    p = years_path(run_id)
    if not p.exists():
        return []
    stt = p.stat()
    key = (stt.st_mtime_ns, stt.st_size)
    hit = _CACHE.get(run_id)
    if hit and hit[0] == key:
        return hit[1]
    raw = p.read_text(encoding="utf-8", errors="replace")
    out: List[str] = []
    for ln in raw.split("\n")[:-1]:
        ln = ln.rstrip("\r")
        if not ln:
            break
        try:
            rec = json.loads(ln)
        except ValueError:
            break
        if not isinstance(rec, dict) or rec.get("t") != len(out):
            break
        if not REQUIRED_YEAR_KEYS <= rec.keys():
            break
        out.append(ln)
    _CACHE[run_id] = (key, out)
    return out


def year_count(run_id: str) -> int:
    return len(_lines(run_id))


def read_year(run_id: str, t: int) -> Optional[Dict[str, Any]]:
    lines = _lines(run_id)
    if t < 0 or t >= len(lines):
        return None
    return json.loads(lines[t])


def iter_years(run_id: str):
    for ln in _lines(run_id):
        yield json.loads(ln)


def read_series(run_id: str) -> List[Dict[str, Any]]:
    """整条时间序列的轻量版：只给曲线与时间轴用，不含地图与群体明细。"""
    out = []
    for ln in _lines(run_id):
        r = json.loads(ln)
        out.append({"t": r["t"], "agg": r["agg"], "year": r["year"],
                    "cum": r["cum"], "integrity": r["integrity"],
                    "events": len(r["events"])})
    return out


# 工作进程探测的三种结果。**“查不到”不等于“死了”**：
# ps 超时、权限不足、系统调用出错都属于未知；未知一律不回收，宁可让槽多占一会儿。
WORKER_ALIVE, WORKER_GONE, WORKER_UNKNOWN = "alive", "gone", "unknown"


def probe_worker(pid: Optional[int], run_id: str) -> str:
    """判断 pid 是不是这次运行还活着的工作进程。返回 alive / gone / unknown。"""
    if not pid:
        return WORKER_GONE                      # 从来没登记过 pid，谈不上有进程
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return WORKER_GONE                      # 确认不存在
    except PermissionError:
        return WORKER_UNKNOWN                   # 进程在，但不归我们管：不确认，也不回收
    except (OSError, ValueError, TypeError):
        return WORKER_UNKNOWN
    try:
        r = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                           capture_output=True, text=True, timeout=5)
    except Exception:                           # noqa: BLE001  超时 / ps 不可用 / 被限制
        return WORKER_UNKNOWN
    if r.returncode != 0:                       # ps 说没这个进程，与 kill(0) 矛盾，再确认一次
        try:
            os.kill(int(pid), 0)
        except ProcessLookupError:
            return WORKER_GONE
        except Exception:                       # noqa: BLE001
            return WORKER_UNKNOWN
        return WORKER_UNKNOWN
    out = r.stdout or ""
    if "observer.worker" in out and run_id in out:
        return WORKER_ALIVE
    return WORKER_GONE                          # pid 被别的进程复用了


def _is_our_worker(pid: Optional[int], run_id: str) -> bool:
    """只有“确认活着”才算数。未知既不算活也不算死，调用方必须自己区分。"""
    return probe_worker(pid, run_id) == WORKER_ALIVE


def stop_worker(pid: int, run_id: str, grace: float = 3.0) -> str:
    """先 SIGTERM，必要时再 SIGKILL，**并核实结果**。返回 gone / alive / unknown。

    返回值就是"到底停没停下来"，调用方必须自己区分 —— 这里**没有**布尔"成功"：

      * `gone`    —— 已确认这个 pid 不再是本次运行的工作进程，可以放心放槽；
      * `alive`   —— 信号发了，它还在；
      * `unknown` —— 查不到（`ps` 超时 / 权限不足 / 发信号本身报错）。
        **未知不等于停下来了**：旧工作进程若还活着，仍会往 `years.jsonl` 里追加，
        而数据库围栏只管数据库，管不住文件写入。

    每次发信号之前都**重新核验一次身份**：pid 随时可能被系统回收并复用，
    拿几秒钟前的判断去 SIGKILL 是在赌别人的进程。
    """
    probe = probe_worker(pid, run_id)
    if probe != WORKER_ALIVE:
        return probe                       # 已经不是我们的进程：gone 不用发信号，unknown 更不发
    try:
        os.kill(int(pid), signal.SIGTERM)
    except ProcessLookupError:
        return probe_worker(pid, run_id)   # 刚好在这一瞬间自己退了，再确认一次
    except OSError:
        return WORKER_UNKNOWN              # 信号发不出去：它现在什么状态我们并不知道
    deadline = time.time() + max(0.0, grace)
    while True:
        state = probe_worker(pid, run_id)
        if state != WORKER_ALIVE:
            return state                   # gone 才是停下来了；unknown 原样交给调用方判断
        if time.time() >= deadline:
            break
        time.sleep(0.1)
    if probe_worker(pid, run_id) != WORKER_ALIVE:
        return probe_worker(pid, run_id)   # 升级前再核验一次身份，别对刚被复用的 pid 下手
    try:
        os.kill(int(pid), signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        return WORKER_UNKNOWN              # KILL 都发不出去，绝不报告"已停止"
    for _ in range(20):                    # KILL 之后同样要**核实**，不假定它一定死
        time.sleep(0.05)
        state = probe_worker(pid, run_id)
        if state != WORKER_ALIVE:
            return state
    return WORKER_ALIVE                    # 连 SIGKILL 都没能让它消失：如实上报


def reap_stale() -> List[Dict[str, Any]]:
    """回收“占着任务槽但其实已经没人在算”的记录。

    服务**运行期间**也会发生：工作进程被 kill、启动失败、或者根本没起来。
    以前这种记录会一直停在 queued/running，把唯一的任务槽永久占死，
    只能重启服务才能再跑一次。判据只有两条，都不猜：

      * running：pid 不是这次运行的活工作进程 -> 回收；
      * queued ：pid 已经不在了，或者根本没写过 pid 且排队超过 QUEUE_GRACE_SEC 秒 -> 回收。

    活着的进程一律不动。回收即 interrupted（终态），已算出的年份仍可回放。
    """
    init_db()
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT run_id, pid, status, created_at FROM runs WHERE status IN (?,?)",
            _STATUS_ACTIVE).fetchall()]
    reaped = []
    now = time.time()
    for r in rows:
        rid, pid, status = r["run_id"], r["pid"], r["status"]
        probe = probe_worker(pid, rid)
        if probe == WORKER_ALIVE:
            continue                                   # 真在跑，不动
        if probe == WORKER_UNKNOWN:
            continue                                   # 查不到 ≠ 死了：这一轮不回收
        if status == "queued":
            waited = now - (r["created_at"] or now)
            if pid is None and waited < config.QUEUE_GRACE_SEC:
                continue                               # 刚建的记录，给工作进程一点启动时间
            why = ("工作进程已不在" if pid is not None
                   else f"排队超过 {config.QUEUE_GRACE_SEC:.0f} 秒仍没有工作进程接手")
        else:
            why = "工作进程已不在（被结束或异常退出）"
        done = len(_lines(rid))
        note = (f"任务槽回收：{why}。本版不做跨进程续跑；"
                f"已完整保存的 {max(done - 1, 0)} 年仍可回放，继续推进请新建运行。")
        # 写入时再比对一次状态与 pid：检查之后如果工作进程刚启动（pid 变了 / 进了 running），
        # 这次 UPDATE 就匹配不到行，本轮不回收，下一轮再看。
        if transition(rid, "interrupted", allow_from=[status], expect_pid=pid,
                      years_done=max(done - 1, 0), finished_at=now, error=note,
                      recovery_note=""):
            _CACHE.pop(rid, None)
            reaped.append({"run_id": rid, "from": status, "why": why})
    return reaped


# 取消收尾的三个阶段。**只有用户明确按过取消**的运行才会走到这里 ——
# "暂时没看到进度"永远不是停掉一个正常计算的理由。
CANCEL_COOPERATIVE = "cooperative"   # 还在协作窗口内：等工作进程算完这一年自己停
CANCEL_ESCALATED = "escalated"       # 协作窗口用完了：已核验身份，强制停止
CANCEL_UNCONFIRMED = "unconfirmed"   # 进程身份查不到：**不杀**，如实报告，等下一轮
CANCEL_STOP_FAILED = "stop_failed"   # 信号发了但没能确认它停下来：**不放槽**，下一轮再来


def cancel_stage(run: Dict[str, Any], now: Optional[float] = None) -> Dict[str, Any]:
    """这条运行的取消进行到哪一步了（纯读，不改任何状态）。"""
    if not run or not run.get("cancel_requested"):
        return {"requested": False, "stage": "none", "requested_at": None,
                "seconds_left": None, "note": ""}
    now = time.time() if now is None else now
    at = run.get("cancel_requested_at")
    left = None if at is None else max(0.0, config.CANCEL_GRACE_SEC - (now - at))
    if run.get("status") in TERMINAL:
        stage = "finished"
    elif left is None or left > 0:
        stage = CANCEL_COOPERATIVE
    else:
        stage = CANCEL_ESCALATED
    return {"requested": True, "stage": stage, "requested_at": at,
            "seconds_left": None if left is None else round(left, 1),
            "note": run.get("cancel_note", "") or ""}


def enforce_cancels() -> List[Dict[str, Any]]:
    """把**用户明确请求的取消**在有界时间内收尾。

    三条路，都不猜：

      * 工作进程已确认不在（`gone`）—— 取消请求没人会读到，直接判 `canceled`；
      * 工作进程确认是本次运行的（`alive`）—— 先给 `CANCEL_GRACE_SEC` 秒的协作窗口，
        让它算完当前这一年自己停下（那条路会写 `canceled`）。窗口用完还在，
        说明它卡在某一步里读不到取消标志：**这时才**停止它；
      * 身份查不到（`unknown`，ps 超时 / 权限不足 / pid 可能被复用）—— **一个信号都不发**，
        只写一条人话说明，等下一轮再看。

    没有取消请求的运行一条都不碰 —— 这个函数里没有任何"多久没进度就杀"的判据。
    与完成/启动的竞态由 `transition(..., allow_from=..., expect_pid=...)` 兜住：
    工作进程要是抢先写了 `done`/`canceled`，这里的写入匹配不到行，赢家保持不变。
    """
    init_db()
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT run_id, pid, status, cancel_requested_at, cancel_last_attempt_at "
            "FROM runs "
            "WHERE cancel_requested=1 AND status IN (?,?)", _STATUS_ACTIVE).fetchall()]
    acted = []
    now = time.time()
    for r in rows:
        rid, pid, status = r["run_id"], r["pid"], r["status"]
        at = r["cancel_requested_at"] or now
        probe = probe_worker(pid, rid)
        if probe == WORKER_UNKNOWN:
            set_cancel_note(rid, "已请求取消，但暂时无法确认那个进程号还是不是这次运行的"
                                 "工作进程（可能已被系统回收并复用）。**不会**对身份不明的"
                                 "进程发信号；下一次检查会再看一遍。")
            acted.append({"run_id": rid, "action": CANCEL_UNCONFIRMED})
            continue
        if probe == WORKER_ALIVE:
            waited = now - at
            if waited < config.CANCEL_GRACE_SEC:
                set_cancel_note(rid, "已请求取消：工作进程会在当前这一年算完后自己停下"
                                     "（最多再等 %.0f 秒；超时就强制停止）。"
                                     % max(0.0, config.CANCEL_GRACE_SEC - waited))
                continue
            # 协作窗口用完。上一次强制停止要是刚试过，这一轮先不重复发信号 ——
            # stop_worker 要同步等好几秒，每来一个页面请求就重试会把接口拖住。
            # 这只是**节流**，不改变任何判断：取消请求、说明、不放槽通通保持原样。
            last_try = r["cancel_last_attempt_at"] or 0.0
            if now - last_try < config.CANCEL_GRACE_SEC:
                acted.append({"run_id": rid, "action": "stop_pending",
                              "why": "上一次停止尝试还不到 %.0f 秒，等下一轮再试"
                                     % config.CANCEL_GRACE_SEC})
                continue
            mark_cancel_attempt(rid, now)
            # stop_worker 内部会在每次发信号前重新核验身份。
            outcome = stop_worker(int(pid), rid)
            if outcome != WORKER_GONE:
                # **没有确认它停下来，就不能放槽。** 旧工作进程若还活着，仍会往
                # years.jsonl 里追加；数据库围栏只管数据库，管不住文件写入。
                # 取消请求保持原样，下一轮继续试 —— 不写 canceled、不放槽、不谎报已停止。
                if outcome == WORKER_ALIVE:
                    msg = ("已请求取消：协作窗口用完后发过停止信号（TERM 之后 KILL），"
                           "但到现在仍能查到这个工作进程还在。任务槽**先不释放**，"
                           "以免旧进程继续往这次运行的记录里追加；下一次检查会再试一次。")
                else:
                    msg = ("已请求取消：停止信号发出后无法确认这个进程的状态"
                           "（ps 超时 / 权限不足 / 信号发不出去）。**未知不等于已停止**，"
                           "任务槽先不释放；下一次检查会再看一遍。")
                set_cancel_note(rid, msg)
                acted.append({"run_id": rid,
                              "action": (CANCEL_STOP_FAILED if outcome == WORKER_ALIVE
                                         else CANCEL_UNCONFIRMED),
                              "stop_result": outcome, "why": msg})
                continue
            why = ("协作取消超时：请求取消 %.0f 秒后工作进程仍卡在同一步，已强制停止"
                   "（已确认该进程不在）。" % waited)
        else:
            why = "取消时工作进程已经不在了。"
        done = len(_lines(rid))
        note = (why + "已完整保存的 %d 年仍可回放（写到一半的那一年不算数）；"
                      "本版不做跨进程续跑，继续推进请新建运行。" % max(done - 1, 0))
        if transition(rid, "canceled", allow_from=[status], expect_pid=pid,
                      years_done=max(done - 1, 0), finished_at=time.time(),
                      cancel_note=note, error=note):
            _CACHE.pop(rid, None)
            acted.append({"run_id": rid, "action": CANCEL_ESCALATED if probe == WORKER_ALIVE
                          else "reaped", "stop_result": WORKER_GONE, "why": why})
        else:
            # 这中间工作进程自己收尾了（或状态/pid 变了）—— 赢家不覆盖。
            acted.append({"run_id": rid, "action": "already_settled"})
    return acted


def recover_interrupted() -> int:
    """服务启动时调用。返回**真正被标成 interrupted 的条数**（不是扫过几条）。

    顺序是固定的：先停掉可能还活着的旧工作进程，**核实它确实不在了**，再标中断。

    只有确认 `gone` 才终态收尾、才释放任务槽。理由和取消那条路一样：旧工作进程即使
    被围栏挡住改不回 `done`，仍然会往 `years.jsonl` 里**追加**年份（文件写入没有围栏），
    所以"在文案里承认没停下来"是不够的 —— 必须真的不放槽。

    停不下来（`alive`）或停没停下来查不到（`unknown`）：记录**保持活动状态**，
    写一条"恢复待处理"说明（`recovery_note`），任务槽继续占着。
    之后**不再主动发信号**：后续的 `/api/runs` 与新建运行会走 `reap_stale()` 重新探测
    （它只探测、不发信号），确认那个进程不在了才收尾。要主动结束它，请用户按取消 ——
    那是有明确同意的、会重新核验身份的有界升级路径。这里不看"跑了多久"，
    也不对没被取消的运行做任何超时判断。
    """
    init_db()
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT run_id, pid, status FROM runs WHERE status IN (?,?)",
            _STATUS_ACTIVE).fetchall()]
    recovered = 0
    for r in rows:
        rid, pid, status = r["run_id"], r["pid"], r["status"]
        probe = probe_worker(pid, rid)
        # 只有"确认是本次运行的活进程"才发信号；unknown 一个信号都不发。
        stopped = stop_worker(int(pid), rid) if probe == WORKER_ALIVE else probe
        done = len(_lines(rid))
        if stopped != WORKER_GONE:
            why = ("发过停止信号后仍能查到那个旧工作进程" if stopped == WORKER_ALIVE
                   else "无法确认那个进程号现在的状态（ps 超时 / 权限不足 / 可能已被复用）")
            set_recovery_note(rid, (
                "服务重启时该任务尚未完成，%s。**没有确认停下来就不放任务槽** —— "
                "旧进程还可能往这次运行的记录里追加年份（数据库围栏管不住文件写入）。"
                "记录保持当前状态，后续每次查看运行列表都会重新探测（只探测、不再发信号），"
                "确认它不在了就收尾；想主动结束它，请对这条运行按取消。" % why))
            continue
        note = ("服务重启时该任务尚未完成，旧工作进程已确认不在。"
                "本版不做跨进程续跑；已完整保存的 %d 年仍可回放，继续推进请新建运行。"
                % max(done - 1, 0))
        # 带上检查时看到的状态与 pid：这中间要是并发写完了 done、换了 pid、
        # 或者已经落到别的终态，这次写入就落空，**不覆盖赢家**。
        if transition(rid, "interrupted", allow_from=[status], expect_pid=pid,
                      years_done=max(done - 1, 0), finished_at=time.time(),
                      error=note, recovery_note=""):
            _CACHE.pop(rid, None)
            recovered += 1
    return recovered
