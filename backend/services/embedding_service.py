import ollama
import chromadb
from chromadb.config import Settings
from backend.core.config import CHROMA_DIR


def get_chroma_collection():
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    # cosine distance is standard for text embeddings — measures angle between
    # vectors rather than magnitude, so text length doesn't affect similarity
    return client.get_or_create_collection(
        name="pdf_chunks",
        metadata={"hnsw:space": "cosine"},
    )


def chunk_page(text: str, chunk_size: int = 200, overlap: int = 30) -> list[str]:
    """
    Split a page's text into overlapping word-based chunks.
    Overlap prevents a sentence that falls on a chunk boundary from being
    split across two chunks where neither contains the full sentence.
    """
    if not text or not text.strip():
        return []

    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def embed_pdf(pdf_id: int, pages: list[dict], title: str) -> int:
    """
    Embed all pages of a PDF into ChromaDB.
    Each chunk stores its source page number so search results can
    point the user to the exact page where the match was found.
    """
    collection = get_chroma_collection()

    ids = []
    embeddings = []
    documents = []
    metadatas = []
    chunk_counter = 0

    for page in pages:
        page_number = page["page_number"]
        chunks = chunk_page(page["text"])

        for chunk in chunks:
            response = ollama.embeddings(model="nomic-embed-text", prompt=chunk)

            ids.append(f"{pdf_id}_{chunk_counter}")
            embeddings.append(response["embedding"])
            documents.append(chunk)
            metadatas.append({
                "pdf_id": pdf_id,
                "title": title,
                "page_number": page_number,
                "chunk_index": chunk_counter,
            })
            chunk_counter += 1

    if ids:
        collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    return chunk_counter


def delete_embeddings(pdf_id: int):
    """Remove all chunks belonging to a PDF — called when the PDF is deleted."""
    collection = get_chroma_collection()
    results = collection.get(where={"pdf_id": pdf_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def semantic_search(query: str, n_results: int = 5) -> list[dict]:
    """
    Embed the query and find the closest chunk vectors in ChromaDB.
    Uses HNSW approximate nearest-neighbour search — fast even at scale.
    """
    collection = get_chroma_collection()

    if collection.count() == 0:
        return []

    response = ollama.embeddings(model="nomic-embed-text", prompt=query)

    # Cap n_results to the actual collection size to avoid ChromaDB errors
    actual_n = min(n_results, collection.count())

    results = collection.query(
        query_embeddings=[response["embedding"]],
        n_results=actual_n,
        include=["documents", "metadatas", "distances"],
    )

    matches = []
    if results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            matches.append({
                "chunk": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

    return matches
