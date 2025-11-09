"use client"

import { Library } from 'lucide-react'

export function DataDiscoveryHeader() {
  return (
    <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 pb-6 border-b border-border">
      <div className="flex items-center space-x-3 mb-4 md:mb-0">
        <div className="p-2 bg-primary rounded-lg">
          <Library className="w-8 h-8 text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-foreground">
            Data Source Discovery
          </h1>
          <p className="text-sm md:text-base text-muted-foreground">
            Discover, test, and select biomedical data sources for your research.
          </p>
        </div>
      </div>
      <div className="text-xs text-muted-foreground bg-muted p-2 rounded-lg text-center md:text-right">
        Based on the Data Ecosystem Report for <br />
        <span className="font-semibold text-foreground">MED13-Related Syndrome Research</span>
      </div>
    </div>
  )
}
