# LLM Agent 社会模拟的现状、成本与失败模式

- **slug**: `llm-agent-social-simulation`
- **一句话范围**: 梳理 2022–2026 年用 LLM 驱动 agent 做社会/文明模拟的既有系统、已被实证记录的失败模式、可复现性与成本约束，并据此给出 civilization-sim 中"规则与 AI 分离"原则的工程依据、职责边界清单、调用预算方案与重放方案。
- **写作日期**: 2026-09-10
- **检索方式**: 本次通过 WebFetch 直接访问 arXiv 摘要页 / alphaxiv / GitHub README / Cambridge Core 逐条核验（WebSearch 配额在本会话开始前已被耗尽，检索策略因此改为"直接命中已知标识符 + 逐条核验"，覆盖不足之处见第 11 节）。
- **修订**: 2026-09-10 第二轮独立核验（同样在 WebSearch 配额耗尽的条件下，改用 arXiv 全文检索 UI、arXiv HTML 版、GitHub Contents API、GitHub raw 源码、Cambridge Core、Europe PMC、PMLR、ACL Anthology、platform.claude.com 官方文档）。第二轮新增的条目一律标 **〔R2〕**；与第一轮记录**冲突**的数字一律双列并标 **⚠冲突待核**，不做静默覆盖。

---

## 1. 本简报要回答的问题

MANDATE 第 5 条写的是"规则与 AI 分离：AI 可以负责人物和组织的判断、计划、解释、文化创造等难以公式化的部分，但 AI 不能直接决定客观结果"。这条原则在项目里目前是一条**信念**。本简报的任务是把它变成一条**有实证依据的工程约束**，具体要回答：

1. 已经有人用 LLM 做过多大规模、多长时间跨度的社会/文明模拟？他们做成了什么，没做成什么，代码和结果能不能复现？
2. LLM 作为"人的替身"（silicon sample / homo silicus）在社会科学里被检验过，检验结果是什么？失败模式的**方向性**是什么（是随机噪声，还是系统性偏移）？
3. 这些失败模式如果直接搬进一个要跑数千年的文明模拟，会以什么形式表现出来？（这是 MANDATE 第 9 条"防止模型为了戏剧性制造事件"的直接对应物。）
4. **允许 LLM 做什么、禁止 LLM 做什么**，理由必须落在具体失败模式上，而不是"感觉不安全"。
5. 数千年模拟的 LLM 调用预算能不能压到可承受？在完全不调用 LLM 的情况下世界能不能继续跑？
6. 如何让 LLM 的输出**可重放**，以满足 MANDATE 第 6 条（记录随机种子、可重放、可做反事实实验）。

本简报**不**回答：具体 prompt 怎么写、用哪家模型更"聪明"、agent 记忆库的向量检索实现细节。那些属于 Phase 1。

---

## 2. 已有成熟模型与理论

### 2.1 Generative Agents / Smallville（Park et al. 2023）

- **核心机制**：`memory stream`（自然语言事件流，带 recency / importance / relevance 三项加权检索）→ `reflection`（周期性把低层观察合成为高层判断，写回记忆流）→ `planning`（自顶向下的日程分解，再递归细化到分钟级动作）。三者共同构成"believability"。
- **形式化程度**：半形式化。检索打分函数（三项加权和）是公式化的，但 importance 分值本身由 LLM 打分；plan 与 reflection 完全是自由文本。没有任何客观世界状态由公式决定——沙盒是 The Sims 式的物件状态机，agent 的动作通过自然语言→沙盒动作的映射落地。
- **状态变量**：每 agent 一条 append-only 的自然语言 memory stream；一棵 plan tree；一份 relationship 摘要。世界侧是物件树（object tree）与其状态字符串。
- **参数**：25 个 agent，2 个模拟日（Smallville）。ablation 证明 observation / planning / reflection 各自都显著贡献可信度。
- **适用范围**：小规模、短时长、社交/日常行为层面的可信性。**不适用**于经济、战争、制度演化等需要客观量化结果的层面——因为它根本没有客观量化层。
- **已知局限（作者自述）**：记忆检索偶尔失败（agent 取不到相关记忆）；agent 会给回答添加"看似合理但虚构"的细节（完整幻觉少见但润色常见）；指令微调导致 agent **过度合作**（即使与自身既定利益冲突也答应请求）与**说话过度正式**；随记忆流增长会做出次优的地点选择、误解未显式编码的物理/社会规范。
- **成本**：官方 repo README 明确写"Running these simulations, at least as of early 2023, could be somewhat costly, especially when there are many agents in the environment"，并警告触发小时级 rate limit 会导致模拟中断需重启。论文与 README 均**未给出**具体美元/token 数字。
- **重放**：repo 提供 `replay` 与 `demo` 端点，但那是**世界状态轨迹的回放**（读取已保存的 storage），不是 LLM 调用的重放；README 自述 replay "primarily intended for debugging purposes"，且回放里所有角色 sprite 长得一样。
- **出处**：arXiv 2304.03442（v1 2023-04-07, v2 2023-08-06）；代码 github.com/joonspk-research/generative_agents。

> **对本项目的直接教训**：Smallville 的"涌现"（情人节派对邀请两天内自发扩散）发生在**没有客观资源约束**的世界里。它证明的是"LLM 能生成连贯的社会互动叙事"，不是"LLM 能生成因果可追溯的社会结构变迁"。把它当作文明模拟内核的模板会直接违反 MANDATE 第 2 条。

- **〔R2〕实现常数（读的是仓库源码，不是论文正文，因此这些是"被实际跑过的值"）**：
  - `reverie/backend_server/persona/cognitive_modules/retrieve.py`：
    - `recency_vals = [persona.scratch.recency_decay ** i for i in range(1, len(nodes)+1)]` —— 注意衰减的指数是**记忆在排序表中的序号 i**，不是物理时间差。这是一个重要的实现细节：Smallville 的"recency"其实是**排名衰减**而非**时间衰减**。
    - `gw = [0.5, 3, 2]`，总分 `master = recency_w*recency*0.5 + relevance_w*relevance*3 + importance_w*importance*2`。即在其默认配置下 **relevance 的权重是 recency 的 6 倍、importance 的 1.5 倍**。
    - `def new_retrieve(persona, focal_points, n_count=30)` —— 每个焦点默认取回 30 条记忆。
  - `.../bootstrap_memory/scratch.json`（`base_the_ville_isabella_maria_klaus` 中 Isabella Rodriguez）：`recency_w=1, relevance_w=1, importance_w=1, recency_decay=0.995, importance_trigger_max=150, importance_trigger_curr=150, vision_r=8, att_bandwidth=8, retention=8, daily_reflection_time=180, daily_reflection_size=5, overlap_reflect_th=4, kw_strg_event_reflect_th=10, kw_strg_thought_reflect_th=9, concept_forget=100`。
  - **对本项目的直接可用性**：`vision_r=8 / att_bandwidth=8 / retention=8` 这三个数是**信息边界的实现原语**（视野半径、每步最多感知的事件数、重复事件抑制窗口），比论文里"agent 只能看到附近发生的事"这句话可操作得多。`importance_trigger_max=150` 则是"反思按**累积重要性预算**触发、而不是按固定周期触发"的现成参数形式——这正是我们需要的：一个平静的世纪不该产生和一个战乱世纪一样多的反思。
  - **不可照搬的部分**：排名衰减（0.995^i）在数千年尺度上会退化成"几乎只看 relevance"，因为 i 会变成十万量级，`0.995^100000 ≈ 0` 对所有旧记忆都一样。我们必须换成**物理时间衰减 + 分层记忆**（见 M5/M10）。

### 2.2 Interview-grounded individual agents（Park et al. 2024/2025）

- **核心机制**：对 1,052 名美国参与者做 2 小时半结构化访谈，把访谈全文作为 agent 的人格基底，再让 agent 回答 GSS、Big Five、经济博弈与若干社会心理学实验。
- **量化结果**（以参与者自身两周后 test-retest 一致性为分母的归一化准确率）：访谈基底 83%、问卷基底 82%、二者合并 86%、纯人口统计基线 74%。作者结论是"一旦模型在某个领域观察到足够证据，来自更多数据的预测收益开始趋于渐近"。同时报告相对纯人口统计基线**缩小了**跨种族/跨意识形态的准确率差距。
- **注意**：该 arXiv 条目当前标题已改为 *"LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals"*（原题为 *Generative Agent Simulations of 1,000 People*）。引用时须注明版本，否则会出现"文献不存在"的检索失败。
- **适用范围**：**有真人访谈数据可锚定**的个体级预测。本项目里没有任何真人可访谈——我们的角色是虚构的。这条路径对我们**不可直接迁移**，但它给出一个重要的量化上界参照：即使有 2 小时深访做锚，一致性也只有真人自身重测一致性的 86%；14% 的残差是不可约的 LLM 表征噪声。
- **出处**：arXiv 2411.10109（2024-11-15 提交）。

### 2.3 Concordia（Google DeepMind）

- **核心机制**：**Game Master (GM)** 架构。实体（agent）用自然语言描述**意图动作**，GM 把意图翻译成实际结果——README 原文："Entities describe their intended actions in natural language, and the GM translates these into appropriate outcomes e.g. checking physical plausibility in simulated worlds"；论文摘要进一步说明 GM 可以"检查物理合理性"或"对数字服务发起 API 调用"。agent 行为由一个 component 系统产生，该系统调解两个基本操作：**LLM 调用**与**联想记忆检索**。
- **形式化程度**：架构形式化（component / GM 分层是明确的），裁决逻辑本身可以是规则也可以是 LLM——框架不强制。
- **对本项目的价值**：**这是"LLM 只做提案、规则做裁决"这一原则在工业级框架里的既有实践**，而且出自 DeepMind、Apache-2.0 许可、代码公开。civilization-sim 的世界内核在架构上应当被理解为一个"纯规则实现的 Game Master"，而 LLM agent 只被允许产出 intent。
- **已知局限**：Concordia 的默认 GM 本身大量使用 LLM 做裁决，因此**不能照抄默认实现**——照抄等于把裁决权交回 LLM。我们要保留的是它的**接口切分**，不是它的裁决实现。
- **出处**：arXiv 2312.03664，Vezhnevets, Agapiou, Aharon, Ziv, Matyas, Duéñez-Guzmán, Cunningham, Osindero, Karmon, Leibo；代码 github.com/google-deepmind/concordia（Apache-2.0）。

### 2.4 Project Sid / PIANO（Altera，2024）

- **主张**：在 Minecraft 中运行 10–1000+ 个 agent，观察到"自主发展出专业化角色、遵守并改变集体规则、进行文化与宗教传播"。架构名 PIANO（Parallel Information Aggregation via Neural Orchestration）。35 页、14 图。
- **可复现性核查结果（重要）**：官方仓库 github.com/altera-al/project-sid 的 README 明确只说"This repository contains our technical report"，内容仅有论文 PDF、一张视觉摘要图与一个视频文件。**PIANO 实现、Minecraft 模拟代码、agent 框架、数据集均未发布。** 论文亦未经同行评议（arXiv preprint）。
- **评级与用法**：C 级。它的定性观察（专业化分工、规则演化、文化传播会在多 agent LLM 系统中出现）可以作为**假设来源**，但其任何数值主张都不能作为本项目的校准依据，也不应在设计文档中被引用为"已被证明"。
- **出处**：arXiv 2411.00114（2024-10-31）。

### 2.5 OASIS（Shanghai AI Lab 等，2024）

- **核心机制**：面向 X / Reddit 的社交媒体模拟器，最大 100 万 agent，21 种动作类型，带推荐系统。
- **硬数字**：百万 agent 实验用 **24 张 A100**；基座模型 **Llama3-8b-instruct**（开放权重，可自托管 → 版本可冻结）；198 个谣言传播实例上 scale 与 max breadth 的 NRMSE 约 30%。
- **与真实世界的偏离（这才是对我们最有价值的部分）**：
  - 模拟中的信息传播**深度系统性偏浅**（作者归因于简化的推荐算法）；
  - agent 对**负面社会线索的从众性强于真实人群**；
  - 未对齐（uncensored）模型的群体极化明显强于对齐模型——即**"社会现象的强度"是模型对齐程度的函数，而不只是社会结构的函数**；
  - 涌现式纠错机制只在 agent 数超过约 1 万时才出现。
- **出处**：arXiv 2411.11581（v1 2024-11-18，v5 2025-03-23），Yang, Zhang, Zheng 等 23 位作者。

- **〔R2〕吞吐锚点（本轮读 arXiv HTML v4 正文得到，是本简报里最有用的"算力现实感"数字）**：
  - "using five A100 GPUs, we can simulate the interactions of **100,000 users over 10 time steps within two days**"。
  - 百万 agent 规模下报告需要 **27.0 张 A100**，每 timestep 产生 48.5 千条新帖、97.1 千条新评论。
  - ⚠**冲突待核**：本文件第一轮记录的是"24 张 A100"，第二轮抓到的是"27.0"。两者可能来自不同表格/不同版本（论文 v1 2024-11-18 至 v5 2025-03-23）。引用前必须回原文表格核对，**不要在设计文档里使用这个数字的任何一个版本作为依据**，只用它的量级（数十张 A100）。
  - **换算成本项目的语言**：10⁵ 个 LLM agent 推进 **10 步**要 5 张 A100 跑 2 天。civilization-sim 要推进的是 **3,000 步（年）**。若按同构方式外推，即使只有 10⁵ 个 LLM agent，也是 5 张 A100 × 600 天。**这单独一条就足以否决"每个 agent 每 tick 一次 LLM 调用"的架构**，与是否有钱无关。
- **〔R2〕规则/LLM 的切分是显式的**：推荐系统完全由**确定性算法**承担，不过 LLM。X 平台按点赞数排序网内内容、用 TwHIN-BERT 做兴趣匹配推荐网外内容；Reddit 平台用固定公式 `h = log10(max(|u-d|,1)) + sign(u-d) * (t-t0)/45000` 计算 hot score。LLM 只负责"看到这些帖子之后做什么动作、给什么理由"。**这就是本项目要的形状：环境与撮合规则是数学，agent 的意图是 LLM。**

### 2.6 AgentSociety（清华 FIB Lab，2025）

- **核心机制**：城市尺度 LLM agent 社会模拟，1 万+ agent、约 500 万次交互，覆盖极化、煽动性信息传播、UBI、灾害响应、城市可持续五个议题。
- **硬数字**：Ray 分布式（每组 agent 独立进程）+ asyncio 并发 I/O；MQTT 消息吞吐 **44,702.1 ± 111.3 msg/s**；环境侧可承载 10⁶ 个体，step time 低至 **0.1680 s**；实验规模分别为 Columbia, SC 飓风 1,000 agent、北京城市可持续 200 agent。
- **明确承认的瓶颈**：**LLM API 成本与 rate limit** 是剩余瓶颈；论文未描述缓存、蒸馏或规则回退机制，效率手段只有架构层的批量与并发。
- **对本项目的教训**：即使把消息总线做到 4.4 万 msg/s、环境侧做到百万实体，**真正卡住规模的仍然是 LLM 调用本身**。这直接支持"必须把绝大多数实体交给规则、只让极少数交给 LLM"的设计。
- **出处**：arXiv 2502.08691（2025-02-12），Piao, Yan, Zhang 等；代码 github.com/tsinghua-fib-lab/agentsociety（Apache-2.0，commercial 目录例外；支持任意 litellm provider）。

- **〔R2〕这篇论文自己把"规则与 AI 分离"写成了设计原则**，原文（arXiv HTML v1）："By offloading tasks such as **numerical computations, where LLMs cannot guarantee absolute accuracy**, this approach simplifies agent design and allows researchers to concentrate on core objectives." 具体做法：agent 的**出行目的地选择**不交给 LLM，而是用**重力模型（Gravity model）**求解，论文的理由是这样"reduce LLM computational overhead while ensuring selections align with human spatial patterns"。
  - **可迁移的判据**：他们的切分线不是"重要 / 不重要"，而是"**这个量有没有一个已被校准过的数学模型**"。有（重力模型、SIR、排队论、价格出清）→ 规则；没有（一个人为什么背叛他的兄长）→ LLM。这条判据比"客观 / 主观"更可操作，建议直接写进本项目的架构文档。

