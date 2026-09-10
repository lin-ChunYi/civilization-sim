# 集体行动、合作演化与治理

> ## ⚠️ 引文核验结果（2026-09-10 独立复核）
>
> 本次对 §10 中承重的 24 组引文逐条做了 Crossref 记录级复核。**没有发现任何伪造或拼接的文献**：所有承载硬数字的 13 篇全文来源（Boyd 2003、Nowak 2006、Gavrilets & Richerson 2017、Turchin et al. 2013、Powers & Lehmann 2014、Powers et al. 2016、Zhou et al. 2005、Mathew & Boyd 2011、Handley & Mathew 2020、Gracia-Lázaro et al. 2012、Rand et al. 2011、Baggio et al. 2016、Traulsen & Nowak 2006）作者、年份、刊名、卷页全部对得上。
>
> 两处需要注意：
> - **条目 31（Dreber et al. "Winners don't punish"）先前被误标为"未核验/未命中"，实际存在**：*Nature* 452:348–351 (2008), DOI `10.1038/nature06723`。§7.1 因此不再需要因"文献查无此文"而回避该争议——但全文数值本次仍未取得，引用时只能用定性方向。
> - **条目 3（Nowak 2006）在 §10 中缺卷页**，正确为 *Science* 314:1560–1563。
>
> **仍然未找到、因此不得承载结论的条目**：Lam, W.F. (1998) *Governing Irrigation Systems in Nepal*；Wade (1988) *Village Republics*；Baland & Platteau *Halting Degradation of Natural Resources*；Chaudhuri (2011)；Guzmán et al. (2007)。受影响的结论：**§4.13「农户管理灌溉系统绩效优于机构管理」这一对比至今没有任何本次可核验的来源支撑，必须继续按参数缺口处理，不得写出数值**；§10.2 中与 Chaudhuri / Guzmán 相关的实验室公共品与规范传播论断同样无来源。Wittfogel (1957) 与 Holmström (1982)、Alchian & Demsetz (1972) 本次已补充核验为真实文献（详见 §10 对应条目）。

- **slug**: `collective-action-cooperation`
- **一句话范围**: 组织（国家、宗教、军队、水利、行会、宗族）在模拟中"自发出现并存续"所需的最小机制集合 —— 公共品供给函数、监督与惩罚（含二阶搭便车）、声誉与信息半径、退出成本、群体间竞争、承诺装置 —— 以及可直接写进内核的函数形式、参数量级与失效条件。
- **交付日期**: 2026-09-09
- **检索状态**: 本次会话 WebSearch 配额已在本任务开始前耗尽（200/200）。所有验证通过 **Crossref REST API**、**OpenAlex API**、**PubMed Central (PMC) 全文与 idconv API**、以及少数开放期刊站点完成。详见 §10 与末尾《检索覆盖说明》。凡是本次未能真实打开、只凭记忆写下的文献，一律在 §10 标注 `[未核验]`，并且**不用它承载任何量化结论**。

---

## 0. 给工程实现的一页摘要（先读这个）

如果只从本简报拿走一件事，是这件：

> **合作不是 agent 的一个属性，合作是一个博弈的均衡结果。任何把"合作/忠诚/凝聚力"实现为 agent 身上一个标量的设计，都会在数学上抹掉产生它的全部约束条件，从而让模拟失去因果链。**

具体地，一个"组织"在本项目里应当是下面六个可计算对象的组合，而不是一个 `Organization` 对象加一个 `loyalty: float`：

| # | 对象 | 类型 | 决定它的东西 |
|---|---|---|---|
| 1 | **供给函数** `P(X)` | 群体总努力 → 公共品产出（凹函数或 contest 函数） | 地理、技术、工程规模 |
| 2 | **收益分配规则** `share_i` | 谁拿多少 | 制度（可被 leader 篡改，见 5） |
| 3 | **监督概率** `q_i` | 个体行为被观测到的概率 ∈ [0,1] | 群体规模、空间距离、信息技术、层级数 |
| 4 | **执法能力与成本** `(κ, δ, c_mon)` | 惩罚强度、执法者成本、监督成本 | 武力垄断程度、是否有专职执法者、二阶搭便车是否被解决 |
| 5 | **退出成本** `C_D` | 个体离开该组织的代价 | 地形、无主地可得性、资产专用性（灌溉渠/定居/储藏） |
| 6 | **群体间竞争压力** `ε_conflict` | 群体被吞并/灭绝/文化覆盖的年概率 | 邻居密度、军事技术、地形 |

**这六个量全部由地理/技术/人口/制度史内生决定；"合作水平"是它们的输出，不是输入。** 只有一个例外可以做成 agent 身上的标量：**规范内化权重 η（norm internalization）**，因为它在文献里本来就是一个"把物质收益与规范收益加权"的偏好参数，而且它自身必须由群体间竞争史演化出来（Gavrilets & Richerson 2017，§2.11、§3.M13）。

**最小可涌现集合（本简报的核心答案）**：在一个 agent 模拟中，让合作与组织自发出现，最少需要同时具备下面 **5 项**；缺任何一项，都会得到一个已知的病态结局：

1. **重复互动 + 折现**（`w > c/b`）—— 缺了它，一次性博弈中背叛严格占优，任何组织都不会诞生。
2. **局部信息与声誉**（`q > c/b`）—— 缺了它，规模一超过面对面互动上限（~30–50 人）就崩。
3. **可被滥用的、成本随违规率下降的惩罚**（Boyd et al. 2003 的关键条件）—— 缺了"成本随违规率下降"，惩罚机制在数学上完全失效（该文 Fig.4）；缺了"可被滥用/可被反击"，会得到一个不真实的顺从社会（Herrmann et al. 2008；Nikiforakis 2008）。
4. **退出成本 `C_D` 作为独立状态变量**（Powers & Lehmann 2014）—— 缺了它，无法内生出"从平等到专制"的转变，专制只能靠脚本给。
5. **群体间竞争（含制度的群体级复制与灭绝）**（`b/c > 1 + n/m`，Traulsen & Nowak 2006；Turchin et al. 2013 的 ethnocide 机制）—— 缺了它，大规模合作在个体层面选择下会被侵蚀，且制度无法在长时段积累。

第 6 项**不是必需但极大增益**：**伙伴选择 / 可流动的互动网络**（Rand et al. 2011：30% 重连率能维持合作，10% 不能）。注意这一项不是"网络拓扑加成"，见 §8 反模式 4。

---

## 1. 本简报要回答的问题

1. Olson 的集体行动逻辑在一个 agent 模拟里应当以什么形式存在？"群体越大越难合作"是否可以直接实现为规模惩罚项？
2. Hardin 的公地悲剧哪一部分被推翻了？被推翻的部分对模拟意味着什么（即：什么时候资源应该崩溃，什么时候不应该）？
3. Ostrom 的设计原则能不能变成一个可计算的"组织存续判定器"？它的证据强度到什么程度，样本偏差在哪里？
4. 公共品博弈 + 惩罚（Fehr & Gächter；Boyd/Gintis/Bowles/Richerson）里，哪些参数是真实有文献数值的，哪些是必须我们自己选的？
5. 二阶搭便车（谁来惩罚不惩罚的人）在模拟里有哪几种可实现的解法？各自的成本是什么？
6. 多层次选择与文化群体选择：在什么条件下大规模合作能被群体间竞争维持？文化变异是否真的足够大到让群体选择有效（量化）？
7. 亲缘选择能撑到多大规模？宗族组织在东亚为什么长期是主要的合作载体？
8. principal-agent 与监督成本：一个政体的规模上限是否可以从"监督概率随距离衰减"推出来？有没有东亚的量化锚点？
9. 可信承诺（credible commitment）如何实现为一个可计算的状态量，而不是一个"制度 buff"？
10. 网络结构对合作到底有多重要？`b/c > k` 规则在人类实验中站得住吗？
11. **最小机制集合是什么？**（见 §0）
12. **如果直接给 agent 一个"忠诚度"数值，会掩盖哪些真实的集体行动约束？**（见 §8 反模式 1，这是本简报最长的一节）

---

## 2. 已有成熟模型与理论

### 2.1 Olson：集体行动的逻辑（1965）

- **核心机制**：公共品的非排他性使个体最优行为是搭便车；除非群体足够小、或存在"选择性激励"（selective incentives）、或存在不成比例受益的大成员（"privileged group"），否则集体物品供给不足。
- **形式化程度**：书中为半形式化（言语论证 + 简单代数），但被后续公共品博弈完全形式化。
- **状态变量**：群体规模 `n`；个体从公共品中获得的份额 `F_i`；私人成本 `c`；选择性激励 `s_i`。
- **参数**：无经验参数。
- **适用范围**：任何非排他性收益的集体项目 —— 在本项目中即：城墙、堤坝、渠道、军队、宗教仪式、市场秩序、公共仓储。
- **已知局限**：（a）"群体越大越难合作"在实验室里**不是**单调成立的 —— 群体规模效应依赖于 MPCR（边际人均回报）与技术的规模报酬，Isaac, Walker & Williams (1994) 专门做了大群体实验，方向并非简单负相关（本次仅核验到该文元数据，未取得数值，故规模效应的方向在本简报按 **C 级**处理）；（b）Olson 完全没有惩罚与声誉机制，因此系统性低估了小规模社会的自组织能力（Ostrom 的整条研究线就是对此的经验反驳）。
- **出处**：Olson, M. (1965) *The Logic of Collective Action*, Harvard University Press, DOI `10.4159/9780674041660`（本次核验元数据）。
- **对模拟的意义**：Olson 给的是**问题陈述**，不是解。工程上应当把它实现为"默认状态"：**任何新的公共品项目，若不附带监督/惩罚/声誉/选择性激励，其均衡供给量应当趋于 0**。这是我们判断"组织是否真的涌现了"的零假设基线。

### 2.2 Hardin：公地悲剧（1968）及其被反驳的部分

- **核心机制**：共享资源上每个使用者的边际私人收益 > 边际私人成本（因为退化成本被分摊），故过度使用至资源崩溃。
- **形式化程度**：定性 + 一个牧场比喻；没有模型。
- **被推翻的部分（重要）**：Hardin 描述的是 **open access（开放进入、无制度）**，而非 **common property（共有产权、有制度）**。Ostrom (1990) 及其后续大量案例研究表明，具备边界、规则、监督与分级制裁的共有产权制度可以长期避免崩溃。Baggio et al. (2016) 的 69 案例编码集给出定量对照：**成功案例平均具备 8.7 ± 2.6 条设计原则，失败案例 4.3 ± 2.7 条**。
- **仍然成立的部分**：在**没有**制度、或制度被规模/异质性/外部冲击破坏时，Hardin 的动力学是正确的。
- **出处**：Hardin, G. (1968) Science 162:1243–1248, DOI `10.1126/science.162.3859.1243`（本次核验元数据）。
- **对模拟的意义**：**资源崩溃必须是"制度失效"的下游结果，不能是默认结果，也不能被禁止。** 工程上：资源子系统里同时实现"开放进入动力学"和"制度约束动力学"，由一个 `institution_state` 开关在两者间切换；开关本身由 §3.M12 的存续判定器驱动。

### 2.3 Ostrom：公共池塘资源治理与设计原则（1990 起）

- **核心机制**：长期存续的 CPR 制度共享一组结构特征（design principles, DP）。它们不是"规则内容"，而是"规则的元性质"：边界清晰、成本收益与本地条件相称、受影响者参与规则制定、监督、分级制裁、廉价冲突解决、被外部承认的自组织权、以及多层嵌套。
- **形式化程度**：**定性理论 + 大量案例编码**。Ostrom 本人从未把 DP 写成方程；后续 QCA/集合论分析（Baggio et al. 2016）把它们变成布尔组合条件。
- **可用的操作化版本（本次核验的 11 条，Baggio et al. 2016）**：
  - `1A` 清晰的社会边界（clearly defined social boundaries）
  - `1B` 清晰的生物物理边界（clearly defined biophysical boundaries）
  - `2A` 规则与本地条件的一致性（congruence between local conditions and rules）
  - `2B` 投入/取用的比例性（investment/extraction proportionality）
  - `3` 集体选择安排（collective choice arrangements）
  - `4A` 监督（monitoring）
  - `4B` 对监督者的监督（monitoring the monitors）
  - `5` 分级制裁（graduated sanctions）
  - `6` 冲突解决机制（conflict-resolution mechanisms）
  - `7` 组织权（rights to organize）
  - `8` 嵌套性（nestedness）
- **状态变量**：每条 DP 的有/无（可扩展为 [0,1] 强度）；资源系统属性；使用者属性。
- **参数与经验强度**：Baggio et al. (2016) —— 69 个案例（25 林业 / 24 灌溉 / 20 渔业），其中**仅 27 个案例所有 DP 都被完整编码**；成功组 8.7 ± 2.6 条 vs 失败组 4.3 ± 2.7 条；**`2A` 与 `2B`（一致性与比例性）在成功/失败案例间差异最显著**；`1B`、`2B`、`4B`、`6` 被识别为**必要但不充分**条件；`2A`、`2B`、`4` 的缺失大幅提高失败概率。
- **已知局限**：（a）**样本偏差**：案例文献本身偏向"有趣的"成功与失败，且 69→27 的完整编码率意味着结论建立在小样本上；（b）**因果方向未定**：DP 可能是存续的结果而不是原因（长期存续的系统有时间发展出这些特征）；（c）DP 是**组合性（configural）**的，不是加法的 —— 这直接否定了"每条 DP 给一个 buff"的实现方式。
- **出处**：Ostrom, E. (1990) *Governing the Commons*, Cambridge University Press, DOI `10.1017/cbo9780511807763`（核验元数据）；Ostrom, Walker & Gardner (1992) APSR 86:404–417, DOI `10.2307/1964229`（核验元数据）；Ostrom (2009) Science 325:419–422, DOI `10.1126/science.1172133`（核验元数据；**全文本次未取得**，被 repositorio 的 bot 防护挡住）；Cox, Arnold & Villamayor-Tomás (2010) Ecology and Society 15(4):38, DOI `10.5751/es-03704-150438`（核验元数据；**全文 403，未取得**）；Baggio et al. (2016) International Journal of the Commons 10:417, DOI `10.18352/ijc.634`（**元数据 + 全文均已核验**）。

### 2.4 公共品博弈 + 惩罚：Fehr & Gächter 的实验线

- **核心机制**：在标准线性公共品博弈里加入第二阶段"付费惩罚"，合作率不再衰减而是维持甚至上升；去掉惩罚阶段则合作迅速崩溃。惩罚是**利他的**（punisher 自己净亏），因此本身构成一个二阶公共品。
- **形式化程度**：完全形式化（线性 PGG + 惩罚技术），但**关键实验参数本次未能核验**。
- **状态变量**：贡献 `x_i`、惩罚点数 `p_ij`、MPCR、期数、匹配方式（partner / stranger）。
- **参数**：⚠️ **文献未提供本次可核验的参数值。** Fehr & Gächter (2000, AER 90(4):980) 与 (2002, Nature 415:137–140) 均为封闭获取（OpenAlex 确认 `is_oa: false`，无 OA 副本）。我记忆中的"n=4、MPCR=0.4、1:3 惩罚兑换率、10 期"等数值**本次未核验，不写入参数表**。
- **适用范围**：小群体、面对面或匿名一次性回合、短时间视野。
- **已知局限（对模拟极重要）**：
  - **反社会惩罚（antisocial punishment）**：Herrmann, Thöni & Gächter (2008) Science 319:1362–1367 —— 跨社会实验发现惩罚会被用于打击**高贡献者**，且这种反社会惩罚的强度随社会而异。
  - **反惩罚（counter-punishment）**：Nikiforakis (2008) J. Public Economics 92:91–112，题目本身即 "Can we really govern ourselves?" —— 允许被惩罚者反击后，惩罚的净收益被摧毁。
  - **时间视野**：Gächter, Renner & Sefton (2008) Science 322:1510，题为 "The Long-Run Benefits of Punishment" —— 主张惩罚的净收益只在长时间视野下才为正。（本次仅核验元数据；具体期数对比**未核验**。）
  - **真实社会的惩罚形态不同**：Bowles, Boyd, Mathew & Richerson (2012) BBS 35:20–21，题为 "The punishment that sustains cooperation is often coordinated and costly" —— 实验室里的"个体第三方惩罚"不是田野中的主要形态；田野中惩罚是**协调的、集体决定的、且对执法者本身昂贵的**。
- **出处**：以上各条均核验元数据（Crossref/OpenAlex）。另：Fehr & Fischbacher (2004) Evolution and Human Behavior 25:63–87, DOI `10.1016/s1090-5138(04)00005-4`（第三方惩罚，核验元数据）；Yamagishi (1986) JPSP 51:110–116, DOI `10.1037/0022-3514.51.1.110`（"制裁系统本身是一个公共品"，核验元数据）。
- **对模拟的意义**：把惩罚实现为**制度性的、协调的、需要被供给的**（即"执法机构"本身是一个二阶公共品项目），而不是每个 agent 私下扣别人分。见 §3.M2 与 §3.M14。

### 2.5 Boyd, Gintis, Bowles & Richerson (2003)：利他惩罚的演化 —— **本简报参数最硬的一篇**

- **核心机制**：多群体文化演化模型。三种类型：Contributor（合作不惩罚）、Defector（不合作不惩罚）、Punisher（合作且惩罚）。群体间通过冲突/灭绝进行群体选择，群体内通过收益差异进行个体选择。
- **形式化程度**：**完全形式化 + 数值模拟**。
- **收益函数（该文原式，本次自 PMC 全文核验）**，设群体中 contributor 比例 `x`、punisher 比例 `y`：
  - Contributor: `b(x+y) − c`
  - Defector: `b(x+y) − p·y`
  - Punisher: `b(x+y) − c − k(1 − x − y)`
- **状态变量**：每个群体的 `(x, y, 1−x−y)`；群体数 `N`。
- **参数（该文 base case，全部自全文核验）**：
  - 合作成本 `c = 0.2`
  - 惩罚成本 `k = 0.2`
  - 被惩罚成本 `p = 0.8`（= 4k，"四倍于惩罚成本"）
  - 执行误差率 `e = 0.02`
  - 迁移率 `m = 0.01`
  - 突变率 `μ = 0.01`
  - 群体冲突概率 `ε = 0.015`（作者称其蕴含约 **0.0075 的群体灭绝率**，并称"与近期对小规模社会文化灭绝率的一个估计一致"——**该原始估计的出处本次未追溯**）
  - 群体数 `N = 128`
  - 作者自述："Base case parameters were chosen to represent cultural evolution in small-scale societies."
- **量化结果（全部自全文核验）**：
  - **无惩罚**：群体选择只能在"很小的群体"里维持高合作；Fig.1a 显示群体规模超过约 **50** 人后合作在所有测试的冲突率（0.003 / 0.015 / 0.075）下都迅速崩溃。
  - **有惩罚**：合作可在 **~100 人量级**的群体里维持。
  - **⚠️ 决定性的失效条件**："punishment leads to increased cooperation only to the extent that the costs associated with being a punisher decline as defectors become rare." 当惩罚成本被设为**固定**（不随 defector 变稀少而下降）时，**该机制完全失效**（Fig.4）。
  - 迁移敏感性：迁移率上升时合作"precipitously"下降；有惩罚时在所有混合率下都能支持更大群体，但在最大群体 + 高混合率下仍会失败（Fig.2）。
  - `p` 值降低导致合作水平大幅降低（Fig.3）。
- **已知局限**：文化演化速率、迁移率、群体灭绝率这三个参数的经验基础都很薄；模型是无空间的（well-mixed groups + 全局群体池）。
- **出处**：Boyd, Gintis, Bowles & Richerson (2003) PNAS 100:3531–3535, DOI `10.1073/pnas.0630443100`, PMC152327（**元数据 + 全文均核验**）。

### 2.6 Nowak (2006)：合作演化的五条规则 —— **最紧凑的可实现条件集**

自 PMC 全文核验，五个机制及其条件（符号定义按该文原文）：

| 机制 | 条件 | 符号含义（原文） |
|---|---|---|
| Kin selection | `r > c/b` | `r` = 亲缘系数（共享基因的概率） |
| Direct reciprocity | `w > c/b` | `w` = "the probability of another encounter between the same two individuals" |
| Indirect reciprocity | `q > c/b` | `q` = "the probability to know someone's reputation" |
| Network reciprocity | `b/c > k` | `k` = "the average number of neighbors per individual" |
| Group selection | `b/c > 1 + n/m` | `n` = 最大群体规模，`m` = 群体数 |

- **形式化程度**：完全形式化（每条都有独立的严格推导来源）。
- **对模拟的意义**：这张表是**本项目"合作可行性检查器"的直接实现蓝本**。给定一个待涌现的组织，计算它的 `(b, c, w, q, k, n, m)`，就能判断在当下条件下该组织在数学上是否可能稳定。**这五个量全部是地理/技术/人口的函数**，因此因果链天然可追溯（"为什么这个渠道联盟垮了？因为村落分散使 w 从 0.7 掉到 0.2"）。
- **已知局限**：全部是弱选择极限下的一阶条件；network reciprocity 那一条在人类实验中受到严重挑战（见 §2.8、§7.2）。
- **出处**：Nowak, M.A. (2006) Science, DOI `10.1126/science.1133755`, PMC3279745（**元数据 + 全文均核验**）。

### 2.7 多层次选择与文化群体选择

- **Traulsen & Nowak (2006)** —— 完全形式化，本次自 PMC 全文核验：
  - 模型：种群分为 `m` 个群体，每群最大规模 `n`；每步全种群中一个个体按适应度比例繁殖，后代留在同群；群体达到 `n` 时以概率 `q` 分裂为两个子群（成员随机分配），同时随机消灭另一个群体以保持 `m` 恒定；以概率 `1−q` 改为随机杀死一个群内个体。
  - **在 `q ≪ 1`（稀有分裂）与 `w ≪ 1`（弱选择）下，合作者被青睐的条件是 `b/c > 1 + n/m`。**
  - **加入迁移率 `λ` 后：`b/c > 1 + z + n/m`，其中 `z = λ/q`** = 一个群体存续期内的平均迁入者数。
  - 作者结论："Smaller group sizes and larger numbers of groups favor cooperators."
  - 出处：PNAS 103:10952–10955, DOI `10.1073/pnas.0602530103`, PMC1544155。
- **文化群体选择的经验基础 —— Handley & Mathew (2020)**，本次自 PMC 全文核验，**这是本简报最有价值的经验量化之一**：
  - 样本：**759 人**，肯尼亚 4 个牧业族群（Borana / Rendille / Samburu / Turkana）的 **9 个 clan**。
  - 测量：**49 条**与牧业生计相关的社会规范（合作 10、犯罪与惩罚 9、袭掠 9、家庭 10、文化标记 11）；**16 个 vignette** 情境测合作意向。
  - **文化 F_ST**：族群内 clan 之间 **0.002–0.058**；Turkana 各 territorial section 之间 **0.002–0.058**；**族群（ethnolinguistic group）之间 0.087–0.215**。
  - 作者表述："up to a fifth of the variation in traits can lie between groups"。
  - **与遗传变异对比**：文化 F_ST 比相关遗传 F_ST **高一个数量级**；文中引用的邻近族群遗传 F_ST **最大仅 0.002**。
  - 合作与文化距离的关系：logistic 回归中 "Cultural F_ST has a significant negative effect (Log Odds = −20.12, p < .001)"；文化 F_ST 从 0.05 升到 0.15 使预测的合作概率"接近腰斩"。
  - 出处：Nature Communications 11:702, DOI `10.1038/s41467-020-14416-8`, PMC7000669。
  - **对模拟的意义**：这给了群体选择一个硬的可行性论证 —— **文化变异确实足够大**（族群间 F_ST 达 0.087–0.215），而遗传变异不够（≤0.002）。因此在本项目中，**群体级选择必须作用在"文化/制度"状态上，而不是作用在遗传或个体性格上**。同时 F_ST 的量级给了我们文化传递保真度的标定靶：我们的文化传递机制跑出来的群体间 F_ST 应当落在 0.05–0.25 这个范围，否则参数错了。
- **战争驱动的多层次选择 —— Turchin et al. (2013)**：见 §2.9，本次自 PMC 全文核验。
- **理论共识与反对意见**：Richerson et al. (2016) BBS 39:e30, DOI `10.1017/s0140525x1400106x`（"Cultural group selection plays an essential role..."，核验元数据）；反对方 Mace & Silva (2016) BBS 39, DOI `10.1017/s0140525x15000187`，题为 "The role of cultural group selection in explaining human cooperation is a hard case to prove"（核验元数据）。
- **战争与人类社会行为演化**：Bowles (2009) Science 324:1293–1298, DOI `10.1126/science.1168112`（核验元数据；数值未取得）。
- **理论综述**：Zefferman & Mathew (2015) Evolutionary Anthropology 24:50–61, DOI `10.1002/evan.21439`（核验元数据）。

### 2.8 网络结构与合作：一个被高估的机制

- **理论侧**：
  - Nowak & May (1992) Nature 359:826–829, DOI `10.1038/359826a0` —— 空间格子上合作者可通过成簇存活（"spatial chaos"）。核验元数据。
  - Ohtsuki, Hauert, Lieberman & Nowak (2006) Nature, DOI `10.1038/nature04605` —— "A simple rule for the evolution of cooperation on graphs and social networks"：**`b/c > k`**（`k` = 平均度）。核验元数据（Crossref 未返回卷/页）。
  - **反例（同一学派内部）**：Hauert & Doebeli (2004) Nature 428:643–646, DOI `10.1038/nature02360` —— "Spatial structure **often inhibits** the evolution of cooperation in the snowdrift game"。核验元数据。**这一条极重要：空间结构对合作的作用方向依赖于博弈类型（PD vs snowdrift/chicken）。**
