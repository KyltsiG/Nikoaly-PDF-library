from pathlib import Path
from sqlmodel import Session, select
from backend.models.pdf import PDF
from backend.services.pdf_parser import extract_text_by_page


def count_matches(text: str, query: str) -> int:
    if not text or not query:
        return 0
    return text.lower().count(query.lower())


def find_match_page(file_path: str, query: str) -> int | None:
    """
    Re-open the PDF to find which page the query first appears on.
    Done at search time rather than stored at ingest time because queries
    are unpredictable — we can't know in advance what to index per page.
    """
    path = Path(file_path)
    if not path.exists():
        return None

    try:
        pages, _ = extract_text_by_page(path)
        lower_query = query.lower()
        for page in pages:
            if lower_query in page["text"].lower():
                return page["page_number"]
    except Exception:
        return None

    return None


def extract_snippet(text: str, query: str, context_chars: int = 200) -> str:
    """Extract a window of text around the first occurrence of the query."""
    if not text:
        return ""

    lower_text = text.lower()
    lower_query = query.lower()

    idx = lower_text.find(lower_query)
    if idx == -1:
        return ""

    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(query) + context_chars)
    snippet = text[start:end].strip()

    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


def search_pdfs(session: Session, query: str) -> list[dict]:
    """
    Keyword search across all PDFs. Counts matches in both title and body,
    ranks by total match count so the most relevant document appears first.
    """
    if not query or not query.strip():
        return []

    query = query.strip()
    all_pdfs = session.exec(select(PDF)).all()

    results = []
    lower_query = query.lower()

    for pdf in all_pdfs:
        title_matches = count_matches(pdf.title, query)
        text_matches = count_matches(pdf.extracted_text, query)
        total_matches = title_matches + text_matches

        if total_matches == 0:
            continue

        snippet = extract_snippet(pdf.extracted_text or "", query)

        # Only scan for page number when there are body matches —
        # a title-only match has no meaningful page to point to
        page_number = None
        if text_matches > 0:
            page_number = find_match_page(pdf.file_path, query)

        results.append({
            "id": pdf.id,
            "title": pdf.filename,
            "filename": pdf.filename,
            "file_path": pdf.file_path,
            "page_count": pdf.page_count,
            "file_size_bytes": pdf.file_size_bytes,
            "uploaded_at": pdf.uploaded_at,
            "snippet": snippet,
            "matches": total_matches,
            "match_page": page_number,
        })

    results.sort(key=lambda r: r["matches"], reverse=True)
    return results
