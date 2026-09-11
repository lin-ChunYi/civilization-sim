#!/usr/bin/env python3
"""EXP-03 正确性测试。

三态结果：PASS / FAIL / UNCOVERED。
**未覆盖项不计入"通过"**；有 FAIL 则退出码非零。
用法：cd exp03 && python3 run_tests.py ; echo $?
"""
import sys, copy, importlib.util, pathlib
import verify3 as v

_HERE = pathlib.Path(__file__).resolve().parent
def _load(name, rel):
    sp = importlib.util.spec_from_file_location(name, _HERE.parent / rel)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
base1 = _load('exp01_frozen', 'exp01/verify.py')      # 冻结基线，只读
base2 = _load('exp02_frozen', 'exp02/verify2.py')     # 冻结基线，只读

SEEDS  = [0, 12345, 777, 4242, 99, 31337, 2026]
SIGMAS = [0, 400]
MORTS  = [0, 20, 50, 100]
Y = 300
R = {}

def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)
def mark(k, ok): R[k] = 'PASS' if ok else 'FAIL'; print(f"  => {k} {'通过' if ok else '失败'}")
def uncov(k, why): R[k] = 'UNCOVERED'; print(f"  => {k} 未覆盖：{why}")

GRID = [(sg, mm) for sg in SIGMAS for mm in MORTS]

# ---------------------------------------------------------------- D1
hdr("D1 守恒 + 人口恒等式（每 tick，全部 8 个组合 × 7 种子）")
w_c = w_p = 0
for sg, mm in GRID:
    for sd in SEEDS:
        st = v.make_world(sd, sigma_m=sg, move_mort_m=mm)
        for _ in range(Y):
            v.step(st)
            w_c = max(w_c, abs(v.conservation_error(st)))
            w_p = max(w_p, abs(v.population_identity_error(st)))
print(f"  能量守恒最大绝对误差 {w_c}")
print(f"  人口恒等式（期末 = 期初 + 出生 − 原规则死亡 − 迁移死亡）最大绝对误差 {w_p}")
mark('D1 守恒 + 人口恒等式', w_c == 0 and w_p == 0)

# ---------------------------------------------------------------- D2 / D3
hdr("D2 重放确定性 / D3 快照续跑")
ok2 = ok3 = True
for sg, mm in GRID:
    a = all(v.state_hash(v.run(sd, Y, sigma_m=sg, move_mort_m=mm)[0]) ==
            v.state_hash(v.run(sd, Y, sigma_m=sg, move_mort_m=mm)[0]) for sd in SEEDS)
    b = True
    for sd in SEEDS:
        full, snap = v.run(sd, Y, snap_at=150, sigma_m=sg, move_mort_m=mm)
        b &= (v.state_hash(full) == v.state_hash(v.resume(snap, Y - 150)))
    print(f"  SIGMA={sg:<4} MORT={mm:<4} 重放 {'一致' if a else '不一致'} | 快照续跑 {'一致' if b else '不一致'}")
    ok2 &= a; ok3 &= b
mark('D2 重放确定性', ok2); mark('D3 快照续跑', ok3)

# ---------------------------------------------------------------- D4
hdr("D4 完整状态比较：新增字段确实进了 state_hash")
st, _ = v.run(12345, 60, sigma_m=400, move_mort_m=50)
h0 = v.state_hash(st); sub = {}
for f in ('move_mort_m', 'mig_deaths_cum', 'births_cum', 'deaths_demo_cum',
          'need_cum', 'personyear_cum', 'macc_global'):
    s2 = copy.deepcopy(st); s2[f] += 1
    sub[f] = v.state_hash(s2) != h0
    print(f"  账本字段 {f:<18} -> 哈希{'改变' if sub[f] else '不变 <<<'}")
b0 = sorted(st['bands'])[0]
s3 = copy.deepcopy(st); s3['bands'][b0]['macc'] += 1
sub['band.macc'] = v.state_hash(s3) != h0
print(f"  群体字段 {'macc':<18} -> 哈希{'改变' if sub['band.macc'] else '不变 <<<'}")
mark('D4 完整状态比较', all(sub.values()))

