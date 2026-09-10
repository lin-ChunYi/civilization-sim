# Agent-Based Modeling 方法论、工具链与验证

- **slug**: `abm-methodology`
- **一句话范围**: ABM 作为方法论本身——如何描述（ODD/ODD+D/TRACE）、如何验证（V&V、docking、POM）、如何在参数未知时校准（history matching / ABC / emulator / GA / iGSS）、如何证明"涌现"不是把结论写进参数、以及在什么平台上跑数千年模拟是工程可行的。
- **写作日期**: 2026-09-09
- **检索工具**: WebSearch + WebFetch（200 次搜索预算用尽）；部分 PDF 由本地 pypdf 全文抽取后逐段阅读
- **本文档中的标注约定**:
  - `[全文]` = 我抽取/读到了论文正文相关段落
  - `[页面]` = 我读到了出版方/期刊的 HTML 全文页
  - `[摘要]` = 我只读到摘要或检索结果摘要，未读正文
  - `[记忆]` = 凭记忆写下、本次检索未确认（在参考文献里标 `recalled_not_verified`）

---

## 1. 本简报要回答的问题

针对 MANDATE.md 中的 Phase 0 待答问题，本领域负责回答其中的方法论部分：

1. **如何产生真正的涌现，而不是隐藏的剧情树？** —— 需要一套可执行的"涌现认证"程序，而不是靠作者宣称。
2. **如何验证一个重大历史事件在逻辑上成立？** —— 需要区分 verification（代码符合概念模型）与 validation（概念模型符合世界），并给出两者各自的可执行步骤。
3. **如何处理我们无法获得准确历史参数的问题？** —— 需要一套"不求点估计、只求排除不可信区域"的校准范式（history matching + ABC + emulator），以及在参数完全无来源时的降级策略（POM 弱模式约束 + 参数活性测试 + 对抗式敏感性分析）。
4. **如何防止模型为了戏剧性制造事件？** —— 需要把 LLM 的输出限制成"提案"而非"结果"，并对每个提案留下可审计的证据链；需要"外生输入审计"防止我们像 Artificial Anasazi 一样，把外生驱动的拟合当成内生解释。
5. **如何衡量一个模拟世界是否"合理但不必真实"？** —— Pattern-Oriented Modeling（POM）的多模式、多尺度弱约束思想，以及"分布对齐"而不是"曲线拟合"的判据。
6. **如何让数千年的模拟在计算成本上可行？** —— 多层级/变粒度 ABM（Zoom / Russian Dolls / Collaboration 三类范式）+ 平台规模上限的真实数字。
7. **如何保证未来可以重放、分叉和比较不同历史线？** —— counter-based RNG + 内容寻址快照 + 显式调度顺序 + 决策缓存。
8. **哪些事情绝对不能让 LLM 直接决定？** —— 现有文献（Larooij & Törnberg 2025）给出的答案是：凡是需要被验证的量都不能交给 LLM 独占，因为 LLM 的黑箱性、文化偏置与随机性会让验证问题变得比传统 ABM 更难而不是更容易。

**本简报特别回答的三个专项问题**（在第 3、6、7、8 节展开）：
- 一个号称"涌现"的 ABM 如何被证明不是把结论写进了参数？
- Artificial Anasazi 被批评为"用外生降水序列拟合出人口曲线"对我们意味着什么？
- 多尺度/变粒度 ABM 有哪些成熟做法？

---

## 2. 已有成熟模型与理论

### 2.1 ODD protocol（Overview, Design concepts, Details）及其两次更新

- **核心机制**: 一个纯文本的模型描述标准，把 ABM 描述固定为七个元素，强制作者把"实体/状态变量/尺度""过程与调度""设计概念""初始化""输入数据""子模型"分开写清。2020 年第二次更新的核心新增是 **Purpose and patterns**：要求作者在"目的"里显式列出模型必须再现的模式（patterns），从而把 ODD 与 POM 缝在一起。
- **七元素**（2020 版）: (1) Purpose and patterns; (2) Entities, state variables and scales; (3) Process overview and scheduling; (4) Design concepts; (5) Initialization; (6) Input data; (7) Submodels。`[页面]`
- **设计概念清单**（Design concepts）: Basic principles / Emergence / Adaptation / Objectives / Learning / Prediction / Sensing / Interaction / Stochasticity / Collectives / Observation。我读到的页面摘要列出 11 项，其中把 "Basic principles" 归入并留了领域自定义扩展位。`[页面]`（注意：Emergence 在 ODD 里是**必须显式声明**的一项——作者必须写清"哪些结果是涌现出来的、哪些是被强加的"。这一条直接对应本项目的核心诉求。）
- **形式化程度**: 半形式化。ODD 是给人读的自然语言模板，不是可执行规范。2020 版明确提出的原则是 **"Describe what the program does, not what you think the model does."** `[页面]`
- **2020 版新增的三种变体**（对长期项目极其有用）:
  - **Summary ODD**：正文里写叙事化摘要，完整 ODD 放补充材料；
  - **Nested ODD**：复杂模型按子模型层层嵌套描述；
  - **Delta ODD**：只描述相对已发布版本的差异——这正是我们跨百次迭代时需要的版本化描述格式。`[页面]`
- **可复现建议**: ODD 各节应超链接到源码位置；记录编译器/库版本与操作系统；文档与实现之间保持命名一致；用 copyleft 声明允许再用。`[页面]`
- **已知局限**: 纯文本描述天然有歧义。有后续工作（arXiv 上的 VISA 协议提案）明确批评"现有协议以文本为中心，自然语言叙述不可避免地带来歧义和解释差异，即使有 ODD，读者也常常无法提取到足以独立重实现的精确规格"`[摘要]`。这一批评与 Kehoe（2016）对 Sugarscape 的形式化结果完全一致（见 2.7）。
- **出处**: Grimm et al. 2006（原始）`[记忆]`；Grimm et al. 2010（第一次更新，Ecological Modelling）`[摘要]`；Grimm, Railsback, Vincenot, Berger, Gallagher, DeAngelis, ..., Ayllón (2020) JASSS 23(2):7, doi:10.18564/jasss.4259 `[页面]`。

### 2.2 ODD+D：把"人的决策"补进 ODD

- **核心机制**: 在 ODD 之上增加对**人类决策模型**的强制描述——决策的理论/经验依据、个体的学习与适应、社会规范、集体决策、异质性、随机性来源。动机是"在 ABM 中表示人类决策具有根本重要性，但选择某个特定人类决策模型的理由在模型文档中往往缺乏充分的经验或理论支撑"。
- **对本项目的意义**: 这正是我们"规则与 AI 分离"原则需要的文档格式——ODD+D 会逼我们对每一个 LLM agent 的决策模块写出"它凭什么这样决策"。
- **出处**: Müller, Bohn, Dreßler, Groeneveld, Klassert, Martin, Schlüter, Schulze, Weise, Schwarz (2013) *Environmental Modelling & Software* 48: 37–48, doi:10.1016/j.envsoft.2013.06.003 `[摘要]`。

### 2.3 TRACE / "evaludation"：把整个建模过程留档

- **核心机制**: TRACE = TRAnsparent and Comprehensive model Evaludation。它不是描述"模型是什么"，而是描述"模型是怎么被建立、测试、分析和使用的"，用一本"建模笔记本"组织成 **8 个元素**：Problem formulation、Model description、Data evaluation、Conceptual model evaluation、Implementation verification、Model output verification、Model analysis and application、Model output corroboration。`[摘要]`
- **"evaludation"** 一词定义为"在模型开发、分析和应用的所有阶段中建立模型质量与可信度的整个过程"（Augusiak et al. 2014 提出，Grimm et al. 2014 采纳）。`[摘要]`
- **对本项目的意义**: 本项目的 Phase 0 成功标准（"未来发生一个荒诞事件时可以解释它为什么发生"）本质上是一个 TRACE 要求：**除了世界内的因果链，我们还需要一条"模型自身的因果链"**——为什么这条规则长这样、它通过了哪些测试、它的参数从哪来。建议把 research/briefs/ 之后的所有内容组织成一个 TRACE notebook。
- **出处**: Grimm et al. (2014) "Towards better modelling and decision support: Documenting model development, testing, and analysis using TRACE" `[摘要]`；Schmolke et al. 2010 `[记忆]`；Augusiak, Van den Brink & Grimm 2014 `[摘要]`；CoMSES Net 官方推荐 ODD + TRACE 组合 `[页面]`。

### 2.4 Pattern-Oriented Modeling（POM）—— 本项目最重要的方法论基石

- **核心机制**: 不用单一宏观曲线拟合模型，而是**同时使用多个在不同尺度、不同层级（个体级与系统级）上观测到的模式**来指导模型结构设计、参数化和检验。原文表述："This approach uses multiple observed patterns, at different scales and at both individual and system levels, to guide model design, parameterization, and testing."`[摘要]`
- **形式化程度**: 定性策略 + 半定量判据。POM 的三个用途在文献中被反复引用为：(a) 用模式决定模型需要多复杂（结构现实主义）；(b) 用多个弱模式同时约束来做**逆向参数化**（inverse modelling），把不可直接测量的参数间接定住；(c) 用"哪个子模型能同时通过全部模式"来做**理论选择**（contrasting theories）。`[摘要]` + 2020 ODD 页面确认 POM 与 ODD 的耦合 `[页面]`
- **为什么对我们决定性**: 我们的目标不是复刻真实历史，所以**不能**用"人口曲线拟合"做验证。POM 提供了唯一在方法论上站得住的替代：定义一批"任何合理文明都应该表现出来的、弱的、序数化的模式"（例如：聚落规模分布右偏且随复杂度上升更陡；战争规模分布重尾；技术扩散呈 S 形且速率受地形阻隔调制；国家寿命分布无特征尺度；等等），然后要求虚拟文明**同时**通过其中足够多条。单条弱模式很容易被过参数化模型伪造，一批弱模式同时通过则很难。
- **已知局限**: POM 没有给出"多少条模式才够""模式之间如何加权"的量化标准；实践中仍是作者判断。文献未提供可用的量化阈值。
- **出处**: Grimm, Revilla, Berger, Jeltsch, Mooij, Railsback, Thulke, Weiner, Wiegand, DeAngelis (2005) *Science* 310(5750): 987–991, doi:10.1126/science.1116681 `[摘要]`。

### 2.5 Sargent 的 V&V 范式 + Rand & Rust（2011）的 ABM 专用规范

Sargent 在多届 Winter Simulation Conference 上给出了一个"图形范式"，把 verification 与 validation 挂到模型开发流程的各个环节上（problem entity ↔ conceptual model ↔ computerized model 三角形，边上分别是 conceptual model validation / computerized model verification / operational validation，中间是 data validity）。`[摘要]`（该三角图的具体形状我凭记忆熟悉，但本次只读到会议论文的摘要级描述，故三角图细节标 `[记忆]`。）

**Rand & Rust (2011)** 给出了目前最可直接落地的 ABM 专用清单。我读了全文，以下是**逐字级**的结构：

**开发四步**: Step 1 Decide if ABM is appropriate → Step 2 Design the model（scope / agents / properties / behaviours / environment / input & output / time step）→ Step 3 Construct the model → Step 4 Analyze the model。`[全文]`

**Verification（实现 ↔ 概念模型）三步**:
1. **Documentation** —— 概念设计与实现都要有文档，且代码内注释要细到"一个不熟练的程序员也能把代码注释与概念文档对上"。
2. **Programmatic testing** —— 四种手段：*unit testing*、*code walkthroughs*（团队走查）、*debugging walkthroughs*（单步执行核对）、*formal testing*（用逻辑证明正确性；原文承认大多数 ABM 复杂到形式化测试"difficult"）。
3. **Test cases and scenarios**（不使用数据）—— 四类：*corner cases*（极值）、*sampled cases*（抽样参数）、*specific scenarios*（已知输出的特定输入）、*relative value testing*（检查输入→输出的单调/方向关系）。
`[全文]`

**Validation（实现 ↔ 现实）四步**:
1. **Micro-face validation** —— 机制与属性"表面上"对应现实：模型里的个体是否有意义地对应真实个体？它拥有的行动是否对应真实行动？**它拥有的信息量是否现实？**（原文："Do consumer agents possess a realistic amount of information?"——这正好是我们"信息边界"原则的验证入口。）
2. **Macro-face validation** —— 聚合模式"表面上"对应现实模式。原文强调 micro/macro face validation 都**不直接比对数据**。
3. **Empirical input validation** —— 输入数据/规则本身要有经验依据；可以用 training/test 划分，用 GA 或神经网络自动校准；**无论用什么方法校准，都必须做 robustness/sensitivity analysis**。
4. **Empirical output validation** —— 三种：*stylized facts*（若模型只是思想实验，对齐 stylized fact 即可）、*real-world data*（若要做预测就必需；关键表述是"要证明真实世界是这个模型的一个**可能输出**，即真实数据落在模型输出的统计分布之内"）、*cross-validation*（与另一个已验证的、可以是别的方法论的模型对比）。
`[全文]`

- **对本项目的意义（重要）**: Rand & Rust 明确说，当模型主要目的是**思想实验**时，对齐 stylized facts 就足以показать validity；只有要做预测才需要 real-world data validation。本项目的定位（"合理但不必真实"）落在前者，因此我们的验证目标应该是 **stylized facts / POM 弱模式的分布对齐**，而不是历史曲线拟合。同时他们那句"real world is a possible output of this model"给了我们判据的正确形状：**真实中国史应当落在我们模型输出分布的支撑集内，但不应当是模型的众数**。
- **出处**: Rand, W. & Rust, R. T. (2011) "Agent-based modeling in marketing: Guidelines for rigor", *International Journal of Research in Marketing* 28(3): 181–193, doi:10.1016/j.ijresmar.2011.04.002 `[全文]`。

### 2.6 Docking / model alignment（Axtell, Axelrod, Epstein & Cohen 1996）

- **核心机制**: 让两个为不同目的构建的模型对齐，判断它们能否产出"相同"结果，从而检验其中一个是否能被另一个包含（subsume）。原案例用 Axelrod 的文化传播模型做 target，用 Epstein & Axtell 的 Sugarscape 逐步简化去对齐它。`[摘要]`
- **三级等价判据**（全项目应统一采用这套术语）:
  1. **Numerical identity** —— 数值完全相同。文献评价为"a high but potentially unattainable standard"，对随机模型尤其难。
  2. **Distributional equivalence** —— 输出分布在统计上不可区分（例如用 Mann–Whitney U 检验判断两组数据是否可能同源）。
  3. **Relational alignment** —— 参数与输出之间的关系模式相同，数值不必相同。
  `[页面]`（这三级最初由 Axtell et al. 1996 提出，我读到的是 Miodownik et al. 2010 JASSS 页面对它的转述与操作化。）
- **replication vs docking 的区分**: *replication* 是尽可能忠实地重实现原模型（可以换平台/工具）；*docking* 是"为不同目的开发的模型的对齐，用以展示它们产生相似结果的能力"（Wilensky & Rand 2007 的定义，经 Miodownik et al. 转述）。`[页面]`
- **docking 证明了什么、没证明什么**: 对齐成功只说明两个实现对同一机制家族给出一致行为，**不说明这个机制家族是对的**。它是 verification 类证据，不是 validation 类证据。
- **出处**: Axtell, Axelrod, Epstein & Cohen (1996) "Aligning simulation models: A case study and results", *Computational and Mathematical Organization Theory* 1(2), doi:10.1007/BF01299065 `[摘要]`；Wilensky & Rand (2007) "Making models match: replicating an agent-based model", JASSS 10(4):2 `[摘要]`；Miodownik, Cartrite & Bhavnani (2010) "Between Replication and Docking", JASSS 13(3):1, doi:10.18564/jasss.1627 `[页面]`。

### 2.7 Sugarscape（Epstein & Axtell 1996）与 Kehoe（2016）的形式化——一个必读的反面教材

- **模型本体**: 第一个大规模 ABSS。agent 有 vision、metabolism、speed 等"遗传"属性，移动规则是"在视野内找糖最多的格子，去那里吃糖"，每次移动按代谢率消耗糖。加入季节后出现迁徙与冬眠；agent 自组织成围绕糖峰的、空间隔离且文化上不同的"部落"，部落之间发生战斗和文化竞争。`[摘要]`
- **Kehoe（2016）的关键发现**（我读了全文结论）: 他用 **Z 规范语言**给出 Sugarscape 全族的第一个完整形式化规范，并把发现的问题归为三类：
  1. **Lack of Clarity** —— 附录里每条规则只给了一个版本，而正文提到多个变体；而且给出的变体不总能一起用（例如附录里的 Movement 规则不是与 pollution 规则同用时所需的那个变体）。
  2. **Missing Information** —— 最严重。例如疾病传播规则里三个未回答的问题：agent 获得某疾病免疫后，该疾病是否从其携带集合中移除（还是仍是携带者）？传播时只传播"自己携带且无免疫"的疾病，还是任何携带的疾病都能传？Mating 规则**遗漏了父母各出一半资源给后代**这一信息，而"这对交配如何运作有巨大影响"。作者的判断是"我们如何填这些空白会对模拟如何演进产生很大影响"。
  3. **Sequential Biases** —— **"书里没有说规则以什么顺序应用"**（"we note that it is not stated in the book what order the rules are to be applied"），Kehoe 只能自己挑一个顺序并固定下来。Sugarscape 隐含假定顺序实现；Z 规范只定义每条规则的前后状态，从而不对并发/冲突解决策略做任何约束。
  `[全文]`
- **对本项目的意义（极重要）**: **调度顺序是一个隐藏参数，而且是一等重要的参数**。ABM 领域最著名的模型在出版 20 年后仍无法被无歧义重实现，原因不是数学难，而是规则顺序和边界情形没写。我们必须把"tick 内的规则执行顺序"当作 spec 的一等公民、显式版本化，并在代码里禁止依赖哈希容器迭代顺序。
- **出处**: Epstein & Axtell (1996) *Growing Artificial Societies: Social Science from the Bottom Up*, MIT Press, ISBN 9780262550253 `[摘要]`；Kehoe, J. (2016) "The Specification of Sugarscape", arXiv:1505.06012v3 `[全文]`。

### 2.8 Artificial Anasazi / Long House Valley —— 本项目最重要的案例研究

**原始模型**（Dean, Gumerman, Epstein, Axtell, Swedlund, Parker, McCarroll 2000；Axtell et al. 2002 PNAS）:
- 模拟 Long House Valley（美国亚利桑那东北部）Kayenta Anasazi 人口，AD 800–1350。
- **实体**: agent = 家户（household，每户 5 人），属性含 age、玉米储量、农田位置、居住位置。
- **景观**: 80×120 格网，每格 100 m × 100 m，分 7 个土地区（land zones），生产力不同。
- **外生输入**: 逐年 **Palmer Drought Severity Index (PDSI)**，按土地区给出，驱动产量表。
- 原文强调"古环境研究（冲积地貌学、孢粉学、树轮气候学）使得对潜在农业产量（kg 玉米/公顷）的年际波动做出准确的定量重建成为可能"。
- 原始模型的主要结论之一是：**环境因素本身不足以解释完全的人口外流**——谷地本可以继续支撑一个不大的人口。
`[摘要]` + `[全文，经 Stonedahl & Wilensky 转述]`

