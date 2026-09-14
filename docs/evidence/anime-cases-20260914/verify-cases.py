#!/usr/bin/env python3
"""逐条复核 docs/ANIME-REAL-CASES.md 里写下的每一个数字。

**在任何一份新检出的仓库里都能跑**，不依赖产生这份清单的那台机器上的临时目录。
数据有两个来源，都在仓库里：

1. 本目录里**已提交的真实 API 响应** —— `run{A,B,C,D}-meta.json`、
   `runA-year-*.json`、`runB/C/D-year-*.json`、`bandA-*.json`、`relationsA-y295.json`。
2. 用仓库里的引擎（`exp06/verify6.py` / `exp07/verify7.py`）与观察层适配器
   （`observer/adapter.py`）**按 `real-cases.json` 里记着的参数就地重算整段历史**。
   参数从证据文件里读，不写死在脚本里；重算只读引擎，不启服务、不落盘、不写任何目录。

脚本先证明「就地重算 == 已提交的 API 响应」（逐字段比，见"响应可重放"一组），
再用重算出来的整段历史去查那些**需要全年数据**的断言：逐年累计、事件总数与去重、
弃耕轨迹、301 年逐年对照。这样既不用把上百 MB 的逐年记录塞进仓库，
也没有任何一条断言被降级。

    python3 docs/evidence/anime-cases-20260914/verify-cases.py [--data-dir 观察台数据目录]

`--data-dir` 是可选的：指向一个真实的观察台数据目录
（里面要有 `runs/<run_id>/years.jsonl`），脚本就改用那份**真正落过盘的记录**，
并额外断言它与就地重算的结果逐年相同。不给就只用仓库里的东西。

任何一条对不上就返回非零退出码：文档里的数字不许"看起来合理"。
"""
import argparse, json, sys, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]                      # docs/evidence/<本目录> -> 仓库根
sys.path.insert(0, str(REPO))

ap = argparse.ArgumentParser()
ap.add_argument("--data-dir", default=os.environ.get("ANIME_CASES_DATA_DIR"),
                help="可选：真实观察台数据目录（需含 runs/<run_id>/years.jsonl）")
ARGS = ap.parse_args()

CASES = json.loads((HERE / "real-cases.json").read_text(encoding="utf-8"))
RUNS = CASES["runs"]
A, B, C, D = (RUNS[t]["run_id"] for t in ("A", "B", "C", "D"))

from observer import adapter, config            # noqa: E402  只读加载，不起服务

PARAM_KEYS = ("sigma_m", "move_mort_m", "share_m", "aid_m", "recip_m", "farm_m")


def replay(tag):
    """按证据里记着的参数就地重算整段历史，返回逐年记录（与接口同一口径）。"""
    r = RUNS[tag]
    eng, sha = adapter.load_engine(r["engine"])
    keys = set(config.ENGINES[r["engine"]]["params"])
    kw = {k: r[k] for k in PARAM_KEYS if k in keys}
    st = eng.make_world(r["seed"], config.ARMS[r["arm"]]["poison"], **kw)
    rec = adapter.Recorder(r["engine"])
    rows = [rec.year_record(st)]
    for _ in range(r["years"]):
        eng.step(st)
        rows.append(rec.year_record(st))
    return rows, sha


def from_disk(run_id):
    """--data-dir 模式：读真正落过盘的逐年记录。"""
    p = Path(ARGS.data_dir) / "runs" / run_id / "years.jsonl"
    return [json.loads(l) for l in p.open(encoding="utf-8")]


ok = bad = 0

def _brief(v, cap=150):
    t = repr(v)
    return t if len(t) <= cap else t[:cap] + f"…（共 {len(t)} 字符）"


def check(name, got, want):
    """比较是**精确**的；只有打印出来的那一行会截断，方便人读。"""
    global ok, bad
    good = got == want
    ok, bad = ok + good, bad + (not good)
    print(f"  {'PASS' if good else 'FAIL'}  {name:52s} 记录={_brief(got)}"
          + ("" if good else f"  文档={_brief(want)}"))

def ev(rows, eid):
    for r in rows:
        for e in r['events']:
            if e['id'] == eid:
                return e
    return None

