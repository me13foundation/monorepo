"use client"

import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import {
  AlertCircle,
  BarChart3,
  HardDrive,
  Loader2,
  ShieldCheck,
  TestTube,
  Trash2,
  TrendingUp,
} from 'lucide-react'
import {
  useStorageConfigurations,
  useStorageHealth,
  useStorageMetrics,
  useStorageMutations,
  useStorageOverview,
} from '@/lib/queries/storage'
import { useMaintenanceState } from '@/lib/queries/system-status'
import type {
  CreateStorageConfigurationRequest,
  StorageConfiguration,
  StorageConfigurationStats,
  StorageOverviewResponse,
  StorageProviderConfig,
  StorageUseCase,
} from '@/types/storage'
import { STORAGE_PROVIDERS, STORAGE_USE_CASES } from '@/types/storage'
import { cn } from '@/lib/utils'

const storageUseCaseEnum = z.enum(STORAGE_USE_CASES)

const localConfigSchema = z.object({
  provider: z.literal('local_filesystem'),
  name: z.string().min(3, 'Name must be at least 3 characters long'),
  default_use_cases: z.array(storageUseCaseEnum).min(1, 'Select at least one use case'),
  base_path: z.string().min(1, 'Base path is required'),
  create_directories: z.boolean().default(true),
  expose_file_urls: z.boolean().default(false),
  enabled: z.boolean().default(true),
})

const gcsConfigSchema = z.object({
  provider: z.literal('google_cloud_storage'),
  name: z.string().min(3, 'Name must be at least 3 characters long'),
  default_use_cases: z.array(storageUseCaseEnum).min(1, 'Select at least one use case'),
  bucket_name: z.string().min(3, 'Bucket name is required'),
  base_path: z.string().default('/'),
  credentials_secret_name: z.string().min(3, 'Secret name is required'),
  public_read: z.boolean().default(false),
  signed_url_ttl_seconds: z.coerce
    .number()
    .min(60, 'TTL must be at least 60 seconds')
    .max(86_400, 'TTL cannot exceed 24 hours')
    .default(3600),
  enabled: z.boolean().default(true),
})

const storageFormSchema = z.discriminatedUnion('provider', [
  localConfigSchema,
  gcsConfigSchema,
])

type StorageFormValues = z.infer<typeof storageFormSchema>
const DEFAULT_LOCAL_BASE_PATH = '/var/med13/storage'
const DEFAULT_GCS_BASE_PATH = '/'

const providerLabels: Record<StorageFormValues['provider'], string> = {
  local_filesystem: 'Local Filesystem',
  google_cloud_storage: 'Google Cloud Storage',
}

const useCaseLabels: Record<StorageUseCase, string> = {
  pdf: 'PubMed PDFs',
  export: 'Exports',
  raw_source: 'Raw Source Payloads',
  backup: 'Backups',
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** exponent
  return `${value.toFixed(1)} ${units[exponent]}`
}

interface StorageConfigurationCardProps {
  configuration: StorageConfiguration
  isToggling: boolean
  onToggleEnabled: (
    configuration: StorageConfiguration,
    enabled: boolean,
    hasUsage: boolean,
  ) => Promise<void>
  onTestConnection: (configuration: StorageConfiguration) => Promise<void>
  isTesting: boolean
  isSelected: boolean
  onSelectionChange: (configurationId: string, selected: boolean) => void
  onDelete: (configuration: StorageConfiguration, hasUsage: boolean) => Promise<void>
  isDeleting: boolean
}

