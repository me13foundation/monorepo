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

export function useTemplates(scope: TemplateScope = 'available') {
  return useEntity<TemplateListResponse, TemplateCreatePayload, TemplateUpdatePayload, { templateId: string }>({
    queryKey: ['templates', scope],
    fetcher: () => fetchTemplates(scope),
    createFn: (payload) => createTemplate(payload),
    updateFn: (payload) => updateTemplate(payload),
    deleteFn: ({ templateId }) => deleteTemplate(templateId),
  })
}
