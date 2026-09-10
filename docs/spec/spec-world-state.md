# spec-world-state — L0 世界内核：状态本体 + 空间/时间/确定性契约

> **【生效范围（2026-09-10）】** 本文件是 Phase 0 的**规格草案**，未获整体批准。
> 四份规格由互不通气的 agent 写成，在若干接口上互不相容（见 `docs/INTEGRATION-REVIEW.md` §1）。
> **凡与 `docs/EXP-01-SPEC.md` 重叠的部分，以 EXP-01-SPEC 为准**；被取代的具体条款逐条列在 `docs/EXP-01-CONFLICTS.md`。
> 本文件保留作为论证与备选方案的来源，不作为实现依据。


- **slug**: `spec-world-state`
- **状态**: 规格草案 v0.1（Phase 0）
- **一句话主张**: **L0 只承认"物质、能量、人、位置、关系边、信息副本"六类东西；它没有制度、没有类别、没有名字、没有浮点数、没有全局自增计数器；一切被称为"国家/宗教/王朝/阶级/价格"的东西都必须在观察层被检测出来，而不是在内核里被存储。**
- **写作日期**: 2026-09-10
- **前置阅读（已实际读取）**: `MANDATE.md` 全文；红队 `pseudo-simulation`、`computational-feasibility`、`mandate-contradictions` 全文；简报 `abm-methodology`、`complex-systems-emergence`、`population-dynamics`、`agriculture-carrying-capacity`、`settlement-urbanization-spatial`、`china-eastasia-geography-archaeology`、`east-asia-climate-environment`、`state-formation`、`stratification-kinship-inheritance` 的相关章节；按需查阅 `provenance-replay-counterfactual`、`causality-bookkeeping`、`emergence-verifiability`。
- **证据等级约定**（全项目统一）: A=多来源实证且有量化参数；B=理论共识但量化弱；C=有实质争议或单一来源；D=无来源、我们自己的假设。
- **引用约定**: 一切引用写成 `brief-slug §小节` 或 `critique-slug F编号`。凡我自己的发明，显式标注 **［本文原创，无来源，D 级］**。
- **本规格的性质**: 这是一份**接口与不变量规格**，不是机制规格。它规定"世界底层能存什么、不能存什么、以什么单位存、在什么网格上、按什么时钟推进、在什么确定性保证下推进"。具体机制（生育率函数、产量函数、战争结算）属于其他规格。

---

## 0. 本规格做出的 12 项裁决（摘要）

| # | 裁决 | 依据 | 不可逆？ |
|---|---|---|---|
| D1 | 原语准入规则 = R1 随附性检验 + R2 参数类型白名单 + R3 禁读标签 + R4 写集静态可判 + R5 类型抹除不变 | `pseudo-simulation` S4 的两条准入规则的可执行化 | 是（决定内核 API 形状） |
| D2 | L0 六类实体：`Cell` / `Person` / `Cohort` / `Household` / `Site+Structure` / `InfoCopy`，外加两张内容寻址注册表（`Substance`/`Taxon`、`Recipe`）与一类 `RelationEdge` | `pseudo-simulation` S5「内核一等对象只有：个体、家户、地块、物质存量、关系边、信息副本」 | 是 |
| D3 | **义务/债务/贡赋不是关系边，是信息副本 + 物理胁迫能力** | 本文原创，无来源，D 级（从 D1-R1 推出） | 是 |
| D4 | 单位体系：g 干重 / kcal / 微人 µp / m / m² / L / mK / Q32 无量纲；**360 日世界年** | `agriculture-carrying-capacity` §4.3、`mandate-contradictions` 决定 18；360 日为本文原创 D 级 | 是 |
| D5 | 定点整数（int64/int32 + 声明标度），内核禁用一切浮点 | `computational-feasibility` F2 的三选一，选 (a) | 是 |
| D6 | 空间：**单一动态网格 H3 res 5（252.9 km²）**，覆盖含草原带的扩大窗口；1 km 只做一次性静态预计算并保留分布摘要；亚格子 = 冻结的位点集 + 图上的边 | 裁决 `settlement §11` vs `china-geography §3.1` vs `computational-feasibility` S3 三方冲突 | 是 |
| D7 | 时间：主时钟 1 世界年；合法年内细分 {1,2,4,12}；合法慢周期 {1,5,25,100}；Strang 对称分裂；相位顺序版本化为 `PHASE_ORDER_V1` | `population-dynamics` §2.2（MTI 40–65 年）、`computational-feasibility` F4/S6 | 是 |
| D8 | 实体 id = 内容/血缘派生 BLAKE3-128；**任何全局自增计数器都是构建期错误** | `causality-bookkeeping` F7 | 是（事后无法回改） |
| D9 | CBRNG：Threefry4x64-20，256 位 counter = (tick, id_lo, id_hi, slot‖draw)；流按机制封闭注册 | `abm-methodology` M4、`provenance-replay-counterfactual` M2 | 是 |
| D10 | 一切离散抽样用 **Gumbel-max，且 Gumbel 分量按候选项的内容哈希寻址**，禁止逆变换采样 | `provenance-replay-counterfactual` §2.7（Oberst & Sontag 2019）；"按内容哈希寻址"为本文原创 D 级 | 是 |
| D11 | 地图基底：**正式主线跑一次性创生扰动基底**；真实基底只进物理隔离的评估进程；扰动算子必须声明其等变类，校准量必须是该等变类下的不变量 | 裁决 `china-geography §3.0` vs `east-asia-climate §11.2`，采纳 `mandate-contradictions` F1 并补上校准可行性的解 | 是 |
| D12 | 世界边界：**草原/牧业生态带整体在世界之内**；窗口外为吸收边界，**默认外部通量恒为 0**；`world_external_flux` 接口在生产线编译期关闭 | `mandate-contradictions` 决定 5 提出问题，本文给出与其建议默认值**相反**的裁决 | 是 |

**这 12 条全部属于 `computational-feasibility` C5 所说的"必须在第一行内核代码之前定死"的类别。**

---

## 1. 原语准入规则的可执行形式

### 1.1 规则的来源与它要挡住什么

`pseudo-simulation` S4 给出了两条准入规则：

> 一个内核原语只有在满足以下两条时才被允许 ——
> - 它的定义**不引用任何制度**（"征税"不合格，因为它预设了政体；"以暴力威胁索取资源转移"合格）。
> - 它的全部参数都是物理量、信息量或关系边。

这两条是正确的方向，但**不可执行**：没有说"什么算制度"，也没有说"关系边"能带什么。下面把它变成五条可以写进 CI 的判定。

### 1.2 五条准入规则（规范文本）

一个候选内核原语 `p`（一个函数、一个字段、一个实体种类、一个关系边种类）被**准入**，当且仅当 R1–R5 全部成立。任一条不成立即为**构建期错误**，不是警告。

---

#### R1 —— 随附性检验（Supervenience Test）：定义不引用制度

**判定式**：

> 令 `B` = 世界的物理—信息—关系基底，定义为三元组
> `B = (PHYS, INFO, REL)`
> 其中 `PHYS` 是全部实体的全部物理量取值，`INFO` 是全部信息副本的 (持有者, 命题 id, 位置, 获取时刻, 保真记录) 元组集合，`REL` 是全部关系边的 (种类 id, 源 id, 宿 id, 物理权重) 元组集合。
>
> 一个词项 `t` 属于**制度集 I**，当且仅当**存在**两个世界状态 `w1, w2`，使得 `B(w1) = B(w2)` 逐位相同，但 `t(w1) ≠ t(w2)`。
>
> `p` 通过 R1，当且仅当 `p` 的**定义闭包**（p 的形式定义中出现的全部词项，及这些词项定义中出现的词项，传递闭包）与 `I` 的交集为空。

**为什么这条能判**：制度的定义性特征就是它**不随附于物理基底**——同一堆人、同一堆粮食、同一组亲子关系，可以是"一个王国"也可以不是，差别在于人们把它**算作**什么。而"算作什么"本身是信息副本的内容，不是一个独立的世界事实。所以：**凡是不随附于 (PHYS, INFO, REL) 的词项，一律不得成为内核原语；它只能作为观察层的检测器输出，或者作为世界内 agent 的信念（即一条 InfoCopy）。**

这正是 `pseudo-simulation` S5 的裁决"'国家'应该是世界里的人头脑中的一个信念对象，而不是模拟器的一个数据结构"的形式化版本。同时它把 `mandate-contradictions` C7（第 9 条只用在历史记载上，没用在社会范畴上）的裁决落到了类型系统里。

**［本文原创，无来源，D 级］**：把"不引用制度"操作化为随附性检验是我的设计。随附性概念本身是标准的（`complex-systems-emergence` §8.9 已经用它约束宏观变量必须是微观状态的纯函数，Rosas 的 `Ψ` 与 Barnett–Seth 的 `T` 都要求 `V_t = f(X_t)`），我把它反向用作**准入**判据。

**可执行形式**（CI 里怎么跑）：随附性是一个存在性断言，不能穷举。落地为两个可判定的代理：

1. **静态代理 R1a**：`p` 的定义只能引用 `PRIMITIVE_REGISTRY`（§3.1）中的条目。这张表是**封闭的、版本化的、人工审批的**。往表里加一条 = 一次内核版本变更（触发 `mandate-contradictions` F9 的"世界作废重跑"）。
2. **动态代理 R1b**：类型抹除测试 T-ERASE（§3.3）。它直接检验"改掉所有范畴标签，物理轨迹是否逐位不变"，这就是随附性的运行时验证。

---

#### R2 —— 参数类型白名单

`p` 的每一个参数与返回值，其类型必须落在下列**封闭集合**内：

| 类族 | 允许的类型 | 表示 | 例 |
|---|---|---|---|
| **PHYS** | 质量 `Mass_g` | int64，g 干重 | 粮食存量 |
| | 能量 `Energy_kcal` | int64，kcal | 摄入、劳动支出、投射的破坏能 |
| | 人数 `Pop_up` | int64，微人（1 人 = 10⁶ µp） | 队列人口 |
| | 劳动 `Labour_mh` | int64，毫人时（10⁻³ person-hour） | 劳动投入 |
| | 长度 `Len_m` / 面积 `Area_m2` / 体积 `Vol_L` | int64 | 距离、耕地、水 |
| | 温度 `Temp_mK` | int32，毫开（或毫摄氏距平） | 气候 |
| | 时间 `Tick_y` / `Day_d` | int64 / int16 | 主时钟、子时钟 |
| | 计数 `Count` | int64，无量纲整数计数（物理对象个数） | 杂草种子、牲畜头数 |
| | 速率 `Rate = PHYS / Time` | 同上除以时间 | 年危险率、kg/ha/yr |
| **INFO** | 比特数 `Bits` | int32 | 一条命题的编码长度 |
| | 副本数 `CopyCount` | int64 | 某命题在世界上的存活副本数 |
| | 副本位置 `CellId` / `HolderId` | 128-bit id | — |
| | 保真/失真概率 `Prob_q32` | int64（Q32） | 传抄错误率 |
| | 传播延迟 `Delay_d` | int32，日 | 消息延迟 |
| **REL** | 有向边 `Edge(kind_id, src_id, dst_id, weight)` | kind_id 来自封闭注册表；weight 类型必须是 PHYS 或 INFO 或 `Q32` | 亲子边、共居边 |
| **无量纲** | `Q32` 定点比值 | int64 分子 / 2³² | 食物比 E、份额、概率 |

**任何不在这张表里的类型都是不合格的**，特别包括：
- 任何"等级 / 阶段 / 级别 / 类型"枚举
- 任何字符串、任何显示名、任何标签 id
- 任何浮点数（见 §6）
- 任何"分数 / 评分 / 指数 / 强度"式的无微观所指的标量（合法性、稳定度、繁荣度、士气、威望、文明度）
- 任何以区域名/文化名/政体名为键的查表

**注意 R2 有意允许 `Q32` 无量纲比值**，否则 `E`（食物比，`population-dynamics` §2.1）这类一等状态量无法表示。但 `Q32` 是一个**危险的口子**：任何"我给它起个无量纲名字就行了"的字段都会往这里钻。堵法：**每一个 `Q32` 字段必须在 `PRIMITIVE_REGISTRY` 里声明它的分子与分母各是哪两个 PHYS/INFO 量**（`E = 食物供给 kcal / 食物需求 kcal`）。声明不出分子分母的 `Q32` 一律拒绝。**［本文原创，无来源，D 级］**

---

#### R3 —— 禁读标签

`p` 的实现不得读取：任何 composite 标签（§3.1）、任何字符串、任何不在 `PRIMITIVE_REGISTRY` 中的枚举判别式、任何实体的显示名、任何观察层写入的字段。

**执行**：内核 crate 对观察层 crate 的依赖必须为空（构建期 DAG 检查，`emergence-verifiability` F5 替代设计第 2 条）；内核 crate 内禁止出现用于比较的字符串字面量（lint）。

---

#### R4 —— 写集静态可判

`p` 必须在 `PRIMITIVE_REGISTRY` 里声明它的 `reads[]` 与 `writes[]`（字段级）。构建期用静态分析抽取实际访问集合，必须与声明**完全相等**（不是包含）。这是 `abm-methodology` M1 第 2 步 (b) 的强化：M1 只要求"一致"，本规格要求"相等"，因为**多声明的读集会污染 `pseudo-simulation` F3 的读取集闭包差集检测**（多声明的读会让 `declared_causes \ read_set_closure` 恒为空，使那条 CI 检测失效）。

---

#### R5 —— 类型抹除不变

`p` 在 T-ERASE（§3.3）下输出必须逐位不变。

---

### 1.3 通过的 10 个例子

每条给出：签名、参数类型、它凭什么通过、以及**它后来能被组合成什么**（这是原语的价值所在）。

| # | 原语 | 签名（类型标注） | 通过理由 | 它是哪些 composite 的构件 |
|---|---|---|---|---|
| **P1** | 以暴力威胁索取资源转移 | `coerced_transfer(src: HolderId, dst: HolderId, sub: SubstanceId, demand: Mass_g, threat_energy: Energy_kcal, target_defense: Energy_kcal, dist: Len_m, delay: Delay_d) -> (moved: Mass_g, injuries: Count, deaths: Pop_up, energy_spent: Energy_kcal)` | 全部参数 PHYS；"威胁"被还原为"施加破坏能的能力 + 目标已知这个能力"（后者是 P4 产生的 InfoCopy）；不引用政体、税率、身份 | 征税、贡赋、抢劫、地租、保护费、勒索 |
| **P2** | 代谢 | `metabolize(who: PersonId \| CohortRef, intake: Energy_kcal, requirement: Energy_kcal, days: Day_d) -> (Δstore: Energy_kcal, death_hazard: Rate)` | 纯能量守恒 + 一个年危险率 | 饥荒、营养不良、`population-dynamics` §2.1 的食物比 E |
| **P3** | 搬运 | `carry(actor: HolderId, sub: SubstanceId, m: Mass_g, from: CellId, to: CellId, mode_capacity: Mass_g, cost: Energy_kcal_per_g_per_m) -> (arrive_tick: Tick_y, lost: Mass_g, spent: Energy_kcal)` | 质量、能量、长度、时间 | 贸易、军队补给、迁徙、漕运 |
| **P4** | 复制信息 | `copy_info(src: InfoCopyId, to: HolderId, delay: Delay_d, corruption: Prob_q32) -> InfoCopyId` | 纯 INFO；命题内容对内核是不透明比特 | 谣言、教义传播、官方公文、口述史、`mandate-contradictions` F6 的命题图 |
| **P5** | 生育 | `bear(mother: PersonId, father: PersonId \| Null, tick: Tick_y, maternal_store: Energy_kcal, hazard: Rate) -> PersonId` + 两条 `parent_of` 边 | 生物物理 + REL；不引用婚姻、合法性、继承 | 世系、家族、王朝、继承纠纷 |
| **P6** | 把劳动施于土地 | `work_land(hours: Labour_mh, cell: CellId, recipe: RecipeId, soil_n: Mass_g, weed_bank: Count, water: Vol_L) -> (out: Mass_g, Δsoil_n: Mass_g, Δweed: Count, hours_used: Labour_mh)` | 全 PHYS；`recipe` 是内容寻址的系数向量（§2.6），不是名字 | 农业、休耕制、灌溉、内卷 |
| **P7** | 藏匿与不交出 | `conceal(holder: HolderId, sub: SubstanceId, m: Mass_g, cost: Energy_kcal) -> detect_prob: Prob_q32` | PHYS + INFO（藏匿改变的是别人能获得的信息量） | 逃税、瞒报、黑市、`state-formation` M6 的可征取性 `ε_grab` |
| **P8** | 破坏结构物 | `damage(s: StructureId, applied: Energy_kcal, mass: Mass_g, material: SubstanceId) -> (destroyed: Mass_g, repair: Labour_mh)` | 纯 PHYS | 攻城、决堤、拆城墙、水利失修 |
| **P9** | 施加致命暴力 | `apply_lethal_force(actor: PersonId, target: PersonId, weapon_energy: Energy_kcal, protection: Mass_g_per_m2, dist: Len_m, surprise: Bits) -> death: bool` | 纯 PHYS + 一个信息量（突然性 = 目标缺少的比特） | 战争、刺杀、械斗、处决 |
| **P10** | 发出一条关于未来转移的命题 | `emit_claim(author: HolderId, about_subject: EntityId, sub: SubstanceId, amount: Mass_g, due: Tick_y) -> InfoCopyId` | 纯 INFO。它**不产生任何强制力**；强制力只能来自 P1 | **债务、贡赋义务、契约、税额、租约、誓约** —— 全部由 P10（有人相信）+ P1（有人能打）合成 |

**P10 是这份清单的核心。** 它体现了 D3：**一条没有人相信、也没有人能强制的义务，在这个世界上不存在。** 把义务做成 L0 的关系边，等于给它一个不依赖任何人信念与暴力的独立存在，那就是把制度偷渡进物理。做成"命题副本 + 胁迫能力"之后，"赖账""改朝换代后旧债作废""债权人死了债就没了"这些现象自动可能，而且它们的因果链是机械的。

---

### 1.4 不通过的 10 个例子

每条给出：它违反哪条规则、以及**合格的分解**。

