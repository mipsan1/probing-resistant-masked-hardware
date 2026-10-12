import re
test = r"test \$_NOT_ foo \$_XNOR_ bar \$_AND_"
print(f"original: {test!r}")
xform = re.sub(r"\$_(\w+)", r"\1", test)
print(f"xform: {xform!r}")