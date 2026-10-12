import json
data = json.load(open(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\tools\prolead-modeB\design\netlist.json"))
mod = data["modules"]["circuit"]
print("Ports:")
for p, info in mod["ports"].items():
    d = info["direction"]
    n = len(info["bits"])
    print(f"  {p}: dir={d} bits={n}")