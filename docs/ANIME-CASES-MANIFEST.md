# 动漫前端案例交接清单（C_ANIME_CASES_02）

给 Grok / Codex 的**最小可分发契约**。四条案例、固定标识、固定模型哈希，
外加开垦 / 收获 / 迁移 / 援助 / 回助五类事件的真实年份与事件 id。
**缺项一律写明是哪一种缺**，不拿 0 顶替。

机器可读的同一份内容：
[`docs/evidence/anime-cases-20260914/anime-cases-manifest.json`](evidence/anime-cases-20260914/anime-cases-manifest.json)
（`contract: "anime-cases-1"`）。逐条核过的细节与取数示例见
[`ANIME-REAL-CASES.md`](ANIME-REAL-CASES.md)。

---

## 1. 装上就能跑（干净检出，三条命令）

```bash
# 1) 现做四条案例的数据。确定性重算，几秒钟；写进 observer/preset/preset-anime-*/
python3 -m observer.make_anime_cases

# 2) 起服务。数据目录挑一个空目录，端口挑一个空闲的（先确认没被占用）
OBSERVER_DATA_DIR=/路径/到/一个空目录 \
  python3 -m uvicorn observer.app:app --host 127.0.0.1 --port 8902

# 3) 直接按固定 id 取
curl -s http://127.0.0.1:8902/api/runs/preset-anime-farm250 | python3 -m json.tool
curl -s http://127.0.0.1:8902/api/runs/preset-anime-farm250/year/295 | python3 -m json.tool
```

启动时 `presets.install_presets()` 会把它们装进数据目录并标成 `kind="preset"`
（预生成案例，不冒充实时任务）。**`run_id` 是下面四个固定值，不是随机 uuid。**

**为什么数据不在版本库里**：一条 300 年的 `years.jsonl` 有 2–8 MB，四条二十多兆。
它们是确定性重算出来的 —— 同一版引擎、同一组参数，在任何机器上生成的
`model_run_id` 与 `full_digest` 都一样，所以清单里的标识跨机器指向同一段历史。
`observer/preset/preset-anime-*/` 已进 `.gitignore`，生成后检出仍然干净。

---

## 2. 四条案例

同一颗种子 **4242**、同一组社会参数（`sigma_m=400`、`move_mort_m=50`、
`share_m=aid_m=recip_m=1000`、`arm=memory`、300 年），**只有引擎与 `FARM_M` 不同**。

| | A 耕作 | B 旧引擎 | C 受控对照 | D 全员耕作 |
|---|---|---|---|---|
| `sample_id` | `preset-anime-farm250` | `preset-anime-exp06` | `preset-anime-farm0` | `preset-anime-farm1000` |
| 引擎 | `exp07` | `exp06` | `exp07` | `exp07` |
| `farm_m` | **250** | 旧引擎没有这个参数 | **0** | **1000** |
| `model_run_id` | `8d6281d91c14c3697d4390e8baca5fb9` | `df1a9f4798463f545288f85ac096169b` | `112c9e1f580ac47710e8dc0c5ae0da17` | `940cca8853e07c07c61dd4d1b1f77868` |
| 末年状态摘要 | `2a3e1ca14a83d53c17973ded56f85776` | `f80ebd6f1b7de72765cc3754ed227a74` | `ff6070addaae8847cf1e61dfa33a6c75` | `b1d6db9717a083d46e26526373cffb8e` |
| 第 300 年人口 / 群体 | 1549 / 45 | 282 / 15 | 282 / 15 | 683 / 25 |
| 全图耕地（末年） | 454 083 | **未记录**（没有 `farm` 段） | 0 | 647 530 |
| 事件总数 | 6969 | 1465 | 1465 | 5680 |

`full_digest` = `model_run_id` + `/` + 末年状态摘要。
引擎源码 sha256：`exp07` = `6c18ed20b1e94035f08ea77847fa1ac7739e50fe76866872cc55a59bbe1e6a20`，
`exp06` = `43c9338551a23d6d7065f657394a25d5be041e63724ab12a23350bde53e5d186`。
装好之后 `GET /api/runs/{sample_id}` 里的这几项必须与上表一致 —— 对不上就是版本不同，
**不要将就着用**。

---

## 3. 五类事件：真实年份与事件 id

「首次」是逐年扫描 0..300 年的 `events` 取该类型的第一条；`id` 规则
`t<展示年>-<类型>-<当年序号>`，序号是**当年事件列表里的位置**（各类型共用一个计数器，
所以第一次迁移可能不是 `-0`），**也不代表相位先后**。

