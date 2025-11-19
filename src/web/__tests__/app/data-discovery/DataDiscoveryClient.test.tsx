"use client"

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DataDiscoveryClient from '@/app/(dashboard)/data-discovery/data-discovery-client'
import type {
  AdvancedQueryParameters,
  DiscoveryPreset,
  DiscoverySearchJob,
  SourceCatalogEntry,
  StorageOperationSummary,
} from '@/lib/types/data-discovery'

const mockUseSourceCatalog = jest.fn()
const mockUseDataDiscoverySessions = jest.fn()
const mockUseSessionTestResults = jest.fn()
const mockUseCreateSession = jest.fn()
const mockUseToggleSelection = jest.fn()
const mockUseExecuteTest = jest.fn()
const mockUseAddToSpace = jest.fn()
const mockUseSetSelections = jest.fn()
const mockUsePubmedPresets = jest.fn()
const mockUseCreatePubmedPreset = jest.fn()
const mockUseDeletePubmedPreset = jest.fn()
const mockUseRunPubmedSearch = jest.fn()
const mockUseDownloadPubmedPdf = jest.fn()
const mockUsePubmedSearchJob = jest.fn()

const defaultCatalogEntry: SourceCatalogEntry = {
  id: 'pubmed-source',
  name: 'PubMed Search',
  description: 'Primary PubMed connector',
  category: 'Articles',
  subcategory: 'PubMed',
  tags: ['pubmed', 'articles'],
  param_type: 'gene',
  source_type: 'pubmed',
  is_active: true,
  requires_auth: false,
  usage_count: 0,
  success_rate: 1,
  capabilities: {
    supports_date_range: true,
    supports_publication_types: true,
    supports_language_filter: true,
    supports_sort_options: true,
    supports_additional_terms: true,
    max_results_limit: 500,
    supported_storage_use_cases: [],
    supports_variation_type: false,
    supports_clinical_significance: false,
    supports_review_status: false,
    supports_organism: false,
  },
}

const baseParameters: AdvancedQueryParameters = {
  gene_symbol: 'MED13L',
  search_term: 'atrial defect',
  date_from: null,
  date_to: null,
  publication_types: [],
  languages: [],
  sort_by: 'relevance',
  max_results: 25,
  additional_terms: null,
}

jest.mock('next/dynamic', () => () => () => null)

jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}))

jest.mock('@/components/space-context-provider', () => ({
  useSpaceContext: () => ({ currentSpaceId: null }),
}))

jest.mock('@/lib/state/discovery-session-sync', () => ({
  syncDiscoverySessionState: jest.fn(() => ({
    nextSessionId: null,
    nextParameters: null,
    nextSelectedSources: [],
    shouldCreateSession: false,
  })),
}))

const { syncDiscoverySessionState: syncDiscoverySessionStateMock } = jest.requireMock(
  '@/lib/state/discovery-session-sync',
) as {
  syncDiscoverySessionState: jest.Mock
}

jest.mock('@/lib/queries/data-discovery', () => ({
  useSourceCatalog: (...args: unknown[]) => mockUseSourceCatalog(...args),
  useDataDiscoverySessions: (...args: unknown[]) => mockUseDataDiscoverySessions(...args),
  useSessionTestResults: (...args: unknown[]) => mockUseSessionTestResults(...args),
  useCreateDataDiscoverySession: (...args: unknown[]) => mockUseCreateSession(...args),
  useToggleDataDiscoverySourceSelection: (...args: unknown[]) => mockUseToggleSelection(...args),
  useExecuteDataDiscoveryTest: (...args: unknown[]) => mockUseExecuteTest(...args),
  useAddDiscoverySourceToSpace: (...args: unknown[]) => mockUseAddToSpace(...args),
  useSetDataDiscoverySelections: (...args: unknown[]) => mockUseSetSelections(...args),
  usePubmedPresets: (...args: unknown[]) => mockUsePubmedPresets(...args),
  useCreatePubmedPreset: (...args: unknown[]) => mockUseCreatePubmedPreset(...args),
  useDeletePubmedPreset: (...args: unknown[]) => mockUseDeletePubmedPreset(...args),
  useRunPubmedSearch: (...args: unknown[]) => mockUseRunPubmedSearch(...args),
  useDownloadPubmedPdf: (...args: unknown[]) => mockUseDownloadPubmedPdf(...args),
  usePubmedSearchJob: (...args: unknown[]) => mockUsePubmedSearchJob(...args),
}))

