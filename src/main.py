"""Compatibility entry point for Vegas Total Solution Doc.

The previous single-file DQ/OCR implementation has been preserved in git history.
Current production startup is delegated to the plugin-based application shell.
"""

from __future__ import annotations

from vegas_doc.app.main import main


if __name__ == "__main__":
    raise SystemExit(main())
