from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "current-state" / "muh-fnd-001"


def test_muhurta_foundation_audit_is_complete_and_scoped():
    required = {
        "00_MASTER_EXECUTION_PROMPT.md",
        "01_EXISTING_STATE_AUDIT.md",
        "02_SOURCE_RESEARCH_METHOD.md",
        "03_PANCHANGA_DEPENDENCY_MATRIX.md",
        "04_MUHURTA_SOURCE_REGISTRY.md",
        "05_EVENT_AND_METHOD_VARIANT_AUDIT.md",
        "06_TIME_LOCATION_SUNRISE_AUDIT.md",
        "07_PERSONAL_BALA_AUDIT.md",
        "08_PRASHNA_BOUNDARY.md",
        "09_READINESS_DECISION.md",
        "10_RUNTIME_AND_RAG_VALIDATION.md",
        "11_LIMITATIONS.md",
        "12_ACCEPTANCE_REGISTER.md",
        "13_FINAL_ACCEPTANCE.md",
    }
    assert required.issubset({p.name for p in AUDIT.iterdir()})

    decision = (AUDIT / "09_READINESS_DECISION.md").read_text(encoding="utf-8")
    prompt = (AUDIT / "00_MASTER_EXECUTION_PROMPT.md").read_text(encoding="utf-8")
    assert "PASS_WITH_CONDITION" in decision
    assert "PARTIAL" in decision
    assert "MISSING_FOUNDATION" in (AUDIT / "08_PRASHNA_BOUNDARY.md").read_text(encoding="utf-8")
    assert "Do not add an electional scorer" in prompt
    assert "Do not create a Panchanga-specific RAG store" in prompt


def test_current_runtime_is_birth_panchanga_only():
    source = (ROOT / "engines" / "ai" / "chatbot" / "tools" / "kundli_calculator.py").read_text(encoding="utf-8")
    assert "def _compute_panchang" in source
    assert "five Panchang limbs at birth" in source
    assert '"tithi"' in source and '"nakshatra"' in source
    assert '"yoga"' in source and '"karana"' in source and '"vara"' in source
    assert "Tarabala" not in source
    assert "Chandrabala" not in source