**Janssen（2009）的批评性复现**（我读到了 JASSS 页面的详细抽取）:
- 用 NetLogo 重实现（后归档于 CoMSES）。
- 距离度量用 L1 和 L2（模拟人口 vs 考古人口时间序列）；扫了 **18,144 组参数组合 × 每组 15 次运行**。
- **关键发现**: 拟合成功主要由**两个调节 Long House Valley 承载力的参数**驱动——Harvest Adjustment Level（扫描区间 0.54–0.7，原始值 1.0，校准值约 0.56–0.6）与 Harvest Variance（扫描 0–0.7，步长 0.1，校准值 0.4）。
- **纯外生的"承载力模型"**（完全不含 agent 行为）取得了**可比的拟合，误差只高 10–50%**。
- 两个模型的最优参数值一致（Harvest Adjustment Level 0.56、Harvest Variance 0.4）。
- Janssen 的表述是："the agent-based model acted as a smoothing function"——ABM 只是对不规则的承载力曲线起了平滑作用。
- 人口学参数（Death Age 26–40，默认 30；End of Fertility Age 26–40；Fission Probability 0.095–0.185，默认 0.125；给子代玉米比例 0.33；营养需求 800 kg/户/年）敏感性远小于承载力参数，且在阈值以上进入平台期（Death Age > 34、End of Fertility Age > 30、Fission Probability ≥ 0.125）。
- 产量表按区与 PDSI 类别取值范围 **411–1201 kg**。
`[页面]`

**Stonedahl & Wilensky（2010）的演化式稳健性检查**（我读了全文，这是本节信息密度最高的来源）:
- 用 GA（BehaviorSearch + NetLogo）在 **12 维**参数空间做校准，对比 Janssen 的 5 参数网格扫描。GA 设置：generational GA、population 30、crossover 0.7、mutation 0.05、tournament size 3、Gray code 编码；适应度 = 15 次重复的平均 L2 误差；100 代 = **45,000 次运行**，约为 Janssen **272,160 次运行**的 16.5%；5 次搜索共约 **2500 CPU 小时**。他们同时指出：GA 空间若做穷举网格需 **6.5×10^16** 组合。
- **校准结果的统计学陷阱（必读）**: 用 30 次重复时 GA 参数平均 L2 = 891.4 (σ=65.8) 优于 Janssen 的 945.3 (σ=80.0)，t 检验 p<0.01 显著；**但改用 100 次重复后，GA 变成 943.1 (σ=324.5)、Janssen 930.6 (σ=194.4)**，结论反转。误差分布非正态，GA 参数"通常更好但偶有极端离群"。中位数 GA 860.4 vs Janssen 893.8；随机取一次运行，GA 设置更接近历史的概率 65.9% vs 34.1%。
- **关于"校准目标该是什么"的根本论点（对本项目直接适用）**: 原文指出，要取得绝对最低的平均误差，就得让**每一次运行都等于历史数据**，而"一般来说这样的结果表明模型极不现实，只有一条历史路径是可能的"（"such a result would indicate a very unrealistic model, where only one path through history is possible"）。他们由此认为，**一个良好校准的模型应当能产出类似历史的东西，但结果中保留一定的变异是模型可信度的可取特征**。他们还把选择表述为三个候选："(1) 总是有点接近历史；(2) 常常很接近但偶尔差很远；(3) 偶尔完美吻合但通常差很远"，并指出在 facsimile 类历史模型里这个选择很难，因为**只有一份历史记录可比**（且这份记录本身也有不确定性），因此需要"对历史以其实际方式展开的可能性做估计，并考虑可信的替代历史"。
- **多变量敏感性分析（±10% 规则）**: 让 12 个参数各在校准值 ±10% 内变动，用 GA **最大化** L2 误差。5 次搜索全部找到误差 > 4 倍校准值的设置；最佳设置平均 L2 = 3918.6 (σ=249.7)，即 **>300% 的误差增幅**；而 Janssen 的单变量（OFAT）敏感性分析在同样 ±10% 内最大只带来 **50%** 的相对 L2 增幅，五个参数各自最大增幅之和也只有约 150%。原因是 GA 动到了更多敏感参数（如 BaseNutritionNeed）以及**参数间的非线性交互**。
- **定性差异的搜索**: 改用 Pearson 相关系数为目标（最小化 r），在同样 ±10% 内得到平均 r = **−0.18**，单次最低 r = **−0.6**，对应人口在 **AD 994** 归零的缓慢衰亡。也就是说，**在校准点 ±10% 的邻域内，同一个模型既能产出"人口爆炸"，也能产出"公元 994 年灭绝"**。
- **顺带发现了两个真实 bug**（这是本简报最有工程价值的一段）:
  1. `HarvestVarianceLocation` 被用作以 1.0 为中心的正态分布的方差，但农业质量不许为负、被截断在 0，**于是"增大方差"同时抬高了分布均值**——一个"方差参数偷偷改了均值"的经典陷阱。原文代码：`set quality ((random-normal 0 1) * harvestVarianceLocation) + 1.0` 后接 `if (quality < 0) [set quality 0]`。
  2. `HarvestVarianceYear` **在代码中从未被使用**（初始化后再未引用），年际变异实际也由 `HarvestVarianceLocation` 控制。这是一个已发表模型中的死参数。
- 他们还指出，若只测 ±10% 的两个端点，12 参数只需 2^12 = 4096 组合（原文写作 4196，应为笔误），是可枚举的；但不能保证非线性交互下极值落在端点。
`[全文]`

**Gunaratne & Garibay（2020）的 Evolutionary Model Discovery**:
- 方法：**遗传编程演化 agent 规则 + random forest 因子重要性分析**两阶段。
- 适应度：模拟与真实 Long House Valley 逐年家户数的 RMSE。
- 测试的 9 个候选决策因子：距离 F_Dist、土地质量 F_Qual、干燥度 F_Dry、上年产量 F_Yield、水可得性 F_Water、社会存在 F_Soc、年龄同质性 F_Age、农业成功同质性 F_Agri、跨区迁移 F_Mig；外加 4 种社会连通性配置（全谷地知识 / 家族网络 / 最近邻 / 表现最好的家户）。
- 重要性排序：**质量 > 社会存在 > 距离 > 迁移 > 水可得性 > 产量 > 农业同质性 > 年龄同质性 > 干燥度**。
- 原模型假定"距离最近"是选择农田的**唯一**因素；演化出的三种策略在随机化参数初始化下显著优于原规则。
- 诚实的负面结论：该文**没有**量化"模型拟合中有多少来自 agent 规则、多少来自环境参数"。
`[页面]`

### 2.9 Epstein 的 civil violence 模型（2002 PNAS）

- **两个变体**: (I) 中央权威镇压去中心化叛乱；(II) 中央权威镇压两个交战族群之间的族际暴力。`[摘要]`
- **数学规范**（我通过 Mesa 官方实现文档 + 一篇复现文献的检索摘要交叉确认）:
  - 每个 citizen 有 hardship `H ~ U[0,1]`、risk aversion `R ~ U[0,1]`、state ∈ {QUIET, ACTIVE, ARRESTED}、剩余刑期。
  - **grievance** `G = H · (1 − L)`，其中 `L` 是政权合法性（`1 − L` 表示民众把所受苦难归咎于政府的程度）。
  - **arrest probability** `P = 1 − exp[−k · (C/A)]`，`C` 为视野内警察数、`A` 为视野内 active 者数（原式含 `v`：`P = 1 − exp[−k(C/A)_v]`）。
  - **net risk** `N = R · P`。
  - **激活规则**: `G − N > T` 则转为 ACTIVE，否则保持 QUIET。
- **参数默认值**（**注意：这是 Mesa 实现的默认值**，我未能访问 PNAS 原文核对，PNAS PDF 返回 403）: 网格 40×40；citizen density 0.7；cop density 0.074；citizen/cop vision 半径 7；government legitimacy 0.82；max jail term 30 步；active threshold 0.1；arrest probability 常数 k = 2.3；允许移动；随机激活顺序；Von Neumann 邻域。`[页面]`
- **一个致命的复现细节**: Mesa 实现的注释明确写道，`arrest_probability = 1 − exp(−k · ⌊cops_in_vision / actives_in_vision⌋)` 里的**取整（floor/round）不在 PNAS 原文中，但没有它就不可能复现原文展示的动态**（"the round is not in the pnas paper but without it, its impossible to replicate the dynamics shown there"）。`[页面]`
- **对本项目的意义**: 这是 Sugarscape 教训的第二个独立证据——**一个已发表 PNAS 的公式，其可复现性依赖于论文里没写的一个取整操作**。任何"由基础机制涌现出的宏观模式"的说法，都可能悬挂在一个未记录的实现细节上。
- **出处**: Epstein, J. M. (2002) PNAS 99(suppl. 3): 7243–7250, doi:10.1073/pnas.092080199 `[摘要]`；Mesa 官方示例文档 `[页面]`。

### 2.10 Village Ecodynamics Project（VEP）—— 与本项目最同构的长期考古 ABM

- **规模**: 模拟中央 Mesa Verde 地区 Pueblo 社会的聚落与生计，**AD 600–1300**（700 年）；agent = 家户，落在"以合理保真度表示史前科罗拉多西南部景观"的地形上；基础模型里家户"最小化获取足够热量、蛋白质、燃料和水的卡路里成本"，景观因外生（气候）与人类资源利用而持续变化。
- **数据基础**: 结合调查数据、陶器、树轮年代等，估计约 **1700 km²** 内 **4000+ 个考古遗址**的人口（以户为单位）。
- **诚实的局限**: 我读到的项目/论文描述里明确说，研究者"当时才刚刚开始把这些模型的输出与考古记录做系统比较"。`[摘要]`
- **对本项目的意义**: VEP 是"从生计成本最小化出发、跑数百年、有真实地形和真实考古校准集"的最接近先例；它的代码在 GitHub（village-ecodynamics 组织）和 tDAR 上有归档。我们可以借它的**状态变量清单和成本最小化目标函数形式**，但必须注意它同样是外生气候驱动。
- **出处**: Kohler et al.（Village Ecodynamics Project；American Antiquity 系列论文）`[摘要]`；tDAR dataset 425610 `[摘要]`；github.com/village-ecodynamics `[摘要]`。

### 2.11 校准方法族（这是本简报最可直接落地的部分）

**(a) Approximate Bayesian Computation（ABC）**
- 不需要似然函数，靠"保留那些产生的输出与观测数据足够相似的参数"，相似性由摘要统计量或距离度量定义。对 ABM 特别有用，因为 ABM 推导似然通常不可行。`[摘要]`+`[全文，经 O'Gara 转述]`
- 出处: Grazzini, Richiardi & Tsionas (2017) "Bayesian estimation of agent-based models", *Journal of Economic Dynamics and Control* 77: 26–47, doi:10.1016/j.jedc.2017.01.014 `[摘要]`；考古学应用见 Crema, Kandler & Shennan (2016) *Scientific Reports* 6:39122, doi:10.1038/srep39122 `[摘要]`。

**(b) History Matching（HM）—— 我推荐作为本项目的主校准范式**
- **核心思想**: 不求"最优点"，而是**反复排除不可信的参数区域**。用 emulator 估计模型在未跑过的参数点上的均值与方差，然后用 **implausibility measure** 排除：
  `I(θ) = |Y − μ̂(θ)| / sqrt(σ̂²_emulator(θ) + σ̂²_obs + σ̂²_discrepancy)`
  多输出时取跨输出的最大值 `I_M(θ) = max_q I_q(θ)`。超过 cutoff 的点被排除，剩下的叫 **NROY（Not Yet Ruled Out）空间**。
- **cutoff 的来历**: 常用 `I(θ) = 3`，依据 Pukelsheim (1994) 的"三西格玛规则"——任何连续单峰分布至少 95% 落在三个标准差内。
- **NROY 空转的意义**: 如果 NROY 空间估计为空（找不到任何非不可信参数），那**既要重新审视模型本身，也要重新审视 model discrepancy 项**。这对我们是一条明确的失败判据。
- **model discrepancy（σ_discrepancy）**: 可由专家先验给出、可单独建模、也可当成总不确定性的乘子。加大它 → implausibility 变小 → 排除得更少（保守）。
`[全文，O'Gara et al.]`
- 出处: Vernon, Goldstein & Bower (2010) "Galaxy Formation: a Bayesian Uncertainty Analysis", *Bayesian Analysis* 5(4): 619–670 `[摘要]`；O'Gara, Kerr, Klein, Binois, Garnett & Hammond, "Improving Policy-Oriented Agent-Based Modeling with History Matching: A Case Study", arXiv:2501.00616 `[全文]`；McCulloch, Ge, Ward, Heppenstall, Polhill & Malleson (2022) JASSS 25(2):1, doi:10.18564/jasss.4791 `[页面]`。

**(c) Emulator / Surrogate（GP / hetGP / ML）**
- **hetGP（heteroskedastic Gaussian process）** 允许噪声随参数空间变化——对 ABM 至关重要，因为 ABM 输出方差本身是参数的函数。关键工程性质：在 hetGP 范式下，若共有 N 次运行、分布在 n 个唯一参数点上（每点 a_i 次重复，Σa_i = N），**训练与推断的复杂度是 O(n³) 而不是标准 GP 的 O(N³)**（靠 Woodbury 恒等式）。这意味着**在同一参数点做多次重复几乎是免费的**——对随机 ABM 是决定性的优势。`[全文]`
- **ML surrogate**: Lamperti, Roventini & Sani (2018) 用监督学习 + 智能迭代采样构建代理元模型，"大幅减少大规模参数空间探索与校准所需的计算时间"；测试模型为 Brock & Hommes (1998) 资产定价模型和 Fagiolo & Dosi (2003) "Islands" 内生增长模型。`[摘要]`（该文摘要页未给出具体加速倍数与算法名，故不引用倍数。）
- **SVM/SVR surrogate 做定性行为模式分类**: ten Broeke, van Voorn, Ligtenberg & Molenaar (2021)，用重复 Latin hypercube 设计 + 自适应采样（每轮 20 点批量）；初始训练样本 1000 点、测试 1000 点；目标 F1 > 0.9（分类）/ coefficient of prognosis > 0.9（回归）；resource–consumer ABM 共需 4100 样本，fishery 模型 2000 样本。明确局限：**代理模型无法捕捉随机变异**（resource–consumer 模型中 2.9% 方差无法解释），**且不能替代局部 OFAT 敏感性分析**。`[页面]`

**(d) 遗传算法 / metaheuristic 校准（BehaviorSearch）**
- 见 2.8 的 Stonedahl & Wilensky 数据。核心工程结论：GA 能在 12 维空间里用 45,000 次运行做到网格扫描 272,160 次的效果，且能顺带做"对抗式敏感性分析"（把 minimize 换成 maximize，把范围收窄到 ±10%）。`[全文]`

**(e) 逆向生成社会科学（iGSS）/ Evolutionary Model Discovery**
- 用（多目标）遗传编程从宏观目标反向**演化出 agent 规则本身**，而不是手工设计规则。Vu et al. (2019) 提出多目标 GP，同时优化"经验拟合"和"理论可解释性"，因为"遗传程序常产出高度预测但复杂难解释的拼接"。`[摘要]`
- Epstein (2023) 的框架性论述见 2.12。

### 2.12 Epstein 的生成主义与 iGSS —— 直接回答"如何证明涌现不是写进参数"

我读了 Epstein (2023) JASSS 全文的关键段落，以下是**逐字**引用的四条判据，它们构成本简报第 3 节"涌现认证"的理论依据：

1. **生成主义口号**: "If you didn't grow it, you didn't explain it"（Epstein 1998）。
2. **口号不等于"一切都必须生长出来"**: "That is emphatically not a dictat that 'You must grow everything in your model.' Some elements of every model must be posited."（有些元素必须被**假定**，例如作为独立 agent 的中间机构）。原文强调这纯粹是定义性的：**没被生成的，就没被解释；但这不意味着它不重要或被禁止。**
3. **必要而非充分**: "the motto ('Not grown implies not explained') must not be confused with its converse ('Grown implies explained')"。Epstein (2006, p.53) 原话："Merely to generate is not necessarily to explain (at least not well) ... A microspecification might generate a macroscopic pattern in a patently absurd—and hence non-explanatory—way." 总结句：**"generative sufficiency is a necessary but not sufficient condition for explanation."**
4. **多重生成者（multiple generators）**: "the motto does not say there is only one way to grow it ... there may be many ways to grow it; many agent specifications that suffice to generate the target"。这不是尴尬而是"embarrassment of riches"。**裁决多个生成者的唯一办法是收集新的微观数据或设计新的微观尺度实验**；文中类比气候科学、飓风预报和流行病学——用几个机制不同但经验上都可信的模型形成"概率锥"。结论句：**"Generative sufficiency confers explanatory candidacy."**（生成充分性只授予"解释候选资格"。）
5. **对 LLM 的直接警告（重要）**: Epstein 指出 AI 打败人类"并不照亮人类如何运作"，混淆在于"the emulation of human **output** and the revelation of a human **generative mechanism**"，并明确说 **"The Turing Test is irrelevant to explanation"**——机器对人类输出的模仿本身不揭示产生该输出的机制。

`[全文]` 出处: Epstein, J. M. (2023) "Inverse Generative Social Science: Backward to the Future", JASSS 26(2):9, doi:10.18564/jasss.5083。另见 Epstein (2008) "Why Model?" JASSS 11(4):12（区分解释与预测，给出除预测之外的 16 条建模理由）`[摘要]`。

### 2.13 涌现的形式定义与它的问题

- **Bedau 的 weak emergence**: "Macrostate P of S with microdynamic D is weakly emergent if and only if P can be derived from D and S's external conditions but only by simulation."（1997）—— 宏观现象在原则上可还原为微观，但除了模拟微观动力学外没有可行的还原解释路径。`[摘要]`
- **Baker (2010) 的批评**（我读到 JASSS 页面的抽取）: "can but only" 这个从句是防止定义被平凡化的关键（排除了可解析推导的 resultant properties），但**"模拟"与其他推导方法之间缺乏有原则的边界**；"full specificity" 相对于微观元素与时间单位的任意选择；涉及全称命题（如"所有未来状态"）的性质无法仅由模拟推导；混合推导（部分模拟部分解析）破坏定义的清晰性。`[页面]`
- **对本项目的现实结论**: **不要试图用"是否满足 Bedau 弱涌现"来给我们的现象颁发涌现证书。** 那个定义在哲学上尚有争议，而且不可操作。可操作的替代是消融实验 + 反事实控制（见第 3 节机制 M6/M7）。
- 出处: Bedau, M. (1997) "Weak Emergence" `[摘要]`；Baker (2010) "Simulation-Based Definitions of Emergence", JASSS 13(1):9, doi:10.18564/jasss.1531 `[页面]`。

### 2.14 敏感性分析：方法选择与真实预算

ten Broeke, van Voorn & Ligtenberg (2016) 对三种方法做了对比，测试模型是一个 15 参数的 NetLogo 空间显式 ABM（自由活动、繁殖的 agent 从扩散型可再生资源上取食，主输出为 agent 种群规模）：

| 方法 | 优点 | 缺点 | 该文实际用的运行次数 |
|---|---|---|---|
| **OFAT**（单因素） | 揭示机制性理解；暴露 tipping point 与非线性；识别涌现模式 | 忽略交互效应；无法做方差分解 | ~1,650（10 参数 × 11 点 × 10 重复） |
| **回归型全局 SA** | 把复杂输出压缩成可解释关系 | 对非正态、有离群、高维交互的 ABM 拟合差 | 5,000（1,000 参数组 × 5 重复） |
| **Sobol'**（方差分解） | 系统性捕捉交互效应 | 对偏斜/重离群分布不适用；缺乏机制洞察；置信区间宽 | 17,000（Saltelli 采样方案） |

