"""Synthetic-only external-readiness audit for VEDA-EVIDENCE-EXTERNAL-READINESS-001.

This module produces governance evidence and synthetic lifecycle checks only. It
does not contact people, submit applications, collect data, or activate VEDA.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

from scripts.veda_evidence_consent_001 import build as build_consent

PROGRAMME = "VEDA-EVIDENCE-EXTERNAL-READINESS-001"
RETRIEVED = "2026-08-17"

SOURCES = [
    {"id": "IND-DPDP-ACT", "jurisdiction": "INDIA", "source_type": "OFFICIAL_STATUTE", "source": "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Digital+Personal+Data+Protection+Act%2C+2023", "retrieved": RETRIEVED, "requirement": "Digital personal-data processing, rights, duties and commencement must be assessed against the Act and applicable notifications.", "applicability": "LIKELY_IF_REAL_DIGITAL_PERSONAL_DATA", "confidence": "HIGH_FOR_SOURCE_LOW_FOR_PROJECT_APPLICATION", "action": "Counsel to map processing and commencement provisions.", "external_review_required": True},
    {"id": "IND-DPDP-RULES-2025", "jurisdiction": "INDIA", "source_type": "OFFICIAL_RULES", "source": "https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa", "retrieved": RETRIEVED, "requirement": "The notified Rules provide operational detail and a phased enforcement timeline.", "applicability": "LIKELY_IF_REAL_DIGITAL_PERSONAL_DATA", "confidence": "HIGH_FOR_SOURCE_LOW_FOR_PROJECT_APPLICATION", "action": "Counsel to confirm which provisions are in force on activation date.", "external_review_required": True},
    {"id": "ICMR-ETHICS-2017", "jurisdiction": "INDIA", "source_type": "INSTITUTIONAL_ETHICS_GUIDANCE", "source": "https://www.icmr.gov.in/icmrobject/custom_data/pdf/resource-guidelines/ICMR_Ethical_Guidelines_2017.pdf", "retrieved": RETRIEVED, "requirement": "Human-participant biomedical, social and behavioural research for health requires dignity, voluntariness, withdrawal and independent ethics review safeguards.", "applicability": "LEGAL_INTERPRETATION_REQUIRED", "confidence": "HIGH_FOR_SCOPE_AND_PRINCIPLES", "action": "Independent ethics reviewer to classify the protocol and review it before recruitment.", "external_review_required": True},
    {"id": "CERT-IN-70B", "jurisdiction": "INDIA", "source_type": "OFFICIAL_CYBER_DIRECTION", "source": "https://cert-in.org.in/Directions70B.jsp", "retrieved": RETRIEVED, "requirement": "Applicable entities must assess information-security practices, incident response and reporting obligations under the 70B directions.", "applicability": "LEGAL_INTERPRETATION_REQUIRED", "confidence": "HIGH_FOR_SOURCE_LOW_FOR_APPLICABILITY", "action": "Security counsel to determine entity/system applicability and required response windows.", "external_review_required": True},
    {"id": "NIST-PRIVACY-FRAMEWORK", "jurisdiction": "GLOBAL_GUIDANCE", "source_type": "VOLUNTARY_STANDARD", "source": "https://www.nist.gov/document/nist-privacy-frameworkv10pdf", "retrieved": RETRIEVED, "requirement": "Use identify, govern, control, communicate and protect outcomes to manage privacy risk; this is not law or a compliance certification.", "applicability": "TECHNICAL_GUIDANCE", "confidence": "HIGH", "action": "Use as an internal control-organizing framework.", "external_review_required": False},
    {"id": "OWASP-FILE-UPLOAD", "jurisdiction": "GLOBAL_GUIDANCE", "source_type": "SECURITY_GUIDANCE", "source": "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html", "retrieved": RETRIEVED, "requirement": "Authenticated and authorized uploads, allowlists, type/signature checks, size limits, isolated storage and scanning are recommended.", "applicability": "TECHNICAL_GUIDANCE", "confidence": "HIGH", "action": "Implement and test before any document upload is enabled.", "external_review_required": False},
    {"id": "ADB-RESEARCH", "jurisdiction": "PROVIDER_TERMS", "source_type": "OFFICIAL_PROVIDER_PAGE", "source": "https://www.astro.com/adb-search/adb-search/", "retrieved": RETRIEVED, "requirement": "Guest users cannot submit queries; full research access requires subscription or special permission as a qualified researcher.", "applicability": "DIRECT_IF_ACCESS_REQUESTED", "confidence": "HIGH", "action": "Founder/provider human action; prepare but do not send permission request.", "external_review_required": True},
    {"id": "ADB-DATA-SUBMISSION", "jurisdiction": "PROVIDER_TERMS", "source_type": "OFFICIAL_PROVIDER_PAGE", "source": "https://www.astro.com/astro-databank/Main_Page?lang=e", "retrieved": RETRIEVED, "requirement": "The provider identifies a route for qualified-source data/correction submissions and requests relevant documents; use and redistribution terms require separate review.", "applicability": "DIRECT_IF_SUBMISSION_REQUESTED", "confidence": "HIGH_FOR_ROUTE_LOW_FOR_RESEARCH_LICENSE", "action": "Founder/provider to confirm research-access, lineage and redistribution terms.", "external_review_required": True},
]

LIFECYCLE = [
    ("REGISTRATION", "contact/identity metadata", "identity vault", "encrypted", "research admin", "registration audit", "provisional", "no production endpoint"),
    ("CONSENT", "versioned scopes and evidence", "consent store", "encrypted", "participant/research reviewer", "consent version event", "review-defined", "withdrawal creates immutable audit event"),
    ("IDENTITY", "minimum contact linkage", "separate identity vault", "encrypted and access-separated", "identity steward only", "vault access audit", "minimum necessary", "delete or sever linkage on withdrawal"),
    ("BIRTH DOCUMENT", "original evidence or verification metadata", "isolated document store or no-retention path", "encrypted, malware-scanned", "evidence adjudicator", "document access audit", "external review required", "prefer fingerprint plus verification metadata"),
    ("VERIFICATION", "tier, precision, conflict and source hash", "research store", "encrypted", "evidence adjudicator", "adjudication event", "study-defined", "no source document in export"),
    ("RESEARCH RECORD", "pseudonymous chart-independent evidence record", "research store", "encrypted", "approved reviewers", "record change audit", "study-defined", "identity key absent"),
    ("EVENT FOLLOW-UP", "consented event category, date precision and provenance", "research store", "encrypted", "participant/reviewer", "follow-up audit", "study-defined", "optional scopes enforced"),
    ("STUDY SNAPSHOT", "frozen hashes and eligibility", "snapshot registry", "integrity-protected", "research admin", "snapshot lock", "study-defined", "no edits after lock"),
    ("ANALYSIS EXPORT", "deidentified aggregate or pseudonymous restricted extract", "export boundary", "encrypted and logged", "authorized analyst", "export audit", "external review required", "scope and reidentification review"),
    ("RETENTION", "metadata and permitted study artifacts", "respective controlled store", "encrypted", "research admin", "retention event", "provisional", "counsel must finalize periods"),
    ("WITHDRAWAL/DELETION/ANONYMIZATION", "status, deletion/tombstone proof", "vault/research/snapshot systems", "encrypted", "research admin", "withdrawal audit", "provisional", "backups and lawful retention require review"),
]

THREATS = [
    ("participant enumeration", "HIGH", "MEDIUM", "no endpoint; synthetic-only", "activation design absent", "deny-by-default identifiers and rate limits", True),
    ("identity/research relinking", "HIGH", "MEDIUM", "logical separation design", "identity vault not deployed", "separate principal, key and audit boundary", True),
    ("birth-document leakage", "HIGH", "MEDIUM", "no real documents; metadata-only recommendation", "upload controls not deployed", "isolated encrypted store, allowlist, signature validation, AV/CDR", True),
    ("IDOR/authorization bypass", "HIGH", "MEDIUM", "no endpoint", "authorization not implemented", "object-level authorization tests and least privilege", True),
    ("export leakage/reidentification", "HIGH", "MEDIUM", "synthetic deidentified export", "real-world risk assessment absent", "minimum fields, k-anonymity/reidentification review, export approval", True),
    ("audit-log leakage", "MEDIUM", "MEDIUM", "audit design only", "log schema/deletion policy absent", "redact identifiers and restrict log access", True),
    ("secret leakage", "HIGH", "LOW", "no new secrets", "secret-management deployment not reviewed", "managed secret store and scanning", True),
    ("backup exposure", "HIGH", "MEDIUM", "no production backup", "backup control not implemented", "encrypted backups, access review, deletion/tombstone procedure", True),
    ("admin compromise/insider access", "HIGH", "MEDIUM", "role list documented", "MFA/PAM not verified", "strong auth, dual control, access review", True),
    ("malicious upload/metadata", "HIGH", "MEDIUM", "no upload endpoint", "scanner and sandbox absent", "OWASP allowlist/signature/size/sandbox controls", True),
    ("consent tampering", "HIGH", "LOW", "versioned consent design", "append-only persistence not deployed", "signed/versioned events and independent audit", True),
    ("prospective-ledger tampering", "HIGH", "LOW", "ledger documented only", "no immutable store", "lock hash, method version, timestamp and outcome separation", True),
    ("deletion failure", "HIGH", "MEDIUM", "synthetic withdrawal design", "real stores/backups absent", "deletion verification and backup tombstones", True),
    ("cross-environment leakage", "HIGH", "MEDIUM", "production collection absent", "environment isolation not verified", "separate accounts, datasets, credentials and CI checks", True),
]

GATES = {
    "TECHNICAL": "PASS_WITH_CONDITION",
    "PRIVACY": "EXTERNAL_REVIEW_REQUIRED",
    "SECURITY": "EXTERNAL_REVIEW_REQUIRED",
    "LEGAL": "EXTERNAL_REVIEW_REQUIRED",
    "ETHICS": "EXTERNAL_REVIEW_REQUIRED",
    "CONSENT": "PASS_WITH_CONDITION",
    "RETENTION": "EXTERNAL_REVIEW_REQUIRED",
    "WITHDRAWAL": "PASS_WITH_CONDITION",
    "INCIDENT_RESPONSE": "PASS_WITH_CONDITION",
    "DOCUMENT_VERIFICATION": "PASS_WITH_CONDITION",
    "RECRUITMENT_PROTOCOL": "PASS_WITH_CONDITION",
}


def synthetic_withdrawal_test() -> dict[str, Any]:
    result = deepcopy(build_consent())
    participant = result["participants"][0]
    before = participant["consent"]["scopes"][:]
    participant["consent"]["scopes"].remove("AGGREGATED_PUBLICATION") if "AGGREGATED_PUBLICATION" in participant["consent"]["scopes"] else None
    participant["status"] = "WITHDRAWAL_REQUESTED"
    participant["followup"]["state"] = "STOPPED"
    participant["status"] = "WITHDRAWN"
    participant["identity_vault_ref"] = None
    return {"synthetic": True, "before_scopes": before, "after_scopes": participant["consent"]["scopes"], "status": participant["status"], "future_contact": "STOPPED", "identity_linkage": "SEVERED", "backup": "TOMBSTONE_REQUIRED", "audit_event": "WITHDRAWAL_SYNTHETIC_TEST", "passed": participant["status"] == "WITHDRAWN" and participant["followup"]["state"] == "STOPPED"}


def build() -> dict[str, Any]:
    consent = build_consent()
    return {
        "programme": PROGRAMME,
        "status": "PASS_WITH_CONDITION",
        "retrieved": RETRIEVED,
        "source_registry": SOURCES,
        "lifecycle": LIFECYCLE,
        "threats": THREATS,
        "gates": GATES,
        "identity_vault_decision": "RECRUITMENT_BLOCKED_UNTIL_SEPARATE_VAULT_OR_MINIMUM_RETENTION_ARCHITECTURE_IS_REVIEWED",
        "document_retention_decision": "PREFER_VERIFICATION_METADATA_PLUS_CRYPTOGRAPHIC_FINGERPRINT; RETAIN_ORIGINAL_ONLY_IF_COUNSEL_AND_SECURITY_APPROVE",
        "india_state": "INDIA_EXTERNAL_REVIEW_READY_FOR_COUNSEL",
        "legal_state": "LEGAL_REVIEW_REQUIRED",
        "ethics_state": "ETHICS_REVIEW_REQUIRED_NOT_APPROVED",
        "security_state": "EXTERNAL_SECURITY_REVIEW_REQUIRED",
        "recruitment_state": "NOT_READY_EXTERNAL_REVIEW_REQUIRED",
        "synthetic_withdrawal_test": synthetic_withdrawal_test(),
        "locks": {"astrology": False, "feature_scoring": False, "predictions": False, "ml": False, "production": False, "rag": False, "approved_core": False, "external_submission": False, "real_pii": False},
        "parent_manifest": consent["snapshot"],
        "provider_calls_added": 0,
        "source_date": date.today().isoformat(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(), indent=2, sort_keys=True))
