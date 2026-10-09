# ----- Built-In Modules -----
import argparse
import sys
from pathlib import Path

# ----- Pillow Modules -----
from PIL import Image, ImageDraw, ImageFont

# ----- Utils Modules -----
from utils.constants import REPO_ROOT
from utils.format_utils import zero_padding

# ----- Module-Level Constants -----
IMAGES_DIR: Path = REPO_ROOT / "test_pdfs" / "images"

DEFAULT_COUNT: int = 8
DEFAULT_SIZE: tuple[int, int] = (1200, 1600)
DEFAULT_DPI: int = 150
DEFAULT_FORMAT: str = "png"
DEFAULT_BOX_FRAC: float = 0.6

TEXT_FRAC: float = 0.5
FONT_CANDIDATES: tuple[str, ...] = (
    "arialbd.ttf",
    "arial.ttf",
    "DejaVuSans-Bold.ttf",
    "DejaVuSans.ttf",
)
FORMAT_EXTENSIONS: dict[str, str] = {
    "png": "png",
    "jpg": "jpg",
    "jpeg": "jpg",
    "webp": "webp",
    "avif": "avif",
    "tiff": "tiff",
}
DPI_FORMATS: frozenset[str] = frozenset({"png", "jpg", "jpeg", "tiff"})


# ----- Function Definitions -----
def load_font(size: int) -> ImageFont.ImageFont:
    """
    Return the first available bold-ish font at the requested pixel size.

    Tries each candidate in FONT_CANDIDATES and falls back to Pillow's
    bundled scalable font when none of them are installed.

    Arguments:
        size: The font size in pixels.
    Returns:
        A font object usable with ImageDraw.text().
    """
    for name in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def draw_numbered_image(
    draw: ImageDraw.ImageDraw,
    label: int,
    size: tuple[int, int],
    box_frac: float,
) -> None:
    """
    Draw a centred numbered box onto an image.

    The box occupies box_frac of the image width and height, so it stays
    centred and visible at any resolution or aspect ratio. The number is
    rendered in bold black text centred both horizontally and vertically.

    Arguments:
        draw: An ImageDraw.ImageDraw to draw onto.
        label: The integer to draw centred in the box.
        size: A (width, height) tuple of the image in pixels.
        box_frac: Fraction of each image dimension the box should occupy.
    """
    width, height = size

    box_w: int = int(width * box_frac)
    box_h: int = int(height * box_frac)
    box_x: int = (width - box_w) // 2
    box_y: int = (height - box_h) // 2
    line_width: int = max(2, min(width, height) // 100)

    draw.rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        outline="black",
        width=line_width,
    )

    font: ImageFont.ImageFont = load_font(int(min(box_w, box_h) * TEXT_FRAC))
    text: str = zero_padding(label)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_x: float = width / 2 - (left + right) / 2
    text_y: float = height / 2 - (top + bottom) / 2
    draw.text((text_x, text_y), text, font=font, fill="black")


