# Convert a hierarchical Yosys write_json netlist ($_gate_ cells) to the flat gate-level Verilog dialect read by cone_lint_def.py / cone_stat_check.py.
# usage: python3 json2v.py netlist.json out.v <top-module>   (rst_n/valid_in tied to 1, DFF enable/reset ignored)
# Yosys write_json (hierarchical, $_gate_ cells) -> flat gate-level Verilog in the dialect used by tools/netlist_functional_check.py
import json,sys
js=json.load(open(sys.argv[1]))['modules']; TOP=sys.argv[3]
parent={}
def find(k):
    parent.setdefault(k,k); r=k
    while parent[r]!=r: r=parent[r]
    while parent[k]!=r: parent[k],k=r,parent[k]
    return r
def union(a,b):
    ra,rb=find(a),find(b)
    if ra!=rb: parent[rb]=ra
cells=[]  # (type, {port: key or const})
def key(ns,b): return b if isinstance(b,str) else (ns,b)
def proc(mn,ns,bind):
    m=js[mn]
    if bind:
        for p,info in m['ports'].items():
            for i,b in enumerate(info['bits']):
                if not isinstance(b,str): union(bind[p][i],(ns,b))
    for cn,c in m['cells'].items():
        t=c['type']; con=c['connections']
        if t in js:
            sb={p:[key(ns,b) for b in con[p]] for p in js[t]['ports']}
            proc(t,ns+'/'+cn,sb)
        else: cells.append((t,{p:[key(ns,b) for b in bits] for p,bits in con.items()}))
proc(TOP,'',None)
# top port mapping
top=js[TOP]['ports']
name={}
CONST1={'rst_n','valid_in'}
def setn(p,i,nm):
    b=top[p]['bits'][i]; name[find(('',b))]=nm
for i in range(8):
    setn('x0_in',i,f'sboxIn[{i}]'); setn('x1_in',i,f'sboxIn[{8+i}]')
    setn('y0_out',i,f'sboxOut[{i}]'); setn('y1_out',i,f'sboxOut[{8+i}]')
    for k in range(7): setn(f'r{k}_in',i,f'randomIn[{8*k+i}]')
setn('clk',0,'clk')
const1={find(('',top[p]['bits'][0])) for p in CONST1}
def nm(k):
    if isinstance(k,str): return {'0':"1'b0",'1':"1'b1"}.get(k,"1'b0")
    r=find(k)
    if r in const1: return "1'b1"
    if r not in name: name[r]='n%d'%len(name)
    return name[r]
out=[];wires=set()
MAP={'$_AND_':'AND_','$_NAND_':'NAND_','$_OR_':'OR_','$_NOR_':'NOR_','$_XOR_':'XOR_','$_XNOR_':'XNOR_','$_ANDNOT_':'ANDNOT_','$_ORNOT_':'ORNOT_','$_NOT_':'NOT_','$_MUX_':'MUX_','$_DFF_PN0_':'DFF_P_','$_DFFE_PN0P_':'DFF_P_'}
body=[]
for i,(t,p) in enumerate(cells):
    ty=MAP[t]; ports=[]
    for pn in ('A','B','S','D','C','Q','Y'):
        if pn in p and not (ty=='DFF_P_' and pn in()): 
            if ty=='DFF_P_' and pn not in('D','C','Q'): continue
            ports.append(f'.{pn}({nm(p[pn][0])})')
    body.append(f'  {ty} c{i} ({", ".join(ports)});')
for line in body:
    for w in __import__('re').findall(r'\((n\d+)\)',line): wires.add(w)
o=['module circuit(clk, sboxIn, randomIn, sboxOut);','  input clk;','  input [15:0] sboxIn;','  input [55:0] randomIn;','  output [15:0] sboxOut;']
o+=[f'  wire {w};' for w in sorted(wires)]
o+=body+['endmodule']
open(sys.argv[2],'w').write('\n'.join(o)+'\n')
print('cells',len(cells),'wires',len(wires))
