"use client"

import { useState, useMemo } from 'react'
import { Search, Filter, ChevronDown, Database, Check } from 'lucide-react'
import { useDataDiscoveryStore } from '@/lib/stores/data-discovery-store'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

// Mock data - in real implementation this would come from API
const MOCK_CATALOG = [
  {
    id: 'clinvar',
    name: 'ClinVar',
    category: 'Genomic Variant Databases',
    description: 'Public archive of reports of the relationships among human variations and phenotypes.',
    param_type: 'gene' as const,
    is_active: true,
    requires_auth: false,
    usage_count: 1250,
    success_rate: 0.94,
    tags: ['variants', 'clinical', 'pathogenic'],
  },
  {
    id: 'gnomad',
    name: 'gnomAD',
    category: 'Genomic Variant Databases',
    description: 'Genome Aggregation Database provides allele frequency data from large-scale sequencing.',
    param_type: 'gene' as const,
    is_active: true,
    requires_auth: false,
    usage_count: 980,
    success_rate: 0.91,
    tags: ['frequency', 'population', 'sequencing'],
  },
  {
    id: 'hpo',
    name: 'Human Phenotype Ontology',
    category: 'Phenotype Ontologies & Databases',
    description: 'Standardized vocabulary for describing human phenotypic abnormalities.',
    param_type: 'term' as const,
    is_active: true,
    requires_auth: false,
    usage_count: 1450,
    success_rate: 0.96,
    tags: ['phenotype', 'ontology', 'standardized'],
  },
  {
    id: 'variantformer',
    name: 'VariantFormer',
    category: 'AI Predictive Models',
    description: 'State-of-the-art AI model for predicting variant pathogenicity.',
    param_type: 'api' as const,
    is_active: true,
    requires_auth: false,
    usage_count: 320,
    success_rate: 0.87,
    tags: ['ai', 'prediction', 'pathogenicity'],
  },
]

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
  'AI Predictive Models',
]

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Genomic Variant Databases': Database,
  'Gene Expression & Functional Genomics': Database,
  'Model Organism Databases': Database,
  'Protein / Pathway Databases': Database,
  'Electronic Health Records (EHRs)': Database,
  'Rare Disease Registries': Database,
  'Clinical Trial Databases': Database,
  'Phenotype Ontologies & Databases': Database,
  'Scientific Literature': Database,
  'Knowledge Graphs / Integrated Platforms': Database,
  'AI Predictive Models': Database,
}

export function SourceCatalog() {
  const [activeCategory, setActiveCategory] = useState('All Sources')
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const { selectedSources, toggleSourceSelection, selectAllInCategory } = useDataDiscoveryStore()

  // Filter sources based on category and search
  const filteredSources = useMemo(() => {
    return MOCK_CATALOG.filter((source) => {
      const categoryMatch =
        activeCategory === 'All Sources' || source.category === activeCategory

      const searchMatch =
        searchQuery === '' ||
        source.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        source.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        source.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))

      return categoryMatch && searchMatch
    })
  }, [activeCategory, searchQuery])

  const allInCategorySelected = useMemo(() => {
    const categorySourceIds = filteredSources.map(s => s.id)
    if (categorySourceIds.length === 0) return false
    return categorySourceIds.every(id => selectedSources.includes(id))
  }, [filteredSources, selectedSources])

  const handleSelectAll = () => {
    const categorySourceIds = filteredSources.map(s => s.id)
    selectAllInCategory(activeCategory)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Filter Sidebar */}
      <div className="lg:col-span-1">
        <Button
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
          className="lg:hidden w-full flex items-center justify-between mb-4"
        >
          <span className="font-medium">Filter Categories</span>
          <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </Button>

        <div className={`${showFilters ? 'block' : 'hidden'} lg:block`}>
          <h2 className="text-lg font-semibold mb-3 px-2 text-foreground">Categories</h2>
          <div className="flex flex-col space-y-1">
            {CATEGORIES.map((category) => {
              const IconComponent = CATEGORY_ICONS[category] || Database
              return (
                <Button
                  key={category}
                  variant={activeCategory === category ? "default" : "ghost"}
                  onClick={() => setActiveCategory(category)}
                  className="w-full justify-start h-auto py-2 px-3"
                >
                  <IconComponent className="w-4 h-4 mr-2 flex-shrink-0" />
                  <span className="text-left">{category}</span>
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
            className="flex items-center space-x-2"
          >
            <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
              allInCategorySelected ? 'bg-primary border-primary' : 'border-muted-foreground'
            }`}>
              {allInCategorySelected && <Check className="w-3 h-3 text-primary-foreground" />}
            </div>
            <span>{allInCategorySelected ? 'Deselect All' : 'Select All'}</span>
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredSources.length > 0 ? (
            filteredSources.map((source) => (
              <SourceCard
                key={source.id}
                source={source}
                isSelected={selectedSources.includes(source.id)}
                onToggle={() => toggleSourceSelection(source.id)}
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
  source: typeof MOCK_CATALOG[0]
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
