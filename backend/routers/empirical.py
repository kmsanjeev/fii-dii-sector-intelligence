"""Admin-only empirical case intake and staged bulk import API."""

from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.auth.middleware import require_admin
from engines.ai.orchestration.case_intake import CaseIntakeService, TEMPLATE_FIELDS, TEMPLATE_VERSION, template_csv

router = APIRouter(prefix="/api/empirical", tags=["veda-empirical-admin"])


class CaseRequest(BaseModel):
    case_external_id: str | None = None
    case_family_id: str | None = None
    independent_source_family: str | None = None
    case_class: str
    subject_name: str | None = None
    subject_id: str | None = None
    birth_date: str | None = None
    birth_time: str | None = None
    birth_time_precision: str | None = None
    birth_place: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    timezone: str | None = None
    birth_data_source: str | None = None
    birth_data_quality: str | None = None
    domain: str = "GENERAL_TIMING"
    event_type: str | None = None
    event_start: str | None = None
    event_end: str | None = None
    event_time_precision: str | None = None
    event_description: str | None = None
    event_direction: str | None = None
    event_source: str | None = None
    event_verification_quality: str | None = None
    source_type: str | None = None
    source_title: str | None = None
    source_author: str | None = None
    source_publication: str | None = None
    source_page: str | None = None
    source_passage_reference: str | None = None
    original_case_source: str | None = None
    independent_verification: str | None = None
    prediction_cutoff: str | None = None
    knowledge_cutoff: str | None = None
    outcome_cutoff: str | None = None
    outcome_known_at_entry: str | None = None
    notes: str | None = None


class IngestRequest(BaseModel):
    rows: list[int] | None = Field(default=None)


def _service() -> CaseIntakeService:
    return CaseIntakeService()


@router.get("/overview")
def overview(current_user=Depends(require_admin)):
    service = _service()
    return {"status": "READY", "template_version": TEMPLATE_VERSION, **service.counts()}


@router.post("/cases/validate")
def validate_case(req: CaseRequest, current_user=Depends(require_admin)):
    return _service().validate_payload(req.model_dump())


@router.post("/cases")
def create_case(req: CaseRequest, current_user=Depends(require_admin)):
    try:
        return _service().create_case(req.model_dump(), actor=current_user.email)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=exc.args[0]) from exc


@router.get("/cases")
def list_cases(limit: int = Query(100, ge=1, le=500), current_user=Depends(require_admin)):
    cases = _service().list_cases(limit)
    return {"cases": cases, "count": len(cases)}


@router.get("/cases/{case_id}")
def get_case(case_id: str, current_user=Depends(require_admin)):
    try:
        return _service().case_detail(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc


@router.post("/imports/preview")
async def preview_import(file: UploadFile = File(...), sheet: str | None = Query(None), current_user=Depends(require_admin)):
    content = await file.read()
    try:
        return _service().preview_import(content, file.filename or "upload", actor=current_user.email, sheet=sheet)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/imports")
def list_imports(limit: int = Query(50, ge=1, le=200), current_user=Depends(require_admin)):
    return {"imports": _service().list_imports(limit)}


@router.get("/imports/{import_id}")
def get_import(import_id: str, current_user=Depends(require_admin)):
    try:
        return _service().import_detail(import_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Import not found") from exc


@router.post("/imports/{import_id}/ingest")
def ingest_import(import_id: str, req: IngestRequest | None = None, current_user=Depends(require_admin)):
    try:
        return _service().ingest_import(import_id, actor=current_user.email, rows=req.rows if req else None)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Import not found") from exc


@router.get("/templates/csv")
def download_csv_template(current_user=Depends(require_admin)):
    return StreamingResponse(io.BytesIO(template_csv().encode("utf-8")), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=VEDA_Empirical_Case_Import_Template.csv"})


@router.get("/templates/xlsx")
def download_xlsx_template(current_user=Depends(require_admin)):
    from openpyxl import Workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Cases"
    sheet.append(["template_version"] + list(TEMPLATE_FIELDS))
    sheet.freeze_panes = "A2"
    sheet.append([TEMPLATE_VERSION] + ["" for _ in TEMPLATE_FIELDS])
    from openpyxl.comments import Comment
    sheet.cell(row=2, column=1).comment = Comment("Template header only. Delete this guidance row before import.", "VEDA")
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=VEDA_Empirical_Case_Import_Template.xlsx"})


@router.get("/validation-report/{import_id}")
def validation_report(import_id: str, current_user=Depends(require_admin)):
    try:
        detail = _service().import_detail(import_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Import not found") from exc
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["row_number", "status", "error_code", "message", "field", "suggested_action"])
    for row in detail["rows"]:
        issues = row["validation"]["errors"] + row["validation"]["warnings"]
        if not issues:
            writer.writerow([row["row_number"], row["status"], "", "", "", ""])
        for issue in issues:
            writer.writerow([row["row_number"], row["status"], issue["code"], issue["message"], issue["field"], "Review before ingest"])
    return StreamingResponse(io.BytesIO(output.getvalue().encode("utf-8")), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={import_id}-validation-report.csv"})
