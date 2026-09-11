#!/usr/bin/env python3
"""EXP-03 观察扫描（112 次运行）。**全部是观察项，不判定通过与否。**

研究的问题：在迁移策略固定时，新增迁移死亡代价如何改变不同信息条件下的
人口、缺粮与迁移结果。该代价适用于所有迁移，不是只惩罚误判。

正确性判定在 run_tests.py。用法：cd exp03 && python3 run_scan.py
"""
import verify3 as v

SEEDS  = [0, 12345, 777, 4242, 99, 31337, 2026]
SIGMAS = [0, 400]
MORTS  = [0, 20, 50, 100]
Y = 300
N = v.NEED_PC

def one(seed, sigma, mort, arm):
    st, _ = v.run(seed, Y, poison=arm, sigma_m=sigma, move_mort_m=mort)
    return dict(
        seed=seed, sigma=sigma, mort=mort, arm=arm or 'memory',
        mig=st['mig_total'], regret=st['mig_regret'],
        migdead=st['mig_deaths_cum'],
        births=st['births_cum'], demodead=st['deaths_demo_cum'],
        pop=sum(b['size'] for b in st['bands'].values()),
        bands=len(st['bands']),
        need=st['need_cum'], deficit=st['deficit_cum'], py=st['personyear_cum'],
        nominal=st['clim_nominal'], planned=st['clim_planned'],
        credited=st['clim_credited'], capped=st['clim_capped'],
    )

def rate(num, den, pct=True, nd=2):
    if den == 0: return "不可计算(分母0)"
    return f"{num*100/den:.{nd}f}%" if pct else f"{num/den:.4f}"

rows = [one(sd, sg, mm, arm)
        for sg in SIGMAS for mm in MORTS for sd in SEEDS for arm in ("", "omniscient")]

print("=" * 120)
print("第 1 节 —— 逐种子原始整数账（未折算，单位 kcal / 人 / 人年；共 %d 行）" % len(rows))
print("=" * 120)
cols = ['seed','sigma','mort','arm','mig','regret','migdead','births','demodead',
        'pop','bands','need','deficit','py','nominal','planned','credited','capped']
print("\t".join(cols))
for r in rows:
    print("\t".join(str(r[c]) for c in cols))

print()
print("=" * 120)
print("第 2 节 —— 逐种子配对可读表（缺粮与需求折成人年口粮；1 人年 = 730,000 kcal）")
print("=" * 120)
h = (f"{'seed':>6} {'SIG':>4} {'MORT':>5} {'arm':>10} {'迁移':>5} {'误判':>4} {'误判率':>14} "
     f"{'迁移死亡':>8} {'原死亡':>7} {'出生':>6} {'末人口':>6} {'群体':>4} "
     f"{'累计需求':>9} {'累计缺粮':>9} {'缺粮/需求':>10} {'累计人年':>9}")
print(h); print("-" * len(h))
for sg in SIGMAS:
    for mm in MORTS:
        for r in [x for x in rows if x['sigma'] == sg and x['mort'] == mm]:
            print(f"{r['seed']:>6} {r['sigma']:>4} {r['mort']:>5} {r['arm']:>10} "
                  f"{r['mig']:>5} {r['regret']:>4} {rate(r['regret'], r['mig']):>14} "
                  f"{r['migdead']:>8} {r['demodead']:>7} {r['births']:>6} "
                  f"{r['pop']:>6} {r['bands']:>4} "
                  f"{r['need']//N:>9} {r['deficit']//N:>9} "
                  f"{rate(r['deficit'], r['need']):>10} {r['py']:>9}")
        print("-" * len(h))

print()
print("=" * 120)
print("第 3 节 —— 汇总（按 SIGMA × MORT × arm 合计 7 个种子）")
print("=" * 120)
h2 = (f"{'SIG':>4} {'MORT':>5} {'arm':>10} {'迁移':>6} {'误判':>5} {'误判率':>14} "
      f"{'迁移死亡':>8} {'原死亡':>7} {'末人口':>7} {'群体':>5} "
      f"{'缺粮/需求':>10} {'人年':>9} {'入账/计划':>10}")
print(h2); print("-" * len(h2))
agg = {}
for sg in SIGMAS:
    for mm in MORTS:
        for arm in ("memory", "omniscient"):
            g = [x for x in rows if x['sigma'] == sg and x['mort'] == mm and x['arm'] == arm]
            a = {k: sum(x[k] for x in g) for k in
                 ('mig','regret','migdead','demodead','births','pop','bands',
                  'need','deficit','py','planned','credited')}
            agg[(sg, mm, arm)] = a
            print(f"{sg:>4} {mm:>5} {arm:>10} {a['mig']:>6} {a['regret']:>5} "
                  f"{rate(a['regret'], a['mig']):>14} {a['migdead']:>8} {a['demodead']:>7} "
                  f"{a['pop']:>7} {a['bands']:>5} {rate(a['deficit'], a['need']):>10} "
                  f"{a['py']:>9} {rate(a['credited'], a['planned'], pct=False):>10}")
        print("-" * len(h2))

