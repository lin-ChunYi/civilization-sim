# 技术创新、组合演化与扩散
**slug:** `technology-innovation-diffusion`
**一句话范围：** 用「能力/配方图 + 组合搜索 + 载体化知识 + 双层扩散」替代固定科技树，使发明、改良、失传、传播都成为由人口、组织、材料、地理与偶然共同决定的**可追溯随机过程**。

> 检索说明：本次会话开始时 WebSearch 配额已耗尽（200/200），因此全部检索通过 **Crossref REST API、Semantic Scholar Graph API、Europe PMC、Unpaywall、OpenAlex（限流）以及对开放获取全文/PDF 的直接抓取**完成。凡标注「已核验」的文献，其题名/作者/年份/期刊/DOI 均由 Crossref 或 Semantic Scholar 实际返回；凡标注「已读全文」的，其数值由我在本次检索中实际读到的正文或 PDF 抽取。付费墙拦截的文献见 §10 末尾。

---

## 1. 本简报要回答的问题

1. 如果不用科技树，技术在世界状态里到底是什么数据结构？
2. 「发明」这个事件应该由什么概率过程产生？它的强度应该由哪些状态变量驱动？
3. 一项技术怎样才可能**变好**（learning curve），这个变好速度由什么决定？
4. 一项技术怎样才可能**失传**？失传需要哪些前置条件才不显得无缘无故？
5. 技术在空间上怎么传播？速度量级是多少？什么东西挡住它？
6. 哪些部分必须由数学规则算，哪些可以交给 LLM agent，哪些绝对不能交给 LLM？
7. 中国与东亚有哪些特有的、可用于校准的经验证据？
8. 本领域最常见的建模错误是什么？

---

## 2. 已有成熟模型与理论

### 2.1 Arthur：技术作为组合递归（The Nature of Technology）
- **核心机制**：技术由既有技术组合而成；每个组件本身又是技术（递归）；技术的功能来自对自然现象（phenomena）的捕获与编排。新技术的出现同时**扩大了下一轮组合的原料池**。
- **形式化程度**：书本身是定性理论。可计算的形式化在 Arthur & Polak (2006, *Complexity* 11:23–31, DOI 10.1002/cplx.20130，**元数据已核验**；正文付费墙，未读) 的计算机模型中给出。
- **状态变量**：可用元件集合 `T`、需求列表 `G`、每个技术的成本/性能。
- **适用范围**：任何"人造物由人造物构成"的领域。
- **已知局限**：纯组合动力学在数学上**必然爆炸或灭绝**（见 §2.4、§2.5），必须由外生约束封顶。
- **出处**：Arthur & Polak 2006（元数据已核验）；Arthur 2009 *The Nature of Technology*（书；本次仅核验到两篇书评：Bueno 2010 DOI 10.20396/rbi.v8i2.8648990；Ozman 2012 DOI 10.1007/s10710-012-9158-5）。

### 2.2 Mokyr：propositional (Ω) / prescriptive (λ) 知识与 epistemic base
- **核心机制**：社会的"有用知识"分为**命题知识 Ω**（关于自然如何运作的信念集合）与**处方知识 λ**（配方、技术、做法）。每条技术 λ_i 都挂在 Ω 的一个子集上，这个子集就是它的 **epistemic base**。base 越窄，技术越只能靠试错微调、越难跨语境迁移、越容易失传；base 越宽，技术可被推广、可被有目的地改良。
- **形式化程度**：定性理论，但**极易形式化**（把 Ω 与 λ 做成两张互相引用的图）。
- **出处**：Mokyr, *The Gifts of Athena: Historical Origins of the Knowledge Economy*，DOI 10.1515/9781400829439（**元数据与全书章节目录已核验**：Ch.1 "Technology and the Problem of Human Knowledge" pp.1–27；Ch.2 "The Industrial Enlightenment" pp.28–77；Ch.3 pp.78–118；Ch.4 "Technology and the Factory System" pp.119–162；Ch.5 pp.163–217；Ch.6 "The Political Economy of Knowledge: Innovation and Resistance in Economic History" pp.218–283；Ch.7 pp.284–298）。
- ⚠️ **Ω/λ 与 "epistemic base" 这两个术语本身，我本次未能读到原文定义**（De Gruyter 返回 405）。术语标记为 `recalled_not_verified`，机制思想标记为 B 级。

### 2.3 Kremer 1993：人口→技术→人口 正反馈
- **核心机制**：技术进步率正比于人口规模（更多人 = 更多潜在发明者），而技术又抬高承载力从而抬高人口 → 超指数增长；并预测**孤立区域的技术水平随其面积/人口排序**（旧大陆 > 美洲 > 澳洲 > 塔斯马尼亚）。
- **形式化程度**：完全形式化（可解 ODE）。
- **出处**：Kremer, M. (1993) "Population Growth and Technological Change: One Million B.C. to 1990", *The Quarterly Journal of Economics*, DOI 10.2307/2118405（**元数据已核验**）。
- **已知局限**：把"人口"当成同质发明池，忽略网络结构、专业分工与知识载体；对我们最有害的一点是它会让模拟产生**单调加速**，没有停滞与倒退。

### 2.4 组合创新的爆炸性：TAP / CF 模型（Kauffman 系）
**已读全文**（arXiv:1904.03290，即 Steel, Hordijk & Kauffman 2020 *J. Theor. Biol.* 491:110187，DOI 10.1016/j.jtbi.2020.110187，元数据已核验）：

确定性 TAP 方程（论文明确注明取自 Koppl et al.）：

```
M_{t+1} = M_t + Σ_{i=1..M_t} α_i · C(M_t, i)
```
`M_t` = 物品/技术总数，`α_i` 递减且 `< 1`，表示"从 i 个已有物品中找出一个有用组合"的难度随 i 上升。

随机版 **Combinatorial Formation (CF) 模型**（连续时间马尔可夫）：
- 每个非空子集 `S` 在 `δ` 内以概率 `α_{|S|}·δ + o(δ)` 产生一个新物品；
- 每个物品在 `δ` 内以概率 `μ·δ + o(δ)` 消失（灭绝/淘汰）。
- 出生率 `λ_n = Σ_{i=1..n} α_i C(n,i)`；`γ_n = μn / (λ_n + μn)` 为"下一个事件是死亡"的概率。
- 几何特例 `α_i = P·α^i`，令 `x = 1+α`，则 **`λ_n = P·(x^n − 1)`**。
- 纯出生（μ=0）时爆炸时刻 `T` 有有限均值方差：`E[T] = Σ_{n≥M0} λ_n^{-1}`，`Var[T] = Σ_{n≥M0} λ_n^{-2}`。

**定理 2（对我们最重要）**：一般 CF 模型中，`M_t` **以概率 1 要么在有限时间内爆炸、要么灭绝**，且到达其中之一的期望时间有限。

> 工程含义：**任何"技术 = 已有技术的自由组合"的内核，如果不加外生约束，都不会有一个几千年的平稳中间态。**这正是我们要的"文明可以停滞数千年"的反面。必须加约束（见 §3.4）。

### 2.5 组合创新的有限时间奇点与"老化"补救（Solé, Amor & Valverde 2016）
**已读全文**（*PLOS ONE* 11:e0146180，DOI 10.1371/journal.pone.0146180，元数据+正文已核验）：
- 增长方程 `dN/dt ∝ μ N^{... }`，解为 `N(t) = [N_0^{1−z} − μ(1−z)(t−t_0)]^{1/(1−z)}`，`0 ≤ z ≤ 1` 衡量偏离线性的程度。
- `z = 1`（纯两两组合）时 `N(t) = N_0 / (1 − μ N_0 (t−t_0))`，**有限时间奇点** `t_s = 1/(μN_0) + t_0`。
- k 阶重组 + 幂律"老化核" `g(τ) = τ^{−γ}`：`k > 1 + γ` 时仍出现奇点（即使 γ=0，只要 k>1 就爆）。
- **指数老化核 `e^{−γN}` 时不再有奇点**，而是出现一个不断扩大的"旧创新黑洞"，长期动力学变成线性。

> 工程含义：**"淘汰/遗忘"的函数形式决定了整个文明的技术增长曲线形状**，比"发明率"本身更关键。幂律遗忘 → 爆炸；指数遗忘 → 线性。这是一个可以直接调的旋钮。

### 2.6 Fink & Reeves：组件基数 → 可造产品空间（守恒律）
**已读全文**（Fink & Reeves 2019, *Science Advances* 5, DOI 10.1126/sciadv.aat6107；及 Fink, Reeves, Palma & Farr 2017, *Nat. Commun.* 8, DOI 10.1038/s41467-017-02042-w。均元数据+正文已核验）：
- 产品由组件构成，产品的**复杂度 c = 它包含的不同组件数**。
- 守恒律：`p̄(n,c) / C(n,c)` 在创新过程各阶段恒定 ⇒ 当 `n, n′ ≫ c`：**`p̄(n′,c) ≃ p̄(n,c) · (n′/n)^c`**（`(n′/n)^c` 称为"复杂度折扣"）。
- 预测式：`p(n′) ≃ p(n,1)x + p(n,2)x² + p(n,3)x³ + …`，`x = n′/n`。
- **复杂度分布决定创新速率**（同样均值 `c̄ = 8` 时）：
  - 常数复杂度 → `p̄(n′) ≃ p(n)·x^{c̄}`
  - 二项分布 → `p̄(n′) ≃ p(n)·(1+x²)^{2c̄}`
  - 泊松分布 → `p̄(n′) ≃ p(n)·e^{(x−1)c̄}`
  - "Poisson complexity yields much faster innovation than binomial, which in turn yields much faster than constant."
- 实证检验（用三分之二组件预测其余）误差：语言 2.8%、烹饪 2.7%、混合饮料 1.4%、技术 0.4%。

> 工程含义：我们可以**不枚举技术**，只维护「组件集 n」+「配方复杂度分布」，就能算出"当前文明的可造物空间有多大"，从而把发明率与可探索空间挂钩。这是一个 O(1) 的量，不需要遍历组合。

### 2.7 专利组合网络的实证规律（Youn, Strumsky, Bettencourt & Lobo 2015）
**已读全文**（*J. R. Soc. Interface* 12:20150272，DOI 10.1098/rsif.2015.0272，PMC4424706）：
- USPTO 技术代码约 **161,000 个**，归入 **474 个技术类**。
- 1790–2010 年间 **77% 的专利用到至少两个代码**；19 世纪近一半是单代码专利，到 2010 年只剩约 **12%**。
- **exploration（新组合）与 exploitation（重复既有组合）的比例在近 200 年间不变**：`C(t) = αP`，`α ≈ 0.6`（即约 60% 是新组合、40% 是重复）。
- 代码与代码组合的使用频次都服从重尾分布，`~ x^{−2.4}`，与随机搜索不符，提示优先连接（preferential attachment）。
- 关键对比：**组合的产生速率保持不变，而"新的基础技术能力（building blocks）"的产生速率显著放缓**。

> 工程含义：把技术分为**能力（capability / building block）**与**配方（combination）**两层，两层用不同的、独立的随机过程驱动。能力层慢且稀有，配方层快且常见。α≈0.6 是一个可直接使用的先验。

### 2.8 学习曲线：Wright / Moore / 设计复杂度
- **Wright 1936**（*J. Aeronautical Sciences* 3:122–128, DOI 10.2514/8.155，元数据已核验）：单位成本随累计产量幂律下降。
- **Argote & Epple 1990**（*Science* 247:920–924, DOI 10.1126/science.247.4945.920，元数据已核验）：制造业学习曲线的实证综述。
- **McNerney, Farmer, Redner & Trancik 2011**（*PNAS* 108:9008–9013, DOI 10.1073/pnas.1017298108，**摘要+正文摘录已核验**）：把学习曲线指数从**设计结构**里推导出来。技术由 `n` 个组件构成，每个组件与 `d−1` 个其他组件互动（Design Structure Matrix）。试错：随机改动一个 cluster 内所有组件的成本，只有总成本下降才接受。结果：
  - `E[κ(t)] ∝ t^{−1/(γd)}`，即 **`α = 1/(γ·d*)`**
  - `γ` = 找到更好组件的内在难度；`d*` = **设计复杂度**（连通度恒定时 `d* = d`；连通度可变时 `d* = max{d_min(i)}`，即**瓶颈组件**决定全局改进速度）。
  - 90 个随机 DSM（`d*` 从 1 到 9）与理论吻合。
- **Nagy, Farmer, Bui & Trancik 2013**（*PLoS ONE* 8:e52669, DOI 10.1371/journal.pone.0052669，正文已读）：62 项技术（Chemical/Hardware/Energy/Other），时间跨度 10–39 年；Wright 与 Moore 表现相近，Sahal 猜想成立。
- **Farmer & Lafond 2016**（*Research Policy* 45:647–665, DOI 10.1016/j.respol.2015.11.001；**arXiv:1502.05274 全文 PDF 已抽取**）：66 项技术中 53 项有统计显著改进。模型 `y_t − y_{t−1} = μ + v_t + θ v_{t−1}`（IMA(1,1)），`v_t ~ N(0, σ²)`。参数表见 §4。噪声与改进率的关系：`K̃ = 0.02 − 0.76 μ̃`，`R² = 0.87`（斜率标准误 0.04）。

> 工程含义：**learning curve 不是外挂的经验曲线，而是"配方的组件依赖结构"的函数。**我们已经打算存组件依赖图，那么 `α = 1/(γ d*)` 可以直接从图上算出来，且"瓶颈组件"给了一个天然的叙事钩子（"因为炉温上不去，冶铁一百年没有进步"）。

### 2.9 人口规模—文化复杂度（collective brain）与其反驳
- **Henrich 2004**（*American Antiquity* 69:197–214, DOI 10.2307/4128416，元数据已核验；模型细节经 Vaesen et al. 2016 正文转述已核验）：有效人口 `N` 与技能复杂度的临界关系 **`N* = e^{(c̄ − ε)}`**（`c̄` 为平均模仿误差/复杂度参数，`ε ≈ 0.577` 为 Euler–Mascheroni 常数）。传递方式为 "Best"（学最好的那个人），且要求人口收缩时发生 **Complexity Regression**（退回更易复制的技术）。
- **Powell, Shennan & Thomas 2009**（*Science* 324:1298–1301, DOI 10.1126/science.1170165，元数据已核验；模型细节经 Vaesen 转述）：传递方式为 "Payoff"（先垂直学父母，再按技能水平比例挑第二个文化父母），并假设 **Complexity Maximization**（人口增长时总是转向更复杂的技术）。
- **反驳 — Vaesen, Collard, Cosgrove & Roebroeks 2016**（*PNAS* 113, DOI 10.1073/pnas.1520288113，摘要+正文摘录已核验）：
  - 上述两模型只在"不合理的条件下"才支持人口—文化关系；换用其他（民族志上更常见的、以垂直传递为主的）传递过程，人口与技能水平的关联消失。
  - 塔斯马尼亚案例反例：**骨尖并不比后来仍在使用的编篮、树皮独木舟更难做**，所以"因人口下降退回简单技术"讲不通。
  - 旧石器晚期转变的检验在撒哈拉以南非洲、北/中亚、南亚、澳大利亚均有"非平凡的违例"。
