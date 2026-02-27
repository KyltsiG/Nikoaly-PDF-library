import { useState } from "react";
import PreviewModal from "./PreviewModal";
import "./PDFCard.css";

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric",
  });
}

export default function PDFCard({ pdf, onDelete }) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [previewing, setPreviewing] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await fetch(`http://127.0.0.1:8000/api/pdfs/${pdf.id}`, { method: "DELETE" });
      onDelete();
    } catch {
      // Reset UI state so the user can try again
      setDeleting(false);
      setConfirming(false);
    }
  };

  const handleDownload = (e) => {
    // Stop click from bubbling up to the card's onClick which opens the preview
    e.stopPropagation();
    window.open(`http://127.0.0.1:8000/api/pdfs/${pdf.id}/download`, "_blank");
  };

  return (
    <>
      <div
        className={`pdf-card ${deleting ? "deleting" : ""}`}
        onClick={() => !confirming && setPreviewing(true)}
      >
        <div className="pdf-card-icon">PDF</div>

        <div className="pdf-card-body">
          <h3 className="pdf-card-title" title={pdf.filename}>{pdf.filename}</h3>
          <div className="pdf-card-meta">
            <span>{pdf.page_count} page{pdf.page_count !== 1 ? "s" : ""}</span>
            <span className="pdf-card-dot">·</span>
            <span>{formatBytes(pdf.file_size_bytes)}</span>
            <span className="pdf-card-dot">·</span>
            <span>{formatDate(pdf.uploaded_at)}</span>
          </div>
        </div>

        {/* Stop action clicks from triggering the card's preview open */}
        <div className="pdf-card-actions" onClick={(e) => e.stopPropagation()}>
          {confirming ? (
            <div className="pdf-card-confirm">
              <span className="pdf-card-confirm-label">Delete?</span>
              <button className="pdf-card-btn danger" onClick={handleDelete} disabled={deleting}>
                {deleting ? "..." : "Yes"}
              </button>
              <button className="pdf-card-btn" onClick={() => setConfirming(false)}>
                No
              </button>
            </div>
          ) : (
            <div className="pdf-card-btns">
              <button className="pdf-card-action-btn" onClick={handleDownload} title="Download">
                ↓
              </button>
              <button className="pdf-card-action-btn delete" onClick={() => setConfirming(true)} title="Delete">
                ✕
              </button>
            </div>
          )}
        </div>
      </div>

      {previewing && (
        <PreviewModal pdf={pdf} onClose={() => setPreviewing(false)} />
      )}
    </>
  );
}
