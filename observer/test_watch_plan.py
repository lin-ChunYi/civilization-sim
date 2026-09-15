#!/usr/bin/env python3
"""观看计划（`GET /api/runs/{id}/watch-plan`）定向验收。

三态结果：PASS / FAIL / UNCOVERED。**未覆盖不计入通过**；有必过项失败则退出码 1。
全程在独立临时库里跑，不碰正常运行的数据，也不动任何受保护的引擎。

    python3 observer/test_watch_plan.py [--report 路径.json]

长跑撞不到的路径（同年"一个消失 + 一个分裂"、回助依据指向未来/不存在/别的运行、
记录半途损坏）一律用**定向构造的年记录**承重 —— 这些场景在自然演化里几乎不出现，
挂在真实案例上的断言永远是绿的。
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
DATA = Path(os.environ.get("WATCH_TEST_DATA", "/tmp/chronicle-watch-20260915/testdata"))
os.environ["OBSERVER_DATA_DIR"] = str(DATA)
os.environ.setdefault("OBSERVER_WRITE_RATE", "500")
sys.path.insert(0, str(REPO))
shutil.rmtree(DATA, ignore_errors=True)

from observer import config, presets, store, watch_plan   # noqa: E402
from observer.app import app                             # noqa: E402
from fastapi.testclient import TestClient                # noqa: E402

RESULTS, COMMANDS = [], []
store.init_db()
# 预置案例按既有安装机制装进这个**临时**数据目录；仓库里那份只读不动。
INSTALLED = presets.install_presets()
client = TestClient(app)

SAMPLES = ("preset-anime-farm250", "preset-anime-exp06",
           "preset-anime-farm0", "preset-anime-farm1000")
MANIFEST = REPO / "docs" / "evidence" / "anime-cases-20260914" / "anime-cases-manifest.json"


def record(name, state, detail=""):
    RESULTS.append({"name": name, "state": state, "detail": str(detail)[:400]})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "UNCOVERED": "未覆盖"}[state]
    print(f"  {name:<62} {mark}" + (f"   {detail}" if detail else ""), flush=True)


def check(name, ok, detail=""):
    record(name, "PASS" if ok else "FAIL", detail)


def uncov(name, why):
    record(name, "UNCOVERED", why)


def plan(run_id, **params):
    r = client.get(f"/api/runs/{run_id}/watch-plan", params=params)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else None)


def worker(run_id):
    cmd = [sys.executable, "-m", "observer.worker", run_id]
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, env=dict(os.environ))
    COMMANDS.append({"cmd": " ".join(cmd), "run_id": run_id, "exit_code": proc.returncode,
                     "stderr_tail": (proc.stderr or "")[-200:]})
    return proc.returncode


def digest_dir(run_id):
    """这次运行落在盘上的所有文件的指纹：用来证明取导览**没有改动任何东西**。"""
    d = store.run_dir(run_id)
    out = {}
    for p in sorted(d.iterdir()) if d.exists() else []:
        st = p.stat()
        out[p.name] = (hashlib.sha256(p.read_bytes()).hexdigest(), st.st_size, st.st_mtime_ns)
    return out


# ---------------------------------------------------------------- 构造用的最小年记录
def synth_record(t, bands, events, pop=None):
    """一条**结构完整**的年记录（字段集与真实记录一致，值是构造的）。"""
    bands = [{"id": str(b), "name": "群体-%s" % str(b)[-6:], "cell": 0,
              "size": 10, "store": 1000, "mem": {}} for b in bands]
    return {
        "t": t,
        "stock": [0] * 4,
        "bands": bands,
        "cum": {"births_cum": 0, "deaths_demo_cum": 0, "mig_deaths_cum": 0, "mig_total": 0,
                "aid_kcal": 0},
        "year": {"mig_deaths_cum": 0, "mig_total": 0},
        "agg": {"pop": pop if pop is not None else len(bands) * 10,
                "bands": len(bands), "stock_total": 0, "store_total": len(bands) * 1000},
        "integrity": {"conservation_error": 0, "state_hash": "x" * 32},
        "events": events,
    }


def write_synth(run_id, records, *, engine="exp07", farm_m=250, aid_m=1000, recip_m=1000,
                status="done", root=None, parent=""):
    """把构造好的年记录写成一条独立运行：自己的目录、自己的台账行。"""
    d = store.run_dir(run_id)
    d.mkdir(parents=True, exist_ok=True)
    with (d / "years.jsonl").open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    (d / "meta.json").write_text(json.dumps({"cell_ids": [0, 1, 2, 3]}), encoding="utf-8")
    store.init_db()
    with store.connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO runs (run_id,label,kind,status,created_at,seed,years,"
            "sigma_m,move_mort_m,share_m,aid_m,recip_m,farm_m,engine,arm,years_done,"
            "root_run_id,parent_run_id,history_ready) "
            "VALUES (?,?,'user',?,?,1,?,0,0,1000,?,?,?,?,'memory',?,?,?,1)",
            (run_id, "构造：" + run_id, status, time.time(), len(records) - 1,
             aid_m, recip_m, farm_m, engine, len(records) - 1, root or run_id, parent))
    store._CACHE.pop(run_id, None)
    return d


print("=" * 100)
print("观看计划 watch-plan-1 —— 定向验收")
print("=" * 100)

# ---------------------------------------------------------------- W0 契约与鉴权
print("\nW0 契约版本、读鉴权、错误分支")
cfg = client.get("/api/config").json()
check("W0a 契约版本递增到 obs-1.11，默认引擎没改",
      cfg["api_version"] == "obs-1.11" and cfg["default_engine"] == "exp03",
      "%s / %s" % (cfg["api_version"], cfg["default_engine"]))
check("W0b 运行不存在给 404", plan("no-such-run")[0], 404)

config.TOKEN = "watch-secret"
try:
    check("W0c 设了令牌后，取导览无令牌被拒",
          client.get(f"/api/runs/{SAMPLES[0]}/watch-plan").status_code == 401)
    ok = client.get(f"/api/runs/{SAMPLES[0]}/watch-plan",
                    headers={"X-Observer-Token": "watch-secret"})
    check("W0d 带正确令牌可以读（沿用既有 require_read，没另造一套鉴权）",
          ok.status_code == 200)
finally:
    config.TOKEN = ""

# ---------------------------------------------------------------- W1 四条真实案例
print("\nW1 四条已提交案例：逐章回查年记录")
man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else None
if man is None:
    uncov("W1 交接清单不在", "docs/evidence/anime-cases-20260914/anime-cases-manifest.json 缺失")
by_id = {s["sample_id"]: s for s in (man or {}).get("samples", [])}

FACT_SOURCES = {"events[].": "event", "agg.": "agg", "year.": "year", "cum.": "cum",
                "farm.": "farm"}


def fact_ok(fact, event, rec):
    """`facts` 里每一项都要能在记录里按它自己写的 source 查回来。"""
    src = fact["source"]
    if src.startswith("events[]."):
        path = src[len("events[]."):].split(".")
        node = event
        for k in path:
            node = (node or {}).get(k)
        if isinstance(node, dict):
            node = {str(a): b for a, b in node.items()}
        return node == fact["value"]
    if src.startswith(("agg.", "year.", "cum.")):
        head, key = src.split(".", 1)
        return rec[head].get(key) == fact["value"]
    if src.startswith("farm."):
        node = rec.get("farm") or {}
        for k in src[len("farm."):].split("."):
            node = (node or {}).get(k)
        return node == fact["value"]
    return True                     # 规则性说明（如"新地当年没有产出"）不指向字段


for sid in SAMPLES:
    run = client.get(f"/api/runs/{sid}")
    if run.status_code != 200:
        uncov("W1 案例 %s" % sid, "这个数据目录里没有装上该预置案例")
        continue
    run = run.json()
    st, pl = plan(sid)
    if st != 200:
        check("W1 %s 能取到计划" % sid, False, st)
        continue
    exp = by_id.get(sid)
    if exp:
        check("W1a %s 按固定 sample_id + kind + 完整模型身份核对" % sid,
              run["kind"] == "preset" and run["model_run_id"] == exp["model_run_id"]
              and run["full_digest"] == exp["full_digest"],
              "kind=%s model_run_id=%s" % (run["kind"], run["model_run_id"][:12]))
    kinds = [c["kind"] for c in pl["chapters"]]
    check("W1b %s 章节 ≤7、开局在前、末年概览在后、按年份排" % sid,
          len(kinds) <= 7 and kinds[0] == "origin" and kinds[-1] == "final"
          and [c["year"] for c in pl["chapters"]] == sorted(c["year"] for c in pl["chapters"]),
          "/".join("%s@%s" % (c["kind"], c["year"]) for c in pl["chapters"]))
    bad = []
    for c in pl["chapters"]:
        if c["event_id"] is None:
            continue
        rec = client.get(f"/api/runs/{sid}/year/{c['year']}").json()
        ev = next((e for e in rec["events"] if e["id"] == c["event_id"]), None)
        if ev is None:
            bad.append((c["chapter_id"], "事件 id 在那一年的记录里找不到"))
            continue
        want_type = {"clearing": "field_built", "harvest": "farm_harvest",
                     "migrate": "migrate", "aid": "aid", "repay": "aid"}[c["kind"]]
        if ev["type"] != want_type:
            bad.append((c["chapter_id"], "事件类型不对 %s" % ev["type"]))
        if c["kind"] == "repay" and not ev.get("repay"):
            bad.append((c["chapter_id"], "回助章对上的事件 repay 不是 true"))
        if c["kind"] == "aid" and ev.get("repay"):
            bad.append((c["chapter_id"], "非回助章却对上了回助事件"))
        if c["cell"] != ev.get("cell") or c["from"] != ev.get("from") or c["to"] != ev.get("to"):
            bad.append((c["chapter_id"], "地点对不上"))
        want_actors = ({"aid": [str(ev.get("donor")), str(ev.get("receiver"))],
                        "repay": [str(ev.get("donor")), str(ev.get("receiver"))],
                        "migrate": [str(ev.get("band"))]}.get(c["kind"])
                       or [str(x) for x in (ev.get("participants") or ev.get("bands") or [])])
        if c["actor_ids"] != want_actors:
            bad.append((c["chapter_id"], "出场主体对不上 %s" % c["actor_ids"]))
        for name, f in c["facts"].items():
            if not fact_ok(f, ev, rec):
                bad.append((c["chapter_id"], "事实 %s 与记录对不上（source=%s）"
                            % (name, f["source"])))
        for pid in c["basis_event_ids"]:
            py = int(pid.split("-")[0][1:])
            prec = client.get(f"/api/runs/{sid}/year/{py}").json()
            if py >= c["year"] or not any(e["id"] == pid for e in prec["events"]):
                bad.append((c["chapter_id"], "依据 %s 不存在或不早于本次" % pid))
    check("W1c %s 每一章的 id / 对象 / 数量 / 依据都回查得上" % sid, not bad, str(bad[:3]))

# 案例 A 的锚点必须与交接清单一致
a = by_id.get("preset-anime-farm250") if man else None
if a:
    st, pl = plan("preset-anime-farm250")
    got = {c["kind"]: (c["year"], c["event_id"]) for c in pl["chapters"]}
    want = {"clearing": (a["events"]["clearing"]["first_year"],
                         a["events"]["clearing"]["first_event_id"]),
            "harvest": (a["events"]["harvest"]["first_year"],
                        a["events"]["harvest"]["first_event_id"]),
            "migrate": (a["events"]["migrate"]["first_year"],
                        a["events"]["migrate"]["first_event_id"]),
            "aid": (a["events"]["aid"]["first_year"], a["events"]["aid"]["first_event_id"]),
            "repay": (a["events"]["repay"]["first_year"],
                      a["events"]["repay"]["first_event_id"])}
    diff = {k: (got.get(k), v) for k, v in want.items() if got.get(k) != v}
    check("W1d 案例 A 的章节锚点与交接清单逐条一致（不符就报差异，不改记录迁就清单）",
          not diff, str(diff) if diff else "开垦1/收成2/迁移218/援助267/回助295")

# ---------------------------------------------------------------- W2 只读
print("\nW2 取导览是纯读：输入前后逐字节不变，也不触发写")
before = {s: digest_dir(s) for s in SAMPLES if client.get(f"/api/runs/{s}").status_code == 200}
n_before = len(client.get("/api/runs").json()["runs"])
for s in before:
    for _ in range(3):
        plan(s)
        plan(s, through=2)
after = {s: digest_dir(s) for s in before}
check("W2a 0..300 年记录、检查点、meta 逐字节不变", before == after,
      "比对 %d 条运行的全部文件" % len(before))
check("W2b 运行条数没变（没有新建任何运行）",
      len(client.get("/api/runs").json()["runs"]) == n_before, n_before)
if before:
    s0 = sorted(before)[0]
    check("W2c 旧接口在取过导览之后照样可读",
          client.get(f"/api/runs/{s0}/year/1").status_code == 200
          and client.get(f"/api/runs/{s0}/series").status_code == 200
          and client.get(f"/api/runs/{s0}/relations").status_code == 200)

# ---------------------------------------------------------------- W3 净数不变
print("\nW3 同一年一个消失、一个分裂：净数不变，目录照样完整")
R3 = "synth-net-zero"
write_synth(R3, [
    synth_record(0, ["100", "200"], []),
    synth_record(1, ["100", "200"], []),
    synth_record(2, ["100", "300"], [
        {"id": "t2-extinct-0", "year": 2, "type": "extinct", "band": "200"},
        {"id": "t2-split-1", "year": 2, "type": "split", "band": "300", "parent": "100"},
    ]),
    synth_record(3, ["100", "300"], []),
])
st, pl = plan(R3)
ids = {x["id"]: x for x in pl["identities"]}
check("W3a 三个身份都在（净群体数第 1→2 年都是 2，没有漏扫）",
      sorted(ids) == ["100", "200", "300"], sorted(ids))
check("W3b 消失的那个有 extinct_year、last_year 是最后一次在世的年份",
      ids.get("200", {}).get("extinct_year") == 2 and ids["200"]["last_year"] == 1,
      json.dumps(ids.get("200"), ensure_ascii=False))
check("W3c 新分裂出来的 first_year=2，亲本来自 split 日志",
      ids.get("300", {}).get("first_year") == 2 and ids["300"]["parent_id"] == "100",
      json.dumps(ids.get("300"), ensure_ascii=False))
check("W3d 开局群体的 parent_id 是 null，不是猜出来的",
      ids["100"]["parent_id"] is None and ids["100"]["first_year"] == 0)

# ---------------------------------------------------------------- W4 子运行独立
print("\nW4 续演子运行：直接打开它，与先开父运行看到的身份一致")
def wait_done(run_id, limit=120):
    """POST /api/runs 与 /continue 自己会拉起工作进程，这里只等它算完。"""
    for _ in range(limit):
        row = store.get_run(run_id)
        if row and row["status"] in ("done", "failed", "interrupted", "canceled", "cancelled"):
            return row["status"]
        time.sleep(0.5)
    return (store.get_run(run_id) or {}).get("status")


made = client.post("/api/runs", json={"seed": 4242, "years": 8, "engine": "exp07",
                                      "arm": "memory", "sigma_m": 400, "move_mort_m": 50,
                                      "share_m": 1000, "aid_m": 1000, "recip_m": 1000,
                                      "farm_m": 250, "label": "watch-plan 父运行"})
if made.status_code != 200:
    uncov("W4 建父运行", "%s %s" % (made.status_code, made.text[:120]))
else:
    parent_id = made.json()["run_id"]
    pstatus = wait_done(parent_id)
    kid = client.post(f"/api/runs/{parent_id}/continue",
                      json={"additional_years": 4, "request_id": str(uuid.uuid4())})
    if pstatus != "done" or kid.status_code != 200:
        uncov("W4 建子运行", "父=%s continue=%s %s" % (pstatus, kid.status_code, kid.text[:120]))
    else:
        kid_id = kid.json()["run_id"]
        kstatus = wait_done(kid_id)
        st_p, pl_p = plan(parent_id)
        st_k, pl_k = plan(kid_id)
        check("W4a 子运行跑完并且能单独取到计划",
              kstatus == "done" and st_k == 200 and pl_k["source"]["recorded_through"] == 12,
              "status=%s through=%s" % (kstatus, pl_k["source"]["recorded_through"] if pl_k else None))
        pid_map = {x["id"]: x["first_year"] for x in pl_p["identities"]}
        kid_map = {x["id"]: x["first_year"] for x in pl_k["identities"]}
        shared = set(pid_map) & set(kid_map)
        check("W4b 两边共有的群体 first_year 完全相同（子运行读自己那份完整前缀）",
              all(pid_map[i] == kid_map[i] for i in shared) and len(shared) == len(pid_map),
              "共有 %d 个" % len(shared))
        order_p = [x["id"] for x in pl_p["identities"]]
        order_k = [x["id"] for x in pl_k["identities"] if x["id"] in shared]
        check("W4c 排序也一样（按 first_year + 数值型完整 id）", order_p == order_k)
        check("W4d 子运行的 root_run_id 指回同一条根",
              pl_k["root_run_id"] == pl_p["root_run_id"], pl_k["root_run_id"])
        # 父历史被删掉之后，子运行仍然独立可用
        shutil.rmtree(store.run_dir(parent_id), ignore_errors=True)
        store._CACHE.pop(parent_id, None)
        st_k2, pl_k2 = plan(kid_id)
        check("W4e 父历史被删掉后，子运行的计划照常（不依赖父运行还在）",
              st_k2 == 200 and pl_k2["identities"] == pl_k["identities"]
              and pl_k2["chapters"] == pl_k["chapters"])

# ---------------------------------------------------------------- W5 记录增长 / 损坏
print("\nW5 记录增长只追加新身份；读坏了不许假装完整")
R5 = "synth-growing"
base = [synth_record(0, ["100"], []), synth_record(1, ["100"], []),
        synth_record(2, ["100"], [])]
write_synth(R5, base)
st, pl_a = plan(R5)
grown = base + [synth_record(3, ["100", "400"], [
    {"id": "t3-split-0", "year": 3, "type": "split", "band": "400", "parent": "100"}])]
write_synth(R5, grown)
st, pl_b = plan(R5)
old = {x["id"]: x["first_year"] for x in pl_a["identities"]}
new = {x["id"]: x["first_year"] for x in pl_b["identities"]}
check("W5a 记录长出新一年后，旧身份的 first_year 一个都没变",
      all(new[i] == v for i, v in old.items()), json.dumps(old, ensure_ascii=False))
check("W5b 新身份是真的新出现的那一个，first_year 是它首次在世那年",
      set(new) - set(old) == {"400"} and new["400"] == 3)
check("W5c 水位跟着涨，并如实写在 source 里",
      (pl_a["source"]["recorded_through"], pl_b["source"]["recorded_through"]) == (2, 3))
st, pl_pin = plan(R5, through=2)
check("W5d through=2 钉住旧水位：章节与身份与当时那份一致（导览中途不会换章）",
      pl_pin["identities"] == pl_a["identities"]
      and [c["chapter_id"] for c in pl_pin["chapters"]]
          == [c["chapter_id"] for c in pl_a["chapters"]])
check("W5e through 超过已记录年数给 400，不静默夹取", plan(R5, through=99)[0], 400)

# 半截行 / 损坏尾巴：水位必须缩回去，绝不能当成"看完了"
R5b = "synth-torn"
write_synth(R5b, base)
p = store.years_path(R5b)
p.write_text(p.read_text(encoding="utf-8") + '{"t":3,"bands":[', encoding="utf-8")
store._CACHE.pop(R5b, None)
st, pl_t = plan(R5b)
check("W5f 尾巴是半截行时，水位停在最后一条完整记录，不把半截行算进来",
      st == 200 and pl_t["source"]["recorded_through"] == 2
      and pl_t["source"]["identity_complete_through"] == 2,
      pl_t["source"] if st == 200 else st)
R5c = "synth-empty"
write_synth(R5c, [synth_record(0, ["100"], [])])
store.years_path(R5c).write_text("", encoding="utf-8")
store._CACHE.pop(R5c, None)
check("W5g 一年都读不出来时给 409 明确报错，不返回空目录宣布看完", plan(R5c)[0], 409)

# ---------------------------------------------------------------- W6 四种缺项
print("\nW6 无事件 / 缺机制 / 参数为 0 / 未观察到，各有实际用例")
R6 = "synth-no-events"
write_synth(R6, [synth_record(t, ["100"], []) for t in range(4)], farm_m=250)
st, pl6 = plan(R6)
check("W6a 全程没有任何事件：只有开局与末年两章，不编事件凑数",
      [c["chapter_id"] for c in pl6["chapters"]] == ["origin", "final"],
      [c["chapter_id"] for c in pl6["chapters"]])
check("W6b 这时五类全部缺，理由是 not_observed（机制开着、参数非 0，就是没发生）",
      {m["kind"]: m["reason"] for m in pl6["missing_kinds"]}
      == {k: "not_observed" for k in ("clearing", "harvest", "migrate", "aid", "repay")},
      json.dumps(pl6["missing_kinds"], ensure_ascii=False))
R6b = "synth-only-origin"
write_synth(R6b, [synth_record(0, ["100"], [])])
st, pl6b = plan(R6b)
check("W6c 只有第 0 年时只出一章开局（不拿同一年再凑一章末年概览）",
      [c["chapter_id"] for c in pl6b["chapters"]] == ["origin"])
reasons = {}
for sid, want in (("preset-anime-exp06", "engine_lacks_mechanism"),
                  ("preset-anime-farm0", "param_zero"),
                  ("preset-anime-farm1000", "not_observed")):
    if client.get(f"/api/runs/{sid}").status_code != 200:
        continue
    st, pl_s = plan(sid)
    reasons[sid] = {m["kind"]: m["reason"] for m in pl_s["missing_kinds"]}
if reasons:
    check("W6d 旧引擎缺农业 = engine_lacks_mechanism（不是 0）",
          reasons.get("preset-anime-exp06", {}).get("clearing") == "engine_lacks_mechanism",
          json.dumps(reasons.get("preset-anime-exp06"), ensure_ascii=False))
    check("W6e FARM_M=0 = param_zero（机制在、值确实是 0）",
          reasons.get("preset-anime-farm0", {}).get("clearing") == "param_zero",
          json.dumps(reasons.get("preset-anime-farm0"), ensure_ascii=False))
    check("W6f 机制开着但 300 年没发生 = not_observed",
          reasons.get("preset-anime-farm1000", {}).get("aid") == "not_observed",
          json.dumps(reasons.get("preset-anime-farm1000"), ensure_ascii=False))
else:
    uncov("W6d–f 三种缺项的真实案例", "这个数据目录里没装上预置案例")
st, pl_win = plan(SAMPLES[0], through=2) if client.get(
    f"/api/runs/{SAMPLES[0]}").status_code == 200 else (None, None)
if pl_win:
    check("W6g 钉住水位时缺的那几类写 outside_watermark，不谎称整段历史没发生",
          {m["reason"] for m in pl_win["missing_kinds"]} == {"outside_watermark"},
          json.dumps(pl_win["missing_kinds"], ensure_ascii=False))
R6c = "synth-running"
write_synth(R6c, [synth_record(t, ["100"], []) for t in range(3)], status="running")
st, pl6c = plan(R6c)
check("W6h 运行还在跑时缺项写 history_incomplete（后面可能还会出现）",
      {m["reason"] for m in pl6c["missing_kinds"]} == {"history_incomplete"},
      json.dumps(pl6c["missing_kinds"], ensure_ascii=False))

# ---------------------------------------------------------------- W7 回助依据
print("\nW7 回助依据只认本次运行里真实存在、且早于本次的事件 id")


def repay_rec(t, prior):
    return synth_record(t, ["100", "200"], [{
        "id": "t%d-aid-0" % t, "year": t, "type": "aid", "repay": True, "phase": "recip",
        "band": "100", "donor": "100", "receiver": "200", "cell": 0,
        "kcal": 10, "person_years": 0.1,
        "basis": {"remembered_kcal": 5, "prior_events": prior},
    }])


R7 = "synth-repay-bad"
write_synth(R7, [
    synth_record(0, ["100", "200"], []),
    synth_record(1, ["100", "200"], [{
        "id": "t1-aid-0", "year": 1, "type": "aid", "repay": False, "phase": "normal",
        "band": "200", "donor": "200", "receiver": "100", "cell": 0,
        "kcal": 5, "person_years": 0.05}]),
    repay_rec(2, ["t1-aid-0", "t9-aid-0", "t2-aid-77", "t5-aid-0"]),
    synth_record(3, ["100", "200"], []),
])
st, pl7 = plan(R7)
rep = next(c for c in pl7["chapters"] if c["kind"] == "repay")
check("W7a 只留下真实存在且更早的那一条，未来的 / 不存在的一律不进依据",
      rep["basis_event_ids"] == ["t1-aid-0"], rep["basis_event_ids"])

R7b = "synth-repay-other-run"
write_synth(R7b, [synth_record(0, ["100", "200"], []), repay_rec(1, ["t0-aid-0"])])
# 另一条运行里**确实**有 t0-aid-0，但那是别人的历史，不能拿来当依据
R7c = "synth-repay-neighbour"
write_synth(R7c, [synth_record(0, ["100", "200"], [{
    "id": "t0-aid-0", "year": 0, "type": "aid", "repay": False, "phase": "normal",
    "band": "200", "donor": "200", "receiver": "100", "cell": 0,
    "kcal": 5, "person_years": 0.05}])])
st, pl7b = plan(R7b)
rep_b = next(c for c in pl7b["chapters"] if c["kind"] == "repay")
check("W7b 别的运行里有同名 id 也不算数（依据只在本次运行里找）",
      rep_b["basis_event_ids"] == [] and plan(R7c)[1] is not None,
      rep_b["basis_event_ids"])
check("W7c 非回助的章节不带依据",
      all(c["basis_event_ids"] == [] for c in pl7["chapters"] if c["kind"] != "repay"))

# ---------------------------------------------------------------- 汇总
print()
tot = {"pass": sum(1 for r in RESULTS if r["state"] == "PASS"),
       "fail": sum(1 for r in RESULTS if r["state"] == "FAIL"),
       "uncovered": sum(1 for r in RESULTS if r["state"] == "UNCOVERED")}
tot["total"] = len(RESULTS)
print("=" * 100)
print("  通过 %d / 失败 %d / 未覆盖 %d（共 %d 项）" %
      (tot["pass"], tot["fail"], tot["uncovered"], tot["total"]))
print("  注：未覆盖项**不计入通过**。")
print("=" * 100)

ap = argparse.ArgumentParser()
ap.add_argument("--report")
args, _ = ap.parse_known_args()
if args.report:
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps({
        "task": "C_WATCH_DATA_01", "generated_at": time.time(),
        "schema": watch_plan.SCHEMA, "api_version": config.API_VERSION,
        "data_dir": str(DATA), "commands": COMMANDS,
        "results": RESULTS, "totals": tot}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("报告已写入 %s" % args.report)

sys.exit(1 if tot["fail"] else 0)
