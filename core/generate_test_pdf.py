# ----- Built-In Modules -----
import argparse

# ----- ReportLab Modules -----
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ----- Utils Modules-----
from utils.format_utils import zero_padding

# ----- Module-Level Constants -----
PAGE_WIDTH, PAGE_HEIGHT = A4


# ----- Function Definitions -----
def draw_numbered_page(
    c: canvas.Canvas,
    number: int,
    book_size: tuple[int, int],
    font_size: int,
    line_width: int,
) -> None:
    """
    Draw a single PDF page with a centered numbered box.

    The function draws a rectangle of size BOX_WIDTH x BOX_HEIGHT centered on
    the A4 page, then renders the provided number in large bold Helvetica
    centered inside the box. Finally it advances the canvas to a new page.

    Args:
        c: A reportlab.pdfgen.canvas.Canvas to draw onto.
        number: The integer to draw centered in the box.
        book_size: A tuple containing the width and height of the book in points.
        font_size: The font size for the page number text.
        line_width: The width of the rectangle border.
    """

    box_x: float = (PAGE_WIDTH - book_size[0]) / 2
    box_y: float = (PAGE_HEIGHT - book_size[1]) / 2

    c.setLineWidth(line_width)
    c.rect(box_x, box_y, book_size[0], book_size[1], stroke=1, fill=0)

    c.setFont("Helvetica-Bold", font_size)
    text_x: float = PAGE_WIDTH / 2
    text_y: float = box_y + (book_size[1] - font_size * 0.7) / 2
    c.drawCentredString(text_x, text_y, zero_padding(number))

    c.showPage()


def generate_test_pdf(
    page_count: int,
    output_path: str,
    book_size: tuple[int, int],
    font_size: int,
    line_width: int,
) -> int:
    """
    Generate a numbered test PDF file with the given page count.

    Args:
        page_count: Number of pages to generate.
        output_path: Path to write the generated PDF file.
        book_size: A tuple containing the width and height of the book in points.
        font_size: The font size for the page numbers.
        line_width: The width of the rectangle border.
    Returns:
        The number of pages written to the generated PDF.
    """

    c = canvas.Canvas(output_path, pagesize=A4)

    for i in range(1, page_count + 1):
        draw_numbered_page(c, i, book_size, font_size, line_width)

    c.save()
    print(f"Generated {zero_padding(page_count)}-page test PDF → {output_path}")


def main() -> None:
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
        "--book",
        type=int,
        nargs=2,
        default=[400, 400],
        metavar=("WIDTH", "HEIGHT"),
        help="Book size in points (default: 400 400)",
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

    book_size: tuple[int, int] = (args.book[0], args.book[1])
    generate_test_pdf(args.pages, args.output, book_size, args.font, args.line)


if __name__ == "__main__":
    main()
