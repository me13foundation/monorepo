'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useSpaceContext } from '@/components/space-context-provider'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useResearchSpace, useUpdateResearchSpace } from '@/lib/queries/research-spaces'
import { Loader2, Settings } from 'lucide-react'
import type { ResearchSpace } from '@/types/research-space'
import {
  SpaceStatus,
  type ResearchSpaceSettings,
  type UpdateSpaceRequest,
} from '@/types/research-space'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

interface SpaceSettingsClientProps {
  spaceId: string
}

interface SpaceFormState {
  name: string
  slug: string
  description: string
  status: SpaceStatus
  tagsInput: string
}

interface AdvancedSettingsState {
  autoApprove: boolean
  requireReview: boolean
  reviewThreshold: number
  maxDataSources: number
  allowedSourceTypes: string
  publicRead: boolean
  allowInvites: boolean
  emailNotifications: boolean
  notificationFrequency: string
}

const toFormState = (space?: ResearchSpace): SpaceFormState => ({
  name: space?.name ?? '',
  slug: space?.slug ?? '',
  description: space?.description ?? '',
  status: space?.status ?? SpaceStatus.ACTIVE,
  tagsInput: (space?.tags ?? []).join(', '),
})

const toAdvancedState = (settings?: ResearchSpaceSettings): AdvancedSettingsState => ({
  autoApprove: settings?.auto_approve ?? false,
  requireReview: settings?.require_review ?? true,
  reviewThreshold: settings?.review_threshold ?? 0.8,
  maxDataSources: settings?.max_data_sources ?? 25,
  allowedSourceTypes: (settings?.allowed_source_types ?? []).join(', '),
  publicRead: settings?.public_read ?? false,
  allowInvites: settings?.allow_invites ?? true,
  emailNotifications: settings?.email_notifications ?? true,
  notificationFrequency: settings?.notification_frequency ?? 'weekly',
})

