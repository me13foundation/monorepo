"use client"

import { useMutation, useQuery, useQueryClient, type UseQueryResult } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'
import {
  acceptInvitation,
  createResearchSpace,
  deleteResearchSpace,
  fetchPendingInvitations,
  fetchResearchSpace,
  fetchResearchSpaceBySlug,
  fetchResearchSpaces,
  fetchMyMembership,
  fetchSpaceCurationQueue,
  fetchSpaceCurationStats,
  fetchSpaceMembers,
  inviteMember,
  removeMember,
  updateMemberRole,
  updateResearchSpace,
  type CurationQueueResponse,
  type CurationStats,
} from '@/lib/api/research-spaces'
import type {
  CreateSpaceRequest,
  InviteMemberRequest,
  MembershipListResponse,
  ResearchSpace,
  ResearchSpaceListResponse,
  ResearchSpaceMembership,
  UpdateMemberRoleRequest,
  UpdateSpaceRequest,
} from '@/types/research-space'
import { SpaceStatus } from '@/types/research-space'
import { researchSpaceKeys } from '@/lib/query-keys/research-spaces'

// Helper to get token from session
function useAuthToken() {
  const { data: session, status } = useSession()
  const token = session?.user?.access_token
  
  // Validate token format (JWT should have 3 parts)
  const isValidToken = token && 
    typeof token === 'string' && 
    token.length > 0 &&
    token.split('.').length === 3
  
  // Only consider authenticated if:
  // 1. Session status is authenticated (not loading, not unauthenticated)
  // 2. Token exists and is a valid JWT format
  // 3. Session has user data
  // 4. We're not on an auth page (additional safety check)
  const isAuthenticated =
    status === 'authenticated' &&
    isValidToken &&
    !!session?.user &&
    !!session?.user?.access_token
  
  // Debug logging in development
  if (process.env.NODE_ENV === 'development') {
    if (status === 'authenticated' && !isValidToken) {
      const tokenPreview = typeof token === 'string'
        ? `${token.substring(0, 20)}...${token.substring(Math.max(0, token.length - 20))}`
        : token !== undefined
          ? JSON.stringify(token)
          : 'null'
      const partsCount = typeof token === 'string' ? token.split('.').length : 0
      console.warn('[useAuthToken] Invalid token format', {
        status,
        hasToken: !!token,
        tokenType: typeof token,
        tokenLength: typeof token === 'string' ? token.length : 0,
        tokenPreview,
        partsCount,
        sessionKeys: session?.user ? Object.keys(session.user) : [],
        hasUser: !!session?.user,
        hasAccessToken: !!session?.user?.access_token,
      })
    }
  }
  
  return { token: isValidToken ? token : undefined, isAuthenticated, status }
}

// Research Spaces queries

export function useResearchSpaces(
  params?: { skip?: number; limit?: number; owner_id?: string },
  options?: {
    enabled?: boolean
    initialData?: ResearchSpaceListResponse
  }
): UseQueryResult<ResearchSpaceListResponse, Error> {
  const { token, isAuthenticated, status } = useAuthToken()

  // Strict check: only enable if we have a valid JWT token
  const hasValidToken = !!(
    token &&
    typeof token === 'string' &&
    token.length > 0 &&
    token.split('.').length === 3
  )

  // Additional check: disable on auth pages to prevent 401 errors
  // This is safe to do as it doesn't violate Rules of Hooks
  const isOnAuthPage = typeof window !== 'undefined' &&
    (window.location.pathname.startsWith('/auth') ||
     window.location.pathname === '/' ||
     window.location.pathname === '/login' ||
     window.location.pathname === '/register' ||
     window.location.pathname === '/forgot-password')

  const computedEnable = Boolean(
    status !== 'loading' &&
      status === 'authenticated' &&
      isAuthenticated &&
      hasValidToken &&
      !isOnAuthPage
  )
  const shouldEnable = options?.enabled ?? computedEnable

  return useQuery<ResearchSpaceListResponse, Error, ResearchSpaceListResponse>({
    queryKey: researchSpaceKeys.list(params),
    queryFn: async () => {
      // Double-check token before making request
      if (!token || typeof token !== 'string' || token.length === 0) {
        throw new Error('No authentication token available')
      }
      // Validate JWT format
      if (token.split('.').length !== 3) {
        throw new Error('Invalid token format')
      }
      return fetchResearchSpaces(params, token)
    },
    // Only enable query when we have a valid authenticated session with a proper JWT token AND not on auth pages
    enabled: shouldEnable,
    initialData: options?.initialData,
    initialDataUpdatedAt: options?.initialData ? Date.now() : undefined,
    retry: false,
    // Auth errors are handled by the API interceptor
    staleTime: 10 * 60 * 1000, // 10 minutes - research spaces rarely change
    gcTime: 30 * 60 * 1000, // 30 minutes - keep in cache longer
  })
}

