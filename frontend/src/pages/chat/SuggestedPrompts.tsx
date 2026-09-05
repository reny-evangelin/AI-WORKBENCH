// src/pages/chat/SuggestedPrompts.tsx

interface SuggestedPromptsProps {
  onSelect: (prompt: string) => void
}

const PROMPTS = [
  'Analyze this P&ID',
  'Find information about Pump P-101',
  'Summarize this document',
  'Generate a maintenance report',
  'What valves are in the system?',
  'List all safety-critical instruments',
]

export default function SuggestedPrompts({ onSelect }: SuggestedPromptsProps) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center' }}>
      {PROMPTS.map((prompt) => (
        <button
          key={prompt}
          onClick={() => onSelect(prompt)}
          style={{
            padding: '0.4375rem 0.875rem',
            borderRadius: 20,
            border: '1px solid var(--border)',
            background: 'var(--panel)',
            color: 'var(--text)',
            fontSize: '0.8125rem',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
          onMouseEnter={(e) => {
            const t = e.currentTarget
            t.style.borderColor = 'var(--primary)'
            t.style.color = 'var(--primary)'
            t.style.background = 'var(--accent-bg)'
          }}
          onMouseLeave={(e) => {
            const t = e.currentTarget
            t.style.borderColor = 'var(--border)'
            t.style.color = 'var(--text)'
            t.style.background = 'var(--panel)'
          }}
        >
          {prompt}
        </button>
      ))}
    </div>
  )
}
