#!/usr/bin/env python3
"""EXP-05 观察扫描：同格食物援助。

只报告现象，不判定通过与否。**42 次运行**（小规模配对扫描，不扩大研究）：
  7 种子 × SIGMA_M{0,400} × MOVE_MORT_M=50 × SHARE_M=1000 × AID_M{0,250,1000}
  每次 300 年，记忆臂。
用法：cd exp05 && python3 run_scan.py
"""
import verify5 as v

SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]
SIGMAS = [0, 400]
MORT = 50
SHARE = 1000
AIDS = [0, 250, 1000]
Y = 300
N = v.NEED_PC

rows = []
for sg in SIGMAS:
    for am in AIDS:
        for sd in SEEDS:
            st, _ = v.run(sd, Y, sigma_m=sg, move_mort_m=MORT, share_m=SHARE, aid_m=am)
            rows.append(dict(
                seed=sd, sigma=sg, mort=MORT, share=SHARE, aid=am,
                aid_events=st['aid_events'], aid_transfers=st['aid_transfers'],
                aid_kcal=st['aid_kcal'], aid_donors=st['aid_donors'],
                aid_receivers=st['aid_receivers'], aid_supply=st['aid_supply'],
                aid_demand=st['aid_demand'],
                mig=st['mig_total'], migdead=st['mig_deaths_cum'],
                births=st['births_cum'], demodead=st['deaths_demo_cum'],
                pop=sum(b['size'] for b in st['bands'].values()),
                bands=len(st['bands']), need=st['need_cum'], deficit=st['deficit_cum'],
                py=st['personyear_cum']))

COLS = ['seed', 'sigma', 'mort', 'share', 'aid', 'aid_events', 'aid_transfers',
        'aid_kcal', 'aid_donors', 'aid_receivers', 'aid_supply', 'aid_demand',
        'mig', 'migdead', 'births', 'demodead', 'pop', 'bands', 'need', 'deficit', 'py']

print("=" * 120)
print(f"第 1 节 —— 逐种子原始整数账（未折算；共 {len(rows)} 行）")
print("=" * 120)
print("\t".join(COLS))
for r in rows:
    print("\t".join(str(r[c]) for c in COLS))

print()
print("=" * 120)
print("第 2 节 —— 援助本身发生了多少（7 种子合计，300 年）")
print("=" * 120)
print("  注意：**一次多人援助活动**与**一笔转移**不是同一个计数。")
print(f"  {'SIGMA':>6} {'AID_M':>6} | {'援助活动':>8} {'逐笔转移':>8} {'供给方人次':>10} {'接收方人次':>10} "
      f"{'援助总量(人年口粮)':>18} {'当年预算合计':>14} {'当年缺口合计':>14} {'覆盖率':>8}")
print("  " + "-" * 118)
for sg in SIGMAS:
    for am in AIDS:
        sel = [r for r in rows if r['sigma'] == sg and r['aid'] == am]
        ev = sum(r['aid_events'] for r in sel); tr = sum(r['aid_transfers'] for r in sel)
        dn = sum(r['aid_donors'] for r in sel); rc = sum(r['aid_receivers'] for r in sel)
        kc = sum(r['aid_kcal'] for r in sel)
        sp = sum(r['aid_supply'] for r in sel); dm = sum(r['aid_demand'] for r in sel)
        cov = f"{kc / dm * 100:.1f}%" if dm else "不适用"
        print(f"  {sg:>6} {am:>6} | {ev:>8} {tr:>8} {dn:>10} {rc:>10} "
              f"{kc / N:>18.1f} {sp / N:>14.1f} {dm / N:>14.1f} {cov:>8}")

print()
print("=" * 120)
print("第 3 节 —— 结果读数（7 种子合计）")
print("=" * 120)
print(f"  {'SIGMA':>6} {'AID_M':>6} | {'缺粮/需求':>10} {'累计缺粮(人年)':>14} {'出生':>7} {'原死亡':>8} "
      f"{'迁移死亡':>8} {'迁移':>6} {'末人口':>7} {'群体':>5} {'累计人年':>10}")
print("  " + "-" * 118)
for sg in SIGMAS:
    for am in AIDS:
        sel = [r for r in rows if r['sigma'] == sg and r['aid'] == am]
        need = sum(r['need'] for r in sel); dfc = sum(r['deficit'] for r in sel)
        print(f"  {sg:>6} {am:>6} | {dfc / need * 100:>9.3f}% {dfc / N:>14.1f} "
              f"{sum(r['births'] for r in sel):>7} {sum(r['demodead'] for r in sel):>8} "
              f"{sum(r['migdead'] for r in sel):>8} {sum(r['mig'] for r in sel):>6} "
              f"{sum(r['pop'] for r in sel):>7} {sum(r['bands'] for r in sel):>5} "
              f"{sum(r['py'] for r in sel):>10}")

print()
print("=" * 120)
print("第 4 节 —— 同种子配对比较（AID_M=0 作基线，不跨种子平均）")
print("=" * 120)
for sg in SIGMAS:
    print(f"  SIGMA_M = {sg}")
    print(f"      {'seed':>6} | {'缺粮强度 0/250/1000':>34} | {'末人口 0/250/1000':>26} | "
          f"{'累计人年 0/250/1000':>32}")
    for sd in SEEDS:
        cells = []
        pops = []
        pys = []
        for am in AIDS:
            r = next(x for x in rows if x['seed'] == sd and x['sigma'] == sg and x['aid'] == am)
            cells.append(f"{r['deficit'] / r['need'] * 100:.3f}%")
            pops.append(str(r['pop']))
            pys.append(str(r['py']))
        print(f"      {sd:>6} | {' / '.join(cells):>34} | {' / '.join(pops):>26} | "
              f"{' / '.join(pys):>32}")

print()
print("=" * 120)
print("第 5 节 —— 读数须知")
print("=" * 120)
print("""  1. **不把"援助一定增加长期人口"设成结论。** 这一节只给原始读数，方向不符合预想也照样保留，
     不调参、不制造灾荒去强行触发援助。
  2. 援助在自然运行里**很稀少**：同格既有余粮者又有缺粮者，本身只在个位数百分比的 tick 上出现
     （见 probes/EXP-05-FEASIBILITY.txt）。所以援助总量相对全局需求是很小的一个数，
     读数差异里有多少来自援助、有多少来自它触发的连锁（谁活下来、谁去了哪一格），本轮**没有分离**。
  3. 覆盖率 = 援助总量 / 当年缺口合计，只统计**发生过援助的格**里的缺口，不是全局缺粮率。
  4. 一次多人援助活动（aid_events）与一笔转移（aid_transfers）是两个计数，不要混用。
  5. 继承 EXP-01~04 的全部已知限制：迁移储存损失结构性恒为零、默认样本无灭绝、
     多数假设为 D 级、跨版本存档兼容与人口学标定都没有做过。""")
