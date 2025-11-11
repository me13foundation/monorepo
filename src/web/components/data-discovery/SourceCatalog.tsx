"use client"

import React, { useMemo, useState } from 'react'
import {
  Activity,
  BarChart3,
  BookOpenText,
  BrainCircuit,
  Building2,
  Check,
  ChevronDown,
  CircleDot,
  ClipboardList,
  CreditCard,
  Database,
  Filter,
  FlaskConical,
  Globe,
  Layers,
  Library,
  Network,
  Search,
  Server,
  Share2,
  Target,
  TestTube2,
  Users,
} from 'lucide-react'
import { useSession } from 'next-auth/react'
import { SourceCatalogEntry } from '@/lib/types/data-discovery'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, Loader2, LogIn } from 'lucide-react'

const CATEGORIES = [
  'All Sources',
  'Genomic Variant Databases',
  'Gene Expression & Functional Genomics',
  'Model Organism Databases',
  'Protein / Pathway Databases',
  'Electronic Health Records (EHRs)',
  'Rare Disease Registries',
  'Clinical Trial Databases',
  'Phenotype Ontologies & Databases',
  'Scientific Literature',
  'Knowledge Graphs / Integrated Platforms',
  'Text-Mined Databases',
  'Cohort Studies',
  'Public Health Databases',
  'Insurance Claims / Billing Data',
  'Patient Advocacy Registries',
  'Social Media & Forums (Ethical Use)',
  'Surveys / PRO Data',
  'Transcriptomics / RNA-seq',
  'Epigenomics / Methylation',
  'Proteomics / Metabolomics',
  'Single-Cell Data',
  'Ontologies & Terminologies',
  'Data Repositories & Storage',
  'AI / ML Benchmark Datasets',
  'Institutional Repositories',
  'Consortia & Initiatives',
  'Cross-disciplinary Data Hubs',
  'Causal Models / Simulations',
  'Integrative Knowledge Graphs',
  'Computed Feature Stores',
  'AI Predictive Models',
]

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Genomic Variant Databases': Database,
  'Gene Expression & Functional Genomics': BarChart3,
  'Model Organism Databases': TestTube2,
  'Protein / Pathway Databases': Network,
  'Electronic Health Records (EHRs)': ClipboardList,
  'Rare Disease Registries': Users,
  'Clinical Trial Databases': TestTube2,
  'Phenotype Ontologies & Databases': Library,
  'Scientific Literature': BookOpenText,
  'Knowledge Graphs / Integrated Platforms': Network,
  'Text-Mined Databases': BookOpenText,
  'Cohort Studies': Users,
  'Public Health Databases': Globe,
  'Insurance Claims / Billing Data': CreditCard,
  'Patient Advocacy Registries': Users,
  'Social Media & Forums (Ethical Use)': Share2,
  'Surveys / PRO Data': ClipboardList,
  'Transcriptomics / RNA-seq': Activity,
  'Epigenomics / Methylation': Layers,
  'Proteomics / Metabolomics': FlaskConical,
  'Single-Cell Data': CircleDot,
  'Ontologies & Terminologies': Library,
  'Data Repositories & Storage': Database,
  'AI / ML Benchmark Datasets': Target,
  'Institutional Repositories': Building2,
  'Consortia & Initiatives': Users,
  'Cross-disciplinary Data Hubs': Globe,
  'Causal Models / Simulations': Activity,
  'Integrative Knowledge Graphs': Network,
  'Computed Feature Stores': Server,
  'AI Predictive Models': BrainCircuit,
}

interface SourceCatalogProps {
  catalog?: SourceCatalogEntry[]
  isLoading: boolean
  error: Error | null
  selectedSources: string[]
  onToggleSource: (sourceId: string) => void | Promise<void>
  onSelectAllInCategory: (category: string, sourceIds: string[]) => void | Promise<void>
}

