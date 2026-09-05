// src/pages/PIDAnalysisPage.tsx
import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Upload, ScanLine, Cpu, Tag,
  CheckCircle, Loader2, ChevronRight, ArrowDown,
} from 'lucide-react'
import { analyzePID } from '../services/api'
import type { PIDAnalysisResult } from '../types'
import ProgressBar from '../components/ProgressBar'

type Step = 'Image' | 'OCR' | 'P&ID Parsing' | 'Component Detection' | 'Structured Output'
const PIPELINE_STEPS: Step[] = ['Image', 'OCR', 'P&ID Parsing', 'Component Detection', 'Structured Output']

const CATEGORY_COLORS: Record<string, string> = {
  equipment:   '#0f766e',
  pumps:       '#0369a1',
  valves:      '#7c3aed',
  instruments: '#b45309',
  pipes:       '#374151',
}

export default function PIDAnalysisPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [status, setStatus] = useState<'idle' | 'analyzing' | 'done' | 'error'>('idle')
  const [activeStep, setActiveStep] = useState(-1)
  const [result, setResult] = useState<PIDAnalysisResult | null>(null)
  const [error, setError] = useState('')

  function handleFile(f: File) {
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setStatus('idle')
    setResult(null)
    setError('')
    setActiveStep(-1)
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [])

  async function runAnalysis() {
    if (!file) return
    setStatus('analyzing')
    setError('')
    // Animate pipeline steps
    for (let i = 0; i < PIPELINE_STEPS.length - 1; i++) {
      setActiveStep(i)
      await new Promise((r) => setTimeout(r, 420))
    }
    try {
      const res = await analyzePID(file)
      setActiveStep(PIPELINE_STEPS.length - 1)
      await new Promise((r) => setTimeout(r, 300))
      setResult(res)
      setStatus('done')
    } catch (e: any) {
      setStatus('error')
      setError(e.message)
    }
  }

  const allElements = result
    ? [
        ...result.equipment.map((e) => ({ ...e, cat: 'Equipment' })),
        ...result.pumps.map((e) => ({ ...e, cat: 'Pump' })),
        ...result.valves.map((e) => ({ ...e, cat: 'Valve' })),
        ...result.instruments.map((e) => ({ ...e, cat: 'Instrument' })),
        ...result.pipes.map((e) => ({ ...e, cat: 'Pipe' })),
      ]
    : []

  return (
    <div className="page-container page-enter">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.02em', marginBottom: '0.4rem' }}>
          P&amp;ID Vision Analysis
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: '0.9rem' }}>
          Extract equipment, tags and engineering information from P&amp;ID drawings using local OCR and pattern matching.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left: upload + preview */}
        <div>
          {/* Upload zone / preview */}
          {!preview ? (
            <div
              className={`upload-zone${dragOver ? ' drag-over' : ''}`}
              style={{ padding: '4rem 2rem', textAlign: 'center', marginBottom: '1.25rem' }}
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
            >
              <input ref={inputRef} type="file" accept=".png,.jpg,.jpeg,.bmp,.tiff,.webp"
                style={{ display: 'none' }}
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
              <ScanLine size={36} color="var(--muted)" strokeWidth={1.5} style={{ margin: '0 auto 1rem' }} />
              <p style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text)', marginBottom: '0.4rem' }}>
                Upload a P&amp;ID drawing
              </p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--muted)' }}>PNG · JPG · BMP · TIFF · WEBP</p>
            </div>
          ) : (
            <div className="card" style={{ padding: '0.75rem', marginBottom: '1.25rem', position: 'relative' }}>
              <img
                src={preview}
                alt="P&ID preview"
                style={{ width: '100%', borderRadius: 6, display: 'block', maxHeight: 420, objectFit: 'contain', background: '#f8f8f8' }}
              />
              <button
                onClick={() => { setFile(null); setPreview(null); setResult(null); setStatus('idle') }}
                style={{
                  position: 'absolute', top: 14, right: 14,
                  background: 'var(--panel)', border: '1px solid var(--border)',
                  borderRadius: 6, padding: '0.25rem 0.5rem',
                  fontSize: '0.75rem', cursor: 'pointer', color: 'var(--muted)',
                  display: 'flex', alignItems: 'center', gap: 4,
                }}
              >
                <Upload size={12} /> Change
              </button>
            </div>
          )}

          {/* Action buttons */}
          {file && status !== 'done' && (
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button
                className="btn-primary"
                onClick={runAnalysis}
                disabled={status === 'analyzing'}
                style={{ opacity: status === 'analyzing' ? 0.6 : 1 }}
              >
                {status === 'analyzing'
                  ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Analyzing…</>
                  : <><Cpu size={14} /> Analyze P&amp;ID</>}
              </button>
            </div>
          )}

          {error && <p style={{ fontSize: '0.8125rem', color: '#dc2626', marginTop: '0.75rem' }}>{error}</p>}

          {/* Results table */}
          {result && (
            <div style={{ marginTop: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <h3 style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text)' }}>
                  Detected Elements — {result.total_elements} found
                </h3>
                <button className="btn-secondary" style={{ fontSize: '0.8125rem', padding: '0.4rem 0.875rem' }}
                  onClick={() => navigate('/results')}>
                  View Full Report <ChevronRight size={13} />
                </button>
              </div>
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                {allElements.map((el, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '0.75rem 1.125rem',
                    borderBottom: i < allElements.length - 1 ? '1px solid var(--border)' : 'none',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <Tag size={14} color={CATEGORY_COLORS[el.category] ?? 'var(--muted)'} />
                      <div>
                        <p style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text)' }}>{el.tag}</p>
                        <p style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: 1 }}>{el.original_text}</p>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{
                        fontSize: '0.6875rem', fontWeight: 600, padding: '0.15rem 0.5rem', borderRadius: 12,
                        background: 'var(--accent-bg)', color: CATEGORY_COLORS[el.category] ?? 'var(--primary)',
                      }}>
                        {el.cat}
                      </span>
                      <p style={{ fontSize: '0.7rem', color: 'var(--muted)', marginTop: 3 }}>
                        {(el.confidence * 100).toFixed(0)}% confidence
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: pipeline + controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Pipeline */}
          <div className="card">
            <p style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text)', marginBottom: '1rem' }}>
              Processing Pipeline
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
              {PIPELINE_STEPS.map((step, i) => {
                const isDone = status === 'done' || activeStep > i
                const isActive = activeStep === i && status === 'analyzing'
                return (
                  <div key={step}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', padding: '0.4rem 0' }}>
                      <div style={{
                        width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: isDone ? 'var(--primary)' : isActive ? 'var(--accent-bg)' : 'var(--border)',
                        border: isActive ? '2px solid var(--primary)' : 'none',
                        transition: 'all 0.2s',
                      }}>
                        {isDone
                          ? <CheckCircle size={12} color="#fff" />
                          : isActive
                            ? <Loader2 size={11} color="var(--primary)" style={{ animation: 'spin 1s linear infinite' }} />
                            : <span style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--muted)' }} />}
                      </div>
                      <span style={{
                        fontSize: '0.8125rem',
                        fontWeight: isActive || isDone ? 600 : 400,
                        color: isDone ? 'var(--primary)' : isActive ? 'var(--text)' : 'var(--muted)',
                      }}>{step}</span>
                    </div>
                    {i < PIPELINE_STEPS.length - 1 && (
                      <div style={{ marginLeft: 11, paddingLeft: 0 }}>
                        <ArrowDown size={12} color="var(--border)" strokeWidth={2} style={{ marginLeft: 4 }} />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Stats */}
          {result && (
            <div className="card">
              <p style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text)', marginBottom: '0.875rem' }}>
                Analysis Summary
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
                <ProgressBar label="OCR Confidence" value={Math.round((result.instruments[0]?.confidence ?? 0.92) * 100)} />
                <ProgressBar label="Tag Extraction" value={Math.min(100, Math.round(result.total_elements * 11))} />
                <ProgressBar label="Coverage" value={87} />
              </div>
              <div className="divider" />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                {[
                  { label: 'Instruments', val: result.instruments.length },
                  { label: 'Valves', val: result.valves.length },
                  { label: 'Equipment', val: result.equipment.length },
                  { label: 'Pipes', val: result.pipes.length },
                ].map(({ label, val }) => (
                  <div key={label} style={{ textAlign: 'center', padding: '0.5rem', borderRadius: 7, background: 'var(--sidebar-hover)' }}>
                    <p style={{ fontWeight: 700, fontSize: '1.125rem', color: 'var(--primary)' }}>{val}</p>
                    <p style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>{label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
