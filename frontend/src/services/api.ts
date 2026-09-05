// src/services/api.ts
// ─────────────────────────────────────────────────────────────────────────────
// Centralised API service layer.
// All fetch calls live here — components never call fetch() directly.
// When the backend is unavailable, mock functions return realistic sample data.
// ─────────────────────────────────────────────────────────────────────────────

import type { PIDAnalysisResult, KnowledgeResult, AnalysisReport, Finding } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'
const USE_MOCK = false // set false when real FastAPI backend is running

// ── Helpers ──────────────────────────────────────────────────────────────────

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

// ── Mock data ─────────────────────────────────────────────────────────────────

const MOCK_PID_RESULT: PIDAnalysisResult = {
  document_type: 'P&ID',
  equipment: [
    { tag: 'TK-101', category: 'equipment', confidence: 0.94, original_text: 'TK-101 FEED TANK' },
    { tag: 'E-201',  category: 'equipment', confidence: 0.91, original_text: 'E-201 HEAT EXCHANGER' },
  ],
  pumps: [
    { tag: 'P-101A', category: 'pumps', confidence: 0.96, original_text: 'P-101A FEED PUMP' },
  ],
  valves: [
    { tag: 'FCV-101', category: 'valves', confidence: 0.97, original_text: 'FCV-101 FLOW CONTROL VALVE' },
    { tag: 'LV-301',  category: 'valves', confidence: 0.93, original_text: 'LV-301 LEVEL CONTROL VALVE' },
    { tag: 'PSV-401', category: 'valves', confidence: 0.95, original_text: 'PSV-401 PRESSURE SAFETY VALVE' },
  ],
  instruments: [
    { tag: 'TI-401', category: 'instruments', confidence: 0.97, original_text: 'TAG: TI-401 TEMP INDICATOR' },
    { tag: 'PT-202', category: 'instruments', confidence: 0.98, original_text: 'TAG: PT-202 PRESSURE TRANSMITTER' },
    { tag: 'FIC-105', category: 'instruments', confidence: 0.92, original_text: 'FIC-105 FLOW INDICATOR CONTROLLER' },
  ],
  pipes: [
    { tag: '4-IA-SS-0012-A1A', category: 'pipes', confidence: 0.97, original_text: 'LINE NO: 4-IA-SS-0012-A1A' },
    { tag: '2-PW-CS-0034-B2B', category: 'pipes', confidence: 0.89, original_text: 'LINE NO: 2-PW-CS-0034-B2B' },
  ],
  raw_text: [
    'P&ID - INSTRUMENT AIR SYSTEM REV-3 SHEET 1 OF 2',
    'SERVICE: INSTRUMENT AIR',
    'DESIGN PRESSURE: 10 BAR G',
    'DESIGN TEMP: 50 DEG C (AMBIENT)',
    'TAG: TI-401 TEMP INDICATOR',
    'TAG: PT-202 PRESSURE TRANSMITTER RANGE: 0-200 DEG C',
    'FCV-101 FLOW CONTROL VALVE ACTUATOR: PNEUMATIC DIAPHRAGM',
    'LINE NO: 4-IA-SS-0012-A1A',
    'POSITIONER: YP-301',
    'BODY: GLOBE SIZE: 3 INCH',
    'FAIL POSITION: CLOSE (FC)',
    'LOCATION: FIELD',
    'DOCUMENT NO: XXXX-PI-001-000',
  ],
  total_elements: 9,
  image_path: 'uploaded_pid.png',
}

const MOCK_KNOWLEDGE_RESULTS: KnowledgeResult[] = [
  {
    id: '1',
    document: 'Safety_Manual.pdf',
    section: 'Section 4.2 — Equipment Inspection',
    text: 'All pressure vessels and associated instrumentation shall be inspected at intervals not exceeding 24 months. Inspection records must be retained for a minimum of 10 years.',
    relevance: 0.94,
    category: 'Safety',
  },
  {
    id: '2',
    document: 'Maintenance_Guidelines.pdf',
    section: 'Section 7.1 — Control Valve Maintenance',
    text: 'Flow control valves (FCV) classified as critical service shall be bench-tested annually. Packing and trim wear shall be assessed during each planned shutdown.',
    relevance: 0.88,
    category: 'Maintenance',
  },
  {
    id: '3',
    document: 'Inspection_Procedures_SOP.pdf',
    section: 'Section 2.4 — P&ID Verification',
    text: 'Prior to any tie-in activity, the responsible engineer must verify all P&ID drawings are at the latest approved revision. Discrepancies must be raised as engineering queries.',
    relevance: 0.82,
    category: 'SOP',
  },
  {
    id: '4',
    document: 'Equipment_Register.xlsx',
    section: 'Sheet: Rotating Equipment',
    text: 'Pump P-101A: Last inspection 14-Mar-2025. Next due 14-Mar-2026. Condition: Satisfactory. Bearing vibration within acceptable limits.',
    relevance: 0.77,
    category: 'Equipment',
  },
]

