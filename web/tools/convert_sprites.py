#!/usr/bin/env python3
"""
Convert sprite sheets to 512×512 (4×4 grid of 128×128 frames).

For each JPG/PNG in the tools directory that isn't already 512×512:
  - Split into 4×4 frames.
  - Each frame is centered (and scaled down if larger than 128×128,
    preserving aspect ratio) into a 128×128 slot.
  - The result is saved as PNG (lossless) next to the original.
    The original is kept as <name>.__orig.<ext>.
"""

import os
import shutil
import sys
from pathlib import Path
from PIL import Image

GRID       = 4          # 4×4 frames
SLOT       = 128        # target pixels per frame slot
TARGET     = GRID * SLOT  # 512
BG         = (255, 255, 255, 255)  # white, fully opaque


def place_frame(frame: Image.Image, slot: int) -> Image.Image:
    """Return a slot×slot RGBA image with frame centered, scaled to fit if needed."""
    fw, fh = frame.size

    # Scale DOWN if frame exceeds slot (keep aspect ratio, never upscale)
    if fw > slot or fh > slot:
        ratio = min(slot / fw, slot / fh)
        new_w = max(1, int(fw * ratio))
        new_h = max(1, int(fh * ratio))
        frame = frame.resize((new_w, new_h), Image.LANCZOS)
        fw, fh = frame.size

    canvas = Image.new("RGBA", (slot, slot), BG)
    x = (slot - fw) // 2
    y = (slot - fh) // 2
    # Paste with alpha mask if available
    mask = frame.split()[3] if frame.mode == "RGBA" else None
    canvas.paste(frame, (x, y), mask)
    return canvas


def convert(src: Path) -> Path:
    img = Image.open(src).convert("RGBA")
    w, h = img.size

    if w == TARGET and h == TARGET:
        print(f"  skip  {src.name}  (already {TARGET}×{TARGET})")
        return src

    frame_w = w // GRID
    frame_h = h // GRID
    print(f"  conv  {src.name}  {w}×{h}  →  frame {frame_w}×{frame_h}  →  {TARGET}×{TARGET}")

    out = Image.new("RGBA", (TARGET, TARGET), BG)

    for row in range(GRID):
        for col in range(GRID):
            left = col * frame_w
            top  = row * frame_h
            frame = img.crop((left, top, left + frame_w, top + frame_h))
            cell  = place_frame(frame, SLOT)
            out.paste(cell, (col * SLOT, row * SLOT))

    # Keep original
    backup = src.with_suffix(f".__orig{src.suffix}")
    if not backup.exists():
        shutil.copy2(src, backup)
        print(f"         original saved as  {backup.name}")

    # Write result as PNG (lossless)
    dst = src.with_suffix(".png")
    out.save(dst, "PNG", optimize=True)
    print(f"         written  {dst.name}")

    # Remove original if it had a different name (e.g. .jpg → .png)
    if dst != src:
        src.unlink()
        print(f"         removed  {src.name}")

    return dst


def main():
    tools = Path(__file__).parent
    images = sorted(p for p in tools.iterdir()
                    if p.is_file()
                    and p.suffix.lower() in (".jpg", ".jpeg", ".png")
                    and ".__orig" not in p.stem)

    if not images:
        print("No images found.")
        return

    print(f"Converting {len(images)} image(s) in {tools}\n")
    for img in images:
        convert(img)
    print("\nDone.")


if __name__ == "__main__":
    main()
