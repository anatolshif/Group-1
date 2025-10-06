# group_scan_main.py
"""
Compatibility shim that exposes `group_scan(...)` at repo root.
It delegates to app.alt_group1proj or app.group1proj (whichever is present).
This allows orchestrator.py to import `group_scan` without changing orchestrator.
"""

import importlib
import os
import sys
import traceback
from typing import Any, Dict

# Ensure repo's app/ folder is importable
ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


def _load_candidate(names):
    """Try to import the first module in names list and return the module if found."""
    for nm in names:
        try:
            mod = importlib.import_module(nm)
            return mod
        except Exception:
            continue
    return None


# Candidate modules (prefer alt_group1proj, then group1proj)
_candidate_mod = _load_candidate(["alt_group1proj", "group1proj", "app.alt_group1proj", "app.group1proj"])

def _find_callable(mod):
    """Try common function names used as entrypoints inside scan modules."""
    if mod is None:
        return None
    for name in ("group_scan", "main", "scan", "run_scan"):
        if hasattr(mod, name):
            return getattr(mod, name)
    return None


_delegate = _find_callable(_candidate_mod)


def group_scan(**kwargs) -> Any:
    """
    Uniform entrypoint used by orchestrator.py.

    Expected kwargs (examples):
        apk_path, package, dynamic (bool), run_data_extraction (bool)

    Behavior:
      - Calls the delegate function with keyword args where possible.
      - If delegate expects positional args, attempts to pass common ones.
      - Returns whatever the delegate returns, or an error-shaped dict if it fails.
    """
    if _delegate is None:
        return {"metadata": {}, "findings": [{"type": "error", "message": "No scan implementation found (alt_group1proj/group1proj)."}], "summary": {}}

    try:
        # Attempt to call delegate using kwargs (preferred)
        try:
            return _delegate(**kwargs)
        except TypeError:
            # Fallback: try calling with common positional signature
            apk = kwargs.get("apk_path") or kwargs.get("apk") or kwargs.get("apk_file")
            package = kwargs.get("package")
            dynamic = kwargs.get("dynamic", True)
            # Try common positional calls with many combinations
            try:
                return _delegate(apk, package, dynamic)
            except Exception:
                # Last resort: call with no args
                return _delegate()
    except Exception as e:
        # Return an error structure that orchestrator will understand
        tb = traceback.format_exc()
        return {
            "metadata": {},
            "findings": [{"type": "error", "message": f"Delegate scan failed: {type(e).__name__}: {e}"}],
            "summary": {},
            "debug_traceback": tb
        }


# Small check when run directly
if __name__ == "__main__":
    import json, sys
    res = group_scan(apk_path=(sys.argv[1] if len(sys.argv) > 1 else None), package=(sys.argv[2] if len(sys.argv) > 2 else None))
    print(json.dumps(res, indent=2))