### 2.7 LLM Archetypes / AgentTorch（Chopra et al., MIT Media Lab）

- **核心机制**：不给每个 agent 单独调 LLM，而是把 agent 聚类成少量**行为原型（archetype）**，每步只对原型查询 LLM，再把原型的行为分布广播回该原型下的所有 agent。
- **硬数字**：**840 万** agent（纽约市规模）；每个决策步约 **400 次** LLM 查询（而非数百万次）；相对逐 agent 查询效率提升约 **95%**；约 400 个行为原型；失业率误差 24.59 ± 1.5、感染误差 95.17 ± 20.23（对照启发式模型分别为 41.05 与 2914.73）。
- **形式化程度**：完全形式化，且有开源可微 ABM 平台（AgentTorch）实现。
- **对本项目的价值**：**这是 LLM 决策蒸馏最干净、最有量化支撑的既有做法**，可以近乎原样搬进 civilization-sim 的人口层（见第 3 节 M3）。
- **出处**：arXiv 2409.10568（2024-11-10 提交版本），Chopra, Kumar, Giray-Kuru, Raskar, Quera-Bofarull。

- **〔R2〕原文给出的调用数公式**（arXiv HTML v2）："By estimating p_alpha(k) for each archetype k, we can simulate the action of its agent by sampling the action from the archetype to which it belongs. Let K be the number of agent archetypes and A be the number of LLM-queryable actions; we can then simulate the behaviour of all agents with **K×A queries**."
  - 也就是说：**LLM 的调用量与 agent 数量完全解耦**，只与"你把人群切成多少类 × 有多少种需要 LLM 判断的动作"有关。这是本简报能给出的最重要的一条工程公式，直接支撑第 9.2 节的预算表。
  - LLM 不是被问"你要做什么"，而是被问"**这一类人在这种处境下选各个动作的概率分布是什么**"（`p_alpha(k)`），然后由**规则侧的 Monte Carlo 采样**把分布落到具体个体上。→ 这天然满足 MANDATE 第 6 条：随机性由我们自己的 PRNG 产生、可记录种子；LLM 只提供分布参数。
  - ⚠**冲突待核**：本轮抓到 NYC 算例用 **100 个原型**；本文件第一轮记录为"~400 个原型 / ~400 次查询每决策步"。两者不一致，须回原文核对。另：本轮明确确认论文**没有给出**任何美元成本、实际调用次数或端到端运行时长；"40,000×" 这个数字是**向量化 ABM 相对面向对象 ABM** 的通用加速比，**与 LLM 无关**，第一轮若把它读成 LLM 相关加速需要更正。
  - 论文报告校准使用 "V100 with 32 GB memory"。

### 2.8 Lyfe Agents（Kaiya et al. 2023）

- **核心机制**：option-action 框架（把高层决策与低层动作分离，降低高层决策频率）、异步自监控、Summarize-and-Forget 记忆。
- **硬数字**：约 **$0.5 / agent / 人类小时**，相对 Stanford GenAgent 框架**降低 10–100 倍**成本。
- **推论（本项目的算术，非文献主张）**：若 Lyfe 是 Park et al. 的 1/10–1/100，则 Park 式全量 generative agent 的量级约为 **$5–50 / agent / 人类小时**。这是我们必须避开的成本结构。
- **出处**：arXiv 2310.02172（2023-10-03），Kaiya, Naim, Kondic, Cortes, Ge, Luo, Yang, Ahn。

### 2.9 CivRealm（北大 / BUPT / BIGAI，2024）——最贴近本项目主题的负面证据

- **核心机制**：基于 Freeciv 的文明类决策环境，不完美信息、一般和、玩家数可变，需要外交与谈判；同时支持 RL agent 与 LLM agent。
- **量化结果**：RL agent 在有明确奖励信号的 mini-game 上约 **90%** 成功率，但在完整游戏中表现**短视**（追逐即时得分而非战略性建城）；LLM 侧 Mastaba 明显优于 BaseLang（Mastaba 在第 **113** 回合达到 BaseLang 需到第 **210** 回合才达到的探索/定居水平），但**两者都难以把知识转化为情境化的有效动作与防御策略**，"both paradigms struggle to make substantial progress in the full game"。
- **对本项目的直接意义**：这是目前最直接的实证——**在一个已经有完整规则内核、完整状态可观测的文明级环境里，LLM agent 依然无法胜任长时程战略决策**。因此在 civilization-sim 里把"国家的长期战略"交给 LLM 是没有实证依据的赌博；LLM 的角色应限定在"给出动机与提案"，长时程后果由规则与搜索/优化决定。
- **出处**：arXiv 2401.10568，Qi, Chen, Li, Kong, Wang, Yang, Wong, Zhong, Zhang, Zhang, Liu, Wang, Yang, Zhu。

---

### 2.10 〔R2〕Cicero（Meta FAIR Diplomacy Team, *Science* 2022）——"语言 / 裁决分离"的最强先例

- **核心机制**：在《外交》（Diplomacy，一个必须靠谈判结盟、且所有行动同时结算的多人博弈）中，Cicero 把系统拆成两半：**策略由规划 + 强化学习引擎产生**，**语言模型只负责把意图翻译成谈判话语、并从对方话语中反推意图**。语言模型不决定下哪一步棋。
- **结果**：40 场线上匿名比赛中"achieved more than double the average score of the human players and ranked in the **top 10%**"（among experienced participants）。
- **形式化程度**：完全形式化的博弈侧 + 神经语言侧；发表于 *Science*，同行评议。
- **对本项目的意义**：这是目前**唯一一个在有明确胜负判据的多主体博弈里、达到人类水平、并且明确把语言与裁决分开**的系统。它证明的不是"LLM 很强"，而是"**把语言能力和结果裁决分开之后，两边都变强了**"。MANDATE 第 5 条在这里有一个真实世界的成功案例可以引用，而不只是一个直觉。
- **局限**：Diplomacy 有精确规则与固定回合；文明模拟没有。因此 Cicero 能给我们的是**架构证据**，不是**参数**。
- **出处**：Meta Fundamental AI Research Diplomacy Team (FAIR) et al. (2022). *Human-level play in the game of Diplomacy by combining language models with strategic reasoning.* Science 378(6624):1067–1074. doi:10.1126/science.ade9097.〔Europe PMC 核验〕

### 2.11 〔R2〕LLM-Modulo（Kambhampati et al., ICML 2024）——"LLM 提案 / 外部验证器裁决"的通用形式

- **核心主张**（position paper，ICML 2024 正式收录）："auto-regressive LLMs **cannot, by themselves, do planning or self-verification**"。应把 LLM 当作**知识源与候选生成器**，把可靠性交给**外部的、基于模型的验证器（model-based verifiers）**，并强调这两者应是"tighter **bi-directional** interaction"而不是简单串联流水线。
- **形式化程度**：框架级（定性），不给参数。
- **对本项目的意义**：这为我们的三层结构提供了学界正式表述——**LLM 生成候选 → 规则验证并裁决 → 反馈回 LLM 作为下一轮上下文**。特别值得注意的是 "bi-directional"：如果我们只做"LLM 提案、规则否决"而不把否决的**理由**回灌给 agent，agent 会反复提出同样的不可行方案，白烧 token。否决理由必须结构化回传（例如 `rejected: insufficient_grain, need=12000, have=4300`），这既省钱，又恰好构成因果链上的一条记录。
- **出处**：Kambhampati, S., Valmeekam, K., Guan, L., Verma, M., Stechly, K., Bhambri, S., Saldyt, L. P., & Murthy, A. B. (2024). *Position: LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks.* ICML 2024, PMLR 235:22895–22907.〔PMLR 核验〕

### 2.12 〔R2〕Eureka / Voyager——"LLM 写代码，规则引擎执行"的蒸馏范式

- **Voyager 的 skill library**：LLM 生成**可执行代码**表示的技能，通过环境反馈与自校验迭代，成功的技能被**存入库中检索复用**。LLM 的产物是**程序**，不是一次性决策。
- **Eureka**：LLM 读环境源码，**直接写出奖励函数代码**；GPU 并行仿真批量评估；用 "reward reflection"（训练统计摘要）驱动 LLM 进化式改写。项目页报告在 29 个任务上 **83%** 优于人类工程师手写奖励，平均归一化提升 **52%**。
- **对本项目的意义**：这是 M5"策略固化 / 蒸馏"最有力的先例——**让 LLM 生产规则，而不是让 LLM 充当规则**。落到 civilization-sim：
  1. LLM 不在每个 tick 决定"这个王国要不要征税"，而是**一次性生成一个税制条文（DSL 代码）**：`tax(household) = min(0.3, base + 0.1*war_state) * grain_yield`；
  2. 规则引擎在之后的几十上百年里**确定性地执行**它，零 token 成本；
  3. 只有当"执行结果与制定者预期严重背离"（规则可检测：连续 N 年税收缺口 > X%）时，才重新唤醒 LLM 去改写条文。
  这同时解决了三件事：成本、可重放性、以及**制度的路径依赖**（制度是一段被写下来的代码，会一直生效，直到有人有动机去改它——这正是 MANDATE 第 3 条要的东西）。
- **证据强度**：Eureka 的 83%/52% 是**项目页自述**，本轮未读到同行评议版本正文；Voyager 的 3.3×/2.3×/15.3× 见第 4 节。作为**架构范式**是 B 级，作为**数值**是 C 级。
- **出处**：Wang, G. et al. (2023). *Voyager.* arXiv:2305.16291〔arXiv 摘要页核验〕；Ma, J. et al. (2023). *Eureka: Human-Level Reward Design via Coding Large Language Models.*〔eureka-research.github.io 项目页核验；venue 未核实〕

### 2.13 〔R2〕领域综述与元研究（用于确认本简报没有系统性漏掉一整支文献）

- Gao, C., Lan, X., Li, N., Yuan, Y., Ding, J., Zhou, Z., Xu, F., & Li, Y. (2023). *Large Language Models Empowered Agent-based Modeling and Simulation: A Survey and Perspectives.* arXiv:2312.11970. 该综述把问题域切成 **environment perception / human alignment / action generation / evaluation** 四类挑战，覆盖 cyber、physical、social、hybrid 四类环境。〔arXiv 检索页核验〕
  - **注意**：这是与 AgentSociety 同一课题组（清华 Yong Li 组）的综述，选材上会偏向他们自己的技术路线；作为"文献地图"可用，作为"评价"须打折。
- Kapoor, S. et al. (2024). *AI Agents That Matter.* arXiv:2407.01502。本轮补齐完整摘要，其中与本项目最相关的四条批评：(1) 只优化准确率、不看成本，导致 agent "needlessly complex and costly"；(2) 模型开发者与下游开发者的评测需求被混为一谈；(3) 许多 agent benchmark **没有 holdout set**，导致 agent 走捷径、过拟合；(4) "a pervasive **lack of reproducibility**"。
  - **对我们的直接约束**：任何"我们的世界产生了合理历史"的结论，如果不同时报告**成本**与**可重放的种子/ledger**，按这篇的标准就是不可信的。建议把"成本 + 种子 + 模型版本"写进每次长跑实验的必填字段。

---

## 3. 可直接用于本项目的机制清单

下列机制按"应当写进内核的优先级"排序。每条给出：输入→输出、算法草图、时间尺度、空间粒度、证据等级、以及**为什么这样简化**。

### M1. Intent/Outcome 二分（Game Master 硬边界）— 证据 B，归属 hybrid（接口）

- **输入**：`Actor`（人物或组织）的世界观切片 `View(actor, t)`（受信息边界约束）+ 可选的 LLM 提案。
- **输出**：一个**类型化的 Intent 对象**（枚举 + 结构化参数），而非自由文本；随后由纯规则的 `Resolver` 计算 `Outcome`。
- **算法草图**：
  ```
  intent  := LLM(View(actor,t), persona, memory)        # 只允许输出 schema 内的枚举与参数
  intent  := validate(intent)                            # 非法 intent → 回退到规则默认策略
  outcome := Resolve(world_state, intent, rng(seed))     # 纯函数，无 LLM
  world'  := Apply(world_state, outcome)
  log(intent, outcome, causal_edges)
  ```
- **时间尺度**：与 actor 的决策周期一致（见 M4，从"季"到"代"不等）。
- **空间粒度**：actor 所在的政治/经济实体。
- **为什么这样简化**：Concordia 已把这个切分做成框架级设计；CivRealm 证明 LLM 在完整状态可观测的文明环境中仍无法可靠地把决策转成好结果；MAST（14 种失败模式，3 大类，其中一大类就是 "task verification"）证明多 agent LLM 系统的失败大量来自缺乏验证环节。把 `Resolve` 做成纯函数还带来一个 MANDATE 必需的副产品：**结果可重算、可反事实**。
- **失效条件**：当 Intent 的枚举空间设计得太窄，LLM 会被迫把复杂动机压进错误的枚举格，产生"制度性误译"。缓解：Intent schema 必须带一个 `freeform_rationale` 字段（只进因果日志，不进裁决）与一个 `novel_action_request` 通道（走人工/规则扩展审批，不即时生效）。

### M2. 规则优先、LLM 例外（LLM 作为稀疏中断，而非每 tick 驱动）— 证据 B，归属 rules_math + llm_agent

- **输入**：世界状态；一组**规则侧触发器**（`trigger predicates`）。
- **输出**：本 tick 需要 LLM 介入的 actor 列表（通常为 0）。
- **算法草图**：
  ```
  for tick in timeline:
      world = step_rules(world)                 # 人口、生产、气候、疫病、价格：纯数学
      hot   = [a for a in actors if any(trig(a, world) for trig in TRIGGERS)]
      hot   = topk(hot, budget_this_tick)       # 预算硬上限
      for a in hot: intent = LLM(...); apply(M1)
  ```
  典型触发器：`资源缺口 > θ`、`合法性指标跌破 θ`、`边界接触新政体`、`继承危机`、`技术阈值跨越`、`外部冲击（灾害/瘟疫）落在本实体`。
- **时间尺度**：触发器每 tick 评估（纯算术，成本可忽略）；LLM 调用只在触发时发生。
- **空间粒度**：政体 / 组织 / 关键人物。
- **为什么这样简化**：AgentSociety 明确指出 LLM API 成本与 rate limit 是剩余瓶颈，即使消息总线做到 4.4 万 msg/s；Lyfe Agents 的主要收益也来自 option-action 分离（降低高层决策**频率**）。降低频率是比换便宜模型更有效的杠杆，因为它同时降低成本、降低不确定性注入率、并缩短因果链长度。
- **失效条件**：触发器集合本身就是一种隐藏剧情树——如果触发器只在"戏剧性时刻"触发，世界就只在戏剧性时刻有 agency。缓解：触发器必须只引用**物理/经济/信息量**（缺口、阈值、接触、冲击），禁止引用"距上次战争已 N 年"这类叙事节拍变量。

### M3. 原型蒸馏（LLM Archetypes）— 证据 A，归属 hybrid

- **输入**：大量同质 actor（村落、家户、士兵群、商人群）的特征向量。
- **输出**：`K` 个原型的行为分布，广播给该原型下所有 actor。
- **算法草图**：
  ```
  archetypes = cluster(features(actors), K)          # K ~ 10^2 量级
  for arch in archetypes:
      dist = LLM(prompt(arch.centroid_description, context))   # 输出概率分布，不是单一动作
      cache[arch.signature] = dist                   # signature 含 context 的离散化桶
  for a in actors: a.action = sample(cache[a.arch], rng)
  ```
- **时间尺度**：原型层的 LLM 刷新频率可以远低于 tick（例如每 10–50 tick，或仅在 context 桶发生跳变时）。
- **空间粒度**：区域 × 社会阶层 × 生业类型。
- **量化依据**：Chopra et al. 用约 400 个原型覆盖 840 万 agent，每决策步约 400 次 LLM 查询，效率提升约 95%，且在失业与感染两个指标上显著优于启发式基线。
- **为什么这样简化**：本项目的人口层必然是 10⁵–10⁷ 量级实体。逐实体调 LLM 在任何价格下都不可行；原型蒸馏是唯一有量化实证的替代方案。
- **失效条件**：原型抹平尾部。真正稀有的行为（第一个铸币者、第一个写下文字的人）**不会**从原型分布里出现。缓解：尾部必须由**规则侧的低概率事件生成器**（受环境条件约束的泊松过程）产生，而不是指望 LLM 采样出来——这与 MANDATE 第 6 条"受约束的随机性"一致，见 M6。