| # | 不合格原语 | 违反 | 为什么（一句话） | 合格的分解 |
|---|---|---|---|---|
| **F1** | `levy_tax(polity: PolityId, rate: f32)` | R1, R2, R5 | `polity` 与 `rate` 都不随附于基底：同一堆人同一堆粮，"是不是一个政体""税率是多少"取决于人们把它算作什么 | P10（若干人持有"应向 X 交出 Y"的命题）+ P1（X 有能力惩罚不交者）+ P7（有人藏匿） |
| **F2** | `promote_to_bureaucrat(p: PersonId, rank: Rank)` | R1, R2 | "官职""品级"是制度对象；同一个人同一份存量，是不是官取决于别人的承认 | P10（一批人持有"P 有权代 X 索取"的命题）+ P1（P 实际上做到了）+ P3（P 的存量流向 X） |
| **F3** | `found_state(cells: [CellId]) -> PolityId` / `spawn_dynasty()` | R1, R3 | 这是 composite 的构造函数，等价于 `pseudo-simulation` L1 层显式脚本 | 不存在。政体只能被观察层的检测器**识别**出来（`state-formation` §9.a 的观测器，且必须由观察层调用） |
| **F4** | `polity.legitimacy: f32` | R1, R2 | 合法性没有微观所指；`complex-systems-emergence` §8.8 已判定 `if legitimacy < 0.3 → rebellion` 就是剧情树，且 `pseudo-simulation` S5 称它是"最坏的字段" | 持有"应服从 X"这条命题的人数 / 副本分布 / 这些人的位置与资源（全部是 InfoCopy 的可计算聚合，且**只在观察层计算**） |
| **F5** | `enum PolityStage { Band, Tribe, Chiefdom, State }` 及任何对它的读取 | R1, R2, R3, R5 | `state-formation` AP1 已明确禁止；Feinman & Neitzel 1984 证明变异连续，Turchin et al. 2018 的 PC1 解释 77.2% 方差且九个特征载荷相同 | 可测量的连续/整数状态：控制树深度、角色种类数、贡赋流经层数、控制半径（`state-formation` AP1 原文），**且只在观察层计算** |
| **F6** | `marry(a: PersonId, b: PersonId)` | R1 | 婚姻是制度：谁算已婚取决于共享信念与规则。这条最容易被误认为"自然事实" | `co_reside` 边（物理共居）+ `sexual_partner_recent` 边（物理）+ 一批人持有"a 与 b 是一对"的 InfoCopy + 财产转移记录（P3）。`stratification-kinship-inheritance` §3.13 的婚姻财产转移就是这样合成的 |
| **F7** | `pay_wage(employer, worker, amount: Money)` | R1, R2 | 预设了货币与雇佣关系。货币尤其危险：它是一个**信念 + 物质**的复合体 | P6（worker 投入 Labour_mh）+ P3（某种 Substance 的转移）+ P10（关于未来转移的命题）。"这块金属值多少"只能是若干 InfoCopy 的聚合，属观察层 |
| **F8** | `declare_war(a: PolityId, b: PolityId)` | R1, R3 | 预设政体 + 一个有规范效力的言语行为 | 一组 Actor 在同一 tick 提交了指向同一批目标的 P9/P1 意图。"战争"是观察层对暴力事件流做时空邻近聚类（`complex-systems-emergence` M7 的雪崩定义）后命名的 |
| **F9** | `inherit(heir: PersonId, estate: EstateId)` | R1 | 继承规则是制度；`stratification-kinship-inheritance` §3.5 的继承规则本身就是要被演化出来的东西 | 死亡后该存量的 `holds` 边失去背书 → 谁最终持有由 P1（胁迫能力）、`co_reside`（谁在场）、以及关于"应由谁继承"的 InfoCopy 分布共同决定 |
| **F10** | `cell.carrying_capacity: f32` / `cell.prosperity` / `polity.stability` | R1, R2 | `agriculture-carrying-capacity` AP 8.2 明确禁止"把承载力 K 当作环境常数写进格网"；`§7.1` 甚至质疑承载力概念本身可用性 | 承载力不是状态，是**每年重算的输出**：由 `work_land` 的产出、劳动供给、绑定约束（LABOUR/LAND/WATER/NITROGEN/WEED/TIME_WINDOW/SEED，见 `agriculture-carrying-capacity` §3.0）共同决定，且**内核不存储它** |

**另外还有一批显然不合格、但一定会有人想加的**（写进禁用清单，见 §2.4）：`Dynasty` 对象、`Religion` 类、`Class` 枚举、`tech_tree.yaml`、`culture.bonus_yield`、`event.cooldown`、`region_modifier["关中"] = +0.1`、`ensure_at_least_one_polity()`、`polity.age_since_founding`。

### 1.5 准入争议的裁决程序

R1 的随附性检验在边界上会有真实争议（"共居"算不算制度？"持有"算不算制度？）。裁决程序：

1. 提出者必须写出一对 `(w1, w2)`：基底逐位相同、该词项取值不同。**写得出来 → 属于 I → 拒绝。**
2. 写不出来 → 提出者必须给出该词项到 (PHYS, INFO, REL) 的**显式计算函数**，且该函数进 `PRIMITIVE_REGISTRY`。
3. 两者都做不到 → 拒绝，并记入"我们没能原语化的概念"清单（这份清单本身是研究产出）。

例：`holds`（持有）——写不出 `(w1, w2)`，因为我们把 `holds` 定义为"该实体处在 X 的物理控制范围内且 X 有能力阻止他人取走"，这是纯 PHYS。通过。
例：`property`（所有权）——写得出：同一批人同一批物，是不是"他的"取决于别人承不承认。拒绝。**所有权 = holds + 一批 InfoCopy。** 这正是 `stratification-kinship-inheritance` §3.6 场址封闭机制想要的形态：产权与阶级同时诞生，而不是产权先被设定。

### 这一节禁止了什么

- 禁止任何以制度词汇命名的内核函数（征税、册封、继承、结婚、宣战、立法、册立、任官、发行货币）。
- 禁止任何不随附于 (PHYS, INFO, REL) 的字段，无论它叫什么名字、藏在哪个结构体里、还是从配置文件读进来。
- 禁止 `Q32` 字段声明不出分子与分母。
- 禁止 `reads[]/writes[]` 声明与静态分析结果只满足"包含"而不满足"相等"（这堵住了通过多声明读集来使因果差集检测失效的路）。
- 禁止内核 crate 依赖观察层 crate；禁止内核内出现用于比较的字符串字面量。
- 禁止把"义务/债务/税额/契约"做成关系边——它们只能是 InfoCopy + 胁迫能力（D3）。
- 禁止在没有走完 §1.5 三步裁决程序的情况下往 `PRIMITIVE_REGISTRY` 里加条目。

---

## 2. L0 完整状态清单

### 2.1 单位体系（D4）

**原则**（`mandate-contradictions` 决定 18）：物质以 kg 干重计、能量以 kcal 计、人以人年计；标定优先用比率而非绝对值，因为"亩有 10 种大小、清代银两 56 种地区标准"（`agriculture-carrying-capacity` §6.6）。本规格把它落成整数标度。

| 量纲 | 单位 | 类型名 | 表示 | 标度 | 量级校验 |
|---|---|---|---|---|---|
| 质量（干重） | 克 | `Mass_g` | int64 | 1 | 1 亿人 × 300 kg/yr = 3×10¹³ g，int64 余量 3×10⁵ 倍 |
| 能量 | 千卡 | `Energy_kcal` | int64 | 1 | 1 亿人 × 2300 kcal/d × 360 d = 8.3×10¹³，余量充足 |
| 人数 | 微人 | `Pop_up` | int64 | 10⁻⁶ 人 | 1 亿人 = 10¹⁴ µp |
| 劳动 | 毫人时 | `Labour_mh` | int64 | 10⁻³ person-hour | 1 亿人 × 2000 h/yr = 2×10¹⁴ mh |
| 长度 | 米 | `Len_m` | int64 | 1 | — |
| 面积 | 平方米 | `Area_m2` | int64 | 1 | 一格 252.9 km² = 2.529×10⁸ m² |
| 体积/水 | 升 | `Vol_L` | int64 | 1 | 一格 100 mm 降水 = 2.53×10¹⁰ L |
| 温度 | 毫开/毫摄氏距平 | `Temp_mK` | int32 | 10⁻³ | ±50 K → ±5×10⁴ |
| 土壤氮 | g/m² | `NDens_g_m2` | int32 | 1 | 0–2000 |
| 主时钟 | 世界年 | `Tick_y` | int64 | 1 | — |
| 年内时间 | 世界日 | `Day_d` | int16 | 1 | 0..359 |
| 无量纲 | Q32 | `Q32` | int64 | 2⁻³² | 1.0 = 4 294 967 296；`E` 可达 3.16（`population-dynamics` §2.1 的 `E_m`），远在 int64 内 |
| 年危险率 | Q32/yr | `Rate_q32` | int64 | 2⁻³² /yr | 死亡率 0.0328（`population-dynamics` §2.1 的 `d̂`）= 140 918 108 |

**世界年 = 360 日**（D4，**［本文原创，无来源，D 级］**）。理由：合法子时钟集合 {1,2,3,4,6,12} 必须整除年长，否则 `computational-feasibility` F4/S6 警告的**拍频**会把宏观周期变成 tick 表的产物。360 = 2³·3²·5 被 1/2/3/4/5/6/8/9/10/12/15/... 整除。代价：与天文年差 1.4%，因此**一切来自文献的 per-day 参数必须乘 360 而不是 365**，且这个换算常数只能出现在一个地方（`units::DAYS_PER_YEAR = 360`），由 lint 强制。世界内部没有真实历法，所以 1.4% 不产生任何对不上的问题；它只影响我们把文献参数搬进来时的算术。

**禁止**：
- 任何"亩""石""斗""两"式的历史单位进入 L0（`agriculture-carrying-capacity` AP 8.10）。历史单位只能出现在**观察层的展示**与**世界内 agent 的信念**里（世界内的人当然可以用自己的乱七八糟的单位——那是 InfoCopy 的内容）。
- 任何以"标准人"为单位的量。人有年龄性别，需求由 `ρ_x`（`population-dynamics` §2.1）加权。
- 任何"金额/价格/货币"单位（见 F7）。

### 2.2 实体类型总表

L0 只有下列实体种类。**这张表是封闭的**；加一类 = 内核版本变更。

| 种类 | 数量级上限 | id 生成 | 是否逐 tick 遍历 | 存在于 |
|---|---|---|---|---|
| `Cell` | ~1.4×10⁵（含海）/ ~9×10⁴ 陆 | H3 index + basemap_hash | 是 | 全程 |
| `Cohort` | Cell × 20 年龄段 × 2 性别 × 6 存量档 ≈ 1.1×10⁷ 槽位（稀疏，活跃 ≤ 2×10⁶） | (cell_id, age_bin, sex, stock_band) | 是（稀疏） | 全程 |
| `Person`（L2 个体） | ≤ 3×10⁴ 活人 | 血缘派生哈希 | 是 | 被提升者 |
| `Household` | ≤ 2×10⁵ | 内容派生哈希 | 是 | 有定居的格 |
| `Site` | Cell × ≤16 = ≤2.2×10⁶ | 内容派生哈希 | **否**（冻结） | 全程 |
| `Structure` | ≤ 3×10⁵ | 内容派生哈希 | 否（按事件） | 建成后 |
| `RelationEdge` | ≤ 3×10⁶ | 内容派生哈希 | 否（按需索引） | — |
| `InfoCopy` | ≤ 5×10⁶ | 内容派生哈希 | 否（按事件 + 年度衰减批处理） | — |
| `Substance` / `Taxon`（注册表） | ≤ 512 / ≤ 2048 | **属性向量的哈希** | 否（创生冻结） | 全程 |
| `Recipe`（注册表） | ≤ 4096 | **系数向量的哈希** | 否（可增长） | — |
| `Proposition`（注册表） | ≤ 10⁶ | 结构化内容的哈希 | 否 | — |
| `LandParcel` | ≤ 10⁵ | 内容派生哈希 | 是（稀疏） | L2 家户 |

实体数硬上限来自 `computational-feasibility` S4「每类实体都要有硬上限」，具体数字沿用该红队的建议（活人 3×10⁴、聚落 5×10⁴ 量级、网络边 3×10⁶），该红队自报这些数字是 **D 级、按预算反推、无外部依据**。本规格把"聚落 ≤5000"改为 `Household ≤ 2×10⁵` + `Site ≤ 2.2×10⁶`（位点不逐 tick 遍历所以不占预算），因为本规格取消了独立的"聚落"实体种类（聚落是 composite，见 §3.1）。

### 2.3 每类实体的字段

下面给出字段级 schema。`[hot]` = 每 tick 可能被写、进增量快照；`[cold]` = 创生冻结或极少变，内存映射共享；`[idx]` = 派生索引，不进快照、不进哈希。

#### 2.3.1 `Cell`

```
Cell {
  // ---- 身份 ----
  id            : CellId128      [cold]  // H128("cell" || basemap_hash || h3_index_res5)
  h3            : u64            [cold]  // H3 res-5 index（仅静态预计算与观察层可读）

  // ---- 静态几何与地形（创生冻结，进 basemap_hash）----
  land_area     : Area_m2        [cold]
  water_area    : Area_m2        [cold]
  elev_p        : [Len_m; 7]     [cold]  // {min,p10,p25,p50,p75,p90,max} —— 分布摘要，不是均值
  slope_p       : [Q32; 7]       [cold]
  twi_p         : [Q32; 7]       [cold]  // 地形湿度指数分位
  arable_frac   : Q32            [cold]  // 由 1 km 预计算聚合
  max_patch     : Area_m2        [cold]  // 格内最大连通可耕斑块（尾部量，见 comp-feas S3.2）
  soil_class    : SoilVecId      [cold]  // 指向 Substance 风格的属性向量，不是名字
  coast_len     : Len_m          [cold]
  neighbors     : [CellId128; 6] [cold]  // H3 六邻；五边形格显式标记
  is_pentagon   : bool           [cold]

  // ---- 水文骨架（创生冻结 + 罕见事件重写）----
  river_out     : Option<CellId128>  [hot]  // 出流邻格（改道时改写）
  river_q_mean  : Vol_L_per_y        [hot]
  navigable     : bool               [hot]
  bed_elev      : Len_m              [hot]  // 悬河：河床高程随淤积上升（east-asia-climate M6）

  // ---- 气候携带态（只有高频分量在这里）----
  clim_ar       : [i32; 4]       [hot]  // 温度/湿润各 2 阶 AR 状态
  soilmoist     : Vol_L          [hot]
  eco_lag       : [i32; 2]       [hot]  // 植被/土壤湿度滞后态（east-asia-climate M4）

  // ---- 生物物理存量（慢变量，路径依赖的载体）----
  soil_n        : NDens_g_m2     [hot]
  topsoil_mm    : i32            [hot]
  salt_g_m2     : i32            [hot]
  weed_bank     : Count_per_m2   [hot]
  biomass       : [(TaxonId, g_per_m2); 8] [hot]  // 只保留 top-8 taxa

  // ---- 土地使用（格级聚合；地块级只在 L2 存在）----
  cultivated    : Area_m2        [hot]
  fallow_age_hist : [Area_m2; 8] [hot]  // 按休耕年龄分桶的面积
  irrigated     : Area_m2        [hot]

  // ---- 物质汇（守恒审计用）----
  sink          : SparseMap<SubstanceId, Mass_g> [hot]

  // ---- 派生索引（不进快照、不进哈希）----
  cohort_slots  : [CohortRef]    [idx]
  sites         : [SiteId]       [idx]
  households    : [HouseholdId]  [idx]
}
```

热字段规模估算：约 200 B/格 × 9×10⁴ 陆格 = **18 MB**。冷字段约 400 B/格 = 36 MB（跨世界线共享只读映射）。

**`Cell` 里明确没有的字段**：`carrying_capacity`、`fertility_bonus`、`region_id`、`region_name`、`owner_polity`、`development`、`culture`、`is_capital`、`terrain_type`（地形"类型"是 composite；只有分布摘要）。

#### 2.3.2 `Cohort`（L0 队列层）

沿用 `population-dynamics` §3.11 / 附录 A.1 的三层结构，但**改动一处**：

```
Cohort {
  key   : (CellId128, age_bin: u8 /*0..19, 5 岁一档*/, sex: u8, stock_band: u8 /*0..5*/)
  n     : Pop_up            [hot]
  store : Energy_kcal       [hot]  // 该队列持有的可食能量存量（人均可算）
  e     : Q32               [hot]  // 食物比 E（population-dynamics §2.2 的一等状态量）
  siler : [Q32; 5]          [hot]  // Siler 死亡率内核参数（population-dynamics §2.8）
  a2_shock : Q32            [hot]  // 外生冲击通道
}
```

**改动与理由**：`population-dynamics` §3.11 用 `wealth_quintile`（财富五分位）作为队列维度。本规格改为 **`stock_band` = 人均物质存量的绝对对数档**（6 档，按 kcal 等值物的 log₂ 分段）。理由：五分位是一个**相对统计量**，把它做成内核状态维度，等于让内核读一个全人口的排序结果——这与 `complex-systems-emergence` §8.8 判定为剧情树的"把宏观指标当触发器"是同一个形状，而且它会制造一个虚假的反馈（人口分布一变，所有人的档位都变，即使没有任何人的物质发生变化）。绝对档随附于物理基底，通过 R1。**［改动为本文原创，无来源，D 级］**

代价：绝对档的边界是 6 个 D 级常数，且在长期财富总量增长时会全部挤进顶档。缓解：档位边界是**创生时冻结的、按世界种子抽取的**，且档数 6 不变；顶档溢出率是一个必须报告的健康指标（>60% 说明档位设计失效，需要改内核版本而不是改数据）。

#### 2.3.3 `Person`（L2 个体层）

```
Person {
  id        : PersonId128    // H128("person" || mother_id || father_id || birth_tick || birth_slot)
  birth_tick: Tick_y
  sex       : u8
  cell      : CellId128      [hot]
  site      : Option<SiteId> [hot]
  body_store: Energy_kcal    [hot]   // 体能储备，P2 的状态
  injury    : Energy_kcal    [hot]   // 累积损伤（以修复所需能量计）
  siler     : [Q32; 5]       [hot]
  frailty   : Q32            [cold]  // 出生时抽取，终身不变（population-dynamics A.2 第 5 点）
  death_tick: Option<Tick_y> [hot]
}
```

**明确没有的字段**：`name`（名字是世界内的 InfoCopy）、`class`/`rank`/`title`/`office`、`loyalty`、`ambition`、`competence`、`piety`、`culture_id`、`religion_id`、`ethnicity`。人物的"能力"如果需要，只能表现为物理量（体能储备、掌握的 Recipe 的保真度、持有的 InfoCopy 集合、`taught_by` 边的入度）。

`stratification-kinship-inheritance` §3.16.3 建议给个体挂 `rule_tags: Set<RuleTagId>`（免税、免刑、可仕、人身可售……）。**本规格拒绝把 `rule_tags` 放进 L0**：一条"免税"标签的效力完全取决于别人承不承认与谁能强制，它不随附于基底，违反 R1。合格分解：`rule_tag` 的每一个具体后果都由 InfoCopy（一批人相信"对 P 不应索取"）+ 胁迫能力共同产生。**这意味着"阶层"在 L0 里彻底没有存储位置**——这正是 `pseudo-simulation` S5 与 `stratification-kinship-inheritance` A1 共同要求的。代价：§3.16.4 的"贵族出现了"六条判据必须整体搬到观察层，且 C3（"存在按身份而非按财富适用的规则"）要改写为"存在一批被广泛持有的、以身份为条件的命题，且其行为后果可测"。这是一个真实的实现难度上升，记入 §11 开放问题。

#### 2.3.4 `Household`

按 `pseudo-simulation` S5 授权保留为一等对象，但**贫化到只剩物理内容**：

