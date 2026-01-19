// TypeScript types for Data Source Discovery (aligned with generated DTOs)

import type {
  AddToSpaceRequest as AddToSpaceRequestModel,
  AdvancedQueryParametersModel,
  CreatePubmedPresetRequestModel,
  CreateSessionRequest as CreateSessionRequestModel,
  DataDiscoverySessionResponse,
  DiscoveryPresetResponse,
  DiscoverySearchJobResponse,
  ExecuteTestRequest as ExecuteTestRequestModel,
  PubmedDownloadRequestModel,
  QueryParametersModel,
  QueryTestResultResponse,
  RunPubmedSearchRequestModel,
  SourceCatalogEntry as GeneratedSourceCatalogEntry,
  StorageOperationResponse,
  UpdateParametersRequest as UpdateParametersRequestModel,
} from '@/types/generated'

export type QueryParameterType = 'gene' | 'term' | 'gene_and_term' | 'none' | 'api'

export type TestResultStatus =
  | 'pending'
  | 'success'
  | 'error'
  | 'timeout'
  | 'validation_failed'

export type StorageUseCase = 'pdf' | 'export' | 'raw_source' | 'backup'

export type QueryParameters = QueryParametersModel

export type PubmedSortOption =
  | 'relevance'
  | 'publication_date'
  | 'author'
  | 'journal'
  | 'title'

export type AdvancedQueryParameters = AdvancedQueryParametersModel

export interface QueryParameterCapabilities {
  supports_date_range: boolean
  supports_publication_types: boolean
  supports_language_filter: boolean
  supports_sort_options: boolean
  supports_additional_terms: boolean
  max_results_limit: number

  supported_storage_use_cases: StorageUseCase[]

  supports_variation_type: boolean
  supports_clinical_significance: boolean
  supports_review_status: boolean
  supports_organism: boolean
}

export type SourceCatalogEntry = Omit<GeneratedSourceCatalogEntry, 'capabilities'> & {
  capabilities: QueryParameterCapabilities
}

export type QueryTestResult = QueryTestResultResponse

export type DataDiscoverySession = DataDiscoverySessionResponse

export type CreateSessionRequest = CreateSessionRequestModel

export type UpdateParametersRequest = UpdateParametersRequestModel

export type ExecuteTestRequest = ExecuteTestRequestModel

export type AddToSpaceRequest = AddToSpaceRequestModel

export interface PromoteSourceRequest {
  source_config?: Record<string, unknown>
}

export interface PromoteSourceResponse {
  data_source_id: string
  message: string
}

export type DiscoveryPreset = DiscoveryPresetResponse

export type DiscoverySearchJob = DiscoverySearchJobResponse

export type StorageOperationSummary = StorageOperationResponse

export type CreatePubmedPresetRequest = CreatePubmedPresetRequestModel

export type RunPubmedSearchRequest = RunPubmedSearchRequestModel

export type PubmedDownloadRequest = PubmedDownloadRequestModel
