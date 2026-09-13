# 续演接口约定（C_CONT_01）

同一引擎、同一配置的真实世界**保存之后继续计算**。

这不是"把新建运行的 `years` 改成 600"，也不是"从第 0 年重跑再假装续演"。
子运行的第 0..C 年是**父运行的原始字节**，第 C+1 年起才是这一次真算出来的。

本批采用的做法是固定的：**完整检查点 + 独立子运行 + 完整历史前缀复制**。
不做"只有 301 年以后记录"的独立文件，也不建递归拼接的历史存储系统。

---

## 1. 谁有检查点

只有**新建的 EXP-06 运行**会写检查点。旧运行与预生成案例没有检查点，
因此**没有续演资格**，而且**不自动补跑**。

检查点只保存在服务自己的数据目录（`<run 目录>/checkpoint.json`）。
没有任意路径读取入口，也没有外部存档上传入口。

## 2. 检查点里有什么

| 字段 | 说明 |
|---|---|
| `checkpoint_schema` | `obs-checkpoint-v1` |
| `recorder_schema` | `obs-recorder-v1` |
| `engine` / `engine_sha256` / `engine_path` | 引擎身份，**全量 sha256**，不用短前缀比较 |
| `params` / `params_fingerprint` / `model_run_id` | 完整参数与模型身份 |
| `tick` / `full_digest` / `state_hash` | 状态的真实年份与摘要 |
| `model_state` | **完整模型状态**，不是 `year_record()` 的展示快照 |
| `recorder_state` | 记录器在该年记完之后的内部状态 |
| `history` | 对应 `years.jsonl` 有效前缀的 `bytes` / `records` / `sha256` |
| `digest`（外层） | 整个负载的完整性摘要 |

`model_state` 保留整数键、字符串键、tuple 与 list 的区别、布尔、`None`，
以及 `log` / `share_log` / `aid_log` 全部日志、`bands` 里的 `mem`/`memt`/`amem`、
人口余数、世界累计账、原始 `tick` 和所有现存字段。

`recorder_state` 保存并恢复 `_prev_cum`、`_prev_cells`、`_log_len`、`_share_len`、
`_aid_len`、`_aid_by_pair`、`_names`、`_birth_year` 与 `engine`。
**恢复之后不会把第 C 年当成空记录器，也不会再调用一次 `year_record(st_C)` 把这一年记两遍。**

### 编码

显式类型标记的 JSON：字典编码成 `[[键, 值], …]` 的条目表（所以整数键还是整数键），
元组带 `~t: "tuple"` 标记。遇到不支持的类型、重复字典键、不合法结构、超深超大，
**一律拒绝**。不用 pickle、不 eval、不从上传文件还原对象，也**不会把字符串键"猜回"整数**。
世界状态是全整数的，**遇到浮点直接拒绝**。

完整性摘要只用来发现损坏，**不是鉴权的替代品**。

## 3. 写入顺序

每个完整年度边界：

```
模型 step → Recorder 生成该年记录 → 追加记录并 flush+fsync
          → 写临时检查点、flush+fsync、os.replace → 才公布可续演年
```

第 0 年同样写检查点。正常结束与协作取消之前，最后一个完整年与检查点是对齐的。
只保留最新一份检查点，不逐年堆越来越大的模型副本。
**写检查点不取任何随机数、不改模型状态**（只调用只读的 `state_hash` / `full_digest` /
`run_id` 与状态的编码副本）。

异常中断留下"完整历史比检查点更新"时：历史**仍可回放**，但本版明确**拒绝**从该记录续演，
原因码 `checkpoint_not_at_tip`。不悄悄删历史、不自动回退、不伪造较新的检查点。
尾部半条记录只被排除在有效前缀之外，**原文件不改写**。

## 4. 历史与运行身份

父运行第 C 年结束后，续演会创建一个**新的 observer `run_id`**：

- 父运行的状态、文件、日志**一概不改**，终态不会被改回 `running`。
- 子运行的 `years.jsonl` 先独立复制父运行有效的 0..C 年**原始字节**，再追加 C+1..目标年。
  不用硬链接，两个运行不共享可写文件。第 C 年只复制一次，子运行**不重复输出第 C 年**。
- `seed` / `arm` / `sigma_m` / `move_mort_m` / `share_m` / `aid_m` / `recip_m` 原样保留。
- 子运行的 `model_run_id` 与父运行**相同**（同一个世界）；observer `run_id` 不同。
- 子运行的 `meta` 保留开局禀赋，另记 `root_run_id` / `parent_run_id` / `from_year` /
  `additional_years` / `history_note`。

读取语义不变：`run.years` 是**全局目标年**，`years_done` / `years_recorded` 是**全局进度**，
`/year/{t}` 仍然是全局模拟年。**`segment.completed_steps` 才是这一次新增算完了几步** ——
继承来的父历史不冒充本段进度。

第 0..C 年的数据是**继承自父运行**的，不声称由新服务版本重新产生（`meta.history_note` 写明）。

父运行必须是**已确认结束**的终态，且没有活着或状态未知的旧 worker。
子任务排队 / 运行期间**禁止删除**它依赖的父运行（`DELETE` 会 409）。
复制历史也属于那唯一的任务槽 —— 不会先放开槽再复制。

## 5. 并发、幂等与限额

沿用现有的单任务槽、鉴权、限流、取消与三态进程检查，**不另造队列**。

- 一次续演新增 **1–300** 年；累计世界年上限 `MAX_WORLD_YEAR = 3000`。
  **3000 是上限，不代表已经标定到 3000 年**：本轮实测到 600 年。
