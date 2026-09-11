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
  arm           TEXT NOT NULL,
  years_done    INTEGER NOT NULL DEFAULT 0,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  engine_sha256 TEXT NOT NULL DEFAULT '',
  engine_path   TEXT NOT NULL DEFAULT '',
  baseline_commit TEXT NOT NULL DEFAULT '',
  repo_commit   TEXT NOT NULL DEFAULT '',
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


def init_db() -> None:
    config.RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


def run_dir(run_id: str) -> Path:
    return config.RUNS_DIR / run_id


def years_path(run_id: str) -> Path:
    return run_dir(run_id) / "years.jsonl"


def meta_path(run_id: str) -> Path:
    return run_dir(run_id) / "meta.json"


# ---------------------------------------------------------------- 写

def claim_slot(*, seed: int, years: int, sigma_m: int, move_mort_m: int, arm: str,
               label: str = "", kind: str = "user", engine: Dict[str, Any],
               repo_commit: str = "") -> Optional[str]:
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
            "move_mort_m,arm,engine_sha256,engine_path,baseline_commit,repo_commit) "
            "VALUES (?,?,?,'queued',?,?,?,?,?,?,?,?,?,?)",
            (run_id, label, kind, time.time(), seed, years, sigma_m, move_mort_m, arm,
             engine["engine_sha256"], engine["engine_path"], engine["baseline_commit"],
             repo_commit))
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


def set_pid(run_id: str, pid: int) -> None:
    """只写 pid，**不碰 status** —— 否则会把工作进程已经推进到的 running/done 打回 queued。"""
    with connect() as conn:
        conn.execute("UPDATE runs SET pid=? WHERE run_id=?", (pid, run_id))


def drop_run_row(run_id: str) -> None:
    """占槽后启动失败时把槽还回去。"""
    with connect() as conn:
        conn.execute("DELETE FROM runs WHERE run_id=?", (run_id,))


def transition(run_id: str, new_status: str, *, allow_from: Optional[List[str]] = None,
               **fields) -> bool:
    """按状态转换表改状态。来源状态不合法就什么都不写，返回 False。

    生产路径一律走这里；`force_status()` 只给测试用。
    """
    srcs = list(allow_from) if allow_from else sources_for(new_status)
    if not srcs:
        return False
    cols = ", ".join(f"{k}=?" for k in fields)
    holes = ",".join("?" for _ in srcs)
    sql = ("UPDATE runs SET status=?" + (", " + cols if cols else "") +
           f" WHERE run_id=? AND status IN ({holes})")
    with connect() as conn:
        cur = conn.execute(sql, (new_status, *fields.values(), run_id, *srcs))
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


def request_cancel(run_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE runs SET cancel_requested=1 WHERE run_id=?", (run_id,))


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


def _is_our_worker(pid: Optional[int], run_id: str) -> bool:
    """pid 还活着，而且确实是这次运行的工作进程（避免 pid 复用误伤别的程序）。"""
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False
    try:
        out = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                             capture_output=True, text=True, timeout=5).stdout
    except Exception:  # noqa: BLE001
        return False
    return "observer.worker" in out and run_id in out


def stop_worker(pid: int, run_id: str, grace: float = 3.0) -> bool:
    """先 SIGTERM，等一会儿再 SIGKILL。必须在标记中断**之前**做完，
    否则会出现“记录标成 interrupted，旧进程还在写、还能把状态改回 done”。"""
    try:
        os.kill(int(pid), signal.SIGTERM)
    except OSError:
        return False
    deadline = time.time() + grace
    while time.time() < deadline:
        if not _is_our_worker(pid, run_id):
            return True
        time.sleep(0.1)
    try:
        os.kill(int(pid), signal.SIGKILL)
    except OSError:
        pass
    time.sleep(0.2)
    return True


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
        if _is_our_worker(pid, rid):
            continue                                   # 真在跑，不动
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
        if transition(rid, "interrupted", years_done=max(done - 1, 0),
                      finished_at=now, error=note):
            _CACHE.pop(rid, None)
            reaped.append({"run_id": rid, "from": status, "why": why})
    return reaped


def recover_interrupted() -> int:
    """服务启动时调用。

    顺序是固定的：**先停掉可能还活着的旧工作进程，再把记录标成中断**。
    工作进程那边所有写入都带 status='running' AND pid=? 的围栏，所以一旦标成 interrupted，
    即使有漏网的进程也改不回 done。已经算出来的年份仍然可以回放。
    """
    init_db()
    with connect() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT run_id, pid FROM runs WHERE status IN (?,?)", _STATUS_ACTIVE).fetchall()]
    for r in rows:
        killed = False
        if _is_our_worker(r["pid"], r["run_id"]):
            killed = stop_worker(int(r["pid"]), r["run_id"])
        done = len(_lines(r["run_id"]))
        note = ("服务重启时该任务尚未完成" + ("，旧工作进程已被停止" if killed else "") +
                "。本版不做跨进程续跑；已完整保存的年份仍可回放，继续推进请新建运行。")
        transition(r["run_id"], "interrupted", years_done=max(done - 1, 0),
                   finished_at=time.time(), error=note)
        _CACHE.pop(r["run_id"], None)
    return len(rows)
