// src/pages/HomePage.tsx
import { Link } from 'react-router-dom'
import { ScanLine, FileText, BookOpen, Clock, ChevronRight, Activity, MessageSquare } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'

const RECENT = [
  { name: 'Inspection_Report.pdf',   type: 'PDF',  status: 'processed' as const, time: '2 hours ago' },
  { name: 'P&ID_Unit_04.png',        type: 'PNG',  status: 'analyzed'  as const, time: '5 hours ago' },
  { name: 'Safety_SOP.pdf',          type: 'PDF',  status: 'ready'     as const, time: 'Yesterday' },
]

const ACTIONS = [
  {
    icon: FileText,
    title: 'Analyze Document',
    desc: 'Upload engineering PDFs or drawings for AI-assisted analysis.',
    to: '/documents',
    cta: 'Open Documents',
  },
  {
    icon: ScanLine,
    title: 'P&ID Analysis',
    desc: 'Extract tags, equipment and piping data from P&ID diagrams.',
    to: '/pid-analysis',
    cta: 'Open P&ID Analysis',
  },
  {
    icon: BookOpen,
    title: 'Search Knowledge Base',
    desc: 'Query internal SOPs, manuals and inspection procedures.',
    to: '/knowledge-base',
    cta: 'Open Knowledge Base',
  },
  {
    icon: MessageSquare,
    title: 'AI Assistant',
    desc: 'Chat with the AI assistant about documents, P&IDs and the knowledge base.',
    to: '/',
    cta: 'Open Chat',
  },
]

export default function HomePage() {
  return (
    <div className="page-container page-enter">
      {/* Header */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <h1 style={{ fontSize: '1.625rem', fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.025em' }}>
            AI Workbench
          </h1>
          <span style={{
            display: 'flex', alignItems: 'center', gap: '0.3rem',
            padding: '0.2rem 0.6rem', borderRadius: 20,
            background: 'var(--accent-bg)', color: 'var(--primary)',
            fontSize: '0.6875rem', fontWeight: 600, letterSpacing: '0.04em',
          }}>
            <Activity size={10} strokeWidth={2.5} />
            LOCAL PROCESSING ACTIVE
          </span>
        </div>
        <p style={{ color: 'var(--muted)', fontSize: '0.9375rem', maxWidth: 560, lineHeight: 1.6 }}>
          Analyze engineering documents, inspect P&amp;ID diagrams, retrieve internal knowledge and generate
          structured deliverables using local AI.
        </p>
      </div>

      {/* Primary action cards */}
      <div style={{ marginBottom: '2.5rem' }}>
        <span className="section-label" style={{ marginBottom: '0.75rem', display: 'block' }}>Primary Actions</span>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
          {ACTIONS.map(({ icon: Icon, title, desc, to, cta }) => (
            <div key={to} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{
                width: 38, height: 38, borderRadius: 8,
                background: 'var(--accent-bg)', display: 'flex',
                alignItems: 'center', justifyContent: 'center',
              }}>
                <Icon size={18} color="var(--primary)" strokeWidth={1.8} />
              </div>
              <div>
                <h3 style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text)', marginBottom: '0.3rem' }}>
                  {title}
                </h3>
                <p style={{ fontSize: '0.8125rem', color: 'var(--muted)', lineHeight: 1.55 }}>{desc}</p>
              </div>
              <Link to={to} className="btn-primary" style={{ marginTop: 'auto', justifyContent: 'space-between' }}>
                {cta}
                <ChevronRight size={14} />
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* Recent activity */}
      <div>
        <span className="section-label" style={{ marginBottom: '0.75rem', display: 'block' }}>Recent Activity</span>
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {RECENT.map((item, i) => (
            <div
              key={item.name}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '0.875rem 1.25rem',
                borderBottom: i < RECENT.length - 1 ? '1px solid var(--border)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                  width: 34, height: 34, borderRadius: 6, background: 'var(--sidebar-hover)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <FileText size={15} color="var(--muted)" />
                </div>
                <div>
                  <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text)' }}>{item.name}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '0.25rem', marginTop: 1 }}>
                    <Clock size={11} /> {item.time}
                  </p>
                </div>
              </div>
              <StatusBadge status={item.status} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
