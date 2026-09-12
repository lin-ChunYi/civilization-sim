"""EXP-05 可行性只读探针：现有世界里"同格有余粮者与缺粮者并存"到底有多常见。

**这不是 EXP-05 的实现**，也不是另开一轮研究：它只在已审阅的 EXP-04 引擎
（exp04/verify4.py，commit 68015cc）上只读地数一数，回答一个问题——
援助这条规则有没有触发面。EXP-01 的教训是分裂冲突在 175 次申请里撞车 0 次，
一个永不触发的机制不值得做。

口径（写明近似之处，不含糊）：
  * 位置取**每个 tick 开始时**的位置 —— 援助相位在采集之后、迁移之前，位置就是这个。
  * 余粮/缺口取**该 tick 结束时**的读数：
      缺粮 ⟺ E_m < 1000（当年可用粮食不够自己的需求）；
      有余粮 ⟺ E_m >= 1000 且期末储粮 > 0。
    期末储粮是**腐损之后**的数，所以它是当年余粮的下界，不是精确值。
  * 当年就消失（人口归零被移除）的群体不在期末读数里，会被漏掉。
真正精确的供给与缺口由 EXP-05 自己在援助相位上算，这里只回答"有没有"。

用法：python3 probes/exp05_feasibility.py
"""
import importlib.util

ENGINE = "/Users/ecool/civilization-sim/exp04/verify4.py"
SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]
YEARS = 300

_spec = importlib.util.spec_from_file_location("exp04_readonly", ENGINE)
v4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v4)          # 只读加载，不修改 exp04/


def probe(sigma_m, move_mort_m, share_m):
    t_any = t_tot = 0
    cell_hits = 0
    pair_ticks = 0
    donors = receivers = 0
    for sd in SEEDS:
        st = v4.make_world(sd, "", sigma_m, move_mort_m, share_m)
        for _ in range(YEARS):
            where = {bid: b['cell'] for bid, b in st['bands'].items() if b['size'] > 0}
            v4.step(st)
            by_cell = {}
            for bid, cell in where.items():
                b = st['bands'].get(bid)
                if b is None or b['size'] == 0:
                    continue
                e = b.get('E_m', v4.MILLE)
                rich = e >= v4.MILLE and b['store'] > 0
                poor = e < v4.MILLE
                if rich or poor:
                    by_cell.setdefault(cell, []).append((bid, rich, poor))
            t_tot += 1
            hit = 0
            for cell, members in by_cell.items():
                r = [m for m in members if m[1]]
                p = [m for m in members if m[2]]
                if r and p:
                    hit += 1
                    donors += len(r)
                    receivers += len(p)
            if hit:
                t_any += 1
                cell_hits += hit
                pair_ticks += 1
    return dict(t_any=t_any, t_tot=t_tot, cell_hits=cell_hits,
                donors=donors, receivers=receivers)


print("=" * 104)
print("EXP-05 可行性只读探针 —— 在 EXP-04 引擎上测量，不含任何援助机制")
print(f"7 个种子 × {YEARS} 年；同格并存 = 同一格上同时有'有余粮者'与'缺粮者'")
print("=" * 104)
print(f"  {'SIGMA':>5} {'MORT':>5} {'SHARE':>6} | {'有并存的tick':>12} {'/总tick':>8} {'占比':>7} "
      f"{'并存的格×年':>12} {'有余粮者人次':>12} {'缺粮者人次':>11}")
for sg in (0, 400):
    for mm in (50,):
        for sh in (0, 1000):
            r = probe(sg, mm, sh)
            print(f"  {sg:>5} {mm:>5} {sh:>6} | {r['t_any']:>12} {r['t_tot']:>8} "
                  f"{r['t_any'] / r['t_tot'] * 100:>6.1f}% {r['cell_hits']:>12} "
                  f"{r['donors']:>12} {r['receivers']:>11}")
print()
print("读法：这些数字只说明'援助有触发面'，**不说明援助会带来更好的结果**。")
print("      后者由 EXP-05 自己的扫描回答，而且结果不符合预想也照样保留。")
