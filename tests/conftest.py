"""
conftest.py — pytest configuration for krff-shell tests.

Imports kr_dart_pipeline so its __init__ registers the package directory on
sys.path. This lets test files use bare module names (import extract_dart,
import transform, from pipeline import ...) that resolve to the canonical
installed package rather than the stale pre-split 02_Pipeline/ copy.
"""

import kr_dart_pipeline  # noqa: F401 — registers kr_dart_pipeline/ on sys.path
