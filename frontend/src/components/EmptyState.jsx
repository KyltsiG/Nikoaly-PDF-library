import "./EmptyState.css";

// Simple component to show when library is empty

export default function EmptyState() {
  return (
    <div className="empty-state">
      <span className="empty-icon">⬡</span>
      <p className="empty-title">Your library is empty</p>
      <p className="empty-subtitle">Upload a PDF above to get started</p>
    </div>
  );
}
