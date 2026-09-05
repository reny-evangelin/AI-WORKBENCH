// src/components/StatusBadge.tsx
interface StatusBadgeProps {
  status: 'processed' | 'analyzed' | 'ready' | 'pending' | 'error'
  label?: string
}

const MAP = {
  processed: { cls: 'badge-green', text: 'Processed' },
  analyzed:  { cls: 'badge-blue',  text: 'Analyzed' },
  ready:     { cls: 'badge-green', text: 'Ready' },
  pending:   { cls: 'badge-amber', text: 'Pending' },
  error:     { cls: 'badge-amber', text: 'Error' },
}

export default function StatusBadge({ status, label }: StatusBadgeProps) {
  const { cls, text } = MAP[status] ?? MAP.pending
  return <span className={`badge ${cls}`}>{label ?? text}</span>
}
