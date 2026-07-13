"""Generate application icon assets from the official Vegas wordmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
BRAND_PURPLE = "#8D58FF"
DEEP_INDIGO = "#17142D"


def _contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Return a high-quality contained copy without changing aspect ratio."""

    copy = image.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    return copy


def generate(source: Path, output_directory: Path) -> None:
    """Copy the official logo and create PNG/ICO application icons."""

    output_directory.mkdir(parents=True, exist_ok=True)
    wordmark = Image.open(source).convert("RGBA")
    wordmark.save(output_directory / "vegas_logo.png", optimize=True)

    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((16, 16, 496, 496), radius=112, fill=DEEP_INDIGO)
    draw.rounded_rectangle((16, 16, 496, 496), radius=112, outline=BRAND_PURPLE, width=12)
    draw.rounded_rectangle((54, 160, 458, 352), radius=44, fill="#FFFFFF")
    fitted = _contain(wordmark, (356, 124))
    canvas.alpha_composite(fitted, ((512 - fitted.width) // 2, (512 - fitted.height) // 2))

    canvas.save(output_directory / "app.png", optimize=True)
    canvas.save(
        output_directory / "app.ico",
        format="ICO",
        sizes=[(size, size) for size in ICON_SIZES],
    )


def main() -> int:
    """Parse paths and generate deterministic brand assets."""

    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Path to the official Vegas PNG wordmark")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "assets")
    args = parser.parse_args()
    generate(args.source.resolve(), args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
