"use client"

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'
import {
  createSpaceDiscoverySession,
  deleteSpaceDiscoverySession,
  fetchSpaceDiscoverySessions,
  fetchSpaceSourceCatalog,
  promoteDiscoverySourceInSpace,
  setSpaceDiscoverySelections,
  toggleSpaceDiscoverySourceSelection,
  updateSpaceDiscoverySessionParameters,
  addDiscoverySourceToSpace,
} from '@/lib/api/space-discovery'
import type {
  CreateSessionRequest,
  DataDiscoverySession,
  PromoteSourceRequest,
  SourceCatalogEntry,
  UpdateParametersRequest,
} from '@/lib/types/data-discovery'
import { spaceDiscoveryKeys } from '@/lib/query-keys/space-discovery'
import { dataSourceKeys } from '@/lib/query-keys/data-sources'

function useAuthToken() {
  const { data: session } = useSession()
  return session?.user?.access_token
}

export function useSpaceSourceCatalog(spaceId: string | null, filters?: { category?: string; search?: string }) {
  const token = useAuthToken()
  return useQuery<SourceCatalogEntry[]>({
    queryKey: spaceId ? spaceDiscoveryKeys.catalog(spaceId, filters) : ['space-discovery', 'catalog', 'pending'],
    queryFn: () => {
      if (!spaceId) {
        throw new Error('Space ID is required to fetch space source catalog')
      }
      return fetchSpaceSourceCatalog(spaceId, token, filters)
    },
    enabled: Boolean(token && spaceId),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

export function useSpaceDiscoverySessions(spaceId: string | null) {
  const token = useAuthToken()
  return useQuery<DataDiscoverySession[]>({
    queryKey: spaceId ? spaceDiscoveryKeys.sessions(spaceId) : ['space-discovery', 'sessions', 'pending'],
    queryFn: () => {
      if (!spaceId) {
        throw new Error('Space ID is required to fetch discovery sessions')
      }
      return fetchSpaceDiscoverySessions(spaceId, token)
    },
    enabled: Boolean(token && spaceId),
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

export function useCreateSpaceDiscoverySession(spaceId: string | null) {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateSessionRequest) => {
      if (!spaceId) {
        throw new Error('Space ID is required to create a discovery session')
      }
      return createSpaceDiscoverySession(spaceId, payload, token)
    },
    onSuccess: (_, __, context) => {
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: spaceDiscoveryKeys.sessions(spaceId) })
      }
      return context
    },
  })
}

export function useUpdateSpaceDiscoverySessionParameters(spaceId: string | null) {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, payload }: { sessionId: string; payload: UpdateParametersRequest }) => {
      if (!spaceId) {
        throw new Error('Space ID is required to update session parameters')
      }
      return updateSpaceDiscoverySessionParameters(spaceId, sessionId, payload, token)
    },
    onSuccess: (session) => {
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: spaceDiscoveryKeys.sessions(spaceId) })
      }
      return session
    },
  })
}

export function useToggleSpaceDiscoverySourceSelection(spaceId: string | null) {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, catalogEntryId }: { sessionId: string; catalogEntryId: string }) => {
      if (!spaceId) {
        throw new Error('Space ID is required to toggle source selection')
      }
      return toggleSpaceDiscoverySourceSelection(spaceId, sessionId, catalogEntryId, token)
    },
    onSuccess: (session) => {
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: spaceDiscoveryKeys.sessions(spaceId) })
      }
      return session
    },
  })
}

export function useSetSpaceDiscoverySelections(spaceId: string | null) {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, sourceIds }: { sessionId: string; sourceIds: string[] }) => {
      if (!spaceId) {
        throw new Error('Space ID is required to update session selections')
      }
      return setSpaceDiscoverySelections(spaceId, sessionId, sourceIds, token)
    },
    onSuccess: (session) => {
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: spaceDiscoveryKeys.sessions(spaceId) })
      }
      return session
    },
  })
}

export function useDeleteSpaceDiscoverySession(spaceId: string | null) {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => {
      if (!spaceId) {
        throw new Error('Space ID is required to delete a discovery session')
      }
      return deleteSpaceDiscoverySession(spaceId, sessionId, token)
    },
    onSuccess: () => {
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: spaceDiscoveryKeys.sessions(spaceId) })
      }
    },
  })
}

export function usePromoteSpaceDiscoverySource(spaceId: string | null) {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      sessionId,
      catalogEntryId,
      payload,
    }: {
      sessionId: string
      catalogEntryId: string
      payload?: PromoteSourceRequest
    }) => {
      if (!spaceId) {
        throw new Error('Space ID is required to promote a discovery source')
      }
      return promoteDiscoverySourceInSpace(spaceId, sessionId, catalogEntryId, payload ?? {}, token)
    },
    onSuccess: () => {
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: spaceDiscoveryKeys.sessions(spaceId) })
        queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(spaceId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() })
      }
    },
  })
}

export function useAddDiscoverySourceToSpace() {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      sessionId,
      catalogEntryId,
      researchSpaceId,
      sourceConfig,
      requestedBy,
    }: {
      sessionId: string
      catalogEntryId: string
      researchSpaceId: string
      sourceConfig?: Record<string, unknown>
      requestedBy?: string
    }) =>
      addDiscoverySourceToSpace(sessionId, catalogEntryId, researchSpaceId, token, {
        ...sourceConfig,
        requested_by: requestedBy,
      }),
    onSuccess: (_dataSourceId, variables) => {
      // Invalidate and explicitly refetch queries to update the UI immediately
      queryClient.invalidateQueries({ 
        queryKey: dataSourceKeys.space(variables.researchSpaceId),
      })
      // Explicitly refetch to ensure immediate update - this will refetch all matching queries
      queryClient.refetchQueries({ 
        queryKey: dataSourceKeys.space(variables.researchSpaceId),
        type: 'active',
      })
      queryClient.invalidateQueries({ 
        queryKey: dataSourceKeys.lists(),
      })
    },
  })
}
