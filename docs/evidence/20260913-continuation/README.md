# C_CONT_01 续演 · 实测证据（2026-09-13）

工作目录 `/Users/ecool/civilization-sim-obs-continuation`，分支 `backend/obs-continuation`，
基准 `8bc48722603ceaa94374c6305b4955b65c31fea9`。
独立端口 **8792**、独立数据目录 `/tmp/chronicle-cont-20260913/live`，
**没有碰 8765 / 8772 / 8788 或任何旧服务**。这里不含数据库文件与任何凭据。

## 1. 定向验收（32 项全过）

```
python3 observer/test_continuation.py --report /tmp/chronicle-cont-20260913/report-full.json
→ 通过 32 / 失败 0 / 未覆盖 0（共 32 项），退出码 0
```

- `report-full.json` —— 机器可读证据：命令与退出码、seed、参数、比较范围、首处差异、
  父记录哈希、引擎身份。
- `test-continuation.log` —— 完整输出。

要点：

| 检查 | 结果 |
|---|---|
| seed 0 / 777 / 4242：60 步 → 存档 → **换进程**再 60 步 vs 连续 120 步 | 逐年记录、完整模型状态与全部日志、稳定事件 id 全部相同 |
| seed 4242：300 → 存档 → 再 300 vs 连续 600 | 逐年完全一致，首处差异 `None` |
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
python3 observer/run_tests.py → 通过 255 / 失败 0 / 未覆盖 0（共 255 项），退出码 0
```
见 `observer-regression.log`。
