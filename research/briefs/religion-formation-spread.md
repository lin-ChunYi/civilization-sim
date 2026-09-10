# 宗教的形成、组织化与传播（religion-formation-spread）

**slug**: `religion-formation-spread`
**一句话范围**：本简报处理"超自然信念如何从认知默认值中持续产生 → 如何被仪式与代价信号锁定为群体边界 → 如何组织化为有经济基础的机构 → 如何跨聚落传播、分裂与被国家收编"，目标是给出可计算的机制、可选函数形式、参数量级，以及"宗教诞生"这件事如何由结构条件触发而非由 LLM 决定。
**检索日期**：2026-09-10。**验证方式**：Crossref REST API、OpenAlex、Europe PMC、Unpaywall、PMC/JASSS/NBER 全文抓取。凡标注"本次未验证"者为记忆写入，须由下一阶段核验。

---

## 0. 给赶时间的读者：本简报的六个硬结论

1. **宗教不是一个"要不要发明"的事件，而是一个始终开着的低强度过程。** 认知宗教学的共识是：超自然主体表征是人类心智默认配置（agency detection、目的论偏误、最小反直觉概念）的副产品。因此模拟里不应该有"某年某人发明了宗教"这个 tick。应该有的是：**归因压力**这个连续场，以及若干个把弥散归因**组织化**为机构的阈值事件。
2. **"大神导致大社会"这条因果链在 2021 年被公开否定过一次，必须如实呈现。** Whitehouse et al. 2019 *Nature* 那篇"复杂社会先于道德神"的论文已于 2021-07-07 **正式撤稿**（Retraction Note: *Nature* 595:320）。撤稿的直接原因是 Beheim et al. (2021) 指出其 61%（n=490）的道德神数据点是缺失值，被作者重编码为"确知不存在"，缺失与"不存在"的相关达 r = 0.97。这是本项目必须内化的一条**建模纪律**：缺失 ≠ 不存在。
3. **撤稿之后，学界并没有回到"大神导致大社会"。** Turchin et al. (2023, *Religion, Brain & Behavior* 13:167–194) 用同一个 Seshat 数据重做，结论是：**群体间战争（由资源可得性支撑）同时驱动了社会复杂度与道德化宗教**，两者的相关来自共同驱动因子，而非彼此的直接因果。Lightner, Bendixen & Purzycki (2023) 进一步指出，跨文化数据里"道德化高神"这个变量本身系统性地在小规模社会产生假阴性。**因此模拟内核不得把"人口超过 X → 解锁道德神"写成规则。**
4. **目前唯一一个可以直接抄进代码的、带完整系数的跨文化宗教预测模型是 Botero et al. (2014, PNAS)**：n = 583 社会，logit 模型，AUC = 0.91。其中**空间邻近（邻居信念均值）的系数 5.867 远大于其余所有项之和**——也就是说，在真实世界数据里，一个社会信什么，最强的预测因子是它的邻居信什么。传播项必须是模拟里最强的项。
5. **仪式的两个维度（频率、唤起度）不是一个轴。** Atkinson & Whitehouse (2011) 在 651 个仪式 / 74 个文化群里得到频率与唤起度 ρ = −0.40（dysphoric ρ = −0.41，euphoric ρ = −0.08）；Kapitány et al. (2020) 重做因子分析发现 **dysphoric 与 euphoric 基本正交**，共 7 个因子。所以仪式状态至少需要三个独立标量：频率、痛苦强度、欢愉强度。
6. **宗教组织的存续和分裂是可以用俱乐部品经济学算的，而且有一个已验证的形式化版本。** Berman (QJE 2000 / NBER WP6715) 对 Iannaccone (1992) 模型的形式化：成员效用 U(S, R, Q)，Q 是群体内其他成员的平均宗教时间投入（外部性），预算约束 wT = pS + wR。竞争均衡下 R 供给不足；**禁令的作用是对"世俗时间的替代用途"征税**，从而抬高 R 与 Q。这直接给出"严格教派为什么强"的可计算解释，以及"补贴 → 劳动供给崩塌 + 生育率飙升"的可检验推论（以色列极端正统派 TFR = 7.6）。

---

## 1. 本简报要回答的问题

针对 MANDATE 的 Phase 0 关键问题，本领域需要回答：

- **世界最底层必须有哪些与宗教相关的状态？** → 见 §3.0 与 §3.1（最小宗教状态定义）。
- **哪些变化由数学/规则决定，哪些交给 LLM？** → 宗教的**存在、强度、组织形态、经济收支、边界规则、分裂与否**全部由规则决定；LLM 只负责**内容**（神叫什么、神话讲什么、禁忌具体禁什么、经文怎么写、异端如何被指控）。见 §3 每条机制的 `belongs_to`。
- **如何产生真正的涌现，而不是隐藏的剧情树？** → 不设"宗教科技树"。设**归因压力场 + 若干门槛条件**，门槛满足则组织形态发生相变；不满足则退化。见 §3.2–§3.9。
- **如何保存因果关系？** → 每个宗教对象携带 `founding_conditions` 快照（触发时的 A、surplus、free-rider 压力、邻居信念场值、具体触发事件 id），任何后世追问都能回到这组数。
- **如何处理拿不到参数的问题？** → §4 明确区分"有文献系数"（Botero 的 logit、Berman 的效用结构、Kapitány 的相关系数、Shults 的 Rescorla-Wagner 参数）与"文献未提供可用参数"（大量）。后者一律走 §9 的 D 级假设通道，并要求写成可调开关。
- **如何防止模型为了戏剧性制造事件？** → §3.10 的"宗教诞生守门人"：LLM 不能创建 `Religion` 对象，只能给已由规则实例化的空壳填内容。

---

## 2. 已有成熟模型与理论

### 2.1 认知宗教学：为什么超自然表征总是存在

| 项 | 内容 |
|---|---|
| **核心机制** | (a) **HADD / agency detection**：面对模糊刺激优先假设"有意图的行动者"，因为假阳性代价远低于假阴性（Guthrie 1993；Barrett 2000）。(b) **最小反直觉概念（MCI）**：违反 1–2 条本体论直觉的概念（会说话的树、无形却能听的人）在记忆与传递中占优；违反过多则崩溃（Boyer & Ramble 2001；Norenzayan et al. 2006）。(c) **拟人化的神概念在在线推理中比神学正确表述更"人形"**（Barrett & Keil 1996）。 |
| **形式化程度** | 半形式化。有实验效应，无跨代传递的封闭方程。 |
| **状态变量** | 每个超自然主体：`ontological_template`（PERSON / ANIMAL / PLANT / ARTIFACT / NATURAL_OBJECT）+ `violations`（对该模板的属性违反集合，计数 k）。 |
| **参数** | Boyer & Ramble 2001 报告跨文化（法国、加蓬、尼泊尔）MCI 项目的回忆优势；Norenzayan et al. 2006 在叙事层面复现，并给出"MCI 数量存在最优值"的结论。**具体的最优违反数与回忆率数值本次未从原文抓取**（论文非 OA），只验证了篇目与结论方向。 |
| **适用范围** | 神概念的产生与最初传播；不适用于解释组织化。 |
| **已知局限** | MCI 效应量在后续复制中不稳定，且"最优 k=2"的说法在文献中被反复讨论（Upal 2022 的综述章节存在，DOI 10.4324/b23047-9，内容本次未读）。副产品说与适应说之争未决（Pyysiäinen & Hauser 2010 TiCS 14:104–109）。 |
| **出处** | Boyer & Ramble 2001, *Cognitive Science* 25:535–564, DOI 10.1207/s15516709cog2504_2（已验证）；Norenzayan, Atran, Faulkner & Schaller 2006, *Cognitive Science* 30:531–553, DOI 10.1207/s15516709cog0000_68（已验证）；Barrett 2000, *TiCS* 4:29–34, DOI 10.1016/S1364-6613(99)01419-9（已验证）；Barrett & Keil 1996, *Cognitive Psychology* 31:219–247, DOI 10.1006/cogp.1996.0017（已验证）。 |

**对本项目的意义**：这一层的产物是"**宗教不需要被发明**"。模拟里每个人 agent 天生带 HADD 参数，因此每个聚落在任何时刻都有非零的超自然归因。要建模的是**从弥散归因到机构**的相变，不是"从无到有"。

### 2.2 萨满教的文化演化（Singh 2018）—— 前文明期最重要的一条

| 项 | 内容 |
|---|---|
| **核心机制** | 萨满是"第一个职业"（超出年龄/性别分工的第一个制度化分工）。其存在条件是：存在**重要但不可预测**的结果（病、猎获、天气、战争）。萨满通过**在入会与出神中"变形"**（违反人性直觉）来使旁观者相信他能影响这些结果。关键洞见：**入会门槛之所以长期存在，是因为从业者的可信度依赖于"他确实变过形"**；这与"造独木舟"这类有可验证结果的职业相反——后者的辖区（jurisdiction）会被任何能做出成品的外人侵入。 |
| **形式化程度** | 定性理论 + 跨文化归纳，无方程。 |
| **状态变量** | `uncertainty_of_domain`（领域结果的不可预测性）、`stakes`（结果的重要性）、`initiation_cost`、`transformation_credibility`。 |
| **参数** | 文献未提供可用的数值参数。 |
| **适用范围** | 采集狩猎—早期农业段的宗教专业化；解释为什么在没有任何其他专业分工时就已经有宗教专家。 |
| **已知局限** | BBS 目标文章格式，附大量同行评论；理论的可证伪性受质疑。 |
| **出处** | Singh 2018, *Behavioral and Brain Sciences* 41, DOI 10.1017/S0140525X17001893（摘要已通过 Europe PMC 验证）。相关：Singh 2021, *Current Anthropology* 62:2–29, DOI 10.1086/713111（巫术/女巫信念的三重文化选择：直觉性魔法、对重大不幸的可信解释、为迫害辩护的妖魔化神话；摘要已验证）。 |

**对本项目的意义**：这给了"宗教专家"出现的**结构触发条件**，且这个条件在前文明期就能满足。同时 Singh 2021 给了"异端/女巫指控"的生成条件，可直接接到 §3.9 的迫害机制。

### 2.3 代价信号 / CREDs：仪式为什么必须"浪费"

| 项 | 内容 |
|---|---|
| **核心机制** | (a) **代价信号（costly signaling）**：难以伪造的高成本行为筛选出真承诺者，降低搭便车（Sosis & Alcorta 2003）。(b) **CREDs（credibility enhancing displays）**：学习者不是根据别人说什么、而是根据别人**为信念付出了什么**来更新自己的信念；这使得代价行为同时是**筛选器**和**传播器**（Henrich 2009）。(c) **共享痛苦经验 → 身份融合（identity fusion）→ 极端自我牺牲**（Whitehouse & Lanman 2014；Whitehouse et al. 2017）。 |
| **形式化程度** | Whitehouse et al. 2017 **有完整数学模型**（Gavrilets 参与）：个体收益 `f_ij = 1 + b·P_j − c·z_ij`，其中 `z_ij` 为个体对集体行动的投入、`Z_j = Σ z_ij`、`P_j = P_j(Z_j) ∈ [0,1]` 为归一化的集体行动成功度、b 与 c 为收益/成本常数；群体存活概率 `S_j = h·E_j + (1−h)·P_j`，`h ∈ [0,1]` 为"过往共享经验"对群体存活的权重，`E_j ∈ {0,1}` 表示该群体过往经验为 euphoric(1) 还是 dysphoric(0)；比例 π 的群体有 euphoric 经历，1−π 有 dysphoric 经历。个体演化出两套条件策略：euphoric 者投入 x，dysphoric 者投入 y。（全文已抓取验证。） |
| **状态变量** | `ritual.cost_time/goods/body`、`ritual.dysphoria`、`agent.fusion[group]`、`group.shared_dysphoric_history`。 |
| **参数** | Whitehouse et al. 2017 明言"我们不知道若干关键参数的现实取值"。实验侧：美国样本 N=97（自然灾害）/ N=98（恐袭），共享自我定义经验与融合 r = 0.239 (P=0.001)，日常经验 r = 0.187 (P=0.009)；N=122 的极端自我牺牲意愿研究。 |
| **适用范围** | 小群体的高承诺、军事动员、殉教、教派存续。 |
| **已知局限** | 代价信号理论的核心实证（Sosis & Bressler 2003 的公社存续分析）**本次检索未能取得其数值结果**（Sage 付费墙）。我只验证了篇目：Sosis & Bressler 2003, *Cross-Cultural Research* 37(2):211–239, DOI 10.1177/1069397103037002003。**该文常被引用的"宗教公社比世俗公社显著更长寿、且代价性要求数量只在宗教公社中预测存续"这一结论，属于我的记忆，本次未验证。** |
| **出处** | Henrich 2009, *Evolution and Human Behavior* 30:244–260, DOI 10.1016/j.evolhumbehav.2009.03.005（已验证）；Sosis & Alcorta 2003, *Evolutionary Anthropology* 12:264–274, DOI 10.1002/evan.10120（已验证）；Sosis & Ruffle 2003, *Current Anthropology* 44:713–722, DOI 10.1086/379260（已验证）；Sosis, Kress & Boster 2007, *EHB* 28:234–247, DOI 10.1016/j.evolhumbehav.2007.02.007（已验证）；Whitehouse & Lanman 2014, *Current Anthropology* 55:674–695, DOI 10.1086/678698（已验证）；Whitehouse et al. 2017, *Scientific Reports* 7:44292, DOI 10.1038/srep44292（全文已验证）；Lanman & Buhrmester 2017, *RBB* 7:3–16, DOI 10.1080/2153599X.2015.1117011（已验证）；Bulbulia & Sosis 2011, *Religion* 41:363–388, DOI 10.1080/0048721X.2011.604508（已验证）。 |

### 2.4 Whitehouse 的 modes of religiosity（doctrinal vs. imagistic）

