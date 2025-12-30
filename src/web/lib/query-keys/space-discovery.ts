type CatalogFilters = {
  category?: string
  search?: string
}

export const spaceDiscoveryKeys = {
  all: ['space-discovery'] as const,
  catalog: (spaceId: string, filters?: CatalogFilters) =>
    [...spaceDiscoveryKeys.all, spaceId, 'catalog', filters] as const,
  sessions: (spaceId: string) => [...spaceDiscoveryKeys.all, spaceId, 'sessions'] as const,
}

