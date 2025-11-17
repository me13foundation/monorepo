"use client"

import { useMemo, useState } from 'react'
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
import { AlertCircle, HardDrive, Loader2, ShieldCheck, TestTube } from 'lucide-react'
import {
  useStorageConfigurations,
  useStorageHealth,
  useStorageMetrics,
  useStorageMutations,
} from '@/lib/queries/storage'
import type {
  CreateStorageConfigurationRequest,
  StorageConfiguration,
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

interface StorageConfigurationCardProps {
  configuration: StorageConfiguration
  isToggling: boolean
  onToggleEnabled: (configuration: StorageConfiguration, enabled: boolean) => Promise<void>
  onTestConnection: (configuration: StorageConfiguration) => Promise<void>
  isTesting: boolean
}

function StorageConfigurationCard({
  configuration,
  onToggleEnabled,
  isToggling,
  onTestConnection,
  isTesting,
}: StorageConfigurationCardProps) {
  const metricsQuery = useStorageMetrics(configuration.id)
  const healthQuery = useStorageHealth(configuration.id)

  const handleToggle = async (checked: boolean) => {
    await onToggleEnabled(configuration, checked)
  }

  return (
    <Card key={configuration.id}>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="size-4 text-muted-foreground" />
            {configuration.name}
          </CardTitle>
          <CardDescription>{providerLabels[configuration.provider]}</CardDescription>
        </div>
        <div className="flex items-center gap-2">
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
              <ShieldCheck className={cn('size-4', {
                'text-emerald-500': healthQuery.data?.status === 'healthy',
                'text-amber-500': healthQuery.data?.status === 'degraded',
                'text-destructive': healthQuery.data?.status === 'offline',
              })} />
              {healthQuery.data?.status ?? 'Unknown'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Files Managed</p>
            <p className="font-medium">{metricsQuery.data?.total_files ?? 0}</p>
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
      <CardFooter className="justify-end gap-3">
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
      </CardFooter>
    </Card>
  )
}

export function StorageConfigurationManager() {
  const [dialogOpen, setDialogOpen] = useState(false)
  const [testingId, setTestingId] = useState<string | null>(null)
  const [togglingId, setTogglingId] = useState<string | null>(null)
  const storageQuery = useStorageConfigurations()
  const storageMutations = useStorageMutations()

  const form = useForm<StorageFormValues>({
    resolver: zodResolver(storageFormSchema),
    defaultValues: {
      provider: 'local_filesystem',
      name: '',
      base_path: '/var/med13/storage',
      create_directories: true,
      expose_file_urls: false,
      default_use_cases: ['pdf'],
      enabled: true,
    } as StorageFormValues,
  })

  const selectedProvider = form.watch('provider')

  const handleCreate = async (values: StorageFormValues) => {
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

  const handleToggleEnabled = async (
    configuration: StorageConfiguration,
    enabled: boolean,
  ) => {
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

  const configurations = storageQuery.data ?? []
  const hasConfigurations = configurations.length > 0

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Storage Configuration</h2>
          <p className="text-sm text-muted-foreground">
            Manage where PDFs, exports, and raw source files are stored.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          Add Configuration
        </Button>
      </div>
      {storageQuery.isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : hasConfigurations ? (
        <div className="grid gap-4">
          {configurations.map((configuration) => (
            <StorageConfigurationCard
              key={configuration.id}
              configuration={configuration}
              onToggleEnabled={handleToggleEnabled}
              onTestConnection={handleTestConnection}
              isTesting={testingId === configuration.id && storageMutations.testConfiguration.isPending}
              isToggling={togglingId === configuration.id && storageMutations.updateConfiguration.isPending}
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
                      name="signed_url_ttl_seconds"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Signed URL TTL (seconds)</FormLabel>
                          <FormControl>
                            <Input type="number" min={60} max={86400} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                  <FormField
                    control={form.control}
                    name="credentials_secret_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Credential JSON Path</FormLabel>
                        <FormControl>
                          <Input placeholder="/secrets/gcs.json" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="public_read"
                    render={({ field }) => (
                      <FormItem className="flex items-center justify-between rounded-md border p-3">
                        <div>
                          <FormLabel>Public file access</FormLabel>
                          <FormDescription>Expose public URLs for stored files.</FormDescription>
                        </div>
                        <FormControl>
                          <Switch checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>
              )}

              <FormField
                control={form.control}
                name="default_use_cases"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Use Cases</FormLabel>
                    <div className="grid gap-2">
                      {STORAGE_USE_CASES.map((useCase) => {
                        const checked = field.value?.includes(useCase)
                        return (
                          <label
                            key={useCase}
                            className="flex cursor-pointer items-center justify-between rounded-md border p-3 text-sm"
                          >
                            <div className="space-y-1 pr-4">
                              <p className="font-medium">{useCaseLabels[useCase]}</p>
                              <p className="text-xs text-muted-foreground">
                                {useCase === 'pdf' && 'PubMed PDF archive and metadata'}
                                {useCase === 'export' && 'CSV/JSON exports from admin workflows'}
                                {useCase === 'raw_source' && 'Raw ingestion payloads'}
                                {useCase === 'backup' && 'Fallback backups for redundancy'}
                              </p>
                            </div>
                            <Switch
                              checked={checked}
                              onCheckedChange={(next) => {
                                if (next) {
                                  field.onChange([...(field.value ?? []), useCase])
                                } else {
                                  field.onChange(
                                    field.value?.filter((item) => item !== useCase) ?? [],
                                  )
                                }
                              }}
                            />
                          </label>
                        )
                      })}
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="enabled"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-md border p-3">
                    <div>
                      <FormLabel>Enable immediately</FormLabel>
                      <FormDescription>
                        Enabled configurations can be assigned to workflows.
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
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
