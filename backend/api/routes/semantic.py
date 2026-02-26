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

    # Group by PDF, keep best match per PDF (lowest distance)
    # Also track the page number of the best match
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

        page_number = match["metadata"].get("page_number")

        results.append({
            "id": pdf.id,
            "title": pdf.title,
            "filename": pdf.filename,
            "file_path": pdf.file_path,
            "page_count": pdf.page_count,
            "file_size_bytes": pdf.file_size_bytes,
            "uploaded_at": pdf.uploaded_at,
            "snippet": match["chunk"][:400] + "..." if len(match["chunk"]) > 400 else match["chunk"],
            "similarity": round((1 - match["distance"]) * 100, 1),
            "match_page": page_number,
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

    result = answer_question(session, question)
    return result


@router.get("/debug")
def debug_chroma():
    """Debug endpoint — shows what's stored in ChromaDB."""
    collection = get_chroma_collection()
    count = collection.count()

    sample = collection.get(limit=5, include=["documents", "metadatas"])

    return {
        "total_chunks": count,
        "sample_chunks": [
            {
                "id": sample["ids"][i],
                "metadata": sample["metadatas"][i],
                "text_preview": sample["documents"][i][:200],
            }
            for i in range(len(sample["ids"]))
        ]
    }