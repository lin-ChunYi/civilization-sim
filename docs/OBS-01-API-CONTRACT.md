# OBS-01 接口约定（后台 ↔ UI 分支）

**这份文件是两边的唯一约定来源。** 后台（Python）与 UI 分支（`observer/web/`）分头改，
靠它对齐；不各自实现一套数据格式。

契约版本 **`obs-1.7`**，由 `GET /api/config` 的 `api_version` 字段给出。
**新增字段 → 小版本 +1；删除或改变已有字段的含义 → 必须先改这份文件并知会对方，再动代码。**

---

## 1. 分工边界（谁改哪些文件）

| 目录 / 文件 | 归属 | 说明 |
|---|---|---|
| `observer/web/` | **UI 分支** | 页面、样式、前端脚本。后台**只读不写**，包括临时文件 |
| `observer/app.py` `store.py` `worker.py` `adapter.py` `config.py` `presets.py` `milestones.py` | **后台** | API、持久化、任务生命周期、只读观察层 |
| `observer/tests/` | **后台** | 后台自己的浏览器回归页（挂在 `/selftest`，与 `/static` 分开） |
| `exp01/ exp02/ exp03/` | **冻结** | 三个基线目录只读，双方都不改（`O12` 每次测试都查） |
| `observer/preset/` | 后台 | 预生成案例数据 |

后台不会往 `observer/web/` 写任何文件：静态目录可用 `OBSERVER_WEB_DIR` 覆盖，
回归用的注入脚本生成到 `observer/tests/web/_poison_app.js`（已 gitignore）。

**不在同一工作目录并行改。** 双方各自分支完成后再统一集成验收。

---

## 2. HTTP API

读接口（设了 `OBSERVER_TOKEN` 时全部需要令牌，请求头 `X-Observer-Token` 或 `Authorization: Bearer`）：

| 端点 | 返回 |
|---|---|
| `GET /api/health` | `{ok, time}` |
| `GET /api/config` | `{api_version, token_required, limits, arms, engine, engines, default_engine, repo_commit, data}` |
| `GET /api/milestones` | `{statuses, items[], note, repo_commit}`；item = `{id,title,status,updated,commit,note,sources[]}` |
| `GET /api/map` | `{w,h,barrier_cols[],cells[]}`；cell = `{i,row,col,passable,region,neighbors[]}` |
| `GET /api/runs` | `{runs[], active}` |
| `GET /api/runs/{id}` | 单条 run，**多一个 `meta`** 字段（可能是 `null`，见 §4） |
| `GET /api/runs/{id}/series` | `{run_id, series[]}`，元素 = `{t, agg, year, cum, integrity, events}`（`events` 是**当年事件条数**，不是列表） |
| `GET /api/runs/{id}/year/{t}` | 某一年的完整记录，见下 |
| `GET /api/runs/{id}/band/{band_id}` | 某个群体的历史卷宗；**obs-1.6 起支持 `?at_year=N`**，只用第 0..N 年的记录 |
| `GET /api/runs/{id}/relations` | **obs-1.6 新增**：这次运行里真实发生过的援助往来汇总；同样支持 `?at_year=N` |

写接口（令牌 + 每 IP 每分钟 `write_rate_per_min` 次）：

| 端点 | 说明 |
|---|---|
| `POST /api/runs` | body `{seed, years, sigma_m, move_mort_m, arm, label, engine, share_m, aid_m, recip_m}`，数值全部**严格整数**（`1.5`/`true` 会被 422 拒绝）；成功 `{run_id, status:"queued"}` |
| `POST /api/runs/{id}/cancel` | 请求取消。有界收尾：正常进程在年边界自己停，卡住的在协作窗口用完后被停止，身份不明的**绝不发信号**。见 §6 |
| `DELETE /api/runs/{id}` | 删除非预生成、非进行中的运行 |

**状态码约定**：`400` 参数越界（含业务校验）、`422` 类型不对（pydantic）、`401` 缺令牌、
`403` 非本机写、`404` 运行或年份不存在、`409` 槽被占 / 条数或容量到上限 / 状态不允许、`429` 写请求超频。

