import datetime
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
MAX_RELEASES = 5  # Maximo de instaladores historicos a conservar (1 GB aprox.)

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
            return f"{vals.get('MAJOR','157')}.{vals.get('MINOR','0')}.{vals.get('BUILD','8079')}.{vals.get('PATCH','2')}"
    return "157.0.8079.2"

def parse_version_tuple(v_str):
    try:
        return tuple(int(x) for x in v_str.split("."))
    except Exception:
        return (0, 0, 0, 0)

def main():
    source_installer = BUILD_OUT / "selenium_AVX2_installer.exe"
    if not source_installer.exists():
        print(f"[ERROR] No se encontro el instalador compilado en: {source_installer}")
        sys.exit(1)

    version = get_exe_version(source_installer)
    release_date = datetime.date.today().isoformat()
    
    print(f"=== Publicando Selenium v{version} en paquete de actualizacion ===")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Nombre del instalador con la version explicita
    installer_filename = f"selenium_{version}_AVX2_installer.exe"
    dest_installer = DIST_DIR / installer_filename
    
    print(f"Generando: {dest_installer}...")
    shutil.copy2(source_installer, dest_installer)
    
    # Copia generica de compatibilidad (apuntando a la mas reciente)
    shutil.copy2(source_installer, DIST_DIR / "selenium_AVX2_installer.exe")
    
    print("Calculando hash SHA-256...")
    sha256 = get_file_sha256(dest_installer)
    size = dest_installer.stat().st_size
    
    # 2. Cargar historial existente de version.json
    manifest_path = DIST_DIR / "version.json"
    existing_releases = []
    
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if "releases" in old_data and isinstance(old_data["releases"], list):
                    existing_releases = old_data["releases"]
                elif "version" in old_data:
                    # Migrar formato anterior de version unica
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

    # 3. Preparar la entrada de la version actual
    current_entry = {
        "version": version,
        "release_date": release_date,
        "filename": installer_filename,
        "download_url": f"{SERVER_BASE_URL}/{installer_filename}",
        "sha256": sha256,
        "size_bytes": size,
        "notes": f"Selenium Browser version {version} estable."
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
    
    # Limitar a maximo MAX_RELEASES (las 4 o 5 mas recientes)
    kept_releases = sorted_releases[:MAX_RELEASES]
    pruned_releases = sorted_releases[MAX_RELEASES:]
    
    # 4. Limpieza automatica de instaladores locales antiguos excedentes
    kept_filenames = {r.get("filename") for r in kept_releases}
    kept_filenames.add("selenium_AVX2_installer.exe")
    
    for f in DIST_DIR.glob("selenium_*_installer.exe"):
        if f.name not in kept_filenames:
            print(f"[ROTACION] Eliminando instalador local antiguo ({f.name}) para no superar {MAX_RELEASES} versiones...")
            try:
                f.unlink()
            except Exception as e:
                print(f"  No se pudo eliminar {f.name}: {e}")
                
    # 5. Generar version.json unificado
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
        
    print(f"\n[EXITO] Manifiesto version.json actualizado con historial (Max {MAX_RELEASES} versiones):")
    for idx, r in enumerate(kept_releases, 1):
        print(f"  {idx}. v{r['version']} ({r.get('filename')}) - {r.get('size_bytes', 0) / (1024*1024):.1f} MB [{r.get('release_date')}]")
        
    if pruned_releases:
        print(f"\nVersiones antiguas podadas del catalogo (> {MAX_RELEASES}):")
        for pr in pruned_releases:
            print(f"  - v{pr.get('version')} ({pr.get('filename')}) -> Puedes borrarlo de tu servidor")
            
    print(f"\nArchivos a subir a tu servidor ({SERVER_BASE_URL}):")
    print(f"  -> {manifest_path.name}")
    print(f"  -> {installer_filename}")

if __name__ == "__main__":
    main()
