from __future__ import annotations

from pathlib import Path

from engines.common.guardrails import scan_hardcoded_credentials


def test_env_file_is_ignored_by_git(project_root):
    gitignore = (project_root / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    assert "data/auth/" in gitignore
    assert "data/portfolio/" in gitignore


def test_env_example_exists_without_live_values(project_root):
    env_example = project_root / ".env.example"
    assert env_example.exists()

    assignments = {}
    for line in env_example.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        assignments[key.strip()] = value.strip()

    assert "VEDA_RUNTIME_ENV" in assignments
    assert assignments["VEDA_RUNTIME_ENV"] == "local"
    assert assignments["VEDA_AUTH_ENABLED"] == "false"
    for key, value in assignments.items():
        if key in {"VEDA_RUNTIME_ENV", "VEDA_AUTH_ENABLED"}:
            continue
        assert value == ""


def test_backend_and_engines_have_no_hardcoded_credentials(project_root):
    backend_hits = scan_hardcoded_credentials(project_root / "backend")
    engine_hits = scan_hardcoded_credentials(project_root / "engines")
    assert backend_hits == []
    assert engine_hits == []
