#!/usr/bin/env python3
"""
sync_src_to_thorium.py
Sincroniza los cambios realizados en el árbol de compilación (C:\src\chromium\src)
de vuelta al repositorio de origen (C:\thorium) para que nunca se pierda nada.
"""

import filecmp
import os
import shutil
import sys
from pathlib import Path

THORIUM_ROOT = Path("C:/thorium").resolve()
CHROMIUM_SRC = Path("C:/src/chromium/src").resolve()

def sync_overlays():
    print("=" * 70)
    print(" [SYNC] Sincronizando Overlays desde Chromium SRC hacia Thorium...")
    print("=" * 70)
    
    thorium_src = THORIUM_ROOT / "src"
    if not thorium_src.exists():
        print(f"No existe el directorio de overlays: {thorium_src}")
        return

    synced_count = 0
    identical_count = 0

    for root, _, files in os.walk(thorium_src):
        for file in files:
            t_file = Path(root) / file
            rel_path = t_file.relative_to(thorium_src)
            c_file = CHROMIUM_SRC / rel_path

            if not c_file.exists():
                continue

            # Comparar si hay diferencias
            if not filecmp.cmp(str(t_file), str(c_file), shallow=False):
                print(f" [ACTUALIZADO] {rel_path}")
                shutil.copy2(str(c_file), str(t_file))
                synced_count += 1
            else:
                identical_count += 1

    print("-" * 70)
    print(f" [RESULTADO] Archivos actualizados en Thorium: {synced_count}")
    print(f"             Archivos ya identicos:           {identical_count}")
    print("=" * 70)

if __name__ == "__main__":
    sync_overlays()
