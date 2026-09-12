# OBS-01 交接 · 历史卷宗与按年关系网（obs-1.6）

给 UI 分支的实操说明。字段定义以 [`OBS-01-API-CONTRACT.md` §6](OBS-01-API-CONTRACT.md) 为准，
这里只给**真实跑出来的请求与响应**。

下面所有输出都是在本机 `python3 -m uvicorn observer.app:app --port 8791` 上
用 `curl` 实跑的，取自预置案例 `preset-exp06-recip1000`（自然演化，150 年，非构造）。
**这是一条运行的记录，不要把它当成"文明的一般规律"往外推。**

---

## 1. 这次修了什么

| 你看到的问题 | 原因 | 现在怎么办 |
|---|---|---|
| 回放到第 124 年，群体档案里已经列着第 125 / 131 年的迁移 | `/band/{id}` 只返回终局全历史，没有"截至某年"的概念 | 加 `?at_year=124` |
| `aid_memory.last_year` / `basis.remembered_last_year` 把第 83 年的援助写成 82 | 这两个是**引擎内部 tick**，比记录年份小 1 | raw 字段语义不动，改用新增的 `last_year_display` / `last_event_id` |

`at_year` 省略时行为与 obs-1.5 完全一致，老调用不用改。

---

## 2. 同一个群体，三个时点（真实输出）

群体 `7567856178022945294`，就是你举的那个 125 / 131 年迁移的例子。

```
$ curl -s ".../api/runs/preset-exp06-recip1000/band/7567856178022945294?at_year=124"
 history_scope.mode = as_of_year   last_seen = 124
 trajectory: [[0,0],[72,1],[75,2],[79,1],[84,0]]
 aid_given: 4 笔 / aid_received: 1 笔

$ curl -s ".../band/7567856178022945294?at_year=125"
 history_scope.mode = as_of_year   last_seen = 125
 trajectory: [[0,0],[72,1],[75,2],[79,1],[84,0],[125,1]]
 aid_given: 4 笔 / aid_received: 2 笔

$ curl -s ".../band/7567856178022945294"          # 省略 = 全档案
 history_scope.mode = full         last_seen = 150
 trajectory: [[0,0],[72,1],[75,2],[79,1],[84,0],[125,1],[131,0]]
 aid_given: 4 笔 / aid_received: 3 笔
```

第 124 年那一条里 **`[125,1]` 和 `[131,0]` 都不在**；`at_year=125` 正好含第 125 年那一步、
不含第 131 年。`history_scope` 直接写在响应里，可以拿去显示"你正在看截至第 N 年的档案"。

完整响应的头部长这样（其余字段见契约 §6.1）：

```json
{
 "id": "7567856178022945294", "name": "群体-69066D",
 "history_scope": {"mode": "as_of_year", "at_year": 124, "years_recorded": 150,
                   "note": "只用第 0..124 年已保存的记录；之后发生的出生/迁移/分裂/消失一律不计入"},
 "first_seen": 0, "last_seen": 124, "alive_at_year": true,
 "state_at_year": {"year": 124, "cell": 0, "size": 20, "store": 0},
 "parent": null, "born_at": null, "extinct_at": null
}
```

---

## 3. 第 83 年那笔援助（raw 与展示分开）

```
$ curl -s ".../band/907731079216851761?at_year=83"
```
```json
{
 "id": "907731079216851761", "name": "群体-0C98E8", "alive_at_year": true,
 "state_at_year": {"year": 83, "cell": 1, "size": 17, "store": 0},
 "aid_memory": {
  "7567856178022945294": {
   "kcal": 6457,
   "last_year": 82,
   "last_year_display": 83,
   "last_event_id": "t83-aid-3",
   "display_source": "本次运行的援助事件 t83-aid-3"
  }
 },
 "aid_received": {"kcal": 6457, "transfers": 1, "events": [
   {"id": "t83-aid-3", "year": 83, "donor": "7567856178022945294",
    "kcal": 6457, "phase": "normal", "repay": false}]}
}
```

对上第 83 年的记录，确实是同一笔：

```
$ curl -s ".../year/83"
 {"id":"t83-aid-3","year":83,"donor":"7567856178022945294","receiver":"907731079216851761",
  "kcal":6457,"phase":"normal","repay":false}
```