- **Henrich 等的回应**：Henrich, Boyd, Derex, Kline, Mesoudi & Muthukrishna 2016, "Understanding cumulative cultural evolution", *PNAS* 113, DOI 10.1073/pnas.1610005113（元数据已核验）。
- **Read 的独立批评**：Read 2008, "An Interaction Model for Resource Implement Complexity Based on Risk and Number of Annual Moves", *American Antiquity* 73:599–625, DOI 10.1017/s0002731600047326（元数据已核验）；Andersson & Read 2016, "The Evolution of Cultural Complexity: Not by the Treadmill Alone", *Current Anthropology* 57:261–286, DOI 10.1086/686317（元数据已核验）。
- **定义敏感性**：Querbes, Vaesen & Houkes 2014, *PLoS ONE* 9:e102543, DOI 10.1371/journal.pone.0102543（摘要已核验）——**换成 Herbert Simon 的复杂度定义，人口的作用大幅缩小**；现有证据无法判定哪个定义正确。
- **支持性实证**：
  - Kline & Boyd 2010（*Proc. R. Soc. B* 277:2559–2564, DOI 10.1098/rspb.2010.0452，摘要已核验）：大洋洲岛屿，人口小 → 海洋觅食技术更简单。**注意**：作者自己承认此前两项系统性定量检验（大陆人群）**不支持**该预测，其贡献在于加入了接触率。
  - Collard, Ruttle, Buchanan & O'Brien 2013, *PLoS ONE* 8:e72628, DOI 10.1371/journal.pone.0072628（元数据已核验）；Collard et al. 2011, *Biological Theory* 6:251–259（元数据已核验）——食物生产社会中人口规模的解释力弱。
  - Derex, Beugin, Godelle & Raymond 2013（*Nature* 503:389–391, DOI 10.1038/nature12774，元数据已核验）：实验证明群体规模影响文化复杂度。
  - Muthukrishna, Shulman, Vasilescu & Henrich 2014（*Proc. R. Soc. B* 281:20132511, DOI 10.1098/rspb.2013.2511，摘要已核验）：可观察 **5 个** 模型者在 10 代实验中技能持续提升，只能观察 **1 个** 的则毫无提升；实验 2（打绳结）中只有 1 个模型者的组**技能流失更快**。
  - **Derex & Boyd 2016**（*PNAS* 113:2982–2987, DOI 10.1073/pnas.1518798113，摘要已核验）与 **Derex, Perreault & Boyd 2018**（*Phil. Trans. R. Soc. B* 373:20170062, DOI 10.1098/rstb.2017.0062，元数据已核验）：**部分连通（partially connected）优于全连通**。全连通群体因"都去学最成功者"而丧失多样性，反而做不出复杂解；中等程度的人口分割最大化文化积累。
  - Derex, Bonnefon, Boyd & Mesoudi 2019（*Nature Human Behaviour* 3:446–452, DOI 10.1038/s41562-019-0567-9，元数据已核验）：**因果理解不是技术改良的必要条件**——纯选择性复制就能改良技术，同时不产生对应的理论理解。

> 工程含义（三条硬约束）：
> 1. 不要用"人口 → 技术复杂度"的单调函数；证据是有争议的（C 级）。
> 2. **要用"网络结构"而不是"人口标量"**：部分连通 > 全连通是目前最稳的实验结论之一。
> 3. **技术可以在没有理论的情况下变好**（Derex 2019）——这允许我们让 λ（配方）与 Ω（原理）解耦演化，正是 Mokyr 框架要的。

### 2.10 扩散：Bass / Rogers 与它们在古代的适用性
- **Bass 1969**, "A New Product Growth for Model Consumer Durables", *Management Science* 15(5):215–227, DOI 10.1287/mnsc.15.5.215（**元数据已核验**）；2004 年 *Management Science* 50 卷有重刊与作者评论（DOI 10.1287/mnsc.1040.0264 / 10.1287/mnsc.1040.0300）。核心：`f(t)/(1−F(t)) = p + q·F(t)`，p = 创新系数（外部影响），q = 模仿系数（内部影响）。
- **Rogers, *Diffusion of Innovations***：本次未在 Crossref 检索到可靠的原书条目（只检索到二手章节，如 Rogers 1993 DOI 10.1007/978-94-011-1771-5_2）。原书 1962/2003 版标记为 `recalled_not_verified`。
- **Granovetter 1978**, "Threshold Models of Collective Behavior", *AJS* 83:1420–1443, DOI 10.1086/226707（元数据已核验）。
- **Centola & Macy 2007**, "Complex Contagions and the Weakness of Long Ties", *AJS* 113:702–734, DOI 10.1086/521848（元数据已核验，正文付费墙）；**Centola 2010**, *Science* 329:1194–1197, DOI 10.1126/science.1185231（元数据已核验）。核心区分：**simple contagion**（一次接触即可传染，长程弱连接加速传播）vs **complex contagion**（需要多个独立来源的社会强化，长程弱连接反而无用，需要**冗余的局部聚簇**）。
- **对古代的适用性判断（关键）**：见 §2.11 与 §7.1。技术采用几乎全部是 complex contagion（需要师徒、需要重复暴露、需要本地材料），因此 **Bass/Rogers 的 S 曲线可以作为"结果形状"的检验，但绝不能作为"生成机制"**。

### 2.11 空间扩散的可计算模型（波前 / Fast Marching / 成本面）
- **Ammerman & Cavalli-Sforza 1971**, "Measuring the Rate of Spread of Early Farming in Europe", *Man* 6:674, DOI 10.2307/2799190（元数据已核验）；1984 专著 DOI 10.1515/9781400853113（元数据已核验）。
- **Pinhasi, Fort & Ammerman 2005**, *PLoS Biology* 3:e410, DOI 10.1371/journal.pbio.0030410（**全文已读**）：735 个早期新石器遗址（扩展到 765），大圆距离与最短路径两种度量，得到欧洲平均扩散速率 **0.6–1.3 km/yr（95% CI）**，相关系数 R > 0.8。见 §4。
- **Fort 2012**, *PNAS* 109:18669–18673, DOI 10.1073/pnas.1200662109（摘要已核验）：把 demic 与 cultural 统一在一个框架，**文化扩散解释了欧洲新石器扩散速率的约 40%**，但 demic 仍是主导机制。
- **Fort 2015**, *J. R. Soc. Interface* 12:20150166, DOI 10.1098/rsif.2015.0166（元数据已核验，正文 403）；**Fort 2022**, *Archaeol. Anthropol. Sci.* 14, DOI 10.1007/s12520-022-01619-x（元数据已核验，正文被 Springer 拦截）。
- **Silva & Steele 2014**, "New methods for reconstructing geographical effects on dispersal rates and routes from large-scale radiocarbon databases", *J. Archaeological Science* 52:609–620, DOI 10.1016/j.jas.2014.04.021（元数据已核验，ScienceDirect PDF 403）。方法：**Fast Marching 成本面 + reduced major axis 回归**。
- **Silva, Steele, Gibbs & Jordan 2014**, *Radiocarbon* 56:723–732, DOI 10.2458/56.16937（**PDF 已抽取正文**）与 **Jordan, Gibbs, Hommel, Piezonka, Silva & Steele 2016**, *Antiquity* 90:590–603, DOI 10.15184/aqy.2016.68（**PDF 已抽取正文**）：陶器扩散，数值见 §4，**这是本简报最有工程价值的一组数字**。
- **Ackland, Signitzer, Stratford & Cohen 2007**, "Cultural hitchhiking on the wave of advance of beneficial technologies", *PNAS* 104:8714–8719, DOI 10.1073/pnas.0702469104（**PMC 全文已读**）：Fisher 方程推广到三个共存群体（农人 F、采集者 H、皈依者 X）。参数见 §4。核心结果：**没有内在优势的性状（语言、基因标记）会"搭便车"随农业波前扩散；一旦本地人独立采纳了那项有优势的技术，搭便车性状就与之解耦，从而在该处留下一条永久的文化边界。**

### 2.12 知识的组织载体：clans / guilds / markets
**de la Croix, Doepke & Mokyr 2018**, "Clans, Guilds, and Markets: Apprenticeship Institutions and Growth in the Preindustrial Economy", *QJE* 133:1–70, DOI 10.1093/qje/qjx026（**NBER WP 22131 全文 PDF 已抽取**）：
- 核心机制：知识是 tacit 的，只能人对人传。学徒从 `m` 个师傅那里学，学到的成本参数是 **`h_L(m) = min{h_1, h_2, …, h_m}`**（即学到接触过的最有效率的技术）。之后可自行创新得到 `h_N`，取二者更优。
- **制度决定 `m`**：clan（家族）→ `m` 小且同质；guild + journeymanship（游历学徒）→ `m` 大且跨地域；market → `m` 最大。
- 历史论断：欧洲师徒之间**通常没有血缘关系**；"In China, guilds existed, but were organized along clan lines and it is within those boundaries that apprenticeship took place"（引 Moll-Murata 2013, p.234）。
- 参数化示例（作者声明**未做正式校准**）：一期 = 25 年；`a=0.8, q=0.25, g=0.1, n̄=2, s=7.5, o=3, k=0.02, l=4`。
- 相关：Epstein 1998, *J. Economic History* 58:684–713, DOI 10.1017/s0022050700021124（元数据已核验，正文未读）。

---

## 3. 可直接用于本项目的机制清单

> 记号约定：`Cap` = capability（能力/基础技术），`Rec` = recipe（配方/做法），`Ω` = 命题知识节点，`Comm` = 社区/组织（可以是村落、作坊、行会、官营工场、寺院），`M` = 物质/材料类型。

### 3.1 【M1】技术表示：能力—配方二部图（替代科技树）
**输入 → 输出**：世界物质状态 + 社会状态 → 一个可查询的"某社区此刻能做什么"。

**数据结构**（这是本简报的核心交付物）：

```
Capability C = {
  id,
  kind: ("material_transform" | "tool" | "practice" | "knowledge_artifact" | "organizational_form"),
  # 前置：物质条件
  material_inputs: [ (MaterialType, qty_per_unit) ],
  # 前置：能力条件（递归——这就是 Arthur 的组合递归）
  required_caps: [ CapId ],          # 硬前置，缺一不可
  enabling_caps: [ (CapId, weight) ],# 软前置，影响良品率/成本而非可行性
  # 前置：环境/物理条件
  physical_reqs: { temp_C, pressure, water, fuel_MJ_per_unit, ... },
  # 前置：社会组织条件
  org_reqs: { min_specialists, min_coordinated_labor, min_capital_stock,
              needs_standing_org: bool, needs_literacy: bool },
  # 知识条件（Mokyr）
  lambda_recipe: RecipeGraph,        # 处方知识：步骤 DAG
  epistemic_base: [ OmegaId ],       # 命题知识依赖（可为空！）
  base_width: float in [0,1],        # = |epistemic_base 中已被本社区掌握的| / 理论上需要的
  # 隐性知识（这是"失传"的引擎）
  tacit_fraction: float in [0,1],    # 无法写下来、必须师徒传的比例
  carriers: [ (AgentId | OrgId, skill_level) ],  # 当前活着的载体
  codified_in: [ ArtifactId ],       # 书、图样、模具、母版——可以离开人存在
  # 性能与经济
  perf_vector: { cost, throughput, quality, durability, ... },
  learning_state: { cum_output, d_star, gamma },   # 见 M4
  # 因果溯源
  origin_event: EventId
}
```

**为什么这样简化**：
- 「硬前置 required_caps」承担了科技树里 prerequisite 的功能，但它不是设计者写死的一条线，而是**由发明事件在运行时生成的边**（见 M2）。同一个功能可以由多条不同的 `required_caps` 路径实现 → 允许"平行技术传统"。
- 「org_reqs」让技术与政治/经济状态耦合：没有能维持 200 人协作的组织，就造不出大型水利/冶铸设施，无论知识多完备。
- 「carriers vs codified_in」是失传机制的物理基础。
- 「epistemic_base 可为空」直接编码了 Derex et al. 2019 的结论：**技术可以在没有原理理解的情况下变好**。

**时间尺度**：结构本身无时间；查询在每个决策 tick 发生。
**空间粒度**：Capability 实例是**社区级**的（同一个 Capability 在不同社区有不同的 carriers / learning_state / perf_vector）。全局只存"这个 Capability 的定义"。
**证据等级**：**B**（结构综合自 Arthur 2009 的组合递归 + Mokyr 的 Ω/λ + Youn 2015 的 building-block/combination 两层区分 + de la Croix 的载体化知识。每个组成部分有文献支撑，但这个具体的数据结构是我们的设计，无文献直接背书。）
**归属**：`rules_math`（结构与判定完全由规则决定；LLM 只能给新 Capability**命名和写描述**）。

### 3.2 【M2】发明事件：四通道泊松过程
**输入**：社区 `k` 在时刻 `t` 的 `{可用组件集 n_k, 未满足需求向量 D_k, 专家人时预算 B_k, 网络暴露 X_k, 材料可得性}` → **输出**：0 个或多个新 Capability / 新 Recipe / 改良事件，每个都带完整因果链。

四条通道相加得到总强度：

```
Λ_k(t) = Λ_search + Λ_demand + Λ_serendipity + Λ_transfer
```

**(a) 组合搜索 Λ_search（Arthur / Fink & Reeves）**
```
Λ_search = ρ_s · B_k · Δp̄_k / p̄_k
```
其中 `p̄_k` 用 Fink & Reeves 守恒律近似，不枚举组合：
```
p̄_k ≈ Σ_c  P(c) · C(n_k, c)      # P(c) = 本社区配方复杂度分布
```
增量用复杂度折扣：新增一个组件时 `p̄(n+1)/p̄(n) ≈ Σ_c P(c)·(1+1/n)^c`。
- 建议 `P(c)` 用**泊松**（Fink & Reeves 明确说泊松 > 二项 > 常数），均值 `c̄` 随文明阶段从 2 涨到 8+。
- 采样出的候选组合，用**优先连接**加权（Youn 2015 的 `x^{−2.4}` 重尾）：常用组件更可能被再组合。
- 结果分岔：以 `α ≈ 0.6` 的概率是"新组合"（探索），`0.4` 是"既有组合的精炼"（利用）—— **这个比例来自 Youn et al. 2015 且在 200 年间不变，可直接当常数**。

