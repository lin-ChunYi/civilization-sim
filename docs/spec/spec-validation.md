# spec-validation —— 验证体系、涌现判据、反剧情树治理与算力预算

> **【生效范围（2026-09-10）】** 本文件是 Phase 0 的**规格草案**，未获整体批准。
> 四份规格由互不通气的 agent 写成，在若干接口上互不相容（见 `docs/INTEGRATION-REVIEW.md` §1）。
> **凡与 `docs/EXP-01-SPEC.md` 重叠的部分，以 EXP-01-SPEC 为准**；被取代的具体条款逐条列在 `docs/EXP-01-CONFLICTS.md`。
> 本文件保留作为论证与备选方案的来源，不作为实现依据。


- **slug**: `spec-validation`
- **阶段**: Phase 0 规格草案（写第一行内核代码之前必须签字的部分已单列）
- **写作日期**: 2026-09-10
- **回答的纲领问题**: Q5「如何产生真正的涌现，而不是隐藏的剧情树」、Q7「如何验证一个重大历史事件在逻辑上成立」、Q10「如何衡量一个模拟世界是否合理但不必真实」、Q11「如何让数千年的模拟在计算成本上可行」
- **姊妹规格**: `spec-world-state`（L0 本体 / 空间 / 时间 / 确定性）、`spec-causality`（因果 / 重放 / 分叉 / 归因）、`spec-llm-boundary`（LLM 权限 / 污染控制 / 叙事分层）
- **证据等级约定（全项目统一）**: A = 多来源实证且有量化参数；B = 理论共识但量化弱；C = 有实质争议或单一来源；D = 无来源、我们自己的假设
- **引用约定**: `brief-slug §小节` 指 `/Users/ecool/civilization-sim/research/briefs/`；`critique-slug F编号` 指 `/Users/ecool/civilization-sim/research/critique/`。凡本文自创且两处都没写过的，一律显式标注 **［本文原创，无来源，D 级］**。

---

## 0. 本规格做出的 20 项裁决（摘要）

| # | 裁决 | 依据 | 不可逆？ |
|---|---|---|---|
| **V1** | **验收集在"功效标定 + 诱饵世界标定"两项都完成之前是空集。** 任何判据进入验收集的前置条件是：(a) 在 W1 家族至少一个变体上失败；(b) 有完成的功效分析且功效 ≥ 0.80；(c) 在健康内核上的伪阳性率 ≤ 5%。当前电池 v0 的 51 条**全部**处于"候选"状态 | `emergence-verifiability` F6 + F9（"功效不足的判据不是弱判据，它是零判据，留着它比删掉它更危险"） | 否（但一旦放松就永久失去意义） |
| **V2** | 模式电池 v0 = **51 条候选模式**，三分区：`calibration`（校准集，可用于调参）/ `sealed_acceptance`（封存验收集，开封即作废）/ `observation`（观察集，永不判定通过失败）。C 级证据一律不进验收集 | `abm-methodology` M2；`emergence-verifiability` F13、F16 | 否 |
| **V3** | 预注册通过规则：**A 级验收模式零失败 + B 级验收模式通过 ≥ 80%**；多重检验用 **Benjamini–Yekutieli，q = 0.10**（不是 BH，因为我们的模式高度相关）；检验总数 m 与家族划分在开跑前冻结 | `emergence-verifiability` F1、F13；BY 的选择为［本文原创，无来源，D 级］ | **是**（预注册按定义不能事后做） |
| **V4** | 诱饵世界 **W1（剧情树，5 个变体）/ W2（纯外生驱动）/ W3（纯噪声）**，与 `pseudo-simulation` F6 的 K1–K7 金丝雀一一映射；交付**判据标定报告**（判据 × 诱饵 的检出矩阵 + 最小检出样本量 n* + 健康内核伪阳性率） | `emergence-verifiability` F6；`pseudo-simulation` F6 | 否（但越晚做越无用） |
| **V5** | **零模型套件 N0–N5 是 CI 合并门，不是评审习惯。** 任何新机制的 PR 必须附 `null_gain_report.json`；若某输出的 N0（纯承载力，零 agent）得分 ≥ 完整模型的 **90%**，该输出在**全部文档中**永久标注"外生驱动，非 agent 解释" | `prior-art-postmortem` 【致命 4】（"这条必须是 CI 门槛，不是评审习惯"）；`complex-systems-emergence` §8.4；`abm-methodology` M6 | **是**（要求内核从第一天就把机制做成可开关的，事后改架构极贵） |
| **V6** | 涌现认证 = **D1–D6 六项 + 三个非统计检查**（类型抹除 / 内核→观察器单向依赖 / 阶跃探测）；消融矩阵必须额外报告**部分可替代性 PS** 与**归零脆性 ZB**，健康区间在中间 | `emergence-verifiability` 7.2 与 F7；`abm-methodology` M7 | **是**（词汇表分层必须在内核里，见 `spec-world-state` §3） |
| **V7** | 事件合理性检查器 = **五闸门 G1–G5 + tick 级守恒审计 A1 + 并发占用检验 A2 + 链式不可能性账 A3 + 归因残差 A4**，外加一份明示的"抓不住什么"清单（8 条）。**所有闸门的输入必须从世界快照重算，永不接受事件 payload 的自报** | `emergence-verifiability` 7.3、F12；`causality-bookkeeping` F2 | 否 |
| **V8** | 纲领第 7 条拆成**三个不同的量**，不是一个：`novelty_bits`（组合口径，正面下界，参考分布是世界自己的历史）/ `surprise_bits`（相对显式声明的 reference ensemble，只决定**报告篇幅**）/ `explanation_bits`（由重放测得）。可执行版本：`explanation_bits(e) ≥ surprise_bits(e) − τ`，τ = 4 bits ［D 级待标定］ | 综合 `emergence-verifiability` F3 与 `mandate-contradictions` F2；两者不是同一个量这一裁决为［本文原创，D 级］ | 否 |
| **V9** | **荒诞度禁止成为运行时变量。** 三重执行：(a) 三个 bits 量只能在 `observer` crate 定义；(b) `--audit` 模式下 observer 输出打污点标记，污点值到达内核写入路径 = 运行时中止；(c) **荒诞度置换不变性检验**：把全部 absurdity 值替换为随机数后重跑，必须逐位相同 | `pseudo-simulation` S1 替代设计 1；`mandate-contradictions` F2 第 2 点；(c) 为［本文原创，D 级］ | **是**（污点架构必须在第一版内核里） |
| **V10** | **《反剧情树宪章》**：九类目标导向调节机制默认禁用；例外必须带 `GATED(...)` 注释 + 触发计数器 + 到期版本；`GATED_COUNT[kind]` **只降不升**（升高需宪章修订 + 两人签字入登记册）。**CI 只允许断言不变量，永远不允许断言宏观结果** | `pseudo-simulation` S3、S11；`prior-art-postmortem` 【结构性 1】 | **是** |
| **V11** | **canon / lab 单向阀**：正式世界线 seed 由事先声明的、与结果无关的规则决定（`seed = BLAKE3("canonical" ‖ kernel_hash ‖ basemap_hash ‖ param_hash)[0:8]`）；lab 分支**永远不能**成为 canon（数据模型硬约束，不是纪律）；**运行登记表 append-only，任何 > 100 世界年的运行自动入表** | `pseudo-simulation` F5 | **是**（不从第一天记，事后永远无法证明没有挑选） |
| **V12** | 参数改动三分类账 `bug / evidence / aesthetics`；**被 `aesthetics` 改过 ≥ 2 次的参数，其下游一切宏观结论永久标注"非涌现（拟合产物）"**；Phase 1 末参数冻结；`justification_class` 里 `叙事` 类允许数量 = **0**；**参数/外部校准目标比 P/T ≤ 3** | `pseudo-simulation` F2；`llm-storytelling` F7 | **是** |
| **V13** | **密封清单测试**：Phase 0 末团队独立写下全部可想到的事件种类，合并去重后加密封存（age + 2-of-3 Shamir），承诺哈希写入 DECISION-REGISTER 与 git tag；第一次完整 canon 长跑后、**先做完无监督聚类再开封**。清单外簇质量占比 < 5% 判失败，≥ 15% 判通过，> 60% 反向报警 | `pseudo-simulation` S4（15% 为该红队自标 D 级；5%/60% 双边为本文追加，D 级） | **是**（看过输出之后再写清单，这个测试就死了） |
| **V14** | 算力四方分账 **模拟 20% : 验证 50% : 因果 25% : LLM 编排 5%**；目标硬件 8 台 × 16 核；`T_run ≤ 1 小时`（不含 LLM）；`N_ensemble = 200`。验证占比连续两个月 < 50% ⇒ 里程碑评审阻塞 | `emergence-verifiability` F15（验证 ≥ 50%）；`causality-bookkeeping` F5（因果必须单列，不得与验证共用）；`computational-feasibility` F1 | **是**（预算决定本体论，反过来做会设计出跑不起来的世界） |
| **V15** | 自由参数硬配额：`free_global ≤ 12` + `free_regional ≤ 3`（东亚专用），总 ≤ 15；每个参数必须标 `source:` 或 `free: true`，CI 计数超限即构建失败 | `computational-feasibility` S2；两本账的拆分依据 `pseudo-simulation` S6 的东亚 holdout | **是** |
| **V16** | **CI 级玩具世界**：一个流域约 600 格、300 世界年、**全部机制开启**（不是简化机制）、200 种子；单次 ≤ 2 s，200 种子 ≤ 7 min（16 核）。全套判据必须能在它上面跑完 | `emergence-verifiability` F15 第 2 条；`computational-feasibility` §7.8 | 否 |
| **V17** | **仓库里必须始终存在一个 `--spike` main**：高程 + 单一作物 + 人口 + 迁徙 + 一种冲突，零 LLM，在参照笔记本上 **≤ 1.8×10¹¹ CPU 周期（≈60 s @3 GHz）** 跑完 3000 世界年，输出因果图，通过 bit 级重放测试。**连红 7 天 ⇒ 全项目其他工作暂停** | `prior-art-postmortem` §1.9 + 【取舍 2】 + §5.1（任务书称其为 "T12"；原文无此编号，实际位置为这三处） | **是** |
| **V18** | **一页纸预注册拒绝条件 R1–R25**，在跑第一个长世界之前签字；每条标注证据等级与是否 D 级待标定 | `emergence-verifiability` F1（"一个没有拒绝域的判据体系不是判据，是修辞"） | **是** |
| **V19** | **《我们承认无法验证什么》清单只允许增长，不允许缩短**，除非附上新的可核验经验来源与提交记录 | `emergence-verifiability` §8 第 10 条（"这份清单的长度是项目诚实度的直接指标"） | 否 |
| **V20** | **判据治理元规则**：判据失败时，改机制的人与改判据的人必须不同；改判据必须开新基线并重跑该判据支撑过的全部历史结论；`views` 计数 ≥ 3 的判据自动降级为校准集 | `emergence-verifiability` §6 第 5 条、F13 | 否 |

**这 20 条里标"是"的 11 条，属于 `computational-feasibility` C5 所说的"必须在第一行内核代码之前定死"的类别。**

---

## 0.1 一句话主张

**这份规格的全部内容都是在给纲领补一样东西：拒绝域。** 纲领的十条原则规定了什么被允许发生，没有一条规定什么会让我们判定这次模拟失败（`emergence-verifiability` F1）。本文把"合理""涌现""荒诞""可行"四个词，各自换成一组**在跑之前就写死的、能失败的、且被证明过能抓住我们自己伪造的世界的**检查。做不到最后半句的检查，一律删除，不许辩护。

---

## 0.2 判据的证据量：为什么"没有标定过的判据等于修辞"

这不是修辞性的说法，它有一个两行的形式化，值得写在最前面。

设判据 `C` 对世界 `W` 输出 `pass/fail`。它对"这个世界不是剧情树"这个命题提供的证据，是对数似然比：

```
bits(C) = log2 [ P(C 通过 | 健康内核) / P(C 通过 | 剧情树内核) ]
```

- 若 `P(C 通过 | 剧情树) = 1`（即判据在 W1 上不失败），则 `bits(C) = log2 P(C 通过 | 健康) ≤ 0`。
- 也就是说：**一个抓不住剧情树的判据，其证据量不是零，是负的。** 它只会在健康内核偶尔误报时降低我们的信心，永远不会在通过时提高我们的信心。
- 一整页绿色的、未标定的判据，其总证据量 = `Σ bits(C_i) ≤ 0`。**验收报告全绿，信息量为负。**

因此 V1 的形式是强制的，不是保守：**判据的准入条件是 `bits(C) > 0` 的实测证据，而这只能来自诱饵世界。** `complex-systems-emergence` §9 第 18 条已经诚实地写下"没有任何文献做过『剧情树能否骗过涌现度量』的研究"——这意味着本项目在使用任何涌现度量之前，必须自己生产这份知识。

### 这一节禁止了什么

- 禁止在标定报告完成前，把任何判据写进"验收"位置（CI 红/绿、里程碑签字、对外表述"我们证明了 X"）。标定前的判据只能出现在仪表盘上。
- 禁止用"这条判据听起来有道理"作为加入判据的理由；唯一合法的理由是"它在 W1 的某个变体上失败，且在健康内核上不失败"。
- 禁止把判据数量当成严谨度指标。50 条未标定的判据的证据量之和 ≤ 0；1 条标定过的判据的证据量 > 0。

---

## 1. 预注册的模式电池 v0

### 1.1 数据结构

每条模式是一条不可变记录，存于 `validation/patterns/*.toml`，文件整体哈希后写入 `DECISION-REGISTER.md`。改动必须新增记录并给出理由，**不许原地修改**。

```toml
[[pattern]]
id            = "P-SET-01"                 # 稳定 ID，永不复用
statement     = "聚落已定居面积对人口的标度指数 α 落在人类已知系统的经验散布内"
form          = "interval"                 # interval | ordinal | existence | absence | conditional | shape | negative
                                           # negative = 反向判据（打中经验值反而失败）
predicate     = "0.55 <= alpha_hat <= 0.95"   # 机器可求值的布尔表达式，只引用 metric 名
metrics       = ["alpha_hat", "alpha_ci_lo", "alpha_ci_hi"]

# 口径三元组（缺任何一项即为无效模式，CI 拒绝加载）
[pattern.caliber]
threshold  = "报警区间 α ∉ [0.55, 0.95]；理论区间 [2/3, 5/6]，实测散布 0.632–0.79"
definition = "聚落 = 连续建成位点簇；面积 = 建成位点凸包外接面积 (m²)；人口 = 该簇内 Cohort 求和 (µp)；截断 N_min = 50 人"
estimator  = "log10(A) ~ log10(N) 的混合效应模型（随机截距按 basemap 区块与 500 年期次），显式建模波动，报告 95% CI；禁止裸 log-log OLS"

evidence      = "A"
source        = "settlement-urbanization-spatial §4.1; complex-systems-emergence §2.5 §4.3"

[pattern.power]
test          = "两样本置换检验（能量距离），H1 = 移动成本参数 ×2"
n_seeds       = 0            # 0 = 尚未标定
effect_target = 0.05         # 需要能分辨的 Δα
achieved      = null
status        = "pending"    # pending | calibrated | insufficient
# 规则：status != "calibrated" 时，assignment 不得为 sealed_acceptance

assignment       = "calibration"      # calibration | sealed_acceptance | observation
morphology_class = ["*"]              # 形态条件化；"*" = 普适（只有守恒律与光锥才配用 "*"）
ergodicity       = "rate"             # rate（可进验收）| identity（只进多样性报告）
views            = 0                  # 模式预算账本：每次被用于指导调参 +1
seal             = { sealed = false, open_at_milestone = null, expired = false }
```

**加载期 CI 检查（`validation::load_patterns`）**：
1. `caliber` 三项非空，且 `estimator` 字段必须命中 `ESTIMATOR_REGISTRY` 中的一个已实现估计器（禁止自然语言描述充当估计方法）。
2. `evidence == "C"` ⇒ `assignment` 必须是 `observation`（`emergence-verifiability` F16 第 3 条）。
3. `power.status != "calibrated"` ⇒ `assignment` 不得是 `sealed_acceptance`（`emergence-verifiability` F9 第 1 条）。
4. `ergodicity == "identity"` ⇒ `assignment` 必须是 `observation`（F9 第 2 条）。
5. `views >= 3` ⇒ 自动降级为 `calibration`，并写入降级记录（F13 第 1 条）。
6. `form == "interval"` 且 `predicate` 中出现 `==` ⇒ 拒绝加载（**禁止点值**）。
7. 全部 `predicate` 的 AST 只能引用 `metrics` 中声明的名字，不得引用 `luck_bits`/`surprise_bits`/`novelty_bits`（防止判据自身依赖荒诞度）。

### 1.2 电池 v0：51 条候选模式

**读法**：`归属` 列是**目标归属**；按 V1，在功效与诱饵标定完成前，全部条目的**实际状态**是"候选"。`形状` 列的 `neg` 表示反向判据（打中经验值反而可疑）。

#### A. 聚落与空间（P-SET）

| ID | 陈述 | 形状 | 口径三元组（阈值 / 定义 / 估计方法） | 证据 | 来源 | 归属 |
|---|---|---|---|---|---|---|
| P-SET-01 | 面积–人口标度指数 α 落在人类经验散布内 | interval | α ∉ [0.55, 0.95] 失败 / 聚落=连续建成位点簇，N_min=50 / 混合效应模型+波动建模，禁 OLS | **A** | `settlement-urbanization-spatial` §4.1（理论 [2/3,5/6]；墨西哥盆地 0.632/0.711/0.718/0.764；中世纪欧洲 0.71–0.79；北美村落 0.643/0.662） | calibration |
| P-SET-02 | 标度关系是"打开"的而不是一开始就在：α 从统计不显著转为显著，且转变处不是单 tick 阶跃 | ordinal | 显著性 p<0.05 的首次出现时间存在，且该处跳变 ≤ 3σ 前驱波动 / 每 100 年一个切片 / 变点检测（PELT，惩罚项预注册） | **B** | `complex-systems-emergence` §2.5（Chelazzi & Lawrence 2026：新石器 β=0.051 p=0.727 → 铜石 0.097 p=0.427 → 青铜 0.246 p<0.001） | sealed_acceptance |
| P-SET-03 | 公共营造产出的标度指数 1+δ 超线性 | interval | 1+δ ∉ [1.00, 1.35] 失败 / 公共 Structure 的年建造量（Labour_mh）/ 同 P-SET-01 | **A** | `settlement-urbanization-spatial` §4.1（1.177，CI 1.028–1.327，n=48） | sealed_acceptance |
| P-SET-04 | **移动成本扰动响应**：运输成本参数 ×2 后 α 必须按理论方向移动 | conditional | \|Δα\| ≥ 0.02 且符号符合 `α = 2/(2+δ)` 类关系；α 完全不动 ⇒ 判定硬编码 | A（理论）/ **D**（阈值） | `complex-systems-emergence` M5 伪阳性对策；`emergence-verifiability` 7.1 L3 末条 | sealed_acceptance |
| P-SET-05 | rank-size 指数只做单边排除 | interval | α ∉ [0.4, 1.8] 报警；**α→1 永远不是目标** / 截断阈值必须随行，且报告 ≥3 个阈值下的敏感性带 / MLE + KS 定 x_min | A（散布）/ C（解释） | `settlement-urbanization-spatial` §4.2（MetaZipf：均值 1.025、中位 0.986、sd 0.282、40% 变异来自技术选择） | observation |
| P-SET-06 | **禁止把 rank-size 形状解读为政治整合** | neg | 任何报告中出现"α 下降 ⇒ 分裂"的推断即判方法错误 | **C** | `emergence-verifiability` F10（Altaweel 2015：中青铜碎片期 0.58，铁器帝国期 0.69，p<0.01，**方向与直觉相反**） | observation |
| P-SET-07 | 城市化率是输出且允许长期下降 | interval + existence | 前工业城市化率 ∉ [3%, 20%] 失败；**且必须存在至少一个 ≥200 年的下降段** / >2000 人口径 / 直接计数 | **A** | `economy-markets-trade` §4.5（中国 1102 年 11% → 1776 年 7%；长三角 25%→19%） | sealed_acceptance |
| P-SET-08 | 首位城市占总人口比例上界 | interval | > 3% 报警 / 最大聚落人口 / 总人口 / 直接计数 | **A** | `economy-markets-trade` §4.5（中国 1100 年 1.0% → 1400 年 1.4% → 1900 年 0.2%；西欧 1900 年 2.3%） | observation |

#### B. 战争与后勤（P-WAR）

| ID | 陈述 | 形状 | 口径三元组 | 证据 | 来源 | 归属 |
|---|---|---|---|---|---|---|
| P-WAR-01 | 战争规模分布重尾，指数落在均值/方差未定义的区间 | interval | α̂ ∉ [1.0, 3.0] 失败；**不得要求打中 1.53** / 规模 = 战斗死亡（Pop_up）/ Clauset 程序：KS 定 x_min + MLE + ≥2500 合成集 bootstrap，p ≤ 0.1 排除幂律 + 与对数正态/指数/拉伸指数/截断幂律做似然比 | A（方法）/ B（迁移） | `complex-systems-emergence` §2.4 §4.2 M7；`war-conflict-logistics` §4.7 | sealed_acceptance（**最低门槛，非正面证据**） |
| P-WAR-02 | **幂律免费性负对照**：打乱地理邻接后重跑，若同样的重尾指数依旧出现，该重尾不得作为成果 | neg | 打乱后 α̂ 的 95% CI 与原 CI 重叠 ⇒ 该幂律与地理机制无关 / 同上 / 同上 | **A** | `complex-systems-emergence` §2.3 §8.3（Marković & Gros 2014：任何把平均活动恒稳维持在界限内的动力系统统计上等价于 SOC 分支过程，因此幂律免费）；`emergence-verifiability` F10 第 5 条 | sealed_acceptance |
| P-WAR-03 | 会战伤亡不对称：败方显著高于胜方 | ordinal | 中位比值 ≥ 2 / 会战 = 单次接触结算 / 中位数 + bootstrap CI | **A** | `war-conflict-logistics` §4.5（CDB90 1600–1815 一手计算：胜方 8.8% / 败方 25.0% 中位） | sealed_acceptance |
| P-WAR-04 | 士气崩溃发生在低损失处，不是歼灭 | interval | 会战结束时败方累计损失的中位数 ∈ [5%, 30%] / 同上 / 中位数 | **A** | `war-conflict-logistics` §4.5（古典希腊 5%/14%；罗马 4.2%/16%；"前现代军队在损失达到 10% 或更早时就散架了"） | sealed_acceptance |
| P-WAR-05 | 野战军规模上界与后勤密度耦合 | conditional | 出现 > 80,000 人的野战军且沿途人口密度 < 7.7 人/km² 且无水运补给 ⇒ 硬失败（此条同时是 Gate 3） | **A** | `war-conflict-logistics` §4.3（地中海：常规 20,000 / 大军 40,000 / 异常 80,000，超过不可持续；全年不间断作战需 ≥7.7–9.7 人/km²） | sealed_acceptance |
| P-WAR-06 | 常备军占总人口的比例上界 | interval | 中位数 > 3% 报警 / 常备军 = 具名军职 Role 的持有者计数 / 直接计数 | **A**（但为 1816–1913 现代数据） | `war-conflict-logistics` §4.6（COW 一手计算：中位 0.72%/0.62%/0.57%，p90 1.31%；19 世纪峰值保加利亚 13.2%） | **observation**（现代数据，不得外推为前现代验收目标） |
| P-WAR-07 | 跨生态带边疆战争的屠城率显著高于同文化内部战争 | ordinal | 比值 ≥ 5（真实 63% vs 1.4% ≈ 45×）/ 屠城 = >10% 定居人口在一次占领中死亡 / 二比例检验 | **A** | `war-conflict-logistics` §4.8（Turchin 2010：G_adj=157, P≪0.0001） | sealed_acceptance |
| P-WAR-08 | 巨型政体与高机动性生态带边疆的空间关联 | ordinal | 峰值面积 >100 万 km² 的政体中，≥50% 的核心区在草原带 500 km 内（真实 >90%，我们只要方向） | A（真实值）/ **D**（阈值） | `war-conflict-logistics` §4.8（63 个巨型帝国中 57–59 个在草原边疆）；`state-formation` §2.3 | sealed_acceptance |