```
Household {
  id         : HouseholdId128  // H128("hh" || sorted(founder_person_ids) || founding_tick)
  cell       : CellId128       [hot]
  site       : Option<SiteId>  [hot]
  founded    : Tick_y          [cold]
  dissolved  : Option<Tick_y>  [hot]
  pool       : SparseMap<SubstanceId, Mass_g>  [hot]   // 共用存量池
  parcels    : [LandParcelId]  [idx]
}
```

成员关系 = 指向该 household 的 `co_reside` 边。**没有 `head_id`**（户主是制度）、**没有 `type`**（核心/主干/联合家庭是分类学，属观察层）、**没有 `lineage_id`**（宗族是 composite）、**没有 `surname`**。

#### 2.3.5 `Site` 与 `Structure`（亚格子）

```
Site {
  id        : SiteId128     [cold]  // 创生冻结：H128("site" || cell_id || site_index)
  cell      : CellId128     [cold]
  sub_xy    : (u16, u16)    [cold]  // 格内相对坐标，1/65536 格边
  suit      : [Q32; 6]      [cold]  // 由 1 km 预计算给出的适宜度分位向量
  dist_water: Len_m         [cold]
  defensib  : Q32           [cold]
  occupied_by : Option<HouseholdId | SettlementRef> [hot]
}

Structure {
  id        : StructureId128
  site      : SiteId
  material  : SubstanceId
  mass      : Mass_g        [hot]
  decay     : Rate_q32      [cold]
  built_tick: Tick_y        [cold]
}
```

**没有 `Settlement` 实体。** 聚落是 composite：观察层把"同一格内共享 Site 邻域、且互相有高频 `co_present` 边的家户集合"聚类为聚落。理由：`settlement-urbanization-spatial` §8 与 `complex-systems-emergence` M5 都指出，一旦聚落面积与人口的关系被写死，标度指数就是定义出来的而不是涌现的；只要 `Settlement` 是一等对象，它就会有 `area` 字段，就会有人写 `area = f(N)`。取消这个实体是唯一结构性的堵法。

代价：`settlement-urbanization-spatial` M1–M10 的全部机制都要改写成"作用在家户与位点上"的形式，M7 的四层空间表示中的 L1 动态 Voronoi 被取消（见 §4.3）。这是一次真实的能力削减，必须签字。

#### 2.3.6 `RelationEdge`

**封闭的边种类注册表**（加一类 = 内核版本变更）：

| kind_id | 名称 | 语义（必须是物理/生物事实） | weight |
|---|---|---|---|
| 1 | `gestated_by` | 生物母亲 | — |
| 2 | `sired_by` | 生物父亲（可为空） | — |
| 3 | `co_reside` | 共用一个 Household 的存量池且同 Site | `Q32` 存量取用权重 |
| 4 | `co_present` | 同 tick 同 Site 出现（瞬时，年末衰减） | `Day_d` 共处天数 |
| 5 | `sexual_partner_recent` | 近 N 年发生生殖接触 | `Count` |
| 6 | `holds` | 物理控制某存量/结构物，且有能力阻止他人取走 | `Energy_kcal` 阻止能力 |
| 7 | `taught_by` | 一次 Recipe/命题的传授事件（信息传输） | `Q32` 保真度 |
| 8 | `damaged_by` | 一次 P8 事件 | `Mass_g` |
| 9 | `killed_by` | 一次 P9 事件 | — |
| 10 | `info_source_of` | InfoCopy 的来源链 | — |

**明确不存在的边种类**：`subject_of`、`vassal_of`、`member_of`、`married_to`、`owns`、`owes`、`allied_with`、`worships`、`belongs_to_clan`。全部由 InfoCopy 合成。

#### 2.3.7 `InfoCopy` 与 `Proposition`

```
Proposition {
  id     : PropId128   // 结构化内容的哈希；内核对内容不透明
  form   : PropForm    // 封闭的命题形式注册表（见下）
  args   : [EntityRef] // 指向 L0 实体或其他 Proposition
}

InfoCopy {
  id           : InfoId128  // H128("info" || prop_id || holder_id || acq_tick || acq_slot)
  prop         : PropId128
  holder       : HolderId
  cell         : CellId128       [hot]
  acquired     : Tick_y          [cold]
  source       : Option<InfoId128> [cold]
  distortion   : [u8; 8]         [cold]  // 失真算子链的编码（mandate-contradictions F6）
  decay_rate   : Rate_q32        [cold]
  strength     : Q32             [hot]   // 记忆强度；归零即遗忘
  substrate    : Substrate       [cold]  // {memory, speech_only, marked_object, inscribed}
}
```

**命题形式必须是封闭的、且全部只引用 L0 原语**（`mandate-contradictions` 决定 14「世界内不存在自然语言」）。起始集合：
- `Observed(entity, field, value_bucket, tick, cell)` —— "我看见 X 在 T 年有 Y"
- `WillTransfer(subject, recipient, substance, amount, due_tick)` —— P10 的载体
- `ShouldNotTake(subject, from_holder, substance)` —— 禁忌/豁免的载体
- `ShouldDefer(subject, to_entity, scope_cells)` —— "应服从"的载体（"国家"就住在这里）
- `CausedBy(event_ref, event_ref)` —— 世界内的因果信念（可以是错的）
- `Recipe_Known(recipe_id, fidelity)` —— 技术知识
- `SameKindAs(entity, entity)` —— 世界内的范畴化（"我们是一伙的"）
- `Named(entity, symbol_id)` —— 名字。`symbol_id` 来自世界内音系/构词引擎（`mandate-contradictions` 决定 16），**不是字符串**

**关键**：内核对 `PropForm` 的处理必须是**结构性的**（传播、失真、遗忘、比对是否相同），**不得对内容做语义解释**。唯一的例外是 `Recipe_Known` 与 `WillTransfer` / `ShouldDefer` / `ShouldNotTake`，它们会被行为机制读取——但读取的是它们的**结构化参数**（谁、多少、何时），不是语义标签。这条界线必须在 `PRIMITIVE_REGISTRY` 里逐条声明。

#### 2.3.8 `Substance` / `Taxon` / `Recipe`（内容寻址注册表）

```
Substance {
  id : H128(property_vector)      // ★ id 就是属性向量的哈希
  props : {
    energy_density : kcal_per_g,
    protein_frac   : Q32,
    storage_decay  : Rate_q32,     // 年腐损率
    density        : g_per_L,
    hardness       : Q32,
    melt_energy    : kcal_per_g,
    toxicity       : Q32,
    ...            // 封闭的属性轴集合
  }
}
```

**这是本规格最重要的一条防泄漏设计**：物质没有名字，只有属性向量；两个属性完全相同的物质就是同一个物质。于是**"小麦""青铜""丝"这些词在 L0 里根本不存在**，世界自己长出来的作物就是它自己的作物，而不是"被我们叫做小麦的那个东西"。`Taxon`（生物类群）同理，属性轴包括生境包络、生物量产出曲线、繁殖体扩散核、**对选择的可响应速率**（驯化的物理基础，不是"是否可驯化"的布尔）。

`Recipe` = 输入 Substance 系数向量 + 劳动系数 + 格条件要求 + 输出 Substance 系数向量，id 是这整套系数的哈希。于是"农业""冶金""织布"不是 L0 概念；L0 只有一大堆系数向量，其中某些恰好把野生 Taxon 的种子变成更多种子。

**创生时的注册表由 `world_seed + 声明的先验` 生成**，不是从真实物种表抄的（见 §7.3）。

#### 2.3.9 `LandParcel`（只在 L2 存在）

```
LandParcel { id, cell, area_m2, holder: HouseholdId, fallow_age: u8, soil_n_local: NDens_g_m2 }
```

数量上限 10⁵。L0 层的耕地只在 `Cell.cultivated` / `Cell.fallow_age_hist` 上聚合。**代价**：地块细碎化、地块基尼、水权纠纷的空间结构不可表示（`settlement-urbanization-spatial` §11.5 C 已列出这条）。

### 2.4 明确禁止的字段清单（可 grep 的黑名单）

下表进 `charter/forbidden_fields.toml`，CI 用 AST 级检查（不是字符串 grep，因为可以改名绕过）：**任何 L0 结构体字段，其声明的类型不在 R2 白名单内，或其 `PRIMITIVE_REGISTRY` 条目缺失，即构建失败。** 黑名单只是给人看的说明书。

| 类别 | 禁止的字段/类型 | 依据 |
|---|---|---|
| 无微观所指的宏观标量 | `legitimacy` `stability` `prosperity` `unrest` `morale`(群体级) `happiness` `development` `civilization_level` `tech_level` `culture_score` `PSI` `carrying_capacity` `authority` `prestige`(实体级) | `pseudo-simulation` S5；`complex-systems-emergence` §8.8/§8.9；`agriculture-carrying-capacity` AP 8.2 |
| 阶段/类别枚举 | `enum PolityStage` `enum Class` `enum SettlementType` `enum GovernmentType` `enum Era` `enum SocietyType` `enum TechEra` | `state-formation` AP1；`stratification-kinship-inheritance` A1 |
| 回溯性史学建构对象 | `Dynasty` `Empire` `Kingdom` `Civilization` `Religion` `Ethnicity` `Nation` `Culture` `Polity` `Settlement` `Class` | `pseudo-simulation` S5（"`Dynasty` 是致命的"）；本规格追加 `Settlement`、`Polity` |
| 真实历史名词 | 任何真实地名/族名/朝代名/人名/作物名/语言名，出现在代码、数据文件、prompt、注释以外的任何地方 | `china-eastasia-geography-archaeology` §3.0(c) 与 AP13；`abm-methodology` M12 |
| 手工区域修正表 | 任何以区域名/区域 id 为键的属性表 | `china-eastasia-geography-archaeology` AP3（"应写成 lint 规则禁止"） |
| 目标导向调节器 | `cooldown` `next_allowed_tick` `min_polities` `respawn_threshold` `difficulty` `pacing` `drama_budget` | `pseudo-simulation` S3 表格全部九行 |
| 复合体的年龄 | `polity.age_since_founding` `dynasty.years` `religion.age` | `cliodynamics-secular-cycles` §3.0 写法 A（不要 `age` 字段），经 `pseudo-simulation` S6 转述 |
| 重要性/戏剧性 | `significance` `importance` `interest` `drama` —— **可以存在，但只能在观察层**，内核对它零可见性 | `pseudo-simulation` G3/G8；`mandate-contradictions` F7 |
| LOD 相关 | LOD 调度器读取"事件密度/重要性/年份/是否存在国家"的任何字段 | `mandate-contradictions` F4；`computational-feasibility` S1；`pseudo-simulation` S8 |
| 浮点 | `f32` `f64` 出现在内核 crate 的任何位置 | `computational-feasibility` F2（本规格选 (a)） |
| 环绕/饱和算术 | `wrapping_*` `saturating_*` `clamp` `min`/`max` 用于约束状态量 | `pseudo-simulation` S3（clamp 制造隐式吸引子且污染均值）；`abm-methodology` AP5 |
| 全局自增 | 任何 `next_id += 1` | `causality-bookkeeping` F7 |

**关于 clamp 的例外程序**：确实存在**表示性下界**（质量不能为负、概率不能超过 1）。规则：
1. 表示性下界必须由**类型**保证（`Mass_g` 是无符号语义，减法用 `checked_sub` 且失败即中止），而不是由 clamp 保证。
2. 若某个机制会算出负质量，那是**机制缺陷**，必须改机制，不得加 clamp（`pseudo-simulation` S3 替代设计第 3 条）。
3. 唯一允许的 clamp 是 Gumbel 抽样中 `u` 到 `[2⁻³², 1−2⁻³²]` 的裁剪（数值表示边界，不是行为边界），且必须带 `# GATED(reason=numeric_representation, ...)` 注释并记录触发率。触发率 > 10⁻⁹/抽样即报警。

### 2.5 守恒审计（定点整数的最大回报）

每 tick 的 `commit` 相位结束时，对每一种 `Substance`：

```
Σ_holders stock(s) + Σ_cells sink(s) + Σ_in_transit(s)
  ==  prev_total(s) + Σ declared_sources(s) − Σ declared_sinks(s)
```

**int64 精确相等**。不相等即**硬中止**，打印第一个不平衡的 (substance, holder, tick, phase)。同样对 `Energy_kcal`（源项 = 光合固定 + 摄食转化，汇项 = 代谢 + 腐损 + 燃烧，每一项都必须是声明过的）与 `Pop_up`（源 = 出生，汇 = 死亡 + 越界外迁）。

**分配的舍入规则（保证零误差）**：把一个整数量 `T` 按权重分给 `k` 个接受者时，用**最大余数法**：先给每人 `floor(T·wᵢ/Σw)`，剩余 `r` 单位按小数余数从大到小分给前 `r` 人，余数相同时按 `entity_id` 字典序升序。这是精确的（无 dust）、确定的（无顺序依赖）。**［最大余数法是标准算法；用 entity_id 破平是本文的规定，D 级］**

这条审计是本规格里**最便宜、抓 bug 最多**的东西，而它只有在选了定点整数之后才可能——浮点下这个等式永远不成立，于是必须写成"误差 < ε"，于是它就抓不到真正的 bug。

### 2.6 内存与快照预算

| 项 | 大小 |
|---|---|
| Cell 热字段 | 9×10⁴ × 200 B = **18 MB** |
| Cell 冷字段（跨线共享 mmap） | 9×10⁴ × 400 B = 36 MB |
| Cohort（活跃 2×10⁶ 槽 × 48 B） | **96 MB** |
| Person（3×10⁴ × 96 B） | 3 MB |
| Household（2×10⁵ × 128 B） | 26 MB |
| InfoCopy（5×10⁶ × 72 B） | **360 MB** |
| RelationEdge（3×10⁶ × 48 B） | 144 MB |
| Site（2.2×10⁶ × 40 B，冷） | 88 MB |
| **热态合计** | **≈ 650 MB** |

年增量（假设 8% 热字节变动）：52 MB/yr → 3000 年 = 156 GB/线。**超过 `computational-feasibility` S5 的可接受留存预算（该红队算的是 73 GB/线）**。因此必须采纳该红队的裁决：**不存轨迹，存配方**。只有参考线保留年度聚合 + 具名个体事件 + 关键节点全快照（每 100 年一个 + 每个被提名的重大事件前 1 年一个），其余世界线只留 `(world_seed, kernel_hash, param_hash, basemap_hash, llm_ledger_hash)` 五元组与年度聚合。

**InfoCopy 是最大的单项（360 MB 热态）**，且它会随文明复杂化而增长。硬上限 5×10⁶ 副本，超限时按 `strength` 最低者驱逐，驱逐记入一个计数器；驱逐率 > 5%/yr 即视为表示能力不足，必须改内核版本（而不是悄悄提高上限）。

### 这一节禁止了什么

- 禁止 L0 出现任何浮点、任何字符串、任何名字、任何类别枚举、任何回溯性史学对象（`Dynasty`/`Polity`/`Settlement`/`Religion`/`Class`）。
- 禁止 `Settlement` 与 `Polity` 成为实体——它们只能被检测。这一条同时把 `pseudo-simulation` S5 的"类型删除测试"变成**构建期恒真**：`Polity` 类根本不存在，所以删掉它内核当然照跑。
- 禁止把义务/所有权/身份特权（`rule_tags`）存进 L0。
- 禁止用相对分位（五分位）做队列维度；只能用绝对档。
- 禁止物质与生物类群有名字；它们只有属性向量，id 即哈希。
- 禁止任何 clamp / saturating / wrapping 算术；溢出与负量是硬中止。
- 禁止"守恒审计误差 < ε"式的软审计；必须是 int64 精确相等。
- 禁止在超出实体硬上限时提高上限；只能改内核版本或改表示。
- 禁止历史度量衡单位、per-day 常数散落在多处、以及 365/360 混用。

---

## 3. primitive / composite 词汇表分层与类型抹除测试

### 3.1 两张注册表

**`PRIMITIVE_REGISTRY`（内核可读，封闭，版本化）**

```toml
[[entity_kind]]  id = 1   name = "cell"        # name 仅供人读；内核只用 id
[[entity_kind]]  id = 2   name = "cohort"
...
[[field]]        id = 101 owner = 1  name = "soil_n"   type = "NDens_g_m2"
                 reads_by  = ["work_land", "erode", "leach"]
                 writes_by = ["work_land", "manure", "leach"]
                 evidence  = "A"   source = "agriculture-carrying-capacity §3.5"
[[relation_kind]] id = 3  name = "co_reside"  weight_type = "Q32"
[[prop_form]]     id = 2  name = "WillTransfer"  kernel_reads = ["subject","recipient","substance","amount","due_tick"]
[[rng_stream]]    id = 7  path = "vital/fertility"
[[phase]]         id = 3  name = "resolve_vital_half_a"  order = 3
[[substance_axis]] id = 4 name = "storage_decay" unit = "Rate_q32"
[[free_param]]    id = 12 name = "..." range = [...] evidence = "D"
```

规模约束（`computational-feasibility` S2）：`free_param` 数 ≤ 15，CI 强制；每个非 free 参数必须带 `source` 指向 22 篇简报中的具体位置。

**`COMPOSITE_LEXICON`（观察层专用，可自由增长）**

```toml
[[composite]] id = "c:polity"      detector = "detect_polity_v3"     reads = ["L0 read-only view"]
[[composite]] id = "c:settlement"  detector = "detect_settlement_v2"
[[composite]] id = "c:aristocracy" detector = "detect_aristocracy_v1" # stratification §3.16.4 的六条判据
[[composite]] id = "c:state"       detector = "detect_state_v1"       # state-formation §9.a 的观测器
[[composite]] id = "c:dynasty"     detector = "detect_dynasty_v1"
[[composite]] id = "c:war"         detector = "detect_avalanche_v2"   # complex-systems M7 的时空邻近聚类
```

**分层规则**：
1. 一个标签是 primitive，当且仅当它在 `PRIMITIVE_REGISTRY` 里。内核只能读 primitive。
2. 一个标签是 composite，当且仅当它在 `COMPOSITE_LEXICON` 里。**composite 标签在 L0 里没有任何存储位置**——它只作为观察层的 `(entity_id, tick, detector_version) → label` 侧表存在。
3. `COMPOSITE_LEXICON` 的条目可以随时增删而**不产生内核版本变更**（因为内核看不见它们）。这是这套分层最大的实用收益：我们可以在跑完 3000 年之后再发明"什么叫王朝"，然后回放着去检测它。
4. **`COMPOSITE_LEXICON` 里的每一条都必须能被删除而不影响世界轨迹。** 这是 T-ERASE 的内容。

对照 `abm-methodology` M7 第 1 段（词汇表检查）：M7 说 composite "必须由运行期规则实例化"。本规格更严：**composite 根本不被实例化，它只被检测**。理由是 `emergence-verifiability` F5 指出 M7 的静态词汇表检查"太弱：它抓不住'内核读取一个由观测器写回的宏观字段'"。取消存储位置是唯一结构性的堵法。

### 3.2 世界内的范畴化怎么办

有一个真实的反对意见：世界里的人**确实**会范畴化（"我们是一伙的""他是外人""这是我们的王"），而且这些范畴**确实**会影响行为。如果 L0 完全没有范畴，这条就丢了。

