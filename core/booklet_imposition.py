# ----- Built-In Modules -----
import io

# ----- PyMuPDF Modules -----
import fitz

# ----- PikePDF Modules -----
from pikepdf import Array, Dictionary, Name, Object, Page, Pdf, Stream

# ----- Core Modules -----
from core.calculation import impose
from core.verify_booklet import stamp_page_numbers, verify_booklet


def place_pages_side_by_side(
    source: Pdf, output: Pdf, left_index: int | None, right_index: int | None
) -> None:
    """
    Place two pages side-by-side on a new output page.

    Extracts pages from the source PDF at the given indices, scales them to fit
    within half the output page width, and positions them side-by-side on a new
    output page.

    Args:
        source: The source PDF object to read pages from.
        output: The output PDF object to append the new page to.
        left_index: Index of the page to place on the left side, or None if blank.
        right_index: Index of the page to place on the right side, or None if blank.
    """
    page_width, page_height = 841.89, 595.28
    half_width: float = page_width / 2  # half_width = 420.945

    new_page = Page(
        Dictionary(
            Type=Name.Page,
            MediaBox=Array([0, 0, page_width, page_height]),
            Resources=Dictionary(XObject=Dictionary()),
            Contents=Stream(output, b""),
        )
    )

    output.pages.append(new_page)
    page: Page = output.pages[-1]  # get the page we just added

    content_stream = b""

    for side, index in [("L", left_index), ("R", right_index)]:
        if index is None:
            continue

        source_page: Page = source.pages[index]
        xobject: Object = Page(source_page).as_form_xobject()
        page.Resources.XObject[Name(f"/Pg{side}")] = output.copy_foreign(xobject)

        media_box: Array = source_page.mediabox
        source_width: float = float(media_box[2]) - float(media_box[0])
        source_height: float = float(media_box[3]) - float(media_box[1])

        scale: float = min(half_width / source_width, page_height / source_height)
        scaled_width: float = source_width * scale
        scaled_height: float = source_height * scale

        if side == "L":
            x: float = (half_width - scaled_width) / 2
        else:
            x = half_width + (half_width - scaled_width) / 2
        y: float = (page_height - scaled_height) / 2

        content_stream += (
            f"q " f"{scale} 0 0 {scale} {x} {y} cm " f"/Pg{side} Do " f"Q "
        ).encode()

    page.Contents = Stream(output, content_stream)


def build_booklet(input_path: str, output_path: str) -> None:
    """
    Create a booklet-imposed PDF from an input PDF file.

    Reads the PDF at input_path, computes an imposition order using
    core.calculation.impose, places two pages side-by-side per output
    page and writes the resulting PDF to output_path.

    Args:
        input_path: Path to the source PDF file.
        output_path: Path where the imposed PDF will be saved.
    """

    fitz_doc = fitz.open(input_path)
    stamp_page_numbers(fitz_doc)
    stamped_bytes = fitz_doc.tobytes()
    fitz_doc.close()

    source: Pdf = Pdf.open(io.BytesIO(stamped_bytes))

    page_numbers: int = len(source.pages)
    order: list[tuple[int, int]] = impose(page_numbers)
    print(order)

    output: Pdf = Pdf.new()  # ONE pdf object for everything

    for left_page, right_page in order:
        left_index: int | None = left_page - 1 if left_page else None
        right_index: int | None = right_page - 1 if right_page else None

        # Delegates the actual PDF construction work to the helper function.
        # Passes both the source document (`source`) and the output document (`output`)
        # so the helper can read pages from `source` and append new pages to `output`.
        place_pages_side_by_side(source, output, left_index, right_index)

    verify_booklet(output, order)
    output.save(output_path)
    print("Booklet saved to:", output_path)


if __name__ == "__main__":
    paths: list[str] = input("Provide the input and output paths: ").split()
    input_path, output_path = paths[0], paths[1]
    build_booklet(input_path, output_path)