**该文的明确建议**: "OFAT as the starting point for any sensitivity analysis of an ABM"，尤其当优先目标是理解机制时；只有当输出分布足够接近正态时，全局方法才适合作为补充。`[页面]`

出处: ten Broeke, van Voorn & Ligtenberg (2016) JASSS 19(1):5, doi:10.18564/jasss.2857 `[页面]`。

**重要补充（Stonedahl & Wilensky 的反证）**: OFAT 在 Artificial Anasazi 上**严重低估**了敏感性——单变量 ±10% 最大只带来 50% 误差增幅，而多变量 GA 搜索在同一 ±10% 盒子里找到 >300% 的增幅。因此**OFAT 只能作为起点，绝不能作为终点**；对本项目这种高维模型，应当用"对抗式搜索"（GA 最大化误差 / 最小化相关）作为敏感性分析的主力。`[全文]`

### 2.15 可复现性危机的真实数字

- Janssen (2017)：分析 **2,367 篇** ABM 出版物（初筛 2,855 篇），覆盖 **722 种期刊**、**1990–2014 年**。**约 10% 的出版物公开模型代码**；到 2014 年上升到约 15%。55% 的论文披露了资助来源，但即使在公共资助研究中代码共享率仍只有 10–15%，说明"资助方没有强制执行公开数据可得性"。JASSS 是显著例外（该刊强烈鼓励作者提供足以复现所报告模拟实验的信息）。`[页面]` 出处: Janssen, M. A. (2017) "The Practice of Archiving Model Code of Agent-Based Models", JASSS 20(1):2, doi:10.18564/jasss.3317。
- 另一项调查（Ecological Modelling / EMS 上关于 individual/agent-based model 代码共享与文档的研究）在检索摘要中给出"2018 年上升到 18%"以及"不同期刊之间差异很大"、"模型文档不包含数学方程、流程图、伪代码等可提升透明度的要素"。`[摘要]`——**该数字我未读到原文，标为 C 级。**
- 复现研究本身极少：检索摘要指出"ABM 的复现或重实现研究很少被开展，在考古学或其他社会科学中的例子很少"。`[摘要]`

### 2.16 多层级 / 变粒度 ABM —— 已有成熟做法的完整分类

Brugière, Nguyen-Ngoc & Drogoul (2022) 的综述给出了目前最清晰的分类（我读到了完整抽取）。按"层级控制自主性"排成一个连续谱：

| 范式 | 机制 | 跨层反馈 | 涌现分析能力 | 代表框架 |
|---|---|---|---|---|
| **Zoom** | 同一时刻只有一个层级在跑；聚合/解聚函数是**破坏性**的（切换层级时信息丢失） | **被阻断** | 只能单层观测 | mean-field 近似、变量聚合法；GAMA 的 *Capture / Release* 属于此思路的可控版本 |
| **Russian Dolls** | 多层级同时执行，严格层级化协调，紧耦合，holonic 调度（例如微观层每宏观步执行 60 次） | **通过层级调度实现** | 层级持久存在，可分析涌现 | GEAMAS、ML-DEVS（DEVS 扩展，James II 实现）、CRIO（holonic，行人流）、**NetLogo LevelSpace**、GAMA Capture/Release |
| **Collaboration** | 各层级自主、弱耦合，双向信息交换，模型间以黑箱交互 | **无限制双向** | 可跨异质模型检测涌现 | GEAMAS-NG、GAMA co-modeling、**IRM4MLS**（Influence–Reaction 多层级模型） |
| **Multi-Hierarchy (AGR)** | agent 被建模为**动态角色集合**而非固定层级成员，支持非空间、非时间的"社会重叠"层级 | 取决于实现 | 实验性 | AGR / AALAADIN / MaDKit、ORIGAMI、AGRE、IRM4S |

**所有范式共有的局限**（原文列出）:
- 缺乏显式的空间/时间尺度表示，尺度一致性由建模者自己负责；
- 无法表示**多个同时存在的层级体系**，只能限于单一视角；
- 因此无法表示"同时具有多重重叠角色的 agent"（例如同一个人既是行人、又是家长、又是权威）。

**范式特有局限**: Zoom 有信息损失且层级间涌现不可能；Russian Dolls 难以整合非 ABM 层级、自主性僵化；Collaboration 对非开发者建模者复杂度过高且验证困难。

**实践指引**（原文给出）: 简单转换用 Zoom + mean-field；自然空间层级用 Russian Dolls；异质模型耦合用 Collaboration；复杂社会结构用 AGR（但工具成熟度低）。

`[页面]` 出处: Brugière, A., Nguyen-Ngoc, D. & Drogoul, A. (2022) "Handling multiple levels in agent-based models of complex socio-environmental systems: A comprehensive review", *Frontiers in Applied Mathematics and Statistics*, doi:10.3389/fams.2022.1020353。

**相关一手工具**:
- **LevelSpace**（NetLogo 扩展）: "allows you to run NetLogo models from inside NetLogo models"，让模型可动态嵌套；设计目标是保持 NetLogo 的 "low-threshold, high-ceiling" 哲学；论文用三个例子分别对应 Morvan 提出的三类多层级 ABM 问题。出处: Hjorth, Head, Brady & Wilensky (2020) JASSS 23(1):4 `[摘要]`。
- **Morvan (2012) 多层级 ABM 文献综述**: arXiv:1205.0561 `[摘要]`。
- 军事/工程侧的 aggregation–disaggregation 框架: DTIC ADA558453 "Agent Based Simulation Design for Aggregation and Disaggregation" `[摘要]`。
- 术语: "macroagents" 定义为一群 "micro-agents" 的聚合体，运算允许在运行期动态改变表示层级。`[摘要]`

### 2.17 平台工程特性与真实规模上限

**基准数据（一手，来自 JuliaDynamics/ABM_Framework_Comparisons 仓库 README，版本 Agents.jl 6.2.10 / Ark.jl 0.5.1 / MASON 22.0 / NetLogo 6.4.0 / Mesa 3.2.0；100 次可重现随机运行取中位数；时间归一化到 Agents.jl = 1.0）** `[页面]`

| 模型（规模） | Ark.jl | MASON | NetLogo | Mesa |
|---|---|---|---|---|
| WolfSheep 小 | 0.36 | 5.29 | 9.94 | 9.38 |
| WolfSheep 大 | 0.17 | 7.8 | 4.81 | 3.28 |
| Flocking 小 | 0.74 | 1.42 | 15.37 | 159.29 |
| Flocking 大 | 0.36 | 0.61 | 19.14 | 59.5 |
| Schelling 小 | 0.85 | 1.19 | 11.39 | 29.73 |
| Schelling 大 | 0.99 | 1.51 | 14.33 | 26.66 |

代码行数（LOC，NetLogo 括号内为含 GUI 的全文件行数）: WolfSheep — Agents.jl 73 / Ark.jl 149 / MASON 202 / NetLogo 137 (871) / Mesa 118；Flocking — 42 / 137 / 159 / 82 (689) / 94；Schelling — 26 / 78 / 129 / 54 (739) / 33。

**⚠ 偏倚警告**: 这份基准由 Agents.jl 的作者维护，是**自报**基准。Mesa 在 Flocking 上慢 59–159 倍这个量级值得怀疑（很可能是 Mesa 侧实现未优化邻域搜索）。作为决策依据时，应当自己重跑我们真实的工作负载。

**各平台的工程特性**:

- **NetLogo**（Wilensky 1999）: 教学/原型最强，内置 **BehaviorSpace** 实验工具——系统性变动设置并记录每次运行结果；支持组合式区间 `["var" [start step end]]`、组合式列表、以及 6.4+ 的 **subexperiment 语法**（让参数组合可以**非组合式**地分组运行，这对我们做"情景族"而非笛卡尔积很有用）；并行运行默认线程数建议 `floor(0.75 × processor_count)`；四种输出格式（table / spreadsheet / statistics(6.4+, 给出重复间均值与标准差) / lists(6.4+)）；支持 `NetLogo_Console --headless` 命令行运行（指定模型、实验名、输出路径、线程数、可覆盖世界尺寸）。局限：后台运行不能用 GUI-only 原语；table 输出因并行完成时序可能乱序。`[页面]`
- **Repast 套件**（Argonne 国家实验室维护 20+ 年，全部开源免费）`[页面]`:
  - **Repast Simphony** v2.11.0（2024-07），Java，面向工作站与小型集群，"richly interactive and easy to learn"；
  - **Repast HPC** v2.3.1（2021-10），C++，"designed for use on large computing clusters and supercomputers"，完整分布式支持；
  - **Repast for Python (Repast4Py)** v1.2.1（2025-11），Python，面向"大规模分布式 ABM 方法"。
  - 相关文献: North, Collier & Vos (2006) ACM TOMACS 16(1):1–25 `[摘要]`；Collier & North (2013) "Parallel agent-based simulation with Repast for High Performance Computing", *Simulation* `[摘要]`；Collier & Ozik, "Distributed Agent-Based Simulation with Repast4Py", WSC `[摘要]`。
- **MASON**（Luke, Cioffi-Revilla, Panait, Sullivan & Balan 2005, *Simulation* 81(7): 517–527, doi:10.1177/0037549705058073）: Java，快速可扩展的离散事件多 agent 工具包；**关键设计特点是严格区分 model 与 visualization**，模型可在运行中动态从可视化器上摘下/挂上，甚至中途更换平台。`[摘要]` 对我们的意义：数千年模拟必须能 headless 跑，可视化必须是可插拔的旁观者。
- **Mesa**（Python）: ter Hoeven, Kwakkel, Hess, Pike, Wang, rht & Kazil (2025) JOSS 10(107):7668, doi:10.21105/joss.07668。自 2014 年起被 **500+ 篇论文、800 位作者**引用；Mesa 3 稳定了 **Cell Space** 系统（`mesa.discrete_space`），支持以格子为中心的模拟、集成 PropertyLayers 和改进的 agent 移动。`[摘要]` 性能是明显弱项（见上表）。
- **Agents.jl**（Julia）: Datseris, Vahdati & DuBois (2022/2024) *Simulation: Transactions of SCS*, doi:10.1177/00375497211068820。声称同时最快且代码最少。基准模型为 Flocking（ContinuousSpace）、Wolf Sheep Grass（GridSpace）、Forest Fire（细胞自动机型）等四个。工程细节（原文）: 提供 **ensemble 模拟与参数扫描的自动分布式计算**（跨多 CPU）；但坦承 **"in-model parallelization is outside the control of Agents.jl"**，因为 ABM 里"同一内存位置的修改一直在发生（不断杀死/添加 agent）"，这是**所有 ABM 框架共同的现实问题**。作者称模型 "reproducible by design"，并计划用 Julia 宏自动预填 ODD 模板。`[全文]`
- **GAMA**（GAML 语言）: 开源、空间显式、多层级 ABM 平台，**原生集成 GIS 矢量与栅格数据**（与 CORMAS、NetLogo 不同）；提供完整建模语言与 IDE 以支持"大规模模型"定义。出处: Taillandier, Gaudou, Grignard, Huynh, Marilleau, Caillou, Philippon & Drogoul (2019) "Building, composing and experimenting complex spatial models with the GAMA platform", *GeoInformatica* 23(2): 299–322 `[摘要]`；另有参与式建模专文 JASSS 22(2):3 `[摘要]`。**对本项目：如果我们要以真实中国东亚地理为舞台并直接吃 GIS/DEM/古气候栅格，GAMA 是唯一原生做这件事的成熟 ABM 平台。**
- **FLAME GPU 2**: Richmond et al. (2023) *Software: Practice and Experience*, doi:10.1002/spe.3207。层级化 sub-modelling 方法已用 **Sugarscape 模型演示到 1600 万 agent**；检索摘要还称可在 A100/H100 上"扩展到数亿 agent"（后者来自 NVIDIA 技术博客，**C 级**）。`[摘要]`
- **极端规模（谨慎引用，均为 arXiv 预印本，C 级）**: BioDynaMo 相关工作报告单服务器 **17 亿 agent**；**TeraAgent** 报告可模拟 **5000 亿 agent**、扩展到 **84,096 CPU 核**（arXiv:2509.24063；另 arXiv:2503.10796 报告"最多三个数量级的加速"）。这些是生物细胞级 agent，**行为规则远比社会 agent 简单**，不能直接外推到我们的场景。`[摘要]`

### 2.18 LLM 驱动的生成式社会模拟：现有验证文献的结论

Larooij & Törnberg (2025) 的系统综述（我读到 PMC 全文抽取，这是本项目最该反复读的一篇）:

- **方法**: Scopus 检索（2025-03-27）初得 **209 篇**，两阶段筛选（要求用 LLM 生成 agent 行为、多 agent、agent 间交互、明确以模拟人类社会行为为目标）后剩 **35 篇**。
- **验证方式分类（作为主要验证手段的论文数）**: Human(-like) Judgment 12 / Well-Known Social Patterns 14 / Similar Models 1 / Human-Generated Data 12 / Internal Consistency 1。
- **核心事实**: **35 篇中有 15 篇完全依赖主观评估。** 许多研究采用的是"face-validity"路径——评估输出**看起来**是否可信，而不验证底层机制。
- **归因于 LLM 的三类问题**:
  1. **黑箱性**: "LLMs are fundamentally black-box models: their capacities are emergent, and it is virtually impossible to determine why a particular input yields a particular output."
  2. **文化与社会偏置**: social bias（复制歧视、刻板印象）与 **selection bias**（源于训练语料构成；LLM 可能**复制历史模式**，或表现出 **"data leakage"——复现既有研究结论**而不是动态生成行为）。
  3. **随机性与幻觉**: "LLMs are probabilistic next-word predictors, they possess no internal mechanism to validate the correctness of their outputs"，在分布外情境下行为变得不稳定。
- **系统性错位**:
  - **弱耦合**: 许多研究验证的是"表层输出——比如生成文本的风格真实性——而不是底层机制或交互动力学"；
  - **主观占主导**，且用 LLM 评估自己的输出"引发关于循环性与偏置的实质性担忧"；
  - **风格混淆**: 客观比较时发现 "LLM responses are longer, more polite, articulate, and respectful"，但这种风格差异并不必然影响 face-validity 判断；
  - **计算成本**: 作者估算适度规模的模拟成本在数千到数十万美元；agent 交互随人口规模**二次**增长，计算需求随参数**指数**增长。
- **该文没有给出正式清单**，但提出了 operational validity 的**最低标准三条**: (i) 验证目标与模型目的**对齐**；(ii) 通过经验数据实现**外部锚定**，而不只是 face-validity；(iii) 在**多次运行**上展示稳健性并做敏感性检查。
- **结论句**: 生成式 ABM "occupy an ambiguous methodological space—lacking both the parsimony of formal models and the empirical validity of data-driven approaches"。
`[页面]` 出处: Larooij, M. & Törnberg, P. (2025) *Artificial Intelligence Review*, doi:10.1007/s10462-025-11412-6。

**补充（C 级，单一综述）**: arXiv:2501.08579 "LLM-based Human Simulations Have Not Yet Been Reliable" 报告的具体差距：临床诊断正确率仅 **40.18%**；GPT-4 情绪理解 **58%** vs 人类 **70%**；被指派的 persona 只能解释人类标注方差的 **不到 10%**（角色遵从性弱）。`[摘要]`

**LLM 非确定性的工程事实（D/C 级，多为技术博客与预印本）**: 即使设置 temperature=0、贪心解码、固定 seed，跨机器或不同 batch size 仍会产生不同输出；归因于 batch-size 相关的浮点归约顺序、MoE 路由变异、以及服务端在非完全相同副本间的负载均衡。一项预印本报告在 690 次 API 调用（2 个提供商、3 个模型档、5 种采样配置）中，即使强制贪心解码，7 个边界样本里仍有 1–2 个不可复现。`[摘要]` **这些来源质量不高（博客 + 未经同行评议预印本），标 C 级；但方向性结论——"不能把 LLM 调用当作可复现的纯函数"——对我们的架构是硬约束。**

### 2.19 仿真研究的 provenance（因果链留档）

- Ruscheinski, Gjorgevikj, Dombrowsky, Budde & Uhrmacher (2018) "Towards a PROV Ontology for Simulation Models"：用 **W3C PROV-DM**（PROV Data Model）识别并关联"为生成一个仿真模型做出贡献的实体与活动"。动机是"虽然仿真**数据**的 provenance 和单个仿真实验的支持受到很多关注，但仿真**模型**没有"。`[摘要]`
- 后续: "SIMPROV: Provenance capturing for simulation studies"（PLOS ONE / bioRxiv），提出轻量方法在建模者熟悉但异质的工作环境中记录**完整仿真研究**的 provenance，架构上明确分离 *provenance capturers*（从各软件系统收集）与 *provenance builder*（组装成连贯的 provenance graph）。`[摘要]`
- 更一般的 provenance-graph 因果追溯范式（来自 LLM agent / 系统安全文献，C 级）: 日志提供时序可观测性，但依赖分析需要**图结构**——把执行工件作为节点、影响关系作为**带类型的边**；回答"为什么"的方式是"给定一个症状，对全系统 provenance 图发起**后向追溯查询**，通过遍历该症状事件的祖先返回根因"。`[摘要]`
- **对本项目**: 这正是 MANDATE 第 2 条"因果链"所需的现成形式化。我们不需要自己发明"因果链"数据结构——PROV-DM 的 Entity / Activity / Agent 三元组 + `wasGeneratedBy` / `used` / `wasDerivedFrom` / `wasAssociatedWith` 边，加上时间戳，已经足够表达"这场战争由哪些先前事件与状态导致"。**注意 PROV 的 Agent 概念与 ABM 的 agent 概念是两个不同东西，命名上要避免混淆。**

### 2.20 可复现随机性：counter-based RNG

- Salmon, Moraes, Dror & Shaw (2011) "Parallel random numbers: as easy as 1, 2, 3", SC'11, doi:10.1145/2063384.2063405。**counter-based RNG (CBRNG)** 对**计数器**施加一个**无状态混合函数**来产生第 N 个随机数，而不是用传统的有状态变换。
- 关键性质（Random123 文档表述）: 这种方式"让应用完全控制 RNG 状态"，因此"天生具有极好的可复现性——只要对同一计数器值重新施加变换，就能重新生成任何特定的随机数"；它们"向量化和并行化都很好，几乎不需要状态内存"，适合多核 CPU、GPU、集群和专用硬件；通过了 TestU01 的 SmallCrush / Crush / BigCrush。`[页面]`
- 实现: DEShawResearch/random123（C/C++/CUDA）；Julia 的 RandomNumbers.jl 提供 Random123 家族。`[页面]`
- **对本项目**: 这是"记录随机种子以便重放和反事实实验"这条 MANDATE 要求的正确技术选择。见第 3 节机制 M4。

---

## 3. 可直接用于本项目的机制清单

每条格式：**输入 → 输出 / 数学或算法草图 / 时间尺度 / 空间粒度 / 证据等级 / 为什么这样简化**。
"归属"一列说明该机制应由数学规则决定（rules_math）、由 LLM agent 决定（llm_agent）、还是混合（hybrid）。

### M1. ODD-as-code：把 spec 变成机器可校验的工件（rules_math）

