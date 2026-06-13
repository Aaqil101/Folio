# ----- PikePDF Modules -----
from pikepdf import Array, Dictionary, Name, Object, Page, Pdf, Stream

# ----- Core Modules -----
from core.calculation import impose


def place_pages_side_by_side(
    source: Pdf, output: Pdf, left_index: int | None, right_index: int | None
) -> None:
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


def build_booklet(input_path: str, output_path: str):
    pass
