# INTEGRATION-REVIEW —— 四份规格的交叉一致性审查

- **slug**: `integration-review`
- **日期**: 2026-09-10
- **审查对象**: `design/spec-world-state.md`（1580 行）、`design/spec-causality.md`（1262 行）、`design/spec-llm-boundary.md`（2479 行）、`design/spec-validation.md`（1858 行）、`design/DECISION-REGISTER.md`（1042 行）。全部逐节实际读取。
- **证据等级约定**: A/B/C/D 同全项目口径。凡本文自己的判断（四份规格与七份红队都没写过的），标注 **［本文原创，无来源，D 级］**。
- **本文不做的事**: 不重复四份规格内部已经写清的论证；不发明新的经验数字；不裁决四份规格已经一致的地方。

---

## 0. 一句话结论

**四份规格在"禁止什么"上高度一致且质量很高；在"世界是什么、按什么比特布局跑、什么叫一个事件、一次实验值多少钱"这四件事上互不相容，而这四件事全部是 A 档不可逆决定。**

更准确地说：`spec-world-state` 定了一套 L0 本体与确定性比特布局；`spec-causality` 用**另一套**比特布局与**另一套**实体假设算了全部存储与算力；`spec-llm-boundary` 用**第三套**世界线身份定义了确定性；`spec-validation` 用**第四套**（且部分已被 world-state 取消的）实体本体写了复杂度契约与预算表。**没有任何两份规格能同时被实现。** 好消息是：冲突集中在少数几个可以一周内裁决的接口上，且每一处都有明确的胜方。

另一个必须说出口的判断：**这四份规格加起来仍然没有一行"世界"**。它们是接口规格、因果规格、边界规格、治理规格。产量函数、生育函数、迁移规则、战争结算、Recipe 变异、牧业生业、`default_policy` —— 一个都没有。`DECISION-REGISTER §6` 把"URR 病：从未跑通一次完整的三千年"排在最可能的失败方式第 1 位，并逐字写下"**如果读完这张表的反应是'那我们再研究半年'，这张表就已经害了项目**"。本审查认为这个风险在四份规格产出之后**上升了**，因为现在有 8,221 行规格、0 行内核。

---

## 1. 实质冲突

分五组：A 内核最底层接口、B 确定性契约与 LLM ledger、C「事件」概念、D 分辨率/tick/算力自洽、E 验证算力与判据适用性。每条给出：双方原文位置、为什么这是实质冲突、建议裁决、以及**裁错了最早在哪看出来**。

---

### 组 A —— 内核最底层接口（这几条决定第一行代码的形状）

#### C1 · CBRNG counter 布局与 Gumbel 寻址：两份规格给出比特级相反的规定

| 方 | 原文 |
|---|---|
| `spec-world-state §6.4` | Threefry4x64-20；`ctr = (tick:u64, entity_id_lo:u64, entity_id_hi:u64, (slot_id:u32<<32)\|draw_index:u32)`；`key = (world_seed_lo, world_seed_hi, H64(stream_path), branch_salt)`。并逐字写明"**为什么用 4×64 而不是 4×32：4×32 装不下完整的 128 位 entity_id，只能截断，而截断会引入碰撞……这是一个会在几百年后才显形的静默 bug**"，禁令表里有"**禁止 counter 中截断 entity_id**"。 |
| `spec-causality §2.2` | `counter = (tick:u32, entity_key:u64, purpose_id:u16, draw_index:u16)`，其中 `entity_key = 实体内容寻址 id 的低 64 位折叠`；key 只有两个分量 `(world_seed, H64(stream_namespace))`，**没有 `branch_salt`**。 |

`spec-causality` 的布局**恰好是** `spec-world-state` 明文禁止的那一种（截断 entity_id 到 64 位），counter 宽度也从 256 位掉到 128 位。

同一处还有第二个相反规定：

| 方 | 原文 |
|---|---|
| `spec-world-state §6.7` | `u = uniform_q32(stream, ctr=(tick, id_lo, id_hi, (slot<<32)\|oh))`，`oh = H32(o.content_id)`；禁令"**禁止 Gumbel 分量按位置索引寻址**"，并论证按位置寻址与 Oberst & Sontag 要消除的病症**完全同构**。 |
| `spec-causality §2.4` | `g_j = -log(-log u_j)`，`u_j = CBRNG(counter ⊕ j)` —— `j` 是候选项的**位置索引**。 |

`spec-llm-boundary §8.2` 的 ledger 字段 `rng_counter: u256` 与 `(tick, actor_lo, actor_hi, slot<<32|content_hash)` 站在 world-state 一边，所以 causality 是唯一的偏离者。

**为什么这是实质冲突**：`DECISION-REGISTER A4/A5` 把它列为"事后更换 = 全部历史与全部反事实结论作废"。两种布局产生的随机流逐位不同，不存在迁移路径。而且 causality 自己的 `T-ISOLATION`（§11.2 判据 4「B 的 DrawSite counter 逐位相同」）恰恰是用来抓 id 截断碰撞的测试 —— 用它自己的布局跑，这个测试会在碰撞发生时静默失败。

**建议裁决**：采用 `spec-world-state §6.4/§6.7` 的布局，**逐字**。理由不是资历，是论证：world-state 给了截断为什么危险的机制性理由，causality 没有给 128 位布局的任何理由（它只是转述 `abm-methodology M4` 的示意写法）。`spec-causality §2.2/§2.4` 整节作废重写；`DrawSite.counter` 的类型跟着改成 4×u64。`branch_salt` 必须保留（causality §10.1 的 O(1) 分叉与 §4.4 的 `ReseedStream` 都需要它）。

**裁错了最早在哪看出来**：`T-ISOLATION` 在健康内核上通过，但在实体数超过 ~10⁹ 的长跑后期出现无法复现的隔离区偏移；或者 `provenance` 的反事实在重排 `match` 分支后给出不同结果。

---

#### C2 · 世界线身份有四个定义，canon 种子有三个公式

| 出处 | 世界线身份 |
|---|---|
| `spec-world-state §7.4`、§11.1 | `(world_seed, kernel_hash, param_prior_hash, basemap_hash, llm_ledger_hash)` |
| `spec-causality §2.1` | `H256(world_seed, code_hash, param_hash, llm_ledger_hash, weights_hash, schema_version, view_render_spec_hash, lineage_class, parent_ref)` —— **没有 `basemap_hash`** |
| `spec-llm-boundary §8.1 推论` | `(world_seed, kernel_hash, config_hash, ledger_hash)` |
| `spec-validation §10.9` | `(world_seed, kernel_hash, param_hash, basemap_hash, llm_ledger_hash)` —— **没有 `lineage_class`** |

canon 种子：

| 出处 | 公式 |
|---|---|
| `spec-causality §10.3` | `BLAKE3("civsim-canon" ‖ kernel_version ‖ param_hash)[0..32]` |
| `spec-validation V11` | `BLAKE3("canonical" ‖ kernel_hash ‖ basemap_hash ‖ param_hash)[0:8]` |
| `DECISION-REGISTER A33` | `sha256(kernel_version ‖ "canonical" ‖ k)`，`k = 0..N−1`（**是一个集合**，register §5.8 明确把"canon 是集合不是单线"作为自己的裁决） |

三个公式用了不同的哈希函数、不同的输入、不同的输出长度、不同的基数（单条 vs 集合）。

**为什么这是实质冲突**：
1. `spec-causality §2.1` 的核心设计是"**`lineage_class` 进身份哈希**，使 lab 线在数据模型上不可能被改名为 canon"。`spec-validation V11` 把 canon/lab 单向阀列为**写第一行代码前必须签字的 11 项之一**，却在 §10.9 用了一个不含 `lineage_class` 的身份定义 —— 按它自己的定义，单向阀不成立。
2. `spec-causality` 的身份**漏掉 `basemap_hash`**。有人会说 basemap 可由 `world_seed` + 扰动算子重算（world-state D11 确实是这样设计的），但 world-state §4.2 同时规定 1 km 静态预计算的输出"**量化为定点整数并内容哈希后冻结为数据资产，进 `basemap_hash`**" —— 那是一个**外部数据工件**，不可从种子重算。漏掉它意味着换一版 1 km 底图不会改变世界线身份。
3. `spec-causality` 的 `param_hash` = "全部**自由参数**的规范序列化"，暗示点值；`spec-world-state §7.4` 明写"**不存在'默认参数值'这个东西**，`params.toml` 里存的是先验分布"。两者哈希的不是同一个对象。

**建议裁决**［本文原创，D 级］：取 causality §2.1 的九元组作为基底，做三处修正 ——
- 加 `basemap_hash`（覆盖不可重算的 1 km 数据资产）；
- `param_hash` 改名 `param_prior_hash`，明确哈希的是先验族与 `evidence_level` 标注，不是实现值；
- canon 种子统一为 `DECISION-REGISTER A33` 的**集合**形式，但换成 BLAKE3 并把 `basemap_hash` 纳入：`seed_k = BLAKE3("civsim-canon" ‖ kernel_hash ‖ param_prior_hash ‖ basemap_hash ‖ u32(k))`，`k = 0..N_ensemble−1`。

**裁错了最早在哪看出来**：两条本应不同的世界线算出同一个 `WorldLineId`；或者换了一版底图数据资产之后旧结论没有作废。

---

#### C3 · 读取集：三种粒度、一个不存在的字段、以及一个从未出现在 L0 接口里的读屏障

这是任务点名的"状态表示与因果记录的耦合"，也是四条冲突里最贵的一条。

| 出处 | 规定 |
|---|---|
| `spec-world-state §1.2 R4` | 每个原语在 `PRIMITIVE_REGISTRY` 声明 `reads[]/writes[]`（**字段级**，即 `(entity_kind, field_id)`），构建期静态分析结果必须与声明**完全相等**（不是包含）。理由逐字："**多声明的读集会污染 `pseudo-simulation F3` 的读取集闭包差集检测**"。 |
| `spec-causality §3.2` | Tier-D 静态读签名，类型是 `(entity_kind, field_id)`，"**不是** `(entity_kind, entity_id, field_id)`"，编译期、零运行时成本；**CI 强制运行时访问签名之外的字段 = 硬失败（"读屏障在内核里，不是外挂"）**。实例级读取集只在 Tier-S 哨兵（采样率 1e-3）与 Tier-R `--taint` 里存在，且 **Tier-S 在类型层被禁止用于任何归因**。 |
| `DECISION-REGISTER A30` + §5.2 裁决第 2 条 | "≤64 项 `(entity_kind, entity_id, field_id)` 三元组……**对全部实体级事件开启**"。（该表自己把它称作"变量级"，但字段里带 `entity_id`，实际是实例级 —— register 内部就不自洽。） |
| `spec-validation §13.2` + §10.7 SPIKE-3 | 每次提交跑"读取集差集 `declared \ measured == ∅`"；`--spike` main 的必过项 SPIKE-3 = "**因果图非空且 `declared_causes \ read_set_closure == ∅`**"。 |

