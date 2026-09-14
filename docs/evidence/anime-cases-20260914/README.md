# 动漫前端真实案例 · 实测证据（2026-09-14）

任务 **C_ANIME_SUPPORT_01**。清单正文是 [`docs/ANIME-REAL-CASES.md`](../../ANIME-REAL-CASES.md)，
这里是它引用的原始 API 响应与复核记录。

工作目录 `/Users/ecool/civilization-sim-exp07-farming`，分支 `backend/exp07-farming`，
服务版本 `repo_commit=6efdd81db2ab` / `api_version=obs-1.10`。
本轮**改了两处 Python**（见下面"顺手修掉的一个记账缺陷"）：写案例清单时对账发现
`cells` 的逐格数加不回 `farm.year`。除此之外没有新增接口、没有新增字段名、没有动前端。

## 怎么产生的

```bash
OBSERVER_DATA_DIR=/tmp/chronicle-exp07-20260913/anime/data \
  python3 -m uvicorn observer.app:app --host 127.0.0.1 --port 8902      # pid 17664
```

端口 **8902**、数据目录 `/tmp/chronicle-exp07-20260913/anime/data`（本任务独立子目录），
**没有碰 8765 / 8772 / 8788，也没有碰上一轮的 `api/testdata`**。
四条运行都是通过 `POST /api/runs` 建的，命令原文见清单正文 §7。

| 运行 | run_id | 引擎 | `farm_m` | 第 300 年人口 / 群体 |
|---|---|---|---|---|
| A 主案例 | `e289c4c7ff47` | exp07 | 250 | 1549 / 45 |
| B 旧引擎对照 | `05c2f8d4d969` | exp06 | 旧引擎没有这个参数 | 282 / 15 |
| C 受控对照 | `fa781b561845` | exp07 | 0 | 282 / 15 |
| D 弃耕案例 | `4f83f009ef28` | exp07 | 1000 | 683 / 25 |

## 文件

| 文件 | 内容 |
|---|---|
| `real-cases.json` | 机器可读的案例清单：三条运行的身份、10 个案例（含完整事件对象与当年快照）、两组受控对照、事件类型清点、"没有发生的事" |
| `series-slim-A.json` | A 的逐年轻量时间轴（301 行：人口/群体/存粮/野外存量/耕地总量/当年收成/开垦/退化/事件数） |
| `runA-year-*.json` | 案例引用到的 12 个年度记录原样响应（第 0/1/2/4/52/218/219/267/290/295/297/300 年） |
| `runB-year-300.json` / `runC-year-300.json` | 旧引擎（无 `farm` 段）与 `FARM_M=0`（有 `farm` 段、里面是真实的 0）的对照 |
| `runD-year-1/41/300.json` | 弃耕案例：第 1 年开垦 20 000、第 41 年三格归零、末年全景 |
| `run{A,B,C,D}-meta.json` | 四条运行的完整身份（`model_run_id` / `full_digest` / `engine_sha256` / `params_used`） |
| `bandA-farmer-y2.json` | 第一个开垦者的卷宗（`at_year=2`） |
| `bandA-repayer-y295.json` | 唯一一次回助的供给方卷宗（`at_year=295`） |
| `relationsA-y295.json` | 第 295 年的援助关系网（41 节点 / 10 边 / 17 笔 / 34 405 481 kcal） |
| `config.json` / `map.json` / `milestones.json` | 引擎能力表、地图形状、预生成案例 |
| `verify-cases.py` / `cases-verify.txt` | **逐条复核清单里每一个数字**的脚本与输出 |
| `archive-size-measured.txt` | EXP-07 存档体积的实测原始数据（`docs/TODO-BACKLOG.md` #17/#18 的更正依据） |
| `service.txt` | 测试服务日志（含每一次真实 HTTP 请求） |

## 复核

```bash
python3 docs/evidence/anime-cases-20260914/verify-cases.py
→ 通过 88 / 失败 0（共 88 项），退出码 0
```

脚本不重跑模型，只把文档里写下的每一个数字拿去和已保存的逐年记录对。
最后一组是**跨实例回放**：上一轮那条 12 年样例运行（`29d5e925003b`，另一个数据目录、
另一个 `run_id`、同样的参数）与 A 的第 12 年逐字段相同，包括状态摘要 —— 这就是
"同参数同版本 ⇒ 同一段历史"在本机的实测依据。
**错误注入实测过它真的会红**：把"第一次收成 `weather_m` = 949"的期望改成 950，
输出 `FAIL weather_m 记录=949 文档=950`、`通过 66 / 失败 1`、退出码 **1**。

