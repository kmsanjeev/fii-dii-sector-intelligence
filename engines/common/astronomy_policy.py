"""Governed astronomical calculation policy for VEDA.

This module deliberately chooses Moshier (MOSEPH) for the current local
runtime.  Swiss Ephemeris silently falls back to Moshier when Swiss data files
are unavailable; callers must use :func:`calc_ut` so that the returned
ephemeris flag is asserted instead of allowing an unnoticed backend change.
"""

from __future__ import annotations

from typing import Any


POLICY_ID = "VEDA-ASTRONOMY-BACKEND-001"
POLICY_VERSION = "1.0.0"
REQUESTED_BACKEND = "MOSEPH"
EXPECTED_BACKEND_FLAG_NAME = "FLG_MOSEPH"
EPHEMERIS_FILE_SET = "NONE_REQUIRED_FOR_MOSEPH"
FAIL_ON_UNAUTHORIZED_FALLBACK = True


def _backend_flag(swe: Any) -> int:
    return int(getattr(swe, EXPECTED_BACKEND_FLAG_NAME))


def backend_name_from_flags(swe: Any, flags: int) -> str:
    """Return the single Swiss backend represented by returned flags."""

    mask = int(swe.FLG_JPLEPH | swe.FLG_SWIEPH | swe.FLG_MOSEPH)
    selected = int(flags) & mask
    names = {
        int(swe.FLG_JPLEPH): "JPLEPH",
        int(swe.FLG_SWIEPH): "SWIEPH",
        int(swe.FLG_MOSEPH): "MOSEPH",
    }
    return names.get(selected, "UNKNOWN")


def assert_backend_flags(swe: Any, returned_flags: int) -> str:
    """Assert that Swiss returned the governed local ephemeris backend."""

    actual = backend_name_from_flags(swe, returned_flags)
    if FAIL_ON_UNAUTHORIZED_FALLBACK and actual != REQUESTED_BACKEND:
        raise RuntimeError(
            f"Unauthorized ephemeris backend: expected {REQUESTED_BACKEND}, "
            f"received {actual} (flags={returned_flags})"
        )
    return actual


def calc_ut(swe: Any, jd_ut: float, body: int, flags: int):
    """Call ``swe.calc_ut`` with explicit MOSEPH and assert its return flag."""

    requested = int(flags) | _backend_flag(swe)
    values, returned_flags = swe.calc_ut(jd_ut, body, requested)
    assert_backend_flags(swe, returned_flags)
    return values, returned_flags


def calc(swe: Any, jd_et: float, body: int, flags: int):
    """Call ``swe.calc`` with explicit MOSEPH and assert its return flag."""

    requested = int(flags) | _backend_flag(swe)
    values, returned_flags = swe.calc(jd_et, body, requested)
    assert_backend_flags(swe, returned_flags)
    return values, returned_flags


def policy_payload(swe: Any) -> dict[str, object]:
    """Return deterministic metadata for documentation and benchmark hashes."""

    import importlib.metadata

    return {
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "requested_backend": REQUESTED_BACKEND,
        "expected_backend_flag": EXPECTED_BACKEND_FLAG_NAME,
        "ephemeris_file_set": EPHEMERIS_FILE_SET,
        "configured_ephemeris_path": None,
        "library_package": "pyswisseph",
        "library_version": importlib.metadata.version("pyswisseph"),
        "library_runtime_version": getattr(swe, "version", None),
        "fail_on_unauthorized_fallback": FAIL_ON_UNAUTHORIZED_FALLBACK,
        "actual_backend_probe": backend_name_from_flags(
            swe, swe.calc_ut(2451545.0, swe.SUN, int(swe.FLG_MOSEPH))[1]
        ),
    }
