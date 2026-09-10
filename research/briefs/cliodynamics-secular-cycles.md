# 历史动力学、长周期与结构-人口理论

- **slug**: `cliodynamics-secular-cycles`
- **一句话范围**: 把历史当作动力系统的定量传统（Cliodynamics / 结构-人口理论 / 世俗周期 / 朝代周期 / Seshat），评估其可信度，抽取可工程实现的机制与参数，并回答"如何让周期成为模拟的输出而不是输入"。
- **完成日期**: 2026-09-10
- **检索方式**: Crossref REST API（可用）、Europe PMC、PMC 全文、eScholarship（Cliodynamics 期刊全部开放获取）、OSF/SocArXiv 预印本、PLOS ONE、Springer 元数据、GitHub 源码。OpenAlex 与 Semantic Scholar 在本次会话中被限流（429），WebSearch 配额已耗尽；因此覆盖面偏向"开放获取 + Crossref 可检索"的文献，付费墙后的经济史论文（Chu & Lee 1994 全文、Bai & Kung 2011、Chen 2014、Zhang 2006/2007 全文）只取到摘要或元数据。详见 §10 的验证状态标注。

---

## 1. 本简报要回答的问题

1. **结构-人口理论（Structural-Demographic Theory, SDT）里哪些部分是"机制"，哪些只是"叙事"？** 哪些能写成微分方程/概率规则，哪些只是事后归因？
2. **如果我们把 Turchin 的周期机制直接写进内核，是否等于把"王朝兴衰"变成预设剧情？** 如何改写，使 200–300 年的兴衰节律成为**涌现结果**而非输入？
3. **有哪些真实可用的量化参数？**（承载力、增长率、精英比例、解体概率、危险率函数形状……）
4. **中国/东亚有哪些经过定量处理的证据？** 它们的可靠性如何？
5. **这一领域被批评在哪里？** 我们必须避免哪些方法论陷阱（选择性编码、自相关、伪相关、不可证伪）？
6. **有哪些现成的开源模型代码和数据库可以直接拿来做校准集？**

---

## 2. 已有成熟模型与理论

### 2.1 Goldstone 的结构-人口理论（DST/SDT，1991）

- **核心机制**：社会分三个"隔间"——平民（populace）、精英（elites）、国家（state）。人口增长超过土地生产率提升 → (a) 实际工资下降、租金上升、城市化、青年膨胀 → 平民动员潜力上升；(b) 精英候选人数量增长快于精英位置数量 → 精英过度生产（elite overproduction）与精英内斗；(c) 军队与官僚扩张、国家名义开支上升 → 财政危机与合法性危机。三者同时到位时形成"革命情境"（revolutionary situation），再由**触发事件**（trigger）引爆。
- **形式化程度**：Goldstone 1991 本身是**口头模型 + 一个手工计算的 Political Stress Indicator (PSI)**。Turchin & Hoyer (2023) 明确写道："This was done first as a verbal model (Goldstone 1991), then later as a formal mathematical model (Turchin 2003, 2016)。"
- **状态变量**：N（人口）、w（相对工资）、E（精英数）、ε（相对精英收入）、S（国家财政/合法性）、Ψ（PSI）、W（不稳定强度）。
- **适用范围**：Goldstone 原始样本是早期近代（英国 1640、法国 1789、奥斯曼 Celali、明末）。后续扩展到罗马、俄国、清、美国、日本、乌克兰、波兰、法国。
- **已知局限**：Goldstone 本人（2017, Cliodynamics 8: 85–112）承认 DST 是"人口变化作用于**制度**的理论"，同样的人口压力在不同制度语境下表现完全不同（"The demographic structural theory is not a 'dumb' theory, predicting the same result from every turn in the underlying cycles that it generates"）。历史学界基本拒绝它（Lawrence Stone 在 NYRB 的负面书评导致出版社"埋葬"了这本书）。
- **出处**：Goldstone 1991/2016（Crossref 验证：Routledge 重版 10.4324/9781315408620；1992 年 AHR、Social Forces 书评已验证）；Goldstone 2017, Cliodynamics 8(2): 85–112, DOI 10.21237/c7clio8237450（**已下载全文**）。

### 2.2 Turchin 的人口-财政模型（Demographic-Fiscal model, DF）

**这是整个领域里最小、最可实现、参数最少的封闭模型。** 方程原文出自 Turchin 2003, *Historical Dynamics*, p.123；本次我通过 Alexander (2016, Cliodynamics 7: 76–108) 的复现取得逐字方程（**未直接核对 Turchin 2003 原书**）：

```
(1) dN/dt = r · N · (1 − N/N_MAX)
(2) N_MAX = K + C·S/(κ + S)
(3) dS/dt = γ·(1 − N/N_MAX)·N − β·N
```

- N = 人口；N_MAX = 承载力；S = 国家资源（单位：人·年，即"劳动力当量"）；r = 内禀增长率；γ = 税率；β = 人均国家开支；K = 无国家时的承载力；C = 强国家能额外支撑的人口上限；κ = S 对 N_MAX 的半饱和常数。
- **机制直觉**：国家提供安全 → 可耕作面积扩大 → N_MAX 提高；人口逼近 N_MAX → 人均剩余下降 → 税基萎缩而开支照旧 → S 单调下降 → S 归零后 N_MAX 塌回 K → 人口崩溃 → 循环。
- Alexander (2016) 把 (2) 简化为 `N_MAX = K + C·[S>0]`（布尔），消掉 κ，**不影响拟合质量**。
- **拟合结果（英格兰 1086–1750）**：`r = 0.013/yr；M = K+C = 5.4（1485 前）/ 7.0（1485 后）百万人；β = 0.31 / 0.45；K = 1.65（Plantagenet）/ 4.75（Tudor-Stuart）/ 6.44（mercantile）百万人`。平均相对误差 **4.6%**，与 9 阶多项式（10 个参数）的 4.8% 相当，但 DF 只用 6 个参数。
- **重要含义**：一个 6 参数的机械模型能达到 10 参数曲线拟合的精度 → 这是"结构有解释力"的**参数效率论证**，也是我们评价自己内核的正确标准。
- **出处**：Alexander, M. 2016. "Application of Mathematical Models to English Secular Cycles." *Cliodynamics* 7(1): 76–108. DOI 10.21237/C7clio7128325（**已下载全文**）。

### 2.3 Turchin & Korotayev 的"战争模型"（2006）

同样由 Alexander (2016) 逐字复现（原文 Turchin & Korotayev 2006: 122，**我未直接核对原文**）：

```
(7)  dN/dt = r·N·(1 − N/N_MAX) − δ·N·W
(8)  dW/dt = a·N² − b·W − α·S
(9)  dS/dt = [(1 − N/N_MAX) − β]·N
(10) N_MAX = K_MAX − c·W
```

- W = 内部不稳定（internal warfare）；其余同上。
- **拟合参数（英格兰，Alexander 2016 Fig.9）**：`第1周期 K_MAX=1.6, c=0, r=3%, β=0.25；第2周期 K_MAX=5.5, c=0.7, r=1.4%, β=0.3；第3周期 K_MAX=5.5, c=0.1, r=2.5%, β=0.25；三周期共用 δ=0, a=0.0045, b=0.003, α=0.005`（1690 后 b=0.1）。共 **18 个可调参数**。
- **Alexander 的判决**：战争模型对人口的拟合"unimpressive"，DF 用 1/3 的参数得到同样好的结果；战争模型唯一的额外价值是它能产生 W。**这是一个警告：加变量不等于加解释力。**

### 2.4 Turchin 2013 的 PSI 框架（可分模块实现）

出自 Turchin, P. 2013. "Modeling Social Pressures Toward Political Instability." *Cliodynamics* 4(2): 241–280. DOI 10.21237/C7clio4221333（**已下载全文**，方程逐字摘录）。

```
Ψ (PSI) = MMP × EMP × SFD

MMP = w⁻¹ · (N_urb/N) · A₂₀₋₂₉          # 逆相对工资 × 城市化率 × 20–29岁人口占比
EMP = ε⁻¹ · E/(s·N)                      # 逆相对精英收入 × 精英数/(职位数≈s·N)
     ≈ ε⁻¹ · e     （s 常数时，e = E/N）
SFD = 财政赤字 / 债务占 GDP 比 的某种单调变换
```

工资的一般式（现象学的 Cobb-Douglas 型）：

```
(1) W_{t+τ} = a · (G_t/N_t)^α · (D_t/S_t)^β · C_t^γ
(2) log W_{t+τ} = A + α·log(G/N) + β·log(D/S) + γ·log C + ε_t
```
- G/N = 人均 GDP；D/S = 劳动需求/供给；C = "文化/强制"（非市场力量）；τ = 工资黏性滞后，"至少 3 年（劳资合同典型长度），大概不超过 10 年"。
- 命令经济退化为 `W = (G/N)^α · C^γ`；奴隶制退化为 `W = C`。**这个降级链条对我们很有用：同一套方程可以覆盖不同制度的社会。**

精英动力学：

```
(3) dE/dt = r·E + μ·N
    μ = μ₀·(w₀/w − 1)                    # 净社会流动率
(4) dE/dt = r·E + μ₀·N·(w₀/w − 1)
    de/dt = μ₀·(w₀/w − 1)                # 若精英与平民人口学相同，e=E/N
(5) ε = (1 − w·λ)/e                      # 相对精英收入；λ = 劳动人口/总人口 ≈ 0.5
```

农村→城市迁移（带非线性阈值）：
```
(6) dN_rur/dt = r·N_rur − r·N_rur·(N_rur/K)^θ ,   θ = 5
```
- Turchin 明确说 θ=1（线性）不现实，θ=10 太像阶跃，取 **θ=5**。这是一个"为了让模拟能跑"的选择，Turchin 自己也这么承认。
- 美国 1780–1860 人口增长率从 3%/yr 降到 2%/yr，模型取 **r = 2.5%/yr**。

### 2.5 Turchin et al. 2013 PNAS：文化多层选择的空间 ABM（**有完整开源实现和参数**）

- 论文：Turchin P., Currie T.E., Turner E.A.L., Gavrilets S. 2013. "War, space, and the evolution of Old World complex societies." *PNAS* 110(41): 16384–16389. DOI 10.1073/pnas.1308825110（PMC3799307，**已读全文**）。
- **网格**：非欧亚大陆 100×100 km 方格，2647 个农业格；每格有 biome（沙漠/草原/农业）与海拔；农业范围随时间外扩（外生时间表）。**时间步 = 2 年**，共 3000 年（1500 BCE–1500 CE）。
- **每格两个二进制向量**：ultrasociality traits U（长度 n_ultra）、military tech M（长度 n_mil）。
- **规则（从 Alan Turing Institute 的复现代码 GUARD 逐行确认）**：

```
attack_power(P)   = 1 + β · Σ_{j∈P} Σ_i u_ij           # 即 1 + β·S·ū
defence_power(c)  = attack_power(polity(c)) + γ · E_c   # E_c = 海拔(km)；海攻时不加海拔
P_success         = max(0, (P_att − P_def)/(P_att + P_def))
P_ethnocide       = clip(ε_min + (ε_max−ε_min)·(Σm_att/n_mil) − γ₁·E_def , 0, 1)
P_disintegrate(P) = clip(δ₀ + max(0, δ_s·|P| − δ_a·ū_P) , 0, 1)
mil-tech 扩散      : 每步以概率 σ 向 4 邻域之一扩散；一旦获得永不丢失
ultrasocial 突变    : 0→1 概率 μ₀₁，1→0 概率 μ₁₀，且 μ₀₁ ≪ μ₁₀
```

- **参数（GUARD `guard/parameters.py`，注释写明"Default parameters taken from Turchin et al. 2013 supporting information"）**：
  `n_ultra=10, n_mil=5, β=1, γ=4, σ=0.25, ε_min=0.05, ε_max=2（APL 源码值；论文文本为 1）, γ₁=1, δ₀=0.05, δ_s=0.05, δ_a=2, μ₀₁=0.0001, μ₁₀=0.002, sea_attacks=True, d_sea=1, Δ_sea=0.0025（APL 源码值；SI 为 0.025）, attack_method='uniform', tech_seed='steppes'`
- **拟合**：全模型解释 imperial density 方差的 **65%**（三个纪元分别 0.56/0.65/0.47）；关掉海拔 → 0.48；军技对 ethnocide 无效 → 0.16；军技随机播种（而非草原界面）→ 0.17。7941 个数据点，12 个参数（其中只有 4 个有显著影响）。
- **最重要的负面结果（Madge et al. 2019 独立复现）**：模型能预测 imperial density（复现 R²=0.66/0.66/0.49，与原文相当）与人口密度（R²<0.75），与欧洲历史战役位置有"轻度"相关（R²<0.42），但**完全无法再现单个政体的形状**；而且**一旦让政体理性地优先攻击弱邻居（"greedy attack"），拟合大幅崩塌**（0.22/0.39/0.26），草原起源的因果链也失效。
  - 出处：Madge J., Colavizza G., Hetherington J., Guo W., Wilson A. 2019. "Assessing Simulations of Imperial Dynamics and Conflict in the Ancient World." *Cliodynamics* 10(2): 99–114. DOI 10.21237/C7clio10245282（**已下载全文**）。代码：https://github.com/alan-turing-institute/guard （MIT 许可，tag v0.15）。

### 2.6 Bennett 2016 的 ADSM（把 DST 装进空间 ABM，参数从历史数据估计）

Bennett, J. 2016. "Repeated Demographic-Structural Crises Propel the Spread of Large-scale Agrarian States throughout the Old World." *Cliodynamics* 7(1): 1–36. DOI 10.21237/C7clio7128530（**已下载全文**）。

