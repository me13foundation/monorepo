"use client"

import { useQueryClient } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'
import { dashboardKeys } from '@/lib/query-keys/dashboard'
import { researchSpaceKeys } from '@/lib/query-keys/research-spaces'
import { dataDiscoveryKeys } from '@/lib/query-keys/data-discovery'
import { fetchDashboardStats, fetchRecentActivities } from '@/lib/api'
import { fetchResearchSpaces, fetchResearchSpace, fetchSpaceMembers, fetchSpaceCurationStats } from '@/lib/api/research-spaces'
import { fetchSourceCatalog, fetchDataDiscoverySessions } from '@/lib/api/data-discovery'

const RECENT_ACTIVITY_LIMIT = 5

/**
 * Hook for prefetching data on navigation hover/focus
 * Pre-warms cache before user clicks, making navigation feel instant
 */
export function usePrefetchOnHover() {
  const queryClient = useQueryClient()
  const { data: session } = useSession()
  const token = session?.user?.access_token

  const prefetchDashboard = () => {
    if (!token || typeof token !== 'string' || token.length === 0) {
      return
    }

    // Prefetch dashboard stats and activities
    queryClient.prefetchQuery({
      queryKey: dashboardKeys.stats(token),
      queryFn: () => fetchDashboardStats(token),
      staleTime: 1 * 60 * 1000, // 1 minute
    })

    queryClient.prefetchQuery({
      queryKey: dashboardKeys.activities(RECENT_ACTIVITY_LIMIT, token),
      queryFn: () => fetchRecentActivities(RECENT_ACTIVITY_LIMIT, token),
      staleTime: 1 * 60 * 1000, // 1 minute
    })
  }

  const prefetchResearchSpaces = () => {
    if (!token || typeof token !== 'string' || token.length === 0) {
      return
    }

    // Prefetch research spaces list
    queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.list(),
      queryFn: () => fetchResearchSpaces(undefined, token),
      staleTime: 10 * 60 * 1000, // 10 minutes
    })
  }

  const prefetchDataDiscovery = () => {
    if (!token || typeof token !== 'string' || token.length === 0) {
      return
    }

    // Prefetch source catalog and sessions
    queryClient.prefetchQuery({
      queryKey: dataDiscoveryKeys.catalog(undefined),
      queryFn: () => fetchSourceCatalog(token),
      staleTime: 5 * 60 * 1000, // 5 minutes
    })

    queryClient.prefetchQuery({
      queryKey: dataDiscoveryKeys.sessions(),
      queryFn: () => fetchDataDiscoverySessions(token),
      staleTime: 2 * 60 * 1000, // 2 minutes
    })
  }

  const prefetchSpaceDetail = (spaceId: string) => {
    if (!token || typeof token !== 'string' || token.length === 0 || !spaceId) {
      return
    }

    // Prefetch space details
    queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.detail(spaceId),
      queryFn: () => fetchResearchSpace(spaceId, token),
      staleTime: 5 * 60 * 1000, // 5 minutes
    })
  }

  const prefetchSpaceMembers = (spaceId: string) => {
    if (!token || typeof token !== 'string' || token.length === 0 || !spaceId) {
      return
    }

    // Prefetch space members
    queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.members(spaceId),
      queryFn: () => fetchSpaceMembers(spaceId, undefined, token),
      staleTime: 5 * 60 * 1000, // 5 minutes
    })
  }

  const prefetchSpaceCuration = (spaceId: string) => {
    if (!token || typeof token !== 'string' || token.length === 0 || !spaceId) {
      return
    }

    // Prefetch curation stats
    queryClient.prefetchQuery({
      queryKey: researchSpaceKeys.curationStats(spaceId),
      queryFn: () => fetchSpaceCurationStats(spaceId, token),
      staleTime: 2 * 60 * 1000, // 2 minutes
    })
  }

  return {
    prefetchDashboard,
    prefetchResearchSpaces,
    prefetchDataDiscovery,
    prefetchSpaceDetail,
    prefetchSpaceMembers,
    prefetchSpaceCuration,
  }
}
