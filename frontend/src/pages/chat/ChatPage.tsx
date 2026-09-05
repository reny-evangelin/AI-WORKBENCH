// src/pages/chat/ChatPage.tsx
import { useRef, useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { Bot, Cpu } from 'lucide-react'
import ChatMessage, { type Message } from './ChatMessage'
import ChatInput from './ChatInput'
import SuggestedPrompts from './SuggestedPrompts'
import { sendChatMessage } from '../../services/api'

const WELCOME: Message = {
  id: 'welcome',
  role: 'assistant',
  content:
    "Hello! I'm your AI Engineering Assistant. I can help you analyze P&ID diagrams, search the knowledge base, review engineering documents, and generate structured reports.\n\nWhat would you like to work on today?",
  timestamp: new Date(),
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.625rem', marginBottom: '1.25rem' }}>
      <div
        style={{
          flexShrink: 0, width: 32, height: 32, borderRadius: '50%',
          background: 'var(--accent-bg)', border: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
      >
        <Bot size={15} color="var(--primary)" strokeWidth={2} />
      </div>
      <div
        style={{
          padding: '0.75rem 1rem',
          borderRadius: '12px 12px 12px 4px',
          background: 'var(--panel)',
          border: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.3rem',
        }}
      >
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: 'var(--muted)',
              display: 'inline-block',
              animation: `chatDot 1.2s ease-in-out ${i * 0.2}s infinite`,
            }}
          />
        ))}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const location = useLocation()
  const [messages, setMessages] = useState<Message[]>([WELCOME])
  const [isTyping, setIsTyping] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Reset conversation when "New Chat" navigates with ?new=<timestamp>
  useEffect(() => {
    if (location.search.includes('new=')) {
      setMessages([{ ...WELCOME, timestamp: new Date() }])
      setIsTyping(false)
    }
  }, [location.search])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  async function handleSend(text: string, file?: File | null) {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: file ? `${text}\n*(Attached File: ${file.name})*` : text,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsTyping(true)

    try {
      const replyText = await sendChatMessage(text, file)
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: replyText,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      console.error(err)
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `**Error**: Failed to connect to the backend API. Please make sure the backend is running.`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } finally {
      setIsTyping(false)
    }
  }

  const hasOnlyWelcome = messages.length === 1 && messages[0].id === 'welcome'

  return (
    <>
      {/* Keyframes injected once */}
      <style>{`
        @keyframes chatDot {
          0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>

      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Page header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border)',
            background: 'var(--panel)',
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <div
            style={{
              width: 36, height: 36, borderRadius: 8,
              background: 'var(--accent-bg)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '1px solid var(--border)',
            }}
          >
            <Cpu size={18} color="var(--primary)" strokeWidth={1.8} />
          </div>
          <div>
            <h1
              style={{
                fontSize: '1rem',
                fontWeight: 700,
                color: 'var(--text)',
                letterSpacing: '-0.015em',
                margin: 0,
              }}
            >
              AI Engineering Assistant
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--muted)', margin: 0, maxWidth: 480 }}>
              Analyze engineering documents, P&amp;ID diagrams, internal knowledge and generate structured engineering results.
            </p>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span
              style={{
                width: 7, height: 7, borderRadius: '50%',
                background: 'var(--primary)',
                display: 'inline-block',
              }}
            />
            <span style={{ fontSize: '0.6875rem', color: 'var(--primary)', fontWeight: 600 }}>
              LOCAL MODEL READY
            </span>
          </div>
        </div>

        {/* Messages area */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '2rem 1.5rem 1rem',
            background: 'var(--bg)',
          }}
        >
          <div style={{ maxWidth: 760, margin: '0 auto' }}>
            {/* Welcome / empty state */}
            {hasOnlyWelcome && (
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div
                  style={{
                    width: 56, height: 56, borderRadius: '50%',
                    background: 'var(--accent-bg)', border: '1px solid var(--border)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 1rem',
                  }}
                >
                  <Bot size={26} color="var(--primary)" strokeWidth={1.8} />
                </div>
                <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.5rem' }}>
                  What can I help you with?
                </h2>
                <p style={{ fontSize: '0.875rem', color: 'var(--muted)', maxWidth: 440, margin: '0 auto 1.5rem' }}>
                  Select a suggested prompt below or type your own question about engineering documents,
                  P&amp;ID diagrams, or the knowledge base.
                </p>
                <SuggestedPrompts onSelect={handleSend} />
              </div>
            )}

            {/* Message list */}
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {/* Typing indicator */}
            {isTyping && <TypingIndicator />}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input area — sticky at bottom */}
        <div style={{ flexShrink: 0 }}>
          <ChatInput onSend={handleSend} disabled={isTyping} />
        </div>
      </div>
    </>
  )
}