- **输入 → 输出**: 完整 ODD（七元素 + 11 设计概念）+ delta-ODD 版本链 → 一份结构化清单文件（YAML/TOML），其中每个实体、状态变量、参数、子模型、以及 **tick 内规则顺序**都有唯一 ID，并指向源码符号。
- **算法草图**:
  1. `spec.yaml` 声明 `entities[]`、`state_vars[]`（含单位、取值域、更新者）、`processes[]`（含 `order: int`、`reads[]`、`writes[]`）、`params[]`（含 `range`、`source`、`evidence_level`）。
  2. 构建期检查（CI）：(a) 每个 `state_var` 恰有声明的写者集合，运行时断言无越权写；(b) 每个 `process` 的 `reads/writes` 与静态分析出的实际访问集合一致；(c) 每个 `param` 必须被至少一个 process 引用（**参数活性测试**，见 M9）；(d) `order` 无重复、无缺号。
  3. 每次发布生成 delta-ODD（相对上一个 tag 的差异），进 TRACE notebook。
- **时间尺度**: 开发期，非运行期。
- **空间粒度**: 不适用。
- **证据等级**: **B**（ODD/TRACE 是学界共识的文档标准；"把它变成机器可校验的 schema"这一步是我们自己的工程决定，属 D 级；但 ODD 2020 明确建议 ODD 各节超链接到源码位置、文档与实现命名一致，故整体记 B）。
- **为什么这样简化**: 因为 Sugarscape（Kehoe 2016）和 Epstein civil violence（Mesa 注释）都证明了纯文本 spec 会丢掉决定性细节，尤其是**规则顺序**和**边界截断**。把 spec 变成 CI 能检查的东西是唯一能在数百次迭代后仍保持"可解释"的办法。

### M2. POM 模式电池（Pattern Battery）作为验收测试套件（rules_math）

- **输入 → 输出**: 一批"弱模式"定义（每条 = 一个可计算的统计量 + 一个**序数/区间**判据，而非点值）→ 每次长跑后的通过/失败矩阵 + 通过分数。
- **算法草图**:
  - 模式定义 `P_i = (statistic_fn, predicate, scale, layer)`，其中 `layer ∈ {individual, settlement, polity, world}`，`scale` 记录时间与空间尺度。
  - `predicate` 只允许三类形状：**序数**（"随复杂度上升该量单调不减"）、**区间**（"该指数落在 [a,b]"）、**存在性**（"在整个运行中至少出现一次某类现象"）。禁止 "等于某个历史数值"。
  - 评分：`score = Σ w_i · 1[P_i passed]`，同时报告**未通过的模式清单**（这比总分重要）。
  - 关键设计约束：模式必须来自**其他简报**（考古、气候、人口、经济史、冲突统计），而不是从我们模型里反向读出来的。
- **时间尺度**: 一次完整长跑（数千模拟年）之后评估；也可分时段（前文明期 / 早期国家 / 帝国期）分别评估。
- **空间粒度**: 多层：个体、聚落、政体、世界。
- **证据等级**: **A**（POM 本身是 Science 上发表并被广泛采用的策略，且 ODD 2020 把 patterns 提升为第一元素）；但"具体哪些模式、权重多少"是 **D 级**，必须由各领域简报填充。
- **为什么这样简化**: 单条宏观曲线拟合在过参数化模型上是无效检验（Fagiolo et al. 2007；Janssen 2009 的承载力空模型），而多条弱模式的**联合**通过很难被伪造。序数化 predicate 让"合理但不必真实"这个目标可操作。

### M3. 因果链 = PROV 风格事件图（rules_math）

- **输入 → 输出**: 每个 tick 内所有状态转移 → 一张单调增长的有向无环事件图，支持"给定一个事件，后向遍历祖先"。
- **算法草图**（PROV-DM 映射）:
  - 节点类型：`Event`（对应 PROV Activity，例如"AD 1342 的 X 城围城"）、`StateFact`（PROV Entity，例如"AD 1341 X 城粮储 = 3.2 万石"）、`Actor`（世界内的人/组织；**注意与 PROV Agent 概念区分**）。
  - 边类型：`used(Event → StateFact)`、`wasGeneratedBy(StateFact → Event)`、`wasDerivedFrom(StateFact → StateFact)`、`wasAssociatedWith(Event → Actor)`、`wasInformedBy(Event → Event)`。
  - 每个 `Event` 额外记录：`rule_id`（对应 M1 的 process ID）、`rng_key`（M4）、`llm_call_id`（若有）、`tick`。
  - 存储：append-only 日志 + 每 N tick 一次索引压缩。为控制体积，采用**重要性分级留档**：`level 0` 全量（仅最近 K tick 的滚动窗口）、`level 1` 聚合（每年的政体级汇总）、`level 2` 只留被标记为"重大事件"的完整祖先闭包（**闭包在事件被标记时立刻物化并冻结**，否则滚动窗口过期后祖先就找不回来了）。
  - 查询："为什么这个国家灭亡" = 对灭亡 Event 做 BFS 后向遍历，按边类型与 `tick` 距离剪枝，返回前 k 层。
- **时间尺度**: 每 tick 写入；查询任意时刻。
- **空间粒度**: 事件本身的粒度（个体 / 聚落 / 政体）。
- **证据等级**: **B**（PROV-DM 是 W3C 标准，且已被明确用于仿真研究的 provenance；"重要性分级留档"与"祖先闭包冻结"是我们的工程设计，D 级）。
- **为什么这样简化**: 全量保留数千年逐 tick 全状态的祖先图在存储上不可行。分级 + 事件触发时冻结闭包，是"因果可追溯"与"存储可行"之间唯一可行的折中。**这个设计决定必须在写第一行模拟代码之前定下来**，因为事后无法补回丢失的祖先。

### M4. 分层 counter-based RNG（rules_math）

- **输入 → 输出**: `(world_seed, tick, stream_id, entity_id, purpose_id, draw_index)` → 一个确定的随机数流。
- **算法草图**:
  - 用 CBRNG（Philox/Threefry 家族，Random123 实现）：`value = F(key, counter)`，其中
    `key = hash(world_seed, stream_id)`，`counter = (tick, entity_id, purpose_id, draw_index)`。
  - **性质**: 无状态 → 任意随机数可在 O(1) 内重算，不需要重跑历史；并行安全 → 不同 entity 天然使用不相交的 counter 子空间，不需要锁；**分叉安全** → 从任意快照分叉时，只需改 `world_seed` 或某个 `stream_id`，其余流完全不变，从而可做"只改这一件事"的反事实实验。
  - `stream_id` 按机制分配（气候、疾病、生育、战斗结算、发现、LLM 采样……），使得"只把疾病流换一个种子"成为一个合法的反事实操作。
- **时间尺度**: 每次抽样。
- **空间粒度**: 每实体。
- **证据等级**: **A**（CBRNG 的可复现性与并行性有一手文献与 TestU01 统计检验支持；`key/counter` 的具体分层布局是我们的设计，D 级）。
- **为什么这样简化**: 传统有状态 PRNG 在并行 ABM 里几乎必然破坏可复现性（执行顺序影响抽样顺序）。CBRNG 把"随机性"变成状态的纯函数，这是 MANDATE 第 6 条（记录种子、可重放、可反事实）唯一干净的实现路径。

### M5. 显式调度顺序 + 无隐式顺序依赖（rules_math）

- **输入 → 输出**: M1 中声明的 `processes[].order` → 确定的 tick 内执行序列。
- **算法草图**:
  - tick 结构固定为若干 **phase**：`observe → decide（含 LLM 调用）→ resolve（规则结算）→ commit → record`。跨 phase 不允许读写穿越；`decide` 阶段只能读 `observe` 快照，只能写"提案队列"。
  - 同一 phase 内多 agent 的处理顺序：**不允许依赖容器迭代顺序**。要么 (a) 顺序无关（纯函数式，读旧写新），要么 (b) 按显式确定性键排序（如 `sort_key = CBRNG(tick, "activation_order", entity_id)`）——后者本身就是一次可复现的随机置换。
  - CI 测试：把容器实现换成不同迭代顺序（例如把 dict 换成逆序遍历），要求输出**逐位相同**。这条测试能自动抓住 Sugarscape 类的顺序歧义。
- **时间尺度**: 每 tick。
- **空间粒度**: 全局。
- **证据等级**: **B**（Kehoe 2016 用形式化方法证明了"规则顺序未记录"是 Sugarscape 不可复现的三大原因之一，且它把 Z 规范设计成"只定义每条规则的前后状态、不约束冲突解决策略"以消除顺序偏倚；"phase + 逆序遍历 CI 测试"是我们的工程设计，D 级）。
- **为什么这样简化**: 因为最著名的 ABM 在 20 年后仍因为这个原因不可复现。

### M6. 外生输入审计 / 空模型支配测试（rules_math）—— Artificial Anasazi 教训的直接产物

- **输入 → 输出**: 一个宏观输出 `Y`（例如总人口曲线、聚落数、政体数）+ 全部外生输入序列（气候、地形、初始禀赋）→ 一个"内生贡献度"报告。
- **算法草图**:
  1. 对每个我们打算作为**成果**展示的宏观输出 `Y`，构造一个**空模型** `M_0`：只用外生输入 + 最简单的解析变换（例如"承载力 = f(外生降水, 地形) 直接给出人口"），**完全不含 agent 决策**。
  2. 用同一误差度量（对我们而言是 POM 模式通过分数，而非 L2）比较 `M_full` 与 `M_0`。
  3. **判据**: 若 `M_full` 相对 `M_0` 的改进小于阈值 τ，则我们**不得**声称该输出是由 agent 行为解释的；必须在文档里写成"该输出主要由外生驱动"。
  4. 额外做**外生序列置换检验**：把外生气候序列做 (a) 时间反转、(b) 块状打乱、(c) 用同一自相关结构的替代序列（surrogate）替换。如果 POM 通过分数**几乎不变**，说明模式来自内部机制（好）；如果分数崩塌，说明模式挂在特定外生序列上（危险，必须披露）。
- **时间尺度**: 每次重大版本发布时做一次完整审计。
- **空间粒度**: 与被审计的输出同级。
- **证据等级**: **A**（Janssen 2009 实证了纯外生承载力模型能取得只差 10–50% 的拟合，且两模型最优参数一致；"the agent-based model acted as a smoothing function" 是原文表述。阈值 τ 与置换检验的具体形式是我们的设计，D 级）。
- **为什么这样简化**: 这是本简报最重要的一条。Artificial Anasazi 是 ABM 考古学的旗舰模型，它被批评的方式正是我们最容易犯的错——**把外生气候重建序列喂进模型，然后把随之而来的人口曲线当作 agent 行为的解释成果**。我们的项目野心更大（数千年、政体、宗教、思想），因此风险更大：真实古气候序列（若我们用它）会天然地把兴衰节律"注入"模型，让任何机制都看起来在解释历史。

### M7. 涌现认证（Emergence Certificate）（rules_math）—— 直接回答"如何证明涌现不是写进参数"

- **输入 → 输出**: 一个被声称"涌现"的现象 `E`（如"出现了官僚制""出现了成文法""出现了货币"）→ 一份四段式认证或一次拒绝。
- **算法草图**（四段，全部必须通过）:
  1. **词汇表检查（Vocabulary Check）**: `E` 的类型标签**不得**在 `t=0` 的类型词汇表中存在为一个"可被触发的预定义状态"。形式化做法：把所有类型标签分成 `primitive`（原语，允许在 t0 存在）与 `composite`（组合，必须由运行期规则实例化）。`E` 必须是 `composite`，且其构成规则必须只引用 `primitive` 或更低层的 `composite`。**这抓的是"隐藏剧情树"——如果代码里有 `if (conditions) then spawn_bureaucracy()`，词汇表检查必然失败。**
  2. **消融测试（Ablation）**: 逐个移除候选支撑机制 `m_1..m_k`，要求存在至少一个 `m_j` 使得移除后 `E` 的出现频率显著下降。若移除任何机制 `E` 都照样出现，说明 `E` 是被某处硬编码或被外生输入决定的。
  3. **多种子频率与非唯一性**: 在 `N ≥ 50` 个独立 `world_seed` 上统计 `E` 的出现频率 `p`。要求 `0 < p < 1`（**两端都要排除**）：`p = 0` 说明它是一次侥幸；`p ≈ 1` 且路径几乎相同，说明它其实是被写死的必然事件，不是涌现。同时记录 `E` 的**多种实现形态**——按 Epstein 的 multiple generators 论点，一个真涌现的制度应当有多个形态各异的实例。
  4. **反事实控制（Counterfactual Control）**: 用 M4 的分流种子做单点扰动（只改某一个具体历史事件的随机流），检查 `E` 的出现是否**路径依赖**。若在数十次单点扰动下 `E` 的出现时间/形态完全不变，说明它对历史路径不敏感——这与 MANDATE 第 3 条（路径依赖）矛盾，应视为可疑。
- **附加要求（借 Epstein）**: 认证只授予"**解释候选资格**"，不是"已解释"。任何认证过的现象在文档中必须同时列出"其他能产出同一现象的候选机制"，以及"要在这些候选之间做裁决需要什么新的微观数据"。
- **时间尺度**: 事后分析（一次认证需要 50+ 次完整长跑，是最大的计算开销项）。
- **空间粒度**: 与现象同级。
- **证据等级**: **B**（第 2、3 段的思想在 ABM 稳健性检查文献中有先例——Stonedahl & Wilensky 的多变量对抗搜索、iGSS 的 multiple generators 论点、Epstein 关于"生成充分性只是必要条件"的明确表述；但这个四段协议**作为一个整体是我们自己拟的**，属 D 级；因此整体给 B/D 混合，落笔时按 D 处理更安全）。
- **为什么这样简化**: 文献里**没有**一个现成的"涌现证明程序"。Bedau 的弱涌现定义不可操作（Baker 2010 的批评成立），POM 只管宏观模式不管"是否被写死"。第 1 段（词汇表检查）是我们能给出的、最接近"证明这不是剧情树"的可执行检查；它把一个哲学问题转化成一个静态分析问题。

### M8. 对抗式敏感性分析（rules_math）

- **输入 → 输出**: 校准点 `θ*` + 每个参数的 ±δ 盒子（建议 δ = 10%）→ "在这个盒子里，模型最坏能坏到什么程度"的包络。
- **算法草图**:
  1. 用 GA（或 CMA-ES 等）在盒子 `[θ*(1−δ), θ*(1+δ)]` 内**最大化** POM 失败模式数；再单独**最小化**与目标模式的序数一致性。
  2. 报告：最坏配置、最坏配置下的模式失败清单、以及"哪些参数在多次独立搜索中被一致推向边界"（这些就是模型的真实敏感参数）。
  3. 同时保留 OFAT 作为**机制理解**工具（ten Broeke et al. 的建议），但**不**把 OFAT 当作敏感性的结论。
  4. 若参数数 `n` 不大，加一轮 `2^n` 角点枚举（12 参数 = 4096 组合）作为廉价下界。
- **参考预算**: Stonedahl & Wilensky 在 12 参数 / 每点 15 重复下用 45,000 次运行完成一次搜索（约 2500 CPU 小时，5 次搜索）。
- **时间尺度**: 每次重大版本一次。
- **空间粒度**: 不适用。
- **证据等级**: **A**（Stonedahl & Wilensky 给出了完整的一手数据：单变量 ±10% 最大 +50% 误差 vs 多变量 GA >300%；且这套方法在真实已发表模型里抓出了两个 bug）。
- **为什么这样简化**: 因为 OFAT 在这个模型族上被实证低估了 6 倍以上的敏感性，而全 Sobol 在我们的维度下预算不可承受（ten Broeke 的 15 参数玩具模型已需 17,000 次运行）。

### M9. 参数活性测试与"方差偷偷改均值"检测（rules_math）

- **输入 → 输出**: 参数清单 → 两类失效报告。
- **算法草图**:
  1. **活性测试（liveness）**: 对每个声明参数 `p`，在其合法域内取两个远离的值，跑 `R` 次重复，用双样本检验判断是否有任何被监控输出的分布发生变化。若**没有**，则 `p` 是死参数 → 构建失败。（这条测试会直接抓住 Artificial Anasazi 的 `HarvestVarianceYear` bug。）
  2. **矩位移测试（moment-shift）**: 对每个被声明为"离散度/方差/噪声幅度"的参数 `s`，检查在改变 `s` 时被它调制的量的**均值**是否显著移动。若移动，则说明存在截断/裁剪导致的均值污染 → 报警，要求改成保均值的形式（例如用截断分布并重标定，或用对数正态代替被裁剪的正态）。（这条抓住 `HarvestVarianceLocation` 的 `if quality < 0 → 0` bug。）
- **时间尺度**: CI，每次提交。
- **空间粒度**: 不适用。
- **证据等级**: **A**（两个具体 bug 都有一手记录：Stonedahl & Wilensky 全文给出了导致均值位移的确切 NetLogo 代码行，以及"HarvestVarianceYear 初始化后从未被引用"）。
- **为什么这样简化**: 这两类 bug 在一个被广泛引用、被多次复现的已发表模型里存活了十年。它们是可以被自动化测试彻底消灭的。

### M10. 波次式 history matching + hetGP emulator（rules_math）

- **输入 → 输出**: 参数先验盒子 + 一批目标模式量 → NROY 空间（"尚未被排除"的参数区域）+ 该区域上的后验样本。
- **算法草图**（照搬 O'Gara et al. 的流程，替换目标量）:
  1. **Wave 1**: maximin Latin hypercube 取 50 个参数点，每点 25 次重复（后续波次 20 次）。
  2. 对每个目标量训练 hetGP emulator（异方差 GP；因 O(n³) 而非 O(N³)，同点重复几乎免费）。
  3. 计算 `I_M(θ) = max_q |Y_q − μ̂_q(θ)| / sqrt(σ̂²_emul + σ̂²_obs + σ̂²_disc)`，用 cutoff 排除；`I = 3` 起步，后续波次收紧（O'Gara 用 3.0 / 3.0 / 2.5）。
  4. 在剩余 NROY 空间内用 maximin 再取 50 点，重复 3–4 波。
  5. 最后在 NROY 空间上定义信息性截断正态先验，做 ABC（SMC / MCMC）得后验。
  6. **失败判据**: 若 NROY 空间变空 → 模型结构或 discrepancy 项有问题，回到模型本身。
- **实测收益（O'Gara et al.，Covasim 4 参数）**: 总计 **5,300 次运行**完成校准，而原始超参优化路径用了 **>100,000 次运行（≈35 天算力）**；三波后**排除了 >99% 的参数空间**（NROY 体积 7.23% → 5.58% → 0.82%）；emulator 在 40^4 = **2,560,000** 个候选点上求值只需"几分钟"，而用模拟器直接跑需"近 2.5 年"。
- **另一组实测（McCulloch et al. 2022）**: HM + ABC 共 **3,185 次运行**，而纯 ABC 需 **>11,000 次**；点估计方法（模拟退火 / 进化算法）只需 256–290 次但**不给分布信息**；HM 平均把 ABC 的运行次数削减约 2,047 次；初始 ABC 容差建议 `ε = 3(V_o + V_s + V_m)`。
- **时间尺度**: 每次重大结构变更后重跑。
- **空间粒度**: 不适用。
- **证据等级**: **A**（两篇独立来源给出可用的量化预算、cutoff 值和空间削减比例）。
- **为什么这样简化**: 我们的绝大多数参数**没有**可靠的历史来源，因此追求点估计是自欺。HM 的哲学（"我不知道参数是多少，但我能证明它不在这些区域"）与本项目"合理但不必真实"的定位天然契合。而 hetGP 的 O(n³) 性质让"每个参数点跑很多次重复"这件对随机 ABM 必需的事变得可负担。

### M11. 多层级 / 变粒度：Zoom 聚合 + 触发式解聚（hybrid）

