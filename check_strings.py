import re
from pathlib import Path

src_root = Path(r"C:\src\chromium\src")

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

total_thorium_in_names = 0
for rel in grd_files:
    p = src_root / rel
    if not p.exists():
        continue
    content = p.read_text(encoding="utf-8", errors="ignore")
    names = re.findall(r'name=[\"\']([^\"\']+)[\"\']', content)
    thorium_names = [n for n in names if "thorium" in n.lower() and not n.startswith("http")]
    if thorium_names:
        print(f"{rel}: {thorium_names}")
        total_thorium_in_names += len(thorium_names)

print("Total message/resource IDs with thorium:", total_thorium_in_names)
