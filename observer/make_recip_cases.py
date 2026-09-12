"""生成"关闭 / 开启优先回助"的真实对照案例，随仓库分发给界面用。

**两条都是自然演化**（同种子、同参数，只差 RECIP_M），不是人工构造的测试案例。
人工构造的场景在 exp06/run_tests.py 里，不放进观察台，免得被当成自然演化。

用法：python3 -m observer.make_recip_cases
"""
from . import presets

# 选 seed 31337 / SIGMA_M=0：第 124 年出现回助、第 125 年优先规则第一次**真的改变了分配**
# （判据是逐对总额，不是拆笔），150 年足够看到两样东西，数据也不会大到进不了版本库。
COMMON = dict(seed=31337, years=150, sigma_m=0, move_mort_m=50, arm="memory")
CASES = [
    dict(run_id="preset-exp06-recip0", engine="exp06", share_m=1000, aid_m=1000, recip_m=0,
         label="对照案例 A · 关闭优先回助（RECIP_M=0）· seed 31337 · 150 年", **COMMON),
    dict(run_id="preset-exp06-recip1000", engine="exp06", share_m=1000, aid_m=1000,
         recip_m=1000,
         label="对照案例 B · 开启优先回助（RECIP_M=1000）· seed 31337 · 150 年", **COMMON),
]

if __name__ == "__main__":
    for case in CASES:
        out = presets.build(**case)
        size = sum(p.stat().st_size for p in out.iterdir()) / 1024
        print(f"已生成 {out.name}（{size:.0f} KB）")