const MOCK_REPORT: AnalysisReport = {
  summary:
    'Analysis of the submitted P&ID drawing identified 9 tagged engineering elements across 5 categories. Cross-referencing with the internal knowledge base flagged 3 items requiring attention prior to operational sign-off.',
  confidence: 0.91,
  generatedAt: new Date().toISOString(),
  findings: [
    {
      id: 'f1',
      type: 'valve',
      finding: 'Control valve FCV-101 is due for annual bench-test per Maintenance Guidelines Section 7.1.',
      evidence: 'Maintenance_Guidelines.pdf',
      section: 'Section 7.1 — Control Valve Maintenance',
      recommendation: 'Schedule bench-test for FCV-101 before next planned shutdown window.',
      severity: 'moderate',
    },
    {
      id: 'f2',
      type: 'equipment',
      finding: 'Pressure transmitter PT-202 inspection record not found in Equipment Register.',
      evidence: 'Equipment_Register.xlsx',
      section: 'Sheet: Instrumentation',
      recommendation: 'Verify calibration certificate and update Equipment Register.',
      severity: 'moderate',
    },
    {
      id: 'f3',
      type: 'instrument',
      finding: 'Temperature indicator TI-401 shows range 0–200 °C, which exceeds normal ambient service range.',
      evidence: 'Safety_Manual.pdf',
      section: 'Section 4.2 — Equipment Inspection',
      recommendation: 'Confirm instrument range is appropriate for process conditions. Raise EQ if discrepancy found.',
      severity: 'low',
    },
    {
      id: 'f4',
      type: 'general',
      finding: 'P&ID is at REV-3. Confirm this matches the latest approved revision in Document Control.',
      evidence: 'Inspection_Procedures_SOP.pdf',
      section: 'Section 2.4 — P&ID Verification',
      recommendation: 'Cross-check revision status with Document Control before tie-in.',
      severity: 'info',
    },
  ] as Finding[],
  sopReferences: MOCK_KNOWLEDGE_RESULTS.slice(0, 3),
}

// ── API functions ─────────────────────────────────────────────────────────────

export async function analyzePID(file: File): Promise<PIDAnalysisResult> {
  if (USE_MOCK) {
    await sleep(2200)
    return MOCK_PID_RESULT
  }
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/analyze-pid`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`P&ID analysis failed: ${res.statusText}`)
  return res.json()
}

export async function uploadDocument(file: File): Promise<{ id: string; status: string }> {
  if (USE_MOCK) {
    await sleep(1500)
    return { id: crypto.randomUUID(), status: 'processed' }
  }
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/documents/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`)
  return res.json()
}

export async function searchKnowledge(query: string): Promise<KnowledgeResult[]> {
  if (USE_MOCK) {
    await sleep(900)
    // Filter mock results that loosely match query
    const q = query.toLowerCase()
    return MOCK_KNOWLEDGE_RESULTS.filter(
      (r) =>
        r.text.toLowerCase().includes(q) ||
        r.section.toLowerCase().includes(q) ||
        r.document.toLowerCase().includes(q) ||
        q.length < 3,
    )
  }
  const res = await fetch(`${API_BASE}/rag/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`)
  return res.json()
}

export async function generateReport(context: {
  pidResult?: PIDAnalysisResult
  knowledgeResults?: KnowledgeResult[]
}): Promise<AnalysisReport> {
  if (USE_MOCK) {
    await sleep(1800)
    return { ...MOCK_REPORT, generatedAt: new Date().toISOString() }
  }
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(context),
  })
  if (!res.ok) throw new Error(`Report generation failed: ${res.statusText}`)
  return res.json()
}

export async function generateDocx(): Promise<{ file_name: string; download_url: string; status: string }> {
  if (USE_MOCK) {
    await sleep(1200)
    return { file_name: "Mock_Report.docx", download_url: "#", status: "success" }
  }
  const res = await fetch(`${API_BASE}/generate-document`, { method: 'POST' })
  if (!res.ok) throw new Error(`DOCX generation failed: ${res.statusText}`)
  const data = await res.json()
  if (data.download_url && data.download_url.startsWith('/')) {
    data.download_url = `${API_BASE}${data.download_url}`
  }
  return data
}

export async function openFileOnSystem(filename: string): Promise<void> {
  const res = await fetch(`${API_BASE}/open-file?filename=${encodeURIComponent(filename)}`)
  if (!res.ok) throw new Error(`Failed to open file: ${res.statusText}`)
}

// ── Chat / AI Assistant ───────────────────────────────────────────────────────
// Mock responses keyed to common engineering queries.
// Replace the USE_MOCK block below with a POST to /api/chat when Member 2's
// agent backend is available. The function signature must remain identical.

