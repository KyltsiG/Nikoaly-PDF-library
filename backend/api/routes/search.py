from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from backend.db.database import get_session
from backend.services.search_service import search_pdfs

router = APIRouter()


@router.get("/")
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    session: Session = Depends(get_session),
):
    results = search_pdfs(session, q)
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }
