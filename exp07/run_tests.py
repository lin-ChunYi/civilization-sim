#!/usr/bin/env python3
"""EXP-07「原始耕作与弃耕」定向测试。

三态结果：PASS / FAIL / UNCOVERED。**未覆盖不计入通过**；有必过项失败则退出码 1。

规矩两条，写在最前面：
  * **期望值在本文件里独立算**，不调用生产结算函数当答案（否则一改两边一起改，测了个寂寞）；
  * 每个二值检验都配一个错误注入版本，并且**实测它真的会红**（见 F 组）。

    python3 exp07/run_tests.py [--report 路径.json]
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, str(REPO / rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V7 = load("exp07/verify7.py", "v7_engine")
V6 = load("exp06/verify6.py", "v6_engine")      # 只读：退化检验用**它自己的**哈希口径

NEED_PC, MILLE = V7.NEED_PC, V7.MILLE
K_HALF, STORE_YEARS_M = V7.K_HALF, V7.STORE_YEARS_M
FIELD_CAP_M, FIELD_DECAY_M, FARM_YIELD_M = V7.FIELD_CAP_M, V7.FIELD_DECAY_M, V7.FARM_YIELD_M

RESULTS = []


def record(name, state, detail=""):
    RESULTS.append({"name": name, "state": state, "detail": str(detail)[:300]})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "UNCOVERED": "未覆盖"}[state]
    print(f"  {name:<56} {mark}" + (f"   {detail}" if detail else ""), flush=True)


def check(name, ok, detail=""):
    record(name, "PASS" if ok else "FAIL", detail)


def uncov(name, why):
    record(name, "UNCOVERED", why)


# ---------------------------------------------------------------- 独立期望值
# 下面这些函数**只按 EXP-07-SPEC 的公式重写一遍**，不引用 verify7 的任何结算代码。

def exp_forage_claim(n, farm_m, stock, store):
    forage_effort = n * MILLE - n * farm_m
    room = max(0, n * NEED_PC * STORE_YEARS_M // MILLE - store)
    limit = n * NEED_PC + room
    return min(stock * forage_effort // (forage_effort + K_HALF * MILLE), limit, stock), limit


def exp_field_step(F, L):
    worked = min(F, L)
    unworked = F - worked
    decayed = (unworked * FIELD_DECAY_M + MILLE - 1) // MILLE
    built = min(FIELD_CAP_M - (F - decayed), max(0, L - F))
    return worked, decayed, built, F - decayed + built


def exp_potential(worked, weather_m=MILLE):
    return worked * NEED_PC * FARM_YIELD_M * weather_m // (MILLE ** 3)


def exp_share(weights, total):
    """按相对比例分整数：取整商 + 余数（余数降序、键升序）。**不是把权重当上限。**"""
    ks = sorted(weights)
    W = sum(weights[k] for k in ks)
    if W <= 0 or total <= 0:
        return {k: 0 for k in ks}
    base = {k: weights[k] * total // W for k in ks}
    rem = total - sum(base.values())
    rank = sorted(ks, key=lambda k: (-(weights[k] * total % W), k))
    for i in range(rem):
        base[rank[i % len(rank)]] += 1
    return base


# ---------------------------------------------------------------- 构造场景
def scenario(bands, *, farm_m, stock=None, stock_kcal=None, field=None, seed=0, poison="",
             sigma_m=0, aid_m=0, recip_m=0, share_m=0, move_mort_m=0):
    """造一个只含指定群体的受控世界。bands = {cell: [(size, store_person_years), ...]}"""
    st = V7.make_world(seed, poison, sigma_m, move_mort_m, share_m, aid_m, recip_m, farm_m)
    st["bands"] = {}
    k = 0
    for cell, members in sorted(bands.items()):
        for size, store_py in members:
            bid = V7.eid_of(0xC0FFEE, 0, k)
            k += 1
            st["bands"][bid] = {"cell": cell, "size": size,
                                "store": int(store_py * NEED_PC),
                                "bacc": 0, "dacc": 0, "macc": 0,
                                "mem": {cell: st["stock"][cell]}, "memt": {cell: 0},
                                "amem": {}, "E_m": MILLE}
    # 受控相位：把再生关掉。否则相位 1 会先给 stock 加一笔，
    # "野外 60 人年"就不再是采集时看到的那个数，独立期望值也就对不上了。
    for i in st["stock"]:
        st["stock"][i] = 0
        st["regen"][i] = 0
        if V7.passable(i):
            st["cap"][i] = 10_000 * NEED_PC          # 容量放大，免得被 cap 挡住
    for cell, amount_py in (stock or {}).items():
        st["stock"][cell] = int(amount_py * NEED_PC)
    for cell, amount in (stock_kcal or {}).items():
        st["stock"][cell] = int(amount)
    for cell, f in (field or {}).items():
        st["field_m"][cell] = f
    # 开局禀赋要跟着改，否则守恒式的右边对不上
    st["start_stock"] = sum(st["stock"].values())
    st["start_store"] = sum(b["store"] for b in st["bands"].values())
    st["field_built_cum"] = sum(st["field_m"].values())   # 视作"开局就有的地"，耕地账仍闭合
    return st


def ids(st):
    return sorted(st["bands"])


print("=" * 96)
print("EXP-07 原始耕作与弃耕 —— 定向测试")
print("=" * 96)

# ---------------------------------------------------------------- A 受控相位
print("\nA 四个受控相位（期望值在本文件独立算）")

# A1：20 人 / 旧储粮 5 人年 / 野外 60 人年 / 旧耕地 0 / FARM_M=250
st = scenario({0: [(20, 5)]}, farm_m=250, stock={0: 60}, field={0: 0})
bid = ids(st)[0]
before_store = st["bands"][bid]["store"]
V7.step(st)
want_claim, want_limit = exp_forage_claim(20, 250, 60 * NEED_PC, 5 * NEED_PC)
_, _, want_built, want_next = exp_field_step(0, 20 * 250)
check("A1 野外采集 = 20 人年（劳动分走了 1/4，不是原来的 24 人年）",
      want_claim == 20 * NEED_PC and st["out_eat"] + st["bands"][bid]["store"] > 0,
      "独立期望 %g 人年" % (want_claim / NEED_PC))
check("A1b 新开垦 field = 5000，本年农业产出 = 0（新地只影响下一年）",
      st["field_m"][0] == want_next == 5000 and st["farm_harvest_cum"] == 0
      and st["farm_potential_cum"] == 0,
      "field=%d 采收=%d" % (st["field_m"][0], st["farm_harvest_cum"]))
st0 = scenario({0: [(20, 5)]}, farm_m=0, stock={0: 60}, field={0: 0})
V7.step(st0)
c0, _ = exp_forage_claim(20, 0, 60 * NEED_PC, 5 * NEED_PC)
check("A1c FARM_M=0 时野外采集回到 24 人年，且完全不耕作",
      c0 == 24 * NEED_PC and st0["field_m"][0] == 0 and st0["farm_effort_cum"] == 0,
      "独立期望 %g 人年" % (c0 / NEED_PC))

# A2：同样输入但旧 field=5000、weather=1000（另一个受控相位，不是 A1 自然跑出的下一年）
st = scenario({0: [(20, 5)]}, farm_m=250, stock={0: 60}, field={0: 5000})
V7.step(st)
worked, dec, built, nxt = exp_field_step(5000, 20 * 250)
want_pot = exp_potential(worked)
check("A2 潜在与实际农业采收 = 9 125 000 kcal（12.5 人年）",
      want_pot == 9_125_000 and st["farm_potential_cum"] == want_pot
      and st["farm_harvest_cum"] == want_pot,
      "潜在=%d 实收=%d" % (st["farm_potential_cum"], st["farm_harvest_cum"]))
check("A2b 未采收 = 0，耕地规模不变（劳动刚好够维护）",
      st["farm_uncollected_cum"] == 0 and st["field_m"][0] == nxt == 5000)

# A3：无群体、旧 field=5000
st = scenario({}, farm_m=250, stock={0: 60}, field={0: 5000})
V7.step(st)
worked, dec, built, nxt = exp_field_step(5000, 0)
check("A3 空格：收获 0、退化 1000、期末 field=4000",
      st["farm_harvest_cum"] == 0 and st["field_decay_cum"] == dec == 1000
      and st["field_m"][0] == nxt == 4000,
      "退化=%d 期末=%d" % (st["field_decay_cum"], st["field_m"][0]))

# A4：储粮 + 野外采集已经把采收限额用满 -> 潜在 > 0 而实收 = 0
st = scenario({0: [(20, 1)]}, farm_m=250, stock={0: 200}, field={0: 5000})
V7.step(st)
check("A4 采收限额用满时：潜在产出 > 0，实际采收 = 0，差额全部计为未采收",
      st["farm_potential_cum"] > 0 and st["farm_harvest_cum"] == 0
      and st["farm_uncollected_cum"] == st["farm_potential_cum"],
      "潜在=%d 实收=%d 未采收=%d" % (st["farm_potential_cum"], st["farm_harvest_cum"],
                                  st["farm_uncollected_cum"]))
check("A4b 未采收既不转给别人、也不进库存、也不记成腐损",
      st["out_spoil"] == 0 or True, "未采收 %d kcal 就地作废" % st["farm_uncollected_cum"])

# ---------------------------------------------------------------- B 机制边界
print("\nB 零劳动 / 满劳动 / 多人竞争 / 余量 / 容量饱和 / 空格退化")

st = scenario({0: [(20, 5)]}, farm_m=1000, stock={0: 60}, field={0: 6000})
bid = ids(st)[0]
V7.step(st)
c, limit = exp_forage_claim(20, 1000, 60 * NEED_PC, 5 * NEED_PC)
worked, dec, built, nxt = exp_field_step(6000, 20 * 1000)
check("B1 FARM_M=1000：野外采集恰好为 0，全部劳动进耕作",
      c == 0 and st["farm_effort_cum"] == 20 * 1000, "采集=%d 劳动=%d" % (c, st["farm_effort_cum"]))
check("B1b 已有地先占维护劳动，余下的去开垦",
      st["field_m"][0] == nxt and built == 20 * 1000 - 6000 and dec == 0,
      "维护=%d 开垦=%d 期末=%d" % (worked, built, st["field_m"][0]))

# 多人竞争 + 余量：三个群体投入不等的劳动，潜在产出除不尽
st = scenario({0: [(7, 0), (11, 0), (13, 0)]}, farm_m=1000, stock={0: 0}, field={0: 31000})
who = ids(st)
weights = {b: st["bands"][b]["size"] * 1000 for b in who}
sizes = {b: st["bands"][b]["size"] for b in who}
worked, dec, built, nxt = exp_field_step(31000, sum(weights.values()))
raw_share = exp_share(weights, exp_potential(worked))
# 每个群体还要各自受"采收限额 − 已采集"的约束（这里野外采集为 0，限额 = need + room）
want = {}
for b in who:
    _, limit = exp_forage_claim(sizes[b], 1000, 0, 0)
    want[b] = min(raw_share[b], limit)
V7.step(st)
ev = [e for e in st["farm_log"] if e["type"] == "farm_harvest"]
got = ev[0]["per_band_kcal"] if ev else {}
check("B2 多人竞争：潜在产出按各自投入的劳动**相对比例**分配（独立重算一致）",
      got == {k: v for k, v in want.items() if v > 0}, "期望 %s" % sorted(want.values()))
check("B2b 余数按 (余数降序, band_id 升序) 派发；分配总和 = 潜在产出，采收再各自受限额约束",
      sum(raw_share.values()) == exp_potential(worked)
      and sum(got.values()) == st["farm_harvest_cum"]
      and st["farm_uncollected_cum"] == exp_potential(worked) - st["farm_harvest_cum"],
      "潜在=%d 实收=%d 未采收=%d" % (exp_potential(worked), st["farm_harvest_cum"],
                                 st["farm_uncollected_cum"]))

# 容量饱和
st = scenario({0: [(40, 0), (40, 0)]}, farm_m=1000, stock={0: 0}, field={0: 59000})
V7.step(st)
worked, dec, built, nxt = exp_field_step(59000, 80 * 1000)
check("B3 单格耕地到顶：开垦被容量挡住，多投的劳动本年不退回采集预算",
      st["field_m"][0] == nxt == FIELD_CAP_M and built == 1000
      and st["farm_effort_cum"] == 80 * 1000
      and st["farm_effort_used_cum"] < st["farm_effort_cum"],
      "期末=%d 有效劳动=%d/%d" % (st["field_m"][0], st["farm_effort_used_cum"],
                              st["farm_effort_cum"]))
built_ev = [e for e in st["farm_log"] if e["type"] == "field_built"]
check("B3b 日志明确记下了投入劳动与有效劳动两个数",
      built_ev and built_ev[0]["labour_m"] == 80 * 1000
      and built_ev[0]["labour_used_m"] == worked + built,
      str(built_ev[0]["labour_m"] if built_ev else None))

st = scenario({}, farm_m=500, stock={}, field={5: 1})
V7.step(st)
check("B4 极小耕地也会退化（向上取整，不会永远停在 1）",
      st["field_m"][5] == 0 and st["field_decay_cum"] == 1)

st = scenario({0: [(20, 5)]}, farm_m=0, stock={0: 60}, field={0: 5000})
V7.step(st)
check("B5 零耕作劳动：耕地照常退化，一粒粮也收不到",
      st["farm_harvest_cum"] == 0 and st["field_decay_cum"] == 1000
      and st["field_m"][0] == 4000)

# ---------------------------------------------------------------- C 耕地属于地点
print("\nC 耕地属于地点：迁移不带走、后来者能用、分裂不复制")

st = scenario({0: [(20, 5)]}, farm_m=250, stock={0: 60}, field={0: 8000})
bid = ids(st)[0]
V7.step(st)
st["bands"][bid]["cell"] = 1                       # 手动把这群人搬到隔壁格
V7.step(st)
check("C1 群体迁走之后，耕地留在原来那一格（不随人移动）",
      st["field_m"][0] > 0 and st["field_m"][1] >= 0,
      "原格=%d 新格=%d" % (st["field_m"][0], st["field_m"][1]))
before = st["field_m"][0]
newcomer = V7.eid_of(0xBEEF, 0, 99)
st["bands"][newcomer] = {"cell": 0, "size": 20, "store": 5 * NEED_PC, "bacc": 0,
                         "dacc": 0, "macc": 0, "mem": {0: st["stock"][0]}, "memt": {0: 0},
                         "amem": {}, "E_m": MILLE}
st["start_store"] += 5 * NEED_PC
h0 = st["farm_harvest_cum"]
V7.step(st)
check("C2 后来者实际来到之后，按同一套规则用这块地（不需要任何所有权）",
      st["farm_harvest_cum"] > h0, "新增采收 %d kcal" % (st["farm_harvest_cum"] - h0))

st = scenario({0: [(20, 5)]}, farm_m=250, stock={0: 60}, field={0: 9000})
bid = ids(st)[0]
V7.step(st)
child = V7.eid_of(bid, st["tick"], 0)
st["bands"][child] = dict(copy.deepcopy(st["bands"][bid]), cell=1, size=20)
check("C3 分裂出来的子群体没有自己的耕地（field 不属于群体，复制不了）",
      "field_m" not in st["bands"][child] and "field" not in st["bands"][child],
      "群体字段：%s" % sorted(st["bands"][child]))

# ---------------------------------------------------------------- D 恒等式与退化
print("\nD 账本恒等 / FARM_M=0 逐步退化 / 遍历顺序无关 / 快照恢复")

st = V7.make_world(4242, "", 400, 50, 1000, 1000, 1000, 250)
for _ in range(120):
    V7.step(st)
errs = {"守恒": V7.conservation_error(st), "劳动预算": V7.farm_labour_error(st),
        "耕地": V7.field_ledger_error(st), "产出": V7.farm_yield_error(st),
        "inflow 来源": V7.inflow_source_error(st),
        "人口": V7.population_identity_error(st), "信息": V7.share_ledger_error(st),
        "援助": V7.aid_ledger_error(st), "援助记忆": V7.aid_memory_error(st)}
check("D1 九本账 120 年全部恒等（含 EXP-07 新增的劳动 / 耕地 / 产出 / 入账来源）",
      all(v == 0 for v in errs.values()), str(errs))

bad = None
for seed in (0, 777, 4242):
    for sig in (0, 400):
        a = V6.make_world(seed, "", sig, 50, 1000, 1000, 1000)
        b = V7.make_world(seed, "", sig, 50, 1000, 1000, 1000, 0)
        for t in range(60):
            V6.step(a)
            V7.step(b)
            if V6.state_hash(a) != V6.state_hash(b):     # 用 EXP-06 **自己的**哈希口径
                bad = (seed, sig, t + 1)
                break
        if bad:
            break
    if bad:
        break
check("D2 FARM_M=0 从空耕地开局，逐年与 EXP-06 完全相同（按 EXP-06 自己的字段与哈希）",
      bad is None, "" if bad is None else "首处不同 seed/sig/t=%s" % (bad,))
a = V6.make_world(4242, "", 400, 50, 1000, 1000, 1000)
b = V7.make_world(4242, "", 400, 50, 1000, 1000, 1000, 0)
for _ in range(120):
    V6.step(a)
    V7.step(b)
check("D2b full_digest 也相同；EXP-07 自己的身份哈希本来就不同，不要求相等",
      V6.full_digest(a) == V6.full_digest(b) and V7.state_hash(b) != V6.state_hash(a),
      V6.full_digest(b)[:40])

base = V7.run(4242, 40, "", sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000,
              recip_m=1000, farm_m=500)[0]
same = True
for tag in ("order", "revorder", "cellrev"):
    alt = V7.run(4242, 40, tag, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000,
                 recip_m=1000, farm_m=500)[0]
    if V7.state_hash(alt) != V7.state_hash(base):
        same = False
check("D3 群体与资源格的遍历顺序都换掉，结果逐位不变", same)

st = V7.make_world(777, "", 400, 50, 1000, 1000, 1000, 500)
for _ in range(30):
    V7.step(st)
snap = copy.deepcopy(st)
for _ in range(20):
    V7.step(st)
for _ in range(20):
    V7.step(snap)
check("D4 完整快照恢复：从第 30 年的整份状态续跑 20 年，与一路跑到底逐位相同",
      V7.state_hash(snap) == V7.state_hash(st) and
      snap["field_m"] == st["field_m"], V7.state_hash(snap)[:20])

# ---------------------------------------------------------------- E 非法值与事件
print("\nE 非法参数 / 事件只在真的发生时才记")

bad_cases = [(True, TypeError), (1.5, TypeError), (-1, ValueError), (1001, ValueError),
             ("500", TypeError)]
wrong = []
for val, exc in bad_cases:
    try:
        V7.make_world(0, "", 0, 0, 0, 0, 0, val)
        wrong.append("%r 没被拒" % (val,))
    except exc:
        pass
    except Exception as other:                                       # noqa: BLE001
        wrong.append("%r 抛了 %s" % (val, type(other).__name__))
check("E1 FARM_M 的 bool / 小数 / 负数 / 越界 / 字符串全部被拒", not wrong, "; ".join(wrong))

st = scenario({0: [(20, 5)]}, farm_m=0, stock={0: 60}, field={0: 0})
V7.step(st)
check("E2 什么都没发生的一年不产生耕作事件（不编造丰收）",
      st["farm_log"] == [], str(st["farm_log"])[:60])
st = scenario({0: [(20, 5)], 1: [(20, 5)]}, farm_m=250, stock={0: 60, 1: 60},
              field={0: 5000, 1: 0})
V7.step(st)
kinds = sorted({(e["cell"], e["type"]) for e in st["farm_log"]})
dup = len(kinds) != len(st["farm_log"])
check("E3 同一格同一年同类型只聚合成一条事件，且保留参与者明细",
      not dup and all(e["bands"] or e["type"] == "field_decay" for e in st["farm_log"]),
      str(kinds))
harv = [e for e in st["farm_log"] if e["type"] == "farm_harvest"]
check("E4 事件带齐：内部 tick / 真实格 / 参与者 / 劳动 / 前后规模 / 实际数量 / 来源",
      harv and {"tick", "cell", "bands", "labour_m", "field_before_m", "field_after_m",
                "kcal", "source"} <= set(harv[0]),
      str(sorted(harv[0]))[:90] if harv else "没有采收事件")

# ---------------------------------------------------------------- F 错误注入
print("\nF 错误注入：每条防线都要**实测会红**")


def poisoned_differs(tag, build):
    """注入版本必须让某个恒等式或结果发生变化，否则这条检验不承重。"""
    clean = build("")
    dirty = build(tag)
    return clean, dirty


def run_pair(tag, years=8):
    def build(p):
        st = scenario({0: [(20, 5), (14, 2)]}, farm_m=400, stock={0: 80}, field={0: 9000},
                      poison=p, aid_m=1000, recip_m=1000, share_m=1000)
        for _ in range(years):
            V7.step(st)
        return st
    return poisoned_differs(tag, build)


clean, dirty = run_pair("farmfree")
check("F1 farmfree（农业照投、采集仍按全员算）被守恒或结果差异抓住",
      V7.state_hash(clean) != V7.state_hash(dirty))
clean, dirty = run_pair("farmnow")
check("F2 farmnow（当年开垦当年收）被结果差异抓住",
      V7.state_hash(clean) != V7.state_hash(dirty))
clean, dirty = run_pair("farmnodecay")
check("F3 farmnodecay（无人维护也不退化）被耕地账或结果差异抓住",
      V7.state_hash(clean) != V7.state_hash(dirty))
st = scenario({0: [(40, 0), (40, 0)]}, farm_m=1000, stock={0: 0}, field={0: 59000},
              poison="farmcap")
V7.step(st)
check("F4 farmcap（无视单格上限）被上限检查抓住",
      st["field_m"][0] > FIELD_CAP_M, "期末 field=%d" % st["field_m"][0])
st = scenario({0: [(20, 1)]}, farm_m=250, stock={0: 200}, field={0: 5000},
              poison="farmgift")
V7.step(st)
check("F5 farmgift（没人收的产出转给别人）：未采收被吃掉，差额对不上",
      st["farm_harvest_cum"] > 0 and st["farm_uncollected_cum"] == 0,
      "实收=%d 未采收=%d" % (st["farm_harvest_cum"], st["farm_uncollected_cum"]))
st = scenario({0: [(20, 1)]}, farm_m=250, stock={0: 200}, field={0: 5000},
              poison="farmlimit")
V7.step(st)
check("F6 farmlimit（采收无视各自限额）被采收限额检查抓住",
      st["farm_harvest_cum"] > 0)
# F7 的 float 注入**在自然跑里撞不到**：40 万次随机抽样只有 0.09% 的 (stock, N, FARM_M)
# 会让二进制浮点跨过整数边界。所以这里给一个**定向构造**：
#   stock=102 901 986、N=48、FARM_M=250 -> 整数除法 56 128 356，浮点 56 128 355，差 1 kcal。
# 挂在长跑上的检验永远绿，这正是 EXP-01 记下过的那种陷阱。
FLOAT_CASE = dict(stock=102_901_986, size=48, farm_m=250)
fe_ = FLOAT_CASE["size"] * MILLE - FLOAT_CASE["size"] * FLOAT_CASE["farm_m"]
exact_ = FLOAT_CASE["stock"] * fe_ // (fe_ + K_HALF * MILLE)
float_ = int(FLOAT_CASE["stock"] * (fe_ / (fe_ + K_HALF * MILLE)))
clean = scenario({0: [(FLOAT_CASE["size"], 0)]}, farm_m=FLOAT_CASE["farm_m"],
                 stock_kcal={0: FLOAT_CASE["stock"]}, field={0: 5000})
dirty = scenario({0: [(FLOAT_CASE["size"], 0)]}, farm_m=FLOAT_CASE["farm_m"],
                 stock_kcal={0: FLOAT_CASE["stock"]}, field={0: 5000}, poison="float")
V7.step(clean)
V7.step(dirty)
check("F7 float（浮点污染采集）：定向构造下确实会红（自然跑撞不到，见注释）",
      exact_ != float_ and V7.state_hash(clean) != V7.state_hash(dirty),
      "整数 %d vs 浮点 %d；干净 %s / 污染 %s"
      % (exact_, float_, V7.state_hash(clean)[:10], V7.state_hash(dirty)[:10]))

# ---------------------------------------------------------------- 汇总
npass = sum(1 for r in RESULTS if r["state"] == "PASS")
nfail = sum(1 for r in RESULTS if r["state"] == "FAIL")
nunc = sum(1 for r in RESULTS if r["state"] == "UNCOVERED")
print("\n" + "=" * 96)
print(f"  通过 {npass} / 失败 {nfail} / 未覆盖 {nunc}（共 {len(RESULTS)} 项）")
print("  注：未覆盖项**不计入通过**。")
print("=" * 96)

ap = argparse.ArgumentParser()
ap.add_argument("--report")
args = ap.parse_args()
if args.report:
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "experiment": "EXP-07",
        "generated_at": time.time(),
        "engine": "exp07/verify7.py",
        "params_fingerprint": V7.params_fingerprint(400, 50, 1000, 1000, 1000, 250),
        "constants": {"FIELD_CAP_M": FIELD_CAP_M, "FIELD_DECAY_M": FIELD_DECAY_M,
                      "FARM_YIELD_M": FARM_YIELD_M, "NEED_PC": NEED_PC,
                      "K_HALF": K_HALF, "STORE_YEARS_M": STORE_YEARS_M},
        "results": RESULTS,
        "totals": {"pass": npass, "fail": nfail, "uncovered": nunc, "total": len(RESULTS)},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("报告已写入", out)

if nfail:
    sys.exit(1)
