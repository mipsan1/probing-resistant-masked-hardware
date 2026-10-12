import re, sys, threading, numpy as np
sys.setrecursionlimit(10**7)
src=open(sys.argv[1]).read()
src=re.sub(r'/\*.*?\*/','',src,flags=re.S); src=re.sub(r'//[^\n]*','',src)
tok=re.findall(r"\\\S+|[A-Za-z_][\w$]*|\d+'[hbdHBD][0-9a-fA-FxXzZ_]+|\d+|[\[\](){},;.:=#]",src)
class P:
    def __init__(s,t): s.t=t; s.i=0
    def peek(s): return s.t[s.i] if s.i<len(s.t) else None
    def nxt(s): x=s.t[s.i]; s.i+=1; return x
    def exp(s,x):
        y=s.nxt(); assert y==x,(x,y,s.t[s.i-5:s.i+5])
def norm(n): return n[1:] if n.startswith('\\') else n
def parse_expr(p):
    if p.peek()=='{':
        p.nxt(); parts=[parse_expr(p)]
        while p.peek()==',': p.nxt(); parts.append(parse_expr(p))
        p.exp('}'); return ('cat',parts)
    t=p.nxt()
    if "'" in t:
        w,r=t.split("'"); base=r[0].lower(); v=r[1:].replace('_','')
        val=int(v,{'h':16,'b':2,'d':10}[base]); return ('const',int(w),val)
    if re.fullmatch(r'\d+',t): return ('const',32,int(t))
    name=norm(t); sel=None
    if p.peek()=='[':
        p.nxt(); a=int(p.nxt()); b=a
        if p.peek()==':': p.nxt(); b=int(p.nxt())
        p.exp(']'); sel=(a,b)
    return ('id',name,sel)
mods={}
p=P(tok)
while p.peek() is not None:
    p.exp('module'); mname=p.nxt(); p.exp('(')
    while p.nxt()!=')': pass
    p.exp(';')
    m={'decl':{}, 'dir':{}, 'assign':[], 'inst':[]}
    while p.peek()!='endmodule':
        t=p.nxt()
        if t in ('input','output','wire','reg'):
            hi=lo=0
            if p.peek()=='[':
                p.nxt(); hi=int(p.nxt()); p.exp(':'); lo=int(p.nxt()); p.exp(']')
            while True:
                n=norm(p.nxt()); m['decl'][n]=(hi,lo)
                if t in('input','output'): m['dir'][n]=t
                if p.peek()==',': p.nxt(); continue
                break
            p.exp(';')
        elif t=='assign':
            l=parse_expr(p); p.exp('='); r=parse_expr(p); p.exp(';'); m['assign'].append((l,r))
        else:
            typ=t; iname=norm(p.nxt()); p.exp('('); ports={}
            while p.peek()!=')':
                p.exp('.'); pn=p.nxt(); p.exp('('); ports[pn]=parse_expr(p); p.exp(')')
                if p.peek()==',': p.nxt()
            p.exp(')'); p.exp(';'); m['inst'].append((typ,iname,ports))
    p.nxt(); mods[mname]=m
CELLS={'AND_','NAND_','OR_','NOR_','XOR_','XNOR_','ANDNOT_','ORNOT_','NOT_','MUX_','DFF_P_'}
def bits(e,mod,prefix):
    k=e[0]
    if k=='cat':
        out=[]
        for q in e[1]: out+=bits(q,mod,prefix)
        return out
    if k=='const': return [('c',(e[2]>>i)&1) for i in range(e[1]-1,-1,-1)]
    _,name,sel=e; hi,lo=mod['decl'][name]
    if sel is None: a,b=hi,lo
    else: a,b=sel
    step=-1 if a>=b else 1
    return [(prefix+name,i) for i in range(a,b+step,step)]
alias={}; drv={}; inputs=[]
def elab(mname,prefix,binds):
    m=mods[mname]
    for l,r in m['assign']:
        lb=bits(l,m,prefix); rb=bits(r,m,prefix); assert len(lb)==len(rb),(l,r)
        for x,y in zip(lb,rb): alias[x]=y
    for typ,iname,ports in m['inst']:
        if typ in CELLS:
            pb={k:bits(v,m,prefix)[0] for k,v in ports.items()}
            outn=pb['Q'] if typ=='DFF_P_' else pb['Y']
            drv[outn]=(typ,pb)
        else:
            sub=mods[typ]; sp=prefix+iname+'.'
            for pn,e in ports.items():
                eb=bits(e,m,prefix); hi,lo=sub['decl'][pn]
                sb=[(sp+pn,i) for i in range(hi,lo-1,-1)] if hi>=lo else [(sp+pn,i) for i in range(hi,lo+1)]
                assert len(eb)==len(sb),(typ,pn,len(eb),len(sb))
                for x,y in zip(eb,sb):
                    if sub['dir'][pn]=='input': alias[y]=x
                    else: alias[x]=y
            elab(typ,sp,None)
