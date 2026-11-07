"""Mart plugins. One module per mart; each defines NAME and build(con) -> DataFrame.

A mart is a small derived table committed under marts/ so the dashboard runs without
raw data. Keep each under 5 MB (tests/test_marts.py enforces it). Add a module here,
then run `uv run python -m royale.build`.
"""
from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType


def modules() -> list[ModuleType]:
    """Every mart module in this package, sorted by name."""
    found = []
    for info in pkgutil.iter_modules(__path__):
        mod = importlib.import_module(f"{__name__}.{info.name}")
        if hasattr(mod, "NAME") and hasattr(mod, "build"):
            found.append(mod)
    return sorted(found, key=lambda m: m.NAME)
