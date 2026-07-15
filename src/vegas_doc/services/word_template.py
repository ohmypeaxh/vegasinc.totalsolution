"""Shared validation and opening of OOXML Word templates."""

from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile

from docx import Document
from docx.document import Document as DocumentObject
from docx.opc.exceptions import PackageNotFoundError


class InvalidTemplateFormatError(ValueError):
    """Raised when a DOCX path does not contain an OOXML Word document."""


def open_template_document(template_path: Path) -> DocumentObject:
    """Open an OOXML template and explain common renamed-DOC failures."""

    try:
        with template_path.open("rb") as stream:
            signature = stream.read(8)
    except OSError as error:
        raise InvalidTemplateFormatError(f"Word 템플릿을 읽을 수 없습니다: {template_path}") from error
    if signature == bytes.fromhex("D0CF11E0A1B11AE1"):
        raise InvalidTemplateFormatError(
            "선택한 템플릿은 확장자만 .docx인 구형 Word 97-2003(.doc) 파일입니다. "
            "Microsoft Word에서 파일을 연 뒤 '다른 이름으로 저장' → 'Word 문서(*.docx)'로 변환해 주세요."
        )
    if not signature.startswith(b"PK"):
        raise InvalidTemplateFormatError(
            "선택한 파일은 유효한 DOCX 문서가 아닙니다. Microsoft Word에서 Word 문서(*.docx) 형식으로 다시 저장해 주세요."
        )
    try:
        return Document(template_path)
    except (BadZipFile, KeyError, OSError, PackageNotFoundError, ValueError) as error:
        raise InvalidTemplateFormatError(
            "Word 템플릿 내부 구조가 손상되었거나 암호화되어 열 수 없습니다. "
            "Microsoft Word에서 새 DOCX 파일로 다시 저장해 주세요."
        ) from error
