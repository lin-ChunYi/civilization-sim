"""
EXP-02 —— 资源再生波动实验。

由 exp01/verify.py（冻结基线 commit 20da486）复制并只加一个机制：
每格再生量的年际波动。**这不是气候模型**，是一个受控的资源波动实验，
用来回答"信息边界在什么条件下开始有后果"。

exp01/ 只读、不改。SIGMA_M=0 时本文件必须逐位复现基线状态——那条退化检验
同时也是"这份复制没有偷偷漂移"的回归检验。
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

def make_world(seed: int, poison: str = "", sigma_m: int = 0):
    split_poisons(poison)          # 未登记的注入标志立刻报错，不许静默通过
    # 先查类型再查范围。顺序不能反：浮点的 sigma_m 会让 stock 整个变成 float，
    # 而守恒误差会是 0.0（浮点相等），守恒检验抓不到它——类型检查不能用守恒检验代替。
    # bool 是 int 的子类，必须单独排除，否则 True 会被静默当成 sigma_m=1。
    if isinstance(sigma_m, bool) or not isinstance(sigma_m, int):
        raise TypeError(f"SIGMA_M 必须是严格整数（不接受 bool），"
                        f"收到 {sigma_m!r} ({type(sigma_m).__name__})")
    if not (SIGMA_M_MIN <= sigma_m <= SIGMA_M_MAX):
        raise ValueError(f"SIGMA_M={sigma_m} 越界，合法范围 [{SIGMA_M_MIN}, {SIGMA_M_MAX}]")
    st = {'tick': 0, 'seed': seed, 'poison': poison, 'sigma_m': sigma_m,
          'stock': {}, 'cap': {}, 'regen': {}, 'bands': {},
          'inflow': 0, 'out_eat': 0, 'out_spoil': 0, 'out_move': 0, 'out_lost': 0,
          'log': [], 'mig_total': 0, 'mig_regret': 0, 'next_ctr': 0, 'stale_sum': 0,
          'prop_total': 0, 'prop_conflict': 0,
          'clim_nominal': 0, 'clim_planned': 0, 'clim_credited': 0, 'clim_capped': 0,
          'clim_ctr': 0, 'deficit_cum': 0, 'trace_clim': None}
    for i in cells():
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
                            'bacc': 0, 'dacc': 0, 'mem': {c: st['stock'][c]}, 'memt': {c: 0}}
    st['start_store'] = sum(b['store'] for b in st['bands'].values())
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
                               'climseq'})            # 波动按调用序而非坐标寻址（EXP-02 新增）

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
               'W', 'H')

def params_fingerprint(sigma_m: int = None) -> str:
    """全部规则参数 + 地图形状 + SIGMA_M 的指纹。改任何一个，运行身份就变。"""
    g = globals()
    h = hashlib.blake2b(digest_size=8)
    h.update(b"EXP02;")
    if sigma_m is not None:
        h.update(f"SIGMA_M={sigma_m};".encode())
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
    h.update(("semantic=" + ",".join(sorted(sem)) + ";").encode())
    h.update(f"params={params_fingerprint(st['sigma_m'])};".encode())
    return h.hexdigest()

def full_digest(st) -> str:
    """对外比较两次运行时应当用的东西：身份 + 状态。"""
    return f"{run_id(st)}/{state_hash(st)}"


BAND_FIELDS = ('cell', 'size', 'store', 'bacc', 'dacc')

def _band_blob(bid, d) -> bytes:
    """一个群体的完整可演化状态。凡是会影响后续演化的字段都必须在这里，
    包括 mem / memt —— 少写一个字段，确定性检验就会漏掉整整一类 bug。"""
    parts = [str(bid)] + [str(d[f]) for f in BAND_FIELDS]
    parts.append('mem{' + ','.join(f"{c}={d['mem'][c]}" for c in sorted(d['mem'])) + '}')
    parts.append('memt{' + ','.join(f"{c}={d['memt'][c]}" for c in sorted(d['memt'])) + '}')
    return (':'.join(parts) + ';').encode()

LEDGER_FIELDS = ('inflow', 'out_eat', 'out_spoil', 'out_move', 'out_lost',
                 'mig_total', 'mig_regret', 'stale_sum', 'next_ctr',
                 'prop_total', 'prop_conflict',
                 # EXP-02 新增。资源账：名义 / 计划 / 实际入账 / 被容量挡住
                 'clim_nominal', 'clim_planned', 'clim_credited', 'clim_capped',
                 'clim_ctr', 'deficit_cum', 'sigma_m')

# 基线（EXP-01）自己的字段集合。A1 退化检验用基线自己的哈希函数判定，
# 不用 EXP-02 的——否则就是把基线改成能通过的样子。
BASELINE_LEDGER_FIELDS = ('inflow', 'out_eat', 'out_spoil', 'out_move', 'out_lost',
                          'mig_total', 'mig_regret', 'stale_sum', 'next_ctr',
                          'prop_total', 'prop_conflict')

def state_hash(st) -> str:
    """全状态哈希：tick + 每格 stock/cap/regen + 每个群体的完整状态 + 全部账本计数。"""
    h = hashlib.blake2b(digest_size=16)
    h.update(f"tick={st['tick']};".encode())
    for i in sorted(st['stock']):
        h.update(f"{i}:{st['stock'][i]}:{st['cap'][i]}:{st['regen'][i]};".encode())
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
    claim = {}; by_cell = {}
    for bid in order:
        b = st['bands'][bid]; c = b['cell']
        need = b['size'] * NEED_PC
        room = max(0, b['size'] * NEED_PC * STORE_YEARS_M // MILLE - b['store'])
        s0 = st['stock'][c]
        if 'float' in P:
            got = int(s0 * (b['size'] / (b['size'] + K_HALF)))   # 浮点污染
        else:
            got = s0 * b['size'] // (b['size'] + K_HALF)
        claim[bid] = min(got, need + room, s0)
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
    # --- 相位 3 consume ---
    for bid in order:
        b = st['bands'][bid]
        need = b['size'] * NEED_PC
        avail = harvest[bid] + b['store']
        eat = min(need, avail)
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
        b['size'] = max(0, b['size'] + births - deaths)
    # --- 相位 6a scout：每年侦察一个随机邻格，记下当年真值 ---
    for bid in order:
        b = st['bands'][bid]
        if b['size'] == 0: continue
        nb = neighbors(b['cell'])
        if not nb: continue
        j = nb[rng(seed, S_SCOUT, t, bid, 0) % len(nb)]
        b['mem'][j] = st['stock'][j]
        b['memt'][j] = t
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
        if best is None: continue
        truth_better = st['stock'][best] > st['stock'][b['cell']]
        loss = b['store'] * MOVE_LOSS_M // MILLE
        b['store'] -= loss; st['out_move'] += loss
        st['stale_sum'] += t - b['memt'].get(best, t)
        b['cell'] = best
        b['mem'][best] = st['stock'][best]; b['memt'][best] = t
        st['mig_total'] += 1
        if not truth_better: st['mig_regret'] += 1
    # --- 相位 7a extinct：同时移除，先于任何分裂 ---
    for bid in [x for x in order if x in st['bands'] and st['bands'][x]['size'] == 0]:
        st['out_lost'] += st['bands'][bid]['store']
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
        if 'counter' in P:
            st['next_ctr'] += 1; nid = 0xB000000 + st['next_ctr']   # 全局自增
        else:
            nid = eid_of(bid, t, 0)
        if nid in st['bands']: continue
        b['size'] -= half; b['store'] -= hs
        st['bands'][nid] = {'cell': j, 'size': half, 'store': hs,
                            'bacc': 0, 'dacc': 0, 'mem': {j: st['stock'][j]}, 'memt': {j: t}}
        st['log'].append((t, 'split', bid, nid))
    st['tick'] += 1

def conservation_error(st) -> int:
    lhs = sum(st['stock'].values()) + sum(b['store'] for b in st['bands'].values())
    rhs = (st['start_stock'] + st['start_store'] + st['inflow']
           - st['out_eat'] - st['out_spoil'] - st['out_move'] - st['out_lost'])
    return lhs - rhs

import copy
def run(seed, years, poison="", suppress=None, snap_at=None, sigma_m=0):
    st = make_world(seed, poison, sigma_m); snap = None
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
                            'bacc': 0, 'dacc': 0,
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
    return st, X, pid, qid


def who_took(st, X):
    """X 格上的群体 id；没有则 None。"""
    for bid in sorted(st['bands']):
        if st['bands'][bid]['cell'] == X:
            return bid
    return None


# ---------- 定向场景：信息边界 ----------
def make_info_scenario(seed: int = 0, sigma_m: int = 0):
    """一个饿着的群体，记忆里只有自己格与一个已知邻格。

    **场景前提**（必须由构造保证，不能事后当失败）：
      P1 群体确实会考虑迁移（E < 1.000）
      P2 存在一个已知邻格，其记忆值高于 1.250×自己格，使基准决策 = 搬去已知格
      P3 侦察目标被填满后能压过已知格，使正对照真的能翻转决策
      P4 至少还有一个既不在记忆里、本 tick 也不会被侦察的邻格

    返回 (st, bid, scout_target, known, unobserved)；找不到满足前提的位置时返回 None。
    """
    st = make_world(seed, sigma_m=sigma_m)
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
                            'bacc': 0, 'dacc': 0,
                            'mem': {P: 0, known: known_val},
                            'memt': {P: 0, known: 0}}
        st['start_store'] = 0
        st['start_stock'] = sum(st['stock'].values())
        return st, bid, scout, known, others[1:]
    return None


def decide_once(st, bid):
    """跑一个 tick，返回该群体最终所在格。"""
    import copy
    s2 = copy.deepcopy(st)
    step(s2)
    b = s2['bands'].get(bid)
    return b['cell'] if b else None