```
(1) dP_r/dt = β(τ_r)·(1 − P_r/K_r)·P_r
(2) K_r     = ρ(τ_r) · I_r(t) · A_r            # 密度 × 农业强化时间表 × 面积
(3) 若 P_r > K_r :  dP_r/dt = −(P_r − δ·K_r)   # 崩塌式回落
(4) dF_r/dt = β_F·(1 − F_r/((1−ε)K_r))·F_r     # 农民
(5) dE_r/dt = β_E·(1 − E_r/(ε·K_r))·E_r        # 精英
```
- **参数**：腹地密度 ρ_h = 4 人/km²，帝国密度 ρ_e = 12 人/km²（据 1150–1300 中世纪英格兰的人口与农业产量标定，Campbell 2010）；帝国净出生率 β_e = **1.71%/yr**，腹地 β_h = **0.2%/yr**（据 KK10 数据）；政体内迁移比例 μ = 0.2%/步；承载力崩塌存活比 δ = **80% 死亡**；精英占承载力比例 ε = **20%**（作者自称"a plausible guess"）；战斗死亡比例：胜方 10%、败方 80%（作者说 δ_vanquished 必须 >50%，>90% 则世界人口低于观测值）；logistic 尺度参数 s = 1.5（700 BCE 前）→ 1.95（之后）。
- **注意矛盾**：Bennett 用 ε=20% 定义精英，Turchin & Hoyer (2023) 说 magnates ≈ 0.01%、中层精英 ≈ 1%、低层 ≈ 10%。**"精英"的操作化在文献内部不一致，这直接影响任何模拟的量级。**

### 2.7 Turchin 2005 的经验检验（英格兰 / 汉 / 唐 / 罗马）

Turchin, P. 2005. "Dynamical Feedbacks between Population Growth and Sociopolitical Instability in Agrarian States." *Structure and Dynamics* 1(1). DOI 10.5070/SD911003259（**已下载全文**）。

- 方法：把人口 X=log N、不稳定 Y=log W 都做 10 年重采样与核平滑（英格兰 h=50y，中国 h=30y，罗马 h=30–50y），拟合 `ΔX(t) = a₀ + a₁X(t−τ) + a₂Y(t−τ)`，τ = 30 年（约一个世代）。
- 结果（Table 2）：

| 数据 | 因变量 | R² | 前半拟合→后半预测 | 后半拟合→前半预测 |
|---|---|---|---|---|
| England | population | 0.93 | 0.90*** | 0.96*** |
| England | instability | 0.85 | 0.92*** | 0.41* |
| Han China | population | 0.42 | 0.86*** | 0.52** |
| Han China | instability | 0.78 | 0.86*** | 0.79*** |
| Tang China | population | 0.64 | 0.76*** | 0.84*** |
| Tang China | instability | 0.63 | 0.80*** | 0.94*** |
| Roman Empire | instability | 0.63 | 0.66** | NS |

- 符号方向与理论一致：不稳定对人口为负，人口对不稳定为正。周期长度"2–3 个世纪"，不稳定相位滞后于人口。
- **中国数据来源**：人口 = Zhao & Xie (1988)；内战频次 = J. S. Lee (1931) 的五年计数。Turchin 排除了汉末–隋之间的分裂期，理由是"DST 是以国家为中心的理论"——**这是一个明显的样本选择动作，我们应当注意。**

### 2.8 Chu & Lee 1994：中国朝代周期的"匪/农/君"三职业人口模型

- Chu, C.Y.C. & Lee, R.D. 1994. "Famine, revolt, and the dynastic cycle: Population dynamics in historic China." *Journal of Population Economics* 7: 351–378. DOI 10.1007/BF00161472（**摘要已验证，全文未取得**；另有 1997 勘误 DOI 10.1007/s001480050040）。
- 摘要原文要点：传统"按年龄分组的密度依赖人口结构"无法解释"密度压力—内战—朝代更替"的互动，因此提出 **bandit / peasant / ruler 三个职业隔间**的人口模型，并给出计量支持；强调"人口构成"的动力学而非总量。
- **对我们的价值极高**：这是把"人是可以改变职业身份的"写进人口模型的最早正式做法——农民在饥荒下转为流寇，流寇被镇压或转为统治者。这正是我们需要的"身份/角色流转"骨架。**但我本次没有取得方程，不能给出具体形式。**

### 2.9 政体寿命的生存分析：三个互相矛盾的结论

| 研究 | 数据 | 结论 | 参数 |
|---|---|---|---|
| Arbesman 2011, *Historical Methods* 44:127–129, DOI 10.1080/01615440.2011.577733 | Taagepera 的 41 个帝国（3000 BCE–600 CE） | 寿命近似**指数分布**（恒定危险率） | τ ≈ 220 年（**转引自 Ciliberti 2025，我未取得原文**） |
| Scheffer M. et al. 2023, *PNAS* 120, DOI 10.1073/pnas.2218834120（**已读全文**） | MOROS 数据库 324 个前现代国家 + Seshat 291 个政体（成立于 2000 BCE–1800 CE） | 终结风险在**前约两个世纪陡升**，之后**饱和**；恒定风险模型拟合明显差；寿命分布**单峰**，众数约 200 年 | 饱和危险函数：MOROS `c=0.0065, h=67.3 (n=324)`；Seshat `c=0.0165, h=161.4 (n=291)` |
| Ciliberti S. 2025, *Cliodynamics* 16, DOI 10.21237/c7clio.53812（**已读全文**） | Gokmen et al. (2020) 的 168 个政治实体（5000 年） | 寿命**指数分布**，τ = 298 年；KS 检验 p = 0.71 | 均值 298 年（剔除 >1500 年的离群值后 277），标准差 310 年，中位数 210 年（指数分布理论中位数 ln2×298 ≈ 207） |
| Wand T. 2024, *Cliodynamics* 15(1): 99–106, DOI 10.21237/c7clio15163477（**已读全文**） | 对 Scheffer 的 MOROS 数据做贝叶斯重分析 | Scheffer 观察到的"年轻国家更稳"可能是**幸存者偏差**：活不过 200 年的国家没留下足够痕迹进入数据库 | 贝叶斯模型 AIC 与 Saturating Risk 模型可比 |
| Lu P., Yang H., Li M., Zhang Z. 2021, *Chaos, Solitons & Fractals* 143: 110615, DOI 10.1016/j.chaos.2020.110615 | 22 个中国帝国 | **幂律分布**，作者推测源于自组织临界（SOC）（**转引自 Scheffer et al. 2023 的描述，我未取得原文**） | — |

**这是本简报最重要的经验事实之一：连"帝国寿命分布是什么形状"这个最基础的问题，学界都没有共识。**

Ciliberti 还给出了帝国规模的平均生命周期：归一化年龄 0→1，规模先 logistic 增长到峰值（约在生命的一半，即真实时间约 250 年），短命帝国（<300 年）到达峰值后**平台化直到猝死**（无收缩预兆，峰值通常比出生时高 50%），长命帝国则在最后 20% 明显衰退。其规模动力学模型：

```
dX⁽⁰⁾/dt = α·X⁽⁰⁾·(1 − γ·Σ_{k∈邻} X⁽ᵏ⁾) + η
α ≈ 1%/yr（"ballpark"，作者自称）；η = 外生随机噪声
```

### 2.10 气候→危机的因果链（Zhang 团队）

Zhang D.D., Lee H.F., Wang C., Li B., Pei Q., Zhang J., An Y. 2011. "The causality analysis of climate change and large-scale human crisis." *PNAS* 108: 17296–17301. DOI 10.1073/pnas.1104268108（PMC3198350，**已读全文**）。

欧洲 1500–1800，16 个变量，Granger 因果检验后得到的链条（**这可以直接当成我们内核的一张 DAG**）：

```
气候变化 → 生物生产力 → 农业产量 → 人均粮食供给 (FSPC)
FSPC → 社会动乱 → 战争
FSPC → 饥荒 → 营养状况
FSPC, 社会动乱, 战争, 饥荒 → 迁徙
营养状况, 迁徙 → 疫病
战争, 饥荒, 疫病 → 人口
人口 → 农业产量 ；人口 → FSPC        （闭环）
```

- **滞后结构**：生物生产力/农业产量/FSPC 对温度**即时**响应；社会动乱、战争、迁徙、营养、疫病、饥荒、人口对 FSPC 下降有 **5–30 年滞后**；社会动乱峰值滞后于温度下降 **1–15 年**。
- **量级**：冷期战争数量 **+41%**；1620–1650 年年均战争死亡是 1500–1619 的 **>12 倍**；人口年增长率从 +0.4% 掉到 **−0.3%**；欧洲人口 1650 年降到最低点 **1.05 亿**。
- **警告**：所有序列都用 **40 年 Butterworth 低通滤波**平滑过；论文报告"120 个交叉相关全部 P<0.05，其中 116 个 P<0.001"。见 §8 反模式 2。

### 2.11 前文明期：狩猎采集人口-资源周期

Szulga R.S. 2012. "Endogenous Population and Resource Cycles in Historical Hunter-Gatherer Economies." *Cliodynamics* 3(2): 234–270. DOI 10.21237/C7clio3213371（**已下载全文**）。
- Hotelling 式空间模型：营地周围的资源点会**拥挤（congestion）**，由此推出采集面积随人口/资源密度/采集效率/通勤时间成本变化的函数；再叠加 Malthus 人口动力学与 Gordon–Schaefer 式驼峰型资源再生。
- **关键结论（定性但重要）**：(a) 可产生稳定平衡、稳定极限环与不稳定振荡；(b) **技术进步反而可能因过度采集导致崩溃**；(c) **群体迁移**消除崩溃与发散振荡但引入新的波动；(d) 若新营地无上限，**个体迁移完全消除振荡**。
- 形式化程度：完全形式化，但**无经验参数标定**。

---

## 3. 可直接用于本项目的机制清单

### 3.0 先回答那个关键的方法论问题

> **"如果我们把 Turchin 的周期机制直接写进内核，我们是否已经把王朝兴衰变成了预设剧情？"**

**是的，如果按下面这三种写法中的任何一种，就是预设剧情：**

- **写法 A（最坏）**：给政体一个 `age` 字段，`if age > 250: collapse_probability += x`。这是显式剧本。
- **写法 B（隐蔽）**：直接实现 Turchin 的 DF 或 war 模型作为顶层驱动，让 `N, S, W` 三个宏观变量以微分方程演化。这仍然是剧本，因为 **DF 模型的周期是它的方程结构（S 的单调下降 + N_MAX 的开关式塌缩）保证的**，不是从下层涌现的。Alexander 2016 的做法暴露了这点：他把 `N_MAX = K + C·[S>0]` 写成布尔开关，模型仍然给出好周期——说明周期性主要来自这个开关，而不是来自任何微观过程。
- **写法 C（更隐蔽）**：把 PSI 当作事件触发器：`if PSI > threshold: spawn_rebellion()`。这把"结构压力"变成了剧情打点器。

**改写原则：把周期性从"方程的性质"降级为"竞争性随机过程的统计后果"。** 具体四条：

**(1) 不要建模"周期"，要建模"危险率"。**
文献中最稳的经验对象不是周期，而是**寿命分布**。Ciliberti 2025 的指数分布意味着**无记忆**（危险率与年龄无关）；Scheffer 2023 的饱和危险意味着危险率在头 200 年上升然后平台化。二者共同点是：**寿命是一个随机变量，不是一个时钟。** 所以内核里不应该有"周期"，应该有

```
λ_collapse(t) = f( 结构状态向量 )          # 单位时间的解体危险率
P(collapse in [t, t+Δt]) = 1 − exp(−λ·Δt)
```
其中 `f` 只依赖**当前可观测的结构量**（人均可耕地、相对工资、精英/职位比、财政余额、边境压力、邻国实力），**绝不依赖政体年龄**。如果模拟跑出来的寿命分布是指数或近饱和危险的形状，那是**结果**，可以拿去和 MOROS/Ciliberti 的分布做校准；如果我们把年龄写进 `f`，我们就是在作弊。

**(2) 让"承载力"由下层物理决定，不要写成参数。**
DF 模型里 `N_MAX = K + C·S/(κ+S)` 是把"国家提供安全→可耕地增加"压缩成一个函数。我们有格网、地形、气候、技术，所以应该把它展开：
```
K_cell = 面积 × 单产(土壤, 气候, 作物, 技术, 灌溉) × (1 − 不安全折损(局部暴力, 距最近据点))
K_polity = Σ_cell K_cell
```
"不安全折损"由实际发生的劫掠/战争事件计算，而不是由 S 这个抽象量。这样，DF 模型里那个制造周期的开关就变成了**空间上分布的、有因果链的过程**。

**(3) 精英过度生产必须由"位置数"这个可数对象产生，不能由比例参数产生。**
Turchin 的 `de/dt = μ₀(w₀/w − 1)` 是现象学的。清代的实证做法（Orlandi et al. 2023）好得多：**数进士名额、数候选人**。我们的世界里应该有具体的官职槽位（数量由行政区划、财政、制度决定）、具体的候选人（由家族、教育、财富生成）。"精英过度生产"= `候选人数 / 空缺数` 这个可数比值随时间上升。这样它就是涌现的会计结果，不是假设。

