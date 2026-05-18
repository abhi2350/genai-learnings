export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
}

export interface UploadedFile {
  id: string
  filename: string
  chunk_count: string
  created_at: string
}