print()
print("=" * 120)
print("第 4 节 —— 待检验假说 H1：全知臂相对记忆臂的福利优势随 MOVE_MORT_M 上升")
print("=" * 120)
print("福利用两个指标衡量，**不合成综合分**：")
print("  指标 A：缺粮强度差 = 记忆臂(缺粮/需求) − 全知臂(缺粮/需求)   正值 = 全知臂更好")
print("  指标 B：末期人口差 = 全知臂人口 − 记忆臂人口                 正值 = 全知臂更好")
print()
for sg in SIGMAS:
    print(f"  SIGMA_M = {sg}")
    seqA, seqB = [], []
    for mm in MORTS:
        m, o = agg[(sg, mm, 'memory')], agg[(sg, mm, 'omniscient')]
        dA = m['deficit']/m['need'] - o['deficit']/o['need']
        dB = o['pop'] - m['pop']
        seqA.append(dA); seqB.append(dB)
        print(f"    MORT={mm:<4} 指标A(缺粮强度差)={dA*100:+.3f}pp   指标B(人口差)={dB:+d}")
    monoA = all(b >= a for a, b in zip(seqA, seqA[1:]))
    monoB = all(b >= a for a, b in zip(seqB, seqB[1:]))
    print(f"    指标A 单调不减：{monoA}    指标B 单调不减：{monoB}")
    if monoA != monoB:
        print("    **两个指标方向不一致 —— 不合成综合赢家，如实并列。**")
    # 逐种子配对差的离散度：聚合差若小于种子间离散度，单调性不可当结论
    print("    逐种子配对差（用于判断聚合差是否大于种子间离散度）：")
    for mm in MORTS:
        per = []
        for sd in SEEDS:
            m = next(x for x in rows if x['sigma']==sg and x['mort']==mm and x['seed']==sd and x['arm']=='memory')
            o = next(x for x in rows if x['sigma']==sg and x['mort']==mm and x['seed']==sd and x['arm']=='omniscient')
            per.append((m['deficit']/m['need'] - o['deficit']/o['need'], o['pop'] - m['pop']))
        a_vals = sorted(x[0] for x in per); b_vals = sorted(x[1] for x in per)
        a_pos = sum(1 for x in a_vals if x > 0); b_pos = sum(1 for x in b_vals if x > 0)
        print(f"      MORT={mm:<4} 指标A 逐种子 {a_vals[0]*100:+.3f}pp … {a_vals[-1]*100:+.3f}pp "
              f"(正号 {a_pos}/7) | 指标B 逐种子 {b_vals[0]:+d} … {b_vals[-1]:+d} (正号 {b_pos}/7)")
    print()
# ---- 从数据算出的判读，不让读者自己推 ----
print("  ---- 判读 ----")
verdict_lines = []
for sg in SIGMAS:
    agg_abs, spread_half, signs = [], [], []
    for mm in MORTS:
        m, o = agg[(sg, mm, 'memory')], agg[(sg, mm, 'omniscient')]
        agg_abs.append(abs(m['deficit']/m['need'] - o['deficit']/o['need']))
        per = []
        for sd in SEEDS:
            mm_ = next(x for x in rows if x['sigma']==sg and x['mort']==mm and x['seed']==sd and x['arm']=='memory')
            oo_ = next(x for x in rows if x['sigma']==sg and x['mort']==mm and x['seed']==sd and x['arm']=='omniscient')
            per.append(mm_['deficit']/mm_['need'] - oo_['deficit']/oo_['need'])
        spread_half.append((max(per) - min(per)) / 2)
        signs.append(sum(1 for x in per if x > 0))
    ratio = max(a / s if s else float('inf') for a, s in zip(agg_abs, spread_half))
    print(f"  SIGMA_M={sg}：聚合差的最大绝对值 / 对应档位逐种子半幅 = {ratio:.2f}"
          f"（<1 表示聚合差小于种子间离散）；各档正号数 {signs}/7")
    verdict_lines.append(ratio < 1)
if all(verdict_lines):
    print("  => **本配置与本样本未支持 H1。** 两个 SIGMA 档位下，聚合差都小于种子间离散半幅，")
    print("     且逐种子符号接近对半，即使 SIGMA_M=0 档的聚合值呈单调，也不能读成支持。")
    print("     注意：这是『未支持』，不是『已证伪』——本样本没有分辨力，不是给出了反向结论。")
else:
    print("  => 至少一个档位的聚合差大于种子间离散半幅，需要单独核对。")
print()
print("  H1 只是待检验假说，不是正确性断言。不成立时报告『本配置与本样本未支持』，")
print("  不调参追曲线。**H1 不成立不能推出决策无效，也不构成禁止以后研究社会机制的依据。**")
print()
print("  **本轮没有计算噪声地板**（例如同配置下只换种子集合会有多大波动）。因此即使某一档")
print("  出现了单调性，只要聚合差没有明显大于上面那些逐种子离散区间，就不能当成结论——")
print("  只能记为『在本样本上呈现该方向』。要把它变成结论需要更多种子与一个空对照，")
print("  那不属于本切片。")

print()
print("=" * 120)
print("第 5 节 —— 读数须知")
print("=" * 120)
print("""  1. **迁移死亡代价适用于所有迁移，不是只惩罚误判。** 因此它同时改变了迁移的收益结构
     与人口规模，不能把它读成"对错误决策的罚款"。
  2. **不要把"死得更多所以缺粮总量下降"读成福利改善。** 这就是为什么主指标用
     缺粮/需求（强度）而不是缺粮总量，并同时报告累计人年——人少了，总需求和总缺粮
     都会跟着少。
  3. 全知对照臂的误判恒为 0 有一部分来自选择规则的定义（它读当年真值，按定义选不错），
     **不把它当福利收益**。福利只看缺粮强度与人口。
  4. "被容量挡"仍占计划再生量的大头（沿用 EXP-02 的口径），资源总量的变化不能
     全部归给决策效应。
  5. 迁移为 0 时误判率记"不可计算(分母0)"，不记 0%。
  6. MORT=0 档是退化档，应与 EXP-02 一致（由 run_tests.py 的 D7 判定，不由本表判定）。
  7. **本实验不检验"决策是否有后果"这一总体命题**，只检验"新增迁移死亡代价如何改变
     不同信息条件下的人口、缺粮与迁移结果"。前者的证据要求远高于本切片。""")
