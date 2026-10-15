"""
Image-set booklet building for Folio (issue #7).

Treats a set of image files (JPEG, PNG, TIFF, WebP) as the pages of a
booklet: every image becomes one PDF page (normalized to the highest DPI
found in the set), and the wrapped document is imposed through the shared
core.booklet_imposition.impose_document() pipeline unchanged.

Command line:
    python -m core.image_booklet IMG [IMG ...] [-o out.pdf] [--sheet A4]
Accepts image files and/or directories (directories are expanded to the
image files inside them, recursively). Inputs are natural-sorted by
filename unless --keep-order is given.
"""

# ----- Built-In Modules -----
import argparse
import io
import re
from pathlib import Path

# ----- Pillow Modules -----
from PIL import Image, ImageOps, UnidentifiedImageError

# ----- PyMuPDF Modules -----
import fitz

# ----- Core Modules -----
from core.booklet_imposition import impose_document
from core.verify_booklet import BookletVerificationError

# ----- Utils Modules -----
from utils.constants import SHEET_SIZES

# File extensions accepted as booklet pages.
IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}

# Fallback DPI when no image in the set carries valid metadata.
DEFAULT_DPI: float = 72.0

# Anything outside this range is treated as missing metadata (TIFF's
# stock (1, 1) dpi is the usual offender).
_DPI_MIN: float = 2.0
_DPI_MAX: float = 4000.0

# Formats MuPDF's insert_image() embeds natively. Anything else (WebP -
# MuPDF 1.27.2 cannot decode it) is decoded by Pillow and re-encoded as
# lossless PNG before embedding.
_FITZ_NATIVE: set[str] = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

# EXIF tag for orientation.
_EXIF_ORIENTATION: int = 0x0112

_DIGIT_RUN = re.compile(r"(\d+)")


def is_image_path(path: str | Path) -> bool:
    """Return True when the path's extension is a supported image type."""
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def natural_sort(paths: list[Path]) -> list[Path]:
    """
    Sort paths by filename with numeric runs compared as numbers.

    AC ordering method 1: 01.jpg, 02.jpg, ... 10.jpg (plain sorted()
    would put 10.jpg between 01 and 02).
    """

    def key(path: Path) -> list:
        parts: list = []
        for chunk in _DIGIT_RUN.split(path.name.lower()):
            parts.append(int(chunk) if chunk.isdigit() else chunk)
        return parts

    return sorted(paths, key=key)


def collect_images(entries: list[str]) -> list[Path]:
    """
    Expand command-line entries into image files.

    Directories contribute their image files (recursively); explicit
    paths must exist and be images. The result is natural-sorted.
    """
    found: list[Path] = []
    for entry in entries:
        path = Path(entry)
        if path.is_dir():
            found.extend(
                p for p in sorted(path.rglob("*")) if p.is_file() and is_image_path(p)
            )
        elif path.is_file() and is_image_path(path):
            found.append(path)
        elif path.is_file():
            raise ValueError(f"Not a supported image file: {path}")
        else:
            raise FileNotFoundError(f"No such file or directory: {path}")
    return natural_sort(found)


def _read_image_meta(path: Path) -> tuple[int, int, float | None, bool]:
    """
    Read the metadata needed for page layout without decoding pixels.

    Returns:
        (width_px, height_px, dpi_or_None, needs_exif_rotation)
        where dpi is the raw X DPI (None when missing/absurd).
    """
    try:
        with Image.open(path) as image:
            width, height = image.size
            raw_dpi = image.info.get("dpi")
            needs_rotation: bool = (
                image.getexif().get(_EXIF_ORIENTATION, 1) not in (None, 1)
            )
    except (UnidentifiedImageError, OSError) as error:
        raise ValueError(f"Cannot read image: {path} ({error})") from error

    dpi_value: float | None = None
    if raw_dpi:
        try:
            candidate = float(raw_dpi[0])
            if _DPI_MIN <= candidate <= _DPI_MAX:
                dpi_value = candidate
        except (TypeError, ValueError, IndexError):
            dpi_value = None

    return width, height, dpi_value, needs_rotation


