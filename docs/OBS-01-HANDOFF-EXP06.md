# 交接说明 · EXP-06 的后台数据（给 UI 分支）

契约版本 **`obs-1.5`**（`GET /api/config` 的 `api_version`）。
字段定义在 [`OBS-01-API-CONTRACT.md`](OBS-01-API-CONTRACT.md)，这份是**拿了就能接**的实操版：
真实请求、真实响应、可直接回放的运行编号与年份。

**全部字段都向后兼容**：旧运行没有新字段时照常读，不要假定字段一定存在。
所有 `text` 都是**真实数据套模板**拼出来的，没有任何 LLM 编故事。

---

## 0. 两条可直接回放的对照运行（随仓库分发，无需自己跑）

| 运行编号 | 含义 | 关键年份 |
|---|---|---|
| `preset-exp06-recip0` | **关闭**优先回助（`RECIP_M=0`） | 首次援助 **第 83 年**；回助 3 笔，首次 **第 124 年**；**分配改变 0 次** |
| `preset-exp06-recip1000` | **开启**优先回助（`RECIP_M=1000`） | 首次援助 **第 83 年**；回助 6 笔，首次 **第 124 年**；**分配改变 2 次，首次第 125 年** |

两条**只差 `RECIP_M`**，其余完全相同（`seed=31337`、`SIGMA_M=0`、`MOVE_MORT_M=50`、
`SHARE_M=1000`、`AID_M=1000`、150 年、记忆臂），都是**自然演化**，不是人工构造的测试案例。
（人工构造的场景只存在于 `exp06/run_tests.py`，**不会**进观察台，免得被当成自然演化。）

这组正好说明本轮最关键的一个区分：**两条都有回助**，但只有开启的那条**改变了分配**。

```bash
# 本地启动后直接看
open "http://127.0.0.1:8765/#run=preset-exp06-recip1000&t=125"
```

---

## 1. 引擎能力表：前端不用再猜参数

```bash
curl -s localhost:8765/api/config | jq '.engines.exp06'
```

```jsonc
{
  "engine": "exp06",
  "engine_label": "EXP-06 援助记忆与优先回助",
  "engine_params": ["sigma_m", "move_mort_m", "share_m", "aid_m", "recip_m"],
  "params": [                       // obs-1.5 新增：范围 / 默认值 / 单位 / 含义
    {"name": "seed",        "min": 0, "max": 2147483647, "default": 0,   "unit": "整数",       "label": "随机种子"},
    {"name": "years",       "min": 1, "max": 300,        "default": 120, "unit": "年",         "label": "模拟年数"},
    {"name": "sigma_m",     "min": 0, "max": 1000,       "default": 0,   "unit": "‰（千分之一）", "label": "资源再生年际波动"},
    {"name": "move_mort_m", "min": 0, "max": 1000,       "default": 0,   "unit": "‰（千分之一）", "label": "迁移死亡强度"},
    {"name": "share_m",     "min": 0, "max": 1000,       "default": 0,   "unit": "‰（千分之一）", "label": "同格信息交换的参与概率"},
    {"name": "aid_m",       "min": 0, "max": 1000,       "default": 0,   "unit": "‰（千分之一）", "label": "供给方愿意拿出的可援助余粮比例"},
    {"name": "recip_m",     "min": 0, "max": 1000,       "default": 0,   "unit": "‰（千分之一）", "label": "优先回助的预算比例"}
  ]
}
```

**照这张表渲染控件即可**：`min/max` 的权威来源是引擎常量，以后再加 EXP 也不用改前端。
每个引擎支持哪些参数看 `engine_params`；传了引擎不支持的参数会被 **400** 拒绝。

## 2. 发起一次 EXP-06 运行