### run 行的字段（`/api/runs` 与 `/api/runs/{id}` 一致）

```
run_id label kind status created_at started_at finished_at
seed years sigma_m move_mort_m share_m aid_m recip_m engine arm
years_done years_recorded cancel_requested cancel_requested_at cancel_note cancel
engine_sha256 engine_path baseline_commit repo_commit model_run_id full_digest
error pid
```

- `status` ∈ `queued | running | done | failed | interrupted | canceled`。
  **终态（done/failed/interrupted/canceled）不会再变**，UI 可以放心缓存。
- `years_done` 是台账里的进度；**`years_recorded` 是真正写完整、可以回放的年数**。
  时间轴的上界请用 `years_recorded`，不要用 `years_done`。
- `kind = "preset"` 表示预生成案例，UI 应当标注出来，不冒充实时任务。
- `error` 是人类可读文本，**可能包含用户输入或路径，展示前必须转义或用 textContent**。
- `label` 由用户填写，服务端**原样保存不做转义**，同样按纯文本展示。
- `pid` 仅供诊断，UI 不必显示。
- **取消相关（obs-1.7 新增）**：`cancel` 是个对象
  `{requested, stage, requested_at, seconds_left, note}`，`stage` ∈
  `none | cooperative | escalated | finished`；`cancel_note` 是同一件事的人话版本
  （**用户输入无关，但仍按纯文本展示**）。`cancel_requested` / `cancel_requested_at`
  是原始字段，语义不变。详见 §6。
- **`engine`（obs-1.2 新增）** ∈ `exp03 | exp04 | exp05 | exp06`，旧记录默认 `exp03`。
  `share_m` 对 `exp04` 起有意义，`aid_m` 对 `exp05` 起有意义，`recip_m` 只对 `exp06` 有意义；
  引擎没有的参数传非 0 会被 400 拒绝。**不要把引擎名和参数写死**，读 `engines` 里的
  `engine_params` 决定给哪些控件。
  可用引擎与各自的参数列表由 `GET /api/config` 的 `engines` 给出，
  形如 `{exp04: {engine_label, engine_params:["sigma_m","move_mort_m","share_m"], ...}}`
  —— **前端据此决定给哪些参数控件，不要把引擎名和参数写死。**

### 年份记录（`/year/{t}`）

```
t, stock[64], bands[], cum{}, year{}, agg{pop,bands,stock_total,store_total},
integrity{conservation_error,population_identity_error,state_hash}, events[]
```

- `cum` 是开局到当年的累计，`year` 是**当年增量**，两者键名相同（都来自账本差值）：
  `births_cum deaths_demo_cum mig_deaths_cum mig_total mig_regret need_cum deficit_cum
  personyear_cum stale_sum inflow out_eat out_spoil out_move out_lost prop_total
  prop_conflict clim_nominal clim_planned clim_credited clim_capped`
  （键名保留 `_cum` 后缀是历史原因：在 `year` 里它是当年增量，不是累计。）
- `bands[]` 元素 = `{id, name, cell, size, store, macc, bacc, dacc, mem}`；
  `mem` 是 `{格号: [记得的存量, 时间戳]}`。
- `events[]` 元素 = `{type, source, text, ...}`，`type ∈ split | migrate | extinct | share`；
  `source` 写明来自模型日志还是状态差分；`migrate` 还带 `unrecorded` 说明哪些细节无法还原。
- **`share` 事件（obs-1.2 新增，只有 `engine=exp04` 的运行才有）**：
  `{type:"share", donor, receiver, cell, mem_cell, value, memt, source, text, band}`
  —— 即"**哪一年（记录所在的 `t`）、哪个群体（`donor`）向谁（`receiver`）、
  在哪一格（`cell`）、传了对哪个格（`mem_cell`）的记忆、值是多少（`value` kcal）、
  那条记忆原本记于哪一年（`memt`，**照抄来源、不刷新**）"。
  `donor`/`receiver`/`band` 都是**字符串** id。`text` 是已经拼好的中文说明，可直接显示。
