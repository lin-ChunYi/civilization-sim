# OBS ↔ 观看计划 数据约定（obs-1.11）

`GET /api/runs/{run_id}/watch-plan` 的固定口径。给 UI 分支用；改接口前先改本文件。
通用部分见 [`OBS-01-API-CONTRACT.md`](OBS-01-API-CONTRACT.md)，
EXP-07 的 `farm` 段见 [`OBS-EXP07-CONTRACT.md`](OBS-EXP07-CONTRACT.md)。

本批服务契约版本 **`obs-1.11`**（新增这一个只读端点；既有端点的语义一个字没改，
默认引擎仍是 `exp03`）。

---

## 1. 这个端点是什么、不是什么

**是**：把**已经存下来**的一段历史，整理成"可以一章一章放给人看"的目录 ——
哪一年、哪条事件、谁参与、在哪个格、记录里的数量是多少。

**不是**：

- 不是新机制。它**不跑模拟、不补事件、不写任何年记录/检查点/模型对象**，
  也**不占模拟任务槽** —— 取导览不会挤掉正在算的运行。
- 不是"未来预告"。只扫描**请求开始那一刻**确定下来的有效前缀 `0..recorded_through`；
  尾巴上还没写完的那一年不算（判据与 `series`/`year` 完全一致）。
- 不是剧本。`facts` 全是记录里的字段与原始单位，**没有一句由模型生成的解释**。
- 不是人物档案。`identities` 只有"第一次出现 / 最后一次出现 / 亲本 / 消失年"，
  **没有任何未来状态快照**；人物卡仍然按当前回放年去取
  `/api/runs/{id}/band/{id}?at_year=N`。

子运行读**自己**那份完整历史（从第 0 年起），**不依赖父运行还在不在**。

---

## 2. 请求

```
GET /api/runs/{run_id}/watch-plan[?through=N]
```

- 沿用既有 `require_read` 读鉴权（设了 `OBSERVER_TOKEN` 就要带令牌）。
- `through=N` 可选：**把计划钉在某个水位上**。导览开始后一直用自己那份水位，
  运行继续长出新历史也不会中途换章节；用户主动刷新时再不带参数取一次。
  `N` 超过已记录年数 → **400**，不静默夹取；负数 → 400。
- 运行不存在 → **404**；第 0 年都还没写完 → **409**（明确报错，
  **不会**返回一份空目录再宣布"看完了"）。

后台侧有**带上限的只读缓存**，键包含 `run_id`、有效水位、年记录文件标识
（mtime+size）与 schema/契约版本 —— 记录长出新的一年键就变了，
文件没动过就直接复用，不会因为前端每 1.5 秒轮询就全量重扫。

---

## 3. 响应

```json
{
  "schema": "watch-plan-1",
  "run_id": "preset-anime-farm250",
  "root_run_id": "preset-anime-farm250",
  "source": {
    "engine_sha256": "6c18ed20b1e9…1e6a20",
    "recorded_through": 300,
    "identity_complete_through": 300,
    "scope": "recorded_history"
  },
  "identities": [
    {"id": "7527436045698980774", "first_year": 0, "last_year": 300,
     "parent_id": null, "extinct_year": null}
  ],
  "chapters": [ … 见 §5 … ],
  "missing_kinds": [{"kind": "repay", "reason": "not_observed"}]
}
```

`source` 四项固定：

| 字段 | 含义 |
|---|---|
| `engine_sha256` | 产出这段记录的引擎源码哈希；记录里没存就是 `null`（**不知道 ≠ 不一样**） |
| `recorded_through` | 这次扫描用到的最后一年（= 请求开始时的有效水位，或你指定的 `through`） |
| `identity_complete_through` | 身份目录完整到哪一年。本实现一次扫完整段前缀，所以恒等于 `recorded_through`；字段留着是为了让前端能识别"部分目录"，**不要假定它一定相等** |
| `scope` | 目前只有 `"recorded_history"`：扫的是已落盘的历史 |

---

## 4. `identities`：稳定别名的唯一依据

```json
{"id": "10755205082838774531", "first_year": 218, "last_year": 300,
 "parent_id": "10929267446675359160", "extinct_year": null}
```

- **`id` 一路是字符串**，64 位。排序由后台定死：按 `(first_year, 数值型完整 id)`，
  前端**不要**用 JS `Number` 排 64 位 id —— 会掉精度，别名顺序就不稳了。
- `first_year` = **这份档案里第一次可核实地出现**，不是生日；
  `last_year` = 最后一次出现在在世记录里，**不等于死亡年份**。
- 只有真的出现过 `extinct` 事件才填 `extinct_year`；否则 `null`。
- `parent_id` 只认 `split` 事件里写下来的那一条，不按"谁先出现"猜；开局群体是 `null`。
- 目录是**逐年实际在世记录**扫出来的，不是看"群体总数有没有变多"。
  同一年一个群体消失、另一个分裂，净数不变，这种年份照样完整。
- 事件里提到、但从没出现在在世记录里的 id **不会**被补成开局实体。

**用途分两种，别混**：

1. 普通自由观察：只用它定**稳定别名与形象**（颜色仍绑定 id）。
   **不能**在回放第 2 年时把第 295 年的关系或经历摆到卡片上。
2. 用户主动进入"完整已记录历史导览"时，才用 `chapters`。

---

## 5. `chapters`：最多 7 章

开局、首次实际开垦、首次实际采收、首次迁移、首次**非回助**援助、首次回助、
当前记录末年概览。按时间排序，**开局永远在最前、末年概览永远在最后**；
同年不同事件各留各的 id，顺序照记录里的原顺序 —— 这只是记录顺序，
**不宣称严格的子年因果先后**。

