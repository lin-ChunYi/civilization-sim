#!/usr/bin/env python3
"""EXP-04 观察扫描：同格信息交换。

只报告现象，不判定通过与否。112 次运行：
  记忆臂  7 种子 × SIGMA{0,400} × MORT{0,50} × SHARE{0,250,1000} = 84
  全知臂  7 种子 × SIGMA{0,400} × MORT{0,50}（只跑 SHARE=0，因为 E4 已证明
          该臂的行动与物质演化对 SHARE_M 不变）                       = 28
用法：cd exp04 && python3 run_scan.py
"""
import verify4 as v

SEEDS  = [0, 12345, 777, 4242, 99, 31337, 2026]
SIGMAS = [0, 400]
MORTS  = [0, 50]
SHARES = [0, 250, 1000]
Y = 300
NEED = v.NEED_PC

rows = []
for sg in SIGMAS:
    for mm in MORTS:
        for sh in SHARES:
            for sd in SEEDS:
                st, _ = v.run(sd, Y, sigma_m=sg, move_mort_m=mm, share_m=sh)
                rows.append(dict(
                    seed=sd, sigma=sg, mort=mm, share=sh, arm='memory',
                    mig=st['mig_total'], regret=st['mig_regret'],
                    migdead=st['mig_deaths_cum'], births=st['births_cum'],
                    demodead=st['deaths_demo_cum'],
                    pop=sum(b['size'] for b in st['bands'].values()),
                    bands=len(st['bands']), need=st['need_cum'],
                    deficit=st['deficit_cum'], py=st['personyear_cum'],
                    stale=st['stale_sum'],
                    sgroups=st['share_groups'], sparts=st['share_participants'],
                    srecv=st['share_received'], sadopt=st['share_adopted'],
                    srej=st['share_rejected'], sdec=st['share_decision_changed']))
        for sd in SEEDS:
            st, _ = v.run(sd, Y, poison='omniscient', sigma_m=sg, move_mort_m=mm, share_m=0)
            rows.append(dict(
                seed=sd, sigma=sg, mort=mm, share=0, arm='omniscient',
                mig=st['mig_total'], regret=st['mig_regret'],
                migdead=st['mig_deaths_cum'], births=st['births_cum'],
                demodead=st['deaths_demo_cum'],
                pop=sum(b['size'] for b in st['bands'].values()),
                bands=len(st['bands']), need=st['need_cum'],
                deficit=st['deficit_cum'], py=st['personyear_cum'],
                stale=st['stale_sum'],
                sgroups=st['share_groups'], sparts=st['share_participants'],
                srecv=st['share_received'], sadopt=st['share_adopted'],
                srej=st['share_rejected'], sdec=st['share_decision_changed']))

COLS = ['seed', 'sigma', 'mort', 'share', 'arm', 'mig', 'regret', 'migdead', 'births',
        'demodead', 'pop', 'bands', 'need', 'deficit', 'py', 'stale',
        'sgroups', 'sparts', 'srecv', 'sadopt', 'srej', 'sdec']

print("=" * 120)
print(f"第 1 节 —— 逐种子原始整数账（未折算；共 {len(rows)} 行）")
print("=" * 120)
print("\t".join(COLS))
for r in rows:
    print("\t".join(str(r[c]) for c in COLS))

print()
print("=" * 120)
print("第 2 节 —— 记忆臂：信息交换本身发生了多少（7 种子合计）")
print("=" * 120)
print(f"  {'SIG':>4} {'MORT':>5} {'SHARE':>6} | {'交换组次':>9} {'参与人次':>9} {'收到条目':>9} "
      f"{'采纳':>7} {'拒绝':>8} {'采纳率':>8} {'决策改变':>9}")
print("  " + "-" * 96)
for sg in SIGMAS:
    for mm in MORTS:
        for sh in SHARES:
            sel = [r for r in rows if r['arm'] == 'memory' and r['sigma'] == sg
                   and r['mort'] == mm and r['share'] == sh]
            g = sum(r['sgroups'] for r in sel); p = sum(r['sparts'] for r in sel)
            rc = sum(r['srecv'] for r in sel); ad = sum(r['sadopt'] for r in sel)
            rj = sum(r['srej'] for r in sel); dc = sum(r['sdec'] for r in sel)
            rate = f"{ad / rc * 100:.1f}%" if rc else "不适用"
            print(f"  {sg:>4} {mm:>5} {sh:>6} | {g:>9} {p:>9} {rc:>9} {ad:>7} {rj:>8} "
                  f"{rate:>8} {dc:>9}")

print()
print("=" * 120)
print("第 3 节 —— 结果读数（缺粮强度 = 累计缺粮 / 累计需求；陈旧度 = stale_sum / 迁移次数）")
print("=" * 120)
print(f"  {'SIG':>4} {'MORT':>5} {'臂/SHARE':>12} | {'迁移':>6} {'误判率':>8} {'迁移死亡':>8} "
      f"{'末人口':>7} {'群体':>5} {'缺粮/需求':>10} {'平均陈旧度':>11} {'累计人年':>9}")
print("  " + "-" * 110)


def agg(sel):
    o = {k: sum(r[k] for r in sel) for k in
         ('mig', 'regret', 'migdead', 'pop', 'bands', 'need', 'deficit', 'py', 'stale')}
    return o


