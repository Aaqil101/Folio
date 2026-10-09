# ----- Built-In Modules -----
import argparse
import contextlib
import hashlib
import io
import json
import re
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

# ----- PyMuPDF Modules -----
import fitz

# ----- Core Modules -----
from core.booklet_imposition import build_booklet
from core.calculation import impose
from core.generate_test_pdf import generate_test_pdf
from core.verify_booklet import stamp_page_numbers, verify_booklet

# ----- Utils Modules -----
from utils.constants import A4_LANDSCAPE, PAGE_HEIGHT, PAGE_WIDTH

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
SYNTHETIC_DIR: Path = REPO_ROOT / "test_pdfs" / "inputs" / "synthetic"
REAL_DIR: Path = REPO_ROOT / "test_pdfs" / "inputs" / "real"
OUTPUT_DIR: Path = REPO_ROOT / "test_pdfs" / "outputs"

SHEET_W: float = A4_LANDSCAPE[0]
SHEET_H: float = A4_LANDSCAPE[1]
HALF_W: float = SHEET_W / 2

REAL_FILES: dict[str, str] = {
    "arxiv_attention_15p.pdf": "https://arxiv.org/pdf/1706.03762v7",
    "irs_w4_form_letter.pdf": "https://www.irs.gov/pub/irs-pdf/fw4.pdf",
}
REAL_ZIP_URL: str = "https://docs.python.org/3.13/archives/python-3.13-docs-pdf-a4.zip"
REAL_ZIP_MEMBERS: tuple[str, ...] = ("tutorial.pdf", "library.pdf")

QUICK_MAX_PAGES: int = 200
QUICK_GEOM_SAMPLE: int = 12
DOWNLOAD_RETRIES: int = 3

CACHE_PATH: Path = REPO_ROOT / "test_pdfs" / "run_cache.json"
FAILURES_DIR: Path = REPO_ROOT / "test_pdfs" / "failures"
CODE_PATHS: tuple[str, ...] = (
    "core/manual_test_suite.py",
    "core/booklet_imposition.py",
    "core/calculation.py",
    "core/verify_booklet.py",
    "core/generate_test_pdf.py",
    "utils/format_utils.py",
    "utils/constants.py",
)

GEOM_DPI: int = 36
GEOM_SAMPLE_SHEETS: int = 48
GEOM_DIFF_MAX: float = 0.10
GEOM_CHANNEL_TOL: int = 60
GEOM_WHITE: int = 250


def make_numbered(path: Path, pages: int) -> None:
    generate_test_pdf(pages, str(path), (400, 400), 192, 10)


def make_rotated_mixed(path: Path) -> None:
    doc: fitz.Document = fitz.open()
    for i in range(4):
        if i == 2:
            page: fitz.Page = doc.new_page(width=612, height=792)
        else:
            page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        label: str = f"Page {i + 1}"
        if i == 0:
            label += " rotated 90"
            page.set_rotation(90)
        if i == 2:
            label += " US Letter"
        page.insert_text((72, 100), label, fontsize=36)
    doc.save(str(path))
    doc.close()


def make_asymmetric(path: Path) -> None:
    doc: fitz.Document = fitz.open()
    for i in range(4):
        page: fitz.Page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        page.draw_rect(page.rect, color=(0.75, 0.75, 0.75))
        box: fitz.Rect = fitz.Rect(0, 0, 150, 150)
        if i % 2 == 1:
            box.x1 = PAGE_WIDTH
            box.x0 = PAGE_WIDTH - 150
        if i >= 2:
            box.y1 = PAGE_HEIGHT
            box.y0 = PAGE_HEIGHT - 150
        page.draw_rect(box, color=(0.85, 0.2, 0.2), fill=(0.95, 0.75, 0.75))
        page.insert_text((box.x0 + 20, box.y0 + 40), f"P{i + 1}", fontsize=28)
    doc.save(str(path))
    doc.close()


