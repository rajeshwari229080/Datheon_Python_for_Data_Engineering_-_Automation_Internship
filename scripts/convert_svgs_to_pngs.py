"""Convert all SVG files in assets/ to high-resolution PNG images using headless Edge.
Supports exact viewBox sizing and transparent/white backgrounds.
"""
import os
import subprocess
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(REPO_ROOT, "assets")

EDGE_BIN = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_BIN):
    EDGE_BIN = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

SVG_CONFIGS = [
    {
        "svg": "hero_banner.svg",
        "png": "hero_banner.png",
        "width": 1200,
        "height": 360,
    },
    {
        "svg": "architecture_diagram.svg",
        "png": "architecture_diagram.png",
        "width": 1100,
        "height": 560,
    },
    {
        "svg": "pipeline_workflow.svg",
        "png": "pipeline_workflow.png",
        "width": 1100,
        "height": 240,
    },
    {
        "svg": "linkedin_post.svg",
        "png": "linkedin_post.png",
        "width": 1200,
        "height": 630,
    },
]


def convert_svg_to_png(svg_name: str, png_name: str, width: int, height: int):
    svg_file = os.path.join(ASSETS_DIR, svg_name)
    png_file = os.path.join(ASSETS_DIR, png_name)

    if not os.path.exists(svg_file):
        print(f"Error: {svg_file} does not exist.")
        return False

    # Create temporary clean HTML wrapper to ensure perfect fit without scrollbars or margins
    html_wrapper = os.path.join(ASSETS_DIR, f"_temp_{svg_name}.html")
    with open(svg_file, "r", encoding="utf-8") as f:
        svg_content = f.read()

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0;
    padding: 0;
    width: {width}px;
    height: {height}px;
    overflow: hidden;
    background: transparent;
  }}
  svg {{
    display: block;
    width: {width}px;
    height: {height}px;
  }}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""
    with open(html_wrapper, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_uri = f"file:///{os.path.abspath(html_wrapper).replace(os.sep, '/')}"

    cmd = [
        EDGE_BIN,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--window-size={width},{height}",
        f"--screenshot={png_file}",
        file_uri
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=20)
        time.sleep(0.5)
        if os.path.exists(png_file) and os.path.getsize(png_file) > 1000:
            print(f"Successfully converted {svg_name} -> {png_name} ({os.path.getsize(png_file)} bytes)")
            success = True
        else:
            print(f"Failed converting {svg_name}: Edge return code {proc.returncode}")
            print("Edge stdout:", proc.stdout.decode("utf-8", errors="ignore"))
            print("Edge stderr:", proc.stderr.decode("utf-8", errors="ignore"))
            success = False
    except Exception as e:
        print(f"Exception converting {svg_name}: {e}")
        success = False
    finally:
        if os.path.exists(html_wrapper):
            try:
                os.remove(html_wrapper)
            except Exception:
                pass

    return success


def main():
    print("Starting SVG to PNG conversion via headless Edge...")
    all_ok = True
    for cfg in SVG_CONFIGS:
        ok = convert_svg_to_png(cfg["svg"], cfg["png"], cfg["width"], cfg["height"])
        if not ok:
            all_ok = False

    # Also update root image.png with linkedin_post.png
    linkedin_png = os.path.join(ASSETS_DIR, "linkedin_post.png")
    root_png = os.path.join(REPO_ROOT, "image.png")
    if os.path.exists(linkedin_png):
        with open(linkedin_png, "rb") as f_in, open(root_png, "wb") as f_out:
            f_out.write(f_in.read())
        print(f"Updated root image.png ({os.path.getsize(root_png)} bytes)")

    if all_ok:
        print("All SVG assets successfully converted to PNG!")
    else:
        print("Some conversions encountered issues.")


if __name__ == "__main__":
    main()
