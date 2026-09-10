# 因果溯源、确定性重放、分叉与反事实基础设施

- **slug**: `provenance-replay-counterfactual`
- **一句话范围**: 为 civilization-sim 提供"任何重大事件都能被机械地追溯因果、任何历史都能位级重放、任何时点都能分叉、任何'如果当年没有 X'都能被最小干预地实验"的计算机科学与统计学基础，并给出可工程化的数据模型、随机数流设计与存储量级估算。
- **撰写日期**: 2026-09-10
- **检索方式**: Crossref REST API（元数据核验）、W3C 规范原文、开放获取 PDF 全文抽取、Harvard Dataverse API + CHGIS V6 原始 DBF 表头解析、厂商官方文档。WebSearch 配额在本次会话开始前已耗尽，因此全部检索通过 WebFetch / curl 直接命中权威端点完成，未使用搜索引擎排序结果。详见 §10 与末尾"检索覆盖说明"。

---

## 1. 本简报要回答的问题

纲领（MANDATE.md）第 2、6 条与 Phase 0 待答问题"如何保存因果关系""如何保证未来可以重放、分叉和比较不同历史线"直接落在本领域。具体拆成七问：

**Q1（存储）** 一个跑数千年、每 tick 产生成千上万次状态变化的模拟，如何把"完整历史"存下来而不爆盘？分层事件日志 + 快照策略应该长什么样，量级是多少？

**Q2（因果数据模型）** "为什么这个国家会灭亡？"应该由**数据结构**回答，而不是由 LLM 事后编故事。因果链需要什么样的数据模型，才能让这个查询变成一次图遍历 + 一次归因计算？

**Q3（随机数流）** "如果当年那场洪水没发生"这种反事实，如何只改动目标事件、而不让后续所有随机决策整体错位？

**Q4（确定性）** 什么工程纪律能保证同一个种子 + 同一份代码 = 逐位相同的历史？哪些东西天然不可重放（LLM、浮点、并行归约），应该怎么处理？

**Q5（分叉）** 如何在任意历史节点建立平行世界，而不是每次都复制整个世界状态？

**Q6（归因）** 反事实实验跑完之后，怎么把"这场灭亡有多少归因于气候、多少归因于那个具体人物"变成一个数？过度决定（overdetermination）和抢占（preemption）怎么办？

**Q7（世界事实 vs 世界内叙事）** 纲领第 9 条要求"模拟器保存实际发生了什么，世界内人类只知道其中一部分并可能篡改"。这在数据模型上是什么？

---

## 2. 已有成熟模型与理论

### 2.1 W3C PROV 数据模型（PROV-DM / PROV-O / PROV-N）

- **核心机制**：三类节点 —— `Entity`（有固定方面的事物，可实/可虚）、`Activity`（在时间上发生、消费/产生实体的过程）、`Agent`（对活动或实体负责的东西）。核心关系：`wasGeneratedBy`（活动产出实体）、`used`（活动消费实体）、`wasInformedBy`（活动之间通过未指明实体交换而相互告知）、`wasDerivedFrom`（实体到实体的转化/更新）、`wasAttributedTo`（实体归因于 agent）、`wasAssociatedWith`（agent 对活动负责，带 `prov:role`）、`wasStartedBy` / `wasEndedBy`（活动被触发实体或触发活动启动/终止）、`actedOnBehalfOf`（代理链/委托）。扩展：`specializationOf` / `alternateOf`（同一事物的不同刻画）、`Bundle`（把一组 provenance 陈述本身当作实体，从而支持"溯源的溯源"）、`Collection`（集合成员关系）、`Plan`（agent 打算执行的一组步骤，通过 `wasAssociatedWith` 挂到活动上）。
- **形式化程度**：完全形式化。PROV-DM 是 W3C Recommendation（2013-04-30，编辑 Luc Moreau, Paolo Missier），有配套的 PROV-O（OWL 本体）、PROV-N（人可读语法）、PROV-CONSTRAINTS（一致性约束）。
- **状态变量**：节点集 + 带类型的有向边集 + 每条边上的可选属性（`prov:role`、`prov:time`）。时间以 ISO 8601 时刻表示：活动有可选 `startTime`/`endTime`，`generation`/`usage` 等瞬时事件关系有可选 `time` 参数。
- **参数**：无数值参数（它是本体，不是模型）。
- **适用范围**：跨系统交换溯源、审计、可重复性声明。已经被用在科学工作流（VisTrails、noWorkflow）、全系统溯源（CamFlow 输出 PROV-JSON）、以及——关键——**agent-based social simulation**（Pignotti, Polhill & Edwards 2013 的两篇 EDBT/ICDT workshop 论文分别做 "PROV-O provenance traces from agent-based social simulation" 与 "Using provenance to analyse agent-based simulations"）。
- **已知局限**（对本项目很要命，必须自己补）：
  1. PROV 只区分"生成/使用/派生"，**没有区分必要因、充分因、促成因、抑制因**。它能记录"这场战争 used 这份粮价数据"，但不能表达"粮价是这场战争的部分原因，权重 0.3"。
  2. PROV 只有**一条时间轴**（记录中的物理时间），没有 valid time / transaction time 的双时态区分。对本项目要求的"世界事实 vs 世界内叙事"完全不够。
  3. 序列化极其臃肿。CamFlow 论文明说 PROV-JSON 是 "bloated, but standard format"，其协作者通过压缩把体积降到等价 PROV-JSON 图的 **8%**（Pasquier et al. 2017, §6.3，引其 [89] = Hassan et al., Winnower, NDSS 2018）。
  4. 没有随机性/概率的位置。
- **出处**：PROV-DM (W3C REC, 2013-04-30)；Moreau L. et al., "The Open Provenance Model core specification (v1.1)", *Future Generation Computer Systems* 2011, DOI 10.1016/j.future.2010.07.005（PROV 的前身 OPM）。

### 2.2 数据库溯源三分：why / where / how（半环溯源）

- **核心机制**：
  - **where-provenance**：输出里的某个**值**是从输入的哪个位置**复制**来的。
  - **why-provenance**：产生这条输出所需的输入元组的**见证基**（witness basis）—— 哪些输入组合足以推出它。
  - **how-provenance**：不只是"哪些"，还包括"以什么代数方式组合、用了几次"。形式化为**溯源半环**：把每个基础元组标记为变元 $x_i$，查询算子映射为半环运算（连接 → 乘法 $\otimes$，并/投影 → 加法 $\oplus$），输出元组的溯源就是 $\mathbb{N}[X]$ 上的一个多项式。不同半环回代同一多项式即得不同语义：布尔半环 → 存在性，$\mathbb{N}$ → 重数，热带半环 → 最小代价，可能性半环 → 置信度。
- **形式化程度**：完全形式化，有代数唯一性定理。
- **为什么对本项目重要**：这是**唯一一个把"多个原因如何组合"变成可计算代数对象**的成熟理论。"这个国家灭亡"的溯源如果写成一个多项式 $3 \cdot (\text{干旱}_{412} \otimes \text{税制}_{398}) \oplus (\text{北境叛乱}_{419} \otimes \text{国库空虚}_{415})$，就自动同时编码了"两条独立的充分路径"和"每条路径需要哪些合取条件"——这正是 §2.6 的过度决定问题所需要的结构。
- **已知局限**：经典结果针对**正关系代数**（SPJU）。递归（Datalog）下 why-provenance 的复杂度是近年才被刻画的（Calautti, Livshits, Pieris & Schneider 有 2024 年三篇：PODS/SIGMOD `10.1145/3651146`、`10.1145/3695829` 与 AAAI `10.1609/aaai.v38i9.28914`）；带否定/聚合的情形理论上仍不干净。模拟里的因果关系天然带负项（"因为没有发生 X"），这块要自己扩。
- **出处**：Buneman, Khanna & Tan, "Why and Where: A Characterization of Data Provenance", ICDT 2001, DOI 10.1007/3-540-44503-x_20；Green, Karvounarakis & Tannen, "Provenance semirings", PODS 2007, pp. 31–40, DOI 10.1145/1265530.1265535；Cheney, Chiticariu & Tan, "Provenance in Databases: Why, How, and Where", *Foundations and Trends in Databases* 2009, pp. 379–474, DOI 10.1561/1900000006。工程实现参考 ProvSQL（Senellart, Jachiet, Maniu, Ramusat, PVLDB 2018, DOI 10.14778/3229863.3236253）——在 PostgreSQL 里维护半环溯源电路。

### 2.3 事件溯源 / CQRS / append-only log

- **核心机制**：系统的**权威真相是不可变的、只追加的事件序列**；任何"当前状态"都是这个序列的一个折叠（fold / projection）。快照只是折叠的缓存，可以随时丢弃重建。CQRS 把写侧（追加事件）与读侧（物化视图）分离。
- **形式化程度**：半形式化。工业模式，没有统一的形式语义；但折叠等式 $S_n = f(S_{n-1}, e_n)$ 本身就是确定性重放的定义。
- **最有价值的实证研究**：Overeem, Spoor, Jansen & Brinkkemper, "An empirical characterization of event sourced systems and their schema evolution — Lessons from industry", *Journal of Systems and Software* 178:110970 (2021), DOI 10.1016/j.jss.2021.110970（CC BY 4.0；预印本 arXiv:2104.01146）。基于 **25 位工程师、19 个实现**的定性研究，报告了五大实践难题：**事件系统演化（event system evolution）、陡峭学习曲线、可用技术缺乏、重建投影（rebuilding projections）、数据隐私**；以及五种 schema 演化战术：**versioned events、weak schema、upcasting、in-place transformation、copy-and-transform**。
- **对本项目的直接含义**：一个跑 5000 模拟年的项目**必然**会在中途修改事件定义。上述研究说明这是事件溯源系统的头号杀手。因此本项目**从第一天起就必须给每个事件带 schema 版本号，并把 upcasting（旧事件→新事件的纯函数升级）作为一等公民**，否则三个月后你就无法重放三个月前的世界。
- **成熟实现的设计取舍**：
  - **Datomic**：数据的原子单位是 datom `(entity, attribute, value, transaction, added?)`；只累积不覆盖（accumulate-only）；"数据库是一个值"，`as-of` / `since` / `history` 直接查历史；`excision` 是唯一的破坏性删除通道（为 GDPR 之类的硬需求存在）。
  - **XTDB**：双时态。同时跟踪 **system time**（数据何时被写入/更新）与 **valid time**（该行在业务上何时生效），四个时态列默认自动维护；支持乱序到达与对过去数据的**更正**。
  - **Kafka**：分区内有序的 append-only log，靠 offset 定位；本质上给了"事件流 = 真相"的分布式基础设施。
  - 取舍轴线：Datomic/XTDB 把历史查询做进查询语言（贵、强）；Kafka 只保证日志（便宜、需要自己建投影）。**本项目单机为主、查询模式极其定制，因此不应该直接采用其中任何一个，而应该借用它们的模型：Datomic 的 datom 五元组 + XTDB 的双时态 + Kafka 的分段 append-only 文件布局。**（这一取舍是 D 级判断，见 §9。）

### 2.4 双时态数据库（bitemporal）

- **核心机制**：每条断言带两个时间区间。**valid time**（有效时间）= 该事实在被建模世界中为真的时段；**transaction time**（事务时间）= 该事实在数据库中被认为已知的时段。二者正交，构成时间平面上的矩形。修正历史 = 在事务时间上追加一条新记录，把旧记录的事务时间闭区间关掉，而 valid time 指向过去——**旧的错误认知被保留，不是被覆盖**。
- **形式化程度**：完全形式化，且已进标准。TSQL2（Snodgrass ed., *The TSQL2 Temporal Query Language*, Kluwer 1995, DOI 10.1007/978-1-4615-2289-8）；SQL:2011 引入 `PERIOD FOR SYSTEM_TIME` 与应用期（Kulkarni & Michels, "Temporal features in SQL:2011", *ACM SIGMOD Record* 41(3):34–43, 2012, DOI 10.1145/2380776.2380786）。
- **对本项目的映射（这是本简报最重要的结构性建议之一）**：本项目需要的其实是**三时态**——
  1. **世界有效时间（world valid time）**：事件在虚构世界里发生的时刻。
  2. **模拟器事务时间（sim transaction time）**：模拟内核在第几个 tick、第几个 phase 把它写进日志。用于确定性重放与"这条记录是在哪一次计算里产生的"。
  3. **世界内认知时间（in-world knowledge time）**：某个世界内 agent / 史官 / 宗教在何时"相信"这件事。纲领第 4 条（信息边界）与第 9 条（世界事实 vs 官方历史）都落在这一层。
  第 3 层不是数据库意义上的时态，而是**一层独立的、以世界内 agent 为主语的溯源图**：`Belief(agent, proposition, since_tick, source_event, distortion)`。它必须与世界事实图物理分离，只通过"某条 belief 声称指向某个世界事实 id"单向引用。
- **已知局限**：双时态查询的写法反直觉，区间连接代价高；SQL:2011 的实现覆盖参差不齐。

### 2.5 确定性重放（deterministic replay）

- **核心机制**：把执行分解为**确定性部分**与**不确定性输入**，只记录后者，重放时把它回放给确定性部分。Chen Y., Zhang S., Guo Q., Li L., Wu R., Chen T., "Deterministic Replay", *ACM Computing Surveys* 48(2):1–47 (2015), DOI 10.1145/2790077 是这一领域的权威综述。
- **模拟系统中的不确定性来源清单**（工程上必须逐条封死）：
  1. **随机数**：见 §2.7。
  2. **迭代顺序**：哈希表/集合的遍历顺序。Python 文档明确 `PYTHONHASHSEED` 未设置或设为 `random` 时会用随机值给 `str` 和 `bytes` 的哈希加盐，"其目的是允许可重复的哈希"，取值范围 `[0, 4294967295]`，设为 `0` 关闭随机化。Go 官方博客明确："When iterating over a map with a range loop, the iteration order is not specified and is not guaranteed to be the same from one iteration to the next."
  3. **浮点**：见 §2.6 与 §8。
  4. **并行归约顺序**：非结合的浮点加法在不同线程划分下结果不同。Demmel & Nguyen, "Parallel Reproducible Summation", *IEEE Transactions on Computers* 64(7):2060–2070 (2015), DOI 10.1109/tc.2014.2345391 与 Ahrens, Demmel & Nguyen, *ACM TOMS* 2020, DOI 10.1145/3389360 给出了可重现求和算法。
  5. **外部服务**：LLM 推理。见 §3 的 M5。
  6. **时钟/线程调度/地址空间布局**。
- **重放开销的经验量级**：全系统溯源捕获（比通用 record-replay 更重的一类）在 CamFlow 上测得：内核解包 2%、内核编译 2%、Postmark 11%、Apache 12%、redis LPOP 22%、pybench <1%（Pasquier et al. 2017, Tables 4–5）。这给出一个粗略的"完整因果捕获值多少钱"的锚点：**同数量级的开销是 2%–22%，不是 10 倍**。
- **已知局限**：这些数字来自系统调用层捕获，与"模拟内核内部每个决策都记因果边"不是一回事，不能直接外推（见 §9）。

### 2.6 实际因果（actual causality）：Halpern–Pearl 框架

