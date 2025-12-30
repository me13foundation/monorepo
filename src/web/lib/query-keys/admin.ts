export const adminKeys = {
  root: ['admin'] as const,
  sourceCatalog: () => [...adminKeys.root, 'source-catalog'] as const,
  spaceSourceAvailability: (spaceId: string) =>
    [...adminKeys.root, 'space-source-availability', spaceId] as const,
}