- **`aid` 事件（obs-1.3 新增，只有 `engine=exp05` 的运行才有）**：
  `{type:"aid", donor, receiver, cell, kcal, person_years, source, text, band}`
  —— 即"**第 X 年（记录所在的 `t`）、哪个群体（`donor`）向哪个群体（`receiver`）、
  在哪一格（`cell`）、援助了多少食物（`kcal`，整数；`person_years = kcal / 730000` 是换算值）**"。
  `text` 是拼好的中文说明，可直接显示；**数量必须带单位**，两种单位都给了。
- **`aid` 事件在 obs-1.4 多两个字段（只有 `exp06` 会出现非默认值）**：
  `phase ∈ "recip" | "normal"`（是否走的优先回助阶段）、`repay`（布尔：供给方**记得**对方帮过自己）。
  **这两个不是一回事，也都不等于"优先规则改变了分配"**：`RECIP_M=0` 时 `repay` 照样会出现，
  那是碰巧。要判断规则是否真的改变了分配，看 `recip.changed`。
- **群体记录在 `exp06` 多一个 `aid_memory`**：`{援助者id字符串: {kcal, last_year}}`
  —— "谁以前帮过我、累计多少、最近哪一年"。**只由实际转移累加**，来源是模型状态 `band['amem']`。
- **`recip`（obs-1.4 新增，只有 `engine=exp06`）**：年份记录多一个顶层段
  `{budget, kcal, transfers, changed, repay_kcal, repay_transfers,
    cum_kcal, cum_changed, cum_repay_transfers, memory_entries, memory_dropped}`，
  前几项是**当年增量**。`changed` = 同一份援助前状态下把 `RECIP_M` 换成 0 再算一遍、
  结果不同的"格×年"次数。校验值在 `integrity.aid_memory_error`（应恒为 0）。
- **`aid`（obs-1.3 新增）**：年份记录多一个顶层段
  `{events, transfers, kcal, donors, receivers, supply, demand, cum_kcal, cum_events, cum_transfers}`。
  **`events` 与 `transfers` 是两个计数，不能混为一谈**：
  `events` = 当年发生过援助的"格 × 年"活动次数（一次多人援助算 1），
  `transfers` = 逐笔转移的笔数（一个供给方给一个接收方算 1 笔）。
  `supply` / `demand` 是当年参与格里的可援助预算与缺口合计（kcal）。
  校验值在 `integrity.aid_ledger_error`（应恒为 0）。
- **`share`（obs-1.2 新增，同上）**：年份记录多一个顶层段
  `{groups, participants, received, adopted, rejected, decision_changed, cum_adopted}`，
  前六项是**当年增量**，`cum_adopted` 是累计采纳数。恒等式 `received = adopted + rejected`，
  校验值在 `integrity.share_ledger_error`（应恒为 0）。
  **`exp03` 的记录里没有 `share` 段，也没有 `share` 事件；前端必须容忍缺席。**

**累计事件数**：`/series` 每个元素的 `events` 是当年条数，UI 端前缀求和即可得到累计，
**不需要后台加新字段**（要真加，走 §5 的流程）。

---

## 3. 前端测试钩子（UI 分支改版时请保留或按需重议）

后台有一套浏览器回归（`observer/tests/web/selftest.html`，用受控 `fetch` 桩驱动**真实的**
`observer/web/app.js`），它依赖两件事：

1. `window.__obs = { S, api, esc, ykey, openRun, gotoYear, selectBand, refresh, renderRuns, boot }`
   —— 只读的测试钩子；页面在 `window.__OBS_MANUAL_BOOT__ === true` 时**不自动 boot**。
2. 这些 DOM id 存在且含义不变：
   `#statusline #side-now #side-year #scrub-year #runtable #map #side-sel`。

**UI 改版后如果钩子没了，回归会如实报告“无法驱动”，由 `run_tests.py` 记为
未覆盖（UNCOVERED），不会假装通过、也不会把你的分支判红。** 想继续保有这层保护，
就在新前端里保留上面两条；结构变了就在这份文件里改约定，我同步改自检页。

自检页跑法：启动服务后打开 <http://127.0.0.1:8765/selftest/selftest.html>。

---

## 4. 口径约定（两边必须一致，避免各写一套）

