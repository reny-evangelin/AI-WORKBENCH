// src/pages/chat/ChatInput.tsx
import React, { useRef, useState } from 'react'
import { Send, Paperclip, Mic, X } from 'lucide-react'

interface ChatInputProps {
  onSend: (text: string, file?: File | null) => void
  disabled?: boolean
}

export default function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleSend() {
    const trimmed = value.trim()
    if ((!trimmed && !selectedFile) || disabled) return
    onSend(trimmed, selectedFile)
    setValue('')
    setSelectedFile(null)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
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

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
    }
  }

  function removeFile() {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const isSendDisabled = disabled || (!value.trim() && !selectedFile)

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
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 10,
          padding: '0.5rem 0.5rem 0.5rem 0.875rem',
          transition: 'border-color 0.15s',
          display: 'flex',
          flexDirection: 'column',
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
        {/* Selected file preview */}
        {selectedFile && (
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'var(--accent-bg)',
            padding: '0.25rem 0.5rem',
            borderRadius: '4px',
            marginBottom: '0.5rem',
            border: '1px solid var(--border)',
            alignSelf: 'flex-start',
            fontSize: '0.75rem',
            color: 'var(--text)'
          }}>
            <Paperclip size={12} />
            <span style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {selectedFile.name}
            </span>
            <button
              onClick={removeFile}
              style={{
                background: 'transparent', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', padding: '0.1rem',
                color: 'var(--muted)'
              }}
            >
              <X size={12} />
            </button>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}>
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
          <input ref={fileInputRef} onChange={handleFileChange} type="file" style={{ display: 'none' }} accept=".pdf,.png,.jpg,.jpeg,.bmp,.tiff,.webp,.dwg" />

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
            disabled={isSendDisabled}
            style={{
              flexShrink: 0,
              padding: '0.4375rem 0.75rem',
              borderRadius: 7,
              border: 'none',
              background: isSendDisabled ? 'var(--border)' : 'var(--primary)',
              color: isSendDisabled ? 'var(--muted)' : '#fff',
              cursor: isSendDisabled ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
              fontSize: '0.8125rem',
              fontWeight: 500,
              transition: 'background 0.15s, transform 0.1s',
            }}
            onMouseEnter={(e) => {
              if (!isSendDisabled) {
                e.currentTarget.style.background = 'var(--primary-hover)'
                e.currentTarget.style.transform = 'translateY(-1px)'
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = isSendDisabled ? 'var(--border)' : 'var(--primary)'
              e.currentTarget.style.transform = 'none'
            }}
          >
            <Send size={14} strokeWidth={2} />
            Send
          </button>
        </div>
      </div>
      <p style={{ textAlign: 'center', fontSize: '0.6875rem', color: 'var(--muted)', marginTop: '0.4rem' }}>
        Press <strong>Enter</strong> to send · <strong>Shift+Enter</strong> for new line
      </p>
    </div>
  )
}