def make_annotations(path: Path) -> None:
    doc: fitz.Document = fitz.open()
    for i in range(8):
        page: fitz.Page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        page.insert_text((72, 100), f"Page {i + 1}", fontsize=36)
        if i == 0:
            page.insert_link(
                {
                    "kind": fitz.LINK_URI,
                    "from": fitz.Rect(72, 120, 320, 150),
                    "uri": "https://example.com",
                }
            )
            page.insert_text((72, 140), "This is a link annotation", fontsize=18)
        if i == 1:
            hits: list[fitz.Rect] = page.search_for("Page 2")
            if hits:
                page.add_highlight_annot(hits)
            page.insert_text((72, 170), "This is a highlight annotation", fontsize=18)
    doc.set_toc([[1, "Chapter 1", 1], [1, "Chapter 2", 5]])
    doc.save(str(path))
    doc.close()


def make_encrypted(path: Path, source_path: Path) -> None:
    src: fitz.Document = fitz.open(source_path)
    src.save(
        str(path),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw="folio",
        owner_pw="folio-owner",
    )
    src.close()


def ensure_synthetic_inputs(regen: bool) -> None:
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    numbered_8p: Path = SYNTHETIC_DIR / "numbered_08p.pdf"
    builders: list[tuple[Path, object]] = [
        (SYNTHETIC_DIR / "numbered_09p.pdf", lambda p: make_numbered(p, 9)),
        (SYNTHETIC_DIR / "numbered_16p.pdf", lambda p: make_numbered(p, 16)),
        (SYNTHETIC_DIR / "rotated_mixed.pdf", make_rotated_mixed),
        (SYNTHETIC_DIR / "asymmetric.pdf", make_asymmetric),
        (SYNTHETIC_DIR / "annotations_bookmarks.pdf", make_annotations),
        (numbered_8p, lambda p: make_numbered(p, 8)),
        (
            SYNTHETIC_DIR / "encrypted_aes256.pdf",
            lambda p: make_encrypted(p, numbered_8p),
        ),
        (SYNTHETIC_DIR / "stress_500p.pdf", lambda p: make_numbered(p, 500)),
    ]
    for path, builder in builders:
        if regen or not path.exists():
            builder(path)


def _looks_like_pdf(data: bytes) -> bool:
    return b"%PDF" in data[:1024]


def _download(url: str, dest: Path) -> None:
    request = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Folio manual test suite)"}
    )
    last_error: Exception | None = None
    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data: bytes = response.read()
            if dest.suffix.lower() == ".pdf" and not _looks_like_pdf(data):
                raise ValueError(f"response is not a PDF ({len(data)} bytes)")
            dest.write_bytes(data)
            return
        except Exception as error:
            last_error = error
            if attempt < DOWNLOAD_RETRIES:
                print(f"download attempt {attempt} failed for {url}: {error}")
    raise RuntimeError(
        f"download failed after {DOWNLOAD_RETRIES} attempts: {last_error}"
    )


def ensure_real_inputs(offline: bool) -> list[str]:
    REAL_DIR.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    missing_files: list[str] = [
        name for name in REAL_FILES if not (REAL_DIR / name).exists()
    ]
    missing_zip: list[str] = [
        name for name in REAL_ZIP_MEMBERS if not (REAL_DIR / name).exists()
    ]

    if offline:
        for name in missing_files + missing_zip:
            warnings.append(f"offline: {name} not present, case skipped")
        return warnings

    for name in missing_files:
        try:
            _download(REAL_FILES[name], REAL_DIR / name)
            print(f"downloaded {name}")
        except Exception as error:
            warnings.append(f"download failed {name}: {error}")

    if missing_zip:
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            _download(REAL_ZIP_URL, tmp_path)
            with zipfile.ZipFile(tmp_path) as bundle:
                for entry in bundle.infolist():
                    base: str = Path(entry.filename).name
                    if base in missing_zip:
                        member: bytes = bundle.read(entry)
                        if not _looks_like_pdf(member):
                            warnings.append(f"zip member {base} is not a PDF, skipped")
                            continue
                        (REAL_DIR / base).write_bytes(member)
                        print(f"downloaded {base}")
            tmp_path.unlink(missing_ok=True)
        except Exception as error:
            warnings.append(f"download failed {REAL_ZIP_URL}: {error}")
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
    return warnings


def _page_count(path: Path) -> int | None:
    try:
        document: fitz.Document = fitz.open(str(path))
        pages: int = len(document)
        document.close()
        return pages
    except Exception:
        return None


