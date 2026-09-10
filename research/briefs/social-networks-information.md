# 社会网络、亲属结构与信息传播（信息边界的基础）

- **slug**: `social-networks-information`
- **范围（一句话）**：为 civilization-sim 的"信息边界（Information Horizon）"原则提供可工程实现的底层机制——社会网络如何生成与演化、消息如何以有限速度沿网络与地理传播、信息如何在传播中延迟／失真／丢失，以及这种失真如何在数百年尺度上机械地生成神话、官方史与史学争议。
- **完成日期**：2026-09-10
- **检索状态说明**：本次 WebSearch 配额在会话开始时即已耗尽（200/200）。全部检索改由 Bash 直连 Crossref API、Europe PMC REST API、DOAJ API、GitHub raw、以及若干可达的开放获取站点完成，另有少量 WebFetch。**凡本简报中标注"[已验证]"的文献，其标题／作者／年份／期刊／卷页／DOI 均在本次会话中由 Crossref 或 Europe PMC 返回的元数据直接读到**；凡标注"[凭记忆·未验证]"的，是我知道但本次未能取得原文或元数据确认的，**不得作为参数来源使用**。第 4 节的多数数字来自我本次实际下载并自己计算的数据集，或来自我本次读到的开放全文。

>
> ## ⚠️ 引文核验结果（2026-09-10，独立核验）
>
> 本次对第 10 节中 24 条承重引文逐条做了独立核验（Crossref API、doi.org 解析、期刊页、原始 PDF）。结论：
>
> - **20 条确认存在且信息正确**（含 ORBIS 2012 技术文档，重新下载确认 56 页与标题页作者）。
> - **3 条已修正**：#9 Barthélemy 2011 实为 *Physics Reports* 499(1–3), 1–101, doi:10.1016/j.physrep.2010.11.002（原标"未验证"，现已确认，**M3 可正常引用**）；#58 Wobst 1974 实为 *American Antiquity* 39(2), 147–178, doi:10.2307/279579（原标"Crossref 中检索不到"，现已确认，但 175–475 仍是经 White 2017 转引）；#61 Dickinson & Drummond 2025 补全为 *Sleep Advances* 6(2)。
> - **1 条未找到（#81）**：中国历代驿传制度的站间距与日行里程，**至今没有任何可引用文献**。
> - **没有发现疑似伪造的引文。**
>
> **因此失去支撑的结论**：**M10（驿传机制）的全部东亚具体参数**——"三十里一驿"、唐驿站总数、宋急脚递、清马递 300/400/500/600 里分级——目前零来源，属无源断言，实现时不得写入任何具体里程数字，只能沿用 ORBIS 的罗马世界参数或标为 D 级占位。第 6 节的东亚校准仅在 CBDB（#74）、De Weerdt（#76）、Wu（#77）三项上有据。
>
> 另需注意：#76 De Weerdt 与 #77 Wu 仅核验到书目／章节元数据，**正文未读**，由其支撑的 filter_upward 参数仍应保持 D 级；#79 Braudel/Sardella 仅确认两书存在，原文未取得，其消息速度数字仍不得引用。

---

## 1. 本简报要回答的问题

本简报服务于 MANDATE 第 4 条（信息边界）与第 9 条（世界事实与历史叙事分离）。具体要回答：

**Q1. 网络结构从哪来？** 一个从前文明期开始、数千年、人口从数百到数千万的世界，社会网络不能手工指定。需要一套能随人口、聚落、生产方式、制度自动演化的网络生成规则。哪些经典网络模型可以用？哪些是学界已经证伪的（尤其是被广泛误用的 Barabási–Albert）？

**Q2. 亲属结构怎么建？** 亲属是前现代社会最稳定、最强、成本最低的信息通道，也是继承／联盟／派系的载体。婚配规则（外婚／内婚／交表婚偏好）、居住规则（从父居／从母居）、继承规则（诸子均分／长子）在真实世界中的分布是什么？这些规则如何机械地决定网络拓扑，从而决定信息能流到哪里？

**Q3. 消息怎么传？** 需要一个既能表达"街谈巷议"、又能表达"八百里加急"、还能表达"一部书在三百年后被人重新读到"的统一消息模型。简单传染（SIR/谣言模型）与复杂传染（阈值模型）分别适用于哪类内容？

**Q4. 物理速度是多少？** 前现代信息传播的真实日行里程、季节性、水陆差异有没有可用的量化参数？（有：ORBIS 给了完整参数表。）

**Q5. 失真怎么建？** 口传、抄写、翻译、官僚层级上报中的失真是随机噪声还是有方向的偏差？有没有实验参数？

**Q6. 核心工程问题**：如何给每一个人物与组织构建一个"可获得信息集"（本地观察 + 社会网络 + 制度化情报渠道 + 文字记录），使其**带延迟、带失真、带缺失**，并且这个信息集本身可以被追溯、可以被重放、可以支撑"为什么他当时做出这个愚蠢决策"的因果解释？

**Q7. 神话化与篡改的机制基础**：世界事实数据库（真实发生了什么）与世界内叙事（人们相信发生了什么）如何分离并各自演化，使得数百年后模拟中的历史学家可以研究一段他们只能部分看见的历史？

---

## 2. 已有成熟模型与理论

### 2.1 Erdős–Rényi 随机图 G(n, p)

- **核心机制**：每对节点以独立同概率 p 连边。
- **形式化程度**：完全形式化，解析可解。
- **状态变量**：n（节点数）、p（连边概率）；导出量：平均度 z = p(n−1)，巨型连通分支出现在 z > 1。
- **适用范围**：**只应作为零模型（null model）**，用来判断"我们生成的网络是否比随机更聚集／更模块化"。
- **已知局限**：聚类系数 C ≈ z/n（随 n 增大趋于 0），与真实社会网络的 C ≈ 0.1–0.6 差几个数量级；无社群结构、无空间、无同质性。**绝不能拿来当社会网络本体。**
- **出处**：本次未单独检索 Erdős–Rényi 原文；作为教科书常识使用，等级 B。

### 2.2 Watts–Strogatz 小世界模型（1998）

- **核心机制**：从规则环格（每点连最近的 K 个邻居）出发，以概率 p 随机重连每条边。小 p 时聚类系数几乎不降，但平均路径长度骤降 → 高聚类 + 短路径共存。
- **形式化程度**：完全形式化。
- **状态变量**：n, K, p；输出 C(p)、L(p)。
- **对本项目的价值**：这是"信息边界"最重要的正面直觉——**一个高度本地化、几乎所有交往都发生在半径 20 公里内的农业社会，仍然可以有 6–10 步的全局直径**，因为总有少数远距离连接（商人、僧侣、宗室联姻、流放官员、逃亡者）。这意味着"消息最终会传到"和"消息传得极慢且极度失真"可以同时为真。
- **已知局限**：度分布过窄（近似泊松），无空间距离概念（重连是均匀随机的），无同质性，无社群层级，网络静态。
- **出处**：Watts, D. J. & Strogatz, S. H. (1998) "Collective dynamics of 'small-world' networks", *Nature* 393(6684): 440–442, doi:10.1038/30918 **[已验证：Crossref]**

### 2.3 Barabási–Albert 优先连接（1999）与其在社会网络中的失效

- **核心机制**：网络持续增长；新节点以正比于已有节点度的概率连接（"富者愈富"），生成幂律度分布 P(k) ~ k^(−3)。
- **形式化程度**：完全形式化。
- **摘要原文（本次读到）**："networks expand continuously by the addition of new vertices" 且 "new vertices attach preferentially to sites that are already well connected"。
- **⚠️ 关键批评（本项目必须采纳）**：Broido & Clauset (2019) 用 ICON（Index of Complex Networks）中 **928 个真实网络数据集**做了严格的统计检验。**社会网络子集的结果是：50% 属于 "Not Scale Free"（既无直接也无间接的无标度证据）；41% 属于 "Super-Weak"；直接证据中 48% 落在 "Weakest"、31% 落在 "Weak"；"not a single network falls into the Strong or Strongest categories"（原文）**。全语料层面 49% Not Scale Free、46% Super-Weak。作者结论："social networks are at best only weakly scale free, and even in cases where the power-law distribution is plausible, non-scale-free distributions are often a better description of the data."
- **对本项目的含义**：**不要用 BA 模型生成人际社会网络。**BA 的机制假设（新节点全局可见所有已有节点的度）恰恰违反信息边界原则——在前现代世界里，一个新出生的农民不可能"看到"京城权贵的度数并优先连接他。真正会产生重尾的是**制度**（官职、市场、寺院、宗族族长），而制度重尾应该由制度规则本身涌现，而不是由抽象的优先连接注入。
- **出处**：Barabási, A.-L. & Albert, R. (1999) "Emergence of Scaling in Random Networks", *Science* 286(5439): 509–512, doi:10.1126/science.286.5439.509 **[已验证：Crossref，摘要原文]**；Broido, A. D. & Clauset, A. (2019) "Scale-free networks are rare", *Nature Communications* 10: 1017, doi:10.1038/s41467-019-08746-5 **[已验证：Crossref + Europe PMC 全文 PMC6399239，上述百分比为原文引用]**；反方观点见 Holme, P. (2019) "Rare and everywhere: Perspectives on scale-free networks", *Nature Communications* 10, doi:10.1038/s41467-019-09038-8 **[已验证：Crossref]**。

### 2.4 空间嵌入网络与引力／距离衰减模型

- **核心机制**：连边概率或交互强度随距离衰减，f(d) ∝ d^(−α) 或 exp(−d/d₀)，并可与两端"质量"（人口、财富）相乘 → 引力模型 I_ij = M_i M_j f(d_ij)。
- **考古学中的成熟应用**：Knappett, Evans & Rivers (2008) "Modelling maritime interaction in the Aegean Bronze Age", *Antiquity* 82(318): 1009–1024, doi:10.1017/s0003598x0009774x **[已验证：Crossref]** —— 该模型（后称 ariadne）以站点"规模"为内生变量、以指数距离衰减核为交互项，用于解释青铜时代爱琴海聚落网络的兴衰。Rihll, T. & Wilson, A. "Modelling settlement structures in Ancient Greece"（收入 *City and Country in the Ancient World*，doi:10.4324/9780203418703_chapter_3）**[已验证：Crossref，年份字段缺失]** 是更早的希腊城邦引力／熵最大化模型。
- **现代经验校准**：Lengyel 等 (2020) 用匈牙利社交网站 iWiW 的完整生命周期数据（2002–2012，**最多 3,000,000 用户、300,000,000 条好友关系**）发现扩散早期距离衰减弱（大城市之间跳跃式传播），晚期距离衰减强（本地为主），并且**加入个体采纳阈值分布后模型对城市规模标度律的拟合显著改善**。这直接支持"技术／信仰扩散是复杂传染 + 空间过程的耦合"。出处：Lengyel, B., Bokányi, E., Di Clemente, R., Kertész, J. & González, M. C. (2020) "The role of geography in the complex diffusion of innovations", *Scientific Reports* 10: 15065, doi:10.1038/s41598-020-72137-w **[已验证：Crossref + Europe PMC 全文 PMC7492253]**
- **手机数据的距离衰减**：Lambiotte, R., Blondel, V., de Kerchove, C., Huens, E., Prieur, C. 等 (2008) "Geographical dispersal of mobile communication networks", *Physica A* 387(21): 5317–5325, doi:10.1016/j.physa.2008.05.014 **[已验证：Crossref；但具体的衰减指数数值本次未读到原文，见第 4 节"未验证参数"]**
- **基于排名而非距离的模型**：Liben-Nowell, D., Novak, J., Kumar, R., Raghavan, P., Tomkins, A. (2005) "Geographic routing in social networks", *PNAS* 102: 11623–11628, doi:10.1073/pnas.0503018102 **[已验证：Europe PMC 元数据 + 摘要]**。摘要原文："existing theoretical models have not been shown to capture behavior in real-world social networks. Here, we introduce a richer mod[el]…"。该文提出用**排名（rank-based）**而非绝对距离来定义友谊概率——在人口密度极不均匀的地图上（正是东亚：华北平原 vs 青藏高原），rank-based 比 d^(−α) 更稳健。**注意：其核心结论"P(friendship) ∝ 1/rank"我本次只读到摘要，未读到正文公式，等级降为 C。**
- **已知局限**：纯几何距离忽略地形、河流、季风、行政边界。ORBIS 的做法（成本表面而非欧氏距离）才是正确姿势。

### 2.5 同质性（Homophily）

- **核心机制**："Birds of a feather flock together"——相似者更易成为连接。可拆为**选择性同质性**（choice homophily，主动选择相似者）与**诱导性同质性**（induced homophily，因为环境本身就把相似者放在一起）。
- **奠基综述**：McPherson, M., Smith-Lovin, L. & Cook, J. M. (2001) "Birds of a Feather: Homophily in Social Networks", *Annual Review of Sociology* 27(1): 415–444, doi:10.1146/annurev.soc.27.1.415 **[已验证：Crossref]**
- **机制拆解的关键实证**：Kossinets, G. & Watts, D. J. (2009) "Origins of Homophily in an Evolving Social Network", *American Journal of Sociology* 115(2): 405–450, doi:10.1086/599247 **[已验证：Crossref]**；前置的 Kossinets & Watts (2006) "Empirical Analysis of an Evolving Social Network", *Science* 311(5757): 88–90, doi:10.1126/science.1116869 **[已验证：Crossref]**
- **对本项目的价值**：**同质性不需要单独实现。**如果模拟中已经有"聚落分配、职业分配、宗族分配、寺庙成员、市场摊位、军队编制"，诱导性同质性会自动出现。只需要额外加一个较弱的选择性同质性项（在候选集中偏好属性相近者）。这符合"涌现优于规定"的纲领原则。
- **文化耦合模型**：Axelrod, R. (1997) "The Dissemination of Culture: A Model with Local Convergence and Global Polarization", *Journal of Conflict Resolution* 41(2): 203–226, doi:10.1177/0022002797041002001 **[已验证：Crossref]**。机制：agent 有 F 个文化特征、每个 q 个取值；两个邻居以正比于其特征重合度的概率互动，互动时复制一个不同的特征。**结果是局部趋同 + 全局极化，且稳定文化区的数量随 q 增大而增大**——这是"为什么会形成有边界的方言区／文化圈"的最小机制，且天然与信息边界耦合（差异太大就不再交流，于是永远不会趋同）。局限：Axelrod 模型在有噪声时会崩溃为单一文化（Klemm 等的后续工作），所以不能直接用作长时段文化内核，只能作为局部机制。

### 2.6 弱连接、桥、结构洞

- **弱连接理论**：Granovetter, M. S. (1973) "The Strength of Weak Ties", *American Journal of Sociology* 78(6): 1360–1380, doi:10.1086/225469 **[已验证：Crossref]**；修订版 Granovetter, M. (1983) "The Strength of Weak Ties: A Network Theory Revisited", *Sociological Theory* 1: 201, doi:10.2307/202051 **[已验证：Crossref]**。核心命题：强连接倾向于闭合三角（你的两个好友多半互相认识），因此**新信息只能经由弱连接跨越社群边界**。可形式化为"禁止三元组（forbidden triad）"：若 A–B 强、A–C 强，则 B–C 不为空的概率极高。
- **大规模经验验证**：Onnela, J.-P., Saramäki, J., Hyvönen, J., Szabó, G., Lazer, D., Kaski, K., Kertész, J., Barabási, A.-L. (2007) "Structure and tie strengths in mobile communication networks", *PNAS* 104(18): 7332–7336, doi:10.1073/pnas.0610245104 **[已验证：Crossref + Europe PMC 元数据／摘要]**。摘要原文："we examine the communication patterns of millions of mobile phone users… We observe a coupling between interaction strengths and the network's local structure"。**注意：该文最著名的结果——按连接强度从弱到强逐条删边会使网络在某个阈值处相变式碎裂，而从强到弱删边不会——我本次只读到摘要，未读到正文与相变点数值，故该具体结论等级为 B 而非 A。**
- **结构洞**：Burt, R. S. *Structural Holes: The Social Structure of Competition*（1992，本次只验证到其再版章节 doi:10.1515/9780691229270-013 与 doi:10.2307/j.ctv1f886rp.15 **[已验证：Crossref]**，原书本身未验证）；Burt, R. S. (2004) "Structural Holes and Good Ideas", *American Journal of Sociology* 110(2): 349–399, doi:10.1086/421787 **[已验证：Crossref]**。核心：跨越结构洞的中间人获得信息套利收益（先知道、知道更多版本、能控制转述）。**这是本项目"权臣／中间商／情报头子"这一类角色的形式化基础，且直接可计算（betweenness / effective size / constraint）。**
- **友谊悖论**：Feld, S. L. (1991) "Why Your Friends Have More Friends Than You Do", *American Journal of Sociology* 96(6): 1464–1477, doi:10.1086/229693 **[已验证：Crossref]**。含义：随机个体感知到的"大家都在做什么"会系统性地偏向高度数节点的行为 → **这是"谣言为什么显得比实际普遍"的结构性来源，不需要额外加认知偏差。**