三个问题叠在一起：

**(a) `declared_causes` 在 causality 的架构里不存在。** `spec-causality §3.1` 的关键观察逐字是："`pseudo-simulation F3` 的反作弊器，在'禁止手写 `emit_event()`、schema 里根本没有 `causes[]` 字段'的前提下，**没有东西可查**"；§4.1 与 §3 的禁令表把 `causes[]`、`reason`、`sigma_declared` 全部列为 schema 级不存在。**所以 `spec-validation` 的 SPIKE-3 与 §13.2 那条每次提交的 CI 门禁，按 `spec-causality` 的 schema 是无法实现的**（差集的被减数没有类型）。这不是措辞差异：SPIKE-3 是 `--spike` main 的三条必过项之一，而 `red_main_days ≥ 7 ⇒ 全项目其他工作暂停` 是宪章条款。

**(b) 粒度三选一没有裁决。** 变量级（causality Tier-D，零成本，过近似）/ 实例级常开（register A30）/ 实例级抽样（causality Tier-S）。这决定存储：实例级 ≤64 项 × 全部实体级事件常开，按 causality §3.3 的写次数量级（1.88e6 写/年）就是每年 1.2e8 项，3000 年 3.6e11 项 —— 这正是 causality 用来否决写入级 provenance 的那个数量级。**A30 的默认值与 causality 的裁决在存储上差三个数量级。**

**(c) 受控访问器/读屏障从未出现在 `spec-world-state` 的 L0 接口里。** causality §3.2 要求"读屏障在内核里"，Tier-R 要求动态数据流追踪。而 world-state §2.3 给出的是**裸结构体 + 公开字段**（`Cell { soil_n : NDens_g_m2 [hot], ... }`），`[hot]/[cold]/[idx]` 是快照与内存布局标注，不是访问控制。要让"运行时访问签名之外的字段 = 硬失败"成立，每一次字段访问都必须经过一个带机制上下文的访问器 —— **这改变内核每一个读写点的形状**，而且它与 world-state §6.3 允许的"对格的纯 map 并行 + SIMD"直接对冲。

**(d) 这笔开销没有进任何预算表。** causality §3.2 自己标注 taint 开销 2–20× 是"[记忆，未核实]"，并逐字说"**⚠ 本项目必须自测这个数，它是 §12 预算表里唯一没有实测锚点的乘数**" —— 而 §12 在文件里**不存在**（见 §3 缺口清单）。`spec-validation §10.3` 的复杂度契约表 12 行里没有任何一行是读屏障或 taint。

**建议裁决**［本文原创，D 级］：
1. **`spec-world-state` 必须升 v0.2，加一节「受控访问接口」**：L0 字段不得被裸结构体字段访问，一切读写经 `ctx.read::<F>(entity)` / `ctx.write::<F>(entity, v)`，`ctx` 携带 `mechanism_id`；R4 的静态相等检查在这个 API 上做。这是本审查认为**唯一真正改变内核最底层接口**的裁决，必须在写第一行代码前定。
2. **粒度**：常开层 = causality 的 Tier-D 变量级静态签名（零成本）；实例级 = Tier-S 哨兵抽样（0.5 GB/跑）+ Tier-R 按需 `--taint`。**否决 `DECISION-REGISTER A30` 的"实例级常开"**，理由是 causality §3.3 的存储算术，register 自己也引用了同一份算术来否决写入级 provenance。
3. **删掉 SPIKE-3 里的 `declared_causes`**，改写为可实现的形式：`SPIKE-3' := read_set_closure(e) 非空 ∧ Tier-S 哨兵抽样与 Tier-R 重算的读取集集合相等`。保留 `pseudo-simulation F3` 的核心禁令（手工声明的原因只能作为独立字段里的"待检验假设"），但它作用在 L2 归因报告的 `candidates` 上，不作用在内核 schema 上。
4. **taint 开销必须在 M1 实测**（见 §5），在实测数之前，§10.3 的复杂度契约表不得签字。

**裁错了最早在哪看出来**：第一次要回答"这个格的粮储为什么掉了"时发现要重跑；或者读屏障加上去之后格扫从 350 ms 涨到 3 s，然后有人提议"先把读屏障关掉"。

---

#### C4 · 相位顺序、Intent 延迟、以及一条没注册的随机流

`spec-llm-boundary §9.1` 已经自己点出这条并要求 `spec-world-state` 升版 `PHASE_ORDER_V2`：V1 的相位表允许 `propose`（order 3）写 Intent 队列、`material`（order 5）在**同一 tick** 读它，那会把 LLM 放上关键路径（`computational-feasibility F5` 明令禁止）。llm 追加的一条更重要：**规则 Intent 与 LLM Intent 必须走同一延迟**，否则 LLM-off 孪生线的所有反应快一年，`event_rate_ratio` 会测到一个纯粹由调度产生的差异，"**而它长得和污染一模一样**"。

本审查追加两条 llm 没提的：

**(a) Perception 的时点也不一致。** world-state §5.3 的 `sense`（order 2）在**本 tick** 构造 Perception，`propose`（order 3）读它；llm §2.1 的生命周期写的是 `propose` 读**上一 tick** 的 View。两者对"agent 看到的是哪一年的世界"给出不同答案，而这直接决定信息边界的一年宽度。

**(b) `opportunity/c` 流没有注册。** llm §2.1 用 `CBRNG(stream=opportunity/c, ctr=(t, actor, slot, 0))` 决定决策点是否存在 —— 这是整套 LLM 边界设计的地基（"不存在决策点"那一步）。而 world-state §6.4 的流分配表是**封闭注册表**（25 条，加一条 = 内核版本变更），里面没有 `opportunity/*`。world-state 的禁令逐字："禁止未注册的 RNG 流"。llm 的 C1-2 记得申请 `worldgen/phonology`、`lang/change` 两条，**漏了它自己最依赖的这一条**。

**建议裁决**：接受 llm C1-1（升 V2、同延迟），并在 V2 里同时把 `sense` 的输出明确为"供下一 tick 的 `propose` 使用"；流表加 `26 worldgen/phonology`、`27 lang/change`、`28 opportunity/<class_id>`（按决策类展开为子路径，`H64(stream_path)` 天然区分）。这三处必须在 t=0 之前完成 —— world-state §5.3 的禁令是"未经 `PHASE_ORDER_V*` 版本升级 + **世界作废重跑**而改动相位顺序"。

---

#### C5 · "site" 有三个互不相容的意思，而且三个都进哈希

| 出处 | `site` 指什么 |
|---|---|
| `spec-world-state §2.3.5` | 地理位点，创生冻结，`site_id = H128("v1/site" ‖ cell_id ‖ site_index)`，每格 ≤16 个 |
| `spec-llm-boundary §2.2` | 决策点，`DecisionSite.site_id = H128("site" ‖ tick ‖ actor_id ‖ slot_id)` |
| `spec-causality §2.7 / §7.2` | 抽样点，`DrawSite`、`SiteRef`；安慰剂合格集 `E(I)` 里同时出现 `s'`（抽样点）与 `cell(s')`（它所在的格） |

三者都是 `H128`，都叫 `site_id`/`SiteRef`，都出现在 schema 里，并且 llm 的域前缀字面就是 `"site"`（world-state 的是 `"v1/site"`，只差一个版本前缀）。这不是命名洁癖问题：`spec-causality §11.2` 的 `T-ISOLATION` 判据里"B 上每个 DrawSite 的 (counter, u, outcome, fired) 逐位相同"与 world-state 的"位点集是 `basemap_hash` 的一部分"会在同一个索引里打架。

**建议裁决**：`Site`（地理）保持不变；llm 的改名 `DecisionPoint` / `decision_point_id`，域前缀 `"v1/dp"`；causality 的改名 `DrawPoint` / `DrawRef`，域前缀 `"v1/draw"`。零成本，现在改。

---

### 组 B —— 确定性契约与 LLM ledger 的一致性

#### C6 · 确定性门禁没有按运行模式分账，因此在 `MODE_FULL` 下集体不可满足

`spec-llm-boundary §8.1` 的结论是硬的：温度 0 不保证确定性（零匹配输出比例 47.56%–75.76%，A 级）；当前前沿模型**已移除** `temperature/top_p/top_k` 且没有 `seed`；因此"**不可能通过重新调用模型来重放历史**"，"世界的确定性"必须重定义为"给定 `(world_seed, kernel_hash, config_hash, ledger_hash)` 四元组的确定性"。

而 `spec-world-state §6` 整节（确定性契约）与 §11.3 的 CI 总表**一次都没有提到 ledger**。它的门禁写成无条件的：

- 跨机器不变性：≥2 种 CPU 架构逐位相同，**每日**；
- 线程数不变性 1/4/16 逐位相同，**每次提交**；
- T-ERASE / T-ITERORDER / T-NULLINT / T-ISOLATE 全部"逐位相同"，**每次提交**。

`spec-validation R2/R3` 更把它们提到 **HALT** 级（"改变线程数 / 容器迭代顺序 / 机器架构导致输出不同 ⇒ HALT"）。

**在 `MODE_FULL` 下这些门禁全部不可满足**：Class-1 自托管推理即使开了 batch-invariant kernel（llm §8.3 引用的是 C 级单来源博客），也不保证跨 CPU/GPU 架构逐位一致；`T-LLM-NOISEFLOOR`（llm §8.4）明确要求测"同 seed 同配置跑两次"的**非零**差异，并预言"**这个数字很可能比人们预期的大**"。也就是说：llm 规格要求测量的那个量，正是 world-state/validation 规定为 HALT 的那个现象。

**建议裁决**［本文原创，D 级］：把运行模式写进每一条门禁的适用域，形成一张小表 ——