裁决：**世界内的范畴住在 `Proposition` 里，形式是 `SameKindAs(a, b)` 与 `ShouldDefer(a, b, scope)`，内核对这些命题的处理是纯结构性的（它们是否被持有、被谁持有、在哪里、多强）。** 内核**不知道**某组 `SameKindAs` 命题构成了"一个民族"；它只知道有 12 万份互相引用的命题副本在这片区域流通。观察层可以把这团命题聚类并命名为"民族 #7"。

这就是 `pseudo-simulation` S5 要的"国家崩溃有了机械意义：那条信念不再被共享、不再被行动所依据"。

### 3.3 类型抹除测试（T-ERASE）的可执行定义

> **T-ERASE**
>
> **输入**：一次已完成的参考运行 `R = (world_seed, θ, basemap_hash, kernel_hash, proposal_log)`，及其逐 tick 的 L0 状态根哈希序列 `{h_t}`。
>
> **步骤**：
> 1. 收集 `L = COMPOSITE_LEXICON` 中出现过的全部标签，以及观察层侧表中出现过的全部 `label_id`。
> 2. 从专用 RNG 流 `meta/type_erasure`（不参与世界）抽取一个**单射** `σ: L → 全新的 128 位 UUID`，要求 `σ(L) ∩ L = ∅`。
> 3. 用 `σ` 重建观察层的全部侧表、全部检测器输出、全部标签常量。**同时把 `COMPOSITE_LEXICON` 里所有 `name` 字段替换为 `σ` 的像。**
> 4. 用**完全相同**的 `(world_seed, θ, basemap_hash, kernel_hash, proposal_log)` 从 t=0 重跑。
>
> **判据（PASS 需全部成立）**：
> - **(a) 物理逐位相同**：对每个 `t ∈ [0, H]`，`h'_t == h_t`。**一位不同即失败。**
> - **(b) 事件提名流相同**：重大事件提名序列（观察层产出）在 `σ` 下逐项对应相等。
> - **(c) 因果读取集相同**：每个被记录事件的读取集摘要逐位相同。
>
> **失败报告**：第一个发散的 `(tick, phase, entity_kind, entity_id, field_id)`，以及导致该字段被写入的 `rule_id` 与调用栈。
>
> **成本**：一次完整重跑 = 1 × T_run。作为 Tier-2 检查（每次内核版本验收）跑，作为 Tier-0 检查在 300 年玩具世界上跑（秒级）。

**为什么 (a) 必须是逐位而不是统计**：`pseudo-simulation` §8 总表最后一段——"凡是能做成二值结构检验的，就不要做成统计检验"。T-ERASE 是二值的，不能被调参绕过。

**必须配套的阳性对照（否则这个测试没有意义）**：按 `emergence-verifiability` F6 的诱饵世界要求，构建一个 `poison-build`，在内核的某个热路径上插入一行 `if label_of(entity) == "c:polity" { yield *= 1.05 }`。**T-ERASE 必须在这个构建上失败，且失败报告必须精确指向那一行。** 如果 T-ERASE 在 poison-build 上通过，这个测试应当被删掉而不是被辩护。

### 3.4 配套的三个结构性检验

| 检验 | 定义 | 抓什么 | 成本 | 频率 |
|---|---|---|---|---|
| **T-DEPGRAPH** | 内核 crate 的依赖闭包不含观察层 crate、不含 LLM crate、不含任何序列化字符串表 | 内核 → 观察层的反向依赖 | 秒 | 每次提交 |
| **T-ITERORDER** | 把所有哈希容器换成逆序迭代、把所有稳定排序换成不稳定排序 + 重复键随机置换，输出逐位相同 | Sugarscape 类顺序歧义（`abm-methodology` M5 / Kehoe 2016 "Sequential Biases"） | 1× T_run（玩具世界秒级） | 每次提交（玩具）/ 每版本（全量） |
| **T-ISOLATE** | 取地理与网络上完全隔离的两片区域 A、B（A 是无航海能力的孤岛），对 A 做任意干预，B 在 100 年内逐位相同 | id 重编号、迭代顺序、归约顺序、索引重建、LLM 账本错位（`causality-bookkeeping` F7 称它是"整个因果基础设施的地基测试"） | 2× 短跑 | 每次提交 |
| **T-NULLINT** | 把某个值"改成它原本的值"，输出逐位相同 | 一切"重放 ≠ 原跑"的漏洞（`causality-bookkeeping` F7 第 2 条） | 2× 短跑 | 每次提交 |

### 这一节禁止了什么

- 禁止 composite 标签在 L0 有任何存储位置（包括"临时"字段、缓存、索引）。
- 禁止内核以任何方式（直接、通过配置文件、通过字符串比较、通过间接查表、通过观察层回写）读取 composite 标签。
- 禁止把 T-ERASE 写成统计检验或允许"可忽略的差异"。
- 禁止在没有 poison-build 阳性对照的情况下宣称 T-ERASE 通过。
- 禁止往 `PRIMITIVE_REGISTRY` 加条目而不走内核版本变更流程（含世界作废重跑，`mandate-contradictions` F9）。
- 禁止世界内的范畴以枚举形式存在；它们只能是 `SameKindAs` / `ShouldDefer` 命题的副本分布。

---

## 4. 空间表示：裁决与代价

### 4.1 三方冲突

| 来源 | 主张 | 自报证据等级 |
|---|---|---|
| `settlement-urbanization-spatial` §11.1/§11.4 | H3 res 5（252.9 km²/格，边长 9.85 km，中心距 ~17 km），东亚约 4.7 万格；**四层**：L0 六边形环境栅格 + L1 动态加权 Voronoi 地块 + L2 多式联运图 + L3 政治连续场 | 分辨率表 A（H3 官方）；四层方案 §M7 自报 **D** |
| `china-eastasia-geography-archaeology` §3.1/§9.1 | 主格 **5–10 km 六边形**；气候慢时钟 100 年 / 社会快时钟 1–5 年 | §9.1 自报 **D**，"纯工程取舍" |
| `computational-feasibility` S3 | **一张网格**；主格 25 km 六边形（19,200 格）承载**所有动态状态**；1 km 只做一次性静态预计算，聚合时**保留分布摘要**；亚格子过程建成"格内 N 个位点的随机过程"，不参与逐 tick 遍历 | 内存表 A（算术）；主格选择自报 **D** |

三方都自报 D 级。所以裁决只能靠算术 + 语义 + 已声明的不可表示清单。

### 4.2 裁决：单一动态网格 H3 res 5

**取 `settlement` 的分辨率 + `computational-feasibility` 的"一张网格"纪律 + `computational-feasibility` 的亚格子方案；拒绝 `china-geography` 的 5–10 km；拒绝 `settlement` 的 L1 动态 Voronoi。**

#### 拒绝 5–10 km 的算术

H3 res 6 = 36.13 km²/格，边长 3.725 km（`settlement` §4.6，A 级 H3 官方表）。同一窗口下格数是 res 5 的 **7.0 倍**。

`computational-feasibility` §8 的预算：单线 3000 年 ≤ 1 小时 → **1.2 s/tick = 3.6×10⁹ 周期 @3 GHz**，其中气候 5% + 农业 10% = 15% = 0.18 s 用于格扫。res 5 下这是 9×10⁴ 陆格 × ~6,000 周期/格；res 6 下同样的每格工作量需要 1.26 s，**单这两个子系统就吃光整个 tick 预算**。因此 res 6 只有在把每格工作量砍到 850 周期时才可行，而 `agriculture-carrying-capacity` §3.0 的产出函数（水驱动生物量 + 三条折减链 + gamma 抽样 + AR(1) + 三重劳动约束）在定点整数下不可能压到 850 周期。**res 6 被算术排除。**

`china-geography` §9.1 自己写明 5–10 km 是"纯工程取舍"、D 级、无文献支持。所以这里没有需要保护的证据，只有需要保护的**能力**——而它想保护的能力（Spencer 的 25–30 km 半天路程半径，`state-formation` §9.10）在 §4.5 用另一种方式保住了。

#### 拒绝 25 km / 625 km² 的语义理由

`computational-feasibility` S3 的 19,200 格对应 625 km²/格、中心距约 26 km。三条反对：

1. **一天行程的语义锚失效**。ORBIS 实测：牛车 12 km/天、挑夫 20、步行与驮兽 30（`settlement` §11.2，A 级）。res 5 的中心距 17 km 落在这个区间内，于是"相邻"= 一天可达，这让邻接关系有物理含义。26 km 超出了载货运输的一天行程，相邻格之间无法形成日常市场往来，`settlement` §2.3 的基层市场区在这个格上不可表示。
2. **前文明期的政体粒度**。`settlement` §11.5 D 已经指出 253 km²/格会**系统性低估早期政体数量、高估其平均规模**；625 km² 让这个偏差再放大 2.5 倍。而纲领要求"从文明形成之前开始"（`MANDATE.md` 第 5 行），最脆弱的恰是这一段。
3. **预算并不真的紧**。见下。

#### 预算：res 5 在扩大窗口下仍然装得下

窗口（见 §10）取约 65°E–150°E、15°N–58°N。球面盒面积 = `R²·Δλ·(sin φ₂ − sin φ₁)` = `4.06×10⁷ km² × 1.4835 × 0.5892` = **3.55×10⁷ km²**（含海）。除以 H3 res 5 均面积 252.9 km² → **约 1.40×10⁵ 格**；按陆比 0.6（**D 级，必须在构建时实测**）→ **约 8.4×10⁴ 陆格**。

预算分配（本规格对 `computational-feasibility` §8 表的修订）：

| 项 | 格数 | 周期/格/tick | 合计周期 | 占 3.6×10⁹ |
|---|---|---|---|---|
| 气候高频 AR + 生态滞后 | 1.40×10⁵（含海） | 2,000 | 2.8×10⁸ | 7.8% |
| 农业/水文/土壤/植被/土地利用 | 8.4×10⁴（陆） | 8,500 | 7.1×10⁸ | 19.8% |
| **格扫合计** | | | **9.9×10⁸** | **27.6%** |

**硬预算：格扫工作 ≤ 350 ms/tick（29%），即所有格扫子系统合计 ≤ 1.05×10⁹ 周期/tick。** CI 用 `computational-feasibility` §7 第 1 条的空壳内核基准实测，超支即构建失败。

这比该红队原表的 15% 高了 14.6 个百分点。**从哪里买回来**（`computational-feasibility` F1 替代设计第 3 条要求"超支必须从别人那里买"）：
- 气候低频分量（轨道基线 + 千年事件）改为 **O(1) 无状态纯函数**，不参与格扫（§9.2），比该红队按整层格扫估的 5% 省下约 3%。
- 取消独立的"聚落"实体与 L1 动态 Voronoi，省下每 tick 的 Voronoi 重划（该红队表里没有这一行，但 `settlement` M7 要求它，两者不兼容）。
- 剩余约 11% 从"贸易 12%"与"制度/文化/宗教 5%"中扣，理由是本规格取消了 `Polity`/`Religion` 实体，这两行的实体计数下降。

**这次调整必须由性能预算表的 owner 签字**，且在空壳内核基准出数之前，本节的所有周期数都是 **D 级估算**。

#### 一张网格的纪律（照抄 `computational-feasibility` S3）

- **所有逐 tick 变化的场量只住在 H3 res 5 这一张网格上。** 禁止任何第二张动态栅格，禁止任何逐 tick 执行的重采样/降尺度算子（该红队的核心论点：插值是"每 tick 都在执行的、有系统性偏置的算子"，从粗到细尤其会造出不存在的空间结构）。
- **1 km 只用于一次性静态预计算**，其输出**量化为定点整数并内容哈希**后冻结为数据资产，进 `basemap_hash`。
- 聚合到 res 5 时**保留分布摘要**（`{min,p10,p25,p50,p75,p90,max}` + 最大连通可耕斑块面积），不是只留均值（`computational-feasibility` S3 第 2 条：下游关心的是尾部）。`settlement` §11.5 J 给出同样的要求。

### 4.3 拒绝 L1 动态 Voronoi 的理由与代价

`settlement` M7 的 L1 是"由聚落生成的加权 Voronoi / XTENT 势场多边形，随聚落密度自适应，10 年重划"。拒绝它的三条理由：

1. 它是**第二张动态空间划分**。虽然不是栅格，但它需要逐期重算，并且会与 res 5 网格产生同一个量的两个值（"这块地属于哪个格"vs"属于哪个地块"），这正是 `computational-feasibility` S3 的可观察症状第一条。
2. 它需要 `Settlement` 作为一等实体，而 §2.3.5 已经因为标度律硬编码风险取消了这个实体。
3. `settlement` §11.5 D 用 L1 来解决"小于一格的政体"问题；但本规格用另一条路解决：**政体不存在于 L0，所以它不需要空间容器**。政体归属只在观察层由四个独立检测器测量（贡赋流向、军事响应半径、效忠信念多数派、婚姻网络社群），而 `pseudo-simulation` S5 判别测试 2 要求这四者**必须不一致**（Fleiss' κ 接近 1 是坏消息）。一个不存在于内核的东西不可能有清晰边界——这把"边界必须模糊"从一个需要努力达到的目标变成了**构造上的必然**。

**代价（必须签字）**：
- 腹地/领地作为一个**面**在 L0 不可用。任何需要"这块地属于谁"的机制（田赋、征兵配额、封地）只能写成"从某位点出发、沿图上的边、在给定成本半径内可达的家户集合"。这是一个**图上的可达集**，不是一个多边形。
- `settlement` M5（城市粮食腹地半径与运输的自噬极限）必须改写成图上的可达集版本。
- 我们**永久放弃**在 L0 表示"渐变的、重叠的、有飞地的前现代政治空间"的**几何**；我们只表示产生它的**流**。

### 4.4 亚格子过程如何表示

三种、且只有三种：

**(1) 冻结位点集（Site）。** 每格在世界创生时生成 ≤16 个候选位点，坐标为格内 (u16,u16) 相对坐标，属性来自 1 km 预计算的分位向量。位点集是 `basemap_hash` 的一部分。位点**不参与逐 tick 遍历**；只在家户创建/迁移/放弃事件时被采样。聚落间 1.5–3 km 抑制距离（`settlement` §3.32 的克里特青铜时代 PCF 实证）实现为**位点生成时的硬核点过程**（hard-core process），一次性完成，不是每 tick 的斥力。

**(2) 图上的边属性。** 关隘、渡口、桥、港口、长城、运河、驿道——全部是 L2 图上的边或"切割边集"，不是格（`settlement` §11.5 B/E/H）。于是"扼守潼关"= 控制某条边；"长城被从某点突破"= 某条切割边失效。**这也是 Spencer 半天路程判据的保命通道**：25–30 km 半径在 res 5 下只有约 1.5–2 格，但在图上它是一条**等时线**，由 1 km 成本面积分出来，精度与格无关（`state-formation` M4）。

**(3) 格内分布摘要的函数。** 承载力、适宜度、洪水淹没比例这类量，必须用格内**分布**而不是均值计算（`settlement` §11.5 J）。例：可耕面积不是 `land_area × arable_frac`，而是对坡度/TWI 分位向量做积分。

### 4.5 因此永久落在分辨率之下的现象（必须写进 README，不得事后惊讶）

照抄并扩充 `settlement` §11.5 的 A–J，补上本规格特有的 K–N：

| # | 不可表示的现象 | 后果 | 缓解（明确标注这是补丁不是涌现） |
|---|---|---|---|
| A | 城市内部空间（坊市、城墙内外、族群聚居、贫富隔离、城内瘟疫传播） | 无法模拟"城市内部空间不平等导致的政治事件" | 位点上的**非空间**属性（隔离指数、密度惩罚），承认它们没有几何 |
| B | 战术地形（500 m 隘口、浅滩、桥） | 不能模拟具体战役的地形优势 | 图上的 `chokepoint` 边属性 |
| C | 田块级农业（轮作空间形态、细碎化、渠系拓扑、水权空间结构） | 不能模拟井田/均田的空间形态差异 | 只模拟其统计后果（产出、不平等、税基） |
| D | 小于一格的政体几何 | 系统性低估早期政体数、高估平均规模 | 政体不存在于 L0（§4.3），归属由图上的流测量 |
| E | 线状地物的几何 | 长城/运河/驿道不是面 | 图上的边集 / 切割边集 |
| F | 低密度分散型都市主义（Hutson et al. 2023 的玛雅形态） | 这一大类文明形态不会自发出现 | **真实的表达能力缺失，不打补丁** |
| G | 转场放牧路线、季节营地、随季节迁移的市集的空间结构 | 游牧社会被表示得过于定居化 | 游牧家户用"活动域 = 一组格 + 一个季节相位"的特殊表示 |
| H | 岛屿、狭窄海峡、良港/不良港的微观地理 | 不能表示"某天然良港决定贸易格局" | 港口是图上的显式节点，"港况"是节点属性 |
| I | 短于 1 年的事件（围城、突袭、市集骚乱） | 不能追踪"某月某日发生了什么" | 事件局部的有界子时钟（§5.4），结果写回主循环 |
| J | 格内空间自相关的真实结构 | 承载力被系统性平均化，关中/四川式的地形优势被削弱 | 每格存**分布摘要**而不是均值 |
| **K** | **任何政治边界的几何** | 地图上画不出国界线 | 只有四个检测器给出的、互相不一致的归属场；这是**特性不是缺陷**（`pseudo-simulation` S5） |
| **L** | **格内地块的空间形态**（LandParcel 只有面积没有形状） | 地块兼并的空间格局不可表示 | 只有面积与持有者 |
| **M** | **格内位点集的动态演化**（位点集创生冻结） | "在山谷里新建一座城"只能落在 16 个预生成位点之一 | 提高 N_site 是内核版本变更；N_site=16 是 **D 级**，必须在 Phase 1 用位点占用饱和率标定 |
| **N** | **特征时间 < 1 日的一切**（`Day_d` 是最细的时间单位） | — | — |

**README 一句话**（改写自 `settlement` §11.6）：

> 本世界的动态状态全部住在一张 252.9 km² 的等积六边形网格上，加上冻结的格内位点集与一张多式联运图。这让我们能在可反复重跑的成本内模拟数千年的人口—聚落—政治演化；代价是我们**永久放弃**了城市内部空间、战术地形、田块几何、低密度都市形态、游动性聚落的真实几何，以及**一切政治边界的几何**。凡是需要这些几何的历史现象，我们要么用非空间的聚合属性近似并明确标注，要么诚实地承认这个世界里不会出现它。

### 这一节禁止了什么

- 禁止第二张动态栅格；禁止任何逐 tick 的空间重采样/降尺度算子。
- 禁止逐 tick 重算的动态空间划分（Voronoi/XTENT/Thiessen）进入内核；它们只能在观察层按需重算。
- 禁止把 1 km 数据带进运行期；1 km 只进一次性静态预计算，输出量化冻结。
- 禁止聚合时只保留均值。
- 禁止位点参与逐 tick 遍历。
- 禁止把关隘/长城/运河/港口做成格属性。
- 禁止 L0 存储任何政治边界几何。
- 禁止在格扫预算超支时提高 T_run；只能砍每格工作量或改内核版本。
- 禁止把 §4.5 A–N 中的任何一项作为"涌现结论"引用。

