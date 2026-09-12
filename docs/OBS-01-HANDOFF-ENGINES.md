# OBS-01 交接 · 六台引擎接入的验收证据（obs-1.8）

后台的能力字段由 UI 分支（Grok）在 `a217dc4` 先落地，本文件补的是**验收**：
六台引擎各自真跑一遍、按各自原始哈希核对、缺值确实没被填成 0。
字段定义以 [`OBS-01-API-CONTRACT.md` §6](OBS-01-API-CONTRACT.md) 为准，这里不重复。

检查脚本：`python3 observer/run_tests.py` 的 **O33 组（34 项）**。

---

## 1. 六台引擎与它们各自的能力

| 引擎 | 冻结身份 | 有的参数 | 没有的参数 | 人口分项账 |
|---|---|---|---|---|
| `exp01` | `20da486`（冻结只读） | —— | sigma_m / move_mort_m / share_m / aid_m / recip_m | 无 |
| `exp02` | `c5a1f18`（冻结只读） | sigma_m | move_mort_m / share_m / aid_m / recip_m | 无 |
| `exp03` | `6b6af4f`（冻结只读） | sigma_m / move_mort_m | share_m / aid_m / recip_m | 有 |
| `exp04` | `68015cc`（已审阅） | + share_m | aid_m / recip_m | 有 |
| `exp05` | `d20a015`（待审） | + aid_m | recip_m | 有 |
| `exp06` | 本轮实现（待审） | + recip_m | —— | 有 |

`engine_sha256` 实测就是那两个冻结提交里的源码（O33b6 逐字节核对 `git show 20da486:exp01/verify.py`
与 `git show c5a1f18:exp02/verify2.py`）。默认引擎仍是 `exp03`，没有改。

---

## 2. 缺的指标长什么样（**不是 0**）

EXP-01 的第 10 年记录实测：

- `integrity` 只有 `conservation_error` 与 `state_hash` —— `population_identity_error`
  **整个键都不出现**（EXP-01/02 没有出生/原死亡/迁移死亡分项账，也就没有人口恒等式可查）。
- `bands[*]` 没有 `macc` 键（群体级迁移死亡累计是 EXP-03 才引入的机制）。
- `cum` / `year` 里没有 `births_cum` / `deaths_demo_cum` / `mig_deaths_cum` /
  `need_cum` / `personyear_cum` / `deficit_cum` / `clim_*`；两个字典的键集合完全一致，
  **没记的量根本不参与差分**（否则会出来一串假的"当年 0 次"）。
- EXP-02 比 EXP-01 多了 `deficit_cum` 与 `clim_*`（资源波动账随 EXP-02 引入），
  但仍然没有人口分项账。

界面侧请按 `GET /api/config` 的 `engines[*].recorded_note` 显示"未记录"：

> year/cum 与 band 只含冻结引擎状态里实际存在的键；省略的指标未测量，界面须显示未记录，禁止填 0 冒充。

**开局人口是个例外**：EXP-01/02 模型里没有 `pop_start`，但开局人口是**数得出来的** ——
`meta.pop_start = 120`，`meta.pop_start_note = "sum of initial band sizes; engine has no
pop_start field"`。这是同一个量的另一种算法，不是拿 0 顶替；而且只在第 0 年推算，
晚一步就只会给 null。

---

## 3. 没有援助机制的引擎

`/relations` 与 `/band/{id}` 都带 `engine_supports`（obs-1.8，两处由后台同一个函数产出）：

```
GET /api/runs/<exp01 的运行>/relations
  engine_supports = {"engine":"exp01","sigma":false,"move_mort":false,
                     "share":false,"aid":false,"recip":false}
  totals.edges = 0
  source 末句："engine_supports.aid=false 时边集为空是能力事实，不是缺年。"
```

群体卷宗同样：`aid_memory = null`、`aid_given.transfers = 0`、`engine_supports.aid = false`，
而 `trajectory` 照常有内容。**不要把它显示成"0 笔援助"** —— 那台引擎里根本没有援助这回事。

---

## 4. 参数：支持的真传进去，不支持的明确拒绝

- EXP-02 同种子只改 `SIGMA_M`（0 vs 900），`full_digest` 实测不同
  （`dbf2d95d37bdef6f…` vs `3d4a5e58cc3543b3…`）—— 参数确实走到了引擎里。
- 不支持的参数传非 0 → `400`，提示写明是哪台引擎没有它：
  `引擎 exp01 没有 SIGMA_M 这个参数，不要把 EXP-03 的波动参数套到 exp01 上`。
- 越界 → `400`；非整数 / 布尔 → `422`。
- 传 0 仍然放行：**零值不等于"不支持"**，EXP-01 带 `sigma_m: 0` 是合法请求。

---

## 5. 记录层没有扰动模型

EXP-01 与 EXP-02 各跑 40 年，用**它们自己的** `state_hash` / `full_digest`
（按路径只读加载冻结源码，不借道适配层）与独立重跑逐年比对：

- 40 个逐年状态哈希逐字相同；
- `full_digest` 相同（`36acb90a…/f1ddca6e…`、`82e6f88a…/1c7dc5b0…`）。

`O12` 每次测试仍然核对 `exp01/`、`exp02/`、`exp03/` 与各自冻结提交逐字节相同。

---

## 6. 失败路径（这些检查确实会红）

- 把缺的指标填成 0（`macc`/`population_identity_error`/`cum` 补零）→ O33e/e2/e3/e6 红 4 项；
- 去掉"不支持的参数传非 0 就拒绝"→ O33g/g2 红 2 项。

本轮 `observer/run_tests.py` 247 项全过（含 O33 的 34 项），`ops/test_dispatch.py` 97 项全过。
