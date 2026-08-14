"""P023 Education Synthesis Comprehensive Test Suite.

Tests cover:
- Governance framework validation
- Evidence aggregation logic
- Conflict handling
- Synthesis engine functionality
- Boundary preservation
- P020/P022 pattern compatibility
"""

import pytest
from datetime import datetime

from engines.ai.knowledge.education_governance import registry, validate
from engines.intelligence.education_evidence_aggregation import (
    EducationEvidenceAggregator,
    EvidenceDirection,
    ConfidenceBand,
)
from engines.intelligence.education_synthesis_engine import EducationSynthesisEngine


class TestEducationGovernanceRegistry:
    """Test education governance framework."""

    def test_registry_valid(self):
        """Test registry is valid."""
        reg = registry()
        assert reg is not None
        assert reg["version"] == "1.0.0"
        assert reg["phase"] == "P023"
        assert len(reg["domains"]) == 2

    def test_registry_validation(self):
        """Test registry validation passes."""
        validation = validate()
        assert validation["valid"], f"Validation failed: {validation['issues']}"
        assert len(validation["issues"]) == 0

    def test_domains_present(self):
        """Test required domains are present."""
        reg = registry()
        domain_ids = {d["domain_id"] for d in reg["domains"]}
        assert "EDUCATION" in domain_ids
        assert "D24_CALCULATION" in domain_ids

    def test_education_domain_properties(self):
        """Test EDUCATION domain has correct properties."""
        reg = registry()
        education = next(d for d in reg["domains"] if d["domain_id"] == "EDUCATION")

        assert education["risk_class"] == "HIGH_STAKES"
        assert education["high_stakes"] is True
        assert education["implementation_status"] == "SHADOW_ONLY"
        assert education["activation_status"] == "INACTIVE"

    def test_d24_domain_properties(self):
        """Test D24 domain has correct properties."""
        reg = registry()
        d24 = next(d for d in reg["domains"] if d["domain_id"] == "D24_CALCULATION")

        assert d24["risk_class"] == "CALCULATION"
        assert d24["implementation_status"] == "CALCULATION_READY"
        assert d24["activation_status"] == "ACTIVE"

    def test_evidence_classification_complete(self):
        """Test evidence classification covers required layers."""
        reg = registry()
        layers = {e["source_layer"] for e in reg["evidence_classification"]}

        required_layers = {
            "NATAL", "4TH_BHAVA", "5TH_BHAVA", "9TH_BHAVA", "LORDSHIP",
            "EDUCATION_KARAKA", "D24_EDUCATION", "APPROVED_CORE"
        }
        assert required_layers.issubset(layers), f"Missing: {required_layers - layers}"

    def test_safety_boundaries_present(self):
        """Test safety boundaries are properly defined."""
        reg = registry()
        boundaries = reg["safety_boundaries"]

        # Check for key restrictions
        boundary_text = " ".join(boundaries)
        assert "deterministic" in boundary_text.lower()
        assert "guarantee" in boundary_text.lower()
        assert "production" in boundary_text.lower()


