# 疾病、流行病与人口冲击（slug: `epidemics-disease`）

**范围一句话**：把"疾病"从一个人口曲线调节旋钮，改造成一个由**病原体属性 × 宿主密度 × 交通网络 × 气候包络 × 储存宿主生态**共同决定、可追溯、可反事实重放的子系统；给出可直接实现的方程、参数量级、数据来源，以及本领域最容易犯的建模错误。

**检索日期**：2026-09-10。检索工具受限说明见文末第 10 节开头。

---

## 1. 本简报要回答的问题

1. 一个"既便宜又不失真"的疫病子系统应该长什么样？（答案在 §3 的 M1–M12 与 §3.13 的三层成本架构）
2. 哪些量是**病原体的属性**，哪些量是**世界状态的函数**？（R0 不是病原体常数，见 §2.3、§8.2）
3. 疾病能不能在前城市社会里存在？什么样的病只有到了某个人口/密度门槛才可能出现？（临界社区规模 CCS 与麻疹起源，§2.1、§2.2、§4）
4. 大疫的死亡率、恢复时间尺度、复发周期的真实量级是多少？（§4）
5. 疫病如何被贸易、军队、气候搬运？（§2.5、§3 的 M5、§4）
6. 疫病之后经济与制度会发生什么？哪些是机制、哪些只是欧洲的一次性结果？（§2.7、§8.7）
7. 中国与东亚史料能给我们什么，又骗我们什么？（§6）
8. **如何避免疫病变成人口曲线的"平衡器"（隐藏剧情）**？（§8.1 与 §3.14 的可执行诊断）

---

## 2. 已有成熟模型与理论

### 2.1 Bartlett 的临界社区规模（Critical Community Size, CCS）

- **核心机制**：一个只感染人、康复后终身免疫的急性传染病，其本地存续依赖于新易感者（出生）的补充速率。当社区太小，流行高峰后的"低谷"里感染者数量的整数性 + 人口统计学随机性会让感染链断掉（fade-out）。存在一个人口规模阈值，低于它疾病无法本地持续存在，只能靠外部反复输入。
- **形式化程度**：完全形式化（随机 SEIR / TSIR，Monte-Carlo 或主方程）。
- **状态变量**：每个斑块的 S, E, I, R（整数）、出生率、季节强迫相位。
- **参数与数值**：Conlan & Grenfell 2007 全文明确写作 "CCS of 250–500 000 for urban communities"，其 SEIR 模型用潜伏期 8 天、传染期 5 天。**关键的非直觉结论**：CCS 对出生率**非单调**——中等出生率（约 15–30‰）由于把动态推入双年周期（biennial），谷底更低，反而**降低**存续性；"a doubling of the birth rate leads to a fivefold reduction in the CCS"；而在高出生率地区，接种疫苗可能把动态从年周期推回双年周期，从而**提高** CCS。（Conlan & Grenfell 2007, Proc R Soc B, DOI 10.1098/rspb.2006.0030，本次检索读到全文）
- **适用范围**：免疫终身、潜伏+传染期为天量级、频率依赖传播的急性儿童病（麻疹、腮腺炎、百日咳、天花在某种近似下）。
- **已知局限**：Keeling & Grenfell 1997（Science 275:65–67）指出，当时的随机模型**高估**了观测到的 CCS，即模型比现实更容易灭绝；把传染期从指数分布改成更接近生物学的分布（低方差）后才拟合上。**含义：CCS 对"传染期分布形状"这种看似细枝末节的假设高度敏感**，任何用指数分布传染期的偷懒实现都会系统性高估 CCS。
- **对照数值**：美国腮腺炎（1923–1932）CCS 估计在 365,583–781,188 之间，上限可达 3,376,438（Pomeroy et al. 2023, Epidemics, DOI 10.1016/j.epidem.2023.100700）。尼日尔麻疹的 CCS 约 750,000（Blake et al. 2020, J R Soc Interface, PMC7482562 引用）。**所以"CCS ≈ 25 万"不是普适常数，而是 20 世纪英格兰-威尔士人口学条件下的值。**

### 2.2 R0 / 群体免疫阈值（HIT）

- **核心机制**：R0 = 一个典型病例在完全易感人群中平均产生的二代病例数；HIT = 1 − 1/R0。
- **形式化**：完全形式化。
- **参数**：麻疹常被引作 12–18；但 Guerra et al. 2017（Lancet Infect Dis 17:e420–e428）系统综述筛出 18 项研究、58 个估计后的结论是 "R0 estimates vary more than the often cited range of 12–18"，并建议各地用**本地数据**计算。另一方面，Xia/Bjørnstad/Grenfell 系的 TSIR 在英格兰-威尔士拟合出的麻疹 R0 被 Bharti et al. 2008 全文写作 "R0 ≈ 30"。这两个数不矛盾（不同定义、不同拟合口径），但直接说明 R0 是**估计流程的产物**。
- **已知局限**：Delamater et al. 2019（EID 25(1):1–4）明确列举误解：R0 不是病原体常数、不是速率、不是严重度指标、"cannot be modified through vaccination campaigns"，且 "modeled R0 values are dependent on model structures and assumptions"。
- **对本项目的直接后果**：**不要在病原体表里存一个 R0 常数然后到处用。** 存"接触-单位传播概率 + 传染期"，让 R0 由世界状态（密度、居住形态、卫生、季节）算出来。见 §3 的 M1。

### 2.3 Metapopulation + 引力耦合（gravity model）与层级行波

- **核心机制**：现实中的疾病空间传播不是均匀扩散波，而是"大城市 → 卫星小镇"的**层级传播**：大城市维持内生流行，向小镇发射"火花"（infective sparks）。Grenfell, Bjørnstad & Kappey 2001（Nature 414:716–723）用小波相位分析在英格兰-威尔士麻疹数据里证实了这种反复出现的层级行波，并指出"host population structure 的空间层级是这些行波的前提"。
- **形式化**：完全形式化。TSIR（离散时间、双周步长，双周 ≈ 麻疹世代间隔）+ 引力耦合。
- **可用的函数形式与拟合参数**（Xia, Bjørnstad & Grenfell 2004, Am Nat 164:267–281；参数值由 Bharti et al. 2008 全文复述）：
  斑块 j→i 的期望流动 ∝ Θ · N_i^{τ1} · N_j^{τ2} / D_ij^{ρ}，
  拟合值 **ρ = 1, τ1 = 1, τ2 = 1.5, Θ = 4.54×10⁻⁹ km·person^{−1.5}·biweek⁻¹**。
- **已知局限**：Bharti et al. 2008 发现该模型在**海岸城市**系统性低估存续性（"edge effect"），因为它按欧氏距离和周围人口算接触数，而海岸城镇少了一半陆地邻居。修正办法是把海岸城镇的人均接触数拉回内陆水平。**对本项目极其重要**：任何以欧氏距离为基础的耦合项在山脉、海岸、沙漠边缘都会系统性出错，必须改用"路网/水网可达性"。

### 2.4 鼠疫的多路径模型（鼠-蚤 / 人体外寄生虫 / 肺鼠疫）

- **核心机制**：历史鼠疫的传播路径至今未定论。三类模型：(a) 经典鼠-蚤-人（需要鼠类流行病 epizootic 崩溃后蚤转向人）；(b) 人体外寄生虫（人蚤、体虱）人-人传播；(c) 原发性肺鼠疫人-人气溶胶传播。
- **形式化**：完全形式化，且有贝叶斯拟合的真实历史死亡曲线。
- **关键结果**（Dean et al. 2018, PNAS, PMC5819418，本次读到全文）：对九次欧洲疫情做贝叶斯模型比较，人体外寄生虫模型的拟合优于肺鼠疫与鼠-蚤模型；其 R0 = **1.48–1.91**（Givry 1348: 1.82；Florence 1400: 1.76；Barcelona 1490: 1.91；London 1563: 1.64；Eyam 1666: 1.48；Gdansk 1709: 1.64；Stockholm 1710: 1.75；Moscow 1771: 1.79；Malta 1813: 1.57）；肺鼠疫模型 R0 ≈ 1.04–1.10；鼠-蚤模型 1.24–2.04。
- **反方**：Benedictow 2019（Can J Infect Dis Med Microbiol, DOI 10.1155/2019/1542024）系统批评把 SIR/SEIR 套到历史鼠疫上的方法论，主张鼠疫本质上仍是鼠-鼠蚤传播，认为可以"invalidate the human ectoparasite hypothesis"。**这是活的争议，不要装作已经解决。**
- **另一个独立拟合**（Didelot, Whittles & Hall 2017, J R Soc Interface, PMC5493801，开罗 1801）：鼠间 R0 = 2.85 [1.82, 3.95]；鼠→人 β_h = 1.45×10⁻²；人→人只占 18% [1%, 41%]；鼠群崩溃约 100 天；25 万人口里约 5000 人死（约 2%）。**注意这与 Dean 的结论方向相反**（此处人-人只占少数）。

### 2.5 交通网络 / 贸易路线作为传播算子（历史尺度上最强的空间预测因子）

- **核心机制**：前工业欧洲鼠疫的空间格局主要由主要贸易路线与可通航河流决定，而非由本地生态决定。
- **形式化**：半形式化（回归 + 机制叙述），但结论可以直接转成模拟里的边权。
- **硬结果**：
  - Yue, Lee & Wu 2016（Sci Rep, DOI 10.1038/srep34867）：AD1347–1760 的 **5,559** 次鼠疫暴发中 **95.5% 发生在可通航河流 10 km 以内**；河宽每增加 100 m，研究期内多 9 次暴发；城市到河的距离每缩短 1 km，多 0.96 次暴发。
  - Yue, Lee & Wu 2017（Sci Rep, DOI 10.1038/s41598-017-13481-2，PMC5636801）：**6,656** 条地理编码的鼠疫暴发记录（1347–1760），OLS 中"到最近主要贸易路线的对数距离"系数约 **−6.18**（模型 2–6 在 −6.09 至 −6.29 之间稳定显著），R² = 0.41–0.44。作者提出的机制是：**从永久疫源地经海港输入 → 沿主要贸易路线到贸易节点 → 节点成为新的次级震中 → 沿可通航河流向内陆散点渗透**。同一分析还从"暴发数与到港口距离负相关"反推**欧洲内陆不存在永久疫源地**。
  - Stenseth et al. 2022（PNAS, DOI 10.1073/pnas.2209816119）独立支持"历史与现代欧洲不存在持久自然疫源地"。
- **对本项目的含义**：**鼠疫类疾病在舞台上不应该"自己长出来"，它应该有固定的储存宿主疫源地（地图特征），只有当疫源地活跃 + 存在通往人类世界的高权重贸易边时才输出。** 这是把大疫从"随机事件"变成"因果链事件"的核心。

### 2.6 气候-媒介包络（为什么疫病有季节性和纬度梯度）

