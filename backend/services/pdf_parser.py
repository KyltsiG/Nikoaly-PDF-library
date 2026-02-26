from pathlib import Path
import fitz  # PyMuPDF


def extract_text(file_path: Path) -> tuple[str, int]:
    """
    Extract full text and page count from a PDF.
    Returns (extracted_text, page_count).
    """
    doc = fitz.open(str(file_path))
    page_count = doc.page_count

    full_text = ""
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        full_text += page.get_text().strip() + "\n\n"

    doc.close()
    return full_text, page_count


def extract_text_by_page(file_path: Path) -> tuple[list[dict], int]:
    """
    Extract text per page from a PDF.
    Returns (pages, page_count) where pages is a list of
    { page_number: int (1-indexed), text: str }
    """
    doc = fitz.open(str(file_path))
    page_count = doc.page_count

    pages = []
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        text = page.get_text().strip()
        if text:
            pages.append({
                "page_number": page_num + 1,  # 1-indexed for display
                "text": text,
            })

    doc.close()
    return pages, page_count


def get_title_from_pdf(file_path: Path, fallback_filename: str) -> str:
    """
    Try to read the PDF's built-in title metadata.
    Falls back to the filename (without extension) if not found.
    """
    doc = fitz.open(str(file_path))
    metadata = doc.metadata
    doc.close()

    title = metadata.get("title", "").strip()
    if title:
        return title

    return Path(fallback_filename).stem.replace("_", " ").replace("-", " ").title()