- **人类实验侧（对理论的强反驳）**：
  - Grujić et al. (2010) PLoS ONE 5:e13749, DOI `10.1371/journal.pone.0013749` —— 中尺度空间 PD 人类实验。核验元数据。
  - **Gracia-Lázaro et al. (2012)** PNAS 109:12922–12926, DOI `10.1073/pnas.1206681109`, PMC3420198（**元数据 + 全文核验**）：
    - **1229 名**西班牙 Aragón 地区 42 所中学的 17–18 岁学生。
    - 两种网络：**25×25 方格（625 人，k=4）** 与 **无标度异质网络（604 人，k ∈ [2,16]）**。
    - **51–59 轮** weak PD，收益：互相合作 7 ECU、背叛者面对合作者 10 ECU、任何面对背叛者的玩家 0 ECU。
    - 结果：合作率"quickly drops from initial values around 60% to values around 40% and finally settles at a slower pace around **30%**"，**两种网络的最终合作水平相同**。
    - 结论原文："heterogeneous networks do not promote cooperation"；"population structure has little relevance as a cooperation promoter or inhibitor"。机制解释是 **"moody conditional cooperation"** —— 人根据邻居近期行为而非收益差异做决定，使网络结构变得无关。
  - **Rand, Arbesman & Christakis (2011)** PNAS 108:19193–19198, DOI `10.1073/pnas.1108243108`, PMC3228461（**元数据 + 全文核验**）：
    - **785 名**被试，40 个 session（2010 年 3 月，Amazon Mechanical Turk），平均网络规模 19.6（SD 6.4）。
    - 四个条件：随机重连 / 固定网络 / **黏性动态网络（每轮更新 k = 10% 的连边）** / **流动动态网络（k = 30%）**。
    - 收益：合作者对每个邻居付 50 单位，使该邻居得 100 单位；背叛无成本无收益。每轮后有 **80%** 概率继续。
    - **结果**：随机 −0.11（P<0.001）、固定 −0.19（P<0.001）、黏性(10%) −0.22（P=0.013）**都在衰减**；**流动(30%) −0.04（P=0.386），"Cooperation is robust and stable"**。第 7–11 轮流动条件显著高于其他（P=0.006）。
    - **关键解读**：**30% 的重连率足够，10% 不够。** 起作用的不是拓扑，而是**换伙伴（partner choice）/ 退出的能力**。
- **对模拟的意义**：见 §8 反模式 4。**不要实现"网络拓扑加成"；要实现"能否更换互动对象 / 能否退出"。**

### 2.9 Turchin et al. (2013)：战争 + 空间 + 军事技术扩散 —— **最接近本项目形态的已有模型**

本次自 PMC 全文核验，是本简报里**唯一一个"整块地理舞台 + 千年时长 + 政体涌现"的可复用架构**。

- **空间与时间**：欧亚非大陆 **100 × 100 km** 网格；共 **2,647 个农业单元**；时间步长 **1 年**；模拟 1500 BCE – 1500 CE。
- **状态变量**：每个 community（网格单元）持有一个 "cultural genome" —— 两个二值向量：
  - **ultrasocial traits `U`**（长度 `n_ultra`）
  - **military technology traits `M`**（长度 `n_mil`）
  - polity 聚合多个 community，并跟踪聚合的 ultrasociality 水平。
- **ultrasocial traits 的动力学**：
  - **突变**：`0→1` 概率 `μ01`，`1→0` 概率 `μ10`，且 **`μ01 ≪ μ10`** —— 即**制度退化远快于制度产生**。无选择时的平衡比例 = `μ01/(μ01+μ10)`。
  - **ethnocide（文化征服）**：吞并成功时，"the values of the ultrasociality vector in the losing cell are set to the values of the attacking cell" —— **无方向偏好地复制 0 和 1**（这一点很关键：不是"征服者一定更先进"）。
- **战争规则**：
  - 每年所有边界单元各有一次以概率 `P` 发起攻击的机会。
  - `P_success = P_att / (P_att + P_def)`
  - `P_att = S_att × (1 + β × n_ultra × avg_ultrasociality)`
  - `P_def = S_def × (1 + β × n_ultra × avg_ultrasociality) + γ × E_def`
  - 其中 `S` = 政体规模（单元数），`β` 把 ultrasocial traits 转成实力，`γ` 是海拔防御系数，`E_def` = 防守单元海拔（km）。
  - **ethnocide 概率**：`P_ethnocide = ε_min + (ε_max − ε_min) × (M_traits/n_mil) − γ1 × E_def`
- **地形效应**：山地既直接提高防守实力（`+γ·E_def`），又降低 ethnocide 概率（`−γ1·E_def`）。原文："Mountainous terrain (proxied by elevation) is easier to defend and less likely to be effectively controlled."
- **军事技术扩散**：起点设在草原–农业交界（"cells bordering on the steppe are set to 1"），随后以概率 `σ` 向随机邻居局部扩散；**"Once a technology trait spreads to a cell, it is never lost"**（不可逆，且外生于战争动力学）。
- **政体解体**：`P_disint` 随政体规模 `S` 上升、随平均复杂度（ultrasocial trait 平均频率）下降。
- **拟合结果（对 7,941 个经验数据点）**：
  - **全模型 R² = 0.65**；分期：1500–500 BCE **R² = 0.56**；500 BCE–500 CE **R² = 0.65**；500–1500 CE **R² = 0.47**。
  - **消融实验**：去掉海拔效应（`γ = γ1 = 0`）→ **R² = 0.48**；去掉军事技术对 ethnocide 的影响（`ε_min = ε_max`）→ **R² = 0.16**；军事技术随机播种（无草原效应）→ **R² = 0.17**。
  - 空间统计（SAR）：草原距离、农业出现历史、海拔三个变量在控制空间自相关后 **解释 42% 的方差**。
- **已知局限**：（a）ultrasocial traits 是**黑箱** —— 它们不从更基础的机制涌现，是外生的二值位；这正是本项目要改进的地方；（b）军事技术扩散完全外生且不可逆；（c）R²=0.65 是对"帝国分布"的空间拟合，不等于机制正确（见 §7.7）。
- **出处**：Turchin, Currie, Turner & Gavrilets (2013) PNAS 110:16384–16389, DOI `10.1073/pnas.1308825110`, PMC3799307（**元数据 + 全文核验**）。
- **对模拟的意义（架构级）**：这套 `100km × 1yr × (二值文化向量 + contest-function 战争 + 文化覆盖 + 规模依赖解体)` 是**已被验证能在千年尺度跑出合理宏观格局的最小架构**。本项目应当**继承其骨架，替换其黑箱**：把 `ultrasocial traits` 从外生二值位换成由 §3 的 M1–M13 机制内生产生的组织能力。

### 2.10 Powers & Lehmann (2014) + Powers, van Schaik & Lehmann (2016)：从平等到专制，退出成本是主变量

**Powers & Lehmann (2014)**，本次自 PMC 全文核验：

- **模型**：patch-structured metapopulation，离散不重叠世代。每个 patch 内三个社会类别：leader（`l`，从偏好等级制的个体中随机选出）、follower（`f`，偏好等级制但未被选为 leader）、acephalous（`a`，偏好平等组织）。
- **文化遗传的性状**：
  - `h` ∈ {0,1}：偏好无首领(0) / 等级制(1)
  - `z` ∈ [0,1]：leader 的**专制程度** —— "the proportion of the surplus it generated that it keeps for itself"
  - `d_f`：follower 的**离开阈值** —— leader 可截留的最大剩余比例，超过就走
  - `d_a`：acephalous 个体的无条件迁出概率
- **动力学**：Beverton–Holt 人口动力学，两个 niche（hierarchical `H` / acephalous `A`）。剩余产生的成功概率**随群体规模上升而下降**（即 scalar stress）；有 leader 的群体更容易产生剩余，因为 `g_H < g_A`。产生剩余时承载力按凹函数上升：`β_k[1 − exp(−γ_k·n)]`。
- **退出条件**：`z_leader > d_f` 时 follower 迁出。原文："If the cost of dispersal is low, then leaders are constrained in how much of the surplus they can monopolize."；反之 "followers evolve larger tolerance values of `d_f` in order to avoid paying a high dispersal cost."
- **专制稳定化的两个条件（原文）**：(i) "Surplus resources lead to demographic expansion of groups, removing the viability of an acephalous niche in the same area and so locking individuals into hierarchy"；(ii) 高迁出成本限制 follower 的外部选择。
- **参数默认值（全部自全文核验）**：

  | 参数 | 值 | 含义 |
  |---|---|---|
  | `K_b` | 20 | 基线承载力 |
  | `r_b` | 2 | 基线出生率 |
  | `β_k` | 100 | 剩余带来的最大承载力增量 |
  | `β_r` | 5–20 | leader 的最大出生率增量 |
  | `g_H` | 0.01 | 有 leader 时的协调难度 |
  | `g_A` | 0.15 | 无 leader 时的协调难度 |
  | `γ_k` | 0.05 | 剩余→承载力梯度 |
  | `γ_r` | 0.1 | 剩余→leader 出生率梯度 |
  | `C_D` | 0–1（变量） | 迁出成本 |
  | `μ` | 0.01 | 突变概率 |
  | `N_p` | 50 | patch 数 |
  | `α_AH = α_HA` | 0.03 | niche 间竞争 |

- **出处**：Proc. R. Soc. B 281:20141349, DOI `10.1098/rspb.2014.1349`, PMC4132689。

**Powers, van Schaik & Lehmann (2016)**，本次自 PMC 全文核验 —— 提供了"制度"的可实现定义：

- **制度的定义（原文）**："a mechanism whose outcome is a game form"，由两个顺序阶段构成：(i) "Active genesis of institutional rules through communication and bargaining"；(ii) "Economic interactions whose outcomes are material"。
- **两阶段结构**：**political game form**（成员通过沟通与讨价还价制定规则）→ **economic game form**（在规则下产生物质收益）。关键工程点：**"the political game form is likely to be played much less frequently than the economic game form."**
- **理论基础**：folk theorem —— 合作可持续，当个体"value future pay-offs and cannot completely hide their actions"，且均衡策略收益 ≥ minimax 收益。
- **制度解决的三个问题（原文）**：在无穷多均衡中协调到高收益均衡；使参与者重视未来互动；传递"sufficient information about the past behaviour"（声誉）。
- **向专制的转变**："despotic leaders that commanded surpluses of resources would then be able to influence institutions for their own good."；农业与储藏 + 定居使 "Permanent agriculture...would have tied individuals to their group, making it hard to escape a despotic leader."
- **平等得以维持的结构条件**：包括 "lethal weapons that reduced the effects of physical differences"。
- **大规模社会转变的必要认知要件（原文）**："(i) To devise alternative rules...create virtual worlds. (ii) To communicate and bargain...language and shared intentionality. (iii) To reach consensus...strong willingness to seek out mutual opportunities, as well as strong inhibitory control."
- **出处**：Phil. Trans. R. Soc. B 371:20150098, DOI `10.1098/rstb.2015.0098`, PMC4760198。
- **对模拟的意义（架构级，非常重要）**：**"制度 = 一个决定博弈形式的机制"** 这个定义可以直接落地为本项目的两层 tick：
  - **快 tick（经济博弈）**：每年/每季，agent 在既有规则下做供给/搭便车/监督/惩罚决策 → 由规则数学解算。
  - **慢 tick（政治博弈）**：仅在触发条件下（危机、leader 更替、外部冲击、规模跨越阈值）开启一次"规则再谈判"，**这是 LLM agent 的正确入口**：LLM 提议规则文本与理由，规则被编译成参数（份额、监督强度、制裁表、边界），随后完全由数学执行。
  - 这一条同时回答了纲领 §Phase 0 的"哪些问题适合交给 LLM Agent"：**LLM 写规则，数学执行规则。**

### 2.11 Gavrilets & Richerson (2017)：集体行动与规范内化 —— **"忠诚度"唯一可接受的形式**

本次自 PMC 全文核验。这是本简报里**最直接可移植成代码的单个模型**。

- **结构**：群体规模恒为 `n`；离散不重叠世代；大量群体；个体可随机迁散。
- **集体行动收益**：`π_CA = b·P − c·x`，`x ∈ {0,1}` 为是否投入努力，`P` 为归一化的群体成功度：
  - **us-vs-nature**（对抗自然，如灌溉/开荒/防洪）：`P = X/(X + X0)`，`X` = 群体总努力，`X0` = 半成功参数。
  - **us-vs-them**（对抗他群，如战争/领地争夺）：`P = X/X̄`（Tullock contest function）。
- **含惩罚的完整收益**：
  `π(x,y) = π_CA − y[(1 − p̃)δ + c_mon] − (1 − x)·κ·q̃`
  其中 `y ∈ {0,1}` 是否执法，`δ` 执法成本，`κ` 被惩罚成本，`c_mon` 监督成本，`p̃`/`q̃` 分别是群内合作者/执法者的频率。
  - **注意 `(1 − p̃)δ` 这一项**：执法成本随合作者比例上升而下降 —— 这正是 Boyd et al. (2003) 指出的**机制成立的必要条件**，在这里被显式写进函数形式。
- **规范内化**：连续（遗传）性状 `η ∈ [0,1]`，个体最大化
  **`u_η(x,y) = (1 − η)·π(x,y) + η·(v1·x + v2·y)`**
  - `η = 0` 为 "undersocialized"（只看物质收益）；`η = 1` 为 "oversocialized"（无论代价都遵从规范）。
  - `v1`、`v2` 分别是"贡献"与"执法"的规范价值，反映社会压力强度。
- **参数（自全文核验，作者未给全部数值）**：
  - 群体规模 `n = 8, 16, 24`（图中典型值）
  - `b = 4`（us-vs-nature）、`b = 1`（us-vs-them）
  - `X0 = n/2`
  - `c`、`ν`（突变/更新率）、`e`（优化误差）、`c_opt`、`c_int` **原文未给数值** → 属于我们必须自选的参数
- **群体间选择**：two-level Fisher–Wright；群体存活概率取决于集体行动的平均成功度 `P̄`；存活群体内个体按生物适应度繁殖：`w = 1 + π̄ − c_opt(1−η) − c_int·η`；**"Half of the offspring disperse randomly to different groups."**
- **主要量化结果（自全文核验）**：
  - **"促进对搭便车者的同伴惩罚，比促进生产本身更有效地导致规范内化"**（原文：more efficient in causing norm internalization than promoting production）。
  - 规范内化在"a wide range of conditions"下演化出来。
  - us-vs-nature 博弈难度上升 → 更多规范内化。
  - **种群常常在 `η` 上变成双峰（dimorphic）：约 2/3 的人 `η` 很高，其余很低。**
  - **us-vs-them 博弈中，群体规模 `n` 增大对内化、生产、惩罚都有强负效应。** us-vs-nature 中，若被惩罚成本中等或较大，较小群体演化出更高 `η`。
  - 无内化（`v_x = v_y = 0`）时：us-vs-nature 中"individuals make no effort"；us-vs-them 中有些人志愿参与但"the average group effort is small and decreases with group size"。
- **出处**：PNAS 114:6068–6073, DOI `10.1073/pnas.1703857114`, PMC5468620。

### 2.12 二阶搭便车的解法：Panchanathan & Boyd (2004)

- **核心机制**：用**基于声誉的排除（reputation-based exclusion）**替代昂贵惩罚 —— 不合作者失去好名声，因而在后续的互惠互助中被排除。由于"拒绝帮助坏名声者"本身**不花额外成本**（甚至省钱），二阶搭便车问题消失。
- **形式化程度**：完全形式化。
- **出处**：Nature 432:499–502, DOI `10.1038/nature02978`（核验元数据）；另有回复 Nature 437:E8–E9, DOI `10.1038/nature04202`（核验元数据，表明该结论受到质疑）。
- **对模拟的意义**：这是**成本最低、最容易在大规模下实现的执法技术**，也是"社会性排斥/逐出宗族/开除行会/绝交"这类历史现象的机制底座。工程上：给每个 agent 一个 `standing ∈ {good, bad}`，以及"帮助 bad-standing 者会使自己变 bad"的规则，就能得到该模型。**这比实现付费惩罚更便宜且更稳。**

### 2.13 声誉、间接互惠与信息半径

- Nowak & Sigmund (1998) Nature 393:573–577, DOI `10.1038/31225` —— image scoring。核验元数据。
- Milinski, Semmann & Krambeck (2002) Nature 415:424–426, DOI `10.1038/415424a` —— "Reputation helps solve the 'tragedy of the commons'"：在公共品博弈与间接互惠博弈交替进行时，声誉维持了公共品供给。核验元数据。
- **对模拟的意义**：**声誉必须有信息半径。** `q`（知道对方声誉的概率）应当是"社交距离 + 信息技术"的函数，而不是全局可见。见 §3.M7。

### 2.14 制度作为承诺装置：North / Weingast / Greif 一线

- **North & Weingast (1989)**，"Constitutions and Commitment: The Evolution of Institutions Governing Public Choice in Seventeenth-Century England"，Journal of Economic History 49:803–832, DOI `10.1017/s0022050700009451`（核验元数据）。
  - **核心机制**：统治者的问题不是"没钱"，而是"无法可信地承诺不违约"。把征税与债务决定权移交给一个统治者无法单方面推翻的机构（议会），使统治者的承诺变得可信，从而降低借贷利率、扩大财政能力。**自我约束反而增强能力。**
- **Greif, Milgrom & Weingast (1994)**，"Coordination, Commitment, and Enforcement: The Case of the Merchant Guild"，Journal of Political Economy 102:745–776, DOI `10.1086/261953`（核验元数据）。
  - **核心机制**：单个商人无法威胁统治者，因此统治者有掠夺激励；商人行会通过**协调集体禁运的能力**使"报复"成为可信威胁，从而让统治者的保护承诺变得可信。行会的功能不是垄断，而是**制造可信的集体制裁能力**。
  - **对模拟的意义**：这是"组织如何约束更强者"的可计算机制：`统治者违约收益 R_now` vs `未来租金流折现 Σ δ^t R_t × Pr(商人继续来)`。若组织能协调禁运，`Pr` 就成为组织的决策变量，统治者的最优策略随之改变。见 §3.M10。
- **Greif (1993)**，"Contract enforceability and economic institutions in early trade: The Maghribi Traders' Coalition"，American Economic Review 83:525–548（OpenAlex 核验元数据；该记录无 DOI）。
  - **核心机制**：**多边声誉机制（multilateral reputation）** —— 代理人欺骗任一委托人，就被整个联盟拉黑。这使得跨地域代理关系在没有国家法律的条件下可行。
  - **争议**：Greif (2008) 有一篇题为 "Contract Enforcement and Institutions Among the Maghribi Traders: Refuting Edwards and Ogilvie" 的文章（SSRN, DOI `10.2139/ssrn.1159681`，核验元数据）—— **这条史料解读存在实质学术争议**，见 §7.8。
- **community responsibility system（社区连带责任制）** —— 用"整个社区为其成员的违约负责"替代个体信用。**⚠️ 本次未核验到 Greif 关于该机制的具体论文。** 我记忆中的出处标为 `[未核验]`，不用它承载结论。不过这一机制在东亚有独立的、可另行考证的对应物（保甲/连坐/里甲），见 §6.5。
- **North, Wallis & Weingast (2009)**，*Violence and Social Orders: A Conceptual Framework for Interpreting Recorded Human History* —— **⚠️ 本次只核验到该书的书评与章节记录**（Choice Reviews Online DOI `10.5860/choice.47-2898`；ORDO DOI `10.1515/ordo-2009-0143`），**未直接核验 CUP 原书记录**。其核心论点（"自然国家 natural state" = 精英通过分配租金来控制暴力；向"开放进入秩序"的转变需要非人格化的组织权与对暴力的统一控制）在本简报中按 **B 级 / 定性理论**处理。

### 2.15 principal-agent 与监督成本

- **理论**：委托人无法直接观测代理人努力，只能观测有噪声的产出；因此必须付出监督成本或设计激励合约，二者都有效率损失。**⚠️ 我记忆中的经典出处（Holmström 1982 "Moral hazard in teams"；Alchian & Demsetz 1972）本次均未核验**，标为 `[未核验]`。
- **东亚的量化锚点（本次核验）** —— Sng & Moriguchi (2014), "Asia's little divergence: state capacity in China and Japan before 1850", Journal of Economic Growth 19:439–470, DOI `10.1007/s10887-014-9108-6`（元数据 + 摘要核验；全文被 Springer 登录墙挡住）：
  - 论点：**行政难度随疆域扩大而上升**；在广土国家中统治者难以密切监督官员，官员可对纳税人进行掠夺；为抑制此种掠夺，统治者必须**维持较低税率与有限政府支出**。
  - 经验发现（摘要原文级）：**清代中国的人均税负低于德川日本，人均地方公共服务也更少**；**德川幕府的收入随人口增长而扩大，而清代在 1750 年后尽管人口扩张，财政收入却下降。**
  - **对模拟的意义**：这给了"政体规模 → 监督衰减 → 必须压低税率 → 国家能力受限"这条因果链一个真实的东亚锚点。它同时是**反 Wittfogel** 的：大国不是更专制更能榨取，而是**更无力**。
- Sng, T.-H. (2014), "Size and dynastic decline: The principal-agent problem in late imperial China, 1700–1850", Explorations in Economic History 54:107–127, DOI `10.1016/j.eeh.2014.05.002`（核验元数据；全文封闭，数值未取得）。
- Xue, M.M. & Koyama, M. (2018), "Autocratic Rule and Social Capital: Evidence from Imperial China", SSRN, DOI `10.2139/ssrn.2856803`（核验元数据；工作论文，数值未取得）。**方向：自上而下的暴力（文字狱）可以摧毁横向社会资本，从而降低民间集体行动能力。**

### 2.16 亲缘选择与亲属组织

- `r > c/b`（Nowak 2006 复述，本次核验）。**⚠️ Hamilton (1964) 原文本次未核验。**
- **关键经验反驳 —— Hill et al. (2011)**，"Co-Residence Patterns in Hunter-Gatherer Societies Show Unique Human Social Structure", Science 331:1286–1289, DOI `10.1126/science.1199071`（核验元数据；数值未取得）。方向：狩猎采集群体的共居成员中**大量是非亲属**，因此人类的群体生活**不能由亲缘选择单独解释**。
- **东亚的宗族路径 —— Greif & Tabellini (2017)**，"The clan and the corporation: Sustaining cooperation in China and Europe", Journal of Comparative Economics 45:1–35, DOI `10.1016/j.jce.2016.12.003`（核验元数据；全文未取得）。方向：中国以**宗族（clan，基于亲属的道德义务 + 内部声誉）**、欧洲以**法人社团（corporation，基于非人格化规则 + 外部执法）**两条不同均衡路径解决合作问题，二者各有规模与范围上的不同天花板。
- **对模拟的意义**：亲属网络提供**近零成本的默认信任**（`r` 高、`q` 高、`w` 高），因此在早期与低信息技术条件下必然是主要合作载体；但它的**规模天花板由亲属网络的自然大小决定**（见 §3.M3 的 ~150 层）。要突破天花板，必须叠加 M7（声誉技术）与 M2（制度化执法）。这条正是本项目"宗族 → 更大组织"演化路径的机制骨架。

### 2.17 群体规模的离散层级：Zhou, Sornette, Hill & Dunbar (2005)

本次自 PMC 全文核验。**这是本简报中最直接可用的"组织层级"硬数字。**

- **核心机制**：人类社会群体规模不是连续分布，而是呈**离散的层级**，相邻层级之间有近似恒定的比例。
- **发现的层级均值**：
  - `S0 = 1`（自我）
  - `S1 = 4.6`（support clique，支持小圈）
  - `S2 = 14.3`（sympathy group，同情群）
  - `S3 = 42.6`（band，队群）
  - `S4 = 132.5`（community group，社区群）
  - `S5 = 566.6`（megaband，大队群）
  - `S6 = 1728`（large tribe，大部落）
- **相邻层级比值**：`4.58, 3.12, 2.98, 3.11, 4.28, 3.05`，**均值 `S_i/S_{i−1} = 3.52`**；谱分析给出的**首选缩放比 `λ = exp(2π/ω1) ≈ 3.2`，置信度 0.993**。
- **统计检验**：主峰 `ω1 = 5.40`（`P_N = 8.67`），二次谐波 `ω2 = 9.80`（`P_N = 5.48`）；蒙特卡洛：10⁴ 组随机数据中只有 238 组通过检验，**信号由偶然产生的概率 = 0.024**。
- **数据来源**：61 个分组聚类，来自 1998 年美国 GSS、跨国同情群研究（埃及、马来西亚、墨西哥、南非、荷兰、马里）、以及 42 名英国被试的圣诞卡分发数据。
- **已知局限（对本项目关键）**：**数据全部来自现代社会（含若干非西方社会），外推到史前与古代组织属于外推**。因此我把"层级存在 + 比值 ≈ 3"这个结构判断定为 **A 级**，把"古代军队/官僚也遵循 ×3"定为 **C 级**，把具体的层级损耗率定为 **D 级**（§9）。
- **出处**：Proc. R. Soc. B 272:439–444, DOI `10.1098/rspb.2004.2970`, PMC1634986。

### 2.18 前现代国家的集体行动理论：Blanton & Fargher (2008)

