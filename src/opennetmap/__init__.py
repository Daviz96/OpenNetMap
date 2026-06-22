"""Shim package `opennetmap` for gradual migration.

This module re-exports the existing `network_inventory` package under
`opennetmap` to provide a stable import path while we migrate code into
`src/opennetmap` progressively.
"""

try:
    # Import the old package and re-export its public names
    import importlib

    _old = importlib.import_module("network_inventory")
    # Expose as a submodule for compatibility
    import sys

    sys.modules["opennetmap.network_inventory"] = _old
except Exception:
    # If import fails, keep shim minimal to avoid breaking imports.
    pass

__all__ = ["network_inventory"]