### 2.7 Dunbar 数与社会网络层级（**争议激烈**）

- **原始命题**：Dunbar, R. I. M. (1992) "Neocortex size as a constraint on group size in primates", *Journal of Human Evolution* 22(6): 469–493, doi:10.1016/0047-2484(92)90081-j **[已验证：Crossref]**；后续 Dunbar (1995) *JHE* 28(3): 287–296, doi:10.1006/jhev.1995.1021 **[已验证]**；Kudo & Dunbar (2001) *Animal Behaviour* 62(4): 711–722, doi:10.1006/anbe.2001.1808 **[已验证]**。
- **层级结构命题**：Zhou, W.-X., Sornette, D., Hill, R. A. & Dunbar, R. I. M. (2005) "Discrete hierarchical organization of social group sizes", *Proceedings of the Royal Society B* 272(1561): 439–444, doi:10.1098/rspb.2004.2970 **[已验证：Crossref + Europe PMC 摘要]**。摘要原文提到 "work on both human and non-human primates has suggested that social groups are often hierarchically structured"。**广为流传的层级序列 5–15–50–150–500–1500（比值≈3）我本次未能读到该文正文予以确认，故标记为 [凭记忆·未验证]，等级 C。**
- **⚠️ 系统性批评（必须采纳）**：Lindenfors, P., Wartel, A. & Lind, J. (2021) "'Dunbar's number' deconstructed", *Biology Letters* 17(5), doi:10.1098/rsbl.2021.0158 **[已验证：Crossref，以下为摘要原文]**："Our analyses on complementary datasets using different methods yield wildly different numbers. Bayesian and generalized least-squares phylogenetic methods generate approximations of average group sizes between **69–109** and **16–42**, respectively. However, enormous 95% confidence intervals (**4–520** and **2–336**, respectively) imply that specifying any one number is futile. A cognitive limit on human group size cannot [be derived in this manner]."
- **对本项目的结论**：**不要把 150 写成硬上限。**正确做法是把"活跃社会关系数"建成一个受**时间预算**约束的内生量：每个 agent 每 tick 有有限的社交时间预算，维持一条关系需要周期性投入，关系强度随不投入而衰减。这样"数量级 10²"会自然涌现，且会随生产方式（觅食 vs 农耕 vs 城市）、识字率（书信可以低成本维持远距关系）、制度（官僚名册替代个人记忆）而变化——这正是我们想要的涌现。
- **另一条经验路线（更适合我们）**：见 2.9 觅食者数据，Hill 等给出的"社会宇宙约 1000 人"是**实测**而非从脑量外推的。

### 2.8 阈值模型、复杂传染与级联

- **阈值模型**：Granovetter, M. (1978) "Threshold Models of Collective Behavior", *American Journal of Sociology* 83(6): 1420–1443, doi:10.1086/226707 **[已验证：Crossref]**。个体 i 有阈值 θ_i；当已行动者比例超过 θ_i 时 i 行动。关键洞察：**总体结果对阈值分布的微小扰动极端敏感**（经典例子：阈值分布 {0,1,2,…,99} 全体暴动；改成 {0,2,2,3,…} 则只有一人行动）。后续 Macy, M. & Evtushenko, A. (2020) "Threshold Models of Collective Behavior II: The Predictability Paradox and Spontaneous Instigation", *Sociological Science* 7: 628–648, doi:10.15195/v7.a26 **[已验证：Crossref]**。
- **网络上的全局级联**：Watts, D. J. (2002) "A simple model of global cascades on random networks", *PNAS* 99(9): 5766–5771, doi:10.1073/pnas.082090499 **[已验证：Crossref]**。核心：存在"级联窗口"——网络太稀疏则冲击无法扩散，太稠密则每个节点被太多未行动邻居锚定，也不扩散；只有中等连通度区间才可能出现全局级联。**具体窗口边界数值（常被引为平均度 z ≈ 1 到 z ≈ 8、阈值 φ = 0.18）本次未读到原文，标记 [凭记忆·未验证]。**
- **复杂传染**：Centola, D. & Macy, M. (2007) "Complex Contagions and the Weakness of Long Ties", *American Journal of Sociology* 113(3): 702–734, doi:10.1086/521848 **[已验证：Crossref]**。核心：当采纳需要**多次独立强化**时，Watts–Strogatz 式的长程弱连接反而**无助于**传播（因为一条长边只能提供一次强化），此时宽桥（wide bridge，两个社群之间的多条平行连接）才是关键。**这与 Granovetter 的弱连接理论并不矛盾，而是内容依赖的：事实型信息 = 简单传染，弱连接有利；规范／宗教／高风险技术 = 复杂传染，弱连接无效。这一二分应当直接写进我们的消息模型。**
- **实验证据**：Centola, D. (2010) "The Spread of Behavior in an Online Social Network Experiment", *Science* 329(5996): 1194–1197, doi:10.1126/science.1185231 **[已验证：Crossref]**。
- **多引发者与临界引发比例**：Singh, P., Sreenivasan, S., Szymanski, B. K. & Korniss, G. (2013) "Threshold-limited spreading in social networks with multiple initiators", *Scientific Reports* 3: 2330, doi:10.1038/srep02330 **[已验证：Crossref + Europe PMC 全文 PMC3728590]**。摘要原文："even for arbitrarily high value of ϕ, there exists a critical initiator fraction p_c(ϕ) beyond which the cascade becomes global. Network structure, in particular clustering, plays a significant role… community structure within the network facilitates opinion spread to a larger extent than a homogeneous random network."
- **对本项目的价值**：这是"叛乱／改宗／新技术采纳／风尚"能够**涌现而不是被脚本触发**的数学基础。我们只需要给每个 agent 一个内生阈值（由风险偏好、既得利益、亲属立场、饥饿程度决定），级联本身由网络拓扑与阈值分布决定。**任何"因为剧情需要所以爆发起义"的写法都被这一机制排除。**

### 2.9 谣言／流言的传染病式模型

- **奠基**：Daley, D. J. & Kendall, D. G. (1964) "Epidemics and Rumours", *Nature* 204(4963): 1118, doi:10.1038/2041118a0 **[已验证：Crossref]**。机制：把人群分为 Ignorant（未知）／Spreader（传播者）／Stifler（不再传播者）。与 SIR 的关键差别是**停止传播的机制是社会性的**（当传播者遇到已知者时以一定概率变成 stifler，"这消息大家都知道了，没意思了"），而不是生理性康复。
- **变体与分析**：Maki–Thompson 模型；Gani, J. (2000) "The Maki–Thompson rumour model: a detailed analysis", *Environmental Modelling & Software* 15(8): 721–725, doi:10.1016/s1364-8152(00)00029-3 **[已验证：Crossref]**；Pittel, B. (1990) "On a Daley-Kendall model of random rumours", *Journal of Applied Probability* 27(1): 14–27, doi:10.1017/s0021900200038390 **[已验证：Crossref]**；小世界网络上的相变见 Agliari, E., Pachon, A., Rodriguez, P. & Tavani, F. (2017) "Phase Transition for the Maki–Thompson Rumour Model on a Small-World Network", *Journal of Statistical Physics* 169(4): 846–875, doi:10.1007/s10955-017-1892-x **[已验证：Crossref]**。
- **著名解析结果**：DK 模型在混合良好人群中，最终仍有约 20% 的人**从未听说**该谣言（常引为 0.203）。**该常数本次未从原文验证，标记 [凭记忆·未验证]。**但"即使在无限传播时间下也有一个非零的永不知情比例"这一定性结论是稳健的（等级 B），且对我们非常重要：**它给了"边远地区永远不知道京城发生了什么"一个内生机制，不需要人为设置地理黑名单。**

### 2.10 历史社会网络分析（Historical Network Research）的实证范例

- **Medici 案例（本领域标杆）**：Padgett, J. F. & Ansell, C. K. (1993) "Robust Action and the Rise of the Medici, 1400–1434", *American Journal of Sociology* 98(6): 1259–1319, doi:10.1086/230190 **[已验证：Crossref]**。核心概念 **robust action**：Cosimo de' Medici 的权力来源不是任何单一联盟，而是他同时嵌在多个互不重叠的网络（婚姻、商业信贷、邻里、党派）中，且这些网络在他之外几乎不连通——因此他的每一个行动可以被不同受众读出不同意图，而任何一方都无法核实。**这对本项目极其重要：robust action 只有在信息边界存在时才可能。全知视角下没有 robust action。**
  - **本次我实际计算的量化结果**（数据来自 NetworkX 内置 `florentine_families_graph`，其来源标注为 Breiger & Pattison 1986, *Social Networks* 8(3): 215–256）：该婚姻网络 **15 个家族、20 条婚姻边**。度数：Medici 6（最高，度中心性 6/14 = 0.429），Guadagni 4，Strozzi 4，Albizzi 3。归一化中介中心性：**Medici 0.522，Guadagni 0.254，Strozzi 0.103**——Medici 的中介中心性是第二名的两倍以上，而其财富与议席在当时并非第一。**这是"结构位置 > 资源存量"的最干净例证，也是我们评估模拟内人物政治潜力的现成指标。**
- **时序网络与信息传播机会**：Roller, R. (2025) "Time-Respecting Paths in Letter Networks Reveal Opportunities for Influencing Information Transmission during the European Reformation", *Journal of Historical Network Research* 12(1), doi:10.25517/jhnr.v12i1.83 **[已验证：本次直接读到期刊页面的题名／作者／年份／DOI／摘要摘录]**。方法核心：**time-respecting path**（时间尊重路径）——只有当边 (A→B) 的时间早于边 (B→C) 时，A 的信息才可能经 B 到达 C。静态网络的中心性会严重高估实际的信息控制力。该文识别出三类改革者：低影响潜力组、使用短冗余路径以求稳健的中等组、占据战略中介位置以控制信息流的中等组。**工程含义：我们的因果链查询必须在时序图上做，不能在聚合的静态图上做。**
- **罗马精英网络**：Hillner, J. & MacCarron, M. (2025) "Social Network Analysis", 收入 *Brill's Companion to Roman Prosopography*, pp. 151–181, doi:10.1163/9789004748613_011 **[已验证：Crossref]**。（正文未读。）
- **考古学网络方法教科书**：Brughmans, T. & Peeples, M. A. (2023) *Network Science in Archaeology*, Cambridge University Press, doi:10.1017/9781009170659 **[已验证：Crossref]**；书评见 *JHNR* 13(1), doi:10.25517/jhnr.v13i1.121 **[已验证：本次读到]**。另有 Terrell, Golitko, Dawson & Kissel, *Modeling the Past: Archaeology, History and Dynamic Networks*（经 *JHNR* 13(1) 书评 doi:10.25517/jhnr.v13i1.125 确认存在 **[已验证]**）。
- **综述**：Erikson, E. & Feltham, E. (2020) "Historical Network Research", 收入 *The Oxford Handbook of Social Networks*, pp. 431–442, doi:10.1093/oxfordhb/9780190251765.013.40 **[已验证：Crossref]**。

### 2.11 亲属结构的形式化

- **p-graph 与结构内婚**：White, D. R. (1997) "Structural endogamy and the network", *Mathématiques et sciences humaines* 137, doi:10.4000/msh.2742 **[已验证：Crossref]**；Schweizer, T. & White, D. R. (1998) "Revitalizing the Study of Kinship and Exchange with Network Approaches", 收入 *Kinship, Networks, and Exchange*, pp. 1–10, doi:10.1017/cbo9780511896620.002 **[已验证：Crossref]**。
  - **p-graph 的关键工程价值**：把亲属网络表示成"以**婚姻／配偶对**为节点、以**个体**为边"的有向无环图（而不是通常的以个人为节点）。在这个表示下，**"结构内婚"（structural endogamy）= 图中的双连通分支**，即一群家族通过反复联姻形成的闭合区块。这是一个**可计算的、无需人为定义"氏族"的社会集团发现算法**——正好符合我们"氏族／门阀不应被预先规定，而应从婚姻记录中涌现"的要求。
- **跨文化编码体系**：Murdock, G. P., Textor, R., Barry, H. III, White, D. R., Gray, J. P. & Divale, W. T. (1999) *Ethnographic Atlas*, *World Cultures* 10: 24–136（codebook）**[已验证：本次从 D-PLACE 数据仓库 `datasets/index.csv` 直接读到该引用条目]**；Murdock, G. P. & White, D. R. (1969) "Standard Cross-Cultural Sample", *Ethnology* 9: 329–369 **[已验证：同上]**。
- **聚合数据库**：Kirby, K. R., Gray, R. D., Greenhill, S. J., Jordan, F. M., Gomes-Ng, S. 等 (2016) "D-PLACE: A Global Database of Cultural, Linguistic and Environmental Diversity", *PLOS ONE* 11(7): e0158391, doi:10.1371/journal.pone.0158391 **[已验证：Crossref + 本次读到 PLOS 页面摘要全文]**。摘要原文：覆盖 "over 1400 human societies"；明确指出该库设计用于克服四类障碍，其中第四类是 "spatial and historical dependencies among cultural groups that present challenges for analysis"（即 Galton 问题）。

### 2.12 觅食者社会网络的实测数据（前文明期的唯一经验锚点）

- **共居模式**：Hill, K. R., Walker, R. S., Božičević, M., Eder, J., Headland, T. 等 (2011) "Co-Residence Patterns in Hunter-Gatherer Societies Show Unique Human Social Structure", *Science* 331(6022): 1286–1289, doi:10.1126/science.1199071 **[已验证：Crossref；正文未读，非 OA]**。
- **跨营地互动率（本次读到全文，见第 4 节数字）**：Hill, K. R., Wood, B. M., Baggio, J., Hurtado, A. M. & Boyd, R. T. (2014) "Hunter-gatherer inter-band interaction rates: implications for cumulative culture", *PLOS ONE* 9: e102806, doi:10.1371/journal.pone.0102806 **[已验证：Crossref + Europe PMC 全文 PMC4105570]**。
- **高分辨率网络测量**：Migliano, A. B., Battiston, F., Viguier, S., Page, A. E., Dyble, M., Schlaepfer, R., Smith, D., Astete, L., Ngales, M., Gomez-Gardenes, J., Latora, V. & Vinicius, L. (2020) "Hunter-gatherer multilevel sociality accelerates cumulative cultural evolution", *Science Advances* 6: eaax5913, doi:10.1126/sciadv.aax5913 **[已验证：Crossref + Europe PMC 全文 PMC7048420]**。用无线传感器（mote）记录 3 米内的每小时接触。
- **合作网络**：Apicella, C. L., Marlowe, F. W., Fowler, J. H. & Christakis, N. A. (2012) "Social networks and cooperation in hunter-gatherers", *Nature* 481(7382): 497–501, doi:10.1038/nature10736 **[已验证：Crossref]**。
- **性别平等与营地组成**：Dyble, M., Salali, G. D., Chaudhary, N., Page, A., Smith, D., Thompson, J., Vinicius, L., Mace, R. & Migliano, A. B. (2015) "Sex equality can explain the unique social structure of hunter-gatherer bands", *Science* 348: 796–798, doi:10.1126/science.aaa5139 **[已验证：Europe PMC 元数据／摘要]**。摘要原文：多变的 meta-group、低营地内亲缘度，由一个 agent-based model 解释——"even if all individuals in a community seek to live with as many kin as possible, within[-camp relatedness stays low]"。**这是一个可以直接抄进我们模拟的居住规则微观机制。**

### 2.13 记忆、口传与历史叙事的形成

