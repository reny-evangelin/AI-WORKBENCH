import { Bot, User, FileText, Download, ExternalLink, Eye } from 'lucide-react'

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

  // Extract file JSON from content
  let textContent = message.content
  const fileCards: Array<{
    type: string;
    filename?: string;
    path?: string;
    file_type?: string;
  }> = []

  if (!isUser) {
    const lines = textContent.split('\n')
    const remainingLines: string[] = []
    
    for (const line of lines) {
      if (line.trim().startsWith('{') && line.trim().endsWith('}')) {
        try {
          const data = JSON.parse(line)
          if (data && data.type === 'file') {
            fileCards.push(data)
            continue
          }
        } catch (e) {
          // not valid json
        }
      }
      remainingLines.push(line)
    }
    textContent = remainingLines.join('\n').trim()
  }

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
          {textContent && <div>{textContent}</div>}
          
          {/* File Cards */}
          {fileCards.length > 0 && (
            <div style={{ marginTop: textContent ? '1rem' : '0', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {fileCards.map((file, idx) => {
                const fileName = file.filename || file.path?.split(/[/\\]/).pop() || 'document'
                const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'
                const fileUrl = `${API_BASE}/outputs/${fileName}`
                
                return (
                  <div key={idx} style={{
                    display: 'flex', alignItems: 'center', gap: '0.75rem',
                    background: 'var(--bg)', border: '1px solid var(--border)',
                    padding: '0.75rem', borderRadius: '8px', color: 'var(--text)',
                    minWidth: '250px'
                  }}>
                    <div style={{
                      background: 'var(--accent-bg)', padding: '0.5rem',
                      borderRadius: '6px', color: 'var(--primary)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center'
                    }}>
                      <FileText size={20} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.1rem' }}>{fileName}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase' }}>
                        Generated {file.file_type || 'Document'}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                      <a href={fileUrl} target="_blank" rel="noreferrer" style={{
                        background: 'var(--accent-bg)', border: '1px solid var(--border)', cursor: 'pointer',
                        color: 'var(--text)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        padding: '0.4rem 0.8rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 500, flex: 1
                      }}>
                        Open
                      </a>
                      <a href={fileUrl} download={fileName} title="Download File" style={{
                        background: 'var(--primary)', border: 'none', cursor: 'pointer',
                        color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        padding: '0.4rem 0.8rem', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 500, flex: 1
                      }}>
                        Download
                      </a>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
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