| 案例 | 开垦 `field_built` | 收获 `farm_harvest` | 迁移 `migrate` | 援助 `aid` | 回助 `aid.repay=true` |
|---|---|---|---|---|---|
| **A** `preset-anime-farm250` | 第 1 年 `t1-field_built-0`（1783 次） | 第 2 年 `t2-farm_harvest-0`（3390 次） | 第 218 年 `t218-migrate-1`（28 次） | 第 267 年 `t267-aid-4`（30 次） | 第 295 年 `t295-aid-24`（**仅 1 次**） |
| **B** `preset-anime-exp06` | **无** · `engine_lacks_mechanism` | **无** · `engine_lacks_mechanism` | 第 26 年 `t26-migrate-0`（153 次） | 第 73 年 `t73-aid-2`（57 次） | 第 128 年 `t128-aid-2`（16 次） |
| **C** `preset-anime-farm0` | **无** · `param_zero` | **无** · `param_zero` | 第 26 年 `t26-migrate-0`（153 次） | 第 73 年 `t73-aid-2`（57 次） | 第 128 年 `t128-aid-2`（16 次） |
| **D** `preset-anime-farm1000` | 第 1 年 `t1-field_built-3`（776 次） | 第 2 年 `t2-farm_harvest-4`（2589 次） | 第 1 年 `t1-migrate-0`（13 次） | **无** · `not_observed` | **无** · `not_observed` |

### 缺项的三种含义（别混）

| 代码 | 含义 | 界面怎么处理 |
|---|---|---|
| `engine_lacks_mechanism` | 这台引擎**根本没有**这套机制，年度记录里整个 `farm` 段缺席 | 显示「未记录」，**不要填 0** |
| `param_zero` | 机制在、字段也在，值**确实是 0**（`FARM_M=0`，一分劳动都没投到耕作） | 显示 0，这是测量结果 |
| `not_observed` | 机制开着、参数非 0，但**这 300 年里一次都没发生** | 显示「没有发生」，不要补桥段 |

B 与 C 的末年人口、群体、事件 id 序列完全一样（`FARM_M=0` 的 EXP-07 就是 EXP-06 的那段
历史），但**两者缺的东西性质不同**：B 是没有这套机制，C 是机制在而值为 0。

### 另外两类顺带给出（不在五类必给项里，但真实存在）

- **分裂 `split`**：A 第 52 年 `t52-split-0`（39 次）、B/C 第 66 年 `t66-split-0`（9 次）、
  D 第 116 年 `t116-split-0`（19 次）。
- **耕地退化 `field_decay`**：A 第 4 年 `t4-field_decay-6`（1251 次）、
  D 第 2 年 `t2-field_decay-5`（1055 次）；B/C 没有（同上表的缺项理由）。
- **弃耕**（耕地退回 0）只在 D 里发生：第 41 年 6/18/26 号格同时归零
  （`t41-field_decay-4` / `-10` / `-11`），整段 300 年共 7 次。A 里**一次都没有**。
- **群体消失 `extinct`**：四条都是 **0 次**。

---

## 4. 怎么核这份清单

```bash
# 只用仓库里的东西：已提交的真实 API 响应 + 按记录参数就地重算整段历史
python3 docs/evidence/anime-cases-20260914/verify-cases.py
→ 通过 170 / 失败 0，退出码 0

# 清单本身也可以重算后逐字节比（不重新生成数据）
python3 -m observer.make_anime_cases --check
→ 清单与已提交的那份逐字节相同
```

复核脚本**不依赖任何临时目录或本机数据库**；`--data-dir <观察台数据目录>` 可选，
给了就再多对一层"盘上的记录 == 就地重算"。

---

## 5. 边界

- 这四条是**自然演化**的运行，不是为了好看构造的演示。不要为了画面重跑成别的参数，
  也不要改 `FARM_M` 之外的东西再冒充同一条案例。
- 事实层与表现层的分界见 [`ANIME-REAL-CASES.md`](ANIME-REAL-CASES.md) §5 末尾：
  手搓群体代表形象、由 `id` 确定性派生别名、把已记录事件做成转述气泡都可以，
  只是别把它们说成模型记录。
- 清单里没有的东西就是没有：情绪、姓名、动机、村落、国家、部族意志、季节与昼夜。
