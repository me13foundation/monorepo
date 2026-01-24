"use server"

import { fetchExtractionDocumentUrl, fetchExtractions } from '@/lib/api/extractions'
import { getActionErrorMessage, requireAccessToken } from '@/app/actions/action-utils'
import type { ExtractionDocumentResponse, PublicationExtraction } from '@/types/extractions'
import type { PaginatedResponse } from '@/types/generated'

type ActionResult<T> = { success: true; data: T } | { success: false; error: string }

const isE2E = process.env.E2E_TEST_MODE === 'playwright'

const buildE2EExtraction = (): PublicationExtraction => {
  const now = new Date().toISOString()
  return {
    id: 'e2e-extraction-1',
    publication_id: 101,
    pubmed_id: '123456',
    source_id: 'e2e-source',
    ingestion_job_id: 'e2e-job',
    queue_item_id: 'e2e-queue',
    status: 'completed',
    extraction_version: 1,
    processor_name: 'rule_based',
    processor_version: '1.0',
    text_source: 'title_abstract',
    document_reference: 'extractions/e2e/doc.txt',
    facts: [],
    metadata: {},
    extracted_at: now,
    created_at: now,
    updated_at: now,
  }
}

export async function fetchRecentExtractionsAction(
  sourceId: string,
  limit = 5,
): Promise<ActionResult<PaginatedResponse<PublicationExtraction>>> {
  if (isE2E) {
    const extraction = buildE2EExtraction()
    return {
      success: true,
      data: {
        items: [extraction],
        total: 1,
        page: 1,
        per_page: limit,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      },
    }
  }

  try {
    const token = await requireAccessToken()
    const response = await fetchExtractions(
      {
        source_id: sourceId,
        page: 1,
        per_page: limit,
        sort_by: 'extracted_at',
        sort_order: 'desc',
      },
      token,
    )
    return { success: true, data: response }
  } catch (error: unknown) {
    if (process.env.NODE_ENV !== 'test') {
      console.error('[ServerAction] fetchRecentExtractions failed:', error)
    }
    return {
      success: false,
      error: getActionErrorMessage(error, 'Failed to load extractions'),
    }
  }
}

export async function fetchExtractionDocumentUrlAction(
  extractionId: string,
): Promise<ActionResult<ExtractionDocumentResponse>> {
  if (isE2E) {
    return {
      success: true,
      data: {
        extraction_id: extractionId,
        document_reference: 'extractions/e2e/doc.txt',
        url: 'https://example.com/extractions/e2e-doc.txt',
      },
    }
  }

  try {
    const token = await requireAccessToken()
    const response = await fetchExtractionDocumentUrl(extractionId, token)
    return { success: true, data: response }
  } catch (error: unknown) {
    if (process.env.NODE_ENV !== 'test') {
      console.error('[ServerAction] fetchExtractionDocumentUrl failed:', error)
    }
    return {
      success: false,
      error: getActionErrorMessage(error, 'Unable to fetch extraction document'),
    }
  }
}
