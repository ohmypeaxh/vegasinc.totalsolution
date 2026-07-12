"""Write reproducible package size and largest-file reports."""

from __future__ import annotations

import argparse
from pathlib import Path


def size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def mib(value: int) -> float:
    return value / (1024 * 1024)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--distribution", required=True, type=Path)
    parser.add_argument("--installer", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()

    distribution_size = size_bytes(args.distribution)
    installer_size = size_bytes(args.installer) if args.installer and args.installer.exists() else 0
    files = sorted(
        ((item.stat().st_size, item) for item in args.distribution.rglob("*") if item.is_file()),
        reverse=True,
    )
    lines = [
        f"label={args.label}",
        f"distribution_bytes={distribution_size}",
        f"distribution_mib={mib(distribution_size):.3f}",
        f"installed_bytes={distribution_size}",
        f"installed_mib={mib(distribution_size):.3f}",
        f"installer_bytes={installer_size}",
        f"installer_mib={mib(installer_size):.3f}",
        "",
        "largest_30_files:",
    ]
    lines.extend(f"{mib(size):10.3f} MiB  {path.relative_to(args.distribution)}" for size, path in files[:30])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