| 项 | 内容 |
|---|---|
| **核心机制** | 仪式在"频率 × 情绪唤起"平面上有两个吸引子。**Doctrinal 模式**：高频、低唤起、语义记忆、需要权威与正典、支持大规模匿名共同体，但有"厌倦效应（tedium effect）"。**Imagistic 模式**：低频、高唤起（尤其 dysphoric）、情节记忆、产生强烈但局部的身份融合，难以规模化。 |
| **形式化程度** | 原书为定性理论；Atkinson & Whitehouse 2011 把它变成了可测量的**形态空间（morphospace）**。 |
| **状态变量** | `ritual.frequency`（每年次数，从每日到每代一次）、`ritual.dysphoria`、`ritual.euphoria`。 |
| **参数（已验证）** | 651 个仪式 / 74 个文化群，102 个二值变量。频率与"唤起度"负相关 **ρ = −0.40**；对 dysphoric 为 **ρ = −0.41**，对 euphoric 仅 **ρ = −0.08**。Kapitány et al. 2020 的重做得到 **7 个因子**：Dysphoric elements、Euphoric elements、Pageantry–physical、Viscera、Pageantry–psychological、Frequency、Kin；**dysphoric 与 euphoric 维度基本正交**。当代样本 779 人（日本、印度、美国）复现四个正交维度（euphoric / dysphoric / frequency / cognitive）。 |
| **适用范围** | 仪式库的生成与组织形态的耦合。 |
| **已知局限** | 二分法被 2020 年的重分析实质性削弱——**不存在单一"唤起度"轴**。"两个模式"更像连续形态空间上的两片高密度区域，而不是两个类型。 |
| **出处** | Whitehouse 2004, *Modes of Religiosity: A Cognitive Theory of Religious Transmission*, AltaMira Press（经由三篇书评验证存在：*American Anthropologist* 108:261–262, DOI 10.1525/aa.2006.108.1.261 等）；Atkinson & Whitehouse 2011, *EHB* 32:50–62, DOI 10.1016/j.evolhumbehav.2010.09.002（已验证）；Kapitány, Kavanagh & Whitehouse 2020, *Phil. Trans. R. Soc. B* 375:20190436, DOI 10.1098/rstb.2019.0436（全文经 PMC 验证）。 |

### 2.5 Big Gods 与其反证——**本项目必须如实呈现的争议样板**

**主张方（Big Gods）**：Norenzayan et al. 2016 (*BBS* 39) 提出，最近 10–12 千年里，"越来越强大、越道德化、越具惩罚性的超自然主体 + 信念的可信增强展示（CREDs）+ 其他促进团结的心理成分"这一**文化包**，提高了共同信仰者之间的生育率与大规模合作，从而在群体间竞争中胜出并扩散。该框架明确调和了副产品说与适应说：信念最初是副产品，之后特定文化变体因其亲社会效果被选择。（摘要已验证。）

**行为证据**：Purzycki et al. 2016, *Nature* 530:327–330。8 个社区（内陆 Tanna 与沿海 Tanna（瓦努阿图）、Yasawa 与 Lovu（斐济）、Pesqueiro（巴西）、Pointe aux Piments（毛里求斯）、图瓦共和国（西伯利亚）、Hadzaland（坦桑尼亚）），**n = 591，观测 35,400**。结论：受访者越认为其道德神具惩罚性且知晓人的想法与行为，**分给地理上遥远的同教陌生人的硬币越多**（相对于自己和本地同教者）。注意这个效应的对象是"远处的同教者"，是**公正性**而非泛泛的善意。（摘要已验证。）

**撤稿事件（必须写进项目文档）**：
- Whitehouse, François, Savage, Currie, Feeney, Cioni, Purcell, Ross 等 13 人 2019, "Complex societies precede moralizing gods throughout world history", *Nature* 568(7751):226–229, DOI 10.1038/s41586-019-1043-4。Crossref 记录现为 **"RETRACTED ARTICLE"**。
- **撤稿通知**：*Nature* 595(7866):320, DOI 10.1038/s41586-021-03656-3，撤稿日期 **2021-07-07**（Retraction Watch 记录 2021-07-06）。
- **批评文**：Beheim, Atkinson, Bulbulia, Gervais, Gray, Henrich, Lang, Monroe 等 15 人 2021, "Treatment of missing data determined conclusions regarding moralizing gods", *Nature* 595(7866):E29–E34, DOI 10.1038/s41586-021-03655-4。要点（摘要原文已验证）：
  - 原文主张道德神只出现在约 **100 万人**规模的"megasociety"形成之后。
  - 但 Seshat 中道德神数据点有 **61%（n = 490）**是缺失值，且主要来自人口 < 100 万的较小社会。
  - 作者在 R 脚本里把所有缺失值**重编码为"确知不存在"**（t 检验 supplementary code folder 04 第 39 行；logistic 回归 folder 06 第 48 行）。
  - **缺失与"不存在"的相关系数 r = 0.97**。
  - 只用现存数据、或使用各类标准插补方法，**结论反转：道德神先于社会复杂度上升**。
  - 12 个世界区域中，"首次出现"几乎总是紧跟在文字或识字观察者出现之后；**整个数据库中只有一个观测报告了"在首次出现之前确知不存在道德神"——中国黄河中游**。（这一点对本项目尤其刺眼：唯一那个"确知没有"的点正好在我们的舞台上，而它极可能是记录条件的产物而非事实。）
- **原作者团队的重做**：Turchin, Whitehouse, Larson, Cioni, Reddish, Hoyer, Savage, Covey 等 2023, "Explaining the rise of moralizing religions: a test of competing hypotheses using the Seshat Databank", *Religion, Brain & Behavior* 13:167–194, DOI 10.1080/2153599X.2022.2065345。摘要已验证，结论：**"我们发现强有力的证据支持既有研究——此类信念并未驱动社会复杂度的上升。相反，我们的分析表明群体间战争（由资源可得性支撑）在社会复杂度与道德化宗教的演化中都起了主要作用。因此社会复杂度与道德化宗教的相关，似乎源自共同的演化驱动因子，而非二者之间的直接因果关系。"**
- **测量层面的釜底抽薪**：Lightner, Bendixen & Purzycki 2023, *EHB* 44:555–565, DOI 10.1016/j.evolhumbehav.2022.10.006（全文已抓取）。要点：SCCS 的 "moralizing high gods"（变量 V237）定义要求该神**先是宇宙的创造者/主宰**，然后才问它是否关心道德。这个前置筛选与"超自然惩罚"在理论上无关，却过滤掉了所有非创世的道德神，**在小规模社会系统性制造假阴性**（作者举 Orokaiva 的 demi-gods、Ainu 的致病惩罚神为例——两者都被编码为"无 MHG"，但都有道德神）。另外一个常被忽略的数字：SCCS 中 186 个社会、V237 与 V238（司法层级数）都完整的有 167 个；即便在**司法层级最高**的一档，MHG 存在的预测概率也只有约 **50%**——"抛硬币和这个模型差不多准"。
- **史学界的回应**：Slingerland, Monroe, Spicer, Muthukrishna 2019, "Historians Respond to Whitehouse et al. (2019)", DOI 10.31234/osf.io/2amjz（预印本，已验证存在）；后续辩论见 *Journal of Cognitive Historiography* 第 6 卷（Rüpke, DOI 10.1558/jch.39885；Patzelt, DOI 10.1558/jch.39573）与 Larson, Whitehouse, François, Hoyer & Turchin 2024, *JCH* 8:168–183, DOI 10.1558/jch.25994。

**竞争假说 1：生态压力（Botero et al. 2014）** — 见 §4 系数表。要点：道德化高神在**资源更贫瘠、生态胁迫更大**的社会更常见；同时在有**牲畜（可移动财产权代理）**和**更高政治复杂度**的社会更常见。n = 583，AUC = 0.91。

**竞争假说 2：富裕/能量捕获（Baumard et al. 2015）** — 公元前约 500–300 年间，长江与黄河流域、东地中海、恒河流域三地几乎同时出现高度相似的、强调自制与禁欲的"彼世的"道德化传统（佛教、耆那教、婆罗门教、道家、第二圣殿犹太教、斯多亚，及后续的基督教、摩尼教、伊斯兰教）。统计建模表明：**是经济发展（能量捕获，取自 Ian Morris 的指数），而非政治复杂度或人口规模，解释了轴心时代的时间点。**（摘要已验证；**具体的能量捕获阈值数值与单位，本次未从原文取得**。）机制猜想来自生活史理论：绝对富裕把人的动机系统从短期策略（资源攫取、强制性互动）推向长期策略（自制技术、合作性互动）。

**竞争假说 3：超自然惩罚而非道德高神（Watts et al. 2015）** — 96 个南岛语系文化，BayesTraits 可逆跳 MCMC，跨 4000 棵语言树。结果：MHG 与政治复杂度的依赖模型 vs 独立模型 **BF = 3.60**；"MHG 跟随复杂度"约束模型 vs 独立 **BF = 4.52**。**广义超自然惩罚（BSP）** 与复杂度依赖 vs 独立 **BF = 3.24**；"BSP 先于复杂度"约束 vs 独立 **BF = 5.02**。也就是说：**是宽泛的超自然惩罚先于政治复杂度，而道德化高神跟在复杂度之后。**

**阴暗面：人祭（Watts et al. 2016）** — 93 个南岛语系传统文化，贝叶斯系统发育方法。结论：**人祭在阶层化出现之后使之稳定，并推动向严格世袭的等级制转变**；对已经平等的社会，人祭并不促成阶层化的产生。这是"宗教做了什么"里最可计算的一条，而且方向是**巩固不平等**，不是促进合作。（*Nature* 532:228–231，摘要已验证。）

### 2.6 宗教经济学：教派—教会循环、严格教会、俱乐部品

| 项 | 内容 |
|---|---|
| **核心机制** | 宗教团体产出的是**排他性俱乐部品**（互助保险、择偶市场、求职网络、集体仪式的临场感）。这类品的质量取决于其他成员的投入 → 存在正外部性 → 竞争均衡下投入不足 → **看似无谓的禁令与牺牲实际上是高效的**：它们对"外部选项"征税，从而抬高成员的内部投入。 |
| **形式化程度（已验证的版本）** | Berman (NBER WP6715 / QJE 2000) 对 Iannaccone (1992) 的复述，全文已抓取，逐字要点：成员从宗教活动时间 **R**、世俗品 **S**、群体质量 **Q**（"其他成员花在 R 上的平均时间"，对他人构成外部性）中获得效用。时间禀赋 T 分配给 R 与工作 H = T − R；工资 w，世俗品价格 p。**完整收入预算约束 wT = pS_i + wR_i**。社会最优 R* 的条件包含两项边际替代率（宗教活动 vs 消费；群体质量 vs 消费），**竞争均衡忽略了后一项**。禁令通过补贴 R 或对 H 征税来修正。若 R 与 Q 互补，Q 会**放大劳动供给弹性**（对称 Nash 均衡下 Q = R），即 Becker & Murphy (2000) 的 "social multiplier"。 |
| **状态变量** | `sect.strictness s`（对外部选项的有效税率）、`member.R`、`group.Q`、`club_good_value`、`monitoring_quality`。 |
| **参数（已验证）** | 以色列极端正统派：男性平均**读经院（yeshiva）到 40 岁**；**TFR = 7.6** 且上升中；相比之下蒙特利尔哈西德社区 **25 岁以上男性只有 6%** 全职就读（Shahar et al. 1997）；犹太律法要求**收入的最低 10%** 用于慈善；36 岁的以色列极端正统派男性在每月 400 美元津贴与两倍以上工资之间仍选择留在读经院，而未来二十年他要为 7–8 个子女各出半套公寓（每套下限 5 万美元）。 |
| **适用范围** | 任何有排他性互助的宗教/非宗教社群；解释"严格 → 强"、补贴的反直觉效应、市场侵入传统社群时极端正统派的诞生。 |
| **已知局限** | Marwell 1996 (*AJS* 101:1097–1103) 的评论标题就是"我们仍然不知道严格教会是不是强，更不知道为什么"（已验证存在）。测量"严格度"与"强度"的内生性未解决。 |
| **出处** | Iannaccone 1988, *AJS* 94:S241–S268, DOI 10.1086/228948；Iannaccone 1992, *JPE* 100:271–291, DOI 10.1086/261818；Iannaccone 1994, *AJS* 99:1180–1211, DOI 10.1086/230409；Berman 2000, *QJE* 115:905–953, DOI 10.1162/003355300554944（NBER WP6715 全文已验证）；Berman & Laitin 2008, *J. Public Economics* 92:1942–1967, DOI 10.1016/j.jpubeco.2008.03.007。以上篇目全部已验证；除 Berman 外，其余论文的内部公式本次未直接读到。 |

**教派—教会循环（Stark & Bainbridge）**：Stark & Bainbridge 1979, *JSSR* 18:117, DOI 10.2307/1385935（"Of Churches, Sects, and Cults"）建立了 church / sect / cult 的概念区分（sect 是从既有主体分裂出来的、与环境张力更高的团体；cult 是新引入或新创的）。**Stark & Bainbridge 1980, *AJS* 85:1376–1395, DOI 10.1086/227169（"Networks of Faith"）是本项目最该抄的一篇**：皈依主要沿**既有人际纽带**发生，而非通过教义说服。这直接决定了传播机制应写成网络上的复杂传染，而不是均匀混合的 SIR。（两篇篇目已验证，内部数据本次未读。）

**分裂的形式模型**：Maloney, Civan & Maloney 2009, *Public Choice* 142:441–460, DOI 10.1007/s11127-009-9533-9（"Model of religious schism with application to Islam"）。**该文存在已验证，模型内部结构本次未取得**（Springer 阻断）。

### 2.7 已有的宗教 ABM：可直接借鉴的一个，和它的坑

**MERV 1.0 / Shults, Gore, Wildman, Lynch, Lane & Toft 2018, *JASSS* 21(4):7, DOI 10.18564/jasss.3840**（全文已抓取验证）。这是目前公开发表的宗教 ABM 里架构最完整、参数最透明的一个。

