export const dashboardKeys = {
  root: ['dashboard'] as const,
  stats: (token: string) => [...dashboardKeys.root, 'stats', token] as const,
  activities: (limit: number, token: string) =>
    [...dashboardKeys.root, 'activities', limit, token] as const,
}