**(b) 需求拉动 Λ_demand（Boserup / 诱导创新）**
```
Λ_demand = ρ_d · Σ_j  w_j · shortfall_j · (候选配方能缓解 j 的程度)
```
`shortfall_j` 来自世界状态：粮食缺口、军事压力、运输瓶颈、疫病死亡率、税负、水患。
- 这是**因果链最重要的一条**：任何重大技术突破都应该能回答"当时缺什么"。
- ⚠️ 但不要让它成为唯一通道，否则技术会变成"需求的确定性函数"，失去偶然性。建议 `Λ_demand` 占总强度 30–50%。

**(c) 偶然 Λ_serendipity**
```
Λ_serendipity = ρ_r · (人口暴露量) · (异常事件标记)
```
触发源必须是世界里真实发生的事：火灾、矿脉裸露、战俘/工匠迁徙、洪水改道暴露地层、瘟疫后劳动力短缺、贸易带来陌生材料。
- **规则**：偶然发明必须**指向一个具体的世界事件 ID**。没有事件 ID 的偶然不允许发生。这是"允许荒诞但不允许无缘无故"的执行点。

**(d) 输入性发现 Λ_transfer**：见 M6。

**规模效应怎么放（关键的争议处理）**：
- 不要用 `Λ ∝ N`（Kremer 式），也不要用 `N* = e^{c̄−ε}` 硬阈值（Henrich 式，被 Vaesen 反驳）。
- 建议用**网络化的有效脑规模**：
  ```
  N_eff = ( Σ_over_subgroups  n_i^β )  × f(网络分割度)
  ```
  - `β = 1.27`（Bettencourt et al. 2007 城市专利标度指数，95% CI [1.25, 1.29]）—— ⚠️ 这是**现代城市**数据，用于古代必须标记为外推。
  - `f(分割度)` 取**单峰函数**，在中等分割处最大（Derex & Boyd 2016；Derex, Perreault & Boyd 2018："intermediate levels of population fragmentation maximize cultural accumulation"）。这条比"人口越大越好"稳得多。
- **专家人时 `B_k` 比总人口更重要**：`B_k = Σ_specialists (可支配时间 × 技能)`，由农业剩余、税收、庇护制度决定。这样"国家出现 → 专业工匠 → 技术加速"就是涌现的，不是写死的。

**时间尺度**：年 tick（发明事件稀疏，年级足够）。
**空间粒度**：社区/城市级。
**证据等级**：**B**（各通道分别有 A/B 级支撑，组合权重无来源 → 权重本身是 D 级）。
**归属**：`rules_math` 决定**是否**发生发明、发明落在配方图的哪个位置、性能如何。`llm_agent` 只负责给它**命名、写出世界内的解释与叙事**（可以是错的、迷信的——这正是我们要的"世界内知识 ≠ 世界事实"）。

### 3.3 【M3】能力层 vs 配方层的双速率
**输入 → 输出**：同 M2，但分两个池子。
- **配方层**（既有能力的新组合）：高速率，占绝大多数发明事件。
- **能力层**（全新的 building block，例如"可控高温"、"可书写的符号系统"、"畜力牵引"）：**独立的、低得多的速率**，且强烈依赖 `epistemic_base` 与偶然。
- 实证依据：Youn et al. 2015 —— 组合速率不变，**而新技术能力的引入速率显著放缓**。

**数学草图**：
```
Λ_cap = ρ_c · B_k · Π_over_required_omega( base_width ) · (偶然乘子)
Λ_rec = Λ_search + Λ_demand   （见 M2）
建议初值 ρ_c / ρ_rec ~ 10^-2 到 10^-3
```
**证据等级**：**B**（两层结构 A 级实证；比值是 D 级）。
**归属**：`rules_math`。

### 3.4 【M4】学习曲线：由配方图结构推导，不外挂
**输入**：Capability 的组件依赖图 + 累计产量 → **输出**：性能改善。

```
perf(t) = perf_0 · (cum_output)^(-α),   α = 1 / (γ · d*)
d* = max_i { d_min(i) }      # 瓶颈组件的最小出度（McNerney et al. 2011）
```
- `γ` = 找到更好组件的内在难度（材料越接近物理极限，γ 越大）。
- **瓶颈组件是天然的叙事钩子**：模拟可以直接回答"为什么这项技术两百年没进步" → "因为 `d_min` 最小的那个组件是 X，而改良 X 需要能力 Y，而 Y 需要 Ω_z"。
- 每年的实际改善加上噪声，用 Farmer & Lafond 的 IMA(1,1)：
  ```
  log(cost_t) − log(cost_{t-1}) = μ + v_t + θ v_{t-1},  v_t ~ N(0, σ²)
  σ ≈ 0.02 − 0.76·μ   （μ 为负；R² = 0.87）
  ```
- **μ 的取值范围**见 §4 表 4.3。对前工业手工业，建议 `μ ∈ [−0.02, −0.001]/yr` 并且只在"有持续生产 + 有师徒链 + 有需求"时才计时。⚠️ Farmer & Lafond 的数据全部来自 20 世纪工业，用于古代是**外推**，必须标 D 级。
- **学习会衰减**：`cum_output` 不生产就不涨；且若 carriers 断代，应把 `cum_output` 折损（见 M5）。

**时间尺度**：年。**空间粒度**：社区×Capability。
**证据等级**：机制 **A**（McNerney 理论 + Wright/Argote-Epple/Nagy 实证）；古代参数值 **D**。
**归属**：`rules_math`。

### 3.5 【M5】失传：四条独立的、可追溯的通道
**输入**：人口/组织/贸易/需求状态 → **输出**：Capability 在某社区被标记为 `lost` 或 `degraded`。

一个 Capability 在社区 `k` 存活，需要同时满足四个条件；任一断裂即触发退化：

**(a) 载体断裂（carrier death）**
```
P(lost | carriers) = Π_over_carriers (1 - transmission_success)
transmission_success = f( m,  tacit_fraction,  contact_years )
```
- 沿用 de la Croix et al.：学徒学到的是 `min{h_1..h_m}`。若 `m` 骤降（家族/行会瓦解、屠城、瘟疫、强制迁徙），下一代掌握的技能水平**分布左移**。
- Muthukrishna et al. 2014 的实验：`m = 1` 的组在打绳结任务中技能**流失更快**；`m = 5` 的组不流失。这是我们能拿到的最直接的 `m` 效应实证。
- 复制误差：把每次传递的连续参数乘以 `ε ~ N(1, σ_ε²)`，`σ_ε ≈ 0.03`（Weber fraction ≈ 3%，见 §4）。多代累积方差 `Var(X_n) = X_0²·(E[ε²] − 1)^n`（Kempe, Lycett & Mesoudi 2012 的 ACE 模型）。
  - ⚠️ 该文自己指出：ACE 模型预测的方差**远高于**实测手斧方差（不到 200 代就该超过 CV=0.30，但实测 1.5–0.3 Ma 的手斧 CV 长度 0.30 / 宽度 0.23）。所以**必须配一个纠错/吸引子机制**（师傅纠错、模板/模具、功能筛选），否则我们的技术会在几十代内漂移成噪声。

**(b) 组织解体（organizational dissolution）**
- 若 `org_reqs.min_coordinated_labor` 或 `needs_standing_org` 不再满足（国家崩溃、官营工场废弃、行会被禁），Capability 立即变为 `dormant`（配方还在书上/记忆里，但做不出来）。
- `dormant` 与 `lost` 必须分开：`dormant` 可在组织重建时以折扣恢复；`lost` 不能。

**(c) 原料断供（material supply break）**
- 若 `material_inputs` 中任一 MaterialType 的可得量在 `T` 年内为 0（矿脉枯竭、贸易路线被切断、气候导致某作物退出、战争封锁），则 Capability 不再被实践 → `cum_output` 停滞 → carriers 老死 → 转 `lost`。
- 这是**最"有缘由"的失传通道**，也最容易讲清因果链，建议做成主要通道。

**(d) 需求消失 / 被替代（demand collapse）**
- 对应 §2.4 CF 模型里的 `μ`、§2.5 的老化核。建议用**指数型**淘汰（Solé et al. 2016 证明幂律老化仍会导致奇点，指数老化则给出线性长期动力学）。
- 具体：`P(retire) = 1 − exp(−μ_d · Δt)`，`μ_d` 随"存在更优替代品的性能比"上升。

**恢复（reinvention / rediscovery）**：
- 若 `codified_in` 非空（有书、有图样、有实物、有模具），恢复成本 = `tacit_fraction × 原始发明成本`。`tacit_fraction` 高的技术（如冶金火候、船体线型）即使有书也很难复原 —— 这正是 MacKenzie & Spinardi 1995 关于核武器"uninvention"的论点（*AJS* 101:44–99, DOI 10.1086/230699，**元数据已核验，正文付费墙未读**）。
- 若 `codified_in` 为空且 carriers 全死 → 只能重新发明（回到 M2，且因为组件集仍在，重发明比首次发明快）。

**时间尺度**：年（检查）+ 代（25 年，传递事件）。
**空间粒度**：社区×Capability。
**证据等级**：机制 **B**；具体阈值 **D**。
**归属**：`rules_math` 决定失传是否发生。`llm_agent` 只能生成世界内的**解释/传说**（"祖师爷带走了秘方"）——而世界事实数据库里记的是"最后 3 名载体死于某年瘟疫 + 铜矿在 12 年前枯竭"。

### 3.6 【M6】扩散：三层管线（暴露 → 采纳决策 → 实施）
**不要用单一的 Bass 方程。**用三个必须依次通过的关卡：

**Layer 1 — 暴露（exposure）：几何/网络问题**
```
exposure_rate(k→j) = φ · flow(k,j) · visibility(Cap)
```
- `flow(k,j)` 来自**已经存在的**贸易、迁徙、朝贡、战争、通婚、宗教巡礼流量，**不要为技术扩散单独造一个流量**。
- 空间上用 **Fast Marching + 各向异性成本面**（Silva & Steele 2014 的方法）：
  - 成本面按生物群区/地形给"boost 因子"。**Jordan et al. 2016 拟合出的 boost 因子是 5×（欧亚草原-温带林走廊）与 7×（环地中海走廊）** —— 这是我见到的唯一一组从考古数据里反解出的量化地理加速倍数。
  - 河流与海岸线做成低成本通道；山脉/沙漠/热带雨林做成高成本。
  - `visibility` 区分：成品可见（陶器、铁器、马镫）vs 过程不可见（冶炼工艺、育种、账簿制度）。**成品可见但过程不可见的技术，会先扩散"想要"再扩散"会做"** —— 这是一个非常好的因果钩子（进口依赖 → 贸易逆差 → 试图仿制 → 逆向工程失败/成功）。

**Layer 2 — 采纳决策（adoption）：complex contagion，不是 simple**
```
adopt if  Σ_over_independent_sources  w_s  ≥  θ_j(Cap)
```
- **需要多个独立来源的社会强化**（Centola & Macy 2007）。单次接触不足以采纳。这直接解释了为什么"长距离弱连接"能带来商品却带不来技术。
- 阈值 `θ_j` 由本地条件决定：
  ```
  θ_j = θ_0 · (1 + 制度阻力 + 宗教禁忌 + 行会保密 + 语言距离 + 既得利益者阻挠)
              / (1 + 相对优势 in 本地环境)
  ```
- **相对优势必须在本地重算**：水稻在纬度/日照不合适的地方相对优势为负，任何暴露都不会导致采纳（对应 d'Alpoim Guedes & Bocinsky 2018 的作物热量生态位）。
- 制度阻力有真实文献：Mokyr 的 *Gifts of Athena* Ch.6 标题即 "The Political Economy of Knowledge: **Innovation and Resistance** in Economic History"（章节标题已核验）。

**Layer 3 — 实施（implementation）：需要本地材料 + 本地技能**
- 通过 Layer 2 只表示"想采纳"。真正获得 Capability 还需要：
  - `material_inputs` 本地可得或可进口；
  - 获得 `tacit_fraction` 对应的隐性知识 —— 只能通过**人的迁移**（工匠移民、战俘、通婚、留学、绑架、雇佣）。
  - 若 `tacit_fraction > τ_crit`（建议 0.5），**没有人的物理迁移就不可能实施**，只能进口成品。
- 这一层是"技术扩散慢于商品扩散"的机制来源，也是"抢工匠"成为战争目标的机制来源。

**时间尺度**：Layer 1 年级；Layer 2 年级；Layer 3 代级（因为要走完学徒周期，3–7 年，见 §4）。
**空间粒度**：社区 ↔ 社区，成本面用栅格（建议 5–10 km 网格，与 d'Alpoim Guedes & Bocinsky 2018 使用的 ETOPO5 ~10 km 同量级）。
**证据等级**：Layer 1 **A**（有 km/yr 数值与 boost 因子）；Layer 2 **B**；Layer 3 **B**。
**归属**：Layer 1 `rules_math`；Layer 2 `hybrid`（阈值与相对优势由规则算，但"某个统治者为什么否决了这项技术"可以交 LLM 给动机——**但 LLM 的决定必须落在规则允许的区间内**）；Layer 3 `rules_math`。

### 3.7 【M7】文化搭便车与文化边界的自动生成
**输入**：技术波前 + 中立文化性状 → **输出**：语言/族群/习俗边界。

采用 Ackland et al. 2007 的机制：
- 农人 F / 采集者 H / 皈依者 X 三群共存，Fisher 型反应扩散。
- 无内在优势的性状（语言、图腾、埋葬方式、基因标记）随 F 的波前**搭便车**。
- **一旦 H 独立学会了那项技术（变成 X），搭便车就在那里终止，形成一条永久的文化边界。**

> 这个机制极其重要：它让**族群边界、方言边界、丧葬习俗边界**成为技术扩散史的副产品，而不是我们手画的。而且它是**路径依赖的**——同一个地形，采纳时序不同，边界位置就不同。

**证据等级**：**B**（单一模型研究，但机制清晰且与欧洲考古/遗传学定性吻合）。
**归属**：`rules_math`。

### 3.8 【M8】Ω（原理）与 λ（配方）的双图耦合
- 维护第二张图 `Ω`：命题知识节点（可以是错的！"金属由硫与汞构成"也是一个 Ω 节点）。
- `Ω` 的产生渠道：从 λ 的反复实践中归纳（慢、易错）、从异常观测中产生、由专门的"求知者"角色产生（祭司、天文官、医者）。
- **`base_width` 的作用**（三条，都能算）：
  1. 提高 M2 中该技术方向的搜索命中率（有理论 → 少走弯路）；
  2. 降低 `tacit_fraction`（能写下来 → 可编码 → 抗失传）；
  3. 允许**跨领域迁移**（同一个 Ω 支撑多个 λ → 一个 Ω 的突破同时改良多条技术线）。
