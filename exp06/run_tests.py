#!/usr/bin/env python3
"""EXP-06 正确性测试（援助记忆与优先回助）。

三态结果：PASS / FAIL / UNCOVERED。**未覆盖项不计入"通过"**；有 FAIL 则退出码非零。
用法：cd exp06 && python3 run_tests.py ; echo $?

对照版本：EXP-05 @ commit d20a015，按路径只读加载，用它**自己的**哈希判定退化。
参考实现写在本文件里（**不调用引擎的分配函数**）—— 参考实现与被测实现不能同住一个文件，
否则改一处会同时改掉两边，等于没有检验（EXP-03 的 D11 空断言就是这么放过错误的）。
"""
import sys, copy, importlib.util, pathlib
import verify6 as v

_HERE = pathlib.Path(__file__).resolve().parent
def _load(name, rel):
    sp = importlib.util.spec_from_file_location(name, _HERE.parent / rel)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
base4 = _load('exp04_frozen', 'exp04/verify4.py')     # 只读
base5 = _load('exp05_review', 'exp05/verify5.py')     # 对照版本 d20a015，只读

SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]
N = v.NEED_PC
R = {}

def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)
def mark(k, ok): R[k] = 'PASS' if ok else 'FAIL'; print(f"  => {k} {'通过' if ok else '失败'}")
def uncov(k, why): R[k] = 'UNCOVERED'; print(f"  => {k} 未覆盖：{why}")


# ---------------------------------------------------------------- 独立参考实现
def ref_settle(spec, ids, memory, aid_m, recip_m):
    """按规格文字独立重写一遍结算，**不调用 verify6 的任何函数**。
    返回 [(供给方, 接收方, 数量, 阶段)]。"""
    def _split(keys, weight, total):
        """把 total 按 weight 的相对比例整数分完（取整商 + 余数降序、id 升序）。"""
        out, rema, acc = {}, [], 0
        W = sum(weight[k] for k in keys)
        for k in keys:
            q, r = divmod(weight[k] * total, W)
            out[k] = q; acc += q; rema.append((-r, k))
        for _, k in sorted(rema)[:total - acc]:
            out[k] += 1
        return out

    def share_out(keys, weight, total):
        """**普通阶段**用：weight 是上限（预算 / 缺口），够分时各拿全额。"""
        W = sum(weight[k] for k in keys)
        if W <= 0 or total <= 0: return {k: 0 for k in keys}
        if total >= W: return {k: weight[k] for k in keys}
        return _split(keys, weight, total)

    def prio_out(keys, weight, total):
        """**优先阶段**用：weight 只是相对优先权重，**不是上限**，永远把 total 分完。
        参考实现原来在这里也用了 share_out，把引擎的同一个错误抄了一遍 ——
        参考实现必须按规格文字写，而不是照抄被测实现。"""
        W = sum(weight[k] for k in keys)
        if W <= 0 or total <= 0: return {k: 0 for k in keys}
        return _split(keys, weight, total)

    avail = {bid: store for bid, (size, store) in zip(ids, spec)}
    need = {bid: size * N for bid, (size, store) in zip(ids, spec)}
    amem = {}
    for who, rel in memory.items():
        amem[ids[who]] = {ids[d]: cum for d, cum in rel.items()}
    donors, receivers, budget, gap = [], [], {}, {}
    for bid in sorted(ids):
        sur = avail[bid] - need[bid]
        if sur > 0:
            bud = sur * aid_m // 1000
            if bud > 0: donors.append(bid); budget[bid] = bud
        elif sur < 0:
            receivers.append(bid); gap[bid] = -sur
    if not donors or not receivers: return []
    left_b, left_g, pairs = dict(budget), dict(gap), []
    # 优先阶段
    if recip_m > 0:
        prop = {}
        for d in sorted(donors):
            pb = budget[d] * recip_m // 1000
            if pb <= 0: continue
            mem = amem.get(d, {})
            targets = [r for r in sorted(receivers) if r in mem and left_g[r] > 0]
            if not targets: continue
            w = {r: max(mem[r], 1) for r in targets}
            alloc = prio_out(targets, w, min(pb, sum(left_g[r] for r in targets)))
            for r in targets:
                a = min(alloc[r], left_g[r])
                if a > 0: prop[(d, r)] = a
        by_r = {}
        for (d, r) in prop: by_r.setdefault(r, []).append(d)
        for r in sorted(by_r):
            ds = sorted(by_r[r]); tot = sum(prop[(d, r)] for d in ds)
            if tot > left_g[r]:
                cut = share_out(ds, {d: prop[(d, r)] for d in ds}, left_g[r])
                for d in ds: prop[(d, r)] = cut[d]
        for (d, r) in sorted(prop):
            a = prop[(d, r)]
            if a <= 0: continue
            pairs.append((d, r, a, 'recip')); left_b[d] -= a; left_g[r] -= a
    # 普通阶段
    ds = [d for d in sorted(donors) if left_b[d] > 0]
    rs = [r for r in sorted(receivers) if left_g[r] > 0]
    if ds and rs:
        t2 = min(sum(left_b[d] for d in ds), sum(left_g[r] for r in rs))
        if t2 > 0:
            recv = share_out(rs, left_g, t2); give = share_out(ds, left_b, t2)
            dleft, rleft, di, ri = dict(give), dict(recv), 0, 0
            while di < len(ds) and ri < len(rs):
                d, r = ds[di], rs[ri]
                if dleft[d] == 0: di += 1; continue
                if rleft[r] == 0: ri += 1; continue
                a = min(dleft[d], rleft[r])
                pairs.append((d, r, a, 'normal')); dleft[d] -= a; rleft[r] -= a
    return pairs


