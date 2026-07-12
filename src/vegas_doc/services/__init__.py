"""Service abstractions for Vegas Total Solution Doc."""

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
    "CustomerStrategy",
    "DQProjectRepository",
    "DocumentTextExtractor",
    "ExtractionPolicyEvaluator",
    "MalformedProjectError",
    "OCRProvider",
    "OCRService",
    "ProjectAlreadyExistsError",
    "ProjectPersistenceError",
    "ProviderOCRService",
    "URSClassifier",
    "URSParser",
    "UnsupportedProjectVersionError",
]