- **核心机制**：前现代国家在"集体（collective）"与"专制（autocratic/exclusionary）"两极之间分布，**分布位置主要由统治者的收入来源结构决定** —— 依赖内部纳税人（internal revenue）的政权必须提供公共品、接受某种程度的问责与"发声"机制；依赖外部租金（战利品、贸易垄断、外部朝贡、资源飞地）的政权则不必。
- **形式化程度**：**定性理论 + 对一组前现代国家的系统编码**（Blanton & Fargher 编码了一批前现代政体的收入来源、公共品供给、官僚问责等变量）。
- **⚠️ 本次未取得其编码数值与样本量**（该书与其 2011 World Archaeology 论文均为封闭获取）。因此本简报只使用其**机制**（B 级），不使用其数字。
- **出处**：Blanton, R. & Fargher, L. (2008) *Collective Action in the Formation of Pre-Modern States*, Fundamental Issues in Archaeology, DOI `10.1007/978-0-387-73877-2`（核验元数据）；Blanton & Fargher (2011) "The collective logic of pre-modern cities", World Archaeology 43:505–522, DOI `10.1080/00438243.2011.607722`（核验元数据）；Blanton & Fargher (2016) "Cooperation in State-Building?" in *How Humans Cooperate*, DOI `10.5876/9781607325147.c008`（核验元数据）。
- **对模拟的意义（极高价值）**：这给了"制度类型"一个**内生的、可计算的决定因素**，而不是让 LLM 选一个政体类型。工程上：
  - 计算 `internal_share = 内部税收 / (内部税收 + 外部租金)`
  - 若 `internal_share` 高，则 ruler 的最优策略包含提供公共品与容忍监督（否则纳税人退出/隐藏/迁移/反抗）
  - 若 `internal_share` 低（例如控制了一条高价值贸易路线或一片银矿），则 ruler 可以专制且仍然稳定
  - **这条机制自动产生"资源诅咒"式的路径依赖**，而且完全不需要脚本。
- **相关的更早理论**：Carneiro (1970) "A Theory of the Origin of the State", Science 169:733–738, DOI `10.1126/science.169.3947.733`（核验元数据）—— **environmental circumscription**：被地理封闭（可耕地被沙漠/山/海围住）的地区，人口压力无法通过迁出释放，从而导致战争与征服性国家形成。**这本质上是"退出成本 `C_D` 由地理决定"的最早表述**，与 Powers & Lehmann (2014) 在数学上同源。

### 2.19 水利与灌溉：Wittfogel 假说及其处理方式

- **Wittfogel 的"东方专制主义/水利社会"假说**：大规模灌溉工程需要中央集权的管理，因此在干旱农业区必然产生专制官僚国家。**⚠️ Wittfogel (1957) 原书本次未核验**，标 `[未核验]`。
- **人类学的经典反驳（本次核验元数据）**：Hunt, R.C. & Hunt, E.K. et al. (1976) "Canal Irrigation and Local Social Organization [and Comments and Reply]", Current Anthropology 17:389–411, DOI `10.1086/201755`。这是一篇带大量评论与回复的靶子论文（评论者包括 Robert Wade、Thomas Glick、William Mitchell 等），**主题即渠道灌溉与地方社会组织的关系**，是"灌溉规模与政治集中度之间关系"这一争论的核心文献之一。（本次仅核验元数据，未取得具体论证内容 → 我只用它来标记"该假说存在实质人类学争议"，不用它承载具体结论。）
- **正面的自组织案例（本次核验元数据）**：Lansing, J.S. & Kremer, J.N. (1993) "Emergent Properties of Balinese Water Temple Networks: Coadaptation on a Rugged Fitness Landscape", American Anthropologist 95:97–114, DOI `10.1525/aa.1993.95.1.02a00050`；以及 Lansing, Cox, Downey, Janssen & Schoenfelder (2009) "A robust budding model of Balinese water temple networks", World Archaeology 41:112–133, DOI `10.1080/00438240802668198`。
  - **对本项目的意义（架构级）**：标题本身即本项目要的东西 —— **一个大规模灌溉协调体系可以作为"涌现性质"从局部规则中自组织出来，位于一个 rugged fitness landscape 上，且其网络结构可由 budding（分芽）过程生成**。这是"水利不必然导致专制"的正面存在性证明，也是"分芽式组织增长"的可实现算法（新灌区从母灌区分出，继承其规则）。
- **现代统计相关（本次核验元数据）**：Bentzen, Kaarsen & Wingender (2016) "Irrigation and Autocracy", Journal of the European Economic Association, DOI `10.1111/jeea.12173`（封闭获取，**数值未取得**）。方向：灌溉潜力与专制程度之间存在跨国相关。**注意：这是一个现代跨国相关性证据，不等于 Wittfogel 的因果机制成立。**
- **东亚灌溉制度的 CPR 编码（本次核验元数据）**：Sarker, A. & Itoh, T. (2001) "Design principles in long-enduring institutions of Japanese irrigation common-pool resources", Agricultural Water Management 48:89–102, DOI `10.1016/s0378-3774(00)00125-6`（封闭获取，数值未取得）。
- **现代中国灌溉的实证（本次核验元数据）**：Wang, Y. & Wu, J. (2018) "An Empirical Examination on the Role of Water User Associations for Irrigation Management in Rural China", Water Resources Research 54:9791–9811, DOI `10.1029/2017wr021837`（数值未取得）。
- **本项目的处理决定**：**不实现"灌溉 → 专制"的科技树。** 把灌溉实现为一个 CPR 分配博弈（上下游天然不对称 + Ostrom DP 存续判定器 + 分芽式增长），让专制与自治都成为**可能的**输出。见 §3.M16、§8 反模式 5。

### 2.20 合作倾向的跨社会/跨群体异质性：两条经验证据

- **Henrich et al. (2005)**，"'Economic man' in cross-cultural perspective: Behavioral experiments in 15 small-scale societies", Behavioral and Brain Sciences 28:795–815, DOI `10.1017/s0140525x05000142`（核验元数据 + 摘要级内容；**具体各社会数值本次未取得**，Cambridge 页面只返回摘要）。
  - 摘要级结论（原文）："found substantially more behavioral variability across social groups than has been found in previous research"；**"group-level differences in economic organization and the structure of social interactions explain a substantial portion of the behavioral variation across societies"**；而 "the available individual-level economic and demographic variables do not consistently explain game behavior, either within or across groups."
  - **对模拟的意义（决定性）**：**合作倾向应当是"群体/文化"层面的状态变量，而不是个体层面的随机数。** 这条经验结论直接支持了"把合作倾向分布挂在文化实体上、由文化演化改变"的设计，并直接反对"每个 agent 随机抽一个合作性格"的设计。
- **Rustagi, Engel & Kosfeld (2010)**，"Conditional Cooperation and Costly Monitoring Explain Success in Forest Commons Management", Science 330:961–965, DOI `10.1126/science.1193649`（核验元数据 + 摘要；封闭获取，具体数值未取得）。
  - 摘要级结论：**埃塞俄比亚 49 个森林使用者组**；(1) 各组的"条件合作者比例"差异显著；(2) 条件合作者比例更高的组，森林管理更成功；(3) **代价高昂的监督（costly monitoring）是条件合作者实施合作的关键渠道**。
  - **对模拟的意义**：给了"群体状态变量 = 条件合作者比例"一个田野层面的效度支持，并把"监督时间投入"确立为一个**可观测、可计量的组织行为**（在模拟里就是 agent 花在 monitoring 上的时间预算）。
- 相关：Agrawal, A. (2001) "Common Property Institutions and Sustainable Governance of Resources", World Development, DOI `10.1016/s0305-750x(01)00063-8`（核验元数据）；Agrawal & Chhatre (2005/2006) "Explaining success on the commons: Community forest governance in the Indian Himalaya", World Development 34:149–166, DOI `10.1016/j.worlddev.2005.07.013`（核验元数据）；McKean, M.A. (1992) "Success on the Commons", Journal of Theoretical Politics 4:247–281, DOI `10.1177/0951692892004003002`（核验元数据 —— 该文是日本 *iriai* 山林共有制的比较研究，是东亚 CPR 的重要文献）。

### 2.21 惩罚的元分析与效应量

- Balliet, D., Mulder, L.B. & Van Lange, P.A.M. (2011) "Reward, punishment, and cooperation: A meta-analysis.", Psychological Bulletin, DOI `10.1037/a0023489`（核验元数据；OpenAlex 标为 green OA，落地页 `https://research.rug.nl/en/publications/442ebd06-0c57-4966-9429-829112970170`，**但本次未取得 PDF，效应量数值未获得**）。
- **⚠️ 结论**：**文献未提供本次可核验的效应量数值。** 本简报不给"惩罚提升合作 x 个百分点"这类数字。工程上应把惩罚强度设为可扫描参数，用 §2.5 的 Boyd et al. 参数作为量级起点。

---

## 3. 可直接用于本项目的机制清单

**说明**：每条给出「输入 → 输出」、可计算的函数形式、时间尺度、空间粒度、证据等级、简化理由、**以及该机制的失效条件**（后者是纲领要求的"什么条件下会失效"）。
标记 `[规则]` = 应由数学决定；`[LLM]` = 适合 LLM agent；`[混合]` = LLM 提议、规则裁决。

---

### M1 — 公共品供给内核（Public-Goods Provision Kernel） `[规则]` 证据 A

**这是整个组织子系统的原子。所有组织（灌溉会、城墙工程、军队、祭祀、行会、国家）都是这个内核的实例，只是参数不同。**

- **输入**：参与者集合 `S`；每人努力 `x_i ∈ [0,1]`；每人能力 `e_i`（由技术、体力、工具决定）；项目类型 `type ∈ {vs_nature, vs_them}`；半成功参数 `X0`（由工程规模/地理难度决定）。
- **输出**：群体成功度 `P ∈ [0,1]`；每人物质收益 `π_i`。
- **数学（直接采用 Gavrilets & Richerson 2017 的形式）**：
  ```
  X = Σ_{i∈S} e_i · x_i

  vs_nature:  P = X / (X + X0)          # 凹的、有饱和的；X0 = 工程难度
  vs_them:    P = X_A / (X_A + X_B)     # Tullock contest；对手的努力进入分母

  π_i = b · share_i · P − c_i · x_i
  ```
- **`share_i`**：分配规则，由制度决定（平均分、按投入比例、按身份等级、leader 截留 `z` 后再分）。**这是制度篡改的入口**，见 M5、M10。
- **时间尺度**：项目周期，1 年（灌溉维护、征兵）到 10–30 年（大堤、城墙、运河）。快 tick。
- **空间粒度**：聚落 / 灌区 / 政体，与 Turchin et al. (2013) 的 100 km 单元兼容（可在单元内再分聚落）。
- **为什么这样简化**：`X/(X+X0)` 是**唯一被两个独立文献线共同使用的凹供给函数**（Gavrilets & Richerson 2017 的 us-vs-nature；Powers & Lehmann 2014 的承载力凹函数 `β_k[1−exp(−γ_k n)]` 形状同类）。它自动给出"规模报酬递减"和"最低门槛"两个真实性质，且只需一个参数 `X0`。Tullock contest 函数是战争/争夺的标准形式（Turchin et al. 2013 的 `P_att/(P_att+P_def)` 就是它）。
- **失效条件**：
  - 当项目有**强互补性/阈值性**（例如堤坝要么合拢要么全溃）时，`X/(X+X0)` 太平滑，应改为 sigmoid 或硬阈值 `P = 1{X > X_threshold}`。**这会把博弈从 PD 变成 stag hunt / snowdrift，合作动力学完全不同**（Hauert & Doebeli 2004 表明空间结构在 snowdrift 中反而抑制合作）。**必须按项目类型选择正确的博弈形式，不能一律用 PD。**
  - 当参与者能力极度异质（`e_i` 方差大）时，Olson 的 "privileged group" 效应出现：单个大户可以独力供给，博弈退化，此时不需要任何治理机制。这**应该被允许发生**（它对应"豪强修渠"这类历史现象）。

---

### M2 — 监督、惩罚与二阶搭便车 `[规则]` 证据 A

- **输入**：`x_i`（是否贡献）、`y_i`（是否执法）、群内合作者频率 `p̃`、执法者频率 `q̃`、监督概率 `q_obs`、执法成本 `δ`、被惩罚成本 `κ`、监督成本 `c_mon`。
- **输出**：修正后的个体收益；违规是否被发现与惩罚。
- **数学（直接采用 Gavrilets & Richerson 2017）**：
  ```
  π_i = b·share_i·P
        − c_i·x_i
        − y_i·[ (1 − p̃)·δ + c_mon ]        # 执法成本：随合作率上升而下降 ★
        − (1 − x_i)·κ·q̃·q_obs               # 被惩罚：需被观测到 ★
  ```
- **两个 ★ 是不可省略的**：
  1. **`(1 − p̃)·δ`** —— 执法成本随合作率上升而下降。Boyd et al. (2003) 的结论是硬的："punishment leads to increased cooperation **only to the extent that** the costs associated with being a punisher decline as defectors become rare."；固定成本时（其 Fig.4）**机制完全失效**。**如果我们把执法实现为一个固定的"维持治安开销"，惩罚机制在数学上就不会工作。**
  2. **`q_obs`** —— 被观测到的概率。这是把"规模/距离/信息技术"接入执法的唯一接口，见 M4。
- **分级制裁（Ostrom DP5）的实现**：`κ = κ_0 · f(累犯次数)`，例如 `κ_0 · (1 + violations_i)`。第一次罚酒，第三次逐出。这既是 DP5 的直接实现，也自动产生"惯犯"这类可追溯个体史。
- **二阶搭便车的三种可实现解法（成本从低到高）**：
  | 解法 | 实现 | 成本 | 出处 |
  |---|---|---|---|
  | **声誉性排除** | agent 有 `standing ∈ {good,bad}`；帮助 bad-standing 者使自己变 bad；不合作者变 bad | **最低**（拒绝帮助不花钱） | Panchanathan & Boyd 2004 |
  | **规范内化** | `η` 权重使执法本身有效用（`v2·y`） | 中（要演化出 `η`） | Gavrilets & Richerson 2017 |
  | **专职执法者** | 把执法变成一个由 M1 供给的**二阶公共品项目**（供养衙役/长老会/教团） | 最高，但可扩展到大规模 | Yamagishi 1986（"制裁系统本身是公共品"） |
- **时间尺度**：与 M1 同步（快 tick，年/季）。
- **空间粒度**：面对面群体（`n ≲ 150`）内为直接监督；跨该规模必须用 M4 的层级监督。
- **失效条件**：
  - 若允许**反惩罚（counter-punishment）**，惩罚的净收益可能被摧毁（Nikiforakis 2008）。**本项目应当实现反惩罚**（它对应血仇、宗族械斗、抗税暴动），并接受它会让某些社会陷入低合作陷阱。
  - 若允许**反社会惩罚（antisocial punishment）**，高贡献者会被打击（Herrmann et al. 2008）。**本项目应当实现它**（它对应"打击出头鸟"、均贫嫉富），并让其强度成为一个文化状态变量。
  - 田野中的惩罚是**协调的、集体决定的**（Bowles et al. 2012），不是个体私下扣分。**因此本项目应把惩罚决策放在"组织"这一层，由组织的集体选择规则（DP3）产生，然后由数学执行。**

---

### M3 — 群体规模层级与协调难度 `[规则]` 证据：结构 A / 古代外推 C

- **输入**：组织总人数 `N_org`。
- **输出**：所需层级数 `L`；每层的 span of control；协调损耗。
- **数学**：
  ```
  λ ≈ 3.2                            # Zhou et al. 2005 首选缩放比（置信 0.993）
  L = ceil( log(N_org) / log(λ) )    # 需要的管理层级数
  span = λ                           # 每个上级直接管辖约 3 个下级单元
  ```
  层级规模的经验锚点（Zhou et al. 2005）：`1 → 4.6 → 14.3 → 42.6 → 132.5 → 566.6 → 1728`。
- **协调难度**：直接采用 Powers & Lehmann (2014) 的形式 —— **剩余产生的成功概率随群体规模上升而下降**（scalar stress），有 leader 时难度参数 `g_H = 0.01`，无 leader 时 `g_A = 0.15`（**即 leader 把协调难度降低约 15 倍**，这是该模型使 hierarchy 能够入侵的核心数字）。
- **时间尺度**：组织结构变化的尺度，10–50 年（慢 tick）。
- **空间粒度**：组织，跨聚落。
- **为什么这样简化**：`λ≈3.2` 是本领域**唯一有显著性检验的组织规模常数**（蒙特卡洛 p=0.024）。用它把"组织规模"和"层级数"绑定，就自动得到"规模扩张必然增加层级，层级必然增加 principal-agent 损耗"这条因果链，而不需要任何脚本。
- **失效条件**：
  - Zhou et al. 的数据**全部来自现代社会**。把 ×3 外推到古代军队编制、官僚层级是外推（C 级）。**校准方式**：如果我们的模拟跑出的军队/官僚层级比与真实古代记载（十进制军制、五进制、什伍制）差太远，说明 `λ` 需要调，而不是说机制错。
  - 当信息技术（文字、簿册、驿传、标准计量）出现时，**有效 span of control 应当上升**。这正是"文字如何使大帝国可能"的机制入口，见 M4。

---

### M4 — principal-agent 损耗与监督概率的空间衰减 `[规则]` 机制 B / 参数 D

**这是把"地理"接入"国家能力"的关键机制，也是本简报中参数最弱的一条 —— 必须诚实标记。**

- **输入**：代理人与委托人的空间距离 `d`；层级数 `L`；信息技术水平 `T_info`（文字、簿册、标准计量、驿传、审计）；代理人数 `n_agents`。
- **输出**：监督概率 `q_obs ∈ [0,1]`；每层的租金漏损率 `leak`；有效税率上限 `τ_max`。
- **数学（建议形式）**：
  ```
  q_obs(d, L, T_info) = q_0 · exp( −d / λ_info(T_info) ) · ρ^L
  leak_per_layer      = leak_0 · (1 − q_obs)
  τ_max               = τ_ceiling · q_obs      # 监督越差，能可持续榨取的越少
  ```
  - `λ_info` = 信息衰减长度（km），**随信息技术上升**。
  - `ρ ∈ (0,1)` = 每增加一层的监督衰减因子。
- **⚠️ 参数状态**：**文献未提供可用的 `λ_info`、`ρ`、`leak_0` 数值。** 本次核验到的最接近的经验锚点是 Sng & Moriguchi (2014) 的**定性方向**（大国 → 难监督 → 官员掠夺 → 统治者被迫压低税率与公共服务；清代 1750 年后人口增长但财政收入下降），以及 Sng (2014) 的题目（"Size and dynastic decline: the principal-agent problem"）。这两条支持**机制**（B 级），但两文全文均封闭，**数值未取得**。因此 `λ_info`、`ρ`、`leak_0` 是 **D 级自选参数**，见 §9。
- **校准靶（可执行）**：调 `λ_info` 与 `ρ`，使模拟中的政体满足两个定性靶：(1) 疆域越大，人均税负与人均地方公共服务**越低**（不是越高）；(2) 人口扩张阶段之后出现财政收入下降。这两个靶都来自 Sng & Moriguchi (2014) 的摘要级结论，是**可核验的定性约束**。
- **时间尺度**：慢 tick（10–50 年），但危机时可快。
- **空间粒度**：政体 × 距首都距离。
- **为什么这样简化**：指数衰减是最少假设的单参数形式；`ρ^L` 把 M3 的层级数直接接进来。二者相乘就产生了"大国天然更弱"这一反 Wittfogel 的正确方向。
- **失效条件**：
  - 当政体采用**间接统治**（承认地方精英自治、包税制、封建分封）时，中央的 `q_obs` 低但**总榨取量可能更高**，因为地方精英自己有近距离监督能力。因此模型必须允许"把监督外包给一个 `q_obs` 高的子组织，代价是分享租金"，这正是封建制/包税制/土司制的机制。**如果不实现这一分支，模拟会错误地断定大帝国不可能存在。**
  - 当信息技术跃升（文字 + 标准计量 + 常规审计）时，衰减长度可能非线性跃升，产生"官僚制革命"。这应当是**涌现的**，触发条件是技术子系统的输出。

---

### M5 — 退出成本 `C_D` 与专制程度 `z` 的内生决定 `[规则]` 证据 A（模型）/ B（映射现实）

**这是"从平等到专制"这一转变在本项目中的唯一合法来源。**

- **输入**：地形（周边可耕无主地面积、迁移障碍）；资产专用性（已投入的渠道/梯田/房屋/储藏）；人口密度；外部群体的接纳意愿。
- **输出**：迁出成本 `C_D`；follower 的容忍阈值 `d_f`；leader 的均衡截留比例 `z*`。
- **数学（直接采用 Powers & Lehmann 2014 的逻辑）**：
  ```
  C_D = C_terrain(地形) + C_asset(已投入的不可移动资产) + C_social(失去亲属/声誉网络)

  follower 退出规则:   if z_leader > d_f  →  迁出（付 C_D）
  d_f 的演化方向:      C_D ↑  →  d_f ↑（容忍度提高，因为走不掉）
  z* 的均衡:           z* 是 "leader 想多拿" 与 "怕 follower 走光" 的平衡点
                       ⇒ z* 单调递增于 C_D
  ```
- **可用参数（Powers & Lehmann 2014 全文核验的默认值）**：`K_b=20, r_b=2, β_k=100, β_r=5–20, g_H=0.01, g_A=0.15, γ_k=0.05, γ_r=0.1, μ=0.01, N_p=50, α_AH=α_HA=0.03`，`C_D` 在 0–1 上扫描。
- **两个专制稳定化条件（原文）**：(i) 剩余带来人口扩张，使同一地区的 acephalous niche 不再可行，从而把个体锁进等级制；(ii) 高迁出成本限制 follower 的外部选择。
- **时间尺度**：`C_D` 随技术/人口变化（50–200 年）；`z` 随 leader 更替（10–30 年）。
- **空间粒度**：聚落 / 政体，且**必须依赖邻域的地理**（周边有无空地是局部量）。
- **为什么这样简化**：`C_D → z*` 是本领域**唯一一条把地理直接连到政治形态、且两端都可计算**的机制链。它同时统一了 Carneiro (1970) 的 environmental circumscription（地理封闭 → 无法退出 → 战争与国家）与 Powers, van Schaik & Lehmann (2016) 的"农业与储藏把人绑在群体里 → 难以逃离专制领袖"。
- **失效条件**：
  - 当出现**大规模的、协调的集体反抗**能力（M2 的执法机制反过来指向 leader）时，`z*` 的上限不再由退出成本决定，而由**推翻成本**决定。这需要额外机制：`z_max = min(d_f + C_D, 推翻门槛)`。**如果只实现退出而不实现反抗，模拟会产出"专制无上限"的错误结论。**
  - 当 leader 提供的协调收益极大（`g_A/g_H` 比值极大，如战时）时，follower 会容忍很高的 `z`。战时专制应当是这个机制的自然输出，战后应当自然回落 —— **除非** `C_D` 在战争期间被永久改变（例如原有聚落被毁、退路被占）。这正是"战争产生的专制为何持续"的可追溯解释。

---

### M6 — 群体间竞争与制度的群体级复制 `[规则]` 证据 A

- **输入**：群体的合作水平/组织能力；邻居分布；地形；军事技术；迁移率。
- **输出**：群体的存活/吞并/文化覆盖；制度状态的复制与消亡。
- **数学（两层）**：
  1. **可行性条件（Traulsen & Nowak 2006，用于诊断而非执行）**：
     ```
     无迁移:  b/c > 1 + n/m
     有迁移:  b/c > 1 + z + n/m,   z = λ_migration / q_split
     ```
     其中 `n` = 最大群体规模，`m` = 群体数，`q_split` = 群体分裂概率。
     **工程用途**：这是一个**运行时断言**。如果模拟中某类合作在长期存续，但当时的 `(b, c, n, m, λ)` 不满足该不等式，说明我们的实现有 bug 或有隐藏的外生补贴 —— 这正是纲领要求的"如何验证一个重大历史事件在逻辑上成立"。
  2. **执行机制（Turchin et al. 2013）**：
     ```
     P_success   = P_att / (P_att + P_def)
     P_att       = S_att × (1 + β · n_ultra · avg_org_capacity_att)
     P_def       = S_def × (1 + β · n_ultra · avg_org_capacity_def) + γ · E_def
     P_ethnocide = ε_min + (ε_max − ε_min)·(M_traits/n_mil) − γ1 · E_def
     P_disint    ↑ with polity size S,  ↓ with avg organizational capacity
     ```
     吞并成功后以 `P_ethnocide` 把败方的制度向量**无方向偏好地**覆盖为攻方的值（0 和 1 都复制）。
- **制度退化必须比制度产生快**：Turchin et al. (2013) 明确设定 `μ01 ≪ μ10`（制度产生率 ≪ 制度丢失率），无选择时平衡比例 = `μ01/(μ01+μ10)`。**这一条是"为什么制度不会单调累积"的机制来源，必须实现。**
- **群体灭绝率的量级锚点**：Boyd et al. (2003) 用 `ε = 0.015` 的群体冲突概率，蕴含 **≈0.0075/世代的群体灭绝率**，作者称其与"小规模社会文化灭绝率的一个估计"一致（**该原始估计本次未追溯**，故此数字按 B 级使用）。
- **文化变异是否够大（可行性验证）**：Handley & Mathew (2020) —— 族群间文化 `F_ST = 0.087–0.215`，比遗传 `F_ST`（最大 0.002）高一个数量级。**校准靶**：我们的文化传递机制跑出来的群体间 `F_ST` 应当落在约 0.05–0.25；若远低于此，群体选择在我们的模拟里将无效，制度不会积累。
- **时间尺度**：战争 1 年（快 tick）；群体选择的累积效应 100–1000 年。
- **空间粒度**：100 km 单元（Turchin et al. 2013 的验证过的粒度）；政体 = 单元集合。
- **失效条件**：
  - **迁移会杀死群体选择**：Boyd et al. (2003) 明确显示合作随迁移率上升"precipitously"下降。**因此如果我们的模拟里人口高度流动（例如实现了自由劳动市场或大规模商队），大规模合作的群体选择支撑会消失。** 这是一个真实的张力，不是 bug，但必须被显式建模（`z = λ/q` 进入不等式）。
  - Turchin et al. (2013) 的消融实验显示，**去掉军事技术扩散后 R² 从 0.65 崩到 0.16**。这意味着"军事技术的空间扩散"在这类模型里承担了绝大部分解释力。**风险**：如果本项目把军事技术做成内生的（应该做），必须确认它仍能产生足够强的空间梯度，否则宏观格局会退化。

