"use client"

import { useQuery } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'
import { fetchTemplate } from '@/lib/api/templates'
import { templateKeys } from '@/lib/query-keys/templates'

export function useTemplate(templateId: string) {
  const { data: session, status } = useSession()
  const token = session?.user?.access_token
  const isAuthenticated = status === 'authenticated' && typeof token === 'string' && token.length > 0

  return useQuery({
    queryKey: templateKeys.detail(templateId),
    queryFn: async () => {
      if (!token || typeof token !== 'string' || token.length === 0) {
        throw new Error('No authentication token available')
      }
      return fetchTemplate(templateId, token)
    },
    enabled: Boolean(templateId) && isAuthenticated,
    retry: false,
  })
}
