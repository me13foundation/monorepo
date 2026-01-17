import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'
import { toast } from 'sonner'
import {
  fetchDataSources,
  fetchDataSourcesBySpace,
  createDataSource,
  createDataSourceInSpace,
  configureDataSourceSchedule,
  updateDataSource,
  deleteDataSource,
  triggerDataSourceIngestion,
  testDataSourceAiConfiguration,
  fetchIngestionJobHistory,
  type DataSourceListParams,
  type DataSourceListResponse,
  type DataSourceAiTestResult,
  type ScheduleConfigurationPayload,
  type IngestionRunResponse,
  type UpdateDataSourcePayload,
} from '../api/data-sources'
import {
  fetchAdminCatalogEntries,
  fetchCatalogAvailabilitySummaries,
  fetchDataSourceAvailability,
  updateGlobalAvailability,
  clearGlobalAvailability,
  updateProjectAvailability,
  clearProjectAvailability,
  bulkUpdateGlobalAvailability,
  type PermissionLevel,
} from '@/lib/api/data-source-activation'
import type { DataSource } from '@/types/data-source'
import { useEntity } from '@/hooks/use-entity'
import { dataSourceKeys } from '@/lib/query-keys/data-sources'

export function useDataSources(params: DataSourceListParams = {}) {
  const { data: session } = useSession()
  const token = session?.user?.access_token

  return useEntity({
    queryKey: dataSourceKeys.list(params),
    fetcher: () => fetchDataSources(params, token),
    enabled: !!token,
  })
}

export function useSpaceDataSources(
  spaceId: string | null,
  params: Omit<DataSourceListParams, 'research_space_id'> = {},
  options?: { enabled?: boolean },
) {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const computedEnabled = !!token && !!spaceId
  const enabled = options?.enabled ?? computedEnabled

  return useQuery({
    queryKey: dataSourceKeys.space(spaceId || '', params),
    queryFn: () => fetchDataSourcesBySpace(spaceId!, params, token),
    enabled,
    refetchOnMount: 'always',
    refetchOnWindowFocus: false,
  })
}

export function useCreateDataSource() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Parameters<typeof createDataSource>[0]) =>
      createDataSource(data, token),
    // Optimistic update - immediately update UI before server responds
    onMutate: async (newDataSource) => {
      await queryClient.cancelQueries({ queryKey: dataSourceKeys.lists() })

      const previousDataSources = queryClient.getQueryData<DataSourceListResponse>(
        dataSourceKeys.list(newDataSource)
      )

      if (previousDataSources) {
        const optimisticDataSource: DataSource = {
          id: `temp-${Date.now()}`,
          name: newDataSource.name,
          description: newDataSource.description || '',
          source_type: newDataSource.source_type,
          status: 'draft',
          owner_id: session?.user?.id || '',
          research_space_id: newDataSource.research_space_id || null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          tags: newDataSource.tags || [],
        }

        queryClient.setQueryData<DataSourceListResponse>(
          dataSourceKeys.list(newDataSource),
          {
            ...previousDataSources,
            items: [optimisticDataSource, ...previousDataSources.items],
            total: previousDataSources.total + 1,
          }
        )
      }

      return { previousDataSources }
    },
    onError: (error, variables, context) => {
      if (context?.previousDataSources) {
        queryClient.setQueryData(dataSourceKeys.list(variables), context.previousDataSources)
      }
      toast.error(`Failed to create data source: ${error.message}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() })
      toast.success('Data source created successfully')
    },
  })
}

export function useCreateDataSourceInSpace(spaceId: string) {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Omit<Parameters<typeof createDataSource>[0], 'research_space_id'>) =>
      createDataSourceInSpace(spaceId, data, token),
    // Optimistic update - immediately update UI before server responds
    onMutate: async (newDataSource) => {
      await queryClient.cancelQueries({ queryKey: dataSourceKeys.space(spaceId) })
      await queryClient.cancelQueries({ queryKey: dataSourceKeys.lists() })

      const previousSpaceDataSources = queryClient.getQueryData<DataSourceListResponse>(
        dataSourceKeys.space(spaceId)
      )

      if (previousSpaceDataSources) {
        const optimisticDataSource: DataSource = {
          id: `temp-${Date.now()}`,
          name: newDataSource.name,
          description: newDataSource.description || '',
          source_type: newDataSource.source_type,
          status: 'draft',
          owner_id: session?.user?.id || '',
          research_space_id: spaceId,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          tags: newDataSource.tags || [],
        }

        queryClient.setQueryData<DataSourceListResponse>(
          dataSourceKeys.space(spaceId),
          {
            ...previousSpaceDataSources,
            items: [optimisticDataSource, ...previousSpaceDataSources.items],
            total: previousSpaceDataSources.total + 1,
          }
        )
      }

      return { previousSpaceDataSources }
    },
    onError: (error, _variables, context) => {
      if (context?.previousSpaceDataSources) {
        queryClient.setQueryData(dataSourceKeys.space(spaceId), context.previousSpaceDataSources)
      }
      toast.error(`Failed to create data source: ${error.message}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(spaceId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() })
      toast.success('Data source created successfully')
    },
  })
}

