// src/pages/DocumentsPage.tsx
import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, X, CheckCircle, Loader2, ChevronRight } from 'lucide-react'
import { uploadDocument } from '../services/api'

type DocTask = 'Document Analysis' | 'Inspection Report' | 'Technical Document' | 'Safety Document'

export default function DocumentsPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [task, setTask] = useState<DocTask>('Document Analysis')
  const [status, setStatus] = useState<'idle' | 'uploading' | 'done' | 'error'>('idle')
  const [error, setError] = useState('')

  const accept = '.pdf,.png,.jpg,.jpeg,.docx'
  const TASKS: DocTask[] = ['Document Analysis', 'Inspection Report', 'Technical Document', 'Safety Document']

  function formatSize(bytes: number) {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 ** 2).toFixed(1)} MB`
  }

  function handleFile(f: File) {
    setFile(f)
    setStatus('idle')
    setError('')
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [])

  async function startAnalysis() {
    if (!file) return
    setStatus('uploading')
    setError('')
    try {
      await uploadDocument(file)
      setStatus('done')
      setTimeout(() => navigate('/results'), 1200)
    } catch (e: any) {
      setStatus('error')
      setError(e.message)
    }
  }

  return (
    <div className="page-container page-enter">
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.02em', marginBottom: '0.4rem' }}>
          Document Analysis
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
          Upload engineering documents for local AI processing. No data leaves your environment.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left — upload */}
        <div>
          {/* Drop zone */}
          <div
            className={`upload-zone${dragOver ? ' drag-over' : ''}`}
            style={{ padding: '3rem 2rem', textAlign: 'center', marginBottom: '1.25rem' }}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
          >
            <input
              ref={inputRef}
              type="file"
              accept={accept}
              style={{ display: 'none' }}
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            <Upload size={32} color="var(--muted)" strokeWidth={1.5} style={{ margin: '0 auto 1rem' }} />
            <p style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text)', marginBottom: '0.4rem' }}>
              Drag &amp; drop a file, or{' '}
              <span style={{ color: 'var(--primary)', textDecoration: 'underline', cursor: 'pointer' }}>
                choose a file
              </span>
            </p>
            <p style={{ fontSize: '0.8125rem', color: 'var(--muted)' }}>
              Supported: PDF · PNG · JPG · DOCX
            </p>
          </div>

          {/* Selected file */}
          {file && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.25rem' }}>
              <div style={{
                width: 40, height: 40, borderRadius: 8,
                background: 'var(--accent-bg)', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <FileText size={18} color="var(--primary)" />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontWeight: 500, fontSize: '0.875rem', color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {file.name}
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: 2 }}>
                  {file.type || 'Unknown type'} · {formatSize(file.size)}
                </p>
              </div>
              {status === 'idle' && (
                <button
                  onClick={(e) => { e.stopPropagation(); setFile(null); setStatus('idle') }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)', padding: 4 }}
                >
                  <X size={16} />
                </button>
              )}
              {status === 'uploading' && <Loader2 size={18} color="var(--primary)" style={{ animation: 'spin 1s linear infinite' }} />}
              {status === 'done' && <CheckCircle size={18} color="var(--primary)" />}
            </div>
          )}

          {error && (
            <p style={{ fontSize: '0.8125rem', color: '#dc2626', marginBottom: '1rem' }}>{error}</p>
          )}

          {/* Start button */}
          <button
            className="btn-primary"
            onClick={startAnalysis}
            disabled={!file || status === 'uploading' || status === 'done'}
            style={{ opacity: !file || status === 'uploading' || status === 'done' ? 0.5 : 1, gap: '0.5rem' }}
          >
            {status === 'uploading' ? (
              <><Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> Processing...</>
            ) : status === 'done' ? (
              <><CheckCircle size={15} /> Redirecting...</>
            ) : (
              <>Start Analysis <ChevronRight size={15} /></>
            )}
          </button>
        </div>

        {/* Right — task selector */}
        <div className="card">
          <p style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text)', marginBottom: '1rem' }}>
            Analysis Task
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {TASKS.map((t) => (
              <button
                key={t}
                onClick={() => setTask(t)}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '0.625rem 0.875rem', borderRadius: 7, cursor: 'pointer',
                  border: task === t ? '1.5px solid var(--primary)' : '1px solid var(--border)',
                  background: task === t ? 'var(--accent-bg)' : 'transparent',
                  color: task === t ? 'var(--primary)' : 'var(--text)',
                  fontSize: '0.8125rem', fontWeight: task === t ? 600 : 400,
                  transition: 'all 0.15s',
                }}
              >
                {t}
                {task === t && <CheckCircle size={14} />}
              </button>
            ))}
          </div>

          <div className="divider" />

          <div>
            <p className="section-label" style={{ marginBottom: '0.4rem' }}>Processing Mode</p>
            <p style={{ fontSize: '0.8125rem', color: 'var(--primary)', fontWeight: 500 }}>
              Local Inference Only
            </p>
            <p style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: 2 }}>
              No data is sent to external servers.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
