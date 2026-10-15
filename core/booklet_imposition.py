# ----- Built-In Modules -----
import shlex

# ----- PyMuPDF Modules -----
import fitz

# ----- Core Modules -----
from core.calculation import impose
from core.verify_booklet import (
    BookletVerificationError,
    stamp_page_numbers,
    verify_booklet,
)

# ----- Utils Modules -----
from utils.constants import A4_LANDSCAPE


def place_pages_side_by_side(
    source: fitz.Document,
    output: fitz.Document,
    left_index: int | None,
    right_index: int | None,
    sheet_size: tuple[float, float] = A4_LANDSCAPE,
) -> None:
    """Compose one landscape output page from a left and a right source page.

    Appends a single landscape page (sheet_size, default A4_LANDSCAPE) to
    `output` and treats it as two halves split at half the width. Each side
    whose index is not None is drawn from `source`, scaled uniformly (aspect
    ratio preserved) to the largest size that fits inside its half, and
    centred both horizontally and vertically within that half. A side whose
    index is None (the sentinel produced by core.calculation.impose for
    padding pages) is left blank, so the new page may hold one real page,
    two, or none.

    Arguments:
        source: Document the pages are copied from.
        output: Document that receives the new composed page.
        left_index: 0-based index in `source` for the left half, or None for blank.
        right_index: 0-based index in `source` for the right half, or None for blank.
        sheet_size: (width, height) of the landscape output sheet.
    """
    page_width, page_height = sheet_size
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


def impose_document(
    source: fitz.Document,
    output_path: str,
    sheet_size: tuple[float, float] = A4_LANDSCAPE,
) -> None:
    """
    Impose an already-open source document into a booklet PDF.

    Shared by build_booklet() (PDF files) and core.image_booklet
    (image sets wrapped into a PDF document first). Clears any /Rotate
    flags, stamps every source page with its invisible page number,
    imposes two pages per sheet, verifies the result, and saves it.

    Arguments:
        source: An open PDF document (already rotation-cleared is fine;
            this function clears /Rotate itself).
        output_path: Path where the imposed PDF will be saved.
        sheet_size: (width, height) of the landscape output sheet.

    Raises:
        ValueError: The source is password-protected.
        BookletVerificationError: The imposed sheets failed stamp
            verification; nothing is written to output_path.
    """
    if source.needs_pass:
        raise ValueError(
            "Source PDF is password-protected and cannot be imposed."
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
        # Passes the source document (`source`), the output document (`output`)
        # and the chosen sheet size so the helper can read pages from `source`
        # and append new pages to `output`.
        place_pages_side_by_side(source, output, left_index, right_index, sheet_size)

    if not verify_booklet(output, order, sheet_size):
        output.close()
        raise BookletVerificationError(
            f"Verification failed for {page_numbers} pages; booklet not saved."
        )
    output.save(output_path)
    output.close()
    print("Booklet saved to:", output_path)


def build_booklet(
    input_path: str,
    output_path: str,
    sheet_size: tuple[float, float] = A4_LANDSCAPE,
) -> None:
    """
    Create a booklet-imposed PDF from an input PDF file.

    Reads the PDF at input_path and delegates to impose_document().

    Arguments:
        input_path: Path to the source PDF file.
        output_path: Path where the imposed PDF will be saved.
        sheet_size: (width, height) of the landscape output sheet.

    Raises:
        ValueError: The source is not a PDF, or is password-protected.
        BookletVerificationError: The imposed sheets failed stamp
            verification; nothing is written to output_path.
    """
    source: fitz.Document = fitz.open(input_path)
    if not source.is_pdf:
        source.close()
        raise ValueError(
            f"Input is not a PDF (use core.image_booklet for images): {input_path}"
        )
    try:
        impose_document(source, output_path, sheet_size)
    finally:
        source.close()


if __name__ == "__main__":
    paths: list[str] = shlex.split(input("Provide the input and output paths: "))
    input_path, output_path = paths[0], paths[1]
    try:
        build_booklet(input_path, output_path)
    except (ValueError, BookletVerificationError) as error:
        print(f"FAILED  {error}")
        raise SystemExit(1)
