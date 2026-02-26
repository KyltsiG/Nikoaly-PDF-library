from datetime import datetime
from sqlmodel import SQLModel, Field


class PDFBase(SQLModel):
    title: str
    filename: str
    file_path: str
    page_count: int
    file_size_bytes: int


class PDF(PDFBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uploaded_at: datetime = Field(default_factory=datetime.now)
    extracted_text: str | None = Field(default=None)


class PDFCreate(PDFBase):
    pass


class PDFRead(PDFBase):
    id: int
    uploaded_at: datetime