def collect_inputs(quick: bool, only: str | None) -> list[Path]:
    inputs: list[Path] = sorted(SYNTHETIC_DIR.glob("*.pdf")) + sorted(
        REAL_DIR.glob("*.pdf")
    )
    if quick:
        kept: list[Path] = []
        for path in inputs:
            pages: int | None = _page_count(path)
            if pages is None or pages <= QUICK_MAX_PAGES:
                kept.append(path)
        inputs = kept
    if only:
        inputs = [p for p in inputs if only.lower() in p.name.lower()]
    return inputs


def clean_stale_outputs(valid_names: set[str]) -> None:
    if not OUTPUT_DIR.exists():
        return
    for path in OUTPUT_DIR.glob("*.pdf"):
        if path.name not in valid_names:
            path.unlink()
            print(f"removed stale output {path.name}")


def _file_fingerprint(path: Path) -> str:
    stat = path.stat()
    return f"{stat.st_size}:{stat.st_mtime_ns}"


def _code_fingerprint() -> str:
    digest = hashlib.sha256()
    for relative in CODE_PATHS:
        source: Path = REPO_ROOT / relative
        if source.exists():
            digest.update(source.read_bytes())
    return digest.hexdigest()[:16]


def _load_cache() -> dict:
    try:
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if not isinstance(cache, dict):
            raise ValueError("cache is not an object")
        return cache
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8"
    )


def _cache_entry(src: Path, cache: dict) -> dict | None:
    entry: dict | None = cache.get(src.name)
    if not isinstance(entry, dict):
        return None
    return entry


def _resolve_sample(quick: bool, sample: int | None) -> int:
    if sample is not None:
        return sample
    return QUICK_GEOM_SAMPLE if quick else GEOM_SAMPLE_SHEETS


def _cache_hit(
    entry: dict | None,
    code_fp: str,
    src: Path,
    dst: Path,
    geometry: bool,
    sample: int,
) -> bool:
    if entry is None or not dst.exists():
        return False
    if entry.get("code") != code_fp or entry.get("src") != _file_fingerprint(src):
        return False
    if geometry:
        if entry.get("sample") != sample:
            return False
        if str(entry.get("geometry", "")) in ("skipped", "n/a", "-"):
            return False
    return True


def _sampled_sheet_indices(total: int, sample: int) -> list[int]:
    if total <= sample:
        return list(range(total))
    return sorted(
        {round(k * (total - 1) / (sample - 1)) for k in range(sample)}
    )


def _expected_sheet(
    baked: fitz.Document, left_page: int, right_page: int
) -> fitz.Document:
    sheet: fitz.Document = fitz.open()
    output: fitz.Page = sheet.new_page(width=SHEET_W, height=SHEET_H)
    for page_number, x0 in ((left_page, 0.0), (right_page, HALF_W)):
        if not page_number:
            continue
        media: fitz.Rect = baked[page_number - 1].mediabox
        scale: float = min(HALF_W / media.width, SHEET_H / media.height)
        scaled_w: float = media.width * scale
        scaled_h: float = media.height * scale
        x: float = x0 + (HALF_W - scaled_w) / 2
        y: float = (SHEET_H - scaled_h) / 2
        output.show_pdf_page(
            fitz.Rect(x, y, x + scaled_w, y + scaled_h),
            baked,
            page_number - 1,
            clip=media,
        )
    return sheet


def _content_diff_ratio(actual: bytes, expected: bytes) -> float:
    if len(actual) != len(expected) or not actual:
        return 1.0
    content: int = 0
    mismatches: int = 0
    for a, b in zip(actual, expected):
        if a < GEOM_WHITE or b < GEOM_WHITE:
            content += 1
            if abs(a - b) > GEOM_CHANNEL_TOL:
                mismatches += 1
    if not content:
        return 0.0
    return mismatches / content


