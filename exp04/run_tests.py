#!/usr/bin/env python3
"""EXP-04 正确性测试（同格信息交换）。

三态结果：PASS / FAIL / UNCOVERED。**未覆盖项不计入"通过"**；有 FAIL 则退出码非零。
用法：cd exp04 && python3 run_tests.py ; echo $?

三条纪律照旧：
  * 退化恒等用**基线自己的**哈希函数判定，基线按路径只读加载，不改基线；
  * 长跑覆盖不到的路径必须有定向场景，前提缺失记未覆盖；
  * 每个二值检验配一个错误注入，并实测它真的会红。
"""
import sys, copy, importlib.util, pathlib
import verify4 as v

_HERE = pathlib.Path(__file__).resolve().parent
def _load(name, rel):
    sp = importlib.util.spec_from_file_location(name, _HERE.parent / rel)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
base1 = _load('exp01_frozen', 'exp01/verify.py')      # 冻结基线，只读
base2 = _load('exp02_frozen', 'exp02/verify2.py')     # 冻结基线，只读
base3 = _load('exp03_frozen', 'exp03/verify3.py')     # 冻结基线，只读

SEEDS  = [0, 12345, 777, 4242, 99, 31337, 2026]
SIGMAS = [0, 400]
MORTS  = [0, 50]
SHARES = [0, 250, 1000]
Y = 300
R = {}

def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)
def mark(k, ok): R[k] = 'PASS' if ok else 'FAIL'; print(f"  => {k} {'通过' if ok else '失败'}")
def uncov(k, why): R[k] = 'UNCOVERED'; print(f"  => {k} 未覆盖：{why}")

# ---------------------------------------------------------------- E1
hdr("E1 守恒 / 人口恒等 / 信息账恒等（每 tick，全部组合 × 7 种子）")
w_c = w_p = w_s = 0
for sg in SIGMAS:
    for mm in MORTS:
        for sh in SHARES:
            for sd in SEEDS:
                st = v.make_world(sd, sigma_m=sg, move_mort_m=mm, share_m=sh)
                for _ in range(60):
                    v.step(st)
                    w_c = max(w_c, abs(v.conservation_error(st)))
                    w_p = max(w_p, abs(v.population_identity_error(st)))
                    w_s = max(w_s, abs(v.share_ledger_error(st)))
print(f"  能量守恒最大绝对误差 {w_c}；人口恒等 {w_p}；信息账（收到 = 采纳 + 拒绝）{w_s}")
mark('E1 三本账每 tick 恒为 0', w_c == 0 and w_p == 0 and w_s == 0)

# ---------------------------------------------------------------- E2
hdr("E2 同种子逐位一致 + 内存快照续跑一致")
ok = True
for sd in SEEDS[:3]:
    a, _ = v.run(sd, 120, sigma_m=400, move_mort_m=50, share_m=1000)
    b, snap = v.run(sd, 120, sigma_m=400, move_mort_m=50, share_m=1000, snap_at=60)
    c = v.resume(snap, 60)
    ok &= v.full_digest(a) == v.full_digest(b) == v.full_digest(c)
print(f"  3 个种子：重跑与快照续跑的 full_digest 全同 = {ok}")
mark('E2 确定性与快照续跑', ok)

# ---------------------------------------------------------------- E3
hdr("E3 三条【逐步】退化恒等（各用基线自己的哈希函数判定）")
def stepwise(basemod, mk_base, mk_exp, years=120):
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

res = []
r3 = stepwise(base3, lambda sd: base3.make_world(sd, sigma_m=400, move_mort_m=50),
              lambda sd: v.make_world(sd, sigma_m=400, move_mort_m=50, share_m=0))
print(f"  vs EXP-03 基线 (SIGMA=400, MORT=50, SHARE=0)：{sum(1 for _,f,_ in r3 if f is None)}/7 逐步全同，"
      f"run_id 全部不同 {all(d for *_, d in r3)}")
