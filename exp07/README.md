# exp07 —— EXP-07「原始耕作与弃耕」

唯一新增机制：群体可以把一部分折算劳动投到耕作上；**耕地跨年保留在地点上**，
没人维护就退化。其余一切照 EXP-06 原样。

规格、公式、42 组读数与"不得宣称"清单见 [`../docs/EXP-07-SPEC.md`](../docs/EXP-07-SPEC.md)。

```bash
python3 exp07/run_tests.py [--report 路径.json]      # 35 项定向测试
python3 exp07/run_scan.py  [--output-dir 目录]        # 42 组 × 300 年观察扫描
```

- `verify7.py` 由 `exp06/verify6.py` 复制而来，**旧引擎一个字节都没改**。
- `FARM_M=0` 时逐步退化到 EXP-06：用 **EXP-06 自己的**字段与哈希口径判定，
  EXP-07 自己的身份哈希本来就不同，不要求相等。
- 最近一次结果：`TESTS.txt`（35 项全过）、`SCAN.txt`（42 组，九本账全恒等）。
- 原始 JSON / CSV 在 `../docs/evidence/exp07-20260913/`。

三个固定常量（`FIELD_CAP_M` / `FIELD_DECAY_M` / `FARM_YIELD_M`）是**本项目自拟的
实验假设（D 级）**，不冒充中国史校准。1000 个 field 刻度 = 1 个"耕作规模单位"，
**不是亩、公顷，也不是人数**。
