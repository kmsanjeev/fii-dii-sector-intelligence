"""Deterministic, non-acquisition audit for VEDA-EVIDENCE-INDIA-ACCESS-RX-001.

This module records source verification and prepares human action packs.  It
does not contact providers, scrape repositories, download records, submit RTI,
recruit subjects, run astrology, score features, train ML, or change PRED-M4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "current-state" / "evidence-india-access-rx-001"
ACTIVITY = "VEDA-EVIDENCE-INDIA-ACCESS-RX-001"
RUN_DATE = "2026-08-19"
STARTING_COMMIT = "c3498340865e2d2b067640c74e96b4c217004726"


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def source_registry() -> list[dict[str, Any]]:
    return [
        {"id": "BVB-ASTROLOGY", "authority": "OFFICIAL_INSTITUTION", "url": "https://www.bvbdelhi.org/astrology/", "finding": "K.N. Rao Institute exists within Bharatiya Vidya Bhavan Delhi; courses, research classes and contact route are documented.", "status": "VERIFIED"},
        {"id": "BVB-INSTITUTE", "authority": "OFFICIAL_INSTITUTION", "url": "https://www.bvbdelhi.org/aaa/", "finding": "The institute describes K.N. Rao courses, research selection and Journal of Astrology publications.", "status": "VERIFIED"},
        {"id": "JOURNAL-KN-RAO", "authority": "OFFICIAL_PUBLICATION", "url": "https://www.journalofastrology.com/page.php?lang=lt&page=KNRAO", "finding": "The page reports that K.N. Rao has more than 50,000 horoscopes with ten important events noted; it is not a documentary inventory.", "status": "CLAIM_SUPPORTED_NOT_INVENTORY"},
        {"id": "ICAS-FAQ", "authority": "OFFICIAL_INSTITUTION", "url": "https://www.icasindia.org/ICAS/FAQ.html", "finding": "ICAS describes its establishment, study, research, practice, courses and membership; no central birth-data repository is established.", "status": "VERIFIED_SCOPE_ONLY"},
        {"id": "ICAS-CONTACT", "authority": "OFFICIAL_INSTITUTION", "url": "https://www.icasindia.org/ICAS/Contacts.html", "finding": "Public contact route, secretary/registrar and chapter structure are documented.", "status": "VERIFIED"},
        {"id": "SHODHGANGA", "authority": "OFFICIAL_REPOSITORY", "url": "https://betasg.inflibnet.ac.in/home", "finding": "INFLIBNET describes Shodhganga as an open-access thesis repository; item-level licensing and methodology must be checked.", "status": "VERIFIED_DISCOVERY_ONLY"},
        {"id": "SHODHGANGA-BROCHURE", "authority": "OFFICIAL_REPOSITORY_DOCUMENT", "url": "https://inflibnet.ac.in/downloads/brochure/shodhganga.pdf", "finding": "Repository brochure describes thesis discovery and CC BY-NC-SA licensing; current home page displays CC BY-NC, so item-level licence verification is required.", "status": "LICENSE_VARIANCE_RECORDED"},
        {"id": "DELHI-CRS", "authority": "OFFICIAL_GOVERNMENT", "url": "https://des.delhi.gov.in/des/registration-births-and-deaths-0", "finding": "Delhi Chief Registrar page links current Birth Reporting Form No. 1 and publishes a metadata contact route.", "status": "VERIFIED"},
        {"id": "DELHI-FORM-1", "authority": "OFFICIAL_FORM", "url": "https://des.delhi.gov.in/sites/default/files/DES/generic_multiple_files/birth_reporting_form_no._1.pdf", "finding": "Current linked one-page form is a scan; the official 2024 instructions enumerate date/place and other reporting fields but do not establish a standard TOB field.", "status": "CRS_TOB_NOT_ESTABLISHED_FROM_FORM"},
        {"id": "RBD-ACT", "authority": "OFFICIAL_STATUTE", "url": "https://www.indiacode.nic.in/handle/123456789/1682?view_type=browse", "finding": "Registration statute governs registration and national registration administration; it does not by itself create a bulk research disclosure entitlement.", "status": "VERIFIED_GOVERNANCE"},
        {"id": "RTI-ACT", "authority": "OFFICIAL_STATUTE", "url": "https://www.indiacode.nic.in/handle/123456789/17520", "finding": "The RTI Act provides a regime for information under public-authority control; this audit prepares metadata-only questions and does not submit a request for personal records.", "status": "VERIFIED_METADATA_SCOPE"},
        {"id": "DELHI-RULES-2024", "authority": "OFFICIAL_STATE_RULES", "url": "https://des.delhi.gov.in/sites/default/files/DES/generic_multiple_files/gazette_notification_amendment_rules_2024.pdf", "finding": "Delhi 2024 rules and Form 1 instructions were used for the bounded form audit; they do not establish a standard TOB field in the current form evidence reviewed.", "status": "VERIFIED_BOUNDED_SCOPE"},
        {"id": "DPDP-ACT", "authority": "OFFICIAL_STATUTE", "url": "https://www.indiacode.nic.in/handle/123456789/22037", "finding": "Research, archiving and statistical processing conditions are distinct from a right to receive personal data.", "status": "VERIFIED_NUANCED"},
        {"id": "DPDP-RULES", "authority": "OFFICIAL_RULES", "url": "https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa", "finding": "Notified DPDP Rules 2025 are a current implementation source; activation and application require legal review at execution time.", "status": "VERIFIED_REVIEW_REQUIRED"},
        {"id": "ICMR-ETHICS", "authority": "OFFICIAL_GUIDANCE", "url": "https://www.icmr.gov.in/guidelines", "finding": "ICMR publishes National Ethical Guidelines and current ethics-review guidance relevant to a hospital research route.", "status": "VERIFIED_DESIGN_ONLY"},
        {"id": "SAPTARISHIS-OFFICIAL", "authority": "PRACTITIONER_PROVIDER", "url": "https://saptarishisastrology.com/", "finding": "Official site invites data submission/research contact, but size, Indian representation, upstream provenance, rights, consent and rectification policy are not established.", "status": "PROVENANCE_RIGHTS_CONSENT_NOT_VERIFIED"},
        {"id": "SAPTARISHIS-SOURCE-WARNING", "authority": "PRACTITIONER_PUBLICATION", "url": "https://saptarishisastrology.com/gouri-jatakam-part-5-by-d-m-sudhindra-kumar-india/", "finding": "An official article says data came from various websites and may not be precise; this is a provenance warning, not an empirical source qualification.", "status": "DOWNGRADED_VARIANT_DISCOVERY"},
    ]


def acceptance_register() -> list[dict[str, str]]:
    rows = [
        ("AC01", "Starting commit and repository boundary verified", "PASS"),
        ("AC02", "Gemini report treated as discovery input only", "PASS"),
        ("AC03", "Primary Indian sources prioritized and registered", "PASS"),
        ("AC04", "BVB institution and research programme verified", "PASS"),
        ("AC05", "50,000+ and 150,000 claims separated", "PASS"),
        ("AC06", "BVB provenance/access/rectification gaps retained", "PASS_WITH_CONDITION"),
        ("AC07", "BVB pack prepared and unsent", "PASS"),
        ("AC08", "ICAS dataset not assumed", "PASS"),
        ("AC09", "ICAS pack prepared and unsent", "PASS"),
        ("AC10", "Saptarishis provenance, rights and consent unverified", "PASS_WITH_CONDITION"),
        ("AC11", "Shodhganga repository/licence variance recorded", "PASS_WITH_CONDITION"),
        ("AC12", "Shodhganga controls not automatically eligible", "PASS"),
        ("AC13", "Delhi Form No. 1 audited without state-wide extrapolation", "PASS_WITH_CONDITION"),
        ("AC14", "CRS TOB storage/certificate/access left unverified", "PASS_WITH_CONDITION"),
        ("AC15", "RTI metadata-only draft prepared and unsent", "PASS"),
        ("AC16", "DPDP research condition separated from disclosure entitlement", "PASS"),
        ("AC17", "ICMR hospital research route and ethics gate documented", "PASS_WITH_CONDITION"),
        ("AC18", "Hospital minimum schema and provider identity custody prepared", "PASS"),
        ("AC19", "Rectified TOB excluded from confirmatory evidence", "PASS"),
        ("AC20", "Outcome-independent selection and no acquisition preserved", "PASS"),
        ("AC21", "Parallel Müller/ADB/POSEND/Ashtakavarga states preserved", "PASS"),
        ("AC22", "No astrology, feature scoring, ML or prediction activation", "PASS"),
        ("AC23", "No provider calls, scraping, OCR harvesting or external emails", "PASS"),
        ("AC24", "No RAG subject-level data or Approved Core change", "PASS"),
        ("AC25", "Route ranking and next human action recorded", "PASS_WITH_CONDITION"),
        ("AC26", "Deterministic two-run artifact hash stable", "PASS"),
        ("AC27", "Focused and parent governance tests pass", "PASS"),
        ("AC28", "git diff --check passes", "PASS"),
        ("AC29", "Selective staging only", "PASS"),
        ("AC30", "Human institutional/legal/ethics gate remains before contact/data", "PASS_WITH_CONDITION"),
    ]
    return [{"id": item[0], "criterion": item[1], "status": item[2]} for item in rows]


def build() -> dict[str, Any]:
    return {
        "activity": ACTIVITY,
        "retrieved": RUN_DATE,
        "starting_commit": STARTING_COMMIT,
        "execution_boundary": {"provider_calls": 0, "personal_data_acquired": False, "external_requests_sent": False, "scraping": False, "bulk_ocr": False, "astrology": False, "feature_scoring": False, "ml": "LOCKED", "pred_m4": "INSUFFICIENT_SAMPLE"},
        "gemini_claim_audit": [
            {"claim": "BVB/K.N. Rao has 50,000+ horoscopes", "classification": "RESEARCH_CANDIDATE_TO_PRIMARY_SOURCE_SUPPORTED", "result": "SUPPORTED_AS_REPORTED_COLLECTION_CLAIM; NOT A DOCUMENTARY INVENTORY"},
            {"claim": "BVB/K.N. Rao has 150,000 horoscopes", "classification": "NOT_VERIFIED", "result": "NO AUTHORITATIVE SOURCE LOCATED"},
            {"claim": "ICAS provides a centralized Indian birth dataset", "classification": "NOT_VERIFIED", "result": "ICAS ORGANIZATION AND RESEARCH ACTIVITY VERIFIED; CENTRAL DATASET NOT VERIFIED"},
            {"claim": "Indian commercial databases provide documentary TOB at scale", "classification": "NOT_VERIFIED", "result": "SIZE, UPSTREAM PROVENANCE, RIGHTS, CONSENT AND RECTIFICATION POLICY UNVERIFIED"},
            {"claim": "Delhi civil records routinely provide usable TOB", "classification": "NOT_ESTABLISHED", "result": "CURRENT STANDARD FORM DOES NOT ESTABLISH A TOB FIELD; NO STATEWIDE EXTRAPOLATION"},
        ],
        "source_registry": source_registry(),
        "bvb": {"institution_verified": True, "research_programme": "VERIFIED", "collection_50k_plus": "PRIMARY_SOURCE_SUPPORTED_AS_SELF-REPORTED_COLLECTION CLAIM", "collection_150k": "NOT_VERIFIED", "provenance_metadata": "NOT_DOCUMENTED_PUBLICLY; AGGREGATE ENQUIRY REQUIRED", "digital_access": "NOT_VERIFIED", "rectified_time_handling": "NOT_VERIFIED", "research_collaboration": "CANDIDATE_ROUTE; HUMAN ENQUIRY REQUIRED", "contact": {"email": "info@bvbdelhi.org", "phone": "+91 011 2338 9942", "address": "Kasturba Gandhi Marg, New Delhi"}, "decision": "BVB_RESEARCH_COLLABORATION_CANDIDATE_AGGREGATE_INVENTORY_REQUIRED"},
        "icas": {"institution_verified": True, "research_activity": "VERIFIED", "central_dataset_verified": False, "classification": ["RESEARCH_PARTNER_CANDIDATE", "SOURCE_DISCOVERY_PARTNER", "NO_DATA_ROUTE"], "public_dataset": "NOT_VERIFIED", "contact": {"email": "info@icasindia.org", "route": "Official contacts page; secretary/registrar/chapter structure"}, "decision": "ICAS_RESEARCH_PARTNER_CANDIDATE_NO_DATASET_ASSUMED"},
        "shodhganga": {"repository_verified": True, "access": "OPEN_ACCESS_DISCOVERY_REPOSITORY", "licence": "CURRENT HOME PAGE CC BY-NC; BROCHURE CC BY-NC-SA; VERIFY ITEM LICENCE", "relevant_theses": "BOUNDED METADATA DISCOVERY ONLY; NO SUBJECT EXTRACTION", "potential_source_leads": "RESEARCHER/THESIS/INSTITUTION METADATA LEADS MAY BE REGISTERED", "general_population_cohorts": "UNKNOWN_UNLESS_METHODOLOGY_PROVES_PRE_EXISTING_BASELINE", "controls_automatically_eligible": "NO", "best_use": "SOURCE-METHODOLOGY AND ORIGINAL-DATA-PROVENANCE DISCOVERY"},
        "crs": {"jurisdiction": "DELHI_BOUNDED_PILOT", "standard_form": "FORM_NO_1_CURRENT_LINKED_SCAN", "tob_in_standard_birth_form": "CRS_TOB_NOT_ESTABLISHED_FROM_FORM", "tob_storage": "NOT_VERIFIED", "tob_on_certificate": "NOT_VERIFIED", "historical_records": "NOT_VERIFIED", "research_access": "NOT_VERIFIED", "bulk_access": "NOT_VERIFIED", "bulk_pii_request": False, "metadata_enquiry": "PREPARED_NOT_SUBMITTED", "decision": "CRS_METADATA_ONLY_ROUTE; NO_EMPIRICAL_FRAME_ASSUMED"},
        "rti": {"status": "PREPARED_NOT_SUBMITTED", "scope": ["TOB storage/schema", "years covered", "retention", "digitisation", "research-access mechanism", "anonymised-data availability", "competent authority", "applicable rules", "aggregate counts"], "excludes": ["names", "DOB", "TOB", "POB", "individual records", "bulk PII"]},
        "dpdp_rbd_rti": {"research_processing": "CONDITIONAL_LEGAL_GOVERNANCE QUESTION", "disclosure_entitlement": "NOT_CREATED_BY_RESEARCH_CONDITION", "rbd": "REGISTRATION_ADMINISTRATION_AND_CERTIFICATION_FRAMEWORK", "rti": "METADATA_ONLY_DRAFT; NO_SUBMISSION", "legal_review": "REQUIRED_BEFORE_ANY_REAL-DATA ROUTE"},
        "hospital": {"documentary_tob_potential": "HIGHER_THAN_PUBLIC_DISCOVERY_IF_INSTITUTIONAL_RECORDS_AND_ETHICS_APPROVE", "ethics_required": True, "data_sharing_required": True, "pseudonymized_architecture": "PROVIDER-HELD IDENTITY KEY; VEDA RECEIVES MINIMUM PSEUDONYMOUS FIELDS", "longitudinal_linkage": "CONSENTED_PROSPECTIVE_OR_TRUSTED-THIRD-PARTY LINKAGE ONLY; NO PUBLIC DEANONYMIZATION", "pilot_design": "DESIGN ONLY; 500-1000 HISTORICAL/PROSPECTIVE RECORDS ONLY IF APPROVED; NO OUTCOME LOOKUP AT ACQUISITION", "decision": "PRIMARY_PROMISING_ROUTE_BUT_INSTITUTIONAL_ETHICS_AND_ACCESS_GATE_REQUIRED"},
        "provenance_contract": [
            {"class": "INDIA_HOSPITAL_DOCUMENT", "veda_tier": "TIER_A_DOCUMENTARY", "confirmatory": True},
            {"class": "INDIA_CIVIL_DOCUMENT", "veda_tier": "TIER_A_DOCUMENTARY", "confirmatory": True},
            {"class": "INDIA_INSTITUTION_DOCUMENTARY", "veda_tier": "TIER_B_INSTITUTIONAL", "confirmatory": "CONDITIONAL_SOURCE_REVIEW"},
            {"class": "INDIA_FAMILY_REPORTED", "veda_tier": "TIER_C_REPORTED", "confirmatory": False},
            {"class": "INDIA_BIOGRAPHICAL", "veda_tier": "TIER_C_REPORTED", "confirmatory": False},
            {"class": "INDIA_RECTIFIED", "veda_tier": "RESEARCH_ONLY", "confirmatory": False, "risk": "OUTCOME_LEAKAGE_RISK_IF_RECTIFIED_FROM_STUDIED_EVENTS"},
            {"class": "INDIA_APPROXIMATE", "veda_tier": "RESEARCH_ONLY", "confirmatory": False},
            {"class": "INDIA_UNKNOWN", "veda_tier": "UNQUALIFIED", "confirmatory": False},
        ],
        "route_ranking": [
            {"rank": 1, "route": "Hospital/medical-college research partnership", "status": "PROMISING_DESIGN_ONLY", "reason": "Potential original documentary TOB, outcome-independent cohort design, provider-held identity custody and longitudinal consent architecture."},
            {"rank": 2, "route": "BVB / K.N. Rao Institute", "status": "COLLABORATION_CANDIDATE", "reason": "Institution and research programme verified; reported 50,000+ collection; provenance/access metadata and rights require aggregate enquiry."},
            {"rank": 3, "route": "ICAS", "status": "PARTNER/DISCOVERY CANDIDATE", "reason": "Research organization and contact verified; no centralized dataset verified."},
            {"rank": 4, "route": "Delhi CRS metadata route", "status": "METADATA_ONLY", "reason": "Government route can clarify schema/retention/access but current Form 1 does not establish TOB."},
            {"rank": 5, "route": "Shodhganga and Saptarishis", "status": "DISCOVERY_ONLY / UNVERIFIED", "reason": "Useful for source leads or method discovery; no automatic empirical eligibility and no ingestion."},
        ],
        "parallel_lanes": {"muller": "MULLER_MANUAL_VERIFICATION_REQUIRED_FOR_SCALE", "position_end": "WAIT_EXTERNAL_ACCESS", "adb": "PREPARED / UNSENT", "ashtakavarga": "ASHTAKAVARGA_REMEDIATION_SPEC_READY", "next_calculation": "VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001"},
        "governance": {"prediction": "UNCHANGED", "pred_m4": "INSUFFICIENT_SAMPLE", "ml": "LOCKED", "rag_subject_level_data": False, "personal_data_acquired": False, "external_requests_sent": False, "approved_core_change": False},
        "next": {"evidence_id": "VEDA-EVIDENCE-INDIA-COLLABORATION-R1", "objective": "Human review of unsent BVB/ICAS/hospital/Delhi metadata packs and selection of one lawful route; no authorization implied.", "human_action_required": "Founder/institutional/legal/ethics review before any real contact or data route.", "calculation_id": "VEDA-CALC-ASHTAKAVARGA-REMEDIATION-001", "calculation_started": False},
        "artifact_policy": {"raw_personal_data": "NONE", "thesis_downloads": "NONE", "provider_calls": 0, "deterministic": True},
        "acceptance": acceptance_register(),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_md(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")


def render(data: dict[str, Any], output: Path = OUT) -> str:
    output.mkdir(parents=True, exist_ok=True)
    _write_md(output / "00_BASELINE.md", ACTIVITY, f"""- Retrieved: {RUN_DATE}\n- Starting commit: `{STARTING_COMMIT}`\n- Gemini India report: discovery input only; every substantive claim was independently classified.\n- Scope: access/source governance and unsent packs only.\n- No personal data, scraping, OCR harvesting, provider calls, RTI submission, recruitment, astrology, scoring, ML, PRED-M4 or production changes.\n- Parent state preserved: Müller manual verification required; POSITION_END waits external access; ADB prepared/unsent; Ashtakavarga remediation spec ready.""")
    _write_json(output / "01_GEMINI_CLAIM_AUDIT.json", {"activity": ACTIVITY, "claims": data["gemini_claim_audit"]})
    _write_json(output / "02_INDIA_SOURCE_MATRIX.json", {"activity": ACTIVITY, "sources": data["source_registry"]})
    _write_md(output / "03_BVB_ACCESS_ASSESSMENT.md", "BVB / K.N. Rao access assessment", """Institution existence, research classes and official contact routes are verified from Bharatiya Vidya Bhavan material. The Journal of Astrology page supports a reported collection of more than 50,000 horoscopes with ten important events noted; this is a self-reported collection claim, not a documentary inventory. No authoritative 150,000 figure, digital export policy, provenance schema, rectification policy or private-access entitlement was verified. Decision: prepare an aggregate inventory enquiry only.""")
    _write_md(output / "04_BVB_CONTACT_PACK.md", "BVB / K.N. Rao unsent contact pack", """**Status: PREPARED / UNSENT.**\n\nTo: Bharatiya Vidya Bhavan / K.N. Rao Institute (use official published route only)\n\nSubject: Aggregate birth-time provenance inventory enquiry for independent VEDA research\n\nI am an independent researcher working on VEDA, a calculation/evidence-governance project. I am not claiming university, medical, statistical, publication or ethics approval affiliation. Before requesting any records, I would like to ask whether the Institute can share an aggregate inventory of its collection, separated where possible into documentary/hospital, civil-registry, family-reported, biographical, rectified, approximate and unknown time classes; whether an outcome-independent subset exists; whether any de-identified research collaboration route is available; and what governance, licence, privacy and provenance conditions apply. No individual records are requested at this stage.\n\n**Pilot concept:** small, feature-blind, outcome-independent, documentary-provenance review only after institutional approval; rectified times excluded from confirmatory analysis; no AI training; minimum fields only; no redistribution.\n\nQuestions: digital availability, source metadata, time precision, rectification disclosure, rights, consent, retention, permitted outputs, review process and responsible contact. Do not send automatically.""")
    _write_md(output / "05_ICAS_ACCESS_ASSESSMENT.md", "ICAS access assessment", """ICAS existence, chapter/membership structure, research objectives and public contact route are verified. A centralized birth-data dataset is not verified and must not be assumed. Classification: research-partner candidate, source-discovery partner, and possible no-data route. Any enquiry must ask only whether an approved aggregate or de-identified research route exists.""")
    _write_md(output / "06_ICAS_CONTACT_PACK.md", "ICAS unsent contact pack", """**Status: PREPARED / UNSENT.**\n\nTo: Indian Council of Astrological Sciences, using the official contact route.\n\nI am an independent researcher working on VEDA. I seek information about whether ICAS has any documented, lawfully shareable, outcome-independent birth-data research resource or can identify a research-methodology partner. I am not requesting names or individual DOB/TOB/POB. Please advise whether any aggregate inventory, institutional documentary source, de-identified pilot, governance review or source-discovery collaboration exists, and the applicable privacy/licensing requirements. No affiliation or ethics approval is claimed. Do not send automatically.""")
    _write_json(output / "07_SHODHGANGA_DISCOVERY_REGISTER.json", {"activity": ACTIVITY, "repository": data["shodhganga"], "leads": [], "control_policy": {"outcome_selected_cases": "INELIGIBLE", "matched_controls": "REVIEW_REQUIRED", "convenience_controls": "INELIGIBLE", "general_population_controls": "POTENTIALLY_ELIGIBLE_AFTER_METHOD_VALIDATION", "pre_existing_baseline_cohort": "POTENTIALLY_ELIGIBLE_AFTER_METHOD_VALIDATION", "unknown": "INELIGIBLE_PENDING PROVENANCE"}, "subject_extraction": False})
    _write_md(output / "08_CRS_TOB_AUDIT.md", "Delhi CRS / Form No. 1 audit", """The Delhi Chief Registrar page publishes the current Form No. 1 link and metadata contact. The linked one-page PDF is a scan; the official 2024 instructions identify date, place, residence, education and occupation fields, but do not establish a standard time-of-birth field. Therefore the bounded result is **CRS_TOB_NOT_ESTABLISHED_FROM_FORM**. This does not establish whether TOB is stored in hospital/registrar systems, appears on certificates, exists historically, or is accessible for research. Those are separate metadata questions. No state-wide inference is made.""")
    _write_md(output / "09_RTI_METADATA_REQUEST.md", "Delhi CRS metadata-only RTI draft", """**PREPARED / NOT SUBMITTED.**\n\nRequest only aggregate or metadata information: whether TOB is stored; data dictionary/schema; years covered; retention; digitisation; research-access mechanism; anonymised-data availability; competent authority; applicable rules; and aggregate record counts.\n\nExplicit exclusions: no names, individual DOB, TOB, POB, certificates, identifiers, contact details, or bulk personal data. The draft must receive legal/privacy review before any submission.""")
    _write_md(output / "10_DPDP_RBD_RTI_GOVERNANCE.md", "DPDP / RBD / RTI governance", """The DPDP research/archiving/statistical conditions are not treated as a disclosure entitlement. The Registration of Births and Deaths framework governs registration and certification; it does not by itself authorize bulk release. RTI is limited here to metadata. Any real-data route requires current legal review, purpose limitation, minimisation, identity custody, security, retention and approved access conditions. No categorical claim that data is automatically illegal or automatically releasable is made.""")
    _write_md(output / "11_HOSPITAL_RESEARCH_ROUTE.md", "Hospital / medical-college research route", """This is the primary promising route, but design-only. A formal institutional partnership could provide original documentary TOB with an outcome-independent cohort, provider-held identity key, minimum pseudonymous fields, no clinical extras, ethics review, data-sharing agreement, security and publication controls. A 500-1,000 record historical/prospective pilot is only a bounded design option if the institution and ethics process approve it; no acquisition or outcome lookup is authorized. Longitudinal linkage must be consented prospective follow-up or trusted-third-party linkage, never public deanonymization.""")
    _write_json(output / "12_HOSPITAL_DATA_MODEL.json", {"activity": ACTIVITY, "fields": ["SUBJECT_ID", "DATE_OF_BIRTH", "TIME_OF_BIRTH", "TIME_PRECISION", "PLACE_OF_BIRTH", "HOSPITAL_INSTITUTION", "SOURCE_TYPE", "SOURCE_DATE", "DOCUMENTARY_STATUS", "RECTIFIED", "APPROXIMATE", "CONSENT_GOVERNANCE_STATE", "IDENTITY_HELD_BY_PROVIDER"], "constraints": {"rectified": "EXPECTED_NO", "identity_custody": "PROVIDER_ONLY", "clinical_fields": "EXCLUDED", "real_subjects": False, "outcome_lookup_at_acquisition": False}})
    _write_md(output / "13_HOSPITAL_CONTACT_PACK.md", "Generic hospital research contact pack", """**Status: PREPARED / UNSENT.**\n\nTo: Research office / Institutional Ethics Committee of a prospective medical college or hospital, after identifying a real institution.\n\nI am an independent researcher working on VEDA and seek an initial discussion about whether a lawful, ethics-reviewed, outcome-independent birth-data methodology study is feasible. The proposed minimum dataset is DOB, TOB, time precision, POB/institution, documentary status and provider-held pseudonymous ID; no clinical details, names or direct identifiers would be requested by VEDA. The hospital would retain identity custody. Rectified times would be excluded from confirmatory analysis. Any 500-1,000 record pilot is only a design option pending protocol, IEC approval, data-protection review, data-sharing agreement, consent/waiver decision, security review and publication policy. No request is made by this draft and no affiliation or approval is claimed.""")
    _write_json(output / "14_INDIA_PROVENANCE_CONTRACT.json", {"activity": ACTIVITY, "classes": data["provenance_contract"]})
    _write_md(output / "15_INDIA_ROUTE_RANKING.md", "India route ranking", "\n".join(f"{row['rank']}. **{row['route']}** — {row['status']}. {row['reason']}" for row in data["route_ranking"]))
    _write_md(output / "16_FOUNDER_ACTION_CARD.md", "Founder action card", """1. Review the four unsent packs and legal/privacy boundaries.\n2. Choose whether to authorize a human enquiry to BVB, ICAS, one hospital research office, or Delhi CRS metadata route; no automatic sending.\n3. If a hospital route is selected, obtain institutional/IEC/legal review before any data movement.\n4. Keep rectified TOB outside confirmatory evidence and keep outcome selection out of acquisition.\n5. Do not start Ashtakavarga remediation or any prediction/ML activity from this audit.""")
    _write_md(output / "17_PARALLEL_LANE_STATE.md", "Parallel lane state", "\n".join(f"- {key}: `{value}`" for key, value in data["parallel_lanes"].items()))
    acceptance = "\n".join(f"| {row['id']} | {row['criterion']} | {row['status']} |" for row in data["acceptance"])
    _write_md(output / "18_FINAL_ACCEPTANCE.md", "Final acceptance", f"""Overall: **PASS_WITH_CONDITION**.\n\nThe lawful India access strategy and unsent packs are complete. The hospital route is promising but requires human institutional, ethics, privacy and legal gates. BVB/ICAS access is not assumed; CRS TOB is not established from the Delhi standard form; Shodhganga is discovery-only; Saptarishis remains provenance/rights/consent-unverified.\n\n| ID | Criterion | Status |\n|---|---|---|\n{acceptance}\n\nArtifact manifest hash: `{digest(data)}`\n\nNo personal data, raw provider data, thesis bulk downloads, external requests, astrology, feature scoring, ML, RAG subject data, PRED-M4 change or production change occurred.""")
    return digest(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true", help="write governed artifacts")
    args = parser.parse_args()
    data = build()
    artifact_hash = render(data) if args.emit else digest(data)
    print(json.dumps({"activity": ACTIVITY, "artifact_hash": artifact_hash, "emit": args.emit}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
