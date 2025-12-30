export const storageKeys = {
  root: ['storage'] as const,
  list: (token?: string, page = 1, perPage = 25, includeDisabled = false) =>
    [...storageKeys.root, 'list', token, page, perPage, includeDisabled] as const,
  configuration: (id: string, token?: string) => [...storageKeys.root, 'configuration', id, token] as const,
  metrics: (id: string, token?: string) => [...storageKeys.root, 'metrics', id, token] as const,
  health: (id: string, token?: string) => [...storageKeys.root, 'health', id, token] as const,
  operations: (id: string, limit: number, token?: string) =>
    [...storageKeys.root, 'operations', id, limit, token] as const,
  stats: (token?: string) => [...storageKeys.root, 'stats', token] as const,
}
