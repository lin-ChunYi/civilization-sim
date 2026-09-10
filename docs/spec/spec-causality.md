# spec-causality —— 因果、重放、分叉、反事实与存储架构

> **【生效范围（2026-09-10）】** 本文件是 Phase 0 的**规格草案**，未获整体批准。
> 四份规格由互不通气的 agent 写成，在若干接口上互不相容（见 `docs/INTEGRATION-REVIEW.md` §1）。
> **凡与 `docs/EXP-01-SPEC.md` 重叠的部分，以 EXP-01-SPEC 为准**；被取代的具体条款逐条列在 `docs/EXP-01-CONFLICTS.md`。
> 本文件保留作为论证与备选方案的来源，不作为实现依据。


> **【悬空引用说明（2026-09-10 修复）】**
> 本规格的正文引用了 **§12.1**（因果算力推导）、**§13.1**（玩具标定世界 `W_cal`）、**§15**（双孪生线实测的通道封闭偏差，`AttributionReport.channel_closure_bias` 字段的定义处）。
> 产出本规格的 agent 在写到 §11 时被会话额度中断，**这三节从未被写出**，经检索工作流 transcript 确认不可恢复。
> 按项目规则处理：**这三节标为未采纳，一切依赖它们的数字与字段一并作废**——
> - 凡引自"§12.1"的算力数字（含 §1 出现的每问 1,100 CPU-h）**不得使用**，因为其推导不存在；
> - `channel_closure_bias` 字段**暂不实现**，它没有定义；
> - `W_cal` 的需求由 `docs/EXP-01-SPEC.md` 的单张小地图承担，不再单列。
> 本文件其余部分（§1–§11）仍然有效，但其中被 `docs/INTEGRATION-REVIEW.md` §1 判定为落败的接口条款以那份审查为准，见 `docs/EXP-01-CONFLICTS.md`。


- **slug**: `spec-causality`
- **状态**: Phase 0 规格草案（写第一行内核代码之前必须冻结的部分已用 ⛔ 标出）
- **日期**: 2026-09-10
- **必读依据**: `provenance-replay-counterfactual`、`abm-methodology`、`complex-systems-emergence`、`writing-records-memory`（简报）；`causality-bookkeeping`、`emergence-verifiability`、`computational-feasibility`、`pseudo-simulation`（红队）；另引用 `mandate-contradictions`、`llm-storytelling`。
- **证据等级约定**: A=多来源实证且有量化参数；B=理论共识但量化弱；C=有实质争议或单一来源；D=无来源、我们自己的假设。
- **引用格式**: `brief-slug §小节` / `critique-slug F编号`。凡本文自创而简报与红队都未写过的，一律标 **【本文原创，无来源，D 级】**。

---

## 0. 一句话主张

**不保存因果，保存可重算性；因果是从可重算性上按需测量出来的，而每一次测量都必须自带零分布、功效、视界和拒答权。**

由此推出本规格的三条骨架：
1. **L0 确定性基底**（比特级、内容寻址、无状态随机）是唯一必须在写代码前定死的东西；它一旦错，18 个月后所有因果结论作废且无法回改。
2. **因果图不是被写入的，是被重放测量出来的**；内核里不存在 `emit_event()`、不存在 `causes[]` 字段、不存在事件类型字符串。
3. **归因报告的默认答案是"不可归因"**，可归因率的健康区间是 15%–45%；超过 60% 是警报而不是成就。

---

## 1. 十一条硬冲突的裁决总表

| # | 冲突 | 裁决 | 详见 |
|---|---|---|---|
| 1 | 写入级 provenance vs 重算架构 vs 读取集追踪 | **四档混合**：Tier-D 静态读签名（永远开，零成本）+ Tier-R 按需重放（默认）+ Tier-S 抽样哨兵（10⁻³，0.5 GB/跑，只做一致性金丝雀）+ Tier-A 审计全量（玩具世界与短跑）。写入级全量 provenance **否决**。参考线 ≈ 12 GB，200 条集合 ≈ 273 GB。 | §3 |
| 2 | 第 2 条（可追溯）vs 第 3 条（强路径依赖） | 两者由**同一条实测曲线** `R_Y(Δ) = median D_placebo(Δ) / median D_indep(Δ)` 同时打分，数学上不可能都满分。因果视界 `H_Y(t)` 定义为 `R_Y` 逼近 1 的 Δ。**「不可归因」是一等返回值**，可归因率健康区间 ρ ∈ [0.15, 0.45]。 | §7 |
| 3 | 安慰剂对照 | 强制。安慰剂 = 同 tick、同机制类、同算子、同幅度、可比分层位置的**另一个抽样点**，M=100。CBRNG 下"推进一个没人用的流"是**退化零分布**（D ≡ 0），它是零干预测试而不是对照。 | §7.2 |
| 4 | 慢变量 | **Event / Channel 双节点模型**。Channel 由 `(变量 id, 窗口)` 定义，**不需要阈值**。四种干预 clamp/detrend/shuffle_time/resample_process 各有闭枚举的修复规则与强制偏置声明，**四种必须全跑全报**；不一致时的正确结论是 `MODALLY_AMBIGUOUS`。 | §4 |
| 5 | 缺席因 | `DrawSite` 是一等公民（不落盘，重算即得）；`fired == false ∧ p ≥ p_min` 的抽样点构成近失账本。追加区分 `STRUCTURAL_ZERO`（连评估机会都没有）与 `UNMODELED`（不在机制库里，永久不可修补）。T18 自我反驳：给出五条缓解（访问分级 + 访问日志强制引用 + 参数冻结点 + 近失回流率 + 分类账），并**承认通道未关闭**。 | §6 |
| 6 | 归因无客观总序 | 返回**归因报告**（不是排序）：N_eff、归因熵、OD、(PN,PS) 二维、最小充分前因集族、必然性剖面 p̂(Δ)、因果视界及 CI、超视界声明、账本穿越计数、常驻未建模声明。**N_eff > 2k 时 UI 硬拒绝显示 top-k**。 | §8 |
| 7 | 事件产生方式 | 禁止 `emit_event()`。`significance(τ) = Σ_Δ ω(Δ)·E[d(X⁺, X⁻)] / σ_ref(Δ)`，只由状态变化量算，与类型完全解耦。**双提名器**（下游散度型 + 信息瓶颈型）必须并跑并报重叠度。**提名延迟至 Δ_max = 200 年**，在重算架构下成本为零。 | §5 |
| 8 | 分层 | L1 机械事实 / L2 因果分析（带 analyzer_version，可被推翻）/ L3 世内叙事（命题图，非文本）/ L4 作者层。**L2 与 L4 对内核与 agent 零可见性**，四道 CI 强制，含"L2 抹除后轨迹逐位不变"的二值检验。 | §9 |
| 9 | 快照/分叉/存储 | 内容寻址 + 写时复制 + 结构共享；世界线身份 = `H(world_seed, code_hash, param_hash, llm_ledger_hash, weights_hash, schema_version, lineage_class, parent_ref)`；`lineage_class` **进哈希**，使 lab 线在数据模型上不可能被改名为 canon。留存预算表见 §10.4；删除必须过三条断言，删失必须显式标 `CENSORED_BY_RETENTION`。 | §10 |
| 10 | 两个地基 CI 测试 | `T-ZERO` 零干预测试（三种 IDENTITY 形式全测，逐位、无容差）；`T-ISOLATION` 因果隔离测试（隔离陆域 A/B，对 A 任意干预，B 在 100 年内逐位相同）。后者顺带给信息边界一个机械定义：**agent 决策的可重算依赖闭包必须落在其传播可达锥内，可逐位验证**。 | §11 |
| 11 | 因果算力 | 一次严肃「为什么」= **1,100 CPU 小时 @ T_run=1h**，11,000 @ T_run=10h（推导见 §12.1）。算力分账 25% 模拟 / 50% 验证 / 20% 因果 / 5% 重算债务 → 每年可严肃回答 **~200 个（T_run=1h）或 ~20 个（T_run=10h）**。功效分析前置，超预算标 `UNANSWERABLE_COMPUTE`，**禁止用小 N 硬答**。 | §12 |

### 这一节禁止了什么

- 禁止把上表任何一条当成"建议"。它们是裁决；改动需要走与改机制相同的评审流程，并作废受影响的 L2 结论。
- 禁止在没有 §3 的四档划分下讨论"我们要不要记因果"——这个问题已经被裁决为"记什么、什么时候记、由谁验"三个子问题。
- 禁止在任何文档、UI、变量名里使用"因果**链**"这个词（`causality-bookkeeping` S7：链暗示单指针，会污染数据结构与全部直觉）。合法词汇：**归因报告**、**因果场**、**依赖闭包**。

---

## 2. L0 确定性基底（⛔ 写代码前必须冻结）

这一层是全部因果基础设施的地基。它不可事后补救：`computational-feasibility` C5 已列出全部不可逆决定，`causality-bookkeeping` F7 给出一个 18 个月后才会被发现的例子。

### 2.1 世界线身份

```rust
struct WorldLineId(H256);   // BLAKE3-256

fn world_line_id(m: &Manifest) -> WorldLineId {
    H256(canonical_cbor(&(
        m.world_seed,          // u256，由 §10.3 的规则产生，不得由人挑
        m.code_hash,           // 内核源码 + 依赖锁文件 + 编译器三元组 + 目标 ISA 的 Merkle 根
        m.param_hash,          // 全部自由参数的规范序列化（含 D 级参数的 evidence_level 标注）
        m.llm_ledger_hash,     // 冻结账本根哈希；无 LLM 时 = H(∅)
        m.weights_hash,        // 本地权重指纹；托管 API 时 = (api_version_string, NOT_RECOMPUTABLE 标志)
        m.schema_version,      // u32
        m.view_render_spec_hash, // ⚠ View 数值渲染精度与粗化函数的哈希，见 §2.7
        m.lineage_class,       // Canon | Lab | CalibrationOnly | Toy —— 进哈希
        m.parent_ref,          // Option<(WorldLineId, fork_tick, intervention_spec_hash)>
    )))
}
```

**`lineage_class` 进身份哈希** 是本文的关键做法：把 `pseudo-simulation` F5.2 的"单向阀"从一条纪律变成一条数据模型约束。一条 lab 线若被改标为 canon，它的 `WorldLineId` 就变了，所有指向它的引用（快照根、L2 报告、登记表条目）立刻断链。**【本文原创，无来源，D 级】**

**`view_render_spec_hash` 进身份哈希** 回应 `llm-storytelling` F4 第三层：prompt 的数值渲染精度控制着蝴蝶效应速率，而它通常是某人随手写的 `f"{x:.1f}"`。把它变成世界线身份的一部分，意味着改精度 = 换世界，不可能悄悄发生。**【本文原创，无来源，D 级】**

### 2.2 随机数：CBRNG 坐标寻址

采用 `abm-methodology` M4 / `provenance-replay-counterfactual` M2 的方案（CBRNG 性质本身 A 级，Salmon et al. 2011, SC'11, doi:10.1145/2063384.2063405；本项目的具体布局 B/D 级）。

```
key     = Threefry4x64_key( world_seed , H64(stream_namespace) )
counter = (tick: u32 , entity_key: u64 , purpose_id: u16 , draw_index: u16)
bits    = Threefry4x64_20(counter, key)
```

- `stream_namespace` 是编译期常量路径（`"climate/precip"`、`"demog/birth"`、`"analysis/placebo"`…），由 `H64` 固定哈希，**禁止使用语言内置 `hash()`**（`provenance-replay-counterfactual` §8.8）。
- `entity_key` = 实体内容寻址 id 的低 64 位折叠（见 §2.3）。
- **`analysis/*` 命名空间与世界命名空间不相交**：分析用的随机（安慰剂选点、bootstrap、随机重启）永不与世界共享 counter 空间。

### 2.3 实体 id：血缘/内容派生哈希（⛔ 最不可逆的一条）

```
child_id      = H128(mother_id, father_id, birth_tick, birth_order_within_mother)
settlement_id = H128(cell_id, founding_tick, founder_lineage_id)
org_id        = H128(founder_id, founding_tick, charter_content_hash)
edge_id       = H128(min(a,b), max(a,b), edge_kind, first_tick)
```

**禁止任何全局自增计数器参与 id 分配**（`causality-bookkeeping` F7）。理由：抑制远洋孤岛上的一次生育 → 全局计数器少加 1 → 此后全世界每个新生者拿到不同 id → counter 全变 → 三年内整片大陆不同。这个 bug 与真实路径依赖在**任何宏观观测量上都不可区分**，我们会把它写进论文当成路径依赖。

碰撞策略：`H128` 冲突时按 `(id, disambiguator)` 扩展，`disambiguator` 从 0 递增；冲突事件写入 `L1_collision_log` 并计入 CI 指标（应恒为 0；非 0 说明 id 构造式的输入不足以唯一确定实体）。

### 2.4 离散决策：Gumbel-max，禁止逆变换采样（⛔）

```
Y = argmax_j { log p_j + g_j } ,  g_j = -log(-log u_j) ,  u_j = CBRNG(counter ⊕ j)
```

