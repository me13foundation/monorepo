import type { DataSourceListParams } from '@/lib/api/data-sources'

/**
 * Query key factory for data sources
 * Follows the same pattern as other query key factories
 */
export const dataSourceKeys = {
  all: ['data-sources'] as const,
  lists: () => [...dataSourceKeys.all, 'list'] as const,
  list: (params: DataSourceListParams) =>
    [...dataSourceKeys.lists(), params] as const,
  space: (spaceId: string, params?: Omit<DataSourceListParams, 'research_space_id'>) =>
    [...dataSourceKeys.all, 'space', spaceId, params] as const,
  detail: (id: string) => [...dataSourceKeys.all, 'detail', id] as const,
  availability: (id: string) => [...dataSourceKeys.all, 'availability', id] as const,
  adminCatalog: () => [...dataSourceKeys.all, 'catalog', 'admin'] as const,
  adminCatalogAvailability: () => [...dataSourceKeys.all, 'catalog', 'availability', 'admin'] as const,
}