架构（逐条验证）：
- N 个 agent 分成多数群 / 少数群，置于 5N × 5N 的二维格点上；组内社会网络用 **Watts-Strogatz 小世界模型**生成，**跨组无连边**。
- 每个 agent 有两个"宗教性"维度：**AP（anthropomorphic promiscuity，把模糊现象归因于超自然行动者的倾向）** 与 **SP（sociographic prudery，服从内群超自然权威所规定的社会规范的倾向）**。两者相互独立。
- 环境每步产生四类危害：**natural**（地震火山）、**predation**（掠食者）、**social**（被视为威胁的文化他者）、**contagion**（看似带病的外群成员）。后两类需要 agent 在指定半径内发现一个外群 agent 才会发生。每类危害的强度由**三角分布**（min, mode, max，取值 0–100）抽样。
- 每个 agent 对每类危害有一个感知阈值（0–100）。
- 焦虑更新用**参数化的 Rescorla-Wagner 模型**：`anxiety ← anxiety + α·β·(λ − anxiety)`，其中感知到危害时 `λ=1, β=1.00, α=0.05`；未感知到时 `λ=0, β=0.10, α=0.05`。焦虑上限 1.0。
- 每个 agent 有 **hyper-vigilance threshold**：焦虑超过它时，agent 沿社会网络（先一跳、再二跳）寻找同样超阈值的同组成员，凑够人数则形成**仪式簇（ritual cluster）**。在寻找或参与仪式期间 agent 不再受危害影响。
- 仪式簇形成后：AP 按 `ap ← ap + mean(ap_簇内)/mean(ap_全组)` 增长；SP 按 `sp ← sp + mean(sp_全组)/mean(sp_外组)` 增长；焦虑按"未感知危害"分支衰减。全簇成员焦虑都降到各自阈值以下时解散。
- 参数扫描：20,000 次运行 × 250 步 = 5,000,000 步，其中 1,212,673 步（**24.25%**）落在"至少一组焦虑上升"的区间内。
- 追踪验证得到唯一 suspiciousness = 1.0 的条件：**（多数群占比 ≤ 70%）AND（contagion 危害强度 ≥ 阈值）AND（social 危害强度 ≥ 阈值）**。自然与掠食危害不足以产生互升的排外焦虑。
- 相关性：焦虑下降 vs AP 上升 **r = 0.51 (p<0.01)**；焦虑下降 vs SP 上升 **r = 0.19 (p<0.01)**。

**这个模型的坑（我们必须避免）**：式(2)(3) 是**无界累加**——AP 和 SP 每步都加一个正数比值，没有衰减项、没有上限，"religiosity" 只会单调上升。论文自己也承认 AP 增长快于 SP 是这种归一化方式的产物而非机制结论。另外整个模型只有"危害 → 焦虑 → 仪式 → 焦虑下降"一个闭环，没有经济、没有繁殖、没有组织。**可以抄它的危害—阈值—仪式簇结构，绝不能抄它的状态更新式。**

其他：Bainbridge 1995, *Sociological Perspectives* 38:483–495, DOI 10.2307/1389269（宗教信念的神经网络模型）；Bainbridge 2014, "Artificial Intelligence Models of Religious Evolution", DOI 10.1093/acprof:oso/9780199688081.003.0012；Lane 2018, *RBB* 8:290–300, DOI 10.1080/2153599X.2017.1302977（用计算模型强化超自然惩罚假说）。三者篇目已验证，内容本次未读。论文中标注的 MERV 代码库 `https://github.com/SimRel/Merv1.0` 在本次检索中**无法访问（GitHub API 返回空）**。

---

## 3. 可直接用于本项目的机制清单

### 3.0 总设计原则：宗教是场，不是对象

在最底层，**每个人 agent 携带三个恒定的认知参数**（出生时从人群分布抽样，终生不变或缓慢漂移）：

- `hadd` ∈ [0,1]：能动性检测阈值的倒数（Barrett 2000）。
- `teleo` ∈ [0,1]：目的论/意图归因倾向（Willard & Norenzayan 2013 的"认知偏误预测宗教信念"）。
- `conformity` ∈ [0,1]：从众传递权重。

这三个参数意味着：**不存在"无宗教"的人群**。任何聚落在任何时刻都有一个非零的 `ambient_supernatural_attribution`。要建模的是组织化的相变，不是从零到一。

### 3.1 最小宗教状态（本简报被要求特别回答的问题）

一个 `Religion` 对象最少需要以下九组状态。设计原则：**每一个字段都必须能被某条规则读写，且必须能被追溯到一个结构条件**。

```
Religion {
  id, birth_tick, birth_settlement,
  founding_conditions: {A, surplus_pc, freerider_pressure, neighbor_field,
                        trigger_event_id, rng_seed}       // 因果链锚点

  // (1) 超自然主体
  pantheon: [ SupernaturalAgent {
      ontological_template: PERSON|ANIMAL|PLANT|ARTIFACT|NATURAL_OBJECT|ANCESTOR,
      violations: set,               // MCI：|violations| 建议 1–2，>3 触发衰减
      domain: [weather, disease, harvest, war, fertility, justice, death, ...],
      // —— 以下四个轴必须独立，不得合成一个"大神"标量（见 §8 反模式 2）
      cosmic_scope: 0..1,            // 是否创世/主宰宇宙（= SCCS 的高神判据）
      moral_concern: 0..1,           // 是否关心人际道德
      punitiveness: 0..1,            // 是否惩罚
      strategic_omniscience: 0..1,   // 对"社会性策略信息"的知晓程度（Purzycki 的核心变量）
      moral_scope: enum{SELF, KIN, LINEAGE, VILLAGE, POLITY, COFAITH, ALL},
      locality: PLACE_BOUND | MOBILE,
      reachability: [ritual_ids]     // 哪些仪式能影响它
  } ]

  // (2) 义务与禁忌
  norms: [ Norm {
      behavior_id, direction: REQUIRE|PROHIBIT,
      cost_time, cost_goods, cost_opportunity,   // 关键：cost_opportunity 是对外部选项的税
      detectability_by_humans: 0..1,
      detectability_by_agent: 0..1,              // = 该神的 strategic_omniscience
      sanction_worldly, sanction_otherworldly,
      irreversibility: 0..1                      // 割礼/刺青/绝育式的不可逆标记
  } ]

  // (3) 仪式库（三个独立标量，见 §2.4）
  rituals: [ Ritual {
      frequency_per_year, dysphoria: 0..1, euphoria: 0..1,
      n_participants, synchrony: 0..1,
      cost_time, cost_material, cost_body,
      officiant_required: bool, exclusive_to_members: bool
  } ]

  // (4) 组织形态（离散状态机，见 §3.3）
  org: {
      form: DIFFUSE | SHAMANIC | LINEAGE_CULT | CONGREGATIONAL |
            MONASTIC | HIERARCHICAL | STATE_CULT,
      membership: BY_BIRTH | BY_INITIATION | BY_PROFESSION | BY_CONQUEST,
      clergy_count, clergy_recruitment: HEREDITARY|ORDINATION|POSSESSION|EXAM,
      succession_rule, succession_contested: bool,
      translocal_coordination: 0..1,
      doctrine_fixity: 0..1,          // 有无正典；影响分裂概率
      strictness s: 0..1              // Iannaccone/Berman 的有效外部选项税率
  }

  // (5) 经济基础
  economy: {
      flows: {offerings, tithe_rate, state_subsidy, fees_for_service,
              sale_of_ordination, commercial_income},
      stocks: {land_area, land_tenants, treasure, granary, buildings, slaves/bondsmen},
      tax_status: TAXED | EXEMPT | TRIBUTARY,
      corvee_exemption: bool
  }

  // (6) 真理主张与可否证性
  claims: [ Claim {
      content_ref,                                  // LLM 生成的文本指针
      verifiability: UNFALSIFIABLE | DELAYED | IMMEDIATE,
      efficacy_domain,                              // 声称能影响什么
      buffers: [reinterpretation, blame_the_faithful, esoteric_reading, date_shift]
  } ]

  // (7) 内群边界
  boundary: {
      markers: [ {type: DIET|DRESS|LANGUAGE|BODY|NAME|CALENDAR,
                  cost, fakeability: 0..1, reversibility: 0..1} ],
      out_group_stance: TOLERANT | EXCLUSIVE | PROSELYTIZING | HOSTILE
  }

  // (8) 与政体的关系
  polity_relation: {
      legitimation_supplied: 0..1,      // 给统治者提供多少合法性
      autonomy: 0..1,
      registered/canonized: bool,       // 中国式的赐额/封号
      rival_sovereignty_claim: bool     // 是否自称掌握世俗权柄（→ 镇压概率）
  }

  // (9) 每聚落的传播状态（稀疏字典）
  presence: { settlement_id -> {prevalence, cred_exposure, clergy_density,
                                last_miracle_tick, local_variant_drift} }
}
```

**为什么这样简化**：这九组是能被其他子系统（人口、经济、战争、政治、信息）读写的最小闭包。删掉任何一组，都会出现"宗教影响了世界但世界无法反作用于宗教"的单向耦合。特别地，(5) 经济基础和 (8) 政体关系是把宗教接进财政与政治系统的唯一接口，没有它们，宗教就退化成装饰。

### 3.2 机制 A：归因压力场（Attribution Pressure）

**输入 → 输出**：聚落层面的冲击统计 → 一个连续标量 `A_s ∈ [0, ∞)`，驱动所有下游宗教活动。

**算法草图**（形式取自 Botero et al. 2014 的实证结构，具体权重需自选）：

```
A_s = w1 * mortality_shock_rate            // 疫病、饥荒、婴幼儿死亡
    + w2 * harvest_CV                       // 产出年际变异系数
    + w3 * climate_unpredictability         // 对应 Colwell's P 的补：1 - P
    + w4 * raid_hazard
    - w5 * ln(1 + explanatory_tech_coverage) // 有可验证疗效的技术会侵蚀辖区（Singh 2018）
```

- Botero 用 **Colwell's P**（0 = 完全不可预测，1 = 完全可预测）度量降水/温度的年际可预测性，用 1901–1950 年 CRU-TS 3.1 的 0.5°×0.5° 格点数据。本项目若有自建气候模块，可直接算 Colwell's P。
- Botero 的实证方向：**资源丰度（PC1，降水+初级生产力+生物多样性）系数为负（−0.333）**——越贫瘠越信道德化高神；且在资源丰度**高于第 15 百分位**的社会，气候越多变不可预测，信念概率越高；而在**最贫瘠的 15%** 社会里，反而是气候越稳定信念概率越高（因为已经差到不能再差，变化意味着可能变好）。这是一个真实的非单调交互，值得抄。

**时间尺度**：年。**空间粒度**：聚落 / 小流域。**证据等级**：**B**（机制有共识，方向有 A 级证据，权重需自选）。**归属**：`rules_math`。

**失效条件**：Botero 的分析单位是"社会"而非个体，作者明确警告结论不可下推到个体信念差异。另外该分析是横断面的，没有时间维度。

### 3.3 机制 B：组织形态状态机（宗教诞生的守门人）

**这是回答"如何让宗教诞生由结构条件触发而不是由 LLM 觉得该有个宗教了"的核心。**

`org.form` 是一个**离散状态机**，转移只由规则触发，LLM 无权调用转移。七个状态与转移条件：

| 从 | 到 | 触发条件（全部为可计算量） | 依据 |
|---|---|---|---|
| DIFFUSE | SHAMANIC | `A_s > θ_A` **且** 聚落可支持一名非全职专家（`surplus_pc > θ_s`）**且** 该领域缺乏可验证疗效技术 **且** 群体规模 ≥ 最小服务市场 | Singh 2018（B） |
| DIFFUSE / SHAMANIC | LINEAGE_CULT | 出现**可继承的团体财产**（土地、畜群、水权、渔场），且继承争端率上升 | Botero: 动物驯养（可移动财产权代理）系数 **+0.988**；Freedman；Faure（B） |
| 任意 | + 社区历法祭 | 定居 **且** 存在需要季节性集体劳动的公共设施（灌溉、梯田、城墙） | B（协调装置论；无量化参数） |
| LINEAGE_CULT / SHAMANIC | CONGREGATIONAL | **排他性俱乐部品价值高** 且 **人际监督失效率高**：`club_value × (1 − monitoring_quality) > θ_c` | Iannaccone 1992 / Berman 2000（B，有形式化） |
| CONGREGATIONAL | HIERARCHICAL | 出现**文字** 且 需要跨聚落再生产（教团存在于创始人未到过的地方）且 `translocal_coordination` 需求 > θ | Whitehouse 的 doctrinal 模式（B） |
| HIERARCHICAL / CONGREGATIONAL | MONASTIC | 该宗教获得**免税可继承地产** 且 存在**独身/脱产**人员类别 | Gernet；Kohn（B） |
| 任意 | STATE_CULT | 政体的合法性赤字 > θ **且** 该宗教 `legitimation_supplied` 在候选中最高 **且** 无 `rival_sovereignty_claim` | B |
| STATE_CULT / MONASTIC | 被镇压 / 强制还俗 | 见 §3.7 财政捕食循环 | Ch'en 1956；Gernet（B） |

**关键设计**：`Religion` 对象的**实例化**发生在第一次离开 DIFFUSE 时，由规则引擎创建一个**空壳**（所有 §3.1 字段有数值但无名字、无神话、无经文）。**然后**才调用 LLM 填内容。LLM 的输出被 schema 校验并 clamp 到规则允许的取值范围内。LLM 无法凭空调用 `create_religion()`。

**时间尺度**：转移检查每 5–10 年一次（不要每年，会抖）。**空间粒度**：聚落 → 区域。**证据等级**：**B**（每条转移的机制有文献支撑，阈值全部自选）。**归属**：`rules_math`（转移）+ `llm_agent`（内容）。

