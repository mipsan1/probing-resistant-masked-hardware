#!/usr/bin/env python3
"""cone_stat_check.py -- statistical check of every register-input / output cone (added 2026-10-12).

For each DFF D-input cone and each output bit, the glitch-extended probe observes the stable frontier
(primary inputs and register outputs feeding the cone).  The script simulates the flat gate-level netlist
bit-parallel (steady state, inputs held constant, fresh shares/masks every sample) for two fixed secrets
(0x00 and 0xA7) and runs a G-test between the two joint distributions of the frontier values.
A cone is "leaking" if -log10(p) exceeds the Bonferroni threshold over all cones.
Usage (bundle root): python3 tools/lint/cone_stat_check.py <netlist.v> <random-bytes> [words]
  e.g. synth/prolead/circuit_v9_xform2.v 7      synth/prolead_d1_candidate_attr.v 6
Needs numpy.  The cone enumeration is shared with cone_lint_def.py.
"""
import sys,os,re,math,pickle,collections,numpy as np
fn=sys.argv[1]; NB=int(sys.argv[2]); W=int(sys.argv[3]) if len(sys.argv)>3 else 2048
HERE=os.path.dirname(os.path.abspath(__file__))
LD=os.path.join(HERE,'cone_lint_def.py')
code=open(LD).read().split('cones=[]')[0]
sys.argv=[LD,fn]
L={'__name__':'x','__file__':LD}
exec(code,L)
drv,root,state,outs,F,Dof,isconst=[L[k] for k in('drv','root','state','outs','F','Dof','isconst')]
order=L['g']['order']
cones=[(q,Dof(q)) for q in state]+[(('OUT',)+tuple(o),root(o)) for o in outs]
M64=np.uint64(0xFFFFFFFFFFFFFFFF)
GF=L['GF']
def simulate(secret,seed):
    rng=np.random.default_rng(seed)
    V={}
    def rnd(): return rng.integers(0,2**63,W,dtype=np.uint64)*np.uint64(2)+rng.integers(0,2,W,dtype=np.uint64)
    for i in range(8):
        a=rnd(); V[('sboxIn',i)]=a; V[('sboxIn',8+i)]=a^(M64 if (secret>>i)&1 else np.uint64(0))
    for i in range(NB*8): V[('randomIn',i)]=rnd()
    V[('clk',0)]=np.zeros(W,np.uint64)
    for q in state: V[q]=np.zeros(W,np.uint64)
    zero=np.zeros(W,np.uint64); one=np.full(W,M64,np.uint64)
    def gv(n):
        n=root(n)
        if isconst(n): return one if n[1] else zero
        return V.get(n,zero)
    def comb():
        for n in order:
            typ,pb=drv[n]
            if typ=='NOT_': V[n]=~gv(pb['A'])
            elif typ=='MUX_':
                a,b,s=gv(pb['A']),gv(pb['B']),gv(pb['S']); V[n]=(a&~s)|(b&s)
            else: V[n]=GF[typ](gv(pb['A']),gv(pb['B']))
    for cyc in range(26):
        comb()
        nq={q:gv(drv[q][1]['D']).copy() for q in state}
        V.update(nq)
    comb()
    keys=[]
    for nm,d in cones:
        Fs=sorted(F(d))[:32]; k=np.zeros(W*64,np.uint32)
        for i,e in enumerate(Fs):
            bits=np.unpackbits(gv(e).view(np.uint8),bitorder='little')
            k|=(bits.astype(np.uint32)<<np.uint32(i))
        keys.append(k)
    return keys,V,gv
def nlog10p(G,df):
    if df<=0: return 0.0
    z=((G/df)**(1/3)-(1-2/(9*df)))/math.sqrt(2/(9*df))
    if z<=0: return 0.0
    if z<30: return -math.log10(max(0.5*math.erfc(z/math.sqrt(2)),1e-300))
    return (z*z/2+math.log(z*math.sqrt(2*math.pi)))/math.log(10)
SA,SB=0x00,0xA7
kA,VA,gvA=simulate(SA,1)
# functional sanity from the same run
def sbox(x):
    def gm(a,b):
        r=0
        while b:
            if b&1: r^=a
            a<<=1
            if a&0x100: a^=0x11b
            b>>=1
        return r
    inv=0
    if x:
        for c in range(1,256):
            if gm(x,c)==1: inv=c
    s=inv
    for k in range(1,5): s^=((inv<<k)|(inv>>(8-k)))&0xff
    return s^0x63
def shares(gv,s):
    o=np.zeros(W*64,np.int64)
    for i in range(8):
        b0=np.unpackbits(gv(('sboxOut',i)).view(np.uint8),bitorder='little').astype(np.int64)
        b1=np.unpackbits(gv(('sboxOut',8+i)).view(np.uint8),bitorder='little').astype(np.int64)
        o|=((b0^b1)<<i)
    return o
okA=float(np.mean(shares(gvA,SA)==sbox(SA)))
del VA
kB,VB,gvB=simulate(SB,2)
okB=float(np.mean(shares(gvB,SB)==sbox(SB)))
res=[]
for (nm,d),a,b in zip(cones,kA,kB):
    ua,ca=np.unique(a,return_counts=True); ub,cb=np.unique(b,return_counts=True)
    allk=np.union1d(ua,ub)
    oa=np.zeros(len(allk)); ob=np.zeros(len(allk))
    oa[np.searchsorted(allk,ua)]=ca; ob[np.searchsorted(allk,ub)]=cb
    tot=oa+ob; keep=tot>=10
    # pool rare bins
    rare_a=oa[~keep].sum(); rare_b=ob[~keep].sum()
    Oa=list(oa[keep]); Ob=list(ob[keep])
    if rare_a+rare_b>=10: Oa.append(rare_a); Ob.append(rare_b)
    Oa=np.array(Oa); Ob=np.array(Ob); E=(Oa+Ob)/2
    with np.errstate(divide='ignore',invalid='ignore'):
        G=2*(np.where(Oa>0,Oa*np.log(Oa/E),0).sum()+np.where(Ob>0,Ob*np.log(Ob/E),0).sum())
    df=len(Oa)-1
    res.append((nm,len(F(d)),df,float(G),nlog10p(G,df)))
od='docs/lint_crosscheck_2026-10-12'; os.makedirs(od,exist_ok=True); bn=os.path.basename(fn)
pickle.dump(res,open(od+'/'+bn+'.gtest.pkl','wb'))
thr=-math.log10(0.05/len(res))
leak=[r for r in res if r[4]>thr]
print(fn,'cones',len(res),'samples/group',W*64,'Bonferroni -log10p',round(thr,2))
print('leaking cones',len(leak),'worst -log10p',round(max(r[4] for r in res),2))
print('nonleaking worst',round(max([r[4] for r in res if r[4]<=thr] or [0]),2))
print('functional sanity: fraction y0^y1==AES_Sbox(x):',okA,okB)
for r in sorted(leak,key=lambda r:-r[4])[:20]: print('  LEAK cone',r[0],'|F|',r[1],'df',r[2],'-log10p',round(r[4],1))
