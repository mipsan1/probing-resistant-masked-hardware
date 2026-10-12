#!/usr/bin/env python3
"""cone_lint_def.py -- definition-faithful cone non-completeness check (added 2026-10-12).

Unlike tools/lint/lint_real.py (which labels primary-input domains and treats ANY cross-domain cone
that contains a mask bit as "BLINDED"), this script follows Definition `cone non-completeness`:
  * share-index support is propagated THROUGH registers;
  * a registered value counts as blinded only if it is u XOR p, where p is a fresh mask (or a
    register already blinded by masks) that occurs nowhere else in the cone's transitive fan-in.
    "d(D)/d(p)==1" is decided functionally on the cone by random evaluation, so it does not depend on
    how the technology mapper expressed the XOR;
  * all intermediate values are functions of the single S-box input secret, so a cone whose
    (unblinded) support contains both share indices is a violation.
Reads a flat Yosys gate-level Verilog netlist (cells AND/NAND/OR/NOR/XOR/XNOR/NOT/MUX/ANDNOT/ORNOT/DFF).
Usage (from the bundle root):  python3 tools/lint/cone_lint_def.py synth/prolead/circuit_v9_xform2.v
It is conservative: a violation is a candidate, not a proof of leakage (see cone_stat_check.py).
"""
# Definition-faithful cone non-completeness check (tracks share-index support through registers,
# blinding only by a mask that occurs nowhere else in the cone's transitive fan-in).
import sys,re,collections
fn=sys.argv[1]
import os
HERE=os.path.dirname(os.path.abspath(__file__))
code=open(os.path.join(HERE,'..','netlist_functional_check.py')).read().split('outs=run()')[0]+'outs=run()\n'
code=code.replace("src=open(sys.argv[1]).read()","src=PRE(open(sys.argv[1]).read())")
def PRE(t):
    t=re.sub(r'\(\*.*?\*\)','',t,flags=re.S)
    t=re.sub(r'^(\s*)(NAND|AND|OR|NOR|NOT|XNOR|XOR)(\s+\S+\s*\()',r'\1\2_\3',t,flags=re.M)
    t=re.sub(r'^(\s*)DFF(\s+\S+\s*\()',r'\1DFF_P_\2',t,flags=re.M)
    return t
sys.argv=['x',fn]; g={'__name__':'x','PRE':None}
g['PRE']=PRE
exec(code,g)
drv=g['drv']; root=g['root']; state=g['state']; outs=g['outs']
sys.setrecursionlimit(200000)
def isconst(n): return n[0]=='c' and isinstance(n[1],int)
fr={}
def F(n):
    n=root(n)
    if isconst(n): return frozenset()
    r=fr.get(n)
    if r is not None: return r
    if n in drv and drv[n][0]!='DFF_P_':
        acc=set()
        for k,v in drv[n][1].items():
            if k!='Y': acc|=F(v)
        r=frozenset(acc)
    else: r=frozenset([n])
    fr[n]=r; return r
def isQ(n): return n in drv and drv[n][0]=='DFF_P_'
def isPI(n): return n not in drv
def Dof(q): return root(drv[q][1]['D'])
Rm={}
def R(n):  # masks in transitive fan-in (through registers)
    if n in Rm: return Rm[n]
    Rm[n]=frozenset()
    if isPI(n): r=frozenset([n]) if n[0]=='randomIn' else frozenset()
    elif isQ(n):
        a=set()
        for e in F(Dof(n)): a|=R(e)
        r=frozenset(a)
    else: r=frozenset()
    Rm[n]=r; return r
def leaves(d):
    out=[]; st=[d]
    while st:
        n=root(st.pop())
        if isconst(n): continue
        if n in drv and drv[n][0] in('XOR_','XNOR_'):
            st+= [drv[n][1]['A'],drv[n][1]['B']]
        elif n in drv and drv[n][0]=='NOT_': st.append(drv[n][1]['A'])
        else: out.append(n)
    return out
