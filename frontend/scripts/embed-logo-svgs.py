"""Embed provided PNG artwork into SVG wrappers for pixel-accurate logos."""
from __future__ import annotations

import base64
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "public"


def wrap_png(png_name: str, svg_name: str, w: int, h: int) -> None:
    png = PUBLIC / png_name
    b64 = base64.b64encode(png.read_bytes()).decode("ascii")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="Plenvo">\n'
        f'  <image href="data:image/png;base64,{b64}" width="{w}" height="{h}" '
        f'preserveAspectRatio="xMidYMid meet"/>\n'
        f"</svg>\n"
    )
    out = PUBLIC / svg_name
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    wrap_png("plenvo-icon-v2.png", "plenvo-icon-v2.svg", 1024, 1024)
    wrap_png("plenvo-logo-full-v2.png", "plenvo-logo-full-v2.svg", 1024, 275)