---

## 5. 时间

### 5.1 主时钟

**主时钟 = 1 世界年（360 世界日），`tick: i64`，唯一合法。** 三条独立依据交汇：

1. **人口模块的硬约束**：`population-dynamics` §2.2 的 MTI（Malthusian Transition Interval）为 **40–65 年**（较低背景死亡率下从 65 缩到 48）。这是整个世界最重要的一次相变，只有 40–65 个 tick 的宽度。tick = 1 年时它有 40–65 个采样点，勉强够；tick = 5 年时只有 8–13 个点，形状会被抹掉。**tick ≤ 1 年是人口模块的硬下界。**
2. **算力的硬上界**：`computational-feasibility` F4 —— 月 tick 是 36,000 步、日 tick 是 1,095,000 步；日 tick 在做任何物理之前，光是每 tick 固定开销（20 个子系统的相位屏障、调度、日志、快照记账，乐观估计 5–50 ms）就要 1.5–15 小时，是 1 小时预算的 1.5–15 倍。**全局细于年的 tick 被算术排除。**
3. **LLM 的结构约束**：`computational-feasibility` F5 要求 LLM 永不在 tick 关键路径上，`decide` 读上一 tick 的视图、`resolve` 在下一 tick 消费。年 tick 下这个 1 tick 滞后是一个合理的"决策到动员"延迟；月 tick 下它不合理。

### 5.2 合法 tick 率集合（整除链）

**规则**：一切子系统的更新周期必须与主时钟成整除关系，且合法值来自两条**整除链**：

```
年内细分  S ∈ { 1, 2, 3, 4, 6, 12 }          # 每年的子步数，必须整除 360 日
慢周期    P ∈ { 1, 5, 25, 100 } 年            # 必须构成整除链：1 | 5 | 25 | 100
```

**禁止**任何不在这两条链上的速率（`computational-feasibility` F4 第 4 条 / S6 第 2 条：不整除的速率产生**拍频**，宏观周期会变成 tick 表的产物——"这对一个要研究长周期的项目是致命的伪影"）。

特别地：`china-eastasia-geography-archaeology` §9.1 建议的"社会快时钟 1–5 年"合法（1 与 5 都在链上）；`complex-systems-emergence` M1 建议的 "L2 区域 5 年 / L3 制度 25 年 / L4 扩散 5 年" 全部合法；**但 `mandate-contradictions` 决定 1 的"气候 100 年一步并可插值到 10 年"里的 10 不合法**（10 ∤ 25，10 ∤ 5 的链外）——改为**插值到 5 年**或**插值到 25 年**。

**子时钟配额表**（`computational-feasibility` F4 第 3 条要求的东西）：

| 子系统 | 允许的子时钟 | 最大步数/实例 | 最大空间范围 | 并发实例上限 | 超限行为 |
|---|---|---|---|---|---|
| 主循环（全部 L0 场量与人口） | 年（S=1） | — | 全域 | 1 | — |
| 价格/交换清算 | 年内 S=4（季） | 4 | 全域 | 1 | — |
| 战役 | 事件局部，日步 | **≤ 180 日** | ≤ 40 格的连通子图 | **≤ 8** | 第 9 场按年尺度粗解算 |
| 疫病爆发 | 事件局部，S=12（月）等价的 30 日步 | ≤ 360 日 | ≤ 50 个活跃斑块 | ≤ 50 | 超限斑块按年尺度 SIR |
| 洪水/溃决 | 事件局部，日步 | ≤ 30 日 | ≤ 200 格（沿河） | ≤ 4 | 粗解算 |
| 气候低频 | **无时钟**（O(1) 纯函数） | — | — | — | — |
| 气候高频 AR | 年（S=1） | — | 全域 | 1 | — |
| 地貌（侵蚀/淤积/海岸） | P=25 | — | 全域 | 1 | — |
| 基底重大改写（改道、海侵） | 事件驱动 | — | 流域 | ≤ 1/世纪 | — |

配额来自 `computational-feasibility` F4 的算术："5 场并发战争 × 180 天 × 10⁴ ops = 9×10⁶ ops/年，3000 年共 2.7×10¹⁰ ops——可忽略"，对比全球日 tick 的 1.05×10¹² ops。**没有配额的子时钟会在第一次"我们让贸易也走月步吧"时悄悄吃掉全部预算，而且这个决定看起来完全合理。**

**所有概率以年危险率存储，禁止存 per-tick 常数**（`mandate-contradictions` 决定 1）。子时钟内的转换用 `1 − (1 − h_year)^(Δt/360)` 的定点实现，且该转换函数只能出现在一个地方。

### 5.3 tick 内相位顺序（`PHASE_ORDER_V1`）

`abm-methodology` M5 与 AP4 指出：Kehoe (2016) 用 Z 规范形式化 Sugarscape 时发现的三大不可复现原因之一是"**书里没有说规则以什么顺序应用**"，出版 20 年后仍无法无歧义重实现。因此相位顺序是 spec 的一等公民、显式版本化、改它要走和改模型一样的评审流程（`computational-feasibility` S6 第 5 条）。

```
PHASE_ORDER_V1  (每 tick 严格按 order 执行；跨相位不允许读写穿越)

order  phase                 reads                        writes                    备注
  0    epoch                 tick 计数器                   tick                      推进主时钟；计算低频气候纯函数
  1    env_slow              Cell 冷字段, tick             Cell.clim_ar, soilmoist   高频气候 AR、生态滞后
  2    sense                 L0 全量（只读快照）            Perception 缓冲区          构造每个 Actor 的受限视图
  3    propose               Perception 缓冲区（仅）        Intent 队列（仅）          规则策略 + LLM（读上一 tick 视图）
  4    vital_half_a          L0 vital 块                   L0 vital 块               Strang 前半步（见 5.4）
  5    material              L0 material 块 + Intent 队列   L0 material 块            整步：生产、搬运、交换、建造、破坏
  6    vital_half_b          L0 vital 块                   L0 vital 块               Strang 后半步
  7    info                  L0 全量                       InfoCopy                  信息复制、失真、遗忘、载体腐损
  8    commit                写集缓冲                       L0                        应用写集；**守恒审计**；溢出检查
  9    record                L0（只读）                     日志/快照（内核外）         读取集摘要、事件提名、快照根哈希
```

**规范约束**：
- `propose` 相位**只能**读 `sense` 产出的 Perception，**只能**写 Intent 队列。CI 静态检查：propose 模块不得 import 世界状态模块（`pseudo-simulation` S9 判别测试 2）。
- 同一相位内多实体的处理顺序**不允许依赖容器迭代顺序**。要么 (a) 顺序无关（读旧写新，纯函数式），要么 (b) 按显式确定性键排序（§6.6）。
- `commit` 之前不允许任何子系统看到其他子系统本 tick 的写入（读旧写新）。**例外**：Strang 分裂内部的三步之间必须看到彼此，这是分裂算法的定义。
- 相位顺序变更 = 新版本号 `PHASE_ORDER_V2`，且**世界作废重跑**（`mandate-contradictions` F9）。

### 5.4 算子分裂：Strang 对称分裂

`computational-feasibility` S6 给出的问题：多速率耦合等价于 Lie–Trotter 分裂，误差正比于对易子 `[A,B]`；**耦合最强的时刻正是饥荒 + 疫病 + 战争同时发生的崩溃期——数值误差在我们最需要精度的地方达到最大**。（该红队注明算子分裂误差的阶数是 **[教科书知识，未核实]**，不得作为 A 级证据引用。）

**分块**：
- **A = vital 块**（相位 4/6）：食物比 `E` 的计算、出生、死亡、疫病死亡率。这三者必须**联立求解，不得跨速率分裂**（`computational-feasibility` S6 第 3 条明确点名"人口 ↔ 食物比 E ↔ 疫病死亡必须在同一速率上联立求解"）。
- **B = material 块**（相位 5）：生产、存量、搬运、交换、建造、破坏、土地利用。

**格式**：`A(h/2) → B(h) → A(h/2)`（Strang），而不是 `A(h) → B(h)`（Lie–Trotter）。代价：vital 块每 tick 多算一次半步，约 +30% 该子系统成本（`computational-feasibility` S6 第 4 条已把这笔钱算进预算表）。

**A 块内部的半步在定点整数下的定义**：所有年危险率折半为 `h_half = 1 − sqrt(1 − h_year)`（定点实现，见 §6.4），而不是 `h_year / 2`。这条必须写清楚，否则两个半步合起来不等于一整步。

### 5.5 步长减半不变性测试（必须在崩溃期窗口上做）

`computational-feasibility` S6 的可观察症状：**把快子系统的步长减半，同种子重跑，宏观轨迹在 Monte Carlo 噪声之外发生偏移 ⇒ 历史是 tick 表的函数，不是机制的函数。注意：这个测试必须在崩溃期窗口上做，在平稳期做会通过。**

**崩溃期窗口的可执行定义**（**［本文原创，无来源，D 级；阈值全部待标定］**）：

> 一个区间 `[t₀, t₁]` 是崩溃期窗口，当且仅当至少满足其一：
> - **人口判据**：世界总 `Pop_up` 在 ≤ 25 年内下降 ≥ 15%；
> - **饥饿判据**：持有全世界 ≥ 20% 人口的格集合，其人口加权 `E` 连续 ≥ 5 年 < 1.0（`population-dynamics` §2.2 的 `E<1` 即"第一次感到饥饿"）；
> - **暴力判据**：暴力致死 `Pop_up` 的 25 年滑动和，超过其此前 500 年分布的 P99。
>
> 阈值 15% / 25 年 / 20% / 5 年 / P99 全部是 **D 级**，必须在 Phase 1 用玩具世界标定；标定前先用这组数跑，不得因为"没标定"而跳过测试。

**测试协议（配对设计 + 收敛阶检验）**：

```
输入: R = 20 个种子（同一 kernel/param/basemap）
1. 在基准子步 S₀ 下跑完整长跑，取每个种子最深的 3 个崩溃期窗口。
2. 对每个种子 i、每个窗口 w：
     从 t₀−10 分叉，分别以 S₀、2S₀、4S₀ 跑到 t₁+50。
     计算声明的 K 个宏观摘要统计量（见下）。
3. 配对差：Δ¹ᵢ = stat(2S₀) − stat(S₀)；Δ²ᵢ = stat(4S₀) − stat(2S₀)。
4. 判据 (I) 幅度: |mean_i(Δ¹)| / SD_between_seeds(stat at S₀) ≤ 0.20
5. 判据 (II) 收敛阶: ‖mean(Δ²)‖ / ‖mean(Δ¹)‖ ∈ [2.5, 6.0]
      （Strang 是二阶 ⇒ 理论比值 4；带宽是 D 级）
6. 判据 (III) 无系统偏向: sign(Δ¹) 在 K 个统计量上不得同号超过 K−1 个
      （同号 = 分裂误差在做单向的物理，而不是随机数值噪声）
```

**声明的 K 个宏观摘要统计量（预注册，跑之前写死）**：窗口内人口最低点、人口下降幅度、崩溃持续年数、崩溃后 50 年的恢复比例、窗口内暴力致死总数、窗口内迁移人-格总量、窗口结束时的 `E` 中位数、活跃家户数变化率。K = 8。

**判据 (II) 是本节最有价值的一条**：它不只问"结果变没变"，它问"结果随步长变化的方式是否符合我们声称的数值格式的阶"。一个通不过 (II) 但通过 (I) 的实现，说明分裂不是它自称的那个分裂。**［判据 (II) 与 (III) 为本文原创，无来源，D 级；Richardson 外推的阶检验思想是标准数值分析，本次未核实一手来源］**

### 5.6 与 `mandate-contradictions` 决定 1 的差异

| 项 | 该红队建议 | 本规格 | 差异理由 |
|---|---|---|---|
| 主 tick | 1 年 | 1 年 | 一致 |
| 气候层 | 100 年一步、插值到 10 年 | 低频 O(1) 纯函数；高频年步；地貌 25 年 | 10 不在整除链上（拍频）；且低频可以完全无步 |
| 空间战争 | 1–2 年 | 事件局部日步 ≤180 日、并发 ≤8 | 2 年不在整除链的年内侧；`computational-feasibility` F4 的算术表明事件局部日步更便宜也更真 |
| 概率存储 | 年危险率 | 年危险率 | 一致 |
| 时间步收敛测试 | "tick 减半后年度聚合量变化 < X%" | 崩溃期窗口 + 配对设计 + 收敛阶检验 | 平稳期测试会通过（`computational-feasibility` S6 明确警告） |

### 这一节禁止了什么

- 禁止全局月 tick 与日 tick，**永远**（`computational-feasibility` §8"必须放弃的清单"第 1 条）。
- 禁止任何不在 `S ∈ {1,2,3,4,6,12}` / `P ∈ {1,5,25,100}` 两条整除链上的更新周期。
- 禁止无配额的子时钟；禁止子时钟超出 §5.2 表中的步数/范围/并发上限而不降级。
- 禁止 per-tick 概率常数；一切概率以年危险率存储。
- 禁止跨相位读写穿越；禁止 `propose` 相位 import 世界状态模块。
- 禁止依赖容器迭代顺序的同相位处理次序。
- 禁止把强耦合三元组（人口 ↔ E ↔ 疫病死亡）拆到不同速率上。
- 禁止用 Lie–Trotter（简单交替）代替 Strang。
- 禁止在平稳期做步长减半不变性测试并据此声称通过。
- 禁止在没有 §5.5 判据 (II)（收敛阶）的情况下声称分裂误差可控。
- 禁止未经 `PHASE_ORDER_V*` 版本升级 + 世界作废重跑而改动相位顺序。

---

## 6. 确定性契约

### 6.1 三选一裁决：定点整数（选项 a）

`computational-feasibility` F2 给出三个选项与本机实测：同一组 100,000 个随机数，顺序求和 / numpy 成对求和 / 分块求和的结果相对差约 **1.2×10⁻¹⁶（约 1 ULP）**；用 logistic map (r=3.9) 代表正 Lyapunov 指数动力学，初始相对差 2.78×10⁻¹⁶ 在 **60 步后放大到 7.9×10⁻²（O(1)）**，80 步完全发散。**我们要跑 3,000 步。**

三个选项：

| | (a) 定点整数 | (b) 确定性树归约 + 编译器约束 | (c) 放弃 bit-exact |
|---|---|---|---|
| 确定性来源 | **结构性**（整数加法严格结合） | 纪律（固定分块、禁 FMA 重结合、锁 BLAS 版本） | 无 |
| 依赖升级的风险 | 无 | **任何一次依赖升级都可能静默破坏** | — |
| 反事实实验 | 干净 | 干净（若纪律不破） | **废掉** |
| 平行世界 | 可行 | 可行 | **废掉** |
| 线内并行求和 | **安全**（结合律成立） | 需要固定树形 | — |
| 守恒审计 | **可以写成精确相等** | 只能写成 `< ε` | 只能写成 `< ε` |
| 代价 | 需设计标度；除法要小心；超越函数要自己实现 | 持续的纪律成本 | 纲领两个卖点作废 |

**裁决：(a) 定点整数。** 决定性理由有两条，第二条 `computational-feasibility` 没有提到：

1. (c) 直接废掉纲领第 6 条与"平行世界/反事实"两个终目标，不可接受；(b) 靠纪律维持，而这是一个长期研究型项目（`MANDATE.md` 第 26 行），纪律必然会在某次依赖升级中破掉，而且**破掉的方式是静默的**。
2. **(a) 让 §2.5 的守恒审计能写成 int64 精确相等，而 (b)/(c) 只能写成 `误差 < ε`。** 一个 `< ε` 的审计抓不到真正的 bug（真 bug 通常先表现为很小的不平衡），而一个精确相等的审计能抓到几乎一切物质流实现错误。**这是本项目最便宜、覆盖面最广的正确性防线，而它只在选项 (a) 下存在。** **［这条论证为本文原创，无来源，D 级］**

### 6.2 定点表示规范

- **表示**：见 §2.1 的单位表。每个字段在 `PRIMITIVE_REGISTRY` 里声明 `type`（决定标度）与 `width`（i32 / i64）。
- **宽度规则**：i32 只允许在"声明的取值域在两倍余量下可证明装得下"的字段上使用；**一切累加器、一切守恒量总和、一切 Q32 都是 i64**。
- **溢出**：一律 `checked_*`。溢出是**硬中止**，不是 wrap、不是 saturate。lint 禁止 `wrapping_*` / `saturating_*`。
- **乘法**：`Q32 × Q32 → Q32` 用 i128 中间量右移 32 位，舍入用**四舍六入五成双（round-half-to-even）**。理由：确定、跨平台唯一、零均值偏置（`abm-methodology` AP5 的教训是舍入/裁剪偷改均值）。
- **除法**：`div_floor` / `div_round_half_even` 两个显式函数，禁止裸 `/`。除数可能为 0 的地方必须有声明的守卫，守卫触发要记账。
- **守恒量的分配**：最大余数法 + `entity_id` 破平（§2.5），保证零 dust。
- **超越函数**：`exp_q32`、`ln_q32`、`pow_q32`、`sqrt_q64`、`log1p_q32` 全部由本项目实现为**查表 + 定点多项式插值**，表内容与算法进 `kernel_hash`，跨平台按构造逐位一致。**禁止调用 libm。** 精度要求：相对误差 ≤ 2⁻³⁰，且必须**单调**（非单调的近似会让阈值比较产生非物理的翻转）。

**浮点的唯一两处合法用途**：
1. **观察层 / 分析层 / 可视化**。它们对内核零可见性（单向依赖，CI 强制）。
2. **一次性静态预计算**（1 km 地形/水文/成本面）。其输出必须量化为定点、内容哈希、冻结为数据资产，并进 `basemap_hash`。预计算代码与内核在不同 crate、不同进程、不同目录。

lint：内核 crate 内出现 `f32`/`f64` 即构建失败。

### 6.3 线内并行的规则（定点的回报）

`computational-feasibility` T3 建议"放弃单条世界线的多线程加速，改为多进程跑不同种子"。本规格**部分保留线内并行**，因为整数加法满足结合律：

- **允许**：(i) 对格的纯 map（无跨格写）；(ii) 整数归约（求和、最大、计数）——分块方式与线程数**不影响结果**，因为整数加法严格结合。
- **禁止**：任何有跨实体写、有顺序依赖、或涉及 Q32 乘法链归约（乘法舍入不结合）的并行。这些一律单线程。
- **CI**：线程数不变性测试（1 / 4 / 16 线程逐位相同）从第一次提交起在 CI 里跑（`computational-feasibility` §7 第 3 条）。

集合层并行（多进程跑不同种子）仍然是主要并行度来源。

### 6.4 CBRNG 与流分配表

**算法**：Threefry4x64-20（Random123 家族，Salmon et al. 2011；通过 TestU01 SmallCrush/Crush/BigCrush，`abm-methodology` §2.20 A 级）。每次调用产出 256 随机位。

