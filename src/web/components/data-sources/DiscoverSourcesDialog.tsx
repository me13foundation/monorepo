'use client'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { DataDiscoveryContent } from '@/components/data-discovery/DataDiscoveryContent'

interface DiscoverSourcesDialogProps {
  spaceId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DiscoverSourcesDialog({
  spaceId,
  open,
  onOpenChange,
}: DiscoverSourcesDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[90vh] max-w-7xl flex-col p-0">
        <DialogHeader className="shrink-0 border-b px-6 py-4">
          <DialogTitle>Discover Data Sources</DialogTitle>
          <DialogDescription>
            Browse and test available data sources before adding them to your research space.
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-hidden p-6">
          <DataDiscoveryContent spaceId={spaceId} isModal={true} />
        </div>
      </DialogContent>
    </Dialog>
  )
}
