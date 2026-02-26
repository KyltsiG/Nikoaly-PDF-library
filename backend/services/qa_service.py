import ollama
from sqlmodel import Session
from backend.services.embedding_service import semantic_search


def answer_question(session: Session, question: str) -> dict:
    """
    RAG pipeline:
    1. Find the most relevant chunks for the question
    2. Filter out low-quality matches by distance threshold
    3. Build a strict context prompt
    4. Ask Llama 3.2 to answer using only that context
    5. Return answer + source citations
    """
    # Step 1 — retrieve top 3 most relevant chunks
    matches = semantic_search(question, n_results=3)

    if not matches:
        return {
            "answer": "I couldn't find any relevant information in your library to answer that question.",
            "sources": [],
        }

    # Step 2 — filter out weak matches (distance > 0.5 means low similarity)
    strong_matches = [m for m in matches if m["distance"] < 0.5]
    if not strong_matches:
        strong_matches = matches[:2]  # fallback to top 2 if all are weak

    # Step 3 — build context, track which PDFs were used
    context_parts = []
    seen_pdf_ids = []
    sources = []

    for match in strong_matches:
        pdf_id = match["metadata"]["pdf_id"]
        title = match["metadata"]["title"]
        chunk = match["chunk"]

        context_parts.append(f'Document: "{title}"\n{chunk}')

        if pdf_id not in seen_pdf_ids:
            seen_pdf_ids.append(pdf_id)
            sources.append({
                "pdf_id": pdf_id,
                "title": title,
            })

    context = "\n\n---\n\n".join(context_parts)

    # Step 4 — strict prompt that forces the model to stay on topic
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

    # Step 5 — call Llama 3.2
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 0.1,  # low temperature = more focused, less creative
        }
    )

    answer = response["message"]["content"].strip()

    return {
        "answer": answer,
        "sources": sources,
    }