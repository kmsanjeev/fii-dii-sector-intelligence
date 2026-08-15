"""P029 property-domain governance registry."""

PROPERTY_DOMAIN = {
    "domain_id": "PROPERTY",
    "capability_id": "VEDA-CAP-DOMAIN-P029",
    "name": "Property, residence and real-estate synthesis",
    "implementation_status": "IMPLEMENTED_WITH_CONDITIONS",
    "activation_status": "ACTIVE_FOR_GOVERNED_FACTS",
    "knowledge_status": "PARTIAL_RESEARCH_CANDIDATE",
    "required_context": ["D1", "BHAVA", "LORDSHIP", "DASHA", "TRANSIT"],
    "optional_context": ["D4_NOT_VALIDATED", "STRENGTH", "WEALTH_CONTEXT"],
    "blocked_outputs": ["PROPERTY_PRICE", "ROI", "FINANCIAL_ADVICE", "LEGAL_ADVICE", "FATALISTIC_OWNERSHIP"],
}


def registry() -> dict[str, object]:
    return {"domains": [PROPERTY_DOMAIN.copy()], "p022_boundary": "WEALTH_CONTEXT_IS_MODIFIER_ONLY", "p027_owner": True}


__all__ = ["PROPERTY_DOMAIN", "registry"]
