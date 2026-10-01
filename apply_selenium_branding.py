import os
import re
from pathlib import Path

src_root = Path(r"C:\src\chromium\src")

# 1. Target GRD and GRDP files
grd_files = [
    "chrome/app/app_management_strings.grdp",
    "chrome/app/chromium_strings.grd",
    "chrome/app/extensions_strings.grdp",
    "chrome/app/generated_resources.grd",
    "chrome/app/settings_chromium_strings.grdp",
    "chrome/app/settings_strings.grdp",
    "chrome/app/shared_settings_strings.grdp",
    "chrome/app/theme/theme_resources.grd",
    "components/autofill_payments_strings.grdp",
    "components/autofill_strings.grdp",
    "components/components_chromium_strings.grd",
    "components/error_page_strings.grdp",
    "components/flags_strings.grdp",
    "components/heavy_ad_intervention_strings.grdp",
    "components/management_strings.grdp",
    "components/new_or_sad_tab_strings.grdp",
    "components/page_info_strings.grdp",
    "components/reset_password_strings.grdp",
    "components/security_interstitials_strings.grdp",
    "components/ssl_errors_strings.grdp",
    "components/version_ui_strings.grdp",
]

# 2. WebUI and installer files
extra_files = [
    "components/webui/version/resources/about_version.html",
    "components/webui/flags/resources/app.html.ts",
    "chrome/installer/launcher_support/chrome_launcher_support.cc",
    "chrome/app/theme/chromium/BRANDING",
]

total_replaced_files = 0
total_replacements = 0

print("--- Processing GRD/GRDP and WebUI files ---")
for rel in grd_files + extra_files:
    p = src_root / rel
    if not p.exists():
        print(f"Skipping missing: {rel}")
        continue
    content = p.read_text(encoding="utf-8", errors="ignore")
    original = content
    
    # Preserve specific C++ message IDs if in generated_resources.grd
    if rel == "chrome/app/generated_resources.grd":
        content = content.replace("IDS_CHROMELABS_THORIUM_2024_NAME", "__TEMP_THOR_NAME__")
        content = content.replace("IDS_CHROMELABS_THORIUM_2024_DESCRIPTION", "__TEMP_THOR_DESC__")
    
    count_t = content.count("Thorium")
    count_os = content.count("ThoriumOS")
    count_low = content.count("thorium.exe") + content.count("thorium://")
    
    content = content.replace("ThoriumOS", "SeleniumOS")
    content = content.replace("Thorium", "Selenium")
    content = content.replace("thorium.exe", "selenium.exe")
    content = content.replace("thorium://", "selenium://")
    content = content.replace("Software\\Thorium", "Software\\Selenium")
    content = content.replace("THORIUM_VERSION.txt", "SELENIUM_VERSION.txt")
    
    if rel == "chrome/app/generated_resources.grd":
        content = content.replace("__TEMP_THOR_NAME__", "IDS_CHROMELABS_THORIUM_2024_NAME")
        content = content.replace("__TEMP_THOR_DESC__", "IDS_CHROMELABS_THORIUM_2024_DESCRIPTION")
        
    if content != original:
        p.write_text(content, encoding="utf-8")
        total_replaced_files += 1
        total_replacements += count_t
        print(f"Updated {rel} ({count_t} replacements)")

# 3. Process all .xtb translation files in chrome/app/resources and components/strings
print("\n--- Processing XTB translation catalogs ---")
xtb_dirs = [
    src_root / "chrome" / "app" / "resources",
    src_root / "components" / "strings",
]

xtb_count = 0
for d in xtb_dirs:
    if not d.exists():
        continue
    for p in d.glob("*.xtb"):
        content = p.read_text(encoding="utf-8", errors="ignore")
        if "Thorium" in content or "thorium" in content:
            original = content
            c_t = content.count("Thorium")
            content = content.replace("ThoriumOS", "SeleniumOS")
            content = content.replace("Thorium", "Selenium")
            content = content.replace("thorium.exe", "selenium.exe")
            content = content.replace("thorium://", "selenium://")
            p.write_text(content, encoding="utf-8")
            xtb_count += 1
            total_replaced_files += 1
            total_replacements += c_t

print(f"Updated {xtb_count} XTB files.")
print(f"Total files updated: {total_replaced_files}")
print(f"Total Thorium replacements: {total_replacements}")
