"""Conservatively remove confirmed-unused Qt runtime payload from a frozen build."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

KEEP_PLUGIN_DIRECTORIES = {"platforms", "imageformats", "styles", "tls"}
KEEP_PLUGIN_FILES = {
    "platforms": {"qwindows.dll"},
    "imageformats": {"qgif.dll", "qico.dll", "qjpeg.dll", "qtga.dll", "qtiff.dll", "qwbmp.dll", "qwebp.dll"},
}
KEEP_TRANSLATION_PREFIXES = ("qt_en", "qtbase_en", "qt_ko", "qtbase_ko")


def remove_path(path: Path) -> None:
    """Remove a file or directory if present."""

    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def optimize_distribution(distribution: Path) -> list[str]:
    """Remove non-runtime content while retaining Windows GUI/image/TLS support."""

    removed: list[str] = []
    qt_roots = list(distribution.rglob("PySide6/Qt"))
    for qt_root in qt_roots:
        plugins = qt_root / "plugins"
        if plugins.is_dir():
            for category in plugins.iterdir():
                if category.is_dir() and category.name not in KEEP_PLUGIN_DIRECTORIES:
                    removed.append(str(category.relative_to(distribution)))
                    remove_path(category)
            for category_name, keep_files in KEEP_PLUGIN_FILES.items():
                category = plugins / category_name
                if category.is_dir():
                    for dll in category.glob("*.dll"):
                        if dll.name.lower() not in keep_files:
                            removed.append(str(dll.relative_to(distribution)))
                            remove_path(dll)
        translations = qt_root / "translations"
        if translations.is_dir():
            for translation in translations.iterdir():
                if translation.is_file() and not translation.name.lower().startswith(KEEP_TRANSLATION_PREFIXES):
                    removed.append(str(translation.relative_to(distribution)))
                    remove_path(translation)

    for pattern in ("**/__pycache__", "**/.pytest_cache", "**/*.pdb", "**/*.map", "**/tests", "**/test"):
        for candidate in distribution.glob(pattern):
            if candidate.exists():
                removed.append(str(candidate.relative_to(distribution)))
                remove_path(candidate)
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("distribution", type=Path)
    args = parser.parse_args()
    removed = optimize_distribution(args.distribution.resolve())
    print(f"Removed {len(removed)} confirmed-unused runtime entries")
    for item in removed:
        print(f"REMOVED {item}")


if __name__ == "__main__":
    main()
