from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from backend.db.database import get_session
from backend.services.search_service import search_pdfs

router = APIRouter()


@router.get("/")
def search(
    q: str = Query(..., min_length=1),
    session: Session = Depends(get_session),
):
    results = search_pdfs(session, q)
    # Envelope format lets the frontend show result count without counting the array
    return {"query": q, "count": len(results), "results": results}
