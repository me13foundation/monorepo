"use client"

import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createStorageConfiguration,
  deleteStorageConfiguration,
  fetchStorageConfigurations,
  fetchStorageHealth,
  fetchStorageMetrics,
  fetchStorageOperations,
  fetchStorageOverview,
  testStorageConfiguration,
  updateStorageConfiguration,
} from '@/lib/api/storage'
import { storageKeys } from '@/lib/query-keys/storage'
import type {
  CreateStorageConfigurationRequest,
  StorageConfiguration,
  StorageConfigurationListResponse,
  StorageHealthReport,
  StorageOperationRecord,
  StorageOverviewResponse,
  StorageProviderTestResult,
  StorageUsageMetrics,
  UpdateStorageConfigurationRequest,
} from '@/types/storage'
import { useSystemAdminAccess } from '@/lib/queries/users'

export interface UseStorageConfigurationParams {
  page?: number
  perPage?: number
  includeDisabled?: boolean
}

const DEFAULT_STORAGE_LIST: Required<UseStorageConfigurationParams> = {
  page: 1,
  perPage: 100,
  includeDisabled: true,
}

export function useStorageConfigurations(params?: UseStorageConfigurationParams) {
  const { token, isReady } = useSystemAdminAccess()
  const resolved = { ...DEFAULT_STORAGE_LIST, ...(params ?? {}) }

  return useQuery<StorageConfigurationListResponse>({
    queryKey: storageKeys.list(
      token,
      resolved.page,
      resolved.perPage,
      resolved.includeDisabled,
    ),
    enabled: isReady,
    queryFn: () =>
      fetchStorageConfigurations(
        {
          page: resolved.page,
          per_page: resolved.perPage,
          include_disabled: resolved.includeDisabled,
        },
        token,
      ),
    staleTime: 30_000,
  })
}

export function useStorageOverview() {
  const { token, isReady } = useSystemAdminAccess()

  return useQuery<StorageOverviewResponse>({
    queryKey: storageKeys.stats(token),
    enabled: isReady,
    queryFn: () => fetchStorageOverview(token),
    staleTime: 15_000,
  })
}

export function useStorageMetrics(configurationId: string) {
  const { token, isReady } = useSystemAdminAccess()

  return useQuery<StorageUsageMetrics | null>({
    queryKey: storageKeys.metrics(configurationId, token),
    enabled: isReady && Boolean(configurationId),
    queryFn: () => fetchStorageMetrics(configurationId, token),
    staleTime: 15_000,
  })
}

export function useStorageHealth(configurationId: string) {
  const { token, isReady } = useSystemAdminAccess()

  return useQuery<StorageHealthReport | null>({
    queryKey: storageKeys.health(configurationId, token),
    enabled: isReady && Boolean(configurationId),
    queryFn: () => fetchStorageHealth(configurationId, token),
    staleTime: 15_000,
  })
}

export function useStorageOperations(configurationId: string, limit = 25) {
  const { token, isReady } = useSystemAdminAccess()

  return useQuery<StorageOperationRecord[]>({
    queryKey: storageKeys.operations(configurationId, limit, token),
    enabled: isReady && Boolean(configurationId),
    queryFn: () => fetchStorageOperations(configurationId, limit, token),
    staleTime: 30_000,
  })
}

export function useStorageMutations() {
  const queryClient = useQueryClient()
  const { token, isReady } = useSystemAdminAccess()

  const ensureToken = useCallback(() => {
    if (!token) {
      throw new Error('Authentication token is required for storage operations')
    }
    return token
  }, [token])

  const invalidateConfigurations = () => {
    queryClient.invalidateQueries({ queryKey: storageKeys.root })
    queryClient.invalidateQueries({ queryKey: storageKeys.stats(token) })
  }

  const createConfiguration = useMutation<StorageConfiguration, Error, CreateStorageConfigurationRequest>({
    mutationFn: (payload) => createStorageConfiguration(payload, ensureToken()),
    onSuccess: invalidateConfigurations,
  })

  const updateConfiguration = useMutation<
    StorageConfiguration,
    Error,
    { configurationId: string; payload: UpdateStorageConfigurationRequest }
  >({
    mutationFn: ({ configurationId, payload }) =>
      updateStorageConfiguration(configurationId, payload, ensureToken()),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: storageKeys.configuration(variables.configurationId, token),
      })
      invalidateConfigurations()
    },
  })

  const testConfiguration = useMutation<
    StorageProviderTestResult,
    Error,
    { configurationId: string }
  >({
    mutationFn: ({ configurationId }) => testStorageConfiguration(configurationId, ensureToken()),
  })

  const deleteConfiguration = useMutation<
    { message: string },
    Error,
    { configurationId: string; force?: boolean }
  >({
    mutationFn: ({ configurationId, force }) =>
      deleteStorageConfiguration(configurationId, force ?? false, ensureToken()),
    onSuccess: invalidateConfigurations,
  })

  return {
    isReady,
    createConfiguration,
    updateConfiguration,
    testConfiguration,
    deleteConfiguration,
  }
}
