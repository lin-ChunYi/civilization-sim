# 文字、记录技术与历史记忆的失真

- **slug**: `writing-records-memory`
- **一句话范围**：文字为什么会出现、记录如何被生产与丢失、记忆在口传与抄写中如何系统性变形、有动机的行为者如何改写记录，以及由此推出的"世界事实层 / 当时记录层 / 后世叙事层"三层模型的可工程化设计。
- **本次检索日期**：2026-09-10
- **检索手段说明**：本次会话的 WebSearch 配额已被上游耗尽。实际检索通过 Crossref REST API（书目检索 + abstract 字段）、Unpaywall API（OA 定位）、DOAJ API，以及对 PMC / Nature / 大学仓储 / CDLI 等站点的直接抓取完成。凡标注 "**已核验**" 的条目，均为本次会话中通过上述接口真实取回元数据、摘要或全文。未能取回的，一律标注 "**未核验**"。

---

## 1. 本简报要回答的问题

给 civilization-sim 的建模者，本简报要回答八个工程问题：

1. **文字在什么条件下会从"没有文字"的世界里长出来？** 需要哪些前置状态变量，触发概率是什么量级，能不能不用科技树？
2. **文字会不会消失？** 如果会，机制是什么？
3. **"被记录"这件事由什么决定？** 是事件重要性，还是别的东西？
4. **记录如何丢失？** 丢失率是多少？丢失是随机的还是结构化的？"存活下来的记录"和"当时存在的记录"之间的偏差有多大、往哪个方向偏？
5. **口传与抄写在每一次传递中把信息变形成什么样？** 有没有可写成算子的规律？时间尺度是什么？
6. **有权力的人改写历史时，能改到什么程度？** 什么东西限制了篡改的彻底性？
7. **世界内部的历史学家在什么信息条件下工作？** 他们的产出如何回流进世界？
8. **上面这些如何组织成一套可以跑数千年、可回放、可反事实、且不会退化成剧情树的数据结构？**

本简报**不**覆盖：语言演化本身、教育制度经济学、印刷术的经济影响、信息传播速度与地理（属于"信息边界"专题）、宗教叙事的内容生成（属于宗教专题）。这些只在与记录/记忆交叉处提及。

---

## 2. 已有成熟模型与理论

### 2.1 Schmandt-Besserat 的 token → 楔形文字假说

- **核心机制**：公元前 8000 年起近东出现黏土筹码（tokens）用于记账；筹码被封入 bulla（黏土球）并在球面压印筹码形状；随后压印取代了实物筹码，再抽象为刻划符号，最终成为 proto-cuneiform。写作因此是**会计技术的副产品**，而非语言的图像化。
- **形式化程度**：只有定性理论 + 类型学序列，没有形式模型。
- **状态变量**：筹码类型数、经济交易复杂度、封装/压印/刻划三阶段。
- **参数**：无可用量化参数。
- **适用范围**：西亚，前 8000–前 3200。
- **已知局限**：因果链是"合理叙事"而非被证明；筹码与最早文字之间的形状对应有多少是选择性匹配，学界长期争论；该模型解释不了埃及、中国、中美洲。**该假说在本次检索中只核验到作者本人的多篇陈述，未核验到系统性的批评文献原文**。
- **出处（已核验）**：Schmandt-Besserat, "The Origin of Visible Language", 1992, in *Language Origin: A Multidisciplinary Approach*, doi:10.1007/978-94-017-2039-7_12；"Clay Tokens as Forerunner of Writing", 1991, doi:10.1515/9783111353180.485；Wilding, Rowan, Maurer & Schmandt-Besserat, "Tokens, Writing and (Ac)counting", *Exchanges* 2017, doi:10.31273/eirj.v5i1.196。

### 2.2 Houston (ed.), *The First Writing: Script Invention as History and Process*

- **核心机制**：把"文字发明"当作**过程**而非事件来比较研究——两河、埃及、中国、中美洲各自的发明路径、社会承载者、早期功能与语音化时机不同。
- **形式化程度**：定性比较，无形式化。
- **对我们的价值**：确立"文字发明是一个可以有多条路径、多个阶段的过程"，这正是我们要的涌现式建模的前提。
- **出处（已核验，但只核验到书评而非原书）**：Millard, "Book Review of *The First Writing: Script Invention as History and Process*, edited by Stephen D. Houston", *American Journal of Archaeology* 2006, doi:10.3764/ajaonline1103.millard。

### 2.3 Postgate, Wang & Wilkinson (1995)：早期文字的"仪式性"是保存偏差的产物 —— **本简报最重要的一条**

- **核心机制**：跨地区比较显示，最早文字看起来偏"仪式与象征"用途，这**更可能来自考古保存条件**（仪式文本用耐久材料，行政文本用易腐材料），而不是各文明文字功能的深层差异。他们明确推断：最早的中国、埃及、中美洲文本很可能与两河一样，主要是**实用性**的。
- **形式化程度**：定性论证 + 材料学推理，无形式模型。
- **对我们的价值**：这条直接给出了"世界事实层 / 记录层"分离的**经验依据**：世界内部观察者（考古学家、历史学家）看到的功能分布 ≠ 真实功能分布，偏差方向可预测（耐久媒介承载的类别被系统性放大）。
- **出处（已核验，读到摘要原文）**：Postgate, Wang & Wilkinson, "The evidence for early writing: utilitarian or ceremonial?", *Antiquity* 69 (1995), doi:10.1017/s0003598x00081874。

### 2.4 Kestemont et al. (2022)：unseen species 模型量化文化存活率 —— **唯一提供可直接使用参数的模型**

- **核心机制**：把"作品（WORK）"当作物种、把"抄本（DOCUMENT）"当作个体观测，用生态学的 Chao1 非参数丰富度估计量反推**原本存在多少作品、多少抄本**。作品存活率 = 样本完备度 $\hat C$；抄本存活率用 Chao1 的最小抽样扩展估计。
- **形式化程度**：**完全形式化**，且估计量是非参数的、对分布形状稳健，可以直接搬进我们的模拟做反向校验。
- **状态变量**：每部作品的现存抄本数 $f_i$；singletons $f_1$、doubletons $f_2$。
- **关键结论（本次读到全文正文与 Table 1）**：
  - 六个欧洲方言（Dutch, English, French, German, Icelandic, Irish）骑士/英雄叙事文学的合并估计：**作品存活 68.3% CI[63.2–73.5]，抄本存活 9.0% CI[7.5–10.7]**。
  - 原本约 **1,170 部作品**，今存 **799 部**；原本约 **40,614 件抄本**，今存 **3,648 件**。
  - 方言间差异极大：作品存活 English 38.6% ↔ Irish 81.0%；抄本存活 English 4.9% ↔ Irish 19.2%。
  - **均匀度（evenness）是被忽视的关键因素**：抄本在作品间分布越均匀，整个语料在冲击下越稳定；French 分布极不均匀（少数作品占大量抄本），因此脆弱。
  - 传统书史学基于中世纪图书馆目录的估计：普通手稿存活率 **7%**，高端抄本 **20%**（Kestemont 引用，来自 Holy Roman Empire 的样本）。
  - Chao1 是**下界**估计量，所以上述存活率严格说是**损失的上界**（实际可能损失更多）。
- **已知局限**：只针对叙事文学；行政文书、账册的分布形状完全不同；对"从未被抄第二次"的作品无能为力（$f_1$ 主导时估计不稳）。
- **出处（已核验，读到 KU Copenhagen 仓储全文 PDF）**：Kestemont, Karsdorp, de Bruijn, Driscoll et al., "Forgotten books: The application of unseen species models to the survival of culture", *Science* 375 (2022), doi:10.1126/science.abl7655。

### 2.5 Vansina, *Oral Tradition as History* (1985) —— 口传史料学的标准框架

- **核心机制**：口传不是"退化的历史"，而是有自己的生产、传承与社会功能规则的信息系统。Vansina 提出的关键结构性概念（**"floating gap"**：口传时间深度上呈"近期详细 + 起源神话 + 中间空洞"的三段式；**structural amnesia**：与当下社会安排无关的世系与事件被系统性遗忘）是本项目"记忆非单调衰减"设计的理论来源。
- **形式化程度**：只有定性理论。
- **重要警告**：**本次检索核验到该书的存在、出版方与年份（Univ. of Wisconsin Press, 1985, doi:10.2307/jj.36106057），但没有读到原书正文，因此上面对 "floating gap" 三段式结构的具体描述属于我的记忆复述，标为未核验（C 级）。**
- **配套的怀疑派**：Henige, *The Chronology of Oral Tradition: Quest for a Chimera* (Clarendon, 1974) —— 论证从口传世系反推绝对年代基本不可行，并识别出 "feedback"（书面史料回流污染口传）问题。**已核验（通过三篇书评：Ekechi, *AHR* 1975, doi:10.2307/1852179；Yoffee, *American Anthropologist* 1975, doi:10.1525/aa.1975.77.2.02a01020；*Journal of African History* 1976, doi:10.1017/s0021853700001353）**。Henige 的 feedback 概念对我们至关重要：一旦世界内有了书面史，口传会被书面史反向重写，两个层不再独立。

### 2.6 Rubin, *Memory in Oral Traditions* (1995) —— 口传的认知约束

- **核心机制**：史诗、民谣、点数童谣之所以能长期稳定传承，是因为它们被**多重约束**（韵律、押韵、音响模式、意象、主题结构）同时限制，使得每一步回忆是"受约束的重构"而非"复制"。约束越多，可行解空间越小，跨代稳定性越高。
- **形式化程度**：半形式化（cue-based 多重约束搜索模型），有实验数据但没有可直接移植的参数表。
- **对我们的价值**：给出"为什么某些叙事形式能活几百年而散文叙事不能"的机制，可以做成"叙事对象的约束度 constraint_score → 每步保真度"的映射。
- **出处（已核验）**：Rubin, *Memory in Oral Traditions: The Cognitive Psychology of Epic, Ballads, and Counting-out Rhymes*, Oxford University Press 1995, doi:10.1093/oso/9780195082111.001.0001（并核验到章节 "Sound" doi:...003.0004、"Counting-out Rhymes" ...003.0010、"North Carolina Ballads" ...003.0011）。

### 2.7 Bartlett 的 serial reproduction 传统与现代文化传递实验

- **核心机制**：信息沿链条传递时发生三类系统性变形——**leveling（细节脱落/整体压缩）、sharpening（少数元素被放大突出）、assimilation（向接收者已有图式同化）**。现代实验把它变成了可测量的"内容偏见（content bias）"测量工具。
- **形式化程度**：半形式化。实验范式高度标准化（平行链 × 若干代），但结果通常报告为效应量而非可移植参数。
- **已确认的内容偏见（均为本次核验到的独立论文）**：
  - **社会信息偏见**：涉及第三方社会互动（八卦）的信息传递保真度高于同等的非社会信息 —— Mesoudi, Whiten & Dunbar 2006, *British Journal of Psychology*, doi:10.1348/000712605x85871（结论经 Mesoudi & Whiten 2008 综述全文确认）。
  - **反直觉偏见**：轻度违反直觉本体论的概念比普通概念和过度反直觉概念传播更好 —— Barrett & Nyhof 2001, *Journal of Cognition and Culture*, doi:10.1163/156853701300063589；Boyer & Ramble 2001, *Cognitive Science*, doi:10.1207/s15516709cog2504_2。
  - **MCI 叙事的文化成功**：含 2–3 个最小反直觉元素的叙事组合最成功 —— Norenzayan, Atran, Faulkner & Schaller 2006, *Cognitive Science*, doi:10.1207/s15516709cog0000_68（**元数据已核验，全文未取到，具体数值未核验**）。
  - **刻板印象一致性偏见**：与接收方文化刻板印象一致的内容在链条中存活率更高 —— Kashima 2000, *PSPB*, doi:10.1177/0146167200267007；Lyons & Kashima 2001, *Social Cognition*, doi:10.1521/soco.19.3.372.21470。
  - **层级化转换**：事件知识在传递中被转换成层级化的脚本结构 —— Mesoudi & Whiten 2004, *JoCC*, doi:10.1163/156853704323074732。
  - **生存/社会信息偏见（都市传说）**：Stubbersfield, Tehrani & Flynn 2014, *BJP*, doi:10.1111/bjop.12073。
  - **情绪选择**：Eriksson & Coultas 2014, *JoCC*, doi:10.1163/15685373-12342107。
- **出处（已核验，读到全文）**：Mesoudi & Whiten, "The multiple roles of cultural transmission experiments in understanding human cultural evolution", *Phil. Trans. R. Soc. B* 363 (2008), doi:10.1098/rstb.2008.0129；Bartlett *Remembering* 1932（CUP 1995 重印版章节 doi:10.1017/cbo9780511759185.010 / .011）；Roediger, Meade, Gallo & Olson, "Bartlett Revisited", 2008, doi:10.1037/e527312012-156。