---

### M7 — 声誉、间接互惠与信息半径 `[规则 + LLM 叙事]` 证据 A（条件）/ B（`q` 的函数形式）

- **输入**：社交距离；聚落规模；市场/集会频率；信息技术（口传、书信、契约、文字记录、榜文、族谱）。
- **输出**：`q`（知道某人声誉的概率）；`standing_i ∈ {good, bad}`（或连续 score）。
- **数学**：
  ```
  可行性条件（Nowak 2006）:  q > c/b

  建议实现:
  q_ij = 1 − Π_{paths} (1 − ρ_path)        # 多条信息路径的并
  或简化:  q_ij = 1 − exp( −k_contact_ij · T_info )

  standing 更新（Panchanathan & Boyd 2004 式）:
     不合作且被观测  →  standing = bad
     帮助 bad-standing 者  →  自己 standing = bad
     拒绝帮助 bad-standing 者  →  standing 不变（不花成本！）
  ```
- **为什么这样简化**：`q > c/b` 是唯一一条"信息条件"直接进入合作可行性的不等式，且它与纲领第 4 条（Information Horizon）天然一致 —— **声誉必须是局部的**。Panchanathan & Boyd 的 standing 规则是**唯一不需要付费惩罚就能解决二阶搭便车的实现**，因此是大规模合作最便宜的执法技术。
- **时间尺度**：快 tick（声誉每次互动更新）；`q` 随信息技术在 100 年尺度上变化。
- **空间粒度**：社交网络 + 地理距离的复合。
- **失效条件**：
  - **信息噪声**：如果误判率高（好人被误标为 bad），standing 机制会退化。文献中的 image scoring 对噪声敏感（Nowak & Sigmund 1998 及其后续争论）。**本项目应当实现误判**（它对应诬告、谣言、构陷），并让"申冤/审判/冲突解决机制"（Ostrom DP6）成为一个可涌现的制度。
  - `q` 高但**执法能力为零**时，声誉只产生"知道谁是坏人"而无后果。声誉必须配合"拒绝互动"的能力，即 M9 的伙伴选择。

---

### M8 — 重复互动与时间视野 `[规则]` 证据 A

- **输入**：个体流动性；聚落规模；婚姻圈；预期寿命；政权稳定性。
- **输出**：`w`（再次相遇概率）；折现因子 `δ`。
- **数学**：
  ```
  可行性条件（Nowak 2006）:  w > c/b

  w_ij = f(共居时长, 迁移率, 聚落规模)
  δ    = 1 / (1 + r),   r = 时间偏好 + 死亡风险 + 制度不稳定风险
  ```
- **实验锚点**：Rand et al. (2011) 用**每轮 80% 的继续概率**（即 `w = 0.8`）实现无限期重复博弈 —— 这是一个可直接借用的实现细节。
- **重要的时间视野约束**：Gächter, Renner & Sefton (2008) Science 322:1510 的标题即 "The Long-Run Benefits of Punishment"，主张惩罚的净收益只在长时间视野下才为正。（**具体期数本次未核验**，故只用其方向，B 级。）
- **对模拟的意义**：`δ` 必须**内生于政权稳定性**，这会产生一条重要的正反馈：
  ```
  政权不稳 → δ 下降 → 统治者与精英都更掠夺 → 更不稳 → δ 更低
  ```
  **这条自我强化的崩溃回路完全不需要脚本，且天然可追溯**（"为什么这个王朝末期突然横征暴敏？因为 δ 从 0.95 掉到 0.6"）。
- **失效条件**：当 `w` 因为大规模移民、战乱、瘟疫而突降，所有基于重复互动的合作会同步崩塌。**这应当被允许，并且是"乱世"的机制定义**。

---

### M9 — 伙伴选择与流动性（**不是**网络拓扑） `[规则]` 证据 A

**这条机制的定义是"我们不实现什么"，同等重要。**

- **输入**：agent 更换互动伙伴的自由度 `k_rewire`；退出成本 `C_D`（M5）。
- **输出**：合作是否可维持。
- **经验参数（Rand et al. 2011 全文核验）**：
  - `k_rewire = 30%`/轮 → 合作稳定（斜率 −0.04，P=0.386）
  - `k_rewire = 10%`/轮 → 合作衰减（斜率 −0.22，P=0.013）
  - 固定网络 → 衰减（−0.19，P<0.001）；随机重连 → 衰减（−0.11，P<0.001）
  - **⇒ 阈值在 10%–30% 之间；30% 够，10% 不够。**
- **明确不实现的东西**：`b/c > k`（Ohtsuki et al. 2006）作为**运行时加成**。人类实验证据是负面的：
  - Gracia-Lázaro et al. (2012)：1229 人，方格 `k=4` vs 无标度 `k∈[2,16]`，**最终合作率相同（~30%）**；作者结论 "population structure has little relevance as a cooperation promoter or inhibitor"。
  - Hauert & Doebeli (2004)：在 snowdrift 博弈中空间结构**often inhibits** 合作 —— 方向依赖于博弈类型。
  - Grujić et al. (2010)：中尺度空间 PD 人类实验。
- **数学（建议实现）**：
  ```
  每 tick，agent 以概率 p_switch 评估是否更换互动对象:
      p_switch = base_mobility · (1 − C_D) · f(是否有更好的备选)
  更换的门槛由 M5 的 C_D 决定 → 地理与资产专用性直接决定合作的可维持性
  ```
- **为什么这样简化**：把"网络效应"全部收进 `C_D`（退出成本）这**一个**已经因地理内生的变量，既符合负面实验证据，又避免引入一个没有经验支持的拓扑加成，还顺便让 M5 和 M9 共用同一个状态量。**这是本简报里"少一个机制"的收益最大的一处简化。**
- **失效条件**：`p_switch` 极高时（完全自由流动）会杀死群体选择（M6 的 `z = λ/q` 项）。因此流动性对合作有**非单调**效应：太低（走不掉，专制无约束）与太高（群体无法积累制度）都坏。**这个非单调性应当被模拟出来，而不是被参数消掉。**

---

### M10 — 可信承诺与制度作为承诺装置 `[混合]` 机制 B / 参数 D

- **输入**：统治者的即期违约收益 `R_now`；未来租金流 `{R_t}`；折现因子 `δ`（来自 M8）；对方（商人/精英/纳税人）协调制裁的能力 `Coord ∈ [0,1]`；是否存在无法被单方推翻的机构（议会/行会/教团/宗族联合）。
- **输出**：统治者是否违约；投资/借贷/贸易是否发生；利率。
- **数学**：
  ```
  违约条件:   R_now  >  Σ_{t≥1} δ^t · R_t · Pr(对方继续参与 | 未违约)
  对方的最优反应:  Pr(继续参与) = 1 − Coord · 1{曾违约}
  ⇒ Coord 越高，统治者的违约门槛越高 ⇒ 承诺越可信 ⇒ R_t 越大

  制度作为承诺装置:  引入一个机构，使 R_now 不可单方取得
                     （例如征税需机构同意）⇒ 违约在技术上不可行
  ```
- **`Coord` 的来源**：这不是一个自由参数，而是 M1–M2 在"商人/精英/纳税人"这个群体上的输出 —— **协调制裁本身是一个公共品**（Greif, Milgrom & Weingast 1994 的核心洞见就是行会的功能是制造这种协调能力）。
- **⚠️ 参数状态**：`δ` 与政权风险的耦合形式、`Coord` 的具体函数形式，**文献未提供可用参数** → D 级，见 §9。
- **LLM 的位置**：`[混合]` —— LLM agent 可以在"政治博弈"慢 tick 中**提议**一种承诺装置（"设立由六大商号共管的关榷监"），并给出理由；随后规则系统把它编译成 `(Coord, R_now 是否可单方取得, 机构的存续条件)` 三个数值，之后完全由数学执行。**LLM 不得决定该装置是否有效。**
- **时间尺度**：慢 tick（制度创设，10–50 年）；违约决策可在危机时的任何一年。
- **失效条件**：
  - 当统治者的收入主要来自**外部租金**（战利品、贸易垄断、资源飞地）时，`Σ δ^t R_t` 中来自内部纳税人的部分很小，承诺装置的收益消失 —— 统治者没有动机自我约束。**这正是 Blanton & Fargher (2008) 的机制**，且它自动产生"资源诅咒"式路径依赖。
  - 当机构本身被统治者俘获（成员由统治者任命）时，`Coord → 0`。**必须实现"机构的独立性"作为状态变量**，否则会得到"设立了议会就自动可信"的假涌现。

---

### M11 — 亲属组织与非亲属组织的替代 `[规则]` 证据 A（条件）/ B（替代关系）

- **输入**：亲属网络结构（谱系深度、外婚圈）；`r_ij`（亲缘系数）；信息技术；国家执法能力。
- **输出**：组织采用"宗族型"还是"法人型"的合作技术；组织的规模天花板。
- **数学**：
  ```
  亲属通道:    合作条件 r_ij > c/b            # Nowak 2006 复述的 Hamilton 规则
               天花板 ≈ 有效亲属网络规模 ≈ 132–567（Zhou et al. 2005 的 S4–S5 层）
  非亲属通道:  合作条件 q > c/b 或 w > c/b     # 需要声誉技术或重复互动
               天花板由 q_obs（M4）与执法能力决定

  组织选择通道 = argmax( 净收益 )，且两条通道有路径依赖（先建的会锁定）
  ```
- **经验约束**：Hill et al. (2011) —— 狩猎采集群体共居成员**大量是非亲属**，因此**从一开始就必须有非亲属通道**；不能把早期社会实现为纯亲属组织。
- **东亚锚点**：Greif & Tabellini (2017) —— clan（中国）与 corporation（欧洲）是**两个不同的稳定均衡**，各有其规模与范围天花板。这意味着本项目**不应该**把"宗族"实现为"法人制度的落后前身"，而应实现为**一条平行的、有自己上限与优势的合作技术路线**。
- **时间尺度**：谱系深度增长 50–200 年；通道切换 100–300 年。
- **空间粒度**：村落 / 跨村落宗族 / 地域性同乡组织。
- **失效条件**：当人口高速迁移或大规模战乱打断谱系连续性时，亲属通道崩塌；此时若非亲属通道（声誉/契约/国家执法）尚未建立，会出现合作真空 —— **这应当是一个可涌现的"社会崩溃"形态**。

---

### M12 — Ostrom 设计原则作为组织存续判定器 `[混合]` 证据 A（相关性）/ C（因果与样本）

- **输入**：组织当前具备的 DP 集合（11 条布尔或强度值，见 §2.3）。
- **输出**：组织的年失效风险 `hazard`。
- **数学（建议形式）**：
  ```
  n_DP = Σ w_j · DP_j

  hazard = h_0 · exp( −β · n_DP ) · shock_multiplier

  权重建议（依据 Baggio et al. 2016）:
     w(2A), w(2B) 最高          # 成功/失败案例间差异最显著
     w(1B), w(4B), w(6) 次高     # 被识别为"必要但不充分"
     w(4A) 高                   # 缺失 4 大幅提高失败概率
     其余为基准
  ```
- **经验锚点（Baggio et al. 2016 全文核验）**：成功组 `n_DP = 8.7 ± 2.6`，失败组 `4.3 ± 2.7`（11 条中）。69 案例（25 林业/24 灌溉/20 渔业），**仅 27 例完整编码**。
- **⚠️ 必须实现为组合性（configural）而非加法性**：作者的核心方法论结论是 DP 是**组合性**的。因此上式的 `exp(−β·Σw·DP)` 只是一个**粗近似**；更忠实的实现是：
  ```
  if NOT (1B AND 2B AND 4B AND 6):  hazard = 高    # 必要条件缺失
  else:                              hazard = h_0 · exp(−β · Σ w_j DP_j)
  ```
  这样"必要但不充分"这一 QCA 结论被正确编码。
- **LLM 的位置**：`[混合]` —— DP 的**内容**（具体的边界怎么划、制裁表怎么写、纠纷怎么裁）适合 LLM 在慢 tick 生成；DP 的**有无与强度**必须被规则系统从 LLM 的产出中**结构化提取**（例如"这条规则是否指定了可核查的边界？"），然后由数学计算 hazard。**LLM 不得直接给出"这个组织有多稳定"。**
- **时间尺度**：慢 tick（10–50 年评估一次），危机时立即重算。
- **空间粒度**：组织。
- **失效条件（重要，因为这是本简报中最容易被误用的机制）**：
  - **因果方向未定**：DP 可能是长期存续的**结果**（有时间发展出来）而非原因。因此如果我们用 DP 数量去决定存续，再用存续去积累 DP，会得到一个**循环论证式的自证系统**。**缓解办法**：让 DP 的获得有明确的独立成本（监督要花人力、冲突解决要花时间、集体选择要花协商成本），这样 DP 数量高的组织在资源上是被惩罚的，循环被打破。
  - **样本小且偏向 CPR**：69 案例（27 完整）全部是林业/灌溉/渔业。**把 DP 外推到国家、军队、宗教组织是外推**，应标 C 级。

---

### M13 — 规范内化 `η`：**"忠诚度"唯一可接受的实现** `[规则]` 证据 A（模型）

- **输入**：群体的规范价值 `v1`（贡献）、`v2`（执法）；群体间竞争史；社会化过程。
- **输出**：个体的内化权重 `η ∈ [0,1]`；进而个体的效用函数。
- **数学（直接采用 Gavrilets & Richerson 2017）**：
  ```
  u_i(x, y) = (1 − η_i) · π_i(x, y)  +  η_i · ( v1·x + v2·y )
  ```
  - `η_i = 0`：完全物质理性（undersocialized）
  - `η_i = 1`：无论代价都遵从规范（oversocialized）
  - 生物适应度：`w = 1 + π̄ − c_opt(1−η) − c_int·η`（内化与优化各有成本）
- **为什么这是"忠诚度"的正确形式，而"loyalty: float"是错的**：
  - `η` **不是一个结果**（"这个人有多忠诚"），而是一个**偏好权重**（"这个人在物质收益与规范之间怎么权衡"）。它进入效用函数，然后**博弈依然要解**。有了 `η`，agent 仍然会在监督概率低、被惩罚成本低、退出成本低的情况下搭便车 —— **约束依然生效**。
  - `η` 必须由**群体间竞争史内生演化**出来，不能初始化为设定值。Gavrilets & Richerson 的核心结果之一是：**"促进对搭便车者的同伴惩罚，比促进生产本身更有效地导致规范内化"** —— 也就是说，`η` 的上升是"执法制度长期存在"的**结果**，不是原因。这给了"为什么某些文明的臣民更顺从"一条完全可追溯的因果链。
  - **预期形态**：种群会变成 `η` 上的**双峰分布，约 2/3 的人 `η` 高、其余很低**（该文核验结果）。这直接给了我们一个校准靶，也自然产生"多数顺从者 + 少数机会主义者"的社会结构。
- **参数**：`n = 8, 16, 24`；`b = 4`（vs nature）/`b = 1`（vs them）；`X0 = n/2`。**`c`、`ν`、`e`、`c_opt`、`c_int` 原文未给数值 → D 级自选。**
- **时间尺度**：`η` 的演化 = 世代尺度（25 年/代 × 数十代 = 数百到千年）。**慢。**
- **空间粒度**：群体（文化实体）。
- **失效条件**：
  - **群体规模的强负效应**：在 us-vs-them 博弈中，"increasing group size `n` has a strong negative effect on internalization, production, and punishment"。**因此大规模政体不能靠 `η` 维持合作** —— 它必须靠 M2（制度化执法）+ M4（层级监督）+ M12（DP）。**如果我们让 `η` 在大政体里也很高，就是在偷懒地用"忠诚度"替代制度。**
  - `η` 高的社会在环境突变时**适应更慢**（oversocialized 个体不会重新优化）。这应当被实现为"僵化的文明"这一可涌现形态。

---

### M14 — 惩罚的病态形态：反社会惩罚、反惩罚、执法俘获 `[规则]` 证据 A（存在）/ B（量级）

**这条机制的作用是防止模拟产出"过于顺从、过于稳定"的假社会。**

- **输入**：`κ`（惩罚强度）、执法者的身份与身份保护、是否允许反击、文化的反社会惩罚倾向。
- **输出**：合作的实际水平（可能显著低于"理想执法"的预测）。
- **三个必须实现的病态通道**：
  1. **反社会惩罚**：惩罚被用于打击**高贡献者**（Herrmann et al. 2008 在跨社会实验中发现，且强度随社会而异）。实现：以概率 `p_anti` 让惩罚目标选择器指向高贡献者。`p_anti` 是一个**文化状态变量**。
  2. **反惩罚**：被惩罚者反击执法者（Nikiforakis 2008，题目即 "Can we really govern ourselves?"）。实现：惩罚后被惩罚者有概率发起反击，其成本落在执法者身上。**这直接对应血仇、宗族械斗、抗税暴动。**
  3. **执法俘获**：执法者用其位置榨取（这是 M4 的 principal-agent 在执法维度上的实例，也是 Ostrom DP `4B`「对监督者的监督」存在的理由）。
- **数学**：
  ```
  effective_κ = κ · (1 − p_counter · retaliation_success) · (1 − capture_rate)
  punish_target = high_contributor  with prob p_anti(culture)
                  free_rider        otherwise
  ```
- **失效条件（反向）**：如果不实现这三条，模拟会系统性**高估**执法的效力，从而让大规模合作过早、过容易地出现 —— 也就是纲领最担心的"无缘无故"。
- **相关**：Rand & Nowak (2011) "The evolution of antisocial punishment in optional public goods games", Nature Communications 2:434, DOI `10.1038/ncomms1442`（核验元数据）。

---

### M15 — 群体级的合作倾向分布（**不是**个体随机性格） `[规则]` 证据 A

- **输入**：群体的文化历史（执法制度存在时长、群体间竞争强度、`v1`/`v2`）。
- **输出**：该群体中"条件合作者 / 无条件合作者 / 自利者"的比例分布。
- **经验依据**：
  - Henrich et al. (2005)：**"group-level differences in economic organization and the structure of social interactions explain a substantial portion of the behavioral variation across societies"**，而 **"individual-level economic and demographic variables do not consistently explain game behavior"**。
  - Rustagi, Engel & Kosfeld (2010)：埃塞俄比亚 **49 个森林使用者组**，条件合作者比例跨组差异显著，比例高的组管理更成功，**代价高昂的监督是渠道**。
- **数学**：
  ```
  群体 g 的类型分布:  (f_cond^g, f_uncond^g, f_selfish^g)
  个体的类型从其出生群体的分布中抽取（文化传递）
  分布本身随 g 的制度史缓慢演化（由 M13 的 η 演化驱动）
  ```
- **为什么这样简化**：这一条把"agent 异质性"从**噪声**变成**可追溯的文化状态**。它的直接后果是：两个地理条件相同的地区，如果制度史不同，合作能力会不同 —— **这就是纲领第 3 条（路径依赖）在集体行动维度的实现。**
- **失效条件**：如果群体内部高度混合（大规模移民、城市化），群体级分布失去意义，需退回个体级。**这应当是"城市 vs 村落"合作能力差异的机制来源。**

---

### M16 — 水利/灌溉：作为 CPR 分配博弈 + 分芽式增长 `[规则]` 证据 B/C

- **输入**：水源流量（含年际波动）；渠系拓扑（上下游序）；各田块需水量；维护劳动需求；参与者集合。
- **输出**：分水结果；维护投入；渠系是否失效；治理形态（自治 / 上级仲裁 / 专制管控）。
- **数学**：
  ```
  1) 分水（天然不对称）:
     上游先取水  ⇒  下游剩余 = Q − Σ_upstream withdraw
     ⇒ 这是一个 asymmetric CPR appropriation game（不是对称 PGG）

  2) 维护（对称公共品）:
     渠系有效容量 C = C_max · P(X_maintenance)   # 用 M1 的 X/(X+X0)
     不维护 ⇒ 淤塞 ⇒ 所有人受损（含上游）
     ⇒ 上游的"扣水权力"被"需要下游出工维护"所制衡  ★

  3) 存续判定: 用 M12 的 DP hazard（DP 2B「投入/取用比例性」在此最关键）

  4) 增长: budding —— 新灌区从母灌区分出，继承其规则集（Lansing et al. 2009 的
     "robust budding model" 形态），并可发生规则突变
  ```
- **★ 这个上下游制衡是本机制的关键**：它让"灌溉需要合作"成为一个**有内在张力的博弈**，而不是"需要一个中央权力"。这正是 Wittfogel 假说被质疑的地方（Hunt & Hunt 1976 及其评论；Lansing & Kremer 1993 的巴厘水庙自组织案例）。
- **⚠️ 参数状态**：**文献未提供本次可核验的灌溉参数**（Sarker & Itoh 2001、Wang & Wu 2018、Bentzen et al. 2016 全部封闭获取）。渠系拓扑、需水量、维护劳动需求应从本项目的农业/气候简报取参数。
- **时间尺度**：分水按季（快 tick）；维护按年；渠系扩张 10–50 年。
- **空间粒度**：灌区（可能跨多个聚落，且**必须**跨聚落 —— 这正是它成为"超村落组织"驱动力的原因）。
- **失效条件**：干旱年（`Q` 骤降）时，分配博弈从"分剩余"变成"分不足"，合作规则通常在此时崩溃或被重写。**这应当是水利组织制度变迁的主要触发点**，而且完全由气候子系统驱动 —— 因果链天然可追溯。

---

### M17 — 统治者收入结构决定制度类型 `[规则]` 证据 B

- **输入**：内部税收 `R_int`；外部租金 `R_ext`（战利品、贸易通道租、资源飞地、朝贡）；监督能力 `q_obs`（M4）。
- **输出**：统治者的最优策略在 collective ↔ autocratic 谱上的位置；公共品供给水平；是否容忍"发声"机制。
- **数学**：
  ```
  internal_share = R_int / (R_int + R_ext)

  统治者提供公共品的边际收益 ∝ internal_share × (纳税人产出对公共品的弹性)
  统治者容忍监督/发声的边际收益 ∝ internal_share × (可信承诺带来的 R_int 增量)   # 接 M10

  ⇒ internal_share 高  ⇒  collective 型（提供公共品、容忍问责）
  ⇒ internal_share 低  ⇒  autocratic 型（可专制且稳定）
  ```
- **出处（机制）**：Blanton & Fargher (2008)（核验元数据；**编码数值本次未取得**）；与 North & Weingast (1989)、Greif, Milgrom & Weingast (1994) 的承诺装置逻辑同源。
- **为什么这样简化**：这是**唯一一条能让"政体类型"完全内生**的机制。它把政治形态还原为一个可计算比值，而这个比值由地理（有没有银矿、有没有过境贸易路线）、军事（能不能持续掠夺）、技术（能不能测量与征收内部税）共同决定。**因此"为什么这个国家变成专制"永远有答案。**
- **失效条件**：`internal_share` 的测量本身依赖 `q_obs` —— 一个监督能力极差的国家**无法征收内部税**，因此被迫依赖外部租金，从而被迫专制。**这个耦合会产生一个吸收态（低能力 → 依赖外部租金 → 无动机建监督能力 → 保持低能力）**，是"为什么某些政体长期停留在掠夺型"的机制解释。这个吸收态是真实的，不要用参数消掉它。

---

### M18 — 制度退化与遗忘 `[规则]` 证据 B

- **输入**：制度的维护投入；世代更替；文字记录的有无；危机冲击。
- **输出**：制度状态的丢失。
- **数学（直接采用 Turchin et al. 2013 的设定）**：
  ```
  μ01 ≪ μ10          # 制度产生率 ≪ 制度丢失率
  无选择时的平衡:  制度存在比例 = μ01 / (μ01 + μ10)

  建议:  μ10 = μ10_base · (1 − literacy) · (1 − maintenance_investment)
  ```
- **为什么必须有这条**：没有它，制度会单调累积，最后所有文明都变成高度组织化的 —— 这是 ABM 中最常见的失真之一。Turchin et al. (2013) 显式设定制度退化快于产生，这是他们的模型能产生"帝国兴衰循环"而非单调上升的原因之一。
- **时间尺度**：世代（25 年）到百年。
- **失效条件**：如果 `μ10` 太大，制度永远无法积累到能支撑大政体；太小则单调上升。**这是一个必须校准的关键参数**，校准靶是 Turchin et al. (2018) 的复杂度维度（Seshat：414 个政体、30 个 NGA、9 个 CC，PC1 解释 **77.2 ± 0.4%** 的方差）—— 我们的模拟应当也能产出一个解释力占主导的单一复杂度主成分。

---

### M19 — 政治博弈的慢 tick：LLM 的正确入口 `[LLM 提议 / 规则裁决]` 证据 B

- **依据**：Powers, van Schaik & Lehmann (2016) 对制度的定义 —— **"a mechanism whose outcome is a game form"**，由 political game form（较少发生）与 economic game form（频繁发生）两阶段构成。
- **实现**：
  ```
  快 tick（每年/每季）:  纯规则。agent 在既有 game form 下解 M1–M2 的博弈。
                        LLM 完全不参与。

  慢 tick（触发式）:     开启一次 political game form。
    触发条件（全部由规则系统检测，LLM 不能自己触发）:
      - 危机（M16 的干旱、M6 的战败、M12 的 hazard 超阈值）
      - leader 更替
      - 组织规模跨越 M3 的层级阈值
      - internal_share（M17）发生显著变化
    LLM 的输出:  一份规则提案 + 理由 + 支持者与反对者
    规则系统的工作:
      1) 把提案编译成参数（share_i 规则、κ 表、边界定义、q_obs 目标、Coord）
      2) 检查可行性（该提案在当前 (b,c,w,q,k,n,m) 下是否满足 §2.6 的不等式）
      3) 按参与者的实际收益计算提案是否通过（不是由 LLM 决定通过）
      4) 记录因果链：提案文本 + 触发条件 + 投票收益计算 + 结果
  ```