for sg in SIGMAS:
    for mm in MORTS:
        for sh in SHARES:
            a = agg([r for r in rows if r['arm'] == 'memory' and r['sigma'] == sg
                     and r['mort'] == mm and r['share'] == sh])
            reg = f"{a['regret'] / a['mig'] * 100:.2f}%" if a['mig'] else "不适用"
            stale = f"{a['stale'] / a['mig']:.2f}" if a['mig'] else "不适用"
            print(f"  {sg:>4} {mm:>5} {('记忆 ' + str(sh)):>12} | {a['mig']:>6} {reg:>8} "
                  f"{a['migdead']:>8} {a['pop']:>7} {a['bands']:>5} "
                  f"{a['deficit'] / a['need'] * 100:>9.3f}% {stale:>11} {a['py']:>9}")
        a = agg([r for r in rows if r['arm'] == 'omniscient' and r['sigma'] == sg
                 and r['mort'] == mm])
        stale = f"{a['stale'] / a['mig']:.2f}" if a['mig'] else "不适用"
        print(f"  {sg:>4} {mm:>5} {'全知(上界)':>12} | {a['mig']:>6} {'0.00%':>8} "
              f"{a['migdead']:>8} {a['pop']:>7} {a['bands']:>5} "
              f"{a['deficit'] / a['need'] * 100:>9.3f}% {stale:>11} {a['py']:>9}")

print()
print("=" * 120)
print("第 4 节 —— 三个预注册观察假说的原始读数（不做趋势推断）")
print("=" * 120)
print("  G1：记忆臂的缺粮强度随 SHARE_M 上升向全知臂靠拢")
print("  G2：记忆臂的平均信息陈旧度随 SHARE_M 上升而下降")
print("  G3：决策改变数 > 0（机制真的改变了决策，而不是只改了不被读取的记忆）")
print()
for sg in SIGMAS:
    for mm in MORTS:
        omni = agg([r for r in rows if r['arm'] == 'omniscient' and r['sigma'] == sg
                    and r['mort'] == mm])
        o_int = omni['deficit'] / omni['need']
        line_a, line_b, line_c = [], [], []
        for sh in SHARES:
            a = agg([r for r in rows if r['arm'] == 'memory' and r['sigma'] == sg
                     and r['mort'] == mm and r['share'] == sh])
            gap = (a['deficit'] / a['need'] - o_int) * 100
            line_a.append(f"SHARE={sh}:{gap:+.3f}pp")
            line_b.append(f"SHARE={sh}:" + (f"{a['stale'] / a['mig']:.2f}" if a['mig'] else "不适用"))
            line_c.append(f"SHARE={sh}:{sum(r['sdec'] for r in rows if r['arm']=='memory' and r['sigma']==sg and r['mort']==mm and r['share']==sh)}")
        print(f"  SIGMA={sg:<4} MORT={mm:<4}")
        print(f"    G1 与全知臂的缺粮强度差（越接近 0 越靠拢）： " + "  ".join(line_a))
        print(f"    G2 平均信息陈旧度：                        " + "  ".join(line_b))
        print(f"    G3 决策改变数：                            " + "  ".join(line_c))

print()
print("  逐种子的 G1 差值（同 seed 配对，不跨种子平均）：")
for sg in SIGMAS:
    for mm in MORTS:
        print(f"    SIGMA={sg} MORT={mm}")
        for sh in SHARES:
            parts = []
            for sd in SEEDS:
                m = next(r for r in rows if r['arm'] == 'memory' and r['seed'] == sd
                         and r['sigma'] == sg and r['mort'] == mm and r['share'] == sh)
                o = next(r for r in rows if r['arm'] == 'omniscient' and r['seed'] == sd
                         and r['sigma'] == sg and r['mort'] == mm)
                parts.append(f"{sd}:{(m['deficit']/m['need'] - o['deficit']/o['need'])*100:+.3f}")
            print(f"      SHARE={sh:<5} " + " ".join(parts))

print()
print("=" * 120)
print("第 5 节 —— 读数须知")
print("=" * 120)
print("""  1. **本轮不做正式的趋势推断。** 没有预注册的检验统计量、没有空对照、没有噪声地板，
     只保留原始读数。结果不符合预想也照样留着，不调参追趋势。
  2. EXP-03 已经测到：全知臂与记忆臂这两个端点之间的差本身在本样本上就不稳定。
     所以“G1 读不到分辨”既不能推出“信息没有用”，也不能反过来当成机制有效的证据。
  3. **决策改变数是机制是否真的影响了行动的直接计数。** 它为 0 说明：信息确实传了
     （采纳数 > 0），但在本配置下没有改变过任何一次迁移目标 —— 这是一个如实保留的否定读数。
  4. 全知臂只跑 SHARE=0：该臂的迁移决策读当年真值，不读记忆，E4 已逐 tick 证明
     它的行动与物质演化对 SHARE_M 不变。它的记忆与信息账会变，那不是模拟错误。
  5. 平均陈旧度 = stale_sum / 迁移次数，单位是年；迁移为 0 时记“不适用”，不记 0。
  6. 继承 EXP-01/02/03 的全部已知限制：迁移储存损失结构性恒为零、默认样本无灭绝、
     多数假设为 D 级、跨版本存档兼容与人口学标定都没有做过。""")