1. **单位**：资源、储粮、需求的原始单位是 kcal 整数；人年口粮 = kcal ÷ 730000。
   展示时两个都标，不要只给换算值。
2. **当年值与累计值分列**，当年出生/死亡/迁移一律取账本差值，**不得用人口净变化冒充**。
3. **分母为 0 显示“不适用”**，不写 0%（当年迁移 0 次时的误判率、第 0 年的缺粮率）。
4. **实体 id 是字符串**（64 位，JS number 装不下），不要 `parseInt`。
5. `meta` 可能是 `null`：新运行的工作进程还没落盘，或文件损坏被判为不可读。
   UI 应当容忍，并在后续轮询里自动补取（现有 `refresh()` 已这么做）。
6. 事件只有两个来源，展示时必须带出 `source`；还原不了的写“未记录”，
   **不得用任何模型/LLM 补编事件、动机或因果**。
7. 回放只读已保存记录，**不触发计算**；改参数等于新建运行，不修改已有运行。

---

## 5. 变更流程

1. 需要新增或改字段 → 在这份文件里写清：字段名、类型、含义、是否可为空、谁来产出。
2. 后台实现 → `api_version` +0.1 → 在 `observer/TESTS.txt` 里留下回归结果。
3. UI 适配 → 双方分支完成后**统一集成验收**：
   `python3 observer/run_tests.py`（后台 185 项 + 浏览器回归）+ 页面实跑 + 截图。
4. 冲突时以这份文件为准；没写进来的字段一律视为**不保证**，不要依赖。

---

## 6. obs-1.7 的变化（取消的可靠性）

以前取消只设一个标志，工作进程在**年边界**才读它。进程活着却卡在某一步时，
那个标志永远读不到，唯一的任务槽就再也放不出来 —— 只能重启服务。

### 6.1 `POST /api/runs/{id}/cancel`

请求体为空。返回：

```json
{"ok": true, "run_id": "…", "status": "running",
 "cancel": {"requested": true, "stage": "cooperative",
            "requested_at": 1789201075.0, "seconds_left": 15.0, "note": "…"},
 "note": "已请求取消：工作进程会在当前这一年算完后自己停下；若它卡住，最多 15 秒后会被强制停止。已完整保存的年份都留着。"}
```

`ok` 与 `note` 是 obs-1.6 就有的字段，语义不变；`run_id` / `status` / `cancel` 是新增的。
非 `queued`/`running` 的运行仍然回 `409`。

### 6.2 三条收尾路径（都不猜）

| 工作进程的探测结果 | 做什么 |
|---|---|
| 确认是本次运行的活进程（`ps` 里能看到 `observer.worker` 和这个 run_id） | 先给 `CANCEL_GRACE_SEC` 秒**协作窗口**，让它算完当前这一年自己停（写 `canceled`）；窗口用完还在，说明它卡住了，这时才 SIGTERM → SIGKILL |
| 确认已经不在 | 取消请求没人会读到，直接判 `canceled` |
| **查不到**（`ps` 超时 / 权限不足 / pid 可能被复用） | **一个信号都不发**，只写一句人话说明，下一轮再看 |

- `CANCEL_GRACE_SEC` 默认 15 秒，环境变量 `OBSERVER_CANCEL_GRACE` 可调。
- **只有用户明确按过取消才会走到这里。** 没有取消请求时，这条路上没有任何
  "多久没进度就停掉它"的判据 —— 一个算得慢的正常任务永远不会被动。
- 收尾时间不依赖页面刷不刷新：取消请求会安排**一次性**的到点检查
  （没有轮询线程、没有后台监控）。页面的 `/api/runs` 轮询也会顺手走一遍同一个函数。

### 6.3 保证与不保证

- **已完整写入的年份一年不少地留着**，`years_recorded` 仍是可回放年数的上界；
  被强制停止时写到一半的那一年**不算数**（只认完整记录，与 obs-1.0 的口径一致）。
- **终态不回退**：`done` / `failed` / `interrupted` / `canceled` 一旦写下就不再变。
- **竞态不覆盖赢家**：工作进程抢先写完 `done` 的那一刻即使正在被停止，收尾写入也匹配不到行，
  记录保持 `done`；反过来取消先落地时，迟到的工作进程也改不回 `done`（写入围栏）。
