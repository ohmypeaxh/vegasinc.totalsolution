"""Real document extraction service using PyMuPDF and OCR fallback."""

from __future__ import annotations

from pathlib import Path

import fitz

from vegas_doc.models.extraction import DocumentExtractionResult, DocumentKind, ExtractionMethod, ExtractionPolicy, PageExtractionMetadata
from vegas_doc.models.ocr import OCRPageRequest, OCRRequest
from vegas_doc.services.extraction import DocumentTextExtractor
from vegas_doc.services.ocr import OCRService

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
MEANINGFUL_TEXT_LENGTH = 30


class PyMuPDFDocumentTextExtractor(DocumentTextExtractor):
    """Extract embedded PDF text first and use OCR only for insufficient pages."""

    def __init__(self, ocr_service: OCRService | None = None) -> None:
        self._ocr_service = ocr_service

    def supports(self, source_path: Path, document_kind: DocumentKind) -> bool:
        return source_path.suffix.lower() == ".pdf" or source_path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES

    def extract(self, source_path: Path, document_kind: DocumentKind, policy: ExtractionPolicy) -> DocumentExtractionResult:
        suffix = source_path.suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf(source_path, policy)
        if suffix in SUPPORTED_IMAGE_SUFFIXES:
            return self._extract_image(source_path, policy)
        raise ValueError(f"Unsupported source type: {source_path.suffix}")

    def _extract_pdf(self, source_path: Path, policy: ExtractionPolicy) -> DocumentExtractionResult:
        pages: list[PageExtractionMetadata] = []
        with fitz.open(source_path) as document:
            for index, page in enumerate(document, start=1):
                embedded = page.get_text("text").strip()
                if policy.prefer_embedded_text and _is_meaningful(embedded):
                    pages.append(PageExtractionMetadata(source_path, index, DocumentKind.SEARCHABLE_PDF, ExtractionMethod.EMBEDDED_TEXT, embedded, _normalize(embedded), confidence=1.0))
                    continue
                if policy.allow_ocr_fallback and self._ocr_service is not None:
                    image_bytes = _render_page_png(page)
                    ocr_result = self._ocr_service.recognize(OCRRequest((OCRPageRequest(source_path, index, image_bytes, "image/png", f"{source_path.name}:{index}"),)))
                    if ocr_result.pages:
                        result = ocr_result.pages[0]
                        method = ExtractionMethod.OCR
                        kind = DocumentKind.SCANNED_PDF if not embedded else DocumentKind.MIXED_PDF
                        pages.append(PageExtractionMetadata(source_path, index, kind, method, result.text, _normalize(result.text), confidence=result.confidence, warnings=result.warnings, errors=tuple(error.message for error in ocr_result.errors), trace_id=f"{source_path.name}:{index}"))
                    else:
                        pages.append(PageExtractionMetadata(source_path, index, DocumentKind.SCANNED_PDF, ExtractionMethod.NOT_EXTRACTED, embedded, _normalize(embedded), errors=tuple(error.message for error in ocr_result.errors), trace_id=f"{source_path.name}:{index}"))
                    continue
                pages.append(PageExtractionMetadata(source_path, index, DocumentKind.SCANNED_PDF, ExtractionMethod.NOT_EXTRACTED, embedded, _normalize(embedded), warnings=("No meaningful embedded text and OCR unavailable",), trace_id=f"{source_path.name}:{index}"))
        document_kind = DocumentKind.MIXED_PDF if any(page.document_kind is DocumentKind.SCANNED_PDF for page in pages) and any(page.extraction_method is ExtractionMethod.EMBEDDED_TEXT for page in pages) else (pages[0].document_kind if pages else DocumentKind.SEARCHABLE_PDF)
        return DocumentExtractionResult(source_path, document_kind, tuple(pages))

    def _extract_image(self, source_path: Path, policy: ExtractionPolicy) -> DocumentExtractionResult:
        if not policy.allow_ocr_fallback or self._ocr_service is None:
            page = PageExtractionMetadata(source_path, 1, DocumentKind.IMAGE, ExtractionMethod.NOT_EXTRACTED, "", warnings=("OCR unavailable",), trace_id=source_path.name)
            return DocumentExtractionResult(source_path, DocumentKind.IMAGE, (page,))
        mime = "image/jpeg" if source_path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{source_path.suffix.lower().lstrip('.')}"
        result = self._ocr_service.recognize(OCRRequest((OCRPageRequest(source_path, 1, source_path.read_bytes(), mime, source_path.name),)))
        if result.pages:
            page_result = result.pages[0]
            page = PageExtractionMetadata(source_path, 1, DocumentKind.IMAGE, ExtractionMethod.OCR, page_result.text, _normalize(page_result.text), confidence=page_result.confidence, warnings=page_result.warnings, errors=tuple(error.message for error in result.errors), trace_id=source_path.name)
        else:
            page = PageExtractionMetadata(source_path, 1, DocumentKind.IMAGE, ExtractionMethod.NOT_EXTRACTED, "", errors=tuple(error.message for error in result.errors), trace_id=source_path.name)
        return DocumentExtractionResult(source_path, DocumentKind.IMAGE, (page,))


def _render_page_png(page: fitz.Page) -> bytes:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    return pixmap.tobytes("png")


def _is_meaningful(text: str) -> bool:
    compact = "".join(text.split())
    return len(compact) >= MEANINGFUL_TEXT_LENGTH


def _normalize(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())
