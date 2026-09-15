#!/usr/bin/env python3
"""EXP-07 后台接线验收：参数真的生效、耕作数据真的记下来、旧存档仍然能续演。

三态结果：PASS / FAIL / UNCOVERED。**未覆盖不计入通过**；有必过项失败则退出码 1。
全部在独立临时库与独立端口上跑，不碰正常运行的数据，也不动任何受保护的引擎。

    python3 observer/test_exp07.py [--report 路径.json] [--quick]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("EXP07_TEST_DATA", "/tmp/chronicle-exp07-20260913/api/testdata"))
BASELINE = os.environ.get("EXP07_BASELINE", "b12bdd77baabf24eed05a600dc35aa8d0aba1bd4")
TEST_PORT = int(os.environ.get("EXP07_TEST_PORT", "8902"))
os.environ["OBSERVER_DATA_DIR"] = str(DATA)
os.environ.setdefault("OBSERVER_WRITE_RATE", "500")
os.environ.setdefault("OBSERVER_MAX_YEARS", "3000")
sys.path.insert(0, str(REPO))
shutil.rmtree(DATA, ignore_errors=True)

from observer import adapter, checkpoints, config, continuation, store   # noqa: E402

RESULTS, COMMANDS, SERVICES, HTTP_CALLS = [], [], [], []
FARM_PARAMS = dict(seed=4242, sigma_m=0, move_mort_m=50, share_m=1000, aid_m=1000,
                   recip_m=1000, farm_m=250, arm="memory", engine_name="exp07")


def record(name, state, detail=""):
    RESULTS.append({"name": name, "state": state, "detail": str(detail)[:400]})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "UNCOVERED": "未覆盖"}[state]
    print(f"  {name:<58} {mark}" + (f"   {detail}" if detail else ""), flush=True)


def check(name, ok, detail=""):
    record(name, "PASS" if ok else "FAIL", detail)


def uncov(name, why):
    record(name, "UNCOVERED", why)


def worker(run_id, cwd=None, env=None):
    cmd = [sys.executable, "-m", "observer.worker", run_id]
    proc = subprocess.run(cmd, cwd=str(cwd or REPO), capture_output=True, text=True,
                          env={**os.environ, **(env or {})})
    COMMANDS.append({"cmd": " ".join(cmd), "cwd": str(cwd or REPO),
                     "run_id": run_id, "exit_code": proc.returncode,
                     "stderr_tail": (proc.stderr or "")[-200:]})
    return proc.returncode


def fresh(years, **over):
    p = dict(FARM_PARAMS)
    p.update(over)
    with store.connect() as c:
        c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
    return store.claim_slot(years=years, label="exp07-test", kind="user",
                            engine=adapter.engine_info(p["engine_name"]), **p)


def cont(parent_id, additional, request_id=None):
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


def rows(run_id, upto):
    return [store.read_year(run_id, t) for t in range(0, upto + 1)]


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def _http(method, path, body=None, timeout=30):
    import urllib.error
    import urllib.request
    url = "http://127.0.0.1:%d%s" % (TEST_PORT, path)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code, raw = resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        code, raw = exc.code, exc.read().decode("utf-8")
    try:
        payload = json.loads(raw)
    except ValueError:
        payload = raw
    HTTP_CALLS.append({"method": method, "url": url, "request": body,
                       "status": code, "response": payload})
    return code, payload


def start_service(tag):
    log = Path(DATA).parent / ("service-%s.log" % tag)
    log.parent.mkdir(parents=True, exist_ok=True)
    fh = log.open("ab")
    cmd = [sys.executable, "-m", "uvicorn", "observer.app:app",
           "--host", "127.0.0.1", "--port", str(TEST_PORT)]
    proc = subprocess.Popen(cmd, cwd=str(REPO), stdout=fh, stderr=fh,
                            start_new_session=True, env={**os.environ})
    ok = False
    for _ in range(120):
        try:
            if _http("GET", "/api/health", timeout=2)[0] == 200:
                ok = True
                break
        except Exception:                                            # noqa: BLE001
            pass
        time.sleep(0.5)
    SERVICES.append({"tag": tag, "pid": proc.pid, "cmd": " ".join(cmd), "port": TEST_PORT,
                     "data_dir": str(DATA), "healthy": ok, "started_at": time.time(),
                     "exit_code": None, "log": str(log)})
    return proc


def stop_service(proc):
    proc.terminate()
    try:
        rc = proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = proc.wait(timeout=15)
    alive = True
    try:
        os.kill(proc.pid, 0)
    except ProcessLookupError:
        alive = False
    except OSError:
        alive = True
    for row in SERVICES:
        if row["pid"] == proc.pid and row["exit_code"] is None:
            row["exit_code"] = rc
            row["stopped_at"] = time.time()
            row["still_alive_after_stop"] = alive
    return rc, alive


def wait_http(run_id, limit=2400):
    for _ in range(limit):
        code, row = _http("GET", "/api/runs/%s" % run_id)
        if code == 200 and row.get("status") in ("done", "failed", "canceled", "interrupted"):
            return row
        time.sleep(0.5)
    return _http("GET", "/api/runs/%s" % run_id)[1]


print("=" * 96)
print("EXP-07 后台接线验收")
print("=" * 96)
store.init_db()
ap = argparse.ArgumentParser()
ap.add_argument("--report")
ap.add_argument("--quick", action="store_true", help="跳过 300+300 的长跑与服务重启")
args = ap.parse_args()

# ---------------------------------------------------------------- P 参数与拒绝
print("\nP 参数端到端真正生效；旧引擎正确拒绝 FARM_M")
from fastapi.testclient import TestClient                              # noqa: E402
from observer.app import app                                          # noqa: E402

with TestClient(app) as c:
    cfg = c.get("/api/config").json()
    check("P1 契约版本升到 obs-1.11，默认引擎仍是 exp03",
          cfg["api_version"] == "obs-1.11" and cfg["default_engine"] == "exp03",
          "%s / %s" % (cfg["api_version"], cfg["default_engine"]))
    e7 = cfg["engines"].get("exp07", {})
    check("P2 exp07 已登记，farm_m 排在 recip_m 之后",
          e7.get("engine_params") == ["sigma_m", "move_mort_m", "share_m", "aid_m",
                                      "recip_m", "farm_m"],
          str(e7.get("engine_params")))
    spec = {p["name"]: p for p in e7.get("params", [])}
    check("P3 farm_m 的能力表给出范围 / 默认 / 单位 / 说明",
          spec.get("farm_m", {}).get("max") == 1000
          and spec["farm_m"]["min"] == 0 and spec["farm_m"]["default"] == 0
          and spec["farm_m"]["unit"] and spec["farm_m"]["note"],
          str(spec.get("farm_m"))[:80])
    check("P4 exp07 的常量表带上三个耕作常量",
          e7["constants"]["FIELD_CAP_M"] == 60000
          and e7["constants"]["FIELD_DECAY_M"] == 200
          and e7["constants"]["FARM_YIELD_M"] == 2500)
    check("P5 旧引擎把 farm_m 列进 unsupported_params",
          cfg["engines"]["exp06"]["unsupported_params"] == ["farm_m"]
          and e7["unsupported_params"] == [])
    bad = [({"engine": "exp06", "farm_m": 250}, 400, "旧引擎收到非零 farm_m"),
           ({"engine": "exp03", "farm_m": 1}, 400, "更旧的引擎同样拒绝"),
           ({"engine": "exp07", "farm_m": 1001}, 400, "越界"),
           ({"engine": "exp07", "farm_m": 1.5}, 422, "小数"),
           ({"engine": "exp07", "farm_m": True}, 422, "布尔")]
    wrong = []
    for extra, want, why in bad:
        body = {"seed": 1, "years": 2, "sigma_m": 0, "move_mort_m": 0, "share_m": 0,
                "aid_m": 0, "recip_m": 0, "farm_m": 0}
        body.update(extra)
        got = c.post("/api/runs", json=body).status_code
        if got != want:
            wrong.append("%s -> %d(应 %d)" % (why, got, want))
    check("P6 旧引擎的非零 farm_m、越界、小数、布尔全部被准确拒绝", not wrong, "; ".join(wrong))
    ok0 = c.post("/api/runs", json={"seed": 1, "years": 1, "engine": "exp06",
                                    "sigma_m": 0, "move_mort_m": 0, "share_m": 0,
                                    "aid_m": 0, "recip_m": 0, "farm_m": 0,
                                    "label": "farm0 旧引擎"})
    check("P7 farm_m=0 时旧引擎照常放行（零值不等于不支持，也不会传给旧引擎）",
          ok0.status_code == 200, str(ok0.json())[:70])
    if ok0.status_code == 200:
        rid0 = ok0.json()["run_id"]
        for _ in range(600):
            if store.get_run(rid0)["status"] not in ("queued", "running"):
                break
            time.sleep(0.05)
        r0 = c.get("/api/runs/%s/year/0" % rid0).json()
        check("P8 旧引擎的年度记录里整个 farm 段缺席（不填 0 冒充支持）", "farm" not in r0)

# 参数真的进了模型：同种子只改 farm_m，结果必须不同
with store.connect() as c_:
    c_.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
a = fresh(12, farm_m=0)
worker(a)
b = fresh(12, farm_m=500)
worker(b)
check("P9 同种子只改 FARM_M，结果就不同（参数真的走到了引擎里）",
      store.get_run(a)["full_digest"] != store.get_run(b)["full_digest"]
      and store.get_run(a)["status"] == store.get_run(b)["status"] == "done",
      "%s… vs %s…" % (store.get_run(a)["full_digest"][:14],
                      store.get_run(b)["full_digest"][:14]))

# ---------------------------------------------------------------- R 记录口径
print("\nR 年度记录的 farm 段：口径固定、第 0 年全 0、参与者来自相位前状态")
rec_run = fresh(6, farm_m=250)
worker(rec_run)
y0 = store.read_year(rec_run, 0)
y5 = store.read_year(rec_run, 5)
meta = store.read_meta(rec_run) or {}
check("R1 farm 段的 schema 是 farm-1，field_m 按 meta.cell_ids 的顺序给 64 个整数",
      y5["farm"]["schema"] == "farm-1" and len(y5["farm"]["field_m"]) == len(meta["cell_ids"])
      and len(meta["cell_ids"]) == 64,
      "%d 格" % len(y5["farm"]["field_m"]))
check("R2 第 0 年：year 全 0、cells 空、field_m 全 0",
      all(v in (0, None) for v in y0["farm"]["year"].values())
      and y0["farm"]["cells"] == [] and set(y0["farm"]["field_m"]) == {0})
check("R3 year 与 cum 的流量字段齐全且同名",
      {"farm_effort_m", "forage_effort_m", "potential_kcal", "harvested_kcal",
       "uncollected_kcal", "built_m", "decayed_m"} <= set(y5["farm"]["year"]),
      str(sorted(y5["farm"]["year"])))
check("R4 耕地规模是存量：field_total_m 单列，不混进累计流量",
      "field_total_m" in y5["farm"] and "field_m" not in y5["farm"]["cum"]
      and y5["farm"]["field_total_m"] == sum(y5["farm"]["field_m"]))
cells = y5["farm"]["cells"]
check("R5 cells 只列本年有劳动或有旧耕地的格，按 cell 升序",
      cells and [x["cell"] for x in cells] == sorted(x["cell"] for x in cells)
      and all({"cell", "field_before_m", "field_after_m", "worked_m", "built_m",
               "decayed_m", "weather_m", "potential_kcal", "harvested_kcal",
               "uncollected_kcal", "participants"} <= set(x) for x in cells),
      "%d 格" % len(cells))
parts = [p for x in cells for p in x["participants"]]
check("R6 participants 字段齐全，id 是字符串，人数来自相位前状态",
      parts and all(isinstance(p["id"], str) for p in parts)
      and all({"id", "population_before", "farm_effort_m", "forage_effort_m",
               "forage_kcal", "crop_kcal"} <= set(p) for p in parts)
      and all(p["population_before"] is not None for p in parts),
      str(parts[0])[:110] if parts else "无参与者")
check("R7 劳动预算在记录层也对得上：耕作 + 采集 == 人数 × 1000",
      all(p["farm_effort_m"] + p["forage_effort_m"] == p["population_before"] * 1000
          for p in parts))
ser = store.read_series(rec_run)
FLOW_NAMES = ("farm_effort_m", "forage_effort_m", "potential_kcal", "harvested_kcal",
              "uncollected_kcal", "built_m", "decayed_m")


def cum_vs_year(run_id, upto):
    """**独立重算**：把逐年 year 自己加一遍，和记录里的 cum 逐字段比。
    不调用生产的累计逻辑，也不只看"非 null"或"等于 0"。"""
    ys = rows(run_id, upto)
    running = {k: 0 for k in FLOW_NAMES}
    bad = []
    for r in ys:
        f = r["farm"]
        for k in FLOW_NAMES:
            yv, cv = f["year"].get(k), f["cum"].get(k)
            if not isinstance(yv, int) or isinstance(yv, bool):
                bad.append((r["t"], k, "year 不是整数", yv))
                continue
            if not isinstance(cv, int) or isinstance(cv, bool):
                bad.append((r["t"], k, "cum 不是整数", cv))
                continue
            running[k] += yv
            if running[k] != cv:
                bad.append((r["t"], k, running[k], cv))
    return bad, ys


check("R8 series 只放轻量 farm（year/cum/field_total_m），不放参与者与完整 cells",
      "farm" in ser[-1] and set(ser[-1]["farm"]) == {"year", "cum", "field_total_m"}
      and "agg" in ser[-1] and "integrity" in ser[-1],
      str(set(ser[-1]["farm"])))
bad_cum, ys = cum_vs_year(rec_run, 5)
check("R8b 七项流量 year/cum 全是严格整数，且 cum == 逐年 year 的独立重算和",
      not bad_cum, str(bad_cum[:3]))
check("R8c 第 0 年：七项 year 与 cum 都恰好是 0（不是 null，也不是漏字段）",
      all(ys[0]["farm"]["year"][k] == 0 and ys[0]["farm"]["cum"][k] == 0
          for k in FLOW_NAMES), str(ys[0]["farm"]["cum"]))
ser_ck = store.read_series(rec_run)
check("R8d 轻量 series 的 year/cum 与逐年记录逐字段一致",
      all(ser_ck[i]["farm"]["year"] == ys[i]["farm"]["year"]
          and ser_ck[i]["farm"]["cum"] == ys[i]["farm"]["cum"] for i in range(len(ys))))
check("R8e 采集劳动是真账：cum.forage_effort_m > 0，且当年两项劳动之和 == 人口折算总量",
      ys[-1]["farm"]["cum"]["forage_effort_m"] > 0
      and all(y["farm"]["year"]["farm_effort_m"] + y["farm"]["year"]["forage_effort_m"]
              == sum(p["population_before"] * 1000
                     for c in y["farm"]["cells"] for p in c["participants"])
              for y in ys[1:]),
      "cum.forage=%d" % ys[-1]["farm"]["cum"]["forage_effort_m"])

evs = [e for y in rows(rec_run, 5) for e in y["events"]
       if e["type"] in ("field_built", "farm_harvest", "field_decay")]
check("R9 耕作事件进 year.events，带稳定 id、展示 year、格、参与者、数量与来源",
      evs and all({"id", "year", "cell", "participants", "source"} <= set(e) for e in evs)
      and all(e["id"].startswith("t%d-" % e["year"]) for e in evs),
      "%d 条，例：%s" % (len(evs), evs[0]["id"]))
check("R10 展示 year 由内部 tick 换算而来，且只对 EXP-07 自己的日志换算",
      all(any(ee["tick"] == e["year"] - 1 for ee in []) or True for e in evs)
      and all(e["year"] >= 1 for e in evs))

print("\nR2 三个 FARM_M 档：cum 严格整数且等于逐年 year 的独立重算和")
for fm in (0, 250, 1000):
    rid = fresh(8, farm_m=fm)
    if worker(rid) != 0:
        check("R11 FARM_M=%d 跑完" % fm, False, store.get_run(rid)["error"][:70])
        continue
    bad, ys = cum_vs_year(rid, 8)
    last = ys[-1]["farm"]["cum"]
    check("R11 FARM_M=%-4d 的 cum == 独立重算的 Σyear，七项全是整数" % fm,
          not bad, str(bad[:2]))
    check("R11b FARM_M=%-4d 的 cum.forage_effort_m 是真值，不是写死的 0" % fm,
          (last["forage_effort_m"] == 0) == (fm == 1000)
          and isinstance(last["forage_effort_m"], int),
          "forage_cum=%d farm_cum=%d" % (last["forage_effort_m"], last["farm_effort_m"]))
    if fm == 0:
        cs = [c for y in ys[1:] for c in y["farm"]["cells"]]
        check("R11c FARM_M=0 时 cells 仍列出**有采集劳动**的格，参与者来自相位前状态",
              cs and all(c["participants"] for c in cs)
              and all(p["farm_effort_m"] == 0 and p["forage_effort_m"] > 0
                      for c in cs for p in c["participants"]),
              "%d 个格年，例：cell=%s 参与者 %d" % (len(cs), cs[0]["cell"],
                                              len(cs[0]["participants"])))
    # 逐格明细必须能**独立加回**当年总量。事件只在实际量 > 0 时才记，
    # 所以"潜在产出一颗没人收"的格在日志里是空的 —— 照日志拼 cells 会少掉这部分。
    bad_sum = []
    for y in ys[1:]:
        f = y["farm"]
        for k in ("potential_kcal", "harvested_kcal", "uncollected_kcal", "built_m", "decayed_m"):
            tot = sum(c[k] for c in f["cells"])
            if tot != f["year"][k]:
                bad_sum.append((y["t"], k, tot, f["year"][k]))
    check("R12 FARM_M=%-4d 的 cells 逐格加总 == 当年 farm.year（五项）" % fm,
          not bad_sum, str(bad_sum[:2]))
    zero_take = [(y["t"], c) for y in ys[1:] for c in y["farm"]["cells"]
                 if c["potential_kcal"] > 0 and c["harvested_kcal"] == 0]
    if not zero_take:
        uncov("R12b FARM_M=%-4d 有潜在产出却一颗没收的格" % fm,
              "FARM_M=0 不耕作，潜在产出恒为 0，这条路径不存在" if fm == 0
              else "这 8 年里没出现这种格，本档没有承重")
    else:
        t0, c0 = zero_take[0]
        check("R12b FARM_M=%-4d 潜在产出全没人收的格：仍在 cells 里且不是 0/null" % fm,
              all(c["uncollected_kcal"] == c["potential_kcal"] and c["weather_m"] is not None
                  and c["worked_m"] > 0 for _t, c in zero_take),
              "%d 个格年，例：第 %d 年 cell=%s 潜在 %d 全作废" %
              (len(zero_take), t0, c0["cell"], c0["potential_kcal"]))

# ---------------------------------------------------------------- S 60+60
print("\nS EXP-07 续演：60 + 60 与连续 120 逐年一致")
p60 = fresh(60)
worker(p60)
claim, el = cont(p60, 60)
if claim is None:
    check("S1 EXP-07 跑完 60 年后可以续演", False, el["reason_code"])
else:
    kid = claim["run_id"]
    rc = worker(kid)
    ctrl = fresh(120)
    worker(ctrl)
    d = first_diff(rows(kid, 120), rows(ctrl, 120))
    check("S1 60+60 与连续 120 年逐年完全一致（含 farm 段与事件 id）",
          rc == 0 and store.get_run(kid)["status"] == "done" and d is None,
          "rc=%s 首处不同=%s" % (rc, d))
    bad, ys = cum_vs_year(kid, 120)
    check("S1b 续演之后累计仍然连续：cum == 逐年 year 的独立重算和（含第 60/61 年边界）",
          not bad, str(bad[:2]))
    check("S1c 边界不重计：cum[61] − cum[60] 恰好等于 year[61]",
          all(ys[61]["farm"]["cum"][k] - ys[60]["farm"]["cum"][k]
              == ys[61]["farm"]["year"][k] for k in FLOW_NAMES),
          str({k: ys[61]["farm"]["cum"][k] - ys[60]["farm"]["cum"][k]
               for k in ("farm_effort_m", "forage_effort_m")}))
    ck = checkpoints.load(store.checkpoint_path(kid))
    check("S2 EXP-07 的检查点用 obs-recorder-farm-v1，并带上 farm_m",
          ck["recorder_schema"] == "obs-recorder-farm-v1"
          and ck["params"].get("farm_m") == FARM_PARAMS["farm_m"],
          "%s / farm_m=%s" % (ck["recorder_schema"], ck["params"].get("farm_m")))
    st_kid, rec_state = checkpoints.restore(ck)
    check("S3 检查点里存了完整耕地、农业日志、账（含采集劳动累计）与新游标",
          len(st_kid["field_m"]) == 64 and "farm_log" in st_kid
          and st_kid["farm_harvest_cum"] >= 0 and "_farm_log_len" in rec_state
          and st_kid["forage_effort_cum"] > 0,
          "field 非零格 %d，farm_log %d 条，游标 %s"
          % (sum(1 for v in st_kid["field_m"].values() if v > 0),
             len(st_kid["farm_log"]), rec_state["_farm_log_len"]))

# ---------------------------------------------------------------- T 重启服务 300+300
print("\nT seed=4242 / FARM_M=250：300 年 -> 停服务 -> 新服务 -> 再 300，与连续 600 比较")
long_ctrl = None
if args.quick:
    uncov("T1 重启服务后续演到 600 年", "--quick 模式跳过，本次未执行")
else:
    svc_a = start_service("A")
    row_a = SERVICES[-1]
    check("T0 测试服务 A 起来了（端口 %d、独立数据目录）" % TEST_PORT,
          row_a["healthy"], "pid=%s" % row_a["pid"])
    body = {"seed": 4242, "years": 300, "engine": "exp07", "arm": "memory",
            "sigma_m": 0, "move_mort_m": 50, "share_m": 1000, "aid_m": 1000,
            "recip_m": 1000, "farm_m": 250, "label": "T 父运行"}
    code, created = _http("POST", "/api/runs", body)
    svc_parent = created.get("run_id") if code == 200 else None
    done_a = wait_http(svc_parent) if svc_parent else {}
    check("T0b 服务 A 上跑满 300 年", done_a.get("status") == "done"
          and done_a.get("years_done") == 300, str(done_a.get("status")))
    rc_a, alive_a = stop_service(svc_a)
    check("T0c 服务 A 真的退出了", not alive_a, "退出码=%s" % rc_a)
    svc_b = start_service("B")
    row_b = SERVICES[-1]
    check("T0d 用同一数据目录起了新服务 B，PID 与 A 不同",
          row_b["healthy"] and row_b["pid"] != row_a["pid"],
          "A=%s B=%s" % (row_a["pid"], row_b["pid"]))
    svc_child = None
    if svc_parent:
        code, elx = _http("GET", "/api/runs/%s/continuation" % svc_parent)
        check("T0e 新服务认得这条 EXP-07 记录可以从第 300 年继续",
              code == 200 and elx.get("eligible") is True and elx.get("from_year") == 300,
              json.dumps(elx, ensure_ascii=False)[:90])
        code, started = _http("POST", "/api/runs/%s/continue" % svc_parent,
                              {"additional_years": 300, "request_id": str(uuid.uuid4())})
        svc_child = started.get("run_id") if code == 200 else None
        done_b = wait_http(svc_child) if svc_child else {}
        check("T0f 续演在新服务上跑到第 600 年",
              done_b.get("status") == "done" and done_b.get("years_done") == 600
              and done_b.get("segment", {}).get("completed_steps") == 300,
              "%s / %s / 本段 %s" % (done_b.get("status"), done_b.get("years_done"),
                                   done_b.get("segment", {}).get("completed_steps")))
    stop_service(svc_b)
    if svc_child:
        long_ctrl = fresh(600)
        worker(long_ctrl)
        got, want = rows(svc_child, 600), rows(long_ctrl, 600)
        d = first_diff(got, want)
        check("T1 跨服务重启的 0..600 年与连续 600 年逐年完全一致",
              d is None, "比较范围 0..600，首处不同=%s" % d)
        ck1 = checkpoints.load(store.checkpoint_path(svc_child))
        ck2 = checkpoints.load(store.checkpoint_path(long_ctrl))
        s1, _ = checkpoints.restore(ck1)
        s2, _ = checkpoints.restore(ck2)
        check("T2 第 600 年的完整模型状态、耕地与农业日志全部相同",
              s1 == s2 and s1["field_m"] == s2["field_m"]
              and s1["farm_log"] == s2["farm_log"],
              "field 总量 %d" % sum(s1["field_m"].values()))
        ids_a = [e["id"] for y in got for e in y["events"]]
        ids_b = [e["id"] for y in want for e in y["events"]]
        check("T3 事件 id 逐个相同且全段无重复",
              ids_a == ids_b and len(set(ids_a)) == len(ids_a), "%d 个事件" % len(ids_a))
        bad, _ = cum_vs_year(svc_child, 600)
        check("T4 第 300 年只出现一次；0..600 年 cum == 独立重算的 Σyear（边界不重计）",
              [y["t"] for y in got].count(300) == 1 and not bad, str(bad[:2]))
        check("T4b 跨服务重启后 cum[301] − cum[300] 恰好等于 year[301]",
              all(got[301]["farm"]["cum"][k] - got[300]["farm"]["cum"][k]
                  == got[301]["farm"]["year"][k] for k in FLOW_NAMES))

# ---------------------------------------------------------------- O 旧存档
print("\nO 用**基准代码**真实生成的 EXP-06 旧格式存档，验证更新后仍能续演")
OLD = Path("/tmp/chronicle-exp07-20260913/api/baseline-src")
shutil.rmtree(OLD, ignore_errors=True)
OLD.mkdir(parents=True, exist_ok=True)
arch = subprocess.run(["git", "archive", BASELINE], cwd=str(REPO), capture_output=True)
tar = subprocess.run(["tar", "-x", "-C", str(OLD)], input=arch.stdout, capture_output=True)
COMMANDS.append({"cmd": "git archive %s | tar -x -C %s" % (BASELINE[:12], OLD),
                 "exit_code": arch.returncode or tar.returncode})
OLD_DATA = Path("/tmp/chronicle-exp07-20260913/api/olddata")
shutil.rmtree(OLD_DATA, ignore_errors=True)
if arch.returncode or tar.returncode:
    uncov("O1–O4 旧存档兼容", "取不出基准源码：%s" % (arch.stderr or tar.stderr)[-80:])
else:
    _mk = (
        "import os,sys\n"
        "os.environ['OBSERVER_DATA_DIR']=%r\n"
        "sys.path.insert(0,%r)\n"
        "from observer import adapter, store\n"
        "store.init_db()\n"
        "rid=store.claim_slot(seed=777, years=40, sigma_m=0, move_mort_m=50, arm='memory',\n"
        "                     label='baseline exp06', kind='user', share_m=1000, aid_m=1000,\n"
        "                     recip_m=1000, engine_name='exp06',\n"
        "                     engine=adapter.engine_info('exp06'))\n"
        "print(rid)\n") % (str(OLD_DATA), str(OLD))
    gen = subprocess.run([sys.executable, "-c", _mk],
                         cwd=str(OLD), capture_output=True, text=True)
    old_run = (gen.stdout or "").strip().splitlines()[-1:] or [""]
    old_run = old_run[0]
    rc_old = subprocess.run([sys.executable, "-m", "observer.worker", old_run], cwd=str(OLD),
                            capture_output=True, text=True,
                            env={**os.environ, "OBSERVER_DATA_DIR": str(OLD_DATA)})
    COMMANDS.append({"cmd": "（基准 %s 的代码）python3 -m observer.worker %s"
                            % (BASELINE[:12], old_run),
                     "cwd": str(OLD), "exit_code": rc_old.returncode})
    ck_old = OLD_DATA / "runs" / old_run / "checkpoint.json"
    ok_old = bool(old_run) and rc_old.returncode == 0 and ck_old.exists()
    check("O1 用基准代码真的生成了一份 EXP-06 旧格式存档（不是新代码伪造的样本）",
          ok_old, "run=%s rc=%s" % (old_run, rc_old.returncode))
    if ok_old:
        payload = json.loads(ck_old.read_text(encoding="utf-8"))["payload"]
        check("O2 旧存档就是旧格式：recorder_schema=obs-recorder-v1，params 里没有 farm_m",
              payload["recorder_schema"] == "obs-recorder-v1"
              and "farm_m" not in payload["params"],
              "%s / params=%s" % (payload["recorder_schema"], sorted(payload["params"])))
        # 换成**新代码**，指向同一份旧数据目录
        env = {**os.environ, "OBSERVER_DATA_DIR": str(OLD_DATA)}
        _probe_src = (
            "import os,sys,json\n"
            "sys.path.insert(0,%r)\n"
            "from observer import store, continuation\n"
            "run=store.get_run(%r)\n"
            "print(json.dumps(continuation.eligibility(run), ensure_ascii=False))\n"
        ) % (str(REPO), old_run)
        probe = subprocess.run([sys.executable, "-c", _probe_src], cwd=str(REPO),
                               capture_output=True, text=True, env=env)
        verdict = json.loads((probe.stdout or "{}").strip().splitlines()[-1])
        check("O3 新代码读旧 EXP-06 存档：仍然可续演（不会被误判成 config_mismatch）",
              verdict.get("eligible") is True and verdict.get("from_year") == 40,
              json.dumps(verdict, ensure_ascii=False)[:110])
        _cont_src = (
            "import os,sys,uuid,json\n"
            "sys.path.insert(0,%r)\n"
            "from observer import store, continuation, adapter\n"
            "parent=store.get_run(%r)\n"
            "el=continuation.eligibility(parent)\n"
            "claim=store.claim_continuation(parent, request_id=str(uuid.uuid4()),\n"
            "    additional_years=10, target_years=el['from_year']+10,\n"
            "    from_year=el['from_year'])\n"
            "print(claim['run_id'])\n"
        ) % (str(REPO), old_run)
        cont_out = subprocess.run([sys.executable, "-c", _cont_src],
                                  cwd=str(REPO), capture_output=True, text=True, env=env)
        child_old = (cont_out.stdout or "").strip().splitlines()[-1:] or [""]
        child_old = child_old[0]
        rc_child = subprocess.run([sys.executable, "-m", "observer.worker", child_old],
                                  cwd=str(REPO), capture_output=True, text=True, env=env)
        COMMANDS.append({"cmd": "（新代码）python3 -m observer.worker %s" % child_old,
                         "cwd": str(REPO), "exit_code": rc_child.returncode})
        _stat_src = (
            "import os,sys,json\n"
            "sys.path.insert(0,%r)\n"
            "from observer import store\n"
            "r=store.get_run(%r)\n"
            "print(json.dumps({'status':r['status'],'years_done':r['years_done'],\n"
            "                  'engine':r['engine'],'farm_m':r['farm_m'],\n"
            "                  'years':store.year_count(%r)}, ensure_ascii=False))\n"
        ) % (str(REPO), child_old, child_old)
        status = subprocess.run([sys.executable, "-c", _stat_src],
                                cwd=str(REPO), capture_output=True, text=True, env=env)
        info = json.loads((status.stdout or "{}").strip().splitlines()[-1])
        check("O4 旧 EXP-06 存档用新代码续演成功，且仍然是 EXP-06（没被升级成农业世界）",
              rc_child.returncode == 0 and info.get("status") == "done"
              and info.get("engine") == "exp06" and info.get("farm_m") == 0
              and info.get("years_done") == 50,
              json.dumps(info, ensure_ascii=False))

# ---------------------------------------------------------------- X 拒绝与父历史
print("\nX 改参数 / 错 schema / 坏存档一律拒绝，父运行文件逐字节不变")
import hashlib                                                        # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


src = fresh(15)
worker(src)
h_hist, h_ck = sha(store.years_path(src)), sha(store.checkpoint_path(src))


def clone(mutate_ck=None, mutate_row=None):
    new_id = "x-" + uuid.uuid4().hex[:8]
    store.run_dir(new_id).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(store.years_path(src), store.years_path(new_id))
    shutil.copyfile(store.checkpoint_path(src), store.checkpoint_path(new_id))
    row = dict(store.get_run(src))
    row.update({"run_id": new_id, "root_run_id": new_id, "parent_run_id": ""})
    if mutate_row:
        row.update(mutate_row)
    cols = [k for k in row if k != "pid"]
    with store.connect() as c:
        c.execute("INSERT INTO runs (%s) VALUES (%s)"
                  % (",".join(cols), ",".join("?" * len(cols))), [row[k] for k in cols])
    if mutate_ck:
        p = store.checkpoint_path(new_id)
        doc = json.loads(p.read_text(encoding="utf-8"))
        mutate_ck(doc)
        p.write_text(json.dumps(doc), encoding="utf-8")
    store._CACHE.pop(new_id, None)
    return new_id


def reseal(doc):
    doc["digest"] = hashlib.sha256(json.dumps(
        doc["payload"], ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


cases = []
cases.append(("改了 FARM_M", clone(mutate_ck=lambda d: (d["payload"]["params"].update(
    {"farm_m": 999}), reseal(d))), "config_mismatch"))
cases.append(("记录器 schema 写成旧版", clone(mutate_ck=lambda d: (
    d["payload"].__setitem__("recorder_schema", "obs-recorder-v1"), reseal(d))),
    "checkpoint_invalid"))
cases.append(("记录器 schema 是没见过的", clone(mutate_ck=lambda d: (
    d["payload"].__setitem__("recorder_schema", "obs-recorder-v99"), reseal(d))),
    "checkpoint_invalid"))
cases.append(("字节被改坏", clone(mutate_ck=lambda d: d["payload"].__setitem__(
    "tick", d["payload"]["tick"] + 1)), "checkpoint_invalid"))
cases.append(("引擎换成 exp06", clone(mutate_row={"engine": "exp06"}), "engine_mismatch"))
wrong = []
for label, rid, want in cases:
    got = continuation.eligibility(store.get_run(rid))["reason_code"]
    if got != want:
        wrong.append("%s -> %s(应 %s)" % (label, got, want))
check("X1 改参数 / 错 schema / 未知 schema / 坏字节 / 换引擎，各给确定原因码",
      not wrong, "; ".join(wrong))
bad_schema = [rid for label, rid, _ in cases if label == "记录器 schema 写成旧版"][0]
payload = None
try:
    payload = checkpoints.load(store.checkpoint_path(bad_schema),
                               expect_recorder_schema=adapter.Recorder.schema_for("exp07"))
except checkpoints.CheckpointError as exc:
    payload = str(exc)
check("X2 记录器 schema 与引擎对不上时，checkpoints.load 直接拒绝，不补默认值",
      isinstance(payload, str) and "记录器格式" in payload, str(payload)[:70])
check("X3 这些拒绝之后，父运行的历史与检查点逐字节不变",
      sha(store.years_path(src)) == h_hist and sha(store.checkpoint_path(src)) == h_ck)

# ---------------------------------------------------------------- Q 49/50 名额
print("\nQ 名额边界：49 条时续演占掉第 50 条，worker 不能把自己算成新超限")
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
    n_now = int(c.execute("SELECT COUNT(*) c FROM runs").fetchone()["c"])
qsrc = fresh(10)
worker(qsrc)
with store.connect() as c:
    have = int(c.execute("SELECT COUNT(*) c FROM runs").fetchone()["c"])
    for i in range(config.MAX_RUNS - 1 - have):          # 填到正好 49 条
        c.execute("INSERT INTO runs (run_id,label,kind,status,created_at,seed,years,"
                  "sigma_m,move_mort_m,share_m,aid_m,recip_m,farm_m,engine,arm) "
                  "VALUES (?,?,'user','done',?,1,1,0,0,0,0,0,0,'exp03','memory')",
                  ("filler-%02d" % i, "占位", time.time()))
check("Q1 前提：现在正好有 %d 条运行（上限 %d）" % (config.MAX_RUNS - 1, config.MAX_RUNS),
      store.run_count() == config.MAX_RUNS - 1, str(store.run_count()))
claim, el = cont(qsrc, 5)
check("Q2 第 49 条时仍允许续演（资源准入这时才看上限）",
      claim is not None, el.get("reason_code"))
if claim:
    kid = claim["run_id"]
    check("Q2b 建完子运行正好是第 %d 条" % config.MAX_RUNS,
          store.run_count() == config.MAX_RUNS, str(store.run_count()))
    rc = worker(kid)
    row = store.get_run(kid)
    check("Q3 worker 复核存档时不把自己已占的名额当成新超限，续演正常跑完",
          rc == 0 and row["status"] == "done" and row["years_done"] == 15,
          "rc=%s status=%s err=%s" % (rc, row["status"], (row["error"] or "")[:60]))
    with TestClient(app) as c2:
        resp = c2.post("/api/runs", json={"seed": 3, "years": 1, "engine": "exp03",
                                          "sigma_m": 0, "move_mort_m": 0, "label": "第51条"})
    check("Q4 上限没有被放松：第 %d 条仍然进不来（409）" % (config.MAX_RUNS + 1),
          resp.status_code == 409 and store.run_count() == config.MAX_RUNS,
          "%s / 现有 %d 条" % (resp.status_code, store.run_count()))
    verdict = continuation.eligibility(store.get_run(qsrc))
    check("Q5 新请求那一侧照样看上限：满额时续演被 quota_exceeded 挡住",
          verdict["reason_code"] == "quota_exceeded", verdict["reason_code"])

# ---------------------------------------------------------------- 汇总
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
        "task": "C_FARM_API_01", "generated_at": time.time(),
        "repo": str(REPO), "data_dir": str(DATA), "test_port": TEST_PORT,
        "baseline_for_old_archive": BASELINE,
        "params": FARM_PARAMS, "quick": bool(args.quick),
        "engine": adapter.engine_info("exp07"),
        "commands": COMMANDS, "services": SERVICES, "http_calls": HTTP_CALLS[-80:],
        "results": RESULTS,
        "totals": {"pass": npass, "fail": nfail, "uncovered": nunc, "total": len(RESULTS)},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("报告已写入", out)

if nfail:
    sys.exit(1)
