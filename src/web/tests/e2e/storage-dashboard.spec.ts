import { expect, test, type Page, type Route } from '@playwright/test'

import type {
  StorageConfiguration,
  StorageConfigurationListResponse,
  StorageConfigurationStats,
  StorageHealthReport,
  StorageOperationRecord,
  StorageOverviewResponse,
  StorageProviderTestResult,
  StorageUsageMetrics,
} from '../../types/storage'
import type { MaintenanceModeResponse } from '../../types/system-status'

interface MockStorageState {
  configs: Map<string, StorageConfiguration>
  metrics: Map<string, StorageUsageMetrics>
  operations: Map<string, StorageOperationRecord[]>
  health: Map<string, StorageHealthReport>
}

const ISO = () => new Date().toISOString()

function createMockStorageState(): MockStorageState {
  const initialConfig: StorageConfiguration = {
    id: 'config-local',
    name: 'Local Vault',
    provider: 'local_filesystem',
    config: {
      provider: 'local_filesystem',
      base_path: '/var/storage',
      create_directories: true,
      expose_file_urls: false,
    },
    enabled: true,
    supported_capabilities: ['pdf', 'export'],
    default_use_cases: ['pdf'],
    metadata: {},
    created_at: ISO(),
    updated_at: ISO(),
  }
  const metrics: StorageUsageMetrics = {
    configuration_id: initialConfig.id,
    total_files: 8,
    total_size_bytes: 5120,
    last_operation_at: ISO(),
    error_rate: 0,
  }
  const health: StorageHealthReport = {
    configuration_id: initialConfig.id,
    provider: initialConfig.provider,
    status: 'healthy',
    last_checked_at: ISO(),
    details: {},
  }
  const operation: StorageOperationRecord = {
    id: 'op-1',
    configuration_id: initialConfig.id,
    user_id: 'admin-1',
    operation_type: 'store',
    key: 'reports/test.pdf',
    file_size_bytes: 2048,
    status: 'success',
    error_message: null,
    metadata: {},
    created_at: ISO(),
  }
  return {
    configs: new Map([[initialConfig.id, initialConfig]]),
    metrics: new Map([[initialConfig.id, metrics]]),
    operations: new Map([[initialConfig.id, [operation]]]),
    health: new Map([[initialConfig.id, health]]),
  }
}

async function respondJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    body: JSON.stringify(body),
    headers: { 'content-type': 'application/json' },
  })
}

function ensureMetrics(state: MockStorageState, configurationId: string): StorageUsageMetrics {
  if (!state.metrics.has(configurationId)) {
    state.metrics.set(configurationId, {
      configuration_id: configurationId,
      total_files: 0,
      total_size_bytes: 0,
      last_operation_at: null,
      error_rate: 0,
    })
  }
  return state.metrics.get(configurationId)!
}

function ensureHealth(state: MockStorageState, configurationId: string, provider: string): StorageHealthReport {
  if (!state.health.has(configurationId)) {
    state.health.set(configurationId, {
      configuration_id: configurationId,
      provider: provider as StorageHealthReport['provider'],
      status: 'healthy',
      last_checked_at: ISO(),
      details: {},
    })
  }
  return state.health.get(configurationId)!
}

function buildOverview(state: MockStorageState): StorageOverviewResponse {
  const stats: StorageConfigurationStats[] = []
  let enabled = 0
  let disabled = 0
  let healthy = 0
  let degraded = 0
  let offline = 0
  let totalFiles = 0
  let totalSize = 0
  const errorRates: number[] = []

  for (const config of state.configs.values()) {
    const usage = ensureMetrics(state, config.id)
    const health = ensureHealth(state, config.id, config.provider)
    stats.push({
      configuration: config,
      usage,
      health,
    })
    if (config.enabled) {
      enabled += 1
    } else {
      disabled += 1
    }
    totalFiles += usage.total_files
    totalSize += usage.total_size_bytes
    if (typeof usage.error_rate === 'number') {
      errorRates.push(usage.error_rate)
    }
    switch (health.status) {
      case 'healthy':
        healthy += 1
        break
      case 'degraded':
        degraded += 1
        break
      case 'offline':
        offline += 1
        break
      default:
        break
    }
  }

  return {
    generated_at: ISO(),
    totals: {
      total_configurations: state.configs.size,
      enabled_configurations: enabled,
      disabled_configurations: disabled,
      healthy_configurations: healthy,
      degraded_configurations: degraded,
      offline_configurations: offline,
      total_files: totalFiles,
      total_size_bytes: totalSize,
      average_error_rate:
        errorRates.length > 0 ? errorRates.reduce((sum, value) => sum + value, 0) / errorRates.length : null,
    },
    configurations: stats,
  }
}

