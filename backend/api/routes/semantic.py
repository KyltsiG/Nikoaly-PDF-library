from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from backend.db.database import get_session
from backend.services.embedding_service import semantic_search, get_chroma_collection
from backend.services.qa_service import answer_question
from backend.models.pdf import PDF

router = APIRouter()


@router.get("/search")
def semantic_search_route(
    q: str = Query(..., min_length=1),
    session: Session = Depends(get_session),
):
    matches = semantic_search(q, n_results=10)

    if not matches:
        return {"query": q, "count": 0, "results": []}

    # Multiple chunks from the same PDF may match — keep only the best one
    # (lowest distance = most similar) so each PDF appears once in results
    pdf_best: dict[int, dict] = {}
    for match in matches:
        pid = match["metadata"]["pdf_id"]
        if pid not in pdf_best or match["distance"] < pdf_best[pid]["distance"]:
            pdf_best[pid] = match

    results = []
    for pid, match in pdf_best.items():
        pdf = session.get(PDF, pid)
        if not pdf:
            continue

        results.append({
            "id": pdf.id,
            "title": pdf.title,
            "filename": pdf.filename,
            "file_path": pdf.file_path,
            "page_count": pdf.page_count,
            "file_size_bytes": pdf.file_size_bytes,
            "uploaded_at": pdf.uploaded_at,
            "snippet": match["chunk"][:400] + "..." if len(match["chunk"]) > 400 else match["chunk"],
            # Convert cosine distance to a 0–100% similarity score for display
            "similarity": round((1 - match["distance"]) * 100, 1),
            "match_page": match["metadata"].get("page_number"),
        })

    results.sort(key=lambda r: r["similarity"], reverse=True)
    return {"query": q, "count": len(results), "results": results}


@router.post("/ask")
def ask_question(
    payload: dict,
    session: Session = Depends(get_session),
):
    question = payload.get("question", "").strip()
    if not question:
        return {"answer": "Please provide a question.", "sources": []}

    return answer_question(session, question)


@router.get("/debug")
def debug_chroma():
    """Shows what's currently stored in ChromaDB — useful for verifying embeddings."""
    collection = get_chroma_collection()
    sample = collection.get(limit=5, include=["documents", "metadatas"])

    return {
        "total_chunks": collection.count(),
        "sample_chunks": [
            {
                "id": sample["ids"][i],
                "metadata": sample["metadatas"][i],
                "text_preview": sample["documents"][i][:200],
            }
            for i in range(len(sample["ids"]))
        ]
    }
