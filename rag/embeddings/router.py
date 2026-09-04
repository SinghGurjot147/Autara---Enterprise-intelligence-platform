from rag.embeddings.local import get_local_embeddings


def get_embeddings():
    """
    Always use local BGE embeddings.

    BGE is used for both:
    - document ingestion
    - query embeddings

    No Gemini embedding API calls are made.
    """
    print("Using local BGE embeddings.")
    return get_local_embeddings()


def get_saved_provider():
    """
    Kept for compatibility with existing code.
    """
    return "local_bge"


def save_provider(provider):
    """
    Kept for compatibility with existing code.
    """
    pass