# ---------------------------------------------------------------- G1
hdr("G1 四本账每 tick 恒为 0（能量守恒 / 人口恒等 / 援助账 / 记忆账）")
w_c = w_p = w_a = w_m = 0
for sg in (0, 400):
    for rc in (0, 500, 1000):
        for sd in SEEDS:
            st = v.make_world(sd, sigma_m=sg, move_mort_m=50, share_m=1000,
                              aid_m=1000, recip_m=rc)
            for _ in range(80):
                v.step(st)
                w_c = max(w_c, abs(v.conservation_error(st)))
                w_p = max(w_p, abs(v.population_identity_error(st)))
                w_a = max(w_a, abs(v.aid_ledger_error(st)))
                w_m = max(w_m, abs(v.aid_memory_error(st)))
print(f"  守恒 {w_c}；人口恒等 {w_p}；援助账 {w_a}；"
      f"记忆账（在世记忆 + 随消失丢失 == 实际援助总量）{w_m}")
mark('G1 四本账恒为 0', w_c == 0 and w_p == 0 and w_a == 0 and w_m == 0)

# ---------------------------------------------------------------- G2
hdr("G2 同种子逐位一致 + 内存快照续跑一致（新状态进入快照）")
ok = True
for sd in SEEDS[:3]:
    a, _ = v.run(sd, 120, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000, recip_m=1000)
    b, snap = v.run(sd, 120, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000,
                    recip_m=1000, snap_at=60)
    c = v.resume(snap, 60)
    ok &= v.full_digest(a) == v.full_digest(b) == v.full_digest(c)
st = v.make_world(4242, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000, recip_m=1000)
for _ in range(120): v.step(st)
h0 = v.state_hash(st)
tweak = copy.deepcopy(st)
victim = next((bid for bid, b in tweak['bands'].items() if b['amem']), None)
if victim is not None:
    k = sorted(tweak['bands'][victim]['amem'])[0]
    tweak['bands'][victim]['amem'][k][0] += 1
print(f"  3 个种子重跑与快照续跑全同 = {ok}")
print(f"  改一条援助记忆 -> state_hash 改变 = {victim is not None and v.state_hash(tweak) != h0}")
mark('G2 确定性 / 快照 / 记忆进入哈希',
     ok and victim is not None and v.state_hash(tweak) != h0)

# ---------------------------------------------------------------- G3
hdr("G3 RECIP_M=0 逐步退化恒等（用对照版本自己的哈希判定）")
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

r5 = stepwise(base5, lambda sd: base5.make_world(sd, "", 400, 50, 1000, 1000),
              lambda sd: v.make_world(sd, "", 400, 50, 1000, 1000, 0))
print(f"  vs EXP-05 @d20a015 (AID=1000, RECIP=0)：{sum(1 for _, f, _ in r5 if f is None)}/7 逐步全同，"
      f"run_id 全部不同 {all(d for *_, d in r5)}")
