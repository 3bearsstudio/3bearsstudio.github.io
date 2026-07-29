#!/usr/bin/env python3
"""
Prepare raw simulator screenshots for the web.

WHY THIS EXISTS
    A raw iPhone screenshot off `xcrun simctl io ... screenshot` is ~2 MB of PNG at
    1206x2622. Nine of them is 14 MB. Committing that to a GitHub Pages repo is the
    exact mistake `~/appDevelopment/md/studio-identity-web-standards.md` warns about
    under "Media rules" — and git keeps it FOREVER, so deleting it later does not
    shrink the repo. Resize and convert BEFORE the first commit, not after.

USAGE
    python3 tools/prep-shots.py <src-dir> <out-dir> [--widths 1206,720] [--quality 92]

    # typical:
    python3 tools/prep-shots.py ~/captures/kove assets/shots/kove

INPUT
    Any directory of .png / .jpg screenshots. Files are processed in sorted order and
    keep their basename, so `01-focus-home.png` becomes `01-focus-home-1206.webp` —
    name the captures deliberately and the output is already ordered for the page.

OUTPUT
    One WebP per width, suffixed `-<width>`, ready to drop straight into a `srcset`:

        srcset="…-720.webp 720w, …-1206.webp 1206w"  sizes="(max-width:900px) 40vw, 20vw"

    Aspect ratio is preserved. Prints a per-file table and the total saving.

ON QUALITY — read this before lowering it
    These are UI screenshots, not photographs. They are full of small, high-contrast
    text, and WebP smears exactly that. The first pass of this script ran at q80/720px
    and squeezed a dark habit-tracker screen down to 28 KB; it looked visibly soft and
    the owner rejected it. Photographic rules of thumb do not transfer. Default is
    **q92 at native width**, and going below ~q88 on app UI is a false economy — the
    screenshots are the entire reason the section exists.

FAILURE MODES
    - Pillow missing or built without WebP  -> exits 1 with the check that failed.
      Verify with: python3 -c "from PIL import features; print(features.check('webp'))"
    - Empty source dir                      -> exits 1 rather than silently doing nothing.
    - Existing output files are OVERWRITTEN without prompting. Point --out at a
      scratch dir first if you care.

WHAT NOT TO DO WITH IT
    Do not use it on App Store submission screenshots. Apple wants the full-resolution
    PNG at exact device sizes; this script deliberately destroys both. It is for the
    WEBSITE only. Keep the raw PNGs somewhere outside the repo.
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, features
except ImportError:
    sys.exit("Pillow is not installed. `pip install Pillow`")

if not features.check("webp"):
    sys.exit("This Pillow build has no WebP support — cannot continue.")

SOURCE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("src", type=Path, help="directory of raw screenshots")
    parser.add_argument("out", type=Path, help="directory to write .webp into (created if absent)")
    parser.add_argument("--widths", default="1206,720",
                        help="comma-separated target widths in px (default 1206,720)")
    parser.add_argument("--quality", type=int, default=92,
                        help="WebP quality 1-100 (default 92 — see ON QUALITY above)")
    args = parser.parse_args()

    try:
        widths = sorted({int(w) for w in args.widths.split(",") if w.strip()}, reverse=True)
    except ValueError:
        return fail(f"--widths must be comma-separated integers, got: {args.widths}")
    if not widths:
        return fail("--widths produced no widths")

    if not args.src.is_dir():
        return fail(f"source is not a directory: {args.src}")

    sources = sorted(p for p in args.src.iterdir() if p.suffix.lower() in SOURCE_SUFFIXES)
    if not sources:
        return fail(f"no .png/.jpg files in {args.src}")

    args.out.mkdir(parents=True, exist_ok=True)

    before_total = after_total = 0
    widest = widths[0]
    print(f"{'file':<26} {'source':>9} " + " ".join(f"{str(w) + 'px':>9}" for w in widths))
    print("-" * (36 + 10 * len(widths)))

    for src in sources:
        with Image.open(src) as img:
            img = img.convert("RGB")
            if img.width < widest:
                print(f"  note: {src.name} is only {img.width}px wide — upscaling to {widest}px "
                      f"will not add detail", file=sys.stderr)
            row_sizes = []
            for width in widths:
                height = round(img.height * width / img.width)
                resized = img.resize((width, height), Image.LANCZOS)
                dest = args.out / f"{src.stem}-{width}.webp"
                resized.save(dest, "WEBP", quality=args.quality, method=6)
                row_sizes.append(dest.stat().st_size)

        before = src.stat().st_size
        before_total += before
        # Only the widest counts toward the "after" total: srcset means a visitor
        # downloads exactly one of these, never all of them.
        after_total += row_sizes[0]
        print(f"{src.name:<26} {kb(before):>9} " + " ".join(f"{kb(s):>9}" for s in row_sizes))

    print("-" * (36 + 10 * len(widths)))
    print(f"{'TOTAL (widest only)':<26} {kb(before_total):>9} {kb(after_total):>9}"
          f"   {pct(before_total, after_total)} smaller")
    print(f"\n{len(sources)} file(s) x {len(widths)} width(s) -> {args.out}  (q{args.quality})")
    print("srcset example:")
    stem = sources[0].stem
    rel = args.out.as_posix().split("assets/", 1)[-1]
    print(f'  srcset="assets/{rel}/{stem}-720.webp 720w, assets/{rel}/{stem}-{widest}.webp {widest}w"')
    return 0


def kb(n: int) -> str:
    return f"{n / 1024:.0f} KB" if n < 1024 * 1024 else f"{n / 1024 / 1024:.1f} MB"


def pct(before: int, after: int) -> str:
    return "—" if not before else f"{100 - after * 100 / before:.0f}%"


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
