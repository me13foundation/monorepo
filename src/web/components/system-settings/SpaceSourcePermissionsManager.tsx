"use client"

import { useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Loader2 } from 'lucide-react'
import {
  useAdminCatalogEntries,
  useCatalogAvailabilitySummaries,
  useSetCatalogProjectAvailability,
  useClearCatalogProjectAvailability,
} from '@/lib/queries/data-sources'
import { useResearchSpaces } from '@/lib/queries/research-spaces'
import type { PermissionLevel, DataSourceAvailability } from '@/lib/api/data-source-activation'

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

function getEffectivePermission(
  summary: DataSourceAvailability | undefined,
  spaceId: string,
): PermissionLevel {
  if (!summary) {
    return 'available'
  }
  const override = summary.project_rules.find((rule) => rule.research_space_id === spaceId)
  if (override) {
    return override.permission_level
  }
  return summary.global_rule?.permission_level ?? 'available'
}

export function SpaceSourcePermissionsManager() {
  const catalogQuery = useAdminCatalogEntries()
  const spacesQuery = useResearchSpaces({ limit: 100 })
  const availabilitySummariesQuery = useCatalogAvailabilitySummaries()
  const setPermissionMutation = useSetCatalogProjectAvailability()
  const clearPermissionMutation = useClearCatalogProjectAvailability()

  const catalogEntries = catalogQuery.data ?? []
  const spaces = spacesQuery.data?.spaces ?? []

  const summaryMap = useMemo(() => {
    const data = availabilitySummariesQuery.data ?? []
    return new Map(data.map((summary) => [summary.catalog_entry_id, summary]))
  }, [availabilitySummariesQuery.data])

  const handlePermissionChange = async (
    sourceId: string,
    spaceId: string,
    value: PermissionLevel | 'inherit',
  ) => {
    if (value === 'inherit') {
      await clearPermissionMutation.mutateAsync({ catalogEntryId: sourceId, researchSpaceId: spaceId })
      return
    }
    await setPermissionMutation.mutateAsync({
      catalogEntryId: sourceId,
      researchSpaceId: spaceId,
      permissionLevel: value,
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Space-Source Permission Matrix</CardTitle>
        <CardDescription>
          Review and adjust the permission level each research space receives for catalog sources.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {catalogQuery.isLoading || spacesQuery.isLoading || availabilitySummariesQuery.isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ) : catalogEntries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No catalog entries available.</p>
        ) : spaces.length === 0 ? (
          <p className="text-sm text-muted-foreground">No research spaces available.</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-[220px]">Source</TableHead>
                  {spaces.map((space) => (
                    <TableHead key={space.id} className="min-w-[160px] text-center">
                      {space.name}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {catalogEntries.map((source) => {
                  const summary = summaryMap.get(source.id)
                  return (
                    <TableRow key={source.id}>
                      <TableCell>
                        <div className="font-medium">{source.name}</div>
                        <div className="text-xs text-muted-foreground">{source.category}</div>
                      </TableCell>
                      {spaces.map((space) => {
                        const override = summary?.project_rules.find(
                          (rule) => rule.research_space_id === space.id,
                        )
                        const effective = getEffectivePermission(summary, space.id)
                        const inherited = summary?.global_rule?.permission_level ?? 'available'
                        const selectValue = override ? override.permission_level : 'inherit'
                        return (
                          <TableCell key={`${source.id}-${space.id}`} className="text-center">
                            <div className="flex flex-col gap-2">
                              <Badge variant={PERMISSION_VARIANTS[effective]}>
                                {PERMISSION_LABELS[effective]}
                                {override ? ' • Override' : ''}
                              </Badge>
                              <Select
                                value={selectValue}
                                onChange={(event) =>
                                  handlePermissionChange(
                                    source.id,
                                    space.id,
                                    event.target.value as PermissionLevel | 'inherit',
                                  )
                                }
                                disabled={
                                  setPermissionMutation.isPending || clearPermissionMutation.isPending
                                }
                                className="w-full"
                              >
                                <option value="inherit">
                                  Inherit ({PERMISSION_LABELS[inherited]})
                                </option>
                                {PERMISSION_ORDER.map((permission) => (
                                  <option key={permission} value={permission}>
                                    {PERMISSION_LABELS[permission]} — {PERMISSION_DESCRIPTIONS[permission]}
                                  </option>
                                ))}
                              </Select>
                            </div>
                          </TableCell>
                        )
                      })}
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
        {(setPermissionMutation.isPending || clearPermissionMutation.isPending) && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Applying permission change…
          </div>
        )}
      </CardContent>
    </Card>
  )
}
