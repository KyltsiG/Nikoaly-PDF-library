import "./SearchModeToggle.css";

const MODES = [
  { value: "keyword",  label: "Keyword",  icon: "#" },
  { value: "semantic", label: "Semantic", icon: "∿" },
  { value: "qa",       label: "Ask AI",   icon: "?" },
];

export default function SearchModeToggle({ mode, onChange }) {
  return (
    <div className="mode-toggle">
      {MODES.map((m) => (
        <button
          key={m.value}
          className={`mode-btn ${mode === m.value ? "active" : ""}`}
          onClick={() => onChange(m.value)}
        >
          <span className="mode-icon">{m.icon}</span>
          {m.label}
        </button>
      ))}
    </div>
  );
}
