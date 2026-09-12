#!/usr/bin/env python3
"""EXP-06 观察扫描：援助记忆与优先回助。

只报告现象，不判定通过与否。**42 次配对运行**：
  7 种子 × SIGMA_M{0,400} × MOVE_MORT_M=50 × SHARE_M=1000 × AID_M=1000 × RECIP_M{0,500,1000}
  每次 300 年，记忆臂。
用法：cd exp06 && python3 run_scan.py
"""
import verify6 as v

SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]
SIGMAS = [0, 400]
MORT, SHARE, AID = 50, 1000, 1000
RECIPS = [0, 500, 1000]
Y = 300
N = v.NEED_PC

rows = []
for sg in SIGMAS:
    for rc in RECIPS:
        for sd in SEEDS:
            st, _ = v.run(sd, Y, sigma_m=sg, move_mort_m=MORT, share_m=SHARE,
                          aid_m=AID, recip_m=rc)
            rows.append(dict(
                seed=sd, sigma=sg, recip=rc,
                aid_events=st['aid_events'], aid_transfers=st['aid_transfers'],
                aid_kcal=st['aid_kcal'],
                recip_kcal=st['recip_kcal'], recip_transfers=st['recip_transfers'],
                recip_changed=st['recip_changed'],
                repay_kcal=st['repay_kcal'], repay_transfers=st['repay_transfers'],
                mutual=v.mutual_pair_count(st), dangling=v.amem_dangling(st),
                amem_entries=sum(len(b['amem']) for b in st['bands'].values()),
                dropped=st['amem_entries_dropped'],
                mig=st['mig_total'], migdead=st['mig_deaths_cum'],
                births=st['births_cum'], demodead=st['deaths_demo_cum'],
                pop=sum(b['size'] for b in st['bands'].values()),
                bands=len(st['bands']), need=st['need_cum'],
                deficit=st['deficit_cum'], py=st['personyear_cum']))

COLS = ['seed', 'sigma', 'recip', 'aid_events', 'aid_transfers', 'aid_kcal',
        'recip_kcal', 'recip_transfers', 'recip_changed', 'repay_kcal',
        'repay_transfers', 'mutual', 'dangling', 'amem_entries', 'dropped',
        'mig', 'migdead', 'births', 'demodead', 'pop', 'bands', 'need', 'deficit', 'py']

print("=" * 120)
print(f"第 1 节 —— 逐种子原始整数账（未折算；共 {len(rows)} 行）")
print("=" * 120)
print("\t".join(COLS))
for r in rows:
    print("\t".join(str(r[c]) for c in COLS))

print()
print("=" * 120)
print("第 2 节 —— 援助 / 回助 / 关系（7 种子合计，300 年）")
print("=" * 120)
print("  回助 = 供给方**记得对方帮过自己**的那些转移；RECIP_M=0 时它仍可能发生，那是**碰巧**。")
print("  分配改变 = 同一份援助前状态下把 RECIP_M 换成 0 再算一遍、结果不同的'格×年'次数，")
print("             这才是'优先规则真的改变了分配'的直接计数。")
print(f"  {'SIGMA':>6} {'RECIP':>6} | {'援助活动':>8} {'援助笔数':>8} {'援助总量':>12} "
      f"{'优先笔数':>8} {'优先总量':>12} {'回助笔数':>8} {'回助总量':>12} {'分配改变':>8} {'重复往来':>8}")
print("  " + "-" * 118)
for sg in SIGMAS:
    for rc in RECIPS:
        sel = [r for r in rows if r['sigma'] == sg and r['recip'] == rc]
        f = lambda k: sum(r[k] for r in sel)
        print(f"  {sg:>6} {rc:>6} | {f('aid_events'):>8} {f('aid_transfers'):>8} "
              f"{f('aid_kcal') / N:>11.1f}人年 {f('recip_transfers'):>8} "
              f"{f('recip_kcal') / N:>11.1f}人年 {f('repay_transfers'):>8} "
              f"{f('repay_kcal') / N:>11.1f}人年 {f('recip_changed'):>8} {f('mutual'):>8}")

