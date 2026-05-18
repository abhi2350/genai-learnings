import { useState } from 'react'

interface Props {
  onSend: (message: string) => void
  disabled: boolean
  placeholder?: string
}

export default function ChatInput({ onSend, disabled, placeholder = 'Type a message...' }: Props) {
  const [input, setInput] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || disabled) return
    onSend(input.trim())
    setInput('')
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as unknown as React.FormEvent)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 flex gap-2 items-end">
      <textarea
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className="flex-1 border border-gray-300 rounded-2xl px-4 py-2.5 text-sm outline-none focus:border-blue-500 disabled:opacity-50 resize-none"
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="bg-blue-600 text-white px-4 py-2.5 rounded-2xl text-sm hover:bg-blue-700 disabled:opacity-50 shrink-0"
      >
        {disabled ? '...' : 'Send'}
      </button>
    </form>
  )
}
