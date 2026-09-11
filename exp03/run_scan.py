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
print("第 4 节 —— 观察假说 H1 的原始读数（本轮未完成正式的趋势推断）")
print("=" * 120)
print("H1：全知臂相对记忆臂的福利优势随 MOVE_MORT_M 上升。")
print("福利用两个指标衡量，**不合成综合分**：")
print("  指标 A：缺粮强度差 = 记忆臂(缺粮/需求) − 全知臂(缺粮/需求)   正值 = 全知臂更好")
print("  指标 B：末期人口差 = 全知臂人口 − 记忆臂人口                 正值 = 全知臂更好")
print()
print("4.1 聚合读数（7 个种子合计）")
for sg in SIGMAS:
    print(f"  SIGMA_M = {sg}")
    seqA, seqB = [], []
    for mm in MORTS:
        m, o = agg[(sg, mm, 'memory')], agg[(sg, mm, 'omniscient')]
        dA = m['deficit']/m['need'] - o['deficit']/o['need']
        dB = o['pop'] - m['pop']
        seqA.append(dA); seqB.append(dB)
        print(f"    MORT={mm:<4} 指标A={dA*100:+.3f}pp   指标B={dB:+d}")
    print(f"    指标A 单调不减：{all(b >= a for a, b in zip(seqA, seqA[1:]))}"
          f"    指标B 单调不减：{all(b >= a for a, b in zip(seqB, seqB[1:]))}")
    print()

print("4.2 逐种子读数（同档位、跨臂的配对差）")
for sg in SIGMAS:
    print(f"  SIGMA_M = {sg}")
    for mm in MORTS:
        per = []
        for sd in SEEDS:
            m = next(x for x in rows if x['sigma']==sg and x['mort']==mm and x['seed']==sd and x['arm']=='memory')
            o = next(x for x in rows if x['sigma']==sg and x['mort']==mm and x['seed']==sd and x['arm']=='omniscient')
            per.append((sd, m['deficit']/m['need'] - o['deficit']/o['need'], o['pop'] - m['pop']))
        print(f"    MORT={mm:<4} 指标A: " + " ".join(f"{sd}:{a*100:+.3f}" for sd, a, _ in per))
        print(f"    {'':>10} 指标B: " + " ".join(f"{sd}:{b:+d}" for sd, _, b in per))
    print()

print("4.3 同种子跨档位的配对变化（记忆臂自身随 MOVE_MORT_M 的变化）")
print("    这是机制的直接效应，按种子配对，不跨种子平均。")
for sg in SIGMAS:
    print(f"  SIGMA_M = {sg}")
    print(f"    {'seed':>6}  " + "  ".join(f"MORT={mm:<4}" for mm in MORTS))
    for key, label, fmt in (('defint', '缺粮强度', lambda x: f"{x*100:.3f}%"),
                            ('pop', '末人口', lambda x: f"{int(x)}"),
                            ('mig', '迁移', lambda x: f"{int(x)}")):
        print(f"    {label}：")
        for sd in SEEDS:
            vals = []
            for mm in MORTS:
                x = next(r for r in rows if r['sigma']==sg and r['mort']==mm and r['seed']==sd and r['arm']=='memory')
                vals.append(x['deficit']/x['need'] if key=='defint' else x[key])
            print(f"    {sd:>6}  " + "  ".join(f"{fmt(v):>10}" for v in vals))
    print()

# 4.3b 端点比较与逐档单调性：由数据直接计算，不做任何推断，也不设自动判据
def _series(sg, sd, key):
    out = []
    for mm in MORTS:
        x = next(r for r in rows if r['sigma']==sg and r['mort']==mm and r['seed']==sd and r['arm']=='memory')
        out.append(x['deficit']/x['need'] if key == 'defint' else x[key])
    return out

_tot, _ep = 0, 0
_mono = {'pop': 0, 'mig': 0, 'defint': 0}
_nonmono = []
for sg in SIGMAS:
    for sd in SEEDS:
        _tot += 1
        ser = {k: _series(sg, sd, k) for k in ('pop', 'mig', 'defint')}
        if all(v[0] > v[-1] for v in ser.values()):
            _ep += 1
        for k, v in ser.items():
            if all(a >= b for a, b in zip(v, v[1:])):
                _mono[k] += 1
            else:
                _nonmono.append((sg, sd, k, v))

print("4.3b 端点比较与逐档单调性（直接计数，不是统计检验）")
print(f"    MORT=0 -> MORT=100 端点上迁移/末人口/缺粮强度三项同时下降：{_ep}/{_tot} 个（种子×SIGMA）组合")
print(f"    逐档单调不增：末人口 {_mono['pop']}/{_tot}   迁移 {_mono['mig']}/{_tot}   缺粮强度 {_mono['defint']}/{_tot}")
print("    逐档非单调的组合（端点仍下降，中间档位有反弹）：")
_lab = {'pop': '末人口', 'mig': '迁移', 'defint': '缺粮强度'}
for sg, sd, k, v in _nonmono:
    vs = "  ".join((f"{x*100:.3f}%" if k == 'defint' else f"{int(x)}") for x in v)
    print(f"      SIGMA={sg:<4} seed={sd:<6} {_lab[k]}: {vs}")
print()

print("4.4 本轮能说与不能说的")
print("""    能说（原始描述）：
      - SIGMA_M=0 档，两个聚合指标随 MOVE_MORT_M 都呈单调不减。
      - SIGMA_M=400 档，两个聚合指标都没有同样的趋势。
      - 逐种子读数在两档都有差异，同一档位内不同种子的符号并不一致。
      - 记忆臂自身随 MOVE_MORT_M 的端点变化（MORT=0 -> 100）：见 4.3b 的计数。
        端点上三项同时下降的组合数与逐档单调不增的组合数不一样 —— 端点下降不等于
        逐档单调，中间档位确有反弹，明细已逐条列出，不做平滑也不做推断。
        缺粮强度的下降是人口下降的伴生结果，不是福利改善。

    不能说：
      - **本轮未完成正式的趋势推断。** 没有预注册的检验统计量、没有空对照、
        没有噪声地板，因此不宣布 H1 成立或不成立。
      - 不事后挑选统计方法来追求结论。上一版用"聚合差 / 逐种子半极差 < 1"
        自动判定 H1 未支持、并宣称样本没有分辨力 —— 那个判据是事后挑的，
        已删除。
      - H1 的成立与否都不能推出"决策有没有后果"，也不构成禁止以后研究
        社会机制的依据。
      - 不为追求趋势调参，不新增大规模扫描。""")

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