### M4. 多时间尺度决策周期 — 证据 D（本项目设计），归属 rules_math

- 人口/生产/气候：每 tick（季或年）纯规则。
- 家户/村落原型：每 10–50 tick 刷新一次原型分布（M3）。
- 组织（宗族、教团、行会、官僚机构）：事件驱动 + 每 5–20 年一次常规复议。
- 关键人物（有名字的历史人物）：仅在触发器命中时（M2），一生 LLM 调用总数应有硬上限（如 ≤ 200 次/人）。
- **为什么**：LLM 调用总量 = Σ(actor 数 × 频率)。把频率做成尺度相关的，是唯一能让"数千年"与"有名字的人物"共存的办法。
- **失效条件**：尺度之间的信息传递若做错，会出现"人物决策与人口趋势脱钩"。缓解：人物 View 中必须包含由规则层聚合出的、带滞后与噪声的宏观指标。

### M5. 缓存与决策复用（语义缓存 + 策略固化）— 证据 C（工程实践，非同行评议），归属 rules_math

- **输入**：`(persona_id, situation_bucket, culture_id, information_state_hash)`。
- **输出**：命中则复用既有 Intent 分布；未命中才调 LLM。
- **算法草图**：把 situation 离散化成桶（资源缺口分 5 档、威胁等级 4 档、合法性 4 档……），缓存键用**离散桶**而非连续状态；命中率随模拟时长单调上升。进一步，可对高频命中的键做"策略固化"：把 LLM 反复给出的同一 Intent 写成一条**显式规则**存入该文化/该组织的 `institutional policy` 表，此后由规则执行，且这条规则本身成为世界内的可观测对象（可以被后来者继承、批评、改革）。
- **量化依据**：GPTCache（MIT 许可）自称语义缓存可"降低 10 倍成本、提升 100 倍速度"——注意这是**项目 README 的营销主张，非同行评议结果**，只能当作量级提示（C 级）。Anthropic 侧的 prompt caching 有明确定价：cache read ≈ 基础输入价的 0.1×，cache write 为 1.25×（5 分钟 TTL）或 2×（1 小时 TTL）。
- **为什么这样简化**：策略固化同时解决三个问题——成本、可重放性（规则是确定性的）、以及 MANDATE 第 3 条路径依赖（固化下来的策略就是"制度"，它有历史连续性）。
- **失效条件**：过度固化会让世界僵化，失去 agency。缓解：给每条固化策略一个"复议触发器"（环境剧变、合法性崩塌、代际更替），命中则回到 LLM 重新提案。

### M6. 尾部事件由规则生成，LLM 只做解释 — 证据 B，归属 rules_math

- **输入**：环境条件、人口密度、贸易网络连通度等。
- **输出**：低概率事件（新技术发现、疫病、天灾、暗杀成功、异端出现）的发生与否。
- **算法草图**：`P(event) = f(structural_preconditions) `，用受约束的泊松/伯努利过程，种子可记录；事件**发生之后**才允许 LLM 生成"世界内的人如何理解与叙述这件事"。
- **为什么这样简化**：Bisbee et al. 实证发现 LLM 合成的调查响应**方差显著小于真实调查**（标准差实质性偏低）；Padmakumar & He 发现 InstructGPT 协作写作显著降低内容多样性；Mohammadi 观测到对齐模型 token 预测熵下降并落入"吸引子态"；Verbalized Sampling 把 mode collapse 归因于人类偏好数据中的 typicality bias（标注者以 51.6–60.8% 的比率偏好"典型"回答）。四条独立证据指向同一结论：**对齐后的 LLM 系统性地压缩尾部**。因此把"罕见事件是否发生"交给 LLM，等于系统性地删除罕见事件——这会直接摧毁 MANDATE 第 7 条（允许荒诞）。
- **失效条件**：如果结构性前置条件函数 `f` 本身写得太保守，世界会平庸。这是参数问题，不是架构问题，可通过校准调节。

### M7. LLM 作为"带种子的外部随机源"（可重放） — 证据 A（非确定性有实证），归属 rules_math（记录层）

- **输入**：完整调用上下文。
- **输出**：一条**不可变的调用记录**，及其在世界状态上的确定性效应。
- **算法草图**：见第 7 节完整方案。核心：`llm_call_id = H(model_id, model_version, params, prompt_bytes, call_seq)`；结果连同 `llm_call_id` 一起写入 append-only 的 `llm_ledger`；重放时**只读 ledger，不重新调用模型**。
- **量化依据**：温度为 0 **不保证**确定性——Ouyang et al. 在 829 个编程任务上发现零匹配输出的比例为 CodeContests 75.76%、APPS 51.00%、HumanEval 47.56%；Thinking Machines 的分析进一步指出根因是推理内核缺乏 **batch invariance**（服务端负载导致 batch size 变化），并给出实验：Qwen3-235B 在温度 0 下对同一 prompt 采样 1000 次得到 **80 个不同 completion**，前 102 个 token 完全一致之后才分叉；启用 batch-invariant kernel 后 1000 次输出完全一致。再加上模型版本漂移（Chen, Zaharia & Zou：GPT-4 在质数判定任务上 2023 年 3 月 84% → 6 月 51%；Bisbee et al.：2023 年 4 月与 7 月同 prompt 重跑，在 6 月 25 日模型更新后出现实质性均值回归）。
- **结论**：**不可能通过"重新调用模型"来重放历史。** 唯一可行的重放机制是把 LLM 输出当作外部熵源持久化。

### M8. 结构化输出 + 工具约束，但把推理留在自由文本里 — 证据 B，归属 hybrid

- Tam et al. 实证发现**格式限制会显著降低 LLM 的推理能力**，且"更严格的格式约束通常导致更大的推理性能下降"。
- 因此推荐的调用形态是**两段式**：先让模型自由推理（thinking / rationale，只进因果日志），再由同一次调用的结构化字段承载可裁决的 Intent。绝不能只给一个纯 JSON schema 就要求它做复杂权衡。
- **失效条件**：自由推理段会成为 prompt injection 与"戏剧化倾向"的载体。缓解：自由段**只写日志、不进裁决、不进下一次调用的上下文**（除非经过规则侧摘要）。

### M9. LLM-as-judge 只用于"世界内叙事质量"，不用于"世界事实" — 证据 A，归属 llm_agent（受限）

- Zheng et al. 报告强 LLM judge 与人类偏好一致率 >80%（与人类之间的一致水平相当），但同时明确记录 position bias、verbosity bias、self-enhancement bias。
- Wang et al. 给出 position bias 的极端量化：仅改变候选回答的出现顺序，就能让 Vicuna-13B 在 80 个查询中的 **66 个**上"胜过"ChatGPT。
- Panickssery et al. 证明 LLM 能以非平凡准确率识别自己的输出，且**自我识别能力与自我偏好强度呈线性相关**。
- **结论**：任何"由 LLM 判定谁赢了/谁更强/事件是否合理"的设计都不可接受。LLM-as-judge 在本项目里唯一合法的用途是**离线评估**：比较两条历史线的叙事可读性、检查生成文本是否泄露了 agent 不该知道的信息（信息边界审计）。且必须做位置随机化 + 双向打分。

### M10. 信息边界的强制实现 — 证据 D（本项目设计），归属 rules_math

- MANDATE 第 4 条要求 agent 不能有上帝视角。工程上这必须是**构造性**的：`View(actor, t)` 由规则层从世界状态**投影**出来，LLM 的 prompt 只能由 `View` 组装，物理上无法访问全局状态。
- 附带收益：`View` 是缓存键的天然组成部分（M5），也是 prompt 前缀稳定性的天然分界（把"人格 + 文化 + 制度"放前缀做缓存，把"当前局势"放后缀）。
- **失效条件**：`Lost in the Middle`（Liu et al.）显示长上下文中置于中部的信息被显著忽略（U 形曲线）。因此 `View` 不能靠"塞进 20 万 token 让模型自己找"，必须由规则层做**显式的相关性筛选与排序**，把最关键的约束放在开头和结尾。

---

## 4. 硬数字与参数表

| 数值 | 单位 | 含义 | 适用时空范围 | 不确定度 | 来源 |
|---|---|---|---|---|---|
| 25 | agent | Smallville 规模 | 2 个模拟日 | 精确 | Park et al. 2023, arXiv 2304.03442 |
| 1,052 | 人 | 访谈基底 agent 的参与者数 | 美国 | 精确 | arXiv 2411.10109 |
| 2 | 小时 | 每人半结构化访谈时长 | 同上 | 名义值 | arXiv 2411.10109 |
| 83 / 82 / 86 / 74 | % | 访谈 / 问卷 / 合并 / 人口统计基线 的归一化准确率（分母＝真人自身 test-retest 一致性） | 同上 | 论文未在摘要给出 CI | arXiv 2411.10109 |
| 10–1000+ | agent | Project Sid 规模主张 | Minecraft | **代码未发布，不可复现** | arXiv 2411.00114 |
| 1,000,000 | agent | OASIS 最大规模 | 社交媒体 | 精确 | arXiv 2411.11581 |
| 24 | 张 A100 | OASIS 百万 agent 实验硬件 | 同上 | 精确 | arXiv 2411.11581 |
| 21 | 种 | OASIS 动作空间大小 | 同上 | 精确 | arXiv 2411.11581 |
| ~30 | % NRMSE | OASIS 谣言传播 scale/max-breadth 误差（198 实例） | X 平台 | 论文报告值 | arXiv 2411.11581 |
| ~10,000 | agent | OASIS 中涌现式纠错机制出现的阈值 | 同上 | 定性阈值 | arXiv 2411.11581 |
| 10,000+ / ~5,000,000 | agent / 交互 | AgentSociety 规模 | 城市 | 精确 | arXiv 2502.08691 |
| 44,702.1 ± 111.3 | msg/s | AgentSociety MQTT 吞吐 | 同上 | ±1σ | arXiv 2502.08691 |
| 0.1680 | s | AgentSociety 环境 step time（10⁶ 个体） | 同上 | 精确 | arXiv 2502.08691 |
| 8,400,000 | agent | AgentTorch LLM-archetype 规模（纽约市） | 城市 | 精确 | arXiv 2409.10568 |
| ~400 | 次/决策步 | 上述规模下的 LLM 查询数 | 同上 | 约数 | arXiv 2409.10568 |
| ~95 | % | 相对逐 agent 查询的效率提升 | 同上 | 约数 | arXiv 2409.10568 |
| ~400 | 个 | 从 840 万 agent 中识别的行为原型数 | 同上 | 约数 | arXiv 2409.10568 |
| 0.5 | USD / agent / 人类小时 | Lyfe Agents 运行成本 | 2023 年模型与价格 | 量级值 | arXiv 2310.02172 |
| 10–100 | 倍 | Lyfe 相对 Stanford GenAgent 的成本下降 | 同上 | 量级值 | arXiv 2310.02172 |
| 48 / 32 | % / % | ChatGPT 合成 ANES 数据中"与真实回归系数显著不同的系数比例"／"其中符号翻转的比例" | 美国 ANES，GPT-3.5-Turbo，2023 | 论文报告值 | Bisbee et al. 2024, Political Analysis 32(4):401–416, doi:10.1017/pan.2024.5 |
| 84 → 51 | % | GPT-4 质数判定准确率，2023-03 → 2023-06 | 该任务集 | 论文报告值 | Chen, Zaharia & Zou, arXiv 2307.09009 |
| 75.76 / 51.00 / 47.56 | % | 温度 0 下"零匹配输出"任务比例（CodeContests / APPS / HumanEval，829 任务） | 代码生成 | 论文报告值 | Ouyang et al., arXiv 2308.02828 |
| 80 / 1000 | 个不同 completion / 次采样 | Qwen3-235B 温度 0 同 prompt 的非确定性 | 单次实验 | 单一来源 | Thinking Machines, "Defeating Nondeterminism in LLM Inference" |
| 102 | token | 上述实验中输出开始分叉的位置 | 同上 | 单一来源 | 同上 |
| 76 | accuracy points | 仅改变 prompt 格式造成的最大性能差（LLaMA-2-13B） | 多任务 | 论文报告值 | Sclar et al., arXiv 2310.11324 |
| 66 / 80 | 查询 | 仅改变候选顺序即可让 Vicuna-13B "胜过" ChatGPT 的查询数 | Vicuna Benchmark | 论文报告值 | Wang et al., arXiv 2305.17926 |
| >80 | % | GPT-4 judge 与人类偏好一致率（与人类间一致水平相当） | MT-Bench / Chatbot Arena | 论文报告值 | Zheng et al., arXiv 2306.05685 |
| 14 / 3 / 1600+ / 150 / 0.88 | 失败模式 / 类别 / 标注轨迹 / 构建分类法用轨迹 / Cohen κ | MAST 多 agent 失败分类法（7 个框架） | LLM 多 agent 系统 | 论文报告值 | Cemri et al., arXiv 2503.13657 |
| 3,200 / 16 | 参与者 / 身份群体 | LLM 对身份群体"扁平化与错误刻画"的实证规模 | 美国 | 论文报告值 | Wang, Morgenstern & Dickerson, arXiv 2402.01908 |
| 51.6–60.8 | % | 人类标注者偏好"典型"回答的比率（typicality bias） | 多数据集 | 论文报告值 | arXiv 2510.01171 |
| 1.6–2.1 | 倍 | Verbalized Sampling 相对直接 prompt 的语义多样性提升 | 创意写作 | 论文报告值 | arXiv 2510.01171 |
| 92 | % | BIG-Bench 中"涌现能力"主张集中于两类指标的比例 | 元分析 | 论文报告值 | Schaeffer, Miranda & Koyejo, arXiv 2304.15004 |
| ~90 | % | RL agent 在 CivRealm mini-game 上的成功率（完整游戏中表现短视） | Freeciv | 论文报告值 | Qi et al., arXiv 2401.10568 |
| 113 vs 210 | 回合 | CivRealm 中 Mastaba 与 BaseLang 达到同等探索/定居水平所需回合 | 同上 | 论文报告值 | 同上 |
| 3.3× / 2.3× / 15.3× | 倍 | Voyager 相对前 SOTA 的独特物品数 / 移动距离 / 科技树解锁速度 | Minecraft | 论文报告值 | Wang et al., arXiv 2305.16291 |

**〔R2〕第二轮新增 / 更正的数字**（与上表并列，不覆盖上表；标 ⚠ 者为两轮结果冲突，须回原文核对后才可使用）