async function setupAdminApiMocks(page: Page, state: MockStorageState) {
  await page.route('**/users/stats/overview', (route) =>
    respondJson(route, {
      total_users: 3,
      active_users: 3,
      inactive_users: 0,
      suspended_users: 0,
      pending_verification: 0,
      by_role: { admin: 1, researcher: 2 },
      recent_registrations: 1,
      recent_logins: 3,
    }),
  )

  await page.route('**/users?**', (route) =>
    respondJson(route, {
      users: [
        {
          id: 'admin-1',
          email: 'admin@med13.dev',
          username: 'admin',
          full_name: 'Admin User',
          role: 'admin',
          status: 'active',
          email_verified: true,
          last_login: ISO(),
          created_at: ISO(),
        },
      ],
      total: 1,
      skip: 0,
      limit: 25,
    }),
  )

  await page.route('**/admin/system/maintenance', (route) =>
    respondJson(route, {
      state: {
        is_active: false,
        message: null,
        updated_at: ISO(),
      },
    } satisfies MaintenanceModeResponse),
  )

  await page.route('**/admin/storage/**', async (route) => {
    const url = new URL(route.request().url())
    const { pathname } = url
    const method = route.request().method().toUpperCase()

    if (pathname.endsWith('/stats') && method === 'GET') {
      return respondJson(route, buildOverview(state))
    }

    const matchMetrics = pathname.match(/\/configurations\/([^/]+)\/metrics$/)
    if (matchMetrics && method === 'GET') {
      const configurationId = matchMetrics[1]
      const metrics = ensureMetrics(state, configurationId)
      return respondJson(route, metrics)
    }

    const matchHealth = pathname.match(/\/configurations\/([^/]+)\/health$/)
    if (matchHealth && method === 'GET') {
      const configurationId = matchHealth[1]
      const config = state.configs.get(configurationId)
      if (!config) {
        return respondJson(route, { detail: 'Not found' }, 404)
      }
      const health = ensureHealth(state, configurationId, config.provider)
      return respondJson(route, health)
    }

    const matchOperations = pathname.match(/\/configurations\/([^/]+)\/operations$/)
    if (matchOperations && method === 'GET') {
      const configurationId = matchOperations[1]
      const operations = state.operations.get(configurationId) ?? []
      return respondJson(route, operations)
    }

    const matchTest = pathname.match(/\/configurations\/([^/]+)\/test$/)
    if (matchTest && method === 'POST') {
      const configurationId = matchTest[1]
      const config = state.configs.get(configurationId)
      if (!config) {
        return respondJson(route, { detail: 'Not found' }, 404)
      }
      const result: StorageProviderTestResult = {
        configuration_id: configurationId,
        provider: config.provider,
        success: true,
        message: 'Connection verified',
        checked_at: ISO(),
        capabilities: config.supported_capabilities,
        latency_ms: 150,
        metadata: { tested_by: 'playwright' },
      }
      state.health.set(configurationId, {
        configuration_id: configurationId,
        provider: config.provider,
        status: 'healthy',
        last_checked_at: result.checked_at,
        details: result.metadata,
      })
      return respondJson(route, result)
    }

    const matchConfiguration = pathname.match(/\/configurations\/([^/]+)$/)
    if (matchConfiguration) {
      const configurationId = matchConfiguration[1]
      const config = state.configs.get(configurationId)
      if (!config) {
        return respondJson(route, { detail: 'Not found' }, 404)
      }
      if (method === 'PUT') {
        const payload = await route.request().postDataJSON()
        const updated: StorageConfiguration = {
          ...config,
          ...payload,
          supported_capabilities: payload.supported_capabilities ?? config.supported_capabilities,
          default_use_cases: payload.default_use_cases ?? config.default_use_cases,
          metadata: payload.metadata ?? config.metadata,
          updated_at: ISO(),
        }
        state.configs.set(configurationId, updated)
        return respondJson(route, updated)
      }
      if (method === 'DELETE') {
        const force = url.searchParams.get('force') === 'true'
        if (force || !config.enabled) {
          state.configs.delete(configurationId)
          state.metrics.delete(configurationId)
          state.health.delete(configurationId)
          state.operations.delete(configurationId)
        } else {
          state.configs.set(configurationId, { ...config, enabled: false, updated_at: ISO() })
        }
        return respondJson(route, { message: force ? 'Storage configuration deleted' : 'Storage configuration disabled' })
      }
    }

    if (pathname.endsWith('/configurations')) {
      if (method === 'GET') {
        const list: StorageConfigurationListResponse = {
          data: Array.from(state.configs.values()),
          total: state.configs.size,
          page: 1,
          per_page: 100,
        }
        return respondJson(route, list)
      }
      if (method === 'POST') {
        const payload = await route.request().postDataJSON()
        const id = `config-${state.configs.size + 1}`
        const created: StorageConfiguration = {
          id,
          name: payload.name,
          provider: payload.provider,
          config: payload.config,
          enabled: payload.enabled ?? true,
          supported_capabilities: payload.supported_capabilities ?? [],
          default_use_cases: payload.default_use_cases ?? [],
          metadata: payload.metadata ?? {},
          created_at: ISO(),
          updated_at: ISO(),
        }
        state.configs.set(id, created)
        state.metrics.set(id, {
          configuration_id: id,
          total_files: 0,
          total_size_bytes: 0,
          last_operation_at: null,
          error_rate: 0,
        })
        state.operations.set(id, [])
        state.health.set(id, {
          configuration_id: id,
          provider: created.provider,
          status: 'healthy',
          last_checked_at: ISO(),
          details: {},
        })
        return respondJson(route, created, 201)
      }
    }

    return route.fallback()
  })
}

