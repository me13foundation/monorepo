// TypeScript types for Data Source Discovery

import type { SourceType } from '@/types/data-source'

export type QueryParameterType = 'gene' | 'term' | 'geneAndTerm' | 'none' | 'api'

export type TestResultStatus =
  | 'pending'
  | 'success'
  | 'error'
  | 'timeout'
  | 'validation_failed'

export type StorageUseCase = 'pdf' | 'export' | 'raw_source' | 'backup'

export interface QueryParameters {
  gene_symbol: string | null
  search_term: string | null
}

export type PubmedSortOption =
  | 'relevance'
  | 'publication_date'
  | 'author'
  | 'journal'
  | 'title'

export interface AdvancedQueryParameters extends QueryParameters {
  date_from?: string | null
  date_to?: string | null
  publication_types?: string[]
  languages?: string[]
  sort_by?: PubmedSortOption | null
  max_results?: number
  additional_terms?: string | null

  // ClinVar specific parameters
  variation_types?: string[]
  clinical_significance?: string[]

  // UniProt specific parameters
  is_reviewed?: boolean | null
  organism?: string | null
}

export interface QueryParameterCapabilities {
  supports_date_range: boolean
  supports_publication_types: boolean
  supports_language_filter: boolean
  supports_sort_options: boolean
  supports_additional_terms: boolean
  max_results_limit: number

  supported_storage_use_cases: StorageUseCase[]

  // ClinVar specific capabilities
  supports_variation_type: boolean
  supports_clinical_significance: boolean

  // UniProt specific capabilities
  supports_review_status: boolean
  supports_organism: boolean
}

export interface SourceCatalogEntry {
  id: string
  name: string
  category: string
  subcategory: string | null
  description: string
  source_type: SourceType
  param_type: QueryParameterType
  is_active: boolean
  requires_auth: boolean
  usage_count: number
  success_rate: number
  tags: string[]
  capabilities: QueryParameterCapabilities
}

export interface QueryTestResult {
  id: string
  catalog_entry_id: string
  session_id: string
  parameters: AdvancedQueryParameters
  status: TestResultStatus
  response_data: Record<string, unknown> | null
  response_url: string | null
  error_message: string | null
  execution_time_ms: number | null
  data_quality_score: number | null
  started_at: string
  completed_at: string | null
}

export interface DataDiscoverySession {
  id: string
  owner_id: string
  research_space_id: string | null
  name: string
  current_parameters: AdvancedQueryParameters
  selected_sources: string[]
  tested_sources: string[]
  total_tests_run: number
  successful_tests: number
  is_active: boolean
  created_at: string
  updated_at: string
  last_activity_at: string
}

export interface CreateSessionRequest {
  name?: string
  research_space_id?: string
  initial_parameters?: AdvancedQueryParameters
}

export interface UpdateParametersRequest {
  parameters: AdvancedQueryParameters
}

export interface ExecuteTestRequest {
  catalog_entry_id: string
  timeout_seconds?: number
  parameters?: AdvancedQueryParameters
}

export interface AddToSpaceRequest {
  catalog_entry_id: string
  research_space_id: string
  source_config?: Record<string, unknown>
}

export interface PromoteSourceRequest {
  source_config?: Record<string, unknown>
}

export interface PromoteSourceResponse {
  data_source_id: string
  message: string
}

export interface DiscoveryPreset {
  id: string
  name: string
  description: string | null
  provider: string
  scope: string
  research_space_id: string | null
  parameters: AdvancedQueryParameters
  metadata: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface DiscoverySearchJob {
  id: string
  owner_id: string
  session_id: string | null
  provider: string
  status: string
  query_preview: string
  parameters: AdvancedQueryParameters
  total_results: number
  result_metadata: Record<string, unknown>
  error_message: string | null
  storage_key: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface StorageOperationSummary {
  id: string
  configuration_id: string
  key: string
  status: string
  created_at: string
  metadata: Record<string, unknown>
}

export interface CreatePubmedPresetRequest {
  name: string
  description?: string | null
  scope?: 'user' | 'space'
  research_space_id?: string | null
  parameters: AdvancedQueryParameters
}

export interface RunPubmedSearchRequest {
  session_id?: string
  parameters: AdvancedQueryParameters
}

export interface PubmedDownloadRequest {
  job_id: string
  article_id: string
}
