import "./QAResultCard.css";

export default function QAResultCard({ answer, sources }) {
  return (
    <div className="qa-card">
      <div className="qa-card-header">
        <span className="qa-card-icon">?</span>
        <span className="qa-card-label">AI Answer</span>
      </div>

      <p className="qa-card-answer">{answer}</p>

      {sources && sources.length > 0 && (
        <div className="qa-card-sources">
          <span className="qa-sources-label">Sources</span>
          <div className="qa-sources-list">
            {sources.map((source) => (
              <span key={source.pdf_id} className="qa-source-tag">
                {source.title}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
