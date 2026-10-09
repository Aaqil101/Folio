# ----- Built-In Modules -----
import argparse
import sys

# ----- ReportLab Modules -----
from reportlab.pdfgen import canvas

# ----- Utils Modules-----
from utils.constants import PAGE_HEIGHT, PAGE_WIDTH
from utils.format_utils import zero_padding


# ----- Function Definitions -----
def draw_numbered_page(
    c: canvas.Canvas,
    number: int,
    box_size: tuple[int, int],
    font_size: int,
    line_width: int,
) -> None:
    """
    Draw a single PDF page with a centred numbered box.

    The function draws a rectangle of size BOX_WIDTH x BOX_HEIGHT centred on
    the A4 page, then renders the provided number in large bold Helvetica
    centred inside the box. Finally it advances the canvas to a new page.

    Arguments:
        c: A reportlab.pdfgen.canvas.Canvas to draw onto.
        number: The integer to draw centred in the box.
        box_size: A tuple containing the width and height of the book in points.
        font_size: The font size for the page number text.
        line_width: The width of the rectangle border.
    """

    box_x: float = (PAGE_WIDTH - box_size[0]) / 2
    box_y: float = (PAGE_HEIGHT - box_size[1]) / 2

    c.setLineWidth(line_width)
    c.rect(box_x, box_y, box_size[0], box_size[1], stroke=1, fill=0)

    c.setFont("Helvetica-Bold", font_size)
    text_x: float = PAGE_WIDTH / 2
    text_y: float = box_y + (box_size[1] - font_size * 0.7) / 2
    c.drawCentredString(text_x, text_y, zero_padding(number))

    c.showPage()


def generate_test_pdf(
    page_count: int,
    output_path: str,
    box_size: tuple[int, int],
    font_size: int,
    line_width: int,
) -> int:
    """
    Generate a numbered test PDF file with the given page count.

    Arguments:
        page_count: Number of pages to generate.
        output_path: Path to write the generated PDF file.
        box_size: A tuple containing the width and height of the book in points.
        font_size: The font size for the page numbers.
        line_width: The width of the rectangle border.
    Returns:
        The number of pages written to the generated PDF.
    """

    c = canvas.Canvas(output_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    for i in range(1, page_count + 1):
        draw_numbered_page(c, i, box_size, font_size, line_width)

    c.save()
    print(f"Generated {zero_padding(page_count)}-page test PDF → {output_path}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Generate a numbered test PDF for Folio imposition testing."
    )

    # Document settings
    doc_group: argparse._ArgumentGroup = parser.add_argument_group("Document settings")
    doc_group.add_argument(
        "--pages",
        type=int,
        default=8,
        help="Number of pages to generate (default: 08). Best as a multiple of 04.",
    )
    doc_group.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"Output file path (default: test_08_pages.pdf)",
    )

    # Layout settings
    layout_group: argparse._ArgumentGroup = parser.add_argument_group("Layout settings")
    layout_group.add_argument(
        "--box",
        type=int,
        nargs=2,
        default=[400, 400],
        metavar=("WIDTH", "HEIGHT"),
        help="Box size in points (default: 400 400)",
    )
    layout_group.add_argument(
        "--font",
        type=int,
        default=192,
        help="Font size for page numbers (default: 192)",
    )
    layout_group.add_argument(
        "--line",
        type=int,
        default=10,
        help="Line width for page borders in points (default: 10)",
    )

    args: argparse.Namespace = parser.parse_args()

    if args.pages < 1:
        parser.error("--pages must be at least 1")

    if args.output is None:
        args.output = f"test_{zero_padding(args.pages)}_pages.pdf"

    box_size: tuple[int, int] = (args.box[0], args.box[1])
    generate_test_pdf(args.pages, args.output, box_size, args.font, args.line)


if __name__ == "__main__":
    main()
