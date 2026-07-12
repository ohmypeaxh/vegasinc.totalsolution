"""Secret storage abstraction for provider credentials."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

import keyring


class SecretStore(ABC):
    """Boundary for storing secrets outside project/config files."""

    @abstractmethod
    def get_secret(self, key: str) -> str:
        """Return a secret value or an empty string."""

    @abstractmethod
    def set_secret(self, key: str, value: str) -> None:
        """Persist a secret value."""


class KeyringSecretStore(SecretStore):
    """Keyring-backed secret store with environment fallback."""

    def __init__(self, service_name: str = "VegasTotalSolutionDoc") -> None:
        self._service_name = service_name

    def get_secret(self, key: str) -> str:
        """Return a keyring secret with VEGAS_CLOVA_SECRET_KEY fallback."""

        if key == "clova_secret_key":
            env_value = os.getenv("VEGAS_CLOVA_SECRET_KEY", "")
            if env_value:
                return env_value
        try:
            return keyring.get_password(self._service_name, key) or ""
        except Exception:
            return ""

    def set_secret(self, key: str, value: str) -> None:
        """Persist the secret in the OS keyring when non-empty."""

        if value:
            keyring.set_password(self._service_name, key, value)
