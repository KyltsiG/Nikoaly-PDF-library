import { useState, useEffect } from "react";
import Library from "./pages/Library";
import "./App.css";

function App() {

  const [pdfs, setPdfs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPdfs = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/pdfs/");
      if (!res.ok) throw new Error("Failed to fetch library");
      const data = await res.json();
      setPdfs(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPdfs();
  }, []);

  return (
    <div className="app">
      <Library
        pdfs={pdfs}
        loading={loading}
        error={error}
        onRefresh={fetchPdfs}
      />
    </div>
  );
}

export default App;
