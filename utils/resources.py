"""
Resource management for the Folio application.
Handles loading of icons and assets, preferring compiled Qt resources with a
filesystem fallback.
"""

# ----- Built-In Modules-----
import re
import sys
from pathlib import Path

# ----- PySide6 Modules-----
from PySide6.QtCore import QByteArray, QFile, QIODevice, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

try:
    import resources_rc  # noqa: F401

    USE_QT_RESOURCES = True
except ImportError:
    USE_QT_RESOURCES = False


def get_resource_path(relative_path: str) -> str:
    """
    Get path to resource, preferring Qt resources when available.

    Args:
        relative_path: Relative path to resource (e.g., 'assets/icon.png')

    Returns:
        Path to resource (Qt resource path or file path)
    """
    # If Qt resources are available, use them
    if USE_QT_RESOURCES:
        qt_path: str = f":/{relative_path}"
        # Check if resource exists in Qt resource system
        if QFile.exists(qt_path):
            return qt_path

    # Fallback to file-based resources
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Not running as bundled app, use source directory
        # Get the project root (utils/ -> repo root)
        base_path: Path = Path(__file__).parent.parent

    return str(base_path / relative_path)


def get_icon(icon_name: str, color: str = None) -> QIcon:
    """
    Load an icon from the assets directory, optionally recoloring SVG icons.

    Args:
        icon_name: Icon filename (e.g., 'obsidian-forge.ico')
        color: Hex color to apply to SVG icons (e.g., '#c0caf5')

    Returns:
        QIcon object
    """
    icon_path: str = get_resource_path(f"assets/{icon_name}")

    # If color is specified and it's an SVG, recolor it
    if color and icon_name.lower().endswith(".svg"):
        try:
            # Read SVG content from Qt resource or file
            if icon_path.startswith(":/"):
                # Read from Qt resource
                file = QFile(icon_path)
                if file.open(
                    QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text
                ):
                    svg_content: str = bytes(file.readAll()).decode("utf-8")
                    file.close()
                else:
                    raise Exception(f"Could not open Qt resource: {icon_path}")
            else:
                # Read from file system
                with open(icon_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()

            # Replace CSS-based fill colors in style tags
            svg_content = re.sub(
                r"\.st\d+\s*\{[^}]*fill\s*:\s*[^;]+;",
                lambda m: re.sub(r"fill\s*:\s*[^;]+", f"fill:{color}", m.group(0)),
                svg_content,
            )

            # Replace CSS-based stroke colors in style tags
            svg_content = re.sub(
                r"\.st\d+\s*\{[^}]*stroke\s*:\s*[^;]+;",
                lambda m: re.sub(r"stroke\s*:\s*[^;]+", f"stroke:{color}", m.group(0)),
                svg_content,
            )

            # Replace inline stroke attributes
            svg_content = re.sub(r'stroke="[^"]*"', f'stroke="{color}"', svg_content)

            # Replace inline fill attributes (but not "none")
            svg_content = re.sub(
                r'fill="(?!none)[^"]*"', f'fill="{color}"', svg_content
            )

            # Handle SVGs with path elements that don't have fill/stroke attributes
            # Add fill to path elements that have classes but no explicit fill
            svg_content = re.sub(
                r'(<path[^>]*class="[^"]*"[^>]*?)(/?>)',
                lambda m: (
                    m.group(1) + f' fill="{color}"' + m.group(2)
                    if "fill=" not in m.group(1)
                    else m.group(0)
                ),
                svg_content,
            )

            # Create icon from modified SVG
            byte_array = QByteArray(svg_content.encode("utf-8"))
            renderer = QSvgRenderer(byte_array)
            # Render large so the icon stays crisp at any requested size
            pixmap = QPixmap(256, 256)
            pixmap.fill(Qt.GlobalColor.transparent)  # Transparent background

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            renderer.render(painter, QRectF(0, 0, 256, 256))
            painter.end()

            return QIcon(pixmap)
        except Exception as e:
            print(f"Warning: Could not recolor SVG icon {icon_name}: {e}")

    # Default icon loading
    icon = QIcon(icon_path)
    if icon.isNull():
        print(f"Warning: Icon not found: {icon_path}")
    return icon


def get_pixmap(image_name: str) -> QPixmap:
    """
    Load a pixmap from the assets directory.

    Args:
        image_name: Image filename (e.g., 'icon.png')

    Returns:
        QPixmap object
    """
    image_path: str = get_resource_path(f"assets/{image_name}")
    pixmap = QPixmap(image_path)
    if pixmap.isNull():
        print(f"Warning: Pixmap not found: {image_path}")
    return pixmap


class Resources:
    """Static resource manager for backwards compatibility."""

    @staticmethod
    def icon(name: str) -> QIcon:
        """Load an icon from assets."""
        return get_icon(name)

    @staticmethod
    def pixmap(name: str) -> QPixmap:
        """Load a pixmap from assets."""
        return get_pixmap(name)
