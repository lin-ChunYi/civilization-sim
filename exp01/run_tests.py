import verify as v
SEEDS=[12345,777,4242,99,31337,2026]; Y=300
R={}
def hdr(t): print("\n"+"="*74+f"\n{t}\n"+"="*74)

hdr("T1 同种子两次运行逐位相同")
ok=all((v.run(s,Y)[0] and v.state_hash(v.run(s,Y)[0])==v.state_hash(v.run(s,Y)[0])) for s in SEEDS[:3])
for s in SEEDS[:3]:
    a=v.state_hash(v.run(s,Y)[0]); b=v.state_hash(v.run(s,Y)[0])
    print(f"  seed={s}: {a[:16]} vs {b[:16]}  {'一致' if a==b else '不一致'}")
R['T1']=ok; print(f"  => {'通过' if ok else '失败'}")

hdr("T2 快照恢复后继续，与不中断的运行逐位相同")
ok=True
for s in SEEDS[:3]:
    full,snap = v.run(s,Y,snap_at=150)
    cont = v.resume(snap, Y-150)
    a,b = v.state_hash(full), v.state_hash(cont)
    print(f"  seed={s}: {a[:16]} vs {b[:16]}  {'一致' if a==b else '不一致'}")
    ok &= (a==b)
R['T2']=ok; print(f"  => {'通过' if ok else '失败'}")

hdr("T3 区块隔离：抑制 A 区分裂，B 区必须逐位相同")
ok=True
for s in SEEDS[:3]:
    base,_ = v.run(s,Y)
    interv,_ = v.run(s,Y,suppress='A')
    hb0,hb1 = v.region_hash(base,'B'), v.region_hash(interv,'B')
    ha0,ha1 = v.region_hash(base,'A'), v.region_hash(interv,'A')
    changedA = ha0!=ha1
    print(f"  seed={s}: B区 {'相同' if hb0==hb1 else '不同'} | A区 {'已改变(干预生效)' if changedA else '未改变(干预无效!)'}")
    ok &= (hb0==hb1) and changedA
R['T3']=ok; print(f"  => {'通过' if ok else '失败'}")

hdr("T4 守恒：每 tick 整数收支闭合")
ok=True
for s in SEEDS:
    st=v.make_world(s)
    worst=0
    for _ in range(Y):
        v.step(st); worst=max(worst,abs(v.conservation_error(st)))
    print(f"  seed={s}: 最大绝对误差 {worst}")
    ok &= (worst==0)
R['T4']=ok; print(f"  => {'通过' if ok else '失败'}")

hdr("T5 信息边界确实在起作用（迁移决策用的是过时信息）")
tot=reg=stale=0
for s in SEEDS:
    st,_=v.run(s,Y); tot+=st['mig_total']; reg+=st['mig_regret']; stale+=st['stale_sum']
print(f"  6 个种子合计：迁移 {tot} 次，平均信息滞后 {stale/max(1,tot):.1f} 年，事后看错 {reg} 次（{reg*100/max(1,tot):.1f}%）")
R['T5']=(stale>0 and reg>0); print(f"  => {'通过（滞后>0 且存在误判）' if R['T5'] else '失败'}")

hdr("T6 逆序遍历不变性（同时结算 ⇒ 与遍历顺序无关）")
ok=True
for s_ in SEEDS:
    a=v.state_hash(v.run(s_,Y)[0]); b=v.state_hash(v.run(s_,Y,poison='revorder')[0])
    print(f"  seed={s_}: {'一致' if a==b else '不一致'}")
    ok &= (a==b)
R['T6']=ok; print(f"  => {'通过' if ok else '失败'}")

hdr("错误注入：每个版本必须让它的目标性质真的失败")
def det_same(s,p): return v.state_hash(v.run(s,Y,poison=p)[0])==v.state_hash(v.run(s,Y,poison=p)[0])
def cons_ok(s,p):
    st=v.make_world(s,p); w=0
    for _ in range(Y):
        v.step(st); w=max(w,abs(v.conservation_error(st)))
    return w==0
def iso_ok(s,p):
    a,_=v.run(s,Y,poison=p); b,_=v.run(s,Y,poison=p,suppress='A')
    return v.region_hash(a,'B')==v.region_hash(b,'B')
def regret(p):
    t=r=0
    for s in SEEDS:
        st,_=v.run(s,Y,poison=p); t+=st['mig_total']; r+=st['mig_regret']
    return r,t

rows=[]
r,t = regret('')
rows.append(("(健康内核)", "—", f"守恒OK 隔离OK 后悔{r}/{t}", "—"))
# poison-seq
res=[v.state_hash(v.run(s,Y,poison='seq')[0])==v.state_hash(v.run(s,Y,poison='seq,revorder')[0]) for s in SEEDS[:3]]
rows.append(("poison-seq  回到顺序结算（放弃同时结算）","T6 逆序不变性",
             f"顺序不变性保持={sum(res)}/3", "触发" if not all(res) else "未触发"))
# poison-counter
res=[iso_ok(s,'counter') for s in SEEDS[:3]]
rows.append(("poison-counter  band_id 改全局自增","T3 区块隔离",
             f"隔离保持={sum(res)}/3", "触发" if not all(res) else "未触发"))
# poison-clamp
res=[cons_ok(s,'clamp') for s in SEEDS[:3]]
rows.append(("poison-clamp  储存腐损处加 max(0,·)","T4 守恒审计",
             f"守恒保持={sum(res)}/3", "触发" if not all(res) else "未触发"))
# poison-omniscient
r2,t2 = regret('omniscient')
rows.append(("poison-omniscient  迁移读当年真值","T5 信息边界",
             f"后悔 {r2}/{t2}（健康版 {r}/{t}）", "触发" if r2==0 and r>0 else "未触发"))
# poison-float
res=[det_same(s,'float') for s in SEEDS[:3]]
rows.append(("poison-float  采集用浮点","跨架构逐位一致（本切片范围外）",
             f"同机确定性保持={sum(res)}/3", "本切片检不出"))
print(f"\n  {'变体':44s} {'目标性质':26s} {'实测':30s} {'结论'}")
for a,b,c,d in rows: print(f"  {a:44s} {b:26s} {c:30s} {d}")

hdr("汇总")
for k in ['T1','T2','T3','T4','T5','T6']: print(f"  {k}: {'通过' if R[k] else '失败'}")