- Krauer et al. 2021（Proc R Soc B, PMC8277479）拟合第二次大流行的季节性：**只有在 11.7 °C（95% CI 9.8–13.4）到 21.5 °C（20.3–22.5）之间才预测到正的流行增长，最大增长在 17.3 °C**；平均温度每低 1 °C，流行高峰推迟 1.4 周（β = −1.39, SE = 0.232, p < 0.01），该温度模型解释了高峰时点方差的 44%；存在纬度梯度（南部如 Alexandria、Barcelona 春季峰，北部如 London、Vienna 秋季峰；中位峰值在第 35 周）。
- Xu et al. 2019（PNAS 116:11833–11838）在第三次大流行的全球尺度上发现：**低人口密度 + 高比例牧地/林地的区域扩散最快**（与直觉相反）；温度与扩散速度呈 **U 形，最小值在 20 °C 附近**；降水与扩散速度正相关；不同谱系（2.MED、1.ORI3）扩散显著更快。
- **含义**：媒介传播病的传播率必须是温度/湿度的**非单调函数**，且"人口密度高 ⇒ 传播快"这条直觉对媒介病可能反号。

### 2.7 大疫的经济与制度后果（黑死病文献）

- Jedwab, Johnson & Koyama 2022（J Econ Lit 60:132–178, DOI 10.1257/jel.20201639）的摘要（本次在 AEA 页面读到）：黑死病是欧洲史上最大的人口冲击，是对经济的"plausibly exogenous shock"；短期"Wages and per capita income rose"；长期后果包括欧洲相对亚洲与中东的增长（Great Divergence）、欧洲经济地理向西北转移（Little Divergence）、**西欧农奴制削弱**、宗教制度权威下降、国家能力增强。
- Pamuk 2007（Eur Rev Econ Hist 11:289–317, DOI 10.1017/s1361491607002031）与 Voigtländer & Voth（Rev Econ Stud 80:774–811, DOI 10.1093/restud/rds034，Crossref 记为 2012 年上线）是这一支的两个支柱（本次只核到书目元数据，未读正文）。
- Jedwab, Johnson & Koyama 2019（J Econ Growth 24:345–395, DOI 10.1007/s10887-019-09167-1）"Negative shocks and mass persecutions: evidence from the Black Death"——**疫病后的替罪羊迫害**也是一条可建模的社会反应链（本次只核到元数据）。
- **必须警惕的不对称**："黑死病 ⇒ 工资上升 ⇒ 农奴制瓦解"只在西欧成立；同一冲击在东欧的结果被广泛认为相反（第二次农奴制）。**因此这不能写成规则，只能写成一个由精英协调能力/劳动力外部选择决定的博弈结果。**（此不对称本身我在本次检索中未取得直接文献，见 §9 D-2。）

### 2.8 人畜共患病起源（Diamond 论证及其批评）

- Wolfe, Dunavan & Diamond 2007（Nature 447:279–283）摘要（本次读到）：许多主要人类传染病是农业起源之后才出现的"新"病；温带与热带的答案不同（温带更依赖家畜、热带更依赖野生灵长类）；提出病原体从"只感染动物"到"只感染人"的**五个中间阶段**。
- 批评：Pearce-Duvet 2006（Biol Rev 81:369–382, DOI 10.1017/s1464793106007020，本次只核到书目元数据）系统质疑"农业与家畜"作为主要来源的份额。
- 支持性证据：Morand et al. 2014（Infect Genet Evol 24:76–81）——被驯化动物与人类共享更多传染病并作为病原体放大器；Bendrey et al. 2025（Evol Med Public Health 13(1):344–354, DOI 10.1093/emph/eoaf029）——早期畜牧创造了让病原体"invade and be sustained in both populations"的生态条件；Rahman et al. 2020（Microorganisms 8(9):1405）——"More than 60% of human pathogens are zoonotic in origin"。
- **最硬的一条时间约束**：Düx et al. 2020（Science, DOI 10.1126/science.aba9411, PMC7713999）用古基因组把**麻疹病毒与牛瘟病毒的分歧定在公元前 6 世纪**，"possibly coinciding with the rise of large cities"。**这直接给了模拟一个可执行的规则：麻疹型（终身免疫、纯人际、需 CCS 级宿主池）的病原体在城市出现之前不该存在。**

---

## 3. 可直接用于本项目的机制清单

> 记号：斑块 = 一个聚落或一个地理单元；tick = 世界主循环步长。所有下述机制都要求写入因果日志（谁、何时、从哪里输入、当时的 R_eff 是多少）。

### M1. 病原体是数据表，不是脚本（rules_math）
- **输入 → 输出**：病原体记录 + 当地世界状态 → 该斑块该 tick 的传播率与病死率。
- **数据结构**（建议字段）：
  `{transmission_mode ∈ {respiratory, faecal_oral, vector_flea, vector_mosquito, direct_contact, sexual}, `
  `unit_transmission_prob p, latent 1/σ, infectious 1/γ, immunity_duration (∞ | 年), `
  `IFR_by_age[], frailty_sensitivity ω, reservoir_species | none, `
  `climate_envelope {T_lo, T_opt, T_hi, moisture}, emergence_prereqs}`
- **算法草图**：`R0_local = p · c(density, dwelling, hygiene) · (1/γ)`，其中 c 是本地有效接触率。**表里不存 R0。**
- **时间尺度**：静态（病原体一旦存在其属性不变，除非发生演化事件）。**空间粒度**：全局。
- **证据等级**：B（结构来自标准建模实践；"R0 非常数"由 Delamater 2019、Guerra 2017 支持）。
- **为什么这样简化**：如果 R0 是常数，那么"城市化提高疾病负担"这件事就必须由建模者手工塞进去，涌现就死了。

### M2. 斑块级随机 SEIR/SEIRS（rules_math）
- **输入 → 输出**：(S,E,I,R)_i、β_i(t)、输入压力 ι_i → 下一 tick 的 (S,E,I,R)_i 与死亡数。
- **数学草图**（离散 tick，τ-leap）：
  `λ_i(t) = β_i(t) · (I_i + ι_i) / N_i`
  `新感染 ~ Binomial(S_i, 1 − exp(−λ_i Δt))`
  `E→I ~ Binomial(E_i, 1 − exp(−σ Δt))`；`I→(R 或 D) ~ Binomial(I_i, 1 − exp(−γ Δt))`，死亡按 IFR 分流。
  `β_i(t) = R0_local · γ · s(t)`，季节项 `s(t) = 1 + α cos(2π(t − φ)/T)`。
- **必须用整数随机过程**，不能用 ODE：CCS、fade-out、burnout 都是随机性的产物（Britton et al. 2015, Epidemics, DOI 10.1016/j.epidem.2014.05.002；Parsons et al. 2024, PNAS, DOI 10.1073/pnas.2313708120 讨论随机 SIR 的 burnout 概率）。
- **传染期分布不要用指数分布**：用 Erlang/Gamma（把 I 分成 k 个子室）。理由是 Keeling & Grenfell 1997 的核心结论——指数传染期会系统性高估 CCS。建议 k = 3–5。
- **时间尺度**：日到周。**空间粒度**：单个聚落（城市单独一格；乡村按 20–50 km 聚合，见 §9 D-1）。
- **证据等级**：A（模型族与参数量级有大量实证支持）。

### M3. CCS 让它涌现，不要硬编码（rules_math）
- **输入 → 输出**：斑块人口 + 出生率 + 季节强迫 → 疾病是否本地持续（自然结果，不是规则）。
- **做法**：因为 M2 是整数随机过程，`I_i = 0` 会自然发生，CCS 就自动出现。**禁止写 `if city.pop > 250000: disease.endemic = True`。**
- **校准目标（不是实现）**：在类英格兰-威尔士人口学下，麻疹型病原体的 CCS 应落在 25–50 万（Conlan & Grenfell 2007 全文原话 "CCS of 250–500 000 for urban communities"）；在高出生率设定下可以显著更低或更高——CCS 对出生率**非单调**，"doubling of the birth rate leads to a fivefold reduction in the CCS"，但中等出生率区间因双年周期反而更易灭绝。
- **证据等级**：A（机制 + 数值范围都有来源）。
- **为什么这样简化**：硬编码门槛会让"城市规模跨过 25 万"变成一个剧情开关；涌现版本会自然产生"疫病在某个世纪反复烧回来又熄灭"的历史纹理。

### M4. 交通网络耦合（取代欧氏距离引力）（rules_math）
- **输入 → 输出**：路网/水网/海运边 + 各斑块 I → 输入压力 ι_i。
- **数学草图**：`ι_i = Σ_j θ_ij · I_j`，
  `θ_ij = Θ · N_i^{τ1} · N_j^{τ2} · w_ij / (TravelTime_ij)^{ρ}`
  基线取 Xia et al. 2004 的 **ρ=1, τ1=1, τ2=1.5**（Θ 必须重标定，见 §9 D-3），`w_ij` 是该边上的实际货运/人流量（由经济子系统给出，不是常数）。
- **为什么用旅行时间而不是欧氏距离**：Bharti et al. 2008 的海岸 "edge effect" 证明欧氏几何在边界地形上系统性出错；Yue 2016/2017 证明前工业时代 95.5% 的鼠疫暴发在可通航河流 10 km 内、且到贸易路线的对数距离是主导变量。
- **军队与围城**：行军路线是**临时的高权重边**，围城是**临时的高密度斑块**（β 上调）。历史依据是 Green & Fancy 2025（Medical History, DOI 10.1017/mdh.2024.29）关于 1257–58 蒙古军自天山运粮入伊拉克、1258 大马士革、1260 马尔丁的叙述链。
- **时间尺度**：与贸易子系统同步（月/季）。**空间粒度**：边。
- **证据等级**：A（空间模式），B（把它接到旅行时间上的具体函数形式）。

### M5. 储存宿主疫源地（reservoir focus）作为地图特征（rules_math）
- **输入 → 输出**：生态区的啮齿类动物群 + 气候 → 疫源地活跃度 → 溢出到人类的危险率。
- **数学草图**：疫源地 f 有自己的鼠类 SIR 与蚤指数 x：
  `spillover_rate(i) = κ · I_rodent(f) · x(f) · contact(i, f) · g(T)`，
  `g(T)` 用 Krauer 2021 的温度窗：在 [11.7, 21.5] °C 外趋近 0，峰在 17.3 °C。
- **关键设计**：疫源地是**固定的地理特征**（天山型高原草原、云南型山地），人类世界内部没有永久疫源地（Yue 2017 的距港口负相关推论；Stenseth et al. 2022 直接结论）。因此大疫的"起点"永远可以追溯到一次具体的生态-贸易耦合事件，而不是"随机降临"。
- **历史模板（只作校准，不作剧本）**：Spyrou et al. 2022（Nature 606:718–724）把黑死病主谱系的 MRCA 定位到吉尔吉斯斯坦伊塞克湖 Kara-Djigach / Burana 墓地，碑铭直书 1338–1339 年"pestilence"，并支持天山地区**本地涌现**。
- **证据等级**：A（疫源地存在与欧洲无疫源地），B（溢出率的具体函数）。

