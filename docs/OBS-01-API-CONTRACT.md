# OBS-01 接口约定（后台 ↔ UI 分支）

**这份文件是两边的唯一约定来源。** 后台（Python）与 UI 分支（`observer/web/`）分头改，
靠它对齐；不各自实现一套数据格式。

契约版本 **`obs-1.2`**，由 `GET /api/config` 的 `api_version` 字段给出。
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
| `GET /api/runs/{id}/band/{band_id}` | 某个群体的可记录轨迹 |

写接口（令牌 + 每 IP 每分钟 `write_rate_per_min` 次）：

| 端点 | 说明 |
|---|---|
| `POST /api/runs` | body `{seed, years, sigma_m, move_mort_m, arm, label, engine, share_m}`，数值全部**严格整数**（`1.5`/`true` 会被 422 拒绝）；成功 `{run_id, status:"queued"}` |
| `POST /api/runs/{id}/cancel` | 请求取消；若工作进程已不在，直接回收任务槽并标中断 |
| `DELETE /api/runs/{id}` | 删除非预生成、非进行中的运行 |

**状态码约定**：`400` 参数越界（含业务校验）、`422` 类型不对（pydantic）、`401` 缺令牌、
`403` 非本机写、`404` 运行或年份不存在、`409` 槽被占 / 条数或容量到上限 / 状态不允许、`429` 写请求超频。

### run 行的字段（`/api/runs` 与 `/api/runs/{id}` 一致）

```
run_id label kind status created_at started_at finished_at
seed years sigma_m move_mort_m share_m engine arm
years_done years_recorded cancel_requested
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
- **`engine`（obs-1.2 新增）** ∈ `exp03 | exp04`，旧记录默认 `exp03`。
  `share_m` 只对 `exp04` 有意义，`exp03` 的运行恒为 0（提交非 0 会被 400 拒绝）。
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
   `python3 observer/run_tests.py`（后台 71 项 + 浏览器回归）+ 页面实跑 + 截图。
4. 冲突时以这份文件为准；没写进来的字段一律视为**不保证**，不要依赖。

---

## 6. obs-1.2 的变化（EXP-04 接入）

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

## 7. 上一轮（obs-1.1）的变化

| 变化 | 兼容性 |
|---|---|
| `GET /api/config` 新增 `api_version` | **新增字段，向后兼容** |
| 任务槽会自动回收“没人在算”的记录（见 `observer/README.md`） | 行为变化，字段不变：这类记录的 `status` 变成 `interrupted`，`error` 写明原因 |
| `meta` 读取容错：损坏时返回 `null` 而不是 500 | 行为变化，字段不变 |
| 自检页从 `observer/web/` 移到 `observer/tests/web/`，挂在 `/selftest` | `observer/web/` 从此完全归 UI 分支 |

没有任何字段被删除或改名。
