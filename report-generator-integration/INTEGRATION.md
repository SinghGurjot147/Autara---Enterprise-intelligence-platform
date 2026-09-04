# Report Generator Integration

This is an additive patch for the existing Enterprise Intelligence Platform.
It does NOT replace the existing RAG pipeline or PPT generator.

## What it adds

- Four document-grounded report modes:
  - Executive Summary
  - Technical Architecture Audit
  - Compliance & Security Review
  - Weekly Intelligence Briefing
- Multiple PDF upload from every report card.
- Reuse of the existing `/documents` ingestion pipeline.
- Per-report selection of newly uploaded or existing indexed documents.
- Existing hybrid-style retrieval: Chroma vector retrieval + BM25 over the selected document IDs.
- Provider failover: Gemini 2.5 Flash -> Groq Llama 3.3 70B -> OpenRouter `openrouter/free` -> deterministic local fallback.
- Markdown preview and downloadable PDF.
- Source references with document name and page.

## Integration

1. Copy the `backend/app` files into your existing backend, preserving your existing files.
2. Copy the `frontend/src` files into the actual Vite frontend:
   `C:\Users\Asus\Desktop\frontend\src`
3. Run `integrate.ps1` from this folder, or make the two tiny manual changes below.

### Backend

In `backend/app/main.py`, add:

```python
from backend.app.routers.reports import router as reports_router
```

and after the FastAPI app is created add:

```python
app.include_router(reports_router)
```

The supplied integration script can insert these automatically and is idempotent.

### Frontend

In `frontend/src/components/workspace/workspace-views.tsx`:

Add this import:

```tsx
import { ReportGeneratorView as IntegratedReportGeneratorView } from "./report-generator"
```

Then replace only the reports switch case with:

```tsx
case "reports":
  return (
    <IntegratedReportGeneratorView
      documents={documents}
      onDocumentsChange={onDocumentsChange}
      onError={onError}
    />
  )
```

Do NOT replace the whole workspace-views.tsx file. This preserves the current PPT generator.

## Dependencies

The backend already uses the RAG stack. The report module additionally requires:

- `reportlab`
- `rank-bm25`
- `langchain-chroma`
- `langchain-core`
- the existing Gemini/Groq/OpenAI-compatible SDKs used by the project

If any are missing from the current environment, install them in the existing `.venv` rather than creating another environment.

For file uploads, FastAPI uses multipart form data and supports multiple `UploadFile` values; the existing document endpoint is reused rather than creating a second ingestion pipeline.
