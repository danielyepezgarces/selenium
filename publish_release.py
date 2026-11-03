import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BUILD_OUT = Path(r"C:\src\chromium\src\out\thorium")
DIST_DIR = BASE_DIR / "server_release"

# URL base para el servidor de actualizaciones y descargas
SERVER_BASE_URL = os.environ.get("SELENIUM_RELEASE_URL", "https://update.dyepezg.dev/dl/selenium")
MAX_RELEASES = 5  # Maximo de instaladores historicos a conservar (1 GB aprox.)
CERT_THUMBPRINT = "A935C06DDDB0A3D3D757D3E6535514BD02AF9A41"
SIGNTOOL_PATH = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe"

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_exe_version(filepath):
    version_file = BUILD_OUT.parent.parent / "chrome" / "VERSION"
    if not version_file.exists():
        version_file = BASE_DIR / "src" / "chrome" / "VERSION"
    if version_file.exists():
        vals = {}
        for line in version_file.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip()
        if "MAJOR" in vals and "BUILD" in vals:
            return f"{vals.get('MAJOR','159')}.{vals.get('MINOR','0')}.{vals.get('BUILD','8133')}.{vals.get('PATCH','1')}"
    return "159.0.8133.1"

def parse_version_tuple(v_str):
    try:
        return tuple(int(x) for x in v_str.split("."))
    except Exception:
        return (0, 0, 0, 0)