| 门禁 | MODE_HEADLESS | MODE_REPLAY | MODE_COUNTERFACTUAL | MODE_FULL |
|---|---|---|---|---|
| 线程数 / 迭代顺序 / 跨机器 逐位不变 | 必过 | 必过 | 必过（分叉点前） | **不适用** |
| T-ZERO / T-ISOLATION / T-NULLINT / T-ERASE | 必过 | 必过 | 必过 | **不适用** |
| 守恒审计 int64 精确相等 | 必过 | 必过 | 必过 | **必过**（它与 LLM 无关） |
| `T-LLM-NOISEFLOOR` | 不适用 | 不适用 | 不适用 | 必测并公布 |

并在 `spec-world-state §6` 开头加一句规范文本：**"本节的一切保证以 `ledger_hash` 为条件；`MODE_FULL` 不在本节的保证范围内，它只保证 ledger 被完整写下。"** 这句话现在不写，第一次 nightly 跨架构测试红掉时会有人去关测试，而不是去分模式。

**裁错了最早在哪看出来**：跨架构 nightly 长期挂红并被加进忽略列表；或者有人为了让它绿而把 Class-1 调用改成托管 API 的固定缓存（那等于放弃可反事实性）。

---

#### C7 · `proposal_log` / `ledger` 是同一个 A 档工件的两个名字，且都没有 schema 归属

`spec-world-state §3.3`（T-ERASE 输入）、`spec-validation R2/§4.6`（"同一 `(state, seed, proposal_log)` 重放"）用 `proposal_log`；`spec-causality` 与 `spec-llm-boundary` 用 `ledger`。`spec-llm-boundary §8.2` 给了完整的 `LlmCallRecord` schema，是四份里唯一一份定义了它的。`spec-causality §10.4` 只给它留了 45 MB/线的位子，`spec-causality` 全文没有 ledger 的 schema，但 `T-ZERO`（§11.1）与 `T-ISOLATION`（§11.2）都把"LLM 账本命中序列（key 序列与 hit/miss 序列）逐位相同"写进判据 —— 判据引用了一个它没有定义的对象。

**建议裁决**：统一为 `ledger`，schema 以 `spec-llm-boundary §8.2` 为准，`spec-world-state` 与 `spec-validation` 把 `proposal_log` 全部替换。`spec-causality` 的 T-ZERO/T-ISOLATION 判据里的"账本命中序列"必须指明是 `(call_key, hit/miss)` 的有序对序列，且明确 `call_seq` 不参与（llm §8.2 已写"仅用于审计与排序，**不用于寻址**"）。

---

#### C8 · ledger 键算在哪里，两份规格互指对方为前提

`spec-llm-boundary` 裁决 **L12：键只含结构化 View，不含渲染后的 prompt 字节**，并在附录 C.2 的冲突 C2-1 里逐字写："若 `spec-causality` 坚持 `provenance-replay-counterfactual M5` 的写法（键含 prompt 字节），则 §6 的置换不变性检验必然失败且 §7.2 的粗化函数失去意义。**这是一个不可逆决定，必须两份规格达成一致后才能写第一行 ledger 代码。**"

`spec-causality` 没有回应 —— 它全文没有 ledger 键的规定。所以这条**没有闭合**，而它是 llm 自己标记为不可逆的。

**建议裁决**：采纳 L12。附带三个必须同时落地的推论：(i) `view_render_spec_hash` / `coarsening_version` 进世界线身份（causality §2.1 已有，保留）；(ii) `rendered_prompt_hash` 作为非键审计字段落盘，`render_drift` 计数进 manifest（llm §8.2 已写）；(iii) `spec-causality §11.1` 的 T-ZERO 判据必须显式说明它检验的是 `call_key` 序列而不是 prompt 字节序列，否则换一版转写表就会让 T-ZERO 假红。

---

### 组 C —— 「事件」这个概念

#### C9 · 四份规格对"事件"给出四个不兼容的定义，并且各自的验收判据建立在自己的那个定义上

| 出处 | "事件"是什么 | 什么时候存在 | 数量级 |
|---|---|---|---|
| `spec-world-state §5.3` | 内核里不存在 `Event`；但相位 9 `record` 的职责包含"**事件提名**" | **本 tick 内** | — |
| `spec-causality §4.1/§5` | `Event` = 某次机制转移的可选物化（`event_id = H(world_line_id, tick, phase, seq, write_set_root)`）；提名由 `significance` 泛函自动做 | **提名延迟至 Δ_max = 200 年后的批作业**，在覆盖 `[t, t+200]` 的分叉格完成后运行 | 转移 ~10⁶/年；**提名 500/年，由配额（分位点）定义** |
| `spec-llm-boundary §4.2/§4.4/§4.5` | 事件 = 按**决策类**可计数的行动实现（`events_c/世纪`、`Fano = Var(N_century)/E(N_century)`、`event_rate_ratio = f_on/f_off`） | 在线，按世纪结算 | 按决策类分层 |
| `spec-validation §5.1/§5.2` | `EventCandidate { actor_id, action_type, targets, rng_key }`，在**裁决之前**过五闸门 G1–G5 | 裁决前，逐事件 | 每个候选动作 |

四个后果，每一个都是实现级的：

**(a) world-state 的相位 9 与 causality 的延迟提名不兼容。** 相位 9 在本 tick 内做不了需要未来 200 年的提名。要么 world-state 的相位表删掉"事件提名"（留"读取集摘要 + 快照根哈希"），要么 causality 放弃延迟提名 —— 而 causality 明确说延迟提名是它解开 `causality-bookkeeping F2(a)` 那个死结的唯一办法。**应当删 world-state 的那一项。**

**(b) 配额定义的提名集使一大批事件率判据在数学上失去意义。** causality §5.2 逐字："θ 由**配额**定义而非绝对值 —— θ = 使提名率等于预算的分位点。默认预算 **500 提名事件 / 模拟年**"。也就是说**被提名的事件数每年恒为 500，与世界发生了什么无关**。于是：

- `spec-llm-boundary §4.3` 的 `event_rate_ratio = f_on/f_off ∈ [0.8, 1.25]` —— 若 f 在提名集上算，恒等于 1；
- `spec-llm-boundary §4.5(b)` 的 `Fano factor ≥ 2.0` —— 若 N 是每世纪提名事件数，恒等于 0（方差为 0）；
- `spec-validation R20` 的"战争/政权更替/宗教诞生的时间间隔分布 CV < 0.5 ⇒ INVESTIGATE" —— 同上；
- `spec-validation §6.2` 的 `novel_combination_rate` 也依赖"事件"的计数口径。

这些判据显然本意是算在别的东西上（多半是 `ResolvedIntent` 中 `a* ≠ NOOP` 的实现动作，按 `class_id` 分层）。**但没有任何一份规格写下这一点。** 这是一个会让一整组污染判据在实现时被随手接到错误的计数器上的缺口。

**(c) validation 的 `action_type` 与 causality 的 `EventType` 禁令冲突。** `spec-causality §5` 禁令逐字："**禁止 `EventType` 枚举与效果函数库动词**"；`spec-world-state §2.4` 把阶段/类别枚举列入 AST 黑名单。而 `spec-validation §5.2` 的 `PRECONDITION_TABLE[cand.action_type]`、G5 的"每个动作类型声明一个最小完成时间下界"、G4 的 `D-G4-2`（逐字："若'**战争**'事件的残差系统性高于其他类型"）都需要一个语义事件类型表，而且五闸门是**内核内的硬失败**，所以这个表住在内核里。

可以调和的部分：如果 `action_type` 严格等同于 `PrimitiveVerb`（P1–P10，world-state §1.3 的封闭集合），那它是合法的 primitive 枚举。但 G4 的"战争"不是 P1–P10 里的任何一个（战争是 P1/P3/P8/P9 的时空聚类，world-state §1.4 F8 明确把它判为 composite）。**所以 validation §5.2 的一部分闸门要求内核读 composite 标签**，那是 world-state R3 的构建期错误。

**(d) 闸门"硬失败"的语义没有定义，且与 llm 的失败处置冲突。** `spec-validation §13.2` 把 G2/G3 列为"每事件 / 硬失败"，`spec-validation §5.2` 的代码写 `return HardFail(...)`。这到底是"该动作被拒绝、世界继续"还是"运行中止"？若是前者，它是一个作用在动作空间上的过滤器 —— 而 `spec-llm-boundary §2.2` 已经把可行性预检放在枚举器里（`Option.feasible`，不可行项不进 `A`），§2.8 规定"**一切调用失败的处置是从 π 采样**"。同一件事有两套处置。若是后者（中止），一次合法的不可行提议会杀掉一条 3000 年的长跑。

**建议裁决**［本文原创，D 级］：写一份一页的《事件词汇裁决》，定义四个**不同名字**的对象，禁止互相替代 ——

| 名字 | 定义 | 住在哪 | 谁用 |
|---|---|---|---|
| `Transition` | 一次机制写入（causality 的 `Event`，改名） | L1，重算 | 因果、读取集 |
| `Nomination` | `significance` 泛函按配额提名的 `Transition` 子集 | L2，派生工件 | 归因报告、快照锚点、`Scope(t)` |
| `Act` | `ResolvedIntent` 中 `a* ≠ NOOP` 的实现动作，带 `class_id` 与 `PrimitiveVerb` | L1，可计数 | **全部事件率/间隔/Fano/CV/β̂ 判据的唯一分母** |
| `Occurrence` | 观察层检测器在 `Act` 流上做时空聚类得到的复合体（"一场战争"） | L2，`COMPOSITE_LEXICON` | 叙事、P-WAR-*、G4 的类型分层 |

并据此：world-state 相位 9 删掉"事件提名"；validation §5.2 的五闸门输入改为 `(&L0Snapshot, Act{actor, verb: PrimitiveVerb, args, rng_key})`，`PRECONDITION_TABLE` 以 `PrimitiveVerb` 为键；G4 的按类型分层改在**观察层**对 `Occurrence` 做（它本来就是分布性判据，不需要在内核里做）；G1–G3 的硬失败明确为"拒绝该 `Act`，回落到 llm §2.8 的 π 采样，并计入 `gate_reject_rate`（分闸门、分决策类，是必须公布的指标）"，**只有守恒审计与并发占用（A1/A2）才是运行中止**。

**裁错了最早在哪看出来**：`Fano factor` 恒等于某个与世界无关的常数；或者有人在内核里加了一个 `enum ActionKind { War, Reform, ... }` 并说"这只是给闸门查表用的"。

---

### 组 D —— 分辨率 / tick 决定与算力预算是否自洽

#### C10 · 算力四方分账有三个互不相容的版本，且权威归属自相矛盾

