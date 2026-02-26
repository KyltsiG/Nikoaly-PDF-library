from sqlmodel import SQLModel, create_engine, Session
from backend.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Create all tables on startup."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency for FastAPI routes."""
    with Session(engine) as session:
        yield session