### 3.4 机制 C：仪式形态空间与代价—回报

**输入 → 输出**：`(A_s, group_size, club_value, free_rider_rate)` → 仪式库的 `(frequency, dysphoria, euphoria, cost)` 分布。

**约束（来自数据，必须满足）**：
- 生成的仪式库必须满足 `corr(frequency, dysphoria) ≈ −0.41`、`corr(frequency, euphoria) ≈ −0.08`（Atkinson & Whitehouse 2011）。实现方式：从一个指定协方差的多元分布抽样，而不是让 LLM 随手写。
- dysphoria 与 euphoria **正交**，不能合并成一个"强度"（Kapitány et al. 2020）。

**回报侧（三条独立通道，不要混）**：
1. **筛选通道**（Iannaccone / Berman）：`ΔQ = f(Σ_i R_i)`，仪式与禁令通过对外部选项征税抬高 R，进而抬高 Q。俱乐部品产出 `club_output = g(Q, N)`。
2. **融合通道**（Whitehouse et al. 2017）：dysphoric 共享经历 → `fusion` 上升 → 极端自我牺牲意愿上升。可直接用其模型：`S_j = h·E_j + (1−h)·P_j`，`f_ij = 1 + b·P_j − c·z_ij`。
3. **焦虑通道**（Shults et al. 2018）：仪式降低 anxiety。可以抄其 Rescorla-Wagner 更新（α=0.05；感知危害 β=1.0, λ=1；未感知 β=0.1, λ=0），**但必须给 AP/SP 类状态加衰减与上界**。

**失效条件**：代价信号的核心实证（Sosis & Bressler 2003）的具体系数**本次未能取得**。不要在没有参数的情况下把"代价越高存续越好"写成单调函数——文献里这个关系在**世俗**公社中不成立，只在宗教公社中成立（此为我的记忆，D 级，待核）。

**时间尺度**：仪式频率是"每年 f 次"，模拟里按年结算聚合效果。**空间粒度**：仪式簇（几人到几百人）。**证据等级**：约束系数为 **A**（ρ 值有原文），回报函数形式为 **B/C**。**归属**：`hybrid`。

### 3.5 机制 D：传播（这是最强的一项，不要做弱）

**输入 → 输出**：`(邻居信念场, 贸易/移民/征服流, CRED 暴露, 社会网络)` → 每聚落 `prevalence` 的更新。

**核心事实**：Botero et al. 2014 多模型平均中，**空间邻近项（10 个最近邻的信念均值，取值 0–1）系数为 5.867 ± 0.967，相对变量重要性 1.00，单变量 AUC = 0.86**。作为对比，政治复杂度系数 0.652、资源丰度 −0.333。**传播项在数量级上碾压所有内生项。**

**可直接抄的 logit（Botero 表 3 多模型平均，全部系数已验证）**：

```
logit P(moralizing_high_god) =
    -3.740
  + 0.652 * political_complexity        // 超出地方社区的司法层级数
  + 0.988 * animal_husbandry            // 可移动财产权代理（0/1）
  - 0.716 * agriculture                 // 0/1；注意与畜牧高度共线
  - 0.333 * resource_abundance          // PC1：降水+NPP+生物多样性，标准化
  - 0.040 * climate_stability           // PC2：降水/温度可预测性+温暖稳定，标准化
  - 0.398 * (resource_abundance * climate_stability)
  + 5.867 * spatial_proximity           // 10 最近邻的信念均值 ∈ [0,1]
  + language_family_random_effect
```

**但传播不能只用这个 logit**。它是横断面的，没有渠道结构。渠道要分开建模：

| 渠道 | 机制 | 速率决定因素 | 依据 |
|---|---|---|---|
| **人际网络**（主导） | 皈依沿既有强纽带发生，不是靠教义说服 | 网络度分布、跨群纽带密度、亲属/婚姻链 | Stark & Bainbridge 1980（B） |
| **CRED 暴露** | 看见他人为信念付出代价 → 更新信念 | 本地高代价行为的可见度 × 行为者的威望 | Henrich 2009；Lanman & Buhrmester 2017（B） |
| **商路** | 商人/僧侣沿路网移动，在节点城市建立据点 | 路网通行成本、节点商业量 | Foltz 2010（C，无参数） |
| **移民/殖民** | 整包携带（Botero 的 language family 效应） | 迁徙流量 | B |
| **征服** | 自上而下强加；先精英后底层，且常只改变**登记**而非**实践** | 征服者的 `out_group_stance`、行政渗透深度 | Szonyi 1997（B） |
| **精英采纳** | 统治者为合法性采纳，然后向下推 | 合法性赤字、教团的 `legitimation_supplied` | B |

**关键的"两层"设计**：`prevalence`（实际实践）与 `registered_status`（官方名册）**必须是两个变量**。Szonyi 1997 对华南五帝信仰的研究表明，"标准化"往往只是地方社群给旧神换了个官方认可的名号，实践几乎没变。这正好实现 MANDATE 第 9 条"世界事实与历史叙事分离"。

**时间尺度**：年（网络扩散）到十年（商路/征服）。**空间粒度**：聚落 + 路网边。**证据等级**：系数 **A**，渠道分解 **B**。**归属**：`rules_math`。

### 3.6 机制 E：道德神的"作用域"是连续量，由合作问题的作用域驱动

**这是本简报对撤稿争议给出的工程解**。不要写"复杂度 → 道德神"或"道德神 → 复杂度"。写：

```
// 每个超自然主体的 moral_scope 与 strategic_omniscience 是慢变量，
// 由"未被熟人网络监督的、经济上重要的互动占比"驱动
anonymity_s = (1 - gossip_coverage_s) * transaction_volume_with_strangers_s / total_transactions_s

d(strategic_omniscience)/dt = κ1 * (anonymity_s - strategic_omniscience) + noise
d(moral_scope)/dt          = κ2 * (scope_of_active_cooperation_problem - moral_scope) + noise
d(punitiveness)/dt         = κ3 * (enforcement_deficit_s - punitiveness) + noise
```

同时，让 `anonymity_s`、`social_complexity_s`、`intergroup_war_intensity_s` **共享驱动因子**（战争强度、资源可得性），正如 Turchin et al. 2023 所主张的。这样：
- 在有些历史线上道德神先于复杂度（符合 Beheim et al. 的重分析）；
- 在有些线上复杂度先于道德神（符合原论文的表面模式）；
- 在小规模社会里也可以有道德神（符合 Lightner et al.）；
- 两者的相关来自共同驱动（符合 Turchin et al. 2023）；
- 而**我们不需要在这场争论中站队**，因为我们建的是机制，不是拟合历史序列的回归。

**辅助约束**：Watts et al. 2015 的南岛证据表明**广义超自然惩罚（BSP）先于政治复杂度（BF=5.02），而道德化高神跟在复杂度之后（BF=4.52）**。所以在状态空间里，`punitiveness` 应该比 `cosmic_scope` 更早上升。这是一条可以写死的顺序约束。

**证据等级**：**C**（争议激烈，量化弱，κ 全靠自选）。**归属**：`rules_math`。**归属理由**：这是明确不能给 LLM 的——一旦 LLM 觉得"该有个大神了"，就是隐藏剧情树。

### 3.7 机制 F：宗教经济与财政捕食循环

这是宗教影响文明轨迹的**最物质、最可算**的一条，而且中国史提供了最好的校准（§6）。

```
每年：
  income  = offerings(prevalence, wealth) + tithe_rate*member_income
          + state_subsidy + fees_for_service + commercial_income
  outgo   = clergy_upkeep + building + charity_out + ritual_cost
  Δtreasure = income - outgo
  // 土地积累：捐赠 + 购买 + 投献（农户为避税把地挂在寺观名下）
  Δland   = donations + purchases + commendation(tax_pressure_on_peasants)
```

**捕食触发**（这是循环的关键）：

```
fiscal_threat = (religion.land_area / polity.taxable_land)
              + (religion.clergy_count / polity.corvee_eligible_pop)
              + w * religion.rival_sovereignty_claim

if fiscal_threat > θ_predation AND polity.fiscal_stress > θ_stress:
    掷骰，可能进入以下之一：
      (a) 出售度牒 / 名额（把宗教身份货币化，短期财政收入，长期加剧问题）
      (b) 限额（规定僧道额数、寺观数）
      (c) 没收 + 强制还俗（把人口和土地拉回税基）
      (d) 承认并征税（把宗教变成税收中介）
```

- (a) 有直接史料依据：Ch'en 1956, "The Sale of Monk Certificates during the Sung Dynasty. A Factor in the Decline of Buddhism in China", *Harvard Theological Review* 49:307–327, DOI 10.1017/S0017816000028315（篇目已验证；具体售价与数量本次未取得）。
- (c) 的经典案例是唐会昌毁佛（845）。**常被引用的具体数字（拆毁寺 4,600 余所、还俗僧尼 260,500 人、毁招提兰若 40,000 余所）源自《旧唐书》《资治通鉴》，属于我的记忆，本次未在文献中验证，D 级，不得作为参数直接使用。**
- 学术锚点：Gernet, *Buddhism in Chinese Society: An Economic History from the Fifth to the Tenth Centuries*（Verellen 英译；经三篇书评验证存在：*JAOS* 116:609, DOI 10.2307/605237；*Pacific Affairs* 68:596–597, DOI 10.2307/2761291；*China Review International* 7:85–90, DOI 10.1353/cri.2000.0023）。**其具体数据本次未读。**

**时间尺度**：年（收支）、几十年到百年（捕食周期）。**空间粒度**：政体 + 寺观点位。**证据等级**：机制 **B**，参数 **D**。**归属**：`rules_math`（收支与触发）+ `llm_agent`（皇帝/宰相的具体诏令措辞与借口）。

### 3.8 机制 G：严格度动力学与教派—教会循环（分裂的可算版本）

这是"宗教分裂"不靠 LLM 拍脑袋的办法。

```
// 每个子群 g（一个地域、一个阶层、一个族群）有其"最优严格度"
s*_g = argmax_s [ club_value_g(s) - private_cost_g(s) ]
     // club_value 随 s 上升（搭便车被挤出），private_cost 随 s 上升（外部机会被放弃）
     // → s*_g 随 (外部机会成本 / 内部互助价值) 下降

// 组织的实际严格度会随财富漂移下降（"教会化"）
ds_org/dt = -δ * (endowment_per_member / subsistence) + ρ * (persecution_pressure)

// 分裂危险
schism_hazard = λ0
              + λ1 * max_g |s_org - s*_g| * size_g
              + λ2 * succession_contested
              + λ3 * doctrine_fixity * local_condition_divergence
              + λ4 * (clergy_rent / lay_contribution)     // 教士食利被视为腐败
```

- 第 2 项：Iannaccone 的严格教会逻辑的直接推论——组织越富、要求越松，某个仍面临高互助需求的子群就有动机另立门户，这正是 Stark & Bainbridge 的 sect formation。
- 第 3 项：doctrine_fixity 高（有正典）时，地方条件偏离会变成**教义争端**而非静默漂移；doctrine_fixity 低时（弥散型民间信仰）同样的偏离只会产生"另一个神"，不产生"异端"。**这解释了为什么中国民间信仰极少产生教义性异端，而有正典的传统频繁产生。**（C 级，机制合理但我未找到直接量化文献。）
- Singh 2021 的三重选择理论给了"异端/巫术指控"的生成条件：直觉性魔法 + 对重大不幸的可信解释 + 为迫害辩护的妖魔化神话。当聚落遭遇不可解释的重大不幸（瘟疫、连年歉收）且存在一个已被边缘化的子群时，指控概率上升。

**形式化程度**：**半形式化——λ 系数全部无来源**。已知存在一个形式化的分裂模型（Maloney, Civan & Maloney 2009, *Public Choice* 142:441–460），但本次未能取得其内容。

**时间尺度**：十年到百年。**空间粒度**：教团 + 子群。**证据等级**：**C**。**归属**：`rules_math`（危险率与分裂发生）+ `llm_agent`（争端的具体教义内容、双方的自我叙述）。

### 3.9 机制 H：人祭 / 极端仪式与阶层固化

Watts et al. 2016 给出一个方向明确、可写死的规则：

```
if society.stratification > 0 and human_sacrifice.present:
    P(stratification 回落) 显著降低              // 稳定既有分层
    P(转向严格世袭等级制) 显著升高
if society.stratification == 0:
    human_sacrifice 不显著提高分层出现概率       // 不能无中生有
```

93 个南岛语系文化，贝叶斯系统发育检验（摘要已验证）。**具体的转移率数值本次未取得**。

这一条对本项目的价值：它是文献里少见的"宗教做了什么"里方向明确且是**负面**的一条。有它，模拟才不会变成"宗教=合作增益器"的美化玩具。

**时间尺度**：百年。**证据等级**：**A/B**（单一但强的系统发育研究，n=93）。**归属**：`rules_math`。

### 3.10 机制 I：LLM 的边界（"宗教诞生守门人"）

| LLM **可以**决定 | LLM **绝对不能**决定 |
|---|---|
| 神的名字、外形、神话叙事 | 是否存在一个新宗教（由 §3.3 状态机决定） |
| 禁忌具体禁什么（吃什么、穿什么、哪天不能动土） | 禁忌的**成本量级**（由规则从 `s` 反解） |
| 仪式的具体形式与象征 | 仪式的 `frequency / dysphoria / euphoria`（从 §3.4 的相关约束抽样） |
| 教义争端的具体论点、异端的罪名 | 是否发生分裂（由 §3.8 的 hazard 掷骰） |
| 教士与统治者对话的措辞、诏令的理由 | 镇压是否发生（由 §3.7 的财政阈值） |
| 神迹传说、灵验故事的内容 | 神迹是否被**记录**、`prevalence` 如何变化 |
| 后世历史学家如何叙述这段宗教史 | 世界事实（真实发生了什么） |

