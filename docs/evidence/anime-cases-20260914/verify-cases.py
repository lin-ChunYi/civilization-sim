#!/usr/bin/env python3
"""逐条复核 docs/ANIME-REAL-CASES.md 里写下的每一个数字。

用法：python3 verify-cases.py [数据目录]
默认数据目录 /tmp/chronicle-exp07-20260913/anime/data —— 也就是生成这份清单的那次运行。
任何一条对不上就返回非零退出码：文档里的数字不许"看起来合理"。
"""
import json, sys, os

DATA = sys.argv[1] if len(sys.argv) > 1 else '/tmp/chronicle-exp07-20260913/anime/data'
A, B, C, D = 'e289c4c7ff47', '05c2f8d4d969', 'fa781b561845', '4f83f009ef28'

def years(rid):
    p = os.path.join(DATA, 'runs', rid, 'years.jsonl')
    return [json.loads(l) for l in open(p)]

ra, rb, rc, rd = years(A), years(B), years(C), years(D)
ok = bad = 0

def check(name, got, want):
    global ok, bad
    good = got == want
    ok, bad = ok + good, bad + (not good)
    print(f"  {'PASS' if good else 'FAIL'}  {name:52s} 记录={got!r}" + ("" if good else f"  文档={want!r}"))

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
cells = json.load(open(os.path.join(DATA, 'runs', A, 'meta.json')))['cell_ids']
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

print("== 案例 11 弃耕（D，FARM_M=1000）==")
cells_d = json.load(open(os.path.join(DATA, 'runs', D, 'meta.json')))['cell_ids']
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
SAMPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', 'exp07-20260913', 'sample-year.json')
if os.path.exists(SAMPLE):
    sm = json.load(open(SAMPLE))
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

print()
print(f"  通过 {ok} / 失败 {bad}（共 {ok + bad} 项）")
sys.exit(1 if bad else 0)