# ---------------------------------------------------------------- D5 / D6
hdr("D5 群体遍历逆序不变 / D6 资源格遍历逆序不变")
ok5 = ok6 = True
for sg, mm in GRID:
    a = all(v.state_hash(v.run(sd, Y, sigma_m=sg, move_mort_m=mm)[0]) ==
            v.state_hash(v.run(sd, Y, poison='revorder', sigma_m=sg, move_mort_m=mm)[0])
            for sd in SEEDS)
    b = all(v.state_hash(v.run(sd, Y, sigma_m=sg, move_mort_m=mm)[0]) ==
            v.state_hash(v.run(sd, Y, poison='cellrev', sigma_m=sg, move_mort_m=mm)[0])
            for sd in SEEDS)
    print(f"  SIGMA={sg:<4} MORT={mm:<4} 群体逆序 {'一致' if a else '不一致'} | 资源格逆序 {'一致' if b else '不一致'}")
    ok5 &= a; ok6 &= b
mark('D5 群体遍历顺序无关', ok5); mark('D6 资源格遍历顺序无关', ok6)

# ---------------------------------------------------------------- D7
hdr("D7 双重【逐步】退化恒等（用两份冻结基线各自的哈希函数判定）")
def stepwise(basemod, mk_base, mk_exp):
    bad = []
    for sd in SEEDS:
        bs, es = mk_base(sd), mk_exp(sd)
        first = 0 if basemod.state_hash(bs) != basemod.state_hash(es) else None
        n = 0
        while first is None and n < Y:
            basemod.step(bs); v.step(es); n += 1
            if basemod.state_hash(bs) != basemod.state_hash(es): first = n
        bad.append((sd, first, basemod.run_id(bs) != v.run_id(es)))
    return bad

r1 = stepwise(base1, lambda sd: base1.make_world(sd),
              lambda sd: v.make_world(sd, sigma_m=0, move_mort_m=0))
ok = all(f is None and d for _, f, d in r1)
print(f"  vs EXP-01 基线 (SIGMA=0, MORT=0)：{sum(1 for _,f,_ in r1 if f is None)}/7 逐步全同，"
      f"run_id 全部不同 {all(d for *_ ,d in r1)}")
for sd, f, d in r1:
    if f is not None: print(f"      seed={sd} 在 tick={f} 处首次不同")
okA = ok
okB = True
for sg in SIGMAS:
    r2 = stepwise(base2, lambda sd, g=sg: base2.make_world(sd, sigma_m=g),
                  lambda sd, g=sg: v.make_world(sd, sigma_m=g, move_mort_m=0))
    good = all(f is None and d for _, f, d in r2)
    print(f"  vs EXP-02 基线 (SIGMA={sg}, MORT=0)：{sum(1 for _,f,_ in r2 if f is None)}/7 逐步全同，"
          f"run_id 全部不同 {all(d for *_ ,d in r2)}")
    for sd, f, d in r2:
        if f is not None: print(f"      seed={sd} 在 tick={f} 处首次不同")
    okB &= good
mark('D7 双重逐步退化恒等 + 身份分开', okA and okB)

# ---------------------------------------------------------------- D8
hdr("D8a 隔离性（必过）/ D8b 干预有效性（前提，可未覆盖）")
print("  隔离性 = 抑制 A 区分裂后 B 区逐位不变。这是被测性质，必过。")
print("  干预有效性 = A 区确实被改变。若该组合下 A 区本来就没发生过分裂，")
print("               干预无效属于**前提缺失**，记未覆盖，不算隔离失败。")
viol, uncovered_cells, covered = [], [], 0
for sg, mm in GRID:
    for sd in SEEDS:
        a, _ = v.run(sd, Y, sigma_m=sg, move_mort_m=mm)
        b, _ = v.run(sd, Y, suppress='A', sigma_m=sg, move_mort_m=mm)
        if v.region_hash(a, 'B') != v.region_hash(b, 'B'):
            viol.append((sg, mm, sd))
        if v.region_hash(a, 'A') != v.region_hash(b, 'A'):
            covered += 1
        else:
            uncovered_cells.append((sg, mm, sd))