#### C. 国家形成与政治（P-STA）

| ID | 陈述 | 形状 | 口径三元组 | 证据 | 来源 | 归属 |
|---|---|---|---|---|---|---|
| P-STA-01 | 定居农业到"国家读数"的时滞是千年量级，且次生显著快于原生 | interval + ordinal | 原生 ∉ [800, 2500] 年报警；次生 ∉ [100, 1000] 年报警；**次生中位数 < 原生中位数**（这一条是序数，才是承重的）/ 国家读数 = `state-formation` §9.a 观测器的 `is_state` / 首次达成时间的分布 | A（中心值）/ **D**（加宽区间） | `state-formation` §2.10（原生 1300±570 年、次生 370±420 年）、§9 第 13 条（加宽是该简报自标 D 级）；§2.9（500 BCE 已有农业的地区 23% 到 1500 年仍无宏观国家；平均时滞约 2000 年） | sealed_acceptance（序数部分）/ observation（绝对值） |
| P-STA-02 | **允许缺席**：≥10% 的种子在 5000 年内不出现 `is_state=True` 的政体，且这不算失败 | interval（双边） | 比例 ∉ [10%, 80%] 报警；**比例 = 0% 同样报警**（说明世界被判据挤成了单一形态）/ 同上 / 二项比例 + Clopper–Pearson CI | **D** | `emergence-verifiability` F14 替代设计第 2 条（该红队自标 D 级）；`pseudo-simulation` F2 替代设计 | sealed_acceptance |
| P-STA-03 | 复杂酋邦级政体的寿命是几十年量级，不是几百年 | interval | 平均寿命 ∉ [20, 150] 年报警 / "复杂酋邦" = 控制层数 c≥2 且规模 s≥10 位点簇 / 均值 + bootstrap | **A** | `state-formation` §2.4（Gavrilets 2010：α=1 时 <55 年，α=2 时 <68 年） | sealed_acceptance |
| P-STA-04 | **继承稳定性的方差主导地位**（比较静力学）：扰动 τ ±50% 对政体寿命方差的响应，必须显著大于同幅度扰动人口/粮食参数的响应 | conditional | 方差响应比 ≥ 2 / τ = 首领平均在位年数 / 双因素方差分解（ANOVA），报告占比 | **A** | `state-formation` §2.4（Gavrilets 方差分解：τ 占复杂酋邦寿命方差 **55.5%**，α 19.9%，θ 8.6%；α 占最大政体规模方差 **39.8%**） | sealed_acceptance |
| P-STA-05 | 政体规模对到高机动性生态带前沿距离的梯度显著为负 | ordinal | 回归斜率显著 < 0（控制空间自相关，SAR）/ 距离 = 网络成本距离 / SAR 空间回归 | **A** | `state-formation` §2.3；`complex-systems-emergence` §6.1（草原距离是最强宏观地理预测因子；草原距离+农业古老度+高程解释 42% 方差） | sealed_acceptance |
| P-STA-06 | **功能主义前置条件必须弱**：灌溉/公共品/市场/货币/信息系统对复杂度的偏效应，必须弱于战争技术与农业古老度 | ordinal | 前者的标准化偏效应绝对值 < 后者 / 动态回归（差分方程，含自回归项）/ AIC 选模型，ΔAIC > 10 视为无支持 | **A** | `state-formation` §2.9（Turchin 2022：Infra/Irrigation/Cap/Market/Money/Info **全线无支持**；"农业+功能主义"模型 ΔAIC 23.19–62.65） | sealed_acceptance |
| P-STA-07 | **大国低税**：有效抽取率与政体面积负相关 | ordinal | 回归斜率显著 < 0 / τ_eff = 到达中枢的物质流 / 域内总产出 / 面板回归 | **A** | `economy-markets-trade` §4.6（19 世纪中国中央财政 ≈GDP 2%，同期西欧 8–12%；1780 年中国 3–4% / 法 9% / 英 12%）；`state-formation` §2.8 | sealed_acceptance |
| P-STA-08 | 复杂度 PC1 方差占比的**双边**判据 | interval（双边） | PC1 ∉ [40%, 90%] 失败：>90% ⇒ 机制退化为单驱动；<40% ⇒ 维度间无耦合 / 复杂度变量矩阵 = 观测器输出的 9 类特征 / PCA，报告碎石图 | **B** | `complex-systems-emergence` §2.15 §4.12（Seshat：414 社会、30 区域、51 变量，PC1 ≈75%）；`emergence-verifiability` 7.1 L2 表 | sealed_acceptance |

#### D. 人口与疫病（P-POP）

| ID | 陈述 | 形状 | 口径三元组 | 证据 | 来源 | 归属 |
|---|---|---|---|---|---|---|
| P-POP-01 | 长期人口增长率接近零 | interval | 任意 500 年滑窗的年均增长率 \|r̄\| > 0.3%/yr 报警 / 世界总 Pop_up / 对数线性拟合 | **B** | `cliodynamics-secular-cycles` §2.10（欧洲人口年增长率从 +0.4% 掉到 −0.3%；1650 年降至 1.05 亿低点） | sealed_acceptance |
| P-POP-02 | 危机死亡率重尾 | ordinal | 最大年死亡率 ≥ 10 × 中位年死亡率 / 区域级粗死亡率 / 分位比 | B（形状）/ **D**（倍数） | `epidemics-disease` §4.4（Givry 1348 ≈42%、Eyam 1666 ≈56%、Malta 1813 ≈4.6%、开罗 1801 ≈2%——同类事件跨两个数量级） | sealed_acceptance |
| P-POP-03 | **疫病不是人口调节器**（反平衡器诊断） | neg | \|corr(疫情起始时点, 人口相对趋势偏离量)\| > 0.1 ⇒ 存在隐性反馈，判失败 / 疫情起始 = 第一例本地传播 / Pearson + 块自助 | B（原则）/ **D**（阈值） | `epidemics-disease` §3.14 第 1 条 + §8.1（该简报称此为"本项目最危险的反模式"） | sealed_acceptance（**CI 级**） |
| P-POP-04 | **临界社区规模是涌现的，不是硬编码的** | conditional | 麻疹型病原体在连通社区规模 < 25 万时不得长期地方性存在（必须消退后再输入）/ 社区 = 连通分量的 Pop_up 和 / 流行持续时间的生存分析 | **A** | `epidemics-disease` §4.1（麻疹 CCS 25–50 万；高出生率环境 ≈75 万；腮腺炎 36.6–78.1 万）；§M3 | sealed_acceptance |
| P-POP-05 | 城市人口学惩罚 | ordinal | 城市粗死亡率 > 农村，且无移民补充时城市人口下降 | A（数据）/ **C**（urban graveyard 有实质争议） | `settlement-urbanization-spatial` §4.4（伦敦婴儿死亡 300–400‰ vs 偏远农村 <100‰）、§7.6（Sharlin 1978 主张是统计假象，Woods 2003 称"未解决的辩论"） | **observation** |
| P-POP-06 | 疫情来源 100% 可追溯 | existence | 无法追溯到具体（疫源地溢出 \| 跨斑块输入）事件及其 rng_key 的疫情数 = 0 | **B** | `epidemics-disease` §3.14 第 2 条 | sealed_acceptance（**CI 级**） |

#### E. 技术与扩散（P-TEC）

| ID | 陈述 | 形状 | 口径三元组 | 证据 | 来源 | 归属 |
|---|---|---|---|---|---|---|
| P-TEC-01 | 扩散前沿速度落在经验量级内 | interval | 前沿速度 ∉ [0.1, 5] km/yr 报警 / 前沿 = 首次采纳时间的等值线 / 距离–年代回归的斜率倒数 | **A** | `technology-innovation-diffusion` §4.1（欧洲新石器农业 0.6–1.3 km/yr；陶器走廊内 1.25/3.23，走廊外 0.25/0.46） | calibration |
| P-TEC-02 | **扩散是噪声主导，不是确定性波前** | neg | 地理模型对到达时间方差的解释力 r² > 0.6 ⇒ 扩散被做成了确定性波前，判失败 / 同上 / 最优地理模型的 r² | **A** | `technology-innovation-diffusion` §4.1 末段（"即使加了地形、生物群区走廊、两个独立起源、自由拟合的加速倍数，最好也只解释 36% 的到达时间方差"） | sealed_acceptance |
| P-TEC-03 | 扩散是不连续的，有千年级停滞 | existence | 相邻区域间到达时间间隔的分布中，必须至少有一个 ≥ 500 年的间隔 / 区域 = basemap 分区 / 直接计数 | **A** | `technology-innovation-diffusion` §4.2（东亚粟作相邻区域平均间隔约 1200 年；向东扩散无清晰时间–距离模式） | sealed_acceptance |
| P-TEC-04 | 生态走廊加速倍数 | interval | 走廊内/外速度比 ∉ [2, 15] 报警 / 走廊 = 生物群区连通带 / 双区段回归 | **A** | `technology-innovation-diffusion` §4.1（拟合值：欧亚走廊 5×、环地中海走廊 7×） | sealed_acceptance |
| P-TEC-05 | 技术可失传 | existence | 全程必须至少出现一次"某能力在某区域丢失 ≥100 年后重新获得" | B（机制）/ **D**（阈值） | `technology-innovation-diffusion` §3.5（四条失传通道）；`complex-systems-emergence` M10 与 §9 第 7 条（Turchin 让技术不可逆，"技术可失传"是该简报的 D 级扩展） | sealed_acceptance |

#### F. 经济（P-ECO）

| ID | 陈述 | 形状 | 口径三元组 | 证据 | 来源 | 归属 |
|---|---|---|---|---|---|---|
| P-ECO-01 | 粮价相关长度落在经验区间且随运输技术单调改善 | interval + ordinal | L ∉ [50, 2000] km 报警；且 L 对水运可达性单调递增 / ρ(d)=exp(−d/L)，对市场对回归 ln ρ 对 d / OLS，块自助 CI | **A** | `economy-markets-trade` §M10 §4.3（江苏 1742–95 L≈480 km；长三角 ≈430 km；法国 1756–90 ≈1650 km） | sealed_acceptance |
| P-ECO-02 | 价格冲击半衰期有前工业下界 | interval | 半衰期 < 6 个月 报警（前工业不可能这么快）/ Δp_it = β_i p_{i,t−1} + γ_i' f_t + ε；半衰期 = ln(0.5)/ln(1+β) / 面板 AR(1) | **A** | `economy-markets-trade` §4.3（华南 8→19→54→28 月；华北 13→34→64→47 月；1810 年中国是英格兰的 22–78 倍） | sealed_acceptance |
| P-ECO-03 | **人均产出长期不增长**（防文明加速主义） | interval | 任意 500 年滑窗的人均产出年增长率 > 0.15% 且无对应机制 ⇒ 失败；**允许长期下降** / 人均产出 = 总 kcal 等价产出 / 总人口 / 对数线性拟合 | **A** | `economy-markets-trade` §M12 §4.5（实际 GDP 年增长率北宋 0.90% / 明 0.35% / 清 0.58%，**人均**由 26.5 两 → 19.8 → 14.2 单调下降） | sealed_acceptance |
| P-ECO-04 | 市场不能消灭饥荒 | interval | 长途粮食贸易量 / 总粮食消费 > 10% 报警 / 长途 = 有效距离 > 300 km / 直接计数 | **A** | `economy-markets-trade` §M14 §4.4（清中期长途粮贸约 260 万吨/年 ≈ 1400 万人口粮，是西欧的约 10 倍，仍只占全国消费个位数百分比） | sealed_acceptance |
| P-ECO-05 | 贸易的距离弹性 | interval | ζ ∉ [1, 4] 报警 / 有效距离 = 多式联运广义成本 / 结构引力模型 | **A** | `economy-markets-trade` §4.4（古亚述有向 3.825、非有向 1.970；现代约 1–2） | sealed_acceptance |
| P-ECO-06 | **财富分布不应是干净幂律**（反向判据） | neg | Clauset 程序对财富分布**未能**排除纯幂律（p > 0.1）且似然比不偏好对数正态 ⇒ 可疑，判失败 / 财富 = 家户存量的 kcal 等价 / Clauset 程序 | **A** | `complex-systems-emergence` §2.4 §4.1（24 个经典数据集中 7 个被排除幂律，**其中包括财富**；对数正态 23/24 未被排除）；`emergence-verifiability` F10 第 2 点 | sealed_acceptance |

#### G. 长周期与危机（P-CLI）

| ID | 陈述 | 形状 | 口径三元组 | 证据 | 来源 | 归属 |
|---|---|---|---|---|---|---|
| P-CLI-01 | 政体寿命分布形状 | — | **不判定通过/失败。** 只报告我们的分布属于哪一族（指数 / 饱和危险 / 幂律），且**必须先跑考古可见性滤镜**再与真实数据比 | **C**（四个互相矛盾的结论） | `cliodynamics-secular-cycles` §2.9（Arbesman 2011 指数 τ≈220；Scheffer 2023 饱和危险，众数≈200，MOROS c=0.0065 h=67.3；Ciliberti 2025 指数 τ=298 KS p=0.71；Lu 2021 幂律；Wand 2024 指幸存者偏差）；`emergence-verifiability` F16 | **observation** |
| P-CLI-02 | 不稳定序列的功率谱成分 | — | **不判定。** 只报告代际（50–90 年）与世纪（150–350 年）成分的功率占比 | **C** | `cliodynamics-secular-cycles` §3.0(5) §7.2（Alexander 2016 英格兰主导波长约 79 年，多世纪周期"not evident"；Turchin 2005 说中国看不到代际节律）；§9 第 8 条自标 D 级 | **observation** |
| P-CLI-03 | 精英过度生产是可数比值，且是先导指标 | ordinal | `候选人数/空缺数` 在解体期前上升，且 t−1 的值对 t 的冲突预测力强于同期值 / 候选人 = 满足门槛的可枚举个体；空缺 = 具名职位槽位计数 / 滞后回归 + 样本外交叉验证 | **B** | `complex-systems-emergence` §2.13 §4.10（清代 PSI 与内战 R²=0.5, p=1.85e−5，t−1 最强）；`cliodynamics-secular-cycles` §3.0(3)、AP-14 | sealed_acceptance |
| P-CLI-04 | 气候→冲突必须经由人均粮食通道 | conditional | 控制人均粮食后，temp 异常对冲突的偏效应不显著 | **C**（Hsiang 2013 vs Buhaug 2014 对立；清代实证发现旱灾/饥荒对内战无显著滞后） | `cliodynamics-secular-cycles` §2.10 §7.6；`complex-systems-emergence` §6.3 第 2 点 | **observation** |

#### H. 元判据（P-MET）

| ID | 陈述 | 形状 | 口径三元组 | 证据 | 来源 | 归属 |
|---|---|---|---|---|---|---|
| P-MET-01 | 真实历史的率型宏观指标落在模拟集合的 5%–95% 分位内 | interval | 落在区间外 ⇒ 报警（不是失败，是调查触发）/ 只对预注册的**率型**量 / 经验分位 + 功效分析前置 | **D**（无文献先例） | `complex-systems-emergence` §8.11 与 §9 第 9 条（该简报明说这个标准是它自己推的）；`abm-methodology` §2.5（Rand & Rust："real world is a possible output"） | sealed_acceptance（**必须先过功效分析**） |
| P-MET-02 | 形态多样性 | interval（双边） | 跨种子的宏观形态聚类数 ≥ 3，且无任何一类占比 > 70% / 形态向量 = 观测器输出的制度向量 / HDBSCAN，min_cluster_size 预注册 | **D** | `emergence-verifiability` F14 替代设计第 3 条 | sealed_acceptance |
| P-MET-03 | 词表增长 K(t) 不饱和 | ordinal | 拟合 K(t)=K_∞(1−e^{−t/T})，要求 T > 2000 年 或 K_∞ 的 95% 置信下界 > 1.2·K(5000) / 通道集由 state schema 机械导出 / 每 500 年聚类一次 | **D** | `pseudo-simulation` S4 判别测试 2（该红队自标 D 级） | sealed_acceptance |
| P-MET-04 | 信念–事实背离度 > 0 且随信息基础设施改善而下降 | ordinal | 背离度恒为 0 ⇒ 信息边界未生效，硬失败 / 背离度 = InfoCopy 内容与 L0 对应事实的加权汉明距离 / 时间序列回归 | B（原则）/ **D**（形式） | `emergence-verifiability` F8 替代设计第 2 条 | sealed_acceptance（**CI 级**） |
| P-MET-05 | 不可解释事件占比有下界 | interval | 占比 < 10% ⇒ 因果库过完备，说明原因是被写上去的 / 不可解释 = 归因报告返回"不可归因" / 直接计数 | **D** | `pseudo-simulation` F1 替代设计 (d)（该红队自标 D 级；本文采纳其建议的 10%） | sealed_acceptance |
| P-MET-06 | 摘要覆盖率 C_7 的健康区间在中间 | interval（双边） | 重大事件 C_7 的**中位数** ∉ [0.3, 0.6] 报警：>0.9 ⇒ 存在解析捷径（按 Bedau 定义不是涌现）；<0.1 ⇒ 我们没有解释力 / C_7 = 前 7 条前因解释的概率质量 / 同种子重放 + 逐个消融 | **D** | `pseudo-simulation` F1 判别测试（该红队明说 0.3–0.6 是它编的，须在玩具世界标定） | sealed_acceptance |

**统计（机器生成，与表格逐行核对）**：51 条中目标归属为 `sealed_acceptance` 的 41 条（其中 P-STA-01 的绝对值部分归 observation）、`calibration` 2 条（P-SET-01、P-TEC-01）、`observation` 8 条。按**主证据等级**分布：**A 32 条、B 9 条、C 4 条、D 6 条**。四条 C 级全部在 observation（符合 §1.1 加载期检查规则 2）；另有 P-SET-05（A 散布 / C 解释）与 P-POP-05（A 数据 / C 争议）出于同样理由主动降级为 observation。

### 1.3 明确不进验收集的量，以及原因

| 量 | 为什么不进 | 出处 |
|---|---|---|
| 政体寿命分布形状 | 学界四个互相矛盾的结论（指数 τ≈220 / 饱和危险众数≈200 / 指数 τ=298 / 幂律），且有幸存者偏差假说；"连帝国寿命分布是什么形状这个最基础的问题，学界都没有共识" | `cliodynamics-secular-cycles` §2.9 §7.1；`emergence-verifiability` F16 |
| 世俗周期的存在与波长 | 英格兰 850–1873 的傅立叶分析主导波长约 79 年，多世纪周期"not evident"；且中国看不到代际节律 | `cliodynamics-secular-cycles` §7.2 |
| 语言分化树的形状 | 22 份简报中找不到任何可核验的经验散布，阈值只能是我们编的 | `emergence-verifiability` F16 第 4 条 |
| 思想运动的扩散、宗教内容的演化 | 同上 | 同上 |
| 前现代东亚的 Zipf 指数 | 检索**未找到**针对中国/东亚历史城市体系的 rank-size 专门研究 | `settlement-urbanization-spatial` §4.7 |
| settlement scaling 在中国考古数据上的值 | **真实空白**：找不到任何一篇把 Ortman/Bettencourt 框架应用于中国聚落数据的同行评议论文 | `settlement-urbanization-spatial` §4.7 §7.8 |
| 中国战争规模的幂律指数 | 找不到经过 Clauset 式严格检验的研究 | `complex-systems-emergence` §6.6 |
| 前现代分政体类型的动员率上限 | "文献未提供可用参数" | `war-conflict-logistics` §4.6 |
| 城市粮食腹地半径的具体公里数 | "文献未提供可用参数" | `settlement-urbanization-spatial` §4.7 |
| 前现代城市规模的物理上限 | "文献未提供可用参数" | 同上 |
| 气候→冲突的直接效应强度 | Hsiang 2013 vs Buhaug 2014 的核心对立；且清代实证中旱灾/饥荒对内战无显著滞后 | `cliodynamics-secular-cycles` §7.6 |
| urban graveyard 的强度 κ | Sharlin 1978 主张是统计假象，Woods 2003 称"未解决的辩论"；必须做成可调参数 + 敏感性分析 | `settlement-urbanization-spatial` §7.6 |

### 1.4 预注册的通过规则

```
family      := (release_tag, morphology_class)      # 家族划分在开跑前冻结
m           := |{p ∈ acceptance_set : p.morphology_class 匹配当前世界形态}|   # 预注册
raw_p[p]    := 该模式检验的原始 p 值（或对区间型判据：落在区间外的自助概率）
adj_p       := benjamini_yekutieli(raw_p, q = 0.10)   # BY 而非 BH：我们的模式高度相关

PASS(release) :=
      ( ∀ p ∈ acceptance_set, p.evidence == "A" :  adj_p[p] 不显著拒绝 )        # A 级零失败
  AND ( |{p : p.evidence == "B" ∧ 通过}| / |{p : p.evidence == "B"}| >= 0.80 )   # B 级 ≥ 80%
  AND ( ∀ p ∈ acceptance_set with form == "neg" : 未命中 )                       # 反向判据全部未命中
  AND ( conservation_audit_failures == 0 )                                       # L1 一致性零容忍
```

**配套的三条规则，缺一则通过规则无效**：
1. **m 在开跑前冻结。** 跑完之后新增的检验一律进 observation，不参与 FDR，不参与 PASS。
2. **失败清单比总分重要。** 报告必须首先列出未通过的模式清单，`abm-methodology` M2 的原话是"这比总分重要"。
3. **通过率不得随版本单调上升。** 若连续 3 个版本通过率单调上升，触发 Goodhart 审计（`emergence-verifiability` F13 的可观察症状之一）：抽查最近改动的 commit message 是否出现 `fix pattern battery` 类字样。

### 1.5 模式预算账本与封存机制

- 每条模式带 `views` 计数器。**每一次它被用于指导参数调整就 +1。** `views ≥ 3` 自动降级为校准集，永久移出验收集（`emergence-verifiability` F13 第 1 条）。
- `sealed = true` 的模式在 Phase 0 结束时封存：其 `predicate` 与阈值以加密形式存储，只在预注册的里程碑开封**一次**，**开封即作废**（之后进入校准集）。
- 验收集必须从"团队尚未读过的文献"中持续补充新模式，否则判别力单调衰减到零。**建议速率：每个里程碑补 ≥ 3 条，且必须来自本次未使用过的文献**［D 级］。

