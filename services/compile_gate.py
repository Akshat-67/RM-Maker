"""
services/compile_gate.py
------------------------
Server-side safety gate for document compilation.

Mirrors the critical-field validation that the frontend performs before
allowing the "Generate" button to be clicked.  Call
``check_compile_prerequisites`` in generation routes *before* delegating to
``compile_and_render_document``; this prevents direct API callers (curl,
Playwright tests, malicious actors) from bypassing the UI safeguard.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Critical field definitions
# ---------------------------------------------------------------------------

# RM: fields that MUST be present (non-empty) in session data before compile.
_RM_CRITICAL: list[tuple[str, str]] = [
    # (dot-separated data path,  human-readable label)
    ("bs.0.n",  "Borrower 1 – Name"),
    ("bsign.n", "Bank Signatory – Name"),
    ("ps.0.adr", "Property 1 – Address"),
    ("rd",      "Execution Date"),
]

# SD: critical fields for Sale Deed compile.
_SD_CRITICAL: list[tuple[str, str]] = [
    ("ss.0.n", "Seller 1 – Name"),
    ("bs.0.n", "Buyer 1 – Name"),
    ("ps.0.adr", "Property – Address"),
    ("rd",     "Execution Date"),
]


def _resolve_path(data: dict, dotpath: str) -> str:
    """Walk a dot-separated path into nested dicts/lists.

    Returns the string value at the path, or '' if anything is missing.
    Supports list indexing via integer path segments, e.g. "bs.0.n".
    """
    parts = dotpath.split(".")
    node: object = data
    for part in parts:
        if isinstance(node, dict):
            node = node.get(part, "")
        elif isinstance(node, list):
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                return ""
        else:
            return ""
    return str(node).strip() if node else ""


def check_compile_prerequisites(session: dict, doc_type: str) -> list[str]:
    """Validate that all critical fields are present before compile.

    Args:
        session: The loaded case session dict (as returned by
            ``load_case_session``).
        doc_type: ``"RM"`` or ``"SD"``.

    Returns:
        A list of human-readable missing-field labels.  Empty list means
        the gate is cleared and compilation may proceed.
    """
    data = session.get("data", {})
    critical = _RM_CRITICAL if doc_type == "RM" else _SD_CRITICAL
    missing: list[str] = []
    for dotpath, label in critical:
        if not _resolve_path(data, dotpath):
            missing.append(label)
    return missing