print("  说明：EXP-05 的哈希函数不认识 amem，所以'新增的援助记忆'不会被误判成演化偏差；")
print("        而记忆确实在累加（G1 的记忆账非空即为证），演化本身逐 tick 相同。")
r4 = stepwise(base4, lambda sd: base4.make_world(sd, "", 400, 50, 1000),
              lambda sd: v.make_world(sd, "", 400, 50, 1000, 0, 0))
print(f"  vs EXP-04 @68015cc (AID=0, RECIP=0)：{sum(1 for _, f, _ in r4 if f is None)}/7 逐步全同")
for sd, f, _ in r5 + r4:
    if f is not None: print(f"      seed={sd} 在 tick={f} 处首次不同")
mark('G3 RECIP_M=0 逐步退化恒等 + 身份分开',
     all(f is None and d for _, f, d in r5) and all(f is None for _, f, _ in r4))

# ---------------------------------------------------------------- G4
hdr("G4 遍历顺序无关（并检出 recipseq）")
ok = True
for sd in SEEDS[:3]:
    a, _ = v.run(sd, 150, poison='order', sigma_m=400, move_mort_m=50, share_m=1000,
                 aid_m=1000, recip_m=1000)
    b, _ = v.run(sd, 150, poison='revorder', sigma_m=400, move_mort_m=50, share_m=1000,
                 aid_m=1000, recip_m=1000)
    ok &= v.state_hash(a) == v.state_hash(b)
print(f"  健康版 正序/逆序 逐位相同 = {ok}")

# 定向场景：两个供给方同时想回助同一个旧伙伴，供给不足 -> 统一裁决 vs 顺序先到先得
# 关键前提：旧伙伴 C 的缺口（1N）**小于**两家的优先提议之和（1N + 2N），
# 统一裁决与"先到先得"才会给出不同结果。
SEQ_SPEC = [(10, 11 * N), (10, 12 * N), (10, 9 * N)]
SEQ_MEM = {0: {2: 3 * N}, 1: {2: 4 * N}}       # A、B 都记得 C 帮过自己
def seq_pairs(pois):
    st, P, ids = v.make_recip_scenario(SEQ_SPEC, SEQ_MEM, 1000, 1000)
    st['poison'] = pois
    v.step(st)
    return sorted((rec[2], rec[3], rec[4]) for rec in st['aid_log'])
h_pairs = seq_pairs('')
sq_f = seq_pairs('recipseq,order'); sq_r = seq_pairs('recipseq,revorder')
print(f"  定向场景（两家抢着回助同一个旧伙伴）：健康版 {len(h_pairs)} 笔，统一裁决后各让一步")
print(f"  poison-recipseq 正序/逆序结果不同 = {sq_f != sq_r}")
mark('G4 顺序无关 + recipseq 检出', ok and sq_f != sq_r)

# ---------------------------------------------------------------- G5
hdr("G5 定向场景：端到端精确核对（与独立参考实现逐笔比对）")
CASES = {
    '优先改变分配（供给不足，只有一个旧伙伴）':
        ([(10, 11 * N + 7), (10, 3 * N - 5), (10, 1 * N + 3)], {0: {1: 5 * N}}, 1000, 1000),
    '同一对照但关掉优先（RECIP=0）':
        ([(10, 11 * N + 7), (10, 3 * N - 5), (10, 1 * N + 3)], {0: {1: 5 * N}}, 1000, 0),
    '优先预算只占一半（RECIP=500）':
        ([(10, 11 * N + 7), (10, 3 * N - 5), (10, 1 * N + 3)], {0: {1: 5 * N}}, 1000, 500),
    '两家抢同一个旧伙伴（统一裁决）': (SEQ_SPEC, SEQ_MEM, 1000, 1000),
    '旧伙伴不缺粮（优先阶段空转，预算回流普通阶段）':
        ([(10, 11 * N), (10, 20 * N), (10, 2 * N)], {0: {1: 5 * N}}, 1000, 1000),
    '没有任何历史关系（照常援助）':
        ([(10, 11 * N), (10, 3 * N), (10, 1 * N)], {}, 1000, 1000),
    '优先目标的缺口小于优先预算（多余部分回流）':
        ([(10, 30 * N), (10, 9 * N + 1), (10, 1 * N)], {0: {1: 9 * N}}, 1000, 1000),
}
bad = []
for name, (spec, mem, am, rc) in CASES.items():
    st, P, ids = v.make_recip_scenario(spec, mem, aid_m=am, recip_m=rc)
    exp = ref_settle(spec, ids, mem, am, rc)
    v.step(st)
    got = [(rec[2], rec[3], rec[4], rec[5]) for rec in st['aid_log']]
    same = sorted(got) == sorted(exp)
    print(f"  {name:36s} 期望 {len(exp)} 笔 / 实际 {len(got)} 笔，逐笔相同={same}，"
          f"优先 {st['recip_transfers']} 笔，分配改变={st['recip_changed']}")
    if not same: bad.append(name)