| 出处 | 分账 |
|---|---|
| `spec-validation V14` / §10.2 | 模拟 20% : **验证 50%** : 因果 25% : LLM 编排 5% |
| `DECISION-REGISTER §5.6`（该表自称是这条冲突的裁决） | 模拟 30% : 验证 35% : 因果 25% : LLM 10% |
| `spec-causality §1` 第 11 行 | 模拟 25% : 验证 50% : 因果 **20%** : **重算债务 5%** |

三个版本、三组数字，且 causality 引入了第四个账户（重算债务）而 validation 没有。更麻烦的是权威：`DECISION-REGISTER §0.3` 逐字规定"**两份文件冲突时，以本表的冲突章节（§5）为准提交人裁决，不许各自实现**" —— 按这条，`spec-validation V14` 不具权威性；但 V14 又被 validation 自己列为"写第一行内核代码之前必须签字的 11 项"之一。

**建议裁决**：这是 register §5.6 明确标 `裁决人 = 人` 的条目，必须由项目所有者签一个数。本审查的建议是取 **validation V14（20/50/25/5）+ causality 的重算债务账户**，即 **模拟 18% : 验证 50% : 因果 25% : LLM 编排 4% : 重算债务 3%**［本文原创，D 级］，理由是：`emergence-verifiability F15` 的"验证 ≥50%"是三方里唯一有独立论证的下界（消融矩阵 10,500 次长跑的算术），而重算债务在 causality §9.3 有一个具体的仪表盘挂钩，不给它账户它会从验证里挤。同时把 `DECISION-REGISTER §5.6` 标为"已被 V14 取代"，并修订 §0.3 的权威条款（见 C16）。

---

#### C11 · 一次"为什么"的标价差 5–9 倍，而这决定纲领核心承诺的量级

| 出处 | 标价 | 年产能 |
|---|---|---|
| `spec-causality §1` 第 11 行 | **1,100 CPU 小时** @ T_run=1h（"推导见 §12.1"） | **~200 个/年** |
| `spec-validation §10.2` | **5,000–10,000 CPU-h**（含安慰剂 100 次 + 20 候选原因 × 326 次重放） | **28–55 个/年** |

**而 causality 的 §12.1 在文件里不存在**（文件在 §11 结束，见 §3）。所以那个 1,100 无法被核对。

纲领第 24 行的承诺是"可以查询任何重大事件的因果链"。`spec-validation §10.2` 已经把诚实表述写好了："每个'为什么'问题的标价是 5,000–10,000 CPU 小时，因此我们一年能严肃回答大约 30–50 个问题，必须挑。" 这句话是 30 还是 200，是两个不同的项目。

**建议裁决**：在 causality 补上 §12.1 的推导之前，**以 validation 的 5,000–10,000 CPU-h 为准并写进对外表述**；把 causality 的 1,100 标为"未推导，暂不采信"。M1 必须实测其中最大的那个乘数（taint 开销，见 C3(d)）。

---

#### C12 · 三份算力/存储预算表建立在已被 `spec-world-state` 取消的本体与被否决的网格上

**(a) `spec-causality §3.3` 的"假设集 A"**逐字："主格 **25 km 六边形 19,200 格** × 40 动态字段；……**聚落 ≤5,000**"。而 `spec-world-state D6` 裁决 H3 res 5、约 **1.40×10⁵ 格**（8.4×10⁴ 陆格），§2.3.5 **取消了 `Settlement` 实体**（逐字："**没有 `Settlement` 实体**"）。causality 的全部存储数字（单快照 60 MB、参考线 12 GB、200 条集合 273 GB、快照配额 ≤140 张）都建立在这套已被否决的假设上。

按 world-state §2.6 的实测口径重算：热态合计 **≈650 MB**（不是 causality 假设的裸 177 MB），压缩 3× ≈ **217 MB/快照**。于是 causality §10.2 的快照配额表变成：140 张 × 217 MB = **30.4 GB**，而它自己的硬上限是"参考线 ≤ 30 GB"，且配额表里写的是"≤ 12 GB / 参考线"。**快照一项就吃光整条参考线的存储上限**，年度聚合 1.2 GB、分叉格摘要 16 GB、哨兵 0.54 GB 全部无处安放。

**(b) `spec-validation §10.3` 的复杂度契约表**有一行是"制度/文化/宗教 | 5 年 | **O(polities × cultures)** | **政体 ≤ 200、文化 ≤ 100**"。`Polity` 与 `Culture` 在 `spec-world-state §2.4` 的禁止字段黑名单里（"回溯性史学建构对象"行，逐条列出 `Polity`、`Culture`、`Religion`）。§10.9 还有"**聚落事件 15 GB**"。**复杂度契约表用不存在的实体做代价函数的自变量与截断常数。**

**(c) 格扫份额的修订从未传播。** world-state §4.2 把气候+农业从 `computational-feasibility` 原表的 5%+10%=15% 改到 **7.8%+19.8%=27.6%**，并逐字说明"从哪里买回来"：低频气候改 O(1) 纯函数省 3%、取消 Voronoi、"**剩余约 11% 从'贸易 12%'与'制度/文化/宗教 5%'中扣**"。`spec-validation §10.3` 的表**仍然是** 气候 5% / 农业 10% / 贸易 12% / 制度 5%，并自称"合计 100%"。两张表都声称是那份签字预算表。

**(d) 预算表缺项。** §10.3 的 12 行里没有：每 tick 的守恒审计（全物质 × 全持有者 × 三个守恒量，world-state §2.5）、InfoCopy 的年度衰减批处理（上限 5×10⁶）、12 条文化通道的每 tick 现算（llm §6.3：2×10⁵ Actor × 12 个 `fn`，每个 `fn` 要聚合该 Actor 可达的 InfoCopy 多重集 —— llm 声称"可忽略"的估算只算了 2.4×10⁶ 次求值，没算可达集聚合）、读屏障/taint（C3）、View 粗化与渲染。

**建议裁决**：**在 M1 的空壳内核基准出数之前，冻结全部三张预算表，禁止任何一份规格引用它们的具体数字。** M1 的交付物之一就是一张**唯一的**《复杂度契约与存储预算表 v1》，其每一行的自变量必须是 `spec-world-state §2.2` 实体总表里真实存在的实体种类，且必须有 owner 签字（validation §13.3 交付物 14 已经要求这一点）。causality §3.3/§10.2/§10.4 与 validation §10.3/§10.9 整体作废重写。

**裁错了最早在哪看出来**：第一次 1000 年长跑时磁盘爆掉，团队的反应是"先关掉细粒度快照"（`DECISION-REGISTER §5.2` 已经预言了这个症状）。

---

#### C13 · `T_run` 没有按模式分账，而三份规格的推导都把它当成模式无关的常数

- `spec-validation V14`：`T_run ≤ 1 小时`（括号里写"不含 LLM"）。
- `spec-causality §10.2`：用 `T_run ≤ 1h / 3000 tick ⇒ 1.2 s/tick` 推出主锚点间隔 50 年，并写"若 `T_run` 退化到 10 h，间隔必须缩到 20 年，快照张数升到 150 ⇒ 触发上限 ⇒ **构建失败**"。
- `spec-llm-boundary §9.5`：`MODE_FULL` 下 ensemble 的墙钟 = 3000 批 × `T_batch`；`T_batch = 5 min ⇒ **250 小时 = 10.4 天**`。

也就是说：同一条 3000 年世界线，`MODE_HEADLESS` 是 1 小时，`MODE_FULL` 是 250 小时。causality 的锚点间隔推导按"最坏重放一个间隔 = 60 秒"做的，在 `MODE_FULL` 下这个数是 250 分钟。**而 causality 已经把"T_run 退化"写成构建失败。**

附带一条：`spec-llm-boundary §9.5` 逐字说"**扩大 ensemble 是免费的墙钟优化**……批处理规模在限额内应当取到最大"。这只对 LLM 墙钟成立 —— CPU 侧是线性增长的，`N = 1000` 就是 5 倍的 CPU 预算，而 `N_ensemble` 是 `DECISION-REGISTER A1` 明确的"所有其他数字的父节点"。llm 的这句建议如果被照做，会直接击穿 validation 的模拟账户。

**建议裁决**：把 `T_run` 拆成 `T_run_headless ≤ 1 h`（用于全部预算推导、锚点间隔、复杂度回归门）与 `T_wall_full`（`MODE_FULL` 的 ensemble 墙钟，单独立项，由 `T_batch` 实测决定，llm 附录 A O8 已经把它列为"Phase 1 第一周就能做完"的实验）。causality §10.2 的"T_run 退化 ⇒ 构建失败"只对 `T_run_headless` 生效。llm §9.5 的"免费"一句加限定：**"对 LLM 墙钟免费，对 CPU 预算不免费；`N_ensemble` 的变更是 A1 级决定。"**

---

### 组 E —— 验证体系要求的算力、以及判据在这个世界上是否可用

#### C14 · 涌现认证是**按范畴**计价的，而预算表按"一次"计价，差 6–9 倍

`spec-validation §4.4`：`臂集合 = { baseline } ∪ { 单机制关闭 : m ∈ M } ∪ { 预先声明的 k 个二元组合 }`，`|M| ≤ 20`、`k = 6`，**每臂 = N=50 种子 × NROY 10 点 = 500 次长跑** ⇒ 27 臂 × 500 = 13,500 次 ⇒ **13,500 CPU-h**。

§10.2 把它列为"一次全尺度涌现认证 13,500 CPU-h，validation 预算下 ≈3.4 次/月，实际按季度做 1 次"。

但 §4.1 说得很清楚：**认证对象是一个由观测器识别的宏观范畴 `C`**。`COMPOSITE_LEXICON`（world-state §3.1）已经列了 6 个（polity / settlement / aristocracy / state / dynasty / war），`spec-llm-boundary §8.5(e)` 的 `T-HEADLESS-REACH` 列了 9 个以上（追加 market / scriptural_religion / literacy）。**每个范畴一份证书 ⇒ 一轮认证 81,000–121,500 CPU-h ⇒ 1.8–2.6 个月的全部验证预算。**

而验证账户同时还要养：诱饵 nightly（≈1,440 CPU-h/月）、里程碑全尺度诱饵（400）、零模型全尺度（1,400）、自主性管线（world-state §8.4.2 的 800 次长跑 = 800 CPU-h/版本）、对抗式敏感性（玩具 100）、HM 校准（≈600）、模式电池、功效分析。

