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

    # 单并发
    store.set_status(run_id, "running")
    dup = client.post("/api/runs", json={"seed": 1, "years": 5})
    check("O8 已有任务在跑时拒绝重复启动", dup.status_code == 409, str(dup.json())[:60])

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
    store.set_status(slot, "interrupted")        # 模拟服务端判定中断
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
             f"http://127.0.0.1:8799/static/selftest.html?app={app_url}"],
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
        hp = healthy.count("PASS ")
        hf = [ln for ln in healthy.splitlines() if ln.startswith("FAIL")]
        check(f"O18a 前端自检全绿（{hp} 项）", hp > 0 and not hf, "; ".join(hf)[:120])
        for ln in healthy.splitlines():
            if ln.startswith(("PASS", "FAIL")):
                print("      " + ln)

        poison = make_poison_js.build()
        bad_out = _selftest("/static/_poison_selftest.js")
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
