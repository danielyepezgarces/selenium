import os
from pathlib import Path

thorium_root = Path(r"C:\thorium")
series_path = thorium_root / "patch_scripts" / "series" / "series"
overlay_dir = thorium_root / "src"

overlay_files = set()
for f in overlay_dir.rglob("*"):
    if f.is_file():
        rel = f.relative_to(overlay_dir).as_posix()
        overlay_files.add(rel)

print(f"Total overlay files in src/: {len(overlay_files)}")

# Check each patch in series for files that match overlay_files
with open(series_path, "r", encoding="utf-8") as sf:
    lines = sf.readlines()

collisions = []
for line in lines:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    patch_file = line.split()[-1]
    patch_path = thorium_root / patch_file
    if not patch_path.is_file():
        continue
    with open(patch_path, "r", encoding="utf-8", errors="ignore") as pf:
        for pline in pf:
            if pline.startswith("--- a/") or pline.startswith("+++ b/"):
                filepath = pline[6:].strip()
                if filepath in overlay_files:
                    collisions.append((patch_file, filepath))

print(f"Found {len(collisions)} collisions between series patches and src/ overlay:")
for c in collisions:
    print(f"  Patch: {c[0]} touches overlay file: {c[1]}")
