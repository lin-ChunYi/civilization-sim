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