**(4) 结构 vs 触发必须在数据结构上分离。**
SDT 最有价值的、也最容易被误用的思想是"压力慢慢积累，触发事件随机到来"。工程化：
- 结构压力 `Ψ(t)` 是**连续状态**，每 tick 由会计规则更新，**它自己不产生任何事件**。
- 触发事件（皇帝暴毙、粮价飙升、边境败仗、自焚、蝗灾）是**独立发生的随机/因果事件**。
- 事件是否"点燃"由一个耦合函数决定：`P(escalate | trigger, Ψ) = g(Ψ)`，g 单调递增。
- **因果链记录的是：trigger 事件 ID + 当时的 Ψ 分解（MMP/EMP/SFD 各自的值和它们各自的上游）**。这样"为什么这个国家灭亡"就能一路回溯到具体的粮价、具体的科举落第者、具体的边境战役。

**(5) 一个可证伪的验收标准。** 如果我们的世界跑 5000 年后：
- 政体寿命分布落在指数(τ∈[200,320]) 或 Scheffer 饱和危险的置信带内；
- 且我们**没有在任何地方写入年龄依赖**；
- 且不稳定的功率谱里**同时**出现代际尺度（约 50–80 年）和世纪尺度（约 200–300 年）的成分；

那么"周期"就是真正的涌现。**注意 Alexander 2016 的经验结果**：英格兰 850–1873 年的不稳定序列做 Fourier 变换，**主导波长是约 79 年**（"父与子"两代际循环），多世纪的世俗周期在频谱里**看不出来**。也就是说，如果我们的模拟只产生 250 年周期而不产生 ~80 年的节律，那反而不像真实历史。

---

### 3.1 机制清单（按重要性排序）

> 记号：`Δt` = tick 长度。建议主 tick = 1 年（会计），事件 tick = 1 年，空间战争 tick = 1–2 年（Turchin 2013 用 2 年）。

---

**M1. 局地承载力与人口 logistic 增长**
- 输入：格网面积 A、单产 Y(土壤,气候,作物,技术,灌溉)、安全折损 σ_sec、人口 P
- 输出：K_cell、dP/dt
- 数学草图：`K = A·Y·(1−σ_sec)/人均口粮需求`；`dP/dt = β·P·(1 − P/K)`；当 P>K 时用 Bennett (3) 式的崩塌回落 `dP/dt = −(P − δK)`，δ ≈ 0.8
- 时间尺度：年；空间粒度：格网（建议 25–100 km；Turchin 2013 用 100 km，Bennett 用"区域"）
- 参数：腹地 β_h ≈ 0.2%/yr、国家治下 β_e ≈ 1.71%/yr（Bennett 2016）；密度 ρ_h ≈ 4 人/km²，ρ_e ≈ 12 人/km²
- 证据等级：**B**（logistic 与密度依赖是共识；具体参数只有一个来源且标定自中世纪英格兰）
- 为什么这样简化：把"国家提供安全"从 DF 的抽象 S 改成空间上的 σ_sec，使承载力开关变成因果可追溯量
- 归属：**rules_math**

**M2. 相对工资 / 平民困苦（immiseration）**
- 输入：人均产出 G/N、劳动供需比 D/S、制度-强制因子 C
- 输出：相对工资 w = W/(G/N)
- 数学草图：`log W_{t+τ} = A + α·log(G/N) + β·log(D/S) + γ·log C`，τ ∈ [3,10] 年
- 时间尺度：年（带 3–10 年黏性）；空间粒度：市场区/城市
- 证据等级：**B**（形式是现象学的 Cobb-Douglas；Turchin 2013 明确说"如果没有从机制推导出来的函数形式，就用这个"）
- 关键提醒：这个式子在命令经济退化为 `W=(G/N)^α C^γ`，在奴隶制退化为 `W=C`。**我们的世界如果演化出这些制度，方程要跟着降级**——这正是"制度改变机制形状"的一个可实现例子
- 归属：**rules_math**（C 可由 llm_agent 影响的政策变量驱动）

**M3. 精英位置的会计（elite overproduction 的可数版本）**
- 输入：官职/爵位/教职槽位数 `Slots(t)`（由行政区划数、财政、制度改革决定）、合格候选人数 `Aspirants(t)`（由家族生育、教育投入、财富门槛决定）
- 输出：竞争比 `κ = Aspirants/Slots`；落第者存量 `Frustrated(t)`
- 数学草图：`Frustrated_{t+1} = Frustrated_t·(1−退出率) + max(0, Aspirants_t − Slots_t)`；`EMP = ε⁻¹ · Aspirants/Slots`
- 时间尺度：考试/铨选周期（清代会试 3 年一次）；空间粒度：政体 + 省级
- 参数（清代实证，Orlandi et al. 2023 Table 2）：会试通过率 1691 年 6.2% → 1737 年 6.4% → 1742 年 5.2% → **1850 年 3.5%** → 1890 年 5.5%；北京乡试 1654 年 6000 人争 276 个名额（比率 4.6），1748 年 10000 人（2.3），1874 年 13000 人（1.8）
- 证据等级：**A**（有真实可数的历史序列；机制被广泛接受）
- 为什么这样简化：把不可测的"精英"替换成可数的"槽位/候选人"，消除 Lempert 批评的主观变量问题
- 归属：**rules_math**（槽位数的**制度改革**由 llm_agent 决定，但改革的财政后果由规则计算）

**M4. 国家财政与合法性**
- 输入：税基（人口 × 人均剩余）、税率 γ、军费/官僚开支 β·N、战争支出、赈灾支出
- 输出：S（国库存量）、SFD（财政窘迫指数）、合法性存量
- 数学草图：`dS/dt = γ·(1 − N/N_MAX)·N − β·N − 战争支出 − 赈灾支出`；`SFD = f(赤字/GDP, 债务/GDP)`
- Alexander 2016 提供了一个漂亮的替代解读：`S/N` = "储备合法性"（单位：年）。英格兰 1200 年前后 S/N ≈ 13 年；Anarchy 期间从 13 掉到 7；1549–57 "中都铎危机"期间从 10 掉到 5——两次都没到 0，所以国家没崩。**这给了我们一个可实现的"国家能撑多久"的度量。**
- 参数：英格兰 β = 0.25–0.45（无量纲，人均开支/人均产出的某种标度）
- 证据等级：**B**
- 归属：**rules_math**

**M5. 政治压力指数（PSI）——只作为状态，不作为触发器**
- 输入：MMP、EMP、SFD
- 输出：Ψ
- 数学草图：`Ψ = MMP × EMP × SFD`（Goldstone 原式，Turchin/Orlandi 沿用），或三者做 PCA 取第一主成分（Turchin & Hoyer 2023 推荐当代理变量多时用 PCA）
- **陷阱**：乘法形式意味着**任何一项为 0 则 Ψ=0**。这在数值上很危险（一个良性的国家财政就能把整个压力清零）。Turchin & Hoyer 自己说"especially when only a few proxies are able to be found... a simple multiplicative approach is used"——说明这是权宜之计，不是理论必然
- 证据等级：**C**（形式是约定的；Orlandi et al. 2023 报告 PSI 对内乱的动态回归 adjusted R² ≈ 0.5–0.54，且 PSI 的组合优于任何单项）
- 归属：**rules_math**

**M6. 结构压力 → 事件危险率（把周期变成输出的关键一环）**
- 输入：Ψ（或其分解）、触发事件流
- 输出：叛乱/政变/革命/解体事件
- 数学草图：
  ```
  λ_unrest(t) = λ₀ · exp(k·Ψ̃(t))          # Ψ̃ 为标准化后的压力
  触发事件到达：独立的因果/随机过程（旱灾、败仗、君主早夭、粮价跳升……）
  P(触发升级为大规模事件) = g(Ψ̃) ，g 单调递增，g(低压)≈0
  ```
- 时间尺度：年；空间粒度：政体 + 区域（不稳定应能在空间上传播）
- 证据等级：**B**（"结构 vs 触发"是 Goldstone/Turchin 的核心且被广泛接受；具体函数形式无经验依据 → 那部分是 D）
- 归属：**hybrid**（危险率由规则算；具体触发事件的**内容与叙事**可以交给 LLM，但**是否成功**必须由规则判定）

**M7. 政体解体（无年龄依赖）**
- 输入：政体规模 |P|、平均整合度 ū（可理解为制度/认同/asabiya 存量）、财政 S、边境压力
- 输出：解体概率
- 数学草图（Turchin 2013 PNAS / GUARD 逐行）：`P_disint = clip(δ₀ + max(0, δ_s·|P| − δ_a·ū), 0, 1)`，δ₀=0.05, δ_s=0.05, δ_a=2（每 2 年一步）
- **注意这个式子没有年龄项** —— 正是我们要的形式。规模越大越易解体，整合度越高越不易
- 证据等级：**A**（参数来自已发表模型的 SI，且被独立复现代码确认）
- 归属：**rules_math**

**M8. 空间战争与文化多层选择（制度/规范的传播）**
- 输入：相邻格、双方政体的规模与平均"超社会性特质"、地形海拔、军事技术
- 输出：征服/失败、制度同化（ethnocide）、技术扩散
- 数学草图：见 §2.5 的四条公式与参数
- 时间尺度：2 年/步；空间粒度：100 km 格（对东亚可以细化到 50 km，但要重新标定 δ_s，因为它是"每格"计的）
- 证据等级：**B**（模型能解释 65% 的帝国密度方差是 A 级证据；但 Madge et al. 2019 证明它无法预测政体形状，且依赖"随机攻击"这个不现实假设 → 机制本身降为 B/C）
- **关键的反直觉发现，必须写进我们的设计笔记**：让 agent 变得"聪明"（优先打弱者）会**降低**与历史的吻合度。这说明该模型的解释力来自"选择压力的空间分布"而不是"agent 的理性"。我们既然要用 LLM agent 做决策，就必须在验收时检查：**agent 的理性是否把世界变得比历史更整齐？**
- 归属：**hybrid**

**M9. 气候 → 生产力 → 危机的滞后链**
- 输入：温度/降水异常
- 输出：单产、人均口粮（FSPC）、然后按滞后触发动乱/战争/迁徙/疫病/人口
- 数学草图：见 §2.10 的 DAG；滞后：生产力 0 年；社会动乱 1–15 年；战争/迁徙/疫病/饥荒/人口 5–30 年
- 时间尺度：年；空间粒度：区域（气候场分辨率）
- 证据等级：**C**（链条本身合理且被多篇论文支持，但因果强度被严重质疑——见 §7；且 Orlandi et al. 2023 在清代发现**旱灾与饥荒对内战没有显著滞后效应，只有 PSI 显著**）
- 为什么这样简化：把气候做成**乘性调节器**（改变 K 和 FSPC），而不是直接的事件触发器。**这样气候永远不能"无缘无故地"引发战争，它只能通过粮食这条链。**
- 归属：**rules_math**

**M10. 职业/身份流转（农民↔流寇↔统治者）**
- 输入：人均口粮缺口、镇压强度、劫掠预期收益
- 输出：三个隔间之间的转移率
- 数学草图：Chu & Lee 1994 的 bandit/peasant/ruler 隔间模型（**我未取得方程**）。可先用最简单的形式：`转匪率 = h(w/w_subsistence, 镇压概率, 附近匪帮规模)`
- 时间尺度：年；空间粒度：县/区域
- 证据等级：**C**（模型经过同行评议且有计量支持，但我只验证了摘要，没有方程和参数）
- 归属：**rules_math**（个体决策可由 llm_agent 修饰）

**M11. 代际不稳定节律（"父与子"周期）**
- 输入：上一代暴力经历的记忆衰减
- 输出：暴力倾向的 ~50–80 年振荡
- 数学草图：给人群一个"暴力记忆"存量，随时间指数衰减，直接压低 `g(Ψ)`；`记忆_{t+1} = 记忆_t·e^{−Δt/T} + 本期暴力量`，T ≈ 25–30 年
- 参数：Turchin 2005 用带宽 h=50 年的核平滑**专门把这个节律滤掉**，说"if fathers participate in bitter internal fightings, their sons tend to value stability at almost any cost, while the grandsons exhibit a renewed willingness to revolt"；Alexander 2016 对英格兰 850–1873 的 Fourier 分析给出**主导波长 ≈ 79 年**，指数平滑（α=0.04）后的峰值间隔平均 78 年
- 证据等级：**B**（现象在英格兰序列中有量化证据；机制解释是推测性的）
- **为什么重要**：这是唯一在英格兰频谱里真正显著的周期。**如果我们的模拟只有世纪周期没有代际节律，它比 Turchin 的模型更不像历史。**
- 归属：**rules_math**

**M12. 关键放缓（critical slowing down）作为内生早期预警——用于因果链诊断**
- 输入：任意状态变量的高分辨率时间序列（人口代理、建设活动、粮价）
- 输出：自相关与方差的上升 → 韧性下降的指标
- 数学草图：滚动窗口的 lag-1 自相关 AR(1) 与方差；上升 = 逼近临界点
- 证据等级：**B**（Downey, Haas & Shennan 2016, *PNAS* 113: 9751–9756 在欧洲新石器人口崩溃前找到显著的早期预警信号；Scheffer et al. 2021, *PNAS* 118 在美国西南 Pueblo 社会的建设活动序列中找到同样信号，且每个 Pueblo 时期的寿命"约两个世纪"）
- **对我们的用途**：这不是世界的机制，是**我们自己的诊断工具**。因为我们的模拟有完美的高分辨率时间序列（真实历史没有），我们可以对每一次崩溃做 CSD 检验，用它来回答"这次崩溃是结构性的还是纯外生冲击？"——这正是纲领里"如何验证一个重大历史事件在逻辑上成立"的一个可操作答案
- 归属：**rules_math**（离线分析层，不进世界状态）