### 这一节禁止了什么

- 禁止点值判据。`predicate` 中出现 `==` 的模式加载即失败。理由：点值判据几乎总能被拟合，序数约束难得多（`emergence-verifiability` F13 第 4 条）。
- 禁止无口径三元组的模式。缺阈值/定义/估计方法任一项 ⇒ 拒绝加载。理由：Zipf 指数 **40% 的变异来自技术选择**（`settlement-urbanization-spatial` §4.2），无口径的指数值是无意义的。
- 禁止 C 级证据进验收集（`emergence-verifiability` F16 第 3 条）。
- 禁止 identity 型（非遍历）统计量进验收集；它们只能进多样性报告（F9 第 2 条）。
- 禁止把 α→1、τ≈250 年、PC1=75% 这类"打中某个历史数值"当成目标。全部改成单边排除或双边区间。
- 禁止在看到数据之后新增检验并计入 PASS。
- 禁止同一批模式同时充当训练信号与验收信号——POM 的三个标准用途里就包括逆向参数化（`abm-methodology` §2.4），因此这两种用途在数学上不可兼得（`emergence-verifiability` F13）。
- 禁止把"模式电池全绿"表述为"我们证明了涌现"。在 §2 的标定报告出来之前，全绿的信息量 ≤ 0（见 §0.2）。

---

## 2. 三个诱饵世界与判据标定报告

### 2.1 为什么这是 Phase 0 的第一交付物

`complex-systems-emergence` §9 第 18 条自述："**没有任何文献做过『剧情树能否骗过涌现度量』的研究**"，并把它列为纯推测。`pseudo-simulation` F6 由此提出的做法是唯一诚实的做法：**故意造假，看能不能抓住自己。**

顺序上这意味着一条反直觉的开发次序（`pseudo-simulation` F6 末段 + `complex-systems-emergence` 附录建议 1）：

> **先实现度量 → 再用假货把度量测一遍 → 然后才实现世界。**

成本论证：诱饵内核是玩具规模的（§10.6 的 CI 玩具世界），不需要跑 5000 年，也不需要真实东亚地形。它们共用同一张地图、同一套观测器、同一套判据代码。

### 2.2 三族诱饵世界的规格

所有诱饵世界与真内核共享：地图（CI 玩具世界的 600 格流域）、时间（300 世界年，nightly 3000 年）、观测器代码、判据代码、CBRNG 流布局、守恒审计。**唯一的差别在机制层。** 这是必需的——如果诱饵世界用了不同的观测器，标定结果不可迁移。

#### W1 族：剧情树世界（5 个变体）

| 变体 | 植入的作弊 | 对应金丝雀 | 应当被谁抓住 |
|---|---|---|---|
| **W1a 显式脚本** | `if pop > X and year > Y: spawn_state()`；宗教/货币同样由显式触发器生成，其余机制照常 | K1 脚本王朝 | 词汇表检查、读取集闭包、C_7 覆盖率、阶跃探测 |
| **W1b 被拆散的触发器** | 同一触发条件 `A ∧ B ∧ C` 拆成三个独立模块，每个单独都不充分，消融矩阵看起来非常健康 | （`emergence-verifiability` F7 指出这是消融**在数学上**抓不住的情形） | 归零脆性 ZB、部分可替代性 PS、跨种子形态雷同度、类型抹除 |
| **W1c 参数拟合** | 内核一行硬编码都没有，但两个全局系数被调到让宏观曲线好看（Anasazi 的 Harvest Adjustment 1.0 → 0.56） | K3 的参数侧 / L3 | 零模型 N0 支配测试、自由度审计、参数活性测试 |
| **W1d 事件表** | 一张 40 条的事件表 + 冷却时间 + 权重调度 | K4 事件表 | 词表增长测试 K(t)、密封清单测试、事件间隔分布的变异系数 |
| **W1e 存在性兜底 + PID** | `ensure_at_least_one_polity()` + 灭绝重生 + 一个把总人口拉回目标走廊的控制器（伪装成"迁移压力"） | K6 + K2 | 灭绝率诊断、GATED 清单、`--no-clamp` 模式、矩位移测试、方差诊断 |

**W1 族必须包含 W1b。** 只做 W1a 的标定是自欺：`emergence-verifiability` F7 明确指出消融证明的是必要性不是非脚本性，一个被拆成三份的硬编码触发器"消融矩阵看起来会非常健康"。**如果我们的判据体系只能抓住 W1a，它抓不住任何一个真正会发生在我们身上的作弊。**

#### W2：纯外生驱动世界

- 宏观节律**完全**由外生气候序列注入；agent 决策替换为随机基线；agent 层只起平滑作用。
- 这一条有强证据支持其必要性：Janssen 2009 对 Artificial Anasazi 的复现证明，一个**零 agent 行为**的纯外生承载力模型取得了只差 **10%（L1）到 50%（L2）** 的拟合，**且两个模型的最优参数完全相同**（Harvest Adjustment 0.56、Harvest Variance 0.4），原话是 "the agent-based model acted as a smoothing function"（`abm-methodology` §2.8；`emergence-verifiability` F6；`prior-art-postmortem` §1.1）。
- 对应金丝雀 K3。
- 应当被抓住的判据：零模型 N0 支配测试、外生序列置换检验（N5）、捷径检验 R²_shortcut、判据 P-TEC-02（扩散过于整齐）。

#### W3：纯噪声世界

- 机制骨架完整保留（同样的实体、同样的相位、同样的守恒审计），**全部因果耦合切断**：每个子系统只读自己上一 tick 的状态与自己的随机流，不读其他子系统。
- 这是伪阴性对照：任何在 W3 上**通过**的判据说明它不需要因果耦合就能满足，因此对"世界是否有内部结构"没有分辨力。
- 应当被抓住的判据：动力学独立性 `T(X→Y|E)`（W3 上应当趋于 0 但 σ(e) 也趋于 0——这正是 `complex-systems-emergence` M3 说的"低 T + 低 σ = 剧情树"的对偶情形）、过量熵 E、复杂度 PC1 方差占比（W3 上应当 < 40%）、市场整合相关长度。

#### K7：策展金丝雀（不是世界变体，是流程变体）

`pseudo-simulation` F6 表格里的 K7 是"内核干净，但只保留分布前 5% 的运行"。它必须在标定报告里出现，**因为它证明了一件事：唯一能抓住 L4（人类回路）的东西是流程留痕，不是任何度量。**

标定方式：跑 200 个健康内核种子，人为只把 P95 以上的 10 个交给判据体系，看**有没有任何一条判据变红**。预期答案是"一条都不会"。这个预期结果必须写在标定报告的第一页，作为"为什么必须有运行登记表（§8）"的实验依据。

### 2.3 判据标定报告的格式

文件：`validation/calibration_report_<kernel_hash>.md` + 机器可读的 `.json`。

**主矩阵**（每格三元组）：

| 判据 ID | W1a | W1b | W1c | W1d | W1e | W2 | W3 | 健康内核 |
|---|---|---|---|---|---|---|---|---|
| （例）`E-ABLATION-ZB` | `(FAIL, n*=12, 1.00)` | `(FAIL, n*=40, 0.92)` | `(pass, —, —)` | `(pass, —, —)` | `(pass, —, —)` | `(pass, —, —)` | `(FAIL, n*=8, 1.00)` | `(pass, —, α̂=0.02)` |

每格三元组含义：
- **第 1 项 `FAIL/pass`**：判据是否在该诱饵世界上失败（`FAIL` = 判据抓到了它，好事）。
- **第 2 项 `n*`**：**最小检出样本量**——需要多少个种子才能以 80% 功效检出。这是本报告最有工程价值的数字，它直接决定 §10 的算力分配。
- **第 3 项**：在该诱饵上的检出率（power），或在健康内核上的**伪阳性率 α̂**。

**准入判定（写在报告顶部，机器生成）**：

```
admit(C) :=
      ( ∃ w ∈ {W1a..W1e} : C 在 w 上 FAIL )       # 硬性：必须能抓住剧情树家族的至少一个变体
  AND ( C 在健康内核上的伪阳性率 α̂ <= 0.05 )       # 否则它会天天红，然后被忽略
  AND ( n*(C) <= N_ensemble = 200 )                # 否则它在我们的预算下是零判据
  AND ( C.power.status == "calibrated" )

若 admit(C) 为假：C 被移出验收集，写入 rejected_criteria.md，并附一行"它对我们要防的东西没有分辨力"。
```

**报告还必须包含的三张附表**：
1. **覆盖表**：每个诱饵世界被几条判据抓住。**只被 1 条判据覆盖的作弊类型 = 单点故障**，必须在报告里高亮（`pseudo-simulation` F6 验收规则第 2 条）。
2. **K7 页**：策展金丝雀的结果与"零条判据变红"的预期确认。
3. **被删判据清单**：`pseudo-simulation` F6 的原话——"**任何检测器，若对它所负责的金丝雀检出率为 0，就删除它，不要发布它。**" 被删的判据必须列出，因为它记录了我们试过什么、什么没用。

### 2.4 金丝雀套件是回归测试，不是一次性实验

每次内核大改后重跑全套诱饵世界，防止检测器在重构中悄悄失效（`pseudo-simulation` F6 验收规则第 4 条）。CI 配置：
- **PR 级**：W1a + W3 + 健康内核，玩具世界 300 年 × 20 种子，预算 ≤ 5 min。
- **Nightly**：全部 8 个诱饵（W1a–e, W2, W3, K7 流程模拟）× 200 种子，预算 ≤ 3 h。
- **里程碑**：全尺度诱饵世界（真实地图窗口，3000 年）× 50 种子。

**回归门**：`detection_rate[C][w]` 相对上一个基线下降超过 0.15 ⇒ 构建失败，理由必须写清是判据退化还是内核改好了（后者需要重新标定）。

### 这一节禁止了什么

- 禁止任何判据在未经诱饵标定的情况下出现在验收位置。
- 禁止只做 W1a 就宣称完成了标定。W1b（被拆散的触发器）是必需变体，因为它是消融在数学上抓不住的那一类。
- 禁止诱饵世界使用与真内核不同的观测器或判据代码——那样标定结果不可迁移。
- 禁止在报告中省略健康内核的伪阳性率。一个在健康内核上 30% 报红的判据，实际效果是训练团队忽略红灯。
- 禁止保留检出率为 0 的判据"以防万一"。它的证据量 ≤ 0（§0.2），保留它比删掉它更危险。
- 禁止把 K7（策展）当成技术问题来解决。它的唯一对策在 §8，是流程性的。
- 禁止在标定报告缺失时对外使用"我们证明了涌现"这一表述。

---

## 3. 零模型套件作为 CI 门槛

### 3.1 六个零模型

`prior-art-postmortem` 【致命 4】要求四个常设对照组，并明确写："**这条必须是 CI 门槛，不是评审习惯。**" `abm-methodology` M6 与 `emergence-verifiability` F3 各自追加了两个。合并为 N0–N5：

| ID | 零模型 | 实现方式 | 它检验什么 | 来源 |
|---|---|---|---|---|
| **N0** | 纯资源承载力（零 agent） | 只保留气候→产量→承载力→人口的解析链，删除全部 agent 决策与空间移动 | Anasazi 病：宏观曲线是否只是外生驱动的重述 | `prior-art-postmortem`【致命 4】1；`abm-methodology` M6；Janssen 2009（误差只高 10–50%） |
| **N1** | 决策随机化 | agent 决策替换为在同一合法动作集上的均匀抽样 | agent 行为是否有净贡献 | `prior-art-postmortem`【致命 4】2；`complex-systems-emergence` §8.5 |
| **N2** | 决策贪心最优 | agent 决策替换为单步效用最大化 | **反向检验**：更聪明是否让宏观更差 | `prior-art-postmortem`【致命 4】3；`complex-systems-emergence` §8.5（Madge et al.：贪心攻击使 R² 从 0.66/0.66/0.49 掉到 0.22/0.39/0.26，且草原起点的因果影响被完全抹平） |
| **N3** | 文化/制度/记忆冻结 | 全部 InfoCopy、Recipe 注册表、关系边在 t=0 后不可变 | 路径依赖是否真的承重 | `prior-art-postmortem`【致命 4】4 |
| **N4** | 地理邻接打乱 | 保留每格属性，随机重排 H3 邻接图（保持度分布） | 宏观模式是否只是地理的重述；同时是 P-WAR-02 的实现 | `emergence-verifiability` F3(b)、F10 第 5 条 |
| **N5** | 外生序列置换 | 气候序列做 (a) 时间反转、(b) 块状打乱、(c) 同自相关结构的 surrogate 替换 | 模式是否挂在特定外生序列的谱结构上 | `abm-methodology` M6 第 4 步（该简报自标：这三种形式是它从时间序列分析类推的，**没有在 ABM 文献中见到有人这样审计外生输入**，D 级） |

**N0/N1/N4 三者同时构成 §6 的 reference ensemble**（`emergence-verifiability` F3 建议的三个空模型）。这是一个刻意的复用：它让"荒诞度"的参考系和"零模型增益"的参考系是同一个东西，从而避免两套互不校准的基线。

### 3.2 合并门（CI gate M-NULL）

任何修改 `kernel/mechanisms/` 的 PR 必须附 `null_gain_report.json`：

```json
{
  "kernel_hash": "...", "mechanism_added": "M-TRIBUTE-CHAIN",
  "toy_world": "basin600_300y", "n_seeds": 200,
  "arms": {
    "full": { "pattern_pass": ["P-STA-03","P-ECO-01", "..."], "score": 0.62 },
    "N0":   { "pattern_pass": ["P-ECO-01"], "score": 0.31, "ratio_to_full": 0.50 },
    "N1":   { "score": 0.44, "ratio_to_full": 0.71 },
    "N2":   { "score": 0.39, "ratio_to_full": 0.63 },
    "N3":   { "score": 0.55, "ratio_to_full": 0.89 },
    "N4":   { "score": 0.20, "ratio_to_full": 0.32 },
    "N5":   { "score": 0.58, "ratio_to_full": 0.94 }
  },
  "newly_passed_vs_all_nulls": ["P-STA-03"],
  "effect_sizes": { "P-STA-03": { "delta": 0.41, "ci": [0.28, 0.53], "power": 0.86 } }
}
```

**门规则**：

```
MERGE_OK :=
      ( newly_passed_vs_all_nulls 非空
        OR 该机制引入了新的守恒律/一致性约束（L1 层，不需要统计证据） )
  AND ( ∀ n ∈ {N0..N5} : ratio_to_full[n] < 0.90 或 该输出被标注为 "外生驱动" )
  AND ( 全部 effect_sizes 的 power >= 0.80 )
```

**90% 规则的出处与后果**：`complex-systems-emergence` §8.4 的原话是"**若基线达到 90%，该机制没有解释力**"（该简报把它作为 M14 的判读规则给出，属 D 级阈值）。落地形式不是"禁止合并"，而是**永久标注**：

> 若 `N0.ratio_to_full ≥ 0.90`，则该机制所支撑的一切宏观输出，在全部文档、图表、对外表述中永久带上标签 `EXOGENOUS_DRIVEN`。这个标签由报告生成器自动注入，人不能手工去掉。

理由：Janssen 的教训不是"纯承载力模型不该存在"，而是"我们会把外生驱动的拟合当成 agent 行为的解释"（`abm-methodology` AP1，该简报列为**最高危**反模式）。标注比禁止更诚实，也更可执行。

### 3.3 零模型的实现约束（这是对内核架构的硬要求）

零模型不能是"另写一个模型"。它们必须是**同一份内核代码在不同开关下的运行**，否则：
- 两份代码会漂移（`complex-systems-emergence` §8.7：Madge et al. 发现 Turchin 2013 的论文与代码在 `ε_max`、`Δ` 与技术扩散机制上都不一致）；
- 差异会包含实现差异而不只是机制差异。

因此对 `spec-world-state` 的硬要求：

```rust
// kernel/mechanisms/mod.rs
pub struct MechanismSwitches {
    pub agents_enabled:       bool,   // N0
    pub decision_mode:        DecisionMode, // Normal | UniformRandom(N1) | Greedy(N2)
    pub culture_frozen:       bool,   // N3
    pub adjacency_shuffled:   Option<u64>,  // N4，值为置换种子
    pub exogenous_transform:  ExoTransform, // N5: Identity | Reverse | BlockShuffle | Surrogate
}
// 约束：这些开关只能在 t=0 读取一次并写入 run_registry；tick 循环内禁止读取。
// CI：AST 检查——MechanismSwitches 的任何字段不得出现在 tick 相位函数的读取集中。
```

最后一条约束（开关只在 t=0 读一次）是为了防止零模型开关本身变成运行时调节器［本文原创，D 级］。

### 3.4 零模型的算力成本

按 §10.6 的玩具世界规格，单次 300 年 ≤ 8 s。

| 层级 | 配置 | 算术 | 墙钟（16 核） |
|---|---|---|---|
| **PR 门** | 7 臂 × **50 种子** × 8 s | 2,800 s = 0.78 CPU-h | **≈ 3 min** |
| **Nightly** | 7 臂 × 200 种子 × 8 s | 11,200 s = 3.1 CPU-h | ≈ 12 min |
| **里程碑（全尺度）** | 7 臂 × 200 种子 × 1 h | **1,400 CPU-h** | 计入验证预算（§10.2） |

PR 门用 50 种子而不是 200，是为了守住 §10.6 的「PR 门总计 ≤ 5 min」预算；代价是 PR 级的效应量分辨率下降，因此 **PR 门只用于抓「增益为零」这种粗粒度失败，精细判定在 nightly**。［本文的取舍，D 级］

### 这一节禁止了什么

- 禁止把零模型当成"评审时讨论一下"的东西。它是 CI 合并门，不通过就不合并。
- 禁止零模型是独立实现的第二份代码。必须是同一内核的开关。
- 禁止零模型开关在 tick 循环内被读取（否则它就是一个运行时调节器）。
- 禁止在 `N0.ratio_to_full ≥ 0.90` 时仍把该输出表述为"由我们的机制解释"。标签由工具注入，人不能删。
- 禁止只跑 N0–N3 而跳过 N4/N5。地理与外生序列是本项目**最大的两次外生注入**（`pseudo-simulation` F4），不审计它们等于不审计最大的风险源。
- 禁止用"零模型跑不动"作为跳过的理由。若跑不动，说明 `T_run` 超预算，应当先修 §10。

---

## 4. 涌现认证协议

### 4.1 认证对象与认证的语义边界

**认证对象**：一个由观测器识别的宏观范畴 `C`（例如"控制层数 ≥3 且治理专门化 ≥0.5 的持久政体"）。注意 `C` 的名字由我们给，**它在内核中不存在**（`spec-world-state` D2/§3.1）。

**认证的语义**（必须写在每一份证书的第一行，逐字）：

> 本证书只授予**解释候选资格**（explanatory candidacy），不是"已解释"。

出处是 Epstein 2023 的逐字表述：`"generative sufficiency is a necessary but not sufficient condition for explanation"`，以及 `"Merely to generate is not necessarily to explain (at least not well) ... A microspecification might generate a macroscopic pattern in a patently absurd—and hence non-explanatory—way."`（`abm-methodology` §2.12，该简报标注读到 JASSS 全文）。

因此每份证书必须附两节：
- **"其他能产出同一现象的候选机制"清单**（multiple generators；Epstein 称之为 "embarrassment of riches" 而非尴尬）；
- **"要在它们之间做裁决需要什么新的微观数据或新的微观尺度实验"**。

### 4.2 六项判定 D1–D6

采自 `emergence-verifiability` 7.2，与 `abm-methodology` M7 合并去重。

| 判定 | 内容 | 可执行形式 | 阈值 | 证据 |
|---|---|---|---|---|
| **D1 随附性** | `obs_C` 是微观状态的纯函数，且位于内核之外，内核对它无任何数据依赖 | 构建期检查：`kernel` crate 不得 `use observer::*`；`obs_C` 的签名只接受 `&L0Snapshot` 且无内部可变状态 | 二值 | `complex-systems-emergence` §8.9（Ψ 与 T 都假设 `V_t = f(X_t)`；若 C 是脚本写入的字段，Ψ 会**异常地大**，度量给出伪阳性满分） |
| **D2 词汇表隔离** | 内核类型词汇表中不存在 `C` 的标签；`C` 的构件只能是原语 | `PRIMITIVE_REGISTRY` / `COMPOSITE_REGISTRY` 分层（`spec-world-state` §3.1）+ T-ERASE | 二值 | `abm-methodology` M7 第 1 段；`state-formation` §9.a（观测器每一项都是对已有状态的读取） |
| **D3 多重实现** | 跨种子的 `C` 实例在制度向量空间中的两两距离，其分布显著大于同一实例的时间自距离 | 能量距离两样本检验，p < 0.05 | p < 0.05 | `emergence-verifiability` 7.2 D3 |
| **D4 有必要机制、无充分机制、且机制间部分可替代** | 见 §4.3 的 ZB/PS | ZB < 0.95 且 PS 存在 | ［D 级待标定］ | `emergence-verifiability` F7（**第三项才是正面指纹**） |
| **D5 路径依赖** | 单点扰动（同种子，只翻转一次抽样）能显著改变 `C` 的出现时间与形态分布 | 相对**安慰剂零分布**的分位 ≥ 0.95（安慰剂协议见 `spec-causality`） | 分位 ≥ 0.95 | `emergence-verifiability` 7.2 D5；`causality-bookkeeping` F5（**必须有安慰剂，否则任意扰动都"有效"**） |
| **D6 前驱连续性** | `C` 的判定量在出现前有连续爬升的前驱轨迹 | 变点检测（PELT），要求出现处的跳变 ≤ 3σ 前驱波动 | 3σ ［D 级］ | `emergence-verifiability` F5 可观察症状 (b)、7.2 D6（"阶跃是触发器的指纹"） |

### 4.3 消融矩阵：为什么它不够，以及必须补什么

**先把限制写清楚**（`emergence-verifiability` F7，这是本节最重要的一句）：

> **消融证明的是必要性，不是非脚本性。** 一个硬编码触发器 `if A and B and C: spawn_state()` 在消融 A 时同样会失败，同样表现为"存在承重机制"。把触发条件拆成三个模块，消融矩阵看起来会非常健康。**消融与涌现之间没有逻辑蕴含关系。**

因此消融矩阵必须额外报告两个量，**而这两个量才是涌现的正面指纹**：

```
设 p_0 = P(C | baseline)，p_m = P(C | 机制 m 关闭)

归零脆性  ZB = max_m (p_0 − p_m) / p_0
部分可替代性 PS = ∃ 不相交的机制子集 S1, S2 使得
                 p_{S1}, p_{S2} ∈ [0.10·p_0, 0.80·p_0]
                 且 关闭 S1 与关闭 S2 之后出现的 C 实例，
                    其制度向量分布的能量距离检验 p < 0.05（形态不同）

健康区间（预注册，全部 D 级待标定）：
  - 至少 3 个机制满足 p_m <= 0.70·p_0      （确有承重机制）
  - 没有任何机制满足 p_m <= 0.05·p_0        （ZB < 0.95，无归零脆性）
  - PS 为真                                  （存在两条形态不同的生成路径）
```

**判读规则（预注册，`emergence-verifiability` 7.2 消融判读 + `abm-methodology` M7）**：

