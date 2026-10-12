from pathlib import Path
import re
data = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead\circuit_v9.v").read_text(errors="replace")
# backslash followed by \$_
# Python regex: to match a literal backslash, use \\
# To match literal $ in raw string, use $
# To match literal _, use _
# So: \\\$\w+ in raw string = match backslash + $ + word
# Wait, raw string r'\\$\w+' = literal \\ + $\w+ = backslash + dollar + word
# But file has: \ + $ + _ + word  (i.e. backslash then dollar then underscore)
# So r'\$\w+' is wrong (3 chars: \\$\w+ = backslash + dollar + word, missing _)
# Need: backslash + $ + _ + word = r'\\$_\w+' but in JSON escape that's '\\\\$_\\w+'

# Let me just do byte-level search
n_bslash = data.count("\\$")
n_dollar = data.count("$")
n_underscore = data.count("_")
print(f"backslash-dollar: {n_bslash}, dollar: {n_dollar}, underscore: {n_underscore}")

# Find context of $_
idx = data.find("$_")
print(f"$_ at index: {idx}")
if idx >= 0:
    print(f"context: {data[max(0,idx-5):idx+15]!r}")

# Find context of \$_
idx = data.find("\\$_")
print(f"\\$_ at index: {idx}")
if idx >= 0:
    print(f"context: {data[max(0,idx-5):idx+15]!r}")
    # also dump raw bytes
    print(f"raw bytes: {data[max(0,idx-5):idx+15].encode('utf-8')!r}")

# Match pattern
matches = re.findall(r"\\\$_\w+", data)
print(f"\\$_ pattern matches: {len(matches)}")
matches2 = re.findall(r"\\\$_\w+", data)
print(f"escaped pattern matches: {len(matches2)}")