res.append(all(f is None and d for _, f, d in r3))
r2 = stepwise(base2, lambda sd: base2.make_world(sd, sigma_m=400),
              lambda sd: v.make_world(sd, sigma_m=400, move_mort_m=0, share_m=0))
print(f"  vs EXP-02 基线 (SIGMA=400, MORT=0, SHARE=0)：{sum(1 for _,f,_ in r2 if f is None)}/7 逐步全同")
res.append(all(f is None for _, f, _ in r2))
r1 = stepwise(base1, lambda sd: base1.make_world(sd),
              lambda sd: v.make_world(sd, sigma_m=0, move_mort_m=0, share_m=0))
print(f"  vs EXP-01 基线 (全部为 0)：{sum(1 for _,f,_ in r1 if f is None)}/7 逐步全同")
res.append(all(f is None for _, f, _ in r1))
for sd, f, _ in r3 + r2 + r1:
    if f is not None: print(f"      seed={sd} 在 tick={f} 处首次不同")
mark('E3 三条逐步退化恒等 + 身份分开', all(res))

# ---------------------------------------------------------------- E4
hdr("E4 全知对照臂：行动与物质演化不变（记忆与信息账变化是预期，不是错误）")
same_material, mem_changed, share_active = True, False, False
for sd in SEEDS[:4]:
    a = v.make_world(sd, 'omniscient', 400, 50, 0)
    b = v.make_world(sd, 'omniscient', 400, 50, 1000)
    for _ in range(120):
        v.step(a); v.step(b)
        if v.material_hash(a) != v.material_hash(b):
            same_material = False; break
    if v.state_hash(a) != v.state_hash(b): mem_changed = True
    if b['share_adopted'] > 0: share_active = True
print(f"  material_hash 逐 tick 相同 = {same_material}")
print(f"  机制确实在该臂内生效（有采纳）= {share_active}；state_hash 随记忆改变 = {mem_changed}")
print("  说明：全知臂的迁移决策读当年真值，不读记忆，所以行动与物质演化必须一样；")
print("        它的记忆内容、信息账与诊断计数会变，那是预期之内，**不作为模拟错误**。")
if share_active:
    mark('E4 全知臂物质演化不变而记忆确实变了', same_material and mem_changed)
else:
    uncov('E4 全知臂物质演化不变', '该样本里全知臂没有发生过一次交换，前提缺失')

# ---------------------------------------------------------------- E5
hdr("E5 遍历顺序无关（正序 / 逆序逐位相同）")
ok = True
for sd in SEEDS[:3]:
    a, _ = v.run(sd, 120, poison='order', sigma_m=400, move_mort_m=50, share_m=1000)
    b, _ = v.run(sd, 120, poison='revorder', sigma_m=400, move_mort_m=50, share_m=1000)
    ok &= v.state_hash(a) == v.state_hash(b)
print(f"  3 个种子：正序与逆序的 state_hash 全同 = {ok}")
mark('E5 遍历顺序无关', ok)

# ---------------------------------------------------------------- E6
hdr("E6 定向场景：端到端精确核对合并规则（并检出 shareseq）")
def expected_exchange(st_after):
    """按写死的规则，从引擎记录的**交换前快照**独立算一遍期望结果。
    规则：同格参与者互为候选；每个格键取 memt 最大者，并列取 band_id 最小者；
          只有严格比自己新才采纳；时戳照抄来源。"""
    pre_mem, pre_cells = st_after['pre_mem'], st_after['pre_cells']
    parts = sorted(set(b for (_, _, _, b, _, _, _) in st_after['share_log']) |
                   set(b for (_, _, b, _, _, _, _) in st_after['share_log']))
    if not parts: return None
    cell = pre_cells[parts[0]]
    exp_log, exp_mem = [], {}
    for x in parts:
        mem, memt = dict(pre_mem[x][0]), dict(pre_mem[x][1])
        pool = {}
        for y in parts:
            if y == x: continue
            my, mt = pre_mem[y]
            for j in sorted(my):
                tj = mt.get(j, 0)
                cur = pool.get(j)
                if cur is None or tj > cur[0] or (tj == cur[0] and y < cur[2]):
                    pool[j] = (tj, my[j], y)
        for j in sorted(pool):
            tj, val, donor = pool[j]
            own = memt.get(j)
            if own is not None and tj <= own: continue
            mem[j] = val; memt[j] = tj
            exp_log.append((st_after['tick'] - 1, cell, donor, x, j, val, tj))
        exp_mem[x] = (mem, memt)
    return exp_log, exp_mem