### M6. 脆弱性（frailty）结构化死亡，而不是统一死亡率（rules_math）
- **输入 → 输出**：个体/队列的年龄 a 与脆弱度 z + 病原体 IFR 曲线 → 死亡概率；并**更新幸存人群的 z 分布**。
- **数学草图**：`h(a, z) = z · IFR_base · f_age(a)`，`z ~ Gamma(k, 1/k)`（均值 1）。疫后幸存者 z 的分布被向下截断 ⇒ 短期死亡率下降。
- **实证依据**：
  - DeWitte & Wood 2008（PNAS 105:1436–1441）：黑死病**不是**无差别杀人，"selective with respect to frailty, although probably not as strongly selective as normal mortality"。
  - DeWitte 2014（PLoS ONE 9:e96513）：黑死病之后伦敦人群的生存率与死亡风险显著改善——**选择效应 + 生活水平改善**的联合结果。
  - DeWitte 2015（Am J Phys Anthropol 158:441–451）：**疫前**（13 世纪）伦敦人群健康已在恶化，生存率显著低于 11–12 世纪；这可能正是黑死病死亡率如此之高的原因之一。
- **对本项目的巨大价值**：这条机制让"饥荒 → 十年后大疫更致命 → 疫后一代人反而更长寿"成为一条**自然涌现的因果链**，而不需要任何脚本。
- **时间尺度**：队列级（5 年年龄组）。**空间粒度**：斑块。
- **证据等级**：A（选择性存在），C（Gamma 形状参数 k 与 ω 的取值，见 §9 D-4）。

### M7. 营养-免疫交互：弱、且要分病种（hybrid）
- **输入 → 输出**：人均热量/蛋白 + 近年饥荒史 → 调整 z 的均值与部分病种的 IFR。
- **证据状态**：Ibrahim et al. 2017（Clin Microbiol Rev, DOI 10.1128/CMR.00119-16）综述指出营养不良与感染的协同"contributes substantially to childhood morbidity and mortality"，且影响跨病毒/细菌/原虫/蠕虫广泛存在，但**机制随病原体不同**。Livi-Bacci 1991《Population and Nutrition》（CUP, DOI 10.1017/cbo9780511563003）是历史人口学侧对"营养决定死亡率"这一直觉的经典质疑（本次只核到书目元数据，未读正文）。
- **工程建议**：给肠道病、呼吸道病、结核型慢性病一个中等强度的营养乘子；给鼠疫、天花的**病死率**几乎不给营养乘子（这两种病的历史证据不支持强营养依赖——本次未检索到支持强依赖的定量文献，见 §9 D-5）；营养主要通过 M6 的 z 影响，而不是直接改 IFR。
- **证据等级**：C（方向有共识，量化弱且分歧大）。

### M8. 疫后人口恢复是慢的，且会被复发打断（rules_math）
- **输入 → 输出**：疫后年龄-性别结构 → 内生增长率 → 数十至数百年的恢复轨迹。
- **硬约束**：英格兰人口从约 500 万降到约一半，"only regaining its former population level 2–3 centuries later"（Robb et al. 2025, Sci Rep, DOI 10.1038/s41598-025-18437-5，本次读到全文）。
- **算法**：**禁止用 logistic 回弹**。恢复速率由存活的育龄女性队列上限约束；第二次大流行在欧洲持续复发约四个世纪（1347–1760 的暴发记录库本身就是证据：Yue 2017 的 6,656 条记录跨越 413 年），所以恢复期内必须允许反复的次级波次重置进度。
- **证据等级**：A。

### M9. 疫后的劳动-土地相对价格与制度反应（hybrid：数学定价 + LLM 决策）
- **输入 → 输出**：劳动力/土地比变化 → 实际工资、地租 → 精英的"提高强制"或"让步"决策 → 制度状态变化。
- **规则侧（数学）**：工资、地租、粮价由要素市场规则算，**不可由 LLM 决定**。
- **Agent 侧（LLM）**：精英是否试图立法固定工资、是否强化人身依附、是否输入外来劳动力——由 LLM agent 在信息边界内决策，其成败仍由规则判定。
- **实证锚点**：Jedwab, Johnson & Koyama 2022 摘要——短期 "Wages and per capita income rose"，长期出现西欧农奴制削弱、国家能力增强、宗教权威下降。
- **证据等级**：B（方向有共识，具体弹性未在本次检索中取得）。

### M10. 替罪羊与迫害作为社会反应（llm_agent，受规则门控）
- **输入 → 输出**：疫情死亡率 + 存在可识别少数群体 + 精英负债 + 既往冲突记忆 → 迫害事件的概率与形式。
- **门控规则**：LLM 只能在"存在该群体 + 存在既有紧张关系 + 有具体触发信息"时提议，规则层决定是否发生与后果。
- **实证锚点**：Jedwab, Johnson & Koyama 2019（J Econ Growth 24:345–395）标题即"Negative shocks and mass persecutions: evidence from the Black Death"（元数据已核，正文未读）。
- **证据等级**：B/C。

### M11. 病原体涌现的门控（rules_math）
- **输入 → 输出**：驯化动物生物量 + 人-野生动物接触强度（新开垦、新生态位）+ 最大连通宿主池规模 → 新病原体涌现的危险率与**类型**。
- **算法草图**：
  `hazard_zoonotic ∝ (domestic_biomass × contact) + (wild_contact × ecotone_novelty)`
  新病原体抽样时，其"能否成为终身免疫的纯人际急性病"必须满足 **连通宿主池 ≥ 该参数下的 CCS**，否则只能成为反复溢出的人畜共患病（自限型）。
- **实证锚点**：Wolfe/Dunavan/Diamond 2007 的五阶段框架；Morand 2014 的家畜放大器；Bendrey 2025 的早期畜牧生态条件；**Düx et al. 2020 的麻疹-牛瘟公元前 6 世纪分歧**给出"城市先于麻疹"的硬时序。
- **反例警告**：Pearce-Duvet 2006 质疑农业/家畜的份额，因此不要把"家畜种类数"做成唯一驱动（Diamond 式的"欧亚有更多可驯化大型哺乳动物 ⇒ 更多瘟疫 ⇒ 征服美洲"这条链条是**有争议的**，见 §7.4）。
- **证据等级**：B（框架），C（具体危险率函数）。

### M12. 世界事实 vs 疫病史料（rules_math + llm_agent）
- **输入 → 输出**：真实疫情事件流 → 世界内部的"疫病编年"记录，带**与真实史料相同的偏倚**。
- **偏倚模型**：记录概率 ∝ 该斑块的识字/官僚密度 × 事件规模 × 该时代的记录制度强度；严重度只保留 3 档定性标签。
- **为什么**：这正好复刻真实中国史料的结构——Liu et al. 2025（J Glob Health 15:04254）从《中国三千年气象记录总集》抽出 5,338 条疫病记录，其中**前明 247 条、明 1,898 条、清 3,193 条**，作者自己承认 1400 年后的上升"may partially reflect improved documentation practices rather than an actual rise in epidemic frequency"，严重度分级只能靠"疫/大疫/疫甚"这类定性措辞。
- **证据等级**：A（史料偏倚是真实的、被明说的）。
- **对纲领第 9 条的直接兑现**：模拟器保存真相；世界内部的历史学家只能看到这份有偏记录，从而未来可以出现"世界内部的历史学家争论某次大疫到底死了多少人"。

### 3.13 成本架构：三层（回答"既便宜又不失真"）

| 层 | 内容 | 何时运行 | 成本 |
|---|---|---|---|
| **Tier 0：地方病背景负担** | 每个生态区一组常数化的额外死亡危险率（南方湿热区的疟疾/血吸虫型负担、高密度城区的肠道病负担），只改年龄别死亡率表 | 每年一次 | O(区域数)，可忽略 |
| **Tier 1：区域随机 SEIR + 网络耦合** | M2 + M4 + M5，**只在"至少一个斑块 I>0"的连通子图上跑** | 疫情活跃时按日/周步进；其余时间完全不跑 | 成本 ∝ 活跃子图大小，典型情况下每世纪只有若干次几十年的活跃期 |
| **Tier 2：具名个体** | 只对有名字的人物（君主、将领、家族成员）按其所在斑块的当期 λ 抽样，并按年龄/脆弱度定生死 | 疫情活跃时 | O(具名人物数) |

- 关键节省：**大多数 tick 疫病系统什么都不做**。触发进入 Tier 1 的只有两类事件：疫源地溢出（M5）或跨斑块输入（M4）。
- 支持性证据：把个体模型降维到 metapopulation 能"lead to a significant gain in computational efficiency, while preserving important dynamical properties"（Winkelmann et al. 2021, Math Biosci, DOI 10.1016/j.mbs.2021.108619）；混合 metapopulation/ABM 可"reduce computational effort by up to 98% without losing the required depth in information in the focus frame"（Bicker et al. 2025, Infect Dis Model, DOI 10.1016/j.idm.2024.12.015）。
- **代价要写清楚**：Zachreson et al. 2022（R Soc Open Sci, DOI 10.1098/rsos.211919）指出，聚合成 metapopulation 会丢掉"local depletion of susceptibility"和"decoupling of different regional groups"。所以 Tier 1 的斑块不能太大（见 §9 D-1）。

### 3.14 反平衡器诊断（必须实现成自动化检查）

在每次长跑结束后自动跑这三个检验，任何一个不通过就说明疫病模块退化成了人口调节器：

1. **触发独立性检验**：`corr(疫情起始时点, 人口相对趋势的偏离量)` 应当**接近 0**。如果人口高于趋势时更容易起疫，说明有隐性反馈。
2. **来源可追溯率**：100% 的 Tier 1 疫情都必须能追溯到一次具体的 (疫源地溢出 | 跨斑块输入) 事件及其随机种子。无法追溯的疫情数应为 0。
3. **重尾检验**：疫情规模分布应当是重尾的（少数极端事件 + 大量小事件），而不是集中在"刚好把人口压回容量"的窄区间。真实证据支持重尾：同一数据集里 Givry 1348 死亡率 636/1500 ≈ 42%、Malta 1813 死亡率 4,487/97,000 ≈ 4.6%（Dean et al. 2018 表）。
4. **反事实一致性**：改变引入事件的随机种子（只改这一个），世界应当分叉出**显著不同**的人口轨迹。如果无论怎么改种子人口都回到同一条线，那条线就是隐藏剧情。

---

## 4. 硬数字与参数表

> 只列本次检索中在原文（摘要或全文）里实际读到的数值。

### 4.1 传播力与阈值

