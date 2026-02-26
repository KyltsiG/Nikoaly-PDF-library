from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Where uploaded PDFs are stored
PDF_STORAGE_DIR = BASE_DIR / "storage" / "pdfs"
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database path
DATABASE_URL = f"sqlite:///{BASE_DIR / 'storage' / 'library.db'}"

# ChromaDB storage path
CHROMA_DIR = BASE_DIR / "storage" / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# PDF text extraction settings
MAX_FILE_SIZE_MB = 50
ALLOWED_CONTENT_TYPE = "application/pdf"