def _add_image_page(
    document: fitz.Document,
    path: Path,
    effective_dpi: float,
    target_dpi: float,
    width_px: int,
    height_px: int,
    rotate: bool,
) -> None:
    """
    Append one page to `document`, holding the image sized in inches.

    When the file is a format MuPDF embeds directly (JPEG/PNG/TIFF),
    effective_dpi == target_dpi and no EXIF rotation is needed, the
    original file is embedded as-is (no re-encode). Otherwise the image
    is decoded by Pillow (also the only route for WebP, which MuPDF
    cannot decode), EXIF-corrected and LANCZOS-resampled to the target
    DPI when needed (physical size preserved), then embedded from
    lossless PNG bytes.
    """
    native: bool = path.suffix.lower() in _FITZ_NATIVE
    if native and effective_dpi == target_dpi and not rotate:
        page: fitz.Page = document.new_page(
            width=width_px / target_dpi * 72, height=height_px / target_dpi * 72
        )
        page.insert_image(page.rect, filename=str(path), keep_proportion=True)
        return

    with Image.open(path) as image:
        if rotate:
            image = ImageOps.exif_transpose(image)
        width_px, height_px = image.size
        factor: float = target_dpi / effective_dpi
        if factor != 1.0:
            new_size = (
                max(1, round(width_px * factor)),
                max(1, round(height_px * factor)),
            )
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

    page = document.new_page(
        width=width_px / effective_dpi * 72, height=height_px / effective_dpi * 72
    )
    page.insert_image(page.rect, stream=image_bytes, keep_proportion=True)


def build_image_document(image_paths: list[str] | list[Path]) -> fitz.Document:
    """
    Wrap a set of images into a real one-page-per-image PDF document.

    Page order is the order of image_paths (callers sort first - see
    natural_sort()). DPI normalization: every image is brought to the
    highest valid DPI in the set; images without valid metadata count as
    already being at the target (they are not upscaled). Physical page
    sizes are preserved, so a low-resolution scan next to a 600 DPI
    photo gets a proportionally smaller page and appears softer.

    Raises:
        ValueError: The set is empty or a file cannot be read.
    """
    paths: list[Path] = [Path(p) for p in image_paths]
    if not paths:
        raise ValueError("No images provided.")

    metas = [_read_image_meta(path) for path in paths]
    known_dpis: list[float] = [meta[2] for meta in metas if meta[2] is not None]
    target_dpi: float = max(known_dpis) if known_dpis else DEFAULT_DPI

    document: fitz.Document = fitz.open()
    for path, (width_px, height_px, dpi_value, rotate) in zip(paths, metas):
        effective_dpi: float = dpi_value if dpi_value is not None else target_dpi
        _add_image_page(
            document, path, effective_dpi, target_dpi, width_px, height_px, rotate
        )

    return document


def build_image_booklet(
    image_paths: list[str] | list[Path],
    output_path: str,
    sheet_size: tuple[float, float] = SHEET_SIZES["A4"],
) -> None:
    """
    Create a booklet-imposed PDF from a set of images.

    Arguments:
        image_paths: Image files in the desired page order.
        output_path: Path where the imposed PDF will be saved.
        sheet_size: (width, height) of the landscape output sheet.

    Raises:
        ValueError: The set is empty or an image cannot be read.
        BookletVerificationError: The imposed sheets failed stamp
            verification; nothing is written to output_path.
    """
    source: fitz.Document = build_image_document(image_paths)
    try:
        impose_document(source, output_path, sheet_size)
    finally:
        source.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Impose a set of images into a booklet PDF."
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="Image files and/or directories containing images",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path of the imposed booklet PDF to write",
    )
    parser.add_argument(
        "--sheet",
        choices=sorted(SHEET_SIZES),
        default="A4",
        help="Landscape sheet size (default: A4)",
    )
    parser.add_argument(
        "--keep-order",
        action="store_true",
        help="Keep the given file order instead of natural-sorting by name",
    )
    args = parser.parse_args()

    try:
        paths: list[Path] = collect_images(args.images)
        if not paths:
            raise ValueError("No images found in the given entries.")
        if not args.keep_order:
            paths = natural_sort(paths)
        build_image_booklet(paths, args.output, SHEET_SIZES[args.sheet])
    except FileNotFoundError as error:
        parser.error(str(error))
    except (ValueError, BookletVerificationError) as error:
        print(f"FAILED  {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