export function useResearchSpace(spaceId: string): UseQueryResult<ResearchSpace, Error> {
  const { token, isAuthenticated, status } = useAuthToken()
  const queryEnabled = Boolean(status !== 'loading' && isAuthenticated && spaceId && token)

  return useQuery<ResearchSpace, Error, ResearchSpace>({
    queryKey: researchSpaceKeys.detail(spaceId),
    queryFn: async () => {
      if (!token) throw new Error('No authentication token available')
      return fetchResearchSpace(spaceId, token)
    },
    enabled: queryEnabled,
    retry: false,
    // Auth errors are handled by the API interceptor
    staleTime: 5 * 60 * 1000, // 5 minutes - space details change infrequently
    gcTime: 15 * 60 * 1000, // 15 minutes - keep in cache
  })
}

export function useResearchSpaceBySlug(slug: string): UseQueryResult<ResearchSpace, Error> {
  const { token, isAuthenticated, status } = useAuthToken()
  const queryEnabled = Boolean(status !== 'loading' && isAuthenticated && slug && token)

  return useQuery<ResearchSpace, Error, ResearchSpace>({
    queryKey: [...researchSpaceKeys.details(), 'slug', slug],
    queryFn: async () => {
      if (!token) throw new Error('No authentication token available')
      return fetchResearchSpaceBySlug(slug, token)
    },
    enabled: queryEnabled,
    retry: false,
    // Auth errors are handled by the API interceptor
  })
}

export function useSpaceMembers(spaceId: string, params?: { skip?: number; limit?: number }): UseQueryResult<MembershipListResponse, Error> {
  const { token, isAuthenticated, status } = useAuthToken()
  const queryEnabled = Boolean(status !== 'loading' && isAuthenticated && spaceId && token)

  return useQuery<MembershipListResponse, Error, MembershipListResponse>({
    queryKey: researchSpaceKeys.members(spaceId),
    queryFn: async () => {
      if (!token) throw new Error('No authentication token available')
      return fetchSpaceMembers(spaceId, params, token)
    },
    enabled: queryEnabled,
    retry: false,
    // Auth errors are handled by the API interceptor
    staleTime: 5 * 60 * 1000, // 5 minutes - members change infrequently
    gcTime: 15 * 60 * 1000, // 15 minutes - keep in cache
  })
}

export function useSpaceMembership(spaceId: string | null, userId: string | null) {
  const { token, isAuthenticated, status } = useAuthToken()
  const isValidSpaceId =
    typeof spaceId === 'string' &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(spaceId)
  const queryEnabled = Boolean(
    status !== 'loading' &&
    isAuthenticated &&
    isValidSpaceId &&
    userId &&
    token
  )

  return useQuery<ResearchSpaceMembership | null, Error, ResearchSpaceMembership | null>({
    queryKey: researchSpaceKeys.membership(spaceId || '', userId || ''),
    queryFn: async () => {
      if (!token || !spaceId) {
        throw new Error('No authentication token available')
      }
      return fetchMyMembership(spaceId, token)
    },
    enabled: queryEnabled,
    retry: false,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export function usePendingInvitations(params?: { skip?: number; limit?: number }): UseQueryResult<MembershipListResponse, Error> {
  const { token, isAuthenticated, status } = useAuthToken()
  const queryEnabled = Boolean(status !== 'loading' && isAuthenticated && token)

  return useQuery<MembershipListResponse, Error, MembershipListResponse>({
    queryKey: researchSpaceKeys.pendingInvitations(),
    queryFn: async () => {
      if (!token) throw new Error('No authentication token available')
      return fetchPendingInvitations(params, token)
    },
    enabled: queryEnabled,
    retry: false,
    // Auth errors are handled by the API interceptor
    staleTime: 2 * 60 * 1000, // 2 minutes - invitations can change more frequently
    gcTime: 10 * 60 * 1000, // 10 minutes - keep in cache
  })
}

// Research Spaces mutations

export function useCreateResearchSpace() {
  const queryClient = useQueryClient()
  const { token, isAuthenticated } = useAuthToken()
  const { data: session } = useSession()

  return useMutation<ResearchSpace, Error, CreateSpaceRequest>({
    mutationFn: async (data) => {
      if (!token || !isAuthenticated) {
        throw new Error('Authentication required. Please log in again.')
      }
      return createResearchSpace(data, token)
    },
    // Optimistic update - immediately update UI before server responds
    onMutate: async (newSpace) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: researchSpaceKeys.lists() })

      // Snapshot previous value
      const previousSpaces = queryClient.getQueryData<ResearchSpaceListResponse>(
        researchSpaceKeys.list()
      )

      // Optimistically update the list
      if (previousSpaces) {
        const optimisticSpace: ResearchSpace = {
          id: `temp-${Date.now()}`, // Temporary ID
          name: newSpace.name,
          description: newSpace.description || '',
          slug: newSpace.slug || newSpace.name.toLowerCase().replace(/\s+/g, '-'),
          owner_id: session?.user?.id || '',
          status: SpaceStatus.ACTIVE,
          settings: newSpace.settings || {},
          tags: newSpace.tags || [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }

        queryClient.setQueryData<ResearchSpaceListResponse>(
          researchSpaceKeys.list(),
          {
            ...previousSpaces,
            spaces: [optimisticSpace, ...previousSpaces.spaces],
          }
        )
      }

      return { previousSpaces }
    },
    onError: (error, _newSpace, context) => {
      // Rollback on error
      if (context && typeof context === 'object' && 'previousSpaces' in context && context.previousSpaces) {
        queryClient.setQueryData(researchSpaceKeys.list(), context.previousSpaces)
      }
      console.error('Failed to create research space:', error)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.lists() })
    },
  })
}