| 量 | 数值 | 适用时空范围 | 不确定度 | 来源 |
|---|---|---|---|---|
| 麻疹 R0（常被引用值） | 12–18 | 通用 | 综述结论：实际估计的离散度**大于**这个区间 | Guerra et al. 2017, Lancet ID 17:e420–e428 |
| 麻疹 R0（TSIR 拟合，英格兰-威尔士） | ≈ 30 | 疫苗前英格兰-威尔士，双周步长 | 口径不同于上行 | Bharti et al. 2008, PLoS ONE 3:e1941（全文） |
| 天花 R0 | 5.0；3.5–6.0（区间 3.4–10.8，18–20 世纪欧美）；6.7（17 世纪巴黎，Bernoulli）；1.1（1.0–1.2）与 6.9（4.5–10.1）（同一场 1967 Abakaliki 疫情的两种模型） | 见各行 | 同一疫情不同模型差 6 倍 | Nishiura, Brockmann & Eichner 2008, Theor Biol Med Model 5:20（全文表） |
| 鼠疫 R0（人体外寄生虫模型） | 1.48–1.91（九次疫情） | 欧洲 1348–1813 | 模型选择敏感 | Dean et al. 2018, PNAS（全文） |
| 鼠疫 R0（肺鼠疫模型） | 1.04–1.10 | 同上 | 同上 | Dean et al. 2018 |
| 鼠疫 R0（鼠-蚤模型） | 1.24–2.04 | 同上 | 同上 | Dean et al. 2018 |
| 鼠疫鼠间 R0 | 2.85 [1.82, 3.95] | 开罗 1801 | 后验区间 | Didelot, Whittles & Hall 2017, J R Soc Interface |
| 群体免疫阈值公式与算例 | v > 1 − 1/R0；R0=6 ⇒ 83.3% | 通用 | 同质混合假设下 | Nishiura et al. 2008 |
| 麻疹 CCS | 250,000–500,000（城市社区） | 20 世纪英格兰-威尔士型人口学 | 对传染期分布形状高度敏感 | Conlan & Grenfell 2007（全文原文） |
| 麻疹 CCS（高出生率环境） | ≈ 750,000 | 尼日尔 | 单一来源引用 | Blake et al. 2020, J R Soc Interface（全文引用） |
| 腮腺炎 CCS | 365,583–781,188（上限可达 3,376,438） | 美国 1923–1932 | 宽 | Pomeroy et al. 2023, Epidemics |
| CCS 对出生率的弹性 | 出生率翻倍 ⇒ CCS 降为约 1/5；但中等出生率（约 15–30‰）因双年周期反而降低存续性 | 模型结论 | 非单调 | Conlan & Grenfell 2007（全文） |

### 4.2 自然史（潜伏期、传染期、病死率）

| 疾病 | 量 | 数值 | 来源 |
|---|---|---|---|
| 麻疹（模型用） | 潜伏 / 传染 | 8 天 / 5 天 | Conlan & Grenfell 2007 |
| 天花 | 潜伏期均值 | 12.5 天（SD 2.2）；99 百分位 18.6 天（95% CI 16.8–22.2） | Nishiura et al. 2008 |
| 天花 | 传播的时间分布 | 发热前仅 2.7%；前驱期（0–2 日）21.1%；3–5 日 61.8% | Nishiura et al. 2008 |
| 天花 | 病死率 | 东巴基斯坦 26%；马德拉斯 36%；模型常用假设 30%（未接种）；年龄别呈 U 形（婴儿与老年高） | Nishiura et al. 2008 |
| 天花 | 孕妇病死率 | 12.7%（95% CI 11.2–14.3，非孕健康成人）→ 34.3%（31.4–37.1） | Nishiura et al. 2008 |
| 天花 | 家庭二代罹患率（未接种→未接种） | 0.0615 | Nishiura et al. 2008 |
| 天花 | 疫苗保护持续时间 | 防病中位 11.7–28.4 年；防死亡中位 49.2 年（95% CI 42.0–57.3） | Nishiura et al. 2008 |
| 腺鼠疫 | 病死率 | 未治疗 60%；抗生素治疗 5% | Barbieri et al. 2020, Clin Microbiol Rev |
| 败血症型鼠疫 | 病死率 | 未治疗 30–100% | Barbieri et al. 2020 |
| 肺鼠疫 | 病死率 | 未治疗接近 100%；24 小时内治疗 25–50% | Barbieri et al. 2020 |
| 鼠疫 | 潜伏期 | 腺鼠疫 2–10 天；原发肺鼠疫 2–4 天 | Barbieri et al. 2020 |
| 鼠疫（Eyam 1666 拟合） | 潜伏 / 传染 | 5.6 天 [4.8, 6.3] / 2.4 天 [2.1, 2.9] | Whittles & Didelot 2016, Proc R Soc B |
| 鼠疫（模型参数集） | 人腺鼠疫潜伏 4 天 [2,6]、传染 10 天 [3,10]、康复概率 0.34 [0.30,0.40]、转肺型概率 0.10 [0,0.15]；肺鼠疫潜伏 4.3 天 [2.5,6.1]、传染 2.5 天 [1.3,3.7] | 用于查士丁尼瘟疫模拟 | White & Mordechai 2020, PLoS ONE |
| 鼠疫（1820 马略卡） | 病死率 78%；平均传染期 2.0–2.8 天 | 提示肺型/败血型为主 | Puig & Pujadas-Mora 2026, PNAS |

### 4.3 媒介与储存宿主

| 量 | 数值 | 来源 |
|---|---|---|
| 蚤早期相传播效率 | *Xenopsylla cheopis* 6.4%；*Oropsylla montana* 7.7–10%；阻塞（blocked）*X. cheopis* 25–50% | Barbieri et al. 2020 |
| 蚤感染所需鼠血菌量 | ≥ 1×10⁷ CFU/ml | Barbieri et al. 2020 |
| 体虱慢性感染阈值 | 菌血症低至 1×10⁵ CFU/ml 可致慢性感染；≥1×10⁷ CFU/ml 时 Pawlowsky 腺感染、传播更稳定 | Bland et al. 2024, PLoS Biol, DOI 10.1371/journal.pbio.3002625 |
| 低温对早期相传播 | *X. cheopis* 在约 10 °C 时无效 | Barbieri et al. 2020 |
| 鼠疫流行的温度窗（第二次大流行） | 正增长仅在 11.7 °C（9.8–13.4）至 21.5 °C（20.3–22.5）之间，峰值 17.3 °C | Krauer et al. 2021, Proc R Soc B |
| 温度对高峰时点 | 平均温度每降 1 °C，高峰推迟 1.4 周（β=−1.39, SE=0.232, p<0.01）；解释 44% 方差 | Krauer et al. 2021 |
| 第三次大流行扩散速度的影响因子 | 低人口密度 + 高牧地/林地比例扩散最快；温度呈 U 形（最小值约 20 °C）；降水正相关 | Xu et al. 2019, PNAS |
| 鼠群参数（模型） | 鼠增长率 0.014/日 [0.011,0.016]；鼠自然死亡 0.00055/日；鼠感染期 5.15 天；每鼠蚤承载力 6 只 [3.29,11.17]；蚤寿命 5 天 [1,11.66] | White & Mordechai 2020 |
| *Y. pestis* 与 *Y. pseudotuberculosis* 分化 | 至少 6,000 年前 | Carcauzon et al. 2026, Appl Environ Microbiol, DOI 10.1128/aem.01658-25 |

### 4.4 大疫死亡率（实测/记载，非模型）

| 事件 | 人口 | 记载死亡 | 死亡率 | 来源 |
|---|---|---|---|---|
| Givry（法）1348 | 1,500 | 636 | ≈42% | Dean et al. 2018 表 |
| Florence 1400 | 60,000 | 10,215 | ≈17% | 同上 |
| Barcelona 1490 | 25,000 | 3,576 | ≈14% | 同上 |
| London 1563 | 80,000 | 16,886 | ≈21% | 同上 |
| Eyam 1666 | 350 | 197 | ≈56% | 同上 |
| Eyam 1665–66（另一研究） | ≈700（分析 N=689，210 户） | 257 | 37% | Whittles & Didelot 2016 |
| Gdansk 1709 | 50,000 | 23,496 | ≈47% | Dean et al. 2018 |
| Stockholm 1710 | 55,000 | 12,252 | ≈22% | 同上 |
| Moscow 1771 | 300,000 | 53,642 | ≈18% | 同上 |
| Malta 1813 | 97,000 | 4,487 | ≈4.6% | 同上 |
| 开罗 1801 | 250,000 | ≈5,000 | ≈2% | Didelot et al. 2017 |
| 黑死病·欧洲整体 | — | — | "one-third of the European population" | Barbieri et al. 2020 |
| 黑死病·英格兰 | 约 500 万 | — | "dropped to about half"；部分地区"50% or higher" | Robb et al. 2025, Sci Rep |
| 查士丁尼瘟疫 | — | — | 极大化派 25–60%；近期重估 0.1% | Barbieri et al. 2020（转述两派） |
| 满洲肺鼠疫 1910–11 | — | >60,000（六个月） | 病死率"near 100 percent" | Michaleas et al. 2022, Le Infezioni in Medicina, PMC9448316 |
| 准噶尔天花 1755 | — | ≈160,000 | — | Tang et al. 2026, Sci Adv, PMC13440406 |
| 新疆 1755–1759 综合崩溃 | — | >400,000 | 约占总人口 70%（天花 40%、武装冲突 30%、强制迁徙 20%） | 同上 |

**⚠ 注意 Eyam 的两组数字互相矛盾（350/197 vs 700/257，均为同行评议文献）。这不是我抄错，是史料本身的不确定度。模拟里给死亡率参数配区间而不是点估计。**

### 4.5 时间尺度

| 量 | 数值 | 来源 |
|---|---|---|
| 黑死病后英格兰人口恢复 | 2–3 个世纪 | Robb et al. 2025 |
| 第二次大流行在欧洲的持续期 | 记录库跨 1347–1760（413 年，6,656 条暴发） | Yue, Lee & Wu 2017 |
| 单城疫情持续期（模型 vs 史料，君士坦丁堡） | 模型给出可检测暴发 70–76 天，史料称约 120 天 | White & Mordechai 2020 |
| 鼠群崩溃时间（开罗 1801） | ≈100 天 | Didelot et al. 2017 |
| 中国大规模疫病的最短重现间隔（统计推断） | "not shorter than once every 32 years" | Gao et al. 2025, GeoHealth, DOI 10.1029/2024GH001224 |

### 4.6 空间耦合

| 量 | 数值 | 来源 |
|---|---|---|
| 引力耦合指数（麻疹，英格兰-威尔士） | ρ=1（距离）, τ1=1（接收方人口）, τ2=1.5（输出方人口）, Θ=4.54×10⁻⁹ km·person^{−1.5}·biweek⁻¹ | Xia et al. 2004，数值经 Bharti et al. 2008 全文复述 |
| 鼠疫与可通航河流 | 95.5% 的暴发在 10 km 以内；河宽 +100 m ⇒ +9 次暴发；距河 −1 km ⇒ +0.96 次暴发 | Yue et al. 2016, Sci Rep |
| 鼠疫与主要贸易路线 | log(到路线距离) 系数 ≈ −6.18（−6.09 ~ −6.29），R²=0.41–0.44 | Yue et al. 2017, Sci Rep |

---

## 5. 数据集与数据库

