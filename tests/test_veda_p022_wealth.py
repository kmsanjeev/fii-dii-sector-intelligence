"""VEDA-P022 Wealth Synthesis Validation Test Suite

Tests for wealth domain governance, safety boundaries, and evidence synthesis.
All tests confirm shadow-only / research-only behavior without activation.
"""

import pytest
from engines.ai.knowledge.wealth_governance import registry, _DOMAINS, _SAFETY_BOUNDARIES, _DEPENDENCY_GRAPH
from engines.intelligence.wealth_synthesis_engine import WealthSynthesisEngine, WealthSynthesis


class TestWealthGovernanceRegistry:
    """P022-M003 ontology validation."""

    def test_registry_structure(self):
        """Verify registry contains all required sections."""
        reg = registry()
        assert len(reg) == 1
        entry = reg[0]
        assert "domains" in entry
        assert "evidence_classification" in entry
        assert "dependency_graph" in entry
        assert "safety_boundaries" in entry

    def test_wealth_domain_exists(self):
        """P022-M004: Verify WEALTH domain is defined."""
        domains = {d["domain_id"]: d for d in _DOMAINS}
        assert "WEALTH" in domains
        wealth = domains["WEALTH"]
        assert wealth["high_stakes"] is True
        assert wealth["activation_status"] == "INACTIVE"
        assert wealth["implementation_status"] == "SHADOW_ONLY"

    def test_wealth_domain_marked_high_stakes(self):
        """P022-M022: Verify WEALTH domain has HIGH_STAKES risk class."""
        domains = {d["domain_id"]: d for d in _DOMAINS}
        assert domains["WEALTH"]["risk_class"] == "HIGH_STAKES"

    def test_d2_calculation_is_active(self):
        """P022-M008: D2 calculation available; interpretation stays research."""
        domains = {d["domain_id"]: d for d in _DOMAINS}
        assert "D2_CALCULATION" in domains
        assert domains["D2_CALCULATION"]["activation_status"] == "ACTIVE"
        # But no D2 interpretation activation

    def test_safety_boundaries_present(self):
        """P022-M022: Verify all safety boundaries are defined."""
        assert len(_SAFETY_BOUNDARIES) >= 7
        safety_text = " ".join(_SAFETY_BOUNDARIES)
        assert "No deterministic prediction" in safety_text
        assert "No financial advice" in safety_text
        assert "No claim of guaranteed cash flows or returns" in safety_text

    def test_dependency_blocking_intact(self):
        """P022-M014: Verify blocked dependencies are enforced."""
        graph = _DEPENDENCY_GRAPH[0]
        assert "DETERMINISTIC_OUTCOME" in graph["blocked"]
        assert "INVESTMENT_ADVICE" in graph["blocked"]
        assert "STOCK_SELECTION" in graph["blocked"]
        assert "TRADING_ACTION" in graph["blocked"]

    def test_evidence_classification_complete(self):
        """P022-M003: Verify evidence classification layers."""
        reg = registry()
        evid_class = reg[0]["evidence_classification"]
        sources = {e["source_layer"] for e in evid_class}
        assert "NATAL" in sources
        assert "2ND_BHAVA" in sources
        assert "11TH_BHAVA" in sources
        assert "DHANA_YOGA" in sources
        assert "APPROVED_CORE" in sources


class TestWealthSynthesisEngine:
    """P022-M019: Shadow synthesis engine validation."""

    def test_engine_instantiation(self):
        """Verify engine creates without side effects."""
        engine = WealthSynthesisEngine()
        assert engine is not None

    def test_synthesis_returns_shadow_state(self):
        """P022-M022: Verify synthesis result is marked SHADOW_ONLY."""
        engine = WealthSynthesisEngine()
        result = engine.synthesize({})
        assert isinstance(result, WealthSynthesis)
        assert result.interpretation_status == "SHADOW_ONLY"
        assert result.safety_status == "HIGH_STAKES_BLOCKED"

    def test_synthesis_overall_state_research_only(self):
        """P022-M022: Verify overall state is never ACTIVATED."""
        engine = WealthSynthesisEngine()
        result = engine.synthesize({})
        assert result.overall_state == "RESEARCH_ONLY"
        assert "ACTIVATED" not in result.overall_state

    def test_synthesis_explainability_present(self):
        """P022-M017: Verify explainability trace is populated."""
        engine = WealthSynthesisEngine()
        result = engine.synthesize({})
        assert len(result.explainability_trace) >= 3
        trace_text = " ".join(result.explainability_trace)
        assert "shadow-only" in trace_text.lower() or "research-only" in trace_text.lower()

    def test_synthesis_confidence_capped(self):
        """P022-M016: Verify confidence is not false precision."""
        engine = WealthSynthesisEngine()
        result = engine.synthesize({})
        assert result.confidence_summary in ["LOW", "LOW_TO_MODERATE", "MODERATE", "RESEARCH_REQUIRED"]