- **输入 → 输出**: 一个巨大的人口 → 一个混合表示：绝大多数人口用**队列（cohort）**表示，少数被"提升"为个体 agent。
- **算法草图**:
  1. **背景层（macro）**: 每个聚落维护一个年龄×性别队列向量 `n(a,s)`，用 Leslie 矩阵式更新 `n_{t+1} = L(θ_local) n_t`，其中 `θ_local` 由本地粮食、疾病、战争损失等驱动。这是"Zoom"范式的宏观端。
  2. **个体层（micro）**: 只对满足**提升触发条件**的实体实例化个体 agent：(a) 被 LLM 需要（有名有姓的人物）、(b) 处在高信息价值位置（统治者、商队首领、宗教创始者）、(c) 参与被标记为重大事件的过程。
  3. **提升（disaggregation）**: 从队列中抽 `k` 个个体，其属性从队列的条件分布中采样（用 M4 的确定性 RNG，使提升本身可复现）；队列相应减去 `k`。**不变量**：提升前后总人数、年龄结构的一阶矩必须守恒（CI 断言）。
  4. **降级（aggregation）**: 个体 agent 死亡或退出关注范围后，其"残余影响"写回队列（如后代数量、财产转移），个体状态归档到事件图（M3）而非丢弃。这是 Zoom 范式**破坏性**聚合的一个受控版本：**我们不丢信息，只把它移出活跃计算**。
  5. **级联控制**: 用固定的"活跃个体预算" `B`（例如 10^4–10^5 个个体 agent），超出时按重要性打分驱逐（降级），保证长跑成本上界。
- **时间尺度**: 宏观层按年更新；微观层可按年或按事件驱动。
- **空间粒度**: 宏观 = 聚落/区域格；微观 = 个体。
- **证据等级**: **B**（多层级 ABM 的三类范式与 aggregation/disaggregation 机制有综述级共识；Zoom 范式的"破坏性、跨层涌现不可能"这一局限也被明确指出；具体的触发条件、预算与守恒不变量是我们的设计，D 级）。
- **为什么这样简化**: 综述明确指出 Zoom 的代价是**信息损失和跨层涌现不可能**。我们的应对是：把"信息损失"改成"移出活跃计算但写进事件图"，并把真正需要跨层涌现的东西（制度、宗教、思想）放在**政体/文化层**——那一层本身就是显式的 meso agent，不是队列。**这条机制上的风险最高，需要在 Phase 1 用真实原型验证成本。**
- **注意（综述给出的硬限制）**: 现有多层级框架"无法表示多个同时存在的层级体系"，也因此**无法表示同时具有多重重叠角色的 agent**（一个人既是族人、又是官员、又是信徒）。我们的世界必然需要这个能力 → 应当采用 AGR（Agent/Group/Role）范式的思想（agent = 动态角色集合），但要清楚 AGR 的实现（AALAADIN、ORIGAMI、AGRE、IRM4S）**仍是实验性的、采用极少**，我们得自己实现。

### M12. LLM 约束层：提案—裁决架构（hybrid）

- **输入 → 输出**: agent 的受限观测 + 记忆 → 一个**类型化的提案**（不是结果）→ 规则系统裁决 → 客观结果。
- **算法草图**:
  1. **观测构造**（rules_math）: 由规则系统从全局状态**投影**出该 agent 在该时刻**合理能获得**的信息（MANDATE 第 4 条），包括延迟、失真、遗漏。投影函数本身是纯函数且被记录。
  2. **提案空间**（rules_math 定义 schema，llm_agent 填内容）: LLM 只能输出符合 JSON schema 的动作提案，例如 `{action: "declare_war", target: polity_id, stated_reason: text, mobilization_fraction: float ∈ [0,1]}`。**schema 之外的任何输出被拒绝并重试；重试次数上限后回落到规则型默认策略。**
  3. **裁决**（rules_math）: 战争胜负、经济后果、疾病传播等**全部**由规则数学计算（军力、经济、后勤、地形、士气、技术、将领能力 + 受约束随机性），LLM 的 `stated_reason` 只进入"叙事/官方历史"层，**不进入世界事实层**（MANDATE 第 9 条）。
  4. **确定性化**（rules_math）: 每次 LLM 调用写入 `llm_call` 记录：`(prompt_hash, model_id, model_version, sampling_params, rng_key, response, response_hash)`。**决策缓存**以 `(prompt_hash, model_id, rng_key)` 为键；重放时命中缓存即得逐位相同结果。这是应对"LLM 不是可复现纯函数"的唯一可靠办法。
  5. **成本控制**: LLM 只对被提升的个体 agent（M11 微观层）调用，且只在"决策点"调用；背景人口的行为由规则型策略产生。
- **时间尺度**: 事件驱动。
- **空间粒度**: 个体 / 组织。
- **证据等级**: **B**（"LLM 输出不可作为被验证量"有系统综述支持：Larooij & Törnberg 明确指出 LLM 的黑箱性、文化/选择偏置、data leakage 与随机性使验证更难；Epstein 明确区分"模仿人类输出"与"揭示生成机制"并称图灵测试与解释无关。"提案—裁决 + 决策缓存"的具体架构是我们的设计，D 级）。
- **为什么这样简化**:
  - **data leakage 是本项目的特定致命风险**。综述明确点出 LLM 可能"复制历史模式"或"复现既有研究结论"。我们的世界舞台是**真实中国及东亚地理**——LLM 极可能因为地理线索而把真实中国史的剧情结构泄漏进来（"这里应该出现一个统一帝国"）。这直接违反 MANDATE"真实历史只是校准集"的核心原则。
  - **缓解措施（我们的设计，D 级）**: (a) 给 LLM 的 prompt 中**移除或替换所有真实地名、族名、朝代名**，只提供该 agent 实际能感知的地理与社会特征（"东侧三日程有一条大河，河北岸有五个村落"）；(b) 建立"泄漏探针"——定期用一批"真实历史专有名词/事件序列"检测模型输出中是否出现，出现则报警；(c) 用 M7 第 1 段（词汇表检查）保证 LLM 无法凭空实例化 composite 类型。

### M13. Docking：双实现分布等价测试（rules_math）

- **输入 → 输出**: 核心内核的两个独立实现（不同语言/不同作者/不同数据结构）→ 三级等价判定。
- **算法草图**:
  1. 期望达到的等价级别按机制分层设定：
     - **numerical identity**：要求于纯确定性子系统（地形、水文、CBRNG 本身、聚合/解聚守恒律）。
     - **distributional equivalence**：要求于随机子系统（生育、疾病、战斗结算），用 Mann–Whitney U 或 KS 检验判断输出分布是否可能同源。
     - **relational alignment**：要求于整体长跑（参数→输出的关系形状一致），因为完整长跑的数值一致在实践中不可达。
  2. 建立一个"参照实现"（reference implementation），故意写得**慢但简单**（例如纯 Python、单线程、O(n²) 邻域搜索），只用于校验高性能实现。
- **时间尺度**: 每次内核变更。
- **空间粒度**: 不适用。
- **证据等级**: **B**（三级等价判据来自被广泛引用的 Axtell et al. 1996，并被后续 JASSS 文献操作化；"慢参照实现"是标准软件工程做法，我们的选择，D 级）。
- **为什么这样简化**: docking 只能提供 verification 级证据（两个实现一致），不能提供 validation 级证据（机制是对的）。但对一个要跑数千年、任何一处数值错误都会被复利放大的系统，verification 是必需的第一道防线。

### M14. 快照 / 分叉 / 反事实实验（rules_math）

- **输入 → 输出**: 任意 tick 的世界状态 → 一个内容寻址的不可变快照 ID；`(snapshot_id, 扰动描述)` → 一条新历史线。
- **算法草图**:
  1. 状态用**结构共享的持久数据结构**（HAMT / 或 append-only 段 + copy-on-write）；快照 = 根哈希。分叉成本 O(1)。
  2. 扰动描述是一个**类型化的小对象**，允许的类型只有：`reseed_stream(stream_id)`、`suppress_event(event_id)`、`force_event(event_template)`、`perturb_param(param_id, delta)`。每种扰动都要求填 `justification`，进 TRACE。
  3. 反事实实验的标准报告形式：`N` 条分叉线在 `K` 个 POM 模式量上的分布，与主线对比；同时报告"主线的那个事件在多少条分叉里自发重现"（这是路径依赖强度的度量）。
  4. **与 M4 的耦合**: 因为 CBRNG 无状态，`suppress_event` 之后的所有其他随机流保持原样——这才是"如果当时没有发生某件事"的干净反事实，而不是"从那一点起整个随机序列都变了"。
- **时间尺度**: 快照可按年/按重大事件；分叉按需。
- **空间粒度**: 全局。
- **证据等级**: **B**（CBRNG 支持这种干净反事实是它的已证明性质；持久数据结构与内容寻址是标准工程；组合起来做历史反事实是我们的设计，D 级）。
- **为什么这样简化**: MANDATE 明确要求"保存任意历史节点并建立平行世界"和"如果当时没有发生某件事"的实验。用有状态 RNG 做这件事会导致扰动点之后**一切**都变，反事实就失去了意义。

### M15. 分级实验预算（rules_math）

- **输入 → 输出**: 一次变更的类型 → 应跑的实验套件与预算。
- **算法草图**（我们的三档，D 级但基于文献预算数字）:
  - **Tier 0（每次提交，秒—分钟级）**: 单元测试 + M1 spec 一致性 + M5 逆序遍历一致性 + M9 参数活性/矩位移（用极短跑）+ 短跑 smoke test。
  - **Tier 1（每次 PR，小时级）**: 10^2–10^3 次短跑（数百模拟年），OFAT 关键参数（参照 ten Broeke: 10 参数 × 11 点 × 10 重复 ≈ 1,650 次运行），POM 模式电池的前文明期子集。
  - **Tier 2（每次重大版本，CPU-天—周级）**: 一次完整 HM（≈ 5×10^3 次运行，参照 O'Gara 的 5,300）+ 一次对抗式敏感性搜索（≈ 4.5×10^4 次运行，参照 Stonedahl 的 45,000 / 2,500 CPU 小时）+ 50–100 次完整长跑用于 M7 涌现认证。
- **证据等级**: **B**（各档的运行次数量级都有一手文献支撑；分档方案本身是 D 级）。
- **为什么这样简化**: 长跑是本项目最贵的资源。把"每次都做"的检查压到 Tier 0（这些恰恰是能抓住最多真实 bug 的检查——死参数、均值位移、顺序依赖），把昂贵的分布级检验留给版本节点。

---

## 4. 硬数字与参数表

**说明**：本表只列我在本次检索中**实际读到**的数值。我读到的方式在"来源可靠度"列标注。**凡文献未提供可用参数的地方，我明确写"文献未提供"。**

### 4.1 方法论协议的结构性数字

| 量 | 数值 | 适用范围 | 来源 | 可靠度 |
|---|---|---|---|---|
| ODD 元素数 | 7 | ODD 2020 第二次更新 | Grimm et al. 2020 JASSS 23(2):7 | `[页面]` |
| ODD 设计概念数 | 11（含领域自定义扩展位） | 同上 | 同上 | `[页面]` |
| TRACE 主元素数 | 8 | TRACE 协议 | Grimm et al. 2014 | `[摘要]` |
| docking 等价级别数 | 3（numerical identity / distributional equivalence / relational alignment） | 模型对齐 | Axtell et al. 1996，经 Miodownik et al. 2010 操作化 | `[页面]` |

### 4.2 敏感性分析与校准的运行预算（**这是本表最有用的部分**）

| 方法 | 运行次数 | 配置 | 来源 | 可靠度 |
|---|---|---|---|---|
| OFAT | ~1,650 | 10 参数 × 11 点 × 10 重复（模型共 15 参数） | ten Broeke et al. 2016 | `[页面]` |
| 回归型全局 SA | 5,000 | 1,000 参数组 × 5 重复 | 同上 | `[页面]` |
| Sobol′ | 17,000 | Saltelli 采样方案 | 同上 | `[页面]` |
| 网格扫描（Artificial Anasazi） | 272,160 | 5 参数、每参数 7–9 档、15 重复（= 18,144 组合 × 15） | Janssen 2009 / Stonedahl & Wilensky 2010 | `[页面]`/`[全文]` |
| GA 校准（同模型，12 参数） | 45,000 / 次搜索 | pop 30、crossover 0.7、mutation 0.05、tournament 3、100 代、每点 15 重复 | Stonedahl & Wilensky 2010 | `[全文]` |
| GA 校准 CPU 成本 | ~2,500 CPU 小时（5 次搜索合计） | 同上 | 同上 | `[全文]` |
| GA 变体（calibration-1） | 18,000 | pop 90、200 代、mutation 3%、每点 1 次运行 | 同上 | `[全文]` |
| 同 12 维空间的穷举网格代价 | 6.5 × 10^16 组合 | 原文估"需一百万处理器跑一百万年以上" | 同上 | `[全文]` |
| ±10% 角点枚举（12 参数） | 2^12 = 4,096 | 廉价敏感性下界 | 同上（原文写 4196，应为笔误） | `[全文]` |
| History Matching + ABC（Covasim, 4 参数） | **5,300** 总运行 | 每波 50 个 LHS 设计点，wave1 25 重复、后续 20 重复；3 波 HM + 1 波 ABC | O'Gara et al. arXiv:2501.00616 | `[全文]` |
| 被替代的超参优化路径 | >100,000 运行 ≈ 35 天算力 | Kerr et al. 2021 原始校准 | 同上 | `[全文]` |
| HM 的 implausibility cutoff | 3.0 / 3.0 / 2.5（逐波收紧） | 依据 Pukelsheim (1994) 三西格玛规则（连续单峰分布 ≥95% 在 3σ 内） | 同上 | `[全文]` |
| NROY 空间体积（逐波） | 7.23% → 5.58% → 0.82%（>99% 被排除） | 同上 | 同上 | `[全文]` |
| emulator 求值规模 | 40^4 = 2,560,000 候选点，"几分钟"；用模拟器需"近 2.5 年" | hetGP emulator | 同上 | `[全文]` |
| hetGP 复杂度优势 | O(n³) 而非 O(N³)（n = 唯一设计点数，N = 总运行数） | Woodbury 恒等式；意味着**同点重复几乎免费** | 同上（引 Binois, Gramacy & Ludkovski 2018） | `[全文]` |
| HM+ABC vs 纯 ABC | 3,185 vs >11,000 运行 | 另一独立案例；HM 平均削减 ABC 约 2,047 次运行 | McCulloch et al. 2022 JASSS 25(2):1 | `[页面]` |
| 点估计方法（模拟退火/进化算法） | 256–290 运行 | 便宜但**不给分布信息** | 同上 | `[页面]` |
| ABC 初始容差建议 | ε = 3(V_o + V_s + V_m) | 观测方差 + 集合方差 + 模型偏差 | 同上 | `[页面]` |
| ABC 粒子数（案例） | 1,000 | Birds 模型 | 同上 | `[页面]` |
| 每设计点的集合规模（案例） | 30（Birds）、100（RISC farming）、200（SugarScape 用于确定集合方差） | 同上 | 同上 | `[页面]` |
| SVM/SVR surrogate 训练量 | 初始 1,000 训练 + 1,000 测试；自适应每批 20 点；resource–consumer 共 4,100 样本，fishery 2,000 | 目标 F1>0.9 / CoP>0.9 | ten Broeke et al. 2021 JASSS 24(2):3 | `[页面]` |
| surrogate 无法解释的随机方差 | 2.9%（resource–consumer 模型） | surrogate 的固有局限 | 同上 | `[页面]` |

### 4.3 Artificial Anasazi 的参数（作为"外生驱动占比"教训的量化证据）

| 参数/量 | 数值 | 来源 | 可靠度 |
|---|---|---|---|
| 时间范围 | AD 800–1350（550 年，历史序列长度 550） | Axtell et al. 2002 / Stonedahl & Wilensky 2010 | `[摘要]`/`[全文]` |
| 网格 | 80 × 120 格，每格 100 m × 100 m | Janssen 2009 | `[页面]` |
| 土地区数 | 7 | 同上 | `[页面]` |
| 家户规模 | 5 人/户 | 同上 | `[页面]` |
| 外生驱动 | 逐年 PDSI（按土地区） | 同上 | `[页面]` |
| 产量表取值范围 | 411 – 1201 kg（按区与 PDSI 类别） | 同上 | `[页面]` |
| 营养需求 | 800 kg/户/年（Janssen 表述）；Stonedahl 表中 `BaseNutritionNeed = 160`（推测为 kg/人，160×5=800，**该换算是我的推断，未在文献中明说**） | 同上 | `[页面]`/`[全文]` |
| Harvest Adjustment Level | 扫描 0.54–0.7（步长 0.02），原始值 1.0，校准值 0.56（Janssen）/ 0.6 | 同上 | `[页面]` |
| Harvest Variance | 扫描 0–0.7（步长 0.1），校准值 0.4 | 同上 | `[页面]` |
| Death Age | 26–40（默认 30）；最佳拟合在 >34 后进入平台 | 同上 | `[页面]` |
| End of Fertility Age | 26–40（默认 30）；>30 后进入平台 | 同上 | `[页面]` |
| Fission Probability | 0.095–0.185（默认 0.125）；≥0.125 后进入平台 | 同上 | `[页面]` |
| 给子代玉米比例 | 0.33（父代存量的 1/3） | 同上 | `[页面]` |
| **纯外生承载力空模型的误差劣势** | **仅高 10–50%** | **Janssen 2009 的核心结论** | `[页面]` |
| 两模型最优参数一致性 | Harvest Adjustment 0.56、Harvest Variance 0.4（两模型相同） | 同上 | `[页面]` |
| GA 校准 L2（30 重复） | 891.4 (σ=65.8) vs Janssen 945.3 (σ=80.0)，t 检验 p<0.01 | Stonedahl & Wilensky 2010 | `[全文]` |
| GA 校准 L2（100 重复，**结论反转**） | 943.1 (σ=324.5) vs Janssen 930.6 (σ=194.4) | 同上 | `[全文]` |
| 中位 L2 | GA 860.4 vs Janssen 893.8；单次运行更优概率 65.9% vs 34.1% | 同上 | `[全文]` |
| calibration-1 最优单次 L2 | 733.6（vs Janssen 最优单次 823.5），但平均误差劣化到 962.4 | 同上 | `[全文]` |
| **单变量 ±10% 敏感性最大误差增幅** | **+50%**（五参数各自最大之和约 +150%） | 同上 | `[全文]` |
| **多变量 GA ±10% 敏感性最大误差增幅** | **>+300%**（平均 L2 = 3918.6, σ=249.7，>4 倍） | 同上 | `[全文]` |
| 最小相关性搜索结果 | 平均 r = −0.18；单次最低 r = −0.6，人口于 **AD 994** 归零 | 同上 | `[全文]` |
| Evolutionary Model Discovery 因子重要性排序 | 质量 > 社会存在 > 距离 > 迁移 > 水 > 产量 > 农业同质性 > 年龄同质性 > 干燥度 | Gunaratne & Garibay 2020 | `[页面]` |

### 4.4 Epstein civil violence 模型参数（**注意来源限制**）

以下是 **Mesa 官方实现的默认值**；我未能访问 PNAS 原文核对（PNAS PDF 返回 403），因此**不能断言这些等于 Epstein 原文数值**。

| 参数 | Mesa 默认值 |
|---|---|
| 网格 | 40 × 40，Von Neumann 邻域 |
| citizen density | 0.7 |
| cop density | 0.074 |
| citizen / cop vision 半径 | 7 格 |
| government legitimacy L | 0.82 |
| max jail term | 30 步 |
| active threshold T | 0.1 |
| arrest probability 常数 k | 2.3 |
| 激活顺序 | 随机 |

