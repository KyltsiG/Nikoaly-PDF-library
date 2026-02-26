import "./SortBar.css";

export default function SortBar({ sortBy, onChange, options }) {
  return (
    <div className="sort-bar">
      <span className="sort-label">Sort by</span>
      <div className="sort-options">
        {options.map((opt) => (
          <button
            key={opt.value}
            className={`sort-btn ${sortBy === opt.value ? "active" : ""}`}
            onClick={() => onChange(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}