| 观察 | 判定 | 理由 |
|---|---|---|
| 关掉任一机制 `C` 都消失（ZB ≈ 1） | **标红：触发链嫌疑** | 这是硬编码触发器的指纹 |
| 关掉任何机制 `C` 都不变 | **标红：硬编码或外生驱动嫌疑** | Janssen 教训：纯外生承载力模型能达到 ABM 90% 的拟合 |
| 若干机制各自使 `P(C)` 显著下降但都不归零，且关闭后形态不同 | **通过** | 这是 Epstein multiple generators 的可测版本 |

**注意这条反直觉的结论**（`emergence-verifiability` F7 末段）：**"可部分替代"是涌现的正面证据，"处处必要"反而可疑。**

### 4.4 消融矩阵的报告格式

照 Turchin 2013 Table 1 的格式（`complex-systems-emergence` §4.6：消融无高程 R²=0.48、`ε_min=ε_max` R²=0.16、技术随机播种 R²=0.17），但**报告的是模式通过率矩阵而不是单一 R²**，并追加三列：

```
臂集合 = { baseline } ∪ { 单机制关闭 : m ∈ M } ∪ { 预先声明的 k 个二元组合 }
  |M| <= 20（硬上限，见 §10.5），k = 6（预先声明，用于抓互补性）
每臂 = N=50 种子 × NROY 参数 10 点 = 500 次长跑

列：
  臂 | 各模式的通过率 | P(C) 的频率值 | C 实例的形态多样性（制度向量成对距离中位数） | C 出现处是否为阶跃（变点检测）
```

**为什么必须做到二阶交互**：留一法的已知失效是——存在强互补性（两个前因单独关闭都无影响、同时关闭才有影响）时留一法给出全零（`complex-systems-emergence` M2 失效条件；`emergence-verifiability` A3）。这正是 W1b（被拆散的触发器）的数学形状。**k=6 个预先声明的二元组合是抓 W1b 的最低配置**［组合数为本文选择，D 级］。

### 4.5 多种子频率判据：把 `0 < p < 1` 写成可检验的形式

`abm-methodology` M7 第 3 段要求 `N ≥ 50` 个独立种子上 `0 < p < 1`（两端都要排除；该简报自述 N≥50 与这个判据都是它编的，D 级）。裸写 `0 < p < 1` 在 N=50 下不可检验（p=0 与 p=0.02 无法区分），因此改写为：

```
以 k = C 出现的种子数，N = 50：
  要求 Clopper–Pearson 95% CI 同时排除 0 与 1
  ⇔  2 <= k <= N − 2   （N=50 时即 2 <= k <= 48）

若 k ∈ {0, 1}：判"一次侥幸"，不予认证，但记入观察集（可能是稀有但真实的形态）。
若 k ∈ {N−1, N}：判"被写死的必然事件"，标红，转 §4.6 的阶跃探测与类型抹除复查。
```

**并且**：`p ≈ 1` 且跨种子路径几乎相同 ⇒ 直接标红。跨种子相似度用 D3 的能量距离检验。

### 4.6 三个非统计检查（因为消融在数学上不够）

1. **类型抹除测试 T-ERASE**：把所有 composite 标签替换为随机 UUID 后，用同一 `(state, seed, proposal_log)` 重跑，世界轨迹必须**逐位相同**。定义与实现在 `spec-world-state` §3.3。本规格追加两条：
   - **观察器侧同样要抹除**：把 `obs_C` 内部使用的类别名也置换，认证结论必须不变（否则我们的判据本身依赖名字）。
   - T-ERASE 必须是**每份证书的必跑项**，不是一次性检查。
   - 出处：`emergence-verifiability` F5 替代设计第 1 条，该红队标注 **［我的推断，无来源］**，理由是"它是纯工程手段，成本低，且失败信号无歧义"。
2. **内核 → 观察器单向依赖的构建期检查**：内核模块不得 import 观察器模块；观察器只能通过只读视图访问内核（`emergence-verifiability` F5 替代设计第 2 条）。
3. **阶跃探测**：对每个宏观判定量做变点检测，要求范畴 `C` 的出现处不是超过前驱波动 3σ 的单 tick 跳变（同上第 3 条；3σ 为本文取值，D 级）。

### 4.7 证书的数据结构

```toml
[[certificate]]
category_id      = "C-POLITY-STATE-READING"
category_def_ref = "observer/state_reading.rs@sha256:..."     # 观测器代码的内容哈希
kernel_hash      = "..."
param_hash       = "..."
n_seeds          = 50
nroy_points      = 10

[certificate.verdict]
D1_supervenience   = "pass"     # 构建期
D2_vocabulary      = "pass"     # PRIMITIVE/COMPOSITE 分层 + T-ERASE
D3_multiple_real   = { verdict = "pass", energy_distance_p = 0.003 }
D4_ablation        = { verdict = "pass", ZB = 0.71, PS = true, load_bearing_count = 5 }
D5_path_dependence = { verdict = "pass", placebo_quantile = 0.98 }
D6_precursor       = { verdict = "pass", max_jump_sigma = 1.9 }
frequency          = { k = 31, N = 50, cp_ci = [0.48, 0.76] }

[certificate.decoy_check]
# 同一套认证流程在 W1 家族上的结果——没有这一节的证书无效
w1a = "rejected"; w1b = "rejected"; w1c = "rejected"; w1d = "rejected"; w1e = "rejected"

[certificate.candidacy]
alternative_generators = [ "……", "……" ]                 # 必填，禁止为空
what_new_data_would_adjudicate = "……"                    # 必填
status = "explanatory_candidate"                          # 唯一合法值
```

`decoy_check` 一节是硬性的：**在 W1 家族上跑完同一套认证流程并报告它把 W1 打回去的成功率，做不到这一点，上面全部是自我安慰**（`emergence-verifiability` 7.2 末句，逐字）。

### 4.8 涌现度量的使用规则（Ψ / T / 幂律）

这三类度量都可以用，但**每一个单独都能被剧情树骗过，必须配对使用**（`complex-systems-emergence` 附录建议 3）：

| 度量 | 单独使用时的伪阳性 | 必须配对的东西 |
|---|---|---|
| 动力学独立性 `T(X→Y\|E)` ≈ 0 | **剧情树给出极低的 T**——脚本驱动的宏观变量确实不由微观决定 | 必须配 `σ(e)` 高（结构性前因占比，由重放测得）。**低 T + 低 σ = 剧情树** | 
| 协同信息 `Ψ⁽¹⁾ > 0` | 若 `V` 是脚本直接写入的字段，`Ψ` 会**异常地大** | 必须配"宏观变量是随附纯函数"的构建期静态检查（D1） |
| 聚落标度 `α ∈ [2/3, 5/6]` | 若占地规则里硬编码了 `A ∝ N^(2/3)` | 必须配移动成本扰动测试 P-SET-04 |
| 幂律通过 Clauset 检验 | **幂律是免费的**：任何把平均活动恒稳维持在界限内的动力系统统计上等价于 SOC 分支过程 | 必须配 N4（打乱地理）负对照 P-WAR-02；正面证据只能来自多指数自洽 + 标度坍缩 |

**转移熵的使用限制**（`complex-systems-emergence` §7.5 / §8.10）：James, Barnett & Crutchfield 2016 论证转移熵**不度量信息流**，可以高估流量或低估影响。因此我们**只使用 `T ≈ 0` 的条件独立性检验方向，不解释 `T` 的数值大小**。这条必须写进度量代码的注释里（该简报的原话）。

### 这一节禁止了什么

- 禁止把"我没写这条规则"当作涌现的证明（`abm-methodology` AP7）。
- 禁止只报消融矩阵而不报 ZB 与 PS。一个只有消融矩阵的认证抓不住 W1b。
- 禁止把"处处必要"当成好消息。它是触发链的指纹。
- 禁止在证书里省略 `alternative_generators` 与 `what_new_data_would_adjudicate`。空的候选清单 ⇒ 证书无效。
- 禁止单独使用任何一个涌现度量下结论。每一个都必须配对。
- 禁止解释转移熵的数值大小（"流了多少比特"）。只允许用 `T ≈ 0` 的检验方向。
- 禁止把 Bedau 弱涌现定义当成颁证依据——它在哲学上尚有争议且不可操作（`abm-methodology` §2.13，Baker 2010 的批评）。它只以"捷径检验"的形式进入（若存在解析捷径则不是弱涌现）。
- 禁止没有 `decoy_check` 一节的证书进入任何文档。

---

## 5. 事件合理性检查器

### 5.1 总原则（决定成败的一句话）

> **所有闸门的输入必须从世界快照重算，永不接受事件 payload 的自报。**

否则检查器验的是生成器写下的理由，而不是实际起作用的原因——那是 `abm-methodology` AP9（用 LLM 评估 LLM）的变形（`emergence-verifiability` 7.3 总原则，逐字）。

工程落地：闸门函数的签名只接受 `(&L0Snapshot at t⁻, EventCandidate{ actor_id, action_type, targets, rng_key })`，**不接受 payload 中的任何数值字段**。CI 用 AST 检查：闸门模块不得访问 `EventCandidate::payload`。

### 5.2 五闸门

#### G1 —— 前置条件充分性

```
fn gate_1(snap: &L0Snapshot, cand: &EventCandidate) -> GateResult {
    let pre: &[Predicate] = PRECONDITION_TABLE[cand.action_type];
    for p in pre {
        if !p.eval(snap) { return HardFail(G1, p.id); }   // 任一不满足即硬失败
    }
    Ok
}
```
- `Pre(e)` 的**资源/人力部分由守恒律自动导出**（不手写）；人工部分必须做**覆盖率审计**：`被至少一个 Pre 引用的 L0 字段数 / L0 字段总数`，逐版本报告，**不设阈值**（这个量不可自证）。
- **抓得住**：无中生有——没有军队的政体发动远征、没有铸币能力的政体发行支付物。
- **抓不住**：谓词集本身写少了。**这是不可自证的**，只能靠覆盖率审计缓解（`emergence-verifiability` 7.3 Gate 1）。

#### G2 —— 信息光锥

```
fn gate_2(snap, cand) -> GateResult {
    let d = cand.actor_id;
    for f in referenced_propositions(snap, cand) {          // 从快照重算，不读 payload
        let copy = snap.belief_store(d).find(f)?;           // 缺失即硬失败
        let path = copy.provenance_chain();                 // 信使/商队/俘虏/文书
        let t_min = path.cumulative_travel_time(&SPEED_TABLE, &snap.terrain);
        if t_min > snap.tick - f.origin_tick { return HardFail(G2, f.id); }
    }
    Ok
}
```
- **`SPEED_TABLE` 是 Phase 0 的前置交付物**：`emergence-verifiability` F17 的原话是"这是原则 4 唯一可机械执行的版本，Phase 0 必须先产出这张速度表，否则原则 4 只是一句愿望"。起点取 ORBIS（`settlement-urbanization-spatial` §4.3，已核验数值）：

| 通道 | 速度 (km/day) |
|---|---|
| 牛车 | 12 |
| 挑夫 / 重载骡 | 20 |
| 步行 / 驮兽 / 骡车 / 骆驼商队 | 30 |
| 常规私人车辆 | 36 |
| 加速私人车辆 | 50 |
| 骑马 | 56 |
| 无辎重急行军 | 60 |
| 快速马车 | 67 |
| **连续换马接力** | **250** |
| 河运顺流（民用） | 65（45–100 因河而异） |
| 河运逆流 | 10–30（多数 15） |
| 运河（双向） | 15 |
| 军用桨船 顺/逆 | 120 / 50 |

  **诚实标注**：这是罗马世界 ca. 200 CE 的地中海参数；`settlement-urbanization-spatial` §4.7 明确记录"中国历史道路/漕运的速度与成本参数，本次未取得可引用数值"，因此**这张表是借用的**，必须在文档里标 `BORROWED_MEDITERRANEAN`。
- **抓得住**：上帝视角泄漏（显式）。
- **抓不住**：LLM 通过训练语料"知道"而不显式引用（隐式泄漏）。缓解是**反事实盲测**：把 prompt 中的真实事实随机替换为等概率的假事实，若决策分布不变说明没泄漏，若显著改变说明该 agent 在用不该有的信息（`emergence-verifiability` F17 替代设计第 2 条，该红队标注 **［我的推断，无来源］**）。这条属 `spec-llm-boundary`，本规格只声明它是 G2 的必需补充。

#### G3 —— 资源与后勤可行性

```
fn gate_3(snap, cand) -> GateResult {
    let ledger = expand_resource_flows(snap, cand);   // 展开为逐步收支
    for step in ledger { if step.stock_after < 0 { return HardFail(G3, step.id); } }
    if cand.is_military_operation() {
        let need = daily_ration(units) * days;                       // 见下表
        let carry = pack_capacity(units);                            // 130 kg/驮骡
        let forage = forage_yield(route, snap, season);              // 见下表
        if need > carry + forage { return HardFail(G3, "logistics"); }
    }
    Ok
}
```

后勤参数（`war-conflict-logistics` §4.1–§4.3，全部为该简报的 `[二手核验]` 或 `[一手推算]`）：

| 量 | 值 | 等级 |
|---|---|---|
| 士兵日粮 | ≈1.0 kg 谷物/日（0.7–1.4） | A（二手核验，多来源） |
| 饮水 | ≈3 L/人/日 | A |
| 骡精料 / 无牧草时另加干草 | 2.25 / +4.5 kg/日 | A |
| 骑兵马（罗马配给 / 最佳放牧） | ≈7 / ≈4.5 kg/日 | A |
| 驮骡载重 | ≈130 kg | A |
| 样例军队（19,200 战斗兵 + 4,000 非战斗 + 9,800 牲畜）总耗 | **61,850 kg/日** | A |
| 单日行军（可长期维持） | 19–24 km/日；兵力翻倍降至 9.0–13.4 km/日（**规模惩罚约 −50%**） | A |
| 纵队长度（23,200 人 + 7,400 畜） | 10.65 km | A |
| 就地征收率 | 一个区域可食用存粮的 **5%–15%** | A |
| 秋收后维持紧凑军队所需人口密度 | ≥ **3.9 人/km²**；十月 ≥ **5.8**；全年不间断 ≥ **7.7–9.7** | A |
| 全年不间断 + 双倍军队 | ≥ **27 人/km²** | A |
| 野战军规模档位 | 常规 ≈20,000；大军 ≈40,000；异常 ≈80,000；**>80,000 不可持续** | A |
| 驮畜破产距离 D* | **231 km**（自带全部草料）/ **693 km**（沿途可放牧） | **D**（该简报的一手推算，C=130 kg, v=24 km/日） |

- **抓得住**：无后勤远征、超财政的常备军、超粮食半径的城市。
- **抓不住**：**并发违约**。必须由 tick 级守恒审计（A1/A2）在事件层之外补上。`emergence-verifiability` Gate 3 的原话：**这不是"检查器可以更好"，而是"逐事件检查在数学上不可能做到"。**

#### G4 —— 动机-收益残差

```
在动作被裁决之前落盘并哈希：
    U(a) = Σ_i w_i · u_i(a | belief_at_t⁻)
    候选集 A 必须包含 "什么都不做" 与 >= k 个可行替代（k >= 3）
    irrationality_bits(e) = −log2 P_softmax(a_chosen | U, τ)
```

**判据是分布性的，不是逐事件硬失败**——因为逐事件硬失败会把 agent 变成最优化器，而那样更不真实（`complex-systems-emergence` §8.5：贪心决策使 R² 从 0.66/0.66/0.49 掉到 0.22/0.39/0.26，且抹平草原起点的因果影响）：

```
D-G4-1: irrationality_bits 的全局分布在相邻世纪间的 KS 距离 < 0.10   ［D 级待标定］
D-G4-2: 不得被单个事件类型长期占据尾部：
        对每个事件类型 t，lift(t) = P(top-decile | t) / P(top-decile)
        要求 lift(t) < 2.0                                            ［D 级待标定］
        （若"战争"事件的残差系统性高于其他类型，说明 LLM 在战争上编故事）
D-G4-3: 权重 w_i 必须是 agent 的持久状态，有世界内来源（家族、教育、经历），
        不能每次由 LLM 现编——否则整个检查是循环的。
```

- **抓得住**：为戏剧性制造事件（作为分布异常，不是单例）。
- **抓不住**：事后合理化（缓解：效用分解在裁决前落盘并哈希；LLM 的自然语言理由是附件，不参与检查）。
- **抓不住**：**共享的系统性偏置**——所有 agent 的价值权重由同一个 LLM 生成时会共享它的偏置。缓解：人格来源审计 + N1 消融（把 LLM 换成随机基线，**若宏观模式变好则接线错了**）。

#### G5 —— 时间尺度下界

每个动作类型声明一个由物理过程决定的**最小完成时间下界**，并验证事件与其因果前驱的时间差不小于信息传播时间：

| 过程 | 下界的物理来源 |
|---|---|
| 军事行动 | 行军距离 / 速度表（19–24 km/日，规模惩罚 −50%） |
| 建造 | 工日 / 可动员劳力（`Labour_mh`） |
| 文书/教义传播 | 传播速度 × 识字率 |
| 制度代际更替 | 人口年龄结构（首领在位 τ = 5–20 年，`state-formation` §2.4） |
| 农业扩散前沿 | 0.1–5 km/yr（`technology-innovation-diffusion` §4.1） |

- **抓得住**：一年建成运河、三年长出官僚体系、一代人完成语言分化。
- **抓不住**：**过慢**（没有上界）。补充对称检查：若某过程的完成时间长期处于下界的 **10 倍**以上，说明它实际由别的瓶颈决定，机制归因写错了（`emergence-verifiability` Gate 5；10× 为该红队取值，D 级）。

### 5.3 跨事件审计层（缺了它前五道闸门都可以被绕过）

#### A1 —— tick 级守恒审计

`emergence-verifiability` F12 的判决是本项目最便宜的一条：**"纲领里一个字都没有提到守恒律"**，而它"完全不引用真实历史，因此是『合理』里最硬、最便宜、最该先做的部分"。

实现由 `spec-world-state` §2.5 给出（int64 精确相等 + 最大余数法分配）。本规格的验证侧追加：

```
每 tick 的 commit 相位末：
  ∀ substance s:  Σ_holders stock(s) + Σ_cells sink(s) + Σ_in_transit(s)
                  == prev_total(s) + Σ declared_sources(s) − Σ declared_sinks(s)
  同样对 Energy_kcal 与 Pop_up。
  不相等 ⇒ 硬中止（不是警告），打印第一个不平衡的 (substance, holder, tick, phase)。
```

**验证侧的三条追加规则**：
1. **守恒审计的失败不允许被 GATED 豁免。** 它不在 §7 的例外程序覆盖范围内。
2. 每个 `declared_source` / `declared_sink` 必须在 `SOURCE_SINK_REGISTRY` 中注册，注册项包含物理解释。**未注册的源汇项 = 构建失败。** 这防止用"其他"项吸收误差。
3. 审计必须在 `--spike` main 里也跑（§10.7），否则最小可跑管线会漂移。

#### A2 —— 并发占用检验

`emergence-verifiability` F12 指出的合成谬误：每座城市单独在粮食半径内，但它们共享同一片腹地。

```
每 tick：对每种共享资源建立占用矩阵 Occ[资源单元][占用者] = 占用量
  ∀ 资源单元 u:  Σ_o Occ[u][o] <= capacity(u)
  违反 ⇒ 硬中止（这是 bug，不是"不合理"）
共享资源清单（封闭，加一项 = 内核版本变更）：
  格内可耕地、水权（同一水系上下游）、放牧地、林地、劳动时间预算、
  同一片腹地的粮食供给、同一条路径的通行能力、同一片渔场
```

#### A3 —— 链式不可能性账

```
luck_bits(e) = Σ_{draw ∈ minimal_sufficient_antecedent_set(e)} −log2 P(realized | dist at draw time)

年度总运气预算 L(t) = Σ_{e in year t} luck_bits(e)
  性质：E[L(t)] ≈ 该年注入的总熵 H(t)，因此 L(t)/H(t) 应当稳定在 1 附近。
  检查 1：|L(t)/H(t) − 1| 的滑动均值漂移 > 0.2 ⇒ 抽样实现有 bug。   ［D 级］
  检查 2：单个事件 luck_excess(e) = luck_bits(e) − median(同类事件)
          > 20 bits（≈ 10^-6）的事件必须在报告中显式列出，不得静默。 ［D 级］
```

**这把纲领第 7 条变成可执行的**（`emergence-verifiability` A2），并且与 §6 的 `surprise_bits` 是两个不同的量：`luck_bits` 度量"这段历史需要多少比特的运气"（相对**内核自己声明的分布**），`surprise_bits` 度量"相对参考集合有多罕见"。

#### A4 —— 归因残差 σ(e)

- `σ(e)` **只能由重放测得，schema 里不存在自报字段**。`emergence-verifiability` §6 第 2 条的原话："字段不存在比『约定不使用』强"。
- 留一法的已知失效（强互补性下全零）要求**至少做到二阶交互**（`complex-systems-emergence` M2 失效条件）。
- 具体协议、安慰剂对照、功效预算属 `spec-causality`；本规格只声明：**没有安慰剂零分布的 σ(e) 不得进入任何合理性判断**（`causality-bookkeeping` F5）。

### 5.4 这套检查器整体抓不住什么（必须写进文档）

`emergence-verifiability` 7.3 末节给了 5 条，本规格追加 3 条：

1. **谓词集不完整** —— 不可自证。只能靠覆盖率审计缓解。
2. **世界本体本身错误** —— 如果我们的经济学模型错了，所有账都平，世界仍然荒谬。这是检查器的上限，只能靠 L3 条件性判据（P-STA-04/06/07、P-SET-04、P-ECO-01）从外部抓。
3. **分布层面的荒谬** —— 每个事件都合理，整体历史却毫无结构（或只有一种模式）。逐事件检查对此**完全失明**。只有 §1 的模式电池能抓。
4. **LLM 的系统性风格偏置** —— 更长、更礼貌、更善表达、过度合作（Generative Agents 作者自述其 agent "excessive cooperation, agreeing to requests even when they conflicted with their established interests"，`abm-methodology` §2.18 / `prior-art-postmortem` §1.14）。只能靠 N1 随机基线消融抓。
5. **被拆散的触发器** —— 每个闸门都通过，因为触发条件写在机制里而不是事件里。只能靠 T-ERASE 与 §4.3 的 ZB/PS 抓。
6. **［本文追加］人类回路的选择偏置** —— 全部闸门都在单次运行内部生效，看不见"我们跑了 400 次只留了 1 条"。只能靠 §8。
7. **［本文追加］闸门参数本身被拟合** —— 后勤门槛、时间下界这些参数如果被反复调到"让世界跑得动"，闸门就变成了通行证。缓解：这些参数全部进 §8.4 的三分类账，且 `aesthetics` 类改动 ≥2 次即污染下游结论。
8. **［本文追加］规则先验 π 被我们自己编排** —— 若 `π` 让继承危机在王朝第三代高发、宗教运动在瘟疫后高发，那么 G4 的残差恒为零，**全部污染指标满分通过，而这个世界是被完全编排的**（`llm-storytelling` F7）。缓解：`π` 必须被拟合不能被撰写；无外部数据的量用最大熵先验；`justification_class == 叙事` 的允许数量为 0（§8.5）。

### 这一节禁止了什么