export function useConfigureDataSourceSchedule(spaceId?: string | null) {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      sourceId,
      payload,
    }: {
      sourceId: string
      payload: ScheduleConfigurationPayload
    }) => configureDataSourceSchedule(sourceId, payload, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() })
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(spaceId) })
      }
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.detail(variables.sourceId) })
      toast.success('Ingestion schedule updated')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update schedule: ${error.message}`)
    },
  })
}

export function useUpdateDataSource(spaceId?: string | null) {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      sourceId,
      payload,
    }: {
      sourceId: string
      payload: UpdateDataSourcePayload
    }) => updateDataSource(sourceId, payload, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() })
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(spaceId) })
      }
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.detail(variables.sourceId) })
      toast.success('Data source updated')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update data source: ${error.message}`)
    },
  })
}

export function useDeleteDataSource(spaceId?: string | null) {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sourceId: string) => deleteDataSource(sourceId, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() })
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(spaceId) })
      }
      toast.success('Data source removed')
    },
    onError: (error: Error) => {
      toast.error(`Failed to remove data source: ${error.message}`)
    },
  })
}

export function useTriggerDataSourceIngestion(
  spaceId?: string | null,
  options?: {
    onSuccess?: (summary: IngestionRunResponse, sourceId: string) => void
  },
) {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sourceId: string) => triggerDataSourceIngestion(sourceId, token),
    onSuccess: (summary, sourceId) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() })
      if (spaceId) {
        queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(spaceId) })
      }
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.detail(sourceId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.history(sourceId) })
      options?.onSuccess?.(summary, sourceId)
    },
    onError: (error: Error) => {
      toast.error(`Failed to trigger ingestion: ${error.message}`)
    },
  })
}

export function useTestDataSourceAiConfiguration() {
  const { data: session } = useSession()
  const token = session?.user?.access_token

  return useMutation<DataSourceAiTestResult, Error, string>({
    mutationFn: (sourceId: string) => testDataSourceAiConfiguration(sourceId, token),
  })
}

export function useIngestionJobHistory(sourceId: string | null, enabled: boolean) {
  const { data: session } = useSession()
  const token = session?.user?.access_token

  return useQuery({
    queryKey: dataSourceKeys.history(sourceId || 'none'),
    enabled: Boolean(token && sourceId && enabled),
    queryFn: () => fetchIngestionJobHistory(sourceId!, token),
    staleTime: 30 * 1000,
  })
}

export function useDataSourceAvailability(sourceId: string | null) {
  const { data: session } = useSession()
  const token = session?.user?.access_token

  return useQuery({
    queryKey: dataSourceKeys.availability(sourceId || 'none'),
    enabled: Boolean(token && sourceId),
    queryFn: () => fetchDataSourceAvailability(sourceId!, token),
    staleTime: 30 * 1000,
  })
}

