from engines.ai.knowledge.strength_governance import (
    build_r1_bundle,
    r1_aspect_foundation,
    r1_motion_facts,
    r1_source_quality,
    validate_r1_bundle,
)


def test_p018_r1_records_executed_research_without_auto_promotion():
    bundle = build_r1_bundle()
    validation = validate_r1_bundle(bundle)
    assert validation["is_valid"] is True
    assert bundle["research_execution"]["missions_executed"] == 3
    assert bundle["research_execution"]["external_queries"] == 3
    assert bundle["summary"]["approved_core_promotions"] == 0
    assert all(claim["promotion_status"] == "NOT_PROMOTED" for claim in bundle["claims"])


def test_p018_r1_reports_source_family_concentration_honestly():
    quality = r1_source_quality()
    assert quality["sources_accepted"] == 7
    assert quality["independent_source_families"] == 1
    assert quality["classical_primary_sources"] == 0
    assert "one Wisdom Library domain" in quality["limitation"]


def test_p018_r1_keeps_numeric_drik_blocked():
    aspect = r1_aspect_foundation()
    assert aspect["existing_inventory"]["executable_aspect_engine"] is False
    assert "verified aspect geometry/contribution method" in aspect["remaining_blockers"]


def test_p018_r1_keeps_cheshta_blocked_without_motion_facts():
    motion = r1_motion_facts()
    assert motion["existing_facts"]["retrograde"] is True
    assert motion["existing_facts"]["speed"] is False
    assert motion["status"] == "BLOCKED_BY_MOTION_FACTS"


def test_p018_r1_preserves_prior_yoga_dosha_backlog():
    assert build_r1_bundle()["summary"]["p017_backlog_preserved"] is True