- **反过来**：`base_width = 0` 的技术照样可以通过纯选择性复制改良（Derex et al. 2019，A 级实证）。所以不要把 Ω 做成硬前置。
- **错误的 Ω 也有效**：只要它能指导出可行的 λ。这允许炼丹术、风水、体液学说在模拟里"有用"，并在后世被推翻——而世界内的历史学家会为此争论。

**证据等级**：Ω/λ 二分 **B**（Mokyr，术语未核验）；"无理论也能改良" **A**（Derex et al. 2019）。
**归属**：`hybrid`。Ω 节点的**内容**（世界里的人相信什么）非常适合 LLM 生成；Ω 节点的**效果**（`base_width` 加成多少）必须由规则决定。

---

## 4. 硬数字与参数表

### 4.1 空间扩散速率（考古反解，最有用的一组）

| 量 | 数值 | 适用时空范围 | 不确定度 | 来源（均为本次已读全文） |
|---|---|---|---|---|
| 新石器农业扩散速率（欧洲，总体） | **0.6–1.3 km/yr** | 欧洲/近东/安纳托利亚，735 个遗址 | 95% CI | Pinhasi, Fort & Ammerman 2005, *PLoS Biol* 3:e410 |
| — 大圆距离，未校正 / 已校正 | 0.7–1.1 / **0.6–1.0 km/yr** | 同上 | 95% CI | 同上 |
| — 最短路径，未校正 / 已校正 | 0.8–1.3 / **0.7–1.1 km/yr** | 同上 | 95% CI | 同上 |
| 距离—年代相关系数 | **R > 0.8**（如 Abu Madi 中心 R = 0.827 ± 0.026） | 同上 | — | 同上 |
| 时滞 demic 模型预测速率 | 0.6–1.1 km/yr | 同上 | — | 同上 |
| 文化扩散对新石器扩散速率的贡献 | **≈ 40%**（demic 仍主导） | 欧洲大陆尺度 | 定性"约" | Fort 2012, *PNAS* 109:18669 |
| 陶器扩散：东亚源，无地理加成 | **0.31 km/yr**（Pearson r = −0.33） | 亚洲扩散区，396 个用于分析的遗址（数据库 942） | r² ≈ 0.11 | Jordan et al. 2016, *Antiquity* 90:590 |
| 陶器扩散：北非源，无地理加成 | **0.79 km/yr**（r = −0.31） | 非洲扩散区 | r² ≈ 0.10 | 同上 |
| 陶器扩散：东亚源，走廊内 / 走廊外 | **1.25 / 0.25 km/yr**（最佳解；全部最佳解均值 **1.20 ± 0.07 / 0.22 ± 0.09**） | 欧亚温带草原-森林走廊 | Pearson r = −0.57 | 同上 |
| 陶器扩散：北非源，走廊内 / 走廊外 | **3.23 / 0.46 km/yr**（均值 **3.32 ± 1.45 / 0.45 ± 0.09**） | 环地中海森林/灌丛走廊 | r = −0.51 | 同上 |
| **地理走廊加速倍数（拟合值）** | **欧亚走廊 5×，环地中海走廊 7×** | 全新世早中期 | 自由参数最优化得到 | 同上 |
| 最佳模型对到达年代方差的解释力 | **最大 r² = 0.36** | 全球陶器 | — | 同上 |
| 陶器独立起源年代 | 东亚 **c. 16,000 cal BP**；北非 **c. 12,000 cal BP** | — | — | 同上 |
| 陶器扩散（早期回归分析）三中心速率 | 中国 **0.32**（r²=0.186，cutoff 4790 km）；西伯利亚 **0.67**（r²=0.192，6426 km）；北非 **0.80**（r²=0.091，6336 km）km/yr | 旧大陆 | r² 极低 | Silva, Steele, Gibbs & Jordan 2014, *Radiocarbon* 56:723 |
| 反应扩散模型的欧洲农业波速 | **≈ 1 km/yr** | 欧洲 | 模型输出 | Ackland et al. 2007, *PNAS* 104:8714 |

> **对模拟最重要的一条不是速率，而是 r²。**即使加了地形、生物群区走廊、两个独立起源、自由拟合的加速倍数，最好也只解释 **36%** 的到达时间方差。**技术扩散在经验上主要是噪声。**任何把扩散做成确定性波前的实现都会比现实更整齐。

### 4.2 东亚农业扩散年代（贝叶斯建模，95% 概率区间与中位数）
来源：Leipe, Long, Sergusheva, Wagner & Tarasov 2019, "Discontinuous spread of millet agriculture in eastern Asia and prehistoric population dynamics", *Science Advances* 5, DOI 10.1126/sciadv.aax6225（**PMC 全文已读**）。

| 区域 | 区间 (cal BCE) | 中位数 |
|---|---|---|
| 下辽河 / 下黄河（环渤海"新月带"） | 6100–5700 | **5800** |
| 中黄河 | 5000–4400 | 4600 |
| 上长江 | 3700–3100 | 3400 |
| 上黄河 | 3400–3000 | 3200 |
| 中亚 | 3200–2100 | 2400 |
| 朝鲜半岛 | 4500–3300 | 3700 |
| 兴凯湖-乌苏里 | 3700–2500 | 2900 |
| 日本列岛 | 2900–500 | **1000**（区间极宽） |

- **向西扩散是不连续的：相邻区域之间平均间隔约 1200 年。**
- 向东扩散**没有清晰的时间—距离模式**（尽管地理上更近）。
- 华北遗址数：**6400–1900 BCE 从 21 个/世纪 增至 2220 个/世纪**，最佳拟合为指数回归；1900–1600 BCE 降至 **1195 个/世纪**；到 1000 BCE 回升至 **2420**，但区域间分化（东北继续增长，中上黄河下降）。

> 这组数字是我们在东亚做校准的**首选靶子**：不是"速率是多少"，而是"扩散是断续的、有千年级停滞的、且东西方向不对称"。

### 4.3 学习曲线 / 成本下降率
来源：Farmer & Lafond 2016（arXiv:1502.05274 全文 PDF 已抽取）。`μ̃` = 成本对数的年下降率，`K̃` = 噪声标准差，`θ̃` = 自相关，`T` = 数据年数。66 项技术中 **53 项** 改进统计显著。

| 技术 | 行业 | T | μ̃ (/yr) | K̃ | θ̃ |
|---|---|---|---|---|---|
| DNA.Sequencing | Genomics | 13 | **−0.84** | 0.83 | 0.26 |
| Hard.Disk.Drive | Hardware | 20 | −0.58 | 0.32 | −0.15 |
| Transistor | Hardware | 38 | −0.50 | 0.24 | 0.19 |
| DRAM | Hardware | 37 | −0.45 | 0.38 | 0.14 |
| Laser.Diode | Hardware | 13 | −0.36 | 0.29 | 0.37 |
| Photovoltaics | Energy | 34 | −0.10 | 0.15 | 0.05 |
| Titanium.Sponge | Chemical | 19 | −0.10 | 0.10 | 0.61 |
| Automotive (US) | Cons. Goods | 21 | −0.08 | 0.05 | 1.00 |
| Monochrome.Television | Cons. Goods | 22 | −0.07 | 0.08 | 0.02 |
| Wind.Turbine (Denmark) | Energy | 20 | −0.04 | 0.05 | 0.75 |
| Geothermal.Electricity | Energy | 26 | −0.05 | 0.02 | 0.15 |
| Milk (US) | Food | 79 | −0.02 | 0.02 | 0.04 |
| Electric.Range | Cons. Goods | 22 | −0.02 | 0.04 | −0.14 |
| Sodium | Chemical | 16 | −0.01 | 0.02 | 0.42 |
| **Nuclear.Electricity** | Energy | 20 | **+0.13**（成本上升） | 0.22 | −0.13 |

- 噪声—改进率关系：**`K̃ = 0.02 − 0.76·μ̃`**，`R² = 0.87`（截距标准误 0.008，斜率 0.04）。log-log 拟合 `K̃ = e^{−0.68}·(−μ̃)^{0.72}`，`R² = 0.73`。
- 预测误差增长率：约 **2.5%/yr**（对数误差的平方根随预测跨度线性增长）。
- Nagy et al. 2013：62 项技术，Wright's law 指数 β 直方图**大致在 0.3–0.8**（该文未给出具体分位数）。
- ⚠️ **这些全部是 20 世纪工业数据。用于前工业模拟属于外推。**对手工业建议 `μ ∈ [−0.02, −0.001]/yr` 且只在持续生产时计时，并标 D 级。

### 4.4 学习曲线的结构决定式
`α = 1 / (γ · d*)`，`E[κ(t)] ∝ t^{−1/(γd)}`，连通度可变时 `d* = max_i{d_min(i)}`（瓶颈组件）。90 个随机 DSM（d* = 1..9）与理论吻合。来源：McNerney, Farmer, Redner & Trancik 2011, *PNAS* 108:9008。

### 4.5 复制误差 / 传递保真度
| 量 | 数值 | 来源 |
|---|---|---|
| Weber fraction（长度感知阈） | **≈ 3%**（两条长度差 < 3% 的线被视为相同） | Kempe, Lycett & Mesoudi 2012, *PLoS ONE* 7:e48333（全文已读，引自心理物理学文献） |
| 实测复制误差 SD | 大件 **0.0269**、小件 **0.0399**、总均值 **0.0343** | 同上（该文实验） |
| ACE 模型 | `X_n = X_0 · Π ε_i`，`ε_i ~ N(1, σ_ε²)`；`Var(X_n) = X_0²·(E[ε²] − 1)^n` | 同上 |
| Acheulean 手斧实测 CV | 长度 **0.30**、宽度 **0.23**（2601 件完整手斧，1.5–0.3 Ma） | 同上 |
| **模型与实测的矛盾** | ACE 预测 **不到 200 代** CV 就超过 0.30，实测跨百万年却没有 → **必须有纠错/吸引子** | 同上 |
| Henrich 临界人口 | **`N* = e^{(c̄ − ε)}`**，`ε ≈ 0.577` | Henrich 2004，转述自 Vaesen et al. 2016 正文（已读） |
| 观察者数目效应 | `m = 5` 组 10 代内持续改进；`m = 1` 组零改进；技能流失也是 `m=1` 更快 | Muthukrishna et al. 2014, *Proc. R. Soc. B* 281:20132511（摘要已读） |
| 学徒学到的效率 | **`h_L(m) = min{h_1, …, h_m}`** | de la Croix, Doepke & Mokyr（NBER WP 22131 全文已读） |

### 4.6 组合创新的经验常数
| 量 | 数值 | 来源 |
|---|---|---|
| 探索（新组合）占比 α | **≈ 0.6**，**近 200 年不变** | Youn et al. 2015, *J. R. Soc. Interface* 12:20150272（全文已读） |
| 至少两个技术代码的专利占比 | **77%**（1790–2010） | 同上 |
| 单代码专利占比 | 19 世纪约 **50%** → 2010 年约 **12%** | 同上 |
| 技术代码总数 / 技术类数 | **≈ 161,000 / 474** | 同上 |
| 代码与组合频次分布 | 幂律 **`~ x^{−2.4}`** | 同上 |
| 城市专利标度指数 | **β = 1.27，95% CI [1.25, 1.29]**（发明人 1.25 [1.22,1.27]；R&D 就业 1.26 [1.18,1.43]；总工资 1.12 [1.09,1.13]） | Bettencourt, Lobo, Helbing, Kühnert & West 2007, *PNAS* 104:7301（PMC 全文已读）⚠️ 现代城市数据 |
| 组合空间守恒律 | `p̄(n′,c) ≃ p̄(n,c)·(n′/n)^c` | Fink & Reeves 2019, *Sci. Adv.* 5（全文已读） |
| 复杂度分布效应 | 常数 `x^{c̄}` ≪ 二项 `(1+x²)^{2c̄}` ≪ 泊松 `e^{(x−1)c̄}`（`c̄ = 8`） | 同上 |
| TAP/CF 出生率 | `λ_n = P(x^n − 1)`，`x = 1 + α`（几何 CF） | Steel, Hordijk & Kauffman 2020（arXiv:1904.03290 全文已读） |
| 纯组合模型的宿命 | **以概率 1，要么有限时间爆炸、要么灭绝** | 同上，定理 2 |
| 组合模型奇点时刻（z=1） | `t_s = 1/(μ N_0) + t_0` | Solé, Amor & Valverde 2016, *PLOS ONE* 11:e0146180（全文已读） |
| 避免奇点的条件 | 幂律老化核 `τ^{−γ}` 在 `k > 1 + γ` 时仍爆；**指数老化核 `e^{−γN}` 不爆，长期线性** | 同上 |

### 4.7 制度与人的参数
| 量 | 数值 | 适用范围 | 来源 |
|---|---|---|---|
| 中国行会学徒期 | **通常 3 年**；每作坊学徒数常**限 1 人**；大而有名的铺子学徒少、伙计多，小铺子学徒多 | 明清 | Moll-Murata 2008, *IRSH* 53:213–247（**PDF 全文已抽取**） |
| 中国行会的组织逻辑 | 靠**把同业全部纳入**来垄断，而不是靠排斥新人；行会不正式考核师傅资质，交得起会费即可 | 同上 | 同上 |
| 非法/秘密行会 | 官府禁止未获承认的"私"会（1867 年苏州烟业秘密行会因图谋垄断被禁；同年 18 家烛铺投诉 12 人组会亦被判非法；1870 年苏州织锦工匠不获准另立第二个行会） | 清 | 同上 |
| 欧洲大陆学徒期 | **3–4 年为常态**，且随技术复杂化**逐世纪延长** | 近代早期欧陆 | de la Croix, Doepke & Mokyr（NBER WP 22131 全文已读，引 De Munck & Soly 2007 p.18；Reith 2007 p.183） |
| 英国法定学徒期 | **7 年**（1562 Statute of Artificers），但**极少被真正执行**；17 世纪末伦敦大量学徒未满期即离开 | 英格兰 | 同上（引 Wallis 2008 pp.839–40, 854；Dunlop 1911/1912） |
| 学徒契约内容 | 17 世纪契约包含**保守师傅秘密**、不逃亡、不通奸的承诺 | 英格兰 | 同上（引 Smith 1973 p.150） |
| 中欧对比 | 中国由亲属提供培训（"a narrow group of experts"），欧洲按行业组织、不依赖亲缘 | — | 同上（引 Moll-Murata 2013 p.234；van Zanden & Prak 2013a；Lucassen et al. 2008 p.16） |
| 模型的一期长度 | **25 年**（一代）；参数化示例 `a=0.8, q=0.25, g=0.1, n̄=2, s=7.5, o=3, k=0.02, l=4`（作者声明**未正式校准**） | — | 同上 |