- **Bartlett 的序列复述（serial reproduction）**：Bartlett, F. C. *Remembering: A Study in Experimental and Social Psychology*（1932；本次验证到 1995 剑桥再版 doi:10.1017/cbo9780511759185 **[已验证：Crossref]**，以及 1933 年 *British Journal of Educational Psychology* 3(2): 187–192 的书评／摘要条目 doi:10.1111/j.2044-8279.1933.tb02913.x **[已验证]**）。核心：故事在人际链条中传递时不是随机丢失细节，而是**朝着接收者已有图式（schema）的方向系统性地变形**——陌生的被本土化，无因果的被补上因果，多个人物被合并，数字被规整。**这正是我们需要的"失真不是噪声，而是有方向的压缩"。**
- **口传的记忆结构**：Rubin, D. C. (1995) *Memory in Oral Traditions: The Cognitive Psychology of Epic, Ballads, and Counting-out Rhymes*, Oxford University Press, doi:10.1093/oso/9780195082111.001.0001 **[已验证：Crossref，含章节 DOI 如 doi:10.1093/oso/9780195082111.003.0010 "Counting-out Rhymes"、doi:10.1093/oso/9780195082111.003.0011 "North Carolina Ballads"、doi:10.1093/oso/9780195082111.003.0004 "Sound"]**。核心论点：口传文本的稳定性来自**多重约束的交叉**（韵律、音韵、意象、主题结构同时约束下一个词），而非逐字背诵。**工程含义：高度格律化的内容（史诗、咒语、族谱、律条口诀）的每跳失真率应显著低于散文式的消息。**
- **现代序列复述的量化**：Dickinson, D. L. & Drummond, S. P. A. (2025) "The impact of insufficient sleep on the serial reproduction of information", *Sleep Advances*, doi:10.1093/sleepadvances/zpaf026 **[已验证：Crossref + Europe PMC 全文 PMC12146842]**。n = 155，最多三跳的故事复述链。原文："While story content decayed with each retell…"。量化系数见第 4 节（**并附我对其符号方向的疑虑**）。另见 Kashima, Y. & Yeung, V. (2010) "Serial Reproduction: An Experimental Simulation of Cultural Dynamics", *Acta Psychologica Sinica* 42(1): 56–71, doi:10.3724/sp.j.1041.2010.00056 **[已验证：Crossref]**；Mesoudi, A. & Whiten, A. (2008) "The multiple roles of cultural transmission experiments in understanding human cultural evolution", *Phil. Trans. R. Soc. B*: 3489–3501, doi:10.1098/rstb.2008.0129 **[已验证：Europe PMC 元数据／摘要；非 OA，正文未读]**。摘要原文指出 transmission chain method "has been used to identify content biases in cultural transmission"。
- **口传作为史料**：Vansina, J. (1985) *Oral Tradition as History*, doi:10.2307/jj.36106057 **[已验证：Crossref]**。**"floating gap"（漂浮空白）概念——口传社会的时间深度呈两端厚中间薄：近世代有细节，起源神话有细节，中间是一段不断向前漂移的空白——我本次未读到原文，标记 [凭记忆·未验证]，但这个结构对我们的"民间传说 vs 官修史"分层极其关键，建议后续核验。**
- **文字的后果**：Goody, J. & Watt, I. (1963) "The Consequences of Literacy", *Comparative Studies in Society and History* 5(3): 304–345, doi:10.1017/s0010417500001730 **[已验证：Crossref]**。核心：口传社会的过去会被**持续地重写以适应当下**（"structural amnesia"，无用的族谱分支被静默遗忘）；文字使得旧版本**不再消失**，从而首次产生"矛盾的史料"与"历史批评"这种活动。**这是我们模拟中"世界内历史学家"这一角色能够出现的前提条件，且它必须是内生的——只有当有文字、有档案、有多份互相矛盾的记录时，历史学才可能作为一种职业涌现。**
- **文化记忆的时间尺度**：Assmann, J. & Czaplicka, J. (1995) "Collective Memory and Cultural Identity", *New German Critique* 65: 125, doi:10.2307/488538 **[已验证：Crossref]**。区分"交往记忆（communicative memory）"与"文化记忆（cultural memory）"。**其著名的交往记忆跨度约 80–100 年（三到四代）的数字，本次未从原文确认，标记 [凭记忆·未验证]。**
- **传统的发明**：Hobsbawm, E. & Ranger, T. (eds.) *The Invention of Tradition*（1983；本次验证到 2012 剑桥版 doi:10.1017/cbo9781107295636 与 1986 书评 doi:10.2307/25142744 **[已验证：Crossref]**）。含义：官方叙事不是对事实的失真副本，而是**为当下政治目的主动构造的、伪装成古老的新事物**。

### 2.14 ORBIS：前现代交通／通信成本的完整参数化模型（本简报最重要的可直接复用资产）

- **出处**：Scheidel, W., Meeks, E. & Weiland, J. (2012) *ORBIS: The Stanford Geospatial Network Model of the Roman World, Version 1.0*, Stanford University. **[已验证：本次直接下载并解析了 56 页 PDF 全文，第 4 节所有数字均为原文引用]** URL: https://orbis.stanford.edu/
- **模型形态**：不是社会网络模型，而是**加权多模态交通网络上的最小成本路径模型**。751 个站点（其中 268 个海港），84,631 km 道路／沙漠路径，28,272 km 可通航河流与运河，900 条海路（连接 450 对站点的双向），海路总长月均 180,033 km；共 1,371 条基础路段，模拟出超过 363,000 个离散成本结果。覆盖约 1,000 万平方公里。时间基准约公元 200 年。
- **为什么这是我们最该抄的东西**：它把"距离"替换成"**时间成本 + 货币成本 + 季节**"，且陆／河／海三种介质、14 种陆行方式各有独立速度。**这正是"信息边界"的物理底座**：一条消息能不能在冬天翻越某个山口，是可计算的，而不是叙事决定的。
- **已知局限（作者自述）**：坡度对速度的影响最终未能建模（因为路线轨迹精度不足、缺乏可比的历史证据）；河流速度变化被"保持在最低限度"；模拟限定白昼行进；只有尼罗河做了季节性区分。
- **对本项目的直接任务**：**东亚没有 ORBIS。**我们需要自建一个东亚版成本表面（黄河／长江水系、季风、秦岭—淮河、河西走廊、蒙古高原、日本海）。ORBIS 的参数可作为**同技术水平的先验**（畜力、帆船、人力的生理上限在欧亚大陆是相通的），但水文与季风必须重做。

---

## 3. 可直接用于本项目的机制清单

> 每条格式：**输入 → 输出** / 数学或算法草图 / 时间尺度 / 空间粒度 / 证据等级 / 为什么这样简化。
> 证据等级按全项目定义：A 多源实证+可用参数；B 机制共识但参数需自选；C 有实质争议或单一来源；D 我们为让模拟能跑而做的假设。

---

### M1 —— 分层社会网络（Multiplex Social Graph）

**输入**：人口个体表（年龄、性别、居住地、家户、职业、宗族、宗教、官职、财富分位）、聚落地理、制度状态。
**输出**：一个多层图 G = {L_kin, L_coresidence, L_economic, L_institutional, L_ritual}，每层有独立的边权 w ∈ (0,1] 与"最近激活时间"。

**算法草图**：
```
每层独立生成，但共享节点集：
  L_kin          : 由婚姻/生育事件确定性生成（见 M2）。权重 = 1/(1+谱系距离)。
  L_coresidence  : 同家户全连接（w=1.0）；同村按 min(1, k/(村人口)) 采样（w~0.3–0.6）。
  L_economic     : 由市场/贸易/雇佣事件生成，权重 = 近 T 期交易次数的对数。
  L_institutional: 由官职/军队/学派/寺院的成员关系生成 —— 这一层天然重尾。
  L_ritual       : 由共同参与仪式/结拜/师徒生成。稀疏但强。

有效连接强度： w_ij = 1 - Π_layers (1 - w_ij^(layer))
```
**为什么必须分层而不是单层**：Padgett & Ansell 的 robust action 只在多层且各层不重合时成立；单层图无法表达"他是我姻亲但不是我同僚"。这是本项目政治机制的基础设施。

- 时间尺度：kin 层按事件更新（婚／生／死）；其余层每模拟年重算一次增量。
- 空间粒度：个体级（仅对 named agents）；群体级（对匿名人口，见 M14）。
- **证据等级：B**（多层网络与 robust action 有共识，但各层权重取值需自选）。
- 简化说明：真实社会的层次远不止 5 层，且层间有交互效应。我们固定 5 层是为了让 `w_ij` 可在 O(1) 内合成。

---

### M2 —— 亲属图与婚配规则采样器

**输入**：适婚个体池、EA 风格的规则参数（descent、residence、cousin-marriage、inheritance）、地理距离、社会地位。
**输出**：婚姻事件流；由此确定性地生成 L_kin 与继承／居住的后果。

**算法草图**：
```
for each 适婚个体 ego:
    候选集 C = {alter | 距离(ego, alter) < d_max
                     ∧ 未违反外婚规则(clan/lineage/moiety)
                     ∧ 未违反乱伦禁忌(按 EA023 参数)}
    偏好打分 s(alter) = β_status·地位匹配
                      + β_kin ·偏好表亲类型匹配(按 EA025)
                      + β_dist·log f(d)            # f(d) 见 M3
                      + β_alliance·(两族现有联盟收益)
                      + ε_Gumbel                     # 使之为离散选择模型
    以 softmax(s) 采样，双向接受则成婚。
婚后居住地：按 EA012 参数抽取 patrilocal / matrilocal / neolocal / ...
继承：按 EA074/EA076 参数分配土地与动产。
```
**p-graph 副产品**：以婚姻对为节点、个体为边构造有向无环图，其**双连通分支即为"结构内婚集团"**（White 1997）——直接把"门阀／世家／通婚圈"从数据里算出来，不需要预先定义。这是一个每 50–100 模拟年跑一次的批处理任务，输出可直接喂给政治模块作为"派系"候选。

- 时间尺度：婚姻事件级（个体一生 0–3 次）；p-graph 分析每 50–100 年一次。
- 空间粒度：个体级；`d_max` 按生产方式设定（觅食者可跨营地，定居农民多在数十公里内）。
- **证据等级：A**（EA 的规则分布是可下载可计算的实测数据，见第 4 节；但把"规则分布"当作"规则演化的初值/先验"是我们的假设，那部分是 D）。
- 简化说明：真实亲属称谓体系（Iroquois/Crow/Omaha/Eskimo…）对婚配的约束远比"允许/禁止表亲"复杂。我们只实现"外婚单位 + 表亲允许类型 + 偏好类型"三个开关，因为这三项已经能产生质上不同的网络拓扑（交表婚会产生环形联姻链，从而产生长期稳定的部落联盟；禁止一二代表亲会强制扩大通婚半径，从而加大信息传播半径）。

---

### M3 —— 空间交互核（成本表面而非欧氏距离）

**输入**：两点坐标、地形／水系／季节、当前交通技术。
**输出**：`travel_time(a, b, mode, month)`、`travel_cost(a, b, mode, month)`、以及派生的交互衰减 `f(a,b)`。

**算法草图**：
```
# 一次性预计算（每当路网/技术/气候带变化时重算）：
构造多模态图 N：陆路段(带坡度惩罚) ∪ 河段(上下行速度不同) ∪ 海段(按月风况)
每条边赋 (t_edge, cost_edge)  ← 用第 4 节 ORBIS 参数表作为速度先验
T[a][b] = Dijkstra 最短时间；  C[a][b] = Dijkstra 最低成本

# 运行时：
f(a,b) = exp( -T[a][b] / τ )          # τ = 内容相关的"耐心尺度"，单位：天
或     = T[a][b]^(-α)                  # α ≈ 1–2
交互强度 I_ab = M_a · M_b · f(a,b)     # M = 人口或经济质量（引力模型）
```
**关键设计决定**：`f` 的自变量必须是**旅行时间**，不是欧氏距离。渡过长江与走 30 公里平原的欧氏距离可能相同，信息成本相差一个数量级。

- 时间尺度：预计算按世纪或按技术突破触发；查询为 O(1)。
- 空间粒度：聚落级（数百到数千个节点，与 ORBIS 的 751 站点同量级）。
- **证据等级：A（速度参数，来自 ORBIS 全文）/ B（衰减核的函数形式与 τ、α 的取值）**。
- 简化说明：把连续地表压缩成数百个节点 + 路段，是 ORBIS 自己做的取舍，理由是"更细的路网对整体结构结论影响甚微"（作者自述）。我们采纳同一取舍，因为它把每次查询从栅格路径规划降到查表。

---

### M4 —— 消息对象与时序传播算法（本简报的核心交付）

**输入**：世界事实事件（由规则内核产生，带 event_id）、观察者集合、网络 G、成本表面 T。
**输出**：每个 agent 的信念库（belief store）中新增的 belief 记录。

**数据结构**：
```python
# 世界事实（模拟器私有，agent 永不可直接读取）
Event = {
  "event_id": UUID,
  "t_world": int,            # 真实发生时间（tick）
  "loc": SiteID,
  "type": str,               # BATTLE / HARVEST_FAIL / DEATH / EDICT / OMEN / ...
  "payload": {...},          # 真实的数值：真实伤亡、真实粮价、真实死因
  "caused_by": [event_id],   # 因果 DAG 的入边（MANDATE 第 2 条）
  "rng_seed": int
}

# agent 可获得的信念（agent 决策时唯一可读的东西）
Belief = {
  "belief_id": UUID,
  "about_event": UUID | None,   # None = 纯谣言，世界上没有对应事实
  "holder": AgentID,
  "content": {...},             # 已失真的 payload 副本
  "t_claimed": int | Interval,  # 信念中的"事情发生时间"（可能错）
  "t_received": int,            # 我是什么时候知道的
  "hops": int,                  # 经过了几手
  "channel": Enum,              # OBSERVED / KIN / NEIGHBOR / MARKET / OFFICIAL
                                # / SPY / TEXT / RITUAL
  "source": AgentID | DocID | None,
  "confidence": float,          # [0,1]，agent 主观置信
  "provenance": [belief_id],    # 我这条信念是从哪些信念合成来的
  "distortions": [str]          # 已施加的失真算子列表（便于事后审计）
}
```

**传播算法（每 tick，或每"信息 tick"）**：
```
1. SEED（本地观察）
   for e in 本 tick 的 events:
       for a in agents_at(e.loc) ∪ agents_with_LOS(e):
           emit Belief(about=e, hops=0, channel=OBSERVED,
                       content=perceive(e.payload, a),   # 已有观察噪声
                       confidence=0.9, t_claimed=e.t_world)

2. ENQUEUE（入队，带物理延迟）
   for b in 新产生/待转述的 beliefs:
       for alter in neighbors(holder) 按 M5 的规则筛选:
           delay = T[loc(holder)][loc(alter)]  (若同地则 = 0..1 天)
                   + channel_latency[b.channel]   # 官方文书要走流程
           push (t_now + delay, alter, b) 到全局优先队列

3. DELIVER（出队，施加失真）
   pop 所有 due 的 (t, alter, b):
       if 该 alter 已持有关于同一 about_event 的信念:
           MERGE（见 M8b）：可能强化 confidence，也可能产生"两种说法"
       else:
           b' = distort(b)                # 见 M8
           b'.hops += 1
           b'.t_received = t
           b'.confidence = decay(b.confidence, b'.hops, channel_trust[b.channel],
                                 trust(alter, b.source))
           insert b' into alter.belief_store

4. STIFLE（停止传播）
   若 alter 发现邻居中已知比例 > s，则以概率 p_stifle 把该 belief 标记为
   "不再转述"（Daley–Kendall 机制）——这是"永远有人不知道"的来源。
```
**必须是 time-respecting path**：优先队列天然保证了 A→B→C 的时间序，静态图上的可达性不等于信息可达性（Roller 2025）。

- 时间尺度：消息 tick 建议为 1 天（战时／京畿）到 1 月（边远地区）自适应；世界主 tick 可以是年。
- 空间粒度：个体级（named agents）+ 聚落级（匿名人口用 M14 的分室近似）。
- **证据等级：B**（结构来自 Daley–Kendall + 时序网络 + ORBIS 延迟三者的组合，是标准做法；但组合本身与具体常数是我们的设计）。
- 简化说明：我们**不**模拟每一次对话。只在网络边上按 Poisson 强度 λ_ij = w_ij · 社交预算 抽样"接触事件"，把 O(N²) 降到 O(E)。

---

### M5 —— 简单传染 / 复杂传染的二分派发

