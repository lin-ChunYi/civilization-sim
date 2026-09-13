# C_CONT_01 续演 · 实测证据（2026-09-13）

工作目录 `/Users/ecool/civilization-sim-obs-continuation`，分支 `backend/obs-continuation`，
基准 `8bc48722603ceaa94374c6305b4955b65c31fea9`。
独立端口 **8792**、独立数据目录 `/tmp/chronicle-cont-20260913/live`，
**没有碰 8765 / 8772 / 8788 或任何旧服务**。这里不含数据库文件与任何凭据。

> **R1 补齐（2026-09-13）**：本批服务版本升到 **obs-1.9**；K2S 组补上"**真的停掉一个测试服务、
> 再用同一数据目录起另一个服务**"的全过程。本页数字与文件都是 R1 之后重新跑出来的。

## 1. 定向验收（45 项全过）

```
CONT_TEST_PORT=8792 python3 observer/test_continuation.py \
    --report /tmp/chronicle-cont-20260913/report-r1.json
→ 通过 45 / 失败 0 / 未覆盖 0（共 45 项），退出码 0
```

- `report-full.json` —— 机器可读证据：命令与退出码、seed、参数、比较范围、首处差异、
  父记录哈希、引擎身份。
- `test-continuation.txt` —— 完整输出。

要点：

| 检查 | 结果 |
|---|---|
| seed 0 / 777 / 4242：60 步 → 存档 → **换进程**再 60 步 vs 连续 120 步 | 逐年记录、完整模型状态与全部日志、稳定事件 id 全部相同 |
| seed 4242：300 → 存档 → 再 300 vs 连续 600（换 worker 进程） | 逐年完全一致，首处差异 `None` |
| **K2S：起测试服务 A 跑 300 年 → 停掉 A → 同一数据目录起服务 B → 在 B 上续 300** | 0..600 逐年与连续 600 完全一致，首处差异 `None` |
| 续演进程的 `make_world` 被测试桩替换成**会抛异常**的函数 | 仍然成功 —— 证明不是从第 0 年重算 |
| 第 300 年 | 只出现一次，年号 0..600 连续无重复 |
| 第 301 年的年度账 | == 301 与 300 的累计账之差（记录器前值确实接上了） |
| 继承历史里的援助 id | 第 314 年的回助依据是 `t128-aid-2`，能跳回第 128 年那一笔 |
| 五本账（资源 / 人口 / 信息 / 援助 / 援助记忆） | 0..600 年全段恒等，误差恒为 0 |
| 8 类坏档 / 不合格来源 | 各自给出确定且正确的原因码 |
| 尾部半条 | 只被排除在有效前缀外，**原文件不改写**，仍可续演 |
| 检查点落后完整历史 | 拒绝续演（`checkpoint_not_at_tip`），历史照常可回放，不删不伪造 |
| 幂等 | 同键重试返回同一条；同键不同参数冲突；**删掉子运行后也不能重放成新任务** |
| 连续续演三次 | 接出来的 50 年与连续 50 年逐年一致，边界与事件 id 都不重复 |

## 1b. 真·重启服务的证据（K2S）

两个服务进程的 PID、起停与退出码都写进了 `report-full.json` 的 `services` 段：

| 服务 | PID | 命令 | 数据目录 | 退出码 | 停止后还活着 |
|---|---|---|---|---|---|
| A | 63130 | `python3 -m uvicorn observer.app:app --host 127.0.0.1 --port 8792` | `/tmp/chronicle-cont-20260913/testdata` | `-15`（SIGTERM） | 否 |
| B | 63145 | 同上（**同一个数据目录**） | 同上 | `-15` | 否 |

过程：A 起来 → `POST /api/runs`（300 年）→ 跑满 → **停 A 并核实端口无人应答** →
起 B（PID 与 A 不同）→ `GET /continuation`（`eligible=true, from_year=300`）→
`POST /continue {additional_years:300}` → 在 B 上跑到第 600 年 → 停 B。
每一次 HTTP 请求与响应都在 `report-full.json` 的 `http_calls` 里；
两个服务的启动日志见 `service-A.txt` / `service-B.txt`。

比较：`comparison = {"range": "0..600 逐年", "k2s_first_diff": null}`。

`make_world` 禁止桩仍然保留在 K1/K2/K6 里（那几组由测试自己起 worker 子进程，
可以注入桩）；K2S 走的是服务自己起的 worker，所以那一组靠"与连续 600 年逐年一致"承重。

## 2. 真实续演案例（端口 8792）

父运行 `e1a1521889df`（EXP-06 / seed 4242 / sigma_m 0 / move_mort_m 50 /
share_m 1000 / aid_m 1000 / recip_m 1000）跑满 300 年，
续演成子运行 `cbc82af8499c` 到第 600 年。

```
GET  /api/runs/e1a1521889df/continuation   → continuation-eligible.json
POST /api/runs/e1a1521889df/continue       → continue-accepted.json
DELETE /api/runs/e1a1521889df              → 409 delete-parent-blocked.json
GET  /api/runs/cbc82af8499c                → child-run.json
POST 同一 request_id 重试                   → continue-idempotent-retry.json（reused=true, status=done）
POST 同键不同参数                            → 409 continue-idempotency-conflict.json
GET  /api/runs/preset-.../continuation     → continuation-unsupported.json
```

实测读数：

- `lineage = {kind: continuation, root_run_id: e1a1521889df, parent_run_id: e1a1521889df, from_year: 300}`
- `segment = {from_year: 300, additional_years: 300, completed_steps: 300, history_ready: true}`
  —— `years_done=600` 是**全局**进度，`completed_steps=300` 才是**这一段**真算的步数。
- `model_run_id` 与父运行相同（`2e4f9160a2effa9bee415dd5415133f7`），observer `run_id` 不同。
- 第 600 年：人口 547、群体 29，五本账误差全为 0（`year600-summary.txt`）。
- 第 300 年的记录，子运行与父运行**逐字段相同**。
- 父 `years.jsonl` 3,063,152 字节，子 12,498,894 字节；
  **子的前 3,063,152 字节与父完全一致**，且 inode 不同（没有硬链接，不共享可写文件）。

## 3. 既有回归

```
python3 observer/run_tests.py       → 通过 256 / 失败 0 / 未覆盖 0（共 256 项），退出码 0
python3 observer/c07_version_test.py → pass=16 fail=0
python3 observer/c08_engines_test.py → pass=51 fail=0
python3 ops/test_dispatch.py         → Ran 97 tests, OK
```
见 `observer-regression.txt`。`O27b` / `O34b` / `O34c` 现在读到的都是 **obs-1.9**。

`run_tests.py` 里的 O35a 跑的是 `--quick`（跳过 K2 / K2S / K3 三组长跑），
完整模式单独执行，就是本页第 1 节那一次。


> 说明：本目录里的日志用 `.txt` 后缀保存 —— 仓库的 `.gitignore` 忽略 `*.log`，用 `.log` 会让这些证据根本进不了版本库。内容是原样输出，一个字没改。