| 数值 | 单位 | 含义 | 适用时空范围 | 不确定度 | 来源 |
|---|---|---|---|---|---|
| 0.995 | — | Smallville recency 衰减因子；**按记忆排序序号 i 幂次衰减**（`0.995**i`），不是按物理时间 | 25 agent × 2 模拟日 | 精确（源码） | `.../bootstrap_memory/scratch.json`〔GitHub raw 核验〕 |
| [0.5, 3, 2] | 权重 | 检索总分中 recency / relevance / importance 的固定乘子 `gw` | 同上 | 精确（源码） | `retrieve.py`〔GitHub raw 核验〕 |
| 30 | 条 | 每个 focal point 默认取回的记忆条数 `n_count` | 同上 | 精确（源码） | 同上 |
| 150 | 累计 importance 分 | 触发一次 reflection 的阈值 `importance_trigger_max` | 同上 | 精确（源码） | `scratch.json` |
| 8 / 8 / 8 | 格 / 事件 / 事件 | `vision_r`（视野半径）/ `att_bandwidth`（每步最多感知事件数）/ `retention`（重复事件抑制窗口）——**信息边界的实现原语** | 同上 | 精确（源码） | 同上 |
| 5 / 180 | 条 / 秒 | `daily_reflection_size` / `daily_reflection_time` | 同上 | 精确（源码） | 同上 |
| 100 / 4 / 10 / 9 | 分 / 次 / 次 / 次 | `concept_forget` / `overlap_reflect_th` / `kw_strg_event_reflect_th` / `kw_strg_thought_reflect_th`（反思与遗忘的其余阈值） | 同上 | 精确（源码） | 同上 |
| 5 / 100,000 / 10 / 2 | A100 / 用户 / time step / 天 | OASIS 实测吞吐锚点："using five A100 GPUs, we can simulate the interactions of 100,000 users over 10 time steps within two days" | 社交媒体 | 论文报告值 | arXiv 2411.11581（HTML v4）〔R2〕 |
| 27.0 ⚠ | A100 | OASIS 百万 agent 所需 GPU 数（**第一轮记录为 24，冲突待核**） | 同上 | ⚠冲突 | 同上 |
| 48.5k / 97.1k | 条 / time step | 百万 agent 规模下每步新增推文 / 评论数 | 同上 | 论文报告值 | 同上〔R2〕 |
| `h = log10(max(|u−d|,1)) + sign(u−d)·(t−t0)/45000` | — | OASIS Reddit 侧的**确定性** hot-score 排序公式（LLM 不参与撮合） | 同上 | 精确（公式） | 同上〔R2〕 |
| **K × A** | 次 / 决策步 | AgentTorch 的 LLM 查询数：K = 原型数，A = 需要 LLM 判断的动作数；**与 agent 数量无关** | 城市尺度 | 精确（公式） | arXiv 2409.10568（HTML v2）〔R2〕 |
| 100 ⚠ | 个 | NYC 840 万 agent 算例使用的原型数（**第一轮记录为 ~400，冲突待核**） | 同上 | ⚠冲突 | 同上 |
| 40,000× | 倍 | 向量化 ABM 相对面向对象 ABM 的加速比——**与 LLM 无关**，不得当作 LLM 加速比引用 | 同上 | 论文报告值 | 同上〔R2，更正〕 |
| 2,414 | 人 | Ozkan 用于 persona 接地的真实 WVS 受访者数 | 非 WEIRD 人群 | 精确 | arXiv 2607.18310〔R2〕 |
| 0.36 → 0.69 | 集中度 | N 个独立 LLM persona agent 复现人群分布时的**分布坍缩** | 同上 | 单一来源（单作者预印本，2026） | 同上 |
| 1.46 → 0.77 | 熵 | 同上（多样性塌陷的另一度量） | 同上 | 同上 | 同上 |
| 0.44 | TVD | 与真实人群分布的总变差距离 | 同上 | 同上 | 同上 |
| 85 | % | 发生坍缩的场景比例；坍缩程度与场景结构相关 r=0.55 | 同上 | 同上 | 同上 |
| ~80 | % | 行为任务中 persona **默认选最便宜选项**的比例；收入档位只把它调制为 0% → 7% → 32% | 同上 | 同上 | 同上 |
| 7–10 / 0.4–0.56 → 1.26–1.37 | 百分点 / SD-ratio | Verbalized Sampling 把保真度提升 7–10 点，但**矫枉过正**（标准差比从过低翻到过高） | 同上 | 同上 | 同上 |
| 83 / 52 | % / % | Eureka 生成的奖励函数优于人类工程师的任务比例 / 平均归一化提升（29 个任务） | 机器人 RL | 项目页自述，未读同行评议正文 | eureka-research.github.io〔R2〕 |
| >2× / top 10% | 倍 / 分位 | Cicero 在 40 场线上 Diplomacy 中相对人类平均分的倍数 / 排名 | Diplomacy | 论文报告值 | Science 378(6624):1067–1074〔R2〕 |
| ~30 | % | **Claude 4.7 及之后模型的新分词器对同一段文本多产生的 token 比例**（官方文档原话："approximately 30% more tokens for the same text"） | Anthropic API | 官方文档，"exact increase depends on content" | platform.claude.com 定价页〔R2〕 |

> **⚠ 冲突处理规则（写进项目规范）**：本表中任何标 ⚠ 的数字，在 Phase 1 被引用进设计文档之前，必须由人回原始论文表格核对一次，并把核对结论写回本文件。两轮独立抓取给出不同数字，说明**至少一轮的抓取管道（含 AI 摘要中间层）引入了误差**——这本身就是"不要把二手摘要当一手数据"的实例。

### 4.1 LLM 价格参数（用于第 6 节预算，Anthropic 一方 API 价格，缓存日期 2026-06-24）

| 模型 | Model ID | 上下文 | 输入 $/MTok | 输出 $/MTok |
|---|---|---|---|---|
| Claude Opus 5 | `claude-opus-5` | 1M | 5.00 | 25.00 |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M | 2.00 | 10.00 |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 200K | 1.00 | 5.00 |

- **Prompt caching**：cache read ≈ 基础输入价的 **0.1×**；cache write **1.25×**（5 分钟 TTL）或 **2×**（1 小时 TTL）。5 分钟 TTL 下两次请求即回本（1.25× + 0.1× = 1.35× vs 2× 未缓存）。
- **Message Batches**：异步批处理为 **50%** 价格。
- **前缀顺序**：`tools → system → messages`；任何字节变动使其后的缓存全部失效。因此"人格 + 文化 + 制度"必须放最前且**逐字节稳定**，"当前局势"放最后。
- 来源：Anthropic 官方 API 文档（经由本机 `claude-api` skill 的缓存表与 `shared/prompt-caching.md` 读取）。

---

### 4.2 〔R2〕Anthropic 官方定价页直接核验（2026-09-10 抓取 platform.claude.com/docs/en/about-claude/pricing）

第一轮的 4.1 节来自本机 skill 的缓存表（缓存日期 2026-06-24）。第二轮直接抓了官方定价页，结论一致，并补齐了缓存写/读的**逐档单价**与 Batch 单价表。**这是本简报中唯一一组 A 级、可直接进预算模型的价格数据。**

| 模型 | 基础输入 $/MTok | 5 分钟缓存写 | 1 小时缓存写 | 缓存命中/刷新 | 输出 $/MTok | Batch 输入 | Batch 输出 |
|---|---|---|---|---|---|---|---|
| Claude Opus 5 | 5.00 | 6.25 | 10.00 | **0.50** | 25.00 | 2.50 | 12.50 |
| Claude Sonnet 5 | 2.00 | 2.50 | 4.00 | **0.20** | 10.00 | 1.00 | 5.00 |
| Claude Haiku 4.5 | 1.00 | 1.25 | 2.00 | **0.10** | 5.00 | 0.50 | 2.50 |
| Claude Fable 5.1 | 10.00 | 12.50 | 20.00 | **0.25**（0.025×，特例） | 50.00 | 5.00 | 25.00 |

- **倍率**：5 分钟缓存写 = 1.25×；1 小时缓存写 = 2×；缓存命中 = **0.1×**（Fable 5.1 / Mythos 5.1 为 0.025×）。官方原文："a cache hit costs 10% of the standard input price, which means caching pays off after **one** cache read for the 5-minute duration (1.25x write), or after **two** cache reads for the 1-hour duration (2x write)."
- **Batch API = 输入与输出**均 50% 折扣；官方明确说明 **Batch 折扣与 prompt caching 可以叠加**（"Batch API and prompt caching discounts can be combined"）。第 9.2 节预算表依赖这一点，现已核实。
- **工具定义也要计费**：只要请求里带 `tools`，就会额外注入工具系统提示（Opus 5：`auto`/`none` 为 **286** token，`any`/`tool` 为 **406** token），再加上你自己的 schema 文本。对"每次调用只输出一个小 JSON"的高频调用，这部分**可能占输入的一大半**——预算时必须计入，否则会低估 20–50%。
- **分词器变更**：官方注明 Claude 4.7 及之后的模型使用新分词器，"produces **approximately 30% more tokens for the same text**"。→ **同一段 prompt 换到新一代模型上，token 数会涨约 30%，即使 $/MTok 没变，账单也会涨。** 预算模型里必须有这个乘子，且在换模型时重新用 `count_tokens` 标定。
- **代码执行**：每组织每月 1,550 小时免费，超出 $0.05/容器·小时。若我们把"规则引擎执行 LLM 写出的制度 DSL"放在服务端沙箱里跑，这是相关成本项；但更合理的做法是在**我们自己的进程内**执行，成本为零。
- **来源**：platform.claude.com/docs/en/about-claude/pricing〔2026-09-10 直接抓取核验〕。价格会变，**每次做长跑预算前重新抓一次**。

---

## 5. 数据集与数据库

| 名称 | 内容 | 覆盖范围 | 访问方式 / URL | 许可 |
|---|---|---|---|---|
| generative_agents | Smallville 完整代码 + 已保存模拟存档 + replay/demo 前端 | 25 agent × 2 模拟日 | github.com/joonspk-research/generative_agents | 见 repo（Apache-2.0 声明于 repo） |
| Concordia | GABM 框架，Game Master / component 架构参考实现 | 通用 | github.com/google-deepmind/concordia | Apache-2.0 |
| AgentSociety | 城市尺度 LLM agent 模拟平台，Ray + MQTT + litellm | 城市（含北京算例） | github.com/tsinghua-fib-lab/agentsociety | Apache-2.0（`packages/agentsociety/commercial` 除外） |
| OASIS | 百万 agent 社交模拟器，21 动作空间，Llama3-8b 基座 | X / Reddit | 论文 arXiv 2411.11581（代码由 camel-ai 生态发布） | 未在本次检索中核实许可 |
| AgentTorch | 可微 ABM 平台 + Archetype API | 840 万 agent 城市算例 | 论文 arXiv 2409.10568 指向开源实现 | 未在本次检索中核实许可 |
| MAST-Data | 1600+ 条多 agent LLM 系统失败轨迹标注（7 个框架） | LLM 多 agent | 论文 arXiv 2503.13657 | 未在本次检索中核实许可 |
| OpinionQA | LM 观点 vs 60 个美国人口群体的民调对齐评测集 | 美国 | 论文 arXiv 2303.17548 | 未在本次检索中核实许可 |
| Project Sid | **仅技术报告 PDF + 视觉摘要图 + 视频**，无代码无数据 | — | github.com/altera-al/project-sid | — |
| CivRealm | Freeciv 决策环境，支持 RL 与 LLM agent | 文明类完整博弈 | 论文 arXiv 2401.10568 | 未在本次检索中核实许可 |
| GPTCache | LLM 语义缓存库 | 通用 | github.com/zilliztech/GPTCache | MIT |

> **对本项目的取舍**：Concordia（架构参考）、AgentTorch/Archetype（成本机制参考）、CivRealm（负面基线）三者最值得投入时间。generative_agents 值得读代码但不值得沿用。OASIS/AgentSociety 主要价值是工程规模数据点。

---

## 6. 中国与东亚特定证据

1. **本领域的大规模系统有相当比例出自中国机构**，这对本项目有直接的工程与许可意义：
   - **AgentSociety**：清华大学 FIB Lab，Apache-2.0，Ray + MQTT，支持任意 litellm provider；算例含**北京**城市可持续性场景（200 agent）。
   - **OASIS**：Shanghai AI Lab 等联合，百万 agent，基座为**开放权重**的 Llama3-8b-instruct。
   - **CivRealm**：北京大学 / 北京邮电大学 / BIGAI，是目前与"文明模拟"主题最贴近的公开基准，且给出的是**负面结果**（LLM 与 RL agent 均无法在完整文明博弈中取得实质进展）。
2. **开放权重模型对本项目的可复现性是决定性的**。第 7 节会论证"重放靠 ledger 而非重调模型"，但**版本冻结**仍然重要：闭源 API 的模型会在你不知情时改变（Chen/Zaharia/Zou 记录的 84%→51%；Bisbee et al. 记录的 2023-06-25 更新后均值回归）。OASIS 用 Llama3-8b 自托管 24×A100 跑百万 agent，说明"自托管开放权重 + 权重哈希入 ledger"在本领域是**已被实践过的**可复现路径。对 civilization-sim，中文/东亚语境下 Qwen、DeepSeek 等开放权重模型是天然候选——但**本次检索未核实其具体版本、许可与价格**，Phase 1 需单独核实，不得凭记忆写入设计文档。
3. **文化偏差的方向性问题**：Santurkar et al. 的 OpinionQA 只覆盖 60 个**美国**人口群体；Bisbee et al. 用的是**美国** ANES；Wang et al. 的 3,200 人身份研究也在美国语境。**目前没有在本次检索中找到针对东亚/中国历史语境的等价评测。** 这意味着：我们对"LLM 在模拟古代东亚社会角色时会偏向什么"**没有量化依据**。这是本简报最重要的一处证据空白，也是把"文化"交给规则+世界内演化（而非交给 LLM 的先验）的额外理由——LLM 的文化先验极可能是"当代美式互联网文化 + 少量教科书式中国印象"，一旦让它决定制度或价值观走向，就会把这个先验注入成为世界的隐藏剧情树。
4. **地理与语言的实践含义**：世界内的文字、命名、称谓体系应当由世界自身演化并由规则层维护（词表、音变、构词规则），LLM 只在这些结构上做**填充**。让 LLM 自由命名会立刻产生可识别的汉语文化专名（"天命""科举""丞相"），从而把真实历史当成剧情模板，违反 MANDATE 的核心禁令。

---

4. **〔R2〕跨文化对齐偏差：第一轮说"没有找到"，第二轮找到了两条，但都不是针对古代东亚的，缺口只被部分填上。**
   - **Durmus et al. (2023), GlobalOpinionQA（Anthropic）**：用跨国民调（Pew Global Attitudes / World Values Survey 题目）构建评测集，度量模型回答与**按国家**分组的人类意见的相似度。核心发现："LLM responses tend to be more similar to the opinions of certain populations, such as those from the **USA, and some European and South American countries**"。用国籍 prompt 引导会让输出移动，但**有时移向的是刻板印象**；单纯把问题**翻译**成目标语言**不能**可靠地把输出移向该语言使用者的观点。
     - **对本项目的直接含义**：（a）"给 agent 写一句『你是一个公元前 2000 年黄河中游的部落首领』"这种引导，其效果**在实证上更接近"生成刻板印象"而不是"切换视角"**；（b）**用中文写 prompt 不会让模型变得更"东亚"**。因此中文 prompt 不能被当作文化保真度的手段。
   - **Ozkan (2026), arXiv:2607.18310（非 WEIRD persona 建模）**：以 **2,414 名真实 WVS 受访者**为底，让 N 个独立 LLM persona agent 复现该人群的回答分布，结果是系统性**分布坍缩**：集中度 0.36→0.69、熵 1.46→0.77、TVD 0.44、**85% 的场景发生坍缩**，且坍缩程度与场景结构可预测地相关（r=0.55）。行为任务里 persona **约 80% 默认选最便宜的选项**，收入档位只能把这个比例调制到 0%→7%→32%。Verbalized Sampling 能提升 7–10 个百分点，但会**矫枉过正**（SD-ratio 从 0.4–0.56 翻到 1.26–1.37）。
     - **证据等级 C**（单作者预印本、2026 年、本次未见独立复现），但它是**唯一一条直接针对非 WEIRD 人群**的量化证据，且方向与 Bisbee et al.（美国 ANES）完全一致：**均值尚可，分布坍缩**。两个独立人群、两套方法、同一方向 → 这个失败模式的**方向性**可以按 B 级对待，**幅度**按 C 级对待。
     - **对本项目最要命的一条**："persona 默认选最便宜选项 ~80%" 意味着 LLM 驱动的个体在缺乏强约束时会**收敛到同一个保守动作**。放到文明模拟里，就是所有部落都做同样的事、所有王朝都做同样的选择——**世界会变得没有历史**。这不是可以靠调温度解决的问题（见 AP12）。
5. **〔R2〕本项目特有的污染风险：真实历史术语会把真实历史模板一并召回（D 级推断，见第 10 节）。** 上述两条证据说明模型的文化先验是"美式当代 + 教科书式他者印象"。对中国史而言，这个先验**异常具体**：模型对"郡县""科举""均田""屯田""封禅"等词的关联极强。这与 Durmus 记录的"引导 → 刻板印象"是同一机制的延伸。**工程结论**：世界内的一切专名与制度名**必须由世界自己生成**（M?/第 9.1 节"允许"清单第 4 条），prompt 中禁止出现任何真实历史专名；描述制度时只能用**结构性描述**（"一种由中央任命、任期有限、不可世袭的地方长官职位"），不能用标签（"郡守"）。这条约束同时保护了 MANDATE"真实历史只作校准集"的要求。
6. **〔R2〕作者归属可核实的部分**：AgentSociety 出自清华 FIB Lab（Yong Li 组），OASIS 由上海 AI Lab 等联合完成（第一作者单位见论文），Gao et al. 的 LLM-ABM 综述（arXiv:2312.11970）同样出自清华 Yong Li 组。**即"大规模 LLM 社会模拟"这一子领域目前的工程重心在中国机构**，这对本项目意味着：可复用的工程实现（Ray/MQTT 调度、百万 agent 分片、开放权重基座）比欧美同类工作更多，但**评测口径与该组自身路线绑定较紧**，选用时要自己做基准。