**M13. 狩猎采集期的资源-人口周期与迁移阀门**
- 输入：营地位置、资源点密度、拥挤度、通勤成本、采集效率
- 输出：人均收益、人口、资源密度的联合动力学
- 数学草图：Szulga 2012（Hotelling 拥挤 + Gordon–Schaefer 驼峰再生 + Malthus）
- 证据等级：**C**（完全形式化，零经验参数）
- **三条可用的定性结论**：技术进步可致过采崩溃；群体迁移消除崩溃与发散振荡；个体迁移（若新营地无上限）**完全消除振荡**。→ 我们的前文明期如果给足自由迁移空间，就**不会**自发出现周期；周期需要"边界"（Carneiro 式的环境限制）
- 归属：**rules_math**

**M14. 军事技术的不可逆扩散与地形防御**
- 输入：邻接、地形海拔、已有技术
- 输出：技术扩散、攻防修正
- 数学草图：`P_spread = σ = 0.25`/步（一旦获得永不丢失）；防御力 `+γ·海拔(km)`，γ=4；ethnocide 概率 `−γ₁·海拔`，γ₁=1
- 证据等级：**A**（参数出自已发表 SI 并被开源复现确认；关掉海拔效应会把 R² 从 0.65 降到 0.48）
- 归属：**rules_math**

**M15. 政体规模的竞争性 logistic 动力学**
- 输入：自身规模、所有邻国规模、外生噪声
- 输出：规模轨迹
- 数学草图：`dX⁰/dt = α·X⁰·(1 − γ·Σ_{k∈邻} X^k) + η`，α ≈ 1%/yr
- 证据等级：**C**（Ciliberti 2025 的 mean-field 模型，只做了平均行为的定性拟合）
- 归属：**rules_math**

---

## 4. 硬数字与参数表

> 只列有真实来源的。所有"文献未提供"的地方我明确写出来。

| 量 | 数值 | 单位 | 适用时空范围 | 不确定度 | 来源 |
|---|---|---|---|---|---|
| 世俗周期长度 | 200–300 | 年 | 前工业农业国家（英格兰/汉唐中国/罗马） | 定性；未给置信区间 | Turchin 2005 (SD 1:1) |
| 时间滞后 τ（人口↔不稳定回归） | 30（备选 20、10） | 年 | 同上 | 结论对 τ 不敏感 | Turchin 2005 |
| DF 模型 r（英格兰） | 0.013 | /yr | 1086–1750 英格兰 | 单一拟合 | Alexander 2016 Fig.5 |
| DF 模型 M = K+C | 5.4（<1485）/ 7.0（>1485） | 百万人 | 英格兰 | 单一拟合 | Alexander 2016 |
| DF 模型 β | 0.31（<1485）/ 0.45（>1485） | 无量纲 | 英格兰 | 单一拟合 | Alexander 2016 |
| DF 模型 K | 1.65 / 4.75 / 6.44 | 百万人 | Plantagenet / Tudor-Stuart / mercantile | 单一拟合 | Alexander 2016 |
| DF 模型拟合误差 | 4.6 | % 平均相对误差 | 英格兰 1086–1750 | 对照 9 阶多项式 4.8% | Alexander 2016 |
| 战争模型 a, b, α | 0.0045, 0.003, 0.005 | — | 英格兰三周期共用 | 18 参数拟合，作者自评"unimpressive" | Alexander 2016 Fig.9 |
| 战争模型 r | 3% / 1.4% / 2.5% | /yr | 三个英格兰周期 | 同上 | Alexander 2016 |
| 战争模型 K_MAX, c | 1.6/5.5/5.5 ；0/0.7/0.1 | 百万人 ; — | 同上 | 同上 | Alexander 2016 |
| 英格兰不稳定序列主导波长 | ≈ 79（峰值平均间隔 78） | 年 | 英格兰 850–1873 | Fourier + 指数平滑 α=0.04 | Alexander 2016 Fig.8 |
| 整合期 vs 解体期不稳定水平 | 1.37 ± 0.18 vs 2.70 ± 0.45 | Sorokin 指数 | 英格兰四个周期合并 | 单周期不显著；四周期合并 p<0.013 | Alexander 2016 Table 1 |
| "储备合法性" S/N（英格兰 1200） | ≈ 13 | 年 | 英格兰 | 模型推导量 | Alexander 2016 |
| 美国人口增长率 r（模型取值） | 2.5 | %/yr | 美国 1780–1860（实测 3%→2%） | 取中值 | Turchin 2013 Clio 4(2) |
| 农村→城市迁移非线性指数 θ | 5 | — | 美国东北四州 | **作者明说是 1 与 10 之间的"合理折中"** | Turchin 2013 |
| 劳动人口占比 λ | ≈ 0.5 | — | 现代社会 | 波动范围窄 | Turchin 2013 |
| 工资黏性滞后 τ | 3–10 | 年 | 现代劳资合同 | "需要经验确定" | Turchin 2013 |
| 精英分层（Turchin & Hoyer 口径） | magnates ≈ 0.01%；中层 ≈ 1%；低层 ≈ 10% | 占总人口 | 一般 | 明说"merely orders of magnitude" | Turchin & Hoyer 2023 |
| 精英占承载力比例 ε（Bennett 口径） | 20 | % | 中古/古代农业社会 | **作者自称"a plausible guess"** | Bennett 2016 |
| 腹地/帝国人口密度 | 4 / 12 | 人/km² | 标定自英格兰 1150–1300 | 单一来源 | Bennett 2016 |
| 净出生率（帝国/腹地） | 1.71 / 0.2 | %/yr | 同上 / KK10 无帝国区 | 单一来源 | Bennett 2016 |
| 承载力崩塌存活比 δ | 20%（即 80% 死亡） | — | 拟合 TCTG13+KK10 | 经验调参 | Bennett 2016 |
| 战斗死亡比例（胜/败） | 10% / 80% | — | 同上 | 作者说败方需 >50%，<90% | Bennett 2016 |
| 政体内迁移率 μ | 0.2 | %/步 | 同上 | 经验调参 | Bennett 2016 |
| Turchin 2013 ABM 格网 | 100 × 100 | km | 非欧亚大陆，2647 农业格 | — | Turchin et al. 2013 PNAS |
| Turchin 2013 ABM 时间步 | 2 | 年 | 1500 BCE–1500 CE（3000 年） | — | Madge et al. 2019 |
| n_ultra / n_mil | 10 / 5 | 个特质 | 同上 | — | GUARD parameters.py |
| β（超社会性→攻击力系数） | 1 | — | 同上 | — | GUARD |
| γ（海拔→防御，km） | 4 | 每 km 海拔 | 同上 | — | GUARD |
| σ（军技扩散概率） | 0.25 | /步/方向 | 同上 | 论文未指定，GUARD 注明"unspecified" | GUARD |
| ε_min / ε_max（ethnocide） | 0.05 / 2（APL 源码；论文文本为 1） | 概率（后裁剪到 ≤1） | 同上 | **论文与源码不一致** | GUARD |
| γ₁（海拔抗同化） | 1 | 每 km | 同上 | — | GUARD |
| δ₀ / δ_s / δ_a（解体） | 0.05 / 0.05 / 2 | — | 同上 | — | GUARD |
| μ₀₁ / μ₁₀（超社会性突变） | 0.0001 / 0.002 | /步/位点 | 同上 | 比值 20:1（不利于超社会性） | GUARD |
| 海攻距离 d_sea / 增量 Δ | 1 / 0.0025（APL；SI 为 0.025） | 格 / 格每步 | 同上 | **源码与 SI 不一致** | GUARD |
| Turchin 2013 全模型 R² | 0.65（分纪元 0.56/0.65/0.47） | — | 7941 个数据点 | 独立复现得 0.66/0.66/0.49 | Turchin 2013；Madge 2019 |
| 关掉海拔 / 军技→同化 / 草原播种 后的 R² | 0.48 / 0.16 / 0.17 | — | 同上 | — | Turchin 2013 Table 1 |
| "贪婪攻击"版本 R² | 0.22 / 0.39 / 0.26 | — | 同上 | **理性化 agent 使拟合崩塌** | Madge et al. 2019 Table 1 |
| 随机播种军技时每格概率 | 4.34 | % | 与草原格占比相等 | — | Madge et al. 2019 |
| 帝国寿命均值（Ciliberti） | 298（剔除 >1500y 后 277） | 年 | 168 个政治实体，5000 年 | sd = 310 | Ciliberti 2025 |
| 帝国寿命中位数 | 210（指数理论值 207） | 年 | 同上 | — | Ciliberti 2025 |
| 指数拟合 τ | 298 | 年 | 同上 | KS 检验 p = 0.71 | Ciliberti 2025 |
| Arbesman 的 τ | ≈ 220 | 年 | 41 个帝国（Taagepera） | **转引自 Ciliberti，未核对原文** | Arbesman 2011 |
| 饱和危险函数参数（MOROS） | c = 0.0065, h = 67.3 | — | n = 324，2000 BCE–1800 CE | 95% bootstrap | Scheffer et al. 2023 |
| 饱和危险函数参数（Seshat） | c = 0.0165, h = 161.4 | — | n = 291 | 同上 | Scheffer et al. 2023 |
| 寿命分布众数 | ≈ 200 | 年 | MOROS | — | Scheffer et al. 2023 |
| 帝国规模峰值时点 | 生命的约 50%（真实时间约 250 年） | — | 168 实体平均 | logistic 拟合到峰值 | Ciliberti 2025 |
| 短命帝国峰值规模 | 出生时的约 150% | — | 寿命 <300 年者 | — | Ciliberti 2025 |
| 帝国规模自然增长率 α | ≈ 1 | %/yr | mean-field 模型 | **作者自称 "ballpark figure"** | Ciliberti 2025 |
| 冷期战争数量变化（欧洲） | +41 | % | 1500–1800 欧洲 | 40y 低通滤波后 | Zhang et al. 2011 PNAS |
| 1620–1650 年均战争死亡 | >12× 1500–1619 | 倍 | 欧洲 | — | Zhang et al. 2011 |
| 危机期人口增长率 | +0.4% → −0.3% | %/yr | 欧洲 1620–1650 | — | Zhang et al. 2011 |
| 欧洲人口最低点 | 1.05 亿 | 人 | 1650 年 | — | Zhang et al. 2011 |
| FSPC→社会后果滞后 | 5–30 | 年 | 欧洲 1500–1800 | — | Zhang et al. 2011 |
| 温度→社会动乱滞后 | 1–15 | 年 | 同上 | — | Zhang et al. 2011 |
| 清代人口 | 1600: 1.2 亿 → 1766: 2 亿 → 1790: 3 亿 → 1812: 3.5 亿 → 1887: 4 亿 | 百万人 | 中国 | 论文正文另称"1700–1850 从 1.25 亿到 4 亿以上" | Orlandi et al. 2023 Table 1 |
| 清代人均可耕地 | 7.87 → 4.98 → 3.35 → 2.89 → 2.78 | 亩（1 亩 = 614.4 m²） | 对应上列年份 | **正文另写作"1736 年 7.87 亩 → 1851 年 2.78 亩"，与表头年份不一致** | Orlandi et al. 2023 Table 1 + 正文 |
| 清代会试通过率 | 6.2 (1691) / 6.4 (1737) / 5.2 (1742) / 3.5 (1850) / 5.5 (1890) | % | 中国 | — | Orlandi et al. 2023 Table 2 |
| 清代乡试（北京） | 1654: 6000人/276名额；1748: 10000人；1874: 13000人 | 人 | 北京 | 通过比 4.6 → 2.3 → 1.8 | Orlandi et al. 2023 |
| 进士单科最低录取 | 81 人 | 人 | 1796 年 | "历史最低" | Orlandi et al. 2023 |
| 清代 PSI 对内乱的解释力 | adjusted R² ≈ 0.50–0.54 | — | 1644–1912，10 年步长动态回归 | PSI 与自相关项显著；旱灾/饥荒/外战不显著 | Orlandi et al. 2023；Turchin & Hoyer 2023 |
| 清代动态回归系数 | PSI_{t−1}: 20.9 (t=2.4, p=0.02)；Internal War_{t−1}: 0.36 (t=1.9, p=0.07)；Drought_{t−1}: −0.00008 (p=0.99) | — | 同上 | Adjusted R² = 0.54 | Turchin & Hoyer 2023 Table S3 |
| 干旱对农民起义的影响 | +约 10 | % | 中国 1470–1900 | 洪水影响不显著；番薯传播缓解干旱效应 | Jia 2011/2013 |
| Seshat 道德神数据缺失率 | 61（n=490/约 803） | % | Whitehouse et al. 2019 用到的观测 | 被作者重编码为"不存在" | Beheim et al. 2021 Nature |
| Seshat 专家审核覆盖率 | 13% 双项审核 / 24% 单项 / **63% 完全无专家审核** | % of polities | 发表时的 backing data | Seshat 方后来修改了标注 | Slingerland et al. 2020 |
| Seshat 与 DRH 编码一致率（中游黄河 12 个政体） | 不到 1/3 | — | 宗教与仪式变量 | — | Slingerland et al. 2020 Table 1 |
| Seshat 中游黄河宗教变量的独立观测数 | 110 个数据点 ← 仅 16 次独立观测 | — | 5 变量 × 22 政体 | 其余为"数据粘贴" | Slingerland et al. 2020 |
| Seshat "high gods" 变量的独立说明数 | 50 条说明 覆盖 298 个政体 | — | 全库 | 单一 NGA 最多 9 条覆盖 30 个政体 | Slingerland et al. 2020 |
| 专家分歧记录率 | 506 例 = 1.1% | 占总数据覆盖 | Whitehouse et al. 2019 SI | Slingerland 认为这只反映"很少咨询第二位专家" | Slingerland et al. 2020 |
| Cliopatria 规模 | >1600 个政治实体，约 14000 行记录 | — | 3400 BCE–2024 CE | EPSG:4326 几何，EPSG:6933 面积 | Cliopatria README |
| Turchin 2010 预测的检验 | 2010–2020 反政府示威与骚乱在美/英/西欧"dramatically increased" | 定性 | Cross-National Time-Series Data Archive | **只有 1 个预测案例；作者自承"may have been a result of luck"** | Turchin & Korotayev 2020；Turchin & Hoyer 2023 |

