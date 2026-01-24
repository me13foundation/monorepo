export type ExtractionStatus = 'completed' | 'failed' | 'skipped'

export type ExtractionTextSource = 'title_abstract' | 'title' | 'abstract' | 'full_text'

export type ExtractionFact = {
  fact_type: string
  value: string
  normalized_id?: string | null
  source?: string | null
  attributes?: Record<string, unknown> | null
}

export interface PublicationExtraction {
  id: string
  publication_id: number
  pubmed_id?: string | null
  source_id: string
  ingestion_job_id: string
  queue_item_id: string
  status: ExtractionStatus
  extraction_version: number
  processor_name: string
  processor_version?: string | null
  text_source: ExtractionTextSource | string
  document_reference?: string | null
  facts?: ExtractionFact[]
  metadata?: Record<string, unknown>
  extracted_at: string
  created_at: string
  updated_at: string
}

export interface ExtractionDocumentResponse {
  extraction_id: string
  document_reference: string
  url: string
}