export function useUpdateResearchSpace() {
  const queryClient = useQueryClient()
  const { token } = useAuthToken()

  return useMutation<
    ResearchSpace,
    Error,
    { spaceId: string; data: UpdateSpaceRequest }
  >({
    mutationFn: async ({ spaceId, data }) => {
      if (!token) throw new Error('No authentication token available')
      return updateResearchSpace(spaceId, data, token)
    },
    // Optimistic update - immediately update UI before server responds
    onMutate: async ({ spaceId, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: researchSpaceKeys.detail(spaceId) })
      await queryClient.cancelQueries({ queryKey: researchSpaceKeys.lists() })

      // Snapshot previous values
      const previousSpace = queryClient.getQueryData<ResearchSpace>(
        researchSpaceKeys.detail(spaceId)
      )
      const previousSpaces = queryClient.getQueryData<ResearchSpaceListResponse>(
        researchSpaceKeys.list()
      )

      // Optimistically update space detail
      if (previousSpace) {
        queryClient.setQueryData<ResearchSpace>(
          researchSpaceKeys.detail(spaceId),
          {
            ...previousSpace,
            ...data,
            updated_at: new Date().toISOString(),
          }
        )
      }

      // Optimistically update space in list
      if (previousSpaces) {
        queryClient.setQueryData<ResearchSpaceListResponse>(
          researchSpaceKeys.list(),
          {
            ...previousSpaces,
            spaces: previousSpaces.spaces.map((space) =>
              space.id === spaceId
                ? { ...space, ...data, updated_at: new Date().toISOString() }
                : space
            ),
          }
        )
      }

      return { previousSpace, previousSpaces }
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context && typeof context === 'object' && 'previousSpace' in context && context.previousSpace) {
        queryClient.setQueryData(
          researchSpaceKeys.detail(variables.spaceId),
          context.previousSpace
        )
      }
      if (context && typeof context === 'object' && 'previousSpaces' in context && context.previousSpaces) {
        queryClient.setQueryData(researchSpaceKeys.list(), context.previousSpaces)
      }
      console.error('Failed to update research space:', error)
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.lists() })
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.detail(data.id) })
    },
  })
}

export function useDeleteResearchSpace() {
  const queryClient = useQueryClient()
  const { token } = useAuthToken()

  return useMutation<void, Error, string>({
    mutationFn: async (spaceId) => {
      if (!token) throw new Error('No authentication token available')
      return deleteResearchSpace(spaceId, token)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.lists() })
    },
  })
}

// Membership mutations