- 原有的 50 条运行与 512 MB 数据上限不变；检查点、复制的前缀与临时文件同样计入配额。
- `POST` 的占槽、建子运行、登记 `request_id` 在**同一个事务**里完成。
- 同一 `request_id` + 同一父运行 + 同一 `additional_years` 重试 → 返回原来那条子运行，
  不重复启动。同一 `request_id` 配不同请求 → `409 idempotency_conflict`。
  **删掉子运行之后，同一个 `request_id` 也不能重放成新任务**（幂等映射独立留存）。
- 请求结果未知时，客户端**只能用原 `request_id` 重试**，不要换键重派。

## 6. 接口

### `GET /api/runs/{id}/continuation`

```json
{"supported": true, "eligible": true, "reason_code": "ready",
 "reason": "可从第 300 年继续", "from_year": 300,
 "max_additional_years": 300, "max_world_year": 3000,
 "checkpoint_schema": "obs-checkpoint-v1"}
```

- `supported` = **引擎**支不支持；`eligible` = **这条记录此刻**行不行。两者不混用。
- 没有检查点时 `from_year` 是 `null` —— **不拿最后一帧画面的年份冒充检查点年份**。
- 不可续演时的原因码：`unsupported_engine`、`missing_checkpoint`、`source_active`、
  `worker_unknown`、`checkpoint_invalid`、`checkpoint_not_at_tip`、`engine_mismatch`、
  `config_mismatch`、`world_limit`、`quota_exceeded`。人话说明与原因码说的是同一件事。
- 判定有成本，可以缓存文件签名；但 **`POST` 与 worker 启动时都会重新校验一遍**。

### `POST /api/runs/{id}/continue`

请求**只接受**这两项，严格整数（排除 bool 与小数），多余字段一律 422：

```json
{"additional_years": 300, "request_id": "客户端生成的 UUID"}
```

成功与幂等重试都返回 200：

```json
{"run_id": "新的子运行ID", "parent_run_id": "父运行ID", "root_run_id": "最初运行ID",
 "from_year": 300, "target_year": 600, "status": "queued", "reused": false}
```

幂等重试的 `status` 返回**真实当前状态**（可能是 `running` / `done`），`reused=true`，
不一律伪装成 `queued`。

### 每条运行新增（`GET /api/runs` 与 `GET /api/runs/{id}` 都有）

```json
"lineage": {"kind": "origin|continuation", "root_run_id": "…",
            "parent_run_id": "…或 null", "from_year": 0}
"segment": {"from_year": 0, "additional_years": 120,
            "completed_steps": 120, "history_ready": true}
```

完整前缀通过临时文件 + `os.replace` 发布之后 `history_ready` 才为 `true`；
普通运行则在第 0 年记录完整之后为 `true`。
普通运行 `from_year = 0`、`additional_years = 原 years`、`completed_steps` 是真实已算步数。

### `GET /api/config` 新增

```json
"continuation": {"engines": ["exp06"], "max_additional_years": 300,
                 "max_world_year": 3000, "checkpoint_schema": "obs-checkpoint-v1"}
```

### 错误

既有接口的错误返回格式**一个字都不改**。鉴权仍是 401/403，找不到 404，类型 422，
范围 400，限流 429。状态 / 存档 / 版本 / 幂等 / 配额冲突用 409，
**新接口**的 `detail` 是结构化的：

```json
{"detail": {"code": "上述原因码或 idempotency_conflict", "message": "说明"}}
```

前端只为这两个新接口解析这个结构。

## 7. 恢复时会重新核验什么

- 检查点**整份**重新校验（外层摘要、schema、字段类型、history 段）；
- 历史**有效前缀**的字节数与 sha256；
- **实际加载的引擎**：`engine_sha256` 全量逐字比对。
  不拿 `app._run_version()` 那个展示用的版本块当恢复许可证，也不用短哈希前缀比较。
- 引擎加载器只从 `config.ENGINES` 白名单取路径，**不接受请求指定的代码路径**；
  并且**算哈希的那份字节就是被 `compile` 执行的那份字节**（只读一次磁盘）。

## 7b. 怎么复现"重启服务之后接着算"

```bash
# 本批自己的端口与数据目录；不碰 8765 / 8772 / 8788
CONT_TEST_PORT=8792 CONT_TEST_DATA=/tmp/chronicle-cont-20260913/testdata \
  python3 observer/test_continuation.py --report /tmp/chronicle-cont-20260913/report.json
```

K2S 组会真的做这几步，并把两个服务的 PID、启动命令、退出码写进报告的 `services` 段：

1. `python3 -m uvicorn observer.app:app --host 127.0.0.1 --port 8792` 起服务 A；
2. `POST /api/runs`（EXP-06，300 年），等它 `done`；
3. **停掉服务 A**（SIGTERM），并核实端口上确实没人应答；
4. 用**同一个数据目录**起服务 B（PID 与 A 不同）；
5. `GET /api/runs/{id}/continuation` → `eligible=true, from_year=300`；
6. `POST /api/runs/{id}/continue {"additional_years":300, "request_id":…}`；
7. 跑到第 600 年，与"连续 600 年"的对照运行逐年比较，首处差异必须是 `None`。

## 8. 本版做不到的

- 累计世界年只实测到 **600 年**，`MAX_WORLD_YEAR=3000` 只是上限。
- 检查点与完整历史对不齐时**不能**续演（只能回放）。本版不做自动回退或修复。
- 只有 EXP-06 写检查点；其它引擎的运行没有续演资格。
- 不做跨版本存档兼容：引擎源码换一版，旧检查点就不再被接受（`engine_mismatch`）。
