import re
# Test string with literal backslash-dollar-underscore
test = "test \\_$_NOT_ foo \\_$_XNOR_ bar"
print(f"test: {test!r}")
# regex
m = re.findall(r"\$_(\w+)", test)
print(f"matches: {m}")