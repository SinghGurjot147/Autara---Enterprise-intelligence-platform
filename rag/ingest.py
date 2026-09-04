from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_chroma import Chroma
from rag.chunking.hierarchical import hierarchical_chunk_documents
from rag.embeddings.local import get_local_embeddings


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# LOAD PDF DOCUMENTS
# --------------------------------------------------

loader = PyPDFDirectoryLoader("documents")
documents = loader.load()

print(f"Loaded {len(documents)} pages")


# --------------------------------------------------
# HIERARCHICAL CHUNKING
# --------------------------------------------------

chunks = hierarchical_chunk_documents(documents)

print(f"Created {len(chunks)} child chunks")


if chunks:
    print("\nSample chunk metadata:")
    print(chunks[0].metadata)


# --------------------------------------------------
# BGE EMBEDDINGS
# --------------------------------------------------

print("\nLoading local BGE embedding model...")

embeddings = get_local_embeddings()

print("Using local BGE embeddings for ingestion.")


# --------------------------------------------------
# CREATE CHROMA VECTOR DATABASE
# --------------------------------------------------

print("\nCreating vector database...")

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="chroma_db"
)

print("\nRAG knowledge base created successfully using BGE!")