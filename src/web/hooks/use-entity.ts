"use client"

import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryKey,
} from '@tanstack/react-query'

interface UseEntityOptions<TData, TCreate, TUpdate, TDelete> {
  queryKey: QueryKey
  fetcher: () => Promise<TData>
  enabled?: boolean
  createFn?: (payload: TCreate) => Promise<unknown>
  updateFn?: (payload: TUpdate) => Promise<unknown>
  deleteFn?: (payload: TDelete) => Promise<unknown>
  invalidateKeys?: QueryKey[]
}

export function useEntity<TData, TCreate = unknown, TUpdate = unknown, TDelete = unknown>(
  options: UseEntityOptions<TData, TCreate, TUpdate, TDelete>,
) {
  const queryClient = useQueryClient()

  const queryResult = useQuery({
    queryKey: options.queryKey,
    queryFn: options.fetcher,
    enabled: options.enabled,
  })

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: options.queryKey })
    options.invalidateKeys?.forEach((key) => {
      queryClient.invalidateQueries({ queryKey: key })
    })
  }

  const createMutation = options.createFn
    ? useMutation({
        mutationFn: options.createFn,
        onSuccess: invalidate,
      })
    : null

  const updateMutation = options.updateFn
    ? useMutation({
        mutationFn: options.updateFn,
        onSuccess: invalidate,
      })
    : null

  const deleteMutation = options.deleteFn
    ? useMutation({
        mutationFn: options.deleteFn,
        onSuccess: invalidate,
      })
    : null

  return {
    ...queryResult,
    create: createMutation?.mutateAsync,
    update: updateMutation?.mutateAsync,
    remove: deleteMutation?.mutateAsync,
  }
}