print()
print("=" * 120)
print("第 3 节 —— 记忆状态（7 种子合计，末年）")
print("=" * 120)
print(f"  {'SIGMA':>6} {'RECIP':>6} | {'在世记忆条目':>12} {'指向已消失群体':>14} {'随消失丢失':>12}")
print("  " + "-" * 60)
for sg in SIGMAS:
    for rc in RECIPS:
        sel = [r for r in rows if r['sigma'] == sg and r['recip'] == rc]
        print(f"  {sg:>6} {rc:>6} | {sum(r['amem_entries'] for r in sel):>12} "
              f"{sum(r['dangling'] for r in sel):>14} {sum(r['dropped'] for r in sel):>12}")

print()
print("=" * 120)
print("第 4 节 —— 结果读数（7 种子合计）")
print("=" * 120)
print(f"  {'SIGMA':>6} {'RECIP':>6} | {'缺粮/需求':>10} {'出生':>7} {'原死亡':>8} {'迁移死亡':>8} "
      f"{'迁移':>6} {'末人口':>7} {'群体':>5} {'累计人年':>10}")
print("  " + "-" * 100)
for sg in SIGMAS:
    for rc in RECIPS:
        sel = [r for r in rows if r['sigma'] == sg and r['recip'] == rc]
        need = sum(r['need'] for r in sel); dfc = sum(r['deficit'] for r in sel)
        print(f"  {sg:>6} {rc:>6} | {dfc / need * 100:>9.3f}% "
              f"{sum(r['births'] for r in sel):>7} {sum(r['demodead'] for r in sel):>8} "
              f"{sum(r['migdead'] for r in sel):>8} {sum(r['mig'] for r in sel):>6} "
              f"{sum(r['pop'] for r in sel):>7} {sum(r['bands'] for r in sel):>5} "
              f"{sum(r['py'] for r in sel):>10}")

print()
print("=" * 120)
print("第 5 节 —— 同种子配对比较（RECIP_M=0 作基线，不跨种子平均）")
print("=" * 120)
for sg in SIGMAS:
    print(f"  SIGMA_M = {sg}")
    print(f"      {'seed':>6} | {'缺粮强度 0/500/1000':>34} | {'末人口 0/500/1000':>24} | "
          f"{'分配改变 0/500/1000':>22}")
    for sd in SEEDS:
        a, b, c = [], [], []
        for rc in RECIPS:
            r = next(x for x in rows if x['seed'] == sd and x['sigma'] == sg and x['recip'] == rc)
            a.append(f"{r['deficit'] / r['need'] * 100:.3f}%")
            b.append(str(r['pop'])); c.append(str(r['recip_changed']))
        print(f"      {sd:>6} | {' / '.join(a):>34} | {' / '.join(b):>24} | {' / '.join(c):>22}")

print()
print("=" * 120)
print("第 6 节 —— 读数须知")
print("=" * 120)
print("""  1. **不把"优先回助一定带来改善"设成结论。** 本节只给原始读数；没触发或没有明显改善
     就如实保留，不调参、不强造关系或联盟。
  2. **回助 ≠ 优先规则起作用**。RECIP_M=0 时回助笔数照样不为零（供给方碰巧就是旧伙伴），
     所以判断"规则是否真的改变了分配"只能看**分配改变**这一列。
  3. 记忆是**本轮的模型假设**：只由实际转移累加、子群体不继承、群体消失时自己的记忆丢失
     （已记账）而别人对它的记忆保留。这些不是现实历史定律。
  4. 援助本身在自然运行里就稀少（见 EXP-05），优先回助是在这个稀少事件上再加一层条件，
     所以样本量很小，**不做趋势推断**。
  5. 继承 EXP-01～05 的全部已知限制。""")