方程：`G = H(1−L)`，`P = 1 − exp[−k·⌊C/A⌋]`，`N = R·P`，激活条件 `G − N > T`。`H, R ~ U[0,1]`。
**关键复现警告**：Mesa 实现注释明确说其中的**取整不在 PNAS 原文中，但没有它就无法复现原文动态**。`[页面]`

### 4.5 平台性能与规模（归一化时间，Agents.jl = 1.0）

见 2.17 的表格。软件版本：Agents.jl 6.2.10 / Ark.jl 0.5.1 / MASON 22.0 / NetLogo 6.4.0 / Mesa 3.2.0；100 次可重现随机运行取中位数；**该基准由 Agents.jl 维护方自报**。`[页面]`

| 量 | 数值 | 来源 | 可靠度 |
|---|---|---|---|
| FLAME GPU 2 层级 sub-model 演示规模 | Sugarscape 至 **1,600 万** agent | Richmond et al. 2023 | `[摘要]` |
| FLAME GPU 2 在 A100/H100 上的上限说法 | "数亿" agent | NVIDIA 技术博客 | `[摘要]`，**C 级** |
| A100/H100 vs V100（100 万 agent） | 最多快 1.38× / 1.0× | RSE Sheffield 基准博客 | `[摘要]`，**C 级** |
| BioDynaMo 单服务器 | 17 亿 agent | arXiv:2503.10796 | `[摘要]`，**C 级（预印本，生物细胞级 agent）** |
| TeraAgent | 5,000 亿 agent，84,096 CPU 核 | arXiv:2509.24063 | `[摘要]`，**C 级（预印本）** |
| Repast Simphony | v2.11.0（2024-07），Java，工作站/小集群 | repast.github.io | `[页面]` |
| Repast HPC | v2.3.1（2021-10），C++，大集群/超算 | 同上 | `[页面]` |
| Repast4Py | v1.2.1（2025-11），Python，分布式 | 同上 | `[页面]` |
| Mesa 采纳度 | 500+ 篇论文、800 位作者引用（自 2014） | ter Hoeven et al. 2025 JOSS | `[摘要]` |
| NetLogo BehaviorSpace 默认并行线程 | `floor(0.75 × processor_count)` | NetLogo 官方手册 | `[页面]` |

### 4.6 可复现性现状

| 量 | 数值 | 范围 | 来源 | 可靠度 |
|---|---|---|---|---|
| 公开模型代码的 ABM 论文比例 | **约 10%**（2014 年约 15%） | 2,367 篇论文、722 种期刊、1990–2014 | Janssen 2017 JASSS 20(1):2 | `[页面]` |
| 公共资助研究的代码共享率 | 仍为 10–15%（55% 论文披露资助来源） | 同上 | 同上 | `[页面]` |
| 2018 年比例 | 18% | 另一项调查（Ecological Modelling/EMS） | 检索摘要 | `[摘要]`，**C 级** |

### 4.7 LLM 驱动社会模拟的验证现状

| 量 | 数值 | 来源 | 可靠度 |
|---|---|---|---|
| 系统综述纳入论文数 | 209 篇初筛 → **35 篇**纳入（Scopus, 2025-03-27） | Larooij & Törnberg 2025 | `[页面]` |
| **完全依赖主观评估的论文数** | **15 / 35** | 同上 | `[页面]` |
| 主要验证方式分布 | Human(-like) Judgment 12 / Well-Known Social Patterns 14 / Similar Models 1 / Human-Generated Data 12 / Internal Consistency 1 | 同上 | `[页面]` |
| 成本估计 | 适度规模模拟数千至数十万美元；交互随人口**二次**增长，计算需求随参数**指数**增长 | 同上 | `[页面]` |
| LLM 临床诊断正确率 | 40.18% | arXiv:2501.08579 | `[摘要]`，**C 级** |
| GPT-4 情绪理解 vs 人类 | 58% vs 70% | 同上 | `[摘要]`，**C 级** |
| persona 解释人类标注方差的比例 | <10% | 同上 | `[摘要]`，**C 级** |
| temperature=0 下的不可复现率（案例） | 690 次调用中，7 个边界样本里 1–2 个不可复现 | arXiv:2606.26185 | `[摘要]`，**C 级** |

### 4.8 文献未提供可用参数的地方（明确声明）

- **POM 的"多少条模式才够"**：文献未提供可用阈值。
- **模式之间的权重**：文献未提供。
- **"内生贡献度"的判定阈值 τ**（M6）：文献未提供；Janssen 只报告了"外生空模型误差高 10–50%"这一事实，未给出可接受阈值。
- **涌现认证所需的种子数**：文献未提供；我在 M7 里写的 N≥50 是自定的（D 级）。
- **数千年尺度社会 ABM 的 agent 规模上限**：文献未提供。已知的极端规模数字全部来自生物细胞级 agent（行为规则简单得多），不可外推。
- **LLM agent 在长期社会模拟中的可接受调用频率/成本模型**：文献未提供，仅有"成本随人口二次增长"的定性表述。
- **多层级 ABM 中 aggregation/disaggregation 的误差界**：综述指出 Zoom 范式有"信息损失"，但**未给出可用的误差界或守恒律形式**。这是本项目必须自己做实验确定的量。

---

## 5. 数据集与数据库

### 5.1 模型代码归档与标准

| 名称 | 内容 | 覆盖范围 | 访问方式 / URL | 许可 |
|---|---|---|---|---|
| **CoMSES Net Computational Model Library**（原 OpenABM） | 同行评议的 ABM 代码归档，分配 DOI，有 Open Code Badge 制度；官方推荐标准包括 ODD（含 Summary / Nested / Delta / ODD+D 变体）、TRACE、codemeta、DataCite、Software Description Ontology | 社会-生态科学 ABM 全域 | https://www.comses.net/ ；标准页 https://www.comses.net/resources/standards/ | 逐模型不同 |
| **Artificial Anasazi (Janssen 复现版)** | NetLogo 实现的 Artificial Anasazi，含 Long House Valley 视图 | AD 800–1350 | https://doi.org/10.25937/krp4-g724 （CoMSES codebase 2222, release 1.1.0；提交者 Marco Janssen，2013-01-17；已被下载 5,377 次） | **GPL-2.0** |
| **JASSS**（Journal of Artificial Societies and Social Simulation） | 开放获取，强烈鼓励作者提供足以复现所报告模拟实验的信息；本简报大量核心文献在此 | 社会模拟方法论 | https://www.jasss.org/ | 开放获取 |
| **NetLogo Models Library** | 含 Rebellion（Epstein civil violence 的 NetLogo 版）、Sugarscape 系列等经典模型 | 教学与基准 | 随 NetLogo 发行 | 见各模型 |
| **Mesa examples** | 含 `epstein_civil_violence` 等高级示例，文档给出完整默认参数与实现注释（含"取整不在原文"的关键注释） | Python ABM | https://mesa.readthedocs.io/ | Apache-2.0（Mesa 主体） |
| **ABM_Framework_Comparisons** | 跨框架基准（Agents.jl / Ark.jl / NetLogo / MASON / Mesa），含时间比与 LOC | 框架选型 | https://github.com/JuliaDynamics/ABM_Framework_Comparisons ；另有 FLAMEGPU fork | 见仓库 |
| **tDAR — Village Ecodynamics Project Settlement Model v5.4 (VEP I)** | VEP 聚落模型数据集 | 中央 Mesa Verde，AD 600–1300 | https://core.tdar.org/dataset/425610/ | 见 tDAR |
| **village-ecodynamics GitHub** | VEP ABM 源码（含 BeyondHooperville 版本） | 同上 | https://github.com/village-ecodynamics/vep_sim_beyondhooperville | 见仓库 |

### 5.2 校准与分析工具链

| 名称 | 内容 | 访问方式 | 备注 |
|---|---|---|---|
| **BehaviorSearch** | 与 NetLogo 对接的参数空间元启发式搜索工具（GA 等），Stonedahl & Wilensky 的 Anasazi 分析即用此工具 | https://www.behaviorsearch.org/ | 一手来源确认 `[全文]` |
| **NetLogo BehaviorSpace** | 内置实验管理器；支持组合式与 6.4+ 的 subexperiment 非组合式语法；四种输出格式；`--headless` 命令行 | 随 NetLogo；文档 https://docs.netlogo.org/behaviorspace.html | `[页面]` |
| **hetGPy** | Python 的异方差 GP emulator 实现，O'Gara et al. 的 HM 分析所用 | O'Gara (2024b)，论文中引用 | `[全文]` 提及；我未访问其仓库 |
| **hmer**（R） | history matching 工具包（O'Gara 引 Iskauskas, Vernon et al. 2024） | 论文引用 | **未核实**，仅见于参考文献 |
| **Random123 / DEShawResearch** | counter-based RNG 的 C/C++/CUDA 参考实现；通过 TestU01 SmallCrush/Crush/BigCrush | https://github.com/DEShawResearch/random123 ；文档 https://www.thesalmons.org/john/random123/ | `[页面]` |
| **RandomNumbers.jl (Random123 家族)** | Julia 侧实现 | https://juliarandom.github.io/RandomNumbers.jl/ | `[摘要]` |
| **W3C PROV-DM** | provenance 数据模型标准；已被用于仿真模型的 provenance 本体 | W3C 规范 | 由 Ruscheinski et al. 2018 引入仿真领域 `[摘要]` |

### 5.3 平台

| 平台 | 语言 | 定位 | URL |
|---|---|---|---|
| NetLogo | NetLogo/Scala/Java | 原型、教学、BehaviorSpace | https://ccl.northwestern.edu/netlogo/ ；docs.netlogo.org |
| Repast Simphony / HPC / 4Py | Java / C++ / Python | 工作站→超算的连续谱 | https://repast.github.io/ |
| MASON | Java | 快速离散事件，model/visualization 严格分离 | https://cs.gmu.edu/~eclab/projects/mason/ |
| Mesa | Python | 生态最丰富（500+ 论文），性能弱 | https://mesa.readthedocs.io/ |
| Agents.jl | Julia | 性能最好（自报）+ 代码最少 | https://juliadynamics.github.io/Agents.jl/ |
| GAMA | GAML | **原生 GIS 矢量/栅格集成 + 多层级（Capture/Release）**，最贴合"真实地理舞台"需求 | https://gama-platform.org/ |
| FLAME GPU 2 | C++/CUDA | GPU 大规模，层级 sub-modelling | https://flamegpu.com/ （论文 doi:10.1002/spe.3207） |

### 5.4 本简报未能覆盖的数据源类型

- 中文 ABM 方法论文献与国内平台（检索预算耗尽前未展开）。
- Seshat Global History Databank 等历史数据库（属其他简报领域，本简报只在第 6 节提及需求）。
- 具体的东亚古气候/考古栅格数据集（属其他简报领域）。

---

## 6. 中国与东亚特定证据

**诚实的总结：ABM 方法论本身没有"中国特定"版本；但"以东亚为舞台的 ABM"这件事在文献里几乎是空白，这本身是本简报最重要的发现之一。**

### 6.1 我在本次检索中**没有**找到的东西

- 一个已发表、文档完整（ODD 级）、经过校准并公开代码的**中国/东亚早期文明形成 ABM**。检索"agent-based model China archaeology settlement pattern simulation Yellow River Neolithic ABM"返回的全是**统计/机器学习分析**而非 ABM，或是**现代**土地利用模拟。
- 一个东亚版的 Village Ecodynamics Project（即"真实地形 + 真实考古人口估计 + 家户级 ABM + 数百年长跑"的组合）。
- **结论**: 我们不能像美国西南部研究者那样"接过一个已校准的区域 ABM 再改"。我们必须从各领域简报（考古、古气候、人口、经济史）自己组装 POM 模式电池。这提高了 Phase 0 研究的必要性，也意味着**我们的模型没有可对齐（dock）的先例模型**——docking 只能在我们自己的双实现之间做（M13）。

### 6.2 我确实找到的、可作为 POM 模式候选的东亚量化结果

这些属于其他简报的领域，我在此只记录**它们可以充当哪种模式**，并标注我只读到摘要：

| 潜在模式 | 数值/形状 | 来源 | 可靠度 | 可作为哪类 POM 判据 |
|---|---|---|---|---|
| 稻作农业扩散速率 | **0.72–0.92 km/yr**（95% 置信；基于 201 个有栽培稻的早期新石器遗址） | "The spread of domesticated rice in eastern and southeastern Asia was mainly demic", *Journal of Archaeological Science*（ScienceDirect S0305440318303765） | `[摘要]` **C 级** | **区间型**：我们的农业扩散前沿速率应落在同量级（0.1–数 km/yr） |
| 粟作农业扩散的**不连续性** | "早期粟作农业促成了指数式人口增长，并在东亚**不连续地**扩散" | *Science Advances* doi:10.1126/sciadv.aax6225 | `[摘要]` **C 级** | **形状型**：扩散前沿不应是光滑的 Fisher 波，应有跳跃与停滞 |
| 双重农业结构 | 南方稻、北方粟（黍/粟），两者约 10,000 年前分别在长江与黄河流域驯化；两流域之间有一条稻粟混作带 | 多篇（Antiquity / The Holocene / Cell Genomics 等） | `[摘要]` **C 级** | **存在性型**：模型应能自发产生两个以上独立的作物-生态复合体及其之间的混作过渡带 |
| 扩散机制的混合性 | 粟向俄罗斯滨海边疆区的扩散支持"内陆满洲路线"，且**长距离文化交流与 demic diffusion 都参与** | *Journal of Archaeological Science: Reports* S2352226719300534 | `[摘要]` **C 级** | **关系型**：模型中人口迁移与纯信息传播应同时存在且比例随距离变化 |
| 新石器聚落选址的**阈值效应** | GAM 分析显示环境变量与聚落存在非线性阈值关系；"古代人群系统性地回避环境不足与环境过剩两端" | 黄河流域 / 嵩山地区研究（ScienceDirect S0031018225005656；PMC13390836） | `[摘要]` **C 级** | **形状型**：模型的选址效用函数不应单调，应有内部最优 |
| 浙江新石器遗址分类 | XGBoost + SHAP 对 432 个遗址按文化期区分环境选择模式 | *npj Heritage Science* s40494-025-01753-4 | `[摘要]` **C 级** | 提供**分期变化**的模式：选址偏好本身应随文化期演化 |

**方法论意义**：这些结果全部是"从数据里提取的模式"，正是 POM 需要的输入形状（多尺度、多层级、弱约束）。但它们**没有一个**是 ABM 参数，因此不能直接填进我们的模型；它们只能作为**验收判据**。这正是 POM 的正确用法。

### 6.3 中国背景下 ABM 的现有用法（与我们的目标不同，但技术可借）

- **CA-ABM + PLUS 混合模型**被用于模拟中国乡村聚落的时空动态（新疆干旱区绿洲上游流域案例），驱动因子含自然环境、社会经济条件与人类决策。`[摘要]` **C 级**。
  - 借鉴点：CA（细胞自动机）负责土地/景观状态演化 + ABM 负责决策，这种混合正好对应我们"规则数学核心 + agent"的分工。
- 中国聚落考古学的方法传统（catchment analysis、聚落等级、rank-size 法则 + 社会演化模型）已被用于建模黄河流域新石器复杂社会的发展；中美日照项目自 1990 年代中期开始做全覆盖系统调查。`[摘要]` **C 级**。
  - 借鉴点：**rank-size 法则**是一个成熟的、跨文化可比的聚落层级模式，应当进入我们的 POM 电池（作为区间型判据：Zipf 指数落在某区间，且随政治整合度变化）。

### 6.4 对本项目的一条特殊警告（东亚舞台特有）

**地理线索泄漏（geographic cue leakage）**：因为我们用的是真实中国及周边东亚地理，任何看到"黄河/长江/华北平原/四川盆地/朝鲜半岛"轮廓的 LLM 都可能激活关于真实中国史的先验并把剧情结构注入进来。Larooij & Törnberg 明确记录了 LLM 的 **selection bias / data leakage**——"LLM 可能复制历史模式，或表现出 data leakage 即复现既有研究结论，而不是动态生成行为"`[页面]`。这不是假设风险，而是有文献记录的机制。缓解措施见 M12（去专名化投影 + 泄漏探针 + 词汇表检查）。

---

## 7. 学界争议与未解决问题

1. **ABM 究竟能否被经验验证？**
   过参数化批评的标准表述是：由于过参数化及相应的自由度，**几乎任何模拟输出都能用 ABM 生成**，因此"再现 stylized facts 只构成对 ABM 有效性的弱检验"`[摘要]`。Fagiolo, Moneta & Windrum (2007) 是这一批评最系统的整理（*Computational Economics* 30(3): 195–226, doi:10.1007/s10614-007-9104-4）`[摘要]`。争议在于：这是 ABM 的固有缺陷，还是校准方法不成熟的暂时状态？HM/ABC 阵营认为后者。**本项目应假定前者为真并据此设计验证（这也是 M2 + M6 的动机）。**

2. **equifinality（等效性）**：同一观测输出可由许多不同参数组合产生。检索摘要中的表述是："一旦你拥有一大批同样可能且合理的候选，就更难识别哪个是正确的""通过测试太多参数组合，我们能找到若干拟合得极好的组合，但只有一小部分代表输入-输出间的真实相关，而区分虚假相关集与真实相关集几乎不可能"`[摘要]`（另有 IJGIS 2024 的"sequential parameter space search"方法论文，doi:10.1080/13658816.2024.2331536 `[摘要]`）。**未解决**：没有公认的办法在等效参数集之间做裁决，除了收集新的微观数据（这正是 Epstein 对 multiple generators 的答案）。

3. **校准目标应该是什么？** Stonedahl & Wilensky 明确提出这是一个**未解决的方法论问题**："要取得绝对最低的平均误差，就得让每一次运行都等于历史数据……这样的结果表明模型极不现实，只有一条历史路径是可能的"，并把选择摆成三个候选（总是有点接近 / 常常很接近但偶尔差很远 / 偶尔完美但通常差很远），承认"回答这个问题很难，尤其在 facsimile 类历史事件模型里，因为只有一份历史记录可比"，且"这些估计和理论大部分是主观的，正因如此，在校准过程中必须显式处理它们"。`[全文]` **对本项目这是核心争议**，因为我们的立场（真实历史只是校准集）恰好落在"应当保留变异"这一侧。

4. **涌现的定义**：Bedau 的"只能通过模拟推导"定义受到 Baker (2010) 的实质批评——模拟与其他推导方法之间缺乏有原则的边界；"完全特定性"相对于微观元素与时间单位的任意选择；涉及全称命题的性质无法由模拟推导。`[页面]` **未解决**。

5. **OFAT vs 全局 SA**：ten Broeke et al. 主张"OFAT 作为任何 ABM 敏感性分析的起点"，理由是 Sobol′ 对偏斜/重离群分布不适用且缺乏机制洞察 `[页面]`；但 Stonedahl & Wilensky 在真实模型上实证 OFAT 低估敏感性 6 倍以上 `[全文]`。**两者都对，但结论相反**：OFAT 好在解释，坏在覆盖。我们的解法是两者都做（M8）。

6. **代码强制公开是否必要**：有预印本明确主张 "Mandating Code Disclosure is Unnecessary — Strict Model Verification Does Not Require Accessing Original Computer Code"（arXiv:2105.05170）`[摘要]`，与 Janssen (2017) 的实证（只有 10% 公开）和 Rand & Rust 的强主张（"源码与所有验证数据都应公开"）形成张力。**C 级争议**。