- **不保证跨进程续跑**：取消就是结束，继续推进请新建运行。
- 取消**不删除**任何已保存的记录；`DELETE /api/runs/{id}` 才是删除。


## 7. obs-1.6 的变化（历史卷宗与按年关系网）

**实操版交接说明（真实 curl / 真实响应 / 截至 83、124、125 年与全档案的差异）见
[`OBS-01-HANDOFF-HISTORY.md`](OBS-01-HANDOFF-HISTORY.md)。**

起因是回放时的两处真实错位：回放到第 124 年，群体档案里已经列着第 125 / 131 年的迁移；
`aid_memory.last_year` 与 `basis.remembered_last_year` 是**引擎内部 tick**，
记录里写第 83 年的那笔援助，它们显示成第 82 年。

### 6.1 `GET /api/runs/{id}/band/{band_id}?at_year=N`

`at_year` **可选**。省略 = 全档案，行为与 obs-1.5 完全一致（老调用不用改）。
带上 `N` 时，**只读第 0..N 年已保存的记录**：第 N 年之后的迁移、分裂、消失、援助一律不出现。

| 字段 | 类型 | 含义 |
|---|---|---|
| `history_scope` | 对象 | `{mode:"full"\|"as_of_year", at_year, years_recorded, note}`，口径写在响应里 |
| `alive_at_year` | 布尔 | 截断那一年这个群体是否还在记录里（全档案时 = 最后一年是否还在） |
| `state_at_year` | 对象或 `null` | `{year, cell, size, store}`，截断年它最后一次被记到的样子 |
| `aid_given` / `aid_received` | 对象 | `{kcal, transfers, events[]}`；`events[]` 元素带 `{id, year, 对方 id, kcal, phase, repay}` |
| `aid_memory` | 对象或 `null` | 键是**施援方 id 字符串**；值见 6.3。旧引擎没有这一段时为 `null` |

原有字段（`trajectory` / `sizes` / `children` / `born_at` / `extinct_at` / `parent` / `origin`）
语义不变，只是按 `at_year` 截断。

**错误响应**：`at_year` 越界或为负 → `400`，提示里写明这次运行**实际存了多少年**
（例：`at_year=999 越界：这次运行已保存 0..150 年`）；非整数 → `422`；
群体在该年之前还没出生 → `404`（不返回空壳档案）。

### 6.2 `GET /api/runs/{id}/relations?at_year=N`

只把**已保存的逐笔援助事件**聚合起来。这里**没有**盟友、国家、联盟这类东西，
只有"谁给过谁多少 kcal"。

```
{
  "run_id": "...", "history_scope": {...}, "as_of_record_year": 83,
  "nodes": [{"id": "字符串", "name": "...", "alive_at_year": true,
             "cell": 1, "last_seen_year": 83}],
  "edges": [{"donor": "...", "receiver": "...", "kcal": 6457, "transfers": 1,
             "last_year": 83, "last_event_id": "t83-aid-3",
             "phase_counts": {"recip": 0, "normal": 1},
             "repay_transfers": 0, "event_ids": ["t83-aid-3"]}],
  "totals": {"nodes": 9, "edges": 2, "transfers": 2, "kcal": 423541},
  "diagnostics": {"recip_changed_cellyears": 2, "note": "..."},
  "source": "..."
}
```

- 边是**有向的**：A→B 与 B→A 是两条，不合并成一条无向关系。
- `last_year` / `event_ids` 用的是**事件年份**（与 `/year/{t}` 的 `t` 同一口径），可直接跳转。
- **`recip.changed` 不属于任何一条边。** 它是"格 × 年"的诊断计数，只在 `diagnostics`
  里给一个运行级合计；也**不能**用 `repay_transfers` 代替它 —— `RECIP_M=0` 时照样会发生回助，
  那是碰巧撞上，不是优先机制起作用。
- 旧引擎（`exp03`/`exp04`）的运行照常返回 `200`，`edges` 为空，`totals` 全 0，不报错也不编造。

### 6.3 展示年份 vs 内部 tick（`aid_memory` 与 `basis`）

