#!/usr/bin/env python3
"""EXP-02 观察扫描。**这里的指标全部是观察项，不判定通过与否。**

正确性判定在 run_tests.py。本脚本只报告现象，包括不支持假说的结果。
用法：cd exp02 && python3 run_scan.py
"""
import verify2 as v

SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]
SIGMAS = [0, 100, 200, 400, 800]
Y = 300
NEED = v.NEED_PC

def obs(seed, sigma, poison=""):
    st, _ = v.run(seed, Y, poison=poison, sigma_m=sigma)
    pop = sum(b['size'] for b in st['bands'].values())
    return dict(
        seed=seed, sigma=sigma, arm=poison or 'memory',
        mig=st['mig_total'], regret=st['mig_regret'],
        deficit=st['deficit_cum'] // NEED,          # 折成"人年口粮"
        pop=pop, bands=len(st['bands']),
        nominal=st['clim_nominal'] // NEED, planned=st['clim_planned'] // NEED,
        credited=st['clim_credited'] // NEED, capped=st['clim_capped'] // NEED,
    )

def rate(num, den):
    return "不可计算(分母0)" if den == 0 else f"{num*100/den:.2f}%"

print("=" * 108)
print("EXP-02 观察扫描 —— 逐种子原始结果（每个 (seed, SIGMA) 配对比较 memory 与 omniscient）")
print("=" * 108)
print("单位：deficit / nominal / planned / credited / capped 均折成人年口粮（1 人年 = 730,000 kcal）")
print()
hdr = (f"{'seed':>6} {'SIGMA':>6} {'arm':>10} {'迁移':>5} {'误判':>4} {'误判率':>14} "
       f"{'累计缺粮':>9} {'人口':>5} {'群体':>4} {'名义':>8} {'计划':>8} {'入账':>8} {'被容量挡':>9}")
print(hdr); print("-" * len(hdr))
rows = []
for sg in SIGMAS:
    for sd in SEEDS:
        for arm in ("", "omniscient"):
            r = obs(sd, sg, arm); rows.append(r)
            print(f"{r['seed']:>6} {r['sigma']:>6} {r['arm']:>10} {r['mig']:>5} {r['regret']:>4} "
                  f"{rate(r['regret'], r['mig']):>14} {r['deficit']:>9} {r['pop']:>5} {r['bands']:>4} "
                  f"{r['nominal']:>8} {r['planned']:>8} {r['credited']:>8} {r['capped']:>9}")
    print("-" * len(hdr))

print()
print("=" * 108)
print("汇总：按 SIGMA 合计 7 个种子")
print("=" * 108)
h2 = (f"{'SIGMA':>6} {'arm':>10} {'迁移合计':>9} {'误判合计':>9} {'误判率':>14} "
      f"{'缺粮合计':>9} {'人口合计':>9} {'群体合计':>9} {'计划/名义':>10} {'入账/计划':>10}")
print(h2); print("-" * len(h2))
summary = {}
for sg in SIGMAS:
    for arm in ("memory", "omniscient"):
        g = [r for r in rows if r['sigma'] == sg and r['arm'] == arm]
        mig = sum(r['mig'] for r in g); reg = sum(r['regret'] for r in g)
        nom = sum(r['nominal'] for r in g); pla = sum(r['planned'] for r in g)
        cre = sum(r['credited'] for r in g)
        summary[(sg, arm)] = (mig, reg)
        print(f"{sg:>6} {arm:>10} {mig:>9} {reg:>9} {rate(reg, mig):>14} "
              f"{sum(r['deficit'] for r in g):>9} {sum(r['pop'] for r in g):>9} "
              f"{sum(r['bands'] for r in g):>9} {pla/nom:>10.4f} {cre/pla:>10.4f}")
    print("-" * len(h2))

print()
print("=" * 108)
print("待检验假说 B1：误判率随 SIGMA_M 单调上升")
print("=" * 108)
seq = []
for sg in SIGMAS:
    mig, reg = summary[(sg, 'memory')]
    seq.append((sg, reg, mig, None if mig == 0 else reg / mig))
for sg, reg, mig, r in seq:
    print(f"  SIGMA_M={sg:<4} 误判 {reg:>3} / 迁移 {mig:<5} = {'不可计算' if r is None else f'{r*100:.2f}%'}")
vals = [r for _, _, _, r in seq if r is not None]
mono = len(vals) == len(seq) and all(b >= a for a, b in zip(vals, vals[1:]))
strict = len(vals) == len(seq) and all(b > a for a, b in zip(vals, vals[1:]))
print()
if strict:   print("  结论：本配置与本样本下，误判率随 SIGMA_M 严格单调上升。")
elif mono:   print("  结论：本配置与本样本下，误判率随 SIGMA_M 单调不减（非严格）。")
else:        print("  结论：**本配置与本样本未支持 B1。** 误判率并非随 SIGMA_M 单调上升。")
print("  B1 只是待检验假说，不是正确性断言。不成立时不调参去追曲线，也不就此宣布找到了另一个原因。")

print()
print("=" * 108)
print("读数须知（这几条不看会读错上面的表）")
print("=" * 108)
print("""  1. 全知对照臂的误判恒为 0 有一部分来自选择规则本身：误判的定义是"搬去的格子事后看
     并不更好"，而全知臂直接读当年真值，按定义几乎不可能选错。**不要把这个 0 当成长期
     福利收益。** 两臂的福利要看缺粮、人口、群体数，不能看误判。
  2. "被容量挡"通常是"计划"的大头：格子很快涨到 cap，此后多数再生量根本没进入世界。
     因此资源总量的变化**不能**全部解释成信息效应——先看 计划/名义 与 入账/计划 两列。
  3. 迁移为 0 时误判率标为"不可计算(分母0)"，不记成 0%。
  4. SIGMA_M=0 一行是退化档，应与 EXP-01 冻结基线一致（由 run_tests.py 的 C7 判定）。""")
