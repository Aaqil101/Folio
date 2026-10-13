"""Source PDF page counting for the job queue.

Kept in core/ so the UI never imports fitz directly. Reading page_count
only touches the PDF trailer, so this is cheap even for large files.
"""

# ----- Core Modules -----
import fitz


def count_pages(path: str) -> int | None:
    """Return the page count of the PDF at path, or None if unreadable.

    Unreadable means the file is missing, corrupt, or password-protected.
    """
    try:
        with fitz.open(path) as document:
            if document.needs_pass:
                return None
            return document.page_count
    except Exception:
        return None
