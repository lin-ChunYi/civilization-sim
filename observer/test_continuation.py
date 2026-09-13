#!/usr/bin/env python3
"""C_CONT_01 续演验收：保存 -> 换进程 -> 接着算，必须与连续算逐年一致。

沿用本项目的三态结果：PASS / FAIL / UNCOVERED。**未覆盖不计入通过**；有必过项失败则退出码 1。
全部在独立临时库里跑，模型计算一律走**子进程**，不碰正常运行的数据，也不改任何受保护的引擎。

    python3 observer/test_continuation.py [--report 路径.json] [--quick]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("CONT_TEST_DATA", "/tmp/chronicle-cont-20260913/testdata"))
os.environ["OBSERVER_DATA_DIR"] = str(DATA)
os.environ.setdefault("OBSERVER_WRITE_RATE", "500")
os.environ.setdefault("OBSERVER_MAX_YEARS", "3000")
sys.path.insert(0, str(REPO))
shutil.rmtree(DATA, ignore_errors=True)

from observer import adapter, checkpoints, config, continuation, store   # noqa: E402

RESULTS = []
PARAMS = dict(seed=4242, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000,
              recip_m=1000, arm="memory", engine_name="exp06")


def record(name, state, detail=""):
    RESULTS.append({"name": name, "state": state, "detail": str(detail)[:400]})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "UNCOVERED": "未覆盖"}[state]
    print(f"  {name:<58} {mark}" + (f"   {detail}" if detail else ""), flush=True)


def check(name, ok, detail=""):
    record(name, "PASS" if ok else "FAIL", detail)


def uncov(name, why):
    record(name, "UNCOVERED", why)


# ---------------------------------------------------------------- 基础设施
COMMANDS = []


def worker(run_id, stub_make_world=False):
    """在**独立子进程**里跑一段计算。`stub_make_world` 时把 make_world 换成会抛异常的桩 ——
    续演还能成功，就证明它不是从第 0 年重算的。"""
    if stub_make_world:
        code = (
            "import sys; sys.path.insert(0, %r)\n"
            "from observer import adapter, worker\n"
            "def _boom(*a, **k):\n"
            "    raise AssertionError('续演不应调用 make_world')\n"
            "adapter.make_world = _boom\n"
            "sys.exit(worker.execute(%r))\n" % (str(REPO), run_id))
        cmd = [sys.executable, "-c", code]
    else:
        cmd = [sys.executable, "-m", "observer.worker", run_id]
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True,
                          env={**os.environ})
    COMMANDS.append({"cmd": " ".join(cmd[:3]) + (" <stub>" if stub_make_world else ""),
                     "run_id": run_id, "exit_code": proc.returncode,
                     "stderr_tail": (proc.stderr or "")[-200:]})
    return proc.returncode


def fresh(years, **over):
    p = dict(PARAMS)
    p.update(over)
    with store.connect() as c:
        c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
    return store.claim_slot(years=years, label="cont-test", kind="user",
                            engine=adapter.engine_info(p["engine_name"]), **p)


def continue_from(parent_id, additional, request_id=None):
    parent = store.get_run(parent_id)
    el = continuation.eligibility(parent)
    if not el["eligible"]:
        return None, el
    with store.connect() as c:
        c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running') "
                  "AND run_id<>?", (parent_id,))
    claim = store.claim_continuation(
        parent, request_id=request_id or str(uuid.uuid4()), additional_years=additional,
        target_years=el["from_year"] + additional, from_year=el["from_year"])
    return claim, el


def year_rows(run_id, upto):
    return [store.read_year(run_id, t) for t in range(0, upto + 1)]


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def cp_state(run_id):
    payload = checkpoints.load(store.checkpoint_path(run_id))
    st, rec = checkpoints.restore(payload)
    return payload, st, rec


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


print("=" * 96)
print("C_CONT_01 续演验收 —— 保存后继续计算")
print("=" * 96)
store.init_db()

ap = argparse.ArgumentParser()
ap.add_argument("--report")
ap.add_argument("--quick", action="store_true", help="跳过 300+300 的长跑")
args = ap.parse_args()

# ------------------------------------------------------- 1. 三个种子 60+60 vs 120
print("\nK1 三个种子：60 步 -> 存档 -> 换进程再 60 步，与连续 120 步逐年比较")
for seed in (0, 777, 4242):
    a = fresh(60, seed=seed)
    if worker(a) != 0 or store.get_run(a)["status"] != "done":
        check(f"K1 seed={seed} 前 60 年跑完", False, store.get_run(a)["error"][:80])
        continue
    claim, el = continue_from(a, 60)
    if claim is None:
        check(f"K1 seed={seed} 可续演", False, el["reason_code"])
        continue
    kid = claim["run_id"]
    rc = worker(kid, stub_make_world=True)      # 桩：续演不许调用 make_world
    ctrl = fresh(120, seed=seed)
    worker(ctrl)
    got, want = year_rows(kid, 120), year_rows(ctrl, 120)
    d = first_diff(got, want)
    check(f"K1 seed={seed} 60+60 与连续 120 逐年完全一致（且未调用 make_world）",
          rc == 0 and store.get_run(kid)["status"] == "done" and d is None,
          f"rc={rc} 首处不同={d}")
    check(f"K1b seed={seed} full_digest 与连续计算相同",
          store.get_run(kid)["full_digest"] == store.get_run(ctrl)["full_digest"],
          store.get_run(kid)["full_digest"][:32])
    _, st_kid, _ = cp_state(kid)
    _, st_ctrl, _ = cp_state(ctrl)
    check(f"K1c seed={seed} **完整模型状态与全部日志**逐字段相同（不只看末人口）",
          st_kid == st_ctrl,
          "log/aid_log/share_log 长度 %s vs %s" % (
              (len(st_kid["log"]), len(st_kid["aid_log"]), len(st_kid["share_log"])),
              (len(st_ctrl["log"]), len(st_ctrl["aid_log"]), len(st_ctrl["share_log"]))))
    ids_kid = [e["id"] for r in got for e in r["events"]]
    ids_ctrl = [e["id"] for r in want for e in r["events"]]
    check(f"K1d seed={seed} 稳定事件 id 逐个相同，且全局无重复",
          ids_kid == ids_ctrl and len(set(ids_kid)) == len(ids_kid),
          f"{len(ids_kid)} 个事件")

# ------------------------------------------------------- 2. 300+300 vs 600
print("\nK2 seed=4242：300 -> 存档并换进程 -> 再 300，与连续 600 步逐年比较")
if args.quick:
    uncov("K2 300+300 与连续 600 一致", "--quick 模式跳过长跑，本次未执行")
    long_kid = long_ctrl = None
else:
    p300 = fresh(300)
    worker(p300)
    claim, el = continue_from(p300, 300)
    long_kid = claim["run_id"] if claim else None
    if long_kid is None:
        check("K2 300 年后可续演", False, el["reason_code"])
    else:
        rc = worker(long_kid, stub_make_world=True)
        long_ctrl = fresh(600)
        worker(long_ctrl)
        got, want = year_rows(long_kid, 600), year_rows(long_ctrl, 600)
        d = first_diff(got, want)
        check("K2 300+300 与连续 600 逐年完全一致（续演进程被禁止调用 make_world）",
              rc == 0 and store.get_run(long_kid)["status"] == "done" and d is None,
              f"rc={rc} 首处不同={d}")
        _, s1, _ = cp_state(long_kid)
        _, s2, _ = cp_state(long_ctrl)
        check("K2b 第 600 年的完整模型状态与日志相同", s1 == s2)
        check("K2c 全局进度与本段进度分开：years_done=600，本段只算了 300 步",
              store.get_run(long_kid)["years_done"] == 600
              and store.get_run(long_kid)["completed_steps"] == 300,
              "%s / %s" % (store.get_run(long_kid)["years_done"],
                           store.get_run(long_kid)["completed_steps"]))

# ------------------------------------------------------- 3/4. 边界年与继承历史
print("\nK3 边界年只出现一次；当年账等于累计差；回助仍能引用继承历史里的原始援助 id")
if long_kid:
    rows = year_rows(long_kid, 600)
    ticks = [r["t"] for r in rows]
    check("K3a 第 300 年只出现一次，年号连续无重复",
          ticks == list(range(601)) and ticks.count(300) == 1)
    c300, c301 = rows[300]["cum"], rows[301]["cum"]
    bad = [k for k in c301 if rows[301]["year"][k] != c301[k] - c300[k]]
    check("K3b 第 301 年的年度账 == 301 与 300 的累计账之差（记录器前值接上了）",
          not bad, "对不上的字段：%s" % bad[:4])
    ids = [e["id"] for r in rows for e in r["events"]]
    check("K3c 全段事件 id 无重复", len(set(ids)) == len(ids), f"{len(ids)} 个")
    repays = [(r["t"], e) for r in rows[301:] for e in r["events"]
              if e["type"] == "aid" and e.get("repay") and e.get("basis", {}).get("prior_events")]
    inherited = [(t, e) for t, e in repays
                 if any(int(pid.split("-")[0][1:]) <= 300 for pid in e["basis"]["prior_events"])]
    if not repays:
        uncov("K3d 回助引用继承历史里的原始援助 id", "第 301 年之后没有带依据的回助，前提缺失")
    elif not inherited:
        uncov("K3d 回助引用继承历史里的原始援助 id",
              "有回助，但依据都落在第 300 年之后，前提缺失")
    else:
        t, ev = inherited[0]
        pid = [p for p in ev["basis"]["prior_events"] if int(p.split("-")[0][1:]) <= 300][0]
        py = int(pid.split("-")[0][1:])
        src = [x for x in rows[py]["events"] if x["id"] == pid]
        check("K3d 第 300 年之后的回助仍能引用继承历史中的原始援助 id（且能跳回去）",
              bool(src) and str(src[0]["donor"]) == str(ev["receiver"])
              and str(src[0]["receiver"]) == str(ev["donor"]),
              f"第 {t} 年的回助依据 {pid}")
else:
    uncov("K3a–d 边界年与继承历史", "K2 未执行，前提缺失")

# ------------------------------------------------------- 5. 恒等式与父文件不变
print("\nK4 全部恒等式成立；父运行文件逐字节不变")
if long_kid:
    rows = year_rows(long_kid, 600)
    bad = []
    for r in rows:
        integ = r["integrity"]
        for k in ("conservation_error", "population_identity_error",
                  "share_ledger_error", "aid_ledger_error", "aid_memory_error"):
            if integ.get(k):
                bad.append((r["t"], k, integ[k]))
    check("K4a 资源 / 人口 / 信息 / 援助 / 援助记忆五本账全段恒等",
          not bad, str(bad[:3]))

# ------------------------------------------------------- 6. 故障注入
print("\nK5 坏档 / 错类型 / 错源哈希 / 参数不符 / 缺档 / 尾部半条 / 检查点落后 / 重复请求")


def clone_run(src_id, mutate_checkpoint=None, mutate_history=None, mutate_row=None):
    """把一条运行**复制**成隔离副本再注入故障 —— 不动原件，更不动任何引擎。"""
    new_id = "clone-" + uuid.uuid4().hex[:8]
    store.run_dir(new_id).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(store.years_path(src_id), store.years_path(new_id))
    if store.checkpoint_path(src_id).exists():
        shutil.copyfile(store.checkpoint_path(src_id), store.checkpoint_path(new_id))
    row = dict(store.get_run(src_id))
    row["run_id"] = new_id
    row["root_run_id"] = new_id
    row["parent_run_id"] = ""
    if mutate_row:
        row.update(mutate_row)
    cols = [k for k in row if k != "pid"]
    with store.connect() as c:
        c.execute("INSERT INTO runs (%s) VALUES (%s)"
                  % (",".join(cols), ",".join("?" * len(cols))), [row[k] for k in cols])
    if mutate_checkpoint:
        mutate_checkpoint(store.checkpoint_path(new_id))
    if mutate_history:
        mutate_history(store.years_path(new_id))
    store._CACHE.pop(new_id, None)
    return new_id


base = fresh(20)
worker(base)
parent_hist_sha = sha_file(store.years_path(base))
parent_cp_sha = sha_file(store.checkpoint_path(base))

cases = []


def corrupt_bytes(path):
    raw = bytearray(path.read_bytes())
    raw[len(raw) // 2] ^= 0x20
    path.write_bytes(bytes(raw))


def wrong_type(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["payload"]["tick"] = "300"
    path.write_text(json.dumps(doc), encoding="utf-8")


def wrong_engine_sha(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["payload"]["engine_sha256"] = "0" * 64
    doc["digest"] = hashlib.sha256(json.dumps(
        doc["payload"], ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    path.write_text(json.dumps(doc), encoding="utf-8")


def wrong_params(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["payload"]["params"]["aid_m"] = 1
    doc["digest"] = hashlib.sha256(json.dumps(
        doc["payload"], ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    path.write_text(json.dumps(doc), encoding="utf-8")


def half_tail(path):
    with path.open("a", encoding="utf-8") as fh:
        fh.write('{"t":21,"stock":[1],"ban')


def behind_history(path):
    """检查点停在旧年份，完整历史更新 —— 历史仍可回放，但不许从这里续演。"""
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["payload"]["history"]["records"] -= 1
    doc["payload"]["tick"] -= 1
    doc["digest"] = hashlib.sha256(json.dumps(
        doc["payload"], ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    path.write_text(json.dumps(doc), encoding="utf-8")


cases.append(("坏档（字节被改）", clone_run(base, mutate_checkpoint=corrupt_bytes),
              "checkpoint_invalid"))
cases.append(("错类型（tick 变成字符串）", clone_run(base, mutate_checkpoint=wrong_type),
              "checkpoint_invalid"))
cases.append(("错源哈希", clone_run(base, mutate_checkpoint=wrong_engine_sha),
              "engine_mismatch"))
cases.append(("参数不符", clone_run(base, mutate_checkpoint=wrong_params), "config_mismatch"))
cases.append(("尾部半条记录", clone_run(base, mutate_history=half_tail), "ready"))
cases.append(("检查点落后完整历史", clone_run(base, mutate_checkpoint=behind_history),
              "checkpoint_not_at_tip"))
missing = clone_run(base)
store.checkpoint_path(missing).unlink()
cases.append(("缺检查点", missing, "missing_checkpoint"))
cases.append(("不支持的引擎", clone_run(base, mutate_row={"engine": "exp03"}),
              "unsupported_engine"))
cases.append(("来源还在跑", clone_run(base, mutate_row={"status": "running"}), "source_active"))

wrong = []
for label, rid, want in cases:
    got = continuation.eligibility(store.get_run(rid))
    code = got["reason_code"]
    if code != want:
        wrong.append(f"{label}->{code}(应 {want})")
check("K5a 八类坏档 / 不合格来源各自给出确定且正确的原因码", not wrong, "; ".join(wrong))
half_id = [rid for label, rid, _ in cases if label == "尾部半条记录"][0]
check("K5b 尾部半条只被排除在有效前缀外，原文件不改写、仍可续演",
      continuation.eligibility(store.get_run(half_id))["eligible"] is True
      and store.years_path(half_id).read_bytes().endswith(b'"ban'),
      "半条仍在文件里")
nt = [rid for label, rid, _ in cases if label == "检查点落后完整历史"][0]
v = continuation.eligibility(store.get_run(nt))
check("K5c 检查点落后时：历史照常可回放，但明确拒绝续演，不删历史也不伪造新检查点",
      v["reason_code"] == "checkpoint_not_at_tip"
      and store.year_count(nt) == 21 and store.read_year(nt, 20) is not None,
      v["reason"][:60])

# 重复请求与并发占槽
req = str(uuid.uuid4())
c1, _ = continue_from(base, 5, request_id=req)
c2 = store.claim_continuation(store.get_run(base), request_id=req, additional_years=5,
                              target_years=25, from_year=20)
check("K5d 同一 request_id 重试返回同一条子运行，不重复启动",
      c1 and c2 and c1["run_id"] == c2["run_id"] and c2["reused"] is True,
      str(c2))
try:
    store.claim_continuation(store.get_run(base), request_id=req, additional_years=9,
                             target_years=29, from_year=20)
    conflict = False
except store.IdempotencyConflict:
    conflict = True
check("K5e 同一 request_id 配不同请求 -> 冲突，不当成新任务", conflict)
busy = store.claim_continuation(store.get_run(base), request_id=str(uuid.uuid4()),
                                additional_years=5, target_years=25, from_year=20)
check("K5f 槽被占时不建第二条子运行（复制历史也占这个槽）", busy is None)
with store.connect() as c:
    c.execute("DELETE FROM runs WHERE run_id=?", (c1["run_id"],))
replay = store.claim_continuation(store.get_run(base), request_id=req, additional_years=5,
                                  target_years=25, from_year=20)
check("K5g 删掉子运行后，同一 request_id 也不能重放成新任务",
      replay is not None and replay["reused"] is True
      and replay["run_id"] == c1["run_id"], str(replay))

check("K4b 父运行的历史文件与检查点在续演之后逐字节不变",
      sha_file(store.years_path(base)) == parent_hist_sha
      and sha_file(store.checkpoint_path(base)) == parent_cp_sha)

# ------------------------------------------------------- 7. 连续三次续演
print("\nK6 连续续演三次：历史不重复边界、不重复事件；活着/未知的来源不放行")
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
chain = fresh(20)
worker(chain)
chain_ids = [chain]
ok_chain = True
for i in range(3):
    claim, el = continue_from(chain_ids[-1], 10)
    if claim is None:
        ok_chain = False
        check(f"K6 第 {i + 1} 次续演可放行", False, el["reason_code"])
        break
    if worker(claim["run_id"], stub_make_world=True) != 0:
        ok_chain = False
        check(f"K6 第 {i + 1} 次续演跑完", False,
              store.get_run(claim["run_id"])["error"][:80])
        break
    chain_ids.append(claim["run_id"])
if ok_chain and len(chain_ids) == 4:
    last = chain_ids[-1]
    rows = year_rows(last, 50)
    ids = [e["id"] for r in rows for e in r["events"]]
    ctrl = fresh(50)
    worker(ctrl)
    d = first_diff(rows, year_rows(ctrl, 50))
    check("K6a 三次续演接出来的 50 年与连续 50 年逐年一致",
          d is None and [r["t"] for r in rows] == list(range(51)), f"首处不同={d}")
    check("K6b 边界年不重复、事件 id 不重复",
          len(set(ids)) == len(ids) and store.year_count(last) == 51, f"{len(ids)} 个事件")
    check("K6c 每一代的血缘都指回最初那条运行",
          all(store.get_run(r)["root_run_id"] == chain for r in chain_ids[1:]),
          str([store.get_run(r)["from_year"] for r in chain_ids[1:]]))

alive_src = clone_run(base, mutate_row={"status": "running", "pid": os.getpid()})
check("K6d 来源还活着 / 状态未知时一律不放行",
      continuation.eligibility(store.get_run(alive_src))["reason_code"]
      in ("source_active", "worker_unknown"),
      continuation.eligibility(store.get_run(alive_src))["reason_code"])

# ------------------------------------------------------- 汇总
npass = sum(1 for r in RESULTS if r["state"] == "PASS")
nfail = sum(1 for r in RESULTS if r["state"] == "FAIL")
nunc = sum(1 for r in RESULTS if r["state"] == "UNCOVERED")
print("\n" + "=" * 96)
print(f"  通过 {npass} / 失败 {nfail} / 未覆盖 {nunc}（共 {len(RESULTS)} 项）")
print("  注：未覆盖项**不计入通过**。")
print("=" * 96)

if args.report:
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "task": "C_CONT_01",
        "generated_at": time.time(),
        "repo": str(REPO),
        "data_dir": str(DATA),
        "params": {k: v for k, v in PARAMS.items()},
        "seeds": [0, 777, 4242],
        "quick": bool(args.quick),
        "engine": adapter.engine_info("exp06"),
        "commands": COMMANDS,
        "results": RESULTS,
        "totals": {"pass": npass, "fail": nfail, "uncovered": nunc, "total": len(RESULTS)},
        "parent_files_unchanged": {"history_sha256": parent_hist_sha,
                                   "checkpoint_sha256": parent_cp_sha},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("报告已写入", out)

if nfail:
    sys.exit(1)
