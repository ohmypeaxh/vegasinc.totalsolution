"""Extensible URS parsing, classification, and customer strategy boundaries."""

from __future__ import annotations

from abc import ABC, abstractmethod

from vegas_doc.models.extraction import DocumentExtractionResult
from vegas_doc.models.urs import URSRequirement


class URSParser(ABC):
    """Boundary for future URS parsing algorithms."""

    @abstractmethod
    def parse(self, extraction: DocumentExtractionResult) -> tuple[URSRequirement, ...]:
        """Parse requirements from extracted text."""


class URSClassifier(ABC):
    """Boundary for future requirement classification algorithms."""

    @abstractmethod
    def classify(self, requirement: URSRequirement) -> URSRequirement:
        """Return a classified requirement without mutating the original."""


class CustomerStrategy(ABC):
    """Boundary for customer-specific parsing/classification policies."""

    @abstractmethod
    def strategy_name(self) -> str:
        """Return a stable strategy name."""