7. **多层级 ABM 缺一个统一形式化**：综述指出所有现有范式都缺乏显式的空间/时间尺度表示（尺度一致性由建模者负责），都无法表示多个同时存在的层级体系，因此无法表示多重重叠角色的 agent；AGR 范式的实现"仍是实验性的、采用极少"`[页面]`。**这是本项目最大的技术空白**：我们需要的正是"一个人同时是族人、官员、信徒"的表示。

8. **LLM agent 能否被验证**：Larooij & Törnberg 的结论是使用 LLM"可能加剧而不是缓解 ABM 的验证挑战"，且生成式 ABM"占据一个含混的方法论空间——既缺乏形式模型的简约性，也缺乏数据驱动方法的经验有效性"`[页面]`。**未解决**，且这是本项目架构上必须绕开而不是解决的问题（因此 M12 把 LLM 限制在"不需要被验证的输出"上）。

9. **纯文本协议是否足够**：有工作主张 ODD 这类文本协议不足以支持机器可复现，提出结构化描述协议（如 VISA）`[摘要]`。这与 Kehoe (2016) 用 Z 语言形式化 Sugarscape 的结论一致。**尚无共识的形式化 ABM 规范语言。**

10. **ABM 分析输出的统计学基础**：Stonedahl & Wilensky 的"30 次重复显著、100 次重复反转"案例说明 ABM 输出分布常常非正态、有重离群，标准 t 检验会给出错误结论。JASSS 18(4):4 "The Complexities of Agent-Based Modeling Output Analysis" 也是这个方向 `[摘要]`。**未解决**：ABM 输出的统计推断缺乏标准实践。

---

## 8. 反模式：本领域常见的错误建模方式（我们必须避免的）

按"对本项目的危害程度"排序。

### AP1. 把外生序列驱动的拟合当成内生机制的解释（**最高危**）
- **表现**：把真实古气候重建序列喂进模型，得到一条与考古人口曲线吻合的曲线，然后宣称"我们的 agent 决策机制解释了兴衰"。
- **证据**：Janssen (2009) 证明纯外生承载力模型（**零 agent 行为**）在 Artificial Anasazi 上取得只差 10–50% 的拟合，且**两模型的最优参数完全相同**；"the agent-based model acted as a smoothing function"。`[页面]`
- **它会让我们的模拟失真在哪里**：我们会误以为"帝国周期"是由我们的政治经济机制涌现出来的，而实际上它是被古气候序列的谱结构注入的。所有基于该机制的后续推断（反事实、"为什么灭亡"）都会指向错误的原因。
- **对策**：M6（空模型支配测试 + 外生序列置换检验）。

### AP2. 用平均误差做校准，从而隐式要求"只有一条历史"
- **证据**：Stonedahl & Wilensky 的原文论证（见第 7 节第 3 点）。`[全文]`
- **失真方式**：会把模型压成一个几乎确定性的系统，直接摧毁 MANDATE 第 3 条（路径依赖）和第 7 条（允许荒诞）。
- **对策**：以**分布对齐**为目标（Rand & Rust 的"真实世界是模型的一个可能输出"），并把"输出方差"本身作为一个需要匹配的量。

### AP3. 只做单因素敏感性分析（OFAT-only）
- **证据**：同一模型上，单变量 ±10% 最大 +50% 误差，多变量 GA 在同一盒子里 >+300%。`[全文]`
- **失真方式**：我们会以为模型稳健，然后在某次参数微调后突然得到一个"文明全灭"的运行，却无法解释。
- **对策**：M8。

### AP4. 隐式调度顺序 / 依赖容器迭代顺序
- **证据**：Kehoe (2016)——**Growing Artificial Societies 书里没有说规则以什么顺序应用**；这是 Sugarscape 不可复现的三大原因之一（"Sequential Biases"）。`[全文]`
- **失真方式**：跨版本、跨机器、并行化后结果漂移；因果链失效（同一输入不再给出同一输出）；反事实实验彻底不可信。
- **对策**：M1（order 显式声明）+ M5（phase 结构 + 逆序遍历 CI 测试）。

### AP5. "方差参数"偷偷改均值（截断污染）
- **证据**：`quality = random-normal(0,1) * harvestVarianceLocation + 1.0` 后 `if quality < 0 → 0`，导致增大方差同时抬高均值；这个 bug 在已发表模型中存活并被 GA 敏感性分析意外发现。`[全文]`
- **失真方式**：我们会以为"气候波动加大"这个实验条件只改变了变异性，实际上同时改变了平均生产力——于是所有关于"波动性 vs 平均水平"的结论都是伪的。
- **对策**：M9 矩位移测试。

### AP6. 死参数（声明但从未生效）
- **证据**：`HarvestVarianceYear` 在 Artificial Anasazi 中初始化后从未被引用。`[全文]`
- **失真方式**：我们会花几周去"调"一个不起作用的参数；更糟的是，在 delta-ODD 里它会被当成真实的模型自由度记入文档。
- **对策**：M9 参数活性测试（构建失败级别）。

### AP7. 把"我没写这条规则"当作涌现的证明
- **证据**：Epstein 的明确表述——"Merely to generate is not necessarily to explain (at least not well) ... A microspecification might generate a macroscopic pattern in a patently absurd—and hence non-explanatory—way"；"generative sufficiency is a necessary but not sufficient condition for explanation"。`[全文]`
- **失真方式**：我们会积累一堆"涌现成果"，每一个都可能是某个未被察觉的硬编码或外生输入的影子。
- **对策**：M7 四段认证（尤其第 1 段词汇表检查与第 2 段消融测试）。

### AP8. 用 face validity 冒充实证验证（LLM 场景下尤甚）
- **证据**：35 篇 LLM-ABM 研究中 **15 篇完全依赖主观评估**；许多研究验证的是"表层输出——比如生成文本的风格真实性——而不是底层机制或交互动力学"；且发现 LLM 输出"更长、更礼貌、更善表达、更尊重"但这种风格差异并不影响 face-validity 判断。`[页面]`
- **失真方式**：我们会因为"这段史料读起来很像真的"而认为世界模拟是对的。这恰恰是 MANDATE 第 10 条（模拟与文学创作分离）要防的事。
- **对策**：把"读起来像"归入叙事层验收，绝不进入世界事实层验收；世界事实层只用 POM 模式电池。

### AP9. 用 LLM 评估 LLM（循环性）
- **证据**：Larooij & Törnberg 指出依赖 LLM 评估自身输出"引发关于循环性与偏置的实质性担忧"。`[页面]`
- **对策**：所有世界事实层判据必须是**可计算的统计量**，不允许"由 LLM 判断这个历史是否合理"。

### AP10. 混淆 verification 与 validation
- **证据**：Rand & Rust 的定义——verification 是"实现 ↔ 概念模型"，validation 是"实现 ↔ 现实"。`[全文]`
- **失真方式**：我们会因为通过了 docking（两个实现一致）而以为机制是对的。
- **对策**：M13 明确标注 docking 只给 verification 级证据。

### AP11. "参数越多越真实"
- **证据**：equifinality 文献的表述——"这一特性会促成模型的过参数化，因为建模者试图放入尽可能多的细节以复现期望但尚未看到的系统输出"。`[摘要]`
- **对策**：M1 的参数清单必须为每个参数标注 `evidence_level`；D 级参数的**数量**本身应作为一个被监控的项目健康指标。

### AP12. 用 GA/优化校准后只报告最优点，不报告分布
- **证据**：30 重复显著优于 → 100 重复反转。`[全文]`
- **对策**：所有校准结果必须以分布形式报告（均值、σ、中位数、"随机一次运行更优的概率"），且**重复次数必须预先声明**。

### AP13. 全量保存逐 tick 因果图（工程反模式）
- 这条没有文献依据（**D 级**），是我们自己的判断：数千年 × 数万实体 × 每 tick 数十次状态转移，全量祖先图的存储与查询都会失控。
- **对策**：M3 的分级留档 + 事件触发时冻结祖先闭包。**必须在写第一行模拟代码前定下来。**

### AP14. 让 LLM 决定客观结果
- **证据**：Epstein 的"模仿人类输出 ≠ 揭示生成机制"与"图灵测试与解释无关"`[全文]`；Larooij & Törnberg 关于黑箱性与不可验证性 `[页面]`。
- **对策**：M12 提案—裁决架构。这也是 MANDATE 第 5 条的原则，本简报为它提供了文献依据。

---

## 9. 无来源判断（D 级，明确标记为 LLM 常识，不得当作历史规律）

以下全部是我为了让项目能推进而做的假设或设计，**在本次检索中没有找到支撑文献**。它们不得被当作方法论共识或历史规律引用。

1. **"涌现认证"四段协议（M7）作为一个整体是我自拟的。** 其中"词汇表检查（primitive vs composite 类型分层 + 静态分析）"这一步我没有在任何 ABM 文献中见过。它可能有未被我检索到的先例（例如程序分析或 DSL 设计领域），也可能在实践中不可行（因为"什么算 primitive"本身是可争论的）。
2. **N ≥ 50 个种子、`0 < p < 1` 的涌现频率判据**是我编的数字。文献未提供任何"多少种子够"的指导。
3. **空模型支配阈值 τ（M6）**没有来源。Janssen 只给出"外生空模型误差高 10–50%"这一事实，没有说多少算"agent 行为有贡献"。
4. **外生序列置换检验（时间反转 / 块状打乱 / surrogate 替换）**的三种具体形式是我从时间序列分析的常见做法类推的，**没有在 ABM 文献中见到有人这样审计外生输入**。这可能是本项目的一个方法论贡献点，也可能是我遗漏了已有工作。
5. **CBRNG 的 `key/counter` 分层布局**（`key = hash(world_seed, stream_id)`，`counter = (tick, entity_id, purpose_id, draw_index)`）是我的设计。Random123 文档只保证"无状态 + 可重算"，具体怎么分层由使用者定。这个布局的**碰撞风险与统计质量我没有验证**。
6. **"phase 结构 + 逆序遍历 CI 测试"**是我的设计。逆序遍历测试能抓住哈希顺序依赖，但**不能**抓住所有顺序依赖（例如显式排序键本身有 bug 的情况）。
7. **PROV 事件图的三级留档策略（level 0 滚动窗口 / level 1 年度聚合 / level 2 冻结闭包）**是我的设计。分级边界（K 个 tick、"重大事件"的判定）完全没有依据，需要靠 Phase 1 的真实存储测量来定。
8. **M11 的活跃个体 agent 预算 10^4–10^5** 是我的量级猜测。文献未提供任何"数千年社会 ABM 的可行 agent 规模"数据；已知的极端规模数字（17 亿 / 5000 亿）都来自行为规则极简的生物细胞级 agent，不可外推。
9. **"提升/降级时守恒总人数与年龄结构一阶矩"**这个不变量是我提的。多层级 ABM 综述明确指出 Zoom 范式有信息损失，但**没有给出任何守恒律或误差界**。二阶矩（方差）在提升-降级循环中是否也需要守恒、以及不守恒会导致什么偏差，我不知道。
10. **LLM 决策缓存以 `(prompt_hash, model_id, rng_key)` 为键即可获得重放确定性**——这个断言在逻辑上成立（缓存命中就是纯查表），但它把"确定性"降格成了"记录+回放"，而不是"可从头重算"。这意味着**换模型或改 prompt 就无法重放旧历史**。这个限制是根本性的，我没有找到文献讨论过它在长期社会模拟中的后果。
11. **去专名化投影（给 LLM 的 prompt 中移除真实地名/族名/朝代名）能有效抑制 data leakage**——这是我的推断。Larooij & Törnberg 记录了 leakage 现象，但**没有**评估任何缓解措施的有效性。去专名化可能不够（LLM 可能从地形拓扑本身识别出黄河流域）。
12. **"泄漏探针"（用真实历史专有名词检测输出）**是我提的测试。我不知道假阴性率会有多高（LLM 可能注入剧情结构而不注入专名）。
13. **三档实验预算（Tier 0/1/2）的划分**是我的设计；各档的运行次数量级有文献支撑（见 4.2），但"哪些检查放哪一档"是我的判断。
14. **AGR（Agent/Group/Role）范式适合表示"一个人同时是族人、官员、信徒"** —— 综述确实指出 AGR 是为此设计的、且指出现有多层级范式无法做到这一点；但**综述同时说 AGR 实现"仍是实验性的、采用极少"**。我判断"我们应该自己实现 AGR 思想"，这个判断没有成功案例支撑。
15. **POM 模式的三种 predicate 形状（序数 / 区间 / 存在性）**是我的形式化。POM 原文没有规定 predicate 的形状。
16. **"D 级参数的数量应作为项目健康指标"** —— 我编的管理指标。
17. **Epstein civil violence 参数表中"BaseNutritionNeed 160 = 160 kg/人 × 5 人 = 800 kg/户"的换算**（4.3 节）是我的推断，两个来源都没有明说单位。
18. **对 Agents.jl 自报基准的怀疑（"Mesa 慢 59–159 倍很可能是 Mesa 侧实现未优化邻域搜索"）**是我的推测，没有验证。
19. **建议采用 GAMA 作为地理集成层** —— 基于"GAMA 原生集成 GIS 矢量与栅格"这一有来源的事实，但"因此它最适合本项目"是我的判断；GAMA 在数千年长跑与自定义内核上的性能我没有任何数据。
20. **本项目"真实中国史应落在模型输出分布的支撑集内、但不应是模型的众数"** —— 这是我从 Rand & Rust 的"real world is a possible output"推出的项目专属判据。原文没有说"不应是众数"这半句；那半句是我为了满足 MANDATE"虚拟文明没有义务重复真实历史"而加的。

---

## 10. 参考文献

标注：**[V]** = 本次检索中我读到了正文/期刊全文页并据以写作；**[A]** = 只读到摘要或检索结果摘要；**[R]** = 凭记忆写下、本次未确认。

### 协议与文档标准
1. **[V]** Grimm, V., Railsback, S. F., Vincenot, C. E., Berger, U., Gallagher, C., DeAngelis, D. L., ..., Ayllón, D. (2020). "The ODD Protocol for Describing Agent-Based and Other Simulation Models: A Second Update to Improve Clarity, Replication, and Structural Realism." *JASSS* 23(2):7. doi:10.18564/jasss.4259 `[已核验]`
2. **[R]** Grimm, V., Berger, U., Bastiansen, F., et al. (2006). "A standard protocol for describing individual-based and agent-based models." *Ecological Modelling* 198(1–2): 115–126.
3. **[A]** Grimm, V., Berger, U., DeAngelis, D. L., Polhill, J. G., Giske, J., Railsback, S. F. (2010). "The ODD protocol: A review and first update." *Ecological Modelling* 221(23): 2760–2768.
4. **[A]** Müller, B., Bohn, F., Dreßler, G., Groeneveld, J., Klassert, C., Martin, R., Schlüter, M., Schulze, J., Weise, H., Schwarz, N. (2013). "Describing human decisions in agent-based models – ODD + D, an extension of the ODD protocol." *Environmental Modelling & Software* 48: 37–48. doi:10.1016/j.envsoft.2013.06.003
5. **[A]** Grimm, V., Augusiak, J., Focks, A., et al. (2014). "Towards better modelling and decision support: Documenting model development, testing, and analysis using TRACE." *Ecological Modelling*.
6. **[A]** Augusiak, J., Van den Brink, P. J., Grimm, V. (2014). "Merging validation and evaluation of ecological models to 'evaludation'." *Ecological Modelling*.
7. **[R]** Schmolke, A., Thorbek, P., DeAngelis, D. L., Grimm, V. (2010). "Ecological models supporting environmental decision making: a strategy for the future." *Trends in Ecology & Evolution* 25(8): 479–486.
8. **[V]** CoMSES Net, "Standards & Best Practices." https://www.comses.net/resources/standards/

### Pattern-Oriented Modeling
9. **[A]** Grimm, V., Revilla, E., Berger, U., Jeltsch, F., Mooij, W. M., Railsback, S. F., Thulke, H.-H., Weiner, J., Wiegand, T., DeAngelis, D. L. (2005). "Pattern-Oriented Modeling of Agent-Based Complex Systems: Lessons from Ecology." *Science* 310(5750): 987–991. doi:10.1126/science.1116681 `[已核验]`
10. **[R]** Grimm, V. & Railsback, S. F. (2005). *Individual-based Modeling and Ecology*. Princeton University Press.

### 验证、确认与对齐
11. **[V]** Rand, W. & Rust, R. T. (2011). "Agent-based modeling in marketing: Guidelines for rigor." *International Journal of Research in Marketing* 28(3): 181–193. doi:10.1016/j.ijresmar.2011.04.002 —— **读到全文，第 2.5 节的 verification/validation 分类逐字来自此文** `[已核验]`
12. **[A]** Sargent, R. G. 多届 Winter Simulation Conference 论文，包括 "An Expository on Verification and Validation of Simulation Models" (WSC 1985)、"Verification and validation of simulation models"（多届，如 WSC 1998, 2008, 2013）、"Verification, Validation, and Accreditation of Simulation Models" (WSC 2000)。**具体的三角形范式图我凭记忆熟悉，标 [R]。**
13. **[A]** Axtell, R., Axelrod, R., Epstein, J. M., Cohen, M. D. (1996). "Aligning simulation models: A case study and results." *Computational and Mathematical Organization Theory* 1(2): 123–141. doi:10.1007/BF01299065
14. **[A]** Wilensky, U. & Rand, W. (2007). "Making Models Match: Replicating an Agent-Based Model." *JASSS* 10(4):2.
15. **[V]** Miodownik, D., Cartrite, B., Bhavnani, R. (2010). "Between Replication and Docking." *JASSS* 13(3):1. doi:10.18564/jasss.1627 —— 三级等价判据的操作化转述来自此页 `[已修正: 完整标题为 "Between Replication and Docking: \"Adaptive Agents, Political Institutions, and Civic Traditions\" Revisited"，其余信息（作者、2010、JASSS 13(3):1、doi:10.18564/jasss.1627）正确]`
16. **[A]** Fagiolo, G., Moneta, A., Windrum, P. (2007). "A Critical Guide to Empirical Validation of Agent-Based Models in Economics: Methodologies, Procedures, and Open Problems." *Computational Economics* 30(3): 195–226. doi:10.1007/s10614-007-9104-4

