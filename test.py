# ----- Build-In Modules -----
import math

pages = 17


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


print(calculate_pages(pages))
