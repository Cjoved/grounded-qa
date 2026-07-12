const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// TODO (Week 1): uploadFile should send FormData, not JSON — adjust
// `request()` or add a separate helper for multipart uploads.
export function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  return fetch(`${API_BASE}/upload`, { method: "POST", body: formData }).then((res) => {
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  });
}

export function listDocuments() {
  return request("/documents");
}

export function askQuestion(question, topK = 5) {
  return request("/ask", {
    method: "POST",
    body: JSON.stringify({ question, top_k: topK }),
  });
}

export function runEval() {
  return request("/eval/run", { method: "POST" });
}

export function getEvalHistory() {
  return request("/eval/history");
}