def _dump_geometry_artifact(
    stem_dir: Path, sheet_no: int, actual: fitz.Page, expected: fitz.Page
) -> None:
    stem_dir.mkdir(parents=True, exist_ok=True)
    actual.get_pixmap(dpi=72).save(stem_dir / f"sheet_{sheet_no:03d}_actual.png")
    expected.get_pixmap(dpi=72).save(stem_dir / f"sheet_{sheet_no:03d}_expected.png")
    actual_gray: fitz.Pixmap = actual.get_pixmap(dpi=GEOM_DPI, colorspace=fitz.csGRAY)
    expected_gray: fitz.Pixmap = expected.get_pixmap(
        dpi=GEOM_DPI, colorspace=fitz.csGRAY
    )
    a: bytes = actual_gray.samples
    b: bytes = expected_gray.samples
    if len(a) != len(b) or not a:
        return
    rgb: bytearray = bytearray(3 * len(a))
    for i, (av, bv) in enumerate(zip(a, b)):
        if (av < GEOM_WHITE or bv < GEOM_WHITE) and abs(av - bv) > GEOM_CHANNEL_TOL:
            rgb[3 * i : 3 * i + 3] = b"\xff\x00\x00"
        else:
            dimmed: int = av // 2
            rgb[3 * i : 3 * i + 3] = bytes((dimmed, dimmed, dimmed))
    fitz.Pixmap(
        fitz.csRGB, actual_gray.width, actual_gray.height, bytes(rgb), False
    ).save(stem_dir / f"sheet_{sheet_no:03d}_diff.png")


def geometry_check(
    src_path: Path,
    dst_path: Path,
    sample: int = GEOM_SAMPLE_SHEETS,
    artifacts: bool = True,
) -> tuple[bool, str]:
    source: fitz.Document = fitz.open(src_path)
    for page in source:
        if page.rotation:
            page.set_rotation(0)
    stamp_page_numbers(source)

    order: list[tuple[int, int]] = impose(len(source))
    output: fitz.Document = fitz.open(dst_path)
    if sample <= 0:
        sample = len(order)
    indices: list[int] = _sampled_sheet_indices(len(order), sample)

    worst: float = 0.0
    failures: list[str] = []
    stem_dir: Path = FAILURES_DIR / src_path.stem
    for index in indices:
        left_page, right_page = order[index]
        if index >= len(output):
            failures.append(f"sheet {index + 1}: missing in output")
            continue
        expected: fitz.Document = _expected_sheet(source, left_page, right_page)
        actual_gray: bytes = output[index].get_pixmap(
            dpi=GEOM_DPI, colorspace=fitz.csGRAY
        ).samples
        expected_gray: bytes = expected[0].get_pixmap(
            dpi=GEOM_DPI, colorspace=fitz.csGRAY
        ).samples
        ratio: float = _content_diff_ratio(actual_gray, expected_gray)
        worst = max(worst, ratio)
        if ratio > GEOM_DIFF_MAX:
            failures.append(f"sheet {index + 1}: {ratio:.1%} of content differs")
            if artifacts:
                _dump_geometry_artifact(stem_dir, index + 1, output[index], expected[0])
        expected.close()

    source.close()
    output.close()

    sampled: str = (
        f"all {len(order)} sheets"
        if len(indices) == len(order)
        else f"{len(indices)}/{len(order)} sheets sampled"
    )
    if failures:
        return False, f"FAIL ({'; '.join(failures[:3])})"
    return True, f"ok ({sampled}, worst diff {worst:.2%})"


def _quiet_verify(dst_path: Path, pages: int) -> tuple[bool, list[int], str]:
    order: list[tuple[int, int]] = impose(pages)
    output: fitz.Document = fitz.open(dst_path)
    buffer: io.StringIO = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        passed: bool = verify_booklet(output, order)
    output.close()
    log: str = buffer.getvalue()
    failed_sheets: list[int] = sorted(
        {int(number) for number in re.findall(r"FAIL\s+Sheet\s+(\d+)", log)}
    )
    return passed, failed_sheets, log


def _dump_verify_artifacts(
    stem_dir: Path, dst_path: Path, log: str, failed_sheets: list[int]
) -> None:
    stem_dir.mkdir(parents=True, exist_ok=True)
    (stem_dir / "verify.log").write_text(log, encoding="utf-8")
    output: fitz.Document = fitz.open(str(dst_path))
    for sheet_no in failed_sheets:
        if 0 < sheet_no <= len(output):
            output[sheet_no - 1].get_pixmap(dpi=72).save(
                stem_dir / f"verify_sheet_{sheet_no:03d}.png"
            )
    output.close()