**输入**：belief 的内容类型。
**输出**：使用哪一套传播规则。

```
SIMPLE   (一次曝光即可传递)  ： 事实型 —— 皇帝死了 / 河决了 / 粮价 / 敌军来了 / 天象
COMPLEX  (需 θ 次独立曝光)  ： 采纳型 —— 改宗 / 造反 / 新农具 / 新葬俗 / 新度量衡
                              / 承认某人为王
```
- SIMPLE：用 M4 的队列，每次接触以概率 p_tell 转述。
- COMPLEX：agent 维护 `exposure_count[topic][distinct_sources]`；当
  `|{distinct sources who adopted}| / |neighbors|  ≥ θ_i` 时才"采纳"（并从此成为传播源）。
  θ_i 由个体属性内生：θ_i = clamp(θ_0 + β_risk·风险厌恶 + β_stake·既得利益
  − β_desperation·饥饿/绝望 − β_kin·已采纳的近亲比例, 0.02, 0.95)

**为什么这个二分不可省略**：如果一切都用 SIR，宗教会像流感一样在十年内席卷大陆，制度会瞬间同质化；如果一切都用阈值模型，"皇帝死了"这种消息传不出京城。这两种错误都会摧毁世界的可信度。Centola & Macy (2007) 的"长弱连接对复杂传染无用"意味着：**孤悬的边疆聚落可以很快知道京城的新闻，却几十年都不会改宗** —— 这正是我们想要的历史质感。

- 时间尺度：SIMPLE 按天／周；COMPLEX 按年（阈值检查每年一次即可）。
- 空间粒度：个体（COMPLEX 必须个体级，因为它依赖邻居的具体身份计数）。
- **证据等级：A（该二分本身有实验证据：Centola 2010）/ B（θ 的分布形状与系数）**。

---

### M6 —— 阈值级联作为"重大事件生成器"

**输入**：某议题下全体 agent 的阈值分布 + 网络拓扑 + 一个触发扰动（饥荒、败仗、征税、异象）。
**输出**：级联规模（可能为 0，可能全局），以及完整的采纳时序（谁先谁后）。

**判据（可解析预筛，避免每 tick 全网模拟）**：
- 计算网络中的"脆弱节点"（θ_i ≤ 1/k_i，即一个邻居就能带动）的比例与其构成的巨型分支大小。若脆弱节点巨型分支不存在，全局级联概率 ≈ 0，跳过详细模拟。
- 若存在，跑 M5 的 COMPLEX 动力学，记录级联的时序与因果边。
- Singh et al. (2013) 的结果保证：**即使 θ 很高，只要初始发动者比例超过 p_c(θ)，仍会全局爆发**；且**社群结构比同质随机网络更有利于扩散**——所以我们的模块化网络会比随机网络更容易出现地方性起义，而不是全国同步暴动。这是对的。

- 时间尺度：事件级（一次级联通常在数月到数年内完成）。
- 空间粒度：个体 + 聚落。
- **证据等级：A（模型有解析与实验支持）/ D（阈值到具体社会变量的映射系数完全是我们设的）**。
- **纲领对齐**：这是"叛乱不能因为戏剧性而发生"的核心保障。一次起义的完整因果链 = 阈值分布如何被前若干年的饥荒／征税／败仗压低 + 网络如何被前若干代的联姻／移民重塑 + 哪个具体扰动越过了 p_c。**每一步都可查询。**

---

### M7 —— 可获得信息集（Available Information Set）—— 直接回答本简报的核心问题

对每个 named agent 与每个组织，定义：

```
AvailableInfo(a, t) =
      LocalObservation(a, t)                     # 本地观察
    ∪ SocialInflow(a, t)                         # 社会网络（M1 × M4）
    ∪ InstitutionalChannels(a, t)                # 制度化情报渠道
    ∪ TextAccess(a, t)                           # 文字记录
```

**四个来源的差异化参数（这是让世界有质感的地方）：**

| 来源 | 延迟 | 失真／跳 | 覆盖 | 可伪造性 | 成本 |
|---|---|---|---|---|---|
| LocalObservation | 0 | 观察噪声 σ_obs，无 hop 失真 | 半径极小（视线 + 当日步行） | 不可（但可被误解） | 0 |
| Kin / Neighbor | 天—月 | 高（口传，schema 变形） | 广但衰减快 | 低（无人有动机） | 极低 |
| Market / 商队 | 周—季 | 中（有数字，商人有核实动机） | 沿贸易路线，跳跃式 | 中（有牟利动机） | 低 |
| Official 上报 | 由制度规定（驿传） | 低—中，但**有系统性偏向**（报喜不报忧、瞒报灾情、虚报战功） | 只覆盖行政层级 | **高**（官员有强动机） | 高（财政） |
| Spy / 密探 | 中 | 中，但**偏向委托人预期** | 定向、稀疏 | 高 | 很高 |
| Text / 档案 | **可为负无穷**（读到几百年前的东西） | 每次抄写引入错误，但**不随时间自然衰减** | 只对识字者 | 高（可篡改、可焚毁） | 中（识字 + 获取） |

**关键：TextAccess 是唯一能突破时间的通道。**这一条决定了文明的性质。在无文字世界，`AvailableInfo` 的时间深度 ≈ 活人的记忆（Assmann 的"交往记忆"）；一旦有文字与档案，时间深度变成"最老的可读文本"，于是才可能出现"复古改制""托古改制""考据学""伪书"这些现象——全部内生。

**组织的信息集**：组织不是 agent 的简单并集。定义
```
AvailableInfo(Org) = ⋃_{a ∈ members} filter_upward(AvailableInfo(a))
```
`filter_upward` 是**层级失真算子**：每上升一个官僚层级，(i) 信息被聚合（个体细节丢失，只剩统计量），(ii) 被选择（对上级不利的以概率 p_suppress 丢弃），(iii) 被延迟（一个处理周期）。**这自动生成"中央不知道地方在饿死人"这一类经典失败**，而不需要任何脚本。

- 时间尺度：每 agent 每决策点重算（惰性求值，只在 agent 需要决策时物化）。
- 空间粒度：个体 / 组织。
- **证据等级：B（结构）/ D（表中的具体延迟与失真数值）**。
- 简化说明：真实的"可获得信息"还包括身体状态、直觉、宗教启示等。我们只建可传递、可追溯的部分。

**给 LLM agent 的接口约定（必须写死在代码里，不能靠提示词自律）：**
```
llm_context(a, t) = render(AvailableInfo(a, t))   # 只渲染信念，不渲染 Event
```
即：**LLM 拿到的 prompt 里，物理上不存在世界真实状态的字段。**不是"请你假装不知道"，而是那段数据从未进入 context window。这是 MANDATE 第 4 条唯一可靠的实现方式。

---

### M8 —— 失真算子（Distortion Operators）

失真**不是高斯噪声**。Bartlett 的实验结论是失真有方向。建议实现以下算子，每跳按内容类型与信道以概率组合施加：

| 算子 | 作用 | 触发条件 | 后果举例 |
|---|---|---|---|
| `ABSTRACT` | 丢弃细节，保留骨架 | 每跳高概率 | "张三在渭水南岸中箭" → "有个将军在河边死了" |
| `SCHEMATIZE` | 向接收者的既有图式靠拢 | 内容与接收者文化不符时 | 异族的仪式被描述成本族熟悉的仪式 |
| `ROUND` | 数字规整化 | 含数字时 | 4,713 人 → "五千" → "上万" |
| `INFLATE` | 数字沿传播方向单调放大 | 内容有戏剧性时 | 每跳 ×(1+ε)，ε ~ Beta，正偏 |
| `MERGE_ACTORS` | 多个人物合并为一个 | hops 大且人物无独立标识时 | 三代同名将领合并成一个不死英雄 |
| `COMPRESS_TIME` | 相隔多年的事件被叙述成连续 | hops 大时 | 两次战役合并成一场 |
| `ADD_CAUSE` | 补上一个因果解释 | 原信念缺 `caused_by` 时 | "所以是因为国君失德" |
| `ATTRIBUTE_AGENCY` | 把结构性原因归因到个人／神明 | 高概率，尤其在低识字社会 | 瘟疫 → 某人下咒 |
| `MORALIZE` | 附加道德评价并据此改写细节 | 与接收者价值冲突时 | 胜者变成仁君，败者变成暴虐 |
| `DROP` | 整条丢失 | 与接收者利益／图式严重冲突 | 不利于本族祖先的记载消失（structural amnesia） |

**数学形式（可实现的最小版）**：
```
distort(b, receiver):
    for op in OPS:
        if rand() < p_op(b.hops, b.channel, b.content_type,
                         cultural_distance(sender, receiver),
                         格律化程度(b)):        # Rubin: 韵文抗失真
            b = op(b)
            b.distortions.append(op.name)
    b.confidence *= γ_channel                    # γ_OFFICIAL > γ_KIN > γ_RUMOR
    return b
```
**`格律化程度` 这个字段来自 Rubin (1995)**：史诗、族谱、律条口诀应当有极低的 `p_ABSTRACT` 与 `p_ROUND`，代价是它们的信息密度低、更新慢。这自动解释了为什么前文字社会会把重要信息编成韵文——**如果我们把这条做对，"口传诗歌传统"可以作为一种技术被 agent 发明出来。**

- **证据等级：B（方向性失真有 Bartlett 以来的稳固实验共识）/ D（每个算子的概率参数完全由我们设定，文献未提供可用参数——见第 4 节）**。

**M8b —— 冲突信念的合并规则**（同一 agent 收到关于同一事件的两个不同版本）：
```
if 版本相容: confidence 按 Bayes 上调，provenance 合并
else:
    if trust(source_A) >> trust(source_B): 采信 A，B 降为 "另一说"
    else: 保留两条，标记 CONTESTED
          —— CONTESTED 的存量正是"史学争议"的种子
```

---

### M9 —— 遗忘、代际衰减与"漂浮空白"

**输入**：belief store、agent 年龄、是否有文字记录。
**输出**：belief 的消失或降级。

```
每年：
  for b in a.belief_store:
      if b 未被使用/复述:
          b.confidence *= exp(-Δt / λ_forget)
      if b.confidence < ε: 删除
  # 关键：agent 死亡时，其 belief_store 中未被传给他人、
  #        且未被写入 Document 的条目 —— 永久消失。
```
**世界层面的后果（自动涌现，不需要额外代码）**：
- 无文字社会：任何超过 ~3 代（约 80–100 年）的事件，只有被反复复述并因此高度变形的版本存活 → 起源神话；中间地带最稀薄 → Vansina 的 floating gap 结构。**[该跨度数字为 [凭记忆·未验证]，见第 9 节]**
- 有文字社会：Document 节点不衰减，但可被销毁（战火、改朝换代的焚毁、虫蛀）与被篡改。于是产生"文献密度随时间指数下降但有幸存者偏差"——这正是真实史学面对的情况。

- 时间尺度：年。
- **证据等级：B（机制共识）/ C（跨度参数）**。

---

### M10 —— 制度化情报渠道（驿传 / 上报 / 密探 / 使节）

**输入**：国家财政、道路技术、行政层级数、官僚忠诚度。
**输出**：一组"高带宽低延迟但昂贵且可腐蚀"的网络边，叠加在 L_institutional 层上。

```
RelaySystem = {
  "stations": [SiteID],              # 站点集合
  "spacing_km": float,               # 站间距（决定换马频率）
  "mode": Enum{FOOT, HORSE, HORSE_RELAY, BOAT},
  "throughput": msgs/day,
  "upkeep_cost": 粮/钱 per year,     # 财政恶化时首先被裁撤 → 帝国的神经先坏死
  "integrity": float ∈ [0,1]         # 被地方势力截留/伪造的程度
}
delay(a→b) = path_length(a,b) / speed[mode]  + 每站换手固定开销
```
**速度参数直接用第 4 节 ORBIS 表**：单人骑马常规 56 km/日；快车（国家驿传或私人信使）67 km/日；**连续换马接力 250 km/日（作者明确说明这是"多日陆上信息传递的绝对速度上限"）**。

**为什么这一条对本项目至关重要**：帝国的最大半径**不是**由军力决定的，而是由"中央下令到地方执行再到反馈回中央"的闭环时间决定的。当闭环时间 > 危机演化时间，中央就只能事后追认既成事实 → 藩镇化。**这个因果链完全由 M3 + M10 的参数决定，不需要任何"帝国衰落脚本"。**同时，`upkeep_cost` 与财政模块耦合，`integrity` 与官僚模块耦合，于是"财政危机 → 驿传废弛 → 中央信息延迟 → 地方坐大 → 财政进一步崩溃"是一个可自我强化的内生回路。

- 时间尺度：制度建立／废弛按年—十年；单条消息按天。
- 空间粒度：站点级。
- **证据等级：A（罗马速度参数）/ D（中国／东亚的对应参数本次未能验证，见第 6、9 节）**。

---

### M11 —— 文本作为一等公民节点

```
Document = {
  "doc_id", "author": AgentID|None, "t_composed": int,
  "claims": [belief_id],       # 文本固化的信念集合
  "copies": [(SiteID, condition)],   # 抄本位置与残缺度
  "script": ScriptID, "language": LangID,
  "readable_by": 谓词(识字层级, 语言, 字体),
  "tampered_by": [(AgentID, t, diff)]   # 篡改历史，模拟器可见，世界内不可见
}
```
- 抄写：每次复制以概率 p_scribal 引入错误（漏字、形近字、注释混入正文）。累积后不同抄本互相矛盾 → **异文与校勘学内生出现**。
- 销毁：战争／火灾／政策性焚毁按概率移除 copies。当 copies 为空，文本永久消失，但**它曾被引用的痕迹**（其他文本中的引文）可能留下 → **辑佚学内生出现**。
- 篡改：掌权者可以对自己控制的 copies 施加 diff。**模拟器保存 diff**（世界事实），世界内的人只看到修改后的版本 → 数百年后如果两个抄本系统重新相遇，矛盾暴露。

- **证据等级：B（Goody & Watt 关于文字后果的论述是经典共识）/ D（p_scribal 等参数）**。

---

### M12 —— 官方史 / 民间传说 / 宗教叙事的分层生成

**这不是三个独立的随机生成器，而是同一套 belief 传播机制在三种不同的选择压力下的产物。**

```
真实事实 DAG  (模拟器私有)
      │
      ├─ 经 M4/M8 传播 ─→ 分散在各 agent 的 belief_store
      │
      ├─ 官方史 = argmax_{叙事 S}  Σ_j  political_utility(S, 当权者 j)
      │            s.t.  S 必须与"广为人知且难以否认的信念"相容
      │            —— 即：可以删除、可以重新归因、可以调整时间与因果，
      │               但不能宣称一场全国皆知的败仗是胜仗。
      │            约束强度 ∝ 该事件在人口中的信念覆盖率。
      │
      ├─ 民间传说 = 高 hops、经过 MERGE_ACTORS / ATTRIBUTE_AGENCY /
      │              MORALIZE 反复作用后的收敛态
      │
      └─ 宗教叙事 = 民间传说 + 制度化固化（写成经典后失真停止，
                     但解释权成为新的政治资源）
```
**LLM 在这里的合法位置**：LLM 可以负责"把一组 belief 与一个政治目标渲染成一篇有文采、有当时文化风格的官方史文本"。LLM **不能**决定哪些事实被删除——那由 `political_utility` 与覆盖率约束计算。这严格符合 MANDATE 第 5 条。

- **证据等级：B（Hobsbawm & Ranger、Goody & Watt 支持机制方向）/ D（效用函数形式）**。

---

### M13 —— 网络演化算子（每年）

```
ADD:    三元闭包 P(i–j | 共同邻居数 m) = 1 - (1-q)^m        # q ~ 0.01–0.1
      + 同质性项 · exp(-属性距离)
      + 空间项 f(d)  (M3)
      + 制度项（新任官职自动连上僚属）
DECAY:  w_ij *= exp(-Δt_since_contact / λ_tie)
DROP:   w_ij < ε 时删边
SHOCK:  死亡（删节点，其结构洞被谁继承是政治机会）
        迁徙（保留少数远程弱连接 —— 移民是历史上最重要的信息桥）
        战争／瘟疫（成批删节点，网络碎裂 → 信息半径骤缩）
```
**注意"移民保留弱连接"这一条**：它是长距离文化传播的主要引擎，而且是**不对称的**——迁出者知道故乡，故乡不一定知道迁出者的现况。**信息流必须是有向的。**