**文献未提供可用参数的项（明确记录）**：
- Chu & Lee 1994 的 bandit/peasant/ruler 转移率函数与参数（**本次只取得摘要**）。
- Zhang et al. 2006 (*Climatic Change* 76: 459–477) 与 2007 (*Human Ecology* 35: 403–414) 的相关系数与回归系数（**只取得摘要**）。
- Bai & Kung 2011 (*REStat* 93: 970–981) 气候冲击→华夷冲突的弹性（**只取得元数据**）。
- Chen 2014 (*Oxford Economic Papers* 67: 185–204) 气候冲击→朝代周期→游牧征服的量化结果（**只取得元数据**）。
- Lu et al. 2021 的中国 22 帝国幂律指数（**只有 Scheffer 的转述**）。
- Turchin 2003 *Historical Dynamics* 的 asabiya 空间模型（附录 2）的方程与参数（**只有 Bennett 2016 的描述**）。
- Turchin 2009 (*JGH* 4: 191–217) 的 metaethnic frontier 帝国形成理论的形式化细节（**只验证了元数据**）。

---

## 5. 数据集与数据库

| 名称 | 内容 | 覆盖 | 访问 | URL | 许可 | 本次验证 |
|---|---|---|---|---|---|---|
| **Seshat: Global History Databank** | 政体级社会复杂性、战争技术、宗教、经济变量；CrisisDB（危机后果、不稳定事件、权力更替、清代危机、美国政治暴力） | 全球，全新世至今 | 网站 + API + Codebook + 用户协议 | https://seshat-db.com/ | 需接受 User Agreement | ✅ HTTP 200，页面结构已确认 |
| **Cliopatria** | 全球政体的**地理多边形** + 起止年份 + Wikidata/Wikipedia/SeshatID 链接 | 3400 BCE – 2024 CE，>1600 实体，约 14K 行 | GeoJSON（zip）；GitHub Releases + Zenodo 镜像 | https://github.com/Seshat-Global-History-Databank/cliopatria | 仓库标 NOASSERTION（需逐版本查看 LICENSE） | ✅ README 全文已读；Zenodo（记录 13363121）本次网络不可达 |
| **GUARD** | Turchin et al. 2013 ABM 的独立 Python 复现 + 数据（imperial density、battles.yml、cities.yml、old_world.yml） | 非欧亚 1500 BCE–1500 CE | GitHub | https://github.com/alan-turing-institute/guard | **MIT** | ✅ 源码逐行读过，参数已提取 |
| **MOROS (Mortality of States)** | 324 个前现代国家的形成/终结年份 | 约 3000 BCE 起 | Scheffer et al. 2023 PNAS 的 SI Appendix | https://doi.org/10.1073/pnas.2218834120 | 随论文 | ✅ 正文与参数已读；SI 本身未下载 |
| **D-PLACE** | 民族志社会 × 文化/环境变量 + 语言系统树 | 全球民族志样本 | 网站 + 下载 | https://d-place.org/ | 见站点 Legal | ✅ HTTP 200 |
| **Cliodynamics 期刊全文** | 本领域几乎全部方法论争论的开放获取来源 | 2010–2026，198 篇 | eScholarship（PDF 直链 `https://escholarship.org/content/qt<ID>/qt<ID>.pdf`） | https://escholarship.org/uc/irows_cliodynamics | CC-BY（多数） | ✅ 已批量下载 8 篇 |
| **Seshat Polaris2025 / Equinox2020 数据发布** | 定期冻结的数据快照 | — | Cliodynamics 论文 + build_polaris_dataset 仓库 | https://github.com/Seshat-Global-History-Databank/build_polaris_dataset | MIT（工具） | ✅ 仓库存在 |
| **seshat_api** | 访问 Seshat 的 Python 包 | — | GitHub / PyPI | https://github.com/Seshat-Global-History-Databank/seshat_api | MIT | ✅ 仓库存在 |
| **CHGIS（中国历史地理信息系统）** | 中国历代行政区划 GIS | 秦–清 | 哈佛 | https://chgis.fairbank.fas.harvard.edu/ | — | ❌ 本次访问被 Akamai 拒绝（403/000），**未能验证当前可用性** |
| **CBDB（中国历代人物传记资料库）** | 约数十万历史人物、亲属、任官、著述 | 汉–清 | 哈佛/北大/中研院 | https://projects.iq.harvard.edu/cbdb/ | — | ❌ 本次 403，**未能验证** |
| **KK10 (Kaplan & Krumhardt 2008)** | 逐年人口估计 | 6050 BCE – 1850 CE | 经 Bennett 2016 引用 | — | — | ⚠️ 只有二手引用 |
| **TCTG13** | Turchin/Currie/Turner/Gavrilets 2013 的历史大型政体地图（100 km 格 × 100 年） | 1500 BCE–1500 CE | PNAS SI + GUARD 仓库 | — | — | ✅ 经 GUARD 仓库确认存在 |
| **Gokmen et al. (2020) 帝国数据库** | 168 个政治实体的起止年份 + 涵盖的现代国家数 | 5000 年 | 经 Ciliberti 2025 引用，来源含 empires.wnvermeulen.com / Britannica / worldhistory.org | — | — | ⚠️ **Crossref 检索未找到该论文，只有二手引用** |
| **ClioInfra** | 长期经济/人口指标 | 全球 | 经 Orlandi et al. 2023 引用（清代人口估计） | — | — | ⚠️ 只有二手引用 |
| **Cross-National Time-Series Data Archive** | 反政府示威、骚乱等不稳定事件计数 | 1815– 至今 | 商业订阅 | — | 商业 | ⚠️ 经 Turchin & Korotayev 2020 引用 |

---

## 6. 中国与东亚特定证据

### 6.1 汉与唐：人口-不稳定的双向反馈（Turchin 2005）

- 数据：人口取自 **Zhao & Xie (1988)**（指数核带宽 10 年插值，10 年重采样）；内战频次取自 **J. S. Lee (1931)** 的五年计数（核带宽 30 年）。Turchin 说 Lee 的数据主要来自《歷代帝王年表》类史源，并称"与独立史源核对显示高准确度（Lee 1931: 114）"。
- 结果见 §2.7 表。**中国的 R² 明显低于英格兰**（人口 0.42–0.64 vs 0.93），Turchin 归因于数据质量。
- 他自己列出的中国人口数据问题：官员伪造户口；应税户数→实际人口的换算系数逐朝变化且未知；国家控制疆域变动；乱世户口下降到底是死亡还是"国家数不到人"无法区分。**Ho 1959、Durand 1960、Song et al. 1985 之间在绝对水平上有争议，只有相对变化有共识。**
- **样本选择动作**：Turchin 明确排除了东汉灭亡到隋统一之间的分裂期，理由是"DST 是以国家为中心（state-centered）而不是以国家体系为中心的理论"。→ **对我们的含义：SDT 在多国并立期没有定义。而我们的世界大部分时间可能就是多国并立。**
- Turchin 还指出中国的动力学"运行在更快的时间尺度上"，所以他对中国用 h=30 年而不是英格兰的 h=50 年，并说中国数据里**看不到双代际（bigenerational）周期**。

### 6.2 清代：目前最完整的东亚 SDT 案例研究

Orlandi G., Hoyer D., Zhao H., Bennett J.S., et al. 2023. "Structural-demographic analysis of the Qing Dynasty (1644–1912) collapse in China." *PLOS ONE* 18(8): e0289748. DOI 10.1371/journal.pone.0289748（**已下载全文**）。

- **操作化**：MMP = 人均可耕地的倒数；EMP = 人均进士名额的倒数；SFD = 总收入 − 总支出；PSI = 三者相乘（全部缩放到 0–1）。
- **硬数据**：见 §4 表（人口 1.2 亿→4 亿；人均可耕地 7.87→2.78 亩；会试通过率 6.2%→3.5%）。人体测量学证据（平均身高下降）佐证 18 世纪的困苦加深。
- **结果**：MMP 与 EMP 在 18 世纪一路上升、19 世纪初见顶；SFD 约 1800 年才开始上升、19 世纪后期见顶；PSI 峰值在 **1840–1850**，此后下降但未回到清初水平。动态回归（10 年步长）显示**只有 PSI 与内战自相关项显著**；旱灾、饥荒、外战都不显著。Adjusted R² ≈ 0.50–0.54。
- **具体的因果链例子**（对我们非常有参考价值）：太平天国的领导层是**一群科举落第的客家人**——"elite overproduction" 在这里不是抽象指数，而是"一群具体的、有组织能力和意识形态的落第者"。同样，1895 公车上书与 1898 戊戌变法是"受教育精英过剩"的另一种表现（改革而非叛乱）。
- **恢复力的证据**：清朝在 PSI 高位撑了几十年——常平仓与荒政体系、江南市场网络、云南矿业投资、增设学校与旗人固定名额。**这说明"高压力"不等于"必崩"，制度适应可以延后崩溃。** 后期 MMP 下降是因为战乱减少人口，EMP 缓解是因为增设官职。
- **作者自己承认的另一条路径**：清末真正致命的是**军事精英崛起**（湘淮系→军阀化）截留了本该用于工业化的剩余，行政精英式微。→ 精英**类型的转换**（Mann 的四种社会权力之间的转移）是一个 SDT 主线模型没有的机制。

### 6.3 中国朝代长度的定量研究

- **Lu, Yang, Li & Zhang 2021**（*Chaos, Solitons & Fractals* 143: 110615）对 22 个中国帝国拟合出**幂律**寿命分布并推测自组织临界；这与 Arbesman/Ciliberti 的指数分布和 Scheffer 的饱和危险都不一致（**我只有 Scheffer 的转述**）。
- **Ciliberti 2025 的数据处理细节值得注意**：他用的数据库"把罗马与拜占庭当作一个长政治实体，而每一个中国朝代都算不同实体"。→ **中国朝代在这类统计里被系统性地切碎，欧洲帝国被系统性地合并。任何"中国朝代平均 X 年"的说法都强烈依赖这个编码约定。**
- **Scheffer et al. 2023 的坦白**：他们明确指出"中国古代的很多朝代更替基本上只是统治精英的替换"（"many dynastic changes in ancient China were largely just a replacement of the ruling elite"），与克里特晚青铜时代那种带来人口、宫殿体系与文字消失的崩溃完全不是一回事。→ **"朝代更替" ≠ "社会崩溃"。我们的内核必须把这两件事分成不同的事件类型。**

### 6.4 气候-冲突的中国证据

- Zhang D.D., Jim C.Y., Lin G.C-S., He Y-Q., Wang J.J., Lee H.F. 2006. "Climatic Change, Wars and Dynastic Cycles in China Over the Last Millennium." *Climatic Change* 76: 459–477. DOI 10.1007/s10584-005-9024-z。摘要（已验证）：战争频率呈周期性，紧跟全球古温度变化；气候变化、战争、收成、人口规模、朝代更替之间有"强而显著"的相关；冷期→热能输入减少→农业社会土地承载力下降→暖期积累的人口无法维持→"推力"→战争→王朝崩溃与人口崩溃；战争频率因华北/华中/华南的地理差异而不同。
- Zhang D.D., Zhang J., Lee H.F., He Y-q. 2007. "Climate Change and War Frequency in Eastern China over the Last Millennium." *Human Ecology* 35: 403–414. DOI 10.1007/s10745-007-9115-8。摘要（已验证）："几乎所有战争频率峰值与朝代更替都发生在降温阶段。"
- Chen Q. 2014/2015. "Climate shocks, dynastic cycles and nomadic conquests: evidence from historical China." *Oxford Economic Papers* 67: 185–204. DOI 10.1093/oep/gpu032（**元数据已验证，内容未取得**）。
- Bai Y. & Kung J.K. 2011. "Climate Shocks and Sino-nomadic Conflict." *Review of Economics and Statistics* 93: 970–981. DOI 10.1162/REST_a_00106（**元数据已验证，内容未取得**）。
- Jia R. 2011 (HiCN WP93) / 2013 (*Economic Journal* 124: 92–118, DOI 10.1111/ecoj.12037)："Weather Shocks, Sweet Potatoes and Peasant Revolts in Historical China"。**已下载工作论文**：1470–1900 年逐年数据，**干旱使农民起义增加约 10%，洪水的影响不显著；番薯的传播削弱了干旱→起义的效应。**
  → **这是我们最需要的那类机制证据：不是"气候导致战争"，而是"气候通过特定作物的抗旱性作用于起义概率"。作物组合是一个可以被技术/贸易改变的中介变量。**
- Kung J.K. & Ma C. 2014. "Can cultural norms reduce conflicts? Confucianism and peasant rebellions in Qing China." *Journal of Development Economics* 111: 132–149. DOI 10.1016/j.jdeveco.2014.08.006（**元数据已验证**）。→ 提示"文化规范"可以作为冲突概率的调节项。
- Pei Q. & Zhang D.D. 2014. "Long-term relationship between climate change and nomadic migration in historical China." *Ecology and Society* 19(2). DOI 10.5751/ES-06528-190268（**元数据已验证**）。
- Yin W. 2019/2020. "Climate Shocks, Political Institutions, and Nomadic Invasions in Early Modern East Asia." *Journal of Conflict Resolution* 64: 1043–1069. DOI 10.1177/0022002719889665（**元数据已验证**）。→ 制度作为调节项。

