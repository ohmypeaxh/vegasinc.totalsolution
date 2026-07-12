"""Write deterministic package size reports for Windows release builds."""

from __future__ import annotations

import argparse
from pathlib import Path


def _files(root: Path) -> list[tuple[int, Path]]:
    return sorted(
        ((path.stat().st_size, path) for path in root.rglob("*") if path.is_file()),
        reverse=True,
    )


def write_report(label: str, distribution: Path, installer: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    dist_files = _files(distribution) if distribution.exists() else []
    lines = [
        f"Package size report: {label}",
        f"Distribution: {distribution}",
        f"Distribution bytes: {sum(size for size, _ in dist_files)}",
        f"Distribution MB: {sum(size for size, _ in dist_files) / 1024 / 1024:.2f}",
        f"Installer: {installer}",
        f"Installer bytes: {installer.stat().st_size if installer.exists() else 0}",
        f"Installer MB: {installer.stat().st_size / 1024 / 1024:.2f}" if installer.exists() else "Installer MB: 0.00",
        "",
        "Largest packaged files:",
    ]
    lines.extend(f"{size / 1024 / 1024:8.2f} MB  {path.relative_to(distribution)}" for size, path in dist_files[:20])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--after", action="store_true")
    parser.add_argument("--distribution", type=Path)
    parser.add_argument("--installer", type=Path)
    args = parser.parse_args()
    label = "after" if args.after else "before"
    write_report(
        label,
        args.distribution or Path("dist/Vegas_Total_Solution_Doc"),
        args.installer or Path("dist/installer/Vegas_Total_Solution_Doc_Setup.exe"),
        Path("artifacts/package_size_after.txt" if args.after else "artifacts/package_size_before.txt"),
    )
