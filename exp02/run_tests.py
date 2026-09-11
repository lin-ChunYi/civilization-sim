#!/usr/bin/env python3
"""EXP-02 正确性测试。必过项失败 => 退出码非零。

用法：cd exp02 && python3 run_tests.py ; echo $?
"""
import sys, copy, importlib.util, pathlib
import verify2 as v

# 冻结基线：按路径加载 exp01/verify.py，只读，不修改
_BP = pathlib.Path(__file__).resolve().parent.parent / 'exp01' / 'verify.py'
_spec = importlib.util.spec_from_file_location('exp01_frozen', _BP)
base = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(base)

SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]
SIGMAS = [0, 100, 200, 400, 800]
Y = 300
MUST = {}

def hdr(t): print("\n" + "=" * 76 + f"\n{t}\n" + "=" * 76)
def mark(k, ok):
    MUST[k] = ok; print(f"  => {k} {'通过' if ok else '失败'}")

# ---------------------------------------------------------------- C1
hdr("C1 守恒：每 tick 整数收支闭合（全部 SIGMA 档）")
ok = True
for sg in SIGMAS:
    worst = 0
    for sd in SEEDS:
        st = v.make_world(sd, sigma_m=sg)
        for _ in range(Y):
            v.step(st); worst = max(worst, abs(v.conservation_error(st)))
    print(f"  SIGMA_M={sg:<4} 7 个种子最大绝对误差 {worst}")
    ok &= (worst == 0)
mark('C1 守恒', ok)

# ---------------------------------------------------------------- C2
hdr("C2 同种子同档位两次运行逐位相同")
ok = True
for sg in SIGMAS:
    same = all(v.state_hash(v.run(sd, Y, sigma_m=sg)[0]) ==
               v.state_hash(v.run(sd, Y, sigma_m=sg)[0]) for sd in SEEDS)
    print(f"  SIGMA_M={sg:<4} {'7/7 一致' if same else '存在不一致'}")
    ok &= same
mark('C2 重放确定性', ok)

# ---------------------------------------------------------------- C3
hdr("C3 第 150 年快照续跑至 300 年，与不中断运行逐位相同")
ok = True
for sg in SIGMAS:
    good = 0
    for sd in SEEDS:
        full, snap = v.run(sd, Y, snap_at=150, sigma_m=sg)
        good += (v.state_hash(full) == v.state_hash(v.resume(snap, Y - 150)))
    print(f"  SIGMA_M={sg:<4} {good}/7 一致")
    ok &= (good == len(SEEDS))
mark('C3 快照续跑', ok)

# ---------------------------------------------------------------- C4
hdr("C4 完整状态比较：新增的资源账字段确实进了 state_hash")
st, _ = v.run(12345, 50, sigma_m=400)
h0 = v.state_hash(st)
sub = {}
for f in ('clim_nominal', 'clim_planned', 'clim_credited', 'clim_capped',
          'deficit_cum', 'sigma_m'):
    s2 = copy.deepcopy(st); s2[f] += 1
    sub[f] = v.state_hash(s2) != h0
    print(f"  改 {f:<15} -> 哈希{'改变' if sub[f] else '不变 <<< 该字段没进哈希'}")
mark('C4 完整状态比较', all(sub.values()))

# ---------------------------------------------------------------- C5 / C6
hdr("C5 群体遍历逆序不变 / C6 资源格遍历逆序不变")
ok5 = ok6 = True
for sg in SIGMAS:
    a5 = all(v.state_hash(v.run(sd, Y, sigma_m=sg)[0]) ==
             v.state_hash(v.run(sd, Y, poison='revorder', sigma_m=sg)[0]) for sd in SEEDS)
    a6 = all(v.state_hash(v.run(sd, Y, sigma_m=sg)[0]) ==
             v.state_hash(v.run(sd, Y, poison='cellrev', sigma_m=sg)[0]) for sd in SEEDS)
    print(f"  SIGMA_M={sg:<4} 群体逆序 {'一致' if a5 else '不一致'} | 资源格逆序 {'一致' if a6 else '不一致'}")
    ok5 &= a5; ok6 &= a6
mark('C5 群体遍历顺序无关', ok5)
mark('C6 资源格遍历顺序无关', ok6)

# ---------------------------------------------------------------- C7
hdr("C7 退化恒等：SIGMA_M=0 必须逐位复现冻结基线（用基线自己的哈希函数判定）")
ok = True; ids_differ = True
for sd in SEEDS:
    bst, _ = base.run(sd, Y)
    est, _ = v.run(sd, Y, sigma_m=0)
    same_state = base.state_hash(bst) == base.state_hash(est)
    diff_id = base.run_id(bst) != v.run_id(est)
    print(f"  seed={sd:<6} 基线口径状态 {'逐位相同' if same_state else '不同'} | "
          f"run_id {'不同（正确）' if diff_id else '相同 <<< 身份没区分开'}")
    ok &= same_state; ids_differ &= diff_id