- **核心机制**：Pearl 的结构因果模型（SCM）$M = \langle U, V, F \rangle$ + 三层阶梯（关联 / 干预 $do(\cdot)$ / 反事实）。**反事实的计算三步法（abduction–action–prediction）**：(1) 用观测到的实际历史反推外生变量 $U$ 的后验；(2) 对目标变量施加 $do(X=x')$，切断其入边；(3) 用同一组 $U$ 重新计算下游。**第 1 步就是"保住随机数流"的理论依据**——外生变量在反事实世界里必须保持不变。
- **HP 实际因果定义**：$\vec X = \vec x$ 是 $\varphi$ 的实际原因，当且仅当 (AC1) 二者实际都发生；(AC2) 存在一个"见证"划分 $(\vec Z, \vec W)$ 与替代值 $\vec x'$，使得在把 $\vec W$ 钉在实际值上时，$do(\vec X = \vec x')$ 使 $\varphi$ 不成立；(AC3) $\vec X$ 极小。**AC2 里"把 $\vec W$ 钉住"这一步正是解决过度决定与抢占的机关**：两个同时充分的原因，朴素反事实（去掉 A 结果不变，去掉 B 结果不变 ⇒ 两个都不是原因）会得出荒谬结论；HP 通过在检验 A 时把 B 钉在"未发生"的反事实值上，恢复了 A 的原因地位。
- **程度化归因**：Chockler & Halpern, "Responsibility and Blame: A Structural-Model Approach", *JAIR* 22:93–115 (2004), DOI 10.1613/jair.1391。原文："Causality is typically treated an all-or-nothing concept... We extend the definition of causality introduced by Halpern and Pearl to take into account the degree of responsibility of A for B. For example, if someone wins an election 11-0, then each person who votes for him is less responsible for the victory than if he had won 6-5." 责任度的直觉形式是 $1/(1+k)$，$k$ 是为了让该原因变得关键所需要额外改动的最小变量数。**blame** 进一步对 agent 的认知状态取期望——这与纲领第 4 条（信息边界）天然契合：世界内史官对某人的"归咎"可以用 blame（基于其当时可得信息），而模拟器知道真实的 responsibility。
- **形式化程度**：完全形式化。
- **已知局限（重要争议）**：HP 定义**至今没有定论**。Halpern & Pearl 2005（BJPS 56:843–887, DOI 10.1093/bjps/axi147 与 axi148）之后 Halpern 自己在 *Actual Causality*（MIT Press 2016/2017, DOI 10.7551/mitpress/9780262035026.001.0001）中给出修改版，学界仍在提新定义（例如 Zhu F., "A New Halpern-Pearl Definition of Actual Causality by Appealing to the Default World", *Axiomathes* 2022, DOI 10.1007/s10516-021-09613-z）。计算复杂度也高：Eiter & Lukasiewicz, "Complexity results for structure-based causality", *Artificial Intelligence* 142:53–89 (2002), DOI 10.1016/s0004-3702(02)00271-0 与 "Causes and explanations in the structural-model approach: Tractable cases", *AIJ* 170:542–580 (2006), DOI 10.1016/j.artint.2005.12.003 专门刻画了难度与可处理片段。**我本次未能取得这两篇的全文，因此不引用具体复杂度类**（见 §9 与 §10 标注）。
- **工程含义**：不要指望在 $10^9$ 条边的因果图上跑完整 HP 判定。正确用法是：**先用图上的可达性把候选原因裁到 $O(10)$ 量级，再在这个小集合上跑 HP + responsibility。**

### 2.7 离散随机系统中的反事实：非可识别性与 Gumbel-Max SCM

这是本简报**最关键的单个技术发现**，直接决定 Q3 的答案质量。

