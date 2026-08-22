"""Build Plenvo brand assets from provided logo artwork."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
ASSETS_SRC = Path(
    r"C:\Users\vala\.cursor\projects\c-Users-vala-OneDrive-gmv-com-Desktop-VAZIM-2026-PERSONAL-TeamOS\assets"
)

ICON_SRC = ASSETS_SRC / (
    "c__Users_vala_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_"
    "image-9ab42b25-00ec-4e0c-b103-ddbf91023c68.png"
)
FULL_SRC = ASSETS_SRC / (
    "c__Users_vala_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_"
    "image-58cc640f-ecf7-4e54-bd13-c98cfe7f7cdb.png"
)

# Geometric P monogram — abstract rounded "P", gold on charcoal squircle.
ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="Plenvo">
  <rect width="128" height="128" rx="28" fill="#14170f"/>
  <path
    d="M42 98V30h30c16.5 0 30 13.5 30 30S88.5 90 72 90H56"
    fill="none"
    stroke="#c4a35a"
    stroke-width="15"
    stroke-linecap="round"
    stroke-linejoin="round"
  />
</svg>
"""

# Full lockup: icon + italic serif wordmark (Instrument Serif when available).
FULL_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 112" role="img" aria-label="Plenvo">
  <rect width="112" height="112" rx="24" fill="#14170f"/>
  <path
    d="M36.75 85.75V26.25h26.25c14.45 0 26.25 11.8 26.25 26.25S77.45 78.75 63 78.75H49"
    fill="none"
    stroke="#c4a35a"
    stroke-width="13.125"
    stroke-linecap="round"
    stroke-linejoin="round"
  />
  <text
    x="136"
    y="74"
    fill="#e8e4d8"
    font-family="Instrument Serif, Georgia, 'Times New Roman', serif"
    font-size="66"
    font-style="italic"
    letter-spacing="0.01em"
  >Plenvo</text>
</svg>
"""


def write_svg(name: str, content: str) -> None:
    path = PUBLIC / name
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"wrote {path}")


def resize_cover(src: Image.Image, size: int) -> Image.Image:
    return src.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)


def on_opaque(
    src: Image.Image,
    size: int,
    bg: tuple[int, int, int, int] = (20, 23, 15, 255),
) -> Image.Image:
    """Apple touch / product icons prefer opaque backgrounds."""
    base = Image.new("RGBA", (size, size), bg)
    icon = resize_cover(src, size)
    return Image.alpha_composite(base, icon)


def save_png(img: Image.Image, name: str) -> None:
    path = PUBLIC / name
    img.save(path, format="PNG", optimize=True)
    print(f"wrote {path}")


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)

    write_svg("plenvo-icon-v2.svg", ICON_SVG)
    write_svg("plenvo-logo-full-v2.svg", FULL_SVG)

    icon = Image.open(ICON_SRC)
    full = Image.open(FULL_SRC)

    save_png(icon.convert("RGBA"), "plenvo-icon-v2.png")
    save_png(full.convert("RGBA"), "plenvo-logo-full-v2.png")

    save_png(resize_cover(icon, 16), "favicon-16x16.png")
    save_png(resize_cover(icon, 32), "favicon-32x32.png")
    save_png(on_opaque(icon, 180), "apple-touch-icon.png")
    save_png(on_opaque(icon, 512), "plenvo-icon-512.png")

    ico_path = PUBLIC / "favicon.ico"
    icon.convert("RGBA").save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"wrote {ico_path}")

    # Vector SVGs are the source of truth for in-app branding; skip PNG embed overwrite.
    # wrap_png("plenvo-icon-v2.png", "plenvo-icon-v2.svg", 1024, 1024)
    # wrap_png("plenvo-logo-full-v2.png", "plenvo-logo-full-v2.svg", 1024, 275)


if __name__ == "__main__":
    main()
