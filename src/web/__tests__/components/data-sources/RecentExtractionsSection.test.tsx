import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RecentExtractionsSection } from '@/components/data-sources/RecentExtractionsSection'
import type { PublicationExtraction } from '@/types/extractions'
import type { PaginatedResponse } from '@/types/generated'

import {
  fetchExtractionDocumentUrlAction,
  fetchRecentExtractionsAction,
} from '@/app/actions/extractions'

jest.mock('@/app/actions/extractions', () => ({
  fetchExtractionDocumentUrlAction: jest.fn(),
  fetchRecentExtractionsAction: jest.fn(),
}))

const mockExtraction: PublicationExtraction = {
  id: 'extraction-1',
  publication_id: 1,
  pubmed_id: '123456',
  source_id: 'source-1',
  ingestion_job_id: 'job-1',
  queue_item_id: 'queue-1',
  status: 'completed',
  extraction_version: 1,
  processor_name: 'rule_based',
  processor_version: '1.0',
  text_source: 'title_abstract',
  document_reference: 'extractions/source-1/doc.txt',
  facts: [],
  metadata: {},
  extracted_at: new Date().toISOString(),
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

const mockResponse: PaginatedResponse<PublicationExtraction> = {
  items: [mockExtraction],
  total: 1,
  page: 1,
  per_page: 5,
  total_pages: 1,
  has_next: false,
  has_prev: false,
}

describe('RecentExtractionsSection', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders recent extractions and opens document links', async () => {
    const openSpy = jest.spyOn(window, 'open').mockImplementation(() => null)
    ;(fetchRecentExtractionsAction as jest.Mock).mockResolvedValue({
      success: true,
      data: mockResponse,
    })
    ;(fetchExtractionDocumentUrlAction as jest.Mock).mockResolvedValue({
      success: true,
      data: {
        extraction_id: mockExtraction.id,
        document_reference: mockExtraction.document_reference,
        url: 'https://example.com/document.txt',
      },
    })

    render(<RecentExtractionsSection sourceId="source-1" open={true} />)

    await waitFor(() => {
      expect(fetchRecentExtractionsAction).toHaveBeenCalledWith('source-1', 5)
    })

    expect(screen.getByText('Recent extractions')).toBeInTheDocument()
    expect(screen.getByText('completed')).toBeInTheDocument()
    expect(screen.getByText('title abstract')).toBeInTheDocument()

    const openButton = screen.getByRole('button', { name: /open/i })
    await userEvent.click(openButton)

    await waitFor(() => {
      expect(fetchExtractionDocumentUrlAction).toHaveBeenCalledWith(mockExtraction.id)
    })
    expect(openSpy).toHaveBeenCalledWith(
      'https://example.com/document.txt',
      '_blank',
      'noopener,noreferrer',
    )
  })
})