```bash
curl -s -X POST localhost:8765/api/runs -H 'Content-Type: application/json' -d '{
  "seed": 31337, "years": 150, "sigma_m": 0, "move_mort_m": 50,
  "engine": "exp06", "share_m": 1000, "aid_m": 1000, "recip_m": 1000,
  "label": "开启优先回助"
}'
# -> {"run_id":"<12 位十六进制>","status":"queued"}
```

数值全部**严格整数**（`1.5` / `true` 会被 422 拒绝）；越界 400；已有任务在跑 409；写请求超频 429。

## 3. 这次运行到底用了什么：引擎、参数、代码版本、状态

```bash
curl -s localhost:8765/api/runs/preset-exp06-recip1000
```

```jsonc
{
  "run_id": "preset-exp06-recip1000",
  "kind": "preset",                 // preset = 预生成案例，不是正在跑的任务
  "status": "done",                 // queued|running|done|failed|interrupted|canceled
  "engine": "exp06",
  "engine_label": "EXP-06 援助记忆与优先回助",
  "engine_sha256": "83cc083323d3f5ad4cf31446c8431be5100c147f4e7ced47c6dc58aee64e085c",
  "baseline_commit": "6b6af4f",
  "model_run_id": "b10e462951226dc74048be9c7a7b5694",   // 世界身份（种子+初始禀赋+参数指纹）
  "years": 150, "years_recorded": 150,                   // 时间轴上界用 years_recorded
  "params_used": [                                       // obs-1.5 新增：带标签与单位的实际取值
    {"name": "seed", "value": 31337, "unit": "整数", "min": 0, "max": 2147483647},
    {"name": "recip_m", "value": 1000, "unit": "‰（千分之一）", "min": 0, "max": 1000}
  ]
}
```

## 4. 回助事件：带稳定 id、来源，并**挂上作为依据的历史援助**

```bash
curl -s localhost:8765/api/runs/preset-exp06-recip1000/year/124 | jq '.events[] | select(.repay)'
```

```jsonc
{
  "id": "t124-aid-5",               // 稳定标识：同一次运行里唯一、可复现（年份-类型-当年序号）
  "year": 124,
  "type": "aid",
  "phase": "recip",                 // recip = 走的优先回助阶段；normal = 普通阶段
  "repay": true,                    // 供给方**记得**对方帮过自己
  "donor": "907731079216851761",    // 64 位 id 一律字符串，别 parseInt
  "receiver": "7567856178022945294",
  "cell": 0,
  "kcal": 6457,
  "person_years": 0.0088,           // = kcal / 730000，换算值
  "text": "回助 · 群体-0C98E8 向 群体-69066D 援助了 6457 kcal（0.01 人年口粮），地点在第 0 号格（优先回助阶段：供给方记得对方帮过自己）",
  "source": "模型日志 st['aid_log']",
  "unrecorded": "动机、路线与因果关系未记录：模型里没有这些量，不要为动画补编。",
  "basis": {                        // obs-1.5 新增：**可核实的依据**
    "why": "供给方的援助记忆里有接收方，且该记忆只由实际转移累加",
    "remembered_kcal": 6457,        // 援助前记住的累计量
    "remembered_last_year": 82,     // 最近一次受助的年份
    "prior_events": ["t83-aid-3"],  // 当初那几笔的事件 id，可直接跳转
    "source": "模型状态 band['amem'] 的援助前快照 + 本次运行的援助日志"
  }
}
```

**关系连线可以这样画**：`basis.prior_events` 里的 id 拿去 `year/<那一年>` 取回原事件，
`donor`/`receiver` 正好是反向的一对——这就是"以前谁帮过谁 → 这次谁回助了谁"的完整链条。

## 5. 分配对照：怎么证明"优先规则确实改变了分配"

**只凭双方以前有往来不能认定**（`RECIP_M=0` 的那条运行里也有 3 笔回助）。
判据是**同一份援助前状态下，开/关优先各算一遍，逐对群体的总额是否不同**：

```bash
curl -s localhost:8765/api/runs/preset-exp06-recip1000/year/125 | jq '.recip.compare[] | select(.changed)'
```

