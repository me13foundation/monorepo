"use client"

import { Search } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface FloatingActionBarProps {
  selectedCount: number
  onGenerate: () => void
  isGenerating?: boolean
}

export function FloatingActionBar({ selectedCount, onGenerate, isGenerating = false }: FloatingActionBarProps) {
  return (
    <div className="fixed inset-x-0 bottom-0 border-t border-border bg-background/80 p-4 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <div className="text-sm font-medium text-foreground">
          <span
            className={`font-bold ${
              selectedCount > 0 ? 'text-primary' : 'text-muted-foreground'
            }`}
          >
            {selectedCount}
          </span>
          <span className="text-muted-foreground">
            {' '}
            data source{selectedCount !== 1 ? 's' : ''} selected
          </span>
        </div>

        <Button onClick={onGenerate} disabled={selectedCount === 0 || isGenerating} size="lg" className="flex items-center space-x-2 shadow-lg">
          <span>{isGenerating ? 'Generating...' : 'Generate Results'}</span>
          <Search className={`size-4 ${isGenerating ? 'animate-pulse' : ''}`} />
        </Button>
      </div>
    </div>
  )
}
