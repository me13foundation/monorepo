import { apiClient, authHeaders } from './client'
import type { PaginatedResponse } from '@/types/generated'
import type { ExtractionDocumentResponse, PublicationExtraction } from '@/types/extractions'

export interface ExtractionListParams {
  page?: number
  per_page?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  publication_id?: string | number
  source_id?: string
  ingestion_job_id?: string
  status?: string
}

export async function fetchExtractions(
  params: ExtractionListParams = {},
  token?: string,
): Promise<PaginatedResponse<PublicationExtraction>> {
  if (!token) {
    throw new Error('Authentication token is required for fetchExtractions')
  }

  const response = await apiClient.get<PaginatedResponse<PublicationExtraction>>('/extractions', {
    params,
    ...authHeaders(token),
  })

  return response.data
}

export async function fetchExtractionDocumentUrl(
  extractionId: string,
  token?: string,
): Promise<ExtractionDocumentResponse> {
  if (!token) {
    throw new Error('Authentication token is required for fetchExtractionDocumentUrl')
  }

  const response = await apiClient.get<ExtractionDocumentResponse>(
    `/extractions/${extractionId}/document-url`,
    authHeaders(token),
  )

  return response.data
}
