import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, r"C:\src\chromium\src\tools\grit")
from grit.extern import tclib

SRC_ROOT = Path(r"C:\src\chromium\src")

grd_files = [
    "chrome/app/chromium_strings.grd",
    "components/components_chromium_strings.grd",
    "chrome/app/generated_resources.grd",
    "chrome/app/settings_chromium_strings.grdp",
    "chrome/app/app_management_strings.grdp",
]

id_mapping = {} # thor_id -> sel_id

def clean_text_for_id(elem):
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        if child.tag == 'ph':
            name = child.attrib.get('name', '').upper()
            parts.append(name)
        else:
            parts.append(clean_text_for_id(child))
        if child.tail:
            parts.append(child.tail)
    raw = "".join(parts)
    return raw.strip()

def run_fix():
    print("--- Paso 1: Extrayendo mapeo de IDs de traduccion desde archivos GRD ---")
    for rel in grd_files:
        p = SRC_ROOT / rel
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8")
        pattern = re.compile(r'<message\s+([^>]*?)>(.*?)</message>', re.DOTALL)
        for m in pattern.finditer(content):
            attrs = m.group(1)
            body = m.group(2)
            
            meaning_m = re.search(r'meaning="([^"]*)"', attrs)
            meaning = meaning_m.group(1) if meaning_m else ''
            
            if "Selenium" not in body:
                continue
                
            try:
                wrapped = f"<root>{body}</root>"
                root = ET.fromstring(wrapped)
                sel_text = clean_text_for_id(root)
            except Exception:
                sel_text = re.sub(r'<ph[^>]*name="([^"]*)"[^>]*>.*?</ph>', r'\1', body, flags=re.DOTALL)
                sel_text = re.sub(r'<[^>]+>', '', sel_text).strip()
            
            thor_text = sel_text.replace("SeleniumOS", "ThoriumOS").replace("Selenium", "Thorium")
            
            if sel_text != thor_text:
                sel_id = tclib.GenerateMessageId(sel_text, meaning)
                thor_id = tclib.GenerateMessageId(thor_text, meaning)
                id_mapping[thor_id] = sel_id

    print(f"Total IDs a mapear: {len(id_mapping)}")

    print("\n--- Paso 2: Inyectando IDs de Selenium en todos los catalogos de traduccion XTB ---")
    xtb_dirs = [
        SRC_ROOT / "chrome" / "app" / "resources",
        SRC_ROOT / "components" / "strings",
    ]

    total_files_updated = 0
    total_translations_added = 0

    trans_pattern = re.compile(r'(<translation\s+id="(\d+)"[^>]*>.*?</translation>)', re.DOTALL)

    for d in xtb_dirs:
        if not d.exists():
            continue
        for xtb_file in d.glob("*.xtb"):
            content = xtb_file.read_text(encoding="utf-8")
            original = content
            
            # Funcion de reemplazo para duplicar / inyectar el nuevo ID de Selenium
            def replacer(match):
                nonlocal total_translations_added
                full_tag = match.group(1)
                tid = match.group(2)
                if tid in id_mapping:
                    sid = id_mapping[tid]
                    if f'id="{sid}"' not in content:
                        total_translations_added += 1
                        # Crear version con el id de Selenium
                        sel_tag = full_tag.replace(f'id="{tid}"', f'id="{sid}"', 1)
                        # Devolver ambos para preservar compatibilidad
                        return full_tag + "\n" + sel_tag
                return full_tag
                
            new_content = trans_pattern.sub(replacer, content)
            if new_content != original:
                xtb_file.write_text(new_content, encoding="utf-8")
                total_files_updated += 1
                if "es" in xtb_file.stem:
                    print(f"  Actualizado archivo en espanol: {xtb_file.name}")

    print(f"\n[EXITO] Archivos XTB actualizados: {total_files_updated}")
    print(f"[EXITO] Nuevas traducciones con IDs de Selenium inyectadas: {total_translations_added}")

if __name__ == "__main__":
    run_fix()
