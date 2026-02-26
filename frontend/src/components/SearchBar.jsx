import { useState, useRef } from "react";
import "./SearchBar.css";

const PLACEHOLDERS = {
  keyword:  "Search by keyword...",
  semantic: "Search by meaning...",
  qa:       "Ask a question about your documents...",
};

const BUTTON_LABELS = {
  keyword:  "Search",
  semantic: "Search",
  qa:       "Ask",
};

export default function SearchBar({ onSearch, onClear, isSearching, mode }) {
  const [value, setValue] = useState("");
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim()) onSearch(value.trim());
  };

  const handleClear = () => {
    setValue("");
    onClear();
    inputRef.current.focus();
  };

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <span className="search-icon">⌕</span>
      <input
        ref={inputRef}
        className="search-input"
        type="text"
        placeholder={PLACEHOLDERS[mode] ?? PLACEHOLDERS.keyword}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        autoComplete="off"
        spellCheck="false"
      />
      {value && (
        <button
          type="button"
          className="search-clear"
          onClick={handleClear}
          title="Clear"
        >
          ✕
        </button>
      )}
      <button
        type="submit"
        className="search-submit"
        disabled={!value.trim() || isSearching}
      >
        {isSearching ? "..." : (BUTTON_LABELS[mode] ?? "Search")}
      </button>
    </form>
  );
}