- **为什么这样切分**：这条切分直接回答了纲领的"哪些问题适合交给 LLM Agent / 哪些绝对不能"。**LLM 写规则的内容与理由（难以公式化、需要文化想象力）；规则系统决定规则是否被采纳、以及采纳后的一切后果。** 而且它自然满足纲领第 4 条（信息边界）：LLM 只能看到该 agent 当时能知道的东西。
- **失效条件**：如果慢 tick 触发得太频繁，LLM 会实际上接管了制度演化，涌现变成生成。**建议硬约束**：每个组织的 political game form 在 100 年内触发次数设上限；且每次提案必须通过步骤 2 的数学可行性检查，不通过的提案可以被提出并失败（这本身就是好的历史材料）。

---

## 4. 硬数字与参数表

**编号规则**：`V` = 本次检索中在全文/摘要里真实看到的数值；`M` = 本次只核验到元数据、数值未取得；`D` = 我们自选（无来源）。

### 4.1 合作可行性条件（无量纲，V）

| 机制 | 条件 | 符号含义 | 适用范围 | 不确定度 | 来源 |
|---|---|---|---|---|---|
| Kin selection | `r > c/b` | `r` 亲缘系数 | 亲属群体 | 弱选择一阶近似 | Nowak 2006（V，PMC 全文） |
| Direct reciprocity | `w > c/b` | `w` 再遇概率 | 双边重复互动 | 同上 | 同上（V） |
| Indirect reciprocity | `q > c/b` | `q` 知道声誉的概率 | 有信息流通的群体 | 同上 | 同上（V） |
| Network reciprocity | `b/c > k` | `k` 平均邻居数 | ⚠️ 人类实验中未被支持 | 大 | 同上（V）；Ohtsuki et al. 2006（M）；反证 Gracia-Lázaro et al. 2012（V） |
| Group selection | `b/c > 1 + n/m` | `n` 最大群体规模, `m` 群体数 | 多群体、低迁移 | 弱选择 + 稀有分裂 | Nowak 2006（V）；Traulsen & Nowak 2006（V，PMC 全文） |
| Group selection + 迁移 | `b/c > 1 + z + n/m` | `z = λ_migration / q_split` | 有迁移 | 同上 | Traulsen & Nowak 2006（V） |

### 4.2 利他惩罚的多群体演化（Boyd et al. 2003，全部 V，PMC 全文）

| 量 | 值 | 单位 | 适用时空范围 | 不确定度 | 来源 |
|---|---|---|---|---|---|
| 合作成本 `c` | 0.20 | 收益单位 | 小规模社会文化演化 | base case，未做敏感性区间报告 | Boyd et al. 2003 |
| 惩罚成本 `k` | 0.20 | 收益单位 | 同上 | 同上 | 同上 |
| 被惩罚成本 `p` | 0.80 | 收益单位（= 4k） | 同上 | `p` 降低 → 合作水平大幅降低（Fig.3） | 同上 |
| 执行误差率 `e` | 0.02 | /次 | 同上 | 作者称"relatively rare" | 同上 |
| 迁移率 `m` | 0.01 | /世代 | 同上 | 合作对此**高度敏感** | 同上 |
| 突变率 `μ` | 0.01 | /世代 | 同上 | — | 同上 |
| 群体冲突概率 `ε` | 0.015 | /世代 | 同上 | 也测试了 0.003 与 0.075 | 同上 |
| 蕴含的群体灭绝率 | ≈0.0075 | /世代 | 小规模社会 | 作者称与"一个文化灭绝率估计"一致（**原估计未追溯**） | 同上 |
| 群体数 `N` | 128 | 个 | 同上 | — | 同上 |
| **无惩罚时的合作规模上限** | **≈50** | 人 | 小规模社会 | 在测试的三个冲突率下都成立 | 同上（Fig.1a） |
| **有惩罚时的合作规模上限** | **≈100** | 人 | 小规模社会 | "on the order of 100 individuals" | 同上（Fig.1b） |
| **机制失效条件** | 惩罚成本固定（不随 defector 变稀少而下降）→ **完全失效** | — | 全部 | 定性但确定 | 同上（Fig.4） |

### 4.3 社会群体规模的离散层级（Zhou et al. 2005，全部 V，PMC 全文）

| 层级 | 均值规模（人） | 相邻比值 |
|---|---|---|
| `S0` 自我 | 1 | — |
| `S1` support clique | 4.6 | 4.58 |
| `S2` sympathy group | 14.3 | 3.12 |
| `S3` band | 42.6 | 2.98 |
| `S4` community group | 132.5 | 3.11 |
| `S5` megaband | 566.6 | 4.28 |
| `S6` large tribe | 1728 | 3.05 |
| **比值均值** | — | **3.52** |
| **谱分析首选缩放比 λ** | — | **≈3.2**（置信度 0.993） |

统计：主峰 `ω1 = 5.40`（`P_N = 8.67`），二次谐波 `ω2 = 9.80`（`P_N = 5.48`）；蒙特卡洛 10⁴ 组中 238 组通过 → **偶然概率 0.024**。数据：61 个分组聚类（1998 美国 GSS、埃及/马来西亚/墨西哥/南非/荷兰/马里的同情群研究、42 名英国被试的圣诞卡数据）。**适用范围警告：全部现代数据。**

### 4.4 从平等到专制的模型参数（Powers & Lehmann 2014，全部 V，PMC 全文）

| 参数 | 值 | 含义 | 备注 |
|---|---|---|---|
| `K_b` | 20 | 基线承载力 | — |
| `r_b` | 2 | 基线出生率 | — |
| `β_k` | 100 | 剩余带来的最大承载力增量 | 承载力增量按 `β_k[1−exp(−γ_k·n)]` |
| `β_r` | 5–20 | leader 的最大出生率增量 | 扫描范围 |
| `g_H` | 0.01 | 有 leader 时的协调难度 | — |
| `g_A` | 0.15 | 无 leader 时的协调难度 | **`g_A/g_H = 15`** —— leader 把协调难度降低 15 倍 |
| `γ_k` | 0.05 | 剩余→承载力梯度 | — |
| `γ_r` | 0.1 | 剩余→leader 出生率梯度 | — |
| `C_D` | 0–1 | 迁出成本 | **主控变量**：`C_D ↑ ⇒ d_f ↑ ⇒ z* ↑` |
| `μ` | 0.01 | 突变概率 | — |
| `N_p` | 50 | patch 数 | — |
| `α_AH = α_HA` | 0.03 | niche 间竞争 | — |

### 4.5 规范内化模型参数（Gavrilets & Richerson 2017，V，PMC 全文）

| 参数 | 值 | 含义 |
|---|---|---|
| 群体规模 `n` | 8, 16, 24 | 图中典型值 |
| `b`（us-vs-nature） | 4 | 集体行动收益 |
| `b`（us-vs-them） | 1 | 集体行动收益 |
| `X0` | `n/2` | 半成功参数 |
| `c`, `ν`, `e`, `c_opt`, `c_int` | **原文未给数值** | 成本与更新率 → **D 级自选** |
| 结果：`η` 分布 | **双峰，约 2/3 高 `η`** | 种群结构预测 |
| 结果：群体规模效应 | us-vs-them 中 `n ↑` → 内化/生产/惩罚**强负效应** | 大群体不能靠内化 |

### 4.6 网络与流动性的人类实验（V，PMC 全文）

| 量 | 值 | 来源 |
|---|---|---|
| 被试数（格子 + 无标度） | 1229（625 + 604） | Gracia-Lázaro et al. 2012 |
| 网络度 | 格子 `k=4`；无标度 `k ∈ [2,16]` | 同上 |
| 轮数 | 51–59 | 同上 |
| 收益（weak PD） | CC=7 ECU；D vs C = 10 ECU；任何面对 D = 0 ECU | 同上 |
| 合作率轨迹 | 初始 ~60% → ~40% → **稳定在 ~30%** | 同上 |
| **两网络的最终合作率** | **相同** | 同上 |
| 被试数（动态网络） | 785（40 sessions），平均网络规模 19.6（SD 6.4） | Rand et al. 2011 |
| 收益 | 合作者对每邻居付 50，使其得 100 | 同上 |
| 每轮继续概率 | **80%** | 同上 |
| 重连率 10%（黏性） | 合作衰减，斜率 **−0.22**（P=0.013） | 同上 |
| **重连率 30%（流动）** | **合作稳定，斜率 −0.04（P=0.386）** | 同上 |
| 固定网络 | 斜率 −0.19（P<0.001） | 同上 |
| 随机重连 | 斜率 −0.11（P<0.001） | 同上 |

### 4.7 文化群体选择的经验量化（Handley & Mathew 2020，V，PMC 全文）

| 量 | 值 | 范围 |
|---|---|---|
| 样本 | 759 人 | 肯尼亚 4 族群 9 clan（Borana/Rendille/Samburu/Turkana） |
| 规范条目 | 49 条（合作 10 / 犯罪惩罚 9 / 袭掠 9 / 家庭 10 / 文化标记 11） | — |
| vignette 情境 | 16 个 | — |
| **文化 F_ST：族群内 clan 间** | **0.002–0.058** | — |
| **文化 F_ST：Turkana 各 section 间** | **0.002–0.058** | — |
| **文化 F_ST：族群间** | **0.087–0.215** | "up to a fifth of the variation in traits can lie between groups" |
| **遗传 F_ST（引用的邻近族群最大值）** | **0.002** | 文化 F_ST 高**一个数量级** |
| 合作与文化距离 | Log Odds = **−20.12**（p<0.001）；F_ST 从 0.05→0.15 使合作概率"接近腰斩" | — |

### 4.8 前国家战争中的惩罚与搭便车（Mathew & Boyd 2011，V，PMC 全文；Turkana）

| 量 | 值 |
|---|---|
| 数据集 | 88 次袭掠，访谈 118 名男性；47 次有伤亡数据的 force raid；34 次 stealth raid；53 次有战利品分配数据的 force raid；32 次成功 force raid 用于分配分析 |
| force raid 规模 | 平均 **315** 名战士，中位 **248** |
| stealth raid 规模 | 平均 **12** 名 |
| 参与者来源多样性 | 平均来自 5 个年龄组、4 个聚落、3 个 territorial section |
| 每名战士的近亲数 | force raid 平均 **4** 名；stealth raid **1** 名 |
| 每次 force raid 的阵亡概率 | **1.1%**；若遭遇对手则 **1.3%** |
| 战争死亡占比 | 青春期至生育期间 **14%** 死于战争；生育期内 **9%** |
| **逃跑（desertion）发生率** | **至少 43%** 的 force raid |
| **战斗中怯战发生率** | 发生战斗的 force raid 中 **45%** |
| **战利品分配违规率** | **56%** 的 force raid |
| **逃跑被制裁的比例** | 报告有逃跑的 force raid 中 **47%** |
| **怯战被制裁的比例** | 报告有怯战的 force raid 中 **67%** |
| 严重制裁（体罚/罚牛） | 20 次被制裁的违规中有 **9** 次 |
| 战利品 | force raid 平均每人 **11** 头牛；stealth raid **3** 头 |

**⇒ 对模拟的直接含义**：这是**本简报中唯一一组真实前国家社会的"搭便车率 + 制裁率"数字**。搭便车非常普遍（43–56%），制裁覆盖率高但不完全（47–67%），严重制裁只占被制裁案例的 45%（9/20）。**这给了我们一个校准靶：一个真实的合作组织应当有 40–60% 的违规率与 50–70% 的制裁覆盖率，而不是接近 0 的违规率。** 如果我们的模拟跑出"人人守规"，就是错的。

### 4.9 Ostrom 设计原则的经验量化（Baggio et al. 2016，V，全文）

| 量 | 值 |
|---|---|
| 案例总数 | 69（25 林业 / 24 灌溉 / 20 渔业） |
| 完整编码案例数 | **27** |
| DP 条目数 | 11（1A,1B,2A,2B,3,4A,4B,5,6,7,8） |
| **成功案例的 DP 数** | **8.7 ± 2.6** |
| **失败案例的 DP 数** | **4.3 ± 2.7** |
| 差异最显著的 DP | **2A、2B**（一致性、比例性） |
| 必要但不充分的 DP | **1B、2B、4B、6** |
| 缺失后大幅提高失败概率 | **2A、2B、4** |
| 方法 | QCA + DP 共现网络可视化 + 缺失数据可靠性度量 |

### 4.10 千年尺度空间模拟的架构参数（Turchin et al. 2013，V，PMC 全文）

| 量 | 值 |
|---|---|
| 网格分辨率 | **100 × 100 km** |
| 农业单元数 | **2,647** |
| 时间步长 | **1 年** |
| 模拟时段 | 1500 BCE – 1500 CE |
| 经验数据点 | **7,941** |
| **全模型 R²** | **0.65** |
| 分期 R² | 1500–500 BCE: **0.56**；500 BCE–500 CE: **0.65**；500–1500 CE: **0.47** |
| 消融：无海拔效应 | R² = **0.48** |
| 消融：军事技术不影响 ethnocide | R² = **0.16** |
| 消融：军事技术随机播种 | R² = **0.17** |
| SAR 空间统计（草原距离 + 农业史 + 海拔） | 解释 **42%** 方差 |
| 制度突变率关系 | **`μ01 ≪ μ10`**（制度产生远慢于丢失） |
| 军事技术扩散 | 起源于草原–农业交界；概率 `σ` 局部扩散；**一旦获得永不丢失** |

### 4.11 社会复杂度的维度（Turchin et al. 2018 / Seshat，V，PMC 全文）

| 量 | 值 |
|---|---|
| 政体数 | **414** |
| Natural Geographic Areas | **30**（10 个世界区域 × 3） |
| 时间切片 | 每 **100 年**，最早可回溯到 **9600 BCE** |
| 复杂度特征（CC）数 | **9**（政体人口、政体疆域、首都人口、层级复杂度、政府、基础设施、信息系统、文本、货币系统） |
| **PC1 解释的方差** | **77.2 ± 0.4%** |
| 特征出现顺序 | 论文**未**给出严格的发展序列；强调各特征"coevolve"，跨区域可预测地共同变化 |

**⇒ 对模拟的校准靶（可执行）**：把我们模拟中的政体在同样 9 个维度上打分，做 PCA。**如果 PC1 解释不到约 70%，说明我们的组织子系统把复杂度维度做得太独立了**（例如文字可以脱离官僚制单独出现）。如果 PC1 解释 >95%，说明我们把它们绑得太死（隐藏的科技树）。

### 4.12 东亚国家能力的定性约束（Sng & Moriguchi 2014，摘要级 V；数值 M）

| 约束 | 方向 | 来源 |
|---|---|---|
| 疆域越大 → 监督越难 → 官员掠夺空间越大 | 正 | Sng & Moriguchi 2014（摘要级） |
| 为抑制掠夺，统治者必须**压低**税率与政府支出 | 负 | 同上 |
| 清代中国的**人均税负低于**德川日本 | — | 同上 |
| 清代中国的**人均地方公共服务少于**德川日本 | — | 同上 |
| 德川幕府收入随人口增长而扩大 | 正 | 同上 |
| **清代 1750 年后人口扩张但财政收入下降** | 负 | 同上 |
| 具体数值（税率、官员密度、距首都距离效应） | **M —— 全文封闭，未取得** | — |

### 4.13 明确的参数缺口（**不要编数字填这些**）

| 缺口 | 状态 |
|---|---|
| Fehr & Gächter 公共品博弈的 MPCR、组数、期数、惩罚兑换率 | **文献未提供本次可核验的参数**（2000 AER 与 2002 Nature 均封闭，无 OA 副本） |
| Balliet et al. 2011 元分析的惩罚/奖励效应量 | **未取得**（Psych Bulletin，green OA 落地页存在但 PDF 未取得） |
| Herrmann et al. 2008 各社会的反社会惩罚强度 | **未取得**（Science 封闭） |
| Gürerk et al. 2006 制度选择实验中迁向制裁制度的比例 | **未取得**（Science 封闭） |
| Gächter, Renner & Sefton 2008 的短/长期期数对比 | **未取得**（Science 封闭；仅标题方向可用） |
| Blanton & Fargher 的 collective-action 编码数值与样本量 | **未取得**（书与 World Archaeology 论文均封闭） |
| Bentzen et al. 2016 灌溉→专制的系数 | **未取得**（JEEA 封闭，OpenAlex 确认无 OA 副本） |
| Sarker & Itoh 2001 日本灌溉 CPR 的编码 | **未取得**（Agricultural Water Management 封闭） |
| Ostrom 2009 Science 的 SES 框架变量清单与"影响自组织的 10 个子系统变量" | **未取得**（Science 封闭；OA 副本被 bot 防护挡住） |
| Cox et al. 2010 对 DP 的重新表述与逐条支持计数 | **未取得**（Ecology and Society 站点 403） |
| Nepal 农户管理 vs 机构管理灌溉的绩效对比数值 | **未取得**，且相关文献（Lam 1998、Tang 1992、Ostrom 1992）本次**完全未核验** |
| `λ_info`（监督随距离衰减长度）、`ρ`（每层衰减）、`leak_0` | **无来源 → D 级**，见 §9 |
| 层级 `λ≈3.2` 在古代军事/官僚编制中的适用性 | **外推 → C 级** |

---

## 5. 数据集与数据库

| 名称 | 内容 | 覆盖范围 | 访问方式 / URL | 许可 | 可用于本项目什么 |
|---|---|---|---|---|---|
| **Seshat Databank** | 全球政体的社会复杂度编码：政体人口、疆域、首都人口、层级层数、政府、基础设施、信息系统、文本、货币系统等 9 个 CC，以及大量其他变量 | **414 个政体 / 30 个 NGA / 每 100 年一切片 / 最早 9600 BCE 至近代** | 数据集名称与规模来自 Turchin et al. 2018（PNAS，PMC5777031，**本次核验**）。⚠️ **其官方站点 URL 本次未核验**，不在此写出以免捏造 | 未核验 | **§4.11 的校准靶**：把模拟政体在同 9 维打分做 PCA，比 PC1 解释率与跨区域共变模式 |
| **Turchin et al. 2013 的经验帝国分布数据** | 欧亚非 100 km 网格上的历史帝国存在与否 | **7,941 个数据点**，1500 BCE–1500 CE | 数值与规模来自 PNAS 论文（PMC3799307，**本次核验**）；论文另有 Exeter 机构库 OA 副本 `http://hdl.handle.net/10871/31320`（OpenAlex 提供，**本次未打开**） | 未核验 | 空间宏观格局的校准靶（R²、消融比较的方法论） |
| **Baggio et al. 2016 的 69 案例 DP 编码集** | 林业/灌溉/渔业 CPR 案例的 11 条设计原则编码 + 成功/失败标签 | 69 案例（27 完整） | 论文本身开放获取：`https://thecommonsjournal.org/articles/10.18352/ijc.634`（**本次核验并读取全文**） | 期刊为开放获取（具体许可本次未核验） | **M12 的 hazard 参数校准**；DP 组合性的实现依据 |
| **Digital Library of the Commons (Indiana University)** | Ostrom 学派的 CPR 案例研究、工作论文、会议论文的开放存档 | 全球 CPR 文献 | `https://dlc.dlib.indiana.edu/`（OpenAlex 的 OA 记录指向该主机；**本次尝试下载一份文件返回 403，站点本身未验证可用性**） | 未核验 | 找 CPR 案例的一手描述（用于给 DP 编码提供更多样本） |
| **PubMed Central (PMC)** | 生物医学 + 演化 + PNAS/Proc R Soc B 等的开放全文 | — | `https://pmc.ncbi.nlm.nih.gov/`；DOI→PMCID 转换 API：`https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?ids=<DOI列表>&format=json`（**本次大量使用，可用**） | 各文献不同 | **本简报中所有"V"级数值的来源渠道**；未来研究阶段应继续用它取全文 |
| **Crossref REST API** | 学术文献元数据（标题、作者、年、期刊、卷、页、DOI） | 全学科 | `https://api.crossref.org/works?query.bibliographic=<查询>&rows=N&select=title,author,issued,container-title,DOI,volume,page`（**本次大量使用；会 429 限流，需串行**） | 开放 | **引文核验的主渠道** |
| **OpenAlex API** | 文献元数据 + 开放获取位置 + 引用数 + 摘要倒排索引 | 全学科 | `https://api.openalex.org/works?...&select=doi,title,best_oa_location,open_access,biblio`（**本次大量使用；配额耗尽后返回 429 且 Retry-After ≈ 11 小时**） | CC0（**本次未核验其许可声明**） | 判断某文是否有 OA 副本、拿摘要；引文核验的第二渠道 |
| **Ethiopia 森林使用者组数据（Rustagi, Engel & Kosfeld 2010）** | 条件合作者比例（实验测量）+ 监督时间（调查）+ 森林管理绩效 | **49 个森林使用者组** | 论文封闭获取（Science，DOI `10.1126/science.1193649`）；**数据可得性本次未核验** | 未核验 | M15（群体级合作倾向分布）的效度支持 |
| **Handley & Mathew 2020 的肯尼亚牧业规范数据** | 49 条规范 × 759 人 × 9 clan；16 个 vignette | 肯尼亚 4 个族群 | 论文开放获取（Nature Comms，PMC7000669，**本次核验全文**）；补充数据本次未核验 | 论文 OA | M6 的文化 F_ST 校准靶（0.05–0.25） |

**⚠️ 本节的诚实声明**：本简报**没有**验证过任何数据集的实际下载链接与许可条款。上表中凡标"未核验"的，下一阶段必须由人工或工具实际打开确认。我特意**没有**写出 Seshat、SESMAD、NIIS 等数据库的 URL，因为本次未真实访问它们，写出来就是捏造。

---

## 6. 中国与东亚特定证据

### 6.1 国家规模与 principal-agent：东亚给了一条反 Wittfogel 的证据链

本次核验到的最强东亚证据是 Sng & Moriguchi (2014) 与 Sng (2014) 这条线（§2.15、§4.12）。它的方向对本项目非常重要：

- **广土 ≠ 强专制榨取能力**。相反：疆域大 → 监督难 → 官员掠夺空间大 → 统治者被迫**压低**税率与政府支出以抑制掠夺。
- 结果是清代中国的**人均税负低于**德川日本、**人均地方公共服务少于**德川日本；且**清代 1750 年后人口扩张而财政收入下降**。
- 这与 Wittfogel 式"大型水利工程 → 强中央集权专制"的直觉**方向相反**：中国式大帝国的特征不是过度榨取，而是**低度榨取 + 薄的地方治理 + 对地方精英与宗族的依赖**。
- **对模拟的含义**：M4 的 `q_obs(d) = q_0·exp(−d/λ_info)·ρ^L` 加上 M17 的 `internal_share`，应当**自动**产出这个格局：一个大而监督弱的政体会走向低税率、少公共品、依赖间接统治。**如果我们的模拟里大帝国总是高税率高控制，参数就错了。**

### 6.2 宗族作为主要合作载体：一条平行的合作技术路线

- Greif & Tabellini (2017) JCE 45:1–35（核验元数据）：中国的 **clan** 与欧洲的 **corporation** 是两个不同的稳定均衡。clan 依赖亲属道德义务 + 内部声誉；corporation 依赖非人格化规则 + 外部（法律）执法。
- Xu & Yao (2015) APSR 109:371–391（核验元数据；数值未取得）："Informal Institutions, Collective Action, and Public Investment in Rural China" —— 方向：**非正式制度（宗族）能够支撑村级公共投资**，即宗族在现代中国农村仍是集体行动的有效载体。
- **对模拟的含义（重要设计决定）**：
  - **不要**把宗族实现为"法人制度的落后前身"或"待解锁的过渡形态"。它应当是 M11 中的一条**平行通道**，有自己的优势（低 `c_mon`、高 `q`、高 `w`）与自己的天花板（规模受亲属网络限制，约 Zhou et al. 的 `S4–S5` 层 = 132–567 人；跨宗族的非人格化合作能力弱）。
  - 两条通道之间应当有**路径依赖与锁定**：先建起 clan 的地区，其成员的 `η` 与规范内容会强化 clan，使 corporation 的边际收益下降。这正是纲领第 3 条（路径依赖）在制度维度的实例。
  - **副产品**：这条设计会自然产出"为什么这个虚构文明的商业组织长成了亲属网络而不是股份公司"这类可追溯回答。

### 6.3 灌溉与水利：东亚的证据既不支持 Wittfogel，也不支持纯自治

- **日本**：Sarker & Itoh (2001) 明确以 Ostrom 设计原则分析**长期存续的日本灌溉 CPR 制度**（核验元数据；编码数值未取得）。McKean (1992) "Success on the Commons"（核验元数据）是日本 *iriai* 山林共有制的比较研究。⇒ **东亚存在长期存续的、非国家主导的 CPR 自治制度**。
- **巴厘（东南亚，虽非中国但同属稻作灌溉文化圈）**：Lansing & Kremer (1993) 与 Lansing et al. (2009)（核验元数据）—— 水庙网络的协调是**涌现性质**，位于 rugged fitness landscape 上，且网络可由 **budding（分芽）**过程生成。⇒ 大规模灌溉协调**不需要**中央国家。
- **现代中国**：Wang & Wu (2018) WRR 54:9791–9811（核验元数据；数值未取得）—— 农民用水协会（WUA）在中国农村灌溉管理中的作用的实证检验。
- **人类学争论的核心文献**：Hunt & Hunt et al. (1976) Current Anthropology 17:389–411（核验元数据）—— 渠道灌溉与地方社会组织的关系，带 Robert Wade、Thomas Glick、William Mitchell 等人的评论与回复。
- **现代跨国相关**：Bentzen, Kaarsen & Wingender (2016) JEEA（核验元数据；系数未取得）—— 灌溉潜力与专制程度的跨国相关。**这是相关性，不是 Wittfogel 的因果机制。**
- **对模拟的含义**：M16 的实现（上下游不对称分水 + 对称维护公共品 + DP hazard + budding 增长）能同时容纳这三类结果：自治的水利社群、被地方精英把持的水利、被国家接管的水利。**哪一个出现，取决于 `C_D`、`q_obs`、`internal_share`，而不是取决于灌溉规模本身。**