export function SourceCatalog({
  catalog: catalogData,
  isLoading,
  error,
  selectedSources,
  onToggleSource,
  onSelectAllInCategory,
}: SourceCatalogProps) {
  const [activeCategory, setActiveCategory] = useState('All Sources')
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [isBulkUpdating, setIsBulkUpdating] = useState(false)
  const { data: session } = useSession()

  const catalog = useMemo(() => catalogData ?? [], [catalogData])

  // Filter sources based on category and search
  const filteredSources = useMemo(() => {
    return catalog.filter((source) => {
      const categoryMatch =
        activeCategory === 'All Sources' || source.category === activeCategory

      const searchMatch =
        searchQuery === '' ||
        source.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        source.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        source.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))

      return categoryMatch && searchMatch
    })
  }, [catalog, activeCategory, searchQuery])

  const allInCategorySelected = useMemo(() => {
    const categorySourceIds = filteredSources.map(s => s.id)
    if (categorySourceIds.length === 0) return false
    return categorySourceIds.every(id => selectedSources.includes(id))
  }, [filteredSources, selectedSources])

  const handleSelectAll = async () => {
    const categorySourceIds = filteredSources.map((s) => s.id)
    if (categorySourceIds.length === 0) {
      return
    }
    setIsBulkUpdating(true)
    try {
      await onSelectAllInCategory(activeCategory, categorySourceIds)
    } finally {
      setIsBulkUpdating(false)
    }
  }

  // Show authentication required state
  if (!session?.user?.access_token) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="max-w-md text-center">
          <LogIn className="mx-auto mb-4 size-12 text-muted-foreground" />
          <h3 className="mb-2 text-lg font-semibold text-foreground">
            Authentication Required
          </h3>
          <p className="mb-4 text-muted-foreground">
            You need to be logged in to access the data source catalog.
          </p>
          <Button asChild>
            <a href="/auth/login">Log In</a>
          </Button>
        </div>
      </div>
    )
  }

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="mx-auto mb-4 size-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading data sources...</p>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="size-4" />
        <AlertDescription>
          Failed to load data sources. Please try refreshing the page.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
      {/* Filter Sidebar */}
      <div className="min-w-0 overflow-hidden lg:col-span-1">
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="mb-4 flex w-full items-center justify-between lg:hidden"
        >
          <span className="font-medium">Filter Categories</span>
          <ChevronDown className={`size-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </Button>

        <div className={`${showFilters ? 'block' : 'hidden'} min-w-0 lg:block`}>
          <h2 className="mb-3 px-2 text-lg font-semibold text-foreground">Categories</h2>
          <div className="flex flex-col space-y-1">
            {CATEGORIES.map((category) => {
              const IconComponent = CATEGORY_ICONS[category] || Database
              return (
                <Button
                  key={category}
                  variant={activeCategory === category ? "default" : "ghost"}
                  onClick={() => setActiveCategory(category)}
                  className="h-auto w-full min-w-0 justify-start px-3 py-2"
                >
                  <IconComponent className="mr-2 size-4 shrink-0" />
                  <span className="min-w-0 flex-1 whitespace-normal break-words text-left">{category}</span>
                </Button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Source List */}
      <div className="lg:col-span-3">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search in "${activeCategory}"...`}
            className="pl-9"
          />
        </div>

        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-foreground">
            {activeCategory} ({filteredSources.length})
          </h2>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSelectAll}
            disabled={isBulkUpdating || filteredSources.length === 0}
            className="flex items-center space-x-2"
          >
            <div className={`flex size-4 items-center justify-center rounded border-2 ${
              allInCategorySelected ? 'border-primary bg-primary' : 'border-muted-foreground'
            }`}>
              {allInCategorySelected && <Check className="size-3 text-primary-foreground" />}
            </div>
            <span>
              {isBulkUpdating
                ? 'Updating…'
                : allInCategorySelected
                  ? 'Deselect All'
                  : 'Select All'}
            </span>
          </Button>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {filteredSources.length > 0 ? (
            filteredSources.map((source) => (
              <SourceCard
                key={source.id}
                source={source}
                isSelected={selectedSources.includes(source.id)}
                onToggle={() => onToggleSource(source.id)}
              />
            ))
          ) : (
            <div className="py-10 text-center text-muted-foreground md:col-span-2">
              <Filter className="mx-auto mb-4 size-12" />
              <h3 className="text-lg font-medium">No Data Sources Found</h3>
              <p>Try adjusting your search query or filter.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface SourceCardProps {
  source: SourceCatalogEntry
  isSelected: boolean
  onToggle: () => void
}

function SourceCard({ source, isSelected, onToggle }: SourceCardProps) {
  const IconComponent = CATEGORY_ICONS[source.category] || Database

  return (
    <Card className={`cursor-pointer transition-all ${
      isSelected ? 'border-primary shadow-md' : 'border-border hover:shadow-sm'
    }`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex min-w-0 flex-1 items-start space-x-3">
            <IconComponent className="mt-0.5 size-5 shrink-0 text-primary" />
            <div className="min-w-0 flex-1">
              <h3 className="mb-1 truncate font-semibold text-foreground">
                {source.name}
              </h3>
              <p className="mb-2 text-xs text-muted-foreground">
                {source.category}
              </p>
              <p className="mb-3 line-clamp-2 text-sm text-muted-foreground">
                {source.description}
              </p>
              <div className="mb-3 flex flex-wrap gap-1">
                {source.tags.slice(0, 3).map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{source.usage_count} uses</span>
                <span>{Math.round(source.success_rate * 100)}% success</span>
              </div>
            </div>
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation()
              onToggle()
            }}
            className="shrink-0 p-1"
          >
            <div className={`flex size-6 items-center justify-center rounded-md border-2 transition-all ${
              isSelected
                ? 'border-primary bg-primary'
                : 'border-muted-foreground bg-background hover:border-primary'
            }`}>
              {isSelected && <Check className="size-4 text-primary-foreground" />}
            </div>
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