st, P, ids, nb = v.make_share_scenario()
v.step(st)
exp = expected_exchange(st)
if exp is None:
    uncov('E6 端到端精确核对', '构造场景里没有发生交换，前提缺失')
else:
    exp_log, exp_mem = exp
    log_ok = sorted(st['share_log']) == sorted(exp_log)
    mem_ok = all(st['bands'][x]['mem'] == m and st['bands'][x]['memt'] == t
                 for x, (m, t) in exp_mem.items() if x in st['bands'])
    print(f"  参与者 {len(ids)}，实际记录 {len(st['share_log'])} 条，独立重算 {len(exp_log)} 条")
    print(f"  逐条相同 = {log_ok}；交换后的 mem/memt 与独立重算一致 = {mem_ok}")
    # 注入：顺序链式合并（读本相位刚更新的中间结果）
    bad, _, _, _ = v.make_share_scenario()
    bad['poison'] = 'shareseq'
    v.step(bad)
    bad_exp = expected_exchange(bad)
    caught = bad_exp is not None and sorted(bad['share_log']) != sorted(bad_exp[0])
    diff = [r for r in bad['share_log'] if r not in (bad_exp[0] if bad_exp else [])]
    print(f"  poison-shareseq 被检出 = {caught}；差异样例 {diff[:2]}")
    mark('E6 端到端精确核对 + shareseq 检出', log_ok and mem_ok and caught)

# ---------------------------------------------------------------- E7
hdr("E7 溯源：每条采纳都能在交换前快照里找到同源（并检出 sharefab / sharefresh）")
def provenance_bad(st):
    """返回违反溯源的记录数：来源在交换前必须**就持有**这条记忆，值与时戳都要对得上。"""
    bad = 0
    for (_, _, donor, _, j, val, stamp) in st['share_log']:
        mem, memt = st['pre_mem'].get(donor, ({}, {}))
        if mem.get(j) != val or memt.get(j) != stamp:
            bad += 1
    return bad

# 长跑：每个 tick 结束后立刻检查当年新增的记录
def scan_provenance(poison='', ticks=120, seed=4242):
    st = v.make_world(seed, poison, 400, 50, 1000)
    seen, bad = 0, 0
    for _ in range(ticks):
        n0 = len(st['share_log'])
        v.step(st)
        new = st['share_log'][n0:]
        seen += len(new)
        for (_, _, donor, _, j, val, stamp) in new:
            mem, memt = st['pre_mem'].get(donor, ({}, {}))
            if mem.get(j) != val or memt.get(j) != stamp: bad += 1
    return seen, bad

seen, bad = scan_provenance()
sf_seen, sf_bad = scan_provenance('sharefab')
fr_seen, fr_bad = scan_provenance('sharefresh')
print(f"  健康版：{seen} 条采纳，溯源违规 {bad}")
print(f"  poison-sharefab ：{sf_seen} 条，溯源违规 {sf_bad}（应 > 0）")
print(f"  poison-sharefresh：{fr_seen} 条，时戳被刷新导致违规 {fr_bad}（应 > 0）")
if seen == 0:
    uncov('E7 溯源', '样本里没有发生过采纳，前提缺失')
else:
    mark('E7 溯源 + sharefab / sharefresh 检出', bad == 0 and sf_bad > 0 and fr_bad > 0)