**建议裁决**：在 Phase 1 的验收集里**预注册最多 3 个被认证的范畴**（本审查建议：`c:settlement_cluster`、`c:control_hierarchy`、`c:scriptural_practice` —— 分别覆盖空间、政治、信息三条主线），其余进观察集；并把"每范畴 13,500 CPU-h"写进 §10.2 的表，而不是"一次"。`|M| ≤ 20` 与 `N=50 × NROY 10` 两个乘数一旦要动，必须同时给出新的年度认证轮数。

---

#### C15 · `spec-validation` 的复杂度契约表里有两条退化规则违反它自己和 world-state 的禁令

§10.3 的"超出时的退化行为"列：

- **"人口 L2 个体 …… 按重要性打分驱逐（降级回队列）"** —— `spec-world-state §2.4` 的黑名单有一整行是 "LOD 相关：LOD 调度器读取'事件密度/重要性/年份/是否存在国家'的任何字段"；`DECISION-REGISTER A17` 逐字"**禁止读取任何重要性/戏剧性/事件密度变量**（写成 lint：LOD 调度器模块不许 import 事件系统）"；`spec-validation` 自己的 L-ABS-1 把 `significance` 限定在 observer crate、L-ABS-2 规定 observer 的返回值到达内核写入路径即**运行时中止**。
- **"事件日志写入 …… 超出时提高 significance 提名阈值（记录阈值变化）"** —— 同上；而且更糟：它让**提名流依赖机器负载**，于是 `T-ERASE` 判据 (b)（"事件提名流相同"，world-state §3.3）在不同机器/不同负载下就不可复现。

**建议裁决**：两条退化规则删除。L2 个体超限的合法退化只能读结构量（A17 允许的：控制的劳动/粮食份额分位、网络中介中心性、组织层级数、人口规模），并且必须配 A17 要求的 **1% 随机提升对照组**与 LOD 不变性检验 —— 而这两样东西**四份规格里一份都没有写**（见 §3）。事件日志超限的合法退化是**硬中止 + 报告**，不是自适应阈值。

---

#### C16 · `spec-world-state §7.4` 的"证据等级闸门"是一个以绝对年份为参数的本体开关，并且它让玩具世界的"全部机制开启"恒假

`spec-world-state §7.4` 逐字：**"在 `tick < 2000` 期间，只有 A/B 级证据支撑的机制生效；C/D 级机制的对外接口返回'不存在/无效应'。"**

三个后果：

**(a) 它本身是被禁止的形态。** `DECISION-REGISTER A16` 的禁令逐字："**禁止任何以年份或政体存在与否为参数的本体切换**"；`spec-validation §6.4 L-ABS-4` 的叙事节拍变量禁令列了"这个王朝已经 K 代了"这一类。一个在 `tick = 2000` 打开一批机制的闸门，是教科书式的隐藏阶段门 —— 它甚至比 `if year > Y: spawn_state()` 更隐蔽，因为它伪装成方法论纪律。

**(b) 它让 CI 玩具世界的定义性要求恒假。** `spec-validation §10.6` 逐字："机制：**全部机制开启**（不是简化机制——这是本规格与'简化玩具'的关键区别）"。basin600 的 PR 门跑 300 年，nightly 跑 3000 年。在 `tick < 2000` 的窗口里，C/D 级机制**全部关闭**。于是：诱饵世界标定（§2）、零模型增益报告（§3）、功效分析（§13.3 交付物 15）、判据标定报告 —— **全部在一个 C/D 机制不存在的世界上做**，然后把标定出来的阈值用到 `t > 2000` 的全跑上，那时机制集合已经变了。这直接违反 §2.2 的规范"所有诱饵世界与真内核共享……**唯一的差别在机制层**"，因为真内核在两个时段是两个机制集合。

**(c) 它与 llm/validation 的阈值体系冲突。** llm 附录 A O4 承认"本文的全部阈值几乎都是 D 级"；validation §12.3 第 36 项逐条列了自己的 D 级阈值。如果 D 级机制在前 2000 年不生效，那么前 2000 年的世界是一个由 A/B 级机制组成的、我们从未设计过的世界。

**建议裁决**［本文原创，D 级］：**取消"以 tick 为参数"的闸门形式，改为"以世界线配置为参数"** —— 每条世界线在 t=0 冻结一个 `evidence_gate ∈ {AB_ONLY, ALL}`，写进 `param_prior_hash` 与运行登记表，全程不变；`AB_ONLY` 与 `ALL` 是两个**分账的集合**，`mandate-contradictions F12` 想要的"不要让 D 级机制主导早期结论"通过**对照两个集合**来实现，而不是通过一个中途翻转的开关。这样它就变成一个零模型式的机制开关（`MechanismSwitches`，validation §3.3 已经要求"只在 t=0 读一次"），而不是阶段门。

**裁错了最早在哪看出来**：所有种子的宏观曲线在 `t = 2000` 附近出现同相位的折点 —— 而且我们会把它解释成"文明加速"。

---

#### C17 · `π` 的拟合目标恰好是 `spec-validation` 明令禁止用作校准目标的那批量

`spec-llm-boundary §2.3(c)` 的"外部锚"规定：`λ_c` 与 `π` "必须对它（Seshat）的**分布级**目标（前工业政体的**战争起始率**、**政体存续时长分布**、权力交接方式分布）拟合"。

`spec-validation §12`《我们承认无法验证什么》：
- 第 1 项：**政体寿命分布的形状** —— "连'帝国寿命分布是什么形状'这个最基础的问题，学界都没有共识"（四个互相矛盾的结论）；
- 第 7 项：**Seshat 数据的可靠性** —— 旗舰论文已撤稿，63% 政体无专家审核；
- §12 的禁令逐字：**"禁止把本清单上的量用作校准目标或验收判据。"**

validation §13.4 的冲突 5 给的缓解是"π 的拟合目标只能取自 `observation` 集与外部经验散布，**不得取自 `sealed_acceptance` 集**" —— 而政体寿命恰恰被放进了 `observation`（§1.3、P-CLI-01）。**这条缓解措施正好把 `π` 推到了 §12 禁止的那批量上。** 两条规则在 validation 内部就打架，llm 又照着其中一条实现了。

**建议裁决**：`π` 的拟合目标做一次白名单化 —— 只允许 (i) `§12` 清单之外的、有量化经验散布的量（例如 `war-conflict-logistics §4.5` 的会战伤亡不对称 8.8%/25.0%、`§4.1–4.3` 的后勤参数、`technology-innovation-diffusion §4.1` 的扩散速度、`economy-markets-trade §4.3` 的价格半衰期），与 (ii) 最大熵先验（无数据时）。**政体寿命、战争起始率、权力交接方式一律不得作为 `π` 的拟合目标**；它们只能在观察集里被**报告**。代价是 `π` 在政体级决策类上退化为最大熵 —— 这是诚实的代价，而且它正好落在 llm §12.2 预期的"中间带在下沿"那一侧。

---

#### C18 · 模式电池没有"不适用"状态，而两份规格已经签字接受"世界可能什么都不长出来"

`spec-world-state §7.3` 逐字签字接受："如果 Recipe 变异过程做不出农业，这个世界就永远是采集狩猎社会……**世界什么都不发生，也是一个合法的科学结果**"；`§10.4` 签字接受"我们的世界很可能没有马"。

`spec-validation §1.4` 的通过规则：`PASS := (∀ A 级验收模式：不显著拒绝) AND (B 级通过率 ≥ 80%) AND (∀ neg 型：未命中) AND (守恒审计失败 = 0)`。

41 条 `sealed_acceptance` 里，绝大多数预设了农业、城市、政体、市场、常备军（P-SET-01/03/07、P-WAR-01/03/04/05/07/08、P-STA-01/03/04/05/06/07/08、P-ECO-01..06 ……）。**如果这个世界没有农业，这些判据既不是通过也不是失败 —— 它们没有可求值的输入。** `PASS` 的定义里没有第三种状态。

`spec-validation` 声明了 `morphology_class` 字段（§1.1，"形态条件化；`*` = 普适"）作为缓解，但**从未定义它的可执行语义**：谁计算一个世界的 `morphology_class`？在哪一层？如果在观察层，那它是一个 gating 验收的 composite 标签，需要自己的检出器、自己的版本化、自己的诱饵标定 —— 一份规格都没写。§12.4 第 42 项已经诚实承认"判据的形态偏置……**这是一条我们以严谨之名亲手装上的隐形科技树**"，但缓解措施停在承认这一步。

**建议裁决**：给模式记录加第四种求值结果 `NOT_APPLICABLE`，并规定 (i) `NOT_APPLICABLE` 不计入 `PASS` 的分子分母；(ii) **`NOT_APPLICABLE` 的比例本身是一等报告项**，且必须与 `P-STA-02`（允许缺席）并列出现在首页；(iii) `morphology_class` 的判定器写成一个显式的、版本化的、进 `COMPOSITE_LEXICON` 的检出器，并**在诱饵世界上标定**（否则它就是一个可以用来豁免任何难看结果的旋钮）。

---

#### C19 · `basin600` 无法承载它被赋予的定义性要求

`spec-validation §10.6` 的定义性要求逐字："**全套判据必须能在它上面跑完**（这是它的定义性要求）"。地图规格：600 格（约 1.5×10⁵ km²），"必须包含：一条主河、一段高机动性生态带（草原）边缘、一个海岸段、一处山口"。

三个问题：

**(a) 它不满足 `spec-world-state` 的窗口准入判据。** D12/§10.3 的 (W1) 要求"包含农耕核心区相邻的温带草原生态带的**完整**纬向与经向跨度，且在草原带之外还有 **≥ 500 km 的缓冲**"，并禁止"把草原/牧业生态带切在世界边界之外"。600 格的流域只有"草原**边缘**"。于是 P-WAR-08（巨型政体与草原边疆 500 km 关联）、P-STA-05（政体规模对草原前沿距离的梯度）在玩具世界上**不可检验**，而这两条都是 `sealed_acceptance`。

**(b) 实体上限的推导不自洽。** §10.6 说"全尺度上限 ÷ 50"，给出 `sites ≤ 4.4×10⁴`。但 `Site` 的上限在 world-state §2.2 是 `Cell × ≤16`，600 格 × 16 = **9,600**。位点数是格数的函数，不能独立缩放。

**(c) 与 C16 叠加。** 300 年的 PR 门在 `tick < 2000` 内，C/D 级机制全关。