**寻址布局**（本文对 `abm-methodology` M4 / `provenance-replay-counterfactual` M2 的具体化；该布局本身是 **D 级**）：

```
key[0] = world_seed_lo64
key[1] = world_seed_hi64
key[2] = H64(stream_path)          # 固定的、与运行时无关的哈希（禁止语言内置 hash()）
key[3] = branch_salt               # 分叉时只改这一个；主线为 0

ctr[0] = tick                      u64
ctr[1] = entity_id_lo64            u64   # 内容/血缘派生 H128 的低 64 位
ctr[2] = entity_id_hi64            u64   # 高 64 位
ctr[3] = (slot_id:u32 << 32) | draw_index:u32
```

**为什么用 4×64 而不是 4×32**：4×32 装不下完整的 128 位 entity_id，只能截断，而截断会引入碰撞，碰撞会让两个实体共用随机流——这是一个会在几百年后才显形的静默 bug。用 256 位 counter 就没有这个问题。代价：Threefry4x64-20 比 Philox4x32-10 略贵，但它一次产出 256 位（4 个 draw 的量），摊薄后可接受。

**流分配表**（`stream_path` 封闭注册表；加一条 = 内核版本变更）：

| id | stream_path | 消费者 | 反事实用途 |
|---|---|---|---|
| 1 | `worldgen/basemap_perturb` | 创生扰动算子 | 换基底实例 |
| 2 | `worldgen/registry` | Substance/Taxon/Recipe 初始注册表生成 | 换生物—物质世界 |
| 3 | `worldgen/sites` | 格内位点硬核点过程 | 换微地理 |
| 4 | `worldgen/seeding` | t=0 人群播撒 | 换初始分布 |
| 5 | `worldgen/params` | θ 从先验抽样 | 换参数实现 |
| 6 | `climate/lowfreq` | 千年事件到达时刻与幅度（创生时冻结成事件表） | **"如果那次大旱没发生"** |
| 7 | `climate/highfreq` | 年际 AR 创新项 | 换气候实现 |
| 8 | `hydro/flood` | 溃决/改道 | "如果黄河没改道" |
| 9 | `eco/yield` | 单产 gamma 抽样（`agriculture-carrying-capacity` §3.4） | 换歉收年 |
| 10 | `vital/fertility` | 生育 | — |
| 11 | `vital/mortality` | 死亡（Siler + 冲击） | "如果那个人没死" |
| 12 | `vital/pairing` | 生殖配对 | — |
| 13 | `disease/emergence` | 病原出现 | "如果那场瘟疫没来" |
| 14 | `disease/transmission` | 传播 | — |
| 15 | `move/migration` | 迁移目的地选择 | — |
| 16 | `violence/resolution` | 暴力结算 | "如果那一仗打输了" |
| 17 | `info/transmission` | 信息复制与失真 | "如果消息没传到" |
| 18 | `info/recall` | 记忆衰减与回忆 | — |
| 19 | `innov/variation` | Recipe 变异 | "如果那项技术没被发明" |
| 20 | `agent/policy` | 规则型策略的抽样 | — |
| 21 | `agent/llm_sampling` | LLM 采样种子 | — |
| 22 | `lod/promotion` | 个体提升的随机对照组（`mandate-contradictions` F4 第 4 条的 1% 随机提升） | — |
| 23 | `order/<phase>` | 同相位处理顺序的确定性置换 | — |
| 24 | `meta/type_erasure` | T-ERASE 的 σ（**不参与世界**） | — |
| 25 | `meta/placebo` | 空干预安慰剂对照（`causality-bookkeeping` F5） | — |

**流隔离的意义**：改动某个模块的抽样次数不影响其他模块；"只把疾病流换一个种子"是一个合法的、干净的反事实操作（`abm-methodology` M4）。

**`slot_id` 注册表**：每个决策点在 `PRIMITIVE_REGISTRY` 里有一个稳定的 u32 `slot_id`。`slot_id` **不得**由代码位置、行号、或函数名的运行时哈希派生（这些会随重构改变）；必须是人工分配的常量。

### 6.5 实体 id：内容/血缘派生哈希（D8）

`causality-bookkeeping` F7 是本规格最重视的一条红队发现：

> 如果新实体的 id 由全局自增计数器分配，那么"抑制远洋某小岛上的一次生育"→ 全局计数器少加 1 → 此后每一个新生者拿到不同 id → 每个人的 counter 全变 → 三年之内整个大陆的一切都不同。**我们会把它写进论文，说这就是路径依赖。** 而这个 bug 与真实的路径依赖在任何宏观观测量上都不可区分。

**规范**：

- 哈希函数：**BLAKE3，取前 128 位**（固定、版本化、语言无关；`H128`）。禁止语言内置 `hash()`（`provenance-replay-counterfactual` M2 明确点名）。
- 生成公式（全部进 `PRIMITIVE_REGISTRY`）：

```
person_id      = H128("v1/person"  ‖ mother_id ‖ father_id_or_zero ‖ birth_tick ‖ birth_slot_within_mother)
founder_id     = H128("v1/founder" ‖ world_seed ‖ cell_id ‖ founder_index)      # 仅 t=0
household_id   = H128("v1/hh"      ‖ sorted(founder_person_ids) ‖ founding_tick)
cell_id        = H128("v1/cell"    ‖ basemap_hash ‖ h3_index)
site_id        = H128("v1/site"    ‖ cell_id ‖ site_index)                       # 创生冻结
structure_id   = H128("v1/struct"  ‖ site_id ‖ built_tick ‖ builder_id ‖ seq_within_site_tick)
parcel_id      = H128("v1/parcel"  ‖ cell_id ‖ holder_id ‖ created_tick ‖ seq)
edge_id        = H128("v1/edge"    ‖ kind_id ‖ src_id ‖ dst_id ‖ created_tick)
info_id        = H128("v1/info"    ‖ prop_id ‖ holder_id ‖ acq_tick ‖ acq_slot)
prop_id        = H128("v1/prop"    ‖ form_id ‖ canonical_encoding(args))
substance_id   = H128("v1/sub"     ‖ canonical_encoding(property_vector))
taxon_id       = H128("v1/taxon"   ‖ canonical_encoding(property_vector))
recipe_id      = H128("v1/recipe"  ‖ canonical_encoding(coefficient_vector))
```

- 公式里出现的每一个 `seq` / `index` 都必须是**局部的、可从局部状态重算的**（"这位母亲的第几胎"、"这个位点当年的第几座建筑"），**绝不是全局的**。
- **碰撞处理**：插入时检查 id 是否已存在。碰撞 = **硬中止**，不是重命名。128 位下 10¹⁰ 个实体的碰撞概率约 10⁻¹⁸，若真发生，它是确定性的、可复现的，值得停下来看。
- **lint**：内核中任何 `+= 1` 用于 id 分配的模式即构建失败；任何 id 类型上的 `<` 比较，只允许出现在声明的 `canonical_order()` 工具函数内。

### 6.6 确定性 tiebreaker

任何需要顺序的地方：

```
canonical_order(entities, phase_id, tick):
    key(e) = ( domain_key(e),                                 # 领域主键（如距离、优先级），Q32/整数
               threefry(stream="order/"+phase_id,
                        ctr=(tick, e.id_lo, e.id_hi, 0))[0],  # 确定性随机置换
               e.id )                                          # 字典序，最终破平
    return stable_sort_by(entities, key)
```

- `domain_key` 必须是 R2 白名单里的整数量。
- 第二项让"同优先级者的处理顺序"成为一次**可复现的随机置换**，而不是插入顺序（`abm-methodology` M5 的 (b) 选项）。
- 第三项保证完全确定。
- **T-ITERORDER**（§3.4）检验这条规则被遵守。

### 6.7 Gumbel-max 而不是逆变换采样（D10）

`provenance-replay-counterfactual` §2.7 转述 Oberst & Sontag (ICML 2019, PMLR 97:4881–4890) 的结果（该简报标注本次取得全文 PDF）：

> 对同一个 4 类分布 `p = (0.25, 0.25, 0.3, 0.2)`，用"把 [0,1] 按某个顺序 `ord` 切成区间、抽 `U~Unif(0,1)` 落哪取哪"的机制采样，**不同的排列 `ord` 给出完全相同的观测分布和干预分布，却给出不同的反事实**。原文："Since all choices for `ord` imply the same interventional distribution, there is no way to distinguish between these mechanisms with data."
> **定理 2：Gumbel-Max SCM 满足反事实稳定性。**

结论（该简报 §8 第 7 条）：**用逆变换采样（`if u < cumsum`）做离散决策，反事实结果暗中依赖于你枚举分支的顺序，且这个依赖不可检验。**

**规范**：

```
categorical_draw(options: Set<Option>, log_p: Map<OptionId, Q32>, stream, tick, entity, slot) -> OptionId:
    require |options| >= 1
    for each o in options:
        oh = H32(o.content_id)                      # ★ 按候选项的内容哈希寻址，不是位置索引
        assert 所有 oh 互不相同  else 硬中止          # 极罕见；确定性可复现
        u  = uniform_q32(stream, ctr=(tick, entity.id_lo, entity.id_hi, (slot<<32)|oh))
        u  = clamp(u, 2^-32, 1 - 2^-32)             # GATED(reason=numeric_representation)
        g  = -ln_q32(-ln_q32(u))                    # 标准 Gumbel
        s  = log_p[o] + g
    return argmax_o s      # 平局按 o.content_id 字典序（概率 ~0，但必须定义）
```

**"按候选项的内容哈希寻址"是关键，且是 `provenance-replay-counterfactual` 没有写的一步**（**［本文原创，无来源，D 级］**）。如果 Gumbel 分量按候选项在代码里的**位置索引**寻址，那么：重排代码里 `match` 分支的顺序 → 每个候选拿到不同的 Gumbel → 反事实变了。这与 Oberst & Sontag 要消除的病症**完全同构**，只是从逆变换搬到了 Gumbel 的下标上。按内容哈希寻址之后：
- 重排代码 → 无变化；
- **增加一个新候选** → 只是多了一个独立的 Gumbel，其他候选的 Gumbel 完全不变（这是正确的行为：候选集变了是一个真实的机制变化，但它不应该扰动其他候选）。

**反事实的 abduction**：给定观测结果 `Y_I = i`，用 Oberst & Sontag §3.4 的精确法采后验（先采最大值——它服从标准 Gumbel；再从截断在该最大值以下的平移 Gumbel 采其余分量；最后减去位置参数 `log p_j`），然后把这组 `g` 加到干预后的 `log p'` 上取新 argmax。

**必须写进方法论声明的诚实条款**（`provenance-replay-counterfactual` §7 第 1 条）：**离散随机系统的反事实根本不可识别。** 多个 SCM 可以蕴含完全相同的干预分布却给出不同的反事实轨迹。Gumbel-max 只是一个"直觉上可接受"（满足反事实稳定性）的选择，不是"正确"的选择。**这是本项目一条不可用数据检验的建模假设，必须公开写在首页，而不是藏起来。**

### 6.8 确定性契约的 CI 门禁（从第一次提交起）

| 测试 | 判据 | 频率 |
|---|---|---|
| **线程数不变性** | 1 / 4 / 16 线程逐位相同 | 每次提交 |
| **容器迭代顺序不变性** T-ITERORDER | 逆序遍历 + 不稳定排序，逐位相同 | 每次提交 |
| **跨机器不变性** | ≥ 2 种 CPU 架构（x86-64 与 aarch64）逐位相同 | 每日 |
| **快照重放** | 从任意快照重放到 t，与原跑逐位相同 | 每次提交 |
| **零干预** T-NULLINT | 把某个值改成它原本的值，逐位相同 | 每次提交 |
| **因果隔离** T-ISOLATE | 对孤岛 A 做任意干预，隔离区 B 在 100 年内逐位相同 | 每次提交 |
| **类型抹除** T-ERASE | §3.3 | 玩具世界每次提交 / 全量每版本 |
| **依赖图** T-DEPGRAPH | 内核不依赖观察层/LLM/字符串表 | 每次提交 |
| **步长减半（崩溃期）** | §5.5 三条判据 | 每版本 |
| **守恒审计** | int64 精确相等 | 每 tick（运行时） |
| **poison-build 阳性对照** | 上述二值测试在各自的 poison-build 上**必须失败** | 每版本 |

**没有 poison-build 阳性对照的二值测试不算数**（`emergence-verifiability` F6：任何在诱饵世界上不失败的判据，不得进入验收集）。

### 6.9 ULP 发散时间的必测项

`computational-feasibility` §7 第 5 条要求的一个数：在玩具世界里扰动一个 bit，测宏观量偏离到 O(1) 需要多少 tick。在定点整数下"1 ULP"变成"1 个最小单位"（1 g、1 kcal、1 µp）。这个数同时回答两件事：(a) 我们的路径依赖有多强；(b) **单条历史线的结论里有多少是数值噪声**。

**规范**：`T_div` = 从单单位扰动到宏观距离达到种子间距离中位数一半所需的年数。**任何跨越 > `T_div` 年的因果解释，必须在集合层面陈述，不得在单条线上陈述。** 这条直接约束纲领第 2 条的表述方式，也直接约束 `causality-bookkeeping` F5 的反事实有效期 `T_half`。

### 这一节禁止了什么

- 禁止内核出现任何浮点数（`f32`/`f64`）。
- 禁止调用 libm 的超越函数；必须用本项目的定点实现。
- 禁止 wrapping / saturating 算术；溢出是硬中止。
- 禁止裸除法；禁止无守卫的除零可能。
- 禁止有状态 PRNG；禁止全局 RNG；禁止未注册的 RNG 流。
- 禁止 counter 中截断 entity_id。
- 禁止 `slot_id` 由代码位置/行号/函数名派生。
- 禁止任何形式的全局自增 id 计数器；禁止 id 碰撞时静默重命名。
- 禁止 id 上的 `<` 比较出现在 `canonical_order()` 之外。
- 禁止逆变换采样（`if u < cumsum`）做任何离散决策。
- 禁止 Gumbel 分量按位置索引寻址。
- 禁止线内并行用于有跨实体写、顺序依赖、或 Q32 乘法链归约的计算。
- 禁止把守恒审计写成 `误差 < ε`。
- 禁止在没有 poison-build 阳性对照的情况下宣称二值测试通过。
- 禁止在单条世界线上陈述跨度 > `T_div` 年的因果结论。

---

## 7. t = 0 初始条件规格

`pseudo-simulation` G1 与 `mandate-contradictions` 决定 4 都把这条列为"纲领一个字没说、但必须先定"的第一类。`pseudo-simulation` G1 原话：**"这是整个项目最大的单次假设注入"**。

### 7.1 t=0 的定义（不是一个真实年代）

**世界时间没有真实历法映射。** `tick = 0` 定义为一个**环境状态**，不是一个公元年：

> `t=0` 的合法条件：窗口内无大陆冰盖；海平面在其全新世稳定值的 ±5 m 内；主要河网拓扑已稳定（改道率低于长期均值的 2 倍）；温带落叶/常绿林带已推进到其全新世中期位置的 ±1 个纬度带内。

**为什么不给真实年代**：一旦写下"t=0 = 12,000 BP"，就有了一把尺子，就会有人做"我们的第 3,500 年对应真实的 8,500 BP"这种对齐，然后 `pseudo-simulation` S6 的对应词典就开始生长。世界时间只是 `tick`。

默认视界 `H = 3,000` 世界年（与 `computational-feasibility` §8 的预算表一致）；一切状态表示必须在 `tick = 10,000` 之前保持有效（int64 余量充足）。

### 7.2 初始人群位置

**规范（可执行）**：

```
habitability(cell) =            # 只读 Cell 的冷字段与 t=0 的气候纯函数
      f_temp(T_annual, T_coldest)          # 梯形隶属函数
    * f_water(dist_to_perennial_water_m)
    * f_biomass(Σ edible_wild_biomass_g_m2) # 由 Taxon 注册表 × 气候算出
    * f_slope(slope_p50)
    * f_flood(flood_return_period)
    全部为 Q32，连乘

seeding:
    intensity(cell) = λ0 * habitability(cell)^κ           # κ 从 θ 抽
    N_founders ~ Poisson_q(Σ intensity)                    # 流 worldgen/seeding
    位置 ~ Thomas 聚簇过程（母点强度 ∝ intensity，子点半径 r_c 从 θ 抽）
    每个母点 = 一个营群：Pop_up ~ 从 θ 抽的对数正态，年龄性别结构 = 稳定人口结构
```

**硬禁止**（`china-eastasia-geography-archaeology` §3.0(c) 第 3 条 + `pseudo-simulation` G1 + `mandate-contradictions` 决定 4）：

- 禁止读取任何考古遗址坐标数据库（Hosner 的 51,074 遗址、Qiu 的 7,083 个 14C 年代、p3k14c、CHGIS）。
- 禁止读取任何现代或历史人口栅格（HYDE）作为初始分布。
- 禁止任何以真实地名/区域为键的初始加成。
- 禁止"重生成直到世界可玩"式的拒绝采样（`pseudo-simulation` S3 表第 4 行：`while arable_fraction < θ: regen_map()` 等于"我们只在文明可能发生的世界里采样"）。**如果一个种子播撒出来的初始人群在 200 年内全部灭绝，那是一个合法结果，必须记入运行登记表。**
- 禁止对初始位置做任何"看起来合理"的人工调整。

**这些数据库的合法用途**：只在物理隔离的评估进程里，作为**事后**比对（"我们的模拟聚落分布 vs 真实遗址分布"的空间统计比较，且比对的是**协变量条件下的密度**而不是位置，见 §8.4）。

### 7.3 初始注册表（Substance / Taxon / Recipe）

这是一个**比初始人群位置更大**的假设注入，而三份红队都没有单独点它。

**规范**：

- **`Taxon` 注册表由 `world_seed` + 声明的先验生成**：抽取 `N_taxon`（从 θ 抽，量级 10³）个生物类群，每个类群的属性向量（生境包络、生物量产出曲线、繁殖体扩散核、营养密度、对选择的可响应速率、毒性、储藏耐久）从声明的多元先验中抽样。**先验的形状**（不是具体物种）从简报的经验分布标定：例如"可食野生生物量的空间梯度"、"驯化响应速率的分布形状"。
- **禁止**：任何以真实物种（粟、稻、小麦、大豆、猪、马）为条目的初始表。世界自己的作物必须是它自己的。
- **`Substance` 注册表同理**：属性向量抽样，id 即哈希。金属的存在与否由地质层（冷字段）的矿产分布决定，而矿产分布本身是扰动基底的一部分。
- **`Recipe` 初始集合是最小的**，且必须逐条列入一个冻结的、内容哈希的清单文件，每条带证据等级：
  1. `forage(cell, hours) → edible_mass_g`（采集野生生物量）
  2. `hunt(cell, hours, group_size) → edible_mass_g`（狩猎）
  3. `consume(substance, mass) → kcal`（进食）
  4. `carry`, `discard`（P3 与其逆）
  5. `shelter(mass_of_material, hours) → structure`（最简遮蔽）

  **就这五条。** 其他一切（栽培、储藏、制陶、冶金、织造、灌溉、书写）必须由 `innov/variation` 流上的变异过程在 Recipe 系数空间里产生，或者永远不出现。

  **这是本规格最激进的一条，也是最容易被侵蚀的一条。** 它的检验是 `pseudo-simulation` S4 判别测试 2（词表增长测试）：Recipe 簇数 `K(t)` 必须持续增长而不饱和。如果 `K(3000) ≈ K(500)`，说明变异过程无效，而正确的反应是**修变异机制**，不是往初始表里加条目。

