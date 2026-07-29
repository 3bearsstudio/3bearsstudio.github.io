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
    python3 tools/prep-shots.py <src-dir> <out-dir> [--width 720] [--quality 80]

    # typical:
    python3 tools/prep-shots.py ~/captures/kove assets/shots/kove

INPUT
    Any directory of .png / .jpg screenshots. Files are processed in sorted order and
    keep their basename, so `01-focus-home.png` becomes `01-focus-home.webp` — name
    the captures deliberately and the output is already ordered for the page.

OUTPUT
    WebP at --width (default 720px wide, which is 2x a ~360px display slot, i.e.
    retina-sharp at the size these are actually shown). Aspect ratio is preserved.
    Prints a before/after table and the total saving.

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
    parser.add_argument("--width", type=int, default=720, help="target width in px (default 720)")
    parser.add_argument("--quality", type=int, default=80, help="WebP quality 1-100 (default 80)")
    args = parser.parse_args()

    if not args.src.is_dir():
        return fail(f"source is not a directory: {args.src}")

    sources = sorted(p for p in args.src.iterdir() if p.suffix.lower() in SOURCE_SUFFIXES)
    if not sources:
        return fail(f"no .png/.jpg files in {args.src}")

    args.out.mkdir(parents=True, exist_ok=True)

    before_total = after_total = 0
    print(f"{'file':<28} {'before':>10} {'after':>10} {'saved':>7}")
    print("-" * 58)

    for src in sources:
        with Image.open(src) as img:
            img = img.convert("RGB")
            height = round(img.height * args.width / img.width)
            resized = img.resize((args.width, height), Image.LANCZOS)
            dest = args.out / f"{src.stem}.webp"
            resized.save(dest, "WEBP", quality=args.quality, method=6)

        before = src.stat().st_size
        after = dest.stat().st_size
        before_total += before
        after_total += after
        print(f"{src.name:<28} {kb(before):>10} {kb(after):>10} {pct(before, after):>7}")

    print("-" * 58)
    print(f"{'TOTAL':<28} {kb(before_total):>10} {kb(after_total):>10} {pct(before_total, after_total):>7}")
    print(f"\n{len(sources)} file(s) -> {args.out}  ({args.width}px wide, q{args.quality})")
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