- **证据等级：B**（三元闭包与衰减是网络演化共识；具体 q、λ 需自选）。

---

### M14 —— 计算可行性：三层粒度

数千年 × 百万人口做不了个体级全模拟。建议：

| 层 | 对象 | 网络表示 | 更新频率 |
|---|---|---|---|
| L0 匿名人口 | 按聚落 × 年龄 × 阶层的分室 | 无个体网络；用"聚落间接触矩阵" C_ab = I_ab（M3 引力）做 SIR/阈值的**平均场**近似 | 年 |
| L1 家户／宗族 | 数千—数万个"家族"节点 | 家族级婚姻网、家族级信念（家族共享一个 belief store） | 年 |
| L2 named agents | 数百—数千个人物（君主、将领、大商、宗师、地方豪强） | 完整个体多层网 + 完整 belief store + LLM 决策 | 事件驱动 |

**升降级规则**：当一个 L1 家族的某成员的影响力超过阈值（财富分位、官职、军队规模、追随者数），把他**具现化**为 L2 named agent，并根据其家族的历史合成一份初始 belief store；影响力跌落且死亡后降级归档。**这样"历史人物"是涌现的，不是预设的。**

- **证据等级：D**（这是我们的工程设计，不是文献结论）。
- 代价说明：L0 的平均场近似会**低估**级联的随机性（真实小社群里一次偶然的三人对话就能改变结果）。缓解办法：在 L0 保留一个显式的随机项，并在其方差超过阈值时把该聚落临时升级到 L1。

---

### M15 —— 因果链与可审计性

每条 Belief 保留 `provenance`，每条 Event 保留 `caused_by`，两者构成两张 DAG，并由 `about_event` 交叉链接。于是可以回答：

- "为什么这位君主决定出兵？" → 查他决策时刻的 `AvailableInfo`，找出置信度最高的几条 belief，沿 provenance 回溯到最初的 Event 与所有失真算子。
- "官方史上说他是被谗言所害，真的吗？" → 比较 Document.claims 与 Event.payload，读 `tampered_by`。
- "如果那封信没有被大雪拖延三十天会怎样？" → 从存档的 RNG seed 与队列状态分叉重放（MANDATE 第 6、第 11 条）。

**存储估算（需在 Phase 1 实测）**：belief 记录是本系统最大的数据源。建议 (i) 对 L0/L1 只存聚合信念，(ii) 对 L2 全存但定期把低置信度、无 provenance 引用的条目压缩成摘要，(iii) `distortions` 列表只存算子名与 RNG 子种子，失真过程可按需重放而不必存中间态。

- **证据等级：D**（工程设计）。

---

## 4. 硬数字与参数表

> **原则**：本节只列本次会话中我实际读到或实际计算出的数字。凡我知道但未验证的，一律放进第 9 节，不放这里。

### 4.1 前现代交通与信息速度（ORBIS v1.0，Scheidel/Meeks/Weiland 2012，全文引用）

**陆行（原文："Mean daily travel distances have been set at…"）**

| 方式 | 速度 | 单位 |
|---|---|---|
| 牛车 (ox cart) | 12 | km/日 |
| 挑夫 / 重载骡 (porters or heavily loaded mules) | 20 | km/日 |
| 步行者、行军中的军队、中等负载的驮畜、骡车、骆驼商队 | 30 | km/日 |
| 常规私人车辆旅行（有便利休息点） | 36 | km/日 |
| 加速的私人车辆旅行 | 50 | km/日 |
| 常规骑马 | 56 | km/日 |
| 无辎重的短期急行军 | 60 | km/日 |
| 快车（国家驿传或私人信使） | 67 | km/日 |
| **连续换马接力 (continuous horse relays)** | **250** | km/日 |

- **重要限定（原文）**：除最后一项外，全部以**白昼行进**为前提；最后一项"primarily meant to provide an absolute speed ceiling for multi-day terrestrial information transfer"（主要用于给多日陆上信息传递提供绝对速度上限）。
- 适用时空：罗马帝国，约公元 200 年，铺装道路网。**不确定度**：作者自述未能建模坡度对速度的影响（"Uncertainty about the impact of grade on travel speed is perhaps the most important concern about simulations of time costs, especially for routes in mountainous terrain"）。
- **来源等级：A**

**河运（原文引用）**

| 项目 | 数值 |
|---|---|
| 民用模式，下行，最常见 | 65 km/日（Tiber, Po, Arno, Rhine, Mosel, Rhone, Tyne, Ouse, Witham, 上 Seine, 上 Loire, 上 Garonne, Guadalquivir, Guadiana, Tagus, 上 Danube, Inn, Drava, Sava, Nisava, 中 Euphrates, Orontes, Khabur） |
| 下行调整值 | 75（上 Euphrates）／60（下 Loire、下 Garonne）／55（中 Danube）／50（下 Seine）／45（下 Danube）km/日 |
| 民用模式，上行，默认 | **15 km/日** |
| 上行调整值 | 10（下 Tiber、Rhone、Euphrates）／20（下 Loire、下 Garonne、中 Danube）／25（下 Danube）／30（下 Seine）km/日 |
| 运河 | 15 km/日，双向（保守假定为纤拉） |
| 军用（桨船）模式 | **下行 120 km/日，上行 50 km/日**（恒定） |
| 尼罗河（唯一建模季节性） | 下埃及下行 7–10 月 90，其余月 35；上埃及下行 7–10 月 100，其余月 50。上行：下埃及 7–10 月 90，其余 30；上埃及 7–10 月 65，其余 35。（km/日） |

- **上下行比 ≈ 4:1（民用）是本表最重要的结构性事实**：内河文明的信息与物资是**单向廉价**的，这决定了首都选址、漕运方向与叛乱的地理格局。
- **来源等级：A**

**海运与网络规模（原文引用）**

- 网络：**751 个站点**（其中 **268 个海港**）；道路与沙漠路径 **84,631 km**；可通航河流与运河 **28,272 km**；**900 条海路**（连接 450 对站点的双向），月均总长 **180,033 km**；其中 **158 条**归类为远洋航线（可关闭以模拟沿岸航行 cabotage）；共 **1,371 条基础路段**，生成 **> 363,000 个离散成本结果**；覆盖约 **1,000 万 km²**。
- 海运有两种帆船速度（逆风能力不同）；**较慢船型的平均模拟航速比较快船型低约 1/6**。
- 校准：对照 **200 多条**有史料记载的航行时间，其中 **117 条**用于正式校准；地中海航线中"almost all simulated outcomes differ by less than plus or minus 30 percent from reported values"。
- 表面洋流：地中海与大西洋沿岸表层流"do not normally exceed 0.5 knots except in strong winds"，因此被排除在模型外。
- **来源等级：A**

**货运费率（用于建"信息也有价格"）**

- 以每日每 modius kastrensis 1 denarius 为基准 → 模型采用**每公斤小麦每日 0.1 denarii**。
- 河运（据 301 CE 戴克里先价格敕令 XXXVA.31-33）：**下行 0.0034 denarii/(kg·km)，上行 0.0068 denarii/(kg·km)**；乘客换算 1 人 = 25 modii kastrenses → 下行 0.86、上行 1.72 denarii。
- **来源等级：A**（模型参数）/ **B**（其历史真实性，作者自述价格敕令"seems overly conservative"）。

**跨地中海整体表现示例（原文）**：某条路线 3,099 km 用某模式需若干日，折合 **114 km/日**，成本 7.8 denarii/kg（陆段用驴）；另一变体 **117 km/日**，价格升至 8.8；再一变体 **138 km/日**，价格降至 3.7；最慢变体 **36 km/日**（3,361 km / 93.2 日），价格升四倍至 15.7 denarii/kg。**这组数字最有价值的地方是：时间与成本不是同向的，快 4 倍可以便宜 4 倍（走海路）也可以贵 2 倍（走陆路快递）。我们的模型必须保留这个二维性。**

---

### 4.2 亲属与婚配规则的全球分布（本次我下载 D-PLACE Ethnographic Atlas 原始 CSV 后自己计算）

**数据来源**：`https://raw.githubusercontent.com/D-PLACE/dplace-data/master/datasets/EA/{variables,codes,societies,data}.csv`，仓库许可 **CC BY 4.0**（GitHub API 返回）。**N = 1,291 个社会**（含缺失编码）。以下百分比为我用 Python 直接统计得到，可复现。

**EA043 世系（Descent: major type），N=1291**

| 编码 | 计数 | 占比 | 类型 |
|---|---|---|---|
| 1 | 590 | **45.7%** | Patrilineal 父系 |
| 6 | 362 | 28.0% | Bilateral 双系 |
| 3 | 160 | 12.4% | Matrilineal 母系 |
| 2 | 52 | 4.0% | Duolateral |
| 7 | 50 | 3.9% | Mixed |
| 5 | 48 | 3.7% | Ambilineal |
| NA | 17 | 1.3% | 缺失 |
| 4 | 12 | 0.9% | Quasi-lineages |

**EA012 婚后居住（Marital residence: prevailing pattern），N=1291**：Patrilocal 638 (**49.4%**)、Virilocal 159 (12.3%)、Ambi-viri 107 (8.3%)、Ambilocal 83 (6.4%)、Neolocal 62 (4.8%)、Matrilocal 58 (4.5%)、Avunculocal 54 (4.2%)、Uxorilocal 45 (3.5%)、Ambi-uxo 37 (2.9%)、NA 24、其余 <1%。
→ **父方居住类合计（8+10+12+4）≈ 71%**。这是"男性网络在地连续、女性作为跨村信息载体"的经验基础。

**EA023 允许的表亲婚（Cousin marriages permitted），N=1291**：No first/second cousins 282 (21.8%)、No first cousins 277 (21.5%)、**NA 249 (19.3%)**、Cross-cousin 206 (16.0%)、Any first cousins 117 (9.1%)、Only second cousins 64 (5.0%)、Matrilateral cross only 44 (3.4%)、Trilateral 25 (1.9%)、其余 <1%。

**EA025 偏好的表亲婚**：None preferred 797 (**61.7%**)、NA 249 (19.3%)、Cross-cousin: either 81 (6.3%)、Cross-cousin: matri 44 (3.4%)、All: FaBrDa 44 (3.4%)、Uni: MoBrDa 27 (2.1%)、其余 <1.5%。

**EA015 社区婚姻组织**：Agamous 396 (30.7%)、Segmented no exogamy 261 (20.2%)、Clans 237 (18.4%)、NA 189 (14.6%)、Exogamous 117 (9.1%)、Demes 83 (6.4%)、Segmented with exogamy 8 (0.6%)。

**EA030 聚落形态**：Villages/towns 518 (**40.1%**)、Seminomadic 188 (14.6%)、Dispersed homesteads 151 (11.7%)、Hamlets 106 (8.2%)、NA 104 (8.1%)、Semisedentary 97 (7.5%)、Nomadic 81 (6.3%)、Complex permanent 31 (2.4%)、Impermanent 15 (1.2%)。

**EA031 地方社区平均规模（！本项目直接可用）**，N=1291：**NA 680 (52.7%)**、50–99 人 119 (9.2%)、<50 人 118 (9.1%)、100–199 人 106 (8.2%)、200–399 人 86 (6.7%)、**50,000+ 人 66 (5.1%)**、400–1000 人 61 (4.7%)、5,000–50,000 人 38 (2.9%)、1,000–5,000 人 17 (1.3%)。
→ **在有编码的 611 个社会中，约 63% 的地方社区规模 < 200 人。**这直接给出"日常面对面信息圈"的规模先验。（注意超高缺失率。）

**EA032 地方社区之内的司法层级**：Extended families 644 (49.9%)、Independent families 370 (28.7%)、Clan-barrios 153 (11.9%)、NA 124 (9.6%)。
**EA033 地方社区之上的司法层级（≈政治复杂度）**：**Acephalous 525 (40.7%)**、One level 341 (26.4%)、Two levels 162 (12.5%)、NA 136 (10.5%)、Three levels 83 (6.4%)、Four levels 44 (3.4%)。
→ **超过 40% 的社会在地方社区之上没有任何司法层级**。这是"国家是罕见的、需要解释的现象"的定量支持——我们的模拟不应默认国家会出现。

**EA074 不动产（土地）继承规则**：NA 435 (33.7%)、Patrilineal by sons 354 (**27.4%**)、No inheritance of real property 223 (17.3%)、Patrilineal by heirs 90 (7.0%)、Matrilineal by heirs 60 (4.6%)、Children 55 (4.3%)、Children less for daughters 43 (3.3%)、Matrilineal by sister's sons 31 (2.4%)。
**EA076 动产继承规则**：Patrilineal by sons 415 (32.1%)、NA 382 (29.6%)、No inheritance 132 (10.2%)、Children 89 (6.9%)、Patrilineal by heirs 87 (6.7%)、Matrilineal by heirs 73 (5.7%)、Children less for daughters 68 (5.3%)、Matrilineal by sister's sons 45 (3.5%)。

**EA017 最大父系亲属群**：None 593 (45.9%)、Sibs 400 (31.0%)、Lineages 170 (13.2%)、Phratries 62 (4.8%)、Moieties 51 (4.0%)。
**EA019 最大母系亲属群**：None 1052 (**81.5%**)、Sibs 120 (9.3%)、Lineages 44 (3.4%)、Moieties 30 (2.3%)、Phratries 17 (1.3%)。

- **来源等级：A**（数据可下载、可复现、我已实际计算）。
- **⚠️ 使用警告**：见第 7、8 节的 Galton 问题与时间错位问题。**这些分布是"民族志现在时"（多为 19–20 世纪记录），不是史前分布。**只能当作**先验的形状**，不能当作我们模拟公元前 5000 年的目标值。

---

### 4.3 觅食者社会的实测网络参数

**Ache / Hadza 跨营地互动（Hill et al. 2014, PLOS ONE 9:e102806，本次读到全文 Table 1 与结果段）**

| 项目 | Ache | Hadza |
|---|---|---|
| 研究期人口 | **560** | **950** |
| 研究期居住营地数 | ~20 | 49（摘要作 42，Table 1 作 49；原文两处不一致） |
| 营地位置 | mobile | tethered |
| 部落核心领地 | **5,270 km²** | **3,000 km²** |
| 访谈的同性 dyad 数 | 351 | 850 |
| 受访者人数 | 32 | 75 |
| 目标人数 | 88 | 400 |

- 随机成年同性 dyad 之间发生某项文化／合作互动的**年概率：5%–29%**（依活动类型而异）。
- **一生中**：Hadza／Ache 男性预期"与 303 名男性一起狩猎"、"观看 395 名不同男性制作工具"、"观察 300 名以上男性"。原文："adults typically interact with more than three hundred same-sex adults during their lifetimes. This implies a **social universe of about a thousand individuals**, when opposite-sex adults [are included]"。
- 对照：黑猩猩典型社群 11 头成年雄性，一生预期只与约 **21** 头其他成年雄性互动。
- **一对同时成年的 Ache/Hadza 个体，两人都还活着的预期时长约 27 年**；黑猩猩雄性对为 **6 年**。
- 回归结果：**仪式关系（ritual relationships）对互动率的提升大于亲缘关系；姻亲的互动率高于无关系 dyad。**
- **来源等级：A**（本次读到全文）。
- **对本项目的直接用法**：把"一个人一生的社会宇宙 ≈ 1000 人"作为觅食阶段的默认值，而不是 Dunbar 的 150。150 更接近"活跃维护的强关系数"，1000 接近"可识别、可能提供信息的全部人"。**我们的 belief 传播应当跑在后者上。**

**Agta 多营地网络（Migliano et al. 2020, Sci Adv 6:eaax5913，本次读到全文）**

| 项目 | 森林组 | 沿海组 |
|---|---|---|
| 营地数 | **7** | **3** |
| 空间范围 | 36 km² | 5 km 海岸 / 25 km² |
| 成年人数 | **53**（28 女） | **37**（17 女） |
| 测量方式 | 无线感应器（mote），记录 3 m 内接触，每小时一次，持续一个月 | 同 |
| 全部（营地内+营地间）dyad 中被记录到至少一次的比例 | **35%**（477/1378） | **69%**（458/666） |
| 营地内 dyad 记录率 | **59%**（181/309） | **85%**（257/304） |
| 营地间 dyad 记录率 | **28%**（296/1069） | **56%**（201/362） |
| 加权后营地内占比 | 53%（9,321/17,555） | 69%（10,439/15,224） |