**校验层**：LLM 每次输出都过一个 schema 校验器，把所有数值字段 clamp 回规则区间；文本字段则检查是否引用了该 agent 在其**信息视野**内不可能知道的实体（MANDATE 第 4 条）。

---

## 4. 硬数字与参数表

只列本次检索中在原文/摘要里实际看到的数值。

| 量 | 数值 | 单位 / 说明 | 适用时空范围 | 不确定度 | 来源 |
|---|---|---|---|---|---|
| MHG logit 截距 | −3.740 ± 0.604 | — | 583 个民族志社会，全球 | SE 见值 | Botero et al. 2014 PNAS，表 3 |
| 政治复杂度系数 | +0.652 ± 0.169 | 每增加一级"超出地方社区的司法层级" | 同上 | 相对重要性 1.00，单变量 AUC 0.78 | 同上 |
| 动物驯养（可移动财产）系数 | +0.988 ± 0.623 | 0/1 | 同上 | 相对重要性 0.40 | 同上 |
| 农业系数 | −0.716 ± 0.461 | 0/1，与畜牧共线（82% 社会同时有/无） | 同上 | 相对重要性 0.33 | 同上 |
| 资源丰度（PC1）系数 | −0.333 ± 0.216 | 标准化 | 同上 | 相对重要性 0.73 | 同上 |
| 气候稳定性（PC2）系数 | −0.040 ± 0.238 | 标准化 | 同上 | 相对重要性 0.48 | 同上 |
| 丰度 × 稳定性交互 | −0.398 ± 0.224 | — | 同上 | 相对重要性 0.25 | 同上 |
| **空间邻近系数** | **+5.867 ± 0.967** | 10 最近邻的信念均值 ∈ [0,1] | 同上 | 相对重要性 1.00，单变量 AUC 0.86 | 同上 |
| 模型总体判别力 | AUC = 0.91 | 在留出的 194 个社会上 | 同上 | 社科中 AUC 0.75 已算大效应 | 同上 |
| 样本量 | 583 社会（自 Ethnographic Atlas 中 775 个有宗教数据者筛出） | 训练 389 / 测试 194 | — | — | 同上 |
| 气候可预测性指标 | Colwell's P ∈ [0,1] | 0=完全不可预测 | CRU-TS 3.1，1901–1950，0.5°格点 | — | 同上（方法节） |
| 仪式频率 vs 唤起度 | ρ = −0.40 | Spearman | 651 仪式 / 74 文化群 | — | Atkinson & Whitehouse 2011，转引自 Kapitány et al. 2020 |
| 频率 vs dysphoric | ρ = −0.41 | 同上 | 同上 | — | 同上 |
| 频率 vs euphoric | ρ = −0.08 | 同上 | 同上 | — | 同上 |
| 仪式因子数 | 7 | Dysphoric / Euphoric / Pageantry-physical / Viscera / Pageantry-psychological / Frequency / Kin | 651 仪式、102 二值变量 | — | Kapitány et al. 2020 |
| 当代仪式体验样本 | 779 人 | 日本、印度、美国；预注册 | — | — | 同上 |
| Purzycki 实验规模 | n = 591，观测 35,400 | 8 个社区，两个行为博弈 | 瓦努阿图/斐济/巴西/毛里求斯/西伯利亚/坦桑尼亚 | — | Purzycki et al. 2016 *Nature* |
| Seshat 道德神数据缺失率 | 61%（n = 490） | 占统计检验所用观测 | 12 个世界区域 | — | Beheim et al. 2021 |
| 缺失—"不存在"相关 | r = 0.97 | 重编码造成的伪相关 | 同上 | — | 同上 |
| 被撤回的"megasociety 阈值" | ≈ 1,000,000 人 | **已撤稿，不得使用** | — | — | Whitehouse et al. 2019（撤稿） |
| Seshat 复杂度 PC1 | 77.2% ± 0.4% 方差 | 51 变量 → 9 特征 | 414 政体 / 30 NGA / 近 10,000 年 | — | Turchin et al. 2018 PNAS |
| Watts BF：MHG 跟随复杂度 | BF = 4.52（vs 独立） | 依赖 vs 独立为 3.60 | 96 个南岛文化，4000 棵语言树 | — | Watts et al. 2015 |
| Watts BF：BSP 先于复杂度 | BF = 5.02（vs 独立） | 依赖 vs 独立为 3.24 | 同上 | — | 同上 |
| 人祭研究样本 | 93 个南岛传统文化 | 贝叶斯系统发育 | — | — | Watts et al. 2016 *Nature* |
| SCCS 规模 | 186 社会；V237×V238 完整者 167 | V237=高神，V238=司法层级数 | 全球 | — | Lightner et al. 2023 |
| 最高复杂度档的 MHG 概率 | ≈ 50% | logistic 拟合 | SCCS 与 Swanson 数据 | 作者称"和抛硬币差不多" | 同上 |
| 极端正统派 TFR | 7.6 | 且上升中 | 以色列，1990s | — | Berman NBER WP6715 / QJE 2000 |
| 全职读经院平均退出年龄 | 40 岁 | 以色列 | 1990s | — | 同上 |
| 对照：蒙特利尔哈西德 25 岁以上全职就读比例 | 6% | 常为同一 rebbe 的追随者 | 1997 | — | Shahar et al. 1997，转引自同上 |
| 犹太律法最低慈善捐赠 | 收入的 10% | 时间捐赠可能更值钱 | — | — | 同上 |
| MERV 焦虑更新 | α = 0.05；感知危害 β=1.00, λ=1；未感知 β=0.10, λ=0；anxiety ≤ 1.0 | Rescorla-Wagner | ABM | 作者自选 | Shults et al. 2018 JASSS |
| MERV 参数扫描规模 | 20,000 次运行 × 250 步 = 5,000,000 步；24.25% 落在焦虑上升区间 | — | ABM | — | 同上 |
| MERV 焦虑↓ vs AP↑ | r = 0.51 (p<0.01) | 焦虑↓ vs SP↑ 为 r = 0.19 (p<0.01) | ABM | — | 同上 |
| MERV 触发条件 | 多数群占比 ≤ 70% AND 社会危害强度 ≥ 阈值 AND 传染危害强度 ≥ 阈值 | suspiciousness = 1.0 | ABM | — | 同上 |
| Whitehouse 2017 融合相关 | 自我定义共享经验 r = 0.239 (P=0.001)；日常共享经验 r = 0.187 (P=0.009) | 美国样本 N=97/98 | 灾害与恐袭后 | — | Whitehouse et al. 2017 |
| Seshat 规模（2026 网站） | 864 政体 / 47 个 Seshat Region / 10 大区；一般变量 26 项 8,924 记录；社会复杂度 77 项 26,206 记录；战争 49 项 17,536 记录；人祭 357 记录覆盖 323 政体 | 9600 BCE–2024 CE | 全球 | — | seshat-db.com（2026-09 抓取） |
| 轴心时代窗口 | 约 BCE 500 – BCE 300 | 三区域：长江/黄河、东地中海、恒河 | — | — | Baumard et al. 2015 |

**明确缺参的地方（不要编）**：
- Sosis & Bressler 2003 的公社存续系数、样本量、危险比 —— **文献未取得**（付费墙）。
- Baumard et al. 2015 的能量捕获阈值（kcal/人/日）—— **文献未取得**。
- Iannaccone 1992/1994 的具体函数形式与弹性 —— **只通过 Berman 的复述取得结构，未取得原文参数**。
- Maloney et al. 2009 分裂模型的方程与均衡条件 —— **文献未取得**。
- Johnson 2005 (*Human Nature* 16:410–446) 的 186 文化分析结果 —— **只验证篇目，未取得数值**。
- 中国各朝僧道人数、寺观数、寺产规模 —— **本次全部未验证**（见 §9）。

---

## 5. 数据集与数据库

| 名称 | 内容 | 覆盖 | 访问 | URL | 许可 |
|---|---|---|---|---|---|
| **Seshat: Global History Databank** | 政体级历史变量：社会复杂度（77 变量/26,206 记录）、战争（49/17,536）、一般（26/8,924）、宗教（含人祭 357 记录/323 政体）、经济；另有 CrisisDB（权力转移 3,439+ 记录） | 864 政体 / 47 Seshat Region / 10 大区；9600 BCE–2024 CE | 网站 Downloads 页 + API + GitHub | seshat-db.com | 需接受 User Agreement 与 Data License |
| **Database of Religious History (DRH)** | 专家填写的结构化"宗教群体/地点/文本"问卷（question–answer–confidence 三元组），定性描述 + 定量编码 | 全球，跨时段 | 网站为 JS 应用，**本次未能通过 API 取得条目数与许可** | religiondatabase.org | 本次未确认 |
| **D-PLACE** | 汇聚 Ethnographic Atlas、SCCS 等；含语言系属、生态变量、系统发育树 | 全球民族志社会 | 网站 + GitHub | d-place.org | **CC BY-NC 4.0**（网站页脚已验证） |
| **SCCS（在 D-PLACE 内）** | 186 个社会；**V237 = 高神**（4 档：缺失/不报告、otiose、活跃但不支持道德、活跃且支持道德）；**V238 = 司法层级数** | 全球 | 经 D-PLACE | d-place.org | 同上 |
| **Ethnographic Atlas（在 D-PLACE 内）** | Botero 用到的变量：v104/v106 地理坐标、**v34 宗教信念**（第 4 档=支持道德）、**v28 农业**、**v40 畜牧**、**v33 政治复杂度** | 1,267 个社会（其中 988 个以独特语言界定） | 经 D-PLACE | d-place.org | 同上 |
| **CRU-TS 3.1** | 月度全球降水/温度格点 | 0.5°×0.5°，Botero 用 1901–1950 | 公开 | — | 本次未确认 |
| **Austronesian 语言系统发育树** | Watts 等用的 4,000 棵后验树 | 南岛语系 | Austronesian Basic Vocabulary Database | — | 本次未确认 |
| **MERV 1.0 代码** | Shults et al. 2018 的 ABM 实现 | — | 论文声明位于 github.com/SimRel/Merv1.0，**本次 GitHub API 查询返回空** | — | 未知 |

**对本项目的用法**：
- Seshat / D-PLACE **不能当剧本**（MANDATE 第 8 条），只能当**校准集**：跑完一条虚拟历史线后，把虚拟世界的"社会复杂度 × 宗教组织形态"联合分布拿去和真实数据的联合分布比，看是否落在同一个流形上。
- 特别注意：**用 Seshat/SCCS 校准时必须复制 Beheim 的教训**——把"缺失"和"不存在"分成两个编码。我们自己的世界里有全知的模拟器，所以我们可以**同时**输出"真实值"和"一个虚构历史学家在当时的记录条件下能得到的值"，然后检查后者是否会重现真实数据里那种"缺失与不存在混淆"的偏差模式。这是一个非常漂亮的自我校验实验。

---

## 6. 中国与东亚特定证据

**声明：以下只作机制校准，不作剧情。** 虚拟世界不需要出现佛教、道教或天命。需要的是"当类似的结构条件出现时，会长出结构上同类的东西"。

### 6.1 祖先崇拜与宗族 → 对应机制 B（LINEAGE_CULT）
- 商代的核心宗教实践是**对祖先的占卜与祭祀**，王权与祖先谱系深度绑定（Keightley, *Sources of Shang History: The Oracle-Bone Inscriptions of Bronze Age China*, 1978，经三篇书评验证存在；Keightley 1988, "Shang Divination and Metaphysics", *Philosophy East and West* 38:367, DOI 10.2307/1399117）。
- 华南宗族研究给出"团体财产 → 祖先崇拜制度化"的经典论证：Freedman, *Lineage Organization in Southeastern China*（Routledge 重印 2021, DOI 10.4324/9781003135296；其中 "Ancestor Worship and Lineage Structure" 一章 DOI 10.4324/9781003135296-11）；Faure, *Emperor and Ancestor: State and Lineage in South China*（经书评验证，DOI 10.5860/choice.45-3344）。
- **对模拟的意义**：LINEAGE_CULT 的触发条件应该是**可继承的团体财产 + 继承争端**，而不是"人口达到 X"。Botero 的畜牧系数 +0.988（可移动财产权代理）在跨文化层面支持这个方向。

### 6.2 巫 → 礼 → 对应机制 B（SHAMANIC → 制度化）
- 李泽厚"由巫到礼"的论证有英译：Li Zehou (trans. Robert A. Carleo), "From Shamanism to Ritual Regulations", in *The Origins of Chinese Thought*, Brill 2018, DOI 10.1163/9789004379626_005（已验证存在，内容本次未读）。
- Puett, *To Become a God: Cosmology, Sacrifice, and Self-Divinization in Early China*（经三篇书评验证：*HJAS* 64:465, DOI 10.2307/25066751；*AHR* 108:1117–1118, DOI 10.1086/529803；*Journal of Religion* 83:421–429, DOI 10.1086/491341）。Puett 的核心论点（据书评标题与语境）是反对"中国宗教天然和谐"的叙事，强调**牺牲与自我神化是对神人关系的持续争夺**。
- **对模拟的意义**：从 SHAMANIC 到制度化的转变，不是"萨满消失"，而是**萨满的技能被王室垄断并转为常规化的历法性仪式**。状态机上应表现为 `org.form: SHAMANIC → STATE_CULT` 且 `ritual.frequency` 上升、`ritual.dysphoria` 下降——正好是 Whitehouse 从 imagistic 向 doctrinal 的移动，且符合 ρ = −0.41 的约束。

