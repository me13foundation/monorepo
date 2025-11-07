"use client"

import { useSession, signOut } from 'next-auth/react'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/theme-toggle'
import { SpaceSelector } from '@/components/research-spaces/SpaceSelector'
import { useSpaceContext } from '@/components/space-context-provider'
import { Settings, Plus, LogOut, User, LayoutDashboard } from 'lucide-react'
import Link from 'next/link'

export function Header() {
  const { data: session } = useSession()
  const { currentSpaceId } = useSpaceContext()

  const handleSignOut = () => {
    signOut({ callbackUrl: '/auth/login' })
  }

  return (
    <header className="bg-card shadow-sm border-b border-border sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="flex items-center gap-2">
              <LayoutDashboard className="h-6 w-6" />
              <span className="text-xl font-bold">MED13 Admin</span>
            </Link>
            {currentSpaceId && (
              <SpaceSelector currentSpaceId={currentSpaceId} />
            )}
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="outline" size="sm" asChild>
              <Link href="/spaces/new">
                <Plus className="h-4 w-4 mr-2" />
                Create Space
              </Link>
            </Button>
            {currentSpaceId && (
              <Button variant="outline" size="sm" asChild>
                <Link href={`/spaces/${currentSpaceId}/data-sources`}>
                  <Plus className="h-4 w-4 mr-2" />
                  Data Sources
                </Link>
              </Button>
            )}
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <User className="h-4 w-4" />
              <span>{session?.user?.role}</span>
            </div>
            <ThemeToggle />
            <Button variant="outline" size="sm" asChild>
              <Link href="/settings">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Link>
            </Button>
            <Button variant="outline" size="sm" onClick={handleSignOut}>
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}
