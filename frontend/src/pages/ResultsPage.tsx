// src/pages/ResultsPage.tsx
import { useState } from 'react'
import {
  BarChart3, Loader2, CheckCircle, AlertTriangle,
  Info, FileText, Download, ChevronDown, ChevronUp,
} from 'lucide-react'
import { generateReport, generateDocx } from '../services/api'
import type { AnalysisReport, Finding } from '../types'
import ProgressBar from '../components/ProgressBar'

const SEVERITY_STYLE = {
  critical: { bg: '#fef2f2', color: '#991b1b', label: 'Critical',  icon: AlertTriangle },
  moderate: { bg: '#fefce8', color: '#92400e', label: 'Moderate',  icon: AlertTriangle },
  low:      { bg: '#f0fdf4', color: '#166534', label: 'Low',       icon: CheckCircle },
  info:     { bg: '#f0f9ff', color: '#1e40af', label: 'Info',      icon: Info },
}

const DARK_SEVERITY_STYLE = {
  critical: { bg: '#450a0a', color: '#fca5a5' },
  moderate: { bg: '#451a03', color: '#fcd34d' },
  low:      { bg: '#052e16', color: '#86efac' },
  info:     { bg: '#082f49', color: '#93c5fd' },
}

function FindingCard({ finding, isDark }: { finding: Finding; isDark: boolean }) {
  const [open, setOpen] = useState(false)
  const sev = SEVERITY_STYLE[finding.severity]
  const darkSev = DARK_SEVERITY_STYLE[finding.severity]
  const Icon = sev.icon

  return (
    <div
      className="card"
      style={{
        marginBottom: '0.75rem',
        borderLeft: `3px solid ${sev.color}`,
        padding: '1rem 1.25rem',
      }}
    >
      <div
        style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', cursor: 'pointer', gap: '0.75rem' }}
        onClick={() => setOpen((o) => !o)}
      >
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <Icon size={14} color={sev.color} />
            <span
              style={{
                fontSize: '0.6875rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: 12,
                background: isDark ? darkSev.bg : sev.bg, color: isDark ? darkSev.color : sev.color,
              }}
            >
              {sev.label}
            </span>
          </div>
          <p style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--text)', lineHeight: 1.55 }}>
            {finding.finding}
          </p>
        </div>
        {open ? <ChevronUp size={15} color="var(--muted)" /> : <ChevronDown size={15} color="var(--muted)" />}
      </div>

      {open && (
        <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div>
              <p className="section-label" style={{ marginBottom: '0.25rem' }}>Evidence</p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text)' }}>{finding.evidence}</p>
              <p style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>{finding.section}</p>
            </div>
            <div>
              <p className="section-label" style={{ marginBottom: '0.25rem' }}>Recommendation</p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text)', lineHeight: 1.55 }}>
                {finding.recommendation}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function ResultsPage() {
  const [status, setStatus] = useState<'idle' | 'generating' | 'done' | 'error'>('idle')
  const [report, setReport] = useState<AnalysisReport | null>(null)
  const [downloading, setDownloading] = useState(false)
  const isDark = document.documentElement.classList.contains('dark')

  async function generate() {
    setStatus('generating')
    try {
      const r = await generateReport({})
      setReport(r)
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  async function downloadDocx() {
    setDownloading(true)
    try {
      const blob = await generateDocx()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = 'AI_Workbench_Report.docx'; a.click()
      URL.revokeObjectURL(url)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="page-container page-enter">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.02em', marginBottom: '0.4rem' }}>
          Analysis Results
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
          AI-generated findings, recommendations and deliverables from your engineering analysis.
        </p>
      </div>

      {status === 'idle' && (
        <div style={{ textAlign: 'center', padding: '4rem 0' }}>
          <BarChart3 size={40} color="var(--muted)" strokeWidth={1.3} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
          <p style={{ color: 'var(--muted)', marginBottom: '1.25rem', fontSize: '0.9375rem' }}>
            No analysis generated yet.
          </p>
          <button className="btn-primary" onClick={generate}>
            <BarChart3 size={15} /> Generate Analysis Report
          </button>
        </div>
      )}

      {status === 'generating' && (
        <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--muted)' }}>
          <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 0.75rem' }} />
          <p>Generating report…</p>
        </div>
      )}

      {status === 'done' && report && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '1.5rem', alignItems: 'start' }}>
          {/* Left: report */}
          <div>
            {/* Executive summary */}
            <div className="card" style={{ marginBottom: '1.25rem' }}>
              <p className="section-label" style={{ marginBottom: '0.5rem' }}>Executive Summary</p>
              <p style={{ fontSize: '0.9375rem', color: 'var(--text)', lineHeight: 1.65 }}>{report.summary}</p>
              <div style={{ marginTop: '1rem' }}>
                <ProgressBar label="Overall Confidence" value={Math.round(report.confidence * 100)} />
              </div>
            </div>

            {/* Findings */}
            <div style={{ marginBottom: '1.25rem' }}>
              <h2 style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text)', marginBottom: '0.75rem' }}>
                Key Findings ({report.findings.length})
              </h2>
              {report.findings.map((f) => (
                <FindingCard key={f.id} finding={f} isDark={isDark} />
              ))}
            </div>

            {/* SOP References */}
            <div>
              <h2 style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text)', marginBottom: '0.75rem' }}>
                Relevant SOP References
              </h2>
              <div className="card" style={{ padding: 0 }}>
                {report.sopReferences.map((ref, i) => (
                  <div key={ref.id} style={{
                    padding: '0.875rem 1.125rem',
                    borderBottom: i < report.sopReferences.length - 1 ? '1px solid var(--border)' : 'none',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
                      <FileText size={13} color="var(--muted)" />
                      <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text)' }}>{ref.document}</span>
                    </div>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--muted)', marginBottom: '0.3rem' }}>{ref.section}</p>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text)', lineHeight: 1.55 }}>{ref.text.slice(0, 120)}…</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: deliverables */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="card">
              <p style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text)', marginBottom: '1rem' }}>
                Deliverables
              </p>

              {[
                { label: 'Approval Note', fmt: 'DOCX', desc: 'Ready to generate' },
                { label: 'Analysis Report', fmt: 'PDF',  desc: 'Ready to generate' },
              ].map((d) => (
                <div key={d.label} style={{
                  padding: '0.875rem', borderRadius: 7, border: '1px solid var(--border)',
                  marginBottom: '0.625rem',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text)' }}>{d.label}</span>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.45rem', borderRadius: 6, background: 'var(--accent-bg)', color: 'var(--primary)' }}>
                      {d.fmt}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.625rem' }}>{d.desc}</p>
                  <button
                    className="btn-secondary"
                    style={{ width: '100%', justifyContent: 'center', fontSize: '0.8125rem', padding: '0.4rem' }}
                    onClick={downloadDocx}
                    disabled={downloading}
                  >
                    {downloading
                      ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />
                      : <Download size={13} />}
                    {d.fmt === 'DOCX' ? 'Download DOCX' : 'View Report'}
                  </button>
                </div>
              ))}
            </div>

            <div className="card">
              <p className="section-label" style={{ marginBottom: '0.4rem' }}>Generated</p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text)' }}>
                {new Date(report.generatedAt).toLocaleString()}
              </p>
              <div className="divider" />
              <p className="section-label" style={{ marginBottom: '0.4rem' }}>Processing</p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--primary)', fontWeight: 500 }}>Local Only</p>
            </div>

            <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={generate}>
              <BarChart3 size={14} /> Regenerate
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