### 校准与敏感性分析
17. **[V]** ten Broeke, G., van Voorn, G., Ligtenberg, A. (2016). "Which Sensitivity Analysis Method Should I Use for My Agent-Based Model?" *JASSS* 19(1):5. doi:10.18564/jasss.2857 `[已核验]`
18. **[V]** ten Broeke, G., van Voorn, G., Ligtenberg, A., Molenaar, J. (2021). "The Use of Surrogate Models to Analyse Agent-Based Models." *JASSS* 24(2):3. doi:10.18564/jasss.4530
19. **[V]** McCulloch, J., Ge, J., Ward, J. A., Heppenstall, A., Polhill, J. G., Malleson, N. (2022). "Calibrating Agent-Based Models Using Uncertainty Quantification Methods." *JASSS* 25(2):1. doi:10.18564/jasss.4791
20. **[V]** O'Gara, D., Kerr, C. C., Klein, D. J., Binois, M., Garnett, R., Hammond, R. A. "Improving Policy-Oriented Agent-Based Modeling with History Matching: A Case Study." arXiv:2501.00616 —— **读到全文，4.2 节的 HM 预算数字来自此文**（预印本，未确认是否已同行评议） `[已核验]` （arXiv 提交日 2024-12-31，标识号 2501.00616，通常著录为 2025；截至核验日仍未见期刊卷期）
21. **[A]** Vernon, I., Goldstein, M., Bower, R. G. (2010). "Galaxy Formation: a Bayesian Uncertainty Analysis." *Bayesian Analysis* 5(4): 619–670.
22. **[A]** Vernon, I., Goldstein, M., Bower, R. G. (2014). "Galaxy Formation: Bayesian History Matching for the Observable Universe." *Statistical Science* 29(1).
23. **[A]** Grazzini, J., Richiardi, M. G., Tsionas, M. (2017). "Bayesian estimation of agent-based models." *Journal of Economic Dynamics and Control* 77: 26–47. doi:10.1016/j.jedc.2017.01.014
24. **[A]** Lamperti, F., Roventini, A., Sani, A. (2018). "Agent-based model calibration using machine learning surrogates." *Journal of Economic Dynamics and Control* 90: 366–389. （另见 arXiv:1703.10639）
25. **[A]** Crema, E. R., Kandler, A., Shennan, S. (2016). "Revealing patterns of cultural transmission from frequency data: equilibrium and non-equilibrium assumptions." *Scientific Reports* 6: 39122. doi:10.1038/srep39122
26. **[A]** Binois, M., Gramacy, R. B., Ludkovski, M. (2018). heteroskedastic GP 方法（经 O'Gara et al. 引用；我未读原文）
27. **[A]** Pukelsheim, F. (1994). "The three sigma rule." *The American Statistician*（经 O'Gara et al. 引用；我未读原文）
28. **[A]** Andrianakis, I., Vernon, I., McCreesh, N., et al. (2015). history matching 应用（经 O'Gara et al. 引用；我未读原文）
29. **[A]** ten Broeke 等引用的 Saltelli 采样方案（Sobol′ 实现）—— 我未读 Saltelli 原文
30. **[A]** "Addressing equifinality in agent-based modeling: a sequential parameter space search method based on sensitivity analysis." *IJGIS* 38(6), 2024. doi:10.1080/13658816.2024.2331536

### 经典模型
31. **[A]** Epstein, J. M. & Axtell, R. (1996). *Growing Artificial Societies: Social Science from the Bottom Up*. MIT Press. ISBN 9780262550253
32. **[V]** Kehoe, J. (2016). "The Specification of Sugarscape." arXiv:1505.06012v3 —— **读到全文，2.7 节的三类问题分类逐字来自此文** `[已核验]` （arXiv v1 为 2015-05-22，v3 为 2016-11-07，故著录年份 2016 成立；作者全名 Joseph Kehoe）
33. **[A]** Dean, J. S., Gumerman, G. J., Epstein, J. M., Axtell, R. L., Swedlund, A. C., Parker, M. T., McCarroll, S. (2000). "Understanding Anasazi Culture Change Through Agent-Based Modeling." In Kohler, T. & Gumerman, G. (eds.) *Dynamics in Human and Primate Societies: Agent-Based Modeling of Social and Spatial Processes*, Oxford University Press, pp. 179–205/206.
34. **[A]** Axtell, R. L., Epstein, J. M., Dean, J. S., Gumerman, G. J., Swedlund, A. C., Harburger, J., Chakravarty, S., Hammond, R., Parker, J., Parker, M. (2002). "Population growth and collapse in a multiagent model of the Kayenta Anasazi in Long House Valley." *PNAS* 99(suppl. 3): 7275–7279. doi:10.1073/pnas.092080799
35. **[V]** Janssen, M. A. (2009). "Understanding Artificial Anasazi." *JASSS* 12(4):13 —— **读到期刊全文页的详细抽取；4.3 节多数数值来自此处** `[已核验]`
36. **[V]** Stonedahl, F. & Wilensky, U. (2010). "Evolutionary Robustness Checking in the Artificial Anasazi Model." *Proceedings of the AAAI Fall Symposium on Complex Adaptive Systems: Resilience, Robustness, and Evolvability*, Arlington VA, Nov 11–13, 2010, pp. 120–128. —— **读到全文；本简报最重要的量化来源之一** `[已核验]` （原件页码实为 pp. 120–129，正文止于 128、参考文献在 129；会议论文集编号 FS-10-03）
37. **[V]** Gunaratne, C. & Garibay, I. (2020). "Evolutionary model discovery of causal factors behind the socio-agricultural behavior of the Ancestral Pueblo." *PLoS ONE* 15(12): e0239922. doi:10.1371/journal.pone.0239922 （另见 arXiv:1802.00435） `[已核验]`
38. **[A]** Epstein, J. M. (2002). "Modeling civil violence: An agent-based computational approach." *PNAS* 99(suppl. 3): 7243–7250. doi:10.1073/pnas.092080199 —— **PNAS PDF 返回 403；参数表来自 Mesa 实现文档，不是原文**
39. **[V]** Mesa 官方文档, "Epstein Civil Violence Model." https://mesa.readthedocs.io/stable/examples/advanced/epstein_civil_violence.html
40. **[A]** Kohler, T. A. 等，Village Ecodynamics Project 系列（含 *American Antiquity* 的 "Historical Ecology in the Mesa Verde Region" 与 "How to Make a Polity (in the Central Mesa Verde Region)"；JASSS 16(4):4 "Simulating Social and Economic Specialization in Small-Scale Agricultural Societies"）
41. **[V]** CoMSES codebase 2222, "Artificial Anasazi" release 1.1.0（Janssen 提交，NetLogo，GPL-2.0）. doi:10.25937/krp4-g724
42. **[A]** Miller, J. H. (1998). "Active Nonlinear Tests (ANTs) of Complex Simulation Models." *Management Science*（经 Stonedahl & Wilensky 引用；±10% 规则出自此文）

### 生成主义、涌现与 iGSS
43. **[V]** Epstein, J. M. (2023). "Inverse Generative Social Science: Backward to the Future." *JASSS* 26(2):9. doi:10.18564/jasss.5083 —— **读到全文；2.12 节的引文逐字来自此文** `[已核验]`
44. **[A]** Epstein, J. M. (2008). "Why Model?" *JASSS* 11(4):12.
45. **[R]** Epstein, J. M. (1999). "Agent-based computational models and generative social science." *Complexity* 4(5): 41–60.
46. **[R]** Epstein, J. M. (2006). *Generative Social Science: Studies in Agent-Based Computational Modeling*. Princeton University Press.（p.53 的引文我在 Epstein 2023 全文中读到了转引 —— 该转引本身是 **[V]**）
47. **[R]** Epstein, J. M. (2013). *Agent_Zero: Toward Neurocognitive Foundations for Generative Social Science*. Princeton University Press.
48. **[A]** Vu, T. M., Probst, C., Epstein, J. M., Brennan, A., Strong, M., Purshouse, R. C. (2019). "Toward inverse generative social science using multi-objective genetic programming." *GECCO '19*. doi:10.1145/3321707.3321840
49. **[A]** Bedau, M. A. (1997). "Weak Emergence." *Philosophical Perspectives* 11: 375–399.
50. **[V]** Baker, L. (2010). "Simulation-Based Definitions of Emergence." *JASSS* 13(1):9. doi:10.18564/jasss.1531 `[已修正: 作者为 Baker, A.（Alan Baker），非 "Baker, L."；其余信息正确]`

### 多层级 / 变粒度
51. **[V]** Brugière, A., Nguyen-Ngoc, D., Drogoul, A. (2022). "Handling multiple levels in agent-based models of complex socio-environmental systems: A comprehensive review." *Frontiers in Applied Mathematics and Statistics*. doi:10.3389/fams.2022.1020353 —— **2.16 节的四范式分类表来自此文** `[已核验]` （完整卷期为 Frontiers in Applied Mathematics and Statistics 8: 1020353）
52. **[A]** Morvan, G. (2012). "Multi-level agent-based modeling – A literature survey." arXiv:1205.0561
53. **[A]** Hjorth, A., Head, B., Brady, C., Wilensky, U. (2020). "LevelSpace: A NetLogo Extension for Multi-Level Agent-Based Modeling." *JASSS* 23(1):4.
54. **[A]** "A Methodology to Engineer and Validate Dynamic Multi-level Multi-agent Based Simulations." arXiv:1311.5108
55. **[A]** "Agent Based Simulation Design for Aggregation and Disaggregation." DTIC ADA558453

### 平台
56. **[V]** JuliaDynamics, ABM_Framework_Comparisons（基准仓库）. https://github.com/JuliaDynamics/ABM_Framework_Comparisons
57. **[V]** Datseris, G., Vahdati, A. R., DuBois, T. C. (2022/2024). "Agents.jl: a performant and feature-full agent-based modeling software of minimal code complexity." *Simulation: Transactions of the Society for Modeling and Simulation International*. doi:10.1177/00375497211068820 —— 读到全文的相关章节
58. **[A]** ter Hoeven, E., Kwakkel, J., Hess, V., Pike, T., Wang, B., rht, Kazil, J. (2025). "Mesa 3: Agent-based modeling with Python in 2025." *JOSS* 10(107): 7668. doi:10.21105/joss.07668
59. **[A]** Luke, S., Cioffi-Revilla, C., Panait, L., Sullivan, K., Balan, G. (2005). "MASON: A Multiagent Simulation Environment." *Simulation* 81(7): 517–527. doi:10.1177/0037549705058073
60. **[A]** North, M. J., Collier, N. T., Vos, J. R. (2006). "Experiences creating three implementations of the Repast agent modeling toolkit." *ACM TOMACS* 16(1): 1–25. doi:10.1145/1122012.1122013
61. **[A]** Collier, N. & North, M. (2013). "Parallel agent-based simulation with Repast for High Performance Computing." *Simulation*. doi:10.1177/0037549712462620
62. **[A]** Collier, N. & Ozik, J. "Distributed Agent-Based Simulation with Repast4Py." *Proceedings of the Winter Simulation Conference*.
63. **[V]** Repast Suite 官方站点（版本号与定位）. https://repast.github.io/
64. **[R]** Wilensky, U. (1999). NetLogo. Center for Connected Learning and Computer-Based Modeling, Northwestern University.
65. **[V]** NetLogo 官方手册, "BehaviorSpace." https://docs.netlogo.org/behaviorspace.html
66. **[A]** Taillandier, P., Gaudou, B., Grignard, A., Huynh, Q.-N., Marilleau, N., Caillou, P., Philippon, D., Drogoul, A. (2019). "Building, composing and experimenting complex spatial models with the GAMA platform." *GeoInformatica* 23(2): 299–322.
67. **[A]** GAMA 参与式建模专文. *JASSS* 22(2):3.
68. **[A]** Richmond, P., Chisholm, R., Heywood, P., Chimeh, M. K., Leach, M. (2023). "FLAME GPU 2: A framework for flexible and performant agent based simulation on GPUs." *Software: Practice and Experience*. doi:10.1002/spe.3207
69. **[A]** "Design and Analysis of an Extreme-Scale, High-Performance, and Modular Agent-Based Simulation Platform." arXiv:2503.10796（BioDynaMo；**预印本**）
70. **[A]** "TeraAgent: A Distributed Agent-Based Simulation Engine for Simulating Half a Trillion Agents." arXiv:2509.24063（**预印本**）

### 可复现性、provenance、随机数
71. **[V]** Janssen, M. A. (2017). "The Practice of Archiving Model Code of Agent-Based Models." *JASSS* 20(1):2. doi:10.18564/jasss.3317 `[已核验]`
72. **[A]** "On code sharing and model documentation of published individual and agent-based models." *Environmental Modelling & Software*（ScienceDirect S1364815220309300）—— 18%/2018 的数字来自此文的检索摘要，**我未读原文**
73. **[A]** "Mandating Code Disclosure is Unnecessary – Strict Model Verification Does Not Require Accessing Original Computer Code." arXiv:2105.05170（**预印本**）
74. **[A]** Ruscheinski, A., Gjorgevikj, D., Dombrowsky, M., Budde, K., Uhrmacher, A. M. (2018). "Towards a PROV Ontology for Simulation Models." *IPAW 2018*, doi:10.1007/978-3-319-98379-0_17
75. **[A]** "SIMPROV: Provenance capturing for simulation studies." *PLOS ONE*（另见 bioRxiv 2025.02.26.640288）
76. **[A]** Ruscheinski, A. et al. "Relating simulation studies by provenance—Developing a family of Wnt signaling models." *PLOS Computational Biology* doi:10.1371/journal.pcbi.1009227
77. **[A]** "Automatic Reuse, Adaption, and Execution of Simulation Experiments via Provenance Patterns." arXiv:2109.06776
78. **[A]** Salmon, J. K., Moraes, M. A., Dror, R. O., Shaw, D. E. (2011). "Parallel random numbers: as easy as 1, 2, 3." *SC '11*. doi:10.1145/2063384.2063405 `[已核验]` （SC '11 论文集页码 1–12，文章号 16）
79. **[V]** Random123 官方文档（无状态性、可复现性、TestU01 通过情况）. https://www.thesalmons.org/john/random123/releases/latest/docs/
80. **[A]** "The Complexities of Agent-Based Modeling Output Analysis." *JASSS* 18(4):4
81. **[A]** "VISA: A Structured Description Protocol for Agent-Based Simulation Models Towards Machine Reproducibility." arXiv:2607.28027（**预印本**）

### LLM 与生成式社会模拟
82. **[V]** Larooij, M. & Törnberg, P. (2025). "Validation is the central challenge for generative social simulation: a critical review of LLMs in agent-based modeling." *Artificial Intelligence Review*. doi:10.1007/s10462-025-11412-6 —— **读到 PMC 全文抽取；2.18 节的引文与统计来自此文** `[已核验]` （完整卷期为 Artificial Intelligence Review 59(1): 15，2025-11-18 在线发表）
83. **[A]** Park, J. S., O'Brien, J., Cai, C. J., Morris, M. R., Liang, P., Bernstein, M. S. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." *UIST '23*. doi:10.1145/3586183.3606763
84. **[A]** "LLM-based Human Simulations Have Not Yet Been Reliable." arXiv:2501.08579（**预印本**；4.7 节的三个百分比来自其检索摘要）
85. **[A]** "Necessary but Not Sufficient: Temperature Control and Reproducibility in LLM-as-Judge Safety Evaluations." arXiv:2606.26185（**预印本**）
86. **[A]** "AI Agents Alone Are Not (Yet) Sufficient for Social Simulation." arXiv:2603.00113（**预印本**，未读）

### 东亚相关（属其他简报领域，此处仅作 POM 模式候选来源）
87. **[A]** "The spread of domesticated rice in eastern and southeastern Asia was mainly demic." *Journal of Archaeological Science*（S0305440318303765）—— 0.72–0.92 km/yr
88. **[A]** "Discontinuous spread of millet agriculture in eastern Asia and prehistoric population dynamics." *Science Advances*. doi:10.1126/sciadv.aax6225
89. **[A]** Silva, F., Fuller, D. Q., et al. "Modelling the Geographical Origin of Rice Cultivation in Asia Using the Rice Archaeological Database." *PLOS ONE*. doi:10.1371/journal.pone.0137024
90. **[A]** "A tale of two rice varieties: Modelling the prehistoric dispersals of japonica and proto-indica rices."（UCL Discovery 10059719）
91. **[A]** "Millet agriculture dispersed from Northeast China to the Russian Far East: Integrating archaeology, genetics, and linguistics." *JAS: Reports*（S2352226719300534）
92. **[A]** "Settlement adaptation and social evolution under mid-holocene environmental duress in the Yellow River Basin." *Palaeogeography...*（S0031018225005656）
93. **[A]** "Settlement strategies and their driving mechanisms of Neolithic settlements using machine learning approaches: a case study in Zhejiang Province." *npj Heritage Science*. doi:10.1038/s40494-025-01753-4
94. **[A]** "Theory and methods of settlement archaeology – the Chinese contribution." *World Archaeology*. doi:10.1080/00438243.2023.2216182
95. **[A]** "Simulating the spatiotemporal variations of oasis rural settlements in the upper reaches of rivers of arid regions in Xinjiang, China."（PMC9522261；CA-ABM + PLUS）

---

## 附：检索覆盖说明

**做到了什么**：
- 200 次 WebSearch 预算全部用尽（本简报占用其中约 30 次，其余为同会话其他简报），另做了约 25 次 WebFetch。
- 对 6 篇最承重的文献做了**本地 PDF 全文抽取并逐段阅读**：Rand & Rust 2011、Stonedahl & Wilensky 2010、Epstein 2023、O'Gara et al. 2025、Kehoe 2016、Datseris et al. 2022。
- 对 9 个期刊/文档 HTML 全文页做了结构化抽取：Grimm et al. 2020 (JASSS)、Janssen 2009 (JASSS)、Janssen 2017 (JASSS)、ten Broeke 2016 & 2021 (JASSS)、McCulloch 2022 (JASSS)、Miodownik 2010 (JASSS)、Baker 2010 (JASSS)、Brugière 2022 (Frontiers)、Larooij & Törnberg 2025 (PMC)、Mesa 文档、NetLogo 文档、repast.github.io、comses.net。

**检索不足之处（诚实披露）**：
1. **Epstein (2002) civil violence 原文未读**：PNAS PDF 返回 403，参数表只能来自 Mesa 实现文档。**第 4.4 节的所有数值都不能当作原文数值引用。**
2. **Grimm et al. 2005 (Science) 与 2006/2010 ODD 原文未读**：付费墙。POM 的三个用途与 ODD 元素演变依赖期刊页/检索摘要与 2020 版的转述。
3. **Axtell et al. 1996 原文未读**：Springer 付费墙。三级等价判据来自 Miodownik et al. 2010 的转述。
4. **Fagiolo, Moneta & Windrum 2007 原文未读**：Springer 付费墙。过参数化批评的具体表述来自检索摘要。
5. **Müller et al. 2013 (ODD+D) 原文未读**：Elsevier 付费墙（有 UFZ 作者稿 PDF 链接但未取）。
6. **TRACE 原文（Grimm et al. 2014 / Schmolke et al. 2010）未读**：8 元素清单来自检索摘要。
7. **Springer 的 Larooij & Törnberg 直链被 IdP 重定向拦住**，改从 PMC 取得全文，成功。
8. **中文文献几乎未检索**：预算耗尽。国内 ABM 方法论工作、以及中文考古/历史模拟文献完全未覆盖。这是明确缺口。
9. **Sugarscape 的具体规则参数（vision/metabolism 的取值范围、糖生长率 α、season 参数等）未取到**：我读了 Kehoe 的 Z 规范全文的结论部分与部分规则，但没有系统抽取常量表。**若需要 Sugarscape 参数，应重新去读 Kehoe 2016 的 §3–§5 或 Growing Artificial Societies 附录。**
10. **VEP 的模型细节与校准结果未深入**：只读到项目/论文摘要级描述。这是与本项目最同构的先例，**值得单独一次深读**。
11. **hmer / hetGPy / Random123 的实际 API 未验证**：只确认了存在与设计原理。
12. **未检索**：ABM 的形式化验证（model checking）文献、DEVS 形式论的详细内容、以及 ABM 与 digital twin 的关系（arXiv:2607.13693 出现在结果里但未读）。

**下一阶段最该核验的三件事**：
1. Epstein (2002) PNAS 原文的参数与方程（当前 4.4 节不可靠）。
2. Grimm et al. (2005) Science 原文中 POM 的三个用途的确切表述（这是 M2 的理论依据）。
3. Village Ecodynamics Project 的 ODD 与校准报告（这是与本项目最同构的先例，可能已经解决了我们在 M11 里担心的粒度问题）。
