# EXP-07 · 实测证据（2026-09-13）

工作目录 `/Users/ecool/civilization-sim-exp07-farming`，分支 `backend/exp07-farming`，
基准 `b12bdd77baabf24eed05a600dc35aa8d0aba1bd4`。
测试端口 **8902**、独立数据目录 `/tmp/chronicle-exp07-20260913/`，
**没有碰 8765 / 8772 / 8788 或任何旧服务**。这里没有数据库文件与凭据。

## 1. 模型与实验（C_FARM_01）

| 文件 | 内容 |
|---|---|
| `scan.json` / `scan.csv` | 42 组 × 300 年的原始读数（九本账 42/42 恒等） |
| `first-events.json` | 全部 42 组的**第一次开垦**与**第一次收获** |
| `tests-report.json` | `exp07/run_tests.py` 的 35 项结果 |

## 2. 后台接线（C_FARM_API_01）

```
EXP07_TEST_PORT=8902 python3 observer/test_exp07.py \
    --report /tmp/chronicle-exp07-20260913/api/report-full.json
→ 通过 59 / 失败 0 / 未覆盖 0，退出码 0（R1 返工后重跑的完整模式）
```

| 文件 | 内容 |
|---|---|
| `api-report.json` | 机器可读证据：命令与退出码、两个服务的 PID 与起停、真实 HTTP 请求与响应 |
| `api-test.txt` | 完整输出 |
| `api-service-A.txt` / `api-service-B.txt` | 两个测试服务的启动日志 |
| `sample-year.json` | 一条真实 EXP-07 运行（SIGMA_M=400）的第 0/1/2/12 年记录与 series 尾项 |
| `observer-regression.txt` | `observer/run_tests.py` 256 项 |

要点：

- **参数真的生效**：同种子只改 `FARM_M`，`full_digest` 就不同；
  旧引擎收到非零 `farm_m` 一律 400，`farm_m=0` 照常放行且不传给旧引擎。
- **EXP-07 60+60 与连续 120 年逐年完全一致**（含 farm 段与事件 id）。
- **300 年 → 停服务 A（pid 50165，退出码 -15）→ 起服务 B（pid 50432，同一数据目录）
  → 再续 300 年**，与连续 600 年**逐年完全一致**，首处差异 `None`；
  第 600 年的完整模型状态、耕地与农业日志全部相同；95 269 个事件 id 逐个相同且无重复。
- **旧存档兼容**：用**基准 `b12bdd7` 的代码**真跑出一份 EXP-06 存档
  （`recorder_schema=obs-recorder-v1`，`params` 里没有 `farm_m`），
  再用**本轮的新代码**读它 —— 仍然 `eligible=true`，续演跑完之后
  `engine` 还是 `exp06`、`farm_m=0`，**没有被升级成农业世界**。
- **拒绝路径**：改 `FARM_M` → `config_mismatch`；记录器格式写成旧版或未知 →
  `checkpoint_invalid`；坏字节 → `checkpoint_invalid`；换引擎 → `engine_mismatch`。
  这些拒绝之后**父运行的历史与检查点逐字节不变**。
- **49/50 名额边界**：49 条时续演占掉第 50 条，worker 复核存档**不再**把自己已占的名额
  算成新超限（`for_new_run=False`）；上限没放松 —— 第 51 条仍然 409，
  满额时新的续演请求照样被 `quota_exceeded` 挡住。

## 2b. R1 返工（2026-09-13）

第一轮验收正确地判红了一处：固定接口要求 `cum` 是 `year` 那七项流量的**同名累计**，
而我把 `cum.forage_effort_m` 写成了 `null`（理由是"引擎没有这本账"）。
**不能以没建账为由改已固定的接口** —— 这一轮把账真的建起来了：

- `exp07/verify7.py` 新增 `forage_effort_cum`：在相位 2a 按**相位前冻结的人数**逐年累加，
  并进 `LEDGER_FIELDS`，因此**进状态哈希、进检查点、跟着续演走**。
- `farm.year` / `farm.cum` 七项现在**全是严格整数**，第 0 年都恰好是 0；
  轻量 series 与逐年记录逐字段一致。
- 定向测试**独立重算** `cum == Σ year`（不调用生产累计逻辑，也不只看"非 null"）：
  覆盖 `FARM_M=0 / 250 / 1000`、60+60 的续演边界（`cum[61] − cum[60] == year[61]`）
  与 300→重启服务→600 的边界（`cum[301] − cum[300] == year[301]`），
  并断言 `forage_effort_m` 只有在 `FARM_M=1000` 时才为 0。
- 顺带核查了另一条：`cells` 的"有劳动"包含**只有采集劳动**的格。
  原实现只从 `farm_log` 拼 `cells`，`FARM_M=0` 时会是空的 —— 已改成
  "相位前有群体的格 ∪ 相位前耕地 > 0 的格"，位置取相位前快照，参与者同样来自相位前状态。
- 给 Grok 的演示案例改用 **SIGMA_M=400**（`sample-year.json`）：
  那时 `weather_m` 每格每年都在变（样例里 20 种取值，最低 651）；
  `SIGMA_M=0` 会让它恒为 1000，只适合受控对照。

## 3. 两件如实记下的代价（已进 `docs/TODO-BACKLOG.md` #17 / #18）

- EXP-07 的逐年记录明显更大：300 年约 **100 MB**，续演再复制一份就翻倍；
  512 MB 的数据目录上限很快会到顶（到顶时如实报 `quota_exceeded`，不丢数据）。
- 检查点随 `farm_log` 线性增大：300 年约 **18 MB**、600 年约 **37 MB**，
  而且**每年都要整份重写**，所以长跑的写入量是 O(n²) ——
  本轮那条 600 年的对照运行，后 100 年明显变慢。
  `MAX_BYTES=64 MB` 在 1000 年左右会被撞到。
  要跑更久得先给 `farm_log` 定截断或分段策略，而不是把上限调大。
