const getToken = () => localStorage.getItem('token') ?? ''

const authHeaders = () => ({
  'Authorization': `Bearer ${getToken()}`,
  'Content-Type': 'application/json',
})

export async function login(email: string, password: string) {
  const res = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error('Invalid credentials')
  return res.json() as Promise<{ access_token: string }>
}

export async function register(email: string, password: string) {
  const res = await fetch('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error('Registration failed')
  return res.json()
}

export async function uploadPDF(file: File) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/rag/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${getToken()}` },
    body: form,
  })
  if (!res.ok) throw new Error('Upload failed')
  return res.json()
}

export async function getFiles() {
  const res = await fetch('/rag/files', { headers: authHeaders() })
  if (!res.ok) throw new Error('Failed to fetch files')
  return res.json()
}

export function streamChat(question: string, history: { role: string; content: string }[]): Promise<Response> {
  return fetch('/rag/chat', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ question, history }),
  })
}

export function streamGeneralChat(message: string, history: { role: string; content: string }[]): Promise<Response> {
  return fetch('/ai/chat/general', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ message, history }),
  })
}