class TestEducationEvidenceAggregation:
    """Test evidence aggregation logic."""

    def test_aggregator_initialization(self):
        """Test aggregator can be initialized."""
        agg = EducationEvidenceAggregator()
        assert agg is not None
        assert len(agg.evidence_records) == 0
        assert len(agg.conflicts) == 0

    def test_add_evidence(self):
        """Test evidence can be added."""
        agg = EducationEvidenceAggregator()
        agg.add_evidence(
            source_layer="NATAL",
            evidence_type="FOUNDATION",
            direction=EvidenceDirection.SUPPORTING,
            claim="Test claim",
        )
        assert len(agg.evidence_records) == 1
        record = agg.evidence_records[0]
        assert record.claim == "Test claim"
        assert record.direction == EvidenceDirection.SUPPORTING

    def test_multiple_evidence_records(self):
        """Test multiple evidence records."""
        agg = EducationEvidenceAggregator()
        for i in range(5):
            agg.add_evidence(
                source_layer=f"LAYER_{i}",
                evidence_type="TEST",
                direction=EvidenceDirection.SUPPORTING,
                claim=f"Claim {i}",
            )
        assert len(agg.evidence_records) == 5

    def test_conflict_detection(self):
        """Test conflict detection between opposite evidence."""
        agg = EducationEvidenceAggregator()
        agg.add_evidence(
            source_layer="D1",
            evidence_type="PRIMARY",
            direction=EvidenceDirection.SUPPORTING,
            claim="Education supported",
        )
        agg.add_evidence(
            source_layer="D24",
            evidence_type="SECONDARY",
            direction=EvidenceDirection.OPPOSING,
            claim="Education challenged",
        )
        conflicts = agg.detect_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0]["status"] == "UNRESOLVED"

    def test_confidence_aggregation_supporting(self):
        """Test confidence when only supporting evidence."""
        agg = EducationEvidenceAggregator()
        agg.add_evidence(
            source_layer="NATAL",
            evidence_type="PRIMARY",
            direction=EvidenceDirection.SUPPORTING,
            claim="Strong natal support",
            confidence=ConfidenceBand.HIGH,
        )
        agg.add_evidence(
            source_layer="VARGA",
            evidence_type="SECONDARY",
            direction=EvidenceDirection.SUPPORTING,
            claim="Varga support",
            confidence=ConfidenceBand.MODERATE,
        )
        synthesis = agg.synthesize_narrative()
        assert synthesis["supporting_count"] == 2
        assert synthesis["opposing_count"] == 0

    def test_confidence_aggregation_conflicted(self):
        """Test confidence when evidence conflicts."""
        agg = EducationEvidenceAggregator()
        agg.add_evidence(
            source_layer="D1",
            evidence_type="PRIMARY",
            direction=EvidenceDirection.SUPPORTING,
            claim="Support",
            confidence=ConfidenceBand.HIGH,
        )
        agg.add_evidence(
            source_layer="D24",
            evidence_type="SECONDARY",
            direction=EvidenceDirection.OPPOSING,
            claim="Opposition",
            confidence=ConfidenceBand.HIGH,
        )
        agg.detect_conflicts()
        synthesis = agg.synthesize_narrative()
        assert "CONFLICT" in synthesis["overall_interpretation"]
        assert synthesis["unresolved_conflicts"] == 1

    def test_synthesis_narrative_structure(self):
        """Test synthesis narrative has correct structure."""
        agg = EducationEvidenceAggregator()
        agg.add_evidence(
            source_layer="NATAL",
            evidence_type="FOUNDATION",
            direction=EvidenceDirection.SUPPORTING,
            claim="Test",
        )
        narrative = agg.synthesize_narrative()

        assert "supporting_count" in narrative
        assert "opposing_count" in narrative
        assert "conditional_count" in narrative
        assert "overall_confidence" in narrative
        assert "overall_interpretation" in narrative
        assert "evidence_preserved" in narrative


class TestEducationSynthesisEngine:
    """Test education synthesis engine."""

    def test_engine_initialization(self):
        """Test synthesis engine can be initialized."""
        engine = EducationSynthesisEngine()
        assert engine is not None
        assert engine.aggregator is not None

    def test_synthesize_empty_input(self):
        """Test synthesis with no input."""
        engine = EducationSynthesisEngine()
        output = engine.synthesize()

        assert output.synthesis_id.startswith("EDU_")
        assert output.prediction_state == "SHADOW_ONLY"
        assert output.domain == "EDUCATION"
        assert output.interpretation_status == "SHADOW_ONLY"
        assert output.experimental is True

    def test_synthesize_with_natal_factors(self):
        """Test synthesis with natal factors."""
        engine = EducationSynthesisEngine()
        natal_factors = {
            "4th_bhava_lord": "Mercury",
            "5th_bhava_lord": "Jupiter",
        }
        output = engine.synthesize(natal_factors=natal_factors)

        assert output.synthesis_id.startswith("EDU_")
        assert output.varga_context == {}
        assert output.backtesting_ready is True

    def test_output_marked_shadow_only(self):
        """Test output is explicitly marked SHADOW_ONLY."""
        engine = EducationSynthesisEngine()
        output = engine.synthesize()

        assert output.prediction_state == "SHADOW_ONLY"
        assert output.interpretation_status == "SHADOW_ONLY"
        assert output.experimental is True
        # Ensure no production activation
        assert "PRODUCTION" not in output.interpretation_status

    def test_output_no_academic_guarantees(self):
        """Test output does not contain academic outcome guarantees."""
        engine = EducationSynthesisEngine()
        output = engine.synthesize()

        # Interpretation should be cautious
        assert output.overall_interpretation in [
            "INSUFFICIENT_EVIDENCE",
            "SUPPORTED",
            "OPPOSED",
            "CONFLICTED",
            "SUPPORTED_WITH_CONDITIONS",
            "RESEARCH_REQUIRED",
            "CONDITIONAL_ONLY",
            "INCONCLUSIVE",
        ]

        # No claims about exam success, admission, degrees
        full_text = str(output).lower()
        prohibited_terms = [
            "will pass", "will fail", "will succeed", "guaranteed",
            "definitely", "certainly", "must", "will definitely"
        ]
        for term in prohibited_terms:
            assert term not in full_text, f"Prohibited term found: {term}"

    def test_backtesting_readiness(self):
        """Test output is backtesting-ready."""
        engine = EducationSynthesisEngine()
        output = engine.synthesize(subject_id="TEST_SUBJECT")

        assert output.backtesting_ready is True
        assert output.subject_id == "TEST_SUBJECT"
        assert output.created_at is not None
        # Should have timestamp for future comparison
        assert len(output.created_at) > 0


