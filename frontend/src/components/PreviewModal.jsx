import { useEffect } from "react";
import "./PreviewModal.css";

export default function PreviewModal({ pdf, onClose }) {
  const previewUrl = `http://127.0.0.1:8000/api/pdfs/${pdf.id}/preview`;

  // Close on Escape key
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  // Prevent background scroll while modal is open
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>

        <div className="modal-header">
          <span className="modal-title" title={pdf.title}>{pdf.title}</span>
          <div className="modal-header-actions">
            <a
              className="modal-download-btn"
              href={`http://127.0.0.1:8000/api/pdfs/${pdf.id}/download`}
              download={pdf.filename}
            >
              ↓ Download
            </a>
            <button className="modal-close-btn" onClick={onClose} title="Close">
              ✕
            </button>
          </div>
        </div>

        <div className="modal-body">
          <iframe
            src={previewUrl}
            title={pdf.title}
            className="modal-iframe"
          />
        </div>

      </div>
    </div>
  );
}