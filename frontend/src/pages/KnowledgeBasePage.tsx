// src/pages/KnowledgeBasePage.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, BookOpen, FileText, ChevronRight, Loader2, Tag } from 'lucide-react'
import { searchKnowledge } from '../services/api'
import type { KnowledgeResult } from '../types'

const SOURCES = [
  { label: 'SOPs',                   count: 12 },
  { label: 'Safety Manuals',         count: 4  },
  { label: 'Maintenance Guidelines', count: 8  },
  { label: 'Inspection Procedures',  count: 6  },
]

const CATEGORY_COLOR: Record<string, string> = {
  Safety:      '#dc2626',
  Maintenance: '#0369a1',
  SOP:         '#7c3aed',
  Equipment:   '#0f766e',
}

export default function KnowledgeBasePage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<KnowledgeResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [selected, setSelected] = useState<KnowledgeResult | null>(null)

  async function doSearch() {
    if (!query.trim()) return
    setLoading(true)
    setSearched(true)
    try {
      const res = await searchKnowledge(query)
      setResults(res)
    } finally {
      setLoading(false)
    }
  }

  function useInAnalysis(r: KnowledgeResult) {
    setSelected(r)
    setTimeout(() => navigate('/results'), 800)
  }

  return (
    <div className="page-container page-enter">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.02em', marginBottom: '0.4rem' }}>
          Engineering Knowledge Base
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
          Search internal SOPs, manuals and engineering documentation. Results are retrieved locally.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left: search + results */}
        <div>
          {/* Search bar */}
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <Search
                size={16} color="var(--muted)"
                style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
              />
              <input
                className="input-field"
                style={{ paddingLeft: '2.25rem' }}
                placeholder="What procedure applies to this inspection finding?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && doSearch()}
              />
            </div>
            <button
              className="btn-primary"
              onClick={doSearch}
              disabled={loading || !query.trim()}
              style={{ opacity: loading || !query.trim() ? 0.5 : 1, whiteSpace: 'nowrap' }}
            >
              {loading ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Search size={14} />}
              Search
            </button>
          </div>

          {/* Results */}
          {!searched && !loading && (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--muted)' }}>
              <BookOpen size={36} strokeWidth={1.2} style={{ margin: '0 auto 0.75rem', opacity: 0.4 }} />
              <p style={{ fontSize: '0.9rem' }}>Enter a query to search the knowledge base.</p>
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>
              <Loader2 size={24} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 0.5rem' }} />
              <p style={{ fontSize: '0.875rem' }}>Retrieving documents…</p>
            </div>
          )}

          {searched && !loading && results.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>
              <p>No results found for your query.</p>
            </div>
          )}

          {results.map((r) => (
            <div key={r.id} className="card" style={{ marginBottom: '0.875rem', position: 'relative' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                    <FileText size={14} color="var(--muted)" />
                    <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text)' }}>{r.document}</span>
                    <span style={{
                      fontSize: '0.6875rem', fontWeight: 600, padding: '0.1rem 0.45rem', borderRadius: 12,
                      background: 'var(--accent-bg)', color: CATEGORY_COLOR[r.category] ?? 'var(--primary)',
                    }}>
                      {r.category}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>{r.section}</p>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text)', lineHeight: 1.6 }}>{r.text}</p>
                </div>
                <div style={{ textAlign: 'center', flexShrink: 0 }}>
                  <p style={{ fontWeight: 700, fontSize: '1.125rem', color: 'var(--primary)' }}>
                    {Math.round(r.relevance * 100)}%
                  </p>
                  <p style={{ fontSize: '0.65rem', color: 'var(--muted)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                    Relevance
                  </p>
                </div>
              </div>
              <div style={{ marginTop: '0.875rem', display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn-primary"
                  style={{ fontSize: '0.8125rem', padding: '0.375rem 0.875rem' }}
                  onClick={() => useInAnalysis(r)}
                >
                  {selected?.id === r.id ? 'Added ✓' : 'Use in Analysis'} <ChevronRight size={12} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Right: sources */}
        <div className="card">
          <p style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text)', marginBottom: '0.875rem' }}>
            Knowledge Sources
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {SOURCES.map((s) => (
              <div key={s.label} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '0.5rem 0.625rem', borderRadius: 6, background: 'var(--sidebar-hover)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Tag size={12} color="var(--muted)" />
                  <span style={{ fontSize: '0.8125rem', color: 'var(--text)' }}>{s.label}</span>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 600 }}>{s.count}</span>
              </div>
            ))}
          </div>
          <div className="divider" />
          <p style={{ fontSize: '0.75rem', color: 'var(--muted)', lineHeight: 1.55 }}>
            All documents are indexed locally. No data leaves your environment.
          </p>
        </div>
      </div>
    </div>
  )
}