mark('G5 与独立参考实现逐笔相同', not bad)
if bad: print("      不一致：", bad)

# ---------------------------------------------------------------- G6
hdr("G6 预算与缺口上限（长跑逐 tick）+ recipbudget / recipover 检出")
def audit(poison='', years=200, seed=4242, sigma=400, recip=1000, st=None):
    single = st is not None
    if not single:
        st = v.make_world(seed, poison, sigma, 50, 1000, 1000, recip)
    over_b = over_g = n = 0
    for _ in range(1 if single else years):
        k0 = len(st['aid_log'])
        v.step(st)
        new = st['aid_log'][k0:]
        n += len(new)
        give, take = {}, {}
        for rec in new:
            give[rec[2]] = give.get(rec[2], 0) + rec[4]
            take[rec[3]] = take.get(rec[3], 0) + rec[4]
        for d, amt in give.items():
            av, nd, _ = st['aid_pre'].get(d, (0, 0, None))
            bud = max(0, av - nd) * st['aid_m'] // v.MILLE
            if amt > bud: over_b += 1
        for r, amt in take.items():
            av, nd, _ = st['aid_pre'].get(r, (0, 0, None))
            if amt > max(0, nd - av): over_g += 1
    return dict(n=n, over_b=over_b, over_g=over_g, st=st)

h = audit()
def one(pois, spec=SEQ_SPEC, mem=SEQ_MEM):
    st, P, ids = v.make_recip_scenario(spec, mem, 1000, 1000)
    st['poison'] = pois
    return audit(st=st)
# recipbudget 要让优先阶段之后**还有缺口**，普通阶段才会把预算再花一遍：
#   A 预算 2N，先优先回助旧伙伴 B（缺口 1N），还剩 C（缺口 5N，无关系）
BUD_SPEC = [(10, 12 * N), (10, 9 * N), (10, 5 * N)]
BUD_MEM = {0: {1: 5 * N}}
# recipover 要让**优先分配额超过某个目标的缺口**：两个旧伙伴，权重大的那个缺口很小
#   A 预算 11N；B 缺口 1N 但记忆权重 9N；C 缺口 9N 记忆权重 1N
OVER_SPEC = [(10, 21 * N), (10, 9 * N), (10, 1 * N)]
OVER_MEM = {0: {1: 9 * N, 2: 1 * N}}
p_b = one('recipbudget', BUD_SPEC, BUD_MEM)   # 优先支出不扣预算 -> 总量超过供给预算
p_o = one('recipover', OVER_SPEC, OVER_MEM)   # 优先分配无视缺口上限
print(f"  长跑健康版 200 年：{h['n']} 笔；超预算 {h['over_b']}，超缺口 {h['over_g']}")
print(f"  poison-recipbudget -> 超预算 {p_b['over_b']}（应 > 0）；"
      f"poison-recipover -> 超缺口 {p_o['over_g']}（应 > 0）")
if h['n'] == 0:
    uncov('G6 预算与缺口上限', '长跑里没有发生援助，前提缺失')
else:
    mark('G6 不超预算 / 不超缺口 + 两个注入检出',
         h['over_b'] == 0 and h['over_g'] == 0 and p_b['over_b'] > 0 and p_o['over_g'] > 0)

