import shutil
from pathlib import Path
from sqlmodel import Session, select
from backend.models.pdf import PDF
from backend.services.pdf_parser import extract_text, extract_text_by_page, get_title_from_pdf
from backend.services.embedding_service import embed_pdf, delete_embeddings
from backend.core.config import PDF_STORAGE_DIR


def save_pdf_file(upload_file, filename: str) -> Path:
    dest = PDF_STORAGE_DIR / filename
    # copyfileobj streams in chunks — avoids loading the whole file into memory
    with dest.open("wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return dest


def ingest_pdf(session: Session, file_path: Path, original_filename: str) -> PDF:
    """
    Full ingestion pipeline for a newly uploaded PDF.
    Extracts text twice: once as a flat string for SQLite keyword search,
    and once per page so embeddings carry page number metadata.
    """
    text, page_count = extract_text(file_path)
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
    # Refresh to populate the auto-assigned id before passing it to embed_pdf
    session.refresh(pdf)

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

    # Remove vectors first — if this fails we want to keep the file and DB record
    # so the user can try deleting again rather than being left with orphaned vectors
    delete_embeddings(pdf_id)

    file = Path(pdf.file_path)
    if file.exists():
        file.unlink()

    session.delete(pdf)
    session.commit()
    return True
