# ----- Built-In Modules -----
import shlex

# ----- PyMuPDF Modules -----
import fitz

# ----- Core Modules -----
from core.calculation import impose
from core.verify_booklet import stamp_page_numbers, verify_booklet

# ----- Utils Modules -----
from utils.constants import A4_LANDSCAPE


def place_pages_side_by_side(
    source: fitz.Document,
    output: fitz.Document,
    left_index: int | None,
    right_index: int | None,
) -> None:
    """Compose one landscape output page from a left and a right source page.

    Appends a single landscape A4 page (A4_LANDSCAPE) to `output` and
    treats it as two halves split at half the width. Each side whose index is
    not None is drawn from `source`, scaled uniformly (aspect ratio preserved)
    to the largest size that fits inside its half, and centred both
    horizontally and vertically within that half. A side whose index is None
    (the sentinel produced by core.calculation.impose for padding pages) is
    left blank, so the new page may hold one real page, two, or none.

    Arguments:
        source: Document the pages are copied from.
        output: Document that receives the new composed page.
        left_index: 0-based index in `source` for the left half, or None for blank.
        right_index: 0-based index in `source` for the right half, or None for blank.
    """
    page_width, page_height = A4_LANDSCAPE
    half_width: float = page_width / 2

    new_page: fitz.Page = output.new_page(width=page_width, height=page_height)

    for side, index in [("L", left_index), ("R", right_index)]:
        if index is None:
            continue

        source_page: fitz.Page = source[index]
        media: fitz.Rect = source_page.mediabox

        source_width: float = media.width
        source_height: float = media.height

        scale: float = min(half_width / source_width, page_height / source_height)
        scaled_width: float = source_width * scale
        scaled_height: float = source_height * scale

        if side == "L":
            x: float = (half_width - scaled_width) / 2
        else:
            x = half_width + (half_width - scaled_width) / 2
        y: float = (page_height - scaled_height) / 2

        dest = fitz.Rect(x, y, x + scaled_width, y + scaled_height)
        new_page.show_pdf_page(dest, source, index, clip=media)


def build_booklet(input_path: str, output_path: str) -> None:
    """
    Create a booklet-imposed PDF from an input PDF file.

    Reads the PDF at input_path, computes an imposition order using
    core.calculation.impose, places two pages side-by-side per output
    page and writes the resulting PDF to output_path.

    Arguments:
        input_path: Path to the source PDF file.
        output_path: Path where the imposed PDF will be saved.
    """

    source: fitz.Document = fitz.open(input_path)
    if source.needs_pass:
        source.close()
        raise ValueError(
            f"Source PDF is password-protected and cannot be imposed: {input_path}"
        )
    for page in source:
        if page.rotation:
            page.set_rotation(0)
    stamp_page_numbers(source)

    page_numbers: int = len(source)
    order: list[tuple[int, int]] = impose(page_numbers)
    print(order)

    output: fitz.Document = fitz.open()  # ONE PDF object for everything

    for left_page, right_page in order:
        left_index: int | None = left_page - 1 if left_page else None
        right_index: int | None = right_page - 1 if right_page else None

        # Delegates the actual PDF construction work to the helper function.
        # Passes both the source document (`source`) and the output document (`output`)
        # so the helper can read pages from `source` and append new pages to `output`.
        place_pages_side_by_side(source, output, left_index, right_index)

    verify_booklet(output, order)
    output.save(output_path)
    source.close()
    output.close()
    print("Booklet saved to:", output_path)


if __name__ == "__main__":
    paths: list[str] = shlex.split(input("Provide the input and output paths: "))
    input_path, output_path = paths[0], paths[1]
    build_booklet(input_path, output_path)