### 6.4 空间粒度：中国的市场层级

- Skinner, G.W. 的"Marketing and social structure in rural China" —— 本次通过 OpenAlex 核验到一条 2002 年的法文期刊重印记录（Études rurales 161–162，DOI `10.4000/etudesrurales.7952`，OpenEdition 有 OA PDF），**但下载时连接被拒（ECONNREFUSED），内容未取得**。原始 1964–65 年 Journal of Asian Studies 三部分连载**本次未核验**。
- **因此**：我记忆中的"一个标准市场镇服务约 18 个村庄 / 约 1,500 户"等数字**本次未核验，不写入参数表**。
- **可用的部分（仅结构性判断，C 级）**：中国农村存在"村落 → 标准市场社区 → 中间市场 → 中心市场"的空间层级，且这一层级是**跨村落集体行动（庙会、水利、团练、宗族联合）的天然单位**。这个结构性判断与 §4.3 的 `λ≈3.2` 层级规律在方向上一致，但**具体数值必须在下一阶段单独核实**。
- **对模拟的含义**：本项目的空间层级建议为 `聚落 → 市场社区 → 州县级 → 政体`，其规模比大致按 M3 的 `λ≈3.2` 分层。**这是 D/C 级设计决定，不是史实。**

### 6.5 连带责任：东亚的"community responsibility system"对应物

- 我记忆中 Greif 关于 community responsibility system 的论文**本次未核验**（§2.14），标 `[未核验]`。
- 东亚的对应物（保甲、里甲、连坐、族规、乡约）在本次检索中**只找到一条相关记录**：Pfautsch, A. (2025) "Village Compact: Law and Local Governance in Late Imperial China", Zeitschrift für Chinesisches Recht 32:297–298, DOI `10.71163/zchinr.2025.297-298`（核验元数据；这是一条 2 页的记录，看起来是书评，**内容未取得**）。相关的历史学文献本次未能有效检索（WebSearch 配额已耗尽，Crossref 的中文主题检索命中率低）。
- **诚实结论**：**东亚连带责任制度的量化证据在本次检索中未获得。** 这是本简报最大的一个东亚缺口，应在下一阶段专项补做（建议关键词：`baojia`、`lijia`、`collective responsibility`、`xiangyue`、`village compact`、`mutual surveillance`、`Qing local administration`）。
- **可用的机制骨架（B 级，来自非东亚文献）**：连带责任的可计算形式是 **"把监督成本从委托人转移给被监督者的同侪"**：
  ```
  个体违规 → 整个连带单位（5家/10家/宗族）被惩罚
  ⇒ 同侪有强激励互相监督（因为他们承担后果）
  ⇒ 委托人的 q_obs 需求下降（不需要自己监督），代价是同侪之间的横向压迫上升
  ```
  这条机制在数学上与 Greif, Milgrom & Weingast (1994) 的行会集体制裁是**同一结构的镜像**（那里是集体对外制裁，这里是集体对内被制裁），因此可以复用同一份代码。**这解释了为什么一个监督能力弱的大帝国（§6.1）会倾向于发明连带责任制度：它是 `q_obs` 低时的最优替代品。** —— 这条推论是 **D 级**（我的推断），见 §9。

### 6.6 自上而下的暴力对横向社会资本的破坏

- Xue, M.M. & Koyama, M. (2018) "Autocratic Rule and Social Capital: Evidence from Imperial China", SSRN DOI `10.2139/ssrn.2856803`（核验元数据；工作论文，数值未取得）。
- **方向**：国家实施的针对性暴力（文字狱一类）可以**降低民间横向组织与集体行动的能力**。
- **对模拟的含义**：这是一条重要的**负向机制**：统治者可以通过破坏 M7（声誉网络）与 M12（组织的 DP）来降低民间集体行动能力，从而降低被推翻的风险 —— 代价是同时降低了民间供给公共品的能力（M1），因此国家必须自己承担更多公共品，而它的 `q_obs` 又很差（M4）。**这个权衡是内生的，会产出一个可追溯的"高压 + 低治理"均衡。**

### 6.7 东亚证据小结（给工程的三条）

1. **大帝国是"弱"的，不是"强"的** —— 用 M4 + M17 实现；校准靶是"疆域大 → 人均税负低、人均地方公共服务少"（Sng & Moriguchi 2014）。
2. **宗族是一条平行的合作技术，不是过渡形态** —— 用 M11 的双通道 + 路径依赖实现。
3. **灌溉不决定政体** —— 用 M16 的 CPR 博弈实现，让政体形态由 `C_D`、`q_obs`、`internal_share` 决定。

---

## 7. 学界争议与未解决问题

### 7.1 昂贵惩罚（costly punishment）的演化解释是否成立

- **支持方**：Boyd, Gintis, Bowles & Richerson (2003) 的多群体模型（V，全文核验）；Fehr & Gächter (2002) 的实验。
- **挑战一（形态不对）**：Bowles, Boyd, Mathew & Richerson (2012) BBS 35:20–21，题为 **"The punishment that sustains cooperation is often coordinated and costly"** —— 田野中的惩罚是**协调的、集体决定的**，不是实验室里的个体第三方惩罚。**注意：这条挑战来自支持方内部（同一批作者），这提高了它的可信度。**
- **挑战二（会被滥用）**：Herrmann, Thöni & Gächter (2008) 的反社会惩罚；Nikiforakis (2008) 的反惩罚；Rand & Nowak (2011) 的反社会惩罚演化。
- **挑战三（有更便宜的替代）**：Panchanathan & Boyd (2004) 用声誉性排除替代昂贵惩罚，从而绕过二阶搭便车；但该文也有 Nature 上的 "Second-order free-riding problem solved? (reply)"（437:E8–E9，核验元数据），表明存在质疑。
- **本项目的立场**：**同时实现三条执法技术**（声誉排除 / 内化 / 专职执法者），让哪一条被采用成为地理与技术的函数。不选边站。

### 7.2 网络互惠（network reciprocity）是否稳健 —— **本简报中最清晰的一个"理论 vs 实验"冲突**

- **理论侧**：`b/c > k`（Ohtsuki et al. 2006，Nature）；Nowak & May (1992) 的空间格子。
- **理论侧内部的反例**：Hauert & Doebeli (2004) —— snowdrift 博弈中空间结构**往往抑制**合作。**⇒ 效应方向依赖博弈类型。**
- **人类实验侧的负面结果**：Gracia-Lázaro et al. (2012)（1229 人；格子与无标度网络的**最终合作率相同**，均 ~30%；结论"population structure has little relevance"）；Grujić et al. (2010)。机制解释是 **"moody conditional cooperation"** —— 人根据邻居近期行为而非收益差异决策。
- **人类实验侧的正面结果（但含义不同）**：Rand et al. (2011) —— **动态重连（30%）有效，10% 无效，固定网络无效**。这支持的不是"拓扑"，而是"伙伴选择/退出"。
- **未解决**：为什么演化博弈论的拓扑预测在人类身上失败？"moody conditional cooperation" 这个行为规则本身从哪来？
- **本项目的立场**：**不实现拓扑加成**；实现伙伴选择与退出（M9），并把它与 `C_D`（M5）共用同一个状态量。**这是一个明确的、有证据支撑的简化决定。**

### 7.3 文化群体选择是否是解释人类合作的必要成分

- **支持**：Richerson et al. (2016) BBS 39:e30 "Cultural group selection plays an essential role in explaining human cooperation: A sketch of the evidence"；经验支撑 Handley & Mathew (2020) 的文化 F_ST 0.087–0.215 vs 遗传 F_ST ≤0.002。
- **反对**：Mace & Silva (2016) BBS 39，题为 "The role of cultural group selection in explaining human cooperation is a hard case to prove"。
- **未解决**：群体间竞争的强度（群体灭绝率）在史前的实际量级；Boyd et al. (2003) 用的 ≈0.0075/世代来自"一个估计"，**该原始估计本次未追溯**。
- **本项目的立场**：把群体灭绝率做成**由模拟内生产生的量**（战争、饥荒、迁移的结果），而不是外生参数。这样它是否达到 0.0075 的量级就变成一个**可检验的输出**，而不是一个假设。

### 7.4 Ostrom 设计原则的因果地位与外推范围

- **争议点**：(a) DP 是存续的原因还是结果？(b) 69 案例（27 完整）的样本能支撑多强的结论？(c) DP 能否外推到国家、军队、宗教等非 CPR 组织？
- **方法论进展**：Baggio et al. (2016) 用 QCA 表明 DP 是**组合性（configural）**的，且 `1B/2B/4B/6` 是**必要但不充分** —— 这本身就否定了"加法式 buff"的用法。
- **本项目的立场**：M12 中实现"必要条件门 + 加权 hazard"的两段式；并给每条 DP 明确的资源成本以打破自证循环。**DP 对非 CPR 组织的应用标 C 级。**

### 7.5 群体规模对合作的效应方向

- Olson (1965) 预测大群体更难合作。
- Isaac, Walker & Williams (1994) J. Public Economics 54:1–36 专门研究大群体的公共品自愿供给（核验元数据；**数值未取得**）—— 该研究线的存在本身说明"大群体一定更差"不是共识。
- Gavrilets & Richerson (2017) 在 **us-vs-them** 博弈中发现 `n` 的强负效应；在 **us-vs-nature** 中效应依赖被惩罚成本。
- **⇒ 效应方向依赖博弈类型与 MPCR。**
- **本项目的立场**：**不实现"规模惩罚项"这个 shortcut。** 规模的影响必须通过 M1（`X0` 与供给函数形状）、M3（层级数）、M4（监督衰减）三条具体通道产生。这样"为什么这个组织在 500 人时垮了"永远有具体答案。

### 7.6 道德神/宗教与社会复杂度的先后顺序 —— **一个已被撤稿的结论**

- Whitehouse, François, Savage, Currie, Feeney, Cioni, Purcell, Ross, Larson, Baines, ter Haar, Covey & Turchin (2019) "Complex societies precede moralizing gods throughout world history", Nature 568:226–229, DOI `10.1038/s41586-019-1043-4` —— **已于 2021 年撤稿**。
- 撤稿声明：Nature 595:320, DOI `10.1038/s41586-021-03656-3`（核验元数据）。
- 触发撤稿的批评：Beheim, Atkinson, Bulbulia, Gervais, Gray, Henrich, Lang, Monroe, Muthukrishna, Norenzayan, Purzycki, Shariff, Slingerland, Spicer & Willard (2021) **"Treatment of missing data determined conclusions regarding moralizing gods"**, Nature 595:E29–E34, DOI `10.1038/s41586-021-03655-4`（核验元数据）。**批评的核心从标题即可读出：缺失数据的处理方式决定了结论。**
- 另有史学界的集体回应：Slingerland et al. (2020) "Historians Respond to Whitehouse et al. (2019)", Journal of Cognitive Historiography 5:124–141, DOI `10.1558/jch.39393`，OA PDF 在 `https://researchonline.lse.ac.uk/id/eprint/107612/1/Historians_Respond_to_Whitehouse_et_al_complete.pdf`（核验元数据；PDF 本次未打开）。
- **本项目的立场（重要）**：
  - **不要**实现"社会复杂度达到阈值 → 解锁道德神"，也**不要**实现反方向。**这个时序关系目前没有可靠的定量结论。**
  - 宗教应当从 M1（祭祀是一个公共品项目）+ M7（声誉与超自然监督是一种降低 `c_mon` 的技术）+ M13（规范内化的载体）中涌现，**其与国家形成的时序关系应当是模拟的输出，而不是输入。**
  - 相关但**不用于承载时序结论**的文献：Purzycki, Apicella, Atkinson et al. (2016) Nature, DOI `10.1038/nature16980`（"Moralistic gods, supernatural punishment and the expansion of human sociality"，核验元数据）；Norenzayan et al. (2016) BBS 39:e1, DOI `10.1017/s0140525x14001356`（核验元数据）。

### 7.7 R² 高不等于机制正确：Turchin 类模型的方法论争议

- Turchin et al. (2013) 的 R² = 0.65 是对**帝国空间分布**的拟合。消融实验显示军事技术扩散贡献巨大（去掉后 R² 崩到 0.16）。**这可以有两种解释**：(a) 军事技术确实是主因；(b) 模型的其他部分弱，全靠一个强空间梯度变量在拟合。
- SAR 分析显示，仅用三个变量（草原距离、农业史、海拔）在控制空间自相关后就能解释 **42%** 方差 —— **即相当一部分解释力来自空间自相关本身，而非机制。**
- 该研究群体内部的方法论争论仍在继续：本次检索到 Turchin (2025) 的预印本，题为 "Bayesian phylogenetic analyses cannot be used to test hypotheses about the evolution of large-scale complex societies during the Holocene"（DOI `10.31235/osf.io/xenpv_v1`，核验元数据）—— 表明这一领域的方法论争议持续存在。相关的系统发生学路线：Currie, Greenhill, Gray, Hasegawa & Mace (2010) "Rise and fall of political complexity in island South-East Asia and the Pacific", Nature 467:801–804, DOI `10.1038/nature09461`（核验元数据）。
- **本项目的立场**：**不要用宏观拟合度作为主要验证标准。** 主要验证标准应当是纲领第 8 条的意思 —— **机制层面的合理性 + 因果链完整性**。宏观统计只作为**辅助 sanity check**（例如 §4.11 的 PC1 解释率靶）。同时，**必须做消融实验**：Turchin et al. 的消融设计（关掉一个机制看 R² 变化）是本项目应当直接照搬的验证方法论。

### 7.8 Greif 的史料解读争议

- Greif (1993) 的 Maghribi 商人多边声誉机制受到 Edwards 与 Ogilvie 的挑战；Greif (2008) 有专门的反驳文（SSRN DOI `10.2139/ssrn.1159681`，题为 "...Refuting Edwards and Ogilvie"，核验元数据）。
- **本项目的立场**：多边声誉机制的**博弈论内核**（`q > c/b` + 集体拉黑）是稳的（它就是 Nowak 2006 的 indirect reciprocity）；争议在于**特定史料是否支持该机制在该时空真实运作**。由于本项目不复刻真实历史，**争议不影响机制的采用**，但它是一个好的提醒：**同一个机制在史料中往往难以与替代机制区分** —— 这正是本项目要求"可追溯因果链"的价值所在（我们的模拟里没有这个识别问题，因为我们保存了真实发生的一切）。

### 7.9 尚未解决且对本项目关键的问题

1. **实验室 `b/c` 与历史项目 `b/c` 如何对齐？** 实验室的 MPCR 与历史上"修渠的收益/成本比"之间没有任何已建立的映射。
2. **制度退化率 `μ10` 的经验估计是什么？** Turchin et al. (2013) 只设定 `μ01 ≪ μ10`，未给经验依据。
3. **信息技术如何量化提升 `q` 与 `λ_info`？** 文字、簿册、标准计量、驿传各提升多少？**本次未找到任何量化文献。**
4. **群体灭绝率在史前的实际量级？** Boyd et al. 用 0.0075/世代，来源未追溯。
5. **`λ≈3.2` 的层级比在古代组织中成立吗？** Zhou et al. 数据全为现代。
6. **反社会惩罚倾向 `p_anti` 的跨文化分布？** Herrmann et al. (2008) 有数据但本次未取得。
7. **如何在不预设的前提下让"科举/常规审计"这类监督技术涌现？** 这是本项目最难的设计问题之一：监督技术的收益只有在政体足够大时才显现，但政体要变大又需要监督技术 —— 一个鸡生蛋问题。**建议方向**：让间接统治（M4 的失效条件分支）成为过渡桥梁。

---

## 8. 反模式：本领域常见的错误建模方式

### 反模式 1（最重要）：给 agent 一个"忠诚度"标量 —— 它具体掩盖了什么

用户特别问了这一条，所以我把它拆到底。假设我们写下：

```python
class Agent:
    loyalty: float   # 0.0 - 1.0，对所属组织的忠诚度
```

然后用 `if random() < agent.loyalty: contribute()`。这一行代码**在数学上一次性抹掉了下面 10 个真实约束**，每一个都是本简报某一节的全部内容：

| # | 被抹掉的约束 | 它本来的样子 | 抹掉的后果 |
|---|---|---|---|
| 1 | **供给函数的形状** | `P = X/(X+X0)`；`X0` 由工程规模与地理决定 | 修一条小渠和修一条大运河变成同一件事。规模报酬递减、最低门槛、阈值效应全部消失。**"这个组织为什么撑不起这个工程"这个问题不再有答案。** |
| 2 | **收益分配规则 `share_i`** | 制度决定；leader 可截留 `z`；可按投入比例（DP 2B） | 分配不公不再影响参与意愿。**"为什么下游村落不出工了"的答案从"因为上游多取了三成水"退化成"因为他们忠诚度低"。** |
| 3 | **监督概率 `q_obs`** | `q_0·exp(−d/λ_info)·ρ^L`，由距离、层级、信息技术决定 | 距首都 2000 里和 20 里变成一样。**文字、簿册、驿传的全部意义消失**，因为它们唯一的作用就是提高 `q_obs`。信息边界（纲领第 4 条）在组织维度上被架空。 |
| 4 | **执法成本随违规率下降** | `(1−p̃)·δ` | 这是 Boyd et al. (2003) 证明的**机制成立的必要条件**（固定成本时机制完全失效，其 Fig.4）。忠诚度标量里根本没有这个项，所以模拟里的执法在数学上是"不可能工作的那一种"。 |
| 5 | **二阶搭便车** | 谁来惩罚不惩罚的人？三种解法各有不同成本与规模上限 | 执法变成免费的、自动的。于是**"为什么这个社会发展出了专职执法者/宗族族规/超自然惩罚"这三条完全不同的历史路径合并成了一个数字。** |
| 6 | **退出成本 `C_D`** | 地形 + 资产专用性 + 社会网络损失 | **专制程度 `z*` 失去唯一的内生来源**（Powers & Lehmann 2014）。从平等到专制的转变只能靠脚本给。Carneiro 的 environmental circumscription 也一起失效。 |
| 7 | **群体间竞争与制度的群体级复制** | `b/c > 1 + z + n/m`；ethnocide 式覆盖；`μ01 ≪ μ10` | 制度不再有群体级的生死。**制度无法在长时段积累，也无法退化。**"为什么这个地区的组织能力比邻区强"的答案从"因为它经历了 400 年的高强度群体竞争"退化成初始化的随机数。 |
| 8 | **重复互动与折现 `w, δ`** | `w > c/b`；`δ = 1/(1+r)`，`r` 含政权不稳风险 | **乱世不再自动降低合作。** "王朝末期为什么突然横征暴敛"这条正反馈回路（δ↓ → 更掠夺 → 更不稳 → δ↓↓）消失。 |
| 9 | **合作倾向的群体级性质** | Henrich et al. (2005)：群体级变量解释力强，个体级变量解释力弱 | 忠诚度作为个体属性，**方向就是错的**（把群体级异质性当成个体级噪声）。M15 的整条路径依赖机制消失。 |
| 10 | **规范内化 `η` 是权重不是结果** | `u = (1−η)π + η(v1x + v2y)`，博弈仍然要解 | 这是最微妙的一条。`η` 高的 agent **仍然会在监督弱、惩罚轻、能跑的时候搭便车**，因为博弈依然在解。而 `loyalty` 直接给出行为，**约束不再有机会生效。** |

**更根本的问题（元层面）**：`loyalty` 是一个**结果变量被当作输入变量**。集体行动理论的全部内容就是"在什么条件下人们会为集体出力"—— 把答案直接写成一个字段，等于把整个理论删掉，只留下它的输出。这在纲领的语言里就是：**它把因果链的中间全部环节替换成了一个不可追溯的数字**。几百年后问"为什么这个国家灭亡了"，能追到的最后一层是 `loyalty = 0.31`，再往上就没有了。

**唯一可接受的替代**：`η`（规范内化权重，M13）。它是**偏好参数**而不是**行为输出**；它进入效用函数而不是替代决策；它**必须由群体间竞争与执法制度的历史内生演化出来**（Gavrilets & Richerson 2017 的核心结果：促进对搭便车者的惩罚比促进生产更有效地导致内化）。也就是说，即使我们要一个"忠诚"的数字，它也必须是**制度史的输出**，而它下游还要经过完整的博弈才变成行为。

**同类反模式（同一个错误的其他化身）**：`cohesion`、`morale`、`legitimacy`、`social_capital`、`trust_level`、`stability` —— 如果这些是 agent/组织上的自由标量而不是可计算量的函数，都是同一个错误。**判据**：问一句"这个数字是由什么算出来的？"如果答案是"由上一 tick 的它自己加减一个增量算出来的"，它就是一个隐藏的剧情变量。

---

### 反模式 2：把公地悲剧当作默认结局

- **错在哪**：Hardin (1968) 描述的是 **open access（无制度）**，不是 **common property（有制度的共有）**。Ostrom 的整条经验研究线（以及 Baggio et al. 2016 的 8.7 vs 4.3 条 DP 对照）表明有制度的共有可以长期存续。
- **失真形态**：所有共有资源单调走向崩溃 → 模拟中不会出现长期存续的水利社群、山林共有、渔场轮作。**东亚最重要的一类组织（水利会、山林共有、族田）在模拟里根本不会出现。**
- **正确做法**：见 §2.2 —— 同时实现两套动力学，由 M12 的存续判定器切换。**崩溃必须是制度失效的下游结果。**

### 反模式 3：把 Ostrom 的 8/11 条原则当 checklist 加 buff

- **错在哪**：Baggio et al. (2016) 的核心方法论结论是 DP 是**组合性（configural）**的，且 `1B/2B/4B/6` 是**必要但不充分**。线性加权抹掉了必要性结构。此外样本是 69 案例（**仅 27 完整**），全部是林业/灌溉/渔业。
- **失真形态**：(a) 一个具备 7 条 DP 但缺 `1B`（生物物理边界不清）的组织在模型里显得很稳，实际上应当高危；(b) DP 没有成本，于是所有组织都会一路点满 DP → 所有组织都变得极稳 → **文明不会崩溃**。
- **正确做法**：M12 的两段式（必要条件门 + 加权 hazard），并给每条 DP 明确的资源成本。

### 反模式 4：用网络拓扑给合作加成

- **错在哪**：`b/c > k`（Ohtsuki et al. 2006）在人类实验中未被支持。Gracia-Lázaro et al. (2012)：1229 人，方格与无标度网络的**最终合作率相同**（~30%）；作者结论 "population structure has little relevance as a cooperation promoter or inhibitor"。Hauert & Doebeli (2004) 进一步表明效应方向依赖博弈类型（snowdrift 中空间结构**抑制**合作）。
- **失真形态**：会给"聚落网络结构"一个虚假的解释力。更糟的是，它会让模拟中"改变道路网/婚姻网拓扑"产生合作率的直接变化，产出一整类不真实的因果链。
- **正确做法**：M9 —— 实现**伙伴选择与退出**（Rand et al. 2011：30% 重连率有效，10% 无效），把它接到 `C_D`。**这是"少一个机制、准一个机制"的净收益。**

### 反模式 5：Wittfogel 式"大型水利 → 必然专制"科技树

- **错在哪**：该假说存在长期实质争议（Hunt & Hunt et al. 1976 及其评论）；有明确的反例（Lansing & Kremer 1993 的巴厘水庙自组织；Sarker & Itoh 2001 的日本长期存续灌溉 CPR；McKean 1992 的日本 *iriai*）；而东亚的国家能力证据方向相反（Sng & Moriguchi 2014：大帝国是低榨取、薄治理的）。Bentzen et al. (2016) 的跨国相关是相关性，不是机制。
- **失真形态**：这是最典型的"隐藏剧情树" —— 一旦地图上出现干旱冲积平原，专制帝国就被预定了。**这直接违反纲领第 1 条（不预先规定文明必须经历哪些阶段）。**
- **正确做法**：M16 —— 灌溉是一个上下游不对称的 CPR 博弈 + 对称的维护公共品，政体形态由 `C_D`、`q_obs`、`internal_share` 决定。让自治、地方精英把持、国家接管三种结局都可能。

### 反模式 6：让惩罚免费、无反击、只针对坏人

- **错在哪**：Herrmann et al. (2008) 的反社会惩罚（打击高贡献者）；Nikiforakis (2008) 的反惩罚（摧毁惩罚净收益）；Ostrom DP `4B`（对监督者的监督）之所以存在就是因为执法者会被俘获。
- **失真形态**：系统性**高估**执法效力 → 大规模合作过早出现 → 得到一个"过于顺从、过于稳定"的假社会。这正是纲领最担心的"无缘无故"。
- **正确做法**：M14 —— 三条病态通道全部实现。**校准靶（来自 Mathew & Boyd 2011 的 Turkana 数据）：真实组织的违规率 40–60%，制裁覆盖率 47–67%，严重制裁只占被制裁案例的约 45%。如果模拟跑出人人守规，就是错的。**

### 反模式 7：把执法成本设为固定值