- **核心结果（非可识别性）**：Oberst & Sontag, "Counterfactual Off-Policy Evaluation with Gumbel-Max Structural Causal Models", ICML 2019, *PMLR* 97:4881–4890。论文 §3.1 给出一个具体反例：对同一个 4 类分类分布 $p = (0.25, 0.25, 0.3, 0.2)$，用"把 $[0,1]$ 按某个顺序 `ord` 切成区间、抽 $U \sim \mathrm{Unif}(0,1)$ 落在哪个区间就取哪个类"的机制去采样。**不同的排列 `ord` 给出完全相同的观测分布和干预分布，却给出不同的反事实。** 具体地，观测到 $S'=2$，干预后 $p' = (0, 0.25, 0.25, 0.5)$，后验 $P(U \mid S'=2) \sim \mathrm{Unif}[0.25, 0.5)$；在 `ord = [1,2,3,4]` 下反事实结果是 $S'=3$，在 `ord' = [1,2,4,3]` 下是 $S'=4$。原文："Since all choices for `ord` imply the same interventional distribution, there is no way to distinguish between these mechanisms with data."
  > **对本项目的翻译**：`if u < p_famine: famine()` 这一行代码里，**你把哪个结果放在区间前面，就已经在偷偷规定"如果历史不同会发生什么"了**。这不是实现细节，这是一条不可检验的因果假设。
- **反事实稳定性（Definition 5）**：若观测到 $Y_I = i$，则对所有 $j \neq i$，$\frac{p'_i}{p_i} \ge \frac{p'_j}{p_j}$ 蕴含 $P_{M \mid Y_I = i; I'}(Y = j) = 0$。直觉：**只有当某个替代结果的相对似然相对于已观测结果上升了，反事实结果才可能改变。** 推论：若干预只提高了 $i$ 的相对概率而没提高任何别的，反事实结果必然仍是 $i$。定理 1：在二值情形，反事实稳定性蕴含 Pearl 的单调性（monotonicity）。
- **Gumbel-Max SCM（Definition 6 + Theorem 2）**：用 Gumbel-max trick 实现分类抽样 ——
  $$Y = f_y(x, g) := \arg\max_j \{\log P(Y = j \mid X = x) + g_j\}, \qquad g_j = -\log(-\log u_j),\ u_j \sim \mathrm{Unif}(0,1)$$
  **定理 2：Gumbel-Max SCM 满足反事实稳定性。** 直觉：反事实里 Gumbel 变量被钉住不变，要让 argmax 换人，替代项的对数似然必须相对上升。
- **后验推断（§3.4）**：给定观测 $Y_I = i$，可以两种方式采 $P(g \mid Y_I = i)$：(a) 拒绝采样（从先验采 $g$，丢掉 argmax ≠ i 的）；(b) 精确法——已知后验中"最大值"与"argmax"独立，且最大值服从标准 Gumbel（归一化概率下），因此先采最大值，再从截断在该最大值以下的平移 Gumbel 分布采其余分量，最后减去位置参数 $\log p_j$ 得到 $g_j$。然后把这组 $g$ 加到干预后的 $\log p'$ 上取新 argmax。
- **对本项目的工程结论**：**所有离散随机决策都应该用 Gumbel-max（或等价的、满足反事实稳定性的机制）实现，而不是用 `if u < cumsum` 的逆变换采样。** 代价是每次抽样要生成 $k$ 个 Gumbel 而不是 1 个均匀数——对本项目的 tick 频率完全可以承受（Philox 的成本见 §4）。收益是：反事实实验的结果不再依赖于你写代码时枚举分支的顺序。

### 2.8 模拟中的干预式反事实分析

- Herd B. C. & Miles S., "Detecting Causal Relationships in Simulation Models Using Intervention-based Counterfactual Analysis", *ACM Transactions on Intelligent Systems and Technology* 10(5):1–25 (2019), DOI 10.1145/3322123。摘要原文（Crossref）："Central to explanatory simulation models is their capability to not just show *that* but also *why* particular things happen... for complex simulation models, conventional 'blackbox' experiments may be too coarse-grained to cope with spurious relationships. We present an intervention-based causal analysis methodology that exploits the manipulability of computational models, and detects and circumvents spurious effects... First, experiments indicate that the methodology can successfully deal with notoriously tricky situations involving **asymmetric and symmetric overdetermination** and detect fine-grained causal relationships **between events in the simulation**."
- **为什么这是本项目最贴脸的一篇**：它明确把因果关系定义在**模拟中的事件之间**（而不是参数与聚合输出之间），并明确处理对称/非对称过度决定。这正是"为什么这个国家灭亡"要回答的问题形态。
- **局限**：我本次**未取得全文**（KCL 门户 500、ACM DL 403），因此不能报告其具体算法步骤、复杂度或实验规模。所有关于其方法细节的进一步说明都必须先取得全文再写。

### 2.9 持久化数据结构与内容寻址（分叉的底座）

- **Driscoll, Sarnak, Sleator & Tarjan, "Making data structures persistent"**，STOC 1986（DOI 10.1145/12130.12142）与 *Journal of Computer and System Sciences* 38(1):86–124, 1989（DOI 10.1016/0022-0000(89)90034-2）。给出把任意有界入度链接数据结构变成**部分持久 / 完全持久**的通用技术（fat node + node splitting / path copying），摊还空间与时间开销为常数级。**完全持久（fully persistent）意味着可以从任意历史版本继续修改并产生新分支——这正是"平行世界"的数据结构定义。** 后续 Driscoll, Sleator & Tarjan, "Fully persistent lists with catenation", *JACM* 41(5):943–959, 1994, DOI 10.1145/185675.185791。
- **内容寻址**：Merkle R., "A Digital Signature Based on a Conventional Encryption Function", CRYPTO '87, LNCS, pp. 369–378, DOI 10.1007/3-540-48184-2_32。Merkle 树给出"用内容哈希做标识 ⇒ 相同子树自动去重、任意版本可以只存差异"的基础。Git 与 IPFS 是它的两个工业化身（**IPFS 的具体文献我本次未验证，见 §10**）。
- **对本项目**：世界状态若组织成不可变、内容寻址的块（chunk）树，则"在第 3120 年分叉"的成本 = 复制根指针 + 后续只为被修改的块写新块（copy-on-write / 结构共享）。这是**唯一能让"随便建平行世界"变得便宜**的方案。

### 2.10 长时程存储：时序压缩与分层保留

- **Gorilla**（Pelkonen, Franklin, Teller, Cavallaro, Huang, Meza, Veeraraghavan, PVLDB 8(12):1816–1827, 2015, DOI 10.14778/2824032.2824078）。硬数字（从原文抽取）：
  - 未压缩 16 字节/点（8 字节时间戳 + 8 字节 double），压缩后**平均 1.37 字节/点，12 倍缩减**；整体存储足迹降 10 倍。
  - **时间戳：delta-of-delta 变长编码**。$D = (t_n - t_{n-1}) - (t_{n-1} - t_{n-2})$；$D=0$ → 1 bit `'0'`；$D \in [-63, 64]$ → `'10'` + 7 bit；$[-255,256]$ → `'110'` + 9 bit；$[-2047,2048]$ → `'1110'` + 12 bit；否则 `'1111'` + 32 bit。块头存对齐到 2 小时窗口的起始时间戳，块内首个时间戳用 14 bit 存 delta。
  - **实测约 96% 的时间戳可以压到 1 bit**（基于 440,000 个真实时间戳的样本）。
  - **数值：与前值 XOR**，利用相邻值符号位、指数、尾数高位相同的特点，编码前导零个数 + 有效位数。
- **分层保留（tiered retention）的工业先例**：Thanos Compactor 产出三档分辨率——**raw**、**5m**（由超过 40 小时的原始数据降采样得到）、**1h**（由超过 10 天的 5m 数据降采样得到）。官方文档给出的原则："If retention at each resolution is lower than minimum age for the successive downsampling pass, data will be deleted before downsampling can be completed."（即：**每一档的保留期必须长于进入下一档所需的年龄，否则数据在被降采样之前就被删掉了**——这是设计分层策略时最容易踩的坑。）
- **通用压缩基线**：Zstandard 官方基准（Silesia 语料，Core i7-9700K @ 4.9GHz，Ubuntu 24.04，lzbench + GCC 14.2）：`zstd -1` 压缩比 **2.896**，压缩 510 MB/s，解压 1550 MB/s；`zlib -1` 比 2.743、105 MB/s / 390 MB/s；`lz4` 比 2.101、675 MB/s / 3850 MB/s。**注意：2.9 倍是通用文本/二进制混合语料的比值，结构化列式事件日志通常远好于此，但没有可直接引用的通用数字——必须自己实测（见 §9）。**
- **溯源图专用缩减**：LogGC（Lee, Zhang & Xu, CCS 2013, DOI 10.1145/2508859.2516731）做审计日志的垃圾回收；NodeMerge（Tang et al., CCS 2018, DOI 10.1145/3243734.3243763）做基于模板的数据缩减；Winnower（Hassan, Lemay, Aguse, Bates & Moyer, "Towards Scalable Cluster Auditing through Grammatical Inference over Provenance Graphs", NDSS 2018, DOI 10.14722/ndss.2018.23141）用文法推断压缩集群溯源图。**这三篇的具体缩减倍数我本次未能取得全文验证，只能引用 CamFlow 论文转述的 "8% of the equivalent PROV-JSON graph size"。**

### 2.11 敏感性分析与贡献分解（把归因变成数）

- **方差分解 / Sobol' 指数**：Sobol' I. M., "Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates", *Mathematics and Computers in Simulation* 55(1–3):271–280 (2001), DOI 10.1016/s0378-4754(00)00270-6；Saltelli, Annoni, Azzini, Campolongo, Ratto & Tarantola, "Variance based sensitivity analysis of model output. Design and estimator for the total sensitivity index", *Computer Physics Communications* 181(2):259–270 (2010), DOI 10.1016/j.cpc.2009.09.018（给出总效应指数 $S_{T_i}$ 的具体估计量与实验设计）。
- **筛选**：Morris M. D., "Factorial Sampling Plans for Preliminary Computational Experiments", *Technometrics* 33(2):161–174 (1991), DOI 10.1080/00401706.1991.10484804（elementary effects，用于在几百个参数里先筛出重要的几个）。
- **ABM 专用**：Ligmann-Zielinska, Kramer, Spence Cheruvelil & Soranno, "Using Uncertainty and Sensitivity Analyses in Socioecological Agent-Based Models to Improve Their Analytical Performance and Policy Relevance", *PLoS ONE* 9(10):e109779 (2014), DOI 10.1371/journal.pone.0109779；同作者 "Spatially-explicit sensitivity analysis of an agent-based model of land use change", *IJGIS* 27(9):1764–1781 (2013), DOI 10.1080/13658816.2013.782613（**空间显式**的方差分解，与本项目的地理舞台直接相关）。
- **Shapley 式分解在模拟中的应用**：Ng, Lin, Lu & Liu, "Who's to Blame? Unraveling Causal Drivers in Supply Chain Simulations with a Shapley Value Based Attribution Mechanism", *Winter Simulation Conference* 2025, DOI 10.1109/wsc68292.2025.11338977。（存在性已验证；具体方法细节未取全文。）
- **公共随机数（CRN）**：Kleijnen J. P. C., "Analyzing Simulation Experiments with Common Random Numbers", *Management Science* 34(1):65–74 (1988), DOI 10.1287/mnsc.34.1.65。**这是"反事实实验要复用随机数"这一直觉在模拟方法学中的正统名字**，且 Kleijnen 这篇讨论的正是 CRN 引入的响应间相关性如何影响统计分析（不能再假设各处理独立）。

### 2.12 ABM 可重复性的血泪教训

- **Edmonds B. & Hales D., "Replication, Replication and Replication: Some Hard Lessons from Model Alignment", *JASSS* 6(4), 2003.** 两人用两种不同语言独立重实现 Riolo et al. (2001) 的合作演化模型。结论：两个重实现与原论文结果**实质不同**，尤其在低配对数与高捐赠成本区域。**分歧的根源是繁殖时锦标赛选择中的平局打破规则**——原模型在得分相等时偏向系统性选出的那个个体（"selected bias"），而重实现默认了随机打破。修正后进一步发现该模型的合作机制完全依赖于遗传相同的 tag 克隆之间的强制捐赠，而非作者强调的容忍度机制。
  > **这是本项目最应该贴在墙上的一条**：**平局打破规则不是实现细节，它是模型的一部分，而且可能是决定性的那一部分。** 本项目里所有排序、所有 argmax、所有"选一个最优候选"的地方，都必须有显式、确定、被记录的平局打破规则。
- **Polhill J. G., Izquierdo L. R. & Gotts N. M., "What every agent-based modeller should know about floating point arithmetic", *Environmental Modelling & Software* 21(3):283–309 (2006), DOI 10.1016/j.envsoft.2004.10.011.** 领域专属的浮点陷阱综述（本次仅验证了书目元数据，未取全文，因此不引用其具体实验数字）。配套的通用基础是 Goldberg D., "What every computer scientist should know about floating-point arithmetic", *ACM Computing Surveys* 23(1):5–48 (1991), DOI 10.1145/103162.103163。
- **ODD 协议**：Grimm et al., "The ODD protocol: A review and first update", *Ecological Modelling* 221(23):2760–2768 (2010), DOI 10.1016/j.ecolmodel.2010.08.019；Grimm et al. 2020 更新版 DOI 10.1016/j.ecolmodel.2020.109105。ODD 是描述规范而非溯源机制，但它规定了必须公开哪些内容（尤其 "Scheduling" 与 "Stochasticity" 两节）——**本项目的模型文档应当以 ODD 为骨架，因为 ODD 强制你写清楚调度顺序与随机性来源，而这两件事正是重放失败的头两名原因。**

### 2.13 可重现的并行随机数：counter-based PRNG

- **Salmon J. K., Moraes M. A., Dror R. O. & Shaw D. E., "Parallel random numbers: as easy as 1, 2, 3", SC '11, pp. 1–12, DOI 10.1145/2063384.2063405.**
- **核心机制**：抛弃"状态迭代"模型，改为 $\text{output} = b_k(n)$，其中 $b_k$ 是以 $k$ 为密钥的双射（缩减轮数的分组密码），$n$ 是计数器。**没有可变状态**。原文："These counter-based PRNGs are ideally suited to modern multi-core CPUs, GPUs, clusters, and special-purpose hardware because they vectorize and parallelize well, and require little or no memory for state." 并且 "produce at least $2^{64}$ unique parallel streams of random numbers, each with period $2^{128}$ or more"，全部通过 TestU01 的 SmallCrush / Crush / BigCrush（零失败，论文称 "Crush-resistant"）。
- **关键 API 论断（对本项目至关重要）**：论文 §2 明确指出，应用可以**用自己的变量作为计数器和密钥**——"lows for machine-independent streams of random numbers... (streams are not associated with machine parameters)"。也就是说：**你可以把 `(实体ID, tick, 决策点ID)` 直接当成计数器，把世界种子当成密钥，随取随用，不需要为每个实体保存任何 RNG 状态。这正是 Q3 的答案的技术底座。**
- **性能数字见 §4 表。**
- **相关的另一路线：可分裂 PRNG（splittable）**。Claessen K. & Pałka M., "Splittable pseudorandom number generators using cryptographic hashing", Haskell Symposium 2013, pp. 47–58, DOI 10.1145/2503778.2503784；Steele G. L. Jr., Lea D. & Flood C. H., "Fast splittable pseudorandom number generators", OOPSLA 2014, pp. 453–472, DOI 10.1145/2660193.2660195（SplitMix）；Steele & Vigna, "LXM: better splittable pseudorandom number generators (and almost as fast)", *PACMPL* 5(OOPSLA), 2021, DOI 10.1145/3485525。可分裂 PRNG 提供 `split : G -> (G, G)`，天然匹配树形/递归的模拟结构。**取舍：counter-based 支持任意随机寻址（"给我第 3120 年、实体 #88121、决策点 harvest 的那个数"），splittable 只支持沿着分裂树走。本项目需要前者。**（此取舍为 D 级判断。）
- **PCG**：O'Neill M. E., "PCG: A Family of Simple Fast Space-Efficient Statistically Good Algorithms for Random Number Generation", Harvey Mudd College Technical Report **HMC-CS-2014-0905**, September 2014。官网说明它讨论了 "k-dimensional equidistribution and seekability (a.k.a. jump-ahead)"，并通过给 LCG 使用不同加性常数来提供多流。**注意：这是技术报告，未经同行评议**（证据等级 C）。

---

## 3. 可直接用于本项目的机制清单

以下每条给出：输入 → 输出、数学/算法草图、时间尺度、空间粒度、证据等级、为什么这样简化。

---

### M1. 三时钟时间模型

- **输入 → 输出**：任一断言 → 三元时间标签 `(world_valid_interval, sim_txn_point, [in_world_belief_intervals])`。
- **草图**：
  ```
  Fact      := (fact_id, subject, predicate, object,
                wvt_begin, wvt_end, wvt_begin_rule, wvt_end_rule,
                stt_tick, stt_phase, stt_seq,        -- 模拟器事务时间，全序
                schema_version)
  Belief    := (belief_id, holder_agent, claimed_fact_id | claimed_content,
                held_from_tick, held_until_tick,
                acquired_via_event_id, distortion_kind, confidence)
  ```
  `stt = (tick, phase, seq)` 的字典序必须是**全序且确定**，它同时充当事件日志的物理排序键与因果图的拓扑序保证。
  `wvt_*_rule` 借用 CHGIS 的做法（见 §6）：区分"精确""约估""数据下限（我们的记录到此为止，不代表它结束了）"。
- **时间尺度**：tick 级（stt）；模拟年/月级（wvt）；agent 生命周期级（belief）。
- **空间粒度**：与断言主体同粒度（个体 / 聚落 / 政体）。
- **证据等级**：**B**（双时态本身是 A 级成熟理论，SQL:2011 已标准化；但"第三层认知时间"是本项目的扩展，无直接文献先例）。
- **为什么这样简化**：不把 belief 做成第三个真正的时态维度（否则区间连接变成三维，查询代价爆炸），而是做成一层单向引用世界事实的独立图。世界事实图保持二维双时态，可以用成熟的区间索引。

---

### M2. 分层 counter-based 随机数寻址（Q3 的核心答案）

- **输入 → 输出**：`(世界主种子 W, 命名空间路径 path, tick t, 实体 id e, 决策点 slot s, 抽样序号 i)` → 一个可重现的随机比特串，**不依赖调用顺序**。
- **草图**：
  ```
  key     = Threefry_key(W, H64(namespace_path))      # 128-bit key，命名空间决定
  counter = (t, e, s, i)                               # 4×32 或 2×64 打包
  bits    = Philox4x32_10(counter, key)                # 或 Threefry4x64_20
  ```
  其中 `namespace_path` 是形如 `"climate/monsoon"`、`"agent/decision/warmake"`、`"disease/outbreak"` 的**语义路径**，`H64` 是固定的、与运行时无关的哈希（**不能用语言内置的 `hash()`**，见 §8）。
- **为什么这解决了"改一个事件不打乱其余一切"**：
  1. **无状态**。传统 PRNG 是一条链：第 $n$ 次调用的结果依赖前 $n-1$ 次调用了多少次。删掉洪水事件 ⇒ 少调用 3 次 ⇒ 此后**全世界所有随机数整体错位**。counter-based 下每个抽样点的随机数由其**坐标**唯一决定，与调用次数无关。
  2. **命名空间隔离**。给"气候"和"某人是否生病"分配不同的 key，则改动气候模块的抽样次数不影响疾病模块。
  3. **实体隔离**。counter 里含实体 id ⇒ 新增/删除一个实体不影响其他实体的抽样序列。
  4. **可随机寻址**。反事实分析时可以直接问"在事实世界里，第 3120 年实体 #88121 在 `harvest` 槽位上抽到的是什么"，无需重放。
- **反事实的最小干预协议**（结合 §2.7）：
  - **abduction**：对每个受影响的离散决策，用 Gumbel-max 后验（§2.7 §3.4 的精确法）从观测结果反推 Gumbel 噪声 $g$。对连续量，直接复用 counter 生成的同一均匀数。
  - **action**：只把目标事件的机制换掉（`do(flood_412 = absent)`），**counter 空间完全不变**。
  - **prediction**：重放。所有未被结构性改变的决策点会读到**完全相同的随机比特**；结果改变只可能来自输入分布 $p$ 的改变，而 Gumbel-max 保证了反事实稳定性（$p$ 没变 ⇒ 结果不变；$p$ 变了 ⇒ 只有相对似然上升的替代项才可能胜出）。
- **必须处理的边界情况**：如果反事实导致**实体 id 的分配序列改变**（洪水没发生 ⇒ 没死的人生了孩子 ⇒ 新实体），counter 空间就分岔了。对策：**实体 id 不用递增计数器，而用内容寻址**——`entity_id = H128(parent_ids, birth_tick, birth_slot_counter)`。这样"多出一个孩子"不会改变任何既有实体的 id。（此对策为 **D 级**：我未找到直接文献支持，是从内容寻址原理推出的工程设计。）
- **时间尺度**：每次抽样（sub-tick）。
- **空间粒度**：每实体、每决策点。
- **证据等级**：**A**（counter-based PRNG 的性质、流数、周期、统计质量均有 Salmon et al. 2011 的实测支撑；Gumbel-max 的反事实稳定性有 Oberst & Sontag 2019 的定理；CRN 的方法学地位有 Kleijnen 1988）。**但"用 (tick, entity, slot) 做 counter"这一具体寻址布局是本项目的设计，等级 B。**
- **归属**：`rules_math`。LLM 绝不参与随机数生成或消费顺序。

---

### M3. 因果事件图数据模型（Q2 的核心答案）

**设计原则：因果关系是数据，不是文字。任何一条因果边都必须由内核在写入时机械产生，且带上"这条边凭什么成立"的可复算凭据。**

- **节点类型**（借 PROV 三分但加限定）：
  ```
  Event     (= PROV Activity)   -- 在某个 (tick,phase,seq) 发生的原子变化
  StateFact (= PROV Entity)     -- 双时态断言，M1 的 Fact
  Actor     (= PROV Agent)      -- 个人 / 家族 / 组织 / 政体
  Mechanism                     -- 产生该事件的规则模块 + 版本 + 参数快照哈希
  RandomDraw                    -- (counter, key_ns, distribution_params_hash, outcome)
  ```
- **边类型**（每条边必须落在下面之一，禁止自由文本关系）：

  | 边 | 语义 | 谁写 | 凭据 |
  |---|---|---|---|
  | `consumed(Event, StateFact)` | 该事件读取了这个事实 | 内核自动（读屏障） | 读取时的 fact 版本 |
  | `produced(Event, StateFact)` | 该事件产生/终止了这个事实 | 内核自动（写屏障） | 新旧值 |
  | `enabled_by(Event, StateFact, margin)` | 若无此事实，该事件的触发条件不成立 | 机制显式声明 | `margin` = 条件富余量 |
  | `raised_hazard(StateFact, Event, Δlogit)` | 该事实把此事件的对数几率抬高了多少 | 机制显式声明 | 概率模型的项分解 |
  | `suppressed(StateFact, Event, Δlogit)` | 抑制项 | 同上 | 同上 |
  | `realized_by(Event, RandomDraw)` | 该事件的偶然实现来自这次抽样 | 内核自动 | counter 坐标 |
  | `intended_by(Event, Actor, plan_id)` | 该事件是某 agent 计划的执行 | agent 层 | plan 的 belief 依赖集 |
  | `mechanism_of(Event, Mechanism)` | | 内核自动 | 代码版本哈希 |
  | `succeeded(Event, Event)` | 直接后继（同一实体上） | 内核自动 | |

- **关键设计：`raised_hazard` 的 Δlogit 分解**。所有连续/概率型机制都写成**加性对数几率**形式：
  $$\mathrm{logit}\,P(\text{event}) = \beta_0 + \sum_{j} \beta_j \cdot f_j(\text{state})$$
  内核在计算时把每一项 $\beta_j f_j$ **连同它引用的 StateFact id** 一起落盘。于是"为什么这个国家灭亡"的**第一层答案是一次纯查表**：把 `collapse` 事件的所有 `raised_hazard` 入边按 $|\Delta\text{logit}|$ 排序，就得到了机械的、可复算的、不需要 LLM 的贡献排序。
  > 这一条是把 §2.2 的半环思想降级到工程可行的形式：不追求完整的 $\mathbb{N}[X]$ 多项式，只保留**加性分解 + 合取前提（`enabled_by`）**两种组合方式。这足以表达"多条独立充分路径"（多个高 Δlogit 项）与"必要合取条件"（`enabled_by` 集合）。
- **"为什么这个国家灭亡"的机械回答流程**：
  1. **L0 — 直接归因（$O(\deg)$）**：取 `collapse` 事件的入边，按 Δlogit 排序，输出 top-k 项及其 StateFact。
  2. **L1 — 结构性回溯（图遍历，有预算）**：对 top-k 中每个 StateFact，沿 `produced` 反向走到产生它的 Event，递归。用**边权 = 归一化 |Δlogit|** 做加权最短路 / 最大流，剪掉贡献低于阈值 $\varepsilon$ 的分支。产出一棵**因果树**，深度上限与宽度上限都是配置项。
  3. **L2 — 反事实验证（重放，昂贵）**：对因果树上的每个候选原因，用 M2 协议跑最小干预重放（$N$ 次以估计概率），得到 $P(\text{collapse} \mid do(\neg c))$。
  4. **L3 — 实际因果判定（HP，只在 L2 的小集合上跑）**：用 §2.6 的 AC1–AC3，在候选集合 $\le O(10)$ 上枚举见证划分 $(\vec Z, \vec W)$，处理过度决定；输出每个原因的 **degree of responsibility** $1/(1+k)$。
  5. **L4 — 叙事（唯一允许 LLM 介入的一层）**：LLM 只被允许把 L0–L3 的**已有结构**翻译成文字，禁止引入 L0–L3 中不存在的因果断言。校验方式：LLM 输出必须逐句引用 event_id / fact_id，任何未引用的因果主张被自动拒绝。
- **时间尺度**：写入是 tick 级；L0 查询是毫秒级；L2 是分钟到小时级（取决于重放深度）。
- **空间粒度**：事件级。
- **证据等级**：**B**。PROV 的节点/边分类是 A 级；`raised_hazard(Δlogit)` 的加性分解是标准统计建模做法但用作溯源边是本项目的设计；L3 用 HP + responsibility 有 A 级理论支撑但无模拟系统的大规模实证。
- **归属**：`rules_math`（L0–L3）；`llm_agent`（仅 L4，且受强约束）。

---

### M4. 分层事件日志 + 内容寻址快照森林（Q1 与 Q5 的答案）

#### 四层存储

| 层 | 内容 | 是否可丢 | 写入时机 | 目标格式 |
|---|---|---|---|---|
| **T0 · 种子层** | 世界主种子、代码版本哈希、机制参数集哈希、schema 版本、外部输入清单（含 LLM 应答表的根哈希） | **绝不可丢** | 世界创建 + 每次机制升级 | 几 KB 的清单文件 |
| **T1 · 规范事件日志** | 所有 Event 记录 + 因果边（M3） | 不可丢（可降级，见下） | 每 tick 追加 | 分段 append-only 列式文件（每段 = 若干模拟年） |
| **T2 · 锚点快照** | 完整世界状态，内容寻址分块 | 可重建（重放代价） | 固定间隔 + 重大事件后 | Merkle chunk 树 |
| **T3 · 派生投影** | 索引、聚合序列、图数据库、检索索引 | 完全可丢 | 惰性/后台 | 任意 |

**关键论断：T1 不需要记录随机数。** 因为 M2 让随机数成为坐标的纯函数。这消掉了传统 record-replay 里最大的一块日志。**T1 也不需要记录"状态变化"本身**——状态是事件的折叠。T1 只需要记录：事件类型 + 主体 + 参数 + 因果边 + 机制版本。

#### 事件降级（tiered retention）策略

借 Thanos 的三档思路（§2.10），但按**语义重要性**而非时间分辨率降级：

| 档 | 内容 | 保留策略 |
|---|---|---|
| **A 档（结构性）** | 政体建立/灭亡、制度变革、技术突破、宗教诞生、大规模迁徙、战争、饥荒、重要人物生死与任职 | **永久保留全部字段与全部因果边** |
| **B 档（个体性）** | 具名人物的日常决策、家族事件、聚落级经济事件 | 保留 N 年（滚动窗口，如 200 模拟年）内的全字段；之后**只保留事件头 + 指向 A 档的因果边**，丢弃细节参数 |
| **C 档（聚合性）** | 人口出生死亡、单笔贸易、单次收成 | 只在滚动窗口内保留个体记录；出窗后**聚合为时序统计量**，用 Gorilla 式 delta-of-delta + XOR 编码存储 |

**关键约束（Thanos 文档的教训）**：B 档降级的年龄门槛必须**短于** B 档的保留期，否则细节在被聚合之前就被删掉了。

**降级的可逆性**：C 档降级是有损的 ⇒ **超出窗口后就无法逐位重放那一段**。对策：**只要 T0 + T1 的 A/B 档头完整，就可以从最近的 T2 锚点重放重建 C 档**。因此 C 档不是"删除历史"，而是"删除缓存"。这一点必须在代码里以断言强制：**任何降级操作前，必须验证该区间已被至少一个 T2 锚点覆盖。**

#### 量级估算（**以下是我的算术，输入假设是 D 级；算术过程公开以便替换假设**）

设：
- 模拟跨度 $Y = 5000$ 模拟年；主循环 tick = 1 模拟月 ⇒ $T = 60{,}000$ ticks。
- 成熟期具名人物 $\sim 10^4$ 同时在世；聚落 $\sim 10^4$；政体 $\sim 10^2$；人口以队列/家户聚合表示 $\sim 10^5$–$10^6$ 单元。

**事件记录尺寸（列式 + 定长编码后的裸尺寸）**：
```
event_id (隐式，段内序号)          0 B
stt (tick delta + phase + seq)     ~2 B   (delta 编码)
event_type (字典编码)              ~1 B
subject_id                         ~5 B   (delta/字典)
mechanism_version                  ~1 B   (字典)
payload (2-6 个定点数值)           ~12 B
因果边 (平均 4 条 × (类型1B + 目标5B + Δlogit 2B))  ~32 B
------------------------------------------------
合计裸尺寸                          ~53 B/事件，取整 60 B
```

**三种事件率下的 T1 体积**（假设列式 + zstd 再压 3–8 倍，取保守的 4 倍）：

| 事件率（事件 / 模拟年） | 总事件数 | 裸尺寸 | 压缩后（÷4） | 判定 |
|---|---|---|---|---|
| $10^4$ | $5 \times 10^7$ | 3.0 GB | **0.75 GB** | 极宽裕 |
| $10^5$ | $5 \times 10^8$ | 30 GB | **7.5 GB** | 舒适 |
| $10^6$ | $5 \times 10^9$ | 300 GB | **75 GB** | 单机可行，需要分段与列裁剪 |
| $10^7$ | $5 \times 10^{10}$ | 3.0 TB | **750 GB** | 临界，L2 反事实重放将非常慢 |
| $10^8$ | $5 \times 10^{11}$ | 30 TB | **7.5 TB** | 不可行 |

> **设计规则（本简报最实用的一条）：把预算加在事件率上，而不是加在存储上。** 目标：**A+B 档规范事件率 $\le 10^6$ 事件/模拟年**（约 $10^5$ 事件/tick 的 1/12，即每 tick 约 $8 \times 10^4$ 个规范事件）。超出这个量的一切必须是 **C 档聚合** 或 **可由重放再生**，不能进 T1。

**T2 锚点快照体积**：设活跃实体 $10^6$，每实体状态平均 200 B ⇒ 单张全量快照 **200 MB**。
- 每 100 模拟年一张锚点 ⇒ 50 张 ⇒ 全量存储 10 GB。
- 用内容寻址分块 + 结构共享：若相邻两张快照间约 10%–30% 的块发生改变，增量存储约 **1–3 GB**（这个 10%–30% 是 D 级假设，必须实测）。
- 再加一个滚动窗口：最近 200 模拟年每 5 年一张细锚点（40 张增量）。

**总盘**：$T1 \approx 7.5\text{–}75$ GB + $T2 \approx 3\text{–}10$ GB + T3 索引（假设 T1 的 50%）$\approx 4\text{–}40$ GB ⇒ **量级 15 GB – 130 GB**。**结论：5000 年的完整可重放历史在单台机器的普通硬盘上是完全可行的，前提是事件率被约束在 $10^6$/模拟年以内。**

**重放代价**：从锚点恢复到任意时点，最坏需重放一个锚点间隔。100 模拟年 = 1200 ticks。若单 tick 纯规则计算耗时 $\tau$：
- $\tau = 10$ ms ⇒ 最坏 12 秒。
- $\tau = 100$ ms ⇒ 最坏 2 分钟。
- $\tau = 1$ s ⇒ 最坏 20 分钟 ⇒ 此时必须把锚点间隔缩到 20 年。

**⚠ 但如果 LLM 调用在重放路径上，上述全部作废**——见 M5。

- **证据等级**：存储机制本身 **A**（Gorilla、zstd、Thanos、内容寻址均有硬数字）；**上表的量级估算是 D 级**（事件率与实体数是我设定的假设，不是文献数据）。
- **归属**：`rules_math`。

---

### M5. LLM 输出作为"被记录的外生输入"（不是可重算的函数）

- **输入 → 输出**：`(prompt_canonical_form, model_id, request_params)` → 一条**不可变的应答记录**，内容寻址存储；重放时**永远从记录读，绝不重新调用**。
- **为什么必须这样**（这不是保守，是被文档确认的约束）：Anthropic 当前世代模型（Claude Fable 5/5.1、Opus 5/4.8/4.7、Sonnet 5）已**移除** `temperature` / `top_p` / `top_k` 参数——传入会返回 400 错误；也没有 `seed` 参数。也就是说，**在当前 API 上你连"把温度设成 0"这个传统的伪确定性手段都没有**。（来源：Claude API 参考文档，2026-06-24 缓存版；证据等级 **B**，厂商文档，非同行评议，且是厂商特定的、会变的。）
  除此之外，即使参数可控，模型权重的服务端更新、批处理形状导致的归约顺序差异等，都会破坏跨时间的位级一致性——这一条**我未取得可引用来源，属于 D 级判断**（见 §9）。
- **草图**：
  ```
  oracle_key   = H256(canonical_json(prompt_blocks, model_id, params, tool_defs))
  oracle_entry = (oracle_key, response_blocks, usage, wallclock, model_id, api_version)
  # 存在 T0 引用的、独立的 append-only "oracle 表"，其根哈希进 T0 清单
  ```
  调用点的规则：`ask_oracle(key)` → 若表中有 ⇒ 返回；若无且处于 **replay 模式** ⇒ **抛错并中止**（这是一个 bug，说明世界状态偏离了）；若无且处于 **live 模式** ⇒ 调用 API、写表、返回。
- **反事实时的三种策略（必须由实验设计者显式选择，不能有默认）**：
  1. **frozen**：所有 LLM 应答复用事实世界的记录。适用于"我只想看物理/经济链条的差异"。风险：agent 会在明显不同的世界里做出事实世界的决定，产生不连贯。
  2. **replay-until-divergence**：只要 prompt 的 canonical form 与事实世界逐字节相同就复用；一旦某个 agent 的输入上下文因反事实而改变，就重新调用。**这是默认推荐**——它自动实现了"最小干预"：没被反事实波及的 agent 完全不动。
  3. **fresh**：全部重新调用。只用于评估"叙事层的方差有多大"。
- **prompt canonical form 必须是确定的**：字典序键、固定浮点格式（见 M6）、不含墙钟时间、不含内存地址、不含集合的自然遍历顺序。
- **成本含义**：策略 2 下，一次反事实实验的 LLM 成本 $\approx$（被波及的 agent 数 × 被波及的 tick 数）而非全量。这就是"最小干预"在预算上的意义。
- **时间尺度**：每次 agent 决策。
- **空间粒度**：每 agent。
- **证据等级**：**B**（record-replay 中"外部输入必须记录回放"是 A 级原则，见 Chen et al. 2015；LLM 特定的不可重现性只有厂商文档级证据）。
- **归属**：`hybrid`（LLM 产生内容，规则系统决定内容是否被采纳、以及重放时如何取用）。

---

### M6. 确定性纪律清单（可作为 CI 检查项）

- **输入 → 输出**：源码 + 运行时配置 → "两次运行世界哈希相同"的可验证保证。
- **规则**：
  1. **禁止哈希序遍历**。所有对 `dict`/`set`/`map` 的遍历必须先排序或使用插入序容器。CI 层用 `PYTHONHASHSEED=random` 跑两遍并比对世界哈希（**故意**用随机哈希种子来抓这类 bug）。Go 侧同理（其 map 遍历顺序官方明确不保证）。
  2. **禁止裸浮点作为世界状态**。所有进入世界状态的量用**定点整数**（如以 $10^{-6}$ 为单位的 `i64`）或**有理数**。浮点只允许出现在**不回写世界状态**的中间计算里，且其结果必须在写回前量化到定点。理由：浮点加法不结合，跨编译器/跨 CPU/跨并行划分不一致（Goldberg 1991；Polhill et al. 2006）。
  3. **若无法完全避免浮点**：固定为 IEEE 754 binary64，禁用 FMA 收缩、禁用 `-ffast-math` 类重排、并行归约改用可重现求和算法（Demmel & Nguyen 2015）。
  4. **显式平局打破**。所有 `max` / `argmax` / 排序在键相等时必须回退到一个稳定的、与世界状态无关的 tiebreaker（推荐：实体的内容寻址 id 的字典序）。**这条源自 Edmonds & Hales 2003 的血泪教训。**
  5. **确定的调度顺序**。每 tick 内的 phase 顺序、每 phase 内的实体处理顺序必须由显式的确定性键给出（如 `(phase_id, entity_content_id)`），不能依赖容器的自然顺序，也不能依赖并行完成顺序。
  6. **世界哈希（canary）**。每 $K$ 个 tick 计算一次世界状态的 Merkle 根，写入 T1。重放时逐点比对，一旦不匹配立即定位到 $K$ 个 tick 的窗口内。$K$ 建议取 12（一模拟年）。
  7. **版本钉死**。T0 记录：代码 git 哈希、每个第三方库的精确版本、编译器/解释器版本、平台三元组。重放时若不匹配则**警告并要求显式确认**。
- **证据等级**：**A**（每一条都有直接文献或官方文档支撑）。
- **归属**：`rules_math`。

---

### M7. 写时复制分叉与结构共享

- **输入 → 输出**：`(world_id, fork_tick)` → 新的 `world_id'`，共享 `fork_tick` 之前的所有块。
- **草图**：世界状态组织为不可变的内容寻址块树（类似 HAMT / B-tree，节点按 `H256(children_hashes || payload)` 命名）。分叉 = 复制根哈希。写入 = path copying（Driscoll et al. 1986/1989 的完全持久化技术）：只重写从被改块到根的路径，深度 $d$ 的树每次写入产生 $O(d)$ 个新块。
- **事件日志侧**：T1 分段文件按 `(world_lineage_id, segment_id)` 命名；分叉世界的段文件从分叉点开始新建，之前的段**通过引用共享**（不复制）。世界谱系本身是一棵树，存为 `Lineage(world_id, parent_world_id, fork_stt, intervention_spec)`。
- **`intervention_spec` 必须是结构化的、可复算的**：`{target: event_id | mechanism_param, op: suppress | force | set, value: ...}`。**禁止用自由文本描述干预**——否则你三年后无法知道那次分叉到底改了什么。
- **时间尺度**：分叉是 $O(1)$；写入是 $O(\log n)$。
- **空间粒度**：块级（建议块 = 一个空间网格单元的全部实体，或一个政体的全部状态）。
- **证据等级**：**A**（Driscoll et al. 的持久化技术与 Merkle 内容寻址都是经典结果）。
- **归属**：`rules_math`。

---

### M8. 反事实实验协议（把 §2.6 与 §2.7 落成流程）

- **输入 → 输出**：`(base_world, intervention_spec, N, horizon)` → 一组反事实历史 + 一份差异报告。
- **草图**：
  ```
  1. 定位：把 intervention_spec 解析到具体的 (stt, event_id | mechanism_site)
  2. 分叉：M7，得到 world'
  3. abduction：对干预点下游 horizon 内所有离散决策，
     用 Gumbel-max 后验（Oberst & Sontag §3.4 精确法）恢复噪声 g；
     对连续抽样，M2 保证 counter 不变 ⇒ 噪声自动不变
  4. action：在 world' 中执行 do(...)；机制其余部分不变
  5. prediction：重放到 horizon
  6. 重复 N 次（只有 abduction 的后验采样是随机的；
     若使用精确后验且干预点唯一，N 可以小到 30–100）
  7. 报告：ΔP(target_event)、Δ 关键状态量的分布、
     首次分歧点（第一个世界哈希不同的 tick）
  ```
- **必须报告"首次分歧点"**：如果反事实历史在干预后第 3 个 tick 就与事实历史全面分歧，说明系统对该干预高度敏感（或者你的随机数隔离做漏了）。首次分歧点距离干预点越远，说明耦合设计越成功。**这应该成为一个持续监控的健康指标。**
- **N 的选择**：Kleijnen 1988 提醒，CRN 使得各处理之间的响应**相关**，标准的独立样本方差公式不适用；应使用配对差分（paired difference）统计，这本身也提高了检出小效应的功效。
- **证据等级**：**B**（三步法 A 级；Gumbel-max 后验 A 级；"首次分歧点"作为指标是本项目设计，D 级；N 的具体取值 D 级）。
- **归属**：`rules_math`（实验执行）；`hybrid`（LLM 侧按 M5 策略 2）。

---

### M9. 归因计算：三种互补方法，各有适用域

| 方法 | 回答的问题 | 代价 | 何时用 | 何时失效 |
|---|---|---|---|---|
| **Δlogit 直接分解**（M3 L0） | "在事件发生的那一刻，各因素各贡献了多少对数几率" | $O(\deg)$，近乎免费 | 默认、总是计算 | 只能看到**直接**输入；无法看到通过其他事件间接起作用的远因 |
| **HP 实际因果 + responsibility**（M3 L3） | "在这条具体历史里，谁是真正的原因？过度决定怎么办？" | 在 $\le 10$ 个候选上枚举见证划分 | 重大事件（A 档）的正式因果报告 | 候选集大时组合爆炸；HP 定义本身仍有争议 |
| **Shapley / 方差分解**（Sobol'、Saltelli；Ng et al. 2025） | "在**分布意义**上，各机制/参数对结果的平均贡献是多少" | $O(2^m)$ 精确，或 Monte Carlo 估计；需要大量重放 | 机制层面的模型诊断，不是单个历史事件的解释 | 它回答的是**总体**问题，不是"这一次为什么"；把它当成单事件解释是范畴错误（见 §8） |

**联合使用的正确姿势**：Δlogit 给排序 → HP 给"是不是真原因" → responsibility 给程度 → Shapley/Sobol' 只用于回答"这个模型里，气候机制整体上有多重要"这类元问题。

- **证据等级**：Sobol'/Saltelli/Morris **A**；HP/responsibility **A**（理论）/ **C**（在大型模拟上的实践，无实证）；Δlogit 分解 **B**。
- **归属**：`rules_math`。

---

### M10. 过度决定与抢占的显式处理

- **问题**：政体崩溃时，"财政破产"与"北境叛乱"可能各自都足以致命。朴素反事实对两者都得出"移除它结果不变 ⇒ 不是原因"。
- **算法**（HP AC2 的工程化）：
  ```
  candidates = top-k by |Δlogit|
  for each subset S ⊆ candidates, |S| ≤ 3:        # AC3 极小性 + 预算
      for each witness assignment W over candidates \ S:
          run counterfactual: do(S := ¬S) ∧ hold(W := actual_or_alternative)
          if target does not occur:  S 是实际原因（带见证 W）
  responsibility(c) = 1 / (1 + min |W| over witnesses that make c critical)
  ```
- **成本控制**：`|S| ≤ 3` 与 `k ≤ 10` 把枚举量压在 $\sum_{i\le3}\binom{10}{i} \times 2^{7} \approx 2.2 \times 10^4$ 次重放。若单次重放 horizon 短（只需跑到目标事件），是可承受的。若不可承受，退化为只查 $|S| = 1$ 与 $|S| = 2$。
- **必须输出的三种判定**：`sole_cause`（唯一充分且必要）、`overdetermined`（多条独立充分路径，各自 responsibility < 1）、`preempted`（某因素本会导致结果，但被另一因素抢先——通过时间序 + 见证划分识别）。**"抢占"这个标签对历史叙事极其重要**：它对应"这个王朝本来也会亡于财政，只是叛乱先到一步"。
- **证据等级**：**B**（HP 框架 A 级；此处的预算化枚举与三种判定标签是本项目设计）。
- **归属**：`rules_math`。

---

### M11. 世界内认知的独立溯源图（Q7）

- **输入 → 输出**：`(agent, tick)` → 该 agent 在该时刻可获得的命题集合 + 每个命题的来源链与失真历史。
- **草图**：
  ```
  Belief(belief_id, holder, claim, held_from, held_until,
         source: {witnessed(event_id) | told_by(belief_id, teller, channel)
                  | inferred(rule_id, [belief_id]) | fabricated(motive)},
         fidelity ∈ [0,1], mutation_kind)
  ```
  - `witnessed`：agent 在事件的信息半径内 ⇒ 直接引用世界事实 id。
  - `told_by`：形成传播链（PROV 的 `wasDerivedFrom` + `actedOnBehalfOf` 的类比）。每一跳可以施加失真算子。
  - `fabricated`：**必须记录动机**，且该 belief 不引用任何世界事实 id ⇒ 系统可以自动区分"官方史书里的这条记载有世界事实支撑吗"。
- **这直接给出纲领第 9 条要的东西**：查询"官修国史 vs 实际发生"= 对官方 belief 集合做 `claim` 与其 `source` 链的可达性检查，找出所有到不了任何世界事实 id 的断言。
- **世界内历史学家**（纲领的目标之一）成为一个自然的 agent 类型：他们只能在 Belief 图上做推理，看不到 Fact 图。
- **证据等级**：**B**（PROV 的委托/派生结构 A 级；三层时间中的认知层是本项目扩展）。
- **归属**：`hybrid`（图结构与传播规则由 rules 决定；具体的失真内容、叙事化、神话化由 LLM 生成，但必须挂在结构化的 `mutation_kind` 上）。

---

### M12. Schema 演化与事件升级（5000 年跑不完就改代码的必然问题）

- **来源**：Overeem et al. 2021 把 "event system evolution" 与 "rebuilding projections" 列为事件溯源系统的头两号实践难题。
- **必须实现的机制**（对应其五种战术）：
  1. **versioned events**：每条事件带 `schema_version`。
  2. **upcasting**：提供纯函数 `upcast_{v→v+1}(event) -> event`，链式组合。**重放时按需升级，日志本身不变。**
  3. **weak schema**：新增字段必须有默认值，删除字段只能标记为 deprecated 不能物理移除。
  4. **copy-and-transform**：只在重大版本跃迁时使用（生成新日志，保留旧日志与其锚点）。
  5. **禁止 in-place transformation**（原地改写历史日志）——它破坏 T0 的哈希链，等于销毁溯源。
- **机制版本也必须溯源**：M3 的 `Mechanism` 节点带代码哈希。**重放时若机制代码变了，重放结果就"合法地"不同**——这不是 bug，但必须被显式标注为一次新的世界谱系（`Lineage` 里记 `mechanism_upgrade` 而非 `counterfactual`）。**不能悄悄地用新代码重放旧世界然后声称那是同一段历史。**
- **证据等级**：**A**（Overeem et al. 2021 的实证）。
- **归属**：`rules_math`。

---

### M13. 图存储的现实取舍

- **不要一开始就上图数据库。** 因果图的边数量级 = 事件数 × 平均度 ≈ $5\times10^8 \times 4 = 2\times10^9$ 边（在 $10^5$ 事件/年的中档假设下）。这个规模对通用图数据库是不友好的（CamFlow 论文明说 "the size of the graph grows over time, and this makes query time grow proportionally"）。
- **推荐布局**：
  - 因果边**内联存储在事件记录里**（列式，边类型 + 目标 id + Δlogit 三列），因为 M3 的 L0 查询是"给定事件取入边"，这是**局部**访问。
  - 反向索引（"这个 StateFact 影响了哪些事件"）作为 T3 派生投影，只为 A 档事件建，可随时重建。
  - 只有 L1–L3 的分析阶段才把裁剪后的**子图**（$10^2$–$10^4$ 节点）载入内存图库跑算法。
- **证据等级**：**C**（有 CamFlow 的定性论断支撑"图会变大、查询会变慢"，但没有针对本项目规模的基准）。
- **归属**：`rules_math`。

---

### M14. 重放等价性测试套件

- 应当在 Phase 1 就建立，且是**唯一能在 Phase 0 之后持续保证纲领第 6 条不被侵蚀**的机制。
- 测试项：
  1. **位级重放**：同一 T0，跑两遍，逐 tick 世界哈希相同。
  2. **抗哈希序**：`PYTHONHASHSEED` 取两个不同值，世界哈希仍相同。
  3. **抗并行度**：单线程 vs $n$ 线程，世界哈希相同。
  4. **锚点一致**：从锚点 $A_k$ 重放到 $A_{k+1}$，得到的状态哈希 == $A_{k+1}$ 的记录哈希。
  5. **空干预不变性**（最重要的一条）：执行一次**语义为空**的反事实（如 `do(x := x_actual)`），要求得到与事实历史**逐位相同**的结果。若不同，说明随机流耦合有漏洞 —— 这是 M2 设计是否成功的唯一硬测试。
  6. **单点干预的分歧半径**：干预一个孤立的低影响事件，测量首次分歧点的距离与波及实体数。这两个数应当随时间**缓慢**增长；若立刻爆炸，说明命名空间隔离做漏了。
- **证据等级**：**B**（测试 1–4 是标准做法；测试 5–6 是本项目设计，D 级但极高价值）。

---

## 4. 硬数字与参数表

| 量 | 数值 | 单位 | 适用时空范围 | 不确定度 | 来源 |
|---|---|---|---|---|---|
| Gorilla 平均压缩后点尺寸 | **1.37** | 字节/点 | Facebook ODS 生产时序数据，2015 | 这是生产平均值，随数据形态变化 | Pelkonen et al., PVLDB 8(12), 2015 |
| Gorilla 压缩比（vs 16 B/点） | **12×**（整体存储足迹 10×） | — | 同上 | — | 同上 |
| Gorilla 中可压到 1 bit 的时间戳比例 | **~96%** | — | 440,000 个真实时间戳样本 | — | 同上，§4.1.1 |
| Gorilla delta-of-delta 分档 | 0 → 1 bit；$[-63,64]$ → 2+7；$[-255,256]$ → 3+9；$[-2047,2048]$ → 4+12；else → 4+32 | bit | — | — | 同上 |
| zstd 1.5.7 `-1` 压缩比 / 速度 | **2.896** / 510 / 1550 | ratio / MB·s⁻¹ 压 / MB·s⁻¹ 解 | Silesia 语料，i7-9700K @ 4.9GHz | 语料相关，结构化列式数据通常更好 | Zstandard 官方基准页 |
| zlib 1.3.1 `-1` | 2.743 / 105 / 390 | 同上 | 同上 | — | 同上 |
| lz4 1.10.0 | 2.101 / 675 / 3850 | 同上 | 同上 | — | 同上 |
| Philox4×32-7 GPU 吞吐 | **201.6** | GB/s | NVIDIA GTX580（1.54 GHz，512 CUDA cores） | 2011 硬件 | Salmon et al., SC'11, Table 2 |
| Philox4×32-10 CPU | 3.6 cpB / 3.4 GB/s | cycles·byte⁻¹ / GB·s⁻¹ | 3.07 GHz Xeon X5667 单核 | 同上 | 同上 |
| Threefry4×64-12 CPU | **1.1** cpB / 11.2 GB/s | 同上 | 同上 | 同上 | 同上 |
| Threefry / Philox 最小状态 | **0** | 字节 | — | — | 同上（表中 "Min. state" 列） |
| Mersenne Twister (`std::mt19937_64`) 状态 | 312×8 = **2496** | 字节 | — | — | 同上 |
| counter-based PRNG 并行流数 | **≥ 2⁶⁴** | 流 | 每个 key | — | 同上，摘要 |
| counter-based PRNG 周期 | **≥ 2¹²⁸** | — | 每流 | Philox 已测到 2²⁵⁶；SP 网络理论上支持到 2¹⁰²⁴ | 同上 |
| TestU01 通过情况 | SmallCrush + Crush + BigCrush **零失败** | — | ARS / Threefry / Philox 全族 | 论文称 "Crush-resistant" | 同上 |
| CamFlow 全系统溯源开销：内核解包 | **2%** | 相对执行时间 | Phoronix，Linux 4.9.5 | — | Pasquier et al., SoCC'17, Table 4 |
| CamFlow：内核编译 | 2% | 同上 | 同上 | — | 同上 |
| CamFlow：Postmark | **11%** | 同上 | 4kB–1MB 文件，10 子目录，1.5M 事务 | — | 同上 |
| CamFlow：Apache req/s 损失 | **12%**（8235 → 7269） | — | 同上 | — | 同上，Table 5 |
| CamFlow：redis LPOP 损失 | **22%**（1,442,627 → 1,120,935 ops/s） | — | 最大开销项 | — | 同上 |
| CamFlow：pybench | **<1%** | — | 纯计算负载 | — | 同上 |
| PROV-JSON 压缩后体积 | **8%** of 原 PROV-JSON 图 | — | CamFlow 溯源图 | 转述自其引用 [89]（Winnower, NDSS'18），未取原文验证 | 同上，§6.3 |
| CamFlow 选择性捕获的数据率削减 | **20%**（12.45 → 9.98 kB/iteration，`wget google.com` 负载） | — | — | 单一微负载 | 同上，§6.3 |
| CamFlow 节点/边类型数 | 24 节点类型 / **39** 边类型 | — | 该实现版本 | — | 同上 |
| Thanos 降采样触发年龄：raw → 5m | **40** | 小时 | — | — | Thanos Compactor 官方文档 |
| Thanos 降采样触发年龄：5m → 1h | **10** | 天 | — | — | 同上 |
| `PYTHONHASHSEED` 取值范围 | $[0,\ 4294967295]$；`0` 关闭随机化 | 整数 | CPython 3.x | — | Python 官方 `cmdline` 文档 |
| CHGIS V6 时间序列县级点记录数 | **10,522** | 条 | 中国，公元前 763 – 公元 1911 | 早于 1350 CE 的空间覆盖有缺口 | 本次直接解析 `v6_time_cnty_pts_utf_wgs84.dbf` |
| CHGIS 县级政区存续期中位数 / 均值 | **141** / 249.4 | 年 | 同上 | 含 1347 条以"数据下限"截断的右删失记录，故均值被低估 | 同上（我对 `END_YR − BEG_YR` 的统计） |
| CHGIS `BEG_CHG_TY` 分布 | 新建 4499 / 更名 2616 / 空 2395 / 迁移治所 552 / 治所迁移 348 / … | 条 | 同上 | **注意"迁移治所"与"治所迁移"是同义异写**，见 §8 | 同上 |
| CHGIS `END_CHG_TY` 分布 | 撤销 3053 / 更名 2626 / 空 2334 / **数据下限 1347** / 迁移治所 539 / 撤消 112 | 条 | 同上 | "撤销/撤消"同义异写 | 同上 |
| Seshat 时间分辨率 | **100** | 年（查询间隔） | 最远约 10,000 BP | — | Seshat 官方 Methods 页 |
| Seshat NGA 规模 | 约 **10,000** km²/个，30（后扩至 35）个 | — | 10 个世界区域 | — | 同上 |
| **本项目事件率预算（建议）** | **≤ 10⁶** | 规范事件 / 模拟年 | A+B 档 | **D 级：我的设计取值** | §3 M4 |
| **本项目 T1 体积估算** | 7.5–75 | GB | 5000 模拟年，事件率 10⁵–10⁶/年 | **D 级：基于 60 B/事件裸尺寸与 4× 压缩假设** | §3 M4 |
| **本项目 T2 单张全量快照** | ~200 | MB | 10⁶ 实体 × 200 B | **D 级** | §3 M4 |
| **本项目总盘估算** | 15–130 | GB | 全部四层 | **D 级** | §3 M4 |

---

## 5. 数据集与数据库

| 名称 | 内容 | 覆盖范围 | 访问方式 | URL | 许可 |
|---|---|---|---|---|---|
| **W3C PROV 系列规范** | PROV-DM / PROV-O / PROV-N / PROV-CONSTRAINTS / PROV-JSON | 溯源本体 | 网页 | https://www.w3.org/TR/prov-dm/ | W3C Document License |
| **CHGIS v6**（中国历史地理信息系统） | 历代政区点/面，含 `BEG_YR`/`END_YR`/`BEG_RULE`/`END_RULE`/`BEG_CHG_TY`/`END_CHG_TY` | 公元前 221 – 1911（1350 后空间覆盖较全） | Harvard Dataverse API / 网页；本次已实测下载 shapefile 并解析 DBF | https://dataverse.harvard.edu/dataverse/chgis | **注意矛盾**：Dataverse 上部分数据集元数据标 CC0 1.0；但 `CHGIS_V6_README.txt` 原文写 "free for academic research, no commercial use, resale, or redistribution permitted"。**使用前必须逐数据集确认。** |
| **CHGIS v6 时间序列县级点** | 10,522 条带存续区间的县级政区 | 前 763 – 1911 | `https://dataverse.harvard.edu/api/access/datafile/3048165`（本次验证可下载） | doi:10.7910/DVN/Q9VOF5 | 同上（该数据集 Dataverse 元数据标 CC0 1.0） |
| **CHGIS v6 时间序列府级面/点** | 府级政区多边形与点 | 1350–1911 覆盖较全 | 同上 | doi:10.7910/DVN/I0Q7SM（面）、doi:10.7910/DVN/WW1PD6（点） | Dataverse 元数据未标 license |
| **Japan Historical GIS** | 日本历史 GIS | — | Harvard Dataverse（CHGIS dataverse 下的子 dataverse，本次仅确认存在） | https://dataverse.harvard.edu/dataverse/chgis | 未验证 |
| **Seshat: Global History Databank** | 政体（polity）× NGA 的编码变量；含"推断存在/推断不存在"、专家分歧与不确定性的显式记录、每条数据附引用段落与编码者姓名+介入日期 | 全球，最远约 10,000 BP，100 年查询间隔 | 网页 / 数据发布 | http://seshatdatabank.info/ | 需逐数据集确认 |
| **CBDB（中国历代人物传记资料库）** | 人物、亲属、社会关系、任官、地址、入仕途径等 | 中古至清 | SQLite / Access / API | https://cbdb.hsites.harvard.edu/ （本次 **403，未能验证内容**） | **未验证** |
| **Random123 参考实现** | Philox / Threefry / ARS 的可移植 C 实现 | — | 源码下载 | https://www.thesalmons.org/john/random123/ | 未验证具体许可（论文称可下载） |
| **Silesia compression corpus** | zstd/lzbench 基准语料 | — | — | （由 zstd 基准页引用） | — |
| **TestU01** | PRNG 统计检验套件（SmallCrush / Crush / BigCrush） | — | — | （由 Salmon et al. 2011 引用为 [24]） | — |
| **XES（IEEE Std 1849）** | 可扩展事件流标准，过程挖掘领域的事件日志交换格式 | — | IEEE | DOI 10.1109/ieeestd.2016.7740858（2016）、10.1109/ieeestd.2023.10267858（2023 修订） | IEEE 标准，付费 |

> **本项目的取舍建议**：不采用 XES（面向业务流程，其 trace/case 概念与本项目不匹配），不采用 PROV-JSON 作为**存储**格式（太臃肿，见 §4），但**采用 PROV 的概念划分作为内部模型的命名与语义基础，并提供 PROV-O 导出**，以便未来把某段历史的因果图交给外部工具分析。

---

## 6. 中国与东亚特定证据

本领域是纯计算机科学/统计学领域，"中国特定证据"不体现为机制差异，而体现为**已有的中国历史数据基础设施如何建模时间与来源**——这些是本项目数据模型的现成参照物，而且是**经过几十年学术使用检验的**。

### 6.1 CHGIS 的时态模型：一个可直接抄的先例

本次直接下载并解析了 CHGIS V6 时间序列县级点数据（`v6_time_cnty_pts_utf_wgs84.dbf`，10,522 条记录）。其表结构：

```
NAME_PY, NAME_CH, NAME_FT      -- 拼音名、简体名、繁体名（三重命名）
X_COOR, Y_COOR                 -- 坐标
PRES_LOC                       -- 今地（"山西保德县城西侧"）
TYPE_PY, TYPE_CH, LEV_RANK     -- 政区类型（州/县）与层级
BEG_YR, BEG_RULE, BEG_CHG_TY   -- 起始年、起始规则码、起始变更类型
END_YR, END_RULE, END_CHG_TY   -- 终止年、终止规则码、终止变更类型
SYS_ID, NOTE_ID                -- 系统 id 与注记 id
GEO_SRC, COMPILER, GECOMPLR, CHECKER, ENT_DATE  -- 来源与编纂责任链
```

样例行：
```
保德州 | 州 | LEV_RANK 6 | BEG_YR 1376 (BEG_RULE 4, 更名) | END_YR 1911 (END_RULE 6, 数据下限)
保德县 | 县 | BEG_YR 1171 (更名前身) | END_YR 1256 (撤销)
```

**四条可以直接搬进本项目的设计**：

1. **实体不是"县"，而是"县的一个存续实例"**。同一个"保德县"在 1171–1256 与 1374–1376 是两条独立记录，各有自己的 `SYS_ID`。这正是 PROV 的 `specializationOf` / 双时态的 valid-time 版本化。**本项目的政体、聚落、组织都应该这样建模：身份的延续性是一个可查询的关系，而不是一个隐含假设。**

2. **区间的两端各带"为什么"**（`BEG_CHG_TY` / `END_CHG_TY`），且词表是有限的：新建、更名、迁移治所、撤销。**这就是 M3 中"因果边必须有类型"的历史学界先例。** 分布（本次统计）：起始 —— 新建 4499、更名 2616、迁移治所 552+348；终止 —— 撤销 3053、更名 2626、数据下限 1347、迁移治所 539+346。

3. **区分"结束了"与"我们的记录到此为止"**。1347 条记录的 `END_CHG_TY` 是 **"数据下限"**（即 CHGIS 的数据截止于 1911，不代表该政区在 1911 年被撤销）。**这是右删失（right censoring）的显式标记。** 本项目必须照做：`wvt_end_rule ∈ {precise, approximate, censored_by_record, censored_by_retention}`。尤其是 `censored_by_retention` —— 当 C 档事件被降级聚合后，任何依赖它的区间都必须被标记为"因保留策略而截断"，否则将来的查询会把"我们删了"误读成"它结束了"。

4. **责任链字段**（`GEO_SRC`、`COMPILER`、`GECOMPLR`、`CHECKER`、`ENT_DATE`）—— 每条记录记录谁编的、谁校的、来源是什么。这正是 PROV 的 `wasAttributedTo` / `wasAssociatedWith`。**本项目的对应物是 `Mechanism` 节点（哪个规则模块、哪个版本、哪次运行产生了这条断言）。**

**同时，CHGIS 也提供了极好的反面教材**（见 §8 反模式 3）：`BEG_CHG_TY` / `END_CHG_TY` 的词表**没有被强制**，导致同义异写并存：「迁移治所」552 条 vs「治所迁移」348 条；「撤销」3053 条 vs「撤消」112 条；「更名和治所迁移」51 条 vs「更名和迁移治所」48 条 vs「更名且治所迁移」3 条；另有 2334 条空值与个别 `？？`、`暂无`。此外 `END_YR` 的最大值为 **11911**（显然是 1911 的录入错误）。**一个跑 5000 年的模拟如果让事件类型成为自由字符串，几百年后的因果查询就废了。事件类型必须是封闭的枚举，由代码常量定义，且改动需要 schema 版本升级。**

### 6.2 Seshat 的不确定性建模

Seshat 官方 Methods 页面说明：变量取值可以是数值、区间、二值（缺失/存在/未知），也可以是**"推断存在（inferred present）"/"推断不存在（inferred absent）"**；并且"Disagreements in the literature or among Seshat experts, as well as uncertainty, are recorded as far as possible so that data analysis can take into account alternative interpretations"；每条数据附带解释编码理由的叙述段落与引用，且**专家与研究助理的姓名以及介入日期都链接到数据上**。

- **对本项目的直接借用**：M11 的 Belief 图应当支持同一命题上**并存的、互相矛盾的**世界内断言（不同史家、不同宗教的记载），并保留各自的来源链与置信度，而不是强行归并成一个"官方版本"。Seshat 证明了这在一个真实运行了十年的历史数据库里是可行的。
- **警示**：Seshat 的方法论受到过实质性的学界批评（例如 Naether F. 关于 Whitehouse et al. 2019 "Complex Societies Precede Moralizing Gods throughout World History" 的评论，*Journal of Cognitive Historiography*, DOI 10.1558/jch.39578）。**这提醒我们：即使数据结构是好的，编码判断仍然可能有系统性偏差。** 本项目的对应风险是：即使因果图结构是好的，机制里的 $\beta_j$ 仍然是我们选的。

### 6.3 时空基准的实务问题

CHGIS 同时提供 WGS84 与西安 80（Xian80）两套坐标，以及 GBK 与 UTF-8 两套编码。**这是"中国历史地理数据的两个长期实务陷阱"**：坐标基准不一致会让空间连接静默出错；GBK/UTF-8 混用会让人名地名在管线中变成乱码，而乱码的名字进了因果图就再也查不出来。本项目虽然是虚构世界，但如果将来要用真实中国地理作为校准/初始化输入（纲领第 8 条），这两个坑一定会遇到。**建议：内部一律 UTF-8 + 一个明确记录在 T0 里的投影/基准。**

### 6.4 CBDB（未验证）

CBDB（China Biographical Database，哈佛/北大/中研院合作）是中国历史人物的关系型数据库，其模型（人物 - 亲属 - 社会关系 - 任官 - 地址 - 著述）与本项目的 Actor 模型高度同构，且每条断言都有出处字段。**但本次抓取返回 403，我未能验证其规模、字段与许可，因此不在本简报中给出任何具体数字。** 已验证存在的相关同行评议文献：Li B., Yuan Y., Lu X. & Bol P., "Normalization of kinship relations to enrich family network analysis: case study on China biographical database", *Digital Scholarship in the Humanities*, 2024, DOI 10.1093/llc/fqad108（该文题目本身即说明 CBDB 的亲属关系需要规范化才能做网络分析——**又一条"词表不规范会毁掉图查询"的证据**）。

---

## 7. 学界争议与未解决问题

1. **离散随机系统的反事实根本不可识别**（最重要的争议）。Oberst & Sontag 2019 明确指出："Multiple SCMs can all entail the same interventional distribution, but a different set of counterfactual trajectories."（§3 前言）以及 "Since all choices for `ord` imply the same interventional distribution, there is no way to distinguish between these mechanisms with data."（§3.1）**含义：本项目的反事实结论永远依赖于一条不可用数据检验的建模假设——我们选了哪种采样机制。** Gumbel-max 只是一个"直觉上可接受"的选择（满足反事实稳定性），不是"正确"的选择。**这必须写进项目的方法论声明里，而不是藏起来。**

2. **HP 实际因果的定义至今没有定论**。Halpern & Pearl 2005 → Halpern 2016 修改版 → 学界继续提新定义（如 Zhu 2022）。**含义：任何自动化的"这是原因"判定都携带一个可争议的定义选择。** 建议：把定义版本作为查询参数，允许输出"在 HP-2005 下 A 是原因，在 HP-2016 下不是"这样的结果——这本身就是有价值的信息。

3. **溯源 ≠ 解释**。CaJaDE（Li, Lee, Miao, Glavic & Roy, PVLDB 2022, DOI 10.14778/3554821.3554852）的立论就是：单纯的 provenance（贡献输入元组）**不足以**解释查询结果的差异，需要用数据库中未被查询使用的其他表来"增广"溯源。**对本项目的含义：因果图给出的是"哪些事实参与了计算"，而人类想要的"为什么"往往需要引入图之外的对比语境（"和邻国比""和上个世纪比"）。** 这是 M3 的 L4 层（LLM 叙事）真正的价值所在，也是它最容易越界的地方。

4. **ABM 上做因果推断本身是否有意义**存在方法论争论。Manzo G.（ed.）, *Agent-based Models and Causal Inference*, Wiley, 2022（DOI 10.1002/9781119704492）整本书就是围绕这个争论组织的（含 "Agent-based Models and Causal Inference"、"Causal Inference in Experimental and Observational Methods"、"Method Diversity and Causal Inference" 等章）。**核心张力**：ABM 里的"因果"是模型内部的机械依赖，与流行病学/经济学意义上从数据中识别因果不是一回事。**本项目在这个争论中的位置是有利的**——我们不需要从数据中识别因果，我们拥有生成过程本身。但这也意味着**我们的因果结论只在模型内部有效，不能外推到真实历史**。纲领第 8 条（真实历史是校准集不是答案）与这一点完全一致，应当在文档中显式引用这个学界共识。

5. **全捕获 vs 选择性捕获的取舍无定论**。CamFlow 明说这是一个"completeness trade-off against performance, storage, and I/O bandwidth"，且"quantitatively measuring provenance completeness or expressivity are complex, ongoing topics of research"。**对本项目：没有理论能告诉你该记录哪些因果边。这必须靠"能否回答我们关心的查询"来经验性决定，且会随项目演进反复调整——所以 M12 的 schema 演化机制不是可选项。**

6. **递归查询的 why-provenance 复杂度**是 2024 年才被系统刻画的（Calautti et al. 的三篇）。模拟里的因果链本质上是递归的（A 导致 B 导致 C…）。**这意味着"完整的 how-provenance"在理论上就是昂贵的**，M3 的分层（L0 便宜 / L3 昂贵）不是偷懒，是必需。

7. **LLM 推理的可重现性**：厂商已移除采样参数（见 M5），也没有 `seed`。**我没有找到任何权威来源说明"同一请求在同一模型上是否返回同一输出"**。这是一个必须靠自己实测建立基线的开放问题（见 §9）。

8. **溯源图压缩的实际收益**在本项目形态下未知。文献中的 8%（Winnower）、LogGC、NodeMerge 都针对**系统审计日志**（大量重复的进程/文件访问模式），本项目的因果图重复模式完全不同。

---

## 8. 反模式：本领域常见的错误建模方式（我们必须避免的）

1. **记录状态而不记录转移**。存"第 3120 年人口是 120 万"，不存"这 3 万人是因为哪场瘟疫死的"。后果：任何"为什么"都无法回答，只能事后由 LLM 编造。**规则：世界状态是事件的折叠，事件是权威。**

2. **把因果写成自由文本**。让 LLM 在事件上写一段 `reason: "因为长期的财政压力和北方边患..."`。后果：不可查询、不可验证、不可反事实。**规则：因果必须是带类型的边 + 可复算的数值凭据（Δlogit）。文本只能作为边的渲染，不能作为边本身。**

3. **事件类型/关系类型用自由字符串**。CHGIS 的实证教训（§6.1）：「迁移治所」552 vs「治所迁移」348、「撤销」3053 vs「撤消」112。这是一个由专业历史地理学者维护了二十多年的数据库，**尚且**出现同义异写。一个跑 5000 年、由 LLM 参与生成内容的系统必然更糟。**规则：事件类型与边类型是代码里的封闭枚举，新增需要 schema 版本升级。**

4. **不区分"结束了"与"记录到此为止"**。CHGIS 有 1347 条「数据下限」记录明确标记了这一点。若本项目的 C 档降级删掉了细节而不标记，将来的因果分析会把"数据缺失"读成"事件未发生"。**规则：所有区间端点带 rule 码，删失必须显式。**

5. **单一全局 RNG 流**。最常见也最致命。后果：任何改动（多一次抽样、少一次抽样、改变模块执行顺序）都让此后全世界的随机数错位，反事实实验变成"重跑一遍完全不同的世界"，无法归因。**规则：M2 的坐标寻址。**

6. **用可变的东西做种子**。`seed = hash(entity) ^ current_population` 或 `seed = time.time()` 或 `seed = len(agents)`。后果：反事实改变了人口 ⇒ 所有种子变了 ⇒ 全盘错位。**规则：种子只能由 (世界主种子, 静态命名空间, tick, 内容寻址的实体 id, 静态槽位 id) 决定。**

7. **用逆变换采样（`if u < cumsum`）做离散决策**。后果：反事实结果暗中依赖于你枚举分支的顺序，且这个依赖不可检验（Oberst & Sontag 2019 §3.1 的反例）。**规则：用 Gumbel-max（或其他满足反事实稳定性的机制）。**

8. **遍历哈希容器**。Python 的 `str`/`bytes` 哈希默认加随机盐；Go 的 map 遍历顺序官方明确不保证。**规则：M6.1，且用随机哈希种子跑 CI 来主动抓这类 bug。**

9. **浮点进入世界状态**。加法不结合，跨平台/编译器/并行度不一致（Goldberg 1991；Polhill et al. 2006 是 ABM 领域的专门警告）。**规则：定点整数。**

10. **不显式打破平局**。Edmonds & Hales 2003 的核心发现：两个独立重实现与原模型的实质性差异，**根源就是锦标赛选择的平局打破规则**；而且修正后才发现该模型的真实机制与作者宣称的完全不同。**规则：所有 argmax/排序带确定性 tiebreaker，且 tiebreaker 是模型规格的一部分，要写进文档。**

11. **重放时重新调用 LLM**。后果：重放不再是重放。**规则：M5 的 oracle 表；重放模式下 oracle miss = 致命错误而非静默补调。**

12. **原地改写历史日志（in-place transformation）来"修 bug"**。Overeem et al. 2021 把它列为可选战术，但对本项目是禁区——它破坏 T0 的哈希链，等于销毁溯源。**规则：只允许 upcasting（读时升级）与 copy-and-transform（生成新谱系）。**

13. **只有快照没有事件日志，或只有事件日志没有快照**。前者无法回答"为什么"，后者让任意时点查询变成 O(全历史) 重放。**规则：两者都要，且快照是可丢弃的缓存。**

14. **一上来就把因果图塞进图数据库**。在 $10^9$ 边规模下查询会随图增长而线性变慢（CamFlow 的定性论断）。**规则：因果边内联在列式事件记录里；图库只用于分析阶段的裁剪子图。**

15. **把方差分解/Shapley 当成单个历史事件的解释**。Sobol' 指数回答的是"在参数分布上，这个因素平均贡献多少输出方差"，**不是**"这一次这个国家为什么亡"。把二者混淆是范畴错误。**规则：M9 的分工表。**

16. **认为"同种子 ⇒ 同结果"而不钉版本**。库版本、编译器、CPU 指令集、并行度都可能改变结果。**规则：T0 记录完整环境指纹，不匹配时警告。**

17. **把三种时间搅在一起**。模拟器 tick、世界内年月、agent 何时知道这件事——混用会导致"某个 agent 用了他当时不可能知道的信息"这类静默违反纲领第 4 条的 bug。**规则：M1 的三时钟，且类型系统上不可互相赋值。**

18. **溯源作为事后附加（bolt-on）**。所有成熟溯源系统（PROV、CamFlow、noWorkflow、ProvSQL）都是在**执行路径上**捕获的。事后从状态差分推因果注定丢信息。**规则：读写屏障在内核里，不是外挂。**

19. **让 LLM 决定客观结果**（纲领第 5 条）。在本领域的具体表现：让 LLM 判断"这场战争的胜负"或"这个原因是不是主要原因"。**规则：LLM 只在 M3 的 L4 层出现，且输出必须逐句引用已存在的 event_id / fact_id，未引用的因果主张自动拒绝。**

20. **降级/删除历史时不检查可重建性**。**规则：任何降级前必须断言"该区间被至少一个 T2 锚点覆盖 + T1 的 A/B 档头完整"。** 呼应 Thanos 文档的警告：保留期短于降采样年龄门槛会导致数据在被处理之前就消失。

---

## 9. 无来源判断（D 级，明确标记为 LLM 常识，不得当作历史规律）

以下全部是我为了让工程能落地而做的假设或设计，**没有文献来源**，必须在实测后替换：

1. **事件率预算 $10^6$ 规范事件/模拟年**、以及 $10^4$ 具名人物 / $10^4$ 聚落 / $10^6$ 活跃实体的规模假设。这些是我设的，不是从任何文献得来的。
2. **60 B/事件的裸尺寸**估算与其字段级分解。
3. **列式 + zstd 对本项目事件日志的压缩比取 4×**。zstd 官方的 2.896 是 Silesia 通用语料，结构化列式数据通常显著更好，但具体多好必须实测。
4. **相邻锚点间 10%–30% 的块发生改变**（决定 T2 增量体积）。
5. **锚点间隔 100 模拟年 / 滚动窗口 200 模拟年 / 细锚点 5 年**这一整套保留参数。
6. **单 tick 计算耗时 $\tau$ 的 10 ms / 100 ms / 1 s 三档**及由此推出的重放时间。
7. **`entity_id = H128(parent_ids, birth_tick, birth_slot_counter)`** 这一"内容寻址实体 id 以避免反事实导致 counter 空间分岔"的设计。原理上是对的（内容寻址的标准用法），但我没有找到在模拟系统中这样做的文献先例。
8. **counter 布局 `(tick, entity, slot, draw_index)` 的具体位宽分配**。
9. **M8 的 N = 30–100** 反事实重复次数。
10. **M10 的预算 `|S| ≤ 3`、`k ≤ 10`**。
11. **"首次分歧点距离"作为随机流耦合质量的健康指标**——这个指标我认为很有价值，但是我发明的，不是文献里的。
12. **A/B/C 三档事件分级的具体归类**（哪些事件算"结构性"）。
13. **counter-based 优于 splittable（因为需要随机寻址）** 这一取舍判断。两者都是成熟技术，选择理由是我的分析。
14. **"不直接采用 Datomic/XTDB/Kafka，而借用其模型"** 的判断。
15. **LLM 推理在参数之外还存在不可重现性**（批处理形状、服务端权重更新等）。我没有取得任何权威来源，只是把它当作保守假设。**必须实测：同一 prompt 连续调用 100 次，统计输出的字节级一致率。**
16. **Δlogit 加性分解足以表达本项目需要的因果组合结构**。这是我从溯源半环理论"降级"来的工程简化，我认为够用，但没有证明。
17. **三时钟（而非双时态）是正确的抽象层数**。第三层（认知时间）做成独立图而非真正的时态维度，是我的性能取舍。

---

## 10. 参考文献

### 10.1 本次检索中**已验证**的文献（元数据经 Crossref API 或原始规范/文档确认）

**溯源模型**
1. Moreau L. & Missier P. (eds.), *PROV-DM: The PROV Data Model*, W3C Recommendation, 2013-04-30. https://www.w3.org/TR/prov-dm/ — **本次抓取原文验证**（核心类型、关系、时间表示、Plan/Role/Collection/Bundle 均从规范原文读取）。 **[已核验]**（W3C Recommendation, 2013-04-30，编辑 Luc Moreau / Paolo Missier，抓取规范原文确认）
2. Moreau L., Clifford B., Freire J., Futrelle J., Gil Y., Groth P., et al., "The Open Provenance Model core specification (v1.1)", *Future Generation Computer Systems* 27(6):743–756, 2011. DOI 10.1016/j.future.2010.07.005
3. Buneman P., Khanna S. & Tan W.-C., "Why and Where: A Characterization of Data Provenance", *Database Theory — ICDT 2001*, LNCS, pp. 316–330. DOI 10.1007/3-540-44503-x_20 **[已核验]**（Crossref：Peter Buneman, Sanjeev Khanna, Wang-Chiew Tan，ICDT 2001, LNCS, pp. 316–330）
4. Green T. J., Karvounarakis G. & Tannen V., "Provenance semirings", *PODS '07*, pp. 31–40. DOI 10.1145/1265530.1265535 **[已核验]**（Crossref：Green / Karvounarakis / Tannen, PODS '07, pp. 31–40, 2007）
5. Cheney J., Chiticariu L. & Tan W.-C., "Provenance in Databases: Why, How, and Where", *Foundations and Trends in Databases*, pp. 379–474, 2009. DOI 10.1561/1900000006 **[已核验]**（Crossref：*FnTDB* 1(4):379–474, 2009）
6. Davidson S. B. & Freire J., "Provenance and scientific workflows: challenges and opportunities", *SIGMOD '08*, pp. 1345–1350. DOI 10.1145/1376616.1376772
7. Freire J., Koop D., Santos E. & Silva C. T., "Provenance for Computational Tasks: A Survey", *Computing in Science & Engineering* 10(3):11–21, 2008. DOI 10.1109/mcse.2008.79
8. Chapman A., Jagadish H. V. & Ramanan P., "Efficient provenance storage", *SIGMOD '08*, pp. 993–1006. DOI 10.1145/1376616.1376715
9. Murta L., Braganholo V., Chirigati F., Koop D. & Freire J., "noWorkflow: Capturing and Analyzing Provenance of Scripts", *IPAW 2015*, pp. 71–83. DOI 10.1007/978-3-319-16462-5_6
10. Senellart P., Jachiet L., Maniu S. & Ramusat Y., "ProvSQL: Provenance and Probability Management in PostgreSQL", *PVLDB* 11(12):2034–2037, 2018. DOI 10.14778/3229863.3236253
11. Pasquier T., Han X., Goldstein M., Moyer T., Eyers D., Seltzer M. & Bacon J., "Practical whole-system provenance capture", *SoCC '17*. DOI 10.1145/3127479.3129249 — **本次取得全文 PDF 并抽取 Tables 3–5 与 §6.3 的全部数字**。 **[已修正: Pasquier T. et al., "Practical whole-system provenance capture", *SoCC '17*, pp. 405–418. DOI 10.1145/3127479.3129249]**（作者、年份、会议均正确；Crossref 记录含页码 405–418，原引用缺页码）
12. Pasquier T., Han X., Moyer T., Bates A., Hermant O., Eyers D., Bacon J. & Seltzer M., "Runtime Analysis of Whole-System Provenance", *CCS '18*. DOI 10.1145/3243734.3243776
13. Hassan W. U., Lemay M., Aguse N., Bates A. & Moyer T., "Towards Scalable Cluster Auditing through Grammatical Inference over Provenance Graphs", *NDSS 2018*. DOI 10.14722/ndss.2018.23141 — **元数据已验证，全文未取得**（PDF 404）。
14. Lee K. H., Zhang X. & Xu D., "LogGC: garbage collecting audit log", *CCS '13*. DOI 10.1145/2508859.2516731 — 元数据已验证，全文未取得。
15. Tang Y., Li D., Li Z., Zhang M., Jee K. & Xiao X., "NodeMerge: Template Based Efficient Data Reduction For Big-Data Causality Analysis", *CCS '18*. DOI 10.1145/3243734.3243763 — 元数据已验证，全文未取得。
16. Li C., Lee J., Miao Z., Glavic B. & Roy S., "CaJaDE: Explaining Query Results by Augmenting Provenance with Context", *PVLDB* 15(12), 2022. DOI 10.14778/3554821.3554852 — 摘要已验证。
17. Calautti M., Livshits E., Pieris A. & Schneider M., "The Complexity of Why-Provenance for Datalog Queries", *PACMMOD* 2024. DOI 10.1145/3651146；同作者 "Below and Above Why-Provenance for Datalog Queries", DOI 10.1145/3695829；"Computing the Why-Provenance for Datalog Queries via SAT Solvers", *AAAI 2024*, DOI 10.1609/aaai.v38i9.28914 — 均为元数据验证。
18. Miao H. & Deshpande A., "Understanding Data Science Lifecycle Provenance via Graph Segmentation and Summarization", *ICDE 2019*. DOI 10.1109/icde.2019.00179

**溯源 × Agent-Based Simulation（本项目最贴近的先例）**
19. Pignotti E., Polhill G. & Edwards P., "PROV-O provenance traces from agent-based social simulation", *Joint EDBT/ICDT 2013 Workshops*, pp. 333–334. DOI 10.1145/2457317.2457377 **[已核验]**（Crossref：Pignotti / Polhill / Edwards, EDBT/ICDT 2013 Workshops, pp. 333–334）
20. Pignotti E., Polhill G. & Edwards P., "Using provenance to analyse agent-based simulations", *Joint EDBT/ICDT 2013 Workshops*. DOI 10.1145/2457317.2457371 — **元数据已验证，摘要为空，全文未取得**。 **[已修正: 页码为 pp. 319–322]**（作者、标题、会议、DOI 均正确；原引用未给页码/写作"同刊"）

**事件溯源 / 双时态**
21. Overeem M., Spoor M., Jansen S. & Brinkkemper S., "An empirical characterization of event sourced systems and their schema evolution — Lessons from industry", *Journal of Systems and Software* 178:110970, 2021 (CC BY 4.0). DOI 10.1016/j.jss.2021.110970；预印本 arXiv:2104.01146 — **摘要经 arXiv 页面验证**（25 位工程师 / 19 个实现；五大挑战与五种 schema 演化战术）。 **[已核验]**（Crossref：*JSS* 178:110970, 2021，四位作者与标题完全一致）
22. Snodgrass R. T. (ed.), *The TSQL2 Temporal Query Language*, Kluwer, 1995. DOI 10.1007/978-1-4615-2289-8
23. Kulkarni K. & Michels J.-E., "Temporal features in SQL:2011", *ACM SIGMOD Record* 41(3):34–43, 2012. DOI 10.1145/2380776.2380786
24. IEEE Std 1849, *IEEE Standard for eXtensible Event Stream (XES)*, 2016 (DOI 10.1109/ieeestd.2016.7740858) 与 2023 修订 (DOI 10.1109/ieeestd.2023.10267858)。
25. XTDB 官方文档，"What is XTDB"（valid time / system time、自动四时态列、更正与乱序到达）。https://docs.xtdb.com/intro/what-is-xtdb.html — **本次抓取验证**。
26. Datomic 官方文档，Transaction Processing（datom、`:db-before`/`:db-after`、as-of/since/history）。https://docs.datomic.com/transactions/transaction-processing.html — **本次抓取验证**（内容较概要，未能验证 excision 细节）。

**确定性与随机数**
27. Chen Y., Zhang S., Guo Q., Li L., Wu R. & Chen T., "Deterministic Replay: A Survey", *ACM Computing Surveys* 48(2):1–47, 2015. DOI 10.1145/2790077 — 元数据已验证，全文未取得。
28. Salmon J. K., Moraes M. A., Dror R. O. & Shaw D. E., "Parallel random numbers: as easy as 1, 2, 3", *SC '11*, pp. 1–12. DOI 10.1145/2063384.2063405 — **本次取得全文 PDF 并抽取 Table 2 全部性能数字、流数、周期与 Crush 结论**。 **[已核验]**（Crossref：SC '11, pp. 1–12, 2011，四位作者一致；Crossref 标题字段截作 "Parallel random numbers"）
29. Claessen K. & Pałka M. H., "Splittable pseudorandom number generators using cryptographic hashing", *Haskell Symposium 2013*, pp. 47–58. DOI 10.1145/2503778.2503784
30. Steele G. L. Jr., Lea D. & Flood C. H., "Fast splittable pseudorandom number generators", *OOPSLA 2014*, pp. 453–472. DOI 10.1145/2660193.2660195
31. Steele G. L. Jr. & Vigna S., "LXM: better splittable pseudorandom number generators (and almost as fast)", *PACMPL* 5(OOPSLA), 2021. DOI 10.1145/3485525
32. O'Neill M. E., "PCG: A Family of Simple Fast Space-Efficient Statistically Good Algorithms for Random Number Generation", Harvey Mudd College Tech Report HMC-CS-2014-0905, Sep 2014. https://www.pcg-random.org/paper.html — **本次抓取官网验证**（报告号、日期、多流与 jump-ahead 声明）。**注意：技术报告，未经同行评议。**
33. Goldberg D., "What every computer scientist should know about floating-point arithmetic", *ACM Computing Surveys* 23(1):5–48, 1991. DOI 10.1145/103162.103163
34. Polhill J. G., Izquierdo L. R. & Gotts N. M., "What every agent-based modeller should know about floating point arithmetic", *Environmental Modelling & Software* 21(3):283–309, 2006. DOI 10.1016/j.envsoft.2004.10.011 — 元数据已验证，全文未取得。
35. Demmel J. & Nguyen H. D., "Parallel Reproducible Summation", *IEEE Transactions on Computers* 64(7):2060–2070, 2015. DOI 10.1109/tc.2014.2345391；Ahrens W., Demmel J. & Nguyen H. D., "Algorithms for Efficient Reproducible Floating Point Summation", *ACM TOMS* 46(3), 2020. DOI 10.1145/3389360
36. Python 官方文档，`PYTHONHASHSEED`（Command line and environment）。https://docs.python.org/3/using/cmdline.html — **本次抓取验证**。
37. Go 官方博客，"Go maps in action"（map 遍历顺序不保证）。https://go.dev/blog/maps — **本次抓取验证**。

**因果推断**
38. Pearl J., *Causality: Models, Reasoning, and Inference*, 2nd ed., Cambridge University Press, 2009. DOI 10.1017/cbo9780511803161
39. Pearl J., "The seven tools of causal inference, with reflections on machine learning", *Communications of the ACM* 62(3):54–60, 2019. DOI 10.1145/3241036
40. Balke A. & Pearl J., "Counterfactual Probabilities: Computational Methods, Bounds and Applications", *UAI 1994*, pp. 46–54. DOI 10.1016/b978-1-55860-332-5.50011-0
41. Halpern J. Y. & Pearl J., "Causes and Explanations: A Structural-Model Approach. Part I: Causes", *BJPS* 56(4):843–887, 2005. DOI 10.1093/bjps/axi147；"Part II: Explanations", DOI 10.1093/bjps/axi148 **[已核验]**（Crossref：Part I *BJPS* 56(4):843–887；Part II *BJPS* 56(4):889–911，均 2005）
42. Halpern J. Y., *Actual Causality*, MIT Press, 2016/2017. DOI 10.7551/mitpress/9780262035026.001.0001 **[已核验]**（Crossref：MIT Press，记录出版日期 2017-05-18）
43. Chockler H. & Halpern J. Y., "Responsibility and Blame: A Structural-Model Approach", *JAIR* 22:93–115, 2004. DOI 10.1613/jair.1391 — **摘要已验证**（责任度定义与 11-0 / 6-5 选举例）。 **[已核验]**（Crossref：*JAIR* 22:93–115, 2004，作者 H. Chockler / J. Y. Halpern）
44. Eiter T. & Lukasiewicz T., "Complexity results for structure-based causality", *Artificial Intelligence* 142(1):53–89, 2002. DOI 10.1016/s0004-3702(02)00271-0 — **元数据已验证，摘要与具体复杂度类未能取得（多个来源 403/404）。本简报未引用任何具体复杂度类。** **[已核验]**（Crossref 元数据：*AIJ* 142(1):53–89, 2002；全文仍未取得，具体复杂度类不得引用）
45. Eiter T. & Lukasiewicz T., "Causes and explanations in the structural-model approach: Tractable cases", *AIJ* 170(6–7):542–580, 2006. DOI 10.1016/j.artint.2005.12.003 — 同上。 **[已核验]**（Crossref 元数据：*AIJ* 170(6–7):542–580, 2006；全文仍未取得）
46. Lewis D., "Causation", *The Journal of Philosophy* 70(17):556–567, 1973. DOI 10.2307/2025310
47. Imai K., Keele L. & Tingley D., "A general approach to causal mediation analysis", *Psychological Methods* 15(4):309–334, 2010. DOI 10.1037/a0020761
48. VanderWeele T. J., "Mediation Analysis: A Practitioner's Guide", *Annual Review of Public Health* 37:17–32, 2016. DOI 10.1146/annurev-publhealth-032315-021402
49. Imbens G. W. & Rubin D. B., *Causal Inference for Statistics, Social, and Biomedical Sciences*, Cambridge University Press, 2015. DOI 10.1017/cbo9781139025751
50. **Oberst M. & Sontag D., "Counterfactual Off-Policy Evaluation with Gumbel-Max Structural Causal Models", ICML 2019, PMLR 97:4881–4890.** — **本次取得全文 PDF 并抽取 §3.1 非可识别性反例、Definition 5（counterfactual stability）、Definition 6（Gumbel-Max trick）、Theorem 1、Theorem 2 与 §3.4 后验推断方法的原文表述。** http://proceedings.mlr.press/v97/oberst19a/ **[已修正: 正确链接为 https://proceedings.mlr.press/v97/oberst19a.html]**（标题、作者、PMLR 97:4881–4890、ICML 2019 全部核实无误；原文给的 `http://proceedings.mlr.press/v97/oberst19a/` 返回 404）

**模拟中的因果与敏感性分析**
51. **Herd B. C. & Miles S., "Detecting Causal Relationships in Simulation Models Using Intervention-based Counterfactual Analysis", *ACM TIST* 10(5):1–25, 2019. DOI 10.1145/3322123** — **摘要已验证**（干预式因果分析、虚假效应、对称/非对称过度决定、事件间细粒度因果）。**全文未取得。** **[已核验]**（Crossref：*ACM TIST* 10(5):1–25, 2019；全文仍未取得，方法细节不得引用）
52. Manzo G. (ed.), *Agent-based Models and Causal Inference*, Wiley, 2022. DOI 10.1002/9781119704492 — 元数据已验证（编者、出版社、日期）。
53. Sobol' I. M., "Global sensitivity indices for nonlinear mathematical models and their Monte Carlo estimates", *Mathematics and Computers in Simulation* 55(1–3):271–280, 2001. DOI 10.1016/s0378-4754(00)00270-6
54. Saltelli A., Annoni P., Azzini I., Campolongo F., Ratto M. & Tarantola S., "Variance based sensitivity analysis of model output. Design and estimator for the total sensitivity index", *Computer Physics Communications* 181(2):259–270, 2010. DOI 10.1016/j.cpc.2009.09.018
55. Morris M. D., "Factorial Sampling Plans for Preliminary Computational Experiments", *Technometrics* 33(2):161–174, 1991. DOI 10.1080/00401706.1991.10484804
56. Ligmann-Zielinska A., Kramer D. B., Spence Cheruvelil K. & Soranno P. A., "Using Uncertainty and Sensitivity Analyses in Socioecological Agent-Based Models to Improve Their Analytical Performance and Policy Relevance", *PLoS ONE* 9(10):e109779, 2014. DOI 10.1371/journal.pone.0109779
57. Ligmann-Zielinska A., "Spatially-explicit sensitivity analysis of an agent-based model of land use change", *IJGIS* 27(9):1764–1781, 2013. DOI 10.1080/13658816.2013.782613
58. Kleijnen J. P. C., "Analyzing Simulation Experiments with Common Random Numbers", *Management Science* 34(1):65–74, 1988. DOI 10.1287/mnsc.34.1.65 **[已核验]**（Crossref：*Management Science* 34(1):65–74, 1988）
59. Ng H., Lin Y., Lu X. & Liu Y., "Who's to Blame? Unraveling Causal Drivers in Supply Chain Simulations with a Shapley Value Based Attribution Mechanism", *Winter Simulation Conference 2025*. DOI 10.1109/wsc68292.2025.11338977 — 元数据已验证，全文未取得。
60. **Edmonds B. & Hales D., "Replication, Replication and Replication: Some Hard Lessons from Model Alignment", *JASSS* 6(4), 2003.** — **本次抓取全文验证**（两个独立重实现与原模型实质不同；根源为锦标赛选择的平局打破规则；修正后发现真实机制与作者宣称不同）。https://www.jasss.org/6/4/11.html **[已核验]**（抓取 JASSS 全文确认：标题、两位作者、6(4), 2003；平局打破/"selected bias" 论断与原文一致）
61. Grimm V., Berger U., DeAngelis D. L., Polhill J. G., Giske J. & Railsback S. F., "The ODD protocol: A review and first update", *Ecological Modelling* 221(23):2760–2768, 2010. DOI 10.1016/j.ecolmodel.2010.08.019；Grimm V. et al., 2020 更新版, DOI 10.1016/j.ecolmodel.2020.109105

**存储、持久化、压缩**
62. Driscoll J. R., Sarnak N., Sleator D. D. & Tarjan R. E., "Making data structures persistent", *STOC '86*, pp. 109–121 (DOI 10.1145/12130.12142)；期刊版 *JCSS* 38(1):86–124, 1989 (DOI 10.1016/0022-0000(89)90034-2) **[已核验]**（Crossref：STOC '86 pp. 109–121 与 *JCSS* 38(1):86–124, 1989，两版四位作者一致）
63. Driscoll J. R., Sleator D. D. & Tarjan R. E., "Fully persistent lists with catenation", *JACM* 41(5):943–959, 1994. DOI 10.1145/185675.185791
64. Merkle R. C., "A Digital Signature Based on a Conventional Encryption Function", *CRYPTO '87*, LNCS, pp. 369–378. DOI 10.1007/3-540-48184-2_32
65. O'Neil P., Cheng E., Gawlick D. & O'Neil E., "The log-structured merge-tree (LSM-tree)", *Acta Informatica* 33:351–385, 1996. DOI 10.1007/s002360050048
66. **Pelkonen T., Franklin S., Teller J., Cavallaro P., Huang Q., Meza J. & Veeraraghavan K., "Gorilla: A Fast, Scalable, In-Memory Time Series Database", *PVLDB* 8(12):1816–1827, 2015. DOI 10.14778/2824032.2824078** — **本次取得全文 PDF 并抽取 1.37 B/点、12×、96% 单 bit 时间戳、delta-of-delta 分档编码的全部细节**。 **[已核验]**（Crossref：*PVLDB* 8(12):1816–1827, 2015，七位作者一致）
67. Zstandard 官方基准页（Silesia 语料，i7-9700K，lzbench + GCC 14.2）。https://facebook.github.io/zstd/ — **本次抓取验证**。
68. Thanos Compactor 官方文档（raw / 5m / 1h 三档降采样，40h 与 10d 门槛，保留期约束）。https://thanos.io/tip/components/compact.md/ — **本次抓取验证**。
69. Alvaro P., Rosen J. & Hellerstein J. M., "Lineage-driven Fault Injection", *SIGMOD '15*. DOI 10.1145/2723372.2723711 — 元数据已验证。（相关：用溯源反向驱动"哪些故障组合会破坏结果"，与本项目的反事实实验设计同构。）
70. Alvaro P., Marczak W. R., Conway N., Hellerstein J. M., Maier D. & Sears R., "Dedalus: Datalog in Time and Space", *Datalog Reloaded*, 2011. DOI 10.1007/978-3-642-24206-9_16

**中国与东亚数据基础设施**
71. **CHGIS Version 6**, Fairbank Center for Chinese Studies (Harvard) & Center for Historical Geographical Studies (Fudan), 2016. Editor: Lex Berman. Harvard Dataverse。**本次直接下载 `v6_time_cnty_pts_utf_wgs84.zip`（doi:10.7910/DVN/Q9VOF5，数据文件 id 3048165）并解析 DBF 表头与全部 10,522 条记录**；同时下载 `CHGIS_V6_README.txt`（数据文件 id 3048161）验证许可条款。相关时间序列数据集：doi:10.7910/DVN/I0Q7SM（府级面）、doi:10.7910/DVN/WW1PD6（府级点）。
72. Seshat: Global History Databank — Methods 页面。http://seshatdatabank.info/methods/ — **本次抓取验证**（polity/NGA 编码单元、inferred present/absent、分歧与不确定性记录、逐条引用与编码者署名、100 年间隔）。
73. François P., Manning J. G., Whitehouse H., Brennan R., Currie T., Feeney K. et al., "A Macroscope for Global History: Seshat Global History Databank, a methodological overview", *Digital Humanities Quarterly* 10(4), 2016. DOI 10.63744/e3j3d5qsvq99 — 元数据已验证。
74. Turchin P., "Seshat: Global History Databank Publishes First Set of Historical Data", *Cliodynamics* 8(1), 2017. DOI 10.21237/c7clio8135421 — 元数据已验证。
75. Naether F., "Some Remarks on Whitehouse et al. (2019), 'Complex Societies Precede Moralizing Gods throughout World History'", *Journal of Cognitive Historiography*, 2022. DOI 10.1558/jch.39578 — 元数据已验证（作为 Seshat 方法论受到实质批评的证据）。
76. Li B., Yuan Y., Lu X. & Bol P., "Normalization of kinship relations to enrich family network analysis: case study on China biographical database", *Digital Scholarship in the Humanities*, 2024. DOI 10.1093/llc/fqad108 — 元数据已验证。
77. Berman M. L., Åhlfeldt J. & Wick M., "Historical Gazetteer System Integration", in *Placing Names*. DOI 10.2307/j.ctt2005zq7.13 — 元数据已验证。
78. Grossner K., Janowicz K. & Keßler C., "Place, Period, and Setting for Linked Data Gazetteers", in *Placing Names*. DOI 10.2307/j.ctt2005zq7.11 — 元数据已验证。
79. Southall H., "Rebuilding the Great Britain Historical GIS, Part 2: A Geo-Spatial Ontology of Administrative Units", *Historical Methods* 45(3), 2012. DOI 10.1080/01615440.2012.664101 — 元数据已验证。（**非中国，但它是"行政区随时间变化"的本体设计的另一个成熟先例，值得与 CHGIS 对读。**）
80. Stapel R., "Conflating Historical Population Statistics Using a Historical GIS with a Flexible Semantic Model for Premodern Administrative Units", *ACM SIGSPATIAL Workshop*, 2023. DOI 10.1145/3615887.3627756 — 元数据已验证。

**厂商 / 工具文档**
81. Claude API 参考（本地 `claude-api` skill 捆绑文档，缓存日期 2026-06-24）：当前世代模型（Claude Fable 5/5.1、Opus 5/4.8/4.7、Sonnet 5）**已移除 `temperature` / `top_p` / `top_k`，传入返回 400**；文档中未提供 `seed` 参数。**证据等级 B（厂商文档，非同行评议，且会随版本变化）。**

### 10.2 本次**未能验证**的条目（不得据此下结论）

- Eiter & Lukasiewicz 2002/2006 的**具体复杂度类**（全文 403/404）。
- Herd & Miles 2019 的**方法细节、算法与实验规模**（全文 403/500）。
- Winnower / LogGC / NodeMerge 的**具体缩减倍数**（仅有 CamFlow 转述的 "8%"）。
- Polhill, Izquierdo & Gotts 2006 的**具体实验数字**。
- Chen et al. 2015 *Deterministic Replay* 综述的**具体开销数据**。
- rr（O'Callahan et al., USENIX ATC 2017）的**记录开销数字**（USENIX 403）。
- IPFS（Benet 2014）的**书目细节**（arXiv 连接重置）。
- Bagwell, "Ideal Hash Trees"（EPFL 技术报告）的**书目细节**（Crossref 无收录，EPFL 405）。
- SHAP（Lundberg & Lee, NeurIPS 2017）的**书目细节**（Crossref/S2 均未返回）。
- Kafka 原始论文（Kreps, Narkhede & Rao, NetDB 2011）的**书目细节**（非 Crossref 收录）。
- CBDB 的**规模、字段与许可**（403）。
- Datomic 的 **excision** 语义细节。

---

## 附：检索覆盖说明

- **WebSearch 在本次会话开始前配额即已耗尽（200/200）**，因此本简报的全部检索通过 WebFetch 与 `curl` 直接命中权威端点完成：Crossref REST API（`api.crossref.org`，约 60 次书目核验查询）、W3C 规范原文、PMLR / VLDB / 作者主页的开放获取 PDF（本地用 pypdf 抽取全文）、Harvard Dataverse REST API 与数据文件直下、Python/Go/Thanos/zstd/XTDB/Datomic 官方文档、JASSS 全文。
- **检索不足之处**：(1) 无法用搜索引擎做发散式发现，因此可能遗漏了标题不含我预设关键词的相关工作，尤其是"模拟系统专用的溯源/反事实基础设施"这一交叉领域的近两年成果；(2) arXiv API 与 Semantic Scholar API 在本沙箱中均不可达（连接被拒/空响应），因此预印本覆盖薄弱；(3) DBLP 被 Anubis 反爬拦截。
- **付费墙拦住的**：ScienceDirect（Eiter & Lukasiewicz、Polhill et al.、Overeem et al. 正文）、ACM DL（Herd & Miles、Chen et al. 综述、Pignotti et al.）、USENIX（rr）、IEEE Xplore（XES 标准）。上述条目均只使用了经 Crossref 验证的书目元数据与（若可得）摘要，未据其正文下任何结论。
- **本次做了原始数据核验的**：CHGIS V6 时间序列县级点 shapefile（下载 → 解压 → 手写 DBF 解析器读表头与全部 10,522 行 → 统计变更类型分布、年份范围、存续期分位数）。§4 与 §6.1 中所有 CHGIS 数字均来自这次直接解析，不是转述。
