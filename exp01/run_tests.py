#!/usr/bin/env python3
"""EXP-01 检验套件。

必过项失败 => 进程退出码非零。
用法：python3 run_tests.py    ；  echo $? 查看退出码
"""
import sys
import verify as v

SEEDS = [0, 12345, 777, 4242, 99, 31337, 2026]   # seed=0 是回归案例，必须在列
Y = 300
MUST = {}          # 必过项 -> bool
NOTE = []          # 已知不触发但保留的记录

def hdr(t):
    print("\n" + "=" * 74 + f"\n{t}\n" + "=" * 74)

def mark(k, ok):
    MUST[k] = ok
    print(f"  => {k} {'通过' if ok else '失败'}")

# ---------------------------------------------------------------- T1
hdr("T1 同种子两次运行逐位相同（全状态哈希）")
ok = True
for s in SEEDS:
    a = v.state_hash(v.run(s, Y)[0]); b = v.state_hash(v.run(s, Y)[0])
    print(f"  seed={s:<6} {a[:16]} vs {b[:16]}  {'一致' if a == b else '不一致'}")
    ok &= (a == b)
mark('T1', ok)

# ---------------------------------------------------------------- T2
hdr("T2 第 150 年快照续跑至 300 年，与不中断运行逐位相同")
ok = True
for s in SEEDS:
    full, snap = v.run(s, Y, snap_at=150)
    cont = v.resume(snap, Y - 150)
    a, b = v.state_hash(full), v.state_hash(cont)
    print(f"  seed={s:<6} {a[:16]} vs {b[:16]}  {'一致' if a == b else '不一致'}")
    ok &= (a == b)
mark('T2', ok)

# ---------------------------------------------------------------- T3
hdr("T3 区块隔离：抑制 A 区分裂后，B 区逐位不变 且 A 区确实改变")
ok = True
for s in SEEDS:
    base, _ = v.run(s, Y)
    itv, _ = v.run(s, Y, suppress='A')
    b_same = v.region_hash(base, 'B') == v.region_hash(itv, 'B')
    a_diff = v.region_hash(base, 'A') != v.region_hash(itv, 'A')
    print(f"  seed={s:<6} B区{'相同' if b_same else '不同'} | A区{'已改变' if a_diff else '未改变(干预无效)'}")
    ok &= (b_same and a_diff)
mark('T3', ok)

# ---------------------------------------------------------------- T4
hdr("T4 守恒：每 tick 整数收支闭合")
ok = True
for s in SEEDS:
    st = v.make_world(s); worst = 0
    for _ in range(Y):
        v.step(st); worst = max(worst, abs(v.conservation_error(st)))
    print(f"  seed={s:<6} 最大绝对误差 {worst}")
    ok &= (worst == 0)
mark('T4', ok)

# ---------------------------------------------------------------- T5
hdr("T5 信息边界确实在起作用（迁移用的是过时信息）")
tot = reg = stale = 0
for s in SEEDS:
    st, _ = v.run(s, Y)
    tot += st['mig_total']; reg += st['mig_regret']; stale += st['stale_sum']
print(f"  {len(SEEDS)} 个种子合计：迁移 {tot} 次，平均信息滞后 {stale/max(1,tot):.1f} 年，"
      f"事后看错 {reg} 次（{reg*100/max(1,tot):.1f}%）")
mark('T5', stale > 0 and reg > 0)

# ---------------------------------------------------------------- T6
hdr("T6 逆序遍历不变性（同时结算 + 分裂同时提交 ⇒ 与遍历顺序无关）")
ok = True
for s in SEEDS:
    a = v.state_hash(v.run(s, Y)[0])
    b = v.state_hash(v.run(s, Y, poison='revorder')[0])
    print(f"  seed={s:<6} {a[:16]} vs {b[:16]}  {'一致' if a == b else '不一致'}")
    ok &= (a == b)
mark('T6', ok)

# ---------------------------------------------------------------- T8
hdr("T8 运行身份与状态摘要分离")
sub = {}

ids = {sd: v.run_id(v.make_world(sd)) for sd in SEEDS}
sub['(a) 不同 seed 的 run_id 两两不同'] = len(set(ids.values())) == len(SEEDS)
print(f"  (a) {len(set(ids.values()))}/{len(SEEDS)} 个不同的 run_id")

base = v.make_world(12345)
rev = v.make_world(12345, 'revorder')
sub['(b) 遍历标志不改变运行身份'] = v.run_id(base) == v.run_id(rev)
print(f"  (b) '' vs 'revorder' 的 run_id {'相同' if v.run_id(base)==v.run_id(rev) else '不同 <<< 遍历标志被误当成语义差异'}")

full, snap = v.run(12345, Y, snap_at=150)
cont = v.resume(snap, Y - 150)
sub['(c) 快照续跑保持同一运行身份'] = v.run_id(full) == v.run_id(cont) and v.full_digest(full) == v.full_digest(cont)
print(f"  (c) 快照续跑 full_digest {'一致' if v.full_digest(full)==v.full_digest(cont) else '不一致'}")

sem = v.make_world(12345, 'counter')
sub['(d) 语义注入改变运行身份'] = v.run_id(base) != v.run_id(sem)
print(f"  (d) '' vs 'counter' 的 run_id {'不同' if v.run_id(base)!=v.run_id(sem) else '相同 <<< 语义注入没进身份'}")

fp0 = v.params_fingerprint(); id0 = v.run_id(base)
v.SPLIT_SIZE += 1
fp1 = v.params_fingerprint(); id1 = v.run_id(base)
v.SPLIT_SIZE -= 1
sub['(e) 改参数改变运行身份'] = (fp0 != fp1) and (id0 != id1) and (v.params_fingerprint() == fp0)
print(f"  (e) SPLIT_SIZE ±1 -> 参数指纹 {'改变' if fp0!=fp1 else '未变'}，run_id {'改变' if id0!=id1 else '未变'}，还原后 {'一致' if v.params_fingerprint()==fp0 else '不一致'}")

