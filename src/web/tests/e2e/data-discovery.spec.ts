import { expect, test, type Page, type Route } from '@playwright/test'

import type {
  AdvancedQueryParameters,
  DataDiscoverySession,
  DiscoveryPreset,
  DiscoverySearchJob,
  SourceCatalogEntry,
  StorageOperationSummary,
} from '../../lib/types/data-discovery'
import type { ResearchSpaceListResponse } from '../../types/research-space'

interface MockDiscoveryState {
  catalog: SourceCatalogEntry[]
  sessions: DataDiscoverySession[]
  presets: DiscoveryPreset[]
  jobs: Map<string, DiscoverySearchJob>
}

const ISO = () => new Date().toISOString()

function createMockDiscoveryState(): MockDiscoveryState {
  return {
    catalog: [
      {
        id: 'pubmed-source',
        name: 'PubMed Clinical',
        category: 'Articles',
        subcategory: 'PubMed',
        description: 'Deterministic PubMed connector for automation',
        source_type: 'pubmed',
        param_type: 'gene',
        is_active: true,
        requires_auth: false,
        usage_count: 42,
        success_rate: 0.98,
        tags: ['pubmed', 'articles'],
        capabilities: {
          supports_date_range: true,
          supports_publication_types: true,
          supports_language_filter: true,
          supports_sort_options: true,
          supports_additional_terms: true,
          max_results_limit: 500,
        },
      },
    ],
    sessions: [
      {
        id: 'session-1',
        owner_id: 'user-1',
        research_space_id: null,
        name: 'Playwright Session',
        current_parameters: {
          gene_symbol: 'MED13',
          search_term: 'syndrome',
          date_from: null,
          date_to: null,
          publication_types: [],
          languages: [],
          sort_by: 'relevance',
          max_results: 25,
          additional_terms: null,
        },
        selected_sources: ['pubmed-source'],
        tested_sources: [],
        total_tests_run: 0,
        successful_tests: 0,
        is_active: true,
        created_at: ISO(),
        updated_at: ISO(),
        last_activity_at: ISO(),
      },
    ],
    presets: [],
    jobs: new Map(),
  }
}

async function respondJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    body: JSON.stringify(body),
    headers: { 'content-type': 'application/json' },
  })
}

async function setupDataDiscoveryMocks(page: Page, state: MockDiscoveryState) {
  await page.route('**/research-spaces?**', (route) =>
    respondJson(route, {
      spaces: [
        {
          id: 'space-1',
          slug: 'med13',
          name: 'MED13 Research',
          description: 'Primary research space',
          owner_id: 'user-1',
          status: 'active',
          settings: {},
          tags: ['med13'],
          created_at: ISO(),
          updated_at: ISO(),
        },
      ],
      total: 1,
      skip: 0,
      limit: 25,
    } satisfies ResearchSpaceListResponse),
  )

  await page.route('**/data-discovery/catalog**', (route) =>
    respondJson(route, state.catalog),
  )

  await page.route('**/data-discovery/sessions', (route) =>
    respondJson(route, state.sessions),
  )

  await page.route('**/data-discovery/sessions/*/tests', (route) =>
    respondJson(route, []),
  )

  await page.route('**/data-discovery/pubmed/presets**', async (route) => {
    const method = route.request().method().toUpperCase()
    if (method === 'GET') {
      return respondJson(route, state.presets)
    }
    if (method === 'POST') {
      const payload = (await route.request().postDataJSON()) as {
        name: string
        description: string | null
        scope?: string
        parameters: Record<string, unknown>
      }
      const preset: DiscoveryPreset = {
        id: `preset-${state.presets.length + 1}`,
        name: payload.name,
        description: payload.description ?? null,
        provider: 'pubmed',
        scope: payload.scope ?? 'user',
        research_space_id: null,
        parameters: payload.parameters as AdvancedQueryParameters,
        metadata: {},
        created_at: ISO(),
        updated_at: ISO(),
      }
      state.presets.push(preset)
      return respondJson(route, preset, 201)
    }
    return route.fallback()
  })

  await page.route('**/data-discovery/pubmed/search/**', async (route) => {
    const method = route.request().method().toUpperCase()
    const url = new URL(route.request().url())
    if (method === 'POST') {
      const payload = (await route.request().postDataJSON()) as {
        session_id?: string
        parameters: SourceCatalogEntry['capabilities']
      }
      const jobId = `job-${state.jobs.size + 1}`
      const job: DiscoverySearchJob = {
        id: jobId,
        owner_id: 'user-1',
        session_id: payload.session_id ?? null,
        provider: 'pubmed',
        status: 'completed',
        query_preview: 'TP53[Title/Abstract]',
        parameters: payload.parameters as AdvancedQueryParameters,
        total_results: 1,
        result_metadata: { article_ids: ['12345'] },
        error_message: null,
        storage_key: null,
        created_at: ISO(),
        updated_at: ISO(),
        completed_at: ISO(),
      }
      state.jobs.set(jobId, job)
      return respondJson(route, job, 202)
    }
    if (method === 'GET') {
      const jobId = url.pathname.split('/').pop() ?? ''
      const job = state.jobs.get(jobId)
      if (!job) {
        return respondJson(route, { detail: 'Job not found' }, 404)
      }
      return respondJson(route, job)
    }
    return route.fallback()
  })

  await page.route('**/data-discovery/pubmed/download', async (route) => {
    const payload = (await route.request().postDataJSON()) as {
      job_id: string
      article_id: string
    }
    if (!state.jobs.has(payload.job_id)) {
      return respondJson(route, { detail: 'Job not found' }, 404)
    }
    const record: StorageOperationSummary = {
      id: `op-${payload.article_id}`,
      configuration_id: 'config-1',
      key: `storage/pubmed/${payload.article_id}.pdf`,
      status: 'success',
      created_at: ISO(),
      metadata: {},
    }
    return respondJson(route, record)
  })
}

test.describe('Data discovery workflows', () => {
  test('supports parameter editing, presets, and PDF automation', async ({ page }) => {
    const state = createMockDiscoveryState()
    await setupDataDiscoveryMocks(page, state)

    await page.goto('/data-discovery')
    await expect(page.getByRole('heading', { name: /PubMed PDF Automation/i })).toBeVisible()

    const geneInput = page.getByLabel('Gene Symbol')
    await geneInput.fill('')
    await geneInput.type('TP53')
    await expect(page.getByText(/TP53\[Title\/Abstract]/i)).toBeVisible()

    await page.getByRole('button', { name: 'Manage Presets' }).click()
    await page.getByLabel('Preset Name').fill('TP53 Focus')
    await page.getByRole('button', { name: 'Save Preset' }).click()
    await expect(page.getByText('TP53 Focus')).toBeVisible()
    await page.keyboard.press('Escape')

    await page.getByRole('button', { name: 'Download PubMed PDFs' }).click()
    await expect(
      page.getByText(/Most recent PDF stored to storage\/pubmed\/12345\.pdf/i),
    ).toBeVisible()
  })
})
