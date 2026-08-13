from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from backend.main import app
from backend.routers.career_validation import get_validated_profiles
from engines.career.veda_p021_engine import build_phase_bundle, export_phase_bundle, load_validated_profiles, validate_bundle
from engines.common import config as cfg


def test_p021_bundle_tracks_shadow_only_validation():
    bundle = build_phase_bundle()
    report = validate_bundle(bundle)

    assert report["is_valid"] is True
    assert bundle["summary"]["profiles_total"] >= 10_000
    assert bundle["summary"]["canonical_rows"] > 0
    assert bundle["summary"]["synthetic_rows"] > bundle["summary"]["canonical_rows"]
    assert bundle["summary"]["synthetic_rate"] > 0.5
    assert len(bundle["domain_registry"]) == 6
    assert bundle["evidence_contract"]["requires_provenance_for_every_row"] is True
    assert bundle["shadow_validation"]["is_valid"] is True


def test_p021_csv_has_required_schema_and_provenance():
    df, summary = load_validated_profiles(limit=5)

    required = {
        "symbol",
        "domain_id",
        "role_id",
        "canonical_role",
        "detected_synonyms",
        "skills",
        "industry",
        "confidence_score",
        "provenance",
        "shadow_payload_id",
        "created_at",
        "validated_by",
    }

    assert required.issubset(set(df.columns))
    assert summary["profiles_total"] >= 10_000
    assert df["confidence_score"].between(0, 1).all()
    assert df["provenance"].astype(str).str.contains("kundli_signals.csv").all()
    assert df["validated_by"].eq("automated").all()

    parsed = json.loads(df.iloc[0]["provenance"])
    assert isinstance(parsed, list)
    assert parsed[0]["source"] == "kundli_signals.csv"


def test_p021_export_writes_csv_bundle_docs_and_schema(tmp_path):
    root = tmp_path
    output_path = root / "data" / "veda" / "career_validated_profiles.csv"
    validation_dir = root / "data" / "veda" / "validation" / "capabilities"

    written = export_phase_bundle(root=root, output_path=output_path, validation_dir=validation_dir)

    expected = {
        output_path,
        validation_dir / "p021_career_bundle.json",
        validation_dir / "p021_career_registry.json",
        validation_dir / "p021_career_validation.json",
        root / "docs" / "current-state" / "p021" / "VEDA-P021-00_EXECUTIVE_SUMMARY.md",
        root / "docs" / "current-state" / "p021" / "VEDA-P021-01_VALIDATION_AND_SHADOWS.md",
    }

    assert expected.issubset(set(written))
    for path in expected:
        assert Path(path).exists()

    df = pd.read_csv(output_path)
    assert len(df) >= 10_000
    assert {"symbol", "role_id", "canonical_role"}.issubset(df.columns)


def test_p021_route_is_registered_and_returns_profiles():
    assert "/api/career/validated" in app.openapi()["paths"]

    response = get_validated_profiles(limit=3)

    assert response["total"] >= 10_000
    assert response["returned"] == 3
    assert response["summary"]["synthetic_rows"] > 0
    assert response["records"][0]["canonical_role"]
    assert "shadow_payload_id" in response["records"][0]
