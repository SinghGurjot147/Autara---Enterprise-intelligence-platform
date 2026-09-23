from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pathlib import Path
import os
from rag.query import run_rag,  get_report_context
from rag.ingest import ingest_pdf
from rag.presentation import create_presentation
import uuid
from rag.report import generate_report_content, create_report

# --------------------------------------------------
# FLASK APP
# --------------------------------------------------
# FRONTEND CONFIGURATION
# --------------------------------------------------

FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIST),
    static_url_path=""
)

CORS(app)

# --------------------------------------------------
# DOCUMENT STORAGE
# --------------------------------------------------

DOCUMENTS_DIR = Path("documents")
DOCUMENTS_DIR.mkdir(exist_ok=True)




# --------------------------------------------------
# CHAT / RAG QUERY
# --------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({
            "error": "Question is required"
        }), 400

    question = data["question"].strip()

    if not question:
        return jsonify({
            "error": "Question cannot be empty"
        }), 400

    try:
        result = run_rag(question)

        return jsonify({
            "answer": result["answer"],
            "sources": result.get("sources", [])
        }), 200

    except Exception as e:
        print(f"RAG error: {e}")

        return jsonify({
            "error": str(e)
        }), 500


# --------------------------------------------------
# PDF UPLOAD / RAG INGESTION
# --------------------------------------------------

@app.route("/documents", methods=["POST"])
def upload_document():

    if "file" not in request.files:
        return jsonify({
            "error": "No file uploaded"
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "error": "No file selected"
        }), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({
            "error": "Only PDF files are supported"
        }), 400

    try:
        filename = secure_filename(file.filename)

        if not filename:
            return jsonify({
                "error": "Invalid filename"
            }), 400

        pdf_path = DOCUMENTS_DIR / filename

        file.save(pdf_path)

        print(f"Uploaded PDF: {pdf_path}")

        result = ingest_pdf(str(pdf_path))

        return jsonify({
            "document_id": pdf_path.stem,
            "filename": filename
        }), 200

    except Exception as e:
        print(f"Upload/Ingestion error: {e}")

        return jsonify({
            "error": str(e)
        }), 500


# --------------------------------------------------
# LIST DOCUMENTS
# --------------------------------------------------

@app.route("/documents", methods=["GET"])
def get_documents():

    files = []

    for file in DOCUMENTS_DIR.glob("*.pdf"):
        files.append({
            "document_id": file.stem,
            "filename": file.name,
            "size": file.stat().st_size,
            "content_type": "application/pdf"
        })

    return jsonify({
        "documents": files
    }), 200


# --------------------------------------------------
# DELETE DOCUMENT
# --------------------------------------------------

@app.route("/documents/<document_id>", methods=["DELETE"])
def delete_document(document_id):

    try:
        pdf_path = DOCUMENTS_DIR / f"{document_id}.pdf"

        if not pdf_path.exists():
            return jsonify({
                "error": "Document not found"
            }), 404

        pdf_path.unlink()

        return jsonify({
            "message": "Document deleted successfully",
            "document_id": document_id
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


# --------------------------------------------------
# SERVE REACT FRONTEND
# --------------------------------------------------

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):

    requested_file = FRONTEND_DIST / path


    if path and requested_file.exists():
        return app.send_static_file(path)

    return app.send_static_file("index.html")


# --------------------------------------------------
# PRESENTATION GENERATOR
# --------------------------------------------------

@app.route("/presentations/generate", methods=["POST"])
def generate_presentation():

    data = request.get_json()

    if not data or "topic" not in data:
        return jsonify({
            "error": "Topic is required"
        }), 400

    topic = data["topic"].strip()

    if not topic:
        return jsonify({
            "error": "Topic cannot be empty"
        }), 400

    try:
        slide_count = int(data.get("slide_count", 6))

        if slide_count < 2:
            slide_count = 2

        # --------------------------------------------
        # GENERATE AI SLIDE CONTENT
        # --------------------------------------------

        from rag.presentation import generate_slide_content

        slides = generate_slide_content(topic)

        # Respect requested slide count
        slides = slides[:slide_count]

        # --------------------------------------------
        # CREATE POWERPOINT
        # --------------------------------------------

        result = create_presentation(
            topic,
            slides,
            include_notes=data.get("include_notes", False)
        )

        return jsonify({
            "success": True,
            "presentation_id": result["presentation_id"],
            "filename": result["filename"],
            "download_url": (
                f"/presentations/"
                f"{result['presentation_id']}/download"
            ),
            "slide_count": result["slide_count"],
            "outline": [
                {
                    "slide_number": index + 1,
                    "type": "title" if index == 0 else "content",
                    "title": slide.get("title", "")
                }
                for index, slide in enumerate(slides)
            ],
            "warnings": []
        }), 200

    except Exception as e:

        print(f"Presentation generation error: {e}")

        return jsonify({
            "error": str(e)
        }), 500

# --------------------------------------------------
# PRESENTATION DOWNLOAD
# --------------------------------------------------

@app.route("/presentations/<presentation_id>/download", methods=["GET"])
def download_presentation(presentation_id):

    from flask import send_file

    presentation_path = (
        Path("generated")
        / "presentations"
        / f"{presentation_id}.pptx"
    )

    if not presentation_path.exists():
        return jsonify({
            "error": "Presentation not found"
        }), 404

    return send_file(
        presentation_path,
        as_attachment=True,
        download_name=presentation_path.name
    )

# --------------------------------------------------
# REPORT GENERATION
# --------------------------------------------------

@app.route("/reports/generate", methods=["POST"])
def generate_report():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    topic = str(data.get("topic", "")).strip()
    document_ids = data.get("document_ids", [])

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    try:
        print(f"\nGenerating report: {topic}")
        print(f"Document IDs: {document_ids}")

        report_context = get_report_context(
            topic,
            k=12,
            document_ids=document_ids
        )

        context = report_context.get("context", "")

        if not context:
            return jsonify({
                "error": "No relevant document content found for report generation."
            }), 400

        report_data = generate_report_content(
            topic,
            context=context
        )

        report_file = create_report(
            topic,
            report_data
        )

        return jsonify({
            "success": True,
            "report_id": report_file["report_id"],
            "filename": report_file["filename"],
            "download_url": f"/reports/{report_file['report_id']}/download"
        }), 200

    except Exception as e:
        print(f"Report generation error: {e}")

        return jsonify({
            "error": str(e)
        }), 500


@app.route("/reports/<report_id>/download", methods=["GET"])
def download_report(report_id):
    try:
        report_path = Path("generated/reports") / f"{report_id}.pdf"

        if not report_path.exists():
            return jsonify({
                "error": "Report not found"
            }), 404

        from flask import send_file

        return send_file(
            report_path,
            as_attachment=True,
            download_name=f"{report_id}.pdf"
        )

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
    
    
# --------------------------------------------------
# RUN SERVER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