**界面上一律用 `last_year_display` 显示、用 `last_event_id` 跳转**；`last_year`（= 82）保留原语义，
是引擎内部 tick，不要拿去显示。回助事件的 `basis` 里同样多了
`remembered_last_year_display` / `remembered_last_event_id`。

推不出出处时（构造场景预置的历史、或本次记录之外发生的援助），
这两个字段是 `null`、`display_source` 写"未记录：…"——**不会**给你一个猜出来的年份。

---

## 4. 援助关系汇总 `GET /api/runs/{id}/relations`

同一条运行，四个口径（真实数字）：

| 口径 | nodes | edges | transfers | kcal | recip_changed（格×年，诊断） |
|---|---|---|---|---|---|
| `at_year=83` | 9 | 2 | 2 | 423,541 | 0 |
| `at_year=124` | 12 | 5 | 9 | 7,461,820 | 0 |
| `at_year=125` | 12 | 5 | 11 | 10,878,620 | 1 |
| 全档案 | 12 | 6 | 19 | 24,803,624 | 2 |

一条边的完整样子：

```json
{"donor": "17485938190730297594", "receiver": "10929267446675359160",
 "kcal": 6290637, "transfers": 2, "last_year": 125, "last_event_id": "t125-aid-6",
 "phase_counts": {"recip": 0, "normal": 2}, "repay_transfers": 0,
 "event_ids": ["t117-aid-6", "t125-aid-6"]}
```

节点：`{"id": "10431967184297706310", "name": "群体-90C5CA", "alive_at_year": true,
"cell": 1, "last_seen_year": 125}`。

用它的时候请守住三条：

1. **边是有向的**，A→B 与 B→A 分开算，不要在界面上合成一条无向连线。
2. **不要叫它盟友 / 联盟 / 邦交。** 这里只有"谁在哪一年给过谁多少 kcal"，
   模型里没有任何结盟、承诺或敌我概念。
3. **`recip.changed` 不属于任何一条边。** 它是"格 × 年"的诊断计数，只在 `diagnostics`
   里给运行级合计；也**不要**用 `repay_transfers` 当它的替身 —— `RECIP_M=0` 时照样会发生回助，
   那是碰巧撞上，不是优先机制起了作用（对照案例 `preset-exp06-recip0` 里就有回助）。

`event_ids` 与 `last_event_id` 都能直接在 `/year/{t}` 的 `events[]` 里找到，可以做跳转。

---

## 5. 边界情况（都实跑过）

```
$ curl ".../band/7567856178022945294?at_year=999"
HTTP 400  {"detail":"at_year=999 越界：这次运行已保存 0..150 年"}

$ curl ".../band/7567856178022945294?at_year=abc"
HTTP 422

$ curl ".../band/15560402854292026230?at_year=67"     # 这个群体第 68 年才分裂出来
HTTP 404  {"detail":"截至该年份的记录里没有这个群体"}

$ curl ".../api/runs/preset-s4242-sig400-mort50/relations?at_year=50"   # exp03，没有援助机制
HTTP 200  {"totals": {"nodes": 6, "edges": 0, "transfers": 0, "kcal": 0}, "edges": []}

$ curl ".../api/runs/preset-s4242-sig400-mort50/band/<id>?at_year=50"
HTTP 200  {"aid_memory": null, "aid_given": {"kcal":0,"transfers":0,"events":[]}, "last_seen": 50}
```

旧引擎的运行**不会**报错，也**不会**编一个空关系网出来充数 —— 边就是 0。

---

## 6. 需要你注意的

- 实体 id 仍是 **64 位字符串**（例：`18446744073709551557`），`parseInt` 会丢精度。
- 这两个端点都是**只读**的：不触发计算、不改已保存记录（测试 O28v 比对了文件哈希与台账）。
- 预置案例 `preset-exp06-recip0` / `preset-exp06-recip1000` 的 `years.jsonl` 已按新记录层重新生成。
  模型结果没变：`model_run_id` 与 `full_digest` 与重算前完全相同，变的只有记录层新增字段。
- 这份文件里的所有数字都来自**这一条运行**。别据此推断"文明一般会怎样"——
  同格援助本身在 EXP-05/06 的 42 次扫描里并没有带来人口上的整体改善。
