"use client"

import { Search } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface FloatingActionBarProps {
  selectedCount: number
  onGenerate: () => void
}

export function FloatingActionBar({ selectedCount, onGenerate }: FloatingActionBarProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-background/80 backdrop-blur-sm border-t border-border p-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
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

        <Button
          onClick={onGenerate}
          disabled={selectedCount === 0}
          size="lg"
          className="flex items-center space-x-2 shadow-lg"
        >
          <span>Generate Results</span>
          <Search className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}
