# ----- Built-In Modules -----
import io

# ----- PyMuPDF Modules -----
import fitz

# ----- PikePDF Modules -----
from pikepdf import Pdf

# ----- ReportLab Modules -----
from reportlab.lib.pagesizes import A4

# ----- Utils Modules -----
from utils.format_utils import zero_padding

# ----- Module-Level Constants -----
# IMPORTANT: 841.89 points is the width of an A4 sheet in landscape orientation
PAGE_WIDTH: float = round(A4[1], 2)  # A4[1] = 841.8897637795277
HALF_WIDTH: float = PAGE_WIDTH / 2
STAMP_MARGIN: float = 10.0
STAMP_FONT_SIZE: float = 6.0


# ----- Function Definitions -----