```jsonc
{
  "cell": 0,
  "changed": true,
  "with_totals":    [{"donor": "9077…", "receiver": "7567…", "kcal": 122601},
                     {"donor": "9077…", "receiver": "1043…", "kcal": 148776}],
  "without_totals": [{"donor": "9077…", "receiver": "7567…", "kcal": 119327},
                     {"donor": "9077…", "receiver": "1043…", "kcal": 152050}],
  "with_recip":    [ /* 逐笔，带 phase */ ],
  "without_recip": [ /* 逐笔 */ ]
}
```

读法：开启优先后，**旧伙伴 7567 多拿了 3274 kcal，另一家少拿同样多**。
同一年第 6 号格的那条 `changed: false` —— 开/关结果完全一样，如实标出来。

> **判据本批修正过**：最初比的是逐笔列表，于是"同一对群体、同样总额、只是拆成优先 + 普通两笔"
> 也被算成改变。现在比逐对总额，计数从 118 降到 47（`SIGMA=0, RECIP=1000`，7 种子 300 年）。
> 用 `changed` 就行，不要自己用 `with_recip` 的笔数去判断。

## 6. 年度读数与群体的援助历史

```bash
curl -s localhost:8765/api/runs/preset-exp06-recip1000/year/125 | jq '.recip | del(.compare)'
```

```jsonc
{
  "budget": 4042606,          // 当年走优先阶段的预算（kcal）
  "kcal": 6457,               // 当年优先阶段实际转移（kcal）
  "transfers": 1,             // 当年优先阶段笔数
  "changed": 1,               // 当年"分配确实被改变"的格数
  "repay_kcal": 122601, "repay_transfers": 2,     // 当年回助（含碰巧）
  "cum_kcal": 12914, "cum_changed": 1, "cum_repay_transfers": 4,   // 累计
  "memory_entries": 5,        // 当年在世群体的援助记忆条目总数
  "memory_dropped": 0         // 累计随群体消失而丢失的记忆条目
}
```

群体的援助历史在群体记录里（`year/<t>` 的 `bands[]`）：

```jsonc
{"id": "907731079216851761", "name": "群体-0C98E8",
 "aid_memory": {"7567856178022945294": {"kcal": 6457, "last_year": 82}}}
```

即"**谁帮助过我、累计多少食物、最近哪一年**"。**只由实际转移累加**，
不是好感度、不是债务、不是联盟。单位：`kcal`（1 人年口粮 = 730,000 kcal）。

`integrity.aid_memory_error` 恒为 0（在世记忆 + 随消失丢失 == 实际援助总量）。

## 7. 计数单位一览（别混用）

| 字段 | 单位 / 含义 |
|---|---|
| `aid.events` | **次**：发生过援助的"格 × 年"活动数，一次多人援助算 1 |
| `aid.transfers` | **笔**：一个供给方给一个接收方算 1 笔 |
| `recip.transfers` | **笔**：其中走优先阶段的 |
| `recip.repay_transfers` | **笔**：供给方记得对方帮过自己的（**含碰巧**，不代表规则起作用） |
| `recip.changed` | **次**：分配确实被改变的格数（**这才是规则起作用的证据**） |
| `*_kcal` / `kcal` | **kcal**，1 人年口粮 = 730,000 kcal；`person_years` 是换算值 |
| `aid_memory[*].kcal` | **kcal**：记住的累计受助量 |

## 8. 还没有的东西（别替它编）

- **动机、路线、因果**：模型里没有，事件的 `unrecorded` 已写明，不要为动画补编。
- **群体层的出生/死亡分项**：账本只记全局分项，`migrate` 事件的 `unrecorded` 已写明。
- **自然运行里没发生过的现象**：例如"带记忆的群体消失"（`memory_dropped` 恒为 0）——
  这条只在 `exp06/run_tests.py` 的构造场景里出现过，**不要**当成自然演化展示。
