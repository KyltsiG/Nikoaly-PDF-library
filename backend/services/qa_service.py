import ollama
from sqlmodel import Session
from backend.services.embedding_service import semantic_search


def answer_question(session: Session, question: str) -> dict:
    """
    RAG (Retrieval-Augmented Generation) pipeline.
    Retrieves the most relevant document chunks, then asks the LLM to answer
    using only that context — keeping the response grounded in the user's library.
    """
    matches = semantic_search(question, n_results=3)

    if not matches:
        return {
            "answer": "I couldn't find any relevant information in your library to answer that question.",
            "sources": [],
        }

    # Filter out weak matches — distance > 0.5 means low semantic similarity
    # and including them tends to confuse the model with irrelevant content
    strong_matches = [m for m in matches if m["distance"] < 0.5]
    if not strong_matches:
        # Fall back to top 2 rather than returning nothing
        strong_matches = matches[:2]

    context_parts = []
    seen_pdf_ids = []
    sources = []

    for match in strong_matches:
        pdf_id = match["metadata"]["pdf_id"]
        title = match["metadata"]["title"]

        # Label each excerpt so the LLM knows which document it came from
        context_parts.append(f'Document: "{title}"\n{match["chunk"]}')

        if pdf_id not in seen_pdf_ids:
            seen_pdf_ids.append(pdf_id)
            sources.append({"pdf_id": pdf_id, "title": title})

    context = "\n\n---\n\n".join(context_parts)

    # Explicit rules in the prompt reduce hallucination — the model is
    # instructed to admit when it doesn't know rather than guess
    prompt = f"""You are a precise document assistant. Your only job is to answer the question using ONLY the document excerpts provided below.

Rules:
- Only use information explicitly stated in the excerpts below
- Always mention which document your answer comes from
- If the excerpts do not contain enough information, say: "The documents in your library do not contain enough information to answer this question."
- Never guess or use outside knowledge
- Keep your answer concise and direct

Document excerpts:
{context}

Question: {question}

Answer:"""

    # Low temperature keeps responses focused and deterministic —
    # high temperature would produce more creative but less accurate answers
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.1},
    )

    return {
        "answer": response["message"]["content"].strip(),
        "sources": sources,
    }