**建议裁决**：把玩具世界拆成两张图 —— `basin600`（流域，用于产量/人口/聚落/信息类判据）与 `frontier900`（一条含完整草原—农耕接触带的窄长条，约 900 格，用于 P-WAR-08/P-STA-05 与一切边疆判据）；`sites` 上限改写为 `cells × 16`；并且把"全套判据必须能在它上面跑完"降级为"**全套判据必须在这两张图的并集上跑完，且每条判据显式标注它在哪张图上有效**"。同时补第三张图 `M_iso`（`spec-causality §11.2` 要求的隔离测试地图），它现在四份规格里没有任何一份给了规格。

---

### 次级冲突与接口缺陷（不改路线，但必须有人签字）

| # | 缺陷 | 位置 |
|---|---|---|
| N1 | 三张互不覆盖的 CI 总表，PR 时间预算无主。validation §10.6 算出 PR 门 ≈4.5 min（诱饵 30 s + 零模型 3 min + 确定性 1 min），但没算 causality §11.1 的 T-ZERO（玩具 20 年）、§11.2 的 T-ISOLATION（32 个干预 × 100 年 × 2，需要独立地图）、world-state §11.3 的 T-ERASE/T-ISOLATE/格扫周期基准/log-log 斜率。5 分钟预算已经超了。 | world-state §11.3 / causality §11.4 / validation §13.2 |
| N2 | `MAX_RANGE` 无处可导。causality §11.2 要求它"由复杂度契约表**机械导出**，不是人手填的数"；validation §10.3 只有贸易的 300 km 与 top-k=12，没有迁徙/信息/疫病/军事的射程常数。 | causality §11.2 ↔ validation §10.3 |
| N3 | 四套内核分解并存，各自做不同预算的分母：`PrimitiveVerb` P1–P10（world-state §1.3）、`mechanism_id`（causality Tier-D，签名条目 10²–10³）、12 个子系统（validation §10.3 的周期份额）、10 个相位（world-state §5.3）、`|M| ≤ 20`（validation §10.5 的消融臂数）。没有一份规格给出映射。消融成本 ∝ \|M\|、读签名规模 ∝ 机制数、周期份额按子系统 —— 三个数不能各算各的。 | 全部四份 |
| N4 | 三值逻辑（`DECISION-REGISTER A14`）只有 causality §10.5 实现了（`QueryResult { Value, NotPresent, CensoredByRetention, Unknown }`），world-state 的 L0 用 `Option<T>`，两值。而 validation R21（信念–事实背离度恒为 0 ⇒ HALT）与 causality §6 的三种缺席都依赖三值。 | world-state §2.3 ↔ causality §10.5 |
| N5 | `spec-llm-boundary §6.3` 的 12 条文化通道要求"每 tick 为每个活跃 Actor 算 12 个纯函数"，自称"可忽略"，但只算了求值次数（2.4×10⁶），没算每个 `fn` 要聚合的可达 InfoCopy 多重集。复杂度契约表没有这一行。 | llm §6.3 ↔ validation §10.3 |
| N6 | `Role` / 职位在 L0 没有表示。llm §2.2 的 `ActorRef = Household \| Person \| RoleHolder`，§10.4 的 `w_f` 用到"具名军职 Role 的持有者计数"（validation P-WAR-06 同），而 world-state §2.2 的实体总表里没有 `Role`，§2.3.3 明确 `Person` 没有 `office`/`title`。按 D3，职位应当是 `ShouldDefer` 命题 + 胁迫能力的合成 —— 但没有一份规格写出这个合成。 | llm §2.2/§5.5 ↔ world-state §2.3.3 |
| N7 | `DECISION-REGISTER` 已陈旧且权威条款自相矛盾。A19–A33 里大量条目仍标"未裁决"，而 causality/llm/validation 已经逐条裁决；§0.3 声称冲突以本表 §5 为准，而 §5.6 与 validation V14 冲突（C10）。签字页不能同时是过期页。 | DECISION-REGISTER §0.3 / §1 索引 |
| N8 | `spec-causality §5.1` 的 `significance` 要求"`layers` 由 schema 反射机械导出"，层划分逐字包含"**制度**"。world-state L0 没有制度层。 | causality §5.1 ↔ world-state §2.2 |

---

## 2. 纲领 13 个待答问题的覆盖度

| # | 问题 | 主要由谁回答 | 质量 | 缺口 |
|---|---|---|---|---|
| 1 | 世界最底层必须有哪些状态？ | `spec-world-state §2`（六类实体 + 三张注册表 + 字段级 schema + 单位体系 + 禁止字段黑名单） | **solid** | 缺 `Role`/职位的合成表示（N6）；缺 L0 三值逻辑（N4）；缺 `MechanismSwitches`（validation V5 要求它是内核字段，world-state 没有）；缺受控访问器接口（C3） |
| 2 | 哪些变化由数学/规则决定？ | `spec-llm-boundary §1.3` 权限矩阵 + `spec-world-state §1.3` P1–P10 + `spec-validation §5` 五闸门 | **partial** | 界线画得很清楚，但**规则集是空的**。产量、生育、死亡（Siler 参数在 schema 里但函数没写）、迁移、交换、疫病、战争结算、Recipe 变异 —— 一条机制规格都不存在。world-state §0 明说"具体机制属于其他规格"，那份规格不存在 |
| 3 | 哪些问题适合交给 LLM Agent？ | `spec-llm-boundary §1.2/§1.3/§5.5`（三段式 + 逐字段权限矩阵 + 制度/教义分工表） | **solid** | `p_LLM` 的校准集在原理上还不存在（llm 附录 A O2 自己列为"最大的一个未解结构性问题"）；`A(state)` 枚举器本身未被审计（O6） |
| 4 | 哪些绝不能让 LLM 决定？ | `spec-llm-boundary` L1 + `T-WRITESET` + §1.3(iii) 因果域全否 + §5 命名权收回 | **solid** | 唯一可机械执行的定义（置换不变性，§6）在 L12 架构下重放变体是恒真式，实跑变体 `T-SUBST-B` "大概率会失败"且失败后怎么办没有好答案（O7） |
| 5 | 如何产生真涌现而不是隐藏剧情树？ | `spec-validation §4`（D1–D6 + ZB/PS）+ §7 宪章 + §2 诱饵 + `spec-world-state §3` T-ERASE + `spec-causality §5` | **partial** | **检测侧非常强，生成侧是空的。** "涌现"的唯一来源是 Recipe 系数空间上的变异过程（world-state §7.3 五条初始 Recipe），而这个变异过程没有任何规格。`P-MET-03`（词表增长 K(t) 不饱和）整条判据挂在一个不存在的机制上。另：C18 的形态偏置 |
| 6 | 如何保存因果？ | `spec-causality §3`（四档）+ §4（Event/Channel 双节点）+ §8（归因报告） | **partial** | 读取集粒度三选一未裁（C3）；`declared_causes` 与 SPIKE-3 矛盾（C3a）；受控访问器不在 L0 接口里（C3c）；taint 开销未实测且无预算（C3d）；§12 推导缺失（§3） |
| 7 | 如何验证重大事件成立？ | `spec-validation §5`（G1–G5 + A1–A4）+ `spec-causality §8`（归因报告 + PN/PS + 必然性剖面） | **partial** | 「事件」有四个定义（C9）；闸门需要内核读语义类型（C9c）；硬失败语义未定义且与 llm §2.8 冲突（C9d）；`SPEED_TABLE` 是借用的地中海参数（validation 自己标 `BORROWED_MEDITERRANEAN`） |
| 8 | 如何处理拿不到准确历史参数？ | `spec-world-state §7.4`（存先验不存点值、`free ≤ 15`）+ `spec-validation §10.5`（12+3 两本账）、§8.4（三分类账）、§12（无法验证清单，只增不减） | **solid** | 唯一的硬伤是 §7.4 的"证据等级闸门"本身是阶段门（C16）。三分类账的执行完全靠治理，validation 自己承认（§12.4 第 38 项） |
| 9 | 如何防止为戏剧性造事件？ | `spec-validation §6`（四量分离 + 审查对称化 + L-ABS-1/2/3/4）+ §7 宪章九类 + `spec-llm-boundary §3`（比特预算）、§4（基率检测三条腿）、§8.5(e)（`T-HEADLESS-REACH`） | **solid** | **这是覆盖最好的一个问题。** 残余：llm 附录 B.4 第 1 项自己承认 `D_KL` 作为"影响力"的度量效度未经验证，§3.3 的算术已表明它与因果杠杆可差五个数量级；且 llm 的十几个指标"没有一个做过阳性对照"（llm 附录 C.3 逐字） |
| 10 | 如何衡量"合理但不必真实"？ | `spec-validation §1`（51 条模式电池 + 口径三元组）+ §2（三族诱饵 + 标定报告）+ §0.2（`bits(C)` 的对数似然比形式化） | **partial** | 方法论是四份里最扎实的一节（§0.2 的"未标定判据证据量 ≤ 0"值得单独表扬）。但：41 条验收模式**全部处于候选状态**，验收集在标定完成前是空集（V1，validation §13.5 第 1 条自己承认这意味着"Phase 1 相当长一段时间里没有任何'通过'的定义"）；`NOT_APPLICABLE` 状态缺失（C18）；`morphology_class` 无可执行语义 |
| 11 | 数千年算力如何可行？ | `spec-validation §10` + `spec-world-state §4/§5` + `spec-llm-boundary §9` | **partial** | 三个不相容的四方分账（C10）；一次"为什么"的价格差 5–9 倍（C11）；三张预算表建立在被取消的本体与被否决的网格上（C12）；`T_run` 未按模式分账（C13）；涌现认证按范畴计价的漏算（C14）；缺项（C12d）。**结论：目前没有一张可信的算力表** |
| 12 | 不同时间尺度与粒度如何设计？ | 时间：`spec-world-state §5`（两条整除链 + 子时钟配额表 + Strang 分裂 + 崩溃期步长减半测试）—— 这一节是四份规格里质量最高的单节之一。粒度：无 | **partial**（时间 solid，粒度 missing） | **LOD 完全没有规格。** `DECISION-REGISTER A17` 标"未裁决"；world-state 只给了 `Person ≤ 3×10⁴` 与 `Cohort`，没有提升/降级规则；A17 要求的三样东西（只读结构量的提升函数、1% 随机提升对照组、LOD 不变性检验）四份规格里**一样都没有**；validation §10.3 唯一提到 LOD 退化的地方违反禁令（C15）。而 A17 逐字说 LOD 是"一条在机制层面制造主角、且不留代码痕迹的正反馈" |
| 13 | 如何保证重放、分叉、比较？ | `spec-causality §10`（内容寻址 + 配额 + 单向阀 + 删失显式）、§11（T-ZERO/T-ISOLATION）+ `spec-world-state §6` + `spec-llm-boundary §8` | **partial** | 四个世界线身份（C2）；三个 canon 种子公式（C2）；CBRNG 布局比特级冲突（C1）；确定性门禁未按模式分账（C6）；ledger 键未闭合（C8）。**比较**这一侧最好：causality R5（跨 `kernel_hash` 比较在 API 层报错）+ 重算债务仪表盘是干净的 |