理由（`provenance-replay-counterfactual` §2.7，A 级）：Oberst & Sontag (ICML 2019, PMLR 97:4881–4890) 给出反例，**不同的分支枚举顺序 `ord` 给出完全相同的观测分布与干预分布，却给出不同的反事实**，且"there is no way to distinguish between these mechanisms with data"。也就是说 `if u < cumsum` 这一行里"你把哪个结果写在前面"是一条**不可检验的因果假设**。Gumbel-max SCM 满足反事实稳定性（该文 Theorem 2）。

代价：每次离散抽样生成 k 个 Gumbel 而非 1 个均匀数。按 Threefry4x64-12 的 1.1 cycles/byte（同表 A 级）与年 tick 的抽样频率，可忽略。

**推论（必须写进 spec-llm 的接口要求）**：LLM 决策点若只输出"选了哪一个"，abduction 无法进行（`llm-storytelling` F4 第三层）。**LLM 必须输出规则给定候选集上的分布 `p_LLM`，由我们的 CBRNG 用 Gumbel-max 采样**，否则该决策点在因果上是一个识别洞。

### 2.5 数值：定点整数（⛔）

- 所有进入世界状态的量用 `i64` 定点（标度在 schema 里声明，如 kcal 以 1、人口以 10⁻³ 人、货币以 10⁻⁶ 单位）。加法严格结合，归约顺序无关。
- 浮点只允许出现在**不回写世界状态**的中间量与诊断输出里，且写回前必须量化到定点。
- 若某处证明必须用浮点：固定 IEEE 754 binary64、禁 FMA 收缩、禁 `-ffast-math`、并行归约用可重现求和（Demmel & Nguyen 2015, IEEE TC 64(7):2060–2070；转引自 `provenance-replay-counterfactual` §2.5，A 级），并把该处登记进"已知浮点点"清单，清单长度只允许下降。

依据强度：`computational-feasibility` F2 本机实测——同一组 10⁵ 随机数，顺序/逆序/成对/分块求和相对差 ≈ 1.2×10⁻¹⁶；用 logistic map (r=3.9) 代表正 Lyapunov 动力学，**约 60 步后 1 ULP 放大到 O(1)**，而我们要跑 3,000 步。

### 2.6 调度、相位与平局打破

- tick 内相位固定：`observe → decide → resolve → commit → record`，跨相位不得读写穿越；`decide` 只读 `observe` 快照，只写提案队列（`abm-methodology` M5）。
- 相位内实体处理顺序：显式确定性键 `(phase_id, entity_content_id)` 或 `CBRNG(tick,"activation_order",entity_id)` 的可复现置换。**禁止依赖容器自然遍历顺序。**
- **所有 `max` / `argmax` / 排序在键相等时必须回退到确定性 tiebreaker**（推荐实体内容寻址 id 的字典序），且 tiebreaker 是模型规格的一部分。依据：Edmonds & Hales 2003 *JASSS* 6(4) 的血泪教训——两个独立重实现与原模型的实质性差异，根源就是锦标赛选择的平局打破规则（`provenance-replay-counterfactual` §2.12，A 级）。
- 相位顺序是 spec 的一等公民，改它要走与改机制相同的评审流程（`computational-feasibility` S6.5；`emergence-verifiability` §6.16 引 Kehoe 2016 对 Sugarscape 的形式化）。

### 2.7 抽样点 `DrawSite`：一等公民，零存储

```rust
struct DrawSite {                  // 不落盘。counter 的纯函数，重算即得。
    counter: (u32 /*tick*/, u64 /*entity_key*/, u16 /*purpose_id*/, u16 /*draw_index*/),
    stream_ns: u16,
    dist: DistSpec,                // 分布族 id（闭枚举）+ 定点参数；是状态的纯函数
    u: I64F0,                      // 抽到的分位（定点）
    gumbel: Option<[I64F0; K]>,    // 离散决策时的 k 个 Gumbel
    threshold: Option<I64F0>,
    outcome: OutcomeRef,
    fired: bool,
    p_fire: I64F0,                 // 该抽样点触发的概率（分布 + 阈值的纯函数）
}
```

**这一条是必然性剖面（§8.2）与近失账本（§6）的共同前提，且在重算架构下边际存储成本为零**（`causality-bookkeeping` F6.1）。落盘的只有 `--emit-draws` 模式下被显式请求的窗口。

### 2.8 世界哈希金丝雀

每 K=1 tick（主时钟=年，故每年）计算一次世界状态的 Merkle 根 `world_merkle_root(t)`，只保留根（32 B × 3,000 = 96 KB/线）。重放时逐 tick 比对，不匹配立即定位到单个 tick（`provenance-replay-counterfactual` M6.6 建议 K=12 月步；我们主时钟为年，取 K=1）。

### 这一节禁止了什么

- **禁止全局自增计数器分配任何实体 id。** 这不是风格问题：它会伪装成路径依赖，并让全部反事实结论静默失效。
- **禁止逆变换采样（`if u < cumsum`）做任何离散决策。** 它把不可检验的因果假设藏进分支枚举顺序。
- **禁止浮点进入世界状态**，除非登记进"已知浮点点"清单。
- **禁止有状态 PRNG、禁止单一全局随机流、禁止用可变量做种子**（`seed = hash(entity) ^ population` / `time.time()` / `len(agents)`，`provenance-replay-counterfactual` §8.5–8.6）。
- **禁止依赖哈希容器遍历顺序，禁止无显式 tiebreaker 的 argmax。**
- **禁止在长跑期间热更新内核。** 机制变更 ⇒ 该世界线作废，必须从 t=0 重跑（`mandate-contradictions` F9.2）。只有 L2/L4 分析器允许热更新（并同样记录版本）。
- **禁止 LLM 只输出单点选择。** 单点选择使 Gumbel-max abduction 失效、熵不可观测、污染指标单边（`llm-storytelling` F5）。

---

## 3. 冲突（1）的裁决：四档混合记账，与存储量级

### 3.1 为什么这是一个假三选一

三份红队各自主张的其实是三件不同的事：

| 主张 | 出处 | 真正的内容 | 我的裁决 |
|---|---|---|---|
| 放弃写入级 provenance，改重算 | `causality-bookkeeping` F2 | 存储与认识论：TB 级 + 自报即伪造 | **采纳为默认架构** |
| 读取集追踪（2–10× 开销） | `pseudo-simulation` F3 | **反作弊器**：`declared_causes(e) \ read_set_closure(e)` 必须为空 | **降级**：见下 |
| 有界读取集（≤64 项，变量级而非实例级） | `computational-feasibility` F3.1 | 常数尺寸的**候选集生成器** | **升格为静态签名，永远开** |

关键观察：**`pseudo-simulation` F3 的反作弊器，在"禁止手写 `emit_event()`、schema 里根本没有 `causes[]` 字段"（§5 与 §4.1）的前提下，没有东西可查。** 它的真正价值转移到另一处：**机械依赖闭包是候选原因集的唯一合法生成规则**（`causality-bookkeeping` F4.3 要求候选集"必须是机械的，不能手挑"）。

于是读取集从"永远开的写入级记账"降级为"两个不同粒度的产物"：一个是编译期的、变量级的、零成本的**静态读签名**；一个是按需重放时打开的、实例级的**taint 追踪**。

### 3.2 四档

**Tier-D 静态读签名（永远开，运行时零成本）**

每个机制在编译期声明它可能读/可能写的字段集合：

```rust
#[mechanism(id = 0x0041, version = "…")]
#[reads(Cell::soil_fert, Cell::stock_grain, Cohort::size, Cohort::age_bucket)]
#[writes(Cohort::size, Cell::stock_grain)]
#[draws(ns = "demog/mortality", purposes = [0x01, 0x02])]
fn m_starvation_mortality(ctx: &mut Ctx) { … }
```

- 类型是 `(entity_kind, field_id)`，**不是** `(entity_kind, entity_id, field_id)`。总条目数 10²–10³，几 KB。
- **CI 强制**：运行时访问签名之外的字段 = 硬失败（读屏障在内核里，不是外挂——`provenance-replay-counterfactual` §8.18）。
- 产物：一张**变量级依赖图** `G_static`。它回答"粮价**有没有可能**影响叛乱"（是/否），不回答"这一次影响了多少"。它是候选集生成规则的骨架，也是 §11.2 信息边界检验的静态部分。
- 认识论地位：这是**过近似**（`causality-bookkeeping` F2(b) 的短路求值与 `max(a,b)` 问题），且它不是"程序员认为的原因"，而是"编译器能证明的可能读取"。这个区别是本档存在的全部理由。

**Tier-R 按需重放 + taint（默认路径）**

- 常态下**不记录任何因果边**。存储 = §10.4 的留存预算表。
- 需要某个转移的实例级读取集时：从最近锚点重放该窗口，编译开关 `--taint` 打开动态数据流追踪。
- 开销：`causality-bookkeeping` T1 引用的软件级动态数据流追踪常见报告为 2–20×（该文标 `[记忆，未核实，必须自测]`）；`provenance-replay-counterfactual` §2.5 给出的全系统溯源捕获实测锚点是 2%–22%（CamFlow, Pasquier et al. SoCC'17，A 级），但明确指出**不能外推到内核内部逐决策记因果边**。**⚠ 本项目必须自测这个数，它是 §12 预算表里唯一没有实测锚点的乘数。**
- 窗口有界：单 tick 到数十年。跨越 3,000 年的闭包**不存在**，因为 `computational-feasibility` F3 的表已证明 `b^d` 在 d=8、b=10 时就到 10⁸。

**Tier-S 抽样哨兵（永远开，0.5 GB/跑）**

这是我给 `pseudo-simulation` F3 的让步，也是四档里唯一一个"永远在写"的档。它的唯一职责是**验证 Tier-R 的重放路径本身没有静默漂移**。

```rust
struct SentinelReadSet {           // 采样率 σ_s = 1e-3（定点，由 CBRNG("analysis/sentinel") 决定，可复现）
    tick: u32,
    site: SiteRef,                 // 12 B
    mechanism_id: u16,
    entries: BoundedVec<(u8 /*kind*/, u64 /*entity_key*/, u16 /*field*/), 64>,  // 实例级，≤64 项
    write_set_root: H64,
    draw_counters: BoundedVec<u32, 8>,
}
```

- CI（每次里程碑）：随机抽 10³ 条哨兵记录，用 Tier-R 重放同一窗口重算读取集，**要求逐条集合相等**。不等 = taint 机制或重放有 bug，构建失败。
- **它不是因果数据库。** 它没有权重、没有排序、不进任何归因报告。任何试图从哨兵表生成 top-k 的代码路径在 CI 里被禁（类型上 `SentinelReadSet` 不实现 `Into<CauseEntry>`）。

**Tier-A 审计全量（只在三处开）**

(a) 玩具标定世界 `W_cal`（§13.1）；(b) `--audit` 短跑（500 模拟年）；(c) 一次归因作业显式请求的 ≤10² 个窗口。

### 3.3 存储量级估算（算术公开，输入假设按来源标级）

假设集 A（沿用 `computational-feasibility` §8 的签字预算表；**该表自标全部百分比与实体上限为 D 级**）：主格 25 km 六边形 19,200 格 × 40 动态字段；人口队列 2,000 单元 × 200 桶；个体层 ≤3×10⁴ × 100 字段；聚落 ≤5,000；网络边 ≤3×10⁶；主时钟=年，3,000 tick。

**全量状态一张快照**：

```
格点     19,200 × 40  × 8 B =   6.1 MB
队列      2,000 × 200 × 8 B =   3.2 MB
个体      3e4   × 100 × 8 B =  24.0 MB
聚落      5,000 × 200 × 8 B =   8.0 MB
网络边    3e6         × 12 B =  36.0 MB
制度/文化/L3 命题图（10× 放大占位）≈ 100 MB
------------------------------------------------
裸尺寸 ≈ 177 MB   →  列式 + zstd 取 3×  →  ≈ 60 MB/张
```

**被否决的方案：写入级 provenance**

```
写次数/年 = 格点 19,200×40=7.68e5
          + 队列 2,000×200=4.0e5
          + 个体 3e4×20  =6.0e5
          + 聚落 5,000×10=5.0e4
          + 边   3e6×2%  =6.0e4
          ≈ 1.88e6 次写 / 模拟年
3,000 年 → 5.6e9 次写
每条边 34 B（8 目标 + 3×8 父指针 + 4 tick + 2 机制）→ 190 GB 裸
索引 ×1.5–3 → 285–570 GB / 单跑
```

换成 `causality-bookkeeping` F2(a) 的假设集（10⁵ 活跃个体、1.1×10⁵ 格）写次数 ×8.5 → **1.6–4.8 TB/跑**，与该文报的 1–3 TB 量级一致。乘 `abm-methodology` M7 的 N ≥ 50 涌现认证 → **14–240 TB**，且不含任何反事实分叉。

**采纳方案的账**：见 §10.4 留存预算表。参考线 ≈ 12 GB（不含分叉格）/ ≈ 24 GB（含），200 条集合 ≈ **273 GB**。

**比值：273 GB vs 14–240 TB = 1/51 到 1/880。**

