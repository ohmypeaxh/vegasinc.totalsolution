"""Install the Vegas wordmark and optional dedicated application icon."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)


def generate_app_icon(source: Path, output_directory: Path) -> None:
    """Create the canonical PNG and multi-resolution Windows ICO assets."""

    icon = Image.open(source).convert("RGBA")
    if icon.width != icon.height:
        raise ValueError("The application icon source must be square.")

    icon.save(output_directory / "app.png", optimize=True)
    icon.save(
        output_directory / "app.ico",
        format="ICO",
        sizes=[(size, size) for size in ICON_SIZES],
    )


def generate(source: Path, output_directory: Path, app_icon_source: Path | None = None) -> None:
    """Copy the official wordmark without replacing an unrelated app icon."""

    output_directory.mkdir(parents=True, exist_ok=True)
    wordmark = Image.open(source).convert("RGBA")
    wordmark.save(output_directory / "vegas_logo.png", optimize=True)
    if app_icon_source is not None:
        generate_app_icon(app_icon_source, output_directory)


def main() -> int:
    """Parse paths and generate deterministic brand assets."""

    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Path to the official Vegas PNG wordmark")
    parser.add_argument(
        "--app-icon",
        type=Path,
        help="Optional square PNG used for app.png and the multi-resolution app.ico",
    )
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "assets")
    args = parser.parse_args()
    generate(
        args.source.resolve(),
        args.output.resolve(),
        args.app_icon.resolve() if args.app_icon is not None else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