**汇总**：solid 5 条（Q1、Q3、Q4、Q8、Q9），partial 8 条（Q2、Q5、Q6、Q7、Q10、Q11、Q12、Q13），missing 0 条 —— 但 Q12 的粒度半边与 Q2 的机制半边实质上是 missing，只是被同一个问题的另一半掩盖了。

---

## 3. 四份规格加起来仍然没有解决的问题

按"会不会挡住 M1"排序。

### 3.1 会立刻挡住第一行代码

1. **没有任何一份机制规格。** 世界怎么长粮食、人怎么生怎么死、东西怎么运、信息怎么传、Recipe 怎么变异 —— 一个函数都没有。四份规格是接口、因果、边界、治理，**没有世界**。这不是疏忽（world-state §0 明说了分工），但它意味着"第一个里程碑"不可能是"跑一个像样的世界"。
2. **`default_policy` 不存在。** `spec-llm-boundary` 的 `T-DEFAULT-COVERAGE`（每个 `llm_eligible` 槽位必须有非空 `default_policy_id`）、`MODE_HEADLESS`、`T-HEADLESS-3K`、退路配置 R、以及 validation 的 N1/N2 消融臂与 `--spike` main，全部建立在它上面。llm 附录 A O10 逐字承认："§12.3 说'动机变成规则侧的效用函数'，但没有给出那个效用函数。**这是一整份规格的工作量**……**现在就应该有人开始想它**。"
3. **LOD 提升/降级规则不存在**（见 Q12）。
4. **受控访问器 / 读屏障的 API 形状未定**（C3）。这是唯一一条真正改变内核每一个读写点的未决项。
5. **`spec-causality` 是残稿。** 文件在 §11 结束（1262 行），但正文引用了 **§12.1**（因果算力推导，§1 的 1,100 CPU-h 就出自这里）、**§13.1**（玩具标定世界 `W_cal`，被 §3.2 与 §4.3 引用两次）、**§15**（双孪生线实测的通道封闭偏差，`AttributionReport.channel_closure_bias` 字段的定义处）。三个被引用的对象都不存在。另：`W_cal` 与 validation 的 `basin600` 大概率是同一个东西，但没人说。
6. **`spec-llm-boundary` 依赖的 `llm-storytelling.md` 是残稿**（该规格说明 0.A 已诚实披露：正文止于 F9，但 F10–F26 被交叉引用）。llm 为此自造了三处替代论证（§2.5、§5.6、§11.2），全部标 D 级。**这是上游文献的洞，不是规格的洞，但它现在是项目的洞。**

### 3.2 会在 Phase 1 中段炸掉

7. **牧业/游牧生业系统没有规格，而 D12 把整个世界的边界押在它上面。** world-state D12 要求草原带完整内生，`DECISION-REGISTER §5.7` 的残余风险逐字："若牧业机制在 Phase 1 做不出来，唯一诚实的退路是**把世界缩回农业带并声明'本世界没有草原压力'**，而不是偷偷打开外部通量接口。**这条退路必须现在写下来。**" 它现在写下来了（在 register 里），但没有任何一份规格给出牧业机制的形状，也没有人估过工作量。
8. **Recipe 变异过程决定这个项目会不会什么都不发生。** world-state §7.3 只给五条初始 Recipe 并签字接受"世界可能永远是采集狩猎社会"。技术空间的拓扑（系数向量空间上的变异核、可达性、适应度地形）没有规格，而 `P-MET-03`、`novel_combination_rate`、整个涌现认证都挂在它上面。
9. **`π` 的函数形式与拟合数据。** llm §2.3 规定了 `π` 的**约束**（下界 2⁻⁶、NOOP 主导、`justification_class` 分类、`P/T ≤ 3`），但没有给出任何一个决策类的 `π`。而 C17 又切掉了它原定的主要拟合目标。
10. **`|A(state)`| 枚举器是一个未被审计的先验**（llm O6 自陈）。"一个不枚举'投降'的选择集，世界里就没有投降。" 唯一的间接读数 `novel_request_rate` 太弱，llm 明说"本文没有想出来"更好的检验。
11. **`T_batch` 未知，而它决定 `MODE_FULL` 是否可行**（llm O8：60 s / 5 min / 30 min 三档差 60 倍，最后一档不可接受）。
12. **自托管栈选型未定**（llm O9），而 llm §8.3 的时限是硬的："一旦第一条正式历史线用托管 API 跑出来，它就永久失去了可反事实性。"

### 3.3 原理上无解，四份规格都已诚实承认（不要再花时间找解）

13. **人类回路（L4）与目标反噬（L5）。** validation §12.4 第 38/39 项、llm O5、register A33、`pseudo-simulation` K7 金丝雀。唯一对策是流程留痕，而"它检验的是我们的纪律，不是我们的正确性"。
14. **`UNMODELED` 类缺席因永远不会出现在任何报告里**（causality §6.3 残余风险第 4 条 + §6.4 常驻页脚）。
15. **等效性（equifinality）**：validation §12.4 第 40 项 —— Epstein 的答案要求新的微观数据，"而我们的世界没有外部微观数据可收集"。
16. **判据的形态偏置**（validation §12.4 第 42 项）："这是一条我们以严谨之名亲手装上的隐形科技树。"
17. **离散随机系统的反事实不可识别**（world-state §6.7 的诚实条款）：Gumbel-max 只是"直觉上可接受"的选择，不是正确的选择，且这条假设不可用数据检验。
18. **决策环路没有被切断，也不应该被切断**（llm §11.2(乙)）：文本环路已切断，状态环路是 agency 本身。

### 3.4 流程性缺口

19. **`DECISION-REGISTER` 需要重生成一次。** 它现在只与 `spec-world-state` 对齐（§0.3 自述），对另外三份规格是过期的，而它自称是签字页。且它的权威条款（§0.3）与 validation V14 冲突（C10）。
20. **没有人拥有 PR 门的时间预算**（N1）。
21. **`spec-validation §13.5` 第 1 条自己提的问题没有答案**："验收集在标定完成前是空集……**谁来决定这段时间的里程碑标准？**" 本审查的建议见 §4 —— M1 的通过标准全部是**二值结构检验 + 必须产出的实测数字**，一条统计判据都不用。这正好绕开这个问题。

---

## 4. 第一个里程碑：`M1 — 契约与毒药`

### 4.1 M1 不是什么

- **不是一个像样的世界。** 没有农业、没有战争、没有制度、没有宗教、没有 LLM、没有归因报告、没有涌现认证、没有模式电池。
- **不是把 80 条 A/B/C 档决定全部裁完。** `DECISION-REGISTER §6` 把"读完这张表的反应是'那我们再研究半年'"判为项目的头号病原体。M1 只需要裁完 §1 里点名的那些接口冲突，其余带着默认值往前走。

### 4.2 M1 是什么（一句话）

**一个只有 6 个机制的内核，跑在三张小地图上，能通过全部二值结构检验，能在每一个对应的"毒药构建"上失败，并且用实测数字替换掉当前预算表里的每一个 D 级乘数。**

理由：`spec-validation §2.1` 逐字给了这个反直觉的开发次序 —— "**先实现度量 → 再用假货把度量测一遍 → 然后才实现世界**"；`spec-validation §0.2` 证明了未标定判据的证据量 ≤ 0。M1 就是把这两条应用到**最底层**：在写任何社会机制之前，先证明我们的确定性、因果、类型抹除、隔离这四套地基检验，在各自的毒药上会红。

### 4.3 第 0 周：签字冲刺（5 个工作日，不许超）

产出四份各一页的规范文本，签字后进 `DECISION-REGISTER v0.2`：

1. **《标识与确定性契约》** —— 解决 C1、C2、C6、C7、C8：一个 CBRNG 布局（world-state §6.4）、一个 Gumbel 寻址规则（内容哈希）、一个世界线身份九元组（+`basemap_hash`、`param_prior_hash`）、一个 canon 种子集合公式、一张确定性门禁 × 运行模式适用表、`ledger` 一个名字一份 schema（llm §8.2）。
2. **《事件词汇裁决》** —— 解决 C9：`Transition` / `Nomination` / `Act` / `Occurrence` 四个名字与各自的归属层，并逐条重新绑定现有判据的分母。
3. **《受控访问接口》** —— 解决 C3：`ctx.read/write` 的签名、`mechanism_id` 上下文、R4 静态相等检查作用在哪、Tier-D/S/R 的粒度裁决、SPIKE-3 的改写。
4. **《相位顺序 V2 与流表 v2》** —— 解决 C4、C5：`PHASE_ORDER_V2`、Intent 同延迟、`sense` 的时点、三条新流（`worldgen/phonology`、`lang/change`、`opportunity/<class_id>`）、`site` 三义改名。

同时冻结三张预算表（C12），标注"待 M1 实测替换"。

### 4.4 M1 的规模