### 3.4 为什么不能只选纯重算，也不能只选读取集

- 纯重算的盲点：如果 taint 机制本身有 bug，或重放路径与原跑有一位偏差，**我们永远不会知道**——因为没有独立记录可比对。Tier-S 哨兵以 0.5 GB 的代价买下这个金丝雀。
- 纯读取集的盲点：`causality-bookkeeping` F2(b) 的**欠近似**是致命的——缺席因不产生读取、不产生写入、不产生任何一条 provenance 边，而"什么没有发生"是历史解释的主干。只有重算架构能重建近失账本（§6）。
- 三个独立理由支持重算架构（全部来自 `causality-bookkeeping`）：能表示缺席因（F2.2）、能事后追加慢变量与提名器（F3.2 / S3.2）、只有一个真相源不会漂移（S8）。**我追加第四个**：延迟提名（§5.3）在写入级架构下不可行，因为它要求在事件发生时预判它未来是否重要——那是不可能的要求，而启发式代替它就是剧情树回流（F2(a) 明确指出的死结）。**这个死结在重算架构下自动消解**，因为提名锚点可以事后由重放生成，成本 ≤25 年重放 ≈ 0.008 CPU 小时。

### 这一节禁止了什么

- **禁止任何"写状态时同时写因果边"的代码路径。** 两个写路径必然漂移，而因果库的错误极难发现（`causality-bookkeeping` S8）。
- **禁止 schema 里存在自报的因果字段**：`causes[]`、`reason`、`structural_prior_weight`、`sigma_declared` 一律不存在。字段不存在比"约定不使用"强（`emergence-verifiability` §6.2）。
- **禁止把 Tier-S 哨兵表用于任何归因、排序、展示。** 类型层隔离。
- **禁止把 Tier-D 静态签名的闭包称为"原因"。** 它的 UI 文案强制为"可能被读取的量"，`evidence_kind = MECHANICAL`，无权重。
- **禁止在没有实测 taint 开销之前把 §12 的算力表当作已定。** 那个乘数是当前唯一无锚点的数。

---

## 4. 冲突（4）的裁决：Event / Channel 双节点因果模型

事件图无法表示"基尼系数 120 年从 0.41 漂到 0.72"（`causality-bookkeeping` F3）。把慢变量离散成事件（`if gini > 0.65: emit(...)`）有双重灾难：每条因果链的终点都停在我们亲手写下的数字上；且该语义对象一旦存在就会被下游机制引用，在结构上与手写剧情树无法区分。

### 4.1 Event 节点

```rust
struct Event {
    event_id: H128,          // = H(world_line_id, tick, phase, seq, write_set_root)
    world_line_id: WorldLineId,
    stt: (u32 /*tick*/, u8 /*phase*/, u32 /*seq*/),   // 全序，同时是拓扑序保证
    site: SiteRef,
    mechanism_id: u16,       // 闭枚举，代码常量
    mechanism_version: H64,
    write_set_root: H128,    // 该转移写入集的 Merkle 根
    draw_ref: Option<DrawSiteRef>,
    nominations: Vec<Nomination>,     // 见 §5
    schema_version: u32,
}

struct Nomination {
    nominator_id: u8,        // 0 = 下游散度型；1 = 信息瓶颈型
    nominator_version: u16,
    significance: I64F32,
    nominated_at_tick: u32,  // ≠ stt.tick —— 延迟提名
}
```

**Event 里没有的东西（schema 级禁止）**：`type: String`、`name`、`causes[]`、`importance_declared`、`parent_event_id`、`reason`、任何自由文本。

### 4.2 Channel 节点与慢变量注册表

```rust
struct Channel {
    channel_id: H128,        // = H(world_line_id, variable_id, scope, t0, t1, aggregator_id)
    variable_id: u16,        // 慢变量注册表条目
    scope: ScopeRef,         // Global | Region(id) | Polity(id) | Stratum(id)
    window: (u32, u32),
    digest: TrajectoryDigest,
    registry_version: u16,
}

struct TrajectoryDigest {
    n: u32,
    mean: I64F32, sd: I64F32,
    slope_ols: I64F32, slope_theil_sen: I64F32,
    ac1: I64F32, ac_decay_time: u32,      // 自相关衰减时标，决定 shuffle 的块长
    q05: I64F32, q25: I64F32, q50: I64F32, q75: I64F32, q95: I64F32,
    detrended_sd: I64F32,
    spectral_peak_period: Option<u32>,
    changepoints: Vec<(u32, I64F32)>,     // 固定的变点检测器算出，非人工
}
```

**Channel 不需要阈值。它由 `(变量, 窗口)` 定义。** 这是它相对"把慢变量事件化"的全部优势。

**窗口生成必须机械**（否则窗口就是新的阈值）：对一个目标事件 `e@t`，候选窗口 = 二进宿窗口 `[t−2^k, t]`（k=3..11，即 8…2048 年）∪ 由变点检测器切出的窗口。**禁止手挑窗口。**

**慢变量注册表 v0（⛔ Phase 0 交付物，允许事后追加）**

命名规则：**注册表条目名必须是状态泛函的机械描述，禁止使用任何历史学概念名**（`causality-bookkeeping` F3.4）。

| variable_id | 内部代号 | 定义（状态的纯函数） | 特征时标（D 级待标定） |
|---|---|---|---|
| 0x01 | `gini(holding_land \| scope)` | 地权持有量的基尼系数 | 100–300 y |
| 0x02 | `q90/q50(stock_grain \| cell)` | 粮储分位比 | 20–80 y |
| 0x03 | `frac(cohort.age≥60 \| scope)` | 老龄份额 | 50–150 y |
| 0x04 | `mean(cost_path_to_nearest_center)` | 到最近中心地的平均通行成本 | 100–500 y |
| 0x05 | `entropy(claim_variants \| proposition)` | 同一命题的世内变体熵（L3） | 50–200 y |
| 0x06 | `frac(edges_crossing_scope_boundary)` | 跨界关系边份额 | 50–200 y |
| 0x07 | `mean(oblig_load \| household)` | 家户义务负荷均值 | 30–120 y |
| 0x08 | `sd(yield \| cell, 30y window)` | 产量 30 年滚动方差 | 30–100 y |
| 0x09 | `frac(literate_practice_matrix nonzero)` | 识字实践矩阵非零率（`writing-records-memory` M12） | 200–800 y |
| 0x0A | `max_connected_component(control_edges)` | 控制关系最大连通分量规模 | 20–200 y |

**事后追加的机制**：新增一条 variable_id 只需要注册 + 递增 `registry_version`，然后**全部历史的因果分析可以重算，不需要重跑世界**——这是重算架构的第三个独立收益（`causality-bookkeeping` F3.2）。

### 4.3 对 Channel 的四种干预：修复规则与偏置声明

干预连续慢变量必然遇到"修复不变量"问题：把地权分布钉在 t0 的值上，那 120 年里实际发生的每一笔土地交易的地要放到哪里去？**每一个修复规则都是一个建模选择，并且它会把偏置直接注入因果结论**（`causality-bookkeeping` F3 路 B）。

修复规则是**闭枚举**，不是自由函数：

```rust
enum ChannelRepair {
    Proportional,       // 按原比例重标定底层原语向量，保总量、保秩序
    MarginalTransfer,   // 从尾部搬运最小质量，保总量、不保秩序
    ExogenousSink,      // 允许总量变化，差额记入 intervention_sink 账户（显式违反守恒）
}
```

| 干预 | 定义 | 允许的修复 | **强制偏置声明（打印在报告上，不可省）** |
|---|---|---|---|
| `clamp(v, c, W, repair)` | 在 W 上把 v 钉在常数 c | 三种全可 | `Proportional` 等于在反事实世界里偷偷执行了一次连续再分配，会**高估**该慢变量的因果作用；`MarginalTransfer` 把反事实集中在尾部，会**高估尾部机制**；`ExogenousSink` 违反守恒，报告必须打印 `mass_created` / `mass_destroyed`。 |
| `detrend(v, W, method)` | 去趋势保波动。method ∈ {linear_ols, theil_sen, loess(span)} | 三种全可 | 保留短期冲击 ⇒ 相对 clamp **低估**慢漂移的作用；它回答的是"如果水平不变但起伏照旧"。 |
| `shuffle_time(v, W, block)` | 保边际分布、打乱时序。块长 = `digest.ac_decay_time` | 三种全可 | 同时摧毁趋势与长记忆 ⇒ **高估"时序本身"的作用**。对应 `abm-methodology` M6 的外生序列置换检验。 |
| `resample_process(v, W, surrogate)` | 同边际分布同自相关的替代序列（IAAFT / 相位随机化） | 三种全可 | 保留功率谱 ⇒ 若因果通过低频功率起作用，效应会被**保留**，故这是四者中**最保守**的一个，效应量通常最小。 |

**硬规则：四种必须全跑、全报，且必须报同一个 `repair` 下的四值。** 若四值的 max/min > 3×（D 级待标定），报告的 channel 判决是 `MODALLY_AMBIGUOUS`，并逐字打印：

> 该慢变量的因果作用取决于我们如何设想它不发生。四种反事实构造给出 {…} 四个效应量，我们没有裁决办法。

这是一个真实的、诚实的结论，不是 bug（`causality-bookkeeping` F3.3 / T4）。

**合法性检查器（每次干预后强制运行）**：

```
legal(intervention) :=
    conserved(population) ∧ conserved(land_area) ∧ conserved(matter_by_kind)
  ∧ nonneg(all stocks) ∧ within_bounds(all fractions)
  ∧ no_orphan_edges ∧ no_time_travel(all wvt intervals)
  ∧ (repair == ExogenousSink ⟹ sink_account_balanced)
非法 ⇒ 干预被拒绝（ILLEGAL），不得"静默修好后继续"。
```

### 4.4 干预代数（完整闭枚举，⛔ 写代码前必须定死）

```rust
enum Intervention {
    Identity(IdentityKind),                                  // §11.1 的三种
    FlipDraw { site: DrawSiteRef, to_u: I64F0 },             // 只改分位，counter 不变
    ForceDraw { site: DrawSiteRef, outcome: OutcomeRef },
    SuppressEvent { event: EventRef, repair: EventRepair },  // 事件不发生 + 修复
    ForceEvent { template: EventTemplate, repair: EventRepair },
    ClampChannel { ch: ChannelRef, to: I64F32, repair: ChannelRepair },
    DetrendChannel { ch: ChannelRef, method: DetrendMethod, repair: ChannelRepair },
    ShuffleChannel { ch: ChannelRef, block: u32, repair: ChannelRepair },
    ResampleChannel { ch: ChannelRef, surrogate: SurrogateSpec, repair: ChannelRepair },
    ReseedStream { ns: u16, new_key: H128 },                 // ⚠ 这是"换世界"不是"改事实"，见下
    Placebo { of: Box<Intervention>, alt_site: SiteRef },    // §7.2
}
```

**`ReseedStream` 与 `do(·)` 是两件不同的事**（`causality-bookkeeping` C4）：换种子 = 换整条抽样实现 = 得到"同分布的另一个世界"；do-干预 = 在同一世界里改一个事实。**API 层强制分离**：`ReseedStream` 只能出现在 `NecessityProfile` 与 `IndependentBaseline` 两类作业里，**不得**出现在任何 `AttributionJob` 的处理臂里。类型层拒绝。

**`intervention_spec` 必须是结构化的、可复算的**；**禁止用自由文本描述干预**（`provenance-replay-counterfactual` M7）。`intervention_spec_hash` 进世界线身份（§2.1）。

### 这一节禁止了什么

- **禁止任何 `if 慢变量 > 常数 then 语义事件` 的内核代码。** 静态检查：内核层不得引用任何以人类历史学概念命名的符号；慢变量注册表条目名必须是泛函描述式。
- **禁止内核读取任何 Channel 对象。** Channel 是 L2 对象（§9），内核对它零可见性。
- **禁止手挑 Channel 窗口。**
- **禁止只报四种干预中的一种或"取平均"。** 平均掉模态含混就是抹掉真实结论。
- **禁止自由形式的修复函数。** 修复规则是三元闭枚举，新增需要 schema 版本升级 + 一段偏置声明文本 + 在 `W_cal`（§13.1）上的解析校验。
- **禁止把 `ReseedStream` 当作反事实干预使用。**
- **禁止在合法性检查失败后"自动修复并继续"。** 非法干预必须失败并报告为什么。

### 这一节没解决什么

`Proportional` 与 `MarginalTransfer` 之间没有原则性的裁决依据。我们能做的只有全报 + 声明方向。这是 `causality-bookkeeping` T4 明确接受的代价，本规格照单接受。

---

## 5. 冲突（7）的裁决：事件由重大性泛函自动提名

`causality-bookkeeping` S3：内核每年做 10⁷ 次状态转移，谁来命名"事件"？默认是写机制的人顺手加一行 `emit_event("battle", …)`。于是**因果图的形状 = 我们注意力的形状 = 我们的历史观**，而这是一个完美闭环的偏见。`emergence-verifiability` F4 从另一侧指出："重大事件"未定义 ⇒ 第 2 条不可执行也不可证伪。

