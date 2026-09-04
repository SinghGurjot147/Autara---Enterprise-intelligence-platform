from pathlib import Path
import sys
import json
import uuid
import shutil
from rag.embeddings.local import get_local_embeddings
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma


# --------------------------------------------------
# Project Root
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))


# --------------------------------------------------
# Existing RAG
# --------------------------------------------------

from rag.query import run_rag


# --------------------------------------------------
# Document Ingestion
# --------------------------------------------------

from rag.chunking.hierarchical import hierarchical_chunk_documents
# --------------------------------------------------
# Paths
# --------------------------------------------------

DOCUMENTS_DIR = ROOT_DIR / "documents"
CHROMA_DIR = ROOT_DIR / "chroma_db"
MANIFEST_FILE = DOCUMENTS_DIR / "manifest.json"

DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# App
# --------------------------------------------------

app = FastAPI(
    title="Enterprise Intelligence Platform API",
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Request Models
# --------------------------------------------------

class QueryRequest(BaseModel):
    question: str


# --------------------------------------------------
# Manifest Helpers
# --------------------------------------------------

def load_manifest():
    if not MANIFEST_FILE.exists():
        return {}

    try:
        with open(MANIFEST_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            return data

        return {}

    except Exception:
        return {}


def save_manifest(manifest):
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    temp_file = MANIFEST_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(
            manifest,
            file,
            indent=2,
            ensure_ascii=False
        )

    temp_file.replace(MANIFEST_FILE)


# --------------------------------------------------
# Basic Routes
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Enterprise Intelligence Platform API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# RAG Query
# --------------------------------------------------

@app.post("/query")
def query_rag(request: QueryRequest):
    result = run_rag(request.question)

    return {
        "answer": result["answer"],
        "sources": result["sources"]
    }


# --------------------------------------------------
# Document List
# --------------------------------------------------

@app.get("/documents")
def list_documents():
    manifest = load_manifest()

    documents = []

    for document_id, metadata in manifest.items():

        file_path = DOCUMENTS_DIR / metadata["filename"]

        # Remove stale manifest entries automatically
        if not file_path.exists():
            continue

        documents.append({
            "document_id": document_id,
            "filename": metadata["filename"],
            "size": file_path.stat().st_size,
            "content_type": metadata.get(
                "content_type",
                "application/pdf"
            )
        })

    return {
        "documents": documents
    }


# --------------------------------------------------
# Document Upload
# --------------------------------------------------

@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):

    # ----------------------------------------------
    # Validate file
    # ----------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided."
        )

    filename = Path(file.filename).name

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    # ----------------------------------------------
    # Generate unique document ID
    # ----------------------------------------------

    document_id = str(uuid.uuid4())

    # Keep original filename
    file_path = DOCUMENTS_DIR / filename

    # Avoid overwriting an existing file
    if file_path.exists():
        stem = file_path.stem
        suffix = file_path.suffix

        counter = 1

        while file_path.exists():
            file_path = DOCUMENTS_DIR / f"{stem}_{counter}{suffix}"
            counter += 1

        filename = file_path.name

    # ----------------------------------------------
    # Save uploaded PDF
    # ----------------------------------------------

    try:

        with open(file_path, "wb") as buffer:

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                buffer.write(chunk)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {error}"
        )


    # ----------------------------------------------
    # Load ONLY this PDF
    # ----------------------------------------------

    try:

        loader = PyPDFLoader(str(file_path))
        pages = loader.load()

        if not pages:
            raise ValueError("The PDF contains no readable pages.")

    except Exception as error:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=f"Failed to read PDF: {error}"
        )


    # ----------------------------------------------
    # Add document metadata BEFORE chunking
    # ----------------------------------------------

    for page in pages:

        page.metadata["document_id"] = document_id
        page.metadata["original_filename"] = filename
        page.metadata["content_type"] = "application/pdf"


    # ----------------------------------------------
    # Hierarchical chunking
    # ----------------------------------------------

    try:

        chunks = hierarchical_chunk_documents(pages)

        if not chunks:
            raise ValueError(
                "No usable text chunks were created from the PDF."
            )

    except Exception as error:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to chunk PDF: {error}"
        )


    # ----------------------------------------------
    # Get current embedding provider
    # ----------------------------------------------

    try:

        embeddings = get_local_embeddings()

    except Exception as error:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize embeddings: {error}"
        )


    # ----------------------------------------------
    # Connect to EXISTING Chroma database
    # ----------------------------------------------

    try:

        vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings
        )

    except Exception as error:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to open vector database: {error}"
        )


    # ----------------------------------------------
    # Generate deterministic chunk IDs
    # ----------------------------------------------

    chunk_ids = [
        f"{document_id}_{index}"
        for index in range(len(chunks))
    ]


    # ----------------------------------------------
    # Add ONLY new document chunks
    # ----------------------------------------------

    try:

        vectorstore.add_documents(
            documents=chunks,
            ids=chunk_ids
        )

    except Exception as error:

        # Try to remove anything that may have been inserted
        try:
            vectorstore.delete(ids=chunk_ids)
        except Exception:
            pass

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to add document to vector database: {error}"
        )


    # ----------------------------------------------
    # Save document metadata
    # ----------------------------------------------

    manifest = load_manifest()

    manifest[document_id] = {
        "filename": filename,
        "content_type": "application/pdf",
        "chunks": len(chunks)
    }

    try:

        save_manifest(manifest)

    except Exception as error:

        # If manifest cannot be saved, remove vector entries
        try:
            vectorstore.delete(ids=chunk_ids)
        except Exception:
            pass

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save document metadata: {error}"
        )


    # ----------------------------------------------
    # Success
    # ----------------------------------------------

    return {
        "document_id": document_id,
        "filename": filename
    }


# --------------------------------------------------
# Document Delete
# --------------------------------------------------

@app.delete("/documents/{document_id}")
def delete_document(document_id: str):

    manifest = load_manifest()

    if document_id not in manifest:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    metadata = manifest[document_id]
    filename = metadata["filename"]

    file_path = DOCUMENTS_DIR / filename


    # ----------------------------------------------
    # Open Chroma using current provider
    # ----------------------------------------------

    try:

        embeddings = get_local_embeddings()

        vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to open vector database: {error}"
        )


    # ----------------------------------------------
    # Delete chunks belonging to this document
    # ----------------------------------------------

    try:

        vectorstore.delete(
            where={
                "document_id": document_id
            }
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove document from vector database: {error}"
        )


    # ----------------------------------------------
    # Delete physical PDF
    # ----------------------------------------------

    try:

        file_path.unlink(missing_ok=True)

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove document file: {error}"
        )


    # ----------------------------------------------
    # Remove manifest entry
    # ----------------------------------------------

    del manifest[document_id]
    save_manifest(manifest)


    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }