# ----- Build-In Modules -----
import math


def calculate_pages(pages) -> int:
    """
    Return the total number of pages after padding to a multiple of 4.

    Folios are printed in sheets of 4 pages, so this function computes the
    smallest page count that is divisible by 4 and returns that total.

    Example:
        >>> calculate_pages(17) -> 20
    """
    padded: int = math.ceil(pages / 4) * 4
    blanks_needed: int = padded - pages

    return blanks_needed + pages


def get_imposition_order(number_pages: int) -> list[tuple[int, int]]:
    """
    Generate the page imposition order for booklet printing.

    Pages are arranged so that when sheets are printed double-sided,
    folded, and stacked, the pages appear in the correct reading order.

    If the page count is not a multiple of 4, the total number of pages
    is padded to the next multiple of 4 using ``calculate_pages()``.

    Args:
        number_pages: Total number of pages in the document.

    Returns:
        A list of ``(left_page, right_page)`` tuples representing the
        printing order for each side of each sheet. The first tuple is
        the front side of the first sheet, the second tuple is the back
        side, and so on.

    Example:
        >>> get_imposition_order(8)
        [(8, 1), (2, 7), (6, 3), (4, 5)]

        This corresponds to:

        Sheet 1:
            Front: (8, 1)
            Back:  (2, 7)

        Sheet 2:
            Front: (6, 3)
            Back:  (4, 5)

    Example with padding:
        >>> get_imposition_order(6)
        [(8, 1), (2, 7), (6, 3), (4, 5)]

        Since 6 is not divisible by 4, the document is padded to 8 pages
        before calculating the imposition order.
    """
    # If the number of pages is not a multiple of 4, calculate the total number of pages after padding.
    if number_pages % 4 != 0:
        number_pages = calculate_pages(number_pages)

    sheets: list[tuple[int, int]] = []
    start: int = 1
    end: int = number_pages

    while start < end:
        # front of sheet (left, right)
        sheets.append((end, start))
        start += 1
        end -= 1

        # back of sheet (left, right)
        sheets.append((start, end))
        start += 1
        end -= 1

    return sheets


def impose(number_pages: int) -> list[tuple[int, int]]:
    order: list[tuple[int, int]] = get_imposition_order(number_pages)
    # Remap page numbers > number_pages to 0 (blank)
    return [
        (l if l <= number_pages else 0, r if r <= number_pages else 0) for l, r in order
    ]


if __name__ == "__main__":
    user_input: int = int(input("Enter the number of pages in the document: "))
    imposition_order: list[tuple[int, int]] = impose(user_input)
    print(imposition_order)