try:
    v.make_world(1, 'not_a_registered_flag'); raised = False
except ValueError:
    raised = True
sub['(f) 未登记的注入标志报错'] = raised
print(f"  (f) 未登记标志 {'已报错' if raised else '被静默接受 <<< 危险'}")

sub['(g) state_hash 不含运行身份（因此不能单独当运行标识）'] = (
    v.state_hash(v.make_world(12345)) == v.state_hash(v.make_world(12345, 'revorder')))
print(f"  (g) state_hash 只描述动态状态，运行身份另记；两者合起来才是 full_digest")

for k, ok in sub.items():
    if not ok: print(f"      失败：{k}")
mark('T8', all(sub.values()))

# ---------------------------------------------------------------- 错误注入
hdr("错误注入：预期触发的必须真的触发")

def iso_holds(s, p):
    a, _ = v.run(s, Y, poison=p); b, _ = v.run(s, Y, poison=p, suppress='A')
    return v.region_hash(a, 'B') == v.region_hash(b, 'B')

def order_holds(s, p):
    base = p
    rev = p + ',revorder' if p else 'revorder'
    return v.state_hash(v.run(s, Y, poison=base)[0]) == v.state_hash(v.run(s, Y, poison=rev)[0])

def cons_holds(s, p):
    st = v.make_world(s, p); w = 0
    for _ in range(Y):
        v.step(st); w = max(w, abs(v.conservation_error(st)))
    return w == 0

def regret_of(p):
    t = r = 0
    for s in SEEDS:
        st, _ = v.run(s, Y, poison=p); t += st['mig_total']; r += st['mig_regret']
    return r, t

P = SEEDS[:4]
r0, t0 = regret_of('')

res = [iso_holds(s, 'counter') for s in P]
mark('P1 poison-counter 打破 T3', not all(res))
print(f"     band_id 改全局自增 -> 区块隔离保持 {sum(res)}/{len(P)}（应为 0）")

res = [order_holds(s, 'seq') for s in P]
mark('P2 poison-seq 打破 T6', not all(res))
print(f"     采集回到顺序结算 -> 逆序不变性保持 {sum(res)}/{len(P)}（应为 0）")

r1, t1 = regret_of('omniscient')
mark('P3 poison-omniscient 打破 T5', r1 == 0 and r0 > 0)
print(f"     迁移读当年真值 -> 事后看错 {r1}/{t1}（健康版 {r0}/{t0}）")

# 长跑里分裂申请 175 次、撞车 0 次，冲突解决路径从不被执行，
# 所以 seqsplit 必须由定向场景覆盖，而不是挂在 T6 的长跑上。
def conflict_probe(poison):
    import copy
    st, X, pid, qid = v.make_conflict_world(0)
    s2 = copy.deepcopy(st); s2['poison'] = poison
    v.step(s2)
    sp = [e for e in s2['log'] if e[1] == 'split']
    return (sp[0][2] if sp else None), pid, qid

fwd, pid, qid = conflict_probe('')
rev, _, _ = conflict_probe('revorder')
print(f"  [定向场景] 两个群体争同一个空位：健康版 正序胜者={'P' if fwd==pid else 'Q'} "
      f"逆序胜者={'P' if rev==pid else 'Q'}；规则是 min(band_id)，P 的 id 较小")
mark('T7 冲突解决与遍历顺序无关（定向场景）', fwd == rev == pid)

sfwd, _, _ = conflict_probe('seqsplit')
srev, _, _ = conflict_probe('seqsplit,revorder')
mark('P4 poison-seqsplit 打破 T7', sfwd != srev)
print(f"     分裂回到顺序解决空位 -> 正序胜者={'P' if sfwd==pid else 'Q'} "
      f"逆序胜者={'P' if srev==pid else 'Q'}（应不同）")

prop = conf = 0
for s in SEEDS:
    st, _ = v.run(s, Y)
    prop += st['prop_total']; conf += st['prop_conflict']
print(f"     [覆盖率记录] 长跑 {len(SEEDS)} 种子 × {Y} 年：分裂申请 {prop} 次，撞车 {conf} 次"
      f" —— 冲突路径在长跑中{'从不' if conf == 0 else '会'}被执行，因此定向场景是它唯一的覆盖")

hdr("已知不触发，保留不删（附原因）")
res = [cons_holds(s, 'clamp') for s in P]
NOTE.append(("poison-clamp", f"守恒保持 {sum(res)}/{len(P)}",
             "本切片内空转：消耗被可得量封顶，store 不可能变负，max(0,·) 是恒等操作。"
             "引入借贷/债务/强制征取后才承重。"))
res = [v.state_hash(v.run(s, Y, poison='float')[0]) == v.state_hash(v.run(s, Y, poison='float')[0]) for s in P]
NOTE.append(("poison-float", f"同机确定性保持 {sum(res)}/{len(P)}",
             "目标性质是跨架构逐位一致，本切片明确不要求；同机 Python 浮点确定，现有检验抓不到。"))
for name, meas, why in NOTE:
    print(f"  {name:20s} {meas:24s} {why}")

# ---------------------------------------------------------------- 汇总
hdr("汇总")
for k in sorted(MUST):
    print(f"  {k:32s} {'通过' if MUST[k] else '失败'}")
failed = [k for k, ok in MUST.items() if not ok]
print(f"\n必过项 {len(MUST) - len(failed)}/{len(MUST)} 通过")
if failed:
    print("失败：" + ", ".join(failed))
    sys.exit(1)
print("全部必过项通过")
sys.exit(0)