## 7. 学界争议与未解决问题

1. **"LLM 能否作为人类被试的替代品"仍未定论。** 支持侧：Horton et al.（homo silicus，行为经济学经典实验可复现）、Argyle et al.（silicon sampling，"algorithmic fidelity"）、Aher et al.（Ultimatum Game / Garden Path / Milgram 三项成功复现）、Xie et al.（GPT-4 在信任博弈上与人类高度行为对齐）、Anthis et al.（认为方法有前景，识别出 5 个可解决的障碍）。反对侧：Bisbee et al.（48% 回归系数显著不同、32% 符号翻转、方差过低、跨月不可复现）、Santurkar et al.（与多个人口群体系统性错位，老年人与丧偶者代表性最差，且 steering 无法修复）、Wang et al.（对身份群体的错误刻画与扁平化）、Aher et al. 自己发现的 **hyper-accuracy distortion**（Wisdom of Crowds 实验中模型给出不真实的精确性）。
   - **本项目的立场**：争议的两侧其实不矛盾——**均值可用，分布不可用**。我们需要的恰恰是分布和尾部，所以这条路径对我们是**净负面**的。
2. **"多 agent 是否真的带来收益"存疑。** Cemri et al. 指出多 agent LLM 系统在流行基准上的收益"往往很小"，并给出 14 种失败模式（3 大类：系统设计问题、agent 间失配、任务验证缺失）。这直接质疑"多 agent 越多越好"的直觉。
3. **"涌现"这个词本身有争议。** Schaeffer et al. 论证所谓涌现能力大量是**指标选择的产物**（92% 的 BIG-Bench 涌现主张集中在 Multiple Choice Grade 与 Exact String Match 两类指标）。这对我们的启示不是"涌现不存在"，而是"**声称观察到涌现之前，必须先说清楚用什么指标、该指标是否连续**"——否则我们会把自己的度量伪影当成文明的涌现。
4. **Project Sid 的主张无法核实。** 代码与数据均未发布，未经同行评议。"AI 文明"这一最接近本项目目标的公开主张，恰恰是证据最弱的一条。
5. **非确定性的可修复程度存在分歧。** Thinking Machines 主张 batch-invariant kernel 可以完全消除温度 0 下的非确定性（1000/1000 完全一致），但这需要控制推理栈；使用第三方 API 时不可用。因此对我们而言这是一个"理论上可解、实践中不可依赖"的问题。
6. **格式约束与推理能力的权衡尚无定量最优解。** Tam et al. 证明存在退化，但不同任务、不同约束强度下的退化幅度没有通用公式。
7. **本项目独有的未解问题**：没有任何既有工作跑过"数千年"尺度。所有系统的最长跨度都在"数十模拟日"到"数百回合"量级（Smallville 2 天，CivRealm 数百回合）。**长时程下 LLM agent 的行为漂移、记忆污染、制度僵化速率，完全没有实证数据。** 这必须在 Phase 1 用我们自己的小规模长跑实验来测。

---

8. **〔R2〕Park et al. 2024 的"85%"到底是什么，以及它自己就是一个版本漂移的活例子。** v1（2024-11-15）标题为 *Generative Agent Simulations of 1,000 People*，摘要称 agent "replicate participants' responses on the General Social Survey **85% as accurately as participants replicate their own answers two weeks later**"——分母是**真人自身的两周 test–retest 一致性**，不是绝对准确率。到 v3（2026-06-28）论文**改了标题**（*LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals*），摘要数字也换成了 **83% / 82% / 86% vs 74% 人口统计基线**。
   - **争议点**：以"人类自身重测一致性"为分母是一种慷慨的归一化——人在两周后回答问卷本来就不稳定，这会把分母压低、把比值抬高。本轮**未检索到**对该指标的正式批评文献，因此这一条属于**方法论质疑而非已确立的学界争议**，标注为 C。
   - **对本项目的元教训**：一篇被广泛引用的论文，**两年内改了标题、改了核心数字**。我们如果在设计文档里写"Park 2024 说 85%"，一年后别人回去找会找不到那句话。→ 引用必须**锁版本号**（arXiv vN + 抓取日期），这与第 9.3 节"锁模型版本"是同一条纪律的两个面。
9. **〔R2〕"结构化输出会不会伤害推理"仍无定论，且本项目对它有硬需求。** Tam et al. (2024) 报告 JSON/XML 等格式约束越严、推理任务退化越大；本轮**未检索到**系统性的反驳文献（不能据此断言"没有反驳"，只能说本次没找到）。
   - **对本项目的两难**：我们**必须**要结构化输出（否则无法把 LLM 提案送进规则引擎、无法记账、无法重放），但结构化又可能削弱判断质量。
   - **可操作的折中**（B 级，源自 Tam et al. 的建议方向与 LLM-Modulo 的双向交互）：**先自由文本推理、再单独一次结构化抽取**（两段式），或在同一次响应里让"推理"字段是自由文本、只把**结论字段**受 schema 约束。绝不要把复杂权衡直接塞进一个深层嵌套的 JSON schema 里一次性产出。
10. **〔R2〕"LLM 是否偏好戏剧性"缺乏直接实证。** MANDATE 第 9 条要防的"模型为了戏剧性制造事件"，本轮**没有找到**任何直接测量该倾向的论文。能找到的只是三条**间接**证据链：typicality bias（偏好熟悉/典型文本，Verbalized Sampling 论文报告人类标注者 51.6–60.8% 偏好"典型"回答）、sycophancy（迎合用户预期）、以及叙事同质化（Doshi & Hauser：AI 辅助的故事**彼此更相似**）。
   - **结论**：把"戏剧化倾向"当作**已证实的失败模式**去引用是不诚实的（详见第 10 节 D 级条目）。但把"**不让 LLM 决定事件是否发生**"当作设计约束是**过度充分**地被上述三条证据支持的——因为无论模型的偏置是"戏剧化"还是"典型化"还是"迎合"，只要它有**任何**系统性偏置，让它决定事件发生与否都会把这个偏置注入成隐藏剧情树。**我们不需要先证明它偏向戏剧，才有理由不让它裁决。**

## 8. 反模式：本领域常见的错误建模方式（我们必须避免的）

### AP1. 让 LLM 裁决客观结果
- **表现**：问模型"这场战争谁赢了"、"这次改革成功了吗"、"这个国家能撑多久"。
- **为什么错**：LLM-as-judge 有已量化的 position bias（改顺序即可让弱者"赢" 66/80 局）、verbosity bias、self-preference bias（自我识别能力与自我偏好线性相关）。更根本的是它有叙事偏好——它会给出"故事上说得通"的结果，而不是"约束上算得出"的结果。
- **正确做法**：M1。任何 `Outcome` 必须是纯函数 `Resolve(state, intent, rng)`。

### AP2. 把 LLM 当作随机源来生成罕见事件
- **表现**：让模型"决定这一年是否发生瘟疫/发现青铜/出现先知"。
- **为什么错**：对齐训练系统性压缩尾部——Bisbee（合成数据方差显著低于真实）、Padmakumar & He（InstructGPT 显著降低多样性）、Mohammadi（熵下降、吸引子态）、Verbalized Sampling（typicality bias 51.6–60.8%）。让 LLM 掷骰子＝掷一枚被磨过的骰子。
- **正确做法**：M6。规则掷骰，LLM 事后解释。

### AP3. 每 tick 给每个 agent 调一次 LLM
- **表现**：Park 式全量 generative agent 架构直接放大到 10⁵ 实体 × 10⁴ tick。
- **为什么错**：算术上不可行（见第 9 节预算）；AgentSociety 在解决了消息总线与并发之后，仍把 LLM API 成本与 rate limit 列为剩余瓶颈。
- **正确做法**：M2（稀疏触发）+ M3（原型蒸馏）+ M4（多尺度频率）+ M5（缓存与策略固化）。

### AP4. 用"重跑一次"来复现历史
- **表现**：保存 prompt 和 seed，认为将来重跑能得到同一段历史。
- **为什么错**：温度 0 不保证确定性（零匹配比例 47.56%–75.76%）；根因是服务端 batch size 随负载变化导致内核非批不变；模型版本会漂移且不通知（84%→51%）。
- **正确做法**：M7 + 第 10 节的 ledger 方案。

### AP5. 用长上下文代替信息边界工程
- **表现**："把这个国家的全部历史塞进 1M 上下文，让模型自己判断该记住什么。"
- **为什么错**：Lost in the Middle 的 U 形曲线意味着中部信息被系统性忽略；成本按 token 线性增长；且这直接违反 MANDATE 第 4 条——把全局状态塞进 prompt 等于给了上帝视角。
- **正确做法**：M10。`View` 由规则层构造性投影，显式排序，短。

### AP6. 用纯 JSON schema 逼模型做复杂权衡
- **表现**：`{"decision": "war|peace|trade", "target": "..."}` 一步到位。
- **为什么错**：格式约束显著降低推理能力，且越严格降得越多（Tam et al.）。
- **正确做法**：M8 的两段式。

### AP7. 把"戏剧性"写进触发器或奖励
- **表现**：触发器里出现"距上次大事件已 N 年"、"该文明太平稳了"。
- **为什么错**：这就是 MANDATE 明令禁止的隐藏剧情树，只是伪装成了工程条件。
- **正确做法**：触发器只引用物理量、经济量、信息量。

### AP8. 把"agent 之间达成一致"当作社会共识的证据
- **表现**：观察到 LLM agent 群体收敛到同一意见，就宣称模拟出了"社会共识形成"。
- **为什么错**：Sharma et al. 记录了 5 个前沿助手一致存在的 sycophancy，且人类偏好数据本身偏好迎合性回答；Park et al. 自述指令微调导致 agent **过度合作**（违背自身利益也答应）；OASIS 观察到 agent 对负面社会线索的从众性**强于**真实人群。收敛可能只是谄媚与从众的产物。
- **正确做法**：冲突与分裂必须有规则侧的物质基础（资源竞争、继承规则、地理隔离），LLM 只在这些基础上产生说辞。同时把"一致性过高"作为一个**告警指标**纳入模拟健康度监控。

### AP9. 声称观察到"涌现"而不定义指标
- **为什么错**：Schaeffer et al. 的元分析显示 92% 的涌现主张集中在两类非连续指标上。
- **正确做法**：任何"涌现"结论必须配一个**连续**指标与其时间序列，且要展示该指标在指标变换下的稳健性。

### AP10. 把 Project Sid 的主张当作已确立事实引用
- **为什么错**：代码、数据、复现材料均未发布，未经同行评议。
- **正确做法**：作为假设来源，标注 C 级，不入校准集。

---

### 〔R2〕AP11. 在 prompt 里使用真实历史专名

写 "这个国家实行郡县制" 或 "他像商鞅一样变法"，等于把模型脑子里那一整套真实历史的因果、结局与评价一并召回。模型会**沿着它记得的剧本补全**，于是世界表面上是原创的，骨架却是真实历史的复读。
**替代做法**：世界内的一切专名由世界自己生成（LLM 只在"命名"这一受限职责下参与，且必须过查重与构词规则）；描述制度时用**结构性谓词**而非标签。
**证据**：Durmus et al. 的"引导 → 刻板印象"是同机制的实证；专名召回本身**本次未检索到针对性研究**，故整体标 **D 级（第 10 节）**。但它的**成本极低**（就是一条 prompt 禁用词表），而失败后果是整个项目的立项前提失效，属于典型的"便宜的保险"。

### 〔R2〕AP12. 用 persona prompt 冒充人口异质性，用调高 temperature 冒充多样性

给 10,000 个 agent 各写一段身份描述，然后指望它们的行为分布像真实人群——Ozkan 的实验直接否定了这一点：分布集中度 0.36→0.69、熵 1.46→0.77、**85% 的场景坍缩**，约 80% 的 persona 默认选同一个（最便宜的）选项。
**为什么调温度救不了**：温度改变的是**同一个分布**的采样锐度；坍缩问题是**分布本身**错了（众数错、方差错、尾部缺失）。把温度调高只会在错误的分布上采到更多噪声，得到"随机的错误"而不是"正确的多样性"。
**正确做法**：异质性必须来自**世界状态**（禀赋、地理、亲属、债务、创伤、信息可得性），由规则生成并作为**约束条件**喂给 LLM；LLM 只在这些约束下产生意图。即：**先有不同的处境，才有不同的人**，而不是先有不同的人设。

### 〔R2〕AP13. 只报告"看起来合理"，不报告成本、种子与模型版本

Kapoor et al. 对整个 agent 领域的批评（"needlessly complex and costly"、"a pervasive lack of reproducibility"）直接适用于我们自己。一次"跑出了很像样的历史"的实验，如果没有同时记录 **总 token 成本 / 随机种子 / 模型 ID 与版本 / ledger 哈希**，它在三个月后**不可复查也不可反驳**，等价于没做。
**红线**：长跑实验的产物必须包含一个 manifest（见 9.3 节），缺任一字段的实验结果**不得进入设计决策**。

## 9. 回答三个特别问题

### 9.1 LLM 在本项目中的职责清单

#### ✅ 允许（LLM 主导）

| 职责 | 理由（对应失败模式） |
|---|---|
| 生成人物**动机与意图提案**（结构化 Intent），供规则裁决 | Concordia 的 GM 切分是既有实践；CivRealm 证明 LLM 可以产生合理提案但无法保证长时程后果 |
| 生成**世界内的叙事**：史书、传说、宗教文本、诗歌、官方说辞、民间谣言 | 这是纯语言产物，不改变世界事实；MANDATE 第 9 条明确要求世界事实与历史叙事分离 |
| 生成**文化产物的内容**：仪式描述、教义条文、法律条文的措辞 | 同上。但**条文的效力参数**必须由规则解析成数值 |
| 对已发生事件生成**世界内行为者的解释与误解** | 事后解释不影响因果链，且误解本身是 MANDATE 第 9 条要求的功能 |
| 为规则生成的低概率事件**命名与叙述** | M6 |
| 组织/派系的**话语立场与说服文本** | 只影响信息传播的内容，效果由规则计算 |
| 离线：**叙事质量与信息边界审计**（LLM-as-judge，仅评估不干预） | 需位置随机化 + 双向打分（AP1/M9） |
| 离线：**为规则系统起草候选规则**，由人类审核后固化 | "用 LLM 生成规则再由规则执行"——生成期非确定性无害，因为产物是确定性代码 |

#### ❌ 禁止（LLM 绝不参与）

| 职责 | 理由（对应失败模式） |
|---|---|
| 决定**战争胜负、战役伤亡、围城结果** | AP1；MANDATE 第 5 条明文 |
| 决定**任何数值状态量**：人口、产量、价格、税收、兵力、疫病死亡率 | AP1 + hyper-accuracy distortion（Aher et al.：模型会给出不真实的精确数值） |
| 决定**罕见事件是否发生**（技术突破、灾害、疫病、暗杀成败、异端出现） | AP2；对齐模型系统性压缩尾部（四条独立证据） |
| 决定**国家兴亡、制度存续、革命是否成功** | AP1 + CivRealm 的长时程失败证据 |
| 充当**随机数发生器** | AP2 + 非确定性不可控（M7 的量化证据） |
| **裁决因果链**（"这件事是不是那件事导致的"） | 因果链必须由 `Resolve` 在执行时**同步写入**，而不是事后由 LLM 推断；事后推断必然产生看似合理的虚构（Park et al. 自述的"embellishment"） |
| 直接**读写世界状态**（无 `View` 投影、无 `Resolve` 裁决的任何路径） | MANDATE 第 4 条；一旦存在这样的旁路，信息边界就形同虚设 |
| 决定**时间推进**或 tick 的内容 | 世界钟必须是规则的 |
| 在**运行时**修改规则、参数或触发器 | 否则整条历史不可重算 |
| 生成**真实历史专名**（朝代名、真实人物、真实制度名） | MANDATE 核心禁令；需在结构化输出侧用词表白名单/黑名单硬约束 |