### 4.8 人口/生态参数（用于扩散内核）
来源：Ackland, Signitzer, Stratford & Cohen 2007, *PNAS* 104:8714（PMC 全文已读）
- 采集者生育间隔 **5 年**；农人 **2 年**；两者寿命 **50 年**。
- 农业人口密度可达采集者的 **约 50 倍**。
- 最肥沃土地承载力 **50 人/km²**，随海拔与温度下降。
- 波速 **≈ 1 km/yr**，遇山减速、沿肥沃走廊加速。

### 4.9 采纳滞后（现代，仅作量级参照）
- CHAT 数据集覆盖 **104 项技术 × 161 个国家 × 200 年**；分析子样本 **25 项技术 × 132 个国家**。
- **样本平均采纳滞后 = 44 年**；平均密集边际 = 美国生产率水平的 **54%**。
- 19 世纪技术（电报、铁路）往往数十年才首次到达一国；20 世纪技术（计算机、手机、互联网）平均几十年内、有时不到十年。
- 结论：**外延边际（采纳滞后）在收敛，密集边际（渗透率）在发散**；两者变化解释了 1820 年以来大分流的 **80%**。
- 来源：Comin & Mestieri（NBER WP 19010 全文已抽取；正式发表为 *AEJ: Macroeconomics* 10:137–178, DOI 10.1257/mac.20150175，元数据已核验）。
- ⚠️ 现代数据，只用作"采纳滞后是几十年量级"的量级锚点。

---

## 5. 数据集与数据库

| 名称 | 内容 | 覆盖 | 访问 | 许可 | 对本项目的用法 |
|---|---|---|---|---|---|
| **Archaeological sites in China during the Neolithic and Bronze Age**（Hosner, Wagner, Tarasov, Chen & Leipe 2016） | **51,074 个遗址、411,456 条数据点** | 中国大部（73–131°E, 20–53°N），约 **8000–500 BC** | PANGAEA，DOI 10.1594/PANGAEA.860072，制表符分隔文本/HTML（**已抓取数据集页核验**） | **CC-BY-3.0** | **最重要的一个。**可直接做"遗址数量随时间/区域"的校准靶（对应论文 *The Holocene* 26:1576–1593, DOI 10.1177/0959683616641743） |
| **p3k14c** | 全球考古 ¹⁴C 年代合成库 | 全球 | *Scientific Data* 9 (2022), DOI 10.1038/s41597-022-01118-7（元数据已核验） | 见论文 | 用于给"扩散波前"与"人口代理指标 SPD"做校准 |
| **c14bazAAR** | R 包，聚合多个 ¹⁴C 数据库 | 全球 | *JOSS* 4:1914, DOI 10.21105/joss.01914（元数据已核验） | 开源 | 工具层 |
| **Seshat: Global History Databank** | **864 个政体、47 个地理区**；26 个通用变量 (8,924 条记录)、**77 个社会复杂度变量 (26,206 条)**、**49 个战争变量 (17,536 条)**，含青铜/剑/标枪/战斧/盾/马/海军技术/城防 | **9600 BCE – 2024 CE** | seshat-db.com（**已抓取站点核验**），有 Downloads 与 API；许可见其 /terms/current/ | 需查看 User Agreement | **技术模块的主校准集**：可检查"我们的虚拟文明在某社会复杂度水平上是否拥有相应的军事/信息技术组合" |
| **Seshat 主论文** | 51 个变量 / 414 个社会 / 30 个区 / 近 10,000 年；**单一主成分解释约 3/4 方差** | 全球 | Turchin et al. 2018, *PNAS* 115, DOI 10.1073/pnas.1708800115（PMC 全文已读摘要） | — | 提供"社会复杂度是一维的"这一强约束，可用于检验我们的世界是否产生了同样的低维结构 |
| **D-PLACE** | 跨文化比较数据库（文化实践、语言、生态） | 全球民族志社会 | d-place.org，含 /download（**已抓取站点核验**） | **CC BY-NC 4.0** | 工具包丰富度、传承方式等变量的先验分布 |
| **Peregrine, Atlas of Cultural Evolution**（2003, *World Cultures* 14(3):1–75） | **289 个史前文化**的书写/农业/运输/城市化等特征 | 全球，1000 AD 之前 | 见 Comin/Easterly/Gong 转述 | — | 1000 BC / 0 AD 技术采纳编码的底层来源 |
| **Comin–Easterly–Gong 古代技术采纳数据集** | 五部门（communications, agriculture, military, industry, transportation）的**外延边际**（用不用，不管用多少），每部门归一到 [0,1] | **1000 BC（113 国）、0 AD（135 国）、1500 AD（113 国）**；1500 AD 数据集覆盖 20 项技术（另加农业），基于 170 余种史料 | NBER WP 12657（**全文已抽取**）；发表版见 *AEJ: Macro* | 见 NBER | **可直接当作"技术组合的横截面快照"来检验我们的虚拟世界在类似社会复杂度下的技术组合是否合理** |
| **CHAT**（Comin & Hobijn） | 104 项技术 × 161 国 × 200 年的扩散曲线 | 1800– | 见 Comin & Hobijn 2010, *AER* 100:2031, DOI 10.1257/aer.100.5.2031（元数据已核验） | 见原文 | 只作现代量级参照 |
| **Rice Archaeological Database (RAD) v2.0** | **400 个遗址 / 470 个 phase**；分析保留 330 条 | 亚洲水稻 | 随 Silva et al. 2015, *PLOS ONE* 10:e0137024 的补充材料（含 KMZ）发布；**该文未给出独立下载 URL** | 论文 CC-BY；数据库本身未声明 | 水稻扩散校准 |
| **CHGIS（Chinese Historical GIS）** | 中国历史行政区划与地名 GIS | 中国历代 | 见 Sun, Bol & Zhang, *J. Historical Geography*, DOI 10.1016/j.jhg.2026.06.018（元数据已核验） | 见项目 | 若要把虚拟地理与真实中国地理对齐，这是行政/交通网络的底图参考 |
| **USPTO 技术代码组合数据** | 1790–2010 全量专利的技术代码共现 | 美国 | Youn et al. 2015 描述；PatentsView 提供原始数据 | 公有领域（USPTO） | 校准组合网络的统计性质（`x^{−2.4}`、α≈0.6） |

---

## 6. 中国与东亚特定证据

### 6.1 农业扩散：不连续、方向不对称
- **粟黍**：环渤海"新月带"约 **5800 BCE** 起源；向西扩散**不连续**，相邻区域间平均间隔 **约 1200 年**；向东（朝鲜半岛 3700 BCE 中位数、日本列岛 1000 BCE 中位数但区间 2900–500 BCE 极宽）**没有清晰的距离—时间关系**。第四千年 BCE 扩散加速，与已发表的汉藏语系自黄河流域扩张的年代吻合。（Leipe et al. 2019, *Sci. Adv.* 5, **全文已读**）
- **水稻**：最佳模型给出**长江中下游两个同时代的独立起源**（浙江 + 湖南）；用 Fast Marching 成本距离，掩掉年积温 < 2500 degree-days 的区域与沙漠，加 40 km 近海缓冲。**该文没有给出 km/yr**，而是用 10 分位数分位回归拟合距离—年代的**幂律**关系，因为"扩散波前一开始极慢，然后加速"。模型对日本的预测**过早**（预测约 2000–1500 BC）；朝鲜若干早期遗址（Gahyeon-ri, Seongjeo, Daechon-ri）比模型**更早**；北印度部分遗址可能比模型早**多达 3000 年**。（Silva, Stevens, Weisskopf, Castillo, Qin, Bevan et al. 2015, *PLOS ONE* 10:e0137024，**全文已读**）
- **小麦入华**：Long, Leipe, Jin, Wagner, Guo, Schröder et al. 2018, "The early history of wheat in China from ¹⁴C dating and Bayesian chronological modelling", *Nature Plants* 4:272–279, DOI 10.1038/s41477-018-0141-x（**元数据已核验；摘要与年代数值本次未能获取**）。⚠️ 具体年代我不给数字。
- **中亚走廊**：Stevens, Murphy, Roberts, Lucas, Silva & Fuller 2016, "Between China and South Asia: A Middle Asian corridor of crop dispersal and agricultural innovation in the Bronze Age", *The Holocene* 26:1541–1555, DOI 10.1177/0959683616650268（元数据已核验，OA 可得，正文本次未读）。
- **东亚农业扩散综述**：Stevens & Fuller 2017, "The spread of agriculture in eastern Asia: Archaeological bases for hypothetical farmer/language dispersals", *Language Dynamics and Change* 7:152–186, DOI 10.1163/22105832-00702001（元数据已核验；Brill 服务器拒绝连接，**正文未读**）。
- **长江下游稻作与劳动投入**：Fuller & Qin 2009, "Water management and labour in the origins and dispersal of Asian rice", *World Archaeology* 41:88–111, DOI 10.1080/00438240802668321（元数据已核验）；Fuller, Harvey & Qin 2007, *Antiquity* 81:316–331（元数据已核验）；Fuller & Qin 2010, *Environmental Archaeology* 15:139–159（元数据已核验）。
- **稻作遗传与考古的整合**：Fuller, Sato, Castillo, Qin, Weisskopf, Kingwell-Banham et al. 2010, *Archaeological and Anthropological Sciences* 2:115–131, DOI 10.1007/s12520-010-0035-y（元数据已核验）。

### 6.2 气候作为技术采纳的硬约束（东亚特有的强机制）
d'Alpoim Guedes & Bocinsky 2018, "Climate change stimulated agricultural innovation and exchange across Asia", *Science Advances* 4, DOI 10.1126/sciadv.aar4491（**PMC 全文已读**）：
- 建模 **6 种作物**（小麦、大麦、粟、黍、荞麦、水稻）的热量生态位，按年积温（GDD）阈值切分。**Table S1 列出各作物热量需求，但本次未能取到具体数值** —— 因此我**不给 GDD 数字**。
- 分辨率：ETOPO5 **5 弧分（约 10 km）**高程模型；用 GHCN 台站的现代日温度 + 全新世温度重建。
- **3750–3000 cal BP 的降温**导致青藏高原部分地区与中亚人群**作物多样化**。
- **约 2000 cal BP 的事件**造成"六种作物的作物生态位发生最大变化"。
- **1690 cal BP（260 CE）**温度最低点时，"几乎整个相当于蒙古的地区落到热量生态位之外"。
- 回报更差的地区，人们转向游牧与长距离贸易来分散风险。

> 工程含义（对本项目极重要）：在东亚，**气候变化不是背景噪声，而是直接改写"哪些配方在哪里可行"的算子**。M6 Layer 2 里的"本地相对优势"必须是气候的函数，而不是常数。这让"某项技术在某地被放弃/被引入"天然带有可追溯的气候原因。

### 6.3 语言—农业—人群三角
- **汉藏语系**：Sagart, Jacques, Lai, Ryder, Thouzeau, Greenhill et al. 2019, "Dated language phylogenies shed light on the ancestry of Sino-Tibetan", *PNAS* 116:10317–10322, DOI 10.1073/pnas.1817972116（元数据已核验）。
- **泛欧亚语系**：Robbeets et al. 2021, "Triangulation supports agricultural spread of the Transeurasian languages", *Nature*, DOI 10.1038/s41586-021-04108-8（**摘要已核验**）：整合语言学 + 考古（**255 个东北亚新石器—青铜时代遗址数据库**）+ 古基因组（韩国、琉球、日本早期谷物农人）。结论：泛欧亚语（日语、朝鲜语、通古斯、蒙古、突厥）的共同祖先与初次扩散可追溯到新石器早期以来在东北亚移动的**第一批农人**（挑战传统"游牧民假说"）；但这一共同遗产自青铜时代起被大量文化互动掩盖。
- **农业—语言扩散总纲**：Diamond & Bellwood 2003, "Farmers and Their Languages: The First Expansions", *Science* 300:597–603, DOI 10.1126/science.1078208（元数据已核验）。
- **与 M7 的对接**：Ackland 的"文化搭便车 + 独立采纳导致解耦"机制，正好能在模拟里**内生地**产生这种"语系边界 ≈ 农业波前边界，但被后来的互动掩盖"的模式。

### 6.4 冶金：中国参与欧亚青铜网络
- Mei Jianjun 2003, "Cultural Interaction between China and Central Asia during the Bronze Age", *Proceedings of the British Academy* 121, DOI 10.5871/bacad/9780197263037.003.0001（**元数据已核验，正文未读**）。
- Linduff & Mei 2009, "Metallurgy in Ancient Eastern Asia: Retrospect and Prospects", *Journal of World Prehistory* 22:265–281, DOI 10.1007/s10963-009-9023-5（元数据已核验；非 OA，**摘要与正文均未取得**）；2014 年有同名章节收入 *Archaeometallurgy in Global Perspective*, DOI 10.1007/978-1-4614-9017-3_27。
- Jaang Li 2015, "The Landscape of China's Participation in the Bronze Age Eurasian Network", *Journal of World Prehistory* 28:179–213, DOI 10.1007/s10963-015-9088-2（元数据已核验；非 OA，**摘要未取得**）。
- 欧亚冶金总纲：Roberts, Thornton & Pigott 2009, "Development of metallurgy in Eurasia", *Antiquity* 83:1012–1022, DOI 10.1017/s0003598x00099312（元数据已核验）。
- ⚠️ **"青铜冶金约公元前 2000 年经西北（齐家/新疆）传入中原"这一常见表述，我本次没有读到任何原文支撑，标为 recalled_not_verified / C 级。**

### 6.5 冶铁：中国的独特路径（生铁优先）
- Wagner, D.B. 1993, *Iron and Steel in Ancient China*, DOI 10.1163/9789004484115（**元数据已核验**，含章节 "The Earliest Evidence of the Use of Iron in China" DOI 10.1163/9789004484115_005）。
- Wagner 2008, *Ferrous Metallurgy*（Needham, *Science and Civilisation in China* 5(11)）——本次仅核验到书评（Souza 2013, *EASTM* 37:98–100, DOI 10.1163/26669323-03701010）与 Wagner 2020 自述（*Cultures of Science* 3:34–42, DOI 10.1177/2096608320915074）。
- 块炼铁的考古计量学个案：Liu Yaxiong, Tian Yaqi & Chen Kunlong 2024, *Archaeometry* 66:1050–1062, DOI 10.1111/arcm.12952（元数据已核验）——西汉早期雪池祭祀遗址的块炼铁冶炼证据。
- 广西东南部古代冶铁"从块炼铁到生铁"的空间分布：Liu Rongtian et al. 2026, *Land* 15:816, DOI 10.3390/land15050816（元数据已核验）。
- **宋代铁业规模**：Hartwell 1962, *J. Asian Studies* 21:153–162, DOI 10.2307/2050519；Hartwell 1966, *J. Economic History* 26:29–58, DOI 10.1017/s0022050700061842（**均元数据已核验，正文未读**）。Wagner 2001, "The administration of the iron industry in eleventh-century China", *JESHO* 44:175–197, DOI 10.1163/156852001753731033（元数据已核验）**对 Hartwell 的产量估计提出修正**。
  - ⚠️ **我不给宋代铁产量的具体吨数**——常被引用的数字来源有争议且我本次未读到原文。这是 §7 的一条争议。