- **错在哪**：Boyd et al. (2003) 的结论是硬的："punishment leads to increased cooperation **only to the extent that** the costs associated with being a punisher decline as defectors become rare."；固定成本时（其 Fig.4）**机制完全失效**。
- **失真形态**：执法机构建起来了，但它在数学上无法把社会推向高合作 —— 合作率会停在一个低平台上，而我们会误以为是别的参数不对，花大量时间调错的东西。
- **正确做法**：M2 的 `(1−p̃)·δ` 项。**这是一行代码，但它决定整个机制是否工作。**

### 反模式 8：只在个体层面演化合作

- **错在哪**：单层选择下，个体层面的合作在大群体中会被侵蚀。多层次选择是唯一已知的、能把合作规模推到 ~100 人以上的机制（Boyd et al. 2003：无惩罚 ~50 人上限，有惩罚 + 群体选择 ~100 人）。而群体选择需要**群体间的文化变异**，Handley & Mathew (2020) 证明了这种变异确实足够大（族群间文化 F_ST 0.087–0.215 vs 遗传 ≤0.002）。
- **失真形态**：制度永远无法在长时段积累；每个群体独立地在低合作均衡附近徘徊；不会出现"某个地区的组织传统显著强于邻区"这种路径依赖。
- **正确做法**：M6 —— 制度以**群体**为单位复制（ethnocide 式覆盖）与灭绝，且 `μ01 ≪ μ10`。

### 反模式 9：把制度当作永久获得的科技

- **错在哪**：Turchin et al. (2013) 显式设定制度退化快于产生（`μ01 ≪ μ10`），这是其模型能产出兴衰循环的原因之一。相反，他们把**军事技术**设为"一旦获得永不丢失"—— 注意这两类东西被区别对待。
- **失真形态**：所有文明单调走向更高组织化；不会有制度崩溃、失传、退化；"为什么这个帝国的官僚系统烂掉了"没有机制答案。
- **正确做法**：M18 —— 制度状态有丢失率，且丢失率受识字率与维护投入调节。

### 反模式 10：用亲缘选择解释大规模合作

- **错在哪**：`r > c/b` 在 `r` 很小时几乎不可能满足；Hill et al. (2011) 表明狩猎采集群体的共居成员**大量是非亲属**。
- **失真形态**：模拟中所有组织都是宗族的放大版；无法产出行会、教团、军事同盟、官僚制这些**非亲属**组织；而这恰恰是东亚历史中最有意思的张力（clan vs corporation，Greif & Tabellini 2017）。
- **正确做法**：M11 的双通道，并让非亲属通道从一开始就存在（依赖 `w` 与 `q`）。

### 反模式 11：让 LLM 决定合作是否成功

- **错在哪**：这直接违反纲领第 5 条。而且实践上，LLM 会倾向于让"有戏剧性的"组织成功。
- **失真形态**：涌现变成生成。因果链的末端是"因为模型这么写了"。
- **正确做法**：M19 的两阶段切分 —— **LLM 写规则内容与理由（political game form，慢 tick，触发式，次数受限）；规则系统编译规则为参数、检查数学可行性、按实际收益裁决通过与否、执行全部后果。** 依据是 Powers, van Schaik & Lehmann (2016) 对制度的定义（"a mechanism whose outcome is a game form"，且政治博弈的频率远低于经济博弈）。

### 反模式 12：把实验室参数直接当古代参数

- **错在哪**：实验室 PGG 的 MPCR、期数、匿名性、支付规模与历史情境都不可比。而且本简报中最常被引用的实验参数（Fehr & Gächter）**本次根本没能核验到**。
- **失真形态**：给出一个看起来精确、实际上没有依据的合作率。
- **正确做法**：用 Boyd et al. (2003) 的**文化演化模型参数**（`c=0.2, k=0.2, p=0.8, e=0.02, m=0.01, μ=0.01, ε=0.015`）作为量级起点 —— 因为作者明确说这组参数是"chosen to represent cultural evolution in small-scale societies"，比实验室参数更接近我们的用途。然后**扫描而不是固定**。

### 反模式 13：把组织规模当作连续可扩展的

- **错在哪**：Zhou et al. (2005) 显示群体规模呈离散层级，比值 ≈3.2（p=0.024）；Powers & Lehmann (2014) 的协调难度随规模上升（`g_A=0.15` vs `g_H=0.01`）；M4 的监督随层级衰减。
- **失真形态**：组织可以平滑地从 50 人长到 50 万人，中间没有结构性危机。**这会抹掉"规模跨越阈值时必须发明新的组织技术"这一整类历史事件**（这恰恰是最有意思的一类）。
- **正确做法**：M3 + M4 —— 规模跨越 `λ` 层时强制增加层级，层级增加即触发 M19 的政治博弈慢 tick。**组织规模危机自动成为制度创新的触发器。**

### 反模式 14：用"道德神/宗教"作为合作的解锁项

- **错在哪**：Whitehouse et al. (2019) 关于"复杂社会先于道德神"的结论**已于 2021 年撤稿**（Nature 595:320），触发撤稿的批评是 Beheim et al. (2021) "Treatment of missing data determined conclusions regarding moralizing gods"（Nature 595:E29–E34）。**这个时序关系目前没有可靠的定量结论**（两个方向都没有）。
- **失真形态**：任何方向的硬编码时序都是在把一个撤稿级别的不确定性写成规则。
- **正确做法**：宗教从 M1（祭祀作为公共品）+ M7（超自然监督作为降低 `c_mon` 的技术）+ M13（规范内化的载体）中涌现；**时序关系是输出。**

### 反模式 15：用宏观拟合度作为主要验证标准

- **错在哪**：Turchin et al. (2013) 的 R²=0.65 中，仅三个空间变量在控制空间自相关后就解释 42% 方差 —— 相当部分解释力来自空间自相关而非机制。而消融实验显示去掉军事技术后 R² 崩到 0.16，说明单一变量承担了过多解释力。
- **失真形态**：会导致我们朝"拟合真实历史"的方向调参，从而把真实历史偷偷变成剧情模板 —— **直接违反纲领的核心原则**。
- **正确做法**：主验证标准是机制合理性 + 因果链完整性。宏观统计只作辅助 sanity check（§4.11 的 PC1 ≈70–90% 靶）。**同时照搬 Turchin et al. 的消融实验方法论**：关掉一个机制，看输出如何变化 —— 这既是验证，也是纲领第 6 条"反事实实验"的直接实现。

---

## 9. 无来源判断（D 级，LLM 常识，不得当作历史规律）

以下全部是**我为了让模拟能跑而做的假设**，没有文献来源。**任何一条都不得被引用为历史规律，也不得作为对真实历史的判断。**

### D-1 监督衰减的函数形式与参数
`q_obs = q_0 · exp(−d/λ_info) · ρ^L` 这个形式、以及 `λ_info`、`ρ`、`leak_0` 的任何数值。**文献只支持"大国监督更难"这个方向**（Sng & Moriguchi 2014 摘要级），不支持任何具体函数形式或参数。

### D-2 每增加一个管理层级的租金漏损率
无来源。建议初值靠扫描确定，并用"疆域大 → 人均税负低"这个定性靶反推。

### D-3 把 `λ≈3.2` 外推到古代军事编制与官僚层级
Zhou et al. (2005) 的数据全部来自现代社会。古代什伍制、十进制军制是否遵循 ×3 —— **我不知道**。

### D-4 DP 数量到 hazard 的映射函数与 `β`
`hazard = h_0·exp(−β·Σw_j DP_j)` 的形式与 `β` 的值无来源。Baggio et al. (2016) 只给了成功/失败两组的 DP 数均值（8.7 vs 4.3），没有给风险函数。

### D-5 退出成本 `C_D` 的组成与权重
`C_D = C_terrain + C_asset + C_social` 这个分解、以及三项的相对权重与具体函数，无来源。Powers & Lehmann (2014) 把 `C_D` 当成一个 0–1 的扫描参数，没有把它分解到地理。

### D-6 折现因子与政权风险的耦合形式
`δ = 1/(1+r)`，`r = 时间偏好 + 死亡风险 + 制度不稳定风险` 这个加法分解无来源。"δ↓ → 更掠夺 → 更不稳 → δ↓↓" 这条正反馈是**我的推断**，尽管它在方向上与 North & Weingast (1989) 的承诺逻辑相容。

### D-7 连带责任是"`q_obs` 低时的最优替代品"这一推论
§6.5 中我推断：一个监督能力弱的大帝国会倾向于发明连带责任制度（保甲/连坐），因为它把监督成本转移给被监督者的同侪。**这条推论没有来源**，本次东亚检索也没有找到支持它的量化文献。它在机制上与 Greif, Milgrom & Weingast (1994) 的行会集体制裁同构，但**同构不等于历史事实**。

### D-8 空间层级设为「聚落 → 市场社区 → 州县 → 政体」
这个层级划分借用了我记忆中的 Skinner 市场层级，但 **Skinner 的具体数值本次未取得**（OpenEdition 连接被拒）。层级的存在是 C 级结构判断，具体规模比是 D 级。

### D-9 "内部税占比 > θ 则必须提供公共品" 的阈值 θ
Blanton & Fargher (2008) 的机制方向有来源，**但其编码数值本次未取得**，因此任何阈值都是我们自选的。

### D-10 M1 中各类项目应当用哪种供给函数
"堤坝用硬阈值、渠道维护用 `X/(X+X0)`、战争用 Tullock"这个分派是我的判断。文献只给了函数形式本身，没有给"哪类工程对应哪个函数"的经验依据。**这条很重要，因为它决定博弈类型（PD vs stag hunt vs snowdrift），而 Hauert & Doebeli (2004) 表明不同博弈类型下空间结构的效应方向相反。**

### D-11 慢 tick 触发频率的上限（"每 100 年不超过 N 次"）
纯工程约束，为了防止 LLM 实际接管制度演化。无来源。

### D-12 文化 F_ST 校准靶设为 0.05–0.25
这个区间取自 Handley & Mathew (2020) 的 0.087–0.215（族群间）与 0.002–0.058（clan 间）的**并集的近似**。**把它当作"我们模拟应当命中的靶"是我的决定**，而不是文献的建议。而且该数据只来自肯尼亚 4 个牧业族群，外推到东亚农业社会是外推。

### D-13 "宗族天花板 ≈ 132–567 人"
把 Greif & Tabellini 的 clan 通道与 Zhou et al. 的 `S4–S5` 层（132.5–566.6）挂钩，是我做的连接。**两篇文献之间没有这个关系。**

### D-14 组织规模跨越 `λ` 层时触发制度创新
把 M3 的层级阈值接到 M19 的政治博弈触发器，是纯工程设计。无来源。

### D-15 反社会惩罚倾向 `p_anti` 作为文化状态变量
Herrmann et al. (2008) 确实发现反社会惩罚强度跨社会不同，但把它实现为一个可演化的文化状态变量、以及它的演化规则，是我的设计。**其数值本次未取得。**

---

## 10. 参考文献

**标记**：`[V-全文]` = 本次真实读取了全文或大段内容；`[V-元]` = 本次真实核验了元数据（Crossref 或 OpenAlex 返回）；`[V-摘]` = 核验了元数据 + 摘要；`[未核验]` = 我凭记忆写下，本次检索中未确认，**不用于承载任何结论**。

### 10.1 集体行动与公共池塘资源治理

1. `[V-元]` Olson, M. (1965). *The Logic of Collective Action*. Harvard University Press. DOI `10.4159/9780674041660`.
2. `[V-元]` Hardin, G. (1968). "The Tragedy of the Commons." *Science* 162:1243–1248. DOI `10.1126/science.162.3859.1243`.
3. `[V-元]` Ostrom, E. (1990). *Governing the Commons*. Cambridge University Press. DOI `10.1017/cbo9780511807763`.（另有 2015 版 DOI `10.1017/cbo9781316423936`）
4. `[V-元]` Ostrom, E., Walker, J. & Gardner, R. (1992). "Covenants with and without a Sword: Self-Governance Is Possible." *American Political Science Review* 86:404–417. DOI `10.2307/1964229`.
5. `[V-元]` Ostrom, E. (2009). "A General Framework for Analyzing Sustainability of Social-Ecological Systems." *Science* 325:419–422. DOI `10.1126/science.1172133`. **全文未取得**（Science 封闭；OA 副本被 bot 防护拦截）。
6. `[V-元]` Ostrom, E. (2010). "Beyond Markets and States: Polycentric Governance of Complex Economic Systems." 本次核验到一条 *Transnational Corporation Review* 100:1–12 的重印记录，DOI `10.1080/19186444.2010.11658229`。**其 American Economic Review 原发表记录本次未核验；全文未取得。**
7. `[V-元]` Cox, M., Arnold, G. & Villamayor-Tomás, S. (2010). "A Review of Design Principles for Community-based Natural Resource Management." *Ecology and Society* 15(4):38. DOI `10.5751/es-03704-150438`. **全文未取得（站点 403）。**
8. `[V-全文]` Baggio, J.A., Barnett, A.J., Perez-Ibarra, I., Brady, U., Ratajczyk, E., Rollins, N., Rubiños, C., Shin, H.C., Yu, D.J., Aggarwal, R., Anderies, J.M. & Janssen, M.A. (2016). "Explaining success and failure in the commons: the configural nature of Ostrom's institutional design principles." *International Journal of the Commons* 10:417. DOI `10.18352/ijc.634`. **← 本简报 §2.3 / §4.9 的数值来源。** **[已核验]**（Crossref：*Int. J. of the Commons* 10:417, 2016，12 位作者相符）
9. `[V-元]` Agrawal, A. (2001). "Common Property Institutions and Sustainable Governance of Resources." *World Development*. DOI `10.1016/s0305-750x(01)00063-8`.
10. `[V-元]` Agrawal, A. & Chhatre, A. (2005/2006). "Explaining success on the commons: Community forest governance in the Indian Himalaya." *World Development* 34:149–166. DOI `10.1016/j.worlddev.2005.07.013`.
11. `[V-元]` McKean, M.A. (1992). "Success on the Commons." *Journal of Theoretical Politics* 4:247–281. DOI `10.1177/0951692892004003002`.（日本 *iriai* 共有制）
12. `[V-摘]` Rustagi, D., Engel, S. & Kosfeld, M. (2010). "Conditional Cooperation and Costly Monitoring Explain Success in Forest Commons Management." *Science* 330:961–965. DOI `10.1126/science.1193649`. **数值未取得（摘要级：埃塞俄比亚 49 个森林使用者组）。**
13. `[V-元]` Ostrom, E. & Ahn, T.K. (2009). "The Meaning of Social Capital and its Link to Collective Action." Edward Elgar. DOI `10.4337/9781848447486.00008`. **全文未取得（DLC 链接 403）。**
14. `[V-元]` Barnett, A. et al. (2020). "Defining Success in the Commons..." *International Journal of the Commons* 14:366. DOI `10.5334/ijc.994`.
15. Ostrom, E. (1992). *Crafting Institutions for Self-Governing Irrigation Systems*. ICS Press. **[已核验]**（Crossref 命中 Smout 在 *Regulated Rivers* 1993 年对该书的书评，DOI `10.1002/rrr.3450080314`）｜ Tang, S.Y. (1992). *Institutions and Collective Action: Self-Governance in Irrigation*. ICS Press. **[已核验]**（同刊 1993 年书评，DOI `10.1002/rrr.3450080315`；完整副标题为 *Self-Governance in Irrigation*）｜ Lam, W.F. (1998). *Governing Irrigation Systems in Nepal*. ICS Press. **[未找到]**（Crossref/OpenLibrary 本次均未命中该书记录；Lam 本人及其与 Ostrom 合著的尼泊尔灌溉论文确实存在，故不判为不存在，但书目未证实）｜ Wade, R. (1988). *Village Republics* **[未找到]**（本次未核验）｜ Baland, J.-M. & Platteau, J.-P. *Halting Degradation of Natural Resources* **[未找到]**（本次未核验）。**以上四条不承载任何结论；§4.13 的参数缺口结论维持。**

### 10.2 公共品博弈、惩罚与二阶搭便车

16. `[V-元]` Fehr, E. & Gächter, S. (2000). "Cooperation and Punishment in Public Goods Experiments." *American Economic Review* 90(4):980. DOI `10.1257/aer.90.4.980`. **封闭获取，参数未取得。**
17. `[V-元]` Fehr, E. & Gächter, S. (2002). "Altruistic punishment in humans." *Nature* 415:137–140. DOI `10.1038/415137a`. **封闭获取（OpenAlex 确认无 OA 副本），参数未取得。** 另有回复 *Nature* 433:E1–E2, DOI `10.1038/nature03257`。
18. `[V-全文]` **Boyd, R., Gintis, H., Bowles, S. & Richerson, P.J. (2003). "The evolution of altruistic punishment." *PNAS* 100:3531–3535. DOI `10.1073/pnas.0630443100`, PMC152327. ← 本简报参数最硬的一篇（§2.5 / §4.2）。** **[已核验]**（Crossref：PNAS 100:3531–3535, 2003，作者与页码全部相符）
19. `[V-元]` Herrmann, B., Thöni, C. & Gächter, S. (2008). "Antisocial Punishment Across Societies." *Science* 319:1362–1367. DOI `10.1126/science.1153808`. **数值未取得。** **[已核验]**
20. `[V-元]` Nikiforakis, N. (2008). "Punishment and counter-punishment in public good games: Can we really govern ourselves?" *Journal of Public Economics* 92:91–112. DOI `10.1016/j.jpubeco.2007.04.008`. **[已核验]**
21. `[V-元]` Gächter, S., Renner, E. & Sefton, M. (2008). "The Long-Run Benefits of Punishment." *Science* 322:1510. DOI `10.1126/science.1164744`. **数值未取得；仅用标题方向。**
22. `[V-元]` Gürerk, Ö., Irlenbusch, B. & Rockenbach, B. (2006). "The Competitive Advantage of Sanctioning Institutions." *Science* 312:108–111. DOI `10.1126/science.1123633`. **数值未取得。**
23. `[V-元]` Panchanathan, K. & Boyd, R. (2004). "Indirect reciprocity can stabilize cooperation without the second-order free rider problem." *Nature* 432:499–502. DOI `10.1038/nature02978`. 另有 "Second-order free-riding problem solved? (reply)" *Nature* 437:E8–E9, DOI `10.1038/nature04202`. **[已核验]**（正文与回复两条记录均在 Crossref 命中：*Nature* 432:499–502, 2004 与 437:E8–E9, 2005）
24. `[V-元]` Yamagishi, T. (1986). "The provision of a sanctioning system as a public good." *JPSP* 51:110–116. DOI `10.1037/0022-3514.51.1.110`.
25. `[V-元]` Fehr, E. & Fischbacher, U. (2004). "Third-party punishment and social norms." *Evolution and Human Behavior* 25:63–87. DOI `10.1016/s1090-5138(04)00005-4`.
26. `[V-元]` Balliet, D., Mulder, L.B. & Van Lange, P.A.M. (2011). "Reward, punishment, and cooperation: A meta-analysis." *Psychological Bulletin*. DOI `10.1037/a0023489`. **效应量未取得**（green OA 落地页 `https://research.rug.nl/en/publications/442ebd06-0c57-4966-9429-829112970170`，PDF 本次未打开）。
27. `[V-元]` Bowles, S., Boyd, R., Mathew, S. & Richerson, P.J. (2012). "The punishment that sustains cooperation is often coordinated and costly." *BBS* 35:20–21. DOI `10.1017/s0140525x1100118x`. **[已核验]**
28. `[V-元]` Rand, D.G. & Nowak, M.A. (2011). "The evolution of antisocial punishment in optional public goods games." *Nature Communications* 2:434. DOI `10.1038/ncomms1442`.
29. `[V-元]` Isaac, R.M., Walker, J.M. & Williams, A.W. (1994). "Group size and the voluntary provision of public goods." *Journal of Public Economics* 54:1–36. DOI `10.1016/0047-2727(94)90068-x`. **数值未取得。** 另有 Isaac & Walker (1988) *QJE* 103:179, DOI `10.2307/1882648`。
30. `[V-元]` Andrighetto, G., Brandts, J., Conte, R., Sabater-Mir, J., Solaz, H. & Villatoro, D. (2013). "Punish and Voice: Punishment Enhances Cooperation when Combined with Norm-Signalling." *PLoS ONE* 8:e64941. DOI `10.1371/journal.pone.0064941`.
31. `[V-元]` Dreber, A., Rand, D.G., Fudenberg, D. & Nowak, M.A. (2008). "Winners don't punish." *Nature* 452:348–351. DOI `10.1038/nature06723`. **[已修正: Dreber, A., Rand, D.G., Fudenberg, D. & Nowak, M.A. (2008). "Winners don't punish." *Nature* 452:348–351. DOI 10.1038/nature06723]** —— 本次核验中该记录在 Crossref 直接命中，前次"未命中"是检索失败而非文献不存在。文献真实，可用于 §7.1；但全文与数值本次仍未取得。
32. Holmström, B. (1982). "Moral Hazard in Teams." *The Bell Journal of Economics* 13(2):324–340. DOI `10.2307/3003457`. **[已核验]**（Crossref 直接命中）｜ Alchian, A.A. & Demsetz, H. (1972). "Production, Information Costs, and Economic Organization." *American Economic Review* 62:777–795. **[已核验]**（AER 原发表记录无 DOI 未直接命中，但 Crossref 命中三条署名相同的重印/转载记录：*The Economic Nature of the Firm*、*Firms, Organizations and Contracts*、*IEEE Engineering Management Review* 1975）｜ Chaudhuri, A. (2011). "Sustaining cooperation in laboratory public goods experiments." **[未找到]**（本次未核验）｜ Guzmán, R.A., Rodríguez-Sickert, C. & Rowthorn, R. (2007). "When in Rome, do as the Romans do." **[未找到]**（本次未核验）。以上两条未找到者不得承载任何结论。

### 10.3 合作演化的一般理论与网络

33. `[V-全文]` **Nowak, M.A. (2006). "Five rules for the evolution of cooperation." *Science*. DOI `10.1126/science.1133755`, PMC3279745. ← §2.6 / §4.1 的五条不等式来源。** **[已核验]**（Crossref：*Science* 314:1560–1563, 2006-12-08；建议补全卷页）
34. `[V-元]` Nowak, M.A. & May, R.M. (1992). "Evolutionary games and spatial chaos." *Nature* 359:826–829. DOI `10.1038/359826a0`.
35. `[V-元]` Nowak, M.A. & Sigmund, K. (1998). "Evolution of indirect reciprocity by image scoring." *Nature* 393:573–577. DOI `10.1038/31225`.
36. `[V-元]` Milinski, M., Semmann, D. & Krambeck, H.-J. (2002). "Reputation helps solve the 'tragedy of the commons'." *Nature* 415:424–426. DOI `10.1038/415424a`.
37. `[V-元]` Ohtsuki, H., Hauert, C., Lieberman, E. & Nowak, M.A. (2006). "A simple rule for the evolution of cooperation on graphs and social networks." *Nature*. DOI `10.1038/nature04605`.（Crossref 未返回卷/页）
38. `[V-元]` Hauert, C. & Doebeli, M. (2004). "Spatial structure often inhibits the evolution of cooperation in the snowdrift game." *Nature* 428:643–646. DOI `10.1038/nature02360`. 另 Doebeli & Hauert (2005) *Ecology Letters* 8:748–766, DOI `10.1111/j.1461-0248.2005.00773.x`.
39. `[V-全文]` **Traulsen, A. & Nowak, M.A. (2006). "Evolution of cooperation by multilevel selection." *PNAS* 103:10952–10955. DOI `10.1073/pnas.0602530103`, PMC1544155. ← `b/c > 1 + z + n/m` 来源。** **[已核验]**（Crossref：PNAS 103:10952–10955, 2006）
40. `[V-全文]` **Gracia-Lázaro, C., Ferrer, A., Ruiz, G., Tarancón, A., Cuesta, J.A., Sánchez, A. & Moreno, Y. (2012). "Heterogeneous networks do not promote cooperation when humans play a Prisoner's Dilemma." *PNAS* 109:12922–12926. DOI `10.1073/pnas.1206681109`, PMC3420198. ← §4.6 数值来源。** **[已核验]**（Crossref：PNAS 109:12922–12926, 2012，七位作者相符）
41. `[V-元]` Grujić, J., Fosco, C., Araujo, L., Cuesta, J.A. & Sánchez, A. (2010). "Social Experiments in the Mesoscale: Humans Playing a Spatial Prisoner's Dilemma." *PLoS ONE* 5:e13749. DOI `10.1371/journal.pone.0013749`.
42. `[V-全文]` **Rand, D.G., Arbesman, S. & Christakis, N.A. (2011). "Dynamic social networks promote cooperation in experiments with humans." *PNAS* 108:19193–19198. DOI `10.1073/pnas.1108243108`, PMC3228461. ← 30% vs 10% 重连率的来源。** **[已核验]**（Crossref：PNAS 108:19193–19198, 2011）
43. `[V-元]` Jordan, J.J., Rand, D.G., Arbesman, S., Fowler, J.H. & Christakis, N.A. (2013). "Contagion of Cooperation in Static and Fluid Social Networks." *PLoS ONE* 8:e66199. DOI `10.1371/journal.pone.0066199`.
44. `[V-元]` Melamed, D. & Simpson, B. (2016). "Strong ties promote the evolution of cooperation in dynamic networks." *Social Networks*. DOI `10.1016/j.socnet.2015.11.001`.
45. `[未核验]` Hamilton, W.D. (1964)；Trivers, R. (1971)；Axelrod, R. & Hamilton, W.D. (1981)；Sigmund, K. (2010) *The Calculus of Selfishness*。**（其结论在本简报中通过 Nowak 2006 的复述使用，标 V。）**

### 10.4 多层次选择、文化群体选择与规范内化