elab('circuit','',None)
top=mods['circuit']
def root(n):
    seen=0
    while n in alias:
        n=alias[n]; seen+=1; assert seen<100000
    return n
undriven=set()
order=[]; state=set(); visited={}
def visit(n):
    n=root(n)
    if n[0]=='c' and isinstance(n[1],int) and n[0]=='c': return n
    if n in visited: return n
    if n in drv:
        typ,pb=drv[n]
        if typ=='DFF_P_': visited[n]='dff'; state.add(n); return n
        visited[n]='tmp'
        for k,v in pb.items():
            if k!='Y': visit(v)
        visited[n]='done'; order.append(n); return n
    visited[n]='in'; return n
def run():
    outs=[('sboxOut',i) for i in range(15,-1,-1)]
    for o in outs: visit(o)
    # DFF D inputs
    todo=list(state)
    seen_dff=set()
    while todo:
        q=todo.pop()
        if q in seen_dff: continue
        seen_dff.add(q); visit(drv[q][1]['D'])
        for s in list(state):
            if s not in seen_dff: todo.append(s)
    return outs
outs=run()
# primary inputs / undriven
pi=[n for n,v in visited.items() if v=='in']
prim={n for n in pi if n[0] in ('sboxIn','randomIn','clk')}
und=[n for n in pi if n not in prim]
print('cells in comb order',len(order),'dffs',len(state),'primary used',len(prim),'UNDRIVEN nets',len(und))
for u in und[:20]: print('  undriven:',u)
# numpy sim
SB=[0]*256
def gm(a,b):
    r=0
    while b:
        if b&1: r^=a
        a<<=1
        if a&0x100: a^=0x11b
        b>>=1
    return r
inv=[0]*256
for a in range(1,256):
    for b in range(1,256):
        if gm(a,b)==1: inv[a]=b
for x in range(256):
    b=inv[x]; s=b
    for k in range(1,5): s^=((b<<k)|(b>>(8-k)))&0xff
    SB[x]=s^0x63
assert SB[0]==0x63 and SB[1]==0x7c
MASKS=int(sys.argv[2]) if len(sys.argv)>2 else 4
B=256*MASKS
rng=np.random.default_rng(1)
sec=np.repeat(np.arange(256),MASKS)
x0=rng.integers(0,256,B); x1=x0^sec
rnd=rng.integers(0,256,(B,7))
idx={n:i for i,n in enumerate(list(visited.keys()))}
V={}
def getv(n):
    n=root(n)
    if n[0]=='c': return np.full(B,n[1],np.uint8)
    return V.get(n, np.zeros(B,np.uint8))
for i in range(8):
    V[('sboxIn',i)]=((x0>>i)&1).astype(np.uint8); V[('sboxIn',8+i)]=((x1>>i)&1).astype(np.uint8)
for byte in range(7):
    for i in range(8): V[('randomIn',byte*8+i)]=((rnd[:,byte]>>i)&1).astype(np.uint8)
V[('clk',0)]=np.zeros(B,np.uint8)
for q in state: V[q]=np.zeros(B,np.uint8)
F={'AND_':lambda a,b:a&b,'NAND_':lambda a,b:1-(a&b),'OR_':lambda a,b:a|b,'NOR_':lambda a,b:1-(a|b),'XOR_':lambda a,b:a^b,'XNOR_':lambda a,b:1-(a^b),'ANDNOT_':lambda a,b:a&(1-b),'ORNOT_':lambda a,b:a|(1-b)}
def comb():
    for n in order:
        typ,pb=drv[n]
        if typ=='NOT_': V[n]=1-getv(pb['A'])
        elif typ=='MUX_':
            a,b,s=getv(pb['A']),getv(pb['B']),getv(pb['S']); V[n]=np.where(s==1,b,a).astype(np.uint8)
        else: V[n]=F[typ](getv(pb['A']),getv(pb['B'])).astype(np.uint8)
res=[]
for cyc in range(24):
    comb()
    y=np.zeros(B,int)
    for k,o in enumerate(outs): pass
    y0=np.zeros(B,int); y1=np.zeros(B,int)
    for i in range(8):
        y0|=getv(('sboxOut',i)).astype(int)<<i; y1|=getv(('sboxOut',8+i)).astype(int)<<i
    ok=((y0^y1)==np.array([SB[s] for s in sec])).mean()
    res.append(round(float(ok),4))
    newq={q:getv(drv[q][1]['D']).copy() for q in state}
    for q,v in newq.items(): V[q]=v
print('fraction of (secret,mask) cases with y0^y1 == AES_Sbox(x), by cycle:')
print(res)
