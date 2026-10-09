# ----- Built-In Modules -----
from pathlib import Path

# ----- ReportLab Modules -----
from reportlab.lib.pagesizes import A4, landscape

# ----- Module-Level Constants -----
PAGE_WIDTH: float = A4[0]
PAGE_HEIGHT: float = A4[1]
A4_LANDSCAPE: tuple[float, float] = landscape(A4)
REPO_ROOT: Path = Path(__file__).resolve().parent.parent
