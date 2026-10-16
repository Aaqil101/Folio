"""Regenerate folio.ico from folio.svg (transparent background).

The icon previously had a baked-in white background (converter default); this
renders the vector at every size Windows actually asks for, with alpha kept.
Artwork uses the app's window-icon blue (#7aa2f7 in main.py) so the exe
icon, installer icon, and in-app window icon all match.

The ICO container is assembled by hand rather than via Pillow's ICO writer:
Pillow stores frames smallest-first, and Windows reads the directory in
order (properties pane, preview), which made the file present as a 16x16
icon. Largest-first is the conventional order.

Usage (from the repo root):
    python assets/application/generate_icon.py [--color #rrggbb]
"""

import argparse
import io
import struct
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

HERE = Path(__file__).parent
SIZES = (16, 24, 32, 48, 64, 128, 256)  # written largest-first into the ICO
DEFAULT_COLOR = "#7aa2f7"


def render_svg(svg_path: Path, color: str, size: int) -> bytes:
    """Render the SVG at one size with the artwork recolored, alpha kept."""
    svg = svg_path.read_text(encoding="utf-8").replace(
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
    return bytes(data)


def build_ico(frames: list[tuple[int, bytes]]) -> bytes:
    """Assemble an ICO from (size, PNG bytes) frames, largest first."""
    header = struct.pack("<HHH", 0, 1, len(frames))
    offset = 6 + 16 * len(frames)
    entries = b""
    blobs = b""
    for size, png in frames:
        dim = 0 if size >= 256 else size  # ICO stores 256 as 0
        entries += struct.pack(
            "<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset
        )
        blobs += png
        offset += len(png)
    return header + entries + blobs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--color", default=DEFAULT_COLOR, help="artwork color")
    args = parser.parse_args()

    QGuiApplication([])  # QPixmap needs a GUI app instance
    frames = [
        (size, render_svg(HERE / "folio.svg", args.color, size))
        for size in sorted(SIZES, reverse=True)
    ]
    out = HERE / "folio.ico"
    out.write_bytes(build_ico(frames))
    print(f"wrote {out} ({', '.join(str(s) for s, _ in frames)} px, largest first)")


if __name__ == "__main__":
    main()
