"use client"

import { useEffect, useMemo, useState, useTransition } from 'react'
import { toast } from 'sonner'
import {
  PlusCircle,
  Pencil,
  Trash2,
  Loader2,
  Beaker,
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { PaginatedResponse } from '@/types/generated'
import type {
  EvidenceTier,
  Mechanism,
  MechanismCreateRequest,
  MechanismUpdateRequest,
  ProteinDomainPayload,
  ProteinDomainType,
} from '@/types/mechanisms'
import {
  createMechanismAction,
  deleteMechanismAction,
  updateMechanismAction,
} from '@/app/actions/mechanisms'

const EVIDENCE_TIER_LABELS: Record<EvidenceTier, string> = {
  definitive: 'Definitive',
  strong: 'Strong',
  moderate: 'Moderate',
  supporting: 'Supporting',
  weak: 'Weak',
  disproven: 'Disproven',
}

const EVIDENCE_TIER_VARIANTS: Record<EvidenceTier, 'default' | 'secondary' | 'outline' | 'destructive'> = {
  definitive: 'default',
  strong: 'default',
  moderate: 'secondary',
  supporting: 'outline',
  weak: 'outline',
  disproven: 'destructive',
}

const DOMAIN_TYPE_OPTIONS: { label: string; value: ProteinDomainType }[] = [
  { label: 'Structural', value: 'structural' },
  { label: 'Functional', value: 'functional' },
  { label: 'Binding site', value: 'binding_site' },
  { label: 'Disordered', value: 'disordered' },
]

type DomainFormState = {
  name: string
  source_id: string
  start_residue: string
  end_residue: string
  domain_type: ProteinDomainType
  description: string
}

type MechanismFormState = {
  name: string
  description: string
  evidence_tier: EvidenceTier
  confidence_score: string
  source: string
  phenotype_ids: string
  domains: DomainFormState[]
}

interface MechanismManagementSectionProps {
  mechanisms: PaginatedResponse<Mechanism> | null
}

const buildDomainState = (domain?: ProteinDomainPayload): DomainFormState => ({
  name: domain?.name ?? '',
  source_id: domain?.source_id ?? '',
  start_residue: domain?.start_residue ? String(domain.start_residue) : '',
  end_residue: domain?.end_residue ? String(domain.end_residue) : '',
  domain_type: domain?.domain_type ?? 'structural',
  description: domain?.description ?? '',
})

const buildFormState = (mechanism?: Mechanism): MechanismFormState => ({
  name: mechanism?.name ?? '',
  description: mechanism?.description ?? '',
  evidence_tier: mechanism?.evidence_tier ?? 'supporting',
  confidence_score: mechanism?.confidence_score ? String(mechanism.confidence_score) : '0.5',
  source: mechanism?.source ?? 'manual_curation',
  phenotype_ids: mechanism?.phenotype_ids?.length
    ? mechanism.phenotype_ids.join(', ')
    : '',
  domains: mechanism?.protein_domains?.length
    ? mechanism.protein_domains.map(buildDomainState)
    : [],
})

export function MechanismManagementSection({ mechanisms }: MechanismManagementSectionProps) {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [editorOpen, setEditorOpen] = useState(false)
  const [activeMechanism, setActiveMechanism] = useState<Mechanism | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Mechanism | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isPending, startTransition] = useTransition()

  const mechanismItems = mechanisms?.items ?? []
  const listError = mechanisms === null ? 'Unable to load mechanisms. Please retry.' : null

  const filtered = useMemo(() => {
    if (!search.trim()) {
      return mechanismItems
    }
    const query = search.trim().toLowerCase()
    return mechanismItems.filter(
      (mechanism) =>
        mechanism.name.toLowerCase().includes(query) ||
        (mechanism.description ?? '').toLowerCase().includes(query),
    )
  }, [mechanismItems, search])

  const handleOpenCreate = () => {
    setActiveMechanism(null)
    setEditorOpen(true)
  }

  const handleOpenEdit = (mechanism: Mechanism) => {
    setActiveMechanism(mechanism)
    setEditorOpen(true)
  }

  const handleSave = async (payload: MechanismCreateRequest | MechanismUpdateRequest) => {
    setIsSaving(true)
    try {
      if (activeMechanism) {
        const result = await updateMechanismAction(activeMechanism.id, payload)
        if (!result.success) {
          toast.error(result.error)
          return
        }
        toast.success(`Updated ${result.data.name}`)
      } else {
        const result = await createMechanismAction(payload as MechanismCreateRequest)
        if (!result.success) {
          toast.error(result.error)
          return
        }
        toast.success(`Created ${result.data.name}`)
      }
      setEditorOpen(false)
      startTransition(() => router.refresh())
    } catch (error) {
      console.error('Failed to save mechanism', error)
      toast.error('Unable to save mechanism')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) {
      return
    }
    setIsDeleting(true)
    try {
      const result = await deleteMechanismAction(deleteTarget.id)
      if (!result.success) {
        toast.error(result.error)
        return
      }
      toast.success(`Deleted ${deleteTarget.name}`)
      setDeleteTarget(null)
      startTransition(() => router.refresh())
    } catch (error) {
      console.error('Failed to delete mechanism', error)
      toast.error('Unable to delete mechanism')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <Card>
      <CardHeader className="space-y-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle className="font-heading text-xl">Mechanisms</CardTitle>
            <CardDescription>
              Manage mechanistic nodes that connect protein domains to phenotypes.
            </CardDescription>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button variant="outline" onClick={() => startTransition(() => router.refresh())} disabled={isPending}>
              {isPending ? (
                <>
                  <Loader2 className="mr-2 size-4 animate-spin" />
                  Refreshing…
                </>
              ) : (
                <>
                  <Beaker className="mr-2 size-4" />
                  Refresh
                </>
              )}
            </Button>
            <Button onClick={handleOpenCreate}>
              <PlusCircle className="mr-2 size-4" />
              Add Mechanism
            </Button>
          </div>
        </div>
        <div className="max-w-md space-y-2">
          <Label htmlFor="mechanism-search">Search</Label>
          <Input
            id="mechanism-search"
            placeholder="Search mechanisms"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
      </CardHeader>
      <CardContent>
        {listError && (
          <div className="mb-4 rounded border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {listError}
          </div>
        )}

        {filtered.length === 0 ? (
          <div className="flex items-center gap-2 rounded border border-dashed px-4 py-8 text-muted-foreground">
            No mechanisms available.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Mechanism</TableHead>
                  <TableHead>Evidence</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Phenotypes</TableHead>
                  <TableHead>Domains</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((mechanism) => (
                  <TableRow key={mechanism.id}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{mechanism.name}</span>
                        {mechanism.description && (
                          <span className="text-xs text-muted-foreground">
                            {mechanism.description}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={EVIDENCE_TIER_VARIANTS[mechanism.evidence_tier]}>
                        {EVIDENCE_TIER_LABELS[mechanism.evidence_tier]}
                      </Badge>
                    </TableCell>
                    <TableCell>{mechanism.confidence_score.toFixed(2)}</TableCell>
                    <TableCell>{mechanism.phenotype_count}</TableCell>
                    <TableCell>{mechanism.protein_domains.length}</TableCell>
                    <TableCell>{formatDate(mechanism.updated_at)}</TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleOpenEdit(mechanism)}>
                          <Pencil className="mr-2 size-4" />
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive"
                          onClick={() => setDeleteTarget(mechanism)}
                        >
                          <Trash2 className="mr-2 size-4" />
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>

      <MechanismEditorDialog
        open={editorOpen}
        onOpenChange={setEditorOpen}
        mechanism={activeMechanism}
        onSubmit={handleSave}
        isSubmitting={isSaving}
      />

      <DeleteMechanismDialog
        mechanism={deleteTarget}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        isPending={isDeleting}
      />
    </Card>
  )
}

function MechanismEditorDialog({
  open,
  onOpenChange,
  mechanism,
  onSubmit,
  isSubmitting,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  mechanism: Mechanism | null
  onSubmit: (payload: MechanismCreateRequest | MechanismUpdateRequest) => Promise<void>
  isSubmitting: boolean
}) {
  const [form, setForm] = useState<MechanismFormState>(buildFormState(mechanism ?? undefined))

  useEffect(() => {
    if (open) {
      setForm(buildFormState(mechanism ?? undefined))
    }
  }, [open, mechanism])

  const updateField = <K extends keyof MechanismFormState>(
    field: K,
    value: MechanismFormState[K],
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const updateDomain = <K extends keyof DomainFormState>(
    index: number,
    field: K,
    value: DomainFormState[K],
  ) => {
    setForm((prev) => {
      const next = [...prev.domains]
      next[index] = { ...next[index], [field]: value }
      return { ...prev, domains: next }
    })
  }

  const addDomain = () => {
    setForm((prev) => ({ ...prev, domains: [...prev.domains, buildDomainState()] }))
  }

  const removeDomain = (index: number) => {
    setForm((prev) => {
      const next = [...prev.domains]
      next.splice(index, 1)
      return { ...prev, domains: next }
    })
  }

  const parsePhenotypeIds = (value: string): number[] => {
    if (!value.trim()) {
      return []
    }
    return value
      .split(',')
      .map((item) => Number.parseInt(item.trim(), 10))
      .filter((item) => Number.isFinite(item))
  }

  const normalizeDomains = (): ProteinDomainPayload[] => {
    return form.domains
      .filter((domain) => domain.name.trim())
      .map((domain) => {
        const start = Number.parseInt(domain.start_residue, 10)
        const end = Number.parseInt(domain.end_residue, 10)
        return {
          name: domain.name.trim(),
          source_id: domain.source_id.trim() || undefined,
          start_residue: Number.isFinite(start) ? start : 1,
          end_residue: Number.isFinite(end) ? end : 1,
          domain_type: domain.domain_type,
          description: domain.description.trim() || undefined,
        }
      })
  }

  const handleSubmit = async () => {
    const confidence = Number.parseFloat(form.confidence_score)
    if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) {
      toast.error('Confidence score must be between 0 and 1')
      return
    }
    if (!form.name.trim()) {
      toast.error('Mechanism name is required')
      return
    }

    const payload = {
      name: form.name.trim(),
      description: form.description.trim() || undefined,
      evidence_tier: form.evidence_tier,
      confidence_score: confidence,
      source: form.source.trim() || 'manual_curation',
      protein_domains: normalizeDomains(),
      phenotype_ids: parsePhenotypeIds(form.phenotype_ids),
    }

    if (mechanism) {
      const updatePayload: MechanismUpdateRequest = {
        name: payload.name,
        description: payload.description ?? null,
        evidence_tier: payload.evidence_tier,
        confidence_score: payload.confidence_score,
        source: payload.source,
        protein_domains: payload.protein_domains,
        phenotype_ids: payload.phenotype_ids,
      }
      await onSubmit(updatePayload)
    } else {
      await onSubmit(payload)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{mechanism ? 'Edit mechanism' : 'Create mechanism'}</DialogTitle>
          <DialogDescription>
            Capture mechanistic evidence and link to phenotypes for causal reasoning.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="mechanism-name">Mechanism name</Label>
              <Input
                id="mechanism-name"
                value={form.name}
                onChange={(event) => updateField('name', event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="mechanism-source">Source</Label>
              <Input
                id="mechanism-source"
                value={form.source}
                onChange={(event) => updateField('source', event.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="mechanism-description">Description</Label>
            <Textarea
              id="mechanism-description"
              value={form.description}
              onChange={(event) => updateField('description', event.target.value)}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="mechanism-evidence">Evidence tier</Label>
              <Select
                value={form.evidence_tier}
                onValueChange={(value) => updateField('evidence_tier', value as EvidenceTier)}
              >
                <SelectTrigger id="mechanism-evidence">
                  <SelectValue placeholder="Select tier" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(EVIDENCE_TIER_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="mechanism-confidence">Confidence score</Label>
              <Input
                id="mechanism-confidence"
                type="number"
                min={0}
                max={1}
                step={0.01}
                value={form.confidence_score}
                onChange={(event) => updateField('confidence_score', event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="mechanism-phenotypes">Phenotype IDs</Label>
              <Input
                id="mechanism-phenotypes"
                placeholder="1, 2, 3"
                value={form.phenotype_ids}
                onChange={(event) => updateField('phenotype_ids', event.target.value)}
              />
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <Label>Protein domains</Label>
                <p className="text-xs text-muted-foreground">
                  Add domains implicated in this mechanism.
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={addDomain}>
                <PlusCircle className="mr-2 size-4" />
                Add domain
              </Button>
            </div>

            {form.domains.length === 0 ? (
              <div className="rounded border border-dashed px-4 py-3 text-sm text-muted-foreground">
                No domains added yet.
              </div>
            ) : (
              <div className="space-y-4">
                {form.domains.map((domain, index) => (
                  <div key={`domain-${index}`} className="rounded border border-border p-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label>Domain name</Label>
                        <Input
                          value={domain.name}
                          onChange={(event) => updateDomain(index, 'name', event.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Source ID</Label>
                        <Input
                          value={domain.source_id}
                          onChange={(event) => updateDomain(index, 'source_id', event.target.value)}
                        />
                      </div>
                    </div>
                    <div className="mt-3 grid gap-4 md:grid-cols-3">
                      <div className="space-y-2">
                        <Label>Start residue</Label>
                        <Input
                          type="number"
                          min={1}
                          value={domain.start_residue}
                          onChange={(event) => updateDomain(index, 'start_residue', event.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>End residue</Label>
                        <Input
                          type="number"
                          min={1}
                          value={domain.end_residue}
                          onChange={(event) => updateDomain(index, 'end_residue', event.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Domain type</Label>
                        <Select
                          value={domain.domain_type}
                          onValueChange={(value) =>
                            updateDomain(index, 'domain_type', value as ProteinDomainType)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                          <SelectContent>
                            {DOMAIN_TYPE_OPTIONS.map((option) => (
                              <SelectItem key={option.value} value={option.value}>
                                {option.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="mt-3 space-y-2">
                      <Label>Description</Label>
                      <Textarea
                        value={domain.description}
                        onChange={(event) => updateDomain(index, 'description', event.target.value)}
                      />
                    </div>
                    <div className="mt-3 flex justify-end">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive"
                        onClick={() => removeDomain(index)}
                      >
                        Remove domain
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Saving…
              </>
            ) : (
              'Save Mechanism'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function DeleteMechanismDialog({
  mechanism,
  onCancel,
  onConfirm,
  isPending,
}: {
  mechanism: Mechanism | null
  onCancel: () => void
  onConfirm: () => Promise<void>
  isPending: boolean
}) {
  return (
    <Dialog open={Boolean(mechanism)} onOpenChange={(open) => (!open ? onCancel() : null)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete mechanism</DialogTitle>
          <DialogDescription>
            This will permanently remove {mechanism?.name ?? 'this mechanism'} and its phenotype links.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={isPending}>
            {isPending ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Deleting…
              </>
            ) : (
              'Delete'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function formatDate(value: string | null) {
  if (!value) {
    return '—'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleDateString()
}
