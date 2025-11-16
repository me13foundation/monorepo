"use client"

import { useEntity } from '@/hooks/use-entity'
import {
  createTemplate,
  deleteTemplate,
  fetchTemplates,
  updateTemplate,
} from '@/lib/api/templates'
import type {
  TemplateCreatePayload,
  TemplateListResponse,
  TemplateScope,
  TemplateUpdatePayload,
} from '@/types/template'
import { useSession } from 'next-auth/react'

export function useTemplates(scope: TemplateScope = 'available') {
  const { data: session, status } = useSession()
  const token = session?.user?.access_token
  const isAuthenticated = status === 'authenticated' && typeof token === 'string' && token.length > 0

  return useEntity<TemplateListResponse, TemplateCreatePayload, TemplateUpdatePayload, { templateId: string }>({
    queryKey: ['templates', scope],
    fetcher: async () => {
      if (!token || typeof token !== 'string' || token.length === 0) {
        throw new Error('No authentication token available')
      }
      return fetchTemplates(scope, token)
    },
    enabled: isAuthenticated,
    createFn: async (payload) => {
      if (!token || typeof token !== 'string' || token.length === 0) {
        throw new Error('No authentication token available')
      }
      return createTemplate(payload, token)
    },
    updateFn: async (payload) => {
      if (!token || typeof token !== 'string' || token.length === 0) {
        throw new Error('No authentication token available')
      }
      return updateTemplate(payload, token)
    },
    deleteFn: async ({ templateId }) => {
      if (!token || typeof token !== 'string' || token.length === 0) {
        throw new Error('No authentication token available')
      }
      return deleteTemplate(templateId, token)
    },
  })
}