def sign_file(filepath):
    if not os.path.exists(SIGNTOOL_PATH):
        print(f"[AVISO] signtool.exe no encontrado en {SIGNTOOL_PATH}")
        return False
    print(f"[FIRMA] Firmando con certificado Selenium: {Path(filepath).name}...")
    cmd = [
        SIGNTOOL_PATH,
        "sign",
        "/sha1", CERT_THUMBPRINT,
        "/fd", "SHA256",
        "/tr", "http://timestamp.digicert.com",
        "/td", "SHA256",
        str(filepath)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  [OK] Firmado exitosamente con DigiCert Timestamp.")
        return True
    else:
        print(f"  [ERROR] Error al firmar {filepath}:\n{res.stderr or res.stdout}")
        return False

def main():
    source_installer = BUILD_OUT / "selenium_AVX2_installer.exe"
    if not source_installer.exists():
        source_mini = BUILD_OUT / "mini_installer.exe"
        if source_mini.exists():
            shutil.copy2(source_mini, source_installer)
        else:
            print(f"[ERROR] No se encontro el instalador compilado en: {source_installer}")
            sys.exit(1)

    version = get_exe_version(source_installer)
    release_date = datetime.date.today().isoformat()
    
    print(f"==============================================================================")
    print(f"  PUBLICACIÓN Y FIRMA DE RELEASE: SELENIUM v{version}")
    print(f"  Destino: dl.dyepezg.dev ({SERVER_BASE_URL})")
    print(f"==============================================================================")
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Firmar los binarios fuente principales si existen
    for bin_name in ["selenium.exe", "chrome.dll", "selenium_AVX2_installer.exe"]:
        p = BUILD_OUT / bin_name
        if p.exists():
            sign_file(p)

    # 2. Nombre del instalador con la version explicita
    installer_filename = f"selenium_{version}_AVX2_installer.exe"
    dest_installer = DIST_DIR / installer_filename
    
    print(f"Generando en directorio de distribucion: {dest_installer.name}...")
    shutil.copy2(source_installer, dest_installer)
    
    # Copia generica de compatibilidad (apuntando a la mas reciente)
    generic_installer = DIST_DIR / "selenium_AVX2_installer.exe"
    shutil.copy2(source_installer, generic_installer)
    
    # Asegurar copia en C:\thorium\selenium_AVX2_installer.exe
    shutil.copy2(source_installer, BASE_DIR / "selenium_AVX2_installer.exe")

    # Firmar copias de distribucion
    sign_file(dest_installer)
    sign_file(generic_installer)
    sign_file(BASE_DIR / "selenium_AVX2_installer.exe")
    
    print("Calculando hash SHA-256...")
    sha256 = get_file_sha256(dest_installer)
    size = dest_installer.stat().st_size
    
    # 3. Cargar historial existente de version.json
    manifest_path = DIST_DIR / "version.json"
    existing_releases = []
    
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if "releases" in old_data and isinstance(old_data["releases"], list):
                    existing_releases = old_data["releases"]
                elif "version" in old_data:
                    existing_releases = [{
                        "version": old_data.get("version"),
                        "release_date": old_data.get("release_date", release_date),
                        "filename": f"selenium_{old_data.get('version')}_AVX2_installer.exe",
                        "download_url": old_data.get("download_url"),
                        "sha256": old_data.get("sha256"),
                        "size_bytes": old_data.get("size_bytes"),
                        "notes": old_data.get("notes", "")
                    }]
        except Exception as e:
            print(f"Aviso al leer version.json previo: {e}")

    # 4. Preparar la entrada de la version actual
    current_entry = {
        "version": version,
        "release_date": release_date,
        "filename": installer_filename,
        "download_url": f"{SERVER_BASE_URL}/{installer_filename}",
        "sha256": sha256,
        "size_bytes": size,
        "notes": f"Selenium Browser version {version} estable (Chromium M159, AVX2 + Helium)."
    }
    
    # Actualizar o agregar
    releases_dict = {r["version"]: r for r in existing_releases if "version" in r}
    releases_dict[version] = current_entry
    
    # Ordenar por version semantica descendente
    sorted_releases = sorted(
        releases_dict.values(),
        key=lambda x: parse_version_tuple(x["version"]),
        reverse=True
    )
    
    # Limitar a maximo MAX_RELEASES
    kept_releases = sorted_releases[:MAX_RELEASES]
    pruned_releases = sorted_releases[MAX_RELEASES:]
    
    # 5. Limpieza automatica de instaladores locales antiguos excedentes
    kept_filenames = {r.get("filename") for r in kept_releases}
    kept_filenames.add("selenium_AVX2_installer.exe")
    
    for f in DIST_DIR.glob("selenium_*_installer.exe"):
        if f.name not in kept_filenames:
            print(f"[ROTACION] Eliminando instalador local antiguo ({f.name}) para no superar {MAX_RELEASES} versiones...")
            try:
                f.unlink()
            except Exception as e:
                print(f"  No se pudo eliminar {f.name}: {e}")
                
    # 6. Generar version.json unificado
    latest_rel = kept_releases[0]
    final_manifest = {
        "name": "Selenium Browser",
        "version": latest_rel["version"],
        "release_date": latest_rel["release_date"],
        "channel": "stable",
        "download_url": latest_rel["download_url"],
        "sha256": latest_rel["sha256"],
        "size_bytes": latest_rel["size_bytes"],
        "notes": latest_rel["notes"],
        "max_stored_versions": MAX_RELEASES,
        "latest": latest_rel,
        "releases": kept_releases
    }
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(final_manifest, f, indent=2, ensure_ascii=False)

    # 7. Generar archivo SHA256SUMS.txt
    sha_file = DIST_DIR / "SHA256SUMS.txt"
    with open(sha_file, "w", encoding="utf-8") as f:
        f.write(f"{sha256}  {installer_filename}\n")
        f.write(f"{sha256}  selenium_AVX2_installer.exe\n")
        
    print(f"\n[EXITO] Manifiesto version.json actualizado con historial (Max {MAX_RELEASES} versiones):")
    for idx, r in enumerate(kept_releases, 1):
        print(f"  {idx}. v{r['version']} ({r.get('filename')}) - {r.get('size_bytes', 0) / (1024*1024):.1f} MB [{r.get('release_date')}]")
        
    if pruned_releases:
        print(f"\nVersiones antiguas podadas del catalogo (> {MAX_RELEASES}):")
        for pr in pruned_releases:
            print(f"  - v{pr.get('version')} ({pr.get('filename')}) -> Puedes borrarlo de tu servidor")
            
    print(f"\n==============================================================================")
    print(f"  RELEASE FIRMADO LISTO PARA SUBIR A: dl.dyepezg.dev ({SERVER_BASE_URL})")
    print(f"==============================================================================")
    print(f"Directorio local: {DIST_DIR}")
    print(f"Archivos listos para transferir:")
    print(f"  1. {installer_filename} ({size / (1024*1024):.1f} MB) [Firmado digitalmente]")
    print(f"  2. selenium_AVX2_installer.exe ({size / (1024*1024):.1f} MB) [Firmado digitalmente]")
    print(f"  3. version.json (Metadatos de actualizacion para updater.ps1)")
    print(f"  4. SHA256SUMS.txt (Checksums)")
    print(f"Hash SHA-256: {sha256}")
    print(f"==============================================================================")

if __name__ == "__main__":
    main()