def firstev(rows, t):
    for r in rows:
        for e in r['events']:
            if e['type'] == t:
                return r['t'], e
    return None, None

def count(rows, t):
    return sum(1 for r in rows for e in r['events'] if e['type'] == t)


def committed(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


print("== 响应可重放：就地重算 == 已提交的真实 API 响应 ==")
REPLAY = {}
for tag in ("A", "B", "C", "D"):
    rows, sha = replay(tag)
    REPLAY[tag] = rows
    meta = committed(f"run{tag}-meta.json")
    check(f"{tag} 重算用的引擎源码就是记录里那一版（sha256）", sha, meta["engine_sha256"])
    check(f"{tag} 重算 {len(rows) - 1} 年，年数与记录一致", len(rows) - 1, meta["years_done"])

CITED = {"A": (0, 1, 2, 4, 52, 218, 219, 267, 290, 295, 297, 300),
         "B": (300,), "C": (300,), "D": (1, 41, 300)}
for tag, ts in CITED.items():
    for t in ts:
        want = committed(f"run{tag}-year-{t}.json")
        check(f"{tag} 第 {t} 年：重算结果与已提交响应逐字段相同",
              REPLAY[tag][t] == want,
              True if REPLAY[tag][t] == want else
              [k for k in set(REPLAY[tag][t]) | set(want)
               if REPLAY[tag][t].get(k) != want.get(k)])

ra, rb, rc, rd = REPLAY["A"], REPLAY["B"], REPLAY["C"], REPLAY["D"]
SOURCE = "就地重算（仓库内引擎 + 适配层）"
if ARGS.data_dir:
    print("== --data-dir：与真正落过盘的逐年记录对照 ==")
    for tag, rid in (("A", A), ("B", B), ("C", C), ("D", D)):
        disk = from_disk(rid)
        diff = [r["t"] for r, q in zip(disk, REPLAY[tag]) if r != q]
        check(f"{tag} 盘上的 years.jsonl 与重算逐年相同：不同的年份", diff, [])
        check(f"{tag} 盘上的年数", len(disk), len(REPLAY[tag]))
    ra, rb, rc, rd = (from_disk(x) for x in (A, B, C, D))
    SOURCE = f"盘上的记录（--data-dir {ARGS.data_dir}）"
print(f"  ——以下断言的数据来源：{SOURCE}")

print("== 案例 1 第一次开垦 ==")
t, e = firstev(ra, 'field_built')
check("首次开垦年份", t, 1)
check("事件 id", e['id'], 't1-field_built-0')
check("cell", e['cell'], 0)
check("参与者", e['participants'], ['7567856178022945294'])
check("amount_m / labour_used_m", (e['amount_m'], e['labour_used_m']), (5000, 5000))
check("field 0 → 5000", (e['field_before_m'], e['field_after_m']), (0, 5000))
check("第1年 人口/群体/存粮/耕地",
      (ra[1]['agg']['pop'], ra[1]['agg']['bands'], ra[1]['agg']['store_total'],
       ra[1]['farm']['field_total_m']), (120, 6, 41401117, 30000))
check("第1年 built_m / harvested_kcal",
      (ra[1]['farm']['year']['built_m'], ra[1]['farm']['year']['harvested_kcal']), (30000, 0))

print("== 案例 2 第一次收成 ==")
t, e = firstev(ra, 'farm_harvest')
check("首次收成年份", t, 2)
check("事件 id", e['id'], 't2-farm_harvest-0')
check("weather_m", e['weather_m'], 949)
check("potential / harvested / uncollected",
      (e['potential_kcal'], e['kcal'], e['uncollected_kcal']), (8659625, 3849598, 4810027))
check("第2年 人口/群体/存粮/耕地",
      (ra[2]['agg']['pop'], ra[2]['agg']['bands'], ra[2]['agg']['store_total'],
       ra[2]['farm']['field_total_m']), (120, 6, 64497805, 30000))
check("第2年 farm.year", tuple(ra[2]['farm']['year'][k] for k in
      ('farm_effort_m', 'forage_effort_m', 'potential_kcal', 'harvested_kcal', 'uncollected_kcal')),
      (30000, 90000, 48399000, 25424715, 22974285))
check("第2年 weather_m 取值",
      sorted({c['weather_m'] for c in ra[2]['farm']['cells'] if c['weather_m'] is not None}),
      [759, 787, 846, 937, 949, 1026])

print("== 案例 3 第一次退化 ==")
t, e = firstev(ra, 'field_decay')
check("首次退化年份 / id", (t, e['id']), (4, 't4-field_decay-6'))
check("cell / 参与者", (e['cell'], e['participants']), (26, ['16913398721865340058']))
check("labour_m / unworked_m / amount_m", (e['labour_m'], e['unworked_m'], e['amount_m']), (4750, 250, 50))
check("field 5000 → 4950", (e['field_before_m'], e['field_after_m']), (5000, 4950))
check("第4年 人口/群体/存粮/耕地",
      (ra[4]['agg']['pop'], ra[4]['agg']['bands'], ra[4]['agg']['store_total'],
       ra[4]['farm']['field_total_m']), (124, 6, 67890000, 31200))

print("== 案例 4 第一次分裂 ==")
t, e = firstev(ra, 'split')
check("首次分裂年份 / id", (t, e['id']), (52, 't52-split-0'))
check("亲子", (e['parent'], e['band']), ('10929267446675359160', '10755205082838774531'))
check("第52年 人口/群体/存粮/耕地",
      (ra[52]['agg']['pop'], ra[52]['agg']['bands'], ra[52]['agg']['store_total'],
       ra[52]['farm']['field_total_m']), (200, 8, 105401609, 50850))

print("== 案例 5 第一次迁移 ==")
t, e = firstev(ra, 'migrate')
check("首次迁移年份 / id", (t, e['id']), (218, 't218-migrate-1'))
check("群体 / 起讫", (e['band'], e['from'], e['to']), ('13746285471758625353', 23, 31))
check("第218年 人口/群体/存粮/耕地",
      (ra[218]['agg']['pop'], ra[218]['agg']['bands'], ra[218]['agg']['store_total'],
       ra[218]['farm']['field_total_m']), (759, 27, 372796670, 191336))
check("第218年 当年迁移 / 迁移死亡",
      (ra[218]['year']['mig_total'], ra[218]['year']['mig_deaths_cum']), (1, 3))
check("A 迁移总次数", count(ra, 'migrate'), 28)
tc, _ = firstev(rc, 'migrate')
check("C 首次迁移年份 / 总次数", (tc, count(rc, 'migrate')), (26, 153))

print("== 案例 6 第一次信息交换 ==")
t, e = firstev(ra, 'share')
check("首次交换年份 / id", (t, e['id']), (219, 't219-share-1'))
check("cell / mem_cell / memt / value", (e['cell'], e['mem_cell'], e['memt'], e['value']),
      (31, 23, 217, 11143912))
check("第219年 人口/群体/存粮/耕地",
      (ra[219]['agg']['pop'], ra[219]['agg']['bands'], ra[219]['agg']['store_total'],
       ra[219]['farm']['field_total_m']), (770, 28, 379642545, 202982))

print("== 案例 7 第一次援助 ==")
t, e = firstev(ra, 'aid')
check("首次援助年份 / id", (t, e['id']), (267, 't267-aid-4'))
check("捐受 / kcal / phase / repay",
      (e['donor'], e['receiver'], e['kcal'], e['phase'], e['repay']),
      ('13746285471758625353', '17007643766652821449', 83864, 'normal', False))
check("第267年 人口/群体/存粮/耕地",
      (ra[267]['agg']['pop'], ra[267]['agg']['bands'], ra[267]['agg']['store_total'],
       ra[267]['farm']['field_total_m']), (1183, 33, 547574682, 298200))

print("== 案例 8 唯一一次回助 ==")
reps = [(r['t'], e) for r in ra for e in r['events'] if e['type'] == 'aid' and e.get('repay')]
check("整段回助笔数", len(reps), 1)
t, e = reps[0]
check("回助年份 / id", (t, e['id']), (295, 't295-aid-24'))
check("捐受 / kcal / phase", (e['donor'], e['receiver'], e['kcal'], e['phase']),
      ('2324318534456326687', '7329565065455868839', 1307221, 'recip'))
check("basis 记得的那一笔", (e['basis']['remembered_kcal'], e['basis']['remembered_last_event_id']),
      (53537, 't290-aid-13'))
prior = ev(ra, 't290-aid-13')
check("被记住那笔的方向相反", (prior['donor'], prior['receiver'], prior['kcal'], prior['cell']),
      ('7329565065455868839', '2324318534456326687', 53537, 22))
check("第295年 人口/群体/存粮",
      (ra[295]['agg']['pop'], ra[295]['agg']['bands'], ra[295]['agg']['store_total']),
      (1518, 41, 490580560))
check("模型里没有 repay 事件类型", count(ra, 'repay'), 0)

print("== 案例 9 / 10 峰值与末年 ==")
pk = max(ra, key=lambda r: r['agg']['pop'])
check("峰值年 / 人口 / 群体", (pk['t'], pk['agg']['pop'], pk['agg']['bands']), (297, 1550, 42))
check("峰值年 存粮 / 耕地", (pk['agg']['store_total'], pk['farm']['field_total_m']), (523032677, 412990))
top3 = [(b['name'], b['cell'], b['size']) for b in sorted(pk['bands'], key=lambda b: -b['size'])[:3]]
check("峰值年 最大三个群体", top3,
      [('群体-4E84D0', 29, 74), ('群体-940B29', 30, 73), ('群体-90C5CA', 18, 71)])
last = ra[300]
check("末年 人口/群体/存粮/野外存量",
      (last['agg']['pop'], last['agg']['bands'], last['agg']['store_total'], last['agg']['stock_total']),
      (1549, 45, 522080652, 1678450826))
check("末年 耕地总量 / cells 条数",
      (last['farm']['field_total_m'], len(last['farm']['cells'])), (454083, 34))
w = [c['weather_m'] for c in last['farm']['cells'] if c['weather_m'] is not None]
check("末年 weather_m 最小/最大/取值数", (min(w), max(w), len(set(w))), (635, 1355, 34))
check("末年 farm.cum", tuple(last['farm']['cum'][k] for k in
      ('farm_effort_m', 'forage_effort_m', 'potential_kcal', 'harvested_kcal',
       'uncollected_kcal', 'built_m', 'decayed_m')),
      (41345500, 124036500, 74138422542, 37875291133, 36263131409, 799841, 345758))
check("末年 全局账", tuple(last['cum'][k] for k in
      ('births_cum', 'deaths_demo_cum', 'mig_deaths_cum', 'mig_total', 'aid_events',
       'aid_transfers', 'aid_kcal', 'repay_transfers', 'repay_kcal', 'share_groups')),
      (7404, 5927, 48, 28, 18, 30, 57271429, 1, 1307221, 193))
check("末年 恒等式全为 0", last['integrity'],
      {'conservation_error': 0, 'state_hash': last['integrity']['state_hash'],
       'population_identity_error': 0, 'share_ledger_error': 0,
       'aid_ledger_error': 0, 'aid_memory_error': 0})

print("== 受控对照 ==")
check("C 末年 人口/群体/存粮/耕地",
      (rc[300]['agg']['pop'], rc[300]['agg']['bands'], rc[300]['agg']['store_total'],
       rc[300]['farm']['field_total_m']), (282, 15, 129103117, 0))
check("C 末年 forage 累计是真账", rc[300]['farm']['cum']['forage_effort_m'], 70686000)
check("C 末年 farm 累计全 0",
      [rc[300]['farm']['cum'][k] for k in ('farm_effort_m', 'potential_kcal', 'harvested_kcal',
                                           'uncollected_kcal', 'built_m', 'decayed_m')],
      [0, 0, 0, 0, 0, 0])
shared = set(rb[0]['cum']) & set(rc[0]['cum'])
diff = [r['t'] for r, s in zip(rb, rc)
        if r['agg'] != s['agg'] or r['stock'] != s['stock']
        or any(r['cum'][k] != s['cum'][k] for k in shared)
        or [(x['id'], x['cell'], x['size'], x['store']) for x in r['bands']]
           != [(x['id'], x['cell'], x['size'], x['store']) for x in s['bands']]
        or [e['id'] for e in r['events']] != [e['id'] for e in s['events']]]
check("C(exp07 farm0) 与 B(exp06) 逐年全同：不同的年份", diff, [])
check("B 第300年没有 farm 段", 'farm' in rb[300], False)
check("B 第300年顶层键", sorted(rb[300]), sorted(
      ['t', 'stock', 'bands', 'cum', 'year', 'agg', 'integrity', 'events', 'share', 'aid', 'recip']))
check("B 末年 人口/群体", (rb[300]['agg']['pop'], rb[300]['agg']['bands']), (282, 15))

print("== 没有发生的事 ==")
check("extinct 事件次数", count(ra, 'extinct'), 0)
cells = committed('runA-meta.json')['meta']['cell_ids']
prev, back = None, []
ever, end = set(), set()
for r in ra:
    f = r['farm']['field_m']
    for i, v in enumerate(f):
        if v > 0: ever.add(cells[i])
    if prev is not None:
        for i, (p0, v) in enumerate(zip(prev, f)):
            if p0 > 0 and v == 0: back.append((r['t'], cells[i]))
    prev = f
for i, v in enumerate(ra[300]['farm']['field_m']):
    if v > 0: end.add(cells[i])
check("耕地退回 0 的次数", len(back), 0)
check("曾有耕地 / 末年仍有耕地 的格数", (len(ever), len(end)), (34, 34))
defy = [r['t'] for r in ra if r['year']['deficit_cum'] > 0]
check("出现缺口的年份数 / 最早", (len(defy), defy[0]), (14, 218))
check("累计缺口 / 累计需求", (last['cum']['deficit_cum'], last['cum']['need_cum']),
      (104865559, 120728860000))
migy = [r['t'] for r in ra if r['year']['mig_deaths_cum'] > 0]
check("迁移死亡分布年份数", len(migy), 14)

print("== 事件 id ==")
ids = [e['id'] for r in ra for e in r['events']]
check("A 事件总数", len(ids), 6969)
check("A 事件 id 无重复", len(set(ids)), len(ids))
check("t218 当年 -0 是分裂（序号各类型共用）", ra[218]['events'][0]['id'], 't218-split-0')

print("== 已提交的卷宗 / 关系网与整段历史对得上 ==")
farmer = committed('bandA-farmer-y2.json')
fid = farmer['id']
check("首个耕作者卷宗的 sizes 就是逐年记录里的 (年, 人数, 存粮)",
      farmer['sizes'],
      [[r['t'], b['size'], b['store']] for r in ra[:3] for b in r['bands'] if b['id'] == fid])
check("卷宗的 state_at_year 与第 2 年记录一致",
      farmer['state_at_year'],
      next({"year": 2, "cell": b['cell'], "size": b['size'], "store": b['store']}
           for b in ra[2]['bands'] if b['id'] == fid))
check("卷宗说它是开局群体，记录里第 0 年就在", (farmer['first_seen'], farmer['parent']),
      (0, None) if any(b['id'] == fid for b in ra[0]['bands']) else ("第0年没有它", None))

rep = committed('bandA-repayer-y295.json')
rid_ = rep['id']
split = next(e for r in ra for e in r['events']
             if e['type'] == 'split' and e['band'] == rid_)
check("回助者卷宗的血缘与分裂事件一致",
      (rep['parent'], rep['born_at']), (split['parent'], split['year']))
check("回助者卷宗的 sizes 覆盖第 218..295 年且逐年对得上",
      rep['sizes'],
      [[r['t'], b['size'], b['store']] for r in ra[218:296]
       for b in r['bands'] if b['id'] == rid_])

rel = committed('relationsA-y295.json')
aid_ids = {e['id'] for r in ra[:296] for e in r['events'] if e['type'] == 'aid'}
edge_ids = [i for e in rel['edges'] for i in e['event_ids']]
check("关系网每一条边引用的事件 id 都在第 0..295 年的记录里", set(edge_ids) - aid_ids, set())
check("关系网的总转移笔数 == 第 0..295 年的援助事件条数",
      rel['totals']['transfers'], len(aid_ids))
check("关系网的总 kcal == 那些援助事件的 kcal 之和",
      rel['totals']['kcal'],
      sum(e['kcal'] for r in ra[:296] for e in r['events'] if e['type'] == 'aid'))
by_edge = {}
for r in ra[:296]:
    for e in r['events']:
        if e['type'] == 'aid':
            by_edge.setdefault((e['donor'], e['receiver']), []).append(e)
check("关系网每条边的 kcal / 笔数 / 最近一次事件都能逐条对回记录",
      [(e['donor'], e['receiver'], e['kcal'], e['transfers'], e['last_event_id'])
       for e in sorted(rel['edges'], key=lambda x: (x['donor'], x['receiver']))],
      [(d, rc_, sum(x['kcal'] for x in evs), len(evs), evs[-1]['id'])
       for (d, rc_), evs in sorted(by_edge.items())])

print("== 案例 11 弃耕（D，FARM_M=1000）==")
cells_d = committed('runD-meta.json')['meta']['cell_ids']
prev, zeroed = None, []
for r in rd:
    f = r['farm']['field_m']
    if prev is not None:
        for i, (a, b) in enumerate(zip(prev, f)):
            if a > 0 and b == 0:
                zeroed.append((r['t'], cells_d[i]))
    prev = f
check("D 里耕地退回 0 的次数与位置", zeroed,
      [(41, 6), (41, 18), (41, 26), (206, 6), (251, 18), (254, 37), (296, 13)])
b1 = [e['id'] for e in rd[1]['events'] if e['type'] == 'field_built' and e['cell'] in (6, 18, 26)]
check("第1年 6/18/26 号格各开垦一块", b1, ['t1-field_built-4', 't1-field_built-6', 't1-field_built-7'])
check("第1年三块地各 20000，且当年 worked_m 都是 0（新地不产出）",
      [(c['cell'], c['built_m'], c['worked_m'], c['potential_kcal'])
       for c in rd[1]['farm']['cells'] if c['cell'] in (6, 18, 26)],
      [(6, 20000, 0, 0), (18, 20000, 0, 0), (26, 20000, 0, 0)])
check("第1年那三个群体就迁走了", [e['id'] for e in rd[1]['events'] if e['type'] == 'migrate'],
      ['t1-migrate-0', 't1-migrate-1', 't1-migrate-2'])
mig1 = next(e for e in rd[1]['events'] if e['id'] == 't1-migrate-1')
check("t1-migrate-1 是 6 号格那一支", (mig1['band'], mig1['from'], mig1['to']),
      ('10929267446675359160', 6, 15))
i6 = cells_d.index(6)
check("6 号格 1→41 年的耕地轨迹（按 200‰ 逐年退化）",
      [rd[t]['farm']['field_m'][i6] for t in (1, 2, 3, 4, 5, 38, 39, 40, 41)],
      [20000, 16000, 12800, 10240, 8192, 3, 2, 1, 0])
check("这些年 6 号格一直没人投耕作劳动",
      all(c['worked_m'] == 0 for r in rd[2:42] for c in r['farm']['cells'] if c['cell'] == 6), True)
dec41 = [(e['id'], e['cell'], e['field_before_m'], e['field_after_m'])
         for e in rd[41]['events'] if e['type'] == 'field_decay' and e['cell'] in (6, 18, 26)]
check("第41年三条归零事件", dec41,
      [('t41-field_decay-4', 6, 1, 0), ('t41-field_decay-10', 18, 1, 0),
       ('t41-field_decay-11', 26, 1, 0)])
check("D 第1/41/300 年的人口 群体 耕地",
      [(rd[t]['agg']['pop'], rd[t]['agg']['bands'], rd[t]['farm']['field_total_m'])
       for t in (1, 41, 300)], [(66, 6, 120000), (76, 6, 76120), (683, 25, 647530)])
badsum_d = [(r['t'], k) for r in rd
            for k in ('potential_kcal', 'harvested_kcal', 'uncollected_kcal', 'built_m', 'decayed_m')
            if sum(c[k] for c in r['farm']['cells']) != r['farm']['year'][k]]
check("D 全部 301 年也满足逐格加总 == farm.year", badsum_d, [])

print("== 逐格明细能独立加回当年总量 ==")
SUMKEYS = ('potential_kcal', 'harvested_kcal', 'uncollected_kcal', 'built_m', 'decayed_m')
badsum = [(r['t'], k, sum(c[k] for c in r['farm']['cells']), r['farm']['year'][k])
          for r in ra for k in SUMKEYS
          if sum(c[k] for c in r['farm']['cells']) != r['farm']['year'][k]]
check("A 全部 301 年：cells 逐格加总 == farm.year（五项）", badsum, [])
zero = [(r['t'], c['cell'], c['potential_kcal']) for r in ra for c in r['farm']['cells']
        if c['potential_kcal'] > 0 and c['harvested_kcal'] == 0]
check("存在「潜在产出全没人收」的格，且它没被算成 0", len(zero) > 0, True)
check("第2年 cell 14 / 30 正是这种格", [z for z in zero if z[0] == 2],
      [(2, 14, 6925875), (2, 30, 9362250)])
check("第2年 逐格明细逐行", [(c['cell'], c['weather_m'], c['worked_m'], c['potential_kcal'],
                          c['harvested_kcal'], c['uncollected_kcal'])
                         for c in ra[2]['farm']['cells']],
      [(0, 949, 5000, 8659625, 3849598, 4810027),
       (6, 937, 5000, 8550125, 8155872, 394253),
       (14, 759, 5000, 6925875, 0, 6925875),
       (18, 787, 5000, 7181375, 5699495, 1481880),
       (26, 846, 5000, 7719750, 7719750, 0),
       (30, 1026, 5000, 9362250, 0, 9362250)])

print("== 跨实例回放（另一条 run_id、另一个数据目录，同参数同版本）==")
SAMPLE = HERE.parent / 'exp07-20260913' / 'sample-year.json'
if SAMPLE.exists():
    sm = json.loads(SAMPLE.read_text(encoding='utf-8'))
    check("样例与案例 A 是同一组参数（跨实例比较的前提）",
          [sm['run'][k] for k in ('seed', 'sigma_m', 'move_mort_m', 'share_m',
                                  'aid_m', 'recip_m', 'farm_m', 'arm')],
          [RUNS['A'][k] for k in ('seed', 'sigma_m', 'move_mort_m', 'share_m',
                                  'aid_m', 'recip_m', 'farm_m', 'arm')])
    s12, a12 = sm['year_12'], ra[12]
    check("样例是另一条 run_id", sm['run']['run_id'] != A, True)
    check("model_run_id 相同", sm['run']['model_run_id'], '8d6281d91c14c3697d4390e8baca5fb9')
    check("第12年 farm.year 相同", s12['farm']['year'], a12['farm']['year'])
    check("第12年 farm.cum 相同", s12['farm']['cum'], a12['farm']['cum'])
    check("第12年 agg 相同", s12['agg'], a12['agg'])
    check("第12年 事件 id 相同", [e['id'] for e in s12['events']], [e['id'] for e in a12['events']])
    check("第12年 状态摘要相同", s12['integrity']['state_hash'], a12['integrity']['state_hash'])
else:
    print("  未覆盖  sample-year.json 不在（跨实例回放这一组没跑）")

print("== 交接清单 anime-cases-1 与整段历史一致 ==")
MAN = HERE / "anime-cases-manifest.json"
if not MAN.exists():
    print("  未覆盖  anime-cases-manifest.json 不在，交接清单这一组没跑")
else:
    man = json.loads(MAN.read_text(encoding="utf-8"))
    check("契约名", man["contract"], "anime-cases-1")
    by_tag = {s["tag"]: s for s in man["samples"]}
    check("清单覆盖 A/B/C/D 四条", sorted(by_tag), ["A", "B", "C", "D"])
    PRED = {"clearing": lambda e: e["type"] == "field_built",
            "harvest": lambda e: e["type"] == "farm_harvest",
            "migrate": lambda e: e["type"] == "migrate",
            "aid": lambda e: e["type"] == "aid",
            "repay": lambda e: e["type"] == "aid" and e.get("repay") is True}
    for tag in ("A", "B", "C", "D"):
        s_ = by_tag[tag]
        rows = REPLAY[tag]
        meta = committed(f"run{tag}-meta.json")
        check(f"{tag} 清单的模型哈希与已核验的运行一致",
              (s_["model_run_id"], s_["full_digest"], s_["engine_sha256"]),
              (meta["model_run_id"], meta["full_digest"], meta["engine_sha256"]))
        check(f"{tag} 清单的配置与已核验的运行一致",
              {k: v for k, v in s_["config"].items() if v is not None},
              {k: RUNS[tag][k] for k in ("seed", "years", "sigma_m", "move_mort_m",
                                         "share_m", "aid_m", "recip_m", "arm")}
              | ({"farm_m": RUNS[tag]["farm_m"]} if s_["engine"] == "exp07" else {}))
        check(f"{tag} 清单的 sample_id 是固定值，不是随机 uuid",
              s_["sample_id"].startswith("preset-anime-"), True)
        for key, pred in PRED.items():
            hits = [(r["t"], e["id"]) for r in rows for e in r["events"] if pred(e)]
            got = s_["events"][key]
            if hits:
                check(f"{tag} {got['label']}：首次/末次/次数与记录一致",
                      (got["present"], got["first_year"], got["first_event_id"],
                       got["last_year"], got["last_event_id"], got["count"]),
                      (True, hits[0][0], hits[0][1], hits[-1][0], hits[-1][1], len(hits)))
            else:
                farm_side = key in ("clearing", "harvest")
                want = ("engine_lacks_mechanism" if farm_side and s_["engine"] != "exp07"
                        else "param_zero" if farm_side and s_["config"]["farm_m"] == 0
                        else "not_observed")
                check(f"{tag} {got['label']}：确实没有，且缺项理由是 {want}",
                      (got["present"], got["count"], got["reason_code"]),
                      (False, 0, want))
        check(f"{tag} 清单的末年读数与记录一致",
              (s_["final_year"]["year"], s_["final_year"]["pop"], s_["final_year"]["bands"],
               s_["final_year"]["store_total_kcal"], s_["final_year"]["field_total_m"]),
              (rows[-1]["t"], rows[-1]["agg"]["pop"], rows[-1]["agg"]["bands"],
               rows[-1]["agg"]["store_total"],
               rows[-1]["farm"]["field_total_m"] if "farm" in rows[-1] else None))
        check(f"{tag} 清单的事件总数与 farm 段有无与记录一致",
              (s_["total_events"], s_["has_farm_section"]),
              (sum(len(r["events"]) for r in rows), "farm" in rows[-1]))
    # 清单文档里另外点名的几类
    check("B/C 分裂首次与次数（清单文档 §3 末）",
          [(next((r["t"], e["id"]) for r in rb for e in r["events"] if e["type"] == "split"),
            count(rb, "split")),
           (next((r["t"], e["id"]) for r in rc for e in r["events"] if e["type"] == "split"),
            count(rc, "split"))],
          [((66, "t66-split-0"), 9), ((66, "t66-split-0"), 9)])
    check("D 分裂首次与次数",
          (next((r["t"], e["id"]) for r in rd for e in r["events"] if e["type"] == "split"),
           count(rd, "split")), ((116, "t116-split-0"), 19))
    check("D 耕地退化首次与次数",
          (next((r["t"], e["id"]) for r in rd for e in r["events"]
                if e["type"] == "field_decay"), count(rd, "field_decay")),
          ((2, "t2-field_decay-5"), 1055))
    check("A 耕地退化次数", count(ra, "field_decay"), 1251)
    check("四条都没有群体消失", [count(x, "extinct") for x in (ra, rb, rc, rd)], [0, 0, 0, 0])

print()
print(f"  通过 {ok} / 失败 {bad}（共 {ok + bad} 项）")
sys.exit(1 if bad else 0)