def _oracle_canary() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src: Path = Path(tmp) / "canary_in.pdf"
        dst: Path = Path(tmp) / "canary_out.pdf"
        tampered: Path = Path(tmp) / "canary_tampered.pdf"
        make_numbered(src, 8)
        build_booklet(str(src), str(dst))
        ok, message = geometry_check(src, dst, artifacts=False)
        if not ok:
            raise RuntimeError(f"pristine output failed the oracle: {message}")
        document: fitz.Document = fitz.open(str(dst))
        document[0].draw_rect(
            document[0].rect, color=(0, 0, 0), fill=(0, 0, 0)
        )
        document.save(str(tampered))
        document.close()
        ok, message = geometry_check(src, tampered, artifacts=False)
        if ok:
            raise RuntimeError("tampered output passed the oracle")
    print("oracle canary: ok (pristine passes, tampered fails)")


def run_suite(
    quick: bool,
    only: str | None,
    offline: bool,
    geometry: bool,
    force: bool,
    sample: int | None = None,
) -> int:
    inputs: list[Path] = collect_inputs(quick, only)
    if not inputs:
        print("No inputs matched.")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if only is None:
        clean_stale_outputs({p.name for p in inputs})

    cache: dict = {} if force else _load_cache()
    code_fp: str = _code_fingerprint()
    geom_sample: int = _resolve_sample(quick, sample)
    cache_changed: bool = False

    rows: list[tuple[str, str, str, str, str, str, str]] = []
    failures: int = 0
    skipped_cache: int = 0

    for src in inputs:
        dst: Path = OUTPUT_DIR / src.name
        probe: fitz.Document = fitz.open(src)
        pages: int = len(probe)
        needs_pass: bool = probe.needs_pass
        probe.close()
        sheets: int = (pages + 3) // 4

        entry: dict | None = _cache_entry(src, cache)
        cache_hit: bool = (
            not force
            and _cache_hit(entry, code_fp, src, dst, geometry, geom_sample)
        )

        print("=" * 70)
        print(f"Input: {src.name} ({pages} pages, {sheets} sheets expected)")
        print("=" * 70)

        if cache_hit:
            skipped_cache += 1
            verify_cell: str = str(entry.get("verify", "-"))
            geom_cell: str = str(entry.get("geometry", "-"))
            rows.append(
                (src.name, str(pages), str(sheets), verify_cell, geom_cell, "-", "cached")
            )
            print(f"cached (unchanged since last run; verify {verify_cell}, geometry {geom_cell})")
            print()
            continue

        start: float = time.perf_counter()
        status: str = "OK"
        verify_cell = "n/a"
        geom_cell = "n/a"
        stem_dir: Path = FAILURES_DIR / src.stem
        shutil.rmtree(stem_dir, ignore_errors=True)

        try:
            build_booklet(str(src), str(dst))
        except ValueError as error:
            elapsed: float = time.perf_counter() - start
            if needs_pass:
                print(f"REJECTED  {src.name}: {error}  ({elapsed:.1f}s)")
                rows.append(
                    (src.name, str(pages), str(sheets), "rejected", "-", f"{elapsed:.1f}s", "REJECTED")
                )
                print()
                continue
            failures += 1
            status = "ERROR"
            verify_cell = str(error)
            print(f"ERROR  {src.name}: {type(error).__name__}: {error}")
        except Exception as error:
            elapsed = time.perf_counter() - start
            failures += 1
            status = "ERROR"
            verify_cell = str(error)
            print(f"ERROR  {src.name}: {type(error).__name__}: {error}")
        else:
            verify_passed, failed_sheets, verify_log = _quiet_verify(dst, pages)
            verify_cell = "pass" if verify_passed else "FAIL"
            if verify_cell == "FAIL":
                failures += 1
                status = "FAIL"
                _dump_verify_artifacts(stem_dir, dst, verify_log, failed_sheets)
                print(f"verify artifacts: {stem_dir}")
            if geometry and status == "OK":
                geom_ok, geom_cell = geometry_check(src, dst, sample=geom_sample)
                if not geom_ok:
                    failures += 1
                    status = "FAIL"
                    print(f"GEOMETRY FAIL  {src.name}: {geom_cell}")
                    print(f"geometry artifacts: {stem_dir}")
                else:
                    print(f"geometry: {geom_cell}")
            elif not geometry:
                geom_cell = "skipped"
            elapsed = time.perf_counter() - start
            print(f"{status}  {src.name} -> {dst.name}  ({elapsed:.1f}s)")

        rows.append(
            (src.name, str(pages), str(sheets), verify_cell, geom_cell, f"{elapsed:.1f}s", status)
        )
        if status == "OK":
            cache[src.name] = {
                "code": code_fp,
                "src": _file_fingerprint(src),
                "verify": verify_cell,
                "geometry": geom_cell,
                "sample": geom_sample if geometry else None,
            }
        else:
            cache.pop(src.name, None)
        cache_changed = True
        print()

    if cache_changed:
        _save_cache(cache)

    print("=" * 120)
    print(f"{'input':32s} {'pages':>6} {'sheets':>7} {'verify':>8} {'geometry':45s} {'time':>7}  status")
    for row in rows:
        print(
            f"{row[0]:32.32s} {row[1]:>6} {row[2]:>7} {row[3]:>8} "
            f"{row[4]:45s} {row[5]:>7}  {row[6]}"
        )
    print("=" * 120)
    print(f"Inputs run : {len(inputs)}")
    if skipped_cache:
        print(f"Cache hits : {skipped_cache} (use --force to re-run them)")
    print(f"Failures   : {failures}")
    print(f"Outputs    : {OUTPUT_DIR}")
    print("Inspect each output with your own eyes — see test_pdfs\\CHECKLIST.md")
    return failures


