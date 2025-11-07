export interface DataSource {
  id: string
  name: string
  description: string
  source_type: string
  status: string
  owner_id: string
  research_space_id: string | null
  created_at: string
  updated_at: string
  tags?: string[]
}

export type SourceType = 'api' | 'file_upload' | 'database' | 'web_scraping'

export type SourceStatus =
  | 'draft'
  | 'active'
  | 'inactive'
  | 'error'
  | 'pending_review'
  | 'archived'