print(f"  隔离性：{len(GRID)*len(SEEDS)} 个组合中违反 {len(viol)} 个")
for c in viol: print(f"      违反：SIGMA={c[0]} MORT={c[1]} seed={c[2]}")
mark('D8a 区块隔离性', not viol)
print(f"  干预有效性：{covered}/{len(GRID)*len(SEEDS)} 个组合里 A 区确实被改变")
for c in uncovered_cells:
    print(f"      未覆盖：SIGMA={c[0]} MORT={c[1]} seed={c[2]} —— 该组合下 A 区没有分裂可抑制")
if uncovered_cells:
    uncov('D8b 干预有效性覆盖', f'{len(uncovered_cells)} 个组合的 A 区无分裂可抑制，干预无从生效')
else:
    mark('D8b 干预有效性覆盖', True)

# ---------------------------------------------------------------- D9
hdr("D9 MOVE_MORT_M 校验：先查严格整数类型（排除 bool），再查 [0,1000]")
sub = {}
for b in (50.0, 50.5, 0.0, True, False, '50', None, 1 + 0j, [50]):
    try: v.make_world(0, move_mort_m=b); got = '被接受'
    except TypeError: got = 'TypeError'
    except ValueError: got = 'ValueError'
    sub[f't{b!r}'] = (got == 'TypeError')
    print(f"  非法类型 {b!r:<8} -> {got}{'' if got=='TypeError' else '  <<<'}")
for b in (-1, 1001, -100, 10**9):
    try: v.make_world(0, move_mort_m=b); got = '被接受'
    except TypeError: got = 'TypeError'
    except ValueError: got = 'ValueError'
    sub[f'r{b}'] = (got == 'ValueError')
    print(f"  越界值 {b:<9} -> {got}{'' if got=='ValueError' else '  <<<'}")
for g in (0, 1, 999, 1000):
    st = v.make_world(0, move_mort_m=g)
    for _ in range(3): v.step(st)
    ai = (all(isinstance(x, int) for x in st['stock'].values()) and
          all(isinstance(b['macc'], int) and isinstance(b['size'], int)
              for b in st['bands'].values()) and
          isinstance(v.conservation_error(st), int))
    sub[f'g{g}'] = ai
    print(f"  合法边界 {g:<9} -> 接受，3 tick 后状态全为整数 {'✓' if ai else '✗'}")
mark('D9 MOVE_MORT_M 类型与范围校验', all(sub.values()))

# ---------------------------------------------------------------- D10
hdr("D10 poison-mort-seq 必须在明确构造的【竞争】场景里被检出")
print("  场景要求：同一 tick 内两个群体都迁移，且各自贡献 <1000、合计 ≥1000，")
print("            使全局累加器把死亡记到谁头上取决于遍历顺序。")
found = None
for mm in (50, 100, 20):
    for s1 in range(10, 40, 2):
        for s2 in range(10, 40, 2):
            r = v.make_two_movers(0, mm, sizes=(s1, s2))
            if r is None: continue
            st, i1, i2, _, _ = r
            a = copy.deepcopy(st); a['poison'] = 'mortseq'; v.step(a)
            b = copy.deepcopy(st); b['poison'] = 'mortseq,revorder'; v.step(b)
            ga = tuple(sorted((k, x['size']) for k, x in a['bands'].items()))
            gb = tuple(sorted((k, x['size']) for k, x in b['bands'].items()))
            if a['mig_total'] == 2 and ga != gb:
                found = (mm, s1, s2, st, i1, i2); break
        if found: break
    if found: break
if found is None:
    uncov('D10 poison-mort-seq 在竞争场景被检出', '搜索范围内未找到能让全局累加器产生顺序依赖的规模组合')
else:
    mm, s1, s2, st, i1, i2 = found
    h = copy.deepcopy(st); h['poison'] = ''; v.step(h)
    hr = copy.deepcopy(st); hr['poison'] = 'revorder'; v.step(hr)
    healthy_same = v.state_hash(h) == v.state_hash(hr)
    a = copy.deepcopy(st); a['poison'] = 'mortseq'; v.step(a)
    b = copy.deepcopy(st); b['poison'] = 'mortseq,revorder'; v.step(b)
    print(f"  构造：MORT={mm}，两群体初始 size=({s1}, {s2})，同 tick 均迁移")
    print(f"    健康版 正序 vs 逆序：{'逐位相同 ✓' if healthy_same else '不同 ✗'}")
    print(f"    mortseq 正序：{[(k%10**6, x['size']) for k, x in sorted(a['bands'].items())]}")
    print(f"    mortseq 逆序：{[(k%10**6, x['size']) for k, x in sorted(b['bands'].items())]}")
    mark('D10 poison-mort-seq 在竞争场景被检出',
         healthy_same and v.state_hash(a) != v.state_hash(b))