test.describe('Storage dashboard', () => {
  test('creates, tests, toggles, and disables configurations', async ({ page }) => {
    const state = createMockStorageState()
    await setupAdminApiMocks(page, state)

    await page.goto('/system-settings')
    await page.getByRole('tab', { name: 'Storage' }).click()

    await expect(page.getByRole('heading', { name: 'Storage Platform Overview' })).toBeVisible()
    await expect(page.getByTestId('storage-card-config-local')).toBeVisible()

    await page.getByRole('button', { name: 'Add Configuration' }).click()
    await page.getByLabel('Name').fill('Cloud Archive')
    await page.getByLabel('Provider').selectOption('google_cloud_storage')
    await page.getByLabel('Bucket Name').fill('med13-e2e')
    await page.getByLabel('Path Prefix').fill('/archives')
    await page.getByLabel('Credentials Secret').fill('projects/playwright/secrets/storage')
    await page.getByRole('button', { name: 'Create Configuration' }).click()

    const cloudCard = page.locator('[data-testid^="storage-card-"]').filter({ hasText: 'Cloud Archive' })
    await expect(cloudCard).toBeVisible()

    await cloudCard.getByRole('button', { name: 'Test Connection' }).click()
    await expect(cloudCard.getByRole('button', { name: 'Testing...' })).toBeVisible()
    await expect(cloudCard.getByRole('button', { name: 'Test Connection' })).toBeVisible()

    const switchControl = cloudCard.getByRole('switch')
    await expect(switchControl).toHaveAttribute('aria-checked', 'true')
    await switchControl.click()
    await expect(switchControl).toHaveAttribute('aria-checked', 'false')

    await cloudCard.getByRole('button', { name: 'Delete' }).click()
    await expect(switchControl).toHaveAttribute('aria-checked', 'false')
    await expect(cloudCard.getByText('Disabled')).toBeVisible()
  })
})