### 2.8 Iterated learning / 文化吸引子 —— 变形的两种形式化路线

- **路线 A：Bayesian iterated learning（Griffiths & Kalish 2007）**。每一代从上一代的输出中学习并产生新输出。核心定理：在贝叶斯学习者链条上，长期分布**收敛到学习者的先验**，与初始输入无关。这是"传承会把内容拉向文化/认知先验"的最干净的数学表述。**已核验**：Griffiths & Kalish, "Language Evolution by Iterated Learning With Bayesian Agents", *Cognitive Science* 31 (2007), doi:10.1080/15326900701326576。
- **路线 B：cultural attraction（Sperber / Claidière）**。变形不是随机漂变，而是被"吸引子"结构化地拉动；因此文化稳定性可以在**没有高保真复制**的情况下实现。**已核验**：Claidière, Scott-Phillips & Sperber, "How Darwinian is cultural evolution?", *Phil. Trans. R. Soc. B* 369 (2014), doi:10.1098/rstb.2013.0368。
- **实验支撑**：迭代学习实验中，语言/序列在传承压力下自发获得结构，因为**可学习性（压缩性）与表达性之间的权衡**。**已核验**：Kirby, Cornish & Smith, PNAS 105 (2008), doi:10.1073/pnas.0707835105；Kirby, Tamariz, Cornish & Smith, "Compression and communication in the cultural evolution of linguistic structure", *Cognition* 141 (2015), doi:10.1016/j.cognition.2015.03.016。
- **对我们的直接含义**：叙事在多代传递后**必然**向一组有限的吸引子（故事类型）收敛。经验上这组吸引子是存在的——ATU 类型索引就是它的实测目录。

### 2.9 Twitchett (1992)：唐代官修史的**多级流水线** —— 三层模型的现成历史原型

- **核心机制**：唐代把"记录"制度化为一条多级编纂链，每一级都是压缩 + 编辑 + 权限瓶颈。本次通过 Crossref 核验到该书**完整章节结构**，它就是流水线本身：
  1. **起居注 Ch'i-chü chu**（Court Diaries）doi:10.1017/cbo9780511572678.006
  2. **内起居注 Nei Ch'i-chü chu**（Inner Palace Diary）...007
  3. **时政记 Shih-cheng chi**（Record of Administrative Affairs）...008
  4. **日历 Jih-li**（Daily Calendar）...009
  5. **实录 Shih-lu**（Veritable Records）...012
  6. **国史 Kuo shih**（National History）...013
  7. **旧唐书**（正史）的编纂 ...014，及其史源分析 ...015 / ...016
  - 旁路：**传记 Biographies** ...010；**典志、类书、文书汇编** ...011
  - 还有一章专门讲 **the bureaucratic apparatus** ...004（史馆的官僚机构本身）
- **形式化程度**：定性制度史，但结构本身已经是一张可以直接实现的有向图。
- **对我们的价值**：这条链给了我们三层模型中"记录层"的**内部子结构**：记录不是一个层，而是若干级，每级有自己的 (采集规则、压缩率、编辑者、读者权限、保存介质、留存周期)。
- **出处（已核验）**：Twitchett, *The Writing of Official History under the T'ang*, Cambridge University Press 1992, doi:10.1017/cbo9780511572678。

### 2.10 Seshat: Global History Databank —— 唯一可用的"记录技术 × 社会复杂度"跨文明校准集

- **核心内容（本次读到 Turchin et al. 2018 PNAS 全文）**：414 个社会、30 个地区、覆盖近 10,000 年，编码 **51 个变量**聚合为 **9 个复杂度特征（CCs）**，其中 **CC7 = Information system（文字、记录保存等特征）**、**CC8 = Texts（是否产生历史、哲学、虚构等专门文献）**。
- **关键定量结论**：9 个 CC 两两相关系数在 **0.49–0.88** 之间；**单一主成分解释约四分之三的总变异**；交叉验证的样本外预测 $\rho^2$：Information system **0.59**、Texts **0.73**（对比 polity population 0.84、monetary system 0.53）。
- **对我们的价值**：这是我们能拿到的、最直接的**校准目标**——在我们的模拟里，"信息系统复杂度"应当与人口/层级/基础设施强相关（0.5–0.9 量级），并且大致落在同一条主轴上。如果我们的世界里出现了"庞大帝国但没有任何记录制度"或"无国家但有成熟史学"，那不是禁止，而是**需要极强的前置解释**（对应纲领第 7 条）。
- **已知局限与争议**：Seshat 的编码由专家判断驱动，缺失值靠多重插补；围绕 Whitehouse et al. 2019 "moralizing gods" 论文的数据编码与缺失处理有实质争议（**已核验**：Slingerland, Monroe, Spicer, Muthukrishna et al., "Historians Respond to Whitehouse et al. (2019)", OSF preprint, doi:10.31234/osf.io/2amjz；以及 *Journal of Cognitive Historiography* 2022 的一组回应，如 Naether doi:10.1558/jch.39578）。**用 Seshat 做校准可以，用它做真值不行。**
- **出处（已核验）**：Turchin, Currie, Whitehouse, François et al., PNAS 115 (2018), doi:10.1073/pnas.1708800115；Turchin, Brennan, Currie, Feeney et al., "Seshat: The Global History Databank", *Cliodynamics* 6 (2015), doi:10.21237/c7clio6127917。

### 2.11 一个必须点明的空白：**没有现成的"记录—记忆—史学"ABM**

本次以多组关键词在 Crossref 检索 agent-based model / simulation × collective memory / record keeping / archives / historiography，**没有检索到任何一个可复用的、把"世界事实 / 记录 / 叙事"分层建模的模拟器或已发表模型**。检索到的 ABM 都是当代议题（灾害风险认知、集体行动、组织问题求解）。

**结论：本领域没有可以直接抄的内核。第 3 节的机制清单必须由我们自己从上述分散的经验部件组装，并明确标注哪些是组装时加的假设。**

---

## 3. 可直接用于本项目的机制清单

下面每条给出：输入 → 输出、数学/算法草图、时间尺度、空间粒度、证据等级、以及"为什么这样简化"。
所有函数形式若无来源，一律在括号里标 **[形式为 D 级假设]**；只有参数量级有来源的，标出来源。

---

### M0. 四层数据结构（本简报的核心设计）

用户纲领要求"世界事实与历史叙事分离"。我建议**不要**做成三层，而是**四层 + 一个递归回流**：

```
L0  WorldFact      模拟器权威事件日志。Agent 永不可读。
                   Event{id, t, actors[], location, type, magnitude, causes[], rng_seed}

L1  Trace          物质痕迹。事件在世界上留下的非意图性残留。
                   Trace{event_id?, kind, location, medium, decay_state, discoverable_after}
                   注意：Trace 可以没有 event_id（自然过程产生的假痕迹）。

L2  Record         意图性记录。由某个 agent/组织为某个目的制作的载体化陈述。
                   Record{id, author_org, genre, medium, created_t, propositions[],
                          copies:[Copy{repository, condition}], access_policy, motive_vector}
                   propositions 是"关于世界的断言"，可真可假。

L3  Narrative      流通中的叙事。官方史、民间传说、宗教故事、学者著作、家族记忆。
                   Narrative{id, carrier(oral|written), propositions[], audience_strata,
                             prestige, constraint_score, lineage[], last_retold_t}

L4  Historiography 世界内历史学家 agent 的产出。它本身是一个 L3 对象，会被抄、被丢、被改。
                   ——这就是递归回流：世界内的史学研究改变了世界内的叙事，
                     从而改变了后来者的信息条件。
```

**四层而不是三层的理由**：L1（物质痕迹）和 L2（意图记录）的**存活规律、发现规律和偏差方向完全不同**，而且它们会互相矛盾——这正是我们想要的"考古与文献冲突"（第 6 节有真实案例）。把它们合并会丢掉整个考古学维度。

**不变量（必须由引擎强制）**：
- 任何 L2/L3/L4 对象上的每一条 proposition，都必须携带一个 `provenance` 链，最终指向某个 L2 记录或某个 agent 的直接经验。**不允许凭空出现的 proposition。**（这条直接实现纲领的"因果链"要求。）
- `truth(p)` 只能由引擎对照 L0 计算，用于分析与验证，**永远不作为任何 agent 的输入**。
- LLM agent 可以生成/改写 L3 的**措辞、动机解释、文学形式**，但 proposition 的 `provenance` 与 `truth` 由规则系统裁定。（纲领第 5 条。）

---

### M1. 记录的产生：由制度惯例驱动，不由事件重要性驱动

- **输入**：组织 $o$ 的记录体裁集合 $G_o$、各体裁的触发条件与周期、书吏供给 $S_o$、介质供给 $M$、事件流。
- **输出**：每 tick 新增的 Record 对象集合。
- **算法草图**：
  ```
  for org o, for genre g in G_o:
      n_g = Poisson( λ_g · activity_g(t) · min(1, S_o / demand_o) )
      for each of n_g:
          create Record(genre=g, medium=m_g, copies=k_g,
                        propositions = schema_g(sampled events),
                        motive_vector = o.motives)
  ```
  关键是 `schema_g`：**每种体裁只记录它的模板槽位所要求的东西**。粮仓账册记录数量与日期，不记录动机；占卜记录记录问卜事项与吉凶，不记录战果；起居注记录皇帝的言与动，不记录皇帝的想法。
- **为什么这样简化**：这是本领域最容易犯的建模错误的解药。经验证据：MacMullen 提出的 "epigraphic habit" 概念——罗马帝国铭文数量随时间的巨大起伏**不能**由人口或识字率解释，立碑是一种会兴起也会消退的**文化习惯**（**已核验元数据**：MacMullen, "The Epigraphic Habit in the Roman Empire", *AJP* 103 (1982), doi:10.2307/294470；**该文的具体数量曲线本次未取到，不引用任何数字**）。
- **时间尺度**：tick（建议年）。
- **空间粒度**：组织/聚落。
- **证据等级**：**B**（机制被广泛接受；λ 无可用参数）。

---

### M2. 记录的存活：介质 × 环境 × 仓储冲击，且冲击在仓储内部相关

- **输入**：Copy 的 (medium, environment, repository)、仓储层的冲击过程。
- **输出**：每个 Copy 的存亡；每个 Work 的存亡。
- **数学草图**：
  $$s_{\text{copy}}(\Delta t)=\exp\Big[-\big(h_{\text{mat}}(m,\text{env})+h_{\text{use}}\big)\Delta t\Big]\cdot\prod_{\text{shocks}}(1-\delta_j)$$
  - $h_{\text{mat}}$：材料—环境年化危险率。
  - 仓储冲击 $j$ 是**仓储级**的 Poisson 事件（火灾、战乱、改朝换代、有意销毁），一次冲击以概率 $\delta_j$ 杀死仓储内**全部或大部分**副本 → 副本之间的存亡**强相关**。
  - Work 存活：$P=1-\prod_i (1-s_i)$，$i$ 遍历该作品的所有副本。
- **为什么这样简化**：Kestemont et al. 2022 明确指出，抄本在作品间分布的**均匀度**决定语料在冲击下的稳定性。只有把冲击建成仓储级相关事件、把副本数建成重尾分布，才能复现"抄本存活 9% 而作品存活 68%"这种巨大落差。
  用他们的数字自检：原始 40,614 抄本 / 1,170 作品 ≈ 平均每作品 34.7 个抄本。若副本独立存活、$p=0.09$，则平均作品存活概率 $1-0.91^{34.7}\approx 96\%$，远高于实测的 68.3%。**差距只能来自分布极不均匀（大量作品只有 1–2 个副本）**。所以副本数必须是重尾的。
- **时间尺度**：年（衰减）+ 事件（冲击）。
- **空间粒度**：仓储（repository）。
- **证据等级**：**A**（存活率有可用区间；分布形状机制有直接实证）。参数见第 4 节。

---

### M3. 保存的非单调性：**毁灭有时是最好的保存**（"沉积事件"机制）

- **输入**：仓储遭遇的事件类型。
- **输出**：副本从"流通/传世通道"转移到"沉积/出土通道"，年化危险率骤降但可读性归零，直到未来被发现。
- **机制**：
  ```
  on shock(repository, kind):
      if kind in {conflagration} and medium == unbaked_clay:
          # 火把泥板烧成陶，危险率下降一个数量级以上
          copy.channel = BURIED; copy.h_mat *= r_fire   (r_fire << 1)
      if kind in {burial, sealing, dumping_in_well} and env is anoxic/arid:
          copy.channel = BURIED; copy.h_mat *= r_anox   (r_anox << 1)
      copy.readable = False
      copy.discoverable_after = t + Geom(p_discovery)
  ```
