from sqlmodel import SQLModel, Session, create_engine
from backend.core.config import DATABASE_URL

# connect_args is SQLite-specific — prevents "same thread" errors in FastAPI
# which uses multiple threads to handle concurrent requests
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db():
    # Creates all tables defined with table=True — safe to call on every startup
    SQLModel.metadata.create_all(engine)


def get_session():
    # FastAPI dependency — opens a session per request and closes it when done,
    # even if an exception is raised mid-request
    with Session(engine) as session:
        yield session