### 5.1 `significance(τ)` 的可计算定义（语义无关）

对 tick `t` 的一个转移 `τ`（写入集 `W(τ)`）：

$$
\mathrm{sig}(\tau) \;=\; \sum_{\Delta \in G} \omega(\Delta)\cdot
\frac{\hat{\mathbb{E}}\big[\, d\big(X_{t+\Delta}^{\,\text{with}\,\tau},\; X_{t+\Delta}^{\,\text{without}\,\tau}\big) \,\big]}
     {\sigma_{\mathrm{ref}}(t,\Delta,\mathrm{stratum}(\tau))}
$$

- `G = {10, 50, 200}` 模拟年，`ω = (0.2, 0.3, 0.5)`（**D 级待标定**；权重偏向长视界，这正是"边境小冲突 80 年后才被提名"的形式化）。
- `d(·,·)` 是**机械导出的全状态距离**：

$$
d(X, X') = \sum_{\ell \in \text{layers}} w_\ell \cdot \frac{1}{|F_\ell|}\sum_{f \in F_\ell} \frac{\lVert X_f - X'_f\rVert_1}{\sigma_f}
$$

  - `layers` = state schema 的顶层结构划分（格点 / 队列 / 个体 / 聚落 / 边 / 制度 / L3 命题图），**由 schema 反射机械导出，禁止手工挑选通道**（`pseudo-simulation` S4 的缓解条款：通道集必须由 state schema 机械导出）。
  - `σ_f` = 该字段在参考线上的跨 tick 标准差。
  - `w_ℓ` = 等权（1/|layers|）。**这是一个已知的自由度**：加权方式会改变提名集。缓解：`sig` 必须在三种加权（每字段等权 / 每层等权 / 每字节等权）下各算一次，报告提名集的 Jaccard；若三者 J < 0.5 则"重大性"对加权敏感，必须在报告里声明（**【本文原创，无来源，D 级】**）。
- `σ_ref(t, Δ, stratum)` = 同 tick、同分层的**安慰剂集合**（§7.2）在 Δ 处的散度中位数。这一步让 `sig` 变成**尺度无关的、相对于"这个时间这个位置的同类扰动通常造成多大后果"的比值**，而不是一个原始数字。它也是 §7 与 §5 共用同一批算力的接口点。

**这个定义里没有任何事件类型词、没有任何历史学概念、没有任何阈值常数。** 它只由状态变化量与安慰剂零分布算。

### 5.2 两个提名器（必须并跑并报重叠度）

逐转移地真跑反事实是不可能的（10⁶/年 × 3 重放）。`sig` 因此由**两个不同失效模式的估计器**近似，二者都从共享分叉格（§7.1）标定：

**提名器 0 — 下游散度回归型**

在分叉格上我们已经测得每个 `(t, stratum, mechanism_class)` 的散度分布。对单个转移，用一个回归器预测 `sig`，特征为：

```
x1 = |W(τ)| 归一化写入幅度（Σ_f |Δ|/σ_f）
x2 = 被写实体在交互图上的度（入度 + 出度）
x3 = 该 (t, stratum) 的局部散度率（分叉格实测）
x4 = 下游机制中读签名包含 W(τ) 字段的机制占比（Tier-D 静态签名导出）
x5 = 被写字段的 σ_f 排名分位
x6 = 到最近提名事件的通行成本
```

⛔ **特征向量禁止包含 `mechanism_id`、`entity_kind`、`field_id` 作为类别变量**，只允许它们机械导出的数值属性。否则提名器会学会"战争类机制重要"，本体又从后门进来。CI：提名器的特征规格文件是版本化工件，含类别变量即构建失败。**【本文原创，无来源，D 级】**

**提名器 1 — 信息瓶颈型**

$$\mathrm{sig}_{\mathrm{IB}}(\tau) = \hat{I}\big(W(\tau)\,;\, M_{t+\Delta}\big)$$

`M` 是粗化的宏观状态向量（分箱），互信息在分叉格集合上估计。与提名器 0 的失效模式不同（前者对"大写入但被吸收"敏感，后者对"小写入但决定分支"敏感）。

**提名规则**：`τ` 被提名 ⟺ `sig_0(τ) > θ_0` ∨ `sig_IB(τ) > θ_IB`，其中 **θ 由配额定义而非绝对值**：θ = 使提名率等于预算的分位点。默认预算 **500 提名事件 / 模拟年**（D 级；由 §10.4 的 0.45 GB 索引预算反推）。这样 `sig` 只被**序数地**使用，避免"我们挑了 0.65"。

**重叠度必须报告**（`causality-bookkeeping` S3.3）：`J = Jaccard(提名集_0, 提名集_1)`。健康区间 **J ∈ [0.3, 0.8]（D 级待标定）**。`J > 0.95` ⇒ 两个提名器是同一个东西，删一个。`J < 0.1` ⇒ "重大性"这个概念在我们世界里不稳定，**这本身是一个必须报告的发现**，且此后任何句子里出现"重大事件"必须同时点名提名器。

### 5.3 延迟提名与追认

- 提名是一个**批作业**，在覆盖 `[t, t+Δ_max]`（`Δ_max = 200` 年）的分叉格完成后运行。因此 `nominated_at_tick − stt.tick` 可以是 80 年、200 年。
- 提名锚点（§10.2）**事后生成**：从最近的 50 年主锚点重放 ≤25 年即可物化，成本 ≈ 0.008 CPU 小时。**这就是 `causality-bookkeeping` F2(a) 那个"必须在事件发生时预判它未来是否重要"死结的解**。
- 提名索引是**版本化派生工件**。更换提名器 ⇒ 全量重生成；`event_id` 因内容寻址而不变，但提名集变。任何引用了被撤销提名事件的 L2 报告自动标 `NOMINATOR_STALE`，进重算债务仪表盘。

### 5.4 与 σ(e) 刷分的关系

`complex-systems-emergence` M6 的 `σ(e) ≥ 0.5` 判据会被"多写几个结构变量"刷高（`causality-bookkeeping` S9，典型 Goodhart）。本规格的对策：

1. `σ` 必须与 `N_eff` 配对报告。σ 高 + `N_eff` 也高 = 稀释，不是深度。
2. **递归深度指标**：从事件出发沿实测因果边回溯直到遇到外生输入（气候、地形、初始禀赋）或超出视界，报告**跳数**与**路径上的平均 σ**。加协变量会抬高首跳 σ 但第二跳立刻触底，因此这个指标刷不高。
3. 协变量数量进受监控的复杂度预算（`emergence-verifiability` F15.3 的 |M| 上限的同一面）。

### 这一节禁止了什么

- **⛔ 禁止 `emit_event()` 存在。** CI 静态检查：符号 `emit_event` / `log_cause` / `mark_important` 在内核 crate 中不得出现（任何拼写）。内核只写状态。
- **禁止 `EventType` 枚举与效果函数库动词**（`found_state()`、`start_religion()`、`reform_bureaucracy()`）。事件是被检测出来的，不是被触发的（`pseudo-simulation` S4）。
- **禁止提名器的特征含类别型 `mechanism_id`/`entity_kind`/`field_id`。**
- **禁止用绝对阈值定义"重大"。** 阈值只能由配额分位点导出。
- **禁止只跑一个提名器。**
- **禁止在没有报告 J（重叠度）与三种加权 Jaccard 的情况下使用"重大事件"这个词。**
- **禁止内核 import 提名器/观察器模块**（构建期单向依赖检查，`emergence-verifiability` F5.2）。

---

## 6. 冲突（5）的裁决：缺席因与近失账本

"为什么这个国家灭亡"的真实答案里有巨大一块是缺席因：改革没有发生、援军没有到、那三年没有下雨、没有人发明出可用的冶铁法。**缺席不产生读取、不产生写入、不产生任何一条 provenance 边**（`causality-bookkeeping` F2(b)）。

### 6.1 三种缺席，两种可表示

| 种类 | 定义 | 可表示？ | 检测方式 |
|---|---|---|---|
| `NEAR_MISS` | 内核评估过概率、抽了样、没触发 | **是** | `DrawSite.fired == false ∧ p_fire ≥ p_min` |
| `STRUCTURAL_ZERO` | 机制的门控条件不满足，连抽样机会都没产生 | **是**【本文原创，无来源，D 级】 | 门控条件的求值本身是一次读取；重放时记录"机制 m 在 (site,t) 被调度但在门控处返回" |
| `UNMODELED` | 这种可能性根本不在机制库里 | **否，原理上不可修补** | 只能声明 |

`STRUCTURAL_ZERO` 是本规格相对 `causality-bookkeeping` F2.2 的一个实质追加：该文只提了近失账本。区分"评估过但没通过"与"连评估机会都没有"，让"为什么他们没有发明成文法"这类问题第一次有了两种不同的机械答案——前者是概率问题，后者是**前置条件问题**，而后者往往才是历史解释的真正落点。

### 6.2 数据结构

```rust
struct NearMissLedger {              // 存储代价 0：按需重放 --emit-draws 重建
    scope: ScopeRef,
    window: (u32, u32),
    mechanism_class: u16,
    sites: Vec<NearMissSite>,
    aggregate_p_at_least_once: I64F32,   // 1 − Π(1 − p_i)
    structural_zeros: Vec<StructuralZero>,
}
struct NearMissSite { tick: u32, site: SiteRef, p_fire: I64F32, u: I64F0, threshold: I64F0 }
struct StructuralZero { tick_range: (u32,u32), mechanism_id: u16, blocking_gate: u16, blocking_field: u16 }
```

在归因报告里它是一个一等 `CauseEntry`：

```
缺席因（NEAR_MISS）
  · 3055–3072 机制 0x0117（提案通过判定），三次评估：p = .11 / .19 / .07
    至少一次触发的概率 = 1 − (.89×.81×.93) = 0.330
    反事实：do(u := u' < threshold) 逐点强制触发，PN = 0.41 [0.31, 0.52], PS = 0.22 [0.14, 0.31]
缺席因（STRUCTURAL_ZERO）
  · 2980–3072 机制 0x0203（成文法典编纂）从未被评估：门控 `scribe_supply ≥ 3` 在全窗口为假
    反事实：do(scribe_supply := 3) 后该机制被评估 214 次，触发 6 次；PN = 0.07 [0.02, 0.15]
```

**近失点的反事实是"强制触发"而不是"删除"**——这是它与 Event 干预的对偶。

### 6.3 T18 的自我反驳：五条缓解，与残余风险

`causality-bookkeeping` T3/T18 的自我反驳：一旦我们能看到"改革提案在 1240、1263、1288 三次差点通过，概率 0.11/0.19/0.07"，我们就会忍不住去想"这个概率是不是太低了"。**近失账本把概率参数变成了一个我们能直接盯着看、并且有强烈动机去调的东西**，与 `pseudo-simulation` F2 的"人类回路梯度下降"是同一条通道，只是带宽更高。该文明说自己给的缓解不足够。

我给五条，并明确说明其中哪些是真的机械可执行的：

**(M1) 近失账本的三级访问分级（机械）**【本文原创，无来源，D 级】

| 模式 | 返回什么 | 门槛 |
|---|---|---|
| `aggregate` | 机制类级别的触发率与 p 分布直方图 | 无门槛。这是校准 hazard 参数**唯一被允许**的输入。 |
| `sited` | 具体 `(tick, site, p, u, threshold)` 元组 | **必须携带已预注册的 `analysis_job_id`**；工具在无 job_id 时拒绝执行。 |
| `narrative` | 渲染成"本可以…"的自然语言 | 只在 L4，且只对**已被预注册归因作业返回过**的近失点，禁止浏览式生成。 |

**(M2) 不可删除的访问日志 + 提交强制引用（机械，这是最硬的一条）**【本文原创，无来源，D 级】

`sited` 与 `narrative` 访问写入 append-only 日志 `(user, mechanism_id, scope, window, ts, job_id)`。**任何修改 hazard/rate 参数的提交，必须在提交信息里逐条引用该作者在此前 30 天内对该 mechanism_id 的全部 sited 访问日志条目。** 引用缺失或引用了无 job_id 的访问 ⇒ CI 失败。

它不阻止梯度下降，它**把梯度下降写进 git 历史**——而 `pseudo-simulation` §1 的判据表明，唯一能抓住 L4 人类回路失效的东西就是流程留痕，不是任何度量。

**(M3) 参数改动分类账 + 冻结点（沿用 `pseudo-simulation` F2 三件套）**

每个自由参数带 `change_log`，每次改动归入 `bug` / `evidence`（须附一手引文）/ `aesthetics` 三类之一。**任何被 `aesthetics` 改过 ≥2 次的参数，其下游一切宏观现象在文档中永久标注为"非涌现（拟合产物）"。** Phase 1 末冻结参数集；此后 hazard 参数只允许 `bug` 与 `evidence` 类改动，`aesthetics` 改动强制换 `param_hash` ⇒ 换世界线 ⇒ canon 作废。

**(M4) 参数漂移审计（机械）**：任一参数在滚动 90 天窗口内被**同方向**微调 ≥2 次 ⇒ CI 警报，并在里程碑评审首页列出。