mark('C7 SIGMA_M=0 退化恒等 + 身份分开记录', ok and ids_differ)

# ---------------------------------------------------------------- C8
hdr("C8 区块隔离（保留；不强求它发现未被触发的错误）")
ok = True
for sg in SIGMAS:
    good = 0
    for sd in SEEDS:
        b0, _ = v.run(sd, Y, sigma_m=sg)
        b1, _ = v.run(sd, Y, suppress='A', sigma_m=sg)
        good += (v.region_hash(b0, 'B') == v.region_hash(b1, 'B') and
                 v.region_hash(b0, 'A') != v.region_hash(b1, 'A'))
    print(f"  SIGMA_M={sg:<4} {good}/7（B 区不变 且 A 区确实改变）")
    ok &= (good == len(SEEDS))
mark('C8 区块隔离', ok)

# ---------------------------------------------------------------- C9
hdr("C9 信息边界（定向场景，含正对照）")
print("  前提：一个饿着的群体，记忆里只有自己格与一个已知邻格；")
print("        本 tick 的侦察目标由 RNG 预先算出，且初始很穷。")
print("        前提由构造保证：P1 确实会考虑迁移 / P2 基准决策落在已知格 /")
print("        P3 侦察目标被填满后能压过已知格 / P4 留有未观察邻格。找不到满足前提的位置即报缺。")
sub = {}
for sd in SEEDS:
    r = v.make_info_scenario(sd)
    if r is None:
        print(f"  seed={sd}: 找不到满足前提的位置 —— 记为前提不成立，不计入通过也不计入失败")
        continue
    st, bid, scout, known, unobs = r
    b = v.decide_once(st, bid)
    s2 = copy.deepcopy(st)
    for j in unobs: s2['stock'][j] = s2['cap'][j]
    d2 = v.decide_once(s2, bid)
    s3 = copy.deepcopy(st); s3['stock'][scout] = s3['cap'][scout]
    d3 = v.decide_once(s3, bid)
    unchanged = (d2 == b); flipped = (d3 != b); on_known = (b == known)
    sub[sd] = unchanged and flipped and on_known
    print(f"  seed={sd:<6} 基准->{b}{'(=已知格)' if on_known else '(≠已知格✗)'}"
          f" | 只改未观察{unobs}->{d2} {'不变✓' if unchanged else '变了✗'}"
          f" | 改侦察目标{scout}->{d3} {'翻转✓' if flipped else '未翻转✗(正对照失效)'}")
mark('C9 未获新信息前决策不变（且正对照有效）', bool(sub) and all(sub.values()))

# ---------------------------------------------------------------- C10
hdr("C10 (tick,cell)→扰动 的寻址：健康版与遍历顺序无关，climseq 必须错配")
def trace(sd, sg, poison, ticks=3):
    st = v.make_world(sd, poison, sg); st['trace_clim'] = {}
    for _ in range(ticks): v.step(st)
    return dict(st['trace_clim'])
sub = {}
for sd in SEEDS[:3]:
    hf, hr = trace(sd, 400, ''), trace(sd, 400, 'cellrev')
    pf, pr = trace(sd, 400, 'climseq'), trace(sd, 400, 'climseq,cellrev')
    healthy_ok = (hf == hr and len(hf) > 0)
    nmis = sum(1 for k in pf if pf[k] != pr.get(k))
    sub[sd] = healthy_ok and nmis > 0
    print(f"  seed={sd:<6} 健康版 正序vs逆序 {'同一映射✓' if healthy_ok else '映射不同✗'}"
          f" | climseq 错配 {nmis}/{len(pf)} 个 (tick,cell) {'✓' if nmis>0 else '✗'}")
mark('C10 波动按坐标寻址（climseq 触发错配）', all(sub.values()))

# ---------------------------------------------------------------- 汇总
hdr("汇总（只列必过项；现象类指标在 run_scan.py，不在这里判定通过与否）")
for k in MUST: print(f"  {k:36s} {'通过' if MUST[k] else '失败'}")
failed = [k for k, o in MUST.items() if not o]
print(f"\n必过项 {len(MUST)-len(failed)}/{len(MUST)} 通过")
if failed:
    print("失败：" + ", ".join(failed)); sys.exit(1)
print("全部必过项通过"); sys.exit(0)
