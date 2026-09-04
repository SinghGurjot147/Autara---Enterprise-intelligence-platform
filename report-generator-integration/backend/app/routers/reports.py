from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.app.services.report_generator import generate_report, resolve_report

router = APIRouter(prefix="/reports", tags=["reports"])


class GenerateReportRequest(BaseModel):
    report_type: str = Field(min_length=1, max_length=80)
    document_ids: list[str] = Field(min_length=1, max_length=50)


@router.post("/generate")
def create_report(request: GenerateReportRequest):
    try:
        return generate_report(request.report_type, request.document_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc


@router.get("/{report_id}/download")
def download_report(report_id: str):
    path = resolve_report(report_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
