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
