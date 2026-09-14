# OBS ↔ EXP-07 数据约定（obs-1.10）

给 UI 分支的固定口径。字段定义以本文件为准；通用部分见
[`OBS-01-API-CONTRACT.md`](OBS-01-API-CONTRACT.md)，续演见
[`OBS-CONTINUATION-CONTRACT.md`](OBS-CONTINUATION-CONTRACT.md)。

本批服务契约版本 **`obs-1.10`**。**默认引擎仍是 `exp03`**，没有改。

---

## 1. 新引擎与新参数

`GET /api/config` 的 `engines` 多了一台：

```json
"exp07": {
  "engine_label": "EXP-07 原始耕作与弃耕",
  "engine_params": ["sigma_m","move_mort_m","share_m","aid_m","recip_m","farm_m"],
  "unsupported_params": [],
  "metrics": {"farm": true, ...},
  "constants": {"FARM_M_MAX":1000,"FIELD_CAP_M":60000,
                "FIELD_DECAY_M":200,"FARM_YIELD_M":2500, ...}
}
```

- `farm_m` 排在 `recip_m` **之后**，能力表里有 `min/max/default/unit/note`。
- 旧引擎把 `farm_m` 列进 `unsupported_params`；**传非 0 一律 400**，提示写明该换哪台引擎。
  传 `0` 照常放行（零值不等于不支持），而且**不会**把这个参数传给旧引擎。
- `POST /api/runs` 的 body 多一个 `farm_m`（严格整数，`bool`/小数 → 422，越界 → 400）。

**1000 个 field 刻度 = 1 个"耕作规模单位"**，不是亩、公顷，也不是人数。
`FIELD_CAP_M` / `FIELD_DECAY_M` / `FARM_YIELD_M` 是本项目自拟的实验假设（D 级），
**不冒充中国史校准**。

---

## 2. 年度记录新增 `farm` 段（`GET /api/runs/{id}/year/{t}`）

```json
"farm": {
  "schema": "farm-1",
  "field_m": [0, 0, 5000, ...],        // 按 meta.cell_ids 顺序的 64 个整数，**年末存量**
  "field_total_m": 30000,
  "year": {"farm_effort_m": 30000, "forage_effort_m": 90000,
           "potential_kcal": 54750000, "harvested_kcal": 406042,
           "uncollected_kcal": 54343958, "built_m": 0, "decayed_m": 0},
  "cum":  {"farm_effort_m": 90000, "forage_effort_m": 270000,
           "potential_kcal": ..., "harvested_kcal": ..., "uncollected_kcal": ...,
           "built_m": ..., "decayed_m": ...},
  "cells": [ ... ],
  "note": "..."
}
```

- `field_m` 是**年末存量**，**不要**把它当流量累加；总量另给 `field_total_m`。
- `year` / `cum` 只放流量，两边**同名**，**七项全部是严格整数**（不会出现 `null`）。
  `cum` 是引擎里那本同名累计账的当前值 —— 包括 `forage_effort_m`：
  采集劳动在相位前按冻结的人数逐年累加，**进状态哈希、进检查点、跟着续演走**。
  第 0 年七项的 `year` 与 `cum` 都恰好是 0。
- 两项劳动可以互相印证：任何一年
  `year.farm_effort_m + year.forage_effort_m == Σ participants.population_before × 1000`。
