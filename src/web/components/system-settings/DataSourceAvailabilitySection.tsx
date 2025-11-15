"use client"

import { useMemo, useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Select } from '@/components/ui/select'
import {
  useAdminCatalogEntries,
  useCatalogAvailability,
  useCatalogAvailabilitySummaries,
  useSetCatalogGlobalAvailability,
  useSetCatalogProjectAvailability,
  useClearCatalogGlobalAvailability,
  useClearCatalogProjectAvailability,
  useBulkSetCatalogGlobalAvailability,
} from '@/lib/queries/data-sources'
import { useResearchSpaces } from '@/lib/queries/research-spaces'
import { Loader2, SlidersHorizontal, ShieldOff, Search } from 'lucide-react'
import type { SourceCatalogEntry } from '@/lib/types/data-discovery'
import type {
  DataSourceAvailability,
  PermissionLevel,
} from '@/lib/api/data-source-activation'
import { toast } from 'sonner'

const EMPTY_CATALOG_ENTRIES: SourceCatalogEntry[] = []
const EMPTY_AVAILABILITY_SUMMARIES: DataSourceAvailability[] = []

const PERMISSION_LABELS: Record<PermissionLevel, string> = {
  available: 'Available',
  visible: 'Visible',
  blocked: 'Blocked',
}

const PERMISSION_VARIANTS: Record<PermissionLevel, 'default' | 'secondary' | 'destructive'> = {
  available: 'default',
  visible: 'secondary',
  blocked: 'destructive',
}

const PERMISSION_DESCRIPTIONS: Record<PermissionLevel, string> = {
  available: 'Catalog + testing enabled',
  visible: 'Catalog only',
  blocked: 'Hidden and disabled',
}

const PERMISSION_ORDER: PermissionLevel[] = ['available', 'visible', 'blocked']

function getEffectivePermissionForSpace(
  summary: DataSourceAvailability | undefined,
  spaceId: string | null,
): PermissionLevel {
  if (!summary) {
    return 'available'
  }
  if (spaceId) {
    const override = summary.project_rules.find((rule) => rule.research_space_id === spaceId)
    if (override) {
      return override.permission_level
    }
  }
  return summary.global_rule?.permission_level ?? 'available'
}

