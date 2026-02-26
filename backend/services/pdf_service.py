import shutil
from pathlib import Path
from sqlmodel import Session, select
from backend.models.pdf import PDF
from backend.services.pdf_parser import extract_text, extract_text_by_page, get_title_from_pdf
from backend.services.embedding_service import embed_pdf, delete_embeddings
from backend.core.config import PDF_STORAGE_DIR


def save_pdf_file(upload_file, filename: str) -> Path:
    """Save an uploaded file to local storage and return its path."""
    dest = PDF_STORAGE_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return dest


def ingest_pdf(session: Session, file_path: Path, original_filename: str) -> PDF:
    """
    Full ingestion pipeline:
    1. Extract text and metadata
    2. Store in SQLite
    3. Embed chunks into ChromaDB with page numbers
    """
    # Extract full text for keyword search storage
    text, page_count = extract_text(file_path)

    # Extract per-page text for embeddings
    pages, _ = extract_text_by_page(file_path)

    title = get_title_from_pdf(file_path, original_filename)
    file_size = file_path.stat().st_size

    pdf = PDF(
        title=title,
        filename=original_filename,
        file_path=str(file_path),
        page_count=page_count,
        file_size_bytes=file_size,
        extracted_text=text,
    )
    session.add(pdf)
    session.commit()
    session.refresh(pdf)

    # Embed into ChromaDB with page-level metadata
    if pages:
        embed_pdf(pdf.id, pages, title)

    return pdf


def get_all_pdfs(session: Session) -> list[PDF]:
    return session.exec(select(PDF)).all()


def get_pdf_by_id(session: Session, pdf_id: int) -> PDF | None:
    return session.get(PDF, pdf_id)


def delete_pdf(session: Session, pdf_id: int) -> bool:
    pdf = session.get(PDF, pdf_id)
    if not pdf:
        return False

    delete_embeddings(pdf_id)

    file = Path(pdf.file_path)
    if file.exists():
        file.unlink()

    session.delete(pdf)
    session.commit()
    return True