describe('DataDiscoveryClient presets and automation', () => {
  const originalBetaFlag = process.env.NEXT_PUBLIC_STORAGE_DASHBOARD_BETA
  let createPresetMutation: { mutateAsync: jest.Mock; isPending: boolean }
  let deletePresetMutation: { mutateAsync: jest.Mock; isPending: boolean }
  let runSearchMutation: { mutateAsync: jest.Mock; isPending: boolean }
  let downloadPdfMutation: { mutateAsync: jest.Mock; isPending: boolean }
  beforeEach(() => {
    jest.clearAllMocks()
    process.env.NEXT_PUBLIC_STORAGE_DASHBOARD_BETA = 'true'
    syncDiscoverySessionStateMock.mockReturnValue({
      nextSessionId: null,
      nextParameters: null,
      nextSelectedSources: [],
      shouldCreateSession: false,
    })
    mockUseSourceCatalog.mockReturnValue({
      data: [defaultCatalogEntry],
      isLoading: false,
    })
    mockUseDataDiscoverySessions.mockReturnValue({
      data: [],
      isSuccess: true,
      isLoading: false,
      refetch: jest.fn(),
    })
    mockUseSessionTestResults.mockReturnValue({
      data: [],
      isLoading: false,
    })
    mockUseCreateSession.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
      isError: false,
    })
    mockUseToggleSelection.mockReturnValue({ mutate: jest.fn(), isPending: false })
    mockUseExecuteTest.mockReturnValue({ mutateAsync: jest.fn(), isPending: false })
    mockUseAddToSpace.mockReturnValue({ mutateAsync: jest.fn(), isPending: false })
    mockUseSetSelections.mockReturnValue({ mutate: jest.fn(), isPending: false })
    mockUsePubmedPresets.mockReturnValue({ data: [], isLoading: false })

    createPresetMutation = {
      mutateAsync: jest.fn().mockResolvedValue({
        id: 'preset-new',
        research_space_id: null,
        provider: 'pubmed',
        name: 'Saved preset',
        description: null,
        scope: 'user',
        parameters: baseParameters,
        metadata: {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } satisfies DiscoveryPreset),
      isPending: false,
    }
    deletePresetMutation = { mutateAsync: jest.fn(), isPending: false }
    mockUseCreatePubmedPreset.mockReturnValue(createPresetMutation)
    mockUseDeletePubmedPreset.mockReturnValue(deletePresetMutation)

    runSearchMutation = {
      mutateAsync: jest
        .fn()
        .mockResolvedValue({
          id: 'job-1234',
          owner_id: 'user-1',
          session_id: 'session-1',
          provider: 'pubmed',
          status: 'completed',
          query_preview: 'MED13 search',
          parameters: baseParameters,
          total_results: 1,
          result_metadata: { article_ids: ['12345'] },
          error_message: null,
          storage_key: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
        } satisfies DiscoverySearchJob),
      isPending: false,
    }
    mockUseRunPubmedSearch.mockReturnValue(runSearchMutation)

    downloadPdfMutation = {
      mutateAsync: jest.fn().mockResolvedValue({
        id: 'op-1',
        configuration_id: 'cfg-1',
        key: 'storage/pubmed/latest.pdf',
        status: 'success',
        created_at: new Date().toISOString(),
        metadata: {},
      } satisfies StorageOperationSummary),
      isPending: false,
    }
    mockUseDownloadPubmedPdf.mockReturnValue(downloadPdfMutation)
    mockUsePubmedSearchJob.mockImplementation((jobId: string | null) => ({
      data: jobId
        ? {
            id: jobId,
            owner_id: 'user-1',
            session_id: 'session-1',
            provider: 'pubmed',
            status: 'completed',
            query_preview: 'MED13 search',
            parameters: baseParameters,
            total_results: 1,
            result_metadata: { article_ids: ['12345'] },
            error_message: null,
            storage_key: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            completed_at: new Date().toISOString(),
          }
        : null,
    }))
  })

  afterAll(() => {
    if (originalBetaFlag === undefined) {
      delete process.env.NEXT_PUBLIC_STORAGE_DASHBOARD_BETA
    } else {
      process.env.NEXT_PUBLIC_STORAGE_DASHBOARD_BETA = originalBetaFlag
    }
  })

  function renderClient(selectedSources: string[] = []) {
    return render(
      <DataDiscoveryClient
        initialSessionId="session-1"
        initialParameters={baseParameters}
        initialSelectedSources={selectedSources}
      />,
    )
  }

  it('saves a PubMed preset through the dialog', async () => {
    const user = userEvent.setup()
    renderClient(['pubmed-source'])

    await user.click(screen.getByRole('button', { name: /Manage Presets/i }))
    await user.type(screen.getByLabelText(/Preset Name/i), 'TP53 Focus')
    await user.type(screen.getByLabelText(/Description/i), 'Focus on TP53 evidence')
    await user.click(screen.getByRole('button', { name: /Save Preset/i }))

    await waitFor(() => {
      expect(createPresetMutation.mutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'TP53 Focus',
          description: 'Focus on TP53 evidence',
          scope: 'user',
        }),
      )
    })
  })

})
