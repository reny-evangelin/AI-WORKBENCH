// src/components/ProgressBar.tsx
interface ProgressBarProps {
  value: number // 0–100
  label?: string
  color?: string
}

export default function ProgressBar({ value, label, color = 'var(--primary)' }: ProgressBarProps) {
  return (
    <div>
      {label && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: '0.8125rem', color: 'var(--muted)' }}>{label}</span>
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text)' }}>{value}%</span>
        </div>
      )}
      <div style={{ height: 5, background: 'var(--border)', borderRadius: 99, overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            width: `${Math.min(100, Math.max(0, value))}%`,
            background: color,
            borderRadius: 99,
            transition: 'width 0.5s ease',
          }}
        />
      </div>
    </div>
  )
}
