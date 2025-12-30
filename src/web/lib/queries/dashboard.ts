"use client"

import { useQuery } from '@tanstack/react-query'
import { fetchDashboardStats, fetchRecentActivities } from '@/lib/api'
import type { DashboardStats, RecentActivitiesResponse } from '@/types/dashboard'
import { useSession } from 'next-auth/react'
import { dashboardKeys } from '@/lib/query-keys/dashboard'

export function useDashboardStats() {
  const { data: session, status } = useSession()
  const token = session?.user?.access_token
  // Only enable if we have BOTH authenticated status AND a valid token
  const isAuthenticated = status === 'authenticated' && typeof token === 'string' && token.length > 0
  
  // Debug logging
  if (status === 'authenticated' && !token) {
    console.warn('[useDashboardStats] Session authenticated but missing access_token', {
      session,
      status,
      hasUser: !!session?.user,
      userKeys: session?.user ? Object.keys(session.user) : [],
      tokenType: typeof token,
      tokenValue: token,
    })
  }
  
  const queryKey = token
    ? dashboardKeys.stats(token)
    : dashboardKeys.stats('unauthenticated')

  return useQuery<DashboardStats>({
    queryKey,
    queryFn: async () => {
      // Double-check token before making request
      if (!token || typeof token !== 'string' || token.length === 0) {
        console.error('[useDashboardStats] Query executed without valid token!', { 
          status, 
          session,
          token,
          tokenType: typeof token,
        })
        throw new Error('No authentication token available')
      }
      return fetchDashboardStats(token)
    },
    enabled: isAuthenticated, // Only run when authenticated and token is available
    retry: false, // Don't retry on 401 errors
    staleTime: 1 * 60 * 1000, // 1 minute - dashboard stats change frequently
    gcTime: 5 * 60 * 1000, // 5 minutes - keep in cache
  })
}

export function useRecentActivities(limit = 10) {
  const { data: session, status } = useSession()
  const token = session?.user?.access_token
  // Only enable if we have BOTH authenticated status AND a valid token
  const isAuthenticated = status === 'authenticated' && typeof token === 'string' && token.length > 0
  
  // Debug logging
  if (status === 'authenticated' && !token) {
    console.warn('[useRecentActivities] Session authenticated but missing access_token', {
      session,
      status,
      hasUser: !!session?.user,
      userKeys: session?.user ? Object.keys(session.user) : [],
      tokenType: typeof token,
      tokenValue: token,
    })
  }
  
  const queryKey = token
    ? dashboardKeys.activities(limit, token)
    : dashboardKeys.activities(limit, 'unauthenticated')

  return useQuery<RecentActivitiesResponse>({
    queryKey,
    queryFn: async () => {
      // Double-check token before making request
      if (!token || typeof token !== 'string' || token.length === 0) {
        console.error('[useRecentActivities] Query executed without valid token!', { 
          status, 
          session,
          token,
          tokenType: typeof token,
        })
        throw new Error('No authentication token available')
      }
      return fetchRecentActivities(limit, token)
    },
    enabled: isAuthenticated, // Only run when authenticated and token is available
    retry: false, // Don't retry on 401 errors
    staleTime: 1 * 60 * 1000, // 1 minute - activities change frequently
    gcTime: 5 * 60 * 1000, // 5 minutes - keep in cache
  })
}