### 6.6 战车与马镫（技术的军事—政治耦合）
- Shaughnessy 1988, "Historical Perspectives on the Introduction of the Chariot into China", *Harvard Journal of Asiatic Studies* 48:189, DOI 10.2307/2719276（**元数据已核验，正文未读**；2017 年重刊于 *Warfare in China to 1600*, DOI 10.4324/9781315234359-1）。
- Dien, A.E., "The Stirrup and its Effect on Chinese Military History"（**元数据已核验**，2017 年重刊于 *Warfare in China to 1600*, DOI 10.4324/9781315234359-9；原刊 *Ars Orientalis* 1986，本次未核验到原刊条目）。相关辩论见 Morillo, "War Horses and the Stirrup Thesis", *Oxford Research Encyclopedia of Military History*, DOI 10.1093/9780197852705.003.0055（元数据已核验）。
- Anthony, D.W., *The Horse, the Wheel, and Language*（元数据已核验，DOI 10.1515/9781400831104 等）。
- ⚠️ 具体年代（战车约公元前 1200 年出现于安阳；马镫约 4 世纪）为 **recalled_not_verified**。

### 6.7 知识传承制度：中国的 clan-based 路径
- 明清行会：学徒期**通常 3 年**，每作坊常**限 1 名学徒**；行会靠"把同业全纳入"来垄断而非排斥；不考核师傅资质；秘密行会被官府禁止（1867 苏州烟业、烛业案；1870 织锦工匠不得另立第二会）。（Moll-Murata 2008, *IRSH* 53:213–247，**PDF 全文已抽取**）
- 与欧洲对比：中国"training was provided by relatives, and hence a narrow group of experts"；欧洲师徒多无血缘、有 journeymanship 游历制。（de la Croix, Doepke & Mokyr，**NBER WP 22131 全文已读**，引 Moll-Murata 2013 p.234、van Zanden & Prak 2013a）
- 理论含义：在 M5 的 `h_L(m) = min{h_1..h_m}` 框架里，**clan 制度 = 小 `m` + 高同质性**。这**同时**意味着：(i) 平均技能水平较低；(ii) **对局部冲击更脆弱**（一个家族灭门 = 一门手艺消失）；(iii) 但**多样性可能更高**（对应 Derex & Boyd 2016 的"部分连通更好"）。**这三个后果不是同向的，所以不要预设 clan 一定劣于 guild。**
- "李约瑟之谜"的经济学表述：Lin, Justin Yifu 1995, "The Needham Puzzle: Why the Industrial Revolution Did Not Originate in China", *Economic Development and Cultural Change* 43:269–292, DOI 10.1086/452150（元数据已核验，正文未读）。Elvin 的"高水平均衡陷阱"见 *The Pattern of the Chinese Past*（本次仅核验到书评：Rawski 1976, DOI 10.2307/202386；Bays 1976, DOI 10.2307/492327）。Pomeranz, *The Great Divergence*, DOI 10.1515/9781400823499（元数据已核验）。

---

## 7. 学界争议与未解决问题

**7.1 人口规模是否驱动文化复杂度（最激烈的一条）**
- 支持：Henrich 2004；Powell et al. 2009；Kline & Boyd 2010；Derex et al. 2013；Muthukrishna et al. 2014。
- 反对：Read 2008；Collard et al. 2011/2013；Querbes et al. 2014（**换复杂度定义结论就变**）；Vaesen et al. 2016（**模型只在不合理条件下成立，且与考古/民族志证据冲突**）；Andersson & Read 2016。
- 回应：Henrich et al. 2016。
- **本项目立场**：这是 **C 级**。不要把 `人口 → 复杂度` 写成核心律。改用 (a) 专家人时预算 `B_k`、(b) 网络分割度的单峰效应（这条实验证据最稳）、(c) 载体数 `m`。

**7.2 网络连通度：越连通越好，还是中等分割最好？**
- Derex & Boyd 2016、Derex, Perreault & Boyd 2018 明确支持**中等分割最好**（全连通因趋同而丧失多样性）。这与"collective brain 越大越好"的直觉相反。目前实验证据倾向前者，但都是**实验室实验**，外推到千年尺度的真实社会**未被检验**。

**7.3 demic vs cultural 扩散的比例**
- Fort 2012 给出欧洲约 40% 文化 / 60% demic；但这是**大陆平均**，区域差异大（Fort 2015 做了区域分解，本次未读到数值）。东亚是否适用完全未知。

**7.4 扩散是波前还是跳跃？**
- 陶器最佳模型 r² 仅 0.36；粟黍在东亚是**明确不连续的**（相邻区间隔约 1200 年）；水稻是"先极慢后加速"的幂律而非线性。**"恒速波前"很可能是一个方法学产物**（回归模型本身假设了线性）。Ammerman 2021 在 *Radiocarbon* 63:741–749（DOI 10.1017/rdc.2021.2，元数据已核验）重新讨论了扩散速率的测量问题。

**7.5 累积文化演化是否需要因果理解？**
- Derex et al. 2019 (*Nat. Hum. Behav.*) 说**不需要**——纯选择性复制即可改良技术，且不产生对应理解。这挑战了"科学驱动技术"的默认叙事，也支持 Mokyr 的"窄 epistemic base 技术照样能存在"。

**7.6 行会：促进还是阻碍技术进步？**
- Epstein 1998 认为行会通过执行学徒契约、克服人力资本外部性而**促进**技术传播；Ogilvie（2014, 2016，转引自 de la Croix et al.）认为行会**阻碍**。de la Croix 等自己引 van Zanden & Prak 的话："contrasting the guild rehabilitationist and the guild-critical positions is difficult to defend… we find arguments supporting both propositions."
- **本项目应把行会做成参数化的两面刃**：提高 `m`（跨家族学习）但也提高 `θ`（采纳阈值，保密与排他）。

**7.7 中国前工业技术水平的量化**
- Hartwell 的宋代铁产量估计被 Wagner 2001 修正，量级仍有争议。**任何把"宋代铁产量"当硬数字用的做法都要打问号。**

**7.8 Tasmania 案例本身**
- 骨器消失究竟是"人口下降导致复杂度回退"（Henrich）还是"因为骨器并不更复杂、退出有其他原因"（Vaesen et al.），未决。⚠️ **不要把 Tasmania 当成失传机制的证明**，只当成一个待解释的案例。

**7.9 复杂度的定义**
- Querbes et al. 2014 表明"复杂度"的操作化选择直接决定人口—复杂度关系是否成立，而现有证据不足以判定哪个定义正确。**我们的 sim 必须自己明确定义复杂度（建议用 `d*` + `c`），并接受它是一个建模选择而非发现。**

---

## 8. 反模式：本领域常见的错误建模方式（我们必须避免的）

**AP1｜固定科技树 / 线性阶段论。**
错在哪：预设了"必须先 A 后 B"的唯一路径，杀死涌现，且让"平行技术传统"不可能。
证据反驳：Youn et al. 2015 显示发明是**任意代码的组合**，且组合空间"实际上无限"，已实现的只是极小子集；Fink & Reeves 2019 显示可造空间只由**组件基数与复杂度分布**决定，不由预设顺序决定。
正确做法：M1 的能力—配方图，前置边**在运行时生成**。

**AP2｜把纯组合动力学直接当内核。**
错在哪：**数学上必然爆炸或灭绝**（Steel/Hordijk/Kauffman 2020 定理 2），不存在几千年的平稳中间态；Solé et al. 2016 给出显式有限时间奇点 `t_s = 1/(μN_0)+t_0`。
正确做法：加三重封顶 —— (i) 专家人时预算 `B_k`（能源/粮食剩余约束）；(ii) 材料与组织的硬前置；(iii) **指数型**淘汰核（Solé et al. 2016 证明指数老化不产生奇点，幂律老化仍会）。

**AP3｜用人口标量单调驱动技术。**
错在哪：Kremer 式 `Λ ∝ N` 会产生单调加速，永远不会停滞或倒退；且人口—复杂度关系本身是 C 级争议（§7.1）。
正确做法：用 `B_k`（专家人时）+ 网络分割度的**单峰**函数（Derex & Boyd 2016）。

**AP4｜用 Bass/Rogers 的 S 曲线当生成机制。**
错在哪：S 曲线是**结果形状**，其内部的 `p, q` 是拟合出来的黑箱，不含"为什么这个村子采纳了而那个没有"的信息，无法支撑因果链。而且技术采纳大多是 **complex contagion**（需社会强化 + 隐性知识），simple contagion 的传染模型会高估长距离弱连接的作用。
正确做法：M6 三层管线；把 S 曲线留作**事后检验**（如果我们的机制自然产生 S 形，说明对了）。

**AP5｜确定性波前（reaction–diffusion 直接当扩散规则）。**
错在哪：最好的经验模型（含地形、生物群区走廊、双起源、自由拟合的 5×/7× 加速）也只解释 **36%** 的到达时间方差（Jordan et al. 2016）。东亚粟黍是明确不连续的，相邻区平均间隔 1200 年（Leipe et al. 2019）。
正确做法：把波前当**期望值**，实际到达用**大方差的随机过程**；显式建模"停滞"（一项技术可以在边界上卡几百年，直到某个具体事件打破）。

**AP6｜技术只进不退。**
错在哪：CF 模型里 `μ = 0` 就必然爆炸；现实中失传是常态。
正确做法：M5 四通道，且**载体、组织、原料、需求都是失传的独立触发器**。

**AP7｜把 learning curve 当外挂的经验曲线。**
错在哪：`α` 是拟合参数，无解释力，无法回答"为什么停滞"。
正确做法：`α = 1/(γ d*)`（McNerney et al. 2011），从配方的组件依赖图上算出来，并让**瓶颈组件**成为叙事钩子。

**AP8｜隐性知识可以被文本完美传递。**
错在哪：若 `tacit_fraction` 不进模型，"抢工匠""留学""逆向工程失败"这些真实的历史动力全部消失，技术会随书本瞬间扩散。
正确做法：`tacit_fraction > τ_crit` 时，**没有人的物理迁移就不可能实施**。参考 MacKenzie & Spinardi 1995 关于武器设计"uninvention"的论点（元数据已核验）。

**AP9｜复制误差不加纠错机制。**
错在哪：纯 ACE 模型（`X_n = X_0 Π ε_i`）预测**不到 200 代** CV 就超过 0.30，但实测手斧跨 1.2 百万年 CV 仍只有 0.30/0.23（Kempe, Lycett & Mesoudi 2012）。放任漂移会让技术在几十代内变成噪声。
正确做法：加师傅纠错（`h_L(m) = min{...}` 天然是一种纠错）、模板/模具（codified_in）、以及功能选择压力。

**AP10｜把真实历史的技术序列当靶子。**
错在哪：违反项目纲领第 8 条。
正确做法：靶子应该是**统计性质**：技术组合的低维结构（Seshat 单主成分解释约 3/4 方差）、扩散速率的量级（0.2–3.3 km/yr）、扩散的低可预测性（r² ≤ 0.36）、探索/利用比（≈0.6/0.4）、失传的存在性与频度。

**AP11｜让 LLM 决定"某项技术是否被发明出来"。**
错在哪：LLM 会为了戏剧性在关键时刻发明关键技术。
正确做法：LLM 只能 (i) 命名、(ii) 生成世界内的解释与传说、(iii) 在**规则给出的可行集**里替 agent 做选择。发明**是否**发生、性能是多少、能否传播成功，全部由 `rules_math` 决定并记录随机种子。

**AP12｜把"缺乏证据"当成"证据表明没有"。**
错在哪：Silva et al. 2015 的模型预测日本水稻比考古证据早 1500–2000 年，北印度遗址比模型早多达 3000 年 —— 考古的"首次出现"是**采样下界**。
正确做法：模拟内部保存"世界事实"的真实首次出现时间，同时保存"世界内考古学家能观察到的"版本（纲领第 9 条）。这两者的系统性偏差本身就是一个可研究的现象。

---

## 9. 无来源判断（D 级，明确标记为 LLM 常识，不得当作历史规律）

以下均为**我为了让模拟能跑而做的假设**，没有文献支撑：

1. **`Λ_demand` 应占总发明强度的 30–50%。**纯属为了在"需求驱动"与"偶然驱动"之间取平衡而设的数字。
2. **能力层与配方层的速率比 `ρ_c / ρ_rec ≈ 10⁻²–10⁻³`。**Youn et al. 只说"新能力引入显著放缓"，没有给比值。
3. **`τ_crit = 0.5`（隐性知识占比超过此值则必须有人迁移）。**完全是猜的。
4. **前工业手工业的成本改善率 `μ ∈ [−0.02, −0.001]/yr`。**由 Farmer & Lafond 表中最慢的几项（Milk −0.02、Sodium −0.01、Electric Range −0.02）向下外推。**没有任何前工业学习曲线的实证数据。**
5. **复制误差 `σ_ε ≈ 0.03` 适用于所有工艺参数。**Weber fraction 3% 是**视觉长度感知**的阈值，把它套到火候、配比、时序上是无根据的类比。
6. **组件复杂度均值 `c̄` 随文明阶段从 2 涨到 8+。**Fink & Reeves 用 `c̄ = 8` 作示例，与史前无关。
7. **`base_width` 对搜索命中率的具体加成函数形式。**Mokyr 的机制是定性的。
8. **"clan 制度 = 小 m + 高同质性 + 高脆弱性 + 可能更高多样性"这四条后果的相对权重。**推理是合理的，但没有量化研究。
9. **成本面网格 5–10 km 是合适的空间粒度。**借自 d'Alpoim Guedes & Bocinsky 用的 ETOPO5，但那是作物生态位建模，不是技术扩散。
10. **"成品可见但过程不可见 → 先扩散需求再扩散能力"这一机制。**逻辑上说得通，我没有找到对它的实证检验。
11. **失传后重发明的成本 = `tacit_fraction × 原始成本`。**函数形式是我编的。
12. **Bettencourt 的 β = 1.27 可外推到古代城市。**这是**现代美国都市区**的专利数据。古代不存在专利，"发明产出"无法测量。**这条外推很可能是错的**，只是我们没有更好的东西。
13. **"技术采纳几乎全部是 complex contagion"。**Centola & Macy 的实证在现代在线网络与健康行为；把它推广到古代技术是我的判断。
14. **青铜冶金约公元前 2000 年经西北传入中原、战车约公元前 1200 年出现于安阳、马镫约 4 世纪。**这些是我记忆中的常见年代，本次检索**没有读到任何原文支撑**（相关文献均被付费墙拦截）。**在下一阶段核验前不得写入任何参数文件。**
15. **宋代铁产量的任何具体数字。**我拒绝给出——Hartwell 的估计被 Wagner 2001 修正，我没读到任何一方的原文。

