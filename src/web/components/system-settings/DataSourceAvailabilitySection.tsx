"use client"

import { useMemo, useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
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
import type { DataSourceAvailability } from '@/lib/api/data-source-activation'
import { toast } from 'sonner'

const EMPTY_CATALOG_ENTRIES: SourceCatalogEntry[] = []
const EMPTY_AVAILABILITY_SUMMARIES: DataSourceAvailability[] = []

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
    const overrides = new Map<string, boolean>()
    availabilityQuery.data?.project_rules.forEach((rule) => {
      if (rule.research_space_id) {
        overrides.set(rule.research_space_id, rule.is_active)
      }
    })
    return overrides
  }, [availabilityQuery.data])

  const getStatusMeta = (sourceId: string) => {
    const summary = availabilitySummaryMap.get(sourceId)
    if (!summary) {
      return {
        label: availabilitySummariesQuery.isLoading ? 'Loading policies…' : 'Active globally',
        description: availabilitySummariesQuery.isLoading
          ? 'Fetching latest availability rules'
          : 'Defaults to global active state',
        variant: availabilitySummariesQuery.isLoading ? ('outline' as const) : ('secondary' as const),
        isLoading: availabilitySummariesQuery.isLoading,
      }
    }

    const defaultState = summary.global_rule?.is_active ?? true
    const overrideMap = new Map<string, boolean>()
    summary.project_rules.forEach((rule) => {
      if (rule.research_space_id) {
        overrideMap.set(rule.research_space_id, rule.is_active)
      }
    })

    let activeCount: number | null = null
    if (totalSpaces > 0) {
      activeCount = spaces.reduce((count, space) => {
        const override = overrideMap.get(space.id)
        const isActive = override ?? defaultState
        return isActive ? count + 1 : count
      }, 0)
    }

    let label: string
    let variant: 'default' | 'secondary' | 'destructive'
    if (activeCount === null) {
      label = defaultState ? 'Active globally' : 'Inactive globally'
      variant = defaultState ? 'default' : 'destructive'
    } else if (activeCount === totalSpaces) {
      label = totalSpaces === 1 ? 'Active in 1 space' : 'Active in all spaces'
      variant = 'default'
    } else if (activeCount === 0) {
      label = 'Inactive in all spaces'
      variant = 'destructive'
    } else {
      label = `Active in ${activeCount}/${totalSpaces} spaces`
      variant = 'secondary'
    }

    const overrideCount = summary.project_rules.length
    const descriptionParts: string[] = []
    if (overrideCount > 0) {
      descriptionParts.push(
        `${overrideCount} override${overrideCount === 1 ? '' : 's'}`,
      )
    }
    descriptionParts.push(`Default: ${defaultState ? 'active' : 'inactive'}`)

    return {
      label,
      description: descriptionParts.join(' • '),
      variant,
      isLoading: false,
    }
  }

  const handleManage = (source: SourceCatalogEntry) => {
    setSelectedSource(source)
    setDialogOpen(true)
  }

  const handleGlobalToggle = async (isActive: boolean) => {
    if (!selectedSource) return
    try {
      await setGlobalAvailability.mutateAsync({ catalogEntryId: selectedSource.id, isActive })
      toast.success(`Global availability updated to ${isActive ? 'active' : 'inactive'}`)
    } catch (error) {
      toast.error('Failed to update global availability')
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

  const handleProjectToggle = async (researchSpaceId: string, isActive: boolean) => {
    if (!selectedSource) return
    try {
      await setProjectAvailability.mutateAsync({
        catalogEntryId: selectedSource.id,
        researchSpaceId,
        isActive,
      })
      toast.success(`Availability updated for project`)
    } catch (error) {
      toast.error('Failed to update project availability')
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

  const handleBulkToggle = async (isActive: boolean) => {
    if (filteredEntries.length === 0) {
      toast.info('No data sources match the current filters.')
      return
    }
    const ids = filteredEntries.map((entry) => entry.id)
    const payloadIds = ids.length === totalCount ? undefined : ids
    try {
      await bulkGlobalAvailability.mutateAsync({
        isActive,
        catalogEntryIds: payloadIds,
      })
      const affectedCount = payloadIds ? ids.length : totalCount
      toast.success(
        `${isActive ? 'Enabled' : 'Disabled'} ${affectedCount} data source${
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
                  onClick={() => handleBulkToggle(true)}
                >
                  {bulkGlobalAvailability.isPending && (
                    <Loader2 className="mr-2 size-4 animate-spin" />
                  )}
                  Enable filtered
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={bulkGlobalAvailability.isPending || visibleCount === 0}
                  onClick={() => handleBulkToggle(false)}
                >
                  Disable filtered
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
                        ? `Global override set to ${availabilityQuery.data.global_rule.is_active ? 'active' : 'inactive'}`
                        : 'No global override. Defaults to active.'}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleGlobalToggle(true)}
                      disabled={setGlobalAvailability.isPending}
                    >
                      {setGlobalAvailability.isPending && (
                        <Loader2 className="mr-2 size-4 animate-spin" />
                      )}
                      Enable globally
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleGlobalToggle(false)}
                      disabled={setGlobalAvailability.isPending}
                    >
                      <ShieldOff className="mr-2 size-4" />
                      Disable globally
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
                      const effective = override ?? availabilityQuery.data?.global_rule?.is_active ?? true
                      return (
                        <div key={space.id} className="rounded-lg border p-3">
                          <div className="flex flex-col gap-1">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium">{space.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {override === undefined
                                    ? `Inherits global (${effective ? 'active' : 'inactive'})`
                                    : `Override: ${override ? 'active' : 'inactive'}`}
                                </p>
                              </div>
                              <div className="flex flex-wrap gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleProjectToggle(space.id, true)}
                                  disabled={setProjectAvailability.isPending}
                                >
                                  Activate
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleProjectToggle(space.id, false)}
                                  disabled={setProjectAvailability.isPending}
                                >
                                  Deactivate
                                </Button>
                                {override !== undefined && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleProjectReset(space.id)}
                                    disabled={clearProjectAvailability.isPending}
                                  >
                                    Clear override
                                  </Button>
                                )}
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