`last_year` / `remembered_last_year` 的**原语义保持不变**：引擎内部 tick，比记录年份小 1。
不要拿它显示。新增的展示字段来自**真实事件记录**：

| 字段 | 含义 |
|---|---|
| `last_year_display` / `remembered_last_year_display` | 该笔援助在记录里的年份，可直接拿去跳 `/year/{t}` |
| `last_event_id` / `remembered_last_event_id` | 对应事件的 `id`，可在那一年的 `events[]` 里找到 |
| `display_source` / `year_note` | 这个年份是从哪来的；找不到出处时写"未记录：…"，**不猜** |

找不到出处的情形是真实存在的：构造场景里预置的历史、或本次运行记录之外发生的援助。
这时 `last_year_display` 与 `last_event_id` 一律为 `null`，不填一个看起来合理的年份。
带 `at_year=N` 时，展示年份由第 0..N 年的事件推出，**不会**指向第 N 年之后的事件。

### 6.4 其他

- 预置案例 `preset-exp06-recip0` / `preset-exp06-recip1000` 的记录已按新记录层重新生成。
  模型结果未变：`model_run_id` 与 `full_digest` 与重算前**逐字节相同**，变的只有记录层字段。
- 全部为新增字段，没有删改任何现有字段；`at_year` 省略时响应与 obs-1.5 一致。


## 8. obs-1.5 的变化（供游戏界面直接使用的数据）

**实操版交接说明（真实请求 / 真实响应 / 可回放的运行编号与年份）见
[`OBS-01-HANDOFF-EXP06.md`](OBS-01-HANDOFF-EXP06.md)。**

| 变化 | 兼容性 |
|---|---|
| 每个事件新增 `id`（`t<年>-<类型>-<当年序号>`，同一次运行里唯一可复现）与 `year` | **新增字段**；老记录在读取时按同一规则补齐 |
| 回助事件新增 `basis`：`{remembered_kcal, remembered_last_year, prior_events[], why, source}` | **新增字段**；只有 `repay=true` 的事件才有 |
| `aid` 事件新增 `unrecorded`（动机/路线/因果未记录） | 新增字段 |
| `recip` 段新增 `compare[]`：同一份援助前状态下开/关优先各算一遍的**逐笔**与**逐对总额** | 新增字段；只有 `engine=exp06` |
| `GET /api/config` 的每个引擎新增 `params[]`：`{name, label, unit, min, max, default, note}` | **新增字段**；原有 `engine_params`（只有名字）保留不变 |
| `GET /api/runs/{id}` 新增 `params_used[]`（带标签与单位的实际取值）与 `engine_label` | 新增字段 |
| 预置案例新增两条：`preset-exp06-recip0` / `preset-exp06-recip1000`（**自然演化**，非构造） | 新增数据 |

**`recip.changed` 的判据本批修正**：从"逐笔转移列表不同"改为"**逐对群体总额不同**"——
同一对群体、同样总额、只是被拆成优先 + 普通两笔，不再算作分配改变。
7 种子 300 年下计数由 118 降为 47（`SIGMA=0, RECIP=1000`）。请用 `changed`，不要自己数笔数。

## 9. obs-1.4 的变化（EXP-06 接入）

| 变化 | 兼容性 |
|---|---|
| `engine` 多一个取值 `exp06`；run 行新增 `recip_m` | **新增**；旧记录 `recip_m = 0` |
| `POST /api/runs` 新增可选 `recip_m` | **可选**，不传等于 0 |
| `aid` 事件新增 `phase` / `repay` | **新增字段**；exp05 的事件里 `phase` 恒为 `normal`、`repay` 恒为 `false` |
| 年份记录新增 `recip` 段；群体记录新增 `aid_memory` | **只在 `engine=exp06`**；其它引擎完全不变 |
| `integrity` 新增 `aid_memory_error` | 只在 exp06 出现 |

没有任何字段被删除或改名。**建议 UI 这样用**：`exp06` 的运行可以显示两样新东西——
①「关系」：某个群体的 `aid_memory`（谁以前帮过我、多少、哪一年）；
②「这次谁回助了谁」：`aid` 事件里 `repay=true` 的那些（`text` 已带"回助 ·"前缀）。
**务必把 `repay`（含碰巧）与 `recip.changed`（规则真的改变了分配）分开显示**，不要合并成一个"互惠"指标。

