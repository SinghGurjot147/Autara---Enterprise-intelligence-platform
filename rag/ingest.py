from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma

from rag.chunking.hierarchical import hierarchical_chunk_documents
from rag.embeddings.local import get_local_embeddings

load_dotenv()

CHROMA_PATH = "chroma_db"


def ingest_pdf(pdf_path: str):
    """Process one uploaded PDF and add it to the RAG knowledge base."""

    print(f"\nIngesting: {pdf_path}")

    # Load PDF
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    print(f"Loaded {len(documents)} pages")

    # Chunk
    chunks = hierarchical_chunk_documents(documents)

    print(f"Created {len(chunks)} child chunks")

    if not chunks:
        raise ValueError("No chunks were created from the PDF.")

    # Embeddings
    print("Loading local BGE embedding model...")
    embeddings = get_local_embeddings()

    # Add to existing Chroma database
    print("Adding chunks to Chroma...")

    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

    vectorstore.add_documents(chunks)

    print("PDF added to RAG knowledge base successfully.")

    return {
        "filename": pdf_path,
        "pages": len(documents),
        "chunks": len(chunks)
    }


if __name__ == "__main__":
    # Manual ingestion of everything inside documents/
    from pathlib import Path

    documents_dir = Path("documents")

    for pdf in documents_dir.glob("*.pdf"):
        ingest_pdf(str(pdf))