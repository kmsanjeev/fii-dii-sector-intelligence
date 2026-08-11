from engines.ai.research.platform.external_providers import RequestsDirectRetrievalProvider
from engines.ai.research.platform.providers import ProviderDocument
from engines.ai.research.platform.contracts import EvidenceType
from engines.ai.knowledge.yoga_dosha_research_p017_r1 import build_r1_bundle, validate_r1_bundle


def test_p017_r1_external_extraction_prefers_claim_relevant_passage():
    provider = RequestsDirectRetrievalProvider()
    document = ProviderDocument(
        source_uri="https://example.com/classical-text",
        source_title="Classical Yoga Text",
        source_type=EvidenceType.WEB_REFERENCE,
        metadata={
            "claim_text": "Gaja Kesari Yoga formation",
            "normalized_claim": "gaja kesari yoga formation",
        },
    )
    content = ("Home About Contact Navigation " * 200) + (
        "Gajakesari yoga: When Jupiter is in a quadrant from the Moon, it is known as Kesari Yoga."
    )

    evidence = provider.extract(document, content=content)

    assert len(evidence) == 1
    assert evidence[0].claim_hint == "Gaja Kesari Yoga formation"
    assert evidence[0].normalized_text == "gaja kesari yoga formation"
    assert "Gajakesari yoga" in evidence[0].passage
    assert len(evidence[0].passage) < len(content)


def test_p017_r1_binds_promoted_formation_to_p017_rule_without_activation():
    bundle = build_r1_bundle()
    assert validate_r1_bundle(bundle)["is_valid"] is True
    assert bundle["promotion"]["promotion_status"] == "PROMOTED"
    assert bundle["promotion"]["preflight"] == "PASS_WITH_CONDITIONS"
    binding = bundle["rule_bindings"][0]
    assert binding["claim_id"] == "VEDA-CLM-000013"
    assert binding["p017_rule_id"] == "VEDA-RUL-YOGA-000001"
    assert binding["production_status"] == "INACTIVE"
    assert bundle["summary"]["production_capabilities_activated"] == 0


def test_p017_r1_keeps_unproven_pilots_blocked_or_research_required():
    pilots = {item["pilot_id"]: item for item in build_r1_bundle()["pilots"]}
    assert pilots["A"]["formation_status"] == "APPROVED_WITH_CONDITIONS"
    assert pilots["B"]["formation_status"] == "FORMATION_UNVERIFIED"
    assert pilots["C"]["formation_status"] == "FORMATION_UNVERIFIED"
    assert pilots["D"]["formation_status"] == "FORMATION_UNVERIFIED"
    assert pilots["E"]["formation_status"] == "PARTIALLY_SUPPORTED"