| 名称 | 内容 | 覆盖 | 访问 | 备注 |
|---|---|---|---|---|
| 欧洲鼠疫暴发地理编码库（Büntgen 等整理，经 Yue/Lee/Wu 使用） | 6,656 条地理编码鼠疫暴发记录 | 欧洲及北非，AD1347–1760 | 见 Yue et al. 2017（Sci Rep, PMC5636801）的数据来源说明；本次未直接取得下载入口 | 前工业疫病空间格局的最佳校准集 |
| Old World Trade Routes Project（Ciolek） | 地理编码的旧大陆贸易路线 | 旧大陆，前工业 | 见 Yue et al. 2017 引用 | 与上表配对使用 |
| 《中国三千年气象记录总集》（张德二 主编，凤凰出版社，2013） | 气象与灾疫记录汇编，编纂自全国 37 城 75 家图书馆，经史料校勘去重 | 公元前 674 – 1911 | 纸本/馆藏 | Liu et al. 2025 从中抽出 **5,338** 条疫病记录（前明 247、明 1,898、清 3,193） |
| 《中国传染病史料》（李文波，化学工业出版社，2004） | 中国历代传染病史料 | 历代 | 纸本 | Lee 2022 使用的三大疫病汇编之一 |
| 《中国古代疫病流行年表》（张志斌，福建科学技术出版社，2007） | 古代疫病流行年表 | 古代—清 | 纸本 | 同上 |
| 《中国近五百年旱涝分布图集》（中央气象局，1981） | 逐年旱涝等级空间分布 | 近 500 年，中国 | 纸本/已有数字化版本 | 气候-疫病耦合的标准气候侧数据 |
| 《中国人口史·清时期》（曹树基，复旦大学出版社，2000） | 清代分省人口序列 | 清代 | 纸本 | Lee 2022 的人口侧数据 |
| 《中国军事史》战争年表（解放军出版社，1985） | 历代战争年表 | 历代 | 纸本 | 用于"战争 vs 疫病"检验 |
| Project Tycho | 美国法定传染病周报时间序列 | 美国，州级，跨数十年 | https://www.tycho.pitt.edu/ | 唯一容易拿到的、能直接校准随机 SEIR/TSIR 动态（周期性、fade-out、层级波）的长序列（Arehart, David & Dukic 2019, Sci Rep, DOI 10.1038/s41598-019-56385-z 描述其用法） |
| 英格兰-威尔士疫苗前麻疹周报（Grenfell 系列研究的底层数据） | 954 个城镇的周报病例 | 英格兰-威尔士，约 1944–1994 | 见 Grenfell et al. 2001 / Xia et al. 2004 | CCS 与引力耦合参数的原始出处 |
| 树轮气候重建：欧洲急流纬度（EU JSL） | 1300–2004 CE 逐年重建（R²=38.5%），并与葡萄收获、粮价、瘟疫、死亡率记录对照 | 欧洲 | Xu et al. 2024, Nature 634:600–608 | 气候→经济→疫病耦合的模板 |
| 树轮 + NDVI 草原生产力重建（准噶尔） | 441 根岩芯、14 个采样点（40–50 °N, 80–90 °E），重建 4–10 月 NDVI（解释 46% 方差） | 阿尔泰-天山，387 年 | Tang et al. 2026, Sci Adv | 东亚内陆草原-游牧-疫病链的量化范例 |

**许可**：上述中文汇编为纸本出版物，需要自行数字化并注意版权；Project Tycho 为公开数据；论文附带数据集需按各刊政策取用。本次检索未逐一核对许可条款。

---

## 6. 中国与东亚特定证据

### 6.1 长时段疫病记录的量化研究（可直接用作校准集）
- **Liu Q, Qin C, Zhang S, Liu J (2025), J Glob Health 15:04254, DOI 10.7189/jogh.15.04254**（本次读到全文）：从《中国三千年气象记录总集》抽取 **5,338** 条疫病记录，覆盖公元前 674 – 1911。严重度按措辞分三级（"疫/疾疫"→"多疫/疫频"→"大疫/疫甚"）。结果：**洪水每增加一次，中等后果的比值上升 42%、严重后果上升 46%；旱灾使严重后果风险上升 23%；饥荒使中等后果上升 40%、严重后果上升 55%**；1451–1911 年间"与气象相关的疫病比例"每十年下降 0.24%。作者明说 1400 年后的上升"可能部分反映记录实践改善，而非疫病频率真的上升"。
- **Lee HF (2022), Human Ecology, DOI 10.1007/s10745-021-00272-7**（本次读到全文）：1841–1911 年 **1,402** 次疫病（度量 = 每年受灾县数），数据来自上述三部汇编交叉核对。单因素回归中水文气候极端、饥荒、经济波动均显著，**战争不显著**；但在纳入全部变量的组合回归里**只有经济波动仍显著**（系数 1.198，SE 0.503，t=2.38，p=0.020，调整 R²=0.328）。小波分析显示经济波动领先疫病约 0.374 年（6 年周期）与 2.965 年（12 年周期）。
- **对本项目的机制含义**：**气候不是直接作用于疫病，而是通过经济（粮价、生计崩溃、流民）作用。** 这正好支持我们把"气候 → 农业 → 粮价 → 迁徙/营养/密度 → 疫病"实现成一条显式链条，而不是给气候一个直接的疫病加成项。
- **Hang X, Sun Z, He J, et al. (2025), Environ Health, DOI 10.1186/s12940-025-01163-w**：1784–1787 年极端干旱触发疫病，路径涉及粮价、人口密度与社会经济瓦解。
- **Gao J, Hou X, Cheng Y, et al. (2025), GeoHealth, DOI 10.1029/2024GH001224**：疫病-旱-涝的交叉相关呈 16 年标度行为，推断"大规模疫病的重现间隔不短于每 32 年一次"。

### 6.2 疫源地与鼠疫（东亚特有的地理事实）
- 云南是中国重要的**商栖鼠疫自然疫源地**，其土壤特征与历史疫源地相关（Ai et al. 2026, Front Vet Sci, DOI 10.3389/fvets.2026.1797277）；2022 年云南野鼠分离株仍聚在 1.IN5 谱系、与丽江野鼠疫源地历史分离株同源，说明"疫情来自本地疫源地"（Yang et al. 2025, Pathogens, DOI 10.3390/pathogens14121212）。
- 西南地区鼠疫风险由自然与人为因素共同决定（Lou et al. 2025, One Health, DOI 10.1016/j.onehlt.2025.101142）；人为干预改变鼠类种群动态（Zhao et al. 2025, One Health, DOI 10.1016/j.onehlt.2025.101276）。
- **黑死病主谱系的源头在天山地区**（Spyrou et al. 2022, Nature 606:718–724）：吉尔吉斯斯坦伊塞克湖 Kara-Djigach 与 Burana 墓地，碑铭直书 1338–1339 年"pestilence"，古基因组是那次大分化的最近共同祖先，且与天山现存疫源地多样性一致。**这意味着以中国及周边东亚为舞台的模拟，地图上必须有内亚草原型疫源地，而且它是可以向外输出世界级大疫的。**
- **蒙古帝国-粮道-疫病链**：Green & Fancy 2025（Medical History, DOI 10.1017/mdh.2024.29, PMC11949646）主张黑死病之前存在"前驱期"的疫源地化，具体线索包括 1257–58 旭烈兀征伐期间蒙古人自天山运入自己的粮食供应（"precisely the ecological circumstance that would allow the importation of rodents and their fleas"）、1258 年巴格达陷落三个月后大马士革出现腺鼠疫症状的疫情、1260 年马尔丁围城后疫情、1295–96 年开罗大疫（"up to 1500 people a day"）、1321/1329/1337 年亚美尼亚文献提及。**这是与 Brack 等人正在进行的争论**（争点包括围城期间疫情能否归因于蒙古人、阿拉伯语 *wabāʾ* 能否作为鼠疫证据、Kara-Djigach 基因组是否为所有黑死病株的祖先）。

### 6.3 天花与人痘（东亚制度性防疫的独特路径）
- Guan LY, Gu SJ, Fu CX (2025), 中华预防医学杂志, DOI 10.3760/cma.j.cn112150-20241217-01018：中国古代人痘接种"represents the world's earliest practice of disease prevention through vaccination"，其理论基础在中医痘疹病机学说中。
- Hwang K (2024), J Trauma Inj, DOI 10.20408/jti.2022.0044：人痘术自中国传入朝鲜。
- **对本项目**：这是"技术不必按固定科技树解锁"的绝佳范例——一个社会可以在完全没有细菌理论的情况下发明有效的免疫干预，只要它有 (a) 高天花负担、(b) 系统化的病例观察传统、(c) 精英对儿童存活的强烈激励。可以把它做成一个**由条件触发的可发明技术**，而不是预置节点。
- Zeng Y, Chen Z, Yan X, Gong S, Zhang T (2025), PLoS ONE, DOI 10.1371/journal.pone.0317108：湖北天花流行的地理特征（省级空间史研究范例）。Chen Z, Gong S, Zhang T (2026), PLoS NTD, DOI 10.1371/journal.pntd.0014125：湖北霍乱时空格局，结论是旱、涝、海拔等自然因素与人为因素在不同时间尺度上共同塑造疫情。

### 6.4 草原-农耕边界上的疾病-国家崩溃链（最值得抄的因果链模板）
**Tang W, et al. (2026), Sci Adv, DOI 10.1126/sciadv.aee4285, PMC13440406**（本次读到全文）重建了：
- 阿尔泰-天山 441 根树轮岩芯 → 极端生长比（EGR）→ 4–10 月 NDVI 重建（R²=46%）；
- **准噶尔汗国核心区在 1751–1761 年经历了过去 387 年最低的草原生产力**；
- 1740 年代气候有利、草原生产力高、朝贡贸易达到峰值（1742 年 26,118 两），**贸易高峰期间 1743–44 出现第一次有记录的天花大流行**；
- 1755 年天花再度暴发，成为准噶尔史上最惨烈的一次，约 **160,000 人**死亡；
- 1755–1759 年间战争与天花导致新疆人口崩溃，**死亡超过 400,000 人，约占总人口 70%（天花 40%、武装冲突 30%、强制迁徙 20%）**；
- 时变 Granger 因果分析显示 NDVI 对动乱有显著负效应（effect = −0.598），低冲突与活跃朝贡相关（−0.459）。

**为什么这条链对本项目是黄金**：它是"气候 → 草场生产力 → 贸易/朝贡强度 → 疾病输入 → 人口崩溃 + 军事失败 → 国家灭亡"的完整可追溯链，每一环都有独立的量化证据。这正是纲领第 2 条要求的那种因果链。**但必须作为机制模板，不是剧本模板**——模拟里应当能生成结构同型但内容完全不同的事件。