export default function SpaceSettingsClient({ spaceId }: SpaceSettingsClientProps) {
  const { setCurrentSpaceId } = useSpaceContext()
  const { data: space, isLoading } = useResearchSpace(spaceId)
  const spaceData = space as ResearchSpace | undefined
  const [formState, setFormState] = useState<SpaceFormState>(() => toFormState(spaceData))
  const [advancedSettings, setAdvancedSettings] = useState<AdvancedSettingsState>(() =>
    toAdvancedState(spaceData?.settings as ResearchSpaceSettings | undefined),
  )
  const updateMutation = useUpdateResearchSpace()

  useEffect(() => {
    if (spaceId) {
      setCurrentSpaceId(spaceId)
    }
  }, [spaceId, setCurrentSpaceId])

  useEffect(() => {
    setFormState(toFormState(spaceData))
    setAdvancedSettings(toAdvancedState(spaceData?.settings as ResearchSpaceSettings | undefined))
  }, [spaceData])

  const parsedTags = useMemo(
    () =>
      formState.tagsInput
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
    [formState.tagsInput],
  )

  const currentSettings = useMemo(
    () => buildSettingsPayload(advancedSettings),
    [advancedSettings],
  )

  const isDirty = useMemo(() => {
    if (!spaceData) {
      return false
    }
    const tagsChanged =
      parsedTags.length !== spaceData.tags.length ||
      parsedTags.some((tag, index) => tag !== spaceData.tags[index])
    const settingsChanged = !areSettingsEqual(
      currentSettings,
      (spaceData.settings ?? {}) as ResearchSpaceSettings,
    )

    return (
      formState.name !== spaceData.name ||
      formState.slug !== spaceData.slug ||
      formState.description !== (spaceData.description ?? '') ||
      formState.status !== spaceData.status ||
      tagsChanged ||
      settingsChanged
    )
  }, [currentSettings, formState, parsedTags, spaceData])

  const handleChange =
    (field: keyof SpaceFormState) =>
    (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const value = event.target.value
      setFormState((prev) => ({ ...prev, [field]: value }))
    }

  const handleStatusChange = (value: string) => {
    setFormState((prev) => ({ ...prev, status: value as SpaceStatus }))
  }

  const handleAdvancedChange = <K extends keyof AdvancedSettingsState>(
    field: K,
    value: AdvancedSettingsState[K],
  ) => {
    setAdvancedSettings((prev) => ({ ...prev, [field]: value }))
  }

  const handleReset = () => {
    setFormState(toFormState(spaceData))
    setAdvancedSettings(toAdvancedState(spaceData?.settings as ResearchSpaceSettings | undefined))
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!spaceData || !isDirty) {
      return
    }

    const payload: UpdateSpaceRequest = {}
    if (formState.name !== spaceData.name) {
      payload.name = formState.name
    }
    if (formState.slug !== spaceData.slug) {
      payload.slug = formState.slug
    }
    if (formState.description !== (spaceData.description ?? '')) {
      payload.description = formState.description
    }
    if (formState.status !== spaceData.status) {
      payload.status = formState.status
    }
    if (!arraysShallowEqual(parsedTags, spaceData.tags)) {
      payload.tags = parsedTags
    }
    if (
      !areSettingsEqual(
        currentSettings,
        (spaceData.settings ?? {}) as ResearchSpaceSettings,
      )
    ) {
      payload.settings = currentSettings
    }

    try {
      await updateMutation.mutateAsync({ spaceId, data: payload })
      toast.success('Space settings updated')
    } catch (error) {
      console.error(error)
      toast.error('Failed to update space settings')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!spaceData) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-sm text-muted-foreground">
          Unable to load this research space. It may have been deleted or you lack permissions.
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Space Settings</h1>
        <p className="mt-1 text-muted-foreground">
          Configure settings for {spaceData.name || 'this research space'}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="size-5" />
            General Settings
          </CardTitle>
          <CardDescription>Manage space metadata and behavior.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="space-name">Space Name</Label>
              <Input id="space-name" value={formState.name} onChange={handleChange('name')} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="space-slug">Slug</Label>
              <Input
                id="space-slug"
                className="font-mono"
                value={formState.slug}
                onChange={handleChange('slug')}
                pattern="^[a-z0-9\\-]+$"
                title="Lowercase letters, numbers, and hyphens only"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="space-description">Description</Label>
              <Textarea
                id="space-description"
                rows={4}
                value={formState.description}
                onChange={handleChange('description')}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="space-tags">Tags</Label>
              <Input
                id="space-tags"
                value={formState.tagsInput}
                onChange={handleChange('tagsInput')}
                placeholder="med13, cardio, genomics"
              />
              <p className="text-xs text-muted-foreground">Comma-separated list used for filtering.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="space-status">Status</Label>
              <Select value={formState.status} onValueChange={handleStatusChange}>
                <SelectTrigger id="space-status">
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  {Object.values(SpaceStatus).map((status) => (
                    <SelectItem key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Curation Settings</CardTitle>
                <CardDescription>Fine-tune how submissions are reviewed.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ToggleRow
                  label="Auto approve submissions"
                  description="Automatically approve curated items that meet the threshold."
                  checked={advancedSettings.autoApprove}
                  onCheckedChange={(checked) => handleAdvancedChange('autoApprove', checked)}
                />
                <ToggleRow
                  label="Require manual review"
                  description="Ensure reviewers manually review each submission."
                  checked={advancedSettings.requireReview}
                  onCheckedChange={(checked) => handleAdvancedChange('requireReview', checked)}
                />
                <div className="space-y-1">
                  <Label htmlFor="review-threshold">Review Threshold</Label>
                  <Input
                    id="review-threshold"
                    type="number"
                    min={0}
                    max={1}
                    step={0.05}
                    value={advancedSettings.reviewThreshold}
                    onChange={(event) =>
                      handleAdvancedChange('reviewThreshold', Number(event.target.value))
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Minimum confidence score (0–1) before auto approval.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Data Source Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1">
                  <Label htmlFor="max-data-sources">Max Data Sources</Label>
                  <Input
                    id="max-data-sources"
                    type="number"
                    min={1}
                    value={advancedSettings.maxDataSources}
                    onChange={(event) =>
                      handleAdvancedChange('maxDataSources', Number(event.target.value))
                    }
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="allowed-source-types">Allowed Source Types</Label>
                  <Input
                    id="allowed-source-types"
                    value={advancedSettings.allowedSourceTypes}
                    onChange={(event) =>
                      handleAdvancedChange('allowedSourceTypes', event.target.value)
                    }
                    placeholder="API, CSV, FHIR"
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Access & Notifications</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ToggleRow
                  label="Public read access"
                  description="Allow non-members to view curated data."
                  checked={advancedSettings.publicRead}
                  onCheckedChange={(checked) => handleAdvancedChange('publicRead', checked)}
                />
                <ToggleRow
                  label="Allow member invites"
                  description="Let space members invite new collaborators."
                  checked={advancedSettings.allowInvites}
                  onCheckedChange={(checked) => handleAdvancedChange('allowInvites', checked)}
                />
                <ToggleRow
                  label="Email notifications"
                  description="Send notification emails for important events."
                  checked={advancedSettings.emailNotifications}
                  onCheckedChange={(checked) =>
                    handleAdvancedChange('emailNotifications', checked)
                  }
                />
                <div className="space-y-1">
                  <Label htmlFor="notification-frequency">Notification Frequency</Label>
                  <Select
                    value={advancedSettings.notificationFrequency}
                    onValueChange={(value) => handleAdvancedChange('notificationFrequency', value)}
                  >
                    <SelectTrigger id="notification-frequency">
                      <SelectValue placeholder="Select frequency" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="instant">Instant</SelectItem>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="weekly">Weekly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            <div className="flex flex-wrap gap-3">
              <Button type="submit" disabled={!isDirty || updateMutation.isPending}>
                {updateMutation.isPending ? 'Saving…' : 'Save Changes'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleReset}
                disabled={!isDirty || updateMutation.isPending}
                className={cn(!isDirty && 'cursor-not-allowed opacity-50')}
              >
                Reset
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

interface ToggleRowProps {
  label: string
  description?: string
  checked: boolean
  onCheckedChange: (checked: boolean) => void
}

function ToggleRow({ label, description, checked, onCheckedChange }: ToggleRowProps) {
  return (
    <label className="flex items-start gap-3">
      <Checkbox
        checked={checked}
        onCheckedChange={onCheckedChange}
        className="mt-1"
      />
      <span>
        <p className="text-sm font-medium leading-none">{label}</p>
        {description ? <p className="text-xs text-muted-foreground">{description}</p> : null}
      </span>
    </label>
  )
}

function buildSettingsPayload(state: AdvancedSettingsState): ResearchSpaceSettings {
  return {
    auto_approve: state.autoApprove,
    require_review: state.requireReview,
    review_threshold: state.reviewThreshold,
    max_data_sources: state.maxDataSources,
    allowed_source_types: state.allowedSourceTypes
      .split(',')
      .map((type) => type.trim())
      .filter(Boolean),
    public_read: state.publicRead,
    allow_invites: state.allowInvites,
    email_notifications: state.emailNotifications,
    notification_frequency: state.notificationFrequency,
  }
}

function areSettingsEqual(
  a: ResearchSpaceSettings,
  b: ResearchSpaceSettings,
): boolean {
  return JSON.stringify(a ?? {}) === JSON.stringify(b ?? {})
}

function arraysShallowEqual<T>(a: T[], b: T[]): boolean {
  if (a.length !== b.length) {
    return false
  }
  return a.every((value, index) => value === b[index])
}
