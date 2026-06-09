import pikepdf
from calculation import impose
from pikepdf import Array, Dictionary, Name, Pdf


def build_booklet(input_path: str, output_path: str):
    src = Pdf.open(input_path)
    n = len(src.pages)
    order = impose(n)

    out = Pdf.new()  # ONE pdf object for everything

    for left_page, right_page in order:
        left_idx = left_page - 1 if left_page else None
        right_idx = right_page - 1 if right_page else None
        place_pages_side_by_side(src, out, left_idx, right_idx)  # pass out in

    out.save(output_path)


def place_pages_side_by_side(
    src: Pdf, out: Pdf, left_idx: int | None, right_idx: int | None
) -> None:
    page_w, page_h = 841.89, 595.28
    half_w = page_w / 2

    new_page = pikepdf.Page(
        pikepdf.Dictionary(
            Type=Name.Page,
            MediaBox=Array([0, 0, page_w, page_h]),
            Resources=Dictionary(XObject=Dictionary()),
            Contents=pikepdf.Stream(out, b""),  # use the shared out
        )
    )
    out.pages.append(new_page)
    page = out.pages[-1]  # get the page we just added

    content_stream = b""

    for side, idx in [("L", left_idx), ("R", right_idx)]:
        if idx is None:
            continue

        src_page = src.pages[idx]
        xobj = pikepdf.Page(src_page).as_form_xobject()
        page.Resources.XObject[Name(f"/Pg{side}")] = out.copy_foreign(xobj)

        media_box = src_page.mediabox
        src_w = float(media_box[2]) - float(media_box[0])
        src_h = float(media_box[3]) - float(media_box[1])

        scale = min(half_w / src_w, page_h / src_h)
        scaled_w = src_w * scale
        scaled_h = src_h * scale

        if side == "L":
            x = (half_w - scaled_w) / 2
        else:
            x = half_w + (half_w - scaled_w) / 2
        y = (page_h - scaled_h) / 2

        content_stream += (
            f"q " f"{scale} 0 0 {scale} {x} {y} cm " f"/Pg{side} Do " f"Q "
        ).encode()

    page.Contents = pikepdf.Stream(out, content_stream)


if __name__ == "__main__":
    input_pdf = "C:\\Users\\Hillcom\\Downloads\\RealityCheck.pdf"
    output_pdf = "C:\\Users\\Hillcom\\Downloads\\RealityCheck_Booklet.pdf"
    build_booklet(input_pdf, output_pdf)
