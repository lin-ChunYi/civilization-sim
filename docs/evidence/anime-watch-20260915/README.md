# C_WATCH_DATA_01 · 观看计划 实测证据（2026-09-15）

基准 `main @ 2f6b04969736e6c3c6ab868204c0a315373eb4cf`，分支 `backend/anime-watch-data`，
独立工作树 `/Users/ecool/civilization-sim-anime-watch-data`。
契约 [`docs/OBS-WATCH-PLAN-CONTRACT.md`](../../OBS-WATCH-PLAN-CONTRACT.md)（`obs-1.11`）。

**`exp01/`–`exp07/` 与基准逐字节相同**（`git diff --exit-code 2f6b0496 -- exp01 … exp07` 退出码 0）。
本批只动了 `observer/`（新增 2 个文件、改 5 个）与 `docs/`。

## 怎么跑出来的

```bash
python3 -m observer.make_anime_cases                       # 现做四条案例
OBSERVER_DATA_DIR=/tmp/chronicle-watch-20260915/data \
  python3 -m uvicorn observer.app:app --host 127.0.0.1 --port 8903   # 起之前确认 8903 空闲
curl -s http://127.0.0.1:8903/api/runs/preset-anime-farm250/watch-plan
python3 observer/test_watch_plan.py --report <路径>.json
```

端口 **8903**、数据目录 `/tmp/chronicle-watch-20260915/`（本批独立）。
没有碰 8765 / 8772 / 8788 / 8901 / 8902，也没有动任何既有存档或用户自建运行。

## 文件

| 文件 | 内容 |
|---|---|
| `watch-plan-preset-anime-*.json` | 四条已提交案例的**真实响应**原样保存 |
| `watch-plan-preset-anime-farm250-through2.json` | 把计划钉在 `through=2` 的真实响应（缺项写 `outside_watermark`） |
| `test-report.json` | `observer/test_watch_plan.py` 的 47 项结果 |
| `observer-regression.txt` | `observer/run_tests.py` 258 项 |
| `poison-check.txt` | 四处关键判据的**错误注入**实测：确认检验真的承重 |
| `config.json` | `/api/config`（`api_version=obs-1.11`） |

## 测试

| 命令 | 结果 |
|---|---|
| `python3 observer/test_watch_plan.py --report …` | **47 / 0 / 未覆盖 0**，退出码 0 |
| `python3 observer/run_tests.py` | **258 / 0 / 0** |
| `python3 observer/c07_version_test.py` | 17 / 0 |
| `python3 observer/c08_engines_test.py` | 51 / 0 |
| `git diff --exit-code 2f6b0496 -- exp01 … exp07` | 退出码 0（一行没动） |

长跑撞不到的路径全部由**构造的年记录**承重，不挂在真实案例上：

- 同一年一个群体消失、另一个分裂（净群体数不变）——目录仍然完整（W3）；
- 回助依据指向**未来 / 不存在 / 别的运行里的同名 id**——一律不进 `basis_event_ids`（W7）；
- 年记录尾巴是半截行 → 水位缩回最后一条完整记录；整个文件空 → **409 明确报错**，
  绝不返回空目录再宣布"看完了"（W5f/W5g）；
- 全程无事件 / 只有第 0 年 / 运行还在跑 —— 各有实际用例（W6）。

真实续演子运行也测了：直接打开子运行与先打开父运行，**共有群体的 `first_year` 与顺序完全相同**；
把父运行的历史目录删掉之后，子运行的计划一字不变（W4）。

## 错误注入（`poison-check.txt`）

| 注入 | 结果 |
|---|---|
| 身份目录改成"只在群体总数变多的年份补读" | 漏掉分裂出来的 `300` → W3a 变红 ✅ |
| 按 JS `Number`（float）排 64 位 id | `…807` 与 `…806` 顺序被调换 → 排序断言变红 ✅ |
| 回助依据照单全收不核验 | 把未来的 `t9-aid-0`、不存在的 `t2-aid-77` 也收进来 → W7a 变红 ✅ |
| `through` 越界时静默夹取 | 用户以为在看第 99 年，实际给的是第 2 年 → W5e（400）变红 ✅ |

## 未覆盖

- 浏览器/前端验收不在本任务内（前端是 `G_WATCH_PLAY_01`）。
- 没有截图、录屏：本任务只交后台接口与数据。
