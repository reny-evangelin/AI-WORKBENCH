// src/types/index.ts
export interface UploadedFile {
  name: string
  type: string
  size: number
  file: File
}

export interface DetectedElement {
  tag: string
  category: string
  confidence: number
  original_text: string
}

export interface PIDAnalysisResult {
  document_type: string
  equipment: DetectedElement[]
  pumps: DetectedElement[]
  valves: DetectedElement[]
  instruments: DetectedElement[]
  pipes: DetectedElement[]
  raw_text: string[]
  total_elements: number
  image_path: string
}

export interface KnowledgeResult {
  id: string
  document: string
  section: string
  text: string
  relevance: number
  category: string
}

export interface Finding {
  id: string
  type: 'equipment' | 'valve' | 'instrument' | 'pipe' | 'general'
  finding: string
  evidence: string
  section: string
  recommendation: string
  severity: 'critical' | 'moderate' | 'low' | 'info'
}

export interface AnalysisReport {
  summary: string
  findings: Finding[]
  confidence: number
  sopReferences: KnowledgeResult[]
  generatedAt: string
}

export type Theme = 'light' | 'dark'