#### ⚠️ 受限（可用但必须有规则侧护栏）

| 职责 | 护栏 |
|---|---|
| 人物性格与偏好的初始化 | 从规则生成的特质向量出发，LLM 只做**文本化**，不改数值 |
| 组织内部的联盟/背叛倾向 | LLM 给倾向**排序**，规则把排序映射为概率并掷骰 |
| 谈判与外交的具体条款 | 条款必须落在预定义的条款类型空间内；违约与执行由规则判定 |
| 记忆的遗忘与重构 | 遗忘曲线由规则控制；LLM 只负责"记忆被重构成了什么内容" |

#### 〔R2〕对上面三张表的补充：一条可判定的切分判据，两条新增条目

**切分判据（取自 AgentSociety 的工程表述，比"客观/主观"更可操作）**：问一个问题——**这个量有没有一个已经被校准过的数学模型？**
- 有（重力模型选址、SIR 传播、Lanchester 交战、排队/运输、价格出清、人口生命表、载畜量）→ **规则**，LLM 连碰都不要碰。AgentSociety 原文的理由是 LLM "cannot guarantee absolute accuracy" 于数值计算，因此把这类任务 offload 给环境。
- 没有（一个人为什么背叛他的兄长、一个教派为什么分裂、一份诏书该怎么措辞）→ **LLM 提案 + 规则裁决**。
- 判据的好处：它是**可争论、可裁决**的。当有人主张"这件事该交给 LLM"时，反问"那你给我那个已校准的模型"，讨论就结束了。

**新增 ❌ 禁止**

| 职责 | 理由 |
|---|---|
| 用 **N 个独立 persona agent 直接生成人群的统计分布**（"给一万个 agent 各写一段身份，然后统计他们的选择"） | Ozkan (arXiv:2607.18310)：集中度 0.36→0.69、熵 1.46→0.77、TVD 0.44、**85% 场景坍缩**，约 80% 的 persona 默认选同一个最便宜选项。这条路在实证上是**坏掉的**，且坏的方向是"让世界失去多样性"，正中本项目要害（AP12） |
| 让 LLM **自我验证**自己的提案是否可行 | Kambhampati et al. (ICML 2024)：LLM "cannot, by themselves, do planning or **self-verification**"。可行性必须由规则侧的 `Resolve` 判定 |

**新增 ✅ 允许 / ⚠️ 受限**

| 职责 | 等级 | 护栏 |
|---|---|---|
| **起草制度 / 税法 / 军制的可执行 DSL 条文**（Eureka / Voyager 范式：LLM 写代码，规则引擎执行几十上百年） | ⚠️ 受限 | 条文必须通过静态校验（只能引用白名单状态量、必须全函数有界、不得含随机源）；必须带**执行折损参数**，且该参数由规则侧（吏治、距离、信息延迟、监察密度）决定而非由 LLM 写死；条文入库时记录作者 agent、动机、当时的世界状态（这就是"制度诞生"的因果链） |
| 输出**某一原型在某处境下各动作的概率分布** `p_α(k)`（AgentTorch 式） | ⚠️ 受限 | 采样由**我们自己的 PRNG** 完成（满足 MANDATE 第 6 条）；分布必须先在有真值的场景上做一次校准，且要监控其熵——Ozkan 显示未加干预时熵会塌，加了 Verbalized Sampling 又会**矫枉过正**（SD-ratio 0.4–0.56 → 1.26–1.37）。**熵本身要作为被监控的运行指标**，不能只看均值 |

**新增执行要求（来自 LLM-Modulo 的 "bi-directional"）**：规则侧否决一个 LLM 提案时，**必须把结构化的否决理由回灌**（如 `{rejected: insufficient_grain, need: 12000, have: 4300, deficit_years: 3}`）。理由有三：(1) 不回灌则 agent 会反复提同一个不可行方案，直接烧钱；(2) 回灌的理由本身就是因果链上的一条记录（"他想打仗，但粮不够，于是转而加税"）；(3) 这是把"信息边界"落实到位的地方——回灌的内容只能包含该 agent **本应知道**的信息（他知道自己缺粮，但未必知道邻国缺不缺）。

### 9.2 数千年模拟的 LLM 调用预算方案

**设定**（下列结构假设为本项目自定，属 D 级；单价与折扣为 A 级）：
- 目标跨度 3,000 模拟年；tick = 1 年（早期可 5 年/tick，晚期 1 年/tick），取 **3,000 tick**。
- 世界人口实体 10⁵–10⁷，全部由规则驱动。

**四层预算**：

| 层 | 实体数 | LLM 驱动方式 | 频率 | 每 tick 调用数 |
|---|---|---|---|---|
| L0 人口/生产/气候/疫病 | 10⁵–10⁷ | **无 LLM** | 每 tick | 0 |
| L1 家户/村落原型（M3） | 10⁴–10⁶ 聚成 ~200 原型 | 原型查询 + 缓存 | 每 20 tick 刷新，或 context 桶跳变时 | ~10 |
| L2 组织（政体/教团/行会） | 50–500 | 触发器驱动（M2） | 平均每 10 tick 一次 | ~20 |
| L3 具名人物 | 100–1,000 在世 | 触发器驱动 + 生涯上限 | 平均每 20 tick 一次 | ~20 |
| **合计** | | | | **~50 次 / tick** |

- 总调用数 ≈ 3,000 × 50 = **150,000 次**。
- 每次调用假设 2,000 输入 token（1,500 稳定前缀 + 500 局势）+ 300 输出 token。

**成本估算**（本项目算术，输入价与折扣为 A 级，token 假设为 D 级）：

| 方案 | 每次调用成本 | 15 万次总成本 |
|---|---|---|
| Haiku 4.5，无缓存无批处理 | 2000×$1e-6 + 300×$5e-6 = **$0.00350** | **$525** |
| Haiku 4.5 + prompt caching（1500 前缀命中，0.1×） | 1500×$0.1e-6 + 500×$1e-6 + 300×$5e-6 = **$0.00215** | **$323** |
| 上者 + Batch API（50%） | **$0.001075** | **$161** |
| Sonnet 5 + caching + batch | $0.00215 × 2 × 0.5 = **$0.00215** | **$323** |
| Opus 5 + caching + batch | $0.00215 × 5 × 0.5 = **$0.005375** | **$806** |

**结论：在上述结构下，跑完 3,000 年的 LLM 成本在数百美元量级，完全可行。** 成本不是瓶颈——**调用结构**才是。作为对照：若采用 AP3（每 tick 每具名人物一次调用，1,000 人 × 3,000 tick = 300 万次），同样单价下 Haiku+cache+batch 也要 **$3,225**，而 Opus 5 要 **$16,125**；若退化到 Park 式全量 agent（Lyfe 论文推得的 $5–50/agent/人类小时量级），任何规模都立刻不可行。

**分层模型选择建议**：
- L1 原型：Haiku 4.5（结构化、重复度高、缓存命中率高）。
- L2 组织：Sonnet 5。
- L3 关键人物的关键抉择（一生中屈指可数的几次）：Opus 5，`thinking: {type:"adaptive"}` + `output_config.effort` 按重要性分档。
- 注意：**缓存是模型作用域的**，跨模型无法复用缓存前缀；因此分层要按"稳定前缀族"划分，而不是按每次调用临时挑模型。

**缓存工程要点（直接决定上表能否成立）**：
- 前缀渲染顺序 `tools → system → messages`；把"世界常量 + 人格 + 文化 + 制度条文"放最前且**逐字节稳定**（禁止在 system 里写时间戳、tick 号、随机 id、未排序 JSON）。
- 用 `usage.cache_read_input_tokens` 做**持续断言**：集成测试里断言第二次相同请求 `cache_read_input_tokens > 0`。缓存失效是静默的，只表现为账单变高。
- tick 之间若间隔大于 5 分钟，考虑 1 小时 TTL（write 2×）或用 `max_tokens: 0` 的保活请求刷新计时器。

**无 LLM 时世界仍能运行（必须做到）**：
- 每个 LLM 决策点都必须有一个**规则默认策略** `default_policy(actor, view)`（例如：最大化预期粮食盈余、最小化外部威胁暴露、维持现状）。
- 系统提供三种运行模式：
  1. `MODE_FULL`：按预算调用 LLM。
  2. `MODE_REPLAY`：只读 ledger，不调用 LLM（第 9.3 节）。
  3. `MODE_HEADLESS`：完全不调用 LLM，全部走 `default_policy` + 已固化的制度策略（M5）。
- `MODE_HEADLESS` 的用途：参数校准（需要跑几百条历史线做敏感性分析时，绝不能每条都花钱）、回归测试、以及**验证世界内核本身是否自洽**——如果世界在 HEADLESS 下就崩溃或平庸化，问题在规则层，加 LLM 只会掩盖它。
- **设计红线**：任何在 `MODE_HEADLESS` 下会导致模拟无法推进的依赖，都是架构缺陷。

**〔R2〕对上述预算表的三条修正与加固**

1. **公式化的上限**：AgentTorch 给出的 `K × A`（K = 原型数，A = 需要 LLM 判断的动作类型数）应当作为**硬预算约束**写进调度器，而不是事后统计出来的数字。做法：调度器持有一个 per-tick 的 LLM 调用配额，超出则**降级到 `default_policy`** 并在 ledger 里记一条 `budget_exhausted`。这样"成本"变成了世界的一个**有记录的约束**，而不是一次意外的账单。
2. **必须加进预算模型的两个乘子（第一轮遗漏）**：
   - **工具系统提示开销**：只要请求带 `tools`，Opus 5 就额外注入 286（`auto`/`none`）或 406（`any`/`tool`）token，再加你自己的 schema 文本。对"输入 2,000 token"这种小请求，这是 **15–20% 的净增**。
   - **分词器变更**：官方文档明示 Claude 4.7 及之后模型 "produces approximately **30% more tokens** for the same text"。换代时即使 $/MTok 不变，账单也会涨约 30%。→ **预算模型必须以 `count_tokens` 实测为准，且每次换模型重新标定。**
   - 合并影响：第一轮表格中的成本应被视为**下界**，实际可能高 1.5 倍左右。结论（数百到一两千美元量级、成本不是瓶颈）不变。
3. **自托管路线的现实感锚点**：若改用开放权重模型自托管，OASIS 给的锚点是 **5 张 A100 / 10⁵ agent / 10 步 / 2 天**。把它换算到我们的 3,000 步：即使只有 10⁵ 个 LLM 驱动实体，也是 5×A100 × 600 天。**→ 自托管并不能解救"每 agent 每 tick 一次调用"的架构；它只是把美元换成了 GPU-天。** 唯一能解救的还是原型化 + 触发器化（把调用数从 `O(agents × ticks)` 降到 `O(K × A × ticks)`）。自托管真正的价值在**可复现性**（权重可哈希、版本可冻结），而不是省钱——这一点应写进 Phase 1 的取舍文档。

### 9.3 让 LLM 输出可重放

**核心命题**：LLM 不是一个可重现的函数，而是一个**外部熵源**。可重放性只能通过**持久化其输出**获得，不能通过"重新调用"获得。

**依据**：温度 0 非确定性（零匹配比例 47.56%–75.76%；Qwen3-235B 1000 次采样得 80 个不同 completion，第 102 token 后分叉）；根因是推理内核非 batch-invariant，而 batch size 随服务端负载变化；模型版本静默漂移（GPT-4 质数任务 84%→51%；Bisbee 观察到 2023-06-25 更新后的均值回归）。

**`llm_ledger` 设计**：

```
LlmCallRecord {
  call_id            : blake3(canonical_request_bytes || call_seq)   # 内容寻址
  call_seq           : u64          # 全局单调序号，与世界 tick 绑定
  world_tick         : u64
  actor_id           : ActorId
  purpose            : enum         # INTENT_PROPOSAL | NARRATIVE | EXPLANATION | ...
  # --- 请求侧（完整、逐字节） ---
  provider           : str          # "anthropic" | "self-hosted"
  model_id           : str          # "claude-haiku-4-5"
  model_fingerprint  : str          # API 返回的版本标识；自托管时为权重文件哈希
  params             : json         # temperature/top_p/effort/thinking/max_tokens/tools（规范化排序）
  prompt_blob_hash   : blake3       # 完整 prompt 存 blob store，ledger 只存哈希
  view_snapshot_hash : blake3       # 该次调用所依据的 View(actor,t)
  # --- 响应侧 ---
  response_blob_hash : blake3
  parsed_intent      : json         # 解析后的结构化 Intent（进入裁决的唯一部分）
  parse_status       : enum         # OK | REPAIRED | REJECTED_FELL_BACK_TO_DEFAULT
  usage              : {input, output, cache_read, cache_write}
  wall_clock_utc     : timestamp
  # --- 世界侧 ---
  rng_stream_id      : u64          # 该 Intent 被裁决时消耗的 RNG 流
  rng_counter_before : u128
  outcome_hash       : blake3       # Resolve 输出的哈希，用于重放校验
}
```

**运行模式与不变量**：

1. `MODE_FULL`：真调用；每次调用**先写 ledger 再应用**（write-ahead）。若进程在两者之间崩溃，重启时用 ledger 补齐。
2. `MODE_REPLAY`：`LlmClient` 被替换为 `LedgerClient`。查询键 = `(call_seq)`，并校验 `prompt_blob_hash` 与 `view_snapshot_hash` 是否与本次重算出的一致。
   - 一致 → 返回 ledger 中的响应，重放严格确定性。
   - **不一致 → 立即 abort，不允许"就近匹配"**。不一致意味着规则层或世界状态发生了变化，这正是我们要检测的东西，而不是要掩盖的东西。
3. `MODE_COUNTERFACTUAL`（反事实实验，MANDATE 第 6 条）：从某个 tick 分叉。分叉点**之前**的 `call_seq` 走 ledger；分叉点之后，凡 `view_snapshot_hash` 未变的调用继续复用 ledger（这让"改动一件小事"的实验成本极低），一旦 View 改变则必须真调用并写入**新的分支 ledger**。
   - ledger 因此是**按世界线分支的 append-only 结构**（内容寻址 + 分支指针），与 git 的对象模型同构。

**RNG 的对称处理**：
- 每个 `(subsystem, entity_id, tick)` 拥有独立的 counter-based RNG 流（如 Philox/ChaCha），从全局 master seed 派生。**禁止使用全局共享的顺序 RNG**——否则任何一处调用次数的变化都会让下游全部漂移，反事实实验将无法隔离变量。
- 这与 ledger 的作用是对称的：规则侧的随机性由 counter-based PRNG 保证可重现，LLM 侧的"随机性"由 ledger 保证可重现。

**版本漂移的处理**：
- `model_fingerprint` 变化时，系统必须在日志里打**显式断点标记**，并禁止把断点前后的历史当作同一实验条件比较。
- 长期严肃实验建议用**自托管开放权重模型**并把权重文件哈希写入 `model_fingerprint`（OASIS 用 Llama3-8b + 24×A100 跑百万 agent 是该路径的可行性证据）。这样"模型"也成为可版本化的资产。
- 若必须用闭源 API：把整个 ledger 视为**唯一的事实来源**，明确接受"这段历史无法从模型重新生成，只能从 ledger 回放"。这在本项目里是可接受的——MANDATE 要求的是可**重放**与可**追溯**，不是可**重新生成**。

**因果链的写入时机**：
- `Resolve` 在产生 `Outcome` 的同时**同步写入因果边** `(cause_event_id, effect_event_id, mechanism_id, weight)`。因果链是裁决的副产品，不是事后由 LLM 推断的解释。
- LLM 产出的 `freeform_rationale` 存入 ledger 但**标记为"世界内行为者的自述动机"**，与客观因果边分属两张表。数百年后查询"为什么这个国家会灭亡"时，可以同时返回客观因果链与当时人的自述理由，并显示二者的差异——这正好实现 MANDATE 第 9 条。

---

## 10. 无来源判断（D 级，LLM 常识，不得当作历史规律）