- 禁止任何闸门读取事件 payload 的自报数值。闸门只接受快照 + 候选动作的类型与目标。
- 禁止把 G4 做成逐事件硬失败。那会把 agent 变成最优化器，而实证显示那样宏观更不真实。
- 禁止 `σ(e)` 以字段形式存在于 schema 中。
- 禁止用"其他/杂项"源汇项吸收守恒误差。未注册的源汇项即构建失败。
- 禁止守恒审计使用"误差 < ε"的软形式（`spec-world-state` §2.5 已禁；本规格重申，因为浮点下这个等式永远不成立，于是它就抓不到真正的 bug）。
- 禁止守恒审计失败被 GATED 豁免。
- 禁止把 `SPEED_TABLE` 的地中海来源隐去不标。
- 禁止在没有安慰剂零分布的情况下报告任何 `σ(e)` 或反事实结论。
- 禁止让 LLM 或人的直觉裁决"这个事件在逻辑上成立"。合理性判定必须是机械的（`pseudo-simulation` S12：LLM 裁判对 L1 作弊的**检出力是负的**——手写规则产生的事件在 LLM 看来"完全说得通"，而真涌现的怪事会被判为"缺乏合理性"）。

---

## 6. 纲领第 7 条的可计算改写

### 6.1 裁决：两个红队方案不是同一个量，必须分开命名、分开用途

红队给了两个互补方案：
- `emergence-verifiability` F3：`surprise_bits(e) = −log2 P(e | 参考集合)`，`explanation_bits(e) = log2[P(e|完整前因)/P(e|参考集合)]`，可执行版本 `explanation_bits ≥ surprise_bits − τ`；参考系是**显式声明、版本化的 reference ensemble**（既不是真实历史，也不是本次运行）。
- `mandate-contradictions` F2：`absurdity(e) = −log P(该事件所涉机制组合 | 此前历史中的机制共现分布)`，即**机制组合的新颖度**，参考分布是世界自己的历史。

**裁决：两者都要，但它们回答的是相反方向的两个问题，因此必须分开命名并分别使用。**［本文原创的综合，D 级］

| 量 | 定义 | 参考系 | 方向 | 用途 |
|---|---|---|---|---|
| `novelty_bits(e)` | `−log2 P(mech_combo(e) \| 此前历史的机制共现分布)` | **世界自己的历史**（内生） | **下界**：我们希望它不饱和 | 防"世界一定会平庸"（`mandate-contradictions` F2 的失败机制） |
| `surprise_bits(e)` | `−log2 P(e \| reference ensemble)` | **显式声明、版本化的 reference ensemble** = N0（纯承载力）+ N1（随机决策）+ N4（打乱地理）三个零模型的输出 | 只决定**报告篇幅** | 度量"我们的机制相对于三个廉价解释多做了什么" |
| `explanation_bits(e)` | `log2[P(e \| 完整前因) / P(e \| reference ensemble)]` | 同上 | 必须**匹配** `surprise_bits` | 防"无缘无故"（`emergence-verifiability` F3） |
| `luck_bits(e)` | `Σ −log2 P(realized draw)`（§5.3 A3） | **内核自己声明的分布** | 报告 + 尾部列举 | 度量"这段历史需要多少比特的运气" |

**为什么必须分开**：`mandate-contradictions` F2 指出，第 7 条的措辞（"罕见""违反常识"）指向的是**数值尾部**，而"现实历史中从未出现过的文明形态"只能来自**组合新颖**。如果我们只实现 `surprise_bits`，工程投资会全部落在"扩大随机分布的尾部"和"给稀有事件加审查"上，而世界会平庸；如果只实现 `novelty_bits`，我们失去了"不能无缘无故"的判据。

### 6.2 三个量的可执行定义

```
# --- novelty_bits：组合口径 ---
mech_combo(e) := 排序后的机制 ID 多重集，取自 e 的最小充分前因集所触及的机制
                （由读取集闭包机械导出，不由事件模板自报）
共现分布 :=  在 [t − W, t) 窗口内出现过的 mech_combo 的经验分布，
             加 Krichevsky–Trofimov 平滑（避免零概率）；W = 500 世界年 ［D 级］
novelty_bits(e) = −log2 P̂(mech_combo(e))

派生的世界级指标：
  novel_combination_rate(t) = 单位时间内首次出现的 mech_combo 数
  验收：novel_combination_rate 随模拟时间**不饱和**（拟合饱和曲线，时间常数 > 2000 年）
  出处：`mandate-contradictions` F2 替代设计第 3 条（"这是一条比『是否出现了荒诞事件』
        可靠得多的判据，因为它不能靠调大方差刷分"）

# --- surprise_bits / explanation_bits ---
reference_ensemble := { N0, N1, N4 } 的联合输出，版本化为 REF_ENSEMBLE_V1，
                      内容哈希写入 DECISION-REGISTER
P(e | ref) := 在参考集合的 M 次运行中，同一时空窗口内出现"同型事件"的经验频率
              同型 = 状态差分向量落在同一个 HDBSCAN 簇（簇模型也版本化）
              M >= 200；P 的下界 clip 到 1/(M+1)（这是估计器的表示下界，不是行为 clamp）
P(e | 完整前因) := 用固定种子重放 + 逐个关闭前因测得（`complex-systems-emergence` M2 的 σ(e) 思路）
                   **不得由事件模板自报**

第 7 条的可执行版本：
  explanation_bits(e) >= surprise_bits(e) − τ,   τ = 4 bits  ［D 级待标定］
```

**τ = 4 bits 的含义**：允许一个事件的解释力比它的意外度低 16 倍。这个数字没有来源，必须在玩具世界与 W1 家族上标定：**在 W1a 上，脚本事件的 `surprise_bits` 高而 `explanation_bits` 低（因为它的"前因"关掉后事件照常发生），所以这条不等式应当在 W1a 上失败。若不失败，τ 取小。**

**顺带的收益**（`emergence-verifiability` F3 末段）：这条改写把纲领第 9 行的"不能因为『这样更有戏剧性』而发生"变成可计算的——**戏剧性事件的特征就是 `surprise_bits` 高而 `explanation_bits` 低。**

### 6.3 审查门槛对称化（这条比不等式本身更重要）

`pseudo-simulation` S1 判定第 7 条是"一台把世界推回真实历史的棘轮"：罕见结果 → 高门槛 → 更容易被判"证据不足" → 我们去改机制 → 该类结果频率下降；寻常结果 → 低门槛 → 无人审查 → 保留。**输出分布被系统性推向真实历史，与第 8 条直接相反。**

第三重伤害（该红队的原话）：**"隐藏剧情树最可能产出符合我们预期的东西——因为它是我们写的。剧情树的产物一定落在『寻常』那一侧，永远不会触发第 7 条的审查。第 7 条是一台自动化的确认偏误机。"**

因此：

```
规则 S-1（审查抽样）：因果链审计按 significance(e) 分层随机抽样，
                     **与 surprise_bits / novelty_bits 完全无关**；
                     每批必须包含 >= 50% 的"寻常"事件（significance 中位数以下）。
规则 S-2（门槛对称）：罕见结果与寻常结果适用**同一套**因果验收程序
                     （读取集闭包、σ(e)、安慰剂对照、五闸门）。
规则 S-3（篇幅≠证据）：surprise_bits 只决定**对外展示时的叙述篇幅**，
                     因为读者缺少先验。**篇幅要求不等于证据要求。**
```

规则 S-3 的措辞逐字采自 `pseudo-simulation` S1 替代设计第 3 条。

### 6.4 「荒诞度禁止成为运行时变量」的 lint 规则

`pseudo-simulation` S1 替代设计第 1 条："**荒诞度绝不可以是运行时变量。内核中不得存在任何计算『这个结果有多反常』并据此调整概率的代码。**" `mandate-contradictions` F2 第 2 点："禁止把 `absurdity` 作为运行时变量喂回任何决定『是否允许』的地方——写成 lint 规则。"

三层执行，逐层加强：

```
L-ABS-1（模块层，构建期）
  novelty_bits / surprise_bits / explanation_bits / luck_bits / significance
  这五个符号只能在 observer crate 中定义。
  kernel crate 的依赖图中不得出现 observer。
  检查方式：cargo tree / 构建脚本，二值。

L-ABS-2（数据流层，运行期 --audit 模式）
  observer 的所有返回值打污点标记（taint bit 随值传播）。
  任何被污点标记的值到达 kernel 的写入路径（L0 字段赋值、RNG 抽样的分布参数、
  Gumbel-max 的候选集构造、动作合法性判定）⇒ **运行时中止**，打印污点传播链。
  这比 import 检查强，因为它抓得住"通过配置文件/查表/序列化绕过模块边界"。

L-ABS-3（行为层，最强，成本几乎为零）
  **荒诞度置换不变性检验（T-ABS）**：把 observer 计算出的全部 absurdity 类值
  替换为同分布的随机数后，用同一 (state, seed, proposal_log) 重跑，
  世界轨迹必须**逐位相同**。
  与 spec-world-state §3.3 的 T-ERASE 同构，可复用同一套测试脚手架。
  ［本文原创，无来源，D 级］——但它是纯工程手段，失败信号无歧义。

L-ABS-4（叙事节拍变量禁令）
  以下变量禁止出现在任何触发器、规则先验 π、LOD 调度器、should_call_llm() 中：
    "距上次大事件已 N 年"、"这个王朝已经 K 代了"、"这个文明太平稳了"、
    "本世纪事件数"、"叙事张力"、"关注度"、"戏剧性"
  这些是伪装成工程条件的剧情树。
  出处：`llm-storytelling` F7 替代设计第 3 条；`pseudo-simulation` S8（LOD 分配规则
        只能引用物理/信息量，禁止引用任何"重要性/戏剧性/关注度"变量）。
```

### 6.5 与 significance 的关系（跨规格接口）

`significance(e)` 由 `spec-causality` 定义（要求：只由状态变化量算，与事件类型完全解耦）。本规格对它的**唯一**要求是：

- `significance` 与 `surprise_bits` 必须是两个不同的量，且审查抽样只用 `significance`（规则 S-1）。
- `significance` 同样受 L-ABS-1/2/3 约束：它是观察层量，内核对它零可见性。
- LOD 调度器不得读取 `significance`（`pseudo-simulation` S8 判别测试 1；`spec-world-state` §2.4 已把 LOD 相关字段列入黑名单）。

### 这一节禁止了什么

- 禁止用单一的"荒诞度"标量。三个量分开命名、分开用途，混用即概念错误。
- 禁止把真实历史当作 `surprise_bits` 的参考分布（读法 A 会把真实历史变回软性剧情模板）。
- 禁止把本次运行自身当作 `surprise_bits` 的参考分布（读法 B 会让自洽的荒诞世界永不荒诞，并奖励单调性）。
- 禁止让 `surprise_bits` 影响证据门槛。它只决定报告篇幅。
- 禁止按稀奇程度抽样审计。抽样只按 `significance` 分层，且每批 ≥50% 寻常事件。
- 禁止内核中存在任何计算"这个结果有多反常"并据此调整概率的代码（三层 lint 执行）。
- 禁止在触发器、π、LOD 调度器、`should_call_llm()` 中引用叙事节拍变量。
- 禁止 `P(e | 完整前因)` 由事件模板自报。它只能由固定种子重放测得。

---

## 7. 《反剧情树宪章》

### 7.1 宪章的地位

本节是一份**可被 CI 执行的章程**，存于 `charter/anti_plot_tree.toml`，与代码同版本化。修订需要两名签字人，签字记录进 `DECISION-REGISTER.md`。

出处：`pseudo-simulation` S3 判定"纲领没有禁止目标导向的调节机制——这是最大的空白"，并给出九类形态；本节把那张表变成 grep 模式与 lint 规则（该红队替代设计第 1 条）。

**实证支撑（不是假想）**：Stonedahl & Wilensky 2010 在 Artificial Anasazi 里发现的两个 bug 都属这一类，且**在一个被广泛引用、被多次复现的已发表模型里存活了十年**（`abm-methodology` §2.8 / AP5 / AP6）：
- `set quality ((random-normal 0 1) * harvestVarianceLocation) + 1.0` 后接 `if (quality < 0) [set quality 0]` —— 一个纯 clamp，导致**增大方差的同时抬高了均值**，所有关于"波动性 vs 平均水平"的结论因此为伪；
- `HarvestVarianceYear` 初始化后从未被引用（死参数）。

### 7.2 九类禁用机制

| # | 形态 | 典型写法 | 常见借口 | 实际做了什么 | 检测方式 |
|---|---|---|---|---|---|
| 1 | **clamp** | `max(0,x)`、`clip(m,0,1)`、`saturating_*`、`wrapping_*` | 防止发散 | 制造隐式吸引子；**并且污染均值** | AST：状态量上的 min/max/clamp/saturating/wrapping |
| 2 | **份额归一化** | 强制求和为 1 | 概率必须归一 | 隐藏了"绝对水平本该变化" | AST：对非概率量做 `x / sum(x)` |
| 3 | **拒绝采样** | `while not valid(s): resample()` | 保证状态合法 | 对结果做过滤 = 条件化 | AST：循环体内含 RNG 抽样且循环条件依赖抽样结果 |
| 4 | **世界初始化重生成** | `while arable < θ: regen_map()` | 保证世界可玩 | 只在"文明可能发生"的世界里采样 | AST + 运行期：`basemap` 生成函数被调用 >1 次 |
| 5 | **自适应速率控制器** | PID / 把变量拉回区间的反馈 | 数值稳定 | **字面意义的 PID = 字面意义的剧情树** | AST：任何读取 `target − current` 并据此改速率的表达式 |
| 6 | **灭绝兜底** | `if pop < 10: respawn_band()` | 避免空世界 | 取消了灭绝这个结局 | AST + 运行期：Pop_up 源项在无出生的情况下为正 |
| 7 | **事件冷却时间** | `event.cooldown = 50y`、`next_allowed_tick` | 避免刷屏 | 这是节奏设计 = 叙事 | 字段黑名单（`spec-world-state` §2.4 已列） |
| 8 | **存在性保证** | `ensure_at_least_one_polity()`、`min_polities` | 后续模块需要 | 直接把结论写死 | 字段/函数名黑名单 + 运行期：某观测量的下界恒被满足 |
| 9 | **隐式求解器** | 半隐式/全隐式积分 | 大步长稳定 | 静默阻尼掉本该发生的崩溃振荡 | 代码审查 + **步长减半不变性测试**（`spec-world-state` §5.5，必须在崩溃期窗口上做） |

### 7.3 GATED 注释规范

确实存在合法例外（例如数值表示边界）。例外必须显式、可计数、会过期：

```rust
// GATED(
//   id       = "G-0042",
//   kind     = "clamp",                       // 九类之一，或 "numeric_representation"
//   reason   = "Gumbel 抽样中 u 到 [2^-32, 1-2^-32] 的裁剪，是浮点表示边界不是行为边界",
//   evidence = "spec-world-state §2.4 clamp 例外程序第 3 条",
//   ticket   = "CS-118",
//   review   = ["reviewer_a", "reviewer_b"],  // 必须两人
//   expires  = "kernel-v0.7",                 // 到期版本，过期即构建失败
//   counter  = "gated_g0042_fires",           // 触发计数器名，必须存在
//   alarm    = 1e-9                           // 每次抽样的触发率上限，超过即报警
// )
```

**规范的四条硬性要求**：
1. **每一处必须带审批注释。** 无注释的九类模式命中 = 构建失败。
2. **每一处必须记账。** 触发时写 `invariant_violation(var, cell, tick, magnitude)`；触发率超过 `alarm` 视为**机制缺陷**（模型在该区域外推失败），**必须改机制，不得加 clamp**（`pseudo-simulation` S3 替代设计第 3 条）。
3. **每一处必须会过期。** `expires` 到期后构建失败，强制复审。
4. **计数只降不升。**

```
charter/gated_baseline.toml:
  [counts]  clamp = 3;  normalize = 0;  reject_sample = 0;  world_regen = 0
            rate_controller = 0;  extinction_floor = 0;  cooldown = 0
            existence_guarantee = 0;  implicit_solver = 0

CI 规则：GATED_COUNT[kind] <= baseline[kind]，否则构建失败。
        baseline 文件**只能被下调**；上调的 commit 自动失败，
        除非同一 commit 包含宪章修订记录与两名签字人（脚本校验签名）。
```

### 7.4 配套的四项常设检查

1. **`--no-clamp` 模式**：定期跑（nightly），允许世界真的崩溃/发散，**把崩溃率作为报告指标**（`pseudo-simulation` S3 替代设计第 4 条）。若 `--no-clamp` 下崩溃率显著高于常规模式，说明常规模式里的 clamp 在承重。
2. **矩位移测试**（`abm-methodology` M9 第 2 条，CI 级）：任何被声明为"离散度/方差/噪声幅度"的参数，改变它时**被它调制的量的均值不得显著移动**。这条测试直接消灭 `HarvestVarianceLocation` 类 bug。
3. **参数活性测试**（`abm-methodology` M9 第 1 条，CI 级，**构建失败级别**）：对每个声明参数取两个远离的合法值，跑 R 次重复，用双样本检验判断是否有任何被监控输出的分布发生变化。若没有 ⇒ 死参数 ⇒ 构建失败。这条直接消灭 `HarvestVarianceYear` 类 bug。
4. **步长减半不变性测试**（`spec-world-state` §5.5 / `computational-feasibility` S6）：**测试窗口必须覆盖至少一次崩溃期**。在平稳期做会通过，这是它最容易被做错的地方。

### 7.5 CI 断言的红线（这是宪章里最容易被违反的一条）

`pseudo-simulation` S11 判定回归测试本身是"被自动化强制执行的剧情树"，而且比手写剧情树更糟：(i) 它不在内核里，任何"内核无硬编码"的审查都看不见它；(ii) 它把"结果不对"自动转化为红色失败，从而把人手梯度下降**自动化、日常化、并赋予道德正当性**（"CI 挂了，得修"）；(iii) 修法永远是改内核或改参数，从来不是改断言。

```
=== CI 允许断言的（不变量） ===
  守恒律闭合（物质/能量/人口，int64 精确相等）
  确定性（同 (state, seed, proposal_log) 逐位相同）
  线程数不变性 / 容器迭代顺序不变性 / 跨机器不变性
  调度顺序无关性
  GATED 计数不上升
  读取集差集为空（declared_causes \ read_set_closure）
  类型抹除测试 T-ERASE 通过
  荒诞度置换不变性 T-ABS 通过
  零干预测试 / 因果隔离测试（定义在 spec-causality）
  金丝雀检出率不下降
  参数活性 / 矩位移
  复杂度 log-log 斜率 <= 1.2
  spike main 的周期数上限
  自由参数配额
  L1 一致性判据（后勤上界、信息光锥、并发占用）

=== CI 禁止断言的（宏观结果） ===
  assert 到 t=2000 至少存在一个人口 > 10000 的政体
  assert 农业在 t=800 之前出现
  assert 世界人口在 t=3000 落在 [2e6, 2e7]
  assert 出现了文字 / 货币 / 官僚制
  任何以模拟年份为条件的期望值
  任何对政体数、城市数、战争数的区间断言

=== 宏观结果的正确归宿 ===
  只能进仪表盘，展示分布随内核版本的漂移，供人观察和解释，**不触发失败**。
  若某个宏观量的漂移确实需要引起注意，正确形式是
  "版本间分布对比报告 + 人工判读记录"，且判读记录进 §8.4 的 change_log。
```

**与 §1 模式电池的关系（重要，容易混淆）**：模式电池**不是** CI 断言。它是**里程碑级的评审工件**，产出通过/失败矩阵与失败清单，由人判读并记录。只有 §7.5 允许清单里的那些不变量才进 CI 红/绿。这条区分是宪章的一部分。

### 这一节禁止了什么

- 禁止九类目标导向调节机制的无注释使用。
- 禁止 `GATED_COUNT` 上升（除非宪章修订 + 两名签字人）。
- 禁止 GATED 处不记账、不设触发率报警、不设到期版本。
- 禁止用加 clamp 的方式解决"触发率过高"。触发率过高是机制缺陷，必须改机制。
- 禁止隐式求解器；显式积分 + 步长减半不变性测试（且测试窗口必须覆盖崩溃期）。
- 禁止 CI 断言任何宏观历史结果。
- 禁止把模式电池接进 CI 红/绿。它是评审工件，不是构建门。
- 禁止把"CI 挂了，得修"当成调参的正当理由——先确认挂的是不变量还是宏观结果断言；后者本身就是违章。

---

## 8. 人类回路防线

### 8.1 为什么这一节存在

`pseudo-simulation` 把伪模拟分成五个层级，并判定：

| 层级 | 形态 | 代码审查能否抓住 |
|---|---|---|
| L1 显式脚本 | `if cond: spawn_dynasty()` | 能 |
| L2 隐式调节器 | clamp、归一化、拒绝采样、自适应速率、兜底重生 | 能，但必须先知道要 grep 什么 |
| L3 参数拟合 | 把结果写进参数 | 只能靠空模型对照 + 自由度审计 |
| **L4 人类回路** | 反复调参直到世界"像样"；跑 400 个种子只展示好看的那个 | **不能。只能靠流程留痕** |
| **L5 目标反噬** | 终极产物的需求反向塑造内核设计与验收标准 | **不能。它污染的是评价函数本身** |

该红队的判决（逐字）：**"纲领与 21 篇简报的全部防御集中在 L1–L3。L4 与 L5 是唯二能让一个彻底干净的内核产出彻底虚假的历史的机制。"**

§2 的 K7 金丝雀已经用实验方式确认了这一点：**内核干净但只展示 P95 的运行，零条判据会变红。** 因此本节的全部措施都是流程性的，而且**必须从第一天生效**——不从第一天记录，事后永远无法证明我们没有挑选。

### 8.2 运行登记表（run registry）

```sql
-- append-only；DELETE 与 UPDATE 由数据库权限禁止；schema 变更需宪章修订
CREATE TABLE run_registry (
  run_id           TEXT PRIMARY KEY,   -- BLAKE3(world_seed ‖ kernel_hash ‖ param_hash ‖ basemap_hash ‖ started_at)
  started_at       TIMESTAMP NOT NULL,
  kernel_hash      TEXT NOT NULL,
  param_hash       TEXT NOT NULL,
  basemap_hash     TEXT NOT NULL,
  llm_ledger_hash  TEXT,               -- 无 LLM 时为 NULL
  world_seed       BLOB NOT NULL,
  seed_rule        TEXT NOT NULL,      -- 见 §8.3：canon 必须是 "declared:<规则字符串>"
  lineage_class    TEXT NOT NULL,      -- 'canon' | 'lab'；不可移除、不可修改
  parent_run_id    TEXT,               -- 分叉来源
  fork_tick        INTEGER,
  sim_years        INTEGER NOT NULL,
  termination      TEXT NOT NULL,      -- 'completed'|'extinction'|'stasis'|'crash'|'oom'|'killed'|'timeout'
  macro_summary    JSON NOT NULL,      -- 预注册的 12 个宏观量的终值 + 分位
  viewed_by        JSON NOT NULL DEFAULT '[]',   -- 谁看过、什么时候看的
  cited_in         JSON NOT NULL DEFAULT '[]',   -- 被哪些文档/图表引用过
  cpu_hours        REAL NOT NULL,
  bucket           TEXT NOT NULL       -- 四方分账：'sim'|'validation'|'causal'|'llm'
);
```