# ---------------------------------------------------------------- G7
hdr("G7 记忆只来自实际转移（并检出 recipfab）")
def mem_audit(poison='', years=200, seed=4242):
    st = v.make_world(seed, poison, 400, 50, 1000, 1000, 1000)
    bad = 0; checked = 0
    for _ in range(years):
        before = {bid: {k: list(vv) for k, vv in b['amem'].items()}
                  for bid, b in st['bands'].items()}
        k0 = len(st['aid_log'])
        v.step(st)
        moved = {}
        for rec in st['aid_log'][k0:]:
            moved[(rec[3], rec[2])] = moved.get((rec[3], rec[2]), 0) + rec[4]
        for bid, b in st['bands'].items():
            for k, vv in b['amem'].items():
                checked += 1
                was = before.get(bid, {}).get(k, [0, 0])[0]
                if vv[0] - was != moved.get((bid, k), 0):
                    bad += 1
    return checked, bad
c_h, b_h = mem_audit()
c_f, b_f = mem_audit('recipfab')
print(f"  健康版：核对 {c_h} 条记忆，与当年实际转移不符 {b_h}")
print(f"  poison-recipfab：不符 {b_f}（应 > 0）")
mark('G7 记忆增量 == 当年实际转移 + recipfab 检出', b_h == 0 and b_f > 0)

# ---------------------------------------------------------------- G8
hdr("G8 只读本年援助之前的关系快照（并检出 recipsame）")
a = v.make_world(4242, '', 400, 50, 1000, 1000, 1000)
b = v.make_world(4242, 'recipsame', 400, 50, 1000, 1000, 1000)
diff = None
for k in range(200):
    v.step(a); v.step(b)
    if diff is None and v.state_hash(a) != v.state_hash(b): diff = k + 1
print(f"  poison-recipsame（先普通后优先、并用刚更新的记忆）：首次不同于第 {diff} tick")
print("  注：它之所以会红，是因为**两个阶段的先后顺序**被换了（普通阶段先占掉预算与缺口）。")

# 另一条、也是规则真正要保证的：本轮的转移不可能在本轮制造回助资格。
st = v.make_world(4242, '', 400, 50, 1000, 1000, 1000)
snap_bad = live_bad = 0
for _ in range(200):
    before = {bid: {k: list(vv) for k, vv in bd['amem'].items()}
              for bid, bd in st['bands'].items()}
    k0 = len(st['aid_log'])
    v.step(st)
    pre = st.get('amem_pre', {})
    for bid in before:                      # 优先阶段读到的快照必须等于"本 tick 开始时"的记忆
        if bid in pre and {k: list(vv) for k, vv in pre[bid].items()} != before[bid]:
            snap_bad += 1
    for rec in st['aid_log'][k0:]:          # 本轮的供给方，其"曾受助"资格只能来自更早的年份
        d, r = rec[2], rec[3]
        if r in pre.get(d, {}) and pre[d][r][1] >= rec[0]:
            live_bad += 1
print(f"  优先阶段读到的关系快照 == 本 tick 开始时的记忆：越界 {snap_bad} 处")
print(f"  用来判定回助资格的记忆条目、其最近年份 >= 本年的：{live_bad} 处（应为 0）")
mark('G8 只读援助前快照 + recipsame 检出',
     diff is not None and snap_bad == 0 and live_bad == 0)

# ---------------------------------------------------------------- G9
hdr("G9 关系随时间保存：分裂不继承、消失记账、别人的记忆保留")
st = v.make_world(4242, '', 400, 50, 1000, 1000, 1000)
splits_checked = 0; inherit_bad = 0
for _ in range(300):
    before = set(st['bands'])
    v.step(st)
    for bid in set(st['bands']) - before:
        splits_checked += 1
        if st['bands'][bid]['amem']:
            inherit_bad += 1
print(f"  新出现的群体 {splits_checked} 个，其中带着记忆出生的 {inherit_bad}（应为 0）")
print(f"  随群体消失丢失的记忆：{st['amem_entries_dropped']} 条 / {st['amem_dropped_kcal']} kcal"
      f"（已记账，所以 G1 的记忆账仍然闭合）")
print(f"  指向已消失群体的记忆（别人对它的记忆保留，但它无法回助）：{v.amem_dangling(st)} 条")
print(f"  重复往来（双向都发生过援助的群体对）：{v.mutual_pair_count(st)} 对")
if splits_checked == 0:
    uncov('G9 分裂不继承记忆', '这段长跑里没有发生分裂，前提缺失')