**代价（必须签字）**：如果 Recipe 变异过程做不出农业，这个世界就永远是采集狩猎社会，而我们要花很长时间才能区分"变异机制错了"和"农业本来就极难出现"。`pseudo-simulation` T2 已经把这个代价说清楚了：**"世界什么都不发生，也是一个合法的科学结果。"** 这句话必须写进纲领。

### 7.4 初始参数取分布不取点值

`mandate-contradictions` F12/决定 4 的裁决，本规格照办并具体化：

```
每条世界线的身份 = (world_seed, kernel_hash, param_prior_hash, basemap_hash, llm_ledger_hash)
θ ~ Π(param_prior_hash)     # 用流 worldgen/params，由 world_seed 决定
```

- **不存在"默认参数值"这个东西。** `params.toml` 里存的是**先验分布**，不是点值。
- 每个参数条目：`{ id, name, unit, prior: {dist, args}, source, evidence_level, free: bool }`。
- `free: true`（无任何简报依据）的参数总数 ≤ 15，CI 强制（`computational-feasibility` S2）。
- ~~**证据等级闸门**：在 `tick < 2000` 期间，只有 A/B 级证据支撑的机制生效；C/D 级机制的对外接口返回"不存在/无效应"。~~
  **【本条已被取代，不得实现】** 理由：它以**绝对模拟年份**为参数决定哪些机制存在，这就是一个阶段门——世界的物理定律会在第 2000 年自己变一次，且这个变化没有任何世界内原因，直接违反本项目的涌现与因果原则（`INTEGRATION-REVIEW` C16 也独立指出了这一点，并注意到它会让玩具世界的"全部机制开启"恒假）。
  **取代条款**：证据等级只用于文档、参数登记与报告，**永不作为运行时开关**。机制的启用与停用只能由世界状态条件决定。如果一个机制的证据不足，正确做法是**不实现它**（返回 `NOT_IMPLEMENTED`，见宪法 §3.1 的四态区分），而不是让它在某个模拟年份自动上线。
- **必填报告字段**：终态方差中来自 `worldgen/*` 流（初始条件 + θ 抽样）的份额。这是 `mandate-contradictions` F12 第 3 条要求的一等报告。

### 7.5 初始条件敏感性作为一等实验

设计：`B 个基底实例 × P 个 θ 抽样 × S 个种子`，做嵌套方差分解。见 §8.5 的自主性测量管线——**它与初始条件敏感性实验是同一批运行**，不需要额外预算。

### 这一节禁止了什么

- 禁止 t=0 与任何真实年代建立映射。
- 禁止初始人群位置读取任何考古遗址、14C、CHGIS、HYDE 数据。
- 禁止初始位置的任何人工调整、任何"重生成直到可玩"的拒绝采样。
- 禁止初始 Taxon/Substance 表包含任何真实物种或真实材料条目。
- 禁止初始 Recipe 集合超出五条；禁止在词表增长测试失败时往初始表加条目。
- 禁止参数取点值；`params.toml` 只能存先验分布。
- 禁止 `free: true` 参数超过 15 个。
- 禁止 C/D 级机制在 `tick < 2000` 期间返回近似值而不是"无效应"。
- 禁止发布任何不带"终态方差中 worldgen 份额"的长跑报告。

---

## 8. 地图基底裁决与"自主性"的可计算定义

### 8.1 冲突的准确形状

| 来源 | 主张 | 核心论据 |
|---|---|---|
| `china-eastasia-geography-archaeology` §3.0 | **真实东亚地形做几何基底**，不要纯合成大陆；配"真实基底 + 扰动族"，`baseline` 用于参数标定（唯一允许看真实考古数据的世界），`variant_*` 用于证明机制不是被地形硬编码的 | 校准资源在合成大陆上**全部失效**：51,074 遗址点、7,083 个 14C 年代、CHGIS、HYDE、CHELSA-TraCE21k。"放弃真实地形 = 放弃校准集"；且合成地形的算法偏见"以不可见的方式污染涌现结论" |
| `east-asia-climate-environment` §11.2 | **真实地理骨架 + 一次性创生扰动**（镜像/旋转/河网局部重连/全面去名）作为主线 | "为什么不用一比一真实地形：因为它会诱导'这里应该出现关中'这类思维，而且真实地名会污染叙事层" |
| `mandate-contradictions` F1 | **正式主线跑扰动基底；未扰动真实基底只在评估进程里出现（物理隔离、只读、不同目录不同进程）**；并把 `china-geography` §3.0 的校准资源全部搬进评估进程 | 三重身份不可兼得：无 holdout + 宏观骨架高概率复演。距草原距离是帝国密度最强预测因子，三因子解释 42% 方差；消掉草原效应 R² 从 0.65 掉到 0.17（Turchin et al. 2013，经该红队转述，标注已核验） |

### 8.2 裁决（D11）

**采纳 `mandate-contradictions` F1：正式主线运行在一次性创生扰动基底上；未扰动的真实基底只存在于物理隔离的评估进程里。**

但 F1 的裁决有一个它自己没有解决的漏洞：`china-geography` 的反对意见——**扰动之后，那 51,074 个遗址点还怎么用？** 如果答案是"用不了"，那 F1 就是在用"放弃校准集"换"自主性"，而纲领第 8 条明确要求真实历史是校准集。

**本规格补上这一步（这是本节的主要贡献）：**

> **扰动算子必须声明它的等变类；校准量必须是该等变类下的不变量。**

具体：

| 扰动算子 `T_k` | 数学性质 | 什么统计量在它下面**精确不变** |
|---|---|---|
| 东西镜像 | 球面等距同构 | 一切**只依赖协变量、不依赖绝对坐标**的统计量：`density(site \| elev, slope, precip, TWI, dist_to_navigable_water, dist_to_grassland_biome)` |
| 旋转 90° | 球面等距同构（需重投影，纬度带随之改变——**因此旋转必须与气候带一起旋转，否则不是等距**） | 同上，**但只有在气候场随之旋转时** |
| 河网局部重连 | **非等距** | 不依赖 `dist_to_navigable_water` 与流域拓扑的统计量 |
| 海平面偏移 ±30 m | **非等距** | 不依赖海岸距离的统计量 |
| 走廊剪断/新开（山口高程 ±200 m） | **非等距** | 不依赖网络中介中心性的统计量 |
| 降水梯度主轴旋转 ±30° | **非等距** | 不依赖降水梯度方向的统计量 |

**规范**：

1. **主线基底 = `T(真实骨架, world_seed)`，一次性、创生时应用、结果冻结、内容哈希为 `basemap_hash`。** 不是每 tick 扰动。
2. `T` 的算子集合与其参数分布进 `params.toml`，用流 `worldgen/basemap_perturb`。
3. **全面去名**：主线基底不含任何真实地名/水名/山名/族名。`Cell.h3` 仅供静态预计算与观察层使用；**任何 agent 面向的视图、任何 LLM prompt 都不得出现经纬度绝对值**，只能出现相对方位与本地地形语义（`china-eastasia-geography-archaeology` §3.0(c) 第 1 条）。
4. **两级校准**：
   - **等距不变量**（镜像/旋转下精确不变的协变量条件统计量）→ **可以在主线上直接校准**。遗址点的空间分布在这类统计量上完全可用。
   - **非等距量**（依赖水系拓扑、海岸、走廊、降水梯度方向的量）→ **只能在评估进程里、在未扰动基底上标定其函数形式**，然后把**函数形式**（不是拟合的空间场）搬到主线。搬运的是 `f(covariates) → rate`，不是 `f(location) → rate`。
5. **物理隔离**（`mandate-contradictions` F1 第 2 条）：评估进程与内核不同 crate、不同进程、不同目录；真实基底与考古数据只读挂载；内核对它零可见性，CI 强制。评估进程的输出**只能是**参数先验与函数形式，且每一次搬运都要在参数登记表留痕（谁、什么时候、搬了什么、依据是什么）。

**这条裁决同时满足了两篇简报**：`china-geography` 要的"统计与拓扑性质 + 全套校准资源"通过等距不变量保留下来；`east-asia-climate` 要的"实例被打乱、没人能预期关中"通过扰动实现。**两者的冲突是可解的，因为它们争的其实是不同的东西：一个要统计结构，一个要实例不可预期。**

### 8.3 为什么不用纯合成大陆

采纳 `china-eastasia-geography-archaeology` §3.0(a) 的判断：合成大陆最大的隐患不是"不像"，而是**"你不知道它哪里不像"**——生成算法的偏见会以不可见的方式污染涌现结论（例如所有文明都长在河口，因为侵蚀算法让河口过于优越）。补充该简报 §9.16 自报的 D 级判断："合成地形算法（Perlin/diamond-square）产生各向同性山脉、缺乏构造走向"——这是一个技术判断而非文献结论，但它指向的问题是真的：**"盆地—走廊—平原"拓扑（一条 900 km 的单线走廊连接两个大生态区）是一个低概率构型，随机生成极难自发产生。**

### 8.4 "自主性"的可计算定义（D 级，附完整测量管线）

`mandate-contradictions` F1 提出 `自主性 = H(宏观历史描述 | 地理, 机制, 参数) / H(宏观历史描述)`，并要求"Phase 0 就要把这个测量管线做出来，并在跑第一条正式历史线之前给出基线数字"。

**问题**：这个定义在 N=200 种子下不可估计——K 维联合熵需要指数级样本。本规格把它改写为一个**可估计的方差分解**（**［改写为本文原创，无来源，D 级；`R²_geo` 部分来自 `complex-systems-emergence` M6 的捷径检验］**）。

#### 8.4.1 预注册的宏观描述向量 M

**跑第一条正式线之前写死，此后不得增删**（增删 = 重新预注册 + 全部旧结论作废）：

**骨架层（预期低自主性）**
1. 人口重心的最终位置（格坐标，二维）
2. 农牧生业分界带的位置（分界带质心的纬向坐标）
3. 最大聚居簇所在流域
4. 人口密度前 10% 的格集合与地理协变量的互信息

**中层（预期高自主性）**
5. 检测到的政体数（观察层四检测器的一致部分）
6. 最大政体的人口规模时间序列的 P95
7. 政体寿命分布的形状参数与变异系数
8. 统一/分裂事件的间隔分布
9. Recipe 簇数 `K(t)` 的终值与增长曲线形状
10. `SameKindAs` 命题聚类数（"民族数"）
11. `ShouldDefer` 命题的最大连通分量占人口比
12. 城市化率（按声明阈值）的时间序列形状
13. 不平等（物质存量 Gini）的时间序列形状
14. 精英职位追逐者/职位比的峰值时刻
15. 首次出现三层控制树的 tick
16. 检测到的宗教样命题簇数
17. 冲突规模谱的幂律指数 α（Clauset 程序）
18. 技术扩散前沿速率（km/yr）
19. 崩溃间隔分布的形状（**不是频次**，`east-asia-climate` §11.4 第 7 条）
20. 世内史学的 `D(t) − U(t)`（史学水平）

K = 20 个分量（前 4 个是骨架层）。

#### 8.4.2 实验设计与估计量

```
设计: B 个基底实例 × P 个 θ 抽样 × S 个种子 = 全因子
建议: B = 4, P = 10, S = 20  →  800 次长跑
成本: T_run ≤ 1 h，8 台 × 16 进程 = 128 并发 → 6.25 小时墙钟
```

对每个分量 `M_k`，做嵌套方差分解（随机效应 ANOVA）：

```
Var(M_k) = σ²_basemap + σ²_θ + σ²_seed + σ²_interaction

Autonomy_k = ( σ²_seed + σ²_(seed×basemap) ) / Var(M_k)
```

以及捷径份额（`complex-systems-emergence` M6 第 2 点）：

```
R²_geo,k = 固定容量 GBM 用 {elev_p50, slope_p50, precip, dist_to_navigable_water,
                            dist_to_grassland_biome, latitude_band}
           预测 M_k 的**样本外**（按基底实例分折）R²
```

**聚合自主性** = 中层 16 个分量的 `Autonomy_k` 的中位数。

#### 8.4.3 预注册的接受带（全部 D 级，签字后冻结）

| 层 | 指标 | 预注册带 | 越界怎么办 |
|---|---|---|---|
| 骨架层（1–4） | `Autonomy_k` | 允许低至 **0.10** | **不许为了提高它去改地图或改机制**（`mandate-contradictions` F10：这是"把伪造引入项目的最典型路径，而且它会打着增强自主性的旗号"） |
| 骨架层 | `R²_geo,k` | 允许高至 **0.80** | 该结论只能表述为"我们复现了地理效应"，**不得表述为"我们的世界演化出了 X"** |
| 中层（5–20） | `Autonomy_k` | **≥ 0.50** | 低于此值 = 中层也被地理/参数决定 = 项目在这一维度失败，必须公开报告 |
| 中层 | `R²_geo,k` | **≤ 0.50** | 超限的那条结论降级为"地理效应"（`mandate-contradictions` F1 第 3 条的措辞纪律） |

**`mandate-contradictions` F10 的疫苗必须现在打**：在跑第一条正式线之前，把上表签字冻结，并同时书面承认——**我们放弃"这个世界的宏观格局会和真实东亚很不一样"这个期待，把承诺改成"这个世界的中层历史与真实东亚不同"。**

### 这一节禁止了什么

- 禁止正式主线跑未扰动的真实基底。
- 禁止把真实基底、考古数据库、CHGIS、HYDE 挂进内核进程；它们只能在物理隔离的评估进程里只读出现。
- 禁止逐 tick 扰动；扰动是一次性创生操作，结果冻结进 `basemap_hash`。
- 禁止在主线上使用任何**非等距不变量**做校准（依赖水系拓扑、海岸距离、走廊中介中心性、降水梯度方向的量）。
- 禁止从评估进程搬运拟合的**空间场**；只能搬运**协变量函数形式**，且每次搬运必须在参数登记表留痕。
- 禁止任何 agent 视图或 LLM prompt 包含经纬度绝对值或真实地名。
- 禁止纯合成大陆作为主线基底。
- 禁止在自主性数字难看时修改地图或机制以提高它。
- 禁止在跑第一条正式线之后修改 M 向量的分量或接受带。
- 禁止把 `R²_geo > 0.5` 的宏观结论表述为"我们的世界演化出了 X"。

---

## 9. 气候：合成生成器

### 9.1 裁决

**生产世界的气候驱动必须是合成序列。** 三处独立要求：

- `pseudo-simulation` F4：**"生产世界（我们将来要写小说、要说'这是这个世界自己的历史'的那个世界）的气候驱动必须是合成序列**，其统计性质（方差、自相关、极端事件重现期、ENSO 类准周期强度）从古气候研究中取，但具体实现由 `world_seed` 生成。真实古气候序列**只能**出现在验证运行中，作为 surrogate 集合里的一个样本，并且那些运行永久标记为 `calibration_only`，不得作为世界史来源。"
- `east-asia-climate-environment` AP6：拿真实古气候序列直接驱动世界，然后惊讶于"历史很像"，是本领域反模式。
- `east-asia-climate-environment` §11.2 方案 B 的五条代价：因果链断裂（外生文件的第 N 行不是原因）、反事实受污染（"改气候"变成"改文件"）、诱导历史匹配（"一旦知道 1637 年应该有大旱，我们会不自觉地调参数让那一年真的出乱子"）、平行世界不可能（所有分支共享同一条气候史）、**序列长度不够**（年分辨率的旱涝网格只覆盖 960 CE 之后，前文明期根本没有年分辨率真实序列——所以方案 B 无论如何都要在早期退化成方案 A）。

**地理与气候的不对称处理**（`east-asia-climate-environment` §11.1，本规格采纳）：

> **地理是边界条件**（山就是山，不需要世界内的原因）；**气候序列是事件生成器**（每一次干旱都是"发生了什么"，在纲领第 2 条下必须可追溯）。

### 9.2 气候的三层分解与它们各自的表示

采用 `east-asia-climate-environment` M1 的加性分解 `M(t) = M_orb(t) + M_evt(t) + M_iav(t)`，但对每一层规定不同的表示：

| 层 | 内容 | 表示 | 是否进 L0 状态 | 是否逐 tick 遍历 | 可否分叉 |
|---|---|---|---|---|---|
| **L-orb** 轨道基线 | 岁差带缓变 | **O(1) 无状态纯函数** `f(world_seed, tick, cell_lat_band)` | 否 | 否 | 是（改 seed） |
| **L-evt** 千年事件 | 世纪级弱季风事件 | **创生时冻结的事件表**：用流 `climate/lowfreq` 在世界创生时对整个视界抽一次非齐次泊松过程，得到 `[(t_k, d_k, a_k, spatial_pattern_k)]`，进世界创生记录，可由 `world_seed` 单独重算 | 否（表在创生记录里） | 否 | **是——这是"如果那次大旱没发生"的合法反事实入口** |
| **L-iav** 年际噪声 | AR(1)/AR(2) 红噪声 | **L0 携带态** `Cell.clim_ar[4]`，每 tick 用流 `climate/highfreq` 的创新项推进 | 是 | 是（1.4×10⁵ 格 × ~2000 周期） | 是 |
| **L-eco** 生态滞后 | 农业适宜度跟随土壤湿度/植被而非降水（`east-asia-climate` M4） | L0 携带态 `Cell.eco_lag[2]` | 是 | 是 | 是 |

**为什么低频不进 L0**：`computational-feasibility` S5 第 5 条明确要求气候场"必须显式禁止落盘"——25 km × 12 月 × 3000 年 × 2 变量 = 5.5 GB/线（本规格的 res 5 会更大）。低频做成纯函数 + 事件表既省掉落盘，又满足 `east-asia-climate` §652 的"气候必须可分叉，否则所有平行世界共享同一条气候史，分岔空间被人为压缩"。

**为什么高频要进 L0**：AR 需要记忆。3 MB 的携带态（1.4×10⁵ 格 × 4 × i32 + 生态滞后）是可以接受的代价，而且它天然随快照分叉。

### 9.3 生成器的标定目标（分布匹配，不是逐年匹配）

照抄 `east-asia-climate-environment` §11.4，**这是校准的正确形态**：

1. 气候序列的**功率谱**（岁差带、千年带、年代际带的相对功率）
2. 干旱事件的**持续时间分布**（真实值：世纪级 100–500 年；多年级 3–7 年）
3. 干旱事件的**空间范围分布**（从 MADA / Hao et al. 2023 实测半变异函数）
4. 年降水 CV 的**空间梯度**（东南低、西北高）
5. 洪水频次对上游人类扰动的**响应弹性**（真实锚点：过去千年增幅近一个数量级，81 ± 6% 人为）
6. 改道的**重现间隔分布**（真实锚点约 1/98 年，该简报标注 **C 级来源**）
7. 社会侧：**崩溃间隔的分布形状**（不是频次）。真实历史的王朝存续时间分布是重尾的；**如果我们的模拟产生近乎周期性的崩溃间隔，说明阈值把气候变成了节拍器——这是失败信号，不是成功信号。**