- `cells`：本年**有劳动或有旧耕地**的格，按 `cell` 升序。
  "有劳动"包括**只有采集劳动**的情况 —— 所以 `FARM_M=0` 时 `cells` 也不是空的：
  那些格的 `built_m/decayed_m/potential_kcal` 都是 0、`weather_m` 为 `null`，
  但 `participants` 会如实列出在那儿采集的群体。

  **逐格能加回当年总量**：任何一年
  `Σ cells[*].potential_kcal == year.potential_kcal`，
  `harvested_kcal` / `uncollected_kcal` / `built_m` / `decayed_m` 四项同理。
  逐格明细取自引擎的**逐格结算痕迹**，不是事件日志 —— 事件只在实际量 > 0 时才记，
  所以"潜在产出一颗没人收"的格在日志里什么都没有，照日志拼出来的 `cells` 会比
  `year` 少一截（少掉的正是没人收的那部分）。`weather_m` 为 `null` 只代表
  **这一格这一年没有产量结算**（没地也没耕作劳动），不是"天气等于 1000"。
  每项：

  | 字段 | 说明 |
  |---|---|
  | `cell` | 格号 |
  | `field_before_m` / `field_after_m` | 相位前 / 年末的耕地规模 |
  | `worked_m` | 被劳动维护到的部分（产量只按它算） |
  | `built_m` / `decayed_m` | 本年开垦 / 退化 |
  | `weather_m` | 该格该年的天气乘数（千分之一）；`SIGMA_M=0` 时为 1000 |
  | `potential_kcal` / `harvested_kcal` / `uncollected_kcal` | 潜在 / 实收 / 没人收的 |
  | `participants` | 见下 |

- `participants` 每项：`id`（**字符串**，64 位）、`population_before`、
  `farm_effort_m`、`forage_effort_m`、`forage_kcal`、`crop_kcal`。
  **主体来自相位前状态**（人数是本年人口变化之前的），不拿年末位置倒推。
  `farm_effort_m + forage_effort_m == population_before * 1000` 恒成立。

- **第 0 年**：`year` 全 0、`cells` 为空、`field_m` 全 0。
- **旧引擎（exp01–exp06）整个 `farm` 段缺席**，不是给一堆 0。
  界面据此显示"未记录"，不要自己补默认值。

---

## 3. `series` 只放轻量的 farm

`GET /api/runs/{id}/series` 的每一项多一个：

```json
"farm": {"year": {...}, "cum": {...}, "field_total_m": 30000}
```

**不放** `participants`，**不放**完整 `cells`。旧的 series 字段一个都没改。

---

## 4. 耕作事件（追加在 `year.events` 末尾）

三类：`field_built`、`farm_harvest`、`field_decay`。每条都有：

```json
{"id": "t1-field_built-0", "year": 1, "type": "field_built", "cell": 0,
 "participants": ["7567856178022945294"], "labour_m": 5000, "labour_used_m": 5000,
 "field_before_m": 0, "field_after_m": 5000, "amount_m": 5000,
 "text": "群体-69066D 在第 0 号格开垦了 5.0 个耕作规模单位",
 "source": "模型状态 st['field_m'] 与本相位的劳动结算",
 "unrecorded": "作物品种、耕作方式与土地权属未记录：模型里没有这些量。"}
```

`farm_harvest` 另有 `kcal` / `person_years` / `worked_m` / `weather_m` /
`potential_kcal` / `uncollected_kcal` / `per_band_kcal`；
`field_decay` 另有 `unworked_m` / `amount_m`。

- `id` 与旧事件同一套规则（`t<展示年>-<类型>-<当年序号>`），同一次运行里唯一可复现。
- **内部 tick → 展示 year 的换算只对 EXP-07 自己这份日志做**；
  旧记录与旧事件 id **一个都没有重写**。
- 同格同年同类型在模型侧已经聚合成一条，参与者明细保留。
- 只有实际量 > 0 才有事件；零产量只留在 `farm.year` 里，**不编"丰收"**。

---

## 5. 续演（EXP-06 与 EXP-07 各自同版本）

- `GET /api/config.continuation.engines` 现在是 `["exp06","exp07"]`。
- **EXP-06 的存档只能续成 EXP-06**，不会被无声升级成农业世界：
  引擎身份（全量 sha256）与记录器格式两道都拦着。
- 记录器格式随引擎分家：
  EXP-01～06 是 `obs-recorder-v1`；**EXP-07 是 `obs-recorder-farm-v1`**（多一个耕作日志游标）。
  检查点里的 `recorder_schema` 必须与引擎对得上，**未知格式一律拒绝，不补默认值**。