现状：`repay=true` 的事件在你当前的前端里已经能正常渲染出来（截图
`observer/docs/screenshots/12-recip-aid.jpg`，第 128 年那条）。还没有做的是
`aid_memory` 的关系展示与 `recip` 段的年度统计 —— 这两块的数据都已经在接口里了。

## 10. obs-1.3 的变化（EXP-05 接入）

| 变化 | 兼容性 |
|---|---|
| `engine` 多一个取值 `exp05`；run 行新增 `aid_m` | **新增**；旧记录 `aid_m = 0` |
| `POST /api/runs` 新增可选 `aid_m` | **可选**，不传等于 0，旧调用不受影响 |
| 年份记录新增 `aid` 段与 `aid` 事件 | **只在 `engine=exp05` 时出现**；exp03/exp04 完全不变 |
| `integrity` 新增 `aid_ledger_error` | 只在 exp05 出现 |

没有任何字段被删除或改名。**建议 UI 这样用**：按 `run.engine` 决定显示哪些栏；
援助列表直接渲染 `text`，要做统计就用 `aid` 段，**注意把"援助活动次数"和"转移笔数"
分开显示**，不要相加也不要互相替代。

**给 UI 分支的两条现状说明**（后台不改前端，供你按自己的节奏处理）：

1. obs-1.3 的 `type:"aid"` 事件已经能在现有事件列表里渲染出来（截图
   `observer/docs/screenshots/11-aid-events.jpg`），但类型标签目前显示的是原始的 `aid`，
   事件筛选条里也还没有"援助"这一档 —— 你那份 `迁移 / 分裂 / 群体消失 / 信息交换` 的标签表
   加一项即可。
2. `showTab()` 遇到未登记的 tab 名（例如旧链接里的 `#tab=events`）会把所有分区都隐藏，
   页面变成空白。给它一个兜底（未知就回到 `world`）会更稳。这两条都不影响数据正确性。

## 11. obs-1.2 的变化（EXP-04 接入）

| 变化 | 兼容性 |
|---|---|
| run 行新增 `engine`、`share_m` | **新增字段**；旧记录默认 `exp03` / `0` |
| `POST /api/runs` 新增可选 `engine`、`share_m` | **可选**，不传等于 `exp03` / `0`，旧调用不受影响 |
| `GET /api/config` 新增 `engines`、`default_engine` | 新增字段，原有 `engine`（默认引擎）保留不变 |
| 年份记录新增 `share` 段与 `share` 事件 | **只在 `engine=exp04` 时出现**；`exp03` 完全不变 |
| `integrity` 新增 `share_ledger_error` | 只在 exp04 出现 |

没有任何字段被删除或改名。**建议 UI 这样用**：按 `run.engine` 决定要不要显示"信息交换"一栏；
事件列表直接渲染 `text` + `source` 即可，要做更细的展示再取结构化字段。

**一处已知的显示错位（留给 UI 分支处理，后台不擅自改前端）**：现有页面顶栏的"模型"读的是
`/api/config` 里的 `engine`（**默认引擎**），所以打开一次 `exp04` 的运行时，顶栏仍写着
`exp03/verify3.py`。正确的来源是该次运行自己的 `run.engine` / `run.engine_path` /
`run.engine_sha256`（早就在 run 行里，obs-1.0 就有）。

## 12. 更早（obs-1.1）的变化

| 变化 | 兼容性 |
|---|---|
| `GET /api/config` 新增 `api_version` | **新增字段，向后兼容** |
| 任务槽会自动回收“没人在算”的记录（见 `observer/README.md`） | 行为变化，字段不变：这类记录的 `status` 变成 `interrupted`，`error` 写明原因 |
| `meta` 读取容错：损坏时返回 `null` 而不是 500 | 行为变化，字段不变 |
| 自检页从 `observer/web/` 移到 `observer/tests/web/`，挂在 `/selftest` | `observer/web/` 从此完全归 UI 分支 |

没有任何字段被删除或改名。