function StorageConfigurationCard({
  configuration,
  onToggleEnabled,
  isToggling,
  onTestConnection,
  isTesting,
  isSelected,
  onSelectionChange,
  onDelete,
  isDeleting,
}: StorageConfigurationCardProps) {
  const metricsQuery = useStorageMetrics(configuration.id)
  const healthQuery = useStorageHealth(configuration.id)
  const totalFiles = metricsQuery.data?.total_files ?? 0

  const handleToggle = async (checked: boolean) => {
    await onToggleEnabled(configuration, checked, totalFiles > 0)
  }

  const handleDelete = async () => {
    await onDelete(configuration, totalFiles > 0)
  }

  return (
    <Card key={configuration.id}>
      <CardHeader className="flex flex-col gap-4 border-b border-border/50 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="size-4 text-muted-foreground" />
            {configuration.name}
          </CardTitle>
          <CardDescription>{providerLabels[configuration.provider]}</CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            size="sm"
            variant={isSelected ? 'default' : 'outline'}
            onClick={() => onSelectionChange(configuration.id, !isSelected)}
          >
            {isSelected ? 'Selected' : 'Select'}
          </Button>
          <Switch
            checked={configuration.enabled}
            onCheckedChange={handleToggle}
            disabled={isToggling}
            id={`storage-toggle-${configuration.id}`}
          />
          <Label
            htmlFor={`storage-toggle-${configuration.id}`}
            className={cn('text-sm', !configuration.enabled && 'text-muted-foreground')}
          >
            {configuration.enabled ? 'Enabled' : 'Disabled'}
          </Label>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {configuration.default_use_cases.map((useCase) => (
            <Badge key={useCase} variant="secondary">
              {useCaseLabels[useCase]}
            </Badge>
          ))}
        </div>
        <div className="text-sm text-muted-foreground">
          <div>Capabilities: {configuration.supported_capabilities.join(', ') || 'n/a'}</div>
          {'base_path' in configuration.config && (
            <div>Base Path: {configuration.config.base_path}</div>
          )}
          {'bucket_name' in configuration.config && (
            <div>Bucket: {configuration.config.bucket_name}</div>
          )}
        </div>
        <Separator />
        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <p className="text-xs text-muted-foreground">Health</p>
            <p className="flex items-center gap-2 font-medium">
              <ShieldCheck
                className={cn('size-4', {
                  'text-emerald-500': healthQuery.data?.status === 'healthy',
                  'text-amber-500': healthQuery.data?.status === 'degraded',
                  'text-destructive': healthQuery.data?.status === 'offline',
                })}
              />
              {healthQuery.data?.status ?? 'Unknown'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Files Managed</p>
            <p className="font-medium">{totalFiles}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Error Rate</p>
            <p className="font-medium">
              {metricsQuery.data?.error_rate
                ? `${(metricsQuery.data.error_rate * 100).toFixed(1)}%`
                : '0%'}
            </p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex flex-wrap justify-end gap-3 border-t border-border/50 pt-4">
        <Button
          variant="outline"
          onClick={() => onTestConnection(configuration)}
          disabled={isTesting}
        >
          {isTesting ? (
            <>
              <Loader2 className="mr-2 size-4 animate-spin" />
              Testing...
            </>
          ) : (
            <>
              <TestTube className="mr-2 size-4" />
              Test Connection
            </>
          )}
        </Button>
        <Button
          variant="destructive"
          onClick={handleDelete}
          disabled={isDeleting}
        >
          {isDeleting ? (
            <>
              <Loader2 className="mr-2 size-4 animate-spin" />
              Removing...
            </>
          ) : (
            <>
              <Trash2 className="mr-2 size-4" />
              Delete
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}

function StorageOverviewSection({ overview }: { overview: StorageOverviewResponse }) {
  const topConfigurations = useMemo(() => {
    return overview.configurations
      .slice()
      .sort((a, b) => (b.usage?.total_files ?? 0) - (a.usage?.total_files ?? 0))
      .slice(0, 3)
  }, [overview.configurations])

  const avgFilesPerConfig = overview.totals.enabled_configurations
    ? Math.round(overview.totals.total_files / overview.totals.enabled_configurations)
    : 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="size-4 text-muted-foreground" />
          Storage Platform Overview
        </CardTitle>
        <CardDescription>
          Updated {new Date(overview.generated_at).toLocaleTimeString()} – capacity forecasting and
          recent usage trends.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <p className="text-xs text-muted-foreground">Enabled configurations</p>
            <p className="text-2xl font-semibold">
              {overview.totals.enabled_configurations} / {overview.totals.total_configurations}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Files managed</p>
            <p className="text-2xl font-semibold">{overview.totals.total_files.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Storage consumed</p>
            <p className="text-2xl font-semibold">
              {formatBytes(overview.totals.total_size_bytes)}
            </p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="border-dashed bg-muted/40">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="size-4 text-muted-foreground" />
                Capacity planning
              </CardTitle>
              <CardDescription>
                Average of {avgFilesPerConfig.toLocaleString()} files per active configuration.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Healthy: {overview.totals.healthy_configurations} • Degraded: {overview.totals.degraded_configurations} •
                Offline: {overview.totals.offline_configurations}
              </p>
            </CardContent>
          </Card>
          <Card className="border-dashed">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ShieldCheck className="size-4 text-muted-foreground" />
                Top configurations
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {topConfigurations.map((entry) => (
                <div key={entry.configuration.id} className="flex items-center justify-between text-sm">
                  <div>
                    <p className="font-medium">{entry.configuration.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {entry.usage?.total_files.toLocaleString() ?? 0} files •{' '}
                      {entry.health?.status ?? 'unknown'}
                    </p>
                  </div>
                  <span className="text-xs font-semibold">
                    {formatBytes(entry.usage?.total_size_bytes ?? 0)}
                  </span>
                </div>
              ))}
              {topConfigurations.length === 0 && (
                <p className="text-sm text-muted-foreground">No usage data yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  )
}

function BulkActionBar({
  count,
  onClear,
  onEnable,
  onDisable,
  onDelete,
  isProcessing,
}: {
  count: number
  onClear: () => void
  onEnable: () => void
  onDisable: () => void
  onDelete: () => void
  isProcessing: boolean
}) {
  if (count === 0) {
    return null
  }

  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
        <div className="text-sm font-medium">
          {count} configuration{count === 1 ? '' : 's'} selected
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={onEnable} disabled={isProcessing}>
            Enable
          </Button>
          <Button variant="outline" size="sm" onClick={onDisable} disabled={isProcessing}>
            Disable
          </Button>
          <Button variant="destructive" size="sm" onClick={onDelete} disabled={isProcessing}>
            Delete
          </Button>
          <Button variant="ghost" size="sm" onClick={onClear}>
            Clear
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export function StorageConfigurationManager() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [togglingId, setTogglingId] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [bulkAction, setBulkAction] = useState<'enable' | 'disable' | 'delete' | null>(null)
  const storageQuery = useStorageConfigurations()
  const overviewQuery = useStorageOverview()
  const storageMutations = useStorageMutations()
  const maintenanceQuery = useMaintenanceState()
  const isMaintenanceActive = maintenanceQuery.data?.state.is_active ?? false
  const [pendingCreate, setPendingCreate] = useState<StorageFormValues | null>(null)
  const [maintenanceModalOpen, setMaintenanceModalOpen] = useState(false)

  const form = useForm<StorageFormValues>({
    resolver: zodResolver(storageFormSchema),
    defaultValues: {
      provider: 'local_filesystem',
      name: '',
      base_path: DEFAULT_LOCAL_BASE_PATH,
      create_directories: true,
      expose_file_urls: false,
      default_use_cases: ['pdf'],
      enabled: true,
    } as StorageFormValues,
  })

  const selectedProvider = form.watch('provider')
  const configurations = useMemo(
    () => storageQuery.data?.data ?? [],
    [storageQuery.data?.data],
  )
  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds])
  const overviewMap = useMemo(() => {
    const map = new Map<string, StorageConfigurationStats>()
    overviewQuery.data?.configurations.forEach((entry) => {
      map.set(entry.configuration.id, entry)
    })
    return map
  }, [overviewQuery.data])

  useEffect(() => {
    if (!configurations.length && selectedIds.length) {
      setSelectedIds([])
    } else {
      const configurationIds = new Set(configurations.map((item) => item.id))
      setSelectedIds((current) => current.filter((id) => configurationIds.has(id)))
    }
  }, [configurations, selectedIds.length])

  const submitConfiguration = async (values: StorageFormValues) => {
    const payload = convertFormToPayload(values)
    try {
      await storageMutations.createConfiguration.mutateAsync(payload)
      toast.success(`Created storage configuration "${values.name}"`)
      form.reset()
      setDialogOpen(false)
    } catch (error) {
      console.error('[StorageConfigurationManager] Failed to create configuration', error)
      toast.error('Unable to create storage configuration')
    }
  }

  const requireMaintenance = (): boolean => {
    if (maintenanceQuery.isLoading) {
      toast.error('Maintenance status is still loading. Please try again.')
      return true
    }
    return false
  }

  const updateConfigurationEnabled = async (
    configuration: StorageConfiguration,
    enabled: boolean,
    hasUsage: boolean,
  ) => {
    if (requireMaintenance()) {
      return
    }
    if (hasUsage && !isMaintenanceActive) {
      toast.error('Enable maintenance mode before changing a storage backend in use.')
      return
    }
    setTogglingId(configuration.id)
    try {
      await storageMutations.updateConfiguration.mutateAsync({
        configurationId: configuration.id,
        payload: { enabled },
      })
      toast.success(`${configuration.name} ${enabled ? 'enabled' : 'disabled'}`)
    } catch (error) {
      console.error('[StorageConfigurationManager] Failed to toggle configuration', error)
      toast.error('Unable to update configuration status')
    } finally {
      setTogglingId(null)
    }
  }

  const handleCreate = async (values: StorageFormValues) => {
    const hasEnabledConfig = configurations.some((config) => config.enabled)
    const providerChanged = values.provider !== 'local_filesystem'
    const basePathChanged =
      (values.provider === 'local_filesystem' && values.base_path !== DEFAULT_LOCAL_BASE_PATH) ||
      (values.provider === 'google_cloud_storage' && values.base_path !== DEFAULT_GCS_BASE_PATH)

    if (!isMaintenanceActive && hasEnabledConfig && (providerChanged || basePathChanged)) {
      setPendingCreate(values)
      setMaintenanceModalOpen(true)
      return
    }

    await submitConfiguration(values)
  }

  const handleTestConnection = async (configuration: StorageConfiguration) => {
    setTestingId(configuration.id)
    try {
      const result = await storageMutations.testConfiguration.mutateAsync({
        configurationId: configuration.id,
      })
      if (result.success) {
        toast.success(result.message ?? 'Connection successful')
      } else {
        toast.error(result.message ?? 'Connection failed')
      }
    } catch (error) {
      console.error('[StorageConfigurationManager] Failed to test storage configuration', error)
      toast.error('Unable to test storage configuration')
    } finally {
      setTestingId(null)
    }
  }

  const handleDeleteConfiguration = async (
    configuration: StorageConfiguration,
    hasUsage: boolean,
    force = false,
  ) => {
    if (requireMaintenance()) {
      return
    }
    if (hasUsage && !isMaintenanceActive && !force) {
      toast.error('Enable maintenance mode before deleting a storage backend in use.')
      return
    }
    setDeletingId(configuration.id)
    try {
      await storageMutations.deleteConfiguration.mutateAsync({
        configurationId: configuration.id,
        force,
      })
      toast.success(force ? 'Configuration deleted' : 'Configuration disabled')
    } catch (error) {
      console.error('[StorageConfigurationManager] Failed to delete configuration', error)
      toast.error('Unable to delete configuration')
    } finally {
      setDeletingId(null)
    }
  }

  const handleBulkToggle = async (enabled: boolean) => {
    setBulkAction(enabled ? 'enable' : 'disable')
    try {
      for (const configurationId of selectedIds) {
        const configuration = configurations.find((item) => item.id === configurationId)
        if (!configuration) {
          continue
        }
        const usage = overviewMap.get(configuration.id)?.usage?.total_files ?? 0
        await updateConfigurationEnabled(configuration, enabled, usage > 0)
      }
      toast.success(`Updated ${selectedIds.length} configuration${selectedIds.length === 1 ? '' : 's'}`)
      setSelectedIds([])
    } finally {
      setBulkAction(null)
    }
  }

  const handleBulkDelete = async () => {
    setBulkAction('delete')
    try {
      for (const configurationId of selectedIds) {
        const configuration = configurations.find((item) => item.id === configurationId)
        if (!configuration) {
          continue
        }
        const usage = overviewMap.get(configuration.id)?.usage?.total_files ?? 0
        await handleDeleteConfiguration(configuration, usage > 0)
      }
      setSelectedIds([])
    } finally {
      setBulkAction(null)
    }
  }

  const handleMaintenanceConfirm = async () => {
    if (!pendingCreate) {
      setMaintenanceModalOpen(false)
      return
    }
    await submitConfiguration(pendingCreate)
    setPendingCreate(null)
    setMaintenanceModalOpen(false)
  }

  const hasConfigurations = configurations.length > 0

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">Storage Platform</h2>
          <p className="text-sm text-muted-foreground">
            Manage where PDFs, exports, and raw source files are stored.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>Add Configuration</Button>
      </div>

      {overviewQuery.isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : overviewQuery.data ? (
        <StorageOverviewSection overview={overviewQuery.data} />
      ) : null}

      {storageQuery.isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : hasConfigurations ? (
        <div className="space-y-4">
          {configurations.map((configuration) => (
            <StorageConfigurationCard
              key={configuration.id}
              configuration={configuration}
              onToggleEnabled={updateConfigurationEnabled}
              onTestConnection={handleTestConnection}
              isTesting={testingId === configuration.id && storageMutations.testConfiguration.isPending}
              isToggling={togglingId === configuration.id && storageMutations.updateConfiguration.isPending}
              isSelected={selectedSet.has(configuration.id)}
              onSelectionChange={(id, selected) => {
                setSelectedIds((current) =>
                  selected ? [...new Set([...current, id])] : current.filter((item) => item !== id),
                )
              }}
              onDelete={handleDeleteConfiguration}
              isDeleting={deletingId === configuration.id && storageMutations.deleteConfiguration.isPending}
            />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex items-center gap-3 py-8 text-muted-foreground">
            <AlertCircle className="size-4" />
            No storage configurations found. Create one to begin storing artifacts.
          </CardContent>
        </Card>
      )}

      <BulkActionBar
        count={selectedIds.length}
        onClear={() => setSelectedIds([])}
        onEnable={() => handleBulkToggle(true)}
        onDisable={() => handleBulkToggle(false)}
        onDelete={handleBulkDelete}
        isProcessing={bulkAction !== null}
      />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>New Storage Configuration</DialogTitle>
            <DialogDescription>
              Define a storage backend for PDFs, exports, and ingestion payloads.
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleCreate)} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Cloud Archive" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="provider"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Provider</FormLabel>
                      <FormControl>
                        <select
                          {...field}
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm"
                        >
                          {STORAGE_PROVIDERS.map((provider) => (
                            <option key={provider} value={provider}>
                              {providerLabels[provider]}
                            </option>
                          ))}
                        </select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {selectedProvider === 'local_filesystem' ? (
                <div className="grid gap-4 md:grid-cols-2">
                  <FormField
                    control={form.control}
                    name="base_path"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Base Path</FormLabel>
                        <FormControl>
                          <Input placeholder="/var/med13/storage" {...field} />
                        </FormControl>
                        <FormDescription>Directory where files will be stored.</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="create_directories"
                    render={({ field }) => (
                      <FormItem className="flex items-center justify-between rounded-md border p-3">
                        <div>
                          <FormLabel>Create directories</FormLabel>
                          <FormDescription>Automatically create missing directories.</FormDescription>
                        </div>
                        <FormControl>
                          <Switch
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="expose_file_urls"
                    render={({ field }) => (
                      <FormItem className="flex items-center justify-between rounded-md border p-3">
                        <div>
                          <FormLabel>Expose file URLs</FormLabel>
                          <FormDescription>
                            Generate file:// URLs for debugging. Not recommended for production.
                          </FormDescription>
                        </div>
                        <FormControl>
                          <Switch checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>
              ) : (
                <div className="grid gap-4">
                  <FormField
                    control={form.control}
                    name="bucket_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Bucket Name</FormLabel>
                        <FormControl>
                          <Input placeholder="med13-storage" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="base_path"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Path Prefix</FormLabel>
                          <FormControl>
                            <Input placeholder="/pubmed" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="credentials_secret_name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Credentials Secret</FormLabel>
                          <FormControl>
                            <Input placeholder="projects/.../secrets/med13" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <FormField
                      control={form.control}
                      name="public_read"
                      render={({ field }) => (
                        <FormItem className="flex items-center justify-between rounded-md border p-3">
                          <div>
                            <FormLabel>Public Read</FormLabel>
                            <FormDescription>Allow unsigned public downloads.</FormDescription>
                          </div>
                          <FormControl>
                            <Switch checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="signed_url_ttl_seconds"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Signed URL TTL (seconds)</FormLabel>
                          <FormControl>
                            <Input type="number" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </div>
              )}

              <Separator />

              <FormField
                control={form.control}
                name="default_use_cases"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Default Use Cases</FormLabel>
                    <div className="flex flex-wrap gap-2">
                      {STORAGE_USE_CASES.map((useCase) => {
                        const selected = field.value.includes(useCase)
                        return (
                          <Button
                            key={useCase}
                            type="button"
                            size="sm"
                            variant={selected ? 'default' : 'outline'}
                            onClick={() => {
                              const next = selected
                                ? field.value.filter((item) => item !== useCase)
                                : [...field.value, useCase]
                              field.onChange(next)
                            }}
                          >
                            {useCaseLabels[useCase]}
                          </Button>
                        )
                      })}
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={storageMutations.createConfiguration.isPending}>
                  {storageMutations.createConfiguration.isPending && (
                    <Loader2 className="mr-2 size-4 animate-spin" />
                  )}
                  Create Configuration
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <Dialog open={maintenanceModalOpen} onOpenChange={setMaintenanceModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Enable maintenance mode first</DialogTitle>
            <DialogDescription>
              At least one storage backend is currently enabled. Enable maintenance mode to log out
              users and prevent writes before changing the provider or base path.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setPendingCreate(null)
                setMaintenanceModalOpen(false)
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleMaintenanceConfirm}>
              Continue without maintenance
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  )
}

function convertFormToPayload(values: StorageFormValues): CreateStorageConfigurationRequest {
  const common = {
    name: values.name.trim(),
    provider: values.provider,
    default_use_cases: values.default_use_cases,
    enabled: values.enabled,
  }

  if (values.provider === 'local_filesystem') {
    return {
      ...common,
      config: {
        provider: 'local_filesystem',
        base_path: values.base_path,
        create_directories: values.create_directories,
        expose_file_urls: values.expose_file_urls,
      } satisfies StorageProviderConfig,
    }
  }

  return {
    ...common,
    config: {
      provider: 'google_cloud_storage',
      bucket_name: values.bucket_name,
      base_path: values.base_path,
      credentials_secret_name: values.credentials_secret_name,
      public_read: values.public_read,
      signed_url_ttl_seconds: values.signed_url_ttl_seconds,
    } satisfies StorageProviderConfig,
  }
}