**入表规则**：
1. **任何超过 100 世界年的运行自动入表，无论结果。**（`pseudo-simulation` F5 替代设计第 3 条）
2. 入表由运行器强制，不经人手；关闭入表需要 `--no-registry` 且该 flag 在生产构建中被编译期移除。
3. 删除条目需要显式的提交记录 + 两名签字人；被删条目的 `run_id` 保留在 tombstone 表中。
4. `viewed_by` 由查看工具自动写入。**"没人看过的运行"是一个必须被统计的量。**

### 8.3 预注册抽样规则（canon seed）

```
canon 世界线的 seed 由**事先声明的、与结果无关的规则**决定：

  world_seed = BLAKE3( "canonical"
                     ‖ kernel_hash            # 内核代码的内容哈希
                     ‖ basemap_hash           # 地图基底的内容哈希
                     ‖ param_hash             # 冻结参数集的内容哈希
                     ‖ canon_index )[0:8]     # 0, 1, 2, ... 预先声明要跑几条

  canon_index 的上限在开跑前写死（建议 N_canon = 8）。
  **先定种子再跑，跑出什么算什么。**
```

- **允许**因技术故障（crash / OOM / 机器掉电）重跑，**不允许**因不好看重跑。重跑必须在 registry 中留下 `termination='crash'` 的原记录 + 新记录，并在 `rerun_log` 中说明技术原因。**重跑次数是必须公布的指标。**
- **单向阀（数据模型硬约束，不是纪律）**：`lineage_class='lab'` 的分支**永远不能**成为 canon。实现：
  - `lineage_class` 是 `run_id` 哈希输入的一部分，改它就换 id；
  - 出版工具（历史书生成器、图表生成器、对外报告）在读取时硬拒绝 `lineage_class != 'canon'` 的数据源，且这条检查在编译期由类型系统保证（`CanonRun` 与 `LabRun` 是两个不同的类型，出版 API 只接受前者）。
- 出处：`pseudo-simulation` F5 替代设计第 1、2 条。理由（逐字）：分叉 = 扩展节点，反事实 = 定向扰动，"选择某个时代/事件/人物写小说" = 评分函数，**三者合起来是一次 beam search，其产物在信息论上等价于人手写的剧情**。

### 8.4 参数改动分类账

```toml
# params/agriculture.toml
[[param]]
name  = "weed_seedbank_decay"
value = 0.31
unit  = "1/yr"
source = "agriculture-carrying-capacity §4.9"     # 二选一：source 或 free
free   = false
justification_class = "外部数据拟合"   # 外部数据拟合 | 理论推导 | 量纲/守恒约束 | 未校准 | 叙事
                                       # 「叙事」类允许数量 = 0（CI 检查）

  [[param.change_log]]
  from = 0.25; to = 0.31
  class = "evidence"                   # bug | evidence | aesthetics
  justification = "Johnston 2003 综述的实验证据链，见 agriculture-carrying-capacity §2.10"
  commit = "a1b2c3d"; date = "2026-10-02"; author_role = "modeler"
```

**三分类的定义（`pseudo-simulation` F2 判别测试第 1 条）**：
- `bug` —— 实现错误（原值与设计意图不符）。
- `evidence` —— 新的一手文献，**必须附引文**（CI 检查 `justification` 非空且含可解析的引用标识）。
- `aesthetics` —— 结果不好看。**这一类不禁止，但它有代价。**

**代价（这是本节的核心规则，逐字采自 `pseudo-simulation` F2）**：

> **任何被 `aesthetics` 改过 ≥2 次的参数，其下游一切宏观现象在文档中永久标注为"非涌现（拟合产物）"。**

工程落地：
```
CI job: compute_taint
  tainted_params = { p : count(p.change_log where class=='aesthetics') >= 2 }
  # 保守传播：任何依赖 tainted_params 的宏观输出都被污染
  # 依赖关系由参数敏感性图给出（OFAT 扫描的非零响应），
  # 敏感性图未建立时**默认全部宏观输出被污染**（保守方向）
  报告生成器自动在受污染的图表与结论上加水印 "NON-EMERGENT (FITTED)"
  这个水印**人不能手工去掉**（生成器不提供接口）
```

**CI 公开指标**：`aesthetics` 改动的总数、涉及的参数清单、以及受污染的宏观输出比例。`pseudo-simulation` F2 的可观察症状：提交历史里出现"调整 X 使国家形成时间更合理""降低 Y 避免早期崩溃"，某几个参数被反复修改、幅度不大、方向一致，团队里出现"这一版世界终于像样了"。

### 8.5 参数溯源审计与 P/T 比

`llm-storytelling` F7 给出两条可计算的治理指标：

```
指标 1（参数-目标比）：
  P = 全部风险率函数、先验函数、机制参数中的**自由参数总数**
  T = 有独立外部经验目标的**校准目标数**
  规则：P / T > 3 ⇒ 该模型不可证伪。
  **这个数字必须出现在每一份模型文档的第一页。**

指标 2（溯源分类占比）：
  justification_class ∈ { 外部数据拟合, 理论推导, 量纲/守恒约束, 未校准, 叙事 }
  规则：「叙事」类的允许数量 = 0（CI 构建失败）
        「未校准」的比例是模型成熟度的直接读数，逐版本报告
```

配合 §10.5 的自由参数硬配额（`free_global ≤ 12` + `free_regional ≤ 3`），P 的上界被两边夹住。

### 8.6 参数冻结时点与回滚测试

- **冻结时点**：Phase 1 末冻结参数集合与取值（`pseudo-simulation` F2 判别测试第 2 条）。
- **冻结之后的表述规则**：**"我们的世界涌现出了 Z"这句话，只有在没有新增或重调任何参数的前提下才成立**（prediction vs postdiction）。冻结后的每一次参数改动都会重置这个资格，并在文档中记录重置时间。
- **回滚测试**（同上第 3 条）：一次性回滚全部 `aesthetics` 改动，重跑 200 种子。**宏观形态若崩塌，我们就知道了那部分形态的真实作者是谁。** 这个测试每个里程碑做一次，结果进报告。

### 8.7 失败率公布制度

必须公布、且必须与任何"成果"并列展示的指标（`pseudo-simulation` F5 替代设计第 4、5 条）：

```
P(extinction)            # 5000 年内世界人口归零
P(no_state_5000y)        # 5000 年内不出现 is_state=True 的政体
P(permanent_stasis)      # 连续 1000 年所有预注册宏观量的变化 < 噪声地板
P(technical_abort)       # crash / oom / timeout
rerun_count              # 因技术故障重跑的次数
unviewed_run_fraction    # 从没人看过的运行占比
```

**"一个在 200 个种子上灭绝率恰为 0 的世界是可疑的"**（该红队原话）。落地为拒绝条件 R7（§11）。

**无聊运行必须被展示**：任何对内/对外汇报，必须同时给出该内核版本**全部运行的分布图**，并标出被展示那一次所处的分位数。该红队给的表述模板值得逐字采用：

> "这是 87 号世界，它在'最大政体规模'上处于 P97。"

### 8.8 角色分离与 L5（目标反噬）的缓解

L5 是"终极产物的需求（可解释、可写成小说）反向塑造内核设计与验收标准"，它污染的是评价函数本身，没有技术手段。可做的只有三件事：

1. **角色分离**（`llm-storytelling` F7 替代设计第 4 条）：**调 `π`（规则先验）的人与看叙事的人必须分离。** 在小团队里做不到人员分离时，最低要求是**时间分离 + 记录分离**：调参会话与读叙事会话分开，且调参决策在读叙事之前写下并哈希。
2. **"清楚"是警报，不是褒奖**（`pseudo-simulation` F1 可观察症状）。评审用语规范：禁止把"这条因果链很清楚""这个解释很漂亮"作为通过依据；这类表述出现时，评审记录必须触发一次 `C_7` 覆盖率检查（P-MET-06）。
3. **Phase 0 成功标准的改写**（`pseudo-simulation` F1 替代设计，逐字采纳）：

> Phase 0 成功 = 我们有能力对任意重大事件：(a) 机械地算出它的读取集闭包；(b) 用同种子干预重放测出每条声称前因的真实因果贡献；(c) **发现并报告至少一类我们原以为是原因、实际不是原因的东西**；(d) **对一个可测量的事件比例，诚实地输出"原因不可恢复"**。

(c) 与 (d) 是硬性交付物，不是修辞。(d) 的下界由 P-MET-05 给出（≥10%）。

### 这一节禁止了什么

- 禁止任何超过 100 世界年的运行不入登记表。
- 禁止 canon 世界线的 seed 由人在跑之后选择。seed 规则必须事先声明且与结果无关。
- 禁止 lab 分支成为 canon（类型系统层面的硬约束，不是纪律）。
- 禁止因"不好看"重跑 canon。技术故障重跑必须留痕并计入公布指标。
- 禁止参数改动不入分类账；禁止 `aesthetics` 改动被伪装成 `evidence`（`evidence` 类必须附可解析的引文）。
- 禁止手工去掉 `NON-EMERGENT (FITTED)` 水印。
- 禁止 `justification_class == 叙事` 的参数存在。
- 禁止在 `P/T > 3` 时对外声称模型可证伪。
- 禁止只展示一条世界线而不给出该内核版本全部运行的分布与分位。
- 禁止把"这条因果链很清楚"当成褒奖。

---

## 9. 密封清单测试与词表增长测试

### 9.1 为什么这两个测试的成本几乎为零而价值极高

`pseudo-simulation` S4 判定："事件类型枚举给世界的可能性封顶，而纲领第 9 段已经写好了那份枚举"（"例如战争、国家形成与灭亡、革命、宗教诞生、制度改革、技术突破、民族迁徙、经济危机、思想运动等"）。这句话读起来像举例，实现起来是 `enum EventType`。后果：世界能发生的"事情的种类"被我们的想象力封顶，而我们的想象力被真实历史训练过。

`spec-world-state` D2 已经在本体层解决了一半（内核里不存在 `Event` 类型，事件是被检测出来的）。剩下的一半——**"我们的世界是否真的产生了我们想不到的东西"**——只能靠这两个测试回答。

### 9.2 密封清单测试（SEALED-LIST）

**协议（必须在看到任何长跑输出之前执行）**：

```
步骤 1（Phase 0 末，独立作答）
  团队每人**独立**写下他们能想到的全部"这个世界可能发生的事件种类"，
  每条 = 一个短语 + 一句话定义（定义必须只用 L0 原语描述，不得用制度名词）。
  独立性要求：作答期间不得互相讨论；提交时间戳记录。

步骤 2（合并与封存）
  合并去重（去重由第三方执行，去重规则记录），得到 sealed_list_v0.txt
  加密：age（X25519）+ 密钥用 2-of-3 Shamir 分持
  承诺：sha256(sealed_list_v0.txt) 写入 DECISION-REGISTER.md 与一个 git annotated tag
  **Phase 2 前不得查看。**

步骤 3（跑完之后，开封之前——顺序不可颠倒）
  对检测到的事件做无监督聚类：
    输入 = 事件的状态差分向量（由 significance 泛函提名，与事件类型完全解耦）
    通道集 = 由 L0 state schema **机械导出**（每个状态字段自动成为一个通道，
             加上一组机械构造的组合通道）；**禁止手工挑选通道**
    手工添加的通道必须在登记表里单独列出并**计入自由度**（P/T 的 P）
    聚类算法 = HDBSCAN（min_cluster_size 预注册，建议 >= 0.5% 的事件数）
    簇数选择 = HDBSCAN 稳定性；**禁止人工分箱**
    （出处：`pseudo-simulation` S4 本方案自身的漏洞与缓解；
      `complex-systems-emergence` §8.12：等级数是分箱产物，必须用无参数方法）

步骤 4（开封与盲评）
  开封 sealed_list_v0.txt
  两名**未参与聚类**的评审独立判定：每个簇能否用清单内的某一词条描述（是/否）
  报告 Cohen's κ；κ < 0.6 时增加第三名评审
  指标：清单外簇的**质量占比** = Σ_{清单外簇} significance / Σ_{全部簇} significance
```

**判读规则（预注册）**：

| 清单外簇质量占比 | 判定 | 依据 |
|---|---|---|
| < 5% | **失败：原语层封顶** | 本文追加，D 级 |
| 5% – 15% | 灰区：报告并调查通道集是否过窄 | 本文追加，D 级 |
| ≥ 15% | **通过** | `pseudo-simulation` S4（"建议最低及格线 15%（我编的数字，D 级）"） |
| > 60% | **反向报警**：`significance` 泛函可能在提名噪声 | 本文追加，D 级 |

`pseudo-simulation` S4 的原话值得逐字保留：**"如果是 0，我们的世界没有产生任何我们想不到的东西——项目在这一维度上失败了。"**

**这个测试是一次性的、不可重来的。** 看过输出之后再写清单，它就死了。因此 V13 标为不可逆。

### 9.3 词表增长测试（VOCAB-GROWTH）

```
每 500 模拟年做一次聚类（协议同 §9.2 步骤 3），记录簇数 K(t)。

拟合  K(t) = K_∞ · (1 − exp(−t / T))
验收：T > 2000 年   或   K_∞ 的 95% 置信下界 > 1.2 · K(5000)     ［D 级待标定］

失败形态（`pseudo-simulation` S4 判别测试 2 的原话）：
  K(500) = 40 而 K(5000) = 41  ⇒  原语层已封顶
```

**配套指标（`mandate-contradictions` F2 替代设计第 3 条）**：

```
novel_combination_rate(t)：机制共现矩阵中单位时间内首次出现的非零格数
验收：不饱和（同样的饱和曲线拟合，T > 2000 年）
可观察的失败症状：机制共现矩阵在 t=1000 之后不再出现新的非零格
```

**为什么这条比"是否出现了荒诞事件"可靠**（该红队原话）：**它不能靠调大方差刷分。** 扩大随机分布的尾部会增加数值极端，但不会增加机制组合的新格。

### 9.4 两个测试的共同漏洞（必须一起说清楚）

`pseudo-simulation` S4 自陈的漏洞：**"在哪些状态通道上做变点检测"这个选择，就是新的枚举，只是从内核挪到了观察层。**
- 好处：它不再影响世界的演化（观察不改变被观察者）。
- 坏处：我们能"发现"的东西仍受限于通道集。
- 缓解：通道集必须由 state schema 机械导出；手工添加的通道单独列出并计入自由度。
- **残余风险（诚实标注）**：如果 L0 的 schema 本身漏掉了某个维度（例如我们根本没有表示"仪式性竞赛"所需的状态），那么该类现象既不会发生，也不会被发现，而这两个测试都看不出来。这条进 §12。

### 这一节禁止了什么

- 禁止在看到任何长跑输出之后再写密封清单。
- 禁止在开封之前偷看，或在聚类之前开封（顺序是协议的一部分）。
- 禁止手工挑选变点检测通道。通道集必须由 state schema 机械导出。
- 禁止手工分箱定义簇数或等级数（必须用无参数方法）。
- 禁止由参与聚类的人担任开封后的盲评。
- 禁止把"清单外簇占比 = 0"解释为"我们的世界很自洽"。它的正确解释是项目在这一维度上失败了。
- 禁止用扩大随机方差的方式提高 `novel_combination_rate`（它在数学上不响应方差，试图这么做只会暴露误解）。

---

## 10. 算力预算

### 10.1 预算的第一性原理：单位是「跑一次 × 集合」

`computational-feasibility` F1 的判决（逐字）：**"纲领把'计算成本'写成了一个待答问题，但它问错了单位：真正的预算单位不是'跑完一次三千年'，而是'跑完一次 × 集合规模'。"** 以及：**"算力预算直接决定了我们能做多少次实验，能做多少次实验直接决定了我们说的话有没有意义。"**

失败链条（该红队给出的具体形态，不是"可能有风险"）：20 个子系统各自"花得起" → 单次长跑 8–24 小时 → 演示时完全可接受 → 到了要验证时 200 种子 × 12 小时 = 12.5 天 → 种子数降到 3–5 → 唯一能做的事是**看这 3 条历史线里哪条好看** → 这正是 L4 失效。**算力不足不是让项目变慢，是让项目失去证伪能力。**

### 10.2 三个必须写死的数 + 四方分账

```
目标硬件      : 8 台 × 16 核工作站（128 核，128 GB RAM/台，NVMe）
                + 1 台参照笔记本（8 核 Apple 芯片级）用于 spike main 的 CI
T_run 上限    : <= 1 小时（单条 3000 世界年，不含 LLM）
N_ensemble    : 200

月度总预算    : 128 核 × 24 h × 30 d = 92,160 CPU-h/月
```

| 账户 | 占比 | CPU-h/月 | 覆盖内容 | 依据 |
|---|---|---|---|---|
| **模拟** `sim` | 20% | 18,432 | canon 世界线、生产集合、演示 | 反推 |
| **验证** `validation` | **50%** | **46,080** | 模式电池、消融矩阵、涌现认证、诱饵世界、零模型、敏感性、玩具世界 CI | `emergence-verifiability` F15 替代设计第 1 条（"验证预算必须被声明为总算力的固定下限，我建议 ≥50%"） |
| **因果** `causal` | 25% | 23,040 | 干预重放、安慰剂零分布、归因报告 | `causality-bookkeeping` F5（"因果算力必须进预算……本条是它的因果侧独立追加项，**两者不能共用同一笔预算**"） |
| **LLM 编排** `llm` | 5% | 4,608 | 批处理编排、ledger 写入、缓存管理（API 费用另账，见 §10.8） | `computational-feasibility` F5 |

**记账机制**：`run_registry.bucket` 字段（§8.2）强制标注；月度自动报表。**验证占比连续两个月 < 50% ⇒ 里程碑评审阻塞**（这是把 F15 的"以后补，然后永远不补"变成硬约束）。

**这个分账的直接后果，必须诚实写下来**：

| 活动 | 单次成本 | 频率上限 |
|---|---|---|
| 一次全尺度 200 种子集合 | 200 CPU-h | sim 预算下 ≈ 92 次/月（实际受人手限制） |
| 一次全尺度涌现认证（27 臂 × 500 跑） | **13,500 CPU-h** | validation 预算下 ≈ **3.4 次/月**，实际按季度做 1 次 |
| 一次全尺度零模型报告（7 臂 × 200） | 1,400 CPU-h | 每里程碑 1 次 |
| 一次严肃的"为什么"（含安慰剂 100 次 + 20 候选原因 × 326 次重放） | **5,000–10,000 CPU-h** | causal 预算下 **2.3–4.6 个/月 = 28–55 个/年** |
| 一次对抗式敏感性搜索（45,000 次运行） | 全尺度 **45,000 CPU-h（超预算）** → **必须在玩具世界做**：45,000 × 8 s = **100 CPU-h** | 每里程碑 1 次 |
| 一次 HM + hetGP 校准（5,300 次运行） | 全尺度 5,300 CPU-h → 前两波在玩具世界（12 CPU-h），末波取 NROY 子集在全尺度（≈600 CPU-h） | 每次重大结构变更 |

对抗式敏感性的运行次数与 CPU 成本参照 `abm-methodology` §4.2（Stonedahl & Wilensky：12 参数、每点 15 重复、100 代 = 45,000 次运行；5 次搜索约 2,500 CPU 小时，模型规模是 80×120 格、700 年的 Artificial Anasazi）。HM 的 5,300 次参照同表（O'Gara et al.，Covasim 4 参数，替代了原本 >100,000 次运行 ≈35 天算力的路径；三波后排除 >99% 参数空间，NROY 体积 7.23% → 5.58% → 0.82%）。

**一句必须写进纲领的诚实表述**（改写自 `causality-bookkeeping` F5(a)）：

> 纲领第 24 行写的是"可以查询任何重大事件的因果链"。诚实的写法是：**每个"为什么"问题的标价是 5,000–10,000 CPU 小时，因此我们一年能严肃回答大约 30–50 个问题，必须挑。** 其余问题的答案是"算力不可回答"，这是一个合法答案。

### 10.3 复杂度契约表

每个子系统一行，写明代价是哪个实体计数的什么函数、截断半径 / top-k 是多少、超出时如何退化。基线份额沿用 `computational-feasibility` §8 的分配（该红队明确自陈"第 8 节预算表里全部 12 行的百分比分配，是我拍的。它的价值在于'总和必须是 100%'这个约束"）。

| 子系统 | tick 率 | 代价函数 | 截断常数（必须是世界内可解释的量） | 份额 | ms/tick | 超出时的退化行为 |
|---|---|---|---|---|---|---|
| 气候/水文 | 年，CBRNG 现算不落盘 | O(cells) | — | 5% | 60 | 无（线性） |
| 农业/承载力 | 年 | O(cells) | — | 10% | 120 | 无 |
| 人口 L0 队列 | 年 | O(cells × age_bins × sex × stock_bands) | 稀疏，活跃槽 ≤ 2×10⁶ | 8% | 96 | 合并最小存量档 |
| 人口 L2 个体 | 年 | O(persons) | persons ≤ 3×10⁴ | 15% | 180 | 按重要性打分驱逐（降级回队列） |
| 聚落/土地利用 | 年 | O(households) + O(sites) 冻结 | households ≤ 2×10⁵ | 10% | 120 | 合并最小家户 |
| 贸易/市场 | 年内 4 子步 | **O(n log n)**，引力 + **300 km 有效距离截断 + top-k=12 伙伴** | 截断依据：ORBIS 成本比 陆:河:海 ≈ 35:3.4:1 ⇒ 半径比约 10× | 12% | 144 | 降 top-k；**禁止全对** |
| 疫病 | 事件驱动，爆发内周步 | O(active_patches) | 活跃斑块 ≤ 50 | 8% | 96 | 拒绝新爆发（记录拒绝率） |
| 战争 | 事件驱动，战役内日步 ≤ 180 | O(concurrent_wars × days) | 并发 ≤ 8 场 | 7% | 84 | 排队（记录排队长度） |
| 制度/文化/宗教 | 5 年 | O(polities × cultures) | 政体 ≤ 200、文化 ≤ 100 | 5% | 60 | 合并最相似文化 |
| 信息/社会网络 | 年 | O(edges) | 边 ≤ 3×10⁶ | 5% | 60 | 按 strength 驱逐 |
| 事件日志写入 | 年 | O(events) | ≤ 2.5×10⁴ 事件/年 | 10% | 120 | 提高 significance 提名阈值（**记录阈值变化**） |
| 快照/结构共享 | 年 | O(dirty_bytes) | 增量 ≤ 25 MB/年 | 5% | 60 | 降低快照频率 |
| **合计** | | | | **100%** | **1,200** | |

**规则（`computational-feasibility` S4 替代设计第 2 条）**：**任何超线性项必须带一个显式常数上限，而且这个上限必须是一个世界内可解释的量，不是魔数。** 例：贸易半径 = 该运输方式在可接受成本内能到达的距离——ORBIS 的每 km 成本表（陆运马车 0.035、驴/骆驼 0.028、河运顺流 0.0034 denarii·kg⁻¹·km⁻¹，`settlement-urbanization-spatial` §4.3）给出 10 倍的成本比，因此给出约 10 倍的合理半径比。

**为什么这张表必须存在**：`computational-feasibility` S4 指出隐藏二次项**是延迟触发的**——世界跑到第 800 年、聚落从 300 涨到 3,000 时，每 tick 时间涨 100 倍而不是 10 倍；**开发期只跑 200 年的原型永远看不到它。** 5,000 个聚落走月度全对贸易评估会超预算 3 个数量级（4.5×10¹¹ ops）。