### 6.3 天命 → 对应机制 §3.1 字段 (8) `legitimation_supplied`
- 天命观把"统治的合法性"变成一个**可撤销的、以德行为条件的授权**，从而同时（a）给现政权提供合法性，（b）给叛乱者提供合法的反叛理由。Ivanhoe, "'Heaven's Mandate' and the Concept of War in Early Confucianism", DOI 10.1017/CBO9780511606861.016（已验证存在）；Grundmann, "Mandate of Heaven", *The Encyclopedia of Ancient History*, DOI 10.1002/9781119399919.eahaa00775（已验证存在）。
- **对模拟的意义**：这是一个漂亮的双刃机制，值得单独建模。`legitimation_supplied` 不应是一个只给统治者加成的常数，而应该是**条件性的**：`legitimacy = f(ruler_virtue_signal, portents, disaster_frequency)`。灾异频发 → 合法性下降 → 叛乱成本下降。这样"天灾导致王朝更替"就有了完整因果链，而不是随机事件。

### 6.4 佛教沿商路传入与本土化 → 对应机制 D（传播）
- Zürcher, *The Buddhist Conquest of China: The Spread and Adaptation of Buddhism in Early Medieval China*（经 *AHR* 书评验证：DOI 10.2307/1846312）。
- Foltz, "Buddhism and the Silk Road", in *Religions of the Silk Road*, DOI 10.1057/9780230109100_3（已验证存在）。
- **对模拟的意义**：外来宗教传入的三个可算前提：(a) 存在稳定的长程路网与商人共同体；(b) 存在**翻译中介**（把外来概念映射到本地概念的成本）；(c) 存在**精英需求缺口**（本地传统未覆盖的领域，如个体救度、来世）。本土化应建模为 `local_variant_drift`：每个聚落的教义副本以速率 μ 向本地既有信念漂移，`doctrine_fixity` 高的宗教漂移慢但一旦漂移就产生异端判定。

### 6.5 道教的组织化 → 对应机制 B（CONGREGATIONAL / HIERARCHICAL）与 §3.1 (8) 的 `rival_sovereignty_claim`
- Kleeman, *Celestial Masters: History and Ritual in Early Daoist Communities*（经三篇书评验证：*The Chinese Historical Review* 24:186–188, DOI 10.1080/1547402X.2017.1369249；*Early Medieval China* 2016:72–74, DOI 10.1080/15299104.2016.1250456；*Dao* 16:599–603, DOI 10.1007/s11712-017-9582-6）。
- Kohn, *Monastic Life in Medieval Daoism*, University of Hawaii Press, DOI 10.1515/9780824841669（已验证存在）。
- **常被引用的"二十四治""五斗米"等具体制度细节，本次未在文献中验证，D 级。**
- **对模拟的意义**：天师道是"宗教组织自带行政层级、税收与户籍"的典型——即 `rival_sovereignty_claim = true`。这应该显著提高被镇压概率，同时在国家崩溃时显著提高其接管地方治理的概率。这是一条很好的**双向**规则：同一个属性在强国家下是死因，在弱国家下是机会。

### 6.6 民间信仰与国家册封 → 对应机制 D 的"两层"设计
- Hansen, *Changing Gods in Medieval China, 1127–1276*, Princeton UP 1990, DOI 10.1515/9781400860432（已验证）。
- Watson, "Standardizing the Gods: The Promotion of T'ien Hou ('Empress of Heaven') Along the South China Coast, 960–1960", in *Popular Culture in Late Imperial China*, DOI 10.1525/9780520340121-013（已验证，被引 106 次）。
- **反论**：Szonyi, "The Illusion of Standardizing the Gods: The Cult of the Five Emperors in Late Imperial China", *Journal of Asian Studies* 56:113–135 (1997), DOI 10.2307/2646345（已验证，被引 31 次）。
- Duara, "Superscribing Symbols: The Myth of Guandi, Chinese God of War", *JAS* 47:778–795 (1988), DOI 10.2307/2057852（已验证）。Duara 的"层累书写（superscription）"概念：新的意义被叠加到旧符号上而不抹除旧层。
- von Glahn, *The Sinister Way: The Divine and the Demonic in Chinese Religious Culture*（经三篇书评验证）。
- **对模拟的意义（这是本节最重要的一条）**：`registered_status`（国家名册/赐额/封号）与 `prevalence`（实际实践）**必须分离**。Watson 说国家成功地标准化了神祇，Szonyi 说那只是地方社群换了个官方标签、实践照旧，Duara 说新旧意义层累共存。三者都对——因为它们描述的是**不同的层**。模拟里把这三层都存下来，就自动获得 MANDATE 第 9 条要求的"世界事实 / 官方历史 / 民间叙事"三分。

### 6.7 寺院经济与国家财政 → 对应机制 F
- Gernet, *Buddhism in Chinese Society: An Economic History from the Fifth to the Tenth Centuries*（见 §3.7）。
- Ch'en, "The Sale of Monk Certificates during the Sung Dynasty", *HTR* 49:307–327 (1956), DOI 10.1017/S0017816000028315。
- von Glahn, "Modalities of the Fiscal State in Imperial China", *Journal of Chinese History* 4:1–29 (2019), DOI 10.1017/jch.2019.15（已验证存在，内容本次未读）。
- He Liqun, *Space and Function: Buddhist State Monasteries in Early Medieval China and their Impact on East Asia*, BAR 2022, DOI 10.30861/9781407358147（已验证存在）。
- **对模拟的意义**：中国史提供了完整的"免税地产积累 → 财政危机 → 出售度牒 → 限额 → 没收还俗"循环的四个环节，而且每个环节都留下了可量化的行政记录。这是校准 §3.7 最好的对象。但**具体数字本次全部未验证**。

### 6.8 一个刺眼的方法论事实
Beheim et al. (2021) 指出：整个 Seshat 数据库中，**唯一一个"在道德神首次出现之前确知不存在道德神"的观测，来自中国黄河中游**。也就是说，那个被写进 *Nature*（后被撤稿）的全球性论断，其唯一的真实负例落在我们要模拟的地理区域上，而它极可能是**书写记录出现得早**造成的观察效应，而非事实。**这一条应当被刻在项目文档最前面**：在我们的世界里，"史书没记" ≠ "没发生"。

---

## 7. 学界争议与未解决问题

1. **道德神与社会复杂度的因果方向（最激烈）**。四种立场并存：(a) 大神促进大社会（Norenzayan et al. 2016）；(b) 复杂社会先于大神（Whitehouse et al. 2019，**已撤稿**）；(c) 大神先于复杂度（Beheim et al. 2021 的重分析）；(d) 两者由战争与资源共同驱动，无直接因果（Turchin et al. 2023，即原作者团队的修正立场）。**工程解见 §3.6：不站队，建共同驱动因子。**
2. **"道德化高神"这个测量本身是否有效**。Lightner et al. 2023 主张 SCCS 的高神变量因为要求"创世/主宰"前置条件，系统性漏掉小规模社会的道德神。若成立，则(a)(b)(c) 三方共用的经验基础都要打折。**这是 C 级问题里最有可能改变结论的一个。**
3. **副产品 vs 适应**。宗教认知是心智其他功能的副产品，还是被选择的适应？Pyysiäinen & Hauser 2010 (*TiCS* 14:104–109) 综述此争。Norenzayan et al. 2016 的调和方案（副产品起源 + 文化群体选择）是目前主流，但文化群体选择本身有争议（Henrich 2004, *JEBO* 53:3–35 是主要辩护）。
4. **modes of religiosity 的二分是否成立**。Kapitány et al. 2020 的因子分析找到 7 个因子且 dysphoric/euphoric 正交，实质上否定了单一"唤起度"轴。二分法作为**形态空间上的两个密度峰**还站得住，作为**类型学**已经不太站得住。
5. **严格教会是否真的强**。Marwell 1996 的评论指出识别问题未解。严格度与存续之间的因果可能双向。
6. **富裕假说 vs 战争假说**。Baumard et al. 2015 说是经济发展（能量捕获）解释轴心时代，Turchin et al. 2023 说是战争。两者用的数据源和时间分辨率都不同，尚无直接对撞。
7. **"标准化"是真的标准化还是标签更换**。Watson vs Szonyi。这个争论对本项目特别重要，因为它决定了国家对宗教的控制力应该建模成多强。
8. **代价信号的关键实证能否复制**。公社存续研究（Sosis & Bressler 2003）是被引用最多的证据之一，但我在本次检索中无法取得其数值，也没找到独立复制。**这是一个需要下一阶段专门核验的点。**
9. **跨文化数据库的编码可靠性**。Watts et al. 2022（Lightner 文中引用，本次未取得）讨论跨文化数据库构建的系统性问题。Beheim 事件是这个问题最贵的一次演示。

---

## 8. 反模式：本领域常见的错误建模方式

1. **把缺失当作不存在**。这是 *Nature* 撤稿的直接原因（61% 缺失被重编码为 0，r = 0.97）。在我们的模拟里，这条对应两个具体禁令：(a) 历史记录层的"未记载"必须编码为 `UNKNOWN` 而非 `FALSE`；(b) 任何用真实数据库校准的脚本，都必须显式声明缺失处理策略，并跑一遍"只用现存数据 / 多重插补 / 全部当零"三种版本看结论是否翻转。
2. **把"道德化高神"当成一个标量**。至少四个独立轴：`cosmic_scope`（创世/主宰）、`moral_concern`（关心道德）、`punitiveness`（惩罚）、`strategic_omniscience`（知晓社会性策略信息）。Lightner et al. 2023 证明把前者当后三者的代理会在小规模社会大量假阴性。**合成一个"大神值"会直接把这个偏差写进内核。**
3. **单向因果："社会复杂了所以有大神"或"有大神所以社会复杂"**。原作者团队自己的修正版说是共同驱动。写成单向就是把一场未决争论固化成物理定律。
4. **人口阈值触发**（"人口过 100 万解锁一神教"）。这正是被撤稿的那个论断，且其数值来自数据处理伪影。**任何形式的"人口/科技达标解锁宗教形态"都是科技树，不是涌现。**
5. **把仪式的强度压成一个轴**。Kapitány et al. 2020：dysphoric 与 euphoric 正交。压成一轴会让"狂欢型仪式"和"苦行型仪式"变成同一个东西的强弱版本，从而丢掉两种完全不同的组织后果。
6. **让宗教变成"合作增益器"**。Watts et al. 2016 的人祭研究给出反例：宗教在南岛社会里的可测作用是**固化阶层**。Purzycki 的效应也很具体——是对"远处的同教陌生人"的**公正性**，不是泛泛的善意；Norenzayan & Shariff 2008 更指出实验效应在**声誉线索被激活**时才稳定出现。把宗教做成 +10% 全局合作是把一整个研究领域的细节抹平。
7. **国家—宗教关系做成二值（政教合一 / 分离）**。Watson vs Szonyi 的争论表明，"国家册封了这个神"和"地方实际在拜什么"是两层，中间还有 Duara 的层累书写。至少需要 `registered_status` / `prevalence` / `local_meaning_layers` 三个变量。
8. **让 LLM 决定"该有个宗教了"**。这是本项目最容易犯的错。任何 `Religion` 实例的创建都必须由 §3.3 的状态机触发，LLM 只能填内容。
9. **无界累加的状态变量**。MERV 1.0 已发表的式(2)(3) 就是这个毛病：AP/SP 每步加一个正比值，无衰减无上界，"宗教性"只能单调上升。抄别人的 ABM 时要专门检查每个状态变量有没有回复项和上下界。
10. **用"轴心时代"当剧情节拍器**。Baumard et al. 2015 确实给出了 BCE 500–300 的三区域同步现象，但机制是能量捕获，且与战争假说未对撞。把它写成"文明发展到 X 阶段必然出现禁欲道德宗教"就是剧情模板。
11. **忽略传播项的量级**。Botero 的空间邻近系数 5.867 vs 政治复杂度 0.652。如果模拟里内生生成项比传播项强，得到的世界会是一堆互不相干的独立发明，跟真实的宗教地理完全不像。
12. **把萨满/巫师建模成"低级版祭司"**。Singh 2018 的核心洞见是，萨满的辖区之所以稳固，正因为其效果**不可验证**；而工匠的辖区可以被任何做出成品的人侵入。这两者是不同的制度逻辑，不是同一条科技树的前后两级。
13. **认为宗教诞生需要一个"创教者"**。绝大多数宗教组织形态（祖先崇拜、社区历法祭、地方神祠）没有创始人。只有 CONGREGATIONAL 及之后的形态才需要一个可识别的发起人。给每个宗教强行配一个"先知 NPC"会制造大量虚假的伟人史观。

---

## 9. 无来源判断（D 级，LLM 常识，不得当作历史规律）

以下全部是我为了让模拟能跑而做的假设，或凭记忆写下但**本次未验证**的内容。使用前必须标记，且必须做成可调开关。

**凭记忆、本次未验证的"事实"**（下一阶段必须核验或删除）：
1. Sosis & Bressler 2003 的结论我记得是"宗教公社比世俗公社每年解散概率显著更低（约 4 倍差距），且代价性要求数量只在宗教公社中预测存续"。**样本量、系数、方向均未验证。**
2. Stark 在 *The Rise of Christianity* 中估计基督徒人数以约 40%/十年的复合速率增长。**未验证。**
3. 唐会昌五年（845）毁佛的数字（寺 4,600 余、还俗僧尼 260,500、招提兰若 40,000 余）。**未验证，且来自正史，本身就是需要史料批判的数字。**
4. 天师道的"二十四治"与"五斗米"税。**未验证。**
5. Boyer 的 MCI 最优违反数为 2。**未验证。**
6. Baumard et al. 2015 的能量捕获阈值约为 20,000 kcal/人/日。**未验证，不要用。**
7. 商代甲骨的出土总量级（约十几万片）。**未验证。**