### 6.5 中国 vs 欧洲的地缘结构

- Ko C.Y., Koyama M., Sng T-H. 2018. "Unified China and Divided Europe." *International Economic Review* 59: 285–327. DOI 10.1111/iere.12270（**元数据已验证，内容未取得**）。→ 这条线索对我们的"东亚舞台"很关键：单一草原威胁方向 vs 多方向威胁，会导致统一 vs 分裂的不同均衡。
- Turchin et al. 2013 的模型里，中国北部之所以是最早的"帝国生成热点"之一，正是因为**紧邻欧亚草原界面**（军事技术最早在那里播种）。模型输出的热点顺序：美索不达米亚、埃及、华北 → 中地中海/西欧、北印度、华南 → 北欧东欧、日本、东南亚、撒哈拉以南。
- 空间自回归（SAR）分析：**距草原的距离是帝国密度的最强单一预测因子**，其次是农业存在的长期性，再次是海拔；三者共解释 42% 的方差。

### 6.6 Seshat 中国数据的质量问题（必须知道）

Slingerland 等人对 Seshat 中游黄河流域（MYRV）的审计（**已下载全文**）：
- 用 DRH（Database of Religious History）的专家生成/专家审核编码重编 12 个 MYRV 政体，**Seshat 与专家数据一致的不到三分之一**。
- MYRV 宗教与仪式变量的 **110 个数据点（5 变量 × 22 政体）只由 16 次独立观测支撑**，其余是把前一个政体的编码粘贴过来。举例：用晚商（约前 1800 年）的仪式频率观测去编码从西周（前 1122）到明（1643）的每一个政体。
- Whitehouse et al. 2019 的关键数据点之一是"中游黄河有文字而无道德神"，依据是 Robert Eno 的一条意见；Slingerland 指出 Eno 的观点在学界是少数派，DRH 里 David Keightley 与 Lothar von Falkenhausen 两位的条目都与之相反。
- 该论文最终被 *Nature* 撤稿（Whitehouse H. et al. 2021. "Retraction Note: Complex societies precede moralizing gods throughout world history." *Nature* 595: 320. DOI 10.1038/s41586-021-03656-3），起因是 Beheim B. et al. 2021 (*Nature* 595: E29–E34, DOI 10.1038/s41586-021-03655-4) 指出 **61%（n=490）的道德神观测在原始数据里是"unknown/suspected unknown"，被作者重编码为"不存在"**；用现存数据或标准插补方法重做，结论**反转**（道德神先于社会复杂性上升）。整个数据库里"某个世界区域在道德神首次出现之前有明确的'不存在'记录"的观测**只有一条，来自中国中游黄河流域**。

→ **对我们的直接后果：不要把 Seshat 的中国宗教/仪式变量当作校准集。社会复杂性与战争技术变量的质量另说，但也需要独立核查。**

---

## 7. 学界争议与未解决问题

**(1) 政体寿命的危险率形状 —— 完全没有共识。**
恒定危险（指数分布：Arbesman 2011；Ciliberti 2025，τ=298，KS p=0.71，n=168）vs 前 200 年上升后饱和（Scheffer et al. 2023，n=324 + 291，明确报告恒定风险模型"consistently produces a bad fit"）vs 幂律/自组织临界（Lu et al. 2021，n=22 中国帝国）vs 幸存者偏差假说（Wand 2024：短命国家没留下痕迹，所以看起来年轻国家更稳）。Scheffer 自己承认"结果对纳入哪些国家和如何断代高度敏感"。

**(2) 世俗周期在英格兰的频谱里看不见。**
Alexander 2016 对英格兰 850–1873 的不稳定序列做 Fourier 分析，**主导波长约 79 年**，多世纪周期"not evident"。整合期 vs 解体期的不稳定差异在**单个周期内都不显著**，要合并四个周期才达到 p<0.013。这是本领域内部一篇同行评议论文对核心经验主张的削弱。

**(3) Turchin 2013 ABM 的解释力来源可疑。**
Madge et al. 2019 的独立复现：能预测帝国密度（R²≈0.65）和人口密度（R²<0.75），但**对政体形状零相关**，对战役位置只有轻度相关（R²<0.42）；一旦让政体理性攻击弱邻居，拟合崩塌。作者结论："random attacks are a key trait of the original model"。→ 这个模型可能拟合的是"哪里适合长出大国"这个地理事实，而不是"大国如何形成"这个过程。

**(4) Seshat 的数据生产方式。**
Slingerland et al. 2020（*Journal of Cognitive Historiography* 5: 124–141, DOI 10.1558/jch.39393）指控：63% 的政体完全无专家审核；"最勤奋的专家审核人" Vesna Wallace 被联系时表示她根本没有参与任何编码/审核，且大部分被列名的 NGA 完全不在她的专业范围；发表时提供给 *Nature* 审稿人的冻结版本后来被系统性修改。Seshat 方在 Cliodynamics 上有多篇方法论回应（"Translating Knowledge about Past Societies into Seshat Data", "Fitting Dynamic Regression Models to Seshat Data", "The Equinox2020 Seshat Data Release"），**我本次未逐篇读完，因此不能给出双方论证的完整对比**。

**(5) 预测性主张的证据基础极薄。**
Turchin 2010 的"2010 年代西方不稳定上升"预测被 Turchin & Korotayev 2020 自评为成功，但 Turchin & Hoyer 2023 自己写："One case of successful prediction is not sufficient to declare this method a fool-proof forecasting tool. Indeed, this one success may have been a result of luck." 同一份文档也承认现有历史检验只有约 20 个案例，正在扩展到 >100 个。

**(6) 气候→冲突的因果强度被广泛质疑。**
Hsiang S., Burke M., Miguel E. 2013. "Quantifying the Influence of Climate on Human Conflict." *Science* 341, DOI 10.1126/science.1235367（元数据已验证）主张普遍效应；Buhaug H., Nordkvelle J., Bernauer T., Böhmelt T., et al. 2014. "One effect to rule them all? A comment on climate and conflict." *Climatic Change* 127: 391–397, DOI 10.1007/s10584-014-1266-1（元数据已验证）是核心反驳。而在清代这个具体案例中，**Orlandi et al. 2023 自己发现旱灾和饥荒对内战没有显著滞后效应，只有 PSI 显著。**

**(7) "精英"的操作化不一致。**
Turchin & Hoyer 2023 用 0.01%/1%/10% 的幂字塔；Bennett 2016 用 20% 的承载力份额；Turchin 2013 美国案例用"顶尖法学院学位数"；Orlandi 2023 清代用"人均进士数"。这些不是同一个量。Lempert 2018 正是抓住这一点批评：cliodynamics 的变量里有大量"不可测量的主观项"（"representational utility", "moral integrity utility", "days of rage", "state strength", "spiral of violence"）。

**(8) 系统发生学方法能不能用来检验国家起源假说。**
Opie C. & Atkinson Q.D. 2025. "State formation across cultures and the role of grain, intensive agriculture, taxation and writing." *Nature Human Behaviour*, DOI 10.1038/s41562-025-02365-5，主张"可征税的谷物"而非"农业剩余"导致国家与文字。Turchin 2025（SocArXiv 10.31235/osf.io/xenpv）反驳：民族志数据库不记录变量随时间的变化，只能推静态相关不能检验因果；语言树重建误差导致高 Type I/II 错误率；印欧语系起源的贝叶斯系统发生结论（安纳托利亚起源）后来被语言学+考古+古 DNA 证据推翻为草原起源。**这场争论对我们的意义是：横截面的"哪些特征共现"永远不能替代时间序列的"什么先于什么"。**

**(9) DST 在多国并立体系下没有定义。**
Turchin 2005 明确排除了中国分裂期。Turchin 2013 PNAS 的 ABM 处理的是多政体，但那是完全不同的模型（没有精英、没有财政）。**目前没有一个模型同时包含 SDT 的三隔间与多政体地缘竞争。** 这正好是我们要填的洞。

---

## 8. 反模式：本领域常见的错误建模方式（我们必须避免）

**AP-1. 把周期写进内核，然后惊喜地发现出现了周期。**
DF 模型的周期由 `N_MAX` 的开关式塌缩保证；Alexander 2016 把它简化成布尔量 `[S>0]` 后模型照样好用，等于承认周期主要来自这个开关。**判据：如果删掉某一行代码周期就消失，那这行代码就是剧本。**

**AP-2. 先做重度平滑，再报告相关显著性。**
Zhang et al. 2011 对所有序列做 **40 年 Butterworth 低通滤波**，然后报告"120 个交叉相关全部 P<0.05，116 个 P<0.001"。低通滤波后的序列有极强的自相关，有效样本量远小于名义样本量，标准 t 检验的 p 值严重高估。Granger & Newbold 1974（*Journal of Econometrics* 2: 111–120，已验证）与 Phillips 1986 早就证明了这一点。Turchin 自己在 2005 年是**先做平稳化去趋势再回归，并做样本外交叉验证**——这是正确做法，值得抄。
> **我们的做法**：任何"我们的模拟再现了历史相关"的声明，都必须给出样本外预测、块自助法（block bootstrap）或替代序列（surrogate）检验，而不是原始 p 值。

**AP-3. 症状当原因（endogeneity）。**
Lempert 2018 的核心批评："因变量是社会崩溃与暴力，那么自变量里就不能包含崩溃与暴力的症状或情绪，因为症状不能是原因。" 他点名"合作/信任/(不)公正感的水平"这类变量。
> **我们的做法**：状态向量必须分层——**物质层**（人口、土地、粮食、金属、马匹）→ **制度层**（职位数、税率、法律）→ **信念层**（合法性、认同、意识形态）。上层可以影响下层的**速率**，但不能同时既是解释项又是被解释项。

**AP-4. 用参数换拟合。**
Alexander 2016：DF 模型 6 参数 vs 战争模型 18 参数，后者对人口的拟合并不更好。Turchin 2013 自己也警告"大型复杂模型往往结构不稳定，一个参数的小变化会导致动力学大变"，主张"a spectrum of models, each simple enough"。
> **我们的做法**：每加一个机制，必须报告它在**参数数量**和**解释的现象数量**上的收支。用 AIC 类的准则，而不是"看起来更真实"。

**AP-5. 用聚合统计的拟合去证明微观机制。**
Turchin 2013 的模型解释了 65% 的帝国密度方差，却完全无法预测任何一个政体的形状（Madge et al. 2019）。聚合量的拟合可以来自完全错误的微观机制。
> **我们的做法**：验收指标必须包含**分布形状**（政体寿命分布、规模分布、战争烈度分布）与**空间形态**（政体边界与地形/河流的关系），而不只是总量曲线。

**AP-6. 缺失值当成"不存在"。**
Beheim et al. 2021：61% 的缺失被重编码为"无道德神"，结论因此反转。
> **我们的做法**：世界状态里"不知道"和"不存在"必须是两个不同的值。这对纲领第 9 条（世界事实 vs 历史叙事分离）是刚需——世界内部的历史学家看到的必须是三值逻辑。

**AP-7. 数据粘贴与数据填充。**
Seshat MYRV：110 个数据点来自 16 次独立观测；"high gods" 变量在 298 个政体上只有 50 条独立说明。
> **我们的做法**：如果我们从真实历史抽取校准集，必须记录每条数据的**独立观测数**，不能被"覆盖率"迷惑。

**AP-8. 幸存者偏差。**
Wand 2024：Scheffer 观察到的"年轻国家风险低"可能纯粹是因为活不过 200 年的国家没进数据库。
> **我们的做法**：拿真实政体寿命分布做校准时，必须先模拟"如果我们的世界只有留下考古痕迹的政体被记录，分布会变成什么样"，再去和真实数据比。这在我们的系统里是可做的（我们有完美的 ground truth）。

**AP-9. 用民族志横截面推时间因果。**
Turchin 2025 对 Opie & Atkinson 2025 的批评。
> **我们的做法**：我们的世界天然有时间序列，别浪费它。任何"A 导致 B"的因果链记录都必须包含时间顺序与中介变量的取值。

**AP-10. 单个成功预测就宣称可预测性。**
> **我们的做法**：涉及"我们的模型能预测"这类话，一律要求预注册 + 多案例。对内部而言：任何机制被加进内核前，先声明它应该产生什么可观测后果，再跑，再比。

**AP-11. 把"朝代更替"与"社会崩溃"混为一谈。**
Scheffer et al. 2023 明确区分：晚青铜时代克里特的终结带来人口、宫殿体系与文字的消失；而中国的很多朝代更替"基本上只是统治精英的替换"。
> **我们的做法**：事件本体（ontology）里至少要有：`政权更替`（统治集团更换，制度延续）/ `国家解体`（中央权威消失，制度部分保留）/ `社会崩溃`（人口、城市化、文字、分层同时下降）。三者的先决条件与后果完全不同。

**AP-12. 让 agent 变聪明就以为更真实。**
Madge et al. 2019 的贪婪攻击实验：R² 从 0.65 掉到 0.16–0.39。
> **我们的做法**：LLM agent 的信息边界（纲领第 4 条）不是一个限制性妥协，而是**拟真的必要条件**。全知理性 agent 会把世界压成一个整齐的最优解，那不像历史。我们应当把"agent 的错误率/信息延迟"当作可调参数，并检查它对宏观分布的影响。

**AP-13. 乘法式 PSI 的零吸收问题。**
`Ψ = MMP × EMP × SFD` 意味着任何一项为零则总压力为零。这在真实数据上被 0–1 缩放掩盖了，但在模拟里会造成病态动力学。
> **我们的做法**：用对数加法 `log Ψ = Σ w_i log(x_i + x_min)`，或者干脆放弃单一标量，直接把三个分量喂给危险率函数。