else:
    mark('G9 分裂不继承 / 消失记账 / 记忆账闭合',
         inherit_bad == 0 and v.aid_memory_error(st) == 0)

# G9b：自然运行里"带着记忆的群体消失"一次都没发生（扫描里 dropped/dangling 恒为 0），
# 所以这条路径必须由定向场景承重 —— 又是 EXP-01 分裂冲突 175:0 的同一课。
print()
print("  G9b 定向场景：带记忆的群体消失（迁移死亡强度拉满，整群在迁移中全灭）")
st1, P1, ids1 = v.make_recip_scenario([(10, 3 * N), (10, 3 * N)], {0: {1: 5 * N}}, 1000, 1000)
st1['move_mort_m'] = 1000
v.step(st1)
drop_ok = (st1['amem_entries_dropped'] == 1 and st1['amem_dropped_kcal'] == 5 * N
           and v.aid_memory_error(st1) == 0)
print(f"    自己的记忆随消失丢失：{st1['amem_entries_dropped']} 条 / "
      f"{st1['amem_dropped_kcal']} kcal，记忆账 {v.aid_memory_error(st1)}")

st2, P2, ids2 = v.make_recip_scenario([(10, 25 * N), (10, 0)], {0: {1: 5 * N}}, 0, 1000)
st2['move_mort_m'] = 1000
A, B = ids2
v.step(st2)
keep_ok = (B not in st2['bands'] and A in st2['bands']
           and B in st2['bands'][A]['amem'] and v.amem_dangling(st2) == 1)
print(f"    援助者消失后、受助者对它的记忆保留：{keep_ok}（悬空条目 {v.amem_dangling(st2)}）")
print("    —— 它确实帮过我，只是再也无法回助；完整历史仍在 aid_log 里。")
mark('G9b 消失群体：自己的记忆记账丢失 / 别人对它的记忆保留', drop_ok and keep_ok)

# ---------------------------------------------------------------- G10
hdr("G10 只读诊断不回灌规则（并检出 recipdiag）")
DIAG_SPEC = [(10, 11 * N + 7), (10, 3 * N - 5), (10, 1 * N + 3)]
DIAG_MEM = {0: {1: 5 * N}}
st_h, P, ids = v.make_recip_scenario(DIAG_SPEC, DIAG_MEM, 1000, 1000)
st_b, _, _ = v.make_recip_scenario(DIAG_SPEC, DIAG_MEM, 1000, 1000)
st_b['poison'] = 'recipdiag'
v.step(st_h); v.step(st_b)
caught = v.material_hash(st_h) != v.material_hash(st_b)
print(f"  定向场景：健康版分配改变 {st_h['recip_changed']}，注入版 {st_b['recip_changed']}；"
      f"物质哈希不同 = {caught}")
mark('G10 诊断回灌会被抓到', caught)

# ---------------------------------------------------------------- G11
hdr("G11 区分'刚好帮了旧伙伴'与'优先规则改变了分配'")
zero = v.run(4242, 300, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000, recip_m=0)[0]
full = v.run(4242, 300, sigma_m=400, move_mort_m=50, share_m=1000, aid_m=1000, recip_m=1000)[0]
print(f"  RECIP=0   ：回助 {zero['repay_transfers']} 笔（**碰巧**帮到旧伙伴），"
      f"分配改变 {zero['recip_changed']} 次")
print(f"  RECIP=1000：回助 {full['repay_transfers']} 笔，优先阶段 {full['recip_transfers']} 笔，"
      f"分配改变 {full['recip_changed']} 次")
print("  '分配改变' = 同一份援助前状态下，把 RECIP_M 换成 0 再算一遍，结果不同的'格×年'次数。")
mark('G11 两者可区分（RECIP=0 时改变数必为 0，开了之后 > 0）',
     zero['recip_changed'] == 0 and full['recip_changed'] > 0
     and zero['repay_transfers'] > 0)