**第 7 条是本项目最重要的失败检测器之一**，且它可以直接写成自动化健康检查。本规格把它列为 CI Tier-2 项。

事件基率来自 `east-asia-climate-environment` M1：`λ_evt ≈ 1/1100 yr⁻¹`（世纪尺度弱季风事件，A 级，来自 Wang 2005 的 8 次/9000 年）；持续时间 `d_k ~ LogUniform(100, 500)` 年；年际 AR 系数 `ρ ≈ 0.1–0.3`（该简报自报为 **D**，无东亚古气候直接来源）。

### 9.4 真实古气候序列的合法用途

**只有两处**：

1. **评估进程里的 surrogate 集合中的一个样本**（`abm-methodology` M6 的外生序列置换检验：真实序列 / 时间反转 / 块状打乱 / 同自相关 surrogate 各跑一遍，比较 POM 通过分数）。
2. **低频包络的标定输入**：CHELSA-TraCE21k 东亚窗口的**平滑后低频包络**可以用来标定 `M_orb` 的振幅与相位分布的先验（`east-asia-climate-environment` §11.2 方案 A 第 2 点），但**不得逐年读取**。

所有使用真实序列驱动的运行，其运行登记表条目永久带 `calibration_only` 标记，且**不得作为世界史来源、不得写小说、不得作为"这个世界自己的历史"**。这条标记必须是数据库层面的（不可删除字段），不是约定。

### 9.5 诚实条款

千年气候事件由 `world_seed` 生成，因此它们**在世界内部没有原因**——它们是边界条件。这与地理是边界条件一样，是可接受的。但必须写清楚：

> 世界内的一次大旱，其因果链的终点是"气候生成器在种子 W 下于第 t_k 年产生了一个持续 d_k 年、幅度 a_k 的事件"。这不是世界内的原因，是世界的边界条件。**任何把大旱本身当作"被解释的事件"的说法都是错的；可以被解释的是社会对它的响应。** 这条必须出现在因果链 UI 上，而不是脚注里。

### 这一节禁止了什么

- 禁止生产世界读取任何真实古气候的逐年序列。
- 禁止气候场落盘；必须现算或由创生冻结的小表重算。
- 禁止把千年事件表做成手工编辑的文件；它只能由 `world_seed` + 声明的过程生成。
- 禁止逐年匹配式的气候校准；只能匹配 §9.3 的七类分布/形状。
- 禁止把气候变量直接连到社会事件（`east-asia-climate` AP3：`if 大旱 then 叛乱`）；气候只改变物理量（产量、水位、可通行性），社会后果必须经由已有脆弱性传导（`state-formation` AP12）。
- 禁止"暖=好/冷=坏"的单调映射（`east-asia-climate` AP7）。
- 禁止用全国单一气候指数（AP2）；必须是空间场。
- 禁止用石笋 δ18O 当降水量（AP4）。
- 禁止 `calibration_only` 标记的运行进入任何世界史叙述、小说素材库或对外展示。
- 禁止在因果链 UI 上把气候事件呈现为"被解释的事件"。

---

## 10. 世界边界：东亚之外是什么

`mandate-contradictions` 决定 5 称这是**"纲领遗漏的最大的一个结构性决定"**，理由是它决定草原压力这一最强的宏观驱动到底是内生的还是外生注入的——而 F1 已经证明距草原距离是帝国密度的最强预测因子（三因子解释 42% 方差；消掉草原效应 R² 从 0.65 掉到 0.17）。该红队的建议默认值是"有限世界 + 一个显式的世界外通量接口：外来技术、病原、人群以低频泊松流进入，到达率由地理通道成本计算，参数冻结并公开"。

### 10.1 裁决（D12）：与该红队的建议相反

**本规格不采纳"低频泊松外部通量"作为默认值。裁决是：**

1. **窗口必须画得足够大，使整条温带草原/牧业生态带及其与农耕带的接触面完整地在世界之内**，其人口、畜群、机动性、技术全部内生模拟。
2. **窗口外是吸收边界，默认外部通量恒为 0。** 越界迁出的人口被记为永久损失（并进入 `Pop_up` 守恒审计的声明汇项）；没有任何东西从窗口外进来。
3. `world_external_flux` 接口**在生产线编译期关闭**（feature flag off，代码里连符号都不存在）。它只能在显式标记的实验线上启用；任何启用它的运行，其登记表条目永久带 `exogenous_flux_on` 标记，**且不得用于任何关于自主性的主张**。

### 10.2 为什么

**理由一（决定性）：草原必须内生。** 如果窗口边界切在草原带里，那么"北方压力"就变成了一条从窗口外流进来的泊松流，其到达率是我们写的一个 D 级参数。于是纲领里最重要的宏观格局（`mandate-contradictions` F1 腿一列出的"北方农牧接触带高频出现大型政体""南北二元"）就是**我们手动注入的**。该红队自己在决定 5 里写了这句话："**若做成外生流，我们等于手动注入了真实历史最重要的那个变量。**" 本规格把这句话当作否决理由，而不是当作一个可接受的代价。

**理由二：非零默认值烤不回来。** 一个非零的外部到达率会静默控制最有后果的东西（新作物、新病原、新军事技术）的出现时刻。它是一个 D 级数字，没有任何办法标定，而它的下游影响会被路径依赖放大三千年。设成 0 之后，世界的贫瘠是**可读的**：如果世界从没长出金属冶炼，那是一个结果，不是一次缺席的进口。而且这个决定在诚实的方向上可逆——**你随时可以打开它并测量差异；你没法把一个已经烤进三千年历史的到达率取出来。**

**理由三：`pseudo-simulation` S3 的形状。** 外部通量接口在结构上与该红队禁用清单里的"兜底重生"同形：它是一个"当世界内部没有产生我们期待的东西时，从外面送一个进来"的通道。它的正当工程借口是"真实东亚不是封闭的"，这个借口是真的，但它同样适用于剧情树。

### 10.3 窗口的可执行定义

**规则（不是一个固定的经纬度框，而是一条准入判据）**：

> 窗口必须满足：
> - **(W1)** 包含农耕核心区相邻的温带草原生态带的**完整纬向与经向跨度**，且在草原带之外还有 **≥ 500 km 的缓冲**（缓冲区仍然完整模拟）。
> - **(W2)** 包含所有直接与陆地核心区相连的海岸线，以及第一列近海群岛链。
> - **(W3)** 边界处的**通行成本必须自然地高**（高原、荒漠、深海），使 (W1)/(W2) 之外的迁移在物理上罕见；若边界不得不切在低成本通道上，该通道必须被显式记为一条"世界的裂口"并在报告中列出。
> - **(W4)** 窗口一旦确定即冻结进 `basemap_hash`；改窗口 = 世界作废重跑。

**指示性取值**（**D 级，必须在构建时按 (W1)–(W3) 实际测量后确定**）：约 65°E–150°E、15°N–58°N。球面盒面积 3.55×10⁷ km²（含海），H3 res 5 约 **1.40×10⁵ 格**，按陆比 0.6 约 **8.4×10⁴ 陆格**。**陆比 0.6 是我拍的数，必须实测。** 注意 `computational-feasibility` S3 里的"东亚陆地约 1.2×10⁷ km²"该红队自己标注为"沿用任务书，未核实"——本规格的窗口比它大得多，因为 (W1) 要求把整个草原带装进来。

### 10.4 代价（必须签字）

**这是本规格代价最大的一条裁决。**

| 代价 | 说明 |
|---|---|
| **没有西亚驯化物** | 小麦、大麦、绵羊、山羊、黄牛、马、青铜与铁的冶炼技术，在真实历史上都是从窗口外传入东亚的。零通量意味着**这些东西必须在窗口内被独立发明，否则永远不存在。** 我们的世界很可能没有马；没有马意味着没有骑射；没有骑射意味着草原压力的形态与真实历史完全不同。 |
| **这不是 bug，是这次裁决买到的东西** | 如果我们注入马，"草原骑兵帝国"就是我们放进去的。如果我们不注入马，世界要么自己驯化出某种大型可骑乘动物（Taxon 注册表里是否存在这样的类群，由 `worldgen/registry` 的抽样决定），要么发展出完全不同的北方接触带动力学。**后者正是纲领第 1 条与第 7 条要的东西。** |
| **失去一批校准锚点** | 一切依赖"传入时间"的考古锚点（`china-eastasia-geography-archaeology` §4.1 的时间锚点里凡涉及外来物种/技术的）在主线上不可用。它们只能在评估进程里用。 |
| **必须公开报告的指标** | 每次长跑必须报告：越界外迁的累计 `Pop_up`、以及"世界的裂口"（W3）处的实际跨界迁移量。若后者不接近 0，说明窗口画错了。 |

### 10.5 被考虑并拒绝的两个替代方案

| 方案 | 为什么拒绝 |
|---|---|
| **"幽灵边缘"**：窗口边界外加一圈 1 格宽的降级模拟带（只有 L0 队列，无个体无聚落），使跨界通量由同一套物理产生而非外部表 | 它不是外生注入（好），但它也产生不了新的驯化物或新技术（因为它没有历史深度、没有个体、没有 Recipe 变异所需的信息网络）。所以它付出了复杂度却没换到 §10.4 的那个代价的缓解。 |
| **窗口扩到整个亚欧非** | 这正是 Turchin et al. 2013 做的（他用 100 km 格）。在 res 5 下格数会到 ~10⁶ 量级，格扫预算超支一个数量级。且它把项目从"以东亚为舞台"变成"以旧大陆为舞台"，超出纲领。 |

### 10.6 这条裁决与其他裁决的耦合

- 与 D11（扰动基底）：扰动算子中的"走廊剪断/新开"可能改变 (W3) 的裂口位置。因此**扰动之后必须重新检查 (W1)–(W3)**，不满足则该基底实例作废重抽。这个检查必须是自动的，且作废率要报告（作废率高说明扰动算子太强）。
- 与 §7.3（初始注册表）：既然没有外部输入，Taxon 注册表的抽样就决定了这个世界的生物学天花板。**"这个世界里有没有可驯化的大型役畜"是一次抽样的结果，不是一个设定。** 这个 bit 会解释后续三千年历史的很大一部分方差，因此它必须作为一个一等的、在报告首页出现的世界属性。**［这条观察为本文原创，无来源，D 级］**
- 与 §8.4（自主性）：零通量提高了自主性（少了一个外生驱动），但降低了与真实东亚的可比性。这个取舍必须在自主性报告里显式说明。

### 这一节禁止了什么

- 禁止把草原/牧业生态带切在世界边界之外。
- 禁止生产线启用任何外部通量（技术、病原、人群、物种、基因）。
- 禁止 `world_external_flux` 的代码在生产构建里存在（feature flag 必须是编译期的，不是运行时的）。
- 禁止把启用了外部通量的运行用于任何自主性主张、任何世界史叙述、任何小说素材。
- 禁止在窗口不满足 (W1)–(W3) 时开跑。
- 禁止改窗口而不作废世界重跑。
- 禁止把"世界里没有马"当作 bug 修（它只能通过改 Taxon 先验来改变，而那是一次内核版本变更 + 全部重跑）。
- 禁止在扰动基底后不重新检查 (W1)–(W3)。

---

## 11. 汇总

### 11.1 不可逆决定清单（写第一行内核代码之前必须签字）

| # | 决定 | 事后无法补的原因 |
|---|---|---|
| 1 | 五条原语准入规则 + `PRIMITIVE_REGISTRY` 的封闭性 | 决定内核每一个 API 的形状 |
| 2 | L0 实体清单（含**不存在** `Polity`/`Settlement`/`Dynasty`/`Class`/`rule_tags`） | 加一类实体 = 全部重跑；减一类 = 全部机制重写 |
| 3 | 义务 = InfoCopy + 胁迫能力（不是关系边） | 债务/税/契约的全部机制挂在它上面 |
| 4 | 单位体系 + 360 日世界年 | 一切参数、一切标定同时失效 |
| 5 | 定点整数（放弃浮点） | 事后改 = 重写内核 |
| 6 | H3 res 5 单一动态网格 + 窗口范围 | 格尺寸是所有空间机制的公共标定基准（`cliodynamics` 明确警告缩小网格必须重新标定 δ_s） |
| 7 | 主时钟 1 年 + 两条整除链 + 子时钟配额表 | 一切速率、预算、事件密度以 tick 计价 |
| 8 | `PHASE_ORDER_V1` | Kehoe 2016 证明的 20 年不可复现 |
| 9 | 实体 id = 内容/血缘派生哈希 | `causality-bookkeeping` F7："18 个月后无法回改（全部历史作废）" |
| 10 | CBRNG 布局 + 流分配表 | 改布局 = 所有旧世界线作废 |
| 11 | Gumbel-max + 内容哈希寻址 | 反事实机制一旦确定就绑定了所有已发表的反事实结论 |
| 12 | 扰动基底 + 等距不变量校准协议 | 主线的地理身份 |
| 13 | 合成气候（低频纯函数 + 冻结事件表 + 高频 L0 态） | 气候是否可分叉决定平行世界是否可能 |
| 14 | 零外部通量 + 窗口准入判据 (W1)–(W4) | 草原压力是内生还是注入 |
| 15 | 初始 Recipe 集合只有 5 条 | 加一条 = 世界的技术天花板被我们抬高，且不可追溯 |

### 11.2 本规格没能解决、必须由人裁决或后续研究的问题

**【原文缺失说明】** 本节原本写的是"见 StructuredOutput 的 `open_problems`"，但产出本规格的 agent 在返回结构化结果那一步被会话额度中断，**那份 `open_problems` 从未存在**，且经检索工作流 transcript 确认不可恢复。

按项目规则（未成功恢复则删除依赖），本节改为指向已实际存在的等价材料：
- 本规格自己发明、无来源的部分：见 §11.4（13 条，逐条标注）。
- 四份规格之间的冲突与缺口：见 `docs/INTEGRATION-REVIEW.md` §1 与 §3。
- 需要人裁决的取舍：见 `docs/OPEN-QUESTIONS.md` §1。

### 11.3 CI 测试总表

| 层级 | 测试 | 判据 | 频率 |
|---|---|---|---|
| 结构（二值） | T-DEPGRAPH | 内核不依赖观察层/LLM | 每次提交 |
| 结构（二值） | T-ERASE（玩具） | 逐位相同 | 每次提交 |
| 结构（二值） | T-ITERORDER | 逐位相同 | 每次提交 |
| 结构（二值） | T-NULLINT | 逐位相同 | 每次提交 |
| 结构（二值） | T-ISOLATE | 隔离区逐位相同 | 每次提交 |
| 结构（二值） | 线程数不变性 | 1/4/16 线程逐位相同 | 每次提交 |
| 结构（二值） | 原语准入检查（R1a/R2/R3/R4） | 全通过 | 每次提交 |
| 结构（二值） | 禁用字段/黑名单 AST 检查 | 零命中 | 每次提交 |
| 结构（二值） | `free: true` 参数 ≤ 15 | 计数 | 每次提交 |
| 运行时（二值） | 守恒审计 | int64 精确相等 | 每 tick |
| 运行时（二值） | 溢出/负量检查 | 零命中 | 每 tick |
| 结构（二值） | 跨机器不变性 | ≥2 架构逐位相同 | 每日 |
| 数值 | 步长减半（崩溃期）判据 (I)(II)(III) | §5.5 | 每版本 |
| 数值 | `T_div`（单单位扰动发散时间） | 报告值 | 每版本 |
| 结构（二值） | T-ERASE（全量） | 逐位相同 | 每版本 |
| 元测试 | poison-build 阳性对照 | 上述二值测试必须**失败** | 每版本 |
| 性能 | 格扫周期预算 ≤ 1.05×10⁹/tick | 空壳内核基准外推 | 每次提交 |
| 性能 | log-log 斜率 ≤ 1.2（`computational-feasibility` S4） | 1×/2×/4× 实体数 | 每次提交 |
| 分布 | 崩溃间隔分布形状不得近周期（`east-asia-climate` §11.4 第 7 条） | 报告 + 拒绝域 | 每版本 |
| 分布 | 自主性管线（800 次长跑） | §8.4.3 接受带 | 每版本 |

### 11.4 本规格自身的不确定性（我编的东西汇总）

1. 随附性检验作为"不引用制度"的操作化 —— 本文原创，D 级。
2. `Q32` 必须声明分子分母 —— 本文原创，D 级。
3. 义务 = InfoCopy + 胁迫能力（D3） —— 本文原创，D 级。
4. 360 日世界年 —— 本文原创，D 级。
5. 队列维度用绝对存量档而不是相对五分位 —— 本文原创，D 级（与 `population-dynamics` §3.11 有意不同）。
6. 取消 `Settlement` 与 `Polity` 实体（比 `pseudo-simulation` S5 的"类型删除测试"更进一步：直接不存在） —— 本文原创，D 级。
7. 拒绝 `stratification-kinship-inheritance` §3.16.3 的 `rule_tags` 进 L0 —— 本文原创，D 级；代价见 §11.2。
8. Gumbel 分量按候选项内容哈希寻址 —— 本文原创，D 级。
9. 步长减半测试的判据 (II)（收敛阶 ∈ [2.5, 6.0]）与 (III)（无系统同号偏向） —— 本文原创，D 级。
10. 崩溃期窗口的三条阈值定义（15%/25y、20%/5y、P99） —— 本文原创，D 级。
11. 自主性的方差分解改写与全部接受带数字（0.10 / 0.80 / 0.50 / 0.50） —— 改写为本文原创，D 级；`R²_geo` 部分沿用 `complex-systems-emergence` M6 与 `mandate-contradictions` F1。
12. 零外部通量的裁决（与 `mandate-contradictions` 决定 5 的建议默认值相反） —— 裁决为本文原创，D 级；论据来自该红队自己的分析。
13. 窗口准入判据 (W1)–(W4) 与 500 km 缓冲 —— 本文原创，D 级。
14. 初始 Recipe 集合只有 5 条 —— 本文原创，D 级。
15. 一切周期预算数字（2,000 周期/格气候、8,500 周期/格农业、350 ms 格扫上限、格扫 29%）—— 本文原创，D 级；在空壳内核基准出数之前全是纸上谈兵，`computational-feasibility` §7 第 1 条已经说了这句话，本规格重复一遍。
16. 实体数硬上限（InfoCopy 5×10⁶、Household 2×10⁵、Site 16/格） —— 沿用或改写 `computational-feasibility` S4 的 D 级反推数字。
17. 陆比 0.6、1.40×10⁵ 格、8.4×10⁴ 陆格 —— 我从球面盒面积与 H3 res5 均面积算的；H3 均面积是 A 级（官方表），盒面积算术可复算，**陆比是我拍的**。
18. `T_div` 作为"单条线因果结论有效期"的上界 —— 概念来自 `computational-feasibility` §7 第 5 条，把它写成硬规则是本文的规定，D 级。