### 6.5 中国史料的可靠性问题（必须写进模拟的史料层）
- 记录数量随朝代急剧上升（前明 247 / 明 1,898 / 清 3,193），作者自陈这**部分是记录制度改善**（Liu et al. 2025）。
- 严重度只能靠定性措辞三分级，**没有病原体特异性**（Liu et al. 2025 自列的局限：主观判断、跨朝代漏报、区域记录不一致、缺乏病原学识别）。
- 度量单位常常是"受灾县数"而不是死亡数（Lee 2022）。
- Lee 2022 自列的局限还包括：历史疫病记录缺少"nature, magnitude, root cause, and length of time"的完整描述；分析假定所有记录都代表重大疫情；国家级分析可能掩盖区域差异。
- **工程结论**：中国史料适合用来校准**疫病事件的频率、空间格局与气候/经济相关性**，**不适合**用来校准死亡率量级。死亡率量级要从欧洲的教区/遗嘱/骨学数据借用（§4.4），并明确标注这是跨文化外推。

---

## 7. 学界争议与未解决问题

1. **查士丁尼瘟疫的规模**：Mordechai et al. 2019（PNAS 116:25546–25554）系统检查文献、立法、钱币、纸草、铭文、孢粉、古 DNA、墓葬考古八类证据后主张"maximalist paradigm 与证据不符"，数据整体显示的是**连续性**而非大规模破坏性死亡。Barbieri et al. 2020 转述的两派数字相差 **600 倍**（25–60% vs 0.1%）。White & Mordechai 2020 的模拟又发现：即便按极大化的 25 万死亡数，模型给出的可检测疫情持续期（70–76 天）也短于史料所称的约 120 天。**结论：本项目不应把"一次大疫可以终结一个古代世界"当成默认设定。**
2. **鼠疫的主要传播路径**：Dean et al. 2018（人体外寄生虫模型最优）vs Benedictow 2019（认为可以证伪外寄生虫假说，坚持鼠-鼠蚤）vs Didelot et al. 2017（开罗 1801 中人-人只占 18%）vs Whittles & Didelot 2016（Eyam 中人-人占 73%）。**同一疾病在不同疫情中路径占比截然不同**——这本身可能就是真相（取决于季节、住房、鼠群状态），也可能是模型不可辨识性。
3. **黑死病的死亡率**："one-third"（Barbieri 2020 转述）vs 英格兰"约一半"、局部"50% or higher"（Robb et al. 2025）。本次检索**未能核实** Benedictow 主张的约 60% 这个数字（见 §10 未核实清单）。
4. **Diamond 的驯化-疫病论证**：Wolfe/Dunavan/Diamond 2007 提供了五阶段框架和"温带靠家畜、热带靠野生灵长类"的区分；Pearce-Duvet 2006 从进化生物学角度质疑农业与家畜作为主要来源的份额（本次仅核到元数据）。**争议的实质是"份额"而不是"存在"。** 本项目应该实现"家畜是一条重要通道但不是唯一通道"，不要实现"家畜种类数决定文明疫病优势"。
5. **临界社区规模是否是一个稳健的量**：Keeling & Grenfell 1997 表明模型对 CCS 的预测对传染期分布形状敏感；Conlan & Grenfell 2007 表明 CCS 对出生率非单调、且接种可能反而提高 CCS。所以 CCS 是一个**依赖人口学与行为的涌现量**，不是常数。
6. **气候是否直接驱动疫病**：Lee 2022 在组合回归中发现只有经济波动显著；Liu et al. 2025 在更长时段上发现洪、旱、饥荒都有显著效应。二者的差别可能来自时段（71 年 vs 2,500 年）、度量（县数 vs 严重度分级）与共线性。**未解决。**
7. **欧洲是否存在过持久鼠疫疫源地**：Stenseth et al. 2022 与 Yue et al. 2017 的间接推断都指向"没有"，即第二次大流行的每一波都需要重新输入。但这与"四个世纪反复复发"的现象之间的张力尚未完全解决。
8. **史料计数 vs 真实频率**：中国疫病记录的时间趋势有多大比例是记录制度的产物，尚无被广泛接受的校正模型。

---

## 8. 反模式：本领域常见的错误建模方式

### 8.1 ❌ 把疫病当成人口曲线的负反馈平衡器（**本项目最危险的反模式**）
典型实现：`if population > carrying_capacity * 0.9: trigger_plague()`。
- **为什么错**：黑死病的死亡是**按脆弱度选择**的（DeWitte & Wood 2008），不是按密度均匀施加的；欧洲鼠疫的每一波都需要外部输入（Stenseth et al. 2022；Yue et al. 2017 的距港口负相关推论），因此其**时点是外生的**，由内亚疫源地生态与贸易网络决定（Spyrou et al. 2022），而不是由欧洲本地人口是否"过密"决定；疫后英格兰花了 **2–3 个世纪**才恢复（Robb et al. 2025），完全不是一个把人口拉回容量线的短期调节器。
- **失真后果**：人口曲线变成一条被隐形手拉住的绳子，任何"为什么这个文明没有突破人口上限"的追问都只能回答"因为系统需要它不突破"——这正是纲领禁止的隐藏剧情。
- **正确做法**：M5 + M4 + §3.14 的四项诊断。

### 8.2 ❌ 把 R0 当成病原体常数存起来
Delamater et al. 2019 明确：R0 不是病原体属性、依赖模型结构与假设、不能被疫苗改变；Guerra et al. 2017 的系统综述发现麻疹 R0 的实际离散度大于常引的 12–18；同一场 1967 年 Abakaliki 天花疫情用两种模型算出 1.1 与 6.9（差 6 倍，Nishiura et al. 2008）。
- **正确做法**：存"单位接触传播概率 + 传染期"，R0 由世界状态导出（M1）。

### 8.3 ❌ 在前城市世界里放现代人群病
Düx et al. 2020 把麻疹-牛瘟分化定在公元前 6 世纪，且"possibly coinciding with the rise of large cities"。一个需要 25–75 万连通宿主池才能维持的病原体，在只有几千人聚落的世界里在生物学上不可能持续存在。
- **正确做法**：M11 的门控——新病原体的"生态位类型"由当时的最大连通宿主池规模决定。

### 8.4 ❌ 用统一死亡率百分比杀人
"这次瘟疫死 30%"然后对每个人独立抽 30%。这会抹掉：脆弱度选择（DeWitte & Wood 2008）、年龄别 U 形病死率（天花，Nishiura et al. 2008）、疫后幸存者健康改善（DeWitte 2014）、疫前营养恶化放大疫情（DeWitte 2015）。
- **失真后果**：饥荒与疫病之间的跨代因果链彻底消失，人口年龄结构在疫后不发生任何形变，恢复速度失真。

### 8.5 ❌ 用 ODE 而不是整数随机过程
CCS、fade-out、burnout 全部是随机性与整数性的产物。确定性 SEIR 里 `I` 可以是 10⁻⁷ 个人然后再长回来（所谓 "atto-fox problem"），疫病永远不会灭绝，历史上"某病在某地消失三十年后又烧回来"这种最有历史质感的现象就不会出现。

### 8.6 ❌ 用指数分布的传染期
Keeling & Grenfell 1997 的核心结论就是这会系统性高估 CCS，让模型比现实更容易灭绝。用 Gamma/Erlang（k=3–5）。

### 8.7 ❌ 把"黑死病 ⇒ 工资上涨 ⇒ 农奴制瓦解"写成规则
Jedwab/Johnson/Koyama 2022 的摘要写的是"西欧农奴制削弱"，这个限定词是关键。同一冲击在不同制度环境下有相反结果。写成规则就等于宣布"任何大疫之后自由都会增加"，这是把一次欧洲的历史结果冒充成历史规律。
- **正确做法**：M9——工资/地租由要素市场算，制度反应由 agent 决策 + 规则裁定。

### 8.8 ❌ 把鼠疫建模成纯人-人 SEIR
Benedictow 2019 专门批评了这一点（虽然他自己的立场也有争议）。至少要有储存宿主 + 媒介的最简表示，否则温度季节性（Krauer 2021 的 11.7–21.5 °C 窗口）、地理疫源地依赖、以及"为什么疫情能突然在一个从未有病例的港口出现"这些性质都拿不到。

### 8.9 ❌ 用欧氏距离做空间耦合
Bharti et al. 2008 的海岸 "edge effect" 是直接反例。前工业世界更极端：山脉、沙漠、季风航路会让欧氏距离与有效距离相差一个量级。Yue et al. 2016 的"95.5% 在可通航河流 10 km 内"说明真实的传播算子几乎就是水网本身。

### 8.10 ❌ 把史料计数当成事件计数
中国疫病记录前明 247 条、明 1,898 条、清 3,193 条（Liu et al. 2025），作者自己说这部分反映记录制度而非真实频率。如果拿这条曲线去校准"疫病频率随时间上升"，就把一个史学假象固化成了世界机制。
- **正确做法**：M12——模拟器保存真相，另外生成一份有偏史料。

### 8.11 ❌ 把整个国家当成一个混合池
Zachreson et al. 2022 指出聚合会丢掉"local depletion of susceptibility"与"decoupling of different regional groups"。结果是疫情会同步扫过全国，而真实的历史疫情是层级的、错峰的、有大量幸免区域的（Grenfell et al. 2001 的层级行波）。

### 8.12 ❌ 采纳极大化的历史死亡数字作为默认值
Mordechai et al. 2019 的论证与 White & Mordechai 2020 的模拟都表明极大化叙事的证据基础薄弱。用极大化数字校准会让模拟里的每一次瘟疫都成为文明终结者。

---

## 9. 无来源判断（D 级，LLM 常识，不得当作历史规律）

以下都是我为了让模拟能跑而做的假设，本次检索**没有**找到支持文献。全部标记为 D 级。