# ---------------------------------------------------------------- G14
hdr("G14 优先预算大于历史权重总和时，权重不得变成回助额度上限")
# 这是 2026-09-12 独立验收发现的阻塞缺陷的定向回归：
#   优先阶段的权重是"记得对方帮过我多少"，它只决定**相对份额**，**不是上限**。
#   旧实现把它传给了"权重即上限、够分各拿全额"的分配器，于是历史受助量
#   意外成了本轮回助的天花板（预算 10N、缺口 10N，却只优先给出 1N）。
BIG = [(10, 20 * N), (10, 0), (10, 0)]          # 供给方预算 10N；两个接收方缺口各 10N
MEM_ONE = {0: {1: 1 * N}}                        # 只记得 1 号帮过自己 1N（远小于预算）
st, P, ids = v.make_recip_scenario(BIG, MEM_ONE, aid_m=1000, recip_m=1000)
v.step(st)
prio = [(rec[3], rec[4]) for rec in st['aid_log'] if rec[5] == 'recip']
prio_total = sum(a for _, a in prio)
expect = min(10 * N, 10 * N)                     # min(优先预算, 目标缺口)
print(f"  预算 {10 * N} / 旧帮助者缺口 {10 * N} / 历史权重 {1 * N}")
print(f"  优先阶段实际给出 {prio_total}（期望 {expect}），收方是旧帮助者 = "
      f"{all(r == ids[1] for r, _ in prio)}")
print(f"  日志：{[(rec[4], rec[5]) for rec in st['aid_log']]}")
mark('G14 权重不是上限：优先阶段给满 min(预算, 缺口)',
     prio_total == expect and all(r == ids[1] for r, _ in prio))

# ---------------------------------------------------------------- G15
hdr("G15 历史权重同比缩放，不应改变任何结果")
# 权重只表达"谁更优先"，等比例放大缩小是同一个相对关系，结果必须逐笔相同。
# 旧实现下这条必然失败：它把权重当额度，×k 就会让优先阶段的给出量也 ×k。
MEM_TWO = {0: {1: 1 * N, 2: 2 * N}}
runs = {}
for k in (1, 7, 1000):
    mem = {0: {i: c * k for i, c in MEM_TWO[0].items()}}
    st_k, _, _ = v.make_recip_scenario(BIG, mem, aid_m=1000, recip_m=1000)
    v.step(st_k)
    runs[k] = sorted((rec[2], rec[3], rec[4], rec[5]) for rec in st_k['aid_log'])
same = runs[1] == runs[7] == runs[1000]
print(f"  权重 ×1 / ×7 / ×1000 的逐笔结果相同 = {same}")
print(f"  ×1    -> {[(a, ph) for _, _, a, ph in runs[1]]}")
print(f"  ×1000 -> {[(a, ph) for _, _, a, ph in runs[1000]]}")
mark('G15 权重同比缩放结果不变', same)

# ---------------------------------------------------------------- G12
hdr("G12 RECIP_M 参数校验 + 进入运行身份")
bad_types, bad_range = [], []
for x in (1.0, 0.5, True, '100', None):
    try: v.make_world(0, recip_m=x); bad_types.append(x)
    except TypeError: pass
    except Exception as e: bad_types.append((x, type(e).__name__))
for x in (-1, 1001, 10 ** 9):
    try: v.make_world(0, recip_m=x); bad_range.append(x)
    except ValueError: pass
edge_ok = True
for x in (0, 1, 999, 1000):
    st = v.make_world(0, recip_m=x)
    for _ in range(3): v.step(st)
    edge_ok &= all(isinstance(y, int) for y in st['stock'].values())
ids_ = {v.run_id(v.make_world(0, "", 400, 50, 1000, 1000, rc)) for rc in (0, 500, 1000)}
print(f"  非整数被 TypeError 拒绝：{not bad_types}；越界被 ValueError 拒绝：{not bad_range}")
print(f"  边界值可用且状态全整数：{edge_ok}；三个 RECIP_M 的 run_id 互不相同：{len(ids_) == 3}")
mark('G12 RECIP_M 校验 + 运行身份',
     not bad_types and not bad_range and edge_ok and len(ids_) == 3)

# ---------------------------------------------------------------- G13
hdr("G13 未登记的注入标志必须报错")
try:
    v.make_world(0, 'recipmagic'); ok = False
except ValueError: ok = True
print(f"  未登记标志被拒绝 = {ok}")
mark('G13 注入标志是封闭集合', ok)

# ---------------------------------------------------------------- 汇总
hdr("汇总")
for k in R: print(f"  {k:50s} {R[k]}")
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
