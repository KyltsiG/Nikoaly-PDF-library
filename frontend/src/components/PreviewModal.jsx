import { useEffect } from "react";
import "./PreviewModal.css";

export default function PreviewModal({ pdf, onClose }) {
  const previewUrl = `http://127.0.0.1:8000/api/pdfs/${pdf.id}/preview`;

  useEffect(() => {
    const handleKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handleKey);
    // Cleanup removes the listener when the modal unmounts
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  useEffect(() => {
    // Prevent the library grid from scrolling behind the modal
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  return (
    // Clicking the overlay (outside the modal) closes it
    <div className="modal-overlay" onClick={onClose}>
      {/* stopPropagation prevents clicks inside the modal from reaching the overlay */}
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
            <button className="modal-close-btn" onClick={onClose} title="Close">✕</button>
          </div>
        </div>

        <div className="modal-body">
          {/* The browser's native PDF renderer activates when an iframe points to a PDF */}
          <iframe src={previewUrl} title={pdf.title} className="modal-iframe" />
        </div>

      </div>
    </div>
  );
}