- 原文结论：营地内 dyad 更可能被观察到、且连接更强；近亲 dyad 在营地内的占比显著高于营地间。
- **来源等级：A**。
- **对本项目的直接用法**：这是 M1 中 `L_coresidence` 层边概率的经验取值——**营地内 0.6–0.85，营地间 0.28–0.56**（在 36 km² 尺度内）。注意这是"一个月内至少一次 3 米内接触"的定义，不是"友谊"。

---

### 4.4 网络结构的经验规律

| 量 | 数值 | 范围 | 来源 |
|---|---|---|---|
| 真实网络语料规模 | **928 个网络数据集**（来自 ICON） | 生物／信息／社会／技术／交通 | Broido & Clauset 2019（全文） |
| 社会网络中 "Not Scale Free" 比例 | **50%** | 该语料的社会网络子集 | 同上 |
| 社会网络中 "Super-Weak" 比例 | 41% | 同上 | 同上 |
| 社会网络中落入 "Strong" 或 "Strongest" 的比例 | **0（原文：not a single network）** | 同上 | 同上 |
| 全语料 "Not Scale Free" | 49% | | 同上 |
| Dunbar 数的系统发育回归估计 | 贝叶斯法 **69–109**，GLS 法 **16–42** | 灵长类外推到人 | Lindenfors et al. 2021（摘要） |
| 上述估计的 95% CI | **4–520** 与 **2–336** | 同上 | 同上 |

**Medici 婚姻网络（我本次用 NetworkX 内置数据自己计算）**

| 家族 | 度 | 归一化中介中心性 |
|---|---|---|
| **Medici** | **6** | **0.522** |
| Guadagni | 4 | 0.254 |
| Albizzi | 3 | 0.213 |
| Salviati | 2 | 0.143 |
| Strozzi | 4 | 0.103 |

（网络共 15 个家族、20 条婚姻边；数据源标注 Breiger & Pattison 1986, *Social Networks* 8(3): 215–256。**来源等级：A**，数据与计算均可复现。）

---

### 4.5 人口—网络的可行性下界

| 量 | 数值 | 条件 | 来源 |
|---|---|---|---|
| 最小可存活觅食者人口（MVP） | **40–140 人** | 定义为 95% 的模拟运行能存活 400 年；依婚配限制与死亡率而变 | White 2017, JASSS 20(4), doi:10.18564/jasss.3393 **[已验证：本次读到文章页]** |
| 最宽松婚配条件（多妻、无乱伦禁忌）下的 MVP | 40–60 人 | 同上 | 同上 |
| 最严格条件下 | 150 人足以维持 | 同上 | 同上 |
| Wobst (1974) 的"最小均衡规模" | **175–475 人** | 含空间分布因素 | 经 White 2017 转引 **[原文未读，等级 C]** |
| 模型人口学参数 | 成年年龄 15；女性生育期 11–55；最大寿命 86；产后闭经上限 72 周；家户抚养比阈值 1.75；死亡率乘数 1／2／4；生育率取自 !Kung 与 Ache 的年龄别生育表 | | White 2017 |

**对本项目的用法**：**觅食社会的最小自维持婚配网络在 100 人量级，而不是 500 人量级。**这意味着我们可以让世界从很少的、彼此几乎不通信的小群体开始，而它们仍然是人口学上可行的——这正是"文明之前"应有的样子。

---

### 4.6 序列复述的失真量化（**证据薄弱，谨慎使用**）

Dickinson & Drummond 2025（*Sleep Advances*, doi:10.1093/sleepadvances/zpaf026，n=155，最多三跳故事复述链）的回归表（本次读到原表）：

| 因变量 | Retell2 系数 | Retell3 系数 | 常数项 |
|---|---|---|---|
| % Characters Lost | 0.06 (0.03) | **0.13** (0.03)** | −0.83** |
| % Details Lost | 0.07* (0.03) | **0.08** (0.02)** | −0.71** |
| % Event Preservation Lost | 0.03 (0.05) | **0.12** (0.04)** | −0.38* |

（Observations 924／924／851；155 名参与者；含故事固定效应。）

**⚠️ 我的谨慎声明**：原文正文写道 "the positive coefficients on the Retell2 and Retell3 indicators indicate the fidelity is lost at a lesser rate in subsequent retells compared with the 1st retell"，这与正系数的通常读法相反；且该文的因变量是**相对于本人收到的版本**（而非原始故事）计算的。因此**我无法从中提取一个可靠的"每跳失真率"参数**。可以确定的只有：(i) 内容在每一跳都显著衰减；(ii) 三跳之内人物名与细节的损失是**数十个百分点量级**（常数项 −0.83／−0.71 结合基线暗示第一跳损失已经很大）。

- **来源等级：C**。
- **结论：文献未提供可直接使用的"每跳失真率"参数。**我们必须自行设定（见第 9 节 D 级），并把它做成可调参数，用"三代之后的传说与事实的偏离程度是否合理"来事后校准。

---

### 4.7 数据库规模（用于第 5 节）

| 数据库 | 规模 | 来源 |
|---|---|---|
| CBDB 中国历代人物传记资料库 | **约 491,000 人**（截至 2021-05）；**275,945** 条官职任命记录；**482,953** 条亲属关系记录；**160,219** 条非亲属社会关系记录；**470 对**编码关系类型；覆盖 **7–19 世纪** | Chen & Wang 2022, *Journal of Open Humanities Data* 8, doi:10.5334/johd.68 **[已验证：本次读到全文页]** |
| D-PLACE | **超过 1,400 个社会** | Kirby et al. 2016, PLOS ONE **[已验证：本次读到摘要]** |
| D-PLACE / EA 子集 | **1,291 个社会**，94 个变量（`variables.csv` 95 行含表头），`data.csv` 121,355 条观测 | 我本次实际下载并统计 |
| ORBIS | 751 站点、1,371 路段、>363,000 个成本结果 | ORBIS v1.0 全文 |
| ICON | Broido & Clauset 从中取用 928 个网络数据集 | Broido & Clauset 2019 全文 |
| iWiW（现代对照） | 峰值 3,000,000 用户、300,000,000 条好友关系，2002–2012 全生命周期 | Lengyel et al. 2020 全文 |

---

## 5. 数据集与数据库

| 名称 | 内容 | 覆盖 | 访问方式 / URL | 许可 | 对本项目的用途 |
|---|---|---|---|---|---|
| **D-PLACE** | 聚合的跨文化数据库：Ethnographic Atlas、SCCS、Binford Hunter-Gatherer、WNAI，加上 GMTED2010／GSHHS／MODIS／TEOW／Kreft／Jenkins／ecoClimate 等环境层 | >1400 社会，全球 | 网站 https://d-place.org/ ；**原始 CSV 直接可取**：`https://raw.githubusercontent.com/D-PLACE/dplace-data/master/datasets/<EA|SCCS|Binford|WNAI>/{variables,codes,societies,data}.csv` | 网站声明 **CC BY-NC 4.0**；GitHub 仓库 API 返回 **CC BY 4.0**（两者不一致，使用前需澄清） | **M2 婚配／继承／居住规则的先验分布**（已用，见 4.2）；Binford 子集可给觅食者流动性参数 |
| **Ethnographic Atlas (EA)** | Murdock 等的 94 变量民族志编码 | 1,291 社会 | 同上；codebook 引用见 `datasets/index.csv` | 同上 | 见 4.2 |
| **SCCS** | 标准跨文化样本，为解决 Galton 问题而设计的 186 社会子样本 | 186 社会 | 同上路径 `datasets/SCCS/` | 同上 | **做统计检验时应优先用 SCCS 而非 EA**（见第 7 节） |
| **Binford Hunter-Gatherer** | Binford (2001) 的觅食者环境—行为数据集 | 觅食者 | `datasets/Binford/` | 同上 | 觅食阶段的流动性、群体规模、领地面积参数 |
| **WNAI** | Jorgensen (1980) 西北美 172 部落 | 172 | `datasets/WNAI/` | 同上 | 区域级校准对照 |
| **CBDB（中国历代人物传记资料库）** | 人物、亲属、社会关系、官职、地址、入仕途径 | 7–19 世纪，~491,000 人 | Harvard/北大/中研院合作项目；Access 与 SQLite 版在 Dataverse 与 GitHub；另有在线查询与 API | **CC BY-NC-SA 4.0** | **本项目最重要的东亚校准集**：可算真实的中国精英亲属网络与社会关系网络的度分布、同配性、地理跨度，用来检验我们生成的网络是否"像"一个东亚官僚社会 |
| **ORBIS** | 罗马世界多模态交通成本网络模型 + 完整参数文档 | 罗马帝国约 200 CE | https://orbis.stanford.edu/ ；参数文档 PDF：`https://orbis.stanford.edu/orbis2012/ORBIS_v1paper_20120501.pdf` | 未在本次读到明确许可声明 | **M3／M10 的速度参数来源**（已用，见 4.1）；也是"如何做一个成本表面模型"的方法论范本 |
| **ICON (Index of Complex Networks)** | 研究级网络数据索引 | 全学科 | Broido & Clauset 2019 引其为语料来源（文献 59） | 未验证 | 网络结构统计的对照基线 |
| **Journal of Historical Network Research (JHNR)** | 完全开放获取的历史网络研究期刊 | 从古代到近代 | https://jhnr.net/ | 文章页显示 **CC BY-SA 4.0** | 方法论与案例来源；本次已从中取得 Roller 2025 |
| **NetworkX 内置历史网络** | Florentine families（15 节点／20 边）、Karate club 等 | — | `networkx.florentine_families_graph()`；源码 `networkx/generators/social.py` | BSD | 单元测试与算法验证的现成基准 |
| **CHGIS（中国历史地理信息系统）** | 中国历代行政区划与聚落点的时空数据 | 公元前 221 – 1911 | 哈佛 Fairbank 中心 | 未验证 | **本次会话网络不可达，未能验证内容与许可。**若可用，将是东亚成本表面的地名／聚落骨架 |
| **Pleiades / Barrington Atlas** | 古代地名地理数据（ORBIS 的底图来源之一，原文提及 Talbert 2000 与 Pleiades） | 地中海世界 | — | 未验证 | 方法论参考 |

**本次会话网络可达性记录（对后续 Phase 有用）**：Crossref API、Europe PMC API、DOAJ API、GitHub API/raw、`orbis.stanford.edu`、`journals.plos.org`、`jhnr.net`、`d-place.org`、`openhumanitiesdata.metajnl.com`、`www.persee.fr`、`www.jstor.org`(首页)、`www.cs.cornell.edu` **可达**；`arxiv.org`、`*.wikipedia.org`、`*.wikisource.org`、`api.ctext.org`、`ctext.org`、`journals.openedition.org`、`chgis.fairbank.fas.harvard.edu`、`tuvalu.santafe.edu` **不可达**；`nature.com`、`science.org`、`journals.uchicago.edu`、`royalsocietypublishing.org`、`pnas.org`、`link.springer.com`、`cambridge.org`、`pmc.ncbi.nlm.nih.gov`(reCAPTCHA) **返回 403/重定向到登录**。OpenAlex 与 Semantic Scholar 搜索 API 均因匿名配额被限流。

---

## 6. 中国与东亚特定证据

### 6.1 东亚社会的亲属结构分布（我本次自己计算）

从 D-PLACE 的 Ethnographic Atlas 中，按经纬度 bbox（纬 20–56°N，经 97–147°E）取出 **39 个社会**：Ainu, Akha, Ami, Atayal, Bunun, Buryat, Cantonese, Chahar, Chekiang, Dagur, Evenk, Ishigakians, Japanese, Kachin, Khalka, Koreans, Lamet, Lolo, Man, Manchu, Miao, Min Chinese, Minchia, Miyakans, Muong, Nanai, Negidal, Nivkh, Okinawans, Oroch, Orok, Paiwan, Palaung, Puyuma, Shantung, Tao, Tu, Udihe, Ulch。

| 变量 | 东亚 (N=39) | 全球 (N=1291) | 差异含义 |
|---|---|---|---|
| 父系世系 EA043=1 | **69.2%** | 45.7% | 东亚显著更父系 |
| 双系 EA043=6 | 10.3% | 28.0% | 东亚双系罕见 |
| 母系 EA043=3 | 5.1% | 12.4% | |
| 从父居 EA012=8 | **61.5%** | 49.4% | |
| 从夫居 EA012=10 | 23.1% | 12.3% | **父方居住合计 ≈ 92%（vs 全球 ~71%）** |
| 允许交表婚 EA023=1 | 28.2% | 16.0% | 东亚交表婚传统更强 |
| 禁一二代表亲 EA023=7 | 17.9% | 21.8% | |
| 偏好母方交表 EA025=2 | **17.9%** | 3.4% | **东亚（尤其西南与东北族群）母方交表婚偏好突出** |
| 氏族社区 EA015=6 | 28.2% | 18.4% | |
| Demes EA015=1 | 17.9% | 6.4% | |
| 无上层司法层级 EA033=1 | 35.9% | 40.7% | |
| 四级司法层级 EA033=5 | **10.3%** | 3.4% | **东亚样本中有比例明显偏高的高度国家化社会**（Japanese, Koreans, Cantonese, Min Chinese, Shantung 等） |
| 土地父系诸子继承 EA074=7 | **48.7%** | 27.4% | **诸子均分（而非长子独占）是东亚常态** |

- **来源等级：A**（数据可下载、计算可复现）。
- **⚠️ 样本警告**：这 39 个社会中，"Cantonese／Chekiang／Min Chinese／Shantung／Japanese／Koreans"是把巨型国家社会当成一个"society"编码的，与 Nivkh、Orok 这类数百人的群体在同一张表里等权。**这个分布不能当作"东亚人口的加权分布"，只能当作"东亚存在的社会形态类型谱"。**
- **对本项目的用法**：这些数字给出的是"如果我们的模拟在东亚地理上跑，什么样的亲属—居住—继承组合是历史上确实出现过的"。它是**合理性区间**，不是目标。诸子均分继承 + 强父系 + 父方居住的组合，会机械地产生：土地在几代内碎片化 → 分家压力 → 向边际土地扩张或向城市／军队／科举外流 → 宗族作为跨家户的风险池出现。**这条因果链完全可以由 M2 的规则参数自动产生，不需要写"中国式家族"脚本。**

### 6.2 中国精英网络的现成研究基础设施

- **CBDB**：见第 4.7、第 5 节。**这是全世界最好的前现代精英社会网络数据集**（482,953 条亲属关系 + 160,219 条非亲属社会关系 + 275,945 条官职记录，跨 13 个世纪）。用途：(i) 校准我们生成的精英网络的度分布形状；(ii) 校准联姻的地理跨度与地位同配性；(iii) 检验"结构洞占据者是否更容易升迁"这类机制在真实东亚数据上是否成立。
- 亲属关系规范化的方法学：Li, B., Yuan, Y., Lu, X. & Bol, P. (2024) "Normalization of kinship relations to enrich family network analysis: case study on China biographical database", *Digital Scholarship in the Humanities* 39(1): 215–227, doi:10.1093/llc/fqad108 **[已验证：Crossref；正文未读]**。
- 宋代信息与网络的专著：De Weerdt, H. (2016) *Information, Territory, and Networks*, doi:10.1163/9781684175635 **[已验证：Crossref]**；另有 *Information, Territory, and Elite Networks* 的章节 DOI 系列（如 "The Multiplexity of Premodern Borders", pp. 233–278, doi:10.2307/j.ctv43vsm3.11）**[已验证：Crossref]**。**这是我所知最直接研究"前现代中国的信息如何在精英网络中流通、以及这如何维系帝国"的专著，强烈建议 Phase 1 取得原文。**
- 明清情报与文书控制：Wu, S. *Communication and Imperial Control in China: Evolution of the Palace Memorial System*（Harvard，1970；本次验证到章节 DOI 如 doi:10.4159/harvard.9780674434660.c6 "The Traditional Memorial System"、c8 "Factionalism and the Growth of the Palace Memorial System"、c9 "Changes in the Palace Memorial System in the Yung-cheng Reign"、c11 "Communication, Values, Control"）**[已验证：Crossref，正文未读]**。**这是"皇帝为了绕开官僚层级失真而发明密折"的经典案例——正是 M7 中 `filter_upward` 与其对抗手段的历史原型。**
- 古代邮驿：Li, B. (2020) "Capital Liaison Office and Ancient Postal System", 收入 *Sociology, Media and Journalism in China*, pp. 19–61, doi:10.1007/978-981-15-7808-3_2 **[已验证：Crossref；Springer 需登录，正文未读]**。

