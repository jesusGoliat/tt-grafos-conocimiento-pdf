export type JobStatus = 'queued' | 'uploading' | 'processing' | 'done' | 'failed'

export interface Progress {
  extracted_pages: number | null
  total_pages: number | null
  remote_state: string | null
}

export interface DocumentStatus {
  id: string
  filename: string
  size_bytes: number
  pages: number
  status: JobStatus
  progress: Progress
  error: string | null
  created_at: string
  updated_at: string
  finished_at: string | null
}

export interface ContentBlock {
  type: string
  page_idx?: number
  text?: string
  text_level?: number
  [key: string]: unknown
}

export interface ExtractionStats {
  pages: number
  blocks_total: number
  blocks_by_type: Record<string, number>
  characters: number
  words: number
}

export interface ExtractionResult {
  id: string
  filename: string
  markdown: string
  content_list: ContentBlock[]
  stats: ExtractionStats
  assets_base_url: string
}

export interface Health {
  status: string
  mineru_token_configured: boolean
  mineru_model_version: string
}
