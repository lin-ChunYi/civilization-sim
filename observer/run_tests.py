"""OBS-01 验收测试。

沿用本项目的三态结果：PASS / FAIL / UNCOVERED。
**未覆盖不计入通过**；有必过项失败则退出码 1。
测试用独立的数据目录（observer/data_test），不碰正常运行的数据。
"""
from __future__ import annotations

import json
import os
import shutil
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
          len(pre) == 1 and pre[0]["status"] == "done", str([p["run_id"] for p in pre]))

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
        pre = next(x for x in c6.get("/api/runs").json()["runs"] if x["kind"] == "preset")
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
        rec3 = c7.get(f"/api/runs/{next(x for x in c7.get('/api/runs').json()['runs'] if x['kind'] == 'preset')['run_id']}/year/1").json()
        check("O25m exp03 的记录里没有 aid 段（前端要容忍缺席）", "aid" not in rec3)

# ---------------------------------------------------------------- EXP-06 接入
print("\nO26 EXP-06 引擎接入观察台（援助记忆与优先回助可展示）")
with store.connect() as c:
    c.execute("UPDATE runs SET status='done' WHERE status IN ('queued','running')")
with TestClient(app) as c8:
    cfg = c8.get("/api/config").json()
    check("O26a /api/config 里有 exp06 且契约版本更新",
          "exp06" in cfg.get("engines", {}) and cfg["api_version"] == "obs-1.4",
          str(sorted(cfg.get("engines", {}))))
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
        pre = next(x for x in c8.get("/api/runs").json()["runs"] if x["kind"] == "preset")
        rec3 = c8.get(f"/api/runs/{pre['run_id']}/year/1").json()
        check("O26l exp03 的记录里没有 recip 段、群体也没有 aid_memory（前端要容忍缺席）",
              "recip" not in rec3 and "aid_memory" not in rec3["bands"][0])

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
