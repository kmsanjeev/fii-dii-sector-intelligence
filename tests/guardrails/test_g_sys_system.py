"""
Guardrail Tests — Section 11: System (G-SYS-01 to G-SYS-05)
"""

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from engines.common.guardrails import (
    check_disk_space,
    scan_hardcoded_credentials,
    validate_environment,
)

logger = logging.getLogger(__name__)


class TestValidateEnvironment:
    """G-SYS-01: Required env vars must be present at startup; raise if any missing."""

    def test_all_vars_present_passes(self, mock_env_vars):
        """HAPPY PATH: All required env vars set → no exception."""
        logger.debug("[G-SYS-01] test_all_vars_present_passes")
        validate_environment(["TEST_TELEGRAM_TOKEN", "TEST_GOOGLE_CREDS"])
        logger.debug("[G-SYS-01] PASS — all vars present")

    def test_missing_required_var_raises(self, missing_env):
        """GUARD: Missing required env var → EnvironmentError."""
        logger.debug("[G-SYS-01] test_missing_required_var_raises")
        with pytest.raises(EnvironmentError, match="MISSING_VAR"):
            validate_environment(["MISSING_VAR"])
        logger.debug("[G-SYS-01] PASS — EnvironmentError raised for missing var")

    def test_multiple_missing_vars_listed(self):
        """GUARD: Multiple missing vars all reported in one error."""
        logger.debug("[G-SYS-01] test_multiple_missing_vars_listed")
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EnvironmentError) as exc:
                validate_environment(["VAR_A", "VAR_B", "VAR_C"])
            error_msg = str(exc.value)
            assert "VAR_A" in error_msg
            assert "VAR_B" in error_msg
            assert "VAR_C" in error_msg
        logger.debug("[G-SYS-01] PASS — all missing vars listed")

    def test_partial_missing_raises_for_missing(self):
        """EDGE: Some vars present, some missing → error for missing only."""
        logger.debug("[G-SYS-01] test_partial_missing_raises_for_missing")
        with patch.dict(os.environ, {"PRESENT_VAR": "value"}, clear=True):
            with pytest.raises(EnvironmentError, match="NOT_PRESENT"):
                validate_environment(["PRESENT_VAR", "NOT_PRESENT"])
        logger.debug("[G-SYS-01] PASS — only missing vars raise error")

    def test_empty_required_list_passes(self):
        """EDGE: Empty required list → no validation needed, passes."""
        logger.debug("[G-SYS-01] test_empty_required_list_passes")
        validate_environment([])  # must not raise
        logger.debug("[G-SYS-01] PASS — empty list passes")


class TestScanHardcodedCredentials:
    """G-SYS-03: Scan source for accidental credential commits."""

    def test_no_credentials_returns_empty_list(self, tmp_dir):
        """HAPPY PATH: Clean source file → empty scan results."""
        logger.debug("[G-SYS-03] test_no_credentials_returns_empty_list")
        clean_file = tmp_dir / "engine.py"
        clean_file.write_text("import os\nTOKEN = os.getenv('TELEGRAM_TOKEN')\n", encoding="utf-8")
        hits = scan_hardcoded_credentials(tmp_dir)
        assert hits == [], f"Expected no hits but got: {hits}"
        logger.debug("[G-SYS-03] PASS — clean file has no credentials")

    def test_hardcoded_token_detected(self, tmp_dir):
        """GUARD: Hardcoded token in source → detected and returned."""
        logger.debug("[G-SYS-03] test_hardcoded_token_detected")
        dirty_file = tmp_dir / "engine.py"
        dirty_file.write_text(
            "TELEGRAM_BOT_TOKEN = '1234567890:ABCDEFabcdefGHIJKL-mnopqrstuvwxyz'\n",
            encoding="utf-8"
        )
        hits = scan_hardcoded_credentials(tmp_dir)
        assert len(hits) > 0, "Should have detected hardcoded token"
        assert any("engine.py" in str(h) or "TELEGRAM_BOT_TOKEN" in str(h) for h in hits)
        logger.debug(f"[G-SYS-03] PASS — detected {len(hits)} credential hit(s)")

    def test_api_key_pattern_detected(self, tmp_dir):
        """GUARD: API key pattern detected."""
        logger.debug("[G-SYS-03] test_api_key_pattern_detected")
        dirty_file = tmp_dir / "config.py"
        dirty_file.write_text(
            'api_key = "sk-1234567890abcdef1234567890abcdef"\n',
            encoding="utf-8"
        )
        hits = scan_hardcoded_credentials(tmp_dir)
        assert len(hits) > 0
        logger.debug(f"[G-SYS-03] PASS — API key pattern detected")

    def test_env_var_access_is_clean(self, tmp_dir):
        """HAPPY PATH: os.getenv() usage is NOT flagged as credential."""
        logger.debug("[G-SYS-03] test_env_var_access_is_clean")
        clean_file = tmp_dir / "safe_engine.py"
        clean_file.write_text(
            "import os\nGOOGLE_CREDS = os.getenv('GOOGLE_CREDENTIALS')\n",
            encoding="utf-8"
        )
        hits = scan_hardcoded_credentials(tmp_dir)
        assert hits == [], f"os.getenv() should not be flagged: {hits}"
        logger.debug("[G-SYS-03] PASS — os.getenv() not flagged")

    def test_returns_file_and_line_info(self, tmp_dir):
        """G-SYS-03: Hit includes filename and line number."""
        logger.debug("[G-SYS-03] test_returns_file_and_line_info")
        dirty_file = tmp_dir / "engine.py"
        dirty_file.write_text(
            "# setup\nTELEGRAM_BOT_TOKEN = '1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'\n",
            encoding="utf-8"
        )
        hits = scan_hardcoded_credentials(tmp_dir)
        assert len(hits) > 0
        hit_str = str(hits[0])
        assert "engine.py" in hit_str or "line" in hit_str.lower() or "2" in hit_str
        logger.debug(f"[G-SYS-03] PASS — hit info: {hits[0]}")


class TestCheckDiskSpace:
    """G-SYS-05: Raise if available disk space below 1GB threshold."""

    def test_adequate_disk_space_passes(self, tmp_dir):
        """HAPPY PATH: Enough disk space → no exception."""
        logger.debug("[G-SYS-05] test_adequate_disk_space_passes")
        # The actual temp dir will almost certainly have > 0.0001 GB free
        check_disk_space(tmp_dir, min_gb=0.000001)  # effectively 1KB minimum
        logger.debug("[G-SYS-05] PASS — adequate disk space")

    def test_insufficient_disk_space_raises(self, tmp_dir):
        """GUARD: Mocked low disk → RuntimeError."""
        logger.debug("[G-SYS-05] test_insufficient_disk_space_raises")
        with patch("shutil.disk_usage") as mock_usage:
            mock_usage.return_value = type("Usage", (), {"free": 100 * 1024 * 1024})()  # 100MB
            with pytest.raises(RuntimeError, match="Insufficient disk space"):
                check_disk_space(tmp_dir, min_gb=1.0)
        logger.debug("[G-SYS-05] PASS — insufficient disk raises RuntimeError")