---

## 10. 参考文献

**标记说明**：【核】= 本次通过 Crossref / Semantic Scholar / Europe PMC 实际返回元数据；【文】= 本次实际读到正文或 PDF 抽取文本；【记】= 凭记忆写下，本次未核验。

### 组合演化与创新的形式化
1. 【核】Arthur, W.B. & Polak, W. (2006). "The evolution of technology within a simple computer model." *Complexity* 11:23–31. DOI 10.1002/cplx.20130.（正文付费墙未读） **[已核验]**
2. 【记】Arthur, W.B. (2009). *The Nature of Technology: What It Is and How It Evolves.* Free Press.（本次仅核验到书评：Bueno 2010 DOI 10.20396/rbi.v8i2.8648990；Ozman 2012 DOI 10.1007/s10710-012-9158-5）
3. 【核】【文】Youn, H., Strumsky, D., Bettencourt, L.M.A. & Lobo, J. (2015). "Invention as a combinatorial process: evidence from US patents." *J. R. Soc. Interface* 12:20150272. DOI 10.1098/rsif.2015.0272. PMC4424706. **[已核验]**
4. 【核】【文】Steel, M., Hordijk, W. & Kauffman, S.A. (2020). "Dynamics of a birth–death process based on combinatorial innovation." *J. Theor. Biol.* 491:110187. DOI 10.1016/j.jtbi.2020.110187.（arXiv:1904.03290 全文已抽取） **[已核验]**
5. 【核】【文】Solé, R., Amor, D.R. & Valverde, S. (2016). "On Singularities and Black Holes in Combination-Driven Models of Technological Innovation Networks." *PLOS ONE* 11:e0146180. DOI 10.1371/journal.pone.0146180. **[已核验]**
6. 【核】【文】Fink, T.M.A. & Reeves, M. (2019). "How much can we influence the rate of innovation?" *Science Advances* 5. DOI 10.1126/sciadv.aat6107. PMC6326754. **[已核验]**
7. 【核】Fink, T.M.A., Reeves, M., Palma, R. & Farr, R.S. (2017). "Serendipity and strategy in rapid innovation." *Nature Communications* 8. DOI 10.1038/s41467-017-02042-w. PMC5722871.
8. 【核】Tria, F., Loreto, V., Servedio, V.D.P. & Strogatz, S.H. (2014). "The dynamics of correlated novelties." *Scientific Reports* 4. DOI 10.1038/srep05890. PMC5376195.（注：Crossref 返回的第四作者是 **Strogatz**，非我记忆中的 Strumsky）
9. 【核】Solé, R.V., Valverde, S., Rosas Casals, M., Kauffman, S.A., Farmer, D. & Eldredge, N. (2013). "The evolutionary ecology of technological innovations." *Complexity* 18:15–27. DOI 10.1002/cplx.21436.
10. 【核】Valverde, S. (2016). "Major transitions in information technology." *Phil. Trans. R. Soc. B* 371:20150450. DOI 10.1098/rstb.2015.0450.
11. 【核】Koppl, R., Cazzolla Gatti, R., Devereaux, A., Fath, B.D., Herriot, J., Hordijk, W. et al. (2023). *Explaining Technology.* Cambridge University Press. DOI 10.1017/9781009386289.
12. 【核】Hidalgo, C.A., Klinger, B., Barabási, A.-L. & Hausmann, R. (2007). "The Product Space Conditions the Development of Nations." *Science* 317:482–487. DOI 10.1126/science.1144581.
13. 【核】Hidalgo, C.A., Balland, P.-A., Boschma, R., Delgado, M., Feldman, M., Frenken, K. et al. (2018). "The Principle of Relatedness." *Springer Proceedings in Complexity*:451–457. DOI 10.1007/978-3-319-96661-8_46.

### 知识、学习曲线与技术改良
14. 【核】Mokyr, J. *The Gifts of Athena: Historical Origins of the Knowledge Economy.* DOI 10.1515/9781400829439.（全书章节目录已核验；Ω/λ 与 epistemic base 的定义**未读到原文**） **[已核验]**
15. 【核】Mokyr, J. (2000). "Knowledge, Technology, and Economic Growth during the Industrial Revolution." In *Productivity, Technology and Economic Growth*:253–292. DOI 10.1007/978-1-4757-3161-3_9.
16. 【核】Wright, T.P. (1936). "Factors Affecting the Cost of Airplanes." *J. Aeronautical Sciences* 3:122–128. DOI 10.2514/8.155.
17. 【核】Argote, L. & Epple, D. (1990). "Learning Curves in Manufacturing." *Science* 247:920–924. DOI 10.1126/science.247.4945.920.
18. 【核】【文】McNerney, J., Farmer, J.D., Redner, S. & Trancik, J.E. (2011). "Role of design complexity in technology improvement." *PNAS* 108:9008–9013. DOI 10.1073/pnas.1017298108. PMC3107265. **[已核验]**
19. 【核】【文】Nagy, B., Farmer, J.D., Bui, Q.M. & Trancik, J.E. (2013). "Statistical Basis for Predicting Technological Progress." *PLoS ONE* 8:e52669. DOI 10.1371/journal.pone.0052669.
20. 【核】【文】Farmer, J.D. & Lafond, F. (2016). "How predictable is technological progress?" *Research Policy* 45:647–665. DOI 10.1016/j.respol.2015.11.001.（arXiv:1502.05274 全文 PDF 已抽取，含完整参数表） **[已核验]**
21. 【核】【文】Bettencourt, L.M.A., Lobo, J., Helbing, D., Kühnert, C. & West, G.B. (2007). "Growth, innovation, scaling, and the pace of life in cities." *PNAS* 104:7301–7306. DOI 10.1073/pnas.0610172104.
22. 【核】Bettencourt, L.M.A., Lobo, J., Strumsky, D. & West, G.B. (2010). "Urban Scaling and Its Deviations." *PLoS ONE* 5:e13541. DOI 10.1371/journal.pone.0013541.
23. 【核】Kremer, M. (1993). "Population Growth and Technological Change: One Million B.C. to 1990." *QJE*. DOI 10.2307/2118405.
24. 【核】Jones, C.I. (2001). "Was an Industrial Revolution Inevitable? Economic Growth Over the Very Long Run." *B.E. Journal of Macroeconomics* 1. DOI 10.2202/1534-6013.1028.

### 累积文化演化、人口与网络
25. 【核】Henrich, J. (2004). "Demography and Cultural Evolution: How Adaptive Cultural Processes Can Produce Maladaptive Losses—The Tasmanian Case." *American Antiquity* 69:197–214. DOI 10.2307/4128416.
26. 【核】Powell, A., Shennan, S. & Thomas, M.G. (2009). "Late Pleistocene Demography and the Appearance of Modern Human Behavior." *Science* 324:1298–1301. DOI 10.1126/science.1170165.
27. 【核】【文】Vaesen, K., Collard, M., Cosgrove, R. & Roebroeks, W. (2016). "Population size does not explain past changes in cultural complexity." *PNAS* 113. DOI 10.1073/pnas.1520288113. PMC4843435. **[已核验]**
28. 【核】Henrich, J., Boyd, R., Derex, M., Kline, M.A., Mesoudi, A. & Muthukrishna, M. (2016). "Understanding cumulative cultural evolution." *PNAS* 113. DOI 10.1073/pnas.1610005113.
29. 【核】Read, D. (2008). "An Interaction Model for Resource Implement Complexity Based on Risk and Number of Annual Moves." *American Antiquity* 73:599–625. DOI 10.1017/s0002731600047326.
30. 【核】Andersson, C. & Read, D. (2016). "The Evolution of Cultural Complexity: Not by the Treadmill Alone." *Current Anthropology* 57:261–286. DOI 10.1086/686317.
31. 【核】【文】Querbes, A., Vaesen, K. & Houkes, W. (2014). "Complexity and Demographic Explanations of Cumulative Culture." *PLoS ONE* 9:e102543. DOI 10.1371/journal.pone.0102543.
32. 【核】Kline, M.A. & Boyd, R. (2010). "Population size predicts technological complexity in Oceania." *Proc. R. Soc. B* 277:2559–2564. DOI 10.1098/rspb.2010.0452.
33. 【核】Collard, M., Ruttle, A., Buchanan, B. & O'Brien, M.J. (2013). "Population Size and Cultural Evolution in Nonindustrial Food-Producing Societies." *PLoS ONE* 8:e72628. DOI 10.1371/journal.pone.0072628.
34. 【核】Derex, M., Beugin, M.-P., Godelle, B. & Raymond, M. (2013). "Experimental evidence for the influence of group size on cultural complexity." *Nature* 503:389–391. DOI 10.1038/nature12774.
35. 【核】【文】Derex, M. & Boyd, R. (2016). "Partial connectivity increases cultural accumulation within groups." *PNAS* 113:2982–2987. DOI 10.1073/pnas.1518798113. **[已核验]**
36. 【核】Derex, M., Perreault, C. & Boyd, R. (2018). "Divide and conquer: intermediate levels of population fragmentation maximize cultural accumulation." *Phil. Trans. R. Soc. B* 373:20170062. DOI 10.1098/rstb.2017.0062.
37. 【核】Derex, M., Bonnefon, J.-F., Boyd, R. & Mesoudi, A. (2019). "Causal understanding is not necessary for the improvement of culturally evolving technology." *Nature Human Behaviour* 3:446–452. DOI 10.1038/s41562-019-0567-9. **[已核验]**
38. 【核】【文】Muthukrishna, M., Shulman, B.W., Vasilescu, V. & Henrich, J. (2014). "Sociality influences cultural complexity." *Proc. R. Soc. B* 281:20132511. DOI 10.1098/rspb.2013.2511.
39. 【核】【文】Muthukrishna, M. & Henrich, J. (2016). "Innovation in the collective brain." *Phil. Trans. R. Soc. B* 371:20150192. DOI 10.1098/rstb.2015.0192.
40. 【核】Kempe, M. & Mesoudi, A. (2014). "An experimental demonstration of the effect of group size on cultural accumulation." *Evolution and Human Behavior* 35:285–290. DOI 10.1016/j.evolhumbehav.2014.02.009.
41. 【核】【文】Kempe, M., Lycett, S. & Mesoudi, A. (2012). "An Experimental Test of the Accumulated Copying Error Model of Cultural Mutation for Acheulean Handaxe Size." *PLoS ONE* 7:e48333. DOI 10.1371/journal.pone.0048333.
42. 【核】Eerkens, J.W. (2000). "Practice Makes Within 5% of Perfect: Visual Perception, Motor Skills, and Memory in Artifact Variation." *Current Anthropology* 41:663–668. DOI 10.1086/317394.
43. 【核】Eerkens, J.W. & Lipo, C.P. (2005). "Cultural transmission, copying errors, and the generation of variation in material culture and the archaeological record." *J. Anthropological Archaeology* 24:316–334. DOI 10.1016/j.jaa.2005.08.001.
44. 【核】Aoki, K., Lehmann, L. & Feldman, M.W. (2011). "Rates of cultural change and patterns of cultural accumulation in stochastic models of social transmission." *Theoretical Population Biology* 79:192–202. DOI 10.1016/j.tpb.2011.02.001.
45. 【核】Strimling, P., Sjöstrand, J., Enquist, M. & Eriksson, K. (2009). "Accumulation of independent cultural traits." *Theoretical Population Biology* 76:77–83. DOI 10.1016/j.tpb.2009.04.006.
46. 【核】Enquist, M., Ghirlanda, S. & Eriksson, K. (2011). "Modelling the evolution and diversity of cumulative culture." *Phil. Trans. R. Soc. B* 366:412–423. DOI 10.1098/rstb.2010.0132.
47. 【核】Lewis, H.M. & Laland, K.N. (2012). "Transmission fidelity is the key to the build-up of cumulative culture." *Phil. Trans. R. Soc. B* 367:2171–2180. DOI 10.1098/rstb.2012.0119.
48. 【核】Mesoudi, A. & Thornton, A. (2018). "What is cumulative cultural evolution?" *Proc. R. Soc. B* 285:20180712. DOI 10.1098/rspb.2018.0712.
49. 【核】Dean, L.G., Kendal, R.L., Schapiro, S.J., Thierry, B. & Laland, K.N. (2012). "Identification of the Social and Cognitive Processes Underlying Human Cumulative Culture." *Science* 335:1114–1118. DOI 10.1126/science.1213969.
50. 【核】Crema, E.R., Kandler, A. & Shennan, S. (2016). "Revealing patterns of cultural transmission from frequency data: equilibrium and non-equilibrium assumptions." *Scientific Reports* 6. DOI 10.1038/srep39122.
51. 【核】Kandler, A., Wilder, B. & Fortunato, L. (2017). "Inferring individual-level processes from population-level patterns in cultural evolution." *Royal Society Open Science* 4:170949. DOI 10.1098/rsos.170949.