- **为什么必须有这条**：真实世界里最重要的行政档案几乎全部走的是这条路。**已核验的中国案例**：里耶（Liye）秦简出自古迁陵县一号井，*Early China* 的介绍文章结尾"推测了这批文书为何在秦王朝开始崩溃时被扔进井里"（**已核验摘要原文**："offering a speculation on why the documents were thrown into the well as the Qin dynasty began to crumble"，doi:10.1017/s0362502800000523）。也就是说：**王朝崩溃 → 档案被抛弃 → 落入缺氧环境 → 存活两千二百年 → 与传世文献冲突。** 这是我们要的完整因果链。
- **副作用（这才是重点）**：BURIED 通道的副本**不参与抄写传承**，因此它保留的是**未被后世编辑过的版本**。当它被后世发现时，会与 L3 的传世叙事**结构性冲突**。这是世界内史学革命的燃料。
- **时间尺度**：事件触发 + 数百至数千年潜伏。
- **空间粒度**：仓储/遗址。
- **证据等级**：**B**（机制有明确的个案证据；转移概率与 $r$ 无参数，为 D 级假设）。

---

### M4. 幸存偏差过滤器：引擎必须显式维护它

- **输入**：L2 全集 + 存活规则。
- **输出**：`SurvivingCorpus(t)` 以及**引擎侧**的偏差向量 $\mathbf{b}(t)$。
- **算法**：对每个体裁 $g$，计算 $b_g(t)=\dfrac{\#\{\text{存活的 }g\}/\#\{\text{存活总数}\}}{\#\{\text{曾存在的 }g\}/\#\{\text{曾存在总数}\}}$。
- **用途**：
  1. 世界内历史学家只能看到分子；引擎知道分母。
  2. $\mathbf{b}(t)$ 是我们做"模拟是否合理"验证的一个直接指标：如果我们的世界里 $b_{\text{ceremonial}} \gg 1$、$b_{\text{administrative}} \ll 1$，那就复现了 Postgate/Wang/Wilkinson 观察到的真实偏差模式，是好事。
- **证据等级**：**A**（偏差方向有直接文献结论；量级无参数）。

---

### M5. 口传的每步变形算子

把一个 Narrative 表示为命题集合 $\{p_i\}$，每个命题有属性 $(agent, action, place, time, quantity, causal\_link, salience)$。一次转述施加算子 $T$：

1. **脱落（leveling）**：命题 $i$ 存活概率
   $$q_i=\sigma\big(\beta_0+\beta_{\text{soc}}\text{soc}_i+\beta_{\text{mci}}\text{mci}_i+\beta_{\text{emo}}\text{emo}_i+\beta_{\text{schema}}\text{fit}_i-\beta_{\text{det}}\text{detail}_i\big)$$
   各 $\beta$ 的**符号**都有实验来源（M 2.7 列表），**数值没有**。**[数值为 D 级]**
2. **放大（sharpening）**：存活命题的数量属性 $x\leftarrow x\cdot(1+\varepsilon)$，$\varepsilon$ 取正偏分布（军队人数、死伤、财富只涨不跌）。**[形式与参数皆为 D 级；但"放大"这一方向来自 Bartlett 传统，B 级]**
3. **同化（assimilation / attraction）**：$p\leftarrow p+\alpha\big(A(p)-p\big)$，$A$ 是接收者所处文化的吸引子。来源：Claidière/Sperber 的 attraction 形式；Griffiths & Kalish 的贝叶斯迭代学习给出"长期收敛到先验"的定理。**证据 B，函数形式 D。**
4. **压缩到约束容量**：命题数 $n$ 衰减到 $n^\ast$，$n^\ast$ 随叙事的 `constraint_score`（韵律/格律/仪式重复）增大而增大。来源：Rubin 的多重约束理论 + Kirby 的压缩—表达权衡。**证据 B。**
5. **行动者合并 / 英雄化**：若两个 actor 在叙事中承担相似功能且都低知名度，以概率 $\propto$ 时间深度合并为一个高知名度 actor。**[D 级，但由 ATU 类型化现象与集体记忆的名人集中现象间接支持]**
6. **年代望远（telescoping）与结构性遗忘**：时间属性带噪且系统性向"整齐的边界"（王朝更替、大灾、圆整数字）吸附；与当下社会安排无关的世系分支被删除。来源：Vansina 的 structural amnesia、Henige 对口传年代学的否定。**证据 C（本次未读到原文）。**
7. **类型化**：叙事以概率漂向最近的故事类型槽位。经验依据：ATU 索引的存在本身（Uther 2004，**已核验通过 Leppälahti 2005 书评 doi:10.30666/elore.78537**）。

- **时间尺度**：一次转述 ≈ 事件级；一代 ≈ 25–30 年（**该代际长度是 D 级常识假设**）。
- **空间粒度**：社群/家族。
- **证据等级**：**B**（各偏见方向）/ **D**（全部数值）。

---

### M6. 记忆保真度对时间深度的**非单调**曲线（floating gap）

- **输入**：事件距今 $\Delta t$、是否被仪式化 anchor、是否有书面记录支撑。
- **输出**：该事件在无书面记录社会中的可回忆度 $F(\Delta t)$。
- **草图（分段，D 级形式）**：
  $$F(\Delta t)=\underbrace{e^{-\Delta t/\tau_1}}_{\text{活人记忆}}+\underbrace{A_{\text{charter}}\cdot\mathbb{1}[\text{锚定于起源}]}_{\text{不衰减}}+\underbrace{c_{\text{ritual}}\cdot r(\Delta t)}_{\text{周期性仪式重锚}}$$
  其中 $\tau_1$ 对应"活着的人 + 从祖辈听说"的深度（**量级为 D 级假设，我建议 60–100 年**），中段近乎为零，而"起源叙事"项因为每代都被仪式重新锚定，**不随时间衰减**。
- **为什么必须非单调**：这是本领域最反直觉、也最常被建模者漏掉的一条。指数衰减会给出"最古老的事情最模糊"，而真实口传社会常常对**起源**有极详细（虽未必真）的叙事，对**中段**几乎一片空白。
- **相关但有争议的极端证据**：Nunn & Reid 主张澳大利亚原住民口传保存了 7000 年前海平面上升的记忆（**已核验元数据**：*Australian Geographer* 46 (2015), doi:10.1080/00049182.2015.1077539；及 Nunn, *Edge of Memory*, Bloomsbury 2018, doi:10.5040/9781472943255）。另一侧，da Silva & Tehrani 用系统发生学方法把 ATU 330 "The Smith and the Devil" 重建到原始印欧语人群/青铜时代（**已核验，读到 PMC 全文**：*Royal Society Open Science* 3 (2016), doi:10.1098/rsos.150645；正文明确：19 个故事以 >50% 似然可回溯到更早的祖先人群，但**在原始印欧语节点上只有 4 个是试探性的，贝叶斯分析最终只支持 1 个**）。
- **对我们的含义**：**极长时程的记忆存活是可能的，但存活的是"故事类型/母题"，不是"事件细节"。** 建模上应当分开两个对象：`event_memory`（快速衰减，非单调）与 `motif`（准永久，但不携带可核验的事实内容）。
- **证据等级**：**C**（Vansina 的结构未读原文；Nunn & Reid 在学界有实质争议；da Silva & Tehrani 的深节点重建自己就承认支持很弱）。

---

### M7. 有动机的改写：篡改是**受副本分散度约束的**，不可能彻底

- **输入**：行为者 $A$、动机、其可触达的仓储集合 $R_A$、目标命题 $p$ 在世界上的副本分布。
- **输出**：改写成功/部分成功/失败 + **可被后世检测的痕迹**。
- **算法草图**：
  ```
  reach   = Σ_{r ∈ R_A} copies(p, r)
  total   = Σ_{all r}   copies(p, r)
  cover   = reach / total
  outcome:
      cover == 1        → 全面抹除；但若存在 BURIED 通道副本，未来仍可能出土
      0 < cover < 1     → 部分抹除：留下"记载密度断崖" + 版本冲突
      cover == 0        → 失败，且尝试本身成为一个 L0 事件（可被记录）
  detect_prob(后世) ∝ 存活的独立矛盾记录数 × 历史学方法水平
  ```
- **量级参数（本次读到 Michel et al. 2011 全文，可直接用作"部分抹除"的强度先验）**：纳粹德国 1933–45 对被禁作者/艺术家在德语书籍中的提及率下降幅度：**历史类作者 9%、文学类 27%、艺术类 56%、政治类 60%、哲学类 76%**；Marc Chagall 的全名在 1936–1944 年间的德语语料中**只出现过一次**；1989 年天安门事件在中文语料中的反应"基本缺失"，而 1976 年事件在英文语料中有明显升高。
- **对我们的直接含义**：**压制的效力强烈依赖领域，且从来不是 100%。** 用一个 0.1–0.8 的领域相关系数比用"删除"这个布尔操作真实得多。
- **制度化改写的历史原型（已核验）**：
  - 唐代史馆的多级链条本身就是编辑瓶颈（Twitchett 1992，见 2.9）。
  - 明《太祖实录》经多次修订，Xie Jin 作为"帝国宣传者"参与改修 —— Chan Hok-lam, "Xie Jin (1369–1415) as Imperial Propagandist: His Role in the Revisions of the *Ming Taizu Shilu*", *T'oung Pao* 91 (2005), doi:10.1163/1568532054905142；同作者 "Legitimating Usurpation: Historical Revisions under the Ming Yongle Emperor (r. 1402–1424)", doi:10.4324/9781003420842-8。
  - 明代关于实录的公开论争 —— Ditmanson, "Historical and Political Arguments: Debates on the Veritable Records in the Ming Dynasty", doi:10.1163/9789004423626_003。**这条很重要：改写不是秘密操作，它本身可以是公开政治斗争的对象。**
  - 清初《旧满洲档》→《满洲实录》的改编 —— 김선민 2012, doi:10.16957/sa..77.201209.139。
  - 罗马的 memory sanctions（damnatio memoriae）作为一整套制度而非单一动作 —— Flower, *The Art of Forgetting*, UNC Press 2006，章节 "The Origins of Memory Sanctions in Roman Political Culture" doi:10.5149/9780807877463_flower.7、"Did the Greeks Have Memory Sanctions?" ...flower.6、"Punitive Memory Sanctions II: The Republic of Sulla" ...flower.9。
- **证据等级**：**A**（部分压制的量级有实测）/ **B**（制度机制）。

---

### M8. 集体记忆中"人"的衰减

- **输入**：人物的历史位置（距今第几位继任者）、峰值声望。
- **输出**：$t$ 时刻该人物在大众叙事中的可及性。
- **实测形状（已核验摘要）**：Roediger & DeSoto 用 1974/1991/2009/2014 四批被试测美国总统回忆，发现**在位者之前的 8–9 位总统呈大致线性的遗忘**，并拟合遗忘函数外推：Truman 大约到 **2040 年**会衰减到 McKinley 目前的水平（*Science* 346 (2014), doi:10.1126/science.1259627；另见 *Psychological Science* 27 (2016), doi:10.1177/0956797616631113）。
- **另一组实测（已核验，读到 Michel et al. 2011 全文）**：
  - 名人轨迹（1865 年出生队列的中位轨迹）：初次成名 34 岁、随后上升的**倍增时间 4 年**、**峰值在出生后约 70 年**、峰值后遗忘阶段的**半衰期 73 年**。
  - 跨队列趋势：初次成名年龄从 43 岁降到 29 岁，倍增时间从 8.1 年降到 3.3 年，峰值年龄稳定在出生后约 75 年。
  - 对"年份"的关注：'1880' 用 32 年衰减到峰值一半，'1973' 只用 10 年 → **文化周转在加速**。
- **建模建议**：`fame(person, t)` = 峰值 × 指数衰减（半衰期量级 70–100 年）+ **首位/创建者的 primacy 加成** + 近期性加成。用"距今第几位继任者"而不是绝对年数作自变量，能自动适应不同的政权更替速度。
- **证据等级**：**A**（有实测参数，但全部来自现代西方，外推到前现代社会需要标为假设）。

---

### M9. 抄写传承与文本谱系（stemma）

- **输入**：一部作品的副本树；每次抄写引入的变异。
- **输出**：版本差异矩阵；后世校勘者可重建的谱系（可能错）。
- **算法**：每次抄写 $c'\leftarrow \text{mutate}(c)$，变异包括：随机字词错误、跳行（saut du même au même）、有意识的"改正"、注释混入正文、避讳性替换。
- **可复用的形式方法**：把抄本当作分类单元、变异当作性状，用系统发生学方法建 stemma —— **已核验**：Barbrook, Howe, Blake & Robinson, "The phylogeny of *The Canterbury Tales*", *Nature* 394 (1998), doi:10.1038/29667；方法论辩护见 Howe, Connolly & Windram, "Responding to Criticisms of Phylogenetic Methods in Stemmatology", *SEL* 52 (2012), doi:10.1353/sel.2012.0008。
- **对我们的价值**：世界内的历史学家 agent 可以**真的跑这个算法**——我们的模拟天然拥有真实 stemma（L0 侧），可以直接测量 agent 重建得对不对。这是一个漂亮的、内建的"史学方法有效性"实验台。
- **附带的偏见机制**：Simkin & Roychowdhury 用引文中错印的传播证明大量引用者**并未读过原文而是复制了引文** —— *Significance* 3 (2006), doi:10.1111/j.1740-9713.2006.00202.x。同样的机制可以用来生成"错误在学术传统中固化"的现象。
- **证据等级**：**A**（方法本身）/ **B**（变异率无可用参数）。

---

### M10. 文字的出现：不用科技树，用条件 + 低概率触发 + 刺激扩散

- **状态前提（都必须由更基础的机制自己长出来）**：
  - **P1 持久图形标记实践**：计数刻符、陶工记号、所有权标记。这**不是**文字。经验支撑：贾湖（Jiahu）龟甲刻符被判定为与仪轨相关的符号使用而非文字（**已核验，读到摘要原文**：Li Xueqin, Harbottle, Zhang & Wang, "The earliest writing? Sign use in the seventh millennium BC at Jiahu, Henan Province, China", *Antiquity* 77 (2003), doi:10.1017/s0003598x00061329）。Demattè 2022 的整书结构也把"新石器符号系统"与"文字"分成不同章节处理（**已核验章节结构**：*The Origins of Chinese Writing*, OUP, doi:10.1093/oso/9780197635766.001.0001；含 "Early and Middle Neolithic Signs to the Fourth Millennium BCE"、"The Third Millennium BCE: Late Neolithic Sign Systems"、"The Second Millennium BCE: Early and Middle Bronze Age Writing"、"Characteristics of Shang Writing"、"What Is Writing?"）。
  - **P2 高频、结构化、模板化的记录需求**：行政记账（Uruk）或制度化占卜（商）。
  - **P3 专业记录者群体 + 训练机制**（不是全民识字）。经验支撑：Anyang 存在书写训练的证据 —— Smith, "The Ernest K. Smith Collection of Shang Divination Inscriptions at Columbia University and the Evidence for Scribal Training at Anyang", in *Archaeologies of Text*, doi:10.2307/j.ctvh1ds1j.9（**已核验元数据**）。
- **触发**：**语音转写（rebus）的发明**是一个低概率创新，其发生率应正比于"P1 × P2 的累积记录活动量"，而不是一个时间节点。
  $$\Pr(\text{phoneticization in }\Delta t)=1-\exp\big(-\kappa\cdot\text{records\_produced}\cdot\text{sign\_inventory}\cdot\Delta t\big)\quad\text{[形式 D 级]}$$
- **第二条完全不同的路径：刺激扩散（stimulus diffusion）**。只要一个 agent **见过**"文字这种东西存在"，他就可能自己造一套。这条路径的发生率比从零发明高**几个数量级**。经验支撑（**已核验，读到摘要原文**）：Kelly, "The invention, transmission and evolution of writing: Insights from the new scripts of West Africa", 2017, doi:10.31235/osf.io/253vc —— 西非自 1830 年代以来出现**多达 20 种**新创文字，其中**至少 3 种由没有受过正规识字教育的个人发明**（与 Cherokee 音节文字同一模式）；这些文字随后被用来"划出一种与殖民行政话语相对立的政治—宗教话语空间"。
- **对我们的直接含义**（这是本条最重要的一句）：
  - **文字的第一次发明**极稀有，需要 P1+P2+P3 同时具备；
  - **文字的后续发明**只需要接触 + 一个有动机的个人，而且**动机常常是政治/宗教认同，不是效率**。
  - 所以我们的世界里应该出现：少数几个"原生文字"，加上大量"因为想跟邻居区分开而造的文字"。这完全符合纲领"涌现而非科技树"的要求。
- **证据等级**：**B**（三前提 + 两路径都有直接文献支撑；$\kappa$ 无参数，D 级）。

---

### M11. 文字**不是**棘轮：脚本可以死，识字可以退

- **机制**：脚本 $s$ 的存续依赖于消费它的制度。若制度消失且没有其他消费者接手，$s$ 的活跃使用者数量按人口更替速度衰减到零；此后 $s$ 的现存文本变为**不可读的 Trace**。
- **对我们的含义**：引擎必须支持"某文明有文字 → 崩溃 → 数百年后无人能读自己祖先的碑刻"。这会产生极好的历史叙事素材（后世把不可读的碑刻解释成神迹/咒语）。
- **反向机制**：脚本复兴/解读（世界内的"商博良事件"）——需要双语文本或大量语料 + 有闲暇的学者阶层。
- **一个反常识的经验发现（已核验，读到 PMC 全文）**：**不要假设字形会随时间自动简化。** Miton & Morin 在 133 种文字、47,880 个字符上做的定量研究发现：字符的图形复杂度主要由它编码的语言单位（音素/音节/词）决定；**"几乎没有证据显示字符复杂度随演化而改变"**；字符集越大，字符越复杂（$\beta=0.12$, 95%CI[0.073, 0.175], $t=4.78$, $p<0.001$）。见 Miton & Morin, "Graphic complexity in writing systems", *Cognition* 214 (2021), doi:10.1016/j.cognition.2021.104771；配套的 Kelly, Winters, Miton & Morin, "The Predictable Evolution of Letter Shapes", *Current Anthropology* 62 (2021), doi:10.1086/717779。
- **证据等级**：**B**（脚本死亡）/ **A**（字形复杂度的定量结论）。

---

### M12. 识字：不是一个标量，是一个"实践 × 阶层"矩阵

- **建议的状态变量**：`literacy[practice][stratum] ∈ [0,1]`，practice ∈ {计数记账, 仪式书写, 行政文书, 契约, 书信, 经典阅读, 文学创作}。
- **理由**：Goody & Watt 1963 的"识字的后果"提出了强版本的技术决定论（**已核验**：*Comparative Studies in Society and History* 5 (1963), doi:10.1017/s0010417500001730），但被 New Literacy Studies 系统性反驳：不存在单一的"自主的（autonomous）识字"，识字总是嵌在具体社会实践中的复数形态（**已核验**：Street, "Literacy in Theory and Practice: Challenges and Debates Over 50 Years", *Theory Into Practice* 52 (2013), doi:10.1080/00405841.2013.795442）。
- **可用的增长量级锚点（已核验，读到摘要原文）**：西欧 6–18 世纪，手稿与印本的产量长期**年均增长率约 1%**；15 世纪中叶后产量上升，很可能源于书价下降与识字率上升；早期需求以修道院为主，中世纪后期转为大学与俗人。Buringh & van Zanden, "Charting the 'Rise of the West'", *Journal of Economic History* 69 (2009), doi:10.1017/s0022050709000837。
- **警告**：清代识字率的经典估计来自 Rawski 1979，但**本次检索未能取得该书正文或任何给出具体百分比的可核验来源**，只核验到该书存在及其被广泛评论的事实（Elvin, *China Quarterly* 1980, doi:10.1017/s0305741000012224；Kessler, *AHR* 1980, doi:10.2307/1853579；Stephens, *Comparative Education Review* 1981, doi:10.1086/446196），以及后续论文集 Elman & Woodside (eds), *Education and Society in Late Imperial China, 1600–1900*, UC Press 1994, doi:10.1525/9780520913639（含 Afterword "The Expansion of Education in Ch'ing China"）。**因此本简报不给出任何清代识字率数字。**
- **证据等级**：**B**（多元识字观）/ 数字层面 **文献未提供本次可核验的参数**。

---

### M13. 世界内历史学家 agent 的信息条件与工作流程

这是用户特别要求回答的部分。

**Historian agent 在 $t$ 时刻可读的东西，严格限定为：**
1. `SurvivingCorpus(t)` 中他**物理上能到达**的仓储里的 L2 记录（受地理、政治边界、门第、语言、脚本可读性、access_policy 限制）；
2. 他所在社群流通的 L3 叙事；
3. 若该社会已发明"古物学/考古"实践，则加上已被发现的 L1 痕迹；
4. 其他历史学家的 L4 产出。

**他绝对读不到：** L0；任何未被发现的 L1；任何他不可达仓储中的 L2；任何 `truth()` 标记。

**他的工作流程（规则系统与 LLM 的分工）：**

| 步骤 | 谁来做 | 说明 |
|---|---|---|
| 收集：枚举可达文献 | **规则** | 纯查询，不能让 LLM"想起"一份不存在的文献 |
| 校勘：对齐同一作品的多个版本，建 stemma | **规则**（跑 M9 的算法） | 可计算，且我们能对照 L0 打分 |
| 辨伪：检测时代错置、内部矛盾、可疑传承 | **混合** | 规则给出可检测的异常清单；LLM 判断其史学意义 |
| 权衡冲突证据 | **混合** | 规则给出各来源的独立性与动机向量；LLM 写论证 |
| 产出叙述 | **LLM** | 但每条断言必须挂 provenance 到具体的 L2/L1 对象 |
| 该叙述成为新的 L3/L4 对象 | **规则** | 进入抄写/存活/变形的正常流程 |

**引擎侧应计算并存储（agent 不可见）的诊断量：**
- **真值偏离** $D(t)=d\big(\text{主流叙事}(t),\ L0\big)$，按命题加权。
- **可知性上界** $U(t)$：在 $t$ 时刻的存活语料下，任何完美推理者最多能恢复多少 L0。**$D(t)-U(t)$ 才是"史学水平"，$U(t)$ 本身是"史料条件"。** 这个分解让我们能回答"这个文明的历史学家是笨，还是史料真的没了"。
- **虚构率**：主流叙事中 `truth == false` 的命题占比。

**为什么这样简化**：真实史学方法论的教科书化描述（外部批判/内部批判、来源独立性、动机分析）足够稳定，可以直接编码。参考 Howell & Prevenier, *From Reliable Sources: An Introduction to Historical Methods*, Cornell UP 2001（**已核验，通过书评 doi:10.1162/00221950260208733**）。

- **证据等级**：**B**（史学方法本身）/ **D**（整套 agent 架构是我们的设计）。

---

### M14. 年代学必须在世界内部被构建，不能免费给出

- **机制**：世界内的日期是**相对的、多套并行的、需要被同步的**：王年、干支类循环、天文事件、地层。绝对年代表是一个**史学成果**，可能是错的。
- **真实世界的教训（已核验元数据）**：夏商周断代工程的方法与结论 —— Li Xueqin, "The Xia-Shang-Zhou Chronology Project: Methodology and Results", *Journal of East Asian Archaeology* 4 (2002), doi:10.1163/156852302322454585；碳十四框架 Qiu Shihua & Cai Lianzhen, *Chinese Archaeology* 2 (2002), doi:10.1515/char.2002.2.1.6；天文学部分 Liu, *JAHH* 5 (2002), doi:10.3724/sp.j.1440-2807.2002.01.01；wiggle-matching 方法 Zhang & Qiu, *Chinese Archaeology* 7 (2007), doi:10.1515/char.2007.7.1.183；以及后续对其争议的讨论 Li Boqian, "The Xia-Shang-Zhou Chronology Project and Archaeological Research on the Xia Dynasty", in *Myth and the Making of History*, 2024, doi:10.1515/9781438497709-006。
- **技术侧对应物**：现实中的校准曲线 IntCal20 / SHCal20（**已核验**：Reimer, "Composition and consequences of the IntCal20 radiocarbon calibration curve", *Quaternary Research* 96 (2020), doi:10.1017/qua.2020.42；Heaton et al., *Radiocarbon* 62 (2020), doi:10.1017/rdc.2020.46；Hogg et al., SHCal20, *Radiocarbon* 62 (2020), doi:10.1017/rdc.2020.59）。校准曲线上的"平台段"会让某些世纪在测年上不可分辨——**我们可以在模拟里给"考古测年"加同样性质的不可分辨区间**，这会自然产生世界内的年代争议。
- **证据等级**：**B**。

---

## 4. 硬数字与参数表

只列本次检索中真实读到的数值。**没有来源的一律不写数字。**

| 量 | 数值 | 单位 | 适用时空范围 | 不确定度 | 来源（均本次核验） |
|---|---|---|---|---|---|
| 中世纪骑士/英雄叙事**作品**存活率（六方言合并） | **68.3%** | — | 欧洲，中世纪→今 | CI [63.2%, 73.5%]；Chao1 是下界估计量，故此为损失上界 | Kestemont et al. 2022, *Science*, doi:10.1126/science.abl7655（读到全文 Table 1 与正文） |
| 同上，**抄本**存活率 | **9.0%** | — | 同上 | CI [7.5%, 10.7%] | 同上 |
| 抄本存活率的方言区间 | **4.9%（English）– 19.2%（Irish）** | — | 同上 | 点估计 | 同上，Table 1 |
| 作品存活率的方言区间 | **38.6%（English）– 81.0%（Irish）** | — | 同上 | 点估计 | 同上，Table 1 |
| 六方言合并的原始规模 | 原 **1,170** 部作品 / **40,614** 件抄本；今存 **799** / **3,648** | 件 | 同上 | 点估计 | 同上 |
| 传统书史学的手稿存活率 | **7%**（普通抄本）；**20%**（高端抄本） | — | 神圣罗马帝国 | 依赖少量图书馆目录，样本有偏 | Kestemont et al. 2022 引述其参考文献 (1, 11, 15) |
| 单件作品的抄本数分布 | **极不均匀（重尾）**；均匀度决定语料抗冲击能力 | — | 同上 | 定性但被定量化为 evenness profile | 同上，Fig. 5 与讨论 |
| 楔形文字实物总量 | 公私收藏合计 **>500,000** 件；CDLI 已电子编目 **>400,000** 件 | 件 | 西亚，约前 3350 年起 | 机构自述 | CDLI "About" 页，https://cdli.mpiwg-berlin.mpg.de/about（2026-09-10 抓取） |
| CDLI 目录中 Uruk IV 期文物条目 | **1,892** | 条 | 约前 3350–3200 | 目录检索结果，非发掘总数 | CDLI 检索接口（2026-09-10） |
| CDLI 目录中 Uruk III 期文物条目 | **5,921** | 条 | 约前 3200–3000 | 同上 | 同上 |
| 甲骨出土总量 | 约 **160,000** 片 | 片 | 商，殷墟 | 综述性数字 | Wang, Zhang, Wang & Han, *Scientific Data* 11 (2024), doi:10.1038/s41597-024-03807-x（读到正文） |
| 甲骨中可区分的字符数 | **>4,600** 种 | 种 | 同上 | — | 同上 |
| 已释读的甲骨字符数 | **约 1,000**（正文另一处作"约 1,500 类已释读"） | 种 | 同上 | 文内两处表述略有差异 | 同上 |
| HUST-OBC 数据集规模 | **140,053** 图像；已释读 **1,588** 类 / **77,064** 图；未释读 **9,411** 类 / **62,989** 图 | — | — | 未释读类别间可能有重复 | 同上 |
| 西欧书籍产量长期增长率 | **约 1%/年** | 年增长率 | 西欧，6–18 世纪 | 长期平均 | Buringh & van Zanden 2009, *JEH*, doi:10.1017/s0022050709000837（摘要） |
| Google Books 语料规模 | **5,195,769** 册，约占**人类曾出版书籍的 4%** | 册 | 1800–2000 为主 | 自述 | Michel et al. 2011, *Science*, doi:10.1126/science.1199644（全文） |
| 对"某一年份"的注意力半衰期 | '1880' → **32 年**；'1973' → **10 年** | 年 | 英语书籍，19–20 世纪 | 逐年缩短 | 同上 |
| 名人声望轨迹（1865 出生队列中位数） | 初次成名 **34 岁**；上升期倍增时间 **4 年**；峰值在出生后 **约 70 年**；峰值后遗忘半衰期 **73 年** | 年 | 英语书籍 | 中位轨迹 | 同上 |
| 名人成名的长期趋势 | 初次成名年龄 **43 → 29 岁**；倍增时间 **8.1 → 3.3 年**；峰值年龄稳定在出生后 **约 75 年** | 年 | 19 世纪初 → 20 世纪中 | — | 同上 |
| 国家压制对提及率的削减幅度 | 历史类 **9%**、文学类 **27%**、艺术类 **56%**、政治类 **60%**、哲学类 **76%** | 相对下降 | 纳粹德国 1933–1945，德语书籍 | 各组名单规模：艺术 100、文学 147、政治 117、历史 53、哲学 35 人 | 同上 |
| 极端压制案例 | Marc Chagall 全名在 1936–1944 年德语书籍中**仅出现 1 次** | 次 | 同上 | — | 同上 |
| 集体记忆中领导者的遗忘形状 | 对在位者之前的 **8–9 位**前任呈**大致线性**遗忘 | — | 美国，1974/1991/2009/2014 四批被试（415 + 497 人） | 现代样本，外推需谨慎 | Roediger & DeSoto, *Science* 346 (2014), doi:10.1126/science.1259627（摘要） |
| 同上，外推 | Truman 约在 **2040 年**衰减到 McKinley 当前水平 | 年 | 同上 | 模型外推 | 同上 |
| 记录技术在社会复杂度中的位置 | 9 个复杂度特征两两相关 **0.49–0.88**；单一主成分解释 **约 3/4** 变异；样本外预测 $\rho^2$：Information system **0.59**、Texts **0.73** | — | 414 社会 / 30 地区 / 约 10,000 年 | 依赖专家编码与多重插补，有争议 | Turchin et al., PNAS 115 (2018), doi:10.1073/pnas.1708800115（全文） |
| 字形复杂度 | 字符集越大字符越复杂：$\beta=0.12$, 95%CI[0.073, 0.175], $t=4.78$, $p<0.001$；**未发现复杂度随演化而变化的证据** | — | 133 种文字，47,880 字符 | — | Miton & Morin, *Cognition* 214 (2021), doi:10.1016/j.cognition.2021.104771（全文） |
| 新文字的发明速率（有接触条件下） | 西非自 1830 年代以来 **多达 20 种**新文字；其中 **≥3 种**由非识字者独立发明 | 种 | 西非，1830s–2002 | 计数依 Dalby 等 | Kelly 2017, doi:10.31235/osf.io/253vc（摘要） |
| 印欧民间故事的时间深度 | **19** 个故事以 >50% 似然可回溯到较早祖先节点；在原始印欧语节点上仅 **4** 个试探性，贝叶斯最终仅支持 **1** 个（ATU 330 "The Smith and the Devil"，青铜时代） | — | 印欧语系 | 深节点支持很弱，作者自陈 | da Silva & Tehrani, *R. Soc. Open Sci.* 3 (2016), doi:10.1098/rsos.150645（全文） |

**明确的空缺（本次检索未能取得可用参数，不要编造）：**
- 各类介质（黏土、甲骨、竹木简、缣帛、纸、石、金属）在各类环境下的**年化降解率**。
- 中国历代**识字率**的可核验数值。
- 传世文献与出土文献的**相对存活率**。
- 抄写过程的**单次变异率**（每千字错字数）。
- MacMullen 的**铭文数量随年代分布曲线**的具体数字。
- serial reproduction 实验中每代**保留命题比例**的具体数值。
- 敦煌藏经洞写卷的确切数量（常被引用的"约 5 万件"本次未能核验）。

---

## 5. 数据集与数据库

| 名称 | 内容 | 覆盖范围 | 访问 / URL | 许可 | 本次是否验证可达 |
|---|---|---|---|---|---|
| **CDLI**（Cuneiform Digital Library Initiative） | 楔形文字文物的目录、转写、图像；按时期/出土地/收藏检索 | 约前 3350 年至基督纪元；>400,000 条编目 | https://cdli.mpiwg-berlin.mpg.de （另有 Periods 列表可导出 CSV/TSV/TTL/RDF-JSON） | 站点未在首页声明统一许可，需逐项确认 | **是**，抓取成功并做了期段计数 |
| **HUST-OBC** | 甲骨字符图像数据集：140,053 图，已释读 1,588 类 / 未释读 9,411 类 | 商代甲骨 | https://github.com/Pengjie-W/HUST-OBC ；论文 doi:10.1038/s41597-024-03807-x | 见 repo | **是**（repo 与论文均可达） |
| **Seshat: Global History Databank** | 414 社会 × 51 变量，含 Information system 与 Texts 两组"记录技术"变量；另有 CrisisDB、Power Transitions、Qing Crisis 等子库 | 近 10,000 年，30 个地区 | https://seshat-db.com （站点提供 Downloads / API / GitHub / Codebook / User Agreement） | 需接受 User Agreement | **是** |
| **D-PLACE** | 社会的文化特征 × 语言系统发生 × 生态环境的整合数据库 | 全球民族志社会 | https://d-place.org | **CC BY-NC 4.0**（站点声明） | **是** |
| **Kestemont et al. 2022 补充数据** | 六个欧洲方言骑士/英雄叙事的作品—抄本计数表（可直接拿来做存活模型的分布拟合） | 中世纪欧洲 | 随 *Science* 论文 doi:10.1126/science.abl7655 提供；作者机构仓储有 accepted manuscript（KU Copenhagen） | 见期刊 | **是**（论文全文取得；补充数据未单独下载） |
| **Google Books Ngram** | 约 5.2M 册书的 n-gram 频次时间序列（含中文语料） | 主要 1800–2000 | https://books.google.com/ngrams | Google 条款 | **是**（页面可达） |
| **IntCal20 / SHCal20 + OxCal** | 放射性碳年代校准曲线与贝叶斯年代建模工具 | 0–55,000 cal BP | https://c14.arch.ox.ac.uk/oxcal.html ；曲线论文 doi:10.1017/qua.2020.42, doi:10.1017/rdc.2020.46, doi:10.1017/rdc.2020.59 | 学术使用 | **是** |
| **IntChron** | 考古年代学数据的互操作交换框架 | 全球 | https://intchron.org | — | **是**（仅确认可达，未核内容） |
| **DOAJ API** | 开放获取期刊文章检索（本次用作补充检索通道） | 全球 OA | https://doaj.org/api/search/articles/{query} | 开放 | **是** |
| **Crossref REST API / Unpaywall API** | 书目元数据 + OA 全文定位。**建议把这两个接口固化进项目的引用核验流程** | 全学科 | https://api.crossref.org ；https://api.unpaywall.org/v2/{doi}?email= | 开放 | **是**（本简报的核验基础设施） |
| CBDB（China Biographical Database） | 中国历代人物传记、亲属、官职、社会关系 | 唐宋至清 | cbdb.fas.harvard.edu | — | **否**，本次访问被 Akamai 拒绝，内容与规模**未核验** |
| CHGIS（China Historical GIS） | 中国历史行政区划时空数据 | 秦至清 | — | — | **否**，未访问成功 |
| IDP（International Dunhuang Programme） | 敦煌及丝路写卷、绘画、文物的高清图像与编目 | 4–11 世纪 | idp.bl.uk | — | **否**，403；规模数字**未核验** |
| CTEXT（中国哲学书电子化计划） | 汉籍全文与版本 | 先秦至清 | ctext.org | — | **否**，连接失败 |
| Trismegistos | 古代地中海文本与人物的元数据 | 前 800–后 800 | trismegistos.org | — | **否**，403 |
| ATU Index（Uther 2004） | 国际民间故事类型目录——**"叙事吸引子"的实测清单** | 全球（欧亚为主） | 非在线开放数据集，需用书 | 版权 | 仅通过书评核验存在（doi:10.30666/elore.78537） |

---

## 6. 中国与东亚特定证据

这一节的目的不是"照抄中国史"，而是给建模者一组**真实存在过的机制样本**，用来检验我们的内核能不能长出类似的东西。

### 6.1 符号 ≠ 文字：新石器刻符与商代文字之间的断裂

- 贾湖龟甲刻符（约前 7 千纪）被判定为**与仪轨相关的符号使用，而非文字**，但被视为一条最终导向文字系统的长期符号使用传统的开端（Li Xueqin et al. 2003，*Antiquity*，**已核验摘要原文**）。
- Demattè 2022 的整书结构（**已核验章节列表**）把"早中期新石器符号"、"三千纪晚期新石器符号系统"、"二千纪早中期青铜时代书写"、"商代书写的特征"分列为独立阶段，并单设 "What Is Writing?" 一章讨论判据。
- **建模含义**：我们的引擎必须能表达"存在了三四千年的符号使用传统，但一直没有跨过语音转写门槛"这种状态。这直接支持 M10 的"低概率触发 + 累积记录活动量"设计，而不是"到某个科技点就解锁文字"。
- Boltz 的经典论述（*The Origin and Early Development of the Chinese Writing System*, AOS 78, 1994）本次通过两篇书评核验其存在与出版信息（Bottéro, *JAOS* 1996, doi:10.2307/605196；Packard, *Language* 1996, doi:10.2307/416104），另核验其早期论文 Boltz, "Early Chinese writing", *World Archaeology* 17 (1986), doi:10.1080/00438243.1986.9979980。**原书论点本次未读到，不做转述。**

### 6.2 商代甲骨：一个"制度化占卜"驱动的记录系统

- 规模：约 **160,000 片**出土，**>4,600** 个可区分字符，**仅约 1,000（另说约 1,500 类）已释读**（*Scientific Data* 2024，**已核验**）。
- 存在**书吏训练**的物质证据（Smith 2014, in *Archaeologies of Text*，**已核验元数据**）。
- **建模含义**：
  1. 一个成熟文字系统可以在**没有大众识字**、**没有商业记账**的条件下运转——它的宿主是宗教—王权制度。这打破了"文字必然由贸易催生"的单一路径假设。
  2. **释读率约 20–30%** 是一个极好的"后世可知性上界"参照：即使一个文明留下了十几万件同类文本，后世也可能只能读懂其中不到三分之一的字符。我们的 historian agent 应当面对同量级的困难。

### 6.3 出土文献 vs 传世文献：中国史料的双通道结构

这是全世界最清楚的"沉积通道 vs 传承通道"案例集，也是 M3 的经验基础。

- **里耶秦简**：湖南龙山里耶一号井出土的秦迁陵县行政档案，涉及军事后勤、法律（罚金与刑罚、赏赐、刑徒口粮、身份区分、买爵）、文书格式、令、地方官吏的宗教活动；*Early China* 的介绍文章明确以"推测这批文书为何在秦王朝开始崩溃时被扔进井里"作结（**已核验摘要原文**，doi:10.1017/s0362502800000523）。另有对其中私人书信的研究（Lü, *Bamboo and Silk* 2025, doi:10.1163/24689246-20250016）与"其他邮书简"研究（Tsuchiguchi 2022, doi:10.1163/24689246-00402018）。
- **睡虎地秦简**：法律文书类，*Falü Dawen* 中的死刑术语研究（Tang, *Bamboo and Silk* 2022, doi:10.1163/24689246-20220024）；相关的墓主身份与聚落研究（Chen & Cai 2020, doi:10.1163/24689246-00302003）。
- **走马楼吴简**：长沙出土的三国吴地方行政简牍，规模巨大，专门研究见 Lander, Ling & Wen, *State and Local Society in Third Century South China*, Brill 2024，含 "The World of the Zoumalou Documents" (doi:10.1163/9789004549654_003) 与 "The Excavation and Collation of the Wu Slips" (doi:10.1163/9789004549654_004)。
- **郭店与清华简**：战国竹书，改写了对早期思想史的理解（*Dao Companions to Chinese Philosophy* 2019 的多篇，如 Chan, "Introduction: The Excavated Guodian Bamboo Manuscripts", doi:10.1007/978-3-030-04633-0_1；Cook, "The Debate Over Coercive Rulership and the 'Human Way' in Light of Recently Excavated Warring States Texts", doi:10.1007/978-3-030-04633-0_15）。
- **竹书纪年**（Bamboo Annals）：西晋时从战国墓中出土的编年史，其年代与事件叙述与《史记》系统冲突，至今存在 Nivison–Shaughnessy 之争（**已核验**：*The Nivison Annals*, De Gruyter 2018, ch. 22 "The Nivison-Shaughnessy Debate on the Bamboo Annals (Zhushu jinian)", doi:10.1515/9781501505393-022；另 ch. 14 关于"今本"问题, doi:10.1515/9781501505393-014）。
- **敦煌藏经洞**：写卷在洞窟被封存后长期与流通通道隔绝，20 世纪初被发现并分散到多国（Rong Xinjiang, *Eighteen Lectures on Dunhuang*, Brill 2013, Lecture 3 "The Discovery of the Dunhuang Cave Library and Its Early Dispersal" doi:10.1163/9789004252332_005；Lecture 4 "The Nature of the Dunhuang Library Cave and the Reasons for Its Sealing" doi:10.1163/9789004252332_006）。**Lecture 4 的标题本身告诉我们："洞为什么被封"是一个可以被世界内学者研究的问题——这正是我们希望 historian agent 能提出的那类问题。**

**总结成一条工程规则**：一个文明的史料应当至少有两条互不相同的通道。它们的**体裁分布不同、偏差方向不同、发现时间不同**。当第二条通道在数百年后被打开时，世界内的历史学必须发生一次可追溯的重构。

### 6.4 官修史的多级流水线与制度化改写

- 唐代的七级链条见 2.9（Twitchett 1992 章节结构，**已核验**）。
- 明代：《太祖实录》的多次改修与 Xie Jin 的宣传角色（Chan 2005, *T'oung Pao*, doi:10.1163/1568532054905142）；永乐朝对历史的系统性改写以使篡位合法化（Chan 2023, doi:10.4324/9781003420842-8）；关于实录的公开政治论争（Ditmanson 2020, doi:10.1163/9789004423626_003）。
- 清初：从《旧满洲档》到《满洲实录》的编纂与改订（김선민 2012, doi:10.16957/sa..77.201209.139）。
- 《明实录》被用作**外部**史源（东南亚史）的研究，说明官修史即使有偏，其"顺带记录"的部分仍有独立价值（Wade, HKU dissertation, doi:10.5353/th_b3123394）。
- **建模含义**：
  1. 改写发生在**编纂链的特定环节**，而不是"改历史书"这一个动作。我们应当把改写实现为对某一级 pipeline 节点的操作，其效果向下游传播，但**上游的原始材料若仍存在，就留下矛盾**。
  2. 改写是**公开可争论**的政治行为，会产生自己的记录（关于改写的争论本身被记录下来了）。这提供了后世史学的检测线索。
  3. 官修史的**副产品**（外国、边疆、经济的顺带记载）偏差最小，因为没人有动机去改。**建模上：motive_vector 是分主题的，不是整篇文档一个标量。**

### 6.5 年代学：世界内的绝对年表是一个有争议的科研成果

见 M14。夏商周断代工程是"国家资助的年代学项目 → 得出一套年表 → 在国内外引发方法论争议"的完整样本（Li Xueqin 2002；Li Boqian 2024 等，**均已核验元数据**）。我们的世界完全应该出现这种事件：一个国家出资建立"官方年表"，而它同时是科学成果和政治工程。

---

## 7. 学界争议与未解决问题

1. **文字起源是否单一驱动（行政记账）**。Schmandt-Besserat 的 token 路径只解释两河；埃及的早期文字有强烈的展示/王权功能（Baines, "Communication and display: the integration of early Egyptian art and writing", *Antiquity* 63 (1989), doi:10.1017/s0003598x00076444，**已核验元数据**）；商代由占卜驱动。**争议未解决。** 我们的对策：不预设单一驱动，把 P1/P2/P3 做成可由不同制度满足的抽象条件。
2. **早期文字"仪式性"是真实功能还是保存假象**。Postgate/Wang/Wilkinson 1995 主张是假象（**已核验**）。这个争议对我们**不是障碍而是设计目标**——我们的引擎应当能同时生成真实功能分布和被过滤后的观测分布。
3. **中国新石器刻符与商代文字是否连续**。Li Xueqin et al. 2003 倾向"预示但非文字"；Demattè 2022 的分章结构显示这仍是需要专门论证的问题。**C 级。**
4. **口传能否跨越数千年保存事件信息**。Nunn & Reid 的 7000 年主张 vs Henige 对口传年代学的根本否定。da Silva & Tehrani 的定量结果（深节点支持很弱）恰好落在中间：**母题能存活，事件不能**。**C 级。**
5. **识字的"后果"是自主的还是被社会实践决定的**。Goody & Watt 1963 vs Street 及 New Literacy Studies。**建模上采用后者（多元识字矩阵），因为它更保守、更不容易产生虚假的技术决定论涌现。**
6. **Seshat 类跨文明数据库的编码可靠性**。Whitehouse et al. 2019 争议（Slingerland et al. 2019；*JCH* 2022 专辑）。**结论：Seshat 只能当校准的软约束，不能当基准真值。**
7. **系统发生学方法用于文本/故事谱系是否有效**。Barbrook et al. 1998 开创，Howe et al. 2012 为其辩护，说明有实质批评存在（污染/contamination 破坏树状假设）。**我们的模拟反而能给这个方法论争议提供一个可控实验台。**
8. **MCI（最小反直觉）效应的稳健性**。Norenzayan et al. 2006 提出 2–3 个反直觉元素最优，但后续如 Upal, "Memory, Mystery and Coherence" (*JoCC* 2011, doi:10.1163/156853711x568671) 与 Harmon-Vukić & Upal (2020, doi:10.1558/jcsr.39064) 对情境效应提出修正。**C 级：方向可用，最优值不可当参数。**
9. **清代及前现代中国识字率的量级**。Rawski 1979 与其批评者的争论至今没有共识数字，**本次也未取得任何可核验的数值**。
10. **各类书写材料的量化降解率**。本次检索**没有找到**可用于建模的年化降解参数。这是一个真实的文献空白，不是我检索不到。

---

## 8. 反模式：本领域常见的错误建模方式（我们必须避免的）

1. **把文字做成科技树节点**。错在两处：(a) 文字可以**消失**（脚本死亡、识字退化）；(b) 文字可以被**同一世界内多次独立发明**，且后续发明主要靠刺激扩散和政治认同动机（Kelly 2017：西非 180 年内 20 种）。失真后果：世界会呈现单调的"技术进步"感，永远不会出现"读不懂祖先碑刻"这种极有价值的历史情境。
2. **把识字率做成单一标量并让它线性驱动一切**。真实的识字是"实践 × 阶层"矩阵（Street）。失真后果：会产生"识字率到 30% 就出现公共舆论"这类隐藏的剧情触发器。
3. **假设"留下来的记录"≈"当时的记录"**。这是本领域最致命的错误。抄本存活率量级只有 **5%–20%**，且损失**不是随机的**——耐久媒介、受保护仓储、被反复抄写的正典被系统性放大（Kestemont 2022；Postgate et al. 1995）。失真后果：世界内的历史学家会显得过于全知，"世界事实与叙事分离"这条纲领原则会名存实亡。
4. **让记录量正比于人口或事件重要性**。记录是**制度惯例**的产物（epigraphic habit）。失真后果：不会出现"一个大帝国几乎没留下文字记载"或"一个小城邦留下海量档案"这类真实存在的格局。
5. **假设记忆保真度随时间单调衰减**。真实口传是非单调的（floating gap：近期清晰 + 起源清晰 + 中段空洞）。失真后果：世界不会产生"创世/建国神话极详细而中间三百年一片空白"这种最典型的前文字社会记忆结构。
6. **把篡改实现为对历史数据库的全局 UPDATE**。真实的压制受副本分散度限制，且**领域相关**（历史类 9% ↔ 哲学类 76%，Michel et al. 2011）。失真后果：会出现"某个皇帝一键抹掉了一个世纪"，既不真实，也毁掉了后世史学的推理素材。
7. **只建一条记录链（官修史）**。真实世界并行存在官方、私家、宗教、商业、家族、外邦六类记录，它们的动机向量互不相同。失真后果：所有叙事冲突都退化为"官方 vs 真相"的二元，失去层次。
8. **把 motive_vector 挂在文档级而不是主题级**。同一部官修史里，关于本朝合法性的部分极度偏颇，而关于边疆物产的部分可能相当可靠（《明实录》被用作东南亚史料即为例证）。
9. **把神话/传说当作"噪声"**。它们是有结构的吸引子（ATU 类型、MCI 结构、社会信息偏见）。失真后果：LLM 会生成随机的怪谈，而不是**可被预测、可被解释**的类型化叙事。
10. **假设字形/文字会自动简化**。133 种文字的定量研究**没有发现**复杂度随演化改变的证据（Miton & Morin 2021）。
11. **把考古证据当成"中立的第二意见"**。出土语料有它**自己的**、与传世语料完全不同的偏差（沉积通道只保留了被抛弃/被埋葬的东西）。失真后果：会让 historian agent 用考古"证伪"文献时过于顺利。
12. **免费提供绝对年表**。真实世界里绝对年代是史学成果，可能错，且会引发政治化争议（夏商周断代工程）。失真后果：世界内的历史学少了一整个最重要的问题域。
13. **让 historian agent 拥有全局 ID 检索**。哪怕只是"查询所有 event 的列表"，也等于给了上帝视角。**必须让检索本身受仓储可达性、语言、脚本可读性和 access_policy 约束。**
14. **让 LLM 直接判定"实际上发生了什么"**。违反纲领第 5 条。LLM 可以写史论、可以选择相信哪个来源、可以编造，但 `truth()` 只能由 L0 决定。
15. **在真实史料缺失的地方推断"什么都没发生"**。我们自己在建模时也会犯这个错——比如因为找不到某地的记载，就在模拟里让那个区域"什么都不发生"。
16. **忘记 feedback 污染**。一旦世界内有了书面史，口传会被书面史反向重写（Henige 的 feedback）。两个层不再独立，不能各自独立采样。

---

## 9. 无源判断（D 级：LLM 常识与工程假设，不得当作历史规律）

以下全部是我为了让模拟能跑而提出的假设，**没有文献来源**，必须在实现时标注为可调参数并在敏感性分析中测试：

1. **四层数据结构（L0/L1/L2/L3 + L4 递归）本身**是我的设计，不是学界共识的模型。
2. M1 中记录生产的 Poisson 形式与 $\lambda_g$ 的取值。
3. M2 中 $h_{\text{mat}}$ 的具体数值、仓储冲击的 Poisson 强度、$\delta_j$ 的取值。文献只给了**结果区间**（抄本 5%–20% 存活），没有给出生成过程的参数。我建议的做法是：**反过来标定**——先设定副本数的重尾分布形状，再调 $h$ 与冲击强度，直到千年尺度的抄本/作品存活率落进 Kestemont 的区间。
4. M3 中"沉积事件"把危险率降低多少倍（$r_{\text{fire}}, r_{\text{anox}}$），以及发现概率 $p_{\text{discovery}}$。
5. M5 中所有变形算子的函数形式与全部 $\beta$ 数值。只有**符号**有来源。
6. M6 中 $\tau_1 = 60\text{–}100$ 年、"中段近零"的具体形状、$A_{\text{charter}}$ 不衰减的假设。Vansina 的 floating gap 我**没有读到原文**。
7. "一代 = 25–30 年"。
8. M7 中 `cover` → 结果的映射规则、检测概率的函数形式。领域相关系数我建议用 Michel et al. 的 0.09–0.76 作为**先验区间**，但把它从"1930 年代德国书籍提及率"外推到"前现代抄本世界"这一步，是我的假设。
9. M8 中"用继任者序号而非绝对年数作自变量"是我的建议；文献只给了绝对年数。把美国总统的遗忘曲线外推到前现代王朝，是我的假设。
10. M10 中语音化触发率的指数形式与 $\kappa$。
11. M13 中"可知性上界 $U(t)$"这个诊断量的定义与计算方法。
12. "一个文明的史料应当至少有两条通道"——这是从中国案例归纳出的工程规则，不是普遍历史规律。
13. 把"叙事"表示为命题集合，这个表示本身丢掉了文体、情感、韵律等 Rubin 强调的约束维度。我建议用 `constraint_score` 这个标量近似它，**这是一个很粗的简化**。
14. 关于 Candia et al. 2018 (*Nature Human Behaviour*, doi:10.1038/s41562-018-0474-5) 的内容：我只核验到**标题、作者、年份、期刊**，该文非 OA，本次**没有读到任何正文或摘要**。我记忆中它提出集体记忆的双指数（communicative + cultural）衰减结构，但**这是未核验的回忆，不得作为参数来源使用**。
15. 敦煌写卷"约 5 万件"、CBDB 人物规模、IDP 编目规模等数字，本次均**未能核验**，本简报正文因此没有写入这些数字。

---

## 10. 参考文献

标注说明：**[V]** = 本次会话通过 Crossref/Unpaywall/DOAJ/直接抓取**真实取回**了元数据、摘要或全文；**[V-full]** = 读到了全文或实质正文段落；**[V-meta]** = 只核验了书目元数据（标题/作者/年份/期刊/DOI）；**[V-review]** = 通过同期书评核验了原著的存在与出版信息，但未读到原著；**[NV]** = 未核验。

### 文字的起源与性质
1. **[V-meta]** Schmandt-Besserat, D. (1992). "The Origin of Visible Language." In *Language Origin: A Multidisciplinary Approach*. doi:10.1007/978-94-017-2039-7_12
2. **[V-meta]** Schmandt-Besserat, D. & Feldbusch, E. (1991). "Clay Tokens as Forerunner of Writing: The Linguistic Significance." doi:10.1515/9783111353180.485
3. **[V-meta]** Wilding, D., Rowan, C., Maurer, B. & Schmandt-Besserat, D. (2017). "Tokens, Writing and (Ac)counting: A Conversation with Denise Schmandt-Besserat and Bill Maurer." *Exchanges* 5(1). doi:10.31273/eirj.v5i1.196
4. **[V-review]** Houston, S. D. (ed.). *The First Writing: Script Invention as History and Process*. — 经 Millard, A. (2006), *American Journal of Archaeology*, doi:10.3764/ajaonline1103.millard 核验。
5. **[V-full]** Postgate, N., Wang, T. & Wilkinson, T. (1995). "The evidence for early writing: utilitarian or ceremonial?" *Antiquity* 69. doi:10.1017/s0003598x00081874 （读到摘要原文） **[已核验]** — Crossref 确认：Antiquity 69(264), 459-480, 1995；Postgate, Wang, Wilkinson。
6. **[V-meta]** Baines, J. (1989). "Communication and display: the integration of early Egyptian art and writing." *Antiquity* 63. doi:10.1017/s0003598x00076444
7. **[V-meta]** Nissen, H. J. (1986). "The archaic texts from Uruk." *World Archaeology* 17(3). doi:10.1080/00438243.1986.9979973
8. **[V-meta]** Trigger, B. (1998). "Writing systems: A case study in cultural evolution." *Norwegian Archaeological Review* 31. doi:10.1080/00293652.1998.9965618
9. **[V-full]** Kelly, P. (2017). "The invention, transmission and evolution of writing: Insights from the new scripts of West Africa." SocArXiv. doi:10.31235/osf.io/253vc （读到摘要原文） **[已核验]** — Crossref 确认：Piers Kelly, 2017, SocArXiv preprint。
10. **[V-full]** Miton, H. & Morin, O. (2021). "Graphic complexity in writing systems." *Cognition* 214. doi:10.1016/j.cognition.2021.104771 （读到 PMC 全文） **[已核验]** — Crossref 确认：Cognition 214, 2021；Miton & Morin。
11. **[V-meta]** Kelly, P., Winters, J., Miton, H. & Morin, O. (2021). "The Predictable Evolution of Letter Shapes." *Current Anthropology* 62(6). doi:10.1086/717779

### 汉字起源与商代书写
12. **[V-full]** Li, X., Harbottle, G., Zhang, J. & Wang, C. (2003). "The earliest writing? Sign use in the seventh millennium BC at Jiahu, Henan Province, China." *Antiquity* 77. doi:10.1017/s0003598x00061329 （读到摘要原文） **[已核验]** — Crossref 确认：Antiquity 77, 2003；Li Xueqin, Harbottle, Zhang Juzhong, Wang Changsui。
13. **[V-meta]** Demattè, P. (2022). *The Origins of Chinese Writing*. Oxford University Press. doi:10.1093/oso/9780197635766.001.0001 （核验到完整章节结构）
14. **[V-review]** Boltz, W. G. (1994). *The Origin and Early Development of the Chinese Writing System*. AOS 78. — 经 Bottéro (1996) doi:10.2307/605196 与 Packard (1996) doi:10.2307/416104 核验。
15. **[V-meta]** Boltz, W. G. (1986). "Early Chinese writing." *World Archaeology* 17(3). doi:10.1080/00438243.1986.9979980
16. **[V-full]** Wang, P., Zhang, K., Wang, X., Han, S. et al. (2024). "An open dataset for oracle bone character recognition and decipherment." *Scientific Data* 11. doi:10.1038/s41597-024-03807-x （读到全文） **[已核验]** — Crossref 确认：Scientific Data 11, 2024；首作者 Pengjie Wang。
17. **[V-meta]** Smith, A. (2014). "The Ernest K. Smith Collection of Shang Divination Inscriptions at Columbia University and the Evidence for Scribal Training at Anyang." In *Archaeologies of Text*. doi:10.2307/j.ctvh1ds1j.9

### 记录的存活与幸存偏差
18. **[V-full]** Kestemont, M., Karsdorp, F., de Bruijn, E., Driscoll, M. et al. (2022). "Forgotten books: The application of unseen species models to the survival of culture." *Science* 375(6582). doi:10.1126/science.abl7655 （读到 KU Copenhagen 仓储全文 PDF，含 Table 1） **[已核验]** — Crossref 确认：Science 375(6582), 765-769, 2022；作者 Kestemont, Karsdorp, de Bruijn, Driscoll, Kapitan, Ó Macháin, Sawyer, Sleiderink, Chao。
19. **[V-full]** Buringh, E. & van Zanden, J. L. (2009). "Charting the 'Rise of the West': Manuscripts and Printed Books in Europe, A Long-Term Perspective from the Sixth through Eighteenth Centuries." *Journal of Economic History* 69(2). doi:10.1017/s0022050709000837 （读到摘要原文） **[已核验]** — Crossref 确认：Journal of Economic History 69(2), 2009；Buringh & van Zanden。
20. **[V-meta]** MacMullen, R. (1982). "The Epigraphic Habit in the Roman Empire." *American Journal of Philology* 103. doi:10.2307/294470 （**具体数字未取到**）
21. **[V-full]** Michel, J.-B., Shen, Y. K., Aiden, A. P., Veres, A. et al. (2011). "Quantitative Analysis of Culture Using Millions of Digitized Books." *Science* 331. doi:10.1126/science.1199644 （读到 PMC 全文） **[已核验]** — Crossref 确认：Science 331, 2011；Michel, Shen, Aiden, Veres et al.。

### 口传、记忆与传递中的变形
22. **[V-meta]** Vansina, J. (1985). *Oral Tradition as History*. University of Wisconsin Press. doi:10.2307/jj.36106057 **[已核验]**（Crossref 确认：Vansina, Univ. of Wisconsin Press, 1985, 专著；书目元数据无误，正文内容仍未核验）（**正文未读；"floating gap"的具体表述属未核验回忆**）
23. **[V-review]** Henige, D. (1974). *The Chronology of Oral Tradition: Quest for a Chimera*. Clarendon Press. — 经 Ekechi, *AHR* 1975 doi:10.2307/1852179；Yoffee, *American Anthropologist* 1975 doi:10.1525/aa.1975.77.2.02a01020；*JAH* 1976 doi:10.1017/s0021853700001353 核验。
24. **[V-meta]** Rubin, D. C. (1995). *Memory in Oral Traditions: The Cognitive Psychology of Epic, Ballads, and Counting-out Rhymes*. Oxford University Press. doi:10.1093/oso/9780195082111.001.0001
25. **[V-meta]** Thomas, R. (1989). "Genealogy and family tradition: the intrusion of writing." In *Oral Tradition and Written Record in Classical Athens*. Cambridge University Press. doi:10.1017/cbo9780511597404.004
26. **[V-meta]** Nunn, P. D. & Reid, N. J. (2015). "Aboriginal Memories of Inundation of the Australian Coast Dating from More than 7000 Years Ago." *Australian Geographer* 46(1). doi:10.1080/00049182.2015.1077539
27. **[V-meta]** Nunn, P. D. (2018). *The Edge of Memory: Ancient Stories, Oral Tradition and the Post-Glacial World*. Bloomsbury. doi:10.5040/9781472943255
28. **[V-full]** Mesoudi, A. & Whiten, A. (2008). "The multiple roles of cultural transmission experiments in understanding human cultural evolution." *Phil. Trans. R. Soc. B* 363. doi:10.1098/rstb.2008.0129 （读到 PMC 全文） **[已核验]** — Crossref 确认：Phil. Trans. R. Soc. B 363, 2008；Mesoudi & Whiten。
29. **[V-meta]** Bartlett, F. C. (1932/1995). "Experiments on Remembering: The Method of Serial Reproduction." In *Remembering*. Cambridge University Press. doi:10.1017/cbo9780511759185.010 及 .011
30. **[V-meta]** Roediger, H. L., Meade, M. L., Gallo, D. A. & Olson, K. R. (2008). "Bartlett Revisited: Direct Comparison of Repeated Reproduction and Serial Reproduction Techniques." doi:10.1037/e527312012-156
31. **[V-meta]** Mesoudi, A. & Whiten, A. (2004). "The Hierarchical Transformation of Event Knowledge in Human Cultural Transmission." *Journal of Cognition and Culture* 4. doi:10.1163/156853704323074732
32. **[V-meta]** Mesoudi, A., Whiten, A. & Dunbar, R. (2006). "A bias for social information in human cultural transmission." *British Journal of Psychology* 97. doi:10.1348/000712605x85871
33. **[V-meta]** Barrett, J. L. & Nyhof, M. A. (2001). "Spreading Non-natural Concepts." *Journal of Cognition and Culture* 1. doi:10.1163/156853701300063589
34. **[V-meta]** Boyer, P. & Ramble, C. (2001). "Cognitive templates for religious concepts." *Cognitive Science* 25(4). doi:10.1207/s15516709cog2504_2
35. **[V-meta]** Norenzayan, A., Atran, S., Faulkner, J. & Schaller, M. (2006). "Memory and Mystery: The Cultural Selection of Minimally Counterintuitive Narratives." *Cognitive Science* 30. doi:10.1207/s15516709cog0000_68 （**全文未取到；具体数值未核验**）
36. **[V-meta]** Upal, M. A. (2011). "Memory, Mystery and Coherence." *Journal of Cognition and Culture* 11. doi:10.1163/156853711x568671
37. **[V-meta]** Kashima, Y. (2000). "Maintaining Cultural Stereotypes in the Serial Reproduction of Narratives." *PSPB* 26. doi:10.1177/0146167200267007
38. **[V-meta]** Lyons, A. & Kashima, Y. (2001). "The Reproduction of Culture." *Social Cognition* 19. doi:10.1521/soco.19.3.372.21470
39. **[V-meta]** Bangerter, A. (2000). "Transformation between scientific and social representations of conception: The method of serial reproduction." *BJSP* 39. doi:10.1348/014466600164615
40. **[V-meta]** Stubbersfield, J., Tehrani, J. & Flynn, E. (2014). "Serial killers, spiders and cybersex." *British Journal of Psychology* 106. doi:10.1111/bjop.12073
41. **[V-meta]** Eriksson, K. & Coultas, J. (2014). "Corpses, Maggots, Poodles and Rats." *Journal of Cognition and Culture* 14. doi:10.1163/15685373-12342107
42. **[V-meta]** Allport, G. W. & Postman, L. (1946). "An Analysis of Rumor." *Public Opinion Quarterly* 10. doi:10.1086/265813；(1945) *Trans. NY Acad. Sci.* doi:10.1111/j.2164-0947.1945.tb00216.x
43. **[V-meta]** Kirby, S., Cornish, H. & Smith, K. (2008). "Cumulative cultural evolution in the laboratory." *PNAS* 105. doi:10.1073/pnas.0707835105
44. **[V-meta]** Kirby, S., Tamariz, M., Cornish, H. & Smith, K. (2015). "Compression and communication in the cultural evolution of linguistic structure." *Cognition* 141. doi:10.1016/j.cognition.2015.03.016
45. **[V-meta]** Griffiths, T. L. & Kalish, M. L. (2007). "Language Evolution by Iterated Learning With Bayesian Agents." *Cognitive Science* 31. doi:10.1080/15326900701326576
46. **[V-meta]** Claidière, N., Scott-Phillips, T. C. & Sperber, D. (2014). "How Darwinian is cultural evolution?" *Phil. Trans. R. Soc. B* 369. doi:10.1098/rstb.2013.0368
47. **[V-full]** da Silva, S. G. & Tehrani, J. J. (2016). "Comparative phylogenetic analyses uncover the ancient roots of Indo-European folktales." *R. Soc. Open Sci.* 3. doi:10.1098/rsos.150645 （读到 PMC 全文） **[已核验]** — Crossref 确认：R. Soc. Open Sci. 3(1), 2016；da Silva & Tehrani。
48. **[V-meta]** Tehrani, J. J. (2013). "The Phylogeny of Little Red Riding Hood." *PLoS ONE* 8. doi:10.1371/journal.pone.0078871
49. **[V-review]** Uther, H.-J. (2004). *The Types of International Folktales* (ATU). — 经 Leppälahti, *Elore* 2005, doi:10.30666/elore.78537 核验。
50. **[V-full]** Roediger, H. L. & DeSoto, K. A. (2014). "Forgetting the presidents." *Science* 346. doi:10.1126/science.1259627 （读到摘要原文） **[已核验]** — Crossref 确认：Science 346, 2014；Roediger III & DeSoto。
51. **[V-meta]** DeSoto, K. A. & Roediger, H. L. (2016). "Recognizing the Presidents." *Psychological Science* 27. doi:10.1177/0956797616631113
52. **[NV-title-only]** Candia, C., Jara-Figueroa, C., Rodriguez-Sickert, C., Barabási, A.-L. et al. (2018). "The universal decay of collective memory and attention." *Nature Human Behaviour* 2. doi:10.1038/s41562-018-0474-5 — **[已修正: Candia, C., Jara-Figueroa, C., Rodriguez-Sickert, C., Barabási, A.-L. & Hidalgo, C. A. (2019). "The universal decay of collective memory and attention." *Nature Human Behaviour* 3(1), 82–91. doi:10.1038/s41562-018-0474-5]** — 文章真实存在、DOI 正确，但卷期年份有误：正式出版为 **Nature Human Behaviour 3(1) (2019)**，"2 (2018)" 系在线预发布年份。末位作者 Hidalgo, C. A.。**仅核验元数据；非 OA，正文与摘要仍未读到。**

### 识字
53. **[V-meta]** Goody, J. & Watt, I. (1963). "The Consequences of Literacy." *Comparative Studies in Society and History* 5. doi:10.1017/s0010417500001730
54. **[V-meta]** Street, B. (2013). "Literacy in Theory and Practice: Challenges and Debates Over 50 Years." *Theory Into Practice* 52. doi:10.1080/00405841.2013.795442
55. **[V-review]** Rawski, E. S. (1979). *Education and Popular Literacy in Ch'ing China*. Univ. of Michigan Press. — 经 Elvin, *China Quarterly* 1980 doi:10.1017/s0305741000012224；Kessler, *AHR* 1980 doi:10.2307/1853579；Stephens, *CER* 1981 doi:10.1086/446196 核验。**具体百分比未核验。**
56. **[V-meta]** Elman, B. & Woodside, A. (eds) (1994). *Education and Society in Late Imperial China, 1600–1900*. University of California Press. doi:10.1525/9780520913639
57. **[V-review]** Cipolla, C. M. (1969). *Literacy and Development in the West*. Pelican. — 经 Day, *Journal of Social History* 1970, doi:10.1353/jsh/4.2.201 核验。
58. **[V-meta]** Brokaw, C. & Chow, K. (eds) (2005). *Printing and Book Culture in Late Imperial China*. University of California Press. doi:10.1525/9780520927797

### 官修史、篡改与记忆制裁
59. **[V-meta]** Twitchett, D. (1992). *The Writing of Official History under the T'ang*. Cambridge University Press. doi:10.1017/cbo9780511572678 **[已核验]**（Crossref 确认：Twitchett, CUP 1992）（核验到完整章节结构：起居注 .006 / 内起居注 .007 / 时政记 .008 / 日历 .009 / 传 .010 / 典志类书 .011 / 实录 .012 / 国史 .013 / 旧唐书编纂 .014 / 史源 .015-.016 / 史馆机构 .004）
60. **[V-meta]** Chan, H.-l. (2005). "Xie Jin (1369–1415) as Imperial Propagandist: His Role in the Revisions of the *Ming Taizu Shilu*." *T'oung Pao* 91. doi:10.1163/1568532054905142
61. **[V-meta]** Chan, H.-l. (2023). "Legitimating Usurpation: Historical Revisions under the Ming Yongle Emperor (r. 1402–1424)." doi:10.4324/9781003420842-8
62. **[V-meta]** Ditmanson, P. (2020). "Historical and Political Arguments: Debates on the Veritable Records in the Ming Dynasty (1368–1644)." In *Powerful Arguments*. doi:10.1163/9789004423626_003
63. **[V-meta]** 김선민 (2012). "From the *Jiu Manzhou dang* to the *Manzhou shilu*: Compilations and revisions of the Veritable Record for the Qing Taizu." *SA-CHONG* 77. doi:10.16957/sa..77.201209.139
64. **[V-meta]** Wade, G. *The Ming Shi-lu as a source for Southeast Asian history, 14th to 17th centuries*. HKU dissertation. doi:10.5353/th_b3123394
65. **[V-meta]** Flower, H. I. (2006). *The Art of Forgetting: Disgrace and Oblivion in Roman Political Culture*. UNC Press. 章节 doi:10.5149/9780807877463_flower.5 / .6 / .7 / .9

### 出土文献与史料双通道（中国）
66. **[V-full]** "The Qin Slips and Boards From Well No. 1, Liye, Hunan: A Brief Introduction to the Qin Qianling County Archives." *Early China* (2013). doi:10.1017/s0362502800000523 （读到摘要原文） **[已核验]** — Crossref 确认：*Early China* 35 (2012-13), pp. 291-329，无单一署名作者；建议引用时补卷号与页码。
67. **[V-meta]** Lü, J. (2025). "An Investigation of Private Letters in the Liye Qin Slips." *Bamboo and Silk*. doi:10.1163/24689246-20250016
68. **[V-meta]** Tsuchiguchi, F. (2022). "A Preliminary Study of 'Other Post Slips' from Liye Site J1." *Bamboo and Silk*. doi:10.1163/24689246-00402018
69. **[V-meta]** Tang, P. (2022). "On the Death Penalty as Seen in the *Falü Dawen* Manuscript from the Shuihudi Qin Slips." *Bamboo and Silk*. doi:10.1163/24689246-20220024
70. **[V-meta]** Lander, B., Ling, W. & Wen, X. (2024). *State and Local Society in Third Century South China*. Brill. doi:10.1163/9789004549654_003 / _004
71. **[V-meta]** Chan, S. (2019). "Introduction: The Excavated Guodian Bamboo Manuscripts." doi:10.1007/978-3-030-04633-0_1
72. **[V-meta]** Rong, X. (2013). *Eighteen Lectures on Dunhuang*. Brill. Lecture 3 doi:10.1163/9789004252332_005；Lecture 4 doi:10.1163/9789004252332_006
73. **[V-meta]** "The Nivison-Shaughnessy Debate on the Bamboo Annals (Zhushu jinian)." In *The Nivison Annals* (2018). De Gruyter. doi:10.1515/9781501505393-022

### 年代学
74. **[V-meta]** Li, X. (2002). "The Xia-Shang-Zhou Chronology Project: Methodology and Results." *Journal of East Asian Archaeology* 4. doi:10.1163/156852302322454585
75. **[V-meta]** Qiu, S. & Cai, L. (2002). "14C Chronological Framework of the Xia-Shang-Zhou Chronology Project." *Chinese Archaeology* 2. doi:10.1515/char.2002.2.1.6
76. **[V-meta]** Zhang, X. & Qiu, S. (2007). "The Use of Wiggle-matching Method in the Xia-Shang-Zhou Chronology Project." *Chinese Archaeology* 7. doi:10.1515/char.2007.7.1.183
77. **[V-meta]** Li, B. (2024). "The Xia-Shang-Zhou Chronology Project and Archaeological Research on the Xia Dynasty." In *Myth and the Making of History*. doi:10.1515/9781438497709-006
78. **[V-meta]** Reimer, P. J. (2020). "Composition and consequences of the IntCal20 radiocarbon calibration curve." *Quaternary Research* 96. doi:10.1017/qua.2020.42
79. **[V-meta]** Heaton, T. J., Blaauw, M., Blackwell, P. G., Bronk Ramsey, C. et al. (2020). *Radiocarbon* 62. doi:10.1017/rdc.2020.46
80. **[V-meta]** Hogg, A. G., Heaton, T. J., Hua, Q., Palmer, J. et al. (2020). "SHCal20." *Radiocarbon* 62. doi:10.1017/rdc.2020.59

### 文本谱系与史学方法
81. **[V-meta]** Barbrook, A. C., Howe, C. J., Blake, N. & Robinson, P. (1998). "The phylogeny of *The Canterbury Tales*." *Nature* 394. doi:10.1038/29667
82. **[V-meta]** Howe, C. J., Connolly, R. & Windram, H. F. (2012). "Responding to Criticisms of Phylogenetic Methods in Stemmatology." *SEL* 52. doi:10.1353/sel.2012.0008
83. **[V-meta]** Simkin, M. V. & Roychowdhury, V. P. (2006). "Do You Sincerely Want to Be Cited? Or: Read Before You Cite." *Significance* 3. doi:10.1111/j.1740-9713.2006.00202.x
84. **[V-review]** Howell, M. & Prevenier, W. (2001). *From Reliable Sources: An Introduction to Historical Methods*. Cornell UP. — 经 Tholfsen, *JIH* 2002, doi:10.1162/00221950260208733 核验。

### 跨文明数据库与其争议
85. **[V-full]** Turchin, P., Currie, T. E., Whitehouse, H., François, P. et al. (2018). "Quantitative historical analysis uncovers a single dimension of complexity that structures global variation in human social organization." *PNAS* 115. doi:10.1073/pnas.1708800115 （读到 PMC 全文） **[已核验]** — Crossref 确认：PNAS 115(2)，在线 2017-12-21 / 印本 2018-01-09。
86. **[V-meta]** Turchin, P., Brennan, R., Currie, T., Feeney, K. et al. (2015). "Seshat: The Global History Databank." *Cliodynamics* 6. doi:10.21237/c7clio6127917
87. **[V-meta]** Slingerland, E., Monroe, M. W., Spicer, R., Muthukrishna, M. et al. (2019). "Historians Respond to Whitehouse et al. (2019)." PsyArXiv. doi:10.31234/osf.io/2amjz
88. **[V-meta]** Naether, F. (2022). "Some Remarks on Whitehouse et al. (2019)." *Journal of Cognitive Historiography*. doi:10.1558/jch.39578

### 本次抓取的在线资源
89. **[V]** CDLI, "About CDLI" 与 "Periods" 页面及检索接口。https://cdli.mpiwg-berlin.mpg.de （2026-09-10）
90. **[V]** Seshat: Global History Databank 站点。https://seshat-db.com （2026-09-10）
91. **[V]** D-PLACE 站点（许可：CC BY-NC 4.0）。https://d-place.org （2026-09-10）
92. **[V]** HUST-OBC 数据仓库。https://github.com/Pengjie-W/HUST-OBC （2026-09-10）
93. **[V]** OxCal / IntChron。https://c14.arch.ox.ac.uk/oxcal.html ；https://intchron.org （2026-09-10）