第一版正文里有 6 个数字是我按印象写的（第 218 年的人口/群体，以及 5 处"全图耕地"总量），
复核时对不上，已按记录改正 —— 这也是加这个脚本的原因。

## 顺手修掉的一个记账缺陷

写案例 2 的时候对账发现：第 2 年 `farm.year.potential_kcal = 48 399 000`，而
`cells` 逐格加起来只有 32 110 875 —— 差的 16 288 125 正好是 14 号与 30 号两格
**长出来却一颗没被收走**的部分。原因是逐格明细当时拼自事件日志，而事件按约定
"只有实际量 > 0 才记"，所以这两格在日志里根本不存在，`cells` 里就被写成
`potential=0 / uncollected=0 / weather_m=null` —— 这正是"未记录填 0 冒充测量"。

修法（最小、按原接口兼容，没有新增字段名、没有改事件规则）：

- `exp07/verify7.py`：新增只读痕迹 `farm_cell_trace`，逐格记下本年的完整结算
  （耕地前后、`worked/built/decayed`、天气、潜在/实收/没人收）。
  **不进状态哈希、不进任何账**，和已有的 `farm_effort_trace` / `field_pre` 同一性质。
- `observer/adapter.py`：`cells` 改从这份痕迹取数，事件日志只再用于参与者的 `crop_kcal`。
  `weather_m` 仍然只有在"这一格这一年真的没有产量结算"时才是 `null`。
- `observer/test_exp07.py`：新增 **R12**（逐格加总 == `farm.year` 五项，三档 `FARM_M` 逐年查）
  与 **R12b**（潜在产出全没人收的格必须出现且不是 0/null；`FARM_M=0` 档如实记 UNCOVERED
  —— 那一档不耕作，这条路径不存在）。

**这次改动是"只影响观察"的**，有两条硬证据：

1. 42 组 × 300 年扫描重跑，`state_hash` / `full_digest` / `params_fingerprint` /
   各项读数与已提交的 `docs/evidence/exp07-20260913/scan.json` **逐项相同**（0 处不同）。
2. 重建的三条运行 `model_run_id` 与 `full_digest` 与修复前**完全一致**
   （A `8d6281d91c14…/2a3e1ca14a83…`）。变的只有 `engine_sha256`（源码本身变了）。

**错误注入实测**：把 `farm_cell_trace` 抽空（等于修复前"照日志拼"的行为）再跑同一组检查，
R12 立刻报出 29 处越界（第 1 年 `built_m` 0≠30000、第 2 年 `potential` 0≠54 750 000），
确认这条检验真的承重。

## 受影响的测试（本轮重跑，不是全量复跑）

| 套件 | 结果 | 文件 |
|---|---|---|
| `python3 exp07/run_tests.py` | **35 / 0 / 0** | `../../..//exp07/TESTS.txt` |
| `python3 exp07/run_scan.py`（42 组 × 300 年） | 42 组读数与 `state_hash` / `full_digest` / `params_fingerprint` 与 2026-09-13 提交的 `scan.json` **逐字段相同（0 处不同）** | `scan-rerun.txt` |
| `EXP07_TEST_PORT=8902 python3 observer/test_exp07.py --report …` | **63 / 0 / 未覆盖 2** | `api-report.json` / `api-test.txt` |
| `python3 observer/run_tests.py` | **256 / 0 / 0** | `observer-regression.txt` |
| `python3 observer/c07_version_test.py` | 17 / 0 | —— |
| `python3 observer/c08_engines_test.py` | 51 / 0 | —— |
| `python3 observer/test_continuation.py --quick` | 24 / 0 / 未覆盖 3 | —— |
| `python3 docs/evidence/anime-cases-20260914/verify-cases.py` | **88 / 0** | `cases-verify.txt` |

两项 UNCOVERED 都在 R12b，如实记着：`FARM_M=0` 那档不耕作、潜在产出恒为 0，
这条路径不存在；`FARM_M=1000` 那档在 8 年的测试窗口里没撞上，本档没有承重
（承重的是 `FARM_M=250`，32 个格年）。

## 边界

- 这四条运行在**本机（远端）**的 8902 上，与根本机 `127.0.0.1:8901` 的 `aaad77b8f251`
  是不同的实例。本轮**没有读过**根本机的数据，清单里也没有替它断言任何事件。
- 没有截图、没有录屏、没有浏览器验收：本任务不含前端工作，前端由 Grok 负责。
- 这里没有数据库文件与凭据。
