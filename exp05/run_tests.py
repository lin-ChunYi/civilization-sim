#!/usr/bin/env python3
"""EXP-05 正确性测试（同格食物援助）。

三态结果：PASS / FAIL / UNCOVERED。**未覆盖项不计入"通过"**；有 FAIL 则退出码非零。
用法：cd exp05 && python3 run_tests.py ; echo $?

对照基线：EXP-04 @ commit 68015cc（已审阅版本），按路径只读加载，用它**自己的**哈希判定退化。
"""
import sys, copy, importlib.util, pathlib
import verify5 as v

_HERE = pathlib.Path(__file__).resolve().parent
def _load(name, rel):
    sp = importlib.util.spec_from_file_location(name, _HERE.parent / rel)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
base3 = _load('exp03_frozen', 'exp03/verify3.py')      # 冻结基线，只读
base4 = _load('exp04_review', 'exp04/verify4.py')      # 对照版本 68015cc，只读

SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]
N = v.NEED_PC
R = {}

def expected_aid_ref(spec, ids, aid_m):
    """**独立**重算一遍援助结算，只按规格文字写，不调用 verify5 的任何分配函数。

    规格：avail = 采集 + 储粮（定向场景里采集恒为 0）；供给方先留 need，
    预算 = (avail − need) × AID_M / 1000 向下取整；接收方最多补齐 need − avail；
    T = min(ΣS, ΣD)；不够分的一侧按比例用最大余数法摊（余数降序、band_id 升序）；
    配对按 band_id 升序瀑布式匹配。
    """
    def share_out(keys, weight, total):
        W = sum(weight[k] for k in keys)
        if W <= 0 or total <= 0:
            return {k: 0 for k in keys}
        if total >= W:
            return {k: weight[k] for k in keys}
        out = {}
        rema = []
        acc = 0
        for k in keys:
            q, r = divmod(weight[k] * total, W)
            out[k] = q; acc += q; rema.append((-r, k))
        for _, k in sorted(rema)[:total - acc]:
            out[k] += 1
        return out

    avail = {bid: store for bid, (size, store) in zip(ids, spec)}
    need = {bid: size * N for bid, (size, store) in zip(ids, spec)}
    donors, receivers, budget, gap = [], [], {}, {}
    for bid in sorted(ids):
        sur = avail[bid] - need[bid]
        if sur > 0:
            bud = sur * aid_m // 1000
            if bud > 0:
                donors.append(bid); budget[bid] = bud
        elif sur < 0:
            receivers.append(bid); gap[bid] = -sur
    if not donors or not receivers:
        return [], 0
    S, D = sum(budget.values()), sum(gap.values())
    T = min(S, D)
    recv = share_out(sorted(receivers), gap, T)
    give = share_out(sorted(donors), budget, T)
    pairs, di, ri = [], 0, 0
    ds, rs = sorted(donors), sorted(receivers)
    dleft, rleft = dict(give), dict(recv)
    while di < len(ds) and ri < len(rs):
        d, r = ds[di], rs[ri]
        if dleft[d] == 0: di += 1; continue
        if rleft[r] == 0: ri += 1; continue
        amt = min(dleft[d], rleft[r])
        pairs.append((d, r, amt)); dleft[d] -= amt; rleft[r] -= amt
    return pairs, T


def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)
def mark(k, ok): R[k] = 'PASS' if ok else 'FAIL'; print(f"  => {k} {'通过' if ok else '失败'}")
def uncov(k, why): R[k] = 'UNCOVERED'; print(f"  => {k} 未覆盖：{why}")

# ---------------------------------------------------------------- F1
hdr("F1 三本账每 tick 恒为 0（能量守恒 / 人口恒等 / 援助账）")
w_c = w_p = w_a = 0
for sg in (0, 400):
    for am in (0, 250, 1000):
        for sd in SEEDS:
            st = v.make_world(sd, sigma_m=sg, move_mort_m=50, share_m=1000, aid_m=am)
            for _ in range(80):
                v.step(st)
                w_c = max(w_c, abs(v.conservation_error(st)))
                w_p = max(w_p, abs(v.population_identity_error(st)))
                w_a = max(w_a, abs(v.aid_ledger_error(st)))