| 项 | 规格 |
|---|---|
| **机制数** | **恰好 6 个**：`metabolize`(P2)、`carry`(P3)、`copy_info`(P4)、`bear`(P5)、`forage/hunt`(P6 的退化形式，用 world-state §7.3 的初始 Recipe 1–3)、`apply_lethal_force`(P9)。**不含** P1（胁迫转移）、P7（藏匿）、P8（破坏结构物）、P10（`emit_claim`）—— 它们留给 M2 |
| **实体** | `Cell`、`Cohort`、`Household`、`Site`（创生冻结）、`Person`（L2，但**固定名单**：t=0 随机选 1% 提升，全程不变 —— 因为 LOD 规则还没有规格，见 §3.1 第 3 条）、`InfoCopy`、`Proposition`（只有 `Observed` 与 `Recipe_Known` 两种形式）、`RelationEdge`（只有 `gestated_by`/`sired_by`/`co_reside`/`holds`/`taught_by`/`killed_by` 六种）、三张内容寻址注册表 |
| **地图** | 三张：`basin600`（600 格，产量/人口/信息）、`frontier900`（900 格，含完整草原—农耕接触带；C19）、`M_iso`（2 × 300 格，两块通行成本 > `MAX_RANGE` 的陆域，专供 T-ISOLATION） |
| **全尺度压力测试** | `--spike` main 在全陆地格（按实测陆比确定，约 8–9 × 10⁴ 格）上跑，只为性能门 |
| **时长** | 玩具：3000 世界年（PR 门用 300 年）；`M_iso`：400 年；`--spike`：3000 年 |
| **种子** | 玩具 200 个；`M_iso` 的干预 32 个 `(point, op)` 组合；`--spike` 1 个 |
| **LLM** | **零**。M1 全程 `MODE_HEADLESS`，`llm` crate 在依赖图中物理不存在（llm §8.5 的 `T-NOLLM-BUILD`） |
| **`default_policy`** | M1 用**最简可判定形式**：所有决策从 `π` 采样，`π` 用最大熵先验。这不是 `default_policy` 的规格，是它的占位符，必须在 M1 的 README 里标 `PLACEHOLDER` |

墙钟目标：玩具单次 3000 年 ≤ 80 s（validation §10.6）；200 种子 × 3000 年 ≤ 17 min（16 核）；`--spike` ≤ **1.8×10¹¹ 归一化周期**（validation §10.7 的形式，用归一化周期数不用墙钟秒）。

日历：签字冲刺 1 周 + 实现 6–8 周。**如果第 3 周结束时 `main` 还跑不到 t=3000，砍机制，不砍里程碑**（这是 `DECISION-REGISTER §6.1` 的 URR 病对策）。

### 4.5 M1 必须造的毒药（这是 M1 的真正交付物）

每一个二值检验配一个**毒药构建**（poison build），CI 里同时跑健康内核与毒药内核，**毒药上不红 ⇒ 删掉那条检验，不许辩护**（`emergence-verifiability F6` + validation §0.2）。

| 毒药 | 植入什么 | 必须让谁失败 |
|---|---|---|
| `poison-id` | 实体 id 改回全局自增计数器 | `T-ISOLATION`（causality §11.2 判据 4 的第一类致命伤） |
| `poison-iter` | 一处依赖 `HashMap` 迭代顺序的处理次序 | `T-ITERORDER`、`T-ISOLATION` |
| `poison-float` | 热路径上一个 `f64` 累加 | 跨机器不变性、线程数不变性 |
| `poison-label` | 内核热路径插 `if label_of(cell) == "c:cluster" { forage_yield *= 1.05 }` | `T-ERASE`（world-state §3.3 明文要求的阳性对照），且失败报告必须精确指向那一行 |
| `poison-clamp` | 产出上加一个 `max(0, x)` | 守恒审计、矩位移测试（validation §7.2 第 1 类，Anasazi 原案） |
| `poison-trigger` | `if year > 1200 and pop > X: 某区域 forage_yield ×1.3`（W1a 的最小形态） | 阶跃探测（3σ）、N0 支配测试、读取集闭包 |
| `poison-decouple` | 切断全部跨子系统耦合（W3-lite） | 动力学独立性 `T ≈ 0` **与** `σ(e) ≈ 0` 同时出现（validation §4.8 的"低 T + 低 σ = 剧情树"对偶） |
| `poison-gumbel` | Gumbel 分量改回按位置索引寻址 | 一个新的二值检验 `T-GUMBEL-PERM`：重排候选项枚举顺序后，同种子的离散抽样结果必须逐位相同［本文原创，D 级 —— world-state §6.7 论证了这条病症但没有给检验］ |
| `poison-ledger`（M2 才用） | ledger 键改成含渲染字节 | `T-SUBST-A` |

`poison-*` 构建全部是同一份内核的 feature flag，不是第二份代码（validation §3.3 的硬要求）。

### 4.6 M1 的通过标准（全部二值，一条统计判据都没有）

**结构类（每次提交，全部必过）**

1. `T-DEPGRAPH`：内核 crate 的依赖闭包不含观察层、不含 LLM crate、不含字符串表。
2. `T-NOLLM-BUILD`：`--no-default-features --features kernel-only` 编译通过，全部不变量测试通过。
3. 原语准入检查 R1a/R2/R3/R4 全通过；禁止字段 AST 黑名单零命中；`free: true` 参数 ≤ 15。
4. `T-ERASE`（玩具，逐位）；且在 `poison-label` 上**失败**并指向正确行号。
5. `T-ITERORDER`（逐位）；且在 `poison-iter` 上失败。
6. `T-NULLINT`（逐位）；`T-ZERO` 的三种 IDENTITY 形式全测（causality §11.1）。
7. `T-ISOLATION`（`M_iso`，32 个干预，B 区 100 年逐位相同）；且在 `poison-id`、`poison-iter` 上失败。**软判据也必须报告**：A 区散度锥与到干预点的通行成本相关 > 0.5（白噪声式散度 = 还有隐藏耦合）。
8. 线程数不变性 1/4/16 逐位相同；跨机器（x86-64 + aarch64）逐位相同；且在 `poison-float` 上失败。
9. `T-GUMBEL-PERM`（新，见上）；且在 `poison-gumbel` 上失败。
10. 守恒审计：每 tick、三个守恒量（`Mass_g` 分物质、`Energy_kcal`、`Pop_up`）、**int64 精确相等**，全程零失败；且在 `poison-clamp` 上失败。未注册的源汇项 = 构建失败。
11. `--spike` 三项：SPIKE-1（bit 级重放）、SPIKE-2（守恒零失败）、SPIKE-3'（改写版，见 C3 建议 3）。
12. 性能门：`--spike` ≤ 1.8×10¹¹ 归一化周期；`CPLX-1` log-log 斜率 ≤ 1.2；`CPLX-3` 玩具外推到全尺度 `T_run_headless` ≤ 1 h。

**治理类（从第一次提交起存在，否则事后无法重建）**

13. `registry/run_registry.sqlite` 存在，且**每一次超过 100 世界年的运行自动入表**（含失败、含中止），append-only。
14. `charter/gated_baseline.toml` 存在，`GATED_COUNT[kind]` 基线从 0 开始且只降不升。
15. `params/*.toml` 里每个参数带 `source` 或 `free: true` 与 `change_log`；三分类账（`bug`/`evidence`/`aesthetics`）的工具链能跑。
16. `MechanismSwitches` 存在，只在 t=0 读一次，AST 检查它不出现在任何相位函数的读取集里（validation §3.3）。
17. canon/lab：`lineage_class` 进世界线身份哈希，且有一个**必须失败**的测试：把一条 lab 线改标为 canon，所有指向它的引用断链。

**必须产出的实测数字（这是 M1 存在的另一半理由 —— 它们现在全是 D 级，而所有预算都建立在它们上面）**

| # | 数字 | 替换掉谁 |
|---|---|---|
| N-1 | 气候 AR、采集产出的**实测周期/格/tick** | world-state §4.2 的 2,000 与 8,500（自标"纸上谈兵"） |
| N-2 | `T_div`：单最小单位（1 g / 1 kcal / 1 µp）扰动到宏观距离达到种子间中位距离一半所需年数 | world-state §6.9 —— 它直接决定"单条线上的因果结论有效期"，进而决定 causality §7 的视界表能不能测 |
| N-3 | **taint 开销倍数**（Tier-R `--taint` 相对基线） | causality §3.2 自标"§12 预算表里唯一没有实测锚点的乘数" |
| N-4 | 单快照压缩后字节数、年增量字节数、200 种子集合总量 | causality §10.2/§10.4 与 validation §10.9（C12） |
| N-5 | 守恒审计的每 tick 开销占比 | 复杂度契约表的缺项（C12d） |
| N-6 | 实测陆比与实际格数 | world-state §10.3 自标"陆比 0.6 是我拍的数，必须实测" |
| N-7 | `InfoCopy` 驱逐率（%/yr） | world-state §2.6 的 5% 报警线是否合理 |
| N-8 | PR 门实际墙钟 | N1（没人拥有这个预算） |

**不作为通过标准的东西（明确写下来，防止跑偏）**：模式电池的任何一条、涌现认证、归因报告、`significance` 提名、Channel 干预、LLM 的任何指标、"世界看起来合不合理"。M1 允许——甚至**预期**——跑出一个 200 个种子全部在 500 年内灭绝的、无聊透顶的世界。`spec-world-state §7.3` 已经签字："**世界什么都不发生，也是一个合法的科学结果。**"

### 4.7 M1 的收尾动作

1. 用 N-1..N-8 重写**一张**《复杂度契约与存储预算表 v1》，取代现有三张，每行 owner 签字。
2. 重生成 `DECISION-REGISTER v0.2`，把 A19–A33 的"未裁决"按四份规格的实际裁决更新，修订 §0.3 的权威条款（C10、N7）。
3. 按 N-3 的实测结果决定 causality §3 四档的最终形态；按 N-2 决定单线因果结论的有效期上限并写进方法论声明首页。
4. 立项两份缺失的规格：`spec-mechanisms`（六个 M1 机制的正式化 + M2 的下一批）与 `spec-actor-policy`（`default_policy` + LOD，llm O10 与 register A17 的合并）。**在这两份出来之前，不要开始 M2。**

---

## 5. 本审查自己的不确定性

1. §1 的全部裁决建议里，**只有 C1、C3、C9、C16 我认为有决定性论证**；其余（尤其 C2 的九元组修正、C10 的 18/50/25/4/3、C18 的 `NOT_APPLICABLE`）是我在两个都说得通的选项里选了一个，标 D 级。
2. C12 里"world-state 热态 650 MB ⇒ 快照 217 MB"这一步用了 3× 压缩比（沿用 causality §3.3 的假设），压缩比本身没有实测，所以"快照吃光 30 GB 上限"这个结论的量级可靠、数字不可靠。
3. §4 的 M1 规模（6 个机制、三张地图、6–8 周）全部是我编的，没有来源。我唯一有信心的是它的**形状**：先造毒药再造世界，先出实测数字再签预算表。
4. 我没有检查 22 份简报的原文 —— 本审查只核对了四份规格与登记表之间的一致性，以及它们对红队的引用是否自洽。**如果某份规格误引了简报，本审查抓不到。**
5. `spec-causality` 的 §12/§13/§15 缺失意味着我无法评估它的算力论证是否成立；C11 的判断（暂以 validation 的 5,000–10,000 为准）是在信息不全下做的。
