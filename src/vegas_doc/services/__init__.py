"""Service abstractions for Vegas Total Solution Doc."""

from vegas_doc.services.clova_ocr import ClovaOCRProvider, ClovaOCRSettings
from vegas_doc.services.document_extraction import PyMuPDFDocumentTextExtractor
from vegas_doc.services.docx_generator import DQDocxGenerator
from vegas_doc.services.dq_processing import DQProjectValidator, DQSuggestionService, DefaultURSParser, KeywordRequirementClassifier
from vegas_doc.services.extraction import DocumentTextExtractor, ExtractionPolicyEvaluator
from vegas_doc.services.ocr import OCRProvider, OCRService, ProviderOCRService
from vegas_doc.services.project_persistence import (
    DQProjectRepository,
    MalformedProjectError,
    ProjectAlreadyExistsError,
    ProjectPersistenceError,
    UnsupportedProjectVersionError,
)
from vegas_doc.services.urs_analysis import CustomerStrategy, URSClassifier, URSParser

__all__ = [
    "ClovaOCRProvider",
    "ClovaOCRSettings",
    "CustomerStrategy",
    "DQProjectRepository",
    "DQDocxGenerator",
    "DQProjectValidator",
    "DQSuggestionService",
    "DefaultURSParser",
    "DocumentTextExtractor",
    "ExtractionPolicyEvaluator",
    "KeywordRequirementClassifier",
    "MalformedProjectError",
    "OCRProvider",
    "OCRService",
    "ProjectAlreadyExistsError",
    "PyMuPDFDocumentTextExtractor",
    "ProjectPersistenceError",
    "ProviderOCRService",
    "URSClassifier",
    "URSParser",
    "UnsupportedProjectVersionError",
]