const MOCK_CHAT_RESPONSES: Array<{ pattern: RegExp; response: string }> = [
  {
    pattern: /p.?id|piping|diagram/i,
    response:
      'I can analyze P&ID diagrams for you. From the uploaded diagrams I can extract:\n\n• Equipment tags (vessels, exchangers, pumps)\n• Valve identifiers and types\n• Instrument tags (TI, PT, FIC, etc.)\n• Line numbers and service classifications\n\nPlease navigate to the **P&ID Analysis** page to upload a diagram, or describe what you need and I\'ll help further.',
  },
  {
    pattern: /pump|p-101/i,
    response:
      'Based on the knowledge base, here is what I found about Pump P-101A:\n\n**Equipment Register — Rotating Equipment**\nLast inspection: 14-Mar-2025\nNext due: 14-Mar-2026\nCondition: Satisfactory\nBearing vibration: Within acceptable limits\n\nNo outstanding maintenance actions are recorded. Would you like me to generate a maintenance summary report?',
  },
  {
    pattern: /summar|document|pdf/i,
    response:
      'I can summarize engineering documents for you. Please upload a PDF via the **Documents** page first. Once processed, I can:\n\n• Extract key findings and recommendations\n• Identify referenced equipment and tags\n• Cross-reference with the knowledge base\n• Flag items requiring action\n\nShall I walk you through the document upload workflow?',
  },
  {
    pattern: /maintenan|report|generate/i,
    response:
      'Generating a maintenance report requires P&ID analysis results and knowledge base data. Here\'s the workflow:\n\n1. Upload and analyze a P&ID diagram\n2. Run a knowledge base search for relevant procedures\n3. Navigate to **Results** to generate a structured DOCX report\n\nThe report will include findings, severity ratings, SOP references, and recommended actions. Would you like me to start with step 1?',
  },
  {
    pattern: /valve|fcv|lcv|psv/i,
    response:
      'From the last P&ID analysis the following valves were identified:\n\n| Tag | Type | Confidence |\n|-----|------|------------|\n| FCV-101 | Flow Control Valve | 97% |\n| LV-301 | Level Control Valve | 93% |\n| PSV-401 | Pressure Safety Valve | 95% |\n\n**Maintenance note:** FCV-101 is due for annual bench-test per Maintenance Guidelines §7.1. Would you like a detailed finding report?',
  },
  {
    pattern: /instrument|ti|pt|fic/i,
    response:
      'Instruments detected in the last P&ID scan:\n\n• **TI-401** — Temperature Indicator (range 0–200 °C)\n• **PT-202** — Pressure Transmitter (0–200 bar)\n• **FIC-105** — Flow Indicator Controller\n\n⚠️ TI-401 range exceeds typical ambient service — recommend verification of process conditions. PT-202 calibration record was not found in the Equipment Register.',
  },
  {
    pattern: /safety|sop|procedure/i,
    response:
      'Relevant safety procedures found in the knowledge base:\n\n**Safety Manual §4.2 — Equipment Inspection**\nAll pressure vessels and associated instrumentation shall be inspected at intervals not exceeding 24 months. Records must be retained for a minimum of 10 years.\n\n**Inspection Procedures SOP §2.4 — P&ID Verification**\nPrior to any tie-in activity, the responsible engineer must verify all P&ID drawings are at the latest approved revision.\n\nWould you like me to cross-reference these against the current P&ID?',
  },
]

const FALLBACK_CHAT_RESPONSE =
  "I've noted your query. As a local AI assistant I'm currently operating with mock data. I can help with:\n\n• P&ID diagram analysis and tag extraction\n• Knowledge base search and SOP lookup\n• Document summarization and review\n• Maintenance report generation\n• Equipment and instrument queries\n\nFor live AI responses, connect Member 2's agent backend via the /api/chat endpoint. What else can I help you with?"

export async function sendChatMessage(userMessage: string, file?: File | null): Promise<string> {
  if (USE_MOCK) {
    await sleep(900 + Math.random() * 800)
    const match = MOCK_CHAT_RESPONSES.find((r) => r.pattern.test(userMessage))
    return match ? match.response : FALLBACK_CHAT_RESPONSE
  }

  const form = new FormData()
  form.append('message', userMessage)

  if (file) {
    form.append('file', file)

    // Determine input_type and file_type from the File object — no LLM needed
    const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
    const IMAGE_EXTS = ['png', 'jpg', 'jpeg', 'webp']
    const inputType = IMAGE_EXTS.includes(ext)
      ? 'image'
      : ext === 'pdf'
      ? 'pdf'
      : ext === 'docx'
      ? 'docx'
      : ext === 'xlsx'
      ? 'xlsx'
      : ext === 'csv'
      ? 'csv'          // backend will reject this with a clear error
      : ext === 'txt'
      ? 'text_file'
      : 'file'

    form.append('input_type', inputType)
    form.append('file_type', ext)
  } else {
    form.append('input_type', 'text')
  }

  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    // Try to surface the backend error message
    let detail = res.statusText
    try {
      const errJson = await res.json()
      detail = errJson.detail ?? detail
    } catch (_) { /* ignore */ }
    throw new Error(`Chat request failed: ${detail}`)
  }
  const data = await res.json()
  return data.reply as string
}
