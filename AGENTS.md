# AGENTS.md

## Project

Folio turns PDFs into print-ready booklets (two-up imposition). Plain Python, no framework. `main.py` is empty — the real entrypoints are `__main__` blocks inside `core/` modules.

## Commands

- Environment: `.venv` (Python 3.14.7). Install deps with `pip install -r requirements.txt` (fully pinned).
- Always run from the repo root as modules — imports are package-absolute (`from core.calculation import impose`), so `python core/booklet_imposition.py` fails; use `python -m core.<module>`:
  - `python -m core.generate_test_pdf --help` — argparse CLI that builds numbered test PDFs (reportlab).
  - `python -m core.booklet_imposition` — interactive: one prompt for both paths, shlex-split (e.g. `"in.pdf" "out.pdf"`). Stamps → imposes → verifies → saves.
  - `python -m core.calculation` — interactive: prints the imposition order for a page count.
- No lint, typecheck, or test framework exists. "Testing" = manual script runs checked by eye: `print(order)`, then `Verifying N sheets...`, per-sheet `FAIL` lines, and `Result: X/Y sheets passed`. **Do not introduce pytest/unittest or new tooling unless asked** — this is a deliberate project convention (GitHub issues #9/#10).
- Verification output comes from `build_booklet()` itself; `verify_booklet.py` has no CLI.

## Commits

- Commit only when explicitly asked, then **one commit per file or logical change** — don't bundle unrelated edits.
- Message style: a short imperative summary line (sentence case), followed by a body of `- ` bullet descriptions of what changed. Examples in `git log` (e.g. `Derive verifier width from shared A4 constants`).
- Check `git status`/`git diff` before staging; stage files individually rather than `git add -A`.

## Architecture

- `core/calculation.py` — `impose(number_pages)` returns `(left, right)` 1-based page-number pairs. Page count pads to a multiple of 4; `0` is the sentinel for a blank/padding side.
- `core/booklet_imposition.py` — `build_booklet()`: PyMuPDF stamps every source page with an invisible 4-digit page number (`render_mode=3`, PDF operator `Tr 3`), then imposes and verifies — the whole pipeline is PyMuPDF-only (no `io.BytesIO` bridging; fitz-only `build_booklet()` landed in `1c87042`). The helper `place_pages_side_by_side(source: fitz.Document, output: fitz.Document, left_index, right_index)` is fitz-only: `output.new_page()` + `show_pdf_page()`, sheet from `A4_LANDSCAPE` (841.89 × 595.28 pt), half-width `420.945` splits left/right, `None` side = blank half.
- `core/verify_booklet.py` — `stamp_page_numbers()` + `verify_booklet(output: Pdf | fitz.Document, order) -> bool`. The `isinstance` branch is a migration leftover: `build_booklet()` now passes a `fitz.Document`, so the pikepdf branch is dead code pending removal as part of issue #10. Known gap: `build_booklet()` ignores the return value (no non-zero exit on failure yet — issue #9).
- `utils/format_utils.py` — `zero_padding(n, width=2)` used at **width=4** for stamps and `_check_side()`, but `generate_test_pdf.py` uses the width=2 default for the visible number. Keep stamp and check in sync; the visible number is never matched by the verifier.
- `utils/constants.py` — `PAGE_WIDTH`/`PAGE_HEIGHT` are portrait A4 (reportlab) for the test PDF; `A4_LANDSCAPE` (841.89 × 595.28) is the shared source for the imposition sheet and the verifier's `HALF_WIDTH`.
- PyMuPDF's import name is `fitz`. PySide6 is pinned in requirements but nothing imports it yet (UI is planned, issue #2).

## In-flight work — check GitHub issues first

Issues are the task tracker (`task` label, parent/sub-issue structure; `gh issue list`). Key open items:

- **#10 migration**: pikepdf is being phased out for a PyMuPDF-only pipeline (`page.show_pdf_page()`). The fitz rewrite of `place_pages_side_by_side()` (`aae11ed`) and the fitz-only `build_booklet()` (`1c87042`) are committed — no new pikepdf-only code paths. Remaining: simplify `verify_booklet()` to fitz-only (drop the isinstance branch and its `io`/`pikepdf` imports — decision already made) and remove pikepdf from `requirements.txt`.
- **#9 verification**: core is shipped and wired into `build_booklet()`; open items are failure exit status and a standalone CLI.
- The old pikepdf-only bugs (scientific-notation content streams, rotated pages) were resolved by the migration, not patched (issue #10).

## Docs live outside this repo

Canonical line-by-line tutorials are Obsidian vault notes in a **separate git repo** under `$GITHUB_DIR\Obsidian\Zettelkasten\00 - P&Q\Projects\Folio` (`GITHUB_DIR` is an env var pointing at the folder holding all GitHub checkouts — `D:\GitHub` on this machine; on others, resolve it via the env var instead of hardcoding). When asked to "update the tutorial", that's where it lives; keep vault notes and code in sync when behavior changes.

## Environment quirks

- `gh` CLI may not be on PATH in fresh shells — fall back to the full path if `Get-Command gh` fails (this machine: `C:\Program Files\GitHub CLI\gh.exe`).
- Default branch is `master`, not `main`.