**AP-14. 把"精英"定义成不可数的东西。**
> **我们的做法**：精英 = 拥有具名职位/爵位/土地阈值以上财产的**可枚举个体或家族**。任何"精英占比"都是从枚举中算出来的会计结果。

---

## 9. 无源判断（D 级，LLM 常识/我的推断，不得当作历史规律）

以下都是我为了让这套东西能落地而做的判断，**没有文献支撑**：

1. **"周期应该改写成危险率"这个改写方案本身是我的设计建议**，不是任何文献的结论。文献只提供了"寿命分布是随机变量"这个经验事实和"结构 vs 触发"这个概念区分。
2. **建议主 tick = 1 年、空间战争 tick = 1–2 年、格网 25–100 km** —— 100 km 与 2 年来自 Turchin 2013，其余是我的推断。缩小格网必须重新标定 `δ_s`（它按"格数"计），我没有见到任何文献讨论这个尺度依赖。
3. **对 Zhang et al. 2011 的"40 年低通滤波导致 p 值虚高"的批评是我的推断**（基于 Granger & Newbold 1974 的一般结论），我没有找到专门针对该论文做此批评的文献。
4. **建议用对数加法替代乘法 PSI** —— 我的建议，无来源。
5. **"AP-12：全知理性 agent 会把世界压平"这个一般化** —— Madge et al. 2019 只在一个模型上证明了这点，我把它推广成一条设计原则，这是外推。
6. **建议的三层状态分层（物质/制度/信念）** —— 我的设计，虽然与 Mann 1986 的四种社会权力和 Lempert 的批评相容，但不是任何人的模型。
7. **建议用 critical slowing down 作为我们自己的因果链诊断工具** —— CSD 用于考古序列有文献（Downey 2016、Scheffer 2021），把它用作**模拟系统的自我诊断**是我的提议。
8. **"如果我们的模拟只有世纪周期没有 ~80 年代际节律，它比 Turchin 的模型更不像历史"** —— Alexander 2016 的英格兰频谱是真的，但把它当作**东亚模拟的验收标准**是我的外推；中国的代际节律 Turchin 2005 明确说"看不到"。
9. **建议把气候做成乘性调节器而非事件触发器** —— 我的设计原则。Zhang 的因果链支持"气候通过粮食起作用"，但不排除直接冲击。
10. **建议的"验收标准"（寿命分布落在指数 τ∈[200,320] 或 Scheffer 饱和带内）** —— 区间是我从 Ciliberti (298)、Arbesman (220)、Scheffer (众数约 200) 三者拼出来的，**没有任何文献给出这个区间**。而且这三者互相矛盾（§7.1），用哪一个当标准本身就是一个未解决的选择。
11. **"Chu & Lee 的匪/农/君隔间是我们最需要的身份流转骨架"** —— 我只读了摘要就下了这个判断。
12. **建议的 `Frustrated` 存量方程（落第者累积 + 退出率）** —— 我构造的，Orlandi 只给了通过率的时间序列，没有给存量模型。
13. **"多国并立期 SDT 没有定义，这正好是我们要填的洞"** —— 前半句有据（Turchin 2005 的排除动作），后半句是我的判断。
14. **代际记忆衰减时间常数 T ≈ 25–30 年** —— 我从 Turchin 描述的"父—子—孙"三代和 h=50 年带宽反推的，文献没有给这个参数。

---

## 10. 参考文献

标注：✅ = 本次检索中取得全文并读过；🟡 = 取得摘要或权威二手引用；⬜ = 仅通过 Crossref 验证了标题/作者/期刊/年份/DOI，内容未取得；⚠️ = 未能在本次检索中验证。

> **引文核验（2026-09-10，独立第三方核验）**：本简报列为"承重"的 22 条引文全部经 Crossref REST API / GitHub API / 原始 URL 独立核对，**无一条不存在，无一条疑似编造，无 not_found**。其中 2 条信息有误已就地修正（Ciliberti 2025 的卷期与页码；Lempert 2018 的题名被截断），另有 1 条（Opie & Atkinson 2025）此前标为"未检索到 Crossref 记录"，本次已找到并核实。因此**没有任何结论因引文问题失去支撑**。注意：核验范围是"文献是否存在、著录是否正确"，**不包括文中援引的具体数值、参数与表格内容是否与原文一致**——那些仍以正文原有的 ✅/🟡/⬜/⚠️ 标注为准。

### 核心模型与理论
1. ✅ Turchin, P. 2005. "Dynamical Feedbacks between Population Growth and Sociopolitical Instability in Agrarian States." *Structure and Dynamics* 1(1). DOI 10.5070/SD911003259. **[已核验]**（Crossref: Turchin Peter, *Structure and Dynamics: eJournal of Anthropological and Related Sciences* 1(1), 2005-09-18）
2. ✅ Turchin, P. 2013. "Modeling Social Pressures Toward Political Instability." *Cliodynamics* 4(2): 241–280. DOI 10.21237/C7clio4221333. **[已核验]**（Crossref: Turchin Peter, *Cliodynamics* 4(2), 2013-12-31）
3. ✅ Turchin, P., Currie, T.E., Turner, E.A.L., Gavrilets, S. 2013. "War, space, and the evolution of Old World complex societies." *PNAS* 110(41): 16384–16389. DOI 10.1073/pnas.1308825110. (PMC3799307) **[已核验]**（Crossref: 四位作者与卷期页码完全一致）
4. ✅ Turchin, P. & Hoyer, D. 2023. "Empirically Testing and Refining Structural Demographic Theory: A Methodological Guide." SocArXiv. DOI 10.31235/osf.io/yrqw5. **[已核验]**（Crossref: Turchin Peter & Hoyer Daniel, 2023-06-23）
5. ✅ Goldstone, J.A. 2017. "Demographic Structural Theory: 25 Years On." *Cliodynamics* 8(2): 85–112. DOI 10.21237/c7clio8237450. **[已核验]**（Crossref: Goldstone Jack A., *Cliodynamics* 8(2), 2017）
6. ✅ Alexander, M. 2016. "Application of Mathematical Models to English Secular Cycles." *Cliodynamics* 7(1): 76–108. DOI 10.21237/C7clio7128325. **[已核验]**（Crossref: Alexander Michael A., *Cliodynamics* 7(1), 2016-06-28） — **本文逐字复现了 Turchin 2003 的 DF 模型与 Turchin & Korotayev 2006 的战争模型方程。**
7. ✅ Bennett, J. 2016. "Repeated Demographic-Structural Crises Propel the Spread of Large-scale Agrarian States throughout the Old World." *Cliodynamics* 7(1): 1–36. DOI 10.21237/C7clio7128530. **[已核验]**（Crossref 标题作 "...Throughout the Old World"，Bennett James, *Cliodynamics* 7(1), 2016）
8. ✅ Szulga, R.S. 2012. "Endogenous Population and Resource Cycles in Historical Hunter-Gatherer Economies." *Cliodynamics* 3(2): 234–270. DOI 10.21237/C7clio3213371.
9. ⬜ Turchin, P. 2003/2018. *Historical Dynamics: Why States Rise and Fall*. Princeton University Press. DOI 10.1515/9781400889310 / 10.23943/princeton/9780691180779.001.0001.
10. ⬜ Turchin, P. & Nefedov, S.A. 2009. *Secular Cycles*. Princeton University Press. DOI 10.1515/9781400830688.
11. ⬜ Goldstone, J.A. 1991/2016. *Revolution and Rebellion in the Early Modern World*. Routledge 重版 DOI 10.4324/9781315408620.（1992 年 *AHR* 97:1488 与 *Social Forces* 70:829 书评的元数据已验证）
12. ⬜ Turchin, P. 2009. "A theory for formation of large empires." *Journal of Global History* 4: 191–217. DOI 10.1017/S174002280900312X.
13. ⬜ Turchin, P. 2012. "Dynamics of political instability in the United States, 1780–2010." *Journal of Peace Research* 49: 577–591. DOI 10.1177/0022343312442078.
14. ⬜ Korotayev, A.V. 2005. "Comment on: Dynamical Feedbacks... by Peter Turchin." *Structure and Dynamics* 1(1). DOI 10.5070/SD911003266.
15. ✅ Turchin, P. & Korotayev, A. 2020. "The 2010 Structural-Demographic Forecast for the 2010–2020 Decade: A Retrospective Assessment." SocArXiv. DOI 10.31235/osf.io/7ahqn.

### 政体寿命与生存分析
16. ✅ Scheffer, M., van Nes, E.H., Kemp, L., Kohler, T.A., Lenton, T.M., Xu, C. 2023. "The vulnerability of aging states: A survival analysis across premodern societies." *PNAS* 120. DOI 10.1073/pnas.2218834120. (PMC10691336) **[已核验]**（Crossref: 六位作者一致，*PNAS* 120(48), 2023-11-20）
17. ✅ Ciliberti, S. 2025. "On the Life Cycle of Empires." *Cliodynamics* 16(2). DOI 10.21237/c7clio.53812. **[已修正: Ciliberti, S. 2025. "On the Life Cycle of Empires." *Cliodynamics* 16(2). Crossref 未登记页码，原写的 "16: 1–12" 的页码无法证实]**
18. ✅ Wand, T. 2024. "A Bayesian Approach to Survivorship Bias in Historical Data Analysis." *Cliodynamics* 15(1): 99–106. DOI 10.21237/c7clio15163477. **[已核验]**（Crossref: Wand Tobias, *Cliodynamics* 15(1), 2024-07-01）
19. ⬜ Arbesman, S. 2011. "The Life-Spans of Empires." *Historical Methods* 44(3): 127–129. DOI 10.1080/01615440.2011.577733. — τ≈220 的数值**只有 Ciliberti 2025 的转述**。
20. ⬜ Lu, P., Yang, H., Li, M., Zhang, Z. 2021. "The sandpile model and empire dynamics." *Chaos, Solitons & Fractals* 143: 110615. DOI 10.1016/j.chaos.2020.110615. — 22 个中国帝国的幂律结论**只有 Scheffer et al. 2023 的转述**。
21. ⬜ Taagepera, R. 1978. "Size and duration of empires: Systematics of size." *Social Science Research* 7: 108–127. DOI 10.1016/0049-089X(78)90007-8.
22. ⬜ Taagepera, R. 1978. "Size and duration of empires: growth-decline curves, 3000 to 600 B.C." *Social Science Research* 7: 180–196. DOI 10.1016/0049-089X(78)90010-8.
23. ⬜ Taagepera, R. 1979. "Size and Duration of Empires: Growth-Decline Curves, 600 B.C. to 600 A.D." *Social Science History* 3: 115–138. DOI 10.1017/S014555320002294X.
24. ⚠️ Gokmen, G. et al. 2020. 帝国兴衰数据库（168 个政治实体）。**Crossref 检索未找到；只有 Ciliberti 2025 的引用与其列出的数据来源 empires.wnvermeulen.com / Britannica / worldhistory.org。**

### 早期预警与韧性
25. ⬜ Downey, S.S., Haas, W.R., Shennan, S.J. 2016. "European Neolithic societies showed early warning signals of population collapse." *PNAS* 113: 9751–9756. DOI 10.1073/pnas.1602504113.（Significance 段落已验证）
26. ⬜ Scheffer, M., van Nes, E.H., Bird, D., Bocinsky, R.K., Kohler, T.A. 2021. "Loss of resilience preceded transformations of pre-Hispanic Pueblo societies." *PNAS* 118. DOI 10.1073/pnas.2024397118.
27. ⬜ Schunck, F., Wiedermann, M., Heitzig, J., Donges, J.F. 2024. "A Dynamic Network Model of Societal Complexity and Resilience Inspired by Tainter's Theory of Collapse." *Entropy* 26: 98. DOI 10.3390/e26020098.

