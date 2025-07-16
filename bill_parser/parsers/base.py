"""Base invoice parser interface.
All supplier-specific parsers must inherit from this class and implement
`can_parse` and `parse` methods.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List

from ..models import Invoice


class BaseParser(ABC):
    """Abstract base class for invoice parsers."""

    name: str = "base"
    supplier_keywords: List[str] = []  # Words expected in the invoice header

    @classmethod
    def can_parse(cls, text: str) -> bool:
        """Return True if this parser is suitable for given raw text."""
        if not cls.supplier_keywords:
            return False
        return all(re.search(k, text, re.IGNORECASE) for k in cls.supplier_keywords)

    @classmethod
    @abstractmethod
    def parse(cls, text: str, tables: list) -> Invoice:  # noqa: D401
        """Parse the invoice and return populated Invoice object."""

    # Optional score (higher = better) for parser selection if multiple match.
    priority: int = 0
