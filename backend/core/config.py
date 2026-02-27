from pathlib import Path

# Resolve project root regardless of where the process is launched from
BASE_DIR = Path(__file__).resolve().parent.parent.parent

PDF_STORAGE_DIR = BASE_DIR / "storage" / "pdfs"
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{BASE_DIR / 'storage' / 'library.db'}"

CHROMA_DIR = BASE_DIR / "storage" / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE_MB = 50
ALLOWED_CONTENT_TYPE = "application/pdf"
