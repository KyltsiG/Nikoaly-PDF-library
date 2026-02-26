import ollama
import chromadb
from chromadb.config import Settings
from backend.core.config import CHROMA_DIR


def get_chroma_collection():
    """Connect to ChromaDB and return the PDF chunks collection."""
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name="pdf_chunks",
        metadata={"hnsw:space": "cosine"},
    )


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 30) -> list[str]:
    """
    Split text into smaller overlapping word-based chunks.
    Smaller chunks = more precise semantic matches.
    chunk_size: number of words per chunk
    overlap: number of words shared between consecutive chunks
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


def embed_pdf(pdf_id: int, text: str, title: str) -> int:
    """
    Chunk the PDF text, embed each chunk via Ollama,
    and store in ChromaDB. Returns number of chunks stored.
    """
    collection = get_chroma_collection()
    chunks = chunk_text(text)

    if not chunks:
        return 0

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        response = ollama.embeddings(model="nomic-embed-text", prompt=chunk)
        embedding = response["embedding"]

        ids.append(f"{pdf_id}_{i}")
        embeddings.append(embedding)
        documents.append(chunk)
        metadatas.append({
            "pdf_id": pdf_id,
            "title": title,
            "chunk_index": i,
        })

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    return len(chunks)


def delete_embeddings(pdf_id: int):
    """Remove all chunks for a given PDF from ChromaDB."""
    collection = get_chroma_collection()
    results = collection.get(where={"pdf_id": pdf_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def semantic_search(query: str, n_results: int = 5) -> list[dict]:
    """
    Embed the query and find the most similar chunks in ChromaDB.
    Returns a list of matching chunks with metadata.
    """
    collection = get_chroma_collection()

    # Check if collection has any data
    if collection.count() == 0:
        return []

    response = ollama.embeddings(model="nomic-embed-text", prompt=query)
    query_embedding = response["embedding"]

    actual_n = min(n_results, collection.count())

    results = collection.query(
        query_embeddings=[query_embedding],
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