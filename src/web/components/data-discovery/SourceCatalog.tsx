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
        <div className="text-center max-w-md">
          <LogIn className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold text-foreground mb-2">
            Authentication Required
          </h3>
          <p className="text-muted-foreground mb-4">
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
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading data sources...</p>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load data sources. Please try refreshing the page.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Filter Sidebar */}
      <div className="lg:col-span-1 min-w-0 overflow-hidden">
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="lg:hidden w-full flex items-center justify-between mb-4"
        >
          <span className="font-medium">Filter Categories</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </Button>

        <div className={`${showFilters ? 'block' : 'hidden'} lg:block min-w-0`}>
          <h2 className="text-lg font-semibold mb-3 px-2 text-foreground">Categories</h2>
          <div className="flex flex-col space-y-1">
            {CATEGORIES.map((category) => {
              const IconComponent = CATEGORY_ICONS[category] || Database
              return (
                <Button
                  key={category}
                  variant={activeCategory === category ? "default" : "ghost"}
                  onClick={() => setActiveCategory(category)}
                  className="w-full justify-start h-auto py-2 px-3 min-w-0"
                >
                  <IconComponent className="w-4 h-4 mr-2 flex-shrink-0" />
                  <span className="text-left break-words whitespace-normal flex-1 min-w-0">{category}</span>
                </Button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Source List */}
      <div className="lg:col-span-3">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={`Search in "${activeCategory}"...`}
            className="pl-9"
          />
        </div>

        <div className="flex justify-between items-center mb-4">
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
            <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
              allInCategorySelected ? 'bg-primary border-primary' : 'border-muted-foreground'
            }`}>
              {allInCategorySelected && <Check className="w-3 h-3 text-primary-foreground" />}
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
            <div className="md:col-span-2 text-center text-muted-foreground py-10">
              <Filter className="w-12 h-12 mx-auto mb-4" />
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
    <Card className={`transition-all cursor-pointer ${
      isSelected ? 'border-primary shadow-md' : 'border-border hover:shadow-sm'
    }`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1 min-w-0">
            <IconComponent className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-foreground mb-1 truncate">
                {source.name}
              </h3>
              <p className="text-xs text-muted-foreground mb-2">
                {source.category}
              </p>
              <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                {source.description}
              </p>
              <div className="flex flex-wrap gap-1 mb-3">
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
            className="flex-shrink-0 p-1"
          >
            <div className={`w-6 h-6 rounded-md flex items-center justify-center border-2 transition-all ${
              isSelected
                ? 'bg-primary border-primary'
                : 'bg-background border-muted-foreground hover:border-primary'
            }`}>
              {isSelected && <Check className="w-4 h-4 text-primary-foreground" />}
            </div>
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
