"use client"

import { SpaceSelector } from '@/components/research-spaces/SpaceSelector'
import { useSpaceContext } from '@/components/space-context-provider'
import { UserMenu } from './UserMenu'
import Link from 'next/link'
import Image from 'next/image'
import { usePrefetchOnHover } from '@/hooks/use-prefetch'

export function Header() {
  const { currentSpaceId } = useSpaceContext()
  const { prefetchDashboard, prefetchResearchSpaces } = usePrefetchOnHover()

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-card shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between sm:gap-0">
          <div className="flex min-w-0 flex-1 items-center gap-3 sm:gap-6">
            <Link
              href="/dashboard"
              className="flex shrink-0 items-center gap-2"
              onMouseEnter={prefetchDashboard}
              onFocus={prefetchDashboard}
              prefetch={true}
            >
              <Image
                src="/logo.svg"
                alt="MED13 Logo"
                width={32}
                height={32}
                className="size-8 sm:size-10"
                priority
              />
              <span className="text-lg font-bold sm:text-xl">MED13 Admin</span>
            </Link>
            <div className="min-w-0 max-w-xs flex-1">
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
