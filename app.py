from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pathlib import Path
import os
from rag.query import run_rag
from rag.ingest import ingest_pdf


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
# RUN SERVER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

