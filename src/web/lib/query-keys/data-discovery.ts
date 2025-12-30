type CatalogQueryParams = {
  category?: string
  search?: string
  research_space_id?: string
}

export const dataDiscoveryKeys = {
  all: ['data-discovery'] as const,
  catalog: (params?: CatalogQueryParams) =>
    [...dataDiscoveryKeys.all, 'catalog', params] as const,
  sessions: () => [...dataDiscoveryKeys.all, 'sessions'] as const,
  sessionTests: (sessionId: string) => [...dataDiscoveryKeys.sessions(), 'tests', sessionId] as const,
  pubmedPresets: (params?: { research_space_id?: string }) =>
    [...dataDiscoveryKeys.all, 'pubmed-presets', params] as const,
  pubmedSearchJob: (jobId: string) => [...dataDiscoveryKeys.all, 'pubmed-search', jobId] as const,
}