print(f"  能量守恒 {w_c}；人口恒等 {w_p}；援助账（逐笔合计 == 账上总量）{w_a}")
print("  说明：援助相位只在同格群体之间搬运当年可用粮食，不增加全图食物，也不直接改人口。")
mark('F1 三本账恒为 0', w_c == 0 and w_p == 0 and w_a == 0)

# ---------------------------------------------------------------- F2
hdr("F2 同种子逐位一致 + 内存快照续跑一致")
ok = True
for sd in SEEDS[:3]:
    a, _ = v.run(sd, 120, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000)
    b, snap = v.run(sd, 120, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000, snap_at=60)
    c = v.resume(snap, 60)
    ok &= v.full_digest(a) == v.full_digest(b) == v.full_digest(c)
print(f"  3 个种子：重跑与快照续跑的 full_digest 全同 = {ok}")
mark('F2 确定性与快照续跑', ok)

# ---------------------------------------------------------------- F3
hdr("F3 AID_M=0 逐步退化恒等（用对照版本自己的哈希判定）")
def stepwise(basemod, mk_base, mk_exp, years=150):
    bad = []
    for sd in SEEDS:
        bs, es = mk_base(sd), mk_exp(sd)
        first = 0 if basemod.state_hash(bs) != basemod.state_hash(es) else None
        n = 0
        while first is None and n < years:
            basemod.step(bs); v.step(es); n += 1
            if basemod.state_hash(bs) != basemod.state_hash(es): first = n
        bad.append((sd, first, basemod.run_id(bs) != v.run_id(es)))
    return bad

r4 = stepwise(base4, lambda sd: base4.make_world(sd, "", 400, 50, 1000),
              lambda sd: v.make_world(sd, "", 400, 50, 1000, 0))
print(f"  vs EXP-04 @68015cc (SIGMA=400, MORT=50, SHARE=1000, AID=0)："
      f"{sum(1 for _, f, _ in r4 if f is None)}/7 逐步全同，run_id 全部不同 {all(d for *_, d in r4)}")
r3 = stepwise(base3, lambda sd: base3.make_world(sd, "", 400, 50),
              lambda sd: v.make_world(sd, "", 400, 50, 0, 0))
print(f"  vs EXP-03 @6b6af4f (SHARE=0, AID=0)：{sum(1 for _, f, _ in r3 if f is None)}/7 逐步全同")
for sd, f, _ in r4 + r3:
    if f is not None: print(f"      seed={sd} 在 tick={f} 处首次不同")
mark('F3 AID_M=0 逐步退化恒等 + 身份分开',
     all(f is None and d for _, f, d in r4) and all(f is None for _, f, _ in r3))

# ---------------------------------------------------------------- F4
hdr("F4 遍历顺序无关（长跑）")
ok = True
for sd in SEEDS[:3]:
    a, _ = v.run(sd, 120, poison='order', sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000)
    b, _ = v.run(sd, 120, poison='revorder', sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000)
    ok &= v.state_hash(a) == v.state_hash(b)
print(f"  健康版 正序/逆序 逐位相同 = {ok}")
mark('F4 顺序无关（长跑）', ok)