export function DataSourceAvailabilitySection() {
  const [selectedSource, setSelectedSource] = useState<SourceCatalogEntry | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  const catalogQuery = useAdminCatalogEntries()
  const catalogEntries = catalogQuery.data ?? EMPTY_CATALOG_ENTRIES

  const availabilitySummariesQuery = useCatalogAvailabilitySummaries()
  const availabilitySummaries =
    availabilitySummariesQuery.data ?? EMPTY_AVAILABILITY_SUMMARIES

  const availabilityQuery = useCatalogAvailability(dialogOpen ? selectedSource?.id ?? null : null)
  const spacesQuery = useResearchSpaces({ limit: 100 })
  const spaces = spacesQuery.data?.spaces ?? []
  const totalSpaces = spaces.length

  const setGlobalAvailability = useSetCatalogGlobalAvailability()
  const clearGlobalAvailability = useClearCatalogGlobalAvailability()
  const setProjectAvailability = useSetCatalogProjectAvailability()
  const clearProjectAvailability = useClearCatalogProjectAvailability()
  const bulkGlobalAvailability = useBulkSetCatalogGlobalAvailability()

  const availabilitySummaryMap = useMemo(() => {
    const entries = new Map<string, NonNullable<typeof availabilitySummaries>[number]>()
    availabilitySummaries.forEach((summary) => {
      entries.set(summary.catalog_entry_id, summary)
    })
    return entries
  }, [availabilitySummaries])

  const filteredEntries = useMemo(() => {
    if (!searchTerm.trim()) {
      return catalogEntries
    }
    const term = searchTerm.toLowerCase()
    return catalogEntries.filter((entry) => {
      return (
        entry.name.toLowerCase().includes(term) ||
        entry.description.toLowerCase().includes(term) ||
        entry.category.toLowerCase().includes(term)
      )
    })
  }, [catalogEntries, searchTerm])
  const visibleCount = filteredEntries.length
  const totalCount = catalogEntries.length

  const selectedOverrides = useMemo(() => {
    const overrides = new Map<string, PermissionLevel>()
    availabilityQuery.data?.project_rules.forEach((rule) => {
      if (rule.research_space_id) {
        overrides.set(rule.research_space_id, rule.permission_level)
      }
    })
    return overrides
  }, [availabilityQuery.data])

  const getStatusMeta = (sourceId: string) => {
    const summary = availabilitySummaryMap.get(sourceId)
    if (!summary) {
      return {
        label: availabilitySummariesQuery.isLoading ? 'Loading policies…' : 'Defaults to Available',
        description: availabilitySummariesQuery.isLoading
          ? 'Fetching latest availability rules'
          : 'No overrides configured',
        variant: availabilitySummariesQuery.isLoading ? ('outline' as const) : ('secondary' as const),
        isLoading: availabilitySummariesQuery.isLoading,
      }
    }

    const effectivePermission = summary.effective_permission_level
    const variant = PERMISSION_VARIANTS[effectivePermission]
    let description = `Global: ${PERMISSION_LABELS[summary.global_rule?.permission_level ?? 'available']}`

    if (totalSpaces > 0) {
      const counts: Record<PermissionLevel, number> = {
        available: 0,
        visible: 0,
        blocked: 0,
      }
      spaces.forEach((space) => {
        const permission = getEffectivePermissionForSpace(summary, space.id)
        counts[permission] += 1
      })
      description = `Available ${counts.available} • Visible ${counts.visible} • Blocked ${counts.blocked}`
    }

    if (summary.project_rules.length > 0) {
      description += ` • ${summary.project_rules.length} override${
        summary.project_rules.length === 1 ? '' : 's'
      }`
    }

    return {
      label: PERMISSION_LABELS[effectivePermission],
      description,
      variant,
      isLoading: false,
    }
  }

  const handleManage = (source: SourceCatalogEntry) => {
    setSelectedSource(source)
    setDialogOpen(true)
  }

  const handleGlobalPermissionChange = async (permissionLevel: PermissionLevel) => {
    if (!selectedSource) return
    try {
      await setGlobalAvailability.mutateAsync({ catalogEntryId: selectedSource.id, permissionLevel })
      toast.success(`Global permission set to ${PERMISSION_LABELS[permissionLevel]}`)
    } catch (error) {
      toast.error('Failed to update global permission')
    }
  }

  const handleGlobalReset = async () => {
    if (!selectedSource) return
    try {
      await clearGlobalAvailability.mutateAsync({ catalogEntryId: selectedSource.id })
      toast.success('Global override removed')
    } catch (error) {
      toast.error('Failed to reset global availability')
    }
  }

  const handleProjectPermissionChange = async (researchSpaceId: string, permissionLevel: PermissionLevel) => {
    if (!selectedSource) return
    try {
      await setProjectAvailability.mutateAsync({
        catalogEntryId: selectedSource.id,
        researchSpaceId,
        permissionLevel,
      })
      toast.success('Permission updated for research space')
    } catch (error) {
      toast.error('Failed to update research space permission')
    }
  }

  const handleProjectReset = async (researchSpaceId: string) => {
    if (!selectedSource) return
    try {
      await clearProjectAvailability.mutateAsync({
        catalogEntryId: selectedSource.id,
        researchSpaceId,
      })
      toast.success('Project override removed')
    } catch (error) {
      toast.error('Failed to remove project override')
    }
  }

  const handleBulkPermissionChange = async (permissionLevel: PermissionLevel) => {
    if (filteredEntries.length === 0) {
      toast.info('No data sources match the current filters.')
      return
    }
    const ids = filteredEntries.map((entry) => entry.id)
    const payloadIds = ids.length === totalCount ? undefined : ids
    try {
      await bulkGlobalAvailability.mutateAsync({
        permissionLevel,
        catalogEntryIds: payloadIds,
      })
      const affectedCount = payloadIds ? ids.length : totalCount
      toast.success(
        `Applied ${PERMISSION_LABELS[permissionLevel]} to ${affectedCount} data source${
          affectedCount === 1 ? '' : 's'
        } globally`,
      )
    } catch (error) {
      toast.error('Failed to apply bulk update')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Source Availability</CardTitle>
        <CardDescription>
          Control which data sources are available globally or inside specific research spaces.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {catalogQuery.isLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Loading data catalog…
          </div>
        ) : catalogQuery.isError ? (
          <p className="text-sm text-destructive">Unable to load catalog entries.</p>
        ) : catalogEntries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No data sources found.</p>
        ) : (
          <>
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center">
                <div className="relative w-full sm:max-w-sm">
                  <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={searchTerm}
                    placeholder="Search by name, description, or category"
                    onChange={(event) => setSearchTerm(event.target.value)}
                    className="pl-10"
                  />
                </div>
                <p className="text-sm text-muted-foreground">
                  Showing {visibleCount} of {totalCount} sources
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                    disabled={bulkGlobalAvailability.isPending || visibleCount === 0}
                    onClick={() => handleBulkPermissionChange('available')}
                >
                  {bulkGlobalAvailability.isPending && (
                    <Loader2 className="mr-2 size-4 animate-spin" />
                  )}
                    Set Available
                </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={bulkGlobalAvailability.isPending || visibleCount === 0}
                    onClick={() => handleBulkPermissionChange('visible')}
                  >
                    Set Visible
                  </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={bulkGlobalAvailability.isPending || visibleCount === 0}
                    onClick={() => handleBulkPermissionChange('blocked')}
                >
                    Set Blocked
                </Button>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Bulk actions respect the current search filters. Use them to enable or disable groups quickly.
            </p>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEntries.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-sm text-muted-foreground">
                      No data sources match “{searchTerm}”.
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredEntries.map((source) => {
                    const statusMeta = getStatusMeta(source.id)
                    return (
                      <TableRow key={source.id}>
                        <TableCell>
                          <div className="font-medium">{source.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {source.description || 'No description'}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {source.category || 'Uncategorized'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {statusMeta.isLoading ? (
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Loader2 className="size-4 animate-spin" />
                              Loading status…
                            </div>
                          ) : (
                            <div className="flex flex-col gap-1">
                              <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
                              <span className="text-xs text-muted-foreground">
                                {statusMeta.description}
                              </span>
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" variant="outline" onClick={() => handleManage(source)}>
                            <SlidersHorizontal className="mr-2 size-4" />
                            Manage availability
                          </Button>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </>
        )}
      </CardContent>

      <Dialog open={dialogOpen} onOpenChange={(open) => {
        setDialogOpen(open)
        if (!open) setSelectedSource(null)
      }}>
        <DialogContent className="max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Manage availability</DialogTitle>
            <DialogDescription>
              {selectedSource ? selectedSource.name : 'Select a data source to manage availability.'}
            </DialogDescription>
          </DialogHeader>

          {availabilityQuery.isLoading || !selectedSource ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Loading availability…
            </div>
          ) : (
            <div className="space-y-6">
              <section className="rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Global availability</p>
                    <p className="text-sm text-muted-foreground">
                      {availabilityQuery.data?.global_rule
                        ? `Global override: ${
                            PERMISSION_LABELS[availabilityQuery.data.global_rule.permission_level]
                          }`
                        : 'No global override. Defaults to Available.'}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleGlobalPermissionChange('available')}
                      disabled={setGlobalAvailability.isPending}
                    >
                      {setGlobalAvailability.isPending && (
                        <Loader2 className="mr-2 size-4 animate-spin" />
                      )}
                      Set Available
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleGlobalPermissionChange('visible')}
                      disabled={setGlobalAvailability.isPending}
                    >
                      Set Visible
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleGlobalPermissionChange('blocked')}
                      disabled={setGlobalAvailability.isPending}
                    >
                      <ShieldOff className="mr-2 size-4" />
                      Set Blocked
                    </Button>
                    {availabilityQuery.data?.global_rule && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleGlobalReset}
                        disabled={clearGlobalAvailability.isPending}
                      >
                        Reset
                      </Button>
                    )}
                  </div>
                </div>
              </section>

              <section>
                <p className="mb-2 font-medium">Project-specific overrides</p>
                {spacesQuery.isLoading ? (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="size-4 animate-spin" />
                    Loading research spaces…
                  </div>
                ) : spacesQuery.data?.spaces?.length ? (
                  <div className="space-y-3">
                    {spacesQuery.data.spaces.map((space) => {
                      const override = selectedOverrides.get(space.id)
                      const effectivePermission = getEffectivePermissionForSpace(
                        availabilityQuery.data,
                        space.id,
                      )
                      const inheritedPermission =
                        availabilityQuery.data?.global_rule?.permission_level ?? 'available'
                      const selectValue = override ?? 'inherit'
                      return (
                        <div key={space.id} className="rounded-lg border p-3">
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium">{space.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {override === undefined
                                    ? `Inherits global (${PERMISSION_LABELS[inheritedPermission]})`
                                    : `Override: ${PERMISSION_LABELS[override]}`}
                                </p>
                              </div>
                              <div className="flex flex-col gap-2">
                                <Badge variant={PERMISSION_VARIANTS[effectivePermission]}>
                                  {PERMISSION_LABELS[effectivePermission]}
                                  {override ? ' • Override' : ''}
                                </Badge>
                                <Select
                                  value={selectValue}
                                  onChange={(event) => {
                                    const value = event.target.value as PermissionLevel | 'inherit'
                                    if (value === 'inherit') {
                                      handleProjectReset(space.id)
                                    } else {
                                      handleProjectPermissionChange(space.id, value)
                                    }
                                  }}
                                  disabled={
                                    setProjectAvailability.isPending || clearProjectAvailability.isPending
                                  }
                                >
                                  <option value="inherit">
                                    Inherit ({PERMISSION_LABELS[inheritedPermission]})
                                  </option>
                                  {PERMISSION_ORDER.map((permission) => (
                                    <option key={permission} value={permission}>
                                      {PERMISSION_LABELS[permission]} — {PERMISSION_DESCRIPTIONS[permission]}
                                    </option>
                                  ))}
                                </Select>
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No research spaces found.</p>
                )}
              </section>
            </div>
          )}

          <DialogFooter>
            <Button variant="secondary" onClick={() => setDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