以下判断在本次检索中**未找到文献支撑**，属于为了让项目能推进而做的工程假设，须在 Phase 1 用自建实验检验：

1. 第 9.2 节四层预算表中的**实体数、触发频率、每 tick ~50 次调用**这一结构，完全是本项目设定，没有任何文献依据。唯一有实证支撑的是"必须做原型蒸馏"（AgentTorch）与"必须降低高层决策频率"（Lyfe）这两条定性原则。
2. 每次调用 **2,000 输入 / 300 输出 token** 的假设，来自我对结构化 Intent prompt 的经验估计，无来源。真实值须在 Phase 1 用 `count_tokens` 实测。
3. 触发器集合（资源缺口、合法性阈值、边界接触、继承危机、技术阈值、外部冲击）是我基于历史社会学常识列的，**不是**从任何模型或文献推出的。它们本身就是一种理论承诺，需要在第 3 阶段与政治学/历史学简报交叉校验。
4. "具名人物一生 LLM 调用 ≤ 200 次"是我为控制成本随手设的上限，没有依据说明这个数量足以维持人物一致性。
5. "缓存键用离散桶（资源缺口 5 档、威胁 4 档、合法性 4 档）"的分档数完全是任意的。
6. 把"策略固化"等同于"制度诞生"是一个**理论主张**，不是经验发现。它在概念上很吸引人（制度＝被固化的、可继承的决策规则），但没有文献支持这种映射是历史学上恰当的。
7. "一致性过高应作为模拟健康度告警指标"（AP8 的正确做法）是我的推论，阈值无依据。
8. Lyfe Agents 的 10–100 倍成本比推出的"Park 式约 $5–50/agent/人类小时"是我的算术外推，Park 论文本身未给出成本数字。
9. 分层模型选择（L1 Haiku / L2 Sonnet / L3 Opus）没有对比实验支撑，纯属按价格与任务复杂度的直觉分配。
10. 关于"LLM 的文化先验是当代美式互联网文化"（第 6 节第 3 点）的具体刻画：**方向性有 Santurkar/Bisbee/Wang 的美国语境证据支撑，但"东亚语境下会如何偏"这一点在本次检索中完全没有证据**，我的描述属于推断。
11. `llm_ledger` 的具体字段设计、内容寻址方案、分支模型与 git 的类比，都是我的工程设计，无文献来源（尽管 write-ahead logging 与 counter-based PRNG 本身是成熟技术）。

---

12. **〔R2〕"LLM 有戏剧化偏好、会为了戏剧性制造事件"**——MANDATE 第 9 条预设的这个失败模式，本次两轮检索都**没有找到任何直接测量它的文献**。能找到的只有 typicality bias / sycophancy / 叙事同质化三条间接证据，它们指向的是"**趋同、迎合、典型化**"，严格说与"戏剧化"甚至方向相反（真实历史的戏剧性事件恰恰是**非典型**的）。
    - 我的判断（D 级）：**LLM 更可能让世界变得平淡而不是狗血**——它会把所有王朝写成同一个王朝，而不是编出精彩的宫斗。如果这个判断成立，我们要防的主要风险应从"抑制戏剧性"改成"**保证异质性与尾部**"，两者的工程手段完全不同（前者是加约束，后者是把尾部事件的生成权交给规则侧的重尾分布）。
    - **这条必须在 Phase 1 用实验判定**：跑两组小规模长跑（LLM 驱动 vs 规则驱动），比较事件类型分布的熵与尾部厚度。在实验做出来之前，**不要在任何设计文档里断言 LLM"倾向戏剧化"**。
13. **〔R2〕"真实历史专名会召回真实历史剧本"（AP11）**：机制上与 Durmus et al. 记录的"国籍引导 → 刻板印象"同源，但**没有针对性研究**。属 D 级。缓解措施（prompt 专名禁用表 + 结构化谓词描述制度）成本极低，建议无条件采纳，但不得把它写成"已知规律"。
14. **〔R2〕把 Eureka / Voyager 的"LLM 写代码→规则执行"直接映射到"LLM 写制度 DSL→规则引擎执行几十年"**：范式是 B 级（有成功先例），但**这个具体映射（制度＝可执行代码）没有任何文献做过**。风险在于制度的真实运作包含大量非形式化的执行偏差（阳奉阴违、地方变通），一段确定性代码会把它建模成完美执行。须在 DSL 里显式留出"执行折损"参数，且该参数应由规则侧（吏治、监察、距离、信息延迟）决定，不由 LLM 决定。
15. **〔R2〕第 4.2 节的价格与倍率是 A 级，但用它们算出的任何总成本都是 D 级**，因为 token 用量假设是 D 级。报告成本时必须写成"在 X token/调用、Y 调用/tick 的假设下"，不得写成"跑完 3000 年要 $N"。

## 11. 检索覆盖说明

- **WebSearch 在本会话开始时配额即已耗尽（200/200）**，因此本次无法做关键词广度检索。策略改为：从我的先验中列出候选文献标识符，然后用 WebFetch 逐条访问 arXiv 摘要页、alphaxiv、GitHub README、Cambridge Core 进行**逐条核验**。凡核验通过的，本简报按原文引用；凡未核验的，一律标注。
- **这一策略的系统性偏差**：它只能找到我先验里已有的文献，**无法发现 2025–2026 年我不知道的新工作**。特别是：2025 年后的 LLM 社会模拟综述、LLM agent 长时程漂移的实证研究、以及任何针对东亚/中文语境的 silicon sampling 评测，本次检索**完全没有覆盖**。这是本简报最大的缺口。
- **访问失败**：Semantic Scholar Graph API 全程返回 429；dl.acm.org 返回 403；arxiv.org 在若干次请求后开始 ECONNRESET（改用 alphaxiv 镜像绕过）；ar5iv 全文页始终无法访问，因此 Park et al. 2023 的 Limitations 细节是经由 alphaxiv 的**论文概览页**（AI 生成摘要）获得的，属二手，已在正文标注。
- **付费墙**：Political Analysis（Bisbee et al.）只读到 Cambridge Core 的摘要与关键数字页，未读全文。
- **本次未能核实**：Qwen / DeepSeek 等中国开放权重模型的具体版本、许可与价格；OASIS / AgentTorch / MAST-Data / OpinionQA / CivRealm 的具体开源许可。Phase 1 需补。

---

### 〔R2〕第二轮检索覆盖说明（2026-09-10）

- **前提相同**：WebSearch 配额在本会话开始时即已耗尽（200/200），因此第二轮同样无法做关键词广度检索。
- **本轮改用的检索面**（与第一轮不同，这是它能补出新东西的原因）：
  1. **arXiv 全文检索 UI**（`arxiv.org/search/?searchtype=all&query=...`）——这个端点在 `/abs/` 被限流时**仍然可用**，且返回带摘要片段的结果列表。本轮靠它发现了第一轮完全没有的 Ozkan (2607.18310)、并核实了 Kapoor、Perez、Xie、Gao 等条目的完整摘要。**这是本轮最有价值的方法学发现，记录下来供后续简报复用。**
  2. **arXiv HTML 版**（`arxiv.org/html/<id>vN`）——比 `/abs/` 摘要页多出正文数字。OASIS 的 "five A100 / 100,000 users / 10 steps / two days"、AgentTorch 的 `K×A` 公式、AgentSociety 的重力模型与 offloading 原话，都来自这里。**PDF 路径不可用**（`arxiv.org/pdf/...` 对这几篇均超出 10MB 抓取上限）。
  3. **GitHub Contents API**（`api.github.com/repos/<o>/<r>/contents/`）——用来**证否**"代码已发布"这类主张。`altera-al/project-sid` 仓库下只有三个文件：`2024-10-31.pdf`（21,270,194 B）、`README.md`（1,999 B）、`visual_abstract.png`（8,215,703 B），**没有目录、没有代码、没有 LICENSE**。这比读 README 得出的结论强得多。
  4. **GitHub raw 源码**——Smallville 的检索常数（`gw=[0.5,3,2]`、`n_count=30`、`recency_decay=0.995`、`importance_trigger_max=150` 等）来自 `retrieve.py` 与 `scratch.json`，**是被实际执行过的值**，比论文正文更可靠。**建议把"读实现而非读论文"作为本项目参数抽取的默认策略。**
  5. **Europe PMC REST API**（`ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:"..."&resultType=core`）——绕开 Science / Nature / Wiley 的 403，成功取到 Cicero (Science 2022)、Doshi & Hauser (Science Advances 2024)、Binz & Schulz (PNAS 2023)、Dillion et al. (TiCS 2023) 的完整书目与摘要。**这是本轮第二个值得复用的方法。**
  6. **PMLR**（`proceedings.mlr.press/vNNN/...`）、**ACL Anthology**（`aclanthology.org/...`）——取到 Aher et al. (ICML 2023, PMLR 202:337–371)、Kambhampati et al. (ICML 2024, PMLR 235:22895–22907)、Liu et al. (TACL 2024, 12:157–173, doi:10.1162/tacl_a_00638) 的正式版书目。
  7. **platform.claude.com 官方定价页**——A 级价格数据，见 4.2 节。
- **本轮访问失败 / 被挡**：`science.org`（403）、`nature.com`（登录重定向）、`onlinelibrary.wiley.com`（403）、`dl.acm.org`（403）、`openreview.net`（浏览器验证页）、Semantic Scholar Graph API（全程 429）、`export.arxiv.org` API（持续 ECONNRESET）、`huggingface.co/papers`（间歇 ECONNRESET）。`arxiv.org/abs/` 在约 10 次请求后开始间歇性 ECONNRESET，恢复不规律。
- **本轮仍未覆盖（真实缺口，不要假装它被覆盖了）**：
  1. **没有任何针对古代 / 前现代东亚语境的 LLM 社会模拟评测**。Durmus 的 GlobalOpinionQA 与 Ozkan 的 WVS 研究都是**当代**人群。"LLM 扮演公元前的黄河流域首领会怎样偏"，**没有任何数据**。
  2. **没有任何跨越"数百模拟步"以上的 LLM agent 长时程实证**。Smallville 2 天、OASIS 10 步、CivRealm 数百回合。**千年尺度的行为漂移、记忆污染、制度僵化速率，全领域空白。**
  3. **没有找到"把 LLM 决策蒸馏成可复用策略"的系统性实证**（只有 AgentTorch 的原型法与 Eureka/Voyager 的代码生成范式两个侧面）。语义缓存的命中率/质量损失曲线**没有可引用的量化结果**。
  4. **Tam et al. 的反驳文献**：本次没找到，但不能断言不存在。
  5. **中国开放权重模型（Qwen / DeepSeek 等）的版本、许可与自托管成本**：两轮均未核实，Phase 1 必须单独做。

## 12. 参考文献

**✅ = 本次检索中直接访问并核验过（标注核验途径）；⚠️ = 仅经二手页面核验**

