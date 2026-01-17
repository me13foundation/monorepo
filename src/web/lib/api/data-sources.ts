import { apiClient, authHeaders } from './client'
import type {
  DataSource,
  DataSourceIngestionSchedule,
  ScheduleFrequency,
} from '@/types/data-source'

export interface DataSourceListParams {
  page?: number
  limit?: number
  status?: string
  source_type?: string
  research_space_id?: string
}

export interface DataSourceListResponse {
  items: DataSource[]
  total: number
  page: number
  limit: number
  has_next: boolean
  has_prev: boolean
}

export interface ScheduleConfigurationPayload {
  enabled: boolean
  frequency: ScheduleFrequency
  start_time?: string | null
  timezone: string
  cron_expression?: string | null
}

export interface UpdateDataSourcePayload {
  name?: string
  description?: string
  status?: 'draft' | 'active' | 'inactive' | 'error' | 'pending_review' | 'archived'
  config?: Record<string, unknown>
  ingestion_schedule?: ScheduleConfigurationPayload
}

export interface ScheduledJobResponse {
  job_id: string
  source_id: string
  next_run_at: string
  frequency: ScheduleFrequency
  cron_expression?: string | null
}

export interface ScheduleConfigurationResponse {
  ingestion_schedule: DataSourceIngestionSchedule
  scheduled_job?: ScheduledJobResponse | null
}

export interface IngestionRunResponse {
  source_id: string
  fetched_records: number
  parsed_publications: number
  created_publications: number
  updated_publications: number
  executed_query?: string | null
}

export interface DataSourceAiTestResult {
  source_id: string
  success: boolean
  message: string
  executed_query?: string | null
  fetched_records: number
  sample_size: number
  checked_at: string
}

export interface IngestionJobHistoryItem {
  id: string
  status: string
  trigger: string
  started_at: string | null
  completed_at: string | null
  records_processed: number
  records_failed: number
  records_skipped: number
  bytes_processed: number
}

export interface IngestionJobHistoryResponse {
  source_id: string
  items: IngestionJobHistoryItem[]
}

export async function fetchDataSources(
  params: DataSourceListParams = {},
  token?: string,
): Promise<DataSourceListResponse> {
  if (!token) {
    throw new Error('Authentication token is required for fetchDataSources')
  }

  const response = await apiClient.get<DataSourceListResponse>(
    '/admin/data-sources',
    {
      params,
      ...authHeaders(token),
    },
  )

  return response.data
}

export async function fetchDataSourcesBySpace(
  spaceId: string,
  params: Omit<DataSourceListParams, 'research_space_id'> = {},
  token?: string,
): Promise<DataSourceListResponse> {
  return fetchDataSources({ ...params, research_space_id: spaceId }, token)
}

export async function createDataSource(
  data: {
    name: string
    description?: string
    source_type: string
    config: Record<string, unknown>
    tags?: string[]
    research_space_id?: string
  },
  token?: string,
): Promise<DataSource> {
  if (!token) {
    throw new Error('Authentication token is required for createDataSource')
  }

  const response = await apiClient.post<DataSource>(
    '/admin/data-sources',
    data,
    authHeaders(token),
  )

  return response.data
}

export async function createDataSourceInSpace(
  spaceId: string,
  data: Omit<Parameters<typeof createDataSource>[0], 'research_space_id'>,
  token?: string,
): Promise<DataSource> {
  return createDataSource({ ...data, research_space_id: spaceId }, token)
}

export async function configureDataSourceSchedule(
  sourceId: string,
  payload: ScheduleConfigurationPayload,
  token?: string,
): Promise<ScheduleConfigurationResponse> {
  if (!token) {
    throw new Error('Authentication token is required for configureDataSourceSchedule')
  }

  const response = await apiClient.put<ScheduleConfigurationResponse>(
    `/admin/data-sources/${sourceId}/schedule`,
    payload,
    authHeaders(token),
  )
  return response.data
}

export async function updateDataSource(
  sourceId: string,
  payload: UpdateDataSourcePayload,
  token?: string,
): Promise<DataSource> {
  if (!token) {
    throw new Error('Authentication token is required for updateDataSource')
  }

  const response = await apiClient.put<DataSource>(
    `/admin/data-sources/${sourceId}`,
    payload,
    authHeaders(token),
  )
  return response.data
}

export async function triggerDataSourceIngestion(
  sourceId: string,
  token?: string,
): Promise<IngestionRunResponse> {
  if (!token) {
    throw new Error('Authentication token is required for triggerDataSourceIngestion')
  }

  const response = await apiClient.post<IngestionRunResponse>(
    `/admin/data-sources/${sourceId}/schedule/run`,
    {},
    authHeaders(token),
  )
  return response.data
}

export async function testDataSourceAiConfiguration(
  sourceId: string,
  token?: string,
): Promise<DataSourceAiTestResult> {
  if (!token) {
    throw new Error('Authentication token is required for testDataSourceAiConfiguration')
  }

  const response = await apiClient.post<DataSourceAiTestResult>(
    `/admin/data-sources/${sourceId}/ai/test`,
    {},
    authHeaders(token),
  )
  return response.data
}

export async function fetchIngestionJobHistory(
  sourceId: string,
  token?: string,
  params: { limit?: number } = {},
): Promise<IngestionJobHistoryResponse> {
  if (!token) {
    throw new Error('Authentication token is required for fetchIngestionJobHistory')
  }
  const response = await apiClient.get<IngestionJobHistoryResponse>(
    `/admin/data-sources/${sourceId}/ingestion-jobs`,
    {
      params,
      ...authHeaders(token),
    },
  )
  return response.data
}

export async function deleteDataSource(
  sourceId: string,
  token?: string,
): Promise<void> {
  if (!token) {
    throw new Error('Authentication token is required for deleteDataSource')
  }

  await apiClient.delete(`/admin/data-sources/${sourceId}`, authHeaders(token))
}