# ---------------------------------------------------------------- E8
hdr("E8 空间边界：来源与接收者在交换时必须同格（并检出 sharecross）")
def scan_space(poison='', ticks=120, seed=4242):
    st = v.make_world(seed, poison, 400, 50, 1000)
    seen, bad = 0, 0
    for _ in range(ticks):
        n0 = len(st['share_log'])
        v.step(st)
        for (_, c, donor, recv, *_rest) in st['share_log'][n0:]:
            seen += 1
            if st['pre_cells'].get(donor) != c or st['pre_cells'].get(recv) != c: bad += 1
    return seen, bad
s_ok, b_ok = scan_space()
s_x, b_x = scan_space('sharecross')
print(f"  健康版：{s_ok} 条，跨格违规 {b_ok}")
print(f"  poison-sharecross：{s_x} 条，跨格违规 {b_x}（应 > 0）")
if s_ok == 0:
    uncov('E8 空间边界', '样本里没有发生过采纳，前提缺失')
else:
    mark('E8 不跨格 + sharecross 检出', b_ok == 0 and b_x > 0)

# ---------------------------------------------------------------- E9
hdr("E9 相位内物质不变：交换不搬运任何物质（并检出 shareleak）")
def material_moved(poison='', ticks=120, seed=4242):
    """比较同一次运行里，只有 shareleak 注入差别时的物质演化。
    注意：**全局守恒查不出群体之间的储存转移**（总量不变），所以必须比物质哈希。"""
    a = v.make_world(seed, '', 400, 50, 1000)
    b = v.make_world(seed, poison, 400, 50, 1000)
    diff_tick, cons = None, 0
    for k in range(ticks):
        v.step(a); v.step(b)
        cons = max(cons, abs(v.conservation_error(b)))
        if diff_tick is None and v.material_hash(a) != v.material_hash(b):
            diff_tick = k + 1
    return diff_tick, cons
d_leak, cons_leak = material_moved('shareleak')
print(f"  poison-shareleak：物质哈希在第 {d_leak} tick 首次不同（应有值）；"
      f"它的全局守恒误差始终是 {cons_leak} —— 守恒账确实抓不到它")
mark('E9 shareleak 被相位内物质不变抓到，而守恒账抓不到', d_leak is not None and cons_leak == 0)

# ---------------------------------------------------------------- E10
hdr("E10 SHARE_M 参数校验（严格整数 -> 范围 -> 边界值可用）")
bad_types, bad_range = [], []
for x in (1.0, 0.5, True, '100', None):
    try: v.make_world(0, share_m=x); bad_types.append(x)
    except TypeError: pass
    except Exception as e: bad_types.append((x, type(e).__name__))
for x in (-1, 1001, 10**9):
    try: v.make_world(0, share_m=x); bad_range.append(x)
    except ValueError: pass
edge_ok = True
for x in (0, 1, 999, 1000):
    st = v.make_world(0, share_m=x)
    for _ in range(3): v.step(st)
    edge_ok &= all(isinstance(y, int) for y in st['stock'].values())
print(f"  非整数被 TypeError 拒绝：{not bad_types}（漏网 {bad_types}）")
print(f"  越界被 ValueError 拒绝：{not bad_range}（漏网 {bad_range}）")
print(f"  边界值 {{0,1,999,1000}} 可用且状态全整数：{edge_ok}")
mark('E10 SHARE_M 类型与范围校验', not bad_types and not bad_range and edge_ok)

# ---------------------------------------------------------------- E11
hdr("E11 SHARE_M 进入运行身份（改了参与概率就是另一次运行）")
r0 = v.run_id(v.make_world(0, sigma_m=400, move_mort_m=50, share_m=0))
r1 = v.run_id(v.make_world(0, sigma_m=400, move_mort_m=50, share_m=250))
r2 = v.run_id(v.make_world(0, sigma_m=400, move_mort_m=50, share_m=1000))
print(f"  SHARE_M=0/250/1000 的 run_id 互不相同 = {len({r0, r1, r2}) == 3}")
mark('E11 SHARE_M 进入运行身份', len({r0, r1, r2}) == 3)