# ---------------------------------------------------------------- F5
hdr("F5 定向场景：端到端精确核对结算（含整数余量与边界）")
CASES = {
    '供给充足（S>D，接收方各自补满缺口）': ([(10, 20 * N), (10, 3 * N), (10, 1 * N)], 1000),
    '供给不足（S<D，按缺口比例最大余数法摊）': ([(10, 11 * N), (10, 12 * N), (10, 3 * N), (10, 1 * N)], 1000),
    '整数余量（余数并列，按 band_id 升序派发）': ([(10, 10 * N + 4), (10, 10 * N - 3), (10, 10 * N - 5)], 1000),
    '预算比例（AID_M=250 向下取整）': ([(10, 20 * N), (10, 5 * N)], 250),
    '无供给方（全部缺粮）': ([(10, 3 * N), (10, 1 * N)], 1000),
    '无接收方（全部有余）': ([(10, 20 * N), (10, 15 * N)], 1000),
    '多人竞争（2 给 3）': ([(10, 30 * N), (10, 25 * N), (10, 2 * N), (10, 1 * N), (10, 0)], 1000),
}
bad = []
for name, (spec, am) in CASES.items():
    st, P, ids = v.make_aid_scenario(spec, aid_m=am)
    exp, T = expected_aid_ref(spec, ids, am)
    v.step(st)
    got = [(d, r, a) for (_, _, d, r, a) in st['aid_log']]
    same = sorted(got) == sorted(exp) and st['aid_kcal'] == T
    ev_ok = st['aid_events'] == (1 if exp else 0)
    tr_ok = st['aid_transfers'] == len(exp)
    print(f"  {name:34s} 期望 {len(exp)} 笔/{T:>9} kcal，实际 {len(got)} 笔/{st['aid_kcal']:>9} kcal，"
          f"活动 {st['aid_events']}，逐笔相同={same}")
    if not (same and ev_ok and tr_ok): bad.append(name)
mark('F5 定向场景逐笔精确核对', not bad)
if bad: print("      不一致：", bad)