def generate_test_images(
    count: int,
    folder: str,
    labels: list[int],
    sizes: list[tuple[int, int]],
    dpis: list[int],
    fmt: str,
    name_from_label: bool,
    box_frac: float,
) -> Path:
    """
    Generate a batch of numbered test images.

    Arguments:
        count: Number of images to generate.
        folder: Batch folder name, created under test_pdfs/images/.
        labels: One number to draw per image (length must equal count).
        sizes: Candidate (width, height) pixel sizes, cycled across the batch.
        dpis: Candidate DPI values, cycled across the batch.
        fmt: Output format key (png, jpg, jpeg, webp, avif, tiff).
        name_from_label: Name each file after its label instead of its position.
        box_frac: Fraction of each image dimension the box should occupy.
    Returns:
        The folder the images were written to.
    """
    extension: str = FORMAT_EXTENSIONS[fmt]
    output_dir: Path = IMAGES_DIR / folder
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, label in enumerate(labels, start=1):
        size: tuple[int, int] = sizes[(index - 1) % len(sizes)]
        dpi: int = dpis[(index - 1) % len(dpis)]

        image: Image.Image = Image.new("RGB", size, "white")
        draw_numbered_image(ImageDraw.Draw(image), label, size, box_frac)

        stem: str = zero_padding(label if name_from_label else index)
        path: Path = output_dir / f"{stem}.{extension}"

        save_kwargs: dict[str, object] = {}
        if fmt in DPI_FORMATS:
            save_kwargs["dpi"] = (dpi, dpi)
        image.save(path, **save_kwargs)

    print(f"Generated {zero_padding(count)} images → {output_dir}")
    return output_dir


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Generate numbered test images for Folio image-input testing."
    )

    # Batch settings
    batch_group: argparse._ArgumentGroup = parser.add_argument_group("Batch settings")
    batch_group.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of images to generate (default: 08, or len(--labels))",
    )
    batch_group.add_argument(
        "--folder",
        type=str,
        default=None,
        help="Batch folder name under test_pdfs/images/ (default: batch_<count>_<format>)",
    )
    batch_group.add_argument(
        "--labels",
        type=str,
        default=None,
        help="Comma-separated numbers to draw, e.g. 5,1,4,2 (default: sequential 1..count)",
    )
    batch_group.add_argument(
        "--name-from-label",
        action="store_true",
        help="Name each file after its drawn number instead of its position",
    )

    # Image settings
    image_group: argparse._ArgumentGroup = parser.add_argument_group("Image settings")
    image_group.add_argument(
        "--size",
        type=int,
        nargs=2,
        action="append",
        metavar=("WIDTH", "HEIGHT"),
        help="Image size in pixels; repeat to cycle sizes across the batch "
        f"(default: {DEFAULT_SIZE[0]} {DEFAULT_SIZE[1]})",
    )
    image_group.add_argument(
        "--dpi",
        type=int,
        action="append",
        help="DPI metadata; repeat to cycle DPIs across the batch "
        f"(default: {DEFAULT_DPI})",
    )
    image_group.add_argument(
        "--format",
        type=str,
        default=DEFAULT_FORMAT,
        choices=sorted(FORMAT_EXTENSIONS),
        help=f"Output format (default: {DEFAULT_FORMAT})",
    )
    image_group.add_argument(
        "--box-frac",
        type=float,
        default=DEFAULT_BOX_FRAC,
        help="Fraction of the image the box occupies (default: 0.6)",
    )

    args: argparse.Namespace = parser.parse_args()

    if args.count is not None and args.count < 1:
        parser.error("--count must be at least 1")
    if not 0.1 <= args.box_frac <= 0.95:
        parser.error("--box-frac must be between 0.1 and 0.95")

    if args.labels is None:
        count: int = args.count if args.count is not None else DEFAULT_COUNT
        labels: list[int] = list(range(1, count + 1))
    else:
        try:
            labels = [int(part) for part in args.labels.split(",") if part.strip()]
        except ValueError:
            parser.error("--labels must be a comma-separated list of integers")
        count = len(labels)
        if count < 1:
            parser.error("--labels must contain at least one value")
        if args.count is not None and args.count != count:
            parser.error(f"--labels has {count} values but --count is {args.count}")
        if len(set(labels)) != count:
            parser.error("--labels values must be unique")

    sizes: list[tuple[int, int]] = (
        [(w, h) for w, h in args.size] if args.size else [DEFAULT_SIZE]
    )
    if any(w < 1 or h < 1 for w, h in sizes):
        parser.error("--size width and height must be at least 1")

    dpis: list[int] = args.dpi if args.dpi else [DEFAULT_DPI]
    if any(d < 1 for d in dpis):
        parser.error("--dpi must be at least 1")

    fmt: str = "jpg" if args.format == "jpeg" else args.format
    folder: str = args.folder or f"batch_{zero_padding(count)}_{fmt}"

    generate_test_images(
        count, folder, labels, sizes, dpis, fmt, args.name_from_label, args.box_frac
    )


if __name__ == "__main__":
    main()
