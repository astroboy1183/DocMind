import { useState } from "react";

const API = "http://localhost:8000";

export default function App() {
  const [query, setQuery] = useState("");
  const [jobs, setJobs] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function submitQuery(e) {
    if (e) e.preventDefault();
    const q = query.trim();
    if (!q || submitting) return;

    setSubmitting(true);
    setError("");
    console.log("[submit] →", q);

    try {
      const res = await fetch(`${API}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      });

      console.log("[submit] response status:", res.status);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      }

      const data = await res.json();
      console.log("[submit] job id:", data.job_id);

      const newJob = { id: data.job_id, query: q, status: "pending", result: null };
      setJobs((prev) => [newJob, ...prev]);
      setQuery("");
      pollResult(data.job_id);
    } catch (err) {
      console.error("[submit] failed:", err);
      setError(err.message || "Network error — is the server running on :8000?");
    } finally {
      setSubmitting(false);
    }
  }

  async function pollResult(jobId) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API}/result/${jobId}`);
        if (!res.ok) {
          console.warn(`[poll ${jobId}] HTTP ${res.status}`);
          return;
        }
        const data = await res.json();

        if (data.status === "completed" || data.status === "failed") {
          clearInterval(interval);
          setJobs((prev) =>
            prev.map((job) =>
              job.id === jobId
                ? { ...job, status: data.status, result: data.result }
                : job
            )
          );
        }
      } catch (err) {
        console.error(`[poll ${jobId}] error:`, err);
      }
    }, 1500);
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>RAG Query</h1>
      <p style={styles.subtitle}>Node.js Guide — Ask anything</p>

      <form onSubmit={submitQuery} style={styles.inputRow}>
        <input
          style={styles.input}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask something about Node.js..."
          disabled={submitting}
          autoFocus
        />
        <button
          type="submit"
          style={{ ...styles.button, opacity: submitting ? 0.6 : 1 }}
          disabled={submitting}
        >
          {submitting ? "Sending..." : "Submit"}
        </button>
      </form>

      {error && <div style={styles.error}>{error}</div>}

      <div style={styles.jobList}>
        {jobs.map((job) => (
          <div key={job.id} style={styles.card}>
            <div style={styles.cardHeader}>
              <span style={styles.queryText}>{job.query}</span>
              <span style={{ ...styles.badge, ...statusColor(job.status) }}>
                {job.status}
              </span>
            </div>
            {job.result && <p style={styles.result}>{job.result}</p>}
            {job.status === "pending" && (
              <p style={styles.pending}>Processing...</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function statusColor(status) {
  return (
    {
      completed: { background: "#d1fae5", color: "#065f46" },
      pending: { background: "#fef9c3", color: "#854d0e" },
      failed: { background: "#fee2e2", color: "#991b1b" },
    }[status] || {}
  );
}

const styles = {
  container: { maxWidth: 720, margin: "40px auto", padding: "0 20px", fontFamily: "sans-serif" },
  title: { fontSize: 28, fontWeight: 700, marginBottom: 4 },
  subtitle: { color: "#6b7280", marginBottom: 24 },
  inputRow: { display: "flex", gap: 8, marginBottom: 16 },
  input: { flex: 1, padding: "10px 14px", fontSize: 15, border: "1px solid #d1d5db", borderRadius: 8, outline: "none" },
  button: { padding: "10px 20px", fontSize: 15, background: "#2563eb", color: "#fff", border: "none", borderRadius: 8, cursor: "pointer" },
  error: { padding: "10px 14px", marginBottom: 16, background: "#fee2e2", color: "#991b1b", borderRadius: 8, fontSize: 14 },
  jobList: { display: "flex", flexDirection: "column", gap: 16 },
  card: { border: "1px solid #e5e7eb", borderRadius: 10, padding: 16 },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  queryText: { fontWeight: 600, fontSize: 15 },
  badge: { fontSize: 12, fontWeight: 600, padding: "2px 10px", borderRadius: 999 },
  result: { fontSize: 14, color: "#374151", lineHeight: 1.6, margin: 0 },
  pending: { fontSize: 13, color: "#9ca3af", margin: 0 },
};
