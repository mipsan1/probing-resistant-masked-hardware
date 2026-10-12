from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "manuscript" / "manuscript.tex"
data = TEX.read_bytes()

# Just delete "comprises\r\nreports" leaving "(\\texttt{...}) " + qualifier start.
# The qualifier begins with "reports" — no, actually I designed the qualifier to
# start with "reports" so the line should read "...}) reports $25,536...".
# So we keep "(\\texttt{...}) " and delete "comprises\r\nreports". Actually we
# need to replace "comprises" with nothing AND delete the next "reports" line.
# Simpler: replace "comprises\r\nreports" with "" — this gives "...}) reports"
# on a single line (since "reports" was on the next line, deleting the \r\n
# joins them).
OLD = b"comprises\r\nreports"
NEW = b""
print(f"OLD: {OLD!r}, len={len(OLD)}, occurrences={data.count(OLD)}")
if data.count(OLD) != 1:
    raise SystemExit("Expected exactly 1")
new_data = data.replace(OLD, NEW, 1)
TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")