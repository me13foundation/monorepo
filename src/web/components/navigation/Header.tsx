"use client"

import { SpaceSelector } from '@/components/research-spaces/SpaceSelector'
import { useSpaceContext } from '@/components/space-context-provider'
import { UserMenu } from './UserMenu'
import { LayoutDashboard } from 'lucide-react'
import Link from 'next/link'

export function Header() {
  const { currentSpaceId } = useSpaceContext()

  return (
    <header className="bg-card shadow-sm border-b border-border sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center py-4 gap-3 sm:gap-0">
          <div className="flex items-center gap-3 sm:gap-6 min-w-0 flex-1">
            <Link href="/dashboard" className="flex items-center gap-2 flex-shrink-0">
              <LayoutDashboard className="h-5 w-5 sm:h-6 sm:w-6" />
              <span className="text-lg sm:text-xl font-bold">MED13 Admin</span>
            </Link>
            <div className="min-w-0 flex-1 max-w-xs">
              <SpaceSelector currentSpaceId={currentSpaceId || undefined} />
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            <UserMenu />
          </div>
        </div>
      </div>
    </header>
  )
}