**纯属我为建模而设的假设（无任何来源）**：
8. 组织形态状态机的七个状态划分（DIFFUSE / SHAMANIC / LINEAGE_CULT / CONGREGATIONAL / MONASTIC / HIERARCHICAL / STATE_CULT）是我为工程方便切的，文献里没有这套分类。它大致对应 Stark-Bainbridge 的 church/sect/cult 加上 Whitehouse 的 modes 加上中国史的经验，但**没有任何研究验证过这七个状态是穷尽且互斥的**。
9. §3.2 归因压力场 A_s 的具体加权形式与各项权重 w1..w5。Botero 给了变量清单和方向，没给这个合成公式。
10. §3.6 的 `anonymity_s` 定义（未被熟人网络监督的经济互动占比）与三个 κ 松弛速率。这是我对"Big Gods 争论"的工程折衷，**文献中没有人这样建模过**。
11. §3.8 的 schism_hazard 五项分解与 λ 系数。存在一个已发表的分裂形式模型（Maloney et al. 2009），但我没读到，所以这是自创的。
12. `doctrine_fixity` 高 → 教义争端、低 → 静默分神（"为什么中国民间信仰少产生教义性异端"）。机制上说得通，**我没有找到直接量化这个关系的研究**。
13. §3.7 财政捕食的四个响应选项（售度牒/限额/没收/征税）的划分与它们的触发阈值。四个选项在中国史上都有实例，但把它们排成一个由 `fiscal_threat` 与 `fiscal_stress` 决定的决策树是我的构造。
14. "外来宗教传入需要翻译中介成本"这一项。合理，但无量化来源。
15. 建议的时间尺度（组织形态转移每 5–10 年检查一次、仪式按年结算、捕食周期几十到百年）。纯工程选择。
16. `registered_status` / `prevalence` / `local_meaning_layers` 三层结构。这是我从 Watson–Szonyi–Duara 三方争论里抽出来的工程折衷，**三方本人都没有提出过这个三层模型**。
17. 把 Whitehouse et al. 2017 的群体存活方程 `S_j = h·E_j + (1−h)·P_j` 直接用于聚落尺度的战争胜负。原文是演化博弈的抽象群体，不是地理聚落。
18. 建议把 Botero 的 logit 直接当模拟内的"先验强度"（尤其是那个 5.867 的邻近系数）。原研究是**横断面的、以民族志采样时点为准的**，把它当动力学方程的系数在方法论上是有跳跃的。

---

## 10. 参考文献

标记：**[V]** = 本次检索中通过 Crossref / OpenAlex / Europe PMC / Unpaywall / 全文抓取**实际看到**书目元数据者；**[VF]** = 全文或摘要正文本次实际读到；**[R]** = 凭记忆写下，本次未验证。

### 认知宗教学
1. **[V][VF]** Barrett, J. L. (2000). Exploring the natural foundations of religion. *Trends in Cognitive Sciences* 4(1):29–34. DOI 10.1016/S1364-6613(99)01419-9
2. **[V]** Barrett, J. L., & Keil, F. C. (1996). Conceptualizing a Nonnatural Entity: Anthropomorphism in God Concepts. *Cognitive Psychology* 31(3):219–247. DOI 10.1006/cogp.1996.0017
3. **[V]** Boyer, P., & Ramble, C. (2001). Cognitive templates for religious concepts: cross-cultural evidence for recall of counter-intuitive representations. *Cognitive Science* 25(4):535–564. DOI 10.1207/s15516709cog2504_2
4. **[V]** Norenzayan, A., Atran, S., Faulkner, J., & Schaller, M. (2006). Memory and Mystery: The Cultural Selection of Minimally Counterintuitive Narratives. *Cognitive Science* 30(3):531–553. DOI 10.1207/s15516709cog0000_68
5. **[V]** Guthrie, S. E. (1993). *Faces in the Clouds: A New Theory of Religion*. Oxford UP.（经三篇书评验证：DOI 10.2307/1386639；10.2307/3712008；10.2307/3511546）
6. **[V]** Boyer, P. (2001). *Religion Explained: The Evolutionary Origins of Religious Thought*. Basic Books.（经书评验证：DOI 10.1093/jaar/71.3.671）
7. **[V]** Atran, S., & Norenzayan, A. (2004). Religion's evolutionary landscape: Counterintuition, commitment, compassion, communion. *Behavioral and Brain Sciences* 27(6):713–730. DOI 10.1017/S0140525X04000172
8. **[V]** Willard, A. K., & Norenzayan, A. (2013). Cognitive biases explain religious belief, paranormal belief, and belief in life's purpose. *Cognition* 129(2):379–391. DOI 10.1016/j.cognition.2013.07.016
9. **[V]** Pyysiäinen, I., & Hauser, M. (2010). The origins of religion: evolved adaptation or by-product? *Trends in Cognitive Sciences* 14(3):104–109. DOI 10.1016/j.tics.2009.12.007

### 萨满、巫术、专业化
10. **[V][VF]** Singh, M. (2018). The cultural evolution of shamanism. *Behavioral and Brain Sciences* 41. DOI 10.1017/S0140525X17001893 **[已核验]**
11. **[V][VF]** Singh, M. (2021). Magic, Explanations, and Evil: On the Origins and Design of Witches and Sorcerers. *Current Anthropology* 62(1):2–29. DOI 10.1086/713111

### 仪式、代价信号、CREDs、身份融合
12. **[V]** Sosis, R. (2000). Religion and Intragroup Cooperation: Preliminary Results of a Comparative Analysis of Utopian Communities. *Cross-Cultural Research* 34(1):70–87. DOI 10.1177/106939710003400105
13. **[V]** Sosis, R., & Bressler, E. R. (2003). Cooperation and Commune Longevity: A Test of the Costly Signaling Theory of Religion. *Cross-Cultural Research* 37(2):211–239. DOI 10.1177/1069397103037002003 —— **元数据已验证，正文与数值本次未取得** **[已核验]** —— 元数据核验通过；正文数值仍未取得，不得引用其数字
14. **[V]** Sosis, R., & Ruffle, B. J. (2003). Religious Ritual and Cooperation: Testing for a Relationship on Israeli Religious and Secular Kibbutzim. *Current Anthropology* 44(5):713–722. DOI 10.1086/379260
15. **[V]** Sosis, R., & Alcorta, C. (2003). Signaling, solidarity, and the sacred: The evolution of religious behavior. *Evolutionary Anthropology* 12(6):264–274. DOI 10.1002/evan.10120
16. **[V]** Sosis, R., Kress, H., & Boster, J. (2007). Scars for war: evaluating alternative signaling explanations for cross-cultural variance in ritual costs. *Evolution and Human Behavior* 28(4):234–247. DOI 10.1016/j.evolhumbehav.2007.02.007
17. **[V]** Sosis, R. (2004). The Adaptive Value of Religious Ritual. *American Scientist* 92:166. DOI 10.1511/2004.46.928 —— 正文本次未取得
18. **[V]** Henrich, J. (2009). The evolution of costly displays, cooperation and religion: credibility enhancing displays and their implications for cultural evolution. *Evolution and Human Behavior* 30(4):244–260. DOI 10.1016/j.evolhumbehav.2009.03.005
19. **[V]** Lanman, J. A., & Buhrmester, M. D. (2017). Religious actions speak louder than words: exposure to credibility-enhancing displays predicts theism. *Religion, Brain & Behavior* 7(1):3–16. DOI 10.1080/2153599X.2015.1117011
20. **[V]** Bulbulia, J., & Sosis, R. (2011). Signalling theory and the evolution of religious cooperation. *Religion* 41(3):363–388. DOI 10.1080/0048721X.2011.604508
21. **[V]** Whitehouse, H., & Lanman, J. A. (2014). The Ties That Bind Us: Ritual, Fusion, and Identification. *Current Anthropology* 55(6):674–695. DOI 10.1086/678698
22. **[V][VF]** Whitehouse, H., Jong, J., Buhrmester, M. D., Gómez, Á., Bastian, B., Kavanagh, C. M., Newson, M., Matthews, M., Lanman, J. A., McKay, R., & Gavrilets, S. (2017). The evolution of extreme cooperation via shared dysphoric experiences. *Scientific Reports* 7:44292. DOI 10.1038/srep44292
23. **[V]** Xygalatas, D., Khan, S., Lang, M., Kundt, R., Kundtová-Klocová, E., et al. (2019). Effects of Extreme Ritual Practices on Psychophysiological Well-Being. *Current Anthropology* 60(5):699–707. DOI 10.1086/705665
24. **[V]** Atkinson, Q. D., & Whitehouse, H. (2011). The cultural morphospace of ritual form: Examining modes of religiosity cross-culturally. *Evolution and Human Behavior* 32(1):50–62. DOI 10.1016/j.evolhumbehav.2010.09.002
25. **[V][VF]** Kapitány, R., Kavanagh, C., & Whitehouse, H. (2020). Ritual morphospace revisited: the form, function and factor structure of ritual practice. *Phil. Trans. R. Soc. B* 375:20190436. DOI 10.1098/rstb.2019.0436 **[已核验]**
26. **[V]** Whitehouse, H. (2004). *Modes of Religiosity: A Cognitive Theory of Religious Transmission*. AltaMira Press.（经三篇书评验证，含 DOI 10.1525/aa.2006.108.1.261）
27. **[V]** Rappaport, R. A. (1999). *Ritual and Religion in the Making of Humanity*. Cambridge UP. DOI 10.1017/CBO9780511814686

### 大神、道德神与撤稿争议
28. **[V][VF]** Norenzayan, A., Shariff, A. F., Gervais, W. M., Willard, A. K., McNamara, R. A., Slingerland, E., & Henrich, J. (2016). The cultural evolution of prosocial religions. *Behavioral and Brain Sciences* 39. DOI 10.1017/S0140525X14001356
29. **[V][VF]** Purzycki, B. G., Apicella, C., Atkinson, Q. D., Cohen, E., McNamara, R. A., et al. (2016). Moralistic gods, supernatural punishment and the expansion of human sociality. *Nature* 530:327–330. DOI 10.1038/nature16980 **[已核验]**
30. **[V]** Norenzayan, A., & Shariff, A. F. (2008). The Origin and Evolution of Religious Prosociality. *Science* 322(5898):58–62. DOI 10.1126/science.1158757
31. **[V]** Shariff, A. F., & Norenzayan, A. (2007). God Is Watching You: Priming God Concepts Increases Prosocial Behavior in an Anonymous Economic Game. *Psychological Science* 18(9):803–809. DOI 10.1111/j.1467-9280.2007.01983.x
32. **[V]** **【已撤稿】** Whitehouse, H., François, P., Savage, P. E., Currie, T. E., Feeney, K. C., Cioni, E., Purcell, R., Ross, R. M., et al. (2019). Complex societies precede moralizing gods throughout world history. *Nature* 568(7751):226–229. DOI 10.1038/s41586-019-1043-4 —— Crossref 现标记为 RETRACTED ARTICLE **[已核验]**
33. **[V]** Retraction Note: Complex societies precede moralizing gods throughout world history (2021). *Nature* 595(7866):320. DOI 10.1038/s41586-021-03656-3 —— 撤稿日期 2021-07-07 **[已核验]**
34. **[V][VF]** Beheim, B., Atkinson, Q. D., Bulbulia, J., Gervais, W., Gray, R. D., Henrich, J., Lang, M., Monroe, M. W., et al. (2021). Treatment of missing data determined conclusions regarding moralizing gods. *Nature* 595(7866):E29–E34. DOI 10.1038/s41586-021-03655-4 **[已核验]**
35. **[V][VF]** Turchin, P., Whitehouse, H., Larson, J., Cioni, E., Reddish, J., Hoyer, D., Savage, P. E., Covey, A., et al. (2023). Explaining the rise of moralizing religions: a test of competing hypotheses using the Seshat Databank. *Religion, Brain & Behavior* 13(2):167–194. DOI 10.1080/2153599X.2022.2065345 **[已核验]**
36. **[V][VF]** Lightner, A. D., Bendixen, T., & Purzycki, B. G. (2023). Moralistic supernatural punishment is probably not associated with social complexity. *Evolution and Human Behavior* 44(6):555–565. DOI 10.1016/j.evolhumbehav.2022.10.006 **[已核验]**
37. **[V]** Bendixen, T., Lightner, A. D., Apicella, C., Atkinson, Q., Bolyanatz, A., et al. (2023). Gods are watching and so what? Moralistic supernatural punishment across 15 cultures. *Evolutionary Human Sciences* 5. DOI 10.1017/ehs.2023.15
38. **[V]** Slingerland, E., Monroe, M. W., Spicer, R., & Muthukrishna, M. (2019). Historians Respond to Whitehouse et al. (2019). Preprint, DOI 10.31234/osf.io/2amjz
39. **[V]** Larson, J., Whitehouse, H., François, P., Hoyer, D., & Turchin, P. (2024). Moralizing Supernatural Punishment and Reward. *Journal of Cognitive Historiography* 8:168–183. DOI 10.1558/jch.25994
40. **[V]** Rüpke, J. (2022). Big Gods and Big Rituals. *Journal of Cognitive Historiography* 6. DOI 10.1558/jch.39885
41. **[V]** Patzelt, M. (2022). How Complex were Ancient Societies and Religions? *Journal of Cognitive Historiography* 6. DOI 10.1558/jch.39573
42. **[V][VF]** Botero, C. A., Gardner, B., Kirby, K. R., Bulbulia, J., Gavin, M. C., & Gray, R. D. (2014). The ecology of religious beliefs. *PNAS* 111(47):16784–16789. DOI 10.1073/pnas.1408701111 **[已核验]**
43. **[V][VF]** Watts, J., Greenhill, S. J., Atkinson, Q. D., Currie, T. E., Bulbulia, J., & Gray, R. D. (2015). Broad supernatural punishment but not moralizing high gods precede the evolution of political complexity in Austronesia. *Proc. R. Soc. B* 282:20142556. DOI 10.1098/rspb.2014.2556 **[已核验]**
44. **[V][VF]** Watts, J., Sheehan, O., Atkinson, Q. D., Bulbulia, J., & Gray, R. D. (2016). Ritual human sacrifice promoted and sustained the evolution of stratified societies. *Nature* 532(7598):228–231. DOI 10.1038/nature17159 **[已核验]**
45. **[V][VF]** Baumard, N., Hyafil, A., Morris, I., & Boyer, P. (2015). Increased Affluence Explains the Emergence of Ascetic Wisdoms and Moralizing Religions. *Current Biology* 25(1):10–15. DOI 10.1016/j.cub.2014.10.063 **[已核验]**
46. **[V][VF]** Baumard, N., & Boyer, P. (2013). Explaining moral religions. *Trends in Cognitive Sciences* 17(6):272–280. DOI 10.1016/j.tics.2013.04.003
47. **[V]** Johnson, D. D. P. (2005). God's punishment and public goods. *Human Nature* 16(4):410–446. DOI 10.1007/s12110-005-1017-0 —— 正文与数值本次未取得
48. **[V]** Atran, S., & Henrich, J. (2010). The Evolution of Religion: How Cognitive By-Products, Adaptive Learning Heuristics, Ritual Displays, and Group Competition Generate Deep Commitments to Prosocial Religions. *Biological Theory* 5(1):18–30. DOI 10.1162/biot_a_00018
49. **[V]** Norenzayan, A. (2013). *Big Gods: How Religion Transformed Cooperation and Conflict*. Princeton UP.（经书评验证：DOI 10.5860/choice.51-5544；10.5334/snr.an）

