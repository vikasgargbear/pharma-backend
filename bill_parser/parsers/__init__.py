"""Register built-in parsers."""
from importlib import import_module, reload

# Ensure base and generic are imported so that they register subclasses.
import_module("bill_parser.parsers.base")
import_module("bill_parser.parsers.generic")
