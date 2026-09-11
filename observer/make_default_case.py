"""生成随仓库分发的预生成案例（真跑，不是假数据）。

用法：python3 -m observer.make_default_case
"""
from . import presets

# 选 seed 4242：120 年里有 48 年出现“同格多个群体”，默认案例一打开就能看到同格摆放，
# 同时 MOVE_MORT_M=50‰ 让 EXP-03 的机制真的在动。挑的是**可观察性**，不是挑好看的结果。
CASE = dict(run_id="preset-s4242-sig400-mort50", seed=4242, years=120, sigma_m=400,
            move_mort_m=50, arm="memory",
            label="预生成案例 · seed 4242 · SIGMA_M 400‰ · MOVE_MORT_M 50‰ · 记忆臂 · 120 年")

if __name__ == "__main__":
    out = presets.build(**CASE)
    size = sum(p.stat().st_size for p in out.iterdir()) / 1024
    print(f"已生成 {out}（{size:.0f} KB）")
    for p in sorted(out.iterdir()):
        print(f"  {p.name:14} {p.stat().st_size/1024:8.1f} KB")