- **D-1 斑块粒度**：建议城市单独成格、乡村按 20–50 km 网格聚合。这个尺度是我在"保留局部易感者耗竭"（Zachreson 2022 的警告）与计算成本之间拍脑袋折中的结果，没有文献依据。需要在实现后做敏感性分析。
- **D-2 东西欧制度反应不对称**：我在 §2.7 与 §8.7 提到"同一冲击在东欧导致第二次农奴制"。这是经济史里的常见说法，但**本次检索未取得任何直接文献**。不得作为已证事实使用。
- **D-3 把 Xia et al. 2004 的 Θ = 4.54×10⁻⁹ 搬到前现代世界**：这个系数是在 20 世纪英格兰-威尔士的铁路/公路通勤结构下拟合的，前现代旅行强度低若干个数量级。**必须重标定**。我建议的做法（用"每年经过该边的旅人-次数"直接替代 Θ·N^τ 项）没有文献支持。指数 ρ=1, τ1=1, τ2=1.5 我倾向于保留，但这也是外推。
- **D-4 脆弱度 z 的 Gamma 形状参数**：DeWitte & Wood 2008 证明了选择性存在，但没有给出可直接使用的分布参数。我建议 k ∈ [1, 3] 起步（k 小 = 异质性强），纯属工程猜测。
- **D-5 鼠疫/天花病死率对营养近乎不敏感**：这是我从"这两种病在富裕阶层也大量致死"这一常识推出的，本次**未找到定量文献**。反方向的证据（DeWitte 2015 显示疫前健康恶化可能放大黑死病死亡率）实际上与我的假设有张力。请在下一阶段专门检索。
- **D-6 三层成本架构（Tier 0/1/2）**：架构本身是我的设计，只有"降维能省算力"这一点有文献（Winkelmann 2021, Bicker 2025）。层与层的切换阈值没有依据。
- **D-7 §3.14 的四项反平衡器诊断**：这是我为本项目设计的检验，不是领域标准做法。阈值（"相关系数接近 0"）需要自行定义显著性标准。
- **D-8 人痘术作为条件触发技术的三个前置条件**（高负担 / 系统化病例观察传统 / 精英对儿童存活的强激励）：这是我对 Guan et al. 2025 那句"世界最早"的机制化重构，不是他们的论点。
- **D-9 "疫病记录概率 ∝ 识字/官僚密度 × 事件规模 × 记录制度强度"**：这是我对 Liu et al. 2025 定性告诫的一个函数化，没有人拟合过这个关系。
- **D-10 军队行军作为"临时高权重边"、围城作为"临时高密度斑块"的具体权重**：机制方向有 Green & Fancy 2025 的叙述支持，但任何具体倍数都是我编的。注意 Lee 2022 在中国 1841–1911 的数据里**发现战争与疫病无显著关联**——这是对该机制强度的一个反向约束。
- **D-11 "大疫的规模分布应当是重尾的"**：§4.4 的表（4.6% 到 56%）与之相容，但我没有找到任何人正式检验过前工业疫病死亡率的分布族。
- **D-12 把 Tier 0 的"南方湿热区疟疾/血吸虫背景负担"参数化**：本次检索**完全没有**取得前现代疟疾、结核在中国或欧洲的可用定量负担参数。这一层目前是纯占位符。

---

## 10. 参考文献

**检索方法与覆盖说明**：本次会话的 WebSearch 配额在开始前已被耗尽（200/200），因此全部检索通过 WebFetch 完成，使用 Europe PMC REST API（搜索 + 开放获取全文 XML）、Crossref API（书目元数据核验）、PubMed 检索页与出版社页面。**这带来两个系统性偏倚**：(1) Europe PMC 偏向生物医学文献且默认按新近度排序，经济史、社会史、历史人口学的期刊覆盖很差；(2) 付费墙挡住了 Lancet Infect Dis、Nature、Science、Am Nat、J Econ Hist、Rev Econ Stud、Eur Rev Econ Hist 的正文，这些只能核到摘要或仅书目元数据。**因此第 2.7 节（经济后果）与 §2.8（Diamond 争论）的证据强度明显弱于第 2.1–2.6 节。** 专著（Benedictow、Campbell、McNeill、Anderson & May 等）本次一律未核。

### 10.1 本次检索中读到全文的文献（最强）
1. Conlan AJ, Grenfell BT. **Seasonality and the persistence and invasion of measles.** Proc Biol Sci, 2007. DOI 10.1098/rspb.2006.0030. PMC1914306. [已核验]
2. Nishiura H, Brockmann SO, Eichner M. **Extracting key information from historical data to quantify the transmission dynamics of smallpox.** Theor Biol Med Model 5:20, 2008. DOI 10.1186/1742-4682-5-20. PMC2538509. [已核验]
3. Dean KR, Krauer F, Walløe L, Lingjærde OC, Bramanti B, Stenseth NC, Schmid BV. **Human ectoparasites and the spread of plague in Europe during the Second Pandemic.** PNAS, 2018. DOI 10.1073/pnas.1715640115. PMC5819418. [已核验]
4. Whittles LK, Didelot X. **Epidemiological analysis of the Eyam plague outbreak of 1665–1666.** Proc Biol Sci, 2016. DOI 10.1098/rspb.2016.0618. PMC4874723. [已核验]
5. Didelot X, Whittles LK, Hall I. **Model-based analysis of an outbreak of bubonic plague in Cairo in 1801.** J R Soc Interface, 2017. DOI 10.1098/rsif.2017.0160. PMC5493801.
6. White LA, Mordechai L. **Modeling the Justinianic Plague: comparing hypothesized transmission routes.** PLoS ONE, 2020. DOI 10.1371/journal.pone.0231256. PMC7192389. [已核验]
7. Krauer F, et al. **[Temperature and seasonality of plague in the Second Pandemic].** Proc Biol Sci, 2021. DOI 10.1098/rspb.2020.2725. PMC8277479. [已修正: Krauer F, Viljugrein H, Dean KR. **The influence of temperature on the seasonality of historical plague outbreaks.** Proc Biol Sci 288:20202725, 2021. DOI 10.1098/rspb.2020.2725 — Schmid BV 不是该文作者]
8. Yue RPH, Lee HF, Wu CYH. **Trade routes and plague transmission in pre-industrial Europe.** Sci Rep, 2017. DOI 10.1038/s41598-017-13481-2. PMC5636801. [已核验]
9. Barbieri R, Signoli M, Chevé D, Costedoat C, Tzortzis S, Aboudharam G, Raoult D, Drancourt M. **Yersinia pestis: the natural history of plague.** Clin Microbiol Rev, 2020. DOI 10.1128/cmr.00044-19. PMC7920731. [已核验]
10. Bharti N, Xia Y, Bjornstad ON, Grenfell BT. **Measles on the edge: coastal heterogeneities and infection dynamics.** PLoS ONE 3:e1941, 2008. DOI 10.1371/journal.pone.0001941. PMC2275791. [已核验]
11. Liu Q, Qin C, Zhang S, Liu J. **Trends of infectious diseases, epidemic patterns, and meteorological events [in historical China].** J Glob Health 15:04254, 2025. DOI 10.7189/jogh.15.04254. PMC12412270. [已修正: 完整标题为 "Trends of infectious diseases, epidemic patterns, and the association with meteorological events: 2500 years of evidence from an observational study in China"]
12. Lee HF. **Did hydro-climatic extremes modulate epidemics outbreaks in late imperial China?** Human Ecology, 2022. DOI 10.1007/s10745-021-00272-7. PMC8527977. [已修正: 完整标题为 "Did Hydro-climatic Extremes, Positive Checks, and Economic Fluctuations Modulate the Epidemics Outbreaks in Late Imperial China?"，Human Ecology 50:113–123, 2022]
13. Tang W, et al. **Steppe productivity decline contributed to smallpox outbreak and the collapse of the last nomadic empire in the 1750s.** Sci Adv, 2026. DOI 10.1126/sciadv.aee4285. PMC13440406. [已核验]
14. Robb J, Dittmar JM, Inskip SA, Rose AK, Mitchell PD, O'Connell TC, Price M, Cessford C. **More continuity than change following the Black Death epidemic in medieval Cambridge.** Sci Rep, 2025. DOI 10.1038/s41598-025-18437-5. PMC12480250. [已核验]
15. Green MH, Fancy N. **Plague history, Mongol history, and the processes of focalisation leading up to the Black Death: a response to Brack et al.** Medical History, 2025. DOI 10.1017/mdh.2024.29. PMC11949646. [已修正: Medical History 68:411–435；Crossref 记为 2024 年 10 月出版，Europe PMC 记为 2025，正式卷期为 vol 68 (2024)]

