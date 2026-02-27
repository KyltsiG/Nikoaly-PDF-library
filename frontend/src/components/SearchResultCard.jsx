import { useState } from "react";
import PreviewModal from "./PreviewModal";
import "./SearchResultCard.css";

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function highlightMatch(text, query) {
  if (!text || !query) return text;
  // Escape special regex characters in the query before building the pattern
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  const parts = text.split(regex);
  return parts.map((part, i) =>
    regex.test(part) ? <mark key={i} className="search-highlight">{part}</mark> : part
  );
}

export default function SearchResultCard({ result, query, onDelete }) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [previewing, setPreviewing] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await fetch(`http://127.0.0.1:8000/api/pdfs/${result.id}`, { method: "DELETE" });
      onDelete();
    } catch {
      setDeleting(false);
      setConfirming(false);
    }
  };

  const handleDownload = (e) => {
    e.stopPropagation();
    window.open(`http://127.0.0.1:8000/api/pdfs/${result.id}/download`, "_blank");
  };

  return (
    <>
      <div
        className={`result-card ${deleting ? "deleting" : ""}`}
        onClick={() => !confirming && setPreviewing(true)}
      >
        <div className="result-card-header">
          <div className="result-card-icon">PDF</div>
          <div className="result-card-meta">
            <h3 className="result-card-title">
              {highlightMatch(result.title, query)}
            </h3>
            <div className="result-card-info-row">
              <span className="result-card-info">
                {result.page_count} page{result.page_count !== 1 ? "s" : ""}
                <span className="result-dot">·</span>
                {formatBytes(result.file_size_bytes)}
                {result.match_page && (
                  <>
                    <span className="result-dot">·</span>
                    <span className="result-match-page">p. {result.match_page}</span>
                  </>
                )}
              </span>
              <div className="result-card-badges">
                {/* Show match count for keyword results, similarity % for semantic */}
                {result.matches !== undefined && (
                  <span className="result-card-matches">
                    {result.matches} match{result.matches !== 1 ? "es" : ""}
                  </span>
                )}
                {result.similarity !== undefined && (
                  <span className="result-card-similarity">
                    {result.similarity}% match
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {result.snippet && (
          <p className="result-card-snippet">
            {highlightMatch(result.snippet, query)}
          </p>
        )}

        <div className="result-card-actions" onClick={(e) => e.stopPropagation()}>
          {confirming ? (
            <div className="result-card-confirm">
              <span className="result-card-confirm-label">Delete?</span>
              <button className="result-card-btn danger" onClick={handleDelete} disabled={deleting}>
                {deleting ? "..." : "Yes"}
              </button>
              <button className="result-card-btn" onClick={() => setConfirming(false)}>No</button>
            </div>
          ) : (
            <div className="result-card-btns">
              <button className="result-card-action-btn" onClick={handleDownload} title="Download">↓</button>
              <button className="result-card-action-btn delete" onClick={() => setConfirming(true)} title="Delete">✕</button>
            </div>
          )}
        </div>
      </div>

      {previewing && (
        <PreviewModal pdf={result} onClose={() => setPreviewing(false)} />
      )}
    </>
  );
}