export function useSetGlobalAvailability() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      sourceId,
      permissionLevel,
    }: {
      sourceId: string
      permissionLevel: PermissionLevel
    }) => updateGlobalAvailability(sourceId, permissionLevel, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.availability(variables.sourceId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() })
    },
  })
}

export function useClearGlobalAvailability() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sourceId }: { sourceId: string }) => clearGlobalAvailability(sourceId, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.availability(variables.sourceId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.lists() })
    },
  })
}

export function useSetProjectAvailability() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      sourceId,
      researchSpaceId,
      permissionLevel,
    }: {
      sourceId: string
      researchSpaceId: string
      permissionLevel: PermissionLevel
    }) => updateProjectAvailability(sourceId, researchSpaceId, permissionLevel, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.availability(variables.sourceId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(variables.researchSpaceId) })
    },
  })
}

export function useClearProjectAvailability() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sourceId, researchSpaceId }: { sourceId: string; researchSpaceId: string }) =>
      clearProjectAvailability(sourceId, researchSpaceId, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.availability(variables.sourceId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(variables.researchSpaceId) })
    },
  })
}

export function useAdminCatalogEntries() {
  const { data: session } = useSession()
  const token = session?.user?.access_token

  return useQuery({
    queryKey: dataSourceKeys.adminCatalog(),
    queryFn: () => fetchAdminCatalogEntries(token),
    enabled: Boolean(token),
    staleTime: 60 * 1000,
  })
}

export function useCatalogAvailability(catalogEntryId: string | null) {
  const { data: session } = useSession()
  const token = session?.user?.access_token

  return useQuery({
    queryKey: dataSourceKeys.availability(catalogEntryId ?? 'none'),
    queryFn: () => fetchDataSourceAvailability(catalogEntryId!, token),
    enabled: Boolean(token && catalogEntryId),
    staleTime: 30 * 1000,
  })
}

export function useSetCatalogGlobalAvailability() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      catalogEntryId,
      permissionLevel,
    }: {
      catalogEntryId: string
      permissionLevel: PermissionLevel
    }) => updateGlobalAvailability(catalogEntryId, permissionLevel, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.availability(variables.catalogEntryId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.adminCatalog() })
    },
  })
}

export function useClearCatalogGlobalAvailability() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ catalogEntryId }: { catalogEntryId: string }) => clearGlobalAvailability(catalogEntryId, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.availability(variables.catalogEntryId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.adminCatalog() })
    },
  })
}

export function useSetCatalogProjectAvailability() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      catalogEntryId,
      researchSpaceId,
      permissionLevel,
    }: {
      catalogEntryId: string
      researchSpaceId: string
      permissionLevel: PermissionLevel
    }) => updateProjectAvailability(catalogEntryId, researchSpaceId, permissionLevel, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.availability(variables.catalogEntryId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(variables.researchSpaceId) })
    },
  })
}

export function useCatalogAvailabilitySummaries(enabled: boolean = true) {
  const { data: session } = useSession()
  const token = session?.user?.access_token

  return useQuery({
    queryKey: dataSourceKeys.adminCatalogAvailability(),
    queryFn: () => fetchCatalogAvailabilitySummaries(token),
    enabled: Boolean(token) && enabled,
    staleTime: 30 * 1000,
  })
}

export function useBulkSetCatalogGlobalAvailability() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: { permissionLevel: PermissionLevel; catalogEntryIds?: string[] }) =>
      bulkUpdateGlobalAvailability(
        {
          permission_level: payload.permissionLevel,
          catalog_entry_ids: payload.catalogEntryIds,
        },
        token,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.adminCatalog() })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.adminCatalogAvailability() })
    },
  })
}

export function useClearCatalogProjectAvailability() {
  const { data: session } = useSession()
  const token = session?.user?.access_token
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ catalogEntryId, researchSpaceId }: { catalogEntryId: string; researchSpaceId: string }) =>
      clearProjectAvailability(catalogEntryId, researchSpaceId, token),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.availability(variables.catalogEntryId) })
      queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(variables.researchSpaceId) })
    },
  })
}
