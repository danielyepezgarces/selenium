import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BUILD_OUT = Path(r"C:\src\chromium\src\out\thorium")
DIST_DIR = BASE_DIR / "server_release"

SERVER_BASE_URL = "https://update.dyepezg.dev/dl/selenium"

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_exe_version(filepath):
    import win32api
    info = win32api.GetFileVersionInfo(str(filepath), "\\")
    ms = info['FileVersionMS']
    ls = info['FileVersionLS']
    return f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"

def main():
    installer_path = BUILD_OUT / "selenium_AVX2_installer.exe"
    if not installer_path.exists():
        print(f"[ERROR] No se encontro el instalador en: {installer_path}")
        sys.exit(1)

    try:
        version = get_exe_version(installer_path)
    except Exception:
        # Fallback reading VERSION file or string
        version = "157.0.8079.1"

    print(f"=== Generando paquete de actualizacion para Selenium v{version} ===")
    
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    dest_installer = DIST_DIR / "selenium_AVX2_installer.exe"
    print(f"Copiando instalador a {dest_installer}...")
    shutil.copy2(installer_path, dest_installer)
    
    print("Calculando hash SHA-256...")
    sha256 = get_file_sha256(dest_installer)
    size = dest_installer.stat().st_size
    
    manifest = {
        "name": "Selenium Browser",
        "version": version,
        "release_date": "2026-10-02",
        "channel": "stable",
        "download_url": f"{SERVER_BASE_URL}/selenium_AVX2_installer.exe",
        "sha256": sha256,
        "size_bytes": size,
        "notes": f"Selenium Browser version {version} estable.",
        "min_windows_version": "10.0"
    }
    
    manifest_path = DIST_DIR / "version.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print(f"\n[EXITO] Paquete de actualizacion generado en: {DIST_DIR}")
    print(f"Archivos listos para subir a tu servidor ({SERVER_BASE_URL}):")
    print(f"  1. {manifest_path.name}  (Metadatos de version y hash)")
    print(f"  2. {dest_installer.name} ({size / (1024*1024):.1f} MB)")
    print("\nContenido de version.json:")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
