// Separated from SortBar.jsx to comply with Vite's fast refresh requirement —
// files that export React components should not also export plain constants

export const LIBRARY_SORT_OPTIONS = [
  { value: "date_desc", label: "Newest first" },
  { value: "date_asc",  label: "Oldest first" },
  { value: "name_asc",  label: "Name A–Z" },
  { value: "name_desc", label: "Name Z–A" },
];

export const SEARCH_SORT_OPTIONS = [
  { value: "relevance", label: "Most relevant" },
  { value: "date_desc", label: "Newest first" },
  { value: "date_asc",  label: "Oldest first" },
  { value: "name_asc",  label: "Name A–Z" },
  { value: "name_desc", label: "Name Z–A" },
];