**(M5) 近失回流率（新指标，机械）**【本文原创，无来源，D 级】

$$\text{回流率} = \frac{\#\{\text{hazard 参数提交} : \text{其 diff 方向会翻转该作者近 30 天 sited 查看过的某个近失点的结果}\}}{\#\{\text{hazard 参数提交}\}}$$

目标 ≈ 0。它上升 = 通道正在活跃。这个数进里程碑仪表盘第一页。

**残余风险（诚实声明，必须写进方法论声明与每份依赖缺席因的报告页脚）**

1. 以上五条**都不阻止**作者内化近失分布，然后在几个月后以一个看起来独立的、合理的理由做出同方向改动。通道只是被**放慢并变得可读**，没有被关闭。
2. (M1) 的分级可以被任何有文件系统访问权的人绕过，而我们都有。它防的是"顺手看一眼"，不是防蓄意。
3. 任何主要归因落在缺席因上的宏观结论，必须携带 `NEARMISS_DEPENDENT` 标志，并在展示时与该 mechanism_id 的参数 `change_log` 并列。
4. `UNMODELED` 类缺席因**永远不会出现在任何报告里**，而它恰恰是真实历史中最重要的一类原因之一（`causality-bookkeeping` §8.3）。这是不可修补的。

### 6.4 常驻页脚（不可删除的常量文本）

> 本报告只能表示内核评估过的机会（近失）与门控阻断的机会（结构性零）。世界里根本没有建模的可能性——"他们没有发明 X，因为我们的技术空间里没有 X"——永远不会出现在任何因果报告里。这在原理上不可修补。

CI：报告序列化器若不含该字段，构建失败。

### 这一节禁止了什么

- **禁止把近失点落盘。** 它们是重算产物。落盘会立刻把近失账本变成一个可浏览的、可优化的目标面。
- **禁止在无 `analysis_job_id` 的情况下取得 sited 近失数据。**
- **禁止修改 hazard 参数而不引用近失访问日志。**
- **禁止在归因报告里用"没有发生 X"作为原因而不区分 `NEAR_MISS` / `STRUCTURAL_ZERO` / `NOT_MODELED`。** 三值逻辑是刚需（`emergence-verifiability` F8.3 引 Beheim et al. 2021：把 61% 缺失重编码为"不存在"使 Whitehouse et al. 2019 *Nature* 的结论反转并导致撤稿）。
- **禁止删除常驻页脚。**

---

## 7. 冲突（2）（3）的裁决：安慰剂对照与因果视界

### 7.1 唯一的规模化原语：共享分叉格（Fork Lattice）

不要围绕"事件图"建基础设施，围绕**分叉格**建（`causality-bookkeeping` §7.3）。

```
分叉格 = { 分叉点 (t_f, region r) : t_f ∈ {50, 100, …, 3000}, r ∈ 主要区域 }
在每个分叉点跑三组：
  arm NULL      : n = 3   零干预（IDENTITY 三形式各一），必须 D ≡ 0     ← 正确性断言
  arm PLACEBO   : M = 100 同分层随机选点的同类型翻转                   ← 零分布
  arm INDEP     : n = 30  不同 world_seed 的独立世界线（同世代、同宏观分层）← 饱和上界
每组跑到 t_f + Δ_max（Δ_max = 500 年，或到 3000 年为止）
```

**同一批算力同时产出五样东西**（这是成本可行的唯一路径）：
1. 安慰剂零分布 `F_placebo(Δ)`（§7.2）
2. 独立基线 `F_indep(Δ)`（§7.3 的饱和参考）
3. 因果视界 `H_Y(t)`（§7.3）
4. 必然性剖面 `p̂(Δ)`（§8.2）
5. `sig` 的标定与提名（§5.2 的 `σ_ref` 与两个提名器的训练/估计集）

### 7.2 安慰剂的构造（强制）

**为什么 CBRNG 下"推进一个没人用的随机流"不能当安慰剂**（四层理由）：

1. **CBRNG 无状态**：随机数是 counter 的纯函数，不存在"游标"可以推进。`abm-methodology` M4 的整个设计目的就是消灭调用序号依赖。所以这个操作在 counter 空间里字面上不存在。
2. **写集为空**：抽取一个无人消费的比特串不改变任何状态 ⇒ 世界逐位不变 ⇒ `D ≡ 0`，且**方差为 0**。
3. **它是一个退化零分布**：任何真实干预相对它的分位恒为 1.0，于是**每一个干预都"显著"**，而这正是 `causality-bookkeeping` F5 描述的自欺形态——所有实验都成功，所有解释都成立，从不产生任何异常。
4. **它测的是别的东西**：`D ≡ 0` 是 §11.1 的零干预测试，一个**正确性**断言。把正确性测试当成统计对照，是把"我们的重放没坏"读成"这个原因很重要"。

**正确的安慰剂**：对真实干预 `I = (t, m, s, op, mag)`，安慰剂 `I' = (t, m, s', op, mag)`，其中 `s'` 从**安慰剂合格集** `E(I)` 均匀抽取：

```
E(I) = { s' : s' ≠ s
             ∧ cell(s') ≠ cell(s)
             ∧ tick(s') = t                              # 严格同 tick
             ∧ mechanism_class(s') = m                    # 同代码路径、同分布族
             ∧ 算子 op 与幅度 mag 可施加于 s'
                 （flip：同 |u − u'| 分位位移；clamp：同 |Δ|/σ_v）
             ∧ stratum(s') = stratum(s) }                 # 预注册分层，四维全匹配
stratum = ( terrain_class ,
            population_density_decile   ±1 ,
            network_centrality_decile   ±1 ,
            cost_distance_to_nearest_polity_center_decile ±1 )
M = 100 次抽取（D 级；功效见 §12.1）
抽取用 CBRNG 命名空间 "analysis/placebo"，key 由 analysis_job_id 决定 ⇒ 安慰剂集本身可复现、可预注册
```

对 Channel 干预，安慰剂是**另一条 Channel**，匹配 `(变量类, 窗口长度, |slope|/sd 分位, ac_decay_time 分位)`，并用同一个 `repair`。

**报告的统计量**：真实效应在零分布中的**分位** `q = F̂_placebo(D_real)`，以及该分位的 bootstrap 95% CI（对 M=100，分位的标准误约 `√(q(1−q)/M)`；q=0.95 时 ±0.043）。

**Schema 强制**：`CauseEntry.placebo_id` 为 `NOT NULL`。没有零分布的反事实结果**拒绝写入 L2**。

### 7.3 因果视界 `H_Y(t)` 的实测协议

`causality-bookkeeping` F1：第 2 条与第 3 条要求单点扰动响应曲线朝相反方向取值，且**两种情况我们都会解读成"成功"**。本规格的解法：让**同一条实测曲线**同时给两条原则打分，使"两个都满分"在算术上不可能。

**定义（本规格采用）**

设 `Y` 是可观测量注册表里的一个标量泛函，`D_Y(·,·)` 是它的预注册距离。令

$$
R_Y(t,\Delta) \;=\; \frac{\mathrm{median}\big[\, D_Y(\text{base},\ \text{placebo}_i)\big|_{t+\Delta} \,\big]}
                          {\mathrm{median}\big[\, D_Y(\text{base},\ \text{indep}_j)\big|_{t+\Delta} \,\big]}
\in [0, \sim 1]
$$

- `R_Y → 0`：一次同类单点扰动几乎没改变 Y ⇒ **第 3 条（路径依赖）在该观测量上不成立**。
- `R_Y → 1`：一次单点扰动把世界推得和"完全另一个种子"一样远 ⇒ **归因崩塌，第 2 条在该观测量上不成立**（不是稀释，是崩塌——因为翻转任何东西结果都变）。

$$
\boxed{\,H_Y(t) \;=\; \max\{\,\Delta \;:\; A_{12}\big(F_{\text{placebo}}(\Delta),\ F_{\text{indep}}(\Delta)\big) \le 0.5 - \delta \,\}\,}
$$

`A₁₂` 是共同语言效应量（随机取一个安慰剂样本小于随机取一个独立样本的概率）；`δ = 0.10`（**D 级待标定**）。含义：在 `H_Y` 之内，单点扰动后的世界**仍可测地比一个随机的另一个世界更接近基线**，即还存在可归因的共享因果结构；超出 `H_Y`，一次抛硬币 ≈ 一整个不同的世界。

**CI 95%**：对 `H_Y` 做 bootstrap（对 placebo 与 indep 两组分别重抽 1000 次），报告 `H_Y` 的 2.5%/97.5% 分位。

**测量协议（每次里程碑，用分叉格的同一批算力）**

```
for each 观测量 Y in 可观测量注册表:            # 注册表由 state schema 机械导出 + 少量登记的组合量
  for each 分叉点 (t_f, r):
    0. 断言 arm NULL 的 D ≡ 0（逐位）。不成立则整批测量作废（先修 §11.1）。
    1. Δ 网格 = {5, 10, 20, 50, 100, 200, 500}（年）
    2. 由 arm PLACEBO 得 F_placebo(Δ)，由 arm INDEP 得 F_indep(Δ)
    3. 算 R_Y(t_f, Δ) 与 A12(Δ)
    4. H_Y(t_f) = 上式；bootstrap CI
    5. 写入视界表 (Y, t_f, r, H, CI, R 曲线, kernel_hash, analyzer_version)
```

**健康区间（全部 D 级待标定，但必须现在给数，否则事后就是拟合）**

| 观测量类 | 例子 | `R_Y(10y)` | `R_Y(200y)` | `H_Y` |
|---|---|---|---|---|
| 身份型（非遍历） | 哪个家族坐在王座上、哪个政体统一了哪块地 | ≤ 0.5 | ≥ 0.6 | 20–150 y |
| 率型（近似可估） | 冲突频率、迁徙率、采纳速率 | ≤ 0.2 | ≥ 0.2 | 50–400 y |
| 结构型（慢变量） | 地权基尼、识字实践矩阵、通行成本场 | ≤ 0.10 | ≥ 0.15 | 200–1500 y |

**报警条件**：
- `R_Y(20y) > 0.8` ⇒ 该观测量**无因果视界**，系统必须对它的一切"为什么"返回 `UNATTRIBUTABLE_BEYOND_HORIZON`，且这不是可以靠改 UI 解决的。
- `R_Y(500y) < 0.10` 对**所有**观测量成立 ⇒ 第 3 条在这个世界里不成立，必须书面承认。
- 从来没有报告过"这个干预的效应在第 N 年后与随机扰动不可区分" ⇒ 说明我们从来没建过对照（`causality-bookkeeping` F1 的可观察症状之一）。

### 7.4 「不可归因」作为一等答案

```rust
enum Attributability {
    Attributed { causes: Vec<CauseEntry> },
    UnattributableBeyondHorizon { observable: u16, H: u32, ci: (u32,u32), asked_delta: u32 },
    UnattributableOverdetermined { OD: u16, msc: Vec<Vec<CauseRef>> },
    UnattributableDiluted { N_eff: f64, k_max: u16 },
    UnattributableUnderpowered { n_required: u32, n_affordable: u32, cpu_h_required: f64 },
    UnattributableLedgerBounded { crossings: u16 },     // 只给下界
    UnattributableUnmodeled,                            // 只能声明，永不主动返回
}
```

标准文案（超视界）：

> 超出该观测量的因果视界（实测 H = 63 年，95% CI [51, 78]，测于分叉点 t=3010/北境）。此处不存在可辩护的具体前因；可归因的只有慢变量通道与初始条件。

**可归因率 ρ**（项目级一等指标，进里程碑首页）：

$$\rho = \frac{\#\{\text{“为什么”查询返回 Attributed 且至少一条 CI 不跨零}\}}{\#\{\text{提交的“为什么”查询}\}}$$

**健康区间 ρ ∈ [0.15, 0.45]**（`causality-bookkeeping` F1.4 猜 20–40%，本规格取略宽区间；**D 级待标定**）。
- `ρ > 0.60` ⇒ **警报**：要么这个世界没有路径依赖，要么因果链是编的。
- `ρ < 0.10` ⇒ 系统对第 2 条没有交付，需要检查是不是视界测量方法坏了（先跑 §11.1）。
- 配套下界（`pseudo-simulation` F1(d)）：`不可解释占比 ≥ 10%`。ρ ≤ 0.45 已蕴含此条。

### 这一节禁止了什么

- **⛔ 禁止任何没有 `placebo_id` 的反事实结论进入 L2。** 这是 schema 级 NOT NULL 约束，不是流程约定。
- **禁止用"推进一个没人用的随机流"、"重跑一遍"、"换个种子"当安慰剂。** 前者恒为 0；后者是 `INDEP` 臂，回答的是另一个问题。
- **禁止无 Δ 的因果声明。** 声明的类型是 `(原因, 结果, 观测量, Δ, evidence_kind, CI)`；缺 Δ 在系统里不合法（`causality-bookkeeping` F1.1）。
- **禁止全局性的"我们的世界有因果链"这类说法。** 视界随观测量、区域、时代变化，全局命题在数学上没有意义。
- **禁止把"所有干预都显著改变了历史"读成路径依赖的胜利。** 它是归因崩塌。
- **禁止在 arm NULL 的 D ≠ 0 时继续做任何因果测量。**
- **禁止 UI 缺少「不可归因」按钮或把它折叠进次级菜单。** 它应当是最常见的答案之一。

---

## 8. 冲突（6）的裁决：归因报告的返回格式

因果重要性不存在客观总序（`causality-bookkeeping` F4）：留一法在过度决定下全返回零（`complex-systems-emergence` M2 自标的失效条件）；Shapley 的效率公理**强制**把效应分解干净即使系统不可加、对称公理抹掉时间顺序；PN 与 PS 对同一原因经常给出相反排名且不能合成一个数；Halpern–Pearl 给的是布尔判定且计算困难，定义本身至今无定论（`provenance-replay-counterfactual` §2.6 / §7.2）。

结论：**把主观性从隐藏的权重挪到公开的公理选择上，并强制同时报告多个序。**

### 8.1 完整返回格式

```rust
struct AttributionReport {
    report_id: H128,
    query: QuerySpec,                 // 目标 + 观测量 + Δ + 等价类定义
    target: TargetRef,                // EventRef | ChannelRef | ThresholdCrossingRef

    // ── 元数据：缺任一字段拒绝写入 L2 ──
    kernel_hash: H256, config_hash: H256, param_hash: H256,
    world_line_id: WorldLineId, seed_set: Vec<u256>,
    analyzer_version: u16, nominator_version: u16, registry_version: u16,
    placebo_id: H128,                 // NOT NULL
    power_analysis_id: H128,          // NOT NULL
    cpu_hours_spent: f64, quota_account: AccountId,

    // ── 视界 ──
    horizon: Horizon,                 // { observable_id, H_years, ci95, R_curve[], fork_lattice_id }
    beyond_horizon_declaration: String,   // 非空强制

    // ── 稀释 ──
    N_eff: f64, H_attr_bits: f64, k_max_displayable: u16,
    display_verdict: DisplayVerdict,

    // ── 过度决定 ──
    OD: u16,
    minimal_sufficient_sets: Vec<Vec<CauseRef>>,
    msc_search: MscSearchSpec,        // { method, restarts, |S|_max, k, exhaustive: false }

    // ── 必然性 ──
    inevitability_profile: Vec<(u32 /*Δ*/, u32 /*k*/, u32 /*n*/, (f64,f64) /*CI*/)>,
    profile_class: ProfileClass,

    // ── 候选原因 ──
    candidate_set_rule: CandidateRuleSpec,   // 机械规则 + 版本；不得手挑
    candidates: Vec<CauseEntry>,

    // ── 慢变量通道（四值必须齐全） ──
    channels: Vec<ChannelEntry>,

    // ── 缺席因 ──
    absent_causes: Vec<AbsentCause>,
    nearmiss_dependent: bool,

    // ── 账本区 ──
    ledger_crossings: u16,
    ledger_bound_note: String,        // "本报告 N 条路径穿过不可重算决策点，其效应为下界"
    channel_closure_bias: Option<EffectDelta>,   // §15 双孪生线实测的通道封闭偏差

    // ── 常驻页脚（常量，不可删） ──
    unmodeled_disclaimer: String,
}

enum DisplayVerdict {
    ShowTopK { k: u16 },
    RefuseTopKDiluted { N_eff: f64 },
    RefuseOverdetermined { OD: u16 },
    RefuseUnderpowered { n_required: u32 },
    RefuseBeyondHorizon { H: u32 },
}

struct CauseEntry {
    r: CauseRef,                      // EventRef | ChannelRef | AbsentCauseRef
    evidence_kind: EvidenceKind,      // Mechanical | LocalAnalytic | InterventionTested | Statistical | Narrative
    // 只有 InterventionTested 允许非 None：
    pn: Option<Estimate>,             // { point, ci95, n_per_arm, method }
    ps: Option<PsEstimate>,           // Estimate | NotEstimable{reason}
    effect: Option<EffectSize>,       // { d_real, placebo_quantile, quantile_ci, delta }
    axiom_note: String,               // "本排序采用 X；若改用 Y，第 i 与第 j 位互换"
    crosses_ledger: bool,
    equivalence_class: EquivClassSpec, // 目标事件的机械等价类定义（见 8.3）
}
```

### 8.2 各字段的定义与估计

**归因熵与有效原因数**

$$H_{\mathrm{attr}} = -\sum_i p_i\log_2 p_i,\quad p_i = \frac{|w_i|}{\sum_j |w_j|},\quad N_{\mathrm{eff}} = 2^{H_{\mathrm{attr}}}$$

`w_i` = 该候选原因的实测效应量（安慰剂校正后）。**`N_eff` 依赖候选集，候选集依赖候选规则** ⇒ `candidate_set_rule` 必须与 `N_eff` 相邻打印，否则该数字无意义。

**候选集生成规则（机械，禁止手挑）**

```
CandidateRuleSpec {
  version: u16,
  horizon_filter: 只取 stt.tick ∈ [target.tick − H_Y, target.tick]
  dependency_filter: 在目标机制的 Tier-D 静态读签名闭包内，深度 ≤ d（默认 d = 4）
  significance_filter: 按 §5.1 的 sig 取前 N（默认 N = 20）
  channel_filter: 所有 registry 中特征时标 ≥ (target.tick − t0) 的慢变量 × 二进宿窗口
  absent_filter: 窗口内 p_fire ≥ p_min = 0.01 的近失点 + 全部 STRUCTURAL_ZERO
}
```

**过度决定度**

`OD(e)` = 搜索找到的**不同的**最小充分前因集的个数。枚举在一般情况下组合爆炸，采用**贪心 + 随机重启近似**（重启 20 次，`|S| ≤ 3`，`k ≤ 10`，`Σ_{i≤3} C(10,i) × 2^7 ≈ 2.2×10⁴` 次重放的预算化枚举，`provenance-replay-counterfactual` M10）。**报告必须声明近似性质**：我们找到了 K 个充分集，不保证最小、不保证穷尽。

`OD ≥ 3` ⇒ `display_verdict = RefuseOverdetermined`，"此事过度决定"显示在任何列表**之前**。

**(PN, PS) 二维，不合成**

- `PN = P(¬e | do(¬c))`，在 `N` 次干预重放中 `e` 的等价类未在匹配窗口内出现的比例。
- `PS = P(e | do(c))`，需要**既无 c 也无 e 的基世界**：从分叉格 `INDEP` 臂里筛。若这样的世界少于 30 条 ⇒ `PS = NotEstimable{ reason: "insufficient c-free & e-free base worlds (found 7 < 30)" }`。**`NotEstimable` 是一等值，不是 0。**
- **禁止把 PN 与 PS 合成一个数、禁止把二者放进同一个排序。** UI 上它们是散点图的两个轴。

**必然性剖面 `p̂(Δ)`**

从分叉格：在目标事件前 Δ 年的分叉点，`INDEP` 与重采样非焦点流的 100 条平行线中，`e` 的等价类在窗口内出现的频数。Δ 网格 `{10, 50, 200, 500}`。

```
兴国之亡 · 世界历 3117 年 · 必然性剖面：10 年前分叉 96/100 · 50 年前 71/100 · 200 年前 23/100 · 500 年前 4/100
```

`profile_class`：`Δ=200` 仍高 ⇒ `STRUCTURAL_INEVITABLE`；`Δ=50` 就塌 ⇒ `CONTINGENT`；处处中等 ⇒ `MULTI_CAUSAL_COINCIDENCE`。

**这一行同时把纲领第 7 条变成可执行的**：荒诞 = 在真实历史参考类中极罕见的事件类型；强前置条件 = 该事件的 `p̂(Δ)` 在较大 Δ 上仍显著高于同类事件的基率。**荒诞不是靠叙事解释的，是靠剖面证明的**（`causality-bookkeeping` F6.3）。

**目标事件的机械等价类**（`EquivClassSpec`，必须预注册并打印）

精确的同一事件不会在平行线里重现，所以 PN/PS 与 `p̂(Δ)` 都需要等价类：

```
EquivClassSpec {
  mechanism_class: u16,
  scope_class: ScopeClassSpec,          // 同区域 | 同政体谱系 | 同格
  observable_crossing: (observable_id, threshold_expr, direction),
  time_window: ±w years (默认 w = 25),
}
```

⚠ **这是一个已知的薄弱点**：等价类是一个建模选择，改它就改 PN/PS/剖面。缓解只有两条——预注册 + 打印，以及对三种备选等价类各算一遍并报告排名是否翻转。**【本文原创，无来源，D 级】**

**`evidence_kind` 的严格分层**（`causality-bookkeeping` S2）

| kind | 来源 | 允许携带 | UI 渲染 |
|---|---|---|---|
| `Mechanical` | Tier-D 静态签名闭包 + 近失点枚举 | **无权重、无排序、无百分比** | 灰色列表，文案强制"可能被读取的量" |
| `LocalAnalytic` | 加性 logit 的单步项分解 | 一步有效的 Δlogit | 文案强制"在此机制内部，给定其他变量"；**不得跨机制边界** |
| `InterventionTested` | 干预实测 | PN/PS/效应量/CI/N | 唯一允许称为"原因"的类型 |
| `Statistical` | 跨运行回归 | 系数 + 混杂警告 | 必须并列打印混杂风险 |
| `Narrative` | L4 渲染 | **零因果内容** | 视觉上不可混淆；**不得作为任何其他边的父节点** |

### 8.3 UI 硬规则（全部是 API 层强制，不是前端约定）

- **R1（本任务点名要求的那一条）：`N_eff > 2k` 时拒绝显示 top-k。** 默认 `k = 7` ⇒ 需要 `N_eff ≤ 14`。`causality-bookkeeping` F4 预期一次千年尺度国家灭亡的 `N_eff` 在 10³–10⁵ 量级，**因此默认答案就是 `RefuseTopKDiluted`，这是正确的**。替代显示：
  > 此事件不存在少数主因（有效原因数 ≈ 4.1×10⁴，归因熵 15.3 bit，候选集规则 v3）。
  API：`display_verdict != ShowTopK` 时，序列化器**不输出 `candidates` 的有序数组**，只输出无序集合 + 摘要统计。前端拿不到序，就画不出排行榜。
- **R2**：禁止跨 `evidence_kind` 排序、合并、求百分比和。类型层不兼容——五种 kind 是五个不同的 Rust 类型，不能装进同一个 `Vec<T: Ord>`。
- **R3**：报告里**没有**"归一化贡献份额"字段。能加到 100% 是效率公理的产物，不是世界的性质。若确实要 Shapley，它作为独立标注块出现，并内联打印效率公理警告。
- **R4**：`Narrative` 边不得作为任何其他边的父节点（防止叙事污染沿因果图反向传播）。
- **R5**：跨 `kernel_hash` 的比较与聚合在 API 层**报错**，不是警告（`causality-bookkeeping` S1.2）。
- **R6**：`placebo_id` / `power_analysis_id` 为空 ⇒ 拒绝写入。
- **R7**：realized `N < 0.8 × n_required` ⇒ 自动标 `RefuseUnderpowered`，且**不得**作为"是原因"的证据，只能作为"我们没能力回答"。
- **R8**：`axiom_note` 非空强制。示例文案：
  > 本排序采用 Shapley（效率+对称+可加）。若改用 PN 排序，第 1 与第 4 位互换；若改用 PS 排序，第 2 位落到第 7 位。

### 8.4 「快表」问题的处置（`causality-bookkeeping` S6）

S6 预言：UI 要秒级，严肃分析要 10³–10⁴ CPU 小时，中间必然长出一个便宜的启发式快表，而它会成为我们、读者、小说、世内史学实际接触到的"因果"。

**本规格的处置比 S6 建议的更强**：不是"给快表打上未验证标记"，而是**让快路径在结构上不可能产出排序**。

- 快路径只允许返回 `evidence_kind = Mechanical` 的内容：静态签名闭包成员 + 近失点枚举 + 从分叉格取的必然性剖面（那是预计算的）。
- `Mechanical` 类型**没有权重字段**（类型层缺失，不是置空）。因此快表在结构上画不出因果链，也无法被误读成排序。
- **季度抽检**（替换 S6.2 的 top-3 重叠率，因为快路径没有 top-3）：随机抽 10 个已答问题，比对
  - `mechanical_recall` = 完整协议找到的 `InterventionTested` 原因中落在静态闭包内的比例。**要求 ≥ 0.90**；低于此说明静态读签名不可靠（是一个 bug，不是一个指标）。
  - `mechanical_precision` = 静态闭包成员中 CI 不跨零的比例。**预期极低（10⁻³ 量级）且这是正常的**——它是过近似。把它印出来，正是为了让人不要把闭包当成原因。

### 这一节禁止了什么

- **禁止返回一个排序作为"为什么"的答案**，除非 `N_eff ≤ 2k`。
- **禁止合成 PN 与 PS。**
- **禁止 `NotEstimable` 被渲染成 0。**
- **禁止百分比加到 100%。** 报告 schema 里根本没有这个字段。
- **禁止 `parent_event_id` 这类单指针字段存在。** 数据结构是 `(节点集, 带类型的边集, 最小充分集族, OD, N_eff)`。
- **禁止跨内核版本比较结论。**
- **禁止一个带权重的快表存在。**
- **禁止在报告缺 `axiom_note` / `beyond_horizon_declaration` / `unmodeled_disclaimer` 时序列化成功。**

---

## 9. 冲突（8）的裁决：四层与零可见性

因果不是状态变量。世界里没有一个字段叫"原因"。状态与转移是事实（可逐位重放校验）；因果归因是**我们对这些事实做的分析**，它有方法、有假设、有误差棒、会随分析器版本改变（`causality-bookkeeping` S4）。

### 9.1 四层与可见性矩阵

| 层 | 内容 | 认识论地位 | 内核可见 | Agent 可见 | L4 可见 | 我们可见 | 存储 |
|---|---|---|---|---|---|---|---|
| **L1 机械事实** | 状态、转移、`DrawSite`（分布+分位+阈值）、写集、Tier-D 静态签名、近失集合、结构性零 | **事实**。可逐位重放校验。无语义、无权重、不可读 | 是（就是内核自己） | **否**（只能经 `Perception` 投影） | 否 | 是 | 重算 |
| **L2 因果分析** | 归因报告、干预效应、PN/PS、必然性剖面、视界、`N_eff`、提名索引、`Channel` | **我们的历史学**。带 `analyzer_version`，可被推翻，改变时旧结论**作废**而不是被"修正" | **零** | **零** | **零** | 是 | 落盘（小） |
| **L3 世内叙事** | Claim 图（命题 + 指涉的 L1 id 或 null + 失真算子链 + 载体群体 + 声望 + 存活副本数），世内史学 | 世界内部的解释 | **部分**：Claim 作为信念影响决策——这是它的功能，不是泄漏 | 是（受信息边界约束） | 是 | 是 | 落盘 |
| **L4 作者层** | LLM 渲染的自然语言、我们的注释、小说 | 我们的旁白 | **零** | **零** | — | 是 | 落盘 |

**关键改动（第 9 条必须的修订）**：**只有 L1 是世界事实。L2 与 L3 是同一类东西——对事实的解释——区别只在于 L2 的工具更好、信息更全。**（`causality-bookkeeping` S4.1）

这不削弱项目，它让"世内历史学家"第一次真正有意思：我们可以测量**在给定信息可得性约束下，L3 能逼近 L2 到什么程度**，以及**当我们改进分析器让 L2 变化时，L3 的"准确度"如何回溯性地改变**。

**L3 里没有自然语言**（`mandate-contradictions` F6）：世内表示是命题图，文本只在 L4 按需渲染，**永不回流为模拟输入**（类型级约束 + 序列化边界强制）。这同时封住了 `pseudo-simulation` S13（世内史官把内核的空洞圆过去，我们丧失发现自己有病的能力）与 `mandate-contradictions` F6（文本吃掉算力与存储预算）。

### 9.2 四道 CI 强制（全部机械，全部二值）

**C1 构建期单向依赖**（编译错误，不是 lint）

```
kernel            ↛ analysis(L2) , authoring(L4) , nomination
agent_context     ↛ analysis(L2) , authoring(L4)
prompt_builder    ↛ analysis(L2) , authoring(L4) , world_state(L1 直读)
analysis(L2)      →  kernel(只读视图) , L1 重放 API           ✓
authoring(L4)     →  analysis , L3 , L1                       ✓
L3                →  kernel(信念作为状态)                      ✓
```
用工作区可见性规则（Cargo `[workspace] deny` / Bazel `visibility` / Python `import-linter`）实现。

**C2 符号可达性检查**

从每个构造 `Perception` 或 LLM prompt 的函数出发做静态调用图可达性；若任何 L2/L4 符号可达 ⇒ 构建失败（`causality-bookkeeping` S4.2）。

**C3 进程/存储隔离**

L2 存在独立存储、独立凭据；模拟进程的凭据对它**无读权限**。运行时尝试读返回 permission denied，**不是返回空**（空会被静默吞掉）。

**C4 L2 抹除的逐位不变性检验**（二值，无法狡辩）【本文原创，无来源，D 级】

把全部 L2 工件替换为**同形状的随机内容**，用同一 `(world_seed, code_hash, param_hash, ledger)` 重跑世界。要求轨迹**逐位相同**。任何读取 L2 的内核/agent 路径都会导致发散。

这是 `emergence-verifiability` F5.1 类型抹除测试的因果侧对偶。原文的类型抹除测试抓"内核读取 composite 标签"；本条抓"内核读取因果分析"。两条都必须跑。

**C5 可知性上界不可超越**（与 spec-society/spec-llm 共有）

世内历史学家对任一历史命题的正确率不得高于 `U(t)`——在存活 L3 语料下任何完美推理者能达到的上限（`mandate-contradictions` F8.3，`writing-records-memory` M13）。超过即证明有泄漏，CI 失败。这是我们独有的实验台：我们同时拥有真实 stemma 与存活语料。

### 9.3 L2 的版本化与竞争

- 每条 L2 结论带 `analyzer_version`，且**允许同时存在多个互相竞争的分析器**。这与第 9 条的多元精神一致，只是把多元提前到了我们这一层（`causality-bookkeeping` S4.3）。
- 内核变更分级（`causality-bookkeeping` S1.4）：
  - `纯性能`：要求位相同，自动验证（§11.1），**重算债务为零**。
  - `参数`：债务 = 受影响结论集（由 `param_hash` 的 diff 机械导出）。
  - `机制`：**全部债务**，且 canon 线作废、必须从 t=0 重跑（`mandate-contradictions` F9.2）。
- **重算债务仪表盘**（里程碑评审第一页）：有多少条结论的 `kernel_hash` 落后于 HEAD、按 `cpu_hours_spent` 排序、重算它们需要多少 CPU 小时。

### 这一节禁止了什么

- **禁止因果表与状态表在同一个 schema / 同一个"世界事实"命名空间下。**
- **禁止任何指标叫"历史学家准确率"并把 L2 当成正确答案。** 合法的指标是 `D(t) − U(t)`（史学水平）与 `U(t)`（史料条件）的分解（`writing-records-memory` M13）。
- **禁止世内 agent 以任何方式取得 L2。** 包括"技术上可以但我们不会"。C1–C4 让它在技术上就不可以。
- **禁止 L3 存储自然语言文本。** L3 是命题图。
- **禁止 L4 的渲染产物回流为模拟输入。**
- **禁止用新内核重放旧世界然后声称那是同一段历史**（`provenance-replay-counterfactual` M12）。
- **禁止 UI 并列比较不同 `kernel_hash` 的结论。**

---

## 10. 冲突（9）的裁决：快照、分叉、存储

### 10.1 内容寻址块存储

- 块 = 一个空间分块的全部实体状态，或一个实体族的一页。块 id = `BLAKE3-256(块内容)`。
- 全局去重：所有世界线共享一个块存储。相同的静态地理（高程、河网、土壤）在 200 条世界线之间只存一份。
- 快照 = 块树的 Merkle 根（32 B）。
- 分叉 = 复制根指针 + 追加一行 `Lineage`。**O(1)**。
- 写入 = path copying（Driscoll, Sarnak, Sleator & Tarjan 1986/1989 的完全持久化技术；`provenance-replay-counterfactual` §2.9，A 级）：深度 `d` 的树每次写入产生 `O(d)` 个新块。

⚠ **必须记住 `computational-feasibility` S5 的警告**：HAMT/COW 让**分叉那一瞬间**是 O(1)，但分叉之后每 tick 写入的新块数量与主线一样多。"结构共享 O(1) 分叉"这句话会系统性低估存储。本规格的对策就是 §10.3 的"不存轨迹存配方"。

### 10.2 快照配额（⛔ 硬上限进 CI）

| 类别 | 规则 | 张数 | 体积 |
|---|---|---|---|
| 主锚点 | 每 50 模拟年 | 60 | 3.6 GB |
| 提名锚点 | 提名事件中 `sig` 前 Q 名；**事后由重放生成**（≤25 年重放 ≈ 0.008 CPU h） | ≤ 60（LRU 可逐出） | ≤ 3.6 GB |
| 滚动细锚点 | 最近 200 模拟年，每 5 年 | 40（滚动） | 2.4 GB |
| **上限** | | **≤ 140** | **≤ 12 GB / 参考线** |

超出上限时按 `1/sig × 1/recent_access` 逐出提名锚点（它们可重算）。**主锚点与滚动细锚点不可逐出。**

**锚点间隔的推导**：从锚点恢复到任意时点最坏需重放一个间隔。50 年 = 50 tick；`T_run ≤ 1 h / 3000 tick` ⇒ 1.2 s/tick ⇒ 最坏 60 s。可接受。若 `T_run` 退化到 10 h，间隔必须缩到 20 年，快照张数升到 150 ⇒ 触发上限 ⇒ **构建失败**。这条把存储预算与 `T_run` 绑死，是好事。

### 10.3 「不存轨迹存配方」与 canon/lab 单向阀

- **只有参考线（canon）保留快照。** 集合成员与分叉只保留：配方（§2.1 的 Manifest）+ 年度聚合投影 + LLM 账本 + 摘要统计。全状态按需重算。
- **必须持久化的不可重算物**：LLM 冻结账本（3×10⁴ 调用 × 1.5 KB = 45 MB/线；按 `llm-agent-social-simulation` 的 1.5×10⁵ 次算则 225 MB/线）。
- **canon 种子由事先声明的、与结果无关的规则决定**（`pseudo-simulation` F5.1）：
  ```
  world_seed_canon = BLAKE3("civsim-canon" || kernel_version || param_hash)[0..32]
  ```
  先定种子再跑，跑出什么算什么。允许因技术故障重跑（必须留痕），**不允许因不好看重跑**。
- **单向阀**：lab 分支永远不能成为 canon。实现方式见 §2.1——`lineage_class` 进世界线身份哈希，改标签即断链。出版工具额外拒绝读取 `lineage_class != Canon` 的世界线。
- **运行登记表（append-only，不可删）**：每一次超过 100 模拟年的运行，无论结果，自动写入
  ```
  RunRegistryRow { world_line_id, kernel_hash, param_hash, world_seed, lineage_class,
                   start_ts, end_ts, termination_reason, macro_summary_digest,
                   viewed_by: Vec<(user, ts)>, deleted_at: Option<ts>, deletion_justification }
  ```
  删除条目需显式提交记录。**失败率必须公布**：`P(灭绝)`、`P(5000 年无国家)`、`P(永久停滞)`。**一个在 200 个种子上灭绝率恰为 0 的世界是可疑的**（`pseudo-simulation` F5.5）。

### 10.4 留存预算表

假设集 A（§3.3）。**全部体积数字为 D 级，随假设按比例变。**

| 项 | 算术 | 参考线 | 每条非参考线 | 可重算？ |
|---|---|---|---|---|
| T0 配方清单 | — | 1 MB | 1 MB | ✗ 绝不可删 |
| 运行登记表条目 | — | 4 KB | 4 KB | ✗ |
| 参数 `change_log` | — | 1 MB | 共享 | ✗ |
| LLM 冻结账本 | 3e4 × 1.5 KB | 45 MB | 45 MB | ✗ |
| 世界哈希金丝雀 | 3,000 × 32 B | 0.1 MB | 0.1 MB | ✗（廉价校验锚） |
| 主锚点快照 | 60 × 60 MB | 3.6 GB | 0 | ✓ |
| 提名锚点 | ≤60 × 60 MB | ≤3.6 GB | 0 | ✓ |
| 滚动细锚点 | 40 × 60 MB | 2.4 GB | 0 | ✓ |
| 年度聚合投影 | 2,000 × 50 × 4 B × 3,000 | 1.2 GB | 1.2 GB | ✓ |
| 提名事件索引 | 500/年 × 3,000 × 300 B | 0.45 GB | 0 | ✓ |
| Tier-S 哨兵读取集 | 1.88e6 × 1e-3 × 3,000 × 96 B | 0.54 GB | 0 | ✓ |
| L2 结论库 | ~10³ 报告 × 100 KB | 0.10 GB | 共享 | ✓ |
| **小计（不含分叉格）** | | **≈ 12.0 GB** | **≈ 1.25 GB** | |
| 分叉格摘要 | 60 分叉点 × 133 线 × 2 MB | 16 GB | 共享 | ✓ |
| **参考线合计** | | **≈ 28 GB** | | |
| **200 条集合合计** | | | **≈ 273 GB** | |

**硬上限（进 CI，超出即作业拒绝）**：参考线 ≤ 30 GB；单个 200 种子集合 ≤ 400 GB；全项目在线存储 ≤ 8 TB。

**对照被否决的方案**：写入级 provenance 单跑 0.29–4.8 TB，×50 涌现认证 = **14–240 TB**。比值 **1/51 到 1/880**。

### 10.5 删除策略

**绝不可删**：T0 配方、LLM 账本、canon 谱系表、运行登记表、L2 结论的元数据行、参数 `change_log`、近失访问日志、世界哈希金丝雀。

**可删（三条断言全过才允许）**：
```
deletable(区间 W of 世界线 L) :=
    covered_by_live_anchor(W, L)                      # 至少一个存活锚点覆盖
  ∧ manifest_complete(L)                              # 配方完整
  ∧ code_buildable(L.code_hash)                       # 该 code_hash 在归档中可构建
```
缺第三条时的删除是**不可逆**的，必须写入 `IRRECOVERABLE_DELETION` 日志，并在里程碑报告首页显示计数。

**删失必须显式**（CHGIS 的「数据下限」教训，`provenance-replay-counterfactual` §6.1.3 / §8.4）：任何因保留策略而无法回答的区间，查询必须返回

```rust
enum QueryResult<T> { Value(T), NotPresent, CensoredByRetention { covered_by: Option<AnchorRef> }, Unknown }
```

**禁止返回"无事件"来表示"我们删了"。** CHGIS 有 1,347 条记录明确标了「数据下限」；我们必须照做，否则几百年后自己的分析会把"数据缺失"读成"事件未发生"。

**三值逻辑是刚需**：L1 与 L3 都必须区分"不存在" / "未知" / "因保留而删失"（`emergence-verifiability` §6.10；`pseudo-simulation` S6 引 Beheim et al. 2021 的撤稿案例）。

### 10.6 Schema 演化

`provenance-replay-counterfactual` M12（依据 Overeem et al. 2021 *JSS* 178:110970，25 位工程师 / 19 个实现的实证，A 级）：

1. **versioned events**：每条持久化记录带 `schema_version`。
2. **upcasting**：`upcast_{v→v+1}` 是纯函数，链式组合，**读时升级，日志本身不变**。
3. **weak schema**：新增字段必须有默认值；删除字段只能标 deprecated，不能物理移除。
4. **copy-and-transform**：只在重大版本跃迁时用（生成新谱系，保留旧谱系与锚点）。
5. **⛔ 禁止 in-place transformation**（原地改写历史日志）——它破坏 T0 哈希链，等于销毁溯源。

### 这一节禁止了什么

- **禁止存储非参考世界线的完整轨迹。** 存配方，不存轨迹。
- **禁止分叉数、快照数无配额。** 无配额的"保存任意历史节点"在组合上无界（`computational-feasibility` C4）。
- **禁止 lab 分支以任何方式成为 canon。**
- **禁止因结果不好看而重跑 canon。** 技术故障重跑必须留痕。
- **禁止删除运行登记表条目而不留删除记录。**
- **禁止用"无事件"表示"因保留而删失"。**
- **禁止两值逻辑（有/无）。** 三值起步。
- **禁止原地改写历史日志。**
- **禁止在没有 `code_buildable` 断言时删除任何区间。**

---

## 11. 冲突（10）的裁决：两个 CI 级地基测试

这两条比任何 schema 设计都重要（`causality-bookkeeping` F7.2）。**它们必须在写第一个机制之前就跑通。**

### 11.1 `T-ZERO` 零干预测试

```
输入: 参考线 L（玩具或全尺度）、分叉点 t_f、视界 Δ_max

IDENTITY 的三种合法形式（必须全部测，不能只测一种）:
  (a) NO_OP           : 空干预规格；不进入干预执行路径
  (b) SET_TO_ACTUAL   : do(x := x_actual) —— 走完整的干预执行路径与修复路径，但值不变
  (c) FLIP_AND_UNFLIP : do(u := u') 后立即 do(u := u_actual)
理由: (a) 可能走了一条不同的代码路径而"碰巧"对；(b) 抓修复规则里的副作用；
      (c) 抓"干预日志/账本索引被推进了但值被还原"这类错位。

步骤:
  1. 从 L 在 t_f 的锚点分叉出 L'，施加 IDENTITY
  2. 重放 L' 到 t_f + Δ_max
  3. 判据（逐位，无容差，任一不满足即构建失败）:
     ∀ t ∈ [t_f, t_f + Δ_max]:
       world_merkle_root(L', t) == world_merkle_root(L, t)
     ∧ ∀ DrawSite d 在窗口内: (d.counter, d.u, H(d.dist), d.outcome, d.fired) 逐位相同
     ∧ LLM 账本命中序列（key 序列与 hit/miss 序列）逐位相同
     ∧ 实体 id 集合逐位相同（抓 id 重编号）
     ∧ Tier-S 哨兵采样点集合逐位相同（抓采样器本身的顺序依赖）

运行频率:
  每次提交    : 玩具世界，Δ_max = 20 年
  每次 PR     : 玩具世界，Δ_max = 200 年
  每次里程碑  : 全尺度，Δ_max = 500 年，t_f 取 8 个不同分叉点
```

**它抓什么**：一切"重放 ≠ 原跑"的漏洞。**它是 §7 全部测量的前置条件**：`arm NULL` 的 `D ≠ 0` 时，安慰剂零分布与视界测量全部作废。

### 11.2 `T-ISOLATION` 因果隔离测试（本规格认为最重要的单条交付物）

**测试地图 `M_iso` 的构造要求（必须由静态分析证明，不能靠假设）**

```
(i)   地理隔离: A 与 B 之间的最小通行成本 > MAX_RANGE
      MAX_RANGE := sup{ 内核中所有运输/迁徙/传播/军事机制的射程常数 }
      —— 由 §复杂度契约表机械导出（computational-feasibility S4.1），不是人手填的数
(ii)  航海封锁: A 的初始技术集合不含任何跨水机制的前置条件，
      且 A 上不存在能产生该前置条件的资源。
      由 Tier-D 静态读签名上的可达性分析证明，不是假设。
(iii) 气候独立: 驱动 A 与 B 的气候 CBRNG counter 不共享任何分量
      （命名空间 "climate/<cell_id>"，cell_id 不跨陆域）
(iv)  无全局归约: 内核中任何跨 A、B 的求和 / 求最值 / 排序 / 排名 / 归一化，
      必须在"全局归约审计表"里逐条列出并裁定：
        要么改为分陆域归约，要么登记为已知泄漏通道并从本测试豁免（豁免条数只允许下降）
```

**测试**

```
1. 跑 M_iso 的参考线 L 到 t = 400 年
2. 在 t_f = 100 年，对 A 上的抽样点做任意合法干预：
   随机抽 K = 32 个 (site, op) 组合，op 遍历干预代数的全部形式
3. 每个干预重放到 t_f + 100 年
4. 硬判据（任一失败即构建失败）:
   ∀ t ∈ [t_f, t_f+100]:
     block_merkle_root(B 的全部状态块, t) 逐位等于参考线
   ∧ B 上每个 DrawSite 的 (counter, u, outcome, fired) 逐位相同
   ∧ B 上的 LLM 账本命中序列逐位相同
   ∧ B 上的实体 id 集合逐位相同
5. 软判据（报告，不失败）:
   A 上的散度锥必须有空间梯度：
     corr( 首次改变的 tick , 到干预点的通行成本 ) > 0.5
   白噪声式的散度（各处同时改变）说明存在隐藏耦合，即使硬判据通过
```

**它一次抓住的五类静默致命伤**（`causality-bookkeeping` F7 的清单，逐条对应到判据 4）

| # | 致命伤 | 传播链 | 被哪条判据抓住 |
|---|---|---|---|
| 1 | **id 重编号** | A 上多/少一个实体 → 全局自增计数器 → B 的新实体 id 变 → B 的 counter 变 → B 的抽样全变 | "B 的实体 id 集合逐位相同" + "B 的 DrawSite counter 逐位相同" |
| 2 | **容器迭代顺序** | A 的实体数变 → 全局哈希容器桶布局变 → B 的处理顺序变 → 平局打破或归约顺序变 | "B 的 block_merkle_root 逐位相同" |
| 3 | **浮点归约顺序** | 全局求和的并行分块边界随 agent 数变 → B 读到的全局量最后一位变 → 阈值比较翻转 | 同上（且若 §2.5 的定点整数被遵守，这一类在原理上不可能发生——本测试是对它的验证） |
| 4 | **空间索引重建** | 四叉树/网格哈希的桶内顺序依赖插入顺序 → B 的邻域查询返回顺序变 | 同上 |
| 5 | **LLM 账本错位** | 账本按调用序号索引 → A 的调用次数变 → B 的调用取到别人的应答 | "B 的 LLM 账本命中序列逐位相同" |

### 11.3 副产品：信息边界的机械定义

`emergence-verifiability` F17 指出信息边界（第 4 条）没有可机械执行的定义（"合理能够获得"是价值判断，不是谓词）。因果隔离测试给出一个：

> **定义**：设 `reach(s, t → t')` 为从时空点 `(s, t)` 出发、沿内核中**已实现的**全部传播机制（人、货、信、病、水、军）在 `t'` 之前可达的时空点集合。它由通行成本图与各机制射程常数**机械计算**，无自由参数。
>
> **信息边界断言**：对任意 agent `d` 与任意 `t'`，`d` 在 `t'` 的决策的**可重算依赖闭包**必须包含在 `⋃_{s ∈ d 的历史位置} reach(s, · → t')` 之内。
>
> **它是可逐位验证的**：对任意 `(s, t)` 做一次单点干预；若某个不在 `reach` 内的 agent 的决策改变了，信息边界被违反，并输出违例路径。

`T-ISOLATION` 是它的一个特例（A 与 B 互不在对方的 `reach` 内）。**完整版按抽样执行**（每次里程碑）：随机抽 `R = 64` 个 `(s, t)`，单点干预，重放 `T = 50` 年，检查所有改变了决策的 agent 是否都在 `reach` 内。违例即失败。

⚠ **诚实边界**：这个定义抓的是**显式泄漏**（状态流到不该流的地方）。它抓不住 `emergence-verifiability` F17 的第二条路径——**隐式泄漏**，即 LLM 从训练语料里"知道"某类局面该怎么走。那需要反事实盲测（把 prompt 中的真实事实随机替换为等概率的假事实，看决策分布变不变），归 spec-llm 负责。本规格只声明：**信息边界的显式部分从此是二值可判定的，隐式部分不是。**

### 11.4 其余门禁测试清单（全部进 CI）

| 测试 | 判据 | 频率 | 出处 |
|---|---|---|---|
| 线程数不变性 | 1/4/16 线程逐位相同 | 提交 | `computational-feasibility` F2 |
| 容器逆序遍历不变性 | dict 反序遍历逐位相同 | 提交 | `abm-methodology` M5 |
| 哈希种子不变性 | `PYTHONHASHSEED` 两个不同值逐位相同 | 提交 | `provenance-replay-counterfactual` M6.1 |
| 跨机器不变性 | ≥2 种 CPU 架构逐位相同 | PR | `computational-feasibility` §7.3 |
| 锚点重放一致 | 从 `A_k` 重放到 `A_{k+1}` 的状态哈希 == 记录 | 提交 | `provenance-replay-counterfactual` M14.4 |
| 步长减半不变性 | **必须在崩溃期窗口上做**；宏观轨迹偏移在 MC 噪声内 | PR | `computational-feasibility` S6.1 |
| 类型抹除测试 | composite 标签换随机 UUID 后轨迹逐位相同 | PR | `emergence-verifiability` F5.1 |
| **L2 抹除测试** | L2 工件换随机内容后轨迹逐位相同 | PR | §9.2 C4（本文原创 D） |
| 提名器确定性 | 同输入两次提名集逐位相同 | PR | §5 |
| 复杂度回归 | tick 耗时 vs 实体数的 log-log 斜率 ≤ 1.2 | PR | `computational-feasibility` S4.3 |
| `GATED` 计数 | 只允许下降 | 提交 | `pseudo-simulation` S3.2 |
| 静态读签名合规 | 运行时越界访问 = 0 | 提交 | §3.2 |
| 哨兵一致性 | 抽 10³ 条哨兵，Tier-R 重算读取集集合相等 | 里程碑 | §3.2 |
| Tier-D 召回率 | `mechanical_recall ≥ 0.90` | 季度 | §8.4 |
| 1 ULP 发散时间 | 玩具世界扰动 1 bit，测宏观量偏离到 O(1) 的 tick 数 | 里程碑 | `computational-feasibility` §7.5 |

**⛔ CI 只允许断言不变量，永远不允许断言宏观结果**（`pseudo-simulation` S11）。允许：守恒律、确定性、顺序无关性、`GATED` 计数、读签名合规、类型抹除、金丝雀检出率。**禁止**：`assert 到 t=2000 至少存在一个人口 > 10000 的政体` 这一类。宏观结果只能进仪表盘，不触发红/绿。

### 这一节禁止了什么

- **禁止在 `T-ZERO` 与 `T-ISOLATION` 未通过的情况下运行任何反事实实验、任何视界测量、任何归因作业。** 它们是前置条件，不是"最好也做一下"。
- **禁止给这两个测试任何容差。** 逐位就是逐位。
- **禁止手填 `MAX_RANGE`。** 它必须从复杂度契约表机械导出。
- **禁止全局归约审计表的豁免条数上升。**
- **禁止 CI 断言任何宏观历史结果。**
- **禁止把 `T-ISOLATION` 的软判据（散度锥空间梯度）当成可选。** 它可以不失败，但必须被报告；硬判据通过而散度像白噪声，说明还有隐藏耦合。
