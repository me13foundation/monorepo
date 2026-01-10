"use client"

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'
import {
  addSourceToSpaceFromDiscovery,
  createPubmedPreset,
  createDataDiscoverySession,
  deletePubmedPreset,
  executeDataDiscoveryQueryTest,
  downloadPubmedPdf,
  fetchDataDiscoverySessions,
  fetchPubmedPresets,
  fetchPubmedSearchJob,
  fetchSessionTestResults,
  fetchSourceCatalog,
  runPubmedSearch,
  toggleDataDiscoverySourceSelection,
  updateDataDiscoverySessionParameters,
  setDataDiscoverySelections,
} from '@/lib/api/data-discovery'
import type {
  AddToSpaceRequest,
  CreatePubmedPresetRequest,
  CreateSessionRequest,
  DataDiscoverySession,
  DiscoveryPreset,
  DiscoverySearchJob,
  ExecuteTestRequest,
  PubmedDownloadRequest,
  QueryTestResult,
  RunPubmedSearchRequest,
  SourceCatalogEntry,
  StorageOperationSummary,
  UpdateParametersRequest,
} from '@/lib/types/data-discovery'
import { dataDiscoveryKeys } from '@/lib/query-keys/data-discovery'
import { dataSourceKeys } from '@/lib/query-keys/data-sources'

function useAuthToken() {
  const { data: session } = useSession()
  return session?.user?.access_token
}

export function useSourceCatalog(params?: { category?: string; search?: string; research_space_id?: string }) {
  const token = useAuthToken()
  return useQuery<SourceCatalogEntry[]>({
    queryKey: dataDiscoveryKeys.catalog(params),
    queryFn: () => fetchSourceCatalog(token, params),
    enabled: Boolean(token),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

export function useDataDiscoverySessions() {
  const token = useAuthToken()
  return useQuery<DataDiscoverySession[]>({
    queryKey: dataDiscoveryKeys.sessions(),
    queryFn: () => fetchDataDiscoverySessions(token),
    enabled: Boolean(token),
    staleTime: 2 * 60 * 1000, // 2 minutes - sessions change moderately
    gcTime: 10 * 60 * 1000, // 10 minutes - keep in cache
  })
}

export function useCreateDataDiscoverySession() {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateSessionRequest) => createDataDiscoverySession(payload, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.sessions() })
    },
  })
}

export function useUpdateDataDiscoverySessionParameters() {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, payload }: { sessionId: string; payload: UpdateParametersRequest }) =>
      updateDataDiscoverySessionParameters(sessionId, payload, token),
    onSuccess: (session) => {
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.sessions() })
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.sessionTests(session.id) })
    },
  })
}

export function useToggleDataDiscoverySourceSelection() {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, catalogEntryId }: { sessionId: string; catalogEntryId: string }) =>
      toggleDataDiscoverySourceSelection(sessionId, catalogEntryId, token),
    onSuccess: (session) => {
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.sessions() })
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.sessionTests(session.id) })
    },
  })
}

export function useExecuteDataDiscoveryTest() {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, payload }: { sessionId: string; payload: ExecuteTestRequest }) =>
      executeDataDiscoveryQueryTest(sessionId, payload, token),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.sessionTests(result.session_id) })
    },
  })
}

export function useSessionTestResults(sessionId: string | null) {
  const token = useAuthToken()
  return useQuery<QueryTestResult[]>({
    queryKey: sessionId ? dataDiscoveryKeys.sessionTests(sessionId) : ['data-discovery', 'tests', 'pending'],
    queryFn: () => {
      if (!sessionId) {
        throw new Error('Session ID is required to fetch test results')
      }
      return fetchSessionTestResults(sessionId, token)
    },
    enabled: Boolean(token && sessionId),
    staleTime: 30 * 1000, // 30 seconds - test results can change frequently during execution
    gcTime: 5 * 60 * 1000, // 5 minutes - keep in cache
  })
}

export function useAddDiscoverySourceToSpace() {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, payload }: { sessionId: string; payload: AddToSpaceRequest }) =>
      addSourceToSpaceFromDiscovery(sessionId, payload, token),
    onSuccess: (_result, variables) => {
      const targetSpace = variables.payload.research_space_id
      if (targetSpace) {
        queryClient.invalidateQueries({ queryKey: dataSourceKeys.space(targetSpace) })
      }
    },
  })
}

export function useSetDataDiscoverySelections() {
  const token = useAuthToken()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, sourceIds }: { sessionId: string; sourceIds: string[] }) =>
      setDataDiscoverySelections(sessionId, sourceIds, token),
    onSuccess: (session) => {
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.sessions() })
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.sessionTests(session.id) })
    },
  })
}

export function usePubmedPresets(
  params?: { research_space_id?: string },
  options?: { enabled?: boolean },
) {
  const token = useAuthToken()
  return useQuery<DiscoveryPreset[]>({
    queryKey: dataDiscoveryKeys.pubmedPresets(params),
    queryFn: () => fetchPubmedPresets(token, params),
    enabled: Boolean(token) && (options?.enabled ?? true),
    staleTime: 60 * 1000,
  })
}

export function useCreatePubmedPreset() {
  const token = useAuthToken()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreatePubmedPresetRequest) => createPubmedPreset(payload, token),
    onSuccess: (_preset, variables) => {
      queryClient.invalidateQueries({
        queryKey: dataDiscoveryKeys.pubmedPresets({ research_space_id: variables.research_space_id ?? undefined }),
      })
    },
  })
}

export function useDeletePubmedPreset(params?: { research_space_id?: string }) {
  const token = useAuthToken()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (presetId: string) => deletePubmedPreset(presetId, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.pubmedPresets(params) })
    },
  })
}

export function useRunPubmedSearch() {
  const token = useAuthToken()
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: RunPubmedSearchRequest) => runPubmedSearch(payload, token),
    onSuccess: (job) => {
      queryClient.invalidateQueries({ queryKey: dataDiscoveryKeys.pubmedSearchJob(job.id) })
    },
  })
}

export function usePubmedSearchJob(jobId: string | null) {
  const token = useAuthToken()
  return useQuery<DiscoverySearchJob>({
    queryKey: jobId ? dataDiscoveryKeys.pubmedSearchJob(jobId) : ['data-discovery', 'pubmed-search', 'pending'],
    queryFn: () => {
      if (!jobId) {
        throw new Error('Job ID is required to fetch search job details')
      }
      return fetchPubmedSearchJob(jobId, token)
    },
    enabled: Boolean(token && jobId),
    refetchInterval: (query) => {
      const job = query.state.data
      return job && (job.status === 'completed' || job.status === 'failed') ? false : 5000
    },
  })
}

export function useDownloadPubmedPdf() {
  const token = useAuthToken()
  return useMutation<StorageOperationSummary, Error, PubmedDownloadRequest>({
    mutationFn: (payload) => downloadPubmedPdf(payload, token),
  })
}
