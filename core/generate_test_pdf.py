# ----- Built-In Modules-----
import argparse

# ----- ReportLab Modules -----
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ----- Module-Level Constants -----
PAGE_WIDTH, PAGE_HEIGHT = A4

BOX_WIDTH = 400
BOX_HEIGHT = 400
FONT_SIZE = 192


# ----- Function Definitions -----
def zero_padding(number: int, width: int = 2) -> str:
    """
    Return the given number as a zero-padded string.

    Args:
        number: The integer to format.
        width: The minimum width of the returned string, padded with leading zeros.

    Returns:
        A string representation of the number with leading zeros as needed.
    """
    return f"{number:0{width}d}"


def draw_numbered_page(c: canvas.Canvas, number: int) -> None:
    """
    Draw a single PDF page with a centered numbered box.

    The function draws a rectangle of size BOX_WIDTH x BOX_HEIGHT centered on
    the A4 page, then renders the provided number in large bold Helvetica
    centered inside the box. Finally it advances the canvas to a new page.

    Args:
        c: A reportlab.pdfgen.canvas.Canvas to draw onto.
        number: The integer to draw centered in the box.
    """

    box_x: float = (PAGE_WIDTH - BOX_WIDTH) / 2
    box_y: float = (PAGE_HEIGHT - BOX_HEIGHT) / 2

    c.setLineWidth(10)
    c.rect(box_x, box_y, BOX_WIDTH, BOX_HEIGHT, stroke=1, fill=0)

    c.setFont("Helvetica-Bold", FONT_SIZE)
    text_x: float = PAGE_WIDTH / 2
    text_y: float = box_y + (BOX_HEIGHT - FONT_SIZE * 0.7) / 2
    c.drawCentredString(text_x, text_y, zero_padding(number))

    c.showPage()


def generate_test_pdf(page_count: int, output_path: str) -> int:
    """
    Generate a numbered test PDF file with the given page count.

    Args:
        page_count: Number of pages to generate.
        output_path: Path to write the generated PDF file.

    Returns:
        The number of pages written to the generated PDF.
    """

    c = canvas.Canvas(output_path, pagesize=A4)

    for i in range(1, page_count + 1):
        draw_numbered_page(c, i)

    c.save()
    print(f"Saved {zero_padding(page_count)}-page test PDF to: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a numbered test PDF for Folio imposition testing."
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=8,
        help="Number of pages to generate (default: 08). Best as a multiple of 04.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"Output file path (default: test_08_pages.pdf)",
    )
    args: argparse.Namespace = parser.parse_args()

    if args.pages < 1:
        parser.error("--pages must be at least 1")

    if args.output is None:
        args.output = f"test_{zero_padding(args.pages)}_pages.pdf"

    generate_test_pdf(args.pages, args.output)


if __name__ == "__main__":
    main()