1. ✅ Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). *Generative Agents: Interactive Simulacra of Human Behavior.* arXiv:2304.03442 (v1 2023-04-07, v2 2023-08-06). 〔arxiv.org/abs 摘要页核验〕 **[已核验]**（DataCite/arXiv DOI 10.48550/arxiv.2304.03442：题名、6 位作者、2023 年、v2 均一致）
2. ⚠️ 同上，Limitations / 失败模式细节经 alphaxiv 概览页（AI 生成摘要）核验，未读到原文逐字引用。
3. ✅ github.com/joonspk-research/generative_agents — README（成本警告、replay/demo、存档机制）核验。
4. ✅ Park, J. S., Zou, C. Q., Kamphorst, J., Egan, N., Shaw, A., Hill, B. M., Cai, C., Morris, M. R., Liang, P., Willer, R., & Bernstein, M. S. (2024). *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals*（原题 *Generative Agent Simulations of 1,000 People*）. arXiv:2411.10109. 〔arxiv.org/abs 核验〕 **[已核验]**（DataCite 显示当前题名确为 *LLM Agents Grounded in Self-Reports…*，11 位作者一致，v3，2024 年首发）
5. ✅ Vezhnevets, A. S., Agapiou, J. P., Aharon, A., Ziv, R., Matyas, J., Duéñez-Guzmán, E. A., Cunningham, W. A., Osindero, S., Karmon, D., & Leibo, J. Z. (2023). *Generative agent-based modeling with actions grounded in physical, social, or digital space using Concordia.* arXiv:2312.03664. 〔arxiv.org/abs 核验〕 **[已核验]**（DataCite：题名与 10 位作者逐一一致，2023 年 v2）
6. ✅ github.com/google-deepmind/concordia — README（Game Master 裁决语义）、Apache-2.0 许可核验。
7. ✅ Altera.AL, Ahn, A., Becker, N., Carroll, S., Christie, N., Cortes, M., Demirci, A., Du, M., Li, F., Luo, S., Wang, P. Y., Willows, M., Yang, F., & Yang, G. R. (2024). *Project Sid: Many-agent simulations toward AI civilization.* arXiv:2411.00114. 〔arxiv.org/abs 核验〕 **[已核验]**（DataCite：题名与作者列表一致，2024 年 v1；仓库内容经 GitHub Contents API 于 2026-09-10 复核，确为 PDF+README+PNG 三文件、无代码无 LICENSE）
8. ✅ github.com/altera-al/project-sid — README 核验：**仅含技术报告 PDF、视觉摘要图与视频，无代码无数据**。
9. ✅ Yang, Z., Zhang, Z., Zheng, Z., Jiang, Y., Gan, Z., Wang, Z., Ling, Z., Chen, J., Ma, M., Dong, B., Gupta, P., Hu, S., Yin, Z., Li, G., Jia, X., Wang, L., Ghanem, B., Lu, H., Lu, C., Ouyang, W., Qiao, Y., Torr, P., & Shao, J. (2024). *OASIS: Open Agent Social Interaction Simulations with One Million Agents.* arXiv:2411.11581 (v1 2024-11-18, v5 2025-03-23). 〔arxiv.org/abs 核验；量化细节经 alphaxiv 概览页核验 ⚠️〕 **[已核验]**（DataCite：题名与 23 位作者一致，2024 年 v5。**注意**：正文 27.0 vs 24 张 A100 的冲突本轮未能复核——arxiv.org 在本次核验环境中不可达，仅核验了书目而非正文数字）
10. ✅ Piao, J., Yan, Y., Zhang, J., Li, N., Yan, J., Lan, X., Lu, Z., Zheng, Z., Wang, J. Y., Zhou, D., Gao, C., Xu, F., Zhang, F., Rong, K., Su, J., & Li, Y. (2025). *AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents Advances Understanding of Human Behaviors and Society.* arXiv:2502.08691. 〔arxiv.org/abs 核验；基础设施数字经 alphaxiv 概览页核验 ⚠️〕 **[已核验]**（Semantic Scholar：题名、16 位作者、2025 年一致）
11. ✅ github.com/tsinghua-fib-lab/agentsociety — README（清华 FIB Lab、Apache-2.0、Ray、litellm）核验。
12. ✅ Chopra, A., Kumar, S., Giray-Kuru, N., Raskar, R., & Quera-Bofarull, A. (2024). *On the limits of agency in agent-based models.* arXiv:2409.10568. 〔alphaxiv 核验〕 **[已核验]**（Semantic Scholar：题名与 5 位作者一致，2024 年；另注该条已被 AAMAS 系列收录，非纯预印本）
13. ✅ Kaiya, Z., Naim, M., Kondic, J., Cortes, M., Ge, J., Luo, S., Yang, G. R., & Ahn, A. (2023). *Lyfe Agents: Generative agents for low-cost real-time social interactions.* arXiv:2310.02172. 〔alphaxiv 核验〕
14. ✅ Qi, S., Chen, S., Li, Y., Kong, X., Wang, J., Yang, B., Wong, P., Zhong, Y., Zhang, X., Zhang, Z., Liu, N., Wang, W., Yang, Y., & Zhu, S.-C. (2024). *CivRealm: A Learning and Reasoning Odyssey in Civilization for Decision-Making Agents.* arXiv:2401.10568. 〔alphaxiv 核验〕
15. ✅ Wang, G., Xie, Y., Jiang, Y., Mandlekar, A., Xiao, C., Zhu, Y., Fan, L., & Anandkumar, A. (2023). *Voyager: An Open-Ended Embodied Agent with Large Language Models.* arXiv:2305.16291. 〔arxiv.org/abs 核验〕
16. ✅ Horton, J. J., Filippas, A., & Manning, B. S. (2023/2026). *Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?* arXiv:2301.07543 (v1 2023-01-18, v2 2026-02-26). 〔arxiv.org/abs 核验〕
17. ✅ Argyle, L. P., Busby, E. C., Fulda, N., Gubler, J., Rytting, C., & Wingate, D. (2022). *Out of One, Many: Using Language Models to Simulate Human Samples.* arXiv:2209.06899. 〔arxiv.org/abs 核验〕
18. ✅ Santurkar, S., Durmus, E., Ladhak, F., Lee, C., Liang, P., & Hashimoto, T. (2023). *Whose Opinions Do Language Models Reflect?* arXiv:2303.17548. 〔arxiv.org/abs 核验〕
19. ✅ Bisbee, J., Clinton, J. D., Dorff, C., Kenkel, B., & Larson, J. M. (2024). *Synthetic Replacements for Human Survey Data? The Perils of Large Language Models.* Political Analysis, 32(4), 401–416. doi:10.1017/pan.2024.5. 〔Cambridge Core 摘要与结果页核验〕 **[已核验]**（Crossref 10.1017/pan.2024.5：题名、5 位作者、Political Analysis 32(4):401–416 完全一致）
20. ✅ Wang, A., Morgenstern, J., & Dickerson, J. P. (2024/2025). *Large language models that replace human participants can harmfully misportray and flatten identity groups.* arXiv:2402.01908. 〔arxiv.org/abs 核验〕
21. ✅ Aher, G., Arriaga, R. I., & Kalai, A. T. (2022/2023). *Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies.* ICML 2023 (oral). arXiv:2208.10264. 〔arxiv.org/abs 核验〕
22. ✅ Xie, C., Chen, C., Jia, F., Ye, Z., Lai, S., Shu, K., Gu, J., Bibi, A., Hu, Z., Jurgens, D., Evans, J., Torr, P., Ghanem, B., & Li, G. (2024). *Can Large Language Model Agents Simulate Human Trust Behavior?* NeurIPS 2024. arXiv:2402.04559. 〔arxiv.org/abs 核验〕
23. ✅ Anthis, J. R., Liu, R., Richardson, S. M., Kozlowski, A. C., Koch, B., Evans, J., Brynjolfsson, E., & Bernstein, M. (2025). *LLM Social Simulations Are a Promising Research Method.* arXiv:2504.02234. 〔arxiv.org/abs 核验〕
24. ✅ Sharma, M., Tong, M., Korbak, T., Duvenaud, D., Askell, A., Bowman, S. R., Cheng, N., Durmus, E., Hatfield-Dodds, Z., Johnston, S. R., Kravec, S., Maxwell, T., McCandlish, S., Ndousse, K., Rausch, O., Schiefer, N., Yan, D., Zhang, M., & Perez, E. (2023). *Towards Understanding Sycophancy in Language Models.* arXiv:2310.13548. 〔arxiv.org/abs 核验〕
25. ✅ Padmakumar, V., & He, H. (2023). *Does Writing with Language Models Reduce Content Diversity?* ICLR 2024. arXiv:2309.05196. 〔arxiv.org/abs 核验〕
26. ✅ Mohammadi, B. (2024). *Creativity Has Left the Chat: The Price of Debiasing Language Models.* arXiv:2406.05587. 〔arxiv.org/abs 核验〕
27. ✅ Zhang, J., Yu, S., Chong, D., Sicilia, A., Tomz, M. R., Manning, C. D., & Shi, W. *Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity.* arXiv:2510.01171. 〔alphaxiv 核验；该页显示的提交日期为 2026-07-15，可能为修订日期，引用时须复核〕
28. ✅ Sclar, M., Choi, Y., Tsvetkov, Y., & Suhr, A. (2023). *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting.* arXiv:2310.11324. 〔arxiv.org/abs 核验〕
29. ✅ Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2023). *Lost in the Middle: How Language Models Use Long Contexts.* arXiv:2307.03172. 〔arxiv.org/abs 核验〕
30. ✅ Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., & Stoica, I. (2023). *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.* arXiv:2306.05685. 〔arxiv.org/abs 核验〕
31. ✅ Wang, P., Li, L., Chen, L., Cai, Z., Zhu, D., Lin, B., Cao, Y., Liu, Q., Liu, T., & Sui, Z. (2023). *Large Language Models are not Fair Evaluators.* arXiv:2305.17926. 〔arxiv.org/abs 核验〕
32. ✅ Panickssery, A., Bowman, S. R., & Feng, S. (2024). *LLM Evaluators Recognize and Favor Their Own Generations.* arXiv:2404.13076. 〔arxiv.org/abs 核验〕
33. ✅ Tam, Z. R., Wu, C.-K., Tsai, Y.-L., Lin, C.-Y., Lee, H.-y., & Chen, Y.-N. (2024). *Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models.* arXiv:2408.02442. 〔arxiv.org/abs 核验；具体退化数值未在摘要页给出，需读全文〕
34. ✅ Chen, L., Zaharia, M., & Zou, J. (2023). *How Is ChatGPT's Behavior Changing over Time?* arXiv:2307.09009. 〔arxiv.org/abs 核验〕
35. ✅ Ouyang, S., Zhang, J. M., Harman, M., & Wang, M. (2023/2024). *An Empirical Study of the Non-determinism of ChatGPT in Code Generation.* arXiv:2308.02828. 〔arxiv.org/abs 核验〕
36. ✅ Thinking Machines Lab. *Defeating Nondeterminism in LLM Inference.* thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ 〔直接访问核验；**非同行评议博客**，作者署名未在本次抓取中确认，引用时须复核作者〕 **[已修正: Horace He (in collaboration with others at Thinking Machines) (2025-09-10). *Defeating Nondeterminism in LLM Inference.* Thinking Machines Lab blog.]**（本轮直接抓取原文：作者署名为 Horace He，发表日 2025-09-10；正文核对无误——Qwen3-235B-A22B-Instruct-2507、温度 0 采样 1000 次得 **80 个不同 completion**、前 102 token 相同、第 103 token 分叉、启用 batch-invariant kernel 后 1000 次完全一致；"2.1×"实为 vLLM default 26 s → 未优化确定性 55 s 的换算，改进注意力核后为 42 s，引用时应写明这是换算值而非原文给出的倍数）
37. ✅ Kapoor, S., Stroebl, B., Siegel, Z. S., Nadgir, N., & Narayanan, A. (2024). *AI Agents That Matter.* arXiv:2407.01502. 〔arxiv.org/abs 核验〕
38. ✅ Cemri, M., Pan, M. Z., Yang, S., Agrawal, L. A., Chopra, B., Tiwari, R., Keutzer, K., Parameswaran, A., Klein, D., Ramchandran, K., Zaharia, M., Gonzalez, J. E., & Stoica, I. (2025). *Why Do Multi-Agent LLM Systems Fail?* arXiv:2503.13657. 〔alphaxiv 核验〕
39. ✅ Schaeffer, R., Miranda, B., & Koyejo, S. (2023). *Are Emergent Abilities of Large Language Models a Mirage?* arXiv:2304.15004. 〔alphaxiv 核验〕
40. ✅ github.com/zilliztech/GPTCache — README（语义缓存、"10x cost / 100x speed" 营销主张、MIT 许可）核验。**营销主张，非同行评议。**
41. ✅ Anthropic API 定价与 prompt caching 语义（模型 ID、$/MTok、cache read 0.1×、cache write 1.25×/2×、Batches 50%、前缀渲染顺序 `tools→system→messages`）。来源：本机 `claude-api` skill 的官方缓存表（缓存日期 2026-06-24）与 `shared/prompt-caching.md`。

**未在本次检索中核验、仅凭记忆提及的**：无。本简报正文中出现的每一条文献主张都对应上表中的一次实际抓取；凡属二手（alphaxiv 概览页）或营销材料的，均已就地标注。

---

### 〔R2〕第二轮新增 / 补强的参考文献（42–59，均为本轮直接抓取核验）

42. ✅ Meta Fundamental AI Research Diplomacy Team (FAIR), Bakhtin, A., Brown, N., Dinan, E., et al. (2022). *Human-level play in the game of Diplomacy by combining language models with strategic reasoning.* **Science, 378(6624), 1067–1074.** doi:10.1126/science.ade9097.〔Europe PMC REST 核验；science.org 本身 403〕 **[已核验]**（Europe PMC + Crossref 10.1126/science.ade9097：Science 378(6624):1067–1074, 2022，团队署名一致）
43. ✅ Kambhampati, S., Valmeekam, K., Guan, L., Verma, M., Stechly, K., Bhambri, S., Saldyt, L. P., & Murthy, A. B. (2024). *Position: LLMs Can't Plan, But Can Help Planning in LLM-Modulo Frameworks.* **ICML 2024, PMLR 235:22895–22907.**〔PMLR 核验〕 **[已核验]**（PMLR 页面：题名与 PMLR 235:22895–22907 完全一致）
44. ✅ Ma, J., Liang, W., Wang, G., Huang, D.-A., Bastani, O., Jayaraman, D., Zhu, Y., Fan, L., & Anandkumar, A. (2023). *Eureka: Human-Level Reward Design via Coding Large Language Models.*〔eureka-research.github.io 项目页核验；**venue 与最终发表版本本次未核实**，83%/52% 为项目页自述数字〕
45. ✅ Durmus, E., Nguyen, K., Liao, T. I., Schiefer, N., Askell, A., Bakhtin, A., Chen, C., Hatfield-Dodds, Z., Hernandez, D., Joseph, N., Lovitt, L., McCandlish, S., Sikder, O., Tamkin, A., Thamkul, J., Kaplan, J., Clark, J., & Ganguli, D. (2023). *Towards Measuring the Representation of Subjective Global Opinions in Language Models.* arXiv:2306.16388（v1 2023-06-28，修订 2024-04-12）.〔arXiv 摘要页核验〕 **[已核验]**（DataCite：题名与 18 位作者一致，2023 年 v2）
46. ✅ Ozkan, G. (2026). *Distribution-First Population Simulation: Collapse, Calibration, and Recall in Non-WEIRD LLM Persona Modeling.* arXiv:2607.18310（2026-07-17）.〔arXiv 摘要页核验〕**单作者预印本，未见同行评议或独立复现 → C 级。** **[已核验，但证据等级不变]**（DataCite 确认 arXiv:2607.18310 存在，单作者 Gurkan Ozkan，题名一致；**注**：DataCite 记录的登记时间为 2026-07-22，与正文写的 2026-07-17 有数日出入。仍为单作者预印本、无独立复现，C 级不变）
47. ✅ Doshi, A. R., & Hauser, O. P. (2024). *Generative AI enhances individual creativity but reduces the collective diversity of novel content.* **Science Advances, 10.** doi:10.1126/sciadv.adn5290.〔Europe PMC REST 核验〕
48. ✅ Kirk, R., Mediratta, I., Nalmpantis, C., Luketina, J., Hambro, E., Grefenstette, E., & Raileanu, R. (2023/2024). *Understanding the Effects of RLHF on LLM Generalisation and Diversity.* arXiv:2310.06452（v2 2024-01-03）。核心结论："RLHF generalises better than SFT to new inputs, particularly as the distribution shift between train and test becomes larger" 但 "significantly reduces output diversity compared to SFT"。〔arXiv 摘要页核验〕
49. ✅ Binz, M., & Schulz, E. (2023). *Using cognitive psychology to understand GPT-3.* **PNAS, 120(6).** doi:10.1073/pnas.2218523120。与本项目相关的三条：对 vignette 任务的**微小改动**极为敏感；**没有**定向探索（directed exploration）的证据；**因果推理表现差**。〔Europe PMC REST 核验〕
50. ✅ Dillion, D., Tandon, N., Gu, Y., & Gray, K. (2023). *Can AI language models replace human participants?* **Trends in Cognitive Sciences, 27(7).** doi:10.1016/j.tics.2023.04.008.〔Europe PMC REST 核验〕
51. ✅ Gao, C., Lan, X., Li, N., Yuan, Y., Ding, J., Zhou, Z., Xu, F., & Li, Y. (2023). *Large Language Models Empowered Agent-based Modeling and Simulation: A Survey and Perspectives.* arXiv:2312.11970（2023-12-19）.〔arXiv 全文检索页核验〕
52. ✅ Perez, J., Léger, C., Ovando-Tellez, M., Foulon, C., Dussauld, J., Oudeyer, P.-Y., & Moulin-Frier, C. (2024). *Cultural evolution in populations of Large Language Models.* arXiv:2403.08882（2024-03-13）.〔arXiv 全文检索页核验〕
53. ✅ **Anthropic 官方定价页**：platform.claude.com/docs/en/about-claude/pricing〔2026-09-10 直接抓取〕。含逐模型的基础输入 / 5m 与 1h 缓存写 / 缓存命中 / 输出 / Batch 单价，缓存倍率（1.25× / 2× / 0.1×），Batch 50% 且可与缓存叠加，工具系统提示 token 数（Opus 5: 286 / 406），以及 "Claude 4.7 and later models ... **produces approximately 30% more tokens for the same text**"。 **[已核验]**（2026-09-10 直接抓取原页逐项复核：Opus 5 $5/$6.25/$10/$0.50/$25，Sonnet 5 $2/$10，Haiku 4.5 $1/$5；缓存写 1.25×/2×、命中 0.1×（Fable 5.1 / Mythos 5.1 例外为 0.025×）；Batch 50% 且与缓存等修饰叠加；Opus 5 工具系统提示 286/406 token；4.7 及之后 tokenizer 约 +30% token。全部与正文一致）
54. ✅ **Smallville 实现常数**：github.com/joonspk-research/generative_agents，`reverie/backend_server/persona/cognitive_modules/retrieve.py`（`gw=[0.5,3,2]`、`new_retrieve(..., n_count=30)`、`recency_decay**i`）与 `environment/frontend_server/storage/base_the_ville_isabella_maria_klaus/personas/Isabella Rodriguez/bootstrap_memory/scratch.json`（`recency_decay=0.995`、`importance_trigger_max=150`、`vision_r=8`、`att_bandwidth=8`、`retention=8`、`daily_reflection_size=5` 等）。〔GitHub raw 直接读源码核验〕
55. ✅ **Project Sid 仓库内容清单**：api.github.com/repos/altera-al/project-sid/contents/ 返回**恰好三个文件**——`2024-10-31.pdf`(21,270,194 B)、`README.md`(1,999 B)、`visual_abstract.png`(8,215,703 B)，**无目录、无代码、无 LICENSE**。〔GitHub Contents API 核验，2026-09-10〕
56. ✅ **OASIS / AgentSociety / AgentTorch 正文数字**：arXiv HTML 版（`arxiv.org/html/2411.11581v4`、`arxiv.org/html/2502.08691v1`、`arxiv.org/html/2409.10568v2`）直接抓取，用于第 4 节 ⚠冲突标记与第 2.5–2.7 节补充。
57. ✅ Aher, G. V., Arriaga, R. I., & Kalai, A. T. (2023). *Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies.* **ICML 2023, PMLR 202:337–371.**〔PMLR 核验，补齐第一轮只有 arXiv 号的书目〕 **[已核验]**（PMLR 页面：题名与 PMLR 202:337–371 完全一致，ICML 2023）
58. ✅ Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024). *Lost in the Middle: How Language Models Use Long Contexts.* **TACL, 12, 157–173.** doi:10.1162/tacl_a_00638.〔ACL Anthology 核验，补齐正式版书目〕
59. ✅ Argyle, L. P., Busby, E. C., Fulda, N., Gubler, J. R., Rytting, C., & Wingate, D. (2023). *Out of One, Many: Using Language Models to Simulate Human Samples.* **Political Analysis, 31(3), 337–351.** doi:10.1017/pan.2023.2.〔Cambridge Core 核验，补齐正式版书目（第一轮只有 arXiv:2209.06899）〕

> **两轮合并后的诚实结论**：本简报中**没有任何一条文献主张是凭记忆写下的**。所有 ⚠ 标记处表示两轮抓取结果不一致，须人工回原文裁决；所有 D 级判断集中在第 10 节，且已逐条说明为什么它没有来源、以及 Phase 1 用什么实验去检验它。
