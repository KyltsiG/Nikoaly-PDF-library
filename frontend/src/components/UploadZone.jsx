import { useState, useRef } from "react";
import "./UploadZone.css";

export default function UploadZone({ onUploadSuccess }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null); // { type: "success"|"error", text }
  const inputRef = useRef(null);

  const uploadFile = async (file) => {
    if (!file || file.type !== "application/pdf") {
      setMessage({ type: "error", text: "Only PDF files are accepted." });
      return;
    }

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/pdfs/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed.");
      }

      const data = await res.json();
      setMessage({ type: "success", text: `"${data.filename}" added to library.` });
      onUploadSuccess();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    uploadFile(file);
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    uploadFile(file);
    e.target.value = "";
  };

  return (
    <div className="upload-wrapper">
      <div
        className={`upload-zone ${dragging ? "dragging" : ""} ${uploading ? "uploading" : ""}`}
        onClick={() => !uploading && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          style={{ display: "none" }}
          onChange={handleFileInput}
        />

        {uploading ? (
          <>
            <div className="upload-spinner" />
            <p className="upload-label">Uploading...</p>
          </>
        ) : (
          <>
            <span className="upload-icon">↑</span>
            <p className="upload-label">
              Drop a PDF here, or <span className="upload-link">browse</span>
            </p>
            <p className="upload-hint">Up to 50MB</p>
          </>
        )}
      </div>

      {message && (
        <p className={`upload-message ${message.type}`}>{message.text}</p>
      )}
    </div>
  );
}