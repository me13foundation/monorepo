import { apiClient, authHeaders } from '@/lib/api/client'
import type {
  CreateSessionRequest,
  DataDiscoverySession,
  PromoteSourceRequest,
  PromoteSourceResponse,
  SourceCatalogEntry,
  UpdateParametersRequest,
} from '@/lib/types/data-discovery'

const SPACE_DISCOVERY_BASE = '/research-spaces'

function requireToken(token?: string): asserts token is string {
  if (!token) {
    throw new Error('Authentication token is required for space discovery requests')
  }
}

function requireSpaceId(spaceId?: string): asserts spaceId is string {
  if (!spaceId) {
    throw new Error('Space ID is required for space discovery requests')
  }
}

type SpaceCreateSessionPayload = Omit<CreateSessionRequest, 'research_space_id'>

export async function fetchSpaceSourceCatalog(
  spaceId: string | undefined,
  token?: string,
  params?: { category?: string; search?: string },
): Promise<SourceCatalogEntry[]> {
  requireToken(token)
  requireSpaceId(spaceId)
  const response = await apiClient.get<SourceCatalogEntry[]>(
    `${SPACE_DISCOVERY_BASE}/${spaceId}/discovery/catalog`,
    {
      params,
      ...authHeaders(token),
    },
  )
  return response.data
}

export async function fetchSpaceDiscoverySessions(
  spaceId: string | undefined,
  token?: string,
): Promise<DataDiscoverySession[]> {
  requireToken(token)
  requireSpaceId(spaceId)
  const response = await apiClient.get<DataDiscoverySession[]>(
    `${SPACE_DISCOVERY_BASE}/${spaceId}/discovery/sessions`,
    authHeaders(token),
  )
  return response.data
}

export async function createSpaceDiscoverySession(
  spaceId: string | undefined,
  payload: SpaceCreateSessionPayload,
  token?: string,
): Promise<DataDiscoverySession> {
  requireToken(token)
  requireSpaceId(spaceId)
  const response = await apiClient.post<DataDiscoverySession>(
    `${SPACE_DISCOVERY_BASE}/${spaceId}/discovery/sessions`,
    payload,
    authHeaders(token),
  )
  return response.data
}

export async function updateSpaceDiscoverySessionParameters(
  spaceId: string | undefined,
  sessionId: string,
  payload: UpdateParametersRequest,
  token?: string,
): Promise<DataDiscoverySession> {
  requireToken(token)
  requireSpaceId(spaceId)
  const response = await apiClient.put<DataDiscoverySession>(
    `${SPACE_DISCOVERY_BASE}/${spaceId}/discovery/sessions/${sessionId}/parameters`,
    payload,
    authHeaders(token),
  )
  return response.data
}

export async function toggleSpaceDiscoverySourceSelection(
  spaceId: string | undefined,
  sessionId: string,
  catalogEntryId: string,
  token?: string,
): Promise<DataDiscoverySession> {
  requireToken(token)
  requireSpaceId(spaceId)
  const response = await apiClient.put<DataDiscoverySession>(
    `${SPACE_DISCOVERY_BASE}/${spaceId}/discovery/sessions/${sessionId}/sources/${catalogEntryId}/toggle`,
    {},
    authHeaders(token),
  )
  return response.data
}

export async function setSpaceDiscoverySelections(
  spaceId: string | undefined,
  sessionId: string,
  sourceIds: string[],
  token?: string,
): Promise<DataDiscoverySession> {
  requireToken(token)
  requireSpaceId(spaceId)
  const response = await apiClient.put<DataDiscoverySession>(
    `${SPACE_DISCOVERY_BASE}/${spaceId}/discovery/sessions/${sessionId}/selections`,
    { source_ids: sourceIds },
    authHeaders(token),
  )
  return response.data
}

export async function deleteSpaceDiscoverySession(
  spaceId: string | undefined,
  sessionId: string,
  token?: string,
): Promise<void> {
  requireToken(token)
  requireSpaceId(spaceId)
  await apiClient.delete(`${SPACE_DISCOVERY_BASE}/${spaceId}/discovery/sessions/${sessionId}`, authHeaders(token))
}

export async function promoteDiscoverySourceInSpace(
  spaceId: string | undefined,
  sessionId: string,
  catalogEntryId: string,
  payload: PromoteSourceRequest,
  token?: string,
): Promise<PromoteSourceResponse> {
  requireToken(token)
  requireSpaceId(spaceId)
  const response = await apiClient.post<PromoteSourceResponse>(
    `${SPACE_DISCOVERY_BASE}/${spaceId}/discovery/sessions/${sessionId}/sources/${catalogEntryId}/promote`,
    payload,
    authHeaders(token),
  )
  return response.data
}

export async function addDiscoverySourceToSpace(
  sessionId: string,
  catalogEntryId: string,
  researchSpaceId: string,
  token?: string,
  sourceConfig?: Record<string, unknown>,
): Promise<string> {
  requireToken(token)
  const metadata =
    (sourceConfig?.metadata as Record<string, unknown> | undefined) ?? {
      query: 'MED13',
    }
  const enrichedConfig: Record<string, unknown> = {
    ...sourceConfig,
    metadata,
  }
  const response = await apiClient.post<{ data_source_id: string }>(
    `/data-discovery/sessions/${sessionId}/add-to-space`,
    {
      catalog_entry_id: catalogEntryId,
      research_space_id: researchSpaceId,
      source_config: enrichedConfig,
    },
    authHeaders(token),
  )
  return response.data.data_source_id
}
