from sqlmodel import Session, select
from backend.models.pdf import PDF


def count_matches(text: str, query: str) -> int:
    """Count how many times the query appears in the text."""
    if not text or not query:
        return 0
    return text.lower().count(query.lower())


def extract_snippet(text: str, query: str, context_chars: int = 200) -> str:
    """
    Find the first occurrence of query in text and return a surrounding snippet.
    Returns empty string if not found.
    """
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
    Search PDFs by title or extracted text.
    Returns results sorted by number of matches (most relevant first).
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

        results.append({
            "id": pdf.id,
            "title": pdf.title,
            "filename": pdf.filename,
            "file_path": pdf.file_path,
            "page_count": pdf.page_count,
            "file_size_bytes": pdf.file_size_bytes,
            "uploaded_at": pdf.uploaded_at,
            "snippet": snippet,
            "matches": total_matches,
        })

    # Sort by matches descending — most relevant first
    results.sort(key=lambda r: r["matches"], reverse=True)

    return results