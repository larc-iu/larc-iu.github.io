#!/usr/bin/env python3
"""Normalise the headshots under content/images/people.

Every photo ends up a JPEG whose longer side is 256 pixels:

  * images are scaled to fit inside a 256x256 box, keeping their own aspect
    ratio. Nothing is cropped and nothing is squashed, so a portrait photo
    stays portrait and keeps its full frame. The site crops to a circle at
    display time via `object-fit: cover`, and that is the right place for it
    -- a crop baked into the file here could not be undone;
  * PNGs are re-encoded as JPEG and the originals deleted, since a photo in
    PNG is several times the size for no benefit;
  * references in content/people.yaml are rewritten to match any renamed file.

Photos already sized correctly are left alone. That matters: JPEG is lossy, so
re-encoding a conforming photo on every run would slowly degrade it. Pass
--force only if you mean it.

Usage:
    python3 tools/normalize_headshots.py --dry-run
    python3 tools/normalize_headshots.py

Requires ImageMagick (`convert` and `identify`).
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PHOTO_DIR = REPO / "content" / "images" / "people"
PEOPLE_YAML = REPO / "content" / "people.yaml"

# The longer side of every photo, in pixels. The site displays headshots at
# 160px at the largest, so this leaves room for high-density screens.
MAX_SIDE = 256
QUALITY = 85
SOURCE_SUFFIXES = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
# The site refers to photos by this path prefix.
YAML_PREFIX = "images/people/"
GOOD_NAME = re.compile(r"^[a-z0-9_]+\.jpg$")


def require_imagemagick() -> None:
    missing = [t for t in ("convert", "identify") if shutil.which(t) is None]
    if missing:
        sys.exit(
            f"ImageMagick is required but {' and '.join(missing)} "
            "not found on PATH.\n"
            "  Debian/Ubuntu: sudo apt install imagemagick\n"
            "  macOS:         brew install imagemagick"
        )


def probe(path: Path) -> tuple[int, int, str] | None:
    """Return (width, height, format) for an image, or None if unreadable."""
    out = subprocess.run(
        ["identify", "-format", "%w %h %m", str(path) + "[0]"],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return None
    try:
        w, h, fmt = out.stdout.split()
    except ValueError:
        return None
    return int(w), int(h), fmt.upper()


def normalise(src: Path, dest: Path) -> None:
    """Scale to fit inside MAX_SIDE, preserving aspect, and write a JPEG."""
    subprocess.run(
        [
            "convert", str(src) + "[0]",
            # Flatten onto white first: PNGs may have transparency, which JPEG
            # cannot store and would otherwise render as black.
            "-background", "white", "-alpha", "remove", "-alpha", "off",
            # Fits the image inside the box: the longer side becomes MAX_SIDE
            # and the shorter side follows from the aspect ratio. No '^' and no
            # -extent, so nothing is cropped.
            "-resize", f"{MAX_SIDE}x{MAX_SIDE}",
            "-strip",
            "-colorspace", "sRGB",
            "-interlace", "Plane",
            "-quality", str(QUALITY),
            # Explicit JPEG: prefix. ImageMagick otherwise infers the output
            # format from the extension, and the caller writes to a .tmp file,
            # which would silently preserve the input's encoding instead.
            f"JPEG:{dest}",
        ],
        check=True,
        capture_output=True,
    )


def rewrite_yaml(renames: dict[str, str], dry_run: bool) -> tuple[list[str], str]:
    """Point people.yaml at the new filenames.

    Returns the changes made and the resulting text. The text is returned even
    under --dry-run so the reference check below compares against the state the
    run would produce, rather than flagging every pending rename twice.
    """
    if not PEOPLE_YAML.exists():
        return [], ""
    text = PEOPLE_YAML.read_text(encoding="utf-8")
    changed = []
    for old, new in renames.items():
        needle = YAML_PREFIX + old
        if needle in text:
            text = text.replace(needle, YAML_PREFIX + new)
            changed.append(f"{needle} -> {YAML_PREFIX + new}")
    if changed and not dry_run:
        PEOPLE_YAML.write_text(text, encoding="utf-8")
    return changed, text


def check_references(filenames: set[str], text: str) -> tuple[list[str], list[str]]:
    """Cross-check the photo directory against people.yaml.

    Commented-out entries count as referenced: retired alumni are commented
    out rather than deleted, and their photos should not be reported as junk.
    """
    if not text:
        return [], []
    referenced = set(re.findall(re.escape(YAML_PREFIX) + r"([^\"'\s]+)", text))
    dangling = sorted(referenced - filenames)
    orphaned = sorted(filenames - referenced)
    return dangling, orphaned


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without touching anything")
    ap.add_argument("--force", action="store_true",
                    help="re-encode photos that are already 256x256 JPEGs")
    args = ap.parse_args()

    require_imagemagick()
    if not PHOTO_DIR.is_dir():
        sys.exit(f"No photo directory at {PHOTO_DIR}")

    sources = sorted(p for p in PHOTO_DIR.iterdir()
                     if p.is_file() and p.suffix in SOURCE_SUFFIXES)
    if not sources:
        sys.exit(f"No images found in {PHOTO_DIR}")

    converted, resized, skipped, failed = [], [], [], []
    renames: dict[str, str] = {}
    final_names: set[str] = set()

    for src in sources:
        info = probe(src)
        if info is None:
            failed.append(f"{src.name}: not a readable image")
            final_names.add(src.name)
            continue
        width, height, fmt = info

        dest = src.with_suffix(".jpg")
        is_jpeg = fmt == "JPEG"
        # Correctly sized means the longer side is already MAX_SIDE. The
        # shorter side is whatever the aspect ratio makes it.
        right_size = max(width, height) == MAX_SIDE
        already_ok = is_jpeg and right_size and src.suffix == ".jpg"

        if already_ok and not args.force:
            skipped.append(src.name)
            final_names.add(dest.name)
            continue

        reasons = []
        if not is_jpeg or src.suffix != ".jpg":
            reasons.append(f"{fmt} -> JPEG")
        if not right_size:
            scale = MAX_SIDE / max(width, height)
            reasons.append(
                f"{width}x{height} -> {round(width * scale)}x{round(height * scale)}")
        if not reasons:
            reasons.append("re-encoded")

        label = f"{src.name}: {', '.join(reasons)}"
        (converted if src.suffix != ".jpg" else resized).append(label)
        final_names.add(dest.name)
        if src.name != dest.name:
            renames[src.name] = dest.name

        if args.dry_run:
            continue

        try:
            # Write beside the target, then move into place, so a failure
            # partway through cannot leave a truncated photo behind.
            tmp = dest.with_name(dest.name + ".tmp")
            normalise(src, tmp)
            tmp.replace(dest)
            if src != dest:
                src.unlink()
        except subprocess.CalledProcessError as exc:
            failed.append(f"{src.name}: {exc.stderr.decode(errors='replace').strip()}")

    yaml_changes, yaml_text = rewrite_yaml(renames, args.dry_run)
    dangling, orphaned = check_references(final_names, yaml_text)

    def report(title: str, items: list[str]) -> None:
        if items:
            print(f"\n{title} ({len(items)}):")
            for item in items:
                print(f"  {item}")

    prefix = "Would change" if args.dry_run else "Changed"
    report(f"{prefix} format", converted)
    report(f"{prefix} size", resized)
    report(f"{prefix} people.yaml", yaml_changes)
    report(f"Left alone (already JPEG, longest side {MAX_SIDE}px)", skipped)

    badly_named = sorted(n for n in final_names if not GOOD_NAME.match(n))
    report("Unconventional filenames (expected lowercase_with_underscores.jpg)",
           badly_named)
    report("Referenced in people.yaml but missing from disk", dangling)
    report("On disk but never referenced in people.yaml", orphaned)
    report("Failed", failed)

    total = len(converted) + len(resized)
    print(f"\n{total} photo(s) {'would be ' if args.dry_run else ''}normalised, "
          f"{len(skipped)} already fine.")
    if args.dry_run and total:
        print("Re-run without --dry-run to apply.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