def run_list(
    quick: bool, only: str | None, geometry: bool, sample: int | None
) -> int:
    inputs: list[Path] = collect_inputs(quick, only)
    if not inputs:
        print("No inputs matched.")
        return 1
    cache: dict = _load_cache()
    code_fp: str = _code_fingerprint()
    geom_sample: int = _resolve_sample(quick, sample)
    planned: int = 0
    for src in inputs:
        dst: Path = OUTPUT_DIR / src.name
        pages: int | None = _page_count(src)
        entry: dict | None = _cache_entry(src, cache)
        cache_hit: bool = _cache_hit(entry, code_fp, src, dst, geometry, geom_sample)
        if cache_hit:
            state: str = "cached"
        else:
            state = "run"
            planned += 1
        print(
            f"{state:7s} {src.name:32.32s} {str(pages if pages is not None else '?'):>6} pages"
        )
    print(f"{len(inputs)} input(s), {planned} would run, {len(inputs) - planned} cached")
    return 0


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Run the manual Folio test suite (by-eye, no test framework)."
    )
    parser.add_argument(
        "--regen",
        action="store_true",
        help="Regenerate synthetic inputs even if they already exist.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Only run inputs with 200 pages or fewer, and sample 12 sheets for the geometry check.",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        metavar="SUBSTRING",
        help="Run only inputs whose filename contains SUBSTRING (leaves other outputs alone).",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Never touch the network; missing real PDFs are skipped.",
    )
    parser.add_argument(
        "--no-geometry",
        action="store_true",
        help="Skip the pixel-level geometry check (faster, stamp verification still runs).",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help="Geometry sheets to sample per file: N, or 0 for every sheet "
        f"(default: {GEOM_SAMPLE_SHEETS}; --quick uses {QUICK_GEOM_SAMPLE}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore the run cache and re-impose every input.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Dry run: show which inputs would run vs. come from the cache, then exit.",
    )
    args: argparse.Namespace = parser.parse_args()

    if args.sample is not None and args.sample < 0:
        parser.error("--sample must be >= 0 (0 = every sheet)")

    ensure_synthetic_inputs(args.regen)
    for warning in ensure_real_inputs(args.offline):
        print(f"WARNING: {warning}")

    if args.list:
        raise SystemExit(
            run_list(
                quick=args.quick,
                only=args.only,
                geometry=not args.no_geometry,
                sample=args.sample,
            )
        )

    if not args.no_geometry:
        _oracle_canary()

    failures: int = run_suite(
        quick=args.quick,
        only=args.only,
        offline=args.offline,
        geometry=not args.no_geometry,
        force=args.force,
        sample=args.sample,
    )
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
