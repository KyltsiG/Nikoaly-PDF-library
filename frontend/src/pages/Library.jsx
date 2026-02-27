import { useState, useMemo } from "react";
import UploadZone from "../components/UploadZone";
import PDFCard from "../components/PDFCard";
import SearchBar from "../components/SearchBar";
import SearchModeToggle from "../components/SearchModeToggle";
import SearchResultCard from "../components/SearchResultCard";
import QAResultCard from "../components/QAResultCard";
import SortBar from "../components/SortBar";
import EmptyState from "../components/EmptyState";
import { LIBRARY_SORT_OPTIONS, SEARCH_SORT_OPTIONS } from "../constants/sortOptions";
import "./Library.css";

function sortItems(items, sortBy) {
  // Spread to avoid mutating the original state array — sort() is in-place
  return [...items].sort((a, b) => {
    switch (sortBy) {
      case "relevance":
        // Works for both keyword (matches) and semantic (similarity) results
        return (b.matches ?? b.similarity ?? 0) - (a.matches ?? a.similarity ?? 0);
      case "date_desc": return new Date(b.uploaded_at) - new Date(a.uploaded_at);
      case "date_asc":  return new Date(a.uploaded_at) - new Date(b.uploaded_at);
      case "name_asc":  return a.title.localeCompare(b.title);
      case "name_desc": return b.title.localeCompare(a.title);
      default: return 0;
    }
  });
}

export default function Library({ pdfs, loading, error, onRefresh }) {
  const [searchMode, setSearchMode] = useState("keyword");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [qaResult, setQaResult] = useState(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [librarySortBy, setLibrarySortBy] = useState("date_desc");
  const [searchSortBy, setSearchSortBy] = useState("relevance");

  // useMemo avoids re-sorting on every render — recalculates only when
  // the source array or sort key actually changes
  const sortedPdfs    = useMemo(() => sortItems(pdfs,    librarySortBy), [pdfs,    librarySortBy]);
  const sortedResults = useMemo(() => sortItems(results, searchSortBy),  [results, searchSortBy]);

  const handleModeChange = (newMode) => {
    setSearchMode(newMode);
    // Clear results when switching modes so stale results don't show
    handleClear();
  };

  const handleSearch = async (q) => {
    setSearching(true);
    setSearchError(null);
    setQuery(q);
    setQaResult(null);
    setSearchSortBy("relevance");

    try {
      if (searchMode === "keyword") {
        const res = await fetch(`http://127.0.0.1:8000/api/search/?q=${encodeURIComponent(q)}`);
        if (!res.ok) throw new Error("Search failed.");
        const data = await res.json();
        setResults(data.results);

      } else if (searchMode === "semantic") {
        const res = await fetch(`http://127.0.0.1:8000/api/semantic/search?q=${encodeURIComponent(q)}`);
        if (!res.ok) throw new Error("Semantic search failed.");
        const data = await res.json();
        setResults(data.results);

      } else if (searchMode === "qa") {
        const res = await fetch("http://127.0.0.1:8000/api/semantic/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q }),
        });
        if (!res.ok) throw new Error("Q&A failed.");
        setQaResult(await res.json());
        setResults([]);
      }

      setHasSearched(true);
    } catch (err) {
      setSearchError(err.message);
    } finally {
      setSearching(false);
    }
  };

  const handleClear = () => {
    setQuery("");
    setResults([]);
    setQaResult(null);
    setHasSearched(false);
    setSearchError(null);
    setSearchSortBy("relevance");
  };

  // hasSearched stays true after the request completes, keeping results visible
  // searching is only true while the request is in flight
  const isSearchMode = hasSearched || searching;

  // Sort bar is irrelevant for Q&A — there's only one answer card
  const showSortBar = searchMode !== "qa" && results.length > 0 && !searching;

  return (
    <div className="library">
      <header className="library-header">
        <div className="library-header-inner">
          <div className="library-title-group">
            <span className="library-logo">(⊙ _ ⊙ )</span>
            <h1 className="library-title">Nikoäly PDF Library</h1>
          </div>
          <p className="library-count">
            {loading ? "Loading..." : `${pdfs.length} document${pdfs.length !== 1 ? "s" : ""}`}
          </p>
        </div>
      </header>

      <main className="library-main">
        <UploadZone onUploadSuccess={onRefresh} />

        <div className="search-block">
          <SearchModeToggle mode={searchMode} onChange={handleModeChange} />
          <SearchBar
            onSearch={handleSearch}
            onClear={handleClear}
            isSearching={searching}
            mode={searchMode}
          />
        </div>

        <section className="library-section">

          {/* ── Search / Q&A results view ── */}
          {isSearchMode && (
            <>
              <div className="search-results-header">
                {searching ? (
                  <span className="search-status">
                    {searchMode === "qa" ? "Thinking..." : "Searching..."}
                  </span>
                ) : (
                  <span className="search-status">
                    {searchMode === "qa" && qaResult
                      ? `Answer for "${query}"`
                      : results.length > 0
                        ? `${results.length} result${results.length !== 1 ? "s" : ""} for "${query}"`
                        : `No results for "${query}"`}
                  </span>
                )}
                <button className="search-back-btn" onClick={handleClear}>
                  ← Back to library
                </button>
              </div>

              {showSortBar && (
                <SortBar sortBy={searchSortBy} onChange={setSearchSortBy} options={SEARCH_SORT_OPTIONS} />
              )}

              {searchError && <div className="library-error">{searchError}</div>}

              {!searching && searchMode === "qa" && qaResult && (
                <QAResultCard answer={qaResult.answer} sources={qaResult.sources} />
              )}

              {!searching && searchMode !== "qa" && results.length === 0 && !searchError && (
                <div className="search-empty">
                  <p>No documents matched your search.</p>
                  <p>Try different keywords or switch search mode.</p>
                </div>
              )}

              {!searching && searchMode !== "qa" && results.length > 0 && (
                <div className="results-list">
                  {sortedResults.map((result) => (
                    <SearchResultCard
                      key={result.id}
                      result={result}
                      query={query}
                      onDelete={onRefresh}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {/* ── Library view ── */}
          {!isSearchMode && (
            <>
              {error && (
                <div className="library-error">
                  Could not connect to server. Make sure the backend is running.
                </div>
              )}
              {loading && !error && <div className="library-loading"><div className="spinner" /></div>}
              {!loading && !error && pdfs.length === 0 && <EmptyState />}
              {!loading && !error && pdfs.length > 0 && (
                <>
                  <SortBar sortBy={librarySortBy} onChange={setLibrarySortBy} options={LIBRARY_SORT_OPTIONS} />
                  <div className="pdf-grid">
                    {sortedPdfs.map((pdf) => (
                      <PDFCard key={pdf.id} pdf={pdf} onDelete={onRefresh} />
                    ))}
                  </div>
                </>
              )}
            </>
          )}

        </section>
      </main>
    </div>
  );
}
