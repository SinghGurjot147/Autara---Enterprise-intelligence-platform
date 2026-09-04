from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.app.schemas.presentation import GenerateResponse, OutlineItem, PresentationRequest
from backend.app.services import rag_context, storage
from backend.app.services.images import fetch_images_for_spec
from backend.app.services.planner import generate_presentation_spec
from backend.app.services.renderer import render_pptx
from backend.app.services.validate import PptxValidationError, validate_pptx

logger = logging.getLogger("presentations.router")

router = APIRouter(prefix="/presentations", tags=["presentations"])


@router.post("/generate", response_model=GenerateResponse)
def generate_presentation(req: PresentationRequest) -> GenerateResponse:
    warnings: list[str] = []

    # ---- Stage 0: optional RAG context (Mode 2 only). Never duplicates retrieval â€”
    # delegates to the existing system via services/rag_context.py.
    context_chunks: list = []
    if req.mode == "rag":
        context_chunks, rag_warnings = rag_context.retrieve_context(req.topic, req.document_ids)
        warnings.extend(rag_warnings)

    # ---- Stage 1: planning (Gemini -> validated PresentationSpec, with local fallback)
    spec, planner_warnings = generate_presentation_spec(req, context_chunks)
    warnings.extend(planner_warnings)

    # ---- Image acquisition (best-effort; missing images degrade to text/shape layout)
    images = fetch_images_for_spec(spec.slides, enabled=req.include_images)
    if req.include_images and not images:
        warnings.append("No images could be retrieved (no image provider configured or all lookups failed) â€” rendered with text/shape layouts instead.")

    # ---- Stage 2: deterministic rendering
    presentation_id, out_path, display_filename = storage.new_presentation_path(spec.title)
    try:
        render_pptx(spec, images, out_path, include_notes=req.include_notes, include_sources=req.include_sources)
        validate_pptx(out_path, expected_slide_count=len(spec.slides))
    except PptxValidationError as e:
        logger.error("PPTX validation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Presentation generation produced an invalid file: {e}") from e
    except Exception as e:  # noqa: BLE001
        logger.exception("PPTX rendering failed")
        raise HTTPException(status_code=500, detail=f"Presentation rendering failed: {e}") from e

    storage.register_presentation(presentation_id, out_path, display_filename, slide_count=len(spec.slides))

    outline = [OutlineItem(slide_number=s.slide_number, type=s.type, title=s.title or s.type.value.title()) for s in spec.slides]

    return GenerateResponse(
        success=True,
        presentation_id=presentation_id,
        filename=display_filename,
        download_url=f"/presentations/{presentation_id}/download",
        slide_count=len(spec.slides),
        outline=outline,
        warnings=warnings,
    )


@router.get("/{presentation_id}/download")
def download_presentation(presentation_id: str):
    entry = storage.resolve_presentation(presentation_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return FileResponse(
        path=str(entry["absolute_path"]),
        filename=entry["filename"],
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@router.get("/{presentation_id}")
def get_presentation_meta(presentation_id: str):
    entry = storage.resolve_presentation(presentation_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return {
        "presentation_id": presentation_id,
        "filename": entry["filename"],
        "slide_count": entry["slide_count"],
        "download_url": f"/presentations/{presentation_id}/download",
    }

