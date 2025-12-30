export const researchSpaceKeys = {
  all: ['research-spaces'] as const,
  lists: () => [...researchSpaceKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) =>
    [...researchSpaceKeys.lists(), filters] as const,
  details: () => [...researchSpaceKeys.all, 'detail'] as const,
  detail: (id: string) => [...researchSpaceKeys.details(), id] as const,
  membership: (spaceId: string, userId: string) =>
    [...researchSpaceKeys.detail(spaceId), 'membership', userId] as const,
  members: (spaceId: string) => [...researchSpaceKeys.detail(spaceId), 'members'] as const,
  pendingInvitations: () => [...researchSpaceKeys.all, 'pending-invitations'] as const,
  curation: (spaceId: string) => [...researchSpaceKeys.detail(spaceId), 'curation'] as const,
  curationStats: (spaceId: string) => [...researchSpaceKeys.curation(spaceId), 'stats'] as const,
  curationQueue: (spaceId: string, filters?: Record<string, unknown>) =>
    [...researchSpaceKeys.curation(spaceId), 'queue', filters] as const,
}