# ---------------------------------------------------------------- D11
hdr("D11 累加器口径：单元 + 端到端精确核对 + 注入必须被抓到")
print("  说明：初版的集成断言写成 `macc == 期望 or macc < 1000`，而后半句恒为真，")
print("        整条断言是空的。独立复核用『只改 step 内实际强度为 min(mm+1,1000)、")
print("        保留 move_mortality 单元测试不变』的注入证明了这一点。下面是补正。")

# (i) 单元：指定独立案例
size, macc, tot = 20, 0, 0
for _ in range(10):
    d, size, macc = v.move_mortality(size, macc, 20)
    tot += d
unit_ok = (tot, size, macc) == (3, 17, 740)
print(f"  (i) 单元案例（初始 20 人 / 余数 0 / 强度 20 / 连续 10 次）："
      f"累计死 {tot}、剩 {size}、余数 {macc} —— 期望 (3, 17, 740) {'✓' if unit_ok else '✗'}")
print(f"      对照：按 N×初始size×强度 会得到 {10*20*20//1000} 人，口径确实是按实际人数")

# (ii) 端到端：出发人数 / 原余数 / 配置强度全部确定，逐字段精确核对
CASES = [(49, 0, 20), (50, 990, 20), (100, 0, 20)]
e2e_rows, e2e_ok, uncovered_cases = [], True, []
for mm, macc0, sz in CASES:
    r = v.make_exact_move_scenario(0, mm, macc0, sz)
    if r is None:
        uncovered_cases.append((mm, macc0, sz)); continue
    st, bid, exp = r
    pop0 = st['pop_start']
    s2 = copy.deepcopy(st); v.step(s2)
    b = s2['bands'].get(bid)
    got = {
        'moved': s2['mig_total'] == 1 and b is not None and b['cell'] == exp['cell'],
        'dead': s2['mig_deaths_cum'], 'survive': b['size'] if b else 0,
        'macc': b['macc'] if b else None,
        'popid': v.population_identity_error(s2),
        'popdelta': (sum(x['size'] for x in s2['bands'].values()) - pop0),
    }
    depart_implied = got['survive'] + got['dead']
    ok = (got['moved'] and got['dead'] == exp['dead'] and got['survive'] == exp['survive']
          and got['macc'] == exp['macc'] and got['popid'] == 0
          and depart_implied == exp['depart']
          and got['popdelta'] == -exp['dead'])
    e2e_ok &= ok
    e2e_rows.append((mm, macc0, sz, exp, got, depart_implied, ok))
    print(f"  (ii) mm={mm:<4} 原余数={macc0:<4} size={sz}：")
    print(f"       出发 {depart_implied}（期望 {exp['depart']}）| 死 {got['dead']}（期望 {exp['dead']}）| "
          f"幸存 {got['survive']}（期望 {exp['survive']}）| 余数 {got['macc']}（期望 {exp['macc']}）")
    print(f"       人口账误差 {got['popid']}（期望 0）| 人口增量 {got['popdelta']}（期望 {-exp['dead']}）"
          f" {'✓' if ok else '✗'}")
for c in uncovered_cases:
    print(f"  (ii) mm={c[0]} 原余数={c[1]} size={c[2]}：**未找到满足前提的构造，记未覆盖**")

