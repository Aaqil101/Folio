# Folio

Turn any PDF into a print-ready booklet. No page shuffling required.

Folio imposes pages two-up — first page beside last, second beside
second-to-last, and so on — so a stack of printed sheets folds straight
into a real booklet. Every output is verified page-by-page before it is
saved; if anything is off, nothing is written.

## Install

Download **Folio-Setup-\<version\>.exe** from the
[releases page](https://github.com/Aaqil101/Folio/releases) and run it.
The installer sets up Folio for all users by default (a per-user install
is offered as an alternative) and leaves your settings in
`%APPDATA%\Folio\` untouched if you later uninstall.

Windows 10/11 on x64.

## Usage

1. **Add files** — drop a PDF (or a folder of images) onto the window,
   or use the Add File / Add Folder buttons. Each queue row is one
   booklet.
2. **Check the output path** — double-click a row to change where the
   result is saved; drag rows to reorder the queue.
3. **Press "Create booklets"** — Folio stamps and verifies every sheet
   before saving.

### Printing the booklet

Print the produced PDF **double-sided, flipping on the short edge**, at
100% scale (no "fit to page"), on the sheet size chosen in
Settings → Sheet size. A4 sheets fold into A5 booklets, A3 into A4.
Fold each sheet in half and stack them in order — the outermost sheet
carries the cover.

## Features

- **Job queue** — impose several PDFs or image folders in one run;
  drag rows to reorder, and keep the queue between sessions
- **Image input** — folders of JPEG/PNG/TIFF/WebP become booklets;
  order is natural-sorted (`page2` before `page10`), and the arrange
  dialog lets you reorder with drag or keyboard
- **Sheet sizes** — A3, A4, or A5 (the paper you feed the printer);
  the booklet ends up one size smaller
- **Verification** — every imposed sheet is checked against the source
  before the file is written
- **Customizable** — accent colors, default folders, output filename
  pattern, and auto-open behavior

## Building from source

Requires Python 3.14 and [Inno Setup 7](https://jrsoftware.org/isinfo.php).

```console
python -m venv .venv
pip install -r requirements.txt -r requirements-build.txt
installer\build.cmd
```

The script wipes previous build output, builds the app with PyInstaller
(onedir), **pauses so you can launch and check `dist\Folio\Folio.exe`**,
then compiles the installer with Inno Setup into `dist\installer\` and
cleans the intermediates.

To run from source without packaging: `pip install -r requirements.txt`,
then `python -m main`.

## Development

The `core/` modules keep their own `__main__` blocks and are runnable
directly, e.g. `python -m core.generate_test_pdf` or
`python -m core.calculation`. The by-eye regression suite is
`python -m core.manual_test_suite` (see AGENTS.md for details).

Issues and pull requests are welcome on
[GitHub](https://github.com/Aaqil101/Folio/issues).

## License

GPL-3.0 — see [LICENSE](LICENSE).
