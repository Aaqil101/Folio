import fitz

from utils.constants import A4_LANDSCAPE
from utils.format_utils import zero_padding

PAGE_WIDTH: float = A4_LANDSCAPE[0]
HALF_WIDTH: float = PAGE_WIDTH / 2
STAMP_FONT_SIZE: float = 6.0
STAMP_RENDER_MODE: int = 3  # Tr 3 — invisible text


class BookletVerificationError(RuntimeError):
    """Raised when an imposed booklet fails stamp verification."""


def stamp_page_numbers(source: fitz.Document) -> None:
    for index, page in enumerate(source, start=1):
        media = page.mediabox
        page.insert_text(
            fitz.Point(media.x0 + 5, media.y0 + 15),
            zero_padding(index, width=4),
            fontsize=STAMP_FONT_SIZE,
            render_mode=STAMP_RENDER_MODE,
        )


def _extract_side_numbers(
    page: fitz.Page,
    half_width: float,
) -> tuple[list[str], list[str]]:
    left: list[str] = []
    right: list[str] = []
    for word in page.get_text("words"):
        x0, _y0, x1, _y1, text, *_ = word
        x_center = (x0 + x1) / 2
        (left if x_center < half_width else right).append(text.strip())
    return left, right


def _check_side(
    sheet_num: int,
    side_label: str,
    expected_page: int,
    found_texts: list[str],
) -> bool:
    if expected_page == 0:
        if found_texts:
            print(
                f"  FAIL  Sheet {sheet_num:>3} {side_label}: expected blank, got {found_texts}"
            )
            return False
        return True

    expected_str = zero_padding(expected_page, width=4)
    if expected_str in found_texts:
        return True

    print(
        f"  FAIL  Sheet {sheet_num:>3} {side_label}: expected '{expected_str}', got {found_texts}"
    )
    return False


def verify_booklet(output: fitz.Document, order: list[tuple[int, int]]) -> bool:
    total_sheets = len(order)
    passed = 0
    failed = 0

    print(f"\nVerifying {total_sheets} sheets...")

    for sheet_index, (expected_left, expected_right) in enumerate(order):
        sheet_num = sheet_index + 1
        fitz_page: fitz.Page = output[sheet_index]

        left_found, right_found = _extract_side_numbers(fitz_page, HALF_WIDTH)

        left_ok = _check_side(sheet_num, "LEFT ", expected_left, left_found)
        right_ok = _check_side(sheet_num, "RIGHT", expected_right, right_found)

        if left_ok and right_ok:
            passed += 1
        else:
            failed += 1

    print(f"\nResult: {passed}/{total_sheets} sheets passed, {failed} failed.")
    return failed == 0
