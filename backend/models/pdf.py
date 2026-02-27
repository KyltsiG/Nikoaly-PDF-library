from datetime import datetime
from sqlmodel import SQLModel, Field


class PDFBase(SQLModel):
    # Shared fields used by both the database model and API schemas
    title: str
    filename: str
    file_path: str
    page_count: int
    file_size_bytes: int


class PDF(PDFBase, table=True):
    # Auto-assigned by SQLite on insert
    id: int | None = Field(default=None, primary_key=True)

    # default_factory calls utcnow at insert time, not at class definition time
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # Stored for keyword search — can be several MB for large documents
    extracted_text: str | None = Field(default=None)


class PDFRead(PDFBase):
    # API response schema — excludes extracted_text to keep responses small
    id: int
    uploaded_at: datetime