# (iii) 注入 mortstrength 必须被 (ii) 抓到
caught = []
for mm, macc0, sz, exp, *_ in e2e_rows:
    st, bid, exp2 = v.make_exact_move_scenario(0, mm, macc0, sz)
    s3 = copy.deepcopy(st); s3['poison'] = 'mortstrength'; v.step(s3)
    b3 = s3['bands'].get(bid)
    differs = (b3 is None or b3['macc'] != exp2['macc'] or b3['size'] != exp2['survive']
               or s3['mig_deaths_cum'] != exp2['dead'])
    caught.append(differs)
    print(f"  (iii) mm={mm} 注入 min(mm+1,1000)："
          f"余数 {b3['macc'] if b3 else '-'}（健康期望 {exp2['macc']}）、"
          f"幸存 {b3['size'] if b3 else '-'}（健康期望 {exp2['survive']}）"
          f" -> {'被抓到 ✓' if differs else '未被抓到 ✗'}")
print("  (iii) 注：mm=1000 时 min(mm+1,1000) 与 mm 相同，该档位注入在原理上不可检出，未纳入本组。")

if uncovered_cases and not e2e_rows:
    uncov('D11 累加器口径', '端到端场景全部未能构造')
else:
    mark('D11 累加器口径（单元 + 端到端 + 注入检出）',
         unit_ok and e2e_ok and all(caught) and not uncovered_cases)

# ---------------------------------------------------------------- D12
hdr("D12 定向场景组（每条独立记账；构造缺失记未覆盖，不得默认通过）")

# (a) 不变量：没有迁移的 tick 不得累计迁移死亡
st = v.make_world(12345, move_mort_m=100)
bad_tick, zero_mig = None, 0
pm, pd = st['mig_total'], st['mig_deaths_cum']
for t in range(Y):
    v.step(st)
    if st['mig_total'] - pm == 0:
        zero_mig += 1
        if st['mig_deaths_cum'] - pd != 0 and bad_tick is None: bad_tick = t + 1
    pm, pd = st['mig_total'], st['mig_deaths_cum']
print(f"  (a) 300 tick 中 {zero_mig} 个 tick 没有迁移；"
      f"{'这些 tick 的迁移死亡增量全为 0' if bad_tick is None else f'tick={bad_tick} 处无迁移却有迁移死亡'}")
if zero_mig == 0: uncov('D12a 无迁移不累计', '本场景没有出现无迁移的 tick')
else: mark('D12a 无迁移的 tick 不累计迁移死亡', bad_tick is None)

# (b) 小群体连续迁移：贡献必须被留存为余数。**没有实际迁移则未覆盖。**
r = v.make_two_movers(0, 20, sizes=(12, 12))
if r is None:
    uncov('D12b 小群体迁移的余数留存', '未找到构造位置')
else:
    st, i1, i2, _, _ = r
    for _ in range(12):
        v.step(st)
        if not st['bands']: break
    macc_sum = sum(b['macc'] for b in st['bands'].values())
    print(f"  (b) 12 人群体连续迁移 12 tick：迁移 {st['mig_total']} 次，"
          f"迁移死亡 {st['mig_deaths_cum']}，余数合计 {macc_sum}")
    if st['mig_total'] == 0:
        uncov('D12b 小群体迁移的余数留存', '本场景未发生实际迁移，前提不成立')
    else:
        mark('D12b 小群体迁移的贡献被留存而非丢弃',
             st['mig_deaths_cum'] > 0 or macc_sum > 0)
        print(f"      对照：若用 size×mm//1000 直接取整，12 人 × 20‰ 每次得 0 且不留余数，"
              f"迁移死亡会永远是 0")

# (c1) MORT=1000 全灭
r = v.make_two_movers(0, 1000, sizes=(20, 20), stores=(5 * v.NEED_PC, 5 * v.NEED_PC))
if r is None:
    uncov('D12c1 MORT=1000 全灭', '未找到构造位置')
else:
    st, i1, i2, _, _ = r
    n0 = len(st['bands']); v.step(st)
    gone = [k for k in (i1, i2) if k not in st['bands']]
    print(f"  (c1) MORT=1000：{len(gone)}/{n0} 个群体全灭并被移除，"
          f"守恒 {v.conservation_error(st)}，人口账 {v.population_identity_error(st)}")
    print(f"       结构性事实：能迁移必然 E<1，E<1 必然储存已被吃光，"
          f"所以死于迁移的群体储存恒为 0（out_lost 不变不是漏记）")
    if not gone: uncov('D12c1 MORT=1000 全灭', '本场景没有群体被全灭')
    else: mark('D12c1 全灭后群体被移除且两条账闭合',
               v.conservation_error(st) == 0 and v.population_identity_error(st) == 0)