### 10.2 本次检索中读到摘要（未读全文）
16. Keeling MJ, Grenfell BT. **Disease extinction and community size: modeling the persistence of measles.** Science 275:65–67, 1997. DOI 10.1126/science.275.5296.65. [已核验]
17. Guerra FM, Bolotin S, Lim G, Heffernan J, Deeks SL, Li Y, Crowcroft NS. **The basic reproduction number (R0) of measles: a systematic review.** Lancet Infect Dis 17:e420–e428, 2017. DOI 10.1016/s1473-3099(17)30307-9. [已核验]
18. Grenfell BT, Bjørnstad ON, Kappey J. **Travelling waves and spatial hierarchies in measles epidemics.** Nature 414:716–723, 2001. DOI 10.1038/414716a. [已核验]
19. Wolfe ND, Dunavan CP, Diamond J. **Origins of major human infectious diseases.** Nature 447:279–283, 2007. DOI 10.1038/nature05775. [已核验]
20. Düx A, et al. **Measles virus and rinderpest virus divergence dated to the sixth century BCE.** Science, 2020. DOI 10.1126/science.aba9411. PMC7713999. [已核验]
21. Mordechai L, Eisenberg M, Newfield TP, Izdebski A, Kay JE, Poinar H. **The Justinianic Plague: an inconsequential pandemic?** PNAS 116:25546–25554, 2019. DOI 10.1073/pnas.1903797116. [已核验]
22. Spyrou MA, et al. **The source of the Black Death in fourteenth-century central Eurasia.** Nature 606:718–724, 2022. DOI 10.1038/s41586-022-04800-3. PMC9217749. [已核验]
23. Xu L, et al. **Historical and genomic data reveal the influencing factors on global transmission velocity of plague during the Third Pandemic.** PNAS 116:11833–11838, 2019. DOI 10.1073/pnas.1901366116.
24. DeWitte SN, Wood JW. **Selectivity of Black Death mortality with respect to preexisting health.** PNAS 105:1436–1441, 2008. DOI 10.1073/pnas.0705460105. PMC2234162. [已核验]
25. DeWitte SN. **Mortality risk and survival in the aftermath of the medieval Black Death.** PLoS ONE 9:e96513, 2014. DOI 10.1371/journal.pone.0096513. PMC4013036. [已核验]
26. DeWitte SN. **Setting the stage for medieval plague: pre-Black Death trends in survival and mortality.** Am J Phys Anthropol 158:441–451, 2015. DOI 10.1002/ajpa.22806. [已核验]
27. Yue RP, Lee HF, Wu CY. **Navigable rivers facilitated the spread and recurrence of plague in pre-industrial Europe.** Sci Rep, 2016. DOI 10.1038/srep34867. PMC5056511. [已核验]
28. Delamater PL, Street EJ, Leslie TF, Yang YT, Jacobsen KH. **Complexity of the basic reproduction number (R0).** Emerg Infect Dis 25(1):1–4, 2019. DOI 10.3201/eid2501.171901. PMC6302597. [已核验]
29. Pomeroy LW, Magsi S, McGill S, Wheeler CE. **Mumps epidemic dynamics in the United States before vaccination (1923–1932).** Epidemics, 2023. DOI 10.1016/j.epidem.2023.100700. PMC11057333.
30. Blake A, Djibo A, Guindo O, Bharti N. **Investigating persistent measles dynamics in Niger and associations with rainfall.** J R Soc Interface, 2020. DOI 10.1098/rsif.2020.0480. PMC7482562.（全文读到 CCS 与 R0 引用）
31. Benedictow OJ. **Epidemiology of plague: problems with the use of mathematical epidemiological methods in plague research.** Can J Infect Dis Med Microbiol, 2019. DOI 10.1155/2019/1542024. PMC6720821.
32. Stenseth NC, et al. **No evidence for persistent natural plague reservoirs in historical and modern Europe.** PNAS 119:e2209816119, 2022. DOI 10.1073/pnas.2209816119. PMC9907128. [已核验]
33. Michaleas SN, Laios K, Karamanou M, Sipsas NV, Androutsos G. **The Manchurian pandemic of pneumonic plague (1910–1911).** Le Infezioni in Medicina, 2022. DOI 10.53854/liim-3003-17. PMC9448316.
34. Puig P, Pujadas-Mora JM. **The 1820 Mallorca plague was not a classic bubonic outbreak.** PNAS, 2026. DOI 10.1073/pnas.2536892123.
35. Bland DM, Long D, Rosenke R, Hinnebusch BJ. **Yersinia pestis can infect the Pawlowsky glands of human body lice.** PLoS Biol, 2024. DOI 10.1371/journal.pbio.3002625. PMC11108126.
36. Xu G, et al. **Jet stream controls on European climate and agriculture since 1300 CE.** Nature 634:600–608, 2024. DOI 10.1038/s41586-024-07985-x. PMC11485261.
37. Carcauzon V, Laudisoit A, Slavin P, Goodman SM, Sebbane F, Tortosa P. **Emergence, global dispersal, and local adaptations of Yersinia pestis.** Appl Environ Microbiol, 2026. DOI 10.1128/aem.01658-25. PMC13101507.
38. Jedwab R, Johnson ND, Koyama M. **The economic impact of the Black Death.** J Econ Lit 60:132–178, 2022. DOI 10.1257/jel.20201639.（摘要读自 AEA 页面） [已核验]
39. Ibrahim MK, Zambruni M, Melby CL, Melby PC. **Impact of childhood malnutrition on host defense and infection.** Clin Microbiol Rev, 2017. DOI 10.1128/CMR.00119-16. PMC5608884.
40. Morand S, McIntyre KM, Baylis M. **[Domesticated animals and human shared infectious diseases].** Infect Genet Evol 24:76–81, 2014. DOI 10.1016/j.meegid.2014.02.013.
41. Bendrey R, et al. **[Early animal farming and pathogen emergence].** Evol Med Public Health 13(1):344–354, 2025. DOI 10.1093/emph/eoaf029.
42. Zachreson C, Chang S, Harding N, Prokopenko M. **The effects of local homogeneity assumptions in metapopulation models of infectious disease.** R Soc Open Sci, 2022. DOI 10.1098/rsos.211919. PMC9277238. [已核验]
43. Bicker J, Schmieding R, Meyer-Hermann M, Kühn MJ. **Hybrid metapopulation agent-based epidemiological models.** Infect Dis Model, 2025. DOI 10.1016/j.idm.2024.12.015. PMC11815675.
44. Winkelmann S, Zonker J, Schütte C, Conrad ND. **Mathematical modeling of spatio-temporal population dynamics and application to epidemic spreading.** Math Biosci, 2021. DOI 10.1016/j.mbs.2021.108619. PMC8054535.
45. Gao J, Hou X, Cheng Y, Ye Y, Wang Y, Kong J. **Emergence from complex interactions of epidemics, droughts, and floods.** GeoHealth, 2025. DOI 10.1029/2024GH001224. PMC12642215.
46. Hang X, Sun Z, He J, et al. **Temporal and spatial effects of extreme drought events on human epidemics [1784–1787].** Environ Health, 2025. DOI 10.1186/s12940-025-01163-w. PMC11895321.
47. Guan LY, Gu SJ, Fu CX. **[The historical status, experience and enlightenment of variolation in ancient China].** 中华预防医学杂志, 2025. DOI 10.3760/cma.j.cn112150-20241217-01018.
48. Hwang K. **Development of variolation and its introduction to Joseon-era Korea.** J Trauma Inj, 2024. DOI 10.20408/jti.2022.0044. PMC11703690.
49. Zeng Y, Chen Z, Yan X, Gong S, Zhang T. **Geographical characteristics of smallpox epidemics in Hubei Province.** PLoS ONE, 2025. DOI 10.1371/journal.pone.0317108. PMC12074586.
50. Chen Z, Gong S, Zhang T. **Spatio-temporal patterns of cholera epidemics in Hubei Province.** PLoS NTD, 2026. DOI 10.1371/journal.pntd.0014125. PMC13020998.
51. Yang R, Yang F, Dong S, Peng H, Shi L, Wang P. **Molecular tracing and comparative genomics of Yersinia pestis from wild rodents in Yunnan (2022).** Pathogens, 2025. DOI 10.3390/pathogens14121212. PMC12735913.
52. Ai ZQ, et al. **Soil characteristics associated with historical commensal rodent plague foci in Yunnan Province, China.** Front Vet Sci, 2026. DOI 10.3389/fvets.2026.1797277. PMC13215812.
53. Lou Z, et al. **Influence of natural and anthropogenic drivers on plague risk in Southwest China.** One Health, 2025. DOI 10.1016/j.onehlt.2025.101142. PMC12319548.
54. Britton T, House T, Lloyd AL, Mollison D, Riley S, Trapman P. **Five challenges for stochastic epidemic models involving global transmission.** Epidemics, 2015. DOI 10.1016/j.epidem.2014.05.002. PMC4996665.
55. Parsons TL, Bolker BM, Dushoff J, Earn DJD. **The probability of epidemic burnout in the stochastic SIR model with vital dynamics.** PNAS, 2024. DOI 10.1073/pnas.2313708120. PMC10835029.
56. Cant S, Shanks GD, Keeling MJ, Penman BS. **Extreme mortality during a historical measles outbreak on Rotuma is consistent with measles immunosuppression.** Epidemiol Infect, 2024. DOI 10.1017/s095026882400075x. PMC11149033.
57. Arehart CH, David MZ, Dukic V. **Tracking U.S. pertussis incidence [Project Tycho].** Sci Rep, 2019. DOI 10.1038/s41598-019-56385-z. PMC6930253.
58. Rahman MT, et al. **Zoonotic diseases: etiology, impact, and control.** Microorganisms 8(9):1405, 2020. DOI 10.3390/microorganisms8091405.
59. Yu X. **Response to epidemic disease in ancient China and its characteristics.** Chinese Medicine and Culture, 2020. DOI 10.4103/cmac.cmac_22_20. PMC9009840.
60. Godde K, DeWitte SN, Beaumont J, Walter BS, Redfern R, Bekvalac JJ. **Selective mortality during famine and plague events in medieval London.** Sci Rep, 2025. DOI 10.1038/s41598-025-13198-7. PMC12297707.
61. Mongillo J, Cerviero A, Zedda N, Rinaldo N, Bramanti B. **A heavy issue: changes in body size in London before, during and after the Black Death.** Am J Biol Anthropol, 2025. DOI 10.1002/ajpa.70098. PMC12272036.

### 10.3 仅核到书目元数据（Crossref 确认存在，本次未读正文，结论不得依赖）
62. Bartlett MS. **Measles periodicity and community size.** J R Stat Soc Ser A 120:48, 1957. DOI 10.2307/2342553.
63. Bartlett MS. **The critical community size for measles in the United States.** J R Stat Soc Ser A 123:37, 1960. DOI 10.2307/2343186.
64. Black FL. **Measles endemicity in insular populations: critical community size and its evolutionary implication.** J Theor Biol 11(2):207–211, 1966. DOI 10.1016/0022-5193(66)90161-5.（Europe PMC 无摘要）
65. Xia Y, Bjørnstad ON, Grenfell BT. **Measles metapopulation dynamics: a gravity model for epidemiological coupling and dynamics.** Am Nat 164:267–281, 2004. DOI 10.1086/422341.（参数值经 Bharti et al. 2008 全文转述） [已核验]
66. Grenfell BT, Bjørnstad ON, Finkenstädt BF. **Dynamics of measles epidemics: scaling noise, determinism, and predictability with the TSIR model.** Ecol Monogr 72:185, 2002. DOI 10.2307/3100024.
67. Keeling MJ, Rohani P. **Modeling Infectious Diseases in Humans and Animals.** Princeton UP, 2008. DOI 10.1515/9781400841035.
68. Pearce-Duvet JMC. **The origin of human pathogens: evaluating the role of agriculture and domestic animals in the evolution of human disease.** Biol Rev 81:369–382, 2006. DOI 10.1017/s1464793106007020. [已核验]
69. Pamuk Ş. **The Black Death and the origins of the 'Great Divergence' across Europe, 1300–1600.** Eur Rev Econ Hist 11:289–317, 2007. DOI 10.1017/s1361491607002031.
70. Voigtländer N, Voth H-J. **The Three Horsemen of Riches: plague, war, and urbanization in early modern Europe.** Rev Econ Stud 80:774–811. DOI 10.1093/restud/rds034.
71. Alfani G, Murphy TE. **Plague and lethal epidemics in the pre-industrial world.** J Econ Hist 77:314–343, 2017. DOI 10.1017/s0022050717000092.
72. Jedwab R, Johnson ND, Koyama M. **Negative shocks and mass persecutions: evidence from the Black Death.** J Econ Growth 24:345–395, 2019. DOI 10.1007/s10887-019-09167-1.
73. Livi-Bacci M. **Population and Nutrition: An Essay on European Demographic History.** Cambridge UP, 1991. DOI 10.1017/cbo9780511563003. [已核验]
74. Alfani G. **A step forward toward solving the main mysteries in the history of plague?** PNAS, 2023. DOI 10.1073/pnas.2221925120. PMC10242720.

### 10.4 中文史料汇编（引自 Lee 2022 与 Liu et al. 2025 的参考文献，本次未直接查阅原书）
75. 张德二（主编）《中国三千年气象记录总集》，凤凰出版社，南京，2013。
76. 李文波《中国传染病史料》，化学工业出版社，2004。
77. 张志斌《中国古代疫病流行年表》，福建科学技术出版社，2007。
78. 中央气象局《中国近五百年旱涝分布图集》，中国地图出版社，1981。
79. 曹树基《中国人口史·清时期》，复旦大学出版社，2000。
80. 中国军事史编写组《中国军事史》（历代战争年表），解放军出版社，北京，1985。

### 10.5 本次**未能核实**、下一阶段必须补检的关键条目
- Benedictow 主张的黑死病约 **60%** 死亡率（本次只核到"三分之一"与"英格兰约一半"两种说法）。
- 1918 大流感的 R0 区间（Mills/Robins/Lipsitch 等）——检索到相关论文但摘要中无数值。
- 前现代疟疾、结核、血吸虫在中国/东亚的定量疾病负担——**完全没有找到可用参数**。
- 黑死病后英格兰实际工资上升的**具体倍数**（只核到定性的"wages and per capita income rose"）。
- Alfani & Murphy 2017 的正文（欧洲各次疫情死亡率的系统汇编，本应是 §4.4 最好的来源，被付费墙挡住）。
- Anderson & May (1991) *Infectious Diseases of Humans* 的标准参数表。
- 美洲"处女地疫情"的定量减员率（检索结果全是无数字的史学评论）。
- 黑死病空间扩散速度的 km/day 量级（多次检索未取得任何数值）。
