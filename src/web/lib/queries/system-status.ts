"use client"

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  disableMaintenanceMode,
  enableMaintenanceMode,
  fetchMaintenanceState,
} from '@/lib/api/system-status'
import type { EnableMaintenanceRequest } from '@/types/system-status'
import { useSystemAdminAccess } from '@/lib/queries/users'

export const systemStatusKeys = {
  maintenance: (token?: string) => ['system-status', 'maintenance', token] as const,
}

export function useMaintenanceState(tokenOverride?: string) {
  const { token, isReady } = useSystemAdminAccess()
  const resolvedToken = tokenOverride ?? token
  return useQuery({
    queryKey: systemStatusKeys.maintenance(resolvedToken),
    enabled: isReady && Boolean(resolvedToken),
    queryFn: () => fetchMaintenanceState(resolvedToken),
  })
}

export function useMaintenanceMutations(tokenOverride?: string) {
  const { token } = useSystemAdminAccess()
  const resolvedToken = tokenOverride ?? token
  const queryClient = useQueryClient()

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: systemStatusKeys.maintenance(resolvedToken) })

  const enable = useMutation({
    mutationFn: (payload: EnableMaintenanceRequest) => enableMaintenanceMode(payload, resolvedToken),
    onSuccess: invalidate,
  })

  const disable = useMutation({
    mutationFn: () => disableMaintenanceMode(resolvedToken),
    onSuccess: invalidate,
  })

  return { enable, disable }
}
