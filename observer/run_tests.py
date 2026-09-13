"""OBS-01 验收测试。

沿用本项目的三态结果：PASS / FAIL / UNCOVERED。
**未覆盖不计入通过**；有必过项失败则退出码 1。
测试用独立的数据目录（observer/data_test），不碰正常运行的数据。
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
TEST_DATA = REPO / "observer" / "data_test"
os.environ["OBSERVER_DATA_DIR"] = str(TEST_DATA)          # 子进程也会读到
# 测试自己要发几十个写请求，先把限流放开；限流本身由 O22 单独测。
os.environ.setdefault("OBSERVER_WRITE_RATE", "500")
# O30 要一条**真的还在算**的运行才能验证协作取消：模型每秒能跑近千年，
# 300 年的运行在请求发出去之前就结束了。只放宽测试库的年数上限，不动默认配置。
os.environ.setdefault("OBSERVER_MAX_YEARS", "20000")
shutil.rmtree(TEST_DATA, ignore_errors=True)

from observer import adapter, config, presets, store  # noqa: E402
from observer.app import app                          # noqa: E402
from fastapi.testclient import TestClient              # noqa: E402

RESULTS = []


def record(name, state, detail=""):
    RESULTS.append((name, state, detail))
    mark = {"PASS": "PASS", "FAIL": "FAIL", "UNCOVERED": "未覆盖"}[state]
    print(f"  {name:<46} {mark}" + (f"   {detail}" if detail else ""))


def check(name, ok, detail=""):
    record(name, "PASS" if ok else "FAIL", detail)


def uncov(name, why):
    record(name, "UNCOVERED", why)


print("=" * 96)
print("OBS-01 文明观察台 —— 验收测试")
print("=" * 96)

v3, engine_sha = adapter.load_engine()
CFG = dict(seed=777, years=60, sigma_m=400, move_mort_m=50, arm="memory")
WCFG = {k: v for k, v in CFG.items() if k != "years"}   # make_world 不吃 years

# ---------------------------------------------------------------- O1 / O2
print("\nO1 记录层不干扰模型")
st_plain = adapter.make_world(**WCFG)
plain_hashes = [v3.state_hash(st_plain)]
for _ in range(CFG["years"]):
    v3.step(st_plain)
    plain_hashes.append(v3.state_hash(st_plain))
plain_digest = v3.full_digest(st_plain)
plain_keys = set(st_plain.keys())
plain_band_keys = {frozenset(b.keys()) for b in st_plain["bands"].values()}

st_rec = adapter.make_world(**WCFG)
rec = adapter.Recorder()
records = [rec.year_record(st_rec)]
rec_hashes = [v3.state_hash(st_rec)]
for _ in range(CFG["years"]):
    adapter.step(st_rec)
    records.append(rec.year_record(st_rec))
    rec_hashes.append(v3.state_hash(st_rec))
rec_digest = v3.full_digest(st_rec)

check("O1a 逐步状态哈希逐年相同", plain_hashes == rec_hashes,
      f"{len(plain_hashes)} 步全同" if plain_hashes == rec_hashes else "有差异")
check("O1b 最终 full_digest 相同", plain_digest == rec_digest, plain_digest[:24])
check("O1c 记录层没有往模型里加字段", set(st_rec.keys()) == plain_keys)
check("O1d 记录层没有往群体里加字段",
      {frozenset(b.keys()) for b in st_rec["bands"].values()} == plain_band_keys)
src = (REPO / "observer" / "adapter.py").read_text(encoding="utf-8")
check("O1e 适配层一次都没有调用引擎的 rng", ".rng(" not in src and "v3.rng" not in src)

# ---------------------------------------------------------------- O3 账本自洽
print("\nO2 指标与账本自洽（逐年）")
bad_incr = bad_pop = bad_cons = 0
for i, r in enumerate(records):
    if i:
        for k, v in r["year"].items():
            if v != r["cum"][k] - records[i - 1]["cum"][k]:
                bad_incr += 1
    c = r["cum"]
    pop_expect = (adapter.static_run_meta(st_rec)["pop_start"] + c["births_cum"]
                  - c["deaths_demo_cum"] - c["mig_deaths_cum"])
    if r["agg"]["pop"] != pop_expect:
        bad_pop += 1
    if r["integrity"]["conservation_error"] != 0:
        bad_cons += 1
check("O2a 年度增量 == 账本差值（不用净变化冒充出生/死亡）", bad_incr == 0, f"越界 {bad_incr} 处")
check("O2b 人口恒等：期末 = 期初 + 出生 − 原死亡 − 迁移死亡", bad_pop == 0, f"越界 {bad_pop} 年")
check("O2c 能量守恒误差恒为 0", bad_cons == 0, f"越界 {bad_cons} 年")

zero_mig_years = [r["t"] for r in records if r["t"] and r["year"]["mig_total"] == 0]
if zero_mig_years:
    check("O2d 分母为零的年份如实记为 0 次（前端显示“不适用”）",
          all(records[t]["year"]["mig_regret"] == 0 for t in zero_mig_years),
          f"{len(zero_mig_years)} 个零迁移年份")
else:
    uncov("O2d 分母为零的年份", "本样本 60 年里没有出现迁移次数为 0 的年份")

check("O3 实体 id 以字符串下发", all(isinstance(b["id"], str) for b in records[-1]["bands"]),
      f"{len(records[-1]['bands'])} 个群体")

# ---------------------------------------------------------------- 起服务
print("\nO4 接口与持久化")
presets.install_presets()
client = TestClient(app)
with client:
    r = client.post("/api/runs", json={"seed": CFG["seed"], "years": CFG["years"],
                                       "sigma_m": CFG["sigma_m"],
                                       "move_mort_m": CFG["move_mort_m"],
                                       "arm": CFG["arm"], "label": "验收运行"})
    check("O4a 合法参数可以启动运行", r.status_code == 200, str(r.json())[:60])
    run_id = r.json()["run_id"] if r.status_code == 200 else None

    deadline = time.time() + 60
    status = "?"
    while run_id and time.time() < deadline:
        j = client.get(f"/api/runs/{run_id}").json()
        status = j["status"]
        if status in ("done", "failed", "canceled", "interrupted"):
            break
        time.sleep(0.2)
    check("O4b 子进程算完并落盘", status == "done", f"状态={status}")

    # 与直接跑模型的结果对齐（任取三个年份）
    picks = [0, CFG["years"] // 2, CFG["years"]]
    mismatch = []
    for t in picks:
        got = client.get(f"/api/runs/{run_id}/year/{t}").json()
        want = records[t]
        for field in ("agg", "cum", "year", "integrity"):
            if got[field] != want[field]:
                mismatch.append((t, field))
        if [b["id"] for b in got["bands"]] != [b["id"] for b in want["bands"]]:
            mismatch.append((t, "bands"))
        if got["stock"] != want["stock"]:
            mismatch.append((t, "stock"))
    check("O5 任选三个年份与独立重跑的快照/账本完全一致", not mismatch,
          f"年份 {picks} 全对" if not mismatch else str(mismatch))

    digest_api = client.get(f"/api/runs/{run_id}").json()["full_digest"]
    check("O5b 服务端记录的 full_digest == 直接跑模型的结果", digest_api == plain_digest,
          digest_api[:24])

    # 回放只读：反复读、乱序读，不改数据也不触发计算
    p = store.years_path(run_id)
    before = (p.stat().st_mtime_ns, p.stat().st_size)
    seq = [client.get(f"/api/runs/{run_id}/year/{t}").json() for t in (7, 3, 30, 3, 7)]
    after = (p.stat().st_mtime_ns, p.stat().st_size)
    check("O6a 反复/乱序回放返回完全相同的记录",
          seq[1] == seq[3] and seq[0] == seq[4])
    check("O6b 回放不改写历史（文件 mtime 与大小不变）", before == after)
    st_after = adapter.make_world(**WCFG)
    for _ in range(CFG["years"]):
        adapter.step(st_after)
    check("O6c 回放期间模型结果不变（重算一遍仍是同一 digest）",
          v3.full_digest(st_after) == plain_digest)

    # 非法输入
    bad_cases = [({"seed": 0, "years": 10 ** 6}, 400), ({"seed": -1, "years": 10}, 400),
                 ({"seed": 0, "years": 10, "sigma_m": 1001}, 400),
                 ({"seed": 0, "years": 10, "move_mort_m": -1}, 400),
                 ({"seed": 0, "years": 10, "arm": "god"}, 400),
                 ({"seed": 0, "years": 1.5}, 422), ({"seed": True, "years": 10}, 422)]
    got_codes = [client.post("/api/runs", json=b).status_code for b, _ in bad_cases]
    check("O7a 非法参数被服务端拒绝", got_codes == [c for _, c in bad_cases], str(got_codes))
    check("O7b 越界年份返回 404",
          client.get(f"/api/runs/{run_id}/year/99999").status_code == 404)
    check("O7c 不存在的运行返回 404", client.get("/api/runs/nope/year/0").status_code == 404)

    # 单并发：占槽的必须是**真的还活着**的工作进程。
    # （槽被死记录占着时，现在会被 reap_stale 回收——那是 O19 的事，不是 409。）
    holder = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)", "observer.worker", run_id])
    time.sleep(0.6)
    store.set_pid(run_id, holder.pid)
    store.force_status(run_id, "running")
    dup = client.post("/api/runs", json={"seed": 1, "years": 5})
    check("O8 有活着的任务在跑时拒绝重复启动", dup.status_code == 409, str(dup.json())[:60])
    holder.kill()
    time.sleep(0.4)
    store.force_status(run_id, "running", pid=holder.pid)

    # 重启恢复
    n = store.recover_interrupted()
    after_status = client.get(f"/api/runs/{run_id}").json()["status"]
    check("O9 重启后未完成任务被标为中断（不假装续跑）",
          n >= 1 and after_status == "interrupted", f"{n} 个 → {after_status}")
    check("O9b 中断的运行仍可回放已算出的年份",
          client.get(f"/api/runs/{run_id}/year/5").status_code == 200)

    # 鉴权
    config.TOKEN = "test-secret"
    try:
        check("O10a 设了令牌后，写操作无令牌被拒",
              client.post("/api/runs", json={"seed": 1, "years": 5}).status_code == 401)
        check("O10b 设了令牌后，读接口无令牌被拒",
              client.get("/api/runs").status_code == 401)
        ok = client.get("/api/runs", headers={"X-Observer-Token": "test-secret"})
        check("O10c 带正确令牌可以读", ok.status_code == 200)
    finally:
        config.TOKEN = ""

    # 预生成案例
    runs = client.get("/api/runs").json()["runs"]
    pre = [r for r in runs if r["kind"] == "preset"]
    check("O11 预生成案例存在且被标记为 preset（不冒充实时任务）",
          len(pre) >= 1 and all(p["status"] == "done" for p in pre),
          str([p["run_id"] for p in pre]))

# ---------------------------------------------------------------- 并发与状态转换
print("\nO13 任务槽与状态转换")
import threading  # noqa: E402

got = []
barrier = threading.Barrier(2)


def _claim(tag):
    barrier.wait()
    got.append(store.claim_slot(seed=1, years=5, sigma_m=0, move_mort_m=0, arm="memory",
                                label=f"并发{tag}", kind="user", engine=adapter.engine_info()))


with store.connect() as c:                      # 先清空任务槽
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
ths = [threading.Thread(target=_claim, args=(i,)) for i in range(2)]
[t.start() for t in ths]
[t.join() for t in ths]
won = [g for g in got if g]
check("O13a 两个同时占槽的请求只有一个成功", len(won) == 1, f"结果={got}")
slot = won[0] if won else None

if slot:
    fake_pid = os.getpid()
    check("O13b 工作进程 queued->running 只能成功一次",
          store.worker_begin(slot, fake_pid) and not store.worker_begin(slot, fake_pid))
    store.set_pid(slot, fake_pid)
    check("O13c 写 pid 不会把 running 打回 queued",
          store.get_run(slot)["status"] == "running", store.get_run(slot)["status"])
    store.force_status(slot, "interrupted")      # 模拟服务端判定中断
    ok_done = store.worker_finish(slot, fake_pid, "done", years_done=5)
    check("O13d 被判中断后，旧工作进程改不回 done",
          (not ok_done) and store.get_run(slot)["status"] == "interrupted",
          f"finish={ok_done} 状态={store.get_run(slot)['status']}")
    check("O13e 被判中断后，进度写入也被拒绝",
          not store.worker_progress(slot, fake_pid, 99))
else:
    uncov("O13b–e 状态围栏", "没有拿到任务槽，前提缺失")

# 真的起一个“假装是工作进程”的活进程，验证重启恢复会先停掉它再标中断
live_run = store.claim_slot(seed=2, years=5, sigma_m=0, move_mort_m=0, arm="memory",
                            label="活进程", kind="user", engine=adapter.engine_info())
if live_run is None:
    with store.connect() as c:
        c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
    live_run = store.claim_slot(seed=2, years=5, sigma_m=0, move_mort_m=0, arm="memory",
                                label="活进程", kind="user", engine=adapter.engine_info())
if live_run:
    stand_in = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)", "observer.worker", live_run])
    time.sleep(0.6)
    store.set_pid(live_run, stand_in.pid)
    store.worker_begin(live_run, stand_in.pid)
    check("O14a 能认出这次运行的活工作进程",
          store._is_our_worker(stand_in.pid, live_run))
    n_rec = store.recover_interrupted()
    time.sleep(0.3)
    alive_after = store._is_our_worker(stand_in.pid, live_run)
    check("O14b 重启恢复会先停掉旧进程再标中断",
          (not alive_after) and store.get_run(live_run)["status"] == "interrupted",
          f"仍活着={alive_after} 状态={store.get_run(live_run)['status']}")
    check("O14c 旧进程即使漏网也改不回 done",
          not store.worker_finish(live_run, stand_in.pid, "done", years_done=5))
    if stand_in.poll() is None:
        stand_in.kill()
else:
    uncov("O14 重启恢复停旧进程", "没拿到任务槽，前提缺失")

# ---------------------------------------------------------------- 半条记录
print("\nO15 只承认写完整的记录")
probe = "partial-probe"
store.run_dir(probe).mkdir(parents=True, exist_ok=True)
full = [json.dumps({"t": i, "stock": [1], "bands": [], "cum": {}, "year": {},
                    "agg": {"pop": i}, "integrity": {}, "events": []},
                   separators=(",", ":")) for i in range(4)]
fp = store.years_path(probe)
cases = [("完整 4 条", "\n".join(full) + "\n", 4),
         ("末尾半条", "\n".join(full) + "\n" + '{"t":4,"stock":[1],"ban', 4),
         ("末尾缺字段", "\n".join(full) + "\n" + '{"t":4}\n', 4),
         ("t 错位", "\n".join(full) + "\n" + full[0] + "\n", 4),
         ("空文件", "", 0),
         ("只有半条", '{"t":0,"sto', 0)]
bad = []
for name, text, want in cases:
    fp.write_text(text, encoding="utf-8")
    if store.year_count(probe) != want or len(store.read_series(probe)) != want:
        bad.append(name)
check("O15a 半条 / 缺字段 / 错位记录都不计入已完成年份", not bad, str(bad))
fp.write_text("\n".join(full) + "\n" + '{"t":4,"stock":[1],"ban', encoding="utf-8")
check("O15b 已完整保存的历史仍可读", store.read_year(probe, 3)["agg"]["pop"] == 3)
check("O15c 半条那一年读不到（不是读到半个）", store.read_year(probe, 4) is None)

# ---------------------------------------------------------------- 接口不被半条记录打爆
print("\nO16 接口层：运行中读取、半条记录、并发启动")
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
client2 = TestClient(app)
with client2:
    # 并发启动：两个请求同时打
    results = []
    b2 = threading.Barrier(2)

    def _post(i):
        b2.wait()
        r = client2.post("/api/runs", json={"seed": 7, "years": 300, "sigma_m": 0,
                                            "move_mort_m": 0, "arm": "memory",
                                            "label": f"并发启动{i}"})
        results.append(r.status_code)

    ts = [threading.Thread(target=_post, args=(i,)) for i in range(2)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    check("O16a 两个同时到达的启动请求只有一个成功",
          sorted(results) == [200, 409], str(results))

    live = store.active_run() or next(
        (r for r in store.list_runs() if r["label"].startswith("并发启动")), None)
    rid2 = live["run_id"] if live else None

    # 运行中读取：边算边读，不能有 5xx；series 任何时候都要正常返回
    calls, during, early404 = [], 0, 0
    deadline = time.time() + 60
    while rid2 and time.time() < deadline:
        st_now = client2.get(f"/api/runs/{rid2}").json()
        calls.append(("series", client2.get(f"/api/runs/{rid2}/series").status_code))
        yc = client2.get(f"/api/runs/{rid2}/year/0").status_code
        calls.append(("year0", yc))
        if yc == 404 and st_now["years_recorded"] == 0:
            early404 += 1          # 第 0 年还没写出来，404 是正确答案，不是错误
        if st_now["status"] == "running":
            during += 1
        if st_now["status"] in ("done", "failed", "canceled", "interrupted"):
            break
        time.sleep(0.01)
    server_err = [c for _, c in calls if c >= 500]
    series_bad = [c for k, c in calls if k == "series" and c != 200]
    year_bad = [c for k, c in calls if k == "year0" and c not in (200, 404)]
    check("O16b 运行中读取没有 5xx，series 始终可用",
          not server_err and not series_bad and not year_bad,
          f"{len(calls)} 次请求；5xx={server_err} series异常={series_bad} year异常={year_bad}")
    check("O16b2 第 0 年未写出前的 404 是如实回答，写出后必为 200",
          client2.get(f"/api/runs/{rid2}/year/0").status_code == 200,
          f"算完前出现 {early404} 次合理 404")
    if during:
        check("O16c 至少读到过一次“运行中”的状态", True, f"{during} 次")
    else:
        uncov("O16c 运行中读取", "这次运行太快，轮询没赶上 running 状态")

    if rid2:
        # 人为把尾巴截半，接口仍要正常工作
        pth = store.years_path(rid2)
        raw = pth.read_text(encoding="utf-8")
        pth.write_text(raw + '{"t":9999,"stock":[1],"ban', encoding="utf-8")
        full_years = raw.count("\n") - 1
        s_code = client2.get(f"/api/runs/{rid2}/series").status_code
        y_ok = client2.get(f"/api/runs/{rid2}/year/{full_years}").status_code
        y_bad = client2.get(f"/api/runs/{rid2}/year/{full_years + 1}").status_code
        listed = next(r for r in client2.get("/api/runs").json()["runs"]
                      if r["run_id"] == rid2)["years_recorded"]
        check("O16d 尾部半条不会让 series 报 500", s_code == 200, f"code={s_code}")
        check("O16e 完整年份照读，半条那年 404",
              y_ok == 200 and y_bad == 404, f"{y_ok}/{y_bad}")
        check("O16f 列表里的已完成年数不含半条", listed == full_years,
              f"{listed} vs {full_years}")
    else:
        uncov("O16d–f 半条记录的接口表现", "没有可用的运行")

    # 备注原样保存（转义是显示层的事，服务端不篡改）
    with store.connect() as c:
        c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
    payload = '<img src=x onerror="alert(1)">'
    r = client2.post("/api/runs", json={"seed": 3, "years": 1, "sigma_m": 0,
                                        "move_mort_m": 0, "arm": "memory", "label": payload})
    if r.status_code == 200:
        rid3 = r.json()["run_id"]
        for _ in range(200):
            if store.get_run(rid3)["status"] in ("done", "failed", "interrupted", "canceled"):
                break
            time.sleep(0.05)
        listed = next(x for x in client2.get("/api/runs").json()["runs"]
                      if x["run_id"] == rid3)
        check("O17 备注原样保存，不在服务端被改写", listed["label"] == payload,
              listed["label"][:30])
    else:
        uncov("O17 备注原样保存", f"启动失败 {r.status_code}")

# ---------------------------------------------------------------- 任务槽回收
print("\nO19 任务槽回收（进程没了就不该继续占着槽）")
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")

DEAD_PID = 999999
r1 = store.claim_slot(seed=11, years=5, sigma_m=0, move_mort_m=0, arm="memory",
                      label="死进程", kind="user", engine=adapter.engine_info())
store.set_pid(r1, DEAD_PID)
store.worker_begin(r1, DEAD_PID)
before = store.get_run(r1)["status"]
reaped = store.reap_stale()
check("O19a running 但进程已不在 -> 回收为中断",
      before == "running" and store.get_run(r1)["status"] == "interrupted",
      f"{before} -> {store.get_run(r1)['status']}")
check("O19b 回收后任务槽真的空了", store.active_run() is None)

r2 = store.claim_slot(seed=12, years=5, sigma_m=0, move_mort_m=0, arm="memory",
                      label="刚排队", kind="user", engine=adapter.engine_info())
store.reap_stale()
check("O19c 刚建的 queued 在宽限期内不被回收",
      store.get_run(r2)["status"] == "queued", store.get_run(r2)["status"])
with store.connect() as c:                       # 把创建时间推回去，模拟“进程始终没起来”
    c.execute("UPDATE runs SET created_at=? WHERE run_id=?",
              (time.time() - config.QUEUE_GRACE_SEC - 5, r2))
store.reap_stale()
check("O19d 超过宽限期仍无进程接手 -> 回收",
      store.get_run(r2)["status"] == "interrupted", store.get_run(r2)["status"])

r3 = store.claim_slot(seed=13, years=5, sigma_m=0, move_mort_m=0, arm="memory",
                      label="活进程占槽", kind="user", engine=adapter.engine_info())
stand_in2 = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(60)", "observer.worker", r3])
time.sleep(0.6)
store.set_pid(r3, stand_in2.pid)
store.worker_begin(r3, stand_in2.pid)
store.reap_stale()
check("O19e 活着的工作进程不会被误回收",
      store.get_run(r3)["status"] == "running", store.get_run(r3)["status"])
stand_in2.kill()
time.sleep(0.4)
store.reap_stale()
check("O19f 进程被杀之后才回收",
      store.get_run(r3)["status"] == "interrupted", store.get_run(r3)["status"])

client3 = TestClient(app)
with client3:
    # 注意顺序：先让服务启动（启动恢复在这时已经跑完），**之后**再造一条“死进程占槽”的记录。
    # 否则这条记录会被启动恢复顺手清掉，测的就不是运行期的任务槽回收了。
    with store.connect() as c:
        c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
    r4 = store.claim_slot(seed=14, years=5, sigma_m=0, move_mort_m=0, arm="memory",
                          label="接口层回收", kind="user", engine=adapter.engine_info())
    store.set_pid(r4, DEAD_PID)
    store.worker_begin(r4, DEAD_PID)
    check("O19g0 前提：槽确实被一条死记录占着",
          (store.active_run() or {}).get("run_id") == r4)
    resp = client3.post("/api/runs", json={"seed": 15, "years": 3})
    check("O19g 接口层：死记录被回收后新运行能启动", resp.status_code == 200,
          f"{resp.status_code} {str(resp.json())[:60]}")
    if resp.status_code == 200:
        nrid = resp.json()["run_id"]
        for _ in range(200):
            if store.get_run(nrid)["status"] in ("done", "failed", "canceled", "interrupted"):
                break
            time.sleep(0.05)
        check("O19h 新运行正常跑完", store.get_run(nrid)["status"] == "done",
              store.get_run(nrid)["status"])

# ---------------------------------------------------------------- 状态转换表
print("\nO20 状态转换表：终态不可逆")
rt = store.claim_slot(seed=16, years=3, sigma_m=0, move_mort_m=0, arm="memory",
                      label="转换表", kind="user", engine=adapter.engine_info())
store.force_status(rt, "done")
bad_moves = {
    "done -> queued": store.transition(rt, "queued"),
    "done -> running": store.transition(rt, "running"),
    "done -> failed": store.transition(rt, "failed"),
}
check("O20a 终态不能回到 queued / running / failed",
      not any(bad_moves.values()), str(bad_moves))
check("O20b 终态记录的状态没有被改动", store.get_run(rt)["status"] == "done")
store.force_status(rt, "queued")
check("O20c queued -> running 合法", store.transition(rt, "running"))
check("O20d running -> done 合法", store.transition(rt, "done", years_done=3))
check("O20e done 之后再 running 不合法", not store.transition(rt, "running"))
store.force_status(rt, "done")

# ---------------------------------------------------------------- meta 原子性
print("\nO21 meta.json：原子写 + 容错读")
rm_ = store.claim_slot(seed=17, years=2, sigma_m=0, move_mort_m=0, arm="memory",
                       label="meta", kind="user", engine=adapter.engine_info())
store.force_status(rm_, "done")
store.write_meta(rm_, {"cell_ids": [0, 1], "cap": [1, 2]})
leftovers = list(store.run_dir(rm_).glob("*.tmp"))
check("O21a 写完没有留下临时文件", not leftovers, str(leftovers))
store.meta_path(rm_).write_text('{"cell_ids":[0,1],"cap":[73000', encoding="utf-8")
check("O21b 半个 meta.json 读成 None，不抛异常", store.read_meta(rm_) is None)
with TestClient(app) as c4:
    rr = c4.get(f"/api/runs/{rm_}")
    check("O21c 半个 meta.json 不会把接口打成 500",
          rr.status_code == 200 and rr.json()["meta"] is None, str(rr.status_code))
store.write_meta(rm_, {"cell_ids": [0, 1], "cap": [1, 2]})
check("O21d 重写之后又能正常读回", (store.read_meta(rm_) or {}).get("cap") == [1, 2])

# ---------------------------------------------------------------- EXP-04 接入
print("\nO24 EXP-04 引擎接入观察台（信息交换事件可展示）")
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
with TestClient(app) as c6:
    cfg = c6.get("/api/config").json()
    check("O24a /api/config 里有 exp04 引擎",
          "exp04" in cfg.get("engines", {}), str(sorted(cfg.get("engines", {}))))
    bad = c6.post("/api/runs", json={"seed": 1, "years": 5, "engine": "exp03",
                                     "share_m": 500})
    check("O24b exp03 引擎不接受 SHARE_M", bad.status_code == 400, str(bad.json())[:60])
    bad2 = c6.post("/api/runs", json={"seed": 1, "years": 5, "engine": "exp99"})
    check("O24c 未登记的引擎被拒", bad2.status_code == 400)
    bad3 = c6.post("/api/runs", json={"seed": 1, "years": 5, "engine": "exp04",
                                      "share_m": 1001})
    check("O24d SHARE_M 越界被拒", bad3.status_code == 400)

    r = c6.post("/api/runs", json={"seed": 4242, "years": 120, "sigma_m": 400,
                                   "move_mort_m": 50, "engine": "exp04",
                                   "share_m": 1000, "label": "EXP-04 接入"})
    check("O24e exp04 运行可以启动", r.status_code == 200, str(r.json())[:60])
    if r.status_code == 200:
        rid4 = r.json()["run_id"]
        for _ in range(600):
            row = store.get_run(rid4)
            if row["status"] in ("done", "failed", "canceled", "interrupted"):
                break
            time.sleep(0.05)
        check("O24f exp04 运行跑完", row["status"] == "done",
              f"{row['status']} {row['error'][:40]}")
        yr = c6.get(f"/api/runs/{rid4}/year/{row['years_done']}").json()
        share_events = [e for e in yr["events"] if e["type"] == "share"]
        # 找一年确实有交换事件的
        found = None
        for t in range(row["years_done"] + 1):
            rec = c6.get(f"/api/runs/{rid4}/year/{t}").json()
            ev = [e for e in rec["events"] if e["type"] == "share"]
            if ev:
                found = (t, rec, ev)
                break
        check("O24g 年份记录里带信息账（share 段）", "share" in yr, str(list(yr)[:9]))
        check("O24h 信息账恒等误差为 0",
              yr["integrity"].get("share_ledger_error") == 0,
              str(yr["integrity"].get("share_ledger_error")))
        if found:
            t, rec, ev = found
            e0 = ev[0]
            ok_fields = all(k in e0 for k in ("donor", "receiver", "cell", "mem_cell",
                                              "value", "memt", "source", "text"))
            print(f"      第 {t} 年的一条交换事件：{e0['text'][:70]}")
            check("O24i 交换事件带齐“哪一年/谁传给谁/传的什么/原时戳/来源”", ok_fields,
                  str(sorted(e0)))
            check("O24j 交换事件的双方 id 是字符串",
                  isinstance(e0["donor"], str) and isinstance(e0["receiver"], str))
        else:
            uncov("O24i 交换事件字段", "这次运行里没有出现交换事件，前提缺失")
        # 兼容性：exp03 的运行不应该带 share 段
        pre = next(x for x in c6.get("/api/runs").json()["runs"]
                   if x["kind"] == "preset" and (x.get("engine") or "exp03") == "exp03")
        rec3 = c6.get(f"/api/runs/{pre['run_id']}/year/1").json()
        check("O24k exp03 的记录里没有 share 段（前端要容忍缺席）", "share" not in rec3)

# ---------------------------------------------------------------- EXP-05 接入
print("\nO25 EXP-05 引擎接入观察台（食物援助事件可展示）")
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
with TestClient(app) as c7:
    cfg = c7.get("/api/config").json()
    check("O25a /api/config 里有 exp05 引擎",
          "exp05" in cfg.get("engines", {}), str(sorted(cfg.get("engines", {}))))
    b1 = c7.post("/api/runs", json={"seed": 1, "years": 5, "engine": "exp04", "aid_m": 500})
    check("O25b exp04 引擎不接受 AID_M", b1.status_code == 400, str(b1.json())[:60])
    b2 = c7.post("/api/runs", json={"seed": 1, "years": 5, "engine": "exp05", "aid_m": 1001})
    check("O25c AID_M 越界被拒", b2.status_code == 400)
    b3 = c7.post("/api/runs", json={"seed": 1, "years": 5, "engine": "exp05", "aid_m": 1.5})
    check("O25d AID_M 非整数被拒（422）", b3.status_code == 422)

    r = c7.post("/api/runs", json={"seed": 4242, "years": 300, "sigma_m": 400,
                                   "move_mort_m": 50, "engine": "exp05",
                                   "share_m": 1000, "aid_m": 1000, "label": "EXP-05 接入"})
    check("O25e exp05 运行可以启动", r.status_code == 200, str(r.json())[:60])
    if r.status_code == 200:
        rid5 = r.json()["run_id"]
        for _ in range(900):
            row = store.get_run(rid5)
            if row["status"] in ("done", "failed", "canceled", "interrupted"):
                break
            time.sleep(0.05)
        check("O25f exp05 运行跑完", row["status"] == "done",
              f"{row['status']} {row['error'][:40]}")
        check("O25g 台账记下了 aid_m 与引擎", row["aid_m"] == 1000 and row["engine"] == "exp05")
        found = None
        for t in range(row["years_done"] + 1):
            rec = c7.get(f"/api/runs/{rid5}/year/{t}").json()
            ev = [e for e in rec["events"] if e["type"] == "aid"]
            if ev:
                found = (t, rec, ev); break
        if found:
            t, rec, ev = found
            e0 = ev[0]
            print(f"      第 {t} 年的一条援助事件：{e0['text'][:74]}")
            check("O25h 援助事件带齐“哪一年/谁给谁/多少/地点/来源”",
                  all(k in e0 for k in ("donor", "receiver", "cell", "kcal",
                                        "person_years", "source", "text")),
                  str(sorted(e0)))
            check("O25i 数量标了单位（kcal + 人年口粮换算）",
                  isinstance(e0["kcal"], int) and e0["kcal"] > 0)
            check("O25j 双方 id 是字符串",
                  isinstance(e0["donor"], str) and isinstance(e0["receiver"], str))
            check("O25k 年份记录带 aid 段，且活动数与笔数是两个计数",
                  "aid" in rec and rec["aid"]["transfers"] >= rec["aid"]["events"] >= 1,
                  str(rec["aid"]))
            check("O25l 援助账恒等误差为 0", rec["integrity"].get("aid_ledger_error") == 0)
        else:
            uncov("O25h–l 援助事件", "这次运行里没有出现援助事件，前提缺失")
        pre3 = next(x for x in c7.get("/api/runs").json()["runs"]
                    if x["kind"] == "preset" and (x.get("engine") or "exp03") == "exp03")
        rec3 = c7.get(f"/api/runs/{pre3['run_id']}/year/1").json()
        check("O25m exp03 的记录里没有 aid 段（前端要容忍缺席）", "aid" not in rec3)

# ---------------------------------------------------------------- EXP-06 接入
print("\nO26 EXP-06 引擎接入观察台（援助记忆与优先回助可展示）")
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
with TestClient(app) as c8:
    cfg = c8.get("/api/config").json()
    check("O26a /api/config 里有 exp06 引擎",
          "exp06" in cfg.get("engines", {}), str(sorted(cfg.get("engines", {}))))
    b1 = c8.post("/api/runs", json={"seed": 1, "years": 5, "engine": "exp05", "recip_m": 500})
    check("O26b exp05 引擎不接受 RECIP_M", b1.status_code == 400, str(b1.json())[:60])
    b2 = c8.post("/api/runs", json={"seed": 1, "years": 5, "engine": "exp06", "recip_m": 1001})
    check("O26c RECIP_M 越界被拒", b2.status_code == 400)
    b3 = c8.post("/api/runs", json={"seed": 1, "years": 5, "engine": "exp06", "recip_m": True})
    check("O26d RECIP_M 非整数被拒（422）", b3.status_code == 422)

    r = c8.post("/api/runs", json={"seed": 4242, "years": 300, "sigma_m": 400,
                                   "move_mort_m": 50, "engine": "exp06", "share_m": 1000,
                                   "aid_m": 1000, "recip_m": 1000, "label": "EXP-06 接入"})
    check("O26e exp06 运行可以启动", r.status_code == 200, str(r.json())[:60])
    if r.status_code == 200:
        rid6 = r.json()["run_id"]
        for _ in range(900):
            row = store.get_run(rid6)
            if row["status"] in ("done", "failed", "canceled", "interrupted"):
                break
            time.sleep(0.05)
        check("O26f exp06 运行跑完", row["status"] == "done",
              f"{row['status']} {row['error'][:40]}")
        check("O26g 台账记下了 recip_m", row["recip_m"] == 1000)
        found = rel = None
        for t in range(row["years_done"] + 1):
            rec = c8.get(f"/api/runs/{rid6}/year/{t}").json()
            ev = [e for e in rec["events"] if e["type"] == "aid"]
            if ev and found is None:
                found = (t, rec, ev)
            withmem = [b for b in rec["bands"] if b.get("aid_memory")]
            if withmem and rel is None:
                rel = (t, withmem[0])
            if found and rel:
                break
        if found:
            t, rec, ev = found
            e0 = ev[0]
            print(f"      第 {t} 年的一条援助事件：{e0['text'][:80]}")
            check("O26h 援助事件带上了阶段与回助标记",
                  "phase" in e0 and "repay" in e0, str(sorted(e0)))
            check("O26i 年份记录带 recip 段（含'分配改变'与'回助'两个不同计数）",
                  "recip" in rec and {"changed", "repay_transfers", "transfers"}
                  <= set(rec["recip"]), str(rec.get("recip"))[:90])
            check("O26j 记忆账恒等误差为 0",
                  rec["integrity"].get("aid_memory_error") == 0)
        else:
            uncov("O26h–j 援助事件与 recip 段", "这次运行里没有援助事件，前提缺失")
        if rel:
            t, band = rel
            k0 = sorted(band["aid_memory"])[0]
            print(f"      第 {t} 年 {band['name']} 的关系记录：{k0[:8]}… "
                  f"{band['aid_memory'][k0]}")
            check("O26k 关系记录可展示（谁以前帮过我、累计多少、最近哪一年）",
                  isinstance(k0, str)
                  and {"kcal", "last_year"} <= set(band["aid_memory"][k0]))
        else:
            uncov("O26k 关系记录", "这次运行里没有群体积累过援助记忆，前提缺失")
        pre = next(x for x in c8.get("/api/runs").json()["runs"]
                   if x["kind"] == "preset" and (x.get("engine") or "exp03") == "exp03")
        rec3 = c8.get(f"/api/runs/{pre['run_id']}/year/1").json()
        check("O26l exp03 的记录里没有 recip 段、群体也没有 aid_memory（前端要容忍缺席）",
              "recip" not in rec3 and "aid_memory" not in rec3["bands"][0])

# ---------------------------------------------------------------- 游戏界面要用的数据
print("\nO27 供界面直接使用的数据：稳定 id / 回助依据 / 分配对照 / 能力表 / 对照案例")
with TestClient(app) as c9:
    cfg = c9.get("/api/config").json()
    spec = {p["name"]: p for p in cfg["engines"]["exp06"]["params"]}
    check("O27a 引擎能力表给出范围/默认/单位",
          {"seed", "years", "sigma_m", "move_mort_m", "share_m", "aid_m", "recip_m"}
          <= set(spec) and spec["recip_m"]["max"] == 1000
          and spec["recip_m"]["unit"] and spec["recip_m"]["min"] == 0,
          str(spec.get("recip_m"))[:80])
    check("O27b 契约版本升到 obs-1.9", cfg["api_version"] == "obs-1.9", cfg["api_version"])

    runs = {r["run_id"]: r for r in c9.get("/api/runs").json()["runs"]}
    pair = ["preset-exp06-recip0", "preset-exp06-recip1000"]
    check("O27c 两条开/关优先回助的对照案例已装入且标为预生成",
          all(k in runs and runs[k]["kind"] == "preset" and runs[k]["engine"] == "exp06"
              for k in pair) and runs[pair[0]]["recip_m"] == 0
          and runs[pair[1]]["recip_m"] == 1000,
          str([(k, runs[k]["recip_m"]) for k in pair if k in runs]))

    # 预置案例必须记**自己那个引擎**的代码版本（曾经错记成默认引擎的，本轮修）
    eng_sha = {n: adapter.engine_info(n)["engine_sha256"] for n in ("exp03", "exp06")}
    bad_id = [k for k in pair if runs.get(k, {}).get("engine_sha256") != eng_sha["exp06"]]
    check("O27c2 预置案例记的是自己引擎的 sha256，不是默认引擎的",
          not bad_id, str([(k, runs[k]["engine_sha256"][:12]) for k in pair if k in runs]))

    detail = c9.get(f"/api/runs/{pair[1]}").json()
    pu = {x["name"]: x for x in detail.get("params_used", [])}
    check("O27d 单条运行返回实际引擎/参数/代码版本/状态",
          detail["engine"] == "exp06" and pu.get("recip_m", {}).get("value") == 1000
          and detail["engine_sha256"] and detail["status"] == "done"
          and pu["recip_m"]["unit"], str(list(pu))[:70])

    # 稳定 id：反复读同一年，id 必须一样；不同年份/类型不重复
    y1 = c9.get(f"/api/runs/{pair[1]}/year/118").json()
    y2 = c9.get(f"/api/runs/{pair[1]}/year/118").json()
    ids = [e["id"] for e in y1["events"]]
    check("O27e 事件有稳定标识且当年不重复",
          ids and ids == [e["id"] for e in y2["events"]] and len(set(ids)) == len(ids),
          str(ids[:4]))
    check("O27f 事件带年份、类型、对象、地点、来源",
          all({"year", "type", "source"} <= set(e) for e in y1["events"]))

    # 回助事件：必须挂上作为依据的历史援助记录。
    # **注意**：预置案例是早先写好的 JSON，只读它验证不了当前代码路径，
    # 所以这里现跑一条同配置的运行（工作进程会用当前的 adapter 生成记录）。
    with store.connect() as _c:
        _c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
    live = c9.post("/api/runs", json={"seed": 777, "years": 150, "sigma_m": 0,
                                      "move_mort_m": 50, "engine": "exp06",
                                      "share_m": 1000, "aid_m": 1000, "recip_m": 1000,
                                      "label": "O27 实时核对"})
    live_id = live.json().get("run_id") if live.status_code == 200 else None
    if live_id:
        for _ in range(900):
            if store.get_run(live_id)["status"] in ("done", "failed", "canceled",
                                                    "interrupted"):
                break
            time.sleep(0.05)
    repay = None
    if live_id and store.get_run(live_id)["status"] == "done":
        for t in range(0, 151):
            rec = c9.get(f"/api/runs/{live_id}/year/{t}").json()
            hit = [e for e in rec["events"] if e["type"] == "aid" and e.get("repay")]
            if hit:
                repay = (t, rec, hit[0]); break
    if repay is None:
        uncov("O27g 回助事件的依据链接", "实时运行里没有回助事件，前提缺失")
    else:
        t, rec, e0 = repay
        basis = e0.get("basis", {})
        prior_ok = bool(basis.get("prior_events"))
        for pid in basis.get("prior_events", []):
            py = int(pid.split("-")[0][1:])
            prec = c9.get(f"/api/runs/{live_id}/year/{py}").json()
            src = [x for x in prec["events"] if x["id"] == pid]
            # 依据必须是"接收方以前援助过供给方"的那几笔（方向相反），且发生在本次回助之前
            if (not src or src[0]["donor"] != e0["receiver"]
                    or src[0]["receiver"] != e0["donor"] or py >= t):
                prior_ok = False
        print(f"      第 {t} 年回助 {e0['id']}：依据 {basis.get('prior_events')}，"
              f"记得对方帮过自己 {basis.get('remembered_kcal')} kcal（最近第 "
              f"{basis.get('remembered_last_year')} 年）")
        check("O27g 回助事件关联了真实的历史援助记录（方向、先后、id 都对得上）",
              prior_ok and bool(basis.get("remembered_kcal")), str(basis)[:90])
        check("O27h 援助事件写明哪些东西未记录", "unrecorded" in e0)

    # 分配对照：关掉优先的那条应当一次都没改变过分配
    chg_on = chg_off = 0
    sample = None
    for t in range(0, 151):
        on = c9.get(f"/api/runs/{pair[1]}/year/{t}").json().get("recip", {}).get("compare", [])
        off = c9.get(f"/api/runs/{pair[0]}/year/{t}").json().get("recip", {}).get("compare", [])
        chg_on += sum(1 for c in on if c["changed"])
        chg_off += sum(1 for c in off if c["changed"])
        if sample is None:
            s2 = [c for c in on if c["changed"]]
            if s2: sample = (t, s2[0])
    print(f"      开启优先回助：分配被改变 {chg_on} 次；关闭：{chg_off} 次")
    if sample:
        t, c = sample
        print(f"      第 {t} 年第 {c['cell']} 号格：开优先 {len(c['with_recip'])} 笔 / "
              f"关优先 {len(c['without_recip'])} 笔")
    check("O27i 分配对照可用，且关闭优先时恒不改变分配",
          chg_on > 0 and chg_off == 0 and sample is not None, f"{chg_on}/{chg_off}")
    check("O27j 对照的两条都确实发生过回助（所以'有往来'本身不能作为判据）",
          any(e.get("repay") for t in range(0, 151)
              for e in c9.get(f"/api/runs/{pair[0]}/year/{t}").json()["events"]
              if e["type"] == "aid"))

# ---------------------------------------------------------------- 历史卷宗与关系网
print("\nO28 截至某年的群体卷宗 / 援助关系汇总：不许把未来混进来")
with TestClient(app) as c10:
    PR = "preset-exp06-recip1000"
    OLD = "preset-s4242-sig400-mort50"          # exp03：没有援助段的旧引擎运行

    def band(bid, at=None):
        u = f"/api/runs/{PR}/band/{bid}" + (f"?at_year={at}" if at is not None else "")
        return c10.get(u)

    def rel(run=PR, at=None):
        u = f"/api/runs/{run}/relations" + (f"?at_year={at}" if at is not None else "")
        return c10.get(u)

    # 只读证据：调用前后记录文件与台账都不能变
    pfile = store.run_dir(PR) / "years.jsonl"
    before_file = (pfile.stat().st_mtime_ns, pfile.stat().st_size,
                   hashlib.sha256(pfile.read_bytes()).hexdigest())
    before_row = dict(store.get_run(PR))

    full_all = rel().json()
    check("O28a 省略 at_year = 全档案，并标明口径",
          full_all["history_scope"]["mode"] == "full"
          and full_all["history_scope"]["at_year"] is None,
          str(full_all["history_scope"])[:60])

    # 逐年重算一遍援助事件，和汇总对账（汇总不许自己造数）
    def recount(upto=None):
        agg, ids = {}, []
        for t in range(0, store.year_count(PR)):
            if upto is not None and t > upto:
                break
            for e in c10.get(f"/api/runs/{PR}/year/{t}").json()["events"]:
                if e["type"] != "aid":
                    continue
                k = (str(e["donor"]), str(e["receiver"]))
                a = agg.setdefault(k, [0, 0, 0, 0])
                a[0] += int(e["kcal"]); a[1] += 1
                a[2] += 1 if (e.get("phase") == "recip") else 0
                a[3] += 1 if e.get("repay") else 0
                ids.append(e["id"])
        return agg, ids

    agg_all, ids_all = recount()
    api_all = {(e["donor"], e["receiver"]):
               [e["kcal"], e["transfers"], e["phase_counts"].get("recip", 0),
                e["repay_transfers"]] for e in full_all["edges"]}
    check("O28b 关系汇总与逐笔记录完全对得上（kcal / 笔数 / 优先笔数 / 回助笔数）",
          api_all == agg_all, f"{len(api_all)} 条边 vs 重算 {len(agg_all)} 条")
    check("O28c 汇总的事件 id 都能在逐年记录里找到",
          set(i for e in full_all["edges"] for i in e["event_ids"]) == set(ids_all),
          f"{len(ids_all)} 笔")
    check("O28d 节点 id 是字符串，64 位 id 不被截断/转成数字",
          all(isinstance(n["id"], str) for n in full_all["nodes"])
          and any(len(n["id"]) >= 19 and int(n["id"]) > 2**53
                  for n in full_all["nodes"]),
          str([n["id"] for n in full_all["nodes"][:2]]))

    # 截至某年：只能是那一年之前发生过的事
    CUT = 83
    a83 = rel(at=CUT).json()
    agg83, ids83 = recount(CUT)
    api83 = {(e["donor"], e["receiver"]):
             [e["kcal"], e["transfers"], e["phase_counts"].get("recip", 0),
              e["repay_transfers"]] for e in a83["edges"]}
    late = [i for e in a83["edges"] for i in e["event_ids"] if int(i.split("-")[0][1:]) > CUT]
    check(f"O28e 截至第 {CUT} 年的汇总 == 前 {CUT} 年逐笔重算", api83 == agg83,
          f"{len(api83)} vs {len(agg83)}")
    check("O28f 截至某年的汇总里没有该年之后的事件（未来不泄漏）", not late, str(late[:3]))
    check("O28g 截断后的总量确实小于全档案（不是原样返回）",
          a83["totals"]["transfers"] < full_all["totals"]["transfers"],
          f'{a83["totals"]["transfers"]} < {full_all["totals"]["transfers"]}')

    # 群体卷宗：最初的真实抱怨 —— 回放到 124 年，档案里已经写着 125/131 年的迁移
    MOVER = "7567856178022945294"
    bf = band(MOVER).json()
    b124 = band(MOVER, 124).json()
    b125 = band(MOVER, 125).json()
    fut_full = [x for x in bf["trajectory"] if x[0] > 124]
    check("O28h 前提：这个群体在第 124 年之后确实又迁过（否则本组测试不承重）",
          bool(fut_full), str(fut_full[:3]))
    check("O28i 回放到第 124 年时，档案里没有 124 年之后的迁移",
          all(x[0] <= 124 for x in b124["trajectory"])
          and all(x[0] <= 124 for x in b124["sizes"]),
          str([x for x in b124["trajectory"] if x[0] > 124][:3]))
    check("O28j 年界：at_year=125 含第 125 年那一步，不含更晚的",
          any(x[0] == 125 for x in b125["trajectory"])
          and all(x[0] <= 125 for x in b125["trajectory"]),
          str(b125["trajectory"][-2:]))
    check("O28k 省略参数仍是全档案（老用法不变）",
          bf["trajectory"] == b125["trajectory"] + [x for x in bf["trajectory"] if x[0] > 125]
          and bf["history_scope"]["mode"] == "full")

    # 未来的出生与消失都不能提前出现
    leak = []
    for t in (0, 40, 83, 124):
        for b in c10.get(f"/api/runs/{PR}/year/{t}").json()["bands"]:
            d = band(b["id"], t).json()
            if d["born_at"] is not None and d["born_at"] > t:
                leak.append(("born", b["id"], d["born_at"], t))
            if d["extinct_at"] is not None and d["extinct_at"] > t:
                leak.append(("extinct", b["id"], d["extinct_at"], t))
            if any(ch[0] > t for ch in d["children"]):
                leak.append(("child", b["id"], d["children"], t))
            if any(e["year"] > t for e in d["aid_given"]["events"] + d["aid_received"]["events"]):
                leak.append(("aid", b["id"], t))
    check("O28l 截至第 N 年的卷宗里没有 N 年之后的出生 / 分裂 / 消失 / 援助",
          not leak, str(leak[:2]))

    # 消失：预置 150 年里可能没有灭绝。没有就写一份隔离短记录承重同一条口径，不改预置包。
    gone = [n["id"] for n in full_all["nodes"]
            if band(n["id"]).json().get("extinct_at") is not None]
    if gone:
        g = gone[0]
        gy = band(g).json()["extinct_at"]
        early = band(g, gy - 1).json()
        check("O28m 消失那年之前查，卷宗写还活着，不预告消失",
              early["extinct_at"] is None and early["alive_at_year"] is True,
              f"{g} 第 {gy} 年消失")
    else:
        EXT = "o28m-extinct"
        LIVE28 = "9223372036854775783"
        GONE28 = "18446744073709551557"
        store.run_dir(EXT).mkdir(parents=True, exist_ok=True)

        def _o28b(bid, cell, size):
            return {"id": bid, "name": "群体-" + bid[:4], "cell": cell, "size": size, "store": 100}

        def _o28r(t, bands, events):
            return {"t": t, "stock": [1], "bands": bands, "cum": {}, "year": {},
                    "agg": {"pop": sum(b["size"] for b in bands)}, "integrity": {},
                    "events": events}

        o28_years = [
            _o28r(0, [_o28b(LIVE28, 0, 10), _o28b(GONE28, 1, 4)], []),
            _o28r(1, [_o28b(LIVE28, 0, 10), _o28b(GONE28, 1, 2)], []),
            _o28r(2, [_o28b(LIVE28, 0, 10)],
                  [{"id": "t2-extinct-0", "year": 2, "type": "extinct",
                    "band": GONE28, "source": "模型日志"}]),
        ]
        store.years_path(EXT).write_text(
            "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":"))
                      for r in o28_years) + "\n",
            encoding="utf-8")
        with store.connect() as _c:
            _c.execute("DELETE FROM runs WHERE run_id=?", (EXT,))
            _c.execute(
                "INSERT INTO runs (run_id,label,kind,status,created_at,seed,years,"
                "sigma_m,move_mort_m,share_m,aid_m,recip_m,engine,arm,years_done) "
                "VALUES (?,?,'preset','interrupted',?,1,3,0,0,0,0,0,'exp03','memory',3)",
                (EXT, "O28m 隔离消失记录", time.time()))
        early = c10.get(f"/api/runs/{EXT}/band/{GONE28}?at_year=1").json()
        gone_full = c10.get(f"/api/runs/{EXT}/band/{GONE28}").json()
        check("O28m 消失那年之前查，卷宗写还活着，不预告消失",
              gone_full.get("extinct_at") == 2
              and early.get("extinct_at") is None
              and early.get("alive_at_year") is True,
              f"{GONE28} 第 2 年消失；隔离记录，预置案例无消失")

    # 展示年份：必须来自真实事件，且不晚于截断年
    mem_ok, mem_bad, mem_seen = True, [], 0
    for t in (83, 124, 150):
        for b in c10.get(f"/api/runs/{PR}/year/{t}").json()["bands"]:
            d = band(b["id"], t).json()
            for donor, m in (d.get("aid_memory") or {}).items():
                mem_seen += 1
                eid = m.get("last_event_id")
                if eid is None:
                    continue
                y = int(eid.split("-")[0][1:])
                src = [e for e in c10.get(f"/api/runs/{PR}/year/{y}").json()["events"]
                       if e["id"] == eid]
                if (y > t or m.get("last_year_display") != y or not src
                        or str(src[0]["donor"]) != donor or str(src[0]["receiver"]) != b["id"]):
                    mem_ok = False; mem_bad.append((b["id"], donor, eid, t))
    if not mem_seen:
        uncov("O28n 记忆的展示年份", "这几年里没有群体带着援助记忆，前提缺失")
    else:
        check("O28n 记忆的展示年份指向真实的那一笔援助，且不晚于截断年",
              mem_ok, f"{mem_seen} 条记忆；越界 {mem_bad[:2]}")
        one = None
        for b in c10.get(f"/api/runs/{PR}/year/83").json()["bands"]:
            m = (band(b["id"], 83).json().get("aid_memory") or {})
            if m:
                one = (b["id"], list(m.items())[0]); break
        if one:
            bid, (donor, m) = one
            print(f"      第 83 年 {bid[:8]}… 记得 {donor[:8]}…："
                  f"内部 tick last_year={m['last_year']} → 展示年份 "
                  f"{m['last_year_display']}（事件 {m['last_event_id']}）")

    # recip.changed 是格×年诊断，不归给关系边，也不能用 repay 代替
    check("O28o 关系边上没有把'分配被改变'算成某一对的往来",
          all("recip_changed" not in e and "changed" not in e for e in full_all["edges"])
          and "recip_changed_cellyears" in full_all["diagnostics"])
    repay_total = sum(e["repay_transfers"] for e in full_all["edges"])
    check("O28p 诊断计数与回助笔数是两个数，没有互相顶替",
          full_all["diagnostics"]["recip_changed_cellyears"] != repay_total
          or repay_total == 0,
          f'changed={full_all["diagnostics"]["recip_changed_cellyears"]} repay={repay_total}')

    # 旧引擎：没有援助段也要正常读
    old_rel = rel(OLD)
    old_band = c10.get(f"/api/runs/{OLD}/year/0").json()["bands"][0]["id"]
    ob = c10.get(f"/api/runs/{OLD}/band/{old_band}?at_year=10")
    check("O28q 旧引擎（无援助段）的关系汇总是空的，不报错也不编造",
          old_rel.status_code == 200 and old_rel.json()["totals"]["edges"] == 0
          and old_rel.json()["totals"]["transfers"] == 0, str(old_rel.status_code))
    check("O28r 旧引擎的群体卷宗照常读，援助字段如实为空",
          ob.status_code == 200 and ob.json()["aid_memory"] is None
          and ob.json()["aid_given"]["transfers"] == 0, str(ob.status_code))

    # 缺年 / 越界 / 类型：一律说清楚，不静默夹取
    codes = [band(MOVER, 999).status_code, band(MOVER, -1).status_code,
             c10.get(f"/api/runs/{PR}/band/{MOVER}?at_year=abc").status_code,
             rel(at=999).status_code, rel(at=-1).status_code,
             c10.get(f"/api/runs/nope/relations").status_code,
             c10.get(f"/api/runs/{PR}/band/nosuchband?at_year=10").status_code]
    check("O28s 越界 400 / 非整数 422 / 不存在 404，都明确回答",
          codes == [400, 400, 422, 400, 400, 404, 404], str(codes))
    msg = band(MOVER, 999).json().get("detail", "")
    check("O28t 越界提示写明这次运行到底存了多少年", "0..150" in msg, msg[:60])

    # 截到群体出生之前：应当是 404，而不是一份空壳档案
    newborn = [n["id"] for n in full_all["nodes"]
               if (band(n["id"]).json().get("born_at") or 0) > 0]
    if not newborn:
        uncov("O28u 出生之前的查询", "这条预置案例里没有中途分裂出来的群体，前提缺失")
    else:
        nb = newborn[0]
        by = band(nb).json()["born_at"]
        check("O28u 群体出生之前查它，如实 404，不返回空壳档案",
              band(nb, by - 1).status_code == 404 and band(nb, by).status_code == 200,
              f"{nb[:8]}… 第 {by} 年出生")

    after_file = (pfile.stat().st_mtime_ns, pfile.stat().st_size,
                  hashlib.sha256(pfile.read_bytes()).hexdigest())
    check("O28v 这些查询是只读的：记录文件与台账一字未改",
          before_file == after_file and dict(store.get_run(PR)) == before_row,
          "文件变了" if before_file != after_file else "")

# ------------------------------------------------- 定向场景：长跑里撞不到的那几条
# 预置那条 150 年里**一个群体都没有消失过**，挂在它身上的"消失年份截断"永远是绿的。
# 所以这里手写一份隔离的记录（不跑任何模型、不碰冻结目录），把这几条路径逼出来。
print("\nO29 定向场景：消失年份、记录不全的运行、援助发生在记录之外")
HIST = "hist-probe"
BIG_A = "18446744073709551557"     # 20 位，超过 2^53，前端一律按字符串处理
BIG_B = "9223372036854775783"
GONE = "1311768467463790320"
store.run_dir(HIST).mkdir(parents=True, exist_ok=True)


def _b(bid, cell, size, mem=None):
    d = {"id": bid, "name": "群体-" + bid[:4], "cell": cell, "size": size, "store": 100}
    if mem is not None:
        d["aid_memory"] = mem
    return d


def _rec(t, bands, events, aid=True):
    r = {"t": t, "stock": [1], "bands": bands, "cum": {}, "year": {},
         "agg": {"pop": sum(b["size"] for b in bands)}, "integrity": {}, "events": events}
    if aid:
        r["aid"] = {"transfers": len([e for e in events if e["type"] == "aid"])}
        r["recip"] = {"changed": 1 if t == 3 else 0}
    return r


def _aid(t, i, donor, recv, kcal, phase="normal", repay=False):
    return {"id": f"t{t}-aid-{i}", "year": t, "type": "aid", "donor": donor,
            "receiver": recv, "kcal": kcal, "cell": 0, "phase": phase,
            "repay": repay, "source": "模型日志 st['aid_log']"}


years = [
    _rec(0, [_b(BIG_A, 0, 10), _b(BIG_B, 0, 10), _b(GONE, 1, 6)], []),
    _rec(1, [_b(BIG_A, 0, 10), _b(BIG_B, 0, 10), _b(GONE, 1, 5)],
         [_aid(1, 0, BIG_A, BIG_B, 500)]),
    _rec(2, [_b(BIG_A, 0, 10), _b(BIG_B, 1, 10, {BIG_A: {"kcal": 500, "last_year": 1}}),
             _b(GONE, 1, 3)], []),
    # 第 3 年：GONE 消失；BIG_B 回助 BIG_A（优先阶段）
    _rec(3, [_b(BIG_A, 0, 10), _b(BIG_B, 1, 10, {BIG_A: {"kcal": 500, "last_year": 1}})],
         [{"id": "t3-extinct-0", "year": 3, "type": "extinct", "band": GONE, "cell": 1,
           "source": "模型日志"},
          _aid(3, 1, BIG_B, BIG_A, 300, phase="recip", repay=True)]),
    # 第 4 年：BIG_A 记得 BIG_B 帮过（真实事件在第 3 年）；另有一条"记录之外"的旧账
    _rec(4, [_b(BIG_A, 0, 10, {BIG_B: {"kcal": 300, "last_year": 2},
                               GONE: {"kcal": 999, "last_year": 0}}),
             _b(BIG_B, 1, 10, {BIG_A: {"kcal": 500, "last_year": 1}})], []),
]
store.years_path(HIST).write_text(
    "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in years) + "\n",
    encoding="utf-8")
with store.connect() as _c:
    _c.execute("DELETE FROM runs WHERE run_id=?", (HIST,))
    _c.execute("INSERT INTO runs (run_id,label,kind,status,created_at,seed,years,sigma_m,"
               "move_mort_m,share_m,aid_m,recip_m,engine,arm,years_done) "
               "VALUES (?,?,'preset','interrupted',?,1,9,0,0,1000,1000,1000,'exp06','memory',5)",
               (HIST, "定向场景：隔离记录", time.time()))

with TestClient(app) as c11:
    def hb(bid, at=None):
        return c11.get(f"/api/runs/{HIST}/band/{bid}" + (f"?at_year={at}" if at is not None else ""))

    check("O29a 前提：这份隔离记录里确实有群体消失",
          hb(GONE).json()["extinct_at"] == 3, str(hb(GONE).json().get("extinct_at")))
    check("O29b 消失那年之前查：写还活着，不预告消失",
          hb(GONE, 2).json()["extinct_at"] is None
          and hb(GONE, 2).json()["alive_at_year"] is True)
    check("O29c 消失那年查：如实写已消失",
          hb(GONE, 3).json()["extinct_at"] == 3
          and hb(GONE, 3).json()["alive_at_year"] is False)
    check("O29d 消失之后仍查得到它的历史（不是 404）",
          hb(GONE, 4).status_code == 200 and hb(GONE, 4).json()["last_seen"] == 2)

    # 声称 9 年、实际只存了 5 年：截到第 6 年应当明确报"只存了 0..4"
    check("O29e 记录不全的运行：问到没存的年份，明说只存了多少",
          hb(BIG_A, 6).status_code == 400 and "0..4" in hb(BIG_A, 6).json()["detail"],
          hb(BIG_A, 6).json().get("detail", "")[:50])
    check("O29f 存到哪查到哪：第 4 年正常返回", hb(BIG_A, 4).status_code == 200)

    # 展示年份：真实事件推出来的（第 3 年），而不是记忆里的内部 tick（2）
    m4 = hb(BIG_A, 4).json()["aid_memory"]
    check("O29g 内部 tick 与展示年份分开：raw 保留 2，展示写 3 并挂上事件 id",
          m4[BIG_B]["last_year"] == 2 and m4[BIG_B]["last_year_display"] == 3
          and m4[BIG_B]["last_event_id"] == "t3-aid-1", str(m4.get(BIG_B))[:90])
    check("O29h 记录里找不到出处的旧账，如实写未记录，不猜一个年份",
          m4[GONE]["last_year_display"] is None and m4[GONE]["last_event_id"] is None
          and "未记录" in m4[GONE]["display_source"], str(m4.get(GONE))[:90])
    m2 = hb(BIG_B, 2).json()["aid_memory"]
    check("O29i 截到第 2 年时，记忆只能指向第 2 年以前的那一笔",
          m2[BIG_A]["last_year_display"] == 1 and m2[BIG_A]["last_event_id"] == "t1-aid-0",
          str(m2.get(BIG_A))[:80])

    r_all = c11.get(f"/api/runs/{HIST}/relations").json()
    r_2 = c11.get(f"/api/runs/{HIST}/relations?at_year=2").json()
    e_all = {(e["donor"], e["receiver"]): e for e in r_all["edges"]}
    check("O29j 两个方向各算一条边，不合并成一条无向关系",
          set(e_all) == {(BIG_A, BIG_B), (BIG_B, BIG_A)}, str(list(e_all))[:80])
    back = e_all.get((BIG_B, BIG_A), {})
    fore = e_all.get((BIG_A, BIG_B), {})
    check("O29k 优先阶段与回助各自计数，来源是事件本身",
          back.get("phase_counts") == {"recip": 1, "normal": 0}
          and back.get("repay_transfers") == 1
          and fore.get("phase_counts") == {"recip": 0, "normal": 1},
          str(back.get("phase_counts")) + " / " + str(fore.get("phase_counts")))
    check("O29l 截到第 2 年只剩先发生的那一条边",
          [(e["donor"], e["receiver"]) for e in r_2["edges"]] == [(BIG_A, BIG_B)]
          and r_2["totals"]["transfers"] == 1, str(r_2["totals"]))
    check("O29m 已消失的群体在截断年之后标为不在世，但仍列在节点里",
          any(n["id"] == GONE and n["alive_at_year"] is False for n in r_all["nodes"])
          and any(n["id"] == GONE and n["alive_at_year"] is True for n in r_2["nodes"]))
    check("O29n 64 位 id 原样返回，没有被当成数字",
          all(isinstance(n["id"], str) for n in r_all["nodes"])
          and {BIG_A, BIG_B} <= {n["id"] for n in r_all["nodes"]})
    check("O29o recip.changed 记在诊断里，不加到任何一条边上",
          r_all["diagnostics"]["recip_changed_cellyears"] == 1
          and all("recip_changed" not in e for e in r_all["edges"]))

    # 把同一份记录改成"没有援助段"，模拟旧引擎
    plain = [dict(r) for r in years]
    for r in plain:
        r.pop("aid", None); r.pop("recip", None)
        r["events"] = [e for e in r["events"] if e["type"] != "aid"]
        r["bands"] = [{k: v for k, v in b.items() if k != "aid_memory"} for b in r["bands"]]
    OLDR = "hist-probe-old"
    store.run_dir(OLDR).mkdir(parents=True, exist_ok=True)
    store.years_path(OLDR).write_text(
        "\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in plain) + "\n",
        encoding="utf-8")
    with store.connect() as _c:
        _c.execute("DELETE FROM runs WHERE run_id=?", (OLDR,))
        _c.execute("INSERT INTO runs (run_id,label,kind,status,created_at,seed,years,"
                   "sigma_m,move_mort_m,share_m,aid_m,recip_m,engine,arm,years_done) "
                   "VALUES (?,?,'preset','done',?,1,5,0,0,0,0,0,'exp03','memory',5)",
                   (OLDR, "定向场景：旧引擎无援助段", time.time()))
    ro = c11.get(f"/api/runs/{OLDR}/relations?at_year=3").json()
    bo = c11.get(f"/api/runs/{OLDR}/band/{GONE}?at_year=3").json()
    check("O29p 同一份历史去掉援助段后照常读：边为 0，卷宗照给，不报错",
          ro["totals"]["edges"] == 0 and bo["extinct_at"] == 3
          and bo["aid_memory"] is None and bo["aid_given"]["transfers"] == 0,
          str(ro["totals"]))

# ---------------------------------------------------------------- 取消的可靠性
# 以前取消只设一个标志，工作进程在**年边界**才读它。进程活着但卡在某一步时，
# 那个标志永远读不到，唯一的任务槽就再也放不出来。这一组把四条路都逼一遍。
# 全部用隔离数据 + 本脚本自己起的测试子进程，不碰任何真实运行。
print("\nO30 取消：协作收尾 / 卡住也能有界停止 / 身份不明绝不误杀 / 竞态不覆盖赢家")


def fake_worker(run_id, ignore_term=True):
    """起一个**本测试自己的**子进程，命令行里带 observer.worker 与 run_id ——
    这正是 probe_worker 用来确认身份的两个特征。ignore_term=True 时它无视 SIGTERM，
    用来检验"协作不成还能强制停止"这条路真的走得通。"""
    code = ("import signal, time\n"
            + ("signal.signal(signal.SIGTERM, signal.SIG_IGN)\n" if ignore_term else "")
            + "time.sleep(600)\n")
    return subprocess.Popen([sys.executable, "-c", code, "observer.worker", run_id])


def alive(proc):
    return proc.poll() is None


def make_row(rid, pid, status="running", cancel=0, cancel_at=None, years=50, age=0.0):
    born = time.time() - age
    with store.connect() as c:
        c.execute("DELETE FROM runs WHERE run_id=?", (rid,))
        c.execute("INSERT INTO runs (run_id,label,kind,status,created_at,started_at,seed,years,"
                  "sigma_m,move_mort_m,share_m,aid_m,recip_m,engine,arm,years_done,pid,"
                  "cancel_requested,cancel_requested_at) "
                  "VALUES (?,?,'user',?,?,?,1,?,0,0,0,0,0,'exp03','memory',0,?,?,?)",
                  (rid, "O30 隔离测试", status, born, born, years,
                   pid, cancel, cancel_at))
    store.run_dir(rid).mkdir(parents=True, exist_ok=True)


# --- (1) 正常工作进程：用户取消后自己在年边界收尾 ---
# 全程在**同一个** TestClient 里做：另开一个客户端会触发启动恢复，
# 把还在算的那条直接标成 interrupted，测的就不是取消了。
with store.connect() as _c:
    _c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
with TestClient(app) as c12:
    # 模型每秒能跑近千年，300 年的运行在请求发出去之前就结束了；这里要一条真的还在算的。
    r = c12.post("/api/runs", json={"seed": 4242, "years": 6000, "sigma_m": 400,
                                    "move_mort_m": 50, "engine": "exp03",
                                    "label": "O30 协作取消"})
    coop_id = r.json().get("run_id") if r.status_code == 200 else None
    if coop_id is None:
        uncov("O30a–e 协作取消", f"运行没起来：{r.status_code} {str(r.json())[:60]}")
    else:
        for _ in range(900):                      # 等它真的算起来，别在第 0 年就取消
            row = store.get_run(coop_id)
            if row["status"] == "running" and (row["years_done"] or 0) >= 50:
                break
            if row["status"] in ("done", "failed", "canceled", "interrupted"):
                break
            time.sleep(0.02)
        row = store.get_run(coop_id)
    if coop_id and row["status"] != "running":
        uncov("O30a–e 协作取消", f"这次运行没来得及进入 running（{row['status']}）")
    elif coop_id:
        t0 = time.time()
        resp = c12.post(f"/api/runs/{coop_id}/cancel")
        check("O30a 取消请求被接受，并给出人话说明",
              resp.status_code == 200 and resp.json()["ok"]
              and resp.json()["cancel"]["requested"], str(resp.json())[:80])
        for _ in range(1500):
            if store.get_run(coop_id)["status"] in ("done", "failed", "canceled",
                                                    "interrupted"):
                break
            time.sleep(0.02)
        row = store.get_run(coop_id)
        took = time.time() - t0
        check("O30b 正常工作进程自己协作收尾为 canceled（不是被杀、不是中断）",
              row["status"] == "canceled" and "自己停下" in (row["cancel_note"] or ""),
              f'{row["status"]} / {took:.1f}s / {(row["cancel_note"] or "")[:36]}')
        check("O30b2 协作收尾远远早于强制窗口（说明走的是协作那条路）",
              took < config.CANCEL_GRACE_SEC, f"{took:.1f}s < {config.CANCEL_GRACE_SEC:.0f}s")
        recorded = store.year_count(coop_id) - 1
        check("O30c 已完整写入的年份一年不少地留着，且与 years_done 对得上",
              recorded >= 50 and row["years_done"] == recorded,
              f"记录 {recorded} 年 / years_done {row['years_done']}")
        check("O30c2 取消的是这一条，不是把整次运行的历史丢掉",
              recorded < 6000, f"{recorded} 年（上限 6000）")
        ser = c12.get(f"/api/runs/{coop_id}/series")
        y1 = c12.get(f"/api/runs/{coop_id}/year/1")
        check("O30d 取消之后历史照常回放",
              ser.status_code == 200 and len(ser.json()["series"]) == recorded + 1
              and y1.status_code == 200, str(ser.status_code))
        detail = c12.get(f"/api/runs/{coop_id}").json()
        check("O30d2 接口给出取消口径（谁请求的、进行到哪一步）",
              detail["cancel"]["requested"] and detail["cancel"]["stage"] == "finished"
              and detail["cancel_note"], str(detail["cancel"])[:70])
        check("O30e 任务槽真的放出来了，可以立刻新建运行",
              store.active_run() is None
              and c12.post("/api/runs", json={"seed": 5, "years": 1, "sigma_m": 0,
                                              "move_mort_m": 0, "engine": "exp03",
                                              "label": "O30 槽复用"}).status_code == 200)
        for _ in range(900):
            if (store.active_run() or {}).get("status") is None:
                break
            time.sleep(0.02)
with store.connect() as _c:
    _c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")

# --- (2) 卡住的工作进程：协作窗口用完之后必须能在有界时间内停下 ---
STUCK = "o30-stuck"
proc = fake_worker(STUCK)
make_row(STUCK, proc.pid, cancel=1, cancel_at=time.time() - config.CANCEL_GRACE_SEC - 1)
store.years_path(STUCK).write_text(
    "".join(json.dumps({"t": i, "stock": [1], "bands": [], "cum": {}, "year": {},
                        "agg": {"pop": i}, "integrity": {}, "events": []},
                       separators=(",", ":")) + "\n" for i in range(3))
    + '{"t":3,"stock":[1],"ban', encoding="utf-8")     # 末尾故意留半条
check("O30f 前提：这个假工作进程确实被认成本次运行的活进程",
      store.probe_worker(proc.pid, STUCK) == store.WORKER_ALIVE,
      store.probe_worker(proc.pid, STUCK))
t0 = time.time()
acted = store.enforce_cancels()
took = time.time() - t0
row = store.get_run(STUCK)
check("O30g 卡住的工作进程在有界时间内被停止（先 TERM 后 KILL）",
      row["status"] == "canceled" and not alive(proc) and took < 10,
      f'{row["status"]} / {took:.1f}s / alive={alive(proc)}')
check("O30h 停止原因写明是取消超时，不写成系统故障",
      "超时" in (row["cancel_note"] or "") and "强制停止" in (row["cancel_note"] or ""),
      (row["cancel_note"] or "")[:50])
check("O30i 半条记录不算完成的年份（只认完整写入的 3 条：第 0..2 年）",
      store.year_count(STUCK) == 3 and row["years_done"] == 2,
      f'year_count={store.year_count(STUCK)} years_done={row["years_done"]}')
check("O30j 槽被放出来了", store.active_run() is None)
proc.kill()

# --- (3) 没有用户取消时，绝不因为"暂时没进度"动一个正常进程 ---
# 这条**故意**长得像"卡住的任务"：跑了很久、一年都没算出来、进度是 0。
# 唯一的区别是**用户没有按过取消** —— 这就是唯一的判据，不许有第二条。
CALM = "o30-no-cancel"
calm = fake_worker(CALM)
make_row(CALM, calm.pid, cancel=0, age=config.CANCEL_GRACE_SEC * 20 + 600)
before = store.get_run(CALM)["status"]
store.enforce_cancels()
store.enforce_cancels()                   # 再来一轮，确认不是"第一轮宽限"
time.sleep(0.3)
row = store.get_run(CALM)
check("O30k 没人取消时，哪怕它看起来'很久没进度'也一个信号都不发",
      alive(calm) and row["status"] == before and not row["cancel_requested"],
      f"alive={alive(calm)} status={row['status']} 已跑 "
      f"{time.time() - row['started_at']:.0f}s 进度 {row['years_done']}")
check("O30k2 也不会顺手给它写一条取消说明（它根本没被取消）",
      not (row["cancel_note"] or ""), (row["cancel_note"] or "")[:40])
calm.kill()
with store.connect() as _c:
    _c.execute("UPDATE runs SET status='interrupted' WHERE run_id=?", (CALM,))

# --- (4) pid 被复用：命令行对不上，绝不发信号 ---
REUSED = "o30-pid-reuse"
victim = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
make_row(REUSED, victim.pid, cancel=1, cancel_at=time.time() - config.CANCEL_GRACE_SEC - 1)
check("O30l 前提：这个 pid 的命令行不是本次运行的工作进程",
      store.probe_worker(victim.pid, REUSED) == store.WORKER_GONE,
      store.probe_worker(victim.pid, REUSED))
store.enforce_cancels()
time.sleep(0.3)
check("O30m pid 被复用时不发任何信号，无关进程活得好好的", alive(victim),
      "无关进程被误杀了")
check("O30n 记录按'进程已经不在'如实收尾为 canceled",
      store.get_run(REUSED)["status"] == "canceled"
      and "已经不在" in (store.get_run(REUSED)["cancel_note"] or ""),
      (store.get_run(REUSED)["cancel_note"] or "")[:40])
victim.kill()

# --- (5) 探测结果未知：不杀、不改状态、如实说 ---
UNK = "o30-unknown"
unk_proc = fake_worker(UNK)
make_row(UNK, unk_proc.pid, cancel=1, cancel_at=time.time() - config.CANCEL_GRACE_SEC - 1)
_real_probe = store.probe_worker
store.probe_worker = lambda pid, rid: (store.WORKER_UNKNOWN if rid == UNK
                                       else _real_probe(pid, rid))
try:
    store.enforce_cancels()
finally:
    store.probe_worker = _real_probe
time.sleep(0.3)
row = store.get_run(UNK)
check("O30o 身份查不到时：不发信号、不改状态，只如实记一句话",
      alive(unk_proc) and row["status"] == "running"
      and "无法确认" in (row["cancel_note"] or ""),
      f'alive={alive(unk_proc)} status={row["status"]} note={(row["cancel_note"] or "")[:24]}')
check("O30p 未知不是失败：取消请求还在，下一轮还会再看",
      bool(row["cancel_requested"]) and row["cancel_requested_at"] is not None)
unk_proc.kill()
time.sleep(0.4)
store.enforce_cancels()              # 进程没了之后，同一条路自己收尾
check("O30q 等进程真的没了，同一条判据把它收尾成 canceled",
      store.get_run(UNK)["status"] == "canceled", store.get_run(UNK)["status"])

# --- (6) 取消与完成的竞态：谁先写完谁算数，不覆盖赢家 ---
RACE = "o30-race-done"
race_proc = fake_worker(RACE)
make_row(RACE, race_proc.pid, cancel=1, cancel_at=time.time() - config.CANCEL_GRACE_SEC - 1)
_real_stop = store.stop_worker


def stop_but_worker_wins(pid, rid, grace=3.0):
    """模拟"就在要停它的一瞬间，工作进程自己把 done 写进去了"。"""
    if rid == RACE:
        store.worker_finish(rid, pid, "done", finished_at=time.time(), years_done=7,
                            full_digest="race-digest")
    return _real_stop(pid, rid, grace)


store.stop_worker = stop_but_worker_wins
try:
    store.enforce_cancels()
finally:
    store.stop_worker = _real_stop
row = store.get_run(RACE)
check("O30r 工作进程抢先写完 done 时，取消收尾不把它覆盖成 canceled",
      row["status"] == "done" and row["full_digest"] == "race-digest",
      f'{row["status"]} / {row["full_digest"]}')
check("O30s 竞态之后不留下半截状态（years_done 仍是赢家写的）",
      row["years_done"] == 7, str(row["years_done"]))
race_proc.kill()

# --- (7) 反过来：取消先落地，迟到的工作进程改不回 done ---
LATE = "o30-race-late"
late_proc = fake_worker(LATE)
make_row(LATE, late_proc.pid, cancel=1, cancel_at=time.time() - config.CANCEL_GRACE_SEC - 1)
store.enforce_cancels()
canceled_row = store.get_run(LATE)
late_ok = store.worker_finish(LATE, late_proc.pid, "done", finished_at=time.time(),
                              years_done=99, full_digest="late-digest")
after = store.get_run(LATE)
check("O30t 取消已经落地后，迟到的工作进程改不回 done",
      canceled_row["status"] == "canceled" and not late_ok
      and after["status"] == "canceled" and after["full_digest"] != "late-digest",
      f'{after["status"]} / late_ok={late_ok}')
late_proc.kill()

# --- (8) 终态不回退：对已结束的运行按取消，什么都不应该变 ---
TERM = "o30-terminal"
make_row(TERM, None, status="done", cancel=0)
with store.connect() as _c:
    _c.execute("UPDATE runs SET years_done=12, full_digest='keep' WHERE run_id=?", (TERM,))
store.request_cancel(TERM)
store.enforce_cancels()
row = store.get_run(TERM)
with TestClient(app) as c13:
    code = c13.post(f"/api/runs/{TERM}/cancel").status_code
check("O30u 已结束的运行：取消不改状态、不清数据，接口如实回 409",
      row["status"] == "done" and row["years_done"] == 12 and row["full_digest"] == "keep"
      and not row["cancel_requested"] and code == 409,
      f'{row["status"]} / {code}')
with store.connect() as _c:
    _c.execute("DELETE FROM runs WHERE run_id IN (?,?,?,?,?,?)",
               (STUCK, REUSED, UNK, RACE, LATE, TERM))

# ------------------------------------------------ 停止的结果必须是"核实过的"
# C05 的漏洞：stop_worker 把"查不到"当成"停下来了"，SIGKILL 失败也无条件返回成功；
# enforce_cancels 又完全忽略返回值，照样写 canceled 并释放任务槽。
# 结果是旧工作进程还活着、还在往 years.jsonl 里**追加**（数据库围栏管不住文件写入），
# 新运行却已经起来了。这一组把"停止失败/未知"的每一条路都逼一遍。
# 发出去的真实信号只打**本脚本自己起的**子进程；失败注入全部用替身函数，不碰任何别的进程。
print("\nO31 停止结果三态：只有确认 gone 才放槽；未知与失败都不许谎报已停止")

_REAL_KILL = os.kill
_REAL_PROBE = store.probe_worker


def scripted(probe_seq=None, kill_error=None, kill_log=None, fixed_probe=None):
    """临时替换探测与发信号：probe 按剧本逐次返回，os.kill 只记录不真发。"""
    seq = list(probe_seq or [])

    def fake_probe(pid, rid):
        if fixed_probe is not None:
            return fixed_probe
        return seq.pop(0) if seq else store.WORKER_ALIVE

    def fake_kill(pid, sig):
        if kill_log is not None:
            kill_log.append(sig)
        if kill_error is not None and (not isinstance(kill_error, dict)
                                       or sig in kill_error):
            err = kill_error[sig] if isinstance(kill_error, dict) else kill_error
            raise err
        return None
    return fake_probe, fake_kill


def run_stop(pid, rid, **kw):
    """在替身下跑一次 stop_worker，跑完立刻还原（真实 os.kill 不被长期改动）。"""
    fake_probe, fake_kill = scripted(**kw)
    store.probe_worker, os.kill = fake_probe, fake_kill
    try:
        return store.stop_worker(pid, rid, grace=0.2)
    finally:
        store.probe_worker, os.kill = _REAL_PROBE, _REAL_KILL


A, G, U = store.WORKER_ALIVE, store.WORKER_GONE, store.WORKER_UNKNOWN
sigs = []
check("O31a TERM 发不出去（OSError）时返回未知，不冒充已停止，也不升级到 KILL",
      run_stop(999999, "x", probe_seq=[A], kill_error=PermissionError("nope"),
               kill_log=sigs) == U and sigs == [signal.SIGTERM], str(sigs))
check("O31b 等待期间探测变'查不到'：返回未知（旧实现在这里返回'已停止'）",
      run_stop(999999, "x", probe_seq=[A, U], kill_log=[]) == U)
sigs = []
check("O31c KILL 发不出去时返回未知，绝不报告已停止",
      run_stop(999999, "x", probe_seq=[A, A, A, A, A, A, A, A, A, A],
               kill_error={signal.SIGKILL: PermissionError("nope")},
               kill_log=sigs) == U and signal.SIGKILL in sigs, str(sigs))
check("O31d KILL 之后仍然查得到它：返回 alive（旧实现无条件说成功）",
      run_stop(999999, "x", fixed_probe=A, kill_log=[]) == A)
sigs = []
check("O31e 升级到 KILL 之前身份变了（pid 被复用）：返回 gone，且一个 KILL 都不发",
      run_stop(999999, "x", probe_seq=[A, A, G], kill_log=sigs) == G
      and signal.SIGKILL not in sigs, str(sigs))
check("O31f 一开始就不是我们的进程：一个信号都不发",
      run_stop(999999, "x", probe_seq=[G], kill_log=sigs) == G)

# 正向对照：真能停下来的进程必须返回 gone（否则上面几条可能是"永远不返回 gone"）
GOOD = "o31-stoppable"
good_proc = fake_worker(GOOD, ignore_term=False)
make_row(GOOD, good_proc.pid, cancel=1, cancel_at=time.time() - config.CANCEL_GRACE_SEC - 1)
check("O31g 真的能停下来的工作进程：返回 gone（信号只打本测试自己的子进程）",
      store.stop_worker(good_proc.pid, GOOD) == store.WORKER_GONE
      and not alive(good_proc))
store.enforce_cancels()
check("O31h 确认停下来之后才释放任务槽，记录写 canceled",
      store.get_run(GOOD)["status"] == "canceled" and store.active_run() is None,
      store.get_run(GOOD)["status"])

# --- 停不下来：**不许**放槽 ---
HARD = "o31-unstoppable"
hard_proc = fake_worker(HARD)          # 无视 SIGTERM
make_row(HARD, hard_proc.pid, cancel=1, cancel_at=time.time() - config.CANCEL_GRACE_SEC - 1)
_saved_stop = store.stop_worker
store.stop_worker = lambda pid, rid, grace=3.0: (store.WORKER_ALIVE if rid == HARD
                                                 else _saved_stop(pid, rid, grace))
try:
    acted = store.enforce_cancels()
finally:
    store.stop_worker = _saved_stop
row = store.get_run(HARD)
check("O31i 信号发了但没能确认它停下来：**不写 canceled、不放槽**",
      row["status"] == "running" and alive(hard_proc)
      and (store.active_run() or {}).get("run_id") == HARD,
      f'{row["status"]} / active={(store.active_run() or {}).get("run_id")}')
check("O31j 说明如实写明没停下来、槽先不释放，不谎报已强制停止",
      "仍能查到" in (row["cancel_note"] or "") and "不释放" in (row["cancel_note"] or "")
      and "已强制停止" not in (row["cancel_note"] or ""),
      (row["cancel_note"] or "")[:48])
check("O31k 取消请求保留着，下一轮还会再试",
      bool(row["cancel_requested"]) and row["cancel_requested_at"] is not None
      and [a for a in acted if a["run_id"] == HARD][0]["action"] == store.CANCEL_STOP_FAILED,
      str([a for a in acted if a["run_id"] == HARD])[:70])

# 节流：刚试过一次就不该在下一个请求里再发一遍信号（stop_worker 要同步等好几秒）
tries = []
store.stop_worker = lambda pid, rid, grace=3.0: (tries.append(rid) or store.WORKER_ALIVE
                                                 if rid == HARD
                                                 else _saved_stop(pid, rid, grace))
try:
    store.enforce_cancels()
    store.enforce_cancels()
finally:
    store.stop_worker = _saved_stop
check("O31l 刚试过就不重复发信号（否则每次页面刷新都要卡住几秒）",
      tries == [], f"这一轮又发了 {len(tries)} 次")
check("O31l2 节流期间状态与取消请求都不变",
      store.get_run(HARD)["status"] == "running"
      and bool(store.get_run(HARD)["cancel_requested"]))


def next_round():
    """把"上一次尝试"清掉，表示已经到了下一轮检查。"""
    with store.connect() as c:
        c.execute("UPDATE runs SET cancel_last_attempt_at=NULL WHERE run_id=?", (HARD,))


# 探测未知同样不放槽
next_round()
store.stop_worker = lambda pid, rid, grace=3.0: (store.WORKER_UNKNOWN if rid == HARD
                                                 else _saved_stop(pid, rid, grace))
try:
    store.enforce_cancels()
finally:
    store.stop_worker = _saved_stop
row = store.get_run(HARD)
check("O31l3 停止结果未知时也不放槽，说明写明'未知不等于已停止'",
      row["status"] == "running" and "未知不等于已停止" in (row["cancel_note"] or ""),
      f'{row["status"]} / {(row["cancel_note"] or "")[:30]}')

# 取消端点不能用乐观通稿盖掉这句准确说明。
# 这里**直接调端点函数**：再开一个 TestClient 会触发启动恢复，把这条还在跑的
# 记录直接标成 interrupted，测的就不是取消了。
from observer import app as _appmod                     # noqa: E402
next_round()
store.stop_worker = lambda pid, rid, grace=3.0: (store.WORKER_ALIVE if rid == HARD
                                                 else _saved_stop(pid, rid, grace))
try:
    resp = _appmod.cancel_run(HARD)
finally:
    store.stop_worker = _saved_stop
check("O31m 再点一次取消，接口回的是真实情况，不是'会在这一年算完后停下'",
      "不释放" in resp["note"] and "算完后自己停下" not in resp["note"]
      and resp["cancel"]["requested"], resp["note"][:44])

# 等它真的没了，同一条判据自行收尾
hard_proc.kill()
time.sleep(0.5)
next_round()
store.enforce_cancels()
check("O31n 旧进程真的没了之后，同一条路才收尾 canceled 并放槽",
      store.get_run(HARD)["status"] == "canceled" and store.active_run() is None,
      store.get_run(HARD)["status"])

# ------------------------------------- 启动恢复：同样只有确认 gone 才终态收尾
# 上一轮只改了文案 —— 停止结果是 unknown / alive 时照样 transition interrupted 并放槽。
# 旧工作进程虽然被围栏挡着改不回 done，却仍然会往 years.jsonl 里**追加**年份，
# 所以"承认没停下来"不够，必须真的不放槽。这一组按恢复的四种结局逐一逼。
print("\nO32 启动恢复：确认停了才收尾；没确认就保持活动状态并说明待处理")

REC_GONE, REC_ALIVE, REC_UNK = "o32-gone", "o32-alive", "o32-unknown"


def recover_with(stop_result, rid):
    """只替换 stop_worker 的**结果**，探测与转换走真实代码。"""
    saved = store.stop_worker
    store.stop_worker = lambda pid, r, grace=3.0: (stop_result if r == rid
                                                   else saved(pid, r, grace))
    try:
        return store.recover_interrupted()
    finally:
        store.stop_worker = saved


# (a) 确认停下来了 -> 终态收尾、放槽、计数 +1
gone_proc = fake_worker(REC_GONE, ignore_term=False)
make_row(REC_GONE, gone_proc.pid)
n_gone = store.recover_interrupted()
grow = store.get_run(REC_GONE)
check("O32a 确认旧工作进程不在了：标中断、放槽，并计入返回数",
      grow["status"] == "interrupted" and not alive(gone_proc) and n_gone >= 1
      and store.active_run() is None and "已确认不在" in (grow["error"] or ""),
      f'{grow["status"]} / n={n_gone}')
check("O32a2 收尾后不留恢复待处理说明",
      not (grow["recovery_note"] or "") and store.recovery_pending() == 0,
      (grow["recovery_note"] or "")[:30])
gone_proc.kill()

# (b) 停不下来（alive）-> **保持活动状态、槽不放**
alive_proc = fake_worker(REC_ALIVE)          # 无视 SIGTERM
make_row(REC_ALIVE, alive_proc.pid)
n_alive = recover_with(store.WORKER_ALIVE, REC_ALIVE)
arow = store.get_run(REC_ALIVE)
check("O32b 停不下来时不标中断、不放槽（旧实现在这里放了槽）",
      arow["status"] == "running" and alive(alive_proc)
      and (store.active_run() or {}).get("run_id") == REC_ALIVE,
      f'{arow["status"]} / active={(store.active_run() or {}).get("run_id")}')
check("O32b2 返回数只算真正标成中断的，不把没收尾的也算进去",
      n_alive == 0, str(n_alive))
check("O32b3 写明恢复待处理：没确认停下来就不放槽，以及后续怎么再核验",
      "仍能查到" in (arow["recovery_note"] or "")
      and "不放任务槽" in (arow["recovery_note"] or "")
      and "重新探测" in (arow["recovery_note"] or "")
      and store.recovery_pending() == 1, (arow["recovery_note"] or "")[:44])

# 后续刷新只探测、不再发信号。
# 这里走的是**查看运行列表那条路**（settle_slot = enforce_cancels + reap_stale），
# 不是再启动一次服务 —— 重启本身当然会再试一次停止，那是 recover_interrupted 的事。
from observer import app as _appmod2                    # noqa: E402
sig_log = []
_saved_kill = os.kill


def _recording_kill(pid, sig):
    sig_log.append(sig)
    if sig == 0:                              # 探测用的 kill(pid, 0) 必须照常工作
        return _saved_kill(pid, sig)
    return None                               # 其余信号只记录，一个都不真发


os.kill = _recording_kill
try:
    _appmod2.settle_slot()
    _appmod2.settle_slot()
finally:
    os.kill = _saved_kill
real_sigs = [x for x in sig_log if x != 0]
check("O32c 后续每次查看运行列表只重新探测，不再对它发任何信号",
      not real_sigs and store.get_run(REC_ALIVE)["status"] == "running",
      f"发出的信号：{real_sigs}")
alive_proc.kill()
time.sleep(0.5)
_appmod2.settle_slot()
check("O32d 旧进程真的没了之后，同一条只探测的路把它收尾成中断",
      store.get_run(REC_ALIVE)["status"] == "interrupted"
      and not (store.get_run(REC_ALIVE)["recovery_note"] or ""),
      store.get_run(REC_ALIVE)["status"])

# (c) 停没停下来查不到（unknown）-> 同样保持活动状态
unk_proc = fake_worker(REC_UNK)
make_row(REC_UNK, unk_proc.pid)
n_unk = recover_with(store.WORKER_UNKNOWN, REC_UNK)
urow = store.get_run(REC_UNK)
check("O32e 停止结果未知时保持活动状态、不放槽（上一轮这里被当成通过）",
      urow["status"] == "running" and n_unk == 0 and alive(unk_proc)
      and (store.active_run() or {}).get("run_id") == REC_UNK,
      f'{urow["status"]} / n={n_unk}')
check("O32f 说明写的是'无法确认'，不是'已被停止'",
      "无法确认" in (urow["recovery_note"] or "")
      and "已被停止" not in (urow["recovery_note"] or ""),
      (urow["recovery_note"] or "")[:40])
unk_proc.kill()
time.sleep(0.4)
store.reap_stale()
check("O32g 未知转为确认之后，只探测的那条路自行收尾",
      store.get_run(REC_UNK)["status"] == "interrupted", store.get_run(REC_UNK)["status"])

# (d) 并发完成：恢复期间工作进程自己写了 done -> 不覆盖赢家
RACE2 = "o32-race-done"
race2 = fake_worker(RACE2)
make_row(RACE2, race2.pid)
_saved_stop2 = store.stop_worker


def stop_then_worker_wins(pid, rid, grace=3.0):
    if rid == RACE2:
        store.worker_finish(rid, pid, "done", finished_at=time.time(), years_done=9,
                            full_digest="recover-race")
        return store.WORKER_GONE           # 进程确实没了，但记录已经是 done
    return _saved_stop2(pid, rid, grace)


store.stop_worker = stop_then_worker_wins
try:
    n_race = store.recover_interrupted()
finally:
    store.stop_worker = _saved_stop2
rrow2 = store.get_run(RACE2)
check("O32h 恢复期间工作进程抢先写完 done：不被覆盖成 interrupted",
      rrow2["status"] == "done" and rrow2["full_digest"] == "recover-race"
      and rrow2["years_done"] == 9 and n_race == 0,
      f'{rrow2["status"]} / n={n_race}')
race2.kill()

# (e) 身份变更：探测之后 pid 被换掉 -> 这次恢复写入落空，不动新占位的那条
SWAP = "o32-pid-swap"
swap_proc = fake_worker(SWAP, ignore_term=False)
make_row(SWAP, swap_proc.pid)
_saved_stop3 = store.stop_worker


def stop_then_pid_changes(pid, rid, grace=3.0):
    out = _saved_stop3(pid, rid, grace)
    if rid == SWAP:
        store.set_pid(rid, 424242)         # 检查之后换了工作进程
    return out


store.stop_worker = stop_then_pid_changes
try:
    n_swap = store.recover_interrupted()
finally:
    store.stop_worker = _saved_stop3
srow = store.get_run(SWAP)
check("O32i 探测之后 pid 被换掉：这次恢复写入落空，不误停新接手的工作进程",
      srow["status"] == "running" and srow["pid"] == 424242 and n_swap == 0,
      f'{srow["status"]} / pid={srow["pid"]} / n={n_swap}')
swap_proc.kill()
with store.connect() as _c:
    _c.execute("UPDATE runs SET status='interrupted' WHERE run_id IN (?,?)", (SWAP, RACE2))
    _c.execute("DELETE FROM runs WHERE run_id IN (?,?,?,?,?)",
               (REC_GONE, REC_ALIVE, REC_UNK, RACE2, SWAP))

# ---------------------------------------------------------------- 探测未知 ≠ 死亡
print("\nO23 进程探测：查不到不等于死了；回收前要比对状态与 pid")
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")

alive_proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
r_unknown = store.claim_slot(seed=21, years=5, sigma_m=0, move_mort_m=0, arm="memory",
                             label="探测未知", kind="user", engine=adapter.engine_info())
store.set_pid(r_unknown, alive_proc.pid)
store.worker_begin(r_unknown, alive_proc.pid)

real_run = store.subprocess.run


def _ps_timeout(*a, **kw):
    if a and isinstance(a[0], list) and a[0][:1] == ["ps"]:
        raise subprocess.TimeoutExpired(cmd="ps", timeout=5)
    return real_run(*a, **kw)


store.subprocess.run = _ps_timeout
try:
    probe = store.probe_worker(alive_proc.pid, r_unknown)
    check("O23a ps 超时 -> 探测结果是未知，不是死亡",
          probe == store.WORKER_UNKNOWN, f"probe={probe}")
    store.reap_stale()
    check("O23b 探测未知时不回收任务槽",
          store.get_run(r_unknown)["status"] == "running",
          store.get_run(r_unknown)["status"])
finally:
    store.subprocess.run = real_run

check("O23c ps 恢复后，pid 被别的进程占着 -> 判为 gone（pid 复用不误认）",
      store.probe_worker(alive_proc.pid, r_unknown) == store.WORKER_GONE)
store.reap_stale()
check("O23d 确认 gone 之后才回收",
      store.get_run(r_unknown)["status"] == "interrupted",
      store.get_run(r_unknown)["status"])
alive_proc.kill()

# 检查与写入之间，工作进程刚刚启动：这一轮不能把它误停
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
r_cas = store.claim_slot(seed=22, years=5, sigma_m=0, move_mort_m=0, arm="memory",
                         label="回收竞态", kind="user", engine=adapter.engine_info())
store.force_status(r_cas, "queued", pid=None,
                   created_at=time.time() - config.QUEUE_GRACE_SEC - 5)
real_probe = store.probe_worker
NEW_PID = 4242424


def _probe_then_start(pid, run_id):
    res = real_probe(pid, run_id)
    if run_id == r_cas:                      # 模拟：探测刚做完，工作进程就起来了
        store.force_status(run_id, "running", pid=NEW_PID)
    return res


store.probe_worker = _probe_then_start
try:
    store.reap_stale()
finally:
    store.probe_worker = real_probe
row = store.get_run(r_cas)
check("O23e 检查后工作进程才启动 -> 本轮不回收（状态与 pid 比对拦住了）",
      row["status"] == "running" and row["pid"] == NEW_PID,
      f"{row['status']} pid={row['pid']}")
store.force_status(r_cas, "interrupted")

# ---------------------------------------------------------------- 写请求限流
print("\nO22 写请求限流仍然有效")
saved_rate = config.WRITE_RATE_LIMIT
config.WRITE_RATE_LIMIT = 2
try:
    with TestClient(app) as c5:
        codes = [c5.post("/api/runs", json={"seed": 1, "years": 1}).status_code
                 for _ in range(5)]
    check("O22 超过每分钟写请求上限后返回 429", 429 in codes, str(codes))
finally:
    config.WRITE_RATE_LIMIT = saved_rate
    from observer import app as _appmod
    _appmod._hits.clear()

# ---------------------------------------------------------------- 浏览器自检
print("\nO18 前端回归（headless Chrome 驱动真实 app.js）")
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "", shutil.which("chromium") or "",
]
chrome = next((c for c in CHROME_CANDIDATES if c and Path(c).exists()), None)
if not chrome:
    uncov("O18 前端回归自检", "本机没有找到 Chrome / Chromium，浏览器检查未执行")
else:
    import re as _re
    import html as _html
    from observer import make_poison_js

    srv = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "observer.app:app",
         "--host", "127.0.0.1", "--port", "8799", "--log-level", "warning"],
        cwd=str(REPO), env={**os.environ, "OBSERVER_DATA_DIR": str(TEST_DATA)},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _selftest(app_url):
        out = subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--virtual-time-budget=25000", "--dump-dom",
             f"http://127.0.0.1:8799/selftest/selftest.html?app={app_url}"],
            capture_output=True, text=True, timeout=180).stdout
        m = _re.search(r'<pre id="result"[^>]*>(.*?)</pre>', out, _re.S)
        return _html.unescape(m.group(1)) if m else ""

    try:
        for _ in range(60):
            try:
                import urllib.request
                urllib.request.urlopen("http://127.0.0.1:8799/api/health", timeout=2)
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.3)
        healthy = _selftest("/static/app.js")
        if "UNDRIVABLE" in healthy or not healthy.strip():
            uncov("O18 前端回归自检",
                  "前端没有暴露 window.__obs 测试钩子（UI 分支改版后需按契约第 3 节重新挂上），"
                  "浏览器回归本轮未执行")
        else:
            hp = healthy.count("PASS ")
            hf = [ln for ln in healthy.splitlines() if ln.startswith("FAIL")]
            check(f"O18a 前端自检全绿（{hp} 项）", hp > 0 and not hf, "; ".join(hf)[:120])
            for ln in healthy.splitlines():
                if ln.startswith(("PASS", "FAIL")):
                    print("      " + ln)

            poison = make_poison_js.build()
            bad_out = _selftest("/selftest/_poison_app.js")
            bf = [ln for ln in bad_out.splitlines() if ln.startswith("FAIL")]
            race = [ln for ln in bf if ln.startswith(("FAIL T1f", "FAIL T7"))]
            xss = [ln for ln in bf if ln.startswith("FAIL T5")]
            check("O18b 把修复去掉后，串运行的检查确实会红", len(race) >= 2,
                  f"{len(race)} 条：" + "; ".join(x.split(" :: ")[0] for x in race))
            check("O18c 把转义去掉后，注入检查确实会红", len(xss) >= 3,
                  f"{len(xss)} 条：" + "; ".join(x.split(" :: ")[0] for x in xss))
            poison.unlink(missing_ok=True)
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=10)
        except Exception:  # noqa: BLE001
            srv.kill()

# ---------------------------------------------------------------- 六台引擎全接入
# "把现有全部引擎接入界面"——冻结的 EXP-01/02 也算。它们的能力比 EXP-03 少：
# 没有 macc、没有 pop_start、没有人口分项账；EXP-01 连资源波动账都没有。
# 缺的指标一律**省略键 + 能力说明**，绝不填 0 冒充测量。
print("\nO33 六台引擎：真实新建 / 逐年回放 / 按各自原始哈希核对 / 缺值不当 0")

ENGINE_CASES = [
    ("exp01", {}),
    ("exp02", {"sigma_m": 400}),
    ("exp03", {"sigma_m": 400, "move_mort_m": 50}),
    ("exp04", {"sigma_m": 400, "move_mort_m": 50, "share_m": 1000}),
    ("exp05", {"sigma_m": 0, "move_mort_m": 50, "share_m": 1000, "aid_m": 1000}),
    ("exp06", {"sigma_m": 0, "move_mort_m": 50, "share_m": 1000, "aid_m": 1000,
               "recip_m": 1000}),
]


def _frozen_engine(rel_path, name):
    """按路径只读加载引擎源码本身，用**它自己的**哈希函数核对，不借道适配层。"""
    spec = importlib.util.spec_from_file_location(name, str(REPO / rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _finish(rid, limit=3000):
    for _ in range(limit):
        row = store.get_run(rid)
        if row["status"] in ("done", "failed", "canceled", "interrupted"):
            return row
        time.sleep(0.02)
    return store.get_run(rid)


with store.connect() as _c:
    _c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")

engine_runs = {}
with TestClient(app) as c17:
    cfg = c17.get("/api/config").json()
    check("O33a 六台引擎全部登记（含冻结的 EXP-01/02）",
          set(cfg["engines"]) == {"exp01", "exp02", "exp03", "exp04", "exp05", "exp06"},
          str(sorted(cfg["engines"])))
    check("O33a2 默认引擎没有被改动", cfg["default_engine"] == "exp03", cfg["default_engine"])
    e01, e02, e03 = (cfg["engines"][k] for k in ("exp01", "exp02", "exp03"))
    check("O33b 各引擎只声明自己真有的参数",
          e01["engine_params"] == [] and e02["engine_params"] == ["sigma_m"]
          and e03["engine_params"] == ["sigma_m", "move_mort_m"],
          f'{e01["engine_params"]} / {e02["engine_params"]}')
    check("O33b2 不支持的参数被点名，前端据此不给控件",
          set(e01["unsupported_params"]) == {"sigma_m", "move_mort_m", "share_m",
                                             "aid_m", "recip_m"}
          and e02["unsupported_params"] == ["move_mort_m", "share_m", "aid_m", "recip_m"]
          and cfg["engines"]["exp06"]["unsupported_params"] == [],
          str(e02["unsupported_params"]))
    check("O33b3 能力表如实标出有没有人口分项账",
          e01["metrics"]["population_identity"] is False
          and e02["metrics"]["population_identity"] is False
          and e03["metrics"]["population_identity"] is True)
    check("O33b4 常量表只给这台引擎真有的（EXP-01 没有 SIGMA_M_MAX）",
          "SIGMA_M_MAX" not in e01["constants"] and "SIGMA_M_MAX" in e02["constants"]
          and "MOVE_MORT_M_MAX" not in e02["constants"]
          and "MOVE_MORT_M_MAX" in e03["constants"],
          str(sorted(e01["constants"]))[:60])
    check("O33b5 两个冻结基线登记了固定身份",
          e01["baseline_commit"] == "20da486" and e02["baseline_commit"] == "c5a1f18",
          f'{e01["baseline_commit"]} / {e02["baseline_commit"]}')
    frozen01 = subprocess.run(["git", "show", "20da486:exp01/verify.py"], cwd=REPO,
                              capture_output=True).stdout
    frozen02 = subprocess.run(["git", "show", "c5a1f18:exp02/verify2.py"], cwd=REPO,
                              capture_output=True).stdout
    check("O33b6 登记的 sha256 就是那两个冻结提交里的源码",
          e01["engine_sha256"] == hashlib.sha256(frozen01).hexdigest()
          and e02["engine_sha256"] == hashlib.sha256(frozen02).hexdigest())

    # 六台引擎：真实新建 -> 跑完 -> 逐年回放
    for engine, params in ENGINE_CASES:
        body = {"seed": 4242, "years": 40, "engine": engine, "arm": "memory",
                "label": "O33 " + engine, "sigma_m": 0, "move_mort_m": 0}
        body.update(params)
        r = c17.post("/api/runs", json=body)
        if r.status_code != 200:
            check(f"O33c {engine} 真实跑完并能逐年回放", False,
                  f"新建失败 {r.status_code} {str(r.json())[:70]}")
            continue
        rid = r.json()["run_id"]
        row = _finish(rid)
        engine_runs[engine] = rid
        series = c17.get(f"/api/runs/{rid}/series").json()["series"]
        y20 = c17.get(f"/api/runs/{rid}/year/20")
        detail = c17.get(f"/api/runs/{rid}").json()
        check(f"O33c {engine} 真实跑完并能逐年回放",
              row["status"] == "done" and len(series) == 41 and y20.status_code == 200
              and detail["engine"] == engine and row["full_digest"],
              f'{row["status"]} / {len(series)} 年 / {(row["error"] or "")[:40]}')

    # EXP-01/02：用**它们自己的**哈希函数核对记录器没有扰动状态
    for engine, rel_path, params in (("exp01", "exp01/verify.py", []),
                                     ("exp02", "exp02/verify2.py", [400])):
        if engine not in engine_runs:
            uncov(f"O33d {engine} 原始哈希核对", "这台引擎没跑起来，前提缺失")
            continue
        mod = _frozen_engine(rel_path, engine + "_frozen_check")
        plain = mod.make_world(4242, "", *params)
        plain_hashes = []
        for _ in range(40):
            mod.step(plain)
            plain_hashes.append(mod.state_hash(plain))
        rid = engine_runs[engine]
        api_hashes = [c17.get(f"/api/runs/{rid}/year/{t}").json()["integrity"]["state_hash"]
                      for t in range(1, 41)]
        first_bad = next((i + 1 for i, (a, b) in enumerate(zip(plain_hashes, api_hashes))
                          if a != b), None)
        check(f"O33d {engine} 逐年状态哈希与独立重跑逐字相同（记录层没扰动模型）",
              plain_hashes == api_hashes, f"第一处不同：第 {first_bad} 年" if first_bad else "")
        check(f"O33d2 {engine} 的 full_digest 也对得上",
              store.get_run(rid)["full_digest"] == mod.full_digest(plain),
              store.get_run(rid)["full_digest"][:44])

    # 缺的指标：省略键 + 能力说明，**不是 0**
    if "exp01" in engine_runs:
        rec = c17.get(f"/api/runs/{engine_runs['exp01']}/year/10").json()
        check("O33e EXP-01 没有人口恒等账：整个键都不出现（而不是给个 0）",
              "population_identity_error" not in rec["integrity"]
              and "conservation_error" in rec["integrity"],
              str(sorted(rec["integrity"]))[:70])
        check("O33e2 EXP-01 的群体没有 macc：键不出现",
              all("macc" not in b for b in rec["bands"])
              and all("size" in b and "store" in b for b in rec["bands"]))
        check("O33e3 没记的累计量不参与差分（cum/year 里根本没有这些键）",
              "births_cum" not in rec["cum"] and "deficit_cum" not in rec["cum"]
              and "clim_nominal" not in rec["cum"] and "inflow" in rec["cum"]
              and set(rec["cum"]) == set(rec["year"]), str(sorted(rec["cum"]))[:70])
        check("O33e4 契约里写明了'省略 = 未记录，禁止填 0'",
              "禁止填 0" in cfg["engines"]["exp01"]["recorded_note"],
              cfg["engines"]["exp01"]["recorded_note"][:40])
        meta = c17.get(f"/api/runs/{engine_runs['exp01']}").json()["meta"]
        check("O33e5 开局人口由真实群体求和得到，并标明来源（不是拿 0 顶）",
              meta["pop_start"] == 120 and "no pop_start" in meta["pop_start_note"],
              f'{meta["pop_start"]} / {meta["pop_start_note"][:40]}')
    if "exp02" in engine_runs:
        rec2 = c17.get(f"/api/runs/{engine_runs['exp02']}/year/10").json()
        check("O33e6 EXP-02 有资源波动账、仍没有人口分项账",
              "deficit_cum" in rec2["cum"] and "clim_nominal" in rec2["cum"]
              and "births_cum" not in rec2["cum"]
              and "population_identity_error" not in rec2["integrity"])

    # 合法参数真的传进了引擎：同种子、只改 SIGMA_M，结果必须不同
    pair = {}
    for tag, sig in (("sig0", 0), ("sig900", 900)):
        r = c17.post("/api/runs", json={"seed": 7, "years": 12, "engine": "exp02",
                                        "sigma_m": sig, "move_mort_m": 0,
                                        "label": "O33 " + tag})
        if r.status_code == 200:
            pair[tag] = _finish(r.json()["run_id"])["full_digest"]
    if len(pair) == 2:
        check("O33f EXP-02 的 SIGMA_M 真的传进了引擎（取值不同，结果就不同）",
              all(pair.values()) and pair["sig0"] != pair["sig900"],
              f'{pair["sig0"][:16]}… vs {pair["sig900"][:16]}…')
    else:
        uncov("O33f SIGMA_M 生效", f"对照运行没起全：{sorted(pair)}")

    bad_cases = [
        ({"engine": "exp01", "sigma_m": 400}, 400, "exp01 不支持 SIGMA_M"),
        ({"engine": "exp01", "move_mort_m": 50}, 400, "exp01 不支持 MOVE_MORT_M"),
        ({"engine": "exp01", "share_m": 1000}, 400, "exp01 不支持 SHARE_M"),
        ({"engine": "exp02", "move_mort_m": 50}, 400, "exp02 不支持 MOVE_MORT_M"),
        ({"engine": "exp02", "sigma_m": 1001}, 400, "SIGMA_M 越界"),
        ({"engine": "exp02", "sigma_m": 1.5}, 422, "SIGMA_M 非整数"),
        ({"engine": "exp02", "sigma_m": True}, 422, "SIGMA_M 是布尔"),
    ]
    wrong = []
    for extra, want, why in bad_cases:
        body = {"seed": 1, "years": 3, "sigma_m": 0, "move_mort_m": 0}
        body.update(extra)
        got = c17.post("/api/runs", json=body).status_code
        if got != want:
            wrong.append(f"{why}->{got}(应 {want})")
    check("O33g 不支持 / 越界 / 类型不对的参数分别被准确拒绝", not wrong, "; ".join(wrong))
    msg = c17.post("/api/runs", json={"seed": 1, "years": 3, "engine": "exp01",
                                      "sigma_m": 400, "move_mort_m": 0}).json().get("detail", "")
    check("O33g2 拒绝时说清楚是哪台引擎没有这个参数",
          "exp01" in msg and "SIGMA_M" in msg, msg[:70])
    check("O33g3 EXP-01 的合法组合仍然放行（零值不等于'不支持'）",
          c17.post("/api/runs", json={"seed": 1, "years": 1, "engine": "exp01",
                                      "sigma_m": 0, "move_mort_m": 0,
                                      "label": "O33 zero"}).status_code == 200)
    _finish((store.active_run() or {}).get("run_id") or "none", limit=1500)

    # 没有援助机制的引擎：空集合是能力事实，并明示支持范围
    if "exp01" in engine_runs:
        rel = c17.get(f"/api/runs/{engine_runs['exp01']}/relations").json()
        check("O33h 没有援助机制的引擎：关系网为空，并写明这是能力事实而非缺数据",
              rel["totals"]["edges"] == 0 and rel["engine_supports"]["aid"] is False
              and "能力事实" in rel["source"],
              str(rel["engine_supports"])[:70])
        bid = c17.get(f"/api/runs/{engine_runs['exp01']}/year/0").json()["bands"][0]["id"]
        band = c17.get(f"/api/runs/{engine_runs['exp01']}/band/{bid}").json()
        check("O33h2 群体卷宗同样明示支持范围，援助字段如实为空、轨迹照常",
              band["engine_supports"]["aid"] is False and band["aid_memory"] is None
              and band["aid_given"]["transfers"] == 0 and band["trajectory"])
    if "exp06" in engine_runs:
        rel6 = c17.get(f"/api/runs/{engine_runs['exp06']}/relations").json()
        check("O33h3 有援助机制的引擎照旧，支持范围写 true",
              rel6["engine_supports"]["aid"] is True
              and rel6["engine_supports"]["recip"] is True)

    # 事件来自真实日志/真实状态，缺的分项不猜
    if "exp01" in engine_runs:
        seen = []
        for t in range(0, 41):
            seen += c17.get(f"/api/runs/{engine_runs['exp01']}/year/{t}").json()["events"]
        kinds = sorted({e["type"] for e in seen})
        if not seen:
            uncov("O33i EXP-01 的事件", "这条运行 40 年里没有事件，前提缺失")
        else:
            bad_src = [e for e in seen if not e.get("source")]
            invented = [e for e in seen if "pop_delta" in e or "path" in e or "deaths" in e]
            check("O33i EXP-01 的事件都带来源，且没有编造模型里没有的分项",
                  not bad_src and not invented, f"{kinds} / 无来源 {len(bad_src)}")
            moves = [e for e in seen if e["type"] == "migrate"]
            if moves:
                check("O33i2 迁移事件给出真实的起讫格，迁移死亡人数如实写未记录",
                      all({"from", "to"} <= set(e) for e in moves)
                      and all("unrecorded" in e for e in moves),
                      str({k: moves[0][k] for k in ("from", "to") if k in moves[0]}))
            else:
                uncov("O33i2 EXP-01 的迁移事件", "这条运行里没有迁移，前提缺失")

with store.connect() as _c:
    _c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")

# ---------------------------------------------------------------- 运行版本身份
# 回放一条旧记录时，必须分得清"产出它的是哪一版"和"现在跑着的是哪一版"。
# 分不清的时候是 null（未知），**不是 false**——"不知道"不等于"不一样"。
print("\nO34 版本身份：记录存的是产出当时那一版，和当前服务比对不靠猜")

c07 = subprocess.run([sys.executable, str(REPO / "observer" / "c07_version_test.py")],
                     cwd=REPO, capture_output=True, text=True,
                     env={**os.environ, "OBSERVER_DATA_DIR": str(TEST_DATA)})
tail = (c07.stdout or "").strip().splitlines()[-1:] or [""]
check("O34a 服务身份自检（observer/c07_version_test.py）随主套件一起跑",
      c07.returncode == 0 and "fail=0" in tail[0], tail[0][:70] or (c07.stderr or "")[-70:])

with TestClient(app) as c18:
    ident = c18.get("/api/config").json().get("service_identity") or {}
    check("O34b 服务身份在启动时冻结，并说明来源",
          ident.get("api_version") == config.API_VERSION
          and ident.get("repo_commit_source") in ("git_startup", "explicit_build", "unknown"),
          str(ident)[:80])

    r = c18.post("/api/runs", json={"seed": 11, "years": 3, "engine": "exp03",
                                    "sigma_m": 0, "move_mort_m": 0, "label": "O34 版本"})
    if r.status_code != 200:
        uncov("O34c–f 运行版本身份", f"运行没起来：{r.status_code}")
    else:
        vid = r.json()["run_id"]
        _finish(vid)
        row = c18.get(f"/api/runs/{vid}").json()
        ver = row["version"]
        check("O34c 新运行把产出当时的契约版本与引擎身份一起存下来",
              ver["recorded"]["api_version"] == config.API_VERSION
              and ver["recorded"]["engine_sha256"]
              and ver["recorded"]["engine_path"] == "exp03/verify3.py",
              str(ver["recorded"])[:80])
        check("O34d 刚跑完的记录与当前服务是同一版",
              ver["matches_running_service"] is True
              and ver["engine_source_unchanged"] is True, ver["note"][:50])

        # 引擎源码换了一版之后回放：必须指出来，而不是默默照读。
        # 这里**不动任何冻结文件**，只在隔离测试库里把记录的 sha256 改成另一份。
        with store.connect() as _c:
            _c.execute("UPDATE runs SET engine_sha256=? WHERE run_id=?",
                       ("0" * 64, vid))
        drift = c18.get(f"/api/runs/{vid}").json()["version"]
        check("O34e 回放时引擎源码已经不是当时那份：明确指出来",
              drift["engine_source_unchanged"] is False
              and drift["matches_running_service"] is False
              and "已经不是产出这条记录时那一份" in drift["note"],
              drift["note"][:50])

        # 没存身份的旧记录 / 预生成案例：未知就是 null
        with store.connect() as _c:
            _c.execute("UPDATE runs SET engine_sha256='', api_version='', repo_commit='' "
                       "WHERE run_id=?", (vid,))
        blank = c18.get(f"/api/runs/{vid}").json()["version"]
        check("O34f 记录里没有可比对的身份：null（未知），不是 false",
              blank["matches_running_service"] is None
              and blank["engine_source_unchanged"] is None
              and "未知，不等于不同" in blank["note"], blank["note"][:60])

    preset = c18.get("/api/runs/preset-exp06-recip1000").json()
    check("O34g 预生成案例同样如实：没存服务身份就说未知，不假装是当前版本产出的",
          preset["version"]["matches_running_service"] is None
          or preset["version"]["recorded"]["api_version"] is not None,
          str(preset["version"]["matches_running_service"]))
    check("O34h 预生成案例仍然带着引擎身份，可追溯到具体源码",
          preset["version"]["recorded"]["engine_sha256"]
          and preset["version"]["recorded"]["engine_path"] == "exp06/verify6.py")

# ---------------------------------------------------------------- 续演
print("\nO35 续演（C_CONT_01）：保存后继续计算的定向验收随主套件一起跑")
_cont = subprocess.run([sys.executable, str(REPO / "observer" / "test_continuation.py"),
                        "--quick"], cwd=REPO, capture_output=True, text=True,
                       env={**os.environ, "CONT_TEST_DATA": str(TEST_DATA / "cont")})
_line = next((ln for ln in reversed((_cont.stdout or "").splitlines())
              if "通过" in ln and "失败" in ln), "")
check("O35a 续演定向验收（observer/test_continuation.py --quick）",
      _cont.returncode == 0 and "失败 0" in _line, _line.strip()[:70]
      or (_cont.stderr or "")[-70:])
print("      注：--quick 跳过 K2（300+300 长跑）、K2S（真·重启服务）与依赖它们的 K3，"
      "这三组在**完整模式**里单独跑；证据见 docs/evidence/20260913-continuation/")

# ---------------------------------------------------------------- 冻结目录
print("\nO12 冻结基线未被改动")
for rev, d in (("20da486", "exp01"), ("c5a1f18", "exp02"), ("6b6af4f", "exp03")):
    out = subprocess.run(["git", "diff", "--stat", rev, "--", d + "/"],
                         cwd=REPO, capture_output=True, text=True)
    check(f"O12 {d}/ 与基线 {rev} 逐字节相同", out.stdout.strip() == "", out.stdout.strip()[:60])

# ---------------------------------------------------------------- 汇总
npass = sum(1 for _, s, _ in RESULTS if s == "PASS")
nfail = sum(1 for _, s, _ in RESULTS if s == "FAIL")
nunc = sum(1 for _, s, _ in RESULTS if s == "UNCOVERED")
print("\n" + "=" * 96)
print(f"  通过 {npass} / 失败 {nfail} / 未覆盖 {nunc}（共 {len(RESULTS)} 项）")
print("  注：未覆盖项**不计入通过**。浏览器与线上部署的验收不在本脚本内，见 README 的验收记录。")
print("=" * 96)
shutil.rmtree(TEST_DATA, ignore_errors=True)
if nfail:
    print(f"失败 {nfail} 项")
    sys.exit(1)
if nunc:
    print(f"无失败项，但有 {nunc} 项未覆盖 —— 不能称为“全部通过”。")
