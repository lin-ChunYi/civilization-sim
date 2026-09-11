"""持久化：SQLite 存运行台账，每次运行一个 years.jsonl 存逐年记录。

刻意选最小可行方案（单用户、小规模）：不引入 Redis、队列、ORM 或数据库平台。
服务重启后已完成记录仍在；重启时把没跑完的任务标为“中断”，不假装能续跑。
"""
from __future__ import annotations

import json
import os
import sqlite3
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

def create_run(*, seed: int, years: int, sigma_m: int, move_mort_m: int, arm: str,
               label: str = "", kind: str = "user", engine: Dict[str, Any],
               repo_commit: str = "") -> str:
    run_id = uuid.uuid4().hex[:12]
    run_dir(run_id).mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute(
            "INSERT INTO runs (run_id,label,kind,status,created_at,seed,years,sigma_m,"
            "move_mort_m,arm,engine_sha256,engine_path,baseline_commit,repo_commit) "
            "VALUES (?,?,?,'queued',?,?,?,?,?,?,?,?,?,?)",
            (run_id, label, kind, time.time(), seed, years, sigma_m, move_mort_m, arm,
             engine["engine_sha256"], engine["engine_path"], engine["baseline_commit"],
             repo_commit))
    return run_id


def set_status(run_id: str, status: str, **fields) -> None:
    cols = ", ".join(f"{k}=?" for k in fields)
    sql = "UPDATE runs SET status=?" + (", " + cols if cols else "") + " WHERE run_id=?"
    with connect() as conn:
        conn.execute(sql, (status, *fields.values(), run_id))


def update_progress(run_id: str, years_done: int) -> None:
    with connect() as conn:
        conn.execute("UPDATE runs SET years_done=? WHERE run_id=?", (years_done, run_id))


def request_cancel(run_id: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE runs SET cancel_requested=1 WHERE run_id=?", (run_id,))


def cancel_requested(run_id: str) -> bool:
    with connect() as conn:
        row = conn.execute("SELECT cancel_requested FROM runs WHERE run_id=?",
                           (run_id,)).fetchone()
    return bool(row and row["cancel_requested"])


def write_meta(run_id: str, meta: Dict[str, Any]) -> None:
    meta_path(run_id).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


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
    p = meta_path(run_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


_CACHE: Dict[str, Any] = {}


def _lines(run_id: str) -> List[str]:
    """逐年记录的进程内缓存，按 (mtime, size) 失效。回放只读文件，不触发任何计算。"""
    p = years_path(run_id)
    if not p.exists():
        return []
    stt = p.stat()
    key = (stt.st_mtime_ns, stt.st_size)
    hit = _CACHE.get(run_id)
    if hit and hit[0] == key:
        return hit[1]
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    _CACHE[run_id] = (key, lines)
    return lines


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


def recover_interrupted() -> int:
    """服务启动时调用：没跑完的任务标为中断，不假装能跨进程续跑。"""
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT run_id FROM runs WHERE status IN (?,?)",
                            _STATUS_ACTIVE).fetchall()
        for r in rows:
            done = len(_lines(r["run_id"]))
            conn.execute(
                "UPDATE runs SET status='interrupted', years_done=?, finished_at=?, "
                "error=? WHERE run_id=?",
                (max(done - 1, 0), time.time(),
                 "服务重启或进程退出时该任务尚未完成。本版不做跨进程续跑，"
                 "已计算的年份仍可回放，继续推进请新建运行。", r["run_id"]))
    return len(rows)