### 中国与东亚
28. ✅ Orlandi, G., Hoyer, D., Zhao, H., Bennett, J.S., et al. 2023. "Structural-demographic analysis of the Qing Dynasty (1644–1912) collapse in China." *PLOS ONE* 18(8): e0289748. DOI 10.1371/journal.pone.0289748. **[已核验]**（Crossref: Orlandi/Hoyer/Zhao/Bennett/Benam/Kohn, *PLOS ONE* 18(8): e0289748, 2023-08-18）
29. 🟡 Chu, C.Y.C. & Lee, R.D. 1994. "Famine, revolt, and the dynastic cycle: Population dynamics in historic China." *Journal of Population Economics* 7: 351–378. DOI 10.1007/BF00161472.（摘要已验证；1997 勘误 DOI 10.1007/s001480050040）**[已核验]**（Crossref: Chu C.Y. Cyrus & Lee Ronald D., *Journal of Population Economics* 7(4): 351–378, 1994-11；Crossref 标题只作 "Famine, revolt, and the dynastic cycle"）
30. ✅ Jia, R. 2011. "Weather Shocks, Sweet Potatoes and Peasant Revolts in Historical China." HiCN Working Paper 93.（工作论文全文已下载）→ 期刊版：2013, *The Economic Journal* 124: 92–118. DOI 10.1111/ecoj.12037. ⬜ **[已核验]**（HiCN WP93 PDF 链接现仍可下载；期刊版 Crossref: Jia Ruixue, *The Economic Journal* 124(575): 92–118，Crossref 登记日期 2013-07，纸本期号属 2014）
31. 🟡 Zhang, D.D., Jim, C.Y., Lin, G.C-S., He, Y-Q., Wang, J.J., Lee, H.F. 2006. "Climatic Change, Wars and Dynastic Cycles in China Over the Last Millennium." *Climatic Change* 76: 459–477. DOI 10.1007/s10584-005-9024-z.（摘要已验证）
32. 🟡 Zhang, D.D., Zhang, J., Lee, H.F., He, Y-q. 2007. "Climate Change and War Frequency in Eastern China over the Last Millennium." *Human Ecology* 35: 403–414. DOI 10.1007/s10745-007-9115-8.（摘要已验证）
33. ✅ Zhang, D.D., Lee, H.F., Wang, C., Li, B., Pei, Q., Zhang, J., An, Y. 2011. "The causality analysis of climate change and large-scale human crisis." *PNAS* 108: 17296–17301. DOI 10.1073/pnas.1104268108. (PMC3198350) **[已核验]**（Crossref: *PNAS* 108(42): 17296–17301, 2011）
34. ⬜ Zhang, D.D., Lee, H.F., Wang, C., Li, B., Zhang, J., Pei, Q., Chen, J. 2011. "Climate change and large-scale human population collapses in the pre-industrial era." *Global Ecology and Biogeography* 20: 520–531. DOI 10.1111/j.1466-8238.2010.00625.x.
35. ⬜ Bai, Y. & Kung, J.K. 2011. "Climate Shocks and Sino-nomadic Conflict." *Review of Economics and Statistics* 93: 970–981. DOI 10.1162/REST_a_00106.
36. ⬜ Chen, Q. 2014/2015. "Climate shocks, dynastic cycles and nomadic conquests: evidence from historical China." *Oxford Economic Papers* 67: 185–204. DOI 10.1093/oep/gpu032.
37. ⬜ Kung, J.K. & Ma, C. 2014. "Can cultural norms reduce conflicts? Confucianism and peasant rebellions in Qing China." *Journal of Development Economics* 111: 132–149. DOI 10.1016/j.jdeveco.2014.08.006.
38. ⬜ Pei, Q. & Zhang, D.D. 2014. "Long-term relationship between climate change and nomadic migration in historical China." *Ecology and Society* 19(2). DOI 10.5751/ES-06528-190268.
39. ⬜ Yin, W. 2019. "Climate Shocks, Political Institutions, and Nomadic Invasions in Early Modern East Asia." *Journal of Conflict Resolution* 64: 1043–1069. DOI 10.1177/0022002719889665.
40. ⬜ Ko, C.Y., Koyama, M., Sng, T-H. 2018. "Unified China and Divided Europe." *International Economic Review* 59: 285–327. DOI 10.1111/iere.12270.
41. ⬜ Ge, Q., Zheng, J., Fang, X., Man, Z., et al. 2003. "Winter half-year temperature reconstruction for the middle and lower reaches of the Yellow River and Yangtze River, China, during the past 2000 years." *The Holocene* 13: 933–940. DOI 10.1191/0959683603hl680rr.
42. ⚠️ Lee, J.S. 1931. 中国内战频次统计（Turchin 2005 使用的主要中国战争数据源）。**未独立验证。**
43. ⚠️ Zhao, W. & Xie, S. 1988. 中国人口史估计（Turchin 2005 使用的主要中国人口数据源）。**未独立验证。**

### 批评与方法论
44. ✅ Slingerland, E., Monroe, M.W., Sullivan, B., Walsh, R.F., et al. 2020. "Historians Respond to Whitehouse et al. (2019), 'Complex Societies Precede Moralizing Gods Throughout World History'." *Journal of Cognitive Historiography* 5: 124–141. DOI 10.1558/jch.39393. **[已核验]**（Crossref: *Journal of Cognitive Historiography* 5(1-2): 124–141, 2020-11-06）（预印本 DOI 10.31234/osf.io/2amjz，已下载）
45. 🟡 Beheim, B., Atkinson, Q.D., Bulbulia, J., Gervais, W., et al. 2021. "Treatment of missing data determined conclusions regarding moralizing gods." *Nature* 595(7866): E29–E34. DOI 10.1038/s41586-021-03655-4. **[已核验]**（Crossref: Beheim/Atkinson/Bulbulia/Gervais/Gray/Henrich, 2021-07-07；伴随撤稿说明 10.1038/s41586-021-03656-3 亦已核验，*Nature* 595: 320）（摘要全文已读）
46. ⬜ Whitehouse, H., François, P., Savage, P.E., Currie, T.E., et al. 2021. "Retraction Note: Complex societies precede moralizing gods throughout world history." *Nature* 595: 320. DOI 10.1038/s41586-021-03656-3.
47. ⬜ Whitehouse, H., et al. 2019. "RETRACTED ARTICLE: Complex societies precede moralizing gods throughout world history." *Nature* 568: 226–229. DOI 10.1038/s41586-019-1043-4.
48. ✅ Madge, J., Colavizza, G., Hetherington, J., Guo, W., Wilson, A. 2019. "Assessing Simulations of Imperial Dynamics and Conflict in the Ancient World." *Cliodynamics* 10(2): 99–114. DOI 10.21237/C7clio10245282. **[已核验]**（Crossref: Madge/Colavizza/Hetherington/Guo/Wilson, *Cliodynamics* 10(2), 2019-12-30）
49. ✅ Lempert, D. 2018. "Futurology Needs to Focus on Measurable Variables, Causality and Social Structural Models and Learn from Past Mistakes: A Response to 'A History of Possible Futures: Multipath Forecasting of Social Breakdown, Recovery, and Resilience.'" *Cliodynamics* 9(2). DOI 10.21237/c7clio9243669. **[已修正: 原引题名被截断，Crossref 完整题名含副标题 "A Response to…"；Lempert David, *Cliodynamics* 9(2), 2018-12-31，Crossref 未登记页码]**
50. ⬜ Turchin, P. 2018. "Response to Lempert: Holism versus Systems Analysis." *Cliodynamics* 9(2). DOI 10.21237/c7clio9243672.
51. ⬜ Goldstone, J.A. 2018. "Social Structure in the Explanation and Prediction of Social Discontinuities: A Response to Lempert's Critique of the MFP." *Cliodynamics* 9(2). DOI 10.21237/c7clio9243671.
52. ✅ Turchin, P. 2025. "Bayesian phylogenetic analyses cannot be used to test hypotheses about the evolution of large-scale complex societies during the Holocene." SocArXiv. DOI 10.31235/osf.io/xenpv. **[已核验]**（Crossref 版本化 DOI 10.31235/osf.io/xenpv_v1，Turchin, 2025-12-19）
53. ⬜ Opie, C. & Atkinson, Q.D. 2025. "State formation across cultures and the role of grain, intensive agriculture, taxation and writing." *Nature Human Behaviour*. DOI 10.1038/s41562-025-02365-5. **[已核验]**（本次核验补上：Crossref: Opie Christopher & Atkinson Quentin D., *Nature Human Behaviour* 10(1): 156–163, 2025-11-25；此前简报注明的"未检索到 Crossref 记录"已作废）
54. ⬜ Granger, C.W.J. & Newbold, P. 1974. "Spurious regressions in econometrics." *Journal of Econometrics* 2(2): 111–120. DOI 10.1016/0304-4076(74)90034-7. **[已核验]**（Crossref: Granger C.W.J. & Newbold P., 1974-07）
55. ⬜ Phillips, P.C.B. 1986. "Understanding spurious regressions in econometrics." *Journal of Econometrics* 33: 311–340. DOI 10.1016/0304-4076(86)90001-1.
56. ⬜ Hsiang, S.M., Burke, M., Miguel, E. 2013. "Quantifying the Influence of Climate on Human Conflict." *Science* 341. DOI 10.1126/science.1235367.
57. ⬜ Buhaug, H., Nordkvelle, J., Bernauer, T., Böhmelt, T., et al. 2014. "One effect to rule them all? A comment on climate and conflict." *Climatic Change* 127: 391–397. DOI 10.1007/s10584-014-1266-1.
58. ⬜ Richerson, P.J. 2017. "A Dynamic Analysis of American Socio-Political History. A Review of *Ages of Discord*." *Cliodynamics* 8(2). DOI 10.21237/c7clio8237156.

### 数据库与工具
59. ⬜ Turchin, P., Brennan, R., Currie, T., Feeney, K., et al. 2015. "Seshat: The Global History Databank." *Cliodynamics* 6(1). DOI 10.21237/C7clio6127917.
60. ⬜ Turchin, P., et al. 2017/2018. "Quantitative historical analysis uncovers a single dimension of complexity that structures global variation in human social organization." *PNAS* 115. DOI 10.1073/pnas.1708800115.
61. ⬜ Bennett, J., Mutch, S., Toleffson, K., Chalstrey, E., et al. 2024. "Cliopatria — A geospatial database of world-wide political entities from 3400BCE to 2024CE." SocArXiv. DOI 10.31235/osf.io/24wd6. **[已核验]**（Crossref: Bennett James S/Mutch Erin/Toleffson Andrew/Chalstrey Ed 等，2024-08-23）
62. ✅ Cliopatria 数据仓库 README（>1600 实体，约 14K 行，EPSG:4326/6933）。https://github.com/Seshat-Global-History-Databank/cliopatria **[已核验]**（GitHub API: 仓库存在，描述与简报一致，许可证 SPDX = NOASSERTION）
63. ✅ GUARD 源码（MIT），`guard/parameters.py`、`guard/community.py`、`guard/polity.py`。https://github.com/alan-turing-institute/guard **[已核验]**（GitHub API: alan-turing-institute/guard，描述 "Simulating Imperial Dynamics and Conflict in the Ancient World"，MIT 许可，tag v0.15 存在，建库 2018-12-17；作者归属 Madge 等人依据配套论文 Cliodynamics 10(2)）
64. ⬜ Turchin, P. 2018. "Fitting Dynamic Regression Models to Seshat Data." *Cliodynamics* 9(1). DOI 10.21237/c7clio9137696.
65. ⬜ Turchin, P., Hoyer, D., Bennett, J., Basava, K., et al. 2020. "The Equinox2020 Seshat Data Release." *Cliodynamics* 11(1). DOI 10.21237/c7clio11148620.
66. ⬜ Turchin, P., et al. 2025. "The Polaris2025 Seshat Data Release." *Cliodynamics*. DOI 10.21237/c7clio.50838.

### 相关但未深读（后续可挖）
67. ⬜ Nefedov, S. 2013. "Modeling Malthusian Dynamics in Pre-Industrial Societies." *Cliodynamics* 4(2). DOI 10.21237/c7clio4221335.（已下载，未读）
68. ⬜ Turchin, P., Witoszek, N., Thurner, S., Garcia, D., et al. 2018. "A History of Possible Futures: Multipath Forecasting of Social Breakdown, Recovery, and Resilience." *Cliodynamics* 9(2). DOI 10.21237/c7clio9242078.
69. ⬜ "State Crisis Theory: A Unification of Institutional, Socio-ecological, Demographic-structural, World-systems..." *Cliodynamics* 15 (2024). DOI 10.21237/c7clio15163324.
70. ⬜ "Circumscription Theory of the Origins of the State: A Cross-Cultural Re-Analysis." *Cliodynamics* 7(2) (2016). DOI 10.21237/c7clio7232817.（Carneiro 环境限制理论的定量再检验，对我们的"边界制造周期"假说直接相关）
71. ⬜ "The Exchequer's Guide to Population Ecology and Resource Exploitation in the Agrarian State." *Cliodynamics* 9 (2018). DOI 10.21237/c7clio9239095.
72. ⬜ "Human social complexity was significantly lower during climate cooling events of the past 10 millennia." *Cliodynamics* 12 (2021). DOI 10.21237/c7clio12054304.
73. ⬜ "The Silk Roads: a Mathematical Model." *Cliodynamics* 5 (2014). DOI 10.21237/c7clio5125309.
74. ⬜ "Modeling the large-scale demographic changes of the Old World." *Cliodynamics* 6 (2015). DOI 10.21237/c7clio6127603.
75. ⬜ "Agricultural productivity in past societies: Toward an empirically informed model." *Cliodynamics* 6 (2015). DOI 10.21237/c7clio6127473.
76. ⬜ Orlandi, G. & Turchin, P. 2025. "A Structural-Demographic Analysis of Japan: 1945–2050." SocArXiv. DOI 10.31235/osf.io/trf2z.（东亚第二个 SDT 案例）

---

## 附：给内核设计者的一页速查

**可以直接抄的**（有参数、有开源实现、有独立复现）：
- Turchin 2013 PNAS 的空间战争/文化多层选择规则与全套参数（§2.5，GUARD 源码）
- 政体解体概率式（无年龄项）：`δ₀ + max(0, δ_s·|P| − δ_a·ū)`
- DF 模型作为**单政体的宏观一致性检查器**（不是内核），6 参数，英格兰误差 4.6%
- 清代的 EMP 操作化：数职位、数候选人
- Zhang 2011 的气候→危机 DAG 与滞后区间

**可以抄结构但必须自己重新标定的**：
- 相对工资的 Cobb-Douglas 型式（含制度降级链）
- 精英流动 `μ₀(w₀/w − 1)`
- 农村→城市迁移的 θ=5 非线性

**绝对不要抄的**：
- 任何带政体年龄的规则
- 乘法式 PSI 作为事件触发器
- "周期长度 = 200–300 年"作为参数

**要拿去做校准（而不是拿来做规则）的**：
- 政体寿命分布（三个互相矛盾的版本，全都要比一遍）
- 帝国规模的归一化生命周期曲线（logistic 上升 → 峰值在生命中点 → 短命者平台、长命者末段衰退）
- 不稳定序列的功率谱（英格兰主导波长 ≈79 年）
- 帝国密度的空间分布（距草原距离 + 农业历史 + 海拔 → 42% 方差）
