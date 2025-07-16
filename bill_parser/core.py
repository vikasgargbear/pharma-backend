"""High-level entry point for bill parsing.

Usage::
    from bill_parser import parse_pdf
    invoice = parse_pdf("/path/to/invoice.pdf")

The function tries each registered parser (supplier-specific or generic)
until one succeeds.  It returns an `Invoice` object ready to be saved to
the database or serialised to JSON.
"""
from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import List, Type

from rapidfuzz import fuzz

from .extractor import ExtractionError, extract
from .models import Invoice
from .parsers.base import BaseParser

LOGGER = logging.getLogger(__name__)

# --- Dynamically discover parser subclasses ---------------------------------

# Any module imported here that defines a subclass of BaseParser will be
# registered automatically via BaseParser.__subclasses__().  We import the
# generic parser explicitly and *attempt* to import custom ones placed by users.
importlib.import_module("bill_parser.parsers.generic")

# Auto-import any *.py in parsers directory (except __init__) to register them.
for _p in (Path(__file__).parent / "parsers").glob("*.py"):
    if _p.stem not in {"__init__", "generic", "base"}:
        importlib.import_module(f"bill_parser.parsers.{_p.stem}")


# ---------------------------------------------------------------------------

def _rank_parsers(text: str) -> List[Type[BaseParser]]:
    """Return parsers ordered by suitability for given text."""
    candidates: List[Type[BaseParser]] = []
    for cls in BaseParser.__subclasses__():
        if cls is BaseParser:  # pragma: no cover
            continue
        # Supplier keyword quick check
        if cls.can_parse(text):
            candidates.append(cls)
        else:
            # Fuzzy ratio fallback (>80 considered match)
            if any(fuzz.partial_ratio(k, text) > 80 for k in cls.supplier_keywords):
                candidates.append(cls)
    # Prioritise explicit matches, then higher priority attribute
    return sorted(candidates, key=lambda c: (-c.priority, c.__name__))


def parse_pdf(pdf_path: str | Path | bytes) -> Invoice:
    """Extract raw text/tables then parse invoice via suitable parser."""
    raw_text, tables = extract(pdf_path)

    for parser_cls in _rank_parsers(raw_text):
        LOGGER.debug("Trying parser %s", parser_cls.__name__)
        try:
            invoice = parser_cls.parse(raw_text, tables)
            invoice.raw_text = raw_text  # type: ignore[assignment]
            return invoice
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Parser %s failed: %s", parser_cls.__name__, exc)

    # Finally fall back to GenericParser (always last in ranking)
    from .parsers.generic import GenericParser

    invoice = GenericParser.parse(raw_text, tables)
    invoice.raw_text = raw_text  # type: ignore[assignment]
    return invoice