### 10.4 复杂度回归测试（CI）

```
测试 CPLX-1（log-log 斜率）
  用 1× / 2× / 4× 实体数各跑 50 tick，拟合 log(tick_ms) ~ log(entity_count)
  **斜率 > 1.2 ⇒ 构建失败**
  出处：`computational-feasibility` S4 可观察症状与替代设计第 3 条

测试 CPLX-2（截断常数活性）
  每个截断常数（top-k、半径、并发上限）改变 2 倍时，
  被截断的子系统的输出分布必须显著变化；不变 ⇒ 截断常数是死的（或截断从未生效）

测试 CPLX-3（T_run 外推门）
  每次提交在玩具世界跑一次标定过的基准，
  按 §10.6 的缩放因子外推到全尺度 T_run；**超预算即构建失败**
  出处：`computational-feasibility` F1 替代设计第 2 条
  （"性能预算像内存泄漏一样必须被自动化守护，因为它的退化永远是渐进的、每次都只慢 3%"）

测试 CPLX-4（晚期负载）
  nightly 跑 3000 年玩具世界，记录 tick 耗时的时间序列；
  若 tick_ms(t=2500) / tick_ms(t=500) > 5 ⇒ 报警（延迟触发的二次项）  ［D 级阈值］
```

### 10.5 自由参数硬配额

```
free_global   <= 12      # 全域自由参数
free_regional <= 3       # 东亚专用参数（水稻、黄土、季风等无法从别处校准的）
总计          <= 15

每个参数在配置里必须标注恰好一个：
  source = "<brief-slug §小节 或 DOI>"    # 可追溯到简报里的具体数值
  free   = true                            # 自由参数，计入配额
CI：
  count(free == true and scope == "global")   <= 12  否则构建失败
  count(free == true and scope == "regional") <= 3   否则构建失败
  count(source 为空 and free 未声明)           == 0   否则构建失败
```

- 配额出处：`computational-feasibility` S2（"自由参数硬配额：12–15 个"；该红队自陈"12–15 是我从 Sobol 次数反推的量级，不是文献值"，D 级）。算术依据：在 `T_run=1 h`、8 台机的现实里（5,760 次/月），一个月的标定预算最多支撑 **d≈10**；Sobol 一阶+总效应 N=1024 时 d=10 → 22,528 次、d=15 → 32,768 次、d=30 → 63,488 次（11 个月）。
- **两本账的拆分依据**：`pseudo-simulation` S6 判别测试 1 的东亚 holdout——参数只在美索不达米亚、中美洲、安第斯、西非、地中海等区域的比较数据上校准，东亚只作测试集；代价是"水稻、黄土、季风等东亚特有参数无法从别处校准，这部分必须显式列为'东亚专用参数'，单独计入自由度预算、单独标注下游结论"。
- **强迫的后果（这是好事）**：配额会强迫子系统之间**共享参数**、用**无量纲比值**代替绝对值（不要"迁徙成本"和"贸易成本"两个自由参数，要一个"运输成本"与一个比值）。同时它给 `abm-methodology` AP11（"参数越多越真实"）与 AP4（Turchin 自己的警告："大型复杂模型往往结构不稳定，一个参数的小变化会导致动力学大变"，主张 "a spectrum of models, each simple enough"）一个可执行的答案。
- **机制数量上限 |M| ≤ 20**：消融成本 ∝ |M|（`emergence-verifiability` F15 替代设计第 3 条）。CI 检查 `MECHANISM_REGISTRY` 的条目数。

### 10.6 CI 级玩具世界规格

`emergence-verifiability` F15 替代设计第 2 条要求"必须有一个 CI 级的玩具世界……玩具世界的规格是 Phase 0 的交付物之一"；`computational-feasibility` §7.8 给出了它的正确形状：**"一个流域、300 年、全部机制、200 个种子"**，并说明它"能在写东亚和三千年之前暴露本文的每一个失败模式"。

```
名称       : basin600
地图       : H3 res 5 的一个连通子集，600 格（约 1.5×10^5 km²），
             必须包含：一条主河、一段高机动性生态带（草原）边缘、
                       一个海岸段、一处山口（否则 P-SET-04/P-TEC-04 无法检验）
             地图由 basemap 生成器用固定 seed 生成，内容哈希写死
时长       : 300 世界年（PR 门）；3000 世界年（nightly）
机制       : **全部机制开启**（不是简化机制——这是本规格与"简化玩具"的关键区别）
实体上限   : 全尺度上限 ÷ 50（persons ≤ 600、households ≤ 4,000、
             edges ≤ 6×10^4、InfoCopy ≤ 10^5、sites ≤ 4.4×10^4）
预算       : 单次 300 年 <= 8 s；单次 3000 年 <= 80 s
             200 种子 × 300 年 = 1,600 s ÷ 16 核 = **100 s**
             200 种子 × 3000 年 = 16,000 s ÷ 16 核 = **17 min**（nightly）
判据       : **全套判据必须能在它上面跑完**（这是它的定义性要求）
缩放       : 提供 scale_factor.toml，记录 basin600 → 全尺度的外推系数，
             每次内核变更后由 CPLX-3 重新标定
```

**PR 门的实际预算**：诱饵 3 臂（健康 + W1a + W3）× 20 种子 × 8 s = 480 s ÷ 16 核 = **30 s**；零模型 7 臂 × 50 种子 × 8 s = 2,800 s ÷ 16 核 = **3 min**；确定性/参数卫生/复杂度测试 ≈ 1 min。**PR 门总计 ≈ 4.5 min ≤ 5 min**，可接受。

### 10.7 `--spike` main：仓库里必须始终能跑的那个东西

`prior-art-postmortem` §1.9 的教训（URR：15 年单人开发、目标高度重合、作者极其胜任，仍停在 0.11 版，仅 0.11 这一个版本就发了 66 篇更新日志）与【取舍 2】给出的硬约束（§5.1 重申）：

> **从 Phase 0 起，仓库里必须始终存在一个能在 60 秒内跑完 3000 模拟年并通过重放测试的 `main`。任何一周内如果这个 `main` 跑不起来，该周的其他工作全部暂停。研究可以慢，但端到端管道不许断。**

（说明：任务书把这条称为 "T12"；`prior-art-postmortem` 原文没有 T 编号体系，该要求实际出现在 §1.9、【取舍 2】与 §5.1 三处。）

```
配置名     : spike
机制       : 高程 + 单一作物 + 人口（L0 队列）+ 迁徙 + 一种冲突。**零 LLM。**
地图       : 全尺度陆地格（≈9×10^4）——刻意不缩小，这样它同时是内存布局的压力测试
状态       : 每格 8 个 int64 热字段
输出       : 事件日志 + 因果图（读取集闭包版本）
时长       : 3000 世界年

性能门（可执行形式）：
  阈值不用墙钟秒，用**归一化周期数**，以消除机器差异：
    calib_factor = 参照标定核（10^9 次 int64 混合运算）在本机的耗时 / 参照机耗时
    normalized_cycles = wall_seconds × 3e9 / calib_factor
  **要求 normalized_cycles <= 1.8e11（= 60 s @ 3 GHz），容差 +20%**
  算术校验：3000 tick / 60 s = 20 ms/tick；20 ms ÷ 9×10^4 格 = 222 ns/格 ≈ 660 周期/格。
            以每格 8 个 int64 字段、每字段 ~5 次运算计，SIMD 下有约 10× 余量。**可行。**

必过的三项测试：
  SPIKE-1  bit 级重放：同 (state, seed) 跑两次逐位一致
  SPIKE-2  守恒审计（A1）全程零失败
  SPIKE-3  因果图非空且 declared_causes \ read_set_closure == ∅

红 main 计数器：
  red_main_days（连续天数）公开在仓库首页徽章上
  red_main_days >= 7  ⇒  **全项目其他工作暂停**，这是宪章条款，不是建议
```

**为什么 spike 不能是"简化的玩具"**：它的作用是保证端到端管道（内核 → 日志 → 因果图 → 重放 → 判据）永不断裂。任何一个环节被跳过，它就失去了意义。因此 SPIKE-3 是硬性的。

### 10.8 LLM 的成本与墙钟（另账）

沿用 `computational-feasibility` F5 与 §8 的实测价格表（来源：该红队标为 A 级，取自本机 `claude-api` skill 的官方定价表，缓存日期 2026-06-24）：Haiku 4.5 $1/$5、Sonnet 5 $2/$10、Opus 5 $5/$25 每 MTok；cache read 0.1× 基础输入价、cache write 1.25×（5 min TTL）/ 2×（1 h TTL）；Message Batches 50%。

```
配额（硬）：每条世界线 LLM 调用总数 <= 3×10^4（= 每 tick <= 10 次）
成本       ：Haiku 4.5 + 缓存 + Batch ≈ $0.00125/次
             → $37/线；200 条 = **$7,500**
             5% 高层判断上 Sonnet 5 → ≈$50/线，200 条 = **$10,000**
结构（硬）：
  1. LLM 永不在 tick 的关键路径上（decide 相位读上一 tick 的 View，
     Intent 在下一 tick 的 resolve 里消费）
  2. 批处理单位 = 「同一 tick 序号 × 全体种子」= 每批 200 × 10 = 2,000 次调用
     （批处理延迟被 200 条线摊薄，**集合反而比单跑更划算**——
      这是本项目唯一能同时拿到 50% Batch 折扣和可接受墙钟的结构）
  3. 超配额直接走规则先验、不排队不降级模型
```

**警告（该红队对 `llm-agent-social-simulation` §9.2 的修正）**：Batch 的 50% 与 prompt caching 的 0.1× **在这个工作负载里很难同时拿到**——批处理周转是分钟到 24 小时量级，5 分钟 TTL 的缓存条目在结果返回前早就过期；换 1 小时 TTL 要付 2× 写入。**必须在 Phase 1 用 `usage.cache_read_input_tokens` 实测验证，不得把两个折扣直接相乘。**

**成本控制与污染控制是同一个旋钮**（`llm-storytelling` 已证明事件密度会跟着调用预算走）：调用配额同时是这两件事的上限。详见 `spec-llm-boundary`。

### 10.9 存储预算

沿用 `computational-feasibility` S5 的裁决"**不存轨迹，存配方**"：

```
世界线身份 = (world_seed, kernel_hash, param_hash, basemap_hash, llm_ledger_hash)
参考线（canon）保留：年度单元聚合 1.2 GB + 具名人物事件 12 GB + 聚落事件 15 GB
                     + LLM ledger 0.2 GB + 年度快照根哈希 ≈ **28 GB**
其余 199 条只留年度聚合：1.2 GB × 199 = 239 GB
**一个 200 种子集合 ≈ 267 GB**（能装进一块盘）

气候场**显式禁止落盘**：25 km × 12 月 × 3000 年 × 2 变量 = 5.5 GB/线（10 km 则 34.6 GB/线）
必须用 CBRNG 按 (tick, cell, purpose) 现算。

注意：`spec-world-state` §2.6 算出的年增量是 52 MB/yr → 156 GB/线，
**超过这个预算**，因此"不存轨迹存配方"不是优化选项而是硬约束，
且它反过来强化 T_run <= 1 h（重算换存储只在 T_run 足够小时成立）。
```

### 这一节禁止了什么

- 禁止在没有写下 `目标硬件 / T_run / N_ensemble` 三个数之前设计任何子系统。**先定预算，再定本体论。**（`prior-art-postmortem` §1.10）
- 禁止验证与因果共用同一笔预算。
- 禁止验证占比连续两个月低于 50% 而不阻塞里程碑。
- 禁止任何超线性项没有显式的、世界内可解释的截断常数。
- 禁止把对抗式敏感性搜索放到全尺度跑（45,000 CPU-h 超月度验证预算）。它必须在玩具世界做。
- 禁止自由参数超过 12（全域）+ 3（区域）。
- 禁止机制数超过 20。
- 禁止 CI 玩具世界使用"简化机制"。全部机制必须开启，否则它检不出 §10.4 的失败模式。
- 禁止 `--spike` main 缺失、跳过因果图输出、或用墙钟秒而不是归一化周期数做门槛。
- 禁止 `red_main_days ≥ 7` 时继续做其他工作。
- 禁止把 Batch 折扣与 prompt caching 折扣直接相乘。
- 禁止气候场落盘。
- 禁止以"3 个种子"为基础下任何关于世界是否合理的结论。

---

## 11. 一页纸的预注册拒绝条件

**签字时点**：在跑第一个长世界（≥1000 世界年）之前。签字后写入 `DECISION-REGISTER.md`，哈希入 git tag。修改任何一条需要两名签字人 + 重跑该条支撑过的全部结论。

**读法**：`级别` 列中 `HALT` = 判定内核错误，立即停跑并修；`INVESTIGATE` = 触发强制调查，48 小时内给出书面结论；`DISCLOSE` = 不是失败，但必须写在报告首页。`阈值来源` 列的 D 级表示这个数字是我们编的、待标定。

| # | 若出现以下情况 | 判定 | 阈值来源 |
|---|---|---|---|
| **R1** | 任一 tick 的守恒审计不满足 int64 精确相等（物质 / 能量 / Pop_up） | HALT | A（无需标定；`emergence-verifiability` F12） |
| **R2** | 同一 `(state, seed, proposal_log)` 重放两次非逐位一致 | HALT | A（`emergence-verifiability` F2 第 5 条） |
| **R3** | 改变线程数 / 容器迭代顺序 / 机器架构导致输出不同 | HALT | A（`computational-feasibility` F2：1 ULP 在约 **60 步**后放大到 O(1)，本机实测） |
| **R4** | 类型抹除测试 T-ERASE 失败 | HALT | A（二值） |
| **R5** | 荒诞度置换不变性 T-ABS 失败 | HALT | **D**（本文原创测试） |
| **R6** | 零干预测试 / 因果隔离测试失败（定义见 `spec-causality`） | HALT | A（二值） |
| **R7** | 200 个种子上 `P(extinction) == 0` 或 `== 1` | INVESTIGATE | **D**（`pseudo-simulation` F5：**"一个在 200 个种子上灭绝率恰为 0 的世界是可疑的"**；我们预注册 `0 < P(extinction) < 0.5`） |
| **R8** | 任一预注册宏观量的种子间变异系数 CV < 0.2；或"最大政体规模 @ t=3000"的 CV < 0.6 | INVESTIGATE | **D**（`pseudo-simulation` S10 建议 CV ≥ 0.6；0.2 通用下界为本文追加） |
| **R9** | 单点扰动 200 年后的状态距离，落在安慰剂零分布 95% 分位以下的比例 > 90% | INVESTIGATE | **D**（`causality-bookkeeping` F5 的安慰剂协议；90% 为本文取值） |
| **R10** | 任一宏观判定量在跨种子上以单 tick 阶跃出现（变点检测跳变 > 5σ 前驱波动） | INVESTIGATE | **D**（`emergence-verifiability` F5：阶跃是触发器的指纹；5σ 为本文取值，D6 用 3σ 作认证门槛，此处用 5σ 作强报警） |
| **R11** | 零模型 N0（纯承载力，零 agent）达到完整模型模式得分的 ≥ 90% | DISCLOSE（永久标注 `EXOGENOUS_DRIVEN`） | **D**（`complex-systems-emergence` §8.4 的 90% 判读规则；Janssen 实测差距是 10–50%） |
| **R12** | 判据体系在 W1 家族全部变体上都不失败（即判据全绿且诱饵世界也全绿） | HALT（判据体系失效，见 §0.2：证据量 ≤ 0） | A（形式化推导） |
| **R13** | 重大事件中由 D 级（我们发明的）概率分布生成的比例 > 80% | DISCLOSE（**必须写在首页，不是藏在附录**） | **D**（`pseudo-simulation` S7 判别测试） |
| **R14** | 密封清单测试的清单外簇质量占比 == 0 | HALT（项目在该维度失败） | **D**（`pseudo-simulation` S4） |
| **R15** | 因果链的平均深度随模拟时间**单调下降** | INVESTIGATE | B（`emergence-verifiability` F4 可观察症状） |
| **R16** | 存在被 `aesthetics` 改过 ≥2 次的参数，且其下游结论未被自动标注 | HALT（治理失效，工具链 bug） | A（二值） |
| **R17** | tick 耗时 vs 实体数的 log-log 斜率 > 1.2 | HALT（复杂度契约违约） | **D**（`computational-feasibility` S4） |
| **R18** | `red_main_days >= 7`（spike main 连续 7 天不通过） | HALT（**全项目其他工作暂停**） | B（`prior-art-postmortem`【取舍 2】） |
| **R19** | 任意 500 年滑窗的人均产出年增长率 > 0.15% 且无对应的机制解释 | HALT（文明加速主义） | A（`economy-markets-trade` §4.5：实际 GDP 年增长率北宋 0.90%/明 0.35%/清 0.58%，而**人均**单调下降；0.15% 阈值为本文由此推得，D 级） |
| **R20** | 战争 / 政权更替 / 宗教诞生的时间间隔分布的变异系数 < 0.5（过于规整，没有长时间无事期） | INVESTIGATE | **D**（`emergence-verifiability` F11 可观察症状；参照：真实州际战争的年间隔近似几何分布 q̂=0.428±0.002，最长间隔 18 年，`war-conflict-logistics` §4.7） |
| **R21** | 信念–事实背离度恒为 0 | HALT（信息边界未生效） | B（`emergence-verifiability` F8） |
| **R22** | 不可解释事件占比 < 10% | INVESTIGATE（因果库过完备 ⇒ 原因是被写上去的） | **D**（`pseudo-simulation` F1(d)） |
| **R23** | 扩散到达时间的最优地理模型 r² > 0.6 | INVESTIGATE（扩散被做成了确定性波前） | A（`technology-innovation-diffusion` §4.1：真实最好只解释 **36%**） |
| **R24** | \|corr(疫情起始时点, 人口相对趋势偏离)\| > 0.1 | HALT（疫病退化为人口调节器） | **D**（`epidemics-disease` §3.14；该简报称此为"本项目最危险的反模式"） |
| **R25** | `GATED_COUNT[kind]` 相对基线上升，且无宪章修订记录 | HALT（宪章违约） | A（二值） |

**统计**：25 条中 A 级 9 条、B 级 3 条、**D 级待标定 13 条**。D 级占比 52%——这个比例本身是一个必须公布的项目成熟度读数，且随标定推进应当下降。

### 这一节禁止了什么

- 禁止在跑第一个长世界之前不签这一页。没有拒绝域的判据体系不是判据，是修辞（`emergence-verifiability` F1）。
- 禁止在看到长跑结果之后调整这些阈值以让它们通过。修改需要两名签字人 + 重跑受影响的全部结论。
- 禁止把 D 级阈值伪装成 A 级。上表的最后一列是强制的。
- 禁止把 `DISCLOSE` 类结论放进附录。R11/R13 必须在首页。
- 禁止把 R7（灭绝率为 0）解释为"我们的机制很稳健"。

---

## 12. 我们承认无法验证什么

`emergence-verifiability` §8 第 10 条：**"这份清单的长度是项目诚实度的直接指标。"** 因此本清单**只允许增长，不允许缩短**（V19），缩短唯一的合法方式是附上新的可核验经验来源与提交记录。

### 12.1 学界无共识，因此我们无法用它校准（只进观察集）

| # | 量 | 状况 | 出处 |
|---|---|---|---|
| 1 | **政体寿命分布的形状** | 四个互相矛盾的结论：指数 τ≈220（Arbesman 2011）/ 饱和危险、众数≈200、恒定风险模型"consistently produces a bad fit"（Scheffer 2023, n=324+291）/ 指数 τ=298, KS p=0.71（Ciliberti 2025, n=168）/ 幂律（Lu 2021, n=22 中国帝国）；外加幸存者偏差假说（Wand 2024）。原话："**连『帝国寿命分布是什么形状』这个最基础的问题，学界都没有共识。**" | `cliodynamics-secular-cycles` §2.9 §7.1 |
| 2 | **世俗周期是否存在、波长多少** | 英格兰 850–1873 的傅立叶分析主导波长约 **79 年**，多世纪周期 "not evident"；整合期 vs 解体期的不稳定差异在单个周期内都不显著，要合并四个周期才达 p<0.013；而 Turchin 2005 明说中国看不到代际节律 | `cliodynamics-secular-cycles` §7.2 |
| 3 | **气候→冲突的因果强度** | Hsiang 2013 主张普遍效应 vs Buhaug 2014 的核心反驳；且清代实证中**旱灾与饥荒对内战没有显著滞后效应，只有 PSI 显著** | `cliodynamics-secular-cycles` §7.6 |
| 4 | **urban graveyard 的真实性与强度** | Sharlin 1978 主张是统计假象，Finlay 1981 回应，Woods 2003 总结为"未解决的辩论" | `settlement-urbanization-spatial` §7.6 |
| 5 | **超线性城市标度是否真的 β≠1** | Leitão et al. 2016：15 个数据集 × 5 个涨落模型，结论"关键取决于对涨落的建模"；同一份数据固定 δ 得 β=1.46±0.19，自由 δ 得 β=1.00±0.30，**结论直接反转** | `settlement-urbanization-spatial` §7.1 |
| 6 | **settlement scaling 是否普适** | Hutson et al. 2023 在北部玛雅低地 48 个遗址上**证伪**了面积–人口关系 | `settlement-urbanization-spatial` §7.2 |
| 7 | **Seshat 数据的可靠性** | Whitehouse et al. 2019 *Nature* **已撤稿**（Beheim et al. 2021：61% 缺失被重编码为"不存在"时结论成立，用现存数据或标准插补时**结论反转**）；Slingerland et al. 2020 指控 63% 的政体完全无专家审核 | `cliodynamics-secular-cycles` §7.4；`state-formation` AP10；`pseudo-simulation` S6 |
| 8 | **"精英"的操作化** | Turchin & Hoyer 用 0.01%/1%/10% 幂字塔；Bennett 用 20% 承载力份额；Turchin 2013 美国案例用"顶尖法学院学位数"；Orlandi 清代用"人均进士数"——**这些不是同一个量** | `cliodynamics-secular-cycles` §7.7 |

### 12.2 文献根本没有可用参数（阈值只能是我们编的）