46. `[V-元]` Richerson, P.J., Baldini, R., Bell, A.V., Demps, K., Frost, K., Hillis, V., Mathew, S., Newton, E.K., Naar, N., Newson, L., Ross, C.T., Smaldino, P.E., Waring, T.M. & Zefferman, M. (2016). "Cultural group selection plays an essential role in explaining human cooperation: A sketch of the evidence." *BBS* 39:e30. DOI `10.1017/s0140525x1400106x`.
47. `[V-元]` Mace, R. & Silva, A.S. (2016). "The role of cultural group selection in explaining human cooperation is a hard case to prove." *BBS* 39. DOI `10.1017/s0140525x15000187`.
48. `[V-全文]` **Handley, C. & Mathew, S. (2020). "Human large-scale cooperation as a product of competition between cultural groups." *Nature Communications* 11:702. DOI `10.1038/s41467-020-14416-8`, PMC7000669. ← 文化 F_ST 数值来源（§4.7）。** **[已核验]**（Crossref：*Nature Communications* 11, 文章号 702, 2020）
49. `[V-全文]` **Mathew, S. & Boyd, R. (2011). "Punishment sustains large-scale cooperation in prestate warfare." *PNAS* 108:11375–11380. DOI `10.1073/pnas.1105604108`, PMC3136302. ← Turkana 搭便车率与制裁率（§4.8）。** **[已核验]**（Crossref：PNAS 108:11375–11380, 2011）
50. `[V-元]` Zefferman, M.R. & Mathew, S. (2015). "An evolutionary theory of large-scale human warfare: Group-structured cultural selection." *Evolutionary Anthropology* 24:50–61. DOI `10.1002/evan.21439`.
51. `[V-元]` Bowles, S. (2009). "Did Warfare Among Ancestral Hunter-Gatherers Affect the Evolution of Human Social Behaviors?" *Science* 324:1293–1298. DOI `10.1126/science.1168112`. **数值未取得。**
52. `[V-全文]` **Gavrilets, S. & Richerson, P.J. (2017). "Collective action and the evolution of social norm internalization." *PNAS* 114:6068–6073. DOI `10.1073/pnas.1703857114`, PMC5468620. ← M1/M2/M13 的函数形式来源（§2.11 / §4.5）。** **[已核验]**（Crossref：PNAS 114:6068–6073, 2017）
53. `[V-元]` Boyd, R. & Richerson, P.J. (2005). *The Origin and Evolution of Cultures*. Oxford. DOI `10.1093/oso/9780195165241`（含 "The Evolution of Altruistic Punishment" 章，pp.241–250, DOI `10.1093/oso/9780195165241.003.0014`）。
54. `[V-元]` Richerson, P.J., Boyd, R. & Henrich, J. (2003). "Cultural Evolution of Human Cooperation." in *Genetic and Cultural Evolution of Cooperation*, pp.357–388. DOI `10.7551/mitpress/3232.003.0021`.
55. `[V-摘]` Henrich, J., Boyd, R., Bowles, S., Camerer, C., Fehr, E., Gintis, H., McElreath, R., Alvard, M., Barr, A., Ensminger, J., Henrich, N., Hill, K., Gil-White, F., Gurven, M., Marlowe, F.W., Patton, J.Q. & Tracer, D. (2005). "'Economic man' in cross-cultural perspective: Behavioral experiments in 15 small-scale societies." *BBS* 28:795–815. DOI `10.1017/s0140525x05000142`. **各社会具体数值未取得**（Cambridge 页面只返回摘要）。 **[已核验]**（Crossref：*BBS* 28:795–815, 2005）
56. `[V-元]` Hill, K.R., Walker, R.S., Božičević, M., Eder, J., Headland, T., Hewlett, B., Hurtado, A.M., Marlowe, F., Wiessner, P. & Wood, B. (2011). "Co-Residence Patterns in Hunter-Gatherer Societies Show Unique Human Social Structure." *Science* 331:1286–1289. DOI `10.1126/science.1199071`. **数值未取得。**
57. `[V-元]` Traulsen, A. & Nowak, M.A. (2007). "Chromodynamics of Cooperation in Finite Populations." *PLoS ONE* 2:e270. DOI `10.1371/journal.pone.0000270`.
58. `[未核验]` Boyd, R. & Richerson, P.J. (1985) *Culture and the Evolutionary Process*；Boyd & Richerson (1988) "The evolution of reciprocity in sizable groups"；Bowles, S. & Gintis, H. (2011) *A Cooperative Species*；Henrich, J. (2004) "Cultural group selection, coevolutionary processes and large-scale cooperation"；Turchin, P. (2016) *Ultrasociety*；Smaldino, P.E. (2014) "The cultural evolution of emergent group-level traits"。

### 10.5 组织规模、层级与从平等到专制

59. `[V-全文]` **Zhou, W.-X., Sornette, D., Hill, R.A. & Dunbar, R. (2005). "Discrete hierarchical organization of social group sizes." *Proc. R. Soc. B* 272:439–444. DOI `10.1098/rspb.2004.2970`, PMC1634986. ← 层级规模与 λ≈3.2（§4.3）。** **[已核验]**（Crossref：Proc. R. Soc. B 272:439–444, 2005）
60. `[V-全文]` **Powers, S.T. & Lehmann, L. (2014). "An evolutionary model explaining the Neolithic transition from egalitarianism to leadership and despotism." *Proc. R. Soc. B* 281:20141349. DOI `10.1098/rspb.2014.1349`, PMC4132689. ← 退出成本→专制程度（§2.10 / §4.4）。** **[已核验]**（Crossref：Proc. R. Soc. B 281:20141349, 2014）
61. `[V-全文]` **Powers, S.T., van Schaik, C.P. & Lehmann, L. (2016). "How institutions shaped the last major evolutionary transition to large-scale human societies." *Phil. Trans. R. Soc. B* 371:20150098. DOI `10.1098/rstb.2015.0098`, PMC4760198. ← "制度 = 决定博弈形式的机制" + 两阶段结构（M19 的依据）。** **[已核验]**（Crossref：Phil. Trans. R. Soc. B 371:20150098, 2016，三作者相符）
62. `[V-元]` Van Vugt, M. (2009). "Despotism, democracy, and the evolutionary dynamics of leadership and followership." *American Psychologist* 64:54–56. DOI `10.1037/a0014178`.
63. `[V-元]` Carneiro, R.L. (1970). "A Theory of the Origin of the State." *Science* 169:733–738. DOI `10.1126/science.169.3947.733`.
64. `[V-元]` Blanton, R. & Fargher, L. (2008). *Collective Action in the Formation of Pre-Modern States*. Springer (Fundamental Issues in Archaeology). DOI `10.1007/978-0-387-73877-2`. **编码数值未取得。** 另：Blanton & Fargher (2011) "The collective logic of pre-modern cities." *World Archaeology* 43:505–522, DOI `10.1080/00438243.2011.607722`；Blanton & Fargher (2016) "Cooperation in State-Building?" in *How Humans Cooperate*, pp.115–158, DOI `10.5876/9781607325147.c008`.
65. `[V-元]` Turchin, P. & Gavrilets, S. (2009). "Evolution of complex hierarchical societies." OpenAlex 有记录（vol. 8），**期刊与 DOI 未返回 → 弱核验**。
66. `[未核验]` Johnson, G.A. (1982) "Organizational structure and scalar stress"；Dunbar, R. (1993) "Coevolution of neocortical size, group size and language in humans"；Flannery, K. & Marcus, J. *The Creation of Inequality*；Levi, M. (1988) *Of Rule and Revenue*。

### 10.6 制度、承诺装置与国家

67. `[V-元]` North, D.C. & Weingast, B.R. (1989). "Constitutions and Commitment: The Evolution of Institutions Governing Public Choice in Seventeenth-Century England." *Journal of Economic History* 49:803–832. DOI `10.1017/s0022050700009451`. **[已核验]**（Crossref 刊名全称 *The Journal of Economic History*）
68. `[V-元]` Greif, A., Milgrom, P. & Weingast, B.R. (1994). "Coordination, Commitment, and Enforcement: The Case of the Merchant Guild." *Journal of Political Economy* 102:745–776. DOI `10.1086/261953`. **[已核验]**
69. `[V-元]` Greif, A. (1993). "Contract enforceability and economic institutions in early trade: The Maghribi Traders' Coalition." *American Economic Review* 83:525–548.（OpenAlex 记录无 DOI）
70. `[V-元]` Greif, A. (2008). "Contract Enforcement and Institutions Among the Maghribi Traders: Refuting Edwards and Ogilvie." SSRN. DOI `10.2139/ssrn.1159681`.（争议存在的证据）
71. `[V-元]` Milgrom, P., North, D. & Weingast, B. "The Role of Institutions in the Revival of Trade: The Law Merchant, Private Judges, and the Champagne Fairs."（本次核验到 2017 年重印记录，*Anarchy And the Law* pp.602–623, DOI `10.4324/9781315082349-37`；**原发表记录未核验**）
72. `[V-元 / 间接]` North, D.C., Wallis, J.J. & Weingast, B.R. (2009). *Violence and Social Orders*. Cambridge University Press. **本次只核验到书评与章节记录**（Choice Reviews Online DOI `10.5860/choice.47-2898`；ORDO DOI `10.1515/ordo-2009-0143`）；**CUP 原书记录未直接核验**。按 B 级 / 定性理论使用。
73. `[V-元]` Rosenthal, J.-L., Weingast, B.R., Greif, A. & Levi, M. (1999). *Analytic Narratives*. DOI `10.1515/9780691216232`.
74. `[V-元]` Elster, J. (1989). "Social Norms and Economic Theory." *JEP* 3:99–117. DOI `10.1257/jep.3.4.99`.
75. `[未核验]` Greif, A. (2006) *Institutions and the Path to the Modern Economy*；Greif, A. 关于 **community responsibility system** 的论文（Chicago Journal of International Law 一类）。**§2.14 与 §6.5 已明确标注该缺口。**

### 10.7 千年尺度模拟与社会复杂度

76. `[V-全文]` **Turchin, P., Currie, T.E., Turner, E.A.L. & Gavrilets, S. (2013). "War, space, and the evolution of Old World complex societies." *PNAS* 110:16384–16389. DOI `10.1073/pnas.1308825110`, PMC3799307. ← 架构与 R² 消融（§2.9 / §4.10）。** **[已核验]**（Crossref：PNAS 110:16384–16389, 2013） OA 副本（未打开）：`http://hdl.handle.net/10871/31320`。
77. `[V-全文]` **Turchin, P., Currie, T.E., Whitehouse, H., François, P., Feeney, K., Mullins, D., Hoyer, D., Collins, C., ... Spencer, C. (2017/2018). "Quantitative historical analysis uncovers a single dimension of complexity that structures global variation in human social organization." *PNAS* 115. DOI `10.1073/pnas.1708800115`, PMC5777031. ← Seshat：414 政体 / 30 NGA / 9 CC / PC1 = 77.2 ± 0.4%（§4.11）。**
78. `[V-元]` Currie, T.E., Greenhill, S.J., Gray, R.D., Hasegawa, T. & Mace, R. (2010). "Rise and fall of political complexity in island South-East Asia and the Pacific." *Nature* 467:801–804. DOI `10.1038/nature09461`.
79. `[V-元]` Turchin, P. (2013). "The Puzzle of Human Ultrasociality: How Did Large-Scale Complex Societies Evolve?" in *Cultural Evolution*, pp.61–74. DOI `10.7551/mitpress/9894.003.0007`.
80. `[V-元]` Turchin, P. (2025). "Bayesian phylogenetic analyses cannot be used to test hypotheses about the evolution of large-scale complex societies during the Holocene." 预印本, DOI `10.31235/osf.io/xenpv_v1`.（方法论争议持续的证据）

### 10.8 宗教、道德神与撤稿争议

81. `[V-元]` **Whitehouse, H., François, P., Savage, P.E., Currie, T.E., Feeney, K., Cioni, E., Purcell, R., Ross, R.M., Larson, J., Baines, J., ter Haar, B., Covey, A. & Turchin, P. (2019). "Complex societies precede moralizing gods throughout world history." *Nature* 568:226–229. DOI `10.1038/s41586-019-1043-4`. ⚠️ 已撤稿。** **[已核验]**（Crossref 题名即标注 RETRACTED ARTICLE，*Nature* 568:226–229, 2019）
82. `[V-元]` **撤稿声明**：Nature 595:320 (2021). DOI `10.1038/s41586-021-03656-3`. **[已核验]**
83. `[V-元]` **Beheim, B., Atkinson, Q.D., Bulbulia, J., Gervais, W.M., Gray, R.D., Henrich, J., Lang, M., Monroe, M.W., Muthukrishna, M., Norenzayan, A., Purzycki, B.G., Shariff, A., Slingerland, E., Spicer, R. & Willard, A.K. (2021). "Treatment of missing data determined conclusions regarding moralizing gods." *Nature* 595:E29–E34. DOI `10.1038/s41586-021-03655-4`.** **[已核验]**
84. `[V-元]` Slingerland, E., Monroe, M.W., Sullivan, B., Walsh, R.F., Veidlinger, D., Noseworthy, W.B., Herriott, C., Raffield, B., Peterson, J.L., Rodríguez, G., Sonik, K., Green, W.H., Tappenden, F.S., Ashtari, A., Muthukrishna, M. & Spicer, R. (2020). "Historians Respond to Whitehouse et al. (2019)." *Journal of Cognitive Historiography* 5:124–141. DOI `10.1558/jch.39393`. OA PDF（未打开）：`https://researchonline.lse.ac.uk/id/eprint/107612/1/Historians_Respond_to_Whitehouse_et_al_complete.pdf`.
85. `[V-元]` Purzycki, B.G., Apicella, C.L., Atkinson, Q.D. et al. (2016). "Moralistic gods, supernatural punishment and the expansion of human sociality." *Nature*. DOI `10.1038/nature16980`. **数值未取得。**
86. `[V-元]` Norenzayan, A., Shariff, A.F., Gervais, W.M., Willard, A.K., McNamara, R.A., Slingerland, E. & Henrich, J. (2016). "The cultural evolution of prosocial religions." *BBS* 39:e1. DOI `10.1017/s0140525x14001356`.
87. `[V-元]` Cox, M., Villamayor-Tomas, S. & Hartberg, Y. (2014). "The Role of Religion in Community-based Natural Resource Management." *World Development* 54:46–55. DOI `10.1016/j.worlddev.2013.07.010`.

### 10.9 灌溉、水利与 Wittfogel 争议

88. `[V-元]` Hunt, R.C., Hunt, E.K., Ahmed, G., Bennett, J.W., Cleek, R.K., Coy, P., Glick, T.F., Lewis, R.E., MacLachlan, B.B., Mitchell, W.P., Partridge, W.L., Price, B.J., Roder, W., Steensberg, A., Wade, R. & Wellmann, I. (1976). "Canal Irrigation and Local Social Organization [and Comments and Reply]." *Current Anthropology* 17:389–411. DOI `10.1086/201755`.
89. `[V-元]` Lansing, J.S. & Kremer, J.N. (1993). "Emergent Properties of Balinese Water Temple Networks: Coadaptation on a Rugged Fitness Landscape." *American Anthropologist* 95:97–114. DOI `10.1525/aa.1993.95.1.02a00050`. 另：(1995) "A Socioecological Analysis of Balinese Water Temples", DOI `10.3362/9781780444734.019`.
90. `[V-元]` Lansing, J.S., Cox, M.P., Downey, S.S., Janssen, M.A. & Schoenfelder, J.W. (2009). "A robust budding model of Balinese water temple networks." *World Archaeology* 41:112–133. DOI `10.1080/00438240802668198`.
91. `[V-元]` Sarker, A. & Itoh, T. (2001). "Design principles in long-enduring institutions of Japanese irrigation common-pool resources." *Agricultural Water Management* 48:89–102. DOI `10.1016/s0378-3774(00)00125-6`. **数值未取得。**
92. `[V-元]` Wang, Y. & Wu, J. (2018). "An Empirical Examination on the Role of Water User Associations for Irrigation Management in Rural China." *Water Resources Research* 54:9791–9811. DOI `10.1029/2017wr021837`. **数值未取得。**
93. `[V-元]` Bentzen, J., Kaarsen, N. & Wingender, A.M. (2016). "Irrigation and Autocracy." *Journal of the European Economic Association*. DOI `10.1111/jeea.12173`. **封闭，系数未取得**（OpenAlex 确认无 OA 副本）。
94. `[V-元]` Çifdalöz, O., Regmi, A.R., Anderies, J.M. & Rodriguez, A.A. (2010). "Robustness, vulnerability, and adaptive capacity in small-scale social-ecological systems: The Pumpa Irrigation System in Nepal." *Ecology and Society* 15(3):39. DOI `10.5751/es-03462-150339`. OA PDF（未打开）：`http://www.ecologyandsociety.org/vol15/iss3/art39/ES-2010-3462.pdf`.
95. `[V-元]` Thapa, B., Scott, C.A., Wester, P. & Varady, R.G. (2016). "Towards characterizing the adaptive capacity of farmer-managed irrigation systems: learnings from Nepal." *Current Opinion in Environmental Sustainability*. DOI `10.1016/j.cosust.2016.10.005`.
96. `[V-元]` Wittfogel, K.A. (1957). *Oriental Despotism: A Comparative Study of Total Power*. Yale University Press. **[已核验]**（未找到该书本身的 DOI，但 Crossref 命中 1957–1958 年三条针对该书的书评记录——*Books Abroad*、*Russian Review* 17(2)、*Geographical Review* 48(2)——书名、作者、年份相符）。全文仍未读取，§2.19 的"只用被批评形式陈述"限制继续有效。

### 10.10 中国与东亚

97. `[V-元]` Greif, A. & Tabellini, G. (2017). "The clan and the corporation: Sustaining cooperation in China and Europe." *Journal of Comparative Economics* 45:1–35. DOI `10.1016/j.jce.2016.12.003`. **全文未取得。** **[已核验]**（Crossref：*J. Comparative Economics* 45:1–35, 2017） 早期版本：SSRN DOI `10.2139/ssrn.2565120`、`10.2139/ssrn.2576644`、`10.2139/ssrn.2101460`（"The Clan and the City", 2012）。
98. `[V-元]` Xu, Y. & Yao, Y. (2015). "Informal Institutions, Collective Action, and Public Investment in Rural China." *American Political Science Review* 109:371–391. DOI `10.1017/s0003055415000155`. **封闭，数值未取得。**
99. `[V-摘]` **Sng, T.-H. & Moriguchi, C. (2014). "Asia's little divergence: state capacity in China and Japan before 1850." *Journal of Economic Growth* 19:439–470. DOI `10.1007/s10887-014-9108-6`. ← §4.12 的定性约束来源（摘要级；全文被 Springer 登录墙挡住）。** **[已核验]**（Crossref：*J. of Economic Growth* 19:439–470, 2014；书目正确，但全文数值仍未取得）
100. `[V-元]` Sng, T.-H. (2014). "Size and dynastic decline: The principal-agent problem in late imperial China, 1700–1850." *Explorations in Economic History* 54:107–127. DOI `10.1016/j.eeh.2014.05.002`. **封闭，数值未取得。**
101. `[V-元]` Xue, M.M. & Koyama, M. (2018). "Autocratic Rule and Social Capital: Evidence from Imperial China." SSRN. DOI `10.2139/ssrn.2856803`. **数值未取得。**
102. `[V-元]` Xu, C. (2011). "The Fundamental Institutions of China's Reforms and Development." *Journal of Economic Literature* 49:1076–1151. DOI `10.1257/jel.49.4.1076`. OA PDF（未打开）：`http://hub.hku.hk/bitstream/10722/153452/2/Content.pdf`.
103. `[V-元]` Skinner, G.W. (2002). "Marketing and social structure in rural China." *Études rurales* 161–162. DOI `10.4000/etudesrurales.7952`.（法文重印记录；**PDF 下载被拒，内容未取得**；原 1964–65 *Journal of Asian Studies* 连载未核验）
104. `[V-元]` Bol, P.K. (2003). "The 'Localist Turn' and 'Local Identity' in Later Imperial China." *Late Imperial China* 24:1–50. DOI `10.1353/late.2004.0002`.
105. `[V-元]` Pfautsch, A. (2025). "Village Compact: Law and Local Governance in Late Imperial China." *Zeitschrift für Chinesisches Recht* 32:297–298. DOI `10.71163/zchinr.2025.297-298`.（2 页记录，疑为书评；**内容未取得**）
106. `[V-元]` Yu, X. (2022). "Local Politics and Book Production: The Popularization of Genealogies in Southern China, 1750s–1920s." *Late Imperial China* 43:43–88. DOI `10.1353/late.2022.0011`.
107. `[V-元]` Rawski, T.G. & Li, L.M. (2024). *Chinese History in Economic Perspective*. DOI `10.2307/jj.15306398`. OA（未打开）：`https://works.swarthmore.edu/fac-history/168`.
108. `[未核验]` Freedman, M. *Lineage Organization in Southeastern China*；Faure, D. *Emperor and Ancestor*；Will, P.-É. & Wong, R.B. *Nourish the People*；Perdue, P. *Exhausting the Earth*；Elvin, M. 关于水利的论文；Zhang, L. (2016) *The River, the Plain, and the State*；Duara, P. *Culture, Power, and the State*；Kiser, E. & Tong, X. (1992) 关于晚期帝制中国官僚腐败的论文；Tsai, L. (2007) *Accountability without Democracy*。**以上全部本次未核验，§6.5 已把东亚连带责任制度列为最大缺口。**

---

## 检索覆盖说明（诚实报告）

**做了什么**：
- WebSearch **完全不可用** —— 本任务开始时该会话已用满 200/200 次检索配额，第一次与最后一次尝试均返回 "web search budget exhausted"。因此我**没有做基于搜索引擎的探索性检索**。
- 改用三条 API 与开放全文渠道，全部为真实网络请求：
  - **Crossref REST API**（`api.crossref.org/works?query.bibliographic=...`）：约 12 次成功查询，用于书目元数据核验。中途多次 429 限流，改为串行。
  - **OpenAlex API**（`api.openalex.org/works?...`）：约 14 次成功查询，用于元数据 + OA 位置 + 摘要倒排索引。**最终配额耗尽（429，Retry-After ≈ 39,000 秒）**，因此最后几条计划中的核验（Guzmán et al. 2007、Dreber et al. 2008、Holmström 1982）未能完成。
  - **PMC**（`pmc.ncbi.nlm.nih.gov`）：DOI→PMCID 转换 API 用了 4 次；**成功读取 10 篇全文**（PMC152327、PMC1544155、PMC1634986、PMC3136302、PMC3228461、PMC3279745、PMC3420198、PMC3799307、PMC4132689、PMC4760198、PMC5468620、PMC5777031、PMC7000669）。**本简报几乎所有硬数字来自这些全文。**
  - 开放期刊站点：`thecommonsjournal.org` 成功读取 Baggio et al. (2016) 全文。

**哪里检索不足**：
1. **没有探索性检索** —— 我只能核验我事先知道要找什么的文献。**这意味着本简报可能漏掉了近 2–3 年的重要新工作**，尤其是 2024–2026 年的文献（我的知识截止为 2026 年 5 月，但没有搜索能力去发现新东西）。
2. **东亚特定证据严重不足** —— Crossref 对中文主题的英文关键词检索命中率低，而我无法用 WebSearch 探索。**保甲/里甲/连坐/乡约、宗族族产与公共品、明清水利组织的量化研究，本次基本没有获得**（只找到一条 2 页的书评记录）。§6.5 已明确标注这是最大缺口。
3. **实验经济学的具体参数几乎全部缺失** —— Fehr & Gächter、Herrmann et al.、Gürerk et al.、Gächter et al.、Balliet et al. 全部封闭获取且无可用 OA 副本。我**拒绝**用记忆中的数值填补（§4.13 逐条列出了缺口）。

**付费墙挡住了什么**（全部为本次实际遭遇的 403 / 登录跳转 / OpenAlex 确认无 OA）：
- `pnas.org` 直接访问 403（改走 PMC 成功）
- `nature.com` 的 PDF 跳转到 `idp.nature.com` 登录（撤稿声明与 Beheim et al. 全文未取得；但标题与卷页已足够支撑 §7.6 的结论）
- `link.springer.com` 跳转到 `idp.springer.com` 登录（Sng & Moriguchi 全文未取得，只有摘要）
- `royalsocietypublishing.org` PDF 403（改走 PMC 成功）
- `ecologyandsociety.org` 403（Cox et al. 2010 未取得 —— 这是一个真实损失，因为它是 DP 逐条支持计数的主要来源）
- `repositorio.utp.edu.co` 返回 BunkerWeb 机器人检测页（Ostrom 2009 Science 的 OA 副本未取得）
- `dlc.dlib.indiana.edu` 403
- `papers.ssrn.com` ECONNRESET（Ostrom 2010 全文未取得）
- `journals.openedition.org` ECONNREFUSED（Skinner 全文未取得）
- `cambridge.org` 的 PDF 只返回摘要（Henrich et al. 2005 各社会数值未取得）
- `wikipedia.org` 检索页 ETIMEDOUT（本来也只打算用它找线索）

**建议下一阶段补做的三件事**：
1. 用可用的 WebSearch 配额专项检索东亚连带责任与宗族公共品的量化研究（§6.5）。
2. 取得 Cox et al. (2010) 与 Ostrom (2009) 的全文，补齐 DP 的逐条支持计数与 SES 框架的完整变量清单。
3. 取得 Fehr & Gächter (2000/2002) 与 Herrmann et al. (2008) 的参数，填上 §4.13 的实验参数缺口 —— 或者明确决定**不使用实验室参数**，全部改用 Boyd et al. (2003) 的文化演化参数（§反模式 12 的建议）。
