# Nikoäly PDF Library — Full System Documentation

A complete explanation of every file, function, and process in the system from the moment a user opens the app to the moment an AI answer appears on screen.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [How the Frontend and Backend Communicate](#2-how-the-frontend-and-backend-communicate)
3. [Application Startup](#3-application-startup)
4. [PDF Upload and Ingestion Pipeline](#4-pdf-upload-and-ingestion-pipeline)
5. [The Database Layer](#5-the-database-layer)
6. [The Embedding Pipeline](#6-the-embedding-pipeline)
7. [Keyword Search](#7-keyword-search)
8. [Semantic Search](#8-semantic-search)
9. [AI Q&A — The RAG Pipeline](#9-ai-qa--the-rag-pipeline)
10. [PDF Preview and Download](#10-pdf-preview-and-download)
11. [Delete Pipeline](#11-delete-pipeline)
12. [The Frontend — Component Tree](#12-the-frontend--component-tree)
13. [State Management in the Frontend](#13-state-management-in-the-frontend)
14. [Data Flow Diagrams](#14-data-flow-diagrams)
15. [File Reference](#15-file-reference)

---

## 1. System Overview

The system is split into two completely separate programs that run at the same time and talk to each other over HTTP:

**The Backend** is a Python program built with FastAPI. It runs at `localhost:8000`. It handles all the heavy work — reading PDF files, extracting text, storing data in databases, running AI models, and serving files. It has no user interface. It only speaks JSON and files.

**The Frontend** is a React application built with Vite. It runs at `localhost:5173`. It is what the user sees and interacts with. It has no direct access to files, databases, or AI — it can only ask the backend to do things by sending HTTP requests.

**The Databases** are two separate storage systems:

- **SQLite** — a single file at `storage/library.db`. Stores structured metadata about each PDF: title, filename, page count, file size, upload date, and the full extracted text.
- **ChromaDB** — a folder at `storage/chroma/`. Stores vector embeddings — numerical representations of meaning — for every chunk of text from every PDF. Used for semantic search and Q&A.

**Ollama** is a third-party program running as a background service on your machine. It hosts two AI models:
- `nomic-embed-text` — converts text into vectors (numbers representing meaning)
- `llama3.2` — a language model that reads context and generates answers

---

## 2. How the Frontend and Backend Communicate

Every action in the UI triggers an HTTP request from the frontend to the backend. This is the only way they communicate — there is no shared memory, no direct database access from the frontend, nothing else.

An HTTP request has:
- A **method** — GET (fetch data), POST (send data), DELETE (remove data)
- A **URL** — identifies what resource or action is being requested
- A **body** (optional) — data sent with POST requests, usually JSON
- A **response** — JSON data sent back from the backend

**CORS** (Cross-Origin Resource Sharing) is a browser security feature that normally blocks requests between different ports. Since the frontend is on port 5173 and the backend is on port 8000, the backend explicitly tells the browser it's okay to receive requests from those origins via the `CORSMiddleware` in `main.py`.

---

## 3. Application Startup

### Backend startup — `backend/main.py`

When you run `python -m uvicorn backend.main:app --reload`, Python loads `main.py`. Here is what happens in order:

**1. The lifespan function runs**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up — initialising database...")
    init_db()
    yield
    print("Shutting down.")
```

The `@asynccontextmanager` decorator means this function runs around the entire lifetime of the app. Everything before `yield` runs on startup, everything after runs on shutdown. `init_db()` is called which creates the SQLite tables if they don't already exist.

**2. The FastAPI app is created**

```python
app = FastAPI(lifespan=lifespan, title="PDF Library API", version="0.3.0")
```

This creates the main application object. All routes and middleware attach to this object.

**3. CORS middleware is added**

```python
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", ...])
```

This tells the browser it's safe to make requests from the frontend. Without this, every fetch call from React would be blocked.

**4. Routers are mounted**

```python
app.include_router(pdfs.router,     prefix="/api/pdfs")
app.include_router(search.router,   prefix="/api/search")
app.include_router(semantic.router, prefix="/api/semantic")
```

Each router is a group of related endpoints defined in separate files. Mounting them with a prefix means all PDF endpoints start with `/api/pdfs`, all search endpoints with `/api/search`, and so on.

### Database initialisation — `backend/db/database.py`

`init_db()` calls `SQLModel.metadata.create_all(engine)`. SQLModel scans all imported model classes that have `table=True` and creates their corresponding tables in SQLite if they don't already exist. Since it checks first, this is safe to run every startup — it won't overwrite existing data.

`get_session()` is a FastAPI dependency. Routes declare it with `Depends(get_session)` and FastAPI automatically opens a database session before the route runs and closes it after, even if an error occurs.

### Frontend startup — `src/main.jsx`

Vite serves the React app. React mounts the `<App />` component into the `#root` div in `index.html`. `App.jsx` immediately fetches all PDFs from the backend via `GET /api/pdfs/` and stores them in state, then passes them down to `Library.jsx`.

### Config — `backend/core/config.py`

This file runs on import and sets up all paths and constants used throughout the backend:

- `BASE_DIR` — the root of the project, calculated by going three directories up from the config file itself
- `PDF_STORAGE_DIR` — where uploaded PDFs are saved on disk (`storage/pdfs/`)
- `DATABASE_URL` — the SQLite connection string pointing to `storage/library.db`
- `CHROMA_DIR` — where ChromaDB stores its vector data (`storage/chroma/`)
- `MAX_FILE_SIZE_MB` — maximum allowed upload size (50MB)
- `ALLOWED_CONTENT_TYPE` — only `application/pdf` is accepted

Both `PDF_STORAGE_DIR` and `CHROMA_DIR` call `.mkdir(parents=True, exist_ok=True)` at import time, which creates the folders automatically if they don't exist yet.

---

## 4. PDF Upload and Ingestion Pipeline

This is the most important flow in the system. When a user drops a PDF onto the upload zone, a chain of seven steps executes.

### Step 1 — Frontend sends the file

In `UploadZone.jsx`, when a file is dropped or selected:

```javascript
const formData = new FormData();
formData.append("file", file);
const res = await fetch("http://127.0.0.1:8000/api/pdfs/upload", {
    method: "POST",
    body: formData,
});
```

`FormData` is a browser API for sending files over HTTP. The file is attached under the key `"file"`. The request is sent to the backend as `multipart/form-data`.

### Step 2 — Backend validates the file

In `backend/api/routes/pdfs.py`, the `upload_pdf` route receives the file:

```python
@router.post("/upload", response_model=PDFRead, status_code=201)
async def upload_pdf(file: UploadFile = File(...), session: Session = Depends(get_session)):
```

FastAPI automatically parses the multipart form and gives you an `UploadFile` object. The route then:

- Checks `file.content_type == "application/pdf"` — rejects anything that isn't a PDF
- Checks `file.size` against `MAX_FILE_SIZE_MB` if the size header is available
- Sanitizes the filename using `sanitize_filename()` which replaces spaces and special characters with underscores
- Prepends a UUID (`uuid.uuid4()`) to make the filename unique, preventing collisions if two people upload files with the same name

### Step 3 — File is saved to disk

`save_pdf_file()` in `pdf_service.py`:

```python
def save_pdf_file(upload_file: UploadFile, filename: str) -> Path:
    dest = PDF_STORAGE_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return dest
```

`shutil.copyfileobj` copies the file in chunks rather than loading it all into memory — important for large files. The file is written to `storage/pdfs/` and the full path is returned.

### Step 4 — Text is extracted from the PDF

`extract_text()` in `pdf_parser.py`:

```python
def extract_text(file_path: Path) -> tuple[str, int]:
    doc = fitz.open(str(file_path))
    page_count = doc.page_count
    full_text = ""
    for page_num in range(page_count):
        page = doc.load_page(page_num)
        full_text += page.get_text().strip() + "\n\n"
    doc.close()
    return full_text, page_count
```

PyMuPDF (`fitz`) opens the PDF file, loops through every page, and calls `get_text()` on each one. The text from all pages is joined together with double newlines. The function returns the full text and the page count as a tuple.

`get_title_from_pdf()` reads the PDF's built-in metadata. Most PDFs have a title field in their metadata. If it's empty, it falls back to cleaning up the filename — replacing underscores and dashes with spaces and capitalising each word.

### Step 5 — Metadata is stored in SQLite

Back in `ingest_pdf()` in `pdf_service.py`:

```python
pdf = PDF(
    title=title,
    filename=original_filename,
    file_path=str(file_path),
    page_count=page_count,
    file_size_bytes=file_size,
    extracted_text=text,
)
session.add(pdf)
session.commit()
session.refresh(pdf)
```

A `PDF` model object is created with all the metadata. `session.add()` stages it for insertion, `session.commit()` writes it to the SQLite file, and `session.refresh()` reloads the object from the database so the auto-generated `id` and `uploaded_at` fields are populated.

### Step 6 — Text is chunked and embedded

After the SQLite record is created:

```python
if text:
    embed_pdf(pdf.id, text, title)
```

This calls `embed_pdf()` in `embedding_service.py`. The full text is first split into chunks by `chunk_text()`:

```python
def chunk_text(text: str, chunk_size: int = 200, overlap: int = 30) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
```

This splits the text into chunks of 200 words with a 30-word overlap. The overlap is critical — it means the end of one chunk and the start of the next share 30 words. This prevents a sentence that falls exactly on a chunk boundary from being split and losing its context.

For each chunk, Ollama is called to generate an embedding:

```python
response = ollama.embeddings(model="nomic-embed-text", prompt=chunk)
embedding = response["embedding"]
```

An embedding is a list of 768 floating-point numbers. Each number represents a dimension in a high-dimensional semantic space. Chunks with similar meaning will have similar numbers — their vectors will be close together in that space. Chunks with unrelated meaning will have very different numbers — their vectors will be far apart.

All chunks are then stored in ChromaDB together:

```python
collection.add(
    ids=ids,             # e.g. "42_0", "42_1", "42_2" (pdf_id + chunk_index)
    embeddings=embeddings,
    documents=documents,  # the actual text of each chunk
    metadatas=metadatas,  # pdf_id, title, chunk_index for each chunk
)
```

The ID format `{pdf_id}_{chunk_index}` ensures uniqueness across all PDFs and makes it possible to delete all chunks for a specific PDF later.

### Step 7 — Response returned to frontend

The route returns the `PDFRead` schema which excludes `extracted_text` (you don't want to send megabytes of text back in the response). The frontend receives the new PDF's metadata, `onUploadSuccess()` fires which re-fetches the full library, and the new card appears in the grid.

---

## 5. The Database Layer

### SQLite via SQLModel — `backend/models/pdf.py`

SQLModel combines two libraries: SQLAlchemy (database ORM) and Pydantic (data validation). You define one class and get both a database table and an API schema.

```python
class PDFBase(SQLModel):
    title: str
    filename: str
    file_path: str
    page_count: int
    file_size_bytes: int
```

`PDFBase` holds the shared fields. It is not a table itself.

```python
class PDF(PDFBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    extracted_text: str | None = Field(default=None)
```

`PDF` is the actual database table. `table=True` tells SQLModel to create a real SQL table for this class. `id` is the primary key — `default=None` means SQLite auto-assigns it on insert. `uploaded_at` uses `default_factory=datetime.utcnow` which calls the function at insert time (not at class definition time — an important Python distinction). `extracted_text` is the full text of the PDF, stored as a potentially very long string.

```python
class PDFRead(PDFBase):
    id: int
    uploaded_at: datetime
```

`PDFRead` is the API response schema. It deliberately excludes `extracted_text` because you never want to send the full document text in API responses — it could be megabytes of data.

### ChromaDB — `backend/services/embedding_service.py`

ChromaDB is a vector database. Unlike SQLite which stores rows of structured data, ChromaDB stores vectors — lists of numbers — alongside the text they represent and metadata about where they came from.

```python
def get_chroma_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name="pdf_chunks",
        metadata={"hnsw:space": "cosine"},
    )
```

`PersistentClient` means data is saved to disk at `CHROMA_DIR`. `get_or_create_collection` either loads the existing collection or creates a new one. `hnsw:space: cosine` sets the distance metric to cosine similarity — the standard for comparing text embeddings. Cosine distance measures the angle between two vectors, not their length, which makes it robust to texts of different lengths.

---

## 6. The Embedding Pipeline

Already covered in detail in Section 4, but here is the key concept:

**Why 200 words per chunk?**

The embedding model converts a piece of text into a fixed-size vector regardless of how long the text is. A 2-word sentence and a 2000-word essay both become 768 numbers. But with very long text, specific details get diluted — the vector represents the overall topic rather than the specific content. Smaller chunks produce vectors that represent specific ideas more precisely, making similarity search much more accurate.

**Why 30-word overlap?**

Consider a sentence: "The mitochondria is the powerhouse of the cell." If chunk 1 ends with "the mitochondria is the" and chunk 2 starts with "powerhouse of the cell", neither chunk contains the full sentence and neither will match a query about it well. With overlap, both chunks contain the full sentence, so at least one will match.

**The embedding model: nomic-embed-text**

This model was specifically designed and trained for text embedding tasks. It produces 768-dimensional vectors and is efficient enough to run on CPU. When two pieces of text are semantically similar, their vectors will have a small cosine distance (close to 0). When they are unrelated, the distance will be large (close to 1, or even 2 at maximum dissimilarity).

---

## 7. Keyword Search

### Backend — `backend/services/search_service.py`

Keyword search is the simplest of the three modes. It works by loading all PDFs from SQLite and doing Python string matching:

```python
def count_matches(text: str, query: str) -> int:
    return text.lower().count(query.lower())
```

`.lower()` on both sides makes it case-insensitive. `.count()` returns the total number of non-overlapping occurrences of the query string in the text.

```python
def extract_snippet(text: str, query: str, context_chars: int = 200) -> str:
    idx = lower_text.find(lower_query)
    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(query) + context_chars)
    snippet = text[start:end].strip()
```

`find()` returns the character index of the first occurrence. A window of 200 characters before and after is sliced out. `max(0, ...)` and `min(len(text), ...)` prevent going outside the string boundaries. Ellipsis is added if the snippet was trimmed.

Results are sorted by `total_matches` descending — the PDF where your query appears most often is most relevant.

### Backend — `backend/api/routes/search.py`

```python
@router.get("/")
def search(q: str = Query(..., min_length=1), session: Session = Depends(get_session)):
    results = search_pdfs(session, q)
    return {"query": q, "count": len(results), "results": results}
```

`Query(..., min_length=1)` means the `q` parameter is required and must be at least 1 character. FastAPI validates this automatically and returns a 422 error if violated.

### Frontend

In `Library.jsx`, when the mode is `keyword`:

```javascript
const res = await fetch(`http://127.0.0.1:8000/api/search/?q=${encodeURIComponent(q)}`);
```

`encodeURIComponent` converts special characters in the query to URL-safe encoding — spaces become `%20`, ampersands become `%26`, etc. Without this, a query like "C&A report" would break the URL.

Results are displayed in `SearchResultCard.jsx` with the matching text highlighted using a regex-based `highlightMatch()` function that wraps matching words in `<mark>` tags styled with a semi-transparent orange background.

---

## 8. Semantic Search

### How it works conceptually

Instead of looking for exact word matches, semantic search finds documents that are *about* the same thing as your query, even if they use completely different words. This works because the embedding model has learned that "heart disease" and "cardiovascular condition" occupy similar regions of the vector space.

### Backend — `backend/services/embedding_service.py`

```python
def semantic_search(query: str, n_results: int = 5) -> list[dict]:
    response = ollama.embeddings(model="nomic-embed-text", prompt=query)
    query_embedding = response["embedding"]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_n,
        include=["documents", "metadatas", "distances"],
    )
```

The query string is embedded using the same model used during ingestion — this is critical. Both the stored chunks and the query must be in the same vector space for similarity to be meaningful.

ChromaDB's `.query()` method performs an **HNSW (Hierarchical Navigable Small World)** graph search. This is an approximate nearest-neighbour algorithm that finds the closest vectors very efficiently without comparing against every single stored vector. It returns the `n_results` closest chunks along with their distances.

### Backend — `backend/api/routes/semantic.py`

The semantic search route groups results by PDF — multiple chunks from the same PDF might match, but you only want to show that PDF once:

```python
pdf_best: dict[int, dict] = {}
for match in matches:
    pid = match["metadata"]["pdf_id"]
    if pid not in pdf_best or match["distance"] < pdf_best[pid]["distance"]:
        pdf_best[pid] = match
```

For each PDF that had a matching chunk, only the best (lowest distance = most similar) chunk is kept. The similarity score shown to the user is calculated as `(1 - distance) * 100` — converting the distance (0=identical, 1=unrelated) to a percentage similarity score (100%=identical, 0%=unrelated).

---

## 9. AI Q&A — The RAG Pipeline

RAG stands for Retrieval-Augmented Generation. It is the technique of giving a language model relevant context from your documents before asking it a question, rather than relying on the model's pre-trained knowledge.

### Why RAG?

Language models are trained on general internet text. They don't know what's in your specific PDF library. But they are very good at reading a piece of text and answering questions about it. RAG combines these two capabilities: use vector search to find relevant text, then use the LLM to reason about that text.

### Step by step — `backend/services/qa_service.py`

**Step 1: Retrieve relevant chunks**

```python
matches = semantic_search(question, n_results=3)
```

The question is semantically searched against ChromaDB. The top 3 most similar chunks are returned. Using 3 rather than 5 keeps the context focused — more chunks means more noise.

**Step 2: Filter weak matches**

```python
strong_matches = [m for m in matches if m["distance"] < 0.5]
```

Cosine distance above 0.5 means the match is quite weak — the chunk is probably from a document that isn't really about the question. These are filtered out. If all matches are weak (which can happen if the question is about something not in the library), the top 2 are kept as a fallback.

**Step 3: Build the context string**

```python
context_parts.append(f'Document: "{title}"\n{chunk}')
```

Each chunk is labelled with its source document title. This is important — it tells the LLM which document each piece of information comes from, so it can cite sources in its answer.

**Step 4: Build the prompt**

```python
prompt = f"""You are a precise document assistant. Your only job is to answer 
the question using ONLY the document excerpts provided below.

Rules:
- Only use information explicitly stated in the excerpts below
- Always mention which document your answer comes from
- If the excerpts do not contain enough information, say: "The documents in 
  your library do not contain enough information to answer this question."
- Never guess or use outside knowledge
- Keep your answer concise and direct

Document excerpts:
{context}

Question: {question}

Answer:"""
```

The prompt has three parts: a system instruction defining the role and rules, the context (the retrieved chunks), and the question. The rules are explicit and repeated — LLMs respond better to clear, specific instructions.

**Step 5: Call the language model**

```python
response = ollama.chat(
    model="llama3.2",
    messages=[{"role": "user", "content": prompt}],
    options={"temperature": 0.1},
)
```

`temperature: 0.1` is crucial. Temperature controls how random the model's output is. At temperature 1.0 (default) the model is creative and varied but tends to hallucinate. At 0.1 it is focused and deterministic — it sticks closely to the provided context rather than improvising. For a factual Q&A system you always want low temperature.

**Step 6: Return answer and sources**

The answer text and the list of source PDFs are returned to the route, which sends them as JSON to the frontend. The `QAResultCard` component displays the answer in a styled block and the source document titles as pill tags below it.

---

## 10. PDF Preview and Download

### Backend endpoints — `backend/api/routes/pdfs.py`

Both preview and download use FastAPI's `FileResponse` which streams the file directly from disk to the browser:

```python
@router.get("/{pdf_id}/preview")
def preview_pdf(pdf_id: int, session: Session = Depends(get_session)):
    pdf = get_pdf_by_id(session, pdf_id)
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{pdf.filename}\""},
    )
```

The difference between preview and download is one header:
- `inline` — tells the browser to display the file inside the page (preview)
- `attachment` — tells the browser to save the file to disk (download)

### Frontend — `PreviewModal.jsx`

The modal renders the PDF using an `<iframe>`:

```jsx
<iframe src={previewUrl} title={pdf.title} className="modal-iframe" />
```

The browser has a built-in PDF renderer that activates when an iframe points to a PDF URL. No third-party library is needed. The preview URL is `http://127.0.0.1:8000/api/pdfs/{id}/preview` which returns the file with `Content-Disposition: inline`.

Two `useEffect` hooks manage side effects:
- One listens for the Escape key and calls `onClose()` when pressed
- One sets `document.body.style.overflow = "hidden"` to prevent the background from scrolling while the modal is open, and restores it when the modal closes via the cleanup function

Clicking the overlay (the dark background outside the modal) closes it. Clicking inside the modal itself does not close it — `e.stopPropagation()` on the modal div prevents the click from bubbling up to the overlay's onClick handler.

---

## 11. Delete Pipeline

When the delete button is confirmed in `PDFCard.jsx`:

```javascript
await fetch(`http://127.0.0.1:8000/api/pdfs/${pdf.id}`, { method: "DELETE" });
```

The backend `remove_pdf` route calls `delete_pdf()` in `pdf_service.py` which does three things in order:

1. `delete_embeddings(pdf_id)` — queries ChromaDB for all chunk IDs that have `pdf_id` in their metadata, then deletes them. This keeps ChromaDB clean and prevents ghost results in future searches.

2. `file.unlink()` — deletes the actual PDF file from `storage/pdfs/`

3. `session.delete(pdf)` + `session.commit()` — removes the row from SQLite

All three must succeed for the delete to be complete. If ChromaDB deletion fails, the file and database record are not deleted either — the system stays consistent.

---

## 12. The Frontend — Component Tree

```
App.jsx
└── Library.jsx
    ├── UploadZone.jsx
    ├── SearchModeToggle.jsx
    ├── SearchBar.jsx
    ├── SortBar.jsx
    │
    ├── [Library view]
    │   ├── PDFCard.jsx (×N)
    │   │   └── PreviewModal.jsx (conditional)
    │   └── EmptyState.jsx
    │
    └── [Search/Q&A view]
        ├── SearchResultCard.jsx (×N)
        │   └── PreviewModal.jsx (conditional)
        └── QAResultCard.jsx
```

### Component responsibilities

**`App.jsx`** — owns the PDF list state. Fetches all PDFs on mount via `useEffect`. Passes `pdfs`, `loading`, `error`, and `onRefresh` down to Library. `onRefresh` is simply the fetch function — any child can call it to trigger a re-fetch of the library.

**`Library.jsx`** — the main orchestrator. Owns all search state: `searchMode`, `query`, `results`, `qaResult`, `hasSearched`, `searching`, `librarySortBy`, `searchSortBy`. Decides which view to show (library or results) and which components to render.

**`UploadZone.jsx`** — handles drag-and-drop and file input. Manages its own `uploading`, `dragging`, and `message` state. Calls `onUploadSuccess` (which is `onRefresh`) after a successful upload.

**`SearchModeToggle.jsx`** — a stateless display component. Renders three buttons, highlights the active one. Calls `onChange` when a button is clicked.

**`SearchBar.jsx`** — a controlled form. The input value is in React state. On submit, calls `onSearch`. The placeholder and submit button label change based on the `mode` prop.

**`SortBar.jsx`** — a stateless display component. Renders pill buttons from the `options` prop. Calls `onChange` when one is clicked.

**`PDFCard.jsx`** — manages its own `confirming`, `deleting`, and `previewing` state. The `onClick` on the card opens the preview modal. The actions div has `e.stopPropagation()` so clicking buttons doesn't also trigger the card click.

**`SearchResultCard.jsx`** — same pattern as `PDFCard` but also receives `query` for the `highlightMatch` function that wraps matching words in styled `<mark>` tags.

**`PreviewModal.jsx`** — a portal-style overlay. Manages scroll lock and keyboard events via `useEffect`. Renders a full-screen overlay with an iframe inside.

**`QAResultCard.jsx`** — a pure display component. Receives `answer` and `sources` as props and renders them.

**`EmptyState.jsx`** — a pure display component. Shown when the library has no PDFs.

---

## 13. State Management in the Frontend

The app uses only React's built-in `useState` and `useMemo` — no external state library.

**`App.jsx` state:**
- `pdfs` — the full array of PDF objects from the backend
- `loading` — true while the initial fetch is in flight
- `error` — error message string if the fetch failed

**`Library.jsx` state:**
- `searchMode` — `"keyword"` | `"semantic"` | `"qa"`
- `query` — the current search string (used for highlighting)
- `results` — array of search result objects
- `qaResult` — the Q&A response object `{ answer, sources }`
- `searching` — true while any search request is in flight
- `searchError` — error message if search failed
- `hasSearched` — true after first search, stays true until clear
- `librarySortBy` — current sort for the library grid
- `searchSortBy` — current sort for search results

**`useMemo` for sorting:**

```javascript
const sortedPdfs = useMemo(() => sortItems(pdfs, librarySortBy), [pdfs, librarySortBy]);
const sortedResults = useMemo(() => sortItems(results, searchSortBy), [results, searchSortBy]);
```

`useMemo` caches the sorted array and only recalculates it when its dependencies (`pdfs`/`results` or the sort key) actually change. Without this, the sort function would run on every single render — wasteful even though it's fast for small arrays.

---

## 14. Data Flow Diagrams

### Upload flow
```
User drops PDF on UploadZone
        ↓
FormData POST → /api/pdfs/upload
        ↓
Validate (type, size)
        ↓
Save to storage/pdfs/
        ↓
PyMuPDF: extract text + page count
        ↓
SQLite: INSERT into pdf table
        ↓
chunk_text() → 200-word chunks with 30-word overlap
        ↓
For each chunk → ollama.embeddings() → 768-number vector
        ↓
ChromaDB: store vectors + text + metadata
        ↓
Return PDFRead JSON to frontend
        ↓
onRefresh() → re-fetch library → card appears in grid
```

### Keyword search flow
```
User types query → clicks Search
        ↓
GET /api/search/?q=query
        ↓
Load all PDFs from SQLite
        ↓
For each PDF: count occurrences in title + extracted_text
        ↓
Extract snippet around first match
        ↓
Sort by total_matches descending
        ↓
Return results JSON
        ↓
SearchResultCard renders with highlighted matches
```

### Semantic search flow
```
User types query → clicks Search (Semantic mode)
        ↓
GET /api/semantic/search?q=query
        ↓
ollama.embeddings(query) → 768-number query vector
        ↓
ChromaDB.query() → top 5 most similar chunk vectors
        ↓
Group chunks by PDF, keep best match per PDF
        ↓
Fetch PDF metadata from SQLite for each match
        ↓
Calculate similarity % → sort descending
        ↓
Return results JSON
        ↓
SearchResultCard renders with similarity score
```

### Q&A flow
```
User types question → clicks Ask
        ↓
POST /api/semantic/ask { question: "..." }
        ↓
ollama.embeddings(question) → query vector
        ↓
ChromaDB.query() → top 3 most similar chunks
        ↓
Filter: remove chunks with distance > 0.5
        ↓
Build prompt: system rules + labelled chunks + question
        ↓
ollama.chat(llama3.2, prompt, temperature=0.1)
        ↓
LLM reads context, generates answer
        ↓
Return { answer, sources } JSON
        ↓
QAResultCard renders answer + source pill tags
```

---

## 15. File Reference

### Backend

| File | Purpose |
|---|---|
| `backend/main.py` | App entry point, lifespan, middleware, router mounting |
| `backend/core/config.py` | All paths and constants |
| `backend/db/database.py` | SQLite engine, init_db, get_session |
| `backend/models/pdf.py` | PDF table schema and API schemas |
| `backend/services/pdf_parser.py` | PyMuPDF text extraction and title detection |
| `backend/services/pdf_service.py` | Ingestion pipeline, CRUD, delete pipeline |
| `backend/services/search_service.py` | Keyword search, match counting, snippet extraction |
| `backend/services/embedding_service.py` | Chunking, Ollama embeddings, ChromaDB operations |
| `backend/services/qa_service.py` | RAG pipeline, prompt building, Llama 3.2 call |
| `backend/api/routes/pdfs.py` | Upload, list, get, preview, download, delete endpoints |
| `backend/api/routes/search.py` | Keyword search endpoint |
| `backend/api/routes/semantic.py` | Semantic search, Q&A, debug endpoints |

### Frontend

| File | Purpose |
|---|---|
| `src/App.jsx` | Root component, PDF list state, initial fetch |
| `src/pages/Library.jsx` | Main view, all search state, view switching |
| `src/components/UploadZone.jsx` | Drag-and-drop file upload |
| `src/components/SearchModeToggle.jsx` | Keyword / Semantic / Ask AI toggle |
| `src/components/SearchBar.jsx` | Search input form, mode-aware |
| `src/components/SortBar.jsx` | Sort pill buttons |
| `src/components/PDFCard.jsx` | Library grid card with preview/download/delete |
| `src/components/SearchResultCard.jsx` | Search result card with highlight, preview/download/delete |
| `src/components/QAResultCard.jsx` | AI answer display with source citations |
| `src/components/PreviewModal.jsx` | Full-screen PDF preview modal |
| `src/components/EmptyState.jsx` | Empty library placeholder |
| `src/constants/sortOptions.js` | Sort option arrays for library and search |

### Storage

| Path | Purpose |
|---|---|
| `storage/pdfs/` | Uploaded PDF files on disk |
| `storage/library.db` | SQLite database file |
| `storage/chroma/` | ChromaDB vector store folder |