export function useInviteMember() {
  const queryClient = useQueryClient()
  const { token } = useAuthToken()
  const { data: session } = useSession()

  return useMutation<
    ResearchSpaceMembership,
    Error,
    { spaceId: string; data: InviteMemberRequest }
  >({
    mutationFn: async ({ spaceId, data }) => {
      if (!token) throw new Error('No authentication token available')
      return inviteMember(spaceId, data, token)
    },
    // Optimistic update - immediately update UI before server responds
    onMutate: async ({ spaceId, data }) => {
      await queryClient.cancelQueries({ queryKey: researchSpaceKeys.members(spaceId) })
      await queryClient.cancelQueries({ queryKey: researchSpaceKeys.pendingInvitations() })

      const previousMembers = queryClient.getQueryData<MembershipListResponse>(
        researchSpaceKeys.members(spaceId)
      )
      const previousInvitations = queryClient.getQueryData<MembershipListResponse>(
        researchSpaceKeys.pendingInvitations()
      )

      // Optimistically add to pending invitations
      if (previousInvitations) {
        const optimisticMembership: ResearchSpaceMembership = {
          id: `temp-${Date.now()}`,
          space_id: spaceId,
          user_id: data.user_id,
          role: data.role,
          invited_by: session?.user?.id || null,
          invited_at: new Date().toISOString(),
          joined_at: null,
          is_active: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }

        queryClient.setQueryData<MembershipListResponse>(
          researchSpaceKeys.pendingInvitations(),
          {
            ...previousInvitations,
            memberships: [optimisticMembership, ...previousInvitations.memberships],
            total: previousInvitations.total + 1,
          }
        )
      }

      return { previousMembers, previousInvitations }
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context && typeof context === 'object' && 'previousInvitations' in context && context.previousInvitations) {
        queryClient.setQueryData(
          researchSpaceKeys.pendingInvitations(),
          context.previousInvitations
        )
      }
      if (context && typeof context === 'object' && 'previousMembers' in context && context.previousMembers) {
        queryClient.setQueryData(
          researchSpaceKeys.members(variables.spaceId),
          context.previousMembers
        )
      }
      console.error('Failed to invite member:', error)
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.members(variables.spaceId) })
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.pendingInvitations() })
    },
  })
}

export function useUpdateMemberRole() {
  const queryClient = useQueryClient()
  const { token } = useAuthToken()

  return useMutation<
    ResearchSpaceMembership,
    Error,
    { spaceId: string; membershipId: string; data: UpdateMemberRoleRequest }
  >({
    mutationFn: async ({ spaceId, membershipId, data }) => {
      if (!token) throw new Error('No authentication token available')
      return updateMemberRole(spaceId, membershipId, data, token)
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.members(variables.spaceId) })
    },
  })
}

export function useRemoveMember() {
  const queryClient = useQueryClient()
  const { token } = useAuthToken()

  return useMutation<void, Error, { spaceId: string; membershipId: string }>({
    mutationFn: async ({ spaceId, membershipId }) => {
      if (!token) throw new Error('No authentication token available')
      return removeMember(spaceId, membershipId, token)
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.members(variables.spaceId) })
    },
  })
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient()
  const { token } = useAuthToken()

  return useMutation<ResearchSpaceMembership, Error, string>({
    mutationFn: async (membershipId) => {
      if (!token) throw new Error('No authentication token available')
      return acceptInvitation(membershipId, token)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.pendingInvitations() })
      queryClient.invalidateQueries({ queryKey: researchSpaceKeys.lists() })
    },
  })
}

// Curation queries

export function useSpaceCurationStats(
  spaceId: string,
  options?: { enabled?: boolean },
): UseQueryResult<CurationStats, Error> {
  const { token, isAuthenticated, status } = useAuthToken()
  const computedEnabled = Boolean(status !== 'loading' && isAuthenticated && spaceId && token)
  const queryEnabled = options?.enabled ?? computedEnabled

  return useQuery<CurationStats, Error, CurationStats>({
    queryKey: researchSpaceKeys.curationStats(spaceId),
    queryFn: async () => {
      if (!token) throw new Error('No authentication token available')
      return fetchSpaceCurationStats(spaceId, token)
    },
    enabled: queryEnabled,
  })
}

export function useSpaceCurationQueue(
  spaceId: string,
  filters?: {
    entity_type?: string
    status?: string
    priority?: string
    skip?: number
    limit?: number
  },
  options?: { enabled?: boolean },
): UseQueryResult<CurationQueueResponse, Error> {
  const { token, isAuthenticated, status } = useAuthToken()
  const computedEnabled = Boolean(status !== 'loading' && isAuthenticated && spaceId && token)
  const queryEnabled = options?.enabled ?? computedEnabled

  return useQuery<CurationQueueResponse, Error, CurationQueueResponse>({
    queryKey: researchSpaceKeys.curationQueue(spaceId, filters),
    queryFn: async () => {
      if (!token) throw new Error('No authentication token available')
      return fetchSpaceCurationQueue(spaceId, filters, token)
    },
    enabled: queryEnabled,
  })
}
