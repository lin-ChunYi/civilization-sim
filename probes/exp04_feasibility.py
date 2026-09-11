"""EXP-04 方案的可行性只读探针。

**这不是 EXP-04 的实现。** 这里没有任何信息交换机制、没有合并规则、没有新参数。
它只做两件事，全部在冻结的 EXP-03 引擎（commit 6b6af4f）上以只读方式进行：

  1. 同格频率：每个 tick 开始时（= 相位 6a 的群体位置，此时本 tick 还没有人移动）
     数一数有多少格上站着 >=2 个 size>0 的群体。
  2. 信息落差：对同格的每个群体，做一次纯集合比较——它的邻格里有多少是
     "自己不知道而同格邻居知道"（新增条目），有多少是"双方都知道但对方时戳更新"
     （可更新条目）。只比较，不写回。

目的是在批准方案之前先确认：这个机制有没有触发面，有没有可传的信息。
EXP-01 的教训是分裂冲突在 175 次申请里撞车 0 次——一个永不触发的机制不值得做。

用法：python3 probes/exp04_feasibility.py
"""
import importlib.util

EXP03 = "/Users/ecool/civilization-sim/exp03/verify3.py"
SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]
YEARS = 300

_spec = importlib.util.spec_from_file_location("exp03_readonly", EXP03)
v3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v3)          # 只读加载冻结基线，不修改其中任何文件


def probe(sigma_m, move_mort_m):
    t_any = t_tot = 0
    b_co = b_tot = 0
    mx = 0
    with_new = with_fresh = 0
    new_entries = 0
    for sd in SEEDS:
        st = v3.make_world(sd, "", sigma_m, move_mort_m)
        for _ in range(YEARS):
            by = {}
            for bid, b in st['bands'].items():
                if b['size'] > 0:
                    by.setdefault(b['cell'], []).append(bid)
            co = sum(len(v) for v in by.values() if len(v) >= 2)
            t_tot += 1
            b_tot += sum(len(v) for v in by.values())
            b_co += co
            if co:
                t_any += 1
            if by:
                mx = max(mx, max(len(v) for v in by.values()))
            for bids in by.values():
                if len(bids) < 2:
                    continue
                for x in bids:
                    bx = st['bands'][x]
                    peers = [st['bands'][y] for y in bids if y != x]
                    nb = v3.neighbors(bx['cell'])
                    n_new = sum(1 for j in nb if j not in bx['mem']
                                and any(j in p['mem'] for p in peers))
                    n_fresh = sum(1 for j in nb if j in bx['mem']
                                  and any(j in p['mem']
                                          and p['memt'].get(j, 0) > bx['memt'].get(j, 0)
                                          for p in peers))
                    new_entries += n_new
                    if n_new:
                        with_new += 1
                    if n_fresh:
                        with_fresh += 1
            v3.step(st)
    return dict(t_any=t_any, t_tot=t_tot, b_co=b_co, b_tot=b_tot, mx=mx,
                with_new=with_new, with_fresh=with_fresh, new_entries=new_entries)


print("=" * 104)
print("EXP-04 可行性只读探针 —— 在冻结的 EXP-03 引擎上测量，未实现任何交换机制")
print(f"7 个种子 × {YEARS} 年；同格 = 同一 tick 同一格上 size>0 的群体数 >= 2")
print("=" * 104)
print()
print("1. 触发面：同格发生得够不够多")
print(f"  {'SIGMA':>5} {'MORT':>5} | {'有同格的tick':>12} {'/总tick':>8} {'占比':>7} "
      f"{'同格群体人次':>12} {'总群体人次':>11} {'占比':>7} {'单格最多群体数':>14}")
res = {}
for sg in (0, 400):
    for mm in (0, 50):
        r = probe(sg, mm)
        res[(sg, mm)] = r
        print(f"  {sg:>5} {mm:>5} | {r['t_any']:>12} {r['t_tot']:>8} "
              f"{r['t_any']/r['t_tot']*100:>6.1f}% {r['b_co']:>12} {r['b_tot']:>11} "
              f"{r['b_co']/r['b_tot']*100:>6.1f}% {r['mx']:>14}")
print()
print("2. 信息落差：同格的两方到底有没有东西可传（纯集合比较，不写回）")
print(f"  {'SIGMA':>5} {'MORT':>5} | {'同格群体人次':>12} {'有新增条目':>11} {'占比':>7} "
      f"{'有可更新条目':>13} {'占比':>7} {'人均新增邻格条目':>16}")
for sg in (0, 400):
    for mm in (0, 50):
        r = res[(sg, mm)]
        print(f"  {sg:>5} {mm:>5} | {r['b_co']:>12} {r['with_new']:>11} "
              f"{r['with_new']/r['b_co']*100:>6.1f}% {r['with_fresh']:>13} "
              f"{r['with_fresh']/r['b_co']*100:>6.1f}% {r['new_entries']/r['b_co']:>16.2f}")
print()
print("读法：")
print("  - 『新增条目』= 该群体的邻格里，它自己没有记忆而同格邻居有记忆的格数（UNKNOWN -> 已知）。")
print("  - 『可更新条目』= 双方都有记忆但邻居的时戳严格更新的格数。口径宽松，只要新一年就算。")
print("  - 这两个数只说明存在可传的信息，**不说明传了以后结果会变好**。后者要 EXP-04 自己测。")