### 6.3 我明确没能验证的东亚参数（**不要编**）

- **中国历代驿传的站间距与日行里程**（如常被引用的"三十里一驿"、唐代驿站总数、宋代急脚递日行里数、清代马递 300/400/500/600 里的分级）：本次会话中 `ctext.org`、`zh.wikisource.org` 均不可达，Springer/Brill/Cambridge 均返回 403，**我没有取得任何一手或二手的可引用来源，因此本简报不给出任何具体里程数字**。见第 9 节。
- **Braudel 关于地中海消息速度的量化表**（*La Méditerranée* 中"新闻到达威尼斯的时间"及 Pierre Sardella 的数据）：本次未取得。**不要凭印象写"从马德里到威尼斯 22 天"这类数字。**
- **东亚季风对海路信息速度的季节性影响**：ORBIS 的地中海风况模型不可迁移。需要独立研究（属于 `east-asia-climate-environment` 简报的范围，本简报只标注这是一个必须补上的耦合点）。

### 6.4 东亚地理对信息边界的结构性含义（推论，D 级，见第 9 节）

我把它明确放在这里并标为推论：东亚的水系（黄河—淮河—长江东西向、大运河南北向）、山系（秦岭—淮河、太行、南岭、横断）与草原—农耕过渡带，会使成本表面呈现**强各向异性**——同样的欧氏距离，东西向沿江与南北向翻岭的信息成本可能差数倍。**这个判断是我从 ORBIS 的"上下行比 4:1"与一般地形常识推出的，不是从东亚的实证文献读到的，因此是 D 级。**Phase 1 必须用真实水文与地形数据把它变成 A/B 级。

---

## 7. 学界争议与未解决问题

1. **Dunbar 数是否存在**。Lindenfors et al. (2021) 的 95% CI 4–520 / 2–336 实质上否定了"从新皮层比例外推出一个特定数字"的做法。Dunbar 一方的回应本次未检索。**本项目立场：不使用固定上限，改用时间预算内生化（见 2.7）。**
2. **无标度网络的普遍性**。Broido & Clauset (2019) vs Holme (2019) 的公开分歧。**本项目立场：社会网络层不用 BA；制度层的重尾必须由制度规则生成，且生成后应实际做统计检验（用 Clauset 的方法）而不是目测。**
3. **简单传染 vs 复杂传染的适用边界**。Centola 的实验是在人工在线社区里做的，其外部效度（尤其对前现代面对面社会）未被独立验证。**本项目立场：采用二分，但把 θ 做成可调，并在校准时检验"宗教扩散速度是否落在历史合理区间"。**
4. **弱连接究竟传播什么**。Granovetter（弱连接带来新信息）与 Centola & Macy（长弱连接对复杂传染无用）在文献中常被误读为互相矛盾。真正的争议在于：**信息与影响是否应该用同一套动力学**。本项目选择分开，但这本身是一个可被后续研究推翻的建模决定。
5. **Ethnographic Atlas / SCCS 的可用性**。三重问题：(i) **Galton 问题**——社会之间不独立（共同祖先与借用），D-PLACE 论文摘要明确把"spatial and historical dependencies among cultural groups"列为它要解决的四大障碍之一；(ii) **编码质量**——EA 的编码来自二手民族志，很多条目的 NA 率极高（EA031 社区规模 NA 率 52.7%，EA074 NA 率 33.7%）；(iii) **时间错位**——"民族志现在时"多为 19–20 世纪，且许多社会已被殖民、市场与国家深度改造。
6. **口传的时间深度**。Vansina 一系认为口传可保存数世纪的可用信息；Henige 一系认为口传会被持续重构、其"年代"多为后设。**本项目立场：两者都建（结构化韵文低失真 + 散文高失真 + structural amnesia 主动删除），让模拟自己产生这两种口传传统。**
7. **历史网络数据的幸存偏差**。所有历史网络（Medici、宗教改革书信、CBDB）都只包含"留下了文书的人"。CBDB 的 491,000 人相对于宋代数千万人口是极小且极偏的样本。**这不只是数据问题，它对本项目还有一个正面用途：我们的模拟应当同时生成"世界事实网络"与"留存文献网络"，后者是前者的偏样本——于是模拟内的历史学家会犯与真实历史学家相同的错误。**
8. **信息的双向性**。绝大多数网络模型默认边是对称的。前现代信息流强烈不对称（中央知道边疆的名字，边疆不知道中央的人事）。**这一点在文献中讨论不足**，我们必须自己处理（M13）。
9. **平均场近似何时失效**。M14 的 L0 层用聚落间接触矩阵做平均场。在小社群、强阈值、强空间结构下，平均场会系统性错估级联概率。**没有现成的判据告诉我们何时必须升级粒度。**这是本项目需要自己做敏感性分析的地方。

---

## 8. 反模式：本领域常见的错误建模方式（我们必须避免的）

1. **用 Barabási–Albert 生成社会网络。** 经验上错（社会网络子集 0% 落在 Strong/Strongest 类），机制上也错（优先连接要求新节点全局可见所有度数，直接违反信息边界）。**后果**：会产生极少数超级枢纽，使全球信息瞬时同步，摧毁地方性与路径依赖。
2. **用单一 SIR 传播一切内容。** 后果：宗教像流感一样十年席卷大陆；制度在一个世纪内全球同质化；再也不会出现"隔壁郡三百年不知道有这种农具"的情形。**必须做简单／复杂传染二分。**
3. **把 Dunbar 150 当作硬编码上限。** 后果：一切组织在 150 人处出现人为断层；官僚制、市场、宗教这些"超越面对面记忆的技术"失去了存在理由（它们存在的意义恰恰是突破这个限制）。**正确做法是把突破 150 做成需要发明的技术。**
4. **给 LLM agent 的 prompt 里塞进世界真实状态"作为背景"。** 这是本项目最容易犯、也最致命的错误。哪怕只是"当前全国粮价均值"这样一个看似无害的字段，也会让 agent 获得任何前现代人都不可能有的统计视野。**工程对策**：渲染函数必须从 `Belief` 对象构造 prompt，而 `Event` 对象在类型系统层面对渲染函数不可见。
5. **让 LLM 决定"消息是否送到"或"消息内容变成什么"。** LLM 可以写出失真后的文本，但**哪些算子被施加、施加几次、置信度降多少，必须由带种子的规则计算**，否则失真不可重放、不可反事实。
6. **把失真建成零均值高斯噪声。** Bartlett 之后的整个文献都说失真是**有方向的**（向图式收敛、数字放大、归因个人化、道德化）。零均值噪声在多跳后会平均掉，什么也不产生；有方向的失真在多跳后会产生神话。**后者才是我们要的。**
7. **只用欧氏距离做衰减。** 会让长江天堑和平原大道等价。**必须用旅行时间成本表面。**
8. **静态网络。** 网络若不随死亡、迁徙、战争、制度变化而重连，路径依赖就只剩下属性层，网络层的历史被抹掉。
9. **把"官方史"做成一个独立的随机文本生成器。** 那样它与真实事实之间就没有可追溯的关系，第 9 条纲领（世界事实与历史叙事分离）就退化成"两个不相干的数据库"。**官方史必须是从真实事实经过可审计的删除／归因/重排算子得到的。**
10. **直接把 Ethnographic Atlas 的现代民族志分布当作史前参数。** Galton 问题 + 时间错位 + 极高 NA 率。**它只能当先验形状，且做统计时应优先用 SCCS 子样本。**
11. **假设信息流对称。** 见第 7 节第 8 点。
12. **只建人际网络，不建组织节点与文本节点。** 前现代信息的三个最重要载体是人、官僚机构、文本，三者的延迟／失真／持久性特征完全不同。只建人际网会让"档案""经典""律令"这些东西无处安放，进而使"复古改制""考据""伪书"永不可能出现。
13. **在静态聚合图上算中心性，然后声称那是信息控制力。** Roller (2025) 的时间尊重路径分析表明这会系统性高估。**因果链查询必须在时序图上做。**
14. **让每个 agent 每 tick 都与所有邻居交换所有信念。** 计算上 O(N·k·|B|) 爆炸，行为上也不真实（人不会每天把三十年前听过的每件事复述一遍）。**必须有接触采样 + stifle 机制 + 遗忘。**
15. **把"没人知道某事"当成 bug 修掉。** Daley–Kendall 的结构性结论是：即使传播时间无限，仍有非零比例的人永不知情。**这是特性，不是缺陷。**

---

## 9. 无源判断（D 级，明确标记为 LLM 常识，不得当作历史规律）

以下全部是我为了让模拟能跑而提出的假设或推论，**本次检索中没有找到直接来源**。它们必须以可调参数的形式实现，并在校准阶段接受检验。

**D-1 失真算子的概率参数。** 文献未提供可用的"每跳失真率"。我建议的起始值（纯属工程占位）：口传散文 `p_ABSTRACT ≈ 0.3/跳`、`p_ROUND ≈ 0.4/跳（含数字时）`、`p_INFLATE` 使数字每跳期望 ×1.15、`p_MERGE_ACTORS ≈ 0.05/跳（hops>3 时上升）`、`p_ATTRIBUTE_AGENCY ≈ 0.2/跳（低识字社会）`；格律化文本各项乘以 0.2；文字抄本 `p_scribal ≈ 0.005/字` 量级。**这些数字没有来源。**

**D-2 信道信任系数与置信衰减形式。** `confidence *= γ^hops` 的指数形式，以及 γ_OBSERVED > γ_OFFICIAL > γ_KIN > γ_MARKET > γ_RUMOR 的序，是我的常识判断。

**D-3 交往记忆约 80–100 年（三到四代）。** 这个数字与 Assmann 的框架关联，但我本次未从原文确认，故降为 D 级占位。

**D-4 Vansina 的 "floating gap" 结构。** 概念本身我有把握，具体形态与时间深度未验证。

**D-5 Dunbar 层级 5–15–50–150–500–1500（比值≈3）。** Zhou et al. 2005 的标题与摘要已验证，但这组具体数值本次未读到原文。

**D-6 Watts 2002 级联窗口的具体边界（常引为平均度 1 < z < 8，阈值 φ=0.18）。**

**D-7 Daley–Kendall 模型的 0.203 永不知情比例。**

**D-8 Liben-Nowell 等的 "P(friendship) ∝ 1/rank" 具体形式。** 只读到摘要。

**D-9 Onnela 2007 的"按弱到强删边导致相变式碎裂"的具体阈值。** 只读到摘要。

**D-10 中国驿传的一切具体里程数字。** 本次完全未能验证，**本简报刻意不给出任何数字**。

**D-11 Braudel 的地中海消息速度表。** 未验证。

**D-12 东亚成本表面的各向异性推论（6.4 节）。** 我的推理，非文献结论。

**D-13 三层粒度架构（M14）与升降级阈值。** 纯工程设计。

**D-14 `political_utility` 的函数形式与"广为人知的事实不可否认"这一约束的强度参数。** 直觉上正确（Hobsbawm & Ranger 与 Goody & Watt 支持方向），但没有任何量化来源。

**D-15 组织信息集的 `filter_upward` 三算子（聚合／选择／延迟）及其参数。** 结构受 Wu (1970) 的密折研究启发，但我未读原文，参数纯属设定。

**D-16 "觅食阶段社会宇宙 ≈ 1000 人"外推到农业与城市阶段的方式。** Hill et al. 2014 的 1000 是觅食者的实测，把它随人口密度与识字率外推是我的假设。

**D-17 `L_coresidence` 层用 Agta 的 0.6–0.85 / 0.28–0.56 作为通用营地内外接触概率。** Agta 数据是 A 级的，但"其他文化、其他生态、其他时代也适用"是 D 级外推。

**D-18 belief store 的压缩策略与存储量级估算。** 未做实测。

---

## 10. 参考文献

**标记说明**：**[V]** = 本次会话中通过 Crossref / Europe PMC / 开放网页实际读到元数据或全文；**[V-full]** = 本次读到全文并从中直接引用了数字；**[R]** = 凭记忆列出，本次未验证，**不得作为参数来源**。

### 网络理论与模型
1. **[V]** Watts, D. J. & Strogatz, S. H. (1998). Collective dynamics of 'small-world' networks. *Nature* 393(6684), 440–442. doi:10.1038/30918
2. **[V]** Barabási, A.-L. & Albert, R. (1999). Emergence of Scaling in Random Networks. *Science* 286(5439), 509–512. doi:10.1126/science.286.5439.509
3. **[已核验]** **[V-full]** Broido, A. D. & Clauset, A. (2019). Scale-free networks are rare. *Nature Communications* 10, 1017. doi:10.1038/s41467-019-08746-5
4. **[V]** Holme, P. (2019). Rare and everywhere: Perspectives on scale-free networks. *Nature Communications* 10. doi:10.1038/s41467-019-09038-8
5. **[V]** Travers, J. & Milgram, S. (1969). An Experimental Study of the Small World Problem. *Sociometry* 32(4), 425. doi:10.2307/2786545
6. **[V]** Feld, S. L. (1991). Why Your Friends Have More Friends Than You Do. *American Journal of Sociology* 96(6), 1464–1477. doi:10.1086/229693
7. **[V]** Liben-Nowell, D., Novak, J., Kumar, R., Raghavan, P. & Tomkins, A. (2005). Geographic routing in social networks. *PNAS* 102, 11623–11628. doi:10.1073/pnas.0503018102（仅读摘要）
8. **[V]** Lambiotte, R., Blondel, V. D., de Kerchove, C., Huens, E., Prieur, C. 等 (2008). Geographical dispersal of mobile communication networks. *Physica A* 387(21), 5317–5325. doi:10.1016/j.physa.2008.05.014（仅元数据）
9. **[已修正: Barthélemy, M. (2011). Spatial networks. *Physics Reports* 499(1–3), 1–101. doi:10.1016/j.physrep.2010.11.002]** 原条目称"未验证 2011 综述"，本次核验已在 Crossref 确认该综述存在，卷页与 DOI 如上。可作为 M3 方法论总纲引用。

### 社会网络理论
10. **[V]** Granovetter, M. S. (1973). The Strength of Weak Ties. *American Journal of Sociology* 78(6), 1360–1380. doi:10.1086/225469
11. **[V]** Granovetter, M. (1983). The Strength of Weak Ties: A Network Theory Revisited. *Sociological Theory* 1, 201. doi:10.2307/202051
12. **[V]** Onnela, J.-P., Saramäki, J., Hyvönen, J., Szabó, G., Lazer, D., Kaski, K., Kertész, J. & Barabási, A.-L. (2007). Structure and tie strengths in mobile communication networks. *PNAS* 104(18), 7332–7336. doi:10.1073/pnas.0610245104（仅摘要）
13. **[V]** Burt, R. S. (2004). Structural Holes and Good Ideas. *American Journal of Sociology* 110(2), 349–399. doi:10.1086/421787
14. **[V]** Burt, R. S. *Structural Holes: The Social Structure of Competition*（1992；本次仅验证到再版章节 doi:10.1515/9780691229270-013、doi:10.2307/j.ctv1f886rp.15）
15. **[V]** McPherson, M., Smith-Lovin, L. & Cook, J. M. (2001). Birds of a Feather: Homophily in Social Networks. *Annual Review of Sociology* 27(1), 415–444. doi:10.1146/annurev.soc.27.1.415
16. **[V]** Kossinets, G. & Watts, D. J. (2009). Origins of Homophily in an Evolving Social Network. *American Journal of Sociology* 115(2), 405–450. doi:10.1086/599247
17. **[V]** Kossinets, G. & Watts, D. J. (2006). Empirical Analysis of an Evolving Social Network. *Science* 311(5757), 88–90. doi:10.1126/science.1116869

