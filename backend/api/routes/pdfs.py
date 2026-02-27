import uuid
import re
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session
from pathlib import Path
from backend.db.database import get_session
from backend.models.pdf import PDFRead
from backend.services.pdf_service import save_pdf_file, ingest_pdf, get_all_pdfs, get_pdf_by_id, delete_pdf
from backend.core.config import MAX_FILE_SIZE_MB, ALLOWED_CONTENT_TYPE

router = APIRouter()


def sanitize_filename(filename: str) -> str:
    # Strip extension, replace anything that isn't a word char or dash with underscore,
    # then reattach .pdf — prevents path traversal and filesystem issues on Windows
    name = filename.rsplit(".", 1)[0]
    name = re.sub(r"[^\w\-]", "_", name)
    return f"{name}.pdf"


@router.post("/upload", response_model=PDFRead, status_code=201)
async def upload_pdf(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    if file.content_type != ALLOWED_CONTENT_TYPE:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Check Content-Length header first — avoids writing oversized files to disk
    if file.size and file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.")

    safe_name = sanitize_filename(file.filename)
    # UUID prefix guarantees uniqueness even if two users upload the same filename
    unique_filename = f"{uuid.uuid4()}_{safe_name}"
    file_path = save_pdf_file(file, unique_filename)

    # Second size check after writing — Content-Length can be absent or spoofed
    if file_path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.")

    try:
        pdf = ingest_pdf(session, file_path, file.filename)
    except Exception as e:
        # Clean up the saved file if ingestion fails so storage stays consistent
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    return pdf


@router.get("/", response_model=list[PDFRead])
def list_pdfs(session: Session = Depends(get_session)):
    return get_all_pdfs(session)


@router.get("/{pdf_id}", response_model=PDFRead)
def get_pdf(pdf_id: int, session: Session = Depends(get_session)):
    pdf = get_pdf_by_id(session, pdf_id)
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found.")
    return pdf


@router.get("/{pdf_id}/preview")
def preview_pdf(pdf_id: int, session: Session = Depends(get_session)):
    pdf = get_pdf_by_id(session, pdf_id)
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found.")
    file_path = Path(pdf.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk.")
    # "inline" tells the browser to render the PDF rather than downloading it
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{pdf.filename}\""},
    )


@router.get("/{pdf_id}/download")
def download_pdf(pdf_id: int, session: Session = Depends(get_session)):
    pdf = get_pdf_by_id(session, pdf_id)
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found.")
    file_path = Path(pdf.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk.")
    # "attachment" tells the browser to save the file to disk
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=pdf.filename,
        headers={"Content-Disposition": f"attachment; filename=\"{pdf.filename}\""},
    )


@router.delete("/{pdf_id}", status_code=204)
def remove_pdf(pdf_id: int, session: Session = Depends(get_session)):
    if not delete_pdf(session, pdf_id):
        raise HTTPException(status_code=404, detail="PDF not found.")
