# Manual test suite — eyeball checklist

Run everything with:

```
$env:PYTHONUTF8=1
python -m core.manual_test_suite
```

- `--quick` runs only inputs with **200 pages or fewer** (drops `stress_500p` + `library`) and samples 12 sheets instead of 48 for the geometry check.
- `--regen` rebuilds synthetic inputs.
- `--only SUBSTRING` runs one case.
- `--offline` skips downloads.
- `--no-geometry` skips the pixel check.
- `--sample N` sets how many sheets the geometry check samples (**0 = every sheet**; default 48, `--quick` uses 12).
- `--force` re-imposes everything.
- `--list` is a dry run showing what would run vs. come from cache.

Missing real PDFs are downloaded automatically (with retry + a `%PDF` magic-byte check). Any real PDF you drop into `inputs\real\` is picked up too (e.g. your own 11-page paper / 242-page book). Outputs land in `outputs\`.

Besides the built-in stamp verification, every run also does a **geometry check**: it independently rebuilds the expected imposition from the input and pixel-diffs it against the output (content pixels only, >10% differs = fail; full runs sample 48 sheets). This is what caught the rotated-page bug below. The run ends with a summary table.

Before the first input, an **oracle canary** builds and imposes an 8-page booklet in a temp dir, asserts the geometry check passes on the pristine output and *fails* on a deliberately blackened sheet — so a silently broken oracle can't mark everything OK.

**Run cache:** results are cached in `run_cache.json` keyed on the input file's size/mtime plus a hash of the suite + core source files **plus the geometry sample size**. Unchanged inputs are skipped on re-runs (shown as `cached`); touching an input, editing the code, or changing `--sample` invalidates them automatically. `--force` bypasses the cache.

**Failure artifacts:** if stamp verification or the geometry check fails for an input, `failures\<input-stem>\` gets `verify.log`, `verify_sheet_NNN.png`, and/or `sheet_NNN_actual.png` / `sheet_NNN_expected.png` / `sheet_NNN_diff.png` (red = mismatched content pixels). The folder is cleared on the next run of that input.

Last full run: 12/12 inputs imposed, 0 verification failures, 0 geometry failures (re-verified after the caching/artifact/canary work).

## What to check with your own eyes

| Output | Sheets | What to verify |
|---|---|---|
| `numbered_08p.pdf` | 4 | Booklet order reads outside→inside (sheet 1 = 1\|8, then 2\|7 …); halves upright and centred |
| `numbered_09p.pdf` | 3 | Odd count: sheets 1–2 carry page 1 alone with blank halves; blanks are truly blank |
| `numbered_16p.pdf` | 8 | Control case (multiple of 4): every page exactly once, clean layout |
| `rotated_mixed.pdf` | 2 | Sheet 1: source page 1 carries `/Rotate 90` — flags are cleared, so the **stored** layout is imposed as-is: "Page 1 rotated 90" reads horizontally at top-left of the right half with its label top aligned with "Page 4" (both y≈52, no white bands); page 3 is US Letter — scales to fit, aspect preserved (its label sits ~23pt lower than "Page 2" — expected letterbox) |
| `asymmetric.pdf` | 1 | Red corner box stays in its corner on every page; faint outlines fit each half |
| `annotations_bookmarks.pdf` | 4 | Page content fine, but **known finding**: the link, highlight and bookmarks are gone (show_pdf_page copies content only) |
| `stress_500p.pdf` | 125 | Skim start/middle/end — no corruption or slowdown deep in the document |
| `arxiv_attention_15p.pdf` | 4 | Real A4 academic paper (TeX fonts): text sharp, figures intact; sheet 1 has page 1 alone (15 pages) |
| `irs_w4_form_letter.pdf` | 2 | Real US Letter form: box grid aligned within halves, small text legible |
| `tutorial.pdf` | 42 | Real 167-page book: spot-check first/last sheets, printed footer page numbers descend correctly |
| `library.pdf` | 1210 | Real 2419-page book: spot-check first/middle/last sheets (~25s to process) |

## Programmatic findings (recorded in issue #10)

- `encrypted_aes256.pdf`: no output written — `build_booklet` rejects password-protected sources with a clear `ValueError` (guard added during this work).
- Annotations, link rectangles and bookmarks (TOC) are **not** carried into the imposed output; page content itself is always fine.
- **Rotated pages (decided 2026-10-08):** `/Rotate` flags are cleared (`page.set_rotation(0)`) before stamping/imposition — the stored page content is imposed as-is, so "Page 1 rotated 90" prints horizontally alongside the other labels. Clearing the flag first also sidesteps `show_pdf_page()`'s mishandling of rotated sources (pre-fix: content shifted ~86pt with the bottom ~14% clipped). Caveat: a real-world PDF whose stored content is sideways and relies on `/Rotate` to display upright will print as stored (viewers still honor the flag).
- Performance on this machine: 2419 pages / 1210 sheets ~49s (incl. sampled geometry); 500 pages / 125 sheets ~3s.
