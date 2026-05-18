import { useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import ChatWindow from './components/ChatWindow'
import ChatInput from './components/ChatInput'
import FileUpload from './components/FileUpload'
import { streamChat, streamGeneralChat, login, register } from './api/client'
import type { Message } from './types'

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [mode, setMode] = useState<'rag' | 'chat'>('rag')
  const [ragMessages, setRagMessages] = useState<Message[]>([])
  const [chatMessages, setChatMessages] = useState<Message[]>([])
  const [streaming, setStreaming] = useState(false)

  const messages = mode === 'rag' ? ragMessages : chatMessages
  const setMessages = mode === 'rag' ? setRagMessages : setChatMessages
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegistering, setIsRegistering] = useState(false)
  const [authError, setAuthError] = useState('')

  async function handleAuth(e: React.FormEvent) {
    e.preventDefault()
    setAuthError('')
    try {
      if (isRegistering) {
        await register(email, password)
      }
      const data = await login(email, password)
      localStorage.setItem('token', data.access_token)
      setToken(data.access_token)
    } catch {
      setAuthError(isRegistering ? 'Registration failed' : 'Invalid credentials')
    }
  }

  async function handleSend(question: string) {
    const history = messages
      .filter(m => !m.isStreaming)
      .map(m => ({ role: m.role, content: m.content }))

    const userMsg: Message = { id: uuidv4(), role: 'user', content: question }
    const assistantId = uuidv4()
    const assistantMsg: Message = { id: assistantId, role: 'assistant', content: '', isStreaming: true }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setStreaming(true)

    try {
      const res = mode === 'rag'
        ? await streamChat(question, history)
        : await streamGeneralChat(question, history)
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Request failed')
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let fullContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        for (const line of chunk.split('\n')) {
          if (line.startsWith('data: ')) {
            fullContent += line.slice(6)
            setMessages(prev => prev.map(m =>
              m.id === assistantId ? { ...m, content: fullContent } : m
            ))
          }
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error getting response.'
      setMessages(prev => prev.map(m =>
        m.id === assistantId ? { ...m, content: message, isStreaming: false } : m
      ))
    } finally {
      setMessages(prev => prev.map(m =>
        m.id === assistantId ? { ...m, isStreaming: false } : m
      ))
      setStreaming(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem('token')
    setToken(null)
    setMessages([])
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm">
          <div className="text-center mb-6">
            <div className="text-3xl mb-2">📚</div>
            <h1 className="text-xl font-bold text-gray-800">DocChat</h1>
            <p className="text-sm text-gray-500 mt-1">Chat with your documents</p>
          </div>
          <form onSubmit={handleAuth} className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-blue-500"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-blue-500"
            />
            {authError && <p className="text-red-500 text-sm">{authError}</p>}
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2.5 rounded-xl text-sm font-medium hover:bg-blue-700"
            >
              {isRegistering ? 'Create Account' : 'Sign In'}
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-4">
            {isRegistering ? 'Already have an account?' : "Don't have an account?"}
            <button
              onClick={() => { setIsRegistering(!isRegistering); setAuthError('') }}
              className="text-blue-600 ml-1 font-medium"
            >
              {isRegistering ? 'Sign in' : 'Register'}
            </button>
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg w-full max-w-4xl flex h-[88vh] overflow-hidden">

        {/* Sidebar — only visible in RAG mode */}
        {mode === 'rag' && (
          <div className="w-64 border-r border-gray-200 flex flex-col shrink-0">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">📚</span>
                <h1 className="font-bold text-gray-800 text-sm">DocChat</h1>
              </div>
              <button onClick={handleLogout} className="text-xs text-gray-400 hover:text-red-500 transition-colors">
                Logout
              </button>
            </div>
            <FileUpload />
          </div>
        )}

        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header with mode toggle */}
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex bg-gray-100 rounded-xl p-1 gap-1">
              <button
                onClick={() => setMode('rag')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  mode === 'rag'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                📄 RAG
              </button>
              <button
                onClick={() => setMode('chat')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  mode === 'chat'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                💬 Chat
              </button>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400">
                {mode === 'rag' ? 'Answers from your documents' : 'General AI assistant'}
              </span>
              {mode === 'chat' && (
                <button onClick={handleLogout} className="text-xs text-gray-400 hover:text-red-500 transition-colors">
                  Logout
                </button>
              )}
            </div>
          </div>

          <ChatWindow messages={messages} />
          <ChatInput
            onSend={handleSend}
            disabled={streaming}
            placeholder={mode === 'rag' ? 'Ask about your documents...' : 'Ask me anything...'}
          />
        </div>
      </div>
    </div>
  )
}