# ---------------------------------------------------------------- E12
hdr("E12 诊断计数只读（并检出 sharediag）")
# 长跑里诊断计数一直是 0（见 E13），所以这个注入挂在长跑上会空转 ——
# 正是 EXP-01「分裂冲突 175 次撞车 0 次」的同一课：必须挂在能让它承重的定向场景上。
a = v.make_world(4242, '', 400, 50, 1000)
b = v.make_world(4242, 'sharediag', 400, 50, 1000)
long_diff = None
for k in range(120):
    v.step(a); v.step(b)
    if long_diff is None and v.material_hash(a) != v.material_hash(b): long_diff = k + 1
print(f"  长跑：物质哈希首次不同于第 {long_diff} tick —— 诊断计数在长跑里始终是 "
      f"{a['share_decision_changed']}，注入条件从不成立，属于空转")

sc = v.make_share_decision_scenario(0)
if sc is None:
    uncov('E12 诊断计数回灌会被抓到', '构造不出让诊断计数变动的场景，前提缺失')
else:
    h_st = sc[0]
    b_st, *_ = v.make_share_decision_scenario(0)
    b_st['poison'] = 'sharediag'
    v.step(h_st); v.step(b_st)
    caught = v.material_hash(h_st) != v.material_hash(b_st)
    print(f"  定向场景：健康版诊断计数 {h_st['share_decision_changed']}，"
          f"注入版 {b_st['share_decision_changed']}；物质哈希不同 = {caught}")
    print(f"    健康版 X 的去向 {[bb['cell'] for bb in h_st['bands'].values()]}，"
          f"注入版 {[bb['cell'] for bb in b_st['bands'].values()]}")
    mark('E12 诊断计数回灌会被抓到（定向场景）', caught)

# ---------------------------------------------------------------- E13
hdr("E13 交换能不能真的改变迁移目标（长跑 + 定向场景）")
# 用与扫描相同的年数（300 年）：120 年的样本里这个计数是 0，300 年就不是了 ——
# 这正是"长跑覆盖不到的路径"那条纪律：年数本身就是前提的一部分。
long_changed, long120 = 0, 0
for sd in SEEDS:
    st = v.make_world(sd, '', 400, 50, 1000)
    for k in range(300):
        v.step(st)
        if k == 119: long120 += st['share_decision_changed']
    long_changed += st['share_decision_changed']
print(f"  长跑（7 种子 × 300 年，SHARE=1000）里诊断计数合计 = {long_changed}"
      f"（同样的配置只跑 120 年时是 {long120}）")
sc = v.make_share_decision_scenario(0)
if sc is None:
    uncov('E13 交换改变迁移目标', '构造不出前提（找不到合适的格与 tick）')
else:
    st, X, Y, good, plain = sc
    v.step(st)
    st0, *_ = v.make_share_decision_scenario(0)
    st0['share_m'] = 0
    v.step(st0)
    print(f"  定向场景：开交换的诊断计数 = {st['share_decision_changed']}，"
          f"关交换 = {st0['share_decision_changed']}")
    mark('E13 定向场景里交换确实改变了迁移目标',
         st['share_decision_changed'] >= 1 and st0['share_decision_changed'] == 0)
if long_changed == 0:
    R['E13b 长跑里出现过决策改变'] = 'UNCOVERED'
    print("  => E13b 长跑里出现过决策改变 未覆盖：本样本里一次都没发生（如实记，不算通过）")
else:
    mark('E13b 长跑里出现过决策改变', True)

# ---------------------------------------------------------------- E14
hdr("E14 未登记的注入标志必须报错")
try:
    v.make_world(0, 'sharemagic'); ok = False
except ValueError: ok = True
print(f"  未登记标志被拒绝 = {ok}")
mark('E14 注入标志是封闭集合', ok)

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
