"use client"

import { QueryParameters } from '@/lib/types/data-discovery'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface ParameterBarProps {
  parameters: QueryParameters
  onParametersChange: (parameters: QueryParameters) => void
}

export function ParameterBar({ parameters, onParametersChange }: ParameterBarProps) {
  const handleGeneSymbolChange = (value: string) => {
    onParametersChange({
      ...parameters,
      gene_symbol: value.toUpperCase() || null,
    })
  }

  const handleSearchTermChange = (value: string) => {
    onParametersChange({
      ...parameters,
      search_term: value || null,
    })
  }

  return (
    <div className="mb-6 grid grid-cols-1 gap-4 rounded-lg border border-border bg-card/50 p-4 md:grid-cols-2">
      <div>
        <Label
          htmlFor="geneSymbol"
          className="mb-1 block text-sm font-medium text-foreground"
        >
          Gene Symbol
        </Label>
        <Input
          type="text"
          id="geneSymbol"
          value={parameters.gene_symbol || ''}
          onChange={(e) => handleGeneSymbolChange(e.target.value)}
          placeholder="e.g., MED13L"
          className="bg-background"
        />
      </div>

      <div>
        <Label
          htmlFor="searchTerm"
          className="mb-1 block text-sm font-medium text-foreground"
        >
          Phenotype / Search Term
        </Label>
        <Input
          type="text"
          id="searchTerm"
          value={parameters.search_term || ''}
          onChange={(e) => handleSearchTermChange(e.target.value)}
          placeholder="e.g., atrial septal defect"
          className="bg-background"
        />
      </div>
    </div>
  )
}