### 扩散：模型与考古测量
52. 【核】Ammerman, A.J. & Cavalli-Sforza, L.L. (1971). "Measuring the Rate of Spread of Early Farming in Europe." *Man* 6:674. DOI 10.2307/2799190.
53. 【核】Ammerman, A.J. & Cavalli-Sforza, L.L. (1984). *The Neolithic Transition and the Genetics of Populations in Europe.* DOI 10.1515/9781400853113.
54. 【核】【文】Pinhasi, R., Fort, J. & Ammerman, A.J. (2005). "Tracing the Origin and Spread of Agriculture in Europe." *PLoS Biology* 3:e410. DOI 10.1371/journal.pbio.0030410. **[已核验]**
55. 【核】【文】Fort, J. (2012). "Synthesis between demic and cultural diffusion in the Neolithic transition in Europe." *PNAS* 109:18669–18673. DOI 10.1073/pnas.1200662109. PMC3503213.
56. 【核】Fort, J. (2015). "Demic and cultural diffusion propagated the Neolithic transition across different regions of Europe." *J. R. Soc. Interface* 12:20150166. DOI 10.1098/rsif.2015.0166.（正文 403 未读）
57. 【核】Fort, J. (2022). "Dispersal distances and cultural effects in the spread of the Neolithic along the northern Mediterranean coast." *Archaeol. Anthropol. Sci.* 14. DOI 10.1007/s12520-022-01619-x.（正文被拦截未读）
58. 【核】Fort, J., Jana, D. & Humet, J. (2004). "Multidelayed random walks: Theory and application to the Neolithic transition in Europe." *Physical Review E* 70. DOI 10.1103/physreve.70.031913.
59. 【核】Fort, J., Pujol, T. & Cavalli-Sforza, L.L. (2004). "Palaeolithic Populations and Waves of Advance." *Cambridge Archaeological Journal* 14:53–61. DOI 10.1017/s0959774304000046.
60. 【核】【文】Ackland, G.J., Signitzer, M., Stratford, K. & Cohen, M.H. (2007). "Cultural hitchhiking on the wave of advance of beneficial technologies." *PNAS* 104:8714–8719. DOI 10.1073/pnas.0702469104. PMC1885568. **[已核验]**
61. 【核】Silva, F. & Steele, J. (2014). "New methods for reconstructing geographical effects on dispersal rates and routes from large-scale radiocarbon databases." *J. Archaeological Science* 52:609–620. DOI 10.1016/j.jas.2014.04.021.（PDF 403 未读）
62. 【核】【文】Silva, F., Steele, J., Gibbs, K. & Jordan, P. (2014). "Modeling Spatial Innovation Diffusion from Radiocarbon Dates and Regression Residuals: The Case of Early Old World Pottery." *Radiocarbon* 56:723–732. DOI 10.2458/56.16937.
63. 【核】【文】Jordan, P., Gibbs, K., Hommel, P., Piezonka, H., Silva, F. & Steele, J. (2016). "Modelling the diffusion of pottery technologies across Afro-Eurasia: emerging insights and future research." *Antiquity* 90:590–603. DOI 10.15184/aqy.2016.68. **[已核验]**
64. 【核】Ammerman, A.J. (2021). "Returning to the Rate of Spread of Early Farming in Europe: Comment on the Article by Manen et al. (2019)." *Radiocarbon* 63:741–749. DOI 10.1017/rdc.2021.2.
65. 【核】Bass, F.M. (1969). "A New Product Growth for Model Consumer Durables." *Management Science* 15:215–227. DOI 10.1287/mnsc.15.5.215.
66. 【核】Bass, F.M. (2004). "Comments on 'A New Product Growth for Model Consumer Durables: The Bass Model.'" *Management Science* 50:1833–1840. DOI 10.1287/mnsc.1040.0300.
67. 【核·书目】Rogers, E.M. (1962; 5th ed. 2003). *Diffusion of Innovations.* New York: Free Press. **[已核验]**（书籍无 Crossref DOI；本次 OpenLibrary 查询受网络限制未能返回，条目依据该书公认的出版事实确认，非本会话在线检索所得）
68. 【核】Granovetter, M. (1978). "Threshold Models of Collective Behavior." *AJS* 83:1420–1443. DOI 10.1086/226707.
69. 【核】Centola, D. & Macy, M. (2007). "Complex Contagions and the Weakness of Long Ties." *AJS* 113:702–734. DOI 10.1086/521848.（正文付费墙未读）
70. 【核】Centola, D. (2010). "The Spread of Behavior in an Online Social Network Experiment." *Science* 329:1194–1197. DOI 10.1126/science.1185231.
71. 【核】Griliches, Z. (1957). "Hybrid Corn: An Exploration in the Economics of Technological Change." *Econometrica* 25:501. DOI 10.2307/1905380.
72. 【核】Comin, D. & Hobijn, B. (2010). "An Exploration of Technology Diffusion." *American Economic Review* 100:2031–2059. DOI 10.1257/aer.100.5.2031.
73. 【核】【文】Comin, D. & Mestieri, M. (2018). "If Technology Has Arrived Everywhere, Why Has Income Diverged?" *AEJ: Macroeconomics* 10:137–178. DOI 10.1257/mac.20150175.（NBER WP 19010 全文已抽取）
74. 【核】【文】Comin, D., Easterly, W. & Gong, E. (2006). "Was the Wealth of Nations Determined in 1000 B.C.?" NBER WP 12657. DOI 10.3386/w12657.（全文已抽取）

### 制度、隐性知识与技术保密
75. 【核】【文】de la Croix, D., Doepke, M. & Mokyr, J. (2018). "Clans, Guilds, and Markets: Apprenticeship Institutions and Growth in the Preindustrial Economy." *QJE* 133:1–70. DOI 10.1093/qje/qjx026.（NBER WP 22131 全文已抽取） **[已核验]**
76. 【核】Epstein, S.R. (1998). "Craft Guilds, Apprenticeship, and Technological Change in Preindustrial Europe." *J. Economic History* 58:684–713. DOI 10.1017/s0022050700021124.（正文未读）
77. 【核】【文】Moll-Murata, C. (2008). "Chinese Guilds from the Seventeenth to the Twentieth Centuries: An Overview." *International Review of Social History* 53:213–247. DOI 10.1017/s0020859008003672. **[已核验]**
78. 【核】MacKenzie, D. & Spinardi, G. (1995). "Tacit Knowledge, Weapons Design, and the Uninvention of Nuclear Weapons." *AJS* 101:44–99. DOI 10.1086/230699.（正文付费墙未读） **[已核验]**
79. 【核】Lin, J.Y. (1995). "The Needham Puzzle: Why the Industrial Revolution Did Not Originate in China." *Economic Development and Cultural Change* 43:269–292. DOI 10.1086/452150.（正文未读）
80. 【核】Pomeranz, K. (2000). *The Great Divergence.* DOI 10.1515/9781400823499.
81. 【记】Elvin, M. (1973). *The Pattern of the Chinese Past.*（本次仅核验到书评：Rawski 1976 DOI 10.2307/202386；Bays 1976 DOI 10.2307/492327）

### 中国与东亚
82. 【核】【文】Leipe, C., Long, T., Sergusheva, E.A., Wagner, M. & Tarasov, P.E. (2019). "Discontinuous spread of millet agriculture in eastern Asia and prehistoric population dynamics." *Science Advances* 5. DOI 10.1126/sciadv.aax6225. PMC6760930. **[已核验]**
83. 【核】【文】Silva, F., Stevens, C.J., Weisskopf, A., Castillo, C., Qin, L., Bevan, A. et al. (2015). "Modelling the Geographical Origin of Rice Cultivation in Asia Using the Rice Archaeological Database." *PLOS ONE* 10:e0137024. DOI 10.1371/journal.pone.0137024.
84. 【核】【文】d'Alpoim Guedes, J. & Bocinsky, R.K. (2018). "Climate change stimulated agricultural innovation and exchange across Asia." *Science Advances* 4. DOI 10.1126/sciadv.aar4491. PMC6209390. **[已核验]**
85. 【核】Stevens, C.J. & Fuller, D.Q. (2017). "The spread of agriculture in eastern Asia: Archaeological bases for hypothetical farmer/language dispersals." *Language Dynamics and Change* 7:152–186. DOI 10.1163/22105832-00702001.（Brill 拒绝连接，正文未读）
86. 【核】Stevens, C.J., Murphy, C., Roberts, R., Lucas, L., Silva, F. & Fuller, D.Q. (2016). "Between China and South Asia: A Middle Asian corridor of crop dispersal and agricultural innovation in the Bronze Age." *The Holocene* 26:1541–1555. DOI 10.1177/0959683616650268.
87. 【核】Fuller, D.Q., Sato, Y.-I., Castillo, C., Qin, L., Weisskopf, A.R., Kingwell-Banham, E.J. et al. (2010). "Consilience of genetics and archaeobotany in the entangled history of rice." *Archaeological and Anthropological Sciences* 2:115–131. DOI 10.1007/s12520-010-0035-y.
88. 【核】Fuller, D.Q. & Qin, L. (2009). "Water management and labour in the origins and dispersal of Asian rice." *World Archaeology* 41:88–111. DOI 10.1080/00438240802668321.
89. 【核】Long, T., Leipe, C., Jin, G., Wagner, M., Guo, R., Schröder, O. et al. (2018). "The early history of wheat in China from ¹⁴C dating and Bayesian chronological modelling." *Nature Plants* 4:272–279. DOI 10.1038/s41477-018-0141-x.（摘要与数值未取得）
90. 【核】【文】Hosner, D., Wagner, M., Tarasov, P.E., Chen, X. & Leipe, C. (2016). "Spatiotemporal distribution patterns of archaeological sites in China during the Neolithic and Bronze Age: An overview." *The Holocene* 26:1576–1593. DOI 10.1177/0959683616641743.（配套数据集 DOI 10.1594/PANGAEA.860072 页面已核验）
91. 【核】Wagner, M., Tarasov, P., Hosner, D., Fleck, A., Ehrich, R. & Chen, X. (2013). "Mapping of the spatial and temporal distribution of archaeological sites of northern China during the Neolithic and Bronze Age." *Quaternary International* 290–291:344–357. DOI 10.1016/j.quaint.2012.06.039.
92. 【核】Sagart, L., Jacques, G., Lai, Y., Ryder, R.J., Thouzeau, V., Greenhill, S.J. et al. (2019). "Dated language phylogenies shed light on the ancestry of Sino-Tibetan." *PNAS* 116:10317–10322. DOI 10.1073/pnas.1817972116.
93. 【核】Robbeets, M. et al. (2021). "Triangulation supports agricultural spread of the Transeurasian languages." *Nature*. DOI 10.1038/s41586-021-04108-8.（摘要已核验）
94. 【核】Diamond, J. & Bellwood, P. (2003). "Farmers and Their Languages: The First Expansions." *Science* 300:597–603. DOI 10.1126/science.1078208.
95. 【核】Mei, J. (2003). "Cultural Interaction between China and Central Asia during the Bronze Age." *Proceedings of the British Academy* 121. DOI 10.5871/bacad/9780197263037.003.0001.（正文未读）
96. 【核】Linduff, K.M. & Mei, J. (2009). "Metallurgy in Ancient Eastern Asia: Retrospect and Prospects." *J. World Prehistory* 22:265–281. DOI 10.1007/s10963-009-9023-5.（摘要未取得）
97. 【核】Jaang, L. (2015). "The Landscape of China's Participation in the Bronze Age Eurasian Network." *J. World Prehistory* 28:179–213. DOI 10.1007/s10963-015-9088-2.（摘要未取得）
98. 【核】Roberts, B.W., Thornton, C. & Pigott, V.C. (2009). "Development of metallurgy in Eurasia." *Antiquity* 83:1012–1022. DOI 10.1017/s0003598x00099312.
99. 【核】Wagner, D.B. (1993). *Iron and Steel in Ancient China.* DOI 10.1163/9789004484115.
100. 【核】Wagner, D.B. (2001). "The Administration of the Iron Industry in Eleventh-Century China." *JESHO* 44:175–197. DOI 10.1163/156852001753731033.
101. 【核】Hartwell, R. (1962). "A Revolution in the Chinese Iron and Coal Industries During the Northern Sung, 960–1126 A.D." *J. Asian Studies* 21:153–162. DOI 10.2307/2050519.
102. 【核】Hartwell, R. (1966). "Markets, Technology, and the Structure of Enterprise in the Development of the Eleventh-Century Chinese Iron and Steel Industry." *J. Economic History* 26:29–58. DOI 10.1017/s0022050700061842.
103. 【核】Liu, Y., Tian, Y. & Chen, K. (2024). "Archaeometric study of the iron objects from the Xuechi sacrificial site…" *Archaeometry* 66:1050–1062. DOI 10.1111/arcm.12952.
104. 【核】Shaughnessy, E.L. (1988). "Historical Perspectives on the Introduction of the Chariot into China." *Harvard Journal of Asiatic Studies* 48:189. DOI 10.2307/2719276.（正文未读）
105. 【核】Dien, A.E. "The Stirrup and its Effect on Chinese Military History." In *Warfare in China to 1600*. DOI 10.4324/9781315234359-9.（正文未读；原刊 *Ars Orientalis* 1986 未核验）
106. 【核】Anthony, D.W. *The Horse, the Wheel, and Language.* DOI 10.1515/9781400831104.

### 数据库
107. 【核】Turchin, P., Currie, T.E., Whitehouse, H., François, P., Feeney, K., Mullins, D. et al. (2018). "Quantitative historical analysis uncovers a single dimension of complexity that structures global variation in human social organization." *PNAS* 115. DOI 10.1073/pnas.1708800115. PMC5777031.
108. 【核】Turchin, P. (2017). "Seshat: Global History Databank Publishes First Set of Historical Data." *Cliodynamics* 8. DOI 10.21237/c7clio8135421.（另：seshat-db.com 站点已抓取核验）
109. 【核】Kirby, K.R., Gray, R.D., Greenhill, S.J., Jordan, F.M., Gomes-Ng, S., Bibiko, H.-J. et al. (2016). "D-PLACE: A Global Database of Cultural, Linguistic and Environmental Diversity." *PLOS ONE* 11:e0158391. DOI 10.1371/journal.pone.0158391.（d-place.org 已抓取核验，CC BY-NC 4.0）
110. 【核】Bird, D., Miranda, L., Vander Linden, M., Robinson, E., Bocinsky, R.K., Nicholson, C. et al. (2022). "p3k14c, a synthetic global database of archaeological radiocarbon dates." *Scientific Data* 9. DOI 10.1038/s41597-022-01118-7.
111. 【核】Schmid, C., Seidensticker, D. & Hinz, M. (2019). "c14bazAAR: An R package for downloading and preparing C14 dates from different source databases." *JOSS* 4:1914. DOI 10.21105/joss.01914.
112. 【核】【数据集页已抓取】Hosner, D., Wagner, M., Tarasov, P.E., Chen, X. & Leipe, C. (2016). *Archaeological sites in China during the Neolithic and Bronze Age* [dataset]. PANGAEA. DOI 10.1594/PANGAEA.860072. **CC-BY-3.0**，51,074 遗址 / 411,456 数据点，73–131°E、20–53°N，约 8000–500 BC。
113. 【记】Peregrine, P.N. (2003). "Atlas of Cultural Evolution." In J.P. Gray (ed.), *World Cultures* 14(3):1–75.（转引自 Comin/Easterly/Gong NBER WP 12657 的参考文献，本次未独立核验）
114. 【核】Sun, T., Bol, P.K. & Zhang, X. "Advancing historical geography through the Chinese Historical Geographic Information System (CHGIS)." *J. Historical Geography*. DOI 10.1016/j.jhg.2026.06.018.

### 本次被付费墙 / 服务器拦截、未能读到正文的重要文献
Arthur & Polak 2006（Wiley）；MacKenzie & Spinardi 1995（UChicago Press）；Epstein 1998（CUP）；Centola & Macy 2007（UChicago Press）；Kline & Boyd 2010（Royal Society，PMC 非 OA）；Jaang 2015 与 Linduff & Mei 2009（Springer，连摘要都无）；Stevens & Fuller 2017（Brill，ECONNREFUSED）；Fort 2015（RSIF 403）与 Fort 2022（Springer IdP 重定向）；Silva & Steele 2014（Elsevier 403）；d'Alpoim Guedes & Bocinsky 2018 的 **Table S1（各作物 GDD 阈值）**；Long et al. 2018 摘要与年代；Hartwell 1962/1966 的产量数字。**这些缺口直接对应 §9 中若干 D 级判断，下一阶段应优先补齐。**
