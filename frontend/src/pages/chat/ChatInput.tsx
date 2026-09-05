// src/pages/chat/ChatInput.tsx
import { useRef, useState } from 'react'
import { Send, Paperclip, Mic } from 'lucide-react'

interface ChatInputProps {
  onSend: (text: string) => void
  disabled?: boolean
}

export default function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleSend() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setValue(e.target.value)
    // Auto-grow textarea
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  return (
    <div
      style={{
        padding: '0.875rem 1rem',
        borderTop: '1px solid var(--border)',
        background: 'var(--panel)',
      }}
    >
      <div
        style={{
          maxWidth: 760,
          margin: '0 auto',
          display: 'flex',
          alignItems: 'flex-end',
          gap: '0.5rem',
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 10,
          padding: '0.5rem 0.5rem 0.5rem 0.875rem',
          transition: 'border-color 0.15s',
        }}
        onFocusCapture={(e) => {
          e.currentTarget.style.borderColor = 'var(--primary)'
          e.currentTarget.style.boxShadow = '0 0 0 3px rgba(26,107,74,0.10)'
        }}
        onBlurCapture={(e) => {
          e.currentTarget.style.borderColor = 'var(--border)'
          e.currentTarget.style.boxShadow = 'none'
        }}
      >
        {/* Attachment button */}
        <button
          type="button"
          title="Attach engineering file"
          onClick={() => fileInputRef.current?.click()}
          style={{
            flexShrink: 0,
            padding: '0.375rem',
            borderRadius: 6,
            border: 'none',
            background: 'transparent',
            color: 'var(--muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            transition: 'color 0.15s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--primary)' }}
          onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--muted)' }}
        >
          <Paperclip size={16} strokeWidth={2} />
        </button>
        <input ref={fileInputRef} type="file" style={{ display: 'none' }} accept=".pdf,.png,.jpg,.dwg" />

        {/* Text area */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask about your engineering documents, P&IDs, or knowledge base…"
          rows={1}
          style={{
            flex: 1,
            resize: 'none',
            border: 'none',
            outline: 'none',
            background: 'transparent',
            color: 'var(--text)',
            fontSize: '0.875rem',
            lineHeight: 1.55,
            fontFamily: 'inherit',
            overflowY: 'auto',
            maxHeight: 160,
            padding: '0.3125rem 0',
          }}
        />

        {/* Mic placeholder */}
        <button
          type="button"
          title="Voice input (coming soon)"
          disabled
          style={{
            flexShrink: 0,
            padding: '0.375rem',
            borderRadius: 6,
            border: 'none',
            background: 'transparent',
            color: 'var(--border)',
            cursor: 'not-allowed',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <Mic size={16} strokeWidth={2} />
        </button>

        {/* Send button */}
        <button
          type="button"
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          style={{
            flexShrink: 0,
            padding: '0.4375rem 0.75rem',
            borderRadius: 7,
            border: 'none',
            background: disabled || !value.trim() ? 'var(--border)' : 'var(--primary)',
            color: disabled || !value.trim() ? 'var(--muted)' : '#fff',
            cursor: disabled || !value.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem',
            fontSize: '0.8125rem',
            fontWeight: 500,
            transition: 'background 0.15s, transform 0.1s',
          }}
          onMouseEnter={(e) => {
            if (!disabled && value.trim()) {
              e.currentTarget.style.background = 'var(--primary-hover)'
              e.currentTarget.style.transform = 'translateY(-1px)'
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = disabled || !value.trim() ? 'var(--border)' : 'var(--primary)'
            e.currentTarget.style.transform = 'none'
          }}
        >
          <Send size={14} strokeWidth={2} />
          Send
        </button>
      </div>
      <p style={{ textAlign: 'center', fontSize: '0.6875rem', color: 'var(--muted)', marginTop: '0.4rem' }}>
        Press <strong>Enter</strong> to send · <strong>Shift+Enter</strong> for new line
      </p>
    </div>
  )
}
