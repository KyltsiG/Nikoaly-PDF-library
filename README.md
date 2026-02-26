# Nikoäly PDF Library

A personal, fully local PDF library with AI-powered search. Upload your documents, have them automatically analyzed and indexed, then find anything across your entire collection using keyword search, semantic search, or natural language Q&A — all running on your own machine with no internet required and no data leaving your computer.

---

## What it does

Most PDF tools make you remember which file contains what. This library lets you search by **meaning**, not just filename. Upload a research paper, a textbook, or a scanned document — the application extracts the full text, indexes it, and makes it instantly searchable. In later phases, an on-device AI model answers questions directly from your documents, citing the exact source.

---

## Tech Stack

### Backend
| Technology | Role |
|---|---|
| **Python 3.12** | Core backend language |
| **FastAPI** | REST API framework — handles all HTTP endpoints, validation, and routing |
| **SQLModel** | Database ORM — bridges Python models and SQLite with type safety |
| **SQLite** | Embedded database — stores all PDF metadata and extracted text in a single local file |
| **PyMuPDF** | PDF parsing — extracts text content and metadata from uploaded documents |
| **Uvicorn** | ASGI server — runs the FastAPI application locally |

### Frontend
| Technology | Role |
|---|---|
| **React 18** | UI framework — component-based interface |
| **Vite** | Build tool and dev server |
| **Plain CSS** | Custom styling with CSS variables — no UI framework dependency |

### Planned (Phase 3+)
| Technology | Role |
|---|---|
| **Ollama** | Local LLM runtime — runs AI models entirely on device |
| **nomic-embed-text** | Embedding model — converts text to vectors for semantic search |
| **Llama 3** | Language model — powers natural language Q&A over documents |
| **ChromaDB** | Vector database — stores and queries embeddings for similarity search |

---

## Features

**Phase 1 — complete**
- Upload PDFs via drag-and-drop or file browser
- Automatic text extraction and metadata parsing (title, page count, file size)
- Full text stored locally in SQLite for search
- View, browse, and delete documents from the library
- Dark-themed React UI

**Phase 2 — in progress**
- Keyword search using SQLite FTS5 full-text search
- Relevant excerpt highlighting in search results

**Phase 3 — planned**
- Semantic search using local embeddings (finds meaning, not just keywords)
- Natural language Q&A powered by local LLM (RAG pipeline)
- All AI runs fully on-device via Ollama

---

## Architecture

```
[ React Frontend — localhost:5173 ]
             ↕  HTTP / REST
[ FastAPI Backend — localhost:8000 ]
        ↕                  ↕
[ SQLite DB ]       [ Local Disk ]
  metadata +          storage/pdfs/
  full text           (PDF files)
        ↕
[ PyMuPDF Parser ]
  text extraction
  on upload
```

---

## Getting Started

### Prerequisites
- Python 3.12
- Node.js 18+

### Backend

```bash
# Create and activate virtual environment
py -3.12 -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn backend.main:app --reload
```

API available at `http://localhost:8000`  
Interactive API docs at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:5173`

---

## Project Structure

```
nikoaly-pdf-library/
├── backend/
│   ├── main.py                 # FastAPI app, lifespan, middleware
│   ├── core/
│   │   └── config.py           # Paths, constants, settings
│   ├── db/
│   │   └── database.py         # SQLite engine and session management
│   ├── models/
│   │   └── pdf.py              # Database models and API schemas
│   ├── services/
│   │   ├── pdf_parser.py       # PyMuPDF text extraction
│   │   └── pdf_service.py      # Ingestion pipeline and CRUD operations
│   └── api/routes/
│       └── pdfs.py             # Upload, list, get, delete endpoints
├── frontend/
│   └── src/
│       ├── App.jsx             # Root component, data fetching
│       ├── pages/
│       │   └── Library.jsx     # Main library view
│       └── components/
│           ├── UploadZone.jsx  # Drag-and-drop upload
│           ├── PDFCard.jsx     # Individual document card
│           └── EmptyState.jsx  # Empty library placeholder
├── storage/
│   ├── pdfs/                   # Uploaded PDF files (gitignored)
│   └── library.db              # SQLite database (gitignored)
├── tests/
│   └── test_phase1.py
├── requirements.txt
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/pdfs/upload` | Upload and ingest a PDF |
| `GET` | `/api/pdfs/` | List all PDFs |
| `GET` | `/api/pdfs/{id}` | Get a single PDF by ID |
| `DELETE` | `/api/pdfs/{id}` | Delete a PDF |

---

## Design Principles

**Fully local** — no cloud services, no API keys, no subscriptions. Every file, database, and AI model runs on your own hardware.

**Privacy first** — your documents never leave your machine. Nothing is sent to external servers at any point.

**Incremental complexity** — built phase by phase so each stage is fully functional before the next is added. The app works at every phase, not just at the end.

---

*Built with Python, FastAPI, React, and a lot of SQLite.*