### Dunbar 数与社会规模
18. **[V]** Dunbar, R. I. M. (1992). Neocortex size as a constraint on group size in primates. *Journal of Human Evolution* 22(6), 469–493. doi:10.1016/0047-2484(92)90081-j
19. **[V]** Dunbar, R. I. M. (1995). Neocortex size and group size in primates: a test of the hypothesis. *Journal of Human Evolution* 28(3), 287–296. doi:10.1006/jhev.1995.1021
20. **[V]** Kudo, H. & Dunbar, R. I. M. (2001). Neocortex size and social network size in primates. *Animal Behaviour* 62(4), 711–722. doi:10.1006/anbe.2001.1808
21. **[V]** Zhou, W.-X., Sornette, D., Hill, R. A. & Dunbar, R. I. M. (2005). Discrete hierarchical organization of social group sizes. *Proc. R. Soc. B* 272(1561), 439–444. doi:10.1098/rspb.2004.2970（仅摘要；层级数值未验证）
22. **[已核验]** **[V]** Lindenfors, P., Wartel, A. & Lind, J. (2021). 'Dunbar's number' deconstructed. *Biology Letters* 17(5). doi:10.1098/rsbl.2021.0158（摘要含全部置信区间数字）

### 传播、级联与阈值
23. **[V]** Granovetter, M. (1978). Threshold Models of Collective Behavior. *American Journal of Sociology* 83(6), 1420–1443. doi:10.1086/226707
24. **[V]** Macy, M. & Evtushenko, A. (2020). Threshold Models of Collective Behavior II. *Sociological Science* 7, 628–648. doi:10.15195/v7.a26
25. **[V]** Watts, D. J. (2002). A simple model of global cascades on random networks. *PNAS* 99(9), 5766–5771. doi:10.1073/pnas.082090499
26. **[已核验]** **[V]** Centola, D. & Macy, M. (2007). Complex Contagions and the Weakness of Long Ties. *American Journal of Sociology* 113(3), 702–734. doi:10.1086/521848
27. **[V]** Centola, D. (2010). The Spread of Behavior in an Online Social Network Experiment. *Science* 329(5996), 1194–1197. doi:10.1126/science.1185231
28. **[已核验]** **[V-full]** Singh, P., Sreenivasan, S., Szymanski, B. K. & Korniss, G. (2013). Threshold-limited spreading in social networks with multiple initiators. *Scientific Reports* 3, 2330. doi:10.1038/srep02330
29. **[已核验]** **[V]** Daley, D. J. & Kendall, D. G. (1964). Epidemics and Rumours. *Nature* 204(4963), 1118. doi:10.1038/2041118a0
30. **[V]** Pittel, B. (1990). On a Daley-Kendall model of random rumours. *Journal of Applied Probability* 27(1), 14–27. doi:10.1017/s0021900200038390
31. **[V]** Gani, J. (2000). The Maki–Thompson rumour model: a detailed analysis. *Environmental Modelling & Software* 15(8), 721–725. doi:10.1016/s1364-8152(00)00029-3
32. **[V]** Agliari, E., Pachon, A., Rodriguez, P. & Tavani, F. (2017). Phase Transition for the Maki–Thompson Rumour Model on a Small-World Network. *J. Stat. Phys.* 169(4), 846–875. doi:10.1007/s10955-017-1892-x
33. **[V-full]** Lengyel, B., Bokányi, E., Di Clemente, R., Kertész, J. & González, M. C. (2020). The role of geography in the complex diffusion of innovations. *Scientific Reports* 10, 15065. doi:10.1038/s41598-020-72137-w
34. **[V]** Axelrod, R. (1997). The Dissemination of Culture. *Journal of Conflict Resolution* 41(2), 203–226. doi:10.1177/0022002797041002001
35. **[V]** Bass, F. M. (2004[1969]). A New Product Growth for Model Consumer Durables. *Management Science* 50(12 suppl.), 1825–1832. doi:10.1287/mnsc.1040.0264
36. **[V]** Hägerstrand, T. *Innovation Diffusion as a Spatial Process*（1967；本次仅验证到 1969 年两篇书评：*Social Forces* 47(3), 356, doi:10.2307/2575048；*Geographical Review* 59(2), 309, doi:10.2307/213473）

### 历史社会网络分析
37. **[已核验]** **[V]** Padgett, J. F. & Ansell, C. K. (1993). Robust Action and the Rise of the Medici, 1400–1434. *American Journal of Sociology* 98(6), 1259–1319. doi:10.1086/230190
38. **[已核验]** Roller, R. (2025). Time-Respecting Paths in Letter Networks Reveal Opportunities for Influencing Information Transmission during the European Reformation. *Journal of Historical Network Research* 12(1), 133–165. doi:10.25517/jhnr.v12i1.83（该 DOI 不在 Crossref，本次经 doi.org 跳转至 jhnr.net 文章页确认；补上页码）
39. **[V]** Hillner, J. & MacCarron, M. (2025). Social Network Analysis. 收入 *Brill's Companion to Roman Prosopography*, 151–181. doi:10.1163/9789004748613_011
40. **[V]** Brughmans, T. & Peeples, M. A. (2023). *Network Science in Archaeology*. Cambridge University Press. doi:10.1017/9781009170659
41. **[V]** Erikson, E. & Feltham, E. (2020). Historical Network Research. 收入 *The Oxford Handbook of Social Networks*, 431–442. doi:10.1093/oxfordhb/9780190251765.013.40
42. **[V]** Tambs, L. (2026). Unnamed Actors and Groups in Select Papyri from the Zenon Archive (3rd cent. BCE). *JHNR* 13(1). doi:10.25517/jhnr.v13i1.117
43. **[R]** Breiger, R. L. & Pattison, P. E. (1986). Cumulated social roles: The duality of persons and their algebras. *Social Networks* 8(3), 215–256.（NetworkX 源码中标注的 Florentine 数据来源，我读到的是 NetworkX 源码的引用，**未直接验证该文献本身**）

### 亲属结构与跨文化数据
44. **[已核验]** White, D. R. (1997). Structural endogamy and the network. *Mathématiques et sciences humaines* 137. doi:10.4000/msh.2742
45. **[V]** Schweizer, T. & White, D. R. (1998). Revitalizing the Study of Kinship and Exchange with Network Approaches. 收入 *Kinship, Networks, and Exchange*, 1–10. doi:10.1017/cbo9780511896620.002
46. **[已核验]** **[V-full]** Kirby, K. R., Gray, R. D., Greenhill, S. J., Jordan, F. M., Gomes-Ng, S. 等 (2016). D-PLACE: A Global Database of Cultural, Linguistic and Environmental Diversity. *PLOS ONE* 11(7), e0158391. doi:10.1371/journal.pone.0158391
47. **[V]** Murdock, G. P., Textor, R., Barry, H. III, White, D. R., Gray, J. P. & Divale, W. T. (1999). Ethnographic Atlas. *World Cultures* 10, 24–136.（经 D-PLACE `datasets/index.csv` 验证该引用条目）
48. **[V]** Murdock, G. P. & White, D. R. (1969). Standard Cross-Cultural Sample. *Ethnology* 9, 329–369.（同上）
49. **[V]** Binford, L. (2001). *Constructing Frames of Reference*. University of California Press.（同上）
50. **[V]** Jorgensen, J. G. (1980). *Western Indians*. W. H. Freeman.（同上）

### 觅食者社会与人口下界
51. **[V]** Hill, K. R., Walker, R. S., Božičević, M., Eder, J., Headland, T. 等 (2011). Co-Residence Patterns in Hunter-Gatherer Societies Show Unique Human Social Structure. *Science* 331(6022), 1286–1289. doi:10.1126/science.1199071
52. **[已核验]** **[V-full]** Hill, K. R., Wood, B. M., Baggio, J., Hurtado, A. M. & Boyd, R. T. (2014). Hunter-gatherer inter-band interaction rates: implications for cumulative culture. *PLOS ONE* 9, e102806. doi:10.1371/journal.pone.0102806
53. **[已核验]** **[V-full]** Migliano, A. B., Battiston, F., Viguier, S., Page, A. E., Dyble, M., Schlaepfer, R., Smith, D., Astete, L., Ngales, M., Gomez-Gardenes, J., Latora, V. & Vinicius, L. (2020). Hunter-gatherer multilevel sociality accelerates cumulative cultural evolution. *Science Advances* 6, eaax5913. doi:10.1126/sciadv.aax5913
54. **[V]** Apicella, C. L., Marlowe, F. W., Fowler, J. H. & Christakis, N. A. (2012). Social networks and cooperation in hunter-gatherers. *Nature* 481(7382), 497–501. doi:10.1038/nature10736
55. **[V]** Dyble, M., Salali, G. D., Chaudhary, N., Page, A., Smith, D., Thompson, J., Vinicius, L., Mace, R. & Migliano, A. B. (2015). Sex equality can explain the unique social structure of hunter-gatherer bands. *Science* 348, 796–798. doi:10.1126/science.aaa5139
56. **[V]** Migliano, A. B. 等 (2016). High-resolution maps of hunter-gatherer social networks reveal human adaptation for cultural exchange. bioRxiv. doi:10.1101/040154
57. **[已核验]** **[V-full]** White, A. A. (2017). A Model-Based Analysis of the Minimum Size of Demographically-Viable Hunter-Gatherer Populations. *JASSS* 20(4). doi:10.18564/jasss.3393
58. **[已修正: Wobst, H. M. (1974). Boundary Conditions for Paleolithic Social Systems: A Simulation Approach. *American Antiquity* 39(2), 147–178. doi:10.2307/279579]** 原条目称 Crossref 中检索不到；本次核验直接在 Crossref 命中，卷期页与 DOI 如上。175–475 仍属二手转引，取用前应读原文。

### 记忆、口传与历史叙事
59. **[V]** Bartlett, F. C. *Remembering: A Study in Experimental and Social Psychology*（1932；1995 剑桥再版 doi:10.1017/cbo9780511759185；1933 *BJEP* 3(2), 187–192, doi:10.1111/j.2044-8279.1933.tb02913.x）
60. **[已核验]** **[V]** Rubin, D. C. (1995). *Memory in Oral Traditions: The Cognitive Psychology of Epic, Ballads, and Counting-out Rhymes*. Oxford University Press. doi:10.1093/oso/9780195082111.001.0001
61. **[已修正: Dickinson, D. L. & Drummond, S. P. A. (2025). The impact of insufficient sleep on the serial reproduction of information. *Sleep Advances* 6(2). doi:10.1093/sleepadvances/zpaf026]** 文献真实存在，原条目缺卷期（Crossref: vol 6, issue 2, 2025-04）。
62. **[V]** Kashima, Y. & Yeung, V. W. L. (2010). Serial Reproduction: An Experimental Simulation of Cultural Dynamics. *Acta Psychologica Sinica* 42(1), 56–71. doi:10.3724/sp.j.1041.2010.00056
63. **[V]** Mesoudi, A. & Whiten, A. (2008). The multiple roles of cultural transmission experiments in understanding human cultural evolution. *Phil. Trans. R. Soc. B*, 3489–3501. doi:10.1098/rstb.2008.0129（仅摘要）
64. **[V]** Vansina, J. (1985). *Oral Tradition as History*. doi:10.2307/jj.36106057（正文未读；floating gap 未验证）
65. **[已核验]** **[V]** Goody, J. & Watt, I. (1963). The Consequences of Literacy. *Comparative Studies in Society and History* 5(3), 304–345. doi:10.1017/s0010417500001730
66. **[V]** Assmann, J. & Czaplicka, J. (1995). Collective Memory and Cultural Identity. *New German Critique* 65, 125. doi:10.2307/488538
67. **[V]** Hobsbawm, E. & Ranger, T. (eds.). *The Invention of Tradition*（1983；2012 剑桥版 doi:10.1017/cbo9781107295636）
68. **[R]** Henige, D. *The Chronology of Oral Tradition*.（本次未检索到）
69. **[R]** Halbwachs, M. *Les cadres sociaux de la mémoire*.（本次未检索）

### 前现代交通、通信与东亚
70. **[已核验]**（本次重新下载 PDF，56 页，标题页作者与题名一致）**[V-full]** Scheidel, W., Meeks, E. & Weiland, J. (2012). *ORBIS: The Stanford Geospatial Network Model of the Roman World, Version 1.0*. Stanford University. https://orbis.stanford.edu/orbis2012/ORBIS_v1paper_20120501.pdf
71. **[V]** Duncan-Jones, R. (1990). Communication-speed and contact by sea in the Roman empire. 收入 *Structure and Scale in the Roman Economy*, 7–29. doi:10.1017/cbo9780511552649.003（正文未读；ORBIS 全文多处引用其 1982 年著作）
72. **[已核验]** **[V]** Knappett, C., Evans, T. & Rivers, R. (2008). Modelling maritime interaction in the Aegean Bronze Age. *Antiquity* 82(318), 1009–1024. doi:10.1017/s0003598x0009774x
73. **[V]** Rihll, T. & Wilson, A. Modelling settlement structures in Ancient Greece. 收入 *City and Country in the Ancient World*, 59–96. doi:10.4324/9780203418703_chapter_3（年份字段缺失）
74. **[已核验]** Chen, S. & Wang, H. (2022). China Biographical Database (CBDB): A Relational Database for Prosopographical Research of Pre-Modern China. *Journal of Open Humanities Data* 8, art. 4. doi:10.5334/johd.68
75. **[V]** Li, B., Yuan, Y., Lu, X. & Bol, P. (2024). Normalization of kinship relations to enrich family network analysis: case study on China biographical database. *Digital Scholarship in the Humanities* 39(1), 215–227. doi:10.1093/llc/fqad108
76. **[已核验]** De Weerdt, H. (2016). *Information, Territory, and Networks*. Harvard University Asia Center. doi:10.1163/9781684175635；相关章节如 The Multiplexity of Premodern Borders, 233–278, doi:10.2307/j.ctv43vsm3.11
77. **[已核验]**（章节 DOI 经 Crossref 解析：c11 = "IX. Communication, Values, Control", pp. 107–124, Harvard University Press, 1970）**[V]** Wu, S. *Communication and Imperial Control in China: Evolution of the Palace Memorial System, 1693–1735*（Harvard, 1970；章节 DOI: c6 doi:10.4159/harvard.9780674434660.c6；c8 …c8；c9 …c9；c11 …c11）
78. **[V]** Li, B. (2020). Capital Liaison Office and Ancient Postal System. 收入 *Sociology, Media and Journalism in China*, 19–61. doi:10.1007/978-981-15-7808-3_2（正文未读）
79. **[已核验（仅存在性）]** Braudel, F. *La Méditerranée et le Monde méditerranéen à l'époque de Philippe II*（Armand Colin, 1949；2ᵉ éd. 1966）；Sardella, P. *Nouvelles et spéculations à Venise au début du XVIe siècle*（Cahiers des Annales, 1948）。本次经 Persée 上多篇论文的引用确认两书确实存在，但**均未取得原文**，故其消息速度数据仍不得引用。

### 模拟方法学
80. **[V]** Epstein, J. M. & Axtell, R. (1996). *Growing Artificial Societies: Social Science from the Bottom Up*. MIT Press. doi:10.7551/mitpress/3374.001.0001

### 未获得来源的引证需求
81. **[未找到]** 中国历代驿传制度的站间距与日行里程（"三十里一驿"、唐驿站总数、宋急脚递、清马递 300/400/500/600 里分级等）——本次核验仍未取得任何一手或二手可引用文献：无作者、无题名、无发表处，ctext.org / zh.wikisource.org 不可达，Springer/Brill/Cambridge 返回 403。**M10 的东亚里程参数目前无任何文献支撑，不得写入任何具体数字。**

---

## 附：给 Phase 1 的四项具体待办

1. **建东亚成本表面**。ORBIS 的速度参数可迁移（生理与技术上限相通），水文与季风必须重做。需要 CHGIS 或等价的历史地名／水系数据（本次不可达）。
2. **取 CBDB 原始数据并计算基线统计量**：精英亲属网络的度分布、地位同配性、联姻地理跨度的分布、社会关系网络的社群结构。**这是我们唯一能拿到的、真正东亚的、前现代的大规模网络基线。**
3. **核验第 9 节的 D-3 至 D-11**：这些是我知道但本次未能验证的具体数字，每一条都可能被写进内核参数，因此必须在写代码前核实原文。特别是中国驿传的里程数据——需要能访问中文古籍数据库或 Springer/Brill。
4. **设计失真算子的校准实验**：由于文献不提供每跳失真率，唯一可行的校准是**行为级的**——跑 300 模拟年，检查"关于同一事件，模拟中的民间传说与真实事实的偏离度"是否落在人类历史的合理区间（例如：三代之内数字夸大 2–10 倍、人物合并偶发、归因个人化普遍）。这需要与 `cultural-evolution` 简报协同。
