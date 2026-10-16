"""Regenerate the installer wizard artwork (issue #14).

Writes transparent PNGs for folio.iss:

- wizard-back-light.png / wizard-back-dark.png -> WizardBackImageFile /
  WizardBackImageFileDynamicDark: the folio book glyph in the app's
  window-icon blue (#7aa2f7, see assets/application/generate_icon.py),
  centered as a watermark at a per-appearance opacity. The wizard paints
  WizardBackColor underneath, so the PNGs stay transparent and the color
  can change without regenerating artwork.
- wizard-small.png -> WizardSmallImageFile: the same glyph at full
  opacity, replacing Inno's stock logo in the wizard's upper right.

Back canvases are 1988x1440 = exactly 497:360 x4 — the aspect ratio
Inno Setup maintains for the wizard-back image area (497:360, per the
docs), and larger than the 200%-DPI area so every DPI only ever
downscales.

Usage (from the repo root):
    python installer/generate_wizard_images.py
"""

import io
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

HERE = Path(__file__).parent
SVG = HERE.parent / "assets" / "application" / "folio.svg"
GLYPH_COLOR = "#7aa2f7"
CANVAS = (1988, 1440)  # 497:360 aspect, x4 — Inno's wizard-back area ratio
GLYPH_SIZE = 640  # rendered square; the glyph sits centered in its own box
SMALL_SIZE = 240  # >147 (Inno's built-in logo size) so DPI scaling stays sharp

# filename -> watermark opacity. Tuned per appearance: on the light
# background the blue needs more alpha to read, dark needs less.
VARIANTS = {
    "wizard-back-light.png": 0.26,
    "wizard-back-dark.png": 0.20,
}


def render_glyph(size: int, color: str) -> Image.Image:
    """Render folio.svg at size x size with the artwork recolored."""
    svg = SVG.read_text(encoding="utf-8").replace(
        'fill="currentColor"', f'fill="{color}"'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    buffer.close()
    return Image.open(io.BytesIO(bytes(data))).convert("RGBA")


def main() -> None:
    QGuiApplication([])  # QPixmap needs a GUI app instance
    glyph = render_glyph(GLYPH_SIZE, GLYPH_COLOR)
    w, h = CANVAS
    for name, opacity in VARIANTS.items():
        watermark = glyph.copy()
        # Scale the glyph's alpha only — color stays exactly #7aa2f7.
        alpha = watermark.getchannel("A").point(
            lambda a, o=opacity: int(a * o)
        )
        watermark.putalpha(alpha)
        canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        canvas.alpha_composite(
            watermark, ((w - GLYPH_SIZE) // 2, (h - GLYPH_SIZE) // 2)
        )
        out = HERE / name
        canvas.save(out, format="PNG", optimize=True)
        print(f"wrote {out} ({w}x{h}, opacity {opacity:.0%})")

    # Upper-right wizard logo: full-opacity glyph, square, no watermark.
    small = render_glyph(SMALL_SIZE, GLYPH_COLOR)
    out = HERE / "wizard-small.png"
    small.save(out, format="PNG", optimize=True)
    print(f"wrote {out} ({SMALL_SIZE}x{SMALL_SIZE}, full opacity)")


if __name__ == "__main__":
    main()
