// src/pages/chat/ChatMessage.tsx
import { Bot, User } from 'lucide-react'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatMessageProps {
  message: Message
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        gap: '0.625rem',
        marginBottom: '1.25rem',
        animation: 'fadeIn 0.18s ease',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          flexShrink: 0,
          width: 32,
          height: 32,
          borderRadius: '50%',
          background: isUser ? 'var(--primary)' : 'var(--accent-bg)',
          border: isUser ? 'none' : '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {isUser ? (
          <User size={15} color="#fff" strokeWidth={2} />
        ) : (
          <Bot size={15} color="var(--primary)" strokeWidth={2} />
        )}
      </div>

      {/* Bubble + timestamp */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
          maxWidth: '72%',
        }}
      >
        <div
          style={{
            padding: '0.75rem 1rem',
            borderRadius: isUser ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
            background: isUser ? 'var(--primary)' : 'var(--panel)',
            color: isUser ? '#fff' : 'var(--text)',
            border: isUser ? 'none' : '1px solid var(--border)',
            fontSize: '0.875rem',
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {message.content}
        </div>
        <span
          style={{
            fontSize: '0.6875rem',
            color: 'var(--muted)',
            marginTop: '0.25rem',
            paddingLeft: isUser ? 0 : '0.25rem',
            paddingRight: isUser ? '0.25rem' : 0,
          }}
        >
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  )
}