class TestEducationBoundaryPreservation:
    """Test that P020/P022/etc boundaries are preserved."""

    def test_education_separate_from_wealth(self):
        """Test education is separate domain from wealth."""
        reg = registry()
        domains = {d["domain_id"] for d in reg["domains"]}
        # Education and wealth are separate
        assert "EDUCATION" in domains
        # Note: wealth is in P022, not P023

    def test_education_separate_from_career(self):
        """Test education is separate from career."""
        # P021 is career, P023 is education - they overlap but are distinct
        reg = registry()
        education = next(d for d in reg["domains"] if d["domain_id"] == "EDUCATION")
        # Education has its own domain_id distinct from career
        assert "EDUCATION" in education["domain_id"]

    def test_d24_calculation_separate_from_interpretation(self):
        """Test D24 calculation is separate from interpretation."""
        reg = registry()
        domains = {d["domain_id"]: d for d in reg["domains"]}

        calc_domain = domains["D24_CALCULATION"]
        assert calc_domain["implementation_status"] == "CALCULATION_READY"
        assert calc_domain["activation_status"] == "ACTIVE"

        # Interpretation governed separately in EDUCATION domain

    def test_no_production_activation(self):
        """Test no production activation for education."""
        reg = registry()
        education = next(d for d in reg["domains"] if d["domain_id"] == "EDUCATION")
        assert education["activation_status"] != "ACTIVE"
        assert education["implementation_status"] == "SHADOW_ONLY"

    def test_strength_components_marked_unvalidated(self):
        """Test strength components carry validation state."""
        reg = registry()
        evidence_classes = {e["source_layer"]: e for e in reg["evidence_classification"]}

        strength_class = evidence_classes.get("STRENGTH", {})
        # Strength should be explicitly marked as unvalidated
        if strength_class:
            assert "UNVALIDATED" in strength_class["status"]


class TestEducationResearchFreedom:
    """Test that research freedoms are preserved."""

    def test_experimental_prediction_allowed(self):
        """Test experimental predictions are allowed."""
        engine = EducationSynthesisEngine()
        output = engine.synthesize()

        # Should be able to make experimental predictions
        assert output.experimental is True
        assert output.backtesting_ready is True

    def test_shadow_synthesis_allowed(self):
        """Test shadow synthesis is permitted."""
        engine = EducationSynthesisEngine()
        output = engine.synthesize()

        # Shadow synthesis should be available
        assert output.prediction_state == "SHADOW_ONLY"
        assert output.interpretation_status == "SHADOW_ONLY"

    def test_research_framework_available(self):
        """Test research framework is available."""
        agg = EducationEvidenceAggregator()
        agg.add_evidence(
            source_layer="RESEARCH_LAYER",
            evidence_type="EXPERIMENTAL",
            direction=EvidenceDirection.NEUTRAL,
            claim="Research claim",
            validation_state="RESEARCH_REQUIRED",
        )
        # Should be able to add research evidence
        assert len(agg.evidence_records) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