| # | 量 | 状况 | 出处 |
|---|---|---|---|
| 9 | 语言分化树的形状 | 22 份简报中**找不到任何可核验的经验散布** | `emergence-verifiability` F16 第 4 条 |
| 10 | 思想运动的扩散 | 同上 | 同上 |
| 11 | 宗教内容的演化 | 同上 | 同上 |
| 12 | 前现代东亚的 Zipf 指数 | 检索**未找到**针对中国/东亚历史城市体系的 rank-size 专门研究 | `settlement-urbanization-spatial` §4.7 |
| 13 | settlement scaling 在中国考古数据上的值 | **真实空白**：找不到任何一篇把 Ortman/Bettencourt 框架应用于中国聚落数据的论文 | `settlement-urbanization-spatial` §4.7 §7.8 |
| 14 | 中国前现代运输的速度与成本 | 未取得可引用数值；**我们借用了 ORBIS 的地中海参数**，必须标 `BORROWED_MEDITERRANEAN` | `settlement-urbanization-spatial` §4.7 |
| 15 | 中国战争/叛乱规模的幂律指数 | 找不到经过 Clauset 式严格检验的研究 | `complex-systems-emergence` §6.6 |
| 16 | 前现代分政体类型的动员率上限 | "文献未提供可用参数" | `war-conflict-logistics` §4.6 |
| 17 | 草原每平方公里载畜量 / 每户所需牧场 | 二手来源明确说明未提供；本次未找到 | `war-conflict-logistics` §4.8 |
| 18 | 城市粮食腹地半径的具体公里数 | "文献未提供可用参数" | `settlement-urbanization-spatial` §4.7 |
| 19 | 前现代城市规模的物理上限 | 没有找到给出机制性上限公式的同行评议来源 | `settlement-urbanization-spatial` §4.7 |
| 20 | 灌溉的成本、维护与盐碱化 | 无可用参数 | `agriculture-carrying-capacity` §7.5 |
| 21 | 内卷的定量结论 | 无共识 | `agriculture-carrying-capacity` §7.6 |
| 22 | 从狩猎采集到农业的密度跃迁机制 | 没有机制模型 | `agriculture-carrying-capacity` §7.7 |
| 23 | 前工业危机死亡率的分布参数 | "文献未提供" | `population-dynamics` §7.4 |
| 24 | Boserup 棘轮的咬合条件 | 没有被形式化（重大缺口） | `population-dynamics` §7.3 |
| 25 | 华北黄土区的轮垦/连作衰减机制 | 未量化 | `agriculture-carrying-capacity` §7.4 |

### 12.3 方法论上无法验证的（这一类最重要）

| # | 量 | 为什么无法验证 | 出处 |
|---|---|---|---|
| 26 | **POM"多少条模式才够"** | 文献未提供可用阈值；"这个数字只能由我们自己预注册，然后不许中途改" | `abm-methodology` §4.8；`emergence-verifiability` F1 |
| 27 | **空模型支配阈值 τ**（我们用了 90%） | Janssen 只报告"外生空模型误差高 10–50%"这一事实，**没有说多少算'agent 行为有贡献'** | `abm-methodology` §4.8 |
| 28 | **涌现认证所需的种子数**（我们用了 N=50） | 文献未提供任何"多少种子够"的指导；N≥50 是 `abm-methodology` 自编的 D 级数字 | `abm-methodology` §4.8 §9 第 2 条 |
| 29 | **多层级 ABM 的聚合/解聚误差界** | 综述指出 Zoom 范式有"信息损失"，但**未给出可用的误差界或守恒律形式**。这是本项目必须自己做实验确定的量 | `abm-methodology` §4.8 |
| 30 | **数千年尺度社会 ABM 的 agent 规模上限** | 文献未提供；已知的极端规模数字（17 亿 / 5000 亿）都来自行为规则极简的生物细胞级 agent，**不可外推** | `abm-methodology` §4.8 |
| 31 | **LLM 在长期社会模拟中的可接受调用频率/成本模型** | 文献未提供，仅有"成本随人口二次增长"的定性表述 | `abm-methodology` §4.8 |
| 32 | **算子分裂误差的阶数与对易子形式** | `computational-feasibility` 明确标注为"[教科书知识，未核实]"，**不得作为 A 级证据引用** | `computational-feasibility` S6 说明 |
| 33 | **「剧情树能否骗过涌现度量」** | **没有任何文献做过这个研究。** 我们的诱饵世界（§2）就是要生产这份知识；**在它产出之前，本项目的一切涌现声明都是未验证的** | `complex-systems-emergence` §9 第 18 条 |
| 34 | **我们自己发明的全部判据的伪阳性率** | 类型抹除测试、反事实盲测、链式不可能性账、三诱饵世界标定协议、模式预算账本、`explanation_bits ≥ surprise_bits`、"功效不足的判据不得进验收集"、"机制间部分可替代是涌现的正面指纹"——`emergence-verifiability` §9 明确列为"我自己发明、无任何来源的东西"；本规格追加：荒诞度置换不变性 T-ABS、novelty/surprise 三量分离、密封清单的 5%/60% 双边阈值 | `emergence-verifiability` §9 末段 + 本文 |
| 35 | **世界内历史学家的错误率的"正确"水平** | 没有外部锚。我们知道准确率过高是失败信号（说明它在直接读数据库），但不知道正确值是多少 | `pseudo-simulation` S13 |
| 36 | **本规格自己编的全部阈值** | τ=4 bits、σ(e)≥0.5、R²_shortcut>0.8、C_7 ∈[0.3,0.6]、清单外簇 15%、CV≥0.6、3σ/5σ 阶跃、ZB<0.95、PS 的 [0.10, 0.80] 带、lift<2.0、KS<0.10、luck_excess>20 bits、T>2000 年——**全部 D 级** | 本文，逐条已在正文标注 |

### 12.4 原理上无法验证的（这一类不会因为多做研究而缩短）

| # | 量 | 为什么原理上无法验证 |
|---|---|---|
| 37 | **"这个世界像不像一个真实文明"** | 真实历史是**一次实现**。Clauset 2018 的结论说明了这一点——"长和平"与之前的大暴力期**都不能与平稳过程的涨落区分**，要让"长和平"成为统计显著的趋势还需要再持续 **100–140 年**。一次实现里的"罕见"根本不可估（`complex-systems-emergence` §8.11；`emergence-verifiability` F3） |
| 38 | **L4（人类回路）是否被污染** | 全部代码层措施对它免疫（`pseudo-simulation` L4 层级表）。§8 的流程留痕**由我们自己维护**，因此它检验的是我们的纪律，不是我们的正确性。K7 金丝雀（§2.2）会实验性地确认这一点：内核干净但只展示 P95 的运行，**零条判据会变红** |
| 39 | **L5（目标反噬）是否发生** | 它污染的是评价函数本身。我们能做的只有角色分离与用语规范（§8.8），这两者都无法被检验 |
| 40 | **等效性（equifinality）** | 同一观测输出可由许多不同参数组合与许多不同机制产生。Epstein 的答案是"裁决多个生成者的唯一办法是收集新的微观数据或设计新的微观尺度实验"——**而我们的世界没有外部微观数据可收集** |
| 41 | **L0 schema 漏掉的维度** | 如果 state schema 本身没有表示某类现象所需的状态（例如"仪式性竞赛替代战争"所需的状态），该现象既不会发生，也不会被密封清单测试或词表增长测试发现（§9.4 的残余风险） |
| 42 | **判据的形态偏置** | 我们能拿到经验散布的量全都是关于城市、战争、财政、政体规模的——因为只有这些有考古与统计数据。任何不产生这些量的文明形态会被系统性判低分。**这是一条我们以严谨之名亲手装上的隐形科技树**，形态条件化与"允许缺席"判据（P-STA-02）只能缓解，不能消除（`emergence-verifiability` F14、F18） |

### 12.5 这份清单的使用规则

1. **它必须出现在每一份对外报告的目录里**，不能只放在附录。
2. **任何"我们证明了 X"的表述，必须先检查 X 是否依赖本清单上的任何一项。** 若依赖，表述改为"我们观察到 X，但 X 依赖 <第 N 项>，该项无法验证"。
3. **高验证等级 / 低验证等级两类结果必须显式分开**（`emergence-verifiability` F18）：后者可以生产、可以展示，但在任何"我们证明了"的表述里必须标注为未验证。**不接受这个取舍的错误方式是：假装判据是形态中立的。**
4. 清单每个里程碑复核一次，只增不减；每次复核的 diff 进 `DECISION-REGISTER.md`。

### 这一节禁止了什么

- 禁止缩短这份清单，除非附上新的可核验经验来源与提交记录。
- 禁止把本清单上的量用作校准目标或验收判据。
- 禁止在报告里只写高验证等级的结果而不标注低验证等级的部分。
- 禁止把"我们的模拟匹配了 Seshat 的模式"当成强证据（Seshat 的编码约定足以翻转结论，且旗舰论文已撤稿）。
- 禁止把本规格自创的判据（第 34、36 项）当作已验证的方法学。它们必须先在诱饵世界上标定。

---

## 13. 汇总

### 13.1 写第一行内核代码之前必须签字的 11 项

| # | 决定 | 为什么事后补不回来 |
|---|---|---|
| V3 | 预注册的通过规则与 FDR 家族划分 | 预注册按定义不能事后做 |
| V5 | 零模型作为同一内核的开关（`MechanismSwitches`） | 事后拆机制 = 重写内核；两份代码会漂移（Turchin 2013 的 `ε_max`/`Δ` 不一致就是先例） |
| V6 | primitive/composite 词汇表分层 + T-ERASE | 类型分层是内核 API 的形状 |
| V9 | 荒诞度的污点架构（observer 输出打 taint） | 污点传播必须贯穿整个数据流，事后加等于重写 |
| V10 | 反剧情树宪章 + GATED 计数基线 | 基线只能从零开始建；事后建基线等于给已有的违章发赦免 |
| V11 | 运行登记表 + canon seed 规则 + canon/lab 类型分离 | **不从第一天记，事后永远无法证明我们没有挑选** |
| V12 | 参数改动三分类账 | 同上；且 `aesthetics` 计数一旦丢失就无法重建 |
| V13 | 密封清单 | 看过输出之后再写，这个测试就死了 |
| V14 | 算力四方分账与 T_run 上限 | 预算决定本体论；反过来做会设计出跑不起来的世界 |
| V15 | 自由参数配额与 `source:`/`free:` 标注规范 | 事后给 300 个参数补溯源不可行 |
| V17 | `--spike` main 与红 main 暂停规则 | URR 病：三个月后仓库里有 40 篇 md、一个精美的本体论、和 0 个能跑到底的 main |

### 13.2 CI 测试总表

| 层 | 测试 | 频率 | 失败后果 | 来源 |
|---|---|---|---|---|
| L1 一致性 | 守恒审计 A1（int64 精确相等） | 每 tick | HALT | `emergence-verifiability` F12 |
| L1 | 并发占用检验 A2 | 每 tick | HALT | 同上 |
| L1 | 信息光锥 G2 | 每事件 | 硬失败 | `emergence-verifiability` F17 |
| L1 | 后勤上界 G3 | 每军事事件 | 硬失败 | `war-conflict-logistics` §4.1–4.3 |
| 确定性 | bit 级重放 / 线程数不变 / 迭代顺序不变 / 跨机器不变 | 每提交 | 构建失败 | `computational-feasibility` F2 |
| 确定性 | 步长减半不变性（**窗口必须覆盖崩溃期**） | nightly | 构建失败 | `computational-feasibility` S6 |
| 反脚本 | T-ERASE（类型抹除） | 每提交 | 构建失败 | `emergence-verifiability` F5 |
| 反脚本 | T-ABS（荒诞度置换不变性） | 每提交 | 构建失败 | 本文原创 D 级 |
| 反脚本 | 内核 → 观察器单向依赖 | 每提交 | 构建失败 | `emergence-verifiability` F5 |
| 反脚本 | 污点传播检查（`--audit`） | nightly | HALT | 本文原创 D 级 |
| 反脚本 | `GATED_COUNT` 不上升 | 每提交 | 构建失败 | `pseudo-simulation` S3 |
| 反脚本 | 读取集差集 `declared \ measured == ∅` | 每提交 | 构建失败 | `pseudo-simulation` F3 |
| 参数卫生 | 参数活性测试 | 每提交 | 构建失败 | `abm-methodology` M9 |
| 参数卫生 | 矩位移测试 | 每提交 | 构建失败 | 同上 |
| 参数卫生 | 自由参数配额 12+3 | 每提交 | 构建失败 | `computational-feasibility` S2 |
| 参数卫生 | `justification_class == 叙事` 计数为 0 | 每提交 | 构建失败 | `llm-storytelling` F7 |
| 性能 | CPLX-1 log-log 斜率 ≤ 1.2 | 每提交 | 构建失败 | `computational-feasibility` S4 |
| 性能 | CPLX-3 `T_run` 外推门 | 每提交 | 构建失败 | `computational-feasibility` F1 |
| 性能 | CPLX-4 晚期负载比 | nightly | 报警 | 本文 D 级 |
| 性能 | spike main ≤ 1.8×10¹¹ 归一化周期 + SPIKE-1/2/3 | 每提交 | 构建失败；连红 7 天全项目暂停 | `prior-art-postmortem` §1.9 |
| 零模型 | N0–N5 增益报告（玩具世界） | 每 PR（改机制时） | 合并阻塞 | `prior-art-postmortem`【致命 4】 |
| 诱饵 | W1a + W3 + 健康（20 种子 × 300 年） | 每 PR | 检出率下降 >0.15 即构建失败 | `pseudo-simulation` F6 |
| 诱饵 | 全部 8 个诱饵 × 200 种子 | nightly | 报告 | 同上 |
| 疫病 | 反平衡器诊断 P-POP-03 / P-POP-06 | nightly | 构建失败 | `epidemics-disease` §3.14 |
| 信息 | 信念–事实背离度 > 0（P-MET-04） | nightly | 构建失败 | `emergence-verifiability` F8 |
| — | **模式电池** | **里程碑** | **不进 CI 红绿**，只出评审工件 | `pseudo-simulation` S11 |
| — | **任何宏观结果断言** | **禁止** | — | 同上 |

### 13.3 交付物清单（Phase 0 的验证侧）

1. `validation/patterns/*.toml` —— 模式电池 v0（51 条），哈希提交。
2. `validation/decoys/` —— W1a–e、W2、W3 的可运行内核变体。
3. `validation/calibration_report_<hash>.md` + `.json` —— 判据标定报告（含 K7 页与被删判据清单）。
4. `validation/null_models/` —— N0–N5 的开关配置与 `null_gain_report` 生成器。
5. `charter/anti_plot_tree.toml` + `charter/gated_baseline.toml` —— 反剧情树宪章。
6. `charter/rejection_conditions.md` —— R1–R25，签字版。
7. `charter/cannot_verify.md` —— §12 的清单，只增不减。
8. `registry/run_registry.sqlite` —— 从第一次超过 100 年的运行开始。
9. `params/*.toml` —— 带 `source`/`free`/`justification_class`/`change_log` 的参数集。
10. `sealed/sealed_list_v0.age` + DECISION-REGISTER 里的承诺哈希。
11. `worlds/basin600/` —— CI 级玩具世界（地图 + scale_factor.toml）。
12. `bin/spike` —— 60 秒 3000 年 main，含 SPIKE-1/2/3。
13. `docs/speed_table.toml` —— 信息传播速度表（标 `BORROWED_MEDITERRANEAN`）。
14. `docs/complexity_contract.md` —— §10.3 的表，每行有 owner 签字。
15. `docs/power_analysis.md` —— 每条验收候选判据的功效分析（当前全部 `pending`）。

### 13.4 与另外三份规格的接口

| 对方规格 | 本规格依赖它的什么 | 它依赖本规格的什么 | 潜在冲突 |
|---|---|---|---|
| `spec-world-state` | 定点整数与守恒审计（§2.5）；T-ERASE（§3.3）；primitive/composite 分层（§3.1）；禁止字段黑名单（§2.4）；实体硬上限（§2.2）；相位顺序与步长减半测试（§5.5）；CBRNG 流布局（§6.4） | 自由参数配额；复杂度契约的截断常数；玩具世界的地图规格；`MechanismSwitches` 的存在与"只在 t=0 读一次"的约束 | **冲突 1**：该规格的年增量估算 52 MB/yr → 156 GB/线，**超过** `computational-feasibility` 的 73 GB/线预算。本规格 §10.9 采纳"不存轨迹存配方"作为解，但这要求 `T_run ≤ 1 h` 成立；若实测 `T_run` 超标，两边都要重开。**冲突 2**：该规格已把 `significance`/`importance` 列为"可以存在但只能在观察层"，本规格 §6.4 的 L-ABS-2 污点检查比它更强（运行期数据流级），需要确认内核 API 支持 taint 传播。 |
| `spec-causality` | `significance(e)` 的定义（必须与事件类型解耦）；安慰剂零分布协议；读取集闭包；归因报告格式；因果视界 H_Y；`analyzer_version` 分层 | §5.3 A3/A4 的链式不可能性账与 σ(e) 的"无自报字段"约束；§10.2 的因果账户 25% 与"每个为什么 5,000–10,000 CPU-h"的配额；R9 的安慰剂分位阈值；P-MET-05 的不可解释率下界 | **冲突 3**：本规格 §6.5 要求审查抽样只按 `significance` 分层且每批 ≥50% 寻常事件；若 `spec-causality` 的 significance 泛函本身带有形态偏置（只提名有城有战有税的变化），这条对称化会失效。需要在标定报告里加一列：significance 在 W1 家族上的提名分布。**冲突 4**：因果预算 25% 与验证预算 50% 不得互相挪用，但两者都要用同一批长跑的快照；需要明确"共享快照不算共享预算"的记账规则。 |
| `spec-llm-boundary` | LLM 权限矩阵（对因果图与信念库的可写性必须全为否）；`π` 的形式规格；LLM-on/off 孪生线的**降级用途**（`llm-storytelling` F6 已推翻它作为长期指标分母）；ledger 内容寻址与"重放 miss 即致命错误" | §5.2 G4 的 `irrationality_bits` 与效用分解落盘时点；N1（决策随机化）与 N2（贪心）作为 LLM 消融的对照臂；§10.8 的调用配额（同时是成本控制与污染控制）；R13 的 D 级分布占比披露 | **冲突 5**：`llm-storytelling` F6 判定 `event_rate_ratio = f_on/f_off` 是坏分母（分叉后两条线不是同一个世界，且控制组可被拟合到处理组上）。本规格因此**不把孪生线写进模式电池**，改用决策点级的 `D_KL(p_LLM ‖ π)`；但这要求 `π` 本身被拟合而非撰写，而 `π` 的拟合目标来自本规格 §1 的模式电池——**这是一个循环**。缓解：π 的拟合目标只能取自 `observation` 集与外部经验散布，**不得取自 `sealed_acceptance` 集**。这条约束必须写进 `spec-llm-boundary`。**冲突 6**：本规格要求"世界在 LLM 完全关闭时必须能独立跑完三千年"（否则 N1/N2/spike 都不成立），这与"LLM 负责文化创造"的纲领第 5 条存在张力，裁决权在 `spec-llm-boundary`。 |

### 13.5 本规格没能解决、必须由人裁决或后续研究的问题

1. **验收集在标定完成前是空集** —— 这在工程上是正确的，但在项目管理上意味着 Phase 1 相当长一段时间里**没有任何"通过"的定义**。谁来决定这段时间的里程碑标准？本规格给不出答案，只能给出"不许用未标定判据"这条禁令。
2. **13/25 条拒绝条件的阈值是 D 级** —— 标定它们需要诱饵世界先跑起来，而诱饵世界的设计又部分依赖于我们对失败形态的预期。这是一个鸡生蛋问题，本规格选择"先写下 D 级数字并公开标注"，而不是留空。
3. **形态偏置无法消除，只能缓解** —— P-STA-02（允许缺席）与形态条件化都只是缓解。**本项目最有价值的那类结果（人类历史上从未出现的文明形态）恰好是最难验证的**（`emergence-verifiability` F18）。这个取舍必须由人明确选择，不能默认。
4. **验证会让项目慢 3–10 倍** —— `emergence-verifiability` F19 的原话，并给出了替代路线："如果团队不接受这个代价，那么诚实的做法是把项目目标降级为『生成有内部一致性的历史文本』——这是一个正当的、有价值的目标"。**这个选择必须由人做，且必须书面做。**
5. **π 与模式电池的循环依赖**（冲突 5）—— 本规格给的缓解（π 只对 observation 集与外部散布拟合）会削弱 π 的质量。是否有更好的解，本规格不知道。
6. **K7（策展）与 L5（目标反噬）没有技术解** —— 只有流程留痕与角色分离，而这两者的有效性无法被本项目自己检验。
7. **`novelty_bits` 的窗口 W=500 年与共现分布的平滑方式** —— 完全没有依据。W 太小则一切都新颖，W 太大则一切都陈旧。需要在玩具世界上做敏感性分析。
8. **模式电池 v0 的 51 条里，32 条 A 级证据中有多少能真正迁移到东亚青铜时代**，本规格无法判断。例如 P-WAR-01 的 α̂=1.53 来自 1823–2003 的国际战争，而同一来源明确写着"只覆盖 1816 年后；前现代战争没有可比的伤亡数据库"（`war-conflict-logistics` §4.7；`emergence-verifiability` F10）。我们用的是"落在 [1,3] 区间"这种极弱的形式，但这个弱化是否足够，不知道。

### 这一节禁止了什么

- 禁止在 13.1 的 11 项签字之前写内核代码。
- 禁止把模式电池接进 CI 红绿（13.2 最后两行）。
- 禁止在 13.5 的问题 4 上默认——"慢 3–10 倍"这个代价必须被明确、书面地选择或拒绝。
- 禁止用 `π` 拟合 `sealed_acceptance` 集里的模式（冲突 5 的缓解措施）。
- 禁止把 13.4 的六个冲突当成"实现细节"推迟。冲突 1、5、6 都会改变内核 API 的形状。

---

## 附：本规格的诚实度自评

- 本规格提出的检查中，**有来源的**：守恒审计、信息光锥、后勤上界、词汇表检查、消融矩阵、多种子频率、零模型套件、外生序列置换、参数活性/矩位移、密封清单、词表增长、GATED 记账、运行登记表、canon seed 规则、参数三分类账、P/T 比、自由参数配额、复杂度契约、spike main、验证预算 ≥50%、因果预算独立。
- 本规格提出的检查中，**无来源、由红队自创（已标 D 级）**：类型抹除测试、反事实盲测、链式不可能性账、三诱饵世界标定协议、模式预算账本与开封即作废、`explanation_bits ≥ surprise_bits` 不等式、"功效不足的判据不得进验收集"、"机制间部分可替代是涌现的正面指纹"、组合口径 `absurdity`。
- 本规格**自己新增、两处都没写过的**（全部已在正文标注 ［本文原创，无来源，D 级］）：
  1. **判据证据量的对数似然比形式化**（§0.2），以及由它推出的"未标定判据的证据量 ≤ 0"。
  2. **`novelty_bits` / `surprise_bits` / `explanation_bits` / `luck_bits` 四量分离**——红队给了两个方案，把它们判定为**不同的量而非竞争方案**是本文的裁决。
  3. **荒诞度置换不变性检验 T-ABS**（§6.4 L-ABS-3）。
  4. **污点传播作为 lint 的第二层**（§6.4 L-ABS-2）。
  5. **ZB/PS 的具体数值形式与健康区间**（§4.3）。
  6. **多种子频率判据改写为 Clopper–Pearson CI 排除两端**（§4.5）。
  7. **密封清单的 5% 下界与 60% 反向报警**（§9.2）。
  8. **零模型开关"只在 t=0 读一次"的约束**（§3.3）。
  9. **自由参数两本账（global/regional）的拆分**（§10.5）。
  10. **spike main 的归一化周期数门槛与算术校验**（§10.7）。
  11. **BY 而非 BH 的多重检验校正**（§1.4）。
  12. **本规格全部 D 级阈值**（§12.3 第 36 项已逐条列出）。

**这些自创部分必须服从自己的规则：先在玩具世界与诱饵世界上标定，再决定哪些进验收集。如果标定结果显示某条检查在 W1 上也通过，那条检查应当被删掉，而不是被辩护。**（`emergence-verifiability` §7.4 末段的自我批评，逐字适用于本文。）