`recorded_through == 0`（只有开局那一年）时只有 `origin` 一章。
全程没有任何事件也至少有 `origin` + `final` 两章。

每章固定这些键：

| 字段 | 说明 |
|---|---|
| `chapter_id` / `kind` | `origin` / `clearing` / `harvest` / `migrate` / `aid` / `repay` / `final` |
| `year` | 展示年份 |
| `title` | 短标签（"第一次开垦"），**不是文案**：文案由界面自己写 |
| `event_id` | 对应的真实事件 id；`origin` / `final` 是 `null` |
| `actor_ids` | 出场主体，**只来自事件本身**。援助固定 `[给的人, 收的人]`；开垦/收成是参与群体表；迁移是那一支 |
| `cell` | 事发格（农业与援助有；迁移用 `from`/`to`） |
| `from` / `to` | 迁移的起讫格，其余为 `null` |
| `facts` | 见下 |
| `basis_event_ids` | 只有回助才非空：**记录里写着的**依据事件 id |

### `facts`：事实，不是故事

每一项都是 `{"value", "unit", "source"}`，可选 `year` / `basis` / `note`：

```json
"harvested_kcal": {"value": 3849598, "unit": "kcal", "source": "events[].kcal"},
"pop_year_end": {"value": 120, "unit": "人", "source": "agg.pop",
                 "year": 1, "basis": "year_end",
                 "note": "第 1 年末的全局人口，不是这件事直接造成的变化"}
```

- `source` 就是**记录里的字段名**（`events[].amount_m`、`year.mig_deaths_cum`、
  `agg.store_total` …），照着能自己去年记录里查。
- `basis` 三种：`snapshot`（开局那一年的状态）、`year_end`（**全年口径**）、
  `cumulative`（累计到这一年）。
  **凡是 `year_end` / `cumulative` 的都不是这件事造成的变化**，`note` 里也写了；
  界面不要说成"因为这件事，所以人口变成了 X"。
- 单位一律原始单位：`kcal`、`field_m`（1000 = 1 个耕作规模单位，**不是亩/公顷/人数**）、
  `‰`、`人`、`次`。`person_years` 是按模型口粮折算的**展示值**，不是人数。

### 回助的依据

`basis_event_ids` 只取事件里已记录的 `basis.prior_events`，并且逐条核过：
**在本次运行里确实存在、而且年份早于这次回助**。核不过的一律不放进来。

它只能说明"以前确实有过这样一笔往来"，**不能**据此宣布"优先规则改变了分配结果" ——
那需要同状态分配对照（`/api/runs/{id}/year/{t}` 的 `recip.compare`），是另一回事。

---

## 6. `missing_kinds`：没有就是没有

没发生的事**不会**生成那一章，也不会编饥荒/战争/对白去凑满 7 章。缺的写清是哪一种缺：

| `reason` | 含义 | 界面怎么说 |
|---|---|---|
| `engine_lacks_mechanism` | 这台引擎根本没有这套机制（旧引擎没有农业） | "这个世界里没有这回事"，**不要填 0** |
| `param_zero` | 机制在，但控制它的参数是 0（`FARM_M=0`） | "参数设成了 0，所以一次都没有" |
| `not_observed` | 机制开着、参数非 0，但这段历史里一次都没发生 | "没有发生过" |
| `outside_watermark` | 你指定的 `through` 水位里没有，**但已记录的后面有** | "这一段还没到" |
| `history_incomplete` | 记录还没写完（运行还在跑） | "还在生成" |
| `capability_unknown` | 记录没写引擎、或引擎不在登记表里 | "未记录"，不要猜 |

四条已提交案例的实测结果（`docs/evidence/anime-watch-20260915/`）：

| 案例 | 章节 | 缺项 |
|---|---|---|
| `preset-anime-farm250`（A） | origin 0 · clearing 1 · harvest 2 · migrate 218 · aid 267 · repay 295 · final 300 | —— |
| `preset-anime-exp06`（B） | origin 0 · migrate 26 · aid 73 · repay 128 · final 300 | clearing/harvest `engine_lacks_mechanism` |
| `preset-anime-farm0`（C） | origin 0 · migrate 26 · aid 73 · repay 128 · final 300 | clearing/harvest `param_zero` |
| `preset-anime-farm1000`（D） | origin 0 · migrate 1 · clearing 1 · harvest 2 · final 300 | aid/repay `not_observed` |

D 的第 1 年里迁移排在开垦前面 —— 那是**记录顺序**，不是相位先后。

---

## 7. 界面上**不要**这样说

- 不要把两章之间的年差画成连续的几天：第 2 年 → 第 218 年**相隔 216 年**，
  画面上的人物一直是**群体代表**，不是活了几百岁的个人。
- 不要拿 `facts` 里 `year_end` / `cumulative` 的读数说成某一件事的后果。
- 不要说"因此没有人饿死""为了感恩""明年一定丰收" —— 记录里没有这些。
- 不要把当前储粮折算成"保证能活多少天"。
- 不要在回放第 2 年时展示第 295 年的关系或经历。
- 跳到某个群体首次出现之前时，说"当时尚未在记录中出现"，**不要**说"已经消失"。

---

## 8. 真实响应与验证

```bash
python3 -m observer.make_anime_cases                      # 现做四条案例（几秒）
OBSERVER_DATA_DIR=<空目录> python3 -m uvicorn observer.app:app \
    --host 127.0.0.1 --port <空闲端口>
curl -s http://127.0.0.1:<端口>/api/runs/preset-anime-farm250/watch-plan

python3 observer/test_watch_plan.py --report <路径>.json   # 定向验收
```

四条案例的真实响应原样存在
[`docs/evidence/anime-watch-20260915/`](evidence/anime-watch-20260915/)。
