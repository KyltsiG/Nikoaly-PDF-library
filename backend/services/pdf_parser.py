from pathlib import Path
import fitz  # PyMuPDF


def extract_text(file_path: Path) -> tuple[str, int]:
    """Extract all text from a PDF as one string, plus the page count."""
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
    Extract text per page so embeddings can be tied to a specific page number.
    Skips empty pages — they add noise without providing searchable content.
    Returns a list of { page_number, text } dicts (1-indexed) and total page count.
    """
    doc = fitz.open(str(file_path))
    page_count = doc.page_count

    pages = []
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        text = page.get_text().strip()
        if text:
            pages.append({
                "page_number": page_num + 1,
                "text": text,
            })

    doc.close()
    return pages, page_count


def get_title_from_pdf(file_path: Path, fallback_filename: str) -> str:
    """
    Derive a display title from the original filename.
    PDF metadata titles are often inconsistent or missing entirely,
    so the filename is always used for predictable display.
    """
    return Path(fallback_filename).stem.replace("_", " ").replace("-", " ").title()