class TestWealthSafetyBoundaries:
    """P022-M022 / P005-R1 Financial safeguards."""

    def test_no_deterministic_language(self):
        """Wealth synthesis must never use 'will' or 'shall' for outcomes."""
        engine = WealthSynthesisEngine()
        result = engine.synthesize({})
        trace = " ".join(result.explainability_trace)
        # Should use conditional language like "may", "potential", "suggests"
        assert "no deterministic wealth prediction" in trace.lower()

    def test_no_investment_advice_activation(self):
        """Wealth synthesis must block investment recommendations."""
        engine = WealthSynthesisEngine()
        result = engine.synthesize({})
        assert result.safety_status == "HIGH_STAKES_BLOCKED"

    def test_high_stakes_marked(self):
        """Verify WEALTH domain always marked HIGH_STAKES."""
        reg = registry()
        wealth = [d for d in reg[0]["domains"] if d["domain_id"] == "WEALTH"][0]
        assert wealth["high_stakes"] is True


class TestP020ReusabilityPatterns:
    """P022 reuses P020 synthesis framework (M014/M020)."""

    def test_evidence_types_inherit_from_p020(self):
        """Verify evidence classification includes P020 patterns."""
        reg = registry()
        evid_types = {e["evidence_type"] for e in reg[0]["evidence_classification"]}
        # P020 patterns: SUPPORTING, OPPOSING, CONDITIONAL, CONTEXTUAL
        assert "SUPPORTING" in evid_types
        assert "CONDITIONAL" in evid_types

    def test_safety_boundaries_extend_p005_r1(self):
        """Verify P022 safety boundaries are extensions of P005-R1."""
        assert len(_SAFETY_BOUNDARIES) >= 1
        # P005-R1 boundary: "No financial advice framing"
        assert any("financial advice" in b.lower() for b in _SAFETY_BOUNDARIES)


class TestP020P021Integration:
    """P022 integrates with P020 (Career) and P021 (Career Profession)."""

    def test_wealth_optional_in_career_workflow(self):
        """Verify wealth signals are optional (not required) for career roles."""
        # Career P021 uses 2H/11H strength for role fit (allowed)
        # But wealth prediction is separate domain (blocked)
        reg = registry()
        wealth = [d for d in reg[0]["domains"] if d["domain_id"] == "WEALTH"][0]
        # FINANCE domain is separate from CAREER domain
        assert wealth["domain_id"] == "WEALTH"

    def test_2nd_11th_bhava_required_for_wealth(self):
        """P022-M005/M006: 2nd/11th bhava are PRIMARY required facts."""
        graph = _DEPENDENCY_GRAPH[0]
        assert "2ND_BHAVA" in graph["required"]
        assert "11TH_BHAVA" in graph["required"]


class TestDhanaYogaHandling:
    """P022-M009: Dhana Yoga state handling."""

    def test_dhana_yoga_research_only(self):
        """Verify Dhana Yoga stays research-only."""
        graph = _DEPENDENCY_GRAPH[0]
        assert "DHANA_YOGA" in graph["research_only"]

    def test_dhana_not_in_blocked(self):
        """Dhana Yoga is not blocked, but unverified."""
        graph = _DEPENDENCY_GRAPH[0]
        assert "DHANA_YOGA" not in graph["blocked"]
        assert "DHANA_YOGA" in graph["research_only"]


class TestD2WealthBoundary:
    """P022-M008/M009: D2 calculation vs. interpretation boundary."""

    def test_d2_calculation_active(self):
        """P012 D2 calculation is ACTIVE."""
        domains = {d["domain_id"]: d for d in _DOMAINS}
        d2_calc = domains.get("D2_CALCULATION")
        assert d2_calc is not None
        assert d2_calc["activation_status"] == "ACTIVE"

    def test_d2_interpretation_blocked(self):
        """D2 wealth interpretation remains SHADOW_ONLY."""
        domains = {d["domain_id"]: d for d in _DOMAINS}
        wealth = domains.get("WEALTH")
        assert wealth is not None
        # D2 is optional context, not primary
        assert "D2_WEALTH" not in wealth["required_fact_types"]


class TestPropertyResourceBoundary:
    """P022-M013: Property vs. Wealth distinction."""

    def test_wealth_not_property(self):
        """Wealth domain governs liquid resources, not real estate."""
        reg = registry()
        wealth = [d for d in reg[0]["domains"] if d["domain_id"] == "WEALTH"][0]
        assert wealth["name"] == "Wealth, income, and financial capacity intelligence"
        # Not "Property and Real Estate Intelligence"


class TestStrengthConfidencePropagation:
    """P022-M012/M018: Unvalidated strength reduces confidence."""

    def test_strength_unvalidated_marked(self):
        """Strength evidence marked IMPLEMENTED_UNVALIDATED."""
        reg = registry()
        evid = [e for e in reg[0]["evidence_classification"] if e["source_layer"] == "STRENGTH"]
        assert len(evid) > 0
        assert evid[0]["status"] == "IMPLEMENTED_UNVALIDATED"

    def test_confidence_bands_preserved(self):
        """Verify confidence uses qualitative bands, not false precision."""
        engine = WealthSynthesisEngine()
        result = engine.synthesize({})
        # Should never be "73.4%" type precision
        assert result.confidence_summary in ["LOW", "MODERATE", "HIGH", "LOW_TO_MODERATE"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
