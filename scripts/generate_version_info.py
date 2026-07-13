"""Generate PyInstaller Windows version metadata from the package version."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vegas_doc.version import BUILD_INFO  # noqa: E402


def write_version_info(destination: Path) -> Path:
    """Write a PyInstaller VSVersionInfo file and return its path."""

    numeric = tuple(int(part) for part in BUILD_INFO.version.split("."))
    file_version = (*numeric, *(0 for _ in range(4 - len(numeric))))[:4]
    dotted_file_version = ".".join(str(part) for part in file_version)
    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={file_version!r}, prodvers={file_version!r}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'Vegas Inc.'),
      StringStruct('FileDescription', '{BUILD_INFO.product}'),
      StringStruct('FileVersion', '{dotted_file_version}'),
      StringStruct('InternalName', 'Vegas_Total_Solution_Doc'),
      StringStruct('LegalCopyright', 'Copyright (c) Vegas Inc.'),
      StringStruct('OriginalFilename', 'Vegas_Total_Solution_Doc.exe'),
      StringStruct('ProductName', '{BUILD_INFO.product}'),
      StringStruct('ProductVersion', '{BUILD_INFO.version}')
    ])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


if __name__ == "__main__":
    path = write_version_info(ROOT / "build" / "version_info.txt")
    print(path)
