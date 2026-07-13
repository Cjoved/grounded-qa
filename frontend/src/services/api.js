import supabase from './supabase'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

async function getAuthHeader() {
  if (!supabase) return {}
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}
}

async function request(path, options = {}) {
  const authHeader = await getAuthHeader()
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...authHeader },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export async function uploadFile(file) {
  const authHeader = await getAuthHeader()
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
    headers: authHeader,
  })
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
  return res.json()
}

export function listDocuments() {
  return request('/documents')
}

export function askQuestion(question, topK = 5) {
  return request('/ask', {
    method: 'POST',
    body: JSON.stringify({ question, top_k: topK }),
  })
}

export function runEval() {
  return request('/eval/run', { method: 'POST' })
}

export function getEvalHistory() {
  return request('/eval/history')
}

export function deleteDocument(documentId) {
  return request(`/documents/${documentId}`, { method: 'DELETE' })
}