from pathlib import Path
p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
data = Path(p).read_bytes()
idx = data.find(b"comprises")
start = data.rfind(b"(", 0, idx)
print(f"start={start}, idx={idx}")
print(f"data[start:idx] = {data[start:idx]!r}")
print(f"len = {idx - start}")
# The issue: data[start:idx] ends with 'comprises', not ')'. Need to find end of ')'
end_paren = data.find(b")", idx)
print(f"end_paren at {end_paren}")
OLD = data[start:end_paren+1] + b"\r\nreports"
print(f"OLD = {OLD!r}, len = {len(OLD)}")
print(f"occurrences = {data.count(OLD)}")