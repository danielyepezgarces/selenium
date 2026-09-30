import os
import re

pattern = re.compile(r'("thorium"|"thorium://"|kThoriumUIScheme)', re.IGNORECASE)
found = []

for root, _, files in os.walk(r"C:\src\chromium\src"):
    if "third_party" in root and "blink" not in root:
        continue
    if "out" in root:
        continue
    for f in files:
        if f.endswith((".cc", ".h", ".mm", ".js", ".ts")):
            p = os.path.join(root, f)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    matches = pattern.findall(content)
                    if matches:
                        print(f"{p} -> matches: {len(matches)}")
            except:
                pass
