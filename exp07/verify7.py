"""
EXP-06 —— 援助记忆与优先回助。

由 exp05/verify5.py（对照版本 commit d20a015）复制并**只加一个机制**：
让**过去发生过的援助**影响未来的分配 —— 每个群体记住谁实际援助过自己，
援助时把一部分预算优先回给"过去帮过我、现在又缺粮"的同格群体。

**这些都是写死的规则与本轮的模型假设，不是涌现，也不冒充现实历史定律。**
本切片不宣称出现了互惠规范、联盟或道德：记忆怎么记、优先怎么排，全部由下面的公式决定。

三条本轮定死的假设：
  1. **记忆只来自实际转移**：`band['amem'][给我援助的群体] = [累计 kcal, 最近年份]`。
     不读第三方的全知关系表，不生成好感度。**记忆不是债务**：不要求等额偿还，
     不自动结盟，也不影响除"优先顺序"以外的任何规则。
  2. **分裂的子群体不继承记忆**（它没有实际接受过任何援助），父群体的记忆原样保留。
     被否掉的另一种做法是"子群体复制父群体的记忆"——那会让一次实际援助在多个群体的
     记忆里重复计数，账也对不上。
  3. **群体消失时**，它自己的记忆随之丢失，数量记入 `amem_dropped_kcal`（因此记忆账仍然闭合）；
     **别人对它的记忆保留**（它确实帮过别人，只是再也无法回助），可由 `amem_dangling` 观察。
     完整历史永远留在 `aid_log` 里，一次实际援助只记一次。

相位位置：**采集结算（相位 2）之后、消费（相位 3）之前**（沿用 EXP-05）。
优先阶段与普通阶段**统一核算**：优先阶段独立提议 → 统一裁决 → 与普通阶段一起一次性提交，
不超预算、不超缺口、不重复送粮；**优先阶段只读本年援助之前的关系快照**，结算完才更新记忆。
  可用粮食 avail = 当年采集 + 原有储粮
  供给方先保留自己当年的需求 need，只有 avail − need 的部分可以援助；
  愿意拿出其中 AID_M/1000（向下取整）作为预算，没被接收的仍归自己。
  接收方最多补齐自己当年的缺口 need − avail。

本切片的假设（写明，不含糊）：同格群体能**如实**提出缺粮请求。
不跨格送粮，不增加运输、欺骗、信任、债务或交换回报。

exp01/ ~ exp05/ 都只读、不改。退化恒等式：
  RECIP_M=0                          =>  逐步复现 EXP-05（用 exp05 自己的哈希；它不认识 amem，
                                         所以"新增的记忆状态"不会被误判成演化偏差）
  RECIP_M=0 且 AID_M=0               =>  逐步复现 EXP-04（用 exp04 自己的哈希）
全整数运算，无浮点进入状态。
"""
import sys, json, hashlib
from typing import Dict, List, Tuple

# ---------- 单位 ----------
KCAL           = 1                      # 状态里的能量单位
NEED_PC        = 730_000                # kcal/人/年  (2000 kcal/日 × 365)
MILLE          = 1000                   # 定点：千分之一
STORE_YEARS_M  = 1000                   # 储存上限 = 1.000 年的口粮
SPOIL_M        = 250                    # 储存年腐损 0.250
K_HALF         = 30                     # 采集饱和半数（人）
MOVE_LOSS_M    = 150                    # 迁移损失储存的 0.150
SPLIT_SIZE     = 40                     # 分裂阈值（人）
MIG_E_M        = 1000                   # E < 1.000（任何热量赤字）即打听邻格
MIG_GAIN_M     = 1250                   # 记忆中邻格存量 > 自己 1.250 倍才动
SHOCK_P_M      = 20                     # 每 band 每年 0.020 概率死亡冲击
# --- EXP-02 唯一新增参数 ---
# 合法范围 SIGMA_M ∈ [0, 1000]（千分之一）。0 = 无波动（退化为 EXP-01）；
# 1000 = 乘数可低至 0（该年该格完全不再生）。超出该范围由 make_world 拒绝。
SIGMA_M_MIN, SIGMA_M_MAX = 0, 1000
# --- EXP-03 唯一新增参数 ---
# 迁移死亡强度（千分之一）。合法范围 [0, 1000]。0 = 无代价（退化为 EXP-02）。
# 1000 = 整群在迁移中全灭。
MOVE_MORT_M_MIN, MOVE_MORT_M_MAX = 0, 1000
# --- EXP-04 唯一新增参数 ---
# 同格信息交换的参与概率（千分之一）。合法范围 [0, 1000]。
# 0 = 不交换（退化为 EXP-03）；1000 = 同格者每年都参与。
SHARE_M_MIN, SHARE_M_MAX = 0, 1000
# --- EXP-05 唯一新增参数 ---
# 供给方愿意拿出多少比例的**可援助余粮**（千分之一），**不是参与概率**。
# 0 = 关闭援助；1000 = 愿意拿出全部可援助余粮。没被接收的仍归供给方。
AID_M_MIN, AID_M_MAX = 0, 1000
# --- EXP-06 唯一新增参数 ---
# 供给方把预算的多少比例**优先**分给"过去帮过自己、现在又缺粮"的同格群体（千分之一）。
# 0 = 不做优先回助（退化为 EXP-05）；1000 = 全部预算先走优先阶段。
# 优先阶段没用掉的预算会回到普通阶段，不浪费。
RECIP_M_MIN, RECIP_M_MAX = 0, 1000
# --- EXP-07 唯一新增参数 ---
# 人口里有多大比例的**折算劳动**投到耕作上（千分之一）。0 = 不耕作（逐位退化为 EXP-06）。
# 人口 N 对应 N×1000 个年度折算劳动刻度，1000 刻度 = 1 个折算劳动年。
# 现在没有年龄结构，**这是人口折算预算，不是说每个婴儿都在劳动**。
FARM_M_MIN, FARM_M_MAX = 0, 1000
# --- EXP-07 固定实验常量（D 级，本项目自拟的实验假设，不冒充中国史校准）---
FIELD_CAP_M    = 60_000                 # 单格耕地规模上限（刻度）
FIELD_DECAY_M  = 200                    # 未维护耕地的年退化率（千分之一，向上取整）
FARM_YIELD_M   = 2500                   # 每单位维护过的耕地的年潜在产出（千分之一人年口粮）
# 1000 个 field 刻度显示为 1 个"耕作规模单位"——**不是亩、公顷，也不是人数**。
# 人口：分段线性（D 级，本项目自拟）
# b(E)：E<=0.55 时为 0，线性升到 E>=1.00 的 0.045
E_BLO_M, E_BHI_M, B_MAX_M = 550, 1000, 45
# d(E)：两段。E>=1.00 取 0.032；E=0.80 取 0.055；E<=0.35 取 0.450
E_D2_M, E_D1_M, E_D0_M = 1000, 800, 350
D_AT_D2_M, D_AT_D1_M, D_AT_D0_M = 32, 55, 450

# ---------- counter-based RNG ----------
def splitmix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    return z ^ (z >> 31)

def rng(seed: int, stream: int, tick: int, eid: int, slot: int) -> int:
    """无状态、按坐标寻址。改动任何一个分量只影响该抽样点。"""
    h = splitmix64(seed ^ 0xA5A5A5A5)
    for v in (stream, tick, eid, slot):
        h = splitmix64(h ^ (v & 0xFFFFFFFFFFFFFFFF))
    return h

S_SHOCK, S_MIG, S_SPLIT, S_SCOUT = 1, 2, 3, 4
S_CLIM = 5                              # EXP-02 新增流：资源再生波动
S_SHARE = 6                             # EXP-04 新增流：同格信息交换的参与抽签
# EXP-05 不需要新的随机流：援助的供给、缺口与分配全部由当年状态确定性算出，不抽签。

def eid_of(parent: int, tick: int, idx: int) -> int:
    """血缘派生 id，无全局自增计数器。"""
    return splitmix64(splitmix64(parent ^ (tick << 20)) ^ idx) & 0xFFFFFFFFFFFFFFFF

# ---------- 地图：8×8，第 3、4 列为 barrier，切成两个不连通区块 ----------
W = H = 8
BARRIER_COLS = {3, 4}
def cells() -> List[int]:
    return [r * W + c for r in range(H) for c in range(W)]
def passable(i: int) -> bool:
    return (i % W) not in BARRIER_COLS
def region(i: int) -> str:
    return 'A' if (i % W) < 3 else ('B' if (i % W) > 4 else '-')
def neighbors(i: int) -> List[int]:
    r, c = divmod(i, W)
    # pointy-top 六边形的 axial 邻居（奇偶行错位）
    off = [(-1,0),(1,0),(0,-1),(0,1)] + ([(-1,1),(1,1)] if r % 2 == 0 else [(-1,-1),(1,-1)])
    out = []
    for dr, dc in off:
        rr, cc = r+dr, c+dc
        if 0 <= rr < H and 0 <= cc < W:
            j = rr*W+cc
            if passable(j): out.append(j)
    return sorted(out)

