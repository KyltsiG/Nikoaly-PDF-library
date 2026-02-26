from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import pdfs
from backend.api.routes import search
from backend.api.routes import semantic
from backend.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up — initialising database...")
    init_db()
    yield
    print("Shutting down.")


app = FastAPI(
    lifespan=lifespan,
    title="PDF Library API",
    description="Local PDF library with AI-powered search.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdfs.router,      prefix="/api/pdfs",     tags=["pdfs"])
app.include_router(search.router,    prefix="/api/search",   tags=["search"])
app.include_router(semantic.router,  prefix="/api/semantic", tags=["semantic"])


@app.get("/health")
def health():
    return {"status": "ok"}