# (c2) 储粮去向只记一次
st = v.make_world(0, move_mort_m=1000)
st['bands'].clear()
S = 7 * v.NEED_PC
bid = v.eid_of(0xDEAD, 0, 1)
P = sorted(i for i in v.cells() if v.passable(i))[0]
st['bands'][bid] = {'cell': P, 'size': 0, 'store': S, 'bacc': 0, 'dacc': 0, 'macc': 0,
                    'mem': {P: st['stock'][P]}, 'memt': {P: 0}}
st['start_store'] = S; st['pop_start'] = 0
v.step(st)
acc = st['out_lost'] + st['out_spoil']
print(f"  (c2) 直接构造 size=0、store={S}：群体{'已移除' if bid not in st['bands'] else '仍存在'}，"
      f"out_lost {st['out_lost']} + out_spoil {st['out_spoil']} = {acc}（应等于 {S}），"
      f"守恒 {v.conservation_error(st)}")
mark('D12c2 储粮去向只记一次',
     bid not in st['bands'] and acc == S and v.conservation_error(st) == 0
     and v.population_identity_error(st) == 0)

# (d) 分裂余数继承
r = v.make_split_scenario(0, macc0=777)
if r is None:
    uncov('D12d 分裂余数继承', '未找到构造位置')
else:
    st, bid = r
    m0 = st['bands'][bid]['macc']; v.step(st)
    tot = sum(b['macc'] for b in st['bands'].values())
    print(f"  (d) 分裂：群体数 1->{len(st['bands'])}，macc 总和 {m0}->{tot}")
    if len(st['bands']) != 2: uncov('D12d 分裂余数继承', '本场景未发生分裂')
    else: mark('D12d 分裂时累加器余数总和不变', tot == m0)

# (e) 两群体累加器独立
r = v.make_two_movers(0, 20, sizes=(20, 30))
if r is None:
    uncov('D12e 两群体独立累加器', '未找到构造位置')
else:
    st, i1, i2, _, _ = r
    both = copy.deepcopy(st); v.step(both)
    only2 = copy.deepcopy(st)
    only2['bands'][i1]['store'] = 50 * only2['bands'][i1]['size'] * v.NEED_PC
    only2['start_store'] = sum(b['store'] for b in only2['bands'].values())
    v.step(only2)
    print(f"  (e) i2 的 macc：两者都迁移时 {both['bands'][i2]['macc']}，"
          f"只有 i2 迁移时 {only2['bands'][i2]['macc']}；i1 未迁移时 macc={only2['bands'][i1]['macc']}")
    if both['mig_total'] != 2:
        uncov('D12e 两群体独立累加器', f"前提不成立：两者都迁移的分支只发生了 {both['mig_total']} 次迁移")
    else:
        mark('D12e 一个群体迁移不影响另一个的累加器',
             both['bands'][i2]['macc'] == only2['bands'][i2]['macc']
             and only2['bands'][i1]['macc'] == 0)

# ---------------------------------------------------------------- D13
hdr("D13 pop_start 必须进入校验（初始人口是运行身份的一部分）")
st, _ = v.run(0, 50, move_mort_m=50)
d0, r0, h0 = v.full_digest(st), v.run_id(st), v.state_hash(st)
s2 = copy.deepcopy(st); s2['pop_start'] += 1
print(f"  pop_start +1 -> run_id 改变={v.run_id(s2) != r0}，full_digest 改变={v.full_digest(s2) != d0}，"
      f"state_hash 改变={v.state_hash(s2) != h0}")
print(f"  同时人口账误差由 {v.population_identity_error(st)} 变为 {v.population_identity_error(s2)}"
      f" —— 改初始人口必须让身份变化，否则两次不同的运行会共享同一个 full_digest")
mark('D13 pop_start 进入运行身份', v.run_id(s2) != r0 and v.full_digest(s2) != d0)

# ---------------------------------------------------------------- 汇总
hdr("汇总")
for k in R: print(f"  {k:40s} {R[k]}")
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
