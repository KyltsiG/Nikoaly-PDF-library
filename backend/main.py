from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import pdfs, search, semantic
from backend.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all SQLite tables exist before the first request arrives
    init_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="PDF Library API",
    description="Local PDF library with AI-powered search.",
    version="0.3.0",
)

# Allow the React dev server to call this API — without this the browser
# blocks all cross-origin requests between port 5173 and port 8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdfs.router,     prefix="/api/pdfs",     tags=["pdfs"])
app.include_router(search.router,   prefix="/api/search",   tags=["search"])
app.include_router(semantic.router, prefix="/api/semantic", tags=["semantic"])


@app.get("/health")
def health():
    return {"status": "ok"}
