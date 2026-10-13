# ----- Built-In Modules -----
from pathlib import Path

# ----- ReportLab Modules -----
from reportlab.lib.pagesizes import A3, A4, A5, landscape

# ----- Module-Level Constants -----
PAGE_WIDTH: float = A4[0]
PAGE_HEIGHT: float = A4[1]
A4_LANDSCAPE: tuple[float, float] = landscape(A4)
SHEET_SIZES: dict[str, tuple[float, float]] = {
    "A3": landscape(A3),
    "A4": A4_LANDSCAPE,
    "A5": landscape(A5),
}
REPO_ROOT: Path = Path(__file__).resolve().parent.parent

# ----- UI Constants (ported from Obsidian-Forge) -----
FONT_FAMILY: str = "JetBrainsMono Nerd Font"
FONT_SIZE_HEADER: int = 13
BORDER_RADIUS: int = 8
BORDER_RADIUS_SMALL: int = 6
BORDER_RADIUS_LARGE: int = 12

# ----- App Metadata -----
APP_NAME: str = "Folio"
APP_VERSION: str = "0.1.0"
AUTHOR: str = "Aaqil"
DESCRIPTION: str = "Turn any PDF into a print-ready booklet.\nNo page shuffling required."
WEBSITE_URL: str = "https://github.com/Aaqil101/Folio"