def largest_remainder(keys, weight, total):
    """按 weight 比例把 total 整数拆给 keys：先取整商，余数按 (余数降序, band_id 升序) 派发。

    这是本项目既有的整数分配规则（EXP-01 的采集分配用的就是它），不另发明一种。
    total >= 总权重时各拿全额（够分，不用摊）。
    """
    W = sum(weight[k] for k in keys)
    if W <= 0 or total <= 0:
        return {k: 0 for k in keys}
    if total >= W:
        return {k: weight[k] for k in keys}
    base = {k: weight[k] * total // W for k in keys}
    rem = total - sum(base.values())
    rank = sorted(keys, key=lambda k: (-(weight[k] * total % W), k))
    for i in range(rem):
        base[rank[i % len(rank)]] += 1
    return base


def alloc_totals(pairs):
    """把逐笔转移聚合成 {(供给方, 接收方): 总额}。
    判断"优先规则是否真的改变了分配"用的是它 —— 拆成两笔但总额不变不算改变。"""
    out = {}
    for d, r, a, _ph in pairs:
        out[(d, r)] = out.get((d, r), 0) + a
    return out


def settle_cell(members, pre_avail, pre_need, am, recip_m, amem_pre, P, order=None):
    """一个格子里的援助结算。**纯函数**：只读入参，不改状态。

    返回 (pairs, S, D, priority_budget)，其中 pairs = [(供给方, 接收方, 数量, 阶段)]，
    阶段 ∈ {'recip', 'normal'}。

    规则（写死在这里，测试用自己独立重写的一份来核对）：
      供给方 avail > need，预算 budget = (avail − need) × AID_M/1000 向下取整；
      接收方 avail < need，缺口 gap = need − avail。
      优先阶段：pbudget = budget × RECIP_M/1000。目标 = 缺粮且在"援助前记忆"里帮过我的群体，
        权重 = 记得对方帮过我的累计量，最大余数法摊分 min(pbudget, Σ目标缺口)，
        每个目标先按自己的缺口封顶；同一接收方被多家提议且合计超过缺口时，
        **按提议额比例统一裁减**（独立提议 → 统一裁决 → 一次提交）。
      普通阶段：用剩余预算与剩余缺口，跑 EXP-05 原规则
        （T = min(ΣS, ΣD)，两侧最大余数法，band_id 升序瀑布式配对）。
      两阶段合计：每个供给方 ≤ 自己的预算，每个接收方 ≤ 自己的缺口，不重复送粮。
    """
    donors, receivers, budget, gap = [], [], {}, {}
    for bid in sorted(members):
        sur = pre_avail[bid] - pre_need[bid]
        if sur > 0:
            bud = (pre_avail[bid] if 'aidoverbudget' in P else sur) * am // MILLE
            if bud > 0:
                donors.append(bid); budget[bid] = bud
        elif sur < 0:
            receivers.append(bid); gap[bid] = -sur
    S, D = sum(budget.values()), sum(gap.values())
    if not donors or not receivers:
        # 记账口径与 EXP-05 完全一致：一边为空时连 supply/demand 都不记，
        # 否则 RECIP_M=0 的退化恒等会因为账本字段不同而失败。
        return [], 0, 0, 0

    left_b, left_g = dict(budget), dict(gap)
    pairs = []
    pbudget_total = 0

    def normal_phase():
        ds = [d for d in sorted(donors) if left_b[d] > 0]
        rs = [r for r in sorted(receivers) if left_g[r] > 0]
        if not ds or not rs:
            return
        s2 = sum(left_b[d] for d in ds); d2 = sum(left_g[r] for r in rs)
        t2 = min(s2, d2)
        if t2 <= 0:
            return
        recv = largest_remainder(rs, left_g, t2)
        give = largest_remainder(ds, left_b, t2)
        if 'aidovergap' in P and s2 > d2:
            base = {r: left_g[r] * s2 // d2 for r in rs}
            rem = s2 - sum(base.values())
            rank = sorted(rs, key=lambda k: (-(left_g[k] * s2 % d2), k))
            for i in range(rem): base[rank[i % len(rank)]] += 1
            recv, give = base, {d: left_b[d] for d in ds}
        dleft, rleft = dict(give), dict(recv)
        di = ri = 0
        while di < len(ds) and ri < len(rs):
            d, r = ds[di], rs[ri]
            if dleft[d] == 0: di += 1; continue
            if rleft[r] == 0: ri += 1; continue
            amt = min(dleft[d], rleft[r])
            pairs.append((d, r, amt, 'normal'))
            dleft[d] -= amt; rleft[r] -= amt
            left_b[d] -= amt; left_g[r] -= amt

    def priority_phase():
        nonlocal pbudget_total
        if recip_m <= 0:
            return
        prop = {}
        for d in sorted(donors):
            pb = budget[d] * recip_m // MILLE
            pbudget_total += pb
            if pb <= 0:
                continue
            mem = amem_pre.get(d, {})
            targets = [r for r in sorted(receivers) if r in mem and left_g[r] > 0]
            if not targets:
                continue
            # 权重 = 记得对方帮过我的累计量，**只决定相对份额，不是额度上限**。
            # 这里必须用 proportional_share：用 largest_remainder 会让"够分时各拿全额"
            # 把历史受助量变成回助上限（本轮修掉的缺陷）。
            w = {r: max(mem[r][0], 1) for r in targets}
            total = min(pb, sum(left_g[r] for r in targets))
            alloc = proportional_share(targets, w, total)
            for r in targets:
                a = alloc[r] if 'recipover' in P else min(alloc[r], left_g[r])
                if a > 0:
                    prop[(d, r)] = a
        if 'recipseq' in P:                       # 注入：按遍历序边算边扣，不统一裁决
            seq = order or sorted(donors)
            for d in [x for x in seq if x in donors]:
                for r in sorted(receivers):
                    a = prop.get((d, r), 0)
                    if a <= 0: continue
                    a = min(a, left_g[r], left_b[d])
                    if a <= 0: continue
                    pairs.append((d, r, a, 'recip'))
                    left_b[d] -= a; left_g[r] -= a
            return
        by_r = {}
        for (d, r) in prop:
            by_r.setdefault(r, []).append(d)
        for r in sorted(by_r):
            ds = sorted(by_r[r])
            tot = sum(prop[(d, r)] for d in ds)
            if tot > left_g[r] and 'recipover' not in P:      # 统一裁决：按提议额比例裁减
                cut = largest_remainder(ds, {d: prop[(d, r)] for d in ds}, left_g[r])
                for d in ds:
                    prop[(d, r)] = cut[d]
        for (d, r) in sorted(prop):
            a = prop[(d, r)]
            if a <= 0: continue
            pairs.append((d, r, a, 'recip'))
            left_g[r] -= a
            if 'recipbudget' not in P:
                left_b[d] -= a      # 注入 recipbudget：优先支出不从总预算里扣 -> 真的会超预算
            
    if 'recipsame' in P:
        # 注入：先普通后优先（若本轮转移能立刻制造回助资格，这里就会暴露）。
        # 实际上它是空转的：优先的方向是"供给方回报曾帮过自己的人"，
        # 而本轮的接收方都是缺粮方，不可能在同一轮里变成供给方。原因写在规格里。
        normal_phase(); priority_phase()
    else:
        priority_phase(); normal_phase()
    return pairs, S, D, pbudget_total


def aid_memory_error(st) -> int:
    """记忆账恒等：在世群体记住的总量 + 随消失丢失的总量 == 实际援助总量。
    子群体不继承记忆，所以这条是精确等式；一次实际援助只会被记一次。"""
    alive = sum(v[0] for b in st['bands'].values() for v in b['amem'].values())
    return alive + st['amem_dropped_kcal'] - st['aid_kcal']


def amem_dangling(st) -> int:
    """指向已经消失的群体的记忆条目数：它们确实帮过我，但再也无法回助。"""
    alive = set(st['bands'])
    return sum(1 for b in st['bands'].values() for k in b['amem'] if k not in alive)


def mutual_pair_count(st) -> int:
    """重复往来：双向都发生过援助的群体对数（从 aid_log 直接数，一次转移只算一次）。"""
    seen = set()
    for rec in st['aid_log']:
        seen.add((rec[2], rec[3]))
    return sum(1 for (a, b) in seen if (b, a) in seen and a < b)


def proportional_share(keys, weight, total):
    """按 weight 的**相对比例**把 total 整数分完：取整商 + 余数（余数降序、band_id 升序）。

    与 `largest_remainder` 的区别，是本轮修掉的那个缺陷的要害：
      * `largest_remainder` 里 weight 是**上限**（预算 / 缺口），所以"够分时各拿全额"是对的；
      * 这里 weight 只是**相对优先权重**（记得对方帮过自己的累计量），**不是上限**。
        用前者会让"历史受助量"意外变成本轮回助额度的天花板 —— 历史是排序依据，不是债务额度。
    因此本函数**永远把 total 分完**（受 total 与权重是否为 0 约束），不看 total 与权重和的大小关系。
    """
    ks = sorted(keys)
    W = sum(weight[k] for k in ks)
    if W <= 0 or total <= 0:
        return {k: 0 for k in ks}
    base = {k: weight[k] * total // W for k in ks}
    rem = total - sum(base.values())
    rank = sorted(ks, key=lambda k: (-(weight[k] * total % W), k))
    for i in range(rem):
        base[rank[i % len(rank)]] += 1
    return base


def make_world(seed: int, poison: str = "", sigma_m: int = 0, move_mort_m: int = 0,
               share_m: int = 0, aid_m: int = 0, recip_m: int = 0, farm_m: int = 0):
    split_poisons(poison)          # 未登记的注入标志立刻报错，不许静默通过
    # 先查类型再查范围。顺序不能反：浮点的 sigma_m 会让 stock 整个变成 float，
    # 而守恒误差会是 0.0（浮点相等），守恒检验抓不到它——类型检查不能用守恒检验代替。
    # bool 是 int 的子类，必须单独排除，否则 True 会被静默当成 sigma_m=1。
    if isinstance(sigma_m, bool) or not isinstance(sigma_m, int):
        raise TypeError(f"SIGMA_M 必须是严格整数（不接受 bool），"
                        f"收到 {sigma_m!r} ({type(sigma_m).__name__})")
    if not (SIGMA_M_MIN <= sigma_m <= SIGMA_M_MAX):
        raise ValueError(f"SIGMA_M={sigma_m} 越界，合法范围 [{SIGMA_M_MIN}, {SIGMA_M_MAX}]")
    if isinstance(move_mort_m, bool) or not isinstance(move_mort_m, int):
        raise TypeError(f"MOVE_MORT_M 必须是严格整数（不接受 bool），"
                        f"收到 {move_mort_m!r} ({type(move_mort_m).__name__})")
    if not (MOVE_MORT_M_MIN <= move_mort_m <= MOVE_MORT_M_MAX):
        raise ValueError(f"MOVE_MORT_M={move_mort_m} 越界，"
                         f"合法范围 [{MOVE_MORT_M_MIN}, {MOVE_MORT_M_MAX}]")
    if isinstance(share_m, bool) or not isinstance(share_m, int):
        raise TypeError(f"SHARE_M 必须是严格整数（不接受 bool），"
                        f"收到 {share_m!r} ({type(share_m).__name__})")
    if not (SHARE_M_MIN <= share_m <= SHARE_M_MAX):
        raise ValueError(f"SHARE_M={share_m} 越界，合法范围 [{SHARE_M_MIN}, {SHARE_M_MAX}]")
    if isinstance(aid_m, bool) or not isinstance(aid_m, int):
        raise TypeError(f"AID_M 必须是严格整数（不接受 bool），"
                        f"收到 {aid_m!r} ({type(aid_m).__name__})")
    if not (AID_M_MIN <= aid_m <= AID_M_MAX):
        raise ValueError(f"AID_M={aid_m} 越界，合法范围 [{AID_M_MIN}, {AID_M_MAX}]")
    if isinstance(recip_m, bool) or not isinstance(recip_m, int):
        raise TypeError(f"RECIP_M 必须是严格整数（不接受 bool），"
                        f"收到 {recip_m!r} ({type(recip_m).__name__})")
    if not (RECIP_M_MIN <= recip_m <= RECIP_M_MAX):
        raise ValueError(f"RECIP_M={recip_m} 越界，合法范围 [{RECIP_M_MIN}, {RECIP_M_MAX}]")
    if isinstance(farm_m, bool) or not isinstance(farm_m, int):
        raise TypeError(f"FARM_M 必须是严格整数（不接受 bool），"
                        f"收到 {farm_m!r} ({type(farm_m).__name__})")
    if not (FARM_M_MIN <= farm_m <= FARM_M_MAX):
        raise ValueError(f"FARM_M={farm_m} 越界，合法范围 [{FARM_M_MIN}, {FARM_M_MAX}]")
    st = {'tick': 0, 'seed': seed, 'poison': poison, 'sigma_m': sigma_m,
          'move_mort_m': move_mort_m, 'share_m': share_m, 'aid_m': aid_m,
          'recip_m': recip_m, 'farm_m': farm_m,
          # --- EXP-07 唯一新增机制：原始耕作与弃耕 ---
          # 耕地**属于地点**，不属于会移动的群体：field_m[格] 是那一格的耕作规模刻度。
          # 没有土地所有权、地主、税收、灌溉与产权冲突，也没有 settled 标志。
          'field_m': {},
          'farm_effort_cum': 0,       # 投进耕作的折算劳动刻度（含投不下去的部分）
          'farm_effort_used_cum': 0,  # 其中真正用上的（维护 + 开垦）
          'farm_potential_cum': 0,    # 潜在产出（维护过的耕地能长出多少）
          'farm_harvest_cum': 0,      # **实际采收**并进入库存的部分（inflow 的来源分项）
          'farm_uncollected_cum': 0,  # 潜在减实际：没人去收的，不转给别人、不留到明年
          'field_built_cum': 0,       # 累计开垦出来的刻度
          'field_decay_cum': 0,       # 累计退化掉的刻度
          'farm_log': [],             # 耕作事件：field_built / farm_harvest / field_decay
          'farm_effort_trace': {},    # 只读痕迹：{bid: (人数, 耕作刻度, 采集刻度)}，不进哈希
          # 援助记忆与优先回助的账（EXP-06 新增）
          'recip_budget': 0,        # 走优先阶段的预算合计
          'recip_kcal': 0,          # 优先阶段实际转移的数量
          'recip_transfers': 0,     # 优先阶段的笔数
          'recip_changed': 0,       # **只读诊断**：优先规则确实改变了分配的"格×年"次数
          'repay_kcal': 0,          # 供给方记得对方帮过自己的那些转移（回助）的数量
          'repay_transfers': 0,     # 同上，笔数
          'amem_dropped_kcal': 0,   # 随群体消失而丢失的记忆量（记账用，保证记忆账闭合）
          'amem_entries_dropped': 0,
          # 援助账（EXP-05 新增）。注意两个计数不是一回事：
          #   aid_events   = 发生过援助的“格 × 年”次数（一次多人援助活动算 1）
          #   aid_transfers= 逐笔转移的笔数（一个供给方给一个接收方算 1 笔）
          'aid_events': 0, 'aid_transfers': 0, 'aid_kcal': 0,
          'aid_donors': 0, 'aid_receivers': 0,
          'aid_supply': 0, 'aid_demand': 0,   # 当年可援助预算 / 当年缺口（同格、参与格内）
          'aid_log': [],                      # (tick, 格, 供给方, 接收方, 数量 kcal, 阶段, 是否回助)
          'aid_pre': {},                      # 援助前状态快照（每 tick 重写，不进哈希）
          # 信息账（EXP-04 新增）：收到 = 采纳 + 拒绝；采纳的条目必须来自交换前快照
          'share_groups': 0, 'share_participants': 0, 'share_received': 0,
          'share_adopted': 0, 'share_rejected': 0,
          'share_log': [],              # (tick, 格, 来源, 接收者, 记忆的格, 值, 时戳)
          'share_decision_changed': 0,  # 只读诊断：交换是否改变了当年的迁移目标
          'pre_mem': {}, 'pre_cells': {},   # 交换前快照，供诊断与检验使用（不进哈希）
          'stock': {}, 'cap': {}, 'regen': {}, 'bands': {},
          'inflow': 0, 'out_eat': 0, 'out_spoil': 0, 'out_move': 0, 'out_lost': 0,
          'log': [], 'mig_total': 0, 'mig_regret': 0, 'next_ctr': 0, 'stale_sum': 0,
          'prop_total': 0, 'prop_conflict': 0,
          'clim_nominal': 0, 'clim_planned': 0, 'clim_credited': 0, 'clim_capped': 0,
          'clim_ctr': 0, 'deficit_cum': 0, 'trace_clim': None,
          'mig_deaths_cum': 0, 'births_cum': 0, 'deaths_demo_cum': 0,
          'need_cum': 0, 'personyear_cum': 0, 'macc_global': 0}
    for i in cells():
        st['field_m'][i] = 0              # 开局全部为 0；不可通行格**始终**为 0
        if not passable(i):
            st['cap'][i] = 0; st['regen'][i] = 0; st['stock'][i] = 0; continue
        h = rng(seed, 9, 0, i, 0)
        # 静态：容量 60–140 人年，年再生 = 容量的 0.20–0.40
        cap = (60 + h % 81) * NEED_PC
        st['cap'][i] = cap
        st['regen'][i] = cap * (200 + (h >> 20) % 201) // MILLE
        st['stock'][i] = cap // 2
    st['start_stock'] = sum(st['stock'].values())
    # 初始 6 个 band，每区 3 个，各 20 人
    init = [i for i in cells() if passable(i)]
    picks = [init[k] for k in (0, 10, 20, 4, 14, 22)]
    for k, c in enumerate(picks):
        bid = eid_of(0xC0FFEE, 0, k)
        st['bands'][bid] = {'cell': c, 'size': 20, 'store': 5 * NEED_PC,
                            'bacc': 0, 'dacc': 0, 'macc': 0,
                            'mem': {c: st['stock'][c]}, 'memt': {c: 0},
                            'amem': {}}          # 援助记忆：谁实际援助过我
    st['start_store'] = sum(b['store'] for b in st['bands'].values())
    st['pop_start'] = sum(b['size'] for b in st['bands'].values())
    return st

def lerp_m(x_m, x0, x1, y0, y1):
    if x_m <= x0: return y0
    if x_m >= x1: return y1
    return y0 + (y1 - y0) * (x_m - x0) // (x1 - x0)

# ---------- 运行身份 vs 动态状态摘要 ----------
# 两者必须分开：
#   run_id      = 这是"哪一次运行"（世界种子、初始禀赋、规则参数、语义注入）
#   state_hash  = 这次运行"当前长什么样"（全部动态状态）
# 单靠 state_hash 不能识别一次运行：它不含 seed 与初始存量，两次不同的运行
# 在原理上可以撞出同一个 state_hash 而我们无从分辨。

# 注入标志分两类。分错会让 T6/T7 假失败或假通过，所以这里是封闭集合 + 拒绝未知名。
TRAVERSAL_POISONS = frozenset({'order', 'revorder',   # 群体遍历顺序
                               'cellrev'})            # 资源格遍历顺序（EXP-02 新增）
SEMANTIC_POISONS  = frozenset({'float', 'seq', 'seqsplit',
                               'clamp', 'counter', 'omniscient',
                               'climseq',             # 波动按调用序而非坐标寻址（EXP-02 新增）
                               'mortseq',             # 迁移死亡用全局累加器而非每群体独立（EXP-03 新增）
                               'mortstrength',        # step 内实际强度改成 min(mm+1,1000)（EXP-03 新增）
                               # --- EXP-04 新增：针对信息交换的六个注入 ---
                               'shareseq',            # 顺序链式合并：读本相位刚更新的中间结果
                               'sharefab',            # 凭空改值：采纳时把存量 +1
                               'sharefresh',          # 刷新时戳：把来源时戳改成当年
                               'shareleak',           # 顺带搬运物质：采纳时挪 1 kcal 储存
                               'sharecross',          # 跨格传播：把不同格的群体拉进候选池
                               'sharediag',           # 诊断计数回灌规则
                               # --- EXP-05 新增：针对食物援助的六个注入 ---
                               'aidseq',              # 顺序结算：按遍历序边算边给
                               'aidfab',              # 凭空生粮：接收方多拿 1
                               'aidovergap',          # 接收超过自己的缺口
                               'aidoverbudget',       # 供给超过预算（动用自己的口粮）
                               'aidcross',            # 跨格送粮
                               'aidregift',           # 本相位内把刚收到的粮再转赠出去
                               # --- EXP-06 新增：针对援助记忆与优先回助的六个注入 ---
                               'recipseq',            # 优先阶段按遍历序边算边扣，不统一裁决
                               'recipover',           # 优先阶段无视接收方缺口上限
                               'recipbudget',         # 优先预算另开一份，总量超过供给预算
                               'recipfab',            # 记忆凭空增加（不来自实际转移）
                               'recipsame',           # 先普通后优先，并用本轮刚更新的记忆
                               'recipdiag',           # 只读诊断计数回灌规则
                               # --- EXP-07 新增：针对耕作的六个注入 ---
                               'farmfree',            # 农业照投，采集仍按全员人数算（白赚劳动）
                               'farmnow',             # 本年新开垦的地当年就收（应当只影响下一年）
                               'farmnodecay',         # 无人维护的耕地不退化
                               'farmcap',             # 无视单格耕地上限
                               'farmgift',            # 未采收的产出转给同格其他人
                               'farmlimit'})          # 采收无视各自的采收限额

def split_poisons(poison: str):
    """返回 (语义注入集合, 遍历注入集合)。未知名字直接报错，不许静默当成非语义。"""
    tags = {x for x in poison.split(',') if x} if poison else set()
    unknown = tags - TRAVERSAL_POISONS - SEMANTIC_POISONS
    if unknown:
        raise ValueError(f"未登记的注入标志: {sorted(unknown)}；"
                         f"必须显式归入 TRAVERSAL_POISONS 或 SEMANTIC_POISONS")
    return tags & SEMANTIC_POISONS, tags & TRAVERSAL_POISONS

PARAM_NAMES = ('NEED_PC', 'MILLE', 'STORE_YEARS_M', 'SPOIL_M', 'K_HALF',
               'MOVE_LOSS_M', 'SPLIT_SIZE', 'MIG_E_M', 'MIG_GAIN_M', 'SHOCK_P_M',
               'E_BLO_M', 'E_BHI_M', 'B_MAX_M',
               'E_D2_M', 'E_D1_M', 'E_D0_M', 'D_AT_D2_M', 'D_AT_D1_M', 'D_AT_D0_M',
               'W', 'H',
               # EXP-07：耕作的三个固定常量也进指纹
               'FIELD_CAP_M', 'FIELD_DECAY_M', 'FARM_YIELD_M')

def params_fingerprint(sigma_m: int = None, move_mort_m: int = None,
                       share_m: int = None, aid_m: int = None,
                       recip_m: int = None, farm_m: int = None) -> str:
    """全部规则参数 + 地图形状 + 五个旧参数 + FARM_M 的指纹。"""
    g = globals()
    h = hashlib.blake2b(digest_size=8)
    h.update(b"EXP07;")
    if sigma_m is not None:
        h.update(f"SIGMA_M={sigma_m};".encode())
    if move_mort_m is not None:
        h.update(f"MOVE_MORT_M={move_mort_m};".encode())
    if share_m is not None:
        h.update(f"SHARE_M={share_m};".encode())
    if aid_m is not None:
        h.update(f"AID_M={aid_m};".encode())
    if recip_m is not None:
        h.update(f"RECIP_M={recip_m};".encode())
    if farm_m is not None:
        h.update(f"FARM_M={farm_m};".encode())
    for n in PARAM_NAMES:
        h.update(f"{n}={g[n]};".encode())
    h.update(("BARRIER_COLS=" + ",".join(map(str, sorted(BARRIER_COLS))) + ";").encode())
    return h.hexdigest()

def run_id(st) -> str:
    """一次运行的身份。**不含遍历注入**——改遍历方式不改变这是哪一次运行，
    否则 T6/T7 会把"同一次运行的两种遍历"误判成两次不同的运行。"""
    sem, _trav = split_poisons(st['poison'])
    h = hashlib.blake2b(digest_size=16)
    h.update(f"seed={st['seed']};".encode())
    h.update(f"start_stock={st['start_stock']};start_store={st['start_store']};".encode())
    h.update(f"pop_start={st['pop_start']};".encode())   # 初始人口也是运行身份的一部分
    h.update(("semantic=" + ",".join(sorted(sem)) + ";").encode())
    h.update(f"params={params_fingerprint(st['sigma_m'], st['move_mort_m'], st['share_m'], st['aid_m'], st['recip_m'])};".encode())
    return h.hexdigest()

def full_digest(st) -> str:
    """对外比较两次运行时应当用的东西：身份 + 状态。"""
    return f"{run_id(st)}/{state_hash(st)}"


BAND_FIELDS = ('cell', 'size', 'store', 'bacc', 'dacc', 'macc')

def _band_blob(bid, d) -> bytes:
    """一个群体的完整可演化状态。凡是会影响后续演化的字段都必须在这里，
    包括 mem / memt —— 少写一个字段，确定性检验就会漏掉整整一类 bug。"""
    parts = [str(bid)] + [str(d[f]) for f in BAND_FIELDS]
    parts.append('mem{' + ','.join(f"{c}={d['mem'][c]}" for c in sorted(d['mem'])) + '}')
    parts.append('memt{' + ','.join(f"{c}={d['memt'][c]}" for c in sorted(d['memt'])) + '}')
    # EXP-06 新增：援助记忆也是会影响后续演化的状态，必须进哈希
    am = d.get('amem', {})
    parts.append('amem{' + ','.join(f"{k}={am[k][0]}@{am[k][1]}" for k in sorted(am)) + '}')
    return (':'.join(parts) + ';').encode()

LEDGER_FIELDS = ('inflow', 'out_eat', 'out_spoil', 'out_move', 'out_lost',
                 'mig_total', 'mig_regret', 'stale_sum', 'next_ctr',
                 'prop_total', 'prop_conflict',
                 # EXP-02 新增。资源账：名义 / 计划 / 实际入账 / 被容量挡住
                 'clim_nominal', 'clim_planned', 'clim_credited', 'clim_capped',
                 'clim_ctr', 'deficit_cum', 'sigma_m',
                 # EXP-03 新增：人口分项账 + 需求/人年账 + 迁移死亡
                 'move_mort_m', 'mig_deaths_cum', 'births_cum', 'deaths_demo_cum',
                 'need_cum', 'personyear_cum', 'macc_global',
                 # EXP-04 新增：参数 + 信息账 + 只读诊断
                 'share_m', 'share_groups', 'share_participants',
                 'share_received', 'share_adopted', 'share_rejected',
                 'share_decision_changed',
                 # EXP-05 新增：参数 + 援助账
                 'aid_m', 'aid_events', 'aid_transfers', 'aid_kcal',
                 'aid_donors', 'aid_receivers', 'aid_supply', 'aid_demand',
                 # EXP-06 新增：参数 + 优先回助账 + 记忆账
                 'recip_m', 'recip_budget', 'recip_kcal', 'recip_transfers',
                 'recip_changed', 'repay_kcal', 'repay_transfers',
                 'amem_dropped_kcal', 'amem_entries_dropped',
                 # EXP-07 新增：参数 + 劳动 / 耕地 / 产出账
                 'farm_m', 'farm_effort_cum', 'farm_effort_used_cum',
                 'farm_potential_cum', 'farm_harvest_cum', 'farm_uncollected_cum',
                 'field_built_cum', 'field_decay_cum')

# 基线（EXP-01）自己的字段集合。A1 退化检验用基线自己的哈希函数判定，
# 不用 EXP-02 的——否则就是把基线改成能通过的样子。
EXP01_LEDGER_FIELDS = ('inflow', 'out_eat', 'out_spoil', 'out_move', 'out_lost',
                          'mig_total', 'mig_regret', 'stale_sum', 'next_ctr',
                          'prop_total', 'prop_conflict')

def state_hash(st) -> str:
    """全状态哈希：tick + 每格 stock/cap/regen + 每个群体的完整状态 + 全部账本计数。"""
    h = hashlib.blake2b(digest_size=16)
    h.update(f"tick={st['tick']};".encode())
    for i in sorted(st['stock']):
        h.update(f"{i}:{st['stock'][i]}:{st['cap'][i]}:{st['regen'][i]};".encode())
    # EXP-07：耕地是跨年保留的世界状态，必须进哈希，
    # 否则"只污染耕地"的一整类 bug 能安静通过（EXP-01 漏 mem/memt 栽过一次）。
    for i in sorted(st.get('field_m', {})):
        h.update(f"F{i}={st['field_m'][i]};".encode())
    for bid in sorted(st['bands']):
        h.update(_band_blob(bid, st['bands'][bid]))
    for f in LEDGER_FIELDS:
        h.update(f"{f}={st[f]};".encode())
    return h.hexdigest()

def region_hash(st, reg) -> str:
    """区块哈希：只含该区块的格与群体的完整状态。
    不含全局账本计数（它们跨区块累加，天然会被另一区块的干预改变）。"""
    h = hashlib.blake2b(digest_size=16)
    for i in sorted(st['stock']):
        if region(i) == reg:
            h.update(f"{i}:{st['stock'][i]}:{st['cap'][i]}:{st['regen'][i]};".encode())
    for bid in sorted(st['bands']):
        d = st['bands'][bid]
        if region(d['cell']) == reg:
            h.update(_band_blob(bid, d))
    return h.hexdigest()

def step(st, suppress_split_in=None):
    P = set(st['poison'].split(',')) if st['poison'] else set()
    t = st['tick']; seed = st['seed']
    # --- 相位 1 regen（EXP-02：叠加年际波动）---
    cell_order = sorted(st['stock'])
    if 'cellrev' in P: cell_order = list(reversed(cell_order))
    sig = st['sigma_m']
    # EXP-07：把本 tick 每格的天气扰动 z 记下来，农业相位直接复用**同一次抽样**，
    # 不新开随机流、不改变原有抽样点。每 tick 重写，不进哈希。
    st['clim_z'] = {}
    for i in cell_order:
        if st['cap'][i] == 0: continue
        base_r = st['regen'][i]
        if sig > 0:
            if 'climseq' in P:
                # 注入：按调用序推进，而不是按 (tick, cell) 坐标寻址
                k = st['clim_ctr']; st['clim_ctr'] += 1
                u1 = rng(seed, S_CLIM, k, 0, 0) % (sig + 1)
                u2 = rng(seed, S_CLIM, k, 0, 1) % (sig + 1)
            else:
                u1 = rng(seed, S_CLIM, t, i, 0) % (sig + 1)
                u2 = rng(seed, S_CLIM, t, i, 1) % (sig + 1)
            z = u1 - u2                       # 离散三角，支撑 [-sig, +sig]，众数 0
            st['clim_z'][i] = z
            if st.get('trace_clim') is not None: st['trace_clim'][(t, i)] = z
            r_eff = base_r * (MILLE + z) // MILLE      # 整数除法，向下取整
        else:
            r_eff = base_r                    # sig=0 时严格恒等，无取整损失
        st['clim_nominal'] += base_r
        st['clim_planned'] += r_eff
        new = min(st['cap'][i], st['stock'][i] + r_eff)
        credited = new - st['stock'][i]
        st['clim_credited'] += credited
        st['clim_capped'] += r_eff - credited
        st['inflow'] += credited
        st['stock'][i] = new
    order = list(st['bands']) if 'order' in P else (sorted(st['bands'], reverse=True) if 'revorder' in P else sorted(st['bands']))
    # --- 相位 2 forage：同时结算，与遍历顺序无关 ---
    # 2a 各自独立算索取量（只看进入本相位时的存量）
    # EXP-07：先冻结本 tick 人口变化前的劳动预算。N 人 = N×1000 个折算劳动刻度，
    # 其中 FARM_M/1000 投到耕作、其余投到野外采集。
    # **不能"野外照拿全额、农业白赚一份"**：采集公式里的人数换成了实际投入采集的劳动。
    fm = st['farm_m']
    st['farm_effort_trace'] = {}
    farm_effort = {}; forage_effort = {}; collection_limit = {}
    claim = {}; by_cell = {}
    for bid in order:
        b = st['bands'][bid]; c = b['cell']
        need = b['size'] * NEED_PC
        room = max(0, b['size'] * NEED_PC * STORE_YEARS_M // MILLE - b['store'])
        farm_effort[bid] = b['size'] * fm
        forage_effort[bid] = b['size'] * MILLE - farm_effort[bid]
        collection_limit[bid] = need + room
        # 只读痕迹（每 tick 重写，不进哈希）：供劳动预算恒等式逐年核对
        st['farm_effort_trace'][bid] = (b['size'], farm_effort[bid], forage_effort[bid])
        fe = forage_effort[bid]
        s0 = st['stock'][c]
        if 'float' in P:
            got = int(s0 * (fe / (fe + K_HALF * MILLE)))         # 浮点污染
        elif 'farmfree' in P:
            # 注入：农业照投，采集却仍按全员人数算 —— 白赚一份劳动
            got = s0 * b['size'] // (b['size'] + K_HALF)
        else:
            # FARM_M=0 时 fe = size*1000，与原式 s0*size//(size+K_HALF) 逐位相同
            got = s0 * fe // (fe + K_HALF * MILLE)
        claim[bid] = min(got, collection_limit[bid], s0)
        by_cell.setdefault(c, []).append(bid)
    # 2b 逐格按比例整数分配；余数按 (余数降序, band_id 升序) 派发
    harvest = {}
    if 'seq' in P:                                            # 注入：回到顺序结算
        for bid in order:
            c = st['bands'][bid]['cell']
            g = min(claim[bid], st['stock'][c])
            st['stock'][c] -= g; harvest[bid] = g
    else:
        for c, bids in by_cell.items():
            bids = sorted(bids)
            tot = sum(claim[x] for x in bids); s0 = st['stock'][c]
            if tot <= s0:
                for x in bids: harvest[x] = claim[x]
            else:
                give = {x: claim[x] * s0 // tot for x in bids}
                rem = s0 - sum(give.values())
                rank = sorted(bids, key=lambda x: (-(claim[x] * s0 % tot), x))
                for k in range(rem): give[rank[k % len(rank)]] += 1
                for x in bids: harvest[x] = give[x]
            st['stock'][c] = s0 - sum(harvest[x] for x in bids)
    for bid in order:
        b = st['bands'][bid]
        b['mem'][b['cell']] = st['stock'][b['cell']]          # 只记得自己格的当年值
    # --- 相位 2b farm：原始耕作与弃耕（EXP-07 唯一新增机制）---
    # 位置：**野外采集结算之后、援助 2c 之前**。
    #
    # 耕地属于地点：每个可通行格（**包括当年没人的格**）都按同一套规则结算。
    #   已有地先占用维护劳动 -> 剩下的劳动去开垦 -> 没维护到的那部分退化。
    #   本年产出只用**相位前的旧 F**：不能先开垦再立刻收获。
    #   新开垦的地只影响下一年。
    farm_cell_crop = {bid: 0 for bid in st['bands']}
    farm_by_cell = {}
    for bid in order:
        if farm_effort[bid] > 0:
            farm_by_cell.setdefault(st['bands'][bid]['cell'], []).append(bid)
    farm_cells = sorted(st['stock'])
    if 'cellrev' in P:
        farm_cells = list(reversed(farm_cells))
    for c in farm_cells:
        if not passable(c):
            st['field_m'][c] = 0          # 不可通行格始终是 0
            continue
        F = st['field_m'][c]
        movers = sorted(farm_by_cell.get(c, []))
        L = sum(farm_effort[x] for x in movers)
        if F == 0 and L == 0:
            continue                      # 没地也没人投劳动：这一格今年什么都没发生
        st['farm_effort_cum'] += L
        worked = min(F, L)
        unworked = F - worked
        if 'farmnodecay' in P:
            decayed = 0                   # 注入：无人维护也不退化
        else:
            decayed = (unworked * FIELD_DECAY_M + MILLE - 1) // MILLE   # 向上取整
        room_field = FIELD_CAP_M - (F - decayed)
        want_build = max(0, L - F)
        if 'farmcap' in P:
            built = want_build            # 注入：无视单格上限
        else:
            built = min(room_field, want_build)
        st['farm_effort_used_cum'] += worked + built
        st['field_built_cum'] += built
        st['field_decay_cum'] += decayed

        # 产量：复用相位 1 **同一个抽样点**的天气扰动，不新开随机流。
        weather_m = MILLE + st['clim_z'].get(c, 0) if st['sigma_m'] > 0 else MILLE
        yield_base = (F - decayed + built) if 'farmnow' in P else worked
        potential = yield_base * NEED_PC * FARM_YIELD_M * weather_m // (MILLE ** 3)
        st['farm_potential_cum'] += potential

        got_here = {}
        if potential > 0 and movers:
            # 按各群体投入耕作的劳动的**相对比例**分潜在产出。
            # 必须用 proportional_share：权重是相对份额，**不是额度上限**。
            share = proportional_share(movers, {x: farm_effort[x] for x in movers}, potential)
            for x in movers:
                b = st['bands'][x]
                if 'farmlimit' in P:
                    room_left = share[x]          # 注入：无视各自的采收限额
                else:
                    room_left = max(0, collection_limit[x] - harvest[x])
                crop = min(share[x], room_left)
                got_here[x] = crop
                farm_cell_crop[x] += crop
        collected = sum(got_here.values())
        if 'farmgift' in P and movers and potential > collected:
            # 注入：没人收的产出转给同格其他人（本来应当就地作废）
            extra = potential - collected
            got_here[movers[0]] = got_here.get(movers[0], 0) + extra
            farm_cell_crop[movers[0]] += extra
            collected = potential
        uncollected = potential - collected
        st['farm_harvest_cum'] += collected
        st['farm_uncollected_cum'] += uncollected
        st['inflow'] += collected         # **只在这里把实际采收计入 inflow 一次**
        st['field_m'][c] = F - decayed + built

        # 事件：同格同年同类型聚合成一条，保留参与者明细；只有实际量 > 0 才记。
        if built > 0:
            st['farm_log'].append({
                'tick': t, 'type': 'field_built', 'cell': c,
                'bands': list(movers), 'labour_m': L, 'labour_used_m': worked + built,
                'field_before_m': F, 'field_after_m': st['field_m'][c], 'amount_m': built,
                'per_band_labour_m': {x: farm_effort[x] for x in movers},
                'source': "模型状态 st['field_m'] 与本相位的劳动结算"})
        if collected > 0:
            st['farm_log'].append({
                'tick': t, 'type': 'farm_harvest', 'cell': c,
                'bands': sorted(x for x in got_here if got_here[x] > 0),
                'labour_m': L, 'labour_used_m': worked,
                'field_before_m': F, 'field_after_m': st['field_m'][c],
                'worked_m': worked, 'weather_m': weather_m,
                'potential_kcal': potential, 'kcal': collected,
                'uncollected_kcal': uncollected,
                'per_band_kcal': {x: v for x, v in sorted(got_here.items()) if v > 0},
                'source': "模型日志 st['farm_log']（潜在产出按投入耕作的劳动比例分配）"})
        if decayed > 0:
            st['farm_log'].append({
                'tick': t, 'type': 'field_decay', 'cell': c,
                'bands': list(movers), 'labour_m': L, 'labour_used_m': worked,
                'field_before_m': F, 'field_after_m': st['field_m'][c],
                'unworked_m': unworked, 'amount_m': decayed,
                'source': "模型状态 st['field_m']：没有劳动维护的部分按 FIELD_DECAY_M 退化"})
    # 把当年农业采收并进 harvest，后面的援助 / 消费 / 人口 / 迁移 / 分裂公式一个字不改
    for bid in order:
        harvest[bid] += farm_cell_crop[bid]

    # --- 相位 2c aid：同格食物援助 + 优先回助（EXP-06）---
    # 位置：采集结算之后、消费之前。可用粮食 avail = 当年采集 + 原有储粮。
    # 供给方先保留自己当年的需求 need，只有 avail − need 的部分可以援助；
    # 预算 = 那部分的 AID_M/1000（向下取整）。接收方最多补齐 need − avail 的缺口。
    #
    # 两个阶段**统一核算**（见 settle_cell）：
    #   优先阶段：把预算的 RECIP_M/1000 先分给"过去帮过我、现在又缺粮"的同格群体；
    #             各供给方**独立提议** → 同一接收方被多家提议时**统一按提议额裁决** → 一次提交。
    #   普通阶段：优先阶段没用掉的预算 + 其余预算，按 EXP-05 原规则分配。
    # 优先阶段只读**本年援助之前**的关系快照；结算完才更新记忆。
    aid_in = {bid: 0 for bid in st['bands']}
    aid_out = {bid: 0 for bid in st['bands']}
    st['aid_pre'] = {}          # 援助前状态快照：{bid: (avail, need, cell)}；不进哈希
    # 只读诊断：同一份援助前状态下"开优先回助"与"关优先回助"各算一遍的逐笔结果。
    # 这是**观察数据**，每 tick 重写，不进哈希，也不回灌规则（poison-recipdiag 盯着）。
    st['recip_compare'] = []
    am = st['aid_m']
    if am > 0:
        pre_avail = {bid: harvest.get(bid, 0) + st['bands'][bid]['store']
                     for bid in st['bands']}
        pre_need = {bid: st['bands'][bid]['size'] * NEED_PC for bid in st['bands']}
        st['aid_pre'] = {bid: (pre_avail[bid], pre_need[bid], st['bands'][bid]['cell'])
                         for bid in st['bands']}
        # 关系快照：本年援助之前的记忆，优先阶段只读它
        amem_pre = {bid: {k: list(vv) for k, vv in st['bands'][bid]['amem'].items()}
                    for bid in st['bands']}
        st['amem_pre'] = amem_pre
        groups = {}
        for bid in sorted(st['bands']):
            if st['bands'][bid]['size'] == 0: continue
            groups.setdefault(st['bands'][bid]['cell'], []).append(bid)
        if 'aidcross' in P:                       # 注入：跨格送粮，全图并成一个池子
            groups = {-1: [x for x in sorted(st['bands']) if st['bands'][x]['size'] > 0]}
        committed = []
        for c in sorted(groups):
            members = groups[c]
            if len(members) < 2: continue
            pairs, S, D, pb = settle_cell(members, pre_avail, pre_need, am,
                                          st['recip_m'], amem_pre, P, order)
            st['aid_supply'] += S; st['aid_demand'] += D; st['recip_budget'] += pb
            if not pairs: continue
            # 只读诊断：同一份援助前状态，把 RECIP_M 换成 0 再算一遍。
            # 两次结果不同 ⇒ **优先规则确实改变了分配**（而不是"刚好帮了旧伙伴"）。
            base_pairs, _, _, _ = settle_cell(members, pre_avail, pre_need, am,
                                              0, amem_pre, P, order)
            # "分配改变"比的是**逐对群体的总额**，不是转移笔数。
            # 同一对群体、同样的总额，只是被拆成"优先 + 普通"两笔，**不算**分配改变 ——
            # 那只是记账分阶段，谁拿到多少一点没变。
            changed = alloc_totals(pairs) != alloc_totals(base_pairs)
            if changed:
                st['recip_changed'] += 1
            if st['recip_m'] > 0:
                st['recip_compare'].append({
                    'cell': c, 'changed': bool(changed),
                    'with_recip': [(d, r, a, ph) for d, r, a, ph in pairs],
                    'without_recip': [(d, r, a, ph) for d, r, a, ph in base_pairs],
                    # 逐对总额（判据本身），方便界面直接比"谁拿到多少"
                    'with_totals': [(d, r, a) for (d, r), a in
                                    sorted(alloc_totals(pairs).items())],
                    'without_totals': [(d, r, a) for (d, r), a in
                                       sorted(alloc_totals(base_pairs).items())],
                })
            if 'recipdiag' in P and st['recip_changed'] % 2 == 1:
                continue                          # 注入：只读诊断回灌规则
            st['aid_events'] += 1
            st['aid_transfers'] += len(pairs)
            st['aid_donors'] += len({d for d, _, _, _ in pairs})
            st['aid_receivers'] += len({r for _, r, _, _ in pairs})
            for d, r, amt, phase in pairs:
                repay = r in amem_pre.get(d, {})   # 供给方记得对方帮过自己 = 回助
                got = amt + 1 if 'aidfab' in P else amt
                aid_out[d] += amt
                aid_in[r] += got
                st['aid_kcal'] += amt
                if phase == 'recip':
                    st['recip_kcal'] += amt; st['recip_transfers'] += 1
                if repay:
                    st['repay_kcal'] += amt; st['repay_transfers'] += 1
                st['aid_log'].append((t, c, d, r, amt, phase, 1 if repay else 0))
                committed.append((d, r, amt))
                if 'shareleak' in P and st['bands'][d]['store'] > 0:
                    st['bands'][d]['store'] -= 1; st['bands'][r]['store'] += 1
        # 结算完才更新记忆：接收方记住"谁实际援助了我"，只累加实际转移
        for d, r, amt in committed:
            e = st['bands'][r]['amem'].get(d)
            add = amt + 1 if 'recipfab' in P else amt   # 注入：记忆凭空增加
            if e is None:
                st['bands'][r]['amem'][d] = [add, t]
            else:
                e[0] += add; e[1] = t

    # --- 相位 3 consume ---
    for bid in order:
        b = st['bands'][bid]
        need = b['size'] * NEED_PC
        avail = harvest[bid] + b['store'] + aid_in[bid] - aid_out[bid]
        eat = min(need, avail)
        st['need_cum'] += need                # 累计需求（缺粮的分母）
        st['personyear_cum'] += b['size']     # 累计人年
        st['deficit_cum'] += need - eat       # 未被满足的需求，不是能量流，不进守恒
        st['out_eat'] += eat
        b['store'] = avail - eat
        b['E_m'] = avail * MILLE // need if need else MILLE
    # --- 相位 4 spoil ---
    for bid in order:
        b = st['bands'][bid]
        sp = b['store'] * SPOIL_M // MILLE
        if 'clamp' in P: b['store'] = max(0, b['store'] - sp)  # 掩盖负值的 clamp
        else: b['store'] -= sp
        st['out_spoil'] += sp
    # --- 相位 5 demography ---
    for bid in order:
        b = st['bands'][bid]; E = b['E_m']
        b_m = lerp_m(E, E_BLO_M, E_BHI_M, 0, B_MAX_M)
        if E >= E_D1_M:
            d_m = lerp_m(E, E_D1_M, E_D2_M, D_AT_D1_M, D_AT_D2_M)
        else:
            d_m = lerp_m(E, E_D0_M, E_D1_M, D_AT_D0_M, D_AT_D1_M)
        u = rng(seed, S_SHOCK, t, bid, 0) % MILLE
        if u < SHOCK_P_M:
            d_m += 100 + (rng(seed, S_SHOCK, t, bid, 1) % 3) * 100
        b['bacc'] += b['size'] * b_m
        b['dacc'] += b['size'] * d_m
        births = b['bacc'] // MILLE; b['bacc'] -= births * MILLE
        deaths = b['dacc'] // MILLE; b['dacc'] -= deaths * MILLE
        raw = b['size'] + births - deaths
        # 原规则用 max(0,·) 截断，所以"声称的死亡数"未必等于实际死亡数
        actual_deaths = deaths if raw >= 0 else b['size'] + births
        st['births_cum'] += births
        st['deaths_demo_cum'] += actual_deaths
        b['size'] = max(0, raw)
    # --- 相位 6a scout：每年侦察一个随机邻格，记下当年真值 ---
    for bid in order:
        b = st['bands'][bid]
        if b['size'] == 0: continue
        nb = neighbors(b['cell'])
        if not nb: continue
        j = nb[rng(seed, S_SCOUT, t, bid, 0) % len(nb)]
        b['mem'][j] = st['stock'][j]
        b['memt'][j] = t
    # --- 相位 6a2 share：同格信息交换（EXP-04 唯一新增机制）---
    # 触发条件只有物理条件：同一 tick、同一格、size>0 的参与者 >= 2。
    # 参与与否由 counter-based 抽签决定，key=(seed, S_SHARE, t, bid, 0)；
    # 不看饥饿、不看亲缘、不看历史、不看规模 —— 那些都会引入制度性状态。
    # 合并只读**交换前快照**：同格参与者之间可以直接互相传，但不许读本相位刚更新的中间结果。
    # 采纳规则：同一个格键取 memt 最大者，并列取 band_id 最小者；时戳照抄来源，不刷新。
    #          只有严格比自己新才采纳（时戳相同保留自己，不做无谓改写）。
    st['pre_mem'] = {bid: (dict(b['mem']), dict(b['memt']))
                     for bid, b in st['bands'].items()}
    st['pre_cells'] = {bid: b['cell'] for bid, b in st['bands'].items()}
    sm = st['share_m']
    if sm > 0:
        joined = {}
        for bid in order:
            if bid not in st['bands']:
                continue
            b = st['bands'][bid]
            if b['size'] == 0:
                continue
            if rng(seed, S_SHARE, t, bid, 0) % MILLE < sm:
                joined.setdefault(b['cell'], []).append(bid)
        for c in sorted(joined):
            parts = sorted(joined[c])
            if len(parts) < 2:
                continue                      # 一个人不叫交换
            st['share_groups'] += 1
            st['share_participants'] += len(parts)
            snap = {x: (dict(st['bands'][x]['mem']), dict(st['bands'][x]['memt']))
                    for x in parts}
            if 'sharecross' in P:             # 注入：把不同格的群体也拉进候选池
                for y in sorted(st['bands']):
                    if y not in snap and st['bands'][y]['size'] > 0:
                        snap[y] = (dict(st['bands'][y]['mem']),
                                   dict(st['bands'][y]['memt']))
            for x in parts:
                bx = st['bands'][x]
                pool, seen = {}, 0
                for y in sorted(snap):
                    if y == x:
                        continue
                    if 'shareseq' in P:       # 注入：读活状态（本相位刚被改过的中间结果）
                        my, mt = st['bands'][y]['mem'], st['bands'][y]['memt']
                    else:
                        my, mt = snap[y]
                    for j in sorted(my):
                        tj = mt.get(j, 0)
                        seen += 1
                        cur = pool.get(j)
                        if cur is None or tj > cur[0] or (tj == cur[0] and y < cur[2]):
                            pool[j] = (tj, my[j], y)
                adopted = 0
                for j in sorted(pool):
                    tj, v, donor = pool[j]
                    own_t = bx['memt'].get(j)
                    if own_t is not None and tj <= own_t:
                        continue              # 不比自己的新：不采纳
                    val = v + 1 if 'sharefab' in P else v       # 注入：凭空改值
                    stamp = t if 'sharefresh' in P else tj      # 注入：刷新时戳
                    bx['mem'][j] = val
                    bx['memt'][j] = stamp
                    adopted += 1
                    st['share_log'].append((t, c, donor, x, j, val, stamp))
                    if 'shareleak' in P and st['bands'][donor]['store'] > 0:
                        st['bands'][donor]['store'] -= 1        # 注入：顺带搬运物质
                        bx['store'] += 1                        # 全局守恒查不出来
                st['share_received'] += seen
                st['share_adopted'] += adopted
                st['share_rejected'] += seen - adopted

    # --- 相位 6b migrate ---
    for bid in order:
        b = st['bands'][bid]
        if b['size'] == 0 or b['E_m'] >= MIG_E_M: continue
        here = st['stock'][b['cell']]
        best, bestv = None, here * MIG_GAIN_M // MILLE
        for j in neighbors(b['cell']):
            v = st['stock'][j] if 'omniscient' in P else b['mem'].get(j)
            if v is None: continue                    # UNKNOWN：没去过就是不知道
            if v > bestv: best, bestv = j, v
        # 只读诊断：用**交换前**的记忆再算一次目标，只统计，不参与规则。
        pm = st['pre_mem'].get(bid, ({}, {}))[0]
        pre_best, pre_v = None, here * MIG_GAIN_M // MILLE
        for j in neighbors(b['cell']):
            v = st['stock'][j] if 'omniscient' in P else pm.get(j)
            if v is None: continue
            if v > pre_v: pre_best, pre_v = j, v
        if pre_best != best:
            st['share_decision_changed'] += 1
        if 'sharediag' in P and st['share_decision_changed'] % 2 == 1:
            continue                      # 注入：让只读诊断回灌规则
        if best is None: continue
        truth_better = st['stock'][best] > st['stock'][b['cell']]
        loss = b['store'] * MOVE_LOSS_M // MILLE
        b['store'] -= loss; st['out_move'] += loss
        # --- EXP-03 唯一新增：迁移死亡代价 ---
        # 相位：本 tick 消费（相位 3）之后。**不回溯修改已结算的当年消费。**
        # 出发人数 = 迁移前的 size；死亡按累加器确定性取整；幸存者带着储存一起走。
        # 储存不因死亡而减少：当前账本只记录可食用资源，不包含人体能量；
        # 人口死亡不自动扣减粮食库存，因此能量守恒式不变。
        mm = st['move_mort_m']
        if 'mortstrength' in P:                # 注入：只改 step 内实际用的强度，
            mm = min(mm + 1, MOVE_MORT_M_MAX)  # move_mortality() 的单元测试照样通过
        if mm > 0:
            depart = b['size']
            if 'mortseq' in P:                 # 注入：全局累加器，按遍历序推进
                dead, _, st['macc_global'] = move_mortality(depart, st['macc_global'], mm)
                dead = min(dead, depart)       # 注入版才可能需要兜底
                b['size'] = depart - dead
            else:                              # 健康版：每群体独立累加器
                dead, b['size'], b['macc'] = move_mortality(depart, b['macc'], mm)
            st['mig_deaths_cum'] += dead
        st['stale_sum'] += t - b['memt'].get(best, t)
        b['cell'] = best
        b['mem'][best] = st['stock'][best]; b['memt'][best] = t
        st['mig_total'] += 1
        if not truth_better: st['mig_regret'] += 1
    # --- 相位 7a extinct：同时移除，先于任何分裂 ---
    for bid in [x for x in order if x in st['bands'] and st['bands'][x]['size'] == 0]:
        st['out_lost'] += st['bands'][bid]['store']
        # 它自己的援助记忆随之丢失，数量记账，好让记忆账仍然闭合（见文件头假设 3）。
        gone = st['bands'][bid]['amem']
        st['amem_dropped_kcal'] += sum(v[0] for v in gone.values())
        st['amem_entries_dropped'] += len(gone)
        del st['bands'][bid]
        st['log'].append((t, 'extinct', bid))

    # --- 相位 7b propose：所有群体基于同一份占用快照独立提出申请 ---
    occupied = {b['cell'] for b in st['bands'].values()}
    proposals = []                      # [(目标格, 申请者)]
    for bid in [x for x in order if x in st['bands']]:
        b = st['bands'][bid]
        if b['size'] < SPLIT_SIZE: continue
        if suppress_split_in and region(b['cell']) == suppress_split_in: continue
        free = [j for j in neighbors(b['cell']) if j not in occupied]
        if not free: continue
        proposals.append((free[rng(seed, S_SPLIT, t, bid, 0) % len(free)], bid))

    st['prop_total'] += len(proposals)
    st['prop_conflict'] += len(proposals) - len({j for j, _ in proposals})
    # --- 相位 7c resolve：同一空位的冲突按 band_id 升序裁决，落败者本 tick 不分裂 ---
    if 'seqsplit' in P:                 # 注入：回到顺序解决（先到先得）
        winners, occ2 = [], set(occupied)
        for j, bid in proposals:
            if j in occ2: continue
            occ2.add(j); winners.append((j, bid))
    else:
        by_target = {}
        for j, bid in proposals: by_target.setdefault(j, []).append(bid)
        winners = sorted((j, min(bids)) for j, bids in by_target.items())

    # --- 相位 7d commit：一次性提交 ---
    for j, bid in winners:
        b = st['bands'][bid]
        half = b['size'] // 2; hs = b['store'] // 2
        hm = b['macc'] // 2                   # 累加器余数显式分配，父 + 子 = 原值
        if 'counter' in P:
            st['next_ctr'] += 1; nid = 0xB000000 + st['next_ctr']   # 全局自增
        else:
            nid = eid_of(bid, t, 0)
        if nid in st['bands']: continue
        b['size'] -= half; b['store'] -= hs; b['macc'] -= hm
        st['bands'][nid] = {'cell': j, 'size': half, 'store': hs,
                            'bacc': 0, 'dacc': 0, 'macc': hm,
                            'mem': {j: st['stock'][j]}, 'memt': {j: t},
                            # 子群体**不继承**援助记忆：它没有实际接受过任何援助。
                            # 父群体的记忆原样保留（见文件头假设 2）。
                            'amem': {}}
        st['log'].append((t, 'split', bid, nid))
    st['tick'] += 1

# 物质与行动的哈希：**不含记忆、信息账与诊断计数**。
# 全知对照臂检查的就是它 —— 记忆内容会随交换机制变化，那是预期之内，不是错误。
# stale_sum 依赖 memt，属于信息指标，因此也不在这里。
MATERIAL_LEDGER_FIELDS = ('inflow', 'out_eat', 'out_spoil', 'out_move', 'out_lost',
                          'mig_total', 'mig_regret', 'next_ctr', 'aid_m', 'recip_m',
                          'recip_kcal', 'recip_transfers',
                          'aid_events', 'aid_transfers', 'aid_kcal',
                          'prop_total', 'prop_conflict',
                          'clim_nominal', 'clim_planned', 'clim_credited', 'clim_capped',
                          'clim_ctr', 'deficit_cum', 'sigma_m', 'move_mort_m',
                          'mig_deaths_cum', 'births_cum', 'deaths_demo_cum',
                          'need_cum', 'personyear_cum', 'macc_global')

def material_hash(st) -> str:
    """行动与物质演化的摘要：tick + 每格资源 + 每个群体的物质字段 + 物质账。"""
    h = hashlib.blake2b(digest_size=16)
    h.update(f"tick={st['tick']};".encode())
    for i in sorted(st['stock']):
        h.update(f"{i}:{st['stock'][i]}:{st['cap'][i]}:{st['regen'][i]};".encode())
    for bid in sorted(st['bands']):
        d = st['bands'][bid]
        h.update((':'.join([str(bid)] + [str(d[f]) for f in BAND_FIELDS]) + ';').encode())
    for f in MATERIAL_LEDGER_FIELDS:
        h.update(f"{f}={st[f]};".encode())
    return h.hexdigest()


def aid_ledger_error(st) -> int:
    """援助账恒等：逐笔记录的总量 + 预置的历史量 == 账上的援助总量。必须恒为 0。
    （`aid_preset_kcal` 只在定向场景里非零：那里的"过去援助"是构造出来的前提。）
    （逐笔"供给方减少 == 接收方增加"由 step 内的同一个 amt 保证，
      再由能量守恒兜底：凭空生粮会让守恒误差非 0。）"""
    return (sum(rec[4] for rec in st['aid_log'])
            + st.get('aid_preset_kcal', 0) - st['aid_kcal'])


def share_ledger_error(st) -> int:
    """信息账恒等：收到 = 采纳 + 拒绝。必须恒为 0。"""
    return st['share_received'] - (st['share_adopted'] + st['share_rejected'])


def move_mortality(size: int, macc: int, mm: int):
    """迁移死亡的唯一实现。返回 (死亡数, 幸存数, 新累加器)。

    累加器口径：macc += 本次出发人数 × mm；取整出死亡数；余数留到下次。
    **按每次迁移前的实际人数累计**，不是 N × 初始人数 × 强度。

    这是一个**确定性取整近似**，不是个体随机死亡模型：它不产生方差、不产生
    尾部事件，只保证长期比例正确。用累加器而不是 size×mm//1000 直接取整，
    是为了消除量化死区——后者在 mm=20 时对小于 50 人的群体损失恒为 0，
    而本世界群体典型规模就是 20–30 人。
    """
    macc += size * mm
    dead = macc // MILLE
    macc -= dead * MILLE
    return dead, size - dead, macc


def population_identity_error(st) -> int:
    """期末人口 == 期初人口 + 出生 − 原规则死亡 − 迁移死亡。
    迁移与分裂本身不增减全球人口，所以这个差必须恒为 0。"""
    pop = sum(b['size'] for b in st['bands'].values())
    return pop - (st['pop_start'] + st['births_cum']
                  - st['deaths_demo_cum'] - st['mig_deaths_cum'])

def farm_labour_error(st) -> int:
    """劳动预算恒等：每个群体的**耕作刻度 + 采集刻度 == 人数 × 1000**。

    用的是本 tick 冻结下来的痕迹（人口变化之前的 N）。不为 0 就是劳动被凭空多算或漏算。
    """
    bad = 0
    for _bid, (n, fe, foe) in (st.get('farm_effort_trace') or {}).items():
        bad += (fe + foe) - n * MILLE
    return bad


def field_ledger_error(st) -> int:
    """耕地账：**期末各格耕地之和 == 累计开垦 − 累计退化**（开局全为 0）。"""
    return sum(st['field_m'].values()) - (st['field_built_cum'] - st['field_decay_cum'])


def farm_yield_error(st) -> int:
    """产出账：**潜在产出 == 实际采收 + 未采收**。未采收既不转给别人也不留到明年。"""
    return st['farm_potential_cum'] - (st['farm_harvest_cum'] + st['farm_uncollected_cum'])


def inflow_source_error(st) -> int:
    """入账来源分项：**inflow == 资源再生入账 + 农业实际采收**。

    野外采集是库存**内部转移**（格 -> 群体），不重复计入 inflow；农业采收才是新进来的能量。
    """
    return st['inflow'] - (st['clim_credited'] + st['farm_harvest_cum'])


def conservation_error(st) -> int:
    lhs = sum(st['stock'].values()) + sum(b['store'] for b in st['bands'].values())
    rhs = (st['start_stock'] + st['start_store'] + st['inflow']
           - st['out_eat'] - st['out_spoil'] - st['out_move'] - st['out_lost'])
    return lhs - rhs

import copy
def run(seed, years, poison="", suppress=None, snap_at=None, sigma_m=0, move_mort_m=0,
        share_m=0, aid_m=0, recip_m=0, farm_m=0):
    st = make_world(seed, poison, sigma_m, move_mort_m, share_m, aid_m, recip_m,
                    farm_m); snap = None
    for _ in range(years):
        if snap_at is not None and st['tick'] == snap_at:
            snap = copy.deepcopy(st)
        step(st, suppress_split_in=suppress)
    return st, snap

def resume(snap, years, suppress=None):
    st = copy.deepcopy(snap)
    for _ in range(years):
        step(st, suppress_split_in=suppress)
    return st


# ---------- 定向场景：构造"优先回助" ----------
# 自然运行里"曾受助者后来有余粮、且两个对象同时求助、且供给不足"这三件事凑齐很少见，
# 所以必须构造。构造时把该格的容量与再生设为 0，当年采集恒为 0，avail 精确等于给定储粮。
def make_recip_scenario(spec, memory, aid_m: int = 1000, recip_m: int = 1000,
                        seed: int = 0, tick: int = 7):
    """spec = [(人口, 储粮), ...]，全部放同一格；
       memory = {接受者下标: {援助者下标: 记忆中的累计 kcal}}（写进 band['amem']）。
    返回 (st, 格号, [band_id...])。
    """
    st = make_world(seed, "", 0, 0, 0, aid_m, recip_m)
    P = next(i for i in cells() if passable(i))
    st['cap'][P] = 0; st['regen'][P] = 0; st['stock'][P] = 0
    ids = sorted(eid_of(0xEC10, 0, k) for k in range(len(spec)))
    st['bands'] = {}
    for bid, (size, store) in zip(ids, spec):
        st['bands'][bid] = {'cell': P, 'size': size, 'store': store,
                            'bacc': 0, 'dacc': 0, 'macc': 0,
                            'mem': {P: 0}, 'memt': {P: 0}, 'amem': {}}
    for who, rel in memory.items():
        for donor_idx, cum in rel.items():
            st['bands'][ids[who]]['amem'][ids[donor_idx]] = [cum, 1]
    # 记忆是构造出来的前提，不是本次运行累加出来的：把它计入 aid_kcal，记忆账才闭合
    st['aid_preset_kcal'] = sum(v[0] for b in st['bands'].values()
                                for v in b['amem'].values())
    st['aid_kcal'] = st['aid_preset_kcal']
    st['start_stock'] = sum(st['stock'].values())
    st['start_store'] = sum(b['store'] for b in st['bands'].values())
    st['pop_start'] = sum(b['size'] for b in st['bands'].values())
    st['tick'] = tick
    return st, P, ids


# ---------- 定向场景：构造同格食物援助 ----------
# 自然运行里"同格既有余粮者又有缺粮者"只在 6–10% 的 tick 上出现（见 probes/），
# 所以结算规则、边界与整数余量必须由构造场景钉死，不能挂在长跑上。
def make_aid_scenario(spec, aid_m: int = 1000, seed: int = 0, tick: int = 5):
    """spec = [(人口, 储粮), ...]，全部放在同一格。

    把该格的容量与再生量设为 0，于是当年采集恒为 0，
    可用粮食 avail 就精确等于给定的储粮，需求 need = 人口 × NEED_PC —— 前提完全可控。
    返回 (st, 格号, [band_id...])。

    **期望结果由测试自己独立重算**（见 run_tests.py 的 expected_aid_ref）——
    参考实现不能和被测实现住在同一个文件里，否则改一处会同时改掉两边，
    等于没有检验（EXP-03 的 D11 空断言就是这么放过错误的）。
    """
    st = make_world(seed, "", 0, 0, 0, aid_m)
    P = next(i for i in cells() if passable(i))
    st['cap'][P] = 0; st['regen'][P] = 0; st['stock'][P] = 0
    ids = sorted(eid_of(0xA1D0, 0, k) for k in range(len(spec)))
    st['bands'] = {}
    for bid, (size, store) in zip(ids, spec):
        st['bands'][bid] = {'cell': P, 'size': size, 'store': store,
                            'bacc': 0, 'dacc': 0, 'macc': 0,
                            'mem': {P: 0}, 'memt': {P: 0}}
    st['start_stock'] = sum(st['stock'].values())
    st['start_store'] = sum(b['store'] for b in st['bands'].values())
    st['pop_start'] = sum(b['size'] for b in st['bands'].values())
    st['tick'] = tick
    return st, P, ids


# ---------- 定向场景：构造一次同格信息交换 ----------
# 长跑里同格交换确实会发生（seed 4242 的 120 年里有 70 组），但要精确核对合并规则、
# 溯源、时戳与注入检出，必须有一个把前提全部钉死的场景。
def make_share_scenario(seed: int = 0, share_m: int = 1000, tick: int = 11):
    """三个群体同格，记忆互有缺口：
         A 知道 nb[1]（时戳 3），C 知道 nb[0]（时戳 7），B 什么都不知道。
       期望（健康版）：A 从 C 拿 nb[0]；B 从 A 拿 nb[1]、从 C 拿 nb[0]；C 从 A 拿 nb[1]。
       顺序链式注入（shareseq）会让 B 的 nb[0] 记成来自 A —— 而 A 在交换前并没有它。
    返回 (st, 所在格, [A,B,C], 邻格列表)。
    """
    st = make_world(seed, "", 0, 0, share_m)
    P = next(i for i in cells() if passable(i) and len(neighbors(i)) >= 3)
    nb = neighbors(P)
    ids = sorted(eid_of(0x5A4E, 0, k) for k in range(3))
    st['bands'] = {}
    for bid in ids:
        st['bands'][bid] = {'cell': P, 'size': 20, 'store': 5 * NEED_PC,
                            'bacc': 0, 'dacc': 0, 'macc': 0,
                            'mem': {P: st['stock'][P]}, 'memt': {P: 0}}
    A, B, C = ids
    st['bands'][C]['mem'][nb[0]] = 12_345_678
    st['bands'][C]['memt'][nb[0]] = 7
    st['bands'][A]['mem'][nb[1]] = 87_654_321
    st['bands'][A]['memt'][nb[1]] = 3
    st['start_store'] = sum(b['store'] for b in st['bands'].values())
    st['pop_start'] = sum(b['size'] for b in st['bands'].values())
    st['tick'] = tick
    return st, P, ids, nb


def make_share_decision_scenario(seed: int = 0):
    """构造一个“交换确实改变了迁移目标”的场景。

    要点：侦察（相位 6a）在交换之前，它每年会给 X 补一个**随机邻格**的记忆。
    所以必须挑一个 tick，使 X 当年侦察到的**不是**那个更好的邻格 ——
    侦察的抽签是 counter-based 的，可以直接算出来，不靠碰运气。

    返回 (st, X, Y, 更好的邻格, 平庸的邻格) 或 None（前提凑不齐，记未覆盖）。
    """
    base = make_world(seed, "", 0, 0, 1000)
    ids = sorted(eid_of(0xD1CE, 0, k) for k in range(2))
    X, Y = ids
    for i in cells():
        if not passable(i) or len(neighbors(i)) < 3:
            continue
        nb = neighbors(i)
        ranked = sorted(nb, key=lambda j: base['stock'][j])
        good, plain = ranked[-1], ranked[0]
        if base['stock'][good] <= base['stock'][plain]:
            continue
        for tick in range(1, 60):
            scouted = nb[rng(seed, S_SCOUT, tick, X, 0) % len(nb)]
            if scouted in (good,):
                continue                       # 当年自己就会侦察到好邻格，交换就不是原因了
            if base['stock'][scouted] >= base['stock'][good]:
                continue
            st = make_world(seed, "", 0, 0, 1000)
            st['bands'] = {}
            for bid in ids:
                st['bands'][bid] = {'cell': i, 'size': 20, 'store': 0,
                                    'bacc': 0, 'dacc': 0, 'macc': 0,
                                    'mem': {i: 0}, 'memt': {i: 0}}
            st['bands'][X]['mem'][plain] = st['stock'][plain]   # X 只记得平庸的那个
            st['bands'][X]['memt'][plain] = 1
            st['bands'][Y]['mem'][good] = st['stock'][good]     # Y 记得更好的那个
            st['bands'][Y]['memt'][good] = 9
            st['stock'][i] = 0                                  # 饿着才会打听邻格
            st['start_stock'] = sum(st['stock'].values())
            st['start_store'] = sum(b['store'] for b in st['bands'].values())
            st['pop_start'] = sum(b['size'] for b in st['bands'].values())
            st['tick'] = tick
            return st, X, Y, good, plain
    return None


# ---------- 定向场景：构造一次空位冲突 ----------
# 长跑（7 种子 × 300 年）里分裂申请 175 次、撞车 0 次，冲突解决路径从不被执行。
# 所以它必须由一个构造出来的场景来覆盖，否则 §7c 是一段没被任何测试碰过的代码。
def make_conflict_world(seed: int = 0):
    """造一个局面：两个够大的群体 P、Q 各自唯一的空邻格都是 X。

    返回 (st, X, pid, qid)。P 与 Q 的其余邻格用小群体占满（size 远低于
    SPLIT_SIZE，不会自己提出申请），因此两者本 tick 必然同时申请 X。
    """
    st = make_world(seed, sigma_m=0)
    st['bands'].clear()
    # 找一个 A 区的格 X，它至少有两个可通行邻居
    cand = [i for i in cells() if passable(i) and region(i) == 'A'
            and len(neighbors(i)) >= 2]
    X = sorted(cand)[0]
    P, Q = sorted(neighbors(X))[:2]

    def add(cell, size, tag):
        bid = eid_of(0xC047, 0, tag)
        st['bands'][bid] = {'cell': cell, 'size': size,
                            'store': size * NEED_PC,          # 一年口粮，吃得饱
                            'bacc': 0, 'dacc': 0, 'macc': 0,
                            'mem': {cell: st['stock'][cell]}, 'memt': {cell: 0}}
        return bid

    pid = add(P, 60, 1)
    qid = add(Q, 60, 2)
    # 占满 P、Q 的其余邻格，使它们唯一的空位是 X
    tag = 10
    for host in (P, Q):
        for j in neighbors(host):
            if j == X: continue
            if any(b['cell'] == j for b in st['bands'].values()): continue
            add(j, 5, tag); tag += 1
    st['start_store'] = sum(b['store'] for b in st['bands'].values())
    st['pop_start'] = sum(b['size'] for b in st['bands'].values())
    return st, X, pid, qid


def who_took(st, X):
    """X 格上的群体 id；没有则 None。"""
    for bid in sorted(st['bands']):
        if st['bands'][bid]['cell'] == X:
            return bid
    return None


# ---------- 定向场景：信息边界 ----------
def make_info_scenario(seed: int = 0, sigma_m: int = 0, move_mort_m: int = 0):
    """一个饿着的群体，记忆里只有自己格与一个已知邻格。

    **场景前提**（必须由构造保证，不能事后当失败）：
      P1 群体确实会考虑迁移（E < 1.000）
      P2 存在一个已知邻格，其记忆值高于 1.250×自己格，使基准决策 = 搬去已知格
      P3 侦察目标被填满后能压过已知格，使正对照真的能翻转决策
      P4 至少还有一个既不在记忆里、本 tick 也不会被侦察的邻格

    返回 (st, bid, scout_target, known, unobserved)；找不到满足前提的位置时返回 None。
    """
    st = make_world(seed, sigma_m=sigma_m, move_mort_m=move_mort_m)
    st['bands'].clear()
    bid = eid_of(0x1F0, 0, 1)
    for P in sorted(i for i in cells() if passable(i) and len(neighbors(i)) >= 3):
        nb = neighbors(P)
        scout = nb[rng(seed, S_SCOUT, 0, bid, 0) % len(nb)]
        others = [j for j in nb if j != scout]
        if len(others) < 2:            # P4：要留一个未观察格
            continue
        # P1：本格清零后，单年再生的可采集量必须仍喂不饱 20 人，否则 E≥1、不进迁移分支
        SIZE = 20
        harvest_est = st['regen'][P] * SIZE // (SIZE + K_HALF)
        if harvest_est >= SIZE * NEED_PC:
            continue
        known = others[0]
        # 自己格清零 => 本 tick 迁移基准恰为 regen[P] × 1.250
        base_thr = st['regen'][P] * MIG_GAIN_M // MILLE
        hi = st['cap'][scout]          # 正对照能给出的最大值
        lo = base_thr
        known_val = (lo + hi) // 2
        if not (lo < known_val < hi and known_val <= st['cap'][known]):
            continue                   # P2/P3 不能同时满足，换一个 P
        st['stock'][P] = 0
        st['stock'][known] = known_val
        st['stock'][scout] = st['cap'][scout] // 10
        st['bands'][bid] = {'cell': P, 'size': 20, 'store': 0,
                            'bacc': 0, 'dacc': 0, 'macc': 0,
                            'mem': {P: 0, known: known_val},
                            'memt': {P: 0, known: 0}}
        st['start_store'] = 0
        st['start_stock'] = sum(st['stock'].values())
        st['pop_start'] = sum(b['size'] for b in st['bands'].values())
        return st, bid, scout, known, others[1:]
    return None


def decide_once(st, bid):
    """跑一个 tick，返回该群体最终所在格。"""
    import copy
    s2 = copy.deepcopy(st)
    step(s2)
    b = s2['bands'].get(bid)
    return b['cell'] if b else None


# ---------- 定向场景：迁移死亡 ----------
def _hungry_mover(st, P, size, store, tag):
    """在格 P 放一个必定迁移的群体：本格清零 => E<1；记忆里有一个富邻格。
    返回 bid；若找不到满足条件的已知邻格返回 None。"""
    nb = neighbors(P)
    base_thr = st['regen'][P] * MIG_GAIN_M // MILLE
    known = None
    for j in nb:
        if st['cap'][j] > base_thr:
            known = j; break
    if known is None:
        return None
    st['stock'][P] = 0
    st['stock'][known] = st['cap'][known]
    bid = eid_of(0x3E0, 0, tag)
    st['bands'][bid] = {'cell': P, 'size': size, 'store': store,
                        'bacc': 0, 'dacc': 0, 'macc': 0,
                        'mem': {P: 0, known: st['cap'][known]},
                        'memt': {P: 0, known: 0}}
    return bid


def make_two_movers(seed: int, move_mort_m: int, sizes=(20, 30), stores=(0, 0)):
    """两个互不相邻的群体，同一 tick 都会迁移。用于竞争场景与独立累加器检验。
    找不到合适位置时返回 None。"""
    st = make_world(seed, move_mort_m=move_mort_m)
    st['bands'].clear()
    cand = [i for i in cells() if passable(i) and region(i) == 'A' and len(neighbors(i)) >= 2]
    for a in sorted(cand):
        for b in sorted(cand):
            if b <= a or b in neighbors(a) or a in neighbors(b):
                continue
            if set(neighbors(a)) & set(neighbors(b)):
                continue                      # 邻格不重叠，免得抢同一个格
            trial = copy.deepcopy(st)
            i1 = _hungry_mover(trial, a, sizes[0], stores[0], 1)
            i2 = _hungry_mover(trial, b, sizes[1], stores[1], 2)
            if i1 is None or i2 is None:
                continue
            trial['start_stock'] = sum(trial['stock'].values())
            trial['start_store'] = sum(x['store'] for x in trial['bands'].values())
            trial['pop_start'] = sum(x['size'] for x in trial['bands'].values())
            return trial, i1, i2, a, b
    return None


def make_split_scenario(seed: int = 0, macc0: int = 777):
    """一个够大、有指定累加器余数、且有空邻格的群体，本 tick 会分裂。
    用于检验 macc 在分裂时的分配与守恒。找不到位置返回 None。"""
    st = make_world(seed)
    st['bands'].clear()
    for P in sorted(i for i in cells() if passable(i) and len(neighbors(i)) >= 2):
        bid = eid_of(0x5A1, 0, 1)
        st['bands'][bid] = {'cell': P, 'size': 60, 'store': 60 * NEED_PC,
                            'bacc': 0, 'dacc': 0, 'macc': macc0,
                            'mem': {P: st['stock'][P]}, 'memt': {P: 0}}
        st['start_store'] = 60 * NEED_PC
        st['start_stock'] = sum(st['stock'].values())
        st['pop_start'] = 60
        return st, bid
    return None


# ---------- 端到端定向场景：出发人数 / 原余数 / 配置强度全部确定 ----------
def make_exact_move_scenario(seed: int, mm: int, macc0: int, size: int = 20):
    """构造一个本 tick 必定迁移、且迁移前人数精确等于 size 的局面。

    做法：把食物比钉在 E_m = 999 —— 刚好低于迁移门槛 1000，同时落在
    b(E)、d(E) 都取不出整人的区间，于是人口相位对 size 零净变动，
    迁移时的出发人数精确等于 size。

    这样死亡数、幸存数、余数、人口账增量全部可以事先算出并精确核对，
    而不是只断言"余数 < 1000"那种恒真式。

    返回 (st, bid, 期望值 dict)；构造不成立时返回 None（记未覆盖，不得默认通过）。
    """
    st = make_world(seed, sigma_m=0, move_mort_m=mm)
    st['bands'].clear()
    need = size * NEED_PC
    for P in sorted(i for i in cells() if passable(i) and len(neighbors(i)) >= 2):
        regen = st['regen'][P]
        if regen == 0 or regen >= st['cap'][P]:
            continue
        harvest = regen * size // (size + K_HALF)
        store0 = need - 1 - harvest            # => avail = need-1 => E_m = 999
        if store0 < 0:
            continue
        # 迁移基准：自己格采完后的存量 × 1.250；已知邻格必须压过它
        base_thr = (regen - harvest) * MIG_GAIN_M // MILLE
        known = next((j for j in neighbors(P) if st['cap'][j] > base_thr), None)
        if known is None:
            continue
        # 死亡冲击不能触发，否则人口相位会多杀人
        bid = eid_of(0xE2E, 0, 1)
        if rng(seed, S_SHOCK, 0, bid, 0) % MILLE < SHOCK_P_M:
            continue
        st['stock'][P] = 0
        st['stock'][known] = st['cap'][known]
        st['bands'][bid] = {'cell': P, 'size': size, 'store': store0,
                            'bacc': 0, 'dacc': 0, 'macc': macc0,
                            'mem': {P: 0, known: st['cap'][known]},
                            'memt': {P: 0, known: 0}}
        st['start_stock'] = sum(st['stock'].values())
        st['start_store'] = store0
        st['pop_start'] = size
        total = macc0 + size * mm
        exp = {'depart': size, 'dead': total // MILLE,
               'survive': size - total // MILLE, 'macc': total % MILLE,
               'cell': known, 'E_m': MILLE - 1}
        return st, bid, exp
    return None
