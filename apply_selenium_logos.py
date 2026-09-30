import os
import shutil
import vtracer
from PIL import Image

SOURCE_IMAGE_PATH = r"C:\Users\Daniel Yepez Garces\Downloads\ChatGPT Image 28 sept 2026, 06_59_51 p.m. (1).png"
DOWNLOADS_DIR = r"C:\Users\Daniel Yepez Garces\Downloads\Selenium_Branding"
LOGOS_DIR = r"C:\thorium\logos"

SRC_ROOT = r"C:\src\chromium\src"
THORIUM_ROOT = r"C:\thorium"

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def generate_assets():
    print(f"Loading source image: {SOURCE_IMAGE_PATH}")
    img_src = Image.open(SOURCE_IMAGE_PATH).convert("RGBA")
    width, height = img_src.size
    print(f"Source image dimensions: {width}x{height}")

    ensure_dir(DOWNLOADS_DIR)
    ensure_dir(LOGOS_DIR)

    # 1. Generate standalone PNGs
    sizes = [16, 22, 24, 32, 48, 64, 128, 176, 252, 256, 504, 512, 600, 720, 1024]
    generated_pngs = {}
    for s in sizes:
        resized = img_src.resize((s, s), Image.Resampling.LANCZOS)
        generated_pngs[s] = resized
        
        # Save common export sizes to export folders
        if s in [16, 24, 32, 48, 64, 128, 256, 512, 1024]:
            out_file = os.path.join(DOWNLOADS_DIR, f"selenium_{s}.png")
            resized.save(out_file, "PNG")
            shutil.copy2(out_file, os.path.join(LOGOS_DIR, f"selenium_{s}.png"))
    print("Standalone PNGs generated.")

    # 2. Generate multi-size ICO
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_path = os.path.join(DOWNLOADS_DIR, "selenium.ico")
    img_src.save(ico_path, format="ICO", sizes=ico_sizes)
    shutil.copy2(ico_path, os.path.join(LOGOS_DIR, "selenium.ico"))
    print("Standalone selenium.ico generated with all 7 resolutions.")

    # 3. Generate vectorized SVG with vtracer
    svg_raw_path = os.path.join(LOGOS_DIR, "selenium_raw.svg")
    print("Vectorizing image to SVG using vtracer...")
    vtracer.convert_image_to_svg_py(SOURCE_IMAGE_PATH, svg_raw_path)
    with open(svg_raw_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Ensure clean viewBox
    if 'viewBox=' not in svg_content:
        svg_content = svg_content.replace(f'width="{width}" height="{height}">', f'viewBox="0 0 {width} {height}" width="100%" height="100%">')
    
    svg_path = os.path.join(DOWNLOADS_DIR, "selenium.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    shutil.copy2(svg_path, os.path.join(LOGOS_DIR, "selenium.svg"))
    print(f"Standalone scalable SVG generated: {svg_path}")

    # 4. Generate banner logos for about_version (342x64 and 684x128)
    banner_100 = Image.new("RGBA", (342, 64), (0, 0, 0, 0))
    logo_for_banner_100 = img_src.resize((60, 60), Image.Resampling.LANCZOS)
    banner_100.paste(logo_for_banner_100, (2, 2), logo_for_banner_100)

    banner_200 = Image.new("RGBA", (684, 128), (0, 0, 0, 0))
    logo_for_banner_200 = img_src.resize((120, 120), Image.Resampling.LANCZOS)
    banner_200.paste(logo_for_banner_200, (4, 4), logo_for_banner_200)

    # 5. Target destinations mapping
    target_operations = [
        # ICO files
        (ico_path, [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\win\chromium.ico"),
            os.path.join(SRC_ROOT, r"chrome\installer\mini_installer\mini_installer.ico"),
            os.path.join(SRC_ROOT, r"chrome\installer\setup\setup.ico"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\win\chromium.ico"),
            os.path.join(THORIUM_ROOT, r"src\chrome\installer\mini_installer\mini_installer.ico"),
            os.path.join(THORIUM_ROOT, r"src\chrome\installer\setup\setup.ico"),
            os.path.join(THORIUM_ROOT, r"thorium_shell\thorium.ico"),
            os.path.join(THORIUM_ROOT, r"thorium_shell\thorium_shell.ico"),
            os.path.join(THORIUM_ROOT, r"src\content\shell\app\thorium_shell.ico"),
        ], "copy"),

        # SVG files
        (svg_path, [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\product_logo.svg"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\product_logo_animation.svg"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\product_logo.svg"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\product_logo_animation.svg"),
            os.path.join(THORIUM_ROOT, r"thorium_shell\thorium.svg"),
        ], "copy"),

        # PNG Tiles
        (generated_pngs[600], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\win\tiles\Logo.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\win\tiles\Logo.png"),
        ], "image"),
        (generated_pngs[176], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\win\tiles\SmallLogo.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\win\tiles\SmallLogo.png"),
        ], "image"),

        # Square product logos
        (generated_pngs[16], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\product_logo_16.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\linux\product_logo_16.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_100_percent\chromium\product_logo_16.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_100_percent\chromium\linux\product_logo_16.png"),
            os.path.join(SRC_ROOT, r"components\resources\default_100_percent\chromium\favicon_product.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\product_logo_16.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\linux\product_logo_16.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_100_percent\chromium\product_logo_16.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_100_percent\chromium\linux\product_logo_16.png"),
        ], "image"),

        (generated_pngs[22], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\product_logo_22_mono.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\product_logo_22_mono.png"),
        ], "image"),

        (generated_pngs[24], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\product_logo_24.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\linux\product_logo_24.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\product_logo_24.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\linux\product_logo_24.png"),
        ], "image"),

        (generated_pngs[32], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_100_percent\chromium\product_logo_32.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_100_percent\chromium\linux\product_logo_32.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_200_percent\chromium\product_logo_16.png"),
            os.path.join(SRC_ROOT, r"components\resources\default_200_percent\chromium\favicon_product.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_100_percent\chromium\product_logo_32.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_100_percent\chromium\linux\product_logo_32.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_200_percent\chromium\product_logo_16.png"),
        ], "image"),

        (generated_pngs[48], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\product_logo_48.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\linux\product_logo_48.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\product_logo_48.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\linux\product_logo_48.png"),
        ], "image"),

        (generated_pngs[64], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\product_logo_64.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\linux\product_logo_64.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_200_percent\chromium\product_logo_32.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\product_logo_64.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\linux\product_logo_64.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_200_percent\chromium\product_logo_32.png"),
        ], "image"),

        (generated_pngs[128], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\product_logo_128.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\linux\product_logo_128.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\product_logo_128.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\linux\product_logo_128.png"),
        ], "image"),

        (generated_pngs[256], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\product_logo_256.png"),
            os.path.join(SRC_ROOT, r"chrome\app\theme\chromium\linux\product_logo_256.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\product_logo_256.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\chromium\linux\product_logo_256.png"),
            os.path.join(THORIUM_ROOT, r"thorium_shell\thorium_shell.png"),
        ], "image"),

        # Mascot / branding graphics
        (generated_pngs[252], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_100_percent\chromium\thorium_mascot.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_100_percent\chromium\thorium_mascot.png"),
        ], "image"),

        (generated_pngs[504], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_200_percent\chromium\thorium_mascot.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_200_percent\chromium\thorium_mascot.png"),
        ], "image"),

        (generated_pngs[720], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_100_percent\chromium\thorium_guy.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_100_percent\chromium\thorium_guy.png"),
        ], "image"),

        (generated_pngs[1024], [
            os.path.join(SRC_ROOT, r"chrome\app\theme\default_100_percent\chromium\thorium_atomic.png"),
            os.path.join(THORIUM_ROOT, r"src\chrome\app\theme\default_100_percent\chromium\thorium_atomic.png"),
        ], "image"),

        # Banner for about_version
        (banner_100, [
            os.path.join(SRC_ROOT, r"components\resources\default_100_percent\chromium\product_logo.png"),
            os.path.join(SRC_ROOT, r"components\resources\default_100_percent\chromium\product_logo_white.png"),
            os.path.join(THORIUM_ROOT, r"src\components\resources\default_100_percent\chromium\product_logo.png"),
            os.path.join(THORIUM_ROOT, r"src\components\resources\default_100_percent\chromium\product_logo_white.png"),
        ], "image"),

        (banner_200, [
            os.path.join(SRC_ROOT, r"components\resources\default_200_percent\chromium\product_logo.png"),
            os.path.join(SRC_ROOT, r"components\resources\default_200_percent\chromium\product_logo_white.png"),
            os.path.join(THORIUM_ROOT, r"src\components\resources\default_200_percent\chromium\product_logo.png"),
            os.path.join(THORIUM_ROOT, r"src\components\resources\default_200_percent\chromium\product_logo_white.png"),
        ], "image"),
    ]

    applied_count = 0
    for src_item, dst_list, op_type in target_operations:
        for dst in dst_list:
            parent = os.path.dirname(dst)
            if not os.path.exists(parent):
                continue
            if op_type == "copy":
                shutil.copy2(src_item, dst)
            elif op_type == "image":
                src_item.save(dst, "PNG")
            applied_count += 1
            print(f"Updated: {dst}")

    print(f"\nSuccessfully replaced {applied_count} logo assets across the project!")

if __name__ == "__main__":
    generate_assets()