# ---------------------------------------------------------------- F6/F7/F10
hdr("F6/F7/F9/F10 三条边界：长跑查健康版，定向场景承重注入")
def audit(st_or_none=None, poison='', years=200, seed=4242, sigma=400, aid=1000, st=None):
    """逐 tick 用引擎记录的**援助前快照**核对边界。给了 st 就只走一个 tick。"""
    single = st is not None
    if not single:
        st = v.make_world(seed, poison, sigma, 50, 1000, aid)
    over_budget = over_gap = no_budget_donor = cross_cell = n = 0
    scarce_cells = 0
    prev_s = prev_d = 0
    for _ in range(1 if single else years):
        k0 = len(st['aid_log'])
        v.step(st)
        new = st['aid_log'][k0:]
        n += len(new)
        if st['aid_demand'] - prev_d > st['aid_supply'] - prev_s:
            scarce_cells += 1                      # 这一 tick 出现过"供不应求"
        prev_s, prev_d = st['aid_supply'], st['aid_demand']
        give, take = {}, {}
        for (_, c, d, r, a) in new:
            give[d] = give.get(d, 0) + a
            take[r] = take.get(r, 0) + a
            dc = st['aid_pre'].get(d, (0, 0, None))[2]
            rc = st['aid_pre'].get(r, (0, 0, None))[2]
            if dc != c or rc != c: cross_cell += 1
        for d, amt in give.items():
            av, nd, _ = st['aid_pre'].get(d, (0, 0, None))
            sur = av - nd
            bud = (sur * st['aid_m'] // v.MILLE) if sur > 0 else 0
            if bud <= 0: no_budget_donor += 1      # 援助前没有预算却在给 = 转赠
            elif amt > bud: over_budget += 1
        for r, amt in take.items():
            av, nd, _ = st['aid_pre'].get(r, (0, 0, None))
            if amt > max(0, nd - av): over_gap += 1
    return dict(n=n, over_budget=over_budget, over_gap=over_gap, scarce=scarce_cells,
                no_budget_donor=no_budget_donor, cross_cell=cross_cell, st=st)

h = audit()
print(f"  长跑健康版（200 年）：{h['n']} 笔；超预算 {h['over_budget']}，超缺口 {h['over_gap']}，"
      f"无预算供给方 {h['no_budget_donor']}，跨格 {h['cross_cell']}")
print(f"  其中出现过'供不应求'的 tick：{h['scarce']} —— 自然运行里供给几乎总是够用，"
      f"所以按比例摊分、转赠、超预算这几条路径在长跑上基本不被走到；")
print("  这正是必须用定向场景承重的原因（与 EXP-01 分裂冲突 175:0 同一课）。")

# 定向场景：1 个供给方、2 个接收方，供给 < 需求，且带零头
SCARCE = [(10, 11 * N + 7), (10, 3 * N - 5), (10, 1 * N + 3)]
def one_tick(poison):
    st, P, ids = v.make_aid_scenario(SCARCE, aid_m=1000)
    st['poison'] = poison
    return audit(st=st)

# 供给充足的场景（S > D）：只有它能让"接收超过缺口"这条注入承重
ABUNDANT = [(10, 30 * N), (10, 9 * N), (10, 8 * N)]
def one_tick_abundant(poison):
    st, P, ids = v.make_aid_scenario(ABUNDANT, aid_m=1000)
    st['poison'] = poison
    return audit(st=st)

s_h = one_tick('')
s_ob = one_tick('aidoverbudget')
s_ah = one_tick_abundant('')
s_og = one_tick_abundant('aidovergap')
s_rg = one_tick('aidregift')
s_sq = one_tick('aidseq')
s_cx = audit(poison='aidcross')
print(f"  定向场景（供给 < 需求）健康版：{s_h['n']} 笔，超预算 {s_h['over_budget']}，"
      f"超缺口 {s_h['over_gap']}，无预算供给方 {s_h['no_budget_donor']}")
print(f"    aidoverbudget -> 超预算 {s_ob['over_budget']}（供给<需求场景）；aidovergap -> 超缺口 {s_og['over_gap']}（供给>需求场景，健康版 {s_ah['over_gap']}）；"
      f"aidregift -> 无预算供给方 {s_rg['no_budget_donor']}；aidseq -> 笔数 {s_sq['n']}（健康版 {s_h['n']}）")
# aidseq 的顺序依赖：正序与逆序给到不同的接收方
def seq_hash(extra):
    st, P, ids = v.make_aid_scenario(SCARCE, aid_m=1000)
    st['poison'] = 'aidseq,' + extra
    v.step(st)
    return v.state_hash(st), tuple(sorted((r, a) for (_, _, _, r, a) in st['aid_log']))
ha, la = seq_hash('order'); hb, lb = seq_hash('revorder')
print(f"    aidseq 正序/逆序结果不同 = {ha != hb}（收到方不同：{la != lb}）")

if h['n'] == 0:
    uncov('F6/F7/F9/F10 三条边界', '长跑里一次援助都没发生，前提缺失')
else:
    mark('F6 供给不超预算 + aidoverbudget 检出',
         h['over_budget'] == 0 and s_h['over_budget'] == 0 and s_ob['over_budget'] > 0)
    mark('F7 接收不超缺口 + aidovergap 检出',
         h['over_gap'] == 0 and s_ah['over_gap'] == 0 and s_og['over_gap'] > 0)
    mark('F9 不跨格 + aidcross 检出', h['cross_cell'] == 0 and s_cx['cross_cell'] > 0)
    mark('F10 不得转赠 + aidregift 检出 + aidseq 顺序依赖被抓',
         h['no_budget_donor'] == 0 and s_h['no_budget_donor'] == 0
         and s_rg['no_budget_donor'] > 0 and ha != hb)

# ---------------------------------------------------------------- F8
hdr("F8 逐笔双方账目相符：凭空生粮会被守恒账抓到（aidfab）")
a = v.make_world(4242, '', 400, 50, 1000, 1000)
b = v.make_world(4242, 'aidfab', 400, 50, 1000, 1000)
err_h = err_b = 0
first = None
for k in range(200):
    v.step(a); v.step(b)
    err_h = max(err_h, abs(v.conservation_error(a)))
    e = abs(v.conservation_error(b))
    err_b = max(err_b, e)
    if first is None and e > 0: first = k + 1
print(f"  健康版守恒误差最大 {err_h}；poison-aidfab 在第 {first} tick 出现误差，最大 {err_b}")
mark('F8 供给方减少 == 接收方增加（aidfab 被守恒账抓到）', err_h == 0 and err_b > 0)

# ---------------------------------------------------------------- F11
hdr("F11 两个计数不混为一谈：一次多人援助活动 ≠ 一笔转移")
st, P, ids = v.make_aid_scenario([(10, 30 * N), (10, 25 * N), (10, 2 * N), (10, 1 * N), (10, 0)])
v.step(st)
print(f"  多人场景：活动 {st['aid_events']} 次，逐笔转移 {st['aid_transfers']} 笔，"
      f"供给方 {st['aid_donors']} 人次，接收方 {st['aid_receivers']} 人次")
long_st, _ = v.run(4242, 300, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000)
print(f"  长跑 300 年：活动 {long_st['aid_events']} 次，逐笔 {long_st['aid_transfers']} 笔，"
      f"总量 {long_st['aid_kcal']} kcal（= {long_st['aid_kcal'] / N:.1f} 人年口粮）")
mark('F11 活动数 < 笔数（多人场景）且长跑两者都有记录',
     st['aid_events'] == 1 and st['aid_transfers'] > 1
     and long_st['aid_events'] > 0 and long_st['aid_transfers'] >= long_st['aid_events'])

# ---------------------------------------------------------------- F12
hdr("F12 AID_M 参数校验（严格整数 -> 范围 -> 边界）+ 进入运行身份")
bad_types, bad_range = [], []
for x in (1.0, 0.5, True, '100', None):
    try: v.make_world(0, aid_m=x); bad_types.append(x)
    except TypeError: pass
    except Exception as e: bad_types.append((x, type(e).__name__))
for x in (-1, 1001, 10 ** 9):
    try: v.make_world(0, aid_m=x); bad_range.append(x)
    except ValueError: pass
edge_ok = True
for x in (0, 1, 999, 1000):
    st = v.make_world(0, aid_m=x)
    for _ in range(3): v.step(st)
    edge_ok &= all(isinstance(y, int) for y in st['stock'].values())
ids_ = {v.run_id(v.make_world(0, "", 400, 50, 1000, am)) for am in (0, 250, 1000)}
print(f"  非整数被 TypeError 拒绝：{not bad_types}；越界被 ValueError 拒绝：{not bad_range}")
print(f"  边界值 {{0,1,999,1000}} 可用且状态全整数：{edge_ok}；三个 AID_M 的 run_id 互不相同：{len(ids_) == 3}")
mark('F12 AID_M 校验 + 运行身份', not bad_types and not bad_range and edge_ok and len(ids_) == 3)

# ---------------------------------------------------------------- F13
hdr("F13 未登记的注入标志必须报错")
try:
    v.make_world(0, 'aidmagic'); ok = False
except ValueError: ok = True
print(f"  未登记标志被拒绝 = {ok}")
mark('F13 注入标志是封闭集合', ok)

# ---------------------------------------------------------------- 汇总
hdr("汇总")
for k in R: print(f"  {k:46s} {R[k]}")
npass = sum(1 for x in R.values() if x == 'PASS')
nfail = sum(1 for x in R.values() if x == 'FAIL')
nunc  = sum(1 for x in R.values() if x == 'UNCOVERED')
print(f"\n  通过 {npass} / 失败 {nfail} / 未覆盖 {nunc}（共 {len(R)} 项）")
print("  注：未覆盖项**不计入通过**。")
if nfail:
    print("失败：" + ", ".join(k for k, x in R.items() if x == 'FAIL')); sys.exit(1)
if nunc:
    print(f"无失败项，但有 {nunc} 项未覆盖 —— 不能称为“全部通过”。"); sys.exit(0)
print("全部必过项通过，且无未覆盖项。"); sys.exit(0)