### 宗教经济学与组织
50. **[V]** Iannaccone, L. R. (1988). A Formal Model of Church and Sect. *American Journal of Sociology* 94:S241–S268. DOI 10.1086/228948
51. **[V]** Iannaccone, L. R. (1992). Sacrifice and Stigma: Reducing Free-riding in Cults, Communes, and Other Collectives. *Journal of Political Economy* 100(2):271–291. DOI 10.1086/261818
52. **[V]** Iannaccone, L. R. (1994). Why Strict Churches Are Strong. *American Journal of Sociology* 99(5):1180–1211. DOI 10.1086/230409
53. **[V]** Marwell, G. (1996). We Still Don't Know if Strict Churches are Strong, Much Less Why: Comment on Iannaccone. *AJS* 101(4):1097–1103. DOI 10.1086/230792
54. **[V][VF]** Berman, E. (2000). Sect, Subsidy, and Sacrifice: An Economist's View of Ultra-Orthodox Jews. *Quarterly Journal of Economics* 115(3):905–953. DOI 10.1162/003355300554944 —— 工作论文版 NBER WP6715, DOI 10.3386/w6715，**全文已抓取** **[已核验]**
55. **[V]** Berman, E., & Laitin, D. D. (2008). Religion, terrorism and public goods: Testing the club model. *Journal of Public Economics* 92(10–11):1942–1967. DOI 10.1016/j.jpubeco.2008.03.007
56. **[V]** Stark, R., & Bainbridge, W. S. (1979). Of Churches, Sects, and Cults: Preliminary Concepts for a Theory of Religious Movements. *JSSR* 18(2):117. DOI 10.2307/1385935
57. **[V]** Stark, R., & Bainbridge, W. S. (1980). Networks of Faith: Interpersonal Bonds and Recruitment to Cults and Sects. *AJS* 85(6):1376–1395. DOI 10.1086/227169
58. **[V]** Stark, R. (1996). *The Rise of Christianity: A Sociologist Reconsiders History*. Princeton UP.（经三篇书评验证：DOI 10.2307/1386421；10.2307/1061256；10.2307/3711877）—— **正文与增长率数字本次未验证**
59. **[V]** Maloney, M. T., Civan, A., & Maloney, M. F. (2009). Model of religious schism with application to Islam. *Public Choice* 142(3–4):441–460. DOI 10.1007/s11127-009-9533-9 —— **内容本次未取得**
60. **[V]** Henrich, J. (2004). Cultural group selection, coevolutionary processes and large-scale cooperation. *JEBO* 53(1):3–35. DOI 10.1016/S0167-2681(03)00094-5

### 计算模型 / ABM
61. **[V][VF]** Shults, F. L., Gore, R., Wildman, W. J., Lynch, C., Lane, J. E., & Toft, M. (2018). A Generative Model of the Mutual Escalation of Anxiety Between Religious Groups. *JASSS* 21(4):7. DOI 10.18564/jasss.3840 —— 全文已抓取 **[已核验]**
62. **[V]** Lane, J. E. (2018). Strengthening the supernatural punishment hypothesis through computer modeling. *Religion, Brain & Behavior* 8(3):290–300. DOI 10.1080/2153599X.2017.1302977
63. **[V]** Bainbridge, W. S. (1995). Neural Network Models of Religious Belief. *Sociological Perspectives* 38(4):483–495. DOI 10.2307/1389269
64. **[V]** Bainbridge, W. S. (2014). Artificial Intelligence Models of Religious Evolution. In *Evolution, Religion, and Cognitive Science*. DOI 10.1093/acprof:oso/9780199688081.003.0012

### 数据库
65. **[V]** Turchin, P., Brennan, R., Currie, T., Feeney, K., François, P., et al. (2015). Seshat: The Global History Databank. *Cliodynamics* 6. DOI 10.21237/C7CLIO6127917
66. **[V][VF]** Turchin, P., Currie, T. E., Whitehouse, H., François, P., Feeney, K., et al. (2018). Quantitative historical analysis uncovers a single dimension of complexity that structures global variation in human social organization. *PNAS* 115(2):E144–E151. DOI 10.1073/pnas.1708800115
67. **[V]** Slingerland, E., & Sullivan, B. (2017). Durkheim with Data: The Database of Religious History. *Journal of the American Academy of Religion* 85(2):312–347. DOI 10.1093/jaarel/lfw012
68. **[VF]** D-PLACE (d-place.org)，许可 CC BY-NC 4.0（2026-09 抓取网站页脚）
69. **[VF]** Seshat 数据库网站（seshat-db.com，2026-09 抓取）

### 中国与东亚
70. **[V]** Keightley, D. N. (1978). *Sources of Shang History: The Oracle-Bone Inscriptions of Bronze Age China*. UC Press.（经三篇书评验证：DOI 10.2307/602342；10.2307/495348；10.2307/1861634）
71. **[V]** Keightley, D. N. (1988). Shang Divination and Metaphysics. *Philosophy East and West* 38(4):367. DOI 10.2307/1399117
72. **[V]** Puett, M. J. (2002). *To Become a God: Cosmology, Sacrifice, and Self-Divinization in Early China*. Harvard UP.（经三篇书评验证：DOI 10.2307/25066751；10.1086/529803；10.1086/491341）
73. **[V]** Li Zehou（trans. R. A. Carleo）(2018). From Shamanism to Ritual Regulations. In *The Origins of Chinese Thought*. Brill. DOI 10.1163/9789004379626_005
74. **[V]** Ivanhoe, P. J. (2004). "Heaven's Mandate" and the Concept of War in Early Confucianism. DOI 10.1017/CBO9780511606861.016
75. **[V]** Grundmann, J. P. (2021). Mandate of Heaven. *The Encyclopedia of Ancient History*. DOI 10.1002/9781119399919.eahaa00775
76. **[V]** Zürcher, E. (1959). *The Buddhist Conquest of China: The Spread and Adaptation of Buddhism in Early Medieval China*. Brill.（经 *AHR* 书评验证：DOI 10.2307/1846312）
77. **[V]** Gernet, J. (trans. F. Verellen). *Buddhism in Chinese Society: An Economic History from the Fifth to the Tenth Centuries*. Columbia UP.（经三篇书评验证：DOI 10.2307/605237；10.2307/2761291；10.1353/cri.2000.0023）
78. **[V]** Ch'en, K. (1956). The Sale of Monk Certificates during the Sung Dynasty: A Factor in the Decline of Buddhism in China. *Harvard Theological Review* 49(4):307–327. DOI 10.1017/S0017816000028315
79. **[V]** von Glahn, R. (2019). Modalities of the Fiscal State in Imperial China. *Journal of Chinese History* 4(1):1–29. DOI 10.1017/jch.2019.15
80. **[V]** He, L. (2022). *Space and Function: Buddhist State Monasteries in Early Medieval China and their Impact on East Asia*. BAR. DOI 10.30861/9781407358147
81. **[V]** Kleeman, T. F. (2016). *Celestial Masters: History and Ritual in Early Daoist Communities*. Harvard UP.（经三篇书评验证：DOI 10.1080/1547402X.2017.1369249；10.1080/15299104.2016.1250456；10.1007/s11712-017-9582-6）
82. **[V]** Kohn, L. (2017). *Monastic Life in Medieval Daoism*. University of Hawaii Press. DOI 10.1515/9780824841669
83. **[V]** Hansen, V. (1990). *Changing Gods in Medieval China, 1127–1276*. Princeton UP. DOI 10.1515/9781400860432
84. **[V]** Watson, J. L. (1985). Standardizing the Gods: The Promotion of T'ien Hou ("Empress of Heaven") Along the South China Coast, 960–1960. In *Popular Culture in Late Imperial China*. UC Press. DOI 10.1525/9780520340121-013
85. **[V]** Szonyi, M. (1997). The Illusion of Standardizing the Gods: The Cult of the Five Emperors in Late Imperial China. *Journal of Asian Studies* 56(1):113–135. DOI 10.2307/2646345 **[已核验]**
86. **[V]** Duara, P. (1988). Superscribing Symbols: The Myth of Guandi, Chinese God of War. *Journal of Asian Studies* 47(4):778–795. DOI 10.2307/2057852
87. **[V]** von Glahn, R. (2004). *The Sinister Way: The Divine and the Demonic in Chinese Religious Culture*. UC Press.（经三篇书评验证：DOI 10.1086/ahr.110.3.770；10.5860/choice.42-2368；10.1353/cri.2005.0091）
88. **[V]** Freedman, M. (1958/2021). *Lineage Organization in Southeastern China*. Routledge. DOI 10.4324/9781003135296
89. **[V]** Faure, D. (2007). *Emperor and Ancestor: State and Lineage in South China*. Stanford UP.（经书评验证：DOI 10.5860/choice.45-3344；10.1353/cri.2011.0026）
90. **[V]** Gerritsen, A. (2000). Visions of Local Culture: Tales of the Strange and Temple Inscriptions from Song-Yuan Jizhou. *Journal of Chinese Religions* 28:69–92. DOI 10.1179/073776900805306685
91. **[V]** Foltz, R. (2010). Buddhism and the Silk Road. In *Religions of the Silk Road*. Palgrave. DOI 10.1057/9780230109100_3
92. **[V]** Clart, P. (2012). Chinese Popular Religion. In *The Wiley-Blackwell Companion to Chinese Religions*. DOI 10.1002/9781444361995.ch10

### 其他
93. **[V]** Cauvin, J. (trans. T. Watkins). *The Birth of the Gods and the Origins of Agriculture*. Cambridge UP.（经书评验证：DOI 10.5860/choice.39-0386；10.2307/1357690）

---

## 附：检索覆盖说明

**做了什么**：由于本会话的 WebSearch 配额在开始前已耗尽（200/200），全部检索改由 HTTP API 完成：Crossref REST（`query.title` 精确题名检索 + DOI 直查，含 `updated-by` 撤稿关系）、OpenAlex、Semantic Scholar Graph、Europe PMC（`resultType=core` 取摘要）、Unpaywall（找 OA 副本），以及对 PMC / JASSS / NBER / Keele / Kent 仓储的直接全文抓取。共执行约 60 次题名检索与约 40 次 DOI/全文抓取。

**全文实际读到的**：Botero et al. 2014（PNAS 全文，含表 2、表 3 全部系数与方法节）、Lightner et al. 2023（EHB 全文前 4 页）、Shults et al. 2018（JASSS 全文，含全部方程与参数表）、Whitehouse et al. 2017（Sci Rep 前 6 页，含数学模型）、Berman NBER WP6715（摘要 + 第 III 节俱乐部品模型全文，需自写字形解码器）、Kapitány et al. 2020（经 PMC 提取关键数字）、Watts et al. 2015（经 PMC 提取 BF 值）、Turchin et al. 2018（经 PMC 提取 PC1 与样本量）、Beheim et al. 2021（Semantic Scholar 全摘要，含所有关键数字）、Purzycki 2016 / Baumard 2015 / Watts 2016 / Baumard & Boyer 2013 / Singh 2018 / Norenzayan 2016 摘要（Europe PMC）。

**被付费墙挡住的**：Sosis & Bressler 2003（Sage，非 OA，**这是本简报最重要的缺口**）；Iannaccone 1988/1992/1994（Chicago Journals，非 OA）；Johnson 2005（Springer 403）；Maloney et al. 2009（Springer 403）；Turchin et al. 2023 全文（Taylor & Francis 与两个仓储均被 Cloudflare 阻断，只取到摘要）；Atkinson & Whitehouse 2011（Elsevier，只经 2020 年重分析间接取得数值）；Szonyi 1997、Watson 1985、Hansen 1990、Gernet、Zürcher、Ch'en 1956（全部为专著/JSTOR，只验证元数据）。

**检索不足之处**：
1. **中国与东亚部分的量化证据几乎全部缺失**。所有中文史料相关的数字（僧道人数、寺产、度牒售价、赐额数量）本次一个也没验证到。§6 目前只有机制方向，没有参数。**建议下一阶段单独立一个 brief 专门做"中国宗教的量化史料"。**
2. **宗教分裂（schism）的形式化文献只找到一篇且未读到内容**。§3.8 基本是自创的，证据等级 C，风险最高。
3. **代价信号的核心实证未验证**。这直接影响 §3.4 回报侧的可信度。
4. **DRH 数据库的条目数、变量结构与许可未能确认**（网站为纯前端 JS 应用，API 未公开）。
5. **未检索的相关领域**：宗教与人口（生育率差异导致的宗教人口结构变迁，Kaufmann 一系）、宗教与识字/教育、宗教法（教会法 vs 世俗法的管辖权竞争）、朝圣与市场（宗教节庆作为周期性市场）、宗教与疾病（隔离规范的流行病学后果）。这几块对本项目都有直接价值，建议后续补。
