"use client"

import { useSpaceContext } from '@/components/space-context-provider'
import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import {
  Database,
  Settings,
  FileText,
  LayoutDashboard,
  Users,
} from 'lucide-react'

interface NavItem {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  description?: string
}

export function SpaceNavigation() {
  const { currentSpaceId } = useSpaceContext()
  const pathname = usePathname()

  if (!currentSpaceId) {
    return null
  }

  const basePath = `/spaces/${currentSpaceId}`

  const navItems: NavItem[] = [
    {
      label: 'Overview',
      href: basePath,
      icon: LayoutDashboard,
      description: 'Space details and information',
    },
    {
      label: 'Data Sources',
      href: `${basePath}/data-sources`,
      icon: Database,
      description: 'Manage data sources',
    },
    {
      label: 'Data Curation',
      href: `${basePath}/curation`,
      icon: FileText,
      description: 'Curate and review data',
    },
    {
      label: 'Members',
      href: `${basePath}/members`,
      icon: Users,
      description: 'Manage team members',
    },
    {
      label: 'Settings',
      href: `${basePath}/settings`,
      icon: Settings,
      description: 'Space configuration',
    },
  ]

  return (
    <nav className="border-b border-border bg-card">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex overflow-x-auto">
          <div className="flex space-x-1 min-w-0">
            {navItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`)
              const Icon = item.icon

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors',
                    'border-b-2 border-transparent hover:border-border hover:text-foreground',
                    'whitespace-nowrap',
                    isActive
                      ? 'border-primary text-foreground bg-accent/50'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                  title={item.description}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span className="hidden sm:inline">{item.label}</span>
                  <span className="sm:hidden">{item.label.split(' ')[0]}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}