import numpy as np
W=8
rng=np.random.default_rng(7)
M64=np.uint64(0xFFFFFFFFFFFFFFFF)
GF={'AND_':lambda a,b:a&b,'NAND_':lambda a,b:~(a&b),'OR_':lambda a,b:a|b,'NOR_':lambda a,b:~(a|b),
    'XOR_':lambda a,b:a^b,'XNOR_':lambda a,b:~(a^b),'ANDNOT_':lambda a,b:a&~b,'ORNOT_':lambda a,b:a|~b}
def evalcone(d,vals):
    memo={}
    def ev(n):
        n=root(n)
        if isconst(n): return np.full(W,M64 if n[1] else 0,dtype=np.uint64)
        if n in vals: return vals[n]
        if n in memo: return memo[n]
        typ,pb=drv[n]
        if typ=='NOT_': r=~ev(pb['A'])
        elif typ=='MUX_':
            a,b,sl=ev(pb['A']),ev(pb['B']),ev(pb['S']); r=(a&~sl)|(b&sl)
        else: r=GF[typ](ev(pb['A']),ev(pb['B']))
        memo[n]=r; return r
    return ev(d)
padm={}
def pad(q):
    if q in padm: return padm[q]
    padm[q]=frozenset()
    d=Dof(q); Fs=sorted(F(d)); best=frozenset()
    cand=[]
    for e in Fs:
        if isPI(e) and e[0]=='randomIn': cand.append((e,frozenset([e])))
        elif isQ(e):
            M=pad(e)
            if M: cand.append((e,M))
    if cand:
        vals={e:rng.integers(0,2**63,W,dtype=np.uint64)*np.uint64(2)+rng.integers(0,2,W,dtype=np.uint64) for e in Fs}
        base=evalcone(d,vals)
        for e,M in cand:
            v2=dict(vals); v2[e]=~vals[e]
            if np.all(evalcone(d,v2)==~base):
                others=set()
                for o in Fs:
                    if o!=e: others|=R(o)
                if not (M & others): best=M; break
    padm[q]=best; return best
def blinded_in(e,Fs):
    p=pad(e)
    if not p: return False
    for o in Fs:
        if o==e: continue
        if p & R(o): return False
    return True
sfull={}
def S(Fs):
    res=set()
    for e in Fs:
        if isPI(e):
            if e[0]=='sboxIn': res.add(0 if e[1]<8 else 1)
        elif isQ(e):
            if blinded_in(e,Fs): continue
            res|=suppfull(e)
    return res
def suppfull(q):
    if q in sfull: return sfull[q]
    sfull[q]=set()
    r=frozenset(S(F(Dof(q)))); sfull[q]=r; return r
cones=[]
for q in state: cones.append((q,Dof(q)))
for o in outs: cones.append((('OUT',)+tuple(o),root(o)))
viol=[]
for nm,d in cones:
    Fs=F(d)
    if len(S(Fs))==2: viol.append((nm,d))
print(fn); print('cones',len(cones),'dffs',len(state),'violating',len(viol),'padded regs',sum(1 for q in state if pad(q)))
grp=collections.Counter()
for nm,d in viol:
    s=nm[0] if isinstance(nm[0],str) else str(nm)
    grp[re.sub(r'[\d_]+','#',s.split('.')[0]) ]+=1
print(grp.most_common(12))
for nm,d in viol[:8]:
    print('  ',nm,'F=',sorted([(e[0],e[1]) for e in F(d)])[:6],'...',len(F(d)))
import pickle
os.makedirs('docs/lint_crosscheck_2026-10-12',exist_ok=True)
pickle.dump([ (nm,d,sorted(F(d))) for nm,d in viol],open('docs/lint_crosscheck_2026-10-12/'+os.path.basename(fn)+'.viol.pkl','wb'))