- 检查点保存完整耕地 `field_m`、`farm_log`、四本新账与新游标。
- 参数比对按引擎取键：`farm_m` **只对声明支持它的引擎**参与比对 ——
  旧 EXP-06 检查点里没有这个键，无条件比对会把正常旧存档误判成 `config_mismatch`。
- 原因码沿用续演契约那一套，另加：记录器格式与引擎对不上时给 `checkpoint_invalid`
  （引擎本身就不同的时候，给的是更准确的 `engine_mismatch`）。

---

## 6. 可回放案例

```bash
# 本批测试服务（独立端口与数据目录，不碰 8765 / 8772 / 8788）
OBSERVER_DATA_DIR=/tmp/chronicle-exp07-20260913/api/testdata \
  python3 -m uvicorn observer.app:app --host 127.0.0.1 --port 8902

# 新建一条 EXP-07 运行（**演示用 SIGMA_M=400**，这样天气乘数不是恒定的 1000，
# 界面能看到 weather_m 真的在变；SIGMA_M=0 只适合做受控对照，不适合当演示）
curl -s -X POST http://127.0.0.1:8902/api/runs -H 'Content-Type: application/json' -d '{
  "seed":4242,"years":300,"engine":"exp07","arm":"memory",
  "sigma_m":400,"move_mort_m":50,"share_m":1000,"aid_m":1000,"recip_m":1000,"farm_m":250,
  "label":"耕作演示 sigma400"}'

# 看第 1 年的 farm 段与耕作事件
curl -s http://127.0.0.1:8902/api/runs/<run_id>/year/1 | python3 -m json.tool

# 从检查点续演 300 年（口径见续演契约）
curl -s -X POST http://127.0.0.1:8902/api/runs/<run_id>/continue \
  -H 'Content-Type: application/json' \
  -d '{"additional_years":300,"request_id":"<uuid>"}'
```

真实请求与响应（含两个服务的 PID 与起停）在
`docs/evidence/exp07-20260913/api-report.json` 的 `http_calls` / `services` 段。

**给前端的真实案例清单**：[`ANIME-REAL-CASES.md`](ANIME-REAL-CASES.md)
—— 十个带 `run_id` / 事件 id / 当年人口存粮耕地的可回放案例，外加两组受控对照、
"本案例里没有发生的事"，以及"参考图里有、模型里没有"的对照表。

**给 Grok 的可回放样例**：`docs/evidence/exp07-20260913/sample-year.json`
—— EXP-07 / seed 4242 / **SIGMA_M=400** / FARM_M=250 / 12 年，含第 0、1、2、12 年的完整
年度记录、`meta.cell_ids` 与 series 尾项。用 SIGMA_M=400 是有意的：
那时 `weather_m` 每格每年都在变（这份样例里出现了 20 种取值，最低 651），
界面能看到真实波动；`SIGMA_M=0` 会让 `weather_m` 恒为 1000，只适合做受控对照。

实测第 12 年（可直接对照）：

```
year: {"farm_effort_m":32500,"forage_effort_m":97500,"potential_kcal":55597711,
       "harvested_kcal":2986031,"uncollected_kcal":52611680,"built_m":250,"decayed_m":22}
cum : {"farm_effort_m":371000,"forage_effort_m":1113000,"potential_kcal":603486871,
       "harvested_kcal":53582401,"uncollected_kcal":549904470,"built_m":33622,"decayed_m":1038}
```

七项都是整数，且把逐年 `year` 自己加一遍正好等于 `cum`。

---

## 7. 界面上**不要**这样说

- 不要把"没挪过窝"说成定居、村落或文明；模型里没有村落、产权与制度。
- 不要说"开垦消耗了森林 / 改变了承载力"——野外 `cap` / `regen` 一个字没改。
- 不要把"未采收"显示成浪费或损耗：它只是采收限额的算术后果，就地作废，
  不转给别人、不留到明年、不进库存。
- 不要把 field 刻度当成亩、公顷或人数。
- 旧引擎没有 `farm` 段时显示"未记录"，**不要填 0**。
