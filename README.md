# Nikoäly PDF Library

A fully local, AI-powered PDF library. Upload your documents, have them automatically analyzed and indexed, then find anything across your entire collection using keyword search, semantic search, or natural language Q&A — all running on your own machine with no internet required and no data leaving your computer.

---

## Features

### Phase 1 — Library
- Upload PDFs via drag-and-drop or file browser
- Automatic text extraction and metadata parsing (title, page count, file size)
- Browse, preview, and delete documents
- Download any PDF directly from the library
- Dark-themed React UI

### Phase 2 — Keyword Search
- Full-text keyword search across all documents
- Match count per document — results ranked by relevance
- Highlighted excerpts showing where the match was found
- Sort results by relevance, date, or name

### Phase 3 — AI Search
- **Semantic search** — finds documents by meaning, not just exact words
- **Ask AI (Q&A)** — ask a natural language question, get a direct answer citing your documents
- All AI runs fully on-device via Ollama — no API keys, no internet required

---

## Tech Stack

### Backend
| Technology | Role |
|---|---|
| **Python 3.12** | Core backend language |
| **FastAPI** | REST API framework |
| **SQLModel** | Database ORM — bridges Python models and SQLite |
| **SQLite** | Stores PDF metadata and extracted text |
| **PyMuPDF** | PDF parsing and text extraction |
| **ChromaDB** | Vector database for semantic search |
| **Ollama** | Local AI runtime — runs models on-device |
| **nomic-embed-text** | Embedding model for semantic search |
| **Llama 3.2** | Language model for Q&A |
| **Uvicorn** | ASGI server |

### Frontend
| Technology | Role |
|---|---|
| **React 18** | UI framework |
| **Vite** | Build tool and dev server |
| **Plain CSS** | Custom styling with CSS variables |

---

## Architecture

```
[ React Frontend — localhost:5173 ]
             ↕  HTTP / REST
[ FastAPI Backend — localhost:8000 ]
      ↕                    ↕
[ SQLite DB ]        [ Local Disk ]
  metadata +           storage/pdfs/
  full text            (PDF files)
      ↕
[ ChromaDB ]
  vector embeddings
  per page chunk
      ↕
[ Ollama ]
  nomic-embed-text (embeddings)
  llama3.2 (Q&A)
```

---

## Prerequisites

- **Python 3.12**
- **Node.js 18+** 
- **Ollama**
### Pull the required AI models

After installing Ollama, open a terminal and run:

```bash
ollama pull nomic-embed-text
ollama pull llama3.2
```

This downloads ~2.5GB total. Only needs to be done once.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/KyltsiG/Nikoaly-PDF-library.git
cd Nikoaly-PDF-library
```

### 2. Backend setup

```bash
# Create and activate virtual environment
py -3.12 -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Start Ollama

```bash
ollama serve
```

Keep this running in a separate terminal.

### 4. Start the backend

```bash
python -m uvicorn backend.main:app --reload
```

API available at `http://localhost:8000`  
Interactive API docs at `http://localhost:8000/docs`

### 5. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:5173`

---


## How It Works

**Upload** — when a PDF is uploaded, PyMuPDF extracts the full text. The text is stored in SQLite for keyword search. It is also split into 200-word chunks per page and each chunk is embedded by `nomic-embed-text` via Ollama, with the page number stored in metadata. The vectors are saved in ChromaDB.

**Keyword search** — searches SQLite for exact text matches, counts occurrences, extracts a snippet around the first match, and identifies which page the match was found on.

**Semantic search** — embeds the query using `nomic-embed-text`, queries ChromaDB for the most similar vectors using cosine similarity, and returns the matching PDFs ranked by similarity score with the matching page number.

**Ask AI** — embeds the question, retrieves the top 3 most relevant chunks from ChromaDB, builds a strict prompt with those chunks as context, and calls `llama3.2` at low temperature to generate a focused answer citing the source documents.

---

## Design Principles

**Fully local** — no cloud services, no API keys, no subscriptions. Every file, database, and AI model runs on your own hardware.

**Privacy first** — your documents never leave your machine at any point.

**Incremental complexity** — built phase by phase so the app works at every stage, not just at the end.

---

*Built with Python, FastAPI, React, SQLite, ChromaDB, and Ollama.*