from __future__ import annotations

import io

from fastapi import FastAPI
from fastapi.testclient import TestClient
from openpyxl import Workbook

from backend.auth.middleware import AuthMiddleware
from backend.routers import empirical
from engines.ai.orchestration.case_intake import CaseIntakeService


def _payload(**overrides):
    value = {
        "case_external_id": "CASE-001",
        "case_class": "HISTORICAL_VERIFIED",
        "subject_name": "Subject A",
        "subject_id": "SUBJECT-A",
        "birth_date": "1980-01-01",
        "birth_time": "10:30:00",
        "birth_time_precision": "EXACT",
        "birth_place": "Delhi",
        "timezone": "Asia/Calcutta",
        "birth_data_source": "DOCUMENT_VERIFIED",
        "birth_data_quality": "HIGH",
        "domain": "CAREER",
        "event_type": "JOB_CHANGE",
        "event_start": "2020-01-01",
        "event_description": "Changed role",
        "event_source": "EMPLOYMENT_RECORD",
        "event_verification_quality": "DOCUMENT_VERIFIED",
        "source_type": "BOOK",
        "source_title": "Verified case file",
        "source_author": "Researcher",
        "source_passage_reference": "p. 10",
        "original_case_source": "ARCHIVE-A",
        "independent_verification": "EMPLOYMENT_RECORD",
        "prediction_cutoff": "2019-01-01",
        "knowledge_cutoff": "2019-01-01",
        "outcome_cutoff": "2020-02-01",
    }
    value.update(overrides)
    return value


def test_case_validation_quality_eligibility_and_persistence(tmp_dir):
    service = CaseIntakeService(tmp_dir / "research.sqlite3")
    result = service.validate_payload(_payload())
    assert result["status"] == "VALID"
    assert result["eligibility"] == "ELIGIBLE"
    created = service.create_case(_payload(), actor="admin@localhost")
    assert created["status"] == "ADDED"
    assert service.counts() == {"cases": 1, "eligible": 1}
    assert service.case_detail("CASE-001")["audit_history"]


def test_duplicate_case_family_and_leakage_are_not_empirical(tmp_dir):
    service = CaseIntakeService(tmp_dir / "research.sqlite3")
    service.create_case(_payload(), actor="admin@localhost")
    duplicate = service.validate_payload(_payload())
    assert duplicate["duplicate_state"] in {"EXACT_DUPLICATE", "SAME_CASE_FAMILY"}
    assert duplicate["eligibility"] == "DUPLICATE"
    no_cutoffs = service.validate_payload(_payload(case_external_id="CASE-002", event_start="2021-01-01", original_case_source="ARCHIVE-B", prediction_cutoff=None, knowledge_cutoff=None, outcome_cutoff=None))
    assert no_cutoffs["eligibility"] == "LEAKAGE_INVALID"


def test_csv_preview_ingest_history_report_and_idempotency(tmp_dir):
    service = CaseIntakeService(tmp_dir / "research.sqlite3")
    csv_data = "case_external_id,case_class,subject_id,birth_date,birth_time,birth_time_precision,birth_data_source,domain,event_type,event_start,event_verification_quality,source_type,source_title,prediction_cutoff,knowledge_cutoff,outcome_cutoff\nCASE-CSV,HISTORICAL_VERIFIED,SUBJECT-CSV,1980-01-01,10:30,EXACT,DOCUMENT_VERIFIED,CAREER,JOB_CHANGE,2020-01-01,DOCUMENT_VERIFIED,BOOK,Case file,2019-01-01,2019-01-01,2020-02-01\n"
    preview = service.preview_import(csv_data.encode(), "cases.csv", actor="admin@localhost")
    assert preview["summary"]["rows"] == 1
    assert preview["summary"]["eligible"] == 1
    first = service.ingest_import(preview["import_id"], actor="admin@localhost")
    second = service.ingest_import(preview["import_id"], actor="admin@localhost")
    assert first["accepted"] == 1
    assert second["duplicates"] == 1
    assert service.import_detail(preview["import_id"])["status"] == "INGESTED"


def test_xlsx_preview_and_templates(tmp_dir):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["case_id", "case_class", "subject_id", "birth_date", "domain", "event_type", "event_start", "source_title"])
    sheet.append(["CASE-XLSX", "HISTORICAL_DOCUMENTED", "SUBJECT-X", "1980-01-01", "CAREER", "JOB_CHANGE", "2020-01-01", "Workbook case"])
    output = io.BytesIO()
    workbook.save(output)
    service = CaseIntakeService(tmp_dir / "research.sqlite3")
    preview = service.preview_import(output.getvalue(), "cases.xlsx", actor="admin@localhost")
    assert preview["file_type"] == "XLSX"
    assert preview["mapping"]["case_id"] == "case_external_id"
    assert preview["summary"]["rows"] == 1


def test_admin_api_requires_admin_and_exposes_case_intake(tmp_dir, monkeypatch):
    monkeypatch.setattr(empirical, "_service", lambda: CaseIntakeService(tmp_dir / "research.sqlite3"))
    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.include_router(empirical.router)
    client = TestClient(app)
    assert client.get("/api/empirical/overview").status_code == 200
    response = client.post("/api/empirical/cases/validate", json=_payload())
    assert response.status_code == 200
    assert response.json()["eligibility"] == "ELIGIBLE"
    assert client.get("/api/empirical/templates/csv").status_code == 200
    assert client.get("/api/empirical/templates/xlsx").status